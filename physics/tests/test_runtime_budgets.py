import json
from pathlib import Path


def test_runtime_budget_profiles_are_complete_and_positive():
    budget_path = Path(__file__).resolve().parents[1] / "config" / "runtime_budgets.json"
    payload = json.loads(budget_path.read_text(encoding="utf-8"))
    profiles = payload["profiles"]

    assert payload["schema_version"] == "raftsim.runtime_budgets.v0"
    assert set(profiles) == {"desktop", "vr", "handheld"}
    for profile in profiles.values():
        assert profile["render_target_hz"] > 0
        assert profile["physics_tick_hz"] > 0
        assert profile["total_physics_ms"] > 0.0
        assert profile["water_solver_ms"] > 0.0
        assert profile["raft_coupling_ms"] > 0.0
        assert profile["probe_telemetry_ms"] > 0.0
        assert profile["max_runtime_multiplier"] >= 1.0
        assert profile["water_solver_ms"] + profile["raft_coupling_ms"] <= profile["total_physics_ms"]
