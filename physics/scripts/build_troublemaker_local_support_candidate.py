"""Bounded interpreted lower-support candidate; never installs game assets."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
from scipy.spatial import Delaunay
from shapely import union_all
from shapely.geometry import Polygon, Point
from build_troublemaker_dem_rock_cap import ORIGIN,RETURNS,RETURNS_SHA,PARENT,PARENT_SHA,close_cap_below_retained_terrain
from south_fork_registered_mesh import RegisteredMeshSampler

def main():
    path=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/source_matched_20260917/original_return_rock_cap.npz'
    output=ROOT/'tmp/troublemaker-local-support-candidate-20260925'
    if output.exists(): raise ValueError('Fresh candidate directory required')
    expected='78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb'
    for p,h in [(path,expected),(RETURNS,RETURNS_SHA),(PARENT,PARENT_SHA)]:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise ValueError('Source identity changed')
    with np.load(path) as data: cap={k:data[k].copy() for k in data.files}
    with np.load(RETURNS) as data: source={k:data[k].copy() for k in data.files}
    xyz=np.column_stack([source['utm_easting_m'],source['utm_northing_m'],source['navd88_m']])-ORIGIN
    removed_ids=np.array([686411,686654]); added_ids=np.array([685883,686116,686117,686330,686331,686332,686333])
    removed=np.flatnonzero(np.isin(cap['original_return_index'],removed_ids))
    if len(removed)!=2: raise ValueError('Unexpected patch identity')
    faces=cap['triangles']; v=cap['vertices_m']; patch=np.isin(faces,removed).any(axis=1)
    region=union_all([Polygon(v[t,:2]) for t in faces[patch]])
    edges=np.sort(np.concatenate([faces[patch][:,[0,1]],faces[patch][:,[1,2]],faces[patch][:,[2,0]]]),axis=1)
    edges,counts=np.unique(edges,axis=0,return_counts=True); boundary=edges[counts==1]
    boundary_ids=np.unique(boundary)
    local=np.concatenate([v[boundary_ids],xyz[added_ids]])
    if any(not region.covers(Point(p)) for p in local[:,:2]):
        raise ValueError('Candidate point outside patch')
    triangles=Delaunay(local[:,:2]).simplices
    triangles=triangles[np.array([region.covers(Polygon(local[t,:2])) for t in triangles])]
    area=union_all([Polygon(local[t,:2]) for t in triangles])
    if area.symmetric_difference(region).area>1e-10: raise ValueError('Patch coverage changed')
    lengths=np.linalg.norm(local[triangles,:2]-np.roll(local[triangles,:2],1,axis=1),axis=2)
    if lengths.max()>1:
        raise ValueError('Unsupported long patch edges: '+str([(local[t].tolist(),lengths[i].tolist()) for i,t in enumerate(triangles) if lengths[i].max()>1]))
    cross=np.cross(local[triangles[:,1]]-local[triangles[:,0]],local[triangles[:,2]]-local[triangles[:,0]])[:,2]
    triangles[cross<0]=triangles[cross<0][:,[0,2,1]]
    all_v=np.concatenate([v,xyz[added_ids]])
    local_map=np.r_[boundary_ids,np.arange(len(v),len(all_v))]
    all_f=np.concatenate([faces[~patch],local_map[triangles]])
    used=np.unique(all_f); remap=np.full(len(all_v),-1); remap[used]=np.arange(len(used))
    vertices=all_v[used]; new_faces=remap[all_f]
    if not np.array_equal(vertices[new_faces[:(~patch).sum()]],v[faces[~patch]]):
        raise ValueError('Outside triangles changed')
    original_ids=np.r_[cap['original_return_index'],added_ids][used]
    if not np.array_equal(vertices,xyz[original_ids]): raise ValueError('Measured coordinates changed')
    floor=float(cap['solid_vertices_m'][len(v):,2].min())
    solid,solid_faces,kinds,closure=close_cap_below_retained_terrain(vertices,new_faces,floor)
    with np.load(PARENT) as parent: parent_height=RegisteredMeshSampler(parent).sample(vertices[:,0],vertices[:,1])
    if not np.isfinite(parent_height).all(): raise ValueError('Missing parent terrain')
    all_edges=np.concatenate([new_faces[:,[0,1]],new_faces[:,[1,2]],new_faces[:,[2,0]]])
    _,first,n=np.unique(np.sort(all_edges,axis=1),axis=0,return_index=True,return_counts=True)
    output.mkdir()
    np.savez_compressed(output/'original_return_rock_cap.npz',vertices_m=vertices,triangles=new_faces,
        original_return_index=original_ids,original_classification=source['classification'][original_ids],
        original_height_above_dem_m=source['height_above_flattened_surface_m'][original_ids],
        retained_parent_height_m=parent_height,boundary_edges=all_edges[first[n==1]],
        bin_support_count=np.r_[cap['bin_support_count'],np.zeros(len(added_ids),dtype=int)][used],
        solid_vertices_m=solid,solid_triangles=solid_faces,solid_face_kind=kinds)
    report=dict(status='unpromoted_interpreted_local_lower_support_candidate',production_promoted=False,
        parent_cap_sha256=expected,original_returns_sha256=RETURNS_SHA,removed_source_ids=removed_ids.tolist(),
        added_source_ids=added_ids.tolist(),raw_source_deleted=False,source_xyz_changed=False,
        patch_area_m2=region.area,old_patch_faces=int(patch.sum()),new_patch_faces=len(triangles),
        outside_triangles_exact=True,patch_coverage_exact=True,closure=closure,
        selection='Two locally unsupported high roof anchors excluded from this interpretation; seven original lower observations inserted. No source reclassification. New bin counts zero mean explicit selection, not absence of returns.',
        limitations='Not verified rock identity or measured underwater flanks. Preserved boundary includes unresolved local relief. Shared bed/flow/collision and normal-play validation pending.',
        candidate_sha256=hashlib.sha256((output/'original_return_rock_cap.npz').read_bytes()).hexdigest())
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))

if __name__=='__main__': main()
