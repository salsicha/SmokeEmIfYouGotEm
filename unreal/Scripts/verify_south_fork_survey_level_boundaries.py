"""Read back saved worlds; the survey preview must not contaminate startup."""
from pathlib import Path
import json
import unreal
ROOT=Path(__file__).resolve().parents[2]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimBoot')
world=unreal.EditorLevelLibrary.get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
expected={'DirectionalLight_0','SkyLight_0','SkyAtmosphere_0','VolumetricCloud_0',
    'ExponentialHeightFog_0','PostProcessVolume_0','CameraActor_0'}
assert {a.get_name() for a in actors}==expected
assert world.get_world_settings().get_editor_property('default_game_mode').get_path_name()=='/Script/SmokeEmIfYouGotEm.RaftSimBootGameMode'
assert levels.load_level('/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable')
world=unreal.EditorLevelLibrary.get_editor_world()
assert world.get_path_name().split('.')[0]=='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
rafts=[a for a in actors if a.get_class().get_name()=='RaftSimRaftActor']
configs=[a for a in actors if a.get_class().get_name()=='RaftSimRiverWaterConfig']
terrain=[a for a in actors if isinstance(a,unreal.StaticMeshActor)]
assert len(rafts)==len(configs)==len(terrain)==1
rotation=rafts[0].get_actor_rotation()
assert abs(rotation.pitch)<.001 and abs(rotation.roll)<.001
assert abs(rotation.yaw-158.434789)<.001
assert configs[0].get_editor_property('cooked_fields_dir').startswith('tmp/south-fork-survey-hydraulics/')
assert not configs[0].get_editor_property('recenter_hydraulic_crux')
report={'status':'saved_world_isolation_passed','boot_original_actor_count':len(expected),
    'boot_game_mode_restored':True,'review_raft_count':1,'review_terrain_count':1,
    'review_water_config_count':1,'review_spawn_upright':True,'production_reconstruction_promoted':False}
(ROOT/'docs/reconstruction-review-2026-09-06/engine/saved_world_isolation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
