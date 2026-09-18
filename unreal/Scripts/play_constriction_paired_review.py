"""Unsaved real PIE motion with verified source-extension terrain and water.

Launch via -ExecCmds="py SCRIPT", not synchronous ExecutePythonScript. No saved
map/profile change, artificial steering, shipping promotion or FPS acceptance.
"""
import json
import os
from pathlib import Path
import struct
import sys
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'unreal/Scripts'),str(ROOT/'physics/scripts')]
from prepare_constriction_paired_review import validate,LEVEL
from south_fork_terrain_replacement import native_source,sha
from verify_south_fork_rock_union_collision import package_file
from verify_constriction_union_collision import verify_runtime

state={};protected={};report=None;started=time.perf_counter()


def finish(error=None):
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    for path,digest in protected.items():
        if not Path(path).is_file() or sha(Path(path))!=digest:error=(error or '')+'\nSaved file changed: '+path
    state.update(complete=error is None,error=error,wall_seconds=time.perf_counter()-started,
        saved_map_or_assets=False,normal_play_promoted=False,linked_cpp_preview_loader_exercised=False,
        visual_accepted=False,performance_accepted=False,semantic_classification_accepted=False)
    if report:
        with report.open('x') as stream:stream.write(json.dumps(state,indent=2)+'\n')
    if error:unreal.log_error(error)
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.perf_counter()-started>480:raise RuntimeError('Paired PIE review exceeded eight-minute bound')
        worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
        if state.get('end_play_requested'):
            if worlds:return
            state['play_session_ended']=True;finish();return
        if not worlds:return
        assert len(worlds)==1;world=worlds[0]
        if not state.get('verified_play_world'):
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.StaticMeshActor)
            counts={role:sum(bool(a.static_mesh_component.static_mesh) and
                a.static_mesh_component.static_mesh.get_path_name().split('.')[0]==entry['asset'] for a in actors)
                for role,entry in probes['assets'].items()}
            state['observed_mesh_counts']=counts
            if counts['candidate']==counts['installed']==0:
                first=state.setdefault('ground_wait_started',time.perf_counter())
                if time.perf_counter()-first<20:return
            assert counts==dict(installed=0,candidate=1,cap=1),'PIE source geometry differs: '+str(counts)
            configs=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RaftSimRiverWaterConfig)
            assert len(configs)==1
            for key,value in config_values.items():assert configs[0].get_editor_property(key)==value,key
            revised=[a for a in actors if a.static_mesh_component.static_mesh==meshes['candidate']]
            assert len(revised)==1 and revised[0].static_mesh_component.get_editor_property('disallow_nanite')
            state.update(verified_play_world=world.get_path_name(),source_time_seconds=descriptor['source_time_seconds'],
                review_start_station_m=descriptor['review_start_station_m'],terrain_actor=revised[0].get_name())
            unreal.log('Source-supported actual PIE geometry and water verified: '+str(counts))
            unreal.SystemLibrary.execute_console_command(world,'RaftSim.CaptureSeries 0.1 24 0.5 '+label+' record')
        now=unreal.GameplayStatics.get_time_seconds(world)
        if now>=state.get('next_motion_sample',0.):
            rafts=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RaftSimRaftActor)
            rows=[]
            for raft in rafts:
                p=raft.get_actor_location();r=raft.get_actor_rotation()
                rows.append(dict(actor=raft.get_name(),location_cm=[p.x,p.y,p.z],rotation_deg=[r.pitch,r.yaw,r.roll]))
            state.setdefault('raft_motion',[]).append(dict(time_seconds=now,rafts=rows));state['next_motion_sample']=now+.25
        final=ROOT/'unreal/Saved/Screenshots'/(label+'_023.png')
        if final.exists():
            paths=[ROOT/'unreal/Saved/Screenshots'/(label+f'_{i:03d}.png') for i in range(24)]
            sizes=[]
            for path in paths:
                with path.open('rb') as stream:header=stream.read(24)
                assert header[:8]==b'\x89PNG\r\n\x1a\n' and header[12:16]==b'IHDR'
                sizes.append(struct.unpack('>II',header[16:24]))
            state.update(screenshots=[str(p) for p in paths],actual_capture_sizes=[list(s) for s in sizes],
                capture_resolution_matched=all(s==(1280,720) for s in sizes),end_play_requested=True)
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:finish(traceback.format_exc())


