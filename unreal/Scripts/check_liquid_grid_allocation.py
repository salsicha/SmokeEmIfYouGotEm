"""Actual bounded XYZ allocation check. Zero inlet; no river-physics claim."""
from pathlib import Path
import json
import re
import time
import traceback
import unreal

ROOT=Path(__file__).resolve().parents[2]
command=unreal.SystemLibrary.get_command_line()
match=re.search(r'-RaftSimAllocationLabel=([A-Za-z0-9_-]+)',command)
assert match, 'Unique allocation report label required'
output=ROOT/'docs/reconstruction-review-2026-09-07'/match.group(1)
output.mkdir(exist_ok=False)
state={'frame':0,'complete':False,'zero_inlet':True,'physical_visual_or_performance_acceptance':False}
started=time.perf_counter()


def finish(error=None):
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    state.update(complete=error is None,error=error,wall_seconds=time.perf_counter()-started)
    (output/'capture.json').write_text(json.dumps(state,indent=2)+'\n')
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        assert time.perf_counter()-started<180, 'Allocation check exceeded bounded wall time'
        frame=state['frame']
        if frame==2:liquid.set_component_tick_enabled(False)
        if frame>=2:liquid.advance_simulation(1,1/60)
        view.capture_scene()
        if frame==30:
            unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidAllocationReport "{output / "allocation.json"}"')
            report=json.loads((output/'allocation.json').read_text())
            state['allocation_verified']=report['allocation_verified']
            assert report['allocation_verified'], 'Actual GPU allocations disagree with requested XYZ layout'
            finish();return
        state['frame']+=1
    except Exception:finish(traceback.format_exc())


try:
    assert unreal.load_object(None,'/NiagaraFluids/Enums/ENiagaraGrid2DResolution.ENiagaraGrid2DResolution')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimBoot')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    water=actors.spawn_actor_from_class(unreal.NiagaraActor,unreal.Vector(0,0,350))
    water.set_actor_scale3d(unreal.Vector(1,1,1))
    liquid=water.get_component_by_class(unreal.NiagaraComponent)
    liquid.deactivate()
    liquid.set_asset(unreal.load_asset('/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview'))
    # Deliberately unequal XYZ metric: max-axis inference cannot produce this.
    state['requested_cells']=[68,36,24];state['requested_extent_cm']=[3400,2700,800]
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.LiquidAllocationReview 68 36 24 3400 2700 800')
    assert liquid.get_editor_property('asset').get_name().startswith('SouthForkLiquidAllocationReview'), 'Independent allocator was not installed'
    liquid.set_variable_float('User.Inlet Particle Rate',0.)
    camera=actors.spawn_actor_from_class(unreal.SceneCapture2D,unreal.Vector(0,0,5000),unreal.Rotator(-90,0,0))
    view=camera.get_component_by_class(unreal.SceneCaptureComponent2D)
    target=unreal.RenderingLibrary.create_render_target2d(world,64,64,unreal.TextureRenderTargetFormat.RTF_RGBA8)
    view.set_editor_property('texture_target',target)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    liquid.activate(True)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
