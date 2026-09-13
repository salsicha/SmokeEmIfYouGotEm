"""Read-only native coincidence/lineage audit; never merge or move particles.

An identical XYZ pair cannot separate under any single-valued shared map.
The paired current-step fields do not locate the first historic collapse;
birth separation proves only that coincidence was not present at initial birth.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read


def coincident_rows(positions):
    p=np.asarray(positions)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('Finite XYZ particle positions required')
    _,inverse,counts=np.unique(p,axis=0,return_inverse=True,return_counts=True)
    return [np.flatnonzero(inverse==group) for group in np.flatnonzero(counts>1)]


def audit(capture):
    capture=Path(capture).resolve();m=json.loads((capture/'stages.json').read_text())
    if not m.get('native_transfer_packet_saved') or m['exchange_error']:raise ValueError('Saved successful native packet required')
    records=m['native_transfer_packet'];positions=[];identities=[];owners=[];offsets={};sources={}
    def load(r,key,count):
        result=read(capture,r,key,(count,4));sources[r[key]]=hashlib.sha256((capture/r[key]).read_bytes()).hexdigest()
        return result
    total=0
    for r in records:
        count=r['particle_count'];offsets[r['region_id']]=total;total+=count
        positions.append(load(r,'positions',count).view('<f4')[:,:3]);identities.append(load(r,'identities',count))
        owners.append(np.full(count,r['region_id']))
    positions=np.concatenate(positions);identities=np.concatenate(identities);owners=np.concatenate(owners)
    groups=coincident_rows(positions);details=[]
    for group in groups:
        members=[]
        for k in group:
            owner=int(owners[k]);r=records[owner];row=int(k-offsets[owner]);identity=identities[k]
            member=dict(row=int(k),owner=owner,identity=identity.tolist(),position_world_cm=positions[k].tolist())
            aid=load(r,'advection_identities',r['particle_count'])
            found=np.flatnonzero(np.all(aid==identity,axis=1))
            if len(found)!=1:raise ValueError('Current advection identity is not uniquely matched')
            for key in ('advection_raw_positions','advection_positions'):
                member[key]=load(r,key,r['particle_count']).view('<f4')[found[0],:3].tolist()
            birth=records[int(identity[0])];bid=load(birth,'birth_identities',birth['birth_particle_count'])
            initial=np.flatnonzero(np.all(bid[:,:2]==identity[:2],axis=1))
            member['initial_birth_captured']=bool(len(initial))
            if len(initial)>1:raise ValueError('Ambiguous initial identity')
            if len(initial):member['initial_birth_position_cm']=load(birth,'birth_positions',birth['birth_particle_count']).view('<f4')[initial[0],:3].tolist()
            members.append(member)
        details.append(dict(multiplicity=len(group),members=members))
    return dict(schema='raftsim.native_coincidence_lineage.v1',native_capture=str(capture),
        native_stages_sha256=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest(),
        native_step=m['native_transfer_packet_step'],particles=len(positions),coincident_groups=len(groups),
        coincident_members=sum(len(g) for g in groups),groups=details,sources_sha256=sources,
        unique_positions_verified=not groups,first_collapse_step_verified=False,particles_modified=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=audit(a.capture);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='sources_sha256'},indent=2,allow_nan=False))
    raise SystemExit(0 if result['unique_positions_verified'] else 1)
