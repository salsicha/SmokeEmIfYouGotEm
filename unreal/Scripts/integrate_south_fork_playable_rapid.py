"""Create the ordinary challenge from matched captured geometry and flow."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
BASE = '/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable'
LEVEL = '/Game/RaftSim/Maps/L_SouthFork_Troublemaker'
BASE_FILE = ROOT / 'unreal/Content/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable.umap'
BASE_SHA = '36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96'
FIELDS = 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
ASSETS = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker'
OUTPUT = ROOT / 'unreal/Saved/RaftSimValidation/southfork-playable-integration-20260912.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha(BASE_FILE) == BASE_SHA, 'Source map changed; re-audit it before integration'
    assert not unreal.EditorAssetLibrary.does_asset_exist(LEVEL), 'Inspect existing integration before repeating'
    delivery = json.loads((ROOT / FIELDS / 'delivery.json').read_text())
    for name, expected in delivery['files'].items():
        assert sha(ROOT / FIELDS / name) == expected, name
    water_source = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_CurrentNormalReviewV2'
    water_path = ASSETS + '/M_TroublemakerWater'
    assert not unreal.EditorAssetLibrary.does_asset_exist(water_path)
    water = unreal.EditorAssetLibrary.duplicate_asset(water_source, water_path)
    assert water and unreal.EditorAssetLibrary.save_loaded_asset(water, only_if_is_dirty=False)

    # Surface appearance only: use existing rights-tracked world-projected
    # rock PBR, not the diagnostic checkerboard. No displacement or invented
    # fixed waterline; measured/inferred geometry remains the exact source mesh.
    ground_parent = unreal.load_asset('/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/M_RaftSim_SouthForkBoulderDressing')
    assert ground_parent
    assert unreal.MaterialEditingLibrary.get_material_property_input_node(
        ground_parent, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None
    ground_material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'MI_TroublemakerGround', ASSETS, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
    assert ground_material
    unreal.MaterialEditingLibrary.set_material_instance_parent(ground_material, ground_parent)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(ground_material, 'RockWaterlineZCm', -1000000.0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(ground_material, only_if_is_dirty=False)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.new_level_from_template(LEVEL, BASE)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == LEVEL
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()

    def one(predicate):
        matches = [actor for actor in actors if predicate(actor)]
        assert len(matches) == 1
        return matches[0]

    ground = one(lambda a: isinstance(a, unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags)
    config = one(lambda a: a.get_class().get_name() == 'RaftSimRiverWaterConfig')
    surface = one(lambda a: a.get_class().get_name() == 'RaftSimWaterSurfaceActor')
    raft = one(lambda a: a.get_class().get_name() == 'RaftSimRaftActor')
    assert ground.static_mesh_component.static_mesh.get_path_name() == '/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate.SM_TroublemakerSurveyCandidate'
    assert ground.get_actor_scale3d() == unreal.Vector(1, -1, 1)
    ground.static_mesh_component.set_material(0, ground_material)
    config.set_editor_property('cooked_fields_dir', FIELDS)
    config.set_editor_property('coordinate_map_path', FIELDS + '/coordinate_map.json')
    config.set_editor_property('live_presentation_hydraulic_relief_scale', 1.0)
    assert not config.get_editor_property('enable_live_raft_local_fluid_heightfield')
    assert not config.get_editor_property('enable_live_solver_volume_core')
    assert not config.get_editor_property('enable_moving_window_streaming')
    assert config.get_editor_property('live_presentation_standing_wave_scale') == 0
    surface.set_editor_property('water_material', water)
    assert surface.get_editor_property('fixed_curved_grid')
    mode = unreal.load_class(None, '/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode')
    assert mode
    world.get_world_settings().set_editor_property('default_game_mode', mode)
    # The native gameplay mode owns its own optional validation director.
    for actor in actors:
        if actor.get_class().get_name() == 'RaftSimContentLockDirector':
            assert subsystem.destroy_actor(actor)

    prior = json.loads((ROOT / 'docs/reconstruction-review-2026-09-07/geographic-scene/staging.json').read_text())
    probes = []
    for record in prior['collision_probes']:
        x, y, z = record['position_cm']
        hit = unreal.SystemLibrary.line_trace_single(world,
            unreal.Vector(x, y, z+1000), unreal.Vector(x, y, z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
            [a for a in actors if a != ground and a.get_class().get_name() != 'RaftSimContentLockDirector'],
            unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0] and abs(values[5].z-z) <= .1, record
        probes.append(abs(values[5].z-z))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert levels.save_current_level()
    assert sha(BASE_FILE) == BASE_SHA

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(synchronous_search=True)
    options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
    visited = set()
    pending = [LEVEL]
    while pending:
        package = pending.pop()
        if package in visited or not package.startswith('/Game/'):
            continue
        visited.add(package)
        assert not package.startswith('/Game/RaftSim/Maps/Review/')
        assert not package.startswith('/Game/RaftSim/Environment/SouthForkSurveyCandidate/'), package
        pending.extend(str(p) for p in registry.get_dependencies(package, options))
    report = {'level': LEVEL, 'fields': FIELDS, 'source_map_unchanged': True,
              'source_map_sha256': BASE_SHA, 'source_geometry_sha256': delivery['source_geometry_sha256'],
              'collision_probe_count': len(probes), 'maximum_collision_height_error_cm': max(probes),
              'raft_start_cm': [raft.get_actor_location().x, raft.get_actor_location().y, raft.get_actor_location().z],
              'game_mode': mode.get_path_name(), 'water_material': water.get_path_name(),
              'ground_material': ground_material.get_path_name(),
              'recursive_game_dependencies': sorted(visited),
              'no_never_cook_review_dependencies': True, 'full_reconstruction_accepted': False,
              'ground_texture_appearance_measured': False, 'runtime_traversal_verified': False}
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log(f'Captured rapid connected to gameplay package: {OUTPUT}')


if __name__ == '__main__':
    main()
