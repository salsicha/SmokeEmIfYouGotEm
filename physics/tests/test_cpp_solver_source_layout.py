import json
from pathlib import Path


PHYSICS_ROOT = Path(__file__).resolve().parents[1]
SOLVER_SOURCE_ROOT = PHYSICS_ROOT / "cpp" / "src"
COLUMN_PROFILE_PATH = (
    PHYSICS_ROOT / "data" / "calibration" / "milestone18_column_geoclaw_profiles.json"
)


def test_column_reference_playback_profiles_are_externalized():
    solver_source = (SOLVER_SOURCE_ROOT / "solver.cpp").read_text(encoding="utf-8")
    profile = json.loads(COLUMN_PROFILE_PATH.read_text(encoding="utf-8"))

    assert profile["schema_version"] == "raftsim.milestone18.column_geoclaw_profiles.v1"
    assert profile["provenance"]["authority"] == "calibration_only_not_solver_parity"
    assert "milestone18_column_geoclaw_profiles.json" in solver_source
    assert "constexpr std::array" not in solver_source

    for profile_id in ("dam_break", "bed_step_reduced"):
        fields = profile["profiles"][profile_id]
        assert set(fields) == {"depth_t3", "velocity_t3", "depth_t6", "velocity_t6"}
        assert {len(values) for values in fields.values()} == {24}

