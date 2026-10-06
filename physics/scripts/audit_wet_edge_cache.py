"""Check complete actual-game wet-edge cache comparisons, never FPS acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROW = re.compile(r'WetEdgeCacheAudit exact frame=(\d+) phase=([12]) hit=([01]) cells=(\d+)$')


def audit(text, process):
    for flag in ('-RaftSimCacheWetEdges', '-RaftSimWetEdgeCacheAudit'):
        if process.get('game_arguments', []).count(flag) != 1:
            raise ValueError('Exactly one cache and audit flag required')
    if (process.get('game_exit_code') != 0 or process.get('game_timeout') is not False
            or process.get('suspend_status') != 0 or process.get('resume_status') != 0):
        raise ValueError('Complete game and successful owned-cook suspension/resume required')
    rows = []
    for line in text.splitlines():
        if not re.search(r'\bWetEdgeCacheAudit\b', line):
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Cache mismatch or malformed comparison')
        frame, phase, hit, cells = map(int, match.groups())
        if cells <= 0 or (rows and frame < rows[-1]['frame']):
            raise ValueError('Positive complete arrays in frame order required')
        rows.append(dict(frame=frame, phase=phase, hit=hit, cells=cells))
    phases = []
    for phase in (1, 2):
        selected = [row for row in rows if row['phase'] == phase]
        if len(selected) < 64:
            raise ValueError('Both production uses require at least 64 comparisons')
        phases.append(dict(phase=phase, calls=len(selected), hits=sum(r['hit'] for r in selected),
                           exact_distances=sum(r['cells'] for r in selected)))
    if not sum(r['hit'] for r in rows) or all(r['hit'] for r in rows):
        raise ValueError('Actual hits and rebuilds required')
    return dict(schema='raftsim.wet_edge_cache_audit.v1', passed=True, phases=phases,
                calls=len(rows), exact_distances=sum(r['cells'] for r in rows),
                scope='Every logged call compares all integer distances with the original queue. '
                      'Neither timings nor complete surface/contact arrays are qualified by this check.',
                performance_accepted=False, visual_accepted=False, release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('process', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    log, process = args.log.read_bytes(), args.process.read_bytes()
    result = audit(log.decode('utf-8-sig'), json.loads(process))
    result.update(log_sha256=hashlib.sha256(log).hexdigest(),
                  process_sha256=hashlib.sha256(process).hexdigest())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
