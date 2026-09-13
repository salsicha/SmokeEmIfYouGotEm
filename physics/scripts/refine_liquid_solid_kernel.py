"""Adaptive-order solid-kernel integration on the same captured bed.

Successive-order agreement is a numerical convergence estimate, not a certified
error bound or proof of physical water volume. All unresolved columns are kept.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_density_projection import solid_kernel_fraction,density_target,solve
from liquid_dataset import resolve
from south_fork_registered_mesh import RegisteredMeshSampler


def refine(package,capture,output,tolerance=.001,max_order=64):
    if output.exists():raise FileExistsError(output)
    meta=json.loads((package/'manifest.json').read_text());native=json.loads((capture/'stages.json').read_text())
    if hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest()!=meta['native_stages_sha256']:raise ValueError('Changed native source')
    cells=np.array(meta['cells']);h=np.array(meta['spacing_cm']);axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    arrays={}
    for key,item in meta['files'].items():
        path=(package/item['file']).resolve()
        if path.parent!=package.resolve() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed prepared source')
        channels=3 if key=='displacement_cm' else 4 if key=='boundary' else 1
        arrays[key]=np.fromfile(path,dtype='<f4').reshape((*cells[::-1],channels) if channels>1 else cells[::-1]).astype(float)
    solid=arrays['solid_kernel_fraction'].reshape(cells[2],-1)
    y,x=np.indices((cells[1],cells[0]));xy=(np.column_stack(((x.ravel()+.5)*h[0],(y.ravel()+.5)*h[1]))@axes[:2,:2]+lower[:2])*[1,-1]
    bed_axes=axes[:2,:2]*[1,-1];heights=lower[2]+(np.arange(cells[2])+.5)*h[2]
    dataset=resolve(native)
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    bed=lambda x,y:100*sampler.sample(x/100,y/100)
    selected=np.arange(len(xy));history=[];estimates=np.full(len(xy),np.inf)
    order=8
    while len(selected) and order<=max_order:
        previous=solid[:,selected].copy();new=np.empty_like(previous)
        for first in range(0,len(selected),1024):
            ids=selected[first:first+1024]
            new[:,first:first+len(ids)]=solid_kernel_fraction(bed,xy[ids],heights,h,bed_axes,order)
        difference=abs(new-previous).max(axis=0);estimates[selected]=difference;solid[:,selected]=new
        history.append(dict(order=order,columns=len(selected),maximum_successive_difference=float(difference.max(initial=0)),
            unresolved_columns=int((difference>tolerance).sum())))
        print(json.dumps(history[-1]),flush=True)
        selected=selected[difference>tolerance];order*=2
    arrays['solid_kernel_fraction']=solid.reshape(cells[::-1])
    arrays['target'],stats=density_target(arrays['particle_density'],arrays['solid_kernel_fraction'],arrays['boundary'])
    delta,potential,projection=solve(arrays['particle_density'],arrays['solid_kernel_fraction'],arrays['boundary'],h,max_iterations=500,tolerance=1e-6)
    arrays['displacement_cm']=delta;arrays['potential_cm2']=potential;stats['projection']=projection
    output.mkdir(parents=True);files={}
    for key,a in arrays.items():
        path=output/(key+'.bin');np.asarray(a,dtype='<f4').tofile(path)
        files[key]=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    meta.update(files=files,statistics=stats,solid_quadrature_refinement=history,solid_quadrature_tolerance=tolerance,
        maximum_successive_solid_fraction_difference=float(estimates.max()),unresolved_solid_kernel_columns=len(selected),
        quadrature_is_estimated_not_certified=True,status='converged' if projection['solver']['converged'] else 'unconverged')
    (output/'manifest.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n')
    return dict(status=meta['status'],unresolved_columns=len(selected),maximum_successive_difference=float(estimates.max()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('capture',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--max-order',type=int,default=64);a=p.parse_args()
    print(json.dumps(refine(a.package,a.capture,a.output,max_order=a.max_order),indent=2))
