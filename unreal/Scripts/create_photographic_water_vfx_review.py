"""Author and verify the isolated photographic V4 Niagara review assets."""

import unreal


COMMAND = "RaftSim.CreatePhotographicV4ReviewNiagaraWaterVfxSystems"
ASSET_ROOT = "/Game/RaftSim/VFX/Water/PhotographicSubUVV4Review"
MATERIAL_ASSET = f"{ASSET_ROOT}/M_RaftSim_NiagaraWaterParticle_V4Review"
ATLAS_ASSET = f"{ASSET_ROOT}/Textures/T_RaftSim_WaterParticleV4Review_SubUV"
ASSETS = (
    "NS_RaftSim_SolverSpray_V4Review",
    "NS_RaftSim_ContactDroplets_V4Review",
    "NS_RaftSim_AeratedMist_V4Review",
    "NS_RaftSim_RapidAerosol_V4Review",
    "NS_RaftSim_RapidRoller_V4Review",
)

unreal.log(f"create_photographic_water_vfx_review: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

particle_material = unreal.EditorAssetLibrary.load_asset(MATERIAL_ASSET)
if not isinstance(particle_material, unreal.Material):
    raise RuntimeError(f"Review particle material did not load: {MATERIAL_ASSET}")
particle_atlas = unreal.EditorAssetLibrary.load_asset(ATLAS_ASSET)
if not isinstance(particle_atlas, unreal.Texture2D):
    raise RuntimeError(f"Review particle atlas did not load: {ATLAS_ASSET}")

for asset_name in ASSETS:
    asset_path = f"{ASSET_ROOT}/{asset_name}"
    system = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(system, unreal.NiagaraSystem):
        raise RuntimeError(f"Review Niagara system did not load: {asset_path}")
    if not unreal.EditorAssetLibrary.save_loaded_asset(
        system, only_if_is_dirty=False
    ):
        raise RuntimeError(f"Review Niagara system did not save: {asset_path}")

unreal.log(
    "create_photographic_water_vfx_review: isolated review complete "
    f"systems={len(ASSETS)}"
)
