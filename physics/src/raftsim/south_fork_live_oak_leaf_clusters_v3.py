"""Prepare dense project-owned live-oak leaf clusters for a true-woody M9 review."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.futaleufu_native_canopy_assets import (
    _derive_leaf_maps,
    _pad_leaf_rgb_for_mips,
)

SOURCE_ROOT = Path("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy")
CHROMA_SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_LeafClustersV3_Chroma.png"
ALPHA_SOURCE_PATH = SOURCE_ROOT / "T_InteriorLiveOak_LeafClustersV3.png"
ALBEDO_OPACITY_PATH = (
    SOURCE_ROOT / "T_InteriorLiveOak_LeafClustersV3_AlbedoOpacity.png"
)
NORMAL_PATH = SOURCE_ROOT / "T_InteriorLiveOak_LeafClustersV3_Normal.png"
PACKED_PATH = (
    SOURCE_ROOT / "T_InteriorLiveOak_LeafClustersV3_AORoughnessSubsurface.png"
)
MANIFEST_PATH = SOURCE_ROOT / "interior_live_oak_leaf_clusters_v3_manifest.json"

OUTPUT_SIZE = 2048
ATLAS_COLUMNS = 4
ATLAS_ROWS = 4
SOURCE_COLUMNS = 2
SOURCE_ROWS = 2
GENERATED_ON = "2026-07-29"
ASSET_STATUS = "m9_review_only_dense_leaf_clusters_v3_visual_promotion_rejected"

IMAGEGEN_PROMPT = """Use case: photorealistic-natural
Asset type: Unreal Engine masked foliage cluster atlas source texture
Primary request: Create one square texture atlas containing exactly four separate, very dense, leaf-dominant branch sprays of California interior live oak (Quercus wislizeni), designed for crossed real-time foliage cards on a true 3D trunk and branch scaffold.
Subject: Each spray must form a broad continuous evergreen mass with hundreds of overlapping, physically believable dark-green narrow-oval live-oak leaves, subtle serrated edges, small olive-green variation, and only a few thin gray-brown twigs visible inside the foliage. These are terminal leafy sprays, not miniature whole trees. No thick trunks. No flowers, berries, or acorns.
Composition/framing: Orthographic front-facing botanical asset capture arranged in an exact 2-by-2 grid. One complete spray centered in each quadrant. Every silhouette must stay fully inside its quadrant with generous clean padding and must not touch any other spray. Vary the four forms: broad horizontal, upright oval, left-sweeping fork, and compact rounded terminal cluster. Each spray should fill roughly 70 percent of its quadrant width and height. Make the foliage silhouette dense and continuous, with only small natural internal gaps; prioritize leaf mass over visible twigs.
Lighting/mood: Neutral bright overcast studio illumination, lightly baked, no dramatic highlights, no crushed shadows, no cast shadow, no contact shadow.
Scene/backdrop: Perfectly flat solid #ff00ff chroma-key background, one uniform color across the entire square with no gradient, texture, reflection, floor plane, shadow, or lighting variation.
Style/medium: High-resolution botanical reference photography; crisp leaf edges; true leaf scale; natural irregular non-repeating structure; restrained Sierra Nevada summer green.
Constraints: Square image; exactly four isolated sprays; exact 2-by-2 layout; no labels, grid lines, text, watermark, border, ground, trunk, roots, scenery, sky, insects, flowers, fruit, or cutout checkerboard. Do not use magenta anywhere in the foliage or branches. Keep all foliage fully opaque against the key.
Avoid: sparse bare twigs, twig-dominant clusters, miniature full-tree silhouettes, black foliage, crushed blacks, neon green, pale speckles, repeated clone shapes, flat painted blobs, low-poly leaves, illustration, CGI look, smeared edges, depth-of-field blur, transparency, translucent leaves."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_top_row_atlas(source: Image.Image) -> Image.Image:
    """Move the four 2x2 source quadrants into the first four 4x4 atlas tiles."""

    source = source.convert("RGBA")
    tile_size = OUTPUT_SIZE // ATLAS_COLUMNS
    source_cell_width = source.width // SOURCE_COLUMNS
    source_cell_height = source.height // SOURCE_ROWS
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    atlas = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (0, 0, 0, 0))
    for row in range(SOURCE_ROWS):
        for column in range(SOURCE_COLUMNS):
            source_box = (
                column * source_cell_width,
                row * source_cell_height,
                source.width if column == SOURCE_COLUMNS - 1 else (column + 1) * source_cell_width,
                source.height if row == SOURCE_ROWS - 1 else (row + 1) * source_cell_height,
            )
            tile = _retain_largest_alpha_component(source.crop(source_box)).resize(
                (tile_size, tile_size), resample=resampling
            )
            target_tile = row * SOURCE_COLUMNS + column
            atlas.paste(tile, (target_tile * tile_size, 0), tile)
    return atlas


