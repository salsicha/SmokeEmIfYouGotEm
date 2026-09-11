"""Bounded upwind distance reconstruction with subcell interface seeds.

CPU reference for a GPU Jacobi implementation. Fixed interface seeds use the
local scalar gradient, capped by the nearest edge crossing. This is an
approximate discrete distance, not exact distance to a triangulated surface.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from liquid_anisotropic_surface import upper_surface


def shifted(values,axis,offset,fill=None):
    result=np.roll(values,-offset,axis=axis)
    edge=[slice(None)]*3
    edge[axis]=-1 if offset>0 else 0
    result[tuple(edge)]=values[tuple(edge)] if fill is None else fill
    return result


def seed_distance(phi,spacing,bandwidth):
    gradient=np.gradient(phi,*spacing,edge_order=1)
    norm=np.sqrt(sum(g*g for g in gradient))
    minimum_edge=np.full(phi.shape,bandwidth)
    seeds=phi==0
    for axis,dx in enumerate(spacing):
        for direction in (-1,1):
            neighbor=shifted(phi,axis,direction)
            crossing=(np.signbit(phi)!=np.signbit(neighbor)) | (neighbor==0)
            denominator=abs(phi)+abs(neighbor)
            distance=np.divide(abs(phi)*dx,denominator,out=np.full(phi.shape,bandwidth),where=denominator>0)
            minimum_edge=np.minimum(minimum_edge,np.where(crossing,distance,bandwidth))
            seeds |= crossing
    linear=np.divide(abs(phi),norm,out=np.full(phi.shape,bandwidth),where=norm>1e-12)
    distance=np.where(seeds,np.minimum(linear,minimum_edge),bandwidth)
    distance[phi==0]=0
    return distance,seeds


def upwind_update(distance,spacing,bandwidth):
    neighbors=np.stack([np.minimum(shifted(distance,a,-1,bandwidth),shifted(distance,a,1,bandwidth)) for a in range(3)],axis=-1)
    order=np.argsort(neighbors,axis=-1)
    values=np.take_along_axis(neighbors,order,axis=-1)
    steps=np.asarray(spacing)[order]
    result=values[...,0]+steps[...,0]
    for count in (2,3):
        weights=1/steps[...,:count]**2
        aa=weights.sum(axis=-1)
        bb=(values[...,:count]*weights).sum(axis=-1)
        cc=(values[...,:count]**2*weights).sum(axis=-1)-1
        root=(bb+np.sqrt(np.maximum(bb*bb-aa*cc,0)))/aa
        result=np.where(result>values[...,count-1],root,result)
    return np.minimum(result,distance)


def redistance(phi,spacing,bandwidth=.5,iterations=12):
    phi=np.asarray(phi,dtype=float)
    spacing=np.asarray(spacing,dtype=float)
    if phi.ndim!=3 or min(phi.shape)<2 or not np.isfinite(phi).all() or spacing.shape!=(3,) or not np.isfinite(spacing).all() or (spacing<=0).any() or not np.isfinite(bandwidth) or bandwidth<=0 or not isinstance(iterations,int) or not 1<=iterations<=128:
        raise ValueError('Finite scalar grid, positive metric spacing/bandwidth and bounded iterations required')
    distance,seeds=seed_distance(phi,spacing,bandwidth)
    deltas=[]
    for _ in range(iterations):
        updated=np.where(seeds,distance,upwind_update(distance,spacing,bandwidth))
        deltas.append(float(np.max(abs(updated-distance))))
        distance=updated
    return distance*np.where(phi<=0,-1.,1.),dict(seed_count=int(seeds.sum()),iteration_max_change_m=deltas)


def run(source,output,reference=None):
    if output.exists():
        raise FileExistsError(output)
    with np.load(source) as data:
        density,minimum,extent,cells=[data[k] for k in ('density','minimum','extent','cells')]
    start=time.perf_counter()
    phi=(.5-density).astype('<f4')
    sdf,details=redistance(phi,(extent/cells)[::-1])
    elapsed=time.perf_counter()-start
    original_top=upper_surface(density,minimum,extent)
    sdf_top=upper_surface(.5-sdf,minimum,extent)
    common=np.isfinite(original_top)&np.isfinite(sdf_top)
    delta=sdf_top[common]-original_top[common]
    report=dict(source=str(source.resolve()),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                grid_cells=cells.tolist(),minimum_m=minimum.tolist(),extent_m=extent.tolist(),bandwidth_m=.5,
                iterations=12,cpu_seconds=elapsed,finite=bool(np.isfinite(sdf).all()),
                sign_matches_density=bool(np.array_equal(sdf<=0,density>=.5)),
                top_change_rms_m=float(np.sqrt(np.mean(delta**2))),
                top_absolute_change_percentiles_m=np.percentile(abs(delta),[50,95,99,100]).tolist(),
                distance_reference='upwind Eikonal narrow band with gradient-corrected subcell seeds',
                renderer_integrated=False,real_time_generation=False,physical_or_visual_acceptance=False,**details)
    if reference:
        with np.load(reference) as data:
            exact=data['sdf']
        if exact.shape!=sdf.shape:
            raise ValueError('Reference dimensions differ')
        band=abs(exact)<.5
        error=sdf[band]-exact[band]
        report.update(triangle_reference=str(reference.resolve()),triangle_band_rms_error_m=float(np.sqrt(np.mean(error**2))),
                      triangle_band_absolute_error_percentiles_m=np.percentile(abs(error),[50,95,99,100]).tolist())
    output.mkdir(parents=True)
    np.savez_compressed(output/'surface.npz',sdf=sdf,minimum=minimum,extent=extent,cells=cells)
    phi.tofile(output/'input_phi.r32f')
    rgba=np.zeros((*sdf.shape,4),dtype='<f2')
    rgba[...,0]=sdf*100
    rgba.tofile(output/'surface.rgba16f')
    report.update(input_scalar='input_phi.r32f',input_scalar_precision='float32',
                  input_scalar_sha256=hashlib.sha256((output/'input_phi.r32f').read_bytes()).hexdigest(),
                  renderer_texture='surface.rgba16f',texture_sha256=hashlib.sha256((output/'surface.rgba16f').read_bytes()).hexdigest(),foam_channel_zero=True)
    metadata=json.loads((source.parent/'report.json').read_text())
    report['particle_capture_sha256']=metadata['source_sha256']
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args()
    run(args.source,args.output,args.reference)
