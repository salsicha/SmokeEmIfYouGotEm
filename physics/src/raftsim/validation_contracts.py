"""Milestone 17 data-contract validators."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema_versions import (
    GEOSPATIAL_FORMAT_CONTRACT_SCHEMA_VERSION,
    REACH_LOCAL_GRID_SCHEMA_VERSION,
    RIVER_VALIDATION_ANNOTATION_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class ContractIssue:
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class ContractValidation:
    contract_id: str
    passed: bool
    issues: tuple[ContractIssue, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "passed": self.passed,
            "issues": [{"path": issue.path, "message": issue.message} for issue in self.issues],
        }


def validate_reach_local_grid_contract(path_or_contract: str | Path | dict[str, object]) -> ContractValidation:
    contract = _load(path_or_contract)
    issues: list[ContractIssue] = []
    _require(contract.get("schema_version") == REACH_LOCAL_GRID_SCHEMA_VERSION, "$.schema_version", "unsupported reach-local grid schema", issues)
    grids = contract.get("reach_local_grids", [])
    _require(isinstance(grids, list) and bool(grids), "$.reach_local_grids", "at least one reach-local grid is required", issues)
    for index, grid in enumerate(grids if isinstance(grids, list) else []):
        if not isinstance(grid, dict):
            issues.append(ContractIssue(f"$.reach_local_grids[{index}]", "grid must be an object"))
            continue
        for key in ("grid_id", "reach_id", "station_range_m", "local_transform", "ghost_zones", "neighbor_refs"):
            _require(key in grid, f"$.reach_local_grids[{index}].{key}", "required reach-local grid field missing", issues)
        ghost = grid.get("ghost_zones", {})
        if isinstance(ghost, dict):
            for key in ("upstream_cells", "downstream_cells", "left_cells", "right_cells"):
                _require(int(ghost.get(key, 0)) > 0, f"$.reach_local_grids[{index}].ghost_zones.{key}", "ghost zones must be positive", issues)
    stitched = contract.get("stitched_validation_outputs", {})
    _require(isinstance(stitched, dict) and stitched.get("required") is True, "$.stitched_validation_outputs.required", "stitched whole-window validation outputs are mandatory", issues)
    for key in ("fields", "probes", "cross_sections", "conservation_summary", "raft_transition_checkpoints"):
        _require(bool(stitched.get(key)), f"$.stitched_validation_outputs.{key}", "stitched validation output is required", issues)
    seam = contract.get("seam_diagnostics", {})
    _require(isinstance(seam, dict) and seam.get("required") is True, "$.seam_diagnostics.required", "seam diagnostics are mandatory", issues)
    required_checks = {"mass", "momentum", "energy", "wet_dry", "bed_slope", "feature_location", "raft_state"}
    _require(required_checks.issubset(set(seam.get("checks", []))), "$.seam_diagnostics.checks", "seam diagnostics must cover conservation, geometry, features, and raft state", issues)
    return ContractValidation(str(contract.get("contract_id", "<unknown>")), not issues, tuple(issues))


def validate_river_validation_annotations(path_or_package: str | Path | dict[str, object]) -> ContractValidation:
    package = _load(path_or_package)
    issues: list[ContractIssue] = []
    _require(package.get("schema_version") == RIVER_VALIDATION_ANNOTATION_SCHEMA_VERSION, "$.schema_version", "unsupported annotation schema", issues)
    _require(package.get("type") == "FeatureCollection", "$.type", "annotations must be a GeoJSON FeatureCollection", issues)
    targets = set(package.get("export_targets", []))
    _require({"python_scenario_generation", "geoclaw_cpp_validation_reports", "unreal_data_assets"}.issubset(targets), "$.export_targets", "annotation exports must feed Python, validation reports, and Unreal", issues)
    features = package.get("features", [])
    _require(isinstance(features, list) and bool(features), "$.features", "at least one validation annotation is required", issues)
    for index, feature in enumerate(features if isinstance(features, list) else []):
        props = feature.get("properties", {}) if isinstance(feature, dict) else {}
        for key in ("annotation_id", "anchor_type", "station_m", "evidence", "expected_outcome", "rights_provenance"):
            _require(key in props, f"$.features[{index}].properties.{key}", "annotation property is required", issues)
        evidence = props.get("evidence", {}) if isinstance(props, dict) else {}
        for key in ("footage", "gauge_history", "aerial_imagery", "guide_feedback"):
            _require(bool(evidence.get(key)), f"$.features[{index}].properties.evidence.{key}", "validation evidence category is required", issues)
        expected = props.get("expected_outcome", {}) if isinstance(props, dict) else {}
        for key in ("feature_behavior", "raft_outcome_class", "confidence"):
            _require(key in expected, f"$.features[{index}].properties.expected_outcome.{key}", "expected outcome field is required", issues)
    return ContractValidation(str(package.get("package_id", "<unknown>")), not issues, tuple(issues))


def validate_geospatial_format_contract(path_or_contract: str | Path | dict[str, object]) -> ContractValidation:
    contract = _load(path_or_contract)
    issues: list[ContractIssue] = []
    _require(contract.get("schema_version") == GEOSPATIAL_FORMAT_CONTRACT_SCHEMA_VERSION, "$.schema_version", "unsupported geospatial contract schema", issues)
    _require(contract.get("source_manifest_required") is True, "$.source_manifest_required", "source manifests are mandatory", issues)
    _require(contract.get("shapefile_canonical_allowed") is False, "$.shapefile_canonical_allowed", "Shapefile cannot be canonical", issues)
    transform = contract.get("transform_policy", {})
    for key in ("wgs84_required", "local_solver_transform_required", "transform_changes_tracked"):
        _require(isinstance(transform, dict) and transform.get(key) is True, f"$.transform_policy.{key}", "transform policy field is required", issues)
    categories = {item.get("category"): set(item.get("formats", [])) for item in contract.get("canonical_formats", []) if isinstance(item, dict)}
    required = {
        "source_manifests": {"JSON"},
        "vectors_annotations": {"GeoJSON", "GeoPackage"},
        "rasters": {"GeoTIFF", "COG"},
        "point_clouds": {"LAS", "LAZ", "COPC"},
        "gauge_history": {"JSON", "CSV", "Parquet"},
        "solver_packages": {"JSON", "NPY", "NPZ"},
        "unreal_corridor_exports": {"JSON", "GeoJSON", "converted_engine_assets"},
    }
    for category, formats in required.items():
        _require(category in categories and formats.issubset(categories[category]), f"$.canonical_formats.{category}", "canonical format category is incomplete", issues)
    _require(all("Shapefile" not in formats for formats in categories.values()), "$.canonical_formats", "Shapefile may not appear as a canonical format", issues)
    return ContractValidation(str(contract.get("contract_id", "<unknown>")), not issues, tuple(issues))


def _load(path_or_data: str | Path | dict[str, object]) -> dict[str, object]:
    if isinstance(path_or_data, (str, Path)):
        return json.loads(Path(path_or_data).read_text(encoding="utf-8"))
    return path_or_data


def _require(condition: bool, path: str, message: str, issues: list[ContractIssue]) -> None:
    if not condition:
        issues.append(ContractIssue(path, message))
