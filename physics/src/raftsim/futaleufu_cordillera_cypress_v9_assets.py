"""Build the V9 high-fidelity cordilleran-cypress branch-spray atlas."""

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
CHROMA_SOURCE_RELATIVE_PATH = (
    SOURCE_ROOT_RELATIVE_PATH / "cordillera_cypress_branch_spray_chroma_source_v9.png"
)
ALPHA_SOURCE_RELATIVE_PATH = (
    SOURCE_ROOT_RELATIVE_PATH / "cordillera_cypress_branch_spray_alpha_source_v9.png"
)
ATLAS_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v9_albedo_opacity.png"
NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v9_normal.png"
PACKED_RELATIVE_PATH = (
    TEXTURE_ROOT_RELATIVE_PATH / "cordillera_cypress_spray_v9_ao_roughness_subsurface.png"
)
MANIFEST_RELATIVE_PATH = CYPRESS_ROOT_RELATIVE_PATH / "futaleufu_cordillera_cypress_v9_texture_manifest.json"

OUTPUT_SIZE = 2048
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
GENERATOR_SEED = 90818427
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
        "status": "v9_isolated_review_candidate_not_production_promoted",
    }


def _build_variant_atlas(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    alpha_bbox = source.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise ValueError("V9 branch-spray source contains no visible pixels")
    subject = source.crop(alpha_bbox)
    rng = np.random.default_rng(GENERATOR_SEED)
    tile_size = OUTPUT_SIZE // ATLAS_COLUMNS
    atlas = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (0, 0, 0, 0))
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    bicubic = getattr(getattr(Image, "Resampling", Image), "BICUBIC")

    for tile_index in range(ATLAS_COLUMNS * ATLAS_ROWS):
        tile = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
        target_height = int(rng.integers(428, 474))
        aspect_scale = float(rng.uniform(0.92, 1.48))
        target_width = max(
            1,
            int(subject.width / subject.height * target_height * aspect_scale),
        )
        variant = subject.resize((target_width, target_height), resampling)
        rgba = np.asarray(variant, dtype=np.float32).copy()
        color_scale = np.array(
            [
                rng.uniform(0.91, 1.07),
                rng.uniform(0.92, 1.10),
                rng.uniform(0.88, 1.06),
                1.0,
            ],
            dtype=np.float32,
        )
        rgba[..., :3] = np.clip(rgba[..., :3] * color_scale[:3], 0.0, 255.0)
        variant = Image.fromarray(rgba.astype(np.uint8), "RGBA")
        if tile_index % 3 == 1:
            variant = variant.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        variant = variant.rotate(
            float(rng.uniform(-8.5, 8.5)),
            resample=bicubic,
            expand=True,
            fillcolor=(0, 0, 0, 0),
        )
        x = (tile_size - variant.width) // 2 + int(rng.integers(-24, 25))
        y = tile_size - variant.height - int(rng.integers(12, 35))
        tile.alpha_composite(variant, (x, y))
        atlas.alpha_composite(
            tile,
            ((tile_index % ATLAS_COLUMNS) * tile_size, (tile_index // ATLAS_COLUMNS) * tile_size),
        )
    return atlas


def generate_futaleufu_cordillera_cypress_v9_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    chroma_source_path = repo_root / CHROMA_SOURCE_RELATIVE_PATH
    alpha_source_path = repo_root / ALPHA_SOURCE_RELATIVE_PATH
    if not chroma_source_path.is_file() or not alpha_source_path.is_file():
        raise FileNotFoundError("V9 chroma and alpha branch-spray sources are required")

    with Image.open(alpha_source_path) as source:
        source_rgba = source.convert("RGBA")
    atlas = _build_variant_atlas(source_rgba)
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
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v9",
        "generated_on": GENERATED_ON,
        "status": "v9_high_fidelity_branch_spray_texture_candidate_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "generation_method": "OpenAI built-in image generation followed by local chroma-key removal",
            "reference_images_supplied": False,
            "external_photo_pixels_vendored": False,
            "botanical_measurement_claimed": False,
            "prompt_summary": "orthographic complete cordilleran-cypress terminal branch spray with dense scale leaves on a flat magenta key",
            "chroma_source": str(CHROMA_SOURCE_RELATIVE_PATH),
            "chroma_source_sha256": _sha256(chroma_source_path),
            "alpha_source": str(ALPHA_SOURCE_RELATIVE_PATH),
            "alpha_source_sha256": _sha256(alpha_source_path),
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "seed": GENERATOR_SEED,
            "atlas_columns": ATLAS_COLUMNS,
            "atlas_rows": ATLAS_ROWS,
            "variant_operations": [
                "aspect-preserving resize with bounded horizontal width variation",
                "bounded rotation and horizontal reflection",
                "bounded RGB variation",
                "tile-local placement with transparent padding",
            ],
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
        "review_boundary": {
            "near_representation_eligible": False,
            "required_before_eligibility": [
                "isolated closeup exceeds V8 far fallback",
                "turntable and 20 m silhouette has no card-wall or repeated-fan artifact",
                "all nine actor-root authority triplets remain overlap-free after hard near selection",
                "resource and masked-overdraw budgets pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
