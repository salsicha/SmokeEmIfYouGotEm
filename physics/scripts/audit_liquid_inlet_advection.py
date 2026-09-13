"""Audit retained native inlet responses against original terrain and float64 math.

Only unobstructed responses can be independently checked here; a subsequent
terrain collision needs its own swept-contact audit. Never call these visual,
discharge, or whole-scene acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_inlet_advection import constrain
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_dataset import resolve as resolve_dataset


def normal_update_roundoff_bound(velocity, normal, target):
    """Arithmetic envelope includes the uncancelled prescribed-current term.

    A small final velocity is not a bound on intermediate arithmetic. Keep the
    existing gamma32, but bound v+n*(U-dot(v,n))*weight before cancellation.
    This is not an uncertainty allowance for physical parameters or bad input.
    """
    velocity,normal=np.asarray(velocity),np.asarray(normal)
    u=2**-24;gamma=32*u/(1-32*u)
    scale=np.abs(velocity)+np.abs(normal)*(abs(target)+np.sum(np.abs(velocity*normal)))
    return gamma*max(1,float(np.max(scale)))


def audit(directory, step):
    directory=Path(directory);repo=Path(__file__).resolve().parents[2]
    d=json.loads((directory/'stages.json').read_text())
    model=d.get('native_inlet_model','plane-only-v1')
    if model not in ('plane-only-v1','normal-relaxation-v1'):raise ValueError('Unknown native inlet model')
    relaxation_enabled=model=='normal-relaxation-v1'
    h=next(x for x in d['native_particle_handoff_history'] if x['native_step']==step)
    if not h['full_audit_retained']:raise ValueError('Full native trajectory retention required')
    root=directory/h['snapshot_directory']
    dataset=resolve_dataset(d)
    profile=json.loads((dataset['parent']/'grid_vector_boundary_profile.json').read_text())
    bed=json.loads(dataset['face_bed'].read_text())
    mesh_path=dataset['mesh']
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=bed['source_mesh_sha256']:
        raise ValueError('Contact source changed')
    sampler=RegisteredMeshSampler(np.load(mesh_path))
    packed=np.asarray(profile['packed_vectors'],dtype=float);axes=packed[:2,:2]
    lower=np.asarray(profile['domain']['native_face_bounds_m'][0])
    def bed_query(face,t):
        local=np.zeros(2);local[face//2]=packed[3,face//2] if face%2 else 0
        local[1-face//2]=t;en=(local/100+lower)@axes
        return float(sampler.sample(*en)*100)
    corrections=[];deferred=[];candidates=0
    for s,r in zip(h['before'],d['native_transfer_packet']):
        if 'route_inlet_offsets' not in r:raise ValueError('Missing raw native inlet inputs')
        n=int(np.fromfile(root/s['counts'],dtype='<u4')[-1]);cap=s['capacity']
        if n>cap:raise ValueError('Native count exceeds capacity')
        w=np.fromfile(root/s['words'],dtype='<u4').reshape(h['float_components']+h['int_components'],cap)
        def point(offset):return w[offset:offset+3,:n].view('<f4').T.astype(float)
        raw_p,raw_v,face_offset=r['route_inlet_offsets']
        a=point(r['route_step_start_offset']);b=point(raw_p);v=point(raw_v)
        p=point(r['route_position_offset']);velocity=point(r['route_velocity_offset'])
        faces=w[face_offset,:n].view('<f4')
        if not np.isfinite(faces).all() or np.any(faces!=np.floor(faces)) or np.any((faces<0)|(faces>4)):
            raise ValueError('Invalid native inlet response marker')
        # Check every predicted exterior trajectory, including zero-marker
        # candidates, not only the particles the implementation marked corrected.
        local=b*[1,-1,1]-packed[2]
        xy=local[:,:2]@axes.T+packed[3,:2]/2
        selected=np.any((xy<0)|(xy>packed[3,:2]),axis=1)|(faces>0)
        if relaxation_enabled:
            start_local=a*[1,-1,1]-packed[2]
            start_xy=start_local[:,:2]@axes.T+packed[3,:2]/2
            width=np.minimum(4*packed[4,:2],.25*packed[3,:2])
            selected|=np.any((start_xy<width)|(start_xy>packed[3,:2]-width),axis=1)
        for i in np.flatnonzero(selected):
            candidates+=1
            expected_p,expected_v,face=constrain(a[i],b[i],v[i],1/60,profile,bed_query,relaxation_enabled=relaxation_enabled)
            if face!=faces[i]:raise ValueError(f'Native inlet classification differs: owner{s["owner"]}, row{i}, CPU{face}, GPU{faces[i]}')
            if not face:continue
            # Subsequent terrain projection is intentionally NOT bypassed.
            # Screen sampled paths against its 2 cm skin before this simple
            # comparison. This is not a proof of continuous swept clearance.
            samples=a[i]+np.linspace(0,1,33)[:,None]*(expected_p-a[i])
            clearance=samples[:,2]-sampler.sample(samples[:,0]/100,-samples[:,1]/100)*100
            if np.min(clearance)<2.1:
                deferred.append(dict(owner=s['owner'],row=int(i)));continue
            # Conservative forward roundoff bound for subtract/dot, unit basis,
            # multiply and additions in the native float32 response.
            u=2**-24;gamma=32*u/(1-32*u)
            pbound=gamma*max(1,float(np.max(abs(a[i])+abs(b[i])+abs(packed[2]))))
            vbound=gamma*max(1,float(np.max(abs(v[i])+abs(expected_v))))
            if relaxation_enabled:
                f=face-1;tangent=1-f//2
                column=int(np.clip(np.floor(start_xy[i,tangent]/packed[4,tangent]),0,packed[5,tangent]-1))
                offsets=[0,int(packed[5,1]),2*int(packed[5,1]),2*int(packed[5,1])+int(packed[5,0])]
                target=packed[8+offsets[f]+column,2]
                normal=packed[f//2]*[1,-1,1]*(1 if f%2==0 else -1)
                vbound=max(vbound,normal_update_roundoff_bound(v[i],normal,target))
            pe=float(np.max(abs(p[i]-expected_p)));ve=float(np.max(abs(velocity[i]-expected_v)))
            if pe>pbound or ve>vbound:
                raise ValueError(f'Native inlet position/velocity differs: owner{s["owner"]} row{i} face{face-1}; '
                    f'position {pe}/{pbound}, velocity {ve}/{vbound}; start={a[i].tolist()}, '
                    f'raw_position={b[i].tolist()}, raw_velocity={v[i].tolist()}, '
                    f'expected_velocity={expected_v.tolist()}, actual_velocity={velocity[i].tolist()}')
            corrections.append(dict(owner=s['owner'],row=int(i),face=face-1,
                position_error_cm=pe,velocity_error_cm_s=ve,
                velocity_impulse_cm_s=(expected_v-v[i]).tolist(),
                minimum_path_clearance_cm=float(np.min(clearance))))
    if not corrections:raise ValueError('No actual inlet response was retained')
    return dict(native_step=step,inlet_model=model,checked_candidates=candidates,verified_responses=corrections,
                terrain_contact_responses_not_verified=deferred,
                all_retained_inlet_responses_verified=not deferred,
                continuous_terrain_clearance_verified=False,
                mass_discharge_visual_performance_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--step',required=True,type=int)
    parser.add_argument('--output',required=True,type=Path);a=parser.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=audit(a.directory,a.step);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
