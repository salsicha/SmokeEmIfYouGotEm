"""Fresh-process verification of installed ground, unchanged envelope and water bindings."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unreal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from package_runtime_bundle import sha
from bind_south_fork_discharge_bed_runtime import load,entries,package_file,LEVEL,MAP_PATH


def with_field_binding(saved, bound):
    """Verify a subsequent water-only save without changing the geometry receipt."""
    if (bound.get('mode') != 'set' or bound.get('level') != LEVEL or
            bound.get('before') != saved['after'] or
            bound.get('coordinate_maps_changed') is not False or
            bound.get('run_manager_changed') is not False):
        raise ValueError('Field update must follow the verified installation without coordinate changes')
    name = bound['config_package']
    if (name not in saved['changed_packages'] or
            saved['changed_packages'][name]['after'] != bound['config_package_sha256_before']):
        raise ValueError('Field update does not follow the installed config package')
    before, after = bound['before'], bound['after']
    if (set(after) != set(before) or
            any(after[key] != before[key] for key in ('hydraulic_coordinate_map', 'route_coordinate_map')) or
            after['initial_fields_manifest'].rsplit('/', 2)[-2] != before['initial_fields_manifest'].rsplit('/', 2)[-2]):
        raise ValueError('Field update must retain coordinate maps and initial window')
    changed = {key: dict(value) for key, value in saved['changed_packages'].items()}
    changed[name]['after'] = bound['config_package_sha256_after']
    return dict(saved, after=dict(after), changed_packages=changed)


def main():
    installation=ROOT/os.environ['RAFTSIM_ENVELOPE_INSTALL_REPORT']
    output=(ROOT/os.environ['RAFTSIM_ENVELOPE_INVENTORY']).resolve()
    assert output.is_relative_to(ROOT/'tmp') and not output.exists()
    saved=json.loads(installation.read_text())
    assert saved['normal_map_saved'] and saved['other_scene_packages_unchanged']
    field_reports = field_binding_paths(os.environ)
    saved, field_proofs = with_field_binding_reports(saved, field_reports, sha(ROOT/MAP_PATH))
    for name,row in saved['changed_packages'].items():assert sha(ROOT/name)==row['after']
    descs,config,manager=load()
    assert entries(config,manager)==saved['after']
    all_descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    extra=[d for d in all_descs if str(d.name) in (saved['ground_actor'],saved['rock_actor'])]
    assert len(extra)==2
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in extra])
    actors={a.get_name():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    native=json.loads((ROOT/saved['native_report']).read_text())
    assert sha(ROOT/saved['native_report'])==saved['native_report_sha256']
    probes=json.loads((ROOT/native['probes']).read_text())
    assert sha(ROOT/native['probes'])==native['probes_sha256']
    proofs={}
    for name,asset,expected in (
        (saved['ground_actor'],saved['new_ground_asset'],probes['meshes']['ground_candidate']),
        (saved['rock_actor'],probes['meshes']['rock']['asset'],probes['meshes']['rock'])):
        actor=actors[name];mesh=actor.static_mesh_component.static_mesh
        assert mesh.get_path_name().split('.')[0]==asset
        pos=actor.get_actor_location();rot=actor.get_actor_rotation()
        assert max(abs(a-b) for a,b in zip([pos.x,pos.y,pos.z],probes['translation_cm']))<.001
        assert actor.get_actor_scale3d()==unreal.Vector(1,-1,1)
        assert max(abs(rot.pitch),abs(rot.yaw),abs(rot.roll))<1e-5
        assert 'RaftSimPhysicalGround' in map(str,actor.tags)
        assert str(actor.static_mesh_component.get_collision_profile_name())=='BlockAll'
        if name==saved['ground_actor']:
            assert actor.static_mesh_component.get_editor_property('disallow_nanite') is True
        proof=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
        assert proof['collision_source_sha256']==expected['native_sha256']
        assert proof['triangle_count']==mesh.get_num_triangles(0)==expected['triangle_count']
        proofs[name]=proof
    bindings={}
    for actor in (config,manager,actors[saved['ground_actor']],actors[saved['rock_actor']]):
        desc,=[d for d in all_descs if str(d.name)==actor.get_name()]
        bindings[actor.get_name()]=dict(actor_name=actor.get_name(),package=str(desc.actor_package),sha256=sha(ROOT/package_file(desc)))
    result=dict(schema='raftsim.saved_runtime_bindings.v1',level=LEVEL,map_sha256=sha(ROOT/MAP_PATH),
        bindings=bindings,entrypoints=entries(config,manager),saved_assets=False,
        native_geometry=proofs,installation_sha256=sha(installation),fresh_reload_verified=True)
    if field_proofs:
        # Keep original geometry installation evidence distinct from the later
        # water-only save; do not fabricate a second geometry installation.
        config_desc, = [d for d in all_descs if str(d.name) == config.get_name()]
        assert package_file(config_desc) == field_proofs[-1]['config_package']
        result['field_binding_sha256'] = field_proofs[-1]['sha256']
        result['field_binding_chain'] = field_proofs
    with output.open('x') as f:json.dump(result,f,indent=2)


def field_binding_paths(environment):
    """Legacy single receipt or an explicit ordered JSON list; never guess history."""
    single = environment.get('RAFTSIM_ENVELOPE_FIELD_BIND_REPORT')
    chain = environment.get('RAFTSIM_ENVELOPE_FIELD_BIND_REPORTS')
    if single and chain:
        raise ValueError('Specify either a single field receipt or its ordered chain')
    names = json.loads(chain) if chain else ([single] if single else [])
    if not isinstance(names, list) or (chain and not names):
        raise ValueError('Field binding chain must be a nonempty JSON list')
    paths = []
    for name in names:
        if not isinstance(name, str) or not name:
            raise ValueError('Field receipt paths must be nonempty strings')
        path = (ROOT/name).resolve()
        if not path.is_relative_to((ROOT/'tmp').resolve()) or path in paths:
            raise ValueError('Field receipts must be distinct files inside tmp')
        paths.append(path)
    return paths


def with_field_binding_reports(saved, paths, map_sha256):
    """Replay every verified save from original geometry to current water state."""
    proofs = []
    for path in paths:
        # Hash the very bytes being interpreted, not a second read that could
        # identify different contents if a receipt changes during inventory.
        data = path.read_bytes()
        bound = json.loads(data)
        if bound['map_sha256'] != map_sha256:
            raise ValueError('Field receipt map identity changed')
        if proofs and bound['config_package'] != proofs[0]['config_package']:
            raise ValueError('Field history changes the target config package')
        saved = with_field_binding(saved, bound)
        proofs.append(dict(path=path.relative_to(ROOT).as_posix(),
                           sha256=hashlib.sha256(data).hexdigest(),
                           config_package=bound['config_package']))
    return saved, proofs


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
