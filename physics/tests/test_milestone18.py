import json
from pathlib import Path

from raftsim.analytic_fixtures import write_analytic_fixture_suite
from raftsim.examples.generate_milestone18_failure_triage_matrix import main as generate_triage_main
from raftsim.examples.generate_milestone18_parity_family_retune_report import main as generate_retune_main
from raftsim.examples.generate_milestone18_pin_release_fixture_report import main as generate_pin_release_main
from raftsim.examples.run_milestone18_analytic_retune_guardrail import main as guardrail_main
from raftsim.milestone18 import (
    MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA,
    MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA,
    MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA,
    MILESTONE18_PIN_RELEASE_REPORT_SCHEMA,
    build_milestone18_failure_triage_matrix,
    build_milestone18_parity_family_retune_report,
    build_milestone18_pin_release_fixture_report,
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
