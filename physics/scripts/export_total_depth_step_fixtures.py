"""Independent CPU double SSP-RK2 single-trial references, no scene acceptance.

Inputs are float32 represented. The Euler intermediate is explicitly rounded
to float32 before reevaluating the independent CPU rate, matching GPU storage,
not copying GPU computations. Nonbreaking rational pressure is recomputed at
both stages. No rejected state repair or clock advance is permitted.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from export_total_depth_transport_fixtures import synthetic_cases
from audit_detail_wave_regime import read_snapshot
from total_depth_bank_replay import rate


def step_reference(state,bed,dx,periodic,second_order,dt,*,breaking_model='none',shoreline_limiter='binary'):
    state=np.asarray(state,dtype=np.float32).astype(float)
    bed=np.asarray(bed,dtype=np.float32).astype(float)
    kwargs=dict(second_order=second_order,periodic=periodic,dispersive=True,
        pressure_model='rational_sgn',pressure_interpolation='depth_weighted',
        pressure_formulation='kinematic',pressure_bed_slope='geometry',breaking_model=breaking_model,
        shoreline_limiter=shoreline_limiter)
    has_foam=state.shape[-1]==4
    def evaluate(value):
        return rate(value[...,:3],bed,dx,foam=value[...,3] if has_foam else None,**kwargs)
    first,bound1=evaluate(state)
    dt=float(np.float32(dt))
    if dt>bound1: raise ValueError('Fixture initial CFL exceeded')
    stage=(state+dt*first).astype(np.float32).astype(float)
    second,bound2=evaluate(stage)
    if dt>bound2: raise ValueError('Fixture stage CFL exceeded')
    result=.5*state+.5*(stage+dt*second)
    if (not np.isfinite(result).all() or np.any(result[...,0]<0)
            or (has_foam and np.any(result[...,3]<0))): raise ValueError('Invalid fixture candidate')
    return state,bed,result,(bound1,bound2)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--snapshot',type=Path)
    model=parser.add_mutually_exclusive_group()
    model.add_argument('--continuous-shoreline',action='store_true')
    model.add_argument('--unscaled-shoreline',action='store_true')
    args=parser.parse_args();manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists(): raise FileExistsError(args.output)
    cases=list(synthetic_cases());hashes={}
    if args.snapshot:
        meta,arrays,hashes=read_snapshot(args.snapshot)
        flow,detail=arrays['flow'].astype(float),arrays['state'].astype(float);h=flow[...,0]+detail[...,0]
        state=np.concatenate((h[...,None],h[...,None]*flow[...,1:3]+detail[...,1:3]),axis=-1)
        cases.append(('captured',state,arrays['mean_geometry'][...,0],meta['cell_m'],False,True))
    moving=next(case for case in synthetic_cases() if case[0]=='moving')
    cases.append(('zero_foam',*moving[1:]))
    # Normal (not subnormal) represented states must survive zero-rate RK2.
    # These native cases preserve state exactly; they do not reproduce the
    # separate captured nonzero-rate Euler underflow.
    for multiple in (1,2):
        h=np.full((2,4),float(np.finfo(np.float32).tiny)*multiple)
        cases.append((f'minimum_normal_{multiple}',np.stack((h,2*h,h*0),axis=-1),h*0,1.,True,True))
    records=[];version=3 if args.unscaled_shoreline else 2 if args.continuous_shoreline else 1
    limiter='unscaled' if args.unscaled_shoreline else 'continuous' if args.continuous_shoreline else 'binary'
    with args.output.open('xb') as out:
        out.write(struct.pack('<III',0x52535354,version,len(cases)))
        for name,original,bed,dx,periodic,second_order in cases:
            y,x=np.indices(bed.shape)
            foam=.125*(1.+.2*np.sin(.4*x)*np.cos(.3*y))
            if name=='zero_foam' or name.startswith('minimum_normal_'): foam.fill(0)
            original=np.concatenate((original,foam[...,None]),axis=-1)
            dt=float(np.float32(.001));state,bed,result,bounds=step_reference(original,bed,dx,periodic,second_order,dt,
                shoreline_limiter=limiter)
            ny,nx=bed.shape;out.write(struct.pack('<IIIIffff',nx,ny,int(periodic),int(second_order),dx,dt,*bounds))
            for data in (bed,state,result):
                out.write(np.asarray(data,dtype='<f4').tobytes(order='C'))
            records.append(dict(name=name,shape=[ny,nx],dt=dt,bounds=[float(b) if np.isfinite(b) else None for b in bounds],
                maximum_state_change=float(abs(result-state).max())))
    record=dict(schema=f'raftsim.total_depth_step_fixtures.v{version}',scope=__doc__,scene_accepted=False,
        shoreline_limiter=limiter,
        source_hashes=hashes,fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),cases=records,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
            ('export_total_depth_step_fixtures.py','export_total_depth_transport_fixtures.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','total_depth_nonlinear_pressure.py',
             'continuous_shoreline_reconstruction.py','pressure_cg_range_reference.py','breaking_front_reference.py')})
    with manifest.open('x') as out:json.dump(record,out,indent=2,allow_nan=False)
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
