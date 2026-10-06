"""Same-state whole source/handover pass timings, not FPS or visual acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median


def summarize(report):
    rows = report.get('atlas_stencil_pairs')
    if (report.get('schema') != 'raftsim.atlas_stencil_pair.v1'
            or not isinstance(rows, list) or len(rows) != 64
            or not isinstance(report.get('map'), str)
            or not report['map'].endswith('L_SouthForkAmerican_FullReach')):
        raise ValueError('Original FullReach 64-pair atlas report required')
    for key in ('passed', 'paired_parallel_passes_exact', 'identical_masks_probe_requests_feather_and_heights'):
        if type(report.get(key)) is not bool:
            raise ValueError('Explicit source equality verdicts required')
    for key in ('samples', 'different_samples'):
        value = report.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or int(value) != value:
            raise ValueError('Finite integral sample counts required')
    if report['samples'] <= 0 or report['different_samples'] > report['samples']:
        raise ValueError('Nonempty source batch required')
    seconds = report.get('world_seconds')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 10:
        raise ValueError('Post-startup source state required')
    for i, row in enumerate(rows):
        if (type(row.get('candidate_first')) is not bool or row['candidate_first'] != bool(i % 2)
                or type(row.get('all_samples_and_masks_exact')) is not bool):
            raise ValueError('Alternating original order and exact-output verdict required')
        for key in ('reference_ms', 'candidate_ms'):
            value = row.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('Positive finite measured timings required')
    groups = {}
    for name, group in (('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2])):
        groups[name] = dict(pairs=len(group), reference_mean_ms=mean(r['reference_ms'] for r in group),
            candidate_mean_ms=mean(r['candidate_ms'] for r in group),
            reference_median_ms=median(r['reference_ms'] for r in group),
            candidate_median_ms=median(r['candidate_ms'] for r in group),
            candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group))
    return dict(exact=report['passed'] and report['paired_parallel_passes_exact']
        and report['identical_masks_probe_requests_feather_and_heights'] and report['different_samples'] == 0
        and all(r['all_samples_and_masks_exact'] for r in rows),
        measured_both_orders_faster=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
        samples=report['samples'], world_seconds=seconds, groups=groups, release_accepted=False,
        scope='64 paired parallel source+handover passes on one frozen actual state. Requires independent captures; not multi-frame, FPS, physical or visual acceptance.')


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
    return 0 if result['exact'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
