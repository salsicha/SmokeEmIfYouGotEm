"""Validate the V34 persistent same-world Futaleufu transition sequence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)


AUTHORITIES = ("source_only", "hlod_only", "combined")
TRANSITION_FRAME_COUNT = 41
SOURCE_COVERAGE_TRANSITION_FRAME_COUNT = 31
SETTLE_FRAME_COUNT = 8
SAVED_FRAME_COUNT = TRANSITION_FRAME_COUNT + SETTLE_FRAME_COUNT


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sequence_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _capture_name(frame_index: int, authority: str) -> str:
    if frame_index < TRANSITION_FRAME_COUNT:
        radius_cm = 2300 + frame_index * 10
        distance = f"{radius_cm // 100:02d}m{radius_cm % 100:02d}"
        return (
            f"open_grown_conical_motion_f{frame_index:03d}_{distance}_{authority}.png"
        )
    settle_index = frame_index - TRANSITION_FRAME_COUNT + 1
    return (
        f"open_grown_conical_motion_f{frame_index:03d}_"
        f"settle{settle_index:02d}_27m00_{authority}.png"
    )


def _compact_comparison(before: Path, after: Path) -> dict[str, float]:
    comparison = _comparison(before, after)
    return {
        "changed_pixel_fraction_max_channel_gt_12": comparison[
            "changed_pixel_fraction_max_channel_gt_12"
        ],
        "mean_absolute_channel_delta": comparison["mean_absolute_channel_delta"],
        "dark_chromatic_foreground_intersection_over_union": comparison[
            "dark_chromatic_foreground_intersection_over_union"
        ],
    }


def _maximum(records: list[dict[str, float]], key: str) -> float:
    return max(record[key] for record in records)


def _minimum(records: list[dict[str, float]], key: str) -> float:
    return min(record[key] for record in records)


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
    motion_contract = structural_report["local_multi_view_atlas_hlod"][
        "persistent_motion_sequence_contract"
    ]
    local_review = structural_report["local_visual_review"]
    contract_valid = (
        motion_contract["enabled"] is True
        and motion_contract["sampling"]
        == "one_loaded_world_and_one_persistent_scene_capture_per_authority_mode"
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
        and local_review["persistent_motion_transition_capture_count"]
        == SAVED_FRAME_COUNT * len(AUTHORITIES)
    )

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
            frame_changes[authority] = comparison[
                "changed_pixel_fraction_max_channel_gt_12"
            ]
        combined_overhead.append(
            max(
                0.0,
                frame_changes["combined"]
                - max(frame_changes["source_only"], frame_changes["hlod_only"]),
            )
        )

    coverage_end = combined_to_hlod[
        SOURCE_COVERAGE_TRANSITION_FRAME_COUNT - 1
    ]
    motion_tail_end = combined_to_hlod[TRANSITION_FRAME_COUNT - 1]
    settle_end = combined_to_hlod[-1]
    source_endpoint = frame_relationships[0]["combined_to_source"]
    changed_key = "changed_pixel_fraction_max_channel_gt_12"
    mad_key = "mean_absolute_channel_delta"
    iou_key = "dark_chromatic_foreground_intersection_over_union"

    run_a_template = args.run_a_root / "open_grown_conical_foliage_template.json"
    run_b_template = capture_root / "open_grown_conical_foliage_template.json"
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
            "per_frame_mean_absolute_channel_deltas": [
                comparison[mad_key] for comparison in comparisons
            ],
            "per_frame_foreground_iou": [
                comparison[iou_key] for comparison in comparisons
            ],
            "maximum_changed_pixel_fraction": _maximum(comparisons, changed_key),
            "maximum_mean_absolute_channel_delta": _maximum(comparisons, mad_key),
            "minimum_foreground_iou": _minimum(comparisons, iou_key),
            "authority_repeatability_passed": authority_passed,
        }

    template_hashes = {
        "run_a": _sha256(run_a_template),
        "run_b": _sha256(run_b_template),
    }
    repeatability_passed &= template_hashes["run_a"] == template_hashes["run_b"]
    motion_harness_gate_passed = (
        contract_valid
        and repeatability_passed
        and source_endpoint[changed_key] <= 0.001
        and source_endpoint[mad_key] <= 0.05
        and source_endpoint[iou_key] >= 0.999
        and motion_tail_end[changed_key] <= 0.03
        and motion_tail_end[mad_key] <= 0.75
        and motion_tail_end[iou_key] >= 0.99
        and settle_end[changed_key] <= 0.02
        and settle_end[mad_key] <= 0.50
        and settle_end[iou_key] >= 0.995
        and settle_end[changed_key] <= coverage_end[changed_key] * 0.15
        and settle_end[mad_key] <= coverage_end[mad_key] * 0.15
    )
    transition_quantization_gate_passed = max(combined_overhead) <= 0.015
    temporal_gate_passed = (
        motion_harness_gate_passed and transition_quantization_gate_passed
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_persistent_motion_review.v34",
        "river_id": "futaleufu_terminator",
        "candidate": "v34_persistent_same_world_complementary_transition",
        "status": (
            "persistent_motion_validation_retained_lit_art_and_performance_gates_open"
            if temporal_gate_passed
            else (
                "persistent_motion_harness_retained_transition_quantization_rejected"
                if motion_harness_gate_passed
                else "persistent_motion_harness_rejected"
            )
        ),
        "comparison_contract": {
            "fixed": [
                "V24 woody and foliage geometry",
                "V25 HLOD photometry",
                "V27 frozen-WPO 512-pixel validation profile",
                "V29 azimuth registration",
                "V30 authored-distance perspective flat proxy",
                "V32 complementary screen ownership",
                "V33 traditional-raster transition wood",
            ],
            "intended_changes": [
                "one loaded world and persistent scene capture per authority mode",
                "TAA history and camera motion vectors across a fixed 60 Hz sequence",
                "source coverage ending at 26 m followed by ten HLOD-only motion frames",
                "eight stationary endpoint-settle frames",
            ],
            "validation_limit": (
                "unlit frozen-WPO diagnostic; fixed simulation delta is not measured "
                "wall-clock frame pacing, packaged performance, or photoreal art review"
            ),
            "art_review_allowed": False,
        },
        "structural_contract_valid": contract_valid,
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
            "maximum_combined_transition_overhead_above_larger_control": max(
                combined_overhead
            ),
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
            "maximum_start_source_changed_pixel_fraction": 0.001,
            "maximum_start_source_mean_absolute_channel_delta": 0.05,
            "minimum_start_source_foreground_iou": 0.999,
            "maximum_combined_transition_overhead_above_larger_control": 0.015,
            "maximum_motion_tail_changed_pixel_fraction": 0.03,
            "maximum_motion_tail_mean_absolute_channel_delta": 0.75,
            "minimum_motion_tail_foreground_iou": 0.99,
            "maximum_settle_changed_pixel_fraction": 0.02,
            "maximum_settle_mean_absolute_channel_delta": 0.50,
            "minimum_settle_foreground_iou": 0.995,
            "maximum_settle_fraction_of_coverage_end": 0.15,
        },
        "decision": {
            "retain": [
                "V34 persistent same-world moving-camera validation harness",
                "26 m source-coverage endpoint and ten-frame HLOD-only motion tail",
                "V33 raster woody source for transition-mask compatibility",
            ]
            if motion_harness_gate_passed
            else ["V33 ordered transition-path precursor"],
            "reject": [
                "V32 4x4 complementary ownership as a production temporal transition",
                "raising the V33 1.5-point transition-overhead limit to accept a 4.34-point spike",
                "fixed simulation delta as wall-clock performance proof",
                "unlit validation frames as photoreal art approval",
                "temporal stability as proof that source and HLOD silhouettes match",
                "this isolated open-grown form as corridor or all-form approval",
            ],
            "next_step": (
                "Replace the 4x4 ownership quantization with a finer complementary mask or "
                "stable blue-noise sequence, rerun this persistent harness, and only then "
                "advance to lit river-view review and packaged performance profiling."
            ),
        },
        "persistent_motion_harness_gate_passed": motion_harness_gate_passed,
        "transition_quantization_gate_passed": transition_quantization_gate_passed,
        "persistent_same_world_motion_gate_passed": temporal_gate_passed,
        "fixed_simulation_pacing_contract_passed": motion_harness_gate_passed,
        "wall_clock_performance_gate_passed": False,
        "underlying_no_pop_gate_passed": False,
        "lit_art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v34_persistent_motion_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
