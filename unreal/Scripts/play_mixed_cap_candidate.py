"""Unsaved normal-map PIE with freshly verified mixed cap and matching fields.

Launch via -ExecCmds="py ABSOLUTE_PATH" so asynchronous ticks remain alive.
This is an unsettled candidate review, not promotion or performance acceptance.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_mixed_cap_installed_union import main as verify_scene,sha
from verify_constriction_union_collision import verify_runtime

LABEL=os.environ.get('RAFTSIM_MIXED_PIE_LABEL','mixed-cap-pie-20260925')
assert LABEL.replace('-','').replace('_','').isalnum()
REPORT=ROOT/'tmp'/(LABEL+'.json')
state={};protected={};started=time.perf_counter()


def finish(error=None):
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    changed=[p for p,d in protected.items() if sha(p)!=d]
    state.update(error=error,protected_files_changed=changed,complete=not error and not changed,
        playable_integrated=False,settling_accepted=False,visual_accepted=False,
        performance_accepted=False,wall_seconds=time.perf_counter()-started)
    with REPORT.open('x') as f:json.dump(state,f,indent=2)
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.perf_counter()-started>480:raise RuntimeError('Eight-minute preview bound exceeded')
        worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
        if state.get('ending'):
            if not worlds:finish()
            return
        if not worlds:return
        assert len(worlds)==1
        world=worlds[0]
        if not state.get('verified_pie'):
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.StaticMeshActor)
            cap=[a for a in actors if a.static_mesh_component.static_mesh==context['replacement']]
            ground=[a for a in actors if a.static_mesh_component.static_mesh==context['meshes']['ground']]
            old=[a for a in actors if a.static_mesh_component.static_mesh==context['meshes']['cap']]
            state['observed_mesh_counts']=dict(candidate=len(cap),ground=len(ground),old_cap=len(old))
            if not cap or not ground:
                first=state.setdefault('stream_wait',time.perf_counter())
                if time.perf_counter()-first<30:return
            assert len(cap)==len(ground)==1 and not old,'Candidate not retained in PIE'
            configs=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RaftSimRiverWaterConfig)
            assert len(configs)==1
            for key,value in values.items():assert configs[0].get_editor_property(key)==value,key
            state['verified_pie']=world.get_path_name()
            unreal.SystemLibrary.execute_console_command(world,
                'RaftSim.CaptureSeries 12 3 10 '+LABEL+' -545900 -362700 2000 -35.27 46.85 record')
        shots=[ROOT/'unreal/Saved/Screenshots'/(LABEL+f'_{i:03d}.png') for i in range(3)]
        if all(p.is_file() for p in shots):
            state['screenshots']=[dict(path=str(p),sha256=sha(p)) for p in shots]
            state['ending']=True
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:finish(traceback.format_exc())


assert not REPORT.exists()
try:
    assert not any((ROOT/'unreal/Saved/Screenshots'/(LABEL+f'_{i:03d}.png')).exists() for i in range(3))
    config=json.loads((ROOT/'tmp/troublemaker-mixed-installed-visible-config-20260925.json').read_text())
    config['report']='tmp/'+LABEL+'-preflight.json'
    context=verify_scene(config);protected=context['protected']
    expected=ROOT/'tmp/troublemaker-mixed-normal-runtime-expectations-20260925.json'
    state['native_runtime']=verify_runtime(expected,context['probe_path'],context['probes'])
    assert state['native_runtime']['field_queries_verified']
    cap=context['owners']['cap'];mesh=context['replacement']
    mesh.set_material(0,cap.static_mesh_component.get_material(0))
    cap.modify();cap.static_mesh_component.modify()
    assert cap.static_mesh_component.set_static_mesh(mesh)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    configs=[a for a in actors if isinstance(a,unreal.RaftSimRiverWaterConfig)]
    assert len(configs)==1
    base='tmp/troublemaker-mixed-normal-runtime-50s-20260925'
    values=dict(cooked_fields_dir=base+'/region_0190',streaming_manifest_path=base+'/streaming_manifest_coverage_checked.json',
        coordinate_map_path='physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json',
        window_center_m=unreal.Vector2D(*state['native_runtime']['window_center_m']),window_extent_m=224.,
        moving_window_station_extent_m=224.,moving_window_lateral_extent_m=224.,
        flow_band=unreal.Name('median_runnable'),recenter_hydraulic_crux=False,
        enable_moving_window_streaming=True,map_provides_terrain=True)
    configs[0].modify()
    for key,value in values.items():configs[0].set_editor_property(key,value)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
except Exception:finish(traceback.format_exc())
