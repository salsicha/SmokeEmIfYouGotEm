"""Exact actual-state relief scheduling comparison, never a frame/FPS gate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def summarize(report):
    if report.get('schema') != 'raftsim.cartesian_hydraulic_relief_pair.v1' or report.get('release_accepted') is not False:
        raise ValueError('Scoped native relief comparison required')
    rows = report['rows']
    if len(rows) != 64:
        raise ValueError('All 64 original comparison pairs required')
    for index, row in enumerate(rows):
        if type(row['parallel_first']) is not bool or row['parallel_first'] != bool(index % 2):
            raise ValueError('Alternating original call order required')
        for key in ('vertices', 'nonzero_relief_vertices', 'different_float_bits'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value != int(value) or value < 0:
                raise ValueError('Finite nonnegative integer comparison counts required')
        if not 0 < row['nonzero_relief_vertices'] <= row['vertices'] or row['different_float_bits'] > row['vertices']:
            raise ValueError('Nontrivial actual relief and consistent counts required')
        for key in ('serial_ms', 'parallel_ms', 'world_seconds'):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]) or row[key] <= 0:
                raise ValueError('Positive finite measured timing required')
        if row['world_seconds'] < 10 or (index and row['world_seconds'] <= rows[index-1]['world_seconds']):
            raise ValueError('Distinct increasing post-warmup refreshes required')
    groups = {}
    for label, selected in [('all', rows), ('serial_first', rows[::2]), ('parallel_first', rows[1::2])]:
        groups[label] = dict(pairs=len(selected),
            serial_mean_ms=statistics.mean(r['serial_ms'] for r in selected),
            parallel_mean_ms=statistics.mean(r['parallel_ms'] for r in selected),
            parallel_faster_pairs=sum(r['parallel_ms'] < r['serial_ms'] for r in selected))
    same = not any(r['different_float_bits'] for r in rows)
    faster = all(g['parallel_mean_ms'] < g['serial_mean_ms'] for g in groups.values())
    return dict(exact_float_comparison_passed=same, measured_both_orders_faster=faster,
        compared_vertices=sum(r['vertices'] for r in rows), groups=groups,
        scope='Same-input CPU relief pass only; timings include output initialization. No scene, FPS, physics, contact or visual acceptance.',
        release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_float_comparison_passed'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
