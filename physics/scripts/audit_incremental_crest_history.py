"""Check a complete alternating actual-game history comparison, never FPS."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

PATTERN = re.compile(r'IncrementalCrestHistoryAudit frame=(\d+) exact=([01]) candidate_first=([01]) dense=([01]) incremental=([01]) changed=(\d+) vertices=(\d+) reference_ms=([^ ]+) candidate_ms=([^ ]+)$')


def summarize(text):
    rows = []
    if 'IncrementalCrestHistoryAudit mismatch' in text:
        raise ValueError('Native history mismatch, including warmup')
    for line in text.splitlines():
        if 'IncrementalCrestHistoryAudit frame=' not in line:
            continue
        match = PATTERN.search(line)
        if not match:
            raise ValueError('Malformed history comparison')
        frame, exact, first, dense, incremental, changed, vertices = map(int, match.groups()[:7])
        reference, candidate = map(float, match.groups()[7:])
        if first != frame % 2 or vertices <= 0 or changed > vertices:
            raise ValueError('Invalid order or vertex counts')
        if (dense and (changed or incremental)) or (incremental and not changed):
            raise ValueError('Inconsistent coordinate update mode')
        if any(not math.isfinite(t) or t <= 0 for t in (reference, candidate)):
            raise ValueError('Positive finite timings required')
        rows.append(dict(frame=frame, exact=bool(exact), candidate_first=bool(first),
            dense=bool(dense), incremental=bool(incremental), changed=changed, vertices=vertices,
            reference_ms=reference, candidate_ms=candidate))
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('All 64 consecutive original pairs required')
    groups = {}
    for name, group in [('all', rows), ('reference_first', rows[::2]), ('candidate_first', rows[1::2]),
                        ('dense', [r for r in rows if r['dense']]),
                        ('incremental', [r for r in rows if r['incremental']]),
                        ('full_rebuild', [r for r in rows if not r['dense'] and not r['incremental']])]:
        groups[name] = dict(calls=len(group),
            reference_mean_ms=statistics.mean(r['reference_ms'] for r in group) if group else None,
            candidate_mean_ms=statistics.mean(r['candidate_ms'] for r in group) if group else None)
    if not groups['incremental']['calls'] or not groups['dense']['calls']:
        raise ValueError('Both stable and sparse moving-coordinate histories required')
    return dict(exact=all(r['exact'] for r in rows),
        measured_both_orders_faster=all(groups[g]['candidate_mean_ms'] < groups[g]['reference_mean_ms']
                                      for g in ('all', 'reference_first', 'candidate_first')),
        groups=groups, pairs=rows, release_accepted=False, visual_accepted=False,
        scope='Exact current vertex/correction comparison; component timing only, not ordinary FPS or scene acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    report = summarize(raw.decode('utf-8-sig'))
    report.update(schema='raftsim.incremental_crest_history.v1', log=str(args.log.resolve()),
                  sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'pairs'}, indent=2))
    return 0 if report['exact'] and report['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
