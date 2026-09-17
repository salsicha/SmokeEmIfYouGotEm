"""Complete exact boundary-classification pairs; never full-frame acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def summarize(report):
    rows = report['pairs']
    if type(report.get('exact')) is not bool or len(rows) != 64:
        raise ValueError('Complete 64-pair native report required')
    for i, row in enumerate(rows):
        if row['pair'] != i or type(row['indexed_first']) is not bool or row['indexed_first'] != bool(i % 2):
            raise ValueError('Numbered pairs and both alternating orders required')
        if type(row['exact']) is not bool:
            raise ValueError('Explicit native exactness required')
        for key in ('frame', 'source_vertices', 'midpoints', 'triangles', 'boundary_midpoints'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or int(value) != value or value < 0:
                raise ValueError('Finite nonnegative native counts required')
        if row['source_vertices'] <= 0 or row['triangles'] <= 0 or row['boundary_midpoints'] > row['midpoints']:
            raise ValueError('Valid native topology counts required')
        if row['frame'] < 120 or (i and row['frame'] < rows[i-1]['frame']):
            raise ValueError('Original post-warmup frame order required')
        for key in ('reference_ms', 'indexed_ms'):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]) or row[key] <= 0:
                raise ValueError('Positive finite original timings required')
    if rows[-1]['frame'] == rows[0]['frame'] or not any(r['midpoints'] for r in rows):
        raise ValueError('Changing frames with actual midpoint classifications required')
    groups = {}
    for name, selected in (('all', rows), ('reference_first', rows[::2]), ('indexed_first', rows[1::2])):
        groups[name] = dict(pairs=len(selected),
            reference_mean_ms=statistics.mean(r['reference_ms'] for r in selected),
            indexed_mean_ms=statistics.mean(r['indexed_ms'] for r in selected),
            indexed_faster_pairs=sum(r['indexed_ms'] < r['reference_ms'] for r in selected))
    return dict(exact_boundary_flags=report['exact'] and all(r['exact'] for r in rows),
        measured_both_orders_faster=all(g['indexed_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
        compared_midpoints=sum(r['midpoints'] for r in rows),
        boundary_midpoints=sum(r['boundary_midpoints'] for r in rows),
        first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'], groups=groups,
        scope='Complete boundary count/propagation including allocations on actual topology rebuilds; exact production/reference flags. Not whole crest update, ordinary FPS, physical or visual acceptance.',
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
    return 0 if result['exact_boundary_flags'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
