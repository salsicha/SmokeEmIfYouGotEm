"""Export native numerical face fluxes for a conservative 3D crux handoff."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/src'))
from raftsim.scenario2_5d import read_scenario2_5d_package


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def control_volume_indices(grid,bounds):
    bounds=np.asarray(bounds,dtype=float)
    if bounds.shape!=(2,2) or not np.isfinite(bounds).all() or (bounds[1]<=bounds[0]).any():
        raise ValueError('Finite nonempty station/lateral face bounds required')
    origin=np.array([grid.origin_x,grid.origin_y]);spacing=np.array([grid.dx,grid.dy])
    indices=(bounds-origin)/spacing+.5
    if not np.allclose(indices,np.rint(indices),rtol=0,atol=1e-9):
        raise ValueError('Control volume must align exactly to native finite-volume faces')
    indices=np.rint(indices).astype(int)
    if (indices[0]<0).any() or (indices[1]>[grid.nx,grid.ny]).any():
        raise ValueError('Control volume extends outside the native source grid')
    return tuple(int(v) for v in indices.ravel())


def main(work=None,output=None,bounds=((-10.5,-10.5),(10.5,10.5))):
    work=Path(work) if work is not None else ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907'
    output=Path(output) if output is not None else ROOT/'docs/reconstruction-review-2026-09-07/liquid-native-face-flux'
    if output.exists(): raise FileExistsError('Preserve the previous audit')
    source=work/'boundary_flux_audit/scenario'
    scenario=read_scenario2_5d_package(source)
    engine=work/'engine_review'
    manifest=json.loads((engine/'manifest.json').read_text())
    for name,array in {'h':scenario.initial_state.depth,'u':scenario.initial_state.u,
                       'v':scenario.initial_state.v,'bed':scenario.bed}.items():
        record=manifest['bands'][0]['arrays'][name]
        path=engine/record['file']
        if sha(path)!=record['sha256'] or not np.array_equal(array.astype(np.float32),np.load(path)):
            raise ValueError(f'Native endpoint does not match engine package: {name}')
    solver=ROOT/'tmp/south-fork-liquid-flux-build-20260908/Release/raftsim_water_solver.exe'
    run=json.loads((work/'run_result.json').read_text())
    command=list(run['command']);command[0]=str(solver)
    command[command.index('--scenario')+1]=str(source)
    output.mkdir(exist_ok=False)
    command[command.index('--output')+1]=str(output/'tiny_step')
    command[command.index('--steps')+1]='1'
    command[command.index('--frame-interval')+1]='1'
    inspected=subprocess.run([*command,'--inspect-face-fluxes'],capture_output=True,text=True,check=True)
    (output/'native_faces.json').write_text(inspected.stdout)
    faces=json.loads(inspected.stdout)
    grid=scenario.grid
    if faces['nx']!=grid.nx or faces['ny']!=grid.ny or faces['units']!='m2/s':
        raise ValueError('Face grid mismatch')
    qx=np.array(faces['x_faces']).reshape(grid.ny,grid.nx+1)
    qy=np.array(faces['y_faces']).reshape(grid.ny+1,grid.nx)
    if not np.isfinite(qx).all() or not np.isfinite(qy).all(): raise ValueError('Nonfinite flux')
    # A whole rapid can be rectangular/off-centre; never round a requested
    # physical boundary onto a different numerical face silently.
    c0,r0,c1,r1=control_volume_indices(grid,bounds)
    sides={'west':qx[r0:r1,c0]*grid.dy,'east':-qx[r0:r1,c1]*grid.dy,
           'south':qy[r0,c0:c1]*grid.dx,'north':-qy[r1,c0:c1]*grid.dx}
    net=float(sum(a.sum() for a in sides.values()))
    stepped=subprocess.run(command,capture_output=True,text=True,check=True)
    (output/'tiny_step_stdout.txt').write_text(stepped.stdout)
    final=np.genfromtxt(output/'tiny_step/survey_final_state_flux_audit/frames/frame_0001.csv',delimiter=',',names=True)
    h1=final['h'].reshape(grid.ny,grid.nx)
    h0=scenario.initial_state.depth
    if scenario.fixed_dt!=1e-6: raise ValueError('Expected existing one-microsecond conservative audit package')
    measured=float((h1[r0:r1,c0:c1]-h0[r0:r1,c0:c1]).sum()*grid.dx*grid.dy/scenario.fixed_dt)
    error=abs(measured-net)
    np.savez_compressed(output/'native_faces.npz',x_faces_m2s=qx,y_faces_m2s=qy)
    checks={'control_volume_matches_tiny_step_storage_derivative':error<1e-3,
            'finite_face_fluxes':bool(np.isfinite(qx).all() and np.isfinite(qy).all())}
    report={'scope':'Native finite-volume face flux and local storage audit, not calibrated real-river discharge',
            'source_geometry_sha256':manifest['review']['source_geometry_sha256'],
            'source_hydraulic_manifest_sha256':sha(engine/'manifest.json'),
            'source_scenario_sha256':sha(source/'scenario.json'),
            'solver_binary_sha256':sha(solver),'faces_sha256':sha(output/'native_faces.npz'),
            'local_station_lateral_face_bounds_m':np.asarray(bounds,dtype=float).tolist(),
            'sign':'positive_into_control_volume',
            'face_discharge_m3_per_s':{k:v.tolist() for k,v in sides.items()},
            'net_numerical_inflow_m3_per_s':net,
            'measured_volume_derivative_m3_per_s':measured,
            'absolute_conservation_error_m3_per_s':error,
            'checks':checks,'passed':all(checks.values()),
            'previous_interpolated_20m_boundary_replaced':False,
            'engine_3d_coupled':False,'production_promoted':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='face_discharge_m3_per_s'},indent=2))
    if not report['passed']: raise SystemExit(1)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--bounds',type=float,nargs=4,default=(-10.5,-10.5,10.5,10.5),
                        metavar=('MIN_STATION','MIN_LATERAL','MAX_STATION','MAX_LATERAL'))
    args=parser.parse_args()
    main(args.work,args.output,np.array(args.bounds).reshape(2,2))
