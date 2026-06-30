import json
from pathlib import Path

from raftsim.examples.generate_milestone18_failure_triage_matrix import main as generate_triage_main
from raftsim.milestone18 import (
    MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA,
    build_milestone18_failure_triage_matrix,
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
