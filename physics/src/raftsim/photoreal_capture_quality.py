"""Review generated river screenshots for photoreal environment blockers."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


CAPTURE_ROOT_RELATIVE_PATH = Path("docs/environment-captures/photoreal_river_previews")
CAPTURE_MANIFEST_RELATIVE_PATH = CAPTURE_ROOT_RELATIVE_PATH / "environment_capture_manifest.json"
CAPTURE_QUALITY_REVIEW_RELATIVE_PATH = CAPTURE_ROOT_RELATIVE_PATH / "photoreal_capture_quality_review.json"


@dataclass(frozen=True)
class CaptureQualityThresholds:
    min_edge_density_for_lifelike_review: float = 0.045
    max_low_gradient_fraction_for_lifelike_review: float = 0.80
    min_quantized_entropy_bits_for_lifelike_review: float = 4.40
    max_flat_blue_field_fraction_for_lifelike_review: float = 0.62
    max_bottom_center_dark_fraction_for_lifelike_review: float = 0.08
    min_luma_std_for_lifelike_review: float = 32.0

    def as_dict(self) -> dict[str, float]:
        return {
            "min_edge_density_for_lifelike_review": self.min_edge_density_for_lifelike_review,
            "max_low_gradient_fraction_for_lifelike_review": self.max_low_gradient_fraction_for_lifelike_review,
            "min_quantized_entropy_bits_for_lifelike_review": self.min_quantized_entropy_bits_for_lifelike_review,
            "max_flat_blue_field_fraction_for_lifelike_review": self.max_flat_blue_field_fraction_for_lifelike_review,
            "max_bottom_center_dark_fraction_for_lifelike_review": self.max_bottom_center_dark_fraction_for_lifelike_review,
            "min_luma_std_for_lifelike_review": self.min_luma_std_for_lifelike_review,
        }


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "BILINEAR")


def _pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    raw = image.tobytes()
    return [(raw[index], raw[index + 1], raw[index + 2]) for index in range(0, len(raw), 3)]


def _luma(pixel: tuple[int, int, int]) -> float:
    red, green, blue = pixel
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _round(value: float, places: int = 4) -> float:
    return round(float(value), places)


def _entropy(counter: Counter[tuple[int, int, int]], sample_count: int) -> float:
    entropy = 0.0
    for count in counter.values():
        probability = count / sample_count
        entropy -= probability * math.log2(probability)
    return entropy


def _blockers(metrics: dict[str, float], thresholds: CaptureQualityThresholds) -> list[dict[str, str | float]]:
    blockers: list[dict[str, str | float]] = []
    if metrics["edge_density"] < thresholds.min_edge_density_for_lifelike_review:
        blockers.append(
            {
                "id": "low_edge_density",
                "metric": "edge_density",
                "value": metrics["edge_density"],
                "threshold": thresholds.min_edge_density_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Screenshots still read as broad smooth proxy fields instead of textured river corridor detail.",
            }
        )
    if metrics["low_gradient_fraction"] > thresholds.max_low_gradient_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "excess_low_gradient_area",
                "metric": "low_gradient_fraction",
                "value": metrics["low_gradient_fraction"],
                "threshold": thresholds.max_low_gradient_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Large low-gradient regions indicate flat water, sky, or terrain proxy surfaces that need production material and geometry detail.",
            }
        )
    if metrics["quantized_entropy_bits"] < thresholds.min_quantized_entropy_bits_for_lifelike_review:
        blockers.append(
            {
                "id": "low_color_texture_entropy",
                "metric": "quantized_entropy_bits",
                "value": metrics["quantized_entropy_bits"],
                "threshold": thresholds.min_quantized_entropy_bits_for_lifelike_review,
                "why_it_blocks_lifelike_review": "The rendered palette is still too compressed for a photoreal river environment.",
            }
        )
    if metrics["flat_blue_field_fraction"] > thresholds.max_flat_blue_field_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "large_flat_blue_field",
                "metric": "flat_blue_field_fraction",
                "value": metrics["flat_blue_field_fraction"],
                "threshold": thresholds.max_flat_blue_field_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Sky and water occupy too much of the frame as smooth blue preview material instead of source-shaped river, bank, and atmosphere detail.",
            }
        )
    if metrics["bottom_center_dark_fraction"] > thresholds.max_bottom_center_dark_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "dark_foreground_proxy",
                "metric": "bottom_center_dark_fraction",
                "value": metrics["bottom_center_dark_fraction"],
                "threshold": thresholds.max_bottom_center_dark_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Foreground raft/oar or river-eye cover proxies are still reading as dark placeholder shapes.",
            }
        )
    if metrics["luma_std"] < thresholds.min_luma_std_for_lifelike_review:
        blockers.append(
            {
                "id": "low_luma_variation",
                "metric": "luma_std",
                "value": metrics["luma_std"],
                "threshold": thresholds.min_luma_std_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Lighting and material variation are not strong enough for a lifelike review frame.",
            }
        )
    return blockers


def analyze_capture(
    repo_root: Path,
    capture_relative_path: str,
    river_id: str,
    view_id: str,
    thresholds: CaptureQualityThresholds | None = None,
) -> dict:
    thresholds = thresholds or CaptureQualityThresholds()
    capture_path = repo_root / capture_relative_path
    with Image.open(capture_path) as source_image:
        full_size = source_image.size
        image = source_image.convert("RGB").resize((320, 180), _resample_filter())

    width, height = image.size
    pixels = _pixels(image)
    luma_values = [_luma(pixel) for pixel in pixels]
    luma_mean = sum(luma_values) / len(luma_values)
    luma_std = math.sqrt(sum((value - luma_mean) ** 2 for value in luma_values) / len(luma_values))

    edge_count = 0
    low_gradient_count = 0
    gradient_sample_count = 0
    for y in range(height - 1):
        row = y * width
        next_row = (y + 1) * width
        for x in range(width - 1):
            index = row + x
            gradient = abs(luma_values[index + 1] - luma_values[index]) + abs(
                luma_values[next_row + x] - luma_values[index]
            )
            gradient_sample_count += 1
            if gradient > 18.0:
                edge_count += 1
            if gradient < 4.0:
                low_gradient_count += 1

    quantized = Counter((red // 32, green // 32, blue // 32) for red, green, blue in pixels)
    flat_blue_count = sum(
        1
        for red, green, blue in pixels
        if blue > 70 and blue > red + 18 and blue > green + 4
    )

    dark_bottom_center_count = 0
    bottom_center_sample_count = 0
    for y in range(int(height * 0.55), height):
        for x in range(int(width * 0.25), int(width * 0.75)):
            bottom_center_sample_count += 1
            if luma_values[y * width + x] < 38.0:
                dark_bottom_center_count += 1

    mean_rgb = [
        _round(sum(pixel[channel] for pixel in pixels) / len(pixels), 2)
        for channel in range(3)
    ]
    metrics = {
        "analysis_size": [width, height],
        "source_size": [full_size[0], full_size[1]],
        "rgb_mean": mean_rgb,
        "luma_mean": _round(luma_mean, 2),
        "luma_std": _round(luma_std, 2),
        "edge_density": _round(edge_count / gradient_sample_count),
        "low_gradient_fraction": _round(low_gradient_count / gradient_sample_count),
        "quantized_entropy_bits": _round(_entropy(quantized, len(pixels)), 2),
        "quantized_color_count": len(quantized),
        "flat_blue_field_fraction": _round(flat_blue_count / len(pixels)),
        "bottom_center_dark_fraction": _round(dark_bottom_center_count / bottom_center_sample_count),
    }
    blockers = _blockers(metrics, thresholds)
    return {
        "river_id": river_id,
        "view_id": view_id,
        "capture": capture_relative_path,
        "sha256": _hash_file(capture_path),
        "metrics": metrics,
        "blockers": blockers,
        "status": "preview_only_not_lifelike_quality_blockers" if blockers else "candidate_for_human_lifelike_review_not_approved",
    }


def _capture_entries(capture_manifest: dict) -> Iterable[tuple[str, str, str]]:
    for river in capture_manifest["captures"]:
        yield river["river_id"], "guide_seat_downstream", river["guide_seat_capture"]
        yield river["river_id"], "river_eye_downstream", river["river_eye_capture"]


def build_capture_quality_review(repo_root: Path, generated_on: str = "2026-07-08") -> dict:
    capture_manifest_path = repo_root / CAPTURE_MANIFEST_RELATIVE_PATH
    capture_manifest = json.loads(capture_manifest_path.read_text(encoding="utf-8"))
    thresholds = CaptureQualityThresholds()
    captures = [
        analyze_capture(repo_root, capture_path, river_id, view_id, thresholds)
        for river_id, view_id, capture_path in _capture_entries(capture_manifest)
    ]

    blocker_counts: Counter[str] = Counter(
        blocker["id"]
        for capture in captures
        for blocker in capture["blockers"]
    )
    per_river_status: dict[str, dict[str, object]] = {}
    for capture in captures:
        river = per_river_status.setdefault(
            capture["river_id"],
            {"capture_count": 0, "blocking_capture_count": 0, "blockers": set()},
        )
        river["capture_count"] = int(river["capture_count"]) + 1
        if capture["blockers"]:
            river["blocking_capture_count"] = int(river["blocking_capture_count"]) + 1
        river["blockers"].update(blocker["id"] for blocker in capture["blockers"])

    normalized_per_river = {
        river_id: {
            "capture_count": data["capture_count"],
            "blocking_capture_count": data["blocking_capture_count"],
            "blockers": sorted(data["blockers"]),
            "status": "preview_only_not_lifelike_quality_blockers"
            if data["blocking_capture_count"]
            else "candidate_for_human_lifelike_review_not_approved",
        }
        for river_id, data in sorted(per_river_status.items())
    }

    return {
        "schema": "raftsim.unreal.photoreal_capture_quality_review.v1",
        "generated_on": generated_on,
        "status": "captures_reviewed_preview_only_not_lifelike_quality_blockers_recorded",
        "source_capture_manifest": str(CAPTURE_MANIFEST_RELATIVE_PATH),
        "policy": {
            "metrics_are_blockers_not_lifelike_approval": True,
            "human_guide_geospatial_and_art_review_still_required": True,
            "water_visuals_must_not_hide_hazards_rescue_targets_or_physics_failures": True,
        },
        "thresholds": thresholds.as_dict(),
        "summary": {
            "capture_count": len(captures),
            "blocking_capture_count": sum(1 for capture in captures if capture["blockers"]),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "per_river": normalized_per_river,
        },
        "captures": captures,
        "current_decision": (
            "Use this automated review as a regression gate for the photoreal environment track. "
            "The current captures remain preview-only because they still show low texture entropy, large smooth proxy "
            "fields, and selected low-edge/low-luma river-eye failures; the July 8 pass removed the flat-blue and "
            "dark-foreground blocker classes, but passing those two checks still does not replace guide, geospatial, "
            "rights, hazard-readability, performance, and art-direction approval."
        ),
    }


def write_capture_quality_review(repo_root: Path, generated_on: str = "2026-07-08") -> Path:
    review = build_capture_quality_review(repo_root, generated_on=generated_on)
    output_path = repo_root / CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output_path
