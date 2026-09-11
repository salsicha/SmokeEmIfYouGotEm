"""Test real Cartesian geometry; rigid rotation only, no unrolled river warp."""
from pathlib import Path
import sys
import json
import argparse
import hashlib
import re
import runpy
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/src'))
import numpy as np
import rasterio
from scipy.ndimage import map_coordinates
from raftsim.scenario2_5d import (GridSpec2_5D,Scenario2_5D,ScenarioMetadata2_5D,
    InitialWaterState2_5D,BoundaryCondition2_5D,Probe2_5D)
from raftsim.dual_solver import run_cpp_solver_scenario,CppSolverRunConfig

BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def physical_grid(cell):
    """Keep the cell-edge domain identical during resolution comparisons."""
    if not np.isfinite(cell) or cell <= 0 or cell > 1:
        raise ValueError('Cell size must be finite and in (0, 1] metres')
    nx,ny=round(271/cell),round(161/cell)
    if abs(nx*cell-271)>1e-8 or abs(ny*cell-161)>1e-8:
        raise ValueError('Cell size must divide the fixed physical domain')
    return GridSpec2_5D(nx=nx,ny=ny,dx=cell,dy=cell,
        origin_x=-135.5+.5*cell,origin_y=-80.5+.5*cell)


def refinement_boundaries(scenario,parent,registration,*,boundary_mode,cfl,solver_sha):
    """Change resolution, not the experiment's forcing or numerical settings."""
    target=scenario.metadata.provenance['target_discharge_m3s']
    if (registration['boundary_mode']!=boundary_mode or registration['cfl']!=cfl or
        registration['solver_binary_sha256']!=solver_sha or
        registration['target_discharge_m3s']!=target or
        registration.get('bed_sampling','bilinear')!=scenario.metadata.provenance.get('bed_sampling','bilinear') or
        parent.fixed_dt!=scenario.fixed_dt or parent.roughness!=scenario.roughness):
        raise ValueError('Refinement forcing, solver, dt, CFL or roughness differs from parent')
    return parent.boundaries


