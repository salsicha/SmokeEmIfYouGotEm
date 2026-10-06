"""Register review ground and the gameplay guide; do not rebuild terrain or water."""
from pathlib import Path
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
MESH = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/SM_TroublemakerSurveyCandidate'
MODE = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/BP_SurveyReviewGameMode'


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError('Cannot load the existing survey playable map')
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0] != LEVEL:
        raise RuntimeError('Refusing to modify a non-review map')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    owners = [actor for actor in actors if isinstance(actor, unreal.StaticMeshActor)
              and actor.static_mesh_component.static_mesh
              and actor.static_mesh_component.static_mesh.get_path_name().split('.')[0] == MESH]
    if len(owners) != 1:
        raise RuntimeError(f'Expected one captured ground mesh, found {len(owners)}')
    guide_class = unreal.load_class(None, '/Script/RaftSimRaft.RaftSimGuidePawn')
    controller_class = unreal.load_class(None, '/Script/SmokeEmIfYouGotEm.RaftSimGuidePlayerController')
    mode = unreal.load_asset(MODE)
    if guide_class is None or controller_class is None or mode is None:
        raise RuntimeError('Missing gameplay classes or the isolated review game mode')
    defaults = unreal.get_default_object(mode.generated_class())
    previous_pawn = defaults.get_editor_property('default_pawn_class')
    defaults.set_editor_property('default_pawn_class', guide_class)
    defaults.set_editor_property('player_controller_class', controller_class)
    unreal.BlueprintEditorLibrary.compile_blueprint(mode)
    defaults = unreal.get_default_object(mode.generated_class())
    if defaults.get_editor_property('default_pawn_class') != guide_class:
        raise RuntimeError('Review game mode did not retain its gameplay pawn')
    if not unreal.EditorAssetLibrary.save_loaded_asset(mode, only_if_is_dirty=False):
        raise RuntimeError('Review game mode save failed')
    world.get_world_settings().set_editor_property('default_game_mode', mode.generated_class())
    actor = owners[0]
    before = [str(tag) for tag in actor.tags]
    actor.tags = [unreal.Name(tag) for tag in dict.fromkeys(before + ['RaftSimPhysicalGround'])]
    if not levels.save_current_level():
        raise RuntimeError('Review collision registration save failed')
    report = {'level': LEVEL, 'mesh': MESH, 'previous_tags': before,
              'tags': [str(tag) for tag in actor.tags], 'production_modified': False,
              'previous_pawn_class': previous_pawn.get_path_name() if previous_pawn else None,
              'pawn_class': guide_class.get_path_name(),
              'collision_traversal_accepted': False}
    output = ROOT / 'docs/reconstruction-review-2026-09-07'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'runtime_registration.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log(json.dumps(report))


if __name__ == '__main__':
    main()
