"""Prepare project-owned interior-live-oak bark maps for a true-woody M9 review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.futaleufu_native_canopy_assets import (
    _derive_bark_maps,
    _make_periodic_bark_albedo,
)

SOURCE_ROOT = Path("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy")
BARK_SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BarkV1_Source.png"
BARK_ALBEDO_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BarkV1_Albedo.png"
BARK_NORMAL_PATH = SOURCE_ROOT / "T_InteriorLiveOak_BarkV1_Normal.png"
BARK_PACKED_PATH = (
    SOURCE_ROOT / "T_InteriorLiveOak_BarkV1_AORoughnessHeight.png"
)
LEAF_MANIFEST_PATH = SOURCE_ROOT / "interior_live_oak_branch_atlas_v2_manifest.json"
MANIFEST_PATH = SOURCE_ROOT / "interior_live_oak_woody_canopy_v1_manifest.json"

OUTPUT_SIZE = 2048
GENERATED_ON = "2026-07-29"
ASSET_STATUS = "m9_review_only_woody_canopy_visual_promotion_rejected"

IMAGEGEN_PROMPT = """Use case: photorealistic-natural
Asset type: seamless tileable Unreal Engine bark albedo source texture
Primary request: Create a square, perfectly seamless, high-resolution diffuse/albedo texture of mature California interior live oak bark (Quercus wislizeni), suitable for a real-time game tree trunk and scaffold branches.
Subject: Dense gray-brown mature bark with irregular shallow-to-medium vertical fissures, broken narrow plates, restrained warm umber in recesses, subtle pale gray lichen traces, natural scale appropriate for a 40-70 cm diameter trunk. The bark should read as California interior live oak rather than pine, eucalyptus, birch, or deeply furrowed cork oak.
Composition/framing: Orthographic surface capture filling the entire square. Uniform texel density. Exact left/right and top/bottom tileability with no visible seams, dominant knots, cut ends, horizon, perspective, curvature, or directional feature that reveals repetition.
Lighting/mood: Flat neutral overcast cross-polarized material-capture lighting with almost no baked shadow or highlight; preserve real color and fine surface detail for physically based rendering.
Color palette: natural neutral gray-brown, dark muted umber fissures, restrained olive-gray lichen; no saturated color.
Materials/textures: crisp fine plate edges, pores, hairline cracks, weathered but living trunk surface; physically believable 2-4 mm microdetail and 2-8 cm plate/fissure structure.
Constraints: seamless tileable square texture; albedo only; no normal-map colors, no roughness map, no displacement visualization, no text, no labels, no watermark, no border, no objects, no leaves, no branches, no moss carpet, no insects.
Avoid: dramatic lighting, cast shadows, specular glare, wet bark, black crushed crevices, obvious repetition, concentric rings, giant knots, illustration, CGI look, procedural noise look, blurry detail, pine scales, eucalyptus peeling strips, white birch markings."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        "unreal_address_mode": "wrap",
        "status": ASSET_STATUS,
    }


