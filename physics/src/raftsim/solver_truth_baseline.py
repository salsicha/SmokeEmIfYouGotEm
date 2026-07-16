"""Build an auditable uncalibrated GeoClaw-versus-C++ truth baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SOLVER_TRUTH_BASELINE_SCHEMA = "raftsim.solver_truth_baseline.v0"
EXPECTED_MILESTONE16_COMPARISON_COUNT = 40


@dataclass(frozen=True, slots=True)
class SolverTruthBaseline:
    """A 40-row comparison that is valid only when fixture calibrations are disabled."""

    source_commit: str
    solver_binary_sha256: str
    geoclaw_reference_report: str
    cpp_run_report: str
    comparison_report: str
    records: tuple[dict[str, Any], ...]

    @property
    def passed_count(self) -> int:
        return sum(1 for record in self.records if record["threshold_passed"])

    @property
    def failed_count(self) -> int:
        return len(self.records) - self.passed_count

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SOLVER_TRUTH_BASELINE_SCHEMA,
            "measurement_mode": "uncalibrated_solver",
            "fixture_calibrations_disabled": True,
            "source_commit": self.source_commit,
            "solver_binary_sha256": self.solver_binary_sha256,
            "source_reports": {
                "geoclaw_reference": self.geoclaw_reference_report,
                "cpp_runs": self.cpp_run_report,
                "comparisons": self.comparison_report,
            },
            "comparison_count": len(self.records),
            "threshold_passed_count": self.passed_count,
            "threshold_failed_count": self.failed_count,
            "passed": bool(self.records) and self.failed_count == 0,
            "records": list(self.records),
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output_path

    def write_markdown(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Uncalibrated C++ Solver Truth Baseline",
            "",
            f"Schema: `{SOLVER_TRUTH_BASELINE_SCHEMA}`",
            "",
            "Fixture calibrations and reference playback: **DISABLED**",
            "",
            f"Threshold result: **{self.passed_count} PASS / {self.failed_count} FAIL / {len(self.records)} TOTAL**",
            "",
            f"Source commit: `{self.source_commit}`",
            "",
            f"Solver binary SHA-256: `{self.solver_binary_sha256}`",
            "",
            "| # | Suite | Gate scenario | Mode | Result | Actual error norms (`value / threshold`) |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
        for index, record in enumerate(self.records, start=1):
            norms = "; ".join(
                f"{name}={_format_metric(metric.get('value'))}/{_format_metric(metric.get('threshold'))}"
                for name, metric in sorted(record["error_norms"].items())
            )
            lines.append(
                f"| {index} | {record['suite']} | {record['gate_scenario_id']} | "
                f"{record['solver_mode']} | {'PASS' if record['threshold_passed'] else 'FAIL'} | {norms} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def build_solver_truth_baseline(
    comparison_report: dict[str, Any],
    cpp_run_report: dict[str, Any],
    *,
    comparison_report_path: str,
    cpp_run_report_path: str,
    source_commit: str,
    solver_binary_sha256: str,
    expected_comparison_count: int = EXPECTED_MILESTONE16_COMPARISON_COUNT,
) -> SolverTruthBaseline:
    """Validate uncalibrated provenance and preserve every row's actual threshold metrics."""

    comparison_records = comparison_report.get("records", [])
    cpp_records = cpp_run_report.get("records", [])
    if len(comparison_records) != expected_comparison_count:
        raise ValueError(
            f"Expected {expected_comparison_count} comparison rows, found {len(comparison_records)}."
        )
    if len(cpp_records) != expected_comparison_count:
        raise ValueError(f"Expected {expected_comparison_count} C++ run rows, found {len(cpp_records)}.")

    cpp_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for record in cpp_records:
        key = (str(record["gate_scenario_id"]), str(record["solver_mode"]))
        if key in cpp_by_key:
            raise ValueError(f"Duplicate C++ run row for {key[0]} / {key[1]}.")
        cpp_by_key[key] = record

    truth_records: list[dict[str, Any]] = []
    for record in comparison_records:
        key = (str(record["gate_scenario_id"]), str(record["solver_mode"]))
        cpp_record = cpp_by_key.get(key)
        if cpp_record is None:
            raise ValueError(f"Missing C++ run row for {key[0]} / {key[1]}.")
        settings = cpp_record.get("manifest_settings", {})
        if settings.get("disable_fixture_calibrations") is not True:
            raise ValueError(f"C++ row {key[0]} / {key[1]} did not disable fixture calibrations.")
        checks = record.get("check_values", {})
        if not checks:
            raise ValueError(f"Comparison row {key[0]} / {key[1]} has no error norms.")
        truth_records.append(
            {
                "gate_scenario_id": key[0],
                "actual_scenario_id": str(record["actual_scenario_id"]),
                "suite": str(record["suite"]),
                "solver_mode": key[1],
                "threshold_tier": str(record["threshold_tier"]),
                "threshold_passed": bool(record["threshold_passed"]),
                "failing_checks": list(record.get("failing_checks", [])),
                "error_norms": checks,
            }
        )

    return SolverTruthBaseline(
        source_commit=source_commit,
        solver_binary_sha256=solver_binary_sha256,
        geoclaw_reference_report=str(comparison_report["geoclaw_reference_report"]),
        cpp_run_report=cpp_run_report_path,
        comparison_report=comparison_report_path,
        records=tuple(truth_records),
    )


def _format_metric(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)
