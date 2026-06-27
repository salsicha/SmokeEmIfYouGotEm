"""Generate Milestone 10 Python-to-Unreal readiness artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ..comparison import evaluate_dual_solver_thresholds
from ..dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_cpp_solver_scenario, run_dual_solver_scenario
from ..performance import build_baseline_performance_report
from ..profiling import (
    profile_cpp_solver_runs,
    profile_probe_export_runs,
    profile_pyclaw_reference_runs,
    profile_raft_coupling_runs,
)
from ..pyclaw_reference import PyClawRunConfig, check_pyclaw_availability, run_pyclaw_reference
from ..readiness import (
    build_adaptive_flow_validation,
    build_milestone10_scenario_suite,
    build_readiness_report,
    check_from_summary,
    summarize_performance_report,
    write_json_artifact,
    write_unreal_visualization_exports,
)
from ..real_world import build_real_world_corridor_package, default_player_selections, generate_real_world_scenario2_5d
from ..tuning import CppTuningCandidate, tune_cpp_solver_against_pyclaw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("physics/data/readiness/milestone_10"))
    parser.add_argument("--scratch-dir", type=Path, default=Path("outputs/readiness_solver_runs"))
    parser.add_argument("--cpp-solver", type=Path, default=None)
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.scratch_dir.mkdir(parents=True, exist_ok=True)
    scenarios = build_milestone10_scenario_suite()
    scenario_summary = _scenario_summary(scenarios)
    write_json_artifact(args.output_dir / "scenario_suite.json", scenario_summary)

    pyclaw_summary = _run_pyclaw_summary(scenarios, args.scratch_dir / "pyclaw_reference")
    write_json_artifact(args.output_dir / "pyclaw_reference_summary.json", pyclaw_summary)

    cpp_summary = _run_cpp_summary(scenarios, args.cpp_solver, args.scratch_dir / "cpp_solver")
    write_json_artifact(args.output_dir / "cpp_solver_summary.json", cpp_summary)

    dual_summary = _run_dual_and_tuning_summary(scenarios, args.cpp_solver, args.scratch_dir / "dual_solver")
    write_json_artifact(args.output_dir / "dual_solver_comparison_summary.json", dual_summary)

    raft_summary = _build_raft_coupling_summary(scenarios)
    write_json_artifact(args.output_dir / "raft_coupling_validation.json", raft_summary)

    adaptive_flow = build_adaptive_flow_validation()
    write_json_artifact(args.output_dir / "adaptive_flow_validation.json", adaptive_flow)

    performance = _build_performance_summary(scenarios, args.cpp_solver, args.scratch_dir / "profiles")
    performance = _scrub_transient_paths(performance)
    write_json_artifact(args.output_dir / "profiling_runtime_budget_report.json", performance)

    visualization_manifest = write_unreal_visualization_exports(args.output_dir / "unreal_visualization")
    corridor = build_real_world_corridor_package()
    corridor_manifest = {
        "corridor_package_version": "raftsim.unreal_preproduction_corridor.v0",
        "river_id": corridor.section.river_id,
        "section_id": corridor.section.section_id,
        "source_manifest": "physics/data/real_world/south_fork_american_chili_bar/source_manifest.json",
        "real_world_package": "physics/data/real_world/south_fork_american_chili_bar",
        "unreal_ready_artifacts": corridor.unreal_ready_artifacts,
        "flow_bands": [band.flow_band for band in corridor.flow_bands],
        "rapid_candidate_count": len(corridor.rapid_candidates),
        "confidence": corridor.source_manifest["confidence"],
    }
    write_json_artifact(args.output_dir / "unreal_corridor_package_manifest.json", corridor_manifest)

    checks = _readiness_checks(
        pyclaw_summary=pyclaw_summary,
        cpp_summary=cpp_summary,
        dual_summary=dual_summary,
        raft_summary=raft_summary,
        adaptive_flow=adaptive_flow,
        performance=performance,
        visualization_manifest=visualization_manifest,
        corridor_manifest=corridor_manifest,
    )
    report = build_readiness_report(
        checks,
        artifact_manifest={
            "scenario_suite": "scenario_suite.json",
            "pyclaw_reference_summary": "pyclaw_reference_summary.json",
            "cpp_solver_summary": "cpp_solver_summary.json",
            "dual_solver_comparison_summary": "dual_solver_comparison_summary.json",
            "raft_coupling_validation": "raft_coupling_validation.json",
            "adaptive_flow_validation": "adaptive_flow_validation.json",
            "profiling_runtime_budget_report": "profiling_runtime_budget_report.json",
            "unreal_visualization": "unreal_visualization/manifest.json",
            "unreal_corridor_package_manifest": "unreal_corridor_package_manifest.json",
        },
    )
    report.write_json(args.output_dir / "python_to_unreal_readiness_report.json")
    report.write_markdown(args.output_dir / "python_to_unreal_readiness_report.md")
    print(f"readiness_report={args.output_dir / 'python_to_unreal_readiness_report.json'}")
    print(f"decision={report.decision.status}")
    return 0


def _scenario_summary(scenarios):
    return {
        "scenario_suite_version": "raftsim.milestone10_scenarios.v0",
        "scenarios": [
            {
                "scenario_id": scenario.metadata.scenario_id,
                "scenario_type": scenario.metadata.scenario_type,
                "fixture_kind": scenario.metadata.fixture_kind,
                "river_id": scenario.metadata.river_id,
                "section_id": scenario.metadata.section_id,
                "season_preset": scenario.metadata.season_preset,
                "flow_band": scenario.metadata.flow_band,
                "difficulty_preset": scenario.metadata.difficulty_preset,
                "grid_cells": scenario.grid.nx * scenario.grid.ny,
                "duration": scenario.duration,
                "fixed_dt": scenario.fixed_dt,
                "provenance": scenario.metadata.provenance,
            }
            for scenario in scenarios
        ],
    }


def _run_pyclaw_summary(scenarios, output_dir: Path) -> dict[str, object]:
    availability = check_pyclaw_availability()
    rows = []
    if not availability.available:
        return {"available": False, "reason": availability.reason, "passed": False, "runs": rows}
    config = PyClawRunConfig(num_output_times=1, mass_relative_tolerance=0.10)
    for scenario in scenarios:
        try:
            result = run_pyclaw_reference(scenario, config=config, output_dir=output_dir / scenario.metadata.scenario_id)
            rows.append(
                {
                    "scenario_id": scenario.metadata.scenario_id,
                    "passed": result.validation.passed,
                    "frame_count": len(result.frames),
                    "mass_relative_drift": result.validation.mass_relative_drift,
                    "max_velocity": result.validation.max_velocity,
                    "min_depth": result.validation.min_depth,
                    "checks": [check.to_json_dict() for check in result.validation.checks],
                }
            )
        except Exception as exc:  # pragma: no cover - exact PyClaw failure can vary by platform.
            rows.append({"scenario_id": scenario.metadata.scenario_id, "passed": False, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "available": True,
        "pyclaw_version": availability.pyclaw_version,
        "passed": all(bool(row["passed"]) for row in rows),
        "run_count": len(rows),
        "solver_outputs_committed": False,
        "runs": rows,
    }


def _run_cpp_summary(scenarios, cpp_solver: Path | None, output_dir: Path) -> dict[str, object]:
    if cpp_solver is None:
        return {"available": False, "passed": False, "reason": "--cpp-solver was not provided.", "runs": []}
    rows = []
    for scenario in scenarios:
        steps = max(1, int(math.ceil(scenario.duration / scenario.fixed_dt)))
        result = run_cpp_solver_scenario(
            scenario,
            output_dir=output_dir / scenario.metadata.scenario_id,
            config=CppSolverRunConfig(executable=cpp_solver, steps=steps, frame_interval=steps),
        )
        validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "scenario_id": scenario.metadata.scenario_id,
                "returncode": result.returncode,
                "passed": result.returncode == 0 and bool(validation.get("passed")),
                "mass_relative_drift": validation.get("mass_relative_drift"),
                "max_velocity": validation.get("max_velocity"),
                "min_depth": validation.get("min_depth"),
            }
        )
    return {
        "available": True,
        "passed": all(bool(row["passed"]) for row in rows),
        "run_count": len(rows),
        "solver_outputs_committed": False,
        "runs": rows,
    }


def _run_dual_and_tuning_summary(scenarios, cpp_solver: Path | None, output_dir: Path) -> dict[str, object]:
    if cpp_solver is None or not check_pyclaw_availability().available:
        return {
            "available": False,
            "passed": False,
            "reason": "PyClaw and --cpp-solver are required for dual-solver comparison.",
            "comparisons": [],
            "tuning": None,
        }
    comparison_scenarios = [scenarios[0], next(scenario for scenario in scenarios if scenario.metadata.scenario_type == "real_world" and scenario.metadata.flow_band == "median_runnable")]
    comparisons = []
    for scenario in comparison_scenarios:
        steps = max(1, int(math.ceil(scenario.duration / scenario.fixed_dt)))
        run_result = run_dual_solver_scenario(
            scenario,
            output_dir=output_dir / "comparisons" / scenario.metadata.scenario_id,
            config=DualSolverRunConfig(
                pyclaw=PyClawRunConfig(num_output_times=1, mass_relative_tolerance=0.10),
                cpp=CppSolverRunConfig(executable=cpp_solver, steps=steps, frame_interval=steps),
            ),
        )
        thresholds = evaluate_dual_solver_thresholds(
            run_result.output_dir,
            output_path=run_result.output_dir / "threshold_evaluation.json",
        )
        comparisons.append(
            {
                "scenario_id": scenario.metadata.scenario_id,
                "passed": thresholds.passed,
                "checks": [check.to_json_dict() for check in thresholds.checks],
            }
        )
    tuning_report = tune_cpp_solver_against_pyclaw(
        scenarios[0],
        output_dir=output_dir / "tuning",
        cpp_solver_executable=cpp_solver,
        candidates=(
            CppTuningCandidate("baseline", feature_strength_scale=1.0, roughness_scale=1.0),
            CppTuningCandidate("rougher", feature_strength_scale=1.0, roughness_scale=1.2),
        ),
        pyclaw_config=PyClawRunConfig(num_output_times=1, mass_relative_tolerance=0.10),
        cpp_steps=max(1, int(math.ceil(scenarios[0].duration / scenarios[0].fixed_dt))),
        cpp_frame_interval=max(1, int(math.ceil(scenarios[0].duration / scenarios[0].fixed_dt))),
    )
    return {
        "available": True,
        "passed": all(bool(comparison["passed"]) for comparison in comparisons),
        "comparisons": comparisons,
        "tuning": {
            "scenario_id": tuning_report.scenario_id,
            "best_candidate": tuning_report.best_candidate.candidate.to_json_dict(),
            "best_passed": tuning_report.best_candidate.passed,
            "candidate_count": len(tuning_report.candidates),
        },
    }


def _build_raft_coupling_summary(scenarios) -> dict[str, object]:
    profile = profile_raft_coupling_runs(scenarios, repetitions=1, samples_per_run=3)
    return {
        "validation_version": "raftsim.raft_coupling_readiness.v0",
        "passed": all(run.validation_passed for run in profile.runs),
        "summary": profile.to_json_dict()["summary"],
        "runs": [run.to_json_dict() for run in profile.runs],
    }


def _build_performance_summary(scenarios, cpp_solver: Path | None, output_dir: Path) -> dict[str, object]:
    reports = [
        profile_raft_coupling_runs(scenarios, repetitions=1, samples_per_run=3),
        profile_probe_export_runs(scenarios, repetitions=1, output_dir=output_dir / "probe_export"),
    ]
    if check_pyclaw_availability().available:
        reports.append(
            profile_pyclaw_reference_runs(
                (scenarios[0], scenarios[-2]),
                config=PyClawRunConfig(num_output_times=1, mass_relative_tolerance=0.10),
                repetitions=1,
                output_dir=output_dir / "pyclaw",
            )
        )
    if cpp_solver is not None:
        reports.append(
            profile_cpp_solver_runs(
                (scenarios[0], scenarios[-2]),
                config=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=3),
                repetitions=1,
                output_dir=output_dir / "cpp",
            )
        )
    report = build_baseline_performance_report(tuple(reports))
    return summarize_performance_report(report)


def _readiness_checks(
    *,
    pyclaw_summary: dict[str, object],
    cpp_summary: dict[str, object],
    dual_summary: dict[str, object],
    raft_summary: dict[str, object],
    adaptive_flow: dict[str, object],
    performance: dict[str, object],
    visualization_manifest: dict[str, object],
    corridor_manifest: dict[str, object],
):
    performance_has_runs = bool(performance.get("runs"))
    return (
        check_from_summary(
            "pyclaw_reference_scenarios",
            "PyClaw Reference Scenarios",
            bool(pyclaw_summary.get("passed")),
            f"{pyclaw_summary.get('run_count', 0)} PyClaw scenario runs completed.",
            ("pyclaw_reference_summary.json",),
        ),
        check_from_summary(
            "custom_cpp_solver_scenarios",
            "Custom C++ Solver Scenarios",
            bool(cpp_summary.get("passed")),
            f"{cpp_summary.get('run_count', 0)} C++ scenario runs completed.",
            ("cpp_solver_summary.json",),
        ),
        check_from_summary(
            "dual_solver_comparison_and_tuning",
            "Dual-Solver Comparison And Tuning",
            bool(dual_summary.get("passed")),
            "Dual comparison threshold reports and a tuning report were generated; real-world median currently determines gate status.",
            ("dual_solver_comparison_summary.json",),
        ),
        check_from_summary(
            "raft_coupling_validation",
            "2.5D Raft Coupling Validation",
            bool(raft_summary.get("passed")),
            "Raft coupling sampled force envelopes across the readiness scenario suite.",
            ("raft_coupling_validation.json",),
        ),
        check_from_summary(
            "real_world_section_package",
            "First Real-World River Section Package",
            bool(corridor_manifest.get("river_id")) and bool(corridor_manifest.get("unreal_ready_artifacts")),
            "South Fork American preproduction corridor package is exported with manifest, flow bands, rapid candidates, and confidence metadata.",
            ("unreal_corridor_package_manifest.json",),
        ),
        check_from_summary(
            "adaptive_flow_parameters",
            "Adaptive Flow Parameters",
            bool(adaptive_flow.get("passed")),
            "Low, median, and high runnable flow presets map monotonically into solver parameters.",
            ("adaptive_flow_validation.json",),
        ),
        check_from_summary(
            "profiling_runtime_budgets",
            "Profiling And Runtime Budget Reports",
            performance_has_runs,
            f"{len(performance.get('runs', []))} profiling runs recorded.",
            ("profiling_runtime_budget_report.json",),
        ),
        check_from_summary(
            "unreal_visualization_exports",
            "Unreal Replay And Telemetry Exports",
            int(visualization_manifest.get("frame_count", 0)) > 0 and int(visualization_manifest.get("force_row_count", 0)) > 0,
            "Representative replay and force telemetry files are exported for Unreal visualization.",
            ("unreal_visualization/replay.json", "unreal_visualization/telemetry_forces.csv"),
        ),
    )


def _scrub_transient_paths(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, child in value.items():
            if key in {"output_dir", "manifest", "validation"} and isinstance(child, str):
                cleaned[key] = "not committed; regenerate during validation work"
            else:
                cleaned[key] = _scrub_transient_paths(child)
        return cleaned
    if isinstance(value, list):
        return [_scrub_transient_paths(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
