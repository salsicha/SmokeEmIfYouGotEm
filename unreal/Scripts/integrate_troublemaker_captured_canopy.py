"""Persist source-constrained canopy in the NORMAL Troublemaker challenge."""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_canopy.json'
LEVEL = '/Game/RaftSim/Maps/L_SouthFork_Troublemaker'
LEVEL_FILE = ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/troublemaker-canopy-integration-20260912.json'
FORMS = ('SpreadingMature', 'CompactRiverEdge', 'AsymmetricCompetition')
PREFIX = '/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads(SOURCE.read_text())
    assert data['normal_playable_level'] == LEVEL and data['world_y_sign'] == -1
    assert not data['terrain_or_hydraulic_geometry_modified']
    assert not data['tree_inventory_surveyed']
    for path, digest in data['sources'].items():
        assert sha(ROOT/path) == digest, path
    delivery_path = SOURCE.with_name('playable_flow')/'delivery.json'
    delivery = json.loads(delivery_path.read_text())
    assert data['source_geometry_sha256'] == delivery['source_geometry_sha256']
    for path, digest in delivery['files'].items():
        assert sha(delivery_path.parent/path) == digest
    before = sha(LEVEL_FILE)
    backup = ROOT/'tmp/troublemaker-canopy-map-backup'/f'{before}.umap'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(LEVEL_FILE, backup)
    assert sha(backup) == before

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == LEVEL
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actors.get_all_level_actors()
    ground = [a for a in all_actors if unreal.Name('RaftSimPhysicalGround') in a.tags]
    assert len(ground) == 1
    ground = ground[0]
    ground_mesh = ground.static_mesh_component.static_mesh
    ground_file = ROOT/('unreal/Content'+ground_mesh.get_path_name().split('.')[0][5:]+'.uasset')
    ground_sha = sha(ground_file)
    assert ground.get_actor_scale3d() == unreal.Vector(1, -1, 1)
    existing = [a for a in all_actors if a.get_class().get_name() == 'RaftSimCapturedCanopyActor']
    assert len(existing) <= 1
    canopy_class = unreal.load_class(None, '/Script/RaftSimRaft.RaftSimCapturedCanopyActor')
    assert canopy_class
    canopy = existing[0] if existing else actors.spawn_actor_from_class(canopy_class, unreal.Vector())
    canopy.set_actor_label('Captured bank canopy - inferred trunks and species')
    canopy.tags = [unreal.Name('RaftSimCapturedCanopy'), unreal.Name('InferredVegetationNotSurveyedTrees')]
    canopy.set_editor_property('placement_source_sha256', sha(SOURCE))
    components = [canopy.get_editor_property(name) for name in ('canopy_a', 'canopy_b', 'canopy_c')]
    bounds = []
    meshes = []
    for component, form in zip(components, FORMS):
        mesh = unreal.load_asset(PREFIX+form)
        assert mesh
        box = mesh.get_bounding_box()
        assert box.max.z-box.min.z > 100
        component.clear_instances()
        component.set_static_mesh(mesh)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        assert not component.get_editor_property('generate_overlap_events')
        component.set_cull_distances(0, 0)
        component.set_cast_shadow(True)
        bounds.append(box)
        meshes.append({'asset': mesh.get_path_name(), 'lod_triangles': [mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())],
                       'bounds_height_cm': box.max.z-box.min.z})
    # Loaded mesh collision is not queryable until async asset compilation has
    # completed. Do not interpret an early miss as permission to snap/move roots.
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    errors = []
    transforms = []
    root_failures = []
    for record in data['instances']:
        x,y,z = record['location_cm']
        assert record['ground_authority'] == 1 and record['support_return_count'] >= 12
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,z+100), unreal.Vector(x,y,z-100),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a for a in all_actors if a != ground],
            unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        if not values or not values[0] or abs(values[5].z-z) >= .1:
            root_failures.append({'instance': record, 'hit': str(values),
                                  'ground_location': str(ground.get_actor_location()),
                                  'ground_rotation': str(ground.get_actor_rotation())})
            continue
        errors.append(abs(values[5].z-z))
        form = record['form_index']
        box = bounds[form]
        scale = record['height_m']*100/(box.max.z-box.min.z)
        # Correct the actual mesh base, not an assumed zero pivot.
        transform = unreal.Transform(location=unreal.Vector(x,y,z-box.min.z*scale),
            rotation=unreal.Rotator(pitch=0,yaw=record['yaw_degrees'],roll=0),
            scale=unreal.Vector(scale,scale,scale))
        components[form].add_instance(transform, False)
        transforms.append({'form': form, 'height_m': record['height_m'], 'scale': scale})
    if root_failures:
        failure_path = REPORT.with_name('troublemaker-canopy-root-failures-20260912.json')
        failure_path.write_text(json.dumps({'failures': root_failures, 'passed':len(errors)},indent=2)+'\n')
        raise AssertionError(f'{len(root_failures)} root probes failed; details: {failure_path}')
    assert sum(c.get_instance_count() for c in components) == data['instance_count']
    # Recheck existing river/rock collision probes, not just the new dry roots.
    prior = json.loads((ROOT/'docs/reconstruction-review-2026-09-07/geographic-scene/staging.json').read_text())
    river_errors = []
    for record in prior['collision_probes']:
        x,y,z = record['position_cm']
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,z+1000), unreal.Vector(x,y,z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a for a in all_actors if a != ground],
            unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0] and abs(values[5].z-z) <= .1
        river_errors.append(abs(values[5].z-z))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert levels.save_current_level()
    assert sha(ground_file) == ground_sha
    for path, digest in delivery['files'].items():
        assert sha(delivery_path.parent/path) == digest
    result = {'normal_playable_level': LEVEL, 'source_sha256': sha(SOURCE),
        'map_before_sha256': before, 'map_after_sha256': sha(LEVEL_FILE), 'backup': str(backup),
        'canopy_instances': len(transforms), 'hism_component_count': 3,
        'root_probe_count': len(errors), 'maximum_root_height_error_cm': max(errors),
        'river_collision_probe_count': len(river_errors), 'maximum_river_collision_error_cm': max(river_errors),
        'ground_mesh_unchanged': True, 'ground_mesh_sha256': ground_sha, 'hydraulic_fields_unchanged': True,
        'meshes': meshes, 'canopy_collision_enabled': False, 'canopy_inventory_surveyed': False,
        'photoreal_accepted': False, 'motion_and_performance_verified': False}
    REPORT.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log(f'Normal captured Troublemaker canopy saved: {json.dumps(result)}')


if __name__ == '__main__':
    main()
