"""Compare pressure-solver conditioning on unchanged captured river states.

This is a fixed-state numerical diagnostic, not a replay, GPU cost measurement,
energy/geometry validation or playable-scene acceptance. No iteration increase.
"""
import argparse
import functools
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from audit_detail_wave_regime import read_snapshot
import total_depth_bank_replay as bank
from total_depth_nonlinear_pressure import AccelerationSystem, nonlinear_pressure_force


def compare(state, bed, dx):
    results, rates = {}, {}
    depth = state[..., 0]
    velocity = np.divide(state[..., 1:], depth[..., None], out=np.zeros_like(state[..., 1:]), where=depth[..., None] > 0)
    fastest = np.unravel_index(np.linalg.norm(velocity, axis=-1).argmax(), depth.shape)
    hydro_rate, _ = bank.rate(state, bed, dx, second_order=True)
    original = bank.nonlinear_pressure_force
    original_solve = AccelerationSystem.solve
    solve_details = []
    def observe_solve(system, rhs, *args, **kwargs):
        value, stats = original_solve(system, rhs, *args, **kwargs)
        residual = system.apply(value)-rhs
        acceleration_residual = residual*system.inv_root[..., None]
        magnitude = np.linalg.norm(acceleration_residual, axis=-1)
        index = np.unravel_index(magnitude.argmax(), magnitude.shape)
        solve_details.append(dict(length=system.length, maximum_acceleration_residual_mps2=float(magnitude[index]),
            worst_cell_yx=list(map(int, index)), worst_cell_depth_m=float(system.h[index]),
            maximum_normalized_residual=float(abs(residual).max()),
            minimum_wet_depth_m=float(system.h[system.h > 0].min())))
        return value, stats
    try:
        AccelerationSystem.solve = observe_solve
        for name, preconditioner, interpolation in (('diagonal', 'diagonal', 'centered'),
                ('block', 'block', 'centered'), ('depth_weighted', 'diagonal', 'depth_weighted')):
            solve_details = []
            bank.nonlinear_pressure_force = functools.partial(nonlinear_pressure_force, preconditioner=preconditioner)
            stats = {}
            started = time.perf_counter()
            rates[name], cfl = bank.rate(state, bed, dx, second_order=True, dispersive=True,
                pressure_model='rational_sgn', pressure_diagnostics=stats, pressure_interpolation=interpolation)
            results[name] = dict(pressure_solver=stats, local_residuals=solve_details,
                wall_seconds=time.perf_counter()-started, cfl_bound_s=cfl,
                fastest_cell_pressure_acceleration_mps2=((rates[name][fastest][1:]-hydro_rate[fastest][1:])/depth[fastest]).tolist())
    finally:
        bank.nonlinear_pressure_force = original
        AccelerationSystem.solve = original_solve
    results['maximum_rate_difference'] = np.max(abs(rates['block']-rates['diagonal']), axis=(0, 1)).tolist()
    results['mass_rate_exactly_equal'] = bool(np.array_equal(rates['block'][..., 0], rates['diagonal'][..., 0]))
    results['fastest_cell'] = dict(yx=list(map(int, fastest)), depth_m=float(depth[fastest]),
        bed_m=float(bed[fastest]), velocity_mps=velocity[fastest].tolist(),
        speed_mps=float(np.linalg.norm(velocity[fastest])))
    results['depth_weighted_mass_rate_exactly_equal'] = bool(np.array_equal(rates['depth_weighted'][..., 0], rates['diagonal'][..., 0]))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--states', type=Path, nargs='*', default=[])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    meta, arrays, hashes = read_snapshot(args.snapshot)
    if 'mean_geometry' not in arrays: raise ValueError('Paired actual bed geometry required')
    geometry, flow, detail = (arrays[k].astype(float) for k in ('mean_geometry', 'flow', 'state'))
    h = flow[..., 0]+detail[..., 0]
    initial = np.concatenate((h[..., None], h[..., None]*flow[..., 1:3]+detail[..., 1:3]), axis=-1)
    cases = [('initial', initial)]
    for path in args.states:
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        cases.append((str(path), np.load(path, allow_pickle=False)))
    files = ('audit_nonlinear_pressure_preconditioner.py', 'total_depth_bank_replay.py',
        'total_depth_nonlinear_pressure.py', 'finite_depth_pressure_reference.py')
    report = dict(schema='raftsim.nonlinear_pressure_preconditioner.v1', scope=__doc__,
        source_hashes=hashes, implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files},
        pressure_iterations=40, integrated=False, scene_accepted=False, cases=[])
    for name, state in cases:
        result = dict(state=name, comparison=compare(state, geometry[..., 0], meta['cell_m']))
        report['cases'].append(result)
        print(json.dumps(result), flush=True)
    with args.report.open('x') as output: json.dump(report, output, indent=2, allow_nan=False)


if __name__ == '__main__': main()
