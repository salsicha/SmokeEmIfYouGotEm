"""Check prepared whole-rapid liquid data; not runtime or realism acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler
from build_south_fork_liquid_contact import sample_packed

ROOT=Path(__file__).resolve().parents[2]


def audit(directory):
    read=lambda name:json.loads((directory/name).read_text())
    window=read('manifest.json');source=read('native_source_profile.json')
    seeds=read('hydraulic_initial_state.json');contact=read('triangle_contact_profile.json')
    boundary=read('grid_vector_boundary_profile.json');base=read('grid_boundary_profile.json')
    native_path=ROOT/window['native_flux_audit_path'];native=json.loads(native_path.read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks={}
    checks['versioned_rectangular_formats']=(source['schema']=='raftsim.native_face_liquid_source.v2' and
        seeds['schema']=='raftsim.registered_liquid_initial_state.v2' and contact['schema']=='raftsim.registered_liquid_contact.v2' and
        boundary['schema']=='raftsim.liquid_grid_boundary.v3')
    checks['source_identity_matches']=all(p['source_geometry_sha256']==window['source_geometry_sha256'] for p in (source,seeds,contact,boundary,native))
    checks['native_faces_unchanged']=sha(native_path.parent/'native_faces.npz')==native['faces_sha256']
    checks['native_audit_unchanged']=sha(native_path)==source['native_flux_report_sha256']==boundary['native_flux_report_sha256']==window['native_flux_audit_sha256']
    checks['solid_unchanged']=sha(directory/'collision_solid.npz')==window['solid_sha256']==source['solid_sha256']
    checks['seed_source_unchanged']=sha(directory/'native_source_profile.json')==seeds['native_source_profile_sha256']
    domain=source['domain']
    checks['one_explicit_domain']=domain==seeds['domain']==boundary['domain']
    geometry=json.loads((ROOT/window['source_geometry_manifest']).read_text())
    mesh=ROOT/geometry['mesh_path'];checks['captured_mesh_unchanged']=sha(mesh)==window['source_geometry_sha256']
    sampler=RegisteredMeshSampler(np.load(mesh))
    positions=np.asarray(seeds['positions_world_cm']);velocities=np.asarray(seeds['velocities_world_cm_per_s'])
    bed=sampler.sample(positions[:,0]/100,positions[:,1]/100)*100
    packed=sample_packed(contact['packed_vectors'],positions[:,:2],relative_vertices=True)
    error=float(np.max(abs(bed-packed)))
    checks['actual_encoded_seed_positions']=bool(np.array_equal(positions,positions.astype(np.float32).astype(float)))
    checks['all_seed_terrain_queries_within_existing_tolerance']=bool(np.isfinite(packed).all() and error<=.01)
    checks['seeds_clear_actual_bed']=bool(np.all(positions[:,2]>bed))
    checks['finite_seed_state']=bool(np.isfinite(positions).all() and np.isfinite(velocities).all() and positions.shape==velocities.shape)
    checks['nominal_volume_quantization']=abs(seeds['volume_quantization_error_m3'])<=domain['nominal_particle_volume_m3']/2
    origin=np.asarray(window['local_origin_engine_cm'])
    source_positions=np.asarray(source['positions_world_offset_cm'])+origin
    source_bed=sampler.sample(source_positions[:,0]/100,source_positions[:,1]/100)*100
    checks['source_offsets_restore_correct_world_origin']=bool(np.all(source_positions[:,2]>source_bed))
    weights=np.asarray(source['weights_m3_per_s'])
    grouped={name:np.zeros(len(values)) for name,values in native['face_discharge_m3_per_s'].items()}
    for identifier,weight in zip(source['source_face_subface_layer'],weights):grouped[identifier[0]][identifier[1]]+=weight
    source_error=max(float(np.max(abs(grouped[name]-np.maximum(values,0)))) for name,values in native['face_discharge_m3_per_s'].items())
    checks['each_native_inflow_face_preserved']=source_error<=1e-9
    scalar=np.asarray(base['packed_vectors']);vectors=np.asarray(boundary['packed_vectors'])
    checks['vector_extension_preserves_scalar_boundary']=np.array_equal(scalar,vectors[:len(scalar)])
    checks['explicit_vector_offset']=boundary['vector_rows_offset']==len(scalar)
    residual=[];velocity_error=0.;cursor=len(scalar)
    for face,(offset,count,report) in enumerate(zip(boundary['face_rows_offsets'],boundary['face_row_counts'],boundary['faces'])):
        rows=scalar[offset:offset+count];v=vectors[cursor:cursor+count];cursor+=count
        velocity_error=max(velocity_error,float(np.max(abs(v[:,0 if face<2 else 1]*(1 if face%2==0 else -1)-rows[:,2]))))
        reconstructed=rows[:,2]/100*np.asarray(report['wet_area_m2'])
        target=np.asarray(native['face_discharge_m3_per_s'][report['face']])
        residual.append(float(target.sum()-reconstructed.sum()))
    checks['vector_normal_agrees_with_scalar_flux']=velocity_error<=1e-8
    checks['outgoing_residual_within_existing_noise_allowance']=all(-1e-7<=r<=1e-10 for r in residual)
    checks['no_implicit_profile_truncation']=cursor==len(vectors)
    cells=np.asarray(domain['computational_cells']);render_cells=cells*2
    result=dict(checks=checks,prepared_data_verified=all(checks.values()),
        seed_particles=len(positions),source_sites=len(source_positions),contact_triangles=contact['triangle_count'],
        encoded_contact_max_error_cm=error,contact_tolerance_cm=.01,
        maximum_native_inflow_face_error_m3s=source_error,unresolved_signed_boundary_flux_m3s=residual,
        minimum_source_clearance_cm=float((source_positions[:,2]-source_bed).min()),
        dry_native_false_volume_excluded_m3=seeds['dry_terrain_interpolation_false_volume_excluded_m3'],
        computational_cells=cells.tolist(),uniform_reconstruction_cells=render_cells.tolist(),
        uniform_reconstruction_voxels=int(np.prod(render_cells)),
        existing_reconstruction_cell_limit=2000000,
        uniform_reconstruction_exceeds_current_limit=bool(np.prod(render_cells)>2000000),
        one_rgba16f_volume_bytes=int(np.prod(render_cells)*8),
        capacity_estimate_not_gpu_measurement=True,engine_3d_coupled=False,physical_or_visual_acceptance=False,
        source_sha256={p.name:sha(p) for p in directory.iterdir() if p.is_file()})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=audit(args.directory)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
    raise SystemExit(0 if result['prepared_data_verified'] else 1)
