"""Validate all prepared-profile query comparisons; not motion or performance acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROW = re.compile(r'PREPARED_CREST_EPOCH epoch=(\d+) frame=(\d+) queries=(\d+) mismatches=(\d+)$')


def summarize(text):
    if 'Prepared physical crest candidate active: audit=1;' not in text:
        raise ValueError('Native audit activation missing')
    rows = []
    for line in text.splitlines():
        if 'PREPARED_CREST_EPOCH' not in line:
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Malformed native epoch')
        epoch, frame, queries, mismatches = map(int, match.groups())
        if mismatches or epoch != len(rows) or (rows and frame < rows[-1]['frame']):
            raise ValueError('Mismatch, duplicate or out-of-order epoch')
        rows.append(dict(epoch=epoch, frame=frame, queries=queries, mismatches=mismatches))
    if sum(r['queries'] > 0 for r in rows) < 64:
        raise ValueError('At least64 nonempty native epochs required')
    return dict(schema='raftsim.prepared_crest_epochs.v1', rows=rows,
                queried_epochs=sum(r['queries'] > 0 for r in rows),
                queries=sum(r['queries'] for r in rows), exact=True,
                performance_accepted=False, visual_accepted=False, scope=__doc__)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('log', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    raw = a.log.read_bytes()
    report = summarize(raw.decode('utf-8-sig'))
    report.update(log=str(a.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with a.report.open('x') as out:
        json.dump(report, out, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
