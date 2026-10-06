#!/usr/bin/env python3
"""Build the review-only, particle-scale Niagara whitewater SubUV V5 atlas.

V4 proved that a photographic macro-plume source collapses at the physical
sprite sizes used by the solver-authorized emitters. V5 selects individual
water events from three project-owned image-generation donor plates, crops
them to their actual silhouettes, and packs simple mip-safe frames without
inventing simulation state. Solver/contact state remains the sole authority
for when and where these presentation sprites emit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "unreal/SourceArt/RaftSim/Water/PhotographicSubUVV5"
SOURCE_PATHS = {
    "spray_foam": OUTPUT_DIR
    / "T_RaftSim_WhitewaterParticleScale_SprayFoam_Source_v5.png",
    "droplets": OUTPUT_DIR
    / "T_RaftSim_WhitewaterParticleScale_Droplets_Source_v5.png",
    "aerated_foam": OUTPUT_DIR
    / "T_RaftSim_WhitewaterParticleScale_AeratedFoam_Source_v5.png",
}
OUTPUT_PATH = OUTPUT_DIR / "T_RaftSim_WaterParticle_SubUV_v5_review.png"
MIP_PREVIEW_PATH = OUTPUT_DIR / "T_RaftSim_WaterParticle_SubUV_v5_mip32_preview.png"
PROVENANCE_PATH = OUTPUT_PATH.with_suffix(".provenance.json")

GENERATOR_VERSION = "raftsim-photographic-water-particle-subuv-review-v5"
GRID_SIZE = 4
CELL_SIZE = 512
ATLAS_SIZE = GRID_SIZE * CELL_SIZE
MIP_REVIEW_SIZE = 32
FRAME_RANGES = {
    "solver_spray": [0, 5],
    "contact_droplets": [6, 10],
    "aerated_mist": [11, 13],
    "rapid_aerosol": [14, 15],
}
FRAME_SOURCES = [
    ("spray_foam", 0),
    ("spray_foam", 1),
    ("spray_foam", 2),
    ("spray_foam", 3),
    ("spray_foam", 6),
    ("spray_foam", 7),
    ("droplets", 2),
    ("droplets", 3),
    ("droplets", 4),
    ("droplets", 6),
    ("droplets", 8),
    ("aerated_foam", 0),
    ("aerated_foam", 1),
    ("aerated_foam", 2),
    ("aerated_foam", 8),
    ("aerated_foam", 10),
]
# The mixed spray/foam donor honored the requested column rhythm but composed
# five visual rows instead of a strict 4x4 grid. These explicit regions select
# six complete top-row ballistic ribbons without accepting clipped neighbors.
# The other two donor plates are true 4x4 sheets and retain regular addressing.
SPRAY_FOAM_SOURCE_REGIONS = {
    0: [20, 60, 345, 260],
    1: [340, 60, 635, 250],
    2: [640, 60, 950, 250],
    3: [940, 60, 1240, 245],
    6: [630, 300, 940, 520],
    7: [940, 320, 1240, 520],
}
CLASS_GAMMA = {
    "solver_spray": 0.68,
    "contact_droplets": 0.72,
    "aerated_mist": 0.86,
    "rapid_aerosol": 0.76,
}
CLASS_MAX_CONTENT_PX = {
    "solver_spray": [324, 176],
    "contact_droplets": [224, 224],
    "aerated_mist": [326, 326],
    "rapid_aerosol": [326, 204],
}
MINIMUM_PADDING_PX = (CELL_SIZE - max(v[0] for v in CLASS_MAX_CONTENT_PX.values())) // 2

SOURCE_PROMPTS = {
    "spray_foam": (
        "Use case: photorealistic-natural\n"
        "Asset type: source plate for an Unreal Engine Niagara 4x4 SubUV particle atlas, designed to survive mipmapping and remain legible when each cell is downsampled to 32x32 pixels\n"
        "Primary request: Create one exact square 4-by-4 contact sheet containing sixteen separate, simple, particle-scale whitewater elements on a perfectly uniform pure black (#000000) background. These are individual airborne water events, never complete splash plumes.\n"
        "Subject order, reading left-to-right then top-to-bottom:\n"
        "Cells 0-5: six distinct ballistic spray fragments. Each cell contains only one torn thin water sheet or ribbon, generally stretched left-to-right or diagonally, with at most two or three attached bright beads. Use a clear asymmetric silhouette, strong white core, broken translucent edge, and generous negative space. No full plume and no mist cloud.\n"
        "Cells 6-10: five distinct droplet events. Each contains only one to four crisp round water beads with one short directional tail or tiny satellite bead. Large simple shapes, sparse composition, no dense cluster.\n"
        "Cells 11-13: three distinct aerated mist kernels. Each is one small porous irregular patch with a broken contour and visible black holes, not a round cloud, not smoke, and not cotton.\n"
        "Cells 14-15: two distinct rapid-aerosol foam fragments. Each is one broad crescent or lace-like eyebrow of aerated water with holes and a ragged crest, not a circular puff.\n"
        "Style/medium: physically plausible high-speed macro photography of real cold freshwater, neutral grayscale/white water only, realistic translucent membranes and aerated white cores, but simplify microdetail so the silhouette remains recognizable at thumbnail size.\n"
        "Composition/framing: exact regular 4x4 layout with no visible grid. Center each element within its invisible cell. Keep every element fully contained with at least 18 percent pure-black padding on all four cell edges. Spray fragments should occupy about 55-62 percent of cell width and 18-30 percent of cell height. Droplets should occupy 30-45 percent of the cell. Mist kernels and foam crescents should occupy 45-60 percent. No overlap between cells.\n"
        "Lighting/mood: neutral directional daylight response, bright aeration, convincing translucent water, high local contrast.\n"
        "Constraints: background must be uniform absolute black across the entire image and every cell boundary; every silhouette must be visibly different; all major features must be at least four source pixels thick; no hidden floor or reflections; no watermark.\n"
        "Avoid: complete splash plumes, fountain shapes, vertical paired puffs, smoke, clouds, fog balls, cotton, paint splatter, snow, fire, dense microdroplet noise, repeated silhouettes, rectangular sprite edges, visible grid, dividers, labels, text, border, river surface, landscape, rocks, raft, people, sky, horizon, watermark."
    ),
    "droplets": (
        "Use case: photorealistic-natural\n"
        "Asset type: donor plate for particle-scale Unreal Engine Niagara whitewater droplet sprites that remain legible at 32x32 pixels\n"
        "Primary request: Create one exact square 4-by-4 contact sheet containing sixteen visibly different sparse freshwater droplet events on a perfectly uniform pure black (#000000) background.\n"
        "Subject: Every invisible cell contains only one to three physically plausible airborne cold-river water beads. Use a simple bright bead silhouette with a small specular white core or crescent, optionally one short tapered directional tail or one tiny satellite bead. The bead should read as water, not a soap bubble: keep the center partially bright, avoid a hollow ring-only silhouette.\n"
        "Style/medium: high-speed macro photography of real freshwater droplets, neutral grayscale/white water only, strong local contrast, simplified detail for thumbnail and mip survival.\n"
        "Composition/framing: exact regular 4x4 layout with no visible grid. Center each event in its invisible cell. Each event occupies 32-48 percent of its cell, remains fully contained, and has at least 20 percent pure-black padding on all four cell edges. No overlap. All significant features at least six source pixels thick.\n"
        "Lighting/mood: neutral directional daylight, crisp translucent beads, bright aerated/specular core.\n"
        "Constraints: uniform absolute black background and cell boundaries; sixteen unique silhouettes; sparse particle-scale events only; no text or watermark.\n"
        "Avoid: soap bubbles, hollow glass rings, dense clusters, full splash plumes, foam sheets, mist, smoke, cloud, cotton, paint splatter, snow, repeated silhouettes, rectangular edges, visible grid, labels, borders, river surface, floor, reflection, landscape, raft, rock, person, sky, horizon, watermark."
    ),
    "aerated_foam": (
        "Use case: photorealistic-natural\n"
        "Asset type: donor plate for mip-safe Unreal Engine Niagara aerated-river mist and rapid-foam sprites, legible at 32x32 pixels\n"
        "Primary request: Create one exact square 4-by-4 contact sheet on a perfectly uniform pure black (#000000) background.\n"
        "Subject order, reading left-to-right then top-to-bottom:\n"
        "Cells 0-7: eight distinct small aerated freshwater mist kernels. Each is an irregular porous patch made from a few connected aerated beads and broken thin film, with large black holes and a ragged asymmetric contour. It must read as wet microfoam spray, never smoke or a round cloud.\n"
        "Cells 8-15: eight distinct rapid-foam fragments. Each is one broad horizontal or diagonal crescent, lace eyebrow, or torn aerated crest fragment with two to six large black holes, a broken leading edge, and a denser white underside. It is an individual fragment, not a complete breaking wave.\n"
        "Style/medium: high-speed macro photography of real turbulent cold freshwater, neutral grayscale/white water only, strong simple silhouettes, physically plausible translucent film and aerated white cores, simplified for thumbnail and mip survival.\n"
        "Composition/framing: exact regular 4x4 layout with no visible grid. Center one event in each invisible cell. Mist kernels occupy 38-50 percent of a cell. Foam fragments occupy 50-65 percent width and 20-38 percent height. Keep at least 18 percent uniform pure-black padding on every cell edge. No overlap. All major strands and holes at least six source pixels wide.\n"
        "Lighting/mood: neutral daylight, bright aerated water, realistic translucent edges, high local contrast.\n"
        "Constraints: uniform absolute-black background and cell boundaries; sixteen unique asymmetric silhouettes; no text or watermark.\n"
        "Avoid: smoke, clouds, fog balls, cotton, circular puffs, vertical paired puffs, complete splash plumes, fountains, complete breaking waves, dense microdroplet noise, paint splatter, fire, snow, repeated shapes, rectangles, visible grid, dividers, labels, borders, river surface, floor, reflection, landscape, rock, raft, people, sky, horizon, watermark."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_class(frame: int) -> str:
    for name, (first, last) in FRAME_RANGES.items():
        if first <= frame <= last:
            return name
    raise ValueError(f"Frame {frame} is outside the authored profile ranges")


def source_cell(source: np.ndarray, frame: int) -> np.ndarray:
    height, width, _ = source.shape
    x_bounds = [round(index * width / GRID_SIZE) for index in range(GRID_SIZE + 1)]
    y_bounds = [round(index * height / GRID_SIZE) for index in range(GRID_SIZE + 1)]
    row, column = divmod(frame, GRID_SIZE)
    return source[
        y_bounds[row] : y_bounds[row + 1],
        x_bounds[column] : x_bounds[column + 1],
    ]


def source_region(source: np.ndarray, source_name: str, frame: int) -> np.ndarray:
    if source_name != "spray_foam":
        return source_cell(source, frame)
    left, top, right, bottom = SPRAY_FOAM_SOURCE_REGIONS[frame]
    return source[top:bottom, left:right]


def fit_dimensions(width: int, height: int, maximum: list[int]) -> tuple[int, int]:
    scale = min(maximum[0] / width, maximum[1] / height)
    return max(1, round(width * scale)), max(1, round(height * scale))


def derive_frame(
    sources: dict[str, np.ndarray], target_frame: int
) -> Image.Image:
    source_name, source_frame = FRAME_SOURCES[target_frame]
    rgb = source_region(
        sources[source_name], source_name, source_frame
    ).astype(np.float32) / 255.0
    luminance = (
        0.2126 * rgb[:, :, 0]
        + 0.7152 * rgb[:, :, 1]
        + 0.0722 * rgb[:, :, 2]
    )

    black = max(float(np.percentile(luminance, 30.0)), 1.0 / 255.0)
    white = max(float(np.percentile(luminance, 99.7)), black + 0.08)
    value = np.clip((luminance - black) / (white - black), 0.0, 1.0)
    value = np.power(value, CLASS_GAMMA[frame_class(target_frame)])

    active_y, active_x = np.nonzero(value >= 0.025)
    if active_x.size == 0 or active_y.size == 0:
        raise ValueError(
            f"No active water pixels in {source_name} source frame {source_frame}"
        )
    source_height, source_width = value.shape
    margin = max(4, round(min(source_height, source_width) * 0.025))
    left = max(0, int(active_x.min()) - margin)
    top = max(0, int(active_y.min()) - margin)
    right = min(source_width, int(active_x.max()) + margin + 1)
    bottom = min(source_height, int(active_y.max()) + margin + 1)
    cropped = value[top:bottom, left:right]

    maximum = CLASS_MAX_CONTENT_PX[frame_class(target_frame)]
    fitted_size = fit_dimensions(cropped.shape[1], cropped.shape[0], maximum)
    content = Image.fromarray(
        np.rint(cropped * 255.0).astype(np.uint8), mode="L"
    ).resize(fitted_size, resample=Image.Resampling.LANCZOS)
    # A light one-pixel-radius dilation protects thin water membranes from
    # disappearing at the 32 px review mip without turning them into blobs.
    content = content.filter(ImageFilter.MaxFilter(3))

    padded = Image.new("L", (CELL_SIZE, CELL_SIZE), color=0)
    offset = ((CELL_SIZE - content.width) // 2, (CELL_SIZE - content.height) // 2)
    padded.paste(content, offset)
    return padded


def build_atlas(sources: dict[str, np.ndarray]) -> Image.Image:
    atlas = Image.new("L", (ATLAS_SIZE, ATLAS_SIZE), color=0)
    for target_frame in range(GRID_SIZE * GRID_SIZE):
        row, column = divmod(target_frame, GRID_SIZE)
        atlas.paste(
            derive_frame(sources, target_frame),
            (column * CELL_SIZE, row * CELL_SIZE),
        )
    return atlas


def build_mip_preview(atlas: Image.Image) -> tuple[Image.Image, list[dict[str, int]]]:
    preview = Image.new("L", (ATLAS_SIZE, ATLAS_SIZE), color=0)
    metrics: list[dict[str, int]] = []
    frame_hashes: set[str] = set()
    for frame in range(GRID_SIZE * GRID_SIZE):
        row, column = divmod(frame, GRID_SIZE)
        cell = atlas.crop(
            (
                column * CELL_SIZE,
                row * CELL_SIZE,
                (column + 1) * CELL_SIZE,
                (row + 1) * CELL_SIZE,
            )
        )
        mip = cell.resize(
            (MIP_REVIEW_SIZE, MIP_REVIEW_SIZE),
            resample=Image.Resampling.LANCZOS,
        )
        mip_array = np.asarray(mip, dtype=np.uint8)
        frame_hashes.add(hashlib.sha256(mip_array.tobytes()).hexdigest())
        border_max = int(
            max(
                mip_array[0, :].max(),
                mip_array[-1, :].max(),
                mip_array[:, 0].max(),
                mip_array[:, -1].max(),
            )
        )
        active = np.argwhere(mip_array > 8)
        if active.size == 0:
            raise ValueError(f"Frame {frame} vanishes at the 32 px review mip")
        metrics.append(
            {
                "frame": frame,
                "active_pixels_gt_8": int((mip_array > 8).sum()),
                "active_pixels_gt_32": int((mip_array > 32).sum()),
                "border_max": border_max,
                "maximum": int(mip_array.max()),
                "bbox_width": int(active[:, 1].max() - active[:, 1].min() + 1),
                "bbox_height": int(active[:, 0].max() - active[:, 0].min() + 1),
            }
        )
        if border_max != 0:
            raise ValueError(f"Frame {frame} contaminates the 32 px mip boundary")
        enlarged = mip.resize((CELL_SIZE, CELL_SIZE), resample=Image.Resampling.NEAREST)
        preview.paste(enlarged, (column * CELL_SIZE, row * CELL_SIZE))
    if len(frame_hashes) != GRID_SIZE * GRID_SIZE:
        raise ValueError("The 32 px review mip contains duplicate frames")
    return preview, metrics


def main() -> None:
    missing = [str(path) for path in SOURCE_PATHS.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing image-generation donor plate(s): {missing}")

    sources: dict[str, np.ndarray] = {}
    source_records: dict[str, dict[str, object]] = {}
    for name, path in SOURCE_PATHS.items():
        with Image.open(path) as image:
            if image.width != image.height:
                raise SystemExit(f"Image-generation donor must be square: {path}")
            sources[name] = np.asarray(image.convert("RGB"), dtype=np.uint8)
            source_records[name] = {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "dimensions_px": [image.width, image.height],
                "sha256": sha256(path),
                "prompt": SOURCE_PROMPTS[name],
            }

    atlas = build_atlas(sources)
    atlas.save(OUTPUT_PATH, optimize=True)
    mip_preview, mip_metrics = build_mip_preview(atlas)
    mip_preview.save(MIP_PREVIEW_PATH, optimize=True)

    provenance = {
        "asset": OUTPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "generator": Path(__file__).relative_to(REPO_ROOT).as_posix(),
        "generator_version": GENERATOR_VERSION,
        "ownership": "project_owned_first_party_image_generation",
        "image_generation_mode": "built_in_imagegen",
        "external_source_input": False,
        "authoritative_geography_claim": False,
        "usage": (
            "Review-only particle-scale presentation atlas; solver/contact state "
            "remains the sole emission authority."
        ),
        "sources": source_records,
        "frame_sources": [
            {"target_frame": index, "source": source, "source_frame": frame}
            for index, (source, frame) in enumerate(FRAME_SOURCES)
        ],
        "spray_foam_source_regions_px": SPRAY_FOAM_SOURCE_REGIONS,
        "dimensions_px": [ATLAS_SIZE, ATLAS_SIZE],
        "format": "8_bit_grayscale_png",
        "grid": [GRID_SIZE, GRID_SIZE],
        "cell_dimensions_px": [CELL_SIZE, CELL_SIZE],
        "minimum_black_padding_px": MINIMUM_PADDING_PX,
        "minimum_black_padding_fraction": MINIMUM_PADDING_PX / CELL_SIZE,
        "frame_ranges": FRAME_RANGES,
        "class_gamma": CLASS_GAMMA,
        "class_max_content_px": CLASS_MAX_CONTENT_PX,
        "mip_review_size_px": MIP_REVIEW_SIZE,
        "mip_review": MIP_PREVIEW_PATH.relative_to(REPO_ROOT).as_posix(),
        "mip_review_sha256": sha256(MIP_PREVIEW_PATH),
        "mip_metrics": mip_metrics,
        "sha256": sha256(OUTPUT_PATH),
    }
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
