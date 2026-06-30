"""Hand-authored analytic shallow-water fixtures for Milestone 17."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .scenario2_5d import (
    BoundaryCondition2_5D,
    Feature2_5D,
    GridSpec2_5D,
    InitialWaterState2_5D,
    Probe2_5D,
    RaftParameters2_5D,
    Scenario2_5D,
    ScenarioMetadata2_5D,
)
from .schema_versions import ANALYTIC_FIXTURE_MANIFEST_SCHEMA_VERSION

ANALYTIC_FIXTURE_SET_VERSION = "manual_swashes_style_seed_v0"
ANALYTIC_FIXTURE_MANIFEST_ID = "milestone17_analytic_fixtures"
ANALYTIC_FIXTURE_GENERATED_AT = "2026-06-30T00:00:00Z"
ANALYTIC_REFERENCE_SCHEMA_VERSION = "raftsim.analytic_reference.v0"
GRAVITY_MPS2 = 9.81

ANALYTIC_FIXTURE_IDS = (
    "lake_at_rest_balance",
    "sloping_channel_friction",
    "wet_dry_shoreline",
    "bed_step_subcritical",
    "dam_break_bore",
    "hydraulic_jump_conjugate_depth",
    "transcritical_bump",
)


@dataclass(frozen=True, slots=True)
class AnalyticFixture:
    """One generated analytic fixture plus reference metadata."""

    fixture_id: str
    scenario: Scenario2_5D
    reference: dict[str, object]
    reference_fields: dict[str, np.ndarray]
    manifest_entry: dict[str, object]


def build_analytic_fixture_suite() -> tuple[AnalyticFixture, ...]:
    """Build the first manually encoded SWASHES-style fixture set."""

    return tuple(_BUILDERS[fixture_id]() for fixture_id in ANALYTIC_FIXTURE_IDS)


def write_analytic_fixture_suite(output_dir: str | Path) -> Path:
    """Write scenario packages, analytic references, and the suite manifest."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict[str, object]] = []

    for fixture in build_analytic_fixture_suite():
        fixture_root = root / "fixtures" / fixture.fixture_id
        scenario_dir = fixture_root / "scenario"
        fixture.scenario.write_package(scenario_dir)
        np.savez_compressed(fixture_root / "reference_fields.npz", **fixture.reference_fields)

        reference = dict(fixture.reference)
        reference["field_files"] = {"reference_fields": "reference_fields.npz"}
        _write_json(fixture_root / "reference.json", reference)
        manifest_entries.append(fixture.manifest_entry)

    manifest = {
        "schema_version": ANALYTIC_FIXTURE_MANIFEST_SCHEMA_VERSION,
        "manifest_id": ANALYTIC_FIXTURE_MANIFEST_ID,
        "fixture_set_version": ANALYTIC_FIXTURE_SET_VERSION,
        "generator": "raftsim.analytic_fixtures",
        "generated_at": ANALYTIC_FIXTURE_GENERATED_AT,
        "license_policy": {
            "external_data_vendored": False,
            "notes": "Fixtures are hand-authored from shallow-water benchmark equations and notes. No external SWASHES data or code is vendored.",
        },
        "fixtures": manifest_entries,
    }
    return _write_json(root / "manifest.json", manifest)


def build_analytic_fixture(fixture_id: str) -> AnalyticFixture:
    """Build one fixture by id."""

    try:
        return _BUILDERS[fixture_id]()
    except KeyError as exc:
        raise ValueError(f"Unknown analytic fixture: {fixture_id}") from exc


