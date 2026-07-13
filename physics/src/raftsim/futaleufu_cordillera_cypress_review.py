"""Build deterministic visual-gate evidence for the Futaleufu cypress family."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v1_isolated_family_report.json"
)
REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v1_visual_review.json"
)
V2_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v2_isolated_family_report.json"
)
V2_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v2_visual_review.json"
)
V3_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v3_isolated_family_report.json"
)
V3_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v3_visual_review.json"
)
V4_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v4_isolated_family_report.json"
)
V4_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v4_visual_review.json"
)
V5_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v5_isolated_family_report.json"
)
V5_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v5_visual_review.json"
)
V6_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v6_isolated_family_report.json"
)
V6_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v6_visual_review.json"
)
V7_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v7_isolated_family_report.json"
)
V7_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v7_visual_review.json"
)
V8_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v8_isolated_family_report.json"
)
V8_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v8_visual_review.json"
)
V9_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v9_isolated_family_report.json"
)
V9_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v9_visual_review.json"
)
V9_TEXTURE_MANIFEST_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
    "CordilleraCypress/futaleufu_cordillera_cypress_v9_texture_manifest.json"
)
V10_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v10_isolated_family_report.json"
)
V10_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v10_visual_review.json"
)
V10_TEXTURE_MANIFEST_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
    "CordilleraCypress/futaleufu_cordillera_cypress_v10_texture_manifest.json"
)
V11_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v11_isolated_family_report.json"
)
V11_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v11_visual_review.json"
)
V12_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v12_isolated_family_report.json"
)
V12_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v12_visual_review.json"
)
V13_REPORT_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v13_morphology_donor_report.json"
)
V13_REVIEW_RELATIVE_PATH = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v13_morphology_donor_visual_review.json"
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
    green_dominant = (
        (green >= 35.0)
        & (green >= red * 1.08)
        & (green >= blue * 1.05)
        & ((green - np.minimum(red, blue)) >= 7.0)
    )
    dark = np.max(rgb, axis=2) < 55.0
    return {
        "sha256": _sha256(path),
        "width": width,
        "height": height,
        "green_dominant_pixel_count": int(np.count_nonzero(green_dominant)),
        "green_dominant_fraction": float(np.mean(green_dominant)),
        "dark_pixel_fraction": float(np.mean(dark)),
        "mean_rgb": [float(value) for value in np.mean(rgb, axis=(0, 1))],
    }


def _foreground_silhouette_fraction(path: Path) -> float:
    """Segment the fixed neutral review background without depending on foliage hue."""
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    sky = (blue > green + 8) & (green > red + 12) & (red > 55)
    channel_range = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    ground = (
        (red > 170)
        & (green > 170)
        & (blue > 170)
        & (channel_range < 35)
    )
    return float(np.mean(~(sky | ground)))


def build_futaleufu_cordillera_cypress_v1_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    captures = []
    green_fractions_by_view: dict[str, list[float]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
        "river_distance_150m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        green_fractions_by_view[view_group].append(metrics["green_dominant_fraction"])
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    view_summaries = {}
    for view_group, values in green_fractions_by_view.items():
        view_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": sum(values) / len(values),
            "maximum_green_dominant_fraction": max(values),
        }

    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v1",
        "generated_on": GENERATED_ON,
        "status": "v1_structurally_valid_visual_gate_rejected_no_corridor_substitution",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "review_scope": {
            "species": report["species"],
            "form_count": report["form_count"],
            "adult_form_count": report["adult_form_count"],
            "intermediate_form_count": report["intermediate_form_count"],
            "capture_count": len(captures),
            "views_per_form": 5,
            "rhi": "offscreen Metal",
            "initial_spray_shadows_enabled": False,
        },
        "accepted_findings": [
            "All five adult and three intermediate forms are independently seeded and dimensioned within the 2.5-25 m authoring envelope.",
            "The project-owned bark and scale-leaf spray textures import, compile, remain alpha-bearing, and bind to saved Unreal materials and meshes.",
            "The rerunnable command saves sixteen static meshes, one isolated review map, forty captures, and a portable structural report without corridor placement.",
        ],
        "rejection_reasons": [
            "Turntable silhouettes read as bare poles with evenly spaced exposed branches rather than compact evergreen crowns.",
            "Foliage remains only as small green traces at 60 m and 150 m, so the family is not distance-stable.",
            "Closeups expose crossed flat spray cards, hard intersections, and thin disconnected foliage instead of layered feathery branch masses.",
            "Primary and secondary wood uses smooth cylindrical joints and repeated tier cadence that remains visibly procedural.",
            "No temporal wind, reduced LOD, masked-overdraw, mixed-ecology, true-north placement, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": view_summaries,
            "decision_thresholds_for_v2": {
                "turntable_mean_green_dominant_fraction_minimum": 0.015,
                "river_distance_60m_mean_green_dominant_fraction_minimum": 0.008,
                "river_distance_150m_mean_green_dominant_fraction_minimum": 0.003,
                "note": "These are regression floors for visible evergreen crown mass, not photoreal acceptance by themselves.",
            },
        },
        "captures": captures,
        "decision": "retain_the_reproducible_pipeline_and_asset_family_structure_reject_v1_visuals",
        "next_iteration_requirements": [
            "Generate substantially denser, wider, source-matched feathery spray silhouettes with alpha-safe padding and no copied reference pixels.",
            "Distribute layered spray clusters continuously along primary and secondary wood so 60 m and 150 m crowns remain compact and green.",
            "Blend branch junctions and break the regular exposed-tier cadence while preserving five adult and three intermediate identities.",
            "Repeat all forty fixed-camera captures and require the V2 green-coverage regression floors before human visual review.",
            "Keep production, corridor placement, and shadow promotion closed until closeup, temporal, LOD, ecology, and performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v1_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v1_visual_review(repo_root)
    output_path = repo_root.resolve() / REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v2_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V2_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v1_review = json.loads((repo_root / REVIEW_RELATIVE_PATH).read_text(encoding="utf-8"))
    captures = []
    green_fractions_by_view: dict[str, list[float]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
        "river_distance_150m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        green_fractions_by_view[view_group].append(metrics["green_dominant_fraction"])
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    v1_summaries = v1_review["quantitative_review"]["view_summaries"]
    view_summaries = {}
    for view_group, values in green_fractions_by_view.items():
        mean = sum(values) / len(values)
        v1_mean = v1_summaries[view_group]["mean_green_dominant_fraction"]
        view_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v1_mean_green_dominant_fraction": v1_mean,
            "mean_increase_factor_from_v1": mean / v1_mean,
            "v2_regression_floor": thresholds.get(view_group),
            "v2_regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v2",
        "generated_on": GENERATED_ON,
        "status": "v2_distance_visibility_improved_closeup_and_turntable_gate_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V2_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v1_review": str(REVIEW_RELATIVE_PATH),
        "v1_review_sha256": _sha256(repo_root / REVIEW_RELATIVE_PATH),
        "review_scope": {
            "species": report["species"],
            "form_count": report["form_count"],
            "adult_form_count": report["adult_form_count"],
            "intermediate_form_count": report["intermediate_form_count"],
            "capture_count": len(captures),
            "views_per_form": 5,
            "rhi": "offscreen Metal",
            "initial_spray_shadows_enabled": False,
        },
        "accepted_findings": [
            "The denser V2 atlas and layered cards raise mean green-dominant coverage by 15.49x in turntables, 10.74x at 60 m, and 14.86x at 150 m relative to V1.",
            "The 60 m and 150 m visibility floors pass across the fixed eight-form capture set.",
            "Overlapping branch collars reduce the most abrupt V1 primary-junction cylinders while preserving all five adult and three intermediate identities.",
        ],
        "rejection_reasons": [
            "Mean turntable green-dominant coverage is 1.26 percent, below the 1.5 percent V2 regression floor.",
            "Closeups expose broad opaque brush-like spray slabs, crossed planes, and hard alpha silhouettes rather than feathery scale-leaf branchlets.",
            "Adult crowns remain vertically sparse with exposed regular branch tiers, especially through the lower and middle crown.",
            "Woody collars still read as intersecting procedural cylinders rather than continuous natural ramification.",
            "No temporal wind, production LOD, masked-overdraw, mixed-ecology, true-north placement, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": view_summaries,
            "regression_floor_result": {
                "turntable": False,
                "river_distance_60m": True,
                "river_distance_150m": True,
                "all_required_floors_passed": False,
                "visual_acceptance_implied_by_floor_pass": False,
            },
        },
        "captures": captures,
        "decision": "retain_v2_distance_density_and_reject_the_spray_shape_and_crown_topology",
        "next_iteration_requirements": [
            "Replace single dense fan tiles with smaller irregular feathery sub-sprays and explicit tertiary attachment directions so closeups do not show broad slabs.",
            "Build layered crown volumes from offset side shoots rather than crossed coplanar cards at the same branch positions.",
            "Add lower- and mid-crown interior ramification while breaking the exposed tier rhythm and retaining form-specific gaps and damage.",
            "Repeat all forty fixed-camera views and clear every visibility floor, then apply human closeup and silhouette review independently.",
            "Keep production, corridor placement, and shadow promotion closed until closeup, temporal, LOD, ecology, and performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v2_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v2_visual_review(repo_root)
    output_path = repo_root.resolve() / V2_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v3_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V3_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v2_review_path = repo_root / V2_REVIEW_RELATIVE_PATH
    v2_review = json.loads(v2_review_path.read_text(encoding="utf-8"))
    captures = []
    green_fractions_by_view: dict[str, list[float]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
        "river_distance_150m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        green_fractions_by_view[view_group].append(metrics["green_dominant_fraction"])
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    v2_summaries = v2_review["quantitative_review"]["view_summaries"]
    view_summaries = {}
    for view_group, values in green_fractions_by_view.items():
        mean = sum(values) / len(values)
        v2_mean = v2_summaries[view_group]["mean_green_dominant_fraction"]
        view_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v2_mean_green_dominant_fraction": v2_mean,
            "mean_fraction_of_v2": mean / v2_mean,
            "v2_regression_floor": thresholds.get(view_group),
            "v2_regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v3",
        "generated_on": GENERATED_ON,
        "status": "v3_explicit_ramification_valid_visual_gate_rejected_no_corridor_substitution",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V3_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v2_review": str(V2_REVIEW_RELATIVE_PATH),
        "v2_review_sha256": _sha256(v2_review_path),
        "review_scope": {
            "species": report["species"],
            "form_count": report["form_count"],
            "adult_form_count": report["adult_form_count"],
            "intermediate_form_count": report["intermediate_form_count"],
            "capture_count": len(captures),
            "views_per_form": 5,
            "rhi": "offscreen Metal",
            "initial_spray_shadows_enabled": False,
        },
        "accepted_findings": [
            "All eight forms build and save with explicit primary, secondary, tertiary, and interior woody shoots plus 950-1,808 individually placed V3 sub-sprays.",
            "The smaller irregular atlas removes the broad opaque brush-fan slabs that dominated V2 closeups.",
            "All forty fixed-camera captures complete without Unreal material, shader, asset, map, or fatal errors; the 60 m and 150 m visibility floors remain above their minimums.",
        ],
        "rejection_reasons": [
            "Mean turntable green-dominant coverage falls to 0.71 percent, less than half the 1.5 percent regression floor.",
            "The narrower sub-sprays reduce mean green coverage to 56.19 percent of V2 in turntables, 61.99 percent at 60 m, and 56.97 percent at 150 m; adult crowns again read as sparse exposed branch tiers.",
            "Closeups expose fern-like planar strips with hard silhouettes and repeated face orientation instead of compact volumetric scale-leaf sprays.",
            "Tertiary and interior shoots are explicit but remain long, smooth, intersecting cylinders with weak taper and insufficient foliage mass at their tips.",
            "No temporal wind, production LOD, masked-overdraw, mixed-ecology, true-north placement, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": view_summaries,
            "regression_floor_result": {
                "turntable": False,
                "river_distance_60m": True,
                "river_distance_150m": True,
                "all_required_floors_passed": False,
                "visual_acceptance_implied_by_floor_pass": False,
            },
        },
        "captures": captures,
        "decision": "retain_explicit_ramification_and_reject_sparse_planar_v3_sprays",
        "next_iteration_requirements": [
            "Build short dense scale-leaf spray clusters as several offset sub-sprays around each tapered terminal shoot, with orientation and size variation that creates crown volume without restoring V2 fan slabs.",
            "Increase terminal density and interior crown overlap selectively until every fixed view clears the existing visibility floors while preserving form-specific gaps, storm damage, and suppressed growth.",
            "Replace long smooth tertiary cylinders with shorter tapered branchlets, irregular junction radii, bark-normal variation, and foliage that begins near each attachment rather than only at distant tips.",
            "Repeat all forty fixed-camera views, hash-lock the result, and apply closeup and silhouette review independently of green-coverage metrics.",
            "Keep production, corridor placement, and shadow promotion closed until closeup, temporal, LOD, ecology, and performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v3_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v3_visual_review(repo_root)
    output_path = repo_root.resolve() / V3_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v4_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V4_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v3_review_path = repo_root / V3_REVIEW_RELATIVE_PATH
    v3_review = json.loads(v3_review_path.read_text(encoding="utf-8"))
    captures = []
    green_fractions_by_view: dict[str, list[float]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
        "river_distance_150m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        green_fractions_by_view[view_group].append(metrics["green_dominant_fraction"])
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                **metrics,
            }
        )

    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    v3_summaries = v3_review["quantitative_review"]["view_summaries"]
    view_summaries = {}
    for view_group, values in green_fractions_by_view.items():
        mean = sum(values) / len(values)
        v3_mean = v3_summaries[view_group]["mean_green_dominant_fraction"]
        v2_mean = v3_summaries[view_group]["v2_mean_green_dominant_fraction"]
        view_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v3_mean_green_dominant_fraction": v3_mean,
            "mean_increase_factor_from_v3": mean / v3_mean,
            "v2_mean_green_dominant_fraction": v2_mean,
            "mean_fraction_of_v2": mean / v2_mean,
            "v2_regression_floor": thresholds.get(view_group),
            "v2_regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    card_counts = [form["spray_source_cards"] for form in report["forms"]]
    woody_vertex_counts = [form["woody_source_vertices"] for form in report["forms"]]
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v4",
        "generated_on": GENERATED_ON,
        "status": "v4_distance_mass_recovered_topology_closeup_gate_rejected_no_corridor_substitution",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V4_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v3_review": str(V3_REVIEW_RELATIVE_PATH),
        "v3_review_sha256": _sha256(v3_review_path),
        "review_scope": {
            "species": report["species"],
            "form_count": report["form_count"],
            "adult_form_count": report["adult_form_count"],
            "intermediate_form_count": report["intermediate_form_count"],
            "capture_count": len(captures),
            "views_per_form": 5,
            "rhi": "offscreen Metal",
            "initial_spray_shadows_enabled": False,
            "minimum_spray_cards_per_form": min(card_counts),
            "maximum_spray_cards_per_form": max(card_counts),
            "minimum_woody_source_vertices_per_form": min(woody_vertex_counts),
            "maximum_woody_source_vertices_per_form": max(woody_vertex_counts),
        },
        "accepted_findings": [
            "Five short tapered terminal shoots with two rolled sub-sprays each replace every V3 single terminal card and preserve all eight form identities.",
            "Mean green-dominant coverage improves 1.53x in turntables, 1.40x at 60 m, and 1.66x at 150 m relative to V3; both distance floors remain clear.",
            "All forty fixed-camera captures complete without Unreal material, shader, asset, map, ensure, or fatal errors, and no corridor substitution occurs.",
        ],
        "rejection_reasons": [
            "Mean turntable green-dominant coverage reaches only 1.09 percent, still below the 1.5 percent regression floor and only 86.17 percent of V2.",
            "Full-tree views remain an evenly tiered sequence of exposed horizontal branches with isolated dark tufts rather than a continuous irregular evergreen crown.",
            "Closeups are overdraw-heavy near-black tangles of repeated planar spray silhouettes, with thin terminal shoots crossing through foliage rather than reading as natural scale-leaf ramification.",
            "The gain requires 12,380-23,600 spray cards and 58,260-110,928 authored woody vertices per tree before any production LOD or masked-overdraw validation.",
            "No temporal wind, production LOD, mixed-ecology, true-north placement, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": view_summaries,
            "regression_floor_result": {
                "turntable": False,
                "river_distance_60m": True,
                "river_distance_150m": True,
                "all_required_floors_passed": False,
                "visual_acceptance_implied_by_floor_pass": False,
            },
        },
        "captures": captures,
        "decision": "retain_v4_volumetric_density_lesson_reject_tiered_topology_and_planar_overdraw",
        "next_iteration_requirements": [
            "Replace repeated primary-branch tiers with source-matched irregular crown envelopes, clustered axial branch groups, and continuous interior foliage mass while preserving each growth-form silhouette.",
            "Create a separate near representation from connected geometric scale-leaf spraylets or another non-card-wall method, with a reduced registered mid/far representation rather than 12,000-24,000 identical masked cards at every distance.",
            "Remove needle-thin intersecting terminal wood, shorten visible junctions, and validate bark and spray response under closeup lighting before another whole-family render.",
            "Repeat all forty fixed-camera views and clear every visibility floor, then apply independent closeup, silhouette, masked-overdraw, and resource-budget gates.",
            "Keep production, corridor placement, and shadow promotion closed until temporal, LOD, ecology, and performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v4_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v4_visual_review(repo_root)
    output_path = repo_root.resolve() / V4_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v5_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V5_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v4_review_path = repo_root / V4_REVIEW_RELATIVE_PATH
    v4_review = json.loads(v4_review_path.read_text(encoding="utf-8"))
    groups: dict[str, list[float]] = {
        "turntable": [],
        "closeup": [],
        "river_distance_60m": [],
        "river_distance_150m": [],
    }
    captures = []
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        view_group = (
            "turntable" if "turntable" in capture_id
            else "closeup" if "closeup" in capture_id
            else "river_distance_60m" if "river_distance_60m" in capture_id
            else "river_distance_150m"
        )
        groups[view_group].append(metrics["green_dominant_fraction"])
        captures.append(
            {"capture_id": capture_id, "path": str(relative_path),
             "view_group": view_group, **metrics}
        )

    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    v4_summaries = v4_review["quantitative_review"]["view_summaries"]
    summaries = {}
    for view_group, values in groups.items():
        mean = sum(values) / len(values)
        v4_mean = v4_summaries[view_group]["mean_green_dominant_fraction"]
        v2_mean = v4_summaries[view_group]["v2_mean_green_dominant_fraction"]
        summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v4_mean_green_dominant_fraction": v4_mean,
            "mean_increase_factor_from_v4": mean / v4_mean,
            "v2_mean_green_dominant_fraction": v2_mean,
            "mean_fraction_of_v2": mean / v2_mean,
            "v2_regression_floor": thresholds.get(view_group),
            "v2_regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    far_cards = [form["far_spray_source_cards"] for form in report["forms"]]
    near_vertices = [
        form["near_geometric_spray_source_vertices"] for form in report["forms"]
    ]
    v4_scope = v4_review["review_scope"]
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v5",
        "generated_on": GENERATED_ON,
        "status": "v5_far_split_improved_near_geometric_spikes_rejected_no_corridor_substitution",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V5_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v4_review": str(V4_REVIEW_RELATIVE_PATH),
        "v4_review_sha256": _sha256(v4_review_path),
        "review_scope": {
            "species": report["species"],
            "form_count": report["form_count"],
            "capture_count": len(captures),
            "views_per_form": 5,
            "rhi": "offscreen Metal",
            "near_max_draw_distance_cm": report["near_max_draw_distance_cm"],
            "far_min_draw_distance_cm": report["far_min_draw_distance_cm"],
            "minimum_far_cards_per_form": min(far_cards),
            "maximum_far_cards_per_form": max(far_cards),
            "minimum_near_vertices_per_form": min(near_vertices),
            "maximum_near_vertices_per_form": max(near_vertices),
            "far_card_fraction_of_v4": (
                max(far_cards) / v4_scope["maximum_spray_cards_per_form"]
            ),
        },
        "accepted_findings": [
            "The 28 m split independently renders connected opaque near geometry in closeups and registered masked silhouettes in turntable, 60 m, and 150 m views.",
            "Far cards fall by 68.25 percent to 3,930-7,494 per form while turntable and 150 m green coverage improve 1.20x and 1.33x over V4.",
            "All forty captures complete without Unreal material, shader, asset, map, ensure, or fatal errors, and no corridor substitution occurs.",
        ],
        "rejection_reasons": [
            "Mean turntable green-dominant coverage reaches 1.31 percent and still misses the 1.5 percent regression floor.",
            "Closeups replace flat alpha planes with large faceted green spikes whose blunt bases, pointed tips, intersections, and flat color do not resemble millimeter-scale cypress foliage.",
            "The wider axial jitter and inner foliage improve mass but full trees still expose repeated horizontal tiers and an underfilled lower trunk.",
            "The near representation costs 65,500-124,900 vertices per form without curved spray topology, texture detail, wind, transition-band evidence, or measured runtime benefit.",
            "No mixed-ecology, true-north corridor, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": summaries,
            "regression_floor_result": {
                "turntable": False,
                "river_distance_60m": True,
                "river_distance_150m": True,
                "all_required_floors_passed": False,
                "visual_acceptance_implied_by_floor_pass": False,
            },
        },
        "captures": captures,
        "decision": "retain_registered_far_split_reject_opaque_spike_near_geometry_and_tiered_crown",
        "next_iteration_requirements": [
            "Replace tapered solid spikes with connected curved geometric spray ribbons or authored branch meshes carrying bounded texture and normal detail without broad alpha walls.",
            "Retain the lighter registered far silhouette, but add 20 m, 28 m, and 36 m handoff captures and temporal motion checks before accepting the split.",
            "Rebuild lower and middle crown topology from irregular axial branch groups and interior fans so trunk exposure and horizontal tier repetition no longer dominate.",
            "Repeat all forty views and clear visibility, closeup, silhouette, transition, overdraw, and resource gates independently.",
            "Keep production, corridor placement, and shadow promotion closed until ecology and platform performance gates also pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v5_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v5_visual_review(repo_root)
    output_path = repo_root.resolve() / V5_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v6_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V6_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v5_path = repo_root / V5_REVIEW_RELATIVE_PATH
    v5 = json.loads(v5_path.read_text(encoding="utf-8"))
    groups = {name: [] for name in (
        "turntable", "closeup", "river_distance_60m", "river_distance_150m",
        "handoff_20m", "handoff_28m", "handoff_36m")}
    captures = []
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "handoff" in capture_id:
            token = next(token for token in ("20m", "28m", "36m") if token in capture_id)
            view_group = f"handoff_{token}"
        elif "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        groups[view_group].append(metrics["green_dominant_fraction"])
        captures.append({"capture_id": capture_id, "path": str(relative_path),
                         "view_group": view_group, **metrics})

    thresholds = {"turntable": 0.015, "river_distance_60m": 0.008,
                  "river_distance_150m": 0.003}
    v5_summaries = v5["quantitative_review"]["view_summaries"]
    summaries = {}
    for view_group, values in groups.items():
        mean = sum(values) / len(values)
        summary = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
        }
        if view_group in v5_summaries:
            v5_mean = v5_summaries[view_group]["mean_green_dominant_fraction"]
            summary["v5_mean_green_dominant_fraction"] = v5_mean
            summary["mean_increase_factor_from_v5"] = mean / v5_mean
        if view_group in thresholds:
            summary["regression_floor"] = thresholds[view_group]
            summary["regression_floor_passed"] = mean >= thresholds[view_group]
        summaries[view_group] = summary

    near_vertices = [form["near_geometric_spray_source_vertices"] for form in report["forms"]]
    near_triangles = [form["near_geometric_spray_source_triangles"] for form in report["forms"]]
    far_cards = [form["far_spray_source_cards"] for form in report["forms"]]
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v6",
        "generated_on": GENERATED_ON,
        "status": "v6_visibility_floors_pass_ribbon_closeup_and_handoff_authority_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V6_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v5_review": str(V5_REVIEW_RELATIVE_PATH),
        "v5_review_sha256": _sha256(v5_path),
        "review_scope": {
            "species": report["species"], "form_count": report["form_count"],
            "fixed_family_capture_count": report["fixed_family_capture_count"],
            "handoff_capture_count": report["handoff_capture_count"],
            "capture_count": len(captures), "rhi": "offscreen Metal",
            "minimum_near_vertices_per_form": min(near_vertices),
            "maximum_near_vertices_per_form": max(near_vertices),
            "minimum_near_triangles_per_form": min(near_triangles),
            "maximum_near_triangles_per_form": max(near_triangles),
            "minimum_far_cards_per_form": min(far_cards),
            "maximum_far_cards_per_form": max(far_cards),
        },
        "accepted_findings": [
            "Connected curved main-and-side ribbons replace V5 pointed solids and all forty fixed plus nine handoff captures complete cleanly.",
            "Mean turntable, 60 m, and 150 m coverage rise 1.39x, 1.64x, and 1.27x over V5 and clear every visibility regression floor for the first time.",
            "The 20 m, 28 m, and 36 m views retain registered foliage mass across two adults and one intermediate, while the far card budget remains unchanged at 3,930-7,494 per form.",
        ],
        "rejection_reasons": [
            "Extreme closeups expose broad rectangular ribbon faces, hard cut ends, flat green material, and dense intersections rather than scale-leaf sprays.",
            "Near assets cost 235,800-449,640 vertices and 366,800-699,440 triangles per tree before wind, collision, or platform profiling.",
            "The unchanged far meshes produce substantially different fixed-distance coverage from V5, so bounds-based culling may overlap representations; the handoff captures do not prove near-only, far-only, and combined authority independently.",
            "Full-tree topology still exposes repeated horizontal primary tiers and an underfilled lower crown despite improved interior mass.",
            "No temporal transition, mixed ecology, true-north corridor, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": summaries,
            "regression_floor_result": {
                "turntable": True, "river_distance_60m": True,
                "river_distance_150m": True, "all_required_floors_passed": True,
                "visual_acceptance_implied_by_floor_pass": False,
            },
        },
        "captures": captures,
        "decision": "retain_curved_ribbon_and_far_budget_lessons_reject_closeup_cost_and_unproven_handoff_authority",
        "next_iteration_requirements": [
            "Capture explicit near-only, far-only, and combined modes at 20 m, 28 m, and 36 m by hiding components rather than relying on bounds-based culling.",
            "Replace broad ribbons with a compact authored frond mesh or narrower branched scale-spray geometry carrying project-owned albedo and normal detail.",
            "Reduce near triangles by at least 75 percent and remove hard cut ends and dense self-intersections before another closeup gate.",
            "Rebuild lower/middle primary topology and repeat all fixed, authority-split handoff, temporal, overdraw, and resource checks.",
            "Keep production and corridor placement closed until ecology and platform performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v6_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v6_visual_review(repo_root)
    output_path = repo_root.resolve() / V6_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v7_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V7_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v6_path = repo_root / V6_REVIEW_RELATIVE_PATH
    v6 = json.loads(v6_path.read_text(encoding="utf-8"))
    fixed_groups = {name: [] for name in (
        "turntable", "closeup", "river_distance_60m", "river_distance_150m")}
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "handoff" in capture_id:
            view_group = "handoff"
        elif "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        if view_group != "handoff":
            fixed_groups[view_group].append(metrics["green_dominant_fraction"])
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "view_group": view_group,
            "authority_mode": capture["authority_mode"],
            **metrics,
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    v6_summaries = v6["quantitative_review"]["view_summaries"]
    thresholds = {"turntable": 0.015, "river_distance_60m": 0.008,
                  "river_distance_150m": 0.003}
    fixed_summaries = {}
    for view_group, values in fixed_groups.items():
        mean = sum(values) / len(values)
        fixed_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v6_mean_green_dominant_fraction":
                v6_summaries[view_group]["mean_green_dominant_fraction"],
            "regression_floor": thresholds.get(view_group),
            "regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    authority_triplets = []
    combined_matches_far_count = 0
    combined_matches_near_count = 0
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            combined_vs_near = image_delta(
                repo_root / combined["path"], repo_root / near["path"])
            combined_vs_far = image_delta(
                repo_root / combined["path"], repo_root / far["path"])
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            authority_triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_only_capture": near["capture_id"],
                "far_only_capture": far["capture_id"],
                "combined_capture": combined["capture_id"],
                "near_vs_far": image_delta(repo_root / near["path"], repo_root / far["path"]),
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    near_triangles = [form["near_geometric_spray_source_triangles"] for form in report["forms"]]
    near_vertices = [form["near_geometric_spray_source_vertices"] for form in report["forms"]]
    v6_max_triangles = v6["review_scope"]["maximum_near_triangles_per_form"]
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v7",
        "generated_on": GENERATED_ON,
        "status": "v7_resource_target_pass_authority_overlap_and_closeup_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V7_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v6_review": str(V6_REVIEW_RELATIVE_PATH),
        "v6_review_sha256": _sha256(v6_path),
        "review_scope": {
            "form_count": report["form_count"],
            "fixed_capture_count": report["fixed_family_capture_count"],
            "authority_handoff_capture_count": report["handoff_capture_count"],
            "capture_count": len(captures),
            "rhi": "offscreen Metal",
            "minimum_near_vertices_per_form": min(near_vertices),
            "maximum_near_vertices_per_form": max(near_vertices),
            "minimum_near_triangles_per_form": min(near_triangles),
            "maximum_near_triangles_per_form": max(near_triangles),
            "maximum_near_triangle_fraction_of_v6": max(near_triangles) / v6_max_triangles,
            "near_triangle_reduction_from_v6": 1.0 - max(near_triangles) / v6_max_triangles,
        },
        "accepted_findings": [
            "The compact one-main/two-side frond reduces near geometry by 77.14 percent to 83,840-159,872 triangles per form, clearing the V7 reduction target.",
            "All forty fixed views retain the V6 visibility-floor pass, and all 27 authority captures complete with explicit near-only, far-only, and combined labels.",
            "Near-only and far-only images are materially distinct at every tested distance, proving the capture harness controls representation authority independently.",
        ],
        "rejection_reasons": [
            "Combined mode matches far-only in only one of nine triplets and never matches near-only; eight triplets render a measurable mixture, proving bounds-based culling overlaps representations.",
            "Near-only views are sparse, dark, jagged strips while extreme closeups still expose flat rectangular fronds, hard ends, intersections, and untextured green material.",
            "Far-only supplies the usable crown mass at all tested distances, so the current near asset adds cost and artifacts instead of a fidelity benefit.",
            "Full-tree crowns retain repeated horizontal primary tiers and underfilled lower/middle interiors.",
            "No actor-root distance selector, dithered transition, temporal motion, mixed ecology, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "view_summaries": fixed_summaries,
            "regression_floor_result": {
                "turntable": True, "river_distance_60m": True,
                "river_distance_150m": True, "all_required_floors_passed": True,
                "visual_acceptance_implied_by_floor_pass": False,
            },
            "authority_result": {
                "triplet_count": len(authority_triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count":
                    len(authority_triplets) - combined_matches_near_count - combined_matches_far_count,
                "bounds_based_authority_passed": False,
                "triplets": authority_triplets,
            },
        },
        "captures": captures,
        "decision": "retain_far_silhouette_and_compact_resource_budget_reject_near_frond_and_bounds_culling",
        "next_iteration_requirements": [
            "Replace bounds culling with actor-root distance authority so combined mode is byte-identical to the selected near or far representation outside a deliberate transition band.",
            "Keep far-only as the current silhouette baseline and replace near fronds with a genuinely higher-fidelity textured branch-spray asset before re-enabling them.",
            "Add a narrow deterministic dither or crossfade only after hard near/far selection is proven without overlap.",
            "Rebuild lower/middle crown topology and rerun fixed, authority, temporal, overdraw, and resource checks.",
            "Keep production and corridor placement closed until ecology and platform performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v7_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v7_visual_review(repo_root)
    output_path = repo_root.resolve() / V7_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v8_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V8_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v7_path = repo_root / V7_REVIEW_RELATIVE_PATH
    v7 = json.loads(v7_path.read_text(encoding="utf-8"))
    fixed_groups = {name: [] for name in (
        "turntable", "closeup", "river_distance_60m", "river_distance_150m")}
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "handoff" in capture_id:
            view_group = "handoff"
        elif "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        if view_group != "handoff":
            fixed_groups[view_group].append(metrics["green_dominant_fraction"])
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "view_group": view_group,
            "authority_mode": capture["authority_mode"],
            **metrics,
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    v7_summaries = v7["quantitative_review"]["view_summaries"]
    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    fixed_summaries = {}
    for view_group, values in fixed_groups.items():
        mean = sum(values) / len(values)
        fixed_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v7_mean_green_dominant_fraction":
                v7_summaries[view_group]["mean_green_dominant_fraction"],
            "regression_floor": thresholds.get(view_group),
            "regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    authority_triplets = []
    combined_matches_far_count = 0
    combined_matches_near_count = 0
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            combined_vs_near = image_delta(
                repo_root / combined["path"], repo_root / near["path"])
            combined_vs_far = image_delta(
                repo_root / combined["path"], repo_root / far["path"])
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            authority_triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_only_capture": near["capture_id"],
                "far_only_capture": far["capture_id"],
                "combined_capture": combined["capture_id"],
                "near_vs_far": image_delta(repo_root / near["path"], repo_root / far["path"]),
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    near_triangles = [form["near_geometric_spray_source_triangles"] for form in report["forms"]]
    near_vertices = [form["near_geometric_spray_source_vertices"] for form in report["forms"]]
    combined_differs_from_both_count = (
        len(authority_triplets)
        - combined_matches_near_count
        - combined_matches_far_count
    )
    authority_passed = (
        combined_matches_far_count == len(authority_triplets)
        and combined_matches_near_count == 0
        and combined_differs_from_both_count == 0
        and report["combined_authority"] == "camera_to_actor_root_distance"
        and report["near_representation_eligible"] is False
    )
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v8",
        "generated_on": GENERATED_ON,
        "status": "v8_actor_root_authority_pass_far_fallback_retained_near_fidelity_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V8_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "v7_review": str(V7_REVIEW_RELATIVE_PATH),
        "v7_review_sha256": _sha256(v7_path),
        "review_scope": {
            "form_count": report["form_count"],
            "fixed_capture_count": report["fixed_family_capture_count"],
            "authority_handoff_capture_count": report["handoff_capture_count"],
            "capture_count": len(captures),
            "rhi": "offscreen Metal",
            "combined_authority": report["combined_authority"],
            "actor_root_selection_distance_cm": report["actor_root_selection_distance_cm"],
            "near_representation_eligible": report["near_representation_eligible"],
            "ineligible_near_fallback": report["ineligible_near_fallback"],
            "minimum_near_vertices_per_form": min(near_vertices),
            "maximum_near_vertices_per_form": max(near_vertices),
            "minimum_near_triangles_per_form": min(near_triangles),
            "maximum_near_triangles_per_form": max(near_triangles),
        },
        "accepted_findings": [
            "Actor-root distance authority eliminates the V7 bounds-culling overlap: all nine combined captures are byte-identical to far-only and none contain near/far mixtures.",
            "Near-only and far-only remain materially distinct in all nine triplets, so the capture harness still proves independent representation control.",
            "The V7 compact near resource budget and all forty fixed captures remain available as diagnostic evidence while the failed near asset stays ineligible.",
        ],
        "rejection_reasons": [
            "The near representation remains ineligible because its sparse rectangular ribbons, hard ends, intersections, and flat green material do not improve close fidelity.",
            "The authoritative far fallback uses masked card foliage at close range and therefore clears authority correctness, not the photoreal visual gate.",
            "Full-tree crowns retain repeated horizontal primary tiers and underfilled lower/middle interiors.",
            "No accepted near asset, deliberate transition band, temporal motion, mixed ecology, packaged desktop, or on-device VR evidence exists.",
        ],
        "quantitative_review": {
            "view_summaries": fixed_summaries,
            "regression_floor_result": {
                "turntable": fixed_summaries["turntable"]["regression_floor_passed"],
                "river_distance_60m": fixed_summaries["river_distance_60m"]["regression_floor_passed"],
                "river_distance_150m": fixed_summaries["river_distance_150m"]["regression_floor_passed"],
                "all_required_floors_passed": all(
                    fixed_summaries[name]["regression_floor_passed"]
                    for name in thresholds
                ),
                "visual_acceptance_implied_by_floor_pass": False,
            },
            "authority_result": {
                "triplet_count": len(authority_triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count": combined_differs_from_both_count,
                "actor_root_authority_passed": authority_passed,
                "triplets": authority_triplets,
            },
        },
        "captures": captures,
        "decision": "retain_actor_root_authority_and_far_fallback_keep_near_disabled_and_corridor_closed",
        "next_iteration_requirements": [
            "Author or acquire a genuinely high-fidelity textured cypress branch-spray asset and keep it ineligible until fixed closeup review passes.",
            "Re-enable hard near authority only after the replacement clearly exceeds the far fallback at close range, then prove all authority triplets again.",
            "Add a narrow deterministic dither or crossfade only after hard near/far selection passes without overlap.",
            "Rebuild lower/middle crown topology and rerun fixed, authority, temporal, overdraw, and resource checks.",
            "Keep production and corridor placement closed until ecology and platform performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v8_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v8_visual_review(repo_root)
    output_path = repo_root.resolve() / V8_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v9_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V9_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v8_path = repo_root / V8_REVIEW_RELATIVE_PATH
    v8 = json.loads(v8_path.read_text(encoding="utf-8"))
    texture_manifest_path = repo_root / V9_TEXTURE_MANIFEST_RELATIVE_PATH
    texture_manifest = json.loads(texture_manifest_path.read_text(encoding="utf-8"))
    fixed_groups = {name: [] for name in (
        "turntable", "closeup", "river_distance_60m", "river_distance_150m")}
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "handoff" in capture_id:
            view_group = "handoff"
        elif "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        if view_group != "handoff":
            fixed_groups[view_group].append(metrics["green_dominant_fraction"])
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "view_group": view_group,
            "authority_mode": capture["authority_mode"],
            **metrics,
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    v8_summaries = v8["quantitative_review"]["view_summaries"]
    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    fixed_summaries = {}
    for view_group, values in fixed_groups.items():
        mean = sum(values) / len(values)
        fixed_summaries[view_group] = {
            "sample_count": len(values),
            "authority_mode": "near_only" if view_group == "closeup" else "combined_far_fallback",
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "v8_mean_green_dominant_fraction":
                v8_summaries[view_group]["mean_green_dominant_fraction"],
            "regression_floor": thresholds.get(view_group),
            "regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    authority_triplets = []
    combined_matches_far_count = 0
    combined_matches_near_count = 0
    near_to_far_green_fraction = []
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            combined_vs_near = image_delta(
                repo_root / combined["path"], repo_root / near["path"])
            combined_vs_far = image_delta(
                repo_root / combined["path"], repo_root / far["path"])
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            coverage_ratio = near["green_dominant_fraction"] / max(
                far["green_dominant_fraction"], 1.0e-9)
            near_to_far_green_fraction.append(coverage_ratio)
            authority_triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_only_capture": near["capture_id"],
                "far_only_capture": far["capture_id"],
                "combined_capture": combined["capture_id"],
                "near_to_far_green_dominant_fraction": coverage_ratio,
                "near_vs_far": image_delta(repo_root / near["path"], repo_root / far["path"]),
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    near_triangles = [form["near_textured_spray_source_triangles"] for form in report["forms"]]
    near_cards = [form["near_textured_spray_source_cards"] for form in report["forms"]]
    v8_max_triangles = v8["review_scope"]["maximum_near_triangles_per_form"]
    combined_differs_from_both_count = (
        len(authority_triplets)
        - combined_matches_near_count
        - combined_matches_far_count
    )
    authority_passed = (
        combined_matches_far_count == len(authority_triplets)
        and combined_matches_near_count == 0
        and combined_differs_from_both_count == 0
        and report["combined_authority"] == "camera_to_actor_root_distance"
        and report["near_representation_eligible"] is False
    )
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v9",
        "generated_on": GENERATED_ON,
        "status": "v9_texture_detail_improved_near_topology_and_overdraw_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V9_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "source_texture_manifest": str(V9_TEXTURE_MANIFEST_RELATIVE_PATH),
        "source_texture_manifest_sha256": _sha256(texture_manifest_path),
        "v8_review": str(V8_REVIEW_RELATIVE_PATH),
        "v8_review_sha256": _sha256(v8_path),
        "review_scope": {
            "form_count": report["form_count"],
            "fixed_capture_count": report["fixed_family_capture_count"],
            "authority_handoff_capture_count": report["handoff_capture_count"],
            "capture_count": len(captures),
            "rhi": "offscreen Metal",
            "combined_authority": report["combined_authority"],
            "near_representation_eligible": report["near_representation_eligible"],
            "minimum_near_cards_per_form": min(near_cards),
            "maximum_near_cards_per_form": max(near_cards),
            "minimum_near_triangles_per_form": min(near_triangles),
            "maximum_near_triangles_per_form": max(near_triangles),
            "near_triangle_reduction_from_v8": 1.0 - max(near_triangles) / v8_max_triangles,
            "texture_source_has_external_reference_images":
                texture_manifest["source_provenance"]["reference_images_supplied"],
        },
        "accepted_findings": [
            "The project-generated V9 source resolves individual scale leaves, twig color, and asymmetric terminal detail far beyond the V8 flat-color ribbons.",
            "Near geometry falls to 20,960-39,968 triangles per form, at least 74.99 percent below the V8 maximum, while all eight near-only closeups render.",
            "Actor-root fallback authority remains exact: all nine combined captures are byte-identical to far-only and contain no representation mixture.",
        ],
        "rejection_reasons": [
            "The narrower V9 atlas regresses the authoritative far fallback: mean turntable coverage falls from 1.82 to 0.39 percent and mean 60 m coverage falls from 2.94 to 0.75 percent, failing both retained floors.",
            "At 20-36 m the near cards often turn edge-on and read as sparse pointed spikes rather than continuous flattened cypress sprays; the far fallback remains visibly fuller.",
            "Closeups expose severe self-intersection, repeated radial card placement, long disconnected-looking twigs, and near-black overdraw pockets even though the source texture itself is improved.",
            "Each form uses 10,480-19,984 masked cards, creating an unvalidated and likely excessive masked-overdraw burden despite the low triangle count.",
            "The sixteen atlas tiles are bounded transformations of one generated source, so repeated branch identity remains visible and is insufficient for production variety.",
            "Full-tree crowns retain repeated horizontal primary tiers and underfilled lower/middle interiors.",
        ],
        "quantitative_review": {
            "view_summaries": fixed_summaries,
            "regression_floor_result": {
                "turntable": fixed_summaries["turntable"]["regression_floor_passed"],
                "river_distance_60m": fixed_summaries["river_distance_60m"]["regression_floor_passed"],
                "river_distance_150m": fixed_summaries["river_distance_150m"]["regression_floor_passed"],
                "all_required_floors_passed": all(
                    fixed_summaries[name]["regression_floor_passed"]
                    for name in thresholds
                ),
                "visual_acceptance_implied_by_floor_pass": False,
            },
            "near_to_far_green_dominant_fraction": {
                "minimum": min(near_to_far_green_fraction),
                "mean": sum(near_to_far_green_fraction) / len(near_to_far_green_fraction),
                "maximum": max(near_to_far_green_fraction),
            },
            "authority_result": {
                "triplet_count": len(authority_triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count": combined_differs_from_both_count,
                "actor_root_authority_passed": authority_passed,
                "triplets": authority_triplets,
            },
        },
        "captures": captures,
        "decision": "retain_v9_texture_detail_lesson_keep_near_disabled_and_rebuild_spray_shape_distribution",
        "next_iteration_requirements": [
            "Author several broader flattened branch-spray sources with much higher lateral alpha occupancy instead of transforming one narrow conical source.",
            "Cut near card count and radial overlap substantially, orient cards in source-matched flattened branch systems, and require the near silhouette to meet or exceed far coverage at 20 m.",
            "Rebuild lower/middle crown topology before reconsidering hard near authority.",
            "Repeat closeup, authority, temporal, overdraw, ecology, desktop, and VR gates; keep the corridor closed.",
        ],
    }


def write_futaleufu_cordillera_cypress_v9_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v9_visual_review(repo_root)
    output_path = repo_root.resolve() / V9_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v10_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V10_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v9_path = repo_root / V9_REVIEW_RELATIVE_PATH
    v9 = json.loads(v9_path.read_text(encoding="utf-8"))
    texture_manifest_path = repo_root / V10_TEXTURE_MANIFEST_RELATIVE_PATH
    texture_manifest = json.loads(texture_manifest_path.read_text(encoding="utf-8"))
    fixed_groups = {
        name: []
        for name in ("turntable", "closeup", "river_distance_60m", "river_distance_150m")
    }
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        metrics = _capture_metrics(repo_root / relative_path)
        capture_id = capture["capture_id"]
        if "handoff" in capture_id:
            view_group = "handoff"
        elif "turntable" in capture_id:
            view_group = "turntable"
        elif "closeup" in capture_id:
            view_group = "closeup"
        elif "river_distance_60m" in capture_id:
            view_group = "river_distance_60m"
        else:
            view_group = "river_distance_150m"
        if view_group != "handoff":
            fixed_groups[view_group].append(metrics["green_dominant_fraction"])
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "view_group": view_group,
            "authority_mode": capture["authority_mode"],
            **metrics,
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    thresholds = {
        "turntable": 0.015,
        "river_distance_60m": 0.008,
        "river_distance_150m": 0.003,
    }
    fixed_summaries = {}
    for view_group, values in fixed_groups.items():
        mean = sum(values) / len(values)
        fixed_summaries[view_group] = {
            "sample_count": len(values),
            "authority_mode": "near_only" if view_group == "closeup" else "combined_far_fallback",
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": mean,
            "maximum_green_dominant_fraction": max(values),
            "regression_floor": thresholds.get(view_group),
            "regression_floor_passed": (
                mean >= thresholds[view_group] if view_group in thresholds else None
            ),
        }

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    authority_triplets = []
    combined_matches_far_count = 0
    combined_matches_near_count = 0
    silhouette_ratios = []
    green_ratios = []
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            near_path = repo_root / near["path"]
            far_path = repo_root / far["path"]
            combined_path = repo_root / combined["path"]
            combined_vs_near = image_delta(combined_path, near_path)
            combined_vs_far = image_delta(combined_path, far_path)
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            near_silhouette = _foreground_silhouette_fraction(near_path)
            far_silhouette = _foreground_silhouette_fraction(far_path)
            silhouette_ratio = near_silhouette / max(far_silhouette, 1.0e-9)
            green_ratio = near["green_dominant_fraction"] / max(
                far["green_dominant_fraction"], 1.0e-9
            )
            silhouette_ratios.append(silhouette_ratio)
            green_ratios.append(green_ratio)
            authority_triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_only_capture": near["capture_id"],
                "far_only_capture": far["capture_id"],
                "combined_capture": combined["capture_id"],
                "near_foreground_silhouette_fraction": near_silhouette,
                "far_foreground_silhouette_fraction": far_silhouette,
                "near_to_far_foreground_silhouette_ratio": silhouette_ratio,
                "near_to_far_green_dominant_fraction": green_ratio,
                "near_vs_far": image_delta(near_path, far_path),
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    near_triangles = [form["near_textured_spray_source_triangles"] for form in report["forms"]]
    near_cards = [form["near_textured_spray_source_cards"] for form in report["forms"]]
    v9_max_cards = v9["review_scope"]["maximum_near_cards_per_form"]
    combined_differs_from_both_count = (
        len(authority_triplets) - combined_matches_near_count - combined_matches_far_count
    )
    authority_passed = (
        combined_matches_far_count == len(authority_triplets)
        and combined_matches_near_count == 0
        and combined_differs_from_both_count == 0
        and report["combined_authority"] == "camera_to_actor_root_distance"
        and report["near_representation_eligible"] is False
    )
    silhouette_passed = min(silhouette_ratios) >= 1.0
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v10",
        "generated_on": GENERATED_ON,
        "status": "v10_broad_spray_silhouette_and_resource_pass_closeup_topology_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V10_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "source_texture_manifest": str(V10_TEXTURE_MANIFEST_RELATIVE_PATH),
        "source_texture_manifest_sha256": _sha256(texture_manifest_path),
        "v9_review": str(V9_REVIEW_RELATIVE_PATH),
        "v9_review_sha256": _sha256(v9_path),
        "review_scope": {
            "form_count": report["form_count"],
            "fixed_capture_count": report["fixed_family_capture_count"],
            "authority_handoff_capture_count": report["handoff_capture_count"],
            "capture_count": len(captures),
            "rhi": "offscreen Metal",
            "combined_authority": report["combined_authority"],
            "near_representation_eligible": report["near_representation_eligible"],
            "minimum_near_cards_per_form": min(near_cards),
            "maximum_near_cards_per_form": max(near_cards),
            "minimum_near_triangles_per_form": min(near_triangles),
            "maximum_near_triangles_per_form": max(near_triangles),
            "near_card_reduction_from_v9_maximum": 1.0 - max(near_cards) / v9_max_cards,
            "independently_generated_source_count":
                texture_manifest["source_provenance"]["source_count"],
            "texture_source_has_external_reference_images":
                texture_manifest["source_provenance"]["reference_images_supplied"],
        },
        "accepted_findings": [
            "Three independently generated broad branch-spray sources replace V9's transformed single-source atlas, while near and retained V3 far textures remain separate.",
            "The hue-independent fixed-background silhouette proxy passes all nine handoff views: near occupies 1.033x-1.094x the far foreground at 20, 28, and 36 m.",
            "Near geometry falls to 3,957-7,545 masked cards and 7,914-15,090 triangles per form, a 62.25 percent maximum-card reduction from V9.",
            "Actor-root fallback authority remains exact: all nine combined captures are byte-identical to far-only and contain no representation mixture.",
        ],
        "rejection_reasons": [
            "Closeups still expose layered whole-spray cards, repeated source silhouettes, long disconnected-looking twigs, and dark overlap pockets rather than connected scale-leaf ramification.",
            "Full-tree crowns remain an evenly tiered sequence of horizontal primary shelves with coarse foliage blocks instead of irregular source-matched cypress branch systems.",
            "The silhouette proxy measures outer occupancy, not topology, botanical fidelity, opacity complexity, or masked overdraw; its pass cannot promote the near representation by itself.",
            "The project-generated source set was not derived from supplied botanical reference images and therefore cannot establish species fidelity without later rights-reviewed reference comparison.",
            "No temporal wind, measured masked-overdraw, mixed-ecology, corridor-density, packaged desktop, or on-device VR gate has passed.",
        ],
        "quantitative_review": {
            "foreground_silhouette_definition": (
                "all pixels outside the fixed blue-sky and neutral-ground chroma ranges; "
                "near/far ratios are valid because camera, woody mesh, lighting, and background are identical"
            ),
            "view_summaries": fixed_summaries,
            "near_to_far_foreground_silhouette": {
                "minimum": min(silhouette_ratios),
                "mean": sum(silhouette_ratios) / len(silhouette_ratios),
                "maximum": max(silhouette_ratios),
                "required_minimum": 1.0,
                "all_handoff_views_passed": silhouette_passed,
            },
            "near_to_far_green_dominant_fraction_diagnostic_only": {
                "minimum": min(green_ratios),
                "mean": sum(green_ratios) / len(green_ratios),
                "maximum": max(green_ratios),
                "acceptance_metric": False,
            },
            "authority_result": {
                "triplet_count": len(authority_triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count": combined_differs_from_both_count,
                "actor_root_authority_passed": authority_passed,
                "triplets": authority_triplets,
            },
        },
        "captures": captures,
        "decision": "retain_v10_sources_silhouette_and_resource_gain_keep_near_disabled_rebuild_topology",
        "next_iteration_requirements": [
            "Build V11 primary branches as irregular grouped, curved, and variably ascending systems rather than evenly spaced horizontal tiers.",
            "Align one or two broad cards to each authored branch system, remove radial overlap, and keep the V10 silhouette and card-budget floors as hard guardrails.",
            "Move closeup cameras to exposed outer terminal attachments so connected twig-to-spray structure remains inspectable without hiding whole-crown overlap in the fixed turntables.",
            "Repeat all 67 captures, authority checks, objective silhouette segmentation, hash locking, and human topology review before enabling near authority.",
            "Keep corridor placement closed until temporal, overdraw, ecology, desktop, and VR gates also pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v10_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v10_visual_review(repo_root)
    output_path = repo_root.resolve() / V10_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v11_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V11_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v10_path = repo_root / V10_REVIEW_RELATIVE_PATH
    v10 = json.loads(v10_path.read_text(encoding="utf-8"))
    texture_manifest_path = repo_root / V10_TEXTURE_MANIFEST_RELATIVE_PATH
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        capture_id = capture["capture_id"]
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "view_group": (
                "handoff" if "handoff" in capture_id
                else "turntable" if "turntable" in capture_id
                else "closeup" if "closeup" in capture_id
                else "river_distance_60m" if "river_distance_60m" in capture_id
                else "river_distance_150m"
            ),
            "authority_mode": capture["authority_mode"],
            **_capture_metrics(repo_root / relative_path),
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    triplets = []
    silhouette_ratios = []
    combined_matches_near_count = 0
    combined_matches_far_count = 0
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            near_path = repo_root / near["path"]
            far_path = repo_root / far["path"]
            combined_path = repo_root / combined["path"]
            combined_vs_near = image_delta(combined_path, near_path)
            combined_vs_far = image_delta(combined_path, far_path)
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            near_silhouette = _foreground_silhouette_fraction(near_path)
            far_silhouette = _foreground_silhouette_fraction(far_path)
            silhouette_ratio = near_silhouette / max(far_silhouette, 1.0e-9)
            silhouette_ratios.append(silhouette_ratio)
            triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_to_far_foreground_silhouette_ratio": silhouette_ratio,
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    cards = [form["near_textured_spray_source_cards"] for form in report["forms"]]
    triangles = [form["near_textured_spray_source_triangles"] for form in report["forms"]]
    combined_differs_from_both_count = (
        len(triplets) - combined_matches_near_count - combined_matches_far_count
    )
    authority_passed = (
        combined_matches_far_count == len(triplets)
        and combined_matches_near_count == 0
        and combined_differs_from_both_count == 0
        and report["near_representation_eligible"] is False
    )
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v11",
        "generated_on": GENERATED_ON,
        "status": "v11_card_budget_improved_silhouette_and_branch_system_regressed",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V11_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "source_texture_manifest": str(V10_TEXTURE_MANIFEST_RELATIVE_PATH),
        "source_texture_manifest_sha256": _sha256(texture_manifest_path),
        "v10_review": str(V10_REVIEW_RELATIVE_PATH),
        "v10_review_sha256": _sha256(v10_path),
        "review_scope": {
            "form_count": report["form_count"],
            "capture_count": len(captures),
            "minimum_near_cards_per_form": min(cards),
            "maximum_near_cards_per_form": max(cards),
            "minimum_near_triangles_per_form": min(triangles),
            "maximum_near_triangles_per_form": max(triangles),
            "maximum_card_reduction_from_v10": (
                1.0 - max(cards) / v10["review_scope"]["maximum_near_cards_per_form"]
            ),
            "near_representation_eligible": report["near_representation_eligible"],
        },
        "accepted_findings": [
            "Two branch-aligned near cards per terminal cluster reduce the family to 2,638-5,030 cards and 5,276-10,060 triangles per form.",
            "Bounded spray roll and an exterior closeup make planar overlap and attachment defects easier to see than the V10 interior-crown view.",
            "All 67 captures complete and all nine combined handoff views remain exact far-only fallbacks.",
        ],
        "rejection_reasons": [
            "The grouped primary layout opens the crown into more obvious horizontal shelves and exposed trunk instead of producing irregular connected cypress mass.",
            "The minimum near/far foreground-silhouette ratio falls to 0.964, regressing V10's hard 1.0 floor.",
            "Exterior closeups prove that complete branch-photo cards are still repeated at leaf-cluster density, producing large intersecting planes, disconnected pale twigs, and implausible scale.",
            "Changing the shared branch topology also changes the far fallback silhouette, so V12 must restore the retained V10 branch distribution before testing a sparser near representation.",
        ],
        "quantitative_review": {
            "near_to_far_foreground_silhouette": {
                "minimum": min(silhouette_ratios),
                "mean": sum(silhouette_ratios) / len(silhouette_ratios),
                "maximum": max(silhouette_ratios),
                "required_minimum": 1.0,
                "all_handoff_views_passed": min(silhouette_ratios) >= 1.0,
            },
            "authority_result": {
                "triplet_count": len(triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count": combined_differs_from_both_count,
                "actor_root_authority_passed": authority_passed,
                "triplets": triplets,
            },
        },
        "captures": captures,
        "decision": "reject_v11_restore_v10_branch_distribution_and_sample_near_at_branch_scale",
        "next_iteration_requirements": [
            "Restore V10's deterministic primary distribution so the retained far fallback is not silently changed by a near-only experiment.",
            "Treat each V10 source as a complete branch spray: place one enlarged near card for a sparse deterministic subset of terminal systems instead of one or two cards at every cluster.",
            "Keep bounded branch-relative roll, exterior closeups, exact actor-root authority, and the V10 silhouette floor.",
            "Repeat all 67 captures and reject any result that reopens the minimum silhouette, topology, or resource contracts.",
        ],
    }


def write_futaleufu_cordillera_cypress_v11_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v11_visual_review(repo_root)
    output_path = repo_root.resolve() / V11_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v12_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V12_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    v11_path = repo_root / V11_REVIEW_RELATIVE_PATH
    v11 = json.loads(v11_path.read_text(encoding="utf-8"))
    v10_path = repo_root / V10_REVIEW_RELATIVE_PATH
    v10 = json.loads(v10_path.read_text(encoding="utf-8"))
    captures = []
    capture_by_id = {}
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        capture_id = capture["capture_id"]
        entry = {
            "capture_id": capture_id,
            "path": str(relative_path),
            "authority_mode": capture["authority_mode"],
            **_capture_metrics(repo_root / relative_path),
        }
        captures.append(entry)
        capture_by_id[capture_id] = entry

    def image_delta(first: Path, second: Path) -> dict:
        with Image.open(first) as image:
            first_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        with Image.open(second) as image:
            second_rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        delta = np.abs(first_rgb - second_rgb)
        return {
            "byte_identical": bool(np.count_nonzero(delta) == 0),
            "changed_pixel_fraction": float(np.mean(np.any(delta > 0, axis=2))),
            "mean_absolute_rgb_delta": float(np.mean(delta)),
            "maximum_channel_delta": int(np.max(delta)),
        }

    triplets = []
    silhouette_ratios = []
    combined_matches_near_count = 0
    combined_matches_far_count = 0
    for form_id in ("open_grown_conical", "closed_grove_columnar", "grove_intermediate"):
        for distance in ("20m", "28m", "36m"):
            base = f"{form_id}_handoff_{distance}"
            near = capture_by_id[f"{base}_near_only"]
            far = capture_by_id[f"{base}_far_only"]
            combined = capture_by_id[f"{base}_combined"]
            near_path = repo_root / near["path"]
            far_path = repo_root / far["path"]
            combined_path = repo_root / combined["path"]
            combined_vs_near = image_delta(combined_path, near_path)
            combined_vs_far = image_delta(combined_path, far_path)
            combined_matches_near_count += int(combined_vs_near["byte_identical"])
            combined_matches_far_count += int(combined_vs_far["byte_identical"])
            near_silhouette = _foreground_silhouette_fraction(near_path)
            far_silhouette = _foreground_silhouette_fraction(far_path)
            silhouette_ratio = near_silhouette / max(far_silhouette, 1.0e-9)
            silhouette_ratios.append(silhouette_ratio)
            triplets.append({
                "form_id": form_id,
                "distance": distance,
                "near_to_far_foreground_silhouette_ratio": silhouette_ratio,
                "combined_vs_near": combined_vs_near,
                "combined_vs_far": combined_vs_far,
            })

    cards = [form["near_textured_spray_source_cards"] for form in report["forms"]]
    triangles = [form["near_textured_spray_source_triangles"] for form in report["forms"]]
    combined_differs_from_both_count = (
        len(triplets) - combined_matches_near_count - combined_matches_far_count
    )
    authority_passed = (
        combined_matches_far_count == len(triplets)
        and combined_matches_near_count == 0
        and combined_differs_from_both_count == 0
        and report["near_representation_eligible"] is False
    )
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_visual_review.v12",
        "generated_on": GENERATED_ON,
        "status": "v12_branch_scale_and_resource_improved_silhouette_floor_rejected",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "source_report": str(V12_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "source_texture_manifest": str(V10_TEXTURE_MANIFEST_RELATIVE_PATH),
        "source_texture_manifest_sha256": _sha256(
            repo_root / V10_TEXTURE_MANIFEST_RELATIVE_PATH
        ),
        "v11_review": str(V11_REVIEW_RELATIVE_PATH),
        "v11_review_sha256": _sha256(v11_path),
        "v10_review": str(V10_REVIEW_RELATIVE_PATH),
        "v10_review_sha256": _sha256(v10_path),
        "review_scope": {
            "form_count": report["form_count"],
            "capture_count": len(captures),
            "minimum_near_cards_per_form": min(cards),
            "maximum_near_cards_per_form": max(cards),
            "minimum_near_triangles_per_form": min(triangles),
            "maximum_near_triangles_per_form": max(triangles),
            "maximum_card_reduction_from_v10": (
                1.0 - max(cards) / v10["review_scope"]["maximum_near_cards_per_form"]
            ),
            "selected_terminal_system_sampling_probability":
                report["near_terminal_system_sampling_probability"],
            "near_representation_eligible": report["near_representation_eligible"],
        },
        "accepted_findings": [
            "Restoring V10's primary distribution removes the V11 grouped-whorl experiment from the retained far-generation path.",
            "Treating each generated source as a complete branch spray reduces near assets to 443-945 cards and 886-1,890 triangles per form, at least 87.47 percent below V10's maximum card count.",
            "Sparse enlarged sprays read at a more plausible branch scale than V10/V11 leaf-cluster stamping, and all nine combined captures remain exact far-only fallbacks.",
        ],
        "rejection_reasons": [
            "Near/far foreground silhouette reaches only 0.815-0.926, failing the retained 1.0 floor in every handoff view.",
            "Closeups still reveal stretched planar photographs, intersecting cards, and disconnected woody attachments; changing sampling density cannot make this representation photoreal at branch distance.",
            "Adding enough of the same planes to recover coverage would return toward V10's overlap problem rather than solve topology or botanical fidelity.",
            "No exact Austrocedrus chilensis production model was found in the initial Fab, SpeedTree, or general commercial-model search; close relatives require explicit morphology-donor review and cannot be labeled native assets without reconstruction and validation.",
        ],
        "quantitative_review": {
            "near_to_far_foreground_silhouette": {
                "minimum": min(silhouette_ratios),
                "mean": sum(silhouette_ratios) / len(silhouette_ratios),
                "maximum": max(silhouette_ratios),
                "required_minimum": 1.0,
                "all_handoff_views_passed": min(silhouette_ratios) >= 1.0,
            },
            "authority_result": {
                "triplet_count": len(triplets),
                "combined_matches_near_count": combined_matches_near_count,
                "combined_matches_far_count": combined_matches_far_count,
                "combined_differs_from_both_count": combined_differs_from_both_count,
                "actor_root_authority_passed": authority_passed,
                "triplets": triplets,
            },
        },
        "captures": captures,
        "decision": "retain_v10_far_and_v12_branch_scale_lesson_stop_density_retuning_a_failed_card_representation",
        "next_iteration_requirements": [
            "Review a rights-cleared high-fidelity Cupressaceae morphology donor, prioritizing Western red cedar flattened sprays, against the Austrocedrus source contract before purchase or import.",
            "If no donor passes, author opaque geometric branchlets and scale-leaf clusters for the near tier rather than another masked-card density iteration.",
            "Keep the V10 far fallback, actor-root authority, V10 silhouette floor, V12 resource ceiling, and exterior closeup as mandatory comparison evidence.",
            "Do not place or label a donor as native Austrocedrus until reconstructed crown, bark, scale-leaf, form-variation, rights, ecology, and performance gates pass.",
        ],
    }


def write_futaleufu_cordillera_cypress_v12_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v12_visual_review(repo_root)
    output_path = repo_root.resolve() / V12_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review


def build_futaleufu_cordillera_cypress_v13_visual_review(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    report_path = repo_root / V13_REPORT_RELATIVE_PATH
    report = json.loads(report_path.read_text(encoding="utf-8"))
    import_report_path = repo_root / report["import_report"]
    import_report = json.loads(import_report_path.read_text(encoding="utf-8"))
    v10_path = repo_root / V10_REVIEW_RELATIVE_PATH
    v12_path = repo_root / V12_REVIEW_RELATIVE_PATH

    captures = []
    view_values: dict[str, list[float]] = {
        "turntable": [],
        "branch_closeup": [],
        "river_distance_60m": [],
    }
    foreground_values: dict[str, list[float]] = {
        "turntable": [],
        "branch_closeup": [],
        "river_distance_60m": [],
    }
    for capture in report["captures"]:
        relative_path = Path(capture["path"])
        capture_id = capture["capture_id"]
        if "turntable" in capture_id:
            view_group = "turntable"
        elif "branch_closeup" in capture_id:
            view_group = "branch_closeup"
        else:
            view_group = "river_distance_60m"
        metrics = _capture_metrics(repo_root / relative_path)
        foreground_fraction = _foreground_silhouette_fraction(repo_root / relative_path)
        view_values[view_group].append(metrics["green_dominant_fraction"])
        foreground_values[view_group].append(foreground_fraction)
        captures.append(
            {
                "capture_id": capture_id,
                "path": str(relative_path),
                "view_group": view_group,
                "foreground_silhouette_fraction": foreground_fraction,
                **metrics,
            }
        )

    view_summaries = {}
    for view_group, values in view_values.items():
        foreground = foreground_values[view_group]
        view_summaries[view_group] = {
            "sample_count": len(values),
            "minimum_green_dominant_fraction": min(values),
            "mean_green_dominant_fraction": sum(values) / len(values),
            "maximum_green_dominant_fraction": max(values),
            "minimum_foreground_silhouette_fraction": min(foreground),
            "mean_foreground_silhouette_fraction": sum(foreground) / len(foreground),
            "maximum_foreground_silhouette_fraction": max(foreground),
        }

    source_triangles = [
        asset["source_triangle_count_lod0"] for asset in import_report["meshes"]
    ]
    fallback_triangles = [donor["render_triangles"] for donor in report["donors"]]
    effective_heights = [donor["bounds_size_cm"][2] for donor in report["donors"]]
    return {
        "schema": "raftsim.unreal.futaleufu_cordillera_cypress_morphology_donor_visual_review.v13",
        "generated_on": GENERATED_ON,
        "status": "v13_cc0_fir_direct_donor_rejected_opaque_geometric_reconstruction_required",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "native_species_claim": False,
        "source_report": str(V13_REPORT_RELATIVE_PATH),
        "source_report_sha256": _sha256(report_path),
        "source_manifest": report["source_manifest"],
        "source_manifest_sha256": _sha256(repo_root / report["source_manifest"]),
        "import_report": report["import_report"],
        "import_report_sha256": _sha256(import_report_path),
        "v10_review": str(V10_REVIEW_RELATIVE_PATH),
        "v10_review_sha256": _sha256(v10_path),
        "v12_review": str(V12_REVIEW_RELATIVE_PATH),
        "v12_review_sha256": _sha256(v12_path),
        "review_scope": {
            "donor_species_identity": report["source_species"],
            "donor_mesh_count": len(report["donors"]),
            "capture_count": len(captures),
            "views_per_mesh": 4,
            "rhi": "offscreen Metal",
            "license": report["license"],
            "minimum_effective_height_cm": min(effective_heights),
            "maximum_effective_height_cm": max(effective_heights),
            "total_source_triangles": sum(source_triangles),
            "total_nanite_fallback_triangles": sum(fallback_triangles),
            "review_actor_scale": 1.0,
            "review_culling_bounds_scale": report["review_culling_bounds_scale"],
        },
        "accepted_findings": [
            "The already rights-reviewed CC0 source supports a repeatable three-mesh, twelve-view isolated donor gate without purchase, new vendoring, corridor placement, or a native-species claim.",
            "All three meshes preserve original bark and needle material slots, Nanite remains enabled, and effective 14.1-18.9 m heights agree with the import report.",
            "Woody trunks and branches are connected, irregular, and materially more organic at close range than V10/V12 intersecting procedural cylinders and detached spray-card attachments.",
            "The gate exposes a legacy import defect: BuildScale3D 100 affects rendered geometry while persisted culling bounds stay pre-build-scale, requiring a review-only expanded bounds override at actor scale one.",
        ],
        "rejection_reasons": [
            "Every turntable and 60 m view reads as a bare or nearly bare snag; the original needle stratum collapses instead of producing an evergreen crown.",
            "The surviving woody hierarchy is sparse fir topology with long exposed limbs, not the flattened dense scale-leaf sprays and broad distance-stable Austrocedrus crown required by the source contract.",
            "The legacy build-scale/culling-bounds mismatch is unsuitable for direct runtime reuse and would need a separately validated reimport or reconstruction pipeline.",
            "Copying or relabeling this non-native geometry would not establish Austrocedrus morphology, form variation, ecology, seasonal response, wind, LOD, or desktop/VR performance.",
            "The link-only Western Red Cedar and generic cypress listings remain unpurchased and unevaluated in-engine; neither can close this gate without license review and the same non-native reconstruction boundary.",
        ],
        "quantitative_review": {
            "green_dominant_definition": "G>=35, G>=1.08R, G>=1.05B, and G-min(R,B)>=7",
            "view_summaries": view_summaries,
            "direct_donor_acceptance": {
                "all_twelve_captures_present": len(captures) == 12,
                "all_three_nanite_meshes_present": all(
                    donor["nanite_enabled"] for donor in report["donors"]
                ),
                "evergreen_crown_mass_present": False,
                "native_morphology_established": False,
                "runtime_bounds_contract_valid": False,
                "direct_geometry_donor_passed": False,
            },
        },
        "captures": captures,
        "decision": "reject_direct_fir_geometry_retain_connected_wood_lesson_and_author_project_owned_opaque_cypress_branchlets_plus_scale_leaf_clusters",
        "next_iteration_requirements": [
            "Build the next near-tier prototype from project-owned opaque geometric primary, secondary, and tertiary branchlets carrying bounded scale-leaf clusters; do not copy or relabel the fir geometry.",
            "Retain V10 far fallback authority, V10 silhouette floors, V12 branch-scale/resource ceiling, V13 exterior closeups, and exact-camera checks as guardrails.",
            "Require connected attachments, non-tiered broad crown mass, visible evergreen silhouette at turntable and 60 m, and no masked whole-spray cards before another corridor review.",
            "Keep the Fab Western Red Cedar and generic cypress options link-only unless a later license and maintenance decision explicitly authorizes acquisition for non-native morphology study.",
            "Repair and separately validate the legacy Poly Haven build-scale/culling-bounds import path before any of those assets are considered for runtime placement elsewhere.",
        ],
    }


def write_futaleufu_cordillera_cypress_v13_visual_review(repo_root: Path) -> dict:
    review = build_futaleufu_cordillera_cypress_v13_visual_review(repo_root)
    output_path = repo_root.resolve() / V13_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return review
