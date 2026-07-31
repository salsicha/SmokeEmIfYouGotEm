#!/usr/bin/env python3
"""Build a project-owned, flow-aligned whitewater foam breakup texture.

This deterministic presentation asset contains no copied photography. Unreal
multiplies it by solver-authored foam, so it cannot create hydraulic features.
Multiscale turbulent fields form soft aerated masses and broken cellular lace
instead of authored strokes, closed bubbles, or long ruler bands.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "unreal/SourceArt/RaftSim/Water"
OUTPUT_PATH = OUTPUT_DIR / "T_RaftSim_SouthForkWater_FoamLace.png"
PROVENANCE_PATH = OUTPUT_PATH.with_suffix(".provenance.json")
GENERATOR_VERSION = "raftsim-production-whitewater-foam-lace-v4"
TEXTURE_SIZE = 1024
RANDOM_SEED = 20260728


def resized_noise(
    rng: np.random.Generator,
    width: int,
    height: int,
    blur_radius: float,
) -> np.ndarray:
    """Return a normalized, softly interpolated deterministic noise octave."""

    source = np.rint(rng.random((height, width)) * 255.0).astype(np.uint8)
    image = Image.fromarray(source, mode="L").resize(
        (TEXTURE_SIZE, TEXTURE_SIZE), Image.Resampling.BICUBIC
    )
    if blur_radius > 0.0:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return np.asarray(image, dtype=np.float32) / 255.0


def normalize(field: np.ndarray) -> np.ndarray:
    low, high = np.percentile(field, (1.0, 99.0))
    return np.clip((field - low) / max(float(high - low), 1.0e-6), 0.0, 1.0)


def smoothstep(low: float, high: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def build_texture() -> Image.Image:
    rng = np.random.default_rng(RANDOM_SEED)
    # More samples across V than U produce short streamwise masses. Independent
    # octaves prevent a single grid or contour scale from surviving at distance.
    low = resized_noise(rng, 34, 92, 9.0)
    medium = resized_noise(rng, 82, 176, 3.8)
    detail = resized_noise(rng, 176, 286, 1.4)
    breakup = resized_noise(rng, 118, 214, 2.4)
    micro = resized_noise(rng, 310, 420, 0.7)
    turbulent = normalize(low * 0.48 + medium * 0.32 + detail * 0.20)

    # Foam appears both as aerated masses at turbulence peaks and as irregular
    # lace around their boundaries. A second field opens holes and joins scales,
    # avoiding the literal pen-stroke read of the former texture.
    foam_mass = smoothstep(0.66, 0.88, turbulent)
    primary_lace = np.exp(-np.square((turbulent - 0.58) / 0.072))
    secondary_lace = np.exp(-np.square((detail - 0.54) / 0.060))
    aeration_gate = smoothstep(0.32, 0.72, normalize(low * 0.62 + breakup * 0.38))
    porous_breakup = 0.42 + 0.58 * smoothstep(0.24, 0.78, breakup)
    lace = np.maximum(primary_lace * 0.78, secondary_lace * 0.36)
    combined = np.maximum(foam_mass * 0.96, lace * aeration_gate) * porous_breakup
    combined += smoothstep(0.72, 0.94, micro) * aeration_gate * 0.18
    combined = np.power(np.clip(combined, 0.0, 1.0), 0.86)
    # Retain a soft shoulder but remove low gray haze before texture mips.
    combined = np.clip((combined - 0.055) / 0.945, 0.0, 1.0)
    return Image.fromarray(np.rint(combined * 255.0).astype(np.uint8), mode="L")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_texture().save(OUTPUT_PATH, optimize=True)
    provenance = {
        "asset": OUTPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "generator": Path(__file__).relative_to(REPO_ROOT).as_posix(),
        "generator_version": GENERATOR_VERSION,
        "ownership": "project_owned_first_party_procedural",
        "external_source_input": False,
        "authoritative_geography_claim": False,
        "usage": (
            "Presentation-only flow-aligned breakup multiplied by solver-authored "
            "foam; it cannot generate or authorize hydraulic features."
        ),
        "dimensions_px": [TEXTURE_SIZE, TEXTURE_SIZE],
        "format": "8_bit_grayscale_png",
        "random_seed": RANDOM_SEED,
        "tile_contract": "multiscale_fields_with_mirrored_runtime_addressing",
        "multiscale_octaves": 5,
        "authored_polyline_count": 0,
        "sha256": sha256(OUTPUT_PATH),
    }
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
