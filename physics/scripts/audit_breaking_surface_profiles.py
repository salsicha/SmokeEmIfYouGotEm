"""Audit actual carrier transects; never infer visual or hydraulic acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(row, name):
    value = row[name]
    require(type(value) in (int, float) and math.isfinite(value), f'Invalid {name}')
    return value


def flag(row, name):
    require(type(row[name]) is bool, f'Invalid {name}')
    return row[name]


def profile_summary(rows, field, available):
    values = [r[field] for r in rows if available(r)]
    slopes = [abs((b[field]-a[field])/(b['along_m']-a['along_m']))
              for a, b in zip(rows, rows[1:]) if available(a) and available(b)]
    # Never bridge a dry/unavailable gap or count missing samples as zero height.
    return dict(samples=len(values), adjacent_segments=len(slopes),
                minimum_m=min(values) if values else None,
                maximum_m=max(values) if values else None,
                range_m=max(values)-min(values) if values else None,
                maximum_adjacent_abs_slope=max(slopes) if slopes else None)


def summarize(report):
    require(report['schema'] == 'raftsim.breaking_surface_profiles.v2', 'Unknown or obsolete height-frame schema')
    require(report['raw_height_frame'] == 'datum_relative_world_z_m', 'Unknown raw height frame')
    datum = number(report, 'river_vertical_datum_m')
    for key in ('world_seconds', 'committed_water_seconds'):
        require(number(report, key) >= 0, f'Negative {key}')
    detail = flag(report, 'presented_detail_available')
    if detail:
        sequence = number(report, 'presented_detail_sequence')
        require(sequence > 0 and int(sequence) == sequence, 'Invalid detail sequence')
        for key in ('presented_detail_simulation_seconds', 'presented_detail_elapsed_seconds'):
            require(number(report, key) >= 0, f'Negative {key}')
    require(isinstance(report['sites'], list) and report['sites'], 'No selected sites')
    result = []
    for site in report['sites']:
        for key in ('east_m', 'north_m', 'direction_east', 'direction_north',
                    'additional_crest_m', 'spilling_fraction', 'presentation_weight'):
            number(site, key)
        dx, dy = site['direction_east'], site['direction_north']
        require(abs(math.hypot(dx, dy)-1) < 2.e-6, 'Invalid flow axis')
        for key in ('spilling_fraction', 'presentation_weight'):
            require(0 <= site[key] <= 1, f'Invalid {key}')
        require(isinstance(site['samples'], list) and len(site['samples']) == 291,
                'Expected three complete 97-point transects')
        seen = set()
        for row in site['samples']:
            for key in ('along_m', 'across_m', 'east_m', 'north_m'):
                number(row, key)
            along, across = row['along_m'], row['across_m']
            require(across in (-2, 0, 2) and -12 <= along <= 12 and along*4 == int(along*4),
                    'Invalid sampling lattice')
            require((along, across) not in seen, 'Duplicate probe')
            seen.add((along, across))
            require(abs(row['east_m']-(site['east_m']+dx*along-dy*across)) < 1.e-4 and
                    abs(row['north_m']-(site['north_m']+dy*along+dx*across)) < 1.e-4,
                    'Probe not in declared flow frame')
            raw, wet, carrier = (flag(row, k) for k in ('raw_available', 'raw_wet', 'carrier_wet'))
            require(not wet or raw, 'Wet sample without raw state')
            if raw:
                for key in ('raw_surface_world_m', 'raw_bed_world_m', 'raw_depth_m',
                            'raw_velocity_east_mps', 'raw_velocity_north_mps'):
                    number(row, key)
                require(row['raw_depth_m'] >= 0, 'Negative raw depth')
                for component in ('surface', 'bed'):
                    absolute = number(row, f'raw_{component}_absolute_m')
                    require(abs(absolute-datum-row[f'raw_{component}_world_m']) < 1.e-8,
                            'Inconsistent raw datum conversion')
            if carrier:
                number(row, 'carrier_macro_world_m')
                if detail:
                    number(row, 'presented_detail_m')
                    number(row, 'carrier_with_detail_world_m')
                    require(abs(row['carrier_with_detail_world_m']-row['carrier_macro_world_m']-
                                row['presented_detail_m']) < 1.e-8, 'Inconsistent combined height')
        transects = []
        for across in (-2, 0, 2):
            rows = sorted((r for r in site['samples'] if r['across_m'] == across),
                          key=lambda r: r['along_m'])
            paired = [r for r in rows if r['raw_wet'] and r['carrier_wet']]
            transects.append(dict(across_m=across,
                raw=profile_summary(rows, 'raw_surface_world_m', lambda r: r['raw_wet']),
                macro=profile_summary(rows, 'carrier_macro_world_m', lambda r: r['carrier_wet']),
                with_detail=profile_summary(rows, 'carrier_with_detail_world_m',
                    lambda r: detail and r['carrier_wet']),
                paired_samples=len(paired),
                maximum_abs_macro_minus_raw_m=max((abs(r['carrier_macro_world_m']-r['raw_surface_world_m'])
                    for r in paired), default=None),
                maximum_abs_detail_m=max((abs(r['presented_detail_m']) for r in rows
                    if detail and r['carrier_wet']), default=None)))
        result.append(dict(east_m=site['east_m'], north_m=site['north_m'],
                           additional_crest_m=site['additional_crest_m'],
                           spilling_fraction=site['spilling_fraction'], transects=transects))
    return dict(schema='raftsim.breaking_surface_profile_summary.v2',
        river_vertical_datum_m=datum, raw_height_frame=report['raw_height_frame'],
        presented_detail_sequence=report.get('presented_detail_sequence'),
        presented_detail_simulation_seconds=report.get('presented_detail_simulation_seconds'),
        presented_detail_elapsed_seconds=report.get('presented_detail_elapsed_seconds'),
        world_seconds=report['world_seconds'], committed_water_seconds=report['committed_water_seconds'],
        scope='Straight transects through one actual submitted surface snapshot; not streamlines, motion, energy loss, physics calibration or FPS.',
        surface_realism_accepted=False, sites=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.capture.read_bytes()
    result = summarize(json.loads(raw))
    result.update(source=str(args.capture.resolve()), source_sha256=hashlib.sha256(raw).hexdigest())
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(f"Audited {len(result['sites'])} selected-site profiles; no acceptance inferred")


if __name__ == '__main__':
    main()
