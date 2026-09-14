"""Observe continuous polynomial response on two actual nearby stage states.

Convex interpolants are diagnostic probes only; no solver state is replaced and
no gate is qualified by interpolation. Report raw/scaled face geometry alongside
the actual hydro rate to separate a sharp switch from a steep continuous response.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records
from audit_recorded_evolution_steps import shoreline_model
from continuous_shoreline_reconstruction import factors


def observe(state,bed,dx,exterior,point,*,limiter='continuous'):
    captures=[];original=temporal.bank.hydrostatic_faces
    def capture(*args,**kwargs):
        result=original(*args,**kwargs);axis=args[4]
        hm,hp,_,_,reduced_a,reduced_b=result
        positive=np.take(reduced_a,range(1,reduced_a.shape[axis]),axis=axis)
        negative=np.take(reduced_b,range(reduced_b.shape[axis]-1),axis=axis)
        factor=kwargs.get('slope_factors')
        phase='scaled' if factor is not None else 'raw'
        if factor is None:
            factor=factors(hm,hp,reduced_a,reduced_b,axis) if limiter=='continuous' else np.ones_like(hm)
        points=[]
        for offset in range(-2,3):
            p=list(point);p[axis]+=offset;p=tuple(p)
            if not all(0<=v<n for v,n in zip(p,bed.shape)):continue
            points.append(dict(yx=list(p),h=float(state[p][0]),hu=float(state[p][1]),hv=float(state[p][2]),
                bed=float(bed[p]),dh=float(args[2][p]),deta=float(args[3][p]),
                owning_minus=float(hm[p]),owning_plus=float(hp[p]),
                reduced_minus=float(negative[p]),reduced_plus=float(positive[p]),factor=float(factor[p])))
        captures.append(dict(axis=axis,phase=phase,points=points));return result
    try:
        temporal.bank.hydrostatic_faces=capture
        rate,cfl=temporal.bank.rate(state,bed,dx,second_order=True,exterior=exterior,shoreline_limiter=limiter)
    finally:temporal.bank.hydrostatic_faces=original
    return rate,dict(point_rate=rate[point].tolist(),cfl_bound_s=float(cfl),polynomials=captures)


def depth_response(state,bed,dx,exterior,point,probe,step,*,limiter='continuous'):
    """Vary only one conserved depth; keep bed and every momentum unchanged.

    Central differences at three scales check local self-monotonicity of the
    owning-cell polynomial. These are diagnostic states, never evolved history.
    Negative owning-face derivatives contradict self-monotonicity, but positive
    samples do not prove it globally or establish a stable time integrator.
    """
    if (len(probe)!=2 or not all(0<=v<n for v,n in zip(probe,bed.shape))
            or not np.isfinite(step) or step<=0 or state[probe][0]<=step):
        raise ValueError('Depth probe requires a positive wet stencil and finite step')
    samples={}
    for multiple in (-1.,-.5,-.25,0.,.25,.5,1.):
        perturbed=state.copy();perturbed[probe][0]+=multiple*step
        rate,row=observe(perturbed,bed,dx,exterior,probe,limiter=limiter)
        row['depth_increment']=float(perturbed[probe][0]-state[probe][0])
        row['target_rate']=rate[point].tolist();samples[multiple]=row
    derivatives=[]
    for multiple in (1.,.5,.25):
        minus,plus=samples[-multiple],samples[multiple]
        denominator=plus['depth_increment']-minus['depth_increment']
        if denominator<=0:raise ValueError('Depth step is not representable')
        faces=[]
        for low,high in zip(minus['polynomials'],plus['polynomials']):
            if (low['axis'],low['phase'])!=(high['axis'],high['phase']):
                raise ValueError('Mismatched polynomial captures')
            a=next(p for p in low['points'] if p['yx']==list(probe))
            b=next(p for p in high['points'] if p['yx']==list(probe))
            faces.append(dict(axis=low['axis'],phase=low['phase'],
                **{key:(b[key]-a[key])/denominator for key in
                   ('owning_minus','owning_plus','reduced_minus','reduced_plus','factor')}))
        derivatives.append(dict(depth_step=multiple*step,polynomials=faces,
            target_rate=((np.array(plus['target_rate'])-minus['target_rate'])/denominator).tolist()))
    return dict(probe_yx=list(probe),target_yx=list(point),base_depth=float(state[probe][0]),
        scope=depth_response.__doc__,samples=list(samples.values()),derivatives=derivatives)


def local_hydro_jacobian(state,bed,dx,exterior,center,radius,relative_step,dt,*,limiter='continuous'):
    """Hydro-only local linearization with the exterior of the patch frozen.

    A principal block is not the complete coupled hydro/pressure operator. Its
    eigenvalues diagnose local stiffness, not a proof of global instability or
    permission to replace the recorded/default timesteps. Dry cells are fixed;
    no positive-depth floor is used for any selected wet-cell perturbation.
    """
    if (type(radius) is not int or radius<0 or len(center)!=2
            or not all(0<=v<n for v,n in zip(center,bed.shape))
            or not np.isfinite(relative_step) or not 0<relative_step<1
            or not np.isfinite(dt) or dt<=0):
        raise ValueError('Invalid local Jacobian probe')
    indices=[(y,x,c) for y in range(max(0,center[0]-radius),min(bed.shape[0],center[0]+radius+1))
        for x in range(max(0,center[1]-radius),min(bed.shape[1],center[1]+radius+1))
        if state[y,x,0]>0 for c in range(3)]
    if not indices:raise ValueError('Local probe contains no wet cells')
    select=tuple(np.array(indices).T);columns=[];increments=[]
    for index in indices:
        h=state[index[:2]][0]
        step=relative_step*(h if index[2]==0 else max(h,abs(state[index])))
        plus,minus=state.copy(),state.copy();plus[index]+=step;minus[index]-=step
        denominator=plus[index]-minus[index]
        if denominator<=0:raise ValueError('Jacobian step is not representable')
        upper=temporal.bank.rate(plus,bed,dx,second_order=True,exterior=exterior,shoreline_limiter=limiter)[0]
        lower=temporal.bank.rate(minus,bed,dx,second_order=True,exterior=exterior,shoreline_limiter=limiter)[0]
        columns.append((upper[select]-lower[select])/denominator);increments.append(float(denominator/2))
    matrix=np.stack(columns,axis=1);values=np.linalg.eigvals(matrix)
    values=values[np.argsort(values.real)]
    # Frozen-Jacobian SSP-RK2 stability polynomial; actual nonlinear stages
    # have different Jacobians and also include pressure.
    amplification=[]
    for scale in (1.,.5,.25,.125):
        z=values*dt*scale;gain=abs(1+z+.5*z*z)
        decaying=values.real<0
        amplification.append(dict(dt=dt*scale,
            maximum_decaying_mode_gain=float(np.max(gain[decaying])) if decaying.any() else None,
            unstable_decaying_modes=int(np.sum(decaying & (gain>1)))))
    return dict(scope=local_hydro_jacobian.__doc__,center_yx=list(center),radius=radius,
        relative_step=relative_step,indices_yxc=[list(p) for p in indices],increments=increments,
        matrix=matrix.tolist(),eigenvalues_real_imag=np.stack((values.real,values.imag),axis=1).tolist(),
        rk2_frozen_linearization=amplification)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path);parser.add_argument('states',type=Path)
    parser.add_argument('--interval',type=int,required=True);parser.add_argument('--trial',type=int,required=True)
    parser.add_argument('--stage',type=int,choices=(0,1),required=True);parser.add_argument('--yx',type=int,nargs=2,required=True)
    parser.add_argument('--depth-probe-yx',type=int,nargs=2)
    parser.add_argument('--depth-probe-step',type=float)
    parser.add_argument('--jacobian-radius',type=int)
    parser.add_argument('--jacobian-relative-step',type=float,default=1e-5)
    parser.add_argument('--evaluation-model',choices=('continuous','unscaled'),default='continuous',
        help='Evaluate nearby inputs with this CPU model; an alternate model is not GPU parity')
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if (args.depth_probe_yx is None)!=(args.depth_probe_step is None):
        parser.error('--depth-probe-yx and --depth-probe-step must be supplied together')
    if args.report.exists():raise FileExistsError(args.report)
    data=args.trace.read_bytes();meta=json.loads(data);source_bytes=Path(meta['source']).read_bytes();source=json.loads(source_bytes)
    if not meta.get('completed') or not meta.get('final_state_exact_to_live') or shoreline_model(meta,source)!='continuous':
        raise ValueError('Qualified continuous stage capture required')
    binary=Path(meta['binary']).read_bytes()
    trial,stages,*_=next(r for r in read_records(meta,binary) if r[0]['interval']==args.interval and r[0]['trial']==args.trial)
    a,b=temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][args.interval],second=source['observations'][args.interval+1]))
    _,boundary=temporal.boundary_provider(a,b)
    es,eb,_=boundary(trial['begin']-a['native_seconds']+(trial['attempted_dt'] if args.stage else 0),None)
    with np.load(args.states,allow_pickle=False) as archive:
        if archive['source_sha256'].item()!=hashlib.sha256(source_bytes).hexdigest():raise ValueError('Unrelated CPU states')
        cpu=archive[str(args.trial)+('_stage' if args.stage else '_input')].copy()
    gpu=stages[args.stage]['state'][...,:3].astype(float);point=tuple(args.yx)
    if not all(0<=v<n for v,n in zip(point,a['bed'].shape)):raise ValueError('Point outside captured grid')
    cases=[];rates=[]
    for alpha in (0.,.25,.5,.75,1.):
        state=(1-alpha)*cpu+alpha*gpu
        rate,row=observe(state,a['bed'],a['cell_meters'],(es,eb),point,limiter=args.evaluation_model)
        row['gpu_interpolation_fraction']=alpha;row['point_state']=state[point].tolist();cases.append(row);rates.append(rate)
    difference=abs(rates[0]-rates[-1]);at=np.unravel_index(difference.argmax(),difference.shape)
    report=dict(schema='raftsim.continuous_polynomial_response.v1',scope=__doc__,trial=trial,stage=args.stage,
        captured_model='continuous',evaluation_model=args.evaluation_model,
        maximum_input_error=float(abs(cpu-gpu).max()),maximum_rate_error=float(difference.max()),worst_yxc=list(map(int,at)),
        same_input_native_rate_error=float(abs(rates[-1]-stages[args.stage]['rate'][...,:3]).max()) if args.evaluation_model=='continuous' else None,cases=cases,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),trace_sha256=hashlib.sha256(data).hexdigest(),
        binary_sha256=hashlib.sha256(binary).hexdigest(),states_sha256=hashlib.sha256(args.states.read_bytes()).hexdigest())
    if args.depth_probe_yx is not None:
        report['single_depth_response']=depth_response(cpu,a['bed'],a['cell_meters'],(es,eb),point,
            tuple(args.depth_probe_yx),args.depth_probe_step,limiter=args.evaluation_model)
    if args.jacobian_radius is not None:
        report['local_hydro_jacobian']=local_hydro_jacobian(cpu,a['bed'],a['cell_meters'],(es,eb),
            tuple(args.depth_probe_yx) if args.depth_probe_yx is not None else point,
            args.jacobian_radius,args.jacobian_relative_step,trial['attempted_dt'],limiter=args.evaluation_model)
    report['implementation_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_continuous_polynomial_response.py','audit_recorded_evolution_steps.py','audit_recorded_stages.py',
            'audit_live_temporal_evolution.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','continuous_shoreline_reconstruction.py')}
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','implementation_hashes','single_depth_response','local_hydro_jacobian')},indent=2))
    if 'single_depth_response' in report:print(json.dumps(report['single_depth_response']['derivatives'],indent=2))
    if 'local_hydro_jacobian' in report:
        result=report['local_hydro_jacobian']
        print(json.dumps(dict(most_negative_eigenvalue=result['eigenvalues_real_imag'][0],
            rk2_frozen_linearization=result['rk2_frozen_linearization']),indent=2))


if __name__=='__main__':main()
