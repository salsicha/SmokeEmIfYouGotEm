"""Check every runtime station-coverage reuse against its original computation."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROW = re.compile(r"StationCoverageAudit frame=(\d+) stations=(\d+) queries=(\d+) "
                 r"differences=(\d+) recentered=([01]) center=(\S+) north=(\S+)$")


def audit(text, minimum_refreshes=30):
    if minimum_refreshes < 1:
        raise ValueError("minimum_refreshes must be positive")
    rows = []
    for line in text.splitlines():
        if "StationCoverageAudit frame=" not in line:
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError("malformed station coverage audit row")
        frame, stations, queries, differences, recentered = map(int, match.groups()[:5])
        center, north = map(float, match.groups()[5:])
        if not all(map(math.isfinite, (center, north))) or stations < 1 or queries < 1:
            raise ValueError("invalid station coverage measurements")
        # Multiple initialized actors may refresh in startup frame zero. Keep
        # those rows too; do not discard observed differences at startup.
        rows.append(dict(frame=frame, stations=stations, queries=queries,
                         differences=differences, recentered=recentered,
                         center=center, north=north))
    if len(rows) < minimum_refreshes:
        raise ValueError("insufficient actual refresh measurements")
    if "LogExit: Exiting." not in text:
        raise ValueError("engine log is not terminal")
    differences = sum(r['differences'] for r in rows)
    recentered = sum(r['recentered'] for r in rows)
    return dict(schema='raftsim.station_coverage_reuse.v1', refreshes=len(rows),
                queries=sum(r['queries'] for r in rows), differences=differences,
                recentered_refreshes=recentered, rows=rows,
                passed=differences == 0 and recentered > 0,
                release_accepted=False,
                scope='Actual calls compared against the original computation, '
                      'including startup and recentered refreshes. Exact scalar '
                      'coverage only; not full geometry, motion or FPS acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = audit(raw.decode('utf-8-sig'))
    result.update(log=str(args.log.resolve()), sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as target:
        json.dump(result, target, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
