"""Transient candidate against actual saved South Fork physical-ground actors.

No PIE, water-state changes, saved asset, saved level or playable promotion.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid,candidate_configuration

LEVEL='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
PROBES=ROOT/'tmp/south-fork-rock-union-full-map-probes-v1-20260915.json'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/south-fork-rock-union-full-map-v1-20260915.json'
GROUND='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def main(runtime_expectations=None,output=REPORT,probe_path=PROBES,export_directory=None,asset_path=None):
    assert not output.exists()
    probes=json.loads(probe_path.read_text())
    assert sha(ROOT/probes['geometry_manifest'])==probes['geometry_manifest_sha256']
    before={str(ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'):
        sha(ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap')}
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level(LEVEL)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0]==LEVEL
    descriptors=unreal.WorldPartitionBlueprintLibrary.get_actor_descs();assert descriptors
    packages={str(d.actor_package):sha(package_file(str(d.actor_package))) for d in descriptors}
    points=[p['world_position_cm'] for p in probes['baseline']+probes['combined']]
    low=[min(p[i] for p in points)-100 for i in range(2)]
    high=[max(p[i] for p in points)+100 for i in range(2)]
    relevant=[d for d in descriptors if d.native_class.get_name()=='StaticMeshActor'
        and d.bounds.min.x<=high[0] and d.bounds.max.x>=low[0]
        and d.bounds.min.y<=high[1] and d.bounds.max.y>=low[1]]
    assert relevant
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in relevant])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors=list(subsystem.get_all_level_actors())
    grounds=[a for a in actors if 'RaftSimPhysicalGround' in map(str,a.tags)]
    assert grounds
    rapid=[a for a in grounds if isinstance(a,unreal.StaticMeshActor) and
        a.static_mesh_component.static_mesh.get_path_name().split('.')[0]==GROUND]
    assert len(rapid)==1
    pos=rapid[0].get_actor_location();scale=rapid[0].get_actor_scale3d()
    assert scale==unreal.Vector(1,-1,1)
    assert max(abs(a-b) for a,b in zip([pos.x,pos.y,pos.z],probes['translation_cm']))<.001
    ground_rows=[]
    for actor in grounds:
        mesh=actor.static_mesh_component.static_mesh
        path=package_file(mesh.get_path_name().split('.')[0]);before[str(path)]=sha(path)
        ground_rows.append(dict(actor=actor.get_name(),mesh=mesh.get_path_name()))
    ignored=[a for a in actors if a not in grounds]
    groups={};failures=[]

    def check(rows,stage,candidate=None):
        for index,probe in enumerate(rows):
            p=unreal.Vector(*probe['world_position_cm']);n=unreal.Vector(*probe.get('outward_normal',[0,0,1]))
            distance=probe.get('ray_half_length_cm',1000.)
            hit=unreal.SystemLibrary.line_trace_single(world,p+n*distance,p-n*distance,
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,False)
            values=hit.to_tuple() if hit else None
            group=groups.setdefault(stage+'/'+probe['kind'],dict(queries=0,hits=0,maximum_error_cm=0.,candidate_hits=0))
            group['queries']+=1
            if not values or not values[0]:
                failures.append(dict(stage=stage,index=index,probe=probe,reason='no_blocking_hit'));continue
            point=values[5];error=math.sqrt((point.x-p.x)**2+(point.y-p.y)**2+(point.z-p.z)**2)
            owner=next((v for v in values if isinstance(v,unreal.Actor)),None)
            group['hits']+=1;group['maximum_error_cm']=max(group['maximum_error_cm'],error)
            group['candidate_hits']+=int(owner==candidate and candidate is not None)
            if error>.1 or (candidate is not None and probe.get('expected_candidate')!=(owner==candidate)):
                failures.append(dict(stage=stage,index=index,probe=probe,reason='position_or_owner_mismatch',
                    error_cm=error,actor=owner.get_name() if owner else None))

    check(probes['baseline'],'retained')
    mesh,export=import_candidate_solid(export_directory,asset_path);assert export['source_cap_sha256']==probes['source_cap_sha256']
    candidate=subsystem.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*probes['translation_cm']))
    candidate.set_actor_location(unreal.Vector(*probes['translation_cm']),False,True)
    candidate.set_actor_rotation(unreal.Rotator(0,0,0),True);candidate.set_actor_scale3d(unreal.Vector(1,-1,1))
    candidate.static_mesh_component.set_static_mesh(mesh)
    candidate.static_mesh_component.set_collision_profile_name('BlockAll')
    check(probes['combined'],'union',candidate)
    runtime_result=None
    if runtime_expectations is not None:
        expected=json.loads(runtime_expectations.read_text())
        assert expected['source_probe_sha256']==sha(probe_path)
        assert expected['solver_dry_threshold_m']==1.e-6 and expected['native_sample_wet_threshold_m']==1.e-4
        for key,digest in [('atlas_manifest','atlas_sha256'),('fields_manifest','fields_manifest_sha256'),
                           ('coordinate_map','coordinate_map_sha256')]:
            assert sha(ROOT/expected[key])==expected[digest]
        for path,digest in expected['array_dependencies'].items():assert sha(ROOT/path)==digest
        water=unreal.RaftSimWaterRuntimeAdapter();config=unreal.RaftSimWaterRuntimeConfig()
        config.require_accepted_report_manifest=False;config.enable_deterministic_capture=False
        water.configure(config);assert water.configure_river_coordinate_map(expected['coordinate_map'])
        assert water.configure_moving_river_window(expected['fields_manifest'].rsplit('/',1)[0],
            'median_runnable',unreal.Vector2D(*expected['window_center_m']),unreal.Vector2D(224,224),.035)
        errors=dict(bed_m=0.,depth_m=0.,surface_m=0.,u_mps=0.,world_v_mps=0.);wet_mismatches=0
        runtime_failures=[]
        for index,row in enumerate(expected['queries']):
            sample=water.sample_water_at_world_position(unreal.Vector(*row['world_position_cm']))
            if sample is None:runtime_failures.append(dict(index=index,reason='missing_native_sample'));continue
            values=dict(bed_m=sample.bed_height_meters,depth_m=sample.depth_meters,
                surface_m=sample.surface_height_meters,u_mps=sample.velocity_meters_per_second.x,
                world_v_mps=sample.velocity_meters_per_second.y)
            for key,value in values.items():
                error=abs(value-row['expected_runtime'][key]);errors[key]=max(errors[key],error)
                # 0.1 mm height and 1e-5 m/s velocity allowances cover native
                # float sample publication; collision still uses its 1 mm gate.
                tolerance=1.e-5 if key in ('u_mps','world_v_mps','depth_m') else 1.e-4
                if error>tolerance:runtime_failures.append(dict(index=index,field=key,error=error))
            wet_mismatches+=int(bool(sample.wet)!=row['expected_runtime']['native_sample_wet'])
        if wet_mismatches:runtime_failures.append(dict(reason='wet_mask_mismatch',count=wet_mismatches))
        failures.extend(dict(stage='native_runtime',**failure) for failure in runtime_failures)
        runtime_result=dict(query_count=len(expected['queries']),maximum_errors=errors,wet_mismatches=wet_mismatches,
            solver_wet_query_count=sum(r['expected_runtime']['solver_wet'] for r in expected['queries']),
            native_sample_wet_query_count=sum(r['expected_runtime']['native_sample_wet'] for r in expected['queries']),
            solver_dry_threshold_m=1.e-6,native_sample_wet_threshold_m=1.e-4,
            field_queries_verified=not runtime_failures,source_time_seconds=expected['source_time_seconds'],
            fields_manifest=expected['fields_manifest'],window_center_m=expected['window_center_m'],
            expectation_sha256=sha(runtime_expectations),solver_steps_run=0)
    for path,digest in before.items():assert sha(Path(path))==digest,('Protected file changed',path)
    for package,digest in packages.items():assert sha(package_file(package))==digest,('Saved actor changed',package)
    result=dict(level=LEVEL,source_probe_sha256=sha(probe_path),source_cap_sha256=export['source_cap_sha256'],
        fbx_sha256=export['fbx_sha256'],geometry_manifest_sha256=probes['geometry_manifest_sha256'],
        original_rapid_actor=rapid[0].get_name(),candidate_translation_cm=probes['translation_cm'],
        ground_actors=ground_rows,groups=groups,failures=failures,
        sampled_full_map_union_verified=not failures,position_tolerance_cm=.1,
        prior_vertical_tangent_gate_closed=False,actual_raft_contact_traversal_verified=False,
        saved_assets=False,saved_levels=False,water_state_modified=False,
        hydraulic_settling_accepted=False,playable_integrated=False,visual_acceptance=False,
        native_runtime=runtime_result,
        protected_file_count=len(before),protected_actor_package_count=len(packages))
    output.write_text(json.dumps(result,indent=2)+'\n')
    assert not failures,str(len(failures))+' union probes failed; '+str(output)
    unreal.log('Actual full-map sampled terrain/rock union verified: '+str(output))


if __name__=='__main__':
    try:
        config_path=os.environ.get('RAFTSIM_ROCK_COLLISION_CONFIG')
        if config_path:
            config=candidate_configuration(config_path)
            main(output=config['report'],probe_path=config['probes'],export_directory=config['export_directory'],asset_path=config['asset'])
        else:main()
    finally:unreal.SystemLibrary.quit_editor()