def _retain_largest_alpha_component(source: Image.Image) -> Image.Image:
    """Remove small silhouettes that cross a generated atlas quadrant boundary."""

    pixels = np.asarray(source.convert("RGBA"), dtype=np.uint8).copy()
    mask = pixels[..., 3] > 8
    visited = np.zeros(mask.shape, dtype=bool)
    largest_component: list[tuple[int, int]] = []
    height, width = mask.shape
    for seed_y, seed_x in np.argwhere(mask):
        y = int(seed_y)
        x = int(seed_x)
        if visited[y, x]:
            continue
        component: list[tuple[int, int]] = []
        queue = deque([(y, x)])
        visited[y, x] = True
        while queue:
            current_y, current_x = queue.popleft()
            component.append((current_y, current_x))
            for offset_y in (-1, 0, 1):
                for offset_x in (-1, 0, 1):
                    if offset_x == 0 and offset_y == 0:
                        continue
                    next_y = current_y + offset_y
                    next_x = current_x + offset_x
                    if (
                        0 <= next_y < height
                        and 0 <= next_x < width
                        and mask[next_y, next_x]
                        and not visited[next_y, next_x]
                    ):
                        visited[next_y, next_x] = True
                        queue.append((next_y, next_x))
        if len(component) > len(largest_component):
            largest_component = component

    retained = np.zeros(mask.shape, dtype=bool)
    if largest_component:
        component_y, component_x = zip(*largest_component, strict=True)
        retained[component_y, component_x] = True
    pixels[..., 3][~retained] = 0
    return Image.fromarray(pixels, mode="RGBA")


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


def generate_south_fork_live_oak_leaf_clusters_v3(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    chroma_source_path = repo_root / CHROMA_SOURCE_PATH
    alpha_source_path = repo_root / ALPHA_SOURCE_PATH
    if not chroma_source_path.is_file():
        raise FileNotFoundError(chroma_source_path)
    if not alpha_source_path.is_file():
        raise FileNotFoundError(alpha_source_path)

    unpadded_albedo_opacity = _build_top_row_atlas(
        Image.open(alpha_source_path)
    )
    normal, packed = _derive_leaf_maps(unpadded_albedo_opacity)
    albedo_opacity, padding = _pad_leaf_rgb_for_mips(unpadded_albedo_opacity)
    for relative_path, image in (
        (ALBEDO_OPACITY_PATH, albedo_opacity),
        (NORMAL_PATH, normal),
        (PACKED_PATH, packed),
    ):
        image.save(repo_root / relative_path, optimize=True)

    alpha = np.asarray(albedo_opacity, dtype=np.uint8)[..., 3]
    tile_size = OUTPUT_SIZE // ATLAS_COLUMNS
    occupied_band = alpha[:tile_size]
    reserved_band = alpha[tile_size:]
    manifest = {
        "schema": "raftsim.unreal.south_fork_live_oak_leaf_clusters.v3",
        "generated_on": GENERATED_ON,
        "status": ASSET_STATUS,
        "production_promoted": False,
        "species": {
            "scientific_name": "Quercus wislizeni",
            "common_name": "California interior live oak",
            "fidelity_boundary": (
                "AI-generated dense terminal-spray visual study; not a "
                "surveyed individual-tree or botanical-measurement claim"
            ),
        },
        "source": {
            "chroma_path": str(CHROMA_SOURCE_PATH),
            "chroma_sha256": _sha256(chroma_source_path),
            "alpha_path": str(ALPHA_SOURCE_PATH),
            "alpha_sha256": _sha256(alpha_source_path),
            "generator": "OpenAI built-in image generation",
            "model_identifier": "not_exposed_by_builtin_surface",
            "seed": "not_exposed_by_builtin_surface",
            "referenced_images": [],
            "prompt": IMAGEGEN_PROMPT,
            "alpha_processing": {
                "tool": "imagegen skill remove_chroma_key.py",
                "auto_key": "border",
                "reported_key_color": "#fa02f9",
                "soft_matte": True,
                "transparent_threshold": 12,
                "opaque_threshold": 220,
                "despill": True,
            },
        },
        "atlas": {
            "columns": ATLAS_COLUMNS,
            "rows": ATLAS_ROWS,
            "occupied_tiles": list(range(4)),
            "reserved_transparent_tiles": list(range(4, 16)),
            "tile_bleed_inset": 0.012,
            "occupied_band_opaque_pixel_count": int(
                np.count_nonzero(occupied_band > 8)
            ),
            "reserved_band_opaque_pixel_count": int(
                np.count_nonzero(reserved_band > 8)
            ),
        },
        "maps": {
            "albedo_opacity": _map_record(
                repo_root,
                ALBEDO_OPACITY_PATH,
                "RGB base color A=opacity mask",
            ),
            "normal": _map_record(
                repo_root, NORMAL_PATH, "RGB tangent-space normal"
            ),
            "ao_roughness_subsurface": _map_record(
                repo_root,
                PACKED_PATH,
                "R=AO G=roughness B=subsurface transmission",
            ),
        },
        "derivation": {
            "layout": (
                "four 2x2 alpha-source quadrants resized independently into "
                "the top row of a 2048-square 4x4 atlas; remaining twelve "
                "tiles stay transparent"
            ),
            "surface_maps": (
                "deterministic alpha-aware normal, AO, roughness, and "
                "subsurface estimates"
            ),
            "mip_padding": padding,
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
            "authoring_flag": "RaftSimOnlyLiveOakDenseWoodyV2Review",
            "capture_flag": "RaftSimLiveOakDenseWoodyV2Review",
            "photoreal_accepted": False,
            "release_promoted": False,
            "review_evidence": (
                "docs/environment-captures/south_fork_full_reach/"
                "m9_live_oak_dense_woody_v211_review.json"
            ),
            "decision": (
                "retain the dense leaf-dominant V3 atlas as a materially "
                "stronger technical source; reject v211 visual promotion "
                "because a single repeated scaffold and four cluster shapes "
                "form dark rounded clumps rather than varied photoreal crowns"
            ),
        },
    }
    (repo_root / MANIFEST_PATH).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    generate_south_fork_live_oak_leaf_clusters_v3(Path.cwd())
