import json

import numpy as np

from raftsim.analytic_fixtures import (
    ANALYTIC_FIXTURE_IDS,
    ANALYTIC_FIXTURE_MANIFEST_ID,
    build_analytic_fixture,
    build_analytic_fixture_suite,
    write_analytic_fixture_suite,
)
from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.schema_versions import ANALYTIC_FIXTURE_MANIFEST_SCHEMA_VERSION


def test_analytic_fixture_suite_covers_first_manual_swashes_style_set():
    fixtures = build_analytic_fixture_suite()

    assert tuple(fixture.fixture_id for fixture in fixtures) == ANALYTIC_FIXTURE_IDS
    assert len(fixtures) == 7
    assert {fixture.manifest_entry["scenario_kind"] for fixture in fixtures} == {
        "lake_at_rest",
        "sloping_channel",
        "wet_dry_shoreline",
        "bed_step",
        "dam_break_bore",
        "hydraulic_jump",
        "transcritical_bump",
    }
    for fixture in fixtures:
        assert fixture.scenario.validate().passed
        assert fixture.manifest_entry["provenance"]["external_data_vendored"] is False
        assert fixture.reference["schema_version"] == "raftsim.analytic_reference.v0"
        assert {"bed", "depth", "eta", "u", "v", "hu", "hv", "wet"}.issubset(fixture.reference_fields)


def test_write_analytic_fixture_suite_outputs_manifest_references_and_scenarios(tmp_path):
    manifest_path = write_analytic_fixture_suite(tmp_path / "analytic_fixtures")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == ANALYTIC_FIXTURE_MANIFEST_SCHEMA_VERSION
    assert manifest["manifest_id"] == ANALYTIC_FIXTURE_MANIFEST_ID
    assert manifest["license_policy"]["external_data_vendored"] is False
    assert len(manifest["fixtures"]) == len(ANALYTIC_FIXTURE_IDS)

    for entry in manifest["fixtures"]:
        outputs = entry["outputs"]
        scenario_dir = manifest_path.parent / outputs["scenario_package"]
        reference_path = manifest_path.parent / outputs["analytic_reference"]
        fields_path = manifest_path.parent / outputs["analytic_fields"]
        loaded = read_scenario2_5d_package(scenario_dir)
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        with np.load(fields_path) as fields:
            assert fields["depth"].shape == loaded.grid.shape
            np.testing.assert_allclose(fields["eta"], loaded.initial_state.eta)
        assert loaded.metadata.provenance["analytic_fixture_id"] == entry["fixture_id"]
        assert reference["fixture_id"] == entry["fixture_id"]


def test_analytic_fixture_semantics_are_encoded_from_equations():
    lake = build_analytic_fixture("lake_at_rest_balance")
    np.testing.assert_allclose(lake.scenario.initial_state.eta, lake.scenario.initial_state.eta[0, 0])
    np.testing.assert_allclose(lake.scenario.initial_state.u, 0.0)
    np.testing.assert_allclose(lake.scenario.initial_state.v, 0.0)

    slope = build_analytic_fixture("sloping_channel_friction")
    slope_params = slope.reference["parameters"]
    expected_velocity = (1.0 / slope_params["manning_n"]) * (
        slope_params["normal_depth"] ** (2.0 / 3.0)
    ) * np.sqrt(slope_params["slope"])
    np.testing.assert_allclose(slope.scenario.initial_state.u, expected_velocity)

    shoreline = build_analytic_fixture("wet_dry_shoreline")
    assert shoreline.scenario.initial_state.wet.any()
    assert (~shoreline.scenario.initial_state.wet).any()

    step = build_analytic_fixture("bed_step_subcritical")
    step_params = step.reference["parameters"]
    assert step_params["downstream_depth"] < step_params["upstream_depth"]
    assert step_params["downstream_velocity"] > step_params["upstream_velocity"]

    jump = build_analytic_fixture("hydraulic_jump_conjugate_depth")
    jump_params = jump.reference["parameters"]
    expected_ratio = 0.5 * (np.sqrt(1.0 + 8.0 * jump_params["upstream_froude"] ** 2) - 1.0)
    np.testing.assert_allclose(jump_params["downstream_depth"] / jump_params["upstream_depth"], expected_ratio)
    assert jump_params["downstream_froude"] < 1.0

    bump = build_analytic_fixture("transcritical_bump")
    bump_diag = bump.reference["diagnostics"]
    assert bump_diag["upstream_froude"] < 1.0
    assert bump_diag["downstream_froude"] > 1.0
    assert 0.75 < bump_diag["crest_froude"] < 1.25
