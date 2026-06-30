import copy
from pathlib import Path

from raftsim.validation_contracts import (
    validate_geospatial_format_contract,
    validate_reach_local_grid_contract,
    validate_river_validation_annotations,
)


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_reach_local_grid_contract_requires_stitched_outputs_and_seam_diagnostics():
    path = CONFIG_ROOT / "reach_local_grid_contract.json"
    validation = validate_reach_local_grid_contract(path)

    assert validation.passed is True

    broken = _load_json(path)
    broken["stitched_validation_outputs"]["required"] = False
    broken["seam_diagnostics"]["checks"] = ["mass"]
    failed = validate_reach_local_grid_contract(broken)
    messages = " ".join(issue.message for issue in failed.issues)

    assert failed.passed is False
    assert "stitched whole-window validation outputs are mandatory" in messages
    assert "seam diagnostics must cover conservation" in messages


def test_river_validation_annotations_require_evidence_and_export_targets():
    path = CONFIG_ROOT / "river_validation_annotations.example.geojson"
    validation = validate_river_validation_annotations(path)

    assert validation.passed is True

    broken = _load_json(path)
    broken["export_targets"] = ["unreal_data_assets"]
    del broken["features"][0]["properties"]["evidence"]["guide_feedback"]
    failed = validate_river_validation_annotations(broken)
    messages = " ".join(issue.message for issue in failed.issues)

    assert failed.passed is False
    assert "annotation exports must feed Python" in messages
    assert "validation evidence category is required" in messages


def test_geospatial_format_contract_rejects_missing_crs_and_shapefile_canonical():
    path = CONFIG_ROOT / "geospatial_format_contract.json"
    validation = validate_geospatial_format_contract(path)

    assert validation.passed is True

    broken = copy.deepcopy(_load_json(path))
    broken["source_manifest_required"] = False
    broken["canonical_formats"][1]["formats"].append("Shapefile")
    failed = validate_geospatial_format_contract(broken)
    messages = " ".join(issue.message for issue in failed.issues)

    assert failed.passed is False
    assert "source manifests are mandatory" in messages
    assert "Shapefile may not appear as a canonical format" in messages


def _load_json(path: Path) -> dict[str, object]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
