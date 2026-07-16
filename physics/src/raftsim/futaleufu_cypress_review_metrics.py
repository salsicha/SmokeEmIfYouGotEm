"""Current reusable metrics for the locked Futaleufu cypress V43 review."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image


V32_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspective"
    "ComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"
)
V32_REPORT = (
    "futaleufu_cordillera_cypress_v32_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_complementary_transition_hlod_calibrated_"
    "irregular_crown_mass_compound_branchlet_atlas_report.json"
)
ROI_XYXY = (280, 0, 1000, 540)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def luma(image: np.ndarray) -> np.ndarray:
    return 0.2126 * image[:, :, 0] + 0.7152 * image[:, :, 1] + 0.0722 * image[:, :, 2]


def silhouette_and_photometry_metrics(source_path: Path, hlod_path: Path) -> dict:
    source = rgb(source_path)
    hlod = rgb(hlod_path)
    x_min, y_min, x_max, y_max = ROI_XYXY
    source = source[y_min:y_max, x_min:x_max]
    hlod = hlod[y_min:y_max, x_min:x_max]
    source_luma = luma(source)
    hlod_luma = luma(hlod)
    source_silhouette = source_luma < 75.0
    hlod_silhouette = hlod_luma < 75.0
    intersection = int(np.count_nonzero(source_silhouette & hlod_silhouette))
    union = int(np.count_nonzero(source_silhouette | hlod_silhouette))
    source_area = int(np.count_nonzero(source_silhouette))
    hlod_area = int(np.count_nonzero(hlod_silhouette))

    differing = np.max(np.abs(source - hlod), axis=2) > 24.0
    source_mean_luma = float(source_luma[differing].mean())
    hlod_mean_luma = float(hlod_luma[differing].mean())
    luma_ratio = hlod_mean_luma / source_mean_luma
    silhouette_iou = intersection / max(union, 1)
    area_ratio = hlod_area / max(source_area, 1)
    roi_mean_delta = float(np.abs(source - hlod).mean())
    silhouette_passed = silhouette_iou >= 0.90 and 0.90 <= area_ratio <= 1.10
    photometry_passed = 0.90 <= luma_ratio <= 1.10 and roi_mean_delta <= 12.0
    return {
        "frame": 15,
        "distance_m": 24.5,
        "roi_xyxy": [x_min, y_min, x_max, y_max],
        "silhouette_classification": "rec709_luminance_below_75_in_fixed_tree_roi",
        "source_silhouette_pixels": source_area,
        "hlod_silhouette_pixels": hlod_area,
        "source_hlod_silhouette_intersection_over_union": silhouette_iou,
        "hlod_to_source_silhouette_area_ratio": area_ratio,
        "minimum_acceptable_silhouette_iou": 0.90,
        "acceptable_silhouette_area_ratio": [0.90, 1.10],
        "source_hlod_silhouette_gate_passed": silhouette_passed,
        "photometry_classification": (
            "mean_rec709_luminance_where_source_hlod_max_channel_delta_exceeds_24"
        ),
        "photometry_sample_fraction": float(differing.mean()),
        "source_mean_luminance": source_mean_luma,
        "hlod_mean_luminance": hlod_mean_luma,
        "hlod_to_source_luminance_ratio": luma_ratio,
        "acceptable_luminance_ratio": [0.90, 1.10],
        "source_hlod_roi_mean_absolute_channel_delta": roi_mean_delta,
        "maximum_acceptable_roi_mean_absolute_channel_delta": 12.0,
        "source_hlod_photometry_gate_passed": photometry_passed,
    }


def fixed_overlap_mask(source_path: Path, control_path: Path) -> np.ndarray:
    x_min, y_min, x_max, y_max = ROI_XYXY
    source_luma = luma(rgb(source_path)[y_min:y_max, x_min:x_max])
    control_luma = luma(rgb(control_path)[y_min:y_max, x_min:x_max])
    return (source_luma < 75.0) & (control_luma < 75.0)


def overlap_photometry(
    source_path: Path,
    candidate_path: Path,
    overlap: np.ndarray,
) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    source = rgb(source_path)[y_min:y_max, x_min:x_max]
    candidate = rgb(candidate_path)[y_min:y_max, x_min:x_max]
    source_luma = luma(source)
    candidate_luma = luma(candidate)
    source_mean_luma = float(source_luma[overlap].mean())
    candidate_mean_luma = float(candidate_luma[overlap].mean())
    ratio = candidate_mean_luma / source_mean_luma
    return {
        "roi_xyxy": list(ROI_XYXY),
        "fixed_overlap_definition": (
            "same_light_source_and_no_transmission_hlod_rec709_luminance_below_75"
        ),
        "fixed_overlap_pixel_count": int(np.count_nonzero(overlap)),
        "fixed_overlap_fraction_of_roi": float(np.count_nonzero(overlap) / overlap.size),
        "source_mean_luminance": source_mean_luma,
        "candidate_mean_luminance": candidate_mean_luma,
        "candidate_to_source_luminance_ratio": ratio,
        "acceptable_luminance_ratio": [0.9, 1.1],
        "luminance_gate_passed": 0.9 <= ratio <= 1.1,
        "mean_absolute_channel_delta": float(
            np.abs(source[overlap] - candidate[overlap]).mean()
        ),
    }


def directional_response(frontlit_path: Path, backlit_path: Path) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    frontlit = rgb(frontlit_path)[y_min:y_max, x_min:x_max]
    backlit = rgb(backlit_path)[y_min:y_max, x_min:x_max]
    delta = np.abs(frontlit - backlit)
    return {
        "frontlit_sha256": sha256(frontlit_path),
        "backlit_sha256": sha256(backlit_path),
        "roi_xyxy": list(ROI_XYXY),
        "mean_absolute_channel_delta": float(delta.mean()),
        "changed_pixel_fraction_at_least_one_level": float(
            np.count_nonzero(np.any(delta >= 1.0, axis=2))
            / delta.shape[0]
            / delta.shape[1]
        ),
        "directional_response_gate_minimum_mean_channel_delta": 5.0,
        "directional_response_gate_passed": float(delta.mean()) >= 5.0,
    }
