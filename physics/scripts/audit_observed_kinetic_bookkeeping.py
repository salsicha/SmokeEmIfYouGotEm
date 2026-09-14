"""Read-only kinetic bookkeeping for a retained observer trial, not energy acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def bookkeeping(state, rate, pressure):
    h, momentum = state[..., 0], state[..., 1:3]
    velocity = np.divide(momentum, h[..., None], out=np.zeros_like(momentum), where=h[..., None] > 0)
    speed2 = np.sum(velocity * velocity, axis=-1)
    kinetic = .5 * np.sum(momentum * velocity, axis=-1)
    # Chain rule for K=|m|^2/(2h), without evaluating a potentially underflowed h^2.
    kinetic_rate = np.sum(velocity * rate[..., 1:3], axis=-1) - .5 * speed2 * rate[..., 0]
    pressure_work = np.sum(velocity * pressure, axis=-1)
    return dict(velocity=velocity, kinetic=kinetic, kinetic_rate=kinetic_rate,
                pressure_work=pressure_work, nonpressure_rate=kinetic_rate-pressure_work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('progress', type=Path)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    raw = args.progress.read_bytes()
    raw = raw[:raw.rfind(b'\n')+1]
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    event, = [r for r in records if r.get('event') == 'observed_trial_rate'
              and Path(r.get('snapshot', {}).get('path', '')).resolve() == args.snapshot.resolve()]
    digest = hashlib.sha256(args.snapshot.read_bytes()).hexdigest()
    assert digest == event['snapshot']['sha256']
    with np.load(args.snapshot, allow_pickle=False) as archive:
        state, rate, pressure, bed = (archive[k] for k in ('state', 'rate', 'pressure', 'bed'))
    assert state.shape == rate.shape and state.shape[-1] == 3
    assert pressure.shape == state.shape[:-1] + (2,) and bed.shape == state.shape[:-1]
    assert all(np.isfinite(a).all() for a in (state, rate, pressure, bed))
    assert np.all(state[..., 0] >= 0)
    values = bookkeeping(state, rate, pressure)
    assert all(np.isfinite(a).all() for a in values.values())
    speed = np.linalg.norm(values['velocity'], axis=-1)
    assert float(speed.max()) == event['maximum_speed_mps']
    cells = []
    for observed in event['fastest_cells']:
        yx = tuple(observed['yx'])
        assert float(state[yx][0]) == observed['depth_m']
        assert values['velocity'][yx].tolist() == observed['velocity_mps']
        cells.append(dict(yx=list(yx), depth_m=float(state[yx][0]),
            speed_mps=float(speed[yx]), mass_rate=float(rate[yx][0]),
            **{k: float(v[yx]) for k, v in values.items() if k != 'velocity'}))
    result = dict(snapshot=str(args.snapshot.resolve()), snapshot_sha256=digest,
        progress_prefix_sha256=hashlib.sha256(raw).hexdigest(),
        observer_trial_clock=event['trial_native_seconds'], rate_index=event['rate_index'],
        independently_matches_observed_cells=True, fastest_cells=cells,
        limitations='Instantaneous trial-state kinetic bookkeeping per unit horizontal area, density omitted. '
        'Nonpressure includes transport, gravity and other original terms; it is not dissipation. '
        'This is not accepted-state total mechanical energy, boundary energy balance, or stability acceptance.',
        stability_accepted=False, solver_modified=False)
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
