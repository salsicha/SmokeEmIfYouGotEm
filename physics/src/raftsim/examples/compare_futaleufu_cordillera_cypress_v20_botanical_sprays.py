"""Compare V20 botanical cypress sprays with the retained V18.2/V19.1 baselines."""

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
    "v18_2_compact_connected": {
        "capture_root": "FutaleufuCordilleraCypressCompactConnectedTwigHierarchy",
        "report": "futaleufu_cordillera_cypress_v18_2_pve_open_grown_conical_"
        "compact_connected_twig_hierarchy_report.json",
    },
    "v19_1_dense_authored_scale_leaf": {
        "capture_root": "FutaleufuCordilleraCypressDenseAuthoredScaleLeafHierarchy",
        "report": "futaleufu_cordillera_cypress_v19_1_pve_open_grown_conical_"
        "dense_authored_scale_leaf_hierarchy_report.json",
    },
    "v20_botanical_flattened_spray": {
        "capture_root": "FutaleufuCordilleraCypressBotanicalFlattenedSprayHierarchy",
        "report": "futaleufu_cordillera_cypress_v20_pve_open_grown_conical_"
        "botanical_flattened_spray_hierarchy_report.json",
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
    for transition, before_key in (
        ("v18_2_to_v20", "v18_2_compact_connected"),
        ("v19_1_to_v20", "v19_1_dense_authored_scale_leaf"),
    ):
        comparisons = {}
        for capture_id, filename in CAPTURES.items():
            before_path = saved_root / VARIANTS[before_key]["capture_root"] / filename
            after_path = (
                saved_root
                / VARIANTS["v20_botanical_flattened_spray"]["capture_root"]
                / filename
            )
            comparison = _comparison(before_path, after_path)
            for side in ("before", "after"):
                comparison[side]["path"] = str(
                    Path(comparison[side]["path"]).relative_to(repo_root)
                )
            comparisons[capture_id] = comparison
        transitions[transition] = {
            "before": before_key,
            "after": "v20_botanical_flattened_spray",
            "capture_comparisons": comparisons,
        }

    output = {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_botanical_review.v20",
        "river_id": "futaleufu_terminator",
        "candidate": "v20_open_grown_conical_botanical_flattened_spray_hierarchy",
        "status": "botanical_contract_retained_visual_and_corridor_promotion_rejected",
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "24.68 m open-grown tree envelope and connected PVE woody collection",
                "exact closeup, 60 m source, and 60 m multi-view HLOD cameras",
            ],
            "v20_changed": (
                "replace V19.1 broad explicit leaf cards with sixteen deterministic "
                "18-23 cm flattened sprays carrying 0.5-2 mm facial and 2-5 mm lateral "
                "scale leaves derived from published dimensional facts"
            ),
            "reports": {
                key: str((report_root / value["report"]).relative_to(repo_root))
                for key, value in VARIANTS.items()
            },
        },
        "source_art_contract": {
            "ownership": "deterministic project-owned generated pixels and geometry",
            "external_photo_pixels_vendored": False,
            "external_reference_pixels_derived": False,
            "external_geometry_copied": False,
            "whole_external_spray_image_tiles": False,
            "botanical_measurement_claimed": True,
            "renderer_split": (
                "Nanite connected wood plus traditional-raster masked micro-foliage"
            ),
        },
        "botanical_provenance": {
            "sources": [
                {
                    "authority": (
                        "Sistema de Informacion de Biodiversidad, Administracion de "
                        "Parques Nacionales, Argentina"
                    ),
                    "url": "https://sib.gob.ar/especies/austrocedrus-chilensis",
                    "facts_used": [
                        "flattened planar branchlets",
                        "opposite imbricate dimorphic scale leaves",
                        "2-5 mm keeled lateral leaves with two pale stomatal bands",
                        "0.5-2 mm triangular facial leaves",
                    ],
                    "pixels_or_geometry_copied": False,
                },
                {
                    "authority": "The Gymnosperm Database",
                    "url": "https://www.conifers.org/cu/Austrocedrus.php",
                    "facts_used": [
                        "dense flat shoots",
                        "lateral leaves longer than facial leaves with incurved tips",
                        "blunt facial leaves and whitish lower-surface bands",
                    ],
                    "pixels_or_geometry_copied": False,
                },
            ],
            "measurement_ranges": {
                "lateral_leaf_length_mm": [2.0, 5.0],
                "facial_leaf_length_mm": [0.5, 2.0],
                "tile_physical_spray_length_cm": [18.0, 23.0],
            },
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
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
                "exact_60m_source_capture_produced": report["local_impostor_source"][
                    "exact_camera_60m_capture_produced"
                ],
                "exact_60m_hlod_capture_produced": report[
                    "local_multi_view_atlas_hlod"
                ]["exact_source_camera_60m_capture_produced"],
            }
            for key, report in reports.items()
        },
        "transitions": transitions,
        "human_review": {
            "accepted": [
                "V20 is the first project-owned source in this sequence whose closeup uses the published dimorphic scale-leaf ranges and flattened shoot arrangement instead of broad lanceolate leaves or whole-spray photographs.",
                "The deterministic generator and source notes establish a reproducible botanical baseline without copying external pixels or geometry.",
                "Multi-view atlas coverage returns to the retained V18.2 silhouette range while preserving the Nanite-wood/traditional-raster foliage split.",
            ],
            "rejected": [
                "The V20 closeup is too sparse: exposed woody stems dominate and the fine scales do not overlap into dense branchlet masses.",
                "At 60 m the source collapses into a skeletal crown with detached noisy pinpricks, a substantial visual regression from V18.2's fuller silhouette.",
                "The unlit HLOD is much darker and more opaque than the sparse source, so it does not preserve the accepted near-source appearance or establish a trustworthy handoff.",
                "Only one form has been rendered; 20/28/36 m authority, temporal wind, ecology, packaged desktop, and target-VR gates remain open.",
            ],
            "decision": (
                "Retain V20 as the factual morphology and source-ownership baseline, but "
                "reject visual, corridor, all-form, and production promotion. Keep V18.2 "
                "only as the density and distance-silhouette benchmark; its broad repeated "
                "spray art remains rejected. V20.1 must overlap more measured sprays per "
                "connected branchlet, reduce exposed stem rhythm, and correct HLOD color, "
                "opacity, and relighting before repeating the exact three-camera gate."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v20_botanical_spray_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
