"""Exact source-space probes for a transient full-map rock/terrain union."""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import SourceRockUnion,sha
from south_fork_registered_mesh import RegisteredMeshSampler
from build_troublemaker_dem_rock_cap import native_collision_probes
from build_troublemaker_dem_rock_cap import sample_cap

ROOT=Path(__file__).resolve().parents[2]


def engine_position(utm_xy,height_navd88,world_origin,datum):
    return [float((utm_xy[0]-world_origin[0])*100),
            float(-(utm_xy[1]-world_origin[1])*100),float((height_navd88-datum)*100)]


def physical_union_samples(union,xy,parent):
    """Rock ownership is relative to the revised bed, not the old height."""
    xy=np.asarray(xy,float);parent=np.asarray(parent,float)
    after,_=union.apply(xy[:,0],xy[:,1],parent)
    bed=parent
    if union.terrain_revision is not None:
        bed,_=union.terrain_revision.apply(xy[:,0],xy[:,1],parent)
    rock=np.zeros(len(xy),bool)
    low=union.xyz[:,:2].min(axis=0)+union.origin[:2]
    high=union.xyz[:,:2].max(axis=0)+union.origin[:2]
    ids=np.flatnonzero(np.all(xy>=low,axis=1)&np.all(xy<=high,axis=1))
    if len(ids):
        roof=sample_cap(union.xyz,union.faces,xy[ids]-union.origin[:2])+union.origin[2]
        rock[ids]=np.isfinite(roof)&(roof>bed[ids])
    return after,rock


def revision_triangle_probes(union,world_origin,datum):
    revision=union.terrain_revision
    if revision is None:return [],[]
    old,new=revision.original,revision.revised
    changed=old.xyz[:,2]!=new.xyz[:,2]
    ids=np.flatnonzero(np.any(changed[old.faces],axis=1))
    xy=old.xyz[old.faces[ids],:2].mean(axis=1)+revision.origin
    # Round-trip the absolute frame exactly as the shared union does.
    before=old.sample(*(xy-revision.origin).T)+revision.datum
    after,rock=physical_union_samples(union,xy,before)
    baseline=[];combined=[]
    for i,face in enumerate(ids):
        baseline.append(dict(kind='original_changed_triangle_centroid',source_triangle_index=int(face),
            world_position_cm=engine_position(xy[i],before[i],world_origin,datum)))
        combined.append(dict(kind='revised_triangle_union_centroid',source_triangle_index=int(face),
            world_position_cm=engine_position(xy[i],after[i],world_origin,datum),expected_candidate=bool(rock[i])))
    return baseline,combined


def visible_union_roof_probe(probe,parent_z,translation):
    """Trace the actual union, retaining the buried source target as evidence."""
    result=dict(probe)
    point=np.asarray(probe['world_position_cm'],float)
    parent_cm=float(parent_z)*100
    if parent_cm>=point[2]:
        result.update(kind='parent_covering_'+probe['kind'],
            retained_original_source_position_cm=point.tolist(),outward_normal=[0.,0.,1.],
            ray_half_length_cm=100.,expected_candidate=False)
        point=point.copy();point[2]=parent_cm
    else:
        result['expected_candidate']=True
    result['world_position_cm']=(point+translation).tolist()
    return result


