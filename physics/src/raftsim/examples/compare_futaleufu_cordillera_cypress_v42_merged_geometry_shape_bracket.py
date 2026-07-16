"""Review the V42 Futaleufu merged-geometry HLOD fidelity upper bound."""

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
    "flat_hlod_control",
    "merged_geometry_hlod",
)
REPORT_NAME = (
    "futaleufu_cordillera_cypress_v42_merged_geometry_shape_bracket_review.json"
)
CONTACT_SHEET_NAME = (
    "futaleufu_cordillera_cypress_v42_merged_geometry_shape_bracket_contact_sheet.png"
)


def _capture_path(capture_root: Path, light_mode: str, representation: str) -> Path:
    return capture_root / (
        "open_grown_conical_hlod_merged_geometry_shape_bracket_"
        f"{light_mode}_{representation}.png"
    )


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    columns = 3
    rows = 2
    thumb_width = 320
    thumb_height = 180
    margin = 16
    title_height = 48
    label_height = 24
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
        "V42 MERGED GEOMETRY HLOD - FIDELITY UPPER BOUND, NOT PRODUCTION COST",
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
    contract = hlod["hlod_merged_geometry_shape_bracket_contract"]
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
        and contract["geometry_materials"] == "preserved_source_bark_and_foliage"
        and contract["geometry_shadow_policy"]
        == "no_cast_shadow_for_bounded_shape_and_direct-light_upper-bound"
        and contract["collision_and_overlap"] is False
        and contract["temporal_handoff_evaluated"] is False
        and contract["wall_clock_performance_evaluated"] is False
        and contract["merged_geometry_vertex_count"] > 1_000_000
        and contract["merged_geometry_triangle_count"] > 1_000_000
        and contract["merged_geometry_material_slot_count"] >= 2
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_merged_geometry_shape_bracket_capture_count"]
        == len(all_paths)
        and not missing_paths
    )

    per_light = {}
    for light_mode in LIGHT_MODES:
        paths = capture_paths[light_mode]
        source_path = paths["source_reference"]
        flat_path = paths["flat_hlod_control"]
        geometry_path = paths["merged_geometry_hlod"]
        overlap = _fixed_overlap_mask(source_path, flat_path)
        flat_geometry = _silhouette_and_photometry_metrics(source_path, flat_path)
        merged_geometry = _silhouette_and_photometry_metrics(
            source_path,
            geometry_path,
        )
        flat_overlap = _overlap_photometry(source_path, flat_path, overlap)
        merged_overlap = _overlap_photometry(source_path, geometry_path, overlap)
        per_light[light_mode] = {
            "flat_hlod_control": {
                "broad_roi_silhouette_and_photometry": flat_geometry,
                "fixed_overlap_photometry": flat_overlap,
            },
            "merged_geometry_hlod": {
                "broad_roi_silhouette_and_photometry": merged_geometry,
                "fixed_overlap_photometry": merged_overlap,
            },
            "merged_geometry_improvement_over_flat": {
                "silhouette_iou_delta": (
                    merged_geometry["source_hlod_silhouette_intersection_over_union"]
                    - flat_geometry["source_hlod_silhouette_intersection_over_union"]
                ),
                "absolute_silhouette_area_ratio_error_reduction": (
                    abs(1.0 - flat_geometry["hlod_to_source_silhouette_area_ratio"])
                    - abs(1.0 - merged_geometry["hlod_to_source_silhouette_area_ratio"])
                ),
                "absolute_fixed_overlap_luminance_ratio_error_reduction": (
                    abs(1.0 - flat_overlap["candidate_to_source_luminance_ratio"])
                    - abs(1.0 - merged_overlap["candidate_to_source_luminance_ratio"])
                ),
                "fixed_overlap_mean_channel_delta_reduction": (
                    flat_overlap["mean_absolute_channel_delta"]
                    - merged_overlap["mean_absolute_channel_delta"]
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
    merged_geometry_shape_gate_passed = all(
        per_light[light_mode]["merged_geometry_hlod"][
            "broad_roi_silhouette_and_photometry"
        ]["source_hlod_silhouette_gate_passed"]
        for light_mode in LIGHT_MODES
    )
    merged_geometry_photometry_gate_passed = all(
        per_light[light_mode]["merged_geometry_hlod"]["fixed_overlap_photometry"][
            "luminance_gate_passed"
        ]
        for light_mode in LIGHT_MODES
    )
    merged_geometry_improves_flat = all(
        per_light[light_mode]["merged_geometry_improvement_over_flat"][
            "silhouette_iou_delta"
        ]
        > 0.0
        and per_light[light_mode]["merged_geometry_improvement_over_flat"][
            "absolute_fixed_overlap_luminance_ratio_error_reduction"
        ]
        > 0.0
        for light_mode in LIGHT_MODES
    )
    fidelity_upper_bound_passed = (
        contract_valid
        and light_direction_valid
        and merged_geometry_shape_gate_passed
        and merged_geometry_photometry_gate_passed
        and merged_geometry_improves_flat
    )

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_merged_geometry_shape_bracket_review.v42",
        "river_id": "futaleufu_terminator",
        "candidate": "v42_merged_source_geometry_hlod_fidelity_upper_bound",
        "status": (
            "merged_geometry_closes_shape_and_lighting_upper_bound_performance_and_source_art_open"
            if fidelity_upper_bound_passed
            else "merged_geometry_upper_bound_still_fails_shape_or_lighting"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 6,
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
            "merged_geometry_material_slot_count": contract[
                "merged_geometry_material_slot_count"
            ],
            "geometry_shadow_policy": contract["geometry_shadow_policy"],
        },
        "measurements": {
            "per_light": per_light,
            "frontlit_to_backlit_directional_response": direction_responses,
        },
        "human_visual_review": {
            "findings": [
                "the merged mesh is the exact V32 source assembly collapsed into one static mesh with source bark and foliage materials preserved",
                "the comparison isolates representation geometry under the same 24.5 m camera and frontlit/backlit bracket used for V41",
                "the merged mesh disables cast shadows because one component cannot reproduce the source trunk-on and foliage-off shadow split",
                "the million-triangle merged mesh is a fidelity upper bound and has no production performance evidence",
                "source whole-spray cards and the regular scaffold remain visible and require separate source-art cleanup",
                "no named rapid or boat line is framed by this representation diagnostic",
            ],
            "light_direction_bracket_passed": light_direction_valid,
            "merged_geometry_shape_gate_passed": merged_geometry_shape_gate_passed,
            "merged_geometry_photometry_gate_passed": (
                merged_geometry_photometry_gate_passed
            ),
            "merged_geometry_improves_flat": merged_geometry_improves_flat,
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 3,
            "rows": 2,
        },
        "decision": {
            "retain": [
                "the merged source geometry as a bounded shape and direct-light fidelity upper bound",
                "the V41 fixed frontlit/backlit physical-corridor bracket",
                "source bark and foliage material identity for reduced-geometry design targets",
            ],
            "reject": [
                "the million-triangle merged source mesh as a production HLOD",
                "this fixed bracket as temporal handoff or wall-clock performance evidence",
                "corridor substitution, other-form regeneration, or production promotion",
                "this diagnostic as source-art or named-hazard approval",
            ],
            "next_step": (
                "Use the measured upper bound to design a reduced source-matched geometry HLOD, then add inverse temporal ownership and rerun the V35 temporal, V41 light, and V37 lit physical-corridor guards before packaged desktop and target-VR profiling."
                if fidelity_upper_bound_passed
                else "Diagnose merged-mesh transform, material, and shadow-policy mismatches before reducing geometry or retuning atlas materials."
            ),
        },
        "merged_geometry_shape_bracket_contract_passed": contract_valid,
        "light_direction_response_gate_passed": light_direction_valid,
        "merged_geometry_shape_gate_passed": merged_geometry_shape_gate_passed,
        "merged_geometry_photometry_gate_passed": (
            merged_geometry_photometry_gate_passed
        ),
        "merged_geometry_improves_flat_gate_passed": merged_geometry_improves_flat,
        "fidelity_upper_bound_gate_passed": fidelity_upper_bound_passed,
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
