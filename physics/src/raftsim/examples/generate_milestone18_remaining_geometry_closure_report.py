"""Generate the Milestone 18 remaining geometry-closure queue."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_remaining_geometry_closure_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-report", type=Path, default=Path("reports/milestone16/geometry_validation.json"))
    parser.add_argument(
        "--focused-report",
        type=Path,
        action="append",
        default=[],
        help="Focused Milestone 18 diagnostic JSON to attach to the matching geometry family.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/remaining_geometry_closure.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/remaining_geometry_closure.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_remaining_geometry_closure_report(
        args.geometry_report,
        focused_reports=tuple(args.focused_report),
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"remaining_geometry_closure_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
