"""Replay the actual GPU compatible midpoint transport before terrain contact."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_compatible_advection import sample
from audit_liquid_affine_transfer import shader_text


def audit(directory):
    capture_path=directory/'capture.json';capture=json.loads(capture_path.read_text())
    if not capture['complete'] or capture['error'] or not capture.get('compatible_advection_requested'):
        raise ValueError('Complete compatible-advection capture required')
    stem=f"terrain_{capture['simulation_steps']:04d}"
    path=directory/(stem+'_particles.json');data=json.loads(path.read_text())
    primary=next(e for e in data['emitters'] if e['emitter']=='Grid3D_FLIP_FluidControl_Emitter')
    before=np.asarray(primary['affine_rows']);actual=np.asarray(primary['advection_rows'])
    if before.shape!=(primary['position_count'],16) or actual.shape!=(len(before),8) or not np.isfinite(actual).all() or not np.array_equal(before[:,0],actual[:,0]):
        raise ValueError('Complete finite paired actual GPU identities required')
    fields=load_fields(directory/(stem+'_grids'));grid=fields['Velocity'].transpose(2,1,0,3)
    size=np.array(grid.shape[:3]);extents=np.array([2231.25,2231.25,800]);h=extents/size
    # Use the actually captured GPU sampling coordinates for the initial query.
    q=before[:,13:16].astype(np.float32)*size.astype(np.float32)-np.float32(.5)
    points=(q.astype(float)+.5)*h
    low=np.floor(q-.5).astype(int)-1
    parent=np.clip((q+.5).astype(int),0,size-1)
    boundary=fields['SolidVelocity_Boundary'][parent[:,2],parent[:,1],parent[:,0],3]
    valid=(low>=0).all(axis=1)&(low+4<size).all(axis=1)&(boundary!=1)
    first=np.zeros_like(points);first[valid]=sample(points[valid],grid,h)
    dt=1/(60*capture.get('simulation_substeps_per_frame',1))
    middle=points+.5*dt*first
    middle_low=np.floor(middle/h-1).astype(int)-1
    valid&=(middle_low>=0).all(axis=1)&(middle_low+4<size).all(axis=1)
    expected=np.zeros_like(points);expected[valid]=sample(middle[valid],grid,h)
    mode_matches=np.array_equal(actual[:,7],valid.astype(float))
    # Transport velocities are independent grid replays, not values copied
    # from the GPU's expected result. World/local float32 round trips are
    # allowed 0.05 cm/s and 0.01 cm; no per-capture fitted scale or tolerance.
    velocity_error=abs(expected[valid]-actual[valid,4:7])
    position_error=abs(before[valid,1:4]+dt*expected[valid]-actual[valid,1:4])
    shaders=list((directory/'active_compiled_shaders').glob('*.hlsl'))
    marker=any('RiverCompatibleMidpointAdvection' in shader_text(p.read_bytes()) for p in shaders)
    result=dict(particles=len(before),compatible_particles=int(valid.sum()),fallback_particles=int((~valid).sum()),
        complete_support_mode_matches=mode_matches,compiled_marker=marker,
        velocity_max_error_cm_s=float(velocity_error.max()),position_max_error_cm=float(position_error.max()),
        velocity_tolerance_cm_s=.05,position_tolerance_cm=.01,
        dt_seconds=dt,scope='Precontact primary advection only; foam/secondary interpolation is not yet changed',
        physical_or_visual_acceptance=False)
    result['verified']=bool(mode_matches and marker and valid.any() and velocity_error.max()<=.05 and position_error.max()<=.01)
    result['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [capture_path,path,*sorted((directory/(stem+'_grids')).glob('*')),*shaders] if p.is_file()}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    args=p.parse_args();result=audit(args.directory)
    with (args.directory/'compatible_advection_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
    raise SystemExit(0 if result['verified'] else 1)
