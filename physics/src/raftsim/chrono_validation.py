"""Validation reports for Chrono/custom-water bridge telemetry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .math3d import Vec3
from .raft_coupling2_5d import (
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    compare_raft_force_samples,
)
from .scenario2_5d import Scenario2_5D, read_scenario2_5d_package


@dataclass(frozen=True, slots=True)
class ChronoBridgeTelemetryComparisonReport:
    scenario_id: str
    force_delta: tuple[float, float, float]
    torque_delta: tuple[float, float, float]
    trajectory_position_delta: float
    trajectory_velocity_delta: float
    outcome_match: bool
    reference_outcome: str
    candidate_outcome: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "force_delta": list(self.force_delta),
            "torque_delta": list(self.torque_delta),
            "trajectory_position_delta": self.trajectory_position_delta,
            "trajectory_velocity_delta": self.trajectory_velocity_delta,
            "outcome_match": self.outcome_match,
            "reference_outcome": self.reference_outcome,
            "candidate_outcome": self.candidate_outcome,
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


def compare_chrono_bridge_telemetry(
    dual_solver_dir_or_manifest: str | Path,
    *,
    output_path: str | Path | None = None,
    state: RaftState6DoF | None = None,
) -> ChronoBridgeTelemetryComparisonReport:
    """Compare C++ custom-water bridge telemetry against PyClaw/Python reference output."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(root / manifest["scenario_package"])
    pyclaw_manifest = _load_manifest(root / manifest["pyclaw"]["manifest"])
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])
    pyclaw_output = root / manifest["pyclaw"]["output_dir"]
    cpp_output = root / manifest["cpp"]["output_dir"]
    pyclaw_water = WaterField2_5D.from_pyclaw_frame_npz(scenario, pyclaw_output / pyclaw_manifest["frames"][-1])
    cpp_water = WaterField2_5D.from_cpp_frame_csv(scenario, cpp_output / cpp_manifest["frames"][-1])
    comparison_state = state or _default_bridge_state(scenario, pyclaw_water)
    properties = build_default_raft_mass_properties(scenario.raft)
    comparison = compare_raft_force_samples(pyclaw_water, cpp_water, comparison_state, properties)
    report = ChronoBridgeTelemetryComparisonReport(
        scenario_id=manifest["scenario_id"],
        force_delta=comparison.force_delta.as_tuple(),
        torque_delta=comparison.torque_delta.as_tuple(),
        trajectory_position_delta=comparison.trajectory_position_delta,
        trajectory_velocity_delta=comparison.trajectory_velocity_delta,
        outcome_match=comparison.outcome_match,
        reference_outcome=comparison.reference.outcome,
        candidate_outcome=comparison.candidate.outcome,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def _default_bridge_state(scenario: Scenario2_5D, water: WaterField2_5D) -> RaftState6DoF:
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    return RaftState6DoF(position=Vec3(center_x, center_y, surface - 0.35), linear_velocity=Vec3(1.0, 0.0, -0.4))


def _manifest_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.name == "dual_solver_manifest.json":
        return candidate
    return candidate / "dual_solver_manifest.json"


def _load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
