"""Validate paired exact region-index reconstructions; not ordinary FPS evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from audit_crest_midpoint_profile import summary

ROW=re.compile(r'CrestRegionAudit exact frame=(\d+) regions=(\d+) vertices=(\d+) triangles=(\d+) '
               r'linear_ms=(\S+) indexed_ms=(\S+) indexed_first=(\d+)')
UNCHANGED=re.compile(r'CrestRegionAudit unchanged frame=(\d+)')


def audit(log,first=120,last=250):
    if first<0 or last<first:raise ValueError('Invalid interval')
    if 'CrestRegionAudit mismatch' in log:raise ValueError('Reconstruction mismatch')
    rows=[];unchanged=[]
    for line in log.splitlines():
        if 'CrestRegionAudit' not in line or 'CrestRegionAudit=' in line:continue
        # Command lines mention the opt-in flag, not an audit record.
        if 'CrestRegionAudit exact' in line:
            match=ROW.search(line)
            if not match:raise ValueError('Malformed exact record')
            f,r,v,t,a,b,o=match.groups()
            row=dict(frame=int(f),regions=int(r),vertices=int(v),triangles=int(t),
                     linear_ms=float(a),indexed_ms=float(b),indexed_first=int(o))
            if (row['indexed_first']!=row['frame']%2 or row['vertices']==0 or row['triangles']==0
                or any(not math.isfinite(row[k]) or row[k]<0 for k in ('linear_ms','indexed_ms'))):
                raise ValueError('Invalid counts, timing or order')
            if first<=row['frame']<=last:rows.append(row)
        elif 'CrestRegionAudit unchanged' in line:
            match=UNCHANGED.search(line)
            if not match:raise ValueError('Malformed unchanged record')
            if first<=int(match[1])<=last:unchanged.append(int(match[1]))
    if {r['frame'] for r in rows}|set(unchanged)!=set(range(first,last+1)):
        raise ValueError('Missing frame; unchanged calls must be explicit')
    if not rows or not any(r['regions'] for r in rows):raise ValueError('No region workload')
    if {r['indexed_first'] for r in rows}!={0,1}:raise ValueError('Both call orders required')
    totals={f:dict(linear_ms=0.,indexed_ms=0.) for f in range(first,last+1)}
    for r in rows:
        for k in ('linear_ms','indexed_ms'):totals[r['frame']][k]+=r[k]
    return dict(first_frame=first,last_frame=last,frames=len(totals),build_calls=len(rows),
        unchanged_calls=len(unchanged),regions=sorted({r['regions'] for r in rows}),
        exact_expanded_vertices=sum(r['vertices'] for r in rows),
        exact_triangles=sum(r['triangles'] for r in rows),
        per_call={k:summary([r[k] for r in rows]) for k in ('linear_ms','indexed_ms')},
        per_frame={k:summary([r[k] for r in totals.values()]) for k in ('linear_ms','indexed_ms')},
        benefit_ms=summary([r['linear_ms']-r['indexed_ms'] for r in rows]),
        call_order_benefit_ms={str(o):summary([r['linear_ms']-r['indexed_ms'] for r in rows if r['indexed_first']==o]) for o in (0,1)},
        ordinary_fps_accepted=False,visual_or_physics_accepted=False,
        limitations='Two independent warm reconstructions of each actual input. Includes per-build index construction. '
        'Original samples, tolerance, parents, triangle order and origins retained. Shared load; no ordinary FPS claim.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path)
    p.add_argument('--report',required=True,type=Path);a=p.parse_args()
    raw=a.log.read_bytes();result=audit(raw.decode('utf-8',errors='replace'))
    result.update(log=str(a.log.resolve()),log_sha256=hashlib.sha256(raw).hexdigest())
    with a.report.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
