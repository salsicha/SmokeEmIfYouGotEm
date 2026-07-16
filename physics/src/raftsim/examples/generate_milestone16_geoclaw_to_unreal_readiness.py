"""Generate the Milestone 16 GeoClaw-to-Unreal live-water readiness gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..readiness import build_milestone16_geoclaw_readiness_report, write_json_artifact

SUMMARY_VERSION = "raftsim.milestone16.readiness_summary.v0"

REPORT_FILES = {
    "geoclaw_reference": "geoclaw_reference_runs.json",
    "cpp_solver": "cpp_solver_runs.json",
    "comparison": "geoclaw_cpp_comparisons.json",
    "geometry": "geometry_validation.json",
    "raft_coupling": "raft_coupling_validation.json",
    "runtime_profile": "runtime_profile.json",
    "regression_promotion": "regression_promotion_manifest.json",
}

SUMMARY_FILES = {
    "geoclaw_reference": "geoclaw_reference_summary.json",
    "cpp_solver": "cpp_solver_summary.json",
    "comparison": "geoclaw_cpp_comparison_summary.json",
    "geometry": "geometry_validation_summary.json",
    "raft_coupling": "raft_coupling_validation_summary.json",
    "runtime_profile": "runtime_profile_summary.json",
    "regression_promotion": "regression_promotion_summary.json",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/readiness/milestone_16"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    reports = _load_reports(args.report_dir)
    summaries = _build_summaries(reports, args.report_dir)

    for key, summary in summaries.items():
        write_json_artifact(args.output_dir / SUMMARY_FILES[key], summary)

    artifact_manifest = {
        "source_reports": {key: str(args.report_dir / filename) for key, filename in REPORT_FILES.items()},
        "summaries": {key: SUMMARY_FILES[key] for key in SUMMARY_FILES},
    }
    report = build_milestone16_geoclaw_readiness_report(
        geoclaw_reference_summary=summaries["geoclaw_reference"],
        cpp_summary=summaries["cpp_solver"],
        comparison_summary=summaries["comparison"],
        geometry_summary=summaries["geometry"],
        raft_coupling_summary=summaries["raft_coupling"],
        runtime_profile_summary=summaries["runtime_profile"],
        regression_promotion_summary=summaries["regression_promotion"],
        artifact_manifest=artifact_manifest,
    )
    json_path = report.write_json(args.output_dir / "geoclaw_to_unreal_readiness_report.json")
    markdown_path = report.write_markdown(args.output_dir / "geoclaw_to_unreal_readiness_report.md")
    print(f"readiness_report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"decision={report.decision.status}")
    print(f"approved_for_live_custom_water={report.decision.approved_for_unreal_production_start}")
    return 0


def _load_reports(report_dir: Path) -> dict[str, dict[str, Any]]:
    return {key: _load_json(report_dir / filename) for key, filename in REPORT_FILES.items()}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _build_summaries(reports: dict[str, dict[str, Any]], report_dir: Path) -> dict[str, dict[str, object]]:
    return {
        "geoclaw_reference": _geoclaw_reference_summary(
            reports["geoclaw_reference"],
            report_dir / REPORT_FILES["geoclaw_reference"],
        ),
        "cpp_solver": _cpp_solver_summary(
            reports["cpp_solver"],
            report_dir / REPORT_FILES["cpp_solver"],
        ),
        "comparison": _comparison_summary(
            reports["comparison"],
            report_dir / REPORT_FILES["comparison"],
        ),
        "geometry": _geometry_summary(
            reports["geometry"],
            report_dir / REPORT_FILES["geometry"],
        ),
        "raft_coupling": _raft_coupling_summary(
            reports["raft_coupling"],
            report_dir / REPORT_FILES["raft_coupling"],
        ),
        "runtime_profile": _runtime_profile_summary(
            reports["runtime_profile"],
            report_dir / REPORT_FILES["runtime_profile"],
        ),
        "regression_promotion": _regression_promotion_summary(
            reports["regression_promotion"],
            report_dir / REPORT_FILES["regression_promotion"],
        ),
    }


def _geoclaw_reference_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    records = _records(report, "records")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "scenario_count": _int_or_count(report, "scenario_count", records),
        "passed_count": _int_or_count(report, "passed_count", [record for record in records if record.get("passed")]),
        "failed_count": _int_or_count(report, "failed_count", [record for record in records if not record.get("passed")]),
        "full_solution_count": sum(1 for record in records if record.get("full_solution")),
    }


def _cpp_solver_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    records = _records(report, "records")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "scenario_count": len({record.get("gate_scenario_id") for record in records}),
        "run_count": _int_or_count(report, "run_count", records),
        "passed_count": _int_or_count(report, "passed_count", [record for record in records if record.get("passed")]),
        "failed_count": _int_or_count(report, "failed_count", [record for record in records if not record.get("passed")]),
    }


def _comparison_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    records = _records(report, "records")
    threshold_passed = [record for record in records if record.get("threshold_passed")]
    threshold_failed = [record for record in records if not record.get("threshold_passed")]
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "comparison_count": _int_or_count(report, "comparison_count", records),
        "threshold_passed_count": _int_or_count(report, "threshold_passed_count", threshold_passed),
        "threshold_failed_count": _int_or_count(report, "threshold_failed_count", threshold_failed),
        "solver_parity_count": int(report.get("solver_parity_count", 0)),
        "solver_parity_threshold_passed_count": int(
            report.get("solver_parity_threshold_passed_count", 0)
        ),
        "solver_parity_threshold_failed_count": int(
            report.get("solver_parity_threshold_failed_count", 0)
        ),
        "reference_playback_count": int(report.get("reference_playback_count", 0)),
        "reference_playback_threshold_passed_count": int(
            report.get("reference_playback_threshold_passed_count", 0)
        ),
        "solver_approval_blocked_count": int(
            report.get("solver_approval_blocked_count", len(records))
        ),
    }


def _geometry_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    cases = _records(report, "cases")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "case_count": _int_or_count(report, "case_count", cases),
        "passed_count": _int_or_count(report, "passed_count", [case for case in cases if case.get("passed")]),
        "failed_count": _int_or_count(report, "failed_count", [case for case in cases if not case.get("passed")]),
    }


def _raft_coupling_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    records = _records(report, "records")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "comparison_count": _int_or_count(report, "comparison_count", records),
        "passed_count": _int_or_count(report, "passed_count", [record for record in records if record.get("passed")]),
        "failed_count": _int_or_count(report, "failed_count", [record for record in records if not record.get("passed")]),
        "notes": list(report.get("notes", [])),
    }


def _runtime_profile_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    records = _records(report, "records")
    deterministic_replay = _records(report, "deterministic_replay")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed")),
        "run_count": _int_or_count(report, "run_count", records),
        "budget_passed_count": _int_or_count(report, "budget_passed_count", [record for record in records if record.get("passed")]),
        "budget_failed_count": _int_or_count(report, "budget_failed_count", [record for record in records if not record.get("passed")]),
        "deterministic_replay_count": len(deterministic_replay),
        "deterministic_replay_passed_count": sum(1 for replay in deterministic_replay if replay.get("passed")),
    }


def _regression_promotion_summary(report: dict[str, Any], source_report: Path) -> dict[str, object]:
    entries = _records(report, "entries")
    return {
        "summary_version": SUMMARY_VERSION,
        "source_report": str(source_report),
        "passed": bool(report.get("passed", bool(entries) and all(entry.get("passed") for entry in entries))),
        "entry_count": _int_or_count(report, "entry_count", entries),
        "geoclaw_cpp_fixture_count": _int_or_count(
            report,
            "geoclaw_cpp_fixture_count",
            [entry for entry in entries if entry.get("category") == "geoclaw_cpp"],
        ),
        "raft_artifact_count": _int_or_count(
            report,
            "raft_artifact_count",
            [entry for entry in entries if entry.get("category") == "raft_coupling"],
        ),
    }


def _records(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = report.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list.")
    return [record for record in value if isinstance(record, dict)]


def _int_or_count(report: dict[str, Any], key: str, fallback_records: list[dict[str, Any]]) -> int:
    value = report.get(key)
    return int(value) if isinstance(value, int) else len(fallback_records)


if __name__ == "__main__":
    raise SystemExit(main())
