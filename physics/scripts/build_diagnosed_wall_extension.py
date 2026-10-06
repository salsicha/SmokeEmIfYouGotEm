"""Bounded mixed-source roof extension; not a surveyed flank or runtime bundle."""
import json
import numpy as np
import laspy
from pyproj import Transformer
from shapely import union_all
from shapely.geometry import Polygon
from build_troublemaker_dem_rock_cap import ROOT, ORIGIN, PARENT, PARENT_SHA, close_cap_below_retained_terrain
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import sha


def append_patch(vertices, faces, edges, points):
    """Append exterior triangles without moving any existing source coordinates."""
    vertices=np.asarray(vertices,float);faces=np.asarray(faces,dtype=np.int64)
    edges=np.asarray(edges,dtype=np.int64);points=np.asarray(points,float)
    if points.shape!=(len(edges),3) or not np.isfinite(points).all():raise ValueError('Finite source additions required')
    boundary=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    unique,counts=np.unique(np.sort(boundary,axis=1),axis=0,return_counts=True)
    valid={tuple(e) for e in unique[counts==1]}
    footprint=union_all([Polygon(p) for p in vertices[faces,:2]])
    result=np.concatenate([vertices,points]);added=[];patches=[]
    for i,(a,b) in enumerate(edges):
        if tuple(sorted((int(a),int(b)))) not in valid:raise ValueError('Not a boundary edge')
        f=np.array([a,b,len(vertices)+i])
        p=result[f];area=np.cross(p[1]-p[0],p[2]-p[0])[2]
        if abs(area)<=1e-10:raise ValueError('Degenerate addition')
        if area<0:f=f[[1,0,2]]
        if np.linalg.norm(p[:,:2]-np.roll(p[:,:2],1,axis=0),axis=1).max()>1.:raise ValueError('One metre edge limit exceeded')
        polygon=Polygon(p[:,:2])
        if polygon.intersection(footprint).area>1e-9 or any(polygon.intersection(q).area>1e-9 for q in patches):raise ValueError('Patch overlap')
        patches.append(polygon);added.append(f)
    all_faces=np.concatenate([faces,np.array(added)])
    if not np.array_equal(result[all_faces[:len(faces)]],vertices[faces]):raise ValueError('Existing roof changed')
    return result,all_faces,float(sum(p.area for p in patches))


def main():
    source=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/mixed_survey_rock_cap.npz'
    expected='2ce993c54e489cf42a9773f5b8f34def310586f9b785c03325af0477033ae4b6'
    audit_path=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/diagnosed-wall-support-connectivity.json'
    rays_path=ROOT/'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/source-rays.json'
    output=ROOT/'tmp/troublemaker-wall-extension-v1-20260925'
    if output.exists():raise ValueError('Fresh output required')
    audit=json.loads(audit_path.read_text());rays=json.loads(rays_path.read_text())
    laz=ROOT/'tmp/troublemaker-independent-lidar-20260925/USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz'
    if sha(source)!=expected or sha(PARENT)!=PARENT_SHA or sha(laz)!=audit['independent_sha256'] or sha(rays_path)!=audit['source_rays_sha256']:raise ValueError('Source identity mismatch')
    with np.load(source) as data:cap={k:data[k].copy() for k in data.files}
    edges=[];points=[];selection=[]
    transform=Transformer.from_crs(6339,32610,always_xy=True)
    with laspy.open(laz) as reader:
        if [c.to_epsg() for c in reader.header.parse_crs().sub_crs_list]!=[6339,5703]:raise ValueError('CRS changed')
        for wall in audit['walls']:
            options=[p for p in wall['ground_connection_candidates'] if p['local_geometric_extension_eligible']]
            if not options:continue
            # Minimize new connection span, never select by preferred height/slope.
            chosen=min(options,key=lambda p:(p['maximum_new_edge_m'],p['index']))
            reader.seek(chosen['index']);raw=reader.read_points(1)
            if len(raw)!=1 or int(np.asarray(raw.withheld)[0]) or int(np.asarray(raw.classification)[0])!=2:raise ValueError('Unusable support observation')
            east,north=transform.transform(float(raw.x[0]),float(raw.y[0]))
            point=np.array([east,north,float(raw.z[0])])-ORIGIN
            recorded=next(p for p in wall['independent_points'] if p['index']==chosen['index'])
            if not np.array_equal(point,recorded['xyz_m']):raise ValueError('Point audit changed')
            hit=next(r['source_hit'] for r in rays['probes'] if r.get('source_hit',{}).get('source_triangle')==wall['old_face'])
            endpoint=np.array(hit['source_xyz_m'])[[0,2]]
            ids=[]
            for xyz in endpoint:
                matches=np.flatnonzero((cap['vertices_m']==xyz).all(axis=1))
                if len(matches)!=1:raise ValueError('Ambiguous wall endpoint')
                ids.append(int(matches[0]))
            edges.append(ids);points.append(point)
            selection.append(dict(old_wall=wall['old_face'],laz_point_index=chosen['index'],source_xyz_m=[float(raw.x[0]),float(raw.y[0]),float(raw.z[0])],local_xyz_m=point.tolist(),maximum_new_edge_m=chosen['maximum_new_edge_m']))
    if len(points)!=2:raise ValueError('Expected exactly two supported walls')
    vertices,faces,area=append_patch(cap['vertices_m'],cap['triangles'],edges,points)
    floor=float(cap['solid_vertices_m'][:,2].min())
    solid,solid_faces,kinds,closure=close_cap_below_retained_terrain(vertices,faces,floor)
    with np.load(PARENT) as terrain: heights=RegisteredMeshSampler(terrain).sample(vertices[:,0],vertices[:,1])
    if not np.isfinite(heights).all():raise ValueError('Missing parent support')
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    _,first,counts=np.unique(np.sort(directed,axis=1),axis=0,return_index=True,return_counts=True)
    output.mkdir()
    path=output/'mixed_survey_rock_cap.npz'
    np.savez_compressed(path,vertices_m=vertices,triangles=faces,solid_vertices_m=solid,solid_triangles=solid_faces,solid_face_kind=kinds,
        boundary_edges=directed[first[counts==1]],retained_parent_height_m=heights,
        source_dataset=np.r_[cap['source_dataset'],np.ones(2,dtype=np.uint8)],
        source_point_index=np.r_[cap['source_point_index'],[r['laz_point_index'] for r in selection]],
        source_classification=np.r_[cap['source_classification'],np.full(2,2,dtype=np.uint8)],
        bin_support_count=np.r_[cap['bin_support_count'],np.zeros(2,dtype=int)])
    report=dict(schema='raftsim.interpreted_wall_extension.v1',parent_cap_sha256=expected,cap_sha256=sha(path),cap_path=str(path.relative_to(ROOT)),
        support_audit_sha256=sha(audit_path),independent_sha256=audit['independent_sha256'],parent_terrain_sha256=PARENT_SHA,
        selected=selection,selection_rule='Minimum maximum new XY edge among non-withheld class2 exterior candidates, index tie-break; not height fitting',
        added_projected_area_m2=area,original_roof_exact=True,source_xyz_changed=False,closure=closure,
        source_dataset_table={'0':'2019 classified_lidar_returns.npz index','1':'2021 original LAZ point index'},
        transform_accuracy_m=transform.accuracy,vertical_adjustment_m=0.,
        flanks_measured=False,render_collision_verified=False,hydraulics_recooked=False,playable_integrated=False,
        limits='A local inferred connection using captured points, not a measured rock outline. New outer vertical closure remains inferred. Mixed epochs/geoid uncertainty retained. Not compatible with legacy runtime manifest until explicitly validated.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
