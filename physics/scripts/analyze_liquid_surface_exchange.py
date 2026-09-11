"""Measure the rendered SDF's wet exchange aperture and matching grid velocity.

This is geometric/velocity evidence, not calibrated liquid mass or an integrated
conservation budget. The SDF iso-surface is the one used by the actual renderer.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_outlet_stage import outlet_pressure_grid


def sample_grid(array, points, minimum=(-1115.625, -1115.625, 350.), extent=(2231.25, 2231.25, 800.)):
    """Trilinear cell-centred grid sampling, XYZ points and ZYXC storage."""
    array = np.asarray(array, dtype=float)
    points = np.asarray(points, dtype=float)
    if array.ndim != 4 or points.shape[-1] != 3 or not np.isfinite(points).all() or not np.isfinite(array).all():
        raise ValueError('Finite ZYXC grid and XYZ points required')
    size = np.asarray(array.shape[:3][::-1])
    index = (points-np.asarray(minimum))/np.asarray(extent)*size-.5
    index = np.clip(index, 0, size-1)
    lower = np.floor(index).astype(int)
    fraction = index-lower
    result = np.zeros((*points.shape[:-1], array.shape[-1]))
    for z in (0, 1):
        for y in (0, 1):
            for x in (0, 1):
                offset = np.array([x, y, z])
                address = np.minimum(lower+offset, size-1)
                weight = np.prod(np.where(offset, fraction, 1-fraction), axis=-1)
                result += weight[..., None]*array[address[..., 2], address[..., 1], address[..., 0]]
    return result


def wet_column_integrals(z, sdf, velocity, bed):
    """Integrate piecewise-linear velocity on negative-SDF intervals above bed.

    All dimensions are cm, cm/s. Returns wet depth in cm, normal integral in
    cm²/s and highest liquid height in cm. Disconnected intervals are included,
    not silently interpreted as one solid column of water.
    """
    z, sdf, velocity, bed = (np.asarray(a, dtype=float) for a in (z, sdf, velocity, bed))
    if z.ndim != 1 or len(z) < 2 or sdf.ndim != 2 or sdf.shape != velocity.shape or sdf.shape[0] != len(z) or bed.shape != sdf.shape[1:]:
        raise ValueError('Ordered Z samples and matching Z-by-column fields required')
    if not all(np.isfinite(a).all() for a in (z, sdf, velocity, bed)) or np.any(np.diff(z) <= 0):
        raise ValueError('Finite fields and strictly increasing heights required')
    a, b = sdf[:-1], sdf[1:]
    z0, z1 = z[:-1, None], z[1:, None]
    crossing = z0+np.divide(a, a-b, out=np.zeros_like(a), where=a != b)*(z1-z0)
    lower = np.where(a < 0, z0, crossing)
    upper = np.where(b < 0, z1, crossing)
    lower = np.maximum(lower, bed[None, :])
    length = np.where((a < 0) | (b < 0), np.maximum(upper-lower, 0.), 0.)
    mid = (lower+upper)*.5
    speed = velocity[:-1]+(velocity[1:]-velocity[:-1])*(mid-z0)/(z1-z0)
    depth = length.sum(axis=0)
    flux = (speed*length).sum(axis=0)
    top = np.max(np.where(length > 0, upper, -np.inf), axis=0)
    return depth, flux, top


def audit_surface_exchange(fields, profile, plane_inset_cm=0.):
    outlet_pressure_grid(profile)
    if not np.isfinite(plane_inset_cm) or not 0 <= plane_inset_cm <= 100:
        raise ValueError('Diagnostic plane inset must be finite and within 0..100 cm')
    sdf = fields['SDF']
    velocity = fields['Velocity']
    if sdf.shape != (48, 136, 136, 1) or velocity.shape != (24, 68, 68, 3):
        raise ValueError('Registered SDF and solver dimensions required')
    packed = np.asarray(profile['packed_vectors'], dtype=float)
    # Union of both grids' centres preserves both linear interpolants in Z.
    z = np.unique(np.r_[350., 1150., 350+(np.arange(48)+.5)*800/48,
                       350+(np.arange(24)+.5)*800/24])
    along = (np.arange(64)+.5)*2100/64-1050
    zz, aa = np.meshgrid(z, along, indexing='ij')
    faces = []
    for index, (name, axis, coordinate, inward) in enumerate([
            ('west', 0, -1050., 1), ('east', 0, 1050., -1),
            ('south', 1, -1050., 1), ('north', 1, 1050., -1)]):
        rows = packed[4+index*64:4+(index+1)*64]
        coordinate += inward*plane_inset_cm
        points = np.stack([np.full_like(aa, coordinate), aa, zz] if axis == 0 else
                          [aa, np.full_like(aa, coordinate), zz], axis=-1)
        distance = sample_grid(sdf, points)[..., 0]
        normal = inward*sample_grid(velocity, points)[..., axis]
        depth, integrated, top = wet_column_integrals(z, distance, normal, rows[:, 0])
        measured = depth > 0
        native_wet = rows[:, 1] > rows[:, 0]
        # A highest surface can belong to a detached fragment. Record that
        # limitation; do not use it as an unqualified hydrostatic head.
        difference = (top-rows[:, 1])/100
        groups = {}
        for label, selected in [('all', measured & native_wet),
                ('native_incoming', measured & native_wet & (rows[:, 2] >= 0)),
                ('native_outgoing', measured & native_wet & (rows[:, 2] < 0))]:
            values = difference[selected]
            groups[label] = dict(columns=int(selected.sum()),
                mean_m=float(values.mean()) if len(values) else None,
                p10_m=float(np.quantile(values, .1)) if len(values) else None,
                p90_m=float(np.quantile(values, .9)) if len(values) else None)
        faces.append(dict(face=name,
            sdf_wet_area_above_profile_bed_m2=float(depth.sum()*(2100/64)/10000),
            sdf_aperture_velocity_inward_m3s=float(integrated.sum()*(2100/64)/1e6),
            native_wet_columns_without_sdf_liquid=int((native_wet & ~measured).sum()),
            sdf_liquid_columns_above_native_dry_profile=int((~native_wet & measured).sum()),
            liquid_reaches_top_of_grid_columns=int((distance[-1] < 0).sum()),
            highest_sdf_surface_minus_native_stage=groups,
            column_depth_cm=depth.tolist(), column_normal_integral_cm2s=integrated.tolist(),
            highest_sdf_surface_cm=[float(v) if np.isfinite(v) else None for v in top]))
    return dict(method='trilinear rendered SDF aperture and collocated velocity; linear-Z wet interval quadrature',
        faces=faces, sdf_aperture_net_inward_m3s=sum(f['sdf_aperture_velocity_inward_m3s'] for f in faces),
        horizontal_samples_per_face=64, vertical_knots=len(z),
        plane_inset_cm=plane_inset_cm,
        inset_uses_original_boundary_bed_and_stage_reference=plane_inset_cm != 0,
        includes_disconnected_liquid_intervals=True, boundary_bed='native profile samples from captured/inferred mesh',
        physical_volume_calibrated=False, time_integrated_mass_budget=False, production_promoted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grids', type=Path)
    parser.add_argument('profile', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--inset-cm', type=float, default=0.)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit_surface_exchange(load_fields(args.grids), json.loads(args.profile.read_text()), args.inset_cm)
    result['source_grids'] = str(args.grids)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({**result, 'faces': [{k: v for k, v in f.items() if not k.startswith('column_') and k != 'highest_sdf_surface_cm'} for f in result['faces']]}, indent=2))
