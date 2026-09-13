"""Inspect exact native-position collisions in a rejected density trial.

Read-only with respect to the source capture, particle package and terrain.
The report preserves every candidate and original identity; it never repairs,
merges, jitters or deletes particles. Not a simulation or acceptance test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_dataset import resolve
from liquid_particle_density import objective, descent_direction
from liquid_particle_quantization import quantized_endpoint
from solve_liquid_particle_density import constrained_direction
from south_fork_registered_mesh import RegisteredMeshSampler
from audit_liquid_native_handoff import read


def diagnose(package, step=1):
    package=package.resolve()
    m=json.loads((package/'manifest.json').read_text())
    if m['position_representation']!='float32-world-cm':
        raise ValueError('Native-representable source required')
    capture=Path(m['native_capture']);geometry=Path(m['geometry_package'])
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if sha(capture/'stages.json')!=m['native_stages_sha256'] or sha(geometry/'manifest.json')!=m['geometry_manifest_sha256']:
        raise ValueError('Source provenance differs')
    native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    g=json.loads((geometry/'manifest.json').read_text())
    h=np.array(g['spacing_cm']);cells=np.array(g['cells'])
    axes=np.array(g['world_axes']);lower=np.array(g['world_lower_cm'])
    item=m['accepted_steps'][step-1];path=package/item['file']
    if sha(path)!=item['sha256'] or sha(package/'state.npz')!=m['state_sha256']:
        raise ValueError('Particle source differs')
    with np.load(path) as s:points=s['positions_world_cm']
    with np.load(package/'state.npz') as s:
        ids=s['identities'];required=s['required_clearance_cm']
    original=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float)
                             for r in native['native_transfer_packet']])
    solid_path=geometry/g['files']['solid_kernel_fraction']['file']
    if sha(solid_path)!=m['solid_kernel_sha256'] or sha(dataset['mesh'])!=m['registered_mesh_sha256']:
        raise ValueError('Bed differs')
    solid=np.fromfile(solid_path,dtype='<f4').reshape(cells[::-1]).astype(float)
    volumes=np.concatenate([np.full(r['particle_count'],float(np.float32(r['particle_volume_m3']))*1e6)
                            for r in native['native_transfer_packet']])
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    local=(points-lower)@axes.T
    result=objective(local,cells,h,volumes,solid)
    direction=descent_direction(result,h)
    move,contact=constrained_direction(points,local,direction,axes,h,2*h*[1,1,0],(cells-[2,2,0])*h,
        sampler,required,native_positions=True)
    trial,_=quantized_endpoint(points,move@axes,float(np.linalg.norm(h)))
    unique,inverse,counts=np.unique(trial,axis=0,return_inverse=True,return_counts=True)
    groups=[]
    for group in np.flatnonzero(counts>1):
        members=np.flatnonzero(inverse==group)
        p=points[members];op=original[members]
        delta=p[:,None]-p[None,:];od=op[:,None]-op[None,:]
        pairs=np.triu_indices(len(p),1)
        groups.append(dict(indices=members.tolist(),identities=ids[members].tolist(),
            original_world_cm=op.tolist(),before_world_cm=p.tolist(),candidate_world_cm=unique[group].tolist(),
            before_pair_distance_cm=np.linalg.norm(delta,axis=2)[pairs].tolist(),
            original_pair_distance_cm=np.linalg.norm(od,axis=2)[pairs].tolist(),
            unquantized_world_cm=(p+move[members]@axes).tolist(),
            direction_local_cm=direction[members].tolist(),contact_move_local_cm=move[members].tolist(),
            before_bed_clearance_cm=(p[:,2]-100*sampler.sample(p[:,0]/100,-p[:,1]/100)).tolist()))
    return dict(schema='raftsim.represented_pair_diagnostic.v1',package=str(package),
        manifest_sha256=sha(package/'manifest.json'),step=step,particles=len(points),
        before_unique=len(np.unique(points,axis=0)),candidate_unique=len(unique),
        collision_groups=groups,contact=contact,changed_source_or_particles=False,
        physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path)
    p.add_argument('--step',type=int,default=1);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    r=diagnose(a.package,a.step)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('contact','collision_groups')}))
    print(json.dumps(r['collision_groups'],indent=2))
