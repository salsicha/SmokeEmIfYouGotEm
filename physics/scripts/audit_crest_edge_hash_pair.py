"""Complete actual-input crest comparison; never FPS or release acceptance."""
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
        if row['pair'] != i or type(row['strong_first']) is not bool or row['strong_first'] != bool(i % 2):
            raise ValueError('Original numbered pairs and alternating order required')
        if type(row['exact']) is not bool:
            raise ValueError('Explicit native exactness result required')
        for key in ('frame', 'vertices', 'triangles'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value != int(value) or value <= 0:
                raise ValueError('Positive finite native integer counts required')
        if row['frame'] < 120 or (i and row['frame'] < rows[i-1]['frame']):
            raise ValueError('Original post-warmup frame order required')
        for key in ('legacy_ms', 'strong_ms'):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]) or row[key] <= 0:
                raise ValueError('Positive finite original timings required')
        for kind in ('legacy', 'strong'):
            stage = row[kind+'_assembly_ms']
            if type(stage) not in (int, float) or not math.isfinite(stage) or stage < 0 or stage > row[kind+'_ms']:
                raise ValueError('Finite assembly timing within the whole build required')
    if rows[-1]['frame'] == rows[0]['frame']:
        raise ValueError('Actual changing-input history, not one repeated frame, required')
    groups = {}
    for name, selected in [('all', rows), ('legacy_first', rows[::2]), ('strong_first', rows[1::2])]:
        groups[name] = dict(pairs=len(selected), legacy_mean_ms=statistics.mean(r['legacy_ms'] for r in selected),
            strong_mean_ms=statistics.mean(r['strong_ms'] for r in selected),
            legacy_assembly_mean_ms=statistics.mean(r['legacy_assembly_ms'] for r in selected),
            strong_assembly_mean_ms=statistics.mean(r['strong_assembly_ms'] for r in selected),
            strong_faster_pairs=sum(r['strong_ms'] < r['legacy_ms'] for r in selected))
    return dict(exact_topology_and_coordinates=report['exact'] and all(r['exact'] for r in rows),
        measured_both_orders_faster=all(g['strong_mean_ms'] < g['legacy_mean_ms'] for g in groups.values()),
        compared_vertices=sum(r['vertices'] for r in rows), compared_triangles=sum(r['triangles'] for r in rows),
        first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'], groups=groups,
        scope='Whole adaptive-build edge-hash CPU comparison on actual changed inputs; not ordinary frame performance, visual or physics acceptance.',
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
    return 0 if result['exact_topology_and_coordinates'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
