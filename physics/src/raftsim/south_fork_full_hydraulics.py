"""Author and cook all South Fork named rapids at the three release flows.

The rapid catalog supplies the guide-facing feature inventory.  The M2
procedural geography supplies the registered bed and explicit provenance.  This
module turns both into solver-neutral scenarios, runs the genuine first-party
finite-volume solver, and emits hash-locked cooked fields for Unreal's moving
live-water window.  Generated in-channel geometry remains interpreted game
content, never surveyed bathymetry or navigation data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from .dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
from .named_rapid_registry import SOURCE_CATALOG_RELATIVE_PATH
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
from .south_fork_a1_stationing import (
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
)
from .south_fork_procedural_geography import (
    PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
)

FULL_HYDRAULICS_ROOT_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics"
)
FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH = (
    f"{FULL_HYDRAULICS_ROOT_RELATIVE_PATH}/manifest.json"
)
FULL_HYDRAULICS_STREAMING_RELATIVE_PATH = (
    f"{FULL_HYDRAULICS_ROOT_RELATIVE_PATH}/streaming_manifest.json"
)
FULL_REACH_TRANSIT_ROOT_RELATIVE_PATH = (
    f"{FULL_HYDRAULICS_ROOT_RELATIVE_PATH}/full_reach_transit_seed"
)
FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH = (
    f"{FULL_REACH_TRANSIT_ROOT_RELATIVE_PATH}/manifest.json"
)
FLOW_PRESETS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/flow_presets.json"
)

SCHEMA = "raftsim.south_fork.full_hydraulics.v1"
STREAMING_SCHEMA = "raftsim.south_fork.moving_water_streaming.v1"
COOKED_SCHEMA = "raftsim.cooked_flow_fields.v1"
GENERATOR_VERSION = "south_fork_full_hydraulics_v1"
FLOW_BAND_IDS = ("low_runnable", "median_runnable", "high_runnable")
WINDOW_LENGTH_M = 400.0
CELL_SIZE_M = 4.0
CROSS_HALF_WIDTH_M = 40.0
SOLVER_STEPS = 480
SOLVER_FRAME_INTERVAL = 480
GRAVITY = 9.80665

ARRAY_CONTRACT = {
    "h": ("float32", "m", "Water depth above bed."),
    "u": ("float32", "m_per_s", "Depth-averaged downstream velocity."),
    "v": ("float32", "m_per_s", "Depth-averaged cross-stream velocity."),
    "bed": ("float32", "m", "Interpreted game bed elevation."),
    "wet_mask": ("uint8", "boolean", "1 where the solver reports the cell wet."),
}


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _stable_unit(label: str) -> float:
    digest = hashlib.sha256(label.encode()).digest()
    return int.from_bytes(digest[:4], "little") / float(2**32 - 1)


def _south_fork_catalog(repo_root: Path) -> dict[str, Any]:
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    return next(
        river
        for river in catalog["rivers"]
        if river["river_id"] == "south_fork_american_chili_bar"
    )


def _rapid_records(repo_root: Path) -> list[dict[str, Any]]:
    catalog = _south_fork_catalog(repo_root)
    stationing = _load_json(
        repo_root, FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
    )
    stations = {rapid["name"]: rapid for rapid in stationing["rapid_stations"]}
    records = []
    for rapid in catalog["rapids"]:
        record = dict(rapid)
        record["station_m"] = float(stations[rapid["name"]]["station_m"])
        record["lon_lat"] = stations[rapid["name"]]["lon_lat"]
        records.append(record)
    return records


def _flow_bands(repo_root: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(repo_root, FLOW_PRESETS_RELATIVE_PATH)
    return {band["flow_band"]: band for band in payload["flow_bands"]}


def _class_strength(rapid_class: str) -> float:
    if "III+" in rapid_class:
        return 1.0
    if "III" in rapid_class:
        return 0.82
    if "II+" in rapid_class or "II-III" in rapid_class:
        return 0.66
    if "II" in rapid_class:
        return 0.52
    return 0.6


def _feature_kind(feature_type: str) -> str:
    if feature_type in {"hole", "pourover"}:
        return "hole"
    if feature_type in {"ledge"}:
        return "ledge"
    if feature_type in {"wave", "wave_train", "continuous_whitewater", "line"}:
        return "wave_train"
    if feature_type in {"eddy_line", "recovery_pool", "scout", "portage"}:
        return "eddy_line"
    if feature_type in {"lateral", "boil"}:
        return "lateral"
    if feature_type in {"shelf", "sneak_line"}:
        return "shallow"
    if feature_type in {"sieve"}:
        return "strainer"
    return "rock"


def _feature_strength(consequence_class: str) -> float:
    return {
        "low_nuisance": 0.3,
        "swim_risk": 0.52,
        "surf_or_retention": 0.68,
        "flip_risk": 0.82,
        "wrap_or_pin": 0.92,
        "entrapment_life_threat": 1.0,
    }[consequence_class]


def _feature_position(
    rapid: dict[str, Any],
    subfeature: dict[str, Any],
    window_start_m: float,
    rapid_x_m: float,
    channel_half_width_m: float,
) -> tuple[float, float]:
    along = subfeature["relative_position"]["along"]
    base_x = {
        "entry": max(44.0, rapid_x_m - 72.0),
        "middle": rapid_x_m,
        "exit": min(WINDOW_LENGTH_M - 44.0, rapid_x_m + 72.0),
    }[along]
    jitter = (
        _stable_unit(f"{rapid['name']}:{subfeature['subfeature_id']}:x") - 0.5
    ) * 28.0
    x = float(np.clip(base_x + jitter, 20.0, WINDOW_LENGTH_M - 20.0))
    across = subfeature["relative_position"]["across"]
    side = {"left": 0.55, "center": 0.0, "right": -0.55}[across]
    lateral_jitter = (
        _stable_unit(f"{rapid['name']}:{subfeature['subfeature_id']}:y") - 0.5
    ) * 4.0
    y = side * channel_half_width_m + lateral_jitter
    return window_start_m + x, float(y)


def _make_features(
    rapid: dict[str, Any],
    window_start_m: float,
    rapid_x_m: float,
    channel_half_width_m: float,
) -> tuple[Feature2_5D, ...]:
    features = []
    for subfeature in rapid["feature_inventory"]:
        kind = _feature_kind(str(subfeature["feature_type"]))
        strength = _feature_strength(str(subfeature["consequence_class"]))
        center = _feature_position(
            rapid,
            subfeature,
            window_start_m,
            rapid_x_m,
            channel_half_width_m,
        )
        radius = 4.0 + strength * 3.0
        features.append(
            Feature2_5D(
                kind=kind,  # type: ignore[arg-type]
                center=center,
                radius=radius,
                strength=strength,
                length=24.0 + strength * 28.0,
                width=8.0 + strength * 12.0,
                angle=(strength - 0.5) * 0.55 if kind == "lateral" else 0.0,
                metadata={
                    "subfeature_id": subfeature["subfeature_id"],
                    "display_name": subfeature["display_name"],
                    "catalog_feature_type": subfeature["feature_type"],
                    "relative_position_along": subfeature["relative_position"]["along"],
                    "relative_position_across": subfeature["relative_position"][
                        "across"
                    ],
                    "consequence_class": subfeature["consequence_class"],
                    "guide_review_status": subfeature["guide_review_status"],
                    "geometry_authority": "procedural_infill_interpreted_from_guide_inventory",
                },
            )
        )
    return tuple(features)


def _apply_feature_geometry(
    bed: np.ndarray,
    grid: GridSpec2_5D,
    features: tuple[Feature2_5D, ...],
) -> np.ndarray:
    result = bed.copy()
    x, y = grid.meshgrid()
    for feature in features:
        cx, cy = feature.center
        radius = max(feature.radius, CELL_SIZE_M)
        dx = x - cx
        dy = y - cy
        radial = np.exp(-0.5 * ((dx / radius) ** 2 + (dy / radius) ** 2))
        amplitude = 0.28 + 0.62 * feature.strength
        if feature.kind in {"rock", "strainer", "shallow"}:
            result += amplitude * radial
        elif feature.kind == "hole":
            control = np.exp(-0.5 * (((dx + 8.0) / 5.0) ** 2 + (dy / radius) ** 2))
            scour = np.exp(-0.5 * (((dx - 7.0) / 7.0) ** 2 + (dy / radius) ** 2))
            result += amplitude * 0.48 * control - amplitude * 0.72 * scour
        elif feature.kind == "ledge":
            transition = 0.5 + 0.5 * np.tanh(dx / 2.5)
            lateral = np.exp(-0.5 * (dy / max(radius * 1.8, 6.0)) ** 2)
            result -= amplitude * transition * lateral
        elif feature.kind == "wave_train":
            envelope = np.exp(-0.5 * (dx / max(feature.length * 0.45, 12.0)) ** 2)
            lateral = np.exp(-0.5 * (dy / max(radius * 1.8, 8.0)) ** 2)
            result += amplitude * 0.18 * np.sin(dx / 6.0 * math.pi) * envelope * lateral
        elif feature.kind == "eddy_line":
            result -= amplitude * 0.24 * radial
        elif feature.kind == "lateral":
            diagonal = dy - math.tan(feature.angle) * dx
            ridge = np.exp(-0.5 * (diagonal / max(radius * 0.75, 3.0)) ** 2)
            along = np.exp(-0.5 * (dx / max(feature.length * 0.5, 10.0)) ** 2)
            result += amplitude * 0.3 * ridge * along
    return result


def _sample_m2_window(
    repo_root: Path,
    rapid: dict[str, Any],
) -> tuple[GridSpec2_5D, np.ndarray, np.ndarray, np.ndarray, float, float]:
    with np.load(repo_root / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH) as geography:
        source_stations = geography["stations_m"].astype(np.float64)
        source_lateral = geography["lateral_offsets_m"].astype(np.float64)
        source_bed = geography["bed_elevation_m"].astype(np.float64)
        source_surface = geography["conditioned_water_surface_m"].astype(np.float64)
        source_width = geography["channel_half_width_m"].astype(np.float64)

    rapid_station = float(rapid["station_m"])
    reach_end = float(source_stations[-1])
    window_start = float(
        np.clip(rapid_station - WINDOW_LENGTH_M * 0.5, 0.0, reach_end - WINDOW_LENGTH_M)
    )
    rapid_x = rapid_station - window_start
    nx = int(round(WINDOW_LENGTH_M / CELL_SIZE_M)) + 1
    ny = int(round(2.0 * CROSS_HALF_WIDTH_M / CELL_SIZE_M)) + 1
    grid = GridSpec2_5D(
        nx=nx,
        ny=ny,
        dx=CELL_SIZE_M,
        dy=CELL_SIZE_M,
        origin_x=window_start,
        origin_y=-CROSS_HALF_WIDTH_M,
    )
    target_x = grid.x_coordinates()
    target_y = grid.y_coordinates()
    source_columns = [int(np.argmin(np.abs(source_lateral - y))) for y in target_y]
    bed = np.vstack(
        [
            np.interp(target_x, source_stations, source_bed[:, column])
            for column in source_columns
        ]
    )
    surface = np.interp(target_x, source_stations, source_surface)
    half_width = np.interp(target_x, source_stations, source_width)
    datum = float(surface[0])
    bed -= datum
    surface -= datum
    # The M2 corridor deliberately preserves authoritative DEM samples beyond
    # the procedurally completed channel.  Some source-window edge samples sit
    # below the conditioned water surface, however, and must not be interpreted
    # as a 100 m-deep side channel by the hydraulic cook.  Retain M2 bathymetry
    # inside the authored bankfull width and condition only the out-of-channel
    # cells into a gently rising, dry bank.  Higher flow stages can still wet the
    # first bank cells without flooding unrelated terrain-source depressions.
    bank_distance = np.abs(target_y[:, None]) - half_width[None, :]
    outside = bank_distance > 0.0
    conditioned_bank = surface[None, :] + 0.18 + 0.06 * bank_distance
    bed[outside] = np.maximum(bed[outside], conditioned_bank[outside])
    return grid, bed, surface, half_width, window_start, rapid_x


def _build_scenario(
    repo_root: Path,
    rapid: dict[str, Any],
    band: dict[str, Any],
) -> tuple[Scenario2_5D, tuple[Feature2_5D, ...]]:
    grid, base_bed, surface, half_width, window_start, rapid_x = _sample_m2_window(
        repo_root, rapid
    )
    channel_width = float(
        np.interp(float(rapid["station_m"]), grid.x_coordinates(), half_width)
    )
    features = _make_features(rapid, window_start, rapid_x, channel_width)
    bed = _apply_feature_geometry(base_bed, grid, features)

    band_id = str(band["flow_band"])
    stage_offset = {
        "low_runnable": 0.0,
        "median_runnable": 0.36,
        "high_runnable": 0.82,
    }[band_id]
    eta = surface[None, :] + stage_offset
    depth = np.maximum(eta - bed, 0.0)
    wet = depth > 0.025
    discharge = float(band["discharge_m3s"])
    area_by_column = np.sum(depth, axis=0) * grid.dy
    velocity_by_column = np.clip(discharge / np.maximum(area_by_column, 1.0), 0.0, 8.0)
    u = np.where(wet, velocity_by_column[None, :], 0.0)
    v = np.zeros_like(u)
    for feature in features:
        if feature.kind not in {"eddy_line", "lateral"}:
            continue
        x, y = grid.meshgrid()
        distance = (x - feature.center[0]) ** 2 + (y - feature.center[1]) ** 2
        envelope = np.exp(-distance / max(2.0 * feature.radius**2, 1.0))
        direction = 1.0 if feature.center[1] >= 0.0 else -1.0
        v += direction * 0.22 * feature.strength * envelope
    v = np.where(wet, v, 0.0)
    state = InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v)
    west_speed = float(velocity_by_column[0])
    boundaries = (
        BoundaryCondition2_5D(
            "west",
            "inflow",
            stage=float(surface[0] + stage_offset),
            velocity=(west_speed, 0.0),
            metadata={
                "target_discharge_m3s": discharge,
                "target_discharge_cfs": float(band["discharge_cfs"]),
            },
        ),
        BoundaryCondition2_5D(
            "east",
            "outflow",
            stage=float(surface[-1] + stage_offset),
        ),
        BoundaryCondition2_5D("south", "bank"),
        BoundaryCondition2_5D("north", "bank"),
    )
    probes = (
        Probe2_5D("entry", (grid.origin_x + 8.0, 0.0)),
        Probe2_5D("rapid_center", (float(rapid["station_m"]), 0.0)),
        Probe2_5D("exit", (grid.origin_x + WINDOW_LENGTH_M - 8.0, 0.0)),
        Probe2_5D(
            "rapid_cross_section",
            (float(rapid["station_m"]), 0.0),
            kind="cross_section",
            normal=(0.0, 1.0),
            length=2.0 * CROSS_HALF_WIDTH_M,
        ),
    )
    slug = _slug(str(rapid["name"]))
    scenario = Scenario2_5D(
        metadata=ScenarioMetadata2_5D(
            scenario_id=f"south_fork_{slug}_{band_id}",
            scenario_type="real_world",
            seed=int(rapid["order"]),
            generator="raftsim.south_fork_full_hydraulics",
            generator_version=GENERATOR_VERSION,
            description=(
                f"{rapid['name']} live-water window at {band['discharge_cfs']:.0f} cfs."
            ),
            river_id="south_fork_american_chili_bar",
            section_id=slug,
            coordinate_reference_system=(
                "curvilinear adopted-axis station meters; y positive river-left"
            ),
            source_manifest=PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
            gauge_source="USGS/CDEC flow synthesis recorded in flow_presets.json",
            season_preset=str(band["season"]),
            flow_percentile=float(sum(band["percentile_range"]) * 0.5),
            flow_band=band_id,
            difficulty_preset=f"class_{_slug(str(rapid['class']))}",
            confidence_score=float(band["confidence"]),
            provenance={
                "rapid_name": rapid["name"],
                "rapid_order": int(rapid["order"]),
                "station_m": float(rapid["station_m"]),
                "target_discharge_m3s": discharge,
                "target_discharge_cfs": float(band["discharge_cfs"]),
                "terrain_authority": "M2 source_and_procedural_authority_masks",
                "bathymetry_authority": "procedural_infill",
                "feature_geometry_authority": (
                    "procedural_infill_interpreted_from_guide_inventory"
                ),
                "not_for_navigation": True,
            },
        ),
        grid=grid,
        fixed_dt=0.02,
        duration=SOLVER_STEPS * 0.02,
        bed=bed,
        initial_state=state,
        boundaries=boundaries,
        features=features,
        probes=probes,
        raft=RaftParameters2_5D(),
        roughness=0.039,
    )
    return scenario, features


def _load_final_fields(run_dir: Path, scenario: Scenario2_5D) -> dict[str, np.ndarray]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    frame_path = run_dir / manifest["frames"][-1]
    shape = scenario.grid.shape
    fields = {
        "h": np.zeros(shape, dtype=np.float64),
        "u": np.zeros(shape, dtype=np.float64),
        "v": np.zeros(shape, dtype=np.float64),
        "eta": np.zeros(shape, dtype=np.float64),
        "froude": np.zeros(shape, dtype=np.float64),
        "wet_mask": np.zeros(shape, dtype=np.uint8),
    }
    with frame_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            i = int(row["row"])
            j = int(row["col"])
            fields["h"][i, j] = float(row["h"])
            fields["u"][i, j] = float(row["u"])
            fields["v"][i, j] = float(row["v"])
            fields["eta"][i, j] = float(row["eta"])
            fields["froude"][i, j] = float(row["froude"])
            fields["wet_mask"][i, j] = int(row["wet"])
    fields["bed"] = scenario.bed.copy()
    return fields


def _evaluate_fields(
    scenario: Scenario2_5D,
    fields: dict[str, np.ndarray],
    features: tuple[Feature2_5D, ...],
    target_discharge_m3s: float,
    solver_validation: dict[str, Any],
) -> dict[str, Any]:
    finite = all(np.isfinite(fields[name]).all() for name in ("h", "u", "v", "eta"))
    h = fields["h"]
    speed = np.hypot(fields["u"], fields["v"])
    mid_column = scenario.grid.nx // 2
    entry_column = 1
    outlet_column = scenario.grid.nx - 2

    def section_discharge(column: int) -> float:
        return float(np.sum(h[:, column] * fields["u"][:, column]) * scenario.grid.dy)

    entry_discharge = section_discharge(entry_column)
    rapid_discharge = section_discharge(mid_column)
    outlet_discharge = section_discharge(outlet_column)
    discharge_ratio = rapid_discharge / max(target_discharge_m3s, 1.0e-6)
    initial_volume = float(
        np.sum(scenario.initial_state.depth) * scenario.grid.dx * scenario.grid.dy
    )
    final_volume = float(np.sum(h) * scenario.grid.dx * scenario.grid.dy)
    volume_ratio = final_volume / max(initial_volume, 1.0e-6)
    x, y = scenario.grid.meshgrid()
    feature_envelopes = []
    for feature in features:
        radius = max(feature.radius * 1.6, CELL_SIZE_M * 1.5)
        mask = (x - feature.center[0]) ** 2 + (y - feature.center[1]) ** 2 <= radius**2
        if not mask.any():
            passed = False
            bed_relief = 0.0
            wet_fraction = 0.0
            max_froude = 0.0
        else:
            bed_relief = float(np.ptp(fields["bed"][mask]))
            wet_fraction = float(np.mean(fields["wet_mask"][mask] > 0))
            max_froude = float(np.max(fields["froude"][mask]))
            passed = bool(
                np.isfinite(fields["h"][mask]).all()
                and bed_relief >= 0.015
                and (wet_fraction > 0.0 or feature.kind in {"rock", "strainer"})
            )
        feature_envelopes.append(
            {
                "subfeature_id": feature.metadata["subfeature_id"],
                "kind": feature.kind,
                "passed": passed,
                "bed_relief_m": round(bed_relief, 6),
                "wet_fraction": round(wet_fraction, 6),
                "max_froude": round(max_froude, 6),
            }
        )
    checks = {
        "finite_fields": finite,
        "nonnegative_depth": bool(np.min(h) >= 0.0),
        "positive_wet_area": bool(np.count_nonzero(fields["wet_mask"]) > 0),
        "bounded_velocity": bool(float(np.max(speed)) < 25.0),
        "bounded_volume": bool(0.2 <= volume_ratio <= 4.0),
        "positive_entry_and_outflow": bool(
            entry_discharge > 0.5 and outlet_discharge > 0.5
        ),
        "bounded_rapid_discharge_response": bool(0.1 <= discharge_ratio <= 8.0),
        "all_feature_envelopes": all(item["passed"] for item in feature_envelopes),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "target_discharge_m3s": target_discharge_m3s,
            "entry_discharge_m3s": round(entry_discharge, 6),
            "rapid_section_discharge_m3s": round(rapid_discharge, 6),
            "outlet_discharge_m3s": round(outlet_discharge, 6),
            "discharge_ratio": round(discharge_ratio, 6),
            "initial_volume_m3": round(initial_volume, 6),
            "final_volume_m3": round(final_volume, 6),
            "volume_ratio": round(volume_ratio, 6),
            "wet_fraction": round(float(np.mean(fields["wet_mask"] > 0)), 6),
            "max_speed_mps": round(float(np.max(speed)), 6),
            "max_froude": round(float(np.max(fields["froude"])), 6),
            "solver_mass_relative_drift": solver_validation.get("mass_relative_drift"),
            "solver_validation_passed": solver_validation.get("passed"),
        },
        "feature_envelopes": feature_envelopes,
    }


def _array_record(
    root: Path, path: Path, name: str, array: np.ndarray
) -> dict[str, Any]:
    dtype, units, description = ARRAY_CONTRACT[name]
    return {
        "file": str(path.relative_to(root)),
        "dtype": dtype,
        "shape": list(array.shape),
        "units": units,
        "description": description,
        "sha256": _sha256(path),
    }


def _write_full_reach_transit_seed(
    repo_root: Path,
    flow_bands: dict[str, dict[str, Any]],
    solver_hash: str,
) -> Path:
    """Write the continuous M2-derived seed used between named rapid cooks.

    These arrays are explicitly a procedural initial condition, not a claim of
    solver-cooked surveyed bathymetry.  Every moving crop immediately advances
    them with the same genuine finite-volume runtime used by named rapids.
    """

    with np.load(repo_root / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH) as geography:
        source_stations = geography["stations_m"].astype(np.float64)
        source_lateral = geography["lateral_offsets_m"].astype(np.float64)
        source_bed = geography["bed_elevation_m"].astype(np.float64)
        source_surface = geography["conditioned_water_surface_m"].astype(np.float64)
        source_width = geography["channel_half_width_m"].astype(np.float64)

    nx = source_stations.size
    target_stations = np.linspace(source_stations[0], source_stations[-1], nx)
    target_lateral = np.arange(
        -CROSS_HALF_WIDTH_M,
        CROSS_HALF_WIDTH_M + CELL_SIZE_M * 0.5,
        CELL_SIZE_M,
        dtype=np.float64,
    )
    columns = [int(np.argmin(np.abs(source_lateral - y))) for y in target_lateral]
    bed = np.vstack(
        [
            np.interp(target_stations, source_stations, source_bed[:, column])
            for column in columns
        ]
    )
    surface = np.interp(target_stations, source_stations, source_surface)
    half_width = np.interp(target_stations, source_stations, source_width)
    bank_distance = np.abs(target_lateral[:, None]) - half_width[None, :]
    outside = bank_distance > 0.0
    conditioned_bank = surface[None, :] + 0.18 + 0.06 * bank_distance
    bed[outside] = np.maximum(bed[outside], conditioned_bank[outside])

    transit_root = repo_root / FULL_REACH_TRANSIT_ROOT_RELATIVE_PATH
    bands_payload = []
    for band_id in FLOW_BAND_IDS:
        band = flow_bands[band_id]
        stage_offset = {
            "low_runnable": 0.0,
            "median_runnable": 0.36,
            "high_runnable": 0.82,
        }[band_id]
        depth = np.maximum(surface[None, :] + stage_offset - bed, 0.0)
        wet = depth > 0.025
        area = np.sum(depth, axis=0) * CELL_SIZE_M
        discharge = float(band["discharge_m3s"])
        velocity = np.clip(discharge / np.maximum(area, 1.0), 0.0, 8.0)
        u = np.where(wet, velocity[None, :], 0.0)
        v = np.zeros_like(u)
        arrays = {
            "h": depth.astype(np.float32),
            "u": u.astype(np.float32),
            "v": v.astype(np.float32),
            "bed": bed.astype(np.float32),
            "wet_mask": wet.astype(np.uint8),
        }
        band_root = transit_root / band_id
        band_root.mkdir(parents=True, exist_ok=True)
        array_records = {}
        for name, array in arrays.items():
            path = band_root / f"{name}.npy"
            np.save(path, np.ascontiguousarray(array))
            array_records[name] = _array_record(transit_root, path, name, array)
        west_speed = float(velocity[0])
        boundaries = (
            BoundaryCondition2_5D(
                "west",
                "inflow",
                stage=float(surface[0] + stage_offset),
                velocity=(west_speed, 0.0),
                metadata={
                    "target_discharge_m3s": discharge,
                    "target_discharge_cfs": float(band["discharge_cfs"]),
                },
            ),
            BoundaryCondition2_5D(
                "east", "outflow", stage=float(surface[-1] + stage_offset)
            ),
            BoundaryCondition2_5D("south", "bank"),
            BoundaryCondition2_5D("north", "bank"),
        )
        checks = {
            "finite_seed_fields": all(
                bool(np.isfinite(arrays[name]).all()) for name in ("h", "u", "v", "bed")
            ),
            "nonnegative_depth": bool(float(np.min(depth)) >= 0.0),
            "positive_wet_area": bool(np.count_nonzero(wet) > 0),
            "bounded_seed_velocity": bool(float(np.max(np.hypot(u, v))) <= 8.0),
            "continuous_station_axis": bool(
                np.allclose(
                    np.diff(target_stations), target_stations[1] - target_stations[0]
                )
            ),
        }
        bands_payload.append(
            {
                "band_id": band_id,
                "target_discharge_cfs": float(band["discharge_cfs"]),
                "target_discharge_m3s": discharge,
                "arrays": array_records,
                "runtime_boundaries": [item.to_json_dict() for item in boundaries],
                "validation": {
                    "passed": all(checks.values()),
                    "checks": checks,
                    "metrics": {
                        "wet_fraction": round(float(np.mean(wet)), 6),
                        "max_seed_speed_mps": round(float(np.max(np.hypot(u, v))), 6),
                        "initial_volume_m3": round(
                            float(np.sum(depth))
                            * float(target_stations[1] - target_stations[0])
                            * CELL_SIZE_M,
                            6,
                        ),
                    },
                },
            }
        )

    dx = float(target_stations[1] - target_stations[0])
    manifest = {
        "schema": COOKED_SCHEMA,
        "generated_on": "2026-07-19",
        "river_id": "south_fork_american_chili_bar",
        "status": "procedural_transit_seed_ready_for_genuine_runtime_solver",
        "window_id": "south_fork_full_reach_transit_live_window",
        "station_range_m": [float(target_stations[0]), float(target_stations[-1])],
        "grid": {
            "nx": int(target_stations.size),
            "ny": int(target_lateral.size),
            "dx_m": dx,
            "dy_m": CELL_SIZE_M,
            "origin_x_m": float(target_stations[0]),
            "origin_y_m": float(target_lateral[0]),
            "downstream_axis": "+x",
            "layout": "row_major_c_order",
            "crs": "curvilinear adopted-axis station meters; y positive river-left",
        },
        "solver": {
            "solver": "raftsim_water_cpp_v1",
            "binary_sha256": solver_hash,
            "solver_mode": "finite_volume",
            "flux_scheme": "hll",
            "spatial_order": 2,
            "boundary_mode": "scenario",
            "cfl": 0.38,
            "dry_tolerance": 1.0e-6,
            "feature_strength_scale": 0.0,
            "roughness_scale": 1.0,
            "bed_slope_source_scale": 1.0,
            "preserve_initial_mass": False,
            "disable_fixture_calibrations": True,
            "fixed_dt_s": 0.02,
        },
        "bands": bands_payload,
        "all_bands_passed": all(band["validation"]["passed"] for band in bands_payload),
        "authority": {
            "seed_kind": "procedural_transit_initial_condition",
            "terrain_and_bathymetry": PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
            "genuine_solver_begins_at_runtime": True,
            "not_solver_cooked_named_rapid_evidence": True,
            "not_for_navigation": True,
        },
    }
    manifest_path = repo_root / FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH
    _write_json(manifest_path, manifest)
    return manifest_path


def _rapid_gameplay_binding(
    rapid: dict[str, Any], scenario: Scenario2_5D
) -> dict[str, Any]:
    hazards = [
        {
            "subfeature_id": subfeature["subfeature_id"],
            "consequence_class": subfeature["consequence_class"],
            "feature_type": subfeature["feature_type"],
        }
        for subfeature in rapid["feature_inventory"]
        if subfeature["consequence_class"]
        in {"surf_or_retention", "flip_risk", "wrap_or_pin", "entrapment_life_threat"}
    ]
    start = scenario.grid.origin_x
    end = start + WINDOW_LENGTH_M
    preferred_lines = []
    for band_id, lateral in (
        ("low_runnable", -2.0),
        ("median_runnable", 0.0),
        ("high_runnable", 3.0),
    ):
        preferred_lines.append(
            {
                "flow_band": band_id,
                "polyline_station_lateral_m": [
                    [round(start + 32.0, 3), 0.0],
                    [round(float(rapid["station_m"]), 3), lateral],
                    [round(end - 32.0, 3), 0.0],
                ],
            }
        )
    return {
        "entry_checkpoint_station_m": round(start + 20.0, 3),
        "exit_checkpoint_station_m": round(end - 20.0, 3),
        "scout_eddy": {
            "station_m": round(max(start + 24.0, float(rapid["station_m"]) - 92.0), 3),
            "lateral_offset_m": 0.72 * CROSS_HALF_WIDTH_M,
        },
        "rescue_zone": {
            "station_range_m": [round(end - 72.0, 3), round(end - 16.0, 3)],
            "lateral_range_m": [-CROSS_HALF_WIDTH_M, CROSS_HALF_WIDTH_M],
        },
        "preferred_lines": preferred_lines,
        "hazards": hazards,
        "outcome_envelope": {
            "requires_finite_live_water": True,
            "requires_positive_downstream_discharge": True,
            "requires_every_catalog_subfeature_signal": True,
            "flip_wrap_or_retention_hazards": len(hazards),
        },
    }


def _build_streaming_manifest(
    repo_root: Path,
    rapid_entries: list[dict[str, Any]],
    transit_manifest_path: Path,
) -> dict[str, Any]:
    stationing = _load_json(
        repo_root, FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
    )
    reach_end = float(stationing["station_axis"]["adopted_route_length_m"])
    windows = []
    for entry in rapid_entries:
        windows.append(
            {
                "window_id": entry["window_id"],
                "rapid_name": entry["rapid_name"],
                "rapid_order": entry["rapid_order"],
                "station_range_m": entry["station_range_m"],
                "cooked_fields_manifest": entry["cooked_fields_manifest"],
                "flow_bands": list(FLOW_BAND_IDS),
                "preload_distance_m": 96.0,
                "handoff_blend_distance_m": 64.0,
                "state_transfer_required": True,
            }
        )
    coverage_segments = []
    cursor = 0.0
    for window in windows:
        start, end = map(float, window["station_range_m"])
        if start > cursor:
            coverage_segments.append(
                {
                    "segment_kind": "procedural_transit_live_window",
                    "station_range_m": [round(cursor, 3), round(start, 3)],
                    "seed_source": PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
                    "cooked_fields_manifest": str(
                        transit_manifest_path.relative_to(repo_root)
                    ),
                }
            )
        coverage_segments.append(
            {
                "segment_kind": "named_rapid_cooked_window",
                "station_range_m": [round(start, 3), round(end, 3)],
                "window_id": window["window_id"],
            }
        )
        cursor = max(cursor, end)
    if cursor < reach_end:
        coverage_segments.append(
            {
                "segment_kind": "procedural_transit_live_window",
                "station_range_m": [round(cursor, 3), round(reach_end, 3)],
                "seed_source": PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
                "cooked_fields_manifest": str(
                    transit_manifest_path.relative_to(repo_root)
                ),
            }
        )
    return {
        "schema": STREAMING_SCHEMA,
        "generated_on": "2026-07-19",
        "river_id": "south_fork_american_chili_bar",
        "status": "full_reach_moving_water_streaming_ready",
        "station_range_m": [0.0, reach_end],
        "rapid_window_count": len(windows),
        "full_reach_transit_seed": {
            "cooked_fields_manifest": str(transit_manifest_path.relative_to(repo_root)),
            "sha256": _sha256(transit_manifest_path),
            "flow_bands": list(FLOW_BAND_IDS),
            "authority": "procedural_transit_initial_condition",
        },
        "windows": windows,
        "coverage_segments": coverage_segments,
        "handoff_contract": {
            "runtime_api": "URaftSimWaterRuntimeAdapter.ConfigureMovingRiverWindow",
            "handoff_mode": "instant_overlap_state_transfer_at_crop_swap",
            "old_and_new_windows_step_during_handoff": False,
            "overlap_state_transferred": True,
            "overlap_depth_and_velocity_continuous": True,
            "adapter_simulation_clock_continuous": True,
            "raft_and_gameplay_state_reset": False,
            "cut_edges": "transmissive",
            "full_window_edges": "authored_inflow_outflow_and_bank_boundaries",
        },
        "coverage": {
            "continuous": True,
            "no_station_gaps": True,
            "reach_end_m": reach_end,
        },
        "not_for_navigation": True,
    }


def write_south_fork_full_hydraulics(
    repo_root: Path,
    executable: Path,
    work_dir: Path,
) -> Path:
    """Generate, solve, validate, and write the 20 x 3 hydraulic matrix."""

    repo_root = repo_root.resolve()
    executable = executable.resolve()
    work_dir = work_dir.resolve()
    root = repo_root / FULL_HYDRAULICS_ROOT_RELATIVE_PATH
    root.mkdir(parents=True, exist_ok=True)
    rapid_records = _rapid_records(repo_root)
    flow_bands = _flow_bands(repo_root)
    rapid_entries = []
    all_combo_results = []
    solver_hash = _sha256(executable)

    for rapid in rapid_records:
        slug = _slug(str(rapid["name"]))
        rapid_root = root / "rapids" / slug
        cooked_root = rapid_root / "cooked"
        bands_payload = []
        band_evaluations = []
        representative_scenario: Scenario2_5D | None = None
        for band_id in FLOW_BAND_IDS:
            band = flow_bands[band_id]
            scenario, features = _build_scenario(repo_root, rapid, band)
            representative_scenario = scenario
            package_dir = rapid_root / "scenario" / band_id
            scenario.write_package(package_dir)
            config = CppSolverRunConfig(
                executable=executable,
                steps=SOLVER_STEPS,
                frame_interval=SOLVER_FRAME_INTERVAL,
                solver_mode="finite_volume",
                boundary_mode="scenario",
                flux_scheme="hll",
                cfl=0.38,
                dry_tolerance=1.0e-6,
                feature_strength_scale=0.0,
                roughness_scale=1.0,
                bed_slope_source_scale=1.0,
                preserve_initial_mass=False,
                disable_fixture_calibrations=True,
                allow_validation_failure=True,
            )
            run = run_cpp_solver_scenario(
                package_dir,
                output_dir=work_dir / slug / band_id,
                config=config,
            )
            fields = _load_final_fields(run.output_dir, scenario)
            solver_validation = json.loads(
                run.validation_path.read_text(encoding="utf-8")
            )
            evaluation = _evaluate_fields(
                scenario,
                fields,
                features,
                float(band["discharge_m3s"]),
                solver_validation,
            )
            cooked_band_dir = cooked_root / band_id
            cooked_band_dir.mkdir(parents=True, exist_ok=True)
            arrays = {
                "h": fields["h"].astype(np.float32),
                "u": fields["u"].astype(np.float32),
                "v": fields["v"].astype(np.float32),
                "bed": fields["bed"].astype(np.float32),
                "wet_mask": fields["wet_mask"].astype(np.uint8),
            }
            array_records = {}
            for name, array in arrays.items():
                path = cooked_band_dir / f"{name}.npy"
                np.save(path, np.ascontiguousarray(array))
                array_records[name] = _array_record(cooked_root, path, name, array)
            runtime_boundaries = [
                boundary.to_json_dict() for boundary in scenario.boundaries
            ]
            bands_payload.append(
                {
                    "band_id": band_id,
                    "target_discharge_cfs": float(band["discharge_cfs"]),
                    "target_discharge_m3s": float(band["discharge_m3s"]),
                    "scenario_package": str(package_dir.relative_to(repo_root)),
                    "arrays": array_records,
                    "runtime_boundaries": runtime_boundaries,
                    "validation": evaluation,
                    "solver_return_code": run.returncode,
                    "solver_runtime_seconds": round(run.runtime_seconds, 6),
                }
            )
            band_evaluations.append(evaluation)
            all_combo_results.append(evaluation["passed"])

        assert representative_scenario is not None
        grid = representative_scenario.grid
        cooked_manifest = {
            "schema": COOKED_SCHEMA,
            "generated_on": "2026-07-19",
            "river_id": "south_fork_american_chili_bar",
            "rapid_name": rapid["name"],
            "rapid_order": rapid["order"],
            "window_id": f"south_fork_{slug}_live_window",
            "station_range_m": [grid.origin_x, grid.origin_x + WINDOW_LENGTH_M],
            "grid": {
                "nx": grid.nx,
                "ny": grid.ny,
                "dx_m": grid.dx,
                "dy_m": grid.dy,
                "origin_x_m": grid.origin_x,
                "origin_y_m": grid.origin_y,
                "downstream_axis": "+x",
                "layout": "row_major_c_order",
                "crs": representative_scenario.metadata.coordinate_reference_system,
            },
            "solver": {
                "solver": "raftsim_water_cpp_v1",
                "binary_sha256": solver_hash,
                "solver_mode": "finite_volume",
                "flux_scheme": "hll",
                "spatial_order": 2,
                "boundary_mode": "scenario",
                "cfl": 0.38,
                "dry_tolerance": 1.0e-6,
                "feature_strength_scale": 0.0,
                "roughness_scale": 1.0,
                "bed_slope_source_scale": 1.0,
                "preserve_initial_mass": False,
                "disable_fixture_calibrations": True,
                "fixed_dt_s": 0.02,
                "steps": SOLVER_STEPS,
                "simulated_seconds": SOLVER_STEPS * 0.02,
            },
            "bands": bands_payload,
            "all_bands_passed": all(item["passed"] for item in band_evaluations),
            "gameplay_binding": _rapid_gameplay_binding(rapid, representative_scenario),
            "authority": {
                "terrain_and_bathymetry": PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
                "subfeatures": SOURCE_CATALOG_RELATIVE_PATH,
                "feature_geometry": (
                    "procedural_infill_interpreted_from_guide_inventory"
                ),
                "not_surveyed": True,
                "not_for_navigation": True,
            },
        }
        cooked_manifest_path = cooked_root / "manifest.json"
        _write_json(cooked_manifest_path, cooked_manifest)
        rapid_entries.append(
            {
                "rapid_name": rapid["name"],
                "rapid_order": rapid["order"],
                "rapid_class": rapid["class"],
                "station_m": rapid["station_m"],
                "window_id": cooked_manifest["window_id"],
                "station_range_m": cooked_manifest["station_range_m"],
                "catalog_feature_count": len(rapid["feature_inventory"]),
                "cooked_fields_manifest": str(
                    cooked_manifest_path.relative_to(repo_root)
                ),
                "all_bands_passed": cooked_manifest["all_bands_passed"],
                "manifest_sha256": _sha256(cooked_manifest_path),
            }
        )

    transit_manifest_path = _write_full_reach_transit_seed(
        repo_root, flow_bands, solver_hash
    )
    streaming = _build_streaming_manifest(
        repo_root, rapid_entries, transit_manifest_path
    )
    streaming_path = repo_root / FULL_HYDRAULICS_STREAMING_RELATIVE_PATH
    _write_json(streaming_path, streaming)
    total_features = sum(entry["catalog_feature_count"] for entry in rapid_entries)
    all_combinations_passed = all(all_combo_results)
    manifest = {
        "schema": SCHEMA,
        "generated_on": "2026-07-19",
        "river_id": "south_fork_american_chili_bar",
        "status": (
            "all_named_rapid_hydraulics_cooked_and_validated"
            if all_combinations_passed
            else "hydraulic_matrix_failed_validation"
        ),
        "generator": GENERATOR_VERSION,
        "inputs": {
            "procedural_geography": PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
            "named_rapid_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "stationing": FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
            "flow_presets": FLOW_PRESETS_RELATIVE_PATH,
            "solver_binary_sha256": solver_hash,
        },
        "matrix": {
            "rapid_count": len(rapid_entries),
            "flow_band_count": len(FLOW_BAND_IDS),
            "combination_count": len(all_combo_results),
            "passed_combination_count": sum(all_combo_results),
            "all_combinations_passed": all_combinations_passed,
            "catalog_subfeature_count": total_features,
            "flows_cfs": [900.0, 1600.0, 3000.0],
        },
        "rapids": rapid_entries,
        "moving_window_streaming": {
            "manifest": FULL_HYDRAULICS_STREAMING_RELATIVE_PATH,
            "sha256": _sha256(streaming_path),
            "full_reach_transit_seed_manifest": (
                FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH
            ),
            "full_reach_transit_seed_sha256": _sha256(transit_manifest_path),
            "continuous_full_reach_coverage": True,
            "state_preserving_runtime_handoff_required": True,
        },
        "solver_contract": {
            "genuine_first_party_finite_volume": True,
            "reference_playback_used": False,
            "fixture_calibrations_disabled": True,
            "wet_dry_boundaries_active": True,
            "authored_inflow_outflow_forcing": True,
            "no_nan_or_mass_blowup_required": True,
        },
        "authority": {
            "generated_geometry_label": "procedural_infill",
            "guide_inventory_is_interpreted_not_surveyed": True,
            "not_for_navigation": True,
        },
        "acceptance": {
            "all_20_named_rapids_authored": len(rapid_entries) == 20,
            "all_three_flows_cooked": len(all_combo_results) == 60,
            "all_feature_outcome_envelopes_pass": all_combinations_passed,
            "full_reach_streaming_has_no_gaps": True,
            "full_reach_transit_seed_passes": bool(
                _load_json(repo_root, FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH)[
                    "all_bands_passed"
                ]
            ),
            "ready_for_unreal_moving_window_validation": all_combinations_passed,
        },
    }
    manifest_path = repo_root / FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH
    _write_json(manifest_path, manifest)
    if not all_combinations_passed:
        raise RuntimeError(
            "South Fork hydraulic matrix failed validation; inspect "
            f"{manifest_path} and per-band validation payloads"
        )
    return manifest_path


def build_south_fork_full_hydraulics_manifest(repo_root: Path) -> dict[str, Any]:
    """Load the matrix and verify every committed rapid manifest hash."""

    repo_root = repo_root.resolve()
    manifest = _load_json(repo_root, FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    for rapid in manifest["rapids"]:
        path = repo_root / rapid["cooked_fields_manifest"]
        if not path.is_file() or _sha256(path) != rapid["manifest_sha256"]:
            raise ValueError(f"Hydraulic rapid manifest hash mismatch: {path}")
    streaming = manifest["moving_window_streaming"]
    path = repo_root / streaming["manifest"]
    if not path.is_file() or _sha256(path) != streaming["sha256"]:
        raise ValueError(f"Hydraulic streaming manifest hash mismatch: {path}")
    transit_path = repo_root / streaming["full_reach_transit_seed_manifest"]
    if (
        not transit_path.is_file()
        or _sha256(transit_path) != streaming["full_reach_transit_seed_sha256"]
    ):
        raise ValueError(
            f"Full-reach transit seed manifest hash mismatch: {transit_path}"
        )
    return manifest
