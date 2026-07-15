"""Compare the V20 and V20.1 measured cordilleran-cypress spray candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


CAPTURES = {
    "exact_60m_source": "open_grown_conical_river_distance_60m.png",
    "branch_spray_closeup": "open_grown_conical_branch_spray_closeup.png",
    "exact_60m_hlod": "open_grown_conical_multiview_atlas_hlod_60m.png",
}
VARIANTS = {
    "v20_botanical_flattened_spray": {
        "capture_root": "FutaleufuCordilleraCypressBotanicalFlattenedSprayHierarchy",
        "report": "futaleufu_cordillera_cypress_v20_pve_open_grown_conical_"
        "botanical_flattened_spray_hierarchy_report.json",
    },
    "v20_1_dense_botanical_flattened_spray": {
        "capture_root": (
            "FutaleufuCordilleraCypressDenseBotanicalFlattenedSprayHierarchy"
        ),
        "report": "futaleufu_cordillera_cypress_v20_1_pve_open_grown_conical_"
        "dense_botanical_flattened_spray_hierarchy_report.json",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _foreground(rgb: np.ndarray) -> np.ndarray:
    channel_range = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    return (np.min(rgb, axis=2) < 75) & (
        (channel_range > 12) | (np.mean(rgb, axis=2) < 55)
    )


def _capture_metrics(path: Path) -> dict:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    mask = _foreground(rgb)
    foreground = rgb[mask]
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "dark_chromatic_foreground_pixels": int(np.count_nonzero(mask)),
        "foreground_mean_rgb": [float(value) for value in np.mean(foreground, axis=0)],
        "foreground_median_rgb": [
            float(value) for value in np.median(foreground, axis=0)
        ],
    }


def _comparison(before_path: Path, after_path: Path) -> dict:
    before = np.asarray(Image.open(before_path).convert("RGB"), dtype=np.int16)
    after = np.asarray(Image.open(after_path).convert("RGB"), dtype=np.int16)
    if before.shape != after.shape:
        raise ValueError(f"capture dimensions differ: {before.shape} != {after.shape}")
    before_mask = _foreground(before)
    after_mask = _foreground(after)
    maximum_delta = np.max(np.abs(before - after), axis=2)
    intersection = int(np.count_nonzero(before_mask & after_mask))
    union = int(np.count_nonzero(before_mask | after_mask))
    return {
        "before": _capture_metrics(before_path),
        "after": _capture_metrics(after_path),
        "changed_pixel_fraction_max_channel_gt_12": float(np.mean(maximum_delta > 12)),
        "mean_absolute_channel_delta": float(np.mean(np.abs(before - after))),
        "dark_chromatic_foreground_intersection_over_union": float(
            intersection / max(union, 1)
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
            / VARIANTS["v20_botanical_flattened_spray"]["capture_root"]
            / filename
        )
        after_path = (
            saved_root
            / VARIANTS["v20_1_dense_botanical_flattened_spray"]["capture_root"]
            / filename
        )
        comparison = _comparison(before_path, after_path)
        for side in ("before", "after"):
            comparison[side]["path"] = str(
                Path(comparison[side]["path"]).relative_to(repo_root)
            )
        comparisons[capture_id] = comparison

    source_pixels = comparisons["exact_60m_source"]
    closeup_pixels = comparisons["branch_spray_closeup"]
    v20_1_source_count = source_pixels["after"][
        "dark_chromatic_foreground_pixels"
    ]
    v20_1_hlod_count = comparisons["exact_60m_hlod"]["after"][
        "dark_chromatic_foreground_pixels"
    ]
    output = {
        "schema": (
            "raftsim.unreal.futaleufu_cordillera_cypress_dense_botanical_review.v20_1"
        ),
        "river_id": "futaleufu_terminator",
        "candidate": "v20_1_open_grown_conical_dense_botanical_flattened_spray",
        "status": (
            "residency_density_and_color_correction_retained_visual_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "V20 deterministic 18-23 cm measured spray tiles and material defaults",
                "24.68 m open-grown tree envelope",
                "exact closeup, 60 m source, and 60 m multi-view HLOD cameras",
            ],
            "v20_1_changed": [
                "classify BotanicalSpray textures as native leaf textures so full-resolution mips remain resident and 0.42 alpha coverage survives repeated runs",
                "layer three measured sprays on each main branchlet and two on each lateral branchlet",
                "replace rejected raw-albedo world-normal relighting with inverse-opacity source-lit color and bounded RGB gain [1.10, 1.38, 0.90]",
            ],
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
                "botanical_spray_layering": report["workflow"].get(
                    "botanical_spray_layering"
                ),
                "hlod_shading": report["workflow"].get("hlod_shading"),
                "foliage_instance_count": report["generated_collection"][
                    "foliage_instance_count"
                ],
                "impostor_source_triangle_count": report["local_impostor_source"][
                    "triangle_count_lod0"
                ],
                "impostor_source_nanite_enabled": report["local_impostor_source"][
                    "nanite_enabled"
                ],
                "atlas_coverage_fraction_range": report[
                    "local_multi_view_atlas_hlod"
                ]["coverage_fraction_range"],
            }
            for key, report in reports.items()
        },
        "capture_comparisons": comparisons,
        "derived_findings": {
            "closeup_foreground_increase_fraction": (
                closeup_pixels["after"]["dark_chromatic_foreground_pixels"]
                / closeup_pixels["before"]["dark_chromatic_foreground_pixels"]
                - 1.0
            ),
            "exact_60m_source_foreground_increase_fraction": (
                v20_1_source_count
                / source_pixels["before"]["dark_chromatic_foreground_pixels"]
                - 1.0
            ),
            "v20_1_hlod_to_source_foreground_ratio": (
                v20_1_hlod_count / v20_1_source_count
            ),
        },
        "human_review": {
            "accepted": [
                "The corrected BotanicalSpray import contract keeps the full-resolution measured scales visible across fresh and repeated editor runs instead of depending on a newly imported resident mip.",
                "Three main and two lateral spray layers make the closeup materially denser without changing the measured tiles or reintroducing broad leaves and whole-spray photographs.",
                "The bounded source-lit HLOD correction removes the failed raw-relit blue-black response and preserves the complete trunk and crown silhouette.",
            ],
            "rejected": [
                "V20.1 remains visibly procedural and branch-heavy in closeup; exposed stems and repeated planar fan rhythms still dominate the fine scale foliage.",
                "The 60 m source improves but remains skeletal compared with V18.2's distance silhouette.",
                "The HLOD dark-foreground footprint remains about twice the exact-source footprint and is still materially darker, so it cannot define a 20/28/36 m handoff.",
                "Only the open-grown form has been evaluated; temporal wind, ecology, packaged desktop, target-VR, and native-species art review remain open.",
            ],
            "decision": (
                "Retain the BotanicalSpray residency/alpha fix, measured-spray layering, and "
                "source-lit HLOD color-correction mechanism. Reject V20.1 for visual, "
                "corridor, all-form, and production promotion. The next source pass must "
                "increase true flattened branchlet mass and reduce repeated exposed wood "
                "before separately calibrating HLOD coverage and luminance at 20/28/36 m."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v20_1_dense_botanical_spray_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
