"""Qualify exact ordered drawn attributes in native compact-source pairs, not scene acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROW = re.compile(r'CompactCrestSourcePair frame=(\d+) exact=([01]) candidate_first=([01]) source=(\d+) compact=(\d+) indices=(\d+) reference_ms=([\d.]+) candidate_ms=([\d.]+)$')


def summarize(text):
    rows = []
    for line in text.splitlines():
        if not re.search(r'\bCompactCrestSource(?:Pair)?\b', line):
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Native mismatch or malformed compact-source row')
        v = match.groups()
        row = dict(zip(('frame', 'exact', 'candidate_first', 'source', 'compact', 'indices'), map(int, v[:6])))
        row.update(reference_ms=float(v[6]), candidate_ms=float(v[7]))
        if (row['exact'] != 1 or row['candidate_first'] != (row['frame']//2) % 2
                or not 0 < row['compact'] <= row['source'] or row['indices'] <= 0 or row['indices'] % 3
                or any(not math.isfinite(row[k]) or row[k] <= 0 for k in ('reference_ms', 'candidate_ms'))):
            raise ValueError('Invalid state, execution order, count or timing')
        rows.append(row)
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('Complete ordered 120..183 native frame pairs required')
    if not any(r['compact'] < r['source'] for r in rows):
        raise ValueError('Capture never exercises source compaction')
    groups = []
    for first in (0, 1):
        group = [r for r in rows if r['candidate_first'] == first]
        groups.append(dict(candidate_first=first, pairs=len(group),
                           reference_mean_ms=statistics.mean(r['reference_ms'] for r in group),
                           candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in group),
                           candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group)))
    return dict(schema='raftsim.compact_crest_source.v1', exact_pairs=len(rows), rows=rows, groups=groups,
                faster_in_both_orders=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups),
                scope=__doc__, performance_accepted=False, visual_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    report = summarize(raw.decode('utf-8-sig'))
    report.update(log=str(args.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
