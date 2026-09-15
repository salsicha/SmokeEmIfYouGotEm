"""Strict actual-input range-bound comparison; never FPS or release acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_crest_inline_pair import summarize as summarize_build_pair


def summarize(report):
    # Reuse the unchanged 64-pair/order/exact-count/timing validation. Only
    # field names differ; no rows, timings or failure results are discarded.
    mapped = dict(exact=report.get('exact'), pairs=[dict(row,
        inline_first=row['bounded_first'], erased_ms=row['reference_ms'], inline_ms=row['bounded_ms'])
        for row in report['pairs']])
    result = summarize_build_pair(mapped)
    groups = {}
    for name, group in result['groups'].items():
        name = name.replace('erased', 'reference').replace('inline', 'bounded')
        groups[name] = {key.replace('erased', 'reference').replace('inline', 'bounded'): value
                        for key, value in group.items()}
    result['groups'] = groups
    result['scope'] = ('Conservative range-bound versus original adaptive-build CPU comparison on actual changed inputs; '
                       'same topology and selection tolerance, not ordinary FPS, visual or physics acceptance.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_topology_and_coordinates'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
