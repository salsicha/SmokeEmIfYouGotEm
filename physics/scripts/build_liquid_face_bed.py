"""Intersect the registered terrain triangles with the four physical fluid faces.

The resulting piecewise-linear bed follows the SAME mesh used for contact.
Cell-centre flux/stage tables are unchanged. This adds no measured bathymetry.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler


def face_bed(sampler, axes, lower, extent):
    axes=np.asarray(axes,dtype=float);lower=np.asarray(lower,dtype=float);extent=np.asarray(extent,dtype=float)
    if (axes.shape!=(2,2) or lower.shape!=(2,) or extent.shape!=(2,) or
        not np.isfinite(np.r_[axes.ravel(),lower,extent]).all() or np.any(extent<=0) or
        not np.allclose(axes@axes.T,np.eye(2),atol=1e-12,rtol=0)):
        raise ValueError('Finite orthonormal parent frame and positive extents required')
    faces=sampler.faces
    edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
    xy=sampler.xyz[:,:2]@axes.T-lower
    result=[]
    for face in range(4):
        normal=face//2;tangent=1-normal;plane=extent[normal] if face%2 else 0.
        a,b=xy[edges[:,0]],xy[edges[:,1]];da=a[:,normal]-plane;db=b[:,normal]-plane
        crosses=((da<=0)&(db>=0))|((db<=0)&(da>=0))
        transverse=crosses&(da!=db)
        f=da[transverse]/(da[transverse]-db[transverse])
        t=a[transverse,tangent]+f*(b[transverse,tangent]-a[transverse,tangent])
        coincident=(da==0)&(db==0)
        t=np.r_[t,a[coincident,tangent],b[coincident,tangent]]
        t=np.unique(np.r_[0.,t[(t>0)&(t<extent[tangent])],extent[tangent]])
        # One shared edge is evaluated only once; no spatial smoothing or
        # arbitrary interval merging may erase a terrain corner.
        def query(x):
            local=np.zeros((len(x),2));local[:,normal]=plane;local[:,tangent]=x
            en=(local+lower)@axes
            return sampler.sample(en[:,0],en[:,1])
        bed=query(t)
        fractions=np.array([.125,.25,.5,.75,.875])
        probes=(t[:-1,None]+np.diff(t)[:,None]*fractions).ravel()
        actual=query(probes);expected=np.interp(probes,t,bed)
        if not np.allclose(actual,expected,atol=1e-8,rtol=0):
            raise ValueError('Face intervals do not preserve original terrain triangles')
        result.append(dict(face=face,knots_cm=np.column_stack((t*100,bed*100)).tolist(),
                           max_independent_height_error_m=float(np.max(abs(actual-expected),initial=0))))
    return result


def build(mesh_path,boundary_path,output):
    mesh_path,boundary_path,output=map(Path,(mesh_path,boundary_path,output))
    if output.exists():raise FileExistsError(output)
    boundary=json.loads(boundary_path.read_text());packed=np.asarray(boundary['packed_vectors'],dtype=float)
    bounds=np.asarray(boundary['domain']['native_face_bounds_m'],dtype=float)
    sampler=RegisteredMeshSampler(np.load(mesh_path))
    faces=face_bed(sampler,packed[:2,:2],bounds[0],packed[3,:2]/100)
    result=dict(schema='raftsim.physical_face_bed.v1',source_mesh=str(mesh_path),
                source_mesh_sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
                source_boundary=str(boundary_path),source_boundary_sha256=hashlib.sha256(boundary_path.read_bytes()).hexdigest(),
                canonical_axes=packed[:2].tolist(),lower_station_lateral_m=bounds[0].tolist(),
                extent_cm=packed[3].tolist(),parent_cells=packed[5].astype(int).tolist(),faces=faces,
                provenance='Derived intersection of existing contact mesh, including its inferred submerged bed; not a new survey.',
                boundary_flux_stage_changed=False,engine_integration_verified=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return dict(path=str(output),knots_per_face=[len(f['knots_cm']) for f in faces],
                maximum_height_error_m=max(f['max_independent_height_error_m'] for f in faces))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mesh',required=True,type=Path);parser.add_argument('--boundary',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    print(json.dumps(build(args.mesh,args.boundary,args.output),indent=2))
