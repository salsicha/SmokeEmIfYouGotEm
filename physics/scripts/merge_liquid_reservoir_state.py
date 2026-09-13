"""Assemble core + exterior initialization, preserving core IDs and shared cuts.

Only the independently prepared OUTER supply is installed in this candidate.
This exports a new dataset; no current runtime profile or map is replaced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_region_state import split_state


def preserved_edges(core_regions, layers, outer_cells):
    edges=[]
    for axis in (0,1):
        old=sorted({r['cell_bounds_xy'][s][axis] for r in core_regions for s in (0,1)})
        if old[0]!=0 or old[-1]+2*layers!=outer_cells[axis]:
            raise ValueError('Outer domain must add declared cell layers to both core faces')
        edges.append([0,*[i+layers for i in old[1:-1]],int(outer_cells[axis])])
    return edges


def merge(core, core_regions, buffer_path, outer, output):
    core,core_regions,buffer_path,outer,output=map(Path,(core,core_regions,buffer_path,outer,output))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    read=lambda p:json.loads(p.read_text())
    if output.exists() or (outer/'hydraulic_initial_state.json').exists():
        raise FileExistsError('Retain prior merged input evidence')
    buffer=read(buffer_path);ownership=read(core_regions/'manifest.json')
    if sha(core_regions/'manifest.json')!=buffer['original_core_ownership_sha256']:
        raise ValueError('Buffer refers to different core ownership')
    for name,digest in ownership['parent_files_sha256'].items():
        if sha(core/name)!=digest:raise ValueError('Core input changed: '+name)
    originals=[]
    for record in ownership['region_files']:
        if Path(record['file']).name!=record['file']:raise ValueError('Invalid region path')
        p=core_regions/record['file']
        if sha(p)!=record['sha256']:raise ValueError('Core region changed')
        originals.append(read(p))
    window=read(outer/'manifest.json');source=read(outer/'native_source_profile.json')
    boundary=read(outer/'grid_boundary_profile.json');initial=read(core/'hydraulic_initial_state.json')
    domain=source['domain'];core_domain=initial['domain'];layers=buffer['exterior_layers']
    for k in ('source_geometry_sha256','source_hydraulic_manifest_sha256'):
        if window[k]!=initial[k] or buffer[k]!=initial[k]:raise ValueError('Core/buffer source provenance differs')
    if (buffer['core_domain']!=core_domain or domain!=boundary['domain'] or
        domain['cell_size_m']!=core_domain['cell_size_m'] or
        domain['nominal_particle_volume_m3']!=initial['nominal_particle_volume_m3'] or
        buffer['nominal_particle_volume_m3']!=initial['nominal_particle_volume_m3']):
        raise ValueError('Core/buffer particle or cell metrics differ')
    margin=layers*np.asarray(domain['cell_size_m'][:2]);core_bounds=np.asarray(core_domain['native_face_bounds_m'])
    if not np.allclose(domain['native_face_bounds_m'],core_bounds+[-margin,margin],rtol=0,atol=1e-9):
        raise ValueError('Proposed outer faces do not match prepared buffer')
    count=initial['particle_count'];n=buffer['particle_count']
    if (count!=ownership['particle_count'] or count!=buffer['original_core_particle_count'] or
        not np.array_equal(buffer['reservoir_seed_parent_ids'],np.arange(count,count+n))):
        raise ValueError('Buffer identities collide with or replace core seed IDs')
    positions=np.concatenate((initial['positions_world_cm'],buffer['positions_canonical_cm']))
    velocity=np.concatenate((initial['velocities_world_cm_per_s'],buffer['velocities_canonical_cm_per_s']))
    if positions.shape!=(count+n,3) or velocity.shape!=positions.shape:
        raise ValueError('Merged seed payload count mismatch')
    axes=np.asarray(boundary['packed_vectors'])[:2,:2]
    source_world=np.asarray(source['positions_world_offset_cm'])+window['local_origin_engine_cm']
    source_sl=source_world[:,:2]@axes.T/100
    if np.any(np.all((source_sl>=core_bounds[0])&(source_sl<=core_bounds[1]),axis=1)):
        raise ValueError('Outer supply must not double-source the internal core interface')
    merged=dict(initial)
    merged.update(positions_world_cm=positions.tolist(),velocities_world_cm_per_s=velocity.tolist(),
        particle_count=count+n,domain=domain,native_source_profile_sha256=sha(outer/'native_source_profile.json'),
        preserved_core_seed_count=count,exterior_buffer_seed_count=n,
        core_initial_state_sha256=sha(core/'hydraulic_initial_state.json'),
        exterior_buffer_preparation_sha256=sha(buffer_path),
        represented_nominal_volume_m3=(count+n)*initial['nominal_particle_volume_m3'],
        column_quadrature_wet_volume_m3=initial['column_quadrature_wet_volume_m3']+buffer['column_quadrature_volume_m3'],
        volume_quantization_error_m3=initial['volume_quantization_error_m3']+buffer['volume_quantization_error_m3'],
        column_counts_xy=(2*np.asarray(domain['physical_cells'][:2])).tolist(),
        volume_quantization_scope='Core and buffer apportioned separately to preserve every original core identity',
        minimum_exact_bed_clearance_m=min(initial['minimum_exact_bed_clearance_m'],buffer['minimum_original_bed_clearance_cm']/100),
        initial_state_applied_once_required=True,production_promoted=False)
    edges=preserved_edges(originals,layers,domain['physical_cells'])
    bundles,manifest=split_state(window,source,merged,axes,cell_edges=edges)
    if len(bundles)!=len(originals):raise ValueError('Buffer unexpectedly changed regional owner count')
    for old,new,expected in zip(originals,bundles,buffer['expanded_owner_bounds']):
        if old['id']!=new['id'] or not np.array_equal(new['cell_bounds_xy'],np.asarray(expected['cell_bounds_xy'])+layers):
            raise ValueError('Original shared cuts moved during buffer merge')
        ids=np.asarray(new['seed_parent_ids']);mask=ids<count
        if (ids[mask].tolist()!=old['seed_parent_ids'] or
            not np.array_equal(np.asarray(new['positions_canonical_cm'])[mask],old['positions_canonical_cm']) or
            not np.array_equal(np.asarray(new['velocities_canonical_cm_per_s'])[mask],old['velocities_canonical_cm_per_s'])):
            raise ValueError('Original core particle identity, owner or state changed')
    # All semantic validation completes before any artifact is written.
    output.mkdir(parents=True,exist_ok=False)
    with (outer/'hydraulic_initial_state.json').open('x') as f:json.dump(merged,f,separators=(',',':'))
    manifest.update(preserved_core_seed_count=count,exterior_buffer_seed_count=n,
        core_seed_state_bit_exact=True,original_shared_cuts_preserved=True,
        core_interface_has_source_emission=False,buffer_runtime_verified=False,
        exterior_buffer_preparation_sha256=sha(buffer_path),explicit_cell_edges=edges)
    manifest['parent_files_sha256']={name:sha(outer/name) for name in
        ('manifest.json','native_source_profile.json','hydraulic_initial_state.json','grid_boundary_profile.json')}
    manifest['region_files']=[]
    for b in bundles:
        p=output/f'region-{b["id"]:03d}.json'
        with p.open('x') as f:json.dump(b,f,separators=(',',':'))
        manifest['region_files'].append(dict(file=p.name,sha256=sha(p)))
    with (output/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    return {k:manifest[k] for k in ('particle_count','preserved_core_seed_count','exterior_buffer_seed_count',
        'region_count','max_region_seeds','max_region_render_voxels','external_inflow_m3_per_s',
        'core_seed_state_bit_exact','original_shared_cuts_preserved','core_interface_has_source_emission','buffer_runtime_verified')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('core','regions','buffer','outer','output'):p.add_argument(name,type=Path)
    a=p.parse_args();print(json.dumps(merge(a.core,a.regions,a.buffer,a.outer,a.output),indent=2))
