"""Milestone 21 Unreal river editor and content-pipeline artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MILESTONE21_RAPID_RIVER_EDITOR_SCHEMA = "raftsim.unreal.rapid_river_editor.v1"
RAPID_RIVER_EDITOR_MANIFEST_PATH = "unreal/Content/RaftSim/River/rapid_river_editor.json"
SOUTH_FORK_WORKFLOW_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/rapid_review_editor_workflow.json"
)
TRACEABLE_RIVER_DATA_ASSETS_PATH = "unreal/Content/RaftSim/River/traceable_river_data_assets.json"

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


@dataclass(frozen=True, slots=True)
class Milestone21RapidRiverEditor:
    """Generated Unreal rapid/river editor manifest."""

    manifest: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
