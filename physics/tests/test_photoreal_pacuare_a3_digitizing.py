import json
from pathlib import Path

from raftsim.examples.validate_pacuare_a3_digitizing_result import (
    main as validate_pacuare_a3_digitizing_result_main,
)
from raftsim.pacuare_a3_digitizing import (
    PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
    PACUARE_A3_DIGITIZING_ACTION_PACKET_SCHEMA,
    PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH,
    PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_SCHEMA,
    PACUARE_A3_DIGITIZING_VALIDATION_REPORT_RELATIVE_PATH,
    PACUARE_A3_DIGITIZING_VALIDATION_REPORT_SCHEMA,
    build_pacuare_a3_digitizing_action_packet,
    build_pacuare_a3_digitizing_result_template,
    build_pacuare_a3_digitizing_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_action_packet() -> dict:
    return json.loads(
        (REPO_ROOT / PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (REPO_ROOT / PACUARE_A3_DIGITIZING_VALIDATION_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_pacuare_a3_digitizing_action_packet_is_reproducible_and_blocked():
    generated = build_pacuare_a3_digitizing_action_packet(REPO_ROOT)
    committed = _load_action_packet()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_DIGITIZING_ACTION_PACKET_SCHEMA
    assert committed["status"] == "digitizing_actions_ready_no_stationing_promotion"
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 15
    assert committed["critical_rapid_count"] == 6
    assert committed["promotion_gate"]["can_replace_order_interpolation"] is False
    assert committed["promotion_gate"]["can_bind_solver_windows"] is False


def test_pacuare_a3_digitizing_actions_cover_every_catalog_rapid():
    packet = _load_action_packet()
    actions = {action["rapid_name"]: action for action in packet["digitizing_actions"]}

    assert set(actions) == {
        "Bienvenidos",
        "Pyramid Rock",
        "Pele El Ojo",
        "Upper Huacas",
        "Bobo Falls",
        "Lower Huacas",
        "Rodeo",
        "Guatemala",
        "Double Drop",
        "Cimarrones",
        "Upper Pinball",
        "Lower Pinball",
        "Wall of Sorrow",
        "Dos Montanas",
        "Las Ranitas",
    }
    assert actions["Upper Huacas"]["current_station_m_from_order_interpolation"] == 6562.5
    assert actions["Dos Montanas"]["aliases"] == ["Dos Montañas"]
    assert actions["Double Drop"]["required_output_geometry"] == ["Point", "LineString"]
    assert "guide_or_outfitter_confirmation" in actions["Cimarrones"]["required_source_classes"]
    assert "solver_window_binding" in actions["Wall of Sorrow"]["blocks_until_complete"]


def test_pacuare_a3_digitizing_template_is_reproducible_and_empty():
    generated = build_pacuare_a3_digitizing_result_template(REPO_ROOT)
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_digitizing_result_template_no_stationing_promotion"
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 15
    first = committed["stationing_result_records"][0]
    assert first["geometry_type"] == ""
    assert first["geometry_coordinates_wgs84"] == []
    assert first["station_m_on_reviewed_route"] is None
    assert first["stationing_kind"] == "not_recorded"
    assert first["stationing_promoted"] is False
    assert first["solver_window_enabled"] is False


def test_pacuare_a3_digitizing_validation_report_blocks_empty_template():
    generated = build_pacuare_a3_digitizing_validation_report(REPO_ROOT)
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_DIGITIZING_VALIDATION_REPORT_SCHEMA
    assert committed["status"] == (
        "digitizing_result_incomplete_stationing_promotion_blocked"
    )
    assert committed["digitizing_valid"] is False
    assert committed["passing_rapid_count"] == 0
    assert committed["validation_error_count"] > 150
    reasons = {error["reason"] for error in committed["errors"]}
    assert {
        "geometry_type_not_allowed_or_missing",
        "station_m_missing",
        "stationing_kind_not_exact_or_missing",
        "required_field_empty",
        "confidence_m_missing",
        "rights_publication_not_approved",
        "protected_area_publication_not_approved",
        "flow_source_class_missing_or_not_allowed",
        "source_evidence_missing",
        "guide_evidence_missing",
    }.issubset(reasons)
    assert {
        failure["role"] for failure in committed["reviewer_failures"]
    } == {
        "owner_or_producer_acceptance",
        "pacuare_guide_or_outfitter_reviewer",
        "geospatial_reviewer",
        "rights_publication_reviewer",
        "hydrology_or_flow_reviewer",
    }
    permissions = committed["promotion_permissions"]
    assert permissions["can_replace_order_interpolation"] is False
    assert permissions["can_regenerate_named_rapid_catalog"] is False
    assert permissions["can_generate_rapid_water_windows"] is False
    assert permissions["can_bind_solver_windows"] is False


def test_pacuare_a3_digitizing_validation_accepts_complete_payload_without_solver_promotion():
    report = build_pacuare_a3_digitizing_validation_report(
        REPO_ROOT, _complete_digitizing_payload()
    )

    assert report["status"] == "digitizing_result_valid_manual_catalog_regeneration_allowed"
    assert report["digitizing_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["passing_rapid_count"] == 15
    permissions = report["promotion_permissions"]
    assert permissions["can_replace_order_interpolation"] is True
    assert permissions["can_regenerate_named_rapid_catalog"] is True
    assert permissions["can_regenerate_editor_geometry"] is True
    assert permissions["can_generate_rapid_water_windows"] is True
    assert permissions["can_bind_solver_windows"] is False
    assert permissions["can_promote_a3_from_validation_report_alone"] is False
    assert report["promotion_gate"]["can_promote_current_preview_route"] is False


def test_pacuare_a3_digitizing_validation_rejects_provisional_and_solver_enabled_records():
    payload = _complete_digitizing_payload()
    payload["stationing_result_records"][0]["stationing_kind"] = (
        "provisional_downstream_order_interpolation"
    )
    payload["stationing_result_records"][0]["solver_window_enabled"] = True
    report = build_pacuare_a3_digitizing_validation_report(REPO_ROOT, payload)

    assert report["digitizing_valid"] is False
    assert {
        "rapid_name": "Bienvenidos",
        "field": "stationing_kind",
        "reason": "stationing_kind_not_exact_or_missing",
    } in report["errors"]
    assert {
        "rapid_name": "Bienvenidos",
        "field": "solver_window_enabled",
        "reason": "solver_binding_requires_later_water_validation",
    } in report["errors"]


def test_pacuare_a3_digitizing_cli_writes_empty_gate():
    exit_code = validate_pacuare_a3_digitizing_result_main(
        ["--repo-root", str(REPO_ROOT)]
    )

    packet_path = REPO_ROOT / PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH
    template_path = REPO_ROOT / PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH
    report_path = REPO_ROOT / PACUARE_A3_DIGITIZING_VALIDATION_REPORT_RELATIVE_PATH
    assert exit_code == 0
    assert packet_path.exists()
    assert template_path.exists()
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["digitizing_valid"] is False
    assert report["status"] == "digitizing_result_incomplete_stationing_promotion_blocked"


def test_pacuare_a3_digitizing_cli_accepts_complete_payload(tmp_path):
    payload = _complete_digitizing_payload()
    result_path = tmp_path / "filled_pacuare_digitizing_result.json"
    output_path = tmp_path / "accepted_pacuare_digitizing_result.json"
    report_path = tmp_path / "pacuare_digitizing_validation_report.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = validate_pacuare_a3_digitizing_result_main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--result",
            str(result_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert report_path.exists()
    accepted = json.loads(output_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert accepted == payload
    assert report["digitizing_valid"] is True
    assert report["passing_rapid_count"] == 15
    assert report["promotion_permissions"]["can_regenerate_named_rapid_catalog"] is True
    assert report["promotion_permissions"]["can_bind_solver_windows"] is False


def test_pacuare_a3_digitizing_cli_blocks_invalid_payload(tmp_path):
    payload = _complete_digitizing_payload()
    payload["stationing_result_records"][0]["solver_window_enabled"] = True
    result_path = tmp_path / "invalid_pacuare_digitizing_result.json"
    output_path = tmp_path / "accepted_pacuare_digitizing_result.json"
    report_path = tmp_path / "pacuare_digitizing_validation_report.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = validate_pacuare_a3_digitizing_result_main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--result",
            str(result_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    assert report_path.exists()
    assert not output_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["digitizing_valid"] is False
    assert {
        "rapid_name": "Bienvenidos",
        "field": "solver_window_enabled",
        "reason": "solver_binding_requires_later_water_validation",
    } in report["errors"]


def _complete_digitizing_payload() -> dict:
    payload = build_pacuare_a3_digitizing_result_template(REPO_ROOT)
    base_lon = -83.65
    base_lat = 9.85
    for index, record in enumerate(payload["stationing_result_records"]):
        record.update(
            {
                "geometry_type": "Point",
                "geometry_coordinates_wgs84": [
                    round(base_lon + index * 0.002, 6),
                    round(base_lat + index * 0.001, 6),
                ],
                "station_m_on_reviewed_route": float(index * 1000 + 500),
                "stationing_kind": "aerial_interpreted_point",
                "reviewed_route_source": "review/pacuare_reviewed_route.geojson",
                "aerial_or_orthomosaic_source": "imagery/reviewed_orthomosaic_manifest.json",
                "digitized_by": "geospatial reviewer",
                "digitized_on": "2026-07-16",
                "confidence_m": 25.0,
                "guide_reviewer": "pacuare guide reviewer",
                "guide_reviewed_on": "2026-07-16",
                "rights_publication_status": "approved",
                "protected_area_publication_status": "approved",
                "flow_band_source_class": "hypothesis_pending_guide_review",
                "source_evidence": ["imagery/reviewed_orthomosaic_manifest.json"],
                "guide_evidence": ["review/pacuare_guide_stationing_review.json"],
                "stationing_promoted": False,
                "editor_binding_enabled": False,
                "solver_window_enabled": False,
                "notes": "synthetic complete test payload",
            }
        )
    for reviewer in payload["reviewer_signoff"].values():
        reviewer.update(
            {
                "name_or_role": "reviewer",
                "review_date": "2026-07-16",
                "approved": True,
                "evidence": ["review/example_pacuare_digitizing_evidence.json"],
                "notes": "synthetic complete test payload",
            }
        )
    return payload
