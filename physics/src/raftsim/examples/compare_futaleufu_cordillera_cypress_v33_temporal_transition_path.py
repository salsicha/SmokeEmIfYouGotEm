"""Validate the V33 ordered Futaleufu source/HLOD transition-path precursor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v29_azimuth_registration import (
    _label_paths,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
    _synthetic_dither_metrics,
)


SAMPLE_COUNT = 17
AUTHORITIES = ("source_only", "hlod_only", "combined")
SOURCE_COVERAGES = tuple(1.0 - index / 16.0 for index in range(SAMPLE_COUNT))
DISTANCE_TOKENS = tuple(
    f"{(2300 + index * 25) // 100:02d}m{(2300 + index * 25) % 100:02d}"
    for index in range(SAMPLE_COUNT)
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_name(distance: str, authority: str) -> str:
    return f"open_grown_conical_temporal_{distance}_{authority}.png"


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
    path_contract = structural_report["local_multi_view_atlas_hlod"][
        "temporal_transition_path_contract"
    ]
    local_export = structural_report["local_review_export"]
    contract_valid = (
        path_contract["enabled"] is True
        and path_contract["sampling"]
        == "ordered_camera_path_precursor_without_same-world_temporal_history"
        and path_contract["radial_band_cm"] == [2300.0, 2700.0]
        and path_contract["radial_step_cm"] == 25.0
        and path_contract["sample_count"] == SAMPLE_COUNT
        and path_contract["source_coverage_start"] == 1.0
        and path_contract["source_coverage_end"] == 0.0
        and path_contract["source_coverage_step"] == -0.0625
        and path_contract["authority_modes_per_sample"] == list(AUTHORITIES)
        and path_contract["source_woody_geometry"] == "unchanged_v24_v30_geometry"
        and path_contract["source_woody_renderer"]
        == "traditional_raster_for_dynamic_screen_mask_compatibility"
        and path_contract["nanite_source_woody_diagnostic"]
        == "rejected_wood_leaked_into_hlod_owned_pixels"
        and path_contract["capture_count"] == SAMPLE_COUNT * len(AUTHORITIES)
        and structural_report["local_visual_review"][
            "temporal_transition_capture_count"
        ]
        == SAMPLE_COUNT * len(AUTHORITIES)
        and local_export["nanite_woody_enabled"] is False
        and local_export["woody_renderer_contract"]
        == "traditional_raster_for_dynamic_screen_mask_compatibility"
    )

    sample_results = {}
    synthetic_changes = []
    synthetic_mad = []
    coverage_ratio_errors = []
    combined_to_source_changes = []
    combined_to_hlod_changes = []
    for distance, coverage in zip(DISTANCE_TOKENS, SOURCE_COVERAGES, strict=True):
        paths = {
            authority: capture_root / _capture_name(distance, authority)
            for authority in AUTHORITIES
        }
        source_to_hlod = _label_paths(
            _comparison(paths["source_only"], paths["hlod_only"]),
            f"run_b/{paths['source_only'].name}",
            f"run_b/{paths['hlod_only'].name}",
        )
        combined_to_source = _label_paths(
            _comparison(paths["source_only"], paths["combined"]),
            f"run_b/{paths['source_only'].name}",
            f"run_b/{paths['combined'].name}",
        )
        combined_to_hlod = _label_paths(
            _comparison(paths["hlod_only"], paths["combined"]),
            f"run_b/{paths['hlod_only'].name}",
            f"run_b/{paths['combined'].name}",
        )
        synthetic = _synthetic_dither_metrics(
            paths["source_only"], paths["hlod_only"], paths["combined"], coverage
        )
        full_change = source_to_hlod["changed_pixel_fraction_max_channel_gt_12"]
        source_side_ratio = (
            combined_to_source["changed_pixel_fraction_max_channel_gt_12"] / full_change
        )
        hlod_side_ratio = (
            combined_to_hlod["changed_pixel_fraction_max_channel_gt_12"] / full_change
        )
        coverage_ratio_errors.extend(
            (
                abs(source_side_ratio - (1.0 - coverage)),
                abs(hlod_side_ratio - coverage),
            )
        )
        synthetic_changes.append(synthetic["changed_pixel_fraction_max_channel_gt_12"])
        synthetic_mad.append(synthetic["mean_absolute_channel_delta"])
        combined_to_source_changes.append(
            combined_to_source["changed_pixel_fraction_max_channel_gt_12"]
        )
        combined_to_hlod_changes.append(
            combined_to_hlod["changed_pixel_fraction_max_channel_gt_12"]
        )
        sample_results[distance] = {
            "source_coverage": coverage,
            "source_to_hlod": source_to_hlod,
            "combined_to_source": combined_to_source,
            "combined_to_hlod": combined_to_hlod,
            "observed_combined_to_source_fraction_of_full_change": (source_side_ratio),
            "observed_combined_to_hlod_fraction_of_full_change": hlod_side_ratio,
            "synthetic_bayer_agreement": synthetic,
        }

    adjacent_results = {}
    source_adjacent_changes = []
    hlod_adjacent_changes = []
    combined_adjacent_changes = []
    combined_overhead = []
    for before_distance, after_distance in zip(
        DISTANCE_TOKENS[:-1], DISTANCE_TOKENS[1:], strict=True
    ):
        pair = f"{before_distance}_to_{after_distance}"
        mode_results = {}
        mode_changes = {}
        for authority in AUTHORITIES:
            before_name = _capture_name(before_distance, authority)
            after_name = _capture_name(after_distance, authority)
            comparison = _label_paths(
                _comparison(capture_root / before_name, capture_root / after_name),
                f"run_b/{before_name}",
                f"run_b/{after_name}",
            )
            mode_results[authority] = comparison
            mode_changes[authority] = comparison[
                "changed_pixel_fraction_max_channel_gt_12"
            ]
        overhead = max(
            0.0,
            mode_changes["combined"]
            - max(mode_changes["source_only"], mode_changes["hlod_only"]),
        )
        source_adjacent_changes.append(mode_changes["source_only"])
        hlod_adjacent_changes.append(mode_changes["hlod_only"])
        combined_adjacent_changes.append(mode_changes["combined"])
        combined_overhead.append(overhead)
        adjacent_results[pair] = {
            "comparisons": mode_results,
            "combined_transition_overhead_above_larger_control": overhead,
        }

    repeatability = {}
    repeat_changes = {authority: [] for authority in AUTHORITIES}
    for distance in DISTANCE_TOKENS:
        distance_results = {}
        for authority in AUTHORITIES:
            name = _capture_name(distance, authority)
            comparison = _label_paths(
                _comparison(args.run_a_root / name, capture_root / name),
                f"run_a_snapshot/{name}",
                f"run_b_regenerated/{name}",
            )
            distance_results[authority] = comparison
            repeat_changes[authority].append(
                comparison["changed_pixel_fraction_max_channel_gt_12"]
            )
        repeatability[distance] = distance_results
    template_name = "open_grown_conical_foliage_template.json"
    template_hashes = {
        "run_a": _sha256(args.run_a_root / template_name),
        "run_b": _sha256(capture_root / template_name),
    }
    repeatability_gate_passed = (
        template_hashes["run_a"] == template_hashes["run_b"]
        and max(repeat_changes["source_only"]) <= 0.012
        and max(repeat_changes["hlod_only"]) <= 0.015
        and max(repeat_changes["combined"]) <= 0.020
    )
    path_precursor_gate_passed = (
        contract_valid
        and repeatability_gate_passed
        and max(synthetic_changes) <= 0.0001
        and max(synthetic_mad) <= 0.01
        and max(coverage_ratio_errors) <= 0.01
        and combined_to_source_changes == sorted(combined_to_source_changes)
        and combined_to_hlod_changes == sorted(combined_to_hlod_changes, reverse=True)
        and max(combined_overhead) <= 0.015
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_temporal_transition_path_review.v33",
        "river_id": "futaleufu_terminator",
        "candidate": "v33_ordered_complementary_transition_path_precursor",
        "status": (
            "ordered_path_precursor_retained_same_world_temporal_and_art_gates_open"
            if path_precursor_gate_passed
            else "ordered_path_precursor_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V24 woody and foliage geometry",
                "V25 photometry and endpoint authority",
                "V27 frozen-WPO 512-pixel deterministic validation profile",
                "V29 16-degree azimuth registration",
                "V30 authored-distance perspective flat proxy",
                "V32 deterministic complementary 4x4 screen Bayer ownership",
            ],
            "intended_changes": [
                "17 exact radial samples at 25 cm spacing through the 23-27 m band",
                "traditional-raster source wood so the dynamic screen mask affects trunk and branches",
            ],
            "sampling_limit": (
                "separate world reload per capture; no persistent view state, temporal history, "
                "TAA, motion vectors, continuous camera velocity, or lit art review"
            ),
            "art_review_allowed": False,
        },
        "structural_contract_valid": contract_valid,
        "sample_results": sample_results,
        "adjacent_path_results": adjacent_results,
        "repeatability_evidence": {
            "run_a_snapshot_not_committed": True,
            "foliage_template_sha256": template_hashes,
            "foliage_template_exact": template_hashes["run_a"]
            == template_hashes["run_b"],
            "samples": repeatability,
            "derived_findings": {
                "maximum_source_changed_pixel_fraction": max(
                    repeat_changes["source_only"]
                ),
                "maximum_hlod_changed_pixel_fraction": max(repeat_changes["hlod_only"]),
                "maximum_combined_changed_pixel_fraction": max(
                    repeat_changes["combined"]
                ),
            },
            "thresholds": {
                "maximum_source_changed_pixel_fraction": 0.012,
                "maximum_hlod_changed_pixel_fraction": 0.015,
                "maximum_combined_changed_pixel_fraction": 0.020,
            },
            "repeatability_gate_passed": repeatability_gate_passed,
        },
        "derived_findings": {
            "maximum_synthetic_bayer_changed_pixel_fraction": max(synthetic_changes),
            "maximum_synthetic_bayer_mean_absolute_channel_delta": max(synthetic_mad),
            "maximum_coverage_ratio_error": max(coverage_ratio_errors),
            "source_adjacent_changed_pixel_fraction_range": [
                min(source_adjacent_changes),
                max(source_adjacent_changes),
            ],
            "hlod_adjacent_changed_pixel_fraction_range": [
                min(hlod_adjacent_changes),
                max(hlod_adjacent_changes),
            ],
            "combined_adjacent_changed_pixel_fraction_range": [
                min(combined_adjacent_changes),
                max(combined_adjacent_changes),
            ],
            "maximum_combined_transition_overhead_above_larger_control": max(
                combined_overhead
            ),
            "endpoint_synthetic_bayer_changed_pixel_fractions": [
                synthetic_changes[0],
                synthetic_changes[-1],
            ],
        },
        "thresholds": {
            "maximum_synthetic_bayer_changed_pixel_fraction": 0.0001,
            "maximum_synthetic_bayer_mean_absolute_channel_delta": 0.01,
            "maximum_coverage_ratio_error": 0.01,
            "maximum_combined_transition_overhead_above_larger_control": 0.015,
        },
        "decision": {
            "retain": [
                "V32 complementary screen-ownership mechanism",
                "V33 17-sample ordered path precursor",
                "traditional-raster source wood for dynamic transition masking",
            ]
            if path_precursor_gate_passed
            else ["V30 registered authored-distance perspective flat proxy"],
            "reject": [
                "Nanite source wood for this dynamic screen-mask implementation",
                "ordered reload captures as proof of same-world temporal stability",
                "validation-only captures as lit art or production approval",
            ],
            "next_step": (
                "Run a persistent same-world moving-camera sequence with temporal history, "
                "motion vectors, target frame pacing, and lit art review; then profile the "
                "raster woody source or replace it with a transition-compatible optimized mesh."
            ),
        },
        "ordered_path_precursor_gate_passed": path_precursor_gate_passed,
        "v33_path_precursor_retained": path_precursor_gate_passed,
        "nanite_source_woody_transition_retained": False,
        "traditional_raster_source_woody_transition_retained": (
            path_precursor_gate_passed
        ),
        "same_world_moving_camera_temporal_gate_passed": False,
        "underlying_no_pop_gate_passed": False,
        "lit_art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v33_temporal_transition_path_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