def refined_initial_state(scenario, parent_work, geometry_sha,*,boundary_mode,cfl,solver_sha):
    """Warm start only: retain the finer bed, and never interpolate dry-bank eta.

    This is not a conservative solver step or a converged result. The measured
    initial storage change is recorded and the refined solve must settle again.
    """
    from raftsim.scenario2_5d import read_scenario2_5d_package
    parent_work=parent_work.resolve()
    registration=json.loads((parent_work/'registration.json').read_text())
    if registration['geometry_sha256']!=geometry_sha:
        raise ValueError('Refinement source geometry differs')
    if not np.allclose(registration['downstream_unit'],[-.9299998355760436,.36755993501540923],atol=1e-12):
        raise ValueError('Refinement source coordinate axes differ')
    parent=read_scenario2_5d_package(next((parent_work/'scenario').iterdir()))
    boundaries=refinement_boundaries(scenario,parent,registration,
        boundary_mode=boundary_mode,cfl=cfl,solver_sha=solver_sha)
    expected=physical_grid(parent.grid.dx)
    keys=('nx','ny','dx','dy','origin_x','origin_y')
    if any(getattr(parent.grid,k)!=getattr(expected,k) for k in keys) or parent.grid.dx<=scenario.grid.dx:
        raise ValueError('Refinement needs a coarser grid with the same physical bounds')
    result=json.loads((parent_work/'run_result.json').read_text())
    output=ROOT/result['output_dir']
    frames=json.loads((output/'manifest.json').read_text())['frames']
    frame=output/frames[-1]
    validate=runpy.run_path(str(ROOT/'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))['validated_frame_state']
    state=validate(parent,np.genfromtxt(frame,delimiter=',',names=True))
    x,y=scenario.grid.meshgrid()
    indices=[(y-parent.grid.origin_y)/parent.grid.dy,(x-parent.grid.origin_x)/parent.grid.dx]
    wet=state.depth>1e-4
    weight=map_coordinates(wet.astype(float),indices,order=1,mode='nearest')
    def interpolate(value):
        return map_coordinates(np.where(wet,value,0),indices,order=1,mode='nearest')/np.maximum(weight,1e-12)
    eta=interpolate(parent.bed+state.depth)
    h=np.where(weight>.01,np.maximum(eta-scenario.bed,0),0)
    initial=InitialWaterState2_5D.from_depth_velocity(scenario.bed,h,interpolate(state.u),interpolate(state.v))
    parent_volume=float(state.depth.sum()*parent.grid.dx*parent.grid.dy)
    refined_volume=float(h.sum()*scenario.grid.dx*scenario.grid.dy)
    return initial,{'source_frame':str(frame.relative_to(ROOT)),
        'source_frame_sha256':hashlib.sha256(frame.read_bytes()).hexdigest(),
        'parent_cell_m':parent.grid.dx,'parent_volume_m3':parent_volume,
        'refined_initial_volume_m3':refined_volume,'storage_change_m3':refined_volume-parent_volume,
        'method':'wet-weighted stage/velocity interpolation onto unchanged finer bed; must re-equilibrate',
        'forcing_inherited_unchanged':True,
        'inherited_boundaries':[b.to_json_dict() for b in boundaries]},boundaries


def sample(path,east,north,order=1):
    with rasterio.open(path) as ds:
        col,row=(~ds.transform)*(east,north)
        result=map_coordinates(ds.read(1).astype(float),[row-.5,col-.5],order=order,mode='constant',cval=np.nan)
    if not np.isfinite(result).all():
        raise ValueError(f'Hydraulic domain outside captured geometry: {path}')
    return result


def validate_continuation_layout(scenario,parent,registration,geometry_sha):
    if registration['geometry_sha256']!=geometry_sha:
        raise ValueError('Continuation source geometry differs')
    if (parent.grid!=scenario.grid or not np.array_equal(parent.bed,scenario.bed) or
        not np.allclose(registration['downstream_unit'],[-.9299998355760436,.36755993501540923],atol=1e-12,rtol=0)):
        raise ValueError('Continuation requires unchanged grid, bed and axes')
    if any(b.hydrograph for b in parent.boundaries):
        raise ValueError('Clock-reset continuation requires constant boundaries')


def continuation_initial_state(scenario,parent_work,geometry_sha,*,boundary_mode,cfl,solver_sha):
    """Resume conserved state and forcing; never re-seed or resample boundaries."""
    from raftsim.scenario2_5d import read_scenario2_5d_package
    parent_work=parent_work.resolve()
    registration=json.loads((parent_work/'registration.json').read_text())
    parent=read_scenario2_5d_package(next((parent_work/'scenario').glob('*/scenario.json')))
    validate_continuation_layout(scenario,parent,registration,geometry_sha)
    boundaries=refinement_boundaries(scenario,parent,registration,
        boundary_mode=boundary_mode,cfl=cfl,solver_sha=solver_sha)
    result=json.loads((parent_work/'run_result.json').read_text())
    folder=ROOT/result['output_dir']
    frame=folder/json.loads((folder/'manifest.json').read_text())['frames'][-1]
    validate=runpy.run_path(str(ROOT/'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))['validated_frame_state']
    from south_fork_survey_sanity import check_frame
    # Check the chosen resume frame independently of the generic native flag.
    raw=np.genfromtxt(frame,delimiter=',',names=True)
    if not check_frame(raw)['passed']:
        raise ValueError('Continuation source fails survey sanity bounds')
    initial=validate(parent,raw)
    return initial,{'source_run':parent_work.relative_to(ROOT).as_posix(),
        'source_frame':frame.relative_to(ROOT).as_posix(),
        'source_frame_sha256':hashlib.sha256(frame.read_bytes()).hexdigest(),
        'source_registration_sha256':hashlib.sha256((parent_work/'registration.json').read_bytes()).hexdigest(),
        'method':'conserved-state restart with unchanged bed and constant forcing; internal clock restarts',
        'forcing_inherited_unchanged':True},boundaries


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--cell',type=float,default=1.)
    parser.add_argument('--steps',type=int,default=6000)
    parser.add_argument('--mixed-inlet',action='store_true')
    parser.add_argument('--label',default='')
    initialization=parser.add_mutually_exclusive_group()
    initialization.add_argument('--resume-frame',type=Path)
    initialization.add_argument('--refine-from-run',type=Path)
    initialization.add_argument('--continue-from-run',type=Path)
    parser.add_argument('--binary',type=Path,default=ROOT/'tmp/troublemaker-solver-dry-cull-release/raftsim_water_solver.exe')
    parser.add_argument('--dt',type=float,default=.1)
    parser.add_argument('--cfl',type=float,default=.38)
    parser.add_argument('--geometry-dir',type=Path,default=BASE/'troublemaker/geometry_candidate')
    parser.add_argument('--bed-sampling',choices=('bilinear','render_triangles','registered_triangles'))
    args=parser.parse_args()
    from south_fork_mesh_sampling import select_bed_sampling
    parent_work=args.continue_from_run or args.refine_from_run
    parent_registration=json.loads((parent_work/'registration.json').read_text()) if parent_work else None
    args.bed_sampling=select_bed_sampling(args.bed_sampling,parent_registration,bool(args.resume_frame))
    if not np.isfinite(args.dt) or args.dt<=0 or not np.isfinite(args.cfl) or not 0<args.cfl<=.45:
        raise ValueError('Diagnostic dt must be positive and CFL must be in (0, .45]')
    if args.geometry_dir.resolve() != (BASE/'troublemaker/geometry_candidate').resolve() and not args.label:
        raise ValueError('Alternate geometry requires a unique diagnostic label')
    from south_fork_geometry_source import geometry_identity, require_sampling_kind, load_registered_mesh
    manifest,geometry_path,geometry_sha,registered=geometry_identity(args.geometry_dir/'manifest.json',ROOT)
    require_sampling_kind(registered,args.bed_sampling)
    cell=args.cell
    grid=physical_grid(cell)
    x,y=grid.meshgrid()
    direction=np.array([-.93,.36756]); direction/=np.linalg.norm(direction)
    left=np.array([-direction[1],direction[0]])
    center=np.asarray(manifest['origin_utm_m'])
    east=center[0]+direction[0]*x+left[0]*y
    north=center[1]+direction[1]*x+left[1]*y
    datum=manifest['vertical_origin_navd88_m']
    if registered:
        _,sampler=load_registered_mesh(geometry_path)
        bed=sampler.sample(east-center[0],north-center[1])
    elif args.bed_sampling=='render_triangles':
        from south_fork_mesh_sampling import sample_mesh_raster
        bed=sample_mesh_raster(geometry_path,east,north)-datum
    else:
        bed=sample(geometry_path,east,north)-datum
    surface=sample(BASE/'troublemaker/survey_surface_navd88_m.tif',east,north)-datum
    wet=sample(BASE/'troublemaker/unknown_submerged_bed_mask.tif',east,north,0)==1
    if wet[0].any() or wet[-1].any():
        raise ValueError('Channel crosses side boundary; expand physical domain, do not wall off the river')
    if not wet[:,0].any() or not wet[:,-1].any():
        raise ValueError('Missing real inlet/outlet in hydraulic domain')
    depth=np.where(wet,np.maximum(surface-bed,0),0)
    q=45.3069545472
    area=np.sum(depth,axis=0)*cell
    if np.min(area)<.1:
        raise ValueError('Disconnected initial wet cross section')
    # Match the conveyance-weighted discharge inlet. A uniform velocity would
    # initialize nearly dry bank cells supercritical despite a subcritical
    # main channel, violating the one-characteristic boundary's contract.
    conveyance=np.sum(depth**(5./3.),axis=0)*cell
    u=np.where(depth>1e-6,q*depth**(2./3.)/conveyance[None,:],0)
    v=np.zeros_like(u)
    state=InitialWaterState2_5D.from_depth_velocity(bed,depth,u,v)
    inlet=float(np.median(surface[wet[:,0],0])); outlet=float(np.median(surface[wet[:,-1],-1]))
    scenario=Scenario2_5D(metadata=ScenarioMetadata2_5D(
        scenario_id=f'troublemaker_survey_candidate_{cell:g}m',scenario_type='real_world',
        description='Captured banks and recovered exposed rock, inferred underwater bed; not accepted reconstruction',
        coordinate_reference_system='Rigid local Cartesian metres from EPSG:32610; no station/lateral deformation',
        confidence_score=.3,provenance={'geometry_sha256':geometry_sha,
            'bed_sampling':args.bed_sampling,
            'bathymetry_authority':'explicitly inferred','target_discharge_m3s':q,'production_promoted':False}),
        grid=grid,fixed_dt=args.dt,duration=args.steps*args.dt,bed=bed,initial_state=state,
        boundaries=(BoundaryCondition2_5D('west','inflow',stage=inlet,velocity=(q/area[0],0),
            metadata={'target_discharge_m3s':q}),BoundaryCondition2_5D('east','outflow',stage=outlet),
            BoundaryCondition2_5D('north','bank'),BoundaryCondition2_5D('south','bank')),
        probes=(Probe2_5D('inlet',(-130,0)),Probe2_5D('crux',(8,0)),Probe2_5D('outlet',(130,0))),roughness=.035)
    if not scenario.validate().passed:
        raise ValueError(scenario.validate().summary_lines())
    refinement=None
    continuation=None
    if args.refine_from_run:
        if args.resume_frame: raise ValueError('Choose refinement or same-grid resume, not both')
        initial,refinement,boundaries=refined_initial_state(scenario,args.refine_from_run,geometry_sha,
            boundary_mode='mixed_characteristic_discharge' if args.mixed_inlet else 'stage_velocity',
            cfl=args.cfl,solver_sha=hashlib.sha256(args.binary.read_bytes()).hexdigest())
        # Recomputing median boundary stage at finer cell centres subtly
        # changed head as well as resolution. Preserve the parent forcing.
        scenario=replace(scenario,initial_state=initial,boundaries=boundaries)
        inlet=next(b.stage for b in boundaries if b.edge=='west')
        outlet=next(b.stage for b in boundaries if b.edge=='east')
    if args.continue_from_run:
        initial,continuation,boundaries=continuation_initial_state(scenario,args.continue_from_run,geometry_sha,
            boundary_mode='mixed_characteristic_discharge' if args.mixed_inlet else 'stage_velocity',
            cfl=args.cfl,solver_sha=hashlib.sha256(args.binary.read_bytes()).hexdigest())
        scenario=replace(scenario,initial_state=initial,boundaries=boundaries)
        inlet=next(b.stage for b in boundaries if b.edge=='west')
        outlet=next(b.stage for b in boundaries if b.edge=='east')
    if args.resume_frame:
        validate=runpy.run_path(str(ROOT/'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))['validated_frame_state']
        initial=validate(scenario,np.genfromtxt(args.resume_frame,delimiter=',',names=True))
        scenario=replace(scenario,initial_state=initial)
    work=ROOT/f'tmp/south-fork-survey-hydraulics/{cell:g}m'
    if args.mixed_inlet: work=work.with_name(work.name+'-mixed-inlet')
    if args.label:
        if not re.fullmatch('[a-z0-9-]+',args.label): raise ValueError('Label must be lowercase alphanumeric/hyphens')
        work=work.with_name(work.name+'-'+args.label)
    work.mkdir(parents=True,exist_ok=False)
    registration={'origin_utm_m':center.tolist(),'downstream_unit':direction.tolist(),'left_unit':left.tolist(),
        'vertical_origin_navd88_m':datum,'target_discharge_m3s':q,'cell_m':cell,
        'inlet_stage_navd88_m':inlet+datum,'outlet_stage_navd88_m':outlet+datum,
        'geometry_sha256':geometry_sha,'production_promoted':False,
        'boundary_mode':'mixed_characteristic_discharge' if args.mixed_inlet else 'stage_velocity'}
    registration['solver_binary_sha256']=hashlib.sha256(args.binary.read_bytes()).hexdigest()
    registration['fixed_dt_seconds']=args.dt
    registration['bed_sampling']=args.bed_sampling
    registration['cfl']=args.cfl
    registration['refinement_warm_start']=refinement
    registration['same_grid_continuation']=continuation
    if args.resume_frame:
        registration['resume_frame']=str(args.resume_frame.resolve())
        registration['resume_frame_sha256']=hashlib.sha256(args.resume_frame.read_bytes()).hexdigest()
    (work/'registration.json').write_text(json.dumps(registration,indent=2),encoding='utf-8')
    print(json.dumps(registration),flush=True)
    result=run_cpp_solver_scenario(scenario,output_dir=work,config=CppSolverRunConfig(
        executable=args.binary,steps=args.steps,
        frame_interval=max(1,args.steps//12),solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',
        cfl=args.cfl,feature_strength_scale=0,roughness_scale=1,bed_slope_source_scale=1,
        preserve_initial_mass=False,disable_fixture_calibrations=True,
        experimental_west_discharge_m3s=q if args.mixed_inlet else None,
        experimental_west_supercritical_stage=args.mixed_inlet))
    (work/'run_result.json').write_text(json.dumps(result.to_json_dict(ROOT),indent=2),encoding='utf-8')
    print(json.dumps(result.to_json_dict(ROOT)),flush=True)


if __name__=='__main__':
    main()
