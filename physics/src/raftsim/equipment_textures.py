"""Deterministic PBR derivation for project-owned raft and crew textiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps


OUTPUT_SIZE = 1024


@dataclass(frozen=True)
class TextileSpec:
    asset_id: str
    raw_filename: str
    unreal_stem: str
    physical_width_cm: float
    albedo_detail_strength: float
    roughness: float
    roughness_variation: float
    normal_strength: float
    prompt_summary: str


TEXTILES = (
    TextileSpec(
        "raft_coated_fabric",
        "Source_RaftCoatedFabric_v1.png",
        "T_RaftSim_RaftCoatedFabric",
        18.0,
        0.12,
        0.74,
        0.16,
        1.6,
        "Neutral unbranded commercial Hypalon/PVC raft fabric; orthographic, "
        "diffuse, edge-to-edge, with woven scrim and restrained abrasion.",
    ),
    TextileSpec(
        "pfd_ripstop",
        "Source_PfdRipstop_v1.png",
        "T_RaftSim_PfdRipstop",
        12.0,
        0.06,
        0.79,
        0.13,
        0.9,
        "Neutral unbranded high-denier Type-V PFD ripstop nylon; orthographic, "
        "diffuse, edge-to-edge, with a fine reinforcement grid.",
    ),
    TextileSpec(
        "wetsuit_neoprene",
        "Source_WetsuitNeoprene_v1.png",
        "T_RaftSim_WetsuitNeoprene",
        8.0,
        0.04,
        0.68,
        0.10,
        0.65,
        "Neutral premium rafting wetsuit neoprene with a fine stretch-jersey "
        "face; orthographic, diffuse, and edge-to-edge.",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tileable_luminance(source: Path) -> np.ndarray:
    image = Image.open(source).convert("RGB")
    image = ImageOps.fit(
        image,
        (OUTPUT_SIZE // 2, OUTPUT_SIZE // 2),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    quadrant = np.asarray(image, dtype=np.float32) / 255.0
    top = np.concatenate((quadrant, quadrant[:, ::-1]), axis=1)
    rgb = np.concatenate((top, top[::-1]), axis=0)
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    low_frequency = np.asarray(
        Image.fromarray(np.round(luminance * 255.0).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(radius=64.0)
        ),
        dtype=np.float32,
    ) / 255.0
    detail = luminance - low_frequency
    scale = max(float(np.percentile(np.abs(detail), 98.0)), 1.0e-4)
    return np.clip(0.5 + 0.46 * detail / scale, 0.0, 1.0)


def _derive_maps(luminance: np.ndarray, spec: TextileSpec) -> dict[str, np.ndarray]:
    # Tintable albedo keeps only bounded scan detail; game material supplies color.
    albedo = np.clip(
        0.68 + (luminance - 0.5) * spec.albedo_detail_strength,
        0.56,
        0.80,
    )
    albedo_rgb = np.repeat(albedo[..., None], 3, axis=2)

    height = np.clip(luminance, 0.0, 1.0)
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * spec.normal_strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * spec.normal_strength
    normal = np.stack((-dx, -dy, np.ones_like(height)), axis=2)
    normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1.0e-6)
    normal = normal * 0.5 + 0.5

    concavity = np.maximum(
        0.0,
        (np.roll(height, 1, axis=0) + np.roll(height, -1, axis=0)
         + np.roll(height, 1, axis=1) + np.roll(height, -1, axis=1)) * 0.25
        - height,
    )
    ao = np.clip(1.0 - concavity * 0.42, 0.82, 1.0)
    roughness = np.clip(
        spec.roughness + (0.5 - height) * spec.roughness_variation,
        0.34,
        0.96,
    )
    packed = np.stack((ao, roughness, height), axis=2)
    return {"albedo": albedo_rgb, "normal": normal, "packed": packed}


def _save_rgb(path: Path, pixels: np.ndarray) -> None:
    image = Image.fromarray(np.round(np.clip(pixels, 0.0, 1.0) * 255.0).astype(np.uint8), "RGB")
    image.save(path, format="PNG", optimize=False, compress_level=9)


def generate_equipment_textures(source_root: Path, output_root: Path) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, object]] = []
    for spec in TEXTILES:
        raw_path = source_root / spec.raw_filename
        if not raw_path.is_file():
            raise FileNotFoundError(f"Missing generated textile source: {raw_path}")
        maps = _derive_maps(_tileable_luminance(raw_path), spec)
        paths = {
            "albedo": output_root / f"{spec.unreal_stem}_Albedo.png",
            "normal": output_root / f"{spec.unreal_stem}_Normal.png",
            "packed": output_root / f"{spec.unreal_stem}_AORoughnessHeight.png",
        }
        for key, path in paths.items():
            _save_rgb(path, maps[key])
        assets.append(
            {
                "asset_id": spec.asset_id,
                "raw_source": spec.raw_filename,
                "raw_source_sha256": _sha256(raw_path),
                "dimensions": [OUTPUT_SIZE, OUTPUT_SIZE],
                "physical_width_cm": spec.physical_width_cm,
                "prompt_summary": spec.prompt_summary,
                "maps": {
                    key: {"path": path.name, "sha256": _sha256(path)}
                    for key, path in paths.items()
                },
            }
        )
    manifest: dict[str, object] = {
        "schema": "raftsim.equipment.generated_textile_pbr.v1",
        "status": "project_owned_generated_fallback_render_reviewed_not_photoreal",
        "generator": {
            "source_tool": "OpenAI built-in image generation",
            "model": "built-in image generation model; exact identifier not exposed",
            "seed": "not exposed",
            "postprocessor": "raftsim.equipment_textures.v1",
            "deterministic_postprocessing": True,
        },
        "processing": {
            "output_size": [OUTPUT_SIZE, OUTPUT_SIZE],
            "seam_method": "four_way_mirrored_material_tile",
            "albedo": "material_specific_bounded_neutral_detail_for_runtime_tint",
            "normal": "periodic_central_difference_tangent_space",
            "packed_channels": {"r": "ambient_occlusion", "g": "roughness", "b": "height"},
        },
        "render_review": "docs/environment-captures/south_fork_full_reach/m9_equipment_textile_fallback_v280_review.json",
        "assets": assets,
        "claim_boundary": "These project-owned generated textures improve the procedural fallback and are reusable on replacement meshes. They do not by themselves satisfy photoreal character, raft, or art-direction acceptance.",
    }
    manifest_path = output_root / "generated_textile_pbr_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    generate_equipment_textures(args.source_root, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
