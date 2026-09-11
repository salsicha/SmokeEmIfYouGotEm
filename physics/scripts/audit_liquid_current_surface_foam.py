"""Compare actual current-surface GPU foam to independent float64 transport.

Predeclared interpolation tolerance: .001 for coverage and source rate.
This verifies bounded transport, not photographic or physical acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from liquid_current_surface_foam import evolve,surface_coverage_statistics
from analyze_liquid_grid_readback import load_fields
from liquid_reconstruction_layout import from_report


def snapshot(path, independent, active):
    report=json.loads((path/'report.json').read_text())
    layout=from_report(report)
    shape=(*layout['render'][::-1],4)
    def read(name, dtype='<f2', dimensions=shape):
        return np.fromfile(path/name,dtype=dtype).reshape(dimensions).astype(float)
    current=read('foam_current.rgba16f');history=read('foam_previous.rgba16f')
    surface=read('surface.rgba16f');audit=read('foam_audit.rgba32f','<f4')
    flow=read('foam_velocity.rgba16f',dimensions=(*layout['solver'][::-1],4))
    boundary=read('boundary.rgba16f',dimensions=(*layout['solver'][::-1],4))
    clock=np.fromfile(path/'clock.rgba32f',dtype='<f4').reshape(-1,4)[-1]
    projected=report.get('current_surface_foam_revision')=='projected-history-v2'
    surface_source=report.get('current_surface_foam_revision')=='surface-strain-v3'
    expected,expected_audit=evolve(current,history,flow,boundary,clock,layout['extent'],half_width=layout['half'],project_history=projected,surface_source=surface_source)
    errors=np.max(abs(audit-expected_audit),axis=(0,1,2))
    coverage_error=float(np.max(abs(surface[...,1]-expected[...,1])))
    native=load_fields(independent)
    metadata=np.array_equal(surface[...,[0,2,3]],current[...,[0,2,3]])
    # Niagara's fourth storage channel is padding, not a velocity component.
    same_flow=np.array_equal(flow[...,:3],native['Velocity'])
    same_boundary=np.array_equal(boundary,native['SolidVelocity_Boundary'])
    pause_identity=np.array_equal(surface[...,1],history[...,1])
    result=dict(clock=clock.tolist(),reconstruction_layout=layout,projected_surface_history=projected,surface_strain_source=surface_source,coverage_max_error=coverage_error,
        audit_max_errors=errors.tolist(),metadata_exact=metadata,
        independent_flow_exact=same_flow,independent_boundary_exact=same_boundary,
        paused_coverage_exact=pause_identity,coverage_max=float(surface[...,1].max()),
        nonzero_source_cells=int((audit[...,0]>0).sum()),
        nonzero_coverage_cells=int((surface[...,1]>0).sum()))
    result['top_surface_coverage']=surface_coverage_statistics(surface)
    result['verified']=bool(np.isfinite(surface).all() and np.isfinite(audit).all()
        and coverage_error<=.001 and errors[0]<=.001 and errors[1]<=.001
        and errors[2]<=1e-7 and errors[3]<=.001 and metadata and same_flow and same_boundary
        and report['current_surface_foam'] and not report['error'] and report['diagnostics']==[0]*4
        and ((clock[1]>0 and result['nonzero_source_cells']>0 and result['nonzero_coverage_cells']>0)
             if active else (clock[1]==0 and pause_identity)))
    result['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(path.iterdir()) if p.is_file()}
    return result


def audit(path):
    capture=json.loads((path/'capture.json').read_text())
    steps=capture['simulation_steps']
    if not isinstance(steps,int) or not 720<=steps<=3600:
        raise ValueError('Bounded actual simulation-step count required')
    active=snapshot(path/'live_foam_active',path/f'terrain_{steps:04d}_grids',True)
    paused=snapshot(path/'live_density',path/'optics_08_grids',False)
    log=path.with_suffix('.log').read_text(errors='replace')
    errors=[line for line in log.splitlines() if re.search(r'\b(?:Error|Fatal):',line)]
    age_matches=abs(active['clock'][0]-steps/60)<=.001 and active['clock'][0]==paused['clock'][0]
    return dict(active=active,paused=paused,engine_errors=errors,simulation_age_matches_requested=age_matches,
        transport_verified=bool(active['verified'] and paused['verified'] and capture['complete']
            and not capture['error'] and not errors and age_matches),physical_or_visual_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('path',type=Path)
    path=parser.parse_args().path;result=audit(path);out=path/'current_foam_audit.json'
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['transport_verified'] else 1)
