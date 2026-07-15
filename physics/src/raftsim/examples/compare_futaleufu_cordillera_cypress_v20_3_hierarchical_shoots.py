"""Compare V20.2 and V20.3 cordilleran-cypress shoot topology."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_2_branchlet_mass import (
    _wood_metrics,
)


CAPTURES = {
    "exact_60m_source": "open_grown_conical_river_distance_60m.png",
    "branch_spray_closeup": "open_grown_conical_branch_spray_closeup.png",
    "exact_60m_hlod": "open_grown_conical_multiview_atlas_hlod_60m.png",
}
VARIANTS = {
    "v20_2_branchlet_mass": {
        "capture_root": (
            "FutaleufuCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy"
        ),
        "report": "futaleufu_cordillera_cypress_v20_2_pve_open_grown_conical_"
        "branchlet_mass_botanical_flattened_spray_hierarchy_report.json",
    },
    "v20_3_hierarchical_shoot_cluster": {
        "capture_root": "FutaleufuCordilleraCypressHierarchicalBotanicalShootCluster",
        "report": "futaleufu_cordillera_cypress_v20_3_pve_open_grown_conical_"
        "hierarchical_botanical_shoot_cluster_report.json",
    },
}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    saved_root = repo_root / "unreal/Saved/RaftSimPveReview"
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    reports = {
        key: json.loads((report_root / value["report"]).read_text(encoding="utf-8"))
        for key, value in VARIANTS.items()
    }
    comparisons = {}
    for capture_id, filename in CAPTURES.items():
        before_path = (
            saved_root / VARIANTS["v20_2_branchlet_mass"]["capture_root"] / filename
        )
        after_path = (
            saved_root
            / VARIANTS["v20_3_hierarchical_shoot_cluster"]["capture_root"]
            / filename
        )
        comparison = _comparison(before_path, after_path)
        for side in ("before", "after"):
            comparison[side]["path"] = str(
                Path(comparison[side]["path"]).relative_to(repo_root)
            )
        if capture_id == "branch_spray_closeup":
            comparison["before"]["wood"] = _wood_metrics(before_path)
            comparison["after"]["wood"] = _wood_metrics(after_path)
        comparisons[capture_id] = comparison

    source = comparisons["exact_60m_source"]
    closeup = comparisons["branch_spray_closeup"]
    hlod = comparisons["exact_60m_hlod"]
    source_before = source["before"]["dark_chromatic_foreground_pixels"]
    source_after = source["after"]["dark_chromatic_foreground_pixels"]
    closeup_before = closeup["before"]["dark_chromatic_foreground_pixels"]
    closeup_after = closeup["after"]["dark_chromatic_foreground_pixels"]
    wood_fraction_before = closeup["before"]["wood"][
        "wood_fraction_of_detected_plant"
    ]
    wood_fraction_after = closeup["after"]["wood"][
        "wood_fraction_of_detected_plant"
    ]
    hlod_after = hlod["after"]["dark_chromatic_foreground_pixels"]

    output = {
        "schema": (
            "raftsim.unreal.futaleufu_cordillera_cypress_hierarchical_shoot_review.v20_3"
        ),
        "river_id": "futaleufu_terminator",
        "candidate": "v20_3_open_grown_conical_hierarchical_botanical_shoot_cluster",
        "status": "fresh_material_gate_passed_hierarchical_topology_rejected",
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "V20 deterministic 18-23 cm measured spray tiles",
                "V20.1 full-resolution residency and 0.42 alpha coverage",
                "three main and two parent-lateral measured-spray layers",
                "V20.2 post-usage shader-resource gate and corrected HLOD path",
                "24.68 m open-grown tree envelope",
                "exact closeup, 60 m source, and 60 m multi-view HLOD cameras",
            ],
            "v20_3_changed": [
                "replace six parent branchlet pairs with five side-offset pairs",
                "shorten parent woody support from 0.68 to 0.60 of spray length",
                "shrink parent lateral sprays to 0.78 width and 0.82 length",
                "add two connected tertiary sub-shoots with smaller measured spray cards to every lateral",
            ],
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
                "authored_branchlet_geometry": report["workflow"][
                    "authored_branchlet_geometry"
                ],
                "foliage_instance_count": report["generated_collection"][
                    "foliage_instance_count"
                ],
                "impostor_source_triangle_count": report["local_impostor_source"][
                    "triangle_count_lod0"
                ],
                "atlas_coverage_fraction_range": report[
                    "local_multi_view_atlas_hlod"
                ]["coverage_fraction_range"],
            }
            for key, report in reports.items()
        },
        "capture_comparisons": comparisons,
        "derived_findings": {
            "closeup_foreground_change_fraction": closeup_after / closeup_before - 1.0,
            "closeup_wood_fraction_change": wood_fraction_after - wood_fraction_before,
            "exact_60m_source_foreground_change_fraction": (
                source_after / source_before - 1.0
            ),
            "v20_3_hlod_to_source_foreground_ratio": hlod_after / source_after,
        },
        "human_review": {
            "accepted": [
                "A genuinely new V20.3 material namespace renders correct measured foliage and alpha on its first capture, directly validating the post-usage shader-resource gate.",
                "The tertiary segments are connected geometry and break some of the six-pair mirror rhythm without changing textures or tree-level transforms.",
            ],
            "rejected": [
                "The closeup exposes more woody stems and still reads as a procedural fan rather than a dense flattened cypress shoot cluster.",
                "Shrinking parent sprays while adding thin tertiary sprays does not close the 60 m tier gaps or improve the crown silhouette.",
                "The merged source cost rises materially without a corresponding source-art gain.",
                "Only the open-grown form is evaluated; handoff, temporal, ecology, packaged desktop, target-VR, and native-species art review remain open.",
            ],
            "decision": (
                "Retain the proven fresh-material shader gate. Reject the V20.3 geometry, "
                "visual, corridor, all-form, and production promotion. The next source pass "
                "should keep parent spray mass, place shorter low-wood sub-shoot clusters "
                "near branchlet ends, and require a positive 60 m density gain before another "
                "triangle-cost increase is accepted."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "v20_3_geometry_retained": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v20_3_hierarchical_shoot_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
