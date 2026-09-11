"""Create the separate terrain-contact candidate; assert actual saved bytes."""
from pathlib import Path
import hashlib
import shutil
import unreal
try:
    saved=Path(__file__).resolve().parents[1]/'Content/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainContactReview.uasset'
    option=''
    if saved.exists():
        # Preserve the exact previously measured candidate before a targeted
        # radius-mode correction. Never overwrite an unknown edited asset.
        assert hashlib.sha256(saved.read_bytes()).hexdigest()=='66f8fde07d3e097cfc05691b5868cc28283cb6305f8ffcb4453e26df2256319e'
        backup=Path(__file__).resolve().parents[2]/'tmp/liquid-terrain-contact-before-radius-20260908.uasset'
        if backup.exists():assert hashlib.sha256(backup.read_bytes()).hexdigest()==hashlib.sha256(saved.read_bytes()).hexdigest()
        else:shutil.copy2(saved,backup)
        option=' replace-reviewed'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.CreateSouthForkLiquidTerrainContact'+option)
    assert saved.is_file(),'Terrain-contact factory did not save a valid candidate'
    if option:assert hashlib.sha256(saved.read_bytes()).hexdigest()!='66f8fde07d3e097cfc05691b5868cc28283cb6305f8ffcb4453e26df2256319e','Contact radius correction was not saved'
finally:
    unreal.SystemLibrary.quit_editor()
