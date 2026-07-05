"""Milestone 21 Unreal river editor and content-pipeline artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .feature_forcing import FEATURE_FORCING_KINDS

MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA = "raftsim.unreal.rapid_river_editor.v1"
MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA = (
    "raftsim.unreal.geospatial_import_pipeline.v1"
)
MILESTONE21_REACH_LOCAL_STREAMING_SCHEMA = "raftsim.unreal.reach_local_streaming.v1"
MILESTONE21_FEATURE_TUNING_EDITOR_SCHEMA = "raftsim.unreal.feature_tuning_editor.v1"
RAPID_RIVER_EDITOR_MANIFEST_PATH = "unreal/Content/RaftSim/River/rapid_river_editor.json"
GEOSPATIAL_IMPORT_PIPELINE_PATH = "unreal/Content/RaftSim/River/geospatial_import_pipeline.json"
REACH_LOCAL_STREAMING_PATH = "unreal/Content/RaftSim/River/reach_local_streaming.json"
FEATURE_TUNING_EDITOR_PATH = "unreal/Content/RaftSim/River/feature_tuning_editor.json"
FEATURE_FORCING_DEFAULTS_PATH = "physics/config/feature_forcing_defaults.json"
RAPID_REVIEW_FLOW_DIFFICULTY_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/rapid_review_flow_difficulty_mapping.json"
)
FLOW_PRESETS_PATH = "physics/data/real_world/south_fork_american_chili_bar/flow_presets.json"
SPATIAL_AUDIO_PRESETS_PATH = "unreal/Content/RaftSim/Audio/spatial_audio_presets.json"
SOUTH_FORK_WORKFLOW_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/rapid_review_editor_workflow.json"
)
TRACEABLE_RIVER_DATA_ASSETS_PATH = "unreal/Content/RaftSim/River/traceable_river_data_assets.json"
GEOSPATIAL_FORMAT_CONTRACT_PATH = "physics/config/geospatial_format_contract.json"
SOUTH_FORK_SOURCE_MANIFEST_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/source_manifest.json"
)
SOUTH_FORK_CORRIDOR_PACKAGE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json"
)

GEOMETRY_KINDS = ("station_pin", "reach_span", "drop_span", "polygon", "raft_line")
EXPECTED_OUTCOMES = ("surf", "flush", "pin", "release", "flip")
REQUIRED_EVIDENCE_LAYERS = (
    "dem_lidar",
    "aerial_satellite_imagery",
    "flowlines",
    "cross_sections",
    "gauge_history",
    "source_manifest",
    "candidate_tags",
    "guide_notes",
)
FEATURE_REVIEW_LABELS = {
    "hole": "hole",
    "boil": "hole",
    "lateral": "lateral",
    "eddy_line": "eddy_line",
    "wave_train": "wave_train",
    "shallow_shelf": "boulder_garden",
    "boulder_push_damping": "boulder_garden",
    "pin_release": "boulder_garden",
    "flip": "lateral",
}
FEATURE_DISPLAY_NAMES = {
    "hole": "Hole Retention And Washout",
    "boil": "Boil And Upwelling",
    "lateral": "Lateral Wave Push",
    "eddy_line": "Eddy-Line Shear",
    "wave_train": "Wave Train",
    "shallow_shelf": "Shallow Shelf",
    "boulder_push_damping": "Boulder Push And Damping",
    "pin_release": "Pin And Release",
    "flip": "Flip And High-Side Counterplay",
}


@dataclass(frozen=True, slots=True)
class Milestone21RapidRiverEditor:
    """Generated Unreal rapid/river editor manifest."""

    manifest: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Milestone21GeospatialImportPipeline:
    """Generated Unreal geospatial import pipeline manifest."""

    manifest: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Milestone21ReachLocalStreaming:
    """Generated Unreal reach-local authoring and streaming manifest."""

    manifest: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Milestone21FeatureTuningEditor:
    """Generated Unreal feature-tuning editor manifest."""

    manifest: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_paths(base_dir: str, paths: list[str]) -> list[str]:
    return [f"{base_dir}/{path}" for path in paths]


def _annotation_template(template_id: str, geometry_kind: str, required_fields: list[str]) -> dict[str, Any]:
    return {
        "template_id": template_id,
        "geometry_kind": geometry_kind,
        "required_fields": required_fields,
        "expected_outcomes": list(EXPECTED_OUTCOMES),
        "requires_rights_provenance": True,
        "requires_confidence": True,
    }


def _seed_annotation(review_item: dict[str, Any]) -> dict[str, Any]:
    evidence_refs = review_item["evidence_refs"]
    raw_span = review_item["station_range_m"]
    span_start = float(raw_span.get("start", review_item["peak_station_m"]))
    span_end = float(raw_span.get("end", review_item["peak_station_m"]))
    if span_start == span_end:
        span_start -= 25.0
        span_end += 25.0
    return {
        "annotation_id": f"unreal_seed_{review_item['rapid_id']}",
        "rapid_id": review_item["rapid_id"],
        "station_pin": {
            "station_m": review_item["peak_station_m"],
            "wgs84": review_item["map_focus_wgs84"],
        },
        "station_span_m": [span_start, span_end],
        "polygon_layers": [
            "hazard_polygon",
            "eddy_polygon",
            "whitewater_polygon",
            "bank_polygon",
        ],
        "raft_line_roles": ["entry_line", "main_current_line", "recovery_line"],
        "footage_timecodes": {
            "required": True,
            "source_layers": ["guide_notes", "field_media"],
            "fields": ["media_id", "start_timecode", "end_timecode", "flow_band", "rights_status"],
        },
        "gauge_history_snippets": evidence_refs["gauge_history"]["artifacts"],
        "aerial_imagery_references": evidence_refs["aerial_satellite_imagery"]["artifacts"],
        "guide_notes": review_item["guide_notes"],
        "expected_outcome_review": [
            {
                "outcome": outcome,
                "flow_band_required": True,
                "line_specific": True,
                "confidence_required": True,
            }
            for outcome in EXPECTED_OUTCOMES
        ],
        "confidence": round(float(review_item["confidence"]), 6),
        "rights_provenance": {
            "required": True,
            "source_manifest": evidence_refs["source_manifest"]["artifacts"][0],
            "source_ids": sorted(
                {
                    source_id
                    for ref in evidence_refs.values()
                    for source_id in ref.get("source_ids", [])
                }
            ),
            "fields": [
                "source_id",
                "license_or_terms",
                "attribution",
                "permission_status",
                "reviewer",
                "review_date",
            ],
        },
    }


def build_rapid_river_editor_manifest(repo_root: Path) -> Milestone21RapidRiverEditor:
    """Build the first Unreal rapid/river editor manifest."""

    root = repo_root.resolve()
    workflow = _read_json(root / SOUTH_FORK_WORKFLOW_PATH)
    traceable_assets = _read_json(root / TRACEABLE_RIVER_DATA_ASSETS_PATH)
    review_items = workflow["review_items"]

    manifest = {
        "schema": MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA,
        "editor_id": "milestone21_unreal_rapid_river_editor",
        "module": "RaftSimRiver",
        "asset_class": "URaftSimRapidRiverEditorConfig",
        "source_workflow": SOUTH_FORK_WORKFLOW_PATH,
        "traceable_river_data_assets": TRACEABLE_RIVER_DATA_ASSETS_PATH,
        "accepted_report_set_lock": traceable_assets["accepted_report_set_lock"],
        "river_id": workflow["river_id"],
        "section_id": workflow["section_id"],
        "geometry_kinds": list(GEOMETRY_KINDS),
        "required_evidence_layers": list(REQUIRED_EVIDENCE_LAYERS),
        "editable_metadata_fields": [
            "footage_timecodes",
            "gauge_history_snippets",
            "aerial_imagery_references",
            "guide_notes",
            "confidence",
            "rights_provenance",
            "expected_outcomes",
        ],
        "expected_outcomes": list(EXPECTED_OUTCOMES),
        "annotation_templates": [
            _annotation_template(
                "station_pin",
                "station_pin",
                ["station_m", "wgs84", "review_labels", "confidence", "rights_provenance"],
            ),
            _annotation_template(
                "reach_drop_span",
                "reach_span",
                ["station_range_m", "reach_id", "drop_id", "expected_outcomes"],
            ),
            _annotation_template(
                "polygon",
                "polygon",
                ["polygon_role", "vertices_wgs84", "source_layer", "rights_provenance"],
            ),
            _annotation_template(
                "raft_line",
                "raft_line",
                ["line_role", "polyline_wgs84", "flow_band", "expected_outcomes"],
            ),
        ],
        "editor_panels": [panel["panel_id"] for panel in workflow["panels"]],
        "quality_gates": [
            *workflow["quality_gates"],
            "Expected surf/flush/pin/release/flip outcomes must be recorded per flow band before annotations can tune gameplay.",
        ],
        "export_targets": {
            "json": "unreal/Content/RaftSim/River/rapid_river_editor.json",
            "geojson": workflow["save_targets"],
            "python_scenario_generation": "physics/data/real_world/south_fork_american_chili_bar",
            "unreal_data_assets": "unreal/Content/RaftSim/River/traceable_river_data_assets.json",
        },
        "seed_annotations": [_seed_annotation(item) for item in review_items],
        "status": "ready_for_unreal_editor_widget_and_data_asset_authoring",
    }
    return Milestone21RapidRiverEditor(manifest=manifest)


def write_rapid_river_editor_manifest(*, repo_root: Path, output_json: Path) -> Milestone21RapidRiverEditor:
    """Generate and write the Unreal rapid/river editor manifest."""

    generated = build_rapid_river_editor_manifest(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return generated


def _format_contract_by_category(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["category"]: item for item in contract["canonical_formats"]}


def _import_stage(
    *,
    stage_id: str,
    category: str,
    contract: dict[str, Any],
    source_paths: list[str],
    unreal_conversion_target: str,
    seed_status: str = "available_in_seed_manifest",
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "category": category,
        "canonical_formats": contract["formats"],
        "required_metadata": contract["required_metadata"],
        "source_paths": source_paths,
        "unreal_conversion_target": unreal_conversion_target,
        "seed_status": seed_status,
        "requires_crs": "crs" in contract["required_metadata"],
        "requires_source_manifest": "source_manifest" in contract["required_metadata"],
    }


def build_geospatial_import_pipeline_manifest(
    repo_root: Path,
) -> Milestone21GeospatialImportPipeline:
    """Build the canonical Unreal geospatial import pipeline manifest."""

    root = repo_root.resolve()
    contract = _read_json(root / GEOSPATIAL_FORMAT_CONTRACT_PATH)
    formats = _format_contract_by_category(contract)
    source_manifest = _read_json(root / SOUTH_FORK_SOURCE_MANIFEST_PATH)
    corridor_package = _read_json(root / SOUTH_FORK_CORRIDOR_PACKAGE_PATH)
    base_dir = "physics/data/real_world/south_fork_american_chili_bar"
    artifacts = source_manifest["artifacts"]
    unreal_ready = corridor_package["unreal_ready_artifacts"]

    stages = [
        _import_stage(
            stage_id="source_manifest_json",
            category="source_manifests",
            contract=formats["source_manifests"],
            source_paths=[SOUTH_FORK_SOURCE_MANIFEST_PATH],
            unreal_conversion_target="URaftSimTraceableRiverDataAsset.source_manifest",
        ),
        _import_stage(
            stage_id="vectors_annotations_geojson_geopackage",
            category="vectors_annotations",
            contract=formats["vectors_annotations"],
            source_paths=[
                *_repo_paths(base_dir, artifacts["hydrography"]),
                f"{base_dir}/rapid_candidates.geojson",
                f"{base_dir}/{unreal_ready['rapids']}",
            ],
            unreal_conversion_target="river splines, banks, rapid polygons, validation annotation layers",
        ),
        _import_stage(
            stage_id="rasters_geotiff_cog",
            category="rasters",
            contract=formats["rasters"],
            source_paths=_repo_paths(base_dir, artifacts["imagery"]),
            unreal_conversion_target="landscape height/mask tiles, water masks, foam confidence masks",
        ),
        _import_stage(
            stage_id="point_clouds_las_laz_copc",
            category="point_clouds",
            contract=formats["point_clouds"],
            source_paths=[],
            unreal_conversion_target="optional high-detail rocks, banks, undercuts, and 3D Tiles source meshes",
            seed_status="planned_not_vendored_in_south_fork_seed",
        ),
        _import_stage(
            stage_id="gauge_history_tables",
            category="gauge_history",
            contract=formats["gauge_history"],
            source_paths=_repo_paths(base_dir, artifacts["gauges"]),
            unreal_conversion_target="flow-band presets, hydrograph snippets, editor review panels",
        ),
        _import_stage(
            stage_id="solver_arrays",
            category="solver_packages",
            contract=formats["solver_packages"],
            source_paths=_repo_paths(base_dir, artifacts["solver"]),
            unreal_conversion_target="custom water runtime scenario packages and validation overlays",
        ),
        _import_stage(
            stage_id="converted_unreal_corridor_assets",
            category="unreal_corridor_exports",
            contract=formats["unreal_corridor_exports"],
            source_paths=[
                SOUTH_FORK_CORRIDOR_PACKAGE_PATH,
                TRACEABLE_RIVER_DATA_ASSETS_PATH,
                RAPID_RIVER_EDITOR_MANIFEST_PATH,
            ],
            unreal_conversion_target="World Partition corridor package, data assets, splines, masks, and review overlays",
        ),
    ]

    manifest = {
        "schema": MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA,
        "pipeline_id": "milestone21_canonical_geospatial_import",
        "module": "RaftSimGeo",
        "asset_class": "URaftSimGeospatialImportPipelineConfig",
        "format_contract": GEOSPATIAL_FORMAT_CONTRACT_PATH,
        "source_manifest": SOUTH_FORK_SOURCE_MANIFEST_PATH,
        "corridor_package": SOUTH_FORK_CORRIDOR_PACKAGE_PATH,
        "traceable_river_data_assets": TRACEABLE_RIVER_DATA_ASSETS_PATH,
        "rapid_river_editor": RAPID_RIVER_EDITOR_MANIFEST_PATH,
        "crs_policy": contract["crs_policy"],
        "transform_policy": contract["transform_policy"],
        "shapefile_canonical_allowed": contract["shapefile_canonical_allowed"],
        "source_manifest_required": contract["source_manifest_required"],
        "import_stages": stages,
        "round_trip_targets": [
            "solver_neutral_scenario_package",
            "geoclaw_cpp_comparison_inputs",
            "unreal_fidelity_review_overlays",
        ],
        "status": "ready_for_unreal_geospatial_import_tooling",
    }
    return Milestone21GeospatialImportPipeline(manifest=manifest)


def write_geospatial_import_pipeline_manifest(
    *, repo_root: Path, output_json: Path
) -> Milestone21GeospatialImportPipeline:
    """Generate and write the canonical Unreal geospatial import pipeline manifest."""

    generated = build_geospatial_import_pipeline_manifest(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return generated


def _reach_adjacency(reach_ids: list[str]) -> list[dict[str, Any]]:
    adjacency: list[dict[str, Any]] = []
    for index, reach_id in enumerate(reach_ids):
        adjacency.append(
            {
                "reach_id": reach_id,
                "upstream_neighbor": reach_ids[index - 1] if index > 0 else None,
                "downstream_neighbor": reach_ids[index + 1] if index + 1 < len(reach_ids) else None,
            }
        )
    return adjacency


def _playable_window(asset: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    cascading_metadata = _read_json(repo_root / asset["ghost_zone_policy"]["source"])
    stitched_manifest = _read_json(repo_root / asset["stitched_validation"]["manifest"])
    reach_ids = list(asset["reach_ids"])
    return {
        "window_id": asset["asset_id"],
        "display_name": asset["display_name"],
        "flow_band": asset["flow_band"],
        "solver_mode": asset["solver_mode"],
        "scenario_package": asset["scenario_package"],
        "authoring_mode": "reach_local_grids",
        "streaming_mode": "reach_window_with_overlap_ghost_zones",
        "reach_ids": reach_ids,
        "reach_adjacency": _reach_adjacency(reach_ids),
        "reach_local_grid_count": asset["reach_local_grid_count"],
        "reach_local_grids": [
            {
                "reach_id": grid["reach_id"],
                "grid": grid["grid"],
                "upstream_ghost_cells": grid["upstream_ghost_cells"],
                "downstream_ghost_cells": grid["downstream_ghost_cells"],
            }
            for grid in cascading_metadata["reach_local_grids"]
        ],
        "ghost_zone_policy": asset["ghost_zone_policy"],
        "stitched_validation": asset["stitched_validation"],
        "stitched_validation_scope": stitched_manifest["validation_scope"],
        "required_exports": {
            "fields": asset["stitched_validation"]["fields"],
            "probes": asset["stitched_validation"]["probes"],
            "conservation_summary": asset["stitched_validation"]["conservation_summary"],
            "raft_transition_checkpoints": asset["stitched_validation"]["raft_transition_checkpoints"],
            "manifest": asset["stitched_validation"]["manifest"],
        },
        "streaming_contract": {
            "overlap_metadata_required": True,
            "neighbor_references_required": True,
            "stitched_whole_window_validation_required": True,
            "isolated_reach_validation_allowed_for_signoff": False,
        },
    }


def build_reach_local_streaming_manifest(repo_root: Path) -> Milestone21ReachLocalStreaming:
    """Build the Unreal reach-local authoring and streaming manifest."""

    root = repo_root.resolve()
    traceable_assets = _read_json(root / TRACEABLE_RIVER_DATA_ASSETS_PATH)
    reach_assets = [
        asset
        for asset in traceable_assets["data_assets"]
        if asset["kind"] == "reach_local_grid_with_stitched_validation"
    ]
    windows = [_playable_window(asset, root) for asset in reach_assets]
    manifest = {
        "schema": MILESTONE21_REACH_LOCAL_STREAMING_SCHEMA,
        "streaming_id": "milestone21_reach_local_authoring_streaming",
        "module": "RaftSimRiver",
        "asset_class": "URaftSimReachLocalStreamingConfig",
        "traceable_river_data_assets": TRACEABLE_RIVER_DATA_ASSETS_PATH,
        "accepted_report_set_lock": traceable_assets["accepted_report_set_lock"],
        "playable_window_count": len(windows),
        "playable_windows": windows,
        "authoring_rules": [
            "Designers may author and stream reach-local grids for ergonomics and memory.",
            "Every playable window must export stitched whole-window fields, probes, conservation summaries, and raft transition checkpoints.",
            "Seam, ghost-zone, bed-slope, wet/dry, and raft-state checks are evaluated on stitched outputs for signoff.",
        ],
        "status": "ready_for_reach_local_unreal_authoring_and_streaming",
    }
    return Milestone21ReachLocalStreaming(manifest=manifest)


def write_reach_local_streaming_manifest(
    *, repo_root: Path, output_json: Path
) -> Milestone21ReachLocalStreaming:
    """Generate and write the Unreal reach-local streaming manifest."""

    generated = build_reach_local_streaming_manifest(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return generated


def _feature_curve_index(feature_defaults: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {curve["curve_id"]: curve for curve in feature_defaults["flow_response_curves"]}


def _review_response_index(review_mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["label"]: entry for entry in review_mapping["label_flow_responses"]}


def _flow_response_by_band(review_entry: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not review_entry:
        return {}
    return {response["flow_band"]: response for response in review_entry["flow_responses"]}


def _flow_band_samples(
    *,
    family: dict[str, Any],
    curve: dict[str, Any],
    flow_bands: list[dict[str, Any]],
    review_entry: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    points = curve["points"]
    review_by_band = _flow_response_by_band(review_entry)
    samples: list[dict[str, Any]] = []
    for index, flow_band in enumerate(flow_bands):
        point = points[min(index, len(points) - 1)]
        review_point = review_by_band.get(flow_band["flow_band"], {})
        gain_multiplier = float(point["gain_multiplier"])
        activation_scale = float(review_point.get("activation_scale", 1.0))
        samples.append(
            {
                "flow_band": flow_band["flow_band"],
                "season": flow_band["season"],
                "discharge_cfs": float(flow_band["discharge_cfs"]),
                "discharge_m3s": float(flow_band["discharge_m3s"]),
                "flow_percentile_range": flow_band["percentile_range"],
                "curve_flow_band": point["flow_band"],
                "gain_multiplier": round(gain_multiplier, 6),
                "south_fork_activation_scale": round(activation_scale, 6),
                "effective_default_gain": round(float(family["default_gain"]) * gain_multiplier * activation_scale, 6),
                "review_priority": review_point.get("review_priority", "medium"),
                "expected_behavior": review_point.get("expected_behavior", point["outcome_note"]),
                "outcome_note": point["outcome_note"],
            }
        )
    return samples


def _hole_stickiness_washout_curve(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    washout_by_curve_band = {
        "too_low": 0.1,
        "sticky": 0.05,
        "washout": 0.85,
    }
    curve: list[dict[str, Any]] = []
    for sample in samples:
        curve_band = str(sample["curve_flow_band"])
        curve.append(
            {
                "flow_band": sample["flow_band"],
                "discharge_cfs": sample["discharge_cfs"],
                "curve_flow_band": curve_band,
                "stickiness_factor": sample["gain_multiplier"],
                "washout_factor": washout_by_curve_band.get(curve_band, 0.0),
                "expected_behavior": sample["expected_behavior"],
            }
        )
    return curve


def _audio_parameter_defaults(kind: str, visual_only_parameters: dict[str, Any]) -> dict[str, float]:
    audio_parameters = {
        key: float(value)
        for key, value in visual_only_parameters.items()
        if "audio" in key or "callout" in key
    }
    if audio_parameters:
        return audio_parameters
    return {f"{kind}_audio_intensity_default": 0.05}


def _specialized_feature_parameters(kind: str) -> list[str]:
    extra_by_kind = {
        "hole": [
            "hole_stickiness_factor",
            "hole_washout_factor",
            "surf_flush_window_modifier",
        ],
        "boil": ["boil_upwelling_scale", "boil_surface_pulse_rate"],
        "lateral": ["lateral_push_scale", "brace_timing_window_s"],
        "eddy_line": ["eddy_line_shear_width_m", "crossing_grab_modifier"],
        "wave_train": ["wave_train_spacing_m", "crest_lift_scale"],
        "shallow_shelf": ["shelf_grounding_depth_m", "pivot_release_modifier"],
        "boulder_push_damping": ["boulder_push_scale", "boulder_damping_scale"],
        "pin_release": [
            "pin_load_threshold_n",
            "release_impulse_threshold_n_s",
            "crew_weight_distribution_scale",
            "high_side_timing_window_s",
        ],
        "flip": [
            "roll_impulse_threshold_n_m_s",
            "high_side_counterplay_window_s",
            "crew_weight_distribution_scale",
        ],
    }
    return extra_by_kind.get(kind, [])


def _feature_tuning_group(
    *,
    family: dict[str, Any],
    flow_bands: list[dict[str, Any]],
    curves: dict[str, dict[str, Any]],
    review_responses: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    kind = family["kind"]
    review_label = FEATURE_REVIEW_LABELS[kind]
    review_entry = review_responses.get(review_label)
    samples = _flow_band_samples(
        family=family,
        curve=curves[family["flow_response_curve_id"]],
        flow_bands=flow_bands,
        review_entry=review_entry,
    )
    visual_only_parameters = family["visual_only_parameters"]
    audio_only_parameters = _audio_parameter_defaults(kind, visual_only_parameters)
    review_parameters = review_entry.get("tuning_parameters", []) if review_entry else []
    tunable_parameters = sorted(
        {
            "default_gain",
            "gain_bounds",
            "flow_response_curve",
            *review_parameters,
            *visual_only_parameters,
            *audio_only_parameters,
            *_specialized_feature_parameters(kind),
        }
    )
    return {
        "feature_kind": kind,
        "display_name": FEATURE_DISPLAY_NAMES[kind],
        "review_label": review_label,
        "review_category": review_entry.get("category") if review_entry else None,
        "expected_raft_outcomes": review_entry.get("expected_raft_outcomes", []) if review_entry else [],
        "enabled_by_default": family["enabled_by_default"],
        "default_gain": family["default_gain"],
        "gain_bounds": family["gain_bounds"],
        "flow_response_curve_id": family["flow_response_curve_id"],
        "flow_response_samples": samples,
        "hole_stickiness_washout_curve": _hole_stickiness_washout_curve(samples) if kind == "hole" else [],
        "editor_domains": ["solver_state", "raft_coupling", "visual_only", "audio_only"],
        "solver_state_effects": family["solver_state_effects"],
        "raft_coupling_effects": family["raft_coupling_effects"],
        "visual_only_parameters": visual_only_parameters,
        "audio_only_parameters": audio_only_parameters,
        "tunable_parameters": tunable_parameters,
        "manifest_recording": {
            "required": True,
            "record_targets": [
                "scenario/features.json",
                "unreal/Content/RaftSim/River/feature_tuning_editor.json",
                "deterministic_run_capture_manifest",
            ],
            "fields": [
                "feature_kind",
                "flow_band",
                "discharge_cfs",
                "gain",
                "gain_bounds",
                "curve_id",
                "editor_user",
                "source_annotation_id",
                "geoclaw_comparison_id",
                "conservation_summary_id",
            ],
        },
        "validation_contract": {
            "bounded": True,
            "manifest_recorded": True,
            "geoclaw_compared": True,
            "flow_dependent": True,
            "conservation_guard_required": True,
            "hide_conservation_failures": False,
            "real_world_annotation_allowed": family["validation_evidence"]["real_world_annotation_allowed"],
        },
    }


def _visual_audio_only_controls(feature_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in feature_groups:
        for domain, parameters in (
            ("visual_only", group["visual_only_parameters"]),
            ("audio_only", group["audio_only_parameters"]),
        ):
            for parameter, default_value in parameters.items():
                control_id = f"{group['feature_kind']}.{parameter}"
                if control_id in seen:
                    continue
                seen.add(control_id)
                controls.append(
                    {
                        "control_id": control_id,
                        "feature_kind": group["feature_kind"],
                        "domain": domain,
                        "default_value": float(default_value),
                        "effective_on_solver_state": False,
                        "effective_on_raft_coupling": False,
                        "manifest_recording_required": True,
                    }
                )
    return controls


def build_feature_tuning_editor_manifest(repo_root: Path) -> Milestone21FeatureTuningEditor:
    """Build the Unreal feature-tuning editor manifest."""

    root = repo_root.resolve()
    feature_defaults = _read_json(root / FEATURE_FORCING_DEFAULTS_PATH)
    flow_presets = _read_json(root / FLOW_PRESETS_PATH)
    review_mapping = _read_json(root / RAPID_REVIEW_FLOW_DIFFICULTY_PATH)
    traceable_assets = _read_json(root / TRACEABLE_RIVER_DATA_ASSETS_PATH)
    curves = _feature_curve_index(feature_defaults)
    review_responses = _review_response_index(review_mapping)
    flow_bands = flow_presets["flow_bands"]
    feature_groups = [
        _feature_tuning_group(
            family=family,
            flow_bands=flow_bands,
            curves=curves,
            review_responses=review_responses,
        )
        for family in feature_defaults["feature_families"]
    ]

    manifest = {
        "schema": MILESTONE21_FEATURE_TUNING_EDITOR_SCHEMA,
        "tuning_id": "milestone21_feature_tuning_editor",
        "module": "RaftSimRiver",
        "asset_class": "URaftSimFeatureTuningEditorConfig",
        "feature_forcing_defaults": FEATURE_FORCING_DEFAULTS_PATH,
        "flow_presets": FLOW_PRESETS_PATH,
        "rapid_review_flow_difficulty_mapping": RAPID_REVIEW_FLOW_DIFFICULTY_PATH,
        "rapid_river_editor": RAPID_RIVER_EDITOR_MANIFEST_PATH,
        "reach_local_streaming": REACH_LOCAL_STREAMING_PATH,
        "spatial_audio_presets": SPATIAL_AUDIO_PRESETS_PATH,
        "accepted_report_set_lock": traceable_assets["accepted_report_set_lock"],
        "runtime_posture": {
            "feature_forcing_enabled_by_default": feature_defaults["defaults"]["enabled_by_default"],
            "global_gain_scale": feature_defaults["defaults"]["global_gain_scale"],
            "max_default_gain": feature_defaults["defaults"]["max_default_gain"],
            "keep_default_gains_low": True,
            "physics_gameplay_visual_separated": True,
        },
        "validation_requirements": {
            **feature_defaults["validation_requirements"],
            "conservation_guard_required": True,
            "force_only_after_water_field_acceptance": True,
        },
        "flow_bands": flow_bands,
        "feature_tuning_groups": feature_groups,
        "visual_audio_only_controls": _visual_audio_only_controls(feature_groups),
        "editor_panels": [
            "flow_band_curve_editor",
            "feature_gain_bounds",
            "hole_stickiness_washout",
            "eddy_lateral_wave_train_tuning",
            "boulder_shelf_pin_release_tuning",
            "visual_audio_only_tuning",
            "manifest_recording_and_validation",
        ],
        "export_rules": {
            "manifest_record_every_edit": True,
            "reject_unbounded_gain": True,
            "require_geoclaw_comparison_before_signoff": True,
            "reject_conservation_failure_masking": True,
            "visual_audio_only_cannot_change_solver_state": True,
        },
        "status": "ready_for_unreal_feature_tuning_data_asset",
    }
    return Milestone21FeatureTuningEditor(manifest=manifest)


def write_feature_tuning_editor_manifest(
    *, repo_root: Path, output_json: Path
) -> Milestone21FeatureTuningEditor:
    """Generate and write the Unreal feature-tuning editor manifest."""

    generated = build_feature_tuning_editor_manifest(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return generated
