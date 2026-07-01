"""Generate the Milestone 18 constriction upstream edge balance diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_constriction_upstream_edge_balance_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--face-state-width-depth-report", type=Path, required=True)
    parser.add_argument("--face-source-audit-report", type=Path, required=True)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/constriction_upstream_edge_balance_diagnostic.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/constriction_upstream_edge_balance_diagnostic.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_constriction_upstream_edge_balance_report(
        args.face_state_width_depth_report,
        args.face_source_audit_report,
        top_n=args.top_n,
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"constriction_upstream_edge_balance_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
