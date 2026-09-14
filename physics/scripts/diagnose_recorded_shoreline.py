"""Locate float32/float64 shoreline polynomial decisions on recorded GPU inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_recorded_stages import read_records
import audit_live_temporal_evolution as temporal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path); parser.add_argument('--record', type=int, default=18)
    parser.add_argument('--stage', type=int, default=0); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    meta = json.loads(args.trace.read_text()); source = json.loads(Path(meta['source']).read_text())
    trial, stages, *_ = list(read_records(meta, Path(meta['binary']).read_bytes()))[args.record]
    gpu = stages[args.stage]; i = trial['interval']
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
                                     first=source['observations'][i], second=source['observations'][i+1]))
    _, boundary = temporal.boundary_provider(a, b)
    es, eb, _ = boundary(trial['begin']-a['native_seconds']+(trial['attempted_dt'] if args.stage else 0), None)
    cases = []
    for dtype in (np.float32, np.float64):
        state, bed = gpu['state'][..., :3].astype(dtype), a['bed'].astype(dtype)
        exterior = (es.astype(dtype), eb.astype(dtype))
        rate, _ = bank.rate(state, bed, .5, second_order=True, exterior=exterior)
        error = np.abs(rate-gpu['rate'][..., :3])
        case = dict(dtype=str(dtype), rate_error_max=float(error.max()),
                    cluster_error_max=float(error[76:80,70:75].max()), decisions=[])
        for axis in (1, 0):
            h=state[...,0];dh=bank.mc(h,axis,False);deta=bank.mc(h,axis,False,other=bed)
            wet=(h>0)&(np.roll(h,1,axis)>0)&(np.roll(h,-1,axis)>0);dh*=wet;deta*=wet
            _,_,_,_,hsa,hsb=bank.hydrostatic_faces(h,bed,dh,deta,axis,False,exterior)
            pos=np.take(hsa,range(1,hsa.shape[axis]),axis=axis);neg=np.take(hsb,range(hsb.shape[axis]-1),axis=axis)
            partial=(h>0)&((pos==0)|(neg==0))
            for y in range(76,80):
                for x in range(70,75):
                    case['decisions'].append(dict(axis=axis,y=y,x=x,h=float(h[y,x]),dh=float(dh[y,x]),deta=float(deta[y,x]),
                        positive=float(pos[y,x]),negative=float(neg[y,x]),flatten=bool(partial[y,x])))
        cases.append(case)
    report=dict(scope=__doc__,record=args.record,stage=args.stage,trial=trial,cases=cases)
    with args.report.open('x') as stream: json.dump(report,stream,indent=2,allow_nan=False)
    print([(c['dtype'],c['rate_error_max'],c['cluster_error_max']) for c in cases])
    print(json.dumps([(a,b) for a,b in zip(cases[0]['decisions'],cases[1]['decisions']) if a['flatten']!=b['flatten']],indent=2))


if __name__=='__main__': main()
