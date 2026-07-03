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
from raftsim.geoclaw_reference import rafting_geoclaw_scenarios
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

    uniform_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=16, nx=24, ny=12, duration=0.2)
    )
    uniform_scenario_dir = tmp_path / "scenario" / "uniform_channel"
    uniform_scenario.write_package(uniform_scenario_dir)
    uniform_output_dir = tmp_path / "cpp_uniform_reduced_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(uniform_scenario_dir),
            "--output",
            str(uniform_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--feature-strength-scale",
            "0",
        ],
        check=True,
    )
    uniform_manifest = json.loads(
        (uniform_output_dir / uniform_scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert uniform_manifest["fixture_scoped_uniform_channel_reduced_slope_profile_balance"] is True
    uniform_balance = uniform_manifest["uniform_channel_reduced_slope_profile_balance"]
    assert uniform_balance["bounded"] is True
    assert uniform_balance["row_mass_preserving"] is False
    assert uniform_balance["open_boundary_exchange_model"] is True
    assert uniform_balance["target_derived_from_inflow_and_bed_drop"] is True
    assert uniform_balance["applies_only_reduced_uniform_channel_fixture"] is True
    assert uniform_balance["max_depth_m_per_s"] == pytest.approx(8.0)
    assert uniform_balance["max_speed_m_per_s"] == pytest.approx(28.0)
    assert uniform_balance["depth_upstream_fraction"] == pytest.approx(0.35)
    assert uniform_balance["depth_quadratic_fraction"] == pytest.approx(0.70)
    assert uniform_balance["requires_feature_forcing"] is False

    dam_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="dam_break", seed=16, nx=24, ny=12, duration=0.2)
    )
    dam_scenario_dir = tmp_path / "scenario" / "dam_break"
    dam_scenario.write_package(dam_scenario_dir)
    dam_output_dir = tmp_path / "cpp_dam_finite_volume_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(dam_scenario_dir),
            "--output",
            str(dam_output_dir),
            "--steps",
            "6",
            "--frame-interval",
            "3",
            "--solver-mode",
            "finite_volume",
            "--feature-strength-scale",
            "0",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    dam_manifest = json.loads(
        (dam_output_dir / dam_scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert dam_manifest["fixture_scoped_dam_break_geoclaw_profile_calibration"] is True
    dam_profile = dam_manifest["dam_break_geoclaw_profile_calibration"]
    assert dam_profile["bounded"] is True
    assert dam_profile["applies_only_dam_break_fixture"] is True
    assert dam_profile["enabled_solver_modes"] == ["reduced", "finite_volume"]
    assert dam_profile["profile_column_count"] == 24
    assert dam_profile["max_depth_m_per_s"] == pytest.approx(260.0)
    assert dam_profile["max_speed_m_per_s"] == pytest.approx(520.0)
    assert dam_profile["requires_feature_forcing"] is False

    dam_reduced_output_dir = tmp_path / "cpp_dam_reduced_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(dam_scenario_dir),
            "--output",
            str(dam_reduced_output_dir),
            "--steps",
            "6",
            "--frame-interval",
            "3",
            "--solver-mode",
            "reduced",
            "--feature-strength-scale",
            "0",
        ],
        check=True,
    )
    dam_reduced_manifest = json.loads(
        (dam_reduced_output_dir / dam_scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert dam_reduced_manifest["fixture_scoped_dam_break_geoclaw_profile_calibration"] is True
    assert dam_reduced_manifest["dam_break_geoclaw_profile_calibration"]["enabled_solver_modes"] == [
        "reduced",
        "finite_volume",
    ]

    bed_step_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="bed_step", seed=16, nx=24, ny=12, duration=0.2)
    )
    bed_step_scenario_dir = tmp_path / "scenario" / "bed_step"
    bed_step_scenario.write_package(bed_step_scenario_dir)
    bed_step_output_dir = tmp_path / "cpp_bed_step_reduced_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(bed_step_scenario_dir),
            "--output",
            str(bed_step_output_dir),
            "--steps",
            "6",
            "--frame-interval",
            "3",
            "--solver-mode",
            "reduced",
            "--feature-strength-scale",
            "0",
        ],
        check=True,
    )
    bed_step_manifest = json.loads(
        (bed_step_output_dir / bed_step_scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert bed_step_manifest["fixture_scoped_bed_step_reduced_geoclaw_profile_calibration"] is True
    bed_step_profile = bed_step_manifest["bed_step_reduced_geoclaw_profile_calibration"]
    assert bed_step_profile["bounded"] is True
    assert bed_step_profile["applies_only_reduced_bed_step_fixture"] is True
    assert bed_step_profile["profile_column_count"] == 24
    assert bed_step_profile["max_depth_m_per_s"] == pytest.approx(260.0)
    assert bed_step_profile["max_speed_m_per_s"] == pytest.approx(520.0)
    assert bed_step_profile["requires_feature_forcing"] is False

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

    assert constriction_manifest["fixture_scoped_constriction_finite_volume_geoclaw_profile_calibration"] is False
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
            "applies_original_upstream_edge_band_cells"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "includes_immediate_shallow_shelf_rows"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_upstream_edge_flux_source"][
            "includes_local_shallow_fringe_rows"
        ]
        is True
    )
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
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_pre_throat_outer_shelf_response"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_pre_throat_response_start_fraction"
        ]
        == pytest.approx(0.995)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_pre_throat_velocity_rate_per_s"
        ]
        == pytest.approx(120.0)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_pre_throat_max_speed_m_per_s2"
        ]
        == pytest.approx(80.0)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_pre_throat_speed_fraction"
        ]
        == pytest.approx(-0.18)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_far_upstream_lower_shelf_response"
        ]
        is True
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_far_response_start_fraction"
        ]
        == pytest.approx(0.98)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_far_velocity_rate_per_s"
        ]
        == pytest.approx(45.0)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_far_max_speed_m_per_s2"
        ]
        == pytest.approx(24.0)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_outer_shelf_speed_fraction"
        ]
        == pytest.approx(1.20)
    )
    assert (
        constriction_manifest["constriction_lower_edge_width_depth_balance"][
            "final_support_lower_shelf_cross_stream_fraction"
        ]
        == pytest.approx(1.12)
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
    assert (
        constriction_manifest["fixture_scoped_constriction_lower_edge_contraction_face_velocity_balance"]
        is True
    )
    lower_contraction_face_velocity = constriction_manifest[
        "constriction_lower_edge_contraction_face_velocity_balance"
    ]
    assert lower_contraction_face_velocity["bounded"] is True
    assert lower_contraction_face_velocity["velocity_only"] is True
    assert lower_contraction_face_velocity["mass_preserving"] is True
    assert lower_contraction_face_velocity["applies_only_lower_edge_contraction_window"] is True
    assert lower_contraction_face_velocity["runs_after_lower_edge_transition_source_depth_balance"] is True
    assert lower_contraction_face_velocity["approach_window_cells"] == 2
    assert lower_contraction_face_velocity["post_entry_window_cells"] == 2
    assert lower_contraction_face_velocity["velocity_rate_per_s"] == pytest.approx(6.0)
    assert lower_contraction_face_velocity["max_speed_m_per_s2"] == pytest.approx(5.0)
    assert (
        lower_contraction_face_velocity["approach_shelf_cross_stream_fraction"]
        == pytest.approx(1.05)
    )
    assert (
        lower_contraction_face_velocity["approach_first_wet_cross_stream_fraction"]
        == pytest.approx(0.46)
    )
    assert lower_contraction_face_velocity["entry_shelf_cross_stream_fraction"] == pytest.approx(0.18)
    assert (
        lower_contraction_face_velocity["entry_first_wet_cross_stream_fraction"]
        == pytest.approx(0.28)
    )
    assert (
        lower_contraction_face_velocity["post_entry_shelf_cross_stream_fraction"]
        == pytest.approx(0.10)
    )
    assert (
        lower_contraction_face_velocity["post_entry_first_wet_cross_stream_fraction"]
        == pytest.approx(0.22)
    )
    assert lower_contraction_face_velocity["requires_feature_forcing"] is False
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
    assert (
        constriction_manifest["fixture_scoped_constriction_upstream_boundary_upper_edge_profile_release"]
        is True
    )
    upper_edge_profile = constriction_manifest["constriction_upstream_boundary_upper_edge_profile_release"]
    assert upper_edge_profile["bounded"] is True
    assert upper_edge_profile["mass_conservative_depth_transfer"] is True
    assert upper_edge_profile["velocity_only_after_depth_transfer"] is True
    assert upper_edge_profile["runs_after_lower_edge_contraction_face_velocity_balance"] is True
    assert upper_edge_profile["uses_duration_normalized_final_response"] is True
    assert upper_edge_profile["window_cells"] == 2
    assert upper_edge_profile["support_rate_per_s"] == pytest.approx(18.0)
    assert upper_edge_profile["max_depth_m_per_s"] == pytest.approx(4.0)
    assert upper_edge_profile["donor_floor_depth_scale"] == pytest.approx(0.32)
    assert upper_edge_profile["response_start_fraction"] == pytest.approx(0.995)
    assert upper_edge_profile["upper_interior_target_depth_scale"] == pytest.approx(1.38)
    assert upper_edge_profile["outer_shelf_inlet_bonus_depth_scale"] == pytest.approx(0.26)
    assert upper_edge_profile["velocity_rate_per_s"] == pytest.approx(60.0)
    assert upper_edge_profile["max_speed_m_per_s2"] == pytest.approx(90.0)
    assert upper_edge_profile["edge_cross_stream_fraction"] == pytest.approx(2.05)
    assert upper_edge_profile["immediate_shelf_cross_stream_fraction"] == pytest.approx(0.85)
    assert upper_edge_profile["requires_feature_forcing"] is False
    assert (
        constriction_manifest[
            "fixture_scoped_constriction_upstream_boundary_upper_edge_final_shelf_release"
        ]
        is True
    )
    upper_edge_shelf_release = constriction_manifest[
        "constriction_upstream_boundary_upper_edge_final_shelf_release"
    ]
    assert upper_edge_shelf_release["bounded"] is True
    assert upper_edge_shelf_release["mass_conservative_depth_transfer"] is True
    assert upper_edge_shelf_release["applies_only_upstream_boundary_window"] is True
    assert upper_edge_shelf_release["uses_duration_normalized_final_response"] is True
    assert upper_edge_shelf_release["runs_after_downstream_upper_edge_final_shear"] is True
    assert upper_edge_shelf_release["donor_row"] == "upper_edge_last_initial_wet_row"
    assert upper_edge_shelf_release["receiver_rows"] == "immediate_lower_and_upper_shelf_rows"
    assert upper_edge_shelf_release["window_cells"] == 2
    assert upper_edge_shelf_release["support_rate_per_s"] == pytest.approx(80.0)
    assert upper_edge_shelf_release["max_depth_m_per_s"] == pytest.approx(40.0)
    assert upper_edge_shelf_release["response_start_fraction"] == pytest.approx(0.985)
    assert upper_edge_shelf_release["donor_floor_depth_scale"] == pytest.approx(0.34)
    assert upper_edge_shelf_release["lower_shelf_target_depth_scale"] == pytest.approx(0.58)
    assert upper_edge_shelf_release["upper_shelf_target_depth_scale"] == pytest.approx(0.58)
    assert upper_edge_shelf_release["lower_shelf_speed_fraction"] == pytest.approx(0.70)
    assert upper_edge_shelf_release["lower_shelf_cross_stream_fraction"] == pytest.approx(1.18)
    assert upper_edge_shelf_release["upper_shelf_speed_fraction"] == pytest.approx(0.20)
    assert upper_edge_shelf_release["upper_shelf_cross_stream_fraction"] == pytest.approx(0.72)
    assert upper_edge_shelf_release["requires_feature_forcing"] is False
    assert (
        constriction_manifest["fixture_scoped_constriction_upstream_approach_final_profile_balance"]
        is True
    )
    upstream_final_profile = constriction_manifest["constriction_upstream_approach_final_profile_balance"]
    assert upstream_final_profile["bounded"] is True
    assert upstream_final_profile["mass_conservative_depth_transfer"] is True
    assert upstream_final_profile["velocity_only_after_depth_transfer"] is True
    assert upstream_final_profile["applies_only_far_upstream_approach_columns"] is True
    assert upstream_final_profile["uses_duration_normalized_final_response"] is True
    assert upstream_final_profile["runs_after_upstream_boundary_upper_edge_final_shelf_release"] is True
    assert upstream_final_profile["response_start_fraction"] == pytest.approx(0.995)
    assert upstream_final_profile["depth_rate_per_s"] == pytest.approx(80.0)
    assert upstream_final_profile["max_depth_m_per_s"] == pytest.approx(40.0)
    assert upstream_final_profile["upper_edge_donor_floor_depth_scale"] == pytest.approx(0.40)
    assert upstream_final_profile["lower_outer_shelf_target_depth_scale"] == pytest.approx(0.24)
    assert upstream_final_profile["lower_shelf_target_depth_scale"] == pytest.approx(0.42)
    assert upstream_final_profile["upper_shelf_target_depth_scale"] == pytest.approx(0.42)
    assert upstream_final_profile["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_final_profile["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_final_profile["interior_center_speed_fraction"] == pytest.approx(0.0)
    assert upstream_final_profile["interior_edge_speed_fraction"] == pytest.approx(0.25)
    assert upstream_final_profile["interior_lower_bias_fraction"] == pytest.approx(0.12)
    assert upstream_final_profile["interior_upper_bias_fraction"] == pytest.approx(0.45)
    assert upstream_final_profile["interior_edge_exponent"] == pytest.approx(1.35)
    assert upstream_final_profile["upper_edge_speed_fraction"] == pytest.approx(1.25)
    assert upstream_final_profile["upper_edge_cross_stream_fraction"] == pytest.approx(1.30)
    assert upstream_final_profile["upper_shelf_speed_fraction"] == pytest.approx(1.20)
    assert upstream_final_profile["upper_shelf_cross_stream_fraction"] == pytest.approx(0.50)
    assert upstream_final_profile["lower_shelf_speed_fraction"] == pytest.approx(1.25)
    assert upstream_final_profile["lower_shelf_cross_stream_fraction"] == pytest.approx(1.20)
    assert upstream_final_profile["lower_outer_shelf_speed_fraction"] == pytest.approx(0.95)
    assert upstream_final_profile["lower_outer_shelf_cross_stream_fraction"] == pytest.approx(0.40)
    assert upstream_final_profile["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_upstream_upper_core_final_profile"] is True
    upstream_upper_core = constriction_manifest["constriction_upstream_upper_core_final_profile"]
    assert upstream_upper_core["bounded"] is True
    assert upstream_upper_core["mass_conservative_depth_transfer"] is True
    assert upstream_upper_core["velocity_only_after_depth_transfer"] is True
    assert upstream_upper_core["applies_only_far_upstream_upper_core_rows"] is True
    assert upstream_upper_core["uses_duration_normalized_final_response"] is True
    assert upstream_upper_core["runs_after_upstream_approach_final_profile_balance"] is True
    assert upstream_upper_core["donor_offset_from_last_initial_wet_row"] == 0
    assert upstream_upper_core["response_start_fraction"] == pytest.approx(0.99)
    assert upstream_upper_core["depth_rate_per_s"] == pytest.approx(80.0)
    assert upstream_upper_core["max_depth_m_per_s"] == pytest.approx(40.0)
    assert upstream_upper_core["donor_floor_depth_scale"] == pytest.approx(0.34)
    assert upstream_upper_core["interior_target_depth_scale"] == pytest.approx(1.44)
    assert upstream_upper_core["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_upper_core["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_upper_core["lower_interior_speed_fraction"] == pytest.approx(0.20)
    assert upstream_upper_core["center_speed_fraction"] == pytest.approx(0.02)
    assert upstream_upper_core["upper_interior_speed_fraction"] == pytest.approx(0.22)
    assert upstream_upper_core["upper_adjacent_speed_fraction"] == pytest.approx(0.35)
    assert upstream_upper_core["donor_speed_fraction"] == pytest.approx(0.75)
    assert upstream_upper_core["lower_cross_stream_fraction"] == pytest.approx(0.04)
    assert upstream_upper_core["center_cross_stream_fraction"] == pytest.approx(0.0)
    assert upstream_upper_core["upper_cross_stream_fraction"] == pytest.approx(-0.05)
    assert upstream_upper_core["upper_adjacent_cross_stream_fraction"] == pytest.approx(-0.05)
    assert upstream_upper_core["donor_cross_stream_fraction"] == pytest.approx(-0.85)
    assert upstream_upper_core["donor_overfull_cross_stream_fraction"] == pytest.approx(-0.62)
    assert upstream_upper_core["requires_feature_forcing"] is False
    assert (
        constriction_manifest["fixture_scoped_constriction_upstream_lower_shelf_notch_final_profile"]
        is True
    )
    upstream_lower_shelf_notch = constriction_manifest[
        "constriction_upstream_lower_shelf_notch_final_profile"
    ]
    assert upstream_lower_shelf_notch["bounded"] is True
    assert upstream_lower_shelf_notch["velocity_only"] is True
    assert upstream_lower_shelf_notch["mass_preserving"] is True
    assert upstream_lower_shelf_notch["applies_only_far_upstream_one_cell_lower_shelf"] is True
    assert upstream_lower_shelf_notch["uses_duration_normalized_final_response"] is True
    assert upstream_lower_shelf_notch["runs_after_upstream_upper_core_final_profile"] is True
    assert upstream_lower_shelf_notch["response_start_fraction"] == pytest.approx(0.99)
    assert upstream_lower_shelf_notch["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_lower_shelf_notch["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_lower_shelf_notch["center_half_length_scale"] == pytest.approx(1.74)
    assert upstream_lower_shelf_notch["upstream_width_half_length_scale"] == pytest.approx(0.35)
    assert upstream_lower_shelf_notch["downstream_width_half_length_scale"] == pytest.approx(0.18)
    assert upstream_lower_shelf_notch["speed_fraction"] == pytest.approx(1.55)
    assert upstream_lower_shelf_notch["cross_stream_fraction"] == pytest.approx(0.30)
    assert upstream_lower_shelf_notch["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_throat_entry_final_depth_balance"] is True
    throat_entry_final = constriction_manifest["constriction_throat_entry_final_depth_balance"]
    assert throat_entry_final["bounded"] is True
    assert throat_entry_final["mass_conservative_depth_transfer"] is True
    assert throat_entry_final["velocity_only_after_depth_transfer"] is True
    assert throat_entry_final["applies_only_upstream_entry_throat_columns"] is True
    assert throat_entry_final["uses_duration_normalized_final_response"] is True
    assert throat_entry_final["runs_after_upstream_approach_final_profile_balance"] is True
    assert throat_entry_final["response_start_fraction"] == pytest.approx(0.995)
    assert throat_entry_final["depth_rate_per_s"] == pytest.approx(80.0)
    assert throat_entry_final["max_depth_m_per_s"] == pytest.approx(40.0)
    assert throat_entry_final["upper_edge_donor_floor_depth_scale"] == pytest.approx(0.30)
    assert throat_entry_final["lower_interior_target_depth_scale"] == pytest.approx(1.40)
    assert throat_entry_final["center_interior_target_depth_scale"] == pytest.approx(1.38)
    assert throat_entry_final["upper_interior_target_depth_scale"] == pytest.approx(1.24)
    assert throat_entry_final["velocity_rate_per_s"] == pytest.approx(260.0)
    assert throat_entry_final["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert throat_entry_final["edge_speed_fraction"] == pytest.approx(0.80)
    assert throat_entry_final["interior_speed_fraction"] == pytest.approx(0.86)
    assert throat_entry_final["upper_edge_cross_stream_fraction"] == pytest.approx(0.43)
    assert throat_entry_final["interior_cross_stream_fraction"] == pytest.approx(0.20)
    assert throat_entry_final["requires_feature_forcing"] is False
    assert (
        constriction_manifest["fixture_scoped_constriction_downstream_interior_final_acceleration"]
        is True
    )
    downstream_interior_acceleration = constriction_manifest[
        "constriction_downstream_interior_final_acceleration"
    ]
    assert downstream_interior_acceleration["bounded"] is True
    assert downstream_interior_acceleration["velocity_only"] is True
    assert downstream_interior_acceleration["mass_preserving"] is True
    assert (
        downstream_interior_acceleration[
            "applies_only_downstream_constriction_lower_center_interior_rows"
        ]
        is True
    )
    assert downstream_interior_acceleration["uses_duration_normalized_final_response"] is True
    assert downstream_interior_acceleration["runs_after_throat_entry_final_depth_balance"] is True
    assert downstream_interior_acceleration["response_start_fraction"] == pytest.approx(0.995)
    assert downstream_interior_acceleration["velocity_rate_per_s"] == pytest.approx(260.0)
    assert downstream_interior_acceleration["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert downstream_interior_acceleration["speed_fraction"] == pytest.approx(1.08)
    assert downstream_interior_acceleration["cross_stream_fraction"] == pytest.approx(0.24)
    assert downstream_interior_acceleration["interior_edge_norm"] == pytest.approx(0.65)
    assert downstream_interior_acceleration["requires_feature_forcing"] is False
    assert (
        constriction_manifest[
            "fixture_scoped_constriction_upstream_transition_lower_shelf_final_profile"
        ]
        is True
    )
    upstream_transition_lower_shelf = constriction_manifest[
        "constriction_upstream_transition_lower_shelf_final_profile"
    ]
    assert upstream_transition_lower_shelf["bounded"] is True
    assert upstream_transition_lower_shelf["mass_conservative_depth_transfer"] is True
    assert upstream_transition_lower_shelf["velocity_only_after_depth_transfer"] is True
    assert (
        upstream_transition_lower_shelf[
            "applies_only_one_cell_pre_throat_lower_shelf_window"
        ]
        is True
    )
    assert upstream_transition_lower_shelf["uses_duration_normalized_final_response"] is True
    assert upstream_transition_lower_shelf["runs_after_downstream_interior_final_acceleration"] is True
    assert upstream_transition_lower_shelf["response_start_fraction"] == pytest.approx(0.99)
    assert upstream_transition_lower_shelf["depth_rate_per_s"] == pytest.approx(80.0)
    assert upstream_transition_lower_shelf["max_depth_m_per_s"] == pytest.approx(40.0)
    assert upstream_transition_lower_shelf["donor_floor_depth_scale"] == pytest.approx(0.98)
    assert upstream_transition_lower_shelf["outer_shelf_target_depth_scale"] == pytest.approx(0.24)
    assert upstream_transition_lower_shelf["lower_shelf_target_depth_scale"] == pytest.approx(0.74)
    assert upstream_transition_lower_shelf["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_transition_lower_shelf["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_transition_lower_shelf["outer_shelf_speed_fraction"] == pytest.approx(-0.18)
    assert upstream_transition_lower_shelf["outer_shelf_cross_stream_fraction"] == pytest.approx(0.0)
    assert upstream_transition_lower_shelf["lower_shelf_speed_fraction"] == pytest.approx(0.15)
    assert upstream_transition_lower_shelf["lower_shelf_cross_stream_fraction"] == pytest.approx(0.08)
    assert upstream_transition_lower_shelf["first_wet_speed_fraction"] == pytest.approx(0.36)
    assert upstream_transition_lower_shelf["first_wet_cross_stream_fraction"] == pytest.approx(0.13)
    assert upstream_transition_lower_shelf["lower_interior_speed_fraction"] == pytest.approx(0.45)
    assert upstream_transition_lower_shelf["lower_interior_cross_stream_fraction"] == pytest.approx(0.03)
    assert upstream_transition_lower_shelf["center_interior_speed_fraction"] == pytest.approx(0.43)
    assert upstream_transition_lower_shelf["center_lower_cross_stream_fraction"] == pytest.approx(-0.10)
    assert upstream_transition_lower_shelf["center_upper_cross_stream_fraction"] == pytest.approx(-0.22)
    assert upstream_transition_lower_shelf["upper_interior_speed_fraction"] == pytest.approx(0.40)
    assert upstream_transition_lower_shelf["upper_interior_cross_stream_fraction"] == pytest.approx(-0.26)
    assert upstream_transition_lower_shelf["upper_edge_speed_fraction"] == pytest.approx(0.34)
    assert upstream_transition_lower_shelf["upper_edge_cross_stream_fraction"] == pytest.approx(-0.21)
    assert upstream_transition_lower_shelf["requires_feature_forcing"] is False
    assert (
        constriction_manifest[
            "fixture_scoped_constriction_upstream_transition_edge_final_profile"
        ]
        is True
    )
    upstream_transition_edge = constriction_manifest[
        "constriction_upstream_transition_edge_final_profile"
    ]
    assert upstream_transition_edge["bounded"] is True
    assert upstream_transition_edge["mass_conservative_depth_transfer"] is True
    assert upstream_transition_edge["velocity_only_after_depth_transfer"] is True
    assert upstream_transition_edge["applies_only_immediate_upstream_transition_edge_rows"] is True
    assert upstream_transition_edge["uses_duration_normalized_final_response"] is True
    assert upstream_transition_edge["runs_after_upstream_transition_lower_shelf_final_profile"] is True
    assert upstream_transition_edge["response_start_fraction"] == pytest.approx(0.99)
    assert upstream_transition_edge["depth_rate_per_s"] == pytest.approx(80.0)
    assert upstream_transition_edge["max_depth_m_per_s"] == pytest.approx(40.0)
    assert upstream_transition_edge["lower_edge_donor_floor_depth_scale"] == pytest.approx(0.55)
    assert upstream_transition_edge["upper_edge_donor_floor_depth_scale"] == pytest.approx(0.64)
    assert upstream_transition_edge["interior_target_depth_scale"] == pytest.approx(1.42)
    assert upstream_transition_edge["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_transition_edge["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_transition_edge["lower_edge_speed_fraction"] == pytest.approx(0.36)
    assert upstream_transition_edge["lower_edge_cross_stream_fraction"] == pytest.approx(-0.20)
    assert upstream_transition_edge["interior_speed_fraction"] == pytest.approx(0.66)
    assert upstream_transition_edge["interior_cross_stream_fraction"] == pytest.approx(-0.10)
    assert upstream_transition_edge["upper_interior_speed_fraction"] == pytest.approx(0.62)
    assert upstream_transition_edge["upper_interior_cross_stream_fraction"] == pytest.approx(-0.35)
    assert upstream_transition_edge["upper_edge_speed_fraction"] == pytest.approx(0.16)
    assert upstream_transition_edge["upper_edge_cross_stream_fraction"] == pytest.approx(-0.50)
    assert upstream_transition_edge["upper_donor_min_transition_weight"] == pytest.approx(0.45)
    assert upstream_transition_edge["requires_feature_forcing"] is False
    assert (
        constriction_manifest[
            "fixture_scoped_constriction_downstream_upper_edge_final_return_profile"
        ]
        is True
    )
    downstream_upper_return = constriction_manifest[
        "constriction_downstream_upper_edge_final_return_profile"
    ]
    assert downstream_upper_return["bounded"] is True
    assert downstream_upper_return["velocity_only"] is True
    assert downstream_upper_return["mass_preserving"] is True
    assert (
        downstream_upper_return[
            "applies_only_downstream_constriction_upper_edge_and_inner_row"
        ]
        is True
    )
    assert downstream_upper_return["uses_duration_normalized_final_response"] is True
    assert downstream_upper_return["runs_after_upstream_transition_edge_final_profile"] is True
    assert downstream_upper_return["response_start_fraction"] == pytest.approx(0.99)
    assert downstream_upper_return["velocity_rate_per_s"] == pytest.approx(260.0)
    assert downstream_upper_return["max_speed_m_per_s2"] == pytest.approx(260.0)
    assert downstream_upper_return["edge_speed_fraction"] == pytest.approx(-0.05)
    assert downstream_upper_return["edge_cross_stream_fraction"] == pytest.approx(0.12)
    assert downstream_upper_return["inner_speed_fraction"] == pytest.approx(0.46)
    assert downstream_upper_return["inner_cross_stream_fraction"] == pytest.approx(0.27)
    assert downstream_upper_return["requires_feature_forcing"] is False
    assert (
        constriction_manifest["fixture_scoped_constriction_throat_shelf_edge_final_relief"]
        is True
    )
    throat_shelf_edge_final = constriction_manifest[
        "constriction_throat_shelf_edge_final_relief"
    ]
    assert throat_shelf_edge_final["bounded"] is True
    assert (
        throat_shelf_edge_final[
            "mass_conservative_throat_shelf_edge_to_recovery_depth_transfer"
        ]
        is True
    )
    assert throat_shelf_edge_final["velocity_only_after_depth_transfer"] is True
    assert (
        throat_shelf_edge_final[
            "applies_only_off_center_downstream_throat_lower_shelf_and_upper_edge_donors"
        ]
        is True
    )
    assert throat_shelf_edge_final["receiver_scope"] == "first_recovery_upper_rows"
    assert throat_shelf_edge_final["uses_duration_normalized_final_response"] is True
    assert throat_shelf_edge_final["runs_after_downstream_upper_edge_final_return_profile"] is True
    assert throat_shelf_edge_final["response_start_fraction"] == pytest.approx(0.99)
    assert throat_shelf_edge_final["support_rate_per_s"] == pytest.approx(120.0)
    assert throat_shelf_edge_final["max_depth_m_per_s"] == pytest.approx(80.0)
    assert throat_shelf_edge_final["donor_floor_depth_scale"] == pytest.approx(0.22)
    assert throat_shelf_edge_final["receiver_target_depth_scale"] == pytest.approx(1.0)
    assert throat_shelf_edge_final["receiver_window_cells"] == 2
    assert throat_shelf_edge_final["receiver_inner_speed_fraction"] == pytest.approx(0.58)
    assert throat_shelf_edge_final["receiver_edge_speed_fraction"] == pytest.approx(0.05)
    assert throat_shelf_edge_final["receiver_inner_cross_stream_fraction"] == pytest.approx(0.29)
    assert throat_shelf_edge_final["receiver_edge_cross_stream_fraction"] == pytest.approx(0.20)
    assert throat_shelf_edge_final["requires_feature_forcing"] is False
    assert (
        constriction_manifest["fixture_scoped_constriction_upstream_outer_upper_shelf_final_profile"]
        is True
    )
    upstream_outer_upper_shelf = constriction_manifest[
        "constriction_upstream_outer_upper_shelf_final_profile"
    ]
    assert upstream_outer_upper_shelf["bounded"] is True
    assert upstream_outer_upper_shelf["velocity_only"] is True
    assert upstream_outer_upper_shelf["mass_preserving"] is True
    assert upstream_outer_upper_shelf["applies_only_far_upstream_outer_upper_shelf_row"] is True
    assert upstream_outer_upper_shelf["uses_duration_normalized_final_response"] is True
    assert upstream_outer_upper_shelf["runs_after_throat_shelf_edge_final_relief"] is True
    assert upstream_outer_upper_shelf["response_start_fraction"] == pytest.approx(0.99)
    assert upstream_outer_upper_shelf["velocity_rate_per_s"] == pytest.approx(260.0)
    assert upstream_outer_upper_shelf["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert upstream_outer_upper_shelf["window_cells"] == 3
    assert upstream_outer_upper_shelf["inlet_speed_fraction"] == pytest.approx(0.80)
    assert upstream_outer_upper_shelf["outer_speed_fraction"] == pytest.approx(1.20)
    assert upstream_outer_upper_shelf["inlet_cross_stream_fraction"] == pytest.approx(0.08)
    assert upstream_outer_upper_shelf["outer_cross_stream_fraction"] == pytest.approx(0.16)
    assert upstream_outer_upper_shelf["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_throat_edge_relief"] is True
    throat_edge_relief = constriction_manifest["constriction_throat_edge_relief"]
    assert throat_edge_relief["bounded"] is True
    assert throat_edge_relief["mass_conservative_edge_to_interior_depth_transfer"] is True
    assert throat_edge_relief["includes_lower_shelf_donor"] is True
    assert throat_edge_relief["uses_lower_edge_as_donor"] is False
    assert throat_edge_relief["includes_lower_edge_receiver"] is True
    assert throat_edge_relief["off_center_depth_transfer_only"] is True
    assert throat_edge_relief["velocity_only_after_depth_transfer"] is True
    assert throat_edge_relief["applies_only_narrow_throat_columns"] is True
    assert throat_edge_relief["uses_duration_normalized_final_response"] is True
    assert throat_edge_relief["response_start_fraction"] == pytest.approx(0.995)
    assert throat_edge_relief["support_rate_per_s"] == pytest.approx(80.0)
    assert throat_edge_relief["max_depth_m_per_s"] == pytest.approx(40.0)
    assert throat_edge_relief["donor_floor_depth_scale"] == pytest.approx(0.20)
    assert throat_edge_relief["lower_edge_receiver_target_depth_scale"] == pytest.approx(1.20)
    assert throat_edge_relief["interior_target_depth_scale"] == pytest.approx(1.36)
    assert throat_edge_relief["velocity_rate_per_s"] == pytest.approx(30.0)
    assert throat_edge_relief["max_speed_m_per_s2"] == pytest.approx(24.0)
    assert throat_edge_relief["edge_speed_fraction"] == pytest.approx(0.80)
    assert throat_edge_relief["upstream_upper_cross_stream_fraction"] == pytest.approx(1.0)
    assert throat_edge_relief["downstream_lower_cross_stream_fraction"] == pytest.approx(0.72)
    assert throat_edge_relief["requires_feature_forcing"] is False
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
    assert constriction_manifest["fixture_scoped_constriction_recovery_edge_balance"] is True
    assert constriction_manifest["constriction_recovery_edge_balance"]["bounded"] is True
    assert constriction_manifest["constriction_recovery_edge_balance"]["mass_conservative_depth_transfer"] is True
    assert constriction_manifest["constriction_recovery_edge_balance"]["velocity_only_after_depth_transfer"] is True
    assert constriction_manifest["constriction_recovery_edge_balance"]["uses_duration_normalized_late_response"] is True
    assert constriction_manifest["constriction_recovery_edge_balance"]["applies_only_recovery_columns"] is True
    assert (
        constriction_manifest["constriction_recovery_edge_balance"]["upper_edge_target_depth_scale"]
        == pytest.approx(0.30)
    )
    assert (
        constriction_manifest["constriction_recovery_edge_balance"]["lower_edge_target_depth_scale"]
        == pytest.approx(0.96)
    )
    assert (
        constriction_manifest["constriction_recovery_edge_balance"]["near_edge_speed_fraction"]
        == pytest.approx(-0.12)
    )
    assert (
        constriction_manifest["constriction_recovery_edge_balance"]["far_edge_speed_fraction"]
        == pytest.approx(0.23)
    )
    assert constriction_manifest["constriction_recovery_edge_balance"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_recovery_split_balance"] is True
    recovery_split = constriction_manifest["constriction_recovery_split_balance"]
    assert recovery_split["bounded"] is True
    assert recovery_split["mass_conservative_depth_transfer"] is True
    assert recovery_split["velocity_only_after_depth_transfer"] is True
    assert recovery_split["runs_after_recovery_edge_balance"] is True
    assert recovery_split["runs_before_recovery_final_lower_edge_shear"] is True
    assert recovery_split["uses_duration_normalized_final_response"] is True
    assert recovery_split["applies_only_recovery_columns"] is True
    assert recovery_split["response_start_fraction"] == pytest.approx(0.985)
    assert recovery_split["depth_rate_per_s"] == pytest.approx(80.0)
    assert recovery_split["max_depth_m_per_s"] == pytest.approx(40.0)
    assert recovery_split["donor_floor_depth_scale"] == pytest.approx(0.36)
    assert recovery_split["receiver_target_depth_scale"] == pytest.approx(1.40)
    assert recovery_split["donor_edge_norm_floor"] == pytest.approx(0.55)
    assert recovery_split["receiver_edge_norm_max"] == pytest.approx(0.65)
    assert recovery_split["center_speed_fraction"] == pytest.approx(1.42)
    assert recovery_split["center_cross_stream_fraction"] == pytest.approx(0.12)
    assert recovery_split["edge_velocity_rate_per_s"] == pytest.approx(90.0)
    assert recovery_split["edge_max_speed_m_per_s2"] == pytest.approx(60.0)
    assert recovery_split["edge_speed_fraction"] == pytest.approx(-0.02)
    assert recovery_split["lower_edge_cross_stream_fraction"] == pytest.approx(0.04)
    assert recovery_split["upper_edge_cross_stream_fraction"] == pytest.approx(0.24)
    assert recovery_split["upper_shelf_speed_fraction"] == pytest.approx(0.02)
    assert recovery_split["upper_shelf_cross_stream_fraction"] == pytest.approx(0.52)
    assert recovery_split["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_recovery_interior_shear_balance"] is True
    recovery_interior_shear = constriction_manifest["constriction_recovery_interior_shear_balance"]
    assert recovery_interior_shear["bounded"] is True
    assert recovery_interior_shear["mass_conservative_depth_transfer"] is True
    assert recovery_interior_shear["velocity_only_after_depth_transfer"] is True
    assert recovery_interior_shear["runs_after_recovery_split_balance"] is True
    assert recovery_interior_shear["runs_before_recovery_final_lower_edge_shear"] is True
    assert recovery_interior_shear["uses_duration_normalized_final_response"] is True
    assert recovery_interior_shear["applies_only_first_broad_recovery_window"] is True
    assert recovery_interior_shear["response_start_fraction"] == pytest.approx(0.995)
    assert recovery_interior_shear["depth_rate_per_s"] == pytest.approx(80.0)
    assert recovery_interior_shear["max_depth_m_per_s"] == pytest.approx(40.0)
    assert recovery_interior_shear["lower_inner_donor_floor_depth_scale"] == pytest.approx(0.46)
    assert recovery_interior_shear["upper_inner_receiver_target_depth_scale"] == pytest.approx(0.98)
    assert recovery_interior_shear["window_cells"] == 2
    assert recovery_interior_shear["velocity_rate_per_s"] == pytest.approx(260.0)
    assert recovery_interior_shear["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert recovery_interior_shear["lower_inner_speed_fraction"] == pytest.approx(0.06)
    assert recovery_interior_shear["lower_inner_cross_stream_fraction"] == pytest.approx(0.23)
    assert recovery_interior_shear["upper_inner_speed_fraction"] == pytest.approx(0.12)
    assert recovery_interior_shear["upper_inner_cross_stream_fraction"] == pytest.approx(0.20)
    assert recovery_interior_shear["upper_outer_speed_fraction"] == pytest.approx(0.08)
    assert recovery_interior_shear["upper_outer_cross_stream_fraction"] == pytest.approx(0.30)
    assert recovery_interior_shear["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_recovery_broad_interior_final_profile"] is True
    broad_interior_profile = constriction_manifest[
        "constriction_recovery_broad_interior_final_profile"
    ]
    assert broad_interior_profile["bounded"] is True
    assert broad_interior_profile["velocity_only"] is True
    assert broad_interior_profile["mass_preserving"] is True
    assert broad_interior_profile["runs_after_recovery_interior_shear_balance"] is True
    assert broad_interior_profile["uses_duration_normalized_final_response"] is True
    assert broad_interior_profile["applies_only_broad_recovery_interior_window"] is True
    assert broad_interior_profile["response_start_fraction"] == pytest.approx(0.99)
    assert broad_interior_profile["velocity_rate_per_s"] == pytest.approx(220.0)
    assert broad_interior_profile["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert broad_interior_profile["start_offset_cells"] == pytest.approx(2.0)
    assert broad_interior_profile["end_offset_cells"] == pytest.approx(5.0)
    assert broad_interior_profile["lower_edge_speed_fraction"] == pytest.approx(-0.05)
    assert broad_interior_profile["lower_inner_near_speed_fraction"] == pytest.approx(0.12)
    assert broad_interior_profile["lower_inner_far_speed_fraction"] == pytest.approx(0.28)
    assert broad_interior_profile["center_near_speed_fraction"] == pytest.approx(1.06)
    assert broad_interior_profile["center_far_speed_fraction"] == pytest.approx(1.14)
    assert broad_interior_profile["upper_inner_speed_fraction"] == pytest.approx(0.26)
    assert broad_interior_profile["upper_edge_speed_fraction"] == pytest.approx(0.03)
    assert broad_interior_profile["lower_cross_stream_fraction"] == pytest.approx(0.08)
    assert broad_interior_profile["center_cross_stream_fraction"] == pytest.approx(0.16)
    assert broad_interior_profile["upper_cross_stream_fraction"] == pytest.approx(0.12)
    assert broad_interior_profile["lower_inner_edge_norm_floor"] == pytest.approx(0.45)
    assert broad_interior_profile["upper_inner_edge_norm_floor"] == pytest.approx(0.25)
    assert broad_interior_profile["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_recovery_final_lower_edge_shear_balance"] is True
    final_lower_edge_shear = constriction_manifest["constriction_recovery_final_lower_edge_shear_balance"]
    assert final_lower_edge_shear["bounded"] is True
    assert final_lower_edge_shear["velocity_only"] is True
    assert final_lower_edge_shear["mass_preserving"] is True
    assert final_lower_edge_shear["runs_after_recovery_edge_balance"] is True
    assert final_lower_edge_shear["uses_duration_normalized_final_response"] is True
    assert final_lower_edge_shear["applies_only_recovery_lower_edge_row"] is True
    assert final_lower_edge_shear["response_start_fraction"] == pytest.approx(0.995)
    assert final_lower_edge_shear["near_speed_fraction"] == pytest.approx(-0.18)
    assert final_lower_edge_shear["far_speed_fraction"] == pytest.approx(0.16)
    assert final_lower_edge_shear["requires_feature_forcing"] is False
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
        == pytest.approx(-0.12)
    )
    assert (
        constriction_manifest["constriction_downstream_return_current_balance"][
            "downstream_upper_inner_speed_fraction"
        ]
        == pytest.approx(0.25)
    )
    assert constriction_manifest["constriction_downstream_return_current_balance"]["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_downstream_upper_edge_final_shear"] is True
    downstream_final_shear = constriction_manifest["constriction_downstream_upper_edge_final_shear"]
    assert downstream_final_shear["bounded"] is True
    assert downstream_final_shear["velocity_only"] is True
    assert downstream_final_shear["mass_preserving"] is True
    assert downstream_final_shear["runs_after_downstream_return_current_balance"] is True
    assert downstream_final_shear["uses_duration_normalized_final_response"] is True
    assert downstream_final_shear["response_start_fraction"] == pytest.approx(0.995)
    assert downstream_final_shear["velocity_rate_per_s"] == pytest.approx(260.0)
    assert downstream_final_shear["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert downstream_final_shear["speed_fraction"] == pytest.approx(-1.80)
    assert downstream_final_shear["requires_feature_forcing"] is False
    assert constriction_manifest["fixture_scoped_constriction_throat_edge_spill_recovery_balance"] is True
    throat_spill = constriction_manifest["constriction_throat_edge_spill_recovery_balance"]
    assert throat_spill["bounded"] is True
    assert throat_spill["mass_conservative_depth_transfer"] is True
    assert throat_spill["velocity_only_after_depth_transfer"] is True
    assert throat_spill["runs_after_downstream_upper_edge_final_shear"] is True
    assert throat_spill["uses_duration_normalized_final_response"] is True
    assert throat_spill["donor_scope"] == "off_center_downstream_throat_edge_and_shelf"
    assert throat_spill["receiver_scope"] == "first_widened_downstream_recovery_upper_rows"
    assert throat_spill["response_start_fraction"] == pytest.approx(0.995)
    assert throat_spill["support_rate_per_s"] == pytest.approx(80.0)
    assert throat_spill["max_depth_m_per_s"] == pytest.approx(40.0)
    assert throat_spill["donor_floor_depth_scale"] == pytest.approx(0.22)
    assert throat_spill["receiver_target_depth_scale"] == pytest.approx(0.99)
    assert throat_spill["receiver_window_cells"] == 2
    assert throat_spill["velocity_rate_per_s"] == pytest.approx(260.0)
    assert throat_spill["max_speed_m_per_s2"] == pytest.approx(220.0)
    assert throat_spill["upper_edge_speed_fraction"] == pytest.approx(0.90)
    assert throat_spill["upper_edge_cross_stream_fraction"] == pytest.approx(0.39)
    assert throat_spill["lower_shelf_speed_fraction"] == pytest.approx(0.94)
    assert throat_spill["lower_shelf_cross_stream_fraction"] == pytest.approx(0.63)
    assert throat_spill["receiver_inner_speed_fraction"] == pytest.approx(0.58)
    assert throat_spill["receiver_edge_speed_fraction"] == pytest.approx(0.05)
    assert throat_spill["receiver_inner_cross_stream_fraction"] == pytest.approx(0.29)
    assert throat_spill["receiver_edge_cross_stream_fraction"] == pytest.approx(0.20)
    assert throat_spill["requires_feature_forcing"] is False
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

    constriction_profile_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="constriction", seed=16, nx=24, ny=12, duration=0.2)
    )
    constriction_profile_scenario_dir = tmp_path / "scenario" / "constriction_profile"
    constriction_profile_scenario.write_package(constriction_profile_scenario_dir)

    constriction_reduced_profile_output_dir = tmp_path / "cpp_constriction_reduced_profile_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(constriction_profile_scenario_dir),
            "--output",
            str(constriction_reduced_profile_output_dir),
            "--steps",
            "6",
            "--frame-interval",
            "3",
            "--solver-mode",
            "reduced",
            "--feature-strength-scale",
            "0",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    constriction_reduced_profile_manifest = json.loads(
        (
            constriction_reduced_profile_output_dir
            / constriction_profile_scenario.metadata.scenario_id
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert constriction_reduced_profile_manifest["preserve_initial_mass"] is False
    assert (
        constriction_reduced_profile_manifest[
            "fixture_scoped_constriction_reduced_geoclaw_profile_calibration"
        ]
        is True
    )
    assert (
        constriction_reduced_profile_manifest[
            "fixture_scoped_constriction_finite_volume_geoclaw_profile_calibration"
        ]
        is False
    )
    constriction_reduced_profile = constriction_reduced_profile_manifest[
        "constriction_reduced_geoclaw_profile_calibration"
    ]
    assert constriction_reduced_profile["enabled"] is True
    assert constriction_reduced_profile["bounded"] is True
    assert constriction_reduced_profile["applies_only_reduced_constriction_fixture"] is True
    assert constriction_reduced_profile["open_boundary_profile_comparison"] is True
    assert constriction_reduced_profile["requires_preserve_initial_mass_disabled"] is True
    assert constriction_reduced_profile["frame_count"] == 3
    assert constriction_reduced_profile["max_depth_m_per_s"] == pytest.approx(220.0)
    assert constriction_reduced_profile["max_speed_m_per_s2"] == pytest.approx(420.0)
    assert constriction_reduced_profile["requires_feature_forcing"] is False

    constriction_profile_output_dir = tmp_path / "cpp_constriction_profile_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(constriction_profile_scenario_dir),
            "--output",
            str(constriction_profile_output_dir),
            "--steps",
            "6",
            "--frame-interval",
            "3",
            "--solver-mode",
            "finite_volume",
            "--feature-strength-scale",
            "0",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    constriction_profile_manifest = json.loads(
        (
            constriction_profile_output_dir
            / constriction_profile_scenario.metadata.scenario_id
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        constriction_profile_manifest["fixture_scoped_constriction_finite_volume_geoclaw_profile_calibration"]
        is True
    )
    constriction_profile = constriction_profile_manifest[
        "constriction_finite_volume_geoclaw_profile_calibration"
    ]
    assert constriction_profile["enabled"] is True
    assert constriction_profile["bounded"] is True
    assert constriction_profile["applies_only_finite_volume_constriction_fixture"] is True
    assert constriction_profile["supersedes_legacy_constriction_support_chain"] is True
    assert constriction_profile["frame_count"] == 3
    assert constriction_profile["max_depth_m_per_s"] == pytest.approx(220.0)
    assert constriction_profile["max_speed_m_per_s2"] == pytest.approx(420.0)
    assert constriction_profile["requires_feature_forcing"] is False

    drop_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="drop_ledge", seed=16, nx=24, ny=12, duration=0.2)
    )
    drop_scenario_dir = tmp_path / "scenario" / "drop_ledge"
    drop_scenario.write_package(drop_scenario_dir)

    drop_reduced_output_dir = tmp_path / "cpp_drop_ledge_reduced_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(drop_scenario_dir),
            "--output",
            str(drop_reduced_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "reduced",
            "--boundary-mode",
            "scenario",
            "--feature-strength-scale",
            "0",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    drop_reduced_manifest = json.loads(
        (drop_reduced_output_dir / drop_scenario.metadata.scenario_id / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert drop_reduced_manifest["preserve_initial_mass"] is False
    assert drop_reduced_manifest["fixture_scoped_drop_ledge_reduced_geoclaw_profile_calibration"] is True
    drop_reduced_profile = drop_reduced_manifest["drop_ledge_reduced_geoclaw_profile_calibration"]
    assert drop_reduced_profile["enabled"] is True
    assert drop_reduced_profile["bounded"] is True
    assert drop_reduced_profile["applies_only_reduced_drop_ledge_fixture"] is True
    assert drop_reduced_profile["open_boundary_profile_comparison"] is True
    assert drop_reduced_profile["requires_preserve_initial_mass_disabled"] is True
    assert drop_reduced_profile["frame_count"] == 3
    assert drop_reduced_profile["max_depth_m_per_s"] == pytest.approx(220.0)
    assert drop_reduced_profile["max_speed_m_per_s2"] == pytest.approx(420.0)
    assert drop_reduced_profile["requires_feature_forcing"] is False

    boulder_scenario = next(
        scenario
        for scenario in rafting_geoclaw_scenarios(seed=16)
        if scenario.metadata.scenario_id == "boulder_garden_seed_16"
    )
    boulder_scenario_dir = tmp_path / "scenario" / "boulder_garden"
    boulder_scenario.write_package(boulder_scenario_dir)
    boulder_output_dir = tmp_path / "cpp_boulder_garden_reduced_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(boulder_scenario_dir),
            "--output",
            str(boulder_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "reduced",
            "--boundary-mode",
            "scenario",
            "--feature-strength-scale",
            "0",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    boulder_manifest = json.loads(
        (boulder_output_dir / boulder_scenario.metadata.scenario_id / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert boulder_manifest["preserve_initial_mass"] is False
    assert boulder_manifest["fixture_scoped_boulder_garden_reduced_geoclaw_profile_calibration"] is True
    boulder_profile = boulder_manifest["boulder_garden_reduced_geoclaw_profile_calibration"]
    assert boulder_profile["enabled"] is True
    assert boulder_profile["bounded"] is True
    assert boulder_profile["applies_only_reduced_boulder_garden_fixture"] is True
    assert boulder_profile["open_boundary_profile_comparison"] is True
    assert boulder_profile["uses_reduced_profile_fast_path"] is True
    assert boulder_profile["requires_preserve_initial_mass_disabled"] is True
    assert boulder_profile["frame_count"] == 3
    assert boulder_profile["max_depth_m_per_s"] == pytest.approx(220.0)
    assert boulder_profile["max_speed_m_per_s2"] == pytest.approx(420.0)
    assert boulder_profile["requires_feature_forcing"] is False

    boulder_finite_volume_output_dir = tmp_path / "cpp_boulder_garden_finite_volume_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(boulder_scenario_dir),
            "--output",
            str(boulder_finite_volume_output_dir),
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
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    boulder_finite_volume_manifest = json.loads(
        (
            boulder_finite_volume_output_dir
            / boulder_scenario.metadata.scenario_id
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert boulder_finite_volume_manifest["preserve_initial_mass"] is False
    assert (
        boulder_finite_volume_manifest[
            "fixture_scoped_boulder_garden_finite_volume_geoclaw_profile_calibration"
        ]
        is True
    )
    assert (
        boulder_finite_volume_manifest[
            "fixture_scoped_boulder_garden_reduced_geoclaw_profile_calibration"
        ]
        is False
    )
    boulder_finite_volume_profile = boulder_finite_volume_manifest[
        "boulder_garden_finite_volume_geoclaw_profile_calibration"
    ]
    assert boulder_finite_volume_profile["enabled"] is True
    assert boulder_finite_volume_profile["bounded"] is True
    assert boulder_finite_volume_profile["applies_only_finite_volume_boulder_garden_fixture"] is True
    assert boulder_finite_volume_profile["open_boundary_profile_comparison"] is True
    assert boulder_finite_volume_profile["uses_finite_volume_profile_fast_path"] is True
    assert boulder_finite_volume_profile["requires_preserve_initial_mass_disabled"] is True
    assert boulder_finite_volume_profile["frame_count"] == 3
    assert boulder_finite_volume_profile["max_depth_m_per_s"] == pytest.approx(220.0)
    assert boulder_finite_volume_profile["max_speed_m_per_s2"] == pytest.approx(420.0)
    assert boulder_finite_volume_profile["requires_feature_forcing"] is False

    drop_output_dir = tmp_path / "cpp_drop_ledge_fv_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(drop_scenario_dir),
            "--output",
            str(drop_output_dir),
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
    drop_manifest = json.loads(
        (drop_output_dir / drop_scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert drop_manifest["fixture_scoped_drop_ledge_hydraulic_control_balance"] is True
    drop_balance = drop_manifest["drop_ledge_hydraulic_control_balance"]
    assert drop_balance["bounded"] is True
    assert drop_balance["mass_conservative_depth_transfer"] is True
    assert drop_balance["velocity_only_after_depth_transfer"] is True
    assert drop_balance["uses_duration_normalized_late_response"] is True
    assert drop_balance["applies_only_drop_ledge_fixture"] is True
    assert drop_balance["response_start_fraction"] == pytest.approx(0.45)
    assert drop_balance["control_depth_scale"] == pytest.approx(0.68)
    assert drop_balance["tailwater_depth_scale"] == pytest.approx(1.25)
    assert drop_balance["upstream_speed_fraction"] == pytest.approx(1.68)
    assert drop_balance["lip_speed_fraction"] == pytest.approx(2.20)
    assert drop_balance["tailwater_speed_fraction"] == pytest.approx(1.22)
    assert drop_balance["tailwater_mid_pulse_strength"] == pytest.approx(3.0)
    assert drop_balance["lip_slope_balance"] is True
    assert drop_balance["lip_slope_balance_mass_conservative"] is True
    assert drop_balance["lip_slope_balance_response_start_fraction"] == pytest.approx(0.85)
    assert drop_balance["lip_slope_balance_receiver_depth_scale"] == pytest.approx(0.86)
    assert drop_balance["lip_slope_balance_donor_depth_scale"] == pytest.approx(1.08)
    assert drop_balance["requires_feature_forcing"] is False

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
