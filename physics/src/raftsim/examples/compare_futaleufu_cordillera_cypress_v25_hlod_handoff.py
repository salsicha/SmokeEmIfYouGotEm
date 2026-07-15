"""Review V25 cypress HLOD photometry and exact handoff authority."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
    _foreground,
)


DISTANCES = ("20m", "28m", "36m")
EXPECTED_AUTHORITY = {"20m": "source_only", "28m": "hlod_only", "36m": "hlod_only"}
V24_REPORT = (
    "futaleufu_cordillera_cypress_v24_pve_open_grown_conical_"
    "irregular_crown_mass_compound_branchlet_atlas_report.json"
)
V25_REPORT = (
    "futaleufu_cordillera_cypress_v25_pve_open_grown_conical_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)


def _intersection_photometry(source_path: Path, hlod_path: Path) -> dict:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.int16)
    hlod = np.asarray(Image.open(hlod_path).convert("RGB"), dtype=np.int16)
    intersection = _foreground(source) & _foreground(hlod)
    if not intersection.any():
        raise ValueError("source and HLOD have no intersecting foreground")
    source_pixels = source[intersection].astype(np.float64)
    hlod_pixels = hlod[intersection].astype(np.float64)
    return {
        "intersection_pixels": int(intersection.sum()),
        "source_mean_rgb": source_pixels.mean(axis=0).tolist(),
        "hlod_mean_rgb": hlod_pixels.mean(axis=0).tolist(),
        "hlod_minus_source_mean_rgb": (hlod_pixels - source_pixels)
        .mean(axis=0)
        .tolist(),
        "mean_absolute_rgb_delta": np.abs(hlod_pixels - source_pixels)
        .mean(axis=0)
        .tolist(),
    }


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
    capture_root = (
        repo_root
        / "unreal/Saved/RaftSimPveReview/"
        "FutaleufuCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"
    )
    v24_report = json.loads((report_root / V24_REPORT).read_text(encoding="utf-8"))
    v25_report = json.loads((report_root / V25_REPORT).read_text(encoding="utf-8"))

    source_60m = capture_root / "open_grown_conical_river_distance_60m.png"
    hlod_60m = capture_root / "open_grown_conical_multiview_atlas_hlod_60m.png"
    source_hlod_60m = _relative_paths(_comparison(source_60m, hlod_60m), repo_root)
    intersection_photometry = _intersection_photometry(source_60m, hlod_60m)

    handoffs = {}
    authority_gate_passed = True
    for distance in DISTANCES:
        paths = {
            authority: capture_root
            / f"open_grown_conical_handoff_{distance}_{authority}.png"
            for authority in ("source_only", "hlod_only", "combined")
        }
        source_hlod = _relative_paths(
            _comparison(paths["source_only"], paths["hlod_only"]), repo_root
        )
        expected_authority = EXPECTED_AUTHORITY[distance]
        selected = _relative_paths(
            _comparison(paths[expected_authority], paths["combined"]), repo_root
        )
        exact_hash_match = (
            selected["before"]["sha256"] == selected["after"]["sha256"]
        )
        selected_equivalent = exact_hash_match or (
            selected["changed_pixel_fraction_max_channel_gt_12"] <= 0.0001
            and selected["mean_absolute_channel_delta"] <= 0.01
            and selected["dark_chromatic_foreground_intersection_over_union"]
            >= 0.9999
        )
        authority_gate_passed &= selected_equivalent
        handoffs[distance] = {
            "expected_authority": expected_authority,
            "source_hlod_comparison": source_hlod,
            "combined_expected_comparison": selected,
            "combined_exact_hash_match": exact_hash_match,
            "combined_selected_authority_equivalent": selected_equivalent,
        }

    source_geometry_unchanged = (
        v25_report["generated_collection"]["foliage_instance_count"]
        == v24_report["generated_collection"]["foliage_instance_count"]
        and v25_report["local_impostor_source"]["triangle_count_lod0"]
        == v24_report["local_impostor_source"]["triangle_count_lod0"]
    )
    signed_rgb_delta = intersection_photometry["hlod_minus_source_mean_rgb"]
    hlod_source_foreground_ratio = (
        source_hlod_60m["after"]["dark_chromatic_foreground_pixels"]
        / source_hlod_60m["before"]["dark_chromatic_foreground_pixels"]
    )
    photometry_gate_passed = (
        source_geometry_unchanged
        and max(abs(value) for value in signed_rgb_delta) <= 4.0
        and 0.95 <= hlod_source_foreground_ratio <= 1.15
    )
    worst_handoff_change_fraction = max(
        value["source_hlod_comparison"][
            "changed_pixel_fraction_max_channel_gt_12"
        ]
        for value in handoffs.values()
    )
    minimum_handoff_foreground_iou = min(
        value["source_hlod_comparison"][
            "dark_chromatic_foreground_intersection_over_union"
        ]
        for value in handoffs.values()
    )
    no_pop_gate_passed = (
        worst_handoff_change_fraction <= 0.10
        and minimum_handoff_foreground_iou >= 0.80
    )

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_hlod_handoff_review.v25",
        "river_id": "futaleufu_terminator",
        "candidate": "v25_hlod_calibrated_irregular_crown_mass",
        "status": (
            "photometry_and_hard_authority_retained_handoff_popping_rejected"
            if photometry_gate_passed and authority_gate_passed
            else "hlod_photometry_or_authority_gate_failed"
        ),
        "comparison_contract": {
            "fixed": [
                "V24 open-grown irregular crown-mass source geometry and material",
                "V24 PVE growth seed, 2,944 foliage transforms, and 1,213,857 merged source triangles",
                "eight-azimuth by two-elevation 2048-pixel multi-view atlas bake",
                "exact 60 m and exact 20/28/36 m cameras",
            ],
            "v25_changed": [
                "atlas linear color gain from [1.10, 1.38, 0.90] to [2.60, 1.63, 1.60]",
                "hard camera-to-HLOD-actor horizontal-distance authority at 2,500 cm",
                "source-only, HLOD-only, and combined captures at 20, 28, and 36 m",
            ],
            "reports": {
                "v24": str((report_root / V24_REPORT).relative_to(repo_root)),
                "v25": str((report_root / V25_REPORT).relative_to(repo_root)),
            },
        },
        "source_geometry_unchanged": source_geometry_unchanged,
        "exact_60m": {
            "source_hlod_comparison": source_hlod_60m,
            "intersection_photometry": intersection_photometry,
            "hlod_to_source_foreground_ratio": hlod_source_foreground_ratio,
        },
        "handoffs": handoffs,
        "derived_findings": {
            "worst_handoff_source_hlod_changed_pixel_fraction": (
                worst_handoff_change_fraction
            ),
            "minimum_handoff_source_hlod_foreground_iou": (
                minimum_handoff_foreground_iou
            ),
        },
        "photometry_gate_passed": photometry_gate_passed,
        "hard_authority_gate_passed": authority_gate_passed,
        "no_pop_gate_passed": no_pop_gate_passed,
        "human_review": {
            "accepted": [
                "The calibrated 60 m HLOD matches the source intersection mean within four RGB levels per channel while keeping foreground mass bounded.",
                "Combined authority selects only the source at 20 m and only the HLOD at 28 and 36 m; the HLOD selections are byte-identical and the temporally lit source selection is pixel-equivalent.",
                "V25 leaves the retained V24 source geometry and source-cost counts unchanged.",
            ],
            "rejected": [
                "The HLOD is visibly blurrier and fuller than the source at handoff distance, so a hard switch would pop despite correct actor authority.",
                "Source/HLOD changed-pixel fraction reaches more than 20 percent and minimum foreground IoU remains near 0.5 instead of the 0.8 no-pop floor.",
                "Closeup source planes, the regular central scaffold, temporal motion, packaged desktop, target-VR, all-form, corridor, and production gates remain open.",
            ],
            "decision": "Retain the V25 color gain and hard single-representation authority mechanism, but reject handoff and visual promotion. The next pass must improve HLOD spatial registration and branch-scale detail or use a bounded complementary dither transition before moving-camera review.",
        },
        "v25_photometry_baseline_retained": photometry_gate_passed,
        "v25_hard_authority_baseline_retained": authority_gate_passed,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = (
        report_root
        / "futaleufu_cordillera_cypress_v25_hlod_handoff_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
