"""Run the uncalibrated Milestone 16 matrix and write the solver-truth baseline."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from ..milestone16 import run_milestone16_comparison_matrix, run_milestone16_cpp_solver_matrix
from ..solver_truth_baseline import build_solver_truth_baseline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geoclaw-report", type=Path, default=Path("reports/milestone16/geoclaw_reference_runs.json"))
    parser.add_argument("--cpp-solver", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/solver_truth_baseline"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/solver_truth_baseline"))
    args = parser.parse_args(argv)

    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    solver_sha256 = hashlib.sha256(args.cpp_solver.read_bytes()).hexdigest()

    cpp_report = run_milestone16_cpp_solver_matrix(
        args.geoclaw_report,
        cpp_solver=args.cpp_solver,
        output_root=args.output_dir / "cpp",
        disable_fixture_calibrations=True,
    )
    cpp_report_path = cpp_report.write_json(args.output_dir / "cpp_solver_runs.json")
    cpp_report.write_markdown(args.output_dir / "cpp_solver_runs.md")

    comparison_report = run_milestone16_comparison_matrix(
        args.geoclaw_report,
        cpp_report_path,
        output_root=args.output_dir / "comparisons",
    )
    comparison_report_path = comparison_report.write_json(args.output_dir / "geoclaw_cpp_comparisons.json")
    comparison_report.write_markdown(args.output_dir / "geoclaw_cpp_comparisons.md")

    baseline = build_solver_truth_baseline(
        comparison_report.to_json_dict(),
        cpp_report.to_json_dict(),
        comparison_report_path=str(comparison_report_path),
        cpp_run_report_path=str(cpp_report_path),
        source_commit=source_commit,
        solver_binary_sha256=solver_sha256,
    )
    json_path = baseline.write_json(args.report_dir / "uncalibrated_baseline.json")
    markdown_path = baseline.write_markdown(args.report_dir / "uncalibrated_baseline.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"comparisons={len(baseline.records)}")
    print(f"passed={baseline.passed_count}")
    print(f"failed={baseline.failed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
