"""Read actual engine contact graph inputs; no asset modifications."""
from pathlib import Path
import unreal
try:
    destination=Path(__file__).resolve().parents[2]/'docs/reconstruction-review-2026-09-07/liquid-particle-update-inputs.json'
    assert not destination.exists()
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world,f'RaftSim.InspectLiquidContactModules "{destination}"')
    assert destination.is_file()
finally:
    unreal.SystemLibrary.quit_editor()
