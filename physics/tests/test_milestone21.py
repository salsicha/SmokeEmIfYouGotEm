import json
from pathlib import Path

from raftsim.feature_forcing import FEATURE_FORCING_KINDS
from raftsim.milestone21 import (
    COLORADO_ROWING_FLOW_PRESETS_PATH,
    COLORADO_ROWING_ROUTE_PATH as COLORADO_ROWING_ROUTE_MANIFEST,
    COLORADO_ROWING_SOURCE_MANIFEST_PATH,
    EXPECTED_OUTCOMES,
    FEATURE_FORCING_DEFAULTS_PATH,
    FEATURE_TUNING_EDITOR_PATH as FEATURE_TUNING_EDITOR_MANIFEST,
    FLOW_PRESETS_PATH,
    GEOSPATIAL_FORMAT_CONTRACT_PATH,
    GEOSPATIAL_IMPORT_PIPELINE_PATH as GEOSPATIAL_IMPORT_PIPELINE_MANIFEST,
    GEOMETRY_KINDS,
    MILESTONE21_COLORADO_ROWING_ROUTE_SCHEMA,
    MILESTONE21_FEATURE_TUNING_EDITOR_SCHEMA,
    MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA,
    MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA,
    MILESTONE21_REACH_LOCAL_STREAMING_SCHEMA,
    MILESTONE21_ROUND_TRIP_VALIDATION_SCHEMA,
    MILESTONE21_SOUTH_FORK_EDITOR_PASS_SCHEMA,
    RAPID_RIVER_EDITOR_MANIFEST_PATH,
    RAPID_REVIEW_FLOW_DIFFICULTY_PATH,
    REACH_LOCAL_STREAMING_PATH as REACH_LOCAL_STREAMING_MANIFEST,
    REQUIRED_EVIDENCE_LAYERS,
    ROUND_TRIP_VALIDATION_PATH as ROUND_TRIP_VALIDATION_MANIFEST,
    SOUTH_FORK_CORRIDOR_PACKAGE_PATH,
    SOUTH_FORK_EDITOR_PASS_PATH as SOUTH_FORK_EDITOR_PASS_MANIFEST,
    SOUTH_FORK_RAPID_CANDIDATES_PATH,
    SOUTH_FORK_SOURCE_MANIFEST_PATH,
    SOUTH_FORK_VALIDATION_MATRIX_PATH,
    SPATIAL_AUDIO_PRESETS_PATH,
    SOUTH_FORK_WORKFLOW_PATH,
    TRACEABLE_RIVER_DATA_ASSETS_PATH,
    build_colorado_rowing_route_draft_manifest,
    build_feature_tuning_editor_manifest,
    build_geospatial_import_pipeline_manifest,
    build_rapid_river_editor_manifest,
    build_reach_local_streaming_manifest,
    build_round_trip_validation_manifest,
    build_south_fork_editor_pass_manifest,
    write_feature_tuning_editor_manifest,
    write_colorado_rowing_route_draft_manifest,
    write_geospatial_import_pipeline_manifest,
    write_rapid_river_editor_manifest,
    write_reach_local_streaming_manifest,
    write_round_trip_validation_manifest,
    write_south_fork_editor_pass_manifest,
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
SOUTH_FORK_EDITOR_PASS_PATH = REPO_ROOT / SOUTH_FORK_EDITOR_PASS_MANIFEST
SOUTH_FORK_EDITOR_PASS_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimSouthForkEditorPassConfig.h"
)
COLORADO_ROWING_ROUTE_PATH = REPO_ROOT / COLORADO_ROWING_ROUTE_MANIFEST
COLORADO_ROWING_SOURCE_MANIFEST_FILE = REPO_ROOT / COLORADO_ROWING_SOURCE_MANIFEST_PATH
COLORADO_ROWING_FLOW_PRESETS_FILE = REPO_ROOT / COLORADO_ROWING_FLOW_PRESETS_PATH
COLORADO_ROWING_ROUTE_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimColoradoRowingRouteConfig.h"
)
ROUND_TRIP_VALIDATION_PATH = REPO_ROOT / ROUND_TRIP_VALIDATION_MANIFEST
ROUND_TRIP_VALIDATION_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimRiverRoundTripValidationConfig.h"
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


