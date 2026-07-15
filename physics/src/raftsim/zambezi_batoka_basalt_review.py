"""Build deterministic isolated visual-review evidence for Batoka basalt modules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


V1_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v1_isolated_family_report.json"
)
V1_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v1_visual_review.json"
)
V2_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v2_isolated_family_report.json"
)
V2_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v2_visual_review.json"
)
V3_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v3_isolated_family_report.json"
)
V3_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v3_visual_review.json"
)
V4_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v4_isolated_family_report.json"
)
V4_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v4_visual_review.json"
)
V5_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v5_isolated_family_report.json"
)
V5_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v5_visual_review.json"
)
V6_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v6_isolated_family_report.json"
)
V6_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v6_visual_review.json"
)
V7_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v7_isolated_family_report.json"
)
V7_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v7_visual_review.json"
)
V8_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v8_isolated_family_report.json"
)
V8_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v8_visual_review.json"
)
V9_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v9_isolated_family_report.json"
)
V9_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v9_visual_review.json"
)
V10_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_isolated_family_report.json"
)
V10_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_visual_review.json"
)
C1_CORRIDOR_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_corridor_comparison_report.json"
)
C1_CORRIDOR_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_corridor_visual_review.json"
)
C2_CORRIDOR_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_c2_corridor_comparison_report.json"
)
C2_CORRIDOR_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_basalt_v10_c2_corridor_visual_review.json"
)
C3_TERRAIN_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v11_terrain_integrated_comparison_report.json"
)
C3_TERRAIN_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v11_terrain_integrated_visual_review.json"
)
C4_WORLD_ALIGNED_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v12_world_aligned_comparison_report.json"
)
C4_WORLD_ALIGNED_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v12_world_aligned_visual_review.json"
)
C5_VISUAL_MORPHOLOGY_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v13_visual_morphology_comparison_report.json"
)
C5_VISUAL_MORPHOLOGY_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_batoka_v13_visual_morphology_visual_review.json"
)
GENERATED_ON = "2026-07-13"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _capture_metrics(path: Path) -> dict:
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
        width, height = image.size
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    sky = (blue > green + 8.0) & (green > red + 12.0) & (red > 55.0)
    channel_range = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    ground = (
        (red > 170.0)
        & (green > 170.0)
        & (blue > 170.0)
        & (channel_range < 35.0)
    )
    foreground = ~(sky | ground)
    dark = np.max(rgb, axis=2) < 55.0
    near_black = np.max(rgb, axis=2) < 24.0
    foreground_count = max(1, int(np.count_nonzero(foreground)))
    gray = red * 0.2126 + green * 0.7152 + blue * 0.0722
    horizontal_gradient = np.abs(np.diff(gray, axis=1))
    vertical_gradient = np.abs(np.diff(gray, axis=0))
    edge_count = int(np.count_nonzero(horizontal_gradient > 18.0)) + int(
        np.count_nonzero(vertical_gradient > 18.0)
    )
    edge_sample_count = horizontal_gradient.size + vertical_gradient.size
    return {
        "sha256": _sha256(path),
        "width": width,
        "height": height,
        "mean_rgb": [float(value) for value in np.mean(rgb, axis=(0, 1))],
        "foreground_fraction": float(np.mean(foreground)),
        "dark_foreground_fraction": float(
            np.count_nonzero(dark & foreground) / foreground_count
        ),
        "near_black_foreground_fraction": float(
            np.count_nonzero(near_black & foreground) / foreground_count
        ),
        "edge_fraction": float(edge_count / max(1, edge_sample_count)),
    }


def _build_followup_visual_review(
    repo_root: Path,
    *,
    version: int,
    report_relative_path: Path,
    status: str,
    accepted_findings: list[str],
    rejection_reasons: list[str],
    next_iteration_requirements: list[str],
) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / report_relative_path
    report = json.loads(report_path.read_text(encoding="utf-8"))
    captures = []
    grouped_metrics: dict[str, list[dict]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        else:
            view_group = "river_distance_60m"
        grouped_metrics[view_group].append(metrics)
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    view_summaries = {}
    for view_group, metrics in grouped_metrics.items():
        view_summaries[view_group] = {
            "sample_count": len(metrics),
            "mean_dark_foreground_fraction": float(
                np.mean([item["dark_foreground_fraction"] for item in metrics])
            ),
            "mean_near_black_foreground_fraction": float(
                np.mean(
                    [item["near_black_foreground_fraction"] for item in metrics]
                )
            ),
            "mean_edge_fraction": float(
                np.mean([item["edge_fraction"] for item in metrics])
            ),
        }

    return {
        "schema": (
            "raftsim.unreal.zambezi_batoka_basalt_visual_review."
            f"v{version}"
        ),
        "generated_on": GENERATED_ON,
        "status": status,
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(report_relative_path),
        "source_report_sha256": _sha256(report_path),
        "review_scope": {
            "module_count": report["module_count"],
            "capture_count": report["capture_count"],
            "views_per_module": 4,
            "rhi": "offscreen Metal",
            "authority": report["authority_boundary"],
        },
        "accepted_findings": accepted_findings,
        "rejection_reasons": rejection_reasons,
        "quantitative_review": {
            "dark_pixel_definition": (
                "max(R,G,B)<55 inside the neutral-review foreground mask"
            ),
            "near_black_definition": (
                "max(R,G,B)<24 inside the neutral-review foreground mask"
            ),
            "edge_definition": "horizontal or vertical luma delta greater than 18",
            "view_summaries": view_summaries,
            "note": (
                "Metrics hash-lock the evidence and expose photometric regressions; "
                "morphology acceptance remains a human visual decision."
            ),
        },
        "next_iteration_requirements": next_iteration_requirements,
        "captures": captures,
    }


def build_zambezi_batoka_basalt_v1_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V1_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    captures = []
    view_groups: dict[str, list[dict]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        else:
            view_group = "river_distance_60m"
        view_groups[view_group].append(metrics)
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    summaries = {}
    for view_group, metrics in view_groups.items():
        summaries[view_group] = {
            "sample_count": len(metrics),
            "mean_dark_foreground_fraction": float(
                np.mean([item["dark_foreground_fraction"] for item in metrics])
            ),
            "mean_near_black_foreground_fraction": float(
                np.mean([item["near_black_foreground_fraction"] for item in metrics])
            ),
            "mean_edge_fraction": float(
                np.mean([item["edge_fraction"] for item in metrics])
            ),
        }

    return {
        "schema": "raftsim.unreal.zambezi_batoka_basalt_visual_review.v1",
        "generated_on": GENERATED_ON,
        "status": "v1_disconnected_slab_geometry_rejected_v2_connected_wall_required",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V1_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "review_scope": {
            "module_count": report["module_count"],
            "capture_count": report["capture_count"],
            "views_per_module": 4,
            "rhi": "offscreen Metal",
            "authority": report["authority_boundary"],
        },
        "accepted_findings": [
            "The command deterministically saves four independent project-owned Nanite meshes, one isolated map, sixteen exact-camera captures, and a structural report.",
            "The review remains non-colliding, performs no corridor substitution, and leaves source terrain, water, GeoClaw, custom C++ physics, forcing, and raft-contact authority unchanged.",
            "The official ZRA and ERM morphology constraints are recorded separately from generated appearance hypotheses.",
        ],
        "rejection_reasons": [
            "The stacked hexahedra read as disconnected elongated slabs rather than one coherent basalt rock mass.",
            "Vertical joints read as full-depth holes and perforations instead of fractures and recessed seams in a continuous cliff face.",
            "Turntables expose large planar side faces, floating overhangs, repeated block cadence, and unsupported organ-pipe-like separation.",
            "Closeups crush most front-facing rock to black and do not expose credible fine joint, breccia, weathering, or surface-scale detail.",
            "At 60 m the wall becomes a sparse perforated silhouette, so V1 cannot improve the rejected pasted-fragment corridor control.",
        ],
        "quantitative_review": {
            "dark_pixel_definition": "max(R,G,B)<55 inside the neutral-review foreground mask",
            "near_black_definition": "max(R,G,B)<24 inside the neutral-review foreground mask",
            "edge_definition": "horizontal or vertical luma delta greater than 18",
            "view_summaries": summaries,
            "note": "The image metrics hash-lock the rejected evidence; morphology rejection remains a human visual judgment and is not inferred from a single threshold.",
        },
        "required_v2_changes": [
            "Replace stacked independent wall blocks with a connected tessellated cliff surface.",
            "Carve bounded subvertical joint grooves into the connected mass instead of opening full-depth gaps.",
            "Express flow breaks as discontinuous shallow ledges and recessions rather than detached slabs.",
            "Increase surface tessellation and bounded relief while retaining independent module silhouettes and basal talus.",
            "Use a neutral isolated diagnostic light/material response that preserves dark basalt without crushing all front-face information.",
            "Repeat all sixteen exact-camera captures before any transient corridor comparison.",
        ],
        "captures": captures,
    }


def write_zambezi_batoka_basalt_v1_visual_review(repo_root: Path) -> Path:
    repo_root = repo_root.resolve()
    output_path = repo_root / V1_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            build_zambezi_batoka_basalt_v1_visual_review(repo_root),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return output_path


def build_zambezi_batoka_basalt_v2_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=2,
        report_relative_path=V2_REPORT_RELATIVE_PATH,
        status="v2_connected_wall_culling_defect_localized_v3_winding_fix_required",
        accepted_findings=[
            "V2 replaces the disconnected V1 slabs with a single tessellated front surface for each module.",
            "The two-sided diagnostic proves the connected source surface survives procedural-to-static-mesh conversion.",
            "Nanite meshes, map, metrics, and sixteen exact-camera captures remain deterministic and non-colliding.",
        ],
        rejection_reasons=[
            "The normal one-sided review hides the main cliff face, while the bounded two-sided diagnostic restores it.",
            "The result localizes the defect to front-face winding or culling rather than missing converted geometry.",
            "A two-sided diagnostic cannot be promoted because it would conceal the unresolved mesh contract.",
        ],
        next_iteration_requirements=[
            "Correct front triangle winding and return to a one-sided review material.",
            "Recompute front normals after the winding correction.",
            "Repeat all sixteen views without changing terrain, water, collision, or corridor authority.",
        ],
    )


def build_zambezi_batoka_basalt_v3_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=3,
        report_relative_path=V3_REPORT_RELATIVE_PATH,
        status="v3_winding_fixed_morphology_rejected_v4_ledge_talus_material_revision_required",
        accepted_findings=[
            "The corrected one-sided winding makes the connected cliff face visible from every required review camera.",
            "Reduced backing depth stops side closure geometry from dominating the module silhouette.",
            "V3 closes the V2 culling diagnosis without relaxing any authority boundary.",
        ],
        rejection_reasons=[
            "The cliff remains a nearly black low-information mass at turntable and closeup distances.",
            "Detached flow-break shelf blocks read as bright floating slabs instead of erosional ledges in one rock mass.",
            "Hexahedral talus reads as cubes and the 60 m silhouette remains soft and blob-like.",
            "The captures do not expose credible joint, breccia, weathering, or flow-unit detail.",
        ],
        next_iteration_requirements=[
            "Remove detached shelf geometry and keep flow breaks embedded in the connected wall.",
            "Replace cubic talus with deterministic angular rock meshes.",
            "Increase bounded joint contrast and neutral diagnostic visibility.",
            "Repeat the isolated review before any corridor comparison.",
        ],
    )


def build_zambezi_batoka_basalt_v4_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=4,
        report_relative_path=V4_REPORT_RELATIVE_PATH,
        status="v4_ledges_and_talus_improved_surface_rejected_v5_smooth_joint_normals_required",
        accepted_findings=[
            "Detached shelf blocks are removed and flow-break color and relief remain embedded in the connected wall.",
            "Angular multi-ring talus replaces the V3 cubic hexahedra.",
            "All four V4 modules build as Nanite visual-only meshes with collision disabled.",
        ],
        rejection_reasons=[
            "Per-cell joint and relief depth jumps fold the wall into large triangular wedges and cavities.",
            "Terrain-oriented normal correction produces inconsistent cliff lighting and closeup information loss.",
            "The dark flat review material still hides most color-band and weathering hypotheses.",
            "At 60 m the surface reads as an amorphous faceted mass rather than stacked basalt scarps.",
        ],
        next_iteration_requirements=[
            "Replace discrete joint lanes with smooth drifting fracture profiles.",
            "Use cliff-specific normals without terrain upward-normal correction.",
            "Reduce high-frequency relief and smooth the cumulative stacked-flow setbacks.",
            "Use a bounded neutral review rig and repeat the exact-camera evidence set.",
        ],
    )


def build_zambezi_batoka_basalt_v5_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=5,
        report_relative_path=V5_REPORT_RELATIVE_PATH,
        status="v5_connected_surface_readable_rejected_v6_fracture_planes_surface_detail_required",
        accepted_findings=[
            "Smooth drifting joint profiles remove the V4 chaotic folded-mass silhouette.",
            "Cliff-specific normals make the one-sided connected wall consistently visible and readable.",
            "The generator preserves angular talus, deterministic metrics, Nanite, and the visual-only collision boundary.",
        ],
        rejection_reasons=[
            "The narrow repeated joint profiles read as regularly spaced flutes instead of irregular fractured basalt planes.",
            "Smooth shared normals make the surface look poured or eroded rather than blocky and joint-controlled.",
            "The diagnostic light and exposure wash the basalt palette toward pale plaster and clip talus highlights.",
            "The flat vertex-color material has no close-range mineral, weathering, roughness, or normal detail.",
            "Large gully and flow-setback transitions still form conspicuous wedge-shaped lighting discontinuities.",
        ],
        next_iteration_requirements=[
            "Author connected macro fracture panels with controlled hard planes and irregular joint spacing.",
            "Reduce gully and flow-setback amplitudes and preserve a stepped but coherent scarp silhouette.",
            "Return the review rig to bounded neutral exposure and record all diagnostic light values.",
            "Acquire or procedurally author a rights-cleared Batoka-appropriate basalt surface set; unrelated rock analogs cannot establish lithology.",
            "Repeat isolated closeup, turntable, and 60 m gates before corridor integration.",
        ],
    )


def build_zambezi_batoka_basalt_v6_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=6,
        report_relative_path=V6_REPORT_RELATIVE_PATH,
        status="v6_rock037_surface_detail_improved_rejected_v7_scale_and_morphology_revision_required",
        accepted_findings=[
            "The hash-reviewed CC0 Rock037 maps establish a working external-pixel provenance and Unreal import path.",
            "Bounded neutral exposure restores dark fractured-rock micro-detail without the V5 washout.",
            "The connected one-sided Nanite family remains deterministic, non-colliding, and isolated from corridor authority.",
        ],
        rejection_reasons=[
            "The 2.4 m texture footprint repeats visibly across every module and reads as masonry wallpaper.",
            "Small hard panels form a regular grid instead of a hierarchy of irregular fracture domains.",
            "Open closure slivers remain visible along the crest and the overall silhouette is still a planar sheet.",
            "Rock037 is a generic dark fractured-rock analog and does not establish Batoka basalt lithology.",
        ],
        next_iteration_requirements=[
            "Project the texture continuously at a much larger footprint with deterministic rotation and offset.",
            "Increase macro-fracture scale and depth variation while removing visible crest closures.",
            "Retain the rights and authority boundary and repeat all sixteen views.",
        ],
    )


def build_zambezi_batoka_basalt_v7_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=7,
        report_relative_path=V7_REPORT_RELATIVE_PATH,
        status="v7_macro_scale_improved_hard_panel_mosaic_rejected_v8_shared_surface_required",
        accepted_findings=[
            "Continuous 12 m texture projection removes the V6 per-cell wallpaper cadence.",
            "Larger irregular domains and stronger depth breaks improve the coarse scarp hierarchy.",
            "Removing closure geometry eliminates the V6 crest slivers.",
        ],
        rejection_reasons=[
            "Hard normals on every coarse quad create obvious polygon bands and rectangular rock tiles.",
            "Deep panel shadows dominate closeups and conceal the intended joint hierarchy.",
            "The exposed module perimeter and talus still read as generated review geometry rather than a natural outcrop.",
        ],
        next_iteration_requirements=[
            "Use shared surface vertices and coherent cliff normals while retaining geometric macro relief.",
            "Increase sampling density and let the PBR normal map carry near-field fracture detail.",
            "Repeat the isolated gate before any corridor use.",
        ],
    )


def build_zambezi_batoka_basalt_v8_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=8,
        report_relative_path=V8_REPORT_RELATIVE_PATH,
        status="v8_shared_surface_readable_rock037_macro_pattern_rejected_v9_nonrepeating_surface_required",
        accepted_findings=[
            "Shared-vertex cliff normals remove the V7 rectangular lighting mosaic.",
            "The denser connected heightfield preserves bounded joints, flow setbacks, gullies, and one-sided visibility.",
            "Rock037 remains useful as a close-range detail analog under explicit CC0 provenance.",
        ],
        rejection_reasons=[
            "Rock037's directional grain repeats at module scale and does not supply unique 20-50 m rock structure.",
            "The central face is readable, but the isolated silhouette still exposes a thin procedural sheet.",
            "Talus shape and grounding are not ready for production placement.",
        ],
        next_iteration_requirements=[
            "Acquire a rights-reviewed nonrepeating natural rock surface at full cliff-module scale.",
            "Keep the shared connected morphology and compare closeup plus 60 m readability.",
            "Do not claim exact Batoka lithology without geologist and reach-specific evidence.",
        ],
    )


def build_zambezi_batoka_basalt_v9_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=9,
        report_relative_path=V9_REPORT_RELATIVE_PATH,
        status="v9_nonrepeating_macro_surface_passes_distance_rejected_close_detail_v10_two_scale_required",
        accepted_findings=[
            "The CC0 Poly Haven Aerial Rocks 02 maps provide a unique publisher-scaled 50 m natural rock pattern.",
            "The central cliff face reads as continuous natural rock at the 60 m review distance without obvious repetition.",
            "The source and import manifests explicitly preserve the aerial-orientation and non-Batoka geology limits.",
        ],
        rejection_reasons=[
            "The publisher density of 0.8 px/cm is visibly soft in the fixed closeup camera.",
            "The aerial source includes vegetation and large forms that remain generic analogs rather than verified Batoka basalt.",
            "The isolated perimeter and talus remain review-only artifacts.",
        ],
        next_iteration_requirements=[
            "Blend restrained hash-reviewed near-field detail without destroying the unique 50 m macro pattern.",
            "Preserve the macro, detail, color, normal, and roughness weights in the report.",
            "Repeat all sixteen views before allowing a transient corridor comparison.",
        ],
    )


def build_zambezi_batoka_basalt_v10_visual_review(repo_root: Path) -> dict:
    return _build_followup_visual_review(
        repo_root,
        version=10,
        report_relative_path=V10_REPORT_RELATIVE_PATH,
        status="v10_two_scale_surface_conditionally_accepted_for_transient_corridor_comparison_only",
        accepted_findings=[
            "The unique 50 m macro surface retains natural large-form variation at river distance.",
            "A bounded 16 percent Rock037 color blend plus 42 percent detail-normal and 28 percent detail-roughness weights restore close-camera breakup without returning to V6 wallpaper.",
            "The connected shared-normal face remains readable in every exact camera and all assets, pixels, and reports retain explicit CC0 provenance.",
            "The family is sufficient for a transient non-colliding corridor comparison with its exposed perimeter hidden by source terrain.",
        ],
        rejection_reasons=[
            "V10 is not production accepted: neither source is a reach-specific Batoka capture or exact lithology authority.",
            "Aerial-source vegetation and baked macro appearance require geologist, guide, and art review in corridor context.",
            "The exposed rectangular perimeter and talus remain unacceptable as visible standalone production geometry.",
            "No surveyed collision, hydrodynamic obstacle, water, forcing, raft-contact, or gameplay authority is granted.",
        ],
        next_iteration_requirements=[
            "Run a paired transient guide-seat and river-eye corridor comparison against the untouched baseline.",
            "Hide module perimeters within visual terrain and reject any pasted-fragment silhouette or hazard occlusion.",
            "Keep production promotion blocked pending geology, guide, geospatial, rights, art, repetition, performance, and surveyed gameplay-collision review.",
        ],
    )


def _build_corridor_visual_review(
    repo_root: Path,
    *,
    version: int,
    report_relative_path: Path,
    status: str,
    decision: str,
    accepted_findings: list[str],
    rejection_reasons: list[str],
    next_iteration_requirements: list[str],
) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / report_relative_path
    report = json.loads(report_path.read_text(encoding="utf-8"))
    evidence = {}
    for view_name in ("guide_seat", "river_eye"):
        baseline_relative = Path(report["captures"][f"baseline_{view_name}"])
        comparison_relative = Path(report["captures"][f"comparison_{view_name}"])
        baseline_path = repo_root / baseline_relative
        comparison_path = repo_root / comparison_relative
        with Image.open(baseline_path) as image:
            baseline = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(comparison_path) as image:
            comparison = np.asarray(image.convert("RGB"), dtype=np.int16)
        if baseline.shape != comparison.shape:
            raise ValueError(
                f"Corridor comparison shape mismatch for {view_name}: "
                f"{baseline.shape} != {comparison.shape}"
            )
        delta = np.abs(comparison - baseline)
        evidence[view_name] = {
            "baseline_capture": str(baseline_relative),
            "baseline_sha256": _sha256(baseline_path),
            "comparison_capture": str(comparison_relative),
            "comparison_sha256": _sha256(comparison_path),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 2, axis=2))),
            "mean_absolute_channel_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    return {
        "schema": (
            "raftsim.unreal.zambezi_batoka_basalt_corridor_visual_review."
            f"v{version}"
        ),
        "generated_on": GENERATED_ON,
        "status": status,
        "decision": decision,
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_map_modified": False,
        "source_report": str(report_relative_path),
        "source_report_sha256": _sha256(report_path),
        "accepted_findings": accepted_findings,
        "rejection_reasons": rejection_reasons,
        "reviewed_evidence": evidence,
        "next_iteration_requirements": next_iteration_requirements,
        "authority": report["authority_boundary"],
    }


def build_zambezi_batoka_basalt_c1_corridor_visual_review(repo_root: Path) -> dict:
    return _build_corridor_visual_review(
        repo_root,
        version=1,
        report_relative_path=C1_CORRIDOR_REPORT_RELATIVE_PATH,
        status="v10_c1_transient_corridor_comparison_rejected_small_pasted_panels",
        decision="retain_v10_isolated_surface_reject_c1_corridor_placement",
        accepted_findings=[
            "The dedicated command captures immutable paired guide-seat and river-eye evidence without saving the source map.",
            "Eight actors per view are transient, non-colliding, and use the validated V10 Nanite modules.",
            "The result confirms that isolated central-face quality alone cannot justify corridor placement.",
        ],
        rejection_reasons=[
            "Modules scaled to 0.72-1.02x are much smaller than the corridor scarps and read as pasted rectangular panels.",
            "Front planes hover away from the sampled slope, producing visible gaps and detached shadows.",
            "The panels neither replace nor integrate with the smooth orange source-terrain approximation.",
            "Foliage, water, terrain resolution, and canyon morphology remain far below lifelike quality.",
        ],
        next_iteration_requirements=[
            "Test gorge-scale visual placement while retaining transient and collision-off boundaries.",
            "Align the actual front plane to the sampled slope and bury the basal perimeter.",
            "Reject further module placement if side seams remain visible; move to terrain-integrated authoring instead.",
        ],
    )


def build_zambezi_batoka_basalt_c2_corridor_visual_review(repo_root: Path) -> dict:
    return _build_corridor_visual_review(
        repo_root,
        version=2,
        report_relative_path=C2_CORRIDOR_REPORT_RELATIVE_PATH,
        status="v10_c2_gorge_scale_corridor_comparison_rejected_terrain_integration_required",
        decision="retain_v10_surface_reference_stop_placing_sheet_modules_author_terrain_integrated_cliffs",
        accepted_findings=[
            "Scaling to 2.8-4.4x gives the modules a plausible 84-132 m gorge-scarp envelope.",
            "Front-plane alignment and a 10 m buried base remove the detached miniature-panel failure from C1.",
            "The V10 two-scale surface remains readable under the physical-corridor light rig.",
        ],
        rejection_reasons=[
            "Vertical side seams and overlapping sheets remain obvious in both gameplay cameras.",
            "Scaled talus produces oversized detached forms and long black shadows on the source slope.",
            "Modules sit on top of rather than reshape or materially integrate with the low-resolution corridor terrain.",
            "The smooth orange source canyon, broken sparse foliage, and flat water prevent a lifelike result regardless of module surface quality.",
        ],
        next_iteration_requirements=[
            "Stop adding standalone cliff sheets to the corridor.",
            "Author the accepted V10 macro/detail response into a terrain-integrated visual material and continuous cliff morphology layer.",
            "Condition or replace the 30 m DSM corridor with reviewed higher-resolution terrain before final gorge silhouette approval.",
            "Rebuild gorge woodland, water, mist, lighting, and hazard-readable river surfaces before any photoreal claim.",
        ],
    )


def build_zambezi_batoka_v11_terrain_integrated_visual_review(
    repo_root: Path,
) -> dict:
    return _build_corridor_visual_review(
        repo_root,
        version=3,
        report_relative_path=C3_TERRAIN_REPORT_RELATIVE_PATH,
        status="v11_continuous_terrain_material_rejected_world_projection_and_geometry_required",
        decision="retain_continuous_visual_terrain_path_reject_top_down_uv_and_coarse_dsm_result",
        accepted_findings=[
            "The V11 command replaces standalone sheets with one continuous material response across all four dense visual-terrain tiles.",
            "Both exact gameplay cameras confirm that the transient override changes only the render mesh while preserving the saved map, Landscape height and collision, water, and gameplay authority.",
            "The 50 m macro and 2.4 m detail sources remain rights-reviewed, parameter-exposed, and visually bounded to the steep-slope mask.",
        ],
        rejection_reasons=[
            "Top-down corridor UVs stretch the macro and detail maps into long vertical streaks on steep banks.",
            "Repeated directional streaks read as texture projection rather than irregular jointed basalt.",
            "The 30 m DSM and 12.5 m visual mesh remain rounded and cannot express stacked scarps, ledges, flow breaks, gullies, or blocky talus.",
            "Smooth orange terrain, sparse broken foliage, flat water, and empty atmosphere remain far below a lifelike Batoka Gorge result.",
        ],
        next_iteration_requirements=[
            "Replace top-down steep-slope sampling with tri-planar or world-aligned macro, detail, normal, roughness, and AO projection.",
            "Acquire or derive reviewed higher-resolution Batoka terrain and condition it into continuous scarps, ledges, gullies, and talus before silhouette approval.",
            "Keep the dense visual mesh render-only and retain the Landscape, collision, water solver, raft contact, and gameplay authority boundary.",
            "Rebuild woodland, water, mist, lighting, and hazard-readable surfaces only after the terrain morphology passes exact-camera review.",
        ],
    )


def build_zambezi_batoka_v12_world_aligned_visual_review(
    repo_root: Path,
) -> dict:
    return _build_corridor_visual_review(
        repo_root,
        version=4,
        report_relative_path=C4_WORLD_ALIGNED_REPORT_RELATIVE_PATH,
        status="v12_world_alignment_retained_as_projection_basis_terrain_and_scene_rejected",
        decision="retain_world_aligned_material_graph_stop_surface_retuning_until_terrain_morphology_improves",
        accepted_findings=[
            "World-aligned projection keeps the 50 m macro and 2.4 m detail footprints consistent across differently oriented banks and removes the worst V11 top-down stretching.",
            "Color, normal, roughness, and AO channels use Unreal world-aligned functions, with the review material explicitly configured for world-space normal output.",
            "The response remains continuous across all four transient visual-terrain tiles with no standalone sheets, map save, collision change, or gameplay-authority change.",
        ],
        rejection_reasons=[
            "The 30 m DSM and 12.5 m visual sampling still produce rounded canyon masses rather than stacked scarps, ledges, flow breaks, joints, gullies, and blocky talus.",
            "The generic source remains brown and directional in places and is not exact Batoka lithology or named-outcrop evidence.",
            "Sparse broken foliage, flat dark water, empty atmosphere, and simple lighting keep both gameplay views far below lifelike quality.",
            "Additional surface-weight tuning cannot repair the missing terrain silhouette and would risk hiding the actual source-resolution blocker.",
        ],
        next_iteration_requirements=[
            "Retain V12 world-aligned projection as a technical material basis without promoting its appearance.",
            "Acquire, derive, or condition reviewed higher-resolution Batoka terrain before further surface tuning or final gorge-silhouette review.",
            "Author continuous visual scarps, ledges, joints, gullies, and talus while preserving source Landscape collision and all hydrodynamic authority.",
            "Resume material, woodland, water, mist, lighting, and hazard-readability review against the improved morphology in the exact cameras.",
        ],
    )


def build_zambezi_batoka_v13_visual_morphology_review(
    repo_root: Path,
) -> dict:
    return _build_corridor_visual_review(
        repo_root,
        version=5,
        report_relative_path=C5_VISUAL_MORPHOLOGY_REPORT_RELATIVE_PATH,
        status="v13_bounded_visual_morphology_rejected_insufficient_source_resolution",
        decision="retain_v12_projection_reject_small_procedural_offsets_require_higher_resolution_terrain",
        accepted_findings=[
            "The transient command preserves the V12 material and applies deterministic authored morphology only to the four collision-free dense render tiles.",
            "A 220 m fully protected river corridor fading to 650 m keeps the visual experiment away from the authored channel, banks, solver, and raft-contact authority.",
            "The report accounts for all 1,631,500 vertices per comparison, including 76,403 river-protected and 1,471,404 low-slope-rejected vertices.",
            "The bounded pass modifies 69,987 vertices with a 29.35 cm mean absolute offset and measured -3.94 m to +2.93 m extrema under a 4.5 m cap.",
        ],
        rejection_reasons=[
            "The paired exact-camera images show no meaningful gorge-silhouette improvement: 5.22 and 7.84 percent of pixels change, but mean absolute channel deltas are only 0.19 and 0.25 levels.",
            "Only 4.29 percent of visual vertices move, while the 30 m DSM continues to define rounded canyon masses without stacked scarps, ledges, gullies, or talus fields.",
            "Increasing procedural offsets enough to replace the missing silhouette would invent unsupported wall and bank geometry rather than recover source detail.",
            "Foliage, water, atmosphere, lighting, and exact Batoka lithology remain separate unresolved scene blockers.",
        ],
        next_iteration_requirements=[
            "Do not increase procedural displacement as a substitute for missing survey or photogrammetry.",
            "Acquire rights-cleared 0.3 m LiDAR, drone photogrammetry, commercial stereo terrain, or another reviewed higher-resolution terrain product with full reach coverage and datum metadata.",
            "Retain V12 world-aligned projection and the source/collision/hydrodynamic authority boundary while the terrain acquisition gate remains open.",
            "Resume continuous morphology and scene dressing only after a higher-resolution terrain candidate passes geospatial and rights review.",
        ],
    )


def _write_followup_visual_review(
    repo_root: Path,
    relative_path: Path,
    review: dict,
) -> Path:
    output_path = repo_root.resolve() / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_zambezi_batoka_basalt_v2_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V2_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v2_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v3_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V3_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v3_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v4_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V4_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v4_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v5_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V5_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v5_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v6_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V6_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v6_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v7_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V7_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v7_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v8_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V8_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v8_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v9_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V9_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v9_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_v10_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        V10_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_v10_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_c1_corridor_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        C1_CORRIDOR_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_c1_corridor_visual_review(repo_root),
    )


def write_zambezi_batoka_basalt_c2_corridor_visual_review(repo_root: Path) -> Path:
    return _write_followup_visual_review(
        repo_root,
        C2_CORRIDOR_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_basalt_c2_corridor_visual_review(repo_root),
    )


def write_zambezi_batoka_v11_terrain_integrated_visual_review(
    repo_root: Path,
) -> Path:
    return _write_followup_visual_review(
        repo_root,
        C3_TERRAIN_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_v11_terrain_integrated_visual_review(repo_root),
    )


def write_zambezi_batoka_v12_world_aligned_visual_review(
    repo_root: Path,
) -> Path:
    return _write_followup_visual_review(
        repo_root,
        C4_WORLD_ALIGNED_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_v12_world_aligned_visual_review(repo_root),
    )


def write_zambezi_batoka_v13_visual_morphology_review(
    repo_root: Path,
) -> Path:
    return _write_followup_visual_review(
        repo_root,
        C5_VISUAL_MORPHOLOGY_REVIEW_RELATIVE_PATH,
        build_zambezi_batoka_v13_visual_morphology_review(repo_root),
    )
