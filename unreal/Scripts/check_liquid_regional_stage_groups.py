"""Regional stage/halo evidence with small or original dense native P2G state.

Neither mode is sustained-flow, visual, or performance acceptance.
"""
from pathlib import Path
import json
import os
import re
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
match=re.search(r'-RaftSimRegionalStageLabel=([A-Za-z0-9_-]+)',unreal.SystemLibrary.get_command_line())
assert match, 'Unique scheduler evidence label required'
output=ROOT/'docs/reconstruction-review-2026-09-07'/match.group(1)
output.mkdir(exist_ok=False)
restart_requested='-RaftSimRegionalRestart' in unreal.SystemLibrary.get_command_line()
restart_root=output
restart_results=[]
if restart_requested:
    output=restart_root/'generation-001'
    output.mkdir(exist_ok=False)
packet='-RaftSimRegionalTransferPacket' in unreal.SystemLibrary.get_command_line()
dense='-RaftSimRegionalDense' in unreal.SystemLibrary.get_command_line()
emission='-RaftSimRegionalEmission' in unreal.SystemLibrary.get_command_line() or dense
step_match=re.search(r'-RaftSimRegionalTransferPacketStep=(\d+)',unreal.SystemLibrary.get_command_line())
packet_step=int(step_match.group(1)) if step_match else 1
state=dict(frame=0,complete=False,zero_water=not packet,fluid_or_performance_acceptance=False)
started=time.perf_counter()
all_regions='-RaftSimRegionalStageAll' in unreal.SystemLibrary.get_command_line()
expected_regions=12 if all_regions else 2


