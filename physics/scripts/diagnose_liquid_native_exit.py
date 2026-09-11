"""Explain exterior trajectories in one fully retained native commit (not acceptance)."""
import argparse
import collections
import json
import hashlib
from pathlib import Path
import numpy as np
from audit_liquid_native_retirement import crossing
from south_fork_registered_mesh import RegisteredMeshSampler


def diagnose(directory, step):
    directory=Path(directory);repo=Path(__file__).resolve().parents[2]
    report=json.loads((directory/'stages.json').read_text())
    profile=json.loads((repo/'tmp/south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json').read_text())
    packed=np.asarray(profile['packed_vectors'],dtype=float)
    axes=packed[:2];bounds=np.asarray(profile['domain']['native_face_bounds_m'])*100
    extent=packed[3];base=packed[2,2]
    bed_query=None
    if report.get('native_exact_exit_bed'):
        bed_profile=json.loads((repo/'tmp/south-fork-liquid-face-bed-20260910/physical_face_bed.json').read_text())
        mesh_path=repo/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz'
        if hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=bed_profile['source_mesh_sha256']:
            raise ValueError('Exact bed mesh changed since profile preparation')
        sampler=RegisteredMeshSampler(np.load(mesh_path))
        def bed_query(face,tangent_cm):
            # Independent original triangle lookup, not interpolation of the
            # same knot table uploaded to the GPU under examination.
            normal=face//2;tangent=1-normal;local=np.zeros(2)
            local[normal]=extent[normal] if face%2 else 0;local[tangent]=tangent_cm
            en=(local/100+bounds[0]/100)@axes[:,:2]
            return float(sampler.sample(en[0],en[1])*100)
    h=next(h for h in report['native_particle_handoff_history'] if h['native_step']==step)
    if not h['full_audit_retained']:raise ValueError('Full retained commit required')
    root=directory/h['snapshot_directory'];records=report['native_transfer_packet']
    counts=collections.Counter();samples=[]
    for s,r in zip(h['before'],records):
        n=int(np.fromfile(root/s['counts'],dtype='<u4')[-1]);cap=s['capacity']
        if n>cap:raise ValueError('Native count exceeds allocation')
        w=np.fromfile(root/s['words'],dtype='<u4').reshape(h['float_components']+h['int_components'],cap)
        def points(offset):return w[offset:offset+3,:n].view('<f4').T.astype(float)
        a=points(r['route_step_start_offset']);b=points(r['route_position_offset'])
        def local(p):
            canonical=p*[1,-1,1]
            return np.column_stack((canonical[:,:2]@axes[:,:2].T-bounds[0],canonical[:,2]-base))
        la,lb=local(a),local(b)
        outside=np.any((lb<0)|(lb>extent),axis=1)|np.any((la<0)|(la>extent),axis=1)
        for i in np.flatnonzero(outside):
            try:
                result=crossing(a[i],b[i],profile,bed_query=bed_query);reason='approved' if result else 'inside'
            except ValueError as error:reason=str(error)
            counts[reason]+=1
            if reason=='approved' or sum(s['reason']==reason for s in samples)>=8:continue
            sample=dict(owner=s['owner'],row=int(i),reason=reason,start_cm=a[i].tolist(),end_cm=b[i].tolist(),
                        local_start_cm=la[i].tolist(),local_end_cm=lb[i].tolist())
            vo=r['route_velocity_offset']
            sample['native_velocity_cm_s']=w[vo:vo+3,i].copy().view('<f4').astype(float).tolist()
            if 'route_inlet_offsets' in r:
                rp,rv,rf=r['route_inlet_offsets']
                sample.update(unconstrained_position_cm=w[rp:rp+3,i].copy().view('<f4').astype(float).tolist(),
                              unconstrained_velocity_cm_s=w[rv:rv+3,i].copy().view('<f4').astype(float).tolist(),
                              inlet_face_marker=float(w[rf:rf+1,i].copy().view('<f4')[0]))
            hits=[]
            for axis in range(3):
                if lb[i,axis]<0 or lb[i,axis]>extent[axis]:
                    high=lb[i,axis]>extent[axis]
                    t=((extent[axis] if high else 0)-la[i,axis])/(lb[i,axis]-la[i,axis])
                    hits.append((float(t),2*axis+int(high)))
            if hits:
                t,face=min(hits);sample.update(first_face=face,fraction=t)
                hit=la[i]+t*(lb[i]-la[i]);sample['local_hit_cm']=hit.tolist()
                if face<4:
                    cells=packed[5].astype(int);tangent=1 if face<2 else 0
                    column=int(np.clip(np.floor(hit[tangent]/packed[4,tangent]),0,cells[tangent]-1))
                    row=[0,cells[1],2*cells[1],2*cells[1]+cells[0]][face]+column
                    sample.update(profile_row=int(row),bed_stage_normal_cm=packed[8+row].tolist(),hit_world_z_cm=float(hit[2]+base))
                    bed,stage,inward=packed[8+row]
                    if bed_query is not None:bed=bed_query(face,hit[tangent])
                    sample.update(pointwise_bed_cm=float(bed),terrain_clearance_cm=float(hit[2]+base-bed),
                                  prescribed_inward_velocity_cm_s=float(inward),
                                  segment_inward_displacement_cm=float((lb[i,face//2]-la[i,face//2])*(-1 if face%2 else 1)),
                                  rejected_conditions=dict(non_outgoing=bool(inward>=0),dry=bool(stage<=bed),
                                                           below_bed=bool(hit[2]+base<=bed)))
            samples.append(sample)
    return dict(native_step=step,pointwise_terrain_query=bed_query is not None,exterior_reasons=dict(counts),examples=samples,acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--step',required=True,type=int)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=diagnose(args.directory,args.step)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
