"""Compare V18.2 and V19 cordilleran-cypress scale-leaf review captures."""

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
    "v19_authored_scale_leaf": {
        "capture_root": "FutaleufuCordilleraCypressAuthoredScaleLeafHierarchy",
        "report": "futaleufu_cordillera_cypress_v19_pve_open_grown_conical_"
        "authored_scale_leaf_hierarchy_report.json",
    },
    "v19_1_dense_authored_scale_leaf": {
        "capture_root": "FutaleufuCordilleraCypressDenseAuthoredScaleLeafHierarchy",
        "report": "futaleufu_cordillera_cypress_v19_1_pve_open_grown_conical_"
        "dense_authored_scale_leaf_hierarchy_report.json",
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
        (
            "v18_2_to_v19",
            "v18_2_compact_connected",
            "v19_authored_scale_leaf",
        ),
        (
            "v19_to_v19_1",
            "v19_authored_scale_leaf",
            "v19_1_dense_authored_scale_leaf",
        ),
    ):
        comparisons = {}
        for capture_id, filename in CAPTURES.items():
            before_path = saved_root / VARIANTS[before_key]["capture_root"] / filename
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
        "schema": (
            "raftsim.unreal.futaleufu_cordillera_cypress_scale_leaf_review.v19"
        ),
        "river_id": "futaleufu_terminator",
        "candidate": "v19_1_open_grown_conical_dense_authored_scale_leaf_hierarchy",
        "status": (
            "authored_scale_leaf_mechanism_retained_visual_and_corridor_promotion_rejected"
        ),
        "comparison_contract": {
            "fixed": [
                "project-owned V17 PVE growth graph and seed",
                "3626 live-foliage transforms",
                "24.68 m open-grown tree envelope and connected PVE woody collection",
                "exact closeup, 60 m source, and 60 m multi-view HLOD cameras",
            ],
            "v19_changed": (
                "replace V18.2 repeated broad spray crops with sixteen deterministic "
                "project-owned scale-leaf tiles and explicit connected leaf-card shoots"
            ),
            "v19_1_changed": (
                "increase branch-hugging imbricate leaf density and shorten the authored "
                "shoot hierarchy while retaining the same atlas and renderer split"
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
            "whole_spray_image_tiles": False,
            "botanical_measurement_claimed": False,
            "renderer_split": (
                "Nanite connected wood plus traditional-raster masked micro-foliage"
            ),
        },
        "structural_evidence": {
            key: {
                "palette_mode": report["palette_mode"],
                "foliage_instance_count": report["generated_collection"][
                    "foliage_instance_count"
                ],
                "impostor_source_vertex_count": report["local_impostor_source"][
                    "vertex_count_lod0"
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
                "V19 removes external and repeated whole-spray photo crops from the near source.",
                "The connected-wood plus traditional-raster micro-foliage split preserves explicit leaf geometry; the first merged Nanite pass was correctly rejected after collapsing it.",
                "V19.1 raises multi-view atlas coverage from V19's 0.087-0.093 range to 0.131-0.146 without reintroducing whole-spray image tiles.",
            ],
            "rejected": [
                "V19 is too sparse at close and river distance, with isolated lanceolate cards instead of attached imbricate cypress scales.",
                "V19.1 is denser but its closeup still reads as discrete broad leaves on a regular comb-like shoot rather than Austrocedrus scale foliage.",
                "The V19.1 60 m source remains noisy and detached, while the unlit HLOD crushes the crown into an overly dark mass.",
                "Neither authored candidate matches V18.2's fuller distance silhouette or clears native-species, 20/28/36 m handoff, temporal, wind, desktop, or target-VR gates.",
            ],
            "decision": (
                "Retain the project-owned atlas generator, explicit connected shoot geometry, "
                "and Nanite-wood/traditional-raster renderer split as reusable mechanisms. "
                "Reject V19 and V19.1 as near art, do not regenerate the other seven forms, "
                "and do not place cypress in the corridor. The next art pass needs a "
                "rights-reviewed native or Cupressaceae branch source with enough independent "
                "sprays, or a botanical authored shoot model whose overlapping scales read "
                "correctly in closeup before repeating the exact gate."
            ),
        },
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / (
        "futaleufu_cordillera_cypress_v19_scale_leaf_hierarchy_visual_review.json"
    )
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
