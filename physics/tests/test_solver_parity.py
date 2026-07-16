import pytest

from raftsim.solver_parity import classify_solver_parity


def test_solver_parity_accepts_explicitly_uncalibrated_manifest():
    classification = classify_solver_parity({"disable_fixture_calibrations": True})

    assert classification.mode == "solver"
    assert classification.evidence == ("fixture_calibrations_disabled",)


def test_solver_parity_accepts_manifest_with_inactive_fixture_flags():
    classification = classify_solver_parity(
        {
            "disable_fixture_calibrations": False,
            "fixture_scoped_wet_dry_reconstruction": False,
            "scenario_geoclaw_profile_calibration": {"enabled": False},
        }
    )

    assert classification.mode == "solver"
    assert classification.evidence == ("no_active_fixture_scoped_behavior",)


def test_solver_parity_marks_fixture_behavior_and_profiles_as_playback():
    classification = classify_solver_parity(
        {
            "disable_fixture_calibrations": False,
            "fixture_scoped_scenario_geoclaw_profile_calibration": True,
            "scenario_geoclaw_profile_calibration": {"enabled": True},
        }
    )

    assert classification.mode == "reference_playback"
    assert classification.evidence == (
        "fixture_scoped_scenario_geoclaw_profile_calibration",
        "scenario_geoclaw_profile_calibration.enabled",
    )


def test_solver_parity_rejects_manifest_without_audit_flags():
    with pytest.raises(ValueError, match="does not expose fixture-scoped audit flags"):
        classify_solver_parity({"disable_fixture_calibrations": False})
