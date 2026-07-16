import json

import pytest

from raftsim.solver_truth_baseline import SOLVER_TRUTH_BASELINE_SCHEMA, build_solver_truth_baseline


def _comparison_record(gate: str, mode: str, *, passed: bool) -> dict[str, object]:
    return {
        "gate_scenario_id": gate,
        "actual_scenario_id": f"{gate}_seed_16",
        "suite": "canonical",
        "solver_mode": mode,
        "threshold_tier": "production_candidate",
        "threshold_passed": passed,
        "failing_checks": [] if passed else ["field_linf"],
        "check_values": {
            "field_linf": {
                "name": "field_linf",
                "value": 0.1 if passed else 0.4,
                "threshold": 0.15,
                "passed": passed,
                "details": "test norm",
            }
        },
    }


def _cpp_record(gate: str, mode: str, *, disabled: bool = True) -> dict[str, object]:
    return {
        "gate_scenario_id": gate,
        "solver_mode": mode,
        "manifest_settings": {"disable_fixture_calibrations": disabled},
    }


def test_solver_truth_baseline_preserves_each_uncalibrated_error_norm(tmp_path):
    comparison_report = {
        "geoclaw_reference_report": "reports/milestone16/geoclaw_reference_runs.json",
        "records": [
            _comparison_record("flat_pool", "reduced", passed=True),
            _comparison_record("flat_pool", "finite_volume", passed=False),
        ],
    }
    cpp_report = {
        "records": [
            _cpp_record("flat_pool", "reduced"),
            _cpp_record("flat_pool", "finite_volume"),
        ]
    }

    baseline = build_solver_truth_baseline(
        comparison_report,
        cpp_report,
        comparison_report_path="outputs/solver_truth_baseline/geoclaw_cpp_comparisons.json",
        cpp_run_report_path="outputs/solver_truth_baseline/cpp_solver_runs.json",
        source_commit="abc123",
        solver_binary_sha256="f" * 64,
        expected_comparison_count=2,
    )
    payload = baseline.to_json_dict()
    baseline.write_json(tmp_path / "baseline.json")
    baseline.write_markdown(tmp_path / "baseline.md")

    assert payload["schema_version"] == SOLVER_TRUTH_BASELINE_SCHEMA
    assert payload["measurement_mode"] == "uncalibrated_solver"
    assert payload["fixture_calibrations_disabled"] is True
    assert payload["comparison_count"] == 2
    assert payload["threshold_passed_count"] == 1
    assert payload["threshold_failed_count"] == 1
    assert payload["passed"] is False
    assert payload["records"][1]["error_norms"]["field_linf"]["value"] == 0.4
    assert json.loads((tmp_path / "baseline.json").read_text(encoding="utf-8")) == payload
    markdown = (tmp_path / "baseline.md").read_text(encoding="utf-8")
    assert "Fixture calibrations and reference playback: **DISABLED**" in markdown
    assert "field_linf=0.4/0.15" in markdown


def test_solver_truth_baseline_rejects_calibrated_rows():
    comparison_report = {
        "geoclaw_reference_report": "reports/milestone16/geoclaw_reference_runs.json",
        "records": [_comparison_record("flat_pool", "reduced", passed=True)],
    }
    cpp_report = {"records": [_cpp_record("flat_pool", "reduced", disabled=False)]}

    with pytest.raises(ValueError, match="did not disable fixture calibrations"):
        build_solver_truth_baseline(
            comparison_report,
            cpp_report,
            comparison_report_path="comparison.json",
            cpp_run_report_path="cpp.json",
            source_commit="abc123",
            solver_binary_sha256="f" * 64,
            expected_comparison_count=1,
        )
