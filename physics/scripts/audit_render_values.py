"""Verify exact alternating actual-frame render-packet pairs, not whole-frame FPS."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

PATTERN = re.compile(
    r'RENDER_VALUES_PAIR frame=(\d+) original_first=([01]) reuse=([01]) '
    r'vertices=(\d+) exact=([01]) original_ms=([\d.eE+-]+) candidate_ms=([\d.eE+-]+)$'
)


def summarize(text):
    rows = []
    for line in text.splitlines():
        if 'RENDER_VALUES_PAIR' not in line:
            continue
        match = PATTERN.search(line)
        if not match:
            raise ValueError('Malformed render-packet evidence')
        frame, first, reuse, vertices, exact = map(int, match.groups()[:5])
        original, candidate = map(float, match.groups()[5:])
        if first != int(frame % 2 == 0) or vertices <= 0:
            raise ValueError('Original alternating order and nonempty actual mesh required')
        if any(not math.isfinite(t) or t <= 0 for t in (original, candidate)):
            raise ValueError('Finite positive measured timings required')
        rows.append(dict(frame=frame, original_first=bool(first), reuse=bool(reuse),
                         vertices=vertices, exact=bool(exact), original_ms=original, candidate_ms=candidate))
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('Exactly one pair for each original frame 120 through 183 required')
    groups = {}
    # The optimized path must improve in both call orders. Include all frames
    # separately so unchanged topology rebuilds cannot be silently discarded.
    for name, group in [('all', rows), ('original_first', rows[::2]), ('candidate_first', rows[1::2]),
                        ('reuse_original_first', [r for r in rows[::2] if r['reuse']]),
                        ('reuse_candidate_first', [r for r in rows[1::2] if r['reuse']])]:
        if not group:
            raise ValueError('Both call orders must exercise unchanged membership')
        groups[name] = dict(pairs=len(group), original_mean_ms=statistics.mean(r['original_ms'] for r in group),
                            candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in group))
    return dict(exact=all(r['exact'] for r in rows),
                measured_both_orders_faster=all(g['candidate_mean_ms'] < g['original_mean_ms'] for g in groups.values()),
                compared_vertices=sum(r['vertices'] for r in rows), groups=groups, pairs=rows,
                release_accepted=False, scope='Current packed render attributes only; not FPS, physics or scene acceptance.')


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
