"""Fresh native controls for Badger's entry choice and following wave angle.

Authored route hypotheses, not surveyed clearances or a class-match receipt.
The same production map and input driver execute every control.
"""
import argparse
import copy
import json
from pathlib import Path
from build_catalog_map_smoke_plan import build as integration


def build(contract,stage='screen'):
    if stage not in ('screen','intercept'):
        raise ValueError('Unknown Badger control stage')
    plans = integration(contract, 700., 1050.)
    plan = plans[0]
    plan['calibration_scope'] = (
        'Badger upper-right hydraulic avoidance and square wave approach at 8000 cfs; '
        'early/late correction share the same right approach. Normal inputs only; '
        'no class equivalence or continuous route-width claim from gate tracks.')
    base = plan['trials'][0]
    base.update(rapid_id='badger_creek', catalog_class='Grand Canyon 5 (guide 1-10 scale)',
                gates=[dict(id='approach',station_m=740),
                       dict(id='entry_hydraulic',station_m=790),
                       dict(id='wave_train',station_m=875),
                       dict(id='pool_exit',station_m=1048)])
    cases = [
        ('tongue', [[700,0],[1050,0]], {}),
        ('right-hydraulic', [[700,-21],[1050,-21]], {}),
        ('right-early', [[700,-21],[720,-21],[770,0],[1050,0]], {}),
        ('right-late', [[700,-21],[770,-21],[820,0],[1050,0]], {}),
        ('left-bypass', [[700,15],[1050,15]], {}),
        ('train-poor-angle', [[700,0],[1050,0]],
         dict(heading_offset_deg=60.,heading_start_m=820.,heading_end_m=930.)),
        ('hands-off', [[700,0],[1050,0]], {}),
    ]
    if stage=='intercept':
        # The original -21 m target actually passed the lip at -30.81 m,
        # outside the strong roller. Do not mistake intended lane for contact
        # or widen a real-world hazard merely to catch an inaccurate driver.
        cases=[
            ('intercept-line',[[700,-12],[1050,-12]],{}),
            ('intercept-no-steering',[[700,-12],[1050,-12]],dict(disable_steering=True)),
            ('intercept-poor-angle',[[700,-12],[1050,-12]],
             dict(heading_offset_deg=60.,heading_start_m=760.,heading_end_m=815.)),
        ]
    plan['trials'] = []
    for variant,route,options in cases:
        trial = copy.deepcopy(base)
        trial.update(id='badger_creek--'+variant,variant=variant,
                     route_laterals=route,**options)
        plan['trials'].append(trial)
    return plans


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--stage',choices=('screen','intercept'),default='screen')
    a=p.parse_args()
    if a.out.exists():raise SystemExit('Fresh evidence plan required')
    a.out.write_text(json.dumps(build(json.loads(a.contract.read_text()),a.stage),indent=2)+'\n')
