"""Isolated 3D SDF liquid visibility/motion review, not a river simulation.

No map is saved. One manual 1/60 s Niagara step is submitted per rendered editor
frame; ordinary component ticking is disabled. Captures include a water-hidden
control. Wall time includes render/export overhead and is not game performance.
Launch with -ExecCmds="py <absolute script path>", not -ExecutePythonScript:
the latter closes the editor immediately after callback registration.
"""
from pathlib import Path
import json
import re
import time
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[2]
label_arg = re.search(r'(?:^|\s)-RaftSimLiquidFixtureLabel=([A-Za-z0-9_-]+)(?:\s|$)',
                      unreal.SystemLibrary.get_command_line())
label = label_arg.group(1) if label_arg else 'liquid-body-fixture'
OUTPUT = ROOT / 'docs/reconstruction-review-2026-09-07' / label
ASSET = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodySDFReview'
collision = '-RaftSimLiquidFixtureCollision' in unreal.SystemLibrary.get_command_line()
channel = '-RaftSimLiquidFixtureChannel' in unreal.SystemLibrary.get_command_line()
bounded = '-RaftSimLiquidFixtureBounded' in unreal.SystemLibrary.get_command_line()
channel = channel or bounded
if channel:
    collision = True
obstacle_control = '-RaftSimLiquidFixtureObstacleControl' in unreal.SystemLibrary.get_command_line()
if collision:
    ASSET = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodyCollisionReview'
if channel:
    ASSET = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelOwnedReview'
if bounded:
    ASSET = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelBoundedReview'
state = {'frame': 0, 'captures': [], 'requested_step_seconds': 1/60,
         'activation_confirmed': False,
         'warmup_steps': 180,
         'scope': 'Isolated 4x4x5 m Hose-derived SDF liquid, no river coupling',
         'production_promoted': False}
profile = '-RaftSimLiquidFixtureProfile' in unreal.SystemLibrary.get_command_line()
state['single_frame_gpu_profile_requested'] = profile
state['collision_variant'] = collision
state['obstacle_present'] = collision or obstacle_control
state['system_asset'] = ASSET
state['flow_through_channel'] = channel
stop_inlet = '-RaftSimLiquidFixtureStopInlet' in unreal.SystemLibrary.get_command_line()
assert not stop_inlet or channel, 'Stopping an inlet requires the channel variant'
state['stop_inlet_after_seconds'] = 4 if stop_inlet else None
readback = '-RaftSimLiquidFixtureReadback' in unreal.SystemLibrary.get_command_line()
state['blocking_particle_readback'] = readback


def spawn(cls, location, target=None):
    rotation = unreal.Rotator() if target is None else unreal.MathLibrary.find_look_at_rotation(location, target)
    result = actors.spawn_actor_from_class(cls, location, rotation)
    assert result
    return result


def capture(name):
    view.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, target_texture, str(OUTPUT), name+'.png')
    path = OUTPUT / (name+'.png')
    assert path.is_file() and path.stat().st_size > 0
    state['captures'].append({'frame': state['frame'], 'image': str(path),
        'requested_age_seconds': min(state['frame'],360)/60,
        'camera_cm': [camera.get_actor_location().x, camera.get_actor_location().y,
                      camera.get_actor_location().z]})
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.LiquidFixtureTelemetry')
    if readback and name.startswith('liquid_0'):
        particle_report = OUTPUT / (name+'_particles.json')
        unreal.SystemLibrary.execute_console_command(world, f'RaftSim.LiquidFixtureParticles "{particle_report}"')
        assert particle_report.is_file(), 'GPU particle readback report missing'


def finish(error=None):
    if 'handle' in state:
        unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    state['wall_seconds'] = time.perf_counter() - started
    state['error'] = error
    state['complete'] = error is None
    (OUTPUT/'capture.json').write_text(json.dumps(state, indent=2)+'\n')
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.perf_counter()-started > 240:
            raise RuntimeError('Isolated capture exceeded four-minute wall bound')
        if not state['activation_confirmed']:
            if not liquid.is_active():
                liquid.activate(True)
                return
            liquid.set_component_tick_enabled(False)
            state['activation_confirmed'] = True
            unreal.SystemLibrary.execute_console_command(world, 'RaftSim.LiquidFixtureTelemetry')
        # Export the preceding rendered step, then enqueue exactly one next step.
        if state['frame'] in (240, 300, 360):
            capture(f'liquid_{state["frame"]:04d}')
        if state['frame'] == 240 and stop_inlet:
            liquid.set_variable_float('User.Inlet Particle Rate', 0)
        if state['frame'] == 330 and profile:
            unreal.SystemLibrary.execute_console_command(world, 'ProfileGPU')
        if state['frame'] == 360:
            camera.set_actor_location(unreal.Vector(950,400,80), False, False)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_actor_location(), unreal.Vector(0,0,-40)), False)
        if state['frame'] == 362:
            capture('liquid_side')
            camera.set_actor_location(unreal.Vector(-650,-800,0), False, False)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_actor_location(), unreal.Vector(0,0,-40)), False)
        if state['frame'] == 364:
            capture('liquid_low')
            camera.set_actor_location(unreal.Vector(750,-950,600), False, False)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_actor_location(), focus), False)
            liquid.set_visibility(False, True)
        if state['frame'] == 366:
            capture('water_hidden')
            finish()
            return
        if state['frame'] < 360:
            liquid.advance_simulation(1, 1/60)
        # Scene captures alone need not execute Niagara GPU simulation. Keep a
        # real editor viewport drawing too, and verify its compute stages in
        # the GPU profile rather than equating CPU age with GPU advancement.
        level_editor.editor_invalidate_viewports()
        view.capture_scene()
        state['frame'] += 1
    except Exception:
        unreal.log_error(traceback.format_exc())
        finish(traceback.format_exc())


