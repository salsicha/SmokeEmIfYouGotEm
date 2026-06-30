"""Generate a Milestone 18 parity-family retune summary report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_parity_family_retune_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-family", required=True)
    parser.add_argument("--gate-scenario-id", required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument(
        "--threshold-report",
        action="append",
        nargs=2,
        metavar=("SOLVER_MODE", "PATH"),
        required=True,
        help="Solver mode and threshold_evaluation.json path. Repeat for each mode.",
    )
    parser.add_argument(
        "--candidate-label",
        action="append",
        nargs=2,
        metavar=("SOLVER_MODE", "LABEL"),
        default=[],
        help="Optional human-readable candidate label for one solver mode.",
    )
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/parity_family_retune.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/parity_family_retune.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_parity_family_retune_report(
        scenario_family=args.scenario_family,
        gate_scenario_id=args.gate_scenario_id,
        reference_manifest=args.reference_manifest,
        threshold_reports={mode: path for mode, path in args.threshold_report},
        candidate_labels={mode: label for mode, label in args.candidate_label},
        notes=tuple(args.note),
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"retune_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed or report.partially_promoted else 1


if __name__ == "__main__":
    raise SystemExit(main())
