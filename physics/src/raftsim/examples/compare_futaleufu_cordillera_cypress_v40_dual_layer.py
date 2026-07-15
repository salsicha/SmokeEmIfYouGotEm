"""Review the V40 dual-layer Futaleufu cypress HLOD lighting diagnostic."""

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

VARIANTS = (
    ("combined_default_lit_control", "COMBINED DEFAULT LIT"),
    ("two_sided_no_transmission", "TWO-SIDED, NO TRANSMISSION"),
    ("two_sided_source_transmission", "TWO-SIDED, SOURCE TRANSMISSION"),
    (
        "two_sided_source_transmission_foliage_gain_150",
        "SOURCE TRANSMISSION, FOLIAGE GAIN 1.5",
    ),
)
REPORT_NAME = "futaleufu_cordillera_cypress_v40_dual_layer_review.json"
CONTACT_SHEET_NAME = "futaleufu_cordillera_cypress_v40_dual_layer_contact_sheet.png"
ROI_XYXY = (280, 0, 1000, 540)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_path(capture_root: Path) -> Path:
    return capture_root / "open_grown_conical_hlod_dual_layer_source_reference.png"


def _variant_path(capture_root: Path, variant_id: str) -> Path:
    return capture_root / f"open_grown_conical_hlod_dual_layer_{variant_id}.png"


def _rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def _fixed_overlap_mask(source_path: Path, control_path: Path) -> np.ndarray:
    x_min, y_min, x_max, y_max = ROI_XYXY
    source_luma = _luma(_rgb(source_path)[y_min:y_max, x_min:x_max])
    control_luma = _luma(_rgb(control_path)[y_min:y_max, x_min:x_max])
    return (source_luma < 75.0) & (control_luma < 75.0)


def _overlap_photometry(
    source_path: Path,
    candidate_path: Path,
    overlap: np.ndarray,
) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    source = _rgb(source_path)[y_min:y_max, x_min:x_max]
    candidate = _rgb(candidate_path)[y_min:y_max, x_min:x_max]
    source_luma = _luma(source)
    candidate_luma = _luma(candidate)
    overlap_pixels = int(np.count_nonzero(overlap))
    source_mean_luma = float(source_luma[overlap].mean())
    candidate_mean_luma = float(candidate_luma[overlap].mean())
    source_mean_rgb = source[overlap].mean(axis=0)
    candidate_mean_rgb = candidate[overlap].mean(axis=0)
    luminance_ratio = candidate_mean_luma / source_mean_luma
    return {
        "roi_xyxy": list(ROI_XYXY),
        "fixed_overlap_definition": (
            "source_and_combined_default_lit_control_rec709_luminance_below_75"
        ),
        "fixed_overlap_pixel_count": overlap_pixels,
        "fixed_overlap_fraction_of_roi": overlap_pixels / overlap.size,
        "source_mean_luminance": source_mean_luma,
        "candidate_mean_luminance": candidate_mean_luma,
        "candidate_to_source_luminance_ratio": luminance_ratio,
        "acceptable_luminance_ratio": [0.9, 1.1],
        "luminance_gate_passed": 0.9 <= luminance_ratio <= 1.1,
        "source_mean_rgb": [float(value) for value in source_mean_rgb],
        "candidate_mean_rgb": [float(value) for value in candidate_mean_rgb],
        "candidate_minus_source_mean_rgb": [
            float(candidate_mean_rgb[index] - source_mean_rgb[index])
            for index in range(3)
        ],
        "mean_absolute_channel_delta": float(
            np.abs(source[overlap] - candidate[overlap]).mean()
        ),
    }


