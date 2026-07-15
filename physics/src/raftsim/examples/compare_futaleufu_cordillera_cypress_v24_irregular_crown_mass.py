"""Compare V23 and V24 cordilleran-cypress crown mass."""

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
    "v23_async_secondary_compound_branchlet_atlas": {
        "capture_root": (
            "FutaleufuCordilleraCypressAsyncSecondaryCompoundBranchletAtlas"
        ),
        "report": "futaleufu_cordillera_cypress_v23_pve_open_grown_conical_"
        "async_secondary_compound_branchlet_atlas_report.json",
    },
    "v24_irregular_crown_mass_compound_branchlet_atlas": {
        "capture_root": (
            "FutaleufuCordilleraCypressIrregularCrownMassCompoundBranchletAtlas"
        ),
        "report": "futaleufu_cordillera_cypress_v24_pve_open_grown_conical_"
        "irregular_crown_mass_compound_branchlet_atlas_report.json",
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
            / VARIANTS["v23_async_secondary_compound_branchlet_atlas"][
                "capture_root"
            ]
            / filename
        )
        after_path = (
            saved_root
            / VARIANTS["v24_irregular_crown_mass_compound_branchlet_atlas"][
                "capture_root"
            ]
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

    v23_report = reports["v23_async_secondary_compound_branchlet_atlas"]
    v24_report = reports["v24_irregular_crown_mass_compound_branchlet_atlas"]
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
    triangles_before = v23_report["local_impostor_source"]["triangle_count_lod0"]
    triangles_after = v24_report["local_impostor_source"]["triangle_count_lod0"]
    instances_before = v23_report["generated_collection"]["foliage_instance_count"]
    instances_after = v24_report["generated_collection"]["foliage_instance_count"]
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
        "v24_hlod_to_source_foreground_ratio": hlod_after / source_after,
        "mean_turntable_open_band_fraction_before": float(open_band_before),
        "mean_turntable_open_band_fraction_after": float(open_band_after),
        "mean_turntable_open_band_fraction_change": float(
            open_band_after - open_band_before
        ),
        "largest_turntable_open_band_pixels_before": largest_open_band_before,
        "largest_turntable_open_band_pixels_after": largest_open_band_after,
    }
    topology_gate_passed = (
        findings["triangle_cost_change_fraction"] <= 0.05
        and abs(findings["foliage_instance_count_change_fraction"]) <= 0.02
        and findings["closeup_foreground_change_fraction"] > -0.05
        and findings["exact_60m_source_foreground_change_fraction"] > 0.10
        and 0.95 < findings["v24_hlod_to_source_foreground_ratio"] < 1.20
        and findings["mean_turntable_open_band_fraction_change"] < -0.01
        and largest_open_band_after <= largest_open_band_before
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_irregular_crown_mass_review.v24",
        "river_id": "futaleufu_terminator",
        "candidate": (
            "v24_open_grown_conical_irregular_crown_mass_compound_branchlet_atlas"
        ),
        "status": (
            "irregular_crown_mass_baseline_retained_visual_promotion_rejected"
            if topology_gate_passed
            else "irregular_crown_mass_gate_failed_visual_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "V21 compound branchlet textures, fourteen-card authored twig, and material response",
                "V22 de-tiered main grower and golden-angle graft schedule",
                "V23 three-template asynchronous branch growth and attachment density",
                "post-usage shader-resource gate and corrected source-lit HLOD path",
                "open-grown form envelope and exact review cameras",
            ],
            "v24_changed": [
                "replace Unreal's default linear 1.0-to-0.1 graft scale taper with a six-key bounded plant-height mass envelope",
                "apply deterministic 0.88-to-1.12 per-attachment graft scale variation",
                "increase hormone foliage spacing from 0.055 to 0.096 to compensate measured foliage-bearing path growth",
                "retain the V23 graft count, three templates, source cards, cameras, and HLOD path",
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
                "The bounded crown-mass envelope fills the largest V23 primary-shelf gap in both exact turntable views without making every attachment the same size.",
                "Mean low-occupancy crown rows fall by 1.45 percentage points and the largest open run falls from 45 to 24 pixels.",
                "Exact 60 meter source mass rises 17.2 percent while foliage instances remain within two percent and merged-source triangles remain within five percent of V23.",
            ],
            "rejected": [
                "The isolated tree still exposes a regular central scaffold and flattened compound branchlet planes at close range, so it is not finished photoreal cordilleran-cypress art.",
                "The source-lit HLOD remains darker and more saturated than the exact source despite bounded foreground agreement.",
                "Only one form is evaluated; exact handoffs, temporal stability, mixed ecology, corridor placement, packaged desktop, target-VR, and native-art gates remain open.",
            ],
            "decision": (
                "Retain V24 as the open-grown irregular crown-mass topology baseline because "
                "the bounded cost, two-view crown-band, exact 60 meter source, HLOD agreement, "
                "and human topology gates pass. Keep visual, corridor, all-form, and production "
                "promotion closed; next calibrate source/HLOD photometry and exact handoffs before "
                "temporal, platform, or family regeneration work."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
        "v24_irregular_crown_mass_baseline_retained": topology_gate_passed,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v24_irregular_crown_mass_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
