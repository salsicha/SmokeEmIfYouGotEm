"""Compare the V18 cordilleran-cypress twig-hierarchy review captures."""

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
    "v18_disconnected": {
        "capture_root": "FutaleufuCordilleraCypressTwigHierarchy",
        "report": "futaleufu_cordillera_cypress_v18_pve_"
        "open_grown_conical_twig_hierarchy_report.json",
    },
    "v18_1_connected": {
        "capture_root": "FutaleufuCordilleraCypressConnectedTwigHierarchy",
        "report": "futaleufu_cordillera_cypress_v18_1_pve_open_grown_conical_"
        "connected_twig_hierarchy_report.json",
    },
    "v18_2_compact_connected": {
        "capture_root": "FutaleufuCordilleraCypressCompactConnectedTwigHierarchy",
        "report": "futaleufu_cordillera_cypress_v18_2_pve_open_grown_conical_"
        "compact_connected_twig_hierarchy_report.json",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _comparison(before_path: Path, after_path: Path) -> dict:
    before = np.asarray(Image.open(before_path).convert("RGB"), dtype=np.int16)
    after = np.asarray(Image.open(after_path).convert("RGB"), dtype=np.int16)
    if before.shape != after.shape:
        raise ValueError(f"capture dimensions differ: {before.shape} != {after.shape}")

    channel_delta = np.abs(before - after)
    maximum_delta = np.max(channel_delta, axis=2)
    before_range = np.max(before, axis=2) - np.min(before, axis=2)
    after_range = np.max(after, axis=2) - np.min(after, axis=2)
    before_mask = (np.min(before, axis=2) < 75) & (
        (before_range > 12) | (np.mean(before, axis=2) < 55)
    )
    after_mask = (np.min(after, axis=2) < 75) & (
        (after_range > 12) | (np.mean(after, axis=2) < 55)
    )
    intersection = int(np.count_nonzero(before_mask & after_mask))
    union = int(np.count_nonzero(before_mask | after_mask))
    return {
        "before": {"path": str(before_path), "sha256": _sha256(before_path)},
        "after": {"path": str(after_path), "sha256": _sha256(after_path)},
        "changed_pixel_fraction_max_channel_gt_12": float(np.mean(maximum_delta > 12)),
        "mean_absolute_channel_delta": float(np.mean(channel_delta)),
        "dark_chromatic_foreground_mask": {
            "contract": "min_channel_lt_75 and (channel_range_gt_12 or mean_rgb_lt_55)",
            "before_pixels": int(np.count_nonzero(before_mask)),
            "after_pixels": int(np.count_nonzero(after_mask)),
            "intersection_over_union": float(intersection / max(union, 1)),
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
    transitions = {}
    for transition, before_key, after_key in (
        ("v18_to_v18_1", "v18_disconnected", "v18_1_connected"),
        ("v18_1_to_v18_2", "v18_1_connected", "v18_2_compact_connected"),
    ):
        comparisons = {}
        for capture_id, filename in CAPTURES.items():
            before_path = (
                saved_root / VARIANTS[before_key]["capture_root"] / filename
            )
            after_path = saved_root / VARIANTS[after_key]["capture_root"] / filename
            comparison = _comparison(before_path, after_path)
            for side in ("before", "after"):
                comparison[side]["path"] = str(
                    Path(comparison[side]["path"]).relative_to(repo_root)
                )
            comparisons[capture_id] = comparison
        transitions[transition] = {
            "before": before_key,
            "after": after_key,
            "capture_comparisons": comparisons,
        }

    output = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_twig_review.v1",
        "river_id": "futaleufu_terminator",
        "candidate": "v18_2_open_grown_conical_compact_connected_twig_hierarchy",
        "status": "connected_geometry_mechanism_retained_source_art_and_corridor_promotion_rejected",
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "V18 branch-scale atlas, material defaults, cameras, and HLOD baker",
                "24.68 m open-grown tree envelope and connected PVE woody collection",
            ],
            "v18_changed": "replace disconnected curved cards with a two-material live twig containing connected authored wood and foliage",
            "v18_2_changed": "shorten eight lateral woody connectors while preserving the main twig axis and foliage-card layout",
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
                "tree_vertex_count": report["generated_collection"]["vertex_count"],
                "tree_triangle_count": report["generated_collection"]["triangle_count"],
                "foliage_instance_count": report["generated_collection"][
                    "foliage_instance_count"
                ],
                "impostor_source_material_slot_count": report["local_impostor_source"][
                    "material_slot_count"
                ],
                "atlas_coverage_fraction_range": report[
                    "local_multi_view_atlas_hlod"
                ]["coverage_fraction_range"],
            }
            for key, report in reports.items()
        },
        "transitions": transitions,
        "rights_reviewed_species_references": {
            "status": "reference_only_no_external_photo_pixels_vendored_or_derived",
            "whole_tree_morphology": {
                "creator": "Krzysztof Ziarnek, Kenraiz",
                "license": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0",
                "files": [
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz01.jpg",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz02.jpg",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz03.jpg",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz04.jpg",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz05.jpg",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_kz06.jpg",
                ],
            },
            "scale_leaf_morphology": {
                "creator": "Gagea",
                "license": "CC BY-SA 3.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/3.0",
                "files": [
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_-_branch_-_01.JPG",
                    "https://commons.wikimedia.org/wiki/File:Austrocedrus_chilensis_-_leaves_-_01.JPG",
                ],
            },
            "screening_decision": "Retain as species and crown-morphology references. Natural forest backgrounds prevent a trustworthy automatic alpha extraction, and the share-alike leaf images require a separately reviewed derivative-license boundary before any pixel-derived texture is committed.",
        },
        "human_review": {
            "accepted": [
                "V18.1 proves that converted PVE live twigs preserve separate bark and foliage material slots and connected woody attachment.",
                "V18.2 removes the oversized lateral spikes that dominate the V18.1 closeup while retaining a denser 60 m crown than disconnected V18.",
                "The exact 60 m HLOD continues to preserve the source silhouette; the two connected candidates remain close at 0.146-0.170 atlas coverage while disconnected V18 remains lower at 0.095-0.106.",
            ],
            "rejected": [
                "Disconnected V18 leaves visible gaps between branch-scale spray cards.",
                "V18.1 overextends woody laterals through masked sprays and reads as a cluster of sharpened sticks.",
                "V18.2 still exposes repeated flat spray crops in closeup and retains coarse horizontal shelf rhythms at 60 m.",
                "The current source atlas does not provide geometric scale leaves or enough independent branch-spray art for a photoreal near tier.",
                "The 20/28/36 m authority, moving-camera temporal, wind, packaged desktop, and target-VR gates remain open.",
            ],
            "decision": "Retain V18.2 as the connected live-twig geometry basis, but do not regenerate the other seven forms or place cypress in the corridor. The next pass must replace the repeated photo-card near art with a rights-reviewed native/Cupressaceae branch source or authored scale-leaf geometry, then repeat this exact isolated gate before LOD and platform work.",
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v18_twig_hierarchy_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
