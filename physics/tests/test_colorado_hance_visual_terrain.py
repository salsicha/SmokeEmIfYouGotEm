from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.colorado_hance_visual_terrain import (
    DEFAULT_OUTPUT_RELATIVE,
    SCHEMA,
    build_colorado_hance_visual_terrain,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_hance_visual_terrain_preserves_solver_strip_and_aligns_runtime(tmp_path: Path):
    output_dir = tmp_path / "hance_visual"
    manifest = build_colorado_hance_visual_terrain(
        REPO_ROOT, output_dir=output_dir, output_size_px=257
    )

    assert manifest["schema"] == SCHEMA
    assert manifest["landscape"]["horizontal_span_x_m"] == 600.0
    assert manifest["landscape"]["horizontal_span_y_m"] == 320.0
    assert manifest["landscape"]["source_solver_span_y_m"] == 78.0
    assert manifest["procedural_infill"]["protected_solver_strip_change_m"] == 0.0
    assert manifest["procedural_infill"]["maximum_source_join_step_m"] < 0.25
    assert manifest["procedural_infill"]["maximum_added_canyon_relief_m"] > 55.0
    assert manifest["procedural_infill"]["algorithm"] == (
        "deterministic_nonperiodic_debris_fan_desert_canyon_v3"
    )
    assert manifest["procedural_infill"]["maximum_outer_cross_bank_grade"] == 1.18
    assert 8.0 < manifest["procedural_infill"][
        "maximum_modeled_debris_fan_analog_relief_m"
    ] < 9.0
    assert 4.5 < manifest["procedural_infill"][
        "maximum_opposing_bedrock_buttress_relief_m"
    ] < 5.2
    assert (
        manifest["procedural_infill"][
            "maximum_outer_adjacent_cross_bank_step_m"
        ]
        < 1.25 * manifest["landscape"]["sample_spacing_y_m"]
    )
    assert (
        manifest["procedural_infill"][
            "maximum_outer_mean_profile_dominant_band_energy_ratio"
        ]
        < 0.40
    )
    assert "seeded non-periodic" in manifest["procedural_infill"][
        "regular_terrace_reduction_policy"
    ]
    official_references = manifest["procedural_infill"][
        "official_reference_contract"
    ]
    assert official_references["usgs_hance_geomorphology"] == (
        "https://pubs.usgs.gov/pp/1492/report.pdf"
    )
    assert official_references["usgs_debris_fan_process"] == (
        "https://pubs.usgs.gov/fs/FS-019-01/"
    )
    assert official_references["nps_geologic_formations"] == (
        "https://www.nps.gov/grca/learn/nature/geologicformations.htm"
    )
    assert official_references["nps_river_corridor_ecology"] == (
        "https://www.nps.gov/grca/learn/nature/"
        "naturalfeaturesandecosystems.htm"
    )
    assert "no downloaded geometry" in official_references[
        "interpretation_boundary"
    ]
    assert (
        manifest["alignment"]["maximum_static_to_runtime_centerline_surface_error_m"]
        < 1e-9
    )
    assert manifest["honesty"]["production_promoted"] is False

    heightfield = np.asarray(
        Image.open(output_dir / "hance_conditioned_heightfield_257.png")
    )
    centerline = json.loads(
        (output_dir / "hance_local_centerline.json").read_text(encoding="utf-8")
    )
    coordinate_map = json.loads(
        (output_dir / "hance_runtime_coordinate_map.json").read_text(encoding="utf-8")
    )
    assert heightfield.shape == (257, 257)
    assert heightfield.min() == 0
    assert heightfield.max() == 65535
    assert len(centerline["points"]) == 301
    assert centerline["points"][0]["unreal_local_cm"] == [0.0, 16000.0]
    assert centerline["points"][-1]["unreal_local_cm"] == [60000.0, 16000.0]
    assert coordinate_map["points"][0] == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert coordinate_map["points"][-1] == [600.0, 600.0, 0.0, 0.0, 1.0]


def test_committed_hance_visual_terrain_matches_generator(tmp_path: Path):
    generated_dir = tmp_path / "generated"
    build_colorado_hance_visual_terrain(REPO_ROOT, output_dir=generated_dir)
    committed_dir = REPO_ROOT / DEFAULT_OUTPUT_RELATIVE
    for name in (
        "hance_conditioned_heightfield_1009.png",
        "hance_local_centerline.json",
        "hance_runtime_coordinate_map.json",
    ):
        assert (committed_dir / name).read_bytes() == (
            generated_dir / name
        ).read_bytes()

    committed = json.loads(
        (committed_dir / "hance_visual_terrain_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    generated = json.loads(
        (generated_dir / "hance_visual_terrain_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    for manifest in (committed, generated):
        for key in ("heightfield", "local_centerline", "runtime_coordinate_map"):
            manifest["outputs"][key] = Path(manifest["outputs"][key]).name
    assert committed == generated
