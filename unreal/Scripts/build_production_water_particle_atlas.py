#!/usr/bin/env python3
"""Build the project-owned Niagara whitewater particle SubUV atlas.

The atlas is deterministic first-party presentation art. It contains six
ballistic spray shapes, five droplet clusters, three aerated mist puffs, and
two porous rapid-aerosol volumes. Runtime emitters select only the frame range
for their profile; live solver/contact state remains the sole emission source.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "unreal/SourceArt/RaftSim/Water"
OUTPUT_PATH = OUTPUT_DIR / "T_RaftSim_WaterParticle_SubUV.png"
PROVENANCE_PATH = OUTPUT_PATH.with_suffix(".provenance.json")
GENERATOR_VERSION = "raftsim-production-water-particle-subuv-v3"
GRID_SIZE = 4
CELL_SIZE = 512
ATLAS_SIZE = GRID_SIZE * CELL_SIZE
RANDOM_SEED = 20260729
FRAME_RANGES = {
    "solver_spray": [0, 5],
    "contact_droplets": [6, 10],
    "aerated_mist": [11, 13],
    "rapid_aerosol": [14, 15],
}


def smoothstep(low: float, high: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - low) / max(high - low, 1.0e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def noise_field(
    rng: np.random.Generator,
    source_size: int,
    blur_radius: float,
) -> np.ndarray:
    source = np.rint(rng.random((source_size, source_size)) * 255.0).astype(
        np.uint8
    )
    image = Image.fromarray(source, mode="L").resize(
        (CELL_SIZE, CELL_SIZE), Image.Resampling.BICUBIC
    )
    if blur_radius > 0.0:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    result = np.asarray(image, dtype=np.float32) / 255.0
    low, high = np.percentile(result, (1.0, 99.0))
    return np.clip((result - low) / max(float(high - low), 1.0e-6), 0.0, 1.0)


def gaussian(
    x: np.ndarray,
    y: np.ndarray,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
) -> np.ndarray:
    distance = np.square((x - center_x) / radius_x) + np.square(
        (y - center_y) / radius_y
    )
    return np.exp(-2.35 * distance)


def coordinates() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    axis = (np.arange(CELL_SIZE, dtype=np.float32) + 0.5) / CELL_SIZE
    axis = axis * 2.0 - 1.0
    x, y = np.meshgrid(axis, axis)
    # The padded edge is mandatory for bilinear/SubUV sampling: no frame can
    # bleed into its neighbor, and a sprite never exposes a rectangular edge.
    edge = 1.0 - smoothstep(0.78, 0.97, np.maximum(np.abs(x), np.abs(y)))
    return x, y, edge


def spray_frame(frame: int, rng: np.random.Generator) -> np.ndarray:
    x, y, edge = coordinates()
    coarse = noise_field(rng, 18 + frame, 5.0)
    detail = noise_field(rng, 58 + frame * 2, 1.5)
    mask = np.zeros_like(x)
    for index in range(4):
        progress = index / 3.0
        center_x = rng.uniform(-0.16, 0.16) + (progress - 0.5) * 0.10
        center_y = rng.uniform(-0.18, 0.18) + (progress - 0.5) * 0.20
        radius_x = (0.34 - 0.08 * progress) * rng.uniform(0.84, 1.16)
        radius_y = (0.25 - 0.05 * progress) * rng.uniform(0.84, 1.18)
        mask = np.maximum(
            mask,
            gaussian(x, y, center_x, center_y, radius_x, radius_y)
            * (1.0 - 0.34 * progress),
        )
    for _ in range(18 + frame):
        center_y = rng.uniform(-0.52, 0.56)
        center_x = rng.normal(0.0, 0.32)
        radius = rng.uniform(0.020, 0.058)
        mask = np.maximum(
            mask,
            gaussian(
                x,
                y,
                center_x,
                center_y,
                radius * rng.uniform(0.65, 1.20),
                radius * rng.uniform(1.0, 2.0),
            )
            * rng.uniform(0.55, 0.95),
        )
    breakup = 0.40 + 0.43 * coarse + 0.17 * detail
    mask = np.power(np.clip(mask * breakup * edge, 0.0, 1.0), 0.86)
    return smoothstep(0.025, 0.88, mask)


def droplet_frame(frame: int, rng: np.random.Generator) -> np.ndarray:
    x, y, edge = coordinates()
    mask = np.zeros_like(x)
    count = 7 + frame % 5
    for index in range(count):
        angle = rng.uniform(0.0, np.pi * 2.0)
        radius_from_center = rng.uniform(0.0, 0.66) * (index / max(count - 1, 1))
        center_x = np.cos(angle) * radius_from_center + rng.normal(0.0, 0.035)
        center_y = np.sin(angle) * radius_from_center + rng.normal(0.0, 0.035)
        radius = rng.uniform(0.025, 0.092) * (1.25 if index == 0 else 1.0)
        bead = gaussian(
            x,
            y,
            center_x,
            center_y,
            radius * rng.uniform(0.72, 1.12),
            radius * rng.uniform(1.0, 1.75),
        )
        mask = np.maximum(mask, bead * rng.uniform(0.72, 1.0))
    return np.power(np.clip(mask * edge, 0.0, 1.0), 0.72)


def mist_frame(frame: int, rng: np.random.Generator) -> np.ndarray:
    x, y, edge = coordinates()
    coarse = noise_field(rng, 14 + frame, 8.0)
    medium = noise_field(rng, 38 + frame * 2, 2.5)
    mask = np.zeros_like(x)
    for _ in range(9):
        center_x = rng.uniform(-0.48, 0.48)
        center_y = rng.uniform(-0.50, 0.50)
        mask += gaussian(
            x,
            y,
            center_x,
            center_y,
            rng.uniform(0.24, 0.46),
            rng.uniform(0.20, 0.42),
        ) * rng.uniform(0.22, 0.52)
    mask = np.clip(mask, 0.0, 1.0)
    mask *= 0.34 + 0.48 * coarse + 0.18 * medium
    mask *= edge
    # Mist keeps a long transparent shoulder; avoiding a binary contour is
    # more important than reaching opaque white in one particle.
    return np.power(np.clip(mask, 0.0, 1.0), 1.28)


def aerosol_frame(frame: int, rng: np.random.Generator) -> np.ndarray:
    x, y, edge = coordinates()
    coarse = noise_field(rng, 12 + frame, 8.5)
    medium = noise_field(rng, 34 + frame * 2, 3.2)
    detail = noise_field(rng, 86 + frame * 3, 1.0)
    mask = np.zeros_like(x)
    for _ in range(13):
        center_x = rng.uniform(-0.58, 0.58)
        center_y = rng.uniform(-0.50, 0.55)
        mask += gaussian(
            x,
            y,
            center_x,
            center_y,
            rng.uniform(0.18, 0.40),
            rng.uniform(0.18, 0.36),
        ) * rng.uniform(0.18, 0.46)
    mask = np.clip(mask, 0.0, 1.0)
    porous = smoothstep(0.28, 0.78, coarse * 0.55 + medium * 0.45)
    lace = smoothstep(0.54, 0.82, detail) * 0.20
    mask = np.clip(mask * (0.30 + 0.70 * porous) + lace * mask, 0.0, 1.0)
    return np.power(np.clip(mask * edge, 0.0, 1.0), 1.10)


def build_atlas() -> Image.Image:
    atlas = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.uint8)
    for frame in range(GRID_SIZE * GRID_SIZE):
        rng = np.random.default_rng(RANDOM_SEED + frame * 7919)
        if frame <= 5:
            value = spray_frame(frame, rng)
        elif frame <= 10:
            value = droplet_frame(frame, rng)
        elif frame <= 13:
            value = mist_frame(frame, rng)
        else:
            value = aerosol_frame(frame, rng)
        row, column = divmod(frame, GRID_SIZE)
        y0 = row * CELL_SIZE
        x0 = column * CELL_SIZE
        atlas[y0 : y0 + CELL_SIZE, x0 : x0 + CELL_SIZE] = np.rint(
            np.clip(value, 0.0, 1.0) * 255.0
        ).astype(np.uint8)
    return Image.fromarray(atlas, mode="L")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_atlas().save(OUTPUT_PATH, optimize=True)
    provenance = {
        "asset": OUTPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "generator": Path(__file__).relative_to(REPO_ROOT).as_posix(),
        "generator_version": GENERATOR_VERSION,
        "ownership": "project_owned_first_party_procedural",
        "external_source_input": False,
        "authoritative_geography_claim": False,
        "usage": (
            "Presentation-only Niagara SubUV breakup selected within live "
            "solver-authorized spray, droplet, mist, and aerosol emitters."
        ),
        "dimensions_px": [ATLAS_SIZE, ATLAS_SIZE],
        "format": "8_bit_grayscale_png",
        "grid": [GRID_SIZE, GRID_SIZE],
        "cell_dimensions_px": [CELL_SIZE, CELL_SIZE],
        "frame_ranges": FRAME_RANGES,
        "random_seed": RANDOM_SEED,
        "sha256": sha256(OUTPUT_PATH),
    }
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
