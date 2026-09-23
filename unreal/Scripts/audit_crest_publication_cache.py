"""Exact live ownership-publication pairs; not ordinary-game FPS acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROW = re.compile(r'CrestPublicationCachePair frame=(\d+) exact=(\d+) candidate_first=(\d+) '
                 r'reused=(\d+) indices=(\d+) cells=(\d+) reference_ms=(\S+) candidate_ms=(\S+)')


def audit(text, first=120, last=247):
    if first < 0 or last < first:
        raise ValueError('Invalid frame interval')
    if 'CrestPublicationCache mismatch' in text:
        raise ValueError('Actual topology mismatch')
    rows = []
    for line in text.splitlines():
        if 'CrestPublicationCachePair' not in line:
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Malformed publication pair')
        frame, exact, order, reused, indices, cells = map(int, match.groups()[:6])
        reference, candidate = map(float, match.groups()[6:])
        if (exact != 1 or order != (frame//2)%2 or reused not in (0, 1)
                or indices % 3 or cells <= 0
                or any(not math.isfinite(v) or v < 0 for v in (reference, candidate))):
            raise ValueError('Invalid publication pair')
        if first <= frame <= last:
            rows.append(dict(frame=frame, candidate_first=order, reused=bool(reused),
                             indices=indices, cells=cells, reference_ms=reference, candidate_ms=candidate))
    if [r['frame'] for r in rows] != list(range(first, last+1)):
        raise ValueError('Missing, duplicate or reordered pair')
    if not any(r['indices'] for r in rows) or {r['candidate_first'] for r in rows} != {0, 1}:
        raise ValueError('Actual workload and both orders required')
    groups = {}
    for order in (0, 1):
        selected = [r for r in rows if r['candidate_first'] == order]
        groups[str(order)] = dict(count=len(selected), reused=sum(r['reused'] for r in selected),
            reference_mean_ms=statistics.mean(r['reference_ms'] for r in selected),
            candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in selected),
            slower_pairs=sum(r['candidate_ms'] > r['reference_ms'] for r in selected))
    return dict(rows=rows, by_candidate_first=groups,
                both_order_mean_improved=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups.values()),
                gameplay_performance_or_scene_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = audit(raw.decode('utf-8', errors='replace'))
    result.update(log=str(args.log), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))
