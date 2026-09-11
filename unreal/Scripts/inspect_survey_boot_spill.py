"""Read-only inventory for repairing the specifically identified review spill."""
from pathlib import Path
import json
import unreal
ROOT=Path(__file__).resolve().parents[2]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimBoot')
world=unreal.EditorLevelLibrary.get_editor_world()
report={'world':world.get_path_name(),'game_mode':str(world.get_world_settings().get_editor_property('default_game_mode')),
    'actors':[{'path':a.get_path_name(),'class':a.get_class().get_path_name(),'label':a.get_actor_label(),
        'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation())}
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()]}
(ROOT/'tmp/south-fork-survey-boot-spill.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
