"""Review V26 cypress HLOD resolution and temporal isolation."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)


DISTANCES = ("20m", "28m", "36m")
EXPECTED_AUTHORITY = {"20m": "source_only", "28m": "hlod_only", "36m": "hlod_only"}
V25_NAMESPACE = (
    "FutaleufuCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"
)
V26_NAMESPACE = (
    "FutaleufuCordilleraCypressHighDetailHlodCalibratedIrregularCrownMass"
    "CompoundBranchletAtlas"
)
V25_REPORT = (
    "futaleufu_cordillera_cypress_v25_pve_open_grown_conical_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
V26_REPORT = (
    "futaleufu_cordillera_cypress_v26_pve_open_grown_conical_"
    "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_"
    "report.json"
)


def _relative_paths(comparison: dict, repo_root: Path) -> dict:
    for side in ("before", "after"):
        comparison[side]["path"] = str(
            Path(comparison[side]["path"]).relative_to(repo_root)
        )
    return comparison


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    capture_parent = repo_root / "unreal/Saved/RaftSimPveReview"
    roots = {
        "v25_512": capture_parent / V25_NAMESPACE,
        "v26_1024": capture_parent / V26_NAMESPACE,
    }
    reports = {
        "v25_512": json.loads((report_root / V25_REPORT).read_text(encoding="utf-8")),
        "v26_1024": json.loads((report_root / V26_REPORT).read_text(encoding="utf-8")),
    }

    comparisons = {}
    authority_gate_passed = True
    for distance in DISTANCES:
        v25_source = roots["v25_512"] / (
            f"open_grown_conical_handoff_{distance}_source_only.png"
        )
        v26_source = roots["v26_1024"] / (
            f"open_grown_conical_handoff_{distance}_source_only.png"
        )
        v25_hlod = roots["v25_512"] / (
            f"open_grown_conical_handoff_{distance}_hlod_only.png"
        )
        v26_hlod = roots["v26_1024"] / (
            f"open_grown_conical_handoff_{distance}_hlod_only.png"
        )
        v26_combined = roots["v26_1024"] / (
            f"open_grown_conical_handoff_{distance}_combined.png"
        )
        expected = (
            v26_source
            if EXPECTED_AUTHORITY[distance] == "source_only"
            else v26_hlod
        )
        selected = _relative_paths(_comparison(expected, v26_combined), repo_root)
        selected_equivalent = (
            selected["before"]["sha256"] == selected["after"]["sha256"]
            or (
                selected["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
                and selected["mean_absolute_channel_delta"] <= 0.01
                and selected[
                    "dark_chromatic_foreground_intersection_over_union"
                ]
                >= 0.9999
            )
        )
        authority_gate_passed &= selected_equivalent
        comparisons[distance] = {
            "expected_authority": EXPECTED_AUTHORITY[distance],
            "v25_to_v26_source": _relative_paths(
                _comparison(v25_source, v26_source), repo_root
            ),
            "v25_to_v26_hlod": _relative_paths(
                _comparison(v25_hlod, v26_hlod), repo_root
            ),
            "v26_source_to_hlod": _relative_paths(
                _comparison(v26_source, v26_hlod), repo_root
            ),
            "v26_combined_to_expected": selected,
            "v26_combined_selected_authority_equivalent": selected_equivalent,
        }

    source_geometry_unchanged = (
        reports["v25_512"]["generated_collection"]["foliage_instance_count"]
        == reports["v26_1024"]["generated_collection"]["foliage_instance_count"]
        and reports["v25_512"]["local_impostor_source"]["triangle_count_lod0"]
        == reports["v26_1024"]["local_impostor_source"]["triangle_count_lod0"]
    )
    source_temporal_changed_fraction_range = [
        min(
            comparison["v25_to_v26_source"][
                "changed_pixel_fraction_max_channel_gt_12"
            ]
            for comparison in comparisons.values()
        ),
        max(
            comparison["v25_to_v26_source"][
                "changed_pixel_fraction_max_channel_gt_12"
            ]
            for comparison in comparisons.values()
        ),
    ]
    hlod_changed_fraction_range = [
        min(
            comparison["v25_to_v26_hlod"][
                "changed_pixel_fraction_max_channel_gt_12"
            ]
            for comparison in comparisons.values()
        ),
        max(
            comparison["v25_to_v26_hlod"][
                "changed_pixel_fraction_max_channel_gt_12"
            ]
            for comparison in comparisons.values()
        ),
    ]
    v26_no_pop_changes = [
        comparison["v26_source_to_hlod"][
            "changed_pixel_fraction_max_channel_gt_12"
        ]
        for comparison in comparisons.values()
    ]
    v26_no_pop_ious = [
        comparison["v26_source_to_hlod"][
            "dark_chromatic_foreground_intersection_over_union"
        ]
        for comparison in comparisons.values()
    ]
    resolution_isolation_valid = source_temporal_changed_fraction_range[1] <= 0.01
    no_pop_gate_passed = max(v26_no_pop_changes) <= 0.10 and min(v26_no_pop_ious) >= 0.80

    atlas_files = (
        "base_color_opacity",
        "world_normal",
        "opacity",
        "depth",
    )
    stored_png_bytes = {
        version: sum(
            (
                root
                / f"open_grown_conical_multiview_atlas_{atlas_name}.png"
            ).stat().st_size
            for atlas_name in atlas_files
        )
        for version, root in roots.items()
    }
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_high_detail_hlod_review.v26",
        "river_id": "futaleufu_terminator",
        "candidate": "v26_1024px_per_view_high_detail_hlod",
        "status": "high_detail_hlod_not_retained_resolution_isolation_invalid",
        "comparison_contract": {
            "intended_fixed": [
                "V24 source geometry and material",
                "V25 atlas color gain and hard 2,500 cm authority",
                "sixteen-view camera, lighting, and output-channel contract",
            ],
            "intended_change": "tile resolution 512 to 1024 and atlas resolution 2048 to 4096",
            "discovered_confounder": (
                "The live source material retains SimpleGrassWind defaults "
                "WindIntensity=0.16, WindWeight=0.28, and WindSpeed=0.42, so "
                "separate runs and sequential atlas views do not share a frozen pose."
            ),
            "reports": {
                version: str(
                    (report_root / report_name).relative_to(repo_root)
                )
                for version, report_name in {
                    "v25_512": V25_REPORT,
                    "v26_1024": V26_REPORT,
                }.items()
            },
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "atlas_resource_evidence": {
            "v25_tile_resolution": 512,
            "v25_atlas_resolution": 2048,
            "v26_tile_resolution": 1024,
            "v26_atlas_resolution": 4096,
            "texel_area_ratio": 4.0,
            "uncompressed_four_rgba8_source_bytes": {
                "v25_512": 4 * 2048 * 2048 * 4,
                "v26_1024": 4 * 4096 * 4096 * 4,
            },
            "stored_png_bytes": stored_png_bytes,
            "packaged_gpu_memory_not_measured": True,
        },
        "distance_comparisons": comparisons,
        "derived_findings": {
            "source_temporal_changed_pixel_fraction_range": (
                source_temporal_changed_fraction_range
            ),
            "hlod_changed_pixel_fraction_range": hlod_changed_fraction_range,
            "v26_source_hlod_changed_pixel_fractions_at_20_28_36m": (
                v26_no_pop_changes
            ),
            "v26_source_hlod_foreground_iou_at_20_28_36m": v26_no_pop_ious,
        },
        "resolution_isolation_valid": resolution_isolation_valid,
        "hard_authority_gate_passed": authority_gate_passed,
        "no_pop_gate_passed": no_pop_gate_passed,
        "human_review": {
            "accepted": [
                "The baker and generated texture/material path support an explicit 1024-pixel-per-view, 4096-pixel atlas profile.",
                "V26 preserves V25 hard one-representation authority at all three exact handoff cameras.",
                "The run exposes temporal pose contamination as a required deterministic-bake gate.",
            ],
            "rejected": [
                "V25 and V26 source-only frames change by more than one percent despite identical source geometry, proving the intended resolution isolation is invalid while live wind remains active.",
                "V25 and V26 HLOD frames contain visibly different branch poses, with 15-27 percent changed pixels across handoff distances.",
                "V26 does not pass the no-pop thresholds and quadruples atlas texel area, so the high-detail profile is not retained for runtime use.",
            ],
            "decision": "Reject V26 promotion and any conclusion that resolution alone improves the handoff. Freeze source wind/WPO for deterministic atlas and source controls, then rerun matched 512 and 1024 profiles before choosing registration, detail, or complementary dither work.",
        },
        "v26_high_detail_hlod_retained": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v26_high_detail_hlod_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
