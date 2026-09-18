"""Validate live interpolation/packing pairs; never FPS or visual acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median


def summarize(report):
    rows = report.get('pairs')
    if (report.get('schema') != 'raftsim.water_interpolation_packing_pair.v1'
            or type(report.get('exact')) is not bool
            or not isinstance(rows, list) or len(rows) != 64):
        raise ValueError('Complete original 64-pair report required')
    for i, row in enumerate(rows):
        if (type(row.get('pair')) is not int or row['pair'] != i
                or type(row.get('candidate_first')) is not bool
                or row['candidate_first'] != bool(i % 2)):
            raise ValueError('Numbered alternating pairs required')
        for key in ('fields_and_packing_exact', 'production_exact'):
            if type(row.get(key)) is not bool:
                raise ValueError('Explicit field and production equality required')
        for key in ('frame', 'vertices'):
            v = row.get(key)
            if type(v) not in (int, float) or not math.isfinite(v) or v <= 0 or int(v) != v:
                raise ValueError('Positive finite integral counts required')
        if row['frame'] < 120 or (i and row['frame'] <= rows[i-1]['frame']):
            raise ValueError('Strictly increasing post-warmup frames required')
        for key in ('reference_ms', 'candidate_ms', 'alpha'):
            v = row.get(key)
            if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
                raise ValueError('Positive finite timing and live blend required')
        if row['alpha'] > 1:
            raise ValueError('Blend outside original interpolation interval')
    groups = {}
    for name, group in (('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2])):
        groups[name] = dict(pairs=len(group), reference_mean_ms=mean(r['reference_ms'] for r in group),
            candidate_mean_ms=mean(r['candidate_ms'] for r in group),
            reference_median_ms=median(r['reference_ms'] for r in group),
            candidate_median_ms=median(r['candidate_ms'] for r in group),
            candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group))
    return dict(exact_all_fields_and_attributes=report['exact'] and all(
        r['fields_and_packing_exact'] and r['production_exact'] for r in rows),
        measured_both_orders_faster=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
        compared_vertices=sum(r['vertices'] for r in rows), first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'],
        groups=groups, release_accepted=False,
        scope='Paired complete rendered fields and packed attributes, plus actual published attributes. Not FPS, physical or visual acceptance.')


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
    return 0 if result['exact_all_fields_and_attributes'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
