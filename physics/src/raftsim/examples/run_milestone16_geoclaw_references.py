"""Run Milestone 16 full GeoClaw reference simulations and write reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_geoclaw_reference_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/m16g"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    parser.add_argument("--seed", type=int, default=16)
    parser.add_argument("--num-output-times", type=int, default=2)
    parser.add_argument("--amr-min-level", type=int, default=1)
    parser.add_argument("--amr-max-level", type=int, default=1)
    parser.add_argument("--canonical-nx", type=int, default=24)
    parser.add_argument("--canonical-ny", type=int, default=12)
    parser.add_argument("--real-world-nx", type=int, default=32)
    parser.add_argument("--real-world-ny", type=int, default=16)
    parser.add_argument("--cascading-nx", type=int, default=56)
    parser.add_argument("--cascading-ny", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    args = parser.parse_args(argv)

    report = run_milestone16_geoclaw_reference_suite(
        args.output_dir,
        seed=args.seed,
        num_output_times=args.num_output_times,
        amr_min_level=args.amr_min_level,
        amr_max_level=args.amr_max_level,
        canonical_nx=args.canonical_nx,
        canonical_ny=args.canonical_ny,
        real_world_nx=args.real_world_nx,
        real_world_ny=args.real_world_ny,
        cascading_nx=args.cascading_nx,
        cascading_ny=args.cascading_ny,
        timeout_seconds=args.timeout_seconds,
    )
    json_path = report.write_json(args.report_dir / "geoclaw_reference_runs.json")
    markdown_path = report.write_markdown(args.report_dir / "geoclaw_reference_runs.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"scenarios={len(report.records)}")
    print(f"passed={report.passed}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
