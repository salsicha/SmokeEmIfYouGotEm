"""Unsaved actual PIE comparison while a separate cook retains its loaded DLLs.

This exercises the real game and renderer, not the new C++ descriptor loader.
The linked-loader, normal-play and uncontended performance gates remain separate.
Launch with -ExecCmds="py ABSOLUTE_SCRIPT_PATH", not -ExecutePythonScript:
the latter closes the editor when this asynchronous setup function returns.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import struct
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_south_fork_rock_union_runtime import runtime_configuration
from verify_south_fork_rock_union_collision import main as verify_native,package_file,LEVEL


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def report_destination(root,value):
    destination=(root/value).resolve()
    if not destination.is_relative_to(root/'tmp') or destination.exists():
        raise ValueError('Evidence report must be a fresh path inside project tmp')
    return destination


state={};started=time.perf_counter()


def finish(error=None):
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    for path,digest in protected.items():
        try:unchanged=sha(Path(path))==digest
        except OSError:unchanged=False
        if not unchanged:error=(error or '')+'\nProtected package changed or missing: '+path
    state.update(complete=error is None,error=error,wall_seconds=time.perf_counter()-started,
        linked_v2_loader_exercised=False,performance_accepted=False,visual_accepted=False,
        normal_scenario_promoted=False,saved_map_or_actor_packages=False)
    try:
        with report.open('x') as stream:stream.write(json.dumps(state,indent=2)+'\n')
    except Exception:
        unreal.log_error('Could not create fresh evidence report: '+traceback.format_exc())
        unreal.SystemLibrary.quit_editor()
        return
    if error:unreal.log_error(error);unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.perf_counter()-started>480:raise RuntimeError('PIE comparison exceeded eight-minute wall bound')
        worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
        if state.get('end_play_requested'):
            if worlds:return
            state['play_session_ended']=True
            finish()
            unreal.SystemLibrary.quit_editor()
            return
        if not worlds:return
        if len(worlds)!=1:raise RuntimeError('Exactly one local PIE world required')
        world=worlds[0]
        if not state.get('verified_play_world'):
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.StaticMeshActor)
            revised=[a for a in actors if a.static_mesh_component.static_mesh and
                a.static_mesh_component.static_mesh.get_path_name().split('.')[0]==terrain['mesh_asset']]
            old=[a for a in actors if a.static_mesh_component.static_mesh and
                a.static_mesh_component.static_mesh.get_path_name().split('.')[0]==terrain['original_mesh_asset']]
            rocks=[a for a in actors if a.static_mesh_component.static_mesh and
                a.static_mesh_component.static_mesh.get_path_name()==descriptor['mesh_asset']]
            state['observed_play_ground']=dict(revised_count=len(revised),original_count=len(old),rock_count=len(rocks),
                actors=[dict(actor=a.get_name(),mesh=a.static_mesh_component.static_mesh.get_path_name()) for a in actors
                    if a.static_mesh_component.static_mesh and ('RaftSimPhysicalGround' in map(str,a.tags) or
                        'Troublemaker' in a.static_mesh_component.static_mesh.get_path_name())])
            if (not revised and not old) or not rocks:
                # World-partition cells may still be arriving after the first
                # PIE tick. Never capture absent ground or substitute a proxy.
                first=state.setdefault('ground_wait_started',time.perf_counter())
                if time.perf_counter()-first<20:return
            if len(revised)!=1 or old or len(rocks)!=1:
                raise RuntimeError('PIE did not retain verified ground: '+json.dumps(state['observed_play_ground']))
            if 'RaftSimPhysicalGround' not in map(str,rocks[0].tags):raise RuntimeError('Rock not registered as physical ground')
            configs=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RaftSimRiverWaterConfig)
            if len(configs)!=1:raise RuntimeError('Unique actual-play water config required')
            for key,value in config_values.items():
                if configs[0].get_editor_property(key)!=value:raise RuntimeError('PIE water config mismatch: '+key)
            state.update(verified_play_world=world.get_path_name(),terrain_actor=revised[0].get_name(),
                rock_actor=rocks[0].get_name(),source_time_seconds=descriptor['source_time_seconds'],
                atlas_manifest=descriptor['atlas_manifest'],terrain_mesh=terrain['mesh_asset'])
            unreal.log('Verified actual PIE uses the paired revised terrain and source-matched water: '+
                json.dumps({key:value for key,value in state.items() if key!='handle'}))
            unreal.SystemLibrary.execute_console_command(world,
                'RaftSim.CaptureSeries 12 3 10 '+label+' -545900 -362700 2000 -35.27 46.85 record')
        final=ROOT/'unreal/Saved/Screenshots'/(label+'_002.png')
        if final.is_file():
            state['screenshots']=[str(ROOT/'unreal/Saved/Screenshots'/(label+f'_{i:03d}.png')) for i in range(3)]
            if not all(Path(p).is_file() for p in state['screenshots']):raise RuntimeError('Capture series incomplete')
            sizes=[]
            for path in state['screenshots']:
                with Path(path).open('rb') as stream:header=stream.read(24)
                if header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR':
                    raise RuntimeError('Invalid screenshot header: '+path)
                sizes.append(struct.unpack('>II',header[16:24]))
            if len(set(sizes))!=1:raise RuntimeError('Capture dimensions changed during playback')
            state['actual_capture_size']=list(sizes[0])
            state['requested_capture_size']=[1280,720]
            state['capture_resolution_matched']=sizes[0]==(1280,720)
            # End PIE while editor services still exist. CaptureSeries' process
            # exit timer is destroyed with its play world, before EditorPreExit.
            state['end_play_requested']=True
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:finish(traceback.format_exc())


protected={};report=None
try:
    raw=json.loads(Path(os.environ['RAFTSIM_PAIRED_PIE_CONFIG']).read_text())
    descriptor_path=(ROOT/raw['descriptor']).resolve();label=raw['label']
    assert descriptor_path.is_relative_to(ROOT)
    # Do not assign report until the destination is validated: failure handling
    # must never create a report outside tmp or overwrite prior evidence.
    report=report_destination(ROOT,raw['report'])
    assert label.replace('-','').replace('_','').isalnum()
    assert not any((ROOT/'unreal/Saved/Screenshots'/(label+f'_{i:03d}.png')).exists() for i in range(3))
    descriptor=json.loads(descriptor_path.read_text());assert descriptor['schema']=='raftsim.south_fork_joint_preview.v2'
    assert descriptor['target_level']==LEVEL and descriptor['candidate'] and not descriptor['production_promoted']
    for relative,digest in descriptor['dependencies'].items():
        path=(ROOT/relative).resolve();assert path.is_relative_to(ROOT) and sha(path)==digest
        if path.suffix in ('.uasset','.umap'):protected[str(path)]=digest
    collision=json.loads((ROOT/descriptor['collision_audit']).read_text());terrain=collision['terrain_replacement']
    assert terrain['saved_mesh_verified'] and collision['sampled_full_map_union_verified']
    config=runtime_configuration(os.environ['RAFTSIM_ROCK_COLLISION_CONFIG'])
    verify_native(config['runtime_expectations'],output=config['report'],probe_path=config['probes'],
        export_directory=config['export_directory'],asset_path=config['asset'],
        saved_mesh_sha256=config['saved_mesh_sha256'],saved_source_sha256=config['saved_source_sha256'],
        terrain_config=os.environ['RAFTSIM_TERRAIN_REPLACEMENT_CONFIG'])
    fresh=json.loads(config['report'].read_text())
    assert fresh['native_runtime']['atlas_sha256']==descriptor['dependencies'][descriptor['atlas_manifest']]
    assert fresh['terrain_replacement']['mesh_sha256']==terrain['mesh_sha256']
    state.update(descriptor_sha256=sha(descriptor_path),preplay_native_report=str(config['report']),
        preplay_native_report_sha256=sha(config['report']))
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors=list(subsystem.get_all_level_actors())
    configs=[a for a in actors if isinstance(a,unreal.RaftSimRiverWaterConfig)];assert len(configs)==1
    # WorldPartitionStreamingGeneration only duplicates unsaved external actors
    # when their packages are dirty. SetStaticMesh alone does not mark the actor:
    # without Modify(), PIE reloads the old mesh from disk. Never save these edits.
    revised=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and
        a.static_mesh_component.static_mesh.get_path_name().split('.')[0]==terrain['mesh_asset']]
    assert len(revised)==1 and revised[0].get_name()==terrain['replacement_actor']
    revised[0].modify();revised[0].static_mesh_component.modify();configs[0].modify()
    state['unsaved_actor_duplication_requested']=True
    config_values=dict(cooked_fields_dir=descriptor['initial_fields_manifest'].rsplit('/',1)[0],
        streaming_manifest_path=descriptor['streaming_manifest'],coordinate_map_path=descriptor['coordinate_map'],
        window_center_m=unreal.Vector2D(*descriptor['window_center_m']),window_extent_m=224.,
        moving_window_station_extent_m=224.,moving_window_lateral_extent_m=224.,
        flow_band=unreal.Name('median_runnable'),recenter_hydraulic_crux=False,
        enable_moving_window_streaming=True,map_provides_terrain=True)
    for key,value in config_values.items():configs[0].set_editor_property(key,value)
    rocks=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and
        a.static_mesh_component.static_mesh.get_path_name()==descriptor['mesh_asset']]
    assert len(rocks)==1
    rocks[0].tags=list(rocks[0].tags)+[unreal.Name('RaftSimPhysicalGround'),unreal.Name('RaftSimJointReconstructionPreview')]
    for desc in unreal.WorldPartitionBlueprintLibrary.get_actor_descs():
        path=package_file(str(desc.actor_package));protected[str(path)]=sha(path)
    path=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap';protected[str(path)]=sha(path)
    # Request the supported PIE operation directly. Do not read or change the
    # protected editor preference object. tick() verifies the actual PIE world,
    # exact ground assets and paired configuration before any capture starts.
    state['editor_play_request']='LevelEditorSubsystem.editor_request_begin_play'
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
except Exception:
    error=traceback.format_exc()
    if report is not None:finish(error)
    else:unreal.log_error(error);unreal.SystemLibrary.quit_editor()
