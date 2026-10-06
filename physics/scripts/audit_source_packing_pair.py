"""Strict full-vertex source packing comparison, not game FPS acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean


def summarize(report):
    schema = report.get('schema')
    kind = report.get('candidate_kind') if schema == 'raftsim.source_packing_pair.v2' else 'vector-color'
    rows = ([dict(r, candidate_first=r['vector_first'], candidate_ms=r['vector_ms']) for r in report['pairs']]
            if schema == 'raftsim.source_packing_pair.v1' else report['pairs'])
    if schema not in ('raftsim.source_packing_pair.v1', 'raftsim.source_packing_pair.v2') or kind not in ('vector-color', 'retained-output') or type(report.get('exact')) is not bool or len(rows) != 64:
        raise ValueError('Complete 64-pair source-packing report required')
    for i, row in enumerate(rows):
        if type(row['pair']) is not int or row['pair'] != i or type(row['candidate_first']) is not bool or row['candidate_first'] != bool(i % 2):
            raise ValueError('Original numbered alternating pairs required')
        if type(row['exact']) is not bool:
            raise ValueError('Explicit per-pair exactness required')
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
        raise ValueError('Live multi-frame comparison required')
    groups = {name: dict(pairs=len(group), reference_mean_ms=mean(r['reference_ms'] for r in group),
                        candidate_mean_ms=mean(r['candidate_ms'] for r in group),
                        candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group))
              for name, group in (('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2]))}
    return dict(candidate_kind=kind, exact_all_attributes=report['exact'] and all(r['exact'] for r in rows),
        measured_both_orders_faster=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
        compared_vertices=sum(r['vertices'] for r in rows), first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'],
        groups=groups, release_accepted=False,
        scope='Packing CPU on paired live inputs; explicit candidate kind and original fresh-allocation reference, all attributes checked. Not game FPS, visual or physical acceptance.')


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
    return 0 if result['exact_all_attributes'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
