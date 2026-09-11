"""Verify the live GPU render-only fluid interior against independent CPU math."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_surface_occupancy import reconcile


def compare(density,boundary,gpu,render_distance,apply_floor=True):
    expected,confidence,parents=reconcile(density,boundary)
    if gpu.shape!=density.shape+(2,) or render_distance.shape!=density.shape:
        raise ValueError('Matching GPU reconstruction domain required')
    phi_error=float(np.max(np.abs(gpu[...,0]-(.5-expected))))
    confidence_error=float(np.max(np.abs(gpu[...,1]-confidence)))
    newly_wet=(density<.5)&(gpu[...,0]<=0)
    false_wet=int((newly_wet&(parents!=0)).sum())
    deep=confidence>=1-1e-12
    selected_phi=gpu[...,0] if apply_floor else .5-density
    sign_mismatch=int(((selected_phi<0)!=(render_distance<0)).sum())
    result=dict(phi_max_error=phi_error,confidence_max_error=confidence_error,
        occupancy_audit_is_control_only=not apply_floor,
        rendered_air_in_fully_supported_interior=int((deep&(render_distance>0)).sum()),
        newly_wet_samples=int(newly_wet.sum()),newly_wet_in_nonfluid_parent_cells=false_wet,
        air_in_fully_supported_interior_before=int((deep&(density<.5)).sum()),
        air_in_fully_supported_interior_after=int((deep&(gpu[...,0]>0)).sum()),
        rendered_sign_mismatches=sign_mismatch,solver_occupancy_floor_applied=apply_floor,
        gpu_cpu_parity=bool(np.isfinite(gpu).all() and np.isfinite(render_distance).all()
            and phi_error<=2e-6 and confidence_error<=1e-6 and false_wet==0 and sign_mismatch==0))
    return result


def audit(path):
    source=path/'live_density'
    report=json.loads((source/'report.json').read_text())
    capture=json.loads((path/'capture.json').read_text())
    shape=(48,136,136)
    density=np.fromfile(source/'density.u32',dtype='<u4').reshape(shape).astype(float)/1048576
    boundary=np.fromfile(source/'boundary.rgba16f',dtype='<f2').reshape(24,68,68,4).astype(float)
    gpu=np.fromfile(source/'occupancy.rg32f',dtype='<f4').reshape(shape+(2,)).astype(float)
    surface=np.fromfile(source/'surface.rgba16f',dtype='<f2').reshape(shape+(4,)).astype(float)
    final_name='benchmark_after' if capture['uninterrupted_benchmark_requested'] else 'optics_08'
    native=load_fields(path/(final_name+'_grids'))['SolidVelocity_Boundary']
    same_classification=np.array_equal(boundary,native)
    particle_only=capture.get('particle_surface_only_requested',False)
    mode_matches=(report.get('particle_surface_only',False)==particle_only and
                  report.get('solver_occupancy_floor_applied',True)==(not particle_only))
    result=compare(density,boundary[...,3],gpu,surface[...,0],apply_floor=not particle_only)
    log=path.with_suffix('.log').read_text(errors='replace')
    errors=[line for line in log.splitlines() if re.search(r'\b(?:Error|Fatal):',line)]
    result.update(live_boundary_matches_independent_grid_readback=same_classification,engine_errors=errors,
        requested_surface_mode_verified=mode_matches,
        gpu_updates=report['gpu_update_count'],diagnostics=report['diagnostics'],
        physical_visual_or_performance_acceptance=False)
    result['live_occupancy_verified']=bool(result['gpu_cpu_parity'] and same_classification and mode_matches and not errors
        and report['live_solver_occupancy_support'] and report['diagnostics']==[0]*4 and not report['error']
        and capture['complete'] and not capture['error'] and report['gpu_update_count']>=714
        and not report['solver_or_particle_state_modified'])
    result['source_sha256']={name:hashlib.sha256((source/name).read_bytes()).hexdigest()
        for name in ('report.json','density.u32','boundary.rgba16f','occupancy.rg32f','surface.rgba16f')}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path)
    args=p.parse_args();result=audit(args.path)
    out=args.path/'occupancy_audit.json'
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
