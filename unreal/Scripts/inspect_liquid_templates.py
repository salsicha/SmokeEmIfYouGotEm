"""Read-only current engine FLIP graph/renderer inspection; quit explicitly."""
import unreal
from pathlib import Path

try:
    destination = Path(__file__).resolve().parents[2] / 'docs/reconstruction-review-2026-09-07/liquid-source-array-inputs.json'
    assert not destination.exists(), 'Retain previous inspection evidence'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(
        world,
        f'RaftSim.InspectLiquidTemplates "{destination}"')
finally:
    unreal.SystemLibrary.quit_editor()
