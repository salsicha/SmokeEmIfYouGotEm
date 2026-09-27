"""Summarize a one-shot live crest-height diagnostic, not visual acceptance."""
import argparse
import json
import math
from pathlib import Path

FIELDS = ('world_s station_m lateral_m up_depth_m up_fr down_fr raw_rise_m '
          'optical_rise_m raw_extra_m optical_extra_m coverage clearance_m accepted').split()
SPATIAL_FIELDS = ('down_station_m down_lateral_m up_surface_m down_surface_m '
                  'up_bed_m down_bed_m flow_direction_x flow_direction_y').split()


def parse(text):
    rows = []
    for line in text.splitlines():
        if 'BreakingHeightAudit world_s=' not in line:
            continue
        tokens = line.split('BreakingHeightAudit ', 1)[1].split()
        pairs = [token.split('=', 1) for token in tokens]
        if len(pairs) not in (len(FIELDS), len(FIELDS)+len(SPATIAL_FIELDS)) or any(len(pair) != 2 for pair in pairs):
            raise ValueError('Malformed diagnostic row')
        row = {key: float(value) for key, value in pairs}
        if (set(row) not in (set(FIELDS), set(FIELDS+SPATIAL_FIELDS)) or
                len(row) != len(pairs) or not all(math.isfinite(v) for v in row.values())):
            raise ValueError('Invalid or missing diagnostic fields')
        if row['accepted'] not in (0., 1.):
            raise ValueError('Invalid acceptance flag')
        if 'up_surface_m' in row:
            # Three independently rounded four-decimal measurements. These
            # checks detect mismatched endpoints without demanding more precision
            # than the native log supplies. They do not validate the hydraulic model.
            if abs(row['down_surface_m']-row['up_surface_m']-row['raw_rise_m']) > .00016:
                raise ValueError('Spatial surface rise does not match source endpoints')
            if abs(math.hypot(row['flow_direction_x'], row['flow_direction_y'])-1.) > .000002:
                raise ValueError('Invalid spatial flow direction')
        rows.append(row)
    if not rows or len({r['world_s'] for r in rows}) != 1:
        raise ValueError('Expected one nonempty diagnostic snapshot')
    if len({len(r) for r in rows}) != 1:
        raise ValueError('Mixed spatial and legacy records')
    return rows


def summarize(rows, lower, upper):
    selected = [r for r in rows if r['accepted'] and lower <= r['station_m'] <= upper]
    return dict(station_interval_m=[lower, upper], pre_deduplication_candidate_count=len(selected),
        spatial_geometry_available=bool(selected) and all('up_surface_m' in r for r in selected),
        rise_reversed_count=sum(r['raw_rise_m'] > 0 and r['optical_rise_m'] < 0 for r in selected),
        maximum_extra_height_deficit_m=max((r['optical_extra_m']-r['raw_extra_m'] for r in selected), default=0.),
        maximum_raw_extra_height_m=max((r['raw_extra_m'] for r in selected), default=0.),
        candidates=selected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--stations', type=float, nargs=2, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not all(math.isfinite(x) for x in args.stations) or args.stations[0] > args.stations[1]:
        parser.error('Expected a finite ordered station interval')
    import hashlib
    raw = args.log.read_bytes()
    rows = parse(raw.decode('utf-8-sig'))
    result = dict(source_log=str(args.log.resolve()), source_log_sha256=hashlib.sha256(raw).hexdigest(),
        snapshot_time_s=rows[0]['world_s'],
        scope='Detected transitions before site deduplication/persistence; not final rendered crest heights or support parity.',
        photorealism_accepted=False, **summarize(rows, *args.stations))
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'candidates'}))
