"""Validate Milestone 16 raft coupling against GeoClaw and C++ water fields."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_raft_coupling_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geoclaw-report", type=Path, default=Path("reports/milestone16/geoclaw_reference_runs.json"))
    parser.add_argument("--cpp-report", type=Path, default=Path("reports/milestone16/cpp_solver_runs.json"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_raft_coupling_validation(args.geoclaw_report, args.cpp_report)
    json_path = report.write_json(args.report_dir / "raft_coupling_validation.json")
    markdown_path = report.write_markdown(args.report_dir / "raft_coupling_validation.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"comparisons={len(report.records)}")
    print(f"passed={report.passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
