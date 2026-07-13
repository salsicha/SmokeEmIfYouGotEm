"""Build the V10 independent broad-spray cypress texture set."""

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


CYPRESS_ROOT_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuNativeCanopy/CordilleraCypress"
)
SOURCE_ROOT_RELATIVE_PATH = CYPRESS_ROOT_RELATIVE_PATH / "Sources"
TEXTURE_ROOT_RELATIVE_PATH = CYPRESS_ROOT_RELATIVE_PATH / "Textures"
SOURCE_TOKENS = ("a", "b", "c")
CHROMA_SOURCE_RELATIVE_PATHS = tuple(
    SOURCE_ROOT_RELATIVE_PATH / f"cordillera_cypress_broad_spray_{token}_chroma_source_v10.png"
    for token in SOURCE_TOKENS
)
ALPHA_SOURCE_RELATIVE_PATHS = tuple(
    SOURCE_ROOT_RELATIVE_PATH / f"cordillera_cypress_broad_spray_{token}_alpha_source_v10.png"
    for token in SOURCE_TOKENS
)
ATLAS_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v10_albedo_opacity.png"
NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v10_normal.png"
PACKED_RELATIVE_PATH = (
    TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v10_ao_roughness_subsurface.png"
)
MANIFEST_RELATIVE_PATH = (
    CYPRESS_ROOT_RELATIVE_PATH / "futaleufu_cordillera_cypress_v10_texture_manifest.json"
)

OUTPUT_SIZE = 2048
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
GENERATOR_SEED = 100818427
GENERATED_ON = "2026-07-13"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _map_record(repo_root: Path, relative_path: Path, channels: str) -> dict:
    path = repo_root / relative_path
    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
    return {
        "path": str(relative_path),
        "sha256": _sha256(path),
        "width": width,
        "height": height,
        "mode": mode,
        "channels": channels,
        "unreal_address_mode": "clamp",
        "status": "v10_isolated_review_candidate_not_production_promoted",
    }


