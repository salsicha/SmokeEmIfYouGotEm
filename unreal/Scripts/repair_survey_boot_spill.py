"""Undo only the inventoried review-script additions, retaining original actors."""
from pathlib import Path
import json
import shutil
import unreal
ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/L_RaftSimBoot'
before=json.loads((ROOT/'tmp/south-fork-survey-boot-spill.json').read_text())
original={'DirectionalLight_0','SkyLight_0','SkyAtmosphere_0','VolumetricCloud_0',
    'ExponentialHeightFog_0','PostProcessVolume_0','CameraActor_0'}
added={'StaticMeshActor_0','StaticMeshActor_1','StaticMeshActor_2',
    'DirectionalLight_1','DirectionalLight_2','DirectionalLight_3',
    'SkyLight_1','SkyLight_2','SkyLight_3','SceneCapture2D_0','SceneCapture2D_1',
    'RaftSimRiverWaterConfig_0','RaftSimRaftActor_0','PlayerStart_0',
    'RaftSimContentLockDirector_0','SkyAtmosphere_1','PostProcessVolume_1'}
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level(LEVEL)
world=unreal.EditorLevelLibrary.get_editor_world()
assert world.get_path_name()==before['world']
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert {a.get_name() for a in actors}==original|added,'Unexpected scene changes; refusing partial cleanup'
for actor in actors:
    prior=next(a for a in before['actors'] if a['path']==actor.get_path_name())
    assert actor.get_actor_label()==prior['label'] and actor.get_class().get_path_name()==prior['class']
backup=ROOT/'tmp/south-fork-review-spill-recovery/L_RaftSimBoot.before_repair.umap'
backup.parent.mkdir(parents=True,exist_ok=True)
if backup.exists():raise RuntimeError('Preserve the existing recovery backup; do not overwrite it')
shutil.copy2(ROOT/'unreal/Content/RaftSim/Maps/L_RaftSimBoot.umap',backup)
for actor in actors:
    if actor.get_name() in added:
        assert unreal.EditorLevelLibrary.destroy_actor(actor)
world.get_world_settings().set_editor_property('default_game_mode',
    unreal.load_class(None,'/Script/SmokeEmIfYouGotEm.RaftSimBootGameMode'))
assert world.get_path_name().split('.')[0]==LEVEL
assert levels.save_current_level()
remaining=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert {a.get_name() for a in remaining}==original
report={'status':'review_spill_removed_original_actors_retained','removed_actor_names':sorted(added),
    'retained_actor_names':sorted(original),'restored_game_mode':'/Script/SmokeEmIfYouGotEm.RaftSimBootGameMode',
    'recovery_backup':str(backup.relative_to(ROOT)),'binary_equals_pre_task_version':False}
(ROOT/'docs/reconstruction-review-2026-09-06/engine/boot_spill_repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
