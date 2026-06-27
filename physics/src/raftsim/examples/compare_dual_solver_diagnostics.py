"""Compare physical diagnostics from an existing dual-solver run."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..comparison import compare_dual_solver_diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
        output = run_dir / "diagnostic_comparison.json"

    report = compare_dual_solver_diagnostics(args.dual_solver_run, output_path=output)
    print(f"report={output}")
    print(f"mass_drift_delta={report.delta.mass_relative_drift_delta:.6g}")
    print(f"energy_change_delta={report.delta.energy_relative_change_delta:.6g}")
    print(f"froude_max_delta={report.delta.froude_max_delta:.6g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
