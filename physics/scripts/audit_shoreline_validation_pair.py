"""Strict actual-input validation-pass timing comparison, not FPS acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean


def summarize(report):
    # The first retained captures predate the explicit schema/kind fields.
    # Preserve their evidence without inventing an unrecorded candidate kind.
    schema = report.get('schema')
    if schema not in (None, 'raftsim.shoreline_validation_pair.v1'):
        raise ValueError('Unknown shoreline validation report schema')
    kind = report.get('candidate_kind', 'unrecorded')
    if schema and kind not in ('serial-fused', 'parallel-fused'):
        raise ValueError('Explicit supported candidate kind required')
    rows = report.get('pairs', [])
    if type(report.get('exact')) is not bool or len(rows) != 64:
        raise ValueError('Complete 64-pair report required')
    for i, row in enumerate(rows):
        if type(row['pair']) is not int or row['pair'] != i:
            raise ValueError('Original numbered pairs required')
        for key in ('candidate_first', 'exact', 'valid', 'reuse'):
            if type(row[key]) is not bool:
                raise ValueError('Explicit Boolean results required')
        if row['candidate_first'] != bool(i % 2):
            raise ValueError('Alternating execution order required')
        for key in ('frame', 'vertices'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value != int(value) or value <= 0:
                raise ValueError('Positive finite integer counts required')
        if row['frame'] < 120 or (i and row['frame'] < rows[i-1]['frame']):
            raise ValueError('Original post-warmup frame order required')
        for key in ('reference_ms', 'candidate_ms'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('Positive finite measured timings required')
    if rows[0]['frame'] == rows[-1]['frame']:
        raise ValueError('Actual multi-frame evidence required')
    groups = {}
    for name, group in (('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2])):
        groups[name] = dict(pairs=len(group), reference_mean_ms=mean(r['reference_ms'] for r in group),
                            candidate_mean_ms=mean(r['candidate_ms'] for r in group),
                            candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group))
    return dict(candidate_kind=kind, exact_validation_and_reuse=report['exact'] and all(r['exact'] for r in rows),
                all_inputs_valid=all(r['valid'] for r in rows),
                measured_both_orders_faster=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
                compared_vertices=sum(r['vertices'] for r in rows), reuse_calls=sum(r['reuse'] for r in rows),
                first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'], groups=groups,
                visual_accepted=False, performance_accepted=False, release_accepted=False,
                scope='Validation/reuse predicate only on paired actual changing inputs, not full mesh or game FPS.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_validation_and_reuse'] and result['all_inputs_valid'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
