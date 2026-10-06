"""Build project-owned branch atlases for the remaining South Fork canopy profiles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from raftsim.futaleufu_native_canopy_assets import (
    _derive_leaf_maps,
    _pad_leaf_rgb_for_mips,
)
from raftsim.south_fork_live_oak_branch_atlas import (
    ASSET_STATUS,
    ATLAS_COLUMNS,
    ATLAS_ROWS,
    OUTPUT_SIZE,
    SOURCE_ROWS,
    _remove_blue_chroma,
)

SOURCE_ROOT = Path("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy")
MANIFEST_PATH = SOURCE_ROOT / "additional_canopy_branch_atlases_v1_manifest.json"
GENERATED_ON = "2026-07-29"


@dataclass(frozen=True)
class BranchAtlasProfile:
    key: str
    scientific_name: str
    common_name: str
    source_filename: str
    output_stem: str
    prompt_intent: str
    unreal_material: str
    unreal_meshes: tuple[str, ...]

    @property
    def source_path(self) -> Path:
        return SOURCE_ROOT / self.source_filename

    @property
    def albedo_opacity_path(self) -> Path:
        return SOURCE_ROOT / f"{self.output_stem}.png"

    @property
    def normal_path(self) -> Path:
        return SOURCE_ROOT / f"{self.output_stem}_Normal.png"

    @property
    def packed_path(self) -> Path:
        return SOURCE_ROOT / f"{self.output_stem}_AORoughnessSubsurface.png"


PROFILES = (
    BranchAtlasProfile(
        key="ponderosa_pine",
        scientific_name="Pinus ponderosa",
        common_name="ponderosa pine",
        source_filename="T_PonderosaPine_BranchAtlas_ChromaV1.png",
        output_stem="T_PonderosaPine_BranchAtlasV1",
        prompt_intent=(
            "twelve isolated mature Sierra Nevada ponderosa-pine branch sprays "
            "in a non-overlapping 4x3 blue-chroma atlas"
        ),
        unreal_material=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
            "M_RaftSim_SouthForkPonderosa_BranchAtlasV1"
        ),
        unreal_meshes=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
            "SM_RaftSim_SouthForkPonderosaMature_ConnectedCrownV1",
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
            "SM_RaftSim_SouthForkPonderosaIntermediate_ConnectedCrownV1",
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
            "SM_RaftSim_SouthForkPonderosaYounger_ConnectedCrownV1",
        ),
    ),
    BranchAtlasProfile(
        key="white_alder",
        scientific_name="Alnus rhombifolia",
        common_name="California white alder",
        source_filename="T_WhiteAlder_BranchAtlas_ChromaV1.png",
        output_stem="T_WhiteAlder_BranchAtlasV1",
        prompt_intent=(
            "twelve isolated California white-alder leafy branch sprays in a "
            "non-overlapping 4x3 blue-chroma atlas"
        ),
        unreal_material=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
            "M_RaftSim_SouthForkWhiteAlder_BranchAtlasV1"
        ),
        unreal_meshes=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
            "SM_RaftSim_SouthForkWhiteAlder_ConnectedCrownV2",
        ),
    ),
    BranchAtlasProfile(
        key="deerbrush",
        scientific_name="Ceanothus integerrimus",
        common_name="deerbrush",
        source_filename="T_Deerbrush_BranchAtlas_ChromaV1.png",
        output_stem="T_Deerbrush_BranchAtlasV1",
        prompt_intent=(
            "twelve isolated Sierra Nevada deerbrush twig sprays in a "
            "non-overlapping 4x3 blue-chroma atlas"
        ),
        unreal_material=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
            "M_RaftSim_SouthForkDeerbrush_BranchAtlasV1"
        ),
        unreal_meshes=(
            "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
            "SM_RaftSim_SouthForkDeerbrush_ConnectedCrownV1",
        ),
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_source_cells(source: Image.Image) -> Image.Image:
    """Preserve each generated cell when the image service changes aspect ratio."""

    source = source.convert("RGB")
    cell_size = OUTPUT_SIZE // ATLAS_COLUMNS
    normalized = Image.new(
        "RGB",
        (OUTPUT_SIZE, cell_size * SOURCE_ROWS),
        (0, 28, 250),
    )
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    for tile_y in range(SOURCE_ROWS):
        source_y0 = round(source.height * tile_y / SOURCE_ROWS)
        source_y1 = round(source.height * (tile_y + 1) / SOURCE_ROWS)
        for tile_x in range(ATLAS_COLUMNS):
            source_x0 = round(source.width * tile_x / ATLAS_COLUMNS)
            source_x1 = round(source.width * (tile_x + 1) / ATLAS_COLUMNS)
            source_cell = source.crop((source_x0, source_y0, source_x1, source_y1))
            fitted = ImageOps.contain(
                source_cell,
                (cell_size, cell_size),
                method=resampling,
            )
            target_x = tile_x * cell_size + (cell_size - fitted.width) // 2
            target_y = tile_y * cell_size + (cell_size - fitted.height) // 2
            normalized.paste(fitted, (target_x, target_y))
    return normalized


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


def _generate_profile(
    repo_root: Path, output_root: Path, profile: BranchAtlasProfile
) -> dict:
    source_path = repo_root / profile.source_path
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    normalized_source = _normalize_source_cells(Image.open(source_path))
    unpadded_albedo_opacity = _remove_blue_chroma(normalized_source)
    normal, packed = _derive_leaf_maps(unpadded_albedo_opacity)
    albedo_opacity, padding = _pad_leaf_rgb_for_mips(unpadded_albedo_opacity)
    for path, image in (
        (profile.albedo_opacity_path, albedo_opacity),
        (profile.normal_path, normal),
        (profile.packed_path, packed),
    ):
        target_path = output_root / path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(target_path, optimize=True)

    alpha = np.asarray(albedo_opacity, dtype=np.uint8)[..., 3]
    source_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS
    return {
        "key": profile.key,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "species": {
            "scientific_name": profile.scientific_name,
            "common_name": profile.common_name,
            "fidelity_boundary": (
                "visual branch-cluster study; not a surveyed individual claim"
            ),
        },
        "source": {
            "path": str(profile.source_path),
            "sha256": _sha256(source_path),
            "generator": "OpenAI built-in image generation",
            "model_identifier": "not_exposed_by_builtin_surface",
            "seed": "not_exposed_by_builtin_surface",
            "input_images_used": False,
            "prompt_intent": profile.prompt_intent,
            "source_dimensions": [
                Image.open(source_path).width,
                Image.open(source_path).height,
            ],
            "cell_normalization": (
                "independent 4x3 cell extraction and aspect-preserving fit into "
                "the top three rows of a 4x4 atlas"
            ),
        },
        "atlas": {
            "columns": ATLAS_COLUMNS,
            "rows": ATLAS_ROWS,
            "occupied_tiles": list(range(12)),
            "reserved_transparent_tiles": list(range(12, 16)),
            "tile_bleed_inset": 0.018,
            "source_band_opaque_pixel_count": int(
                np.count_nonzero(alpha[:source_height] > 8)
            ),
            "reserved_band_opaque_pixel_count": int(
                np.count_nonzero(alpha[source_height:] > 8)
            ),
        },
        "maps": {
            "albedo_opacity": _map_record(
                output_root,
                profile.albedo_opacity_path,
                "RGB base color A=opacity mask",
            ),
            "normal": _map_record(
                output_root,
                profile.normal_path,
                "RGB tangent-space normal",
            ),
            "ao_roughness_subsurface": _map_record(
                output_root,
                profile.packed_path,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "derivation": {
            "alpha": "deterministic blue-dominance matte with bounded edge cleanup",
            "despill": "cell-bounded nearest-opaque RGB propagation and blue cap",
            "surface_maps": (
                "deterministic alpha-aware normal, AO, roughness, and subsurface estimates"
            ),
            "mip_padding": padding,
        },
        "integration": {
            "milestone": "M9",
            "active_candidate": True,
            "unreal_material": profile.unreal_material,
            "unreal_meshes": list(profile.unreal_meshes),
            "core_triangles_per_mesh": 2 if profile.key == "white_alder" else 4,
            "branch_cards_per_mesh": 36 if profile.key == "white_alder" else 12,
            "branch_triangles_per_mesh": 72 if profile.key == "white_alder" else 24,
            "total_triangles_per_mesh": 74 if profile.key == "white_alder" else 28,
            "collision": "disabled",
            "photoreal_accepted": False,
            "release_promoted": False,
        },
    }


def generate_south_fork_additional_canopy_branch_atlases(
    repo_root: Path,
    output_dir: Path | None = None,
) -> dict:
    repo_root = repo_root.resolve()
    # output_dir mirrors the repo layout (tests use tmp); default stays the
    # in-place evidence-machine flow. Sources are always read from repo_root.
    output_root = output_dir.resolve() if output_dir is not None else repo_root
    profiles = {
        profile.key: _generate_profile(repo_root, output_root, profile)
        for profile in PROFILES
    }
    manifest = {
        "schema": "raftsim.unreal.south_fork_additional_canopy_branch_atlases.v1",
        "generated_on": GENERATED_ON,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "profiles": profiles,
        "authority": {
            "affects_ecology_classification": False,
            "affects_instance_placement": False,
            "affects_collision": False,
            "affects_hydraulics": False,
        },
    }
    manifest_target = output_root / MANIFEST_PATH
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
