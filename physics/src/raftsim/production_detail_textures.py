"""Build first-party production-detail terrain texture candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


DETAIL_ROOT_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/ProductionDetailTextures")
SOURCE_ROOT_RELATIVE_PATH = DETAIL_ROOT_RELATIVE_PATH / "Sources"
MANIFEST_RELATIVE_PATH = DETAIL_ROOT_RELATIVE_PATH / "first_party_production_detail_texture_manifest.json"
TEXTURE_ASSET_ROOT_RELATIVE_PATH = DETAIL_ROOT_RELATIVE_PATH / "Textures"
MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
)
OUTPUT_SIZE = 1024
GENERATED_ON = "2026-07-09"
TEXTURE_ASSET_STATUS = (
    "created_unreal_first_party_terrain_detail_texture_candidates_bound_to_review_material_not_lifelike"
)


@dataclass(frozen=True)
class RiverDetailSpec:
    river_id: str
    display_name: str
    asset_name: str
    source_filename: str
    target_read: str
    prompt: str
    normal_strength: float
    roughness_center: float
    detail_tiling: tuple[float, float, float, float]
    albedo_weight: float
    normal_weight: float
    surface_response_weight: float


SPECS = (
    RiverDetailSpec(
        river_id="american_south_fork",
        display_name="South Fork American River",
        asset_name="AmericanSouthFork",
        source_filename="american_south_fork_terrain_bank_detail_source_v1.png",
        target_read="weathered Sierra granite gravel, compacted bank soil, pine needles, and restrained lichen",
        prompt=(
            "Photorealistic seamless straight-down terrain scan combining weathered Sierra Nevada granite "
            "fragments, compacted warm gray-brown riverbank soil, rounded gravel, sparse dry pine needles, "
            "tiny lichen traces, and darker damp seams; neutral diffuse scan lighting; base-color only."
        ),
        normal_strength=2.2,
        roughness_center=206.0,
        detail_tiling=(5.0, 5.0, 0.17, 0.31),
        albedo_weight=0.74,
        normal_weight=0.20,
        surface_response_weight=0.22,
    ),
    RiverDetailSpec(
        river_id="colorado_river",
        display_name="Colorado River, Grand Canyon",
        asset_name="ColoradoRiver",
        source_filename="colorado_river_terrain_bank_detail_source_v1.png",
        target_read="fractured red-brown sandstone, limestone chips, canyon silt, and rounded river gravel",
        prompt=(
            "Photorealistic seamless straight-down canyon ground scan combining fractured red-brown and buff "
            "sandstone, weathered limestone fragments, compacted silt, rounded river gravel, mineral dust, "
            "and darker damp seams; neutral diffuse scan lighting; base-color only."
        ),
        normal_strength=2.5,
        roughness_center=218.0,
        detail_tiling=(4.5, 4.5, 0.41, 0.13),
        albedo_weight=0.76,
        normal_weight=0.22,
        surface_response_weight=0.24,
    ),
    RiverDetailSpec(
        river_id="pacuare",
        display_name="Pacuare River",
        asset_name="Pacuare",
        source_filename="pacuare_terrain_bank_detail_source_v1.png",
        target_read="dark volcanic gravel, humid soil, leaf litter, moss, roots, and wet mineral staining",
        prompt=(
            "Photorealistic seamless straight-down rainforest ground scan combining dark volcanic river gravel, "
            "wet brown-black soil, rounded stones, decomposed leaf litter, tiny moss patches, fine roots, and "
            "humid mineral staining; neutral diffuse scan lighting; base-color only."
        ),
        normal_strength=2.0,
        roughness_center=192.0,
        detail_tiling=(5.0, 5.0, 0.29, 0.47),
        albedo_weight=0.74,
        normal_weight=0.18,
        surface_response_weight=0.20,
    ),
)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def _force_periodic_edges(array: np.ndarray) -> np.ndarray:
    result = array.copy()
    result[-1, ...] = result[0, ...]
    result[:, -1, ...] = result[:, 0, ...]
    return result


def _make_periodic_albedo(source: Image.Image) -> Image.Image:
    source = ImageOps.fit(source.convert("RGB"), (OUTPUT_SIZE, OUTPUT_SIZE), method=_resample_filter())
    array = np.asarray(source, dtype=np.float32).copy()
    feather = OUTPUT_SIZE // 10
    for distance in range(feather):
        normalized = distance / max(1, feather - 1)
        alpha = 1.0 - normalized * normalized * (3.0 - 2.0 * normalized)
        left = array[:, distance, :].copy()
        right = array[:, -1 - distance, :].copy()
        average = (left + right) * 0.5
        array[:, distance, :] = left * (1.0 - alpha) + average * alpha
        array[:, -1 - distance, :] = right * (1.0 - alpha) + average * alpha
    for distance in range(feather):
        normalized = distance / max(1, feather - 1)
        alpha = 1.0 - normalized * normalized * (3.0 - 2.0 * normalized)
        top = array[distance, :, :].copy()
        bottom = array[-1 - distance, :, :].copy()
        average = (top + bottom) * 0.5
        array[distance, :, :] = top * (1.0 - alpha) + average * alpha
        array[-1 - distance, :, :] = bottom * (1.0 - alpha) + average * alpha
    array = _force_periodic_edges(np.clip(array, 0.0, 255.0).astype(np.uint8))
    periodic = Image.fromarray(array, mode="RGB")
    periodic = ImageEnhance.Contrast(periodic).enhance(1.04)
    periodic = periodic.filter(ImageFilter.UnsharpMask(radius=0.8, percent=48, threshold=3))
    return Image.fromarray(_force_periodic_edges(np.asarray(periodic, dtype=np.uint8)), mode="RGB")


def _wrapped_smooth(values: np.ndarray) -> np.ndarray:
    result = values * 0.36
    for offset, weight in ((1, 0.12), (3, 0.075), (7, 0.035)):
        result += np.roll(values, offset, axis=0) * weight
        result += np.roll(values, -offset, axis=0) * weight
        result += np.roll(values, offset, axis=1) * weight
        result += np.roll(values, -offset, axis=1) * weight
    return result


def _derive_surface_maps(albedo: Image.Image, spec: RiverDetailSpec) -> tuple[Image.Image, Image.Image]:
    rgb = np.asarray(albedo.convert("RGB"), dtype=np.float32) / 255.0
    luma = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    smooth = _wrapped_smooth(luma)
    local = np.clip(luma - smooth, -0.22, 0.22)
    height = np.clip(smooth * 0.62 + local * 1.72 + 0.19, 0.0, 1.0)

    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * spec.normal_strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * spec.normal_strength
    normal = np.stack((-dx, -dy, np.ones_like(height)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1.0e-6)
    normal_rgb = np.clip((normal * 0.5 + 0.5) * 255.0, 0.0, 255.0).astype(np.uint8)
    normal_rgb = _force_periodic_edges(normal_rgb)

    laplacian = np.abs(
        np.roll(height, 1, axis=0)
        + np.roll(height, -1, axis=0)
        + np.roll(height, 1, axis=1)
        + np.roll(height, -1, axis=1)
        - 4.0 * height
    )
    ao = np.clip(226.0 - laplacian * 520.0 - np.maximum(0.0, smooth - height) * 96.0, 92.0, 238.0)
    roughness = np.clip(
        spec.roughness_center + np.abs(local) * 165.0 + (0.5 - luma) * 24.0,
        118.0,
        244.0,
    )
    height_bytes = np.clip(height * 255.0, 0.0, 255.0)
    packed = np.stack((ao, roughness, height_bytes), axis=-1).astype(np.uint8)
    packed = _force_periodic_edges(packed)
    return Image.fromarray(normal_rgb, mode="RGB"), Image.fromarray(packed, mode="RGB")


def _output_paths(spec: RiverDetailSpec) -> dict[str, Path]:
    stem = f"{spec.river_id}_terrain_bank_detail_v1"
    return {
        "albedo": DETAIL_ROOT_RELATIVE_PATH / f"{stem}_albedo.png",
        "normal": DETAIL_ROOT_RELATIVE_PATH / f"{stem}_normal.png",
        "ao_roughness_height": DETAIL_ROOT_RELATIVE_PATH / f"{stem}_ao_roughness_height.png",
    }


def _texture_asset(spec: RiverDetailSpec, map_id: str, source_png: Path) -> dict:
    suffix_by_map = {
        "albedo": "TerrainDetailAlbedo",
        "normal": "TerrainDetailNormal",
        "ao_roughness_height": "TerrainDetailAORoughnessHeight",
    }
    parameter_by_map = {
        "albedo": "TerrainDetailAlbedo",
        "normal": "TerrainDetailNormal",
        "ao_roughness_height": "TerrainDetailAORoughnessHeight",
    }
    compression_by_map = {
        "albedo": "TC_Default",
        "normal": "TC_Normalmap",
        "ao_roughness_height": "TC_Masks",
    }
    lod_by_map = {
        "albedo": "TEXTUREGROUP_World",
        "normal": "TEXTUREGROUP_WorldNormalMap",
        "ao_roughness_height": "TEXTUREGROUP_World",
    }
    asset_name = f"T_RaftSim_{spec.asset_name}_{suffix_by_map[map_id]}"
    return {
        "path": f"/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/{asset_name}",
        "asset_file": str(TEXTURE_ASSET_ROOT_RELATIVE_PATH / f"{asset_name}.uasset"),
        "parameter": parameter_by_map[map_id],
        "source_png": str(source_png),
        "status": "created_unreal_texture2d_first_party_detail_candidate_not_lifelike",
        "import_settings": {
            "source_pixel_format": "TSF_BGRA8",
            "source_png_mode": "RGB",
            "srgb": map_id == "albedo",
            "compression_settings": compression_by_map[map_id],
            "mip_gen_settings": "TMGS_FromTextureGroup",
            "lod_group": lod_by_map[map_id],
            "compression_no_alpha": True,
            "virtual_texture_streaming": False,
        },
    }


def _refresh_candidate_manifest(repo_root: Path, manifest: dict) -> None:
    path = repo_root / MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    if not path.exists():
        return
    candidates = json.loads(path.read_text(encoding="utf-8"))
    by_river = {river["river_id"]: river for river in manifest["rivers"]}
    candidates["generated_on"] = GENERATED_ON
    candidates["production_detail_texture_manifest"] = str(MANIFEST_RELATIVE_PATH)
    candidates["production_detail_texture_asset_root"] = str(TEXTURE_ASSET_ROOT_RELATIVE_PATH)
    candidates["production_detail_texture_asset_status"] = TEXTURE_ASSET_STATUS
    candidates["map_bindings"].update(
        {
            "AtlasTileOrigin": "RG atlas-tile origin split from scale so Metal never needs an unavailable vector alpha component.",
            "AtlasTileScale": "RG atlas-tile scale split from origin for Metal-safe material compilation.",
            "TerrainDetailAlbedo": "First-party close-range seamless terrain detail albedo sampled on dedicated tiled UVs.",
            "TerrainDetailNormal": "Derived tangent-space close-range terrain normal sampled on the same tiled UVs.",
            "TerrainDetailAORoughnessHeight": "Derived packed R=AO, G=roughness, B=height terrain detail response.",
            "TerrainDetailUvScaleOffset": "Per-river XY detail tiling and ZW phase offset independent of corridor source UVs.",
            "TerrainDetailUvScale": "RG terrain-detail tiling split from offset for Metal-safe material compilation.",
            "TerrainDetailUvOffset": "RG terrain-detail phase offset split from scale for Metal-safe material compilation.",
            "TerrainDetailAlbedoWeight": "Terrain-only close-range albedo blend; zero on water, foliage, boulder, foam, and raft candidates.",
            "TerrainDetailNormalWeight": "Terrain-only close-range normal blend.",
            "TerrainDetailSurfaceResponseWeight": "Terrain-only AO/roughness/height blend.",
        }
    )
    for candidate in candidates["candidates"]:
        river = by_river[candidate["river_id"]]
        atlas_origin_scale = candidate["review_asset_parameters"]["AtlasTileOriginScale"]
        candidate["production_detail_texture_bindings"] = {
            map_data["unreal_texture_asset"]["parameter"]: {
                "path": map_data["path"],
                "sha256": map_data["sha256"],
            }
            for map_data in river["maps"].values()
        }
        candidate["production_detail_texture_asset_bindings"] = {
            map_data["unreal_texture_asset"]["parameter"]: map_data["unreal_texture_asset"]
            for map_data in river["maps"].values()
        }
        is_terrain = candidate["recipe_id"] == "terrain_bank_layered_material"
        candidate["review_asset_parameters"].update(
            {
                "AtlasTileOrigin": atlas_origin_scale[:2],
                "AtlasTileScale": atlas_origin_scale[2:],
                "TerrainDetailUvScaleOffset": river["material_parameters"]["TerrainDetailUvScaleOffset"],
                "TerrainDetailUvScale": river["material_parameters"]["TerrainDetailUvScaleOffset"][:2],
                "TerrainDetailUvOffset": river["material_parameters"]["TerrainDetailUvScaleOffset"][2:],
                "TerrainDetailAlbedoWeight": (
                    river["material_parameters"]["TerrainDetailAlbedoWeight"] if is_terrain else 0.0
                ),
                "TerrainDetailNormalWeight": (
                    river["material_parameters"]["TerrainDetailNormalWeight"] if is_terrain else 0.0
                ),
                "TerrainDetailSurfaceResponseWeight": (
                    river["material_parameters"]["TerrainDetailSurfaceResponseWeight"] if is_terrain else 0.0
                ),
            }
        )
        candidate["expected_parameters"].update(
            {
                "AtlasTileOrigin": "metal_safe_rg_origin_split_from_legacy_combined_parameter",
                "AtlasTileScale": "metal_safe_rg_scale_split_from_legacy_combined_parameter",
                "TerrainDetailUvScaleOffset": "per_river_world_scale_detail_tiling_and_phase",
                "TerrainDetailUvScale": "metal_safe_rg_detail_tiling_split",
                "TerrainDetailUvOffset": "metal_safe_rg_detail_phase_split",
                "TerrainDetailAlbedoWeight": "terrain_only_bounded_first_party_close_range_detail",
                "TerrainDetailNormalWeight": "terrain_only_bounded_first_party_close_range_normal",
                "TerrainDetailSurfaceResponseWeight": "terrain_only_bounded_first_party_close_range_surface_response",
            }
        )
        sampler = candidate["atlas_sampler_review_material"]
        for parameter in (
            "TerrainDetailAlbedo",
            "TerrainDetailNormal",
            "TerrainDetailAORoughnessHeight",
        ):
            if parameter not in sampler["sampled_parameters"]:
                sampler["sampled_parameters"].append(parameter)
        for parameter in (
            "AtlasTileOrigin",
            "AtlasTileScale",
            "TerrainDetailUvScale",
            "TerrainDetailUvOffset",
            "TerrainDetailAlbedoWeight",
            "TerrainDetailNormalWeight",
            "TerrainDetailSurfaceResponseWeight",
        ):
            if parameter not in sampler["tuning_parameters"]:
                sampler["tuning_parameters"].append(parameter)
        sampler["output_wiring"].update(
            {
                "BaseColor": "source-conditioned corridor macro color blended with terrain-only first-party close-range albedo on dedicated tiled UVs",
                "Normal": "atlas/source normal response blended with terrain-only first-party close-range tangent normal",
                "AmbientOcclusion": "atlas/source AO blended with terrain-only packed detail red channel",
                "Roughness": "atlas/source roughness blended with terrain-only packed detail green channel",
                "PixelDepthOffset": "bounded atlas/source height blended with terrain-only packed detail blue channel",
                "uv_compile_policy": "atlas and terrain-detail scale/offset use separate RG vector parameters; no material graph component mask reads vector alpha on Metal",
            }
        )
    path.write_text(json.dumps(candidates, indent=2) + "\n", encoding="utf-8")


def generate_production_detail_textures(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    output_root = repo_root / DETAIL_ROOT_RELATIVE_PATH
    output_root.mkdir(parents=True, exist_ok=True)
    river_records = []
    for spec in SPECS:
        source_path = repo_root / SOURCE_ROOT_RELATIVE_PATH / spec.source_filename
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        source = Image.open(source_path).convert("RGB")
        albedo = _make_periodic_albedo(source)
        normal, packed = _derive_surface_maps(albedo, spec)
        relative_outputs = _output_paths(spec)
        images = {"albedo": albedo, "normal": normal, "ao_roughness_height": packed}
        for map_id, image in images.items():
            image.save(repo_root / relative_outputs[map_id], optimize=True)
        river_records.append(
            {
                "river_id": spec.river_id,
                "display_name": spec.display_name,
                "status": "first_party_generated_close_range_terrain_detail_candidate_not_lifelike",
                "target_read": spec.target_read,
                "source": {
                    "path": str(SOURCE_ROOT_RELATIVE_PATH / spec.source_filename),
                    "sha256": _hash_file(source_path),
                    "generator": "OpenAI built-in image generation",
                    "generated_on": GENERATED_ON,
                    "input_images_used": False,
                    "prompt_summary": spec.prompt,
                },
                "maps": {
                    map_id: {
                        "path": str(relative_path),
                        "sha256": _hash_file(repo_root / relative_path),
                        "width": OUTPUT_SIZE,
                        "height": OUTPUT_SIZE,
                        "channels": (
                            "RGB base color"
                            if map_id == "albedo"
                            else ("RGB tangent-space normal" if map_id == "normal" else "R=AO G=roughness B=height")
                        ),
                        "seam_policy": "opposite_edge_feather_with_exact_matching_outer_edges",
                        "unreal_texture_asset": _texture_asset(spec, map_id, relative_path),
                    }
                    for map_id, relative_path in relative_outputs.items()
                },
                "material_parameters": {
                    "TerrainDetailUvScaleOffset": list(spec.detail_tiling),
                    "TerrainDetailAlbedoWeight": spec.albedo_weight,
                    "TerrainDetailNormalWeight": spec.normal_weight,
                    "TerrainDetailSurfaceResponseWeight": spec.surface_response_weight,
                },
            }
        )

    manifest = {
        "schema": "raftsim.unreal.first_party_production_detail_textures.v1",
        "generated_on": GENERATED_ON,
        "status": "first_party_terrain_detail_candidates_generated_and_unreal_bound_not_lifelike",
        "unreal_texture_asset_root": str(TEXTURE_ASSET_ROOT_RELATIVE_PATH),
        "material_instance_candidate_manifest": str(MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH),
        "unreal_integration": {
            "asset_root": str(TEXTURE_ASSET_ROOT_RELATIVE_PATH),
            "asset_status": TEXTURE_ASSET_STATUS,
            "asset_count": len(SPECS) * 3,
            "material_parent": "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset",
            "material_binding_scope": "terrain_bank_layered_material_candidates_only",
        },
        "policy": {
            "first_party_generated_sources_only": True,
            "third_party_photos_or_social_media_used": False,
            "source_prompts_and_hashes_recorded": True,
            "terrain_detail_does_not_drive_water_or_hydraulic_geometry": True,
            "textures_must_not_hide_hazards_or_rescue_targets": True,
            "capture_human_review_and_performance_gates_remain_required": True,
        },
        "derivation": {
            "albedo": "bounded opposite-edge feathering with exact periodic edge matching and no mirrored center seam",
            "normal": "deterministic wrapped-gradient tangent-space normal derived from periodic albedo luma",
            "ao_roughness_height": "deterministic wrapped local-relief response packed as R=AO G=roughness B=height",
        },
        "rivers": river_records,
        "current_decision": (
            "Use these assets as a close-range terrain/bank detail layer below the corridor-scale source drape. "
            "They replace flat proxy material response but do not establish geospatial, guide, art, rights, "
            "hazard-readability, performance, or lifelike approval."
        ),
    }
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _refresh_candidate_manifest(repo_root, manifest)
    return manifest


if __name__ == "__main__":
    generate_production_detail_textures(Path(__file__).resolve().parents[3])
