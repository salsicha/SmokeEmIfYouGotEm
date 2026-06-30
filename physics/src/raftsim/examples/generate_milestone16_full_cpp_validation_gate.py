"""Generate the Milestone 16 suite-level full C++ validation gate report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import build_milestone16_full_cpp_validation_gate_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/milestone16/full_cpp_validation_gate.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/milestone16/full_cpp_validation_gate.md"))
    args = parser.parse_args(argv)

    report = build_milestone16_full_cpp_validation_gate_report(args.report_dir)
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    blocked = ",".join(component.component_id for component in report.components if not component.passed)
    print(f"suite_report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"decision={'PASS' if report.passed else 'BLOCKED'}")
    print(f"blocked_components={blocked}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
