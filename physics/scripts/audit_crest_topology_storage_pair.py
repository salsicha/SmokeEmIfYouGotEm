"""Exact retained-capacity A/B qualification; not ordinary FPS acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from audit_crest_edge_hash_pair import summarize as summarize_original


def summarize(report):
    rows = report['pairs']
    for row in rows:
        if not {'retained_first', 'retained_ms', 'retained_assembly_ms', 'root_changed',
                'legacy_storage_bytes', 'retained_storage_bytes'} <= row.keys():
            raise ValueError('Native topology-storage fields required')
        if any('strong' in key or 'indexed' in key for key in row):
            raise ValueError('Mixed candidate evidence is not accepted')
        if type(row['root_changed']) is not bool:
            raise ValueError('Explicit root-change result required')
        for key in ('legacy_storage_bytes', 'retained_storage_bytes'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or int(value) != value:
                raise ValueError('Finite nonnegative native storage counts required')
    if not any(row['root_changed'] for row in rows):
        raise ValueError('Actual root topology changes required')
    translated = dict(report, pairs=[{key.replace('retained', 'strong'): value for key, value in row.items()}
                                    for row in rows])
    result = summarize_original(translated)

    def labels(value):
        if isinstance(value, dict):
            return {key.replace('strong', 'retained'): labels(item) for key, item in value.items()}
        return value

    result = labels(result)
    result.update(root_changes=sum(row['root_changed'] for row in rows),
                  maximum_legacy_storage_bytes=max(row['legacy_storage_bytes'] for row in rows),
                  maximum_retained_storage_bytes=max(row['retained_storage_bytes'] for row in rows),
                  scope='Whole adaptive-build capacity reuse on actual changing roots; exact selection/cache decisions and output, not ordinary FPS, physics or visual acceptance.')
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