def finish(error=None):
    global output,started,components
    if error is not None and not (output/'stages.json').exists():
        # Keep the actual failed schedule and native error, not only a Python
        # traceback. The capture remains failed even if diagnostic saving works.
        try:
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidRegionalStageProbe stop "{output / "stages.json"}"')
        except Exception:
            state['failure_snapshot_error']=traceback.format_exc()
    state.update(complete=error is None,error=error,wall_seconds=time.perf_counter()-started,process_id=os.getpid())
    (output/'capture.json').write_text(json.dumps({k:v for k,v in state.items() if k!='handle'},indent=2)+'\n')
    if restart_requested:
        restart_results.append(dict(directory=output.name,complete=error is None,process_id=os.getpid()))
        if error is None and len(restart_results)==1:
            # stop already removed render callbacks, flushed pending work and
            # destroyed the old native components. Start fresh in the SAME world
            # and process, so no process exit can conceal stale coordinator state.
            handle=state['handle']
            state.clear();state.update(frame=0,complete=False,zero_water=not packet,fluid_or_performance_acceptance=False,handle=handle)
            output=restart_root/'generation-002';output.mkdir(exist_ok=False)
            started=time.perf_counter()
            try:
                components=start_regions()
                return
            except Exception:
                finish(traceback.format_exc());return
        (restart_root/'restart.json').write_text(json.dumps(dict(complete=error is None and len(restart_results)==2,
            process_id=os.getpid(),generations=restart_results,visual_or_performance_acceptance=False),indent=2)+'\n')
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        assert time.perf_counter()-started<240, 'Regional stage probe wall-time bound exceeded'
        # Every component enqueues its tick before one common render flush.
        # A scheduler proof requires observed groups, not this intended order.
        # A reset batch can otherwise queue several ticks before the first GPU
        # spawn completes. Native CPU dispatch bounds then exclude future imports.
        # Wait for observed completion of the first native tick, not a frame delay.
        if not packet or not state.get('initial_tick_enqueued') or state.get('initial_native_complete'):
            for component in components:component.advance_simulation(1,1/60)
            state['initial_tick_enqueued']=True
        view.capture_scene()
        ready=not packet and state['frame']==30
        if packet and (emission or not state.get('initial_native_complete') or state['frame']>=packet_step):
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidRegionalStageProbe status "{output / "live-status.json"}"')
            live=json.loads((output/'live-status.json').read_text())
            assert not live['error'], live['error']
            if live['native_steps']>=1:state['initial_native_complete']=True
            if emission and live['native_steps']>=1 and not state.get('emission_requested'):
                unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidRegionalStageProbe emit')
                state['emission_requested']=True
            ready=live['packet_captured']
        if ready:
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidRegionalStageProbe stop "{output / "stages.json"}"')
            report=json.loads((output/'stages.json').read_text())
            state['scheduler_alignment_observed']=report['scheduler_alignment_observed']
            assert report['scheduler_alignment_observed'], 'Regional dispatch stages did not align; inspect retained group records'
            assert not report['records_truncated'], 'Retained schedule evidence truncated'
            state['empty_regional_exchange_dispatched']=report['empty_regional_exchange_dispatched']
            assert report['empty_regional_exchange_dispatched'], report['exchange_error']
            assert report['region_count']==expected_regions
            solve_groups=sum(g['entries'][0]['name']=='Solve Pressure' for g in report['groups'])
            assert report['pressure_halo_dispatches']==solve_groups, 'Missed same-iteration halo exchange'
            assert report['shared_columns']==(5960 if all_regions else 136), 'Incomplete shared face/corner map'
            # Independent prepared canonical mappings, not the C++ builder's
            # counts. Reflect both Y addresses and compare every source/target.
            ids=set(report['region_ids'])
            geometry=ROOT/'tmp/south-fork-liquid-regional-geometry-v4-20260910'
            pages={i:json.loads((geometry/f'region-{i:03d}-boundary.json').read_text()) for i in ids}
            expected=[]
            for dest,page in pages.items():
                dy_size=page['computational_cells'][1]
                for dx,dy,source,sx,sy in page['shared_halo_columns']:
                    if source in ids:
                        expected.append((source,dest,sx,pages[source]['computational_cells'][1]-1-sy,dx,dy_size-1-dy))
            assert sorted(map(tuple,report['halo_columns_niagara']))==sorted(expected), 'Regional GPU addresses disagree with independently audited canonical ownership'
            state['all_halo_addresses_match_prepared_geometry']=True
            if '-RaftSimRegionalContact' in unreal.SystemLibrary.get_command_line():
                assert report['canonical_regional_contact_installed'] and report['boundary_readback_valid'], 'Missing actual regional contact/grid evidence'
            if '-RaftSimRegionalProjection' in unreal.SystemLibrary.get_command_line():
                assert report['regional_compatible_projection_installed'], 'Regional metric/pressure ownership installation missing'
            if '-RaftSimRegionalPressureMarker' in unreal.SystemLibrary.get_command_line():
                assert report['nonzero_pressure_marker_seeded'] and report['nonzero_pressure_marker_readback_valid'], 'Nonzero pressure marker readback missing'
            if '-RaftSimRegionalBoundaryExchange' in unreal.SystemLibrary.get_command_line():
                boundary_groups=sum(g['entries'][0]['name']=='Compute Boundary' for g in report['groups'])
                assert report['shared_boundary_exchange_enabled'] and report['boundary_halo_dispatches']==boundary_groups>0, 'Missing same-step boundary exchange'
            if '-RaftSimRegionalParentExterior' in unreal.SystemLibrary.get_command_line():
                assert report['parent_exterior_forcing_installed'] and report['outlet_pressure_readback_valid'], 'Parent-domain forcing/pressure evidence missing'
            if '-RaftSimRegionalTransfer' in unreal.SystemLibrary.get_command_line():
                raster_groups=sum(g['entries'][0]['name']=='Neighbor Grid Rasterize Particles' for g in report['groups'])
                assert report['conservative_transfer_enabled'] and report['raw_transfer_reductions']==raster_groups>0, 'Missing same-step raw reduction / native resolve'
            if packet:
                assert not report['zero_water'] and report['native_transfer_packet_saved'], 'Actual native particle/raw/total snapshots missing'
            finish();return
        state['frame']+=1
    except Exception:finish(traceback.format_exc())


def start_regions():
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidRegionalStageProbe start'+(' all' if all_regions else ''))
    # EditorActorSubsystem deliberately excludes RF_Transient actors. Keep the
    # probe unsavable and enumerate its exact labels in this world instead.
    current=[a.get_component_by_class(unreal.NiagaraComponent) for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
                if a.get_actor_label().startswith('LiquidRegionalStageProbe_')]
    assert len(current)==expected_regions and all(current), 'Expected unsaved regional components required'
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    return current


try:
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimBoot')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    components=start_regions()
    camera=actors.spawn_actor_from_class(unreal.SceneCapture2D,unreal.Vector(0,0,5000),unreal.Rotator(-90,0,0))
    view=camera.get_component_by_class(unreal.SceneCaptureComponent2D)
    view.set_editor_property('capture_every_frame',False)
    view.set_editor_property('capture_on_movement',False)
    view.set_editor_property('texture_target',unreal.RenderingLibrary.create_render_target2d(world,64,64,unreal.TextureRenderTargetFormat.RTF_RGBA8))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
