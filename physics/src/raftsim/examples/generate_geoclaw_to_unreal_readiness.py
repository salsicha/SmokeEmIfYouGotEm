"""Generate GeoClaw-to-Unreal readiness artifacts for Milestone 14."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..chrono_validation import compare_chrono_bridge_telemetry
from ..comparison import evaluate_dual_solver_thresholds
from ..dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
from ..geoclaw_reference import (
    GeoClawExportConfig,
    canonical_geoclaw_scenarios,
    export_geoclaw_scenario,
    normalize_geoclaw_fixed_grid_output,
)
from ..readiness import build_geoclaw_readiness_report, write_json_artifact
from ..tuning import CppTuningCandidate, tune_cpp_solver_against_geoclaw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("physics/data/readiness/milestone_14"))
    parser.add_argument("--scratch-dir", type=Path, default=Path("outputs/geoclaw_readiness"))
    parser.add_argument("--cpp-solver", type=Path, default=None)
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.scratch_dir.mkdir(parents=True, exist_ok=True)
    scenario = canonical_geoclaw_scenarios(seed=300)[1]
    config = GeoClawExportConfig(num_output_times=1)

    export = export_geoclaw_scenario(scenario, args.scratch_dir / "geoclaw_export" / scenario.metadata.scenario_id, config=config)
    normalized = normalize_geoclaw_fixed_grid_output(
        export.output_dir,
        args.scratch_dir / "geoclaw_reference" / scenario.metadata.scenario_id,
        config=config,
    )
    normalized_manifest = json.loads(normalized.manifest_path.read_text(encoding="utf-8"))
    geoclaw_summary = {
        "summary_version": "raftsim.geoclaw_reference_readiness.v1",
        "passed": normalized.frame_count > 0,
        "exports_passed": True,
        "export_count": 1,
        "scenario_id": scenario.metadata.scenario_id,
        "normalized_mode": normalized_manifest["run_status"]["mode"],
        "has_full_geoclaw_frames": normalized_manifest["run_status"]["mode"] == "fgout_npz",
        "normalized_frame_count": normalized.frame_count,
        "solver_outputs_committed": False,
    }
    write_json_artifact(args.output_dir / "geoclaw_reference_summary.json", geoclaw_summary)

    cpp_summary = _cpp_summary(args.cpp_solver, scenario, args.scratch_dir / "cpp_solver")
    write_json_artifact(args.output_dir / "cpp_solver_summary.json", cpp_summary)

    comparison_summary, tuning_summary, raft_summary = _comparison_summaries(
        args.cpp_solver,
        scenario,
        args.scratch_dir / "geoclaw_cpp",
    )
    write_json_artifact(args.output_dir / "geoclaw_cpp_comparison_summary.json", comparison_summary)
    write_json_artifact(args.output_dir / "geoclaw_cpp_tuning_summary.json", tuning_summary)
    write_json_artifact(args.output_dir / "geoclaw_raft_coupling_validation.json", raft_summary)

    report = build_geoclaw_readiness_report(
        geoclaw_reference_summary=geoclaw_summary,
        cpp_summary=cpp_summary,
        comparison_summary=comparison_summary,
        tuning_summary=tuning_summary,
        raft_coupling_summary=raft_summary,
        artifact_manifest={
            "geoclaw_reference_summary": "geoclaw_reference_summary.json",
            "cpp_solver_summary": "cpp_solver_summary.json",
            "geoclaw_cpp_comparison_summary": "geoclaw_cpp_comparison_summary.json",
            "geoclaw_cpp_tuning_summary": "geoclaw_cpp_tuning_summary.json",
            "geoclaw_raft_coupling_validation": "geoclaw_raft_coupling_validation.json",
        },
    )
    report.write_json(args.output_dir / "geoclaw_to_unreal_readiness_report.json")
    report.write_markdown(args.output_dir / "geoclaw_to_unreal_readiness_report.md")
    print(f"readiness_report={args.output_dir / 'geoclaw_to_unreal_readiness_report.json'}")
    print(f"decision={report.decision.status}")
    return 0


def _cpp_summary(cpp_solver: Path | None, scenario, output_dir: Path) -> dict[str, object]:
    if cpp_solver is None:
        return {"available": False, "passed": False, "reason": "--cpp-solver was not provided.", "run_count": 0, "runs": []}
    result = run_cpp_solver_scenario(
        scenario,
        output_dir=output_dir,
        config=CppSolverRunConfig(executable=cpp_solver, steps=1, frame_interval=1),
    )
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "passed": result.returncode == 0 and bool(validation.get("passed")),
        "run_count": 1,
        "runs": [
            {
                "scenario_id": scenario.metadata.scenario_id,
                "returncode": result.returncode,
                "passed": result.returncode == 0 and bool(validation.get("passed")),
                "mass_relative_drift": validation.get("mass_relative_drift"),
                "max_velocity": validation.get("max_velocity"),
                "min_depth": validation.get("min_depth"),
            }
        ],
    }


def _comparison_summaries(cpp_solver: Path | None, scenario, output_dir: Path):
    if cpp_solver is None:
        reason = "--cpp-solver was not provided."
        return (
            {"available": False, "passed": False, "reason": reason, "comparison_count": 0, "comparisons": []},
            {"available": False, "passed": False, "reason": reason, "candidate_count": 0, "best_candidate": None},
            {"available": False, "passed": False, "reason": reason, "comparison_count": 0, "comparisons": []},
        )
    report = tune_cpp_solver_against_geoclaw(
        scenario,
        output_dir=output_dir / "tuning",
        cpp_solver_executable=cpp_solver,
        candidates=(CppTuningCandidate("baseline"),),
        cpp_steps=1,
        cpp_frame_interval=1,
    )
    manifest_dir = report.best_candidate.dual_solver_dir
    thresholds = evaluate_dual_solver_thresholds(manifest_dir, output_path=manifest_dir / "threshold_evaluation.json")
    raft = compare_chrono_bridge_telemetry(manifest_dir, output_path=manifest_dir / "geoclaw_raft_coupling_validation.json")
    return (
        {
            "available": True,
            "passed": thresholds.passed,
            "comparison_count": 1,
            "comparisons": [
                {
                    "scenario_id": scenario.metadata.scenario_id,
                    "passed": thresholds.passed,
                    "checks": [check.to_json_dict() for check in thresholds.checks],
                }
            ],
        },
        {
            "available": True,
            "passed": report.best_candidate.passed,
            "candidate_count": len(report.candidates),
            "best_candidate": report.best_candidate.candidate.to_json_dict(),
        },
        {
            "available": True,
            "passed": raft.outcome_match,
            "comparison_count": 1,
            "comparisons": [raft.to_json_dict()],
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
