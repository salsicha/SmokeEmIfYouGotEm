"""Decode the bounded first GPU rejection, not a guessed later frame.

The latch is evidence of one actual rejected particle. It cannot by itself
certify the complete simulation, or which same-step rejected thread ran first.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_retirement import crossing
from south_fork_registered_mesh import RegisteredMeshSampler
from audit_liquid_native_handoff import read


def decode(record, generation):
    if (record.get('schema')!='raftsim.liquid_exit_first_rejection.v1' or
            record.get('simulation_generation')!=generation or record.get('retained_bytes')!=1280):
        raise ValueError('Current-generation fixed-size GPU latch required')
    values=record.get('words',[])
    if len(values)!=320 or any(type(v) is not int or v<0 or v>2**32-1 for v in values):
        raise ValueError('Exact uint32 trace words required')
    w=np.asarray(values,dtype='<u4')
    if not w[0]:
        if np.any(w):raise ValueError('Unclaimed latch contains stale payload')
        return dict(captured=False)
    step,version,owner,index,reason,nf,ni,position,start=map(int,w[:9])
    if (version!=1 or not 6<=nf<=128 or not 1<=ni<=128 or position>nf-3 or start>nf-3 or
            max(position,start)<min(position,start)+3 or index>=w[12] or index>=w[13] or
            not reason or reason&~63 or int(w[14]) not in (4,8) or int(w[15]) not in (0,1)):
        raise ValueError('Invalid first-rejection header or payload layout')
    payload=w[64:64+nf+ni]
    vec=lambda offset: w[offset:offset+3].copy().view('<f4').astype(float).tolist()
    point=lambda offset: payload[offset:offset+3].copy().view('<f4').astype(float).tolist()
    return dict(captured=True,native_step=step,owner=owner,particle_index=index,reason_bits=reason,
                float_components=nf,int_components=ni,position_offset=position,start_offset=start,
                residual_outer_boundary=bool(w[15]),
                face=int(w[9]),profile_row=int(w[10]),fraction=float(w[11:12].copy().view('<f4')[0]),
                source_capacity=int(w[12]),source_count=int(w[13]),status=int(w[14]),route=w[16:20].tolist(),
                gpu_local_start_cm=vec(20),gpu_local_end_cm=vec(23),gpu_lower_world_cm=vec(26),
                gpu_axis_x=vec(29),gpu_axis_y=vec(32),gpu_extent_cm=vec(35),gpu_profile=vec(38),
                start_cm=point(start),end_cm=point(position),payload_words=payload.tolist())


def controls(directory, history):
    """Read actual controls from compact summaries or a full native snapshot."""
    directory=Path(directory).resolve();result=[]
    for h in history:
        if h['full_audit_retained']:
            root=(directory/h['snapshot_directory']).resolve()
            if root.parent!=directory:raise ValueError('Full snapshot escapes capture')
            control=read(root/'handoff-receiving',h['receiving'],'control',(4,)).tolist()
        else:
            control=h['control']
        if len(control)!=4 or any(type(v) is not int or not 0<=v<=2**32-1 for v in control):
            raise ValueError('Exact four-word native control required')
        result.append(dict(native_step=h['native_step'],control=control))
    return result


def captured_frame_precision(record):
    """Separate arithmetic loss from quantizing the prepared frame itself.

    Float64 evaluates the exact float inputs retained by the GPU latch. The
    survey's original double frame is a different comparison, kept separately.
    This reports errors; it never approves a rejected exit or changes a gate.
    """
    lower=np.asarray(record['gpu_lower_world_cm'],dtype=float)
    axes=np.asarray([record['gpu_axis_x'],record['gpu_axis_y'],[0,0,1]],dtype=float)
    points=np.asarray([record['start_cm'],record['end_cm']],dtype=float)
    observed=np.asarray([record['gpu_local_start_cm'],record['gpu_local_end_cm']],dtype=float)
    if lower.shape!=(3,) or axes.shape!=(3,3) or points.shape!=(2,3) or observed.shape!=(2,3):
        raise ValueError('Complete captured physical frame and endpoints required')
    exact=(points-lower)@axes.T
    rounded=exact.astype('<f4').astype(float)
    return dict(exact_captured_frame_endpoints_cm=exact.tolist(),
        rounded_captured_frame_endpoints_cm=rounded.tolist(),
        gpu_arithmetic_error_cm=(observed-exact).tolist(),
        gpu_matches_single_rounding=bool(np.array_equal(observed,rounded)),
        acceptance=False)


def diagnose(directory):
    directory=Path(directory);repo=Path(__file__).resolve().parents[2]
    d=json.loads((directory/'stages.json').read_text())
    result=decode(d['first_exit_rejection'],d['simulation_generation'])
    history=controls(directory,d['native_particle_handoff_history'])
    failed=[h for h in history if h['control'][0]!=1]
    exit_failed=[h for h in failed if h['control'][1]&64]
    if (bool(exit_failed)!=result['captured'] or
            (exit_failed and exit_failed[0]['native_step']!=result['native_step'])):
        raise ValueError('Latch does not match the first failed exit transaction')
    result['first_commit_failure_step']=failed[0]['native_step'] if failed else None
    result['first_exit_failure_matches_commit']=bool(exit_failed) and failed[0]==exit_failed[0]
    result['acceptance']=False
    if not result['captured']:return result
    result['captured_frame_precision']=captured_frame_precision(result)
    owner=result['owner'];records=d['native_transfer_packet']
    if owner>=len(records):raise ValueError('Invalid traced source owner')
    r=records[owner];payload=np.asarray(result['payload_words'],dtype='<u4')
    if (r['route_float_components']!=result['float_components'] or r['route_int_components']!=result['int_components'] or
            r['route_position_offset']!=result['position_offset'] or r['route_step_start_offset']!=result['start_offset']):
        raise ValueError('Traced native layout differs from actual owner')
    p=lambda offset:payload[offset:offset+3].copy().view('<f4').astype(float).tolist()
    result['velocity_cm_s']=p(r['route_velocity_offset'])
    if 'route_inlet_offsets' in r:
        rp,rv,rf=r['route_inlet_offsets']
        result.update(unconstrained_position_cm=p(rp),unconstrained_velocity_cm_s=p(rv),
                      inlet_face_marker=float(payload[rf:rf+1].copy().view('<f4')[0]))
    from liquid_dataset import resolve as resolve_dataset
    dataset=resolve_dataset(d)
    boundary_path=dataset['parent']/'grid_vector_boundary_profile.json'
    profile=json.loads(boundary_path.read_text());packed=np.asarray(profile['packed_vectors'],dtype=float)
    bed=json.loads(dataset['face_bed'].read_text())
    mesh_path=dataset['mesh']
    if (hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=bed['source_mesh_sha256'] or
            hashlib.sha256(boundary_path.read_bytes()).hexdigest()!=bed['source_boundary_sha256']):
        raise ValueError('Current terrain/boundary sources differ from prepared profile')
    sampler=RegisteredMeshSampler(np.load(mesh_path));bounds=np.asarray(profile['domain']['native_face_bounds_m'])
    def query(face,t):
        xy=np.zeros(2);xy[face//2]=packed[3,face//2] if face%2 else 0;xy[1-face//2]=t
        en=(xy/100+bounds[0])@packed[:2,:2]
        return float(sampler.sample(*en)*100)
    try:
        c=crossing(result['start_cm'],result['end_cm'],profile,bed_query=query)
        result['independent_classification']='approved' if c else 'inside'
        result['independent_crossing']=c
    except ValueError as error:result['independent_classification']=str(error)
    a,b=np.asarray(result['start_cm']),np.asarray(result['end_cm'])
    def local(p):
        canonical=p*[1,-1,1]
        return np.r_[packed[:2,:2]@canonical[:2]-bounds[0]*100,canonical[2]-packed[2,2]]
    la,lb=local(a),local(b);result.update(independent_local_start_cm=la.tolist(),independent_local_end_cm=lb.tolist())
    face=result['face']
    if face<4 and np.isfinite([la,lb]).all() and np.all((la>=0)&(la<=packed[3])):
        axis=face//2;delta=lb[axis]-la[axis]
        t=((packed[3,axis] if face%2 else 0)-la[axis])/delta if delta else float('nan')
        if 0<=t<=1:
            hit=la+t*(lb-la);z=hit[2]+packed[2,2];zbed=query(face,hit[1-axis])
            result.update(independent_hit_z_cm=float(z),independent_hit_bed_cm=zbed,
                          independent_hit_clearance_cm=float(z-zbed))
    return result


def json_safe(value):
    if isinstance(value,np.generic):return json_safe(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    parser.add_argument('--output',required=True,type=Path);a=parser.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=json_safe(diagnose(a.directory));a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False))
