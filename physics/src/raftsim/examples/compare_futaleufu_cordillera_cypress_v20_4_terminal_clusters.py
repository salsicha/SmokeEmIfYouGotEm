"""Compare V20.2 and V20.4 cordilleran-cypress terminal clusters."""

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
    "v20_4_terminal_cluster": {
        "capture_root": "FutaleufuCordilleraCypressTerminalClusterBotanicalShoot",
        "report": "futaleufu_cordillera_cypress_v20_4_pve_open_grown_conical_"
        "terminal_cluster_botanical_shoot_report.json",
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
            saved_root / VARIANTS["v20_4_terminal_cluster"]["capture_root"] / filename
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
    wood_before = closeup["before"]["wood"]["wood_fraction_of_detected_plant"]
    wood_after = closeup["after"]["wood"]["wood_fraction_of_detected_plant"]
    hlod_after = hlod["after"]["dark_chromatic_foreground_pixels"]
    triangles_before = reports["v20_2_branchlet_mass"]["local_impostor_source"][
        "triangle_count_lod0"
    ]
    triangles_after = reports["v20_4_terminal_cluster"]["local_impostor_source"][
        "triangle_count_lod0"
    ]

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_terminal_cluster_review.v20_4",
        "river_id": "futaleufu_terminator",
        "candidate": "v20_4_open_grown_conical_terminal_cluster_botanical_shoot",
        "status": "terminal_cluster_cost_gate_failed_visual_promotion_rejected",
        "comparison_contract": {
            "fixed": [
                "V20.2 parent topology, measured sprays, 3/2 layering, seed, and 3626 transforms",
                "post-usage shader-resource gate and corrected HLOD path",
                "open-grown form envelope and exact cameras",
            ],
            "v20_4_changed": [
                "add two 9-10 cm terminal spray cards per lateral at 0.69 and 0.82 parent length",
                "connect each terminal card with a 0.28-length tapered woody support",
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
            "triangle_cost_increase_fraction": triangles_after / triangles_before - 1.0,
            "closeup_foreground_change_fraction": closeup_after / closeup_before - 1.0,
            "closeup_wood_fraction_change": wood_after - wood_before,
            "exact_60m_source_foreground_change_fraction": (
                source_after / source_before - 1.0
            ),
            "v20_4_hlod_to_source_foreground_ratio": hlod_after / source_after,
        },
        "human_review": {
            "accepted": [
                "The clean first-run material and corrected HLOD path remain stable.",
                "V20.4 preserves V20.2 parent spray mass and limits new woody supports to short terminal connections.",
            ],
            "rejected": [
                "The terminal clusters do not produce enough exact 60 m source-density gain to justify the merged triangle increase.",
                "The closeup remains a woody procedural fan and the open-grown crown retains large tier gaps.",
                "Only one form is evaluated; no handoff, temporal, ecology, desktop, VR, or native-art promotion gate is closed.",
            ],
            "decision": (
                "Retain V20.2 as the source baseline and reject V20.4 geometry and every "
                "promotion path. Stop adding per-twig cards until a lower-cost source "
                "strategy or reviewed native asset can improve the 60 m silhouette."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "v20_4_geometry_retained": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v20_4_terminal_cluster_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
