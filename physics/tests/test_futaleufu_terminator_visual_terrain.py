from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.futaleufu_terminator_visual_terrain import (
    SCHEMA,
    build_futaleufu_terminator_visual_terrain,
)
from raftsim.editor_source_layout import read_raftsim_editor_source


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_build_futaleufu_terminator_visual_terrain(tmp_path: Path) -> None:
    manifest = build_futaleufu_terminator_visual_terrain(
        REPO_ROOT, output_dir=tmp_path, output_size_px=257
    )

    assert manifest["schema"] == SCHEMA
    assert manifest["reference_flow_band"] == "median_runnable"
    assert manifest["landscape"]["horizontal_span_x_m"] == 600.0
    assert manifest["landscape"]["horizontal_span_y_m"] == 600.0
    assert manifest["landscape"]["source_solver_span_y_m"] == 84.0
    assert manifest["procedural_infill"]["protected_solver_strip_change_m"] == 0.0
    assert manifest["procedural_infill"][
        "maximum_corridor_dem_edge_correction_m"
    ] < 8.0
    assert manifest["procedural_infill"]["maximum_procedural_microrelief_m"] <= 1.5
    assert manifest["alignment"][
        "maximum_static_to_runtime_centerline_surface_error_m"
    ] < 1.0e-9
    assert manifest["honesty"]["production_promoted"] is False
    assert manifest["honesty"]["route_station_authority"].startswith(
        "order_distributed"
    )

    image = np.asarray(
        Image.open(tmp_path / "terminator_conditioned_heightfield_257.png")
    )
    assert image.shape == (257, 257)
    assert image.dtype == np.uint16
    assert int(image.min()) == 0
    assert int(image.max()) == 65535

    centerline = json.loads(
        (tmp_path / "terminator_local_centerline.json").read_text(encoding="utf-8")
    )
    assert len(centerline["points"]) == 301
    assert centerline["points"][0]["unreal_local_cm"] == [0.0, 30000.0]
    assert centerline["points"][-1]["unreal_local_cm"] == [60000.0, 30000.0]
    assert centerline["points"][0]["corridor_station_m"] == 5012.259
    assert centerline["points"][-1]["corridor_station_m"] == 5612.259

    coordinate_map = json.loads(
        (tmp_path / "terminator_runtime_coordinate_map.json").read_text(
            encoding="utf-8"
        )
    )
    assert coordinate_map["points"][0] == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert coordinate_map["points"][-1] == [600.0, 600.0, 0.0, 0.0, 1.0]
    assert 190.0 < coordinate_map["vertical_datum_m"] < 220.0


def test_unreal_binds_terminator_reach_local_landscape_and_runtime_water() -> None:
    source = read_raftsim_editor_source(REPO_ROOT)

    assert 'TEXT("/Game/RaftSim/Maps/L_Terminator")' in source
    assert "terminator_conditioned_heightfield_1009.png" in source
    assert "terminator_visual_terrain_manifest.json" in source
    assert "terminator_local_centerline.json" in source
    assert "terminator_runtime_coordinate_map.json" in source
    assert "futaleufu_terminator_median_depth_speed_froude_surface_v1.png" in source
    assert 'FlowBand = FName(TEXT("median_runnable"))' in source
    assert 'TEXT("RaftSim_FutaleufuTerminator_PlayerRaft")' in source
    assert 'TEXT("RaftSimFutaleufuTerminatorSolverVisualization")' in source
    assert 'TEXT("RaftSim_FutaleufuTerminator_D4_EntryMarkerBoulder")' in source


def test_shared_temperate_canopy_breaks_repeated_geometry_and_placement() -> None:
    foliage_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeFoliage.cpp"
    ).read_text(encoding="utf-8")
    map_test_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimTroublemakerMapTest.cpp"
    ).read_text(encoding="utf-8")

    assert "UMaterialExpressionPerInstanceRandom" in foliage_source
    assert "constexpr int32 SatelliteLobeCount = 3" in foliage_source
    assert "const int32 BranchCount = 6 + FMath::Clamp" in foliage_source
    assert "const bool bStormShortenedBranch" in foliage_source
    assert "const float ConiferCrownBodyScale" in foliage_source
    assert "constexpr float TreeHeightCm = 850.0f" in foliage_source
    assert "0.88f" in foliage_source
    assert "1.13f" in foliage_source
    assert "constexpr int32 TemperateSpeciesPermutation = 7" in foliage_source
    assert "TemperateBlockOffset" in foliage_source
    assert "ZambeziVegetationUnitRandom(ClusterIndex, 9161)" in foliage_source
    assert 'TEXT("RaftSimTemperateCanopyStructureV3")' in foliage_source
    assert 'TEXT("RaftSimTemperateCanopyStructureV3")' in map_test_source
