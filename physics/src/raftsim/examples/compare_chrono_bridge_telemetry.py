"""Compare Chrono/custom-water bridge telemetry against PyClaw reference output."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..chrono_validation import compare_chrono_bridge_telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
    output = args.output or run_dir / "chrono_bridge_telemetry_comparison.json"
    report = compare_chrono_bridge_telemetry(args.dual_solver_run, output_path=output)
    print(f"report={output}")
    print(f"scenario={report.scenario_id}")
    print(f"outcome_match={report.outcome_match}")
    print(f"trajectory_position_delta={report.trajectory_position_delta:.6g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
