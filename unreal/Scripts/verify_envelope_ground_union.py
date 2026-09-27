"""Transient candidate ground with installed envelope; never save map or assets."""
import json
import math
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from package_runtime_bundle import sha
LEVEL='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def package_file(name):
    assert name.startswith('/Game/') and '..' not in name.split('/')
    return ROOT/'unreal/Content'/(name[6:]+'.uasset')


def main():
    source=(ROOT/os.environ['RAFTSIM_ENVELOPE_UNION_PROBES']).resolve()
    output=(ROOT/os.environ['RAFTSIM_ENVELOPE_UNION_REPORT']).resolve()
    assert source.is_relative_to(ROOT/'tmp') and output.is_relative_to(ROOT/'tmp') and not output.exists()
    probes=json.loads(source.read_text())
    assert probes['schema']=='raftsim.envelope_union_native_probes.v1'
    protected={source:sha(source)}
    for name,digest in probes['dependencies'].items():
        path=(ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and sha(path)==digest
        protected[path]=digest
    meshes={};native={}
    for role,row in probes['meshes'].items():
        path=package_file(row['asset']);assert sha(path)==row['package_sha256']
        protected[path]=sha(path)
        mesh=unreal.load_asset(row['asset']);assert mesh
        proof=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
        assert proof['collision_source_sha256']==row['native_sha256']
        assert proof['triangle_count']==mesh.get_num_triangles(0)==row['triangle_count']
        assert proof['flip_normals'] and proof['collision_trace_flag']==3
        meshes[role]=mesh;native[role]=proof
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0]==LEVEL
    map_path=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected[map_path]=sha(map_path)
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    for d in descs:
        path=package_file(str(d.actor_package));protected[path]=sha(path)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs if d.native_class.get_name()=='StaticMeshActor'])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    grounds=[a for a in actors if 'RaftSimPhysicalGround' in map(str,a.tags)]
    ground,=[a for a in grounds if a.get_name()==probes['ground_actor']]
    rock,=[a for a in grounds if a.get_name()==probes['rock_actor']]
    for actor,role in ((ground,'ground_before'),(rock,'rock')):
        assert isinstance(actor,unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh==meshes[role]
        pos=actor.get_actor_location();rot=actor.get_actor_rotation()
        assert max(abs(a-b) for a,b in zip([pos.x,pos.y,pos.z],probes['translation_cm']))<.001
        assert actor.get_actor_scale3d()==unreal.Vector(1,-1,1)
        assert max(abs(rot.pitch),abs(rot.yaw),abs(rot.roll))<1e-5
        assert str(actor.static_mesh_component.get_collision_profile_name())=='BlockAll'
    # Include other physical scene geometry as possible occluders.
    ignored=[a for a in actors if a not in grounds]
    component=ground.static_mesh_component
    prior_nanite=component.get_editor_property('disallow_nanite')
    failures=[];groups={}
    try:
        assert component.set_static_mesh(meshes['ground_candidate'])
        component.set_editor_property('disallow_nanite',True)
        for index,row in enumerate(probes['rows']):
            p=unreal.Vector(*row['world_position_cm'])
            n=unreal.Vector(*row.get('outward_normal',[0,0,1]))
            distance=row.get('ray_half_length_cm',1000.)
            for trace_complex in (False,True):
                hit=unreal.SystemLibrary.line_trace_single(world,p+n*distance,p-n*distance,
                    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,trace_complex,ignored,unreal.DrawDebugTrace.NONE,False)
                v=hit.to_tuple() if hit else None
                group=groups.setdefault(row['kind']+('/complex' if trace_complex else '/simple'),
                    dict(count=0,maximum_error_cm=0.))
                group['count']+=1
                if not v or not v[0]:
                    failures.append(dict(index=index,trace_complex=trace_complex,reason='no_hit'))
                    continue
                q=v[5];error=math.sqrt((q.x-p.x)**2+(q.y-p.y)**2+(q.z-p.z)**2)
                owner=next((a for a in v if isinstance(a,unreal.Actor)),None)
                group['maximum_error_cm']=max(group['maximum_error_cm'],error)
                expected=rock if row['expected_rock'] else ground
                if error>.1 or owner!=expected:
                    failures.append(dict(index=index,trace_complex=trace_complex,error_cm=error,
                        reason='position_or_owner',expected_actor=expected.get_name(),
                        actual_actor=owner.get_name() if owner else None,probe=row))
    finally:
        assert component.set_static_mesh(meshes['ground_before'])
        component.set_editor_property('disallow_nanite',prior_nanite)
    for path,digest in protected.items():assert sha(path)==digest,('Saved file changed',str(path))
    assert sum(g['count'] for g in groups.values())==2*len(probes['rows'])
    report=dict(schema='raftsim.envelope_ground_union_native.v1',passed=not failures,
        probes=source.relative_to(ROOT).as_posix(),probes_sha256=sha(source),groups=groups,
        failures=failures,native_meshes=native,position_tolerance_cm=.1,
        protected_file_count=len(protected),
        protected_files={p.relative_to(ROOT).as_posix():digest for p,digest in protected.items()},
        normal_scene_restored=True,saved_assets=False,
        playable_integrated=False,motion_verified=False,performance_accepted=False,
        scope=probes['limitation'])
    with output.open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
    assert not failures,'Combined ground/envelope traces failed; inspect preserved report'
    unreal.log('Combined ground/envelope native probes passed; normal scene unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
