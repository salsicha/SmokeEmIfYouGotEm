"""Validate Milestone 16 geometry-specific shallow-water cases."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_geometry_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-report", type=Path, default=Path("reports/milestone16/geoclaw_cpp_comparisons.json"))
    parser.add_argument("--geoclaw-report", type=Path, default=Path("reports/milestone16/geoclaw_reference_runs.json"))
    parser.add_argument("--milestone18-report-dir", type=Path, default=Path("reports/milestone18"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_geometry_validation(
        args.comparison_report,
        args.geoclaw_report,
        milestone18_report_dir=args.milestone18_report_dir,
    )
    json_path = report.write_json(args.report_dir / "geometry_validation.json")
    markdown_path = report.write_markdown(args.report_dir / "geometry_validation.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"cases={len(report.cases)}")
    print(f"passed={report.passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
