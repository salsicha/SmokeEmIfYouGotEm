"""Represented-state CPU references for GPU breaking classification and RK2.

Cardinal raster adaptation, not a calibrated river or 3D overturning model.
All inputs are rounded to float32 before the independent double calculation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from breaking_front_reference import dispersion_fraction
from total_depth_pressure import wet_pairs
from export_total_depth_step_fixtures import step_reference
from export_nonlinear_pressure_fixtures import fixture
from audit_detail_wave_regime import read_snapshot
from audit_live_temporal_evolution import observations
from audit_recorded_stages import read_records


def synthetic_cases():
    for kind in ('bore', 'subcell', 'tiny_trough', 'weak', 'downhill', 'lake', 'dry', 'disconnected', 'long_front'):
        h = np.ones((3, 64)); bed = np.zeros_like(h); ht = np.zeros_like(h)
        h[:, 20:40] = 2
        if kind == 'subcell': h[:]=.01; h[:,20:40]=.03; ht[:]=1
        if kind == 'tiny_trough': h[:]=1e-30; h[:,20:40]=2
        if kind == 'weak': h[:,20:40]=1.1; ht[:]=100
        if kind == 'downhill': h[:]=1; bed[:]=np.arange(64)*.25
        if kind == 'lake': bed[:]=np.arange(64)*.125; h=10-bed
        if kind == 'dry': h[:]=0
        if kind == 'disconnected': h[:,20:25]=10
        if kind == 'long_front':
            h=np.ones((1,512)); bed=h*0; ht=h*0
            h[:,1:256]=np.linspace(1,3,255); ht[:]=3
        periodic = kind not in ('downhill','lake','dry','disconnected')
        pairs = wet_pairs(h,bed,periodic)
        if kind == 'disconnected': pairs[0][:,30]=False
        yield kind,h,bed,ht,pairs,1.,periodic,kind in ('bore','subcell','lake')
    h=np.ones((1,64)); h[:,20:40]=2; bed=h*0
    for shift in (3,25,43):
        value=np.roll(h,shift,1)
        yield f'shift{shift}',value,bed,bed,wet_pairs(value,bed,True),1.,True,False
        yield f'transpose{shift}',value.T,bed.T,bed.T,wet_pairs(value.T,bed.T,True),1.,True,False
    h=np.ones((1,64)); eta=h*0
    h[:,20:24]=[3.,2.5,2.,1.]; eta[:,20:24]=[2.,1.5,1.5,0.]
    bed=eta-h
    for shift in (0,43):
        value,z=np.roll(h,shift,1),np.roll(bed,shift,1)
        pairs=wet_pairs(value,z,True)
        yield f'plateau{shift}',value,z,value*0,pairs,1.,True,False
        yield f'plateau_transpose{shift}',value.T,z.T,value.T*0,[pairs[1].T,pairs[0].T],1.,True,False
    for trough in (2.**-149,2.**-130,2.**-126):
        for peak,forcing in ((2.,0.),(3*trough,0.),(3*trough,1.)):
            h=np.full((1,64),trough);h[:,20:40]=peak;bed=np.zeros_like(h)
            pairs=[np.ones_like(h,dtype=bool),np.zeros_like(h,dtype=bool)]
            yield f'represented_{trough}_{peak}_{forcing}',h,bed,h*0+forcing,pairs,1.,True,False
            yield f'represented_transpose_{trough}_{peak}_{forcing}',h.T,bed.T,h.T*0+forcing,[pairs[1].T,pairs[0].T],1.,True,False


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--observations',type=Path)
    parser.add_argument('--recorded-stage-trace',type=Path)
    parser.add_argument('--recorded-interval',type=int)
    parser.add_argument('--recorded-trial',type=int)
    args=parser.parse_args(); manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists(): raise FileExistsError(args.output)
    cases=[]; hashes={}
    for name,h,bed,ht,pairs,dx,periodic,do_step in synthetic_cases():
        h,bed,ht=(np.asarray(v,dtype=np.float32).astype(float) for v in (h,bed,ht))
        state=np.stack((h,h*0,h*0,np.where(h>0,.125,0)),axis=-1)
        rate=np.stack((ht,ht*0,ht*0,ht*0),axis=-1)
        cases.append((name,state,bed,rate,pairs,dx,periodic,do_step))
    if args.snapshot:
        meta,arrays,hashes=read_snapshot(args.snapshot)
        flow,detail=arrays['flow'].astype(float),arrays['state'].astype(float)
        h=flow[...,0]+detail[...,0]
        state=np.concatenate((h[...,None],h[...,None]*flow[...,1:3]+detail[...,1:3]),axis=-1)
        fields,_=fixture(state,arrays['mean_geometry'][...,0],meta['cell_m'],False,'front')
        pairs=[(fields[5]&1)!=0,(fields[5]&2)!=0]
        cases.append(('captured',fields[1],fields[0][...,1],fields[2],pairs,meta['cell_m'],False,True))
    if args.observations:
        data=args.observations.read_bytes(); first,_=observations(json.loads(data))
        hashes['native_observations']=hashlib.sha256(data).hexdigest()
        fields,_=fixture(first['state'][...,:3],first['bed'],first['cell_meters'],False,'front')
        pairs=[(fields[5]&1)!=0,(fields[5]&2)!=0]
        cases.append(('native_source_closed_step',fields[1],fields[0][...,1],fields[2],pairs,first['cell_meters'],False,True))
    if args.recorded_stage_trace:
        data=args.recorded_stage_trace.read_bytes(); metadata=json.loads(data)
        if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
            raise ValueError('Unqualified recorded trace')
        binary=Path(metadata['binary']).read_bytes()
        matches=[r for r in read_records(metadata,binary)
                 if r[0]['interval']==args.recorded_interval and r[0]['trial']==args.recorded_trial]
        if len(matches)!=1:raise ValueError('Exactly one recorded trial required')
        gpu=matches[0][1][0]
        pairs=[(gpu['pairs']&1)!=0,(gpu['pairs']&2)!=0]
        cases.append(('recorded_front_switch',gpu['state'],gpu['geometry'][...,1],gpu['rate'],pairs,.5,False,False))
        hashes.update(recorded_trace=hashlib.sha256(data).hexdigest(),recorded_binary=hashlib.sha256(binary).hexdigest())
    records=[]
    with args.output.open('xb') as output:
        output.write(struct.pack('<III',0x52464252,1,len(cases)))
        for name,state,bed,rate,pairs,dx,periodic,do_step in cases:
            state,bed,rate=(np.asarray(v,dtype=np.float32).astype(float) for v in (state,bed,rate))
            fraction,stats=dispersion_fraction(state[...,0],bed,rate[...,0],pairs,dx)
            dt=float(np.float32(.001)) if do_step else 0.
            expected=None
            if do_step:
                _,_,expected,_=step_reference(state,bed,dx,periodic,True,dt,breaking_model='hybrid_front')
            ny,nx=bed.shape
            output.write(struct.pack('<IIIffIII',nx,ny,int(periodic),dx,dt,stats['detected_fronts'],
                stats['boundary_truncated_runs'],stats['subcell_fronts']))
            packed=pairs[0].astype(np.uint32)+2*pairs[1].astype(np.uint32)
            arrays=[np.stack((state[...,0],bed),axis=-1),rate,packed,fraction,state]
            if expected is not None: arrays.append(expected)
            for i,value in enumerate(arrays):
                data=np.asarray(value,dtype='<u4' if i==2 else '<f4')
                if not np.isfinite(data).all():raise ValueError('Nonfinite represented fixture')
                output.write(data.tobytes(order='C'))
            records.append(dict(name=name,shape=[ny,nx],dt=dt,**stats))
    record=dict(schema='raftsim.breaking_front_fixtures.v1',scope=__doc__,scene_accepted=False,
        fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),source_hashes=hashes,cases=records,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_breaking_front_fixtures.py','breaking_front_reference.py',
                         'export_total_depth_step_fixtures.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','total_depth_nonlinear_pressure.py')})
    with manifest.open('x') as output:json.dump(record,output,indent=2,allow_nan=False)
    print(json.dumps(record,indent=2,allow_nan=False))


if __name__=='__main__':main()
