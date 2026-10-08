"""Unsaved native environment review: no playable water, raft, or FPS acceptance."""
import hashlib,json,os,time,traceback
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[2]
out=Path(os.environ.get('RAFTSIM_TERRAIN_REVIEW_OUT',str(root/'tmp/futaleufu-continuous-terrain-review')))
level=os.environ.get('RAFTSIM_TERRAIN_REVIEW_LEVEL','/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousTerrainV1')
counts={'/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousTerrainV1':177,
        '/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1':800}
if level not in counts:raise RuntimeError('Only explicit continuous terrain candidates may be reviewed here')
expected_count=counts[level]
path=root/('unreal/Content/'+level.removeprefix('/Game/')+'.umap')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=dict(frames=0,captures=[],scope='Native continuous-environment diagnostic; no playable water, boat or performance acceptance')
views=[('azul_canyon',[439504.80775,-386523.59978,8907.82743]),
       ('confluence',[563655.26699,-378484.39764,5614.38904]),
       ('mainstem_island',[304528.62221,-96383.43869,4023.28625])]
def finish(error=None):
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    state.update(error=error,map_unchanged=sha(path)==state['map_sha256'])
    (out/'receipt.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    unreal.SystemLibrary.quit_editor()
def aim(index):
    name,p=views[index];focus=unreal.Vector(*p)
    location=focus+unreal.Vector(28000,35000,36000)
    if not camera.set_actor_location(location,False,False):raise RuntimeError('Capture camera move failed')
    if not camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),False):raise RuntimeError('Capture camera rotation failed')
    levels.set_level_viewport_camera_info(location,camera.get_actor_rotation(),'None')
    state.setdefault('camera_poses',[]).append(dict(name=name,location=str(camera.get_actor_location()),rotation=str(camera.get_actor_rotation())))
    view.capture_scene()
def tick(delta):
    try:
        state['frames']+=1
        if time.monotonic()-started>240:raise RuntimeError('Terrain view review exceeded four-minute bound')
        frame=state['frames'];index=(frame-1)//60
        if index>=len(views):finish();return
        if frame%60==1:aim(index)
        levels.editor_invalidate_viewports()
        view.capture_scene()
        if frame%60==0:
            name,_=views[index]
            unreal.RenderingLibrary.export_render_target(world,target,str(out),name+'.png')
            image=out/(name+'.png')
            if not image.is_file() or image.stat().st_size==0:raise RuntimeError('Missing native frame')
            state['captures'].append(dict(name=name,path=str(image),sha256=sha(image),frame=frame))
    except Exception:finish(traceback.format_exc())
try:
    if out.exists():raise RuntimeError('Fresh review output required')
    out.mkdir();state['map_sha256']=sha(path)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(level):raise RuntimeError('Map load failed')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    state['descriptors']=[dict(label=str(d.label),guid=str(d.guid)) for d in descs]
    # ContinuousTerrain labels identify empty, always-loaded roots. The
    # separate spatial LandscapeStreamingProxy actors own the visible surface.
    # This terrain-only candidate has no runtime actors; load its full set and
    # validate real resident proxies, never equate root descriptors to geometry.
    wanted=[d.guid for d in descs]
    if len(wanted)<2*expected_count:raise RuntimeError('Incomplete root/proxy descriptor set: '+str(len(wanted)))
    unreal.WorldPartitionBlueprintLibrary.load_actors(wanted)
    resident=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeStreamingProxy)]
    state['loaded_terrain_proxies']=len(resident)
    if len(resident)!=expected_count:raise RuntimeError('Actual resident streaming proxies differ from expected count: '+str(len(resident)))
    state['canopy_instances_by_mesh']={}
    for actor in actors.get_all_level_actors():
        if not isinstance(actor,unreal.InstancedFoliageActor):continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not component.static_mesh:continue
            name=component.static_mesh.get_path_name()
            state['canopy_instances_by_mesh'][name]=state['canopy_instances_by_mesh'].get(name,0)+component.get_instance_count()
            if component.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION:
                raise RuntimeError('Canopy introduced physical collision')
    state['canopy_instance_count']=sum(state['canopy_instances_by_mesh'].values())
    expected_canopy=int(os.environ.get('RAFTSIM_TERRAIN_REVIEW_EXPECTED_CANOPY','0'))
    if state['canopy_instance_count']!=expected_canopy:raise RuntimeError('Saved continuous canopy count mismatch')
    state['terrain_materials']={}
    for actor in resident:
        material=actor.get_editor_property('landscape_material')
        name=material.get_path_name() if material else 'None'
        state['terrain_materials'][name]=state['terrain_materials'].get(name,0)+1
    expected=os.environ.get('RAFTSIM_TERRAIN_REVIEW_MATERIAL')
    if expected and state['terrain_materials']!={expected:expected_count}:raise RuntimeError('Saved terrain material mismatch')
    state['terrain_bounds']=[dict(name=a.get_name(),bounds=str(a.get_actor_bounds(False))) for a in resident]
    levels.editor_set_viewport_realtime(False)
    levels.editor_set_viewport_realtime(True)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    def spawn(cls,location):
        actor=actors.spawn_actor_from_class(cls,location)
        if actor is None:raise RuntimeError('Unable to spawn unsaved review actor')
        return actor
    sun=spawn(unreal.DirectionalLight,unreal.Vector(0,0,3000))
    sun.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-30,roll=0),False)
    sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',50000.)
    sky=spawn(unreal.SkyLight,unreal.Vector())
    light=sky.get_component_by_class(unreal.SkyLightComponent)
    light.set_editor_property('intensity',1.)
    light.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    light.set_cubemap(unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
    state['lighting']='Unsaved neutral diagnostic sun/ambient; not final game lighting'
    camera=spawn(unreal.SceneCapture2D,unreal.Vector())
    view=camera.capture_component2d
    view.set_editor_property('fov_angle',65.)
    view.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    view.set_editor_property('capture_every_frame',False)
    view.set_editor_property('capture_on_movement',False)
    view.set_editor_property('always_persist_rendering_state',True)
    settings=unreal.PostProcessSettings()
    settings.set_editor_property('override_auto_exposure_method',True)
    settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
    settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
    settings.set_editor_property('override_auto_exposure_bias',True)
    settings.set_editor_property('auto_exposure_bias',-10.)
    view.set_editor_property('post_process_settings',settings)
    target=unreal.RenderingLibrary.create_render_target2d(world,1280,800,unreal.TextureRenderTargetFormat.RTF_RGBA8,
                                                        unreal.LinearColor(.04,.04,.04,1),False)
    view.set_editor_property('texture_target',target)
    for command in ('r.ScreenPercentage 100','r.MotionBlurQuality 0','r.AntiAliasingMethod 0'):
        unreal.SystemLibrary.execute_console_command(world,command)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    started=time.monotonic();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:
    unreal.log_error(traceback.format_exc())
    if out.exists() and 'map_sha256' in state:finish(traceback.format_exc())
    else:unreal.SystemLibrary.quit_editor()
