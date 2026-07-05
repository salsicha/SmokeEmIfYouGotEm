import json
from pathlib import Path

from raftsim.milestone21 import (
    EXPECTED_OUTCOMES,
    GEOMETRY_KINDS,
    MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA,
    RAPID_RIVER_EDITOR_MANIFEST_PATH,
    REQUIRED_EVIDENCE_LAYERS,
    SOUTH_FORK_WORKFLOW_PATH,
    TRACEABLE_RIVER_DATA_ASSETS_PATH,
    build_rapid_river_editor_manifest,
    write_rapid_river_editor_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RAPID_RIVER_EDITOR_PATH = REPO_ROOT / RAPID_RIVER_EDITOR_MANIFEST_PATH
RAPID_RIVER_EDITOR_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRiver/Public/RaftSimRapidRiverEditorConfig.h"
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
