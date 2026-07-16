"""Review the V41 Futaleufu HLOD frontlit/backlit transmission bracket."""

from __future__ import annotations

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
from raftsim.examples.compare_futaleufu_cordillera_cypress_v40_dual_layer import (
    ROI_XYXY,
    _luma,
    _pairwise_response,
    _rgb,
    _sha256,
)

LIGHT_MODES = ("frontlit", "backlit")
REPRESENTATIONS = (
    "source_reference",
    "two_sided_no_transmission",
    "two_sided_source_transmission",
)
REPORT_NAME = "futaleufu_cordillera_cypress_v41_transmission_light_bracket_review.json"
CONTACT_SHEET_NAME = (
    "futaleufu_cordillera_cypress_v41_transmission_light_bracket_contact_sheet.png"
)


def _capture_path(capture_root: Path, light_mode: str, representation: str) -> Path:
    return capture_root / (
        "open_grown_conical_hlod_transmission_light_bracket_"
        f"{light_mode}_{representation}.png"
    )


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
    source_mean_luma = float(source_luma[overlap].mean())
    candidate_mean_luma = float(candidate_luma[overlap].mean())
    ratio = candidate_mean_luma / source_mean_luma
    return {
        "roi_xyxy": list(ROI_XYXY),
        "fixed_overlap_definition": (
            "same_light_source_and_no_transmission_hlod_rec709_luminance_below_75"
        ),
        "fixed_overlap_pixel_count": int(np.count_nonzero(overlap)),
        "fixed_overlap_fraction_of_roi": float(
            np.count_nonzero(overlap) / overlap.size
        ),
        "source_mean_luminance": source_mean_luma,
        "candidate_mean_luminance": candidate_mean_luma,
        "candidate_to_source_luminance_ratio": ratio,
        "acceptable_luminance_ratio": [0.9, 1.1],
        "luminance_gate_passed": 0.9 <= ratio <= 1.1,
        "mean_absolute_channel_delta": float(
            np.abs(source[overlap] - candidate[overlap]).mean()
        ),
    }


