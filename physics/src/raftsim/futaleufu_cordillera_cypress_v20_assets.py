"""Generate botanically measured flattened sprays for V20 cordilleran cypress."""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

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
    TEXTURE_ROOT / "cordillera_cypress_botanical_spray_v20_albedo_opacity.png"
)
NORMAL_PATH = TEXTURE_ROOT / "cordillera_cypress_botanical_spray_v20_normal.png"
PACKED_PATH = (
    TEXTURE_ROOT
    / "cordillera_cypress_botanical_spray_v20_ao_roughness_subsurface.png"
)
MANIFEST_PATH = CYPRESS_ROOT / "futaleufu_cordillera_cypress_v20_texture_manifest.json"

ATLAS_SIZE = 2048
GRID_SIZE = 4
TILE_SIZE = ATLAS_SIZE // GRID_SIZE
SUPERSAMPLE = 2
GENERATED_ON = "2026-07-14"

MORPHOLOGY_SOURCES = (
    {
        "authority": (
            "Sistema de Informacion de Biodiversidad, Administracion de Parques "
            "Nacionales, Argentina"
        ),
        "url": "https://sib.gob.ar/especies/austrocedrus-chilensis",
        "accessed_on": GENERATED_ON,
        "facts_used": [
            "branchlets flattened in one plane",
            "leaves opposite, scale-like, imbricate, and dimorphic",
            "lateral leaves keeled with two whitish stomatal bands, 2-5 mm long",
            "facial leaves triangular, 0.5-2 mm long",
        ],
        "pixels_or_geometry_copied": False,
    },
    {
        "authority": "The Gymnosperm Database",
        "url": "https://www.conifers.org/cu/Austrocedrus.php",
        "accessed_on": GENERATED_ON,
        "facts_used": [
            "shoots dense and flat",
            "lateral leaves longer than facial leaves and incurved at the apex",
            "facial leaves blunt with whitish bands on the lower surface",
        ],
        "pixels_or_geometry_copied": False,
    },
)


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
            "status": "v20_isolated_review_candidate_not_production_promoted",
        }


def _point_on_segment(
    start: tuple[float, float], end: tuple[float, float], amount: float
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * amount,
        start[1] + (end[1] - start[1]) * amount,
    )


def _draw_scale(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    angle: float,
    length: float,
    width: float,
    color: tuple[int, int, int, int],
    highlight: tuple[int, int, int, int],
    stomatal_band: bool,
) -> None:
    axis = (math.cos(angle), math.sin(angle))
    right = (-axis[1], axis[0])
    base = (
        center[0] - axis[0] * length * 0.46,
        center[1] - axis[1] * length * 0.46,
    )
    shoulder = (
        center[0] - axis[0] * length * 0.04,
        center[1] - axis[1] * length * 0.04,
    )
    tip = (
        center[0] + axis[0] * length * 0.54,
        center[1] + axis[1] * length * 0.54,
    )
    points = [
        base,
        (shoulder[0] + right[0] * width * 0.50, shoulder[1] + right[1] * width * 0.50),
        tip,
        (shoulder[0] - right[0] * width * 0.50, shoulder[1] - right[1] * width * 0.50),
    ]
    draw.polygon(points, fill=color)
    ridge_start = _point_on_segment(base, tip, 0.20)
    ridge_end = _point_on_segment(base, tip, 0.78)
    draw.line((ridge_start, ridge_end), fill=highlight, width=max(1, int(width * 0.12)))
    if stomatal_band and width >= 3.0:
        band_offset = width * 0.24
        band_color = (135, 154, 118, 155)
        for side in (-1.0, 1.0):
            draw.line(
                (
                    (
                        ridge_start[0] + right[0] * band_offset * side,
                        ridge_start[1] + right[1] * band_offset * side,
                    ),
                    (
                        ridge_end[0] + right[0] * band_offset * side,
                        ridge_end[1] + right[1] * band_offset * side,
                    ),
                ),
                fill=band_color,
                width=1,
            )


