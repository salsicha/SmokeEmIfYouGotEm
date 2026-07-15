"""Compare the V27 cypress HLOD against a handoff-aligned azimuth grid."""

from __future__ import annotations

import json
import math
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)


DISTANCES = ("20m", "28m", "36m")
DISTANCES_CM = {"20m": 2000.0, "28m": 2800.0, "36m": 3600.0}
EXPECTED_AUTHORITY = {"20m": "source_only", "28m": "hlod_only", "36m": "hlod_only"}
CAMERA_LATERAL_OFFSET_CM = -800.0
V27_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMass"
    "CompoundBranchletAtlas"
)
V29_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredHlodCalibrated"
    "IrregularCrownMassCompoundBranchletAtlas"
)
V27_REPORT = (
    "futaleufu_cordillera_cypress_v27_pve_open_grown_conical_frozen_wpo_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
V29_REPORT = (
    "futaleufu_cordillera_cypress_v29_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_"
    "branchlet_atlas_report.json"
)


def _label_paths(comparison: dict, before_label: str, after_label: str) -> dict:
    comparison["before"]["path"] = before_label
    comparison["after"]["path"] = after_label
    return comparison


def _nearest_frame_error_degrees(angle_degrees: float, offset_degrees: float) -> float:
    frame = round((angle_degrees - offset_degrees) / 45.0)
    nearest = (offset_degrees + frame * 45.0) % 360.0
    return abs((angle_degrees - nearest + 180.0) % 360.0 - 180.0)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v27_zero_degree_grid": capture_root / V27_NAMESPACE,
        "v29_16_degree_grid": capture_root / V29_NAMESPACE,
    }
    reports = {
        "v27_zero_degree_grid": json.loads(
            (report_root / V27_REPORT).read_text(encoding="utf-8")
        ),
        "v29_16_degree_grid": json.loads(
            (report_root / V29_REPORT).read_text(encoding="utf-8")
        ),
    }

    comparisons = {}
    source_control_changes = []
    hlod_grid_changes = []
    v27_no_pop_changes = []
    v29_no_pop_changes = []
    v27_no_pop_ious = []
    v29_no_pop_ious = []
    hard_authority_gate_passed = True
    camera_azimuths = {}
    v27_frame_errors = []
    v29_frame_errors = []
    for distance in DISTANCES:
        filenames = {
            authority: f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        v27_source = roots["v27_zero_degree_grid"] / filenames["source_only"]
        v29_source = roots["v29_16_degree_grid"] / filenames["source_only"]
        v27_hlod = roots["v27_zero_degree_grid"] / filenames["hlod_only"]
        v29_hlod = roots["v29_16_degree_grid"] / filenames["hlod_only"]
        v29_combined = roots["v29_16_degree_grid"] / filenames["combined"]

        source_control = _label_paths(
            _comparison(v27_source, v29_source),
            f"v27_zero_degree_grid/{filenames['source_only']}",
            f"v29_16_degree_grid/{filenames['source_only']}",
        )
        hlod_grid_change = _label_paths(
            _comparison(v27_hlod, v29_hlod),
            f"v27_zero_degree_grid/{filenames['hlod_only']}",
            f"v29_16_degree_grid/{filenames['hlod_only']}",
        )
        v27_no_pop = _label_paths(
            _comparison(v27_source, v27_hlod),
            f"v27_zero_degree_grid/{filenames['source_only']}",
            f"v27_zero_degree_grid/{filenames['hlod_only']}",
        )
        v29_no_pop = _label_paths(
            _comparison(v29_source, v29_hlod),
            f"v29_16_degree_grid/{filenames['source_only']}",
            f"v29_16_degree_grid/{filenames['hlod_only']}",
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        expected = v29_source if expected_authority == "source_only" else v29_hlod
        authority = _label_paths(
            _comparison(expected, v29_combined),
            f"v29_16_degree_grid/{filenames[expected_authority]}",
            f"v29_16_degree_grid/{filenames['combined']}",
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
        hlod_grid_changes.append(
            hlod_grid_change["changed_pixel_fraction_max_channel_gt_12"]
        )
        v27_no_pop_changes.append(
            v27_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v29_no_pop_changes.append(
            v29_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v27_no_pop_ious.append(
            v27_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        v29_no_pop_ious.append(
            v29_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        authored_azimuth = math.degrees(
            math.atan2(CAMERA_LATERAL_OFFSET_CM, -DISTANCES_CM[distance])
        ) % 360.0
        camera_azimuths[distance] = authored_azimuth
        v27_error = _nearest_frame_error_degrees(authored_azimuth, 0.0)
        v29_error = _nearest_frame_error_degrees(authored_azimuth, 16.0)
        v27_frame_errors.append(v27_error)
        v29_frame_errors.append(v29_error)
        comparisons[distance] = {
            "authored_camera_azimuth_degrees": authored_azimuth,
            "v27_nearest_frame_error_degrees": v27_error,
            "v29_nearest_frame_error_degrees": v29_error,
            "expected_authority": expected_authority,
            "v27_to_v29_source_control": source_control,
            "v27_to_v29_hlod_grid_change": hlod_grid_change,
            "v27_source_to_hlod": v27_no_pop,
            "v29_source_to_hlod": v29_no_pop,
            "v29_combined_to_expected": authority,
            "v29_authority_equivalent": authority_equivalent,
        }

    source_geometry_unchanged = (
        reports["v27_zero_degree_grid"]["generated_collection"][
            "foliage_instance_count"
        ]
        == reports["v29_16_degree_grid"]["generated_collection"][
            "foliage_instance_count"
        ]
        and reports["v27_zero_degree_grid"]["local_impostor_source"][
            "triangle_count_lod0"
        ]
        == reports["v29_16_degree_grid"]["local_impostor_source"][
            "triangle_count_lod0"
        ]
    )
    v27_hlod = reports["v27_zero_degree_grid"]["local_multi_view_atlas_hlod"]
    v29_hlod = reports["v29_16_degree_grid"]["local_multi_view_atlas_hlod"]
    validation_contracts_match = (
        v27_hlod["source_wpo_contract"] == v29_hlod["source_wpo_contract"]
        and v27_hlod["deterministic_capture_contract"]
        == v29_hlod["deterministic_capture_contract"]
        and v27_hlod["atlas_color_gain"] == v29_hlod["atlas_color_gain"]
        and v27_hlod["view_contract"]["tile_resolution"]
        == v29_hlod["view_contract"]["tile_resolution"]
        and v27_hlod["view_contract"]["atlas_resolution"]
        == v29_hlod["view_contract"]["atlas_resolution"]
    )
    azimuth_isolation_valid = (
        source_geometry_unchanged
        and validation_contracts_match
        and max(source_control_changes) <= 0.012
        and v27_hlod["view_contract"].get("azimuth_offset_degrees", 0.0) == 0.0
        and v29_hlod["view_contract"]["azimuth_offset_degrees"] == 16.0
    )
    no_pop_delta_change = [
        after - before for before, after in zip(v27_no_pop_changes, v29_no_pop_changes)
    ]
    no_pop_iou_change = [
        after - before for before, after in zip(v27_no_pop_ious, v29_no_pop_ious)
    ]
    azimuth_registration_improves_no_pop = all(
        value < 0.0 for value in no_pop_delta_change
    ) and all(value > 0.0 for value in no_pop_iou_change)
    v29_no_pop_gate_passed = (
        max(v29_no_pop_changes) <= 0.10 and min(v29_no_pop_ious) >= 0.90
    )
    registration_retained = (
        azimuth_isolation_valid and azimuth_registration_improves_no_pop
    )
    status = (
        "azimuth_registration_retained_no_pop_gate_still_open"
        if registration_retained and not v29_no_pop_gate_passed
        else "azimuth_registration_rejected"
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_azimuth_registration_review.v29",
        "river_id": "futaleufu_terminator",
        "candidate": "v29_frozen_wpo_16_degree_azimuth_registration_test",
        "status": status,
        "comparison_contract": {
            "fixed": [
                "V24 source geometry and generated foliage transforms",
                "V25 atlas gain and hard 2500 centimeter authority",
                "V27 frozen-WPO 512-pixel unlit deterministic validation profile",
                "sixteen views, elevation rows, orthographic projection, and output channels",
            ],
            "only_intended_change": (
                "capture and runtime frame-selection azimuth offset from 0 to 16 degrees"
            ),
            "art_review_allowed": False,
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "validation_contracts_match": validation_contracts_match,
        "azimuth_isolation_valid": azimuth_isolation_valid,
        "authored_handoff_geometry": {
            "camera_lateral_offset_cm": CAMERA_LATERAL_OFFSET_CM,
            "camera_azimuth_degrees_at_20_28_36m": [
                camera_azimuths[distance] for distance in DISTANCES
            ],
            "v27_nearest_frame_errors_degrees_at_20_28_36m": v27_frame_errors,
            "v29_nearest_frame_errors_degrees_at_20_28_36m": v29_frame_errors,
        },
        "distance_comparisons": comparisons,
        "derived_findings": {
            "source_control_changed_pixel_fractions_at_20_28_36m": (
                source_control_changes
            ),
            "hlod_azimuth_grid_changed_pixel_fractions_at_20_28_36m": (
                hlod_grid_changes
            ),
            "v27_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v27_no_pop_changes
            ),
            "v29_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v29_no_pop_changes
            ),
            "v27_source_hlod_foreground_iou_at_20_28_36m": v27_no_pop_ious,
            "v29_source_hlod_foreground_iou_at_20_28_36m": v29_no_pop_ious,
            "v29_minus_v27_changed_pixel_fraction_at_20_28_36m": (
                no_pop_delta_change
            ),
            "v29_minus_v27_foreground_iou_at_20_28_36m": no_pop_iou_change,
        },
        "hard_authority_gate_passed": hard_authority_gate_passed,
        "azimuth_registration_improves_no_pop": (
            azimuth_registration_improves_no_pop
        ),
        "v29_no_pop_gate_passed": v29_no_pop_gate_passed,
        "decision": {
            "retain": [
                "V27 deterministic 512 validation profile",
                "16-degree authored-handoff azimuth registration mechanism",
            ]
            if registration_retained
            else ["V27 deterministic 512 validation profile"],
            "reject": [
                "V29 as a completed no-pop or photoreal-art solution",
                "azimuth registration as the only remaining representation fix",
            ],
            "next_step": (
                "Keep the registered frame grid and isolate projection or depth-aware "
                "representation shape before evaluating complementary dither."
                if registration_retained
                else "Retain V27 and isolate projection or depth-aware representation shape."
            ),
        },
        "v27_validation_baseline_retained": True,
        "v29_azimuth_registration_retained": registration_retained,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v29_azimuth_registration_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
