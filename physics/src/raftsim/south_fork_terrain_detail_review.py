"""Build the versioned South Fork terrain-detail v2 review candidate.

This intentionally leaves the production-detail v1 texture set and manifests
untouched.  The resulting maps are review inputs until fixed-camera evidence,
art review, rights review, and physical-scale review all pass.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from raftsim.production_detail_textures import (
    RiverDetailSpec,
    _derive_surface_maps,
    _hash_file,
    _make_periodic_albedo,
)


GENERATED_ON = "2026-07-29"
SOURCE_RELATIVE_PATH = Path(
    "unreal/SourceArt/RaftSim/Environment/GeneratedTerrain/"
    "american_south_fork_terrain_bank_detail_source_v2.png"
)
REVIEW_ROOT_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Rendering/ReviewTerrainTextures/SouthForkDetailV2"
)
MANIFEST_RELATIVE_PATH = REVIEW_ROOT_RELATIVE_PATH / "south_fork_terrain_detail_v2_manifest.json"
ASSET_ROOT = "/Game/RaftSim/Rendering/ReviewTerrainTextures/SouthForkDetailV2/Textures"

PROMPT = """Use case: photorealistic-natural
Asset type: tileable Unreal Engine riverbank base-color source texture representing a documented 2.0 metre by 2.0 metre ground patch
Primary request: create a photorealistic, seamless straight-down surface scan of a dry-to-damp Sierra Nevada foothill riverbank beside the South Fork American River
Scene/backdrop: the entire square is continuous ground surface, edge-to-edge
Subject: compacted warm gray-brown granitic alluvium with a natural multi-scale mix of angular weathered granite chips, rounded river gravel, coarse sand, sparse pine needles, tiny fragments of dry oak leaf litter, restrained pale lichen, and a few darker damp seams; most stones 1–8 cm, occasional stones 10–18 cm, no boulders
Style/medium: physically plausible high-resolution photogrammetry-style diffuse/base-color scan, not a rendered material ball
Composition/framing: perfectly orthographic 90-degree top-down view; even density; seamless/tileable opposite edges; no central focal point; no border
Lighting/mood: flat overcast cross-polarized scan lighting with no directional shadows, no ambient occlusion baked into color, no highlights, and neutral white balance
Color palette: natural Sierra foothill granite, muted gray, warm brown, restrained olive lichen; avoid saturated green
Materials/textures: crisp centimeter-scale mineral grains, soil aggregates, gravel edge wear, needle fibers, subtle moisture color variation; realistic stochastic distribution without repeated motifs
Constraints: square texture; no perspective; no horizon; no plants growing upright; no water; no footprints; no human objects; no text; no watermark; no logos
Avoid: obvious AI repetition, circular pebble tiling, oversized rocks, smooth mud, fantasy colors, studio shadows, vignetting, depth of field, border seams, mirrored symmetry"""


SPEC = RiverDetailSpec(
    river_id="american_south_fork_detail_v2_review",
    display_name="South Fork American River terrain detail v2 review",
    asset_name="AmericanSouthForkTerrainDetailV2Review",
    source_filename=SOURCE_RELATIVE_PATH.name,
    target_read=(
        "human-scale weathered Sierra granite gravel, compacted bank soil, "
        "pine needles, restrained litter, and damp seams"
    ),
    prompt=PROMPT,
    normal_strength=2.2,
    roughness_center=206.0,
    detail_tiling=(1.0, 1.0, 0.0, 0.0),
    albedo_weight=1.0,
    normal_weight=1.0,
    surface_response_weight=1.0,
)


def _map_paths() -> dict[str, Path]:
    stem = "american_south_fork_terrain_bank_detail_v2"
    return {
        "albedo": REVIEW_ROOT_RELATIVE_PATH / f"{stem}_albedo.png",
        "normal": REVIEW_ROOT_RELATIVE_PATH / f"{stem}_normal.png",
        "ao_roughness_height": REVIEW_ROOT_RELATIVE_PATH
        / f"{stem}_ao_roughness_height.png",
    }


def generate_south_fork_terrain_detail_v2_review(repo_root: Path) -> dict:
    """Generate a deterministic, versioned review set without touching v1."""

    repo_root = repo_root.resolve()
    source_path = repo_root / SOURCE_RELATIVE_PATH
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    review_root = repo_root / REVIEW_ROOT_RELATIVE_PATH
    review_root.mkdir(parents=True, exist_ok=True)
    albedo = _make_periodic_albedo(Image.open(source_path).convert("RGB"))
    normal, packed = _derive_surface_maps(albedo, SPEC)
    relative_paths = _map_paths()
    images = {
        "albedo": albedo,
        "normal": normal,
        "ao_roughness_height": packed,
    }
    for map_id, image in images.items():
        image.save(repo_root / relative_paths[map_id], optimize=True)

    asset_suffixes = {
        "albedo": "Albedo",
        "normal": "Normal",
        "ao_roughness_height": "Packed",
    }
    maps = {}
    for map_id, relative_path in relative_paths.items():
        asset_name = f"T_RaftSim_SouthForkTerrainDetailV2Review_{asset_suffixes[map_id]}"
        maps[map_id] = {
            "path": str(relative_path),
            "sha256": _hash_file(repo_root / relative_path),
            "width": images[map_id].width,
            "height": images[map_id].height,
            "channels": (
                "RGB base color"
                if map_id == "albedo"
                else (
                    "RGB tangent-space normal"
                    if map_id == "normal"
                    else "R=AO G=roughness B=height"
                )
            ),
            "unreal_texture_asset": f"{ASSET_ROOT}/{asset_name}",
        }

    manifest = {
        "schema": "raftsim.unreal.south_fork_terrain_detail_review.v2",
        "generated_on": GENERATED_ON,
        "status": "project_owned_ai_generated_review_candidate_not_lifelike_or_accepted",
        "decision": "review_only_do_not_promote_without_visual_scale_rights_and_art_approval",
        "source": {
            "path": str(SOURCE_RELATIVE_PATH),
            "sha256": _hash_file(source_path),
            "generator": "OpenAI built-in image generation",
            "generation_mode": "built_in_image_generation_without_input_or_reference_images",
            "model_or_seed": "not_exposed_by_generation_tool",
            "prompt": PROMPT,
            "prompted_physical_width_m": 2.0,
            "source_pixel_dimensions": list(Image.open(source_path).size),
        },
        "derivation": {
            "implementation": "raftsim.production_detail_textures deterministic periodic-map functions",
            "output_size": [albedo.width, albedo.height],
            "albedo": "opposite-edge feathering, exact outer-edge matching, bounded contrast, and unsharp detail",
            "normal": "wrapped luma-gradient tangent-space normal",
            "ao_roughness_height": "wrapped local-relief response packed as R=AO G=roughness B=height",
            "seam_policy": "opposite_edge_feather_with_exact_matching_outer_edges",
        },
        "unreal_review": {
            "asset_root": ASSET_ROOT,
            "binding_scope": "transient_fixed_camera_capture_only",
            "material_parameters": {
                "GroundAlbedo": maps["albedo"]["unreal_texture_asset"],
                "GroundNormal": maps["normal"]["unreal_texture_asset"],
                "GroundPacked": maps["ao_roughness_height"]["unreal_texture_asset"],
            },
            "current_parent_world_projection_width_m": 3.2,
            "scale_mismatch": (
                "The generated source was prompted as a 2.0 m patch, while the locked production "
                "terrain parent projects Ground* at 3.2 m. This review measures the candidate under "
                "that current parent and cannot establish physical-scale acceptance."
            ),
        },
        "maps": maps,
        "policy": {
            "does_not_replace_production_v1": True,
            "does_not_drive_hydraulics_collision_or_navigation": True,
            "not_geospatial_evidence": True,
            "not_lithology_evidence": True,
            "not_photoreal_acceptance": True,
            "named_art_and_rights_review_required": True,
        },
    }
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    generate_south_fork_terrain_detail_v2_review(Path(__file__).resolve().parents[3])
