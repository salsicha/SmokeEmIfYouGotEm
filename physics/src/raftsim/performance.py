"""Baseline performance reporting for solver and coupling profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .profiling import ProfiledSolverRun, SolverProfileReport


@dataclass(frozen=True, slots=True)
class SolverPerformanceSummary:
    solver: str
    run_count: int
    scenario_count: int
    total_runtime_seconds: float
    mean_runtime_seconds: float
    max_runtime_seconds: float
    mean_seconds_per_simulated_second: float
    max_seconds_per_simulated_second: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "solver": self.solver,
            "run_count": self.run_count,
            "scenario_count": self.scenario_count,
            "total_runtime_seconds": self.total_runtime_seconds,
            "mean_runtime_seconds": self.mean_runtime_seconds,
            "max_runtime_seconds": self.max_runtime_seconds,
            "mean_seconds_per_simulated_second": self.mean_seconds_per_simulated_second,
            "max_seconds_per_simulated_second": self.max_seconds_per_simulated_second,
        }


@dataclass(frozen=True, slots=True)
class BaselinePerformanceReport:
    scenario_ids: tuple[str, ...]
    summaries: tuple[SolverPerformanceSummary, ...]
    runs: tuple[ProfiledSolverRun, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_ids": list(self.scenario_ids),
            "summaries": [summary.to_json_dict() for summary in self.summaries],
            "runs": [run.to_json_dict() for run in self.runs],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path

    def write_markdown(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Baseline Performance Report",
            "",
            f"Scenarios: {len(self.scenario_ids)}",
            "",
            "| Solver | Runs | Scenarios | Mean Runtime (s) | Max Runtime (s) | Mean s/sim-s | Max s/sim-s |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for summary in self.summaries:
            lines.append(
                "| "
                f"{summary.solver} | "
                f"{summary.run_count} | "
                f"{summary.scenario_count} | "
                f"{summary.mean_runtime_seconds:.6f} | "
                f"{summary.max_runtime_seconds:.6f} | "
                f"{summary.mean_seconds_per_simulated_second:.6f} | "
                f"{summary.max_seconds_per_simulated_second:.6f} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def build_baseline_performance_report(profile_reports: tuple[SolverProfileReport, ...]) -> BaselinePerformanceReport:
    """Aggregate solver/coupling profile reports into one baseline report."""

    runs = tuple(run for report in profile_reports for run in report.runs)
    scenario_ids = tuple(sorted({run.scenario_id for run in runs}))
    summaries = tuple(_summarize_solver(report) for report in profile_reports)
    return BaselinePerformanceReport(scenario_ids=scenario_ids, summaries=summaries, runs=runs)


def _summarize_solver(report: SolverProfileReport) -> SolverPerformanceSummary:
    scenario_ids = {run.scenario_id for run in report.runs}
    max_seconds_per_simulated_second = max((run.seconds_per_simulated_second for run in report.runs), default=0.0)
    return SolverPerformanceSummary(
        solver=report.solver,
        run_count=len(report.runs),
        scenario_count=len(scenario_ids),
        total_runtime_seconds=report.total_runtime_seconds,
        mean_runtime_seconds=report.mean_runtime_seconds,
        max_runtime_seconds=report.max_runtime_seconds,
        mean_seconds_per_simulated_second=report.mean_seconds_per_simulated_second,
        max_seconds_per_simulated_second=max_seconds_per_simulated_second,
    )
