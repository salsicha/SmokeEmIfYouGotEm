"""Prepare the second project-owned interior-live-oak branch atlas for Unreal review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.futaleufu_native_canopy_assets import (
    _derive_leaf_maps,
    _pad_leaf_rgb_for_mips,
)

SOURCE_ROOT = Path("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy")
CHROMA_SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV2_Chroma.png"
ALPHA_SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV2.png"
ALBEDO_OPACITY_PATH = (
    SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV2_AlbedoOpacity.png"
)
NORMAL_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV2_Normal.png"
PACKED_PATH = (
    SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV2_AORoughnessSubsurface.png"
)
MANIFEST_PATH = SOURCE_ROOT / "interior_live_oak_branch_atlas_v2_manifest.json"

OUTPUT_SIZE = 2048
SOURCE_ROWS = 3
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
GENERATED_ON = "2026-07-29"
ASSET_STATUS = "m9_review_only_visual_promotion_rejected"

IMAGEGEN_PROMPT = """Use case: photorealistic-natural
Asset type: Unreal Engine masked foliage branch atlas source texture
Primary request: Create one square texture atlas containing exactly 12 separate, photorealistic branch clusters of California interior live oak (Quercus wislizeni), suitable for close and mid-distance real-time game foliage cards.
Subject: Each cluster must be a naturally forked woody branch with dense but irregular evergreen live-oak leaves; dark leathery narrow-oval leaves with subtly serrated edges; mature gray-brown fissured bark; realistic twig hierarchy; restrained Sierra Nevada summer green with a few sun-aged olive leaves. No flowers, no berries, no acorns.
Composition/framing: Orthographic/front-facing botanical asset capture. Arrange the 12 clusters in a clean 4-by-3 atlas grid. Every cluster must remain completely inside its own cell, fully separated from every other cluster, with generous empty padding around all silhouettes. Mix upright, left-sweeping, right-sweeping, broad forked, and compact terminal clusters. Show each entire branch from cut stem to leaf tips. No overlap between cells.
Lighting/mood: Neutral overcast studio illumination baked as lightly as possible, no dramatic highlights, no cast shadows, no contact shadows.
Scene/backdrop: Perfectly flat solid #ff00ff chroma-key background for background removal. The background must be one uniform color with no gradients, texture, reflections, floor plane, or lighting variation.
Style/medium: High-resolution botanical reference photography, physically believable leaf scale, crisp fine twigs and leaf edges, natural non-repeating structure.
Constraints: Square image; exactly 12 clusters; subject-only atlas; no labels, grid lines, text, watermark, border, ground, trunk, roots, flowers, fruit, insects, sky, or scenery. Do not use #ff00ff or magenta anywhere in the branches. Keep all foliage opaque and fully separated from the background with crisp edges.
Avoid: illustration, CGI look, low-poly leaves, blocky leaf masses, repeated clone shapes, smeared leaf edges, depth-of-field blur, transparent or translucent leaves."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_source_atlas(source: Image.Image) -> Image.Image:
    """Fit the 4x3 keyed source into a 4x4 atlas without crossing cell borders."""

    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    occupied_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS
    fitted = source.convert("RGBA").resize(
        (OUTPUT_SIZE, occupied_height),
        resample=resampling,
    )
    atlas = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (0, 0, 0, 0))
    atlas.paste(fitted, (0, 0), fitted)
    return atlas


def _map_record(repo_root: Path, relative_path: Path, channels: str) -> dict:
    path = repo_root / relative_path
    image = Image.open(path)
    return {
        "path": str(relative_path),
        "sha256": _sha256(path),
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "channels": channels,
        "unreal_address_mode": "clamp",
        "status": ASSET_STATUS,
    }


