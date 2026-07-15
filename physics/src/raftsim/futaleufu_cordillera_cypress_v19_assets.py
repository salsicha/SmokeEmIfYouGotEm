"""Generate project-owned scale-leaf tiles for the V19 cypress near tier."""

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


CYPRESS_ROOT = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuNativeCanopy/CordilleraCypress"
)
TEXTURE_ROOT = CYPRESS_ROOT / "Textures"
ALBEDO_PATH = TEXTURE_ROOT / "cordillera_cypress_scale_leaf_v19_albedo_opacity.png"
NORMAL_PATH = TEXTURE_ROOT / "cordillera_cypress_scale_leaf_v19_normal.png"
PACKED_PATH = (
    TEXTURE_ROOT / "cordillera_cypress_scale_leaf_v19_ao_roughness_subsurface.png"
)
MANIFEST_PATH = CYPRESS_ROOT / "futaleufu_cordillera_cypress_v19_texture_manifest.json"

ATLAS_SIZE = 2048
GRID_SIZE = 4
TILE_SIZE = ATLAS_SIZE // GRID_SIZE
GENERATED_ON = "2026-07-14"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _map_record(repo_root: Path, relative_path: Path, channels: str) -> dict:
    path = repo_root / relative_path
    with Image.open(path) as image:
        return {
            "path": str(relative_path),
            "sha256": _sha256(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "channels": channels,
            "unreal_address_mode": "clamp",
            "status": "v19_isolated_review_candidate_not_production_promoted",
        }


def _smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    amount = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return amount * amount * (3.0 - 2.0 * amount)


def _build_scale_leaf_tile(tile_index: int) -> tuple[Image.Image, dict]:
    yy, xx = np.mgrid[0:TILE_SIZE, 0:TILE_SIZE].astype(np.float32)
    x = (xx + 0.5) / TILE_SIZE
    y = (yy + 0.5) / TILE_SIZE
    seed = tile_index + 1

    bottom = 0.91 + 0.008 * np.sin(seed * 1.7)
    top = 0.075 + 0.009 * np.cos(seed * 1.3)
    progress = np.clip((bottom - y) / (bottom - top), 0.0, 1.0)
    center = 0.5 + (0.018 + 0.003 * (seed % 4)) * np.sin(
        progress * np.pi * (0.82 + 0.04 * (seed % 3)) + seed * 0.71
    )
    width_scale = 0.19 + 0.012 * ((seed * 7) % 5)
    half_width = width_scale * np.power(
        np.maximum(np.sin(np.pi * progress), 0.0), 0.72
    )
    half_width *= 1.18 - 0.40 * progress
    normalized_edge = np.abs(x - center) / np.maximum(half_width, 1.0e-4)
    horizontal_coverage = _smoothstep(1.035, 0.965, normalized_edge)
    vertical_coverage = _smoothstep(-0.006, 0.016, progress) * _smoothstep(
        1.006, 0.984, progress
    )
    alpha = horizontal_coverage * vertical_coverage

    edge_distance = np.clip(1.0 - normalized_edge, 0.0, 1.0)
    ridge = np.exp(-np.square((x - center) / np.maximum(half_width * 0.16, 0.012)))
    side_roll = np.clip((x - center) / np.maximum(half_width, 1.0e-4), -1.0, 1.0)
    mottle = (
        np.sin(xx * (0.033 + 0.001 * (seed % 3)) + seed * 2.1)
        * np.sin(yy * 0.047 - seed * 0.9)
        * 0.5
        + 0.5
    )
    light = 0.68 + 0.18 * edge_distance + 0.10 * ridge + 0.07 * progress
    light += 0.045 * mottle + 0.035 * side_roll
    base = np.array(
        [
            55.0 + 2.0 * (seed % 4),
            79.0 + 3.0 * ((seed * 3) % 5),
            35.0 + 2.0 * ((seed * 5) % 4),
        ],
        dtype=np.float32,
    )
    rgb = np.clip(base[None, None, :] * light[..., None], 0.0, 255.0)
    rgb += ridge[..., None] * np.array([5.0, 9.0, 3.0], dtype=np.float32)
    rgba = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(rgb, 0.0, 255.0).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)
    rgba[rgba[..., 3] == 0, :3] = 0
    return Image.fromarray(rgba, mode="RGBA"), {
        "tile": tile_index,
        "seed": seed,
        "width_scale": round(float(width_scale), 6),
        "curve_phase": round(float(seed * 0.71), 6),
        "nonzero_alpha_fraction": float(np.mean(rgba[..., 3] > 0)),
        "opaque_alpha_fraction": float(np.mean(rgba[..., 3] == 255)),
    }