def _draw_scale_rows(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    pixels_per_cm: float,
    rng: random.Random,
    underside: bool,
) -> int:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_pixels = math.hypot(dx, dy)
    if length_pixels < 8.0:
        return 0
    angle = math.atan2(dy, dx)
    spacing_cm = rng.uniform(0.18, 0.26)
    node_count = max(3, int(length_pixels / (spacing_cm * pixels_per_cm)))
    for node_index in range(node_count):
        amount = (node_index + 0.32) / node_count
        center = _point_on_segment(start, end, amount)
        lateral_length_cm = rng.uniform(0.20, 0.50)
        lateral_width_cm = lateral_length_cm * rng.uniform(0.42, 0.62)
        facial_length_cm = rng.uniform(0.05, 0.20)
        facial_width_cm = facial_length_cm * rng.uniform(0.62, 0.92)
        lateral_length = lateral_length_cm * pixels_per_cm
        lateral_width = lateral_width_cm * pixels_per_cm
        facial_length = facial_length_cm * pixels_per_cm
        facial_width = facial_width_cm * pixels_per_cm
        leaf_green = rng.randint(-7, 8)
        lateral_color = (
            43 + leaf_green,
            73 + leaf_green,
            35 + leaf_green // 2,
            255,
        )
        opposite_color = (
            35 + leaf_green,
            63 + leaf_green,
            31 + leaf_green // 2,
            255,
        )
        highlight = (73 + leaf_green, 103 + leaf_green, 55 + leaf_green, 210)
        spread = rng.uniform(0.48, 0.68)
        _draw_scale(
            draw,
            center,
            angle - spread,
            lateral_length,
            lateral_width,
            opposite_color,
            highlight,
            underside,
        )
        _draw_scale(
            draw,
            center,
            angle + spread,
            lateral_length * rng.uniform(0.90, 1.06),
            lateral_width,
            lateral_color,
            highlight,
            underside,
        )
        _draw_scale(
            draw,
            center,
            angle + rng.uniform(-0.08, 0.08),
            facial_length,
            facial_width,
            (52 + leaf_green, 84 + leaf_green, 41 + leaf_green // 2, 255),
            highlight,
            False,
        )
    return node_count * 4


def _build_botanical_spray_tile(tile_index: int) -> tuple[Image.Image, dict]:
    canvas_size = TILE_SIZE * SUPERSAMPLE
    tile = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile, "RGBA")
    rng = random.Random(18427 + tile_index * 7919)
    physical_length_cm = rng.uniform(18.0, 23.0)
    pixels_per_cm = (canvas_size * 0.78) / physical_length_cm
    root = (
        canvas_size * (0.48 + rng.uniform(-0.04, 0.04)),
        canvas_size * 0.94,
    )
    tip = (
        canvas_size * (0.50 + rng.uniform(-0.08, 0.08)),
        canvas_size * 0.20,
    )
    main_angle = math.atan2(tip[1] - root[1], tip[0] - root[0])
    branch_count_per_side = 5 + tile_index % 3
    primary_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for branch_index in range(branch_count_per_side):
        amount = 0.13 + branch_index * (0.69 / max(branch_count_per_side - 1, 1))
        branch_root = _point_on_segment(root, tip, amount)
        for side in (-1.0, 1.0):
            spread_cm = rng.uniform(5.2, 8.6) * (1.0 - amount * 0.38)
            branch_length = spread_cm * pixels_per_cm
            branch_angle = main_angle + side * rng.uniform(0.62, 0.94)
            branch_tip = (
                branch_root[0] + math.cos(branch_angle) * branch_length,
                branch_root[1] + math.sin(branch_angle) * branch_length,
            )
            primary_segments.append((branch_root, branch_tip))
    terminal_segments = [
        (
            _point_on_segment(root, tip, 0.72),
            (
                tip[0] + math.cos(main_angle + side * 0.46) * pixels_per_cm * 3.8,
                tip[1] + math.sin(main_angle + side * 0.46) * pixels_per_cm * 3.8,
            ),
        )
        for side in (-1.0, 1.0)
    ]
    primary_segments.extend(terminal_segments)
    secondary_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for primary_index, (branch_root, branch_tip) in enumerate(primary_segments):
        branch_angle = math.atan2(
            branch_tip[1] - branch_root[1], branch_tip[0] - branch_root[0]
        )
        secondary_count = 3 + (primary_index + tile_index) % 2
        for secondary_index in range(secondary_count):
            amount = 0.28 + secondary_index * (0.52 / max(secondary_count - 1, 1))
            secondary_root = _point_on_segment(branch_root, branch_tip, amount)
            side = -1.0 if (secondary_index + primary_index) % 2 == 0 else 1.0
            secondary_angle = branch_angle + side * rng.uniform(0.44, 0.72)
            secondary_length = (
                rng.uniform(1.5, 3.2) * pixels_per_cm * (1.0 - amount * 0.24)
            )
            secondary_tip = (
                secondary_root[0] + math.cos(secondary_angle) * secondary_length,
                secondary_root[1] + math.sin(secondary_angle) * secondary_length,
            )
            secondary_segments.append((secondary_root, secondary_tip))
    branch_segments = primary_segments + secondary_segments

    woody_color = (72, 55, 34, 255)
    woody_light = (98, 75, 44, 210)
    draw.line((root, tip), fill=woody_color, width=max(3, int(pixels_per_cm * 0.12)))
    draw.line(
        (
            _point_on_segment(root, tip, 0.06),
            _point_on_segment(root, tip, 0.88),
        ),
        fill=woody_light,
        width=max(1, int(pixels_per_cm * 0.035)),
    )
    for branch_root, branch_tip in branch_segments:
        draw.line(
            (branch_root, branch_tip),
            fill=woody_color,
            width=max(2, int(pixels_per_cm * 0.07)),
        )

    underside = tile_index % 4 in (2, 3)
    scale_leaf_count = _draw_scale_rows(
        draw, root, tip, pixels_per_cm, rng, underside
    )
    for branch_root, branch_tip in branch_segments:
        scale_leaf_count += _draw_scale_rows(
            draw, branch_root, branch_tip, pixels_per_cm, rng, underside
        )

    lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    tile = tile.resize((TILE_SIZE, TILE_SIZE), lanczos)
    alpha = np.asarray(tile.getchannel("A"), dtype=np.uint8)
    return tile, {
        "tile": tile_index,
        "seed": 18427 + tile_index * 7919,
        "physical_spray_length_cm": round(physical_length_cm, 6),
        "primary_branch_count": len(primary_segments),
        "secondary_branch_count": len(secondary_segments),
        "branch_count": len(branch_segments),
        "scale_leaf_count": scale_leaf_count,
        "underside_stomatal_band_variant": underside,
        "nonzero_alpha_fraction": float(np.mean(alpha > 0)),
        "opaque_alpha_fraction": float(np.mean(alpha == 255)),
    }


