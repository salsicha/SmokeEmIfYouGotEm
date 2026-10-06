"""Isolated lower-ground interpretation; preserve unaffected source triangles."""
import json
import numpy as np
from scipy.spatial import Delaunay
from shapely import union_all
from shapely.geometry import Polygon, Point
from build_troublemaker_dem_rock_cap import ROOT, RETURNS, RETURNS_SHA, ORIGIN, close_cap_below_retained_terrain
from build_troublemaker_source_connected_cap import recover_segment, separate_vertex_fans
from south_fork_rock_union import sha


def edges(faces):
    return {tuple(sorted(map(int,e))) for t in faces for e in (t[[0,1]],t[[1,2]],t[[2,0]])}


def replace_cavity(vertices, faces, upper, lower, maximum_edge=1.):
    """Rebuild affected faces with exact coordinates; reject holes at shared seams."""
    polygons=[Polygon(t) for t in vertices[faces,:2]]
    removed=np.any(faces==upper,axis=1)|np.array([p.covers(Point(lower[:2])) for p in polygons])
    region=union_all([p for p,take in zip(polygons,removed) if take])
    if region.geom_type!='Polygon':raise ValueError('Disconnected cavity')
    kept=faces[~removed]
    boundary=edges(kept)&edges(faces[removed])
    ids=np.array(sorted(set(faces[removed].ravel())-{upper}),dtype=int)
    existing=np.flatnonzero(np.all(vertices[ids]==lower,axis=1))
    lower_local=int(existing[0]) if len(existing) else len(ids)
    points=vertices[ids].copy() if len(existing) else np.vstack([vertices[ids],lower])
    if len(np.unique(points[:,:2],axis=0))!=len(points):raise ValueError('Duplicate local XY')
    patch=Delaunay(points[:,:2]).simplices.copy()
    lookup={int(old):new for new,old in enumerate(ids)}
    for a,b in sorted(boundary):
        patch=recover_segment(points,patch,lookup[a],lookup[b])
    patch=np.array([t for t in patch if region.covers(Polygon(points[t,:2]))],dtype=int).reshape(-1,3)
    if not len(patch) or lower_local not in patch:raise ValueError('Lower witness not connected')
    xyz=points[patch];normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    patch[normals[:,2]<0]=patch[normals[:,2]<0][:,[0,2,1]]
    if (normals[:,2]==0).any():raise ValueError('Degenerate patch')
    longest=float(np.linalg.norm(xyz[:,:,:2]-np.roll(xyz[:,:,:2],1,axis=1),axis=2).max())
    if longest>maximum_edge:raise ValueError(f'Unsupported patch edge {longest:.9f}m')
    remap=ids if len(existing) else np.r_[ids,len(vertices)];added=remap[patch]
    if not boundary.issubset(edges(added)):raise ValueError('Lost retained seam')
    combined=np.vstack([kept,added]);result=vertices.copy() if len(existing) else np.vstack([vertices,lower])
    return result,combined,dict(removed_faces=int(removed.sum()),added_faces=len(added),
        maximum_edge_m=longest,lower_already_in_roof=bool(len(existing)),retained_faces_exact=bool(np.array_equal(result[combined[:len(kept)]],vertices[kept])),
        interpreted_footprint_loss_m2=float(region.area-union_all([Polygon(t) for t in result[added,:2]]).area))


def main():
    output=ROOT/'tmp/boundary-ground-cavities-v2-20260925'
    if output.exists():raise ValueError('Fresh output required')
    context=json.loads((ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/boundary-ground-context.json').read_text())
    path=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925/mixed_survey_rock_cap.npz'
    if sha(path)!=context['cap_sha256'] or sha(RETURNS)!=RETURNS_SHA:raise ValueError('Source changed')
    with np.load(path) as d:cap={k:d[k].copy() for k in d.files}
    vertices,faces=cap['vertices_m'],cap['triangles']
    rows=[];output.mkdir()
    with np.load(RETURNS) as raw:
        for target in context['targets']:
            index=target['source_index'];point=np.array([raw[k][index] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-ORIGIN
            if not np.array_equal(point,target['source_xyz_m']) or raw['classification'][index]!=2:raise ValueError('Witness mismatch')
            row=dict(source_index=index,excluded_upper_source_index=target['upper_source_index'])
            try:
                v,f,stats=replace_cavity(vertices,faces,target['vertex'],point)
                v,f,mapping=separate_vertex_fans(v,f)
                solid,triangles,kinds,closed=close_cap_below_retained_terrain(v,f,float(cap['solid_vertices_m'][:,2].min()))
                candidate=output/(str(index)+'.npz')
                np.savez_compressed(candidate,vertices_m=v,triangles=f,solid_vertices_m=solid,
                    solid_triangles=triangles,solid_face_kind=kinds,source_dataset=cap['source_dataset'][mapping],
                    source_point_index=cap['source_point_index'][mapping],source_classification=cap['source_classification'][mapping])
                row.update(passed=True,construction=stats,closure=closed,candidate_path=candidate.relative_to(ROOT).as_posix(),candidate_sha256=sha(candidate))
            except ValueError as error:row.update(passed=False,reason=str(error))
            rows.append(row)
    report=dict(parent_sha256=sha(path),source_sha256=RETURNS_SHA,independent_local_hypotheses=rows,
        interpretation='Ground-supported lower-layer hypothesis, not certified rock classification. Upper raw observations retained.',
        geometry_installed=False,acceptance=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
