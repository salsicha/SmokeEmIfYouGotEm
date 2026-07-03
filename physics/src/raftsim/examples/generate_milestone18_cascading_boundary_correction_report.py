"""Generate the Milestone 18 South Fork cascading boundary-correction diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_cascading_boundary_correction_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corrected-threshold-report",
        type=Path,
        action="append",
        required=True,
        help="Corrected-boundary South Fork cascading threshold_evaluation.json path.",
    )
    parser.add_argument("--stale-comparison-report", type=Path)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/cascading_boundary_correction_diagnostic.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/cascading_boundary_correction_diagnostic.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_cascading_boundary_correction_report(
        tuple(args.corrected_threshold_report),
        stale_comparison_report=args.stale_comparison_report,
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    payload = report.to_json_dict()
    print(f"cascading_boundary_correction_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"flow_count={payload['summary']['flow_count']}")
    print(f"decision={payload['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
