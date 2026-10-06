"""Trace every source face from outside in the physical reflected actor frame."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid


def main():
    path=(ROOT/os.environ['RAFTSIM_MIXED_CAP_ORIENTATION']).resolve()
    config=json.loads(path.read_text());out=(ROOT/config['report']).resolve()
    assert path.is_relative_to(ROOT/'tmp') and out.is_relative_to(ROOT/'tmp') and not out.exists()
    mesh,export=import_candidate_solid(ROOT/config['export_directory'],
        '/Game/RaftSim/Environment/GeneratedLocalReview/MixedCapOrientation20260925/SM_OriginalReturnRockSolid')
    assert export['source_cap_sha256']==config['source_cap_sha256']
    native=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
    assert native['collision_source_sha256']==config['reversed_provider_sha256'] and native['flip_normals'] is True
    assert native['triangle_count']==len(config['probes'])==export['triangle_count']
    assert sorted(row['face'] for row in config['probes'])==list(range(export['triangle_count']))
    api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);ignored=api.get_all_level_actors()
    actor=api.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
    actor.set_actor_location(unreal.Vector(0,0,0),False,True)
    actor.set_actor_rotation(unreal.Rotator(0,0,0),True)
    actor.set_actor_scale3d(unreal.Vector(1,-1,1))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    failures=[];groups={}
    for row in config['probes']:
        p=unreal.Vector(*row['position_cm']);n=unreal.Vector(*row['outward_normal'])
        hit=unreal.SystemLibrary.line_trace_single(world,p+n*.1,p-n*.1,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,unreal.DrawDebugTrace.NONE,False)
        v=hit.to_tuple() if hit else None
        g=groups.setdefault(str(row['kind']),dict(count=0,maximum_error_cm=0.,minimum_normal_dot=1.))
        g['count']+=1
        if not v or not v[0]:failures.append(dict(face=row['face'],reason='no_hit'));continue
        q=v[5];normal=v[7]
        error=math.sqrt((q.x-p.x)**2+(q.y-p.y)**2+(q.z-p.z)**2)
        dot=normal.x*n.x+normal.y*n.y+normal.z*n.z
        g['maximum_error_cm']=max(g['maximum_error_cm'],error);g['minimum_normal_dot']=min(g['minimum_normal_dot'],dot)
        if error>.1 or dot<.999 or actor not in v:
            failures.append(dict(face=row['face'],reason='position_normal_or_owner',error_cm=error,normal_dot=dot))
    api.destroy_actor(actor)
    out.write_text(json.dumps(dict(passed=not failures,native=native,groups=groups,failures=failures,
        source_cap_sha256=config['source_cap_sha256'],probe_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        saved_assets=False,saved_levels=False,full_map_collision_verified=False,playable_integrated=False),indent=2)+'\n')
    assert not failures,str(len(failures))+' source-face orientation failures: '+str(out)


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
