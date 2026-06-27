"""Compare probe and cross-section outputs from a dual-solver run."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..comparison import compare_dual_solver_probes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
        output = run_dir / "probe_comparison.json"

    report = compare_dual_solver_probes(args.dual_solver_run, output_path=output)
    print(f"report={output}")
    print(f"point_probes={len(report.point_probes)}")
    print(f"cross_sections={len(report.cross_sections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
