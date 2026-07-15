"""Validate the bounded complementary source/HLOD transition used by V32."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v29_azimuth_registration import (
    DISTANCES,
    EXPECTED_AUTHORITY,
    _label_paths,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v30_perspective_projection import (
    ATLAS_CHANNELS,
    V30_NAMESPACE,
    V30_REPORT,
)


V32_NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspective"
    "ComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"
)
V32_REPORT = (
    "futaleufu_cordillera_cypress_v32_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_complementary_transition_hlod_calibrated_"
    "irregular_crown_mass_compound_branchlet_atlas_report.json"
)
TRANSITION_DISTANCES = ("24m", "25m", "26m")
SOURCE_COVERAGE = {"24m": 0.75, "25m": 0.50, "26m": 0.25}
BAYER_4X4 = np.asarray(
    (
        (0, 8, 2, 10),
        (12, 4, 14, 6),
        (3, 11, 1, 9),
        (15, 7, 13, 5),
    ),
    dtype=np.float32,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_dither_metrics(
    source_path: Path,
    hlod_path: Path,
    combined_path: Path,
    source_coverage: float,
) -> dict:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.int16)
    hlod = np.asarray(Image.open(hlod_path).convert("RGB"), dtype=np.int16)
    combined = np.asarray(Image.open(combined_path).convert("RGB"), dtype=np.int16)
    height, width, _ = combined.shape
    ranks = np.tile(BAYER_4X4, (height // 4 + 1, width // 4 + 1))[:height, :width]
    source_owned = ranks < source_coverage * 16.0
    expected = np.where(source_owned[:, :, None], source, hlod)
    delta = np.abs(combined - expected)
    return {
        "expected_source_coverage": source_coverage,
        "expected_hlod_coverage": 1.0 - source_coverage,
        "changed_pixel_fraction_max_channel_gt_12": float(
            np.any(delta > 12, axis=2).mean()
        ),
        "mean_absolute_channel_delta": float(delta.mean()),
        "maximum_channel_delta": int(delta.max()),
        "exact_pixel_fraction": float(np.all(delta == 0, axis=2).mean()),
    }


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v30_hard": capture_root / V30_NAMESPACE,
        "v32_transition": capture_root / V32_NAMESPACE,
    }
    reports = {
        "v30_hard": json.loads((report_root / V30_REPORT).read_text(encoding="utf-8")),
        "v32_transition": json.loads(
            (report_root / V32_REPORT).read_text(encoding="utf-8")
        ),
    }

    endpoint_comparisons = {}
    endpoint_source_controls = []
    endpoint_hlod_controls = []
    hard_authority_gate_passed = True
    for distance in DISTANCES:
        filenames = {
            authority: f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        source_control = _label_paths(
            _comparison(
                roots["v30_hard"] / filenames["source_only"],
                roots["v32_transition"] / filenames["source_only"],
            ),
            f"v30_hard/{filenames['source_only']}",
            f"v32_transition/{filenames['source_only']}",
        )
        hlod_control = _label_paths(
            _comparison(
                roots["v30_hard"] / filenames["hlod_only"],
                roots["v32_transition"] / filenames["hlod_only"],
            ),
            f"v30_hard/{filenames['hlod_only']}",
            f"v32_transition/{filenames['hlod_only']}",
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        expected_path = roots["v32_transition"] / filenames[expected_authority]
        authority = _label_paths(
            _comparison(
                expected_path,
                roots["v32_transition"] / filenames["combined"],
            ),
            f"v32_transition/{filenames[expected_authority]}",
            f"v32_transition/{filenames['combined']}",
        )
        authority_equivalent = authority["before"]["sha256"] == authority["after"][
            "sha256"
        ] or (
            authority["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
            and authority["mean_absolute_channel_delta"] <= 0.01
            and authority["dark_chromatic_foreground_intersection_over_union"] >= 0.9999
        )
        hard_authority_gate_passed &= authority_equivalent
        endpoint_source_controls.append(
            source_control["changed_pixel_fraction_max_channel_gt_12"]
        )
        endpoint_hlod_controls.append(
            hlod_control["changed_pixel_fraction_max_channel_gt_12"]
        )
        endpoint_comparisons[distance] = {
            "expected_authority": expected_authority,
            "v30_to_v32_source_control": source_control,
            "v30_to_v32_hlod_control": hlod_control,
            "v32_combined_to_expected_endpoint_authority": authority,
            "v32_endpoint_authority_equivalent": authority_equivalent,
        }

    transition_comparisons = {}
    synthetic_changed = []
    synthetic_mad = []
    source_side_ratios = []
    hlod_side_ratios = []
    combined_to_source_changes = []
    combined_to_hlod_changes = []
    for distance in TRANSITION_DISTANCES:
        filenames = {
            authority: f"open_grown_conical_transition_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        source_path = roots["v32_transition"] / filenames["source_only"]
        hlod_path = roots["v32_transition"] / filenames["hlod_only"]
        combined_path = roots["v32_transition"] / filenames["combined"]
        source_to_hlod = _label_paths(
            _comparison(source_path, hlod_path),
            f"v32_transition/{filenames['source_only']}",
            f"v32_transition/{filenames['hlod_only']}",
        )
        combined_to_source = _label_paths(
            _comparison(source_path, combined_path),
            f"v32_transition/{filenames['source_only']}",
            f"v32_transition/{filenames['combined']}",
        )
        combined_to_hlod = _label_paths(
            _comparison(hlod_path, combined_path),
            f"v32_transition/{filenames['hlod_only']}",
            f"v32_transition/{filenames['combined']}",
        )
        synthetic = _synthetic_dither_metrics(
            source_path,
            hlod_path,
            combined_path,
            SOURCE_COVERAGE[distance],
        )
        full_change = source_to_hlod["changed_pixel_fraction_max_channel_gt_12"]
        source_ratio = (
            combined_to_source["changed_pixel_fraction_max_channel_gt_12"] / full_change
        )
        hlod_ratio = (
            combined_to_hlod["changed_pixel_fraction_max_channel_gt_12"] / full_change
        )
        source_side_ratios.append(source_ratio)
        hlod_side_ratios.append(hlod_ratio)
        synthetic_changed.append(synthetic["changed_pixel_fraction_max_channel_gt_12"])
        synthetic_mad.append(synthetic["mean_absolute_channel_delta"])
        combined_to_source_changes.append(
            combined_to_source["changed_pixel_fraction_max_channel_gt_12"]
        )
        combined_to_hlod_changes.append(
            combined_to_hlod["changed_pixel_fraction_max_channel_gt_12"]
        )
        transition_comparisons[distance] = {
            "source_coverage": SOURCE_COVERAGE[distance],
            "source_to_hlod": source_to_hlod,
            "combined_to_source": combined_to_source,
            "combined_to_hlod": combined_to_hlod,
            "observed_combined_to_source_fraction_of_full_change": source_ratio,
            "observed_combined_to_hlod_fraction_of_full_change": hlod_ratio,
            "synthetic_bayer_agreement": synthetic,
        }

    repeatability = {"transition": {}, "handoff": {}, "atlas_channels": {}}
    repeat_source_changes = []
    repeat_hlod_changes = []
    repeat_combined_changes = []
    for distance in TRANSITION_DISTANCES:
        distance_result = {}
        for authority in ("source_only", "hlod_only", "combined"):
            name = f"open_grown_conical_transition_{distance}_{authority}.png"
            comparison = _label_paths(
                _comparison(args.run_a_root / name, roots["v32_transition"] / name),
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
        repeatability["transition"][distance] = distance_result
    for distance in DISTANCES:
        distance_result = {}
        for authority in ("source_only", "hlod_only", "combined"):
            name = f"open_grown_conical_handoff_{distance}_{authority}.png"
            distance_result[f"{authority}_run_a_to_run_b"] = _label_paths(
                _comparison(args.run_a_root / name, roots["v32_transition"] / name),
                f"run_a_snapshot/{name}",
                f"run_b_regenerated/{name}",
            )
        repeatability["handoff"][distance] = distance_result
    repeat_atlas_changes = []
    for channel in ATLAS_CHANNELS:
        name = f"open_grown_conical_multiview_atlas_{channel}.png"
        comparison = _label_paths(
            _comparison(args.run_a_root / name, roots["v32_transition"] / name),
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
        "run_b": _sha256(roots["v32_transition"] / template_name),
    }
    foliage_template_exact = template_hashes["run_a"] == template_hashes["run_b"]
    repeatability_gate_passed = (
        foliage_template_exact
        and max(repeat_source_changes) <= 0.012
        and max(repeat_hlod_changes) <= 0.015
        and max(repeat_combined_changes) <= 0.020
        and max(repeat_atlas_changes) <= 0.020
    )

    v30_hlod = reports["v30_hard"]["local_multi_view_atlas_hlod"]
    v32_hlod = reports["v32_transition"]["local_multi_view_atlas_hlod"]
    source_geometry_unchanged = (
        reports["v30_hard"]["generated_collection"]["foliage_instance_count"]
        == reports["v32_transition"]["generated_collection"]["foliage_instance_count"]
        and reports["v30_hard"]["local_impostor_source"]["triangle_count_lod0"]
        == reports["v32_transition"]["local_impostor_source"]["triangle_count_lod0"]
    )
    fixed_contracts_match = all(
        v30_hlod[key] == v32_hlod[key]
        for key in (
            "view_contract",
            "orthographic_width_cm",
            "projection_contract",
            "atlas_color_gain",
            "source_wpo_contract",
            "deterministic_capture_contract",
        )
    )
    transition_contract = v32_hlod["complementary_transition_contract"]
    transition_contract_valid = (
        transition_contract["enabled"] is True
        and transition_contract["pattern"] == "deterministic_4x4_screen_bayer"
        and transition_contract["radial_band_cm"] == [2300.0, 2700.0]
        and transition_contract["sample_radii_cm"] == [2400.0, 2500.0, 2600.0]
        and transition_contract["source_coverage"] == [0.75, 0.50, 0.25]
        and transition_contract["capture_count"] == 9
    )
    isolation_valid = (
        source_geometry_unchanged
        and fixed_contracts_match
        and transition_contract_valid
        and max(endpoint_source_controls) <= 0.012
        and max(endpoint_hlod_controls) <= 0.015
    )
    coverage_ratio_errors = []
    for index, distance in enumerate(TRANSITION_DISTANCES):
        coverage_ratio_errors.extend(
            (
                abs(source_side_ratios[index] - (1.0 - SOURCE_COVERAGE[distance])),
                abs(hlod_side_ratios[index] - SOURCE_COVERAGE[distance]),
            )
        )
    transition_operational_gate_passed = (
        max(synthetic_changed) <= 0.015
        and max(synthetic_mad) <= 0.50
        and max(coverage_ratio_errors) <= 0.06
        and combined_to_source_changes == sorted(combined_to_source_changes)
        and combined_to_hlod_changes == sorted(combined_to_hlod_changes, reverse=True)
    )
    transition_retained = (
        isolation_valid
        and repeatability_gate_passed
        and hard_authority_gate_passed
        and transition_operational_gate_passed
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_complementary_transition_review.v32",
        "river_id": "futaleufu_terminator",
        "candidate": "v32_registered_perspective_complementary_transition_test",
        "status": (
            "complementary_transition_retained_temporal_and_art_gates_open"
            if transition_retained
            else "complementary_transition_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V24 source geometry and generated foliage transforms",
                "V25 photometry and hard endpoint authority",
                "V27 frozen-WPO 512-pixel deterministic validation profile",
                "V29 16-degree azimuth registration",
                "V30 authored-distance perspective flat proxy",
            ],
            "only_intended_change": (
                "deterministic complementary 4x4 source/HLOD pixel ownership over "
                "a 23-27 m radial band, sampled at exact 24/25/26 m cameras"
            ),
            "art_review_allowed": False,
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "fixed_contracts_match": fixed_contracts_match,
        "transition_contract_valid": transition_contract_valid,
        "isolation_valid": isolation_valid,
        "endpoint_comparisons": endpoint_comparisons,
        "transition_comparisons": transition_comparisons,
        "repeatability_evidence": {
            "run_a_snapshot_not_committed": True,
            "foliage_template_sha256": template_hashes,
            "foliage_template_exact": foliage_template_exact,
            "transition": repeatability["transition"],
            "handoff": repeatability["handoff"],
            "atlas_channels": repeatability["atlas_channels"],
            "derived_findings": {
                "source_changed_pixel_fractions_at_24_25_26m": repeat_source_changes,
                "hlod_changed_pixel_fractions_at_24_25_26m": repeat_hlod_changes,
                "combined_changed_pixel_fractions_at_24_25_26m": (
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
                "maximum_combined_changed_pixel_fraction": 0.020,
                "maximum_atlas_channel_changed_pixel_fraction": 0.020,
            },
            "repeatability_gate_passed": repeatability_gate_passed,
        },
        "derived_findings": {
            "endpoint_source_control_changed_pixel_fractions_at_20_28_36m": (
                endpoint_source_controls
            ),
            "endpoint_hlod_control_changed_pixel_fractions_at_20_28_36m": (
                endpoint_hlod_controls
            ),
            "combined_to_source_changed_pixel_fractions_at_24_25_26m": (
                combined_to_source_changes
            ),
            "combined_to_hlod_changed_pixel_fractions_at_24_25_26m": (
                combined_to_hlod_changes
            ),
            "observed_combined_to_source_fraction_of_full_change_at_24_25_26m": (
                source_side_ratios
            ),
            "observed_combined_to_hlod_fraction_of_full_change_at_24_25_26m": (
                hlod_side_ratios
            ),
            "maximum_coverage_ratio_error": max(coverage_ratio_errors),
            "synthetic_bayer_changed_pixel_fractions_at_24_25_26m": (synthetic_changed),
            "synthetic_bayer_mean_absolute_channel_delta_at_24_25_26m": (synthetic_mad),
        },
        "hard_endpoint_authority_gate_passed": hard_authority_gate_passed,
        "transition_operational_gate_passed": transition_operational_gate_passed,
        "decision": {
            "retain": [
                "V30 registered authored-distance perspective flat proxy",
                "V32 deterministic complementary source/HLOD transition mechanism",
                "23-27 m radial band and explicit 24/25/26 m review cameras",
            ]
            if transition_retained
            else ["V30 registered authored-distance perspective flat proxy"],
            "reject": [
                "V32 as proof that the underlying source/HLOD silhouettes match",
                "static validation frames as moving-camera temporal evidence",
                "validation-only captures as lit art or production approval",
            ],
            "next_step": (
                "Retain the complementary transition and run a moving-camera temporal "
                "sweep through the 23-27 m band before lit art and platform review."
                if transition_retained
                else "Keep V30 hard authority and revise the complementary transition."
            ),
        },
        "v30_perspective_flat_proxy_retained": True,
        "v32_complementary_transition_retained": transition_retained,
        "underlying_no_pop_gate_passed": False,
        "moving_camera_temporal_gate_passed": False,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v32_complementary_transition_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
