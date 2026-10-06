"""Read-only saved-actor audit for the diagnosed checkpoint terrain gap."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
OUTPUT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-checkpoint-saved-terrain-v1-20260924.json'
NAMES = ['context1024_2560_2560', 'coarse_2432_2816', 'coarse_2560_2816',
         'coarse_2560_2688', 'coarse_2688_2688', 'coarse_2688_2560',
         'coarse_2816_2560', 'coarse_2816_2432', 'coarse_2560_2432']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not OUTPUT.exists(), 'Preserve previous evidence'
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    before = digest(map_file)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    rows = []
    protected = {}
    for name in NAMES:
        matches = [d for d in descs if str(d.label).endswith('SM_SouthFork_'+name)]
        entry = dict(mesh_name='SM_SouthFork_'+name, descriptors=[])
        for desc in matches:
            package = str(desc.actor_package)
            path = ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')
            protected[path] = digest(path)
            unreal.WorldPartitionBlueprintLibrary.load_actors([desc.guid])
            actors = [a for a in subsystem.get_all_level_actors() if a.get_name() == str(desc.name)]
            assert len(actors) == 1, (name, len(actors))
            actor = actors[0]
            component = actor.static_mesh_component
            entry['descriptors'].append(dict(label=str(desc.label), package=package,
                package_sha256=protected[path], spatially_loaded=desc.is_spatially_loaded,
                editor_only=desc.actor_is_editor_only,
                runtime_grid=str(actor.get_editor_property('runtime_grid')),
                mesh=component.static_mesh.get_path_name(),
                transform=str(actor.get_actor_transform()),
                hidden=actor.get_editor_property('hidden'),
                visible=component.get_editor_property('visible')))
            unreal.WorldPartitionBlueprintLibrary.unload_actors([desc.guid])
        rows.append(entry)
    assert digest(map_file) == before
    assert all(digest(p) == h for p, h in protected.items())
    OUTPUT.write_text(json.dumps(dict(saved_nothing=True, map_sha256=before,
        terrain=rows), indent=2)+'\n')
    unreal.log(str(OUTPUT))

if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
