"""Explicit inferred interior surface for ambiguous unclassified cap returns.

This is NOT an original-return cap and cannot pass its source-exact runtime
gate. Preserve original XYZ separately, all seed/ground vertices, and the
entire footprint. Boundary XYZ is protected unless boundary-height inference
is explicitly requested; boundary XY is always fixed. Only well-surrounded
high outliers may be fitted down.
The 0.75m radius/0.3m threshold are modeling priors, not measured uncertainty.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from build_troublemaker_dem_rock_cap import ROOT, RETURNS, RETURNS_SHA, ORIGIN, close_cap_below_retained_terrain
from build_troublemaker_source_connected_cap import pulse_eligibility
from south_fork_rock_union import sha


def supported_plane(point, neighbours, radius=.75):
    point, neighbours = np.asarray(point,float), np.asarray(neighbours,float)
    if point.shape!=(3,) or neighbours.ndim!=2 or neighbours.shape[1]!=3 or not np.isfinite(point).all() or not np.isfinite(neighbours).all() or not np.isfinite(radius) or radius<=0:
        raise ValueError('Finite XYZ and positive modeling radius required')
    delta=neighbours[:,:2]-point[:2]
    distance=np.linalg.norm(delta,axis=1)
    keep=(distance>0)&(distance<radius)
    delta,distance,z=delta[keep],distance[keep],neighbours[keep,2]
    if len(z)<8:return None
    angles=np.sort(np.arctan2(delta[:,1],delta[:,0]))
    gap=float(np.diff(np.r_[angles,angles[0]+2*np.pi]).max())
    if gap>=np.pi:return None # No one-sided extrapolation across a rock edge.
    matrix=np.column_stack([np.ones(len(z)),delta/radius])
    base=(1-(distance/radius)**2)**2
    weight=base.copy()
    for _ in range(8):
        root=np.sqrt(weight)
        coefficients,_,rank,_=np.linalg.lstsq(matrix*root[:,None],z*root,rcond=None)
        if rank!=3:return None
        residual=z-matrix@coefficients
        mad=float(np.median(abs(residual-np.median(residual))))
        # Huber weighting remains positive; no source is removed or relabeled.
        scale=max(1e-9,1.4826*mad)
        weight=base*np.minimum(1.,1.5*scale/np.maximum(abs(residual),1e-30))
    return dict(height_m=float(coefficients[0]),mad_m=mad,
        support_count=len(z),maximum_angular_gap_radians=gap,
        threshold_m=max(.3,3*1.4826*mad))


def infer_surface(cap, seed_ids, cloud_xyz, last, classes, *, infer_boundary_heights=False):
    xyz=cap['vertices_m'];ids=cap['original_return_index']
    if not np.array_equal(xyz,cloud_xyz[ids]):raise ValueError('Original cap XYZ changed')
    boundary=np.zeros(len(xyz),bool);boundary[np.unique(cap['boundary_edges'])]=True
    protected=np.isin(ids,seed_ids)|(classes[ids]!=1)
    if not infer_boundary_heights:protected|=boundary
    pool_ids=np.flatnonzero(last & np.isin(classes,[1,2,10]))
    tree=cKDTree(cloud_xyz[pool_ids,:2])
    result=xyz.copy();changes=[]
    for i in np.flatnonzero(~protected):
        neighbours=pool_ids[tree.query_ball_point(xyz[i,:2],.75)]
        neighbours=neighbours[neighbours!=ids[i]]
        fit=supported_plane(xyz[i],cloud_xyz[neighbours])
        if fit is None or xyz[i,2]-fit['height_m']<=fit['threshold_m']:continue
        result[i,2]=fit['height_m']
        changes.append(dict(vertex=int(i),original_return_id=int(ids[i]),
            original_height_m=float(xyz[i,2]),inferred_height_m=float(result[i,2]),**fit))
    if not np.array_equal(result[protected],xyz[protected]) or not np.array_equal(result[:,:2],xyz[:,:2]):raise ValueError('Protected geometry changed')
    return result,protected,changes


def run(cap_manifest,seed_manifest,pulse_manifest,output,infer_boundary_heights=False):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):raise ValueError('Fresh project tmp output required')
    records=[json.loads(p.read_text()) for p in (cap_manifest,seed_manifest)]
    caps=[]
    for record in records:
        path=ROOT/record['cap_path']
        if sha(path)!=record['cap_sha256'] or record['original_returns_sha256']!=RETURNS_SHA:raise ValueError('Original cap provenance changed')
        with np.load(path,allow_pickle=False) as d:caps.append({k:d[k] for k in d.files})
    if sha(RETURNS)!=RETURNS_SHA:raise ValueError('Original point cloud changed')
    with np.load(RETURNS,allow_pickle=False) as d:
        cloud=np.column_stack([d[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-ORIGIN
        classes=d['classification']
    last,pulses=pulse_eligibility(pulse_manifest,len(cloud))
    pulses=dict(pulses,
        rule='Last/only returns support the local fit; they do not certify ground or rock. Generated roof heights may be inferred.',
        source_xyz_modified=False,
        source_xyz_modified_scope='Original captured archive only; see vertex_authority for fitted roof heights')
    cap,seed=caps
    surface,protected,changes=infer_surface(cap,seed['original_return_index'],cloud,last,classes,
        infer_boundary_heights=infer_boundary_heights)
    if not changes:raise ValueError('No supported high outliers; no hypothesis generated')
    floor=records[0]['inferred_solid']['internal_floor_m']
    vertices,faces,kinds,solid=close_cap_below_retained_terrain(surface,cap['triangles'],floor)
    # A different schema/field names intentionally prevents an original-return
    # loader from silently labeling fitted roof vertices as captured positions.
    output.mkdir();path=output/'inferred_surface.npz'
    authority=np.zeros(len(surface),np.uint8)
    authority[[r['vertex'] for r in changes]]=1
    np.savez_compressed(path,surface_vertices_m=surface,triangles=cap['triangles'],
        original_source_vertices_m=cap['vertices_m'],original_return_index=cap['original_return_index'],
        original_classification=cap['original_classification'],vertex_authority=authority,
        protected_vertices=protected,boundary_edges=cap['boundary_edges'],
        solid_vertices_m=vertices,solid_triangles=faces,solid_face_kind=kinds)
    report=dict(schema='raftsim.interpreted_cap_interior_surface.v1',
        parent_cap_manifest_sha256=sha(cap_manifest),parent_cap_sha256=records[0]['cap_sha256'],
        seed_manifest_sha256=sha(seed_manifest),original_returns_sha256=RETURNS_SHA,
        pulse_provenance=pulses,surface_path=path.relative_to(ROOT).as_posix(),surface_sha256=sha(path),
        authority_codes={'0':'Unchanged selected original return; classification remains uncertain','1':'INFERRED robust-plane height; not a captured XYZ'},
        footprint_and_topology_unchanged=True,seed_and_ground_xyz_unchanged=True,
        boundary_xy_unchanged=True,boundary_height_inference_requested=infer_boundary_heights,
        boundary_xyz_unchanged=bool(np.array_equal(surface[np.unique(cap['boundary_edges'])],cap['vertices_m'][np.unique(cap['boundary_edges'])])),
        original_capture_archive_unchanged=True,protected_vertex_count=int(protected.sum()),
        changed_vertex_count=len(changes),changes=changes,inferred_solid=solid,
        requires_new_physical_union=True,original_return_runtime_loader_compatible=False,
        engine_verified=False,hydraulics_recooked=False,normal_play_changed=False,
        visual_or_physical_accepted=False,
        limits='Explicit interpretation only. Robust neighbors cannot certify vegetation or rock. Do not use as a cosmetic-only mesh swap or copy old water state.')
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cap',type=Path,required=True);p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--pulses',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--infer-boundary-heights',action='store_true',help='Explicitly infer ambiguous boundary Z too, preserving all boundary XY and fixed seed/ground anchors')
    a=p.parse_args();run(a.cap,a.seed,a.pulses,a.output,a.infer_boundary_heights)
