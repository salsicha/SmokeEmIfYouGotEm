"""Generate lower-cost compound branchlet atlases for V21 cordilleran cypress."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.futaleufu_cordillera_cypress_v20_assets import (
    ALBEDO_PATH as V20_ALBEDO_PATH,
    GRID_SIZE,
    MORPHOLOGY_SOURCES,
    TILE_SIZE,
    generate_futaleufu_cordillera_cypress_v20_assets,
)
from raftsim.futaleufu_native_canopy_assets import (
    _derive_leaf_maps,
    _pad_leaf_rgb_for_mips,
)


CYPRESS_ROOT = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuNativeCanopy/CordilleraCypress"
)
TEXTURE_ROOT = CYPRESS_ROOT / "Textures"
ALBEDO_PATH = (
    TEXTURE_ROOT / "cordillera_cypress_compound_branchlet_v21_albedo_opacity.png"
)
NORMAL_PATH = TEXTURE_ROOT / "cordillera_cypress_compound_branchlet_v21_normal.png"
PACKED_PATH = (
    TEXTURE_ROOT
    / "cordillera_cypress_compound_branchlet_v21_ao_roughness_subsurface.png"
)
MANIFEST_PATH = CYPRESS_ROOT / "futaleufu_cordillera_cypress_v21_texture_manifest.json"

ATLAS_SIZE = TILE_SIZE * GRID_SIZE
WORK_SIZE = TILE_SIZE * 2
GENERATED_ON = "2026-07-14"
MASK_ALPHA_0_42 = round(0.42 * 255)


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
            "status": "v21_isolated_review_candidate_not_production_promoted",
        }


def _place_spray(
    canvas: Image.Image,
    source: Image.Image,
    target_root: tuple[float, float],
    scale: float,
    rotation_degrees: float,
) -> None:
    bicubic = getattr(getattr(Image, "Resampling", Image), "BICUBIC")
    width = max(1, round(source.width * scale))
    height = max(1, round(source.height * scale))
    resized = source.resize((width, height), bicubic)
    root = (width * 0.50, height * 0.94)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    origin = (round(target_root[0] - root[0]), round(target_root[1] - root[1]))
    layer.alpha_composite(resized, origin)
    layer = layer.rotate(
        rotation_degrees,
        resample=bicubic,
        center=(round(target_root[0]), round(target_root[1])),
    )
    canvas.alpha_composite(layer)


def _build_compound_tile(
    source_tiles: list[Image.Image], tile_index: int
) -> tuple[Image.Image, dict]:
    rng = random.Random(21917 + tile_index * 6151)
    canvas = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), (0, 0, 0, 0))
    source_indices = [
        (tile_index * 5 + offset * 7 + rng.randrange(0, 3)) % len(source_tiles)
        for offset in range(6)
    ]
    placements = [
        ((0.50, 0.95), 1.58, rng.uniform(-4.0, 4.0)),
        ((0.47, 0.73), 1.22, rng.uniform(-39.0, -31.0)),
        ((0.54, 0.66), 1.18, rng.uniform(30.0, 38.0)),
        ((0.45, 0.56), 1.02, rng.uniform(-30.0, -22.0)),
        ((0.55, 0.49), 0.98, rng.uniform(21.0, 29.0)),
        (
            (0.49 + rng.uniform(-0.025, 0.025), 0.38),
            0.88,
            rng.uniform(-15.0, 15.0),
        ),
    ]
    placement_records = []
    for source_index, (root_fraction, scale, rotation) in zip(
        source_indices, placements, strict=True
    ):
        target_root = (
            root_fraction[0] * WORK_SIZE,
            root_fraction[1] * WORK_SIZE,
        )
        _place_spray(
            canvas,
            source_tiles[source_index],
            target_root,
            scale,
            rotation,
        )
        placement_records.append(
            {
                "source_tile": source_index,
                "root_fraction": [round(root_fraction[0], 6), round(root_fraction[1], 6)],
                "work_scale": round(scale, 6),
                "rotation_degrees": round(rotation, 6),
            }
        )

    lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    tile = canvas.resize((TILE_SIZE, TILE_SIZE), lanczos)
    alpha = np.asarray(tile.getchannel("A"), dtype=np.uint8)
    occupied = np.argwhere(alpha > 0)
    bounds = (
        [0, 0, 0, 0]
        if occupied.size == 0
        else [
            int(occupied[:, 1].min()),
            int(occupied[:, 0].min()),
            int(occupied[:, 1].max()),
            int(occupied[:, 0].max()),
        ]
    )
    return tile, {
        "tile": tile_index,
        "seed": 21917 + tile_index * 6151,
        "component_spray_count": 6,
        "placements": placement_records,
        "physical_branchlet_length_cm": round(rng.uniform(36.0, 44.0), 6),
        "physical_branchlet_width_cm": round(rng.uniform(27.0, 35.0), 6),
        "nonzero_alpha_fraction": float(np.mean(alpha > 0)),
        "mask_clip_0_42_fraction": float(np.mean(alpha >= MASK_ALPHA_0_42)),
        "opaque_alpha_fraction": float(np.mean(alpha == 255)),
        "occupied_pixel_bounds": bounds,
    }


def generate_futaleufu_cordillera_cypress_v21_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    v20_path = repo_root / V20_ALBEDO_PATH
    if not v20_path.is_file():
        generate_futaleufu_cordillera_cypress_v20_assets(repo_root)

    with Image.open(v20_path) as source_atlas_image:
        source_atlas = source_atlas_image.convert("RGBA")
    source_alpha = np.asarray(source_atlas.getchannel("A"), dtype=np.uint8)
    source_mask_coverage = float(np.mean(source_alpha >= MASK_ALPHA_0_42))
    source_tiles = []
    for index in range(GRID_SIZE * GRID_SIZE):
        tile = source_atlas.crop(
            (
                (index % GRID_SIZE) * TILE_SIZE,
                (index // GRID_SIZE) * TILE_SIZE,
                (index % GRID_SIZE + 1) * TILE_SIZE,
                (index // GRID_SIZE + 1) * TILE_SIZE,
            )
        )
        # V20's transparent RGB padding is for final texture mips. Clear it before
        # geometric resampling so interpolation cannot turn padded texels opaque.
        pixels = np.array(tile, dtype=np.uint8)
        pixels[pixels[:, :, 3] == 0, :3] = 0
        source_tiles.append(Image.fromarray(pixels, mode="RGBA"))

    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    tile_records = []
    for tile_index in range(GRID_SIZE * GRID_SIZE):
        tile, record = _build_compound_tile(source_tiles, tile_index)
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
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v21",
        "generated_on": GENERATED_ON,
        "status": "v21_compound_branchlet_atlas_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "derivation": (
                "deterministic project-owned composition of six independently generated "
                "V20 measured botanical sprays per branchlet tile"
            ),
            "source_texture_manifest": str(
                V20_ALBEDO_PATH.parent.parent
                / "futaleufu_cordillera_cypress_v20_texture_manifest.json"
            ),
            "external_photo_pixels_vendored": False,
            "external_reference_pixels_derived": False,
            "external_geometry_copied": False,
            "morphology_sources": list(MORPHOLOGY_SOURCES),
        },
        "representation_contract": {
            "component_sprays_per_tile": 6,
            "compound_branchlet_length_cm": [36.0, 44.0],
            "compound_branchlet_width_cm": [27.0, 35.0],
            "intended_cards_per_authored_twig": 14,
            "v20_2_cards_per_authored_twig": 27,
            "intended_card_count_reduction_fraction": 13.0 / 27.0,
            "v20_source_mask_clip_0_42_fraction": source_mask_coverage,
            "compound_mask_clip_0_42_fraction": float(
                np.mean(alpha >= MASK_ALPHA_0_42)
            ),
            "compound_per_card_mask_coverage_gain": float(
                np.mean(alpha >= MASK_ALPHA_0_42) / source_mask_coverage
            ),
            "purpose": (
                "consolidate measured foliage mass at branchlet scale before Unreal "
                "geometry, avoiding additional per-twig terminal cards"
            ),
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "atlas_grid": [GRID_SIZE, GRID_SIZE],
            "tile_size": TILE_SIZE,
            "independent_project_owned_branchlet_variants": 16,
            "tile_records": tile_records,
            "mip_padding": padding_contract,
        },
        "alpha": {
            "nonzero_pixel_count": int(np.count_nonzero(alpha)),
            "nonzero_fraction": float(np.mean(alpha > 0)),
            "mask_clip_0_42_pixel_count": int(
                np.count_nonzero(alpha >= MASK_ALPHA_0_42)
            ),
            "mask_clip_0_42_fraction": float(
                np.mean(alpha >= MASK_ALPHA_0_42)
            ),
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
            "compound_branchlet_albedo_opacity": _map_record(
                repo_root, ALBEDO_PATH, "RGB base color A=opacity mask"
            ),
            "compound_branchlet_normal": _map_record(
                repo_root, NORMAL_PATH, "RGB tangent-space normal"
            ),
            "compound_branchlet_ao_roughness_subsurface": _map_record(
                repo_root,
                PACKED_PATH,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "unreal_contract": {
            "texture_key_prefix": "CompoundBranchlet",
            "palette_mode": "compound_branchlet_atlas",
            "required_before_eligibility": [
                "fresh-material first-run shader gate",
                "closeup and exact 60 m comparison against V20.2",
                "merged raster triangle count no greater than V20.2",
                "multi-view HLOD source ratio remains bounded",
                "masked overdraw and packaged desktop/target-VR cost pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    generate_futaleufu_cordillera_cypress_v21_assets(
        Path(__file__).resolve().parents[3]
    )
