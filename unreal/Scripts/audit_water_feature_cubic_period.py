"""Full-period/refinement trials using all-row cubic quadratic-pressure solve.

Same unchanged physical gates. First 20 coarse steps compared against the
qualified full-SVD trajectory; no pressure modes discarded by the fast solve.
Both meshes target 1.2 seconds, stop on first failed candidate and preserve it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_cubic_fast import CubicMaterialFast


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('audit', 'qualified', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit, qualified = (json.loads(p.read_text()) for p in (args.audit, args.qualified))
    pins = {str(args.audit.resolve()): digest(args.audit), str(args.qualified.resolve()): digest(args.qualified),
            **qualified['dependency_sha256']}
    for name in ('audit_water_feature_cubic_period.py', 'water_feature_cubic_fast.py'):
        path = Path(__file__).with_name(name); pins[str(path.resolve())] = digest(path)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualified cubic predecessor changed')
    baseline = next(r for r in audit['runs'] if r['label'] == 'cubic-p2-regular-n2')
    q = next(r for r in qualified['runs'] if r['label'] == baseline['label'])
    if not q['preliminary_motion_gate_passed'] or q['all_completed_steps_checked'] != 20:
        raise ValueError('Qualified entire 20-step full-SVD predecessor required')
    old = {k: np.load(p, allow_pickle=False) for k, p in baseline['arrays'].items()}
    args.output.mkdir(); outputs = {}; runs = []; started = time.perf_counter()
    for n in (2, 3):
        label = f'cubic-fast-n{n}-period'; v, t = tank_mesh(n); m = CubicMaterialFast(v, t, pressure_degree=2)
        x = m.positions.copy(); x[:, 2] += x[:, 2]/.5*.02*np.cos(np.pi*x[:, 0]); m.initialize_material(x); m.tank_slip_walls()
        if n == 2:
            for name, actual in dict(positions=x, scalar_material_mass=m.scalar_mass, cells=m.cells,
                                    vertex_cells=m.vertex_cells, pressure_cells=m.pressure_cells, fixed=m.fixed).items():
                expected = old[name][0] if name == 'positions' else old[name]
                if not np.array_equal(actual, expected):
                    raise ValueError('Coarse actual initial material differs from SVD baseline: '+name)
        initial_energy = m.energy(x, m.velocities, np.array([0., 0., -9.80665])); initial_volume = m.volume(x)
        positions = [x.copy()]; velocities = [m.velocities.copy()]; pressures = [np.zeros(m.pressure_nodes)]; proofs = []
        dt = .004; steps = 300; failure = None; begin = time.perf_counter()
        agreement = dict(steps_checked=0, maximum_position_difference_m=0., maximum_velocity_difference_m_s=0.,
                         maximum_pressure_coefficient_difference_pa=0., maximum_relative_pressure_comparison=0.)
        for step in range(steps):
            before_x, before_u = m.positions.copy(), m.velocities.copy()
            try:
                pressure, proof = m.step(dt)
            except Exception as error:
                failure = dict(kind='integration_failure', step=step+1, physical_time_s=step*dt,
                    exception=type(error).__name__, message=str(error),
                    failed_step_positions_unchanged=bool(np.array_equal(before_x, m.positions)),
                    failed_step_velocities_unchanged=bool(np.array_equal(before_u, m.velocities)))
                print('CUBIC_PERIOD_FAILED', label, failure, flush=True); break
            actual_p = m.pressure_basis@pressure[m.pressure_cells].T
            proof.update(pressure_coefficient_min_pa=float(pressure.min()), pressure_coefficient_max_pa=float(pressure.max()),
                         quadrature_pressure_min_pa=float(actual_p.min()), quadrature_pressure_max_pa=float(actual_p.max()))
            positions.append(m.positions.copy()); velocities.append(m.velocities.copy()); pressures.append(pressure); proofs.append(proof)
            if n == 2 and step < 20:
                xe = float(np.max(np.abs(m.positions-old['positions'][step+1])))
                ue = float(np.max(np.abs(m.velocities-old['velocities'][step+1])))
                pe = float(np.max(np.abs(pressure-old['pressures'][step+1])))
                comparison = float(np.max(np.abs(pressure-old['pressures'][step+1])/(3e-6+3e-8*np.abs(old['pressures'][step+1]))))
                agreement['steps_checked'] += 1
                agreement['maximum_position_difference_m'] = max(agreement['maximum_position_difference_m'], xe)
                agreement['maximum_velocity_difference_m_s'] = max(agreement['maximum_velocity_difference_m_s'], ue)
                agreement['maximum_pressure_coefficient_difference_pa'] = max(agreement['maximum_pressure_coefficient_difference_pa'], pe)
                agreement['maximum_relative_pressure_comparison'] = max(agreement['maximum_relative_pressure_comparison'], comparison)
                if xe > 2e-12 or ue > 2e-10 or comparison > 1:
                    failure = dict(kind='original_full_svd_comparison_failure', step=step+1, position_difference_m=xe,
                        velocity_difference_m_s=ue, pressure_comparison=comparison, candidate_geometry_and_velocity_retained=True)
                    print('CUBIC_PERIOD_SOLVE_COMPARISON_FAILED', label, failure, flush=True); break
            error = max(abs(proof['bernstein_density_ratio_lower']-1), abs(proof['bernstein_density_ratio_upper']-1))
            if (step+1) % 10 == 0:
                print('CUBIC_PERIOD', label, step+1, steps, error, proof['quadrature_pressure_min_pa'],
                      proof['quadrature_pressure_max_pa'], time.perf_counter()-begin, flush=True)
            if error > .01:
                failure = dict(kind='preliminary_density_gate_failure', step=step+1, physical_time_s=(step+1)*dt,
                    bounded_density_error=error, fixed_allowance=.01, candidate_geometry_and_velocity_retained=True,
                    not_an_atomic_integration_failure=True)
                print('CUBIC_PERIOD_DENSITY_REJECTED', label, failure, flush=True); break
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
        runs.append(dict(label=label, refinement=n, barycentric_split=False, velocity_degree=3, pressure_degree=2,
            pressure_mode=m.pressure_mode, dt_s=dt, amplitude_m=.02, requested_duration_s=1.2,
            requested_steps=steps, completed_steps=len(proofs), arrays=arrays, proofs=proofs, failure=failure,
            finite_trial_completed=len(proofs) == steps, preliminary_motion_gate_passed=passed,
            maximum_bounded_density_error=rho_error, maximum_global_volume_error_m3=volume_error,
            maximum_energy_error_j=energy_error, full_svd_prefix_comparison=agreement if n == 2 else None,
            material_mass_kg=m.material_mass, maximum_motion_m=float(np.max(np.abs(m.positions-x))),
            total_seconds=time.perf_counter()-begin, accepted=False))
        print('CUBIC_PERIOD_TERMINAL', label, len(proofs), steps, passed, flush=True)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Full-period cubic trials changed preserved data')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, outputs_sha256=outputs, runs=runs,
        fixed_preliminary_density_allowance=.01, fixed_volume_allowance_m3=1e-10, fixed_energy_allowance_j=1e-8,
        openblas_threads_environment=os.environ.get('OPENBLAS_NUM_THREADS'), total_seconds=time.perf_counter()-started,
        scope='Both refinements target full 1.2 s motion under unchanged density gates and original all-row solve equations. All failed states retained. Not feature/pressure stability/convergence/animation acceptance.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
