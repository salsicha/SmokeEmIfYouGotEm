"""Check SGN acceleration against the actual FV update on fixed river states.

Uses the standard one-pole SGN closure so there is one physical acceleration.
The rational extension's two auxiliary pole accelerations are not individually
the actual total acceleration. This audit does not test energy stability,
breaking, GPU cost or playable acceptance, and never repairs its input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_detail_wave_regime import read_snapshot
from total_depth_nonlinear_pressure import AccelerationSystem, depth_weights, kinematic_terms


def compare(state, bed, dx):
    h = state[..., 0]
    u = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(state[..., 1:]), where=h[..., None] > 0)
    original_force, original_solve = bank.nonlinear_pressure_force, AccelerationSystem.solve
    result = {}
    for formulation in ('expanded', 'kinematic'):
        solved = []
        arguments = []
        def capture_force(*args, **kwargs):
            # mass/momentum rates alias bank's output; copy before pressure adds
            # to it so the observed input remains the exact pre-pressure rate.
            arguments.append((args[4], kwargs['mass_rate'].copy(), kwargs['momentum_rate'].copy(), args[3].copy()))
            return original_force(*args, **kwargs)
        def capture_solve(system, rhs, *args, **kwargs):
            value, stats = original_solve(system, rhs, *args, **kwargs)
            solved.append((value*system.inv_root[..., None], stats.copy()))
            return value, stats
        try:
            bank.nonlinear_pressure_force = capture_force
            AccelerationSystem.solve = capture_solve
            rate, _ = bank.rate(state, bed, dx, second_order=True, dispersive=True,
                pressure_model='sgn', pressure_interpolation='depth_weighted', pressure_formulation=formulation)
        finally:
            bank.nonlinear_pressure_force, AccelerationSystem.solve = original_force, original_solve
        pairs, mass_rate, momentum_rate, hydro_force = arguments[0]
        _, _, advective = kinematic_terms(h, bed, u, mass_rate, pairs, dx, depth_weights(h))
        base_force = momentum_rate-u*mass_rate[..., None] if formulation == 'kinematic' else hydro_force
        base = np.divide(base_force, h[..., None], out=np.zeros_like(u), where=h[..., None] > 0)
        if formulation == 'kinematic': base += advective
        solved_acceleration = base+solved[0][0]
        actual = np.divide(rate[..., 1:]-u*rate[..., 0, None], h[..., None],
            out=np.zeros_like(u), where=h[..., None] > 0)+advective
        mismatch = np.linalg.norm(actual-solved_acceleration, axis=-1)
        index = np.unravel_index(mismatch.argmax(), h.shape)
        result[formulation] = dict(maximum_acceleration_mismatch_mps2=float(mismatch[index]),
            worst_cell_yx=list(map(int, index)), worst_cell_depth_m=float(h[index]),
            weighted_mismatch_l2=float(np.linalg.norm(np.sqrt(h)*mismatch)),
            actual_acceleration_at_worst_mps2=actual[index].tolist(),
            solved_acceleration_at_worst_mps2=solved_acceleration[index].tolist(), pressure_solver=solved[0][1])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--states', type=Path, nargs='*', default=[])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    meta, arrays, hashes = read_snapshot(args.snapshot)
    geometry, flow, detail = (arrays[k].astype(float) for k in ('mean_geometry', 'flow', 'state'))
    h = flow[..., 0]+detail[..., 0]
    initial = np.concatenate((h[..., None], h[..., None]*flow[..., 1:3]+detail[..., 1:3]), axis=-1)
    cases = [('initial', initial)]
    for path in args.states:
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        cases.append((str(path), np.load(path, allow_pickle=False)))
    files = ('audit_nonlinear_kinematics.py', 'total_depth_bank_replay.py', 'total_depth_nonlinear_pressure.py')
    report = dict(schema='raftsim.nonlinear_kinematics.v1', scope=__doc__, source_hashes=hashes,
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files},
        pressure_iterations=40, integrated=False, scene_accepted=False, cases=[])
    for name, state in cases:
        value = dict(state=name, comparison=compare(state, geometry[..., 0], meta['cell_m']))
        report['cases'].append(value)
        print(json.dumps(value), flush=True)
    with args.report.open('x') as output: json.dump(report, output, indent=2, allow_nan=False)


if __name__ == '__main__': main()
