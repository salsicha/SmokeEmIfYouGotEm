"""Migrate the retained rapid-bank canopy into the South Fork scenario.

One new external actor, no terrain/water edits and no separate rapid scenario.
The retained tree inventory and forms are inferred, not surveyed or accepted art.
"""
import hashlib
import json
from pathlib import Path
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/captured_canopy_placement_v1.json'
SOURCE_SHA = '7147f349c5d32893440b2bf63ebd404aedebadceab1751ee4ae2a9f78cbc347c'
MAP_SHA = '3d52dd5bdfdf4fb9a3e0c57fa728e437cef16ccc0bf827892458e55ee8eade77'
PROFILE_SHA = '181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1'
GROUND_NAME = 'StaticMeshActor_UAID_04421A89ABE5ED0003_2136936984'
GROUND_PACKAGE_SHA = '315f035f39e1293a1648ff82c925bb51bfce4c1bf837e03ce8bdc3839d4538b4'
GROUND_MESH = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround'
GROUND_MESH_SHA = '6aec899c1dad1d26b8410813637f705c4fdd2552d5b4db718bb974eb6fa51a4a'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-canopy-integration-v1-20260912.json'
BACKUP = REPORT.with_name('south-fork-before-canopy-integration-v1-20260912.zip')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def xyz(vector):
    return [vector.x, vector.y, vector.z]


def verify_instances(canopy, data):
    assert xyz(canopy.get_actor_location()) == data['translation_cm']
    assert xyz(canopy.get_actor_scale3d()) == [1., 1., 1.]
    rotation = canopy.get_actor_rotation()
    assert rotation.pitch == rotation.yaw == rotation.roll == 0.
    assert canopy.get_editor_property('placement_source_sha256') == SOURCE_SHA
    assert 'RaftSimPhysicalGround' not in [str(tag) for tag in canopy.tags]
    errors, counts = [], []
    for form, name in enumerate(('canopy_a', 'canopy_b', 'canopy_c')):
        component = canopy.get_editor_property(name)
        expected = [row for row in data['instances'] if row['form_index'] == form]
        assert component.get_instance_count() == len(expected)
        counts.append(len(expected))
        assert component.static_mesh.get_path_name().split('.')[0] == data['assets'][form]['package']
        assert component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
        assert not component.get_editor_property('generate_overlap_events')
        bounds = component.static_mesh.get_bounding_box()
        for index, row in enumerate(expected):
            transform = component.get_instance_transform(index, True)
            position, scale = transform.translation, transform.scale3d
            x, y, z = row['world_root_cm']
            error = max(abs(position.x-x), abs(position.y-y),
                abs(position.z+bounds.min.z*scale.z-z),
                abs((bounds.max.z-bounds.min.z)*scale.z-row['height_m']*100))
            assert error <= .1, ('Saved canopy root or height changed', row['id'], error)
            errors.append(error)
    assert len(errors) == data['instance_count'] == 1268
    return dict(instance_count=len(errors), component_counts=counts,
                maximum_transform_or_height_error_cm=max(errors))


def verify_roots(actors, ground, data):
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = [actor for actor in actors.get_all_level_actors() if actor != ground]
    maximum = 0.
    for row in data['instances']:
        x, y, z = row['world_root_cm']
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,z+1000),
            unreal.Vector(x,y,z-1000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], ('Missing original root collision', row['id'])
        error = abs(values[5].z-z)
        assert error <= .1, ('Original root collision changed', row['id'], error)
        maximum = max(maximum, error)
    return maximum


