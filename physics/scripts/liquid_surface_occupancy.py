"""Reconcile a render-only density field with conservative solver-fluid interior.

This is not a bathymetry correction, particle deletion or a two-phase bubble
model. Only neighborhoods that the single-phase solver labels entirely fluid
seed an interior density floor. A trilinear transition stays behind the solver's
outer fluid/air boundary; wave geometry remains particle-derived outside it.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_anisotropic_surface import upper_surface
from liquid_density_surface import triangles_from_density


def fluid_core(classification):
    types=np.asarray(classification)
    if types.ndim!=3 or min(types.shape)<3 or not np.isfinite(types).all() or not np.isin(types,(0,1,2,3)).all():
        raise ValueError('Finite 3D fluid/solid/air/external-stage classification required')
    core=np.zeros(types.shape,dtype=bool)
    interior=np.ones(tuple(n-2 for n in types.shape),dtype=bool)
    for z,y,x in product((-1,0,1),repeat=3):
        interior &= types[1+z:types.shape[0]-1+z,1+y:types.shape[1]-1+y,1+x:types.shape[2]-1+x]==0
    core[1:-1,1:-1,1:-1]=interior
    return core


def centered_upsample(values,shape):
    """Trilinear interpolation at target cell centers, clamped at grid edges."""
    result=np.asarray(values,dtype=float)
    if result.ndim!=3 or len(shape)!=3 or any(n<1 for n in shape):
        raise ValueError('Positive ZYX grid shape required')
    for axis,count in enumerate(shape):
        position=(np.arange(count)+.5)*result.shape[axis]/count-.5
        lower=np.floor(position).astype(int)
        fraction=position-lower
        lo=np.clip(lower,0,result.shape[axis]-1)
        hi=np.clip(lower+1,0,result.shape[axis]-1)
        weight_shape=[1,1,1]
        weight_shape[axis]=count
        weight=fraction.reshape(weight_shape)
        result=np.take(result,lo,axis=axis)*(1-weight)+np.take(result,hi,axis=axis)*weight
    return result


def reconcile(density,classification):
    density=np.asarray(density,dtype=float)
    if density.ndim!=3 or not np.isfinite(density).all() or (density<0).any():
        raise ValueError('Finite nonnegative reconstruction density required')
    core=fluid_core(classification)
    ratios=np.array(density.shape)/np.array(core.shape)
    if not (ratios==ratios[0]).all() or ratios[0] not in (1,2,4):
        raise ValueError('Matching registered domain with integral uniform refinement required')
    confidence=centered_upsample(core,density.shape)
    result=np.maximum(density,confidence)
    parents=np.asarray(classification)
    for axis in range(3):
        parents=parents.repeat(int(ratios[0]),axis=axis)
    if np.any((density<.5)&(result>=.5)&(parents!=0)):
        raise ValueError('Interior floor created liquid outside a solver-fluid cell')
    return result,confidence,parents


def run(source,grids,output):
    if output.exists():
        raise FileExistsError(output)
    original=json.loads((source.parent/'report.json').read_text())
    particles=Path(original['source'])
    expected=particles.parent/(particles.stem.removesuffix('_particles')+'_grids')
    if grids.resolve()!=expected.resolve() or hashlib.sha256(particles.read_bytes()).hexdigest()!=original['source_sha256']:
        raise ValueError('Reconstruction and solver must be from the same captured state')
    with np.load(source) as data:
        arrays={key:data[key] for key in data.files}
    fields=load_fields(grids)
    raw=fields['SolidVelocity_Boundary'][...,3]
    if not np.isfinite(raw).all() or not np.allclose(raw,np.rint(raw),atol=1e-6):
        raise ValueError('Invalid categorical solver boundary field')
    types=np.rint(raw).astype(int)
    before=arrays['density']
    after,confidence,parents=reconcile(before,types)
    core=fluid_core(types)
    deep=confidence>=1-1e-12
    repeated=core.repeat(2,0).repeat(2,1).repeat(2,2)
    if repeated.shape!=before.shape:
        raise ValueError('Captured review expects 2x renderer resolution')
    minimum,extent,cells=[arrays[key] for key in ('minimum','extent','cells')]
    a=upper_surface(before,minimum,extent)
    b=upper_surface(after,minimum,extent)
    common=np.isfinite(a)&np.isfinite(b)
    change=b[common]-a[common]
    changed=(before<.5)&(after>=.5)
    volume=float(np.prod(extent/cells))
    arrays.update(density=after,upper_surface=b,core_confidence=confidence)
    output.mkdir(parents=True)
    np.savez_compressed(output/'reconstruction.npz',**arrays)
    boundary_metadata=json.loads((grids/'grids.json').read_text())
    raw_files=[g['file'] for g in boundary_metadata['grids'] if any(a['name']=='SolidVelocity_Boundary' for a in g['attributes'])]
    report={key:original[key] for key in ('source','source_sha256','particle_count','kernel_radius_m','moment_matched_footprint_m','center_smoothing','weighting')}
    report.update(reconstruction_source=str(source.resolve()),reconstruction_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  solver_grid_source=str(grids.resolve()),solver_boundary_sha256={name:hashlib.sha256((grids/name).read_bytes()).hexdigest() for name in raw_files},
                  conservative_core_cells=int(core.sum()),conservative_core_render_samples=int(repeated.sum()),
                  air_in_core_before=int((repeated&(before<.5)).sum()),air_in_core_after=int((repeated&(after<.5)).sum()),
                  fully_confident_samples=int(deep.sum()),air_in_fully_confident_after=int((deep&(after<.5)).sum()),
                  original_renderer_air_in_core=int((repeated&(fields['SDF'][...,0]>0)).sum()),
                  new_liquid_samples=int(changed.sum()),new_liquid_in_nonfluid_parent_cells=int((changed&(parents!=0)).sum()),
                  iso_05_voxel_volume_m3=[float((before>=.5).sum()*volume),float((after>=.5).sum()*volume)],
                  added_render_volume_m3_not_physical_mass=float(changed.sum()*volume),
                  top_crossing_common_columns=int(common.sum()),top_crossing_added_columns=int((~np.isfinite(a)&np.isfinite(b)).sum()),
                  top_crossing_removed_columns=int((np.isfinite(a)&~np.isfinite(b)).sum()),
                  top_crossing_changed_columns=int((abs(change)>1e-10).sum()),
                  top_crossing_change_rms_m=float(np.sqrt(np.mean(change**2))),
                  top_crossing_absolute_change_percentiles_m=np.percentile(abs(change),[50,95,99,100]).tolist(),
                  density_range=[float(after.min()),float(after.max())],triangle_count=len(triangles_from_density(after,minimum,extent)),
                  solver_occupancy_reconciled=True,simulation_modified=False,renderer_integrated=False,
                  physical_or_visual_acceptance=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--grids',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.source,args.grids,args.output)
