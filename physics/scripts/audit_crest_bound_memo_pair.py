"""Exact live-input lookup-binding timings, not gameplay FPS acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_crest_inline_pair import summarize as summarize_build_pair


def summarize(report):
    mapped = dict(exact=report.get('exact'), pairs=[dict(row,
        inline_first=row['bound_first'], erased_ms=row['reference_ms'], inline_ms=row['bound_ms'])
        for row in report['pairs']])
    result = summarize_build_pair(mapped)
    result['groups'] = {
        name.replace('erased', 'reference').replace('inline', 'bound'): {
            key.replace('erased', 'reference').replace('inline', 'bound'): value for key, value in group.items()
        } for name, group in result['groups'].items()
    }
    memory = {}
    for field in ('reference_retained_bytes', 'bound_retained_bytes'):
        values = [row[field] for row in report['pairs']]
        if any(type(value) not in (int, float) or not 0 <= value < 2**53 or int(value) != value for value in values):
            raise ValueError('Finite nonnegative exact byte counts required')
        memory[field + '_maximum'] = max(values)
    result['retained_memory'] = memory
    result['scope'] = ('Exact per-triangle coordinate-binding versus original adaptive-build CPU comparison; '
                       'current profile values recomputed each epoch. No mesh, cadence or tolerance reduction. '
                       'Not ordinary FPS, visual, hydraulic or release acceptance.')
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
