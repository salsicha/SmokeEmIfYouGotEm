"""Triangulate density's interface and reconstruct metric narrow-band distance.

Offline rendering reference only. Uses a consistent six-tetrahedron cube split;
the interface is piecewise linear, not the exact trilinear-density isosurface.
No particle/physics edits, artificial wave displacement, or extra water plane.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def triangles_from_density(density, minimum, extent, level=.5):
    density = np.asarray(density, dtype=float)
    minimum, extent = np.asarray(minimum, float), np.asarray(extent, float)
    if density.ndim != 3 or min(density.shape) < 2 or not np.isfinite(density).all():
        raise ValueError('Finite ZYX density grid, at least two cells per axis required')
    if minimum.shape != (3,) or extent.shape != (3,) or not np.isfinite([*minimum, *extent, level]).all() or (extent <= 0).any():
        raise ValueError('Finite positive metric grid required')
    nz, ny, nx = density.shape
    spacing = extent/np.array([nx, ny, nz])
    corners = np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0],
                        [0,0,1],[1,0,1],[0,1,1],[1,1,1]])
    values = np.stack([density[z:z+nz-1,y:y+ny-1,x:x+nx-1] for x,y,z in corners], axis=-1)
    active = (values.min(axis=-1) < level) & (values.max(axis=-1) >= level)
    z, y, x = np.nonzero(active)
    base = np.stack((x,y,z), axis=-1)
    values = values[active]
    positions = minimum+(base[:,None,:]+corners[None,:,:]+.5)*spacing
    output = []
    for tet in ((0,1,3,7),(0,3,2,7),(0,2,6,7),(0,6,4,7),(0,4,5,7),(0,5,1,7)):
        p, v = positions[:,tet,:], values[:,tet]
        cases = ((v >= level)*np.array([1,2,4,8])).sum(axis=1)
        for case in range(1,15):
            selected = cases == case
            if not selected.any():
                continue
            pp, vv = p[selected], v[selected]
            inside = [i for i in range(4) if case & (1 << i)]
            outside = [i for i in range(4) if not case & (1 << i)]
            outward = pp[:,outside,:].mean(axis=1)-pp[:,inside,:].mean(axis=1)
            def edge(i,j):
                t = (level-vv[:,i])/(vv[:,j]-vv[:,i])
                return pp[:,i]+t[:,None]*(pp[:,j]-pp[:,i])
            if len(inside) == 1:
                polygons = [np.stack([edge(inside[0],j) for j in outside], axis=1)]
            elif len(outside) == 1:
                polygons = [np.stack([edge(i,outside[0]) for i in inside], axis=1)]
            else:
                a,b = inside
                c,d = outside
                ac,ad,bc,bd = edge(a,c),edge(a,d),edge(b,c),edge(b,d)
                polygons = [np.stack((ac,ad,bc),axis=1),np.stack((ad,bd,bc),axis=1)]
            for triangle in polygons:
                normal = np.cross(triangle[:,1]-triangle[:,0],triangle[:,2]-triangle[:,0])
                flip = np.einsum('ij,ij->i',normal,outward) < 0
                triangle[flip] = triangle[flip][:,[0,2,1]]
                valid = np.linalg.norm(normal,axis=1) > np.min(spacing)**2*1e-12
                output.append(triangle[valid])
    return np.concatenate(output) if output else np.empty((0,3,3))


def triangle_distance_squared(points, triangle):
    """Exact point-to-triangle distance (plane interior or nearest edge)."""
    a,b,c = triangle
    ab,ac = b-a,c-a
    normal = np.cross(ab,ac)
    area_squared = np.dot(normal,normal)
    if area_squared <= 0:
        raise ValueError('Nondegenerate triangle required')
    delta = points-a
    height = delta@normal
    projected = delta-height[:,None]*normal/area_squared
    aa,bb,cc = np.dot(ab,ab),np.dot(ab,ac),np.dot(ac,ac)
    pa,pb = projected@ab,projected@ac
    u,v = (cc*pa-bb*pb)/area_squared,(aa*pb-bb*pa)/area_squared
    inside = (u >= 0) & (v >= 0) & (u+v <= 1)
    distance = np.where(inside,height**2/area_squared,np.inf)
    for start,end in ((a,b),(b,c),(c,a)):
        edge = end-start
        t = np.clip((points-start)@edge/np.dot(edge,edge),0,1)
        d = points-(start+t[:,None]*edge)
        distance = np.minimum(distance,np.einsum('ij,ij->i',d,d))
    return distance


def narrow_band_distance(density, triangles, minimum, extent, bandwidth, level=.5):
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError('Positive finite metric bandwidth required')
    cells = np.array(density.shape[::-1])
    minimum, extent = np.asarray(minimum,float),np.asarray(extent,float)
    spacing = extent/cells
    distance = np.full(density.shape,bandwidth**2)
    flat = distance.ravel()
    for triangle in triangles:
        lo = np.maximum(np.ceil((triangle.min(0)-bandwidth-minimum)/spacing-.5).astype(int),0)
        hi = np.minimum(np.floor((triangle.max(0)+bandwidth-minimum)/spacing-.5).astype(int),cells-1)
        if np.any(lo > hi):
            continue
        z,y,x = np.meshgrid(np.arange(lo[2],hi[2]+1),np.arange(lo[1],hi[1]+1),np.arange(lo[0],hi[0]+1),indexing='ij')
        indices = np.stack((x.ravel(),y.ravel(),z.ravel()),axis=-1)
        points = minimum+(indices+.5)*spacing
        linear = indices[:,0]+cells[0]*(indices[:,1]+cells[1]*indices[:,2])
        flat[linear] = np.minimum(flat[linear],triangle_distance_squared(points,triangle))
    return np.sqrt(distance)*np.where(density >= level,-1.,1.)


def run(source,output,bandwidth):
    if output.exists():
        raise FileExistsError(output)
    start = time.perf_counter()
    with np.load(source) as data:
        density,minimum,extent,cells = [data[k] for k in ('density','minimum','extent','cells')]
    triangles = triangles_from_density(density,minimum,extent)
    mesh_seconds = time.perf_counter()-start
    sdf = narrow_band_distance(density,triangles,minimum,extent,bandwidth)
    output.mkdir(parents=True)
    np.savez_compressed(output/'surface.npz',triangles=triangles,sdf=sdf,minimum=minimum,extent=extent,cells=cells)
    # Renderer consumes centimeters, RGBA16f, X fastest. G is intentionally
    # zero: this snapshot validates geometry, not a new foam transport model.
    rgba = np.zeros((*sdf.shape,4),dtype='<f2')
    rgba[...,0] = sdf*100
    rgba.tofile(output/'surface.rgba16f')
    report = dict(source=str(source.resolve()),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  triangle_count=len(triangles),grid_cells=cells.tolist(),minimum_m=minimum.tolist(),extent_m=extent.tolist(),
                  bandwidth_m=bandwidth,mesh_seconds=mesh_seconds,total_seconds=time.perf_counter()-start,
                  sdf_range_m=[float(sdf.min()),float(sdf.max())],
                  finite=bool(np.isfinite(sdf).all()),
                  sign_matches_density=bool(np.array_equal(sdf <= 0,density >= .5)),
                  renderer_texture='surface.rgba16f',texture_sha256=hashlib.sha256((output/'surface.rgba16f').read_bytes()).hexdigest(),
                  distance_reference='nearest piecewise-linear tetrahedron isosurface triangle, truncated narrow band',
                  foam_channel_zero=True,renderer_integrated=False,real_time_generation=False,
                  physical_or_visual_acceptance=False)
    metadata=source.parent/'report.json'
    if metadata.is_file():
        reconstruction=json.loads(metadata.read_text())
        if 'particle_count' in reconstruction and 'source_sha256' in reconstruction:
            report['particle_capture_sha256']=reconstruction['source_sha256']
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bandwidth',type=float,default=.5)
    args = parser.parse_args()
    run(args.source,args.output,args.bandwidth)
