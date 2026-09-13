"""Independently re-deposit saved density-correction positions and inspect terrain.

No trust in the optimization's reported objective or phase mask. Reuse the
separate volume-scatter reference, original native identities and exact bed.
Only the final endpoint is independently available in v1 packages; their full
piecewise correction trajectory is NOT independently certified by this audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from liquid_dataset import resolve
from liquid_volume_interface import deposit_volume,measure_interface
from liquid_density_projection import density_accounting
from diagnose_liquid_projection_packet import load_field
from south_fork_registered_mesh import RegisteredMeshSampler
from audit_liquid_particle_routes import physical_owners
from liquid_swept_bed import swept_clearance


def audit(package):
    package=package.resolve();m=json.loads((package/'manifest.json').read_text())
    representation=m.get('position_representation','float64-world-cm')
    if representation not in ('float64-world-cm','float32-world-cm'):raise ValueError('Unknown position representation')
    capture=Path(m['native_capture']);geometry=Path(m['geometry_package'])
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if (m['schema']!='raftsim.liquid_particle_density_descent.v1' or
            sha(capture/'stages.json')!=m['native_stages_sha256'] or sha(geometry/'manifest.json')!=m['geometry_manifest_sha256'] or
            sha(package/'state.npz')!=m['state_sha256'] or not m['sources_unchanged']):raise ValueError('Intact source and saved-state provenance required')
    for name,digest in m['source_files_sha256'].items():
        p=(package/'sources'/name).resolve()
        if p.parent!=package/'sources' or sha(p)!=digest:raise ValueError('Algorithm snapshot changed')
    native=json.loads((capture/'stages.json').read_text());g=json.loads((geometry/'manifest.json').read_text());dataset=resolve(native)
    if sha(dataset['mesh'])!=m['registered_mesh_sha256']:raise ValueError('Physical bed changed')
    solid_file=geometry/g['files']['solid_kernel_fraction']['file']
    if solid_file.resolve().parent!=geometry or sha(solid_file)!=m['solid_kernel_sha256']:raise ValueError('Bed kernel changed')
    cells=np.array(g['cells']);h=np.array(g['spacing_cm']);axes=np.array(g['world_axes']);lower=np.array(g['world_lower_cm'])
    solid=np.fromfile(solid_file,dtype='<f4').reshape(cells[::-1]).astype(float)
    records=native['native_transfer_packet']
    original=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in records])
    identities=np.concatenate([read(capture,r,'identities',(r['particle_count'],4)) for r in records])
    with np.load(package/'state.npz') as state:
        moved=state['positions_world_cm'];required=state['required_clearance_cm']
        if (moved.shape!=original.shape or moved.dtype!=np.float64 or not np.isfinite(moved).all() or
                not np.array_equal(state['identities'],identities) or required.shape!=(len(original),)):
            raise ValueError('All original particle identities and finite saved positions required')
        if representation=='float32-world-cm' and not np.array_equal(moved,moved.astype('<f4').astype(float)):
            raise ValueError('Saved positions do not match declared native representation')
    volume_set={float(np.float32(r['particle_volume_m3'])) for r in records}
    if len(volume_set)!=1:raise ValueError('Independent fixed-volume scatter requires one native particle volume')
    volume=volume_set.pop()
    manifest=json.loads((dataset['regions']/'manifest.json').read_text());physical=np.array(manifest['domain']['physical_cells'])
    edges=manifest['explicit_cell_edges'];types=np.zeros(tuple(cells[::-1]),int);written=np.zeros_like(types,bool)
    regions=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    for r in records:
        row,col=divmod(r['region_id'],4);width=edges[0][col+1]-edges[0][col];height=edges[1][row+1]-edges[1][row]
        offset=np.array([edges[0][col],physical[1]-edges[1][row+1]])
        lo=np.array([0 if offset[a]==0 else 2 for a in range(2)])
        hi=np.array([width+4 if offset[0]+width==physical[0] else width+2,height+4 if offset[1]+height==physical[1] else height+2])
        src=(slice(None),slice(lo[1],hi[1]),slice(lo[0],hi[0]))
        dest=(slice(None),slice(offset[1]+lo[1],offset[1]+hi[1]),slice(offset[0]+lo[0],offset[0]+hi[0]))
        if written[dest].any():raise ValueError('Double-counted native phase ownership')
        types[dest]=np.rint(load_field(capture,r,'projection_boundary',4)[src][...,3]).astype(int);written[dest]=True
    if not written.all():raise ValueError('Incomplete original native phase map')
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    before_clearance=original[:,2]-100*sampler.sample(original[:,0]/100,-original[:,1]/100)
    if not np.array_equal(required,np.minimum(before_clearance,2.)):raise ValueError('Required input skin was changed')
    path_reports=[];previous=original
    if 'accepted_steps' in m:
        if len(m['accepted_steps'])!=m['accepted_iterations']:raise ValueError('Accepted step history count differs')
        for index,item in enumerate(m['accepted_steps']):
            path=(package/item['file']).resolve()
            if path.parent!=package or path.name!=f'step-{index+1:03d}.npz' or sha(path)!=item['sha256']:
                raise ValueError('Saved correction trajectory changed')
            with np.load(path) as step:current=step['positions_world_cm']
            if current.shape!=original.shape or current.dtype!=np.float64 or not np.isfinite(current).all():raise ValueError('Incomplete path positions')
            if representation=='float32-world-cm' and not np.array_equal(current,current.astype('<f4').astype(float)):
                raise ValueError('Intermediate path differs from native representation')
            swept,_,_=swept_clearance(sampler,previous*[1,-1,1]/100,current*[1,-1,1]/100)
            skin=100*swept-required;owners=physical_owners(current,regions)
            path_reports.append(dict(step=index+1,physical_bed_penetrations=int((swept<0).sum()),
                unique_particle_positions=len(np.unique(current,axis=0)),
                skin_violations=int((skin < -1e-6).sum()),minimum_skin_margin_cm=float(skin.min()),
                minimum_swept_clearance_cm=float(100*swept.min()),survey_outer_violations=int((owners<0).sum())))
            previous=current
        if not np.array_equal(previous,moved):raise ValueError('Final saved state differs from accepted trajectory')
    summaries=[]
    for name,points in (('original',original),('saved_float64',moved),('prospective_native_float32',moved.astype('<f4').astype(float))):
        local=(points-lower)@axes.T/100;mass=deposit_volume(local,cells,h/100,volume);rho=mass/np.prod(h/100)
        clearance=points[:,2]-100*sampler.sample(points[:,0]/100,-points[:,1]/100)
        margin=clearance-required;owners=physical_owners(points,regions)
        full=density_accounting(rho,solid,types)
        summaries.append(dict(state=name,whole_domain=full,energy=.5*full['total_density_excess_squared_sum'],
            unique_particle_positions=len(np.unique(points,axis=0)),
            particle_count=len(points),nominal_volume_m3=len(points)*volume,deposited_volume_m3=float(mass.sum()),
            physical_bed_penetrations=int((clearance<0).sum()),minimum_bed_clearance_cm=float(clearance.min()),
            raw_negative_required_margins=int((margin<0).sum()),required_skin_violations=int((margin < -1e-6).sum()),
            minimum_required_margin_cm=float(margin.min()),survey_outer_violations=int((owners<0).sum()),
            fixed_density_isovalue_candidate=measure_interface(mass,h/100,local)))
    original_result,saved,native_result=summaries
    return dict(schema='raftsim.liquid_particle_density_independent.v1',package=str(package),manifest_sha256=sha(package/'manifest.json'),
        all_original_identities_preserved=True,particles=len(original),states=summaries,
        declared_position_representation=representation,
        represented_positions_verified=representation=='float32-world-cm',
        energy_decreased=saved['energy']<original_result['energy'],
        saved_endpoint_geometry_valid=not(saved['physical_bed_penetrations'] or saved['required_skin_violations'] or saved['survey_outer_violations']),
        prospective_native_endpoint_geometry_valid=not(native_result['physical_bed_penetrations'] or native_result['required_skin_violations'] or native_result['survey_outer_violations']),
        physical_momentum_or_particle_volume_modified=False,path_steps=path_reports,
        full_piecewise_path_independently_verified=bool(path_reports and not any(
            r['physical_bed_penetrations'] or r['skin_violations'] or r['survey_outer_violations'] for r in path_reports)),
        all_saved_steps_have_distinct_positions=bool(path_reports and all(
            r['unique_particle_positions']==len(original) for r in path_reports)),
        native_integrated=False,physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    r=audit(a.package);a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='states'},indent=2))
    for state in r['states']:print(json.dumps({k:v for k,v in state.items() if k not in ('whole_domain','fixed_density_isovalue_candidate')}))
