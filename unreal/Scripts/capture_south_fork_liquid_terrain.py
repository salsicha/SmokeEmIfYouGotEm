"""Captured-bed FLIP coupling review in an unsaved copy of the registered scene.

Launch with -EnablePlugins=NiagaraFluids -ExecCmds="py ABS_PATH". Blocking particle reads are correctness
diagnostics, not timing measurements. This is not production or visual acceptance.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
COMMAND=unreal.SystemLibrary.get_command_line()
steps_match=re.search(r'-RaftSimLiquidTerrainSteps=(\d+)',COMMAND)
SIM_STEPS=int(steps_match.group(1)) if steps_match else 720
assert 720<=SIM_STEPS<=3600, 'Bounded review permits 12 to 60 simulated seconds'
substeps_match=re.search(r'-RaftSimLiquidTerrainSubsteps=(\d+)',COMMAND)
SIM_SUBSTEPS=int(substeps_match.group(1)) if substeps_match else 1
assert SIM_SUBSTEPS in (1,2) and SIM_STEPS*SIM_SUBSTEPS<4000, 'Bounded GPU history permits one or two substeps and fewer than 4000 total steps'
match=re.search(r'-RaftSimLiquidTerrainLabel=([A-Za-z0-9_-]+)',COMMAND)
OUTPUT=ROOT/'docs/reconstruction-review-2026-09-07'/(match.group(1) if match else 'liquid-terrain-runtime')
LEVEL='/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable'
ASSET='/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview'
contact='-RaftSimLiquidTerrainContact' in COMMAND
fixed_overhead='-RaftSimLiquidTerrainFixedOverhead' in COMMAND
fixed_oblique='-RaftSimLiquidTerrainFixedOblique' in COMMAND
optics_sweep='-RaftSimLiquidTerrainOpticsSweep' in COMMAND
base_scattering='-RaftSimLiquidTerrainBaseScattering' in COMMAND
world_normal='-RaftSimLiquidTerrainWorldNormal' in COMMAND
world_ray='-RaftSimLiquidTerrainWorldRay' in COMMAND
assert not world_ray or world_normal, 'World-ray candidate follows the world-normal correction'
assert not world_normal or base_scattering, 'World-normal candidate requires the isolated optical material'
assert not (fixed_overhead and fixed_oblique), 'Select one fixed-camera angle'
assert not fixed_oblique or optics_sweep, 'Fixed oblique is an optical diagnostic'
assert not optics_sweep or fixed_overhead or fixed_oblique, 'Optics controls require one fixed camera'
optics_cases=[(opacity,bias) for bias in (-10.,-14.,-18.) for opacity in (0.,.1,.5,1.)]
if base_scattering:
    assert optics_sweep, 'Base scattering diagnostic requires the fixed optics sweep'
    optics_cases=[(coefficient,bias) for bias in (-10.,-12.,-14.) for coefficient in (.0001,.001,.01)]
if contact:ASSET='/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainContactReview'
control_centered='-RaftSimLiquidControlCentered' in COMMAND
geographic='-RaftSimLiquidGeographicReview' in COMMAND
assert not geographic or control_centered, 'Geographic registration requires the control-centred source frame'
if geographic:LEVEL='/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable'
window_name='SouthForkLiquidControlCentered20260909' if control_centered else 'SouthForkLiquidWindow20260908'
SOLID='/Game/RaftSim/Environment/'+window_name+'/SM_SouthForkLiquidCollisionSolid'
manifest=json.loads((ROOT/'unreal/SourceArt/RaftSim'/window_name/'manifest.json').read_text())
assert manifest['local_origin_engine_cm']==[0.,0.,350.], 'This capture retains its verified vertical frame'
control='-RaftSimLiquidTerrainNoCollision' in COMMAND
solid_loss_control='-RaftSimLiquidTerrainSolidLossControl' in COMMAND
state={'frame':0,'captures':[],'activation_confirmed':False,'system_asset':ASSET,
       'level':LEVEL,'collision_control':control,'complete':False,
       'production_promoted':False,'spawn_volume_calibrated':False,
       'scope':'21m captured-terrain/native-face handoff; unverified rapid identity; inferred submerged bed',
       'step_seconds':1/60,'blocking_particle_readback':True}
state['solid_loss_control_not_collision_fix']=solid_loss_control
state['terrain_contact_candidate']=contact
state['control_centered_window']=control_centered
state['window_manifest']=str(ROOT/'unreal/SourceArt/RaftSim'/window_name/'manifest.json')
state['source_geometry_sha256']=manifest['source_geometry_sha256']
state['fixed_overhead_camera']=fixed_overhead
state['fixed_oblique_camera']=fixed_oblique
state['optics_sweep']=optics_sweep
state['base_scattering_candidate']=base_scattering
state['world_normal_candidate']=world_normal
state['world_ray_candidate']=world_ray
momentum='-RaftSimLiquidTerrainMomentum' in COMMAND
foam='-RaftSimLiquidTerrainFoam' in COMMAND
state['advected_foam_candidate']=foam
foam_optics='-RaftSimLiquidTerrainFoamOptics' in COMMAND
assert not foam_optics or (foam and world_ray), 'Foam optics requires transported foam and corrected optical frames'
state['advected_foam_optics']=foam_optics
foam_strength_sweep='-RaftSimLiquidTerrainFoamStrengthSweep' in COMMAND
assert not foam_strength_sweep or foam_optics
state['foam_strength_sweep']=foam_strength_sweep
foam_motion='-RaftSimLiquidTerrainFoamMotion' in COMMAND
assert not foam_motion or foam_optics
state['foam_motion_capture']=foam_motion
benchmark='-RaftSimLiquidTerrainBenchmark' in COMMAND
assert not benchmark or (foam_optics and fixed_oblique and not foam_motion and not foam_strength_sweep)
state['uninterrupted_benchmark_requested']=benchmark
benchmark_intervals=[]
live_density='-RaftSimLiquidLiveDensity' in COMMAND
assert not live_density or (foam_optics and fixed_oblique and (foam_motion or benchmark)), 'Live density review requires transported foam, fixed optics and motion capture or benchmark'
state['live_density_requested']=live_density
smooth_sparse='-RaftSimLiquidSmoothSparse' in COMMAND
assert not smooth_sparse or live_density
state['smooth_sparse_requested']=smooth_sparse
live_bulk='-RaftSimLiquidLiveBulk' in COMMAND
assert not live_bulk or live_density
state['live_solver_occupancy_requested']=live_bulk
particle_surface_only='-RaftSimLiquidParticleSurfaceOnly' in COMMAND
assert not particle_surface_only or live_bulk
state['particle_surface_only_requested']=particle_surface_only
surface_foam='-RaftSimLiquidSurfaceFoam' in COMMAND
assert not surface_foam or live_bulk
state['current_surface_foam_requested']=surface_foam
state['native_grid_foam_evolution_requested']=foam and not surface_foam
secondary_foam='-RaftSimLiquidSecondaryFoam' in COMMAND
assert not secondary_foam or surface_foam
state['native_secondary_foam_requested']=secondary_foam
secondary_shared_surface='-RaftSimLiquidSecondarySharedSurface' in COMMAND
assert not secondary_shared_surface or secondary_foam
state['secondary_shared_surface_requested']=secondary_shared_surface
secondary_exact_contact='-RaftSimLiquidSecondaryExactContact' in COMMAND
assert not secondary_exact_contact or secondary_foam
state['secondary_exact_contact_requested']=secondary_exact_contact
secondary_endpoint_prediction='-RaftSimLiquidSecondaryEndpointPrediction' in COMMAND
assert not secondary_endpoint_prediction or secondary_shared_surface
state['secondary_endpoint_prediction_requested']=secondary_endpoint_prediction
secondary_current_surface='-RaftSimLiquidSecondaryCurrentSurface' in COMMAND
assert not secondary_current_surface or (secondary_endpoint_prediction and live_density)
state['secondary_current_surface_requested']=secondary_current_surface
if foam_motion:
    state['motion_capture']={'simulation_fps':60,'image_stride_steps':4,'playback_fps':15,
                             'duration_seconds':2,'not_realtime_performance_measurement':True}
if foam_strength_sweep:
    optics_cases=[(strength,-10.) for strength in (0.,1.,4.)]
snapshot_match=re.search(r'-RaftSimLiquidSurfaceSnapshot=([A-Za-z0-9_-]+)',COMMAND)
surface_snapshot=ROOT/'docs/reconstruction-review-2026-09-07'/snapshot_match.group(1) if snapshot_match else None
baseline_match=re.search(r'-RaftSimLiquidSurfaceBaseline=([A-Za-z0-9_-]+)',COMMAND)
surface_baseline=ROOT/'docs/reconstruction-review-2026-09-07'/baseline_match.group(1) if baseline_match else None
assert not surface_baseline or surface_snapshot
if surface_snapshot:
    assert not benchmark
    assert not live_density, 'Frozen snapshot and live reconstruction are mutually exclusive'
    assert foam_optics and fixed_oblique and SIM_STEPS==3600 and not foam_strength_sweep and not foam_motion
    snapshot_manifest=json.loads((surface_snapshot/'report.json').read_text())
    assert snapshot_manifest['finite'] and snapshot_manifest['sign_matches_density']
    assert hashlib.sha256((surface_snapshot/'surface.rgba16f').read_bytes()).hexdigest()==snapshot_manifest['texture_sha256']
    if 'input_scalar_sha256' in snapshot_manifest:
        assert hashlib.sha256((surface_snapshot/'input_phi.r32f').read_bytes()).hexdigest()==snapshot_manifest['input_scalar_sha256']
    state['surface_snapshot']={'source':str(surface_snapshot),'offline_geometry_not_live_animation':True,
                               'from_prior_particle_capture_not_current_run':True,
                               'texture_sha256':snapshot_manifest['texture_sha256']}
    optics_cases=[(0.,-10.),(1.,-10.)]
    if surface_baseline:
        baseline_manifest=json.loads((surface_baseline/'report.json').read_text())
        assert baseline_manifest['finite'] and baseline_manifest['red_channel_bitwise_unchanged']
        assert baseline_manifest['particle_capture_sha256']==snapshot_manifest['particle_capture_sha256']
        assert hashlib.sha256((surface_baseline/'surface.rgba16f').read_bytes()).hexdigest()==baseline_manifest['texture_sha256']
        state['surface_snapshot'].update(baseline_source=str(surface_baseline),
                                         same_particle_capture_sha256=baseline_manifest['particle_capture_sha256'])
river_optics='-RaftSimLiquidTerrainRiverOpticsSweep' in COMMAND
river_optics_motion='-RaftSimLiquidTerrainRiverOpticsMotion' in COMMAND
assert not (river_optics and river_optics_motion)
if river_optics or river_optics_motion:
    assert base_scattering and (foam_motion or (river_optics_motion and benchmark)) and not foam_strength_sweep and not surface_snapshot
    # Authored optical hypotheses, not measured South Fork turbidity. Cross
    # spectra and roughness independently with identical geometry/exposure.
    river_spectra=[
        ('inherited_cyan',[.0336,.0028,.00112],[.001,.001,.001]),
        ('muted_green',[.003,.0018,.0022],[.0002,.00025,.00022]),
        ('neutral_turbid',[.004,.0035,.0038],[.0005,.00055,.0005]),
    ]
    river_cases=[dict(name=name,absorption_per_cm=a,scattering_per_cm=s,roughness=r)
                 for name,a,s in river_spectra for r in (.12,.22,.35)]
    if river_optics_motion:
        # Selected from the fixed-state comparison, not a river measurement.
        river_cases=[dict(river_cases[4]) for _ in river_cases]
        state['river_optics_motion_profile']=river_cases[0]
    optics_cases=[(0.,-10.) for _ in river_cases]
    state['river_optics_cases']=river_cases
    state['river_optics_coefficients_measured']=False
vector_boundary=foam or '-RaftSimLiquidTerrainVectorBoundary' in COMMAND
state['vector_boundary_candidate']=vector_boundary
centered_transfer=vector_boundary or '-RaftSimLiquidTerrainCenteredTransfer' in COMMAND
state['centered_transfer_candidate']=centered_transfer
outlet_stage=centered_transfer or '-RaftSimLiquidTerrainOutletStage' in COMMAND
pic_flip_match=re.search(r'-RaftSimLiquidTerrainPicFlip=([0-9.]+)',COMMAND)
pic_flip_ratio=float(pic_flip_match.group(1)) if pic_flip_match else None
if pic_flip_ratio is not None:
    assert outlet_stage and math.isfinite(pic_flip_ratio) and 0<=pic_flip_ratio<=1
    state['pic_flip_diagnostic_requested']=pic_flip_ratio
compatible_projection=outlet_stage or '-RaftSimLiquidTerrainCompatibleProjection' in COMMAND
driven_boundary=compatible_projection or '-RaftSimLiquidTerrainDrivenBoundary' in COMMAND
grid_halo=driven_boundary or '-RaftSimLiquidTerrainGridHalo' in COMMAND
exact_triangles=grid_halo or '-RaftSimLiquidTerrainExactTriangles' in COMMAND
wet_start=exact_triangles or '-RaftSimLiquidTerrainWetStart' in COMMAND
open_sides=wet_start or '-RaftSimLiquidTerrainOpenSides' in COMMAND
complete_gather=open_sides or '-RaftSimLiquidTerrainCompleteGather' in COMMAND
grid_frame=complete_gather or '-RaftSimLiquidTerrainGridFrame' in COMMAND
private_contact=grid_frame or '-RaftSimLiquidTerrainPrivateContact' in COMMAND
momentum=momentum or private_contact
state['terrain_momentum_candidate']=momentum
state['private_mesh_contact_candidate']=private_contact
state['grid_frame_transfer_candidate']=grid_frame
state['complete_neighbor_gather_candidate']=complete_gather
state['river_boundary_axes_candidate']=open_sides
if open_sides:
    state['boundary_control_revision']='exposed-xyz-bindings-v2'
    state['open_boundary_controls']={'Left':True,'Right':True,'Back':True,
                                     'Front':True,'Down':False,'Up':True}
state['hydraulic_initial_state_candidate']=wet_start
state['exact_triangle_contact_candidate']=exact_triangles
state['grid_halo_candidate']=grid_halo
state['driven_boundary_candidate']=driven_boundary
state['compatible_projection_candidate']=compatible_projection
state['outlet_stage_candidate']=outlet_stage
if driven_boundary:
    boundary_name='grid_vector_boundary_profile.json' if vector_boundary else 'grid_boundary_profile.json'
    state['grid_boundary_profile']=boundary_name
    state['grid_boundary_sha256']=hashlib.sha256((ROOT/'unreal/SourceArt/RaftSim'/window_name/boundary_name).read_bytes()).hexdigest()
if grid_halo:
    state['physical_exchange_width_cm']=2100
    state['computational_width_cm']=2231.25
    state['computational_max_axis_cells']=68
state['simulation_steps']=SIM_STEPS
state['simulation_substeps_per_frame']=SIM_SUBSTEPS
state['affine_transfer_requested']='-RaftSimLiquidAffineTransfer' in COMMAND
state['quadratic_transfer_requested']='-RaftSimLiquidQuadraticTransfer' in COMMAND
assert not state['quadratic_transfer_requested'] or state['affine_transfer_requested']
state['compatible_advection_requested']='-RaftSimLiquidCompatibleAdvection' in COMMAND
assert not state['compatible_advection_requested'] or state['quadratic_transfer_requested']
pressure_match=re.search(r'-RaftSimLiquidTerrainPressureIterations=(\d+)',COMMAND)
pressure_iterations=int(pressure_match.group(1)) if pressure_match else None
if pressure_iterations is not None:
    assert 40<=pressure_iterations<=320, 'Bounded pressure convergence diagnostic only'
    state['pressure_iteration_diagnostic']=pressure_iterations
if exact_triangles:
    triangle_path=ROOT/'unreal/SourceArt/RaftSim'/window_name/'triangle_contact_profile.json'
    state['contact_triangle_profile_sha256']=hashlib.sha256(triangle_path.read_bytes()).hexdigest()
if wet_start:
    seed_path=ROOT/'unreal/SourceArt/RaftSim'/window_name/'hydraulic_initial_state.json'
    seed=json.loads(seed_path.read_text())
    state['initial_state_sha256']=hashlib.sha256(seed_path.read_bytes()).hexdigest()
    state['initial_state_particle_count']=seed['particle_count']
    state['initial_nominal_volume_m3']=seed['represented_nominal_volume_m3']
started=time.perf_counter()
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from south_fork_liquid_frame import review_frame, world_point_cm
frame_geometry=json.loads((ROOT/manifest['source_geometry_manifest']).read_text()) if geographic else {}
liquid_frame=review_frame(manifest,frame_geometry,geographic)
state['liquid_world_frame']=liquid_frame
state['geographic_review']=geographic
state['whole_rapid_integrated']=False
yaw=liquid_frame['yaw_degrees']
angle=math.radians(yaw)


def position(x,y,z):
    return unreal.Vector(*world_point_cm(liquid_frame,(x,y,z)))


def spawn(cls,point):
    actor=actors.spawn_actor_from_class(cls,point)
    assert actor
    return actor


def aim(point,focus):
    camera.set_actor_location(point,False,False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(point,focus),False)
    levels.set_level_viewport_camera_info(point,camera.get_actor_rotation(),'None')


def capture(name,particles=True):
    view.capture_scene()
    unreal.RenderingLibrary.export_render_target(world,target,str(OUTPUT),name+'.png')
    path=OUTPUT/(name+'.png')
    assert path.is_file()
    state['captures'].append({'name':name,'frame':state['frame'],
        'age_seconds':min(state['frame'],SIM_STEPS)/60,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if optics_sweep and 'optics_control' in state:
        state['captures'][-1]['optics_control']=dict(state['optics_control'])
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidFixtureTelemetry')
    if particles:
        report=OUTPUT/(name+'_particles.json')
        unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidFixtureParticles "{report}"')
        assert report.is_file(),'Actual GPU particle report missing'
        if secondary_foam:
            emitters=json.loads(report.read_text())['emitters']
            assert len(emitters)==2 and any('_Secondary_' in e['emitter'] for e in emitters), 'Native secondary emitter did not initialize'
            materials=json.loads(report.read_text())['runtime_materials']
            sprite_materials=[m for m in materials if 'River Secondary Roughness' in m['scalars']]
            assert len(sprite_materials)==1, 'Owned secondary foam material is not active'
            assert abs(sprite_materials[0]['scalars']['River Secondary Roughness']-.65)<1e-6
            assert abs(sprite_materials[0]['scalars']['River Secondary Specular']-.25)<1e-6
        if pic_flip_ratio is not None:
            captured=json.loads(report.read_text())['captured_system_state']
            ratios=[v for k,v in captured.items() if k.endswith('PIC FLIP Ratio')]
            assert len(ratios)==1 and len(ratios[0])==1 and abs(ratios[0][0]-pic_flip_ratio)<1e-6, 'Requested transfer ratio is not the actual captured runtime value'
        if base_scattering:
            materials=json.loads(report.read_text())['runtime_materials']
            assert any('River Roughness' in m['scalars'] for m in materials), 'Optical candidate is not the active material'
            if geographic:
                # Read actual shader bindings, not just the actor transform.
                import re
                material=next(m for m in materials if 'WorldGridExtents' in m['vectors'])
                vector=lambda key: tuple(float(v) for v in re.findall(r'[RGBA]=([-+0-9.eE]+)',material['vectors'][key]))
                assert vector('WorldGridExtents')[:3]==(2231.25,2231.25,800.), 'Native allocation extents differ from the physical grid'
                origin=vector('LocalToWorld3')[:3]
                expected=tuple(liquid_frame['origin_cm'][i]+(400 if i==2 else 0) for i in range(3))
                assert max(abs(a-b) for a,b in zip(origin,expected))<.001, 'Material volume is not centred on the registered liquid domain'
                for axis in range(2):
                    actual=vector(f'LocalToWorld{axis}')[:3]
                    angle=math.radians(yaw)
                    expected=(math.cos(angle),math.sin(angle),0) if axis==0 else (-math.sin(angle),math.cos(angle),0)
                    assert max(abs(a-b) for a,b in zip(actual,expected))<1e-5, 'Material axis differs from the positive-scale simulation frame'
                state['actual_material_frame_verified']=True
            if state.get('surface_snapshot_installed'):
                assert any('T_RaftSimOfflineSurfaceSnapshot' in m.get('textures',{}).get('VolumeTex','') for m in materials), 'Snapshot texture binding was overwritten'
        if ('-RaftSimLiquidTerrainReadGrid' in COMMAND and name in ('terrain_0006',f'terrain_{SIM_STEPS:04d}')) or (live_bulk and name in ('benchmark_after',f'optics_{len(optics_cases)-1:02d}')) or (surface_foam and name==f'terrain_{SIM_STEPS:04d}'):
            grids=OUTPUT/(name+'_grids')
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidGridReadback "{grids}"')
            assert (grids/'grids.json').is_file(),'Actual GPU grid report missing'
            data=json.loads((grids/'grids.json').read_text())
            assert data['grid_count']>0 and all(g['readback_saved'] for g in data['grids']), 'Incomplete grid readback'
            if geographic:
                flow=[g for g in data['grids'] if any(a['name']=='Velocity' for a in g['attributes'])]
                assert len(flow)==1 and flow[0]['cells']==[68,68,24], 'Geographic fluid grid collapsed or changed resolution'
                state['actual_geographic_grid_cells']=flow[0]['cells']
            if surface_foam:
                distance=[g for g in data['grids'] if any(a['name']=='SDF' for a in g['attributes'])]
                assert distance and all(g['rgba_texture'] and len(g['attributes'])==1 for g in distance), 'Native SDF must stay single-attribute RGBA for secondary readers'
                assert not any(a['name']=='RiverFoam' for g in data['grids'] for a in g['attributes']), 'Redundant native foam field remains'


def finish(error=None):
    if 'handle' in state:
        unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    if state.pop('live_density_started',False):
        try:
            result=OUTPUT/'live_density'
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidLiveDensityReview stop "{result}"')
            state['live_density_result']=json.loads((result/'report.json').read_text())
            live_result=state['live_density_result']
            assert live_result['gpu_update_count']>0 and not live_result['error'] and live_result['diagnostics']==[0,0,0,0], 'Live GPU reconstruction did not verify'
            if smooth_sparse:
                assert live_result['kernel_sparse_transition']=='continuous-weight-8-24', 'Continuous sparse reconstruction was not installed'
            if particle_surface_only:
                assert live_result['particle_surface_only'] and not live_result['solver_occupancy_floor_applied'], 'Particle-only surface was not installed'
        except Exception:
            error=(error or '')+'\n'+traceback.format_exc()
    state.update(complete=error is None,error=error,wall_seconds=time.perf_counter()-started)
    (OUTPUT/'capture.json').write_text(json.dumps(state,indent=2)+'\n')
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.perf_counter()-started>480:
            raise RuntimeError('Captured-terrain review exceeded eight-minute wall bound')
        if not state['activation_confirmed']:
            if not liquid.is_active():
                liquid.activate(True)
                return
            liquid.set_component_tick_enabled(False)
            state['activation_confirmed']=True
        frame=state['frame']
        if live_density and frame==6:
            unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidLiveDensityReview start'+(' profile' if benchmark else '')+(' bulk' if live_bulk else '')+(' foam' if surface_foam else ''))
            state['live_density_started']=True
        if (foam_motion or benchmark) and frame==2:
            unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainOpacityReview 0')
            unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainScatteringControl 0.001 0.12')
            if river_optics_motion:
                optical=river_cases[0]
                values=optical['absorption_per_cm']+optical['scattering_per_cm']+[optical['roughness']]
                unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainExtinctionControl '+' '.join(map(str,values)))
        if benchmark:
            # Warm up the actual simulated/rendered scene. All blocking image
            # and particle diagnostics stay outside [240, SIM_STEPS]. These
            # are editor fixture throughput intervals, not packaged-game FPS.
            now=time.perf_counter()
            if frame==230:
                capture('benchmark_before')
            if frame==240:
                state['benchmark_started_at']=now
                state['benchmark_last_at']=now
            elif frame>240:
                benchmark_intervals.append(1000*(now-state['benchmark_last_at']))
                state['benchmark_last_at']=now
            if frame==SIM_STEPS:
                state['benchmark']={'start_frame':240,'end_frame':frame,
                    'intervals_ms':benchmark_intervals,
                    'wall_seconds':now-state.pop('benchmark_started_at'),
                    'simulation_seconds':(frame-240)/60,
                    'blocking_readbacks_during_window':False,
                    'image_exports_during_window':False,
                    'render_target_size':[960,640],
                    'measurement':'editor fixed-step simulation plus scene-capture throughput, not packaged-game FPS'}
                state.pop('benchmark_last_at')
                capture('benchmark_after')
                finish()
                return
            liquid.advance_simulation(SIM_SUBSTEPS,1/(60*SIM_SUBSTEPS))
            levels.editor_invalidate_viewports()
            view.capture_scene()
            state['frame']+=1
            return
        if foam_motion and SIM_STEPS-120<=frame<SIM_STEPS and frame%4==0:
            capture(f'motion_{(frame-SIM_STEPS+120)//4:03d}',False)
        if frame in (6,30,60,240,480,SIM_STEPS):
            capture(f'terrain_{frame:04d}')
            if surface_foam and frame==SIM_STEPS:
                unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidLiveDensityReview inspect "{OUTPUT / "live_foam_active"}"')
        if optics_sweep and frame>=SIM_STEPS:
            offset=frame-SIM_STEPS
            case=offset//4
            if case==len(optics_cases):
                finish()
                return
            opacity,bias=optics_cases[case]
            if offset%4==0:
                unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidTerrainOpacityReview {0 if base_scattering else opacity}')
                if base_scattering:
                    unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidTerrainScatteringControl {0.001 if foam_strength_sweep or surface_snapshot else opacity} 0.12')
                if river_optics or river_optics_motion:
                    optical=river_cases[case]
                    values=optical['absorption_per_cm']+optical['scattering_per_cm']+[optical['roughness']]
                    unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainExtinctionControl '+' '.join(map(str,values)))
                if foam_strength_sweep:
                    unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidTerrainFoamControl {opacity}')
                if surface_snapshot:
                    unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainFoamControl 0')
                    if case==1 or surface_baseline:
                        source=surface_snapshot if case==1 else surface_baseline
                        binding=OUTPUT/('snapshot_binding' if case==1 else 'baseline_binding')
                        unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidSurfaceSnapshotReview "{source}" "{binding}"')
                        verified=json.loads((binding/'binding.json').read_text())
                        assert verified.get('gpu_result_verified',verified.get('gpu_upload_readback_exact',False)) and verified['material_binding_verified']
                        state['surface_snapshot_installed']=True
                settings=view.get_editor_property('post_process_settings')
                settings.set_editor_property('auto_exposure_bias',bias)
                view.set_editor_property('post_process_settings',settings)
                state['optics_control']={'opacity':0 if base_scattering else opacity,'exposure_bias':bias,
                                         'simulation_frozen':True,'camera_fixed':True}
                if base_scattering:
                    state['optics_control'].update(scattering_coefficient_per_cm=.001 if foam_strength_sweep or surface_snapshot else opacity,roughness=.12)
                if river_optics or river_optics_motion:
                    state['optics_control'].pop('scattering_coefficient_per_cm',None)
                    state['optics_control'].update(river_cases[case])
                if surface_snapshot:
                    state['optics_control'].update(surface_snapshot=case==1,foam_strength=0)
                if foam_strength_sweep:
                    state['optics_control']['foam_strength']=opacity
            if offset%4==3:
                capture(f'optics_{case:02d}',river_optics or case in (0,len(optics_cases)-1))
            levels.editor_invalidate_viewports()
            view.capture_scene()
            state['frame']+=1
            return
        # Keep the existing fixed-camera presentation controls at their own
        # timeline, independently of the duration of actual fluid simulation.
        frame=720+frame-SIM_STEPS if frame>=SIM_STEPS else -1
        if fixed_overhead and frame>=720:
            # The direct-SDF carrier is camera-facing. Do not change the camera
            # after freezing its emitter state and call that a second view.
            if frame==720:
                unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainOpacityReview 1')
            if frame==724:
                capture('fixed_overhead_opacity_one',True)
                hidden=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.StaticMeshActor)]
                state['capture_only_hidden_static_meshes']=[a.get_path_name() for a in hidden]
                for actor in hidden:view.hide_actor_components(actor)
            if frame==728:
                capture('fixed_overhead_water_only',True)
                liquid.set_visibility(False,True)
            if frame==732:
                capture('fixed_overhead_empty_control',False)
                finish()
                return
            levels.editor_invalidate_viewports()
            view.capture_scene()
            state['frame']+=1
            return
        if frame==720:
            aim(position(-14,-16,5),position(0,0,2.5))
        if frame==722:
            capture('terrain_low',False)
            liquid.set_visibility(False,True)
        if frame==724:
            capture('water_hidden',False)
            liquid.set_visibility(True,True)
        if frame in (725,729,733,737):
            bias={725:-14.,729:-18.,733:-22.,737:-26.}[frame]
            settings=view.get_editor_property('post_process_settings')
            settings.set_editor_property('auto_exposure_bias',bias)
            view.set_editor_property('post_process_settings',settings)
        if frame in (728,732,736,740):
            capture(f'exposure_{frame:04d}',False)
        if frame==742:
            aim(position(-17,-23,12),position(0,0,2.5))
            settings=view.get_editor_property('post_process_settings')
            settings.set_editor_property('auto_exposure_bias',-10.)
            view.set_editor_property('post_process_settings',settings)
        if frame==744:capture('same_view_original_opacity',False)
        if frame==745:unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainOpacityReview 1')
        if frame==748:capture('same_view_opacity_one',True)
        if frame==749:liquid.set_visibility(False,True)
        if frame==752:
            capture('same_view_water_hidden',False)
            liquid.set_visibility(True,True)
            unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainOpacityReview 0')
            aim(position(0,-1,35),position(0,0,3))
        if frame==756:
            capture('overhead_terrain',False)
            hidden=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.StaticMeshActor)]
            state['capture_only_hidden_static_meshes']=[a.get_path_name() for a in hidden]
            for actor in hidden:view.hide_actor_components(actor)
        if frame==760:
            capture('overhead_water_only',True)
            liquid.set_visibility(False,True)
        if frame==764:
            capture('overhead_empty_control',False)
            finish()
            return
        if frame<720:
            liquid.advance_simulation(SIM_SUBSTEPS,1/(60*SIM_SUBSTEPS))
        levels.editor_invalidate_viewports()
        view.capture_scene()
        state['frame']+=1
    except Exception:
        unreal.log_error(traceback.format_exc())
        finish(traceback.format_exc())


try:
    OUTPUT.mkdir(parents=True,exist_ok=False)
    assert unreal.load_object(None,'/NiagaraFluids/Enums/ENiagaraFLIPRenderingMethod.ENiagaraFLIPRenderingMethod'), 'Liquid review requires -EnablePlugins=NiagaraFluids; do not load dependent assets without it'
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0]==LEVEL
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    state['hidden_legacy_water']=[]
    state['recentered_scene_meshes']=[]
    if geographic:
        ground=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags]
        assert len(ground)==1
        scale=ground[0].get_actor_scale3d()
        assert abs(scale.x-1)+abs(scale.y+1)+abs(scale.z-1)<1e-5, 'Geographic source terrain must already be reflected'
        state['registered_ground_transform_unchanged']=str(ground[0].get_actor_transform())
    if control_centered and not geographic:
        geometry=json.loads((ROOT/manifest['source_geometry_manifest']).read_text())
        offset=geometry['parent_frame_offset_east_north_m']
        assert len(offset)==2 and geometry['coordinate_rebase_only']
        for actor in actors.get_all_level_actors():
            if isinstance(actor,unreal.StaticMeshActor) and not actor.get_attach_parent_actor():
                old=actor.get_actor_location()
                assert actor.set_actor_location(old-unreal.Vector(offset[0]*100,offset[1]*100,0),False,False)
                state['recentered_scene_meshes'].append(actor.get_path_name())
        assert state['recentered_scene_meshes'], 'No original terrain mesh was translated into the rebased review frame'
        state['parent_frame_offset_east_north_m']=offset
    for actor in actors.get_all_level_actors():
        if actor.get_class().get_name() in ('RaftSimWaterSurfaceActor','RaftSimWaterVfxActor',
                'WaterBodyRiver','WaterBodyLake','WaterBodyOcean'):
            actor.set_is_temporarily_hidden_in_editor(True)
            actor.set_actor_hidden_in_game(True)
            state['hidden_legacy_water'].append(actor.get_path_name())
    collider=spawn(unreal.StaticMeshActor,position(0,0,0))
    collider.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
    collider.set_actor_scale3d(unreal.Vector(*liquid_frame['scale']))
    forward=collider.get_actor_forward_vector()
    assert abs(forward.x-math.cos(angle))<1e-5 and abs(forward.y-math.sin(angle))<1e-5 and abs(forward.z)<1e-5, 'Collision registration is not the prescribed horizontal yaw'
    collider.set_actor_label('Unsaved captured liquid collision solid')
    collider.set_editor_property('tags',['RaftSimLiquidTerrainProbe']+([] if control else ['RaftSimLiquidTerrain']))
    mesh=collider.static_mesh_component
    mesh.set_static_mesh(unreal.load_asset(SOLID))
    mesh.set_collision_profile_name('BlockAll')
    # Retain scene/distance-field registration without drawing a second top
    # over the original captured terrain. Do not hide the component itself.
    mesh.set_editor_property('render_in_main_pass',False)
    mesh.set_editor_property('render_in_depth_pass',False)
    mesh.set_editor_property('affect_distance_field_lighting',True)
    mesh.set_editor_property('cast_shadow',True)
    state['collision_actor_transform']=str(collider.get_actor_transform())
    state['collision_render_main_pass']=False
    # The editor-only scene does not execute its gameplay lighting director.
    # Record existing lights and add a neutral review rig only if absent.
    existing_lights=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.DirectionalLight)]
    state['existing_directional_lights']=[a.get_path_name() for a in existing_lights]
    if not existing_lights:
        sun=spawn(unreal.DirectionalLight,unreal.Vector(0,0,3000))
        sun.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-30,roll=0),False)
        sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',50000.)
        sky=spawn(unreal.SkyLight,unreal.Vector())
        skylight=sky.get_component_by_class(unreal.SkyLightComponent)
        skylight.set_editor_property('intensity',1.)
        skylight.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        skylight.set_cubemap(unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
        state['lighting']='Neutral unsaved review rig, not photographic lighting calibration'
    else:
        state['original_directional_intensities']=[a.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property('intensity') for a in existing_lights]
        for light in existing_lights:
            light.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',50000.)
            light.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-30,roll=0),False)
        skies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.SkyLight)]
        if not skies:skies=[spawn(unreal.SkyLight,unreal.Vector())]
        for sky in skies:
            skylight=sky.get_component_by_class(unreal.SkyLightComponent)
            skylight.set_editor_property('intensity',1.)
            skylight.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
            skylight.set_cubemap(unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
        state['lighting']='Unsaved -40deg 50000-lux sun and 1x cubemap ambient diagnostic rig, not photographic calibration'
    levels.editor_set_viewport_realtime(False)
    levels.editor_set_viewport_realtime(True)
    camera=spawn(unreal.SceneCapture2D,position(-17,-23,12))
    aim(position(-17,-23,12),position(0,0,2.5))
    if fixed_overhead:aim(position(0,-1,35),position(0,0,3))
    view=camera.capture_component2d
    view.set_editor_property('fov_angle',48)
    view.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    view.set_editor_property('capture_every_frame',False)
    view.set_editor_property('capture_on_movement',False)
    view.set_editor_property('always_persist_rendering_state',True)
    exposure=unreal.PostProcessSettings()
    exposure.set_editor_property('override_auto_exposure_method',True)
    exposure.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
    exposure.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
    exposure.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
    exposure.set_editor_property('override_auto_exposure_bias',True)
    exposure.set_editor_property('auto_exposure_bias',-10.)
    view.set_editor_property('post_process_settings',exposure)
    target=unreal.RenderingLibrary.create_render_target2d(world,960,640,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,unreal.LinearColor(.025,.03,.04,1),False)
    view.set_editor_property('texture_target',target)
    for command in ('r.ScreenPercentage 100','r.MotionBlurQuality 0','r.AntiAliasingMethod 0'):
        unreal.SystemLibrary.execute_console_command(world,command)
    water=spawn(unreal.NiagaraActor,position(0,0,0))
    water.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
    # Niagara dimensions and quaternion grid orientation require a proper
    # rotation, not signed actor scale. Source/contact adapters reflect Y.
    water.set_actor_scale3d(unreal.Vector(1,1,1))
    state['liquid_reflection_method']='source/contact coordinate adapter; positive Niagara grid scale'
    assert abs(water.get_actor_up_vector().z-1)<1e-5, 'Liquid grid must remain upright'
    state['actual_frame_probe_errors_cm']=[]
    for actor in (collider,water):
        for point in ((0,0,0),(1,0,0),(0,1,0),(-8,9,4)):
            local_point=(point[0],-point[1],point[2]) if geographic and actor==water else point
            actual=unreal.MathLibrary.transform_location(actor.get_actor_transform(),unreal.Vector(*(100*p for p in local_point)))
            expected=position(*point)
            error=math.sqrt((actual.x-expected.x)**2+(actual.y-expected.y)**2+(actual.z-expected.z)**2)
            state['actual_frame_probe_errors_cm'].append(error)
            assert error<.0001, 'Actual engine source/collision frame differs from geographic registration'
    liquid=water.get_component_by_class(unreal.NiagaraComponent)
    system=unreal.load_asset(ASSET)
    assert system
    if '-RaftSimLiquidTerrainDumpShaders' in COMMAND:
        unreal.SystemLibrary.execute_console_command(world,f'RaftSim.DumpLiquidChannelShaders "{OUTPUT / "compiled_shaders"}" terrain')
    liquid.set_asset(system)
    if momentum:
        assert contact,'Momentum variant requires the contact baseline'
        variant=' surface-foam' if surface_foam else ' foam' if foam else ' vector-boundary' if vector_boundary else ' centered-transfer' if centered_transfer else ' outlet-stage' if outlet_stage else ' compatible-projection' if compatible_projection else ' driven-boundary' if driven_boundary else ' grid-halo' if grid_halo else ' exact-triangles' if exact_triangles else ' wet-start' if wet_start else ' open-sides' if open_sides else ' complete-gather' if complete_gather else ' grid-frame' if grid_frame else ' private' if private_contact else ''
        if pic_flip_ratio is not None:variant+=f' pic-flip={pic_flip_ratio}'
        unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainMomentumReview'+variant)
        assert 'MomentumReview' in liquid.get_editor_property('asset').get_name(), 'Momentum candidate was not installed'
        if private_contact:assert '_Private_' in liquid.get_editor_property('asset').get_name()
        if grid_frame:assert '_GridFrame_' in liquid.get_editor_property('asset').get_name()
        if complete_gather:assert '_CompleteGather_' in liquid.get_editor_property('asset').get_name()
        if open_sides:assert '_OpenSides_' in liquid.get_editor_property('asset').get_name()
        if wet_start:assert '_WetStart_' in liquid.get_editor_property('asset').get_name()
        if exact_triangles:assert '_ExactTriangles_' in liquid.get_editor_property('asset').get_name()
        if grid_halo:assert '_GridHalo_' in liquid.get_editor_property('asset').get_name()
        if driven_boundary:assert '_DrivenBoundary_' in liquid.get_editor_property('asset').get_name()
        if compatible_projection:assert '_CompatibleProjection_' in liquid.get_editor_property('asset').get_name()
        if outlet_stage:assert '_OutletStage_' in liquid.get_editor_property('asset').get_name()
        if centered_transfer:assert '_CenteredTransfer_' in liquid.get_editor_property('asset').get_name()
        if vector_boundary:assert '_VectorBoundary_' in liquid.get_editor_property('asset').get_name()
        if foam:assert '_Foam_' in liquid.get_editor_property('asset').get_name()
        if '-RaftSimLiquidTerrainDumpActiveShaders' in COMMAND or state['affine_transfer_requested']:
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.DumpLiquidChannelShaders "{OUTPUT / "active_compiled_shaders"}" active')
            assert (OUTPUT/'active_compiled_shaders').is_dir()
            if state['affine_transfer_requested']:
                raw=[p.read_bytes() for p in (OUTPUT/'active_compiled_shaders').glob('*.hlsl')]
                code='\n'.join(b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig') for b in raw)
                state['affine_compiled_markers']={name:name in code for name in ('RiverAffineGridToParticle','RiverAffineParticleToGrid')}
                if state['quadratic_transfer_requested']:
                    state['affine_compiled_markers'].update({name:name in code for name in ('RiverQuadraticGridToParticle','RiverQuadraticParticleToGrid')})
                assert all(state['affine_compiled_markers'].values()), 'Requested affine transfer not present in active GPU shader'
                if state['compatible_advection_requested']:
                    assert 'RiverCompatibleMidpointAdvection' in code, 'Compatible advection not compiled'
    if secondary_foam:
        unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidSecondaryReview'+(' shared-surface' if secondary_shared_surface else ''))
        if '-RaftSimLiquidTerrainDumpActiveShaders' in COMMAND or secondary_exact_contact or secondary_endpoint_prediction:
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.DumpLiquidChannelShaders "{OUTPUT / "secondary_compiled_shaders"}" active')
            assert (OUTPUT/'secondary_compiled_shaders').is_dir()
            if secondary_exact_contact or secondary_endpoint_prediction:
                raw=[p.read_bytes() for p in (OUTPUT/'secondary_compiled_shaders').glob('*.hlsl')]
                code='\n'.join(b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig') for b in raw)
                if secondary_exact_contact:
                    assert 'RiverSecondaryExactTerrainSweep' in code, 'Exact secondary terrain sweep absent from compiled GPU shader'
                    state['secondary_exact_contact_compiled']=True
                if secondary_endpoint_prediction:
                    assert 'RiverSecondaryEndpointPrediction' in code, 'Endpoint phase prediction absent from compiled GPU shader'
                    state['secondary_endpoint_prediction_compiled']=True
                if secondary_current_surface:
                    assert 'RiverSecondaryCurrentSurfaceStage' in code and 'RiverCurrentSurfaceStage_Ready' in code, 'Current-surface stage DI absent from actual GPU shader'
                    state['secondary_current_surface_compiled']=True
    if base_scattering:
        assert outlet_stage, 'Optical candidate requires the transient outlet-stage system'
        unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainBaseScatteringReview'+(' foam-world-frame' if foam_optics else ' world-frame' if world_ray else ' world-normal' if world_normal else ''))
    if solid_loss_control:
        unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidTerrainSolidLossControl')
        assert 'SolidLossControl' in liquid.get_editor_property('asset').get_name(), 'Solid-loss control was not installed; do not treat baseline as a control'
    liquid.set_force_solo(True)
    if pressure_iterations is not None:
        liquid.set_variable_int('User.Pressure Iterations',pressure_iterations)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    liquid.activate(True)
    view.capture_scene()
    state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:
    unreal.log_error(traceback.format_exc())
    if OUTPUT.exists():finish(traceback.format_exc())
    else:unreal.SystemLibrary.quit_editor()
