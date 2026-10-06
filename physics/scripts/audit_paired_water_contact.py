"""Fail-closed checker for the engine's paired carrier/support and GPU reports.

This checks one published snapshot, not traversal, swept collision, render
latency, photographic fidelity, or performance. Run on fresh reports from the
same healthy process; matching sequence numbers alone cannot establish that.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def number(report, key, *, integer=False, positive=False):
    value = report[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key}: expected a number")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{key}: expected finite {'positive' if positive else 'nonnegative'} value")
    if integer and int(value) != value:
        raise ValueError(f"{key}: expected an integer")
    return value


def boolean(report, key):
    value = report[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key}: expected a boolean")
    return value


def audit(contact, gpu):
    """Return a scoped numerical regression result, or reject malformed data."""
    sequence = number(contact, 'detail_frame_sequence', integer=True, positive=True)
    gpu_sequence = number(gpu, 'detail_frame_sequence', integer=True, positive=True)
    wet = number(contact, 'tested_wet_points', integer=True, positive=True)
    dry = number(contact, 'raw_dry_points', integer=True)
    unavailable = number(contact, 'unavailable_points', integer=True)
    affected = number(contact, 'detail_affected_contact_points', integer=True)
    maximum = number(contact, 'maximum_support_carrier_error_cm')
    rms = number(contact, 'rms_support_carrier_error_cm')
    height = number(contact, 'maximum_contact_detail_height_cm')
    queries = number(gpu, 'queries', integer=True, positive=True)
    rgba = number(gpu, 'maximum_rgba_error')
    gpu_height = number(gpu, 'maximum_sampled_detail_height_cm')
    number(contact, 'world_seconds', positive=True)
    number(gpu, 'sample_elapsed_seconds')
    number(gpu, 'simulation_seconds')
    if affected > wet or rms > maximum:
        raise ValueError('inconsistent contact counters/error bounds')
    probes = contact['ground_contact_probes']
    if not isinstance(probes, list) or len(probes) != wet + dry + unavailable:
        raise ValueError('probe population does not match contact counters')
    counts = dict(wet=0, dry=0, unavailable=0, occluded=0, occluded_wet=0)
    for probe in probes:
        available = boolean(probe, 'support_available')
        is_wet = boolean(probe, 'support_wet')
        raw_available = boolean(probe, 'raw_available')
        raw_wet = boolean(probe, 'raw_wet')
        if (is_wet and not available) or (raw_wet and not raw_available):
            raise ValueError('wet probe without available support/raw sample')
        counts['unavailable' if not available else ('wet' if is_wet else 'dry')] += 1
        for key in ('x_cm', 'y_cm', 'water_z_cm'):
            value = probe[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'{key}: invalid probe coordinate')
        if boolean(probe, 'ground_hit'):
            ground = probe['ground_z_cm']
            if isinstance(ground, bool) or not isinstance(ground, (int, float)) or not math.isfinite(ground):
                raise ValueError('invalid ground coordinate')
            if probe['water_z_cm'] <= ground:
                counts['occluded'] += 1
                counts['occluded_wet'] += int(is_wet)
    expected = dict(wet=wet, dry=dry, unavailable=unavailable,
                    occluded=number(contact, 'ground_occluded_points', integer=True),
                    occluded_wet=number(contact, 'ground_occluded_wet_points', integer=True))
    if counts != expected:
        raise ValueError('per-probe classifications disagree with summary counters')
    paired = boolean(contact, 'includes_paired_detail')
    requested = boolean(contact, 'detail_gpu_audit_requested')
    gpu_passed = boolean(gpu, 'passed')
    failures = []
    checks = {
        'matching_nonzero_sequence': sequence == gpu_sequence,
        'paired_detail_present_and_audited': paired and requested,
        'nonzero_detail_exercised': affected > 0 and height > 0 and gpu_height > 0,
        'all_support_samples_available': unavailable == 0,
        # A narrow numeric equivalence guard, not a physical accuracy claim.
        'support_matches_submitted_carrier': maximum <= 0.001,
        'gpu_upload_sampler_parity': gpu_passed and rgba < 1e-6,
        'no_wet_support_below_registered_ground': counts['occluded_wet'] == 0,
    }
    failures.extend(name for name, passed in checks.items() if not passed)
    return dict(passed=not failures, failures=failures, checks=checks,
                detail_frame_sequence=sequence, tested_wet_points=wet,
                detail_affected_contact_points=affected, gpu_queries=queries,
                maximum_support_carrier_error_cm=maximum, maximum_rgba_error=rgba,
                probe_counts=counts,
                scope='One paired published snapshot only. Requires fresh same-process inputs. '
                      'Not full traversal, independent source-ground verification, swept collision, '
                      'render latency, visual acceptance or FPS qualification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contact', type=Path)
    parser.add_argument('gpu', type=Path)
    args = parser.parse_args()
    try:
        data = [path.read_bytes() for path in (args.contact, args.gpu)]
        result = audit(*(json.loads(item) for item in data))
        result['input_sha256'] = dict(zip(('contact', 'gpu'),
                                         (hashlib.sha256(item).hexdigest() for item in data)))
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(2, f'Paired water audit refused: {error}\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
