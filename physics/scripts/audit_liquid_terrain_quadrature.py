"""Bounded captured-state comparison of scalar-only and exact-bed quadrature.

This audit does not move particles or change terrain/surface data. Selected
columns are deterministic, with their coordinates, gradients and convergence
retained. A bounded sample cannot accept the complete South Fork surface.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from liquid_terrain_volume_gradient import evaluate_bed_columns
from liquid_adaptive_terrain_volume import adaptive_bed_columns
from liquid_split_volume_gradient import evaluate_columns
from liquid_bed_ray_intervals import bed_ray_intervals
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_dataset import resolve


def run(package,output,*,count=64,adaptive=False):
    started=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if output.exists():raise FileExistsError(output)
    if count<1:raise ValueError('Positive column count required')
    report=json.loads((package/'report.json').read_text());geometry=Path(report['geometry_package'])
    capture=Path(report['native_capture']);native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    for path,digest in ((geometry/'manifest.json',report['geometry_manifest_sha256']),
                       (package/'state.npz',report['state_sha256']),(dataset['mesh'],report['registered_mesh_sha256']),
                       (capture/'stages.json',report['native_stages_sha256'])):
        if sha(path)!=digest:raise ValueError('Captured seed provenance changed')
    g=json.loads((geometry/'manifest.json').read_text());h=np.array(g['spacing_cm'])/100;axes=np.array(g['world_axes'])
    origin=np.array(g['world_lower_cm'])/100;cells=np.array(g['cells'])
    with np.load(package/'state.npz') as data:phi=data['phi']/100
    with np.load(dataset['mesh']) as data:sampler=RegisteredMeshSampler(data)
    names=['audit_liquid_terrain_quadrature.py','liquid_terrain_volume_gradient.py','liquid_split_volume_gradient.py','liquid_adaptive_terrain_volume.py',
           'liquid_bed_ray_intervals.py','liquid_bed_contour_intervals.py','liquid_surface_volume_gradient.py',
           'liquid_interface_volume.py','south_fork_registered_mesh.py']
    sources={n:(Path(__file__).parent/n).read_bytes() for n in names};output.mkdir(parents=True);(output/'sources').mkdir()
    for n,b in sources.items():(output/'sources'/n).write_bytes(b)
    def bed(xy):
        world=xy@axes[:2,:2]+origin[:2]
        return sampler.sample(world[:,0],-world[:,1])-origin[2]
    def segments(a,b):
        world_a=(a@axes[:2,:2]+origin[:2])*[1,-1];world_b=(b@axes[:2,:2]+origin[:2])*[1,-1]
        row,lo,hi,z0,z1=bed_ray_intervals(sampler,world_a,world_b)
        return row,lo,hi,z0-origin[2],z1-origin[2]
    # Interior full cells. Bias to bed/surface contact columns without changing
    # data: include all cases, then pick a reproducible stratified subset.
    y,x=np.mgrid[2:cells[1]-3,2:cells[0]-3];lower=np.column_stack((x.ravel(),y.ravel()))
    centers=(lower+1)*h[:2];half=np.broadcast_to(h[:2]/2,centers.shape).copy()
    corners=np.stack([phi[:,lower[:,1]+cy,lower[:,0]+cx].T for cx,cy in ((0,0),(1,0),(0,1),(1,1))],axis=-1)
    mixed=np.any((corners.min(axis=2)<0)&(corners.max(axis=2)>0),axis=1)
    candidate=np.flatnonzero(mixed)
    if not len(candidate):raise ValueError('No contour-changing columns in captured sample')
    pick=candidate[np.unique(np.linspace(0,len(candidate)-1,min(count,len(candidate))).astype(int))]
    corners=corners[pick];lower=lower[pick];centers=centers[pick];half=half[pick]
    records=[];previous=None;arrays=dict(lower_xy=lower,centers_xy=centers,half_extent_xy=half)
    adaptive_proof=None
    if adaptive:
        v,gradient,diagnostics,adaptive_proof=adaptive_bed_columns(corners,lower,centers,half,h,segments,
            progress=lambda r:print(json.dumps(r),flush=True))
        arrays.update(diagnostics);arrays.update(adaptive_volume=v,adaptive_gradient=gradient);previous=(v,gradient)
        records.append(dict(order=None,unresolved_columns=adaptive_proof['unresolved_columns'],volume_m3=float(v[:,0].sum())))
    for order in (() if adaptive else (2,4,8,16,32,64,128)):
        v,gradient,detail=evaluate_bed_columns(corners,lower,centers,half,h,segments,order)
        vd=None if previous is None else np.max(abs(v-previous[0]),axis=1)
        gd=None if previous is None else np.max(abs(gradient-previous[1]),axis=(1,2))
        r=dict(order=order,volume_m3=float(v[:,0].sum()),volume_difference_max=None if vd is None else float(vd.max()),
               gradient_difference_max=None if gd is None else float(gd.max()),
               unresolved_columns=None if vd is None else int(((vd>1e-4)|(gd>1e-4)).sum()),
               elapsed_seconds=time.perf_counter()-started,**detail)
        records.append(r);print(json.dumps(r),flush=True)
        arrays[f'volume_{order}']=v;arrays[f'gradient_{order}']=gradient
        previous=(v,gradient)
        if r['unresolved_columns']==0:break
    # Independent scalar-only tensor/ray partition on the same immutable cells.
    reference,ref_gradient,ref_detail=evaluate_columns(corners,lower,centers,half,h,bed,32)
    arrays['scalar_only_volume_32']=reference;arrays['scalar_only_gradient_32']=ref_gradient
    np.savez_compressed(output/'columns.npz',**arrays)
    result=dict(schema='raftsim.terrain_quadrature_sample.v1',seed_package=str(package),seed_report_sha256=sha(package/'report.json'),
        selected_columns=len(pick),candidate_columns=len(candidate),orders=records,adaptive=adaptive,adaptive_proof=adaptive_proof,
        final_unresolved_columns=records[-1]['unresolved_columns'],scalar_only_comparison_order=32,
        scalar_only_volume_difference_max=float(np.max(abs(reference-previous[0]))),
        scalar_only_gradient_difference_max=float(np.max(abs(ref_gradient-previous[1]))),
        columns_sha256=sha(output/'columns.npz'),sources_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
        sources_unchanged=all((Path(__file__).parent/n).read_bytes()==b for n,b in sources.items()),
        full_surface_accepted=False,physical_visual_or_performance_acceptance=False,elapsed_seconds=time.perf_counter()-started)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--count',type=int,default=64);p.add_argument('--adaptive',action='store_true')
    a=p.parse_args();r=run(a.package,a.output,count=a.count,adaptive=a.adaptive)
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['final_unresolved_columns']==0 and r['sources_unchanged'] else 1)
