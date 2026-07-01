"""Generate the Milestone 18 constriction hydrostatic/source-split decision."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_constriction_hydrostatic_source_decision_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--face-source-audit-report",
        type=Path,
        default=Path("reports/milestone18/constriction_face_source_audit_diagnostic.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/constriction_hydrostatic_source_decision.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/constriction_hydrostatic_source_decision.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_constriction_hydrostatic_source_decision_report(args.face_source_audit_report)
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"constriction_hydrostatic_source_decision_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
