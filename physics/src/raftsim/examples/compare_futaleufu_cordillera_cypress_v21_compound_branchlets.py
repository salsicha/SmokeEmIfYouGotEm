"""Compare V20.2 and V21 cordilleran-cypress compound branchlet sources."""

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
    "v21_compound_branchlet_atlas": {
        "capture_root": "FutaleufuCordilleraCypressCompoundBranchletAtlas",
        "report": "futaleufu_cordillera_cypress_v21_pve_open_grown_conical_"
        "compound_branchlet_atlas_report.json",
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
            / VARIANTS["v21_compound_branchlet_atlas"]["capture_root"]
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
    wood_before = closeup["before"]["wood"]["wood_fraction_of_detected_plant"]
    wood_after = closeup["after"]["wood"]["wood_fraction_of_detected_plant"]
    hlod_after = hlod["after"]["dark_chromatic_foreground_pixels"]
    triangles_before = reports["v20_2_branchlet_mass"]["local_impostor_source"][
        "triangle_count_lod0"
    ]
    triangles_after = reports["v21_compound_branchlet_atlas"][
        "local_impostor_source"
    ]["triangle_count_lod0"]
    findings = {
        "triangle_cost_change_fraction": triangles_after / triangles_before - 1.0,
        "closeup_foreground_change_fraction": closeup_after / closeup_before - 1.0,
        "closeup_wood_fraction_change": wood_after - wood_before,
        "exact_60m_source_foreground_change_fraction": (
            source_after / source_before - 1.0
        ),
        "v21_hlod_to_source_foreground_ratio": hlod_after / source_after,
    }
    source_gate_passed = (
        findings["triangle_cost_change_fraction"] < -0.15
        and findings["closeup_foreground_change_fraction"] > 0.05
        and findings["closeup_wood_fraction_change"] < 0.0
        and findings["exact_60m_source_foreground_change_fraction"] > 0.05
        and 1.0 < findings["v21_hlod_to_source_foreground_ratio"] < 1.25
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_compound_branchlet_review.v21",
        "river_id": "futaleufu_terminator",
        "candidate": "v21_open_grown_conical_compound_branchlet_atlas",
        "status": (
            "compound_branchlet_source_baseline_retained_visual_promotion_rejected"
            if source_gate_passed
            else "compound_branchlet_source_gate_failed_visual_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V20.2 six-pair connected parent topology, seed, and 3626 transforms",
                "post-usage shader-resource gate and corrected source-lit HLOD path",
                "open-grown form envelope and exact cameras",
            ],
            "v21_changed": [
                "compose six independent measured V20 sprays into each project-owned branchlet atlas tile",
                "reduce each authored twig from 27 source cards to 14",
                "use two main cards and one card per connected lateral with bounded larger card dimensions",
            ],
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
                "botanical_spray_layering": report["workflow"][
                    "botanical_spray_layering"
                ],
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
        "derived_findings": findings,
        "source_gate_passed": source_gate_passed,
        "human_review": {
            "accepted": [
                "V21 reduces merged source triangles while increasing closeup and exact 60 m foliage mass.",
                "The compound tiles replace repeated per-twig card growth with a reusable branchlet-scale source representation.",
                "The fresh V21 material renders measured alpha on its first run and the HLOD remains bounded to the source silhouette.",
            ],
            "rejected": [
                "The isolated crown still has coarse horizontal tiers and large open bands.",
                "Close inspection still reveals a regular procedural woody fan and flattened compound source plane.",
                "Only one form is evaluated; no handoff, temporal, ecology, corridor, desktop, VR, or native-art promotion gate is closed.",
            ],
            "decision": (
                "Retain V21 as the lower-cost open-grown source baseline if the automated "
                "source gate passes. Keep every promotion path closed and next break the "
                "whole-crown tier rhythm before regenerating other forms."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "v21_source_baseline_retained": source_gate_passed,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v21_compound_branchlet_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
