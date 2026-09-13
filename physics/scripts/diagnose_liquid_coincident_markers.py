"""Locate exact native marker coincidences and retain their birth lineage.

No merges, jitter or deleted volume. Distinct markers at one position receive
the same shared-field correction, so diagnosing their origin precedes choosing
a legitimate redistribution/contact change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from liquid_dataset import resolve
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_stage_journal import stage_groups


def duplicate_groups(positions):
    p=np.asarray(positions)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('Finite XYZ markers required')
    _,inverse,counts=np.unique(p,axis=0,return_inverse=True,return_counts=True)
    return [np.flatnonzero(inverse==group) for group in np.flatnonzero(counts>1)]


def run(directory):
    directory=directory.resolve();native=json.loads((directory/'stages.json').read_text());records=native['native_transfer_packet']
    positions=[];identities=[];velocities=[];owners=[];births={};files={}
    for r in records:
        n=r['particle_count'];nb=r['birth_particle_count'];owner=r['region_id']
        positions.append(read(directory,r,'positions',(n,4)).view('<f4')[:,:3])
        identities.append(read(directory,r,'identities',(n,4)))
        velocities.append(read(directory,r,'velocities',(n,4)).view('<f4')[:,:3])
        owners.append(np.full(n,owner))
        birth_ids=read(directory,r,'birth_identities',(nb,4));order=np.argsort(birth_ids[:,1])
        if np.any(birth_ids[:,0]!=owner) or not np.array_equal(birth_ids[order,1],np.arange(nb)):
            raise ValueError('Original contiguous immutable birth sequences required')
        births[owner]=read(directory,r,'birth_positions',(nb,4)).view('<f4')[:,:3][order]
        for key in ('positions','identities','velocities','birth_identities','birth_positions'):
            files[r[key]]=hashlib.sha256((directory/r[key]).read_bytes()).hexdigest()
    p=np.concatenate(positions).astype(float);ids=np.concatenate(identities);v=np.concatenate(velocities).astype(float);owner=np.concatenate(owners)
    if len(np.unique(ids[:,:2],axis=0))!=len(ids):raise ValueError('Native immutable identities duplicated')
    groups=duplicate_groups(p)
    observed=[g for g in stage_groups(native) if g['entries'][0]['first']]
    if any([e['owner'] for e in g['entries']]!=list(range(12)) for g in observed):
        raise ValueError('Complete ordered native spawn history required')
    cumulative=np.cumsum([[e['native_rate_spawns']+e['native_event_spawns'] for e in g['entries']] for g in observed],axis=0)
    with np.load(resolve(native)['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    details=[]
    for g in groups:
        initial=[]
        for i in g:
            birth_owner,sequence=map(int,ids[i,:2]);original=births.get(birth_owner)
            initial.append(original[sequence].astype(float).tolist() if original is not None and sequence<len(original) else None)
        all_initial=all(point is not None for point in initial)
        birth_steps=[int(np.searchsorted(cumulative[:,int(ids[i,0])],int(ids[i,1]),side='right')+1) for i in g]
        if max(birth_steps)>len(observed):raise ValueError('Native birth identity exceeds recorded spawn counts')
        details.append(dict(current_position_cm=p[g[0]].tolist(),current_owners=owner[g].tolist(),native_identities=ids[g].astype(int).tolist(),
            native_birth_steps=birth_steps,same_native_birth_step=len(set(birth_steps))==1,
            current_velocity_cm_s=v[g].tolist(),initial_positions_cm=initial,
            all_original_seed_markers=all_initial,
            original_max_separation_cm=float(np.linalg.norm(np.array(initial)-initial[0],axis=1).max()) if all_initial else None,
            original_same_xy=bool(np.array_equal(np.array(initial)[:,:2],np.broadcast_to(np.array(initial)[0,:2],(len(g),2)))) if all_initial else None,
            bed_clearance_cm=float(p[g[0],2]-100*sampler.sample(np.array([p[g[0],0]/100]),np.array([-p[g[0],1]/100]))[0])))
    initial_all=np.concatenate(list(births.values()))
    return dict(particles=len(p),coincident_groups=len(groups),coincident_particles=sum(len(g) for g in groups),
        initial_seed_coincident_groups=len(duplicate_groups(initial_all)),
        groups_all_original_seed_markers=sum(r['all_original_seed_markers'] for r in details),
        groups_original_same_xy=sum(r['original_same_xy'] is True for r in details),
        groups_same_native_birth_step=sum(r['same_native_birth_step'] for r in details),
        groups_below_2_5cm_clearance=sum(r['bed_clearance_cm']<=2.5 for r in details),
        details=details,source_files_sha256=files,
        native_stages_sha256=hashlib.sha256((directory/'stages.json').read_bytes()).hexdigest(),
        markers_modified=False,exact_event_of_coincidence_identified=False,
        physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    report=run(a.capture);a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('details','source_files_sha256')},indent=2))
