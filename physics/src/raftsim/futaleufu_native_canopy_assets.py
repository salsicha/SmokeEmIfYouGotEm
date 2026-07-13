"""Generate first-party texture candidates for the Futaleufu native canopy."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


CANOPY_ROOT_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy"
)
SOURCE_ROOT_RELATIVE_PATH = CANOPY_ROOT_RELATIVE_PATH / "Sources"
TEXTURE_ROOT_RELATIVE_PATH = CANOPY_ROOT_RELATIVE_PATH / "Textures"
MANIFEST_RELATIVE_PATH = CANOPY_ROOT_RELATIVE_PATH / "futaleufu_native_canopy_texture_manifest.json"

BARK_SOURCE_RELATIVE_PATH = SOURCE_ROOT_RELATIVE_PATH / "coigue_bark_source_v1.png"
LEAF_CHROMA_SOURCE_RELATIVE_PATH = SOURCE_ROOT_RELATIVE_PATH / "coigue_leaf_atlas_chroma_source_v2.png"

BARK_ALBEDO_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_bark_v1_albedo.png"
BARK_NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_bark_v1_normal.png"
BARK_PACKED_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_bark_v1_ao_roughness_height.png"
LEAF_ALBEDO_OPACITY_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_leaf_atlas_v2_albedo_opacity.png"
LEAF_NORMAL_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_leaf_atlas_v2_normal.png"
LEAF_PACKED_RELATIVE_PATH = TEXTURE_ROOT_RELATIVE_PATH / "coigue_leaf_atlas_v2_ao_roughness_subsurface.png"

OUTPUT_SIZE = 2048
GENERATED_ON = "2026-07-12"
LEAF_ATLAS_COLUMNS = 4
LEAF_ATLAS_ROWS = 4
LEAF_RGB_MIP_PADDING_PIXELS = 24
LEAF_TRANSPARENT_ALPHA_THRESHOLD = 2


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def _force_periodic_edges(array: np.ndarray) -> np.ndarray:
    result = array.copy()
    result[-1, ...] = result[0, ...]
    result[:, -1, ...] = result[:, 0, ...]
    return result


def _make_periodic_bark_albedo(source: Image.Image) -> Image.Image:
    image = ImageOps.fit(source.convert("RGB"), (OUTPUT_SIZE, OUTPUT_SIZE), method=_resample_filter())
    array = np.asarray(image, dtype=np.float32).copy()
    feather = OUTPUT_SIZE // 9
    for distance in range(feather):
        normalized = distance / max(1, feather - 1)
        weight = 1.0 - normalized * normalized * (3.0 - 2.0 * normalized)
        left = array[:, distance, :].copy()
        right = array[:, -1 - distance, :].copy()
        average = (left + right) * 0.5
        array[:, distance, :] = left * (1.0 - weight) + average * weight
        array[:, -1 - distance, :] = right * (1.0 - weight) + average * weight
    for distance in range(feather):
        normalized = distance / max(1, feather - 1)
        weight = 1.0 - normalized * normalized * (3.0 - 2.0 * normalized)
        top = array[distance, :, :].copy()
        bottom = array[-1 - distance, :, :].copy()
        average = (top + bottom) * 0.5
        array[distance, :, :] = top * (1.0 - weight) + average * weight
        array[-1 - distance, :, :] = bottom * (1.0 - weight) + average * weight
    periodic = Image.fromarray(_force_periodic_edges(np.clip(array, 0.0, 255.0).astype(np.uint8)), "RGB")
    periodic = ImageEnhance.Contrast(periodic).enhance(1.06)
    periodic = periodic.filter(ImageFilter.UnsharpMask(radius=0.85, percent=55, threshold=3))
    return Image.fromarray(_force_periodic_edges(np.asarray(periodic, dtype=np.uint8)), "RGB")


def _wrapped_smooth(values: np.ndarray) -> np.ndarray:
    result = values * 0.36
    for offset, weight in ((1, 0.12), (3, 0.075), (7, 0.035)):
        result += np.roll(values, offset, axis=0) * weight
        result += np.roll(values, -offset, axis=0) * weight
        result += np.roll(values, offset, axis=1) * weight
        result += np.roll(values, -offset, axis=1) * weight
    return result


def _derive_bark_maps(albedo: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgb = np.asarray(albedo, dtype=np.float32) / 255.0
    luma = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    smooth = _wrapped_smooth(luma)
    local = np.clip(luma - smooth, -0.24, 0.24)
    height = np.clip(0.18 + smooth * 0.58 + local * 1.95, 0.0, 1.0)

    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 3.1
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 3.1
    normal = np.stack((-dx, -dy, np.ones_like(height)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1.0e-6)
    normal_rgb = _force_periodic_edges(
        np.clip((normal * 0.5 + 0.5) * 255.0, 0.0, 255.0).astype(np.uint8)
    )

    crevice = np.maximum(0.0, smooth - height)
    ao = np.clip(232.0 - crevice * 300.0 - np.abs(local) * 125.0, 76.0, 240.0)
    roughness = np.clip(218.0 + np.abs(local) * 105.0 + (0.48 - luma) * 30.0, 166.0, 244.0)
    packed = _force_periodic_edges(
        np.stack((ao, roughness, np.clip(height * 255.0, 0.0, 255.0)), axis=-1).astype(np.uint8)
    )
    return Image.fromarray(normal_rgb, "RGB"), Image.fromarray(packed, "RGB")


def _border_key(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate((rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]), axis=0)
    return np.median(border, axis=0)


def _smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    normalized = np.clip((values - edge0) / max(edge1 - edge0, 1.0e-6), 0.0, 1.0)
    return normalized * normalized * (3.0 - 2.0 * normalized)


def _remove_leaf_chroma(source: Image.Image) -> Image.Image:
    image = ImageOps.fit(source.convert("RGB"), (OUTPUT_SIZE, OUTPUT_SIZE), method=_resample_filter())
    rgb = np.asarray(image, dtype=np.float32)
    key = _border_key(rgb)
    distance = np.linalg.norm(rgb - key[None, None, :], axis=-1)
    alpha = _smoothstep(42.0, 178.0, distance)
    alpha_image = Image.fromarray(np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8), "L")
    alpha_image = (
        alpha_image.filter(ImageFilter.MedianFilter(size=3))
        .filter(ImageFilter.MinFilter(size=3))
        .filter(ImageFilter.GaussianBlur(radius=0.35))
    )
    alpha = np.asarray(alpha_image, dtype=np.float32) / 255.0
    alpha = _smoothstep(0.07, 0.96, alpha)

    # Remove magenta spill only near partially transparent silhouettes.
    safe_alpha = np.maximum(alpha, 0.08)[..., None]
    unmixed = np.clip(
        (rgb - (1.0 - alpha)[..., None] * key[None, None, :]) / safe_alpha,
        0.0,
        255.0,
    )
    unmix_weight = np.clip((1.0 - alpha) * 0.58, 0.0, 0.58)[..., None]
    keyed = rgb * (1.0 - unmix_weight) + unmixed * unmix_weight
    magenta_excess = np.maximum(np.minimum(keyed[..., 0], keyed[..., 2]) - keyed[..., 1] * 1.04, 0.0)
    correction = magenta_excess * (0.72 + np.clip(1.0 - alpha, 0.0, 1.0) * 0.28)
    keyed[..., 0] -= correction * 0.72
    keyed[..., 2] -= correction
    # Chroma spill can remain opaque on fine twigs. Bound blue against the
    # retained green/red channels without suppressing natural brown bark.
    keyed[..., 2] = np.minimum(keyed[..., 2], np.maximum(keyed[..., 1] * 1.12, keyed[..., 0] * 0.58))
    keyed = np.clip(keyed, 0.0, 255.0).astype(np.uint8)
    rgba = np.dstack((keyed, np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)))
    rgba[rgba[..., 3] <= 2, :3] = 0
    return Image.fromarray(rgba, "RGBA")


def _pad_leaf_rgb_for_mips(albedo_opacity: Image.Image) -> tuple[Image.Image, dict]:
    rgba = np.asarray(albedo_opacity.convert("RGBA"), dtype=np.uint8).copy()
    original = rgba.copy()
    tile_height = rgba.shape[0] // LEAF_ATLAS_ROWS
    tile_width = rgba.shape[1] // LEAF_ATLAS_COLUMNS
    if tile_height * LEAF_ATLAS_ROWS != rgba.shape[0] or tile_width * LEAF_ATLAS_COLUMNS != rgba.shape[1]:
        raise ValueError("leaf atlas dimensions must divide evenly into the configured tile grid")

    padded_pixel_count = 0
    offsets = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )
    for tile_y in range(LEAF_ATLAS_ROWS):
        for tile_x in range(LEAF_ATLAS_COLUMNS):
            y0 = tile_y * tile_height
            y1 = y0 + tile_height
            x0 = tile_x * tile_width
            x1 = x0 + tile_width
            tile = rgba[y0:y1, x0:x1]
            colors = tile[..., :3].astype(np.float32)
            known = tile[..., 3] > LEAF_TRANSPARENT_ALPHA_THRESHOLD
            original_known = known.copy()

            for _ in range(LEAF_RGB_MIP_PADDING_PIXELS):
                color_sum = np.zeros_like(colors)
                neighbor_count = np.zeros(known.shape, dtype=np.float32)
                for dy, dx in offsets:
                    shifted_known = np.roll(known, shift=(dy, dx), axis=(0, 1))
                    shifted_colors = np.roll(colors, shift=(dy, dx), axis=(0, 1))
                    if dy < 0:
                        shifted_known[dy:, :] = False
                    elif dy > 0:
                        shifted_known[:dy, :] = False
                    if dx < 0:
                        shifted_known[:, dx:] = False
                    elif dx > 0:
                        shifted_known[:, :dx] = False
                    color_sum += shifted_colors * shifted_known[..., None]
                    neighbor_count += shifted_known
                frontier = ~known & (neighbor_count > 0.0)
                if not np.any(frontier):
                    break
                colors[frontier] = color_sum[frontier] / neighbor_count[frontier, None]
                known[frontier] = True

            padded = known & ~original_known
            tile[..., :3][padded] = np.clip(colors[padded], 0.0, 255.0).astype(np.uint8)
            padded_pixel_count += int(np.count_nonzero(padded))

    if not np.array_equal(rgba[..., 3], original[..., 3]):
        raise RuntimeError("leaf RGB mip padding changed the opacity channel")
    opaque = original[..., 3] > LEAF_TRANSPARENT_ALPHA_THRESHOLD
    if not np.array_equal(rgba[..., :3][opaque], original[..., :3][opaque]):
        raise RuntimeError("leaf RGB mip padding changed nontransparent source color")

    transparent = rgba[..., 3] <= LEAF_TRANSPARENT_ALPHA_THRESHOLD
    padded_nonzero = np.any(rgba[..., :3] != 0, axis=-1) & transparent
    contract = {
        "method": "eight-neighbor frontier propagation bounded independently to each atlas tile",
        "padding_pixels": LEAF_RGB_MIP_PADDING_PIXELS,
        "alpha_threshold_255": LEAF_TRANSPARENT_ALPHA_THRESHOLD,
        "atlas_columns": LEAF_ATLAS_COLUMNS,
        "atlas_rows": LEAF_ATLAS_ROWS,
        "tile_boundary_crossing_allowed": False,
        "alpha_preserved_byte_for_byte": True,
        "nontransparent_rgb_preserved_byte_for_byte": True,
        "alpha_sha256": _hash_array(rgba[..., 3]),
        "nontransparent_rgb_sha256": _hash_array(rgba[..., :3][opaque]),
        "padded_transparent_pixel_count": padded_pixel_count,
        "transparent_nonzero_rgb_pixel_count": int(np.count_nonzero(padded_nonzero)),
    }
    return Image.fromarray(rgba, "RGBA"), contract


def _derive_leaf_maps(albedo_opacity: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgba = np.asarray(albedo_opacity, dtype=np.float32) / 255.0
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    luma = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722

    weighted = Image.fromarray(np.clip(luma * alpha * 255.0, 0.0, 255.0).astype(np.uint8), "L")
    smooth = np.asarray(weighted.filter(ImageFilter.GaussianBlur(radius=1.15)), dtype=np.float32) / 255.0
    height = np.clip(0.42 + (smooth - 0.22) * 0.48, 0.28, 0.72)
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 1.7
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 1.7
    normal = np.stack((-dx, -dy, np.ones_like(height)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1.0e-6)
    normal_rgb = np.clip((normal * 0.5 + 0.5) * 255.0, 0.0, 255.0).astype(np.uint8)
    normal_rgb[alpha <= 0.01] = (128, 128, 255)

    local = np.abs(luma - smooth)
    ao = np.clip(226.0 - local * 120.0 - (1.0 - luma) * 24.0, 142.0, 238.0)
    roughness = np.clip(184.0 + local * 115.0 + (0.42 - luma) * 28.0, 146.0, 226.0)
    subsurface = np.clip(138.0 + luma * 92.0, 132.0, 218.0)
    packed = np.stack((ao, roughness, subsurface), axis=-1).astype(np.uint8)
    packed[alpha <= 0.01] = (255, 255, 0)
    return Image.fromarray(normal_rgb, "RGB"), Image.fromarray(packed, "RGB")


def _map_record(repo_root: Path, relative_path: Path, channels: str, address: str) -> dict:
    image = Image.open(repo_root / relative_path)
    return {
        "path": str(relative_path),
        "sha256": _hash_file(repo_root / relative_path),
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "channels": channels,
        "unreal_address_mode": address,
        "status": "first_party_generated_isolated_review_candidate_not_production_promoted",
    }


def generate_futaleufu_native_canopy_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    bark_source_path = repo_root / BARK_SOURCE_RELATIVE_PATH
    leaf_source_path = repo_root / LEAF_CHROMA_SOURCE_RELATIVE_PATH
    if not bark_source_path.exists():
        raise FileNotFoundError(bark_source_path)
    if not leaf_source_path.exists():
        raise FileNotFoundError(leaf_source_path)

    output_root = repo_root / TEXTURE_ROOT_RELATIVE_PATH
    output_root.mkdir(parents=True, exist_ok=True)
    bark_albedo = _make_periodic_bark_albedo(Image.open(bark_source_path))
    bark_normal, bark_packed = _derive_bark_maps(bark_albedo)
    unpadded_leaf_albedo_opacity = _remove_leaf_chroma(Image.open(leaf_source_path))
    leaf_normal, leaf_packed = _derive_leaf_maps(unpadded_leaf_albedo_opacity)
    leaf_albedo_opacity, leaf_rgb_mip_padding = _pad_leaf_rgb_for_mips(
        unpadded_leaf_albedo_opacity
    )

    outputs = {
        BARK_ALBEDO_RELATIVE_PATH: bark_albedo,
        BARK_NORMAL_RELATIVE_PATH: bark_normal,
        BARK_PACKED_RELATIVE_PATH: bark_packed,
        LEAF_ALBEDO_OPACITY_RELATIVE_PATH: leaf_albedo_opacity,
        LEAF_NORMAL_RELATIVE_PATH: leaf_normal,
        LEAF_PACKED_RELATIVE_PATH: leaf_packed,
    }
    for relative_path, image in outputs.items():
        image.save(repo_root / relative_path, optimize=True)

    manifest = {
        "schema": "raftsim.unreal.futaleufu_native_canopy_textures.v3",
        "generated_on": GENERATED_ON,
        "status": "first_party_coigue_texture_candidates_ready_for_isolated_unreal_review",
        "production_promoted": False,
        "species": {
            "scientific_name": "Nothofagus dombeyi",
            "common_names": ["coigue", "coihue"],
            "scope": "first prototype species for the low-valley evergreen canopy band",
        },
        "sources": {
            "bark": {
                "path": str(BARK_SOURCE_RELATIVE_PATH),
                "sha256": _hash_file(bark_source_path),
                "generator": "OpenAI built-in image generation",
                "input_images_used": False,
                "prompt_intent": "dark gray mature coigue bark with fine vertical fissures under diffuse scan lighting",
            },
            "leaf_atlas_chroma": {
                "path": str(LEAF_CHROMA_SOURCE_RELATIVE_PATH),
                "sha256": _hash_file(leaf_source_path),
                "generator": "OpenAI built-in image generation",
                "input_images_used": True,
                "reference_image": str(SOURCE_ROOT_RELATIVE_PATH / "coigue_leaf_atlas_chroma_source_v1.png"),
                "reference_role": "botanical and material study only; the v1 branch-spray layout was not retained",
                "prompt_intent": (
                    "twelve isolated coigue leaf studies and four tiny three-to-five-leaf twigs arranged as a "
                    "non-overlapping 4x4 chroma atlas"
                ),
            },
        },
        "maps": {
            "bark_albedo": _map_record(repo_root, BARK_ALBEDO_RELATIVE_PATH, "RGB base color", "wrap"),
            "bark_normal": _map_record(repo_root, BARK_NORMAL_RELATIVE_PATH, "RGB tangent-space normal", "wrap"),
            "bark_ao_roughness_height": _map_record(
                repo_root, BARK_PACKED_RELATIVE_PATH, "R=AO G=roughness B=height", "wrap"
            ),
            "leaf_albedo_opacity": _map_record(
                repo_root, LEAF_ALBEDO_OPACITY_RELATIVE_PATH, "RGB base color A=opacity mask", "clamp"
            ),
            "leaf_normal": _map_record(repo_root, LEAF_NORMAL_RELATIVE_PATH, "RGB tangent-space normal", "clamp"),
            "leaf_ao_roughness_subsurface": _map_record(
                repo_root, LEAF_PACKED_RELATIVE_PATH, "R=AO G=roughness B=subsurface transmission", "clamp"
            ),
        },
        "derivation": {
            "bark": "periodic opposite-edge feathering followed by deterministic wrapped relief derivation",
            "leaf_alpha": "deterministic border-key chroma distance matte with soft edge cleanup and bounded despill",
            "leaf_rgb_mip_padding": leaf_rgb_mip_padding,
            "leaf_surface": "deterministic alpha-aware normal, AO, roughness, and subsurface estimates",
        },
        "unreal_contract": {
            "texture_asset_root": "/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Textures",
            "bark_material": "opaque DefaultLit; periodic UVs; packed surface channels",
            "leaf_material": "masked TwoSidedFoliage; opacity from alpha; packed subsurface response",
            "leaf_atlas_layout": {
                "columns": LEAF_ATLAS_COLUMNS,
                "rows": LEAF_ATLAS_ROWS,
                "single_leaf_tiles": list(range(12)),
                "tiny_twig_tiles": list(range(12, 16)),
                "tile_bleed_inset": 0.012,
            },
            "nanite": (
                "enable PreserveArea on reviewed trunk geometry; retain full non-Nanite source geometry for "
                "masked leaf microcards because the isolated UE 5.8 comparison proved PreserveArea expands "
                "them into opaque triangles and None simplifies them away"
            ),
        },
        "provenance_and_fidelity_boundary": {
            "project_owned_generated_sources": True,
            "external_images_or_data_vendored": False,
            "botanical_reference_contract": str(
                CANOPY_ROOT_RELATIVE_PATH / "futaleufu_native_canopy_authoring_spec.json"
            ),
            "generated_pixels_are_not_botanical_measurements": True,
            "isolated_closeup_turntable_60m_150m_review_required": True,
            "corridor_use_before_visual_acceptance_forbidden": True,
        },
    }
    (repo_root / MANIFEST_RELATIVE_PATH).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    generate_futaleufu_native_canopy_assets(Path(__file__).resolve().parents[3])
