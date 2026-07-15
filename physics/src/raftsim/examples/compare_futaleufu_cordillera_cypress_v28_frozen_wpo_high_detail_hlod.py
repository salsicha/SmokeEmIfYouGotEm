"""Compare matched frozen-WPO 512 and 1024 cypress HLOD profiles."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)


DISTANCES = ("20m", "28m", "36m")
EXPECTED_AUTHORITY = {"20m": "source_only", "28m": "hlod_only", "36m": "hlod_only"}
V27_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMass"
    "CompoundBranchletAtlas"
)
V28_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoHighDetailHlodCalibratedIrregular"
    "CrownMassCompoundBranchletAtlas"
)
V27_REPORT = (
    "futaleufu_cordillera_cypress_v27_pve_open_grown_conical_frozen_wpo_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
V28_REPORT = (
    "futaleufu_cordillera_cypress_v28_pve_open_grown_conical_frozen_wpo_"
    "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_"
    "report.json"
)


def _label_paths(comparison: dict, before_label: str, after_label: str) -> dict:
    comparison["before"]["path"] = before_label
    comparison["after"]["path"] = after_label
    return comparison


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v27_512": capture_root / V27_NAMESPACE,
        "v28_1024": capture_root / V28_NAMESPACE,
    }
    reports = {
        "v27_512": json.loads((report_root / V27_REPORT).read_text(encoding="utf-8")),
        "v28_1024": json.loads(
            (report_root / V28_REPORT).read_text(encoding="utf-8")
        ),
    }

    comparisons = {}
    source_control_changes = []
    hlod_resolution_changes = []
    v27_no_pop_changes = []
    v28_no_pop_changes = []
    v27_no_pop_ious = []
    v28_no_pop_ious = []
    hard_authority_gate_passed = True
    for distance in DISTANCES:
        filenames = {
            authority: f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        v27_source = roots["v27_512"] / filenames["source_only"]
        v28_source = roots["v28_1024"] / filenames["source_only"]
        v27_hlod = roots["v27_512"] / filenames["hlod_only"]
        v28_hlod = roots["v28_1024"] / filenames["hlod_only"]
        v28_combined = roots["v28_1024"] / filenames["combined"]

        source_control = _label_paths(
            _comparison(v27_source, v28_source),
            f"v27_512/{filenames['source_only']}",
            f"v28_1024/{filenames['source_only']}",
        )
        hlod_resolution = _label_paths(
            _comparison(v27_hlod, v28_hlod),
            f"v27_512/{filenames['hlod_only']}",
            f"v28_1024/{filenames['hlod_only']}",
        )
        v27_no_pop = _label_paths(
            _comparison(v27_source, v27_hlod),
            f"v27_512/{filenames['source_only']}",
            f"v27_512/{filenames['hlod_only']}",
        )
        v28_no_pop = _label_paths(
            _comparison(v28_source, v28_hlod),
            f"v28_1024/{filenames['source_only']}",
            f"v28_1024/{filenames['hlod_only']}",
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        expected = v28_source if expected_authority == "source_only" else v28_hlod
        authority = _label_paths(
            _comparison(expected, v28_combined),
            f"v28_1024/{filenames[expected_authority]}",
            f"v28_1024/{filenames['combined']}",
        )
        authority_equivalent = (
            authority["before"]["sha256"] == authority["after"]["sha256"]
            or (
                authority["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
                and authority["mean_absolute_channel_delta"] <= 0.01
                and authority[
                    "dark_chromatic_foreground_intersection_over_union"
                ]
                >= 0.9999
            )
        )
        hard_authority_gate_passed &= authority_equivalent

        source_control_changes.append(
            source_control["changed_pixel_fraction_max_channel_gt_12"]
        )
        hlod_resolution_changes.append(
            hlod_resolution["changed_pixel_fraction_max_channel_gt_12"]
        )
        v27_no_pop_changes.append(
            v27_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v28_no_pop_changes.append(
            v28_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v27_no_pop_ious.append(
            v27_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        v28_no_pop_ious.append(
            v28_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        comparisons[distance] = {
            "expected_authority": expected_authority,
            "v27_to_v28_source_control": source_control,
            "v27_to_v28_hlod_resolution_change": hlod_resolution,
            "v27_source_to_hlod": v27_no_pop,
            "v28_source_to_hlod": v28_no_pop,
            "v28_combined_to_expected": authority,
            "v28_authority_equivalent": authority_equivalent,
        }

    source_geometry_unchanged = (
        reports["v27_512"]["generated_collection"]["foliage_instance_count"]
        == reports["v28_1024"]["generated_collection"]["foliage_instance_count"]
        and reports["v27_512"]["local_impostor_source"]["triangle_count_lod0"]
        == reports["v28_1024"]["local_impostor_source"]["triangle_count_lod0"]
    )
    v27_hlod = reports["v27_512"]["local_multi_view_atlas_hlod"]
    v28_hlod = reports["v28_1024"]["local_multi_view_atlas_hlod"]
    validation_contracts_match = (
        v27_hlod["source_wpo_contract"] == v28_hlod["source_wpo_contract"]
        and v27_hlod["deterministic_capture_contract"]
        == v28_hlod["deterministic_capture_contract"]
        and v27_hlod["atlas_color_gain"] == v28_hlod["atlas_color_gain"]
    )
    resolution_isolation_valid = (
        source_geometry_unchanged
        and validation_contracts_match
        and max(source_control_changes) <= 0.012
    )
    no_pop_delta_change = [
        after - before for before, after in zip(v27_no_pop_changes, v28_no_pop_changes)
    ]
    no_pop_iou_change = [
        after - before for before, after in zip(v27_no_pop_ious, v28_no_pop_ious)
    ]
    resolution_improves_no_pop = all(value < 0.0 for value in no_pop_delta_change) and all(
        value > 0.0 for value in no_pop_iou_change
    )
    v28_no_pop_gate_passed = (
        max(v28_no_pop_changes) <= 0.10 and min(v28_no_pop_ious) >= 0.90
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_frozen_wpo_resolution_review.v28",
        "river_id": "futaleufu_terminator",
        "candidate": "v28_frozen_wpo_1024px_per_view_resolution_test",
        "status": "high_detail_hlod_rejected_512_validation_baseline_retained",
        "comparison_contract": {
            "fixed": [
                "V24 source geometry and generated foliage transforms",
                "V25 atlas gain and hard 2500 centimeter authority",
                "V27 frozen-WPO and unlit deterministic validation profile",
                "sixteen-view camera and output-channel contract",
            ],
            "only_intended_change": "512 to 1024 pixels per view and 2048 to 4096 atlas pixels",
            "art_review_allowed": False,
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "validation_contracts_match": validation_contracts_match,
        "resolution_isolation_valid": resolution_isolation_valid,
        "atlas_resource_evidence": {
            "v27_view_contract": v27_hlod["view_contract"],
            "v28_view_contract": v28_hlod["view_contract"],
            "texel_area_ratio": 4.0,
            "uncompressed_four_rgba8_source_bytes": {
                "v27_512": 4 * 2048 * 2048 * 4,
                "v28_1024": 4 * 4096 * 4096 * 4,
            },
            "packaged_gpu_memory_not_measured": True,
        },
        "distance_comparisons": comparisons,
        "derived_findings": {
            "source_control_changed_pixel_fractions_at_20_28_36m": (
                source_control_changes
            ),
            "hlod_resolution_changed_pixel_fractions_at_20_28_36m": (
                hlod_resolution_changes
            ),
            "v27_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v27_no_pop_changes
            ),
            "v28_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v28_no_pop_changes
            ),
            "v27_source_hlod_foreground_iou_at_20_28_36m": v27_no_pop_ious,
            "v28_source_hlod_foreground_iou_at_20_28_36m": v28_no_pop_ious,
            "v28_minus_v27_changed_pixel_fraction_at_20_28_36m": (
                no_pop_delta_change
            ),
            "v28_minus_v27_foreground_iou_at_20_28_36m": no_pop_iou_change,
        },
        "hard_authority_gate_passed": hard_authority_gate_passed,
        "resolution_improves_no_pop": resolution_improves_no_pop,
        "v28_no_pop_gate_passed": v28_no_pop_gate_passed,
        "decision": {
            "retain": [
                "V27 512-pixel validation baseline",
                "flexible 512/1024 baker for later bounded diagnostics",
                "frozen-WPO and unlit isolation contracts",
            ],
            "reject": [
                "V28 1024-pixel runtime profile",
                "resolution-only handoff fix",
                "four-times atlas texel area without no-pop improvement",
            ],
            "next_step": "Keep 512 for validation and address HLOD spatial registration or representation shape, then evaluate a bounded complementary dither transition before returning to lit art review.",
        },
        "v27_validation_baseline_retained": True,
        "v28_high_detail_hlod_retained": False,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v28_frozen_wpo_resolution_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
