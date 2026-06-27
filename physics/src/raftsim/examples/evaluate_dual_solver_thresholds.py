"""Evaluate a dual-solver run against scenario pass/fail thresholds."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..comparison import ScenarioThresholds, evaluate_dual_solver_thresholds

DEFAULT_THRESHOLDS = ScenarioThresholds()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path, help="Run directory or dual_solver_manifest.json.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    parser.add_argument("--max-field-linf", type=float, default=DEFAULT_THRESHOLDS.max_field_linf)
    parser.add_argument("--max-slope-linf", type=float, default=DEFAULT_THRESHOLDS.max_slope_linf)
    parser.add_argument("--max-wet-mismatch-fraction", type=float, default=DEFAULT_THRESHOLDS.max_wet_mismatch_fraction)
    parser.add_argument("--max-probe-linf", type=float, default=DEFAULT_THRESHOLDS.max_probe_linf)
    parser.add_argument("--max-cross-section-linf", type=float, default=DEFAULT_THRESHOLDS.max_cross_section_linf)
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        run_dir = args.dual_solver_run.parent if args.dual_solver_run.name == "dual_solver_manifest.json" else args.dual_solver_run
        output = run_dir / "threshold_evaluation.json"

    report = evaluate_dual_solver_thresholds(
        args.dual_solver_run,
        thresholds=ScenarioThresholds(
            max_field_linf=args.max_field_linf,
            max_slope_linf=args.max_slope_linf,
            max_wet_mismatch_fraction=args.max_wet_mismatch_fraction,
            max_probe_linf=args.max_probe_linf,
            max_cross_section_linf=args.max_cross_section_linf,
        ),
        output_path=output,
    )
    print(f"report={output}")
    print(f"passed={report.passed}")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"{status} {check.name}: value={check.value:.6g} threshold={check.threshold:.6g}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