def _pairwise_response(
    baseline_path: Path,
    candidate_path: Path,
    overlap: np.ndarray,
) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    baseline = _rgb(baseline_path)[y_min:y_max, x_min:x_max]
    candidate = _rgb(candidate_path)[y_min:y_max, x_min:x_max]
    baseline_luma = _luma(baseline)[overlap]
    candidate_luma = _luma(candidate)[overlap]
    delta = np.abs(candidate[overlap] - baseline[overlap])
    mean_baseline_luma = float(baseline_luma.mean())
    mean_candidate_luma = float(candidate_luma.mean())
    ratio = mean_candidate_luma / mean_baseline_luma
    return {
        "baseline_sha256": _sha256(baseline_path),
        "candidate_sha256": _sha256(candidate_path),
        "fixed_overlap_pixel_count": int(np.count_nonzero(overlap)),
        "baseline_mean_luminance": mean_baseline_luma,
        "candidate_mean_luminance": mean_candidate_luma,
        "candidate_to_baseline_luminance_ratio": ratio,
        "mean_absolute_channel_delta": float(delta.mean()),
        "changed_pixel_fraction_at_least_one_level": float(
            np.count_nonzero(np.any(delta >= 1.0, axis=1)) / delta.shape[0]
        ),
        "material_luminance_improvement_gate": 1.02,
        "material_luminance_improvement_gate_passed": ratio >= 1.02,
    }


