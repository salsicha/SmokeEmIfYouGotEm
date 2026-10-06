"""Test Bidwell's full exit, not just crossing the old 1015 m finish.

The 45 m driver reached 1013 m without contact, then clipped the right bank.
The source terrain at lateral -6 m rises to water level there. These routes
are explicit hypotheses, not surveyed safe lines; no terrain/forces change.
"""
import argparse
import copy
import json
from pathlib import Path
from build_rapid_driver_controls import plans


def build():
    plan=next(p for p in plans() if p['river']=='chilko')
    baseline=copy.deepcopy(next(t for t in plan['trials'] if t['variant']=='driver-lookahead45'))
    baseline.update(finish_m=1080, gates=[dict(id='exit_'+str(s),station_m=s) for s in (930,985,1020,1075)])
    old=baseline['route_laterals']
    baseline['route_laterals']=old+[[1080,old[-1][1]]]
    rows=[]
    for name,route in (
        ('old-right-exit',baseline['route_laterals']),
        ('centered-exit',[[650,-4],[814.25,-6],[920,-5],[975,1],[1080,1]]),
        ('late-center-exit',[[650,-4],[814.25,-6],[970,-5],[1025,1],[1080,1]])):
        row=copy.deepcopy(baseline)
        row.update(id='bidwell--'+name, variant=name, route_laterals=route,
                   route_authority='Explicit exit-route hypothesis; validate complete full-hull clearance and runout')
        rows.append(row)
    plan.update(trials=rows,campaign_scope='Matched input-only exit controls; 65 m extended runout; no class acceptance')
    return [plan]


def matched_core():
    """Keep the upstream route exactly linear-identical to the control.

    v1 changed the slope after 814.25 m and consequently hit the bank at
    850-870 m, BEFORE the intended exit move. Anchor the unchanged original
    interpolation before the move; do not label those contacts exit failures.
    """
    plan=build()[0]
    baseline=plan['trials'][0]
    route=baseline['route_laterals']
    def old_lateral(station):
        for (a,x),(b,y) in zip(route,route[1:]):
            if a<=station<=b:return x+(y-x)*(station-a)/(b-a)
        raise ValueError('Exit anchor outside original route')
    rows=[copy.deepcopy(baseline)]
    for name,start,end in (('matched-early-exit',930,980),('matched-late-exit',980,1030)):
        row=copy.deepcopy(baseline)
        row.update(id='bidwell--'+name,variant=name,
            route_laterals=copy.deepcopy(route[:2])+[[start,old_lateral(start)],[end,1],[1080,1]])
        rows.append(row)
    plan['trials']=rows
    plan['campaign_scope']='Same upstream interpolation; input-only exit timing at full 1080 m finish'
    return [plan]


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--matched-core',action='store_true')
    a=p.parse_args()
    if a.out.exists(): raise SystemExit('Fresh controls path required')
    a.out.write_text(json.dumps(matched_core() if a.matched_core else build(),indent=2)+'\n',encoding='utf-8')
