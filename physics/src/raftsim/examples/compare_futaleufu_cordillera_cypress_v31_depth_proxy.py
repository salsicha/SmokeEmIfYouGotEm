"""Compare matched flat and depth-displaced registered perspective HLOD proxies."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v29_azimuth_registration import (
    DISTANCES,
    EXPECTED_AUTHORITY,
    _label_paths,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v30_perspective_projection import (
    V30_NAMESPACE,
    V30_REPORT,
)


V31_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveDepthHlod"
    "CalibratedIrregularCrownMassCompoundBranchletAtlas"
)
V31_REPORT = (
    "futaleufu_cordillera_cypress_v31_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_"
    "mass_compound_branchlet_atlas_report.json"
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v30_flat": capture_root / V30_NAMESPACE,
        "v31_depth": capture_root / V31_NAMESPACE,
    }
    reports = {
        "v30_flat": json.loads((report_root / V30_REPORT).read_text(encoding="utf-8")),
        "v31_depth": json.loads((report_root / V31_REPORT).read_text(encoding="utf-8")),
    }

    comparisons = {}
    source_control_changes = []
    hlod_shape_changes = []
    v30_no_pop_changes = []
    v31_no_pop_changes = []
    v30_no_pop_ious = []
    v31_no_pop_ious = []
    hard_authority_gate_passed = True
    for distance in DISTANCES:
        filenames = {
            authority: f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        v30_source = roots["v30_flat"] / filenames["source_only"]
        v31_source = roots["v31_depth"] / filenames["source_only"]
        v30_hlod = roots["v30_flat"] / filenames["hlod_only"]
        v31_hlod = roots["v31_depth"] / filenames["hlod_only"]
        v31_combined = roots["v31_depth"] / filenames["combined"]

        source_control = _label_paths(
            _comparison(v30_source, v31_source),
            f"v30_flat/{filenames['source_only']}",
            f"v31_depth/{filenames['source_only']}",
        )
        hlod_shape = _label_paths(
            _comparison(v30_hlod, v31_hlod),
            f"v30_flat/{filenames['hlod_only']}",
            f"v31_depth/{filenames['hlod_only']}",
        )
        v30_no_pop = _label_paths(
            _comparison(v30_source, v30_hlod),
            f"v30_flat/{filenames['source_only']}",
            f"v30_flat/{filenames['hlod_only']}",
        )
        v31_no_pop = _label_paths(
            _comparison(v31_source, v31_hlod),
            f"v31_depth/{filenames['source_only']}",
            f"v31_depth/{filenames['hlod_only']}",
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        expected = v31_source if expected_authority == "source_only" else v31_hlod
        authority = _label_paths(
            _comparison(expected, v31_combined),
            f"v31_depth/{filenames[expected_authority]}",
            f"v31_depth/{filenames['combined']}",
        )
        authority_equivalent = authority["before"]["sha256"] == authority["after"][
            "sha256"
        ] or (
            authority["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
            and authority["mean_absolute_channel_delta"] <= 0.01
            and authority["dark_chromatic_foreground_intersection_over_union"] >= 0.9999
        )
        hard_authority_gate_passed &= authority_equivalent

        source_control_changes.append(
            source_control["changed_pixel_fraction_max_channel_gt_12"]
        )
        hlod_shape_changes.append(
            hlod_shape["changed_pixel_fraction_max_channel_gt_12"]
        )
        v30_no_pop_changes.append(
            v30_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v31_no_pop_changes.append(
            v31_no_pop["changed_pixel_fraction_max_channel_gt_12"]
        )
        v30_no_pop_ious.append(
            v30_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        v31_no_pop_ious.append(
            v31_no_pop["dark_chromatic_foreground_intersection_over_union"]
        )
        comparisons[distance] = {
            "expected_authority": expected_authority,
            "v30_to_v31_source_control": source_control,
            "v30_to_v31_hlod_representation_shape_change": hlod_shape,
            "v30_source_to_hlod": v30_no_pop,
            "v31_source_to_hlod": v31_no_pop,
            "v31_combined_to_expected": authority,
            "v31_authority_equivalent": authority_equivalent,
        }

    source_geometry_unchanged = (
        reports["v30_flat"]["generated_collection"]["foliage_instance_count"]
        == reports["v31_depth"]["generated_collection"]["foliage_instance_count"]
        and reports["v30_flat"]["local_impostor_source"]["triangle_count_lod0"]
        == reports["v31_depth"]["local_impostor_source"]["triangle_count_lod0"]
    )
    v30_hlod = reports["v30_flat"]["local_multi_view_atlas_hlod"]
    v31_hlod = reports["v31_depth"]["local_multi_view_atlas_hlod"]
    validation_contracts_match = (
        v30_hlod["source_wpo_contract"] == v31_hlod["source_wpo_contract"]
        and v30_hlod["deterministic_capture_contract"]
        == v31_hlod["deterministic_capture_contract"]
        and v30_hlod["atlas_color_gain"] == v31_hlod["atlas_color_gain"]
        and v30_hlod["view_contract"] == v31_hlod["view_contract"]
        and v30_hlod["orthographic_width_cm"] == v31_hlod["orthographic_width_cm"]
        and v30_hlod["projection_contract"] == v31_hlod["projection_contract"]
    )
    v30_shape = v30_hlod.get(
        "representation_shape_contract",
        {
            "type": "flat_billboard",
            "depth_parallax_enabled": False,
        },
    )
    v31_shape = v31_hlod["representation_shape_contract"]
    representation_contract_valid = (
        v30_shape["type"] == "flat_billboard"
        and v30_shape["depth_parallax_enabled"] is False
        and v31_shape["type"] == "32x32_tessellated_depth_displaced_billboard"
        and v31_shape["depth_parallax_enabled"] is True
        and v31_shape["proxy_vertex_count"] == 1089
        and v31_shape["proxy_triangle_count"] == 2048
        and 1400.0 <= v31_shape["depth_parallax_scale_cm"] <= 1450.0
    )
    shape_isolation_valid = (
        source_geometry_unchanged
        and validation_contracts_match
        and representation_contract_valid
        and max(source_control_changes) <= 0.012
    )
    no_pop_delta_change = [
        after - before for before, after in zip(v30_no_pop_changes, v31_no_pop_changes)
    ]
    no_pop_iou_change = [
        after - before for before, after in zip(v30_no_pop_ious, v31_no_pop_ious)
    ]
    depth_shape_improves_no_pop = all(
        value < 0.0 for value in no_pop_delta_change
    ) and all(value > 0.0 for value in no_pop_iou_change)
    v31_no_pop_gate_passed = (
        max(v31_no_pop_changes) <= 0.10 and min(v31_no_pop_ious) >= 0.90
    )
    depth_proxy_retained = shape_isolation_valid and depth_shape_improves_no_pop

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_depth_proxy_review.v31",
        "river_id": "futaleufu_terminator",
        "candidate": "v31_registered_perspective_depth_displaced_proxy_test",
        "status": "depth_displaced_proxy_rejected_v30_flat_proxy_retained",
        "comparison_contract": {
            "fixed": [
                "V24 source geometry and generated foliage transforms",
                "V25 atlas gain and hard 2500 centimeter authority",
                "V27 frozen-WPO 512-pixel deterministic validation profile",
                "V29 16-degree azimuth registration",
                "V30 authored-distance perspective projection and proxy span",
            ],
            "only_intended_change": (
                "flat billboard to 32x32 tessellated proxy displaced at vertices by "
                "the normalized selected-view depth atlas over measured horizontal "
                "source span"
            ),
            "art_review_allowed": False,
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "validation_contracts_match": validation_contracts_match,
        "representation_contract_valid": representation_contract_valid,
        "shape_isolation_valid": shape_isolation_valid,
        "representation_shape_contracts": {
            "v30": v30_shape,
            "v31": v31_shape,
        },
        "distance_comparisons": comparisons,
        "derived_findings": {
            "source_control_changed_pixel_fractions_at_20_28_36m": (
                source_control_changes
            ),
            "hlod_shape_changed_pixel_fractions_at_20_28_36m": hlod_shape_changes,
            "v30_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v30_no_pop_changes
            ),
            "v31_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v31_no_pop_changes
            ),
            "v30_source_hlod_foreground_iou_at_20_28_36m": v30_no_pop_ious,
            "v31_source_hlod_foreground_iou_at_20_28_36m": v31_no_pop_ious,
            "v31_minus_v30_changed_pixel_fraction_at_20_28_36m": (no_pop_delta_change),
            "v31_minus_v30_foreground_iou_at_20_28_36m": no_pop_iou_change,
        },
        "hard_authority_gate_passed": hard_authority_gate_passed,
        "depth_shape_improves_no_pop": depth_shape_improves_no_pop,
        "v31_no_pop_gate_passed": v31_no_pop_gate_passed,
        "decision": {
            "retain": [
                "V30 registered authored-distance perspective flat proxy",
                "bounded 32x32 depth-proxy generation path for later diagnostics",
                "explicit representation-shape manifest contract",
            ],
            "reject": [
                "V31 normalized-depth whole-span displacement as a runtime profile",
                "depth displacement as the current no-pop solution",
                "art, corridor, or all-form promotion from validation-only captures",
            ],
            "next_step": (
                "Keep V30 and evaluate a bounded complementary dither transition at "
                "the 25 m authority boundary before returning to lit art review."
            ),
        },
        "v30_perspective_flat_proxy_retained": True,
        "v31_depth_displaced_proxy_retained": depth_proxy_retained,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root / "futaleufu_cordillera_cypress_v31_depth_proxy_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
