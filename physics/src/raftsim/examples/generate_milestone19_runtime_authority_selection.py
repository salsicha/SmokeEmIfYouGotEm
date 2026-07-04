"""Generate the Milestone 19 runtime authority selection report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone19 import write_runtime_authority_selection_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--comparison-report",
        type=Path,
        default=Path("physics/reports/milestone19/chaos_vs_jolt_comparison.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("physics/reports/milestone19/runtime_authority_selection.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("physics/reports/milestone19/runtime_authority_selection.md"),
    )
    args = parser.parse_args(argv)

    report = write_runtime_authority_selection_report(
        comparison_report_path=args.comparison_report,
        output_json=args.output_json,
        output_md=args.output_md,
    )
    print(f"selection={args.output_json}")
    print(f"markdown={args.output_md}")
    print(f"decision={report.report['decision']}")
    print(f"selected_runtime={report.report['selected_runtime']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
