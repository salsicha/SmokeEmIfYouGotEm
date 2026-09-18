"""Add source-supported put-in canopy to normal South Fork, not a new scenario.

Every inferred root is checked against actual terrain collision before saving
and after a level reload. Existing terrain, hydraulics, and rapid canopy stay
byte-identical. Small spatial groups keep World Partition ownership local.
"""
import hashlib
import json
from pathlib import Path
import zipfile

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/chili_bar/canopy_20260918/placement.json'
SOURCE_SHA = '6ec5e61274dd44aa2ed4d187ffe8252b118f06e231e2c2267de69ec8027f54e3'
MAP_SHA = 'a220724f5ac1df61aeeb9ea1e86f51cf43f20d101a62345120c96839829e4d7a'
PROFILE_SHA = 'a4b12527ef6dd8c6ac0d2eb0c4c790c66626a9a8d48c4d02ebb19af5a434d42b'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/chili-bar-canopy-integration-v1-20260918.json'
BACKUP = REPORT.with_suffix('.before.zip')
NAMES = ('canopy_a','canopy_b','canopy_c')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def package_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def xyz(vector):
    return [vector.x,vector.y,vector.z]


def roots(subsystem, ground_names, rows):
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    loaded = subsystem.get_all_level_actors()
    assert ground_names.issubset({actor.get_name() for actor in loaded})
    ignore = [actor for actor in loaded if actor.get_name() not in ground_names]
    maximum = 0.
    for row in rows:
        x,y,z = row['world_root_cm']
        hit = unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+1000),
            unreal.Vector(x,y,z-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,
            ignore,unreal.DrawDebugTrace.NONE,False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], ('Missing actual ground collision',row['id'])
        error = max(abs(values[5].x-x),abs(values[5].y-y),abs(values[5].z-z))
        assert error <= .1, ('Root differs from rendered/collision terrain',row['id'],error)
        maximum = max(maximum,error)
    return maximum


def verify(canopy, rows, data):
    assert canopy.get_editor_property('placement_source_sha256') == SOURCE_SHA
    assert xyz(canopy.get_actor_scale3d()) == [1.,1.,1.]
    rotation = canopy.get_actor_rotation()
    assert rotation.pitch == rotation.yaw == rotation.roll == 0
    assert 'RaftSimPhysicalGround' not in map(str,canopy.tags)
    errors = []
    for form,name in enumerate(NAMES):
        component = canopy.get_editor_property(name)
        expected = [row for row in rows if row['form_index'] == form]
        assert component.get_instance_count() == len(expected)
        assert component.static_mesh.get_path_name().split('.')[0] == data['assets'][form]['package']
        assert component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
        assert not component.get_editor_property('generate_overlap_events')
        bounds = component.static_mesh.get_bounding_box()
        for i,row in enumerate(expected):
            transform = component.get_instance_transform(i,True)
            point,scale = transform.translation,transform.scale3d
            x,y,z = row['world_root_cm']
            error = max(abs(point.x-x),abs(point.y-y),abs(point.z+bounds.min.z*scale.z-z),
                abs((bounds.max.z-bounds.min.z)*scale.z-row['height_m']*100))
            assert error <= .1, ('Stored root/height mismatch',row['id'],error)
            assert abs(scale.x-scale.y) < 1.e-6 and abs(scale.x-scale.z) < 1.e-6
            errors.append(error)
    assert len(errors) == len(rows)
    return max(errors)


