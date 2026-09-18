"""Strict corner-range experiment adapter for the existing 64-pair protocol.

Require this experiment's schema before sharing invariant/statistical checks.
Never rewrite the capture, omit pairs, or turn component timing into FPS proof.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_crest_interval_pair import summarize as summarize_pairs


def summarize(report):
    if report.get('schema') != 'raftsim.crest_corner_range_pair.v1':
        raise ValueError('Original corner-range experiment report required')
    # The wire fields and alternating-pair contract are intentionally identical.
    # Adapt only the validator input; hash and retain the original capture bytes.
    result = summarize_pairs({**report, 'schema': 'raftsim.crest_interval_pair.v1'})
    result['scope'] = ('Whole adaptive build on paired current inputs. Candidate samples '
        'corners before the range bound and skips only bounds unable to reject. Same '
        'quarter-point selection, tolerance and detail window; exact ordered topology, '
        'ownership, coordinates and production topology. Not FPS or visual acceptance.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_topology_and_production'] and result['measured_both_orders_faster'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
