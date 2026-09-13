"""Inspect a real retained particle neighborhood; never certify spray from height.

Distance-connected sets are geometric diagnostics, not a fluid phase classifier.
The named birth identity is resolved in this capture, not assumed to retain its
storage index or its position from a different run.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from diagnose_liquid_first_rejection import decode


def connected(points, seed, radius):
    points=np.asarray(points,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all() or not 0<=seed<len(points) or not np.isfinite(radius) or radius<=0:
        raise ValueError('Finite points, valid seed and positive radius required')
    seen=np.zeros(len(points),bool);seen[seed]=True;queue=[seed]
    for i in queue:
        neighbors=np.flatnonzero((np.sum((points-points[i])**2,axis=1)<=radius**2)&~seen)
        seen[neighbors]=True;queue.extend(neighbors.tolist())
    return seen


def diagnose(directory,step,birth_owner,birth_sequence):
    directory=Path(directory).resolve();repo=Path(__file__).resolve().parents[2]
    d=json.loads((directory/'stages.json').read_text())
    h=next(x for x in d['native_particle_handoff_history'] if x['native_step']==step)
    if not h['full_audit_retained']:raise ValueError('Full native pre-commit snapshot required')
    root=(directory/h['snapshot_directory']).resolve()
    if root.parent!=directory:raise ValueError('Snapshot directory escapes capture')
    positions=[];velocities=[];identities=[];owners=[]
    for s,r in zip(h['before'],d['native_transfer_packet']):
        counts=read(root,s,'counts',(15,));n=int(counts[-1]);cap=s['capacity']
        if n>cap:raise ValueError('Invalid native count')
        w=read(root,s,'words',(h['float_components']+h['int_components'],cap))
        p=r['route_position_offset'];v=r['route_velocity_offset'];ids=r['route_identity_offsets']
        positions.append(w[p:p+3,:n].copy().view('<f4').T.astype(float))
        velocities.append(w[v:v+3,:n].copy().view('<f4').T.astype(float))
        identities.append(w[h['float_components']+np.asarray(ids[:2]),:n].T.copy())
        owners.extend([s['owner']]*n)
    positions=np.concatenate(positions);velocities=np.concatenate(velocities);identities=np.concatenate(identities)
    selected=np.flatnonzero(np.all(identities==[birth_owner,birth_sequence],axis=1))
    if len(selected)!=1:raise ValueError('Birth identity must be present exactly once')
    target=int(selected[0]);p=positions[target]
    from liquid_dataset import resolve as resolve_dataset
    profile=json.loads((resolve_dataset(d)['parent']/'grid_vector_boundary_profile.json').read_text())
    a=np.asarray(profile['packed_vectors']);axes=a[:2]*[1,-1,1];origin=a[2]*[1,-1,1]
    local=lambda points:np.column_stack(((points-origin)@axes.T+a[3,:2]/2,points[:,2]))
    q=local(positions);t=q[target]
    distances=np.array([t[0],a[3,0]-t[0],t[1],a[3,1]-t[1]])
    face=int(np.argmin(np.abs(distances)));tangent=1-face//2;nx,ny=map(int,a[5,:2])
    row=[0,ny,2*ny,2*ny+nx][face]+int(np.clip(np.floor(t[tangent]/a[4,tangent]),0,[ny,ny,nx,nx][face]-1))
    stage=float(a[8+row,1])
    near=np.flatnonzero(np.linalg.norm(positions-p,axis=1)<=200)
    if len(near)>10000:raise ValueError('Neighborhood diagnostic budget exceeded')
    seed=int(np.flatnonzero(near==target)[0]);points=positions[near];links=[]
    for radius in (25,35,50):
        mask=connected(points,seed,radius)
        links.append(dict(link_radius_cm=radius,particle_count=int(mask.sum()),
                          reaches_below_prescribed_stage=bool(np.any(points[mask,2]<stage)),
                          min_z_cm=float(points[mask,2].min()),max_z_cm=float(points[mask,2].max())))
    nearest=np.argsort(np.linalg.norm(positions-p,axis=1))[1:9]
    trace=decode(d['first_exit_rejection'],d['simulation_generation'])
    linked=False
    if trace['captured']:
        tr=d['native_transfer_packet'][trace['owner']];ti=tr['route_identity_offsets'];payload=trace['payload_words']
        key=[payload[trace['float_components']+i] for i in ti[:2]]
        linked=(trace['native_step']==step+1 and key==[birth_owner,birth_sequence] and
                np.array_equal(np.asarray(trace['start_cm'],dtype='<f4').view('<u4'),p.astype('<f4').view('<u4')))
    control=read(root/'handoff-receiving',h['receiving'],'control',(4,)).tolist()
    return dict(native_step=step,simulation_generation=d['simulation_generation'],birth_identity=[birth_owner,birth_sequence],
                current_owner=owners[target],position_cm=p.tolist(),local_station_lateral_z_cm=t.tolist(),
                velocity_cm_s=velocities[target].tolist(),nearest_physical_face=face,profile_row=row,
                prescribed_stage_cm=stage,height_above_prescribed_stage_cm=float(p[2]-stage),
                neighbors_within_2m=len(near)-1,geometric_connectivity=links,
                nearest_neighbors=[dict(birth_identity=identities[i].tolist(),position_cm=positions[i].tolist(),
                                        distance_cm=float(np.linalg.norm(positions[i]-p))) for i in nearest],
                native_commit_control=control,same_generation_pre_failure_position_bit_exact=bool(linked),
                following_first_failure_step=trace.get('native_step'),
                same_state_as_another_run=False,disconnected_spray_classification_verified=False,acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    parser.add_argument('--step',type=int,required=True);parser.add_argument('--birth-owner',type=int,required=True)
    parser.add_argument('--birth-sequence',type=int,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=diagnose(args.directory,args.step,args.birth_owner,args.birth_sequence)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