def main():
    assert 'RaftSimIntegrateChiliBarCanopy' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists() and not BACKUP.exists(), 'Inspect earlier mutation before retrying'
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    profile = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert sha(SOURCE) == SOURCE_SHA and sha(map_file) == MAP_SHA and sha(profile) == PROFILE_SHA
    data = json.loads(SOURCE.read_text())
    assert data['level'] == LEVEL and data['scenario_id'] == 'south_fork_full_descent'
    assert data['no_rapid_scenario'] and not data['tree_inventory_surveyed']
    assert not data['terrain_or_hydraulic_geometry_modified'] and not data['normal_map_integrated']
    assert data['world_y_sign'] == -1 and data['vertical_datum_m'] == 220
    rows = data['instances']
    assert len(rows) == data['instance_count'] > 0 and len({r['id'] for r in rows}) == len(rows)
    protected = {ROOT/name:digest for name,digest in data['sources'].items()}
    source = json.loads((SOURCE.parent/'source.json').read_text())
    audit_path = SOURCE.parent/'source_audit.json'
    source_audit = json.loads(audit_path.read_text())
    assert source_audit['passed'] and source_audit['every_record_replayed_exactly']
    assert source_audit['source_manifest_sha256'] == sha(SOURCE.parent/'source.json')
    assert source_audit['payload_sha256'] == source['payload_sha256']
    assert source_audit['retained_nonwithheld_points'] == source['return_count']
    protected[audit_path] = sha(audit_path)
    protected.update({ROOT/name:digest for name,digest in source['sources'].items()})
    protected.update({ROOT/r['file']:r['sha256'] for name,r in source.get('provider_sources',{}).items() if not name.startswith('ept-data/')})
    protected.update({package_file(row['package']):row['sha256'] for row in data['assets']})
    protected[SOURCE] = SOURCE_SHA
    for path,digest in protected.items():
        assert path.resolve().is_relative_to(ROOT) and sha(path) == digest
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert levels.load_level(LEVEL)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == 457
    assert not any(str(d.label).startswith('Chili Bar captured canopy') for d in descriptors)
    before = {str(d.actor_package):sha(package_file(str(d.actor_package))) for d in descriptors}
    # Load only actual physical-ground packages intersecting the put-in crop.
    xs,ys = [r['world_root_cm'][0] for r in rows],[r['world_root_cm'][1] for r in rows]
    ground_descs = [d for d in descriptors if str(d.label).startswith(('SouthFork_coarse_terrain_','SouthFork_captured_context_'))
        and d.bounds.min.x <= max(xs) and d.bounds.max.x >= min(xs)
        and d.bounds.min.y <= max(ys) and d.bounds.max.y >= min(ys)]
    assert ground_descs
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ground_descs])
    ground_names = {str(d.name) for d in ground_descs}
    for actor in subsystem.get_all_level_actors():
        if actor.get_name() in ground_names:
            assert 'RaftSimPhysicalGround' in map(str,actor.tags)
    before_root_error = roots(subsystem,ground_names,rows)
    groups = {}
    for row in rows:
        x,y,_ = row['world_root_cm']
        key = (int(x//25600),int(y//25600))
        groups.setdefault(key,[]).append(row)
    with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(map_file,map_file.relative_to(ROOT).as_posix())
        archive.writestr('external_packages_before.json',json.dumps(before,indent=2))
    canopy_class = unreal.load_class(None,'/Script/RaftSimRaft.RaftSimCapturedCanopyActor')
    assert canopy_class
    created = []
    for (cx,cy),group in sorted(groups.items()):
        origin = unreal.Vector(cx*25600,cy*25600,0)
        canopy = subsystem.spawn_actor_from_class(canopy_class,origin)
        assert canopy
        label = f'Chili Bar captured canopy {cx} {cy} - inferred trees'
        canopy.set_actor_label(label)
        canopy.tags = [unreal.Name('RaftSimCapturedCanopy'),unreal.Name('InferredVegetationNotSurveyedTrees')]
        canopy.set_editor_property('placement_source_sha256',SOURCE_SHA)
        for form,name in enumerate(NAMES):
            component = canopy.get_editor_property(name)
            mesh = unreal.load_asset(data['assets'][form]['package'])
            assert mesh and component.set_static_mesh(mesh)
            bounds = mesh.get_bounding_box()
            assert bounds.max.z-bounds.min.z > 100
            for row in group:
                if row['form_index'] != form:
                    continue
                x,y,z = row['world_root_cm']
                scale = row['height_m']*100/(bounds.max.z-bounds.min.z)
                component.add_instance(unreal.Transform(location=unreal.Vector(x-origin.x,y-origin.y,z-bounds.min.z*scale),
                    rotation=unreal.Rotator(pitch=0,yaw=row['yaw_degrees'],roll=0),scale=unreal.Vector(scale,scale,scale)),False)
        error = verify(canopy,group,data)
        created.append(dict(name=canopy.get_name(),label=label,key=[cx,cy],instances=len(group),transform_error_cm=error))
    assert levels.save_current_level()
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,False)
    after = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    new = [d for d in after if str(d.actor_package) not in before]
    assert len(after) == len(before)+len(groups) and len(new) == len(groups)
    assert {str(d.name) for d in new} == {r['name'] for r in created}
    for desc in new:
        assert desc.native_class.get_name() == 'RaftSimCapturedCanopyActor' and desc.is_spatially_loaded
        assert not desc.actor_is_editor_only
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    assert levels.load_level(LEVEL)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ground_descs]+[d.guid for d in new])
    loaded = {a.get_name():a for a in subsystem.get_all_level_actors()}
    for record in created:
        record['reload_transform_error_cm'] = verify(loaded[record['name']],groups[tuple(record['key'])],data)
    after_root_error = roots(subsystem,ground_names,rows)
    assert len(unreal.WorldPartitionBlueprintLibrary.get_actor_descs()) == len(before)+len(groups)
    for package,digest in before.items():
        assert sha(package_file(package)) == digest, ('Existing actor changed',package)
    for path,digest in protected.items():
        assert sha(path) == digest, ('Source changed',str(path))
    assert sha(profile) == PROFILE_SHA
    catalog = unreal.RaftSimProgressionLibrary.get_scenario_catalog()
    assert any(str(s.scenario_id) == 'south_fork_full_descent' for s in catalog)
    assert all('troublemaker' not in str(s.scenario_id).lower() for s in catalog)
    result = dict(schema='raftsim.chili_bar.canopy_integration.v1',level=LEVEL,placement_sha256=SOURCE_SHA,
        instance_count=len(rows),actors=created,previous_external_actor_count=len(before),external_actor_count=len(after),
        new_packages=[dict(package=str(d.actor_package),sha256=sha(package_file(str(d.actor_package)))) for d in new],
        previous_map_sha256=MAP_SHA,map_sha256=sha(map_file),profile_sha256=PROFILE_SHA,
        root_probe_count_before=len(rows),root_probe_count_after_reload=len(rows),
        maximum_root_collision_error_cm=max(before_root_error,after_root_error),
        old_external_packages_unchanged=True,source_assets_unchanged=True,profile_unchanged=True,
        backup=BACKUP.relative_to(ROOT).as_posix(),backup_sha256=sha(BACKUP),
        normal_map_integrated=True,reload_verified=True,no_rapid_scenario=True,tree_inventory_surveyed=False,
        terrain_or_hydraulic_geometry_modified=False,canopy_collision_enabled=False,
        scope='Supported dry ground within retained Chili Bar imagery only; inferred crown forms and trunk locations',
        photoreal_accepted=False,runtime_motion_and_performance_verified=False)
    with REPORT.open('x') as stream:
        json.dump(result,stream,indent=2); stream.write('\n')
    unreal.log('CHILI BAR CANOPY INTEGRATION VERIFIED: '+str(REPORT))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
