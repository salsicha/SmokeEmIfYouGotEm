"""Generate the Milestone 18 GeoClaw/C++ failure triage matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_failure_triage_matrix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-report", type=Path, default=Path("reports/milestone16/geoclaw_cpp_comparisons.json"))
    parser.add_argument("--geometry-report", type=Path, default=Path("reports/milestone16/geometry_validation.json"))
    parser.add_argument("--raft-report", type=Path, default=Path("reports/milestone16/raft_coupling_validation.json"))
    parser.add_argument("--full-gate-report", type=Path, default=Path("reports/milestone16/full_cpp_validation_gate.json"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/milestone18/geoclaw_cpp_failure_triage_matrix.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/milestone18/geoclaw_cpp_failure_triage_matrix.md"))
    args = parser.parse_args(argv)

    report = build_milestone18_failure_triage_matrix(
        args.comparison_report,
        args.geometry_report,
        args.raft_report,
        args.full_gate_report,
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"triage_matrix={json_path}")
    print(f"markdown={markdown_path}")
    print(f"decision={'PASS' if report.passed else 'ACTION_REQUIRED'}")
    print(f"entry_count={len(report.entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
