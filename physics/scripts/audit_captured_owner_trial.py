"""Inspect actual retained-state GPU intermediates; never repairs or promotes them."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from breaking_front_reference import dispersion_fraction, surface_jumps
from total_depth_nonlinear_pressure import nonlinear_pressure_force


def fields(metadata,binary,*,schema='raftsim.captured_owner_trial_diagnostic.v1'):
    if metadata.get('schema')!=schema or not metadata.get('capture_completed'):
        raise ValueError('Incomplete captured trial')
    result={};offset=0
    for field in metadata['fields']:
        name=field['name'];size=field['bytes'];components=field['components']
        if name in result or field['byte_offset']!=offset or size<=0 or size%4 or components not in (1,2,4):
            raise ValueError('Invalid captured field layout')
        dtype={'uint32':'<u4','float32':'<f4'}.get(field['dtype'])
        if dtype is None or offset+size>len(binary):raise ValueError('Invalid field storage')
        result[name]=np.frombuffer(binary,dtype,count=size//4,offset=offset).reshape(-1,components)
        offset+=size
    if offset!=len(binary):raise ValueError('Trailing captured bytes')
    return result


def state_statistics(value):
    state=value.reshape(128,128,4)
    invalid=(~np.isfinite(state).all(-1)) | (state[...,0]<0) | (state[...,3]<0) | ((state[...,0]==0)&np.any(state[...,1:3]!=0,axis=-1))
    # Decode to double before dividing so the host check does not flush valid
    # FP32 subnormal inputs. Round the velocity back to its actual FP32 storage
    # range: finite conserved values can still imply overflowing velocity.
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        velocity=(state[...,1:3].astype(np.float64)/state[...,0,None].astype(np.float64)).astype(np.float32)
    invalid |= (state[...,0]>0)&~np.isfinite(velocity).all(-1)
    positions=np.argwhere(invalid)
    def safe(v):return float(v) if np.isfinite(v) else None
    return dict(invalid_cells=len(positions),examples=[dict(y=int(y),x=int(x),state=list(map(safe,state[y,x]))) for y,x in positions[:16]])


def bit_exact_state(a,b):
    return a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes()


def breaking_comparison(gpu,stage,shape,dx):
    """Classify the actual captured graph, not a separately reconstructed one."""
    suffix=str(stage)
    names=[name+suffix for name in ('geometry','pairs','surface_jumps','breaking_diagnostics')]
    if not all(name in gpu for name in names):
        return dict(available=False)
    geometry=gpu[names[0]].reshape(*shape,2).astype(float)
    packed=gpu[names[1]].reshape(shape)
    flags=gpu[names[3]].reshape(-1)
    result=dict(available=True,gpu_diagnostics=flags.tolist(),comparison_passed=False)
    if flags[0]!=0:
        result['error']='GPU classifier rejected this stage; no valid fraction comparison'
        return result
    if np.any(packed&~np.uint32(3)):
        raise ValueError('Unknown captured graph bits')
    pairs=[(packed&1)!=0,(packed&2)!=0]
    rate=gpu['rate'+suffix].reshape(*shape,4).astype(float)
    expected,stats=dispersion_fraction(geometry[...,0],geometry[...,1],rate[...,0],pairs,dx)
    actual=gpu['fraction'+suffix].reshape(shape).astype(float)
    delta=abs(actual-expected)
    counts=[stats[name] for name in ('detected_fronts','boundary_truncated_runs','subcell_fronts')]
    valid=np.isfinite(delta).all() and np.all((actual>=0)&(actual<=1))
    maximum=float(delta.max()) if valid else None
    # Read back the computed jumps as an independent diagnostic, without
    # substituting those GPU values into the CPU classifier.
    expected_jumps=np.stack([surface_jumps(geometry[...,0],geometry[...,1],axis)
                            for axis in (1,0)],axis=-1)
    actual_jumps=gpu[names[2]].reshape(*shape,2).astype(float)
    jump_delta=abs(actual_jumps-expected_jumps)
    result.update(cpu_counts=counts,cpu_statistics=stats,maximum_fraction_error=maximum,
        maximum_surface_jump_error=float(jump_delta.max()) if np.isfinite(jump_delta).all() else None,
        comparison_passed=bool(valid and maximum<2e-5 and flags[1:].tolist()==counts))
    return result


def pressure_comparison(gpu,stage,shape,dx):
    """Independent pressure solve on all actual represented stage inputs."""
    suffix=str(stage)
    names=('pressure_diagnostics','solver_diagnostics','pressure_rhs','pressure_correction',
           'pressure','pressure_residual','bed_slope','boundary_trace','geometry','pairs','rate','fraction','force')
    if not all(name+suffix in gpu for name in names):return dict(available=False)
    flags=gpu['pressure_diagnostics'+suffix].reshape(-1)
    solver=gpu['solver_diagnostics'+suffix].reshape(-1)
    result=dict(available=True,gpu_diagnostics=flags.tolist(),solver_diagnostics=solver.tolist(),comparison_passed=False)
    if np.any(flags[:2]) or np.any(solver[:2]):
        result['error']='GPU pressure rejected this stage; no valid operator comparison'
        return result
    geometry=gpu['geometry'+suffix].reshape(*shape,2).astype(float)
    h=geometry[...,0];state=gpu['input_state' if stage==0 else 'euler_state'].reshape(*shape,4).astype(float)
    if not np.array_equal(h,state[...,0]):raise ValueError('Captured pressure geometry/state mismatch')
    velocity=np.divide(state[...,1:3],h[...,None],out=np.zeros((*shape,2)),where=h[...,None]>0)
    packed=gpu['pairs'+suffix].reshape(shape);pairs=[(packed&1)!=0,(packed&2)!=0]
    if np.any(packed&~np.uint32(3)):raise ValueError('Unknown captured graph bits')
    rate=gpu['rate'+suffix].reshape(*shape,4).astype(float);poles=[]
    force,stats=nonlinear_pressure_force(h,geometry[...,1],velocity,velocity*0,pairs,dx,
        interpolation='depth_weighted',formulation='kinematic',mass_rate=rate[...,0],momentum_rate=rate[...,1:3],
        bed_slope=gpu['bed_slope'+suffix].reshape(*shape,2).astype(float),
        dispersion_fraction=gpu['fraction'+suffix].reshape(shape).astype(float),
        boundary_velocity=gpu['boundary_trace'+suffix].reshape(-1,2).astype(float),on_pressure=poles.extend)
    expected=dict(pressure_rhs=np.concatenate([p['rhs'] for p in poles],-1),
        pressure_correction=np.concatenate([p['correction'] for p in poles],-1),
        pressure=np.stack([v for p in poles for v in (p['pressure'],p['bottom_pressure'])],-1),force=force)
    comparisons={}
    for name,reference in expected.items():
        actual=gpu[name+suffix].reshape(reference.shape).astype(float);delta=actual-reference
        finite=bool(np.isfinite(delta).all());norm=np.linalg.norm(reference.ravel())
        relative=float(np.linalg.norm(delta.ravel())/(norm if norm>0 else 1)) if finite else None
        maximum=float(abs(delta).max()) if finite else None
        comparisons[name]=dict(maximum_error=maximum,relative_error=relative,
            passed=bool(finite and relative<2e-5 and (name!='force' or maximum<1e-3)))
    residual=gpu['pressure_residual'+suffix].reshape(*shape,4).astype(float)
    rhs=gpu['pressure_rhs'+suffix].reshape(*shape,4).astype(float)
    norm=np.linalg.norm(rhs.ravel());relative=float(np.linalg.norm(residual.ravel())/(norm if norm>0 else 1))
    weighted_residual=np.sqrt(h)[...,None]*residual;weighted_rhs=np.sqrt(h)[...,None]*rhs
    physical_scale=max(float(abs(weighted_residual).max()),float(abs(weighted_rhs).max())) or 1.
    physical_norm=np.linalg.norm((weighted_rhs/physical_scale).ravel())
    physical_relative=float(np.linalg.norm((weighted_residual/physical_scale).ravel())/(physical_norm if physical_norm>0 else 1))
    thin=np.argwhere((h>0)&(h<1e-30));actual_force=gpu['force'+suffix].reshape(*shape,2).astype(float)
    result.update(reference_solver=stats,fields=comparisons,true_residual_relative=relative if np.isfinite(relative) else None,
        physical_true_residual_relative=physical_relative if np.isfinite(physical_relative) else None,
        thin_forces=[dict(y=int(y),x=int(x),gpu=actual_force[y,x].tolist(),cpu=force[y,x].tolist()) for y,x in thin[:16]],
        comparison_passed=bool(all(v['passed'] for v in comparisons.values()) and np.isfinite(relative) and relative<2e-5
            and np.isfinite(physical_relative) and physical_relative<2e-5
            and all(s['relative_residual']<2e-5 for s in stats)))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('capture',type=Path)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    metadata=json.loads(args.capture.read_text());binary=Path(metadata['binary']).read_bytes();gpu=fields(metadata,binary)
    manifest=json.loads(Path(metadata['input']).with_suffix('.json').read_text())
    input_bytes=Path(metadata['input']).read_bytes();source_bytes=Path(manifest['source']).read_bytes()
    if hashlib.sha256(input_bytes).hexdigest()!=manifest['input_sha256'] or hashlib.sha256(source_bytes).hexdigest()!=manifest['source_sha256']:
        raise ValueError('Captured source provenance mismatch')
    source=json.loads(source_bytes);i=manifest['interval']
    a,b=temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',first=source['observations'][i],second=source['observations'][i+1]))
    _,boundary=temporal.boundary_provider(a,b);clock=np.array(source['progress'],dtype=float)
    time=clock[0]+clock[1];dt=float(gpu['info'][0,1]);rows=[]
    for k,name in enumerate(('input_state','euler_state')):
        state=gpu[name].reshape(128,128,4).astype(float);es,eb,trace=boundary(time-a['native_seconds']+(dt if k else 0),None)
        stats=state_statistics(state);row=dict(stage=k,**stats)
        fraction=gpu['fraction'+str(k)][:,0]
        row['invalid_breaking_fraction_cells']=int(np.count_nonzero(~np.isfinite(fraction)|(fraction<0)|(fraction>1)))
        row['breaking_comparison']=breaking_comparison(gpu,k,(128,128),.5)
        row['pressure_comparison']=pressure_comparison(gpu,k,(128,128),.5)
        velocity_name='velocity'+str(k)
        if velocity_name in gpu:
            actual_velocity=gpu[velocity_name].reshape(128,128,2).astype(float)
            expected_velocity=np.divide(state[...,1:3],state[...,0,None],out=np.zeros_like(actual_velocity),where=state[...,0,None]>0)
            difference=abs(actual_velocity-expected_velocity)
            row['maximum_velocity_error']=float(difference.max()) if np.isfinite(difference).all() else None
            thin=np.argwhere((state[...,0]>0)&(state[...,0]<1e-30))
            row['thin_velocities']=[dict(y=int(y),x=int(x),gpu=actual_velocity[y,x].tolist(),cpu=expected_velocity[y,x].tolist()) for y,x in thin[:16]]
        flags=gpu['transport_diagnostics'+str(k)][0]
        row.update(gpu_transport_flags=flags.tolist(),gpu_transport_valid=bool(not np.any(flags)))
        if np.any(flags):
            # An invalid GPU input suppresses reconstruction in the transport
            # shader. Its output is diagnostic storage, not a valid operator
            # evaluation against which to calculate an accuracy error.
            thin=np.argwhere((state[...,0]>0)&(state[...,0]<1e-30))
            row.update(gpu_operator_error='GPU transport rejected this stage; no accuracy comparison',
                thin_cells=[dict(y=int(y),x=int(x),state=state[y,x].tolist()) for y,x in thin[:16]])
            rows.append(row);continue
        try:
            hydro,_=temporal.bank.rate(state[...,:3],a['bed'],.5,second_order=True,exterior=(es,eb))
            actual=gpu['rate'+str(k)].reshape(128,128,4)[...,:3].astype(float)
            error=abs(hydro-actual);worst=np.unravel_index(error.argmax(),error.shape)
            thin=np.argwhere((state[...,0]>0)&(state[...,0]<1e-30))
            row.update(maximum_hydro_error=float(error.max()),worst_yxc=list(map(int,worst)),
                thin_cells=[dict(y=int(y),x=int(x),state=state[y,x].tolist(),gpu_rate=actual[y,x].tolist(),cpu_rate=hydro[y,x].tolist()) for y,x in thin[:16]])
        except (ValueError,FloatingPointError) as error:row['cpu_operator_error']=str(error)
        rows.append(row)
    accepted=bool(gpu['diagnostics'][0,3])
    report=dict(schema='raftsim.captured_owner_trial_analysis.v1',scope=__doc__,transaction_accepted=accepted,
        info=gpu['info'].tolist(),progress=gpu['progress'].tolist(),diagnostics=gpu['diagnostics'].tolist(),
        transport_diagnostics=[gpu['transport_diagnostics'+str(k)].tolist() for k in range(2)],
        cfl=[gpu['cfl'+str(k)].tolist() for k in range(2)],stages=rows,
        output_state_exact_to_input=bit_exact_state(gpu['input_state'],gpu['output_state']),
        candidate=state_statistics(gpu['candidate_state']),source_sha256=manifest['source_sha256'],
        captured_binary_sha256=hashlib.sha256(binary).hexdigest())
    report['implementation_hashes'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_captured_owner_trial.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py', 'breaking_front_reference.py', 'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py')}
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':main()
