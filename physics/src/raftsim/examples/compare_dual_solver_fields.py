"""Compare field frames from an existing PyClaw/C++ dual-solver run."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..comparison import compare_dual_solver_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
        output = run_dir / "field_comparison.json"

    report = compare_dual_solver_fields(args.dual_solver_run, output_path=output)
    print(f"report={output}")
    for frame in report.frame_comparisons:
        worst = max((*frame.field_errors, *frame.slope_errors), key=lambda summary: summary.linf)
        print(
            f"{frame.label}: wet_mismatch={frame.wet_mismatch_fraction:.6f} "
            f"worst={worst.field} linf={worst.linf:.6g}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
