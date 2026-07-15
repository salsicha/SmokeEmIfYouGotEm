"""Review the V39 material-identity Futaleufu HLOD split-shading search."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v37_temporal_lit_handoff import (
    _silhouette_and_photometry_metrics,
)

PRESETS = (
    ("baseline", 1.0, 1.0),
    ("foliage_gain_150", 1.0, 1.5),
    ("foliage_gain_200", 1.0, 2.0),
    ("foliage_gain_250", 1.0, 2.5),
    ("trunk_gain_150", 1.5, 1.0),
    ("trunk_gain_200", 2.0, 1.0),
    ("trunk_gain_250", 2.5, 1.0),
    ("balanced_gain_175", 1.75, 1.75),
    ("balanced_gain_200", 2.0, 2.0),
)
REPORT_NAME = "futaleufu_cordillera_cypress_v39_split_shading_review.json"
CONTACT_SHEET_NAME = "futaleufu_cordillera_cypress_v39_split_shading_contact_sheet.png"
ROI_XYXY = (280, 0, 1000, 540)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()


def _source_path(capture_root: Path) -> Path:
    return capture_root / "open_grown_conical_hlod_split_shading_source_reference.png"


def _preset_path(capture_root: Path, preset_id: str) -> Path:
    return capture_root / f"open_grown_conical_hlod_split_shading_{preset_id}.png"


def _rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def _overlap_photometry(
    source_path: Path, baseline_path: Path, candidate_path: Path
) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    source = _rgb(source_path)[y_min:y_max, x_min:x_max]
    baseline = _rgb(baseline_path)[y_min:y_max, x_min:x_max]
    candidate = _rgb(candidate_path)[y_min:y_max, x_min:x_max]
    source_luma = _luma(source)
    baseline_luma = _luma(baseline)
    candidate_luma = _luma(candidate)
    overlap = (source_luma < 75.0) & (baseline_luma < 75.0)
    overlap_pixels = int(np.count_nonzero(overlap))
    source_mean_luma = float(source_luma[overlap].mean())
    candidate_mean_luma = float(candidate_luma[overlap].mean())
    source_mean_rgb = source[overlap].mean(axis=0)
    candidate_mean_rgb = candidate[overlap].mean(axis=0)
    mean_absolute_channel_delta = float(
        np.abs(source[overlap] - candidate[overlap]).mean()
    )
    luma_ratio = candidate_mean_luma / source_mean_luma
    return {
        "roi_xyxy": list(ROI_XYXY),
        "fixed_overlap_definition": (
            "source_and_baseline_hlod_rec709_luminance_below_75"
        ),
        "fixed_overlap_pixel_count": overlap_pixels,
        "fixed_overlap_fraction_of_roi": overlap_pixels / overlap.size,
        "source_mean_luminance": source_mean_luma,
        "candidate_mean_luminance": candidate_mean_luma,
        "candidate_to_source_luminance_ratio": luma_ratio,
        "acceptable_luminance_ratio": [0.9, 1.1],
        "luminance_gate_passed": 0.9 <= luma_ratio <= 1.1,
        "source_mean_rgb": [float(value) for value in source_mean_rgb],
        "candidate_mean_rgb": [float(value) for value in candidate_mean_rgb],
        "candidate_minus_source_mean_rgb": [
            float(candidate_mean_rgb[index] - source_mean_rgb[index])
            for index in range(3)
        ],
        "mean_absolute_channel_delta": mean_absolute_channel_delta,
    }


def _material_identity_metrics(path: Path) -> dict:
    identity = np.asarray(Image.open(path).convert("RGBA"), dtype=np.uint8)
    occupied = identity[:, :, 3] > 5
    foliage = occupied & (identity[:, :, 0] >= 128)
    trunk = occupied & ~foliage
    occupied_count = int(np.count_nonzero(occupied))
    foliage_count = int(np.count_nonzero(foliage))
    trunk_count = int(np.count_nonzero(trunk))
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "occupied_texel_count": occupied_count,
        "foliage_texel_count": foliage_count,
        "trunk_texel_count": trunk_count,
        "foliage_fraction_of_occupied": foliage_count / max(occupied_count, 1),
        "trunk_fraction_of_occupied": trunk_count / max(occupied_count, 1),
        "both_material_classes_present": foliage_count > 0 and trunk_count > 0,
    }


def _write_contact_sheet(capture_root: Path, output_path: Path, best_id: str) -> None:
    items = [("SOURCE", _source_path(capture_root))]
    items.extend(
        (
            f"{preset_id.replace('_', ' ').upper()}{'  BEST BOUNDED' if preset_id == best_id else ''}",
            _preset_path(capture_root, preset_id),
        )
        for preset_id, _, _ in PRESETS
    )
    columns = 5
    rows = 2
    thumb_width = 320
    thumb_height = 180
    margin = 16
    title_height = 48
    label_height = 24
    canvas_width = margin * (columns + 1) + thumb_width * columns
    canvas_height = (
        title_height + margin * (rows + 1) + (label_height + thumb_height) * rows
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), (22, 24, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V39 EXACT MATERIAL-IDENTITY SPLIT-SHADING - BOUNDED GAIN INSUFFICIENT",
        fill=(240, 240, 240),
    )
    for item_index, (label, path) in enumerate(items):
        row = item_index // columns
        column = item_index % columns
        x = margin + column * (thumb_width + margin)
        y = title_height + margin + row * (label_height + thumb_height + margin)
        draw.text((x, y), label, fill=(210, 210, 210))
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        canvas.paste(image, (x, y + label_height))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    structural_report_path = report_root / V32_REPORT
    structural_report = json.loads(structural_report_path.read_text(encoding="utf-8"))
    hlod = structural_report["local_multi_view_atlas_hlod"]
    contract = hlod["hlod_split_shading_search_contract"]
    relightable = hlod["relightable_representation_contract"]
    local_review = structural_report["local_visual_review"]
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    source_path = _source_path(capture_root)
    preset_paths = {
        preset_id: _preset_path(capture_root, preset_id) for preset_id, _, _ in PRESETS
    }
    all_paths = [source_path, *preset_paths.values()]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    expected_presets = [
        {"id": preset_id, "trunk": trunk, "foliage": foliage}
        for preset_id, trunk, foliage in PRESETS
    ]
    contract_valid = (
        contract["enabled"] is True
        and contract["source_map"].endswith(
            "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        )
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture"
        and contract["camera_radius_cm"] == 2450.0
        and contract["warmup_frames_per_preset"] == 8
        and contract["temporal_history_reset_per_preset"]
        == "scene_capture_camera_cut_before_warmup"
        and contract["lighting"] is True
        and contract["temporal_aa"] is True
        and contract["material_identity_parameter"] == "AtlasMaterialIdentity"
        and contract["gain_presets"] == expected_presets
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_split_shading_search_capture_count"] == len(all_paths)
        and not missing_paths
    )

    baseline_path = preset_paths["baseline"]
    broad_metrics = {
        preset_id: _silhouette_and_photometry_metrics(source_path, path)
        for preset_id, path in preset_paths.items()
    }
    overlap_metrics = {
        preset_id: _overlap_photometry(source_path, baseline_path, path)
        for preset_id, path in preset_paths.items()
    }
    best_preset_id = min(
        preset_paths,
        key=lambda preset_id: (
            abs(
                1.0 - overlap_metrics[preset_id]["candidate_to_source_luminance_ratio"]
            ),
            overlap_metrics[preset_id]["mean_absolute_channel_delta"],
        ),
    )
    best_preset = next(
        {
            "id": preset_id,
            "trunk_gain_multiplier": trunk,
            "foliage_gain_multiplier": foliage,
        }
        for preset_id, trunk, foliage in PRESETS
        if preset_id == best_preset_id
    )
    best_overlap = overlap_metrics[best_preset_id]
    baseline_geometry = broad_metrics["baseline"]

    identity_relative = relightable["material_identity_output"]
    identity_path = repo_root / identity_relative
    if identity_path.is_file():
        identity_metrics = _material_identity_metrics(identity_path)
        identity_metrics["path"] = identity_relative
        identity_metrics["md5"] = _md5(identity_path)
    else:
        identity_metrics = {
            "path": identity_relative,
            "sha256": "",
            "md5": "",
            "occupied_texel_count": 0,
            "foliage_texel_count": 0,
            "trunk_texel_count": 0,
            "foliage_fraction_of_occupied": 0.0,
            "trunk_fraction_of_occupied": 0.0,
            "both_material_classes_present": False,
        }
    identity_valid = (
        identity_path.is_file()
        and hlod["material_identity_contract"]["fallback_pixels"] == 0
        and identity_metrics["both_material_classes_present"]
        and identity_metrics["md5"] == relightable["material_identity_md5"]
    )
    luminance_calibrated = best_overlap["luminance_gate_passed"]
    geometry_passed = baseline_geometry["source_hlod_silhouette_gate_passed"]
    baseline_overlap = overlap_metrics["baseline"]
    trunk_upper_overlap = overlap_metrics["trunk_gain_250"]
    foliage_upper_overlap = overlap_metrics["foliage_gain_250"]

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path, best_preset_id)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_split_shading_review.v39",
        "river_id": "futaleufu_terminator",
        "candidate": "v39_exact_material_identity_split_shading_search",
        "status": (
            "split_shading_controls_retained_luminance_calibrated_geometry_rejected"
            if contract_valid and identity_valid and luminance_calibrated
            else (
                "split_shading_controls_retained_bounded_gain_insufficient_geometry_rejected"
                if contract_valid and identity_valid
                else "split_shading_contract_or_identity_failed"
            )
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 10,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "camera_radius_cm": contract["camera_radius_cm"],
            "warmup_frames_per_preset": contract["warmup_frames_per_preset"],
        },
        "material_identity": {
            **identity_metrics,
            "fallback_pixels": hlod["material_identity_contract"]["fallback_pixels"],
            "identity_gate_passed": identity_valid,
        },
        "shading_controls": {
            "trunk_parameters": relightable["trunk_parameters"],
            "foliage_parameters": relightable["foliage_parameters"],
            "default_gain_multipliers": relightable["default_gain_multipliers"],
            "default_roughness": relightable["default_roughness"],
            "default_specular": relightable["default_specular"],
            "tested_gain_presets": expected_presets,
        },
        "measurements": {
            "fixed_overlap_photometry_by_preset": overlap_metrics,
            "broad_roi_silhouette_and_photometry_by_preset": broad_metrics,
            "best_preset": best_preset,
            "best_fixed_overlap_photometry": best_overlap,
            "baseline_geometry": baseline_geometry,
            "bounded_gain_search": {
                "baseline_luminance_ratio": baseline_overlap[
                    "candidate_to_source_luminance_ratio"
                ],
                "foliage_gain_250_luminance_ratio": foliage_upper_overlap[
                    "candidate_to_source_luminance_ratio"
                ],
                "trunk_gain_250_luminance_ratio": trunk_upper_overlap[
                    "candidate_to_source_luminance_ratio"
                ],
                "foliage_gain_250_relative_improvement": (
                    foliage_upper_overlap["candidate_to_source_luminance_ratio"]
                    / baseline_overlap["candidate_to_source_luminance_ratio"]
                    - 1.0
                ),
                "trunk_gain_250_relative_improvement": (
                    trunk_upper_overlap["candidate_to_source_luminance_ratio"]
                    / baseline_overlap["candidate_to_source_luminance_ratio"]
                    - 1.0
                ),
                "bounded_gain_range_exhausted_without_luminance_pass": (
                    not luminance_calibrated
                ),
            },
        },
        "human_visual_review": {
            "findings": [
                "the owner atlas visibly separates brown woody structure from green foliage",
                "foliage-only gain changes the crown while trunk-only gain is spatially bounded",
                "the strongest bounded foliage preset improves common-pixel luminance but remains far below source",
                "trunk gain has little effect, isolating the dominant fault to foliage shading response",
                "the flat proxy remains fuller and cannot reproduce source branch parallax",
                "terrain, distant foliage, and water remain physical-corridor blockout quality",
                "no named rapid or boat line is framed by this representation diagnostic",
            ],
            "material_identity_passed": identity_valid,
            "common_pixel_luminance_passed": luminance_calibrated,
            "source_hlod_silhouette_match_passed": geometry_passed,
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 5,
            "rows": 2,
        },
        "decision": {
            "retain": [
                "frontmost material-identity atlas with zero fallback texels",
                "independent trunk and foliage gain, roughness, and specular controls",
                f"{best_preset_id} only as the bounded upper-response diagnostic",
                "automatic frame 5 and the V37 temporal ownership path",
            ],
            "reject": [
                "treating gain calibration as a silhouette or parallax fix",
                "raising gain beyond the bounded 2.5 search to hide a foliage lighting-model failure",
                "the current flat plane as a source-matched production HLOD",
                "corridor substitution, other-form regeneration, or production promotion",
                "this diagnostic as hazard-readability or performance approval",
            ],
            "next_step": (
                "Split trunk and foliage into separate proxy layers and materials, give foliage a transmission/subsurface-capable two-sided response, and combine that with a source-matched depth-aware, view-interpolated, or geometry representation before rerunning V35/V37."
            ),
        },
        "split_shading_contract_passed": contract_valid,
        "material_identity_gate_passed": identity_valid,
        "common_pixel_luminance_gate_passed": luminance_calibrated,
        "source_hlod_silhouette_gate_passed": geometry_passed,
        "lit_art_review_passed": False,
        "hazard_readability_gate_passed": False,
        "wall_clock_performance_gate_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / REPORT_NAME
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))
    print(contact_sheet_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
