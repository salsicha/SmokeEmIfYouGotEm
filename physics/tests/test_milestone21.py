import json
from pathlib import Path

from raftsim.milestone21 import (
    EXPECTED_OUTCOMES,
    GEOSPATIAL_FORMAT_CONTRACT_PATH,
    GEOSPATIAL_IMPORT_PIPELINE_PATH as GEOSPATIAL_IMPORT_PIPELINE_MANIFEST,
    GEOMETRY_KINDS,
    MILESTONE21_GEOSPATIAL_IMPORT_PIPELINE_SCHEMA,
    MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA,
    RAPID_RIVER_EDITOR_MANIFEST_PATH,
    REQUIRED_EVIDENCE_LAYERS,
    SOUTH_FORK_WORKFLOW_PATH,
    TRACEABLE_RIVER_DATA_ASSETS_PATH,
    build_geospatial_import_pipeline_manifest,
    build_rapid_river_editor_manifest,
    write_geospatial_import_pipeline_manifest,
    write_rapid_river_editor_manifest,
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
