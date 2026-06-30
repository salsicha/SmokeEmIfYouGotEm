import csv
import json

import numpy as np

from raftsim.analytic_fixtures import ANALYTIC_FIXTURE_IDS, write_analytic_fixture_suite
from raftsim.analytic_validation import (
    ANALYTIC_VALIDATION_REPORT_SCHEMA_VERSION,
    compare_analytic_fixture_manifest,
)


def test_analytic_validation_report_passes_for_generated_scenario_initial_states(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")
    report = compare_analytic_fixture_manifest(manifest_path)
    payload = report.to_json_dict()

    assert report.passed is True
    assert payload["schema_version"] == ANALYTIC_VALIDATION_REPORT_SCHEMA_VERSION
    assert payload["fixture_count"] == len(ANALYTIC_FIXTURE_IDS)
    assert payload["failed_count"] == 0

    json_path = report.write_json(tmp_path / "report.json")
    md_path = report.write_markdown(tmp_path / "report.md")
    assert json.loads(json_path.read_text(encoding="utf-8"))["passed"] is True
    assert "Decision: **PASS**" in md_path.read_text(encoding="utf-8")


def test_analytic_validation_report_fails_when_fixture_regresses(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")
    state_path = (
        manifest_path.parent
        / "fixtures"
        / "lake_at_rest_balance"
        / "scenario"
        / "initial_state.npz"
    )
    with np.load(state_path) as state:
        payload = {key: np.asarray(state[key]) for key in state.files}
    payload["eta"] = payload["eta"] + 0.01
    np.savez_compressed(state_path, **payload)

    report = compare_analytic_fixture_manifest(manifest_path)

    assert report.passed is False
    failed = next(comparison for comparison in report.comparisons if comparison.fixture_id == "lake_at_rest_balance")
    assert failed.passed is False
    assert any(metric.metric_id == "surface_linf" and not metric.passed for metric in failed.metrics)


def test_analytic_validation_can_compare_cpp_frame_csv_manifests(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["fixtures"]:
        fixture_id = entry["fixture_id"]
        fixture_root = manifest_path.parent / "fixtures" / fixture_id
        with np.load(fixture_root / "reference_fields.npz") as fields:
            reference = {key: np.asarray(fields[key]) for key in fields.files}
        cpp_root = tmp_path / "cpp_candidates" / fixture_id
        frame_dir = cpp_root / "frames"
        frame_dir.mkdir(parents=True)
        frame_path = frame_dir / "frame_0000.csv"
        with frame_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                (
                    "row",
                    "col",
                    "x",
                    "y",
                    "h",
                    "eta",
                    "u",
                    "v",
                    "hu",
                    "hv",
                    "wet",
                    "normal_x",
                    "normal_y",
                    "normal_z",
                    "froude",
                )
            )
            for row in range(reference["depth"].shape[0]):
                for col in range(reference["depth"].shape[1]):
                    writer.writerow(
                        (
                            row,
                            col,
                            col,
                            row,
                            reference["depth"][row, col],
                            reference["eta"][row, col],
                            reference["u"][row, col],
                            reference["v"][row, col],
                            reference["hu"][row, col],
                            reference["hv"][row, col],
                            int(reference["wet"][row, col]),
                            0.0,
                            0.0,
                            1.0,
                            0.0,
                        )
                    )
        (cpp_root / "manifest.json").write_text(
            json.dumps({"scenario_id": f"analytic_{fixture_id}", "frames": ["frames/frame_0000.csv"]}),
            encoding="utf-8",
        )

    report = compare_analytic_fixture_manifest(
        manifest_path,
        candidate_kind="cpp",
        candidate_root=tmp_path / "cpp_candidates",
    )

    lake = next(comparison for comparison in report.comparisons if comparison.fixture_id == "lake_at_rest_balance")
    assert lake.passed is True