def _directional_response(frontlit_path: Path, backlit_path: Path) -> dict:
    x_min, y_min, x_max, y_max = ROI_XYXY
    frontlit = _rgb(frontlit_path)[y_min:y_max, x_min:x_max]
    backlit = _rgb(backlit_path)[y_min:y_max, x_min:x_max]
    delta = np.abs(frontlit - backlit)
    return {
        "frontlit_sha256": _sha256(frontlit_path),
        "backlit_sha256": _sha256(backlit_path),
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


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    columns = 3
    rows = 2
    thumb_width = 320
    thumb_height = 180
    margin = 16
    title_height = 48
    label_height = 24
    canvas = Image.new(
        "RGB",
        (
            margin * (columns + 1) + thumb_width * columns,
            title_height + margin * (rows + 1) + rows * (label_height + thumb_height),
        ),
        (22, 24, 26),
    )
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V41 TRANSMISSION LIGHT BRACKET - LIGHT DIRECTION VALID, FLAT HLOD REJECTED",
        fill=(240, 240, 240),
    )
    for row, light_mode in enumerate(LIGHT_MODES):
        for column, representation in enumerate(REPRESENTATIONS):
            x = margin + column * (thumb_width + margin)
            y = title_height + margin + row * (label_height + thumb_height + margin)
            label = f"{light_mode.upper()} - {representation.replace('_', ' ').upper()}"
            draw.text((x, y), label, fill=(210, 210, 210))
            image = Image.open(
                _capture_path(capture_root, light_mode, representation)
            ).convert("RGB")
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
    contract = hlod["hlod_transmission_light_bracket_contract"]
    local_review = structural_report["local_visual_review"]
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    capture_paths = {
        light_mode: {
            representation: _capture_path(
                capture_root,
                light_mode,
                representation,
            )
            for representation in REPRESENTATIONS
        }
        for light_mode in LIGHT_MODES
    }
    all_paths = [
        capture_paths[light_mode][representation]
        for light_mode in LIGHT_MODES
        for representation in REPRESENTATIONS
    ]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
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
        and contract["warmup_frames_per_representation"] == 8
        and contract["temporal_history_reset_per_representation"]
        == "scene_capture_camera_cut_before_warmup"
        and contract["sun_actor_label"] == "RaftSim_Sun_LumenPreview"
        and contract["sun_original_transform_restored"] is True
        and contract["light_modes"] == list(LIGHT_MODES)
        and contract["representations_per_light"] == list(REPRESENTATIONS)
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_transmission_light_bracket_capture_count"]
        == len(all_paths)
        and not missing_paths
    )

    per_light = {}
    for light_mode in LIGHT_MODES:
        paths = capture_paths[light_mode]
        source_path = paths["source_reference"]
        no_transmission_path = paths["two_sided_no_transmission"]
        source_transmission_path = paths["two_sided_source_transmission"]
        overlap = _fixed_overlap_mask(source_path, no_transmission_path)
        per_light[light_mode] = {
            "fixed_overlap_photometry": {
                "no_transmission": _overlap_photometry(
                    source_path,
                    no_transmission_path,
                    overlap,
                ),
                "source_transmission": _overlap_photometry(
                    source_path,
                    source_transmission_path,
                    overlap,
                ),
            },
            "broad_roi_silhouette_and_photometry": {
                "no_transmission": _silhouette_and_photometry_metrics(
                    source_path,
                    no_transmission_path,
                ),
                "source_transmission": _silhouette_and_photometry_metrics(
                    source_path,
                    source_transmission_path,
                ),
            },
            "source_transmission_response_over_no_transmission": _pairwise_response(
                no_transmission_path,
                source_transmission_path,
                overlap,
            ),
        }

    direction_responses = {
        representation: _directional_response(
            capture_paths["frontlit"][representation],
            capture_paths["backlit"][representation],
        )
        for representation in REPRESENTATIONS
    }
    light_direction_valid = all(
        response["directional_response_gate_passed"]
        for response in direction_responses.values()
    )
    transmission_response_passed = any(
        per_light[light_mode]["source_transmission_response_over_no_transmission"][
            "material_luminance_improvement_gate_passed"
        ]
        for light_mode in LIGHT_MODES
    )
    best_light_mode = max(
        LIGHT_MODES,
        key=lambda light_mode: per_light[light_mode][
            "source_transmission_response_over_no_transmission"
        ]["candidate_to_baseline_luminance_ratio"],
    )
    best_transmission_photometry = per_light[best_light_mode][
        "fixed_overlap_photometry"
    ]["source_transmission"]
    best_transmission_geometry = per_light[best_light_mode][
        "broad_roi_silhouette_and_photometry"
    ]["source_transmission"]

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_transmission_light_bracket_review.v41",
        "river_id": "futaleufu_terminator",
        "candidate": "v41_fixed_frontlit_backlit_two_sided_foliage_bracket",
        "status": (
            "light_direction_validated_source_tint_response_insufficient_flat_hlod_rejected"
            if contract_valid and light_direction_valid
            else "transmission_light_bracket_contract_or_directional_response_failed"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 6,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "camera_radius_cm": contract["camera_radius_cm"],
            "light_direction_contract": contract["light_direction_contract"],
            "sun_original_transform_restored": contract[
                "sun_original_transform_restored"
            ],
        },
        "measurements": {
            "per_light": per_light,
            "frontlit_to_backlit_directional_response": direction_responses,
            "best_transmission_response_light_mode": best_light_mode,
            "best_transmission_fixed_overlap_photometry": (
                best_transmission_photometry
            ),
            "best_transmission_geometry": best_transmission_geometry,
        },
        "human_visual_review": {
            "findings": [
                "the frontlit and backlit brackets visibly and quantitatively change the source tree, HLOD, terrain, and cast shadows",
                "source foliage responds strongly to backlight while the flat HLOD remains predominantly dark",
                "the source transmission tint is nearly indistinguishable from black transmission under both brackets",
                "the corrected layer identity is retained before complementary temporal masking",
                "the nearest-view flat proxy remains fuller and cannot reproduce source branch or foliage-normal parallax",
                "no named rapid or boat line is framed by this material diagnostic",
            ],
            "light_direction_bracket_passed": light_direction_valid,
            "source_transmission_response_passed": transmission_response_passed,
            "source_hlod_silhouette_match_passed": best_transmission_geometry[
                "source_hlod_silhouette_gate_passed"
            ],
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 3,
            "rows": 2,
        },
        "decision": {
            "retain": [
                "the fixed frontlit/backlit physical-corridor bracket",
                "the corrected identity-before-temporal-mask layer ordering",
                "the disjoint Default Lit bark and TwoSidedFoliage architecture",
                "the source transmission tint as an exposed but unvalidated tuning input",
            ],
            "reject": [
                "light direction as the explanation for V40's negligible source-tint response",
                "the current source tint as a validated foliage transmission solution",
                "the flat nearest-view plane as a source-matched production HLOD",
                "corridor substitution, other-form regeneration, or production promotion",
                "this diagnostic as hazard-readability or performance approval",
            ],
            "next_step": (
                "Replace the flat plane with a source-matched depth-aware, view-interpolated, or geometry representation that preserves foliage orientation, then rerun this light bracket plus the V35 temporal and V37 lit physical-corridor guards before tuning transmission strength."
            ),
        },
        "transmission_light_bracket_contract_passed": contract_valid,
        "light_direction_response_gate_passed": light_direction_valid,
        "source_transmission_improvement_gate_passed": transmission_response_passed,
        "source_hlod_silhouette_gate_passed": best_transmission_geometry[
            "source_hlod_silhouette_gate_passed"
        ],
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