def generate_futaleufu_cordillera_cypress_v20_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    tile_records = []
    for tile_index in range(GRID_SIZE * GRID_SIZE):
        tile, record = _build_botanical_spray_tile(tile_index)
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
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v20",
        "generated_on": GENERATED_ON,
        "status": "v20_botanical_flattened_spray_atlas_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "derivation": (
                "deterministic project-owned flattened spray raster authoring from "
                "published dimensional facts"
            ),
            "external_photo_pixels_vendored": False,
            "external_reference_pixels_derived": False,
            "external_geometry_copied": False,
            "morphology_sources": list(MORPHOLOGY_SOURCES),
        },
        "botanical_contract": {
            "branchlet_arrangement": "flattened in one plane",
            "leaf_arrangement": "opposite decussate, scale-like, and imbricate",
            "lateral_leaf_length_mm": [2.0, 5.0],
            "lateral_leaf_form": "keeled, incurved tip, paired pale stomatal bands",
            "facial_leaf_length_mm": [0.5, 2.0],
            "facial_leaf_form": "small triangular or blunt appressed scale",
            "tile_physical_spray_length_cm": [18.0, 23.0],
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "atlas_grid": [GRID_SIZE, GRID_SIZE],
            "tile_size": TILE_SIZE,
            "whole_external_spray_image_tiles": False,
            "independent_project_owned_spray_variants": 16,
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
            "botanical_spray_albedo_opacity": _map_record(
                repo_root, ALBEDO_PATH, "RGB base color A=opacity mask"
            ),
            "botanical_spray_normal": _map_record(
                repo_root, NORMAL_PATH, "RGB tangent-space normal"
            ),
            "botanical_spray_ao_roughness_subsurface": _map_record(
                repo_root,
                PACKED_PATH,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "unreal_contract": {
            "texture_key_prefix": "BotanicalSpray",
            "intended_geometry": (
                "connected flattened branch hierarchy carrying curved independent "
                "botanical spray tiles"
            ),
            "near_representation_eligible": False,
            "required_before_eligibility": [
                "isolated exact-camera 60 m, closeup, and multi-view HLOD review",
                "millimetre-scale dimorphic leaves remain legible without broad leaf cards",
                "curved spray boundaries and sixteen source variants avoid repeated planar motifs",
                "source and HLOD silhouettes do not regress against V18.2",
                "masked overdraw and packaged desktop/target-VR cost pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    generate_futaleufu_cordillera_cypress_v20_assets(Path(__file__).resolve().parents[3])
