"""Install verified ground plus matching water into normal FullReach, with rollback files.

No new rock actor, overlay, solver mode, material or coordinate-map changes.
This is a playable candidate installation, not acceptance or equilibrium.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from package_runtime_bundle import Closure,sha
from south_fork_packet_geometry_identity import verify_packet_geometry_identity
from bind_south_fork_discharge_bed_runtime import entries
from verify_envelope_ground_union import package_file,LEVEL
DEST='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/ConveyanceEnvelope20260927/SM_ConveyanceGround'


def main():
    assert '-RaftSimInstallEnvelopeConveyance' in unreal.SystemLibrary.get_command_line()
    native_path=(ROOT/os.environ['RAFTSIM_ENVELOPE_NATIVE_REPORT']).resolve()
    export=(ROOT/os.environ['RAFTSIM_ENVELOPE_RUNTIME']).resolve()
    report=(ROOT/os.environ['RAFTSIM_ENVELOPE_INSTALL_REPORT']).resolve()
    assert all(p.is_relative_to(ROOT/'tmp') for p in (native_path,export,report)) and not report.exists()
    backup=report.with_suffix('.before.zip');assert not backup.exists()
    proof=json.loads(native_path.read_text())
    assert proof['schema']=='raftsim.envelope_ground_union_native.v1' and proof['passed']
    assert proof['normal_scene_restored'] and not proof['saved_assets'] and not proof['failures']
    for name,digest in proof['protected_files'].items():
        path=(ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and sha(path)==digest,('Scene/source changed since native check',name)
    probe_path=ROOT/proof['probes'];assert sha(probe_path)==proof['probes_sha256']
    probes=json.loads(probe_path.read_text())
    for name,digest in probes['dependencies'].items():assert sha(ROOT/name)==digest,('Changed dependency',name)
    geometry=json.loads((ROOT/probes['geometry_manifest']).read_text())
    audit=json.loads((export/'export_audit.json').read_text())
    assert audit['completed'] and audit['source_packet_count']==799 and audit['atlas_tile_count']==841
    assert audit['exact_bed_intersection_cells']>0 and audit['live_center_bounds_copied_unchanged']
    packet_path=ROOT/audit['source_packets_manifest'];assert sha(packet_path)==audit['source_packets_manifest_sha256']
    verify_packet_geometry_identity(json.loads(packet_path.read_text()),geometry)
    assert sha(export/'streaming_manifest_coverage_checked.json')==audit['streaming_manifest_sha256']
    assert sha(export/'atlas/manifest.json')==audit['atlas_manifest_sha256']
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    protected={package_file(str(d.actor_package)):sha(package_file(str(d.actor_package))) for d in descs}
    map_path=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected[map_path]=sha(map_path)
    selected=[d for d in descs if str(d.name) in (probes['ground_actor'],probes['rock_actor']) or
              d.native_class.get_name() in ('RaftSimRiverWaterConfig','RaftSimRunManager')]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selected])
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    ground,=[a for a in actors if a.get_name()==probes['ground_actor']]
    rock,=[a for a in actors if a.get_name()==probes['rock_actor']]
    config,=[a for a in actors if a.get_class().get_name()=='RaftSimRiverWaterConfig']
    manager,=[a for a in actors if a.get_class().get_name()=='RaftSimRunManager']
    before=entries(config,manager)
    assert before['streaming_manifest']=='tmp/discharge-bed-v2-runtime450-20260927/streaming_manifest_coverage_checked.json'
    window=before['initial_fields_manifest'].rsplit('/',2)[-2]
    updated=dict(before,streaming_manifest=(export/'streaming_manifest_coverage_checked.json').relative_to(ROOT).as_posix(),
                 initial_fields_manifest=(export/window/'manifest.json').relative_to(ROOT).as_posix())
    closure=Closure(ROOT);closure.collect(updated)  # Verify all transitive payload hashes before mutation.
    assert ground.static_mesh_component.static_mesh.get_path_name().split('.')[0]==probes['meshes']['ground_before']['asset']
    assert rock.static_mesh_component.static_mesh.get_path_name().split('.')[0]==probes['meshes']['rock']['asset']
    changed=[package_file(str(a.get_package().get_name())) for a in (ground,config)]
    with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
        for path in changed:z.write(path,path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(backup) as z:
        for path in changed:assert hashlib.sha256(z.read(path.relative_to(ROOT).as_posix())).hexdigest()==protected[path]
    assert not package_file(DEST).exists() and not unreal.EditorAssetLibrary.does_asset_exist(DEST)
    candidate=probes['meshes']['ground_candidate']
    mesh=unreal.EditorAssetLibrary.duplicate_asset(candidate['asset'],DEST)
    assert isinstance(mesh,unreal.StaticMesh)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    native=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
    assert native['collision_source_sha256']==candidate['native_sha256']
    assert native['triangle_count']==mesh.get_num_triangles(0)==candidate['triangle_count']
    assert mesh.get_material(0)==ground.static_mesh_component.get_material(0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
    ground.modify();ground.static_mesh_component.modify();config.modify()
    assert ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_editor_property('disallow_nanite',True)
    config.set_editor_property('streaming_manifest_path',updated['streaming_manifest'])
    config.set_editor_property('cooked_fields_dir',updated['initial_fields_manifest'].rsplit('/',1)[0])
    assert entries(config,manager)==updated
    # Save only the two intended external packages, never all dirty packages.
    assert unreal.EditorLoadingAndSavingUtils.save_packages([ground.get_package(),config.get_package()],False)
    for path,digest in protected.items():
        if path not in changed:assert sha(path)==digest,('Unrelated package changed',str(path))
    for name,digest in probes['dependencies'].items():assert sha(ROOT/name)==digest
    result=dict(schema='raftsim.envelope_conveyance_runtime_install.v1',before=before,after=updated,
        level=LEVEL,ground_actor=ground.get_name(),rock_actor=rock.get_name(),new_ground_asset=DEST,
        new_ground_package_sha256=sha(package_file(DEST)),native_source=native,
        backup=backup.relative_to(ROOT).as_posix(),backup_sha256=sha(backup),
        native_report=native_path.relative_to(ROOT).as_posix(),native_report_sha256=sha(native_path),
        changed_packages={p.relative_to(ROOT).as_posix():dict(before=protected[p],after=sha(p)) for p in changed},
        source_dependencies_unchanged=True,other_scene_packages_unchanged=True,
        normal_map_saved=True,fresh_reload_verified=False,settled_hydraulics=False,
        visual_accepted=False,performance_accepted=False)
    with report.open('x') as f:json.dump(result,f,indent=2)
    unreal.log('Candidate ground and matching water installed; fresh reload, rebuild and actual play required')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
