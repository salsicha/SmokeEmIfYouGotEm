"""Promotion helpers for accepted 2.5D regression scenarios."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RegressionPromotionResult:
    scenario_id: str
    fixture_dir: Path
    registry_path: Path
    threshold_report: Path

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "fixture_dir": str(self.fixture_dir),
            "registry_path": str(self.registry_path),
            "threshold_report": str(self.threshold_report),
        }


def promote_passing_dual_solver_run(
    dual_solver_dir: str | Path,
    *,
    regression_root: str | Path = "regression_fixtures",
    registry_path: str | Path | None = None,
) -> RegressionPromotionResult:
    """Promote a passing dual-solver run's shared scenario package to regressions."""

    run_dir = Path(dual_solver_dir)
    manifest_path = run_dir / "dual_solver_manifest.json"
    threshold_path = run_dir / "threshold_evaluation.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing dual-solver manifest: {manifest_path}")
    if not threshold_path.exists():
        raise FileNotFoundError(f"Missing threshold evaluation: {threshold_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    threshold = json.loads(threshold_path.read_text(encoding="utf-8"))
    if not threshold.get("passed", False):
        raise ValueError(f"Refusing to promote failed scenario: {manifest['scenario_id']}")

    root = Path(regression_root)
    registry = Path(registry_path) if registry_path is not None else root / "registry.json"
    scenario_id = str(manifest["scenario_id"])
    fixture_dir = root / scenario_id
    scenario_source = run_dir / manifest["scenario_package"]
    scenario_target = fixture_dir / "scenario"
    reports_target = fixture_dir / "reports"

    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    shutil.copytree(scenario_source, scenario_target)
    reports_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, reports_target / "dual_solver_manifest.json")
    shutil.copy2(threshold_path, reports_target / "threshold_evaluation.json")

    entry = {
        "scenario_id": scenario_id,
        "fixture_dir": str(fixture_dir),
        "scenario": str(scenario_target / "scenario.json"),
        "threshold_report": str(reports_target / "threshold_evaluation.json"),
    }
    registry_data = _read_registry(registry)
    registry_data["fixtures"] = [
        existing for existing in registry_data.get("fixtures", []) if existing.get("scenario_id") != scenario_id
    ]
    registry_data["fixtures"].append(entry)
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(registry_data, indent=2, sort_keys=True), encoding="utf-8")

    return RegressionPromotionResult(
        scenario_id=scenario_id,
        fixture_dir=fixture_dir,
        registry_path=registry,
        threshold_report=reports_target / "threshold_evaluation.json",
    )


def _read_registry(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"fixtures": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("fixtures"), list):
        data["fixtures"] = []
    return data
