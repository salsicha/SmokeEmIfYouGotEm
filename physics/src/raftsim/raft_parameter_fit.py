"""Fit C++ solver and raft force parameters together against PyClaw water."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from raftsim.comparison import ScenarioThresholds, evaluate_dual_solver_thresholds
from raftsim.dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_dual_solver_scenario
from raftsim.math3d import Vec3
from raftsim.pyclaw_reference import PyClawRunConfig
from raftsim.raft_coupling2_5d import RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties, sample_buoyancy_forces, sample_grounding_forces, sample_hydrodynamic_forces, sum_force_contributions
from raftsim.scenario2_5d import Scenario2_5D
from raftsim.sweeps import ParameterSweepCandidate
from raftsim.tuning import (_last_manifest_file, _relative_or_absolute, _score_threshold_report)


@dataclass(frozen=True, slots=True)
class ParameterFitCandidateResult:
    candidate: ParameterSweepCandidate
    score: float
    water_score: float
    raft_force_score: float
    passed: bool
    dual_solver_dir: Path
    threshold_report: Path

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "candidate": self.candidate.to_json_dict(),
            "score": self.score,
            "water_score": self.water_score,
            "raft_force_score": self.raft_force_score,
            "passed": self.passed,
            "dual_solver_dir": _relative_or_absolute(self.dual_solver_dir, root),
            "threshold_report": _relative_or_absolute(self.threshold_report, root),
        }


@dataclass(frozen=True, slots=True)
class ParameterFitReport:
    scenario_id: str
    best_candidate: ParameterFitCandidateResult
    candidates: tuple[ParameterFitCandidateResult, ...]

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


def fit_cpp_and_raft_parameters_against_pyclaw(
    scenario: Scenario2_5D,
    *,
    output_dir: str | Path,
    cpp_solver_executable: str | Path,
    candidates: tuple[ParameterSweepCandidate, ...],
    pyclaw_config: PyClawRunConfig | None = None,
    thresholds: ScenarioThresholds | None = None,
    cpp_steps: int | None = None,
    cpp_frame_interval: int | None = None,
    raft_state: RaftState6DoF | None = None,
) -> ParameterFitReport:
    """Fit C++ water and raft-force parameters against PyClaw reference output."""

    if not candidates:
        raise ValueError("At least one fit candidate is required.")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    results: list[ParameterFitCandidateResult] = []
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
        water_score = _score_threshold_report(threshold_report)
        raft_force_score = _score_raft_force_fit(scenario, run_result.output_dir, candidate, raft_state)
        score = water_score + raft_force_score
        results.append(
            ParameterFitCandidateResult(
                candidate=candidate,
                score=score,
                water_score=water_score,
                raft_force_score=raft_force_score,
                passed=threshold_report.passed,
                dual_solver_dir=run_result.output_dir,
                threshold_report=threshold_path,
            )
        )
    best = min(results, key=lambda result: result.score)
    report = ParameterFitReport(
        scenario_id=scenario.metadata.scenario_id,
        best_candidate=best,
        candidates=tuple(results),
    )
    report.write_json(root / "parameter_fit_report.json")
    return report


def _score_raft_force_fit(
    scenario: Scenario2_5D,
    dual_solver_dir: Path,
    candidate: ParameterSweepCandidate,
    raft_state: RaftState6DoF | None,
) -> float:
    pyclaw_frame = _last_manifest_file(dual_solver_dir / "pyclaw_reference" / scenario.metadata.scenario_id / "manifest.json", "frames")
    cpp_frame = _last_manifest_file(dual_solver_dir / "cpp_solver" / scenario.metadata.scenario_id / "manifest.json", "frames")
    pyclaw_water = WaterField2_5D.from_pyclaw_frame_npz(
        scenario,
        dual_solver_dir / "pyclaw_reference" / scenario.metadata.scenario_id / pyclaw_frame,
    )
    cpp_water = WaterField2_5D.from_cpp_frame_csv(
        scenario,
        dual_solver_dir / "cpp_solver" / scenario.metadata.scenario_id / cpp_frame,
    )
    state = raft_state or _default_fit_state(scenario, pyclaw_water)
    properties = build_default_raft_mass_properties(scenario.raft)
    pyclaw_force, pyclaw_torque = _candidate_force(state, properties, pyclaw_water, candidate)
    cpp_force, cpp_torque = _candidate_force(state, properties, cpp_water, candidate)
    force_delta = (cpp_force - pyclaw_force).magnitude
    torque_delta = (cpp_torque - pyclaw_torque).magnitude
    weight = max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    inertia_scale = max(properties.inertia_diagonal_kg_m2.magnitude, 1.0)
    return force_delta / weight + torque_delta / inertia_scale


def _candidate_force(
    state: RaftState6DoF,
    properties,
    water: WaterField2_5D,
    candidate: ParameterSweepCandidate,
):
    contributions = (
        *sample_buoyancy_forces(
            state,
            properties,
            water,
            water_density_kg_m3=1000.0 * candidate.buoyancy_density_scale,
        ),
        *sample_hydrodynamic_forces(
            state,
            properties,
            water,
            horizontal_drag_coefficient=1.25 * candidate.raft_drag_scale,
        ),
        *sample_grounding_forces(
            state,
            properties,
            water,
            contact_stiffness=12000.0 * candidate.contact_stiffness_scale,
            contact_damping=1200.0 * candidate.contact_damping_scale,
            grounding_friction=0.65 * candidate.grounding_friction_scale,
        ),
    )
    return sum_force_contributions(contributions)


def _default_fit_state(scenario: Scenario2_5D, water: WaterField2_5D) -> RaftState6DoF:
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    return RaftState6DoF(
        position=Vec3(center_x, center_y, surface - 0.35),
        linear_velocity=Vec3(1.0, 0.0, -0.4),
    )
