"""Validate the V35 8x8 Futaleufu transition with the V34 motion harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v34_persistent_motion import (
    AUTHORITIES,
    SAVED_FRAME_COUNT,
    SETTLE_FRAME_COUNT,
    SOURCE_COVERAGE_TRANSITION_FRAME_COUNT,
    TRANSITION_FRAME_COUNT,
    _compact_comparison,
    _maximum,
    _minimum,
    _sequence_sha256,
    _sha256,
)


V34_REVIEW = "futaleufu_cordillera_cypress_v34_persistent_motion_review.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    return parser.parse_args()


def _capture_name(frame_index: int, authority: str, fine: bool = True) -> str:
    sequence = "motion_8x8" if fine else "motion"
    if frame_index < TRANSITION_FRAME_COUNT:
        radius_cm = 2300 + frame_index * 10
        distance = f"{radius_cm // 100:02d}m{radius_cm % 100:02d}"
        return (
            f"open_grown_conical_{sequence}_f{frame_index:03d}_"
            f"{distance}_{authority}.png"
        )
    settle_index = frame_index - TRANSITION_FRAME_COUNT + 1
    return (
        f"open_grown_conical_{sequence}_f{frame_index:03d}_"
        f"settle{settle_index:02d}_27m00_{authority}.png"
    )


def _bayer_rank_8x8(x: int, y: int) -> int:
    rank = 0
    for bit in (2, 1, 0):
        x_bit = (x >> bit) & 1
        y_bit = (y >> bit) & 1
        rank = rank * 4 + 2 * (x_bit ^ y_bit) + y_bit
    return rank


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    structural_report = json.loads(
        (report_root / V32_REPORT).read_text(encoding="utf-8")
    )
    v34_review_path = report_root / V34_REVIEW
    v34_review = json.loads(v34_review_path.read_text(encoding="utf-8"))
    motion_contract = structural_report["local_multi_view_atlas_hlod"][
        "fine_persistent_motion_sequence_contract"
    ]
    local_review = structural_report["local_visual_review"]
    contract_valid = (
        motion_contract["enabled"] is True
        and motion_contract["sampling"]
        == "one_loaded_world_and_one_persistent_scene_capture_per_authority_mode"
        and motion_contract["pattern"] == "deterministic_8x8_screen_bayer"
        and motion_contract["pattern_rank_count"] == 64
        and motion_contract["base_pattern_retained_for_control"]
        == "deterministic_4x4_screen_bayer"
        and motion_contract["authority_modes"] == list(AUTHORITIES)
        and motion_contract["radial_band_cm"] == [2300.0, 2700.0]
        and motion_contract["camera_step_cm"] == 10.0
        and motion_contract["fixed_delta_seconds"] == 0.016666667
        and motion_contract["target_simulation_fps"] == 60.0
        and motion_contract["nominal_camera_speed_cm_per_second"] == 600.0
        and motion_contract["warmup_frame_count"] == 8
        and motion_contract["transition_frame_count"] == TRANSITION_FRAME_COUNT
        and motion_contract["source_coverage_transition_frame_count"]
        == SOURCE_COVERAGE_TRANSITION_FRAME_COUNT
        and motion_contract["source_coverage_transition_end_radius_cm"] == 2600.0
        and motion_contract["moving_hlod_only_tail_frame_count"] == 10
        and motion_contract["endpoint_settle_frame_count"] == SETTLE_FRAME_COUNT
        and motion_contract["saved_frame_count_per_mode"] == SAVED_FRAME_COUNT
        and motion_contract["source_coverage_start"] == 1.0
        and motion_contract["source_coverage_end"] == 0.0
        and motion_contract["source_coverage_step"] == -0.033333333
        and motion_contract["persistent_view_state"] is True
        and motion_contract["temporal_history"] is True
        and motion_contract["anti_aliasing_method"] == "temporal_aa"
        and motion_contract["camera_motion_vectors"]
        == "camera_transform_advanced_before_each_capture_with_persistent_view_state"
        and motion_contract["target_pacing_scope"]
        == "fixed_simulation_delta_not_wall_clock_performance_measurement"
        and motion_contract["lighting"] is False
        and motion_contract["motion_blur"] is False
        and motion_contract["capture_count"] == SAVED_FRAME_COUNT * len(AUTHORITIES)
        and len(motion_contract["captures"])
        == SAVED_FRAME_COUNT * len(AUTHORITIES)
        and local_review["fine_persistent_motion_transition_capture_count"]
        == SAVED_FRAME_COUNT * len(AUTHORITIES)
    )
    bayer_matrix = [
        [_bayer_rank_8x8(x, y) for x in range(8)] for y in range(8)
    ]
    bayer_rank_contract_valid = sorted(
        rank for row in bayer_matrix for rank in row
    ) == list(range(64))

    changed_key = "changed_pixel_fraction_max_channel_gt_12"
    mad_key = "mean_absolute_channel_delta"
    iou_key = "dark_chromatic_foreground_intersection_over_union"
    frame_relationships = []
    combined_to_hlod = []
    for frame_index in range(SAVED_FRAME_COUNT):
        paths = {
            authority: capture_root / _capture_name(frame_index, authority)
            for authority in AUTHORITIES
        }
        source_hlod = _compact_comparison(paths["source_only"], paths["hlod_only"])
        source_combined = _compact_comparison(
            paths["source_only"], paths["combined"]
        )
        hlod_combined = _compact_comparison(paths["hlod_only"], paths["combined"])
        combined_to_hlod.append(hlod_combined)
        frame_relationships.append(
            {
                "frame": frame_index,
                "source_coverage": (
                    1.0
                    - frame_index / (SOURCE_COVERAGE_TRANSITION_FRAME_COUNT - 1)
                    if frame_index < SOURCE_COVERAGE_TRANSITION_FRAME_COUNT
                    else 0.0
                ),
                "source_to_hlod": source_hlod,
                "combined_to_source": source_combined,
                "combined_to_hlod": hlod_combined,
            }
        )

    adjacent_motion = {authority: [] for authority in AUTHORITIES}
    combined_overhead = []
    for frame_index in range(TRANSITION_FRAME_COUNT - 1):
        frame_changes = {}
        for authority in AUTHORITIES:
            before = capture_root / _capture_name(frame_index, authority)
            after = capture_root / _capture_name(frame_index + 1, authority)
            comparison = _compact_comparison(before, after)
            adjacent_motion[authority].append(comparison)
            frame_changes[authority] = comparison[changed_key]
        combined_overhead.append(
            max(
                0.0,
                frame_changes["combined"]
                - max(frame_changes["source_only"], frame_changes["hlod_only"]),
            )
        )

    pattern_isolation = {}
    pattern_isolation_passed = True
    for authority in AUTHORITIES:
        comparisons = [
            _compact_comparison(
                capture_root / _capture_name(frame_index, authority, fine=False),
                capture_root / _capture_name(frame_index, authority),
            )
            for frame_index in range(SAVED_FRAME_COUNT)
        ]
        maximum_changed = _maximum(comparisons, changed_key)
        maximum_mad = _maximum(comparisons, mad_key)
        minimum_iou = _minimum(comparisons, iou_key)
        authority_passed = (
            maximum_changed <= 0.005
            and maximum_mad <= 0.10
            and minimum_iou >= 0.995
        ) if authority != "combined" else maximum_changed >= 0.05
        pattern_isolation_passed &= authority_passed
        pattern_isolation[authority] = {
            "per_frame_changed_pixel_fractions": [
                comparison[changed_key] for comparison in comparisons
            ],
            "maximum_changed_pixel_fraction": maximum_changed,
            "maximum_mean_absolute_channel_delta": maximum_mad,
            "minimum_foreground_iou": minimum_iou,
            "expected_pattern_response_passed": authority_passed,
        }

    repeatability = {}
    repeatability_passed = True
    for authority in AUTHORITIES:
        run_a_paths = [
            args.run_a_root / _capture_name(frame_index, authority)
            for frame_index in range(SAVED_FRAME_COUNT)
        ]
        run_b_paths = [
            capture_root / _capture_name(frame_index, authority)
            for frame_index in range(SAVED_FRAME_COUNT)
        ]
        comparisons = [
            _compact_comparison(run_a, run_b)
            for run_a, run_b in zip(run_a_paths, run_b_paths, strict=True)
        ]
        authority_passed = (
            _maximum(comparisons, changed_key) <= 0.005
            and _maximum(comparisons, mad_key) <= 0.10
            and _minimum(comparisons, iou_key) >= 0.995
        )
        repeatability_passed &= authority_passed
        repeatability[authority] = {
            "run_a_sequence_sha256": _sequence_sha256(run_a_paths),
            "run_b_sequence_sha256": _sequence_sha256(run_b_paths),
            "per_frame_changed_pixel_fractions": [
                comparison[changed_key] for comparison in comparisons
            ],
            "maximum_changed_pixel_fraction": _maximum(comparisons, changed_key),
            "maximum_mean_absolute_channel_delta": _maximum(comparisons, mad_key),
            "minimum_foreground_iou": _minimum(comparisons, iou_key),
            "authority_repeatability_passed": authority_passed,
        }

    run_a_template = args.run_a_root / "open_grown_conical_foliage_template.json"
    run_b_template = capture_root / "open_grown_conical_foliage_template.json"
    template_hashes = {
        "run_a": _sha256(run_a_template),
        "run_b": _sha256(run_b_template),
    }
    repeatability_passed &= template_hashes["run_a"] == template_hashes["run_b"]

    coverage_end = combined_to_hlod[
        SOURCE_COVERAGE_TRANSITION_FRAME_COUNT - 1
    ]
    motion_tail_end = combined_to_hlod[TRANSITION_FRAME_COUNT - 1]
    settle_end = combined_to_hlod[-1]
    source_endpoint = frame_relationships[0]["combined_to_source"]
    v34_overhead = v34_review["adjacent_motion_controls"][
        "maximum_combined_transition_overhead_above_larger_control"
    ]
    maximum_overhead = max(combined_overhead)
    gate_passed = (
        contract_valid
        and bayer_rank_contract_valid
        and pattern_isolation_passed
        and repeatability_passed
        and source_endpoint[changed_key] <= 0.001
        and source_endpoint[mad_key] <= 0.05
        and source_endpoint[iou_key] >= 0.999
        and maximum_overhead <= 0.015
        and maximum_overhead < v34_overhead
        and motion_tail_end[changed_key] <= 0.03
        and motion_tail_end[mad_key] <= 0.75
        and motion_tail_end[iou_key] >= 0.99
        and settle_end[changed_key] <= 0.02
        and settle_end[mad_key] <= 0.50
        and settle_end[iou_key] >= 0.995
        and settle_end[changed_key] <= coverage_end[changed_key] * 0.20
        and settle_end[mad_key] <= coverage_end[mad_key] * 0.25
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_fine_transition_review.v35",
        "river_id": "futaleufu_terminator",
        "candidate": "v35_deterministic_8x8_complementary_transition",
        "status": (
            "fine_transition_retained_lit_art_and_performance_gates_open"
            if gate_passed
            else "fine_transition_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V24 woody and foliage geometry",
                "V25 HLOD photometry",
                "V27 frozen-WPO 512-pixel validation profile",
                "V29 azimuth registration",
                "V30 authored-distance perspective flat proxy",
                "V33 traditional-raster transition wood",
                "V34 camera path, persistent view state, TAA, coverage curve, tail, and settling",
            ],
            "intended_change": (
                "ComplementaryPatternSize 4 to 8, increasing deterministic screen "
                "ownership ranks from 16 to 64"
            ),
            "validation_limit": (
                "unlit frozen-WPO diagnostic; fixed simulation delta is not measured "
                "wall-clock frame pacing, packaged performance, or photoreal art review"
            ),
            "art_review_allowed": False,
        },
        "source_structural_report_sha256": _sha256(report_root / V32_REPORT),
        "v34_review_sha256": _sha256(v34_review_path),
        "structural_contract_valid": contract_valid,
        "bayer_rank_contract": {
            "matrix": bayer_matrix,
            "contains_each_rank_0_through_63_once": bayer_rank_contract_valid,
        },
        "frame_relationships": frame_relationships,
        "adjacent_motion_controls": {
            "source_only_changed_pixel_fraction_range": [
                _minimum(adjacent_motion["source_only"], changed_key),
                _maximum(adjacent_motion["source_only"], changed_key),
            ],
            "hlod_only_changed_pixel_fraction_range": [
                _minimum(adjacent_motion["hlod_only"], changed_key),
                _maximum(adjacent_motion["hlod_only"], changed_key),
            ],
            "combined_changed_pixel_fraction_range": [
                _minimum(adjacent_motion["combined"], changed_key),
                _maximum(adjacent_motion["combined"], changed_key),
            ],
            "combined_transition_overhead_by_pair": combined_overhead,
            "maximum_combined_transition_overhead_above_larger_control": (
                maximum_overhead
            ),
            "v34_4x4_maximum_overhead": v34_overhead,
            "overhead_reduction_fraction": 1.0 - maximum_overhead / v34_overhead,
        },
        "temporal_history_decay": {
            "coverage_end_frame_30_combined_to_hlod": coverage_end,
            "motion_tail_end_frame_40_combined_to_hlod": motion_tail_end,
            "settle_end_frame_48_combined_to_hlod": settle_end,
            "settle_changed_fraction_of_coverage_end": (
                settle_end[changed_key] / coverage_end[changed_key]
            ),
            "settle_mean_delta_fraction_of_coverage_end": (
                settle_end[mad_key] / coverage_end[mad_key]
            ),
        },
        "pattern_isolation": {
            "authorities": pattern_isolation,
            "source_and_hlod_control_thresholds": {
                "maximum_changed_pixel_fraction": 0.005,
                "maximum_mean_absolute_channel_delta": 0.10,
                "minimum_foreground_iou": 0.995,
            },
            "minimum_combined_changed_pixel_fraction": 0.05,
            "pattern_isolation_gate_passed": pattern_isolation_passed,
        },
        "repeatability_evidence": {
            "run_a_snapshot_not_committed": True,
            "foliage_template_sha256": template_hashes,
            "foliage_template_exact": template_hashes["run_a"]
            == template_hashes["run_b"],
            "authorities": repeatability,
            "thresholds": {
                "maximum_changed_pixel_fraction": 0.005,
                "maximum_mean_absolute_channel_delta": 0.10,
                "minimum_foreground_iou": 0.995,
            },
            "repeatability_gate_passed": repeatability_passed,
        },
        "thresholds": {
            "maximum_combined_transition_overhead_above_larger_control": 0.015,
            "maximum_motion_tail_changed_pixel_fraction": 0.03,
            "maximum_motion_tail_mean_absolute_channel_delta": 0.75,
            "minimum_motion_tail_foreground_iou": 0.99,
            "maximum_settle_changed_pixel_fraction": 0.02,
            "maximum_settle_mean_absolute_channel_delta": 0.50,
            "minimum_settle_foreground_iou": 0.995,
            "maximum_settle_changed_fraction_of_coverage_end": 0.20,
            "maximum_settle_mean_delta_fraction_of_coverage_end": 0.25,
        },
        "decision": {
            "retain": [
                "V35 deterministic 8x8 complementary ownership for the validation path",
                "V34 persistent same-world motion harness and 1.5-point overhead ceiling",
                "26 m source-coverage endpoint and ten-frame HLOD-only motion tail",
                "V33 raster woody source for dynamic transition-mask compatibility",
            ]
            if gate_passed
            else ["V34 persistent same-world motion harness"],
            "reject": [
                "V32 4x4 ownership quantization for moving production transitions",
                "fixed simulation delta as wall-clock performance proof",
                "unlit validation frames as photoreal art approval",
                "temporal stability as proof that source and HLOD silhouettes match",
            ],
            "next_step": (
                "Capture the retained 8x8 transition in a lit river-view sequence, review "
                "visible patterning and art quality, then profile packaged desktop and "
                "target-VR wall-clock cost before corridor or all-form promotion."
            ),
        },
        "fine_transition_gate_passed": gate_passed,
        "persistent_same_world_motion_gate_passed": gate_passed,
        "fixed_simulation_pacing_contract_passed": gate_passed,
        "wall_clock_performance_gate_passed": False,
        "underlying_no_pop_gate_passed": False,
        "lit_art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v35_fine_transition_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