def generate_south_fork_live_oak_branch_atlas_v2(
    repo_root: Path, output_dir: Path | None = None
) -> dict:
    repo_root = repo_root.resolve()
    # output_dir mirrors the repo layout (tests use tmp); default stays the
    # in-place evidence-machine flow. Sources are always read from repo_root.
    output_root = output_dir.resolve() if output_dir is not None else repo_root
    alpha_source_path = repo_root / ALPHA_SOURCE_PATH
    chroma_source_path = repo_root / CHROMA_SOURCE_PATH
    if not alpha_source_path.is_file():
        raise FileNotFoundError(alpha_source_path)
    if not chroma_source_path.is_file():
        raise FileNotFoundError(chroma_source_path)

    unpadded_albedo_opacity = _normalise_source_atlas(
        Image.open(alpha_source_path)
    )
    normal, packed = _derive_leaf_maps(unpadded_albedo_opacity)
    albedo_opacity, padding = _pad_leaf_rgb_for_mips(unpadded_albedo_opacity)
    for relative_path, image in (
        (ALBEDO_OPACITY_PATH, albedo_opacity),
        (NORMAL_PATH, normal),
        (PACKED_PATH, packed),
    ):
        target_path = output_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(target_path, optimize=True)

    alpha = np.asarray(albedo_opacity, dtype=np.uint8)[..., 3]
    occupied_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS
    occupied_band = alpha[:occupied_height]
    reserved_band = alpha[occupied_height:]
    manifest = {
        "schema": "raftsim.unreal.south_fork_live_oak_branch_atlas.v2",
        "generated_on": GENERATED_ON,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "species": {
            "scientific_name": "Quercus wislizeni",
            "common_name": "interior live oak",
            "fidelity_boundary": (
                "AI-generated branch-cluster visual study; not a surveyed "
                "individual-tree or botanical-measurement claim"
            ),
        },
        "source": {
            "chroma_path": str(CHROMA_SOURCE_PATH),
            "chroma_sha256": _sha256(chroma_source_path),
            "alpha_path": str(ALPHA_SOURCE_PATH),
            "alpha_sha256": _sha256(alpha_source_path),
            "generator": "OpenAI built-in image generation",
            "model_identifier": "not_exposed_by_builtin_surface",
            "seed": "not_exposed_by_builtin_surface",
            "referenced_images": [],
            "prompt": IMAGEGEN_PROMPT,
            "alpha_processing": {
                "tool": "imagegen skill remove_chroma_key.py",
                "auto_key": "border",
                "reported_key_color": "#ea03ee",
                "soft_matte": True,
                "transparent_threshold": 12,
                "opaque_threshold": 220,
                "despill": True,
            },
        },
        "atlas": {
            "columns": ATLAS_COLUMNS,
            "rows": ATLAS_ROWS,
            "occupied_tiles": list(range(12)),
            "reserved_transparent_tiles": list(range(12, 16)),
            "tile_bleed_inset": 0.018,
            "occupied_band_opaque_pixel_count": int(
                np.count_nonzero(occupied_band > 8)
            ),
            "reserved_band_opaque_pixel_count": int(
                np.count_nonzero(reserved_band > 8)
            ),
        },
        "maps": {
            "albedo_opacity": _map_record(
                output_root,
                ALBEDO_OPACITY_PATH,
                "RGB base color A=opacity mask",
            ),
            "normal": _map_record(
                output_root, NORMAL_PATH, "RGB tangent-space normal"
            ),
            "ao_roughness_subsurface": _map_record(
                output_root,
                PACKED_PATH,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "derivation": {
            "layout": (
                "4x3 alpha source resized into the occupied 2048x1536 band "
                "of a 4x4 atlas; bottom four tiles remain transparent"
            ),
            "surface_maps": (
                "deterministic alpha-aware normal, AO, roughness, and "
                "subsurface estimates"
            ),
            "mip_padding": padding,
        },
        "authority": {
            "affects_ecology_classification": False,
            "affects_instance_placement": False,
            "affects_collision": False,
            "affects_hydraulics": False,
        },
        "integration": {
            "milestone": "M9",
            "active_candidate": False,
            "review_flag": "RaftSimLiveOakBranchAtlasV2Review",
            "expanded_review_flag": (
                "RaftSimLiveOakBranchAtlasV2ExpandedReview"
            ),
            "unreal_mesh": (
                "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                "SM_RaftSim_SouthForkInteriorLiveOakAtlasV2Review_ConnectedCrownV2"
            ),
            "collision": "disabled",
            "photoreal_accepted": False,
            "release_promoted": False,
            "decision": (
                "retain source and isolated review packages as negative "
                "evidence; reject v208 as visually ineffective and v209 for "
                "pale leaf speckles, thin card silhouettes, and persistent "
                "billboard-like crown mass"
            ),
        },
    }
    manifest_target = output_root / MANIFEST_PATH
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
