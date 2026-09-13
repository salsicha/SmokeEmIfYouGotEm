"""Independent core/buffer/outer control-volume balance from native face fluxes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/src'))
from raftsim.scenario2_5d import read_scenario2_5d_package


def balance(qx, qy, core, outer):
    qx,qy=np.asarray(qx,dtype=float),np.asarray(qy,dtype=float)
    core,outer=np.asarray(core),np.asarray(outer)
    if (qx.ndim!=2 or qy.shape!=(qx.shape[0]+1,qx.shape[1]-1) or
        not np.isfinite(qx).all() or not np.isfinite(qy).all() or
        any(p.shape!=(2,2) or not np.issubdtype(p.dtype,np.integer) for p in (core,outer)) or
        np.any(outer[0]<0) or np.any(outer[1]>[qx.shape[1]-1,qx.shape[0]]) or
        np.any(core[0]<=outer[0]) or np.any(core[1]>=outer[1]) or np.any(core[1]<=core[0])):
        raise ValueError('Finite staggered fluxes and a strictly nested nonempty core required')
    def net(box):
        (x0,y0),(x1,y1)=box
        return float(qx[y0:y1,x0].sum()-qx[y0:y1,x1].sum()+
                     qy[y0,x0:x1].sum()-qy[y1,x0:x1].sum())
    # This independent cell sum includes every corner once. Internal face
    # cancellation is verified against the two complete boundary integrals.
    mask=np.zeros((qx.shape[0],qx.shape[1]-1),dtype=bool)
    (x0,y0),(x1,y1)=outer;mask[y0:y1,x0:x1]=True
    (x0,y0),(x1,y1)=core;mask[y0:y1,x0:x1]=False
    cell_gain=qx[:,:-1]-qx[:,1:]+qy[:-1,:]-qy[1:,:]
    core_net,outer_net=net(core),net(outer)
    return dict(core_inflow=core_net,outer_inflow=outer_net,
        buffer_inflow=outer_net-core_net,buffer_cell_gain=float(cell_gain[mask].sum())),mask


def audit(core_dir,outer_dir,work):
    core_dir,outer_dir,work=map(Path,(core_dir,outer_dir,work))
    read=lambda p:json.loads(p.read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    reports=[read(p/'report.json') for p in (core_dir,outer_dir)]
    for k in ('source_geometry_sha256','source_hydraulic_manifest_sha256',
              'source_scenario_sha256','solver_binary_sha256','faces_sha256'):
        if reports[0][k]!=reports[1][k]:raise ValueError('Core and buffer use different source state: '+k)
    for directory,report in zip((core_dir,outer_dir),reports):
        if sha(directory/'native_faces.npz')!=report['faces_sha256']:
            raise ValueError('Native face bytes changed')
    scenario_dir=work/'boundary_flux_audit/scenario'
    if sha(scenario_dir/'scenario.json')!=reports[0]['source_scenario_sha256']:
        raise ValueError('Original native state changed')
    scenario=read_scenario2_5d_package(scenario_dir);grid=scenario.grid
    if scenario.fixed_dt!=1.e-6:raise ValueError('Use the original independently stepped microsecond audit')
    bounds=[]
    for report in reports:
        indices=(np.asarray(report['local_station_lateral_face_bounds_m'])-
                 [grid.origin_x,grid.origin_y])/[grid.dx,grid.dy]+.5
        if not np.allclose(indices,np.rint(indices),rtol=0,atol=1e-9):
            raise ValueError('Physical interface is not an original numerical face')
        bounds.append(np.rint(indices).astype(int))
    with np.load(outer_dir/'native_faces.npz') as data:
        result,mask=balance(data['x_faces_m2s']*grid.dy,data['y_faces_m2s']*grid.dx,*bounds)
    frame=outer_dir/'tiny_step/survey_final_state_flux_audit/frames/frame_0001.csv'
    after=np.genfromtxt(frame,delimiter=',',names=True)['h'].reshape(grid.ny,grid.nx)
    before=scenario.initial_state.depth
    if not np.isfinite(after).all():raise ValueError('Nonfinite actual native step')
    measured=float((after-before)[mask].sum()*grid.dx*grid.dy/scenario.fixed_dt)
    if (abs(result['core_inflow']-reports[0]['net_numerical_inflow_m3_per_s'])>1.e-10 or
        abs(result['outer_inflow']-reports[1]['net_numerical_inflow_m3_per_s'])>1.e-10):
        raise ValueError('Boundary report disagrees with original numerical faces')
    checks=dict(interface_flux_cancels=abs(result['buffer_inflow']-result['buffer_cell_gain'])<1.e-10,
        actual_buffer_storage_matches_signed_exchange=abs(measured-result['buffer_inflow'])<1.e-3)
    if not all(checks.values()):raise ValueError('Native buffer control-volume balance failed: '+str(result))
    return dict(schema='raftsim.liquid_reservoir_flux_audit.v1',
        source_geometry_sha256=reports[0]['source_geometry_sha256'],
        source_hydraulic_manifest_sha256=reports[0]['source_hydraulic_manifest_sha256'],
        core_flux_report_sha256=sha(core_dir/'report.json'),outer_flux_report_sha256=sha(outer_dir/'report.json'),
        actual_native_frame_sha256=sha(frame),buffer_cell_count=int(mask.sum()),
        flux_m3_per_s=result,measured_buffer_storage_derivative_m3_per_s=measured,
        absolute_buffer_conservation_error_m3_per_s=abs(measured-result['buffer_inflow']),
        checks=checks,passed=True,engine_backflow_verified=False,
        scope='Native finite-volume core/buffer exchange only; not a FLIP run, calibration or scene acceptance')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('core',type=Path);p.add_argument('outer',type=Path);p.add_argument('work',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    report=audit(a.core,a.outer,a.work)
    with a.output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