def _subject(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("V10 branch-spray source contains no visible pixels")
    return image.crop(bbox)


def _build_variant_atlas(sources: list[Image.Image]) -> tuple[Image.Image, list[dict]]:
    rng = np.random.default_rng(GENERATOR_SEED)
    tile_size = OUTPUT_SIZE // ATLAS_COLUMNS
    atlas = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (0, 0, 0, 0))
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    bicubic = getattr(getattr(Image, "Resampling", Image), "BICUBIC")
    tile_records = []

    for tile_index in range(ATLAS_COLUMNS * ATLAS_ROWS):
        source_index = tile_index % len(sources)
        subject = sources[source_index]
        target_height = int(rng.integers(398, 456))
        target_width = int(subject.width / subject.height * target_height)
        maximum_extent = 458
        extent_scale = min(
            1.0,
            maximum_extent / max(target_width, target_height),
        )
        target_width = max(1, int(target_width * extent_scale))
        target_height = max(1, int(target_height * extent_scale))
        variant = subject.resize((target_width, target_height), resampling)
        rgba = np.asarray(variant, dtype=np.float32).copy()
        color_scale = np.array(
            [rng.uniform(0.93, 1.05), rng.uniform(0.94, 1.08), rng.uniform(0.91, 1.05)],
            dtype=np.float32,
        )
        rgba[..., :3] = np.clip(rgba[..., :3] * color_scale, 0.0, 255.0)
        variant = Image.fromarray(rgba.astype(np.uint8), "RGBA")
        mirrored = tile_index % 4 == 2
        if mirrored:
            variant = variant.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        rotation_degrees = float(rng.uniform(-6.0, 6.0))
        variant = variant.rotate(
            rotation_degrees,
            resample=bicubic,
            expand=True,
            fillcolor=(0, 0, 0, 0),
        )
        tile = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
        x = (tile_size - variant.width) // 2 + int(rng.integers(-13, 14))
        y = tile_size - variant.height - int(rng.integers(16, 29))
        tile.alpha_composite(variant, (x, y))
        atlas.alpha_composite(
            tile,
            ((tile_index % ATLAS_COLUMNS) * tile_size, (tile_index // ATLAS_COLUMNS) * tile_size),
        )
        tile_records.append({
            "tile": tile_index,
            "independent_source": SOURCE_TOKENS[source_index],
            "mirrored": mirrored,
            "rotation_degrees": rotation_degrees,
            "placed_width": variant.width,
            "placed_height": variant.height,
        })
    return atlas, tile_records


def generate_futaleufu_cordillera_cypress_v10_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    source_records = []
    subjects = []
    for token, chroma_relative, alpha_relative in zip(
        SOURCE_TOKENS,
        CHROMA_SOURCE_RELATIVE_PATHS,
        ALPHA_SOURCE_RELATIVE_PATHS,
        strict=True,
    ):
        chroma_path = repo_root / chroma_relative
        alpha_path = repo_root / alpha_relative
        if not chroma_path.is_file() or not alpha_path.is_file():
            raise FileNotFoundError(f"V10 source {token} is incomplete")
        with Image.open(alpha_path) as image:
            source_rgba = image.convert("RGBA")
        alpha = np.asarray(source_rgba.getchannel("A"), dtype=np.uint8)
        subjects.append(_subject(source_rgba))
        source_records.append({
            "id": token,
            "chroma_source": str(chroma_relative),
            "chroma_source_sha256": _sha256(chroma_path),
            "alpha_source": str(alpha_relative),
            "alpha_source_sha256": _sha256(alpha_path),
            "width": source_rgba.width,
            "height": source_rgba.height,
            "nonzero_alpha_fraction": float(np.mean(alpha > 0)),
            "transparent_corners": all(
                alpha[y, x] == 0
                for x, y in (
                    (0, 0),
                    (source_rgba.width - 1, 0),
                    (0, source_rgba.height - 1),
                    (source_rgba.width - 1, source_rgba.height - 1),
                )
            ),
        })

    atlas, tile_records = _build_variant_atlas(subjects)
    padded_atlas, mip_padding = _pad_leaf_rgb_for_mips(atlas)
    normal, packed = _derive_leaf_maps(padded_atlas)
    for relative_path, image in (
        (ATLAS_RELATIVE_PATH, padded_atlas),
        (NORMAL_RELATIVE_PATH, normal),
        (PACKED_RELATIVE_PATH, packed),
    ):
        path = repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, optimize=True)

    alpha = np.asarray(padded_atlas.getchannel("A"), dtype=np.uint8)
    manifest = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v10",
        "generated_on": GENERATED_ON,
        "status": "v10_three_source_broad_spray_texture_candidate_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "generation_method": "three independent OpenAI built-in image generations followed by local chroma-key removal",
            "reference_images_supplied": False,
            "external_photo_pixels_vendored": False,
            "botanical_measurement_claimed": False,
            "source_count": len(source_records),
            "sources": source_records,
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "seed": GENERATOR_SEED,
            "atlas_columns": ATLAS_COLUMNS,
            "atlas_rows": ATLAS_ROWS,
            "tile_records": tile_records,
            "mip_padding": mip_padding,
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
                    (OUTPUT_SIZE - 1, 0),
                    (0, OUTPUT_SIZE - 1),
                    (OUTPUT_SIZE - 1, OUTPUT_SIZE - 1),
                )
            ),
        },
        "maps": {
            "spray_albedo_opacity": _map_record(
                repo_root, ATLAS_RELATIVE_PATH, "RGB base color A=opacity mask"
            ),
            "spray_normal": _map_record(
                repo_root, NORMAL_RELATIVE_PATH, "RGB tangent-space normal"
            ),
            "spray_ao_roughness_subsurface": _map_record(
                repo_root, PACKED_RELATIVE_PATH, "R=AO G=roughness B=subsurface transmission"
            ),
        },
        "unreal_contract": {
            "near_texture_keys": [
                "NearLeafAlbedoOpacity",
                "NearLeafNormal",
                "NearLeafAORoughnessSubsurface",
            ],
            "far_fallback_texture_version": "v3",
            "near_representation_eligible": False,
            "required_before_eligibility": [
                "near green-dominant coverage meets or exceeds far at 20 m",
                "closeup has no radial card tangle or dark overdraw pocket",
                "all nine actor-root authority triplets remain overlap-free",
                "masked-card and measured overdraw budgets pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
