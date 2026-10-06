"""Build a separate captured-terrain Niagara source asset, not a production edit."""
import unreal
from pathlib import Path

try:
    path='/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview'
    assert not unreal.EditorAssetLibrary.does_asset_exist(path)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.CreateSouthForkLiquidTerrain')
    assert unreal.EditorAssetLibrary.does_asset_exist(path), 'Terrain liquid was not created'
    saved=Path(__file__).resolve().parents[1]/'Content/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.uasset'
    assert saved.is_file(), 'Factory returned without saving a valid terrain liquid asset'
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
finally:
    unreal.SystemLibrary.quit_editor()
