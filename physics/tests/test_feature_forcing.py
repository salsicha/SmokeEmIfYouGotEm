import copy
from pathlib import Path

from raftsim.feature_forcing import (
    FEATURE_FORCING_KINDS,
    load_feature_forcing_manifest,
    validate_feature_forcing_manifest,
)


def test_feature_forcing_defaults_are_low_bounded_and_flow_dependent():
    manifest = load_feature_forcing_manifest(_manifest_path())
    validation = validate_feature_forcing_manifest(manifest)

    assert validation.passed is True
    assert tuple(family["kind"] for family in manifest["feature_families"]) == FEATURE_FORCING_KINDS
    assert manifest["defaults"]["enabled_by_default"] is False
    assert manifest["defaults"]["max_default_gain"] <= 0.15
    assert all(family["default_gain"] <= manifest["defaults"]["max_default_gain"] for family in manifest["feature_families"])
    assert all(family["conservation_limits"]["hides_conservation_failures"] is False for family in manifest["feature_families"])


def test_feature_forcing_validator_rejects_unbounded_or_uncompared_forcing():
    manifest = load_feature_forcing_manifest(_manifest_path())
    broken = copy.deepcopy(manifest)
    broken["feature_families"][0]["default_gain"] = 0.9
    broken["feature_families"][0]["validation_evidence"]["geoclaw_comparison_required"] = False
    broken["feature_families"][0]["conservation_limits"]["hides_conservation_failures"] = True

    validation = validate_feature_forcing_manifest(broken)
    messages = " ".join(issue.message for issue in validation.issues)

    assert validation.passed is False
    assert "default gain exceeds low-default policy" in messages
    assert "must require GeoClaw comparison" in messages
    assert "may not hide conservation failures" in messages


def _manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "feature_forcing_defaults.json"
