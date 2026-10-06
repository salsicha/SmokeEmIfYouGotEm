"""Exact native base-vertex histories/statistics; not FPS or visual acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


ROW = re.compile(r'BaseVertexAudit frame=(\d+) pair=(\d+) exact=([01]) candidate_first=([01]) vertices=(\d+) wet=(\d+) reference_ms=([\d.]+) candidate_ms=([\d.]+)$')


def summarize(text):
    rows = []
    for line in text.splitlines():
        if not re.search(r'\bBaseVertexAudit\b', line):
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Native mismatch or malformed base-vertex pair')
        values = match.groups()
        row = dict(zip(('frame', 'pair', 'exact', 'candidate_first', 'vertices', 'wet'), map(int, values[:6])))
        row.update(reference_ms=float(values[6]), candidate_ms=float(values[7]))
        if (not row['exact'] or not 0 < row['wet'] <= row['vertices']
                or row['candidate_first'] != (row['pair']-1) % 2
                or any(not math.isfinite(row[k]) or row[k] <= 0 for k in ('reference_ms', 'candidate_ms'))):
            raise ValueError('Nonexact state, incorrect order or invalid timing/count')
        rows.append(row)
    if (not 32 <= len(rows) <= 64 or [r['pair'] for r in rows] != list(range(1, len(rows)+1))
            or rows[0]['frame'] not in (120, 121) or rows[-1]['frame'] not in (182, 183)
            or any(not 1 <= b['frame']-a['frame'] <= 2 for a, b in zip(rows, rows[1:]))):
        raise ValueError('Complete ordered 120..183 refresh coverage required')
    groups = []
    for first in (0, 1):
        group = [r for r in rows if r['candidate_first'] == first]
        groups.append(dict(candidate_first=first, pairs=len(group),
                           reference_mean_ms=statistics.mean(r['reference_ms'] for r in group),
                           candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in group),
                           candidate_faster_pairs=sum(r['candidate_ms'] < r['reference_ms'] for r in group)))
    return dict(schema='raftsim.base_vertex_pairs.v1', exact_pairs=len(rows), rows=rows, groups=groups,
                faster_in_both_orders=all(g['candidate_mean_ms'] < g['reference_mean_ms'] for g in groups),
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
