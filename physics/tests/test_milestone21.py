import json
from pathlib import Path

from raftsim.feature_forcing import FEATURE_FORCING_KINDS
from raftsim.milestone21 import (
    EXPECTED_OUTCOMES,
    FEATURE_FORCING_DEFAULTS_PATH,
    FEATURE_TUNING_EDITOR_PATH as FEATURE_TUNING_EDITOR_MANIFEST,
    FLOW_PRESETS_PATH,
    GEOSPATIAL_FORMAT_CONTRACT_PATH,
    GEOSPATIAL_IMPORT_PIPELINE_PATH as GEOSPATIAL_IMPORT_PIPELINE_MANIFEST,
    GEOMETRY_KINDS,
    MILESTONE21_FEATURE_TUNING_EDITOR_SCHEMA,
    MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA,
    MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA,
    MILESTONE21_REACH_LOCAL_STREAMING_SCHEMA,
    RAPID_RIVER_EDITOR_MANIFEST_PATH,
    RAPID_REVIEW_FLOW_DIFFICULTY_PATH,
    REACH_LOCAL_STREAMING_PATH as REACH_LOCAL_STREAMING_MANIFEST,
    REQUIRED_EVIDENCE_LAYERS,
    SPATIAL_AUDIO_PRESETS_PATH,
    SOUTH_FORK_WORKFLOW_PATH,
    TRACEABLE_RIVER_DATA_ASSETS_PATH,
    build_feature_tuning_editor_manifest,
    build_geospatial_import_pipeline_manifest,
    build_rapid_river_editor_manifest,
    build_reach_local_streaming_manifest,
    write_feature_tuning_editor_manifest,
    write_geospatial_import_pipeline_manifest,
    write_rapid_river_editor_manifest,
    write_reach_local_streaming_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RAPID_RIVER_EDITOR_PATH = REPO_ROOT / RAPID_RIVER_EDITOR_MANIFEST_PATH
RAPID_RIVER_EDITOR_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimRapidRiverEditorConfig.h"
)
GEOSPATIAL_IMPORT_PIPELINE_PATH = REPO_ROOT / GEOSPATIAL_IMPORT_PIPELINE_MANIFEST
GEOSPATIAL_IMPORT_PIPELINE_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimGeo/Public/RaftSimGeospatialImportPipeline.h"
)
REACH_LOCAL_STREAMING_PATH = REPO_ROOT / REACH_LOCAL_STREAMING_MANIFEST
REACH_LOCAL_STREAMING_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimReachLocalStreamingConfig.h"
)
FEATURE_TUNING_EDITOR_PATH = REPO_ROOT / FEATURE_TUNING_EDITOR_MANIFEST
FEATURE_TUNING_EDITOR_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimFeatureTuningEditorConfig.h"
)


