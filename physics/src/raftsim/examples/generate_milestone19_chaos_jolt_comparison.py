"""Generate the Milestone 19 Chaos-vs-Jolt comparison report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone19 import write_chaos_jolt_comparison_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json"),
    )
    parser.add_argument(
        "--chaos-summary",
        type=Path,
        default=Path("physics/reports/milestone19/chaos/summary.json"),
    )
    parser.add_argument(
        "--jolt-summary",
        type=Path,
        default=Path("physics/reports/milestone19/jolt/summary.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("physics/reports/milestone19/chaos_vs_jolt_comparison.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("physics/reports/milestone19/chaos_vs_jolt_comparison.md"),
    )
    args = parser.parse_args(argv)

    report = write_chaos_jolt_comparison_report(
        contract_path=args.contract,
        chaos_summary_path=args.chaos_summary,
        jolt_summary_path=args.jolt_summary,
        output_json=args.output_json,
        output_md=args.output_md,
    )
    print(f"comparison={args.output_json}")
    print(f"markdown={args.output_md}")
    print(f"decision={report.report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
