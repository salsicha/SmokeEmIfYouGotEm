"""Quantify bed/control loss between matched hydraulic sample lattices.

This frozen-stage capacity audit is not a flow solve, a submerged survey or a
convergence test. It distinguishes point-sampling loss of narrow rocks/channels
from temporal settling. The four half-metre samples are not exact cell integrals.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from compare_south_fork_resolution import comparable,restrict


def capacity(coarse_bed,fine_bed,ratio,stage,mask,dx,dy):
    coarse_bed=np.asarray(coarse_bed,dtype=float)
    fine_bed=np.asarray(fine_bed,dtype=float)
    if (coarse_bed.ndim!=2 or mask.shape!=coarse_bed.shape or mask.dtype!=bool or
        not mask.any() or not np.isfinite(coarse_bed).all() or not np.isfinite(stage) or
        not np.isfinite(dx) or not np.isfinite(dy) or min(dx,dy)<=0):
        raise ValueError('Finite beds/stage, positive cells and a nonempty Boolean mask required')
    fine_mean=restrict(fine_bed,ratio)
    if fine_mean.shape!=coarse_bed.shape:raise ValueError('Nested bed shapes differ')
    h=np.maximum(stage-coarse_bed,0.)
    fine_h=restrict(np.maximum(stage-fine_bed,0.),ratio)
    fraction=restrict((fine_bed<stage).astype(float),ratio)
    wet=h>0
    selected_fractions=fraction[mask]
    area=dx*dy
    sections=lambda depth:np.sum(np.where(mask,depth,0.),axis=0)*dy
    c_section,f_section=sections(h),sections(fine_h)
    return {'stage_above_datum_m':float(stage),
        'coarse_wet_area_m2':float(wet[mask].sum()*area),
        'fine_sampled_wet_area_m2':float(selected_fractions.sum()*area),
        'coarse_storage_m3':float(h[mask].sum()*area),
        'fine_sampled_storage_m3':float(fine_h[mask].sum()*area),
        'coarse_cell_area_with_mixed_fine_wet_dry_m2':float(((fraction>0)&(fraction<1)&mask).sum()*area),
        'coarse_dry_cell_area_with_some_fine_water_m2':float((~wet&(fraction>0)&mask).sum()*area),
        'coarse_wet_cell_area_with_some_fine_dry_rock_m2':float((wet&(fraction<1)&mask).sum()*area),
        'coarse_section_area_m2':c_section.tolist(),
        'fine_sampled_section_area_m2':f_section.tolist(),
        'maximum_absolute_section_area_difference_m2':float(np.max(abs(f_section-c_section)))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coarse',type=Path,required=True)
    parser.add_argument('--fine',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.png').exists():raise FileExistsError('Retain previous evidence')
    runs=[p.resolve() for p in (args.coarse,args.fine)]
    registrations=[json.loads((p/'registration.json').read_text()) for p in runs]
    scenario_paths=[next((p/'scenario').glob('*/scenario.json')) for p in runs]
    scenarios=[read_scenario2_5d_package(p) for p in scenario_paths]
    coarse,fine=scenarios
    ratio=comparable(coarse,fine,*registrations)
    # Select a representative stage from the existing coarse final field, not
    # a source water-level measurement. It is deliberately spatially frozen.
    fields=runs[0]/'engine_review'
    manifest=json.loads((fields/'manifest.json').read_text())
    records=manifest['bands'][0]['arrays']
    arrays={}
    for key in ('h','bed'):
        path=fields/records[key]['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=records[key]['sha256']:raise ValueError('Coarse field changed')
        arrays[key]=np.load(path)
    x,y=coarse.grid.meshgrid()
    mask=(abs(x)<25.5)&(abs(y)<30.5)
    reference=float(np.median((arrays['h']+arrays['bed'])[mask&(arrays['h']>.1)]))
    reports=[capacity(coarse.bed,fine.bed,ratio,stage,mask,coarse.grid.dx,coarse.grid.dy)
        for stage in (reference-.5,reference-.25,reference,reference+.25,reference+.5)]
    cbed=coarse.bed;fbed=fine.bed
    difference=restrict(fbed,ratio)-cbed
    selected=difference[mask]
    order=np.argsort(np.where(mask,abs(difference),-1).ravel())[-10:][::-1]
    hotspots=[]
    for index in order:
        row,col=np.unravel_index(index,difference.shape)
        hotspots.append({'station_lateral_m':[float(x[row,col]),float(y[row,col])],
            'coarse_sample_bed_m':float(cbed[row,col]),'fine_child_sample_beds_m':fbed[row*ratio:(row+1)*ratio,col*ratio:(col+1)*ratio].tolist(),
            'fine_mean_minus_coarse_m':float(difference[row,col])})
    result={'scope':__doc__.strip(),'source_runs':[p.relative_to(ROOT).as_posix() for p in runs],
        'source_geometry_sha256':registrations[0]['geometry_sha256'],
        'source_bed_sampling':registrations[0].get('bed_sampling','bilinear'),
        'scenario_json_sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in scenario_paths],
        'region_station_lateral_bounds_m':[[-25.5,25.5],[-30.5,30.5]],
        'reference_stage_source':'coarse final common-crux median; frozen diagnostic, not surveyed stage',
        'reference_stage_above_datum_m':reference,
        'bed_sample_mean_difference_p50_p95_max_absolute_m':np.percentile(abs(selected),[50,95,100]).tolist(),
        'hotspots':hotspots,'frozen_stage_capacities':reports,
        'submerged_geometry_measured':False,'resolution_converged':False,'production_promoted':False}
    with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,3,figsize=(14,5),layout='constrained')
    cextent=[coarse.grid.origin_x-coarse.grid.dx/2,coarse.grid.origin_x+(coarse.grid.nx-.5)*coarse.grid.dx,
        coarse.grid.origin_y-coarse.grid.dy/2,coarse.grid.origin_y+(coarse.grid.ny-.5)*coarse.grid.dy]
    grids=[cbed,fbed,difference]
    titles=['1 m cell-centre bed','0.5 m cell-centre bed','Mean fine bed minus coarse sample']
    for index,(ax,grid,title) in enumerate(zip(axes,grids,titles)):
        options={'cmap':'terrain','vmin':4,'vmax':12} if index<2 else {'cmap':'RdBu_r','vmin':-1,'vmax':1}
        mesh=ax.imshow(grid,origin='lower',extent=cextent,interpolation='nearest',**options)
        ax.set(xlim=(-25.5,25.5),ylim=(-30.5,30.5),title=title,xlabel='Downstream station (m)',ylabel='Lateral (m)')
        figure.colorbar(mesh,ax=ax,label='m above datum' if index<2 else 'difference (m)')
    figure.suptitle('Same captured/inferred source triangles; different hydraulic sampling\nNot measured bathymetry or grid-convergence acceptance')
    figure.savefig(args.output.with_suffix('.png'),dpi=140);plt.close(figure)
    print(json.dumps({k:v for k,v in result.items() if k not in ('hotspots','frozen_stage_capacities')},indent=2))


if __name__=='__main__':main()
