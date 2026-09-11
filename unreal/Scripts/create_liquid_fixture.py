"""Create the explicit-SDF isolated review asset, never overwrite it."""
import unreal

try:
    collision = '-RaftSimLiquidFixtureCollision' in unreal.SystemLibrary.get_command_line()
    channel = '-RaftSimLiquidFixtureChannel' in unreal.SystemLibrary.get_command_line()
    bounded = '-RaftSimLiquidFixtureBounded' in unreal.SystemLibrary.get_command_line()
    channel = channel or bounded
    suffix = 'CollisionReview' if collision else 'SDFReview'
    asset = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBody'+suffix
    if channel:
        asset = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelOwnedReview'
    if bounded:
        asset = '/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelBoundedReview'
    assert not unreal.EditorAssetLibrary.does_asset_exist(asset), 'Refusing existing fixture'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.CreateLiquidFixture'+(' bounded' if bounded else ' channel' if channel else ' collision' if collision else ''))
    assert unreal.EditorAssetLibrary.does_asset_exist(asset)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
finally:
    unreal.SystemLibrary.quit_editor()