def generate_south_fork_live_oak_woody_canopy_v1(
    repo_root: Path, output_dir: Path | None = None
) -> dict:
    repo_root = repo_root.resolve()
    # output_dir mirrors the repo layout (tests use tmp); default stays the
    # in-place evidence-machine flow. Sources are always read from repo_root.
    output_root = output_dir.resolve() if output_dir is not None else repo_root
    source_path = repo_root / BARK_SOURCE_PATH
    leaf_manifest_path = repo_root / LEAF_MANIFEST_PATH
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if not leaf_manifest_path.is_file():
        raise FileNotFoundError(leaf_manifest_path)

    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    source = Image.open(source_path).convert("RGB").resize(
        (OUTPUT_SIZE, OUTPUT_SIZE), resample=resampling
    )
    albedo = _make_periodic_bark_albedo(source)
    normal, packed = _derive_bark_maps(albedo)
    for relative_path, image in (
        (BARK_ALBEDO_PATH, albedo),
        (BARK_NORMAL_PATH, normal),
        (BARK_PACKED_PATH, packed),
    ):
        target_path = output_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(target_path, optimize=True)

    albedo_pixels = np.asarray(albedo, dtype=np.uint8)
    normal_pixels = np.asarray(normal, dtype=np.uint8)
    packed_pixels = np.asarray(packed, dtype=np.uint8)
    manifest = {
        "schema": "raftsim.unreal.south_fork_live_oak_woody_canopy.v1",
        "generated_on": GENERATED_ON,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "species": {
            "scientific_name": "Quercus wislizeni",
            "common_name": "California interior live oak",
            "fidelity_boundary": (
                "AI-generated bark visual study and deterministic procedural "
                "woody-form prototype; not a surveyed individual-tree or "
                "botanical-measurement claim"
            ),
        },
        "source": {
            "path": str(BARK_SOURCE_PATH),
            "sha256": _sha256(source_path),
            "generator": "OpenAI built-in image generation",
            "model_identifier": "not_exposed_by_builtin_surface",
            "seed": "not_exposed_by_builtin_surface",
            "referenced_images": [],
            "prompt": IMAGEGEN_PROMPT,
        },
        "maps": {
            "bark_albedo": _map_record(
                output_root, BARK_ALBEDO_PATH, "RGB base color"
            ),
            "bark_normal": _map_record(
                output_root, BARK_NORMAL_PATH, "RGB tangent-space normal"
            ),
            "bark_ao_roughness_height": _map_record(
                output_root,
                BARK_PACKED_PATH,
                "R=AO G=roughness B=height",
            ),
        },
        "periodic_edge_contract": {
            "albedo_left_right_exact": bool(
                np.array_equal(albedo_pixels[:, 0], albedo_pixels[:, -1])
            ),
            "albedo_top_bottom_exact": bool(
                np.array_equal(albedo_pixels[0], albedo_pixels[-1])
            ),
            "normal_left_right_exact": bool(
                np.array_equal(normal_pixels[:, 0], normal_pixels[:, -1])
            ),
            "normal_top_bottom_exact": bool(
                np.array_equal(normal_pixels[0], normal_pixels[-1])
            ),
            "packed_left_right_exact": bool(
                np.array_equal(packed_pixels[:, 0], packed_pixels[:, -1])
            ),
            "packed_top_bottom_exact": bool(
                np.array_equal(packed_pixels[0], packed_pixels[-1])
            ),
            "derivation": (
                "2048-square Lanczos normalization, opposite-edge feathering, "
                "and deterministic wrapped normal/AO/roughness/height derivation"
            ),
        },
        "leaf_source": {
            "manifest": str(LEAF_MANIFEST_PATH),
            "manifest_sha256": _sha256(leaf_manifest_path),
            "representation": (
                "reuse the project-owned V2 branch atlas on branch-aligned "
                "terminal clusters; do not reuse the rejected billboard core"
            ),
        },
        "geometry_contract": {
            "form": "open-grown mature interior live oak prototype",
            "true_woody_topology": True,
            "billboard_core": False,
            "hierarchy": [
                "tapered trunk",
                "irregular primary scaffold limbs",
                "secondary branches",
                "terminal branchlets",
                "branch-aligned crossed leaf-cluster cards",
            ],
            "collision": "disabled",
            "nanite": "disabled for masked HISM review prototype",
        },
        "authority": {
            "affects_ecology_classification": False,
            "affects_instance_placement": False,
            "affects_collision": False,
            "affects_hydraulics": False,
            "affects_navigation": False,
        },
        "integration": {
            "milestone": "M9",
            "active_candidate": False,
            "authoring_flag": "RaftSimOnlyLiveOakWoodyCanopyV1Review",
            "capture_flag": "RaftSimLiveOakWoodyCanopyV1Review",
            "photoreal_accepted": False,
            "release_promoted": False,
            "review_evidence": (
                "docs/environment-captures/south_fork_full_reach/"
                "m9_live_oak_true_woody_v210_review.json"
            ),
            "decision": (
                "retain the bark maps, true-woody topology, strict render-data "
                "authoring gate, and isolated review seam as technical "
                "infrastructure; reject v210 visual promotion because sparse "
                "dark leaf-card fragments expose repetitive geometric limbs "
                "and do not form a photoreal crown"
            ),
        },
    }
    manifest_target = output_root / MANIFEST_PATH
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    generate_south_fork_live_oak_woody_canopy_v1(Path.cwd())
