"""Parameter tuning harness for the C++ reduced water solver."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .comparison import ScenarioThresholds, ThresholdEvaluationReport, evaluate_dual_solver_thresholds
from .dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_dual_solver_scenario
from .pyclaw_reference import PyClawRunConfig
from .scenario2_5d import Scenario2_5D


@dataclass(frozen=True, slots=True)
class CppTuningCandidate:
    label: str
    feature_strength_scale: float = 1.0
    roughness_scale: float = 1.0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "feature_strength_scale": self.feature_strength_scale,
            "roughness_scale": self.roughness_scale,
        }


@dataclass(frozen=True, slots=True)
class CppTuningCandidateResult:
    candidate: CppTuningCandidate
    score: float
    passed: bool
    dual_solver_dir: Path
    threshold_report: Path

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "candidate": self.candidate.to_json_dict(),
            "score": self.score,
            "passed": self.passed,
            "dual_solver_dir": _relative_or_absolute(self.dual_solver_dir, root),
            "threshold_report": _relative_or_absolute(self.threshold_report, root),
        }


@dataclass(frozen=True, slots=True)
class CppTuningReport:
    scenario_id: str
    best_candidate: CppTuningCandidateResult
    candidates: tuple[CppTuningCandidateResult, ...]

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "best_candidate": self.best_candidate.to_json_dict(root),
            "candidates": [candidate.to_json_dict(root) for candidate in self.candidates],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(output_path.parent), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


def tune_cpp_solver_against_pyclaw(
    scenario: Scenario2_5D,
    *,
    output_dir: str | Path,
    cpp_solver_executable: str | Path,
    candidates: tuple[CppTuningCandidate, ...],
    pyclaw_config: PyClawRunConfig | None = None,
    thresholds: ScenarioThresholds | None = None,
    cpp_steps: int | None = None,
    cpp_frame_interval: int | None = None,
) -> CppTuningReport:
    """Run C++ parameter candidates against PyClaw and select the lowest score."""

    if not candidates:
        raise ValueError("At least one tuning candidate is required.")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    results: list[CppTuningCandidateResult] = []
    for candidate in candidates:
        candidate_dir = root / candidate.label
        run_result = run_dual_solver_scenario(
            scenario,
            output_dir=candidate_dir,
            config=DualSolverRunConfig(
                pyclaw=pyclaw_config or PyClawRunConfig(num_output_times=2),
                cpp=CppSolverRunConfig(
                    executable=Path(cpp_solver_executable),
                    steps=cpp_steps,
                    frame_interval=cpp_frame_interval,
                    feature_strength_scale=candidate.feature_strength_scale,
                    roughness_scale=candidate.roughness_scale,
                ),
            ),
        )
        threshold_path = candidate_dir / "threshold_evaluation.json"
        threshold_report = evaluate_dual_solver_thresholds(
            run_result.output_dir,
            thresholds=thresholds,
            output_path=threshold_path,
        )
        results.append(
            CppTuningCandidateResult(
                candidate=candidate,
                score=_score_threshold_report(threshold_report),
                passed=threshold_report.passed,
                dual_solver_dir=run_result.output_dir,
                threshold_report=threshold_path,
            )
        )
    best = min(results, key=lambda result: result.score)
    report = CppTuningReport(
        scenario_id=scenario.metadata.scenario_id,
        best_candidate=best,
        candidates=tuple(results),
    )
    report.write_json(root / "tuning_report.json")
    return report


def _score_threshold_report(report: ThresholdEvaluationReport) -> float:
    score = 0.0
    for check in report.checks:
        normalized = check.value / max(check.threshold, 1.0e-12)
        score += normalized
        if not check.passed:
            score += 10.0 + normalized
    return score


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
