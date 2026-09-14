"""Exact rational and double reconstructed faces around a captured thin cell."""
import argparse
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from diagnose_recorded_polynomials import exact_face
import audit_live_temporal_evolution as temporal


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path)
    parser.add_argument('--interval',type=int,required=True);parser.add_argument('--y',type=int,required=True);parser.add_argument('--x',type=int,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    source=json.loads(args.source.read_text());i=args.interval
    a,b=temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',first=source['observations'][i],second=source['observations'][i+1]))
    state=np.asarray(source['state']).reshape(a['ny'],a['nx'],4);h=state[...,0];bed=a['bed']
    _,boundary=temporal.boundary_provider(a,b);es,eb,_=boundary(sum(source['progress'][:2])-a['native_seconds'],None)
    rows=[]
    for axis in (0,1):
        dh=bank.mc(h,axis,False);de=bank.mc(h,axis,False,other=bed)
        wet=(h>0)&(np.roll(h,1,axis)>0)&(np.roll(h,-1,axis)>0);dh*=wet;de*=wet
        *_,left,right=bank.hydrostatic_faces(h,bed,dh,de,axis,False,(es,eb),reconstruction=True)
        partial=(h>0)&((np.take(left,range(1,left.shape[axis]),axis=axis)==0)|(np.take(right,range(right.shape[axis]-1),axis=axis)==0))
        dh[partial]=0;de[partial]=0
        *_,left,right=bank.hydrostatic_faces(h,bed,dh,de,axis,False,(es,eb),reconstruction=True,flattened=partial)
        for direction in (-1,1):
            p=(args.y,args.x);q=(args.y+direction,args.x) if axis==0 else (args.y,args.x+direction)
            for point,d in ((p,direction),(q,-direction)):
                index=list(point);index[axis]+=int(d>0)
                actual=(left if d>0 else right)[tuple(index)]
                rows.append(dict(axis=axis,direction=d,y=point[0],x=point[1],double_partial=bool(partial[point]),
                    exact_raw=float(exact_face(h,bed,*point,axis,d)),exact_final=float(exact_face(h,bed,*point,axis,d,final=True)),double_final=float(actual)))
    with args.report.open('x') as stream:json.dump(rows,stream,indent=2,allow_nan=False)
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
