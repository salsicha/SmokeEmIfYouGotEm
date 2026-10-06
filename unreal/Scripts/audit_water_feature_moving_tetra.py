"""Recorded weak/local moving liquid trials, including rejected controls.

Preserves every computed step; no engine bake. New authored tiny tank geometry,
not an old native checkpoint repair. Gates remain fixed across refinements.
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
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    prior = json.loads(args.prior.read_text()); pins = {str(args.prior.resolve()): digest(args.prior),
        **prior['dependency_sha256'], **prior.get('outputs_sha256', {})}
    for name in (Path(__file__).name, 'water_feature_moving_tetra.py', 'water_feature_rt0_step.py'):
        p = Path(__file__).with_name(name); pins[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Preserved preceding pressure/motion evidence changed')
    args.output.mkdir(); outputs = {}; runs = []; started = time.perf_counter()
    cases = [('weak-n2-dt004', 2, .004, 'continuous_p1'), ('local-n2-dt004', 2, .004, 'discontinuous_p1'),
             ('local-n2-dt002', 2, .002, 'discontinuous_p1'), ('local-n3-dt002', 3, .002, 'discontinuous_p1')]
    for label, n, dt, mode in cases:
        begin = time.perf_counter(); v, t = tank_mesh(n); m = MovingLiquid(v, t, pressure_mode=mode)
        x = m.positions.copy(); x[:, 2] += x[:, 2]/.5*.02*np.cos(np.pi*x[:, 0]); m.initialize_material(x); m.tank_slip_walls()
        initial_energy = m.energy(x, m.velocities, np.array([0., 0., -9.80665])); initial_volume = m.volume(x)
        positions = [x.copy()]; velocities = [m.velocities.copy()]; pressures = [np.zeros(m.pressure_nodes)]; proofs = []; failure = None
        steps = round(.4/dt)
        for step in range(steps):
            before_x, before_u = m.positions.copy(), m.velocities.copy()
            try:
                pressure, proof = m.step(dt)
            except Exception as error:
                failure = dict(step=step+1, physical_time_s=step*dt, exception=type(error).__name__, message=str(error),
                    failed_step_positions_unchanged=bool(np.array_equal(before_x, m.positions)),
                    failed_step_velocities_unchanged=bool(np.array_equal(before_u, m.velocities)))
                print('MOVING_TRIAL_FAILED', label, failure, flush=True); break
            positions.append(m.positions.copy()); velocities.append(m.velocities.copy()); pressures.append(pressure); proofs.append(proof)
            if (step+1) % 10 == 0:
                print('MOVING_TRIAL', label, step+1, steps, proof['bernstein_density_ratio_lower'],
                      proof['bernstein_density_ratio_upper'], proof['maximum_point_divergence_per_second'],
                      time.perf_counter()-begin, flush=True)
        arrays = {}
        saved = dict(positions=np.array(positions), velocities=np.array(velocities), pressures=np.array(pressures),
            times=np.arange(len(positions))*dt, cells=m.cells, vertex_cells=m.vertex_cells, pressure_cells=m.pressure_cells,
            scalar_material_mass=m.scalar_mass, fixed=m.fixed)
        for name, array in saved.items():
            p = args.output/(label+'-'+name+'.npy')
            with p.open('xb') as stream:
                np.save(stream, array, allow_pickle=False)
            arrays[name] = str(p.resolve()); outputs[str(p.resolve())] = digest(p)
        rho_error = max([max(abs(p['bernstein_density_ratio_lower']-1), abs(p['bernstein_density_ratio_upper']-1)) for p in proofs], default=0.)
        volume_error = max([abs(p['volume_m3']-initial_volume) for p in proofs], default=0.)
        energy_error = max([abs(p['energy_j']-initial_energy) for p in proofs], default=0.)
        passed = failure is None and rho_error <= .01 and volume_error <= 1e-10 and energy_error <= 1e-8
        runs.append(dict(label=label, refinement=n, pressure_mode=mode, dt_s=dt, amplitude_m=.02,
            requested_duration_s=.4, completed_steps=len(proofs), requested_steps=steps, arrays=arrays, proofs=proofs,
            failure=failure, finite_trial_completed=failure is None, preliminary_motion_gate_passed=passed,
            maximum_bounded_density_error=rho_error, maximum_global_volume_error_m3=volume_error,
            maximum_energy_error_j=energy_error, material_mass_kg=m.material_mass,
            maximum_motion_m=float(np.max(np.abs(m.positions-x))), total_seconds=time.perf_counter()-begin,
            accepted=False))
        print('MOVING_TRIAL_COMPLETE', label, passed, rho_error, time.perf_counter()-begin, flush=True)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Recorded trials changed preserved work')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, outputs_sha256=outputs, runs=runs,
        fixed_preliminary_density_allowance=.01, fixed_volume_allowance_m3=1e-10, fixed_energy_allowance_j=1e-8,
        total_seconds=time.perf_counter()-started,
        scope='Full recorded moving 3D quadratic-tetrahedral trials, including weak-density rejection and local refinement outcomes. Not inf-sup/convergence/feature/animation acceptance. No original engine cache, emitter or primary-particle advance.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
