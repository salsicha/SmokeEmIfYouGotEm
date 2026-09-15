"""Add source-visible vertex probes without removing any legacy probe.

A one-metre ray can encounter a different part of a nonconvex roof first.
The additional rays use every incident source plane and certify visibility
against the original closed solid. This does not waive legacy failures.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_troublemaker_dem_rock_cap import ROOT
from south_fork_rock_union import SourceRockUnion, sha


def segment_hits(triangles, start, end):
    """Double-precision two-sided intersections, ordered from segment start.

    Barycentric slack only absorbs arithmetic at shared vertices/edges; it is
    not the native physical position tolerance (which stays 0.1 cm).
    """
    triangles=np.asarray(triangles,float);start=np.asarray(start,float);end=np.asarray(end,float)
    if triangles.ndim!=3 or triangles.shape[1:]!=(3,3) or start.shape!=(3,) or end.shape!=(3,):
        raise ValueError('Triangles and three-dimensional segment endpoints required')
    if not np.isfinite(triangles).all() or not np.isfinite([start,end]).all() or np.array_equal(start,end):
        raise ValueError('Finite nonzero source segment required')
    direction=end-start
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
    nonsingular=det!=0
    reciprocal=np.zeros_like(det);reciprocal[nonsingular]=1/det[nonsingular]
    s=start-triangles[:,0];u=reciprocal*np.einsum('ij,ij->i',s,h)
    q=np.cross(s,e1);v=reciprocal*np.einsum('j,ij->i',direction,q)
    t=reciprocal*np.einsum('ij,ij->i',e2,q)
    keep=nonsingular&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(t>=0)&(t<=1)
    return np.sort(t[keep])


def visible_vertex_probes(vertices, faces, solid_vertices, solid_faces):
    vertices=np.asarray(vertices,float);faces=np.asarray(faces)
    triangles=np.asarray(solid_vertices)[solid_faces]*[100,-100,100]
    result=[]
    for index,point in enumerate(vertices):
        # All spatially coincident fans constrain the exterior direction, even
        # if their indices were split for watertight extrusion.
        coincident=np.flatnonzero(np.all(vertices==point,axis=1))
        incident=faces[np.isin(faces,coincident).any(axis=1)]
        own=faces[np.any(faces==index,axis=1)]
        if not len(own):raise ValueError('Unsupported original vertex')
        own_xyz=vertices[own]
        a=own_xyz[:,1,:2]-own_xyz[:,0,:2];b=own_xyz[:,2,:2]-own_xyz[:,0,:2]
        area=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])
        center=own_xyz[np.argmax(area)].mean(axis=0)
        horizontal=point[:2]-center[:2]
        adjacent=vertices[incident]
        edges=adjacent[:,1:]-adjacent[:,0,None,:]
        gradient=np.linalg.solve(edges[:,:,:2],edges[:,:,2,None])[...,0]
        dz=max(1.,float((gradient@horizontal).max())+1.)
        normal=np.r_[horizontal,dz];normal/=np.linalg.norm(normal);normal*=np.array([1,-1,1])
        target=point*[100,-100,100]
        distance=100.
        for _ in range(32):
            hits=segment_hits(triangles,target+normal*distance,target-normal*distance)
            error=abs(float(hits[0])-.5)*2*distance if len(hits) else float('inf')
            if error<1e-7:
                break
            distance*=.5
            if distance<=.4:
                raise ValueError('No source-visible probe longer than four native tolerances')
        else:raise ValueError('Source ray visibility did not converge')
        result.append(dict(kind='original_vertex_source_visible_cone',source_vertex_index=index,
            world_position_cm=target.tolist(),outward_normal=normal.tolist(),ray_half_length_cm=distance,
            source_first_hit_error_cm=error))
    return result


def prepare(manifest_path, legacy_path, output):
    manifest_path,legacy_path,output=map(lambda p:Path(p).resolve(),(manifest_path,legacy_path,output))
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp probe file required')
    manifest=json.loads(manifest_path.read_text());origin=manifest['origin_utm_and_vertical_datum_m']
    union=SourceRockUnion(manifest_path,ROOT,ROOT/manifest['source_mesh_path'],origin[:2],origin[2])
    legacy=json.loads(legacy_path.read_text())
    if legacy['source_cap_sha256']!=manifest['cap_sha256']:
        raise ValueError('Legacy probes belong to different source geometry')
    with np.load(ROOT/manifest['cap_path'],allow_pickle=False) as data:
        extra=visible_vertex_probes(union.xyz,union.faces,data['solid_vertices_m'],data['solid_triangles'])
    record=dict(legacy,probes=legacy['probes']+extra,
        legacy_probe_file=legacy_path.relative_to(ROOT).as_posix(),legacy_probe_sha256=sha(legacy_path),
        retained_legacy_probe_count=len(legacy['probes']),all_legacy_probes_retained_unchanged=True,
        additional_source_vertex_count=len(extra),source_cap_manifest_sha256=sha(manifest_path),
        native_position_tolerance_cm=.1,legacy_failures_waived=False)
    output.write_text(json.dumps(record,indent=2)+'\n')
    return dict(path=output.relative_to(ROOT).as_posix(),sha256=sha(output),
        retained_legacy_probe_count=len(legacy['probes']),additional_source_vertex_count=len(extra),
        ray_half_length_min_max_cm=[min(p['ray_half_length_cm'] for p in extra),max(p['ray_half_length_cm'] for p in extra)],
        source_first_hit_max_error_cm=max(p['source_first_hit_error_cm'] for p in extra),legacy_failures_waived=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--legacy-probes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.manifest,args.legacy_probes,args.output),indent=2),flush=True)
