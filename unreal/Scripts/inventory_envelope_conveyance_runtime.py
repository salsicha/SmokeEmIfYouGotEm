"""Fresh-process verification of installed ground, unchanged envelope and water bindings."""
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


def main():
    installation=ROOT/os.environ['RAFTSIM_ENVELOPE_INSTALL_REPORT']
    output=(ROOT/os.environ['RAFTSIM_ENVELOPE_INVENTORY']).resolve()
    assert output.is_relative_to(ROOT/'tmp') and not output.exists()
    saved=json.loads(installation.read_text())
    assert saved['normal_map_saved'] and saved['other_scene_packages_unchanged']
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
    with output.open('x') as f:json.dump(result,f,indent=2)


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
