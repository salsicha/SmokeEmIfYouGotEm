"""Validate same-frame froth/transport velocity evidence; not visual acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def summarize(report):
    if report.get('schema') != 'raftsim.foam_flow_pair.v1' or report.get('paired_frame_valid') is not True:
        raise ValueError('Validated paired native frame required')
    rows = report['samples']
    if not rows or report['vertices'] != len(rows):
        raise ValueError('Complete nonempty sample list required')
    for key in ('game_frame', 'detail_sequence'):
        if type(report[key]) not in (int, float) or not math.isfinite(report[key]) or report[key] <= 0 or report[key] != int(report[key]):
            raise ValueError('Positive native frame identity required')
    for key in ('world_seconds', 'simulation_seconds'):
        if type(report[key]) not in (int, float) or not math.isfinite(report[key]) or report[key] < 0:
            raise ValueError('Finite native clock required')
    previous = -1
    for row in rows:
        for key in ('vertex', 'x_m', 'y_m', 'mean_u_mps', 'mean_v_mps', 'optical_u_mps',
                    'optical_v_mps', 'depth_m', 'coverage', 'difference_mps'):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
                raise ValueError('Finite native sample required')
        if row['vertex'] != int(row['vertex']) or row['vertex'] <= previous:
            raise ValueError('Unique native vertex order required')
        previous = row['vertex']
        if row['depth_m'] <= .01 or not 0 <= row['coverage'] <= 1:
            raise ValueError('Wet bounded-coverage samples required')
        delta = math.hypot(row['mean_u_mps']-row['optical_u_mps'], row['mean_v_mps']-row['optical_v_mps'])
        if not math.isclose(delta, row['difference_mps'], abs_tol=1e-9, rel_tol=1e-9):
            raise ValueError('Native difference does not match retained velocities')
    groups = {}
    for name, selected in [('all', rows), ('coverage_above_point_one', [r for r in rows if r['coverage'] > .1])]:
        groups[name] = dict(samples=len(selected),
            maximum_difference_mps=max((r['difference_mps'] for r in selected), default=None),
            rms_difference_mps=math.sqrt(sum(r['difference_mps']**2 for r in selected)/len(selected)) if selected else None,
            opposed=sum(r['mean_u_mps']*r['optical_u_mps']+r['mean_v_mps']*r['optical_v_mps'] < 0 for r in selected))
    for key in ('maximum_difference_mps', 'rms_difference_mps'):
        if not math.isclose(report[key], groups['all'][key], abs_tol=1e-9, rel_tol=1e-9):
            raise ValueError('Native summary disagrees with complete rows')
    if report['opposed_vertices'] != groups['all']['opposed'] or report['coverage_above_point_one'] != groups['coverage_above_point_one']['samples']:
        raise ValueError('Native population counts disagree')
    return dict(detail_sequence=report['detail_sequence'], game_frame=report['game_frame'], groups=groups,
                scope='Paired displayed-frame input versus submitted optical velocity; not measured fluid motion or pixel attribution.',
                visual_accepted=False, physical_accepted=False, release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as output:
        json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
