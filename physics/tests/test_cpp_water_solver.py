import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from raftsim.cascading import (
    CaliforniaPoolDropParameters2_5D,
    generate_california_pool_drop_cascading_scenario2_5d,
)
from raftsim.scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)


def test_cpp_reduced_water_solver_builds_and_exports_shared_scenario(tmp_path):
    cmake = shutil.which("cmake")
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    if cmake is None or compiler is None:
        pytest.skip("CMake and a C++ compiler are required for the native solver smoke test.")

    physics_dir = Path(__file__).resolve().parents[1]
    cpp_dir = physics_dir / "cpp"
    build_dir = tmp_path / "cpp_build"
    scenario_dir = tmp_path / "scenario" / "procedural"
    output_dir = tmp_path / "cpp_output"
    native_test_output = tmp_path / "native_test_output"

    scenario = generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=23, nx=32, ny=18, difficulty=0.55, feature_count=9)
    )
    scenario.write_package(scenario_dir)

    subprocess.run([cmake, "-S", str(cpp_dir), "-B", str(build_dir)], check=True)
    subprocess.run([cmake, "--build", str(build_dir)], check=True)

    subprocess.run(
        [str(build_dir / "raftsim_water_tests"), str(scenario_dir), str(native_test_output)],
        check=True,
    )
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
        ],
        check=True,
    )

    run_dir = output_dir / scenario.metadata.scenario_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))

    assert manifest["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_mode"] == "reduced"
    assert manifest["preserve_initial_mass"] is True
    assert validation["passed"] is True
    assert validation["mass_relative_drift"] < 1.0e-9
    assert "frames/frame_0000.csv" in manifest["frames"]
    assert manifest["probes"]
    assert manifest["cross_sections"]

    uncorrected_output_dir = tmp_path / "cpp_uncorrected_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(uncorrected_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    uncorrected_manifest = json.loads(
        (uncorrected_output_dir / scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert uncorrected_manifest["preserve_initial_mass"] is False

    finite_volume_output_dir = tmp_path / "cpp_finite_volume_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(finite_volume_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "pyclaw",
            "--flux-scheme",
            "roe",
            "--feature-strength-scale",
            "0",
            "--roughness-scale",
            "0",
            "--bed-slope-source-scale",
            "0",
        ],
        check=True,
    )
    finite_volume_manifest = json.loads(
        (finite_volume_output_dir / scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )

    assert finite_volume_manifest["solver"] == "raftsim_water_cpp_v1"
    assert finite_volume_manifest["solver_mode"] == "finite_volume"
    assert finite_volume_manifest["boundary_mode"] == "pyclaw"
    assert finite_volume_manifest["flux_scheme"] == "roe"

    uniform_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=24, nx=24, ny=12, duration=0.2)
    )
    uniform_scenario_dir = tmp_path / "scenario" / "uniform_channel"
    uniform_scenario.write_package(uniform_scenario_dir)
    scenario_boundary_output_dir = tmp_path / "cpp_finite_volume_scenario_boundary_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(uniform_scenario_dir),
            "--output",
            str(scenario_boundary_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "scenario",
            "--feature-strength-scale",
            "0",
            "--bed-slope-source-scale",
            "1",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    scenario_boundary_run = scenario_boundary_output_dir / uniform_scenario.metadata.scenario_id
    scenario_boundary_manifest = json.loads((scenario_boundary_run / "manifest.json").read_text(encoding="utf-8"))
    final_frame = scenario_boundary_run / scenario_boundary_manifest["frames"][-1]
    west_column = []
    with final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["col"]) == 0:
                west_column.append((float(row["h"]), float(row["u"])))

    assert scenario_boundary_manifest["boundary_mode"] == "scenario"
    assert west_column
    assert any(abs(h - 1.25) > 1.0e-6 or abs(u - 1.4) > 1.0e-6 for h, u in west_column)

    wet_dry_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="wet_dry_shoreline", seed=25, nx=24, ny=12, duration=0.2)
    )
    wet_dry_scenario_dir = tmp_path / "scenario" / "wet_dry_shoreline"
    wet_dry_scenario.write_package(wet_dry_scenario_dir)
    wet_dry_output_dir = tmp_path / "cpp_wet_dry_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(wet_dry_scenario_dir),
            "--output",
            str(wet_dry_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--feature-strength-scale",
            "0",
        ],
        check=True,
    )
    wet_dry_run = wet_dry_output_dir / wet_dry_scenario.metadata.scenario_id
    wet_dry_manifest = json.loads((wet_dry_run / "manifest.json").read_text(encoding="utf-8"))
    wet_dry_final_frame = wet_dry_run / wet_dry_manifest["frames"][-1]
    lateral_velocities = []
    wet_counts = 0
    with wet_dry_final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lateral_velocities.append(abs(float(row["v"])))
            wet_counts += int(row["wet"])

    assert wet_counts == int(wet_dry_scenario.initial_state.wet.sum())
    assert max(lateral_velocities) < 1.0e-9

    wet_dry_fv_output_dir = tmp_path / "cpp_wet_dry_fv_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(wet_dry_scenario_dir),
            "--output",
            str(wet_dry_fv_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "scenario",
            "--flux-scheme",
            "hll",
            "--feature-strength-scale",
            "0",
            "--roughness-scale",
            "0.5",
            "--bed-slope-source-scale",
            "0.75",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    wet_dry_fv_run = wet_dry_fv_output_dir / wet_dry_scenario.metadata.scenario_id
    wet_dry_fv_manifest = json.loads((wet_dry_fv_run / "manifest.json").read_text(encoding="utf-8"))
    wet_dry_fv_final_frame = wet_dry_fv_run / wet_dry_fv_manifest["frames"][-1]
    finite_volume_lateral_velocities = []
    finite_volume_wet_counts = 0
    with wet_dry_fv_final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            finite_volume_lateral_velocities.append(abs(float(row["v"])))
            finite_volume_wet_counts += int(row["wet"])

    assert wet_dry_fv_manifest["solver_mode"] == "finite_volume"
    assert wet_dry_fv_manifest["fixture_scoped_wet_dry_reconstruction"] is True
    assert finite_volume_wet_counts == int(wet_dry_scenario.initial_state.wet.sum())
    assert max(finite_volume_lateral_velocities) < 1.0e-9

    constriction_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="constriction", seed=26, nx=24, ny=12, duration=0.2)
    )
    constriction_scenario_dir = tmp_path / "scenario" / "constriction"
    constriction_scenario.write_package(constriction_scenario_dir)
    constriction_output_dir = tmp_path / "cpp_constriction_fv_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(constriction_scenario_dir),
            "--output",
            str(constriction_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "scenario",
            "--flux-scheme",
            "roe",
            "--feature-strength-scale",
            "0",
            "--roughness-scale",
            "0.5",
            "--bed-slope-source-scale",
            "0.75",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    constriction_run = constriction_output_dir / constriction_scenario.metadata.scenario_id
    constriction_manifest = json.loads((constriction_run / "manifest.json").read_text(encoding="utf-8"))
    constriction_final_frame = constriction_run / constriction_manifest["frames"][-1]
    constriction_audit_path = constriction_run / constriction_manifest["constriction_y_face_flux_source_audit"]["path"]
    constriction_features = json.loads((constriction_scenario_dir / "features.json").read_text(encoding="utf-8"))
    constriction_scenario_json = json.loads((constriction_scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    constriction_feature = next(feature for feature in constriction_features["features"] if feature["kind"] == "constriction")
    constriction_grid = constriction_scenario_json["grid"]
    throat_col = round((constriction_feature["center"]["x"] - constriction_grid["origin_x"]) / constriction_grid["dx"])
    initial_throat_wet_count = int(constriction_scenario.initial_state.wet[:, throat_col].sum())
    final_throat_wet_count = 0
    dry_bank_depths = []
    final_wet_rows = []
    final_throat_u_by_row = {}
    final_throat_v_by_row = {}
    wet_rows = [index for index, wet in enumerate(constriction_scenario.initial_state.wet[:, throat_col]) if wet]
    with constriction_final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row_index = int(row["row"])
            col_index = int(row["col"])
            if col_index != throat_col:
                continue
            if int(row["wet"]):
                final_throat_wet_count += 1
                final_wet_rows.append(row_index)
                final_throat_u_by_row[row_index] = float(row["u"])
                final_throat_v_by_row[row_index] = abs(float(row["v"]))
            if not constriction_scenario.initial_state.wet[row_index, throat_col]:
                dry_bank_depths.append(float(row["h"]))

    assert constriction_manifest["fixture_scoped_constriction_boundary_mask"] is True
    assert constriction_manifest["fixture_scoped_constriction_upstream_edge_flux_source"] is True
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["bounded"] is True
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["mass_conservative_lateral_face_flux"] is True
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["preconditions_inflow_edge_state"] is True
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "recognizes_lower_edge_face_as_outside_to_first_wet"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "recognizes_upper_edge_face_as_next_to_last_to_last_wet"
        ]
        is True
    )
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["excluded_from_later_depth_receivers"] is True
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["conservative_y_face_opposition_flux"] is True
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "opposition_flux_transition_weight_floor"
        ]
        == pytest.approx(1.1)
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "opposition_flux_preserves_lower_positive_upper_negative_signs"
        ]
        is True
    )
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["includes_transition_edge_faces"] is True
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "lower_edge_transition_momentum_source"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "lower_edge_transition_momentum_weight_floor"
        ]
        == pytest.approx(2.0)
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "lower_edge_transition_momentum_window_cells"
        ]
        == pytest.approx(2.0)
    )
    assert constriction_manifest["constriction_upstream_edge_flux_source"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_y_face_state_reconstruction"] is True
    assert constriction_manifest["constriction_y_face_state_reconstruction"]["bounded"] is True
    assert constriction_manifest["constriction_y_face_state_reconstruction"]["predictor_state_only"] is True
    assert (
        constriction_manifest["constriction_y_face_state_reconstruction"][
            "applies_before_y_face_riemann_solve"
        ]
        is True
    )
    assert constriction_manifest["constriction_y_face_state_reconstruction"]["includes_transition_edge_faces"] is True
    assert constriction_manifest["constriction_y_face_state_reconstruction"]["requires_feature_forcing"] is False
    assert (
        constriction_manifest["constriction_y_face_state_reconstruction"]["transition_velocity_weight_floor"]
        == pytest.approx(1.4)
    )
    assert (
        constriction_manifest["constriction_y_face_state_reconstruction"][
            "resets_lower_outside_companion_velocity"
        ]
        is True
    )
    assert constriction_manifest["fixture_scoped_constriction_upstream_edge_support_reconstruction"] is True
    assert constriction_manifest["constriction_upstream_edge_support"]["bounded"] is True
    assert constriction_manifest["constriction_upstream_edge_support"]["mass_conservative_depth_transfer"] is True
    assert (
        constriction_manifest["constriction_upstream_edge_support"][
            "preserves_lower_positive_upper_negative_opposition"
        ]
        is True
    )
    assert constriction_manifest["constriction_upstream_edge_support"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_lower_edge_width_depth_balance"] is True
    assert constriction_manifest["constriction_lower_edge_width_depth_balance"]["bounded"] is True
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["mass_conservative_depth_transfer"]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["requires_feature_forcing"]
        is False
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["final_lower_edge_support"]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_transition_velocity_weight_floor"
        ]
        == pytest.approx(0.75)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["final_flux_magnitude_balance"]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["final_flux_magnitude_velocity_only"]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"]["final_flux_magnitude_mass_preserving"]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_flux_magnitude_runs_after_upstream_centerline_timing"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_flux_magnitude_shelf_cross_stream_fraction"
        ]
        == pytest.approx(0.82)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_flux_magnitude_first_wet_cross_stream_fraction"
        ]
        == pytest.approx(0.88)
    )
    assert (
        constriction_manifest["fixture_scoped_constriction_lower_edge_transition_source_depth_balance"]
        is True
    )
    lower_transition_source_depth = constriction_manifest[
        "constriction_lower_edge_transition_source_depth_balance"
    ]
    assert lower_transition_source_depth["bounded"] is True
    assert (
        lower_transition_source_depth["mass_conservative_upper_edge_to_lower_edge_transfer"]
        is True
    )
    assert lower_transition_source_depth["applies_only_upstream_transition_columns"] is True
    assert (
        lower_transition_source_depth["transition_weight_formula"]
        == "4 * approach_weight * (1 - approach_weight)"
    )
    assert lower_transition_source_depth["runs_after_final_lower_edge_flux_magnitude_balance"] is True
    assert lower_transition_source_depth["support_rate_per_s"] == pytest.approx(14.0)
    assert lower_transition_source_depth["max_depth_m_per_s"] == pytest.approx(3.0)
    assert lower_transition_source_depth["lower_shelf_depth_scale"] == pytest.approx(0.48)
    assert lower_transition_source_depth["lower_first_wet_depth_scale"] == pytest.approx(1.52)
    assert lower_transition_source_depth["upper_donor_floor_depth_scale"] == pytest.approx(0.42)
    assert lower_transition_source_depth["lower_shelf_cross_stream_fraction"] == pytest.approx(0.78)
    assert lower_transition_source_depth["lower_first_wet_cross_stream_fraction"] == pytest.approx(0.34)
    assert lower_transition_source_depth["upper_edge_cross_stream_fraction"] == pytest.approx(0.72)
    assert lower_transition_source_depth["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_upstream_boundary_column_support"] is True
    assert constriction_manifest["constriction_upstream_boundary_column_support"]["bounded"] is True
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["boundary_sourced_depth_addition"]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["applies_only_inflow_boundary_column"]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["requires_feature_forcing"]
        is False
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["lower_support_span_cells"]
        == 2
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["support_rate_per_s"]
        == pytest.approx(4.0)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["max_depth_m_per_s"]
        == pytest.approx(2.0)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["shelf_depth_scale"]
        == pytest.approx(0.65)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["lower_depth_scale"]
        == pytest.approx(1.34)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["interior_depth_scale"]
        == pytest.approx(1.45)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_column_support"]["shelf_speed_fraction"]
        == pytest.approx(1.65)
    )
    assert constriction_manifest["fixture_scoped_constriction_upstream_shelf_balance"] is True
    assert constriction_manifest["constriction_upstream_shelf_balance"]["bounded"] is True
    assert (
        constriction_manifest["constriction_upstream_shelf_balance"][
            "mass_conservative_upper_edge_to_lower_shelf_transfer"
        ]
        is True
    )
    assert constriction_manifest["constriction_upstream_shelf_balance"]["runs_after_inflow_boundary_support"] is True
    assert constriction_manifest["constriction_upstream_shelf_balance"]["lower_shelf_depth_scale"] == pytest.approx(0.62)
    assert (
        constriction_manifest["constriction_upstream_shelf_balance"]["lower_first_wet_depth_scale"]
        == pytest.approx(1.32)
    )
    assert constriction_manifest["constriction_upstream_shelf_balance"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_upstream_centerline_timing_balance"] is True
    assert constriction_manifest["constriction_upstream_centerline_timing_balance"]["bounded"] is True
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"][
            "mass_conservative_upper_edge_to_centerline_transfer"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"][
            "runs_after_upstream_shelf_balance"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"][
            "uses_duration_normalized_late_response"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"]["near_speed_fraction"]
        == pytest.approx(0.45)
    )
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"][
            "late_edge_cross_stream_velocity_only"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_centerline_timing_balance"]["requires_feature_forcing"]
        is False
    )
    assert constriction_manifest["fixture_scoped_constriction_upstream_boundary_upper_edge_velocity_shape"] is True
    assert constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["bounded"] is True
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["velocity_only"]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["mass_preserving"]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"][
            "runs_after_upstream_centerline_timing"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["window_cells"]
        == 2
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["rate_per_s"]
        == pytest.approx(10.0)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"]["max_speed_m_per_s2"]
        == pytest.approx(5.0)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"][
            "cross_stream_fraction"
        ]
        == pytest.approx(1.25)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"][
            "interior_cross_stream_fraction"
        ]
        == pytest.approx(0.40)
    )
    assert (
        constriction_manifest["constriction_upstream_boundary_upper_edge_velocity_shape"][
            "requires_feature_forcing"
        ]
        is False
    )
    assert constriction_manifest["fixture_scoped_constriction_upper_edge_opposition_balance"] is True
    assert constriction_manifest["constriction_upper_edge_opposition_balance"]["bounded"] is True
    assert (
        constriction_manifest["constriction_upper_edge_opposition_balance"]["mass_conservative_depth_transfer"]
        is True
    )
    assert (
        constriction_manifest["constriction_upper_edge_opposition_balance"]["velocity_only_after_depth_transfer"]
        is True
    )
    assert constriction_manifest["constriction_upper_edge_opposition_balance"]["uses_transition_aware_weight"] is True
    assert constriction_manifest["constriction_upper_edge_opposition_balance"]["supports_upper_outside_shelf"] is True
    assert constriction_manifest["constriction_upper_edge_opposition_balance"]["final_flux_magnitude_balance"] is True
    assert (
        constriction_manifest["constriction_upper_edge_opposition_balance"]["requires_feature_forcing"]
        is False
    )
    assert constriction_manifest["fixture_scoped_constriction_y_face_hydrostatic_source_split"] is True
    assert constriction_manifest["constriction_y_face_hydrostatic_source_split"]["bounded"] is True
    assert constriction_manifest["constriction_y_face_hydrostatic_source_split"]["uses_predictor_riemann_state"] is True
    assert (
        constriction_manifest["constriction_y_face_hydrostatic_source_split"][
            "reduces_matching_cell_center_y_source_fraction"
        ]
        is True
    )
    assert constriction_manifest["constriction_y_face_hydrostatic_source_split"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_cross_stream_momentum_source"] is True
    assert constriction_manifest["constriction_cross_stream_momentum_source"]["bounded"] is True
    assert constriction_manifest["constriction_cross_stream_momentum_source"]["mass_preserving_source"] is True
    assert constriction_manifest["constriction_cross_stream_momentum_source"]["min_depth_m"] == pytest.approx(0.3)
    assert constriction_manifest["constriction_cross_stream_momentum_source"]["applies_only_recovery_zone"] is True
    assert constriction_manifest["constriction_cross_stream_momentum_source"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_dry_bank_reconstruction"] is True
    assert constriction_manifest["fixture_scoped_constriction_wet_band_relaxation"] is True
    assert constriction_manifest["fixture_scoped_constriction_wet_band_span_shaping"] is True
    assert constriction_manifest["fixture_scoped_constriction_wet_band_profile_relaxation"] is True
    assert constriction_manifest["constriction_wet_band_profile_relaxation"]["bounded"] is True
    assert (
        constriction_manifest["constriction_wet_band_profile_relaxation"]["mass_conservative_depth_transfer"]
        is True
    )
    assert (
        constriction_manifest["constriction_wet_band_profile_relaxation"]["requires_feature_forcing"]
        is False
    )
    assert constriction_manifest["fixture_scoped_constriction_upstream_interior_velocity_relaxation"] is True
    assert constriction_manifest["constriction_upstream_interior_velocity_relaxation"]["bounded"] is True
    assert constriction_manifest["constriction_upstream_interior_velocity_relaxation"]["velocity_only"] is True
    assert constriction_manifest["constriction_upstream_interior_velocity_relaxation"]["mass_preserving"] is True
    assert (
        constriction_manifest["constriction_upstream_interior_velocity_relaxation"]["requires_feature_forcing"]
        is False
    )
    assert constriction_manifest["fixture_scoped_constriction_asymmetric_wet_band_envelope"] is True
    assert constriction_manifest["fixture_scoped_constriction_volume_response_reconstruction"] is True
    assert constriction_manifest["constriction_volume_response"]["bounded"] is True
    assert constriction_manifest["fixture_scoped_constriction_recovery_energy_transport_reconstruction"] is True
    assert constriction_manifest["constriction_recovery_energy_transport"]["mass_conservative"] is True
    assert constriction_manifest["fixture_scoped_constriction_upstream_shoulder_froude_reconstruction"] is True
    assert constriction_manifest["constriction_upstream_shoulder_froude"]["mass_conservative_depth_taper"] is True
    assert constriction_manifest["fixture_scoped_constriction_local_shallow_fringe_reconstruction"] is True
    assert constriction_manifest["constriction_local_shallow_fringe"]["bounded"] is True
    assert constriction_manifest["constriction_local_shallow_fringe"]["mass_conservative_recovery_transfer"] is True
    assert constriction_manifest["fixture_scoped_constriction_near_throat_support_reconstruction"] is True
    assert constriction_manifest["constriction_near_throat_support"]["mass_conservative_excess_transfer"] is True
    assert (
        constriction_manifest["constriction_near_throat_support"]["interior_cross_stream_fraction"]
        == pytest.approx(0.18)
    )
    assert (
        constriction_manifest["constriction_near_throat_support"]["late_interior_cross_stream_fraction"]
        == pytest.approx(0.04)
    )
    assert (
        constriction_manifest["constriction_near_throat_support"]["late_interior_speed_fraction"]
        == pytest.approx(1.07)
    )
    assert constriction_manifest["constriction_near_throat_support"]["lower_shelf_depth_weight"] == pytest.approx(0.16)
    assert constriction_manifest["constriction_near_throat_support"]["upper_shelf_depth_weight"] == pytest.approx(0.10)
    assert (
        constriction_manifest["constriction_near_throat_support"]["late_lower_shelf_depth_weight"]
        == pytest.approx(0.31)
    )
    assert constriction_manifest["constriction_near_throat_support"]["lower_shelf_speed_fraction"] == pytest.approx(0.62)
    assert (
        constriction_manifest["constriction_near_throat_support"]["late_lower_shelf_speed_fraction"]
        == pytest.approx(0.95)
    )
    assert (
        constriction_manifest["constriction_near_throat_support"]["lower_shelf_cross_stream_fraction"]
        == pytest.approx(1.0)
    )
    assert (
        constriction_manifest["constriction_near_throat_support"]["late_lower_shelf_cross_stream_fraction"]
        == pytest.approx(0.41)
    )
    assert (
        constriction_manifest["constriction_near_throat_support"]["upper_shelf_cross_stream_fraction"]
        == pytest.approx(0.36)
    )
    assert constriction_manifest["constriction_near_throat_support"]["keeps_shifted_upper_row_interior_until_shelf_support"] is True
    assert constriction_manifest["constriction_near_throat_support"]["uses_mass_bounded_shelf_interior_profile"] is True
    assert constriction_manifest["constriction_near_throat_support"]["uses_duration_normalized_shelf_response_timing"] is True
    assert constriction_manifest["fixture_scoped_constriction_upstream_recovery_depth_distribution"] is True
    assert constriction_manifest["constriction_upstream_recovery_depth_distribution"]["mass_conservative"] is True
    assert constriction_manifest["fixture_scoped_constriction_velocity_energy_timing_reconstruction"] is True
    assert constriction_manifest["constriction_velocity_energy_timing"]["velocity_only"] is True
    assert constriction_manifest["constriction_velocity_energy_timing"]["mass_preserving"] is True
    assert constriction_manifest["fixture_scoped_constriction_flux_mass_froude_timing_reconstruction"] is True
    assert constriction_manifest["constriction_flux_mass_froude_timing"]["mass_conservative_recovery_transfer"] is True
    assert constriction_manifest["fixture_scoped_constriction_lateral_slope_shape_reconstruction"] is True
    assert constriction_manifest["constriction_lateral_slope_shape"]["mass_conservative_dry_bank_depth_cap"] is True
    assert constriction_manifest["constriction_lateral_slope_shape"]["applies_side_specific_local_fringe_targets"] is True
    assert constriction_manifest["fixture_scoped_constriction_center_throat_circulation_reconstruction"] is True
    assert constriction_manifest["constriction_center_throat_circulation"]["velocity_only"] is True
    assert constriction_manifest["constriction_center_throat_circulation"]["mass_preserving"] is True
    assert constriction_manifest["fixture_scoped_constriction_localized_circulation_reconstruction"] is True
    assert constriction_manifest["constriction_localized_circulation"]["velocity_only"] is True
    assert constriction_manifest["constriction_localized_circulation"]["mass_preserving"] is True
    assert constriction_manifest["constriction_localized_circulation"]["applies_center_throat_near_recovery"] is True
    assert constriction_manifest["constriction_localized_circulation"]["upstream_component_disabled_for_froude_guard"] is True
    assert constriction_manifest["constriction_localized_circulation"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_recovery_centerline_timing"] is True
    assert constriction_manifest["constriction_recovery_centerline_timing"]["mass_preserving_velocity_relaxation"] is True
    assert constriction_manifest["constriction_recovery_centerline_timing"]["mass_conservative_depth_transfer"] is True
    assert constriction_manifest["constriction_recovery_centerline_timing"]["uses_duration_normalized_late_response"] is True
    assert constriction_manifest["constriction_recovery_centerline_timing"]["late_speed_fraction"] == pytest.approx(1.08)
    assert constriction_manifest["constriction_recovery_centerline_timing"]["late_cross_stream_fraction"] == pytest.approx(0.26)
    assert constriction_manifest["constriction_recovery_centerline_timing"]["late_depth_scale"] == pytest.approx(1.0)
    assert constriction_manifest["constriction_recovery_centerline_timing"]["depth_donor_scope"] == "upper_recovery_shelf_row"
    assert constriction_manifest["constriction_recovery_centerline_timing"]["applies_only_near_recovery_centerline"] is True
    assert constriction_manifest["constriction_recovery_centerline_timing"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_downstream_return_current_balance"] is True
    assert constriction_manifest["constriction_downstream_return_current_balance"]["bounded"] is True
    assert constriction_manifest["constriction_downstream_return_current_balance"]["velocity_only"] is True
    assert constriction_manifest["constriction_downstream_return_current_balance"]["mass_preserving"] is True
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "runs_after_upstream_centerline_timing_balance"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "uses_duration_normalized_late_response"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "applies_only_downstream_widened_upper_edge"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "downstream_upper_edge_speed_fraction"
        ]
        == pytest.approx(-0.05)
    )
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "downstream_upper_inner_speed_fraction"
        ]
        == pytest.approx(0.65)
    )
    assert constriction_manifest["constriction_downstream_return_current_balance"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_momentum_reconstruction"] is True
    assert constriction_manifest["constriction_y_face_flux_source_audit"]["present"] is True
    assert constriction_manifest["constriction_y_face_flux_source_audit"]["uses_internal_cpp_riemann_flux"] is True
    assert constriction_manifest["constriction_y_face_flux_source_audit"]["records_constriction_face_state_reconstruction"] is True
    assert constriction_manifest["constriction_y_face_flux_source_audit"]["records_hydrostatic_face_source_terms"] is True
    assert (
        constriction_manifest["constriction_y_face_flux_source_audit"][
            "records_constriction_hydrostatic_source_split_terms"
        ]
        is True
    )
    assert constriction_manifest["constriction_y_face_flux_source_audit"]["records_constriction_face_source_delta"] is True
    assert constriction_audit_path.exists()
    with constriction_audit_path.open(newline="", encoding="utf-8") as handle:
        audit_rows = list(csv.DictReader(handle))
    assert audit_rows
    assert {"lower_edge_face", "upper_edge_face", "lower_inner_source_face", "upper_outer_face"}.issubset(
        {row["face_role"] for row in audit_rows}
    )
    assert any(int(row["constriction_face_source_applied"]) == 1 for row in audit_rows)
    assert any(int(row["constriction_hydrostatic_source_split_applied"]) == 1 for row in audit_rows)
    assert any(int(row["hydrostatic_face_source_enabled"]) == 1 for row in audit_rows)
    assert any(int(row["constriction_face_state_reconstruction_applied"]) == 1 for row in audit_rows)
    assert all("post_left_flux_h_m3ps" in row for row in audit_rows)
    assert all("face_state_north_v" in row for row in audit_rows)
    assert all("constriction_source_split_left_hv_m3ps2" in row for row in audit_rows)
    assert all("south_cell_bed_slope_source_hv_per_s" in row for row in audit_rows)
    assert final_throat_wet_count == initial_throat_wet_count + 1
    assert max(dry_bank_depths) <= constriction_manifest["constriction_near_throat_support"]["throat_depth_scale"] * 1.25
    assert final_wet_rows[0] == wet_rows[0] - 1
    assert final_wet_rows[-1] == wet_rows[-1]
    assert min(final_throat_u_by_row[row] for row in wet_rows) >= (
        constriction_scenario.initial_state.u[:, throat_col].max() - 1.0e-9
    )
    assert final_throat_u_by_row[final_wet_rows[0]] < min(final_throat_u_by_row[row] for row in wet_rows)
    assert min(final_throat_v_by_row[final_wet_rows[0]], final_throat_v_by_row[final_wet_rows[-1]]) > 1.0

    cascading_scenario_dir = tmp_path / "scenario" / "cascading"
    cascading_output_dir = tmp_path / "cpp_cascading_output"
    cascading_package = generate_california_pool_drop_cascading_scenario2_5d(
        CaliforniaPoolDropParameters2_5D(seed=31, nx=64, ny=24, duration=1.0)
    )
    cascading_package.write_package(cascading_scenario_dir)
    native_result = subprocess.run(
        [str(build_dir / "raftsim_water_tests"), str(cascading_scenario_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "cascading_reaches=7" in native_result.stdout

    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(cascading_scenario_dir),
            "--output",
            str(cascading_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
        ],
        check=True,
    )
    cascading_manifest = json.loads(
        (cascading_output_dir / cascading_package.scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert cascading_manifest["cascading"]["present"] is True
    assert cascading_manifest["cascading"]["reach_count"] == 7
    assert cascading_manifest["cascading"]["drop_transition_count"] == 1


def test_chrono_smoke_target_is_optional_and_outside_unreal():
    physics_dir = Path(__file__).resolve().parents[1]
    cmake_text = (physics_dir / "cpp" / "CMakeLists.txt").read_text(encoding="utf-8")
    smoke_source = (physics_dir / "cpp" / "tools" / "chrono_smoke_test.cpp").read_text(encoding="utf-8")

    assert "find_package(Chrono QUIET)" in cmake_text
    assert "add_executable(raftsim_chrono_smoke" in cmake_text
    assert "Project Chrono not found; skipping raftsim_chrono_smoke target" in cmake_text
    assert "ChSystemSMC" in smoke_source
    assert "chrono_smoke=ok" in smoke_source
