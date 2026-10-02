"""Continue qualified finest material state toward a full tank oscillation.

No re-authoring of material mass, resetting density, replaying the prefix or
relaxing density/volume/energy gates. Preserve the first failed candidate and
stop; an observation timeout must never restart this owned worker.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_moving_tetra import MovingLiquid


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
            str(Path(__file__).resolve()): digest(__file__), **qualified['dependency_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualified material checkpoint changed')
    row = next(r for r in audit['runs'] if r['label'] == 'local-n3-dt002')
    q = next(r for r in qualified['runs'] if r['label'] == row['label'])
    if not q['preliminary_motion_gate_passed'] or q['all_completed_steps_checked'] != row['requested_steps']:
        raise ValueError('Finest complete independently qualified prefix required')
    arrays = {name: np.load(path, allow_pickle=False) for name, path in row['arrays'].items()}
    v, t = tank_mesh(row['refinement']); m = MovingLiquid(v, t, pressure_mode=row['pressure_mode'])
    # Restore immutable initial material before any motion, then the saved state.
    m.initialize_material(arrays['positions'][0]); m.tank_slip_walls()
    for key, actual in dict(cells=m.cells, vertex_cells=m.vertex_cells, pressure_cells=m.pressure_cells,
                            scalar_material_mass=m.scalar_mass, fixed=m.fixed).items():
        if not np.array_equal(actual, arrays[key]):
            raise ValueError('Checkpoint topology/material/walls do not reproduce exactly: '+key)
    m.positions = arrays['positions'][-1].copy(); m.velocities = arrays['velocities'][-1].copy(); m.steps = row['completed_steps']
    positions = list(arrays['positions']); velocities = list(arrays['velocities']); pressures = list(arrays['pressures'])
    proofs = list(row['proofs']); dt = row['dt_s']; requested_duration = 1.2; requested_steps = round(requested_duration/dt)
    initial_energy = m.energy(m.reference_positions, arrays['velocities'][0], np.array([0., 0., -9.80665]))
    initial_volume = m.volume(m.reference_positions); initial_steps = len(proofs); failure = None
    args.output.mkdir(); started = time.perf_counter()
    for step in range(initial_steps, requested_steps):
        before_x, before_u = m.positions.copy(), m.velocities.copy()
        try:
            pressure, proof = m.step(dt)
        except Exception as error:
            failure = dict(kind='integration_failure', step=step+1, physical_time_s=step*dt,
                exception=type(error).__name__, message=str(error),
                failed_step_positions_unchanged=bool(np.array_equal(before_x, m.positions)),
                failed_step_velocities_unchanged=bool(np.array_equal(before_u, m.velocities)))
            print('PERIOD_EXTENSION_FAILED', failure, flush=True); break
        positions.append(m.positions.copy()); velocities.append(m.velocities.copy()); pressures.append(pressure); proofs.append(proof)
        density_error = max(abs(proof['bernstein_density_ratio_lower']-1), abs(proof['bernstein_density_ratio_upper']-1))
        if (step+1) % 10 == 0:
            print('PERIOD_EXTENSION', step+1, requested_steps, (step+1)*dt,
                  density_error, proof['maximum_point_divergence_per_second'], time.perf_counter()-started, flush=True)
        if density_error > audit['fixed_preliminary_density_allowance']:
            failure = dict(kind='preliminary_density_gate_failure', step=step+1, physical_time_s=(step+1)*dt,
                message='First retained computed candidate exceeds unchanged whole-cell density bound allowance',
                bounded_density_error=density_error, fixed_allowance=audit['fixed_preliminary_density_allowance'],
                candidate_geometry_and_velocity_retained=True,
                not_an_atomic_integration_failure=True)
            print('PERIOD_EXTENSION_DENSITY_REJECTED', failure, flush=True); break
    outputs = {}; paths = {}
    saved = dict(positions=np.array(positions), velocities=np.array(velocities), pressures=np.array(pressures),
        times=np.arange(len(positions))*dt, cells=m.cells, vertex_cells=m.vertex_cells,
        pressure_cells=m.pressure_cells, scalar_material_mass=m.scalar_mass, fixed=m.fixed)
    for name, array in saved.items():
        path = args.output/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        paths[name] = str(path.resolve()); outputs[str(path.resolve())] = digest(path)
    rho_error = max(max(abs(p['bernstein_density_ratio_lower']-1), abs(p['bernstein_density_ratio_upper']-1)) for p in proofs)
    volume_error = max(abs(p['volume_m3']-initial_volume) for p in proofs)
    energy_error = max(abs(p['energy_j']-initial_energy) for p in proofs)
    passed = failure is None and len(proofs) == requested_steps and rho_error <= .01 and volume_error <= 1e-10 and energy_error <= 1e-8
    extended = dict(row, label='local-n3-dt002-period', requested_duration_s=requested_duration,
        requested_steps=requested_steps, completed_steps=len(proofs), arrays=paths, proofs=proofs,
        failure=failure, finite_trial_completed=len(proofs) == requested_steps,
        preliminary_motion_gate_passed=passed, maximum_bounded_density_error=rho_error,
        maximum_global_volume_error_m3=volume_error, maximum_energy_error_j=energy_error,
        maximum_motion_m=float(np.max(np.abs(m.positions-m.reference_positions))), total_seconds=time.perf_counter()-started,
        preserved_prefix_steps=initial_steps, new_steps=len(proofs)-initial_steps, accepted=False)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Period extension changed its preserved checkpoint')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, outputs_sha256=outputs,
        runs=[extended], fixed_preliminary_density_allowance=.01, fixed_volume_allowance_m3=1e-10,
        fixed_energy_allowance_j=1e-8, total_seconds=time.perf_counter()-started,
        scope='Finest continuation from immutable qualified material prefix toward a full period. First failed state retained, not feature or visual acceptance.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('PERIOD_EXTENSION_TERMINAL', len(proofs), requested_steps, passed, flush=True)


if __name__ == '__main__':
    main()
