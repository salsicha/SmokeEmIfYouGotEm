"""Read compiled channel translations without changing the asset."""
from pathlib import Path
import unreal

try:
    destination = Path(__file__).resolve().parents[2] / 'docs/reconstruction-review-2026-09-07/liquid-channel-outlet-shaders'
    assert not destination.exists()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, f'RaftSim.DumpLiquidChannelShaders "{destination}"')
    assert destination.is_dir()
finally:
    unreal.SystemLibrary.quit_editor()
