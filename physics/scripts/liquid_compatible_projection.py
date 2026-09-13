"""Collocated D M G projection reference using actual captured liquid boundaries.

The existing particle/grid sampling remains collocated. M fixes the same normal
velocity components as the terrain/river boundary, so the pressure matrix is
the composition of the divergence and the actual masked velocity correction.
This CPU reference is not a production solver or performance claim.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields


def shift(a, offset, axis):
    """Sample a[i+offset], with zero outside the computational domain."""
    result = np.roll(a, -offset, axis=axis)
    edge = [slice(None)]*a.ndim
    edge[axis] = slice(-offset, None) if offset > 0 else slice(None, -offset)
    result[tuple(edge)] = 0
    return result


def gradient(p, spacing):
    return np.stack([(shift(p, 1, 2-component)-shift(p, -1, 2-component))/(2*h)
                     for component, h in enumerate(spacing)], axis=-1)


def divergence(v, spacing):
    return sum((shift(v[..., c], 1, 2-c)-shift(v[..., c], -1, 2-c))/(2*h)
               for c, h in enumerate(spacing))


def surface_gradient_weights(boundary, phi):
    """Ghost-fluid distances for the existing centred +/-h gradient.

    phi is a current signed liquid interface field at pressure locations, in
    consistent length units, negative in water. At each velocity location the
    pressure samples are 2h apart. If only one is wet, the gradient reaches the
    zero-pressure surface after theta*2h, not the far empty-cell centre.
    The same weights MUST enter D M W G and the final velocity update. This
    function alone is not a native surface reconstruction or boundary model.
    """
    phi=np.asarray(phi,dtype=float);boundary=np.asarray(boundary,dtype=float)
    if boundary.shape!=(*phi.shape,4) or phi.ndim!=3 or not np.isfinite(phi).all() or not np.isfinite(boundary).all():
        raise ValueError('Matching finite signed interface and boundary required')
    types=np.rint(boundary[...,3]).astype(int)
    if (not np.isin(types,[0,1,2,3]).all() or
            np.any((types==0)&(phi>=0)) or np.any((types==2)&(phi<0))):
        raise ValueError('Fluid/air classification must agree with the supplied interface')
    wet=(types==0)|((types==3)&(phi<0))
    air=(types==2)|((types==3)&(phi>=0))
    weights=np.ones((*phi.shape,3))
    for c in range(3):
        pm,pp=shift(phi,-1,2-c),shift(phi,1,2-c)
        left=shift(wet,-1,2-c)&shift(air,1,2-c)
        right=shift(air,-1,2-c)&shift(wet,1,2-c)
        for selected,water,empty in ((left,pm,pp),(right,pp,pm)):
            # No empirical lower theta clamp: near-interface conditioning is
            # visible to the linear solver and convergence checks.
            weights[...,c][selected]=(empty[selected]-water[selected])/(-water[selected])
    if not np.isfinite(weights).all() or (weights<1).any():
        raise ValueError('Invalid liquid-to-interface pressure distance')
    return weights


def constrain_velocity(velocity, boundary):
    if velocity.shape[-1] != 3 or boundary.shape != (*velocity.shape[:-1], 4):
        raise ValueError('Matching XYZ velocity and XYZ/type boundary arrays required')
    if not np.isfinite(velocity).all() or not np.isfinite(boundary).all():
        raise ValueError('Finite input fields required')
    types = np.rint(boundary[..., 3]).astype(int)
    if not np.isin(types, [0, 1, 2, 3]).all():
        raise ValueError('Unknown boundary classification')
    solid = types == 1
    fixed = velocity.copy()
    mobility = np.ones_like(velocity)
    for component in range(3):
        # Match installed projection's priority when both adjacent cells solid.
        for offset in ((1, -1) if component == 2 else (-1, 1)):
            neighbor = shift(boundary, offset, 2-component)
            wall = np.rint(neighbor[..., 3]) == 1
            fixed[..., component] = np.where(wall, neighbor[..., component], fixed[..., component])
            mobility[..., component][wall] = 0
    fixed[solid] = boundary[..., :3][solid]
    mobility[solid] = 0
    return fixed, mobility, types == 0


def project(velocity, boundary, spacing=(32.8125, 32.8125, 800/24), dt=1/60,
            max_iterations=600, tolerance=1e-7, boundary_pressure=None, free_surface_phi=None,
            target_divergence=None):
    spacing = np.asarray(spacing, dtype=float)
    if spacing.shape != (3,) or not np.isfinite(spacing).all() or (spacing <= 0).any() or not np.isfinite(dt) or dt <= 0:
        raise ValueError('Finite positive cell dimensions and time step required')
    fixed, mobility, fluid = constrain_velocity(velocity, boundary)
    gradient_weights=(np.ones_like(mobility) if free_surface_phi is None else
                      surface_gradient_weights(boundary,free_surface_phi))
    pressure_mobility=mobility*gradient_weights
    stage = np.rint(boundary[..., 3]) == 3
    if boundary_pressure is None:
        if stage.any():
            raise ValueError('External stage cells require prescribed pressure')
        boundary_pressure = np.zeros(fluid.shape)
    boundary_pressure = np.asarray(boundary_pressure, dtype=float)
    if boundary_pressure.shape != fluid.shape or not np.isfinite(boundary_pressure).all() or np.any(boundary_pressure[~stage] != 0):
        raise ValueError('Finite pressure on external stage cells only required')
    if free_surface_phi is not None and np.any(stage & (np.asarray(free_surface_phi)>=0) & (boundary_pressure!=0)):
        raise ValueError('Atmospheric external-stage air must have zero gauge pressure')
    before = divergence(fixed, spacing)
    target=np.zeros_like(before) if target_divergence is None else np.asarray(target_divergence,float)
    if target.shape!=before.shape or not np.isfinite(target).all() or np.any(target[~fluid]!=0):
        raise ValueError('Finite target divergence on fluid pressure DOFs only required')
    rhs = np.where(fluid, (target-before)/dt+divergence(pressure_mobility*gradient(boundary_pressure, spacing), spacing), 0.)

    def matrix(p):
        p = np.where(fluid, p, 0.)
        return np.where(fluid, -divergence(pressure_mobility*gradient(p, spacing), spacing), 0.)

    diagonal = sum((shift(pressure_mobility[..., c], 1, 2-c)+shift(pressure_mobility[..., c], -1, 2-c))/(4*h*h)
                   for c, h in enumerate(spacing))
    unsupported = fluid & (diagonal == 0) & (abs(rhs) > tolerance)
    if unsupported.any():
        raise ValueError(f'{unsupported.sum()} fluid cells have incompatible fixed flux and no pressure DOF')
    inverse = np.divide(1., diagonal, out=np.zeros_like(diagonal), where=fluid & (diagonal > 0))
    pressure = np.zeros_like(rhs)
    residual = rhs.copy()
    z = inverse*residual
    direction = z.copy()
    rz = float(np.sum(residual*z))
    initial_norm = float(np.linalg.norm(rhs))
    history = []
    for iteration in range(max_iterations):
        relative = float(np.linalg.norm(residual))/max(initial_norm, 1e-30)
        if iteration % 20 == 0:
            history.append(dict(iteration=iteration, relative_residual=relative))
        if relative <= tolerance:
            break
        ad = matrix(direction)
        denominator = float(np.sum(direction*ad))
        if denominator <= 0 or not np.isfinite(denominator):
            raise ValueError('Pressure matrix lost positive semidefiniteness or has incompatible nullspace')
        alpha = rz/denominator
        pressure += alpha*direction
        residual -= alpha*ad
        z = inverse*residual
        next_rz = float(np.sum(residual*z))
        direction = z+(next_rz/rz)*direction
        rz = next_rz
    updated = fixed-dt*pressure_mobility*gradient(pressure+boundary_pressure, spacing)
    after = divergence(updated, spacing)
    actual_residual = rhs-matrix(pressure)
    relative = float(np.linalg.norm(actual_residual))/max(initial_norm, 1e-30)
    rms = lambda a: float(np.sqrt(np.mean(a*a)))
    report = dict(iterations=iteration+1, relative_pressure_residual=relative,
                  fluid_cells=int(fluid.sum()), divergence_before_rms_per_s=rms(before[fluid]),
                  divergence_after_rms_per_s=rms(after[fluid]),
                  max_divergence_after_per_s=float(abs(after[fluid]).max()),
                  maximum_fixed_velocity_change_cm_s=float(abs(updated-fixed)[mobility == 0].max(initial=0.)),
                  pressure_min=float(pressure.min()), pressure_max=float(pressure.max()),
                  history=history, converged=relative <= tolerance,
                  method='collocated matrix-free PCG of -D M W G, anisotropic spacing' if free_surface_phi is not None else
                         'collocated matrix-free PCG of -D M G, anisotropic spacing',
                  current_interface_supplied=free_surface_phi is not None,
                  target_divergence_supplied=target_divergence is not None,
                  target_divergence_rms_error=rms((after-target)[fluid]),
                  maximum_free_surface_gradient_weight=float(gradient_weights.max()),
                  production_promoted=False, cpu_reference_only=True)
    return updated, pressure+boundary_pressure, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grid_directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--stage-profile', type=Path)
    parser.add_argument('--input-velocity', choices=('Velocity', 'StartVelocity'), default='Velocity',
        help='StartVelocity evaluates the same pre-projection transfer as the GPU; Velocity reprojects its final result')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    fields = load_fields(args.grid_directory)
    boundary = fields['SolidVelocity_Boundary'].copy()
    external = None
    if args.stage_profile:
        from liquid_outlet_stage import outlet_pressure_grid
        known, external = outlet_pressure_grid(json.loads(args.stage_profile.read_text()))
        boundary[known, 3] = 3
    velocity, pressure, report = project(fields[args.input_velocity], boundary, boundary_pressure=external)
    report['input_velocity_attribute'] = args.input_velocity
    report['boundary_replaced_for_stage_reference'] = bool(args.stage_profile)
    report['source_grid_directory'] = str(args.grid_directory)
    args.output.mkdir(parents=True)
    np.savez_compressed(args.output/'projected_fields.npz', velocity=velocity, pressure=pressure)
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report, indent=2, allow_nan=False))
