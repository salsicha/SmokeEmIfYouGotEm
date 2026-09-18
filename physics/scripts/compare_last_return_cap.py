"""Compare a pulse-selection hypothesis with the installed source cap.

Reports coverage lost as missing geometry, never as recovered ground. No
steep-area or pulse-selection result alone authorizes playable promotion.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from shapely import union_all
from shapely.geometry import Polygon
from build_troublemaker_dem_rock_cap import ROOT, RETURNS, RETURNS_SHA
from south_fork_rock_union import sha


def stats(cap):
    tri=cap['vertices_m'][cap['triangles']]
    cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    area=np.linalg.norm(cross,axis=1)/2
    slope=np.degrees(np.arccos(np.clip(cross[:,2]/(2*area),-1,1)))
    footprint=union_all([Polygon(t[:,:2]) for t in tri])
    polygons=list(footprint.geoms) if footprint.geom_type=='MultiPolygon' else [footprint]
    return dict(roof_vertices=len(cap['vertices_m']),roof_triangles=len(tri),
        projected_area_m2=footprint.area,roof_area_above_60_degrees_m2=float(area[slope>60].sum()),
        connected_components=len(polygons),interior_holes=sum(len(p.interiors) for p in polygons)),footprint


def run(baseline_path,candidate_path,output):
    if output.exists(): raise ValueError('Fresh report required')
    records=[json.loads(p.read_text()) for p in (baseline_path,candidate_path)]
    caps=[]
    for r in records:
        path=ROOT/r['cap_path']
        if sha(path)!=r['cap_sha256']: raise ValueError('Cap source changed')
        with np.load(path,allow_pickle=False) as d:caps.append({k:d[k] for k in d.files})
    if sha(RETURNS)!=RETURNS_SHA: raise ValueError('Original returns changed')
    with np.load(RETURNS,allow_pickle=False) as d:
        xyz=np.column_stack([d[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-np.array(records[0]['origin_utm_and_vertical_datum_m'])
        for cap in caps:
            if not np.array_equal(xyz[cap['original_return_index']],cap['vertices_m']): raise ValueError('Original roof XYZ changed')
            if not np.array_equal(d['classification'][cap['original_return_index']],cap['original_classification']): raise ValueError('Source classification changed')
    measures=[stats(cap) for cap in caps]
    old,new=(cap['original_return_index'] for cap in caps)
    report=dict(schema='raftsim.cap_pulse_selection_comparison.v1',
        baseline_manifest_sha256=sha(baseline_path),candidate_manifest_sha256=sha(candidate_path),
        baseline_cap_sha256=records[0]['cap_sha256'],candidate_cap_sha256=records[1]['cap_sha256'],
        original_returns_sha256=RETURNS_SHA,all_roof_xyz_and_classifications_exact=True,
        baseline=measures[0][0],candidate=measures[1][0],
        lost_coverage_m2=measures[0][1].difference(measures[1][1]).area,
        added_coverage_m2=measures[1][1].difference(measures[0][1]).area,
        removed_original_ids=np.setdiff1d(old,new).tolist(),added_original_ids=np.setdiff1d(new,old).tolist(),
        production_promoted=False,hydraulics_recooked=False,visual_or_physical_accepted=False,
        limits='A removed observation remains in the immutable original archive. Lower steep area is not physical validation; missing coverage is NOT exposed ground or a measured gap.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('removed_original_ids','added_original_ids')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.baseline,a.candidate,a.output)
