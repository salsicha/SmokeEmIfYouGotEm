"""Review generated river screenshots for photoreal environment blockers."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


CAPTURE_ROOT_RELATIVE_PATH = Path("docs/environment-captures/photoreal_river_previews")
CAPTURE_MANIFEST_RELATIVE_PATH = CAPTURE_ROOT_RELATIVE_PATH / "environment_capture_manifest.json"
CAPTURE_QUALITY_REVIEW_RELATIVE_PATH = CAPTURE_ROOT_RELATIVE_PATH / "photoreal_capture_quality_review.json"
HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH = (
    CAPTURE_ROOT_RELATIVE_PATH / "photoreal_human_lifelike_review_handoff.json"
)
HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH = (
    CAPTURE_ROOT_RELATIVE_PATH / "photoreal_human_lifelike_review_packet.md"
)
HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH = (
    CAPTURE_ROOT_RELATIVE_PATH / "photoreal_human_lifelike_review_results_template.json"
)
PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH = (
    CAPTURE_ROOT_RELATIVE_PATH / "photoreal_environment_performance_review.json"
)
RUNTIME_BUDGETS_RELATIVE_PATH = Path("physics/config/runtime_budgets.json")
PROXY_WATER_OVERLAY_RENDERER_COVERAGE_ID = "first_party_source_aware_tapered_water_chroma_microbreakup"
VISIBLE_WATER_CARD_RENDERER_COVERAGE_IDS = {
    "first_party_capture_quality_water_texture_fleck_cards",
}
FACETED_WATER_MESH_RENDERER_COVERAGE_ID = "flow_aware_water_mesh_undulation"
SMOOTHED_WATER_MESH_RENDERER_COVERAGE_ID = "first_party_smoothed_near_field_water_surface_faceting_demotion"
REFERENCE_MEDIA_REVIEW_QUEUE_RELATIVE_PATH = Path("physics/data/real_world/reference_media_review_queue.json")
PRODUCTION_ENVIRONMENT_GAP_REGISTER_RELATIVE_PATH = Path(
    "physics/data/real_world/production_environment_gap_register.json"
)
PHOTOREAL_RIVER_ENVIRONMENT_SOURCES_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
)


HUMAN_REVIEW_DOMAINS: tuple[dict[str, object], ...] = (
    {
        "domain_id": "art_direction_visual_lifelike",
        "required_reviewer": "environment_art_or_art_direction",
        "required_evidence": [
            "side_by_side_review_against_rights_reviewed_reference_links_or_first_party_field_media",
            "river_specific_notes_for_terrain_water_rocks_foliage_foam_mist_lighting_and_raft_foreground",
        ],
    },
    {
        "domain_id": "guide_hydraulic_fidelity",
        "required_reviewer": "river_guide_or_oarsman_domain_reviewer",
        "required_evidence": [
            "flow_band_specific_notes_for_line_choice_holes_laterals_boils_eddy_lines_wave_trains_and_wet_banks",
            "raft_outcome_sanity_notes_for_surf_flush_pin_release_flip_and_swimmer_visibility",
        ],
    },
    {
        "domain_id": "geospatial_source_alignment",
        "required_reviewer": "geospatial_or_technical_art_reviewer",
        "required_evidence": [
            "capture_overlays_or_notes_checking_river_centerline_banks_heightfield_masks_and_source_drape_alignment",
            "known_preview_derivative_limitations_and_required_production_import_replacements",
        ],
    },
    {
        "domain_id": "rights_and_reference_media",
        "required_reviewer": "rights_or_content_provenance_reviewer",
        "required_evidence": [
            "item_level_license_permission_attribution_and_allowed_use_for_any_photo_footage_or_social_reference",
            "confirmation_that_uncleared_media_remains_link_only_and_not_used_as_texture_training_or_packaged_asset_input",
        ],
    },
    {
        "domain_id": "hazard_and_rescue_readability",
        "required_reviewer": "gameplay_safety_or_rescue_readability_reviewer",
        "required_evidence": [
            "notes_that_water_foam_mist_foliage_and_lighting_do_not_hide_hazards_swimmers_throw_rope_zones_or_rescue_targets",
            "notes_that_visual_forcing_or_art_layers_do_not_hide_solver_or_conservation_failures",
        ],
    },
    {
        "domain_id": "production_material_asset_promotion",
        "required_reviewer": "technical_art_or_rendering_reviewer",
        "required_evidence": [
            "promotion_decision_for_review_only_texture2d_material_instance_and_procedural_proxy_surfaces",
            "replacement_or_approval_plan_for_landscape_water_rocks_foliage_foam_mist_lighting_and_raft_foreground_assets",
        ],
    },
    {
        "domain_id": "desktop_and_vr_performance",
        "required_reviewer": "performance_or_vr_reviewer",
        "required_evidence": [
            "desktop_capture_settings_frame_time_gpu_memory_and_scalability_notes",
            "vr_or_low_power_capture_settings_comfort_frame_time_and_visual_readability_notes",
        ],
    },
)


@dataclass(frozen=True)
class CaptureQualityThresholds:
    min_edge_density_for_lifelike_review: float = 0.045
    max_low_gradient_fraction_for_lifelike_review: float = 0.80
    min_quantized_entropy_bits_for_lifelike_review: float = 4.40
    max_flat_blue_field_fraction_for_lifelike_review: float = 0.62
    max_bottom_center_dark_fraction_for_lifelike_review: float = 0.08
    min_luma_std_for_lifelike_review: float = 32.0

    def as_dict(self) -> dict[str, float]:
        return {
            "min_edge_density_for_lifelike_review": self.min_edge_density_for_lifelike_review,
            "max_low_gradient_fraction_for_lifelike_review": self.max_low_gradient_fraction_for_lifelike_review,
            "min_quantized_entropy_bits_for_lifelike_review": self.min_quantized_entropy_bits_for_lifelike_review,
            "max_flat_blue_field_fraction_for_lifelike_review": self.max_flat_blue_field_fraction_for_lifelike_review,
            "max_bottom_center_dark_fraction_for_lifelike_review": self.max_bottom_center_dark_fraction_for_lifelike_review,
            "min_luma_std_for_lifelike_review": self.min_luma_std_for_lifelike_review,
        }


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample_filter() -> int:
    return getattr(getattr(Image, "Resampling", Image), "BILINEAR")


def _pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    raw = image.tobytes()
    return [(raw[index], raw[index + 1], raw[index + 2]) for index in range(0, len(raw), 3)]


def _luma(pixel: tuple[int, int, int]) -> float:
    red, green, blue = pixel
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _round(value: float, places: int = 4) -> float:
    return round(float(value), places)


def _entropy(counter: Counter[tuple[int, int, int]], sample_count: int) -> float:
    entropy = 0.0
    for count in counter.values():
        probability = count / sample_count
        entropy -= probability * math.log2(probability)
    return entropy


def _blockers(metrics: dict[str, float], thresholds: CaptureQualityThresholds) -> list[dict[str, str | float]]:
    blockers: list[dict[str, str | float]] = []
    if metrics["edge_density"] < thresholds.min_edge_density_for_lifelike_review:
        blockers.append(
            {
                "id": "low_edge_density",
                "metric": "edge_density",
                "value": metrics["edge_density"],
                "threshold": thresholds.min_edge_density_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Screenshots still read as broad smooth proxy fields instead of textured river corridor detail.",
            }
        )
    if metrics["low_gradient_fraction"] > thresholds.max_low_gradient_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "excess_low_gradient_area",
                "metric": "low_gradient_fraction",
                "value": metrics["low_gradient_fraction"],
                "threshold": thresholds.max_low_gradient_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Large low-gradient regions indicate flat water, sky, or terrain proxy surfaces that need production material and geometry detail.",
            }
        )
    if metrics["quantized_entropy_bits"] < thresholds.min_quantized_entropy_bits_for_lifelike_review:
        blockers.append(
            {
                "id": "low_color_texture_entropy",
                "metric": "quantized_entropy_bits",
                "value": metrics["quantized_entropy_bits"],
                "threshold": thresholds.min_quantized_entropy_bits_for_lifelike_review,
                "why_it_blocks_lifelike_review": "The rendered palette is still too compressed for a photoreal river environment.",
            }
        )
    if metrics["flat_blue_field_fraction"] > thresholds.max_flat_blue_field_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "large_flat_blue_field",
                "metric": "flat_blue_field_fraction",
                "value": metrics["flat_blue_field_fraction"],
                "threshold": thresholds.max_flat_blue_field_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Sky and water occupy too much of the frame as smooth blue preview material instead of source-shaped river, bank, and atmosphere detail.",
            }
        )
    if metrics["bottom_center_dark_fraction"] > thresholds.max_bottom_center_dark_fraction_for_lifelike_review:
        blockers.append(
            {
                "id": "dark_foreground_proxy",
                "metric": "bottom_center_dark_fraction",
                "value": metrics["bottom_center_dark_fraction"],
                "threshold": thresholds.max_bottom_center_dark_fraction_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Foreground raft/oar or river-eye cover proxies are still reading as dark placeholder shapes.",
            }
        )
    if metrics["luma_std"] < thresholds.min_luma_std_for_lifelike_review:
        blockers.append(
            {
                "id": "low_luma_variation",
                "metric": "luma_std",
                "value": metrics["luma_std"],
                "threshold": thresholds.min_luma_std_for_lifelike_review,
                "why_it_blocks_lifelike_review": "Lighting and material variation are not strong enough for a lifelike review frame.",
            }
        )
    return blockers


def _renderer_proxy_blockers(repo_root: Path, capture_manifest: dict) -> list[dict[str, str | float]]:
    procedural_asset_plan = capture_manifest.get("procedural_asset_plan")
    if not isinstance(procedural_asset_plan, str):
        return []

    asset_plan_path = repo_root / procedural_asset_plan
    if not asset_plan_path.exists():
        return []

    asset_plan = json.loads(asset_plan_path.read_text(encoding="utf-8"))
    unreal_integration = asset_plan.get("unreal_integration", {})
    renderer_coverage = set(unreal_integration.get("current_renderer_coverage", []))
    blockers: list[dict[str, str | float]] = []
    if PROXY_WATER_OVERLAY_RENDERER_COVERAGE_ID in renderer_coverage:
        blockers.append(
            {
                "id": "visible_proxy_water_overlay_geometry",
                "metric": "renderer_coverage",
                "value": PROXY_WATER_OVERLAY_RENDERER_COVERAGE_ID,
                "threshold": "production_water_material_or_human_approved_proxy_replacement",
                "why_it_blocks_lifelike_review": (
                    "Water color/texture entropy is still carried by visible first-party proxy overlay geometry, "
                    "so the frame can pass pixel statistics while still reading as non-photoreal preview art."
                ),
            }
        )

    active_water_card_coverage = sorted(VISIBLE_WATER_CARD_RENDERER_COVERAGE_IDS & renderer_coverage)
    if active_water_card_coverage:
        blockers.append(
            {
                "id": "visible_proxy_water_card_geometry",
                "metric": "renderer_coverage",
                "value": ",".join(active_water_card_coverage),
                "threshold": "integrated_water_material_or_approved_water_vfx_replacement",
                "why_it_blocks_lifelike_review": (
                    "Water detail is still carried by visible preview card geometry; it must be folded into the "
                    "water material, Niagara/equivalent VFX, or a human-approved replacement before lifelike review."
                ),
            }
        )

    if (
        FACETED_WATER_MESH_RENDERER_COVERAGE_ID in renderer_coverage
        and SMOOTHED_WATER_MESH_RENDERER_COVERAGE_ID not in renderer_coverage
    ):
        blockers.append(
            {
                "id": "faceted_proxy_water_surface_mesh",
                "metric": "renderer_coverage",
                "value": FACETED_WATER_MESH_RENDERER_COVERAGE_ID,
                "threshold": SMOOTHED_WATER_MESH_RENDERER_COVERAGE_ID,
                "why_it_blocks_lifelike_review": (
                    "The base river surface still depends on visibly faceted preview mesh undulation. "
                    "Near-field water must use smoothed displacement and material-scale flow cues before "
                    "the capture can be treated as a lifelike-review candidate."
                ),
            }
        )

    return blockers


def analyze_capture(
    repo_root: Path,
    capture_relative_path: str,
    river_id: str,
    view_id: str,
    thresholds: CaptureQualityThresholds | None = None,
) -> dict:
    thresholds = thresholds or CaptureQualityThresholds()
    capture_path = repo_root / capture_relative_path
    with Image.open(capture_path) as source_image:
        full_size = source_image.size
        image = source_image.convert("RGB").resize((320, 180), _resample_filter())

    width, height = image.size
    pixels = _pixels(image)
    luma_values = [_luma(pixel) for pixel in pixels]
    luma_mean = sum(luma_values) / len(luma_values)
    luma_std = math.sqrt(sum((value - luma_mean) ** 2 for value in luma_values) / len(luma_values))

    edge_count = 0
    low_gradient_count = 0
    gradient_sample_count = 0
    for y in range(height - 1):
        row = y * width
        next_row = (y + 1) * width
        for x in range(width - 1):
            index = row + x
            gradient = abs(luma_values[index + 1] - luma_values[index]) + abs(
                luma_values[next_row + x] - luma_values[index]
            )
            gradient_sample_count += 1
            if gradient > 18.0:
                edge_count += 1
            if gradient < 4.0:
                low_gradient_count += 1

    quantized = Counter((red // 32, green // 32, blue // 32) for red, green, blue in pixels)
    flat_blue_count = sum(
        1
        for red, green, blue in pixels
        if blue > 70 and blue > red + 18 and blue > green + 4
    )

    dark_bottom_center_count = 0
    bottom_center_sample_count = 0
    for y in range(int(height * 0.55), height):
        for x in range(int(width * 0.25), int(width * 0.75)):
            bottom_center_sample_count += 1
            if luma_values[y * width + x] < 38.0:
                dark_bottom_center_count += 1

    mean_rgb = [
        _round(sum(pixel[channel] for pixel in pixels) / len(pixels), 2)
        for channel in range(3)
    ]
    metrics = {
        "analysis_size": [width, height],
        "source_size": [full_size[0], full_size[1]],
        "rgb_mean": mean_rgb,
        "luma_mean": _round(luma_mean, 2),
        "luma_std": _round(luma_std, 2),
        "edge_density": _round(edge_count / gradient_sample_count),
        "low_gradient_fraction": _round(low_gradient_count / gradient_sample_count),
        "quantized_entropy_bits": _round(_entropy(quantized, len(pixels)), 2),
        "quantized_color_count": len(quantized),
        "flat_blue_field_fraction": _round(flat_blue_count / len(pixels)),
        "bottom_center_dark_fraction": _round(dark_bottom_center_count / bottom_center_sample_count),
    }
    blockers = _blockers(metrics, thresholds)
    return {
        "river_id": river_id,
        "view_id": view_id,
        "capture": capture_relative_path,
        "sha256": _hash_file(capture_path),
        "metrics": metrics,
        "blockers": blockers,
        "status": "preview_only_not_lifelike_quality_blockers" if blockers else "candidate_for_human_lifelike_review_not_approved",
    }


def _capture_entries(capture_manifest: dict) -> Iterable[tuple[str, str, str]]:
    for river in capture_manifest["captures"]:
        yield river["river_id"], "guide_seat_downstream", river["guide_seat_capture"]
        yield river["river_id"], "river_eye_downstream", river["river_eye_capture"]


def build_capture_quality_review(repo_root: Path, generated_on: str = "2026-07-08") -> dict:
    capture_manifest_path = repo_root / CAPTURE_MANIFEST_RELATIVE_PATH
    capture_manifest = json.loads(capture_manifest_path.read_text(encoding="utf-8"))
    thresholds = CaptureQualityThresholds()
    captures = [
        analyze_capture(repo_root, capture_path, river_id, view_id, thresholds)
        for river_id, view_id, capture_path in _capture_entries(capture_manifest)
    ]
    renderer_proxy_blockers = _renderer_proxy_blockers(repo_root, capture_manifest)
    if renderer_proxy_blockers:
        for capture in captures:
            capture["blockers"].extend(renderer_proxy_blockers)
            capture["status"] = "preview_only_not_lifelike_quality_blockers"

    blocker_counts: Counter[str] = Counter(
        blocker["id"]
        for capture in captures
        for blocker in capture["blockers"]
    )
    per_river_status: dict[str, dict[str, object]] = {}
    for capture in captures:
        river = per_river_status.setdefault(
            capture["river_id"],
            {"capture_count": 0, "blocking_capture_count": 0, "blockers": set()},
        )
        river["capture_count"] = int(river["capture_count"]) + 1
        if capture["blockers"]:
            river["blocking_capture_count"] = int(river["blocking_capture_count"]) + 1
        river["blockers"].update(blocker["id"] for blocker in capture["blockers"])

    normalized_per_river = {
        river_id: {
            "capture_count": data["capture_count"],
            "blocking_capture_count": data["blocking_capture_count"],
            "blockers": sorted(data["blockers"]),
            "status": "preview_only_not_lifelike_quality_blockers"
            if data["blocking_capture_count"]
            else "candidate_for_human_lifelike_review_not_approved",
        }
        for river_id, data in sorted(per_river_status.items())
    }
    blocking_capture_count = sum(1 for capture in captures if capture["blockers"])
    status = (
        "captures_reviewed_preview_only_not_lifelike_quality_blockers_recorded"
        if blocking_capture_count
        else "captures_reviewed_candidate_for_human_lifelike_review_not_approved"
    )
    current_decision = (
        "Use this automated review as a regression gate for the photoreal environment track. "
        "The current captures have no automated blocker counts and may advance to human art, guide, "
        "geospatial, rights, hazard-readability, and performance review, but automated metrics do not approve "
        "the visuals as lifelike or production-ready."
        if blocking_capture_count == 0
        else (
            "Use this automated review as a regression gate for the photoreal environment track. "
            "The current captures remain preview-only because at least one automated or source-aware blocker "
            "is present; passing pixel checks still does not replace guide, geospatial, rights, "
            "hazard-readability, performance, and art-direction approval."
        )
    )

    return {
        "schema": "raftsim.unreal.photoreal_capture_quality_review.v1",
        "generated_on": generated_on,
        "status": status,
        "source_capture_manifest": str(CAPTURE_MANIFEST_RELATIVE_PATH),
        "policy": {
            "metrics_are_blockers_not_lifelike_approval": True,
            "human_guide_geospatial_and_art_review_still_required": True,
            "water_visuals_must_not_hide_hazards_rescue_targets_or_physics_failures": True,
        },
        "thresholds": thresholds.as_dict(),
        "summary": {
            "capture_count": len(captures),
            "blocking_capture_count": blocking_capture_count,
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "per_river": normalized_per_river,
        },
        "captures": captures,
        "current_decision": current_decision,
    }


def write_capture_quality_review(repo_root: Path, generated_on: str = "2026-07-08") -> Path:
    review = build_capture_quality_review(repo_root, generated_on=generated_on)
    output_path = repo_root / CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output_path


def _path_size_bytes(repo_root: Path, relative_path: str | Path) -> int:
    path = repo_root / relative_path
    if not path.exists() or not path.is_file():
        return 0
    return path.stat().st_size


def _hash_if_file(repo_root: Path, relative_path: str | Path) -> str | None:
    path = repo_root / relative_path
    if not path.exists() or not path.is_file():
        return None
    return _hash_file(path)


def _unreal_package_to_relative_asset_path(package_path: str) -> Path:
    if package_path.startswith("/Game/"):
        return Path("unreal/Content") / f"{package_path.removeprefix('/Game/')}.umap"
    return Path(package_path)


def _asset_root_inventory(repo_root: Path, relative_path: str | Path, suffix: str = ".uasset") -> dict[str, object]:
    root = repo_root / relative_path
    files = sorted(path for path in root.rglob(f"*{suffix}") if path.is_file()) if root.exists() else []
    return {
        "root": str(relative_path),
        "exists": root.exists(),
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def _capture_static_inventory(
    repo_root: Path,
    river: dict[str, object],
    capture_reviews: dict[tuple[str, str], dict[str, object]],
) -> dict[str, object]:
    capture_entries = []
    total_capture_bytes = 0
    for view_id, field in (
        ("guide_seat_downstream", "guide_seat_capture"),
        ("river_eye_downstream", "river_eye_capture"),
    ):
        capture_path = str(river[field])
        capture_review = capture_reviews.get((str(river["river_id"]), view_id), {})
        size_bytes = _path_size_bytes(repo_root, capture_path)
        total_capture_bytes += size_bytes
        capture_entries.append(
            {
                "view_id": view_id,
                "capture": capture_path,
                "exists": (repo_root / capture_path).exists(),
                "sha256": capture_review.get("sha256") or _hash_if_file(repo_root, capture_path),
                "size_bytes": size_bytes,
                "source_size": capture_review.get("metrics", {}).get("source_size"),
                "automated_blocker_count": len(capture_review.get("blockers", [])),
                "automated_status": capture_review.get("status"),
            }
        )

    map_asset_relative_path = _unreal_package_to_relative_asset_path(str(river["map_package"]))
    return {
        "map_package": river["map_package"],
        "map_asset": {
            "path": str(map_asset_relative_path),
            "exists": (repo_root / map_asset_relative_path).exists(),
            "size_bytes": _path_size_bytes(repo_root, map_asset_relative_path),
            "sha256": _hash_if_file(repo_root, map_asset_relative_path),
        },
        "captures": capture_entries,
        "total_capture_png_bytes": total_capture_bytes,
        "source_inputs": {
            "aerial_drape_image": river.get("aerial_drape_image"),
            "terrain_relief_image": river.get("terrain_relief_image"),
            "heightfield_preview_image": river.get("heightfield_preview_image"),
            "water_mask_image": river.get("water_mask_image"),
            "vegetation_mask_image": river.get("vegetation_mask_image"),
        },
    }


def _profile_budget_rows(runtime_budgets: dict[str, object]) -> list[dict[str, object]]:
    profiles = runtime_budgets.get("profiles", {})
    rows: list[dict[str, object]] = []
    for profile_id in ("desktop", "vr"):
        profile = profiles.get(profile_id, {})
        render_target_hz = int(profile.get("render_target_hz", 0))
        rows.append(
            {
                "profile_id": profile_id,
                "render_target_hz": render_target_hz,
                "target_frame_time_ms": round(1000.0 / render_target_hz, 3) if render_target_hz > 0 else None,
                "physics_tick_hz": profile.get("physics_tick_hz"),
                "total_physics_budget_ms": profile.get("total_physics_ms"),
                "water_solver_budget_ms": profile.get("water_solver_ms"),
                "raft_coupling_budget_ms": profile.get("raft_coupling_ms"),
                "probe_telemetry_budget_ms": profile.get("probe_telemetry_ms"),
                "max_runtime_multiplier": profile.get("max_runtime_multiplier"),
            }
        )
    return rows


def build_photoreal_environment_performance_review(
    repo_root: Path,
    generated_on: str = "2026-07-08",
) -> dict[str, object]:
    """Build the desktop/VR performance evidence packet for photoreal environment review."""

    capture_manifest = _read_json_if_present(repo_root, CAPTURE_MANIFEST_RELATIVE_PATH)
    capture_quality_review = build_capture_quality_review(repo_root, generated_on=generated_on)
    runtime_budgets = _read_json_if_present(repo_root, RUNTIME_BUDGETS_RELATIVE_PATH)
    capture_reviews = _capture_reviews_by_key(capture_quality_review)
    profile_budgets = _profile_budget_rows(runtime_budgets)
    material_texture_asset_root = capture_manifest.get("first_party_material_texture_asset_root", "")
    source_conditioned_texture_asset_root = capture_manifest.get("source_conditioned_material_texture_asset_root", "")
    material_instance_asset_root = capture_manifest.get("first_party_material_instance_review_asset_root", "")
    shared_asset_inventory = {
        "first_party_material_texture_assets": _asset_root_inventory(repo_root, material_texture_asset_root),
        "source_conditioned_material_texture_assets": _asset_root_inventory(
            repo_root,
            source_conditioned_texture_asset_root,
        ),
        "material_instance_review_assets": _asset_root_inventory(repo_root, material_instance_asset_root),
    }

    rivers: list[dict[str, object]] = []
    open_profile_measurement_count = 0
    for river in capture_manifest.get("captures", []):
        profiles = []
        for profile in profile_budgets:
            open_profile_measurement_count += 1
            profiles.append(
                {
                    **profile,
                    "status": "requires_measured_unreal_profile_capture",
                    "approved": False,
                    "evidence_attached": False,
                    "required_measurements": {
                        "scalability_preset": None,
                        "resolution_or_hmd_render_target": None,
                        "frame_time_ms_p50": None,
                        "frame_time_ms_p95": None,
                        "game_thread_ms_p95": None,
                        "render_thread_ms_p95": None,
                        "gpu_ms_p95": None,
                        "draw_calls": None,
                        "visible_primitives_or_triangles": None,
                        "gpu_memory_mb": None,
                        "vr_comfort_or_motion_readability_notes": None,
                        "hazard_and_rescue_readability_notes": None,
                    },
                    "blocking_open_measurements": [
                        "measured_frame_time_distribution",
                        "game_render_gpu_thread_breakdown",
                        "gpu_memory_and_draw_call_or_primitive_count",
                        "scalability_settings_and_capture_hardware",
                        "vr_comfort_readability_notes" if profile["profile_id"] == "vr" else "desktop_readability_notes",
                    ],
                }
            )

        rivers.append(
            {
                "river_id": river["river_id"],
                "display_name": river["display_name"],
                "status": "static_capture_inventory_recorded_performance_measurement_required",
                "approved_for_production_playable": False,
                "flow_context": {
                    "flow_band_id": river.get("flow_band_id"),
                    "flow_band_display_name": river.get("flow_band_display_name"),
                    "flow_reference_discharge_cfs": river.get("flow_reference_discharge_cfs"),
                    "flow_visual_width_scale": river.get("flow_visual_width_scale"),
                    "flow_visual_foam_scale": river.get("flow_visual_foam_scale"),
                    "flow_visual_current_cue_scale": river.get("flow_visual_current_cue_scale"),
                },
                "static_inventory": _capture_static_inventory(repo_root, river, capture_reviews),
                "profiles": profiles,
                "current_decision": (
                    "Use this row to attach measured desktop and VR profiling for the current zero-blocker capture "
                    "candidate. Static map/capture/asset inventory is recorded, but this river is not production-playable "
                    "until every profile has measured frame-time, thread/GPU/memory, scalability, and readability evidence."
                ),
            }
        )

    return {
        "schema": "raftsim.unreal.photoreal_environment_performance_review.v1",
        "generated_on": generated_on,
        "status": "awaiting_measured_desktop_vr_performance_capture_not_approved",
        "source_capture_manifest": str(CAPTURE_MANIFEST_RELATIVE_PATH),
        "source_capture_quality_review": str(CAPTURE_QUALITY_REVIEW_RELATIVE_PATH),
        "source_runtime_budgets": str(RUNTIME_BUDGETS_RELATIVE_PATH),
        "policy": {
            "static_inventory_is_not_performance_approval": True,
            "desktop_and_vr_profiles_required_before_production_playable": True,
            "vr_profile_requires_comfort_and_hazard_readability_notes": True,
            "performance_must_not_trade_away_hazard_rescue_or_water_readability": True,
        },
        "summary": {
            "river_count": len(rivers),
            "profile_count": len(rivers) * len(profile_budgets),
            "profile_ids": [profile["profile_id"] for profile in profile_budgets],
            "measured_profile_count": 0,
            "open_profile_measurement_count": open_profile_measurement_count,
            "automated_capture_blocking_count": capture_quality_review["summary"]["blocking_capture_count"],
            "approved_river_count": 0,
        },
        "shared_asset_inventory": shared_asset_inventory,
        "profiling_capture_plan": {
            "desktop": [
                "Open each generated preview map from the guide-seat camera.",
                "Record scalability preset, resolution, frame-time distribution, game/render/GPU thread costs, draw calls/primitives, and GPU memory.",
                "Attach a screenshot or video clip proving hazards, swimmers/rescue targets, and water cues remain readable at the measured setting.",
            ],
            "vr": [
                "Run the same map path in the OpenXR/VR profile or the target HMD simulator with comfort settings recorded.",
                "Record target render resolution, refresh rate, frame-time distribution, thread/GPU costs, dropped/reprojected frames, and GPU memory.",
                "Attach comfort, motion readability, hazard/rescue readability, and guide-seat visibility notes.",
            ],
        },
        "rivers": rivers,
        "current_decision": (
            "This artifact closes the missing static evidence packet for desktop/VR review, but does not pass the "
            "performance gate. Real Unreal profiling captures must be attached for every river/profile before any "
            "environment is marked production-playable or lifelike-approved."
        ),
    }


def write_photoreal_environment_performance_review(
    repo_root: Path,
    generated_on: str = "2026-07-08",
) -> Path:
    review = build_photoreal_environment_performance_review(repo_root, generated_on=generated_on)
    output_path = repo_root / PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output_path


def _read_json_if_present(repo_root: Path, relative_path: Path) -> dict:
    path = repo_root / relative_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _review_targets_by_river(reference_queue: dict) -> dict[str, list[dict[str, object]]]:
    targets_by_river: dict[str, list[dict[str, object]]] = {}
    for target in reference_queue.get("review_targets", []):
        river_id = target.get("river_id")
        if not isinstance(river_id, str):
            continue
        targets_by_river.setdefault(river_id, []).append(
            {
                "target_id": target.get("target_id"),
                "anchor_hint": target.get("anchor_hint"),
                "visual_questions": target.get("visual_questions", []),
                "candidate_source_ids": target.get("candidate_source_ids", []),
                "annotation_outputs": target.get("annotation_outputs", []),
                "flow_context_needed": target.get("flow_context_needed", []),
                "rights_status": target.get("rights_status"),
            }
        )
    return targets_by_river


def _source_plan_rivers_by_id(source_plan: dict) -> dict[str, dict[str, object]]:
    return {
        river["river_id"]: river
        for river in source_plan.get("rivers", [])
        if isinstance(river, dict) and isinstance(river.get("river_id"), str)
    }


def _gap_register_rivers_by_id(gap_register: dict) -> dict[str, dict[str, object]]:
    return {
        river["river_id"]: river
        for river in gap_register.get("rivers", [])
        if isinstance(river, dict) and isinstance(river.get("river_id"), str)
    }


def _capture_reviews_by_key(capture_quality_review: dict) -> dict[tuple[str, str], dict[str, object]]:
    return {
        (capture["river_id"], capture["view_id"]): capture
        for capture in capture_quality_review.get("captures", [])
        if isinstance(capture, dict)
        and isinstance(capture.get("river_id"), str)
        and isinstance(capture.get("view_id"), str)
    }


def _open_review_gates() -> list[dict[str, object]]:
    return [
        {
            "domain_id": domain["domain_id"],
            "required_reviewer": domain["required_reviewer"],
            "required_evidence": domain["required_evidence"],
            "status": "open_pending_human_review_or_production_evidence",
            "approved": False,
        }
        for domain in HUMAN_REVIEW_DOMAINS
    ]


def _visual_replacement_targets(gap_register: dict) -> list[dict[str, object]]:
    targets: list[dict[str, object]] = []
    for target in gap_register.get("global_visual_replacement_targets", []):
        if not isinstance(target, dict):
            continue
        targets.append(
            {
                "target": target.get("target"),
                "required_before_lifelike": target.get("required_before_lifelike", []),
                "current_preview_progress": target.get("current_preview_progress", []),
            }
        )
    return targets


def _capture_handoff_entry(
    river_id: str,
    view_id: str,
    capture_relative_path: str,
    capture_review: dict[str, object],
) -> dict[str, object]:
    return {
        "view_id": view_id,
        "capture": capture_relative_path,
        "sha256": capture_review.get("sha256"),
        "automated_status": capture_review.get("status"),
        "automated_blockers": capture_review.get("blockers", []),
        "metrics": capture_review.get("metrics", {}),
        "human_review_status": "not_reviewed",
        "required_capture_checks": [
            "visual_lifelike_match_to_rights_reviewed_reference_or_first_party_field_media",
            "hazards_swimmers_rescue_targets_and_readable_water_features_not_hidden",
            "source_alignment_notes_for_visible_banks_terrain_water_mask_and_flow_band",
            "production_asset_material_or_first_party_equivalent_promotion_decision",
            "desktop_and_vr_performance_readability_notes",
        ],
        "approval_status": "not_approved_for_lifelike_or_production",
        "river_id": river_id,
    }


def build_human_lifelike_review_handoff(repo_root: Path, generated_on: str = "2026-07-08") -> dict:
    """Build the human-review handoff for zero-blocker photoreal capture candidates."""

    capture_manifest = _read_json_if_present(repo_root, CAPTURE_MANIFEST_RELATIVE_PATH)
    capture_quality_review = build_capture_quality_review(repo_root, generated_on=generated_on)
    reference_queue = _read_json_if_present(repo_root, REFERENCE_MEDIA_REVIEW_QUEUE_RELATIVE_PATH)
    gap_register = _read_json_if_present(repo_root, PRODUCTION_ENVIRONMENT_GAP_REGISTER_RELATIVE_PATH)
    source_plan = _read_json_if_present(repo_root, PHOTOREAL_RIVER_ENVIRONMENT_SOURCES_RELATIVE_PATH)

    capture_reviews = _capture_reviews_by_key(capture_quality_review)
    reference_targets = _review_targets_by_river(reference_queue)
    source_rivers = _source_plan_rivers_by_id(source_plan)
    gap_rivers = _gap_register_rivers_by_id(gap_register)
    visual_replacement_targets = _visual_replacement_targets(gap_register)
    review_domains = [
        {
            **domain,
            "status": "required_before_lifelike_approval",
            "approved": False,
        }
        for domain in HUMAN_REVIEW_DOMAINS
    ]

    rivers: list[dict[str, object]] = []
    candidate_capture_count = 0
    for river in capture_manifest.get("captures", []):
        river_id = river["river_id"]
        source_river = source_rivers.get(river_id, {})
        gap_river = gap_rivers.get(river_id, {})
        captures: list[dict[str, object]] = []
        for view_id, capture_path in (
            ("guide_seat_downstream", river["guide_seat_capture"]),
            ("river_eye_downstream", river["river_eye_capture"]),
        ):
            capture_review = capture_reviews.get((river_id, view_id), {})
            if not capture_review.get("blockers"):
                candidate_capture_count += 1
            captures.append(_capture_handoff_entry(river_id, view_id, capture_path, capture_review))

        rivers.append(
            {
                "river_id": river_id,
                "display_name": river.get("display_name") or source_river.get("display_name"),
                "review_status": "awaiting_human_lifelike_review_not_approved",
                "readiness": gap_river.get("readiness", "preview_only_not_lifelike"),
                "map_package": river.get("map_package") or source_river.get("target_unreal_map"),
                "source_manifest": river.get("source_manifest") or source_river.get("source_manifest"),
                "flow_context": {
                    "flow_band_id": river.get("flow_band_id"),
                    "flow_band_display_name": river.get("flow_band_display_name"),
                    "flow_band_source": river.get("flow_band_source"),
                    "flow_reference_discharge_cfs": river.get("flow_reference_discharge_cfs"),
                    "flow_visual_width_scale": river.get("flow_visual_width_scale"),
                    "flow_visual_foam_scale": river.get("flow_visual_foam_scale"),
                    "flow_visual_wet_bank_scale": river.get("flow_visual_wet_bank_scale"),
                    "flow_visual_current_cue_scale": river.get("flow_visual_current_cue_scale"),
                    "flow_visual_water_level_offset_cm": river.get("flow_visual_water_level_offset_cm"),
                    "flow_visual_note": river.get("flow_visual_note"),
                },
                "source_inputs_for_review": {
                    "aerial_drape_image": river.get("aerial_drape_image"),
                    "terrain_relief_image": river.get("terrain_relief_image"),
                    "heightfield_preview_image": river.get("heightfield_preview_image"),
                    "water_mask_image": river.get("water_mask_image"),
                    "vegetation_mask_image": river.get("vegetation_mask_image"),
                    "elevation_sample": river.get("elevation_sample"),
                },
                "captures": captures,
                "reference_media_review_targets": reference_targets.get(river_id, []),
                "open_review_gates": _open_review_gates(),
                "visual_replacement_targets": visual_replacement_targets,
                "fidelity_note": river.get("fidelity_note"),
                "current_decision": (
                    "Automated blockers are clear for this river's current guide-seat and river-eye captures, "
                    "but lifelike approval is withheld until every open human-review, rights, production-material, "
                    "hazard-readability, geospatial, guide, and performance gate records accepted evidence."
                ),
            }
        )

    blocking_gate_count = len(rivers) * len(review_domains)
    return {
        "schema": "raftsim.unreal.photoreal_human_lifelike_review_handoff.v1",
        "generated_on": generated_on,
        "status": "awaiting_human_lifelike_review_not_approved",
        "source_capture_manifest": str(CAPTURE_MANIFEST_RELATIVE_PATH),
        "source_capture_quality_review": str(CAPTURE_QUALITY_REVIEW_RELATIVE_PATH),
        "source_performance_review": str(PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH),
        "source_reference_media_review_queue": str(REFERENCE_MEDIA_REVIEW_QUEUE_RELATIVE_PATH),
        "source_gap_register": str(PRODUCTION_ENVIRONMENT_GAP_REGISTER_RELATIVE_PATH),
        "policy": {
            "automated_metrics_do_not_approve_lifelike_visuals": True,
            "human_review_must_not_use_uncleared_media_as_texture_training_or_packaged_assets": True,
            "approval_requires_hazard_rescue_and_water_readability": True,
            "approval_requires_desktop_and_vr_performance_evidence": True,
            "all_review_domains_must_be_approved_before_lifelike_status": True,
        },
        "summary": {
            "river_count": len(rivers),
            "capture_count": len(capture_quality_review["captures"]),
            "candidate_capture_count": candidate_capture_count,
            "automated_blocking_capture_count": capture_quality_review["summary"]["blocking_capture_count"],
            "human_approved_capture_count": 0,
            "open_human_review_gate_count": blocking_gate_count,
            "per_river": {
                river["river_id"]: {
                    "review_status": river["review_status"],
                    "capture_count": len(river["captures"]),
                    "open_review_gate_count": len(river["open_review_gates"]),
                    "reference_media_review_target_count": len(river["reference_media_review_targets"]),
                }
                for river in rivers
            },
        },
        "review_domains": review_domains,
        "rivers": rivers,
        "current_decision": (
            "Use this handoff to drive the next human art, guide, geospatial, rights, hazard-readability, "
            "production-material, and performance review pass. The zero-blocker captures are review candidates only; "
            "no river is approved as lifelike or production-playable by this artifact."
        ),
    }


def write_human_lifelike_review_handoff(repo_root: Path, generated_on: str = "2026-07-08") -> Path:
    handoff = build_human_lifelike_review_handoff(repo_root, generated_on=generated_on)
    output_path = repo_root / HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    return output_path


def _format_metric(metrics: dict[str, object], key: str) -> str:
    value = metrics.get(key)
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, int):
        return str(value)
    return ""


def _capture_image_link(capture_relative_path: str) -> str:
    return Path(capture_relative_path).name


def _domain_title(domain_id: str) -> str:
    return domain_id.replace("_", " ").title()


def build_human_lifelike_review_packet_markdown(repo_root: Path, generated_on: str = "2026-07-08") -> str:
    """Build a reviewer-facing Markdown packet from the current human-review handoff."""

    handoff = build_human_lifelike_review_handoff(repo_root, generated_on=generated_on)
    lines: list[str] = [
        "# Photoreal Human Lifelike Review Packet",
        "",
        f"Generated on: `{handoff['generated_on']}`",
        "",
        f"Status: `{handoff['status']}`",
        "",
        (
            "This packet is for human review of the current zero-blocker Unreal capture candidates. "
            "The images are not approved as lifelike or production-ready until every review domain below has accepted evidence."
        ),
        "",
        "Source artifacts:",
        "",
        f"- Capture manifest: `{handoff['source_capture_manifest']}`",
        f"- Automated capture review: `{handoff['source_capture_quality_review']}`",
        f"- Desktop/VR performance evidence: `{handoff['source_performance_review']}`",
        f"- Human review handoff JSON: `{HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH}`",
        f"- Human review results template: `{HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH}`",
        f"- Reference media queue: `{handoff['source_reference_media_review_queue']}`",
        f"- Gap register: `{handoff['source_gap_register']}`",
        "",
        "## Required Review Domains",
        "",
    ]

    for domain in handoff["review_domains"]:
        lines.extend(
            [
                f"- [ ] **{_domain_title(domain['domain_id'])}**",
                f"  Reviewer: `{domain['required_reviewer']}`",
                "  Required evidence:",
            ]
        )
        for evidence in domain["required_evidence"]:
            lines.append(f"  - `{evidence}`")

    lines.extend(
        [
            "",
            "## River Review Sheets",
            "",
        ]
    )

    for river in handoff["rivers"]:
        lines.extend(
            [
                f"### {river['display_name']} (`{river['river_id']}`)",
                "",
                f"Review status: `{river['review_status']}`",
                "",
                f"Map package: `{river['map_package']}`",
                "",
                f"Source manifest: `{river['source_manifest']}`",
                "",
                "Flow context:",
                "",
            ]
        )
        flow_context = river["flow_context"]
        for key in (
            "flow_band_id",
            "flow_band_display_name",
            "flow_band_source",
            "flow_reference_discharge_cfs",
            "flow_visual_width_scale",
            "flow_visual_foam_scale",
            "flow_visual_wet_bank_scale",
            "flow_visual_current_cue_scale",
            "flow_visual_water_level_offset_cm",
        ):
            if flow_context.get(key) is not None:
                lines.append(f"- `{key}`: `{flow_context[key]}`")
        if flow_context.get("flow_visual_note"):
            lines.append(f"- `flow_visual_note`: {flow_context['flow_visual_note']}")

        lines.extend(["", "Source inputs for review:", ""])
        for key, value in river["source_inputs_for_review"].items():
            if value:
                lines.append(f"- `{key}`: `{value}`")

        lines.extend(
            [
                "",
                "Captures:",
                "",
                "| View | Image | Entropy | Edge | Low-gradient | Luma std | Human status |",
                "| --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for capture in river["captures"]:
            image_name = _capture_image_link(capture["capture"])
            metrics = capture["metrics"]
            lines.append(
                "| "
                f"`{capture['view_id']}` | "
                f"![{river['river_id']} {capture['view_id']}]({image_name}) | "
                f"{_format_metric(metrics, 'quantized_entropy_bits')} | "
                f"{_format_metric(metrics, 'edge_density')} | "
                f"{_format_metric(metrics, 'low_gradient_fraction')} | "
                f"{_format_metric(metrics, 'luma_std')} | "
                f"`{capture['human_review_status']}` |"
            )

        lines.extend(["", "Reviewer checks:", ""])
        for gate in river["open_review_gates"]:
            lines.append(f"- [ ] `{gate['domain_id']}` - `{gate['required_reviewer']}`")

        lines.extend(["", "Reference media review prompts:", ""])
        for target in river["reference_media_review_targets"]:
            lines.append(f"- `{target['target_id']}`: {target['anchor_hint']}")
            for question in target.get("visual_questions", []):
                lines.append(f"  - {question}")
            lines.append(f"  - Rights status: `{target.get('rights_status')}`")

        lines.extend(
            [
                "",
                "Reviewer notes:",
                "",
                "- Art direction visual lifelike:",
                "- Guide/hydraulic fidelity:",
                "- Geospatial source alignment:",
                "- Rights/media provenance:",
                "- Hazard and rescue readability:",
                "- Production material/asset promotion:",
                "- Desktop and VR performance:",
                "",
                "Decision:",
                "",
                "- [ ] Keep as preview-only candidate evidence",
                "- [ ] Request regeneration with listed fixes",
                "- [ ] Approve this river for lifelike promotion after all gates above are signed off",
                "",
            ]
        )

    lines.extend(
        [
            "## Final Promotion Rule",
            "",
            (
                "Do not mark any river lifelike or production-playable from this packet unless every review domain "
                "has accepted evidence, rights are recorded for any visual references, hazards and rescue targets remain readable, "
                "and desktop plus VR performance evidence is attached."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_human_lifelike_review_packet_markdown(repo_root: Path, generated_on: str = "2026-07-08") -> Path:
    packet = build_human_lifelike_review_packet_markdown(repo_root, generated_on=generated_on)
    output_path = repo_root / HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(packet, encoding="utf-8")
    return output_path


def _empty_review_domain_result(domain: dict[str, object]) -> dict[str, object]:
    return {
        "domain_id": domain["domain_id"],
        "required_reviewer": domain["required_reviewer"],
        "status": "not_reviewed",
        "approved": False,
        "reviewer_name": "",
        "reviewer_role_or_credential": "",
        "review_date": "",
        "required_evidence": domain["required_evidence"],
        "evidence_links_or_artifacts": [],
        "notes": "",
        "blockers": [],
        "follow_up_actions": [],
    }


def build_human_lifelike_review_results_template(repo_root: Path, generated_on: str = "2026-07-08") -> dict:
    """Build the machine-readable intake template for external human review results."""

    handoff = build_human_lifelike_review_handoff(repo_root, generated_on=generated_on)
    review_domains = handoff["review_domains"]
    rivers: list[dict[str, object]] = []
    for river in handoff["rivers"]:
        rivers.append(
            {
                "river_id": river["river_id"],
                "display_name": river["display_name"],
                "review_status": "not_reviewed_not_approved",
                "source_manifest": river["source_manifest"],
                "map_package": river["map_package"],
                "flow_context": river["flow_context"],
                "captures": [
                    {
                        "view_id": capture["view_id"],
                        "capture": capture["capture"],
                        "sha256": capture["sha256"],
                        "automated_status": capture["automated_status"],
                        "human_review_status": "not_reviewed",
                        "approval_status": "not_approved_for_lifelike_or_production",
                    }
                    for capture in river["captures"]
                ],
                "domain_results": [_empty_review_domain_result(domain) for domain in review_domains],
                "river_level_notes": "",
                "final_river_decision": {
                    "status": "not_reviewed",
                    "approved_for_lifelike": False,
                    "approved_for_production_playable": False,
                    "decision_maker": "",
                    "decision_date": "",
                    "decision_notes": "",
                    "required_follow_up_before_promotion": [],
                },
            }
        )

    return {
        "schema": "raftsim.unreal.photoreal_human_lifelike_review_results_template.v1",
        "generated_on": generated_on,
        "status": "awaiting_external_human_review_inputs_not_approved",
        "source_handoff": str(HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH),
        "source_packet": str(HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH),
        "source_capture_quality_review": str(CAPTURE_QUALITY_REVIEW_RELATIVE_PATH),
        "source_performance_review": str(PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH),
        "policy": {
            "do_not_self_approve_with_automated_metrics": True,
            "reviewer_identity_role_and_date_required_for_approval": True,
            "evidence_links_or_artifacts_required_for_each_domain_approval": True,
            "uncleared_media_must_remain_link_only_until_rights_are_recorded": True,
            "hazard_rescue_and_physics_readability_block_lifelike_promotion": True,
            "desktop_and_vr_performance_evidence_required_before_production_playable": True,
        },
        "summary": {
            "river_count": len(rivers),
            "capture_count": sum(len(river["captures"]) for river in rivers),
            "review_domain_count": len(review_domains),
            "open_review_result_count": len(rivers) * len(review_domains),
            "approved_river_count": 0,
        },
        "rivers": rivers,
        "promotion_rule": (
            "A river may be promoted from preview-only only after every domain result is approved with reviewer "
            "identity, date, evidence, and notes; the river-level decision approves lifelike status; rights are "
            "recorded for visual references; hazards and rescue targets remain readable; and desktop/VR performance "
            "evidence is attached."
        ),
    }


def write_human_lifelike_review_results_template(repo_root: Path, generated_on: str = "2026-07-08") -> Path:
    template = build_human_lifelike_review_results_template(repo_root, generated_on=generated_on)
    output_path = repo_root / HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    return output_path
