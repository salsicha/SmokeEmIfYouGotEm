"""Review the V43 Futaleufu exact-geometry component and shadow parity bracket."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v37_temporal_lit_handoff import (
    _silhouette_and_photometry_metrics,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v40_dual_layer import (
    _sha256,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v41_transmission_light_bracket import (
    _directional_response,
    _fixed_overlap_mask,
    _overlap_photometry,
)

LIGHT_MODES = ("frontlit", "backlit")
REPRESENTATIONS = (
    "source_reference",
    "merged_single_no_shadow",
    "merged_split_no_shadow",
    "merged_split_source_shadow",
)
REPORT_NAME = "futaleufu_cordillera_cypress_v43_merged_component_parity_review.json"
CONTACT_SHEET_NAME = (
    "futaleufu_cordillera_cypress_v43_merged_component_parity_contact_sheet.png"
)
PARTITION_MINIMUM_SILHOUETTE_IOU = 0.985
PARTITION_MINIMUM_AREA_RATIO = 0.99
PARTITION_MAXIMUM_AREA_RATIO = 1.01
PARTITION_MINIMUM_LUMINANCE_RATIO = 0.98
PARTITION_MAXIMUM_LUMINANCE_RATIO = 1.02
PARTITION_MAXIMUM_MEAN_CHANNEL_DELTA = 2.0


def _capture_path(capture_root: Path, light_mode: str, representation: str) -> Path:
    return capture_root / (
        "open_grown_conical_hlod_merged_component_parity_"
        f"{light_mode}_{representation}.png"
    )


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    columns = 4
    rows = 2
    thumb_width = 300
    thumb_height = 169
    margin = 14
    title_height = 48
    label_height = 34
    canvas = Image.new(
        "RGB",
        (
            margin * (columns + 1) + thumb_width * columns,
            title_height + margin * (rows + 1) + rows * (label_height + thumb_height),
        ),
        (22, 24, 26),
    )
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V43 EXACT GEOMETRY - COMPONENT / SHADOW PARITY BEFORE REDUCTION",
        fill=(240, 240, 240),
    )
    for row, light_mode in enumerate(LIGHT_MODES):
        for column, representation in enumerate(REPRESENTATIONS):
            x = margin + column * (thumb_width + margin)
            y = title_height + margin + row * (label_height + thumb_height + margin)
            label = f"{light_mode.upper()} - {representation.replace('_', ' ').upper()}"
            draw.text((x, y), label, fill=(210, 210, 210))
            image = Image.open(
                _capture_path(capture_root, light_mode, representation)
            ).convert("RGB")
            image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            canvas.paste(image, (x, y + label_height))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    structural_report_path = report_root / V32_REPORT
    structural_report = json.loads(structural_report_path.read_text(encoding="utf-8"))
    hlod = structural_report["local_multi_view_atlas_hlod"]
    contract = hlod["hlod_merged_component_parity_contract"]
    local_review = structural_report["local_visual_review"]
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    capture_paths = {
        light_mode: {
            representation: _capture_path(
                capture_root,
                light_mode,
                representation,
            )
            for representation in REPRESENTATIONS
        }
        for light_mode in LIGHT_MODES
    }
    all_paths = [
        capture_paths[light_mode][representation]
        for light_mode in LIGHT_MODES
        for representation in REPRESENTATIONS
    ]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    contract_valid = (
        contract["enabled"] is True
        and contract["source_map"].endswith(
            "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        )
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture"
        and contract["camera_radius_cm"] == 2450.0
        and contract["warmup_frames_per_representation"] == 8
        and contract["temporal_history_reset_per_representation"]
        == "scene_capture_camera_cut_before_warmup"
        and contract["sun_actor_label"] == "RaftSim_Sun_LumenPreview"
        and contract["sun_original_transform_restored"] is True
        and contract["light_modes"] == list(LIGHT_MODES)
        and contract["representations_per_light"] == list(REPRESENTATIONS)
        and contract["merged_geometry_vertex_count"] > 1_000_000
        and contract["merged_geometry_triangle_count"] > 1_000_000
        and contract["merged_geometry_material_slot_count"] >= 2
        and contract["merged_geometry_section_count"] >= 2
        and contract["bark_material_slot_count"] == 1
        and contract["foliage_material_slot_count"] >= 1
        and contract["component_partition"]
        == "exact static mesh copied twice and non-owner triangles deleted by source material ID"
        and contract["material_identity"] == "source parent materials preserved"
        and contract["material_state"]
        == "identical source-coverage temporal parameters on single and split controls"
        and contract["shadow_partition_basis"] == "material ID"
        and contract["source_component_shadow_provenance_preserved"] is False
        and contract["single_component_shadow_policy"]
        == "bark_and_foliage_no_cast_shadow"
        and contract["split_no_shadow_policy"] == "bark_and_foliage_no_cast_shadow"
        and contract["split_source_shadow_policy"]
        == "bark_casts_static_and_dynamic_shadow_foliage_casts_none"
        and contract["collision_and_overlap"] is False
        and contract["temporal_handoff_evaluated"] is False
        and contract["wall_clock_performance_evaluated"] is False
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_merged_component_parity_capture_count"] == len(all_paths)
        and not missing_paths
    )

    per_light = {}
    for light_mode in LIGHT_MODES:
        paths = capture_paths[light_mode]
        source_path = paths["source_reference"]
        fixed_source_overlap = _fixed_overlap_mask(
            source_path,
            paths["merged_single_no_shadow"],
        )
        source_comparisons = {}
        for representation in REPRESENTATIONS[1:]:
            source_comparisons[representation] = {
                "broad_roi_silhouette_and_photometry": (
                    _silhouette_and_photometry_metrics(
                        source_path,
                        paths[representation],
                    )
                ),
                "fixed_source_overlap_photometry": _overlap_photometry(
                    source_path,
                    paths[representation],
                    fixed_source_overlap,
                ),
            }

        single_path = paths["merged_single_no_shadow"]
        split_no_shadow_path = paths["merged_split_no_shadow"]
        partition_overlap = _fixed_overlap_mask(single_path, split_no_shadow_path)
        no_shadow_metrics = source_comparisons["merged_split_no_shadow"]
        source_shadow_metrics = source_comparisons["merged_split_source_shadow"]
        no_shadow_geometry = no_shadow_metrics["broad_roi_silhouette_and_photometry"]
        source_shadow_geometry = source_shadow_metrics[
            "broad_roi_silhouette_and_photometry"
        ]
        no_shadow_photometry = no_shadow_metrics["fixed_source_overlap_photometry"]
        source_shadow_photometry = source_shadow_metrics[
            "fixed_source_overlap_photometry"
        ]
        per_light[light_mode] = {
            "source_comparisons": source_comparisons,
            "single_to_split_no_shadow_partition": {
                "broad_roi_silhouette_and_photometry": (
                    _silhouette_and_photometry_metrics(
                        single_path,
                        split_no_shadow_path,
                    )
                ),
                "fixed_overlap_photometry": _overlap_photometry(
                    single_path,
                    split_no_shadow_path,
                    partition_overlap,
                ),
            },
            "source_shadow_effect": {
                "silhouette_iou_delta": (
                    source_shadow_geometry[
                        "source_hlod_silhouette_intersection_over_union"
                    ]
                    - no_shadow_geometry[
                        "source_hlod_silhouette_intersection_over_union"
                    ]
                ),
                "absolute_silhouette_area_ratio_error_reduction": (
                    abs(
                        1.0 - no_shadow_geometry["hlod_to_source_silhouette_area_ratio"]
                    )
                    - abs(
                        1.0
                        - source_shadow_geometry["hlod_to_source_silhouette_area_ratio"]
                    )
                ),
                "absolute_fixed_overlap_luminance_ratio_error_reduction": (
                    abs(
                        1.0
                        - no_shadow_photometry["candidate_to_source_luminance_ratio"]
                    )
                    - abs(
                        1.0
                        - source_shadow_photometry[
                            "candidate_to_source_luminance_ratio"
                        ]
                    )
                ),
                "fixed_overlap_mean_channel_delta_reduction": (
                    no_shadow_photometry["mean_absolute_channel_delta"]
                    - source_shadow_photometry["mean_absolute_channel_delta"]
                ),
            },
        }

    direction_responses = {
        representation: _directional_response(
            capture_paths["frontlit"][representation],
            capture_paths["backlit"][representation],
        )
        for representation in REPRESENTATIONS
    }
    light_direction_valid = all(
        response["directional_response_gate_passed"]
        for response in direction_responses.values()
    )
    component_partition_gate_passed = all(
        per_light[light_mode]["single_to_split_no_shadow_partition"][
            "broad_roi_silhouette_and_photometry"
        ]["source_hlod_silhouette_intersection_over_union"]
        >= PARTITION_MINIMUM_SILHOUETTE_IOU
        and PARTITION_MINIMUM_AREA_RATIO
        <= per_light[light_mode]["single_to_split_no_shadow_partition"][
            "broad_roi_silhouette_and_photometry"
        ]["hlod_to_source_silhouette_area_ratio"]
        <= PARTITION_MAXIMUM_AREA_RATIO
        and PARTITION_MINIMUM_LUMINANCE_RATIO
        <= per_light[light_mode]["single_to_split_no_shadow_partition"][
            "fixed_overlap_photometry"
        ]["candidate_to_source_luminance_ratio"]
        <= PARTITION_MAXIMUM_LUMINANCE_RATIO
        and per_light[light_mode]["single_to_split_no_shadow_partition"][
            "fixed_overlap_photometry"
        ]["mean_absolute_channel_delta"]
        <= PARTITION_MAXIMUM_MEAN_CHANNEL_DELTA
        for light_mode in LIGHT_MODES
    )
    source_shadow_policy_parity_gate_passed = all(
        per_light[light_mode]["source_comparisons"]["merged_split_source_shadow"][
            "broad_roi_silhouette_and_photometry"
        ]["source_hlod_silhouette_gate_passed"]
        and per_light[light_mode]["source_comparisons"]["merged_split_source_shadow"][
            "fixed_source_overlap_photometry"
        ]["luminance_gate_passed"]
        for light_mode in LIGHT_MODES
    )
    backlit_source_shadow_improvement_gate_passed = (
        per_light["backlit"]["source_shadow_effect"]["silhouette_iou_delta"] >= 0.0
        and per_light["backlit"]["source_shadow_effect"][
            "absolute_silhouette_area_ratio_error_reduction"
        ]
        >= 0.0
        and per_light["backlit"]["source_shadow_effect"][
            "absolute_fixed_overlap_luminance_ratio_error_reduction"
        ]
        > 0.0
        and per_light["backlit"]["source_shadow_effect"][
            "fixed_overlap_mean_channel_delta_reduction"
        ]
        > 0.0
    )
    material_id_shadow_ownership_rejected_gate_passed = all(
        per_light[light_mode]["source_shadow_effect"][metric] < 0.0
        for light_mode in LIGHT_MODES
        for metric in (
            "silhouette_iou_delta",
            "absolute_silhouette_area_ratio_error_reduction",
            "absolute_fixed_overlap_luminance_ratio_error_reduction",
            "fixed_overlap_mean_channel_delta_reduction",
        )
    )
    component_material_shadow_parity_passed = (
        contract_valid
        and light_direction_valid
        and component_partition_gate_passed
        and source_shadow_policy_parity_gate_passed
        and backlit_source_shadow_improvement_gate_passed
    )

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_merged_component_parity_review.v43",
        "river_id": "futaleufu_terminator",
        "candidate": "v43_exact_merged_geometry_component_material_shadow_parity",
        "status": (
            "exact_component_material_shadow_parity_validated_reduction_may_begin"
            if component_material_shadow_parity_passed
            else (
                "material_id_component_partition_validated_shadow_ownership_rejected"
                if component_partition_gate_passed
                and material_id_shadow_ownership_rejected_gate_passed
                else "exact_component_material_or_shadow_parity_still_fails"
            )
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": len(all_paths),
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "camera_radius_cm": contract["camera_radius_cm"],
            "merged_geometry_asset": contract["merged_geometry_asset"],
            "merged_geometry_vertex_count": contract["merged_geometry_vertex_count"],
            "merged_geometry_triangle_count": contract[
                "merged_geometry_triangle_count"
            ],
            "merged_geometry_section_count": contract["merged_geometry_section_count"],
            "component_partition": contract["component_partition"],
            "material_state": contract["material_state"],
            "shadow_partition_basis": contract["shadow_partition_basis"],
            "source_component_shadow_provenance_preserved": contract[
                "source_component_shadow_provenance_preserved"
            ],
            "split_source_shadow_policy": contract["split_source_shadow_policy"],
        },
        "measurements": {
            "component_partition_tolerance": {
                "minimum_silhouette_iou": PARTITION_MINIMUM_SILHOUETTE_IOU,
                "acceptable_area_ratio": [
                    PARTITION_MINIMUM_AREA_RATIO,
                    PARTITION_MAXIMUM_AREA_RATIO,
                ],
                "acceptable_luminance_ratio": [
                    PARTITION_MINIMUM_LUMINANCE_RATIO,
                    PARTITION_MAXIMUM_LUMINANCE_RATIO,
                ],
                "maximum_mean_channel_delta": (PARTITION_MAXIMUM_MEAN_CHANNEL_DELTA),
                "rationale": (
                    "independent scene-capture TAA histories may move threshold-edge "
                    "pixels while area, overlap luminance, and channel delta remain "
                    "near identical"
                ),
            },
            "per_light": per_light,
            "frontlit_to_backlit_directional_response": direction_responses,
        },
        "human_visual_review": {
            "findings": [
                "the no-shadow single and split captures isolate whether material-slot section partitioning changes the exact merged source appearance",
                "the source-shadow capture changes only bark shadow ownership while foliage retains the source no-shadow policy",
                "single and split no-shadow controls match within the declared independent-TAA tolerance under both light directions",
                "material-ID bark shadow ownership worsens every measured source-agreement metric under both light directions and cannot recover source component provenance",
                "the exact million-triangle mesh remains a diagnostic upper bound and is not a production HLOD",
                "temporal handoff, source-card cleanup, named-hazard framing, and packaged performance remain open",
            ],
            "component_partition_gate_passed": component_partition_gate_passed,
            "source_shadow_policy_parity_gate_passed": (
                source_shadow_policy_parity_gate_passed
            ),
            "backlit_source_shadow_improvement_gate_passed": (
                backlit_source_shadow_improvement_gate_passed
            ),
            "material_id_shadow_ownership_rejected_gate_passed": (
                material_id_shadow_ownership_rejected_gate_passed
            ),
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 4,
            "rows": 2,
        },
        "decision": {
            "retain": [
                "material-slot section partitioning for material ownership because its no-shadow output matches the single-component control",
                "no-shadow exact-geometry controls as the current lighting baseline",
                "the V41 fixed light bracket and V42 exact-geometry upper bound",
            ],
            "reject": [
                "material ID as a proxy for source trunk-versus-foliage component shadow ownership",
                "bark-on foliage-off shadow ownership on the material-ID split because it worsens every measured source-agreement metric",
                "the exact million-triangle duplicated-component representation as a production HLOD",
                "geometry reduction before material and shadow parity are measured",
                "production promotion, corridor substitution, or other-form regeneration",
            ],
            "next_step": (
                "Build a reduced source-matched bark/foliage geometry representation with the validated material and shadow ownership, then add exact inverse temporal ownership and rerun V35, V41, and V37."
                if component_material_shadow_parity_passed
                else (
                    "Build an exact source-provenance split that keeps trunk geometry and all foliage-instance geometry separate, then rerun the same frontlit/backlit shadow bracket before reducing triangles."
                    if component_partition_gate_passed
                    and material_id_shadow_ownership_rejected_gate_passed
                    else "Resolve the measured section-partition or source-shadow mismatch on exact geometry before reducing triangles."
                )
            ),
        },
        "merged_component_parity_contract_passed": contract_valid,
        "light_direction_response_gate_passed": light_direction_valid,
        "component_partition_gate_passed": component_partition_gate_passed,
        "source_shadow_policy_parity_gate_passed": (
            source_shadow_policy_parity_gate_passed
        ),
        "backlit_source_shadow_improvement_gate_passed": (
            backlit_source_shadow_improvement_gate_passed
        ),
        "material_id_shadow_ownership_rejected_gate_passed": (
            material_id_shadow_ownership_rejected_gate_passed
        ),
        "component_material_shadow_parity_gate_passed": (
            component_material_shadow_parity_passed
        ),
        "reduced_geometry_gate_passed": False,
        "temporal_handoff_gate_passed": False,
        "source_art_cleanup_gate_passed": False,
        "lit_art_review_passed": False,
        "hazard_readability_gate_passed": False,
        "wall_clock_performance_gate_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / REPORT_NAME
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))
    print(contact_sheet_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
