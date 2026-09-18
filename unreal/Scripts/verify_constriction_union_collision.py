"""Fresh reload and transient full-map source-extension collision comparison.

Uses the actual installed ground actor and retained cap. Never saves an asset,
level, or actor; no duplicate ground or replacement cap is spawned.
"""
import json
import math
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from south_fork_terrain_replacement import native_source, sha
from verify_south_fork_rock_union_collision import package_file


def verify_runtime(expected_path,probe_path,probes):
    expected=json.loads(expected_path.read_text())
    assert expected['source_probe_sha256']==sha(probe_path)
    assert expected['solver_dry_threshold_m']==1.e-6 and expected['native_sample_wet_threshold_m']==1.e-4
    for key,digest in [('atlas_manifest','atlas_sha256'),('fields_manifest','fields_manifest_sha256'),
                       ('coordinate_map','coordinate_map_sha256')]:
        assert sha(ROOT/expected[key])==expected[digest]
    for path,digest in expected['array_dependencies'].items():assert sha(ROOT/path)==digest
    atlas=json.loads((ROOT/expected['atlas_manifest']).read_text())
    assert atlas['terrain_union']['terrain_revision']==probes['terrain_revision']
    assert atlas['terrain_union']['cap_sha256']==probes['source_cap_sha256']
    rows=[p for p in probes['combined'] if p['kind']=='union_hydraulic_cell']
    assert len(rows)==len(expected['queries']) and len(rows)>=12800 and len(rows)%6400==0
    assert all(a['world_position_cm']==b['world_position_cm'] for a,b in zip(rows,expected['queries']))
    water=unreal.RaftSimWaterRuntimeAdapter();config=unreal.RaftSimWaterRuntimeConfig()
    config.require_accepted_report_manifest=False;config.enable_deterministic_capture=False
    water.configure(config);assert water.configure_river_coordinate_map(expected['coordinate_map'])
    assert water.configure_moving_river_window(expected['fields_manifest'].rsplit('/',1)[0],
        'median_runnable',unreal.Vector2D(*expected['window_center_m']),unreal.Vector2D(224,224),.035)
    errors=dict(bed_m=0.,depth_m=0.,surface_m=0.,u_mps=0.,world_v_mps=0.)
    failures=[];wet_mismatches=0
    for index,row in enumerate(expected['queries']):
        sample=water.sample_water_at_world_position(unreal.Vector(*row['world_position_cm']))
        if sample is None:
            failures.append(dict(index=index,reason='missing_native_sample'));continue
        values=dict(bed_m=sample.bed_height_meters,depth_m=sample.depth_meters,
            surface_m=sample.surface_height_meters,u_mps=sample.velocity_meters_per_second.x,
            world_v_mps=sample.velocity_meters_per_second.y)
        for key,value in values.items():
            error=abs(value-row['expected_runtime'][key]);errors[key]=max(errors[key],error)
            tolerance=1.e-5 if key in ('u_mps','world_v_mps','depth_m') else 1.e-4
            if not math.isfinite(error) or error>tolerance:
                failures.append(dict(index=index,field=key,error=error))
        wet_mismatches+=int(bool(sample.wet)!=row['expected_runtime']['native_sample_wet'])
    return dict(query_count=len(rows),maximum_errors=errors,wet_mismatches=wet_mismatches,failures=failures,
        field_queries_verified=not failures and wet_mismatches==0,
        solver_dry_threshold_m=1.e-6,native_sample_wet_threshold_m=1.e-4,
        source_time_seconds=expected['source_time_seconds'],atlas_manifest=expected['atlas_manifest'],
        atlas_sha256=expected['atlas_sha256'],fields_manifest=expected['fields_manifest'],
        fields_manifest_sha256=expected['fields_manifest_sha256'],window_center_m=expected['window_center_m'],
        expectation_sha256=sha(expected_path),solver_steps_run=0)


