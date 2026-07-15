"""Compare registered orthographic and authored-distance perspective HLOD bakes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v29_azimuth_registration import (
    DISTANCES,
    EXPECTED_AUTHORITY,
    V29_NAMESPACE,
    V29_REPORT,
    _label_paths,
)


V30_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveHlod"
    "CalibratedIrregularCrownMassCompoundBranchletAtlas"
)
V30_REPORT = (
    "futaleufu_cordillera_cypress_v30_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_"
    "compound_branchlet_atlas_report.json"
)
ATLAS_CHANNELS = ("base_color_opacity", "world_normal", "opacity", "depth")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v29_orthographic": capture_root / V29_NAMESPACE,
        "v30_perspective": capture_root / V30_NAMESPACE,
    }
    reports = {
        "v29_orthographic": json.loads(
            (report_root / V29_REPORT).read_text(encoding="utf-8")
        ),
        "v30_perspective": json.loads(
            (report_root / V30_REPORT).read_text(encoding="utf-8")
        ),
    }

    comparisons = {}
    source_control_changes = []
    hlod_projection_changes = []
    v29_no_pop_changes = []
    v30_no_pop_changes = []
    v29_no_pop_ious = []
    v30_no_pop_ious = []
    hard_authority_gate_passed = True
    for distance in DISTANCES:
        filenames = {
            authority: f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        v29_source = roots["v29_orthographic"] / filenames["source_only"]
        v30_source = roots["v30_perspective"] / filenames["source_only"]
        v29_hlod = roots["v29_orthographic"] / filenames["hlod_only"]
        v30_hlod = roots["v30_perspective"] / filenames["hlod_only"]
        v30_combined = roots["v30_perspective"] / filenames["combined"]

        source_control = _label_paths(
            _comparison(v29_source, v30_source),
            f"v29_orthographic/{filenames['source_only']}",
            f"v30_perspective/{filenames['source_only']}",
        )
        hlod_projection = _label_paths(
            _comparison(v29_hlod, v30_hlod),
            f"v29_orthographic/{filenames['hlod_only']}",
            f"v30_perspective/{filenames['hlod_only']}",
        )
        v29_no_pop = _label_paths(
            _comparison(v29_source, v29_hlod),
            f"v29_orthographic/{filenames['source_only']}",
            f"v29_orthographic/{filenames['hlod_only']}",
        )
        v30_no_pop = _label_paths(
            _comparison(v30_source, v30_hlod),
            f"v30_perspective/{filenames['source_only']}",
            f"v30_perspective/{filenames['hlod_only']}",
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        expected = v30_source if expected_authority == "source_only" else v30_hlod
        authority = _label_paths(
            _comparison(expected, v30_combined),
            f"v30_perspective/{filenames[expected_authority]}",
            f"v30_perspective/{filenames['combined']}",
        )
        authority_equivalent = (
            authority["before"]["sha256"] == authority["after"]["sha256"]
            or (
                authority["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
                and authority["mean_absolute_channel_delta"] <= 0.01
                and authority["dark_chromatic_foreground_intersection_over_union"]
                >= 0.9999
            )
        )
        hard_authority_gate_passed &= authority_equivalent

        source_control_changes.append(
            source_control["changed_pixel_fraction_max_channel_gt_12"]
        )
        hlod_projection_changes.append(
            hlod_projection["changed_pixel_fraction_max_channel_gt_12"]
        )
        v29_no_pop_changes.append(
            v29_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v30_no_pop_changes.append(
            v30_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v29_no_pop_ious.append(
            v29_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        v30_no_pop_ious.append(
            v30_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        comparisons[distance] = {
            "expected_authority": expected_authority,
            "v29_to_v30_source_control": source_control,
            "v29_to_v30_hlod_projection_change": hlod_projection,
            "v29_source_to_hlod": v29_no_pop,
            "v30_source_to_hlod": v30_no_pop,
            "v30_combined_to_expected": authority,
            "v30_authority_equivalent": authority_equivalent,
        }

    repeatability = {"handoffs": {}, "atlas_channels": {}}
    repeat_source_changes = []
    repeat_hlod_changes = []
    repeat_combined_changes = []
    for distance in DISTANCES:
        distance_result = {}
        for authority in ("source_only", "hlod_only", "combined"):
            name = f"open_grown_conical_handoff_{distance}_{authority}.png"
            comparison = _label_paths(
                _comparison(args.run_a_root / name, roots["v30_perspective"] / name),
                f"run_a_snapshot/{name}",
                f"run_b_regenerated/{name}",
            )
            distance_result[f"{authority}_run_a_to_run_b"] = comparison
            changed = comparison["changed_pixel_fraction_max_channel_gt_12"]
            if authority == "source_only":
                repeat_source_changes.append(changed)
            elif authority == "hlod_only":
                repeat_hlod_changes.append(changed)
            else:
                repeat_combined_changes.append(changed)
        repeatability["handoffs"][distance] = distance_result

    repeat_atlas_changes = []
    for channel in ATLAS_CHANNELS:
        name = f"open_grown_conical_multiview_atlas_{channel}.png"
        comparison = _label_paths(
            _comparison(args.run_a_root / name, roots["v30_perspective"] / name),
            f"run_a_snapshot/{name}",
            f"run_b_regenerated/{name}",
        )
        repeatability["atlas_channels"][channel] = comparison
        repeat_atlas_changes.append(
            comparison["changed_pixel_fraction_max_channel_gt_12"]
        )
    template_name = "open_grown_conical_foliage_template.json"
    template_hashes = {
        "run_a": _sha256(args.run_a_root / template_name),
        "run_b": _sha256(roots["v30_perspective"] / template_name),
    }
    foliage_template_exact = template_hashes["run_a"] == template_hashes["run_b"]
    repeatability_gate_passed = (
        foliage_template_exact
        and max(repeat_source_changes) <= 0.012
        and max(repeat_hlod_changes) <= 0.015
        and max(repeat_atlas_changes) <= 0.020
    )

    source_geometry_unchanged = (
        reports["v29_orthographic"]["generated_collection"][
            "foliage_instance_count"
        ]
        == reports["v30_perspective"]["generated_collection"][
            "foliage_instance_count"
        ]
        and reports["v29_orthographic"]["local_impostor_source"][
            "triangle_count_lod0"
        ]
        == reports["v30_perspective"]["local_impostor_source"][
            "triangle_count_lod0"
        ]
    )
    v29_hlod = reports["v29_orthographic"]["local_multi_view_atlas_hlod"]
    v30_hlod = reports["v30_perspective"]["local_multi_view_atlas_hlod"]
    validation_contracts_match = (
        v29_hlod["source_wpo_contract"] == v30_hlod["source_wpo_contract"]
        and v29_hlod["deterministic_capture_contract"]
        == v30_hlod["deterministic_capture_contract"]
        and v29_hlod["atlas_color_gain"] == v30_hlod["atlas_color_gain"]
        and v29_hlod["view_contract"] == v30_hlod["view_contract"]
        and v29_hlod["orthographic_width_cm"] == v30_hlod["orthographic_width_cm"]
    )
    v29_projection = v29_hlod.get(
        "projection_contract",
        {
            "type": "orthographic",
            "proxy_plane_width_cm": v29_hlod["orthographic_width_cm"],
        },
    )
    v30_projection = v30_hlod["projection_contract"]
    projection_isolation_valid = (
        source_geometry_unchanged
        and validation_contracts_match
        and max(source_control_changes) <= 0.012
        and repeatability_gate_passed
        and v29_projection["type"] == "orthographic"
        and v30_projection["type"] == "perspective"
        and v30_projection["capture_radius_cm"] == 2912.043945
        and 50.0 <= v30_projection["perspective_horizontal_fov_degrees"] <= 51.0
    )
    no_pop_delta_change = [
        after - before for before, after in zip(v29_no_pop_changes, v30_no_pop_changes)
    ]
    no_pop_iou_change = [
        after - before for before, after in zip(v29_no_pop_ious, v30_no_pop_ious)
    ]
    active_hlod_indices = (1, 2)
    perspective_improves_active_hlod_handoffs = all(
        no_pop_delta_change[index] < 0.0 and no_pop_iou_change[index] > 0.0
        for index in active_hlod_indices
    )
    source_authority_distance_bounded = (
        no_pop_delta_change[0] <= 0.012 and no_pop_iou_change[0] >= -0.012
    )
    v30_no_pop_gate_passed = (
        max(v30_no_pop_changes) <= 0.10 and min(v30_no_pop_ious) >= 0.90
    )
    perspective_retained = (
        projection_isolation_valid
        and perspective_improves_active_hlod_handoffs
        and source_authority_distance_bounded
    )
    status = (
        "authored_distance_perspective_retained_no_pop_gate_still_open"
        if perspective_retained and not v30_no_pop_gate_passed
        else "authored_distance_perspective_rejected"
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_projection_review.v30",
        "river_id": "futaleufu_terminator",
        "candidate": "v30_registered_authored_distance_perspective_test",
        "status": status,
        "comparison_contract": {
            "fixed": [
                "V24 source geometry and generated foliage transforms",
                "V25 atlas gain and hard 2500 centimeter authority",
                "V27 frozen-WPO 512-pixel deterministic validation profile",
                "V29 16-degree azimuth registration, view count, elevation rows, and output channels",
            ],
            "only_intended_change": (
                "orthographic capture to perspective capture at the authored 28 m radial camera distance"
            ),
            "art_review_allowed": False,
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "validation_contracts_match": validation_contracts_match,
        "projection_isolation_valid": projection_isolation_valid,
        "projection_contracts": {
            "v29": v29_projection,
            "v30": v30_projection,
        },
        "repeatability_evidence": {
            "run_a_snapshot_not_committed": True,
            "regeneration_instruction": (
                "Run the V30 command twice, preserve the first namespace, and pass it as --run-a-root."
            ),
            "foliage_template_sha256": template_hashes,
            "foliage_template_exact": foliage_template_exact,
            "handoffs": repeatability["handoffs"],
            "atlas_channels": repeatability["atlas_channels"],
            "derived_findings": {
                "source_changed_pixel_fractions_at_20_28_36m": (
                    repeat_source_changes
                ),
                "hlod_changed_pixel_fractions_at_20_28_36m": (
                    repeat_hlod_changes
                ),
                "combined_changed_pixel_fractions_at_20_28_36m": (
                    repeat_combined_changes
                ),
                "atlas_channel_changed_pixel_fraction_range": [
                    min(repeat_atlas_changes),
                    max(repeat_atlas_changes),
                ],
            },
            "thresholds": {
                "maximum_source_changed_pixel_fraction": 0.012,
                "maximum_hlod_changed_pixel_fraction": 0.015,
                "maximum_atlas_channel_changed_pixel_fraction": 0.020,
            },
            "repeatability_gate_passed": repeatability_gate_passed,
        },
        "distance_comparisons": comparisons,
        "derived_findings": {
            "source_control_changed_pixel_fractions_at_20_28_36m": (
                source_control_changes
            ),
            "hlod_projection_changed_pixel_fractions_at_20_28_36m": (
                hlod_projection_changes
            ),
            "v29_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v29_no_pop_changes
            ),
            "v30_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v30_no_pop_changes
            ),
            "v29_source_hlod_foreground_iou_at_20_28_36m": v29_no_pop_ious,
            "v30_source_hlod_foreground_iou_at_20_28_36m": v30_no_pop_ious,
            "v30_minus_v29_changed_pixel_fraction_at_20_28_36m": (
                no_pop_delta_change
            ),
            "v30_minus_v29_foreground_iou_at_20_28_36m": no_pop_iou_change,
        },
        "hard_authority_gate_passed": hard_authority_gate_passed,
        "perspective_improves_active_hlod_handoffs": (
            perspective_improves_active_hlod_handoffs
        ),
        "source_authority_distance_bounded": source_authority_distance_bounded,
        "v30_no_pop_gate_passed": v30_no_pop_gate_passed,
        "editor_exit_boundary": {
            "evaluation_completed": True,
            "request_exit_logged": True,
            "first_execution_post_completion_shutdown_required_interrupt": True,
            "exact_rerun_completed_cleanly": True,
        },
        "decision": {
            "retain": [
                "V27 deterministic 512 validation profile",
                "V29 16-degree azimuth registration",
                "V30 authored-distance perspective capture",
            ]
            if perspective_retained
            else [
                "V27 deterministic 512 validation profile",
                "V29 16-degree azimuth registration",
            ],
            "reject": [
                "V30 as a completed no-pop or photoreal-art solution",
                "projection correction as the only remaining representation fix",
            ],
            "next_step": (
                "Keep the registered perspective bake and isolate depth-aware representation shape before complementary dither."
                if perspective_retained
                else "Keep V29 and isolate depth-aware representation shape before complementary dither."
            ),
        },
        "v29_azimuth_registration_retained": True,
        "v30_perspective_capture_retained": perspective_retained,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v30_perspective_projection_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
