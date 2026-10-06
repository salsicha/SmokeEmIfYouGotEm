#!/usr/bin/env python3
"""Build the review-only photographic Niagara whitewater SubUV atlas.

The source plate is project-owned image-generation output. This deterministic
derivation isolates, reorders, tone-maps, and pads the sixteen source studies
without inventing simulation state: solver/contact state remains the sole authority
for emission when this presentation atlas is under review.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Water/PhotographicSubUVV4"
)
SOURCE_PATH = OUTPUT_DIR / "T_RaftSim_WhitewaterSubUV_Source_v4.png"
OUTPUT_PATH = OUTPUT_DIR / "T_RaftSim_WaterParticle_SubUV_v4_review.png"
PROVENANCE_PATH = OUTPUT_PATH.with_suffix(".provenance.json")
GENERATOR_VERSION = "raftsim-photographic-water-particle-subuv-review-v4"
GRID_SIZE = 4
CELL_SIZE = 512
ATLAS_SIZE = GRID_SIZE * CELL_SIZE
# The generated source grouped droplets and mist by row rather than following
# the requested linear ordering. Keep the established runtime ranges and make
# that remapping explicit and reviewable here.
SOURCE_FRAME_FOR_TARGET = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 6, 12, 13, 14, 15, 7]
FRAME_RANGES = {
    "solver_spray": [0, 5],
    "contact_droplets": [6, 10],
    "aerated_mist": [11, 13],
    "rapid_aerosol": [14, 15],
}
CLASS_GAMMA = {
    "solver_spray": 0.76,
    "contact_droplets": 0.70,
    "aerated_mist": 1.05,
    "rapid_aerosol": 0.96,
}
CONTENT_SIZE = 358
CONTENT_OFFSET = (CELL_SIZE - CONTENT_SIZE) // 2
PADDING_PX = CONTENT_OFFSET
PROMPT = (
    "Use case: photorealistic-natural\n"
    "Asset type: source plate for an Unreal Engine Niagara 4x4 SubUV sprite atlas\n"
    "Primary request: Create one square 4-by-4 contact sheet containing sixteen "
    "separate photoreal whitewater sprite studies, each centered in its own "
    "invisible cell against an absolute pure black (#000000) background.\n"
    "Subject order, reading left-to-right then top-to-bottom: cells 0-5 are six "
    "distinct ballistic river spray plumes with torn sheets, aerated foam "
    "fragments, and fine microdroplets; cells 6-10 are five distinct clusters "
    "of suspended water beads and short droplet trails; cells 11-13 are three "
    "soft aerated river-mist puffs with porous natural density; cells 14-15 are "
    "two dense turbulent rapid-aerosol/foam volumes with lace-like breakup.\n"
    "Style/medium: high-speed macro photography of real cold freshwater "
    "whitewater, physically plausible droplet scale, varied organic silhouette, "
    "detailed thin foam membranes, crisp beads plus soft aerosol, neutral "
    "grayscale/white water only.\n"
    "Composition/framing: exact square canvas; regular 4x4 layout; every "
    "phenomenon fully contained within its cell with at least 15 percent black "
    "padding on every cell edge; no overlap between cells; no visible grid, "
    "dividers, labels, text, or borders.\n"
    "Lighting/mood: neutral directional daylight response with convincing "
    "translucent water and bright aeration, no colored lighting.\n"
    "Constraints: background must be uniform pure black across the entire image; "
    "isolate only the airborne water/foam; keep all cell boundaries black for "
    "bilinear sampling; each of the sixteen silhouettes must be visibly "
    "different and direction-neutral enough for billboard rotation; no watermark.\n"
    "Avoid: river surface, landscape, rocks, raft, people, sky, horizon, "
    "reflections on a floor, smoke, clouds, fire, snow, paint splatter, "
    "cotton-like blobs, repeated silhouettes, rectangular sprite edges, grid "
    "lines, labels, text, watermark."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_class(frame: int) -> str:
    for name, (first, last) in FRAME_RANGES.items():
        if first <= frame <= last:
            return name
    raise ValueError(f"Frame {frame} is outside the authored profile ranges")


def smoothstep(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def source_cell(source: np.ndarray, frame: int) -> np.ndarray:
    height, width, _ = source.shape
    x_bounds = [round(index * width / GRID_SIZE) for index in range(GRID_SIZE + 1)]
    y_bounds = [round(index * height / GRID_SIZE) for index in range(GRID_SIZE + 1)]
    row, column = divmod(frame, GRID_SIZE)
    return source[
        y_bounds[row] : y_bounds[row + 1],
        x_bounds[column] : x_bounds[column + 1],
    ]


def derive_frame(source_rgb: np.ndarray, target_frame: int) -> Image.Image:
    source_index = SOURCE_FRAME_FOR_TARGET[target_frame]
    rgb = source_cell(source_rgb, source_index).astype(np.float32) / 255.0
    luminance = (
        0.2126 * rgb[:, :, 0]
        + 0.7152 * rgb[:, :, 1]
        + 0.0722 * rgb[:, :, 2]
    )

    # Remove the source's near-black compression floor, normalize against its
    # bright water response, and preserve the distinct density of each class.
    black = max(float(np.percentile(luminance, 25.0)), 1.0 / 255.0)
    white = max(float(np.percentile(luminance, 99.8)), black + 0.08)
    value = np.clip((luminance - black) / (white - black), 0.0, 1.0)
    value = np.power(value, CLASS_GAMMA[frame_class(target_frame)])

    # Some source studies reach a generated cell boundary. Feather any clipped
    # fragments before downscaling so no hard rectangular edge survives.
    height, width = value.shape
    x = np.minimum(np.arange(width), np.arange(width)[::-1]).astype(np.float32)
    y = np.minimum(np.arange(height), np.arange(height)[::-1]).astype(np.float32)
    feather = max(8.0, min(height, width) * 0.045)
    edge = smoothstep(np.minimum(y[:, None], x[None, :]) / feather)
    value *= edge

    cell = Image.fromarray(np.rint(value * 255.0).astype(np.uint8), mode="L")
    cell = cell.resize(
        (CONTENT_SIZE, CONTENT_SIZE),
        resample=Image.Resampling.LANCZOS,
    )
    padded = Image.new("L", (CELL_SIZE, CELL_SIZE), color=0)
    padded.paste(cell, (CONTENT_OFFSET, CONTENT_OFFSET))
    return padded


def build_atlas(source_image: Image.Image) -> Image.Image:
    source = np.asarray(source_image.convert("RGB"), dtype=np.uint8)
    atlas = Image.new("L", (ATLAS_SIZE, ATLAS_SIZE), color=0)
    for target_frame in range(GRID_SIZE * GRID_SIZE):
        row, column = divmod(target_frame, GRID_SIZE)
        atlas.paste(
            derive_frame(source, target_frame),
            (column * CELL_SIZE, row * CELL_SIZE),
        )
    return atlas


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise SystemExit(f"Missing image-generation source plate: {SOURCE_PATH}")
    with Image.open(SOURCE_PATH) as source_image:
        if source_image.width != source_image.height:
            raise SystemExit("The image-generation source plate must be square")
        source_dimensions = [source_image.width, source_image.height]
        build_atlas(source_image).save(OUTPUT_PATH, optimize=True)

    provenance = {
        "asset": OUTPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "generator": Path(__file__).relative_to(REPO_ROOT).as_posix(),
        "generator_version": GENERATOR_VERSION,
        "ownership": "project_owned_first_party_image_generation",
        "image_generation_mode": "built_in_imagegen",
        "external_source_input": False,
        "authoritative_geography_claim": False,
        "usage": (
            "Review-only presentation atlas; solver/contact state remains the "
            "sole emission authority."
        ),
        "source": SOURCE_PATH.relative_to(REPO_ROOT).as_posix(),
        "source_dimensions_px": source_dimensions,
        "source_sha256": sha256(SOURCE_PATH),
        "source_prompt": PROMPT,
        "source_frame_for_target": SOURCE_FRAME_FOR_TARGET,
        "dimensions_px": [ATLAS_SIZE, ATLAS_SIZE],
        "format": "8_bit_grayscale_png",
        "grid": [GRID_SIZE, GRID_SIZE],
        "cell_dimensions_px": [CELL_SIZE, CELL_SIZE],
        "minimum_black_padding_px": PADDING_PX,
        "minimum_black_padding_fraction": PADDING_PX / CELL_SIZE,
        "frame_ranges": FRAME_RANGES,
        "class_gamma": CLASS_GAMMA,
        "sha256": sha256(OUTPUT_PATH),
    }
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
