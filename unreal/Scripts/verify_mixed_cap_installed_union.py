"""No-save replacement of the installed cap, with retained normal-scene ground."""
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
from verify_south_fork_rock_union_collision import package_file


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    config=json.loads((ROOT/os.environ['RAFTSIM_MIXED_UNION_CONFIG']).read_text())
    output=(ROOT/config['report']).resolve();probe_path=ROOT/config['probes']
    assert output.is_relative_to(ROOT/'tmp') and not output.exists()
    assert sha(probe_path)==config['probes_sha256']
    probes=json.loads(probe_path.read_text())
    assert sha(ROOT/probes['geometry_manifest'])==probes['geometry_manifest_sha256']
    meshes={};native={};protected={}
    for role,row in config['installed'].items():
        path=package_file(row['asset']);assert sha(path)==row['package_sha256'];protected[str(path)]=sha(path)
        meshes[role]=unreal.load_asset(row['asset']);assert meshes[role]
        native[role]=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(meshes[role]))
        assert native[role]['collision_source_sha256']==row['native_sha256']
        assert native[role]['flip_normals'] is True
    level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    map_path=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected[str(map_path)]=sha(map_path)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    for d in descs:protected[str(package_file(str(d.actor_package)))]=sha(package_file(str(d.actor_package)))
    points=[p['world_position_cm'] for p in probes['combined']]
    low=[min(p[i] for p in points)-100 for i in range(2)];high=[max(p[i] for p in points)+100 for i in range(2)]
    selected=[d for d in descs if d.native_class.get_name()=='StaticMeshActor'
        and d.bounds.min.x<=high[0] and d.bounds.max.x>=low[0] and d.bounds.min.y<=high[1] and d.bounds.max.y>=low[1]]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selected])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    grounds=[a for a in actors if 'RaftSimPhysicalGround' in map(str,a.tags)]
    owners={}
    for role,mesh in meshes.items():
        found=[a for a in grounds if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh==mesh]
        assert len(found)==1,(role,len(found));owners[role]=found[0]
        p=found[0].get_actor_location()
        assert max(abs(a-b) for a,b in zip([p.x,p.y,p.z],probes['translation_cm']))<.001
        assert found[0].get_actor_scale3d()==unreal.Vector(1,-1,1)
    replacement,receipt=import_candidate_solid(ROOT/config['export_directory'],
        '/Game/RaftSim/Environment/GeneratedLocalReview/MixedUnion20260925/SM_OriginalReturnRockSolid')
    assert receipt['source_cap_sha256']==probes['source_cap_sha256']
    replacement_native=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(replacement))
    assert replacement_native['collision_source_sha256']==config['candidate_native_sha256'] and replacement_native['flip_normals'] is True
    cap=owners['cap'];ignored=[a for a in actors if a not in grounds]
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    groups={};failures=[]
    try:
        assert cap.static_mesh_component.set_static_mesh(replacement)
        for index,row in enumerate(probes['combined']):
            p=unreal.Vector(*row['world_position_cm']);n=unreal.Vector(*row.get('outward_normal',[0,0,1]))
            distance=row.get('ray_half_length_cm',1000.)
            hit=unreal.SystemLibrary.line_trace_single(world,p+n*distance,p-n*distance,
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,unreal.DrawDebugTrace.NONE,False)
            v=hit.to_tuple() if hit else None
            g=groups.setdefault(row['kind'],dict(count=0,maximum_error_cm=0.));g['count']+=1
            if not v or not v[0]:failures.append(dict(index=index,reason='no_hit',probe=row));continue
            q=v[5];error=math.sqrt((q.x-p.x)**2+(q.y-p.y)**2+(q.z-p.z)**2)
            owner=next((a for a in v if isinstance(a,unreal.Actor)),None)
            g['maximum_error_cm']=max(g['maximum_error_cm'],error)
            if error>.1 or (owner==cap)!=bool(row['expected_candidate']):
                failures.append(dict(index=index,error_cm=error,reason='position_or_owner',probe=row))
    finally:
        assert cap.static_mesh_component.set_static_mesh(meshes['cap'])
    for path,digest in protected.items():assert sha(path)==digest,('Saved file changed',path)
    output.write_text(json.dumps(dict(passed=not failures,groups=groups,failures=failures,
        installed_native=native,candidate_native=replacement_native,source_probe_sha256=sha(probe_path),
        protected_file_count=len(protected),saved_assets=False,saved_levels=False,
        ground_replaced=False,cap_actor=cap.get_name(),cap_restored=True,playable_integrated=False),indent=2)+'\n')
    assert not failures,str(len(failures))+' full-map union failures: '+str(output)


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
