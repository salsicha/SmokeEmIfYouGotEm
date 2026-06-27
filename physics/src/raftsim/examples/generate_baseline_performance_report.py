"""Generate baseline performance reports for canonical/generated scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..dual_solver import CppSolverRunConfig
from ..performance import build_baseline_performance_report
from ..profiling import (
    profile_cpp_solver_runs,
    profile_probe_export_runs,
    profile_pyclaw_reference_runs,
    profile_raft_coupling_runs,
)
from ..pyclaw_reference import PyClawRunConfig, canonical_pyclaw_scenarios


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--samples-per-run", type=int, default=120)
    parser.add_argument("--pyclaw-output-times", type=int, default=2)
    parser.add_argument("--include-pyclaw", action="store_true")
    parser.add_argument("--cpp-solver", type=Path, default=None, help="Optional path to raftsim_water_solver.")
    parser.add_argument("--cpp-steps", type=int, default=None)
    parser.add_argument("--cpp-frame-interval", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/performance_baseline"))
    args = parser.parse_args(argv)

    scenarios = canonical_pyclaw_scenarios(seed=args.seed)
    profile_reports = [
        profile_raft_coupling_runs(
            scenarios,
            repetitions=args.repetitions,
            samples_per_run=args.samples_per_run,
        ),
        profile_probe_export_runs(
            scenarios,
            config=PyClawRunConfig(num_output_times=args.pyclaw_output_times),
            repetitions=args.repetitions,
            output_dir=args.output_dir / "probe_exports",
        ),
    ]
    if args.include_pyclaw:
        profile_reports.append(
            profile_pyclaw_reference_runs(
                scenarios,
                config=PyClawRunConfig(num_output_times=args.pyclaw_output_times),
                repetitions=args.repetitions,
                output_dir=args.output_dir / "pyclaw_runs",
            )
        )
    if args.cpp_solver is not None:
        profile_reports.append(
            profile_cpp_solver_runs(
                scenarios,
                config=CppSolverRunConfig(
                    executable=args.cpp_solver,
                    steps=args.cpp_steps,
                    frame_interval=args.cpp_frame_interval,
                ),
                repetitions=args.repetitions,
                output_dir=args.output_dir / "cpp_runs",
            )
        )

    report = build_baseline_performance_report(tuple(profile_reports))
    json_path = report.write_json(args.output_dir / "baseline_performance_report.json")
    markdown_path = report.write_markdown(args.output_dir / "baseline_performance_report.md")
    print(f"json={json_path}")
    print(f"markdown={markdown_path}")
    print(f"scenarios={len(report.scenario_ids)}")
    print(f"profile_groups={len(report.summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
