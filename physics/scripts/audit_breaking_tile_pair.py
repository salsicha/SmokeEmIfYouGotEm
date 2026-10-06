"""Strict actual-grid hash/direct crest comparison, not frame acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def summarize(report):
    rows = report['pairs']
    if type(report.get('exact')) is not bool or len(rows) != 64:
        raise ValueError('Complete 64-pair native exactness report required')
    for i, row in enumerate(rows):
        if type(row['pair']) not in (int, float) or row['pair'] != i:
            raise ValueError('Original numbered pairs required')
        if type(row['dense_first']) is not bool or row['dense_first'] != bool(i % 2):
            raise ValueError('Alternating native order required')
        if type(row['exact']) is not bool:
            raise ValueError('Explicit native exactness required')
        for key in ('frame', 'points', 'nonzero_heights', 'dense_tiles', 'hash_tiles'):
            v = row[key]
            if type(v) not in (int, float) or not math.isfinite(v) or v != int(v) or v <= 0:
                raise ValueError('Positive finite native counts required')
        if row['nonzero_heights'] > row['points'] or not row['hash_tiles'] <= row['dense_tiles'] <= 65536:
            raise ValueError('Valid bounded coverage and nonzero source samples required')
        if row['frame'] < 120 or (i and row['frame'] <= rows[i-1]['frame']):
            raise ValueError('Distinct post-warmup actual frames required')
        for key in ('hash_ms', 'dense_ms'):
            v = row[key]
            if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
                raise ValueError('Positive finite native timings required')
    groups = {}
    for name, selected in [('all', rows), ('hash_first', rows[::2]), ('dense_first', rows[1::2])]:
        groups[name] = dict(pairs=len(selected), hash_mean_ms=statistics.mean(r['hash_ms'] for r in selected),
            dense_mean_ms=statistics.mean(r['dense_ms'] for r in selected),
            dense_faster_pairs=sum(r['dense_ms'] < r['hash_ms'] for r in selected))
    return dict(exact_height_and_foam=report['exact'] and all(r['exact'] for r in rows),
        measured_both_orders_faster=all(g['dense_mean_ms'] < g['hash_mean_ms'] for g in groups.values()),
        compared_points=sum(r['points'] for r in rows), nonzero_heights=sum(r['nonzero_heights'] for r in rows),
        first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'], groups=groups,
        scope='Actual full-grid profile sampling only; excludes construction, frame timing and motion acceptance.',
        release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_height_and_foam'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
