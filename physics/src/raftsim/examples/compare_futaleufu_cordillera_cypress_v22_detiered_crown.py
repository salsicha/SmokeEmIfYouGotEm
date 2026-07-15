"""Compare V21 and V22 cordilleran-cypress crown topology."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
    _foreground,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_2_branchlet_mass import (
    _wood_metrics,
)


CAPTURES = {
    "exact_60m_source": "open_grown_conical_river_distance_60m.png",
    "branch_spray_closeup": "open_grown_conical_branch_spray_closeup.png",
    "exact_60m_hlod": "open_grown_conical_multiview_atlas_hlod_60m.png",
    "turntable_azimuth_035": "open_grown_conical_turntable_azimuth_035.png",
    "turntable_azimuth_145": "open_grown_conical_turntable_azimuth_145.png",
}
VARIANTS = {
    "v21_compound_branchlet_atlas": {
        "capture_root": "FutaleufuCordilleraCypressCompoundBranchletAtlas",
        "report": "futaleufu_cordillera_cypress_v21_pve_open_grown_conical_"
        "compound_branchlet_atlas_report.json",
    },
    "v22_detiered_compound_branchlet_atlas": {
        "capture_root": ("FutaleufuCordilleraCypressDeTieredCompoundBranchletAtlas"),
        "report": "futaleufu_cordillera_cypress_v22_pve_open_grown_conical_"
        "detiered_compound_branchlet_atlas_report.json",
    },
}
TURNTABLE_CAPTURES = ("turntable_azimuth_035", "turntable_azimuth_145")


def _runs(mask: np.ndarray) -> list[int]:
    lengths: list[int] = []
    start: int | None = None
    for index, value in enumerate(np.append(mask, False)):
        if value and start is None:
            start = index
        elif not value and start is not None:
            lengths.append(index - start)
            start = None
    return lengths


def _crown_band_metrics(path: Path) -> dict:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    height, width, _ = rgb.shape
    foreground = _foreground(rgb)
    roi = np.zeros_like(foreground)
    roi[
        int(height * 0.03) : int(height * 0.95),
        int(width * 0.25) : int(width * 0.75),
    ] = True
    foreground &= roi
    rows, columns = np.where(foreground)
    if rows.size == 0:
        raise ValueError(f"no crown foreground detected in {path}")

    top = int(rows.min())
    bottom = int(rows.max())
    left = int(columns.min())
    right = int(columns.max())
    crown_bottom = top + int((bottom - top + 1) * 0.82)
    row_occupancy = foreground[top:crown_bottom, left : right + 1].sum(
        axis=1, dtype=np.float64
    )
    smoothed_occupancy = np.convolve(
        row_occupancy, np.full(11, 1.0 / 11.0), mode="same"
    )
    occupancy_scale = max(float(np.percentile(smoothed_occupancy, 90)), 1.0)
    normalized_occupancy = smoothed_occupancy / occupancy_scale
    open_rows = normalized_occupancy < 0.25
    open_runs = _runs(open_rows)
    return {
        "analysis_roi_normalized": [0.25, 0.03, 0.75, 0.95],
        "detected_plant_bounds_pixels": [left, top, right, bottom],
        "crown_height_fraction_of_detected_plant": 0.82,
        "row_smoothing_window_pixels": 11,
        "occupancy_normalization_percentile": 90,
        "open_row_normalized_occupancy_threshold": 0.25,
        "open_band_fraction": float(np.mean(open_rows)),
        "large_open_band_count_minimum_8_pixels": int(
            sum(length >= 8 for length in open_runs)
        ),
        "largest_open_band_pixels": int(max(open_runs, default=0)),
        "smoothed_row_occupancy_coefficient_of_variation": float(
            np.std(smoothed_occupancy) / max(np.mean(smoothed_occupancy), 1.0)
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
            / VARIANTS["v21_compound_branchlet_atlas"]["capture_root"]
            / filename
        )
        after_path = (
            saved_root
            / VARIANTS["v22_detiered_compound_branchlet_atlas"]["capture_root"]
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
        if capture_id in TURNTABLE_CAPTURES:
            comparison["before"]["crown_bands"] = _crown_band_metrics(before_path)
            comparison["after"]["crown_bands"] = _crown_band_metrics(after_path)
        comparisons[capture_id] = comparison

    v21_report = reports["v21_compound_branchlet_atlas"]
    v22_report = reports["v22_detiered_compound_branchlet_atlas"]
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
    triangles_before = v21_report["local_impostor_source"]["triangle_count_lod0"]
    triangles_after = v22_report["local_impostor_source"]["triangle_count_lod0"]
    instances_before = v21_report["generated_collection"]["foliage_instance_count"]
    instances_after = v22_report["generated_collection"]["foliage_instance_count"]
    open_band_before = np.mean(
        [
            comparisons[capture]["before"]["crown_bands"]["open_band_fraction"]
            for capture in TURNTABLE_CAPTURES
        ]
    )
    open_band_after = np.mean(
        [
            comparisons[capture]["after"]["crown_bands"]["open_band_fraction"]
            for capture in TURNTABLE_CAPTURES
        ]
    )
    largest_open_band_before = max(
        comparisons[capture]["before"]["crown_bands"]["largest_open_band_pixels"]
        for capture in TURNTABLE_CAPTURES
    )
    largest_open_band_after = max(
        comparisons[capture]["after"]["crown_bands"]["largest_open_band_pixels"]
        for capture in TURNTABLE_CAPTURES
    )
    findings = {
        "triangle_cost_change_fraction": triangles_after / triangles_before - 1.0,
        "foliage_instance_count_change_fraction": (
            instances_after / instances_before - 1.0
        ),
        "closeup_foreground_change_fraction": closeup_after / closeup_before - 1.0,
        "closeup_wood_fraction_change": wood_after - wood_before,
        "exact_60m_source_foreground_change_fraction": (
            source_after / source_before - 1.0
        ),
        "v22_hlod_to_source_foreground_ratio": hlod_after / source_after,
        "mean_turntable_open_band_fraction_before": float(open_band_before),
        "mean_turntable_open_band_fraction_after": float(open_band_after),
        "mean_turntable_open_band_fraction_change": float(
            open_band_after - open_band_before
        ),
        "largest_turntable_open_band_pixels_before": largest_open_band_before,
        "largest_turntable_open_band_pixels_after": largest_open_band_after,
    }
    topology_gate_passed = (
        findings["triangle_cost_change_fraction"] < -0.05
        and findings["foliage_instance_count_change_fraction"] > -0.12
        and findings["closeup_foreground_change_fraction"] > -0.05
        and findings["exact_60m_source_foreground_change_fraction"] > -0.15
        and 0.95 < findings["v22_hlod_to_source_foreground_ratio"] < 1.20
        and findings["mean_turntable_open_band_fraction_change"] < -0.015
        and largest_open_band_after <= largest_open_band_before
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_detiered_crown_review.v22",
        "river_id": "futaleufu_terminator",
        "candidate": "v22_open_grown_conical_detiered_compound_branchlet_atlas",
        "status": (
            "detiered_crown_topology_baseline_retained_visual_promotion_rejected"
            if topology_gate_passed
            else "detiered_crown_topology_gate_failed_visual_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V21 compound branchlet textures, fourteen-card authored twig, and material response",
                "post-usage shader-resource gate and corrected source-lit HLOD path",
                "open-grown form envelope and exact review cameras",
            ],
            "v22_changed": [
                "replace coarse main-axis priority steps with a gradual six-key growth ramp",
                "use the 137.507764-degree golden angle and larger stagger on main and graft phyllotaxy",
                "reduce branch flattening and increase bounded main, branch, and graft angle jitter",
                "reduce graft axil angle from 72 to 66 degrees and stop graft distribution at normalized 0.98 height",
            ],
            "crown_band_measurement": (
                "Within the central 50% by horizontal and 3-95% by vertical capture ROI, "
                "measure the upper 82% of the detected plant. Smooth per-row dark/chromatic "
                "foreground occupancy over 11 pixels, normalize to its 90th percentile, and "
                "classify rows below 0.25 occupancy as open. Average two exact turntable views."
            ),
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "structural_evidence": {
            key: {
                "crown_topology_mode": report["workflow"].get(
                    "crown_topology_mode", "legacy_tiered"
                ),
                "foliage_instance_count": report["generated_collection"][
                    "foliage_instance_count"
                ],
                "impostor_source_triangle_count": report["local_impostor_source"][
                    "triangle_count_lod0"
                ],
                "atlas_coverage_fraction_range": report["local_multi_view_atlas_hlod"][
                    "coverage_fraction_range"
                ],
            }
            for key, report in reports.items()
        },
        "capture_comparisons": comparisons,
        "derived_findings": findings,
        "topology_gate_passed": topology_gate_passed,
        "human_review": {
            "accepted": [
                "V22 produces a less regular crown at both exact turntable angles; the measured mean low-occupancy row fraction falls while the largest open run does not grow.",
                "The de-tiered scheduling lowers source triangles and keeps exact closeup foliage mass and HLOD/source agreement bounded.",
                "Golden-angle graft distribution and bounded jitter provide a reusable crown-topology control independent of the V21 compound branchlet source art.",
            ],
            "rejected": [
                "The isolated crown remains too sparse and still exposes broad horizontal shelf rhythms, especially through its upper and middle thirds.",
                "The exact 60 m footprint and foliage instance count both fall, so the next pass must restore irregular fine-scale crown mass without returning to synchronized tiers.",
                "Only one form is evaluated; no handoff, temporal, ecology, corridor, desktop, VR, or native-art promotion gate is closed.",
            ],
            "decision": (
                "Retain V22 as the open-grown crown-topology baseline if the automated "
                "gate passes, but keep visual, corridor, all-form, and production promotion "
                "closed. Next densify the crown with asynchronous secondary shoot clusters "
                "while preserving the de-tiered scheduling and exact-camera measurement."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "v22_crown_topology_baseline_retained": topology_gate_passed,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v22_detiered_crown_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
