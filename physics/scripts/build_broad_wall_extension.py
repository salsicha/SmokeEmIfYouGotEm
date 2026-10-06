"""Source-exact, edge-connected exterior extension; isolated hypothesis only."""
import json
import argparse
import sys
import numpy as np
from scipy.spatial import Delaunay
from shapely import union_all
from shapely.geometry import Polygon,Point
from build_troublemaker_dem_rock_cap import ROOT,PARENT,PARENT_SHA,close_cap_below_retained_terrain,ORIGIN
from build_troublemaker_source_connected_cap import separate_vertex_fans, constrained_extension
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import sha


def connected_extensions(old, candidates):
    edges=lambda t:{tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for i in range(3)}
    reached=set().union(*(edges(t) for t in old))
    pending=list(range(len(candidates)));chosen=[]
    while pending:
        accepted=[i for i in pending if edges(candidates[i]) & reached]
        if not accepted:break
        for i in accepted:reached.update(edges(candidates[i]))
        chosen.extend(accepted);pending=[i for i in pending if i not in accepted]
    return candidates[sorted(chosen)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--constrained-boundary',action='store_true')
    constrained=parser.parse_args().constrained_boundary
    output=ROOT/('tmp/troublemaker-constrained-wall-extension-v1-20260925' if constrained else 'tmp/troublemaker-broad-wall-extension-v1-20260925')
    if output.exists():raise ValueError('Fresh output required')
    source=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/mixed_survey_rock_cap.npz'
    audit_path=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/diagnosed-wall-support-connectivity.json'
    audit=json.loads(audit_path.read_text())
    if sha(source)!=audit['cap_sha256'] or sha(PARENT)!=PARENT_SHA:raise ValueError('Source changed')
    with np.load(source) as data:cap={k:data[k].copy() for k in data.files}
    v,f=cap['vertices_m'],cap['triangles']
    footprint=union_all([Polygon(t) for t in v[f,:2]])
    pool={p['index']:p for w in audit['walls'] for p in w['independent_points'] if p['classification']==2 and not p['withheld'] and not footprint.covers(Point(p['xyz_m'][:2]))}
    ids=sorted(pool); points=np.array([pool[i]['xyz_m'] for i in ids])
    import laspy
    from pyproj import Transformer
    laz=ROOT/'tmp/troublemaker-independent-lidar-20260925/USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz'
    if sha(laz)!=audit['independent_sha256']:raise ValueError('Independent source changed')
    transform=Transformer.from_crs(6339,32610,always_xy=True)
    with laspy.open(laz) as reader:
        if [c.to_epsg() for c in reader.header.parse_crs().sub_crs_list]!=[6339,5703]:raise ValueError('CRS changed')
        for i,index in enumerate(ids):
            reader.seek(index);raw=reader.read_points(1)
            x,y=transform.transform(float(raw.x[0]),float(raw.y[0]))
            if not np.array_equal(np.array([x,y,float(raw.z[0])])-ORIGIN,points[i]) or int(np.asarray(raw.classification)[0])!=2 or int(np.asarray(raw.withheld)[0]):raise ValueError('Point identity mismatch')
    vertices=np.vstack([v,points])
    if constrained:
        triangles=constrained_extension(vertices,f,maximum_edge_m=1.)[len(f):]
    else:
        triangles=Delaunay(vertices[:,:2]).simplices
        triangles=triangles[np.any(triangles>=len(v),axis=1)]
        triangles=triangles[np.linalg.norm(vertices[triangles,:2]-np.roll(vertices[triangles,:2],1,axis=1),axis=2).max(axis=1)<=1.]
        triangles=np.array([t for t in triangles if Polygon(vertices[t,:2]).intersection(footprint).area<=1e-9])
    possible=len(triangles);triangles=connected_extensions(f,triangles)
    if not len(triangles):raise ValueError('No edge-connected extension')
    patch=union_all([Polygon(t) for t in vertices[triangles,:2]])
    if abs(patch.area-sum(Polygon(t).area for t in vertices[triangles,:2]))>1e-9:raise ValueError('Overlapping additions')
    faces=np.vstack([f,triangles]);used=np.unique(faces);remap=np.full(len(vertices),-1);remap[used]=np.arange(len(used))
    vertices,faces,mapping=separate_vertex_fans(vertices[used],remap[faces]);mapping=used[mapping]
    if not np.array_equal(vertices[faces[:len(f)]],v[f]):raise ValueError('Original roof changed')
    solid,solid_faces,kinds,closure=close_cap_below_retained_terrain(vertices,faces,float(cap['solid_vertices_m'][:,2].min()))
    with np.load(PARENT) as terrain:heights=RegisteredMeshSampler(terrain).sample(vertices[:,0],vertices[:,1])
    if not np.isfinite(heights).all():raise ValueError('Missing retained ground')
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);_,first,count=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True)
    output.mkdir();path=output/'mixed_survey_rock_cap.npz'
    np.savez_compressed(path,vertices_m=vertices,triangles=faces,solid_vertices_m=solid,solid_triangles=solid_faces,solid_face_kind=kinds,
        boundary_edges=edges[first[count==1]],retained_parent_height_m=heights,
        source_dataset=np.r_[cap['source_dataset'],np.ones(len(ids),dtype=np.uint8)][mapping],
        source_point_index=np.r_[cap['source_point_index'],ids][mapping],
        source_classification=np.r_[cap['source_classification'],np.full(len(ids),2,dtype=np.uint8)][mapping],
        bin_support_count=np.r_[cap['bin_support_count'],np.zeros(len(ids),dtype=int)][mapping])
    sys.path.insert(0,str(ROOT/'unreal/Scripts'))
    from audit_terrain_camera_sources import resolve_ray
    rays_path=ROOT/'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/source-rays.json';rays=json.loads(rays_path.read_text())
    ground_path=ROOT/rays['source_identities']['ground']['path']
    if sha(ground_path)!=rays['source_identities']['ground']['sha256']:raise ValueError('Ray ground changed')
    with np.load(ground_path) as g:sources={'ground':(np.column_stack([g[k].ravel() for k in ('east_m','north_m','z_m')]),g['triangles']),'cap':(solid,solid_faces)}
    ray_results=[]
    for probe in rays['probes']:
        if probe.get('source_hit',{}).get('solid_face_kind')!=2:continue
        hit=resolve_ray(probe['engine'],sources,rays['translation_cm'],rays['reflection'])
        ray_results.append(dict(pixel=probe['pixel'],hit=hit,face_kind=int(kinds[hit['source_triangle']]) if hit and hit['source']=='cap' else None))
    report=dict(schema='raftsim.interpreted_broad_wall_extension.v1',parent_cap_sha256=sha(source),cap_sha256=sha(path),
        preserved_boundary_constraints=constrained,
        support_audit_sha256=sha(audit_path),independent_sha256=audit['independent_sha256'],retained_rays_sha256=sha(rays_path),
        exterior_point_indices=ids,used_added_point_indices=sorted(set(int(i) for i in np.r_[cap['source_point_index'],ids][mapping[mapping>=len(v)]])),
        possible_triangles=possible,added_triangles=len(triangles),added_area_m2=patch.area,fan_split_vertices=len(mapping)-len(used),
        original_roof_exact=True,closure=closure,diagnosed_wall_rays=ray_results,playable_integrated=False,
        limits='Source-exact coordinates, interpreted adjacency and class2 ground selection, not certified rock. Same <=1m XY edge bound; no fitted vertical offset; 2m declared transform accuracy. Outer closure still inferred; no engine/cook acceptance.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('added_triangles','added_area_m2','fan_split_vertices','closure','diagnosed_wall_rays')},indent=2))


if __name__=='__main__':main()
