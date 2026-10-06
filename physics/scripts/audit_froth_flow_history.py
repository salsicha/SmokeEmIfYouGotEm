"""Characteristics through actual piecewise-held native flow inputs.

This measures transport approximations, not photographed motion or foam quality.
No interpolation across missing time, invented exterior flow, or source edits.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from audit_froth_characteristics import FrozenCurrent, error_summary


class FlowHistory:
    def __init__(self, intervals):
        self.intervals = tuple(intervals)
        if not self.intervals:
            raise ValueError('Original nonempty history required')
        previous = None
        for start, end, field in self.intervals:
            if (type(start) not in (int, float) or type(end) not in (int, float) or
                    not math.isfinite(start) or not math.isfinite(end) or
                    start < 0 or end <= start or
                    (previous is not None and start != previous) or
                    not isinstance(field, FrozenCurrent)):
                raise ValueError('Finite contiguous positive intervals required')
            previous = end
        self.start = self.intervals[0][0]
        self.end = self.intervals[-1][1]

    def depart(self, points, duration, max_step, order=2):
        if (not math.isfinite(duration) or duration < 0 or
                not math.isfinite(max_step) or max_step <= 0 or order not in (1, 2, 4)):
            raise ValueError('Nonnegative duration and positive integration step required')
        x = np.array(points, dtype=float, copy=True)
        if x.ndim != 2 or x.shape[1] != 2:
            raise ValueError('Nx2 points required')
        valid = np.isfinite(x).all(axis=1)
        target = self.end-duration
        if target < self.start:
            return np.full_like(x, np.nan), np.zeros(len(x), dtype=bool)
        # Split exactly at every actual source change. Never interpolate time
        # using a later input or evaluate an RK stage across a discontinuity.
        for start, end, field in reversed(self.intervals):
            if end <= target:
                break
            seconds = end-max(start, target)
            if seconds <= 0:
                continue
            x, ok = field.depart(x, seconds, max(1, math.ceil(seconds/max_step)), order)
            valid &= ok
        if duration == 0:
            _, ok = self.intervals[-1][2].sample(x)
            valid &= ok
        return np.where(valid[:, None], x, np.nan), valid


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def load(prefix):
    prefix = Path(prefix)
    index_path = Path(str(prefix)+'.history.json')
    snapshot_path = Path(str(prefix)+'.json')
    index = json.loads(index_path.read_text())
    snapshot = json.loads(snapshot_path.read_text())
    if (index.get('schema') != 'raftsim.froth_flow_history.v1' or
            index.get('dtype') != 'little-endian float32' or index.get('arrays_complete') is not True or
            snapshot.get('schema') != 'raftsim.detail.snapshot.v2' or
            snapshot.get('dtype') != 'little-endian float32' or snapshot.get('arrays_complete') is not True):
        raise ValueError('Complete original history and paired snapshot required')
    files = [index_path, snapshot_path]
    intervals = []
    for i, record in enumerate(index['intervals']):
        expected = f'{prefix.name}.history-{i:03d}.f32'
        shape = record['shape']
        if (record['file'] != expected or not isinstance(shape, list) or len(shape) != 3 or
                shape[2] != 4 or any(type(n) is not int or n < 2 for n in shape) or
                not _number(record['mean_sample_elapsed_s']) or record['mean_sample_elapsed_s'] < 0):
            raise ValueError('Original local filename, lattice and sample time required')
        path = prefix.parent/expected
        flow = np.fromfile(path, dtype='<f4').reshape(shape)
        field = FrozenCurrent(flow, record['origin_m'], record['cell_m'])
        intervals.append((record['start_s'], record['end_s'], field))
        files.append(path)
    history = FlowHistory(intervals)
    last = history.intervals[-1][2]
    if (snapshot['shape'] != list(last.flow.shape) or snapshot['origin_m'] != last.origin.tolist() or
            snapshot['cell_m'] != last.cell or not _number(snapshot['simulation_s']) or
            # The existing snapshot serializes its native clock to nine decimals.
            # Compare that representation; integrate using the full history clock.
            f'{snapshot["simulation_s"]:.9f}' != f'{history.end:.9f}'):
        raise ValueError('History end must match the same completed snapshot')
    arrays = {}
    for name in ('flow', 'surface'):
        path = Path(str(prefix)+f'.{name}.f32')
        arrays[name] = np.fromfile(path, dtype='<f4').reshape(last.flow.shape)
        files.append(path)
    if not np.array_equal(arrays['flow'], last.flow):
        raise ValueError('Final historical flow differs from actual paired input')
    coverage = arrays['surface'][..., 3]
    if (not np.isfinite(arrays['surface']).all() or (coverage < 0).any() or (coverage > 1).any()):
        raise ValueError('Finite bounded original surface required')
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return history, coverage, hashes


def analyze(prefix):
    history, coverage, hashes = load(prefix)
    last = history.intervals[-1][2]
    y, x = np.indices(coverage.shape)
    edge = np.minimum.reduce((x, y, coverage.shape[1]-1-x, coverage.shape[0]-1-y))*last.cell
    selected = (last.flow[..., 0] > .01) & (edge >= 4)
    points = np.stack((x[selected], y[selected]), axis=1)*last.cell+last.origin
    amount = coverage[selected]
    records = []
    for seconds in (.25, .5, .75):
        coarse, coarse_ok = history.depart(points, seconds, 1/128, 4)
        reference, reference_ok = history.depart(points, seconds, 1/256, 4)
        common_ref = coarse_ok & reference_ok
        convergence = np.linalg.norm(reference[common_ref]-coarse[common_ref], axis=1)
        if (not np.array_equal(coarse_ok, reference_ok) or not common_ref.any() or
                convergence.max() > .0001):
            raise ValueError('Historical reference did not converge within unchanged 0.1mm gate')
        methods = {
            'straight_latest': last.depart(points, seconds, 1, 1),
            'frozen_midpoint_8': last.depart(points, seconds, 8, 2),
            'history_midpoint': history.depart(points, seconds, 1/32, 2),
            'frozen_rk4': last.depart(points, seconds, math.ceil(seconds*256), 4),
        }
        common = reference_ok.copy()
        for _, ok in methods.values():
            common &= ok
        rows = []
        summaries = {}
        for name, (result, ok) in methods.items():
            error = np.linalg.norm(result-reference, axis=1)
            summaries[name] = dict(supported=int(ok.sum()),
                common=error_summary(error[common]),
                common_foamy=error_summary(error[common & (amount > .1)]))
        for i, point in enumerate(points):
            row = dict(position_m=point.tolist(), coverage=float(amount[i]),
                       reference_supported=bool(reference_ok[i]), common_supported=bool(common[i]),
                       reference_m=reference[i].tolist() if reference_ok[i] else None, methods={})
            for name, (result, ok) in methods.items():
                row['methods'][name] = dict(supported=bool(ok[i]),
                    departure_m=result[i].tolist() if ok[i] else None,
                    error_m=float(np.linalg.norm(result[i]-reference[i])) if ok[i] and reference_ok[i] else None)
            rows.append(row)
        records.append(dict(duration_s=seconds, reference_convergence=error_summary(convergence),
                            common_supported_rows=int(common.sum()), methods=summaries, rows=rows))
    for path, digest in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError('Original evidence changed during audit')
    return dict(schema='raftsim.historical_froth_characteristics.v1', input_sha256=hashes,
                start_s=history.start, end_s=history.end, interval_count=len(history.intervals),
                registrations=[dict(start_s=a,end_s=b,origin_m=f.origin.tolist(),cell_m=f.cell)
                               for a,b,f in history.intervals],
                original_wet_interior_cells=len(points), records=records,
                model='piecewise-held exact native mean inputs; bilinear space; no time interpolation',
                visual_accepted=False, physical_accepted=False, performance_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError('Preserve previous audit')
    report = analyze(args.prefix)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'records'}, indent=2))
    for record in report['records']:
        print(json.dumps({k:v for k,v in record.items() if k != 'rows'}, indent=2))