try:
    OUTPUT.mkdir(parents=True, exist_ok=False)
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    assert world
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    # The subsystem's true path removes its own override and asserts if none
    # exists. Establish that named override before removing it.
    level_editor.editor_set_viewport_realtime(False)
    level_editor.editor_set_viewport_realtime(True)
    focus = unreal.Vector(0, 0, 180)
    # Plain neutral geometry and lights expose shape; this is not river scenery.
    floor = spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, -10 if (collision or obstacle_control) else -270))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(12, 12, .2))
    if collision or obstacle_control:
        # GPU readback establishes the tank bottom at z=0 (not -250).
        # Put the obstacle in the liquid, not merely touching its bottom.
        obstacle = spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, 100))
        obstacle.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
        obstacle.set_actor_scale3d(unreal.Vector(1.6, 1.6, 1.6))
        obstacle.static_mesh_component.set_collision_profile_name('BlockAll')
        obstacle.set_editor_property('tags', ['RaftSimLiquidFixtureObstacle'])
        state['obstacle'] = {'centre_cm': [0,0,100], 'radius_cm': 80,
                             'geometry': 'analytic test sphere, not surveyed rock'}
    for location, strength in [(unreal.Vector(500,-450,700), 4000),
                               (unreal.Vector(-500,300,450), 2200)]:
        light = spawn(unreal.RectLight, location, focus)
        light_component = light.get_component_by_class(unreal.RectLightComponent)
        light_component.set_editor_property('intensity', strength)
        light_component.set_editor_property('source_width', 350)
        light_component.set_editor_property('source_height', 350)
    sky = spawn(unreal.SkyLight, unreal.Vector())
    skylight = sky.get_component_by_class(unreal.SkyLightComponent)
    skylight.set_editor_property('intensity', 1000.0)
    skylight.set_editor_property('real_time_capture', False)
    skylight.set_editor_property('source_type', unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    skylight.set_cubemap(unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
    spawn(unreal.SkyAtmosphere, unreal.Vector())
    sun = spawn(unreal.DirectionalLight, unreal.Vector(0,0,700))
    sun.set_actor_rotation(unreal.Rotator(-40,-30,0), False)
    sun_light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_light.set_editor_property('atmosphere_sun_light', True)
    sun_light.set_editor_property('intensity', 50000.0)
    camera = spawn(unreal.SceneCapture2D, unreal.Vector(750,-950,600), focus)
    level_editor.set_level_viewport_camera_info(camera.get_actor_location(),
        camera.get_actor_rotation(), 'None')
    view = camera.capture_component2d
    view.set_editor_property('fov_angle', 46)
    view.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    view.set_editor_property('capture_every_frame', False)
    view.set_editor_property('capture_on_movement', False)
    view.set_editor_property('always_persist_rendering_state', True)
    exposure = unreal.PostProcessSettings()
    exposure.set_editor_property('override_auto_exposure_method', True)
    exposure.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
    exposure.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True)
    exposure.set_editor_property('auto_exposure_apply_physical_camera_exposure', False)
    exposure.set_editor_property('override_auto_exposure_bias', True)
    exposure.set_editor_property('auto_exposure_bias', -10.0)
    view.set_editor_property('post_process_settings', exposure)
    target_texture = unreal.RenderingLibrary.create_render_target2d(world, 960, 640,
        unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(.025,.03,.04,1), False)
    view.set_editor_property('texture_target', target_texture)
    for command in ('r.EyeAdaptationQuality 2', 'r.ScreenPercentage 100',
                    'r.MotionBlurQuality 0', 'r.AntiAliasingMethod 0',
                    'r.ProfileGPU.ShowUI 0'):
        unreal.SystemLibrary.execute_console_command(world, command)
    water_actor = spawn(unreal.NiagaraActor, unreal.Vector())
    liquid = water_actor.get_component_by_class(unreal.NiagaraComponent)
    system = unreal.load_asset(ASSET)
    assert system
    liquid.set_asset(system)
    if channel:
        state['inlet_rate_before_override'] = str(liquid.get_variable_float('User.Inlet Particle Rate'))
        state['inlet_velocity_before_override'] = str(liquid.get_variable_vec3('User.Inlet Velocity'))
        if '-RaftSimLiquidFixtureSetInlet' in unreal.SystemLibrary.get_command_line():
            liquid.set_variable_float('User.Inlet Particle Rate', 20000)
            liquid.set_variable_vec3('User.Inlet Velocity', unreal.Vector(250,0,0))
            liquid.set_variable_vec3('User.Inlet Position', unreal.Vector(-135,0,60))
            liquid.set_variable_vec3('User.Inlet Scale', unreal.Vector(.4,2.8,.8))
            state['inlet_explicitly_set_on_component'] = True
    liquid.set_force_solo(True)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    # Asset compilation and PSO readiness can defer Activate. Leave its retry
    # tick enabled until is_active() confirms activation in a later editor frame.
    liquid.activate(True)
    view.capture_scene()
    started = time.perf_counter()
    state['handle'] = unreal.register_slate_post_tick_callback(tick)
except Exception:
    unreal.log_error(traceback.format_exc())
    unreal.SystemLibrary.quit_editor()