def test_rapid_river_editor_manifest_matches_generator():
    expected = build_rapid_river_editor_manifest(REPO_ROOT).manifest
    committed = json.loads(RAPID_RIVER_EDITOR_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA
    assert committed["status"] == "ready_for_unreal_editor_widget_and_data_asset_authoring"


def test_rapid_river_editor_manifest_covers_required_annotation_tools():
    manifest = json.loads(RAPID_RIVER_EDITOR_PATH.read_text(encoding="utf-8"))
    template_ids = {template["template_id"] for template in manifest["annotation_templates"]}

    assert manifest["asset_class"] == "URaftSimRapidRiverEditorConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["source_workflow"] == SOUTH_FORK_WORKFLOW_PATH
    assert manifest["traceable_river_data_assets"] == TRACEABLE_RIVER_DATA_ASSETS_PATH
    assert set(manifest["geometry_kinds"]) == set(GEOMETRY_KINDS)
    assert set(manifest["required_evidence_layers"]) == set(REQUIRED_EVIDENCE_LAYERS)
    assert set(manifest["expected_outcomes"]) == set(EXPECTED_OUTCOMES)
    assert {"station_pin", "reach_drop_span", "polygon", "raft_line"} == template_ids
    assert {"one_view_map", "station_profile", "flow_and_sources", "annotation_editor"}.issubset(
        manifest["editor_panels"]
    )


def test_rapid_river_editor_seed_annotations_require_evidence_and_outcomes():
    manifest = json.loads(RAPID_RIVER_EDITOR_PATH.read_text(encoding="utf-8"))

    assert len(manifest["seed_annotations"]) >= 3
    for annotation in manifest["seed_annotations"]:
        assert annotation["station_pin"]["station_m"] > 0.0
        assert annotation["station_span_m"][0] < annotation["station_span_m"][1]
        assert annotation["polygon_layers"]
        assert annotation["raft_line_roles"] == ["entry_line", "main_current_line", "recovery_line"]
        assert annotation["footage_timecodes"]["required"] is True
        assert annotation["gauge_history_snippets"]
        assert annotation["aerial_imagery_references"]
        assert annotation["guide_notes"]
        assert annotation["rights_provenance"]["required"] is True
        assert set(annotation["rights_provenance"]["fields"]).issuperset(
            {"source_id", "license_or_terms", "attribution", "permission_status"}
        )
        assert {outcome["outcome"] for outcome in annotation["expected_outcome_review"]} == set(
            EXPECTED_OUTCOMES
        )


def test_rapid_river_editor_header_exposes_unreal_data_contract():
    header_text = RAPID_RIVER_EDITOR_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimRapidRiverEditorConfig" in header_text
    assert "ERaftSimRiverAnnotationGeometryKind" in header_text
    assert "ERaftSimRiverExpectedOutcome" in header_text
    for enum_value in ("StationPin", "ReachSpan", "DropSpan", "Polygon", "RaftLine"):
        assert enum_value in header_text
    for enum_value in ("Surf", "Flush", "Pin", "Release", "Flip"):
        assert enum_value in header_text
    assert "FRaftSimRiverEditorRightsProvenance" in header_text
    assert "FRaftSimRiverEditorEvidenceRef" in header_text
    assert "bRequireRightsProvenanceBeforeExport" in header_text
    assert "bRequireExpectedOutcomeBeforeGameplayTuning" in header_text


def test_write_rapid_river_editor_manifest_creates_json(tmp_path):
    output_json = tmp_path / "rapid_river_editor.json"

    generated = write_rapid_river_editor_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest


def test_geospatial_import_pipeline_manifest_matches_generator():
    expected = build_geospatial_import_pipeline_manifest(REPO_ROOT).manifest
    committed = json.loads(GEOSPATIAL_IMPORT_PIPELINE_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA
    assert committed["status"] == "ready_for_unreal_geospatial_import_tooling"


def test_geospatial_import_pipeline_covers_all_canonical_formats():
    manifest = json.loads(GEOSPATIAL_IMPORT_PIPELINE_PATH.read_text(encoding="utf-8"))
    stages = {stage["category"]: stage for stage in manifest["import_stages"]}

    assert manifest["asset_class"] == "URaftSimGeospatialImportPipelineConfig"
    assert manifest["module"] == "RaftSimGeo"
    assert manifest["format_contract"] == GEOSPATIAL_FORMAT_CONTRACT_PATH
    assert manifest["shapefile_canonical_allowed"] is False
    assert manifest["source_manifest_required"] is True
    assert set(stages) == {
        "source_manifests",
        "vectors_annotations",
        "rasters",
        "point_clouds",
        "gauge_history",
        "solver_packages",
        "unreal_corridor_exports",
    }
    assert {"GeoJSON", "GeoPackage"}.issubset(stages["vectors_annotations"]["canonical_formats"])
    assert {"GeoTIFF", "COG"}.issubset(stages["rasters"]["canonical_formats"])
    assert {"LAS", "LAZ", "COPC"}.issubset(stages["point_clouds"]["canonical_formats"])
    assert {"JSON", "CSV", "Parquet"}.issubset(stages["gauge_history"]["canonical_formats"])
    assert {"JSON", "NPY", "NPZ"}.issubset(stages["solver_packages"]["canonical_formats"])
    assert {"JSON", "GeoJSON", "converted_engine_assets"}.issubset(
        stages["unreal_corridor_exports"]["canonical_formats"]
    )
    assert stages["point_clouds"]["seed_status"] == "planned_not_vendored_in_south_fork_seed"
    assert stages["solver_packages"]["source_paths"]
    assert stages["unreal_corridor_exports"]["requires_source_manifest"] is True


def test_geospatial_import_pipeline_header_exposes_unreal_data_contract():
    header_text = GEOSPATIAL_IMPORT_PIPELINE_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimGeospatialImportPipelineConfig" in header_text
    assert "ERaftSimGeospatialImportCategory" in header_text
    for enum_value in (
        "SourceManifest",
        "VectorAnnotation",
        "Raster",
        "PointCloud",
        "GaugeHistory",
        "SolverPackage",
        "UnrealCorridorExport",
    ):
        assert enum_value in header_text
    assert "FRaftSimGeospatialImportStage" in header_text
    assert "bRejectShapefileAsCanonical" in header_text
    assert "bTrackTransformChanges" in header_text


def test_write_geospatial_import_pipeline_manifest_creates_json(tmp_path):
    output_json = tmp_path / "geospatial_import_pipeline.json"

    generated = write_geospatial_import_pipeline_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest


def test_reach_local_streaming_manifest_matches_generator():
    expected = build_reach_local_streaming_manifest(REPO_ROOT).manifest
    committed = json.loads(REACH_LOCAL_STREAMING_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_REACH_LOCAL_STREAMING_SCHEMA
    assert committed["status"] == "ready_for_reach_local_unreal_authoring_and_streaming"


def test_reach_local_streaming_requires_ghost_zones_and_stitched_exports():
    manifest = json.loads(REACH_LOCAL_STREAMING_PATH.read_text(encoding="utf-8"))

    assert manifest["asset_class"] == "URaftSimReachLocalStreamingConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["playable_window_count"] == 6
    for window in manifest["playable_windows"]:
        assert window["authoring_mode"] == "reach_local_grids"
        assert window["streaming_mode"] == "reach_window_with_overlap_ghost_zones"
        assert window["reach_local_grid_count"] == len(window["reach_ids"]) == len(
            window["reach_local_grids"]
        )
        assert window["streaming_contract"] == {
            "isolated_reach_validation_allowed_for_signoff": False,
            "neighbor_references_required": True,
            "overlap_metadata_required": True,
            "stitched_whole_window_validation_required": True,
        }
        assert window["ghost_zone_policy"]["max_upstream_ghost_cells"] == 2
        assert window["ghost_zone_policy"]["max_downstream_ghost_cells"] == 2
        assert window["stitched_validation"]["required"] is True
        assert window["stitched_validation_scope"]["covers_reach_local_grids"] is True
        assert window["stitched_validation_scope"]["seams_visible_to_validators"] is True
        for export_path in window["required_exports"].values():
            assert (REPO_ROOT / export_path).exists()


def test_reach_local_streaming_records_reach_adjacency():
    manifest = json.loads(REACH_LOCAL_STREAMING_PATH.read_text(encoding="utf-8"))

    for window in manifest["playable_windows"]:
        adjacency = window["reach_adjacency"]
        assert len(adjacency) == len(window["reach_ids"])
        assert adjacency[0]["upstream_neighbor"] is None
        assert adjacency[-1]["downstream_neighbor"] is None
        for previous, current in zip(adjacency, adjacency[1:]):
            assert previous["downstream_neighbor"] == current["reach_id"]
            assert current["upstream_neighbor"] == previous["reach_id"]


def test_reach_local_streaming_header_exposes_unreal_data_contract():
    header_text = REACH_LOCAL_STREAMING_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimReachLocalStreamingConfig" in header_text
    assert "FRaftSimReachLocalGridWindow" in header_text
    assert "FRaftSimReachStreamingWindow" in header_text
    assert "bRequireOverlapGhostZones" in header_text
    assert "bRejectIsolatedReachValidationForSignoff" in header_text
    assert "bRequiresStitchedWholeWindowValidation" in header_text


def test_write_reach_local_streaming_manifest_creates_json(tmp_path):
    output_json = tmp_path / "reach_local_streaming.json"

    generated = write_reach_local_streaming_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest


def test_feature_tuning_editor_manifest_matches_generator():
    expected = build_feature_tuning_editor_manifest(REPO_ROOT).manifest
    committed = json.loads(FEATURE_TUNING_EDITOR_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_FEATURE_TUNING_EDITOR_SCHEMA
    assert committed["status"] == "ready_for_unreal_feature_tuning_data_asset"


def test_feature_tuning_editor_covers_flow_dependent_feature_surface():
    manifest = json.loads(FEATURE_TUNING_EDITOR_PATH.read_text(encoding="utf-8"))
    groups = {group["feature_kind"]: group for group in manifest["feature_tuning_groups"]}

    assert manifest["asset_class"] == "URaftSimFeatureTuningEditorConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["feature_forcing_defaults"] == FEATURE_FORCING_DEFAULTS_PATH
    assert manifest["flow_presets"] == FLOW_PRESETS_PATH
    assert manifest["rapid_review_flow_difficulty_mapping"] == RAPID_REVIEW_FLOW_DIFFICULTY_PATH
    assert manifest["spatial_audio_presets"] == SPATIAL_AUDIO_PRESETS_PATH
    assert manifest["runtime_posture"]["feature_forcing_enabled_by_default"] is False
    assert manifest["runtime_posture"]["keep_default_gains_low"] is True
    assert manifest["validation_requirements"]["bounded"] is True
    assert manifest["validation_requirements"]["manifest_recorded"] is True
    assert manifest["validation_requirements"]["geoclaw_compared"] is True
    assert manifest["validation_requirements"]["flow_dependent"] is True
    assert manifest["validation_requirements"]["hide_conservation_failures"] is False
    assert manifest["validation_requirements"]["conservation_guard_required"] is True
    assert set(groups) == set(FEATURE_FORCING_KINDS)

    flow_band_ids = {band["flow_band"] for band in manifest["flow_bands"]}
    assert flow_band_ids == {"low_runnable", "median_runnable", "high_runnable"}
    for group in groups.values():
        assert group["enabled_by_default"] is False
        assert group["default_gain"] <= manifest["runtime_posture"]["max_default_gain"]
        assert set(group["editor_domains"]) == {
            "solver_state",
            "raft_coupling",
            "visual_only",
            "audio_only",
        }
        assert group["solver_state_effects"]
        assert group["raft_coupling_effects"]
        assert group["visual_only_parameters"]
        assert group["audio_only_parameters"]
        assert set(sample["flow_band"] for sample in group["flow_response_samples"]) == flow_band_ids
        assert all(sample["discharge_cfs"] > 0.0 for sample in group["flow_response_samples"])
        assert all(sample["effective_default_gain"] <= 0.15 for sample in group["flow_response_samples"])
        assert group["manifest_recording"]["required"] is True
        assert group["validation_contract"]["bounded"] is True
        assert group["validation_contract"]["geoclaw_compared"] is True
        assert group["validation_contract"]["conservation_guard_required"] is True
        assert group["validation_contract"]["hide_conservation_failures"] is False


def test_feature_tuning_editor_exposes_hole_washout_and_counterplay_parameters():
    manifest = json.loads(FEATURE_TUNING_EDITOR_PATH.read_text(encoding="utf-8"))
    groups = {group["feature_kind"]: group for group in manifest["feature_tuning_groups"]}
    hole_curve = {point["flow_band"]: point for point in groups["hole"]["hole_stickiness_washout_curve"]}

    assert hole_curve["median_runnable"]["stickiness_factor"] > hole_curve["low_runnable"]["stickiness_factor"]
    assert hole_curve["median_runnable"]["stickiness_factor"] > hole_curve["high_runnable"]["stickiness_factor"]
    assert hole_curve["high_runnable"]["washout_factor"] > hole_curve["median_runnable"]["washout_factor"]
    assert "hole_stickiness_factor" in groups["hole"]["tunable_parameters"]
    assert "hole_washout_factor" in groups["hole"]["tunable_parameters"]
    assert "boulder_push_scale" in groups["boulder_push_damping"]["tunable_parameters"]
    assert "boulder_damping_scale" in groups["boulder_push_damping"]["tunable_parameters"]
    assert "pin_load_threshold_n" in groups["pin_release"]["tunable_parameters"]
    assert "release_impulse_threshold_n_s" in groups["pin_release"]["tunable_parameters"]
    assert "crew_weight_distribution_scale" in groups["flip"]["tunable_parameters"]
    assert "high_side_counterplay_window_s" in groups["flip"]["tunable_parameters"]


def test_feature_tuning_editor_keeps_visual_audio_controls_non_authoritative():
    manifest = json.loads(FEATURE_TUNING_EDITOR_PATH.read_text(encoding="utf-8"))
    controls = manifest["visual_audio_only_controls"]

    assert controls
    assert {control["domain"] for control in controls} == {"visual_only", "audio_only"}
    assert len({control["control_id"] for control in controls}) == len(controls)
    for control in controls:
        assert control["manifest_recording_required"] is True
        assert control["effective_on_solver_state"] is False
        assert control["effective_on_raft_coupling"] is False
    assert manifest["export_rules"]["visual_audio_only_cannot_change_solver_state"] is True
    assert manifest["export_rules"]["manifest_record_every_edit"] is True
    assert manifest["export_rules"]["require_geoclaw_comparison_before_signoff"] is True
    assert manifest["export_rules"]["reject_conservation_failure_masking"] is True


def test_feature_tuning_editor_header_exposes_unreal_data_contract():
    header_text = FEATURE_TUNING_EDITOR_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimFeatureTuningEditorConfig" in header_text
    assert "ERaftSimRiverFeatureTuningKind" in header_text
    assert "ERaftSimRiverFeatureTuningDomain" in header_text
    for enum_value in (
        "Hole",
        "Boil",
        "Lateral",
        "EddyLine",
        "WaveTrain",
        "ShallowShelf",
        "BoulderPushDamping",
        "PinRelease",
        "Flip",
    ):
        assert enum_value in header_text
    for enum_value in ("SolverState", "RaftCoupling", "VisualOnly", "AudioOnly"):
        assert enum_value in header_text
    assert "FRaftSimRiverFeatureFlowBandSample" in header_text
    assert "FRaftSimRiverFeatureTuningRecord" in header_text
    assert "FRaftSimRiverVisualAudioOnlyControl" in header_text
    assert "bFeatureForcingEnabledByDefault" in header_text
    assert "bManifestRecordEveryEdit" in header_text
    assert "bRequireGeoClawComparisonBeforeSignoff" in header_text
    assert "bRejectConservationFailureMasking" in header_text


def test_write_feature_tuning_editor_manifest_creates_json(tmp_path):
    output_json = tmp_path / "feature_tuning_editor.json"

    generated = write_feature_tuning_editor_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest
