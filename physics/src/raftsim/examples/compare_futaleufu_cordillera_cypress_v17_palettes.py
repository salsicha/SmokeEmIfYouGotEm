"""Compare the flat-card and curved-shell V17 cypress review captures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


PAIRS = {
    "exact_60m_source": "open_grown_conical_river_distance_60m.png",
    "branch_spray_closeup": "open_grown_conical_branch_spray_closeup.png",
    "exact_60m_hlod": "open_grown_conical_multiview_atlas_hlod_60m.png",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _comparison(flat_path: Path, curved_path: Path) -> dict:
    flat = np.asarray(Image.open(flat_path).convert("RGB"), dtype=np.int16)
    curved = np.asarray(Image.open(curved_path).convert("RGB"), dtype=np.int16)
    if flat.shape != curved.shape:
        raise ValueError(f"capture dimensions differ: {flat.shape} != {curved.shape}")

    channel_delta = np.abs(flat - curved)
    maximum_delta = np.max(channel_delta, axis=2)
    flat_range = np.max(flat, axis=2) - np.min(flat, axis=2)
    curved_range = np.max(curved, axis=2) - np.min(curved, axis=2)
    flat_mask = (np.min(flat, axis=2) < 75) & (
        (flat_range > 12) | (np.mean(flat, axis=2) < 55)
    )
    curved_mask = (np.min(curved, axis=2) < 75) & (
        (curved_range > 12) | (np.mean(curved, axis=2) < 55)
    )
    intersection = int(np.count_nonzero(flat_mask & curved_mask))
    union = int(np.count_nonzero(flat_mask | curved_mask))
    return {
        "flat": {"path": str(flat_path), "sha256": _sha256(flat_path)},
        "curved": {"path": str(curved_path), "sha256": _sha256(curved_path)},
        "changed_pixel_fraction_max_channel_gt_12": float(np.mean(maximum_delta > 12)),
        "mean_absolute_channel_delta": float(np.mean(channel_delta)),
        "dark_chromatic_foreground_mask": {
            "contract": "min_channel_lt_75 and (channel_range_gt_12 or mean_rgb_lt_55)",
            "flat_pixels": int(np.count_nonzero(flat_mask)),
            "curved_pixels": int(np.count_nonzero(curved_mask)),
            "intersection_over_union": float(intersection / max(union, 1)),
        },
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    saved_root = repo_root / "unreal/Saved/RaftSimPveReview"
    flat_root = saved_root / "FutaleufuCordilleraCypress"
    curved_root = saved_root / "FutaleufuCordilleraCypressCurvedShell"
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    flat_report_path = report_root / (
        "futaleufu_cordillera_cypress_v17_pve_open_grown_conical_report.json"
    )
    curved_report_path = report_root / (
        "futaleufu_cordillera_cypress_v17_pve_"
        "open_grown_conical_curved_shells_report.json"
    )
    flat_report = json.loads(flat_report_path.read_text(encoding="utf-8"))
    curved_report = json.loads(curved_report_path.read_text(encoding="utf-8"))

    comparisons = {
        key: _comparison(flat_root / filename, curved_root / filename)
        for key, filename in PAIRS.items()
    }
    for comparison in comparisons.values():
        for side in ("flat", "curved"):
            comparison[side]["path"] = str(
                Path(comparison[side]["path"]).relative_to(repo_root)
            )

    output = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_palette_review.v1",
        "river_id": "futaleufu_terminator",
        "candidate": "v17_open_grown_conical_curved_shells",
        "status": "curved_shell_mechanism_retained_visual_and_corridor_promotion_rejected",
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE tree graph and seed",
                "three V10 broad-spray source textures",
                "3626 foliage instances",
                "material defaults and photographic capture settings",
                "exact source camera and multi-view HLOD baker",
            ],
            "changed": "each foliage mesh uses three six-segment curved shells instead of three flat cards",
            "flat_report": str(flat_report_path.relative_to(repo_root)),
            "curved_report": str(curved_report_path.relative_to(repo_root)),
        },
        "structural_evidence": {
            "flat_foliage_instance_count": flat_report["generated_collection"][
                "foliage_instance_count"
            ],
            "curved_foliage_instance_count": curved_report["generated_collection"][
                "foliage_instance_count"
            ],
            "flat_atlas_coverage_fraction_range": flat_report[
                "local_multi_view_atlas_hlod"
            ]["coverage_fraction_range"],
            "curved_atlas_coverage_fraction_range": curved_report[
                "local_multi_view_atlas_hlod"
            ]["coverage_fraction_range"],
            "flat_triangles_per_live_twig_mesh": 6,
            "curved_triangles_per_live_twig_mesh": 36,
            "estimated_flat_live_foliage_triangles": 21756,
            "estimated_curved_live_foliage_triangles": 130536,
        },
        "capture_comparisons": comparisons,
        "human_review": {
            "accepted": [
                "The branch closeup follows a bent surface and no longer exposes the baseline's large flat polygon faces.",
                "The exact 60 m source and HLOD retain green response, branch detail, and nearly the same foreground coverage.",
                "The isolated palette and capture namespaces preserve a rerunnable flat baseline.",
            ],
            "rejected": [
                "Each shell still carries one complete broad-spray image, so repeated whole-spray motifs remain visible.",
                "The PVE crown still reads as coarse horizontal shelves rather than a continuous irregular Austrocedrus crown.",
                "The HLOD faithfully bakes those source limitations and is not photoreal production art.",
                "The 20/28/36 m authority, moving-camera temporal, wind, packaged desktop, and target-VR gates have not run.",
            ],
            "decision": "Retain curved_shells as the preferred V17 source-palette experiment, but do not regenerate the other seven forms or place it in the corridor. Next decompose the whole-spray source into connected branch-scale twig hierarchy before repeating this paired gate.",
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v17_curved_shell_palette_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
