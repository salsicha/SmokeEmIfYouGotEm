"""Promote passing Milestone 16 validation artifacts into regression manifests."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_regression_promotion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-report", type=Path, default=Path("reports/milestone16/geoclaw_cpp_comparisons.json"))
    parser.add_argument("--raft-report", type=Path, default=Path("reports/milestone16/raft_coupling_validation.json"))
    parser.add_argument("--fixture-root", type=Path, default=Path("regression_fixtures/milestone16"))
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_regression_promotion(
        args.comparison_report,
        args.raft_report,
        fixture_root=args.fixture_root,
        registry_path=args.registry,
    )
    json_path = report.write_json(args.report_dir / "regression_promotion_manifest.json")
    markdown_path = report.write_markdown(args.report_dir / "regression_promotion_manifest.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"registry={report.registry_path}")
    print(f"entries={len(report.entries)}")
    print(f"passed={report.passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
