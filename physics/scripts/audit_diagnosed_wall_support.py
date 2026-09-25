"""Check captured support around diagnosed inferred walls; never fit a flank."""
import json
from pathlib import Path
import numpy as np
import laspy
from pyproj import Transformer
from shapely import union_all
from shapely.geometry import Polygon, Point
from build_troublemaker_dem_rock_cap import ROOT, RETURNS, RETURNS_SHA, ORIGIN
from south_fork_rock_union import sha


def main():
    rays_path=ROOT/'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/source-rays.json'
    rays=json.loads(rays_path.read_text())
    laz=ROOT/'tmp/troublemaker-independent-lidar-20260925/USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz'
    laz_sha='2261adeac1a3ea49cdeaaa038cbb8bba40b2c1ada7f15b0e42e98192957fd96e'
    output=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/diagnosed-wall-support-connectivity.json'
    if output.exists():raise ValueError('Fresh output required')
    if sha(RETURNS)!=RETURNS_SHA or sha(laz)!=laz_sha:raise ValueError('Source identity changed')
    walls=[r for r in rays['probes'] if r.get('source_hit',{}).get('solid_face_kind')==2]
    targets=np.array([r['source_hit']['local_hit_m'] for r in walls])
    if len(targets)!=4:raise ValueError('Expected four diagnosed walls')
    cap_path=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/mixed_survey_rock_cap.npz'
    cap_sha='2ce993c54e489cf42a9773f5b8f34def310586f9b785c03325af0477033ae4b6'
    if sha(cap_path)!=cap_sha:raise ValueError('Mixed cap identity mismatch')
    with np.load(cap_path) as cap:
        footprint=union_all([Polygon(t) for t in cap['vertices_m'][cap['triangles'],:2]])
    with np.load(RETURNS) as old:
        xyz=np.column_stack([old[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-ORIGIN
        cls=old['classification'].copy()
    rows=[dict(pixel=r['pixel'],old_face=r['source_hit']['source_triangle'],
               target_local_m=targets[i].tolist(),independent_points=[]) for i,r in enumerate(walls)]
    transform=Transformer.from_crs(6339,32610,always_xy=True)
    offset=0
    with laspy.open(laz) as reader:
        crs=reader.header.parse_crs()
        if not crs.is_compound or [c.to_epsg() for c in crs.sub_crs_list]!=[6339,5703]:raise ValueError('CRS mismatch')
        for points in reader.chunk_iterator(500000):
            x,y=transform.transform(np.asarray(points.x),np.asarray(points.y))
            p=np.column_stack([x,y,np.asarray(points.z)])-ORIGIN
            fields={k:np.asarray(getattr(points,k)) for k in ('classification','withheld','return_number','number_of_returns')}
            for i,target in enumerate(targets):
                ids=np.flatnonzero(np.linalg.norm(p[:,:2]-target[:2],axis=1)<=1.5)
                for j in ids:
                    rows[i]['independent_points'].append(dict(index=int(offset+j),xyz_m=p[j].tolist(),
                        **{k:int(v[j]) for k,v in fields.items()}))
            offset+=len(points)
        if offset!=reader.header.point_count:raise ValueError('Incomplete cloud')
    for i,row in enumerate(rows):
        endpoints=np.array(walls[i]['source_hit']['source_xyz_m'])[[0,2],:2]
        row['ground_connection_candidates']=[]
        for p in row['independent_points']:
            if p['classification']!=2 or p['withheld']:continue
            point=np.array(p['xyz_m'])[:2]
            triangle=Polygon(np.vstack([endpoints,point]))
            maximum_edge=float(np.linalg.norm(endpoints-point,axis=1).max())
            overlap=triangle.intersection(footprint).area
            row['ground_connection_candidates'].append(dict(index=p['index'],maximum_new_edge_m=maximum_edge,
                inside_existing_roof=footprint.covers(Point(point)),triangle_area_m2=triangle.area,
                existing_roof_overlap_m2=overlap,
                local_geometric_extension_eligible=bool(maximum_edge<=1. and triangle.area>1e-9 and overlap<=1e-9)))
        ids=np.flatnonzero(np.linalg.norm(xyz[:,:2]-targets[i,:2],axis=1)<=1.5)
        row['original_points']=[dict(index=int(j),xyz_m=xyz[j].tolist(),classification=int(cls[j])) for j in ids]
        for key in ('original_points','independent_points'):
            pool=row[key]
            counts={str(c):sum(p['classification']==c for p in pool) for c in sorted({p['classification'] for p in pool})}
            row[key+'_class_counts']=counts
            ground=[p for p in pool if p['classification']==2 and not p.get('withheld',0)]
            row[key+'_ground_z_range_m']=[min(p['xyz_m'][2] for p in ground),max(p['xyz_m'][2] for p in ground)] if ground else None
    if sha(RETURNS)!=RETURNS_SHA or sha(laz)!=laz_sha:raise ValueError('Source changed during scan')
    if sha(cap_path)!=cap_sha:raise ValueError('Mixed cap changed during audit')
    report=dict(source_rays_sha256=sha(rays_path),original_sha256=RETURNS_SHA,independent_sha256=laz_sha,cap_sha256=cap_sha,
        radius_m=1.5,transform_accuracy_m=transform.accuracy,points_scanned=offset,walls=rows,
        geometry_changed=False,flanks_measured=False,playable_changed=False,
        limits='Coordinate neighborhoods, not point correspondences. Class2 is ground, not certified rock; class1 is unclassified, not automatically vegetation. No fitted vertical offset. Mixed epochs/GEOID12B versus GEOID18 remain uncertainty.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(face=r['old_face'],original=r['original_points_class_counts'],independent=r['independent_points_class_counts'],independent_ground_z=r['independent_points_ground_z_range_m']) for r in rows],indent=2))


if __name__=='__main__':main()
