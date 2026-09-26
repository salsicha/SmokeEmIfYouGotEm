"""Give the terrain backdrop the material the placed coarse tiles actually render.

The placed tile actors override their meshes' default slot with the draped
composite ground material; the backdrop mesh was imported with the tiles' mesh
default and so rendered the untextured fallback colour past the loading range.
Only the backdrop static mesh asset is saved; no map or actor package changes.
Environment: RAFTSIM_BACKDROP_MATERIAL_REPORT (fresh repo tmp JSON).
"""
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
BACKDROPS = ['/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Backdrop/SM_SouthFork_terrain_backdrop_8m',
             '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Backdrop/SM_SouthFork_terrain_backdrop_outer_16m']


def main():
    report_path = ROOT / os.environ['RAFTSIM_BACKDROP_MATERIAL_REPORT']
    assert report_path.is_relative_to(ROOT / 'tmp') and not report_path.exists()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if str(d.label).startswith('SouthFork_coarse_terrain')][:3]
    assert descs, 'No coarse tile actor descriptors'
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    names = {str(d.name) for d in descs}
    actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
              if a.get_name() in names]
    materials = sorted({a.static_mesh_component.get_material(0).get_path_name() for a in actors})
    assert len(materials) == 1, materials
    material = unreal.load_asset(materials[0].split('.')[0])
    changed = []
    for path in BACKDROPS:
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        mesh = unreal.load_asset(path)
        before = mesh.get_material(0).get_path_name()
        if before != material.get_path_name():
            mesh.set_material(0, material)
            assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        changed.append(dict(backdrop=path, material_before=before))
    report = dict(backdrops=changed, material_after=material.get_path_name(),
                  sampled_tile_actors=[a.get_actor_label() for a in actors])
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_BACKDROP_MATERIAL ' + json.dumps(report))


if __name__ == '__main__':
    main()
