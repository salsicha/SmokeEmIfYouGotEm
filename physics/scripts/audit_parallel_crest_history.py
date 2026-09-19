"""Same-input native history comparison; never a whole-frame or visual pass."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


ROW = re.compile(r'ParallelCrestHistoryPair frame=(\d+) exact=([01]) candidate_first=([01]) dense=([01]) vertices=(\d+) reference_ms=([\d.]+) candidate_ms=([\d.]+)(?: parallel_used=([01]))?$')


def summarize(text):
    if 'ParallelCrestHistory mismatch' in text:
        raise ValueError('Native vertex or history mismatch')
    rows = []
    for line in text.splitlines():
        if 'ParallelCrestHistoryPair' not in line:
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Malformed comparison row')
        frame, exact, first, dense, vertices, reference, candidate, parallel_used = match.groups()
        row = dict(frame=int(frame), exact=int(exact), candidate_first=int(first), dense=int(dense),
                   vertices=int(vertices), reference_ms=float(reference), candidate_ms=float(candidate))
        row['parallel_used'] = None if parallel_used is None else int(parallel_used)
        if not row['exact'] or row['vertices'] <= 0 or any(not math.isfinite(row[k]) or row[k] <= 0 for k in ('reference_ms', 'candidate_ms')):
            raise ValueError('Non-exact or invalid timing pair')
        if row['candidate_first'] != (row['frame']//2)%2:
            raise ValueError('Execution order must alternate independently of frame parity')
        rows.append(row)
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('All 64 ordered native frame pairs required')
    mapped_only = all(r['parallel_used'] is not None for r in rows)
    if not mapped_only and any(r['parallel_used'] is not None for r in rows):
        raise ValueError('Comparison policy changes inside capture')
    if mapped_only and any(r['parallel_used'] != 1-r['dense'] for r in rows):
        raise ValueError('Mapped-only candidate must retain serial dense execution')
    groups = []
    for dense in (0, 1):
        for first in (0, 1):
            group = [r for r in rows if r['dense'] == dense and r['candidate_first'] == first]
            if len(group) < 8:
                raise ValueError('Both states require both execution orders')
            ref = statistics.mean(r['reference_ms'] for r in group)
            cand = statistics.mean(r['candidate_ms'] for r in group)
            groups.append(dict(dense=dense, candidate_first=first, pairs=len(group),
                               reference_mean_ms=ref, candidate_mean_ms=cand,
                               candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group)))
    return dict(schema='raftsim.parallel_crest_history_pairs.v1', exact_pairs=len(rows), groups=groups, rows=rows,
                policy='mapped-only' if mapped_only else 'all-history',
                mapped_only_dispatch_verified=mapped_only,
                changed_path_faster_in_both_orders=all(g['candidate_mean_ms'] < g['reference_mean_ms']
                                                      for g in groups if not mapped_only or not g['dense']),
                faster_in_both_states_and_orders=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups),
                gameplay_or_performance_accepted=False, scope=__doc__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = summarize(raw.decode('utf-8-sig'))
    result.update(log=str(args.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
