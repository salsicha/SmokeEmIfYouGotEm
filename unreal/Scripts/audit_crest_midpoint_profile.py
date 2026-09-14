"""Strict paired actual-input midpoint timing; never ordinary-game FPS evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROW=re.compile(r'CrestMidpointAudit exact frame=(\d+) vertices=(\d+) midpoints=(\d+) bands=(\d+) '
               r'serial_ms=(\S+) parallel_ms=(\S+) parallel_first=(\d+)')


def summary(values):
    ordered=sorted(values)
    return dict(count=len(values),mean=statistics.mean(values),median=statistics.median(values),
                p95=ordered[math.ceil(.95*len(ordered))-1],maximum=ordered[-1])


def audit(log,first=120,last=250):
    if first<0 or last<first:raise ValueError('Invalid frame interval')
    if 'CrestMidpointAudit mismatch' in log:raise ValueError('Actual vertex attribute mismatch')
    records=[]
    for line in log.splitlines():
        if 'CrestMidpointAudit exact' not in line:continue
        match=ROW.search(line)
        if not match:raise ValueError('Malformed midpoint audit record')
        frame,vertices,midpoints,bands,serial,parallel,order=match.groups()
        record=dict(frame=int(frame),vertices=int(vertices),midpoints=int(midpoints),bands=int(bands),
                    serial_ms=float(serial),parallel_ms=float(parallel),parallel_first=int(order))
        if (record['parallel_first']!=record['frame']%2 or record['vertices']<record['midpoints']
                or not 0<=record['bands']<=record['midpoints']
                or (record['midpoints']>0 and record['bands']==0)
                or any(not math.isfinite(record[k]) or record[k]<0 for k in ('serial_ms','parallel_ms'))):
            raise ValueError('Invalid midpoint counts/timing/order')
        if first<=record['frame']<=last:records.append(record)
    if set(r['frame'] for r in records)!=set(range(first,last+1)):
        raise ValueError('Missing requested frame; no skipped-frame acceptance')
    if not any(r['midpoints'] for r in records):raise ValueError('No actual midpoint workload')
    if {r['parallel_first'] for r in records}!={0,1}:raise ValueError('Both call orders required')
    by_frame={frame:dict(serial_ms=0.,parallel_ms=0.) for frame in range(first,last+1)}
    for r in records:
        for key in ('serial_ms','parallel_ms'):by_frame[r['frame']][key]+=r[key]
    return dict(first_frame=first,last_frame=last,frames=len(by_frame),calls=len(records),
        exact_vertex_attribute_sets=sum(r['vertices'] for r in records),
        actual_midpoint_evaluations_per_variant=sum(r['midpoints'] for r in records),
        bands=sorted({r['bands'] for r in records}),
        per_call={key:summary([r[key] for r in records]) for key in ('serial_ms','parallel_ms')},
        per_frame={key:summary([r[key] for r in by_frame.values()]) for key in ('serial_ms','parallel_ms')},
        benefit_ms=summary([r['serial_ms']-r['parallel_ms'] for r in records]),
        call_order_benefit_ms={str(order):summary([r['serial_ms']-r['parallel_ms'] for r in records if r['parallel_first']==order])
                               for order in (0,1)},
        ordinary_game_fps_accepted=False,visual_or_physics_accepted=False,
        limitations='Paired same-input midpoint expansion only. Full attributes compare exactly, excluding unobservable struct padding. '
        'Includes candidate dependency-plan lookup/rebuild and parallel joins. Does not include source packing, history, '
        'crest selection or normals; those remain unchanged. Shared system load and order effects must be retained.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('log',type=Path)
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--first',type=int,default=120)
    parser.add_argument('--last',type=int,default=250);args=parser.parse_args()
    raw=args.log.read_bytes();result=audit(raw.decode('utf-8',errors='replace'),args.first,args.last)
    result.update(log=str(args.log.resolve()),log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