def generate_futaleufu_cordillera_cypress_v19_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    tile_records = []
    for tile_index in range(GRID_SIZE * GRID_SIZE):
        tile, record = _build_scale_leaf_tile(tile_index)
        atlas.alpha_composite(
            tile,
            ((tile_index % GRID_SIZE) * TILE_SIZE, (tile_index // GRID_SIZE) * TILE_SIZE),
        )
        tile_records.append(record)

    padded_atlas, padding_contract = _pad_leaf_rgb_for_mips(atlas)
    normal, packed = _derive_leaf_maps(padded_atlas)
    for relative_path, image in (
        (ALBEDO_PATH, padded_atlas),
        (NORMAL_PATH, normal),
        (PACKED_PATH, packed),
    ):
        path = repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, optimize=True)

    alpha = np.asarray(padded_atlas.getchannel("A"), dtype=np.uint8)
    manifest = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v19",
        "generated_on": GENERATED_ON,
        "status": "v19_project_owned_scale_leaf_atlas_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "derivation": "deterministic project-owned scale-leaf tile authoring",
            "external_photo_pixels_vendored": False,
            "external_reference_pixels_derived": False,
            "botanical_measurement_claimed": False,
            "reference_boundary": (
                "rights-reviewed species photographs remain link-only morphology evidence"
            ),
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "atlas_grid": [GRID_SIZE, GRID_SIZE],
            "tile_size": TILE_SIZE,
            "whole_spray_image_tiles": False,
            "tile_records": tile_records,
            "mip_padding": padding_contract,
        },
        "alpha": {
            "nonzero_pixel_count": int(np.count_nonzero(alpha)),
            "nonzero_fraction": float(np.mean(alpha > 0)),
            "opaque_pixel_count": int(np.count_nonzero(alpha == 255)),
            "opaque_fraction": float(np.mean(alpha == 255)),
            "transparent_corners": all(
                alpha[y, x] == 0
                for x, y in (
                    (0, 0),
                    (ATLAS_SIZE - 1, 0),
                    (0, ATLAS_SIZE - 1),
                    (ATLAS_SIZE - 1, ATLAS_SIZE - 1),
                )
            ),
        },
        "maps": {
            "scale_leaf_albedo_opacity": _map_record(
                repo_root, ALBEDO_PATH, "RGB base color A=opacity mask"
            ),
            "scale_leaf_normal": _map_record(
                repo_root, NORMAL_PATH, "RGB tangent-space normal"
            ),
            "scale_leaf_ao_roughness_subsurface": _map_record(
                repo_root, PACKED_PATH, "R=AO G=roughness B=subsurface transmission"
            ),
        },
        "unreal_contract": {
            "texture_key_prefix": "Scale",
            "intended_geometry": (
                "connected branch-scale hierarchy carrying explicit overlapping scale-leaf cards"
            ),
            "near_representation_eligible": False,
            "required_before_eligibility": [
                "isolated exact-camera 60 m, closeup, and multi-view HLOD review",
                "no whole-spray crop boundaries or repeated broad spray motifs",
                "leaf-scale cards read as an attached imbricate shoot rather than detached planes",
                "source and HLOD silhouettes do not regress against V18.2",
                "masked overdraw and packaged desktop/target-VR cost pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
