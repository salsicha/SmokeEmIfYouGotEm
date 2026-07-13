"""Build sourced named-rapid editor markers and simulator review-run definitions."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


SOURCE_CATALOG_RELATIVE_PATH = "physics/data/real_world/named_rapid_source_catalog.json"
EDITOR_MARKERS_RELATIVE_PATH = "unreal/Content/RaftSim/River/named_rapid_editor_markers.json"
EDITOR_GEOMETRY_RELATIVE_PATH = "unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson"
SIMULATOR_RUNS_RELATIVE_PATH = (
    "unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json"
)

MILES_TO_METERS = 1609.344
FLOW_BANDS = ("low_review", "reference_review", "high_review")
REQUIRED_RIVERS = {
    "south_fork_american_chili_bar",
    "colorado_river_grand_canyon_rowing",
    "pacuare_river_costa_rica",
    "zambezi_batoka_gorge",
    "futaleufu_river_chile",
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not slug:
        raise ValueError(f"Cannot build an identifier from {value!r}")
    return slug


def load_source_catalog(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SOURCE_CATALOG_RELATIVE_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema") != "raftsim.real_world.named_rapid_source_catalog.v1":
        raise ValueError("Unexpected named-rapid source catalog schema")
    if catalog.get("status") != "review_baseline_not_guide_approved":
        raise ValueError("Named-rapid catalog must remain review-gated")
    if "link-only" not in catalog.get("rights_policy", "").lower():
        raise ValueError("Named-rapid sources must remain link-only")

    sources = catalog.get("sources", [])
    source_ids = {source["source_id"] for source in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Named-rapid source IDs must be unique")
    for source in sources:
        if not source["url"].startswith("https://"):
            raise ValueError(f"Source URL must use HTTPS: {source['source_id']}")
        if not source["rights_status"].startswith(("link_only", "government_source")):
            raise ValueError(f"Source is not rights-gated: {source['source_id']}")

    rivers = catalog.get("rivers", [])
    river_ids = {river["river_id"] for river in rivers}
    if river_ids != REQUIRED_RIVERS:
        raise ValueError(f"Named-rapid river set mismatch: {sorted(river_ids)}")

    feature_ids: set[str] = set()
    for river in rivers:
        if river["run_length_m"] <= 0:
            raise ValueError(f"Run length must be positive: {river['river_id']}")
        if not set(river["source_ids"]).issubset(source_ids):
            raise ValueError(f"Unknown source in {river['river_id']}")
        rapids = river.get("rapids", [])
        if not rapids:
            raise ValueError(f"No rapid records for {river['river_id']}")
        orders = [rapid["order"] for rapid in rapids]
        if orders != sorted(orders) or len(set(orders)) != len(orders):
            raise ValueError(f"Rapid order must be unique and downstream: {river['river_id']}")
        for rapid in rapids:
            feature_id = f"{river['river_id']}__{_slug(rapid['name'])}"
            if feature_id in feature_ids:
                raise ValueError(f"Duplicate rapid feature ID: {feature_id}")
            feature_ids.add(feature_id)
            if not rapid.get("feature_tags"):
                raise ValueError(f"Rapid has no feature tags: {feature_id}")
            if rapid.get("review_priority") not in {"medium", "high", "critical"}:
                raise ValueError(f"Invalid review priority: {feature_id}")


def _station_record(river: dict[str, Any], rapid: dict[str, Any]) -> dict[str, Any]:
    if "river_mile" in rapid:
        station_m = float(rapid["river_mile"]) * MILES_TO_METERS
        return {
            "station_m": round(station_m, 3),
            "station_kind": "published_river_mile_converted",
            "published_value": rapid["river_mile"],
            "published_unit": "river_mile",
            "production_authoritative": river["stationing_authority"] == "published_river_miles",
        }
    if "river_km" in rapid:
        return {
            "station_m": round(float(rapid["river_km"]) * 1000.0, 3),
            "station_kind": "published_river_kilometer_converted",
            "published_value": rapid["river_km"],
            "published_unit": "river_kilometer",
            "production_authoritative": True,
        }

    rapids = river["rapids"]
    station_m = river["run_length_m"] * rapid["order"] / (len(rapids) + 1)
    return {
        "station_m": round(station_m, 3),
        "station_kind": "provisional_downstream_order_interpolation",
        "published_value": rapid["order"],
        "published_unit": "downstream_order",
        "production_authoritative": False,
    }


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon_a, lat_a = map(math.radians, a)
    lon_b, lat_b = map(math.radians, b)
    d_lon = lon_b - lon_a
    d_lat = lat_b - lat_a
    h = math.sin(d_lat / 2.0) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(d_lon / 2.0) ** 2
    return 6371008.8 * 2.0 * math.asin(min(1.0, math.sqrt(h)))


def _load_route_samples(repo_root: Path, source: dict[str, Any]) -> list[tuple[float, float, float]]:
    path = repo_root / source["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if source["format"] == "route_stationing_json":
        return [
            (float(sample["station_m"]), float(sample["lon"]), float(sample["lat"]))
            for sample in payload["samples"]
        ]
    if source["format"] != "geojson_linestring":
        raise ValueError(f"Unsupported named-rapid geometry source format: {source['format']}")
    coordinates = payload["features"][0]["geometry"]["coordinates"]
    samples: list[tuple[float, float, float]] = []
    station_m = 0.0
    previous: tuple[float, float] | None = None
    for raw_lon, raw_lat, *_ in coordinates:
        point = (float(raw_lon), float(raw_lat))
        if previous is not None:
            station_m += _haversine_m(previous, point)
        samples.append((station_m, point[0], point[1]))
        previous = point
    return samples


def _project_station_to_candidate_geometry(
    repo_root: Path,
    river: dict[str, Any],
    station_m: float,
) -> dict[str, Any] | None:
    source = river.get("editor_geometry_source")
    if not source or source.get("binding_enabled") is not True:
        return None
    maximum_bind_station_m = float(source.get("maximum_bind_station_m", math.inf))
    if station_m > maximum_bind_station_m:
        return None
    samples = _load_route_samples(repo_root, source)
    if not samples or station_m < samples[0][0] or station_m > samples[-1][0]:
        return None
    for left, right in zip(samples, samples[1:]):
        if station_m > right[0]:
            continue
        span = max(right[0] - left[0], 1e-9)
        alpha = (station_m - left[0]) / span
        lon = left[1] + (right[1] - left[1]) * alpha
        lat = left[2] + (right[2] - left[2]) * alpha
        return {
            "type": "Point",
            "coordinates": [round(lon, 8), round(lat, 8)],
            "source_path": source["path"],
            "source_status": source["status"],
            "binding_method": "station_interpolation_on_review_gated_candidate_centerline",
            "production_authoritative": False,
        }
    return None


def _expected_outcomes(tags: list[str]) -> list[str]:
    tag_set = set(tags)
    outcomes = {"clean_line", "flush"}
    if any("surf" in tag or "wave" in tag for tag in tag_set):
        outcomes.update({"surf", "splash"})
    if any("hole" in tag or "pourover" in tag for tag in tag_set):
        outcomes.update({"surf", "retention", "release"})
    if any("pin" in tag or "wrap" in tag or "boulder" in tag or "rock" in tag for tag in tag_set):
        outcomes.update({"pin", "release"})
    if any("flip" in tag or "lateral" in tag or "wall" in tag for tag in tag_set):
        outcomes.add("flip")
    if any("portage" in tag for tag in tag_set):
        outcomes.add("portage")
    if any("swimmer" in tag for tag in tag_set):
        outcomes.add("swimmer_recovery")
    return sorted(outcomes)


def _flow_hypotheses(tags: list[str]) -> list[dict[str, str]]:
    tag_set = set(tags)
    has_hole = any("hole" in tag or "pourover" in tag for tag in tag_set)
    has_wave = any("wave" in tag for tag in tag_set)
    has_rock = any("rock" in tag or "boulder" in tag or "shelf" in tag for tag in tag_set)
    return [
        {
            "flow_band": "low_review",
            "hypothesis": (
                "Expose more rocks, shelves, and narrow slots; reduce water-feature scale but retain collision and pin review."
                if has_rock
                else "Reduce feature scale and expose shallow geometry; verify the rapid does not receive artificial high-flow behavior."
            ),
        },
        {
            "flow_band": "reference_review",
            "hypothesis": (
                "Test peak useful retention and clean-line versus contact-line outcomes; require footage and guide comparison."
                if has_hole
                else "Use the guide-reviewed reference line and compare raft timing, angle, acceleration, and recovery."
            ),
        },
        {
            "flow_band": "high_review",
            "hypothesis": (
                "Increase momentum and wave scale while testing whether the hydraulic washes out rather than becoming monotonically stickier."
                if has_hole
                else "Increase momentum, laterals, boils, and wave scale where supported; verify submerged hazards and recovery distance."
                if has_wave
                else "Increase downstream momentum and cover shallow geometry; do not invent hydraulics without source evidence."
            ),
        },
    ]


def build_editor_markers(catalog: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    validate_source_catalog(catalog)
    source_lookup = {source["source_id"]: source for source in catalog["sources"]}
    rivers: list[dict[str, Any]] = []
    for river in catalog["rivers"]:
        markers = []
        for rapid in river["rapids"]:
            feature_id = f"{river['river_id']}__{_slug(rapid['name'])}"
            station = _station_record(river, rapid)
            map_geometry = _project_station_to_candidate_geometry(
                repo_root,
                river,
                float(station["station_m"]),
            )
            markers.append(
                {
                    "feature_id": feature_id,
                    "display_name": rapid["name"],
                    "aliases": rapid.get("aliases", []),
                    "rapid_number": rapid.get("rapid_number"),
                    "downstream_order": rapid["order"],
                    "difficulty_label": rapid["class"],
                    "feature_tags": rapid["feature_tags"],
                    "review_priority": rapid["review_priority"],
                    "stationing": station,
                    "geometry_kind": "station_pin",
                    "editor_map_geometry": map_geometry,
                    "editor_map_geometry_status": (
                        "candidate_centerline_projection_not_exact"
                        if map_geometry is not None
                        else "unavailable_outside_current_candidate_centerline"
                    ),
                    "exact_geometry_status": "required_before_production",
                    "expected_outcomes": _expected_outcomes(rapid["feature_tags"]),
                    "flow_hypotheses": _flow_hypotheses(rapid["feature_tags"]),
                    "source_ids": river["source_ids"],
                    "guide_review_status": "required",
                    "solver_window_status": "not_authored",
                    "editor_color": (
                        "red" if rapid["review_priority"] == "critical" else "orange"
                        if rapid["review_priority"] == "high" else "yellow"
                    ),
                }
            )
        rivers.append(
            {
                "river_id": river["river_id"],
                "display_name": river["display_name"],
                "run_length_m": river["run_length_m"],
                "stationing_authority": river["stationing_authority"],
                "source_refs": [source_lookup[source_id] for source_id in river["source_ids"]],
                "marker_count": len(markers),
                "markers": markers,
            }
        )
    return {
        "schema": "raftsim.unreal.named_rapid_editor_markers.v1",
        "status": "editor_review_markers_ready_exact_geometry_and_guide_review_required",
        "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
        "production_promoted": False,
        "editor_contract": {
            "show_provisional_station_badge": True,
            "show_source_and_rights_panel": True,
            "show_flow_hypotheses": True,
            "show_expected_outcomes": True,
            "block_solver_window_export_without_exact_geometry": True,
            "block_gameplay_promotion_without_guide_review": True,
        },
        "rivers": rivers,
    }


def build_editor_geometry_geojson(editor_markers: dict[str, Any]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for river in editor_markers["rivers"]:
        for marker in river["markers"]:
            geometry = marker["editor_map_geometry"]
            if geometry is None:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": geometry["type"],
                        "coordinates": geometry["coordinates"],
                    },
                    "properties": {
                        "feature_id": marker["feature_id"],
                        "river_id": river["river_id"],
                        "display_name": marker["display_name"],
                        "difficulty_label": marker["difficulty_label"],
                        "review_priority": marker["review_priority"],
                        "station_m": marker["stationing"]["station_m"],
                        "station_kind": marker["stationing"]["station_kind"],
                        "geometry_status": marker["editor_map_geometry_status"],
                        "geometry_source": geometry["source_path"],
                        "geometry_source_status": geometry["source_status"],
                        "production_authoritative": False,
                        "guide_review_status": marker["guide_review_status"],
                    },
                }
            )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.unreal.named_rapid_editor_geometry.geojson.v1",
        "status": "candidate_centerline_projections_for_editor_review_not_exact_geometry",
        "production_promoted": False,
        "source_markers": EDITOR_MARKERS_RELATIVE_PATH,
        "feature_count": len(features),
        "features": features,
    }


def _line_definitions(marker: dict[str, Any]) -> list[dict[str, Any]]:
    tags = set(marker["feature_tags"])
    if any("mandatory" in tag and "portage" in tag for tag in tags):
        return [
            {
                "line_id": "mandatory_portage_control",
                "intent": "Verify the mandatory commercial-raft portage and reject any normal runnable-line binding for this hazard.",
                "expected_outcome": "portage",
                "guide_line_required": True,
            }
        ]
    lines = [
        {
            "line_id": "clean_reference",
            "intent": "Run the sourced or guide-reviewed clean line and measure timing, angle, acceleration, crew loading, and recovery.",
            "expected_outcome": "clean_line",
            "guide_line_required": True,
        }
    ]
    if marker["review_priority"] in {"high", "critical"}:
        lines.append(
            {
                "line_id": "bounded_feature_contact",
                "intent": "Deliberately contact the primary hydraulic or obstacle inside a bounded review run to test surf, flush, pin, release, flip, and swimmer consequences.",
                "expected_outcome": "feature_dependent",
                "guide_line_required": True,
            }
        )
    if any("portage" in tag for tag in tags):
        lines.append(
            {
                "line_id": "portage_control",
                "intent": "Verify the authored portage/scout decision and prevent normal gameplay from treating the hazard as a routine runnable line.",
                "expected_outcome": "portage",
                "guide_line_required": True,
            }
        )
    return lines


def build_simulator_review_runs(editor_markers: dict[str, Any]) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for river in editor_markers["rivers"]:
        control_mode = "manual_oar_rig" if river["river_id"] == "colorado_river_grand_canyon_rowing" else "guided_paddle_crew"
        voice_commands = control_mode == "guided_paddle_crew"
        for marker in river["markers"]:
            for flow_band in FLOW_BANDS:
                for line in _line_definitions(marker):
                    run_id = f"{marker['feature_id']}__{flow_band}__{line['line_id']}"
                    runs.append(
                        {
                            "run_id": run_id,
                            "river_id": river["river_id"],
                            "feature_id": marker["feature_id"],
                            "display_name": marker["display_name"],
                            "flow_band": flow_band,
                            "line_id": line["line_id"],
                            "line_intent": line["intent"],
                            "expected_outcome": line["expected_outcome"],
                            "control_mode": control_mode,
                            "voice_paddle_commands_enabled": voice_commands,
                            "crew_weight_distribution_enabled": True,
                            "swimmer_and_rescue_enabled": True,
                            "initial_conditions": {
                                "entry_station_offset_m": -120.0,
                                "entry_heading": "guide_line_required",
                                "entry_velocity": "sample_from_validated_cpp_window",
                                "crew_loading": "balanced_then_scripted_error_for_consequence_runs",
                            },
                            "required_overlays": [
                                "depth",
                                "velocity",
                                "froude",
                                "wet_dry_mask",
                                "feature_tags",
                                "raft_trajectory",
                                "contact_probes",
                                "crew_center_of_mass",
                                "conservation_deltas",
                            ],
                            "required_metrics": [
                                "entry_angle_error_deg",
                                "trajectory_cross_track_error_m",
                                "peak_roll_deg",
                                "peak_pitch_deg",
                                "crew_center_of_mass_shift_m",
                                "surf_or_retention_duration_s",
                                "pin_duration_s",
                                "release_success",
                                "flip_occurred",
                                "swimmer_count",
                                "rescue_time_s",
                                "mass_conservation_error",
                            ],
                            "platform_profiles": [
                                "desktop_high",
                                "desktop_scalable",
                                "console_quality",
                                "console_performance",
                                "handheld_low",
                            ],
                            "definition_status": "ready_for_window_binding",
                            "execution_status": "blocked_until_exact_geometry_validated_cpp_window_and_guide_line",
                        }
                    )
    return {
        "schema": "raftsim.unreal.named_rapid_simulator_review_runs.v1",
        "status": "review_run_definitions_ready_execution_evidence_pending",
        "production_promoted": False,
        "editor_markers": EDITOR_MARKERS_RELATIVE_PATH,
        "run_count": len(runs),
        "pass_policy": {
            "physics": "C++ water window passes analytic guardrails, GeoClaw parity where applicable, stitched conservation, and raft-coupling checks.",
            "behavior": "Guide-reviewed clean line is reproducible and bounded consequence lines produce flow-appropriate surf, flush, pin, release, flip, swimmer, and rescue outcomes.",
            "visual": "Water, foam, spray, wet banks, rocks, foliage, and lighting agree with rights-reviewed references at the recorded flow.",
            "platform": "The same authored rapid and outcome envelope survives all target scalability profiles without changing gameplay physics.",
        },
        "runs": runs,
    }


def write_named_rapid_review_assets(repo_root: Path) -> tuple[Path, Path, Path]:
    catalog = load_source_catalog(repo_root)
    markers = build_editor_markers(catalog, repo_root)
    geometry = build_editor_geometry_geojson(markers)
    runs = build_simulator_review_runs(markers)
    marker_path = repo_root / EDITOR_MARKERS_RELATIVE_PATH
    geometry_path = repo_root / EDITOR_GEOMETRY_RELATIVE_PATH
    run_path = repo_root / SIMULATOR_RUNS_RELATIVE_PATH
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    geometry_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(json.dumps(markers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    geometry_path.write_text(json.dumps(geometry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_path.write_text(json.dumps(runs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return marker_path, geometry_path, run_path
