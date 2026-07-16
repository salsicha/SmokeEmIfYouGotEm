import json
from pathlib import Path

from raftsim.colorado_a2_centerline_decision import (
    COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH,
    COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_SCHEMA,
    COLORADO_A2_CENTERLINE_DECISION_VALIDATION_REPORT_RELATIVE_PATH,
    COLORADO_A2_CENTERLINE_DECISION_VALIDATION_SCHEMA,
    build_colorado_a2_centerline_decision_template,
    build_colorado_a2_centerline_decision_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (
            REPO_ROOT / COLORADO_A2_CENTERLINE_DECISION_VALIDATION_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_colorado_a2_centerline_decision_template_is_reproducible_and_empty():
    generated = build_colorado_a2_centerline_decision_template(REPO_ROOT)
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_SCHEMA
    assert committed["status"] == (
        "empty_centerline_decision_template_no_source_download_no_promotion"
    )
    assert committed["production_promoted"] is False
    result = committed["decision_result"]
    assert result["chosen_option_id"] == ""
    assert result["decision_owner"] == ""
    assert result["decision_status"] == "not_recorded"
    assert result["route_regeneration_scope"] == []


def test_colorado_a2_centerline_decision_template_records_evidence_and_options():
    template = _load_template()

    assert template["evidence_summary"]["existing_editor_binding_max_station_m"] == 4700.0
    assert template["evidence_summary"]["planned_run_length_m"] == 451420.0
    assert template["evidence_summary"]["hydrography_tnm_total"] == 94
    assert template["evidence_summary"]["terrain_tnm_total"] == 0
    assert template["evidence_summary"]["naip_tnm_total"] == 0
    assert template["allowed_option_ids"] == [
        "official_hydrography_with_nps_gcmrc_river_mile_calibration",
        "reviewed_local_river_mile_axis_with_source_raster_transforms",
        "defer_until_pearce_ferry_anchor_or_source_family_is_reviewed",
    ]
    assert set(template["required_reviewer_roles"]) == {
        "owner_or_producer_acceptance",
        "grand_canyon_oarsman_or_guide_reviewer",
        "geospatial_reviewer",
        "rights_publication_reviewer",
        "technical_world_partition_reviewer",
    }


def test_colorado_a2_centerline_decision_template_blocks_promotion():
    template = _load_template()
    gate = template["promotion_gate"]
    contract = template["validation_contract"]

    assert contract["template_is_empty"] is True
    assert contract["may_download_sources_from_empty_template"] is False
    assert contract["may_generate_window_bboxes_from_empty_template"] is False
    assert contract["may_bind_solver_windows_from_empty_template"] is False
    assert gate["can_download_full_reach_sources"] is False
    assert gate["can_generate_source_window_bboxes"] is False
    assert gate["can_promote_full_reach_centerline"] is False
    assert gate["can_bind_solver_windows"] is False


def test_colorado_a2_centerline_decision_validation_report_is_reproducible():
    generated = build_colorado_a2_centerline_decision_validation_report(REPO_ROOT)
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_CENTERLINE_DECISION_VALIDATION_SCHEMA
    assert committed["status"] == "centerline_decision_incomplete_a2_promotion_blocked"
    assert committed["decision_valid"] is False
    assert committed["production_promoted"] is False


def test_colorado_a2_centerline_decision_validation_blocks_empty_template():
    report = _load_validation_report()

    assert set(report["missing_required_fields"]) == {
        "chosen_option_id",
        "decision_owner",
        "decision_date",
        "full_length_centerline_source",
        "lees_ferry_anchor_geometry",
        "pearce_ferry_anchor_geometry",
        "working_crs_or_station_axis_policy",
        "river_mile_calibration_policy",
        "major_rapid_crosscheck_policy",
        "source_window_bbox_generation_scope",
        "route_regeneration_scope",
        "rights_publication_policy",
    }
    assert {failure["role"] for failure in report["reviewer_failures"]} == {
        "owner_or_producer_acceptance",
        "grand_canyon_oarsman_or_guide_reviewer",
        "geospatial_reviewer",
        "rights_publication_reviewer",
        "technical_world_partition_reviewer",
    }
    permissions = report["regeneration_permissions"]
    assert permissions["can_download_full_reach_sources"] is False
    assert permissions["can_generate_source_window_bboxes"] is False
    assert permissions["can_restation_major_rapids"] is False
    assert permissions["can_bind_solver_windows"] is False


def test_colorado_a2_centerline_decision_validation_accepts_complete_payload():
    report = build_colorado_a2_centerline_decision_validation_report(
        REPO_ROOT, _complete_decision_payload()
    )

    assert report["status"] == "centerline_decision_valid_manual_regeneration_allowed"
    assert report["decision_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["missing_required_fields"] == []
    assert report["invalid_fields"] == []
    assert report["reviewer_failures"] == []
    assert report["regeneration_permissions"]["can_download_full_reach_sources"] is True
    assert report["regeneration_permissions"]["can_generate_source_window_bboxes"] is True
    assert report["regeneration_permissions"]["can_bind_solver_windows"] is True
    assert report["regeneration_permissions"]["can_promote_from_validation_report_alone"] is False
    assert report["promotion_gate"]["can_import_unreal_full_reach_landscape"] is False


def test_colorado_a2_centerline_decision_validation_rejects_bad_option_and_buffer():
    payload = _complete_decision_payload()
    payload["decision_result"]["chosen_option_id"] = "not_allowed"
    payload["decision_result"]["source_window_bbox_generation_scope"][
        "buffer_policy_m"
    ] = 0.0
    report = build_colorado_a2_centerline_decision_validation_report(REPO_ROOT, payload)

    assert report["decision_valid"] is False
    assert {"field": "chosen_option_id", "reason": "option_id_not_allowed"} in report[
        "invalid_fields"
    ]
    assert {
        "field": "source_window_bbox_generation_scope",
        "reason": "buffer_policy_m_must_be_positive",
    } in report["invalid_fields"]


def _complete_decision_payload() -> dict:
    payload = build_colorado_a2_centerline_decision_template(REPO_ROOT)
    result = payload["decision_result"]
    result.update(
        {
            "chosen_option_id": payload["allowed_option_ids"][0],
            "decision_owner": "owner-review",
            "decision_date": "2026-07-16",
            "decision_status": "approved",
            "full_length_centerline_source": {
                "source_family": "USGS hydrography plus NPS/GCMRC river miles",
                "source_product_or_dataset": "NHD Best Resolution review extract",
                "source_report": "review/colorado_centerline_source_selection.json",
                "source_feature_id_policy": "preserve source IDs through clipped centerline",
                "notes": "synthetic complete test payload",
            },
            "lees_ferry_anchor_geometry": _point("upstream_start", -111.5167285, 36.8777351),
            "pearce_ferry_anchor_geometry": _point("downstream_end", -114.0900, 36.0910),
            "working_crs_or_station_axis_policy": {
                "policy_id": "local_river_mile_axis",
                "crs_or_axis": "reviewed station axis with per-window raster CRS",
                "distortion_review_report": "review/colorado_crs_distortion_review.json",
                "unreal_world_partition_notes": "use per-window local origins",
            },
            "river_mile_calibration_policy": {
                "source_authority": "NPS/GCMRC reviewed river mile references",
                "station_zero_policy": "Lees Ferry put-in is station zero",
                "river_mile_tick_policy": "cross-check against reviewed references",
                "source_report": "review/colorado_river_mile_calibration.json",
            },
            "major_rapid_crosscheck_policy": {
                "required_sources": ["NPS", "USGS hydraulic maps", "oarsman review"],
                "crosscheck_report": "review/full_reach_rapid_mile_crosscheck.json",
                "acceptable_tolerance_m": 150.0,
                "unresolved_disagreement_policy": "keep rapid blocked and preserve aliases",
            },
            "source_window_bbox_generation_scope": {
                "windows_to_generate": [
                    "colorado_a2_window_01",
                    "colorado_a2_window_02",
                ],
                "buffer_policy_m": 900.0,
                "terrain_export_policy": "bounded USGS 3DEP ImageServer exports",
                "imagery_export_policy": "bounded USDA/APFO NAIP ImageServer exports",
            },
            "route_regeneration_scope": [
                "full_reach_centerline_candidate",
                "source_window_bboxes",
                "rapid_mile_crosscheck",
                "full_reach_source_pull_plan",
            ],
            "rights_publication_policy": "link-only sources and sensitive access review",
        }
    )
    for role in payload["reviewer_signoff"].values():
        role.update(
            {
                "name_or_role": "reviewer",
                "review_date": "2026-07-16",
                "approved": True,
                "evidence": ["review/example_colorado_decision_evidence.json"],
                "notes": "synthetic complete test payload",
            }
        )
    return payload


def _point(role: str, lon: float, lat: float) -> dict:
    return {
        "role": role,
        "geometry_type": "Point",
        "coordinates": [lon, lat],
        "crs": "EPSG:4326",
        "source_authority": "reviewed geospatial/oarsman point",
        "source_report": "review/colorado_endpoint_review.json",
        "publication_sensitivity": "public screenshot requires rights/access review",
    }