def _lake_at_rest_balance() -> AnalyticFixture:
    grid = _grid()
    x, y = grid.meshgrid()
    x_span = max(float(x.max() - x.min()), 1.0)
    y_span = max(float(y.max() - y.min()), 1.0)
    bed = 0.12 * np.sin(2.0 * math.pi * x / x_span) + 0.06 * np.cos(2.0 * math.pi * y / y_span)
    eta = 1.35
    depth = eta - bed
    u = np.zeros(grid.shape, dtype=np.float64)
    v = np.zeros(grid.shape, dtype=np.float64)
    scenario = _scenario(
        fixture_id="lake_at_rest_balance",
        title="Lake At Rest Over Uneven Bed",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.0,
        boundaries=_wall_boundaries(),
        description="Well-balanced still water over a non-flat bed.",
    )
    reference = _reference(
        fixture_id="lake_at_rest_balance",
        summary="Free surface eta is spatially constant and velocity is zero.",
        parameters={"eta": eta},
        diagnostics={"eta_min": eta, "eta_max": eta, "speed_linf": 0.0},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Lake At Rest Over Uneven Bed",
        benchmark_family="well-balanced shallow-water steady state",
        scenario_kind="lake_at_rest",
        source_note="Derived from eta = h + z_b constant with zero velocity.",
        equations=("eta(x,y) = h(x,y) + z_b(x,y) = constant", "u(x,y) = 0", "v(x,y) = 0"),
        expected_summary="A well-balanced solver keeps the free surface flat and velocity near zero over a non-flat bed.",
        exact_fields=("eta", "u", "v"),
        approximate_fields=("h",),
        failure_modes=("spurious bed-slope velocity", "free-surface drift", "negative depth near bed peaks"),
        tolerance_tier="well_balanced",
        metrics=(
            _metric("surface_linf", "eta", "linf", 1.0e-9, "m"),
            _metric("speed_linf", "speed", "linf", 1.0e-9, "m/s"),
        ),
    )


def _sloping_channel_friction() -> AnalyticFixture:
    grid = _grid()
    x, _ = grid.meshgrid()
    slope = 0.0025
    roughness = 0.035
    depth_value = 1.1
    velocity_value = (1.0 / roughness) * (depth_value ** (2.0 / 3.0)) * math.sqrt(slope)
    bed = -slope * x
    depth = np.full(grid.shape, depth_value, dtype=np.float64)
    u = np.full(grid.shape, velocity_value, dtype=np.float64)
    v = np.zeros(grid.shape, dtype=np.float64)
    scenario = _scenario(
        fixture_id="sloping_channel_friction",
        title="Sloping Manning Channel",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=roughness,
        boundaries=_channel_boundaries(depth_value, velocity_value),
        description="Uniform wide-channel flow where bed slope and Manning friction balance.",
    )
    reference = _reference(
        fixture_id="sloping_channel_friction",
        summary="Wide-channel Manning velocity is constant for a uniform depth and bed slope.",
        parameters={
            "manning_n": roughness,
            "slope": slope,
            "normal_depth": depth_value,
            "normal_velocity": velocity_value,
            "unit_discharge": depth_value * velocity_value,
        },
        diagnostics={"velocity_linf": velocity_value, "bed_drop": float(bed[:, 0].mean() - bed[:, -1].mean())},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Sloping Manning Channel",
        benchmark_family="steady uniform flow with Manning friction",
        scenario_kind="sloping_channel",
        source_note="Derived from the wide-channel Manning relation u = h^(2/3) sqrt(S) / n.",
        equations=("u = h^(2/3) sqrt(S) / n", "q = h u", "z_b(x) = -S x"),
        expected_summary="A friction/source-balanced solver preserves uniform velocity and normal depth down the slope.",
        exact_fields=("h", "u", "v"),
        approximate_fields=("eta", "hu"),
        failure_modes=("roughness/source imbalance", "velocity drift", "mass flux drift"),
        tolerance_tier="analytic",
        metrics=(
            _metric("normal_velocity_linf", "u", "linf", 2.5e-2, "m/s"),
            _metric("unit_discharge_linf", "hu", "linf", 3.0e-2, "m2/s"),
        ),
    )


