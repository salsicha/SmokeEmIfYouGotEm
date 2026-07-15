"""Compare V20.1 and V20.2 cordilleran-cypress branchlet topology."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
    _foreground,
)


CAPTURES = {
    "exact_60m_source": "open_grown_conical_river_distance_60m.png",
    "branch_spray_closeup": "open_grown_conical_branch_spray_closeup.png",
    "exact_60m_hlod": "open_grown_conical_multiview_atlas_hlod_60m.png",
}
VARIANTS = {
    "v20_1_dense_botanical_flattened_spray": {
        "capture_root": (
            "FutaleufuCordilleraCypressDenseBotanicalFlattenedSprayHierarchy"
        ),
        "report": "futaleufu_cordillera_cypress_v20_1_pve_open_grown_conical_"
        "dense_botanical_flattened_spray_hierarchy_report.json",
    },
    "v20_2_branchlet_mass_botanical_flattened_spray": {
        "capture_root": (
            "FutaleufuCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy"
        ),
        "report": "futaleufu_cordillera_cypress_v20_2_pve_open_grown_conical_"
        "branchlet_mass_botanical_flattened_spray_hierarchy_report.json",
    },
}


def _wood_mask(rgb: np.ndarray) -> np.ndarray:
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]
    return (
        (red >= 45)
        & (red <= 180)
        & (green >= 25)
        & (red > green * 1.18)
        & (red > blue * 1.22)
    )


def _wood_metrics(path: Path) -> dict:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    wood = _wood_mask(rgb)
    plant_foreground = wood | _foreground(rgb)
    return {
        "wood_pixels": int(np.count_nonzero(wood)),
        "wood_fraction_of_detected_plant": float(
            np.count_nonzero(wood) / max(np.count_nonzero(plant_foreground), 1)
        ),
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
            saved_root
            / VARIANTS["v20_1_dense_botanical_flattened_spray"]["capture_root"]
            / filename
        )
        after_path = (
            saved_root
            / VARIANTS[
                "v20_2_branchlet_mass_botanical_flattened_spray"
            ]["capture_root"]
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
            "raftsim.unreal.futaleufu_cordillera_cypress_branchlet_mass_review.v20_2"
        ),
        "river_id": "futaleufu_terminator",
        "candidate": "v20_2_open_grown_conical_branchlet_mass_botanical_spray",
        "status": (
            "connected_branchlet_and_fresh_material_gate_retained_"
            "visual_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "V20 deterministic 18-23 cm measured spray tiles",
                "V20.1 full-resolution residency and 0.42 alpha coverage",
                "three main and two lateral measured-spray layers",
                "V20.1 source-lit HLOD color correction",
                "24.68 m open-grown tree envelope",
                "exact closeup, 60 m source, and 60 m multi-view HLOD cameras",
            ],
            "v20_2_changed": [
                "increase connected lateral branchlet pairs per authored twig from four to six",
                "stagger attachments from normalized 0.10 through 0.825 with three-state vertical variation",
                "shorten woody support length from 0.82 to 0.68 of each lateral spray length",
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
                "authored_branchlet_geometry": report["workflow"].get(
                    "authored_branchlet_geometry"
                ),
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
            "closeup_foreground_increase_fraction": closeup_after / closeup_before - 1.0,
            "closeup_wood_fraction_change": wood_fraction_after - wood_fraction_before,
            "exact_60m_source_foreground_increase_fraction": (
                source_after / source_before - 1.0
            ),
            "v20_2_hlod_to_source_foreground_ratio": hlod_after / source_after,
        },
        "human_review": {
            "accepted": [
                "V20.2 replaces part of the repeated four-pair fan with six genuinely connected and vertically varied branchlets rather than increasing opacity or changing the measured spray texture.",
                "The shorter support segments reduce unsupported bare woody tips while preserving connected branch topology.",
                "After adding the post-usage shader-resource gate, a fresh run with no V20.2 material asset present produced the correct measured foliage and alpha on its first capture; the earlier pre-fix gray fallback run is explicitly excluded from evidence.",
                "Removing fallback planes from the source bake corrects atlas coverage to 0.096-0.105 and reduces exact-camera HLOD/source foreground mismatch to about 1.13x.",
            ],
            "rejected": [
                "The exact closeup still reads as a regular woody fan and does not reach photographic branch density.",
                "The 60 m source remains skeletal, with tier gaps and exposed branch arcs still dominating the crown.",
                "The corrected HLOD is still darker than the exact source, and no 20/28/36 m source/HLOD handoff, overlap, or moving-camera evidence exists yet.",
                "Only the open-grown form is evaluated; all-form, ecology, temporal, packaged desktop, target-VR, and native-species art review remain open.",
            ],
            "decision": (
                "Retain V20.2 as the connected branchlet-topology baseline, but reject visual, "
                "corridor, all-form, and production promotion. The next source-art pass must "
                "replace repeated whole-axis fans with hierarchically subdivided flattened "
                "shoot clusters and reduce tier gaps before separately calibrating corrected "
                "HLOD luminance and authority at 20/28/36 m."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v20_2_branchlet_mass_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