def main():
    path=(ROOT/os.environ['RAFTSIM_CONSTRICTION_UNION_PROBES']).resolve()
    output=(ROOT/os.environ['RAFTSIM_CONSTRICTION_UNION_REPORT']).resolve()
    assert path.is_relative_to(ROOT/'tmp') and output.is_relative_to(ROOT/'unreal/Saved/RaftSimValidation') and not output.exists()
    probes=json.loads(path.read_text())
    assert probes['schema']=='raftsim.constriction_installed_union_probes.v1'
    assert probes['position_tolerance_cm']==.1
    assert sha(ROOT/probes['geometry_manifest'])==probes['geometry_manifest_sha256']
    assert sha(ROOT/probes['native_proof'])==probes['native_proof_sha256']
    assert sha(ROOT/probes['native_report'])==probes['native_report_sha256']
    revision=probes['terrain_revision']
    assert sha(ROOT/revision['manifest'])==revision['manifest_sha256']
    assert sha(ROOT/revision['mesh_path'])==revision['revised_geometry_sha256']
    map_path=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    assert sha(map_path)==probes['map_sha256']
    protected={str(map_path):sha(map_path)}
    meshes={};native={}
    for role,row in probes['assets'].items():
        file=package_file(row['asset']);assert sha(file)==row['package_sha256']
        protected[str(file)]=sha(file)
        meshes[role]=unreal.load_asset(row['asset']);assert meshes[role]
        native[role]=native_source(meshes[role],row['triangle_count'])
        assert native[role]['collision_source_sha256']==row['native_source_sha256']
    assert meshes['candidate'].get_material(0)==meshes['installed'].get_material(0)
    level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
    descriptors=unreal.WorldPartitionBlueprintLibrary.get_actor_descs();assert descriptors
    for d in descriptors:
        file=package_file(str(d.actor_package));protected[str(file)]=sha(file)
    points=[p['world_position_cm'] for p in probes['baseline']+probes['combined']]
    low=[min(p[i] for p in points)-100 for i in range(2)]
    high=[max(p[i] for p in points)+100 for i in range(2)]
    relevant=[d for d in descriptors if d.native_class.get_name()=='StaticMeshActor'
        and d.bounds.min.x<=high[0] and d.bounds.max.x>=low[0]
        and d.bounds.min.y<=high[1] and d.bounds.max.y>=low[1]]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in relevant])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    ground=[a for a in actors if 'RaftSimPhysicalGround' in map(str,a.tags)]
    def owner(role):
        found=[a for a in ground if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh==meshes[role]]
        assert len(found)==1,(role,len(found))
        actor=found[0];assert actor.get_actor_scale3d()==unreal.Vector(1,-1,1)
        p=actor.get_actor_location()
        assert max(abs(a-b) for a,b in zip([p.x,p.y,p.z],probes['translation_cm']))<.001
        return actor
    rapid,cap=owner('installed'),owner('cap')
    for a in ground:
        file=package_file(a.static_mesh_component.static_mesh.get_path_name().split('.')[0]);protected[str(file)]=sha(file)
    ignored=[a for a in actors if a not in ground]
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    groups={};failures=[]
    def check(rows,stage):
        for i,row in enumerate(rows):
            p=unreal.Vector(*row['world_position_cm']);n=unreal.Vector(*row.get('outward_normal',[0,0,1]))
            distance=row.get('ray_half_length_cm',1000.)
            hit=unreal.SystemLibrary.line_trace_single(world,p+n*distance,p-n*distance,
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,unreal.DrawDebugTrace.NONE,False)
            v=hit.to_tuple() if hit else None
            g=groups.setdefault(stage+'/'+row['kind'],dict(queries=0,maximum_error_cm=0.,cap_hits=0))
            g['queries']+=1
            if not v or not v[0]:
                failures.append(dict(stage=stage,index=i,reason='no_blocking_hit',probe=row));continue
            q=v[5];error=math.sqrt((p.x-q.x)**2+(p.y-q.y)**2+(p.z-q.z)**2)
            actor=next((x for x in v if isinstance(x,unreal.Actor)),None)
            g['maximum_error_cm']=max(error,g['maximum_error_cm']);g['cap_hits']+=int(actor==cap)
            if error>.1 or bool(row['expected_candidate'])!=(actor==cap):
                failures.append(dict(stage=stage,index=i,reason='position_or_owner_mismatch',error_cm=error,
                    actor=actor.get_name() if actor else None,probe=row))
    check(probes['baseline'],'installed')
    assert rapid.static_mesh_component.set_static_mesh(meshes['candidate'])
    check(probes['combined'],'candidate')
    runtime_path=os.environ.get('RAFTSIM_CONSTRICTION_RUNTIME_EXPECTATIONS')
    runtime=verify_runtime((ROOT/runtime_path).resolve(),path,probes) if runtime_path else None
    assert rapid.static_mesh_component.set_static_mesh(meshes['installed'])
    for file,digest in protected.items():assert sha(Path(file))==digest,('Saved file changed',file)
    result=dict(schema='raftsim.constriction_installed_union_audit.v1',source_probe_sha256=sha(path),
        geometry_manifest_sha256=probes['geometry_manifest_sha256'],native_sources=native,
        original_actor=rapid.get_name(),retained_cap_actor=cap.get_name(),groups=groups,failures=failures,
        sampled_full_map_union_verified=not failures,position_tolerance_cm=.1,
        protected_file_count=len(protected),saved_assets=False,saved_levels=False,duplicate_ground_added=False,
        fresh_saved_candidate_reload_verified=True,actual_raft_traversal_verified=False,
        hydraulic_state_verified=bool(runtime and runtime['field_queries_verified']),native_runtime=runtime,
        semantic_classification_accepted=False,normal_game_integrated=False,
        source_cap_sha256=probes['source_cap_sha256'],terrain_revision=revision,
        assets=probes['assets'],candidate_translation_cm=probes['translation_cm'],
        material_asset=meshes['candidate'].get_material(0).get_path_name())
    output.write_text(json.dumps(result,indent=2)+'\n')
    assert not failures,str(len(failures))+' full-map union probes failed: '+str(output)
    assert runtime is None or runtime['field_queries_verified'],'Native water does not match the audited atlas: '+str(output)
    unreal.log('Source-supported full-map collision union verified: '+str(output))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
