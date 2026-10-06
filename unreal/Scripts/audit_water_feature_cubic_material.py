"""Recorded cubic geometry/velocity pressure-space experiments, including failures."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_cubic_material import CubicMaterial, barycentric_split


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    prior = json.loads(args.prior.read_text())
    pins = {str(args.prior.resolve()): digest(args.prior), **prior['dependency_sha256']}
    for name in ('audit_water_feature_cubic_material.py', 'water_feature_cubic_material.py', 'water_feature_moving_tetra.py', 'water_feature_rt0_step.py'):
        path = Path(__file__).with_name(name); pins[str(path.resolve())] = digest(path)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualified rejected period/preserved controls changed')
    args.output.mkdir(); runs = []; outputs = {}; started = time.perf_counter()
    cases = [('cubic-p1-regular-n2', 2, False, 1, .08), ('cubic-p2-regular-n2', 2, False, 2, .08),
             ('cubic-p2-bary-n1-period', 1, True, 2, 1.2)]
    for label, n, split, degree, duration in cases:
        begin = time.perf_counter(); v, t = tank_mesh(n)
        if split:
            v, t = barycentric_split(v, t)
        m = CubicMaterial(v, t, pressure_degree=degree)
        x = m.positions.copy(); x[:, 2] += x[:, 2]/.5*.02*np.cos(np.pi*x[:, 0]); m.initialize_material(x); m.tank_slip_walls()
        positions = [x.copy()]; velocities = [m.velocities.copy()]; pressures = [np.zeros(m.pressure_nodes)]
        initial_energy = m.energy(x, m.velocities, np.array([0., 0., -9.80665])); initial_volume = m.volume(x)
        proofs = []; failure = None; dt = .004; steps = round(duration/dt)
        for step in range(steps):
            before_x, before_u = m.positions.copy(), m.velocities.copy()
            try:
                pressure, proof = m.step(dt)
            except Exception as error:
                failure = dict(kind='integration_failure', step=step+1, physical_time_s=step*dt,
                    exception=type(error).__name__, message=str(error),
                    failed_step_positions_unchanged=bool(np.array_equal(before_x, m.positions)),
                    failed_step_velocities_unchanged=bool(np.array_equal(before_u, m.velocities)))
                print('CUBIC_TRIAL_FAILED', label, failure, flush=True); break
            actual_pressure = np.einsum('qi,ti->tq', m.pressure_basis, pressure[m.pressure_cells])
            proof.update(pressure_coefficient_min_pa=float(pressure.min()), pressure_coefficient_max_pa=float(pressure.max()),
                quadrature_pressure_min_pa=float(actual_pressure.min()), quadrature_pressure_max_pa=float(actual_pressure.max()))
            positions.append(m.positions.copy()); velocities.append(m.velocities.copy()); pressures.append(pressure); proofs.append(proof)
            error = max(abs(proof['bernstein_density_ratio_lower']-1), abs(proof['bernstein_density_ratio_upper']-1))
            if (step+1) % 10 == 0:
                print('CUBIC_TRIAL', label, step+1, steps, error, proof['quadrature_pressure_min_pa'],
                      proof['quadrature_pressure_max_pa'], time.perf_counter()-begin, flush=True)
            if error > .01:
                failure = dict(kind='preliminary_density_gate_failure', step=step+1, physical_time_s=(step+1)*dt,
                    bounded_density_error=error, fixed_allowance=.01, candidate_geometry_and_velocity_retained=True,
                    not_an_atomic_integration_failure=True)
                print('CUBIC_DENSITY_REJECTED', label, failure, flush=True); break
        saved = dict(positions=np.array(positions), velocities=np.array(velocities), pressures=np.array(pressures),
            times=np.arange(len(positions))*dt, cells=m.cells, vertex_cells=m.vertex_cells, pressure_cells=m.pressure_cells,
            scalar_material_mass=m.scalar_mass, fixed=m.fixed)
        arrays = {}
        for name, array in saved.items():
            path = args.output/(label+'-'+name+'.npy')
            with path.open('xb') as stream:
                np.save(stream, array, allow_pickle=False)
            arrays[name] = str(path.resolve()); outputs[str(path.resolve())] = digest(path)
        rho_error = max((max(abs(p['bernstein_density_ratio_lower']-1), abs(p['bernstein_density_ratio_upper']-1)) for p in proofs), default=0.)
        volume_error = max((abs(p['volume_m3']-initial_volume) for p in proofs), default=0.)
        energy_error = max((abs(p['energy_j']-initial_energy) for p in proofs), default=0.)
        passed = failure is None and len(proofs) == steps and rho_error <= .01 and volume_error <= 1e-10 and energy_error <= 1e-8
        runs.append(dict(label=label, refinement=n, barycentric_split=split, velocity_degree=3,
            pressure_degree=degree, pressure_mode=m.pressure_mode, dt_s=dt, amplitude_m=.02,
            requested_duration_s=duration, completed_steps=len(proofs), requested_steps=steps, arrays=arrays, proofs=proofs,
            failure=failure, finite_trial_completed=len(proofs) == steps, preliminary_motion_gate_passed=passed,
            maximum_bounded_density_error=rho_error, maximum_global_volume_error_m3=volume_error,
            maximum_energy_error_j=energy_error, material_mass_kg=m.material_mass,
            maximum_motion_m=float(np.max(np.abs(m.positions-x))), total_seconds=time.perf_counter()-begin, accepted=False))
        print('CUBIC_TRIAL_TERMINAL', label, len(proofs), steps, passed, flush=True)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Cubic experiment modified preserved inputs')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, outputs_sha256=outputs, runs=runs,
        fixed_preliminary_density_allowance=.01, fixed_volume_allowance_m3=1e-10, fixed_energy_allowance_j=1e-8,
        total_seconds=time.perf_counter()-started,
        scope='Cubic moving-material pressure-space experiments under unchanged density gate. Includes first failed candidates; no easier-mesh feature acceptance or animation.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
