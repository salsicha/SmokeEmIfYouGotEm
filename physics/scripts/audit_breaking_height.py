"""Summarize a one-shot live crest-height diagnostic, not visual acceptance."""
import argparse
import json
import math
from pathlib import Path

FIELDS = ('world_s station_m lateral_m up_depth_m up_fr down_fr raw_rise_m '
          'optical_rise_m raw_extra_m optical_extra_m coverage clearance_m accepted').split()


def parse(text):
    rows = []
    for line in text.splitlines():
        if 'BreakingHeightAudit world_s=' not in line:
            continue
        tokens = line.split('BreakingHeightAudit ', 1)[1].split()
        pairs = [token.split('=', 1) for token in tokens]
        if len(pairs) != len(FIELDS) or any(len(pair) != 2 for pair in pairs):
            raise ValueError('Malformed diagnostic row')
        row = {key: float(value) for key, value in pairs}
        if set(row) != set(FIELDS) or not all(math.isfinite(v) for v in row.values()):
            raise ValueError('Invalid or missing diagnostic fields')
        if row['accepted'] not in (0., 1.):
            raise ValueError('Invalid acceptance flag')
        rows.append(row)
    if not rows or len({r['world_s'] for r in rows}) != 1:
        raise ValueError('Expected one nonempty diagnostic snapshot')
    return rows


def summarize(rows, lower, upper):
    selected = [r for r in rows if r['accepted'] and lower <= r['station_m'] <= upper]
    return dict(station_interval_m=[lower, upper], pre_deduplication_candidate_count=len(selected),
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
    rows = parse(args.log.read_text())
    result = dict(source_log=str(args.log.resolve()), snapshot_time_s=rows[0]['world_s'],
        scope='Detected transitions before site deduplication/persistence; not final rendered crest heights or support parity.',
        photorealism_accepted=False, **summarize(rows, *args.stations))
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'candidates'}))