try:
    config_path=(ROOT/os.environ['RAFTSIM_CONSTRICTION_PLAY_CONFIG']).resolve()
    raw=json.loads(config_path.read_text());label=raw['label']
    destination=(ROOT/raw['report']).resolve()
    assert config_path.is_relative_to(ROOT/'tmp') and destination.is_relative_to(ROOT/'tmp') and not destination.exists()
    assert label.replace('-','').replace('_','').isalnum();report=destination
    assert not list((ROOT/'unreal/Saved/Screenshots').glob(label+'_*.png'))
    descriptor_path=(ROOT/raw['descriptor']).resolve();descriptor,collision,probes=validate(descriptor_path)
    state['descriptor_sha256']=sha(descriptor_path)
    for name,digest in descriptor['dependencies'].items():
        if Path(name).suffix in ('.umap','.uasset'):protected[str(ROOT/name)]=digest
    profile=ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    if profile.exists():protected[str(profile)]=sha(profile)
    meshes={}
    for role,row in probes['assets'].items():
        mesh=unreal.load_asset(row['asset']);actual=native_source(mesh,row['triangle_count'])
        assert actual['collision_source_sha256']==row['native_source_sha256'];meshes[role]=mesh
    assert meshes['candidate'].get_num_triangles(0)==probes['assets']['candidate']['triangle_count']
    material=meshes['candidate'].get_material(0);assert material==meshes['installed'].get_material(0)
    parent=material.get_editor_property('parent')
    assert unreal.MaterialEditingLibrary.get_material_property_input_node(parent,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None
    protected[str(package_file(parent.get_path_name().split('.')[0]))]=sha(package_file(parent.get_path_name().split('.')[0]))
    state['fresh_preplay_water']=verify_runtime(ROOT/descriptor['runtime_expectations'],ROOT/descriptor['union_probes'],probes)
    assert state['fresh_preplay_water']['field_queries_verified']
    route=unreal.RaftSimWaterRuntimeAdapter();assert route.configure_river_coordinate_map(descriptor['route_coordinate_map'])
    point=route.river_to_world_position(unreal.Vector2D(descriptor['review_start_station_m'],0),220.)
    water=unreal.RaftSimWaterRuntimeAdapter();wc=unreal.RaftSimWaterRuntimeConfig()
    wc.require_accepted_report_manifest=False;wc.enable_deterministic_capture=False;water.configure(wc)
    assert water.configure_river_coordinate_map(descriptor['coordinate_map'])
    assert water.configure_moving_river_window(descriptor['initial_fields_manifest'].rsplit('/',1)[0],
        'median_runnable',unreal.Vector2D(*descriptor['window_center_m']),unreal.Vector2D(224,224),.035)
    sample=water.sample_water_at_world_position(point);assert sample and sample.wet,'Review start is dry'
    state['start_center_preflight']=dict(point_cm=[point.x,point.y,point.z],depth_m=sample.depth_meters,
        surface_m=sample.surface_height_meters,bed_m=sample.bed_height_meters,full_hull_clearance_accepted=False)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level(LEVEL)
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs();assert descs
    for d in descs:
        path=package_file(str(d.actor_package));protected[str(path)]=sha(path)
    p=probes['translation_cm'];radius=25000
    selected=[d for d in descs if d.native_class.get_name()=='StaticMeshActor' and
        d.bounds.min.x<=p[0]+radius and d.bounds.max.x>=p[0]-radius and
        d.bounds.min.y<=p[1]+radius and d.bounds.max.y>=p[1]-radius]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selected])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    grounds=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh==meshes['installed']]
    caps=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh==meshes['cap']]
    configs=[a for a in actors if isinstance(a,unreal.RaftSimRiverWaterConfig)]
    assert len(grounds)==len(caps)==len(configs)==1
    assert grounds[0].get_name()==collision['original_actor'] and caps[0].get_name()==collision['retained_cap_actor']
    for actor in (grounds[0],caps[0]):
        assert 'RaftSimPhysicalGround' in map(str,actor.tags) and actor.get_actor_scale3d()==unreal.Vector(1,-1,1)
        p=actor.get_actor_location();assert max(abs(a-b) for a,b in zip([p.x,p.y,p.z],probes['translation_cm']))<.001
    # Dirty only the unsaved actor instance so PIE duplicates the replacement,
    # instead of silently reloading the old external-actor mesh from disk.
    ground=grounds[0];ground.modify();ground.static_mesh_component.modify();configs[0].modify()
    assert ground.static_mesh_component.set_static_mesh(meshes['candidate'])
    ground.static_mesh_component.set_editor_property('disallow_nanite',True)
    config_values=dict(cooked_fields_dir=descriptor['initial_fields_manifest'].rsplit('/',1)[0],
        streaming_manifest_path=descriptor['streaming_manifest'],coordinate_map_path=descriptor['coordinate_map'],
        window_center_m=unreal.Vector2D(*descriptor['window_center_m']),window_extent_m=224.,
        moving_window_station_extent_m=224.,moving_window_lateral_extent_m=224.,flow_band=unreal.Name('median_runnable'),
        recenter_hydraulic_crux=False,enable_moving_window_streaming=True,map_provides_terrain=True)
    for key,value in config_values.items():configs[0].set_editor_property(key,value)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    levels.editor_request_begin_play()
except Exception:finish(traceback.format_exc())