def _wet_dry_shoreline() -> AnalyticFixture:
    grid = _grid()
    _, y = grid.meshgrid()
    beach_slope = 0.08
    eta = 0.75
    y_min = float(y.min())
    bed = beach_slope * (y - y_min)
    depth = np.maximum(eta - bed, 0.0)
    u = np.zeros(grid.shape, dtype=np.float64)
    v = np.zeros(grid.shape, dtype=np.float64)
    shoreline_y = y_min + eta / beach_slope
    features = (
        Feature2_5D(
            kind="shallow",
            center=(grid.center[0], shoreline_y),
            radius=grid.dy,
            length=float((grid.nx - 1) * grid.dx),
            width=2.0 * grid.dy,
            metadata={"analytic_fixture_role": "exact_wet_dry_line"},
        ),
    )
    scenario = _scenario(
        fixture_id="wet_dry_shoreline",
        title="Planar Wet/Dry Shoreline",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.0,
        boundaries=_shoreline_boundaries(),
        description="Still-water shoreline on a planar beach with exact wet/dry split.",
        features=features,
    )
    reference = _reference(
        fixture_id="wet_dry_shoreline",
        summary="Cells with z_b below eta are wet; cells above eta are dry.",
        parameters={"eta": eta, "beach_slope": beach_slope, "shoreline_y": shoreline_y},
        diagnostics={"wet_cell_count": int(np.count_nonzero(depth > 1.0e-6)), "dry_cell_count": int(np.count_nonzero(depth <= 1.0e-6))},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Planar Wet/Dry Shoreline",
        benchmark_family="wet/dry shoreline balance",
        scenario_kind="wet_dry_shoreline",
        source_note="Derived from h = max(eta - z_b, 0) on a planar beach.",
        equations=("z_b(y) = S(y - y_min)", "h(y) = max(eta - z_b(y), 0)", "wet iff h > dry_tolerance"),
        expected_summary="The shoreline stays at the analytic eta/bed intersection without wetting dry high ground.",
        exact_fields=("h", "eta", "wet"),
        approximate_fields=("shoreline_position",),
        failure_modes=("dry-cell leakage", "negative depth", "shoreline drift"),
        tolerance_tier="well_balanced",
        metrics=(
            _metric("wet_mask_mismatch_count", "wet", "count", 0.0, "cells"),
            _metric("shoreline_position_abs", "shoreline_y", "abs", 0.5 * grid.dy, "m"),
        ),
    )


def _bed_step_subcritical() -> AnalyticFixture:
    grid = _grid()
    x, _ = grid.meshgrid()
    step_x = grid.center[0]
    step_height = 0.22
    upstream_depth = 1.2
    unit_discharge = 0.72
    upstream_velocity = unit_discharge / upstream_depth
    total_head = upstream_depth + (unit_discharge**2) / (2.0 * GRAVITY_MPS2 * upstream_depth**2)
    downstream_depth = _specific_energy_depth(total_head, step_height, unit_discharge, branch="subcritical")
    downstream_velocity = unit_discharge / downstream_depth
    bed = np.where(x >= step_x, step_height, 0.0)
    depth = np.where(x >= step_x, downstream_depth, upstream_depth)
    u = np.where(x >= step_x, downstream_velocity, upstream_velocity)
    v = np.zeros(grid.shape, dtype=np.float64)
    features = (
        Feature2_5D(
            kind="ledge",
            center=(step_x, grid.center[1]),
            radius=0.0,
            strength=step_height,
            length=float((grid.ny - 1) * grid.dy),
            metadata={"analytic_fixture_role": "bed_step"},
        ),
    )
    scenario = _scenario(
        fixture_id="bed_step_subcritical",
        title="Subcritical Bed Step",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.0,
        boundaries=_channel_boundaries(upstream_depth, upstream_velocity),
        description="Subcritical steady flow over an upward bed step from specific-energy balance.",
        features=features,
    )
    reference = _reference(
        fixture_id="bed_step_subcritical",
        summary="Specific energy and unit discharge define upstream/downstream subcritical depths.",
        parameters={
            "step_height": step_height,
            "unit_discharge": unit_discharge,
            "upstream_depth": upstream_depth,
            "downstream_depth": downstream_depth,
            "upstream_velocity": upstream_velocity,
            "downstream_velocity": downstream_velocity,
            "total_head": total_head,
        },
        diagnostics={"specific_energy_residual": 0.0},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Subcritical Bed Step",
        benchmark_family="steady flow over bed step",
        scenario_kind="bed_step",
        source_note="Derived from steady specific-energy balance for a rectangular channel.",
        equations=("H = z_b + h + q^2/(2 g h^2)", "q = h u", "H_upstream = H_downstream"),
        expected_summary="Subcritical flow shallows and accelerates over the raised bed without violating energy balance.",
        exact_fields=("h", "u", "hu"),
        approximate_fields=("eta",),
        failure_modes=("wrong depth branch", "spurious jump at step", "unit discharge drift"),
        tolerance_tier="analytic",
        metrics=(
            _metric("depth_linf", "h", "linf", 4.0e-2, "m"),
            _metric("specific_energy_abs", "specific_energy", "abs", 5.0e-2, "m"),
        ),
    )


