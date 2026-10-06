"""Exact indexed-edge A/B qualification using the unchanged complete-pair gates."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_crest_edge_hash_pair import summarize as summarize_edge_hash


def summarize(report):
    for row in report['pairs']:
        if not {'indexed_first', 'indexed_ms', 'indexed_assembly_ms'} <= row.keys():
            raise ValueError('Native indexed-edge fields required')
        if any('strong' in key for key in row):
            raise ValueError('Mixed edge-hash/indexed-edge evidence is not accepted')
    # Reuse the original completeness, finite timing, exactness and BOTH-order
    # gates, not its implementation label. Never modify the native evidence.
    translated = dict(report, pairs=[{
        key.replace('indexed', 'strong'): value for key, value in row.items()
    } for row in report['pairs']])
    result = summarize_edge_hash(translated)

    def labels(value):
        if isinstance(value, dict):
            return {key.replace('strong', 'indexed'): labels(item) for key, item in value.items()}
        return value

    result = labels(result)
    result['scope'] = ('Whole adaptive-build indexed-edge CPU comparison on actual changed inputs, '
                       'including map construction; not ordinary FPS, visual or physics acceptance.')
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