def main():
    assert 'RaftSimIntegrateSouthForkCanopy' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists() and not BACKUP.exists(), 'Do not repeat a map mutation blindly'
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    profile = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert sha(map_file) == MAP_SHA and sha(profile) == PROFILE_SHA
    assert sha(SOURCE) == SOURCE_SHA
    data = json.loads(SOURCE.read_text())
    assert data['level'] == LEVEL and data['scenario_id'] == 'south_fork_full_descent'
    assert data['no_rapid_scenario'] and not data['tree_inventory_surveyed']
    assert not data['terrain_or_hydraulic_geometry_modified'] and not data['photoreal_accepted']
    assert data['world_y_sign'] == -1 and data['original_instances_unchanged']
    protected = {ROOT/path: digest for path, digest in data['dependencies'].items()}
    protected.update({package_file(row['package']): row['sha256'] for row in data['assets']})
    protected[package_file(GROUND_MESH)] = GROUND_MESH_SHA
    protected[SOURCE] = SOURCE_SHA
    # Preserve the original source evidence as well as the new placement manifest.
    original = json.loads((ROOT/data['source_canopy']).read_text())
    protected.update({ROOT/path: digest for path, digest in original['sources'].items()})
    for path, digest in protected.items():
        assert path.resolve().is_relative_to(ROOT) and sha(path) == digest, str(path)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == 455
    assert not any(d.native_class.get_name() == 'RaftSimCapturedCanopyActor' for d in descriptors)
    ground_desc = next(d for d in descriptors if str(d.name) == GROUND_NAME)
    assert sha(package_file(str(ground_desc.actor_package))) == GROUND_PACKAGE_SHA
    before = {str(d.actor_package): sha(package_file(str(d.actor_package))) for d in descriptors}
    unreal.WorldPartitionBlueprintLibrary.load_actors([ground_desc.guid])
    ground = next(a for a in actors.get_all_level_actors() if a.get_name() == GROUND_NAME)
    assert ground.static_mesh_component.static_mesh.get_path_name().split('.')[0] == GROUND_MESH
    assert xyz(ground.get_actor_location()) == data['translation_cm']
    assert xyz(ground.get_actor_scale3d()) == [1., -1., 1.]
    root_error_before = verify_roots(actors, ground, data)
    # The old external actors are read-only; the backup records all their hashes
    # and retains the map bytes, so the single new package can be identified.
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(map_file, map_file.relative_to(ROOT).as_posix())
        archive.writestr('external_packages_before.json', json.dumps(before, indent=2))
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(map_file.relative_to(ROOT).as_posix())).hexdigest() == MAP_SHA
    canopy_class = unreal.load_class(None, '/Script/RaftSimRaft.RaftSimCapturedCanopyActor')
    assert canopy_class
    canopy = actors.spawn_actor_from_class(canopy_class, unreal.Vector(*data['translation_cm']))
    assert canopy
    canopy.set_actor_label('South Fork captured rapid-bank canopy - inferred trees')
    canopy.tags = [unreal.Name('RaftSimCapturedCanopy'), unreal.Name('InferredVegetationNotSurveyedTrees')]
    canopy.set_editor_property('placement_source_sha256', SOURCE_SHA)
    for form, name in enumerate(('canopy_a', 'canopy_b', 'canopy_c')):
        component = canopy.get_editor_property(name)
        mesh = unreal.load_asset(data['assets'][form]['package'])
        assert mesh and component.set_static_mesh(mesh)
        bounds = mesh.get_bounding_box()
        assert bounds.max.z-bounds.min.z > 100
        for row in data['instances']:
            if row['form_index'] != form:
                continue
            # Local positions already use east/-north. Translate exactly once
            # via the actor, never copy the ground mesh's reflected Y scale.
            x, y, z = row['location_cm']
            scale = row['height_m']*100/(bounds.max.z-bounds.min.z)
            component.add_instance(unreal.Transform(location=unreal.Vector(x,y,z-bounds.min.z*scale),
                rotation=unreal.Rotator(pitch=0, yaw=row['yaw_degrees'], roll=0),
                scale=unreal.Vector(scale,scale,scale)), False)
    initial = verify_instances(canopy, data)
    assert levels.save_current_level()
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    after = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    new = [d for d in after if str(d.actor_package) not in before]
    assert len(after) == 456 and len(new) == 1
    assert new[0].native_class.get_name() == 'RaftSimCapturedCanopyActor'
    canopy_package = str(new[0].actor_package)
    canopy_name, canopy_guid = str(new[0].name), new[0].guid
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    assert levels.load_level(LEVEL)
    unreal.WorldPartitionBlueprintLibrary.load_actors([ground_desc.guid, canopy_guid])
    loaded = actors.get_all_level_actors()
    canopy = next(a for a in loaded if a.get_name() == canopy_name)
    ground = next(a for a in loaded if a.get_name() == GROUND_NAME)
    reloaded = verify_instances(canopy, data)
    assert initial == reloaded
    root_error_after = verify_roots(actors, ground, data)
    assert len(unreal.WorldPartitionBlueprintLibrary.get_actor_descs()) == 456
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(synchronous_search=True)
    options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
    seen, pending = set(), [row['package'] for row in data['assets']]
    while pending:
        package = pending.pop()
        if package in seen or not package.startswith('/Game/'):
            continue
        assert not package.startswith(('/Game/RaftSim/Maps/Review/', '/Game/RaftSim/Environment/SouthForkSurveyCandidate/'))
        assert package_file(package).exists(), package
        seen.add(package)
        pending.extend(str(p) for p in registry.get_dependencies(package, options))
    for package, digest in before.items():
        assert sha(package_file(package)) == digest, ('Unrelated actor changed', package)
    for path, digest in protected.items():
        assert sha(path) == digest, ('Source asset changed', str(path))
    assert sha(profile) == PROFILE_SHA
    catalog = unreal.RaftSimProgressionLibrary.get_scenario_catalog()
    assert any(str(s.scenario_id) == 'south_fork_full_descent' for s in catalog)
    assert all(str(s.scenario_id) != 'troublemaker_challenge' and str(s.level_name) != data['retired_source_level'] for s in catalog)
    result = dict(schema='raftsim.south_fork.canopy_integration.v1', level=LEVEL,
        scenario_id=data['scenario_id'], placement_sha256=SOURCE_SHA, **reloaded,
        root_probe_count_before=1268, root_probe_count_after_reload=1268,
        maximum_root_collision_error_cm=max(root_error_before,root_error_after),
        actor=canopy_name, actor_package=canopy_package, actor_package_sha256=sha(package_file(canopy_package)),
        previous_external_actor_count=455, external_actor_count=456,
        previous_map_sha256=MAP_SHA, map_sha256=sha(map_file),
        backup=str(BACKUP.relative_to(ROOT)), backup_sha256=sha(BACKUP),
        old_external_packages_unchanged=True, source_assets_unchanged=True, profile_unchanged=True,
        terrain_or_hydraulic_geometry_modified=False, canopy_collision_enabled=False,
        no_rapid_scenario=True, reload_verified=True, canopy_dependencies=sorted(seen),
        no_never_cook_canopy_dependencies=True, tree_inventory_surveyed=False,
        scope='Original 360 x 280 m rapid survey footprint only; not the entire river canopy.',
        photoreal_accepted=False, runtime_motion_and_performance_verified=False)
    REPORT.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log(f'South Fork canopy integration verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
