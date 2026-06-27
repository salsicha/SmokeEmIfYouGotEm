import json
from pathlib import Path


def test_custom_cpp_water_solver_is_primary_unreal_runtime_candidate():
    baseline_path = Path(__file__).resolve().parents[1] / "config" / "runtime_baseline.json"
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    primary = payload["primary_unreal_water_runtime"]

    assert payload["schema_version"] == "raftsim.runtime_baseline.v0"
    assert primary["solver_id"] == "raftsim_water_reduced_cpp_v0"
    assert primary["executable"] == "raftsim_water_solver"
    assert primary["source"] == "physics/cpp"
    assert primary["validation_reference"] == "PyClaw"
    assert payload["chrono_role"]["fsi_policy"] == "optional_experiment_reference_only"
