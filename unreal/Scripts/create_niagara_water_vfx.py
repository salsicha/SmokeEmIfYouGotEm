"""Author and verify the project-owned Niagara live-water VFX systems."""

import unreal


COMMAND = "RaftSim.CreateNiagaraWaterVfxSystems"
ASSET_ROOT = "/Game/RaftSim/VFX/Water"
MATERIAL_ASSET = "/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle"
ATLAS_ASSET = "/Game/RaftSim/VFX/Water/Textures/T_RaftSim_WaterParticle_SubUV"
ASSETS = (
    "NS_RaftSim_SolverSpray",
    "NS_RaftSim_ContactDroplets",
    "NS_RaftSim_AeratedMist",
    "NS_RaftSim_RapidAerosol",
    "NS_RaftSim_RapidRoller",
    "NS_RaftSim_RapidCrestSpray",
)

unreal.log(f"create_niagara_water_vfx: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

particle_material = unreal.EditorAssetLibrary.load_asset(MATERIAL_ASSET)
if not isinstance(particle_material, unreal.Material):
    raise RuntimeError(f"Niagara particle material did not load: {MATERIAL_ASSET}")
particle_atlas = unreal.EditorAssetLibrary.load_asset(ATLAS_ASSET)
if not isinstance(particle_atlas, unreal.Texture2D):
    raise RuntimeError(f"Niagara particle atlas did not load: {ATLAS_ASSET}")

for asset_name in ASSETS:
    asset_path = f"{ASSET_ROOT}/{asset_name}"
    system = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(system, unreal.NiagaraSystem):
        raise RuntimeError(f"Niagara system did not load: {asset_path}")
    if not unreal.EditorAssetLibrary.save_loaded_asset(
        system, only_if_is_dirty=False
    ):
        raise RuntimeError(f"Niagara system did not save: {asset_path}")

unreal.log(f"create_niagara_water_vfx: complete systems={len(ASSETS)}")
