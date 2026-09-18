"""Verify actual-game exact prefetch samples; not FPS or scene acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re


ROW = re.compile(r'CrestPrefetchAudit exact frame=(\d+) samples=(\d+) batches=(\d+)$')


def audit(text, process):
    args = process.get('game_arguments', [])
    for option in ('-RaftSimPrefetchCrestProfile', '-RaftSimCrestPrefetchAudit'):
        if args.count(option) != 1:
            raise ValueError('Exactly one candidate and audit switch required')
    if process.get('game_exit_code') != 0 or process.get('game_timeout') is not False:
        raise ValueError('Completed non-timeout game required')
    if process.get('suspend_status') != 0 or process.get('resume_status') != 0:
        raise ValueError('Successful owned-cook suspension/resume required')
    rows = []
    for line in text.splitlines():
        if not re.search(r'\bCrestPrefetchAudit\b', line):
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Prefetch mismatch or malformed audit record')
        frame, samples, batches = map(int, match.groups())
        if samples <= 0 or batches <= 0 or (rows and frame <= rows[-1]['frame']):
            raise ValueError('Positive samples/batches in unique ordered frames required')
        rows.append(dict(frame=frame, samples=samples, batches=batches))
    if len(rows) < 64:
        raise ValueError('At least 64 completed current-profile adoptions required')
    return dict(schema='raftsim.crest_prefetch_audit.v1', passed=True,
        scope='Every adopted prepared sample compared bit-for-bit with the current original callback. Native topology/history checks are separate. No performance, visual, physical or release acceptance.',
        adopted_profiles=len(rows), exact_sample_comparisons=sum(r['samples'] for r in rows), rows=rows,
        performance_accepted=False, visual_accepted=False, release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('process', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw, process_raw = args.log.read_bytes(), args.process.read_bytes()
    report = audit(raw.decode('utf-8-sig'), json.loads(process_raw))
    report.update(log_sha256=hashlib.sha256(raw).hexdigest(),
                  process_sha256=hashlib.sha256(process_raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
