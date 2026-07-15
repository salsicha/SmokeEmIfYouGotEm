"""Build the first source-recorded Chilko River production attachment."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import fmean, median
from typing import Any, Iterable


SCHEMA = "raftsim.chilko_source_attachment.v0"
RELATIVE_ROOT = Path("physics/data/real_world/chilko_river_bc")
CORRIDOR_BBOX = (-124.2, 51.6, -123.6, 52.1)
PUT_IN_SEED = (-124.10681, 51.69627)
TAKE_OUT_SEED = (-123.677222, 52.006944)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    value = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * 6_371_000.0 * math.asin(math.sqrt(value))


def _line_points(geometry: dict[str, Any]) -> Iterable[list[float]]:
    if geometry["type"] == "LineString":
        yield from geometry["coordinates"]
        return
    if geometry["type"] == "MultiLineString":
        for line in geometry["coordinates"]:
            yield from line
        return
    raise ValueError(f"unsupported FWA geometry type: {geometry['type']}")


def _nearest_fwa_vertex(source: dict[str, Any], seed: tuple[float, float]) -> dict[str, Any]:
    best: tuple[float, dict[str, Any], list[float]] | None = None
    for feature in source["features"]:
        for point in _line_points(feature["geometry"]):
            distance = _haversine_m(seed, (float(point[0]), float(point[1])))
            if best is None or distance < best[0]:
                best = (distance, feature, point)
    if best is None:
        raise ValueError("FWA source contains no route vertices")
    distance, feature, point = best
    properties = feature["properties"]
    return {
        "source_feature_id": feature["id"],
        "linear_feature_id": properties["LINEAR_FEATURE_ID"],
        "nearest_source_coordinate_wgs84": [point[0], point[1]],
        "seed_to_source_distance_m": round(distance, 3),
        "feature_downstream_route_measure_m": properties["DOWNSTREAM_ROUTE_MEASURE"],
        "feature_length_m": properties["LENGTH_METRE"],
        "feature_source": properties["FEATURE_SOURCE"],
        "edge_type": properties["EDGE_TYPE"],
        "stream_order": properties["STREAM_ORDER"],
    }


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _monthly_flow_summary(payload: dict[str, Any]) -> dict[str, Any]:
    by_month: dict[int, list[float]] = defaultdict(list)
    dates: list[str] = []
    for feature in payload["features"]:
        properties = feature["properties"]
        dates.append(properties["DATE"])
        discharge = properties.get("MONTHLY_MEAN_DISCHARGE")
        if discharge is not None:
            by_month[int(properties["DATE"][5:7])].append(float(discharge))

    climatology = []
    for month in range(1, 13):
        values = by_month[month]
        if not values:
            continue
        climatology.append(
            {
                "month": month,
                "sample_count": len(values),
                "minimum_m3_s": round(min(values), 3),
                "p10_m3_s": round(_percentile(values, 0.10), 3),
                "median_m3_s": round(median(values), 3),
                "mean_m3_s": round(fmean(values), 3),
                "p90_m3_s": round(_percentile(values, 0.90), 3),
                "maximum_m3_s": round(max(values), 3),
            }
        )
    return {
        "record_count": len(payload["features"]),
        "first_month": min(dates),
        "last_month": max(dates),
        "discharge_record_count": sum(len(values) for values in by_month.values()),
        "calendar_month_climatology": climatology,
    }


def _polygon_bounds(polygon: list[Any]) -> tuple[float, float, float, float]:
    points = [point for ring in polygon for point in ring]
    return (
        min(float(point[0]) for point in points),
        min(float(point[1]) for point in points),
        max(float(point[0]) for point in points),
        max(float(point[1]) for point in points),
    )


def _bounds_intersect(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def _hrdem_coverage_review(search: dict[str, Any], extents: list[dict[str, Any]]) -> dict[str, Any]:
    extent_records = []
    intersecting_polygon_count = 0
    for extent in extents:
        geometry = extent["geometry"]
        if geometry["type"] != "MultiPolygon":
            raise ValueError("expected NRCan HRDEM extent MultiPolygon")
        bounds = [_polygon_bounds(polygon) for polygon in geometry["coordinates"]]
        intersection_count = sum(_bounds_intersect(bound, CORRIDOR_BBOX) for bound in bounds)
        intersecting_polygon_count += intersection_count
        extent_records.append(
            {
                "project_name": extent["properties"]["name"],
                "polygon_count": len(bounds),
                "corridor_bbox_intersection_count": intersection_count,
                "polygon_bounds_wgs84": [list(bound) for bound in bounds],
            }
        )
    return {
        "stac_search_item_count": len(search["features"]),
        "actual_extent_intersection_count": intersecting_polygon_count,
        "decision": "no_confirmed_hrdem_lidar_coverage_use_mrdem30_fallback_and_continue_source_search",
        "warning": "STAC item bounding boxes are project envelopes and are not proof of local lidar coverage.",
        "extent_records": extent_records,
    }


def _full_bbox_coverage(item_bbox: list[float]) -> bool:
    return (
        item_bbox[0] <= CORRIDOR_BBOX[0]
        and item_bbox[1] <= CORRIDOR_BBOX[1]
        and item_bbox[2] >= CORRIDOR_BBOX[2]
        and item_bbox[3] >= CORRIDOR_BBOX[3]
    )


def build_chilko_source_attachment(repo_root: Path) -> list[Path]:
    root = repo_root.resolve() / RELATIVE_ROOT
    source = root / "source"

    fwa_path = source / "hydrography/fwa_chilko_river_segments.geojson"
    station_paths = {
        "08MA001": source / "hydrology/eccc_08MA001_station.json",
        "08MA002": source / "hydrology/eccc_08MA002_station.json",
    }
    monthly_paths = {
        "08MA001": source / "hydrology/eccc_08MA001_monthly_mean.json",
        "08MA002": source / "hydrology/eccc_08MA002_monthly_mean.json",
    }
    hrdem_search_path = source / "terrain/nrcan_hrdem_lidar_stac_search.json"
    hrdem_extent_paths = [
        source / "terrain/nrcan_hrdem_riverine_floodplain_extent.geojson",
        source / "terrain/nrcan_hrdem_bcts_chinook_kamloops_extent.geojson",
    ]
    mrdem_search_path = source / "terrain/nrcan_mrdem30_stac_search.json"
    sentinel_search_path = source / "imagery/sentinel2_summer_2025_stac_search.json"
    selected_preview_path = source / "imagery/sentinel2_20250825_selected_preview.jpg"
    cloud_screening_preview_path = source / "imagery/sentinel2_20250904_preview.jpg"

    required_sources = [
        fwa_path,
        *station_paths.values(),
        *monthly_paths.values(),
        hrdem_search_path,
        *hrdem_extent_paths,
        mrdem_search_path,
        sentinel_search_path,
        selected_preview_path,
        cloud_screening_preview_path,
    ]
    missing = [str(path.relative_to(repo_root)) for path in required_sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing Chilko source attachments: {missing}")

    fwa = _read_json(fwa_path)
    if len(fwa["features"]) != 545:
        raise ValueError("expected 545 named Chilko River FWA source features")
    if any(feature["properties"]["GNIS_NAME"] != "Chilko River" for feature in fwa["features"]):
        raise ValueError("FWA response contains a non-Chilko named feature")

    put_in_match = _nearest_fwa_vertex(fwa, PUT_IN_SEED)
    take_out_match = _nearest_fwa_vertex(fwa, TAKE_OUT_SEED)
    downstream_limit = take_out_match["feature_downstream_route_measure_m"]
    upstream_limit = (
        put_in_match["feature_downstream_route_measure_m"] + put_in_match["feature_length_m"]
    )
    selected_features = []
    for feature in fwa["features"]:
        properties = feature["properties"]
        start = properties["DOWNSTREAM_ROUTE_MEASURE"]
        end = start + properties["LENGTH_METRE"]
        if start < upstream_limit and end > downstream_limit:
            selected_features.append(feature)
    selected_features.sort(
        key=lambda feature: feature["properties"]["DOWNSTREAM_ROUTE_MEASURE"], reverse=True
    )

    route_candidate_path = root / "hydrography/lodge_to_taseko_junction_candidate_segments.geojson"
    route_review_path = root / "hydrography/route_source_review.json"
    route_candidate = {
        "type": "FeatureCollection",
        "schema": "raftsim.chilko.fwa_route_candidate.v0",
        "status": "official_source_segments_with_review_seed_limits_not_exact_route_approval",
        "source": str(fwa_path.relative_to(repo_root)),
        "candidate_limits": {
            "put_in_seed_wgs84": list(PUT_IN_SEED),
            "take_out_seed_wgs84": list(TAKE_OUT_SEED),
            "downstream_route_measure_m": downstream_limit,
            "upstream_route_measure_m": upstream_limit,
        },
        "features": selected_features,
    }
    _write_json(route_candidate_path, route_candidate)
    route_review = {
        "schema": "raftsim.chilko.route_source_review.v0",
        "status": "official_fwa_source_attached_exact_endpoints_and_stitched_centerline_blocked",
        "source_feature_count": len(fwa["features"]),
        "candidate_feature_count": len(selected_features),
        "candidate_feature_length_sum_m": round(
            sum(feature["properties"]["LENGTH_METRE"] for feature in selected_features), 3
        ),
        "put_in": {
            "name": "Chilko River Lodge",
            "seed_wgs84": list(PUT_IN_SEED),
            "seed_authority": "openstreetmap_discovery_seed_not_launch_geometry_authority",
            "exact_geometry_approved": False,
            "nearest_fwa_match": put_in_match,
        },
        "take_out": {
            "name": "Chilko-Taseko Junction",
            "seed_wgs84": list(TAKE_OUT_SEED),
            "seed_authority": "bc_geographical_names_taseko_river_mouth_discovery_seed",
            "exact_ramp_geometry_approved": False,
            "nearest_fwa_match": take_out_match,
        },
        "route_authority": {
            "source_geometry": "official_bc_freshwater_atlas_named_stream_network",
            "candidate_is_stitched_centerline": False,
            "candidate_is_bathymetry": False,
            "production_promotion_allowed": False,
            "required_next_review": [
                "confirm_put_in_permission_and_exact_launch_geometry_with_operator_and_land_authority",
                "confirm_take_out_ramp_and_confluence_geometry",
                "resolve_areal_stream_skeleton_choice_and_stitch_one_downstream_centerline",
                "compare_against_current_orthophoto_and_guide_gps",
                "attach_crs_accuracy_scale_and_update_metadata",
            ],
        },
    }
    _write_json(route_review_path, route_review)

    station_payloads = {station: _read_json(path) for station, path in station_paths.items()}
    monthly_payloads = {station: _read_json(path) for station, path in monthly_paths.items()}
    station_roles = {
        "08MA002": {
            "role": "primary_upstream_seasonality_and_timing_candidate",
            "limitation": "lake_outlet_is_upstream_of_put_in_and_does_not_include_reach_tributaries",
        },
        "08MA001": {
            "role": "downstream_context_and_routing_check_only",
            "limitation": (
                "station_is_downstream_of_taseko_confluence_and_cannot_define_"
                "pre_confluence_route_discharge"
            ),
        },
    }
    flow_context_path = root / "hydrology/seasonal_flow_context.json"
    stations = []
    for station_number in ("08MA002", "08MA001"):
        station_payload = station_payloads[station_number]
        if len(station_payload["features"]) != 1:
            raise ValueError(f"expected one station feature for {station_number}")
        feature = station_payload["features"][0]
        if feature["properties"]["STATION_NUMBER"] != station_number:
            raise ValueError(f"station response mismatch for {station_number}")
        stations.append(
            {
                "station_number": station_number,
                "station_name": feature["properties"]["STATION_NAME"],
                "coordinates_wgs84": feature["geometry"]["coordinates"],
                "status": feature["properties"]["STATUS_EN"],
                "real_time": bool(feature["properties"]["REAL_TIME"]),
                "reference_hydrometric_basin_network": bool(feature["properties"]["RHBN"]),
                "drainage_area_gross_km2": feature["properties"]["DRAINAGE_AREA_GROSS"],
                "vertical_datum": feature["properties"]["VERTICAL_DATUM"],
                **station_roles[station_number],
                "monthly_history": _monthly_flow_summary(monthly_payloads[station_number]),
            }
        )
    flow_context = {
        "schema": "raftsim.chilko.seasonal_flow_context.v0",
        "status": "official_monthly_history_attached_gameplay_bands_blocked",
        "units": "m3/s",
        "stations": stations,
        "gameplay_flow_bands": {
            "status": "blocked_pending_daily_window_routing_and_local_guide_review",
            "numeric_thresholds": [],
            "required_before_authoring": [
                "attach_daily_and_event_windows_for_reviewed_run_dates",
                "estimate_lag_and_tributary_change_from_08MA002_to_put_in",
                "separate_pre_confluence_chilko_flow_from_08MA001_taseko_influence",
                "review_low_reference_high_and_washout_behavior_with_local_guides",
            ],
        },
    }
    _write_json(flow_context_path, flow_context)

    hrdem_search = _read_json(hrdem_search_path)
    hrdem_extents = [_read_json(path) for path in hrdem_extent_paths]
    mrdem_search = _read_json(mrdem_search_path)
    hrdem_review = _hrdem_coverage_review(hrdem_search, hrdem_extents)
    if hrdem_review["actual_extent_intersection_count"] != 0:
        raise ValueError("HRDEM coverage decision must be reviewed because coverage now intersects Chilko")
    if len(mrdem_search["features"]) != 1:
        raise ValueError("expected one national MRDEM STAC item")
    terrain_review_path = root / "terrain/terrain_source_review.json"
    terrain_review = {
        "schema": "raftsim.chilko.terrain_source_review.v0",
        "status": "mrdem30_fallback_attached_higher_resolution_terrain_open",
        "corridor_search_bbox_wgs84": list(CORRIDOR_BBOX),
        "hrdem_lidar": hrdem_review,
        "mrdem30": {
            "stac_item_id": mrdem_search["features"][0]["id"],
            "collection": mrdem_search["features"][0]["collection"],
            "resolution_m": 30,
            "dtm_cog": mrdem_search["features"][0]["assets"]["dtm"]["href"],
            "source_cog": mrdem_search["features"][0]["assets"]["source"]["href"],
            "authority": "official_nrcan_fallback_not_rapid_scale_geometry",
            "clip_attached": False,
        },
        "production_promotion_allowed": False,
        "required_next_review": [
            "extract_and_verify_mrdem30_corridor_clip_and_per_pixel_source",
            "search_bc_data_catalogue_and_local_holdings_for_lidar_or_photogrammetry",
            "record_horizontal_and_vertical_datum_and_transform",
            "obtain_rapid_scale_terrain_or_reviewed_field_reconstruction",
        ],
    }
    _write_json(terrain_review_path, terrain_review)

    sentinel_search = _read_json(sentinel_search_path)
    full_coverage = [
        feature for feature in sentinel_search["features"] if _full_bbox_coverage(feature["bbox"])
    ]
    selected_scene = min(full_coverage, key=lambda feature: feature["properties"]["eo:cloud_cover"])
    if selected_scene["id"] != "S2C_10UDC_20250825_0_L2A":
        raise ValueError("selected Sentinel scene changed; review imagery decision")
    imagery_review_path = root / "imagery/imagery_source_review.json"
    imagery_review = {
        "schema": "raftsim.chilko.imagery_source_review.v0",
        "status": "cloud_screened_sentinel_preview_attached_production_corridor_clip_open",
        "search_bbox_wgs84": list(CORRIDOR_BBOX),
        "search_item_count": len(sentinel_search["features"]),
        "full_bbox_coverage_item_count": len(full_coverage),
        "selected_scene": {
            "item_id": selected_scene["id"],
            "datetime_utc": selected_scene["properties"]["datetime"],
            "platform": selected_scene["properties"]["platform"],
            "tile": selected_scene["properties"]["grid:code"],
            "cloud_cover_percent": selected_scene["properties"]["eo:cloud_cover"],
            "visual_cog": selected_scene["assets"]["visual"]["href"],
            "attached_preview": str(selected_preview_path.relative_to(repo_root)),
            "attached_preview_sha256": _sha256(selected_preview_path),
        },
        "rejected_cloud_screening_example": {
            "item_id": "S2C_10UDC_20250904_0_L2A",
            "attached_preview": str(cloud_screening_preview_path.relative_to(repo_root)),
            "reason": "broad_tile_preview_has_visible_haze_and_cloud_despite_acceptable_scene_level_metadata",
        },
        "rights": {
            "data": "Copernicus Sentinel data",
            "use_basis": "free_full_and_open_sentinel_data_subject_to_legal_notice",
            "terms_url": "https://dataspace.copernicus.eu/terms-and-conditions",
            "attribution": "Contains modified Copernicus Sentinel data (2025)",
            "third_party_portal_content_promoted": False,
        },
        "production_promotion_allowed": False,
        "required_next_review": [
            "extract_cloud_and_shadow_checked_corridor_tci_and_spectral_masks",
            "compare_against_rights_compatible_provincial_orthophoto",
            "review_water_color_snow_smoke_burn_and_vegetation_season",
            "record_processing_graph_and_output_hashes",
        ],
    }
    _write_json(imagery_review_path, imagery_review)

    land_review_path = root / "review/land_and_publication_source_review.json"
    land_review = {
        "schema": "raftsim.chilko.land_publication_source_review.v0",
        "status": "official_and_nation_source_links_recorded_consultation_and_publication_review_open",
        "sources": [
            {
                "source_id": "tsilhqotin_fisheries",
                "url": "https://tsilhqotin.ca/our-territory/fisheries/",
                "role": "watershed_stewardship_salmon_and_nation_context",
                "use": "link_only_review_context",
            },
            {
                "source_id": "tsilhqotin_declared_title_area",
                "url": "https://tsilhqotin.ca/governance/declared-title-area/",
                "role": "title_land_access_and_visiting_context",
                "use": "link_only_review_context",
            },
            {
                "source_id": "tsilhqotin_place_names",
                "url": "https://tsilhqotin.ca/our-nation/heritage/place-names/",
                "role": "place_name_and_cultural_publication_context",
                "use": "link_only_review_context",
            },
            {
                "source_id": "bc_chilko_taseko_recreation_site",
                "url": (
                    "https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/"
                    "forestry/bc-timber-sales/environmental-stewardship-sustainability/"
                    "forest-stewardship-plans/cariboo-chilcotin/"
                    "bcts_cariboo-chilcotin_fsp_828_final.pdf"
                ),
                "role": "official_recreation_site_and_access_source_lead",
                "use": "link_only_until_exact_site_geometry_and_current_access_review",
            },
        ],
        "policy": {
            "consultation_or_permission_complete": False,
            "detailed_access_or_sensitive_location_publication_allowed": False,
            "nation_media_or_text_downloaded": False,
            "nation_knowledge_used_as_geometry_authority": False,
            "required_before_public_release": [
                "review_title_land_access_and_publication_with_appropriate_tsilhqotin_contact",
                "confirm_operator_permission_and_put_in_access",
                "confirm_current_take_out_access_and_ramp_condition",
                "screen_cultural_ecological_salmon_and_rescue_sensitive_locations",
            ],
        },
    }
    _write_json(land_review_path, land_review)

    generated_paths = [
        route_candidate_path,
        route_review_path,
        flow_context_path,
        terrain_review_path,
        imagery_review_path,
        land_review_path,
    ]
    manifest_path = root / "source_manifest.json"
    manifest = {
        "schema": SCHEMA,
        "status": "first_official_source_attachment_complete_production_corridor_blocked",
        "generated_on": "2026-07-14",
        "river_id": "chilko_river_lava_canyon",
        "reach": {
            "put_in": "Chilko River Lodge",
            "take_out": "Chilko-Taseko Junction",
            "exact_endpoint_geometry_approved": False,
            "corridor_search_bbox_wgs84": list(CORRIDOR_BBOX),
        },
        "source_records": [
            {
                "source_id": "bc_freshwater_atlas_chilko_named_stream",
                "authority": "official_provincial_hydrography",
                "license": "Open Government Licence - British Columbia",
                "url": "https://openmaps.gov.bc.ca/geo/pub/WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP/ows",
                "artifact": str(fwa_path.relative_to(repo_root)),
                "sha256": _sha256(fwa_path),
            },
            {
                "source_id": "eccc_hydrometric_historical_data",
                "authority": "official_federal_hydrometric_archive",
                "license": "Open Government Licence - Canada",
                "url": "https://api.weather.gc.ca/collections/hydrometric-monthly-mean/",
                "artifacts": [
                    str(path.relative_to(repo_root))
                    for path in (*station_paths.values(), *monthly_paths.values())
                ],
                "sha256": {
                    str(path.relative_to(repo_root)): _sha256(path)
                    for path in (*station_paths.values(), *monthly_paths.values())
                },
            },
            {
                "source_id": "nrcan_canelevation",
                "authority": "official_federal_elevation_catalog",
                "license": "Open Government Licence - Canada",
                "url": "https://datacube.services.geo.ca/stac/api/",
                "artifacts": [
                    str(path.relative_to(repo_root))
                    for path in (hrdem_search_path, *hrdem_extent_paths, mrdem_search_path)
                ],
                "sha256": {
                    str(path.relative_to(repo_root)): _sha256(path)
                    for path in (hrdem_search_path, *hrdem_extent_paths, mrdem_search_path)
                },
            },
            {
                "source_id": "copernicus_sentinel2_l2a_earth_search",
                "authority": "copernicus_data_via_public_stac_mirror",
                "license": "Copernicus Sentinel Data Legal Notice",
                "url": "https://earth-search.aws.element84.com/v1/",
                "artifacts": [
                    str(path.relative_to(repo_root))
                    for path in (
                        sentinel_search_path,
                        selected_preview_path,
                        cloud_screening_preview_path,
                    )
                ],
                "sha256": {
                    str(path.relative_to(repo_root)): _sha256(path)
                    for path in (
                        sentinel_search_path,
                        selected_preview_path,
                        cloud_screening_preview_path,
                    )
                },
            },
        ],
        "generated_artifacts": [
            {
                "path": str(path.relative_to(repo_root)),
                "sha256": _sha256(path),
            }
            for path in generated_paths
        ],
        "promotion_gates": {
            "source_attachment_complete": True,
            "production_corridor_complete": False,
            "exact_route_and_endpoints": False,
            "rapid_scale_terrain": False,
            "numeric_flow_bands": False,
            "named_rapid_stationing": False,
            "guide_review": False,
            "land_and_publication_review": False,
            "lifelike_unreal_capture": False,
        },
    }
    _write_json(manifest_path, manifest)
    return [*generated_paths, manifest_path]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    for path in build_chilko_source_attachment(repo_root):
        print(path.relative_to(repo_root))


if __name__ == "__main__":
    main()
