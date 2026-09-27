"""Probe the inferred envelope plus revised ground, without retaining the old roof."""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import sha
from prepare_south_fork_rock_union_geometry import retained_union
from prepare_south_fork_union_collision import engine_position
from build_troublemaker_dem_rock_cap import sample_cap
from source_native_triangle_hash import triangle_hash

ROOT=Path(__file__).resolve().parents[2]


def union_heights(sampler, roof, faces, xy):
    xy=np.asarray(xy,float)
    ground=sampler.sample(*xy.T)
    active=np.full(len(xy),np.nan)
    ids=np.flatnonzero(np.all(xy>=roof[:,:2].min(0),axis=1)&np.all(xy<=roof[:,:2].max(0),axis=1))
    if len(ids):active[ids]=sample_cap(roof,faces,xy[ids])
    rock=np.isfinite(active)&(active>ground)
    return np.where(rock,active,ground),rock


def flank_probes(sampler,roof,faces,edges,translation):
    result=[]
    for ia,ib in edges:
        a,b=roof[[ia,ib]];mid=(a+b)*.5
        ground=float(sampler.sample(mid[0],mid[1]))
        if ground>=mid[2]:
            mid[2]=ground
            normal=np.array([0.,0.,1.]);kind='covered_boundary';distance=1000.;rock=False
        else:
            incident=faces[np.any(faces==ia,axis=1)&np.any(faces==ib,axis=1)]
            if len(incident)!=1:raise ValueError('Ambiguous envelope boundary')
            interior=roof[incident[0]].mean(0)
            delta=b-a;normal=np.array([delta[1],-delta[0],0.]);normal/=np.linalg.norm(normal)
            if np.dot(normal[:2],interior[:2]-mid[:2])>0:normal=-normal
            mid[2]=(mid[2]+ground)*.5
            kind='exposed_inferred_flank';distance=1.;rock=True
        result.append(dict(kind=kind,world_position_cm=(mid*[100,-100,100]+translation).tolist(),
            outward_normal=(normal*[1,-1,1]).tolist(),ray_half_length_cm=distance,expected_rock=rock))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--ground-native',type=Path,required=True)
    p.add_argument('--envelope-install',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();deps={}
    if out.exists() or not out.is_relative_to(ROOT/'tmp'):raise ValueError('Fresh tmp output required')
    def add(path):
        path=Path(path).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Project dependency required')
        deps[path.relative_to(ROOT).as_posix()]=sha(path)
        return path
    gp=add(a.geometry);geometry=json.loads(gp.read_text())
    union=retained_union(geometry,ROOT)
    if union is None or 'interpreted_envelope' not in union.identity or union.terrain_revision is None:
        raise ValueError('Explicit revised ground and inferred envelope required')
    sampler=union.terrain_revision.revised;roof=union.xyz;faces=union.faces
    origin=union.origin[:2];datum=union.origin[2];world=geometry['world_origin_utm_m']
    translation=np.array(engine_position(origin,datum,world,datum))
    native=json.loads(add(a.ground_native).read_text())
    if not native['passed'] or not native['saved_candidate_mesh'] or not native['normal_scene_unchanged']:
        raise ValueError('Previously verified candidate ground required')
    preflight_path=add(ROOT/native['preflight'])
    if sha(preflight_path)!=native['preflight_sha256']:raise ValueError('Ground preflight changed')
    preflight=json.loads(preflight_path.read_text())
    for name,digest in preflight['dependencies'].items():
        if sha(add(ROOT/name))!=digest:raise ValueError('Ground dependency changed')
    revision=json.loads(add(ROOT/geometry['terrain_revision_manifest']).read_text())
    if revision['mesh_sha256']!=native['source_mesh_sha256']:raise ValueError('Cook and native ground differ')
    envelope=union.identity['interpreted_envelope']
    descriptor=json.loads(add(ROOT/envelope['descriptor']).read_text())
    for key in ('source_cap_manifest','envelope_file','build_receipt'):
        if sha(add(ROOT/descriptor[key]))!=descriptor[key+'_sha256']:raise ValueError('Envelope dependency changed')
    installed=json.loads(add(a.envelope_install).read_text())
    if installed['envelope_sha256']!=envelope['envelope_sha256']:raise ValueError('Installed envelope differs')
    with np.load(ROOT/descriptor['envelope_file'],allow_pickle=False) as data:
        rock_hash=triangle_hash(data['solid_vertices_m']*100,data['solid_triangles'][:,[0,2,1]])
        rock_count=len(data['solid_triangles'])
    cap=json.loads((ROOT/geometry['rock_cap_manifest']).read_text())
    with np.load(add(ROOT/cap['cap_path']),allow_pickle=False) as data:edges=data['boundary_edges'].copy()
    rows=[]
    def vertical(kind,xy,expected=None):
        z,rock=union_heights(sampler,roof,faces,xy)
        if expected is not None and not np.allclose(z+datum,expected,atol=1e-8,rtol=0):
            raise ValueError('Hydraulic bed differs from independently sampled union')
        for point,height,owner in zip(xy,z,rock):
            rows.append(dict(kind=kind,world_position_cm=engine_position(point+origin,height+datum,world,datum),
                expected_rock=bool(owner)))
    # Previously ground-only probes now include all possible rock/ground occlusion.
    vertical('changed_ground_triangle_union',np.asarray(preflight['ground_triangle_centroids_cm'])[:,:2]/100)
    vertical('inferred_roof_triangle_union',roof[faces].mean(1)[:,:2])
    hydraulic=0
    low,high=roof[:,:2].min(0)+origin,roof[:,:2].max(0)+origin
    for record in geometry['regions']:
        center=np.asarray(record['center_utm_m'])
        if np.any(center-40>high) or np.any(center+39<low):continue
        path=add(ROOT/record['geometry_file'])
        if sha(path)!=record['geometry_sha256']:raise ValueError('Hydraulic geometry changed')
        x,y=np.meshgrid(center[0]+np.arange(80)-40,center[1]+np.arange(80)-40)
        xy=np.column_stack((x.ravel(),y.ravel()))-origin
        ids=np.flatnonzero(np.isfinite(sample_cap(roof,faces,xy)))
        with np.load(path,allow_pickle=False) as data:
            vertical('hydraulic_envelope_cell',xy[ids],data['bed_navd88_m'].ravel()[ids])
        hydraulic+=len(ids)
    if not hydraulic:raise ValueError('No hydraulic-envelope overlap')
    rows.extend(flank_probes(sampler,roof,faces,edges,translation))
    mesh_rows=dict(
        ground_before=dict(asset=native['original_asset'],package_sha256=preflight['baseline_package_sha256'],
                           native_sha256=native['original_native_source']['collision_source_sha256'],triangle_count=preflight['triangle_count']),
        ground_candidate=dict(asset=native['mesh_asset'],package_sha256=native['candidate_package_sha256'],
                              native_sha256=native['revised_native_source']['collision_source_sha256'],triangle_count=preflight['triangle_count']),
        rock=dict(asset=installed['new_mesh'],package_sha256=installed['new_mesh_sha256'],
                  native_sha256=rock_hash,triangle_count=rock_count))
    for row in mesh_rows.values():
        path=add(ROOT/'unreal/Content'/(row['asset'][6:]+'.uasset'))
        if sha(path)!=row['package_sha256']:raise ValueError('Native package changed')
    result=dict(schema='raftsim.envelope_union_native_probes.v1',dependencies=deps,rows=rows,meshes=mesh_rows,
        ground_actor=native['original_actor'],rock_actor=installed['rock_actor'],translation_cm=translation.tolist(),
        geometry_manifest=gp.relative_to(ROOT).as_posix(),geometry_manifest_sha256=sha(gp),
        groups={kind:sum(r['kind']==kind for r in rows) for kind in sorted({r['kind'] for r in rows})},
        source_returns_unchanged=True,faces_measured=False,normal_map_integrated=False,
        limitation='Native mesh identity and enumerated ray probes; not complete continuous surface, motion or performance acceptance.')
    for name,digest in deps.items():
        if sha(ROOT/name)!=digest:raise ValueError('Dependency changed during preparation')
    with out.open('x') as f:json.dump(result,f,separators=(',',':'),allow_nan=False)
    print(json.dumps(dict(output=str(out),sha256=sha(out),groups=result['groups'])),flush=True)


if __name__=='__main__':main()
