"""Matched controls separating steering-driver stalls from physical obstacles.

Only ordinary commands change. No water/hull tuning, target-line scouting,
teleports during a run, reset-as-recovery or artificially refilled stamina.
These controls diagnose the two failed prepared lines; they do not grade rapids.
"""
import argparse
import copy
import json
from pathlib import Path
from build_rapid_decision_campaign import build


def plans():
    result=[]
    for base in build()[1]:
        rapid={'chilko':'bidwell','zambezi':'rapid_18'}.get(base['river'])
        if not rapid: continue
        prepared=next(t for t in base['trials'] if t['id']==rapid+'--prepared')
        if rapid=='bidwell':
            # Historical failed baseline must not silently follow a later
            # corrected campaign route, or old diagnostics cease to match.
            prepared.update(finish_m=1015,route_laterals=[[650,-4],[814.25,-6],[1014,-3]])
            for gate,station in zip(prepared['gates'],(741.25,832.5,923.75,996.75)):
                gate['station_m']=station
        prepared['lookahead_m']=12.  # retain the failing diagnostic baseline even after campaign correction
        plan={k:copy.deepcopy(v) for k,v in base.items() if k!='trials'}
        plan.update(trials=[],campaign_scope='Matched diagnostic controls, not class or safe-width acceptance')
        for name,options in (
            ('driver-baseline',{}),
            ('driver-lookahead45',dict(lookahead_m=45.)),
            ('driver-downstream-heading',dict(heading_start_m=prepared['start_m'],
                 heading_end_m=prepared['finish_m'],heading_offset_deg=0.)),
            ('driver-no-steering',dict(disable_steering=True))):
            trial=copy.deepcopy(prepared)
            trial.update(id=rapid+'--'+name,variant=name,**options)
            plan['trials'].append(trial)
        result.append(plan)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise SystemExit('Fresh diagnostic plan required')
    args.out.write_text(json.dumps(plans(),indent=2)+'\n',encoding='utf-8')
