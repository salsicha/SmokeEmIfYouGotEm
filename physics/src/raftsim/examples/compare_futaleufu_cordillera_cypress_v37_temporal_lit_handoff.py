"""Review the V37 temporal, relightable Futaleufu HLOD handoff."""

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
from raftsim.examples.compare_futaleufu_cordillera_cypress_v34_persistent_motion import (
    _compact_comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v36_lit_river_view import (
    _background_stability_metrics,
    _phase_ownership_metrics,
)

AUTHORITIES = ("source_only", "hlod_only", "combined")
TRANSITION_FRAME_COUNT = 41
SOURCE_COVERAGE_TRANSITION_FRAME_COUNT = 31
SAVED_FRAME_COUNT = 49
SELECTED_FRAMES = (0, 15, 30, 40, 48)
V35_REVIEW = "futaleufu_cordillera_cypress_v35_fine_transition_review.json"
V36_REVIEW = "futaleufu_cordillera_cypress_v36_lit_river_view_review.json"
REPORT_NAME = "futaleufu_cordillera_cypress_v37_temporal_lit_handoff_review.json"
CONTACT_SHEET_NAME = (
    "futaleufu_cordillera_cypress_v37_temporal_lit_handoff_contact_sheet.png"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_name(frame_index: int, authority: str) -> str:
    if frame_index < TRANSITION_FRAME_COUNT:
        radius_cm = 2300 + frame_index * 10
        distance = f"{radius_cm // 100:02d}m{radius_cm % 100:02d}"
        return (
            "open_grown_conical_motion_temporal_lit_river_view_"
            f"f{frame_index:03d}_{distance}_{authority}.png"
        )
    settle_index = frame_index - TRANSITION_FRAME_COUNT + 1
    return (
        "open_grown_conical_motion_temporal_lit_river_view_"
        f"f{frame_index:03d}_settle{settle_index:02d}_27m00_{authority}.png"
    )


def _capture_path(capture_root: Path, frame_index: int, authority: str) -> Path:
    return capture_root / _capture_name(frame_index, authority)


def _silhouette_and_photometry_metrics(source_path: Path, hlod_path: Path) -> dict:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.float32)
    hlod = np.asarray(Image.open(hlod_path).convert("RGB"), dtype=np.float32)
    x_min, y_min, x_max, y_max = 280, 0, 1000, 540
    source = source[y_min:y_max, x_min:x_max]
    hlod = hlod[y_min:y_max, x_min:x_max]
    source_luma = (
        0.2126 * source[:, :, 0] + 0.7152 * source[:, :, 1] + 0.0722 * source[:, :, 2]
    )
    hlod_luma = 0.2126 * hlod[:, :, 0] + 0.7152 * hlod[:, :, 1] + 0.0722 * hlod[:, :, 2]
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


def _temporal_metrics(capture_root: Path) -> dict:
    changed_key = "changed_pixel_fraction_max_channel_gt_12"
    mad_key = "mean_absolute_channel_delta"
    iou_key = "dark_chromatic_foreground_intersection_over_union"
    overhead_by_pair = []
    for frame_index in range(TRANSITION_FRAME_COUNT - 1):
        changes = {
            authority: _compact_comparison(
                _capture_path(capture_root, frame_index, authority),
                _capture_path(capture_root, frame_index + 1, authority),
            )[changed_key]
            for authority in AUTHORITIES
        }
        overhead_by_pair.append(
            max(
                0.0,
                changes["combined"] - max(changes["source_only"], changes["hlod_only"]),
            )
        )

    selected_relationships = {}
    for frame_index in SELECTED_FRAMES:
        paths = {
            authority: _capture_path(capture_root, frame_index, authority)
            for authority in AUTHORITIES
        }
        selected_relationships[str(frame_index)] = {
            "source_coverage": (
                1.0 - frame_index / (SOURCE_COVERAGE_TRANSITION_FRAME_COUNT - 1)
                if frame_index < SOURCE_COVERAGE_TRANSITION_FRAME_COUNT
                else 0.0
            ),
            "combined_to_source": _compact_comparison(
                paths["combined"], paths["source_only"]
            ),
            "combined_to_hlod": _compact_comparison(
                paths["combined"], paths["hlod_only"]
            ),
        }

    source_endpoint = selected_relationships["0"]["combined_to_source"]
    motion_tail = selected_relationships["40"]["combined_to_hlod"]
    settle_endpoint = selected_relationships["48"]["combined_to_hlod"]
    maximum_overhead = max(overhead_by_pair)
    gate_passed = (
        source_endpoint[changed_key] <= 0.03
        and maximum_overhead <= 0.015
        and motion_tail[changed_key] <= 0.03
        and motion_tail[mad_key] <= 0.75
        and motion_tail[iou_key] >= 0.99
        and settle_endpoint[changed_key] <= 0.02
        and settle_endpoint[mad_key] <= 0.50
        and settle_endpoint[iou_key] >= 0.995
    )
    return {
        "selected_frame_relationships": selected_relationships,
        "maximum_combined_transition_overhead_above_larger_control": maximum_overhead,
        "maximum_acceptable_transition_overhead": 0.015,
        "combined_transition_overhead_by_pair": overhead_by_pair,
        "source_endpoint_frame_0_combined_to_source": source_endpoint,
        "motion_tail_frame_40_combined_to_hlod": motion_tail,
        "settle_endpoint_frame_48_combined_to_hlod": settle_endpoint,
        "thresholds": {
            "maximum_source_endpoint_changed_pixel_fraction": 0.03,
            "maximum_motion_tail_changed_pixel_fraction": 0.03,
            "maximum_motion_tail_mean_absolute_channel_delta": 0.75,
            "minimum_motion_tail_foreground_iou": 0.99,
            "maximum_settle_changed_pixel_fraction": 0.02,
            "maximum_settle_mean_absolute_channel_delta": 0.50,
            "minimum_settle_foreground_iou": 0.995,
        },
        "temporal_transition_guard_passed": gate_passed,
        "fixed_delta_is_wall_clock_performance_evidence": False,
    }


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    thumb_width = 400
    thumb_height = 225
    margin = 16
    title_height = 48
    header_height = 28
    row_label_width = 92
    canvas_width = row_label_width + margin * 4 + thumb_width * 3
    canvas_height = (
        title_height + header_height + margin * 6 + thumb_height * len(SELECTED_FRAMES)
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), (22, 24, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V37 TEMPORAL + RELIT HLOD - TRANSITION RETAINED, SHAPE REJECTED",
        fill=(240, 240, 240),
    )
    for column, authority in enumerate(AUTHORITIES):
        x = row_label_width + margin * (column + 1) + thumb_width * column
        draw.text(
            (x, title_height), authority.replace("_", " ").upper(), fill=(210, 210, 210)
        )

    top = title_height + header_height + margin
    for row, frame_index in enumerate(SELECTED_FRAMES):
        y = top + row * (thumb_height + margin)
        label = f"f{frame_index:03d}"
        if frame_index == 15:
            label += "\n24.5 m"
        elif frame_index == 48:
            label += "\nsettled"
        draw.multiline_text((margin, y + 8), label, fill=(210, 210, 210), spacing=4)
        for column, authority in enumerate(AUTHORITIES):
            image = Image.open(
                _capture_path(capture_root, frame_index, authority)
            ).convert("RGB")
            image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            x = row_label_width + margin * (column + 1) + thumb_width * column
            canvas.paste(image, (x, y))
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
    v35_path = report_root / V35_REVIEW
    v36_path = report_root / V36_REVIEW
    v35_review = json.loads(v35_path.read_text(encoding="utf-8"))
    v36_review = json.loads(v36_path.read_text(encoding="utf-8"))
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE

    hlod_contract = structural_report["local_multi_view_atlas_hlod"]
    relightable = hlod_contract["relightable_representation_contract"]
    contract = hlod_contract["temporal_lit_river_view_motion_sequence_contract"]
    local_review = structural_report["local_visual_review"]
    all_paths = [
        _capture_path(capture_root, frame_index, authority)
        for authority in AUTHORITIES
        for frame_index in range(SAVED_FRAME_COUNT)
    ]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    relightable_valid = (
        relightable["ready"] is True
        and relightable["albedo_source"]
        == "SCS_BaseColor linear converted to sRGB atlas texels"
        and relightable["shading_model"] == "DefaultLit"
        and relightable["base_color_gain"] == [1.55, 1.55, 1.55]
        and relightable["tangent_space_normal"] is False
        and relightable["world_normal_sampled"] is True
        and relightable["emissive_connected"] is False
        and relightable["transition_modes"]
        == ["legacy_ordered_control", "engine_temporal_aa_complementary"]
    )
    contract_valid = (
        contract["enabled"] is True
        and contract["source_map"].endswith(
            "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        )
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_and_one_persistent_scene_capture_per_authority_mode"
        and contract["transition"]
        == "engine_DitherTemporalAA_with_exact_inverse_hlod_ownership"
        and contract["legacy_ordered_modes_retained"] is True
        and contract["hlod_shading"]
        == "DefaultLit albedo plus captured world normal, no emissive connection"
        and contract["authority_modes"] == list(AUTHORITIES)
        and contract["radial_band_cm"] == [2300.0, 2700.0]
        and contract["camera_step_cm"] == 10.0
        and contract["persistent_view_state"] is True
        and contract["temporal_history"] is True
        and contract["anti_aliasing_method"] == "temporal_aa"
        and all(
            contract[field] is True
            for field in (
                "lighting",
                "atmosphere",
                "fog",
                "ambient_occlusion",
                "global_illumination",
                "lumen_gi",
                "lumen_reflections",
                "screen_space_reflections",
                "reflection_environment",
            )
        )
        and contract["capture_count"] == 147
        and len(contract["captures"]) == 147
        and local_review["temporal_lit_river_view_motion_transition_capture_count"]
        == 147
        and not missing_paths
    )

    midpoint = {
        authority: _capture_path(capture_root, 15, authority)
        for authority in AUTHORITIES
    }
    pattern = _phase_ownership_metrics(
        midpoint["source_only"], midpoint["hlod_only"], midpoint["combined"]
    )
    pattern["purpose"] = (
        "8x8 grouping is retained only as a periodicity diagnostic for the temporal mask"
    )
    background = _background_stability_metrics(
        midpoint["source_only"], midpoint["hlod_only"]
    )
    shape_and_light = _silhouette_and_photometry_metrics(
        midpoint["source_only"], midpoint["hlod_only"]
    )
    temporal = _temporal_metrics(capture_root)
    legacy_guard_passed = (
        v35_review["fine_transition_gate_passed"] is True
        and v35_review["persistent_same_world_motion_gate_passed"] is True
    )

    old_phase_contrast = v36_review["visible_pattern_review"]["phase_contrast"]
    old_background_delta = v36_review["authority_background_stability"][
        "maximum_mean_absolute_channel_delta"
    ]
    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_temporal_lit_handoff_review.v37",
        "river_id": "futaleufu_terminator",
        "candidate": "v37_engine_temporal_aa_relightable_multiview_hlod",
        "status": (
            "temporal_pattern_and_background_isolation_passed_"
            "hlod_shape_photometry_and_corridor_art_rejected"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "legacy_v35_guard": {
            "review": str(v35_path.relative_to(repo_root)),
            "sha256": _sha256(v35_path),
            "fine_transition_gate_passed": v35_review["fine_transition_gate_passed"],
            "persistent_same_world_motion_gate_passed": v35_review[
                "persistent_same_world_motion_gate_passed"
            ],
            "legacy_guard_passed": legacy_guard_passed,
        },
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "relightable_material_contract_valid": relightable_valid,
            "expected_capture_count": 147,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "transition": contract["transition"],
            "legacy_ordered_modes_retained": contract["legacy_ordered_modes_retained"],
            "relightable_representation": relightable,
            "fixed_delta_is_wall_clock_performance_evidence": False,
        },
        "v36_to_v37_delta": {
            "v36_review": str(v36_path.relative_to(repo_root)),
            "v36_review_sha256": _sha256(v36_path),
            "phase_contrast": {
                "v36": old_phase_contrast,
                "v37": pattern["phase_contrast"],
                "reduction_fraction": 1.0
                - pattern["phase_contrast"] / old_phase_contrast,
            },
            "maximum_background_mean_absolute_channel_delta": {
                "v36": old_background_delta,
                "v37": background["maximum_mean_absolute_channel_delta"],
                "reduction_fraction": (
                    1.0
                    - background["maximum_mean_absolute_channel_delta"]
                    / old_background_delta
                ),
            },
        },
        "visible_pattern_review": pattern,
        "authority_background_stability": background,
        "source_hlod_shape_and_photometry": shape_and_light,
        "temporal_transition_review": temporal,
        "human_visual_review": {
            "reviewed_frames": list(SELECTED_FRAMES),
            "reviewed_authorities": list(AUTHORITIES),
            "findings": [
                "the V36 fixed 8x8 checker is no longer visible in the V37 midpoint",
                "source-only and HLOD-only terrain and water backgrounds remain stable",
                "the HLOD is now Default Lit and uses captured albedo and world normal instead of emissive color",
                "the flat nearest-view HLOD crown is darker, fuller, and structurally different from the source tree",
                "partial-coverage frames expose doubled and ghosted branch silhouettes",
                "terrain, distant foliage, and water remain physical-corridor blockout quality rather than photoreal",
                "no named rapid, boat line, hole, wave, or other hazard is present in the reviewed framing",
            ],
            "visible_mask_patterning_passed": pattern[
                "visible_periodic_pattern_gate_passed"
            ],
            "source_hlod_silhouette_match_passed": shape_and_light[
                "source_hlod_silhouette_gate_passed"
            ],
            "source_hlod_lit_material_response_passed": shape_and_light[
                "source_hlod_photometry_gate_passed"
            ],
            "photoreal_art_quality_passed": False,
            "hazard_readability": "not_assessable_no_named_hazard_in_frame",
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "selected_frames": list(SELECTED_FRAMES),
            "authority_columns": list(AUTHORITIES),
        },
        "decision": {
            "retain": [
                "selectable engine temporal-AA complementary ownership",
                "legacy ordered controls and the passing V35 temporal regression guard",
                "separate SCS_BaseColor albedo atlas and Default Lit world-normal HLOD path",
                "stable transient physical-corridor authority-only capture setup",
            ],
            "reject": [
                "the flat nearest-view proxy as a source-matched production silhouette",
                "the current HLOD photometry and ghosted partial-coverage handoff",
                "this sequence as evidence of photoreal corridor or hazard quality",
                "fixed 60 Hz simulation delta as packaged desktop or target-VR performance proof",
            ],
            "next_step": (
                "Replace the flat nearest-view proxy with a depth-aware, view-interpolated, or geometry HLOD that matches the source silhouette and lit response; rerun V35 and V37 before packaged profiling, corridor substitution, or all-form regeneration."
            ),
        },
        "legacy_transition_guard_passed": legacy_guard_passed,
        "lit_capture_contract_passed": contract_valid,
        "relightable_material_contract_passed": relightable_valid,
        "visible_patterning_gate_passed": pattern[
            "visible_periodic_pattern_gate_passed"
        ],
        "temporal_transition_guard_passed": temporal[
            "temporal_transition_guard_passed"
        ],
        "authority_background_stability_gate_passed": background[
            "authority_background_stability_gate_passed"
        ],
        "source_hlod_silhouette_gate_passed": shape_and_light[
            "source_hlod_silhouette_gate_passed"
        ],
        "source_hlod_photometry_gate_passed": shape_and_light[
            "source_hlod_photometry_gate_passed"
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