def prepare(geometry_path,output,source_visible_probes=None):
    geometry_path=Path(geometry_path).resolve();output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp probe file required')
    geometry=json.loads(geometry_path.read_text());cap_path=ROOT/geometry['rock_cap_manifest']
    cap=json.loads(cap_path.read_text());origin=np.asarray(cap['origin_utm_and_vertical_datum_m'])
    revision=geometry.get('terrain_revision_manifest')
    union=SourceRockUnion(cap_path,ROOT,ROOT/cap['source_mesh_path'],origin[:2],origin[2],
                          ROOT/revision if revision else None)
    if union.identity!=geometry['terrain_union']:raise ValueError('Changed compound source identity')
    world_origin=np.asarray(geometry['world_origin_utm_m']);datum=geometry['vertical_datum_navd88_m']
    if datum!=origin[2]:raise ValueError('Geometry/engine datum mismatch')
    baseline=[];combined=[]
    for record in geometry['regions']:
        if not record.get('terrain_union'):continue
        paths=[ROOT/record['geometry_file'],ROOT/record['original_core_geometry_file']]
        if [sha(p) for p in paths]!=[record['geometry_sha256'],record['original_core_geometry_sha256']]:
            raise ValueError('Changed hydraulic reference core')
        with np.load(paths[0],allow_pickle=False) as a,np.load(paths[1],allow_pickle=False) as b:
            x0,y0=np.asarray(record['center_utm_m'])-40
            x,y=np.meshgrid(x0+np.arange(80),y0+np.arange(80))
            expected,rock=physical_union_samples(union,np.column_stack((x.ravel(),y.ravel())),b['bed_navd88_m'].ravel())
            if not np.array_equal(expected.reshape(80,80),a['bed_navd88_m']):
                raise ValueError('Collision probes differ from exact hydraulic union')
            for row in range(80):
                for col in range(80):
                    xy=[x0+col,y0+row]
                    before=engine_position(xy,b['bed_navd88_m'][row,col],world_origin,datum)
                    after=engine_position(xy,a['bed_navd88_m'][row,col],world_origin,datum)
                    baseline.append(dict(kind='retained_hydraulic_cell',world_position_cm=before))
                    combined.append(dict(kind='union_hydraulic_cell',world_position_cm=after,
                        expected_candidate=bool(rock[row*80+col])))
    original_faces,revised_faces=revision_triangle_probes(union,world_origin,datum)
    baseline.extend(original_faces);combined.extend(revised_faces)
    with np.load(ROOT/cap['cap_path'],allow_pickle=False) as data:
        native=native_collision_probes(data['vertices_m'],data['triangles'],data['solid_vertices_m'],
            data['solid_triangles'],data['solid_face_kind'],cap['cap_sha256'])
        translation=np.array(engine_position(origin[:2],origin[2],world_origin,datum))
        with np.load(ROOT/cap['source_mesh_path'],allow_pickle=False) as parent:
            sampler=RegisteredMeshSampler({key:parent[key] for key in parent.files})
        if union.terrain_revision is not None:sampler=union.terrain_revision.revised
        if source_visible_probes is None:
            roof_probes=[p for p in native['probes'] if p['kind'] in ('original_vertex_interior_cone','roof_triangle_centroid')]
        else:
            source_visible_probes=Path(source_visible_probes).resolve()
            extra=json.loads(source_visible_probes.read_text())
            if extra['source_cap_sha256']!=cap['cap_sha256'] or extra['source_cap_manifest_sha256']!=sha(cap_path):
                raise ValueError('Source-visible probes belong to different geometry')
            vertices=[p for p in extra['probes'] if p['kind']=='original_vertex_source_visible_cone']
            if [p['source_vertex_index'] for p in vertices]!=list(range(len(data['vertices_m']))) or not np.array_equal(
                    [p['world_position_cm'] for p in vertices],data['vertices_m']*[100,-100,100]):
                raise ValueError('Every exact original vertex must have a source-visible probe')
            roof_probes=vertices+[p for p in native['probes'] if p['kind']=='roof_triangle_centroid']
        for probe in roof_probes:
            point=np.asarray(probe['world_position_cm'])/[100,-100,100]
            parent_z=float(sampler.sample(point[0],point[1]))
            combined.append(visible_union_roof_probe(probe,parent_z,translation))
        for ia,ib in data['boundary_edges']:
            a,b=data['vertices_m'][[ia,ib]];mid=(a+b)*.5
            parent_z=float(sampler.sample(mid[0],mid[1]))
            if parent_z>=mid[2]:
                combined.append(dict(kind='parent_covering_union_boundary_midpoint',
                    retained_original_source_position_cm=(mid*[100,-100,100]).tolist(),
                    world_position_cm=(np.r_[mid[:2],parent_z]*[100,-100,100]+translation).tolist(),
                    outward_normal=[0.,0.,1.],ray_half_length_cm=100.,expected_candidate=False))
                continue
            # Orient away from the incident roof triangle, independent of
            # the boundary-edge array's undirected index ordering.
            faces=data['triangles'];incident=faces[np.any(faces==ia,axis=1)&np.any(faces==ib,axis=1)]
            if len(incident)!=1:raise ValueError('Ambiguous source perimeter')
            interior=data['vertices_m'][incident[0]].mean(axis=0)
            delta=b-a;n=np.array([delta[1],-delta[0],0.]);n/=np.linalg.norm(n)
            if np.dot(n[:2],interior[:2]-mid[:2])>0:n=-n
            mid[2]=(mid[2]+parent_z)*.5
            combined.append(dict(kind='exposed_union_flank_midpoint',
                world_position_cm=(mid*[100,-100,100]+translation).tolist(),
                outward_normal=(n*[1,-1,1]).tolist(),ray_half_length_cm=1.,expected_candidate=True))
    result=dict(schema='raftsim.full_map_rock_union_probes.v1',geometry_manifest=geometry_path.relative_to(ROOT).as_posix(),
        geometry_manifest_sha256=sha(geometry_path),cap_manifest_sha256=sha(cap_path),
        source_cap_sha256=cap['cap_sha256'],parent_mesh_sha256=cap['source_mesh_sha256'],
        translation_cm=translation.tolist(),world_origin_utm_m=world_origin.tolist(),datum_m=datum,
        baseline=baseline,combined=combined,prior_vertical_tangent_gate_closed=False)
    if union.terrain_revision is not None:
        old=union.terrain_revision.original.xyz;new=union.terrain_revision.revised.xyz
        changed=np.flatnonzero(old[:,2]!=new[:,2])
        result.update(terrain_revision=union.terrain_revision.identity,
            terrain_replacement_required=True,changed_triangle_probe_count=len(revised_faces),
            terrain_vertex_changes_cm=[dict(source_vertex_index=int(i),before=(old[i]*100).tolist(),
                after=(new[i]*100).tolist()) for i in changed])
    if source_visible_probes is not None:
        result.update(source_visible_probe_file=source_visible_probes.relative_to(ROOT).as_posix(),
            source_visible_probe_sha256=sha(source_visible_probes),
            every_roof_vertex_and_centroid_represents_physical_union=True,
            covered_roof_targets_preserved_in_probe_metadata=True,
            legacy_isolated_probe_failures_waived=False)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k not in ('baseline','combined','terrain_vertex_changes_cm')}|dict(baseline_count=len(baseline),combined_count=len(combined))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('geometry',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-visible-probes',type=Path);args=parser.parse_args()
    print(json.dumps(prepare(args.geometry,args.output,args.source_visible_probes),indent=2),flush=True)
