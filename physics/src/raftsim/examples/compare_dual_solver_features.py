"""Compare feature-local responses from an existing dual-solver run."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..comparison import compare_dual_solver_features


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
        output = run_dir / "feature_comparison.json"

    report = compare_dual_solver_features(args.dual_solver_run, output_path=output)
    print(f"report={output}")
    print(f"feature_count={report.feature_count}")
    print(f"max_location_delta={report.max_location_delta:.6g}")
    print(f"max_abs_strength_delta={report.max_abs_strength_delta:.6g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
