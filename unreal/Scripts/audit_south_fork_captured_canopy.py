"""Fresh-process, read-only verification of the saved South Fork canopy."""
import json
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_captured_canopy as integration


def main():
    root, level = integration.ROOT, integration.LEVEL
    output = root/'unreal/Saved/RaftSimValidation/south-fork-canopy-fresh-audit-v1-20260912.json'
    assert not output.exists()
    evidence = json.loads(integration.REPORT.read_text())
    data = json.loads(integration.SOURCE.read_text())
    map_file = root/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    profile = root/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert integration.sha(map_file) == evidence['map_sha256']
    assert integration.sha(integration.SOURCE) == integration.SOURCE_SHA
    assert integration.sha(profile) == integration.PROFILE_SHA
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(level)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == evidence['external_actor_count'] == 456
    canopies = [d for d in descriptors if d.native_class.get_name() == 'RaftSimCapturedCanopyActor']
    assert len(canopies) == 1 and str(canopies[0].actor_package) == evidence['actor_package']
    ground_desc = next(d for d in descriptors if str(d.name) == integration.GROUND_NAME)
    before = {str(d.actor_package): integration.sha(integration.package_file(str(d.actor_package))) for d in descriptors}
    assert before[evidence['actor_package']] == evidence['actor_package_sha256']
    assert before[str(ground_desc.actor_package)] == integration.GROUND_PACKAGE_SHA
    unreal.WorldPartitionBlueprintLibrary.load_actors([canopies[0].guid, ground_desc.guid])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    loaded = actors.get_all_level_actors()
    canopy = next(a for a in loaded if a.get_name() == evidence['actor'])
    ground = next(a for a in loaded if a.get_name() == integration.GROUND_NAME)
    assert ground.static_mesh_component.static_mesh.get_path_name().split('.')[0] == integration.GROUND_MESH
    result = integration.verify_instances(canopy, data)
    result['maximum_root_collision_error_cm'] = integration.verify_roots(actors, ground, data)
    for package, digest in before.items():
        assert integration.sha(integration.package_file(package)) == digest
    for row in data['assets']:
        assert integration.sha(integration.package_file(row['package'])) == row['sha256']
    assert integration.sha(map_file) == evidence['map_sha256']
    assert integration.sha(profile) == integration.PROFILE_SHA
    result.update(fresh_process=True, read_only=True, level=level, no_duplicate_canopy_actor=True,
                  external_actor_count=456, map_sha256=evidence['map_sha256'],
                  map_actors_and_profile_unchanged=True, photoreal_accepted=False)
    output.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log(f'Fresh South Fork canopy audit passed: {output}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
