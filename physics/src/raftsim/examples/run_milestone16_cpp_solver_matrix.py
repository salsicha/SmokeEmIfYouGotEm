"""Run C++ reduced and finite-volume modes for Milestone 16 scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_cpp_solver_matrix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geoclaw-report", type=Path, default=Path("reports/milestone16/geoclaw_reference_runs.json"))
    parser.add_argument("--cpp-solver", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/m16cpp"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_cpp_solver_matrix(
        args.geoclaw_report,
        cpp_solver=args.cpp_solver,
        output_root=args.output_dir,
    )
    json_path = report.write_json(args.report_dir / "cpp_solver_runs.json")
    markdown_path = report.write_markdown(args.report_dir / "cpp_solver_runs.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"runs={len(report.records)}")
    print(f"passed={report.passed}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
