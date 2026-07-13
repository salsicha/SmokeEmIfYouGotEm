"""Generate project-owned Cordilleran cypress texture candidates for Futaleufu."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from raftsim.futaleufu_native_canopy_assets import (
    _derive_bark_maps,
    _derive_leaf_maps,
    _force_periodic_edges,
    _pad_leaf_rgb_for_mips,
)


CYPRESS_ROOT_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuNativeCanopy/CordilleraCypress"
)
SOURCE_ROOT_RELATIVE_PATH = CYPRESS_ROOT_RELATIVE_PATH / "Sources"
TEXTURE_ROOT_RELATIVE_PATH = CYPRESS_ROOT_RELATIVE_PATH / "Textures"
AUTHORING_MANIFEST_RELATIVE_PATH = (
    CYPRESS_ROOT_RELATIVE_PATH / "futaleufu_cordillera_cypress_authoring_manifest.json"
)
TEXTURE_MANIFEST_RELATIVE_PATH = (
    CYPRESS_ROOT_RELATIVE_PATH / "futaleufu_cordillera_cypress_texture_manifest.json"
)

BARK_SOURCE_RELATIVE_PATH = SOURCE_ROOT_RELATIVE_PATH / "cordillera_cypress_bark_source_v3.png"
SPRAY_SOURCE_RELATIVE_PATH = SOURCE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_atlas_source_v3.png"
BARK_ALBEDO_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_bark_v3_albedo.png"
BARK_NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_bark_v3_normal.png"
BARK_PACKED_RELATIVE_PATH = (
    TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_bark_v3_ao_roughness_height.png"
)
SPRAY_ALBEDO_OPACITY_RELATIVE_PATH = (
    TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v3_albedo_opacity.png"
)
SPRAY_NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v3_normal.png"
SPRAY_PACKED_RELATIVE_PATH = (
    TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v3_ao_roughness_subsurface.png"
)

OUTPUT_SIZE = 2048
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
SUPERSAMPLE = 2
GENERATOR_SEED = 18427
GENERATED_ON = "2026-07-13"


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def _periodic_noise(
    size: int,
    rng: np.random.Generator,
    term_count: int,
    maximum_frequency_x: int = 24,
    maximum_frequency_y: int = 14,
) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    x /= float(size - 1)
    y /= float(size - 1)
    result = np.zeros((size, size), dtype=np.float32)
    amplitude_sum = 0.0
    for index in range(term_count):
        frequency_x = int(rng.integers(1, maximum_frequency_x + 1))
        frequency_y = int(rng.integers(1, maximum_frequency_y + 1))
        amplitude = 1.0 / (1.0 + index * 0.31)
        phase = float(rng.uniform(0.0, math.tau))
        result += np.sin(math.tau * (frequency_x * x + frequency_y * y) + phase) * amplitude
        amplitude_sum += amplitude
    result /= max(amplitude_sum, 1.0e-6)
    return result


def _build_bark_source() -> Image.Image:
    rng = np.random.default_rng(GENERATOR_SEED)
    y, x = np.mgrid[0:OUTPUT_SIZE, 0:OUTPUT_SIZE].astype(np.float32)
    x /= float(OUTPUT_SIZE - 1)
    y /= float(OUTPUT_SIZE - 1)
    broad = _periodic_noise(OUTPUT_SIZE, rng, 18, 18, 10)
    fine = _periodic_noise(OUTPUT_SIZE, rng, 38, 72, 34)
    micro = _periodic_noise(OUTPUT_SIZE, rng, 54, 180, 90)

    fissures = np.zeros_like(x)
    for _ in range(40):
        center = float(rng.uniform(0.0, 1.0))
        width = float(rng.uniform(0.0015, 0.0065))
        wander_frequency = int(rng.integers(1, 5))
        wander = float(rng.uniform(0.001, 0.008))
        phase = float(rng.uniform(0.0, math.tau))
        centerline = center + np.sin(math.tau * wander_frequency * y + phase) * wander
        wrapped_distance = np.abs((x - centerline + 0.5) % 1.0 - 0.5)
        depth = np.exp(-np.square(wrapped_distance / width))
        interruption = 0.62 + 0.38 * np.sin(
            math.tau * int(rng.integers(1, 7)) * y + float(rng.uniform(0.0, math.tau))
        )
        fissures = np.maximum(fissures, depth * np.clip(interruption, 0.18, 1.0))

    vertical_fiber = (
        np.sin(math.tau * (31.0 * x + 0.55 * np.sin(math.tau * 3.0 * y))) * 0.55
        + np.sin(math.tau * (67.0 * x - 0.35 * np.sin(math.tau * 5.0 * y))) * 0.28
        + np.sin(math.tau * (113.0 * x + 2.0 * y)) * 0.17
    )
    relief = np.clip(
        0.54
        + broad * 0.30
        + fine * 0.15
        + micro * 0.075
        + vertical_fiber * 0.17
        - fissures * 0.62,
        0.0,
        1.0,
    )
    warm = np.clip(0.52 + broad * 0.20 - y * 0.04, 0.0, 1.0)
    base_brown = np.array([117.0, 86.0, 61.0], dtype=np.float32)
    ash_gray = np.array([126.0, 111.0, 91.0], dtype=np.float32)
    base = base_brown[None, None, :] * warm[..., None] + ash_gray[None, None, :] * (
        1.0 - warm[..., None]
    )
    rgb = base + (relief[..., None] - 0.5) * np.array([112.0, 102.0, 86.0])
    rgb -= fissures[..., None] * np.array([58.0, 53.0, 46.0])
    rgb += fine[..., None] * np.array([13.0, 15.0, 11.0])
    rgb += micro[..., None] * np.array([8.0, 9.0, 7.0])
    array = _force_periodic_edges(np.clip(rgb, 18.0, 176.0).astype(np.uint8))
    return Image.fromarray(array, "RGB")


def _point_along(start: np.ndarray, end: np.ndarray, value: float) -> np.ndarray:
    return start * (1.0 - value) + end * value


def _draw_scale_leaf(
    draw: ImageDraw.ImageDraw,
    center: np.ndarray,
    direction: np.ndarray,
    normal: np.ndarray,
    length: float,
    width: float,
    color: tuple[int, int, int, int],
) -> None:
    base = center - direction * length * 0.38
    tip = center + direction * length * 0.62
    left = center + normal * width
    right = center - normal * width
    draw.polygon(
        [tuple(base), tuple(left), tuple(tip), tuple(right)],
        fill=color,
    )


def _normalized(vector: np.ndarray) -> np.ndarray:
    return vector / max(float(np.linalg.norm(vector)), 1.0e-6)


def _draw_scale_leaf_segment(
    draw: ImageDraw.ImageDraw,
    start: np.ndarray,
    end: np.ndarray,
    tile_size: int,
    rng: np.random.Generator,
    stem_color: tuple[int, int, int, int],
    stem_width_scale: float,
) -> None:
    direction = _normalized(end - start)
    normal = np.array([-direction[1], direction[0]], dtype=np.float32)
    length = float(np.linalg.norm(end - start))
    draw.line(
        [tuple(start), tuple(end)],
        fill=stem_color,
        width=max(3, int(tile_size * stem_width_scale * 1.35)),
    )
    leaf_count = max(10, int(length / max(tile_size * 0.0075, 1.0)))
    for leaf_index in range(leaf_count):
        progress = 0.08 + leaf_index / max(1, leaf_count - 1) * 0.86
        center = _point_along(start, end, progress)
        for side in (-1.0, 0.0, 1.0):
            side_weight = side * float(rng.uniform(0.28, 0.52))
            leaf_center = center + normal * side * tile_size * float(rng.uniform(0.001, 0.0045))
            leaf_direction = _normalized(
                direction * float(rng.uniform(0.78, 0.96)) + normal * side_weight
            )
            leaf_normal = np.array([-leaf_direction[1], leaf_direction[0]], dtype=np.float32)
            light = int(rng.integers(-9, 15))
            _draw_scale_leaf(
                draw,
                leaf_center,
                leaf_direction,
                leaf_normal,
                tile_size * float(rng.uniform(0.015, 0.026)),
                tile_size * float(rng.uniform(0.0060, 0.0110)),
                (
                    int(np.clip(58 + light, 34, 86)),
                    int(np.clip(103 + light, 65, 132)),
                    int(np.clip(48 + light // 2, 29, 76)),
                    int(rng.integers(238, 256)),
                ),
            )


def _draw_spray_tile(
    canvas: Image.Image,
    tile_x: int,
    tile_y: int,
    rng: np.random.Generator,
) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    tile_size = canvas.width // ATLAS_COLUMNS
    origin = np.array([tile_x * tile_size, tile_y * tile_size], dtype=np.float32)
    inset = tile_size * 0.085
    root = origin + np.array(
        [tile_size * float(rng.uniform(0.42, 0.58)), tile_size - inset],
        dtype=np.float32,
    )
    lean = float(rng.uniform(-0.22, 0.22))
    tip = origin + np.array(
        [tile_size * (0.5 + lean), inset * float(rng.uniform(0.92, 1.25))],
        dtype=np.float32,
    )
    axis = _normalized(tip - root)
    side_axis = np.array([-axis[1], axis[0]], dtype=np.float32)

    stem_color = (
        int(rng.integers(104, 132)),
        int(rng.integers(62, 82)),
        int(rng.integers(40, 55)),
        255,
    )
    segments: list[tuple[np.ndarray, np.ndarray, float]] = [(root, tip, 0.0068)]
    pair_count = int(rng.integers(8, 12))
    for pair_index in range(pair_count):
        progress = 0.12 + pair_index / max(1, pair_count - 1) * 0.72
        branch_base = _point_along(root, tip, progress)
        for side in (-1.0, 1.0):
            if rng.random() < 0.08:
                continue
            taper = 1.0 - progress * 0.72
            length = tile_size * taper * float(rng.uniform(0.16, 0.24))
            branch_direction = _normalized(
                axis * float(rng.uniform(0.22, 0.42))
                + side_axis * side * float(rng.uniform(0.84, 1.0))
            )
            branch_end = branch_base + branch_direction * length
            segments.append((branch_base, branch_end, 0.0048 - progress * 0.0016))
            branch_normal = np.array(
                [-branch_direction[1], branch_direction[0]],
                dtype=np.float32,
            )
            secondary_count = int(rng.integers(3, 6))
            for secondary_index in range(secondary_count):
                secondary_progress = 0.20 + secondary_index / max(1, secondary_count - 1) * 0.62
                secondary_base = _point_along(branch_base, branch_end, secondary_progress)
                secondary_side = -1.0 if secondary_index % 2 == 0 else 1.0
                secondary_direction = _normalized(
                    branch_direction * float(rng.uniform(0.46, 0.68))
                    + branch_normal * secondary_side * float(rng.uniform(0.55, 0.80))
                )
                secondary_length = length * (1.0 - secondary_progress * 0.42) * float(
                    rng.uniform(0.20, 0.34)
                )
                secondary_end = secondary_base + secondary_direction * secondary_length
                segments.append(
                    (
                        secondary_base,
                        secondary_end,
                        0.0032 - progress * 0.0009,
                    )
                )
                secondary_normal = np.array(
                    [-secondary_direction[1], secondary_direction[0]],
                    dtype=np.float32,
                )
                tertiary_count = int(rng.integers(1, 3))
                for tertiary_index in range(tertiary_count):
                    tertiary_progress = 0.30 + tertiary_index / max(1, tertiary_count - 1) * 0.46
                    tertiary_base = _point_along(
                        secondary_base, secondary_end, tertiary_progress
                    )
                    tertiary_side = -1.0 if tertiary_index % 2 == 0 else 1.0
                    tertiary_direction = _normalized(
                        secondary_direction * float(rng.uniform(0.52, 0.72))
                        + secondary_normal
                        * tertiary_side
                        * float(rng.uniform(0.48, 0.72))
                    )
                    tertiary_length = secondary_length * float(rng.uniform(0.26, 0.42))
                    segments.append(
                        (
                            tertiary_base,
                            tertiary_base + tertiary_direction * tertiary_length,
                            0.0024 - progress * 0.0005,
                        )
                    )

    for segment_start, segment_end, width_scale in segments:
        _draw_scale_leaf_segment(
            draw,
            segment_start,
            segment_end,
            tile_size,
            rng,
            stem_color,
            width_scale,
        )


def _build_spray_source() -> Image.Image:
    high_size = OUTPUT_SIZE * SUPERSAMPLE
    canvas = Image.new("RGBA", (high_size, high_size), (0, 0, 0, 0))
    rng = np.random.default_rng(GENERATOR_SEED + 1)
    for tile_y in range(ATLAS_ROWS):
        for tile_x in range(ATLAS_COLUMNS):
            _draw_spray_tile(canvas, tile_x, tile_y, rng)
    return canvas.resize((OUTPUT_SIZE, OUTPUT_SIZE), _resample_filter())


def _map_record(repo_root: Path, relative_path: Path, channels: str, address: str) -> dict:
    path = repo_root / relative_path
    with Image.open(path) as image:
        width, height, mode = image.width, image.height, image.mode
    return {
        "path": str(relative_path),
        "sha256": _hash_file(path),
        "width": width,
        "height": height,
        "mode": mode,
        "channels": channels,
        "unreal_address_mode": address,
        "status": "first_party_generated_isolated_review_candidate_not_production_promoted",
    }


def generate_futaleufu_cordillera_cypress_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    source_root = repo_root / SOURCE_ROOT_RELATIVE_PATH
    texture_root = repo_root / TEXTURE_ROOT_RELATIVE_PATH
    source_root.mkdir(parents=True, exist_ok=True)
    texture_root.mkdir(parents=True, exist_ok=True)

    bark_source = _build_bark_source()
    spray_source = _build_spray_source()
    bark_source.save(repo_root / BARK_SOURCE_RELATIVE_PATH, optimize=True)
    spray_source.save(repo_root / SPRAY_SOURCE_RELATIVE_PATH, optimize=True)

    bark_normal, bark_packed = _derive_bark_maps(bark_source)
    spray_normal, spray_packed = _derive_leaf_maps(spray_source)
    spray_albedo_opacity, spray_rgb_mip_padding = _pad_leaf_rgb_for_mips(spray_source)
    outputs = {
        BARK_ALBEDO_RELATIVE_PATH: bark_source,
        BARK_NORMAL_RELATIVE_PATH: bark_normal,
        BARK_PACKED_RELATIVE_PATH: bark_packed,
        SPRAY_ALBEDO_OPACITY_RELATIVE_PATH: spray_albedo_opacity,
        SPRAY_NORMAL_RELATIVE_PATH: spray_normal,
        SPRAY_PACKED_RELATIVE_PATH: spray_packed,
    }
    for relative_path, image in outputs.items():
        image.save(repo_root / relative_path, optimize=True)

    generator_path = Path("physics/src/raftsim/futaleufu_cordillera_cypress_assets.py")
    manifest = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v3",
        "generated_on": GENERATED_ON,
        "status": "first_party_cypress_texture_candidates_ready_for_isolated_unreal_review",
        "production_promoted": False,
        "corridor_use_allowed": False,
        "species": {
            "scientific_name": "Austrocedrus chilensis",
            "common_names": ["cipres de la cordillera", "cordilleran cypress"],
            "scope": "second native canopy stratum for bounded north/east dry-slope groves",
        },
        "sources": {
            "bark": {
                "path": str(BARK_SOURCE_RELATIVE_PATH),
                "sha256": _hash_file(repo_root / BARK_SOURCE_RELATIVE_PATH),
                "generator": "deterministic project-owned Python procedural synthesis",
                "generator_path": str(generator_path),
                "generator_sha256": _hash_file(repo_root / generator_path),
                "input_images_used": False,
                "intent": "periodic rough vertically fibrous brown-to-ash bark candidate",
            },
            "scale_leaf_spray_atlas": {
                "path": str(SPRAY_SOURCE_RELATIVE_PATH),
                "sha256": _hash_file(repo_root / SPRAY_SOURCE_RELATIVE_PATH),
                "generator": "deterministic project-owned Python procedural synthesis",
                "generator_path": str(generator_path),
                "generator_sha256": _hash_file(repo_root / generator_path),
                "input_images_used": False,
                "intent": "sixteen non-overlapping flattened scale-leaf branch sprays",
            },
        },
        "procedural_parameters": {
            "seed": GENERATOR_SEED,
            "output_size_px": OUTPUT_SIZE,
            "atlas_columns": ATLAS_COLUMNS,
            "atlas_rows": ATLAS_ROWS,
            "supersample": SUPERSAMPLE,
            "source_facts": str(AUTHORING_MANIFEST_RELATIVE_PATH),
            "generated_pixels_are_botanical_measurements": False,
        },
        "maps": {
            "bark_albedo": _map_record(repo_root, BARK_ALBEDO_RELATIVE_PATH, "RGB base color", "wrap"),
            "bark_normal": _map_record(repo_root, BARK_NORMAL_RELATIVE_PATH, "RGB tangent-space normal", "wrap"),
            "bark_ao_roughness_height": _map_record(
                repo_root, BARK_PACKED_RELATIVE_PATH, "R=AO G=roughness B=height", "wrap"
            ),
            "spray_albedo_opacity": _map_record(
                repo_root,
                SPRAY_ALBEDO_OPACITY_RELATIVE_PATH,
                "RGB base color A=opacity mask",
                "clamp",
            ),
            "spray_normal": _map_record(
                repo_root, SPRAY_NORMAL_RELATIVE_PATH, "RGB tangent-space normal", "clamp"
            ),
            "spray_ao_roughness_subsurface": _map_record(
                repo_root,
                SPRAY_PACKED_RELATIVE_PATH,
                "R=AO G=roughness B=subsurface transmission",
                "clamp",
            ),
        },
        "derivation": {
            "bark": "periodic integer-frequency relief and fissure synthesis followed by wrapped map derivation",
            "spray": "supersampled project-authored branch and scale-leaf polygons with deterministic variation",
            "spray_rgb_mip_padding": spray_rgb_mip_padding,
            "spray_surface": "alpha-aware normal, AO, roughness, and subsurface estimates shared with coigue",
        },
        "unreal_contract": {
            "texture_asset_root": (
                "/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
                "CordilleraCypress/Textures"
            ),
            "bark_material": "opaque DefaultLit with periodic UVs and packed surface channels",
            "spray_material": "masked TwoSidedFoliage with alpha2 review tuning exposed only in instances",
            "atlas_layout": {
                "columns": ATLAS_COLUMNS,
                "rows": ATLAS_ROWS,
                "branch_spray_tiles": list(range(ATLAS_COLUMNS * ATLAS_ROWS)),
                "tile_bleed_inset": 0.012,
            },
            "shadow_policy": "off for initial isolated and corridor ecology review pending a V23-compatible shadow pass",
        },
        "provenance_and_fidelity_boundary": {
            "project_owned_generated_sources": True,
            "external_images_or_data_vendored": False,
            "botanical_reference_contract": str(AUTHORING_MANIFEST_RELATIVE_PATH),
            "generated_pixels_are_not_botanical_measurements": True,
            "isolated_visual_review_required": True,
            "corridor_use_before_visual_acceptance_forbidden": True,
        },
    }
    (repo_root / TEXTURE_MANIFEST_RELATIVE_PATH).write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    generate_futaleufu_cordillera_cypress_assets(Path(__file__).resolve().parents[3])
