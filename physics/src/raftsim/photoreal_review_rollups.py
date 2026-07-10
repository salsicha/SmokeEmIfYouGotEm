"""Synchronize photoreal capture evidence into planning manifests."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.production_detail_textures import (
    MANIFEST_RELATIVE_PATH as PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH,
    TEXTURE_ASSET_ROOT_RELATIVE_PATH as PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH,
    TEXTURE_ASSET_STATUS as PRODUCTION_DETAIL_ASSET_STATUS,
)


CAPTURE_ROOT = Path("docs/environment-captures/photoreal_river_previews")
BASE_CAPTURE_REVIEW_PATH = CAPTURE_ROOT / "photoreal_capture_quality_review.json"
FLOW_CAPTURE_REVIEW_PATH = CAPTURE_ROOT / "photoreal_flow_variant_capture_quality_review.json"
BASE_HUMAN_HANDOFF_PATH = CAPTURE_ROOT / "photoreal_human_lifelike_review_handoff.json"
FLOW_HUMAN_HANDOFF_PATH = CAPTURE_ROOT / "photoreal_flow_variant_human_lifelike_review_handoff.json"
BASE_PERFORMANCE_REVIEW_PATH = CAPTURE_ROOT / "photoreal_environment_performance_review.json"
FLOW_PERFORMANCE_REVIEW_PATH = CAPTURE_ROOT / "photoreal_flow_variant_environment_performance_review.json"

ASSET_PLAN_PATH = Path("unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json")
SOURCE_PLAN_PATH = Path("unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json")
ART_RESEARCH_PATH = Path("unreal/Content/RaftSim/Rendering/art_asset_source_research.json")
GAP_REGISTER_PATH = Path("physics/data/real_world/production_environment_gap_register.json")

PRODUCTION_DETAIL_CHECKPOINT_ID = "production_detail_material_checkpoint_2026_07_09"
SOURCE_TERRAIN_CHECKPOINT_ID = "source_terrain_geometry_checkpoint_2026_07_09"
CHECKPOINT_ID = "water_light_response_checkpoint_2026_07_09"
GENERATED_ON = "2026-07-09"


def _read_json(repo_root: Path, relative_path: Path) -> dict:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _write_json(repo_root: Path, relative_path: Path, payload: dict) -> None:
    (repo_root / relative_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _checkpoint(base_review: dict, flow_review: dict) -> dict:
    return {
        "status": "source_terrain_and_dedicated_water_light_response_rendered_gate_blocked_not_lifelike",
        "production_detail_texture_manifest": str(PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH),
        "production_detail_texture_asset_root": str(PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH),
        "production_detail_texture_asset_status": PRODUCTION_DETAIL_ASSET_STATUS,
        "renderer_corrections": [
            "metal_safe_split_rg_atlas_and_detail_uv_parameters",
            "first_party_close_range_terrain_detail_albedo_normal_and_ao_roughness_height",
            "legacy_terrain_overlay_proxy_geometry_disabled",
            "legacy_water_overlay_proxy_geometry_disabled",
            "synthetic_capture_film_grain_disabled",
            "source_heightfield_bilinear_sampling_and_center_seam_feathering",
            "source_heightfield_meter_scale_macro_relief_and_multiscale_local_erosion_residual",
            "river_specific_source_terrain_normal_flattening_reduced",
            "dedicated_default_lit_water_parent_isolated_from_atlas_terrain_parent",
            "flow_dependent_river_ribbon_mesh_normals_preserved",
            "tile_safe_first_party_water_normal_atlas_sampling",
            "river_specific_bounded_water_emissive_roughness_specular_and_normal_response",
            "near_camera_water_color_and_relief_suppression_reduced_with_luminance_floor_retained",
            "source_baked_terrain_vertex_color_material_retained_after_atlas_parent_loaded_black",
        ],
        "base_capture_quality_summary": base_review["summary"],
        "flow_variant_capture_quality_summary": flow_review["summary"],
        "remaining_base_blocker_counts": base_review["summary"]["blocker_counts"],
        "remaining_flow_variant_blocker_counts": flow_review["summary"]["blocker_counts"],
        "comparison_to_committed_production_detail_checkpoint": {
            "committed_checkpoint": "4fb76ae4f",
            "prior_base_blocker_counts": {
                "excess_low_gradient_area": 6,
                "low_color_texture_entropy": 6,
                "low_edge_density": 6,
                "low_luma_variation": 2,
            },
            "current_base_blocker_counts": base_review["summary"]["blocker_counts"],
            "prior_flow_variant_blocker_counts": {
                "excess_low_gradient_area": 19,
                "low_color_texture_entropy": 20,
                "low_edge_density": 20,
                "low_luma_variation": 6,
            },
            "current_flow_variant_blocker_counts": flow_review["summary"]["blocker_counts"],
            "excess_low_gradient_area_delta": {
                "base": base_review["summary"]["blocker_counts"].get("excess_low_gradient_area", 0) - 6,
                "flow_variant": (
                    flow_review["summary"]["blocker_counts"].get("excess_low_gradient_area", 0) - 19
                ),
            },
        },
        "comparison_to_source_terrain_checkpoint": {
            "checkpoint": SOURCE_TERRAIN_CHECKPOINT_ID,
            "prior_base_blocker_counts": {
                "excess_low_gradient_area": 5,
                "low_color_texture_entropy": 6,
                "low_edge_density": 6,
                "low_luma_variation": 2,
            },
            "current_base_blocker_counts": base_review["summary"]["blocker_counts"],
            "prior_flow_variant_blocker_counts": {
                "excess_low_gradient_area": 18,
                "low_color_texture_entropy": 20,
                "low_edge_density": 20,
                "low_luma_variation": 6,
            },
            "current_flow_variant_blocker_counts": flow_review["summary"]["blocker_counts"],
            "excess_low_gradient_area_delta": {
                "base": base_review["summary"]["blocker_counts"].get("excess_low_gradient_area", 0) - 5,
                "flow_variant": (
                    flow_review["summary"]["blocker_counts"].get("excess_low_gradient_area", 0) - 18
                ),
            },
        },
        "next_visual_art_blocker": (
            "Promote conditioned source terrain into production Landscape/Nanite assets and replace the dedicated "
            "review water parent with production WaterBody/custom shading, reflection/refraction, solver-driven foam, "
            "and spray; then replace proxy rocks/foliage and placeholder atmosphere/VFX until edge density, broad smooth "
            "area, color entropy, and Colorado luminance blockers clear without synthetic grain or overlay cards."
        ),
    }


def sync_photoreal_environment_review_rollups(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    base_review = _read_json(repo_root, BASE_CAPTURE_REVIEW_PATH)
    flow_review = _read_json(repo_root, FLOW_CAPTURE_REVIEW_PATH)
    base_handoff = _read_json(repo_root, BASE_HUMAN_HANDOFF_PATH)
    flow_handoff = _read_json(repo_root, FLOW_HUMAN_HANDOFF_PATH)
    base_performance = _read_json(repo_root, BASE_PERFORMANCE_REVIEW_PATH)
    flow_performance = _read_json(repo_root, FLOW_PERFORMANCE_REVIEW_PATH)
    production_detail = _read_json(repo_root, PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH)

    if production_detail["unreal_integration"]["asset_status"] != PRODUCTION_DETAIL_ASSET_STATUS:
        raise ValueError("Production detail manifest and rollup asset status disagree")

    checkpoint = _checkpoint(base_review, flow_review)

    asset_plan = _read_json(repo_root, ASSET_PLAN_PATH)
    asset_plan["generated_on"] = GENERATED_ON
    integration = asset_plan["unreal_integration"]
    integration["production_detail_texture_manifest"] = str(PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH)
    integration["production_detail_texture_asset_root"] = str(PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH)
    integration["production_detail_texture_asset_status"] = PRODUCTION_DETAIL_ASSET_STATUS
    integration["photoreal_capture_quality_summary"] = base_review["summary"]
    integration["photoreal_human_lifelike_review_handoff_summary"] = base_handoff["summary"]
    integration[CHECKPOINT_ID] = checkpoint
    integration["visual_blocker_reduction_checkpoint_2026_07_08"]["superseded_by"] = CHECKPOINT_ID
    if PRODUCTION_DETAIL_CHECKPOINT_ID in integration:
        integration[PRODUCTION_DETAIL_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    if SOURCE_TERRAIN_CHECKPOINT_ID in integration:
        integration[SOURCE_TERRAIN_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    asset_plan["current_decision"] = (
        "Use the first-party procedural plan and production-detail textures as traceable Unreal inputs, but keep "
        "all rivers preview_only_not_lifelike. The corrected material graph now renders real close-range terrain "
        "detail without legacy overlay geometry or synthetic film grain. Bilinear seam-feathered source heightfields "
        "provide meter-scale macro terrain and local erosion relief. A dedicated DefaultLit water parent now preserves "
        "flow mesh normals, samples the tile-safe first-party water normal atlas, and exposes bounded per-river light "
        "response without destabilizing terrain. The current reviews still record smooth-water, edge-density, entropy, "
        "and Colorado luminance blockers; human review and measured desktop/VR performance remain open after those clear."
    )
    _write_json(repo_root, ASSET_PLAN_PATH, asset_plan)

    source_plan = _read_json(repo_root, SOURCE_PLAN_PATH)
    source_plan["generated_on"] = GENERATED_ON
    source_plan["production_detail_texture_manifest"] = str(PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH)
    source_plan["production_detail_texture_asset_root"] = str(PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH)
    source_plan["production_detail_texture_asset_status"] = PRODUCTION_DETAIL_ASSET_STATUS
    generation = source_plan["unreal_generation"]
    generation["production_detail_texture_manifest"] = str(PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH)
    generation["production_detail_texture_asset_root"] = str(PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH)
    generation["production_detail_texture_asset_status"] = PRODUCTION_DETAIL_ASSET_STATUS
    generation["photoreal_capture_quality_summary"] = base_review["summary"]
    generation["flow_variant_capture_quality_review_summary"] = flow_review["summary"]
    generation["photoreal_human_lifelike_review_handoff_summary"] = base_handoff["summary"]
    generation["flow_variant_human_lifelike_review_handoff_summary"] = flow_handoff["summary"]
    generation["photoreal_environment_performance_review_summary"] = base_performance["summary"]
    generation["flow_variant_environment_performance_review_summary"] = flow_performance["summary"]
    generation[CHECKPOINT_ID] = checkpoint
    generation["visual_blocker_reduction_checkpoint_2026_07_08"]["superseded_by"] = CHECKPOINT_ID
    if PRODUCTION_DETAIL_CHECKPOINT_ID in generation:
        generation[PRODUCTION_DETAIL_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    if SOURCE_TERRAIN_CHECKPOINT_ID in generation:
        generation[SOURCE_TERRAIN_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    _write_json(repo_root, SOURCE_PLAN_PATH, source_plan)

    art_research = _read_json(repo_root, ART_RESEARCH_PATH)
    art_research["date"] = GENERATED_ON
    art_decision = art_research["first_party_procedural_equivalent_decision_2026_07_06"]
    art_decision["production_detail_texture_manifest"] = str(PRODUCTION_DETAIL_MANIFEST_RELATIVE_PATH)
    art_decision["production_detail_texture_asset_root"] = str(PRODUCTION_DETAIL_ASSET_ROOT_RELATIVE_PATH)
    art_decision["production_detail_texture_asset_status"] = PRODUCTION_DETAIL_ASSET_STATUS
    art_decision["photoreal_capture_quality_blockers"] = base_review["summary"]["blocker_counts"]
    art_decision["photoreal_human_lifelike_review_handoff_summary"] = base_handoff["summary"]
    art_decision[CHECKPOINT_ID] = checkpoint
    art_decision["visual_blocker_reduction_checkpoint_2026_07_08"]["superseded_by"] = CHECKPOINT_ID
    if PRODUCTION_DETAIL_CHECKPOINT_ID in art_decision:
        art_decision[PRODUCTION_DETAIL_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    if SOURCE_TERRAIN_CHECKPOINT_ID in art_decision:
        art_decision[SOURCE_TERRAIN_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    art_decision["human_review_note"] = (
        "Human review scaffolding is synchronized, but every current capture remains automatically blocked. "
        "Do not request lifelike approval until the current smoothness, edge-density, entropy, and Colorado "
        "luminance failures are closed with production geometry and shading."
    )
    _write_json(repo_root, ART_RESEARCH_PATH, art_research)

    gap_register = _read_json(repo_root, GAP_REGISTER_PATH)
    gap_register["generated_on"] = GENERATED_ON
    gap_register["next_checkpoint_order"][0] = (
        "Promote conditioned source terrain into production Landscape/Nanite assets; replace the dedicated review "
        "water parent with production WaterBody/custom reflection, refraction, solver-driven foam, and spray; then "
        "replace proxy rocks/foliage and placeholder atmosphere/VFX until the current edge-density, low-gradient, "
        "entropy, and Colorado luminance blockers clear without synthetic grain or overlay cards."
    )
    gap_register[CHECKPOINT_ID] = checkpoint
    gap_register["visual_blocker_reduction_checkpoint_2026_07_08"]["superseded_by"] = CHECKPOINT_ID
    if PRODUCTION_DETAIL_CHECKPOINT_ID in gap_register:
        gap_register[PRODUCTION_DETAIL_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    if SOURCE_TERRAIN_CHECKPOINT_ID in gap_register:
        gap_register[SOURCE_TERRAIN_CHECKPOINT_ID]["superseded_by"] = CHECKPOINT_ID
    _write_json(repo_root, GAP_REGISTER_PATH, gap_register)

    return [ASSET_PLAN_PATH, SOURCE_PLAN_PATH, ART_RESEARCH_PATH, GAP_REGISTER_PATH]
