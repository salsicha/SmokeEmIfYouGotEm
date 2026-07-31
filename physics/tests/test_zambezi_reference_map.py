import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.named_rapid_registry import build_editor_markers
from raftsim.zambezi_reference_map import (
    CATALOG_RELATIVE,
    HEIGHT_IMAGE_SHA256,
    OUTPUT_RELATIVE,
    RAPID_MAP_SHA256,
    REFERENCE_HEIGHTFIELD_SIZE,
    REFERENCE_MESH_SIZE,
    SCENARIO_RELATIVE,
    build_rapid_map_digitization,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_supplied_reference_sources_and_digitized_rapid_order_are_locked():
    assert _sha256(REPO_ROOT / "zambezi_batoka_heightmap.png") == HEIGHT_IMAGE_SHA256
    assert _sha256(REPO_ROOT / "victoria-falls-rapids-map.pdf") == RAPID_MAP_SHA256
    digitization = build_rapid_map_digitization(REPO_ROOT)
    assert digitization["rapid_count"] == 25
    assert [rapid["rapid_number"] for rapid in digitization["rapids"]] == [
        str(number) for number in range(1, 26)
    ]
    assert digitization["rapids"][0]["pdf_label"] == "The Wall"
    assert digitization["rapids"][-1]["pdf_label"] == "Rapid 25"
    assert digitization["rapids"][0]["station_m"] == 0.0
    assert digitization["rapids"][-1]["station_m"] == 27358.848
    increments = np.diff([rapid["station_m"] for rapid in digitization["rapids"]])
    assert increments.min() > 0.0
    assert increments.max() / increments.min() > 4.0
    assert all(not rapid["production_authoritative"] for rapid in digitization["rapids"])


def test_committed_reference_bundle_is_self_consistent_and_not_physics_authority():
    root = REPO_ROOT / OUTPUT_RELATIVE
    manifest = _load(root / "source_and_conversion_manifest.json")
    assert manifest["production_promoted"] is False
    assert manifest["terrain_authority"]["policy"].startswith("Copernicus DEM remains")
    assert manifest["height_conversion"]["overlay_rejected_fraction"] > 0.1
    assert manifest["height_conversion"]["overlay_rejected_fraction"] < 0.4

    artifacts = manifest["artifacts"]
    for artifact in artifacts.values():
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]

    heightfield_path = REPO_ROOT / artifacts["heightfield_16bit"]["path"]
    with Image.open(heightfield_path) as heightfield:
        assert heightfield.size == REFERENCE_HEIGHTFIELD_SIZE
        values = np.asarray(heightfield)
    assert values.dtype in (np.dtype("uint16"), np.dtype("int32"))
    assert int(values.max()) - int(values.min()) > 50000

    mesh = artifacts["morphology_mesh"]
    assert mesh["grid_size"] == list(REFERENCE_MESH_SIZE)
    assert mesh["vertex_count"] == REFERENCE_MESH_SIZE[0] * REFERENCE_MESH_SIZE[1]
    assert mesh["triangle_count"] == (
        (REFERENCE_MESH_SIZE[0] - 1) * (REFERENCE_MESH_SIZE[1] - 1) * 2
    )
    assert mesh["physics_authority"] is False
    assert mesh["collision_authority"] is False


def test_zambezi_scenario_and_named_rapid_markers_use_pdf_relative_stationing():
    scenario = _load(REPO_ROOT / SCENARIO_RELATIVE)
    assert scenario["rapid_count"] == 25
    assert scenario["production_promoted"] is False
    assert scenario["rapids"][8]["mandatory_commercial_portage"] is True
    assert sum(rapid["mandatory_commercial_portage"] for rapid in scenario["rapids"]) == 1
    assert scenario["route_variants"][0]["start_rapid"] == "1"
    assert scenario["route_variants"][0]["end_rapid"] == "25"
    assert {source["source_id"] for source in scenario["route_evidence"]} == {
        "zambezi_whitewater_guidebook",
        "zambezi_shearwater_operator_guide",
        "zambezi_victoria_falls_guide",
    }
    assert scenario["route_variants"][1]["source_id"] == "zambezi_shearwater_operator_guide"
    assert scenario["route_variants"][2]["source_id"] == "zambezi_victoria_falls_guide"
    assert len(scenario["acceptance_gates"]) >= 5

    catalog = _load(REPO_ROOT / CATALOG_RELATIVE)
    generated = build_editor_markers(catalog, REPO_ROOT)
    zambezi = next(
        river for river in generated["rivers"] if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert len(zambezi["markers"]) == 25
    assert all(
        marker["stationing"]["station_kind"]
        == "stylized_map_relative_spacing_scaled_to_published_run_length"
        for marker in zambezi["markers"]
    )
    assert [marker["stationing"]["station_m"] for marker in zambezi["markers"]] == [
        rapid["station_m"] for rapid in scenario["rapids"]
    ]


def test_unreal_candidate_binds_the_zambezi_scenario_and_builds_editor_markers():
    internal = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    ).read_text(encoding="utf-8")
    catalog_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentCatalog.cpp"
    ).read_text(encoding="utf-8")
    build_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeBuild.cpp"
    ).read_text(encoding="utf-8")
    geometry_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeGeometry.cpp"
    ).read_text(encoding="utf-8")
    assert "ScenarioRelativePath" in internal
    assert SCENARIO_RELATIVE.as_posix() in catalog_cpp
    assert "AddLandscapeCandidateScenarioMarkers" in build_cpp
    assert "RaftSim_ZambeziRapid_" in geometry_cpp

    validation = _load(
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "zambezi_reference_scenario_map_validation.json"
    )
    assert validation["passed"] is True
    assert validation["scenario_marker_count"] == 25
    assert validation["rapid_numbers"] == list(range(1, 26))
    assert validation["mandatory_portage_actor"] == (
        "RaftSim_ZambeziRapid_9_Commercial_Suicide"
    )
