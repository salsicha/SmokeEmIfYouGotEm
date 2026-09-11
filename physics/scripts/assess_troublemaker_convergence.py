"""Screen saved hydraulic audits for mean-flow settling, not visual acceptance.

Tolerances are diagnostic authoring choices, not measured river uncertainty:
last four samples, section discharge within 5% of target, storage rate within
2% of target and each region's median stage range within 1 cm. Instantaneous
numerical boundary flux must still be checked separately. Passing this screen
does not validate bathymetry, turbulence, breaking geometry or animation.
"""
from pathlib import Path
import argparse
import json
import math


def assess(audit, samples=4):
    target = audit.get('experimental_prescribed_discharge_m3s')
    if target is None:
        target = (audit.get('warm_start_provenance') or {}).get('target_discharge_m3s')
    if target is None or not math.isfinite(target) or target <= 0:
        raise ValueError('a finite positive target discharge must be recorded in the audit')
    if samples < 3:
        raise ValueError('at least three samples are needed for this convergence screen')
    rows = audit['snapshots'][-samples:]
    if len(rows) != samples:
        raise ValueError('insufficient recorded samples')
    times = [float(r['nominal_cumulative_seconds']) for r in rows]
    volumes = [float(r['volume_m3']) for r in rows]
    sections = [[float(s['discharge_m3s']) for s in r['sections']] for r in rows]
    stations = [[s['station_m'] for s in r['sections']] for r in rows]
    regions = [[rgn['station_range_m'] for rgn in r['regions']] for r in rows]
    if not sections[0] or any(s != stations[0] for s in stations) or any(r != regions[0] for r in regions):
        raise ValueError('all samples must have identical nonempty measurement locations')
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('sample times must increase strictly')
    if any(len(rgn['stage_p10_p50_p90_m']) != 3 for r in rows for rgn in r['regions']):
        raise ValueError('each region needs wet stage measurements')
    stages = [[float(rgn['stage_p10_p50_p90_m'][1]) for rgn in r['regions']] for r in rows]
    values = times + volumes + [q for qs in sections for q in qs] + [s for ss in stages for s in ss]
    if not all(math.isfinite(v) for v in values) or not stages[0]:
        raise ValueError('convergence inputs must be finite and contain measured regions')
    storage = [(b-a)/(tb-ta) for a, b, ta, tb in zip(volumes, volumes[1:], times, times[1:])]
    relative_q_error = max(abs(q-target)/target for qs in sections for q in qs)
    relative_storage = max(abs(v)/target for v in storage)
    stage_ranges = [max(s[i] for s in stages)-min(s[i] for s in stages) for i in range(len(stages[0]))]
    checks = {'section_flux_within_5_percent': relative_q_error <= .05,
              'interval_storage_within_2_percent_of_target': relative_storage <= .02,
              'regional_median_stage_range_within_1cm': max(stage_ranges) <= .01}
    return {'scope': __doc__.strip(), 'mean_flow_screen_passed': all(checks.values()),
            'photorealism_accepted': False, 'production_promoted': False,
            'target_discharge_m3s': target, 'sample_count': samples,
            'time_range_seconds': [times[0], times[-1]],
            'maximum_section_discharge_relative_error': relative_q_error,
            'interval_storage_m3s': storage,
            'maximum_storage_relative_to_target': relative_storage,
            'regional_median_stage_ranges_m': stage_ranges, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = assess(json.loads(args.audit.read_text()))
    result['source_audit'] = str(args.audit.resolve())
    with args.output.open('x') as output:
        output.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
