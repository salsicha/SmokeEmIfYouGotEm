"""Exact current-build adjacent-box cache comparison, not playable acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_crest_inline_pair import summarize as summarize_build_pair


def summarize(report):
    if report.get('schema') != 'raftsim.crest_adjacent_range_pairs.v1':
        raise ValueError('Adjacent-range native capture schema required')
    mapped = dict(exact=report.get('exact'), pairs=[dict(row,
        inline_first=row['candidate_first'], erased_ms=row['reference_ms'], inline_ms=row['candidate_ms'])
        for row in report['pairs']])
    result = summarize_build_pair(mapped)
    result['groups'] = {
        name.replace('erased', 'reference').replace('inline', 'candidate'): {
            key.replace('erased', 'reference').replace('inline', 'candidate'): value
            for key, value in group.items()
        } for name, group in result['groups'].items()
    }
    result['scope'] = ('Whole adaptive build including allocation/destruction of batch-owned one-box caches; '
                       'current immutable profile only, original exact bounds and topology. '
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
