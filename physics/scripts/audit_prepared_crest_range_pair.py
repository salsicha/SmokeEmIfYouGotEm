"""Exact current-input refinement comparison, charging immutable preparation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_crest_inline_pair import summarize as summarize_build_pair


def summarize(report):
    mapped = []
    for row in report['pairs']:
        for key in ('prepared_ms', 'preparation_ms'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('Finite nonnegative candidate timings required')
        if row['prepared_ms'] == 0:
            raise ValueError('Positive build timing required')
        mapped.append(dict(row, inline_first=row['prepared_first'], erased_ms=row['reference_ms'],
                           inline_ms=row['prepared_ms'] + row['preparation_ms']))
    result = summarize_build_pair(dict(exact=report.get('exact'), pairs=mapped))
    rename = lambda s: s.replace('erased', 'reference').replace('inline', 'prepared_including_preparation')
    result['groups'] = {rename(name): {rename(k): v for k, v in group.items()}
                        for name, group in result['groups'].items()}
    result['scope'] = ('Same-input whole refinement builds, charging preparation to EVERY candidate build '
                       'even when a profile is reused. No FPS, visual, physics or release acceptance.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if result['exact_topology_and_coordinates'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
