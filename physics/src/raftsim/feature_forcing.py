"""Feature-forcing manifest validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema_versions import FEATURE_FORCING_SCHEMA_VERSION

FEATURE_FORCING_KINDS = (
    "hole",
    "boil",
    "lateral",
    "eddy_line",
    "wave_train",
    "shallow_shelf",
    "boulder_push_damping",
    "pin_release",
    "flip",
)
MAX_LOW_DEFAULT_GAIN = 0.15


@dataclass(frozen=True, slots=True)
class FeatureForcingIssue:
    path: str
    message: str

    def to_json_dict(self) -> dict[str, object]:
        return {"path": self.path, "message": self.message}


@dataclass(frozen=True, slots=True)
class FeatureForcingValidation:
    manifest_id: str
    passed: bool
    issues: tuple[FeatureForcingIssue, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "manifest_id": self.manifest_id,
            "passed": self.passed,
            "issues": [issue.to_json_dict() for issue in self.issues],
        }


def load_feature_forcing_manifest(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_feature_forcing_manifest(path_or_manifest: str | Path | dict[str, object]) -> FeatureForcingValidation:
    manifest = load_feature_forcing_manifest(path_or_manifest) if isinstance(path_or_manifest, (str, Path)) else path_or_manifest
    issues: list[FeatureForcingIssue] = []
    manifest_id = str(manifest.get("manifest_id", "<unknown>"))

    _require(manifest.get("schema_version") == FEATURE_FORCING_SCHEMA_VERSION, "$.schema_version", "unsupported feature-forcing schema", issues)
    defaults = _object(manifest.get("defaults"), "$.defaults", issues)
    max_default_gain = float(defaults.get("max_default_gain", MAX_LOW_DEFAULT_GAIN))
    _require(max_default_gain <= MAX_LOW_DEFAULT_GAIN, "$.defaults.max_default_gain", "default feature forcing must stay turned down", issues)
    _require(defaults.get("enabled_by_default") is False, "$.defaults.enabled_by_default", "feature forcing must be disabled by default", issues)
    _require(defaults.get("tuning_surface_exposed") is True, "$.defaults.tuning_surface_exposed", "parameters must be exposed for tuning", issues)
    _require(
        defaults.get("physics_gameplay_visual_separated") is True,
        "$.defaults.physics_gameplay_visual_separated",
        "physics, raft/gameplay, and visual-only controls must be separated",
        issues,
    )

    requirements = _object(manifest.get("validation_requirements"), "$.validation_requirements", issues)
    for key in ("bounded", "manifest_recorded", "geoclaw_compared", "flow_dependent"):
        _require(requirements.get(key) is True, f"$.validation_requirements.{key}", f"{key} is required", issues)
    _require(
        requirements.get("hide_conservation_failures") is False,
        "$.validation_requirements.hide_conservation_failures",
        "forcing must not hide conservation failures",
        issues,
    )

    curves = manifest.get("flow_response_curves", [])
    if not isinstance(curves, list):
        curves = []
        issues.append(FeatureForcingIssue("$.flow_response_curves", "flow response curves must be a list"))
    curve_ids = {str(curve.get("curve_id")) for curve in curves if isinstance(curve, dict)}
    for index, curve in enumerate(curves):
        if not isinstance(curve, dict):
            continue
        points = curve.get("points", [])
        _require(isinstance(points, list) and len(points) >= 3, f"$.flow_response_curves[{index}].points", "flow response needs at least three points", issues)
        multipliers = [float(point.get("gain_multiplier", -1.0)) for point in points if isinstance(point, dict)]
        _require(all(value >= 0.0 for value in multipliers), f"$.flow_response_curves[{index}].points", "gain multipliers must be non-negative", issues)

    families = manifest.get("feature_families", [])
    if not isinstance(families, list):
        families = []
        issues.append(FeatureForcingIssue("$.feature_families", "feature families must be a list"))
    family_kinds = tuple(str(family.get("kind")) for family in families if isinstance(family, dict))
    _require(set(family_kinds) == set(FEATURE_FORCING_KINDS), "$.feature_families", "feature families must exactly cover the accepted forcing surface", issues)
    _require(len(family_kinds) == len(set(family_kinds)), "$.feature_families", "feature family kinds must be unique", issues)

    for index, family in enumerate(families):
        if not isinstance(family, dict):
            continue
        path = f"$.feature_families[{index}]"
        kind = str(family.get("kind", "<unknown>"))
        _require(family.get("enabled_by_default") is False, f"{path}.enabled_by_default", f"{kind} must be disabled by default", issues)
        default_gain = float(family.get("default_gain", 999.0))
        _require(default_gain <= max_default_gain, f"{path}.default_gain", f"{kind} default gain exceeds low-default policy", issues)
        bounds = _object(family.get("gain_bounds"), f"{path}.gain_bounds", issues)
        _require(float(bounds.get("min", 1.0)) <= default_gain <= float(bounds.get("max", -1.0)), f"{path}.gain_bounds", f"{kind} default gain must sit inside gain bounds", issues)
        _require(str(family.get("flow_response_curve_id")) in curve_ids, f"{path}.flow_response_curve_id", f"{kind} references a missing flow curve", issues)
        _require(bool(family.get("solver_state_effects")), f"{path}.solver_state_effects", f"{kind} must record solver-state effects", issues)
        _require(bool(family.get("raft_coupling_effects")), f"{path}.raft_coupling_effects", f"{kind} must record raft-coupling effects", issues)
        _require(isinstance(family.get("visual_only_parameters"), dict), f"{path}.visual_only_parameters", f"{kind} must record visual-only parameters separately", issues)
        limits = _object(family.get("conservation_limits"), f"{path}.conservation_limits", issues)
        _require(limits.get("hides_conservation_failures") is False, f"{path}.conservation_limits.hides_conservation_failures", f"{kind} may not hide conservation failures", issues)
        for key in ("mass_relative_delta", "momentum_relative_delta", "energy_relative_delta", "wet_dry_mismatch_fraction", "reach_handoff_delta"):
            _require(float(limits.get(key, 999.0)) >= 0.0, f"{path}.conservation_limits.{key}", f"{kind} conservation limit must be non-negative", issues)
        evidence = _object(family.get("validation_evidence"), f"{path}.validation_evidence", issues)
        _require(evidence.get("manifest_record_required") is True, f"{path}.validation_evidence.manifest_record_required", f"{kind} must be manifest-recorded", issues)
        _require(evidence.get("geoclaw_comparison_required") is True, f"{path}.validation_evidence.geoclaw_comparison_required", f"{kind} must require GeoClaw comparison", issues)

    return FeatureForcingValidation(manifest_id=manifest_id, passed=not issues, issues=tuple(issues))


def _object(value: object, path: str, issues: list[FeatureForcingIssue]) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    issues.append(FeatureForcingIssue(path, "expected object"))
    return {}


def _require(condition: bool, path: str, message: str, issues: list[FeatureForcingIssue]) -> None:
    if not condition:
        issues.append(FeatureForcingIssue(path, message))
