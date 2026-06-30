"""Compare Milestone 16 GeoClaw and C++ outputs against frozen thresholds."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_comparison_matrix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geoclaw-report", type=Path, default=Path("reports/milestone16/geoclaw_reference_runs.json"))
    parser.add_argument("--cpp-report", type=Path, default=Path("reports/milestone16/cpp_solver_runs.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/m16cmp"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_comparison_matrix(
        args.geoclaw_report,
        args.cpp_report,
        output_root=args.output_dir,
    )
    json_path = report.write_json(args.report_dir / "geoclaw_cpp_comparisons.json")
    markdown_path = report.write_markdown(args.report_dir / "geoclaw_cpp_comparisons.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"comparisons={len(report.records)}")
    print(f"threshold_passed={report.passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
