"""Create a separate playable diagnostics level, without checkpoints or production writes."""
from pathlib import Path
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-conservative-edge/engine_review/engine_start.json'
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate'


def main():
    start=json.loads(DATA.read_text())
    imported=json.loads((ROOT/'docs/reconstruction-review-2026-09-06/engine/import_report.json').read_text())
    if imported['source_geometry_sha256']!=start['source_geometry_sha256']:
        raise ValueError('Imported terrain and hydraulic geometry disagree')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    # new_level returns False for an existing asset and otherwise leaves the
    # startup map open. Never mutate or save that unrelated world on failure.
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        if not levels.load_level(LEVEL): raise RuntimeError('Cannot load the review level')
        world=unreal.EditorLevelLibrary.get_editor_world()
        if world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Wrong review world')
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if actor.get_class().get_name() not in ('WorldSettings','Brush'):
                unreal.EditorLevelLibrary.destroy_actor(actor)
    elif not levels.new_level(LEVEL):
        raise RuntimeError('Cannot create the review level; no scene was modified')
    world=unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Refusing to modify a non-review level')
    def spawn(cls,location=None,rotation=None):
        return unreal.EditorLevelLibrary.spawn_actor_from_class(cls,location or unreal.Vector(),rotation or unreal.Rotator())
    terrain=spawn(unreal.StaticMeshActor)
    terrain.set_actor_label('Captured banks and exposed rock - inferred submerged bed')
    terrain.tags = [unreal.Name('RaftSimPhysicalGround')]
    terrain.static_mesh_component.set_static_mesh(unreal.load_asset(imported['mesh']))
    terrain.static_mesh_component.set_collision_profile_name('BlockAll')
    config=spawn(unreal.load_class(None,'/Script/RaftSimWater.RaftSimRiverWaterConfig'))
    settings={'cooked_fields_dir':start['cooked_fields_dir'],'coordinate_map_path':start['coordinate_map_path'],
        'flow_band':'median_runnable','window_center_m':unreal.Vector2D(0,0),
        'window_extent_m':start['window_extent_m'],'recenter_hydraulic_crux':False,
        'enable_moving_window_streaming':False,'map_provides_terrain':True,
        'live_solver_owns_runtime_rendering':True,'enable_live_solver_volume_core':False,
        'live_surface_calm_coverage':1.,'live_surface_active_coverage':1.,
        'enable_live_presentation_surface_smoothing':False,
        'live_presentation_standing_wave_scale':0.,'live_presentation_hydraulic_relief_scale':0.,
        'enable_live_rapid_surface_refinement':False,'live_rapid_surface_subdivision':1,
        'enable_live_raft_local_fluid_heightfield':False}
    for name,value in settings.items():config.set_editor_property(name,value)
    raft=spawn(unreal.load_class(None,'/Script/RaftSimRaft.RaftSimRaftActor'),
        unreal.Vector(*start['location_cm']),unreal.Rotator(pitch=0,yaw=start['yaw_degrees'],roll=0))
    actual=raft.get_actor_rotation()
    if abs(actual.pitch)>1e-3 or abs(actual.roll)>1e-3 or abs(actual.yaw-start['yaw_degrees'])>1e-3:
        raise ValueError('Review raft orientation does not match the geographic tangent')
    raft.set_actor_label('Survey review raft - free drift, no saved-run relocation')
    spawn(unreal.PlayerStart,unreal.Vector(*start['location_cm']),unreal.Rotator(pitch=0,yaw=start['yaw_degrees'],roll=0))
    # GameModeBase avoids loading saved 49-km route stations into this local
    # 271-m test. Retain the game's guide controls, camera and raft interaction.
    bp=unreal.load_asset(DEST+'/BP_SurveyReviewGameMode')
    if bp is None:
        factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.GameModeBase)
        bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_SurveyReviewGameMode',DEST,unreal.Blueprint,factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    defaults=unreal.get_default_object(bp.generated_class())
    guide_class = unreal.load_class(None, '/Script/RaftSimRaft.RaftSimGuidePawn')
    if guide_class is None:
        raise RuntimeError('Gameplay guide class is missing; refusing an unpossessed review level')
    defaults.set_editor_property('default_pawn_class', guide_class)
    defaults.set_editor_property('player_controller_class',unreal.load_class(None,'/Script/SmokeEmIfYouGotEm.RaftSimGuidePlayerController'))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    world.get_world_settings().set_editor_property('default_game_mode',bp.generated_class())
    spawn(unreal.load_class(None,'/Script/SmokeEmIfYouGotEm.RaftSimContentLockDirector'))
    light=spawn(unreal.DirectionalLight,unreal.Vector(0,0,30000),unreal.Rotator(pitch=-40,yaw=-35,roll=0))
    light.light_component.set_editor_property('intensity',3.)
    sky=spawn(unreal.SkyAtmosphere)
    light.light_component.set_editor_property('atmosphere_sun_light',True)
    skylight=spawn(unreal.SkyLight);skylight.light_component.set_editor_property('real_time_capture',True)
    post=spawn(unreal.PostProcessVolume);post.set_editor_property('unbound',True)
    settings=post.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_method',True)
    settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
    settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
    post.set_editor_property('settings',settings)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Refusing to save a non-review level')
    if not levels.save_current_level(): raise RuntimeError('Review level save failed')
    report={'status':'playable_diagnostic_created_not_accepted','level':LEVEL,'source':str(DATA.relative_to(ROOT)),
        'source_geometry_sha256':start['source_geometry_sha256'],'production_scene_modified':False,
        'water_surface_count_expected':1,'geometric_presentation_overrides_disabled':True,
        'raft_collision_validated':False,'performance_validated':False}
    (ROOT/'docs/reconstruction-review-2026-09-06/engine/playable_setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log(json.dumps(report))


if __name__=='__main__':main()
