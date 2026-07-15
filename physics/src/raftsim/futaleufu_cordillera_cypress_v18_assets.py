"""Build a branch-scale twig atlas from the project-owned V10 cypress sources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
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
SOURCE_ROOT = CYPRESS_ROOT / "Sources"
TEXTURE_ROOT = CYPRESS_ROOT / "Textures"
SOURCE_PATHS = {
    token: SOURCE_ROOT / f"cordillera_cypress_broad_spray_{token}_alpha_source_v10.png"
    for token in ("a", "b", "c")
}
ALBEDO_PATH = TEXTURE_ROOT / "cordillera_cypress_twig_v18_albedo_opacity.png"
NORMAL_PATH = TEXTURE_ROOT / "cordillera_cypress_twig_v18_normal.png"
PACKED_PATH = TEXTURE_ROOT / "cordillera_cypress_twig_v18_ao_roughness_subsurface.png"
MANIFEST_PATH = CYPRESS_ROOT / "futaleufu_cordillera_cypress_v18_texture_manifest.json"

ATLAS_SIZE = 2048
GRID_SIZE = 4
TILE_SIZE = ATLAS_SIZE // GRID_SIZE
GENERATED_ON = "2026-07-14"


@dataclass(frozen=True)
class TwigCrop:
    source: str
    box: tuple[int, int, int, int]
    rotation_degrees: float


TWIG_CROPS = (
    TwigCrop("a", (400, 20, 600, 330), 0.0),
    TwigCrop("a", (60, 540, 470, 780), -70.3),
    TwigCrop("a", (570, 470, 920, 730), 57.2),
    TwigCrop("a", (80, 880, 480, 1160), -62.0),
    TwigCrop("a", (560, 800, 1015, 1070), 62.9),
    TwigCrop("a", (580, 1060, 950, 1320), 64.8),
    TwigCrop("b", (580, 30, 1040, 500), 43.3),
    TwigCrop("b", (30, 580, 430, 880), -69.8),
    TwigCrop("b", (560, 500, 980, 760), 72.5),
    TwigCrop("b", (90, 880, 440, 1220), -134.0),
    TwigCrop("b", (500, 900, 780, 1280), 158.5),
    TwigCrop("c", (500, 20, 730, 350), -9.5),
    TwigCrop("c", (160, 280, 550, 650), -50.5),
    TwigCrop("c", (700, 250, 1240, 650), 59.9),
    TwigCrop("c", (230, 670, 630, 970), -59.0),
    TwigCrop("c", (650, 620, 1340, 930), 74.5),
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
            "status": "v18_isolated_review_candidate_not_production_promoted",
        }


def _fit_twig_to_tile(source: Image.Image, crop: TwigCrop) -> tuple[Image.Image, dict]:
    bicubic = getattr(getattr(Image, "Resampling", Image), "BICUBIC")
    lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    subject = source.crop(crop.box).rotate(
        crop.rotation_degrees,
        resample=bicubic,
        expand=True,
        fillcolor=(0, 0, 0, 0),
    )
    alpha_box = subject.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError(f"twig crop has no visible alpha: {crop}")
    subject = subject.crop(alpha_box)
    maximum_extent = 454
    scale = min(
        maximum_extent / subject.width,
        maximum_extent / subject.height,
        1.0,
    )
    size = (
        max(1, int(round(subject.width * scale))),
        max(1, int(round(subject.height * scale))),
    )
    subject = subject.resize(size, lanczos)
    tile = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    position = ((TILE_SIZE - subject.width) // 2, TILE_SIZE - subject.height - 22)
    tile.alpha_composite(subject, position)
    alpha = np.asarray(tile.getchannel("A"), dtype=np.uint8)
    return tile, {
        **asdict(crop),
        "normalized_size": list(subject.size),
        "tile_position": list(position),
        "nonzero_alpha_fraction": float(np.mean(alpha > 0)),
        "opaque_alpha_fraction": float(np.mean(alpha == 255)),
    }


def generate_futaleufu_cordillera_cypress_v18_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    sources: dict[str, Image.Image] = {}
    source_records = []
    for token, relative_path in SOURCE_PATHS.items():
        path = repo_root / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        source = Image.open(path).convert("RGBA")
        sources[token] = source
        source_records.append(
            {
                "id": token,
                "path": str(relative_path),
                "sha256": _sha256(path),
                "width": source.width,
                "height": source.height,
            }
        )

    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    crop_records = []
    for tile_index, crop in enumerate(TWIG_CROPS):
        tile, record = _fit_twig_to_tile(sources[crop.source], crop)
        atlas.alpha_composite(
            tile,
            ((tile_index % GRID_SIZE) * TILE_SIZE, (tile_index // GRID_SIZE) * TILE_SIZE),
        )
        crop_records.append({"tile": tile_index, **record})

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
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_textures.v18",
        "generated_on": GENERATED_ON,
        "status": "v18_branch_scale_twig_atlas_ready_for_isolated_review",
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "species": "Austrocedrus chilensis",
        "source_provenance": {
            "derivation": "fixed peripheral twig crops from three project-owned V10 alpha sources",
            "external_photo_pixels_vendored": False,
            "botanical_measurement_claimed": False,
            "sources": source_records,
        },
        "derivation": {
            "generator": str(Path(__file__).resolve().relative_to(repo_root)),
            "generator_sha256": _sha256(Path(__file__).resolve()),
            "atlas_grid": [GRID_SIZE, GRID_SIZE],
            "tile_size": TILE_SIZE,
            "whole_spray_image_tiles": False,
            "crop_records": crop_records,
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
            "twig_albedo_opacity": _map_record(
                repo_root, ALBEDO_PATH, "RGB base color A=opacity mask"
            ),
            "twig_normal": _map_record(repo_root, NORMAL_PATH, "RGB tangent-space normal"),
            "twig_ao_roughness_subsurface": _map_record(
                repo_root, PACKED_PATH, "R=AO G=roughness B=subsurface transmission"
            ),
        },
        "unreal_contract": {
            "texture_key_prefix": "Twig",
            "intended_geometry": "connected branch-scale hierarchy of small curved cards",
            "near_representation_eligible": False,
            "required_before_eligibility": [
                "isolated exact-camera palette review",
                "no visible cut boundaries or repeated whole-spray motifs",
                "60 m silhouette does not regress against curved-shell V17",
                "masked overdraw and packaged desktop/target-VR cost pass",
            ],
        },
    }
    manifest_path = repo_root / MANIFEST_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
