import json
from pathlib import Path

from raftsim.examples.generate_flexible_raft_d6_comparison_report import (
    main as generate_d6_comparison_report_main,
)
from raftsim.examples.merge_flexible_raft_d6_chaos_measured_results import (
    main as merge_d6_chaos_measured_results_main,
)
from raftsim.examples.merge_flexible_raft_d6_compliant_measured_results import (
    main as merge_d6_compliant_measured_results_main,
)
from raftsim.flexible_raft_d6 import (
    D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
    D6_BEHAVIORAL_SUITE_SCHEMA,
    D6_CHAOS_FIXTURE_CONTRACT_RELATIVE_PATH,
    D6_CHAOS_FIXTURE_CONTRACT_SCHEMA,
    D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_SCHEMA,
    D6_CHAOS_MEASURED_RESULTS_SIDECAR_SCHEMA,
    D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_SCHEMA,
    D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_SCHEMA,
    D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPARISON_REPORT_RELATIVE_PATH,
    D6_COMPARISON_REPORT_SCHEMA,
    D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
    D6_FIXTURE_INPUT_PACKAGE_SCHEMA,
    D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
    D6_MEASURED_RESULTS_TEMPLATE_SCHEMA,
    D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
    D6_MEASUREMENT_MANIFEST_SCHEMA,
    REQUIRED_D6_FIXTURE_IDS,
    build_d6_replay_channel_probe,
    build_flexible_raft_d6_chaos_fixture_contract,
    build_flexible_raft_d6_chaos_measured_results_merge_report,
    build_flexible_raft_d6_chaos_measured_results_sidecar_template,
    build_flexible_raft_d6_behavioral_suite,
    build_flexible_raft_d6_compliant_measured_results_merge_report,
    build_flexible_raft_d6_compliant_measured_results_sidecar_template,
    build_flexible_raft_d6_comparison_report,
    build_flexible_raft_d6_fixture_input_package,
    build_flexible_raft_d6_measured_results_template,
    build_flexible_raft_d6_measurement_manifest,
    merge_flexible_raft_d6_chaos_measured_results_sidecar,
    merge_flexible_raft_d6_compliant_measured_results_sidecar,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flexible_raft_d6_suite_is_reproducible_and_not_promoted():
    generated = build_flexible_raft_d6_behavioral_suite()
    committed = json.loads(
        (REPO_ROOT / D6_BEHAVIORAL_SUITE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_BEHAVIORAL_SUITE_SCHEMA
    assert committed["d6_complete"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False
    assert committed["production_promoted"] is False


def test_flexible_raft_d6_suite_covers_all_required_behavioral_fixtures():
    suite = build_flexible_raft_d6_behavioral_suite()
    fixture_ids = [fixture["fixture_id"] for fixture in suite["fixtures"]]

    assert fixture_ids == list(REQUIRED_D6_FIXTURE_IDS)
    assert suite["fixture_count"] == 7
    assert set(suite["required_fixture_ids"]) == set(REQUIRED_D6_FIXTURE_IDS)


def test_flexible_raft_d6_requires_compliant_reference_and_chaos_baseline():
    suite = build_flexible_raft_d6_behavioral_suite()

    assert suite["reference_requirements"]["compliant_reference"]["status"] == "missing_measured_reference_results"
    assert suite["reference_requirements"]["chaos_rigid_baseline"]["status"] == "missing_measured_unreal_chaos_results"
    assert suite["reference_requirements"]["chaos_rigid_baseline"]["source_contract"] == D6_CHAOS_FIXTURE_CONTRACT_RELATIVE_PATH
    for fixture in suite["fixtures"]:
        targets = {target["target_id"]: target for target in fixture["comparison_targets"]}
        assert targets["project_chrono_or_reviewed_compliant_model"]["required"] is True
        assert targets["project_chrono_or_reviewed_compliant_model"]["status"] == "pending_measured_reference"
        assert targets["unreal_chaos_rigid_baseline"]["required"] is True
        assert targets["unreal_chaos_rigid_baseline"]["status"] == "pending_measured_chaos_baseline"
        assert fixture["can_promote"] is False


def test_flexible_raft_d6_suite_records_current_python_metrics():
    suite = build_flexible_raft_d6_behavioral_suite()
    by_id = {fixture["fixture_id"]: fixture for fixture in suite["fixtures"]}

    assert by_id["static_seat_load_sag"]["python_reference_metrics"]["max_seat_freeboard_loss_m"] > 0.0
    assert by_id["rock_pinch_wrap"]["python_reference_metrics"]["wrapping_contact_count"] >= 3
    assert by_id["upstream_tube_overwash_flip"]["python_reference_metrics"]["total_overtopping_flux_m3_s"] > 0.0
    assert by_id["post_contact_recovery"]["python_reference_metrics"]["recovering_contact_count"] > 0
    assert by_id["pressure_flow_sweeps"]["python_reference_metrics"]["sweep_case_count"] == 9


def test_flexible_raft_d6_replay_probe_exposes_d5_hashes():
    probe = build_d6_replay_channel_probe()

    assert probe["frame_count"] == 2
    assert len(probe["frame_hashes"]) == 2
    assert len(probe["replay_sha256"]) == 64


def test_flexible_raft_d6_comparison_report_is_reproducible_and_pending():
    generated = build_flexible_raft_d6_comparison_report()
    committed = json.loads(
        (REPO_ROOT / D6_COMPARISON_REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_COMPARISON_REPORT_SCHEMA
    assert committed["status"] == "blocked_pending_measured_engine_results"
    assert committed["d6_complete"] is False
    assert committed["comparison_passed"] is False
    assert committed["missing_target_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2


def test_flexible_raft_d6_comparison_report_requires_every_target_fixture_pair():
    report = build_flexible_raft_d6_comparison_report()

    for fixture in report["fixtures"]:
        assert fixture["passed"] is False
        assert fixture["target_count"] == 2
        assert {target["status"] for target in fixture["targets"]} == {"missing_measured_result"}
        assert {target["target_id"] for target in fixture["targets"]} == {
            "project_chrono_or_reviewed_compliant_model",
            "unreal_chaos_rigid_baseline",
        }


def test_flexible_raft_d6_comparison_harness_accepts_synthetic_measured_results():
    report = build_flexible_raft_d6_comparison_report(_synthetic_measured_results())

    assert report["all_measurements_present"] is True
    assert report["comparison_passed"] is True
    assert report["d6_complete"] is False
    assert report["promotion_gate"]["may_mark_d6_complete"] is True
    assert {fixture["passed"] for fixture in report["fixtures"]} == {True}
    for fixture in report["fixtures"]:
        target_statuses = {target["target_id"]: target["status"] for target in fixture["targets"]}
        assert target_statuses["project_chrono_or_reviewed_compliant_model"] == "passed_numeric_equivalence"
        assert target_statuses["unreal_chaos_rigid_baseline"] == "recorded_baseline_delta"


def test_flexible_raft_d6_comparison_harness_flags_compliant_reference_metric_delta():
    measured = _synthetic_measured_results()
    measured["project_chrono_or_reviewed_compliant_model"]["static_seat_load_sag"]["metrics"][
        "raft_width_m"
    ] *= 2.0

    report = build_flexible_raft_d6_comparison_report(measured)
    by_id = {fixture["fixture_id"]: fixture for fixture in report["fixtures"]}
    static_targets = {
        target["target_id"]: target for target in by_id["static_seat_load_sag"]["targets"]
    }

    assert report["comparison_passed"] is False
    assert by_id["static_seat_load_sag"]["passed"] is False
    assert static_targets["project_chrono_or_reviewed_compliant_model"]["status"] == "failed_numeric_equivalence"
    assert static_targets["project_chrono_or_reviewed_compliant_model"]["metric_summary"]["failed_metric_count"] >= 1
    assert static_targets["unreal_chaos_rigid_baseline"]["status"] == "recorded_baseline_delta"


def test_flexible_raft_d6_comparison_harness_requires_engine_version_and_valid_hash():
    measured = _synthetic_measured_results()
    target_result = measured["project_chrono_or_reviewed_compliant_model"][
        "static_seat_load_sag"
    ]
    target_result["engine_version"] = ""
    target_result["telemetry_sha256"] = "not-a-sha256"

    report = build_flexible_raft_d6_comparison_report(measured)
    by_id = {fixture["fixture_id"]: fixture for fixture in report["fixtures"]}
    static_targets = {
        target["target_id"]: target for target in by_id["static_seat_load_sag"]["targets"]
    }
    target = static_targets["project_chrono_or_reviewed_compliant_model"]

    assert report["comparison_passed"] is False
    assert target["status"] == "incomplete_measured_result_provenance"
    assert "engine_version" in target["missing_provenance_fields"]
    assert target["invalid_provenance_fields"] == ["telemetry_sha256"]


def test_flexible_raft_d6_measurement_manifest_is_reproducible_and_pending():
    generated = build_flexible_raft_d6_measurement_manifest()
    committed = json.loads(
        (REPO_ROOT / D6_MEASUREMENT_MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_MEASUREMENT_MANIFEST_SCHEMA
    assert committed["status"] == "measurement_manifest_ready_engine_runs_pending"
    assert committed["d6_complete"] is False
    assert committed["production_promoted"] is False
    assert committed["measurement_task_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert committed["fixture_input_package_path"] == D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH


def test_flexible_raft_d6_measurement_manifest_covers_every_target_fixture_pair():
    manifest = build_flexible_raft_d6_measurement_manifest()
    task_pairs = {(task["target_id"], task["fixture_id"]) for task in manifest["tasks"]}

    assert manifest["summary"]["pending_measurement_task_count"] == 14
    assert manifest["summary"]["required_compliant_reference_task_count"] == 7
    assert manifest["summary"]["required_chaos_baseline_task_count"] == 7
    for fixture_id in REQUIRED_D6_FIXTURE_IDS:
        assert ("project_chrono_or_reviewed_compliant_model", fixture_id) in task_pairs
        assert ("unreal_chaos_rigid_baseline", fixture_id) in task_pairs
    for task in manifest["tasks"]:
        assert task["status"] == "pending_measured_engine_run"
        assert task["required_metric_count"] == len(task["required_metric_paths"])
        assert task["required_metric_count"] > 0
        assert "source_report" in task["required_provenance_fields"]
        assert "telemetry_sha256" in task["required_provenance_fields"]
        assert "engine_version" in task["required_provenance_fields"]
        assert task["can_promote_fixture"] is False
    chaos_tasks = [
        task for task in manifest["tasks"]
        if task["target_id"] == "unreal_chaos_rigid_baseline"
    ]
    assert {
        task["adapter_contract"]["fixture_contract"] for task in chaos_tasks
    } == {D6_CHAOS_FIXTURE_CONTRACT_RELATIVE_PATH}


def test_flexible_raft_d6_measured_results_template_is_reproducible_and_empty():
    generated = build_flexible_raft_d6_measured_results_template()
    committed = json.loads(
        (REPO_ROOT / D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert committed["schema"] == D6_MEASURED_RESULTS_TEMPLATE_SCHEMA
    assert committed["status"] == "measured_results_template_empty"
    assert committed["required_result_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert committed["filled_result_count"] == 0
    assert committed["d6_complete"] is False
    assert committed["production_promoted"] is False
    assert committed["source_fixture_input_package_path"] == D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH


def test_flexible_raft_d6_measured_results_template_matches_comparison_contract():
    template = build_flexible_raft_d6_measured_results_template()

    assert set(template["measured_results"]) == {
        "project_chrono_or_reviewed_compliant_model",
        "unreal_chaos_rigid_baseline",
    }
    for target_id, fixtures in template["measured_results"].items():
        assert set(fixtures) == set(REQUIRED_D6_FIXTURE_IDS)
        for fixture_id, payload in fixtures.items():
            assert payload["target_id"] == target_id
            assert payload["fixture_id"] == fixture_id
            assert payload["status"] == "not_measured"
            assert payload["source_report"] == ""
            assert payload["telemetry_sha256"] == ""
            assert payload["engine_version"] == ""
            assert payload["metric_paths_required"]
            assert payload["metrics"]


def test_flexible_raft_d6_fixture_input_package_is_reproducible_and_pending():
    generated = build_flexible_raft_d6_fixture_input_package()
    committed = json.loads(
        (REPO_ROOT / D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert committed["schema"] == D6_FIXTURE_INPUT_PACKAGE_SCHEMA
    assert committed["status"] == "fixture_inputs_ready_engine_adapter_runs_pending"
    assert committed["fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert committed["measurement_task_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert committed["d6_complete"] is False
    assert committed["production_promoted"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False


def test_flexible_raft_d6_fixture_input_package_covers_required_inputs():
    package = build_flexible_raft_d6_fixture_input_package()
    by_id = {fixture["fixture_id"]: fixture for fixture in package["fixtures"]}

    assert list(by_id) == list(REQUIRED_D6_FIXTURE_IDS)
    assert package["common_setup"]["crew_seat_count"] == 5
    assert package["common_setup"]["default_tube_layout"]["segment_count"] > 0
    assert package["common_setup"]["initial_state"]["position"] == {
        "x": 3.0,
        "y": 2.0,
        "z": 0.0,
    }

    shift_phases = by_id["traveling_crew_shift"]["input_contract"]["phases"]
    assert [phase["phase_id"] for phase in shift_phases] == [
        "neutral_occupied_seats",
        "port_lean_requested",
        "starboard_high_side",
    ]
    assert shift_phases[1]["action_count"] == 5
    assert {action["lean_clamp_expected"] for action in shift_phases[1]["crew_actions"]} == {True}
    assert {action["high_side_direction"] for action in shift_phases[2]["crew_actions"]} == {1}

    rock = by_id["rock_pinch_wrap"]["input_contract"]["obstacles"][0]
    assert rock["obstacle_id"] == "wrap_starboard_pillow"
    assert rock["local_position"] == {"x": 0.0, "y": 1.0, "z": 0.0}
    assert rock["radius_m"] == 1.45

    overwash = by_id["upstream_tube_overwash_flip"]["input_contract"]["water"]
    assert overwash["surface_height_m"] == 0.24
    assert overwash["velocity_mps"] == {"x": 0.0, "y": -3.0, "z": 0.0}

    timed = by_id["timed_high_side_save"]["input_contract"]
    assert timed["previous_retained_volume_by_segment"]
    assert timed["phases"][1]["phase_id"] == "starboard_high_side_with_retained_water_memory"

    recovery = by_id["post_contact_recovery"]["input_contract"]
    assert recovery["previous_indentation_by_segment"] == {
        "starboard_1": 0.08,
        "starboard_2": 0.12,
    }

    sweeps = by_id["pressure_flow_sweeps"]["input_contract"]
    assert sweeps["nominal_pressure_values_pa"] == [14000.0, 18000.0, 22000.0]
    assert sweeps["incoming_velocity_values_mps"] == [1.2, 2.4, 3.6]
    assert sweeps["sweep_case_count"] == 9
    assert len(sweeps["sweep_cases"]) == 9


def test_flexible_raft_d6_fixture_input_package_targets_and_metrics_match_manifest():
    package = build_flexible_raft_d6_fixture_input_package()

    for fixture in package["fixtures"]:
        assert fixture["can_promote"] is False
        assert fixture["required_metric_count"] == len(fixture["required_metric_paths"])
        assert fixture["required_metric_count"] > 0
        assert {target["target_id"] for target in fixture["adapter_targets"]} == {
            "project_chrono_or_reviewed_compliant_model",
            "unreal_chaos_rigid_baseline",
        }
        for target in fixture["adapter_targets"]:
            assert target["fixture_id"] == fixture["fixture_id"]
            assert "source_report" in target["required_provenance_fields"]
            assert "telemetry_sha256" in target["required_provenance_fields"]
            assert "engine_version" in target["required_provenance_fields"]
            assert target["adapter_contract"]["may_substitute_with_synthetic_python_reference"] is False
            assert target["can_promote_fixture"] is False


def test_flexible_raft_d6_chaos_fixture_contract_is_reproducible_and_pending():
    generated = build_flexible_raft_d6_chaos_fixture_contract()
    committed = json.loads(
        (REPO_ROOT / D6_CHAOS_FIXTURE_CONTRACT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert committed["schema"] == D6_CHAOS_FIXTURE_CONTRACT_SCHEMA
    assert committed["status"] == "chaos_fixture_contract_ready_runner_implementation_pending"
    assert committed["runtime"] == "UnrealChaos"
    assert committed["job_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert committed["required_fixture_ids"] == list(REQUIRED_D6_FIXTURE_IDS)
    assert committed["d6_complete"] is False
    assert committed["production_promoted"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False


def test_flexible_raft_d6_chaos_fixture_contract_maps_every_job():
    contract = build_flexible_raft_d6_chaos_fixture_contract()
    jobs = {job["fixture_id"]: job for job in contract["jobs"]}

    assert set(jobs) == set(REQUIRED_D6_FIXTURE_IDS)
    static = jobs["static_seat_load_sag"]
    assert static["job_id"] == "unreal_chaos_rigid_baseline__static_seat_load_sag"
    assert static["automation_test_name"] == "RaftSim.D6.Chaos.StaticSeatLoadSag"
    assert static["fixture_input_package"] == D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH
    assert static["expected_result_template_path"].endswith(
        "unreal_chaos_rigid_baseline/static_seat_load_sag.json"
    )
    assert "telemetry_sha256" in static["required_output_fields"]
    assert "determinism_hash" in static["required_telemetry_fields"]
    assert static["guardrails"]["may_substitute_python_reference"] is False
    assert static["guardrails"]["must_preserve_fixture_input_semantics"] is True


def test_flexible_raft_d6_unreal_contract_guard_is_registered():
    source_path = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimD6ChaosFixtureContractTest.cpp"
    )
    source = source_path.read_text(encoding="utf-8")

    assert "RaftSim.D6.ChaosFixtureContract" in source
    for automation_test_name in (
        "RaftSim.D6.Chaos.StaticSeatLoadSag",
        "RaftSim.D6.Chaos.TravelingCrewShift",
        "RaftSim.D6.Chaos.RockPinchWrap",
        "RaftSim.D6.Chaos.UpstreamTubeOverwashFlip",
        "RaftSim.D6.Chaos.TimedHighSideSave",
        "RaftSim.D6.Chaos.PostContactRecovery",
        "RaftSim.D6.Chaos.PressureFlowSweeps",
    ):
        assert automation_test_name in source
    assert "flexible_raft_d6_chaos_fixture_contract.json" in source
    assert "telemetry_sha256" in source
    assert "must_preserve_fixture_input_semantics" in source
    assert "may_substitute_python_reference" in source


def test_flexible_raft_d6_compliant_sidecar_template_is_reproducible_and_empty():
    generated = build_flexible_raft_d6_compliant_measured_results_sidecar_template()
    committed = json.loads(
        (
            REPO_ROOT / D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_SCHEMA
    assert committed["status"] == "compliant_measured_results_sidecar_template_empty"
    assert committed["target_id"] == "project_chrono_or_reviewed_compliant_model"
    assert committed["filled_result_count"] == 0
    assert set(committed["results"]) == set(REQUIRED_D6_FIXTURE_IDS)
    assert committed["promotion_gate"]["may_merge_into_measured_results_template"] is False
    for fixture_id, record in committed["results"].items():
        assert fixture_id in REQUIRED_D6_FIXTURE_IDS
        assert record["status"] == "not_measured"
        assert record["source_report"] == ""
        assert record["telemetry_sha256"] == ""
        assert record["engine_version"] == ""
        assert record["target_id"] == "project_chrono_or_reviewed_compliant_model"


def test_flexible_raft_d6_compliant_sidecar_merge_report_blocks_empty_template():
    sidecar = build_flexible_raft_d6_compliant_measured_results_sidecar_template()
    generated = build_flexible_raft_d6_compliant_measured_results_merge_report(sidecar)
    committed = json.loads(
        (
            REPO_ROOT / D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_SCHEMA
    assert committed["status"] == "blocked_pending_complete_compliant_measured_results"
    assert committed["can_merge"] is False
    assert committed["filled_fixture_count"] == 0
    assert committed["invalid_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    for fixture_report in committed["fixture_reports"]:
        assert "result_status_not_measured" in fixture_report["errors"]
        assert "missing_required_provenance" in fixture_report["errors"]
        assert fixture_report["missing_metric_count"] == fixture_report["required_metric_count"]


def test_flexible_raft_d6_compliant_sidecar_merge_populates_only_reference_target():
    sidecar = _synthetic_compliant_sidecar()
    report = build_flexible_raft_d6_compliant_measured_results_merge_report(sidecar)
    merged = merge_flexible_raft_d6_compliant_measured_results_sidecar(sidecar)
    comparison = build_flexible_raft_d6_comparison_report(merged["measured_results"])

    assert report["can_merge"] is True
    assert report["filled_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["filled_result_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["measured_results"]["project_chrono_or_reviewed_compliant_model"][
        "static_seat_load_sag"
    ]["status"] == "measured_engine_output"
    assert merged["measured_results"]["unreal_chaos_rigid_baseline"][
        "static_seat_load_sag"
    ]["status"] == "not_measured"
    assert comparison["failed_target_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert comparison["comparison_passed"] is False
    assert comparison["status"] == "measured_comparisons_failed"
    for fixture in comparison["fixtures"]:
        targets = {target["target_id"]: target for target in fixture["targets"]}
        assert targets["project_chrono_or_reviewed_compliant_model"]["status"] == (
            "passed_numeric_equivalence"
        )
        assert targets["unreal_chaos_rigid_baseline"]["status"] == (
            "incomplete_measured_result_provenance"
        )


def test_flexible_raft_d6_compliant_sidecar_merge_rejects_bad_fixture_payloads():
    sidecar = _synthetic_compliant_sidecar()
    del sidecar["results"]["pressure_flow_sweeps"]
    sidecar["results"]["static_seat_load_sag"]["telemetry_sha256"] = "bad-hash"
    sidecar["results"]["traveling_crew_shift"]["target_id"] = (
        "unreal_chaos_rigid_baseline"
    )
    sidecar["results"]["unexpected_fixture"] = {
        "source_report": "synthetic/unexpected.json",
        "telemetry_sha256": "a" * 64,
        "engine_version": "synthetic-test",
        "metrics": {"value": 1.0},
    }

    report = build_flexible_raft_d6_compliant_measured_results_merge_report(sidecar)

    assert report["can_merge"] is False
    assert report["missing_fixture_ids"] == ["pressure_flow_sweeps"]
    assert report["unexpected_fixture_ids"] == ["unexpected_fixture"]
    by_id = {fixture["fixture_id"]: fixture for fixture in report["fixture_reports"]}
    assert by_id["static_seat_load_sag"]["invalid_provenance_fields"] == [
        "telemetry_sha256"
    ]
    assert "target_id_mismatch" in by_id["traveling_crew_shift"]["errors"]


def test_flexible_raft_d6_compliant_sidecar_cli_merges_valid_sidecar(tmp_path):
    sidecar_path = tmp_path / "compliant_sidecar.json"
    report_path = tmp_path / "compliant_sidecar.merge_report.json"
    merged_path = tmp_path / "merged_measured_results.json"
    sidecar_path.write_text(
        json.dumps(_synthetic_compliant_sidecar(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    exit_code = merge_d6_compliant_measured_results_main(
        [
            "--compliant-sidecar",
            str(sidecar_path),
            "--report",
            str(report_path),
            "--output",
            str(merged_path),
        ]
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    merged = json.loads(merged_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["can_merge"] is True
    assert report["filled_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["filled_result_count"] == len(REQUIRED_D6_FIXTURE_IDS)


def test_flexible_raft_d6_chaos_sidecar_template_is_reproducible_and_empty():
    generated = build_flexible_raft_d6_chaos_measured_results_sidecar_template()
    committed = json.loads(
        (REPO_ROOT / D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert committed["schema"] == D6_CHAOS_MEASURED_RESULTS_SIDECAR_SCHEMA
    assert committed["status"] == "chaos_measured_results_sidecar_template_empty"
    assert committed["target_id"] == "unreal_chaos_rigid_baseline"
    assert committed["filled_result_count"] == 0
    assert set(committed["results"]) == set(REQUIRED_D6_FIXTURE_IDS)
    assert committed["promotion_gate"]["may_merge_into_measured_results_template"] is False
    for fixture_id, record in committed["results"].items():
        assert fixture_id in REQUIRED_D6_FIXTURE_IDS
        assert record["status"] == "not_measured"
        assert record["source_report"] == ""
        assert record["telemetry_sha256"] == ""
        assert record["engine_version"] == ""
        assert record["target_id"] == "unreal_chaos_rigid_baseline"


def test_flexible_raft_d6_chaos_sidecar_merge_report_blocks_empty_template():
    sidecar = build_flexible_raft_d6_chaos_measured_results_sidecar_template()
    generated = build_flexible_raft_d6_chaos_measured_results_merge_report(sidecar)
    committed = json.loads(
        (REPO_ROOT / D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert committed["schema"] == D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_SCHEMA
    assert committed["status"] == "blocked_pending_complete_chaos_measured_results"
    assert committed["can_merge"] is False
    assert committed["filled_fixture_count"] == 0
    assert committed["invalid_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    for fixture_report in committed["fixture_reports"]:
        assert "result_status_not_measured" in fixture_report["errors"]
        assert "missing_required_provenance" in fixture_report["errors"]
        assert fixture_report["missing_metric_count"] == fixture_report["required_metric_count"]


def test_flexible_raft_d6_chaos_sidecar_merge_populates_only_chaos_target():
    sidecar = _synthetic_chaos_sidecar()
    report = build_flexible_raft_d6_chaos_measured_results_merge_report(sidecar)
    merged = merge_flexible_raft_d6_chaos_measured_results_sidecar(sidecar)
    comparison = build_flexible_raft_d6_comparison_report(merged["measured_results"])

    assert report["can_merge"] is True
    assert report["filled_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["filled_result_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["measured_results"]["project_chrono_or_reviewed_compliant_model"][
        "static_seat_load_sag"
    ]["status"] == "not_measured"
    assert merged["measured_results"]["unreal_chaos_rigid_baseline"][
        "static_seat_load_sag"
    ]["status"] == "measured_engine_output"
    assert comparison["missing_target_count"] == 0
    assert comparison["failed_target_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert comparison["comparison_passed"] is False
    assert comparison["status"] == "measured_comparisons_failed"
    for fixture in comparison["fixtures"]:
        targets = {target["target_id"]: target for target in fixture["targets"]}
        assert targets["project_chrono_or_reviewed_compliant_model"]["status"] == (
            "incomplete_measured_result_provenance"
        )
        assert targets["project_chrono_or_reviewed_compliant_model"][
            "missing_provenance_fields"
        ] == ["source_report", "telemetry_sha256", "engine_version"]
        assert targets["unreal_chaos_rigid_baseline"]["status"] == (
            "recorded_baseline_delta"
        )


def test_flexible_raft_d6_chaos_sidecar_merge_rejects_bad_fixture_payloads():
    sidecar = _synthetic_chaos_sidecar()
    del sidecar["results"]["pressure_flow_sweeps"]
    sidecar["results"]["static_seat_load_sag"]["telemetry_sha256"] = "bad-hash"
    sidecar["results"]["traveling_crew_shift"]["metrics"].pop("port_roll_load_bias_nm")
    sidecar["results"]["unexpected_fixture"] = {
        "source_report": "synthetic/unexpected.json",
        "telemetry_sha256": "a" * 64,
        "engine_version": "synthetic-test",
        "metrics": {"value": 1.0},
    }

    report = build_flexible_raft_d6_chaos_measured_results_merge_report(sidecar)

    assert report["can_merge"] is False
    assert report["missing_fixture_ids"] == ["pressure_flow_sweeps"]
    assert report["unexpected_fixture_ids"] == ["unexpected_fixture"]
    by_id = {fixture["fixture_id"]: fixture for fixture in report["fixture_reports"]}
    assert by_id["static_seat_load_sag"]["invalid_provenance_fields"] == [
        "telemetry_sha256"
    ]
    assert "port_roll_load_bias_nm" in by_id["traveling_crew_shift"][
        "missing_metric_paths"
    ]


def test_flexible_raft_d6_chaos_sidecar_cli_merges_valid_sidecar(tmp_path):
    sidecar_path = tmp_path / "chaos_sidecar.json"
    report_path = tmp_path / "chaos_sidecar.merge_report.json"
    merged_path = tmp_path / "merged_measured_results.json"
    sidecar_path.write_text(
        json.dumps(_synthetic_chaos_sidecar(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    exit_code = merge_d6_chaos_measured_results_main(
        [
            "--chaos-sidecar",
            str(sidecar_path),
            "--report",
            str(report_path),
            "--output",
            str(merged_path),
        ]
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    merged = json.loads(merged_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["can_merge"] is True
    assert report["filled_fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert merged["filled_result_count"] == len(REQUIRED_D6_FIXTURE_IDS)


def test_flexible_raft_d6_comparison_cli_accepts_populated_measured_results(tmp_path):
    measured_payload = build_flexible_raft_d6_measured_results_template()
    measured_payload["measured_results"] = _synthetic_measured_results()
    measured_path = tmp_path / "measured_results.json"
    report_path = tmp_path / "comparison_report.json"
    measured_path.write_text(
        json.dumps(measured_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    exit_code = generate_d6_comparison_report_main(
        [
            "--measured-results",
            str(measured_path),
            "--output",
            str(report_path),
        ]
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["status"] == "measured_comparisons_passed_manual_promotion_required"
    assert report["all_measurements_present"] is True
    assert report["comparison_passed"] is True
    assert report["d6_complete"] is False
    assert report["promotion_gate"]["may_mark_d6_complete"] is True


def _synthetic_compliant_sidecar() -> dict[str, object]:
    sidecar = build_flexible_raft_d6_compliant_measured_results_sidecar_template()
    compliant_results = _synthetic_measured_results()[
        "project_chrono_or_reviewed_compliant_model"
    ]
    for fixture_id, payload in compliant_results.items():
        sidecar["results"][fixture_id].update(payload)
        sidecar["results"][fixture_id]["status"] = "measured_engine_output"
        sidecar["results"][fixture_id]["fixture_id"] = fixture_id
        sidecar["results"][fixture_id]["target_id"] = (
            "project_chrono_or_reviewed_compliant_model"
        )
    sidecar["status"] = "compliant_measured_results_sidecar_populated"
    sidecar["filled_result_count"] = len(REQUIRED_D6_FIXTURE_IDS)
    return sidecar


def _synthetic_chaos_sidecar() -> dict[str, object]:
    sidecar = build_flexible_raft_d6_chaos_measured_results_sidecar_template()
    chaos_results = _synthetic_measured_results()["unreal_chaos_rigid_baseline"]
    for fixture_id, payload in chaos_results.items():
        sidecar["results"][fixture_id].update(payload)
        sidecar["results"][fixture_id]["status"] = "measured_engine_output"
        sidecar["results"][fixture_id]["fixture_id"] = fixture_id
        sidecar["results"][fixture_id]["target_id"] = "unreal_chaos_rigid_baseline"
    sidecar["status"] = "chaos_measured_results_sidecar_populated"
    sidecar["filled_result_count"] = len(REQUIRED_D6_FIXTURE_IDS)
    return sidecar


def _synthetic_measured_results() -> dict[str, dict[str, dict[str, object]]]:
    suite = build_flexible_raft_d6_behavioral_suite()
    measured: dict[str, dict[str, dict[str, object]]] = {
        "project_chrono_or_reviewed_compliant_model": {},
        "unreal_chaos_rigid_baseline": {},
    }
    for fixture in suite["fixtures"]:
        for target_id in measured:
            measured[target_id][fixture["fixture_id"]] = {
                "source_report": f"synthetic/{target_id}/{fixture['fixture_id']}.json",
                "telemetry_sha256": "a" * 64,
                "engine_version": "synthetic-test",
                "metrics": json.loads(json.dumps(fixture["python_reference_metrics"])),
            }
    return measured