def _dam_break_bore() -> AnalyticFixture:
    grid = _grid()
    x, _ = grid.meshgrid()
    split_x = grid.center[0]
    left_depth = 2.0
    right_depth = 0.35
    bed = np.zeros(grid.shape, dtype=np.float64)
    depth = np.where(x < split_x, left_depth, right_depth)
    u = np.zeros(grid.shape, dtype=np.float64)
    v = np.zeros(grid.shape, dtype=np.float64)
    features = (
        Feature2_5D(
            kind="ledge",
            center=(split_x, grid.center[1]),
            radius=0.0,
            length=float((grid.ny - 1) * grid.dy),
            metadata={"analytic_fixture_role": "riemann_depth_discontinuity"},
        ),
    )
    scenario = _scenario(
        fixture_id="dam_break_bore",
        title="Dam-Break Bore Riemann Initial State",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.0,
        boundaries=_wall_boundaries(),
        description="Still-water Riemann problem with high left depth and shallow right depth.",
        features=features,
    )
    reference = _reference(
        fixture_id="dam_break_bore",
        summary="A left rarefaction and right-moving bore should form from the initial discontinuity.",
        parameters={
            "left_depth": left_depth,
            "right_depth": right_depth,
            "left_gravity_wave_speed": math.sqrt(GRAVITY_MPS2 * left_depth),
            "right_gravity_wave_speed": math.sqrt(GRAVITY_MPS2 * right_depth),
        },
        diagnostics={"left_total_depth": float(depth[:, : grid.nx // 2].sum()), "right_total_depth": float(depth[:, grid.nx // 2 :].sum())},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Dam-Break Bore Riemann Initial State",
        benchmark_family="shallow-water Riemann dam-break",
        scenario_kind="dam_break_bore",
        source_note="Hand-authored left/right still-water states from the classic shallow-water dam-break Riemann problem.",
        equations=("h_L > h_R", "u_L = u_R = 0", "c = sqrt(g h)"),
        expected_summary="The initial state should evolve into a left rarefaction and right-moving bore without negative depth.",
        exact_fields=("initial_h", "initial_u", "initial_v"),
        approximate_fields=("bore_speed", "rarefaction_fan"),
        failure_modes=("negative depth at discontinuity", "wrong wave direction", "excessive mass drift"),
        tolerance_tier="diagnostic",
        metrics=(
            _metric("initial_depth_linf", "h", "linf", 1.0e-12, "m"),
            _metric("mass_relative_drift", "mass", "relative", 5.0e-4, "ratio"),
        ),
    )


def _hydraulic_jump_conjugate_depth() -> AnalyticFixture:
    grid = _grid()
    x, _ = grid.meshgrid()
    jump_x = grid.center[0]
    upstream_depth = 0.45
    upstream_froude = 3.0
    upstream_velocity = upstream_froude * math.sqrt(GRAVITY_MPS2 * upstream_depth)
    downstream_depth = 0.5 * upstream_depth * (math.sqrt(1.0 + 8.0 * upstream_froude**2) - 1.0)
    unit_discharge = upstream_depth * upstream_velocity
    downstream_velocity = unit_discharge / downstream_depth
    bed = np.zeros(grid.shape, dtype=np.float64)
    depth = np.where(x < jump_x, upstream_depth, downstream_depth)
    u = np.where(x < jump_x, upstream_velocity, downstream_velocity)
    v = np.zeros(grid.shape, dtype=np.float64)
    features = (
        Feature2_5D(
            kind="wave_train",
            center=(jump_x, grid.center[1]),
            radius=float(grid.dy * 2.0),
            strength=upstream_froude,
            length=float(grid.dx * 6.0),
            width=float((grid.ny - 1) * grid.dy),
            metadata={"analytic_fixture_role": "hydraulic_jump"},
        ),
    )
    scenario = _scenario(
        fixture_id="hydraulic_jump_conjugate_depth",
        title="Hydraulic Jump Conjugate Depth",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.02,
        boundaries=_channel_boundaries(upstream_depth, upstream_velocity),
        description="Rectangular-channel hydraulic jump using conjugate depth relation.",
        features=features,
    )
    reference = _reference(
        fixture_id="hydraulic_jump_conjugate_depth",
        summary="Supercritical upstream flow transitions to the conjugate subcritical downstream depth.",
        parameters={
            "upstream_depth": upstream_depth,
            "downstream_depth": downstream_depth,
            "upstream_velocity": upstream_velocity,
            "downstream_velocity": downstream_velocity,
            "upstream_froude": upstream_froude,
            "downstream_froude": downstream_velocity / math.sqrt(GRAVITY_MPS2 * downstream_depth),
            "unit_discharge": unit_discharge,
        },
        diagnostics={"depth_ratio": downstream_depth / upstream_depth},
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Hydraulic Jump Conjugate Depth",
        benchmark_family="hydraulic jump conjugate depths",
        scenario_kind="hydraulic_jump",
        source_note="Derived from the rectangular-channel conjugate-depth relation h2/h1 = 0.5(sqrt(1 + 8 Fr1^2) - 1).",
        equations=("Fr1 = u1 / sqrt(g h1)", "h2/h1 = 0.5(sqrt(1 + 8 Fr1^2) - 1)", "q = h1 u1 = h2 u2"),
        expected_summary="The solver should preserve a supercritical-to-subcritical jump with the expected conjugate depth ratio.",
        exact_fields=("h1", "h2", "u1", "u2"),
        approximate_fields=("jump_location", "energy_loss"),
        failure_modes=("wrong conjugate depth", "jump moves upstream/downstream too far", "Froude class mismatch"),
        tolerance_tier="analytic",
        metrics=(
            _metric("conjugate_depth_ratio_abs", "h2_over_h1", "abs", 6.0e-2, "ratio"),
            _metric("froude_class_agreement", "froude", "class", 0.0, "class_mismatch_count"),
        ),
    )


def _transcritical_bump() -> AnalyticFixture:
    grid = _grid()
    x, _ = grid.meshgrid()
    center_x = grid.center[0]
    width = 8.0
    unit_discharge = 0.9
    critical_depth = (unit_discharge**2 / GRAVITY_MPS2) ** (1.0 / 3.0)
    bump_height = 0.18
    total_head = bump_height + 1.5 * critical_depth + 0.005
    bed = bump_height * np.maximum(0.0, 1.0 - ((x - center_x) / width) ** 2)
    depth = np.empty(grid.shape, dtype=np.float64)
    for index, bed_value in np.ndenumerate(bed):
        branch = "subcritical" if x[index] <= center_x else "supercritical"
        depth[index] = _specific_energy_depth(total_head, float(bed_value), unit_discharge, branch=branch)
    u = unit_discharge / depth
    v = np.zeros(grid.shape, dtype=np.float64)
    features = (
        Feature2_5D(
            kind="constriction",
            center=(center_x, grid.center[1]),
            radius=width,
            strength=bump_height,
            length=2.0 * width,
            width=float((grid.ny - 1) * grid.dy),
            metadata={"analytic_fixture_role": "transcritical_bump"},
        ),
    )
    scenario = _scenario(
        fixture_id="transcritical_bump",
        title="Transcritical Flow Over Bump",
        grid=grid,
        bed=bed,
        depth=depth,
        u=u,
        v=v,
        roughness=0.0,
        boundaries=_channel_boundaries(float(depth[:, 0].mean()), float(u[:, 0].mean())),
        description="Steady rectangular-channel flow over a smooth bump with near-critical crest behavior.",
        features=features,
    )
    froude = u / np.sqrt(GRAVITY_MPS2 * depth)
    reference = _reference(
        fixture_id="transcritical_bump",
        summary="Specific energy selects a subcritical upstream branch and supercritical downstream branch over the bump.",
        parameters={
            "unit_discharge": unit_discharge,
            "critical_depth": critical_depth,
            "bump_height": bump_height,
            "bump_width": width,
            "total_head": total_head,
        },
        diagnostics={
            "crest_froude": float(froude[:, grid.nx // 2].mean()),
            "upstream_froude": float(froude[:, 0].mean()),
            "downstream_froude": float(froude[:, -1].mean()),
        },
    )
    return _fixture(
        scenario=scenario,
        reference=reference,
        reference_fields=_reference_fields(bed, depth, u, v),
        title="Transcritical Flow Over Bump",
        benchmark_family="steady transcritical bump flow",
        scenario_kind="transcritical_bump",
        source_note="Derived from rectangular-channel specific energy with branch selection across a parabolic bed bump.",
        equations=("H = z_b + h + q^2/(2 g h^2)", "h_c = (q^2/g)^(1/3)", "Fr = q/(h sqrt(g h))"),
        expected_summary="The flow approaches critical near the crest, with subcritical upstream and supercritical downstream branches.",
        exact_fields=("h", "u", "hu", "froude"),
        approximate_fields=("critical_location",),
        failure_modes=("wrong energy branch", "crest Froude far from one", "unit discharge drift"),
        tolerance_tier="analytic",
        metrics=(
            _metric("unit_discharge_linf", "hu", "linf", 4.0e-2, "m2/s"),
            _metric("crest_froude_abs", "froude", "abs", 2.0e-1, "ratio"),
        ),
    )


def _fixture(
    *,
    scenario: Scenario2_5D,
    reference: dict[str, object],
    reference_fields: dict[str, np.ndarray],
    title: str,
    benchmark_family: str,
    scenario_kind: str,
    source_note: str,
    equations: tuple[str, ...],
    expected_summary: str,
    exact_fields: tuple[str, ...],
    approximate_fields: tuple[str, ...],
    failure_modes: tuple[str, ...],
    tolerance_tier: str,
    metrics: tuple[dict[str, object], ...],
) -> AnalyticFixture:
    fixture_id = str(reference["fixture_id"])
    manifest_entry = {
        "fixture_id": fixture_id,
        "title": title,
        "benchmark_family": benchmark_family,
        "scenario_kind": scenario_kind,
        "provenance": {
            "source_type": "manual_analytic_derivation",
            "source_note": source_note,
            "derived_by": "raftsim milestone 17",
            "external_data_vendored": False,
        },
        "equations": list(equations),
        "expected_behavior": {
            "summary": expected_summary,
            "exact_fields": list(exact_fields),
            "approximate_fields": list(approximate_fields),
            "failure_modes": list(failure_modes),
        },
        "tolerance_tier": tolerance_tier,
        "metrics": list(metrics),
        "outputs": {
            "scenario_package": f"fixtures/{fixture_id}/scenario",
            "analytic_reference": f"fixtures/{fixture_id}/reference.json",
            "analytic_fields": f"fixtures/{fixture_id}/reference_fields.npz",
        },
    }
    return AnalyticFixture(
        fixture_id=fixture_id,
        scenario=scenario,
        reference=reference,
        reference_fields=reference_fields,
        manifest_entry=manifest_entry,
    )


def _scenario(
    *,
    fixture_id: str,
    title: str,
    grid: GridSpec2_5D,
    bed: np.ndarray,
    depth: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    roughness: float,
    boundaries: tuple[BoundaryCondition2_5D, ...],
    description: str,
    features: tuple[Feature2_5D, ...] = (),
) -> Scenario2_5D:
    return Scenario2_5D(
        metadata=ScenarioMetadata2_5D(
            scenario_id=f"analytic_{fixture_id}",
            scenario_type="fixture",
            seed=17,
            fixture_kind=None,
            generator="raftsim.analytic_fixtures",
            generator_version=ANALYTIC_FIXTURE_SET_VERSION,
            description=description,
            flow_band="analytic_diagnostic",
            difficulty_preset="not_gameplay",
            confidence_score=1.0,
            provenance={
                "analytic_fixture_id": fixture_id,
                "title": title,
                "external_data_vendored": False,
            },
        ),
        grid=grid,
        fixed_dt=1.0 / 60.0,
        duration=6.0,
        bed=bed,
        initial_state=InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v),
        boundaries=boundaries,
        features=features,
        probes=_probes(grid),
        raft=RaftParameters2_5D(),
        roughness=roughness,
    )


def _reference(
    *,
    fixture_id: str,
    summary: str,
    parameters: dict[str, object],
    diagnostics: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": ANALYTIC_REFERENCE_SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "fixture_set_version": ANALYTIC_FIXTURE_SET_VERSION,
        "summary": summary,
        "parameters": parameters,
        "diagnostics": diagnostics,
    }


def _reference_fields(bed: np.ndarray, depth: np.ndarray, u: np.ndarray, v: np.ndarray) -> dict[str, np.ndarray]:
    eta = bed + depth
    return {
        "bed": np.asarray(bed, dtype=np.float64),
        "depth": np.asarray(depth, dtype=np.float64),
        "eta": np.asarray(eta, dtype=np.float64),
        "u": np.asarray(u, dtype=np.float64),
        "v": np.asarray(v, dtype=np.float64),
        "hu": np.asarray(depth * u, dtype=np.float64),
        "hv": np.asarray(depth * v, dtype=np.float64),
        "wet": np.asarray(depth > 1.0e-6, dtype=np.bool_),
    }


def _grid(nx: int = 64, ny: int = 24) -> GridSpec2_5D:
    return GridSpec2_5D(nx=nx, ny=ny, dx=1.0, dy=1.0, origin_x=0.0, origin_y=-0.5 * (ny - 1))


def _wall_boundaries() -> tuple[BoundaryCondition2_5D, ...]:
    return (
        BoundaryCondition2_5D("west", "wall"),
        BoundaryCondition2_5D("east", "wall"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )


def _channel_boundaries(depth: float, speed: float) -> tuple[BoundaryCondition2_5D, ...]:
    return (
        BoundaryCondition2_5D("west", "inflow", depth=depth, velocity=(speed, 0.0)),
        BoundaryCondition2_5D("east", "outflow"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )


def _shoreline_boundaries() -> tuple[BoundaryCondition2_5D, ...]:
    return (
        BoundaryCondition2_5D("west", "open"),
        BoundaryCondition2_5D("east", "open"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )


def _probes(grid: GridSpec2_5D) -> tuple[Probe2_5D, ...]:
    xs = grid.x_coordinates()
    return (
        Probe2_5D("upstream_center", (float(xs[grid.nx // 4]), grid.center[1])),
        Probe2_5D("midstream_center", grid.center),
        Probe2_5D("downstream_center", (float(xs[(grid.nx * 3) // 4]), grid.center[1])),
        Probe2_5D(
            "mid_cross_section",
            grid.center,
            kind="cross_section",
            normal=(0.0, 1.0),
            length=float((grid.ny - 1) * grid.dy),
        ),
    )


def _specific_energy_depth(total_head: float, bed: float, unit_discharge: float, *, branch: str) -> float:
    available_energy = total_head - bed
    critical_depth = (unit_discharge**2 / GRAVITY_MPS2) ** (1.0 / 3.0)
    minimum_energy = 1.5 * critical_depth
    if available_energy < minimum_energy:
        raise ValueError("available specific energy is below the critical minimum.")

    def residual(depth: float) -> float:
        return depth + unit_discharge**2 / (2.0 * GRAVITY_MPS2 * depth**2) - available_energy

    if abs(available_energy - minimum_energy) < 1.0e-12:
        return critical_depth

    if branch == "supercritical":
        lo = 1.0e-6
        hi = critical_depth
    elif branch == "subcritical":
        lo = critical_depth
        hi = max(available_energy + 1.0, critical_depth * 2.0)
        while residual(hi) < 0.0:
            hi *= 2.0
    else:
        raise ValueError(f"Unknown specific-energy branch: {branch}")

    f_lo = residual(lo)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = residual(mid)
        if abs(f_mid) < 1.0e-13:
            return mid
        if f_lo * f_mid <= 0.0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)


def _metric(metric_id: str, field: str, norm: str, threshold: float, units: str) -> dict[str, object]:
    return {
        "metric_id": metric_id,
        "field": field,
        "norm": norm,
        "threshold": threshold,
        "units": units,
    }


def _write_json(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


_BUILDERS = {
    "lake_at_rest_balance": _lake_at_rest_balance,
    "sloping_channel_friction": _sloping_channel_friction,
    "wet_dry_shoreline": _wet_dry_shoreline,
    "bed_step_subcritical": _bed_step_subcritical,
    "dam_break_bore": _dam_break_bore,
    "hydraulic_jump_conjugate_depth": _hydraulic_jump_conjugate_depth,
    "transcritical_bump": _transcritical_bump,
}
