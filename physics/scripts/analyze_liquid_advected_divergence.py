"""Compare projected grid divergence to actual G2P interpolation derivatives.

An instantaneous kinematic diagnostic, not a measured time-integrated mass loss.
Boundary-adjacent samples are separated from fully fluid interpolation support.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_affine_transfer import velocity_derivative,stencil
from liquid_compatible_projection import divergence
from analyze_liquid_grid_readback import load_fields


def analyze(directory):
    capture_path=directory/'capture.json';capture=json.loads(capture_path.read_text())
    if not capture['complete'] or capture['error']:raise ValueError('Complete capture required')
    stem=f"terrain_{capture['simulation_steps']:04d}"
    path=directory/(stem+'_particles.json');data=json.loads(path.read_text())
    emitter=next(e for e in data['emitters'] if e['emitter']=='Grid3D_FLIP_FluidControl_Emitter')
    rows=np.asarray(emitter['affine_rows']);fields=load_fields(directory/(stem+'_grids'))
    grid=fields['Velocity'].transpose(2,1,0,3);types=fields['SolidVelocity_Boundary'][...,3].transpose(2,1,0)
    shape=np.array(grid.shape[:3]);h=np.array([2231.25,2231.25,800])/shape
    q=rows[:,13:16].astype(np.float32)*shape.astype(np.float32)-np.float32(.5)
    points=(q.astype(float)+.5)*h;quad=capture.get('quadratic_transfer_requested',False)
    low=np.floor(q-(.5 if quad else 0)).astype(int)
    supported=(low>=0).all(axis=1)&(low+(2 if quad else 1)<shape).all(axis=1)
    points=points[supported]
    entirely_fluid=np.ones(len(points),bool)
    for index,_,_,_ in stencil(points,shape,h,quad):entirely_fluid&=types[tuple(index.T)]==0
    jac=velocity_derivative(points,grid,h,quad);tr=np.trace(jac,axis1=1,axis2=2)
    determinant=np.linalg.det(np.eye(3)+jac/60)
    stats=lambda a:dict(count=len(a),rms=float(np.sqrt(np.mean(a*a))),quantiles=np.quantile(a,[0,.01,.1,.5,.9,.99,1]).tolist()) if len(a) else dict(count=0)
    discrete=divergence(fields['Velocity'],h)
    return dict(capture=str(directory),quadratic=quad,fully_fluid_support_count=int(entirely_fluid.sum()),
        projected_grid_divergence_per_s=stats(discrete[fields['SolidVelocity_Boundary'][...,3]==0]),
        interpolated_divergence_per_s=stats(tr),
        interior_interpolated_divergence_per_s=stats(tr[entirely_fluid]),
        interior_one_euler_step_volume_ratio=stats(determinant[entirely_fluid]),
        scope='Instantaneous derivative before terrain contact; volume ratios are local Euler-map Jacobians, not a measured mass budget',
        physical_or_visual_acceptance=False,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [capture_path,path,*sorted((directory/(stem+'_grids')).glob('*'))] if p.is_file()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    args=p.parse_args();result=analyze(args.directory)
    with (args.directory/'advected_divergence.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
