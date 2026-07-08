"""Generate source-conditioned material map candidates for photoreal river previews."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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


def _invert_mask(mask: Image.Image) -> Image.Image:
    return ImageOps.invert(mask.convert("L"))


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
    base = ImageOps.autocontrast(source_drape, cutoff=0.5)
    base = ImageEnhance.Color(base).enhance(1.08)
    base = ImageEnhance.Contrast(base).enhance(1.10)

    water_tint = Image.blend(base, Image.new("RGB", base.size, (42, 88, 82)), 0.42)
    veg_tint = Image.blend(base, Image.new("RGB", base.size, (42, 86, 42)), 0.28)
    water_edge = ImageChops.subtract(water_mask.filter(ImageFilter.MaxFilter(31)), water_mask)
    wet_bank_tint = Image.blend(base, Image.new("RGB", base.size, (42, 44, 38)), 0.30)

    result = Image.composite(veg_tint, base, _scale_mask(vegetation_mask, 0.78))
    result = Image.composite(wet_bank_tint, result, _scale_mask(water_edge, 1.25))
    result = Image.composite(water_tint, result, _scale_mask(water_mask, 0.90))
    return _apply_relief_shade(result.filter(ImageFilter.UnsharpMask(radius=1.0, percent=90, threshold=3)), relief)


def _material_zones(water_mask: Image.Image, vegetation_mask: Image.Image) -> Image.Image:
    water = water_mask.filter(ImageFilter.GaussianBlur(radius=0.6))
    vegetation = vegetation_mask.filter(ImageFilter.GaussianBlur(radius=0.6))
    wet_bank = ImageChops.subtract(water.filter(ImageFilter.MaxFilter(37)), water).filter(ImageFilter.GaussianBlur(radius=1.0))
    non_water = _invert_mask(water)
    terrain = ImageChops.lighter(_scale_mask(non_water, 0.92), _scale_mask(wet_bank, 1.25))
    vegetation_channel = ImageChops.multiply(vegetation, non_water)
    return Image.merge("RGB", (terrain, vegetation_channel, water))


def _ao_roughness_height(relief: Image.Image, water_mask: Image.Image, vegetation_mask: Image.Image) -> Image.Image:
    height = ImageOps.autocontrast(relief)
    edges = relief.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(radius=1.0))
    ao = edges.point(lambda p: max(84, min(244, int(226 - p * 0.42))))

    water = water_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    vegetation = vegetation_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    wet_bank = ImageChops.subtract(water.filter(ImageFilter.MaxFilter(33)), water)
    non_water = _invert_mask(water)

    rough_terrain = Image.new("L", relief.size, 210)
    rough_veg = Image.new("L", relief.size, 235)
    rough_water = Image.new("L", relief.size, 74)
    rough_wet_bank = Image.new("L", relief.size, 160)
    roughness = Image.composite(rough_veg, rough_terrain, _scale_mask(vegetation, 0.9))
    roughness = Image.composite(rough_wet_bank, roughness, _scale_mask(wet_bank, 1.2))
    roughness = Image.composite(rough_water, roughness, _scale_mask(water, 0.95))
    roughness = ImageChops.multiply(roughness, non_water.point(lambda p: max(220, p)))
    return Image.merge("RGB", (ao, roughness, height))


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
        "ao_roughness_height": _ao_roughness_height(relief, water, vegetation),
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
        "generated_on": "2026-07-08",
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
            "SourceConditionedZoneWeights",
            "SourceConditionedMacroAlbedoWeight",
            "SourceConditionedSurfaceResponseWeight",
        ],
        "map_semantics": {
            "macro_albedo": "Source-drape-colored material macro map with bounded water, wet-bank, vegetation, and DEM-relief shading.",
            "material_zones": "RGB material-zone weights: R=terrain/wet bank, G=vegetation away from water, B=visible water.",
            "ao_roughness_height": "Packed RGB map: R=relief-derived ambient-occlusion proxy, G=material roughness candidate, B=DEM relief height candidate.",
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
    return manifest


if __name__ == "__main__":
    generate_source_conditioned_material_maps(Path(__file__).resolve().parents[3])
