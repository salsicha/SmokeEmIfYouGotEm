"""Prepare an equally sized drop/pool window without moving surveyed terrain.

Rebase coordinates only: preserve every height, face, authority label, hydraulic
array and boundary value. The old review and evidence remain untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler
from build_south_fork_liquid_window import build,write_collision_probes
from audit_south_fork_liquid_flux import main as audit_flux
from build_south_fork_liquid_sources import main as build_sources
from build_south_fork_liquid_initial_state import main as build_initial
from build_south_fork_liquid_contact import main as build_contact
from build_south_fork_liquid_grid_boundary import main as build_boundary

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path,data):
    with path.open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')


def rebase_mesh(data,offset):
    offset=np.asarray(offset,dtype=float)
    if offset.shape!=(2,) or not np.isfinite(offset).all():raise ValueError('Finite east/north translation required')
    result={key:np.array(data[key],copy=True) for key in data.files}
    for key,axis in [('east_m',0),('north_m',1),('nominal_east_axis_m',0),('nominal_north_axis_m',1)]:
        result[key]=np.asarray(data[key],dtype=float)-offset[axis]
    if not all(np.array_equal(result[k],data[k]) for k in result if k not in
        ('east_m','north_m','nominal_east_axis_m','nominal_north_axis_m')):
        raise ValueError('Rebase changed non-coordinate geometry')
    return result


def prepare(work,window,flux_output,station_shift,lateral_shift=2.):
    shift=np.array([station_shift,lateral_shift],dtype=float)
    if not np.isfinite(shift).all() or not np.array_equal(shift,np.round(shift)) or (abs(shift)>20).any():
        raise ValueError('Bounded whole-metre shift required for native-face alignment')
    for path in (work,window,flux_output):
        if path.exists():raise FileExistsError(f'Preserve previous review: {path}')
        if not path.resolve().is_relative_to(ROOT):raise ValueError('Outputs must stay inside the workspace')
    old_geometry=ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907'
    old_work=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907'
    geometry=json.loads((old_geometry/'manifest.json').read_text())
    registration=json.loads((old_work/'registration.json').read_text())
    rotation=np.column_stack([registration['downstream_unit'],registration['left_unit']])
    if not np.allclose(rotation.T@rotation,np.eye(2),atol=1e-9) or np.linalg.det(rotation)<0:
        raise ValueError('Source frame must be rigid and right handed')
    offset=rotation@shift
    original_mesh=ROOT/geometry['mesh_path']
    if sha(original_mesh)!=geometry['mesh_sha256']:raise ValueError('Original captured mesh changed')
    work.mkdir(parents=True);geometry_dir=work/'geometry';geometry_dir.mkdir()
    new_mesh=geometry_dir/'registered_mesh_source.npz'
    with np.load(original_mesh) as source:
        rebased=rebase_mesh(source,offset)
        sampler=RegisteredMeshSampler(rebased)
        original_sampler=RegisteredMeshSampler(source)
        error=float(np.max(abs(sampler.xyz[:,:2]+offset-original_sampler.xyz[:,:2])))
        if error>1e-12:raise ValueError('Translation changed physical XY')
        np.savez_compressed(new_mesh,**rebased)
    new_origin=np.array(geometry['origin_utm_m'])+offset
    geometry.update(parent_mesh_path=str(original_mesh.relative_to(ROOT)),parent_mesh_sha256=sha(original_mesh),
        mesh_path=str(new_mesh.relative_to(ROOT)),mesh_sha256=sha(new_mesh),origin_utm_m=new_origin.tolist(),
        coordinate_rebase_only=True,parent_frame_offset_east_north_m=offset.tolist(),
        physical_xy_roundtrip_max_error_m=error,non_coordinate_arrays_bitwise_identical=True,
        status='recentered_review_candidate_not_new_survey_or_physics')
    write_json(geometry_dir/'manifest.json',geometry)
    engine=work/'engine_review';engine.mkdir()
    old_engine=old_work/'engine_review';flow=json.loads((old_engine/'manifest.json').read_text())
    for band in flow['bands']:
        for record in band['arrays'].values():
            source=old_engine/record['file'];dest=engine/record['file']
            if not dest.resolve().is_relative_to(engine.resolve()):raise ValueError('Unsafe array path')
            if sha(source)!=record['sha256']:raise ValueError('Changed hydraulic source array')
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copyfile(source,dest)
            if sha(dest)!=record['sha256']:raise ValueError('Hydraulic bytes changed during rebase')
    flow['grid']['origin_x_m']-=shift[0];flow['grid']['origin_y_m']-=shift[1]
    flow['review'].update(source_geometry_sha256=geometry['mesh_sha256'],
        source_geometry_manifest=str((geometry_dir/'manifest.json').relative_to(ROOT)),
        coordinate_rebase_only=True,parent_frame_offset_station_lateral_m=shift.tolist(),
        parent_hydraulic_manifest_sha256=sha(old_engine/'manifest.json'))
    write_json(engine/'manifest.json',flow)
    coordinate=json.loads((old_engine/'coordinate_map.json').read_text())
    for point in coordinate['points']:
        point[0]-=shift[0];point[1]-=offset[0];point[2]-=offset[1]
    write_json(engine/'coordinate_map.json',coordinate)
    registration.update(origin_utm_m=new_origin.tolist(),geometry_sha256=geometry['mesh_sha256'],
        coordinate_rebase_only=True,parent_frame_offset_station_lateral_m=shift.tolist(),
        parent_registration_sha256=sha(old_work/'registration.json'))
    write_json(work/'registration.json',registration)
    # The native solver's one-microsecond flux audit uses exactly the same
    # numerical state, shifted coordinates, and unchanged boundary conditions.
    scenario_dir=work/'boundary_flux_audit/scenario';scenario_dir.mkdir(parents=True)
    old_scenario=old_work/'boundary_flux_audit/scenario'
    scenario=json.loads((old_scenario/'scenario.json').read_text())
    scenario['grid']['origin_x']-=shift[0];scenario['grid']['origin_y']-=shift[1]
    if scenario['feature_count']!=0:raise ValueError('Feature coordinates need explicit rebase support')
    for filename in scenario['array_files'].values():
        source=old_scenario/filename;dest=scenario_dir/filename
        if not dest.resolve().is_relative_to(scenario_dir.resolve()):raise ValueError('Unsafe scenario array path')
        if filename=='probes.json':
            probes=json.loads(source.read_text())
            for probe in probes['probes']:
                probe['position']['x']-=shift[0];probe['position']['y']-=shift[1]
            write_json(dest,probes)
        else:shutil.copyfile(source,dest)
    write_json(scenario_dir/'scenario.json',scenario)
    run=json.loads((old_work/'run_result.json').read_text())
    run['coordinate_rebase_only']=True;run['not_a_new_simulation_result']=True
    write_json(work/'run_result.json',run)
    result=build(geometry_dir,engine,window)
    write_collision_probes(window)
    audit_flux(work,flux_output)
    build_sources(window,flux_output)
    build_initial(window);build_contact(window)
    try:
        build_boundary(False,window,flux_output/'report.json')
        build_boundary(True,window,flux_output/'report.json')
    except ValueError as exc:
        write_json(work/'boundary_failure.json',dict(error=str(exc),shift_station_lateral_m=shift.tolist(),
            no_flux_discarded=True,engine_integrated=False,production_promoted=False))
        raise
    control=np.array([-9.,1.])@rotation
    shelf=control+[-2,0];plunge=control+[5,0]
    report=dict(schema='raftsim.recentered_liquid_window.v1',coordinate_rebase_only=True,
        shift_station_lateral_m=shift.tolist(),shift_east_north_m=offset.tolist(),
        original_hypothesized_shelf_station_lateral_m=shelf.tolist(),
        original_hypothesized_plunge_station_lateral_m=plunge.tolist(),
        new_hypothesized_shelf_station_lateral_m=(shelf-shift).tolist(),
        new_hypothesized_plunge_station_lateral_m=(plunge-shift).tolist(),
        physical_bounds_m=[[-10.5,-10.5],[10.5,10.5]],
        physical_xy_roundtrip_max_error_m=error,all_heights_topology_authority_unchanged=True,
        hydraulic_array_bytes_unchanged=True,not_a_new_hydraulic_solve=True,
        local_origin_engine_cm=result['local_origin_engine_cm'],window=str(window.relative_to(ROOT)),
        native_flux_report_sha256=sha(flux_output/'report.json'),
        submerged_control_measured=False,engine_integrated=False,production_promoted=False)
    write_json(work/'recenter_review.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--window',type=Path,required=True)
    # Midpoint of the two controls rounds to station/lateral (10,2) metres,
    # retaining exact native-face alignment and room on both sides of the drop.
    parser.add_argument('--flux-output',type=Path,required=True);parser.add_argument('--station-shift',type=float,default=10)
    parser.add_argument('--lateral-shift',type=float,default=2)
    args=parser.parse_args()
    print(json.dumps(prepare(args.work.resolve(),args.window.resolve(),args.flux_output.resolve(),args.station_shift,args.lateral_shift),indent=2))
