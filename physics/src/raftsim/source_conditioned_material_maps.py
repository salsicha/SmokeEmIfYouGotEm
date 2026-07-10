"""Generate source-conditioned material map candidates for photoreal river previews."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


CAPTURE_MANIFEST_RELATIVE_PATH = Path("docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json")
SOURCE_CONDITIONED_MATERIAL_MAP_ROOT_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps"
)
SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH = (
    SOURCE_CONDITIONED_MATERIAL_MAP_ROOT_RELATIVE_PATH
    / "first_party_source_conditioned_material_map_manifest.json"
)
SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH = (
    SOURCE_CONDITIONED_MATERIAL_MAP_ROOT_RELATIVE_PATH / "Textures"
)
FIRST_PARTY_MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
)
SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS = (
    "created_unreal_texture2d_review_assets_bound_to_source_conditioned_material_instances_not_lifelike"
)

OUTPUT_SIZE = 2048

RIVER_ASSET_NAMES = {
    "american_south_fork": "AmericanSouthFork",
    "colorado_river": "ColoradoRiver",
    "pacuare": "Pacuare",
}

UNREAL_TEXTURE_ASSET_BY_MAP_ID = {
    "macro_albedo": {
        "parameter": "SourceConditionedMacroAlbedo",
        "asset_suffix": "SourceConditionedMacroAlbedo",
        "compression_settings": "TC_Default",
        "srgb": True,
        "lod_group": "TEXTUREGROUP_World",
    },
    "material_zones": {
        "parameter": "SourceConditionedMaterialZones",
        "asset_suffix": "SourceConditionedMaterialZones",
        "compression_settings": "TC_Masks",
        "srgb": False,
        "lod_group": "TEXTUREGROUP_World",
    },
    "ao_roughness_height": {
        "parameter": "SourceConditionedAORoughnessHeight",
        "asset_suffix": "SourceConditionedAORoughnessHeight",
        "compression_settings": "TC_Masks",
        "srgb": False,
        "lod_group": "TEXTUREGROUP_World",
    },
    "normal_detail": {
        "parameter": "SourceConditionedNormalDetail",
        "asset_suffix": "SourceConditionedNormalDetail",
        "compression_settings": "TC_Normalmap",
        "srgb": False,
        "lod_group": "TEXTUREGROUP_WorldNormalMap",
    },
}
SOURCE_CONDITIONED_TEXTURE_PARAMETERS = {
    spec["parameter"]: map_id for map_id, spec in UNREAL_TEXTURE_ASSET_BY_MAP_ID.items()
}

MATERIAL_RESPONSE_BY_RECIPE = {
    "terrain_bank_layered_material": {
        "RoughnessScale": 0.92,
        "RoughnessFloor": 0.72,
        "EmissiveFillScale": 0.42,
        "SpecularLevel": 0.0,
    },
    "wet_boulder_contact_material_set": {
        "RoughnessScale": 0.64,
        "RoughnessFloor": 0.66,
        "EmissiveFillScale": 0.42,
        "SpecularLevel": 0.0,
    },
    "biome_foliage_groundcover_materials": {
        "RoughnessScale": 0.78,
        "RoughnessFloor": 0.68,
        "EmissiveFillScale": 0.42,
        "SpecularLevel": 0.0,
    },
    "foam_spray_mist_atmosphere_materials": {
        "RoughnessScale": 0.40,
        "RoughnessFloor": 0.74,
        "EmissiveFillScale": 0.42,
        "SpecularLevel": 0.0,
    },
    "raft_foreground_review_materials": {
        "RoughnessScale": 0.56,
        "RoughnessFloor": 0.70,
        "EmissiveFillScale": 0.42,
        "SpecularLevel": 0.0,
    },
}

WATER_MATERIAL_RESPONSE_BY_RIVER = {
    "american_south_fork": {
        "RoughnessScale": 0.18,
        "RoughnessFloor": 0.28,
        "EmissiveFillScale": 0.26,
        "SpecularLevel": 0.22,
        "MeshNormalUpBlend": 0.15,
        "NormalIntensity": 0.32,
    },
    "colorado_river": {
        "RoughnessScale": 0.22,
        "RoughnessFloor": 0.34,
        "EmissiveFillScale": 0.28,
        "SpecularLevel": 0.18,
        "MeshNormalUpBlend": 0.18,
        "NormalIntensity": 0.22,
    },
    "pacuare": {
        "RoughnessScale": 0.18,
        "RoughnessFloor": 0.30,
        "EmissiveFillScale": 0.26,
        "SpecularLevel": 0.22,
        "MeshNormalUpBlend": 0.12,
        "NormalIntensity": 0.36,
    },
}


@dataclass(frozen=True)
class SourceConditionedMaterialMapRecord:
    river_id: str
    display_name: str
    flow_band_id: str
    source_inputs: dict[str, str]
    outputs: dict[str, Path]
    sha256: dict[str, str]
    width: int
    height: int


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_rgb(repo_root: Path, relative_path: str) -> Image.Image:
    return Image.open(repo_root / relative_path).convert("RGB").resize((OUTPUT_SIZE, OUTPUT_SIZE), _resample_filter())


def _open_luma(repo_root: Path, relative_path: str) -> Image.Image:
    return Image.open(repo_root / relative_path).convert("L").resize((OUTPUT_SIZE, OUTPUT_SIZE), _resample_filter())


def _scale_mask(mask: Image.Image, factor: float) -> Image.Image:
    return mask.point(lambda pixel: max(0, min(255, int(pixel * factor))))


def _odd_kernel_size(size: int) -> int:
    size = max(3, int(round(size)))
    return size if size % 2 else size + 1


def _fast_rank_filter(mask: Image.Image, size: int, filter_class: type[ImageFilter.Filter]) -> Image.Image:
    mask = mask.convert("L")
    if size <= 9:
        return mask.filter(filter_class(_odd_kernel_size(size)))

    downsample = 4
    reduced_size = (
        max(1, mask.size[0] // downsample),
        max(1, mask.size[1] // downsample),
    )
    reduced = mask.resize(reduced_size, _resample_filter())
    reduced_filter_size = _odd_kernel_size(size / downsample)
    filtered = reduced.filter(filter_class(reduced_filter_size))
    return filtered.resize(mask.size, _resample_filter()).convert("L")


def _fast_dilate(mask: Image.Image, size: int) -> Image.Image:
    return _fast_rank_filter(mask, size, ImageFilter.MaxFilter)


def _fast_erode(mask: Image.Image, size: int) -> Image.Image:
    return _fast_rank_filter(mask, size, ImageFilter.MinFilter)


def _invert_mask(mask: Image.Image) -> Image.Image:
    return ImageOps.invert(mask.convert("L"))


def _source_luma_detail(source_drape: Image.Image) -> Image.Image:
    luma = ImageOps.autocontrast(source_drape.convert("L"), cutoff=0.5)
    local_contrast = luma.filter(ImageFilter.UnsharpMask(radius=2.0, percent=160, threshold=4))
    broad = luma.filter(ImageFilter.GaussianBlur(radius=9.0))
    highpass = ImageChops.subtract(local_contrast, broad, scale=1.0, offset=128)
    return ImageOps.autocontrast(highpass.filter(ImageFilter.GaussianBlur(radius=0.45)), cutoff=0.25)


def _wet_edge_mask(water_mask: Image.Image) -> Image.Image:
    return ImageChops.subtract(
        _fast_dilate(water_mask, 41),
        _fast_erode(water_mask, 9),
    ).filter(ImageFilter.GaussianBlur(radius=1.1))


def _outer_water_edge_mask(water_mask: Image.Image, size: int) -> Image.Image:
    return ImageChops.subtract(_fast_dilate(water_mask, size), water_mask.convert("L"))


def _detail_shade(detail: Image.Image, strength: float) -> Image.Image:
    strength = max(0.0, min(1.0, strength))
    return detail.point(lambda p: max(0, min(255, int(255 - (128 - p) * strength))))


def _blend_luma(base: Image.Image, detail: Image.Image, mask: Image.Image, strength: float) -> Image.Image:
    detail_shade = _detail_shade(detail, strength)
    detailed = ImageChops.multiply(base, Image.merge("RGB", (detail_shade, detail_shade, detail_shade)))
    return Image.composite(detailed, base, _scale_mask(mask, 1.0))


def _height_with_source_microdetail(
    relief: Image.Image,
    source_detail: Image.Image,
    water_mask: Image.Image,
    vegetation_mask: Image.Image,
) -> Image.Image:
    relief_height = ImageOps.autocontrast(relief)
    wet_edge = _wet_edge_mask(water_mask)
    non_water = _invert_mask(water_mask)
    non_water_detail = ImageChops.multiply(source_detail, non_water)
    bank_detail = ImageChops.multiply(source_detail.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120)), wet_edge)
    vegetation_detail = ImageChops.multiply(
        source_detail.filter(ImageFilter.GaussianBlur(radius=0.6)),
        ImageChops.multiply(vegetation_mask, non_water),
    )
    height = Image.blend(relief_height, non_water_detail, 0.18)
    height = Image.composite(Image.blend(height, bank_detail, 0.34), height, _scale_mask(wet_edge, 1.20))
    height = Image.composite(
        Image.blend(height, vegetation_detail, 0.20),
        height,
        _scale_mask(vegetation_mask, 0.62),
    )
    return ImageOps.autocontrast(height.filter(ImageFilter.GaussianBlur(radius=0.45)), cutoff=0.15)


def _apply_relief_shade(image: Image.Image, relief: Image.Image) -> Image.Image:
    relief_smooth = relief.filter(ImageFilter.GaussianBlur(radius=5.0))
    high = relief_smooth.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(radius=1.2))
    shade = relief_smooth.point(lambda p: max(196, min(255, int(226 + (p - 128) * 0.16))))
    ridge_shadow = high.point(lambda p: max(196, min(255, int(255 - p * 0.18))))
    shaded = ImageChops.multiply(image, Image.merge("RGB", (shade, shade, shade)))
    return ImageChops.multiply(shaded, Image.merge("RGB", (ridge_shadow, ridge_shadow, ridge_shadow)))


def _macro_albedo(
    source_drape: Image.Image,
    relief: Image.Image,
    water_mask: Image.Image,
    vegetation_mask: Image.Image,
) -> Image.Image:
    source_detail = _source_luma_detail(source_drape)
    base = ImageOps.autocontrast(source_drape, cutoff=0.5)
    base = ImageEnhance.Color(base).enhance(1.08)
    base = ImageEnhance.Contrast(base).enhance(1.10)

    water_tint = Image.blend(base, Image.new("RGB", base.size, (42, 88, 82)), 0.42)
    veg_tint = Image.blend(base, Image.new("RGB", base.size, (42, 86, 42)), 0.28)
    water_edge = _outer_water_edge_mask(water_mask, 31)
    wet_bank_tint = Image.blend(base, Image.new("RGB", base.size, (42, 44, 38)), 0.30)

    result = Image.composite(veg_tint, base, _scale_mask(vegetation_mask, 0.78))
    result = Image.composite(wet_bank_tint, result, _scale_mask(water_edge, 1.25))
    result = Image.composite(water_tint, result, _scale_mask(water_mask, 0.90))
    result = _blend_luma(result, source_detail, _invert_mask(water_mask), 0.20)
    result = _blend_luma(result, source_detail, ImageChops.multiply(vegetation_mask, _invert_mask(water_mask)), 0.16)
    result = _blend_luma(result, source_detail, water_edge, 0.24)
    return _apply_relief_shade(result.filter(ImageFilter.UnsharpMask(radius=1.0, percent=95, threshold=3)), relief)


def _material_zones(water_mask: Image.Image, vegetation_mask: Image.Image) -> Image.Image:
    water = water_mask.filter(ImageFilter.GaussianBlur(radius=0.6))
    vegetation = vegetation_mask.filter(ImageFilter.GaussianBlur(radius=0.6))
    wet_bank = _outer_water_edge_mask(water, 37).filter(ImageFilter.GaussianBlur(radius=1.0))
    non_water = _invert_mask(water)
    terrain = ImageChops.lighter(_scale_mask(non_water, 0.92), _scale_mask(wet_bank, 1.25))
    vegetation_channel = ImageChops.multiply(vegetation, non_water)
    return Image.merge("RGB", (terrain, vegetation_channel, water))


def _ao_roughness_height(
    source_drape: Image.Image,
    relief: Image.Image,
    water_mask: Image.Image,
    vegetation_mask: Image.Image,
) -> Image.Image:
    source_detail = _source_luma_detail(source_drape)
    height = _height_with_source_microdetail(relief, source_detail, water_mask, vegetation_mask)
    edges = height.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(radius=1.0))
    ao = edges.point(lambda p: max(84, min(244, int(226 - p * 0.42))))

    water = water_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    vegetation = vegetation_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    wet_bank = _wet_edge_mask(water)
    non_water = _invert_mask(water)

    rough_terrain = Image.new("L", relief.size, 210)
    rough_veg = Image.new("L", relief.size, 235)
    rough_water = Image.new("L", relief.size, 74)
    rough_wet_bank = Image.new("L", relief.size, 160)
    roughness = Image.composite(rough_veg, rough_terrain, _scale_mask(vegetation, 0.9))
    roughness = Image.composite(rough_wet_bank, roughness, _scale_mask(wet_bank, 1.2))
    roughness = Image.composite(rough_water, roughness, _scale_mask(water, 0.95))
    rough_micro = source_detail.point(lambda p: max(0, min(255, int(194 + (p - 128) * 0.28))))
    roughness = Image.composite(
        ImageChops.multiply(roughness, rough_micro),
        roughness,
        _scale_mask(non_water, 0.82),
    )
    roughness = ImageChops.multiply(roughness, non_water.point(lambda p: max(220, p)))
    return Image.merge("RGB", (ao, roughness, height))


def _normal_detail(
    source_drape: Image.Image,
    relief: Image.Image,
    water_mask: Image.Image,
    vegetation_mask: Image.Image,
) -> Image.Image:
    source_detail = _source_luma_detail(source_drape)
    height = _height_with_source_microdetail(relief, source_detail, water_mask, vegetation_mask).filter(
        ImageFilter.GaussianBlur(radius=0.8)
    )
    water = water_mask.filter(ImageFilter.GaussianBlur(radius=0.9))
    vegetation = vegetation_mask.filter(ImageFilter.GaussianBlur(radius=1.1))
    wet_bank = _outer_water_edge_mask(water, 35).filter(ImageFilter.GaussianBlur(radius=1.0))

    height_array = np.asarray(height, dtype=np.float32) / 255.0
    dy, dx = np.gradient(height_array)
    dx *= 2.0
    dy *= 2.0

    water_t = np.asarray(water, dtype=np.float32) / 255.0
    vegetation_t = np.asarray(vegetation, dtype=np.float32) / 255.0
    wet_bank_t = np.asarray(wet_bank, dtype=np.float32) / 255.0
    terrain_t = np.maximum(0.0, 1.0 - water_t)
    strength = 2.25 * terrain_t + 0.72 * vegetation_t + 1.20 * wet_bank_t + 0.18 * water_t

    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.dstack(
        (
            np.clip((nx / length * 0.5 + 0.5) * 255.0, 0, 255),
            np.clip((ny / length * 0.5 + 0.5) * 255.0, 0, 255),
            np.clip((nz / length * 0.5 + 0.5) * 255.0, 0, 255),
        )
    ).astype(np.uint8)
    return Image.fromarray(normal, "RGB")


def _record_for_capture(repo_root: Path, capture: dict[str, object], output_root: Path) -> SourceConditionedMaterialMapRecord:
    river_id = str(capture["river_id"])
    source_inputs = {
        "aerial_drape_image": str(capture["aerial_drape_image"]),
        "terrain_relief_image": str(capture["terrain_relief_image"]),
        "heightfield_preview_image": str(capture["heightfield_preview_image"]),
        "water_mask_image": str(capture["water_mask_image"]),
        "vegetation_mask_image": str(capture["vegetation_mask_image"]),
    }
    source_drape = _open_rgb(repo_root, source_inputs["aerial_drape_image"])
    relief = _open_luma(repo_root, source_inputs["terrain_relief_image"])
    water = _open_luma(repo_root, source_inputs["water_mask_image"])
    vegetation = _open_luma(repo_root, source_inputs["vegetation_mask_image"])

    images = {
        "macro_albedo": _macro_albedo(source_drape, relief, water, vegetation),
        "material_zones": _material_zones(water, vegetation),
        "ao_roughness_height": _ao_roughness_height(source_drape, relief, water, vegetation),
        "normal_detail": _normal_detail(source_drape, relief, water, vegetation),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        map_id: output_root / f"{river_id}_source_conditioned_{map_id}.png"
        for map_id in images
    }
    for map_id, image in images.items():
        image.save(outputs[map_id])

    return SourceConditionedMaterialMapRecord(
        river_id=river_id,
        display_name=str(capture.get("display_name", river_id)),
        flow_band_id=str(capture.get("flow_band_id", "")),
        source_inputs=source_inputs,
        outputs=outputs,
        sha256={map_id: _hash_file(path) for map_id, path in outputs.items()},
        width=OUTPUT_SIZE,
        height=OUTPUT_SIZE,
    )


def _records_to_manifest(repo_root: Path, records: Iterable[SourceConditionedMaterialMapRecord]) -> dict:
    river_maps = []
    for record in records:
        river_asset_name = RIVER_ASSET_NAMES[record.river_id]
        river_maps.append(
            {
                "river_id": record.river_id,
                "display_name": record.display_name,
                "flow_band_id": record.flow_band_id,
                "status": "generated_review_gated_source_conditioned_material_maps_not_lifelike",
                "source_inputs": record.source_inputs,
                "maps": {
                    map_id: {
                        "path": str(path.relative_to(repo_root)),
                        "sha256": record.sha256[map_id],
                        "width": record.width,
                        "height": record.height,
                        "unreal_texture_asset": {
                            "path": (
                                "/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures/"
                                f"T_RaftSim_{river_asset_name}_{UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id]['asset_suffix']}"
                            ),
                            "asset_file": str(
                                SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
                                / f"T_RaftSim_{river_asset_name}_{UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id]['asset_suffix']}.uasset"
                            ),
                            "parameter": UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id]["parameter"],
                            "source_png": str(path.relative_to(repo_root)),
                            "status": "created_unreal_texture2d_review_asset_not_lifelike",
                            "import_settings": {
                                "source_pixel_format": "TSF_BGRA8",
                                "source_png_mode": "RGB",
                                "srgb": UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id]["srgb"],
                                "compression_settings": UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id][
                                    "compression_settings"
                                ],
                                "mip_gen_settings": "TMGS_FromTextureGroup",
                                "lod_group": UNREAL_TEXTURE_ASSET_BY_MAP_ID[map_id]["lod_group"],
                                "compression_no_alpha": True,
                                "virtual_texture_streaming": False,
                            },
                        },
                    }
                    for map_id, path in record.outputs.items()
                },
                "promotion_gate": (
                    "Use as source-conditioned Unreal material candidates only after geospatial/source review, "
                    "rights/provenance review, guide readability review, in-engine material assignment, "
                    "capture comparison, and desktop/VR performance evidence pass."
                ),
            }
        )
    return {
        "schema": "raftsim.unreal.source_conditioned_material_maps.v1",
        "generated_on": "2026-07-09",
        "status": "generated_review_gated_source_conditioned_material_maps_not_lifelike",
        "source_capture_manifest": str(CAPTURE_MANIFEST_RELATIVE_PATH),
        "unreal_texture_asset_root": str(SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH),
        "unreal_texture_asset_status": SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS,
        "unreal_material_instance_binding_status": (
            "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
        ),
        "policy": {
            "source_inputs_are_manifest_recorded": True,
            "third_party_social_or_outfitter_media_used": False,
            "maps_are_review_gated_not_lifelike_evidence": True,
            "material_maps_must_not_hide_hazards_rescue_targets_or_physics_failures": True,
            "promotion_requires_unreal_material_assignment_capture_review_guide_review_and_performance_evidence": True,
        },
        "unreal_sampled_parameters": [
            "SourceConditionedMacroAlbedo",
            "SourceConditionedMaterialZones",
            "SourceConditionedAORoughnessHeight",
            "SourceConditionedNormalDetail",
            "SourceConditionedZoneWeights",
            "SourceConditionedMacroAlbedoWeight",
            "SourceConditionedSurfaceResponseWeight",
            "SourceConditionedNormalDetailWeight",
        ],
        "source_conditioned_detail_model": {
            "model_id": "source_luma_wet_vegetation_microdetail_v2",
            "source_inputs": [
                "aerial_drape_luma_local_contrast",
                "dem_relief_edges",
                "water_mask_wet_edge_band",
                "vegetation_mask_non_water_detail",
            ],
            "safety_bounds": [
                "visible_water_normal_strength_remains_low",
                "wet_edge_microdetail_is_visual_only",
                "maps_do_not_create_or_hide_hydraulic_geometry",
                "promotion_still_requires_capture_guide_geospatial_hazard_and_performance_review",
            ],
            "intended_visual_delta": (
                "Add source-drape texture variation to banks, rocks, vegetation, wet edges, roughness, height, "
                "and normal-detail candidates so reviewed materials read less like smooth DEM-only proxies."
            ),
        },
        "map_semantics": {
            "macro_albedo": "Source-drape-colored material macro map with bounded water, wet-bank, vegetation, DEM-relief shading, and source-luma microdetail.",
            "material_zones": "RGB material-zone weights: R=terrain/wet bank, G=vegetation away from water, B=visible water.",
            "ao_roughness_height": "Packed RGB map: R=source/relief-derived ambient-occlusion proxy, G=material roughness candidate with aerial-luma variation, B=DEM plus source-luma height candidate.",
            "normal_detail": "Tangent-space normal-detail candidate derived from DEM relief, source-drape luma, water wet-edge bands, and vegetation masks; visible water is deliberately low-strength so material response does not invent hidden hydraulic geometry.",
        },
        "rivers": river_maps,
        "current_decision": (
            "Use these source-conditioned maps as the next first-party material replacement candidates for Unreal "
            "terrain, water-edge, vegetation, wet-bank, and relief-driven surface response. They are derived from "
            "review-gated aerial/DEM/mask inputs and are not lifelike approval or production-playable evidence."
        ),
    }


def generate_source_conditioned_material_maps(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    capture_manifest = json.loads((repo_root / CAPTURE_MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8"))
    output_root = repo_root / SOURCE_CONDITIONED_MATERIAL_MAP_ROOT_RELATIVE_PATH
    records = [_record_for_capture(repo_root, capture, output_root) for capture in capture_manifest["captures"]]
    manifest = _records_to_manifest(repo_root, records)
    manifest_path = repo_root / SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_source_conditioned_material_instance_candidate_bindings(repo_root)
    return manifest


def refresh_source_conditioned_material_instance_candidate_bindings(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    source_map_manifest_path = repo_root / SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    candidate_manifest_path = repo_root / FIRST_PARTY_MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    if not candidate_manifest_path.exists():
        return {}

    source_map_manifest = json.loads(source_map_manifest_path.read_text(encoding="utf-8"))
    candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    source_maps_by_river = {river["river_id"]: river["maps"] for river in source_map_manifest["rivers"]}

    candidate_manifest["map_bindings"].update(
        {
            "EmissiveFillScale": (
                "Per-instance DefaultLit emissive fill; water keeps this low so mesh normals and scene lighting "
                "remain visible."
            ),
            "SpecularLevel": (
                "Per-instance DefaultLit dielectric specular response; bounded by river and review-only until "
                "production water shading is approved."
            ),
        }
    )

    for candidate in candidate_manifest["candidates"]:
        source_maps = source_maps_by_river[candidate["river_id"]]
        candidate["source_conditioned_texture_bindings"] = {
            parameter: {
                "path": source_maps[map_id]["path"],
                "sha256": source_maps[map_id]["sha256"],
            }
            for parameter, map_id in SOURCE_CONDITIONED_TEXTURE_PARAMETERS.items()
        }
        candidate["source_conditioned_texture_asset_bindings"] = {
            parameter: source_maps[map_id]["unreal_texture_asset"]
            for parameter, map_id in SOURCE_CONDITIONED_TEXTURE_PARAMETERS.items()
        }

        recipe_id = candidate["recipe_id"]
        is_water = recipe_id == "flow_dependent_water_surface_material"
        if is_water:
            material_response = WATER_MATERIAL_RESPONSE_BY_RIVER[candidate["river_id"]]
        else:
            material_response = MATERIAL_RESPONSE_BY_RECIPE[recipe_id]
        candidate["material_response_parameters"] = material_response
        review_parameters = candidate["review_asset_parameters"]
        review_parameters["RoughnessFloor"] = material_response["RoughnessFloor"]
        review_parameters["RoughnessScaleValue"] = material_response["RoughnessScale"]
        atlas_sampler_parent = candidate["atlas_sampler_review_material"]
        atlas_sampler_parent["tuning_parameters"] = [
            parameter_name
            for parameter_name in atlas_sampler_parent["tuning_parameters"]
            if parameter_name not in {"EmissiveFillScale", "SpecularLevel"}
        ]
        atlas_sampler_parent["output_wiring"].pop("EmissiveColor", None)
        atlas_sampler_parent["output_wiring"].pop("Specular", None)
        if is_water:
            review_parameters["EmissiveFillScale"] = material_response["EmissiveFillScale"]
            review_parameters["SpecularLevel"] = material_response["SpecularLevel"]
            review_parameters["NormalIntensity"] = material_response["NormalIntensity"]
            candidate["expected_parameters"]["EmissiveFillScale"] = (
                "river_specific_default_lit_emissive_fill_bounded_to_preserve_mesh_light_response"
            )
            candidate["expected_parameters"]["SpecularLevel"] = (
                "river_specific_bounded_default_lit_dielectric_specular_response"
            )
            candidate["parent_preview_material"] = "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview"
            candidate["review_parent_material"] = {
                "path": "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview",
                "asset_file": "unreal/Content/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview.uasset",
                "status": "created_unreal_default_lit_water_review_parent_material_not_lifelike",
                "sampled_parameters": ["NormalAtlas"],
                "tuning_parameters": [
                    "AtlasTileOrigin",
                    "AtlasTileScale",
                    "NormalIntensity",
                    "RoughnessScale",
                    "RoughnessFloor",
                    "EmissiveFillScale",
                    "SpecularLevel",
                ],
                "output_wiring": {
                    "BaseColor": "flow-aware river-ribbon vertex color",
                    "EmissiveColor": "bounded vertex-color fill scaled per river material instance",
                    "Roughness": "bounded sum of per-river RoughnessScale and RoughnessFloor",
                    "Specular": "bounded per-river DefaultLit dielectric response",
                    "Normal": (
                        "tile-safe first-party water normal atlas blended over the procedural river-ribbon mesh normal"
                    ),
                },
            }
        else:
            review_parameters.pop("EmissiveFillScale", None)
            review_parameters.pop("SpecularLevel", None)
            candidate["expected_parameters"].pop("EmissiveFillScale", None)
            candidate["expected_parameters"].pop("SpecularLevel", None)
            candidate["review_parent_material"] = candidate["atlas_sampler_review_material"]

    candidate_manifest["generated_on"] = "2026-07-09"
    candidate_manifest["source_conditioned_material_map_manifest"] = str(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    )
    candidate_manifest["source_conditioned_material_texture_asset_root"] = str(
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    candidate_manifest["source_conditioned_material_texture_asset_status"] = (
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    candidate_manifest_path.write_text(json.dumps(candidate_manifest, indent=2) + "\n", encoding="utf-8")
    return candidate_manifest


if __name__ == "__main__":
    generate_source_conditioned_material_maps(Path(__file__).resolve().parents[3])
