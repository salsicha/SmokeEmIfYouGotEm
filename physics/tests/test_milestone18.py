import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

import raftsim.milestone18 as milestone18
from raftsim.analytic_fixtures import write_analytic_fixture_suite
from raftsim.examples.generate_milestone18_constriction_mask_alignment_report import (
    main as generate_constriction_mask_main,
)
from raftsim.examples.generate_milestone18_constriction_lateral_face_flux_report import (
    main as generate_constriction_lateral_face_flux_main,
)
from raftsim.examples.generate_milestone18_constriction_face_source_audit_report import (
    main as generate_constriction_face_source_audit_main,
)
from raftsim.examples.generate_milestone18_constriction_face_state_width_depth_report import (
    main as generate_constriction_face_state_width_depth_main,
)
from raftsim.examples.generate_milestone18_constriction_field_profile_report import (
    main as generate_constriction_field_profile_main,
)
from raftsim.examples.generate_milestone18_constriction_hydrostatic_source_decision_report import (
    main as generate_constriction_hydrostatic_source_decision_main,
)
from raftsim.examples.generate_milestone18_constriction_upstream_edge_balance_report import (
    main as generate_constriction_upstream_edge_balance_main,
)
from raftsim.examples.generate_milestone18_constriction_probe_cross_section_report import (
    main as generate_constriction_probe_cross_section_main,
)
from raftsim.examples.generate_milestone18_constriction_response_timing_report import (
    main as generate_constriction_response_main,
)
from raftsim.examples.generate_milestone18_constriction_shape_timing_report import (
    main as generate_constriction_shape_timing_main,
)
from raftsim.examples.generate_milestone18_constriction_throat_shape_report import (
    main as generate_constriction_throat_main,
)
from raftsim.examples.generate_milestone18_cascading_boundary_correction_report import (
    main as generate_cascading_boundary_correction_main,
)
from raftsim.examples.generate_milestone18_drop_ledge_hydraulic_control_report import (
    main as generate_drop_ledge_hydraulic_control_main,
)
from raftsim.examples.generate_milestone18_failure_triage_matrix import main as generate_triage_main
from raftsim.examples.generate_milestone18_parity_family_retune_report import main as generate_retune_main
from raftsim.examples.generate_milestone18_pin_release_fixture_report import main as generate_pin_release_main
from raftsim.examples.generate_milestone18_remaining_geometry_closure_report import (
    main as generate_remaining_geometry_closure_main,
)
from raftsim.examples.run_milestone18_analytic_retune_guardrail import main as guardrail_main
from raftsim.milestone18 import (
    MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_FIELD_PROFILE_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA,
    MILESTONE18_CONSTRICTION_UPSTREAM_EDGE_BALANCE_REPORT_SCHEMA,
    MILESTONE18_CASCADING_BOUNDARY_CORRECTION_REPORT_SCHEMA,
    MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA,
    MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA,
    MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA,
    MILESTONE18_PIN_RELEASE_REPORT_SCHEMA,
    MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA,
    build_milestone18_constriction_face_source_audit_report,
    build_milestone18_constriction_face_state_width_depth_report,
    build_milestone18_constriction_field_profile_report,
    build_milestone18_constriction_hydrostatic_source_decision_report,
    build_milestone18_constriction_lateral_face_flux_report,
    build_milestone18_constriction_mask_alignment_report,
    build_milestone18_constriction_probe_cross_section_report,
    build_milestone18_constriction_response_timing_report,
    build_milestone18_constriction_shape_timing_report,
    build_milestone18_constriction_throat_shape_report,
    build_milestone18_constriction_upstream_edge_balance_report,
    build_milestone18_cascading_boundary_correction_report,
    build_milestone18_drop_ledge_hydraulic_control_report,
    build_milestone18_failure_triage_matrix,
    build_milestone18_parity_family_retune_report,
    build_milestone18_pin_release_fixture_report,
    build_milestone18_remaining_geometry_closure_report,
    run_milestone18_analytic_retune_guardrail,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _triage_input_reports(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    comparison = _write_json(
        tmp_path / "reports" / "milestone16" / "geoclaw_cpp_comparisons.json",
        {
            "passed": False,
            "comparison_count": 1,
            "threshold_passed_count": 0,
            "threshold_failed_count": 1,
            "records": [
                {
                    "gate_scenario_id": "bed_step",
                    "actual_scenario_id": "bed_step_seed_16",
                    "suite": "canonical",
                    "solver_mode": "reduced",
                    "threshold_passed": False,
                    "failing_checks": ["field_linf", "mass_drift_delta"],
                    "check_values": {
                        "field_linf": {
                            "passed": False,
                            "value": 0.45,
                            "threshold": 0.15,
                            "details": "field mismatch",
                        },
                        "mass_drift_delta": {
                            "passed": False,
                            "value": 0.05,
                            "threshold": 0.02,
                            "details": "mass drift",
                        },
                    },
                    "threshold_report": "outputs/m16cmp/c_step/reduced/threshold_evaluation.json",
                    "comparison_dir": "outputs/m16cmp/c_step/reduced",
                }
            ],
        },
    )
    geometry = _write_json(
        tmp_path / "reports" / "milestone16" / "geometry_validation.json",
        {
            "passed": False,
            "case_count": 1,
            "passed_count": 0,
            "failed_count": 1,
            "cases": [
                {
                    "case_id": "bed_step",
                    "title": "Bed Steps",
                    "passed": False,
                    "evidence": [
                        {
                            "gate_scenario_id": "bed_step",
                            "solver_mode": "reduced",
                            "threshold_passed": False,
                            "failing_checks": ["field_linf", "mass_drift_delta"],
                        }
                    ],
                    "notes": ["Threshold failures remain in: bed_step."],
                }
            ],
        },
    )
    raft = _write_json(
        tmp_path / "reports" / "milestone16" / "raft_coupling_validation.json",
        {
            "passed": False,
            "thresholds": {
                "force_delta_weight_ratio": 1.0,
                "torque_delta_inertia_ratio": 2.5,
                "trajectory_position_delta_m": 0.25,
                "trajectory_velocity_delta_mps": 0.5,
            },
            "comparison_count": 1,
            "passed_count": 0,
            "failed_count": 1,
            "records": [
                {
                    "gate_scenario_id": "boulder_garden",
                    "actual_scenario_id": "boulder_garden_seed_16",
                    "suite": "rafting",
                    "solver_mode": "finite_volume",
                    "case_id": "boulder_impacts",
                    "passed": False,
                    "reference_frame": "outputs/m16g/r_boulder/normalized/frames/frame_0002.npz",
                    "candidate_frame": "outputs/m16cpp/r_boulder/finite_volume/frames/frame_0008.csv",
                    "reference_passed": False,
                    "candidate_passed": False,
                    "feature_outcome_match": False,
                    "force_envelope_outcome_match": False,
                    "force_delta_weight_ratio": 1.5,
                    "torque_delta_inertia_ratio": 0.1,
                    "trajectory_position_delta_m": 0.01,
                    "trajectory_velocity_delta_mps": 0.1,
                    "reference_checks": [{"name": "rock_contact", "passed": False, "value": 0.0, "threshold": 1.0}],
                    "candidate_checks": [{"name": "submerged_depth", "passed": False, "value": 0.0, "threshold": 0.1}],
                    "notes": ["Force delta exceeds the weight-normalized threshold."],
                }
            ],
        },
    )
    full_gate = _write_json(
        tmp_path / "reports" / "milestone16" / "full_cpp_validation_gate.json",
        {
            "passed": False,
            "components": [
                {
                    "component_id": "geoclaw_cpp_comparisons",
                    "title": "GeoClaw/C++ Threshold Comparisons",
                    "source_report": "reports/milestone16/geoclaw_cpp_comparisons.json",
                    "passed": False,
                    "failed_count": 1,
                    "blockers": ["bed_step: GeoClaw/C++ threshold comparison failed"],
                }
            ],
        },
    )
    return comparison, geometry, raft, full_gate


def test_milestone18_failure_triage_matrix_groups_failed_evidence(tmp_path):
    comparison, geometry, raft, full_gate = _triage_input_reports(tmp_path)

    report = build_milestone18_failure_triage_matrix(comparison, geometry, raft, full_gate)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA
    assert payload["decision"] == "ACTION_REQUIRED"
    assert payload["summary"]["by_source_component"]["geoclaw_cpp_comparison"] == 2
    assert payload["summary"]["by_source_component"]["geometry_validation"] == 1
    assert payload["summary"]["by_source_component"]["raft_coupling"] == 5
    assert payload["summary"]["by_source_component"]["full_cpp_validation_gate"] == 1
    assert payload["summary"]["by_scenario_family"]["bed_step"] == 3
    assert payload["summary"]["by_scenario_family"]["boulder_impacts"] == 5

    field_entry = next(entry for entry in payload["entries"] if entry["metric"] == "field_linf")
    assert field_entry["scenario_family"] == "bed_step"
    assert field_entry["likely_root_cause"]
    assert field_entry["retune_lever"]
    assert field_entry["dependency_phase"] == "geometry_parity_thresholds"


def test_generate_milestone18_failure_triage_cli_writes_reports(tmp_path):
    comparison, geometry, raft, full_gate = _triage_input_reports(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "triage.json"
    output_md = tmp_path / "reports" / "milestone18" / "triage.md"

    exit_code = generate_triage_main(
        [
            "--comparison-report",
            str(comparison),
            "--geometry-report",
            str(geometry),
            "--raft-report",
            str(raft),
            "--full-gate-report",
            str(full_gate),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA
    assert payload["summary"]["entry_count"] == 9
    assert "Milestone 18 GeoClaw/C++ Failure Triage Matrix" in output_md.read_text(encoding="utf-8")


def _parity_retune_inputs(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    export_manifest = _write_json(
        tmp_path / "geoclaw" / "manifest.json",
        {
            "schema": "raftsim.geoclaw_export.v1",
            "scenario_id": "uniform_channel_seed_16",
            "boundary_semantics": {
                "bc_lower": ["user", "wall"],
                "bc_upper": ["extrap", "wall"],
                "requires_user_boundary_adapter": True,
            },
        },
    )
    reference_manifest = _write_json(
        tmp_path / "geoclaw" / "normalized" / "manifest.json",
        {
            "schema": "raftsim.geoclaw_normalized_output.v1",
            "scenario_id": "uniform_channel_seed_16",
            "source_export_manifest": "../manifest.json",
        },
    )
    _ = export_manifest

    reports: dict[str, Path] = {}
    for mode, passed, checks, config in (
        (
            "finite_volume",
            True,
            [
                {"name": "field_linf", "passed": True, "value": 0.12, "threshold": 0.15},
                {"name": "slope_linf", "passed": True, "value": 0.02, "threshold": 0.035},
            ],
            {
                "solver_mode": "finite_volume",
                "boundary_mode": "scenario",
                "flux_scheme": "hll",
                "feature_strength_scale": 0.0,
                "roughness_scale": 0.5,
                "bed_slope_source_scale": 0.75,
                "preserve_initial_mass": False,
            },
        ),
        (
            "reduced",
            False,
            [
                {"name": "field_linf", "passed": False, "value": 0.28, "threshold": 0.15},
                {"name": "slope_linf", "passed": False, "value": 0.09, "threshold": 0.035},
            ],
            {
                "solver_mode": "reduced",
                "boundary_mode": "scenario",
                "flux_scheme": "rusanov",
                "feature_strength_scale": 0.0,
                "roughness_scale": 1.0,
                "bed_slope_source_scale": 0.0,
                "preserve_initial_mass": True,
            },
        ),
    ):
        root = tmp_path / "comparisons" / mode
        _write_json(root / "cpp_manifest.json", config)
        _write_json(root / "dual_solver_manifest.json", {"cpp": {"manifest": "cpp_manifest.json"}})
        reports[mode] = _write_json(
            root / "threshold_evaluation.json",
            {"scenario_id": "uniform_channel_seed_16", "passed": passed, "checks": checks},
        )
    return reference_manifest, reports


def _constriction_throat_inputs(tmp_path: Path) -> Path:
    scenario_root = tmp_path / "scenario" / "constriction_seed_18"
    scenario = _write_json(
        scenario_root / "scenario.json",
        {
            "array_files": {"initial_state": "initial_state.npz", "features": "features.json"},
            "grid": {"nx": 3, "ny": 3, "dx": 1.0, "dy": 1.0, "origin_x": 0.0, "origin_y": 0.0},
            "metadata": {"scenario_id": "constriction_seed_18"},
        },
    )
    _ = scenario
    _write_json(
        scenario_root / "features.json",
        {
            "features": [
                {
                    "kind": "constriction",
                    "center": {"x": 1.0, "y": 1.0},
                    "width": 1.0,
                    "length": 4.0,
                    "radius": 0.5,
                    "strength": 2.0,
                    "angle": 0.0,
                }
            ]
        },
    )
    zeros = np.zeros((3, 3), dtype=float)
    np.savez(
        scenario_root / "initial_state.npz",
        depth=np.array([[0.0, 0.05, 0.0], [0.0, 1.0, 0.0], [0.0, 0.05, 0.0]], dtype=float),
        eta=zeros,
        u=np.ones((3, 3), dtype=float),
        v=zeros,
        hu=zeros,
        hv=zeros,
        wet=np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=bool),
    )

    geoclaw_root = tmp_path / "geoclaw" / "normalized"
    geoclaw_frame = geoclaw_root / "frames" / "frame_0002.npz"
    geoclaw_frame.parent.mkdir(parents=True, exist_ok=True)
    geoclaw_h = np.array([[0.0, 0.35, 0.0], [0.0, 1.45, 0.0], [0.0, 0.35, 0.0]], dtype=float)
    np.savez(
        geoclaw_frame,
        h=geoclaw_h,
        eta=geoclaw_h,
        u=np.full((3, 3), 1.2, dtype=float),
        v=np.full((3, 3), 0.1, dtype=float),
        hu=zeros,
        hv=zeros,
        wet=geoclaw_h > 0.0,
        froude=np.full((3, 3), 0.6, dtype=float),
    )
    _write_json(geoclaw_root / "manifest.json", {"scenario_id": "constriction_seed_18", "frames": ["frames/frame_0002.npz"]})

    cpp_root = tmp_path / "cpp" / "constriction_seed_18"
    cpp_frame = cpp_root / "frames" / "frame_0008.csv"
    cpp_frame.parent.mkdir(parents=True, exist_ok=True)
    rows = ["row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude"]
    cpp_h = np.array([[0.0, 0.02, 0.0], [0.0, 0.95, 0.0], [0.0, 0.02, 0.0]], dtype=float)
    cpp_v = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]], dtype=float)
    for row_index in range(3):
        for col_index in range(3):
            h = cpp_h[row_index, col_index]
            v = cpp_v[row_index, col_index]
            rows.append(
                f"{row_index},{col_index},{col_index},{row_index},{h},{h},1.8,{v},0,0,{1 if h > 0 else 0},0,0,1,1.4"
            )
    cpp_frame.write_text("\n".join(rows) + "\n", encoding="utf-8")
    _write_json(cpp_root / "manifest.json", {"scenario_id": "constriction_seed_18", "frames": ["frames/frame_0008.csv"]})

    return _write_json(
        tmp_path / "comparison" / "dual_solver_manifest.json",
        {
            "scenario_id": "constriction_seed_18",
            "scenario_package": "../scenario/constriction_seed_18",
            "geoclaw": {"manifest": "../geoclaw/normalized/manifest.json"},
            "cpp": {"manifest": "../cpp/constriction_seed_18/manifest.json"},
        },
    )


def test_milestone18_constriction_throat_shape_report_records_width_depth_deltas(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)

    report = build_milestone18_constriction_throat_shape_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["throat_column_index"] == 1
    assert payload["center_row_index"] == 1
    assert payload["summary"]["cpp_center_depth_delta_m"] == -0.5
    assert payload["summary"]["cpp_wet_width_delta_m"] == -2.0
    assert "width/depth mapping" in payload["next_levers"][0]
    assert any("wet width" in reason for reason in payload["blocked_reasons"])


def test_generate_milestone18_constriction_throat_shape_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_throat.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_throat.md"

    exit_code = generate_constriction_throat_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Throat Shape Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_mask_alignment_report_records_column_mismatch(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)

    report = build_milestone18_constriction_mask_alignment_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["domain_mask_mismatch_count"] == 2
    assert payload["summary"]["domain_mask_mismatch_fraction"] == 2 / 9
    assert payload["summary"]["max_abs_wet_width_delta_m"] == 2.0
    worst_column = payload["summary"]["worst_columns"][0]
    assert worst_column["column_index"] == 1
    assert worst_column["mask_mismatch_count"] == 2
    assert worst_column["first_wet_row_delta"] == 1
    assert worst_column["last_wet_row_delta"] == -1
    assert "wet-band span" in payload["next_levers"][0]


def test_generate_milestone18_constriction_mask_alignment_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_mask.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_mask.md"

    exit_code = generate_constriction_mask_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Mask Alignment Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_response_timing_report_records_zone_mass_timing(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)

    report = build_milestone18_constriction_response_timing_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["zones"]["constriction_throat"] == [1]
    assert payload["summary"]["max_abs_final_mass_delta_m3"] > 1.0
    throat_delta = next(delta for delta in payload["zone_deltas"] if delta["zone_id"] == "constriction_throat")
    assert throat_delta["final_mass_delta_m3"] < -1.0
    assert "water volume" in payload["next_levers"][0]


def test_generate_milestone18_constriction_response_timing_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_throat_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_response.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_response.md"

    exit_code = generate_constriction_response_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Response Timing Diagnostic" in output_md.read_text(encoding="utf-8")


def _constriction_shape_timing_inputs(tmp_path: Path) -> Path:
    dual_manifest = _constriction_throat_inputs(tmp_path)
    comparison_root = dual_manifest.parent
    geoclaw_frame = tmp_path / "geoclaw" / "normalized" / "frames" / "frame_0002.npz"
    cpp_frame = tmp_path / "cpp" / "constriction_seed_18" / "frames" / "frame_0008.csv"
    _write_json(
        comparison_root / "field_comparison.json",
        {
            "scenario_id": "constriction_seed_18",
            "frame_comparisons": [
                {
                    "label": "final",
                    "reference_frame": str(geoclaw_frame),
                    "cpp_frame": str(cpp_frame),
                    "field_errors": [],
                    "slope_errors": [],
                    "wet_mismatch_fraction": 2 / 9,
                }
            ],
        },
    )
    _write_json(
        comparison_root / "probe_comparison.json",
        {
            "scenario_id": "constriction_seed_18",
            "point_probes": [
                {
                    "sample_id": "midstream_center",
                    "kind": "point",
                    "field_errors": [
                        {"field": "h", "linf": 0.2},
                        {"field": "hv", "linf": 1.4},
                    ],
                }
            ],
            "cross_sections": [
                {
                    "sample_id": "mid_cross_section",
                    "kind": "cross_section",
                    "field_errors": [
                        {"field": "h", "linf": 0.4},
                        {"field": "v", "linf": 1.7},
                    ],
                }
            ],
        },
    )
    _write_json(
        comparison_root / "threshold_evaluation.json",
        {
            "scenario_id": "constriction_seed_18",
            "passed": False,
            "thresholds": {
                "max_field_linf": 0.25,
                "max_slope_linf": 0.25,
                "max_probe_linf": 0.25,
                "max_cross_section_linf": 0.25,
            },
        },
    )
    return dual_manifest


def test_milestone18_constriction_shape_timing_report_records_worst_shape_samples(tmp_path):
    dual_manifest = _constriction_shape_timing_inputs(tmp_path)

    report = build_milestone18_constriction_shape_timing_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["max_cross_section_linf"] == 1.7
    worst_field = payload["samples"]["field"][0]
    assert worst_field["field"] == "v"
    assert worst_field["column_index"] == 1
    assert worst_field["zone_id"] == "constriction_throat"
    assert payload["samples"]["probe"][0]["field"] == "hv"
    assert any("cross-section" in reason for reason in payload["blocked_reasons"])
    assert "mid-cross-section" in " ".join(payload["next_levers"])


def test_generate_milestone18_constriction_shape_timing_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_shape_timing_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_shape_timing.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_shape_timing.md"

    exit_code = generate_constriction_shape_timing_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Shape/Timing Diagnostic" in output_md.read_text(encoding="utf-8")


def _constriction_probe_cross_section_inputs(tmp_path: Path) -> Path:
    dual_manifest = _constriction_shape_timing_inputs(tmp_path)
    geoclaw_root = tmp_path / "geoclaw" / "normalized"
    cpp_root = tmp_path / "cpp" / "constriction_seed_18"

    geoclaw_probe_dir = geoclaw_root / "probes"
    cpp_probe_dir = cpp_root / "probes"
    geoclaw_probe_dir.mkdir(parents=True, exist_ok=True)
    cpp_probe_dir.mkdir(parents=True, exist_ok=True)
    geoclaw_probe = geoclaw_probe_dir / "midstream_center.csv"
    cpp_probe = cpp_probe_dir / "midstream_center.csv"
    geoclaw_probe.write_text(
        "\n".join(
            [
                "time,h,eta,u,v,hu,hv,wet,froude",
                "0,1.0,1.0,1.0,0.0,1.0,0.0,1,0.3",
                "3,1.0,1.0,1.0,1.2,1.0,1.5,1,0.5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cpp_probe.write_text(
        "\n".join(
            [
                "time,h,eta,u,v,hu,hv,wet,froude",
                "0,1.0,1.0,1.0,0.0,1.0,0.0,1,0.3",
                "1.5,1.0,1.0,1.0,0.0,1.0,0.0,1,0.3",
                "3,1.0,1.0,1.0,-0.8,1.0,-1.0,1,0.4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    geoclaw_cross_dir = geoclaw_root / "cross_sections"
    cpp_cross_dir = cpp_root / "cross_sections"
    geoclaw_cross_dir.mkdir(parents=True, exist_ok=True)
    cpp_cross_dir.mkdir(parents=True, exist_ok=True)
    times = np.array([0.0, 3.0], dtype=float)
    distance = np.array([-1.0, 0.0, 1.0], dtype=float)
    h = np.ones((2, 3), dtype=float)
    u = np.ones((2, 3), dtype=float)
    v = np.array([[0.0, 0.0, 0.0], [0.0, 0.5, 2.8]], dtype=float)
    froude = np.array([[0.3, 0.3, 0.3], [0.3, 0.7, 2.0]], dtype=float)
    np.savez(
        geoclaw_cross_dir / "mid_cross_section.npz",
        times=times,
        distance=distance,
        h=h,
        eta=h,
        u=u,
        v=v,
        froude=froude,
    )
    rows = ["time,distance,h,eta,u,v,froude"]
    for time_index, time in enumerate(times):
        for distance_index, dist in enumerate(distance):
            candidate_v = -0.2 if (time_index, distance_index) == (1, 2) else v[time_index, distance_index]
            rows.append(f"{time},{dist},1.0,1.0,1.0,{candidate_v},0.6")
    (cpp_cross_dir / "mid_cross_section.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    geoclaw_manifest = json.loads((geoclaw_root / "manifest.json").read_text(encoding="utf-8"))
    geoclaw_manifest.update(
        {
            "probes": ["probes/midstream_center.csv"],
            "probe_manifest": [
                {
                    "probe_id": "midstream_center",
                    "kind": "point",
                    "sample_count": 2,
                    "metadata": {"position": [1.0, 1.0], "column": 1, "row": 1},
                }
            ],
            "cross_sections": ["cross_sections/mid_cross_section.npz"],
            "cross_section_manifest": [
                {
                    "probe_id": "mid_cross_section",
                    "time_count": 2,
                    "distance_count": 3,
                    "metadata": {"position": [1.0, 1.0], "normal": [0.0, 1.0], "length": 2.0},
                }
            ],
        }
    )
    _write_json(geoclaw_root / "manifest.json", geoclaw_manifest)

    cpp_manifest = json.loads((cpp_root / "manifest.json").read_text(encoding="utf-8"))
    cpp_manifest.update(
        {
            "probes": ["probes/midstream_center.csv"],
            "cross_sections": ["cross_sections/mid_cross_section.csv"],
        }
    )
    _write_json(cpp_root / "manifest.json", cpp_manifest)
    return dual_manifest


def test_milestone18_constriction_probe_cross_section_report_records_raw_locations(tmp_path):
    dual_manifest = _constriction_probe_cross_section_inputs(tmp_path)

    report = build_milestone18_constriction_probe_cross_section_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    worst = payload["summary"]["worst_overall"][0]
    assert worst["category"] == "cross_section"
    assert worst["field"] == "v"
    assert worst["time_s"] == 3.0
    assert worst["distance_m"] == 1.0
    assert worst["row_index"] == 2
    assert worst["column_index"] == 1
    assert worst["zone_id"] == "constriction_throat"
    assert payload["samples"]["probe"][0]["field"] == "hv"
    assert "Cross-stream velocity" in " ".join(payload["blocked_reasons"])


def test_generate_milestone18_constriction_probe_cross_section_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_probe_cross_section_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_probe_cross_section.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_probe_cross_section.md"

    exit_code = generate_constriction_probe_cross_section_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Probe/Cross-Section Diagnostic" in output_md.read_text(encoding="utf-8")


def _constriction_lateral_face_flux_inputs(tmp_path: Path) -> Path:
    scenario_root = tmp_path / "scenario" / "constriction_seed_18"
    _write_json(
        scenario_root / "scenario.json",
        {
            "array_files": {"initial_state": "initial_state.npz", "features": "features.json"},
            "grid": {"nx": 4, "ny": 4, "dx": 1.0, "dy": 1.0, "origin_x": 0.0, "origin_y": 0.0},
            "metadata": {"scenario_id": "constriction_seed_18"},
        },
    )
    _write_json(
        scenario_root / "features.json",
        {
            "features": [
                {
                    "kind": "constriction",
                    "center": {"x": 2.0, "y": 1.5},
                    "width": 1.0,
                    "length": 3.0,
                    "radius": 0.5,
                    "strength": 2.0,
                    "angle": 0.0,
                }
            ]
        },
    )
    initial_h = np.zeros((4, 4), dtype=float)
    initial_h[1:3, 0] = 1.0
    initial_h[1:3, 1] = 1.0
    initial_h[1, 2] = 1.0
    initial_h[1:3, 3] = 1.0
    zeros = np.zeros((4, 4), dtype=float)
    bed = np.zeros((4, 4), dtype=float)
    bed[2:, :] = 0.15
    np.save(scenario_root / "bed.npy", bed)
    np.savez(
        scenario_root / "initial_state.npz",
        depth=initial_h,
        eta=initial_h + bed,
        u=np.ones((4, 4), dtype=float),
        v=zeros,
        hu=initial_h,
        hv=zeros,
        wet=initial_h > 0.0,
    )

    geoclaw_root = tmp_path / "geoclaw" / "normalized"
    geoclaw_frame = geoclaw_root / "frames" / "frame_0002.npz"
    geoclaw_frame.parent.mkdir(parents=True, exist_ok=True)
    geoclaw_h = initial_h.copy()
    geoclaw_h[0, 1] = 0.3
    geoclaw_v = zeros.copy()
    geoclaw_v[0, 1] = 3.0
    geoclaw_v[1, 1] = 0.8
    geoclaw_v[2, 1] = -3.0
    np.savez(
        geoclaw_frame,
        h=geoclaw_h,
        eta=geoclaw_h + bed,
        u=np.ones((4, 4), dtype=float),
        v=geoclaw_v,
        hu=geoclaw_h,
        hv=geoclaw_h * geoclaw_v,
        wet=geoclaw_h > 0.0,
        froude=np.ones((4, 4), dtype=float),
    )
    _write_json(geoclaw_root / "manifest.json", {"scenario_id": "constriction_seed_18", "frames": ["frames/frame_0002.npz"]})

    cpp_root = tmp_path / "cpp" / "constriction_seed_18"
    cpp_frame = cpp_root / "frames" / "frame_0008.csv"
    cpp_frame.parent.mkdir(parents=True, exist_ok=True)
    cpp_diagnostics = cpp_root / "diagnostics" / "constriction_y_face_flux_source_audit.csv"
    cpp_diagnostics.parent.mkdir(parents=True, exist_ok=True)
    cpp_h = geoclaw_h.copy()
    cpp_v = zeros.copy()
    cpp_v[0, 1] = -0.2
    cpp_v[1, 1] = -0.1
    cpp_v[2, 1] = -0.05
    rows = ["row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude"]
    for row_index in range(4):
        for col_index in range(4):
            h = cpp_h[row_index, col_index]
            v = cpp_v[row_index, col_index]
            rows.append(
                f"{row_index},{col_index},{col_index},{row_index},{h},{h + bed[row_index, col_index]},1.0,{v},{h},{h * v},{1 if h > 0 else 0},0,0,1,1.0"
            )
    cpp_frame.write_text("\n".join(rows) + "\n", encoding="utf-8")
    cpp_diagnostics.write_text(
        "\n".join(
            [
                "face_role,column_index,south_row_index,north_row_index,time_s,base_flux_h_m3ps,post_left_flux_h_m3ps,hydro_left_source_hv_m3ps2,hydro_right_source_hv_m3ps2,constriction_left_source_h_m3ps,constriction_right_source_h_m3ps,south_cell_bed_slope_source_hv_per_s,north_cell_bed_slope_source_hv_per_s,hydrostatic_face_source_enabled,constriction_face_source_applied",
                "lower_edge_face,1,0,1,6.0,-0.1,-0.1,0,0,0,0,-0.2,-0.2,0,0",
                "upper_edge_face,1,1,2,6.0,-0.2,-0.2,0,0,0.05,0.05,-0.1,-0.1,0,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        cpp_root / "manifest.json",
        {
            "scenario_id": "constriction_seed_18",
            "frames": ["frames/frame_0008.csv"],
            "constriction_y_face_flux_source_audit": {
                "present": True,
                "path": "diagnostics/constriction_y_face_flux_source_audit.csv",
            },
            "diagnostics": ["diagnostics/constriction_y_face_flux_source_audit.csv"],
        },
    )

    return _write_json(
        tmp_path / "comparison" / "dual_solver_manifest.json",
        {
            "scenario_id": "constriction_seed_18",
            "scenario_package": "../scenario/constriction_seed_18",
            "geoclaw": {"manifest": "../geoclaw/normalized/manifest.json"},
            "cpp": {"manifest": "../cpp/constriction_seed_18/manifest.json"},
        },
    )


def test_milestone18_constriction_lateral_face_flux_report_records_edge_signs(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)

    report = build_milestone18_constriction_lateral_face_flux_report(dual_manifest, top_n=8)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["sign_mismatch_count"] >= 1
    assert payload["summary"]["opposition_mismatch_count"] >= 1
    worst = payload["summary"]["worst_samples"][0]
    assert worst["face_role"] == "lower_edge_face"
    assert worst["reference_sign"] == 1
    assert worst["candidate_sign"] == -1
    assert any(pair["column_index"] == 1 and pair["reference_opposed_edges"] for pair in payload["edge_pair_summary"])
    assert "opposite-signed" in " ".join(payload["blocked_reasons"])


def test_generate_milestone18_constriction_lateral_face_flux_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_lateral_face_flux.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_lateral_face_flux.md"

    exit_code = generate_constriction_lateral_face_flux_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Lateral Face Flux Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_face_source_audit_records_flux_source_balance(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)

    report = build_milestone18_constriction_face_source_audit_report(dual_manifest, top_n=8)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "not internal per-timestep Riemann telemetry" in payload["diagnostic_scope"]
    assert payload["summary"]["volume_sign_mismatch_count"] >= 1
    assert payload["summary"]["x_momentum_sign_mismatch_count"] >= 1
    assert payload["summary"]["opposition_mismatch_count"] >= 1
    assert payload["summary"]["cpp_internal_audit_sample_count"] == 2
    assert payload["summary"]["cpp_internal_source_applied_count"] == 1
    assert payload["summary"]["cpp_internal_face_state_reconstruction_applied_count"] == 0
    assert payload["summary"]["cpp_internal_post_source_sign_mismatch_count"] >= 1
    assert payload["summary"]["cpp_internal_hydrostatic_face_source_enabled_count"] == 0
    assert payload["summary"]["cpp_internal_constriction_source_split_applied_count"] == 0
    assert payload["summary"]["max_abs_balance_delta_m3ps2"] > 0.0
    worst = payload["summary"]["worst_samples"][0]
    assert worst["face_role"] == "lower_edge_face"
    assert worst["reference_volume_sign"] == 1
    assert worst["candidate_volume_sign"] == -1
    assert "bed_source_delta_m3ps2" in worst
    assert payload["cpp_internal_audit"][0]["source_report"].endswith(
        "diagnostics/constriction_y_face_flux_source_audit.csv"
    )
    assert any(pair["column_index"] == 1 and pair["reference_opposed_edges"] for pair in payload["edge_pair_summary"])
    assert "face/source" in " ".join(payload["next_levers"])


def _passing_face_source_audit_sample() -> milestone18.Milestone18ConstrictionFaceSourceAuditSample:
    return milestone18.Milestone18ConstrictionFaceSourceAuditSample(
        face_role="lower_edge_face",
        column_index=0,
        south_row_index=1,
        north_row_index=2,
        x_m=0.0,
        y_face_m=-4.0,
        bed_step_m=-2.0,
        reference_eta_step_m=0.0,
        candidate_eta_step_m=0.0,
        reference_mean_h=1.0,
        candidate_mean_h=1.0,
        reference_mean_u=1.0,
        candidate_mean_u=1.0,
        reference_mean_v=1.0,
        candidate_mean_v=1.0,
        reference_volume_flux_m3ps=1.0,
        candidate_volume_flux_m3ps=1.0,
        volume_flux_delta_m3ps=0.0,
        abs_volume_flux_delta_m3ps=0.0,
        flux_delta_threshold_m3ps=0.25,
        volume_ratio_to_threshold=0.0,
        reference_volume_sign=1,
        candidate_volume_sign=1,
        volume_sign_matches=True,
        reference_x_momentum_flux_proxy_m3ps2=1.0,
        candidate_x_momentum_flux_proxy_m3ps2=1.0,
        x_momentum_flux_delta_m3ps2=0.0,
        abs_x_momentum_flux_delta_m3ps2=0.0,
        reference_x_momentum_sign=1,
        candidate_x_momentum_sign=1,
        x_momentum_sign_matches=True,
        reference_normal_momentum_flux_proxy_m3ps2=1.0,
        candidate_normal_momentum_flux_proxy_m3ps2=1.0,
        normal_momentum_flux_delta_m3ps2=0.0,
        abs_normal_momentum_flux_delta_m3ps2=0.0,
        reference_bed_source_proxy_m3ps2=1.0,
        candidate_bed_source_proxy_m3ps2=1.0,
        bed_source_delta_m3ps2=0.0,
        abs_bed_source_delta_m3ps2=0.0,
        reference_flux_source_balance_proxy_m3ps2=1.0,
        candidate_flux_source_balance_proxy_m3ps2=1.0,
        balance_delta_m3ps2=0.0,
        abs_balance_delta_m3ps2=0.0,
        balance_delta_threshold_m3ps2=0.75,
        balance_ratio_to_threshold=0.0,
    )


def test_milestone18_face_source_internal_sign_mismatches_are_diagnostic_after_final_frame_passes():
    sample = _passing_face_source_audit_sample()

    reasons = milestone18._face_source_audit_blocked_reasons(
        (sample,),
        ({"matches_reference_opposition": True},),
        ({"post_left_sign_matches": False, "hydrostatic_face_source_enabled": True},),
    )

    assert reasons == ()


def test_milestone18_face_source_internal_sign_mismatch_blocks_with_final_frame_failure():
    failed_sample = replace(_passing_face_source_audit_sample(), volume_sign_matches=False)

    reasons = milestone18._face_source_audit_blocked_reasons(
        (failed_sample,),
        ({"matches_reference_opposition": True},),
        ({"post_left_sign_matches": False, "hydrostatic_face_source_enabled": True},),
    )

    assert any("internal y-face" in reason for reason in reasons)


def test_generate_milestone18_constriction_face_source_audit_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.md"

    exit_code = generate_constriction_face_source_audit_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Face/Source Audit" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_face_state_width_depth_report_separates_geometry_from_face_state(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)

    report = build_milestone18_constriction_face_state_width_depth_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["face_state_blocker_count"] >= 1
    assert payload["summary"]["face_sign_mismatch_count"] >= 1
    assert payload["summary"]["edge_opposition_mismatch_count"] >= 1
    assert payload["summary"]["width_mapping_blocker_count"] == 0
    assert payload["summary"]["bank_alignment_blocker_count"] == 0
    assert "geometry_aware_face_state_reconstruction" in payload["summary"]["recommended_levers"]
    worst = payload["summary"]["worst_face_state_samples"][0]
    assert worst["face_role"] == "lower_edge_face"
    assert worst["reference_volume_sign"] == 1
    assert worst["candidate_volume_sign"] == -1
    assert worst["recommended_solver_lever"] == "geometry_aware_face_state_reconstruction"
    assert "source split alone" in " ".join(payload["next_levers"])


def test_generate_milestone18_constriction_face_state_width_depth_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_face_state_width_depth.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_face_state_width_depth.md"

    exit_code = generate_constriction_face_state_width_depth_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Face-State Width/Depth Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_field_profile_report_records_profile_blockers(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)

    report = build_milestone18_constriction_field_profile_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FIELD_PROFILE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["max_abs_v_delta"] > 0.25
    worst = payload["summary"]["worst_cells"][0]
    assert worst["field"] == "v"
    assert worst["zone_id"] == "upstream_approach"
    assert worst["profile_role"] == "lower_shelf"
    assert any(
        profile_bin["profile_role"] == "lower_shelf" and profile_bin["max_abs_v_delta"] > 0.25
        for profile_bin in payload["profile_bins"]
    )
    assert "Cross-stream" in " ".join(payload["blocked_reasons"])
    assert "feature forcing off" in " ".join(payload["next_levers"])


def test_generate_milestone18_constriction_field_profile_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "constriction_field_profile.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_field_profile.md"

    exit_code = generate_constriction_field_profile_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_FIELD_PROFILE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Field-Profile Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_upstream_edge_balance_joins_focused_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    face_state_report = build_milestone18_constriction_face_state_width_depth_report(dual_manifest)
    face_state_json = face_state_report.write_json(
        tmp_path / "reports" / "milestone18" / "constriction_face_state_width_depth.json"
    )
    face_source_report = build_milestone18_constriction_face_source_audit_report(dual_manifest, top_n=8)
    face_source_json = face_source_report.write_json(
        tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.json"
    )

    report = build_milestone18_constriction_upstream_edge_balance_report(face_state_json, face_source_json)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_UPSTREAM_EDGE_BALANCE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["target_sample_count"] >= 1
    assert payload["summary"]["source_balance_blocker_count"] >= 1
    assert payload["summary"]["paired_edge_opposition_mismatch_count"] >= 1
    primary = payload["summary"]["primary_target"]
    assert primary["face_role"] == "lower_edge_face"
    assert primary["native_post_left_flux_h_m3ps"] == -0.1
    assert primary["recommended_solver_lever"] in {
        "upstream_edge_y_face_flux_source_balance",
        "upstream_edge_width_depth_flux_balance",
    }
    assert "feature forcing off" in " ".join(payload["next_levers"])


def test_milestone18_constriction_upstream_edge_balance_empty_target_queue_passes():
    reasons = milestone18._constriction_upstream_edge_balance_blocked_reasons(
        (),
        ({"matches_reference_opposition": True},),
    )
    levers = milestone18._constriction_upstream_edge_balance_next_levers(
        (),
        ({"matches_reference_opposition": True},),
    )

    assert reasons == ()
    assert "guardrails" in levers[0]


def test_generate_milestone18_constriction_upstream_edge_balance_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    face_state_json = build_milestone18_constriction_face_state_width_depth_report(dual_manifest).write_json(
        tmp_path / "reports" / "milestone18" / "constriction_face_state_width_depth.json"
    )
    face_source_json = build_milestone18_constriction_face_source_audit_report(dual_manifest, top_n=8).write_json(
        tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.json"
    )
    output_json = tmp_path / "reports" / "milestone18" / "constriction_upstream_edge_balance.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_upstream_edge_balance.md"

    exit_code = generate_constriction_upstream_edge_balance_main(
        [
            "--face-state-width-depth-report",
            str(face_state_json),
            "--face-source-audit-report",
            str(face_source_json),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_UPSTREAM_EDGE_BALANCE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Constriction Upstream Edge Balance Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_constriction_hydrostatic_source_decision_records_next_experiment(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    audit_report = build_milestone18_constriction_face_source_audit_report(dual_manifest, top_n=8)
    audit_json = audit_report.write_json(tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.json")

    report = build_milestone18_constriction_hydrostatic_source_decision_report(audit_json)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA
    assert payload["decision"] == "TEST_REQUIRED"
    assert payload["passed"] is False
    assert payload["summary"]["cpp_internal_audit_sample_count"] == 2
    assert payload["summary"]["cpp_internal_hydrostatic_face_source_enabled_count"] == 0
    assert payload["summary"]["cpp_internal_constriction_source_split_applied_count"] == 0
    assert payload["target_face"]["face_role"] == "lower_edge_face"
    assert payload["target_face"]["post_left_sign_matches"] is False
    assert "feature/gameplay forcing disabled" in " ".join(payload["acceptance_constraints"])
    assert "finite-volume face/source update" in " ".join(payload["next_levers"])


def test_generate_milestone18_constriction_hydrostatic_source_decision_cli_writes_reports(tmp_path):
    dual_manifest = _constriction_lateral_face_flux_inputs(tmp_path)
    audit_report = build_milestone18_constriction_face_source_audit_report(dual_manifest, top_n=8)
    audit_json = audit_report.write_json(tmp_path / "reports" / "milestone18" / "constriction_face_source_audit.json")
    output_json = tmp_path / "reports" / "milestone18" / "constriction_hydrostatic_source_decision.json"
    output_md = tmp_path / "reports" / "milestone18" / "constriction_hydrostatic_source_decision.md"

    exit_code = generate_constriction_hydrostatic_source_decision_main(
        [
            "--face-source-audit-report",
            str(audit_json),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA
    assert payload["decision"] == "TEST_REQUIRED"
    assert "Hydrostatic Source Decision" in output_md.read_text(encoding="utf-8")


def _drop_ledge_hydraulic_control_inputs(tmp_path: Path) -> Path:
    scenario_root = tmp_path / "scenario" / "drop_ledge_seed_18"
    _write_json(
        scenario_root / "scenario.json",
        {
            "array_files": {"initial_state": "initial_state.npz", "features": "features.json"},
            "grid": {"nx": 5, "ny": 3, "dx": 1.0, "dy": 1.0, "origin_x": 0.0, "origin_y": 0.0},
            "metadata": {"scenario_id": "drop_ledge_seed_18"},
        },
    )
    _write_json(
        scenario_root / "features.json",
        {
            "features": [
                {
                    "kind": "ledge",
                    "center": {"x": 2.0, "y": 1.0},
                    "width": 2.0,
                    "length": 3.0,
                    "radius": 0.0,
                    "strength": 0.45,
                    "angle": 0.0,
                },
                {
                    "kind": "wave_train",
                    "center": {"x": 3.5, "y": 1.0},
                    "width": 2.0,
                    "length": 2.0,
                    "radius": 0.5,
                    "strength": 0.65,
                    "angle": 0.0,
                },
            ]
        },
    )
    h = np.ones((3, 5), dtype=float)
    zeros = np.zeros((3, 5), dtype=float)
    np.savez(
        scenario_root / "initial_state.npz",
        depth=h,
        eta=h,
        u=np.ones((3, 5), dtype=float),
        v=zeros,
        hu=h,
        hv=zeros,
        wet=h > 0.0,
    )

    geoclaw_root = tmp_path / "geoclaw" / "normalized"
    geoclaw_frame = geoclaw_root / "frames" / "frame_0002.npz"
    geoclaw_frame.parent.mkdir(parents=True, exist_ok=True)
    geoclaw_h = np.ones((3, 5), dtype=float)
    geoclaw_h[:, 2] = 1.35
    geoclaw_eta = geoclaw_h + 0.1
    geoclaw_u = np.full((3, 5), 1.2, dtype=float)
    geoclaw_froude = np.full((3, 5), 0.45, dtype=float)
    np.savez(
        geoclaw_frame,
        h=geoclaw_h,
        eta=geoclaw_eta,
        u=geoclaw_u,
        v=zeros,
        hu=geoclaw_h * geoclaw_u,
        hv=zeros,
        wet=geoclaw_h > 0.0,
        normal_x=zeros,
        normal_y=zeros,
        normal_z=np.ones((3, 5), dtype=float),
        froude=geoclaw_froude,
    )
    _write_json(
        geoclaw_root / "manifest.json",
        {
            "scenario_id": "drop_ledge_seed_18",
            "frames": ["frames/frame_0002.npz"],
            "probes": ["probes/control_probe.csv"],
            "probe_manifest": [
                {
                    "probe_id": "control_probe",
                    "kind": "point",
                    "sample_count": 2,
                    "metadata": {"position": [2.0, 1.0], "column": 2, "row": 1},
                }
            ],
            "cross_sections": ["cross_sections/control_section.npz"],
            "cross_section_manifest": [
                {
                    "probe_id": "control_section",
                    "time_count": 2,
                    "distance_count": 3,
                    "metadata": {"position": [2.0, 1.0], "normal": [0.0, 1.0], "length": 2.0},
                }
            ],
        },
    )

    cpp_root = tmp_path / "cpp" / "drop_ledge_seed_18"
    cpp_frame = cpp_root / "frames" / "frame_0008.csv"
    cpp_frame.parent.mkdir(parents=True, exist_ok=True)
    cpp_h = geoclaw_h.copy()
    cpp_h[1, 2] = 0.55
    rows = ["row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude"]
    for row_index in range(3):
        for col_index in range(5):
            h_value = cpp_h[row_index, col_index]
            eta = h_value + 0.1
            u = 1.2
            rows.append(
                f"{row_index},{col_index},{col_index},{row_index},{h_value},{eta},{u},0.0,{h_value * u},0.0,1,0,0,1,0.45"
            )
    cpp_frame.write_text("\n".join(rows) + "\n", encoding="utf-8")
    _write_json(
        cpp_root / "manifest.json",
        {
            "scenario_id": "drop_ledge_seed_18",
            "frames": ["frames/frame_0008.csv"],
            "probes": ["probes/control_probe.csv"],
            "cross_sections": ["cross_sections/control_section.csv"],
        },
    )

    geoclaw_probe_dir = geoclaw_root / "probes"
    cpp_probe_dir = cpp_root / "probes"
    geoclaw_probe_dir.mkdir(parents=True, exist_ok=True)
    cpp_probe_dir.mkdir(parents=True, exist_ok=True)
    (geoclaw_probe_dir / "control_probe.csv").write_text(
        "\n".join(
            [
                "time,h,eta,u,v,hu,hv,wet,froude",
                "0,1.0,1.1,1.0,0.0,1.0,0.0,1,0.3",
                "3,1.35,1.45,1.2,0.0,1.62,0.0,1,0.45",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (cpp_probe_dir / "control_probe.csv").write_text(
        "\n".join(
            [
                "time,h,eta,u,v,hu,hv,wet,froude",
                "0,1.0,1.1,1.0,0.0,1.0,0.0,1,0.3",
                "3,0.55,0.65,1.2,0.0,0.66,0.0,1,0.45",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    geoclaw_cross_dir = geoclaw_root / "cross_sections"
    cpp_cross_dir = cpp_root / "cross_sections"
    geoclaw_cross_dir.mkdir(parents=True, exist_ok=True)
    cpp_cross_dir.mkdir(parents=True, exist_ok=True)
    times = np.array([0.0, 3.0], dtype=float)
    distance = np.array([-1.0, 0.0, 1.0], dtype=float)
    cross_h = np.ones((2, 3), dtype=float)
    cross_eta = cross_h + 0.1
    cross_u = np.ones((2, 3), dtype=float)
    cross_v = np.zeros((2, 3), dtype=float)
    cross_froude = np.full((2, 3), 0.3, dtype=float)
    cross_h[1, 1] = 1.35
    cross_eta[1, 1] = 1.45
    cross_u[1, :] = 1.2
    cross_froude[1, :] = 0.45
    np.savez(
        geoclaw_cross_dir / "control_section.npz",
        times=times,
        distance=distance,
        h=cross_h,
        eta=cross_eta,
        u=cross_u,
        v=cross_v,
        froude=cross_froude,
    )
    cross_rows = ["time,distance,h,eta,u,v,froude"]
    for time_index, time in enumerate(times):
        for distance_index, dist in enumerate(distance):
            h_value = 0.65 if (time_index, distance_index) == (1, 1) else cross_h[time_index, distance_index]
            cross_rows.append(f"{time},{dist},{h_value},{h_value + 0.1},{cross_u[time_index, distance_index]},0.0,0.45")
    (cpp_cross_dir / "control_section.csv").write_text("\n".join(cross_rows) + "\n", encoding="utf-8")

    comparison_root = tmp_path / "comparison"
    _write_json(
        comparison_root / "threshold_evaluation.json",
        {
            "scenario_id": "drop_ledge_seed_18",
            "passed": False,
            "thresholds": {
                "max_field_linf": 0.25,
                "max_slope_linf": 0.25,
                "max_probe_linf": 0.25,
                "max_cross_section_linf": 0.25,
            },
            "checks": [
                {"name": "field_linf", "passed": False, "value": 0.8, "threshold": 0.25},
                {"name": "probe_linf", "passed": False, "value": 0.96, "threshold": 0.25},
                {"name": "cross_section_linf", "passed": False, "value": 0.7, "threshold": 0.25},
                {"name": "mass_drift_delta", "passed": True, "value": 0.01, "threshold": 0.05},
                {"name": "energy_change_delta", "passed": True, "value": 0.02, "threshold": 0.25},
                {"name": "froude_delta", "passed": True, "value": 0.1, "threshold": 0.5},
            ],
        },
    )
    return _write_json(
        comparison_root / "dual_solver_manifest.json",
        {
            "scenario_id": "drop_ledge_seed_18",
            "scenario_package": "../scenario/drop_ledge_seed_18",
            "geoclaw": {"manifest": "../geoclaw/normalized/manifest.json"},
            "cpp": {"manifest": "../cpp/drop_ledge_seed_18/manifest.json"},
        },
    )


def test_milestone18_drop_ledge_hydraulic_control_report_records_control_blockers(tmp_path):
    dual_manifest = _drop_ledge_hydraulic_control_inputs(tmp_path)

    report = build_milestone18_drop_ledge_hydraulic_control_report(dual_manifest)
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["zones"]["hydraulic_control"] == [1, 2, 3]
    assert payload["summary"]["max_final_field_linf"] == pytest.approx(0.96)
    assert payload["summary"]["max_probe_linf"] == pytest.approx(0.96)
    worst_field = payload["summary"]["worst_final_field_samples"][0]
    assert worst_field["field"] == "hu"
    assert worst_field["zone_id"] == "hydraulic_control"
    worst_raw = payload["summary"]["worst_raw_samples"][0]
    assert worst_raw["sample_id"] == "control_probe"
    assert worst_raw["zone_id"] == "hydraulic_control"
    assert "hydraulic-control" in " ".join(payload["blocked_reasons"])


def test_generate_milestone18_drop_ledge_hydraulic_control_cli_writes_reports(tmp_path):
    dual_manifest = _drop_ledge_hydraulic_control_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "drop_ledge_hydraulic_control.json"
    output_md = tmp_path / "reports" / "milestone18" / "drop_ledge_hydraulic_control.md"

    exit_code = generate_drop_ledge_hydraulic_control_main(
        [
            "--dual-solver-manifest",
            str(dual_manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Drop/Ledge Hydraulic-Control Diagnostic" in output_md.read_text(encoding="utf-8")


def _cascading_boundary_inputs(tmp_path: Path) -> tuple[Path, Path]:
    threshold_report = _write_json(
        tmp_path / "outputs" / "m18cmp" / "cascading_low" / "finite_volume_hll" / "threshold_evaluation.json",
        {
            "passed": False,
            "scenario_id": "american_south_fork_chili_bar_to_coloma_low_runnable_beginner_cascading",
            "checks": [
                {"name": "field_linf", "value": 17.0, "threshold": 0.35, "passed": False},
                {"name": "wet_mismatch_fraction", "value": 0.06, "threshold": 0.1, "passed": True},
                {"name": "mass_drift_delta", "value": 0.3, "threshold": 0.04, "passed": False},
            ],
        },
    )
    _write_json(
        threshold_report.parent / "dual_solver_manifest.json",
        {
            "scenario_id": "american_south_fork_chili_bar_to_coloma_low_runnable_beginner_cascading",
            "boundary_semantics": {
                "bc_lower": ["user", "wall"],
                "bc_upper": ["user", "wall"],
                "requires_user_boundary_adapter": True,
                "edges": [
                    {
                        "edge": "west",
                        "scenario_kind": "inflow",
                        "geoclaw_code": "user",
                        "requires_user_boundary_adapter": True,
                    },
                    {
                        "edge": "east",
                        "scenario_kind": "outflow",
                        "geoclaw_code": "user",
                        "requires_user_boundary_adapter": True,
                    },
                    {"edge": "south", "scenario_kind": "bank", "geoclaw_code": "wall"},
                    {"edge": "north", "scenario_kind": "bank", "geoclaw_code": "wall"},
                ],
            },
            "cpp": {
                "returncode": 2,
                "command": [
                    "raftsim_water_solver",
                    "--feature-strength-scale",
                    "0.0",
                    "--boundary-mode",
                    "scenario",
                ],
            },
        },
    )
    stale_report = _write_json(
        tmp_path / "reports" / "milestone16" / "geoclaw_cpp_comparisons.json",
        {
            "passed": False,
            "records": [
                {
                    "gate_scenario_id": "south_fork_cascading_low_runnable",
                    "actual_scenario_id": "american_south_fork_chili_bar_to_coloma_low_runnable_beginner_cascading",
                    "solver_mode": "finite_volume",
                    "threshold_passed": False,
                    "check_values": {
                        "field_linf": {"value": 39.6, "threshold": 0.35, "passed": False},
                        "wet_mismatch_fraction": {"value": 0.33, "threshold": 0.1, "passed": False},
                        "mass_drift_delta": {"value": 1.91, "threshold": 0.04, "passed": False},
                    },
                }
            ],
        },
    )
    return threshold_report, stale_report


def test_milestone18_cascading_boundary_correction_report_records_corrected_blockers(tmp_path):
    threshold_report, stale_report = _cascading_boundary_inputs(tmp_path)

    report = build_milestone18_cascading_boundary_correction_report(
        (threshold_report,),
        stale_comparison_report=stale_report,
    )
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_CASCADING_BOUNDARY_CORRECTION_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["boundary_corrected_count"] == 1
    assert payload["summary"]["feature_forcing_off_count"] == 1
    assert payload["summary"]["failing_check_counts"] == {"field_linf": 1, "mass_drift_delta": 1}
    flow = payload["flow_results"][0]
    assert flow["gate_scenario_id"] == "south_fork_cascading_low_runnable"
    assert flow["boundary_corrected"] is True
    wet_check = {check["name"]: check for check in flow["checks"]}["wet_mismatch_fraction"]
    assert wet_check["passed"] is True
    assert wet_check["stale_value"] == pytest.approx(0.33)
    assert wet_check["stale_to_corrected_delta"] == pytest.approx(-0.27)
    assert "corrected-boundary thresholds" in " ".join(payload["blocked_reasons"])


def test_generate_milestone18_cascading_boundary_correction_cli_writes_reports(tmp_path):
    threshold_report, stale_report = _cascading_boundary_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "cascading_boundary_correction_diagnostic.json"
    output_md = tmp_path / "reports" / "milestone18" / "cascading_boundary_correction_diagnostic.md"

    exit_code = generate_cascading_boundary_correction_main(
        [
            "--corrected-threshold-report",
            str(threshold_report),
            "--stale-comparison-report",
            str(stale_report),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_CASCADING_BOUNDARY_CORRECTION_REPORT_SCHEMA
    assert payload["summary"]["stale_reference_compared"] is True
    assert "Cascading Boundary Correction Diagnostic" in output_md.read_text(encoding="utf-8")


def test_milestone18_remaining_geometry_closure_records_cascading_boundary_evidence(tmp_path):
    threshold_report, stale_report = _cascading_boundary_inputs(tmp_path)
    geometry_report, _, _ = _remaining_geometry_closure_inputs(tmp_path)
    cascading_report = build_milestone18_cascading_boundary_correction_report(
        (threshold_report,),
        stale_comparison_report=stale_report,
    )
    cascading_report_path = tmp_path / "reports" / "milestone18" / "cascading_boundary_correction_diagnostic.json"
    cascading_report.write_json(cascading_report_path)

    report = build_milestone18_remaining_geometry_closure_report(
        geometry_report,
        focused_reports=(cascading_report_path,),
    )
    payload = report.to_json_dict()

    cases = {case["case_id"]: case for case in payload["cases"]}
    evidence = cases["drops_ledges_tailwater"]["focused_evidence"][0]
    assert evidence["source_report"] == str(cascading_report_path)
    assert evidence["gate_scenario_id"] == "south_fork_cascading_window"
    assert evidence["gate_scenario_ids"] == ["south_fork_cascading_low_runnable"]
    assert "corrected-boundary thresholds" in " ".join(evidence["blocked_reasons"])


def _remaining_geometry_closure_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    geometry_report = _write_json(
        tmp_path / "reports" / "milestone16" / "geometry_validation.json",
        {
            "schema_version": "raftsim.milestone16.geometry_validation.v0",
            "passed": False,
            "comparison_report": "reports/milestone16/geoclaw_cpp_comparisons.json",
            "geoclaw_reference_report": "reports/milestone16/geoclaw_reference_runs.json",
            "cases": [
                {
                    "case_id": "bed_step",
                    "title": "Bed Steps",
                    "passed": True,
                    "scenarios": ["bed_step"],
                    "solver_modes": ["finite_volume", "reduced"],
                    "evidence": [
                        {
                            "gate_scenario_id": "bed_step",
                            "solver_mode": "finite_volume",
                            "threshold_passed": True,
                            "failing_checks": [],
                        },
                        {
                            "gate_scenario_id": "bed_step",
                            "solver_mode": "reduced",
                            "threshold_passed": False,
                            "diagnostic_only": True,
                            "failing_checks": ["field_linf", "mass_drift_delta"],
                        },
                    ],
                    "notes": ["Reduced mode is diagnostic-only."],
                },
                {
                    "case_id": "constriction",
                    "title": "Constrictions",
                    "passed": False,
                    "scenarios": ["constriction"],
                    "solver_modes": ["finite_volume", "reduced"],
                    "evidence": [
                        {
                            "gate_scenario_id": "constriction",
                            "solver_mode": "finite_volume",
                            "threshold_passed": False,
                            "failing_checks": ["field_linf", "probe_linf"],
                        }
                    ],
                    "notes": ["Threshold failures remain in: constriction."],
                },
                {
                    "case_id": "drops_ledges_tailwater",
                    "title": "Drops, Ledges, And Tailwater",
                    "passed": False,
                    "scenarios": [
                        "drop_ledge",
                        "south_fork_cascading_low_runnable",
                    ],
                    "solver_modes": ["finite_volume", "reduced"],
                    "evidence": [
                        {
                            "gate_scenario_id": "drop_ledge",
                            "solver_mode": "finite_volume",
                            "threshold_passed": False,
                            "failing_checks": ["field_linf", "probe_linf"],
                        },
                        {
                            "gate_scenario_id": "south_fork_cascading_low_runnable",
                            "solver_mode": "finite_volume",
                            "threshold_passed": False,
                            "failing_checks": ["field_linf", "mass_drift_delta"],
                        },
                    ],
                    "notes": ["Threshold failures remain in: drop_ledge, south_fork_cascading_low_runnable."],
                },
                {
                    "case_id": "stitched_reach_drop_handoffs",
                    "title": "Stitched Reach/Drop Boundary Handoffs",
                    "passed": True,
                    "scenarios": ["south_fork_cascading_low_runnable"],
                    "solver_modes": ["geoclaw", "package"],
                    "evidence": [{"gate_scenario_id": "south_fork_cascading_low_runnable", "passed": True}],
                    "notes": [],
                },
            ],
        },
    )
    constriction_report = _write_json(
        tmp_path / "reports" / "milestone18" / "constriction_lateral_face_flux_diagnostic.json",
        {
            "schema_version": "raftsim.milestone18.constriction_lateral_face_flux.v0",
            "decision": "BLOCKED",
            "passed": False,
            "summary": {"sign_mismatch_count": 2},
            "blocked_reasons": ["C++ upstream lateral face velocity signs do not match GeoClaw."],
            "next_levers": ["Instrument constriction lateral face flux/source balance."],
        },
    )
    drop_report = _write_json(
        tmp_path / "reports" / "milestone18" / "drop_ledge_hydraulic_control_diagnostic.json",
        {
            "schema_version": "raftsim.milestone18.drop_ledge_hydraulic_control.v0",
            "decision": "BLOCKED",
            "passed": False,
            "summary": {"max_final_field_linf": 0.83},
            "blocked_reasons": ["C++ drop/ledge final-field Linf still exceeds the GeoClaw/C++ threshold."],
            "next_levers": ["Retune the ledge hydraulic-control reconstruction."],
        },
    )
    return geometry_report, constriction_report, drop_report


def test_milestone18_remaining_geometry_closure_report_records_active_blockers(tmp_path):
    geometry_report, constriction_report, drop_report = _remaining_geometry_closure_inputs(tmp_path)
    passing_drop_report = _write_json(
        tmp_path / "reports" / "milestone18" / "drop_ledge_hydraulic_control_balance.json",
        {
            "schema_version": "raftsim.milestone18.drop_ledge_hydraulic_control.v0",
            "decision": "PASS",
            "passed": True,
            "scenario_id": "drop_ledge_seed_16",
            "summary": {"max_final_field_linf": 0.1946, "max_probe_linf": 0.1890},
            "blocked_reasons": [],
            "next_levers": ["Promote the finite-volume drop/ledge lane as a guardrail."],
        },
    )

    report = build_milestone18_remaining_geometry_closure_report(
        geometry_report,
        focused_reports=(constriction_report, drop_report, passing_drop_report),
    )
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert payload["summary"]["active_blockers"] == ["constriction", "drops_ledges_tailwater"]
    assert payload["summary"]["next_case"] == "constriction"
    cases = {case["case_id"]: case for case in payload["cases"]}
    assert cases["bed_step"]["promotion_ready"] is True
    assert cases["constriction"]["focused_evidence"][0]["source_report"] == str(constriction_report)
    assert cases["drops_ledges_tailwater"]["failing_check_counts"]["field_linf"] == 1
    drop_notes = " ".join(cases["drops_ledges_tailwater"]["notes"])
    assert "Threshold failures remain in: south_fork_cascading_low_runnable." in drop_notes
    assert "Focused passing evidence supersedes stale aggregate failures for: drop_ledge." in drop_notes
    assert "whole-window water-field parity" in drop_notes


def test_milestone18_remaining_geometry_closure_promotes_focused_passing_family(tmp_path):
    geometry_report, _, drop_report = _remaining_geometry_closure_inputs(tmp_path)
    passing_constriction_report = _write_json(
        tmp_path / "reports" / "milestone18" / "constriction_upstream_edge_balance.json",
        {
            "schema_version": "raftsim.milestone18.constriction_upstream_edge_balance.v0",
            "decision": "PASS",
            "passed": True,
            "scenario_id": "constriction_seed_16",
            "summary": {"target_sample_count": 0, "blocked_target_count": 0},
            "blocked_reasons": [],
            "next_levers": ["Preserve constriction-focused reports as guardrails."],
        },
    )

    report = build_milestone18_remaining_geometry_closure_report(
        geometry_report,
        focused_reports=(passing_constriction_report, drop_report),
    )
    payload = report.to_json_dict()

    assert payload["summary"]["active_blockers"] == ["drops_ledges_tailwater"]
    assert payload["summary"]["next_case"] == "drops_ledges_tailwater"
    cases = {case["case_id"]: case for case in payload["cases"]}
    assert cases["constriction"]["promotion_ready"] is True
    assert cases["constriction"]["failing_check_counts"] == {}
    assert "Focused passing evidence supersedes stale aggregate failures for: constriction." in " ".join(
        cases["constriction"]["notes"]
    )


def test_generate_milestone18_remaining_geometry_closure_cli_writes_reports(tmp_path):
    geometry_report, constriction_report, drop_report = _remaining_geometry_closure_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "remaining_geometry_closure.json"
    output_md = tmp_path / "reports" / "milestone18" / "remaining_geometry_closure.md"

    exit_code = generate_remaining_geometry_closure_main(
        [
            "--geometry-report",
            str(geometry_report),
            "--focused-report",
            str(constriction_report),
            "--focused-report",
            str(drop_report),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA
    assert payload["decision"] == "BLOCKED"
    assert "Remaining Geometry Closure" in output_md.read_text(encoding="utf-8")


def test_milestone18_parity_family_retune_report_records_partial_promotion(tmp_path):
    reference_manifest, threshold_reports = _parity_retune_inputs(tmp_path)

    report = build_milestone18_parity_family_retune_report(
        scenario_family="uniform_channel",
        gate_scenario_id="uniform_channel",
        reference_manifest=reference_manifest,
        threshold_reports=threshold_reports,
        candidate_labels={"finite_volume": "hll_roughness_0p5_bed_0p75"},
    )
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA
    assert payload["decision"] == "PARTIAL_PROMOTION"
    assert payload["reference_boundary_semantics"]["bc_lower"] == ["user", "wall"]
    assert payload["summary"]["promoted_modes"] == ["finite_volume"]
    assert payload["summary"]["blocked_modes"] == ["reduced"]
    finite_volume = next(result for result in payload["mode_results"] if result["solver_mode"] == "finite_volume")
    assert finite_volume["tuning_parameters"]["flux_scheme"] == "hll"
    assert finite_volume["tuning_parameters"]["feature_strength_scale"] == 0.0


def test_generate_milestone18_parity_family_retune_cli_writes_reports(tmp_path):
    reference_manifest, threshold_reports = _parity_retune_inputs(tmp_path)
    output_json = tmp_path / "reports" / "milestone18" / "retune.json"
    output_md = tmp_path / "reports" / "milestone18" / "retune.md"

    exit_code = generate_retune_main(
        [
            "--scenario-family",
            "uniform_channel",
            "--gate-scenario-id",
            "uniform_channel",
            "--reference-manifest",
            str(reference_manifest),
            "--threshold-report",
            "finite_volume",
            str(threshold_reports["finite_volume"]),
            "--threshold-report",
            "reduced",
            str(threshold_reports["reduced"]),
            "--candidate-label",
            "finite_volume",
            "hll_roughness_0p5_bed_0p75",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA
    assert payload["decision"] == "PARTIAL_PROMOTION"
    assert "Milestone 18 Parity Family Retune" in output_md.read_text(encoding="utf-8")


def test_milestone18_pin_release_fixture_report_records_distinct_flow_dependent_paths():
    report = build_milestone18_pin_release_fixture_report()
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_PIN_RELEASE_REPORT_SCHEMA
    assert payload["decision"] == "PASS"
    assert payload["feature_forcing_strength_scale"] == 0.0
    assert payload["proxy_separation"]["excluded_proxy_families"] == ["shallow_shelf", "boulder_impacts"]
    assert payload["summary"]["flow_bands"] == ["low_scrape", "runnable_sticky", "high_washout"]
    assert {"pinned", "released", "failed_rescue"}.issubset(set(payload["summary"]["outcomes"]))

    sticky = next(case for case in payload["flow_cases"] if case["flow_band"] == "runnable_sticky")
    paths = {path["path_id"]: path for path in sticky["response_paths"]}
    assert paths["no_action_pin"]["outcome"] == "pinned"
    assert paths["no_action_pin"]["release_margin_n"] < 0.0
    assert paths["timed_high_side_release"]["outcome"] == "released"
    assert paths["timed_high_side_release"]["crew_weight"]["high_side_count"] > 0
    assert paths["late_high_side_failed_rescue"]["outcome"] == "failed_rescue"
    assert paths["late_high_side_failed_rescue"]["swimmer"]["states"][-1] == "failed_rescue"
    assert paths["late_high_side_failed_rescue"]["swimmer"]["safety_score_delta"] < 0.0


def test_generate_milestone18_pin_release_fixture_cli_writes_reports(tmp_path):
    output_json = tmp_path / "reports" / "milestone18" / "pin_release_fixture.json"
    output_md = tmp_path / "reports" / "milestone18" / "pin_release_fixture.md"

    exit_code = generate_pin_release_main(
        [
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_PIN_RELEASE_REPORT_SCHEMA
    assert payload["decision"] == "PASS"
    assert "Milestone 18 Pin/Release Fixture" in output_md.read_text(encoding="utf-8")


def test_milestone18_analytic_retune_guardrail_passes_for_baseline_scenario(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")

    report = run_milestone18_analytic_retune_guardrail(
        manifest_path,
        tmp_path / "guardrails",
        retune_batch_id="baseline",
    )
    payload = report.to_json_dict()

    assert payload["schema_version"] == MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA
    assert payload["decision"] == "PASS"
    assert payload["preflight"]["passed"] is True
    assert payload["postflight"]["passed"] is True
    assert payload["regression_count"] == 0
    assert (Path(report.output_dir) / "preflight_analytic_validation.json").exists()
    assert (Path(report.output_dir) / "postflight_analytic_validation.json").exists()


def test_run_milestone18_analytic_retune_guardrail_cli_writes_summary(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")

    exit_code = guardrail_main(
        [
            "--manifest",
            str(manifest_path),
            "--output-dir",
            str(tmp_path / "guardrails"),
            "--retune-batch-id",
            "baseline",
        ]
    )

    assert exit_code == 0
    output_root = tmp_path / "guardrails" / "baseline"
    payload = json.loads((output_root / "analytic_retune_guardrail.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA
    assert payload["passed"] is True
    assert "Milestone 18 Analytic Retune Guardrail" in (output_root / "analytic_retune_guardrail.md").read_text(
        encoding="utf-8"
    )