def test_south_fork_editor_pass_manifest_matches_generator():
    expected = build_south_fork_editor_pass_manifest(REPO_ROOT).manifest
    committed = json.loads(SOUTH_FORK_EDITOR_PASS_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_SOUTH_FORK_EDITOR_PASS_SCHEMA
    assert committed["status"] == "ready_for_south_fork_unreal_editor_pass"


def test_south_fork_editor_pass_links_sources_flows_and_overlays():
    manifest = json.loads(SOUTH_FORK_EDITOR_PASS_PATH.read_text(encoding="utf-8"))

    assert manifest["asset_class"] == "URaftSimSouthForkEditorPassConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["source_manifest"] == SOUTH_FORK_SOURCE_MANIFEST_PATH
    assert manifest["corridor_package"] == SOUTH_FORK_CORRIDOR_PACKAGE_PATH
    assert manifest["rapid_candidates"] == SOUTH_FORK_RAPID_CANDIDATES_PATH
    assert manifest["flow_presets"] == FLOW_PRESETS_PATH
    assert manifest["validation_matrix"] == SOUTH_FORK_VALIDATION_MATRIX_PATH
    assert manifest["rapid_river_editor"] == RAPID_RIVER_EDITOR_MANIFEST_PATH
    assert manifest["feature_tuning_editor"] == FEATURE_TUNING_EDITOR_MANIFEST
    assert manifest["traceable_river_data_assets"] == TRACEABLE_RIVER_DATA_ASSETS_PATH
    assert manifest["reviewed_rapid_count"] == 4
    assert len(manifest["reviewed_rapids"]) == 4
    assert {band["flow_band"] for band in manifest["flow_bands"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert {run["flow_band"] for run in manifest["validation_runs"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert len(manifest["validation_overlays"]) == 6
    assert {overlay["solver_mode"] for overlay in manifest["validation_overlays"]} == {
        "reduced",
        "finite_volume",
    }
    assert {overlay["flow_band"] for overlay in manifest["validation_overlays"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert all(overlay["stitched_whole_window_required"] is True for overlay in manifest["validation_overlays"])


def test_south_fork_editor_pass_records_guide_feedback_for_each_reviewed_rapid():
    manifest = json.loads(SOUTH_FORK_EDITOR_PASS_PATH.read_text(encoding="utf-8"))
    overlay_ids = {overlay["overlay_id"] for overlay in manifest["validation_overlays"]}

    for rapid in manifest["reviewed_rapids"]:
        assert rapid["accepted_for_editor_pass"] is True
        assert rapid["review_status"] == "seed_reviewed_for_first_editor_pass_needs_human_signoff"
        assert rapid["reviewed_labels"]
        assert rapid["expected_outcomes"]
        assert rapid["guide_feedback_annotations"]
        assert rapid["rights_provenance"]["required"] is True
        assert {"aerial_satellite_imagery", "gauge_history", "source_manifest", "guide_notes"}.issubset(
            rapid["required_evidence_layers_present"]
        )
        assert {review["flow_band"] for review in rapid["flow_review"]} == {
            "low_runnable",
            "median_runnable",
            "high_runnable",
        }
        for review in rapid["flow_review"]:
            assert review["requires_outcome_review"] is True
            assert set(review["validation_overlay_ids"]).issubset(overlay_ids)
            assert len(review["validation_overlay_ids"]) == 2
        for annotation in rapid["guide_feedback_annotations"]:
            assert annotation["flow_context_required"] is True
            assert annotation["footage_timecodes_required"] is True
            assert annotation["rights_status"] == "manifest_references_only"
            assert annotation["human_guide_signoff_required"] is True


def test_south_fork_editor_pass_header_exposes_unreal_data_contract():
    header_text = SOUTH_FORK_EDITOR_PASS_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimSouthForkEditorPassConfig" in header_text
    assert "ERaftSimSouthForkReviewStatus" in header_text
    assert "FRaftSimSouthForkReviewedRapid" in header_text
    assert "FRaftSimSouthForkFlowReviewBand" in header_text
    assert "FRaftSimSouthForkGuideFeedbackAnnotation" in header_text
    assert "FRaftSimSouthForkValidationOverlay" in header_text
    assert "SeedReviewedNeedsHumanSignoff" in header_text
    assert "ReviewedRapids" in header_text
    assert "ValidationOverlays" in header_text
    assert "bRequireGuideFeedbackAnnotations" in header_text
    assert "bRequireLowMedianHighFlowPresets" in header_text
    assert "bRequireStitchedValidationOverlays" in header_text
    assert "bFieldMediaManifestReferencesOnlyUntilRightsClear" in header_text


def test_write_south_fork_editor_pass_manifest_creates_json(tmp_path):
    output_json = tmp_path / "south_fork_first_river_editor_pass.json"

    generated = write_south_fork_editor_pass_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest


def test_colorado_rowing_route_draft_files_preserve_generator_seed_and_reviewed_enrichment():
    expected = build_colorado_rowing_route_draft_manifest(REPO_ROOT)
    committed_manifest = json.loads(COLORADO_ROWING_ROUTE_PATH.read_text(encoding="utf-8"))
    committed_source = json.loads(COLORADO_ROWING_SOURCE_MANIFEST_FILE.read_text(encoding="utf-8"))
    committed_flows = json.loads(COLORADO_ROWING_FLOW_PRESETS_FILE.read_text(encoding="utf-8"))

    assert committed_flows == expected.flow_presets
    for key in (
        "schema",
        "route_id",
        "module",
        "asset_class",
        "river_id",
        "section_id",
        "section_name",
        "route_style",
        "source_manifest",
        "flow_presets",
        "route_endpoints",
        "route_segments",
        "flow_bands",
        "flow_band_policy",
        "guide_review_requirements",
        "validation_annotation_needs",
        "status",
    ):
        assert committed_manifest[key] == expected.manifest[key]
    assert expected.manifest["editor_status"].items() <= committed_manifest["editor_status"].items()

    expected_controls = {
        control["control_id"]: control
        for control in expected.manifest["rowing_frame_controls"]
    }
    committed_controls = {
        control["control_id"]: control
        for control in committed_manifest["rowing_frame_controls"]
    }
    assert committed_controls.keys() == expected_controls.keys()
    for control_id, expected_control in expected_controls.items():
        committed_control = committed_controls[control_id]
        for key in ("control_kind", "gameplay_role", "telemetry"):
            assert committed_control[key] == expected_control[key]
        assert committed_control["input_axes"]

    for key in (
        "schema_version",
        "manifest_id",
        "river_id",
        "section_id",
        "section_name",
        "route_style",
        "bounds_wgs84",
        "coordinate_reference_systems",
        "provenance",
    ):
        assert committed_source[key] == expected.source_manifest[key]
    expected_source_ids = {
        source["source_id"] for source in expected.source_manifest["sources"]
    }
    committed_source_ids = {
        source["source_id"] for source in committed_source["sources"]
    }
    assert expected_source_ids <= committed_source_ids
    expected_fetch_ids = {
        fetch["fetch_id"] for fetch in expected.source_manifest["remote_fetches"]
    }
    committed_fetch_ids = {
        fetch["fetch_id"] for fetch in committed_source["remote_fetches"]
    }
    assert expected_fetch_ids <= committed_fetch_ids
    for category, expected_paths in expected.source_manifest["artifacts"].items():
        assert set(expected_paths) <= set(committed_source["artifacts"][category])
    for confidence_key, expected_value in expected.source_manifest["confidence"].items():
        assert committed_source["confidence"][confidence_key] >= expected_value

    assert committed_manifest["schema"] == MILESTONE21_COLORADO_ROWING_ROUTE_SCHEMA
    assert committed_manifest["status"] == "ready_for_colorado_rowing_route_planning"


def test_colorado_rowing_route_has_source_manifest_and_planning_flow_bands():
    manifest = json.loads(COLORADO_ROWING_ROUTE_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(COLORADO_ROWING_SOURCE_MANIFEST_FILE.read_text(encoding="utf-8"))
    flow_presets = json.loads(COLORADO_ROWING_FLOW_PRESETS_FILE.read_text(encoding="utf-8"))

    assert manifest["asset_class"] == "URaftSimColoradoRowingRouteConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["route_style"] == "rowing_oar_rig"
    assert manifest["source_manifest"] == COLORADO_ROWING_SOURCE_MANIFEST_PATH
    assert manifest["flow_presets"] == COLORADO_ROWING_FLOW_PRESETS_PATH
    assert manifest["route_endpoints"]["put_in"] == "Lees Ferry"
    assert manifest["route_endpoints"]["take_out"] == "Diamond Creek"
    assert source_manifest["route_style"] == "rowing_oar_rig"
    assert source_manifest["provenance"]["review_status"] == "draft_target_needs_geospatial_pull_and_guide_review"
    assert {"usgs_09380000_lees_ferry", "usgs_09402500_near_grand_canyon", "nps_grand_canyon_river_trips"}.issubset(
        {source["source_id"] for source in source_manifest["sources"]}
    )
    assert flow_presets["status"] == "planning_placeholders_require_usgs_gauge_history_and_release_context"
    assert flow_presets["flow_band_policy"]["must_replace_placeholders"] is True
    assert flow_presets["flow_band_policy"]["requires_gauge_history"] is True
    assert flow_presets["flow_band_policy"]["requires_dam_release_context"] is True
    assert {band["flow_band"] for band in flow_presets["flow_bands"]} == {
        "low_release_planning",
        "moderate_release_planning",
        "high_release_planning",
    }
    assert [band["discharge_cfs"] for band in flow_presets["flow_bands"]] == sorted(
        band["discharge_cfs"] for band in flow_presets["flow_bands"]
    )


def test_colorado_rowing_route_exposes_oar_controls_guide_review_and_annotation_needs():
    manifest = json.loads(COLORADO_ROWING_ROUTE_PATH.read_text(encoding="utf-8"))
    controls = {control["control_id"]: control for control in manifest["rowing_frame_controls"]}
    needs = {need["need_id"]: need for need in manifest["validation_annotation_needs"]}

    assert set(controls) == {
        "pull_stroke",
        "back_row",
        "ferry_angle_hold",
        "spin_and_pivot_correction",
        "passenger_weight_trim",
        "rescue_assist_rowing",
    }
    assert controls["pull_stroke"]["control_kind"] == "pull"
    assert controls["back_row"]["control_kind"] == "back_row"
    assert "swimmer_distance_m" in controls["rescue_assist_rowing"]["telemetry"]
    assert manifest["guide_review_requirements"]["oar_rig_guide_signoff_required"] is True
    assert manifest["guide_review_requirements"]["field_media_timecodes_required"] is True
    assert manifest["guide_review_requirements"]["rights_cleared_guide_notes_required"] is True
    assert manifest["guide_review_requirements"]["do_not_vendor_guidebook_text"] is True
    assert {"river_mile_stationing", "large_volume_lines", "rowing_rescue_windows"}.issubset(needs)
    assert "river_mile" in needs["river_mile_stationing"]["review_fields"]
    assert "pull_back_row_plan" in needs["large_volume_lines"]["review_fields"]
    assert "swimmer_drift_path" in needs["rowing_rescue_windows"]["review_fields"]
    assert len(manifest["route_segments"]) >= 4


def test_colorado_rowing_route_header_exposes_unreal_data_contract():
    header_text = COLORADO_ROWING_ROUTE_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimColoradoRowingRouteConfig" in header_text
    assert "ERaftSimColoradoRowingControlKind" in header_text
    assert "FRaftSimColoradoFlowBand" in header_text
    assert "FRaftSimColoradoRowingControl" in header_text
    assert "FRaftSimColoradoRouteSegment" in header_text
    assert "FRaftSimColoradoValidationAnnotationNeed" in header_text
    for enum_value in ("Pull", "BackRow", "FerryAngle", "SpinCorrection", "PassengerTrim", "RescueAssist"):
        assert enum_value in header_text
    assert "RowingFrameControls" in header_text
    assert "ValidationAnnotationNeeds" in header_text
    assert "bOarRigGuideSignoffRequired" in header_text
    assert "bRequiresGaugeHistoryReplacement" in header_text


def test_write_colorado_rowing_route_draft_manifest_creates_json(tmp_path):
    output_json = tmp_path / "colorado_rowing_route_editor_pass.json"
    source_json = tmp_path / "source_manifest.json"
    flow_json = tmp_path / "flow_presets.json"

    generated = write_colorado_rowing_route_draft_manifest(
        repo_root=REPO_ROOT,
        output_json=output_json,
        source_manifest_json=source_json,
        flow_presets_json=flow_json,
    )

    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest
    assert json.loads(source_json.read_text(encoding="utf-8")) == generated.source_manifest
    assert json.loads(flow_json.read_text(encoding="utf-8")) == generated.flow_presets


def test_round_trip_validation_manifest_matches_generator():
    expected = build_round_trip_validation_manifest(REPO_ROOT).manifest
    committed = json.loads(ROUND_TRIP_VALIDATION_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE21_ROUND_TRIP_VALIDATION_SCHEMA
    assert committed["status"] == "ready_for_round_trip_validation_harness"


def test_round_trip_validation_covers_required_targets_and_metadata_guards():
    manifest = json.loads(ROUND_TRIP_VALIDATION_PATH.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in manifest["round_trip_cases"]}

    assert manifest["asset_class"] == "URaftSimRiverRoundTripValidationConfig"
    assert manifest["module"] == "RaftSimRiver"
    assert manifest["canonical_format_contract"] == GEOSPATIAL_FORMAT_CONTRACT_PATH
    assert manifest["geospatial_import_pipeline"] == GEOSPATIAL_IMPORT_PIPELINE_MANIFEST
    assert set(manifest["required_target_kinds"]) == {
        "solver_packages",
        "geoclaw_cpp_comparison_inputs",
        "fidelity_review_overlays",
    }
    assert {"south_fork_unreal_exports_to_solver_packages", "south_fork_reach_local_streaming_to_stitched_windows", "colorado_rowing_route_metadata_to_planning_inputs"} == set(cases)
    assert manifest["metadata_guard_categories"]["crs"]["source_crs_required"] is True
    assert manifest["metadata_guard_categories"]["transform"]["wgs84_required"] is True
    assert manifest["metadata_guard_categories"]["provenance"]["source_manifest_required"] is True
    assert manifest["metadata_guard_categories"]["flow_response_metadata"]["flow_dependent_forcing_required"] is True
    assert manifest["source_summaries"]["south_fork_reviewed_rapids"] == 4
    assert manifest["source_summaries"]["colorado_route_segments"] >= 4

    for case in cases.values():
        assert set(case["regenerates"]) == {
            "solver_packages",
            "geoclaw_cpp_comparison_inputs",
            "fidelity_review_overlays",
        }
        assert case["metadata_guards"]["crs"]
        assert case["metadata_guards"]["provenance"]
        assert case["metadata_guards"]["flow_response_metadata"]
        assert "coordinate_reference_systems_preserved" in case["loss_checks"]
        assert "source_ids_and_license_terms_preserved" in case["loss_checks"]
        assert "flow_band_ids_and_discharge_values_preserved" in case["loss_checks"]


def test_round_trip_validation_preserves_south_fork_stitched_overlays_and_colorado_metadata():
    manifest = json.loads(ROUND_TRIP_VALIDATION_PATH.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in manifest["round_trip_cases"]}
    south_fork = cases["south_fork_unreal_exports_to_solver_packages"]
    reach_streaming = cases["south_fork_reach_local_streaming_to_stitched_windows"]
    colorado = cases["colorado_rowing_route_metadata_to_planning_inputs"]

    assert len(south_fork["regenerates"]["solver_packages"]) == 6
    assert len(south_fork["regenerates"]["fidelity_review_overlays"]) == 6
    assert {overlay["flow_band"] for overlay in south_fork["regenerates"]["fidelity_review_overlays"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert {overlay["solver_mode"] for overlay in south_fork["regenerates"]["fidelity_review_overlays"]} == {
        "reduced",
        "finite_volume",
    }
    assert len(reach_streaming["regenerates"]["solver_packages"]) == 6
    assert all("stitched" in overlay["overlay_id"] for overlay in reach_streaming["regenerates"]["fidelity_review_overlays"])
    assert colorado["status"] == "metadata_round_trip_ready_solver_outputs_planned"
    assert colorado["regenerates"]["solver_packages"] == ["planned_after_geospatial_pull"]
    assert len(colorado["regenerates"]["fidelity_review_overlays"]) >= 5
    assert COLORADO_ROWING_FLOW_PRESETS_PATH in colorado["metadata_guards"]["flow_response_metadata"]


def test_round_trip_validation_header_exposes_unreal_data_contract():
    header_text = ROUND_TRIP_VALIDATION_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimRiverRoundTripValidationConfig" in header_text
    assert "ERaftSimRiverRoundTripTargetKind" in header_text
    assert "FRaftSimRiverRoundTripCase" in header_text
    assert "FRaftSimRiverRoundTripMetadataGuards" in header_text
    assert "FRaftSimRiverRoundTripOverlay" in header_text
    for enum_value in ("SolverPackages", "GeoClawCppComparisonInputs", "FidelityReviewOverlays"):
        assert enum_value in header_text
    assert "bRequireCrsPreservation" in header_text
    assert "bRequireProvenancePreservation" in header_text
    assert "bRequireFlowResponseMetadataPreservation" in header_text
    assert "bRejectIsolatedReachLocalSignoff" in header_text


def test_write_round_trip_validation_manifest_creates_json(tmp_path):
    output_json = tmp_path / "round_trip_validation.json"

    generated = write_round_trip_validation_manifest(repo_root=REPO_ROOT, output_json=output_json)

    assert output_json.exists()
    assert json.loads(output_json.read_text(encoding="utf-8")) == generated.manifest
