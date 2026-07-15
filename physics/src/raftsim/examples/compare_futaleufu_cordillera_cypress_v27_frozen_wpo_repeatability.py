"""Review repeatability of the V27 frozen-WPO validation profile."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)


NAMESPACE = (
    "FutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMass"
    "CompoundBranchletAtlas"
)
REPORT_NAME = (
    "futaleufu_cordillera_cypress_v27_pve_open_grown_conical_frozen_wpo_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
DISTANCES = ("20m", "28m", "36m")
EXPECTED_AUTHORITY = {"20m": "source_only", "28m": "hlod_only", "36m": "hlod_only"}
ATLAS_CHANNELS = ("base_color_opacity", "world_normal", "opacity", "depth")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _label_paths(comparison: dict, relative_name: str) -> dict:
    comparison["before"]["path"] = f"run_a_snapshot/{relative_name}"
    comparison["after"]["path"] = f"run_b_regenerated/{relative_name}"
    return comparison


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a-root", type=Path, required=True)
    parser.add_argument("--run-a-report", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    run_b_root = repo_root / "unreal/Saved/RaftSimPveReview" / NAMESPACE
    run_b_report_path = report_root / REPORT_NAME
    run_a_report = json.loads(args.run_a_report.read_text(encoding="utf-8"))
    run_b_report = json.loads(run_b_report_path.read_text(encoding="utf-8"))

    handoffs = {}
    source_repeatability = []
    hlod_repeatability = []
    combined_repeatability = []
    hard_authority_gate_passed = True
    for distance in DISTANCES:
        distance_result = {}
        for authority in ("source_only", "hlod_only", "combined"):
            name = f"open_grown_conical_handoff_{distance}_{authority}.png"
            comparison = _label_paths(
                _comparison(args.run_a_root / name, run_b_root / name), name
            )
            distance_result[f"{authority}_run_a_to_run_b"] = comparison
            changed = comparison["changed_pixel_fraction_max_channel_gt_12"]
            if authority == "source_only":
                source_repeatability.append(changed)
            elif authority == "hlod_only":
                hlod_repeatability.append(changed)
            else:
                combined_repeatability.append(changed)

        expected_authority = EXPECTED_AUTHORITY[distance]
        expected_name = (
            f"open_grown_conical_handoff_{distance}_{expected_authority}.png"
        )
        combined_name = f"open_grown_conical_handoff_{distance}_combined.png"
        authority_comparison = _label_paths(
            _comparison(run_b_root / expected_name, run_b_root / combined_name),
            f"{expected_name}_to_{combined_name}",
        )
        authority_equivalent = (
            authority_comparison["before"]["sha256"]
            == authority_comparison["after"]["sha256"]
            or (
                authority_comparison[
                    "changed_pixel_fraction_max_channel_gt_12"
                ]
                <= 0.0001
                and authority_comparison["mean_absolute_channel_delta"] <= 0.01
                and authority_comparison[
                    "dark_chromatic_foreground_intersection_over_union"
                ]
                >= 0.9999
            )
        )
        hard_authority_gate_passed &= authority_equivalent
        distance_result["expected_authority"] = expected_authority
        distance_result["run_b_combined_to_expected"] = authority_comparison
        distance_result["run_b_authority_equivalent"] = authority_equivalent
        handoffs[distance] = distance_result

    atlas_repeatability = {}
    atlas_changed_fractions = []
    for channel in ATLAS_CHANNELS:
        name = f"open_grown_conical_multiview_atlas_{channel}.png"
        comparison = _label_paths(
            _comparison(args.run_a_root / name, run_b_root / name), name
        )
        atlas_repeatability[channel] = comparison
        atlas_changed_fractions.append(
            comparison["changed_pixel_fraction_max_channel_gt_12"]
        )

    template_name = "open_grown_conical_foliage_template.json"
    template_a = args.run_a_root / template_name
    template_b = run_b_root / template_name
    template_hashes = {"run_a": _sha256(template_a), "run_b": _sha256(template_b)}
    foliage_template_exact = template_hashes["run_a"] == template_hashes["run_b"]
    source_repeatability_gate_passed = max(source_repeatability) <= 0.012
    hlod_repeatability_gate_passed = max(hlod_repeatability) <= 0.015
    atlas_repeatability_gate_passed = max(atlas_changed_fractions) <= 0.020
    deterministic_validation_gate_passed = all(
        (
            foliage_template_exact,
            source_repeatability_gate_passed,
            hlod_repeatability_gate_passed,
            atlas_repeatability_gate_passed,
            hard_authority_gate_passed,
        )
    )

    run_a_hlod = run_a_report["local_multi_view_atlas_hlod"]
    run_b_hlod = run_b_report["local_multi_view_atlas_hlod"]
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_frozen_wpo_repeatability.v27",
        "river_id": "futaleufu_terminator",
        "candidate": "v27_frozen_wpo_512px_per_view_validation_profile",
        "status": (
            "frozen_wpo_tolerance_bounded_deterministic_validation_baseline_retained"
            if deterministic_validation_gate_passed
            else "frozen_wpo_deterministic_validation_gate_failed"
        ),
        "validation_scope": {
            "purpose": "isolate source and atlas geometry for matched resolution tests",
            "art_review_allowed": False,
            "reason": "lighting, post processing, atmosphere, fog, AA, temporal effects, GI, AO, and reflections are intentionally disabled",
            "run_a_command_equals_run_b_command": True,
            "run_a_snapshot_not_committed": True,
            "regeneration_instruction": "Run the V27 Unreal command twice and preserve the first RaftSimPveReview namespace before the second run.",
        },
        "source_contract": {
            "foliage_instance_count_run_a": run_a_report["generated_collection"][
                "foliage_instance_count"
            ],
            "foliage_instance_count_run_b": run_b_report["generated_collection"][
                "foliage_instance_count"
            ],
            "source_triangle_count_run_a": run_a_report["local_impostor_source"][
                "triangle_count_lod0"
            ],
            "source_triangle_count_run_b": run_b_report["local_impostor_source"][
                "triangle_count_lod0"
            ],
            "foliage_template_sha256": template_hashes,
            "foliage_template_exact": foliage_template_exact,
            "source_wpo_contract": run_b_hlod["source_wpo_contract"],
            "deterministic_capture_contract": run_b_hlod[
                "deterministic_capture_contract"
            ],
        },
        "atlas_contract": {
            "run_a_view_contract": run_a_hlod["view_contract"],
            "run_b_view_contract": run_b_hlod["view_contract"],
            "run_a_coverage_fraction_range": run_a_hlod[
                "coverage_fraction_range"
            ],
            "run_b_coverage_fraction_range": run_b_hlod[
                "coverage_fraction_range"
            ],
            "atlas_color_gain": run_b_hlod["atlas_color_gain"],
        },
        "handoff_repeatability": handoffs,
        "atlas_channel_repeatability": atlas_repeatability,
        "derived_findings": {
            "source_changed_pixel_fractions_at_20_28_36m": source_repeatability,
            "hlod_changed_pixel_fractions_at_20_28_36m": hlod_repeatability,
            "combined_changed_pixel_fractions_at_20_28_36m": (
                combined_repeatability
            ),
            "atlas_channel_changed_pixel_fraction_range": [
                min(atlas_changed_fractions),
                max(atlas_changed_fractions),
            ],
        },
        "thresholds": {
            "maximum_source_changed_pixel_fraction": 0.012,
            "maximum_hlod_changed_pixel_fraction": 0.015,
            "maximum_atlas_channel_changed_pixel_fraction": 0.020,
        },
        "source_repeatability_gate_passed": source_repeatability_gate_passed,
        "hlod_repeatability_gate_passed": hlod_repeatability_gate_passed,
        "atlas_repeatability_gate_passed": atlas_repeatability_gate_passed,
        "hard_authority_gate_passed": hard_authority_gate_passed,
        "deterministic_validation_gate_passed": (
            deterministic_validation_gate_passed
        ),
        "v27_validation_baseline_retained": deterministic_validation_gate_passed,
        "art_review_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "next_step": "Generate the same frozen-WPO validation profile at 1024 pixels per view and compare it with V27 under these measured repeatability tolerances before returning to lit art review.",
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v27_frozen_wpo_repeatability_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
