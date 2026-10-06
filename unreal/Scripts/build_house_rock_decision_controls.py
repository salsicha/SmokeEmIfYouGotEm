"""Matched production-raft approaches for House Rock, not a difficulty grade.

The rightward move and left-side hydraulics follow the guide's qualitative
description. Routes and trigger stations are authored test hypotheses; inspect
actual tracks before calling an intended lane a successful passage.
"""
import argparse
import copy
import json
from pathlib import Path
from build_catalog_map_smoke_plan import build as integration


def build(contract):
    if contract['section_id'] != 'catalog_house_rock':
        raise ValueError('House Rock coordinates required')
    plan = integration(contract, 700., 1060.)[0]
    plan['calibration_scope'] = (
        'House Rock rightward setup against left-side hydraulics at 8000 cfs. '
        'Authored route hypotheses, actual ordinary oar controls. '
        'Not a measured route-width, surveyed obstacle or class-equivalence claim.')
    base = plan['trials'][0]
    base.update(rapid_id='house_rock', catalog_class='Grand Canyon 7 (guide 1-10 scale)',
                gates=[dict(id='approach',station_m=760),
                       dict(id='lateral',station_m=842),
                       dict(id='first_hole',station_m=882),
                       dict(id='second_hole',station_m=910),
                       dict(id='pool_exit',station_m=1058)])
    cases = [
        ('right-prepared', [[700,-8],[1060,-8]], {}),
        ('left-early', [[700,12],[720,12],[820,-8],[1060,-8]], {}),
        ('left-late', [[700,12],[800,12],[900,-8],[1060,-8]], {}),
        ('left-no-steering', [[700,12],[1060,12]], dict(disable_steering=True)),
        ('right-poor-angle', [[700,-8],[1060,-8]],
         dict(heading_offset_deg=60.,heading_start_m=820.,heading_end_m=935.)),
        ('hands-off', [[700,12],[1060,12]], {}),
    ]
    plan['trials'] = []
    for variant, route, options in cases:
        trial = copy.deepcopy(base)
        trial.update(id='house_rock--'+variant,variant=variant,
                     route_laterals=route,**options)
        plan['trials'].append(trial)
    return [plan]


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise SystemExit('Fresh evidence plan required')
    a.out.write_text(json.dumps(build(json.loads(a.contract.read_text())),indent=2)+'\n')
