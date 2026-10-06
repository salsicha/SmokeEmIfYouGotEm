"""Fresh-process read-only proof of normal South Fork reconstruction persistence.

Emits the real saved bindings for the exact runtime dependency packager.
No preview flag, asset/level save, fallback geometry, or acceptance override.
"""
import json
import os
from pathlib import Path
import sys

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
sys.path.insert(0, str(ROOT / 'unreal/Scripts'))
from prepare_south_fork_joint_preview import asset_file, require
from package_runtime_bundle import sha
from install_south_fork_source_matched_reconstruction import native, xyz, LEVEL


def main():
    receipt_path = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_INSTALL_REPORT']).resolve()
    output = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_RELOAD_REPORT']).resolve()
    bindings_path = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_BINDINGS']).resolve()
    for path in (output, bindings_path):
        require(path.is_relative_to(ROOT / 'tmp') and not path.exists(), 'Fresh local report required')
    receipt = json.loads(receipt_path.read_text())
    require(receipt['normal_map_saved'] is True and receipt['level'] == LEVEL, 'Normal installation receipt required')
    require(sha(ROOT / receipt['descriptor']) == receipt['descriptor_sha256'], 'Descriptor changed')
    descriptor = json.loads((ROOT / receipt['descriptor']).read_text())
    require(sha(ROOT / receipt['preflight']) == receipt['preflight_sha256'], 'Preflight changed')
    preflight = json.loads((ROOT / receipt['preflight']).read_text())
    for name, digest in receipt['changed_saved_files'].items():
        require(sha(ROOT / name) == digest, 'Saved installation changed: ' + name)
    for name, digest in preflight['protected_files'].items():
        if name not in receipt['changed_saved_files']:
            require(sha(ROOT / name) == digest, 'Unrelated saved file changed: ' + name)
    for name, digest in descriptor['dependencies'].items():
        require(sha(ROOT / name) == digest, 'Source dependency changed: ' + name)
    require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL), 'Normal map load failed')
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    by_name = {str(row.name): row for row in descs}
    names = [receipt['original_terrain_actor'], receipt['new_rock_actor']]
    unreal.WorldPartitionBlueprintLibrary.load_actors([by_name[name].guid for name in names])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = {actor.get_name(): actor for actor in
              unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    mesh_proofs = []
    for name, row in zip(names, receipt['meshes']):
        actor = actors[name]
        component = actor.static_mesh_component
        mesh = component.static_mesh
        require(mesh.get_path_name().split('.')[0] == row['asset'], 'Saved mesh binding differs')
        require(sha(asset_file(row['asset'])) == row['sha256'], 'Production asset changed')
        require(xyz(actor.get_actor_location()) == descriptor['translation_cm'] and
                xyz(actor.get_actor_scale3d()) == [1., -1., 1.], 'Saved transform differs')
        rotation = actor.get_actor_rotation()
        require(max(abs(rotation.pitch), abs(rotation.yaw), abs(rotation.roll)) < .00001, 'Saved rotation differs')
        require(component.get_editor_property('disallow_nanite') is True, 'Exact render fallback not persisted')
        require(component.get_material(0).get_path_name() == descriptor['material_asset'], 'Saved material differs')
        require(str(component.get_collision_profile_name()) == 'BlockAll' and
                'RaftSimPhysicalGround' in map(str, actor.tags), 'Physical ground contract differs')
        mesh_proofs.append(native(mesh, row['native_source']['collision_source_sha256'],
                                 row['native_source']['triangle_count']))
    require(len([row for row in descs if row.native_class.get_name() == 'RaftSimWaterSurfaceActor']) == 1,
            'Multiple saved water surfaces')
    config, = [a for a in actors.values() if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors.values() if a.get_class().get_name() == 'RaftSimRunManager']
    full, = [row for row in preflight['launches'] if row['scenario_id'] == 'south_fork_full_descent']
    entries = dict(streaming_manifest=str(config.get_editor_property('streaming_manifest_path')),
        initial_fields_manifest=str(config.get_editor_property('cooked_fields_dir')).rstrip('/')+'/manifest.json',
        hydraulic_coordinate_map=str(config.get_editor_property('coordinate_map_path')),
        route_coordinate_map=str(manager.get_editor_property('progress_coordinate_map_path')))
    require(entries['streaming_manifest'] == descriptor['streaming_manifest'] and
            entries['initial_fields_manifest'] == full['initial_fields_manifest'] and
            entries['hydraulic_coordinate_map'] == descriptor['coordinate_map'], 'Saved water binding differs')
    center = config.get_editor_property('window_center_m')
    require([center.x, center.y] == full['window_center_m'], 'Saved launch crop differs')
    catalog = {str(row.scenario_id): row for row in unreal.RaftSimProgressionLibrary.get_scenario_catalog()}
    require('troublemaker_challenge' not in catalog, 'Rapid exposed as scenario')
    for row in preflight['launches']:
        item = catalog[row['scenario_id']]
        require(str(item.level_name) == LEVEL and abs(item.start_station_m-row['start_m']) < .002 and
                abs(item.finish_station_m-row['finish_m']) < .002, 'Saved catalog changed')
    bindings = {}
    for actor in (config, manager):
        package = str(by_name[actor.get_name()].actor_package)
        bindings[actor.get_class().get_name()] = dict(actor_name=actor.get_name(), package=package,
                                                    sha256=sha(asset_file(package)))
    map_path = ROOT / 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    # Include every current saved actor in the post-reload no-write proof.
    current = {map_path.relative_to(ROOT).as_posix(): sha(map_path)}
    for desc in descs:
        path = asset_file(str(desc.actor_package))
        current[path.relative_to(ROOT).as_posix()] = sha(path)
    for name, digest in receipt['changed_saved_files'].items():
        require(sha(ROOT / name) == digest, 'Read-only reload changed saved file')
    bindings_path.write_text(json.dumps(dict(schema='raftsim.saved_runtime_bindings.v1', level=LEVEL,
        map_sha256=sha(map_path), bindings=bindings, entrypoints=entries, saved_assets=False), indent=2)+'\n')
    output.write_text(json.dumps(dict(schema='raftsim.south_fork_source_matched_reload.v1', passed=True,
        installation_receipt=receipt_path.relative_to(ROOT).as_posix(), installation_sha256=sha(receipt_path),
        descriptor_sha256=receipt['descriptor_sha256'], source_time_seconds=receipt['source_time_seconds'],
        native_meshes=mesh_proofs, saved_actor_count=len(descs), saved_files=current,
        bindings=bindings_path.relative_to(ROOT).as_posix(), bindings_sha256=sha(bindings_path),
        one_saved_water_carrier=True, all_five_catalog_contracts_unchanged=True,
        exact_ground_fallback_persisted=True, source_dependencies_unchanged=True,
        saved_assets=False, fresh_process_reload=True, settled_hydraulics=False,
        visual_accepted=False, performance_accepted=False), indent=2)+'\n')
    unreal.log('Fresh normal South Fork reconstruction reload verified: ' + str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
