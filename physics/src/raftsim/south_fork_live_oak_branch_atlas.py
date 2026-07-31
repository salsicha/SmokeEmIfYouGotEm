"""Prepare a project-owned interior-live-oak branch atlas for Unreal review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from raftsim.futaleufu_native_canopy_assets import (
    _derive_leaf_maps,
    _pad_leaf_rgb_for_mips,
)

SOURCE_ROOT = Path("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy")
SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlas_ChromaV1.png"
ALBEDO_OPACITY_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV1.png"
NORMAL_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV1_Normal.png"
PACKED_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BranchAtlasV1_AORoughnessSubsurface.png"
MANIFEST_PATH = SOURCE_ROOT / "interior_live_oak_branch_atlas_v1_manifest.json"

OUTPUT_SIZE = 2048
SOURCE_ROWS = 3
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
GENERATED_ON = "2026-07-29"
ASSET_STATUS = "active_m9_technical_fallback_photoreal_and_release_promotion_rejected"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    t = np.clip((values - edge0) / max(edge1 - edge0, 1.0e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _remove_blue_chroma(source: Image.Image) -> Image.Image:
    """Key the generated blue field without depending on a single flat key color."""

    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    source_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS
    fitted = ImageOps.fit(
        source.convert("RGB"),
        (OUTPUT_SIZE, source_height),
        method=resampling,
    )
    rgb = np.asarray(fitted, dtype=np.float32)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    # The corrective ImageGen pass intentionally uses saturated blue, but its
    # renderer introduced a low-frequency luminance gradient. Blue dominance
    # is therefore a more stable matte than distance to one sampled key value.
    blue_dominance = blue - np.maximum(red, green)
    background = _smoothstep(44.0, 122.0, blue_dominance) * _smoothstep(
        82.0, 188.0, blue
    )
    alpha = 1.0 - background
    alpha_image = Image.fromarray(
        np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8), "L"
    )
    alpha_image = (
        alpha_image.filter(ImageFilter.MedianFilter(size=3))
        .filter(ImageFilter.MinFilter(size=3))
        .filter(ImageFilter.GaussianBlur(radius=0.35))
    )
    alpha = _smoothstep(
        0.06,
        0.96,
        np.asarray(alpha_image, dtype=np.float32) / 255.0,
    )

    # Replace antialiased key RGB with the nearest opaque branch colour inside
    # the same atlas cell. Direct blue subtraction produced yellow edge texels
    # that became visible in lower mips; bounded colour propagation preserves
    # the generated leaf/bark spectrum and cannot cross a UV-cell boundary.
    keyed = rgb.copy()
    tile_height = source_height // SOURCE_ROWS
    tile_width = OUTPUT_SIZE // ATLAS_COLUMNS
    offsets = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )
    for tile_y in range(SOURCE_ROWS):
        for tile_x in range(ATLAS_COLUMNS):
            y0, y1 = tile_y * tile_height, (tile_y + 1) * tile_height
            x0, x1 = tile_x * tile_width, (tile_x + 1) * tile_width
            tile_alpha = alpha[y0:y1, x0:x1]
            tile_colors = keyed[y0:y1, x0:x1]
            known = tile_alpha >= 0.72
            propagated = tile_colors.copy()
            for _ in range(18):
                color_sum = np.zeros_like(propagated)
                neighbor_count = np.zeros(known.shape, dtype=np.float32)
                for dy, dx in offsets:
                    shifted_known = np.roll(known, shift=(dy, dx), axis=(0, 1))
                    shifted_colors = np.roll(propagated, shift=(dy, dx), axis=(0, 1))
                    if dy < 0:
                        shifted_known[dy:, :] = False
                    elif dy > 0:
                        shifted_known[:dy, :] = False
                    if dx < 0:
                        shifted_known[:, dx:] = False
                    elif dx > 0:
                        shifted_known[:, :dx] = False
                    color_sum += shifted_colors * shifted_known[..., None]
                    neighbor_count += shifted_known
                frontier = ~known & (neighbor_count > 0.0)
                if not np.any(frontier):
                    break
                propagated[frontier] = (
                    color_sum[frontier] / neighbor_count[frontier, None]
                )
                known[frontier] = True
            replace = (tile_alpha > 0.01) & (tile_alpha < 0.96) & known
            tile_colors[replace] = propagated[replace]
    keyed[..., 2] = np.minimum(
        keyed[..., 2],
        np.maximum(keyed[..., 1] * 1.10, keyed[..., 0] * 0.64),
    )
    keyed = np.clip(keyed, 0.0, 255.0).astype(np.uint8)
    keyed[alpha <= 0.01] = 0

    square = np.zeros((OUTPUT_SIZE, OUTPUT_SIZE, 4), dtype=np.uint8)
    square[:source_height, :, :3] = keyed
    square[:source_height, :, 3] = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(square, "RGBA")


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


def generate_south_fork_live_oak_branch_atlas(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    source_path = repo_root / SOURCE_PATH
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    unpadded_albedo_opacity = _remove_blue_chroma(Image.open(source_path))
    normal, packed = _derive_leaf_maps(unpadded_albedo_opacity)
    albedo_opacity, padding = _pad_leaf_rgb_for_mips(unpadded_albedo_opacity)
    for path, image in (
        (ALBEDO_OPACITY_PATH, albedo_opacity),
        (NORMAL_PATH, normal),
        (PACKED_PATH, packed),
    ):
        image.save(repo_root / path, optimize=True)

    alpha = np.asarray(albedo_opacity, dtype=np.uint8)[..., 3]
    source_band = alpha[: OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS]
    reserved_band = alpha[OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS :]
    manifest = {
        "schema": "raftsim.unreal.south_fork_live_oak_branch_atlas.v1",
        "generated_on": GENERATED_ON,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "species": {
            "scientific_name": "Quercus wislizeni",
            "common_name": "interior live oak",
            "fidelity_boundary": "visual branch-cluster study; not a surveyed individual-tree claim",
        },
        "source": {
            "path": str(SOURCE_PATH),
            "sha256": _sha256(source_path),
            "generator": "OpenAI built-in image generation",
            "model_identifier": "not_exposed_by_builtin_surface",
            "seed": "not_exposed_by_builtin_surface",
            "input_images_used_for_initial_generation": False,
            "corrective_edit_used_generated_reference": True,
            "prompt_intent": "twelve isolated interior-live-oak branch sprays in a non-overlapping 4x3 blue-chroma atlas",
        },
        "atlas": {
            "columns": ATLAS_COLUMNS,
            "rows": ATLAS_ROWS,
            "occupied_tiles": list(range(12)),
            "reserved_transparent_tiles": list(range(12, 16)),
            "tile_bleed_inset": 0.018,
            "source_band_opaque_pixel_count": int(np.count_nonzero(source_band > 8)),
            "reserved_band_opaque_pixel_count": int(
                np.count_nonzero(reserved_band > 8)
            ),
        },
        "maps": {
            "albedo_opacity": _map_record(
                repo_root, ALBEDO_OPACITY_PATH, "RGB base color A=opacity mask"
            ),
            "normal": _map_record(repo_root, NORMAL_PATH, "RGB tangent-space normal"),
            "ao_roughness_subsurface": _map_record(
                repo_root,
                PACKED_PATH,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "derivation": {
            "alpha": "deterministic blue-dominance matte with bounded edge cleanup",
            "despill": "cell-bounded nearest-opaque RGB propagation and blue cap",
            "surface_maps": "deterministic alpha-aware normal, AO, roughness, and subsurface estimates",
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
            "active_candidate": True,
            "unreal_mesh": "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOak_ConnectedCrownV2",
            "unreal_material": "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/M_RaftSim_SouthForkInteriorLiveOak_BranchAtlasV1",
            "core_triangles": 2,
            "branch_cards": 36,
            "branch_triangles": 72,
            "total_triangles": 74,
            "collision": "disabled",
            "photoreal_accepted": False,
            "release_promoted": False,
        },
    }
    (repo_root / MANIFEST_PATH).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
