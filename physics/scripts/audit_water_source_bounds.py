"""Audit same-input live bounds pairs; never infer game FPS from component times."""
import argparse
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

PATTERN = re.compile(r'WaterBoundsPair frame=(\d+) exact=(\d+) candidate_first=(\d+) '
                     r'vertices=(\d+) reference_ms=([\d.]+) candidate_ms=([\d.]+)')


def audit(text):
    lines = [line for line in text.splitlines() if 'WaterBoundsPair ' in line]
    rows = []
    for line in lines:
        match = PATTERN.search(line)
        if not match:
            raise ValueError('malformed bounds pair')
        frame, exact, first, vertices = map(int, match.groups()[:4])
        reference, candidate = map(float, match.groups()[4:])
        if exact != 1 or first != (frame // 2) % 2 or vertices <= 0:
            raise ValueError('nonexact pair, wrong order, or empty source')
        if not all(math.isfinite(v) and v > 0 for v in (reference, candidate)):
            raise ValueError('invalid duration')
        rows.append(dict(frame=frame, candidate_first=bool(first), vertices=vertices,
                         reference_ms=reference, candidate_ms=candidate))
    if [r['frame'] for r in rows] != list(range(120, 184)):
        raise ValueError('missing, duplicated, or reordered live pairs')
    if 'Water source bounds mismatch' in text:
        raise ValueError('runtime mismatch reported')
    groups = []
    for first in (False, True):
        selected = [r for r in rows if r['candidate_first'] == first]
        groups.append(dict(candidate_first=first, count=len(selected), **{
            f'{kind}_{stat}_ms': fn([r[f'{kind}_ms'] for r in selected])
            for kind in ('reference', 'candidate')
            for stat, fn in (('mean', statistics.mean), ('median', statistics.median))}))
    return dict(schema='raftsim.water_source_bounds_pairs.v1', passed=True,
                pairs=rows, order_groups=groups, game_performance_accepted=False,
                visual_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = audit(raw.decode('utf-8-sig'))
    result.update(log=str(args.log), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps(result['order_groups'], indent=2))


if __name__ == '__main__':
    main()
