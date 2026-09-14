"""Represented-state CPU fixtures for GPU conservative transport + pressure.

The CPU double FV reference consumes float32-representable state/bed. Its
rounded hydro rate is the input to the independent CPU pressure reference.
Native tests must instead use the GPU transport's own rate/graph/slope as the
GPU pressure input. Precision verification only, not scene acceptance.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from export_nonlinear_pressure_fixtures import fixture
from audit_detail_wave_regime import read_snapshot


def synthetic_cases():
    for kind in ('dry','lake_bank','dam','first_order_dam','thin_datum','moving','periodic','column'):
        y,x=np.indices((17,1) if kind=='column' else (13,17))
        bed=.125*(x+y);h=np.maximum(0,1.-bed);u=np.zeros_like(h);v=np.zeros_like(h)
        if kind=='dry': h[:]=0
        elif kind in ('dam','first_order_dam'): bed[:]=0;h=np.where(x<8,1.,0.)
        elif kind=='thin_datum': bed=1000.+.03125*x;h[:]=1e-20
        elif kind in ('moving','periodic','column'):
            bed=.08*np.sin(x*.2)*np.cos(y*.3);h=.9+.2*np.sin(x*.23)+.1*np.cos(y*.31)
            u=.4*np.sin(x*.31)+1.;v=.3*np.cos(y*.19)
        yield kind,np.stack((h,h*u,h*v),axis=-1),bed,.5,kind=='periodic',kind!='first_order_dam'


def resting_lake_cases():
    """Exact represented equilibria on rough beds, with/without emergent islands."""
    for periodic in (False, True):
        for emergent in (False, True):
            for datum in (0., 1024.):
                rng=np.random.default_rng(914)
                relief=rng.integers(0,6144 if emergent else 4096,(13,17))/1024.
                h=np.maximum(0,4.-relief);bed=datum+relief
                state=np.stack((h,np.zeros_like(h),np.zeros_like(h)),axis=-1)
                yield f'rough_lake_periodic{periodic}_islands{emergent}_datum{datum}',state,bed,.5,periodic,True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path)
    model=parser.add_mutually_exclusive_group()
    model.add_argument('--continuous-shoreline',action='store_true',help='Experimental continuous reconstruction fixture v2')
    model.add_argument('--unscaled-shoreline',action='store_true',help='Unscaled original MC diagnostic reconstruction fixture v3')
    parser.add_argument('--resting-lakes',action='store_true',help='Append exact rough-bed lakes, emerged banks, periodicity and shifted datum')
    parser.add_argument('--recorded-trace',type=Path,help='Append both stages of one actual captured trial as a closed 11x11 operator crop')
    parser.add_argument('--interval',type=int);parser.add_argument('--trial',type=int)
    parser.add_argument('--crop-center',type=int,nargs=2,metavar=('Y','X'))
    args=parser.parse_args();manifest_path=args.output.with_suffix('.json')
    if args.output.exists() or manifest_path.exists(): raise FileExistsError(args.output)
    cases=list(synthetic_cases());hashes={}
    if args.resting_lakes: cases.extend(resting_lake_cases())
    if args.recorded_trace:
        from audit_recorded_stages import read_records
        if args.interval is None or args.trial is None or args.crop_center is None:
            raise ValueError('Recorded crop requires exact interval/trial and center')
        data=args.recorded_trace.read_bytes();meta=json.loads(data);binary=Path(meta['binary']).read_bytes()
        if not meta.get('completed') or not meta.get('final_state_exact_to_live'):
            raise ValueError('Unqualified recorded trace')
        trial,stages,*_=next(r for r in read_records(meta,binary) if r[0]['interval']==args.interval and r[0]['trial']==args.trial)
        y,x=args.crop_center
        if not 5<=y<123 or not 5<=x<123:raise ValueError('Crop outside bounded captured grid')
        for index,stage in enumerate(stages):
            cases.append((f'recorded_stage{index}_closed_crop',stage['state'][y-5:y+6,x-5:x+6,:3],
                stage['geometry'][y-5:y+6,x-5:x+6,1],.5,False,True))
        hashes.update(trace_sha256=hashlib.sha256(data).hexdigest(),binary_sha256=hashlib.sha256(binary).hexdigest(),
            source_sha256=hashlib.sha256(Path(meta['source']).read_bytes()).hexdigest(),trial=trial,crop_center=[y,x],
            scope='Closed 11x11 operator crop from both actual stages; not the live boundary or full interval')
    if args.snapshot:
        meta,arrays,hashes=read_snapshot(args.snapshot)
        flow,detail=arrays['flow'].astype(float),arrays['state'].astype(float)
        h=flow[...,0]+detail[...,0]
        state=np.concatenate((h[...,None],h[...,None]*flow[...,1:3]+detail[...,1:3]),axis=-1)
        cases.append(('captured',state,arrays['mean_geometry'][...,0],meta['cell_m'],False,True))
    records=[];version=3 if args.unscaled_shoreline else 2 if args.continuous_shoreline else 1
    limiter='unscaled' if args.unscaled_shoreline else 'continuous' if args.continuous_shoreline else 'binary'
    with args.output.open('xb') as out:
        out.write(struct.pack('<III',0x52534656,version,len(cases)))
        for name,state,bed,dx,periodic,second_order in cases:
            fields,record=fixture(state,bed,dx,periodic,'nonbreaking',second_order=second_order,
                shoreline_limiter=limiter)
            if name.startswith('rough_lake_') and (np.any(fields[2]!=0) or np.any(fields[9]!=0)):
                raise ValueError('Independent rough-lake reference is not exactly at rest: '+name)
            ny,nx=record['shape'];cfl=record['cfl_bound_s']
            out.write(struct.pack('<IIIIff',nx,ny,int(periodic),int(second_order),dx,np.inf if cfl is None else cfl))
            selected=[fields[0][...,1],fields[1],fields[2],fields[5],fields[3],fields[9],fields[4]]
            for i,field in enumerate(selected):
                data=np.asarray(field,dtype='<u4' if i==3 else '<f4')
                if not np.all(np.isfinite(data)): raise ValueError('Nonfinite fixture array')
                out.write(data.tobytes(order='C'))
            records.append(dict(name=name,**record))
    manifest=dict(schema=f'raftsim.total_depth_transport_fixtures.v{version}',scope=__doc__,scene_accepted=False,
        shoreline_limiter=limiter,
        fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),source_hashes=hashes,cases=records,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_total_depth_transport_fixtures.py','export_nonlinear_pressure_fixtures.py',
                         'total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','total_depth_nonlinear_pressure.py',
                         'continuous_shoreline_reconstruction.py','pressure_cg_range_reference.py','audit_recorded_stages.py')})
    with manifest_path.open('x') as out: json.dump(manifest,out,indent=2,allow_nan=False)
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