def _write_contact_sheet(capture_root: Path, output_path: Path, best_id: str) -> None:
    items = [("SOURCE", _source_path(capture_root))]
    items.extend(
        (
            f"{label}{'  BEST' if variant_id == best_id else ''}",
            _variant_path(capture_root, variant_id),
        )
        for variant_id, label in VARIANTS
    )
    columns = 5
    thumb_width = 320
    thumb_height = 180
    margin = 16
    title_height = 48
    label_height = 24
    canvas = Image.new(
        "RGB",
        (
            margin * (columns + 1) + thumb_width * columns,
            title_height + margin + label_height + thumb_height,
        ),
        (22, 24, 26),
    )
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V40 DUAL-LAYER HLOD - MATERIAL SPLIT RETAINED, REPRESENTATION REJECTED",
        fill=(240, 240, 240),
    )
    for column, (label, path) in enumerate(items):
        x = margin + column * (thumb_width + margin)
        y = title_height + margin
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
    contract = hlod["hlod_dual_layer_review_contract"]
    relightable = hlod["relightable_representation_contract"]
    local_review = structural_report["local_visual_review"]
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    source_path = _source_path(capture_root)
    variant_paths = {
        variant_id: _variant_path(capture_root, variant_id)
        for variant_id, _ in VARIANTS
    }
    all_paths = [source_path, *variant_paths.values()]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    expected_variants = ["source_reference", *variant_paths]
    contract_valid = (
        contract["enabled"] is True
        and relightable["split_layer_ready"] is True
        and relightable["split_shading_models"]
        == {"trunk": "DefaultLit", "foliage": "TwoSidedFoliage"}
        and relightable["split_layer_opacity"]
        == {
            "trunk": "opacity_times_one_minus_material_identity",
            "foliage": "opacity_times_material_identity",
        }
        and relightable["foliage_transmission_default"] == [0.78, 1.0, 0.58]
        and relightable["split_default_roughness"] == [0.62, 0.72]
        and relightable["split_default_specular"] == [0.12, 0.18]
        and contract["source_map"].endswith(
            "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        )
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture"
        and contract["camera_radius_cm"] == 2450.0
        and contract["warmup_frames_per_representation"] == 8
        and contract["temporal_history_reset_per_representation"]
        == "scene_capture_camera_cut_before_warmup"
        and contract["component_layers"] == ["combined_control", "trunk", "foliage"]
        and contract["variants"] == expected_variants
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_dual_layer_capture_count"] == len(all_paths)
        and not missing_paths
    )

    control_path = variant_paths["combined_default_lit_control"]
    overlap = _fixed_overlap_mask(source_path, control_path)
    broad_metrics = {
        variant_id: _silhouette_and_photometry_metrics(source_path, path)
        for variant_id, path in variant_paths.items()
    }
    overlap_metrics = {
        variant_id: _overlap_photometry(source_path, path, overlap)
        for variant_id, path in variant_paths.items()
    }
    best_variant_id = min(
        variant_paths,
        key=lambda variant_id: (
            abs(
                1.0 - overlap_metrics[variant_id]["candidate_to_source_luminance_ratio"]
            ),
            overlap_metrics[variant_id]["mean_absolute_channel_delta"],
        ),
    )
    best_overlap = overlap_metrics[best_variant_id]
    best_geometry = broad_metrics[best_variant_id]
    no_transmission_id = "two_sided_no_transmission"
    source_transmission_id = "two_sided_source_transmission"
    gain_id = "two_sided_source_transmission_foliage_gain_150"
    transmission_response = _pairwise_response(
        variant_paths[no_transmission_id],
        variant_paths[source_transmission_id],
        overlap,
    )
    gain_response = _pairwise_response(
        variant_paths[source_transmission_id],
        variant_paths[gain_id],
        overlap,
    )
    luminance_calibrated = best_overlap["luminance_gate_passed"]
    geometry_passed = best_geometry["source_hlod_silhouette_gate_passed"]

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path, best_variant_id)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_dual_layer_review.v40",
        "river_id": "futaleufu_terminator",
        "candidate": "v40_disjoint_default_lit_bark_two_sided_foliage_hlod",
        "status": (
            "dual_layer_contract_retained_lighting_and_representation_rejected"
            if contract_valid
            else "dual_layer_contract_failed"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 5,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "camera_radius_cm": contract["camera_radius_cm"],
            "warmup_frames_per_representation": contract[
                "warmup_frames_per_representation"
            ],
        },
        "layer_contract": {
            "component_layers": contract["component_layers"],
            "material_assets": {
                "combined_control": relightable["material_asset"],
                "trunk": relightable["trunk_material_asset"],
                "foliage": relightable["foliage_material_asset"],
            },
            "shading_models": relightable["split_shading_models"],
            "opacity": relightable["split_layer_opacity"],
            "foliage_transmission_default": relightable["foliage_transmission_default"],
            "split_default_roughness": relightable["split_default_roughness"],
            "split_default_specular": relightable["split_default_specular"],
        },
        "measurements": {
            "fixed_overlap_photometry_by_variant": overlap_metrics,
            "broad_roi_silhouette_and_photometry_by_variant": broad_metrics,
            "best_variant": best_variant_id,
            "best_fixed_overlap_photometry": best_overlap,
            "best_variant_geometry": best_geometry,
            "source_transmission_response_over_no_transmission": transmission_response,
            "foliage_gain_150_response_over_source_transmission": gain_response,
        },
        "human_visual_review": {
            "findings": [
                "the trunk and foliage components remain exactly registered while using disjoint material-identity opacity",
                "TwoSidedFoliage does not materially brighten this fixed-light source-transmission view over its black-transmission control",
                "foliage gain 1.5 brightens the expected crown pixels but does not reach source photometry",
                "the nearest-view flat proxy remains fuller than the source and cannot reproduce branch parallax",
                "terrain, distant foliage, and water remain physical-corridor blockout quality",
                "no named rapid or boat line is framed by this representation diagnostic",
            ],
            "dual_layer_architecture_passed": contract_valid,
            "source_transmission_luminance_improvement_passed": transmission_response[
                "material_luminance_improvement_gate_passed"
            ],
            "common_pixel_luminance_passed": luminance_calibrated,
            "source_hlod_silhouette_match_passed": geometry_passed,
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 5,
            "rows": 1,
        },
        "decision": {
            "retain": [
                "the exact material-identity atlas and disjoint component architecture",
                "Default Lit bark and TwoSidedFoliage as independently tunable physical material paths",
                "source transmission and foliage gain parameters as bounded diagnostics",
                "the combined V3 material as a fixed historical control",
            ],
            "reject": [
                "claiming the source-transmission tint is validated by this front/side-lit view",
                "using foliage gain to hide the remaining lighting and shape mismatch",
                "the current flat nearest-view plane as a source-matched production HLOD",
                "corridor substitution, other-form regeneration, or production promotion",
                "this diagnostic as hazard-readability or performance approval",
            ],
            "next_step": (
                "Add a fixed backlit/frontlit transmission bracket, then replace the flat nearest-view plane with a source-matched depth-aware, view-interpolated, or geometry representation and rerun the V35 temporal and V37 lit physical-corridor guards."
            ),
        },
        "dual_layer_contract_passed": contract_valid,
        "source_transmission_improvement_gate_passed": transmission_response[
            "material_luminance_improvement_gate_passed"
        ],
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
