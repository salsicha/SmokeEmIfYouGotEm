"""Audit all 64 alternating-order actual topology-publication pairs; not FPS."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

PATTERN = re.compile(
    r'CrestTopologyPublishAudit frame=(\d+) exact=([01]) candidate_first=([01]) '
    r'indices=(\d+) cells=(\d+) reference_ms=([\d.eE+-]+) candidate_ms=([\d.eE+-]+)'
)


def summarize(text):
    lines = [line for line in text.splitlines() if 'CrestTopologyPublishAudit frame=' in line]
    rows = []
    for line in lines:
        match = PATTERN.search(line)
        if not match:
            raise ValueError('Malformed native audit row')
        frame, exact, first, indices, cells = map(int, match.groups()[:5])
        reference, candidate = map(float, match.groups()[5:])
        if indices <= 0 or indices % 3 or cells <= 0:
            raise ValueError('Positive complete topology counts required')
        if any(not math.isfinite(t) or t <= 0 for t in (reference, candidate)):
            raise ValueError('Finite positive original timings required')
        if first != frame % 2:
            raise ValueError('Alternating original call order required')
        rows.append(dict(frame=frame, exact=bool(exact), candidate_first=bool(first),
                         indices=indices, cells=cells, reference_ms=reference, candidate_ms=candidate))
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('Exactly one original pair on every frame 120 through 183 required')
    groups = {}
    for name, group in [('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2])]:
        groups[name] = dict(pairs=len(group), reference_mean_ms=statistics.mean(r['reference_ms'] for r in group),
                           candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in group),
                           candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group))
    return dict(exact=all(r['exact'] for r in rows),
                measured_both_orders_faster=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
                compared_indices=sum(r['indices'] for r in rows), compared_cells=sum(r['cells'] for r in rows),
                groups=groups, pairs=rows, release_accepted=False,
                scope='Existing topology publication only; not ordinary FPS, water physics, visual or scene acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    payload = args.log.read_bytes()
    result = summarize(payload.decode('utf-8-sig'))
    result.update(log=str(args.log.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'pairs'}))
    return 0 if result['exact'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
