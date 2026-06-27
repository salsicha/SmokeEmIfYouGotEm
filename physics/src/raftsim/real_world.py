"""Real-world river content helpers for source manifests and 2.5D seeds."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

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
from .schema_versions import SOURCE_MANIFEST_SCHEMA_VERSION

DataCategory = Literal["elevation", "hydrography", "imagery", "gauge", "guide_reference", "field_media"]
DifficultyPreset = Literal["beginner", "intermediate", "advanced", "expert"]
SourceStatus = Literal["planned", "metadata_ready", "downloaded", "derived", "reviewed"]

SOURCE_MANIFEST_FILE = "source_manifest.json"
DISCHARGE_CFS_TO_M3S = 0.028316846592


@dataclass(frozen=True, slots=True)
class BoundsWGS84:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def to_json_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CandidateRiverSection:
    river_id: str
    river_name: str
    section_id: str
    section_name: str
    region: str
    country: str
    bounds_wgs84: BoundsWGS84
    difficulty_range: tuple[str, ...]
    playable_reason: str
    data_priorities: tuple[str, ...]
    gauge_candidates: tuple[str, ...] = ()
    notes: str = ""

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["bounds_wgs84"] = self.bounds_wgs84.to_json_dict()
        return data


@dataclass(frozen=True, slots=True)
class SourceCatalogEntry:
    source_id: str
    category: DataCategory
    provider: str
    title: str
    url: str
    license_or_terms: str
    attribution: str
    access_notes: str
    use_in_pipeline: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RemoteFetchSpec:
    fetch_id: str
    category: DataCategory
    source_id: str
    url: str
    target_artifact: str
    status: SourceStatus
    notes: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CenterlineStation:
    station_m: float
    lon: float
    lat: float
    elevation_m: float
    channel_width_m: float
    roughness_indicator: float
    boulder_density: float
    imagery_whitewater_texture: float
    bend_score: float
    guide_note_score: float = 0.0
    access_score: float = 0.0

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ChannelIndicator:
    station_m: float
    lon: float
    lat: float
    elevation_m: float
    channel_width_m: float
    left_bank_offset_m: float
    right_bank_offset_m: float
    gradient: float
    constriction_score: float
    roughness_score: float
    rapid_score: float
    signals: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RapidCandidate:
    rapid_id: str
    start_station_m: float
    end_station_m: float
    peak_station_m: float
    score: float
    suggested_labels: tuple[str, ...]
    signals: tuple[str, ...]
    confidence: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RapidReviewLabel:
    label: str
    category: str
    description: str
    solver_tags: tuple[str, ...]
    requires_human_review: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FlowBand:
    flow_band: str
    season: str
    percentile_range: tuple[float, float]
    discharge_cfs: float
    stage_ft: float | None
    runnable: bool
    notes: str
    confidence: float

    @property
    def discharge_m3s(self) -> float:
        return self.discharge_cfs * DISCHARGE_CFS_TO_M3S

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["discharge_m3s"] = self.discharge_m3s
        return data


@dataclass(frozen=True, slots=True)
class PlayerSelection:
    region: str
    river_id: str
    section_id: str
    season: str
    flow_band: str
    difficulty: DifficultyPreset
    raft_setup: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SolverParameterPreset:
    selection: PlayerSelection
    boundary_inflow_m3s: float
    outflow_stage_bias_m: float
    initial_depth_m: float
    downstream_velocity_mps: float
    downstream_momentum_scale: float
    roughness_manning_n: float
    aeration_turbulence_scale: float
    hole_retention_strength: float
    wave_train_strength: float
    eddy_line_shear: float
    boil_strength: float
    shallow_hazard_threshold_m: float
    hazard_activation_scale: float
    raft_drag_coefficient_scale: float
    paddle_catch_scale: float
    damping_scale: float
    confidence_score: float
    notes: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "selection": self.selection.to_json_dict(),
            **{key: value for key, value in asdict(self).items() if key != "selection"},
        }


@dataclass(frozen=True, slots=True)
class RealWorldCorridorPackage:
    section: CandidateRiverSection
    source_manifest: dict[str, object]
    centerline: tuple[CenterlineStation, ...]
    indicators: tuple[ChannelIndicator, ...]
    rapid_candidates: tuple[RapidCandidate, ...]
    flow_bands: tuple[FlowBand, ...]
    player_selections: tuple[PlayerSelection, ...]
    unreal_ready_artifacts: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "section": self.section.to_json_dict(),
            "source_manifest": self.source_manifest,
            "centerline": [station.to_json_dict() for station in self.centerline],
            "indicators": [indicator.to_json_dict() for indicator in self.indicators],
            "rapid_candidates": [candidate.to_json_dict() for candidate in self.rapid_candidates],
            "flow_bands": [band.to_json_dict() for band in self.flow_bands],
            "player_selections": [selection.to_json_dict() for selection in self.player_selections],
            "unreal_ready_artifacts": self.unreal_ready_artifacts,
        }


def default_candidate_river_inventory() -> tuple[CandidateRiverSection, ...]:
    """Return the first-pass river inventory for real-world playable sections."""

    return (
        CandidateRiverSection(
            river_id="american_south_fork",
            river_name="South Fork American River",
            section_id="chili_bar_to_coloma",
            section_name="Chili Bar to Coloma",
            region="California Sierra Nevada",
            country="US",
            bounds_wgs84=BoundsWGS84(-120.90, 38.74, -120.72, 38.83),
            difficulty_range=("class_ii", "class_iii"),
            playable_reason="Commercially important training-to-intermediate run with clear access, named rapids, gauge context, and varied channel geometry.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "nwis_gauge_11445500", "osm_access"),
            gauge_candidates=("USGS 11445500 South Fork American River near Lotus, CA",),
            notes="Representative Milestone 9 seed section; coordinates are planning bounds and must be verified before production extraction.",
        ),
        CandidateRiverSection(
            river_id="youghiogheny_lower",
            river_name="Youghiogheny River",
            section_id="ohiopyle_to_bruner_run",
            section_name="Lower Yough",
            region="Pennsylvania Laurel Highlands",
            country="US",
            bounds_wgs84=BoundsWGS84(-79.53, 39.83, -79.43, 39.91),
            difficulty_range=("class_iii", "class_iv"),
            playable_reason="Classic technical pool-drop section with many named rapids and strong guide/reference availability.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "nwis_gauge_search", "guide_reference_review"),
            gauge_candidates=("USGS/NWIS Ohiopyle-area gauge search",),
        ),
        CandidateRiverSection(
            river_id="arkansas_browns_canyon",
            river_name="Arkansas River",
            section_id="browns_canyon",
            section_name="Browns Canyon",
            region="Colorado Rockies",
            country="US",
            bounds_wgs84=BoundsWGS84(-106.15, 38.67, -105.95, 38.83),
            difficulty_range=("class_iii", "class_iv"),
            playable_reason="High-value mountain whitewater corridor with seasonal snowmelt variability and strong public-land geodata coverage.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "nwis_gauge_search", "seasonal_snowmelt_context"),
            gauge_candidates=("USGS/NWIS Arkansas River Browns Canyon-area gauge search",),
        ),
        CandidateRiverSection(
            river_id="nantahala",
            river_name="Nantahala River",
            section_id="nantahala_gorge",
            section_name="Nantahala Gorge",
            region="North Carolina Appalachians",
            country="US",
            bounds_wgs84=BoundsWGS84(-83.72, 35.27, -83.55, 35.36),
            difficulty_range=("class_ii", "class_iii"),
            playable_reason="Accessible training river with repeatable dam-release flows, narrow gorge banks, and useful beginner/intermediate difficulty mapping.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "release_schedule_research", "osm_access"),
            gauge_candidates=("USGS/NWIS Nantahala Gorge-area gauge search",),
        ),
        CandidateRiverSection(
            river_id="new_river_gorge",
            river_name="New River",
            section_id="new_river_gorge",
            section_name="New River Gorge",
            region="West Virginia Appalachians",
            country="US",
            bounds_wgs84=BoundsWGS84(-81.15, 37.78, -80.95, 38.08),
            difficulty_range=("class_iii", "class_iv"),
            playable_reason="Large-volume river with iconic rapids, broad flow ranges, canyon visuals, and strong future UE5 photoreal corridor value.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "nwis_gauge_search", "rapid_guide_reference_review"),
            gauge_candidates=("USGS/NWIS New River Gorge-area gauge search",),
        ),
        CandidateRiverSection(
            river_id="gauley_upper",
            river_name="Gauley River",
            section_id="upper_gauley",
            section_name="Upper Gauley",
            region="West Virginia Appalachians",
            country="US",
            bounds_wgs84=BoundsWGS84(-80.96, 38.19, -80.82, 38.27),
            difficulty_range=("class_iv", "class_v"),
            playable_reason="Expert-flow stretch with release-driven seasonal difficulty, powerful hydraulics, and future high-consequence validation value.",
            data_priorities=("3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "release_schedule_research", "nwis_gauge_search"),
            gauge_candidates=("USGS/NWIS Gauley River release/gauge search",),
        ),
    )


def default_source_catalog() -> tuple[SourceCatalogEntry, ...]:
    """Return source availability and licensing notes for Milestone 9 planning."""

    return (
        SourceCatalogEntry(
            source_id="usgs_3dep",
            category="elevation",
            provider="USGS",
            title="3D Elevation Program (3DEP)",
            url="https://www.usgs.gov/3d-elevation-program",
            license_or_terms="U.S. federal source; treat as public-domain geospatial data unless a product-specific notice says otherwise.",
            attribution="Credit USGS 3D Elevation Program and preserve dataset/product identifiers in source manifests.",
            access_notes="Use The National Map, 3DEP services, or state lidar portals for DEM/lidar tiles.",
            use_in_pipeline=("terrain_dem", "gradient", "banks", "cross_sections", "roughness_indicators"),
        ),
        SourceCatalogEntry(
            source_id="usgs_3dhp_nhd",
            category="hydrography",
            provider="USGS",
            title="3D Hydrography Program, NHD, and NHDPlus",
            url="https://www.usgs.gov/3d-hydrography-program",
            license_or_terms="U.S. federal source; preserve attribution and confirm product-specific terms.",
            attribution="Credit USGS 3D Hydrography Program, NHD, or NHDPlus as applicable.",
            access_notes="Use 3DHP where available; fall back to NHD/NHDPlus flowlines and catchments for older coverage.",
            use_in_pipeline=("centerline", "drainage_context", "banks_seed", "gauge_transfer_context"),
        ),
        SourceCatalogEntry(
            source_id="usgs_tnm",
            category="elevation",
            provider="USGS",
            title="The National Map",
            url="https://apps.nationalmap.gov/tnmaccess/",
            license_or_terms="U.S. federal access portal; individual products keep their own metadata and attribution.",
            attribution="Credit source product providers listed by The National Map download metadata.",
            access_notes="Inventory and download elevation, hydrography, and base map products by bounding box.",
            use_in_pipeline=("source_discovery", "download_metadata", "source_manifest"),
        ),
        SourceCatalogEntry(
            source_id="usgs_nwis",
            category="gauge",
            provider="USGS",
            title="Water Services and NWIS",
            url="https://waterservices.usgs.gov/",
            license_or_terms="U.S. federal hydrologic data; cite USGS Water Data for the Nation and site IDs.",
            attribution="Credit USGS Water Data for the Nation / NWIS and record gauge site, parameter code, and retrieval date.",
            access_notes="Use parameter 00060 for discharge and 00065 for stage when available.",
            use_in_pipeline=("gauge_history", "flow_percentiles", "season_windows", "gauge_transfer_function"),
        ),
        SourceCatalogEntry(
            source_id="noaa_nwps_nwm",
            category="gauge",
            provider="NOAA/NWS",
            title="National Water Prediction Service and National Water Model context",
            url="https://water.noaa.gov/",
            license_or_terms="Public forecast/model products; cite NOAA/NWS/NWPS and verify service-specific use notes.",
            attribution="Credit NOAA National Water Prediction Service / National Water Model for modeled flow context.",
            access_notes="Use as forecast/model context, not as sole validation truth for historical runnable bands.",
            use_in_pipeline=("forecast_context", "modeled_reach_flow", "seasonal_context"),
        ),
        SourceCatalogEntry(
            source_id="usgs_streamstats",
            category="gauge",
            provider="USGS",
            title="StreamStats",
            url="https://www.usgs.gov/streamstats",
            license_or_terms="U.S. federal analysis service; cite USGS StreamStats and preserve report metadata.",
            attribution="Credit USGS StreamStats for basin characteristics and estimated streamflow statistics.",
            access_notes="Use for ungauged or transfer-function context; flag lower confidence than direct gauge history.",
            use_in_pipeline=("basin_characteristics", "ungauged_flow_estimates", "confidence_scoring"),
        ),
        SourceCatalogEntry(
            source_id="usda_naip",
            category="imagery",
            provider="USDA Farm Service Agency",
            title="NAIP aerial imagery",
            url="https://www.fsa.usda.gov/resources/aerial-photography",
            license_or_terms="Public U.S. aerial imagery source; verify product year/portal terms and attribution before redistribution.",
            attribution="Credit USDA/FSA NAIP imagery, acquisition year, and tile identifiers.",
            access_notes="Use for water masks, exposed rocks, banks, access points, vegetation, foam texture, and visual reference.",
            use_in_pipeline=("imagery_masks", "foam_texture", "boulder_density", "banks", "access_points"),
        ),
        SourceCatalogEntry(
            source_id="osm",
            category="hydrography",
            provider="OpenStreetMap contributors",
            title="OpenStreetMap supplemental map data",
            url="https://www.openstreetmap.org/copyright",
            license_or_terms="ODbL; requires attribution and care with database derivatives and share-alike obligations.",
            attribution="Credit OpenStreetMap contributors where OSM data is used.",
            access_notes="Use mostly for access roads, trails, bridges, named features, land use, and supplemental hydrography.",
            use_in_pipeline=("access_points", "roads_trails", "bridges", "named_features", "review_context"),
        ),
        SourceCatalogEntry(
            source_id="guide_references",
            category="guide_reference",
            provider="Guidebooks, outfitters, public agency pages, and reviewed local references",
            title="Human rapid and season references",
            url="source_manifest://guide_references",
            license_or_terms="Do not copy protected guidebook text or photos into the repo; record citations, page/URL pointers, and derived review notes only.",
            attribution="Credit reference title/author/URL where licenses allow; keep internal notes separate from redistributable assets.",
            access_notes="Use for named rapids, hazards, portages, access, commercial season, and difficulty calibration.",
            use_in_pipeline=("rapid_names", "hazards", "season_windows", "difficulty_mapping", "review_labels"),
        ),
        SourceCatalogEntry(
            source_id="field_media",
            category="field_media",
            provider="Project field capture",
            title="Field photos, drone video, audio, GPS, and notes",
            url="source_manifest://field_media",
            license_or_terms="Require explicit project-owned or licensed rights, model/property releases where applicable, and redistribution notes.",
            attribution="Credit capture crew and rights owner according to media release.",
            access_notes="Use for validation and photoreal/audio references after permissions are complete.",
            use_in_pipeline=("visual_reference", "audio_reference", "rapid_review", "validation_media"),
        ),
    )


def south_fork_american_fetch_specs() -> tuple[RemoteFetchSpec, ...]:
    bbox = "-120.90,38.74,-120.72,38.83"
    return (
        RemoteFetchSpec(
            fetch_id="sfa_3dep_dem",
            category="elevation",
            source_id="usgs_3dep",
            url=f"https://apps.nationalmap.gov/tnmaccess/api/products?datasets=Digital%20Elevation%20Model%20(DEM)&bbox={bbox}",
            target_artifact="terrain/3dep_dem_tiles",
            status="metadata_ready",
            notes="Representative bounding-box query for DEM discovery; production pull should pick highest-resolution 3DEP/state lidar product with metadata.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_3dhp_nhd_flowlines",
            category="hydrography",
            source_id="usgs_3dhp_nhd",
            url=f"https://apps.nationalmap.gov/tnmaccess/api/products?datasets=National%20Hydrography%20Dataset%20(NHD)&bbox={bbox}",
            target_artifact="hydrography/nhd_or_3dhp_flowlines",
            status="metadata_ready",
            notes="Use 3DHP if available for the bbox; otherwise use NHD/NHDPlus flowlines and catchments.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_osm_access",
            category="hydrography",
            source_id="osm",
            url="https://overpass-api.de/api/interpreter",
            target_artifact="hydrography/osm_access_bridges_named_features.geojson",
            status="planned",
            notes="Overpass query should fetch river way, roads, trails, bridges, parking/access points, and named nearby features within the bbox.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_naip_imagery",
            category="imagery",
            source_id="usda_naip",
            url=f"https://tnmaccess.nationalmap.gov/api/v1/products?datasets=NAIP%20Plus&bbox={bbox}",
            target_artifact="imagery/naip_tiles",
            status="planned",
            notes="Use most recent leaf-on/low-shadow NAIP where available, then compare with historic imagery at known gauge values.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_nwis_daily_discharge",
            category="gauge",
            source_id="usgs_nwis",
            url="https://waterservices.usgs.gov/nwis/dv/?format=json&sites=11445500&parameterCd=00060&startDT=2000-01-01",
            target_artifact="hydrology/usgs_11445500_daily_discharge.json",
            status="metadata_ready",
            notes="Daily discharge query for preliminary flow percentiles. Add instantaneous values and stage parameter 00065 when building final presets.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_nwps_nwm_context",
            category="gauge",
            source_id="noaa_nwps_nwm",
            url="https://water.noaa.gov/",
            target_artifact="hydrology/noaa_nwps_nwm_context.json",
            status="planned",
            notes="Link NOAA/NWPS/NWM reach context after the gauge/COMID mapping is verified.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_streamstats_context",
            category="gauge",
            source_id="usgs_streamstats",
            url="https://www.usgs.gov/streamstats",
            target_artifact="hydrology/streamstats_basin_context.json",
            status="planned",
            notes="Use for drainage area and transfer-function context; keep lower confidence than direct gauge observations.",
        ),
    )


def build_source_manifest(section: CandidateRiverSection | None = None) -> dict[str, object]:
    """Build the source_manifest.json payload for a representative section."""

    target = section or south_fork_american_section()
    return {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "manifest_id": f"{target.river_id}.{target.section_id}.source_manifest.v0",
        "river_id": target.river_id,
        "section_id": target.section_id,
        "section_name": target.section_name,
        "bounds_wgs84": target.bounds_wgs84.to_json_dict(),
        "coordinate_reference_systems": {
            "source": "EPSG:4326",
            "working": "local projected CRS selected per section at extraction time",
            "solver": "local meters: x downstream, y river-left positive",
            "unreal": "georeferenced corridor transform derived from the working CRS",
        },
        "sources": [source.to_json_dict() for source in default_source_catalog()],
        "remote_fetches": [fetch.to_json_dict() for fetch in south_fork_american_fetch_specs()],
        "artifacts": {
            "elevation": ["terrain/3dep_dem_tiles", "terrain/solver_bed_grid.npy"],
            "hydrography": ["hydrography/centerline.geojson", "hydrography/banks.geojson", "hydrography/cross_sections.geojson"],
            "imagery": ["imagery/naip_tiles", "imagery/water_mask.tif", "imagery/foam_texture_mask.tif"],
            "gauges": ["hydrology/usgs_11445500_daily_discharge.json", "hydrology/flow_presets.json"],
            "guide_references": ["review/guide_reference_index.json", "review/rapid_review_labels.json"],
            "field_media": ["field_media/README.md"],
            "solver": ["scenario/scenario.json", "scenario/bed.npy", "scenario/initial_state.npz"],
            "validation": ["validation_matrix.json"],
            "unreal": ["unreal/corridor_package_manifest.json"],
        },
        "provenance": {
            "generated_by": "raftsim.real_world.build_source_manifest",
            "processing_version": "milestone_9_seed.v0",
            "review_status": "seed_data_needs_human_geospatial_review",
            "redistribution_notes": "Do not redistribute third-party imagery, guidebook text, or field media unless the manifest records explicit rights.",
        },
        "confidence": {
            "overall": 0.35,
            "terrain": 0.45,
            "hydrography": 0.40,
            "imagery": 0.30,
            "hydrology": 0.35,
            "rapid_labels": 0.25,
        },
    }


def south_fork_american_section() -> CandidateRiverSection:
    return default_candidate_river_inventory()[0]


def south_fork_american_centerline_stations() -> tuple[CenterlineStation, ...]:
    """Return a tiny fixture-like station set for the representative data package.

    Values are intentionally coarse seed data. Production data must replace these
    with extracted GIS/lidar/imagery measurements recorded in the source manifest.
    """

    return (
        CenterlineStation(0.0, -120.8730, 38.7600, 304.0, 26.0, 0.22, 0.18, 0.10, 0.12, access_score=0.70),
        CenterlineStation(450.0, -120.8650, 38.7640, 299.2, 24.0, 0.28, 0.25, 0.18, 0.28),
        CenterlineStation(920.0, -120.8580, 38.7685, 291.0, 18.0, 0.62, 0.55, 0.55, 0.44, guide_note_score=0.60),
        CenterlineStation(1370.0, -120.8500, 38.7730, 286.0, 30.0, 0.24, 0.20, 0.16, 0.25),
        CenterlineStation(1880.0, -120.8420, 38.7765, 278.0, 17.0, 0.70, 0.68, 0.62, 0.38, guide_note_score=0.55),
        CenterlineStation(2360.0, -120.8330, 38.7800, 274.8, 33.0, 0.18, 0.16, 0.12, 0.18),
        CenterlineStation(2920.0, -120.8235, 38.7850, 265.2, 20.0, 0.58, 0.50, 0.44, 0.70, guide_note_score=0.45),
        CenterlineStation(3470.0, -120.8140, 38.7900, 258.0, 23.0, 0.36, 0.32, 0.28, 0.34),
        CenterlineStation(4050.0, -120.8040, 38.7960, 249.0, 19.0, 0.66, 0.58, 0.58, 0.60, guide_note_score=0.50),
        CenterlineStation(4630.0, -120.7930, 38.8030, 244.5, 29.0, 0.26, 0.22, 0.18, 0.20),
        CenterlineStation(5200.0, -120.7820, 38.8100, 238.0, 27.0, 0.30, 0.26, 0.20, 0.16, access_score=0.60),
    )


def extract_channel_indicators(stations: tuple[CenterlineStation, ...]) -> tuple[ChannelIndicator, ...]:
    """Derive stationing, banks, width, gradient, constriction, and roughness indicators."""

    if len(stations) < 3:
        raise ValueError("At least three centerline stations are required.")
    ordered = tuple(sorted(stations, key=lambda station: station.station_m))
    station_values = np.asarray([station.station_m for station in ordered], dtype=np.float64)
    elevations = np.asarray([station.elevation_m for station in ordered], dtype=np.float64)
    widths = np.asarray([station.channel_width_m for station in ordered], dtype=np.float64)
    if np.any(np.diff(station_values) <= 0.0):
        raise ValueError("Centerline station distances must be strictly increasing.")

    median_width = float(np.median(widths))
    indicators: list[ChannelIndicator] = []
    for index, station in enumerate(ordered):
        previous_index = max(0, index - 1)
        next_index = min(len(ordered) - 1, index + 1)
        distance = max(station_values[next_index] - station_values[previous_index], 1.0)
        gradient = max(0.0, (elevations[previous_index] - elevations[next_index]) / distance)

        local_widths = widths[max(0, index - 2) : min(len(widths), index + 3)]
        local_reference_width = max(float(np.percentile(local_widths, 75)), median_width, 1.0)
        constriction = _clamp01((local_reference_width - station.channel_width_m) / local_reference_width)

        roughness = _clamp01(
            0.34 * station.roughness_indicator
            + 0.24 * station.boulder_density
            + 0.20 * station.imagery_whitewater_texture
            + 0.12 * station.bend_score
            + 0.10 * station.guide_note_score
        )
        gradient_score = _clamp01(gradient / 0.020)
        rapid_score = _clamp01(
            0.33 * gradient_score
            + 0.22 * constriction
            + 0.20 * roughness
            + 0.12 * station.imagery_whitewater_texture
            + 0.08 * station.boulder_density
            + 0.05 * station.guide_note_score
        )
        signals = _indicator_signals(station, gradient, constriction, roughness, rapid_score)
        half_width = station.channel_width_m * 0.5
        indicators.append(
            ChannelIndicator(
                station_m=station.station_m,
                lon=station.lon,
                lat=station.lat,
                elevation_m=station.elevation_m,
                channel_width_m=station.channel_width_m,
                left_bank_offset_m=half_width,
                right_bank_offset_m=-half_width,
                gradient=gradient,
                constriction_score=constriction,
                roughness_score=roughness,
                rapid_score=rapid_score,
                signals=signals,
            )
        )
    return tuple(indicators)


def identify_candidate_rapids(
    indicators: tuple[ChannelIndicator, ...],
    *,
    threshold: float = 0.42,
) -> tuple[RapidCandidate, ...]:
    """Cluster rapid candidates from slope, constriction, roughness, imagery, and guide signals."""

    if not indicators:
        return ()
    ordered = tuple(sorted(indicators, key=lambda indicator: indicator.station_m))
    candidates: list[RapidCandidate] = []
    active: list[ChannelIndicator] = []
    for indicator in ordered:
        if indicator.rapid_score >= threshold:
            active.append(indicator)
            continue
        if active:
            candidates.append(_rapid_candidate_from_cluster(len(candidates) + 1, active))
            active = []
    if active:
        candidates.append(_rapid_candidate_from_cluster(len(candidates) + 1, active))
    return tuple(candidates)


def default_manual_rapid_review_labels() -> tuple[RapidReviewLabel, ...]:
    return (
        RapidReviewLabel("pool", "water_state", "Recovery or staging pool with low gradient and lower velocity.", ("pool", "recovery")),
        RapidReviewLabel("riffle", "water_state", "Shallow rough water with small waves and moderate roughness.", ("shallow", "roughness")),
        RapidReviewLabel("wave_train", "hydraulic", "Series of standing waves aligned with the main tongue.", ("wave_train", "aeration")),
        RapidReviewLabel("hole", "hydraulic", "Recirculating hydraulic or keeper-like feature needing raft interaction tuning.", ("hole", "retention")),
        RapidReviewLabel("ledge", "bedform", "Abrupt bed drop or shelf that can form a hydraulic or lateral wave.", ("ledge", "bed_step")),
        RapidReviewLabel("lateral", "hydraulic", "Sideways wave or current crossing the main current.", ("lateral", "cross_current")),
        RapidReviewLabel("eddy", "current", "Circulating slack/current reversal area useful for recovery or route choice.", ("eddy", "recovery")),
        RapidReviewLabel("eddy_line", "current", "High shear boundary between main current and eddy circulation.", ("eddy_line", "shear")),
        RapidReviewLabel("strainer", "hazard", "Tree, debris, sieve, or brush hazard that should be avoided.", ("strainer", "hazard")),
        RapidReviewLabel("portage", "hazard", "Feature or reach that should support scout/portage gameplay and safety warnings.", ("portage", "hazard")),
        RapidReviewLabel("access_point", "logistics", "Put-in, take-out, trail, road, or scout access.", ("access", "logistics"), False),
        RapidReviewLabel("boulder_garden", "bedform", "Cluster of exposed or submerged rocks that drives roughness and collision hazards.", ("rock", "roughness")),
        RapidReviewLabel("constriction", "geometry", "Narrowed channel that accelerates flow and can produce stronger waves or holes.", ("constriction", "velocity")),
    )


def south_fork_american_flow_bands() -> tuple[FlowBand, ...]:
    """Return preliminary flow bands for the representative section.

    These are seed values for software integration. Milestone 10 must replace or
    calibrate them using pulled NWIS/NWPS/StreamStats records and domain review.
    """

    return (
        FlowBand(
            flow_band="low_runnable",
            season="late_summer_low_water",
            percentile_range=(0.10, 0.35),
            discharge_cfs=900.0,
            stage_ft=None,
            runnable=True,
            notes="Lower training-oriented flow; expect exposed rocks, shallows, and slower recovery from mistakes.",
            confidence=0.30,
        ),
        FlowBand(
            flow_band="median_runnable",
            season="summer_commercial",
            percentile_range=(0.35, 0.70),
            discharge_cfs=1600.0,
            stage_ft=None,
            runnable=True,
            notes="Default validation band for intermediate commercial-style runs.",
            confidence=0.35,
        ),
        FlowBand(
            flow_band="high_runnable",
            season="spring_runoff_or_release",
            percentile_range=(0.70, 0.90),
            discharge_cfs=3000.0,
            stage_ft=None,
            runnable=True,
            notes="Higher consequence preset with stronger holes, wave trains, eddy-line shear, and faster raft response.",
            confidence=0.25,
        ),
    )


def build_player_selection_model() -> dict[str, object]:
    section = south_fork_american_section()
    flow_bands = south_fork_american_flow_bands()
    return {
        "regions": [
            {
                "region": section.region,
                "rivers": [
                    {
                        "river_id": section.river_id,
                        "river_name": section.river_name,
                        "sections": [
                            {
                                "section_id": section.section_id,
                                "section_name": section.section_name,
                                "difficulty_range": list(section.difficulty_range),
                                "seasons": sorted({band.season for band in flow_bands}),
                                "flow_bands": [band.to_json_dict() for band in flow_bands],
                                "difficulty_presets": ["beginner", "intermediate", "advanced", "expert"],
                                "raft_setups": ["standard_14ft_paddle_raft", "heavier_training_raft"],
                                "gauge_sources": list(section.gauge_candidates),
                                "data_confidence": 0.35,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def default_player_selections() -> tuple[PlayerSelection, ...]:
    section = south_fork_american_section()
    return tuple(
        PlayerSelection(
            region=section.region,
            river_id=section.river_id,
            section_id=section.section_id,
            season=band.season,
            flow_band=band.flow_band,
            difficulty=difficulty,
            raft_setup="standard_14ft_paddle_raft",
        )
        for band, difficulty in (
            (south_fork_american_flow_bands()[0], "beginner"),
            (south_fork_american_flow_bands()[1], "intermediate"),
            (south_fork_american_flow_bands()[2], "advanced"),
        )
    )


def adaptive_solver_parameters(
    selection: PlayerSelection,
    *,
    flow_bands: tuple[FlowBand, ...] | None = None,
    representative_width_m: float = 24.0,
) -> SolverParameterPreset:
    """Map river + season + flow + difficulty into shallow-water and raft parameters."""

    bands = flow_bands or south_fork_american_flow_bands()
    flow_band = next((band for band in bands if band.flow_band == selection.flow_band), None)
    if flow_band is None:
        raise ValueError(f"Unknown flow band: {selection.flow_band}")
    difficulty_scale = {
        "beginner": 0.82,
        "intermediate": 1.0,
        "advanced": 1.18,
        "expert": 1.35,
    }[selection.difficulty]
    median_discharge = next((band.discharge_cfs for band in bands if band.flow_band == "median_runnable"), flow_band.discharge_cfs)
    flow_factor = max(0.35, flow_band.discharge_cfs / max(median_discharge, 1.0))
    depth = 0.72 + 0.52 * math.sqrt(flow_factor)
    inflow_m3s = flow_band.discharge_m3s
    velocity = inflow_m3s / max(representative_width_m * depth, 1.0)
    confidence = _clamp01(flow_band.confidence * (0.92 if selection.difficulty == "expert" else 1.0))
    return SolverParameterPreset(
        selection=selection,
        boundary_inflow_m3s=inflow_m3s,
        outflow_stage_bias_m=0.08 * (flow_factor - 1.0),
        initial_depth_m=depth,
        downstream_velocity_mps=velocity * difficulty_scale,
        downstream_momentum_scale=flow_factor * difficulty_scale,
        roughness_manning_n=0.034 + 0.007 * min(flow_factor, 1.6),
        aeration_turbulence_scale=flow_factor * difficulty_scale,
        hole_retention_strength=0.55 * flow_factor * difficulty_scale,
        wave_train_strength=0.70 * math.sqrt(flow_factor) * difficulty_scale,
        eddy_line_shear=0.60 * flow_factor * difficulty_scale,
        boil_strength=0.40 * flow_factor * difficulty_scale,
        shallow_hazard_threshold_m=max(0.18, 0.32 / math.sqrt(flow_factor)),
        hazard_activation_scale=0.65 * difficulty_scale * (1.12 if flow_factor > 1.2 else 1.0),
        raft_drag_coefficient_scale=1.0 + 0.10 * (flow_factor - 1.0),
        paddle_catch_scale=max(0.75, 1.0 + 0.06 * (flow_factor - 1.0)),
        damping_scale=max(0.70, 1.0 - 0.08 * (flow_factor - 1.0)),
        confidence_score=confidence,
        notes="Seed mapping for validation against PyClaw and custom C++ solver; tune with pulled gauge history and reviewed terrain.",
    )


def build_real_world_corridor_package() -> RealWorldCorridorPackage:
    section = south_fork_american_section()
    centerline = south_fork_american_centerline_stations()
    indicators = extract_channel_indicators(centerline)
    rapid_candidates = identify_candidate_rapids(indicators)
    return RealWorldCorridorPackage(
        section=section,
        source_manifest=build_source_manifest(section),
        centerline=centerline,
        indicators=indicators,
        rapid_candidates=rapid_candidates,
        flow_bands=south_fork_american_flow_bands(),
        player_selections=default_player_selections(),
        unreal_ready_artifacts={
            "terrain": "terrain/solver_bed_grid.npy",
            "imagery_masks": ["imagery/water_mask.tif", "imagery/foam_texture_mask.tif"],
            "centerline": "hydrography/centerline.geojson",
            "banks": "hydrography/banks.geojson",
            "rapids": "review/rapid_candidates.geojson",
            "hazards": "review/rapid_review_labels.json",
            "flow_presets": "hydrology/flow_presets.json",
            "validation_matrix": "validation_matrix.json",
            "confidence_metadata": "confidence.json",
        },
    )


def generate_real_world_scenario2_5d(
    selection: PlayerSelection | None = None,
    *,
    nx: int = 72,
    ny: int = 32,
    dx: float = 4.0,
    dy: float = 2.0,
    duration: float = 8.0,
    pyclaw_reference_min_depth_m: float = 0.01,
) -> Scenario2_5D:
    """Generate a small solver-neutral scenario from the representative real-world package."""

    if pyclaw_reference_min_depth_m < 0.0:
        raise ValueError("pyclaw_reference_min_depth_m must be non-negative.")
    chosen = selection or default_player_selections()[1]
    centerline = south_fork_american_centerline_stations()
    indicators = extract_channel_indicators(centerline)
    rapid_candidates = identify_candidate_rapids(indicators)
    preset = adaptive_solver_parameters(chosen, representative_width_m=float(np.mean([s.channel_width_m for s in centerline])))

    grid = GridSpec2_5D(nx=nx, ny=ny, dx=dx, dy=dy, origin_x=0.0, origin_y=-0.5 * (ny - 1) * dy)
    x, y = grid.meshgrid()
    xs = grid.x_coordinates()
    x_span = max(float(xs[-1] - xs[0]), dx)
    station_min = centerline[0].station_m
    station_max = centerline[-1].station_m
    station_grid = station_min + (x / max(x_span, 1.0)) * (station_max - station_min)

    station_values = np.asarray([station.station_m for station in centerline], dtype=np.float64)
    elevations = np.asarray([station.elevation_m for station in centerline], dtype=np.float64)
    widths = np.asarray([station.channel_width_m for station in centerline], dtype=np.float64)
    roughness = np.asarray([station.roughness_indicator for station in centerline], dtype=np.float64)
    bends = np.asarray([station.bend_score for station in centerline], dtype=np.float64)

    width_grid = np.interp(station_grid, station_values, widths)
    roughness_grid = np.interp(station_grid, station_values, roughness)
    bend_grid = np.interp(station_grid, station_values, bends)
    elevation_profile = np.interp(station_grid, station_values, elevations)

    normalized_x = x / max(x_span, 1.0)
    center_offset = 4.8 * np.sin(2.25 * math.tau * normalized_x) + 1.5 * np.sin(5.0 * math.tau * normalized_x)
    lateral = y - center_offset
    half_width = width_grid * 0.5
    wet_channel = np.abs(lateral) <= half_width

    bank_fraction = np.abs(lateral) / np.maximum(half_width, 1.0)
    depth = preset.initial_depth_m * np.maximum(0.24, 1.0 - 0.42 * bank_fraction**2)
    depth *= 1.0 + 0.11 * roughness_grid
    depth = np.where(wet_channel, depth, 0.0)

    surface_eta = preset.initial_depth_m - (elevation_profile[0, 0] - elevation_profile) * 0.018
    bank_lift = preset.initial_depth_m + 0.65 + 0.20 * np.maximum(bank_fraction - 1.0, 0.0)
    bed = np.where(wet_channel, surface_eta - depth, surface_eta + bank_lift)

    tangent_y = np.gradient(center_offset[0, :], dx)[np.newaxis, :]
    tangent_scale = np.sqrt(1.0 + tangent_y**2)
    tangent_x = 1.0 / tangent_scale
    tangent_y = tangent_y / tangent_scale
    constriction_speedup = float(np.median(widths)) / np.maximum(width_grid, 1.0)
    speed = preset.downstream_velocity_mps * np.sqrt(constriction_speedup) * (1.0 + 0.10 * roughness_grid)
    bank_slowdown = np.maximum(0.30, 1.0 - 0.55 * bank_fraction**2)
    u = np.where(wet_channel, tangent_x * speed * bank_slowdown, 0.0)
    v = np.where(wet_channel, tangent_y * speed * bank_slowdown + 0.10 * preset.eddy_line_shear * bend_grid, 0.0)

    features = _features_from_rapid_candidates(rapid_candidates, grid, station_min, station_max, preset)
    for feature in features:
        influence = _feature_influence(feature, x, y)
        if feature.kind == "constriction":
            u *= 1.0 + 0.16 * feature.strength * influence
        elif feature.kind == "wave_train":
            wave = np.sin((x - feature.center[0]) * 0.42)
            depth = np.maximum(0.0, depth + 0.08 * feature.strength * wave * influence)
            u *= 1.0 + 0.08 * feature.strength * np.abs(wave) * influence
        elif feature.kind == "hole":
            u -= tangent_x * 0.20 * feature.strength * influence
            depth += 0.10 * feature.strength * influence
        elif feature.kind == "rock":
            obstacle = influence > 0.55
            depth = np.where(obstacle, 0.0, depth)
            u = np.where(obstacle, 0.0, u)
            v = np.where(obstacle, 0.0, v)
        elif feature.kind == "lateral":
            v += 0.22 * feature.strength * influence

    bed = np.where(depth > 1.0e-6, bed, surface_eta + bank_lift)
    if pyclaw_reference_min_depth_m > 0.0:
        shallow_reference_mask = depth <= pyclaw_reference_min_depth_m
        depth = np.maximum(depth, pyclaw_reference_min_depth_m)
        u = np.where(shallow_reference_mask, 0.0, u)
        v = np.where(shallow_reference_mask, 0.0, v)
        bed = np.where(shallow_reference_mask, surface_eta - depth, bed)
    state = InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v)
    boundaries = (
        BoundaryCondition2_5D("west", "inflow", depth=preset.initial_depth_m, velocity=(preset.downstream_velocity_mps, 0.0), metadata={"flow_band": chosen.flow_band}),
        BoundaryCondition2_5D("east", "outflow", stage=preset.initial_depth_m + preset.outflow_stage_bias_m, metadata={"flow_band": chosen.flow_band}),
        BoundaryCondition2_5D("south", "bank"),
        BoundaryCondition2_5D("north", "bank"),
    )
    metadata = ScenarioMetadata2_5D(
        scenario_id=f"{chosen.river_id}_{chosen.section_id}_{chosen.flow_band}_{chosen.difficulty}",
        scenario_type="real_world",
        seed=9,
        generator="raftsim.real_world",
        generator_version="milestone_9_seed.v0",
        description="Representative real-world 2.5D seed scenario built from source-manifest, centerline, rapid candidate, and seasonal flow presets.",
        river_id=chosen.river_id,
        section_id=chosen.section_id,
        coordinate_reference_system="local meters from source_manifest EPSG:4326 planning bounds",
        source_manifest=SOURCE_MANIFEST_FILE,
        gauge_source="USGS 11445500 South Fork American River near Lotus, CA",
        season_preset=chosen.season,
        flow_percentile=float(np.mean(_flow_band_by_name(chosen.flow_band).percentile_range)),
        flow_band=chosen.flow_band,
        difficulty_preset=chosen.difficulty,
        confidence_score=preset.confidence_score,
        provenance={
            "source_manifest": SOURCE_MANIFEST_FILE,
            "source_package": "physics/data/real_world/south_fork_american_chili_bar",
            "flow_preset_confidence": preset.confidence_score,
            "rapid_candidate_count": len(rapid_candidates),
            "pyclaw_reference_min_depth_m": pyclaw_reference_min_depth_m,
        },
    )
    return Scenario2_5D(
        metadata=metadata,
        grid=grid,
        fixed_dt=1.0 / 60.0,
        duration=duration,
        bed=bed,
        initial_state=state,
        boundaries=boundaries,
        features=features,
        probes=_real_world_probes(grid, rapid_candidates, station_min, station_max),
        raft=RaftParameters2_5D(drag_coefficient=1.25 * preset.raft_drag_coefficient_scale),
        roughness=preset.roughness_manning_n,
    )


def write_real_world_seed_package(directory: str | Path) -> Path:
    """Write manifest, review data, flow presets, and a shared scenario package."""

    output_dir = Path(directory)
    data_dir = output_dir / "south_fork_american_chili_bar"
    scenario_dir = data_dir / "scenario"
    data_dir.mkdir(parents=True, exist_ok=True)
    package = build_real_world_corridor_package()
    _write_json(output_dir / "candidate_rivers.json", {"sections": [section.to_json_dict() for section in default_candidate_river_inventory()]})
    _write_json(output_dir / "source_catalog.json", {"sources": [source.to_json_dict() for source in default_source_catalog()]})
    _write_json(output_dir / "rapid_review_labels.json", {"labels": [label.to_json_dict() for label in default_manual_rapid_review_labels()]})
    _write_json(output_dir / "player_selection_model.json", build_player_selection_model())
    _write_json(data_dir / SOURCE_MANIFEST_FILE, package.source_manifest)
    _write_json(data_dir / "river_course.json", package.to_json_dict())
    _write_json(data_dir / "flow_presets.json", {"flow_bands": [band.to_json_dict() for band in package.flow_bands]})
    _write_json(data_dir / "rapid_candidates.geojson", _rapid_candidates_geojson(package.rapid_candidates, package.indicators))
    _write_json(data_dir / "corridor_package_manifest.json", _corridor_manifest(package))
    generate_real_world_scenario2_5d().write_package(scenario_dir)
    return data_dir


def _flow_band_by_name(flow_band: str) -> FlowBand:
    for band in south_fork_american_flow_bands():
        if band.flow_band == flow_band:
            return band
    raise ValueError(f"Unknown flow band: {flow_band}")


def _indicator_signals(
    station: CenterlineStation,
    gradient: float,
    constriction: float,
    roughness: float,
    rapid_score: float,
) -> tuple[str, ...]:
    signals: list[str] = []
    if gradient >= 0.012:
        signals.append("dem_slope")
    if constriction >= 0.18:
        signals.append("constriction")
    if station.boulder_density >= 0.45:
        signals.append("boulder_density")
    if station.imagery_whitewater_texture >= 0.40:
        signals.append("foam_whitewater_texture")
    if station.bend_score >= 0.55:
        signals.append("bend_or_lateral_candidate")
    if station.guide_note_score >= 0.45:
        signals.append("guide_note")
    if station.access_score >= 0.50:
        signals.append("access_point")
    if roughness >= 0.45:
        signals.append("roughness")
    if rapid_score >= 0.55:
        signals.append("high_score")
    return tuple(signals)


def _rapid_candidate_from_cluster(index: int, cluster: list[ChannelIndicator]) -> RapidCandidate:
    peak = max(cluster, key=lambda indicator: indicator.rapid_score)
    all_signals = sorted({signal for indicator in cluster for signal in indicator.signals})
    labels: list[str] = []
    if "constriction" in all_signals:
        labels.append("constriction")
    if "boulder_density" in all_signals:
        labels.append("boulder_garden")
    if "foam_whitewater_texture" in all_signals:
        labels.append("wave_train")
    if "bend_or_lateral_candidate" in all_signals:
        labels.append("lateral")
    if "guide_note" in all_signals:
        labels.append("manual_review_required")
    if not labels:
        labels.append("riffle")
    confidence = _clamp01(0.25 + 0.55 * peak.rapid_score + 0.04 * len(all_signals))
    return RapidCandidate(
        rapid_id=f"rapid_candidate_{index:02d}",
        start_station_m=cluster[0].station_m,
        end_station_m=cluster[-1].station_m,
        peak_station_m=peak.station_m,
        score=peak.rapid_score,
        suggested_labels=tuple(labels),
        signals=tuple(all_signals),
        confidence=confidence,
    )


def _features_from_rapid_candidates(
    rapid_candidates: tuple[RapidCandidate, ...],
    grid: GridSpec2_5D,
    station_min: float,
    station_max: float,
    preset: SolverParameterPreset,
) -> tuple[Feature2_5D, ...]:
    features: list[Feature2_5D] = []
    x_min = float(grid.x_coordinates()[0])
    x_max = float(grid.x_coordinates()[-1])
    station_span = max(station_max - station_min, 1.0)
    for candidate in rapid_candidates:
        x = x_min + (candidate.peak_station_m - station_min) / station_span * (x_max - x_min)
        base_strength = max(0.2, candidate.score) * preset.hazard_activation_scale
        feature_kind = "wave_train"
        if "constriction" in candidate.suggested_labels:
            feature_kind = "constriction"
        elif "boulder_garden" in candidate.suggested_labels:
            feature_kind = "rock"
        elif "lateral" in candidate.suggested_labels:
            feature_kind = "lateral"
        features.append(
            Feature2_5D(
                kind=feature_kind,  # type: ignore[arg-type]
                center=(float(x), 0.0),
                radius=4.0 if feature_kind == "rock" else 7.0,
                strength=float(base_strength),
                length=float(max(10.0, (candidate.end_station_m - candidate.start_station_m) * (x_max - x_min) / station_span)),
                width=16.0,
                metadata={
                    "rapid_id": candidate.rapid_id,
                    "source": "real_world_rapid_candidate",
                    "confidence": candidate.confidence,
                    "signals": ",".join(candidate.signals),
                },
            )
        )
        if "wave_train" in candidate.suggested_labels and feature_kind != "wave_train":
            features.append(
                Feature2_5D(
                    kind="wave_train",
                    center=(float(min(x + 8.0, x_max)), 0.0),
                    radius=7.0,
                    strength=float(base_strength * preset.wave_train_strength),
                    length=18.0,
                    width=15.0,
                    metadata={"rapid_id": candidate.rapid_id, "source": "paired_wave_train"},
                )
            )
        if candidate.score >= 0.58:
            features.append(
                Feature2_5D(
                    kind="hole",
                    center=(float(min(x + 4.0, x_max)), 0.0),
                    radius=5.0,
                    strength=float(base_strength * preset.hole_retention_strength),
                    length=10.0,
                    width=12.0,
                    metadata={"rapid_id": candidate.rapid_id, "source": "high_score_hole_proxy"},
                )
            )
    return tuple(features)


def _real_world_probes(
    grid: GridSpec2_5D,
    rapid_candidates: tuple[RapidCandidate, ...],
    station_min: float,
    station_max: float,
) -> tuple[Probe2_5D, ...]:
    probes: list[Probe2_5D] = [
        Probe2_5D("put_in_center", (grid.x_coordinates()[2], 0.0)),
        Probe2_5D("mid_run_center", (grid.center[0], 0.0)),
        Probe2_5D("take_out_center", (grid.x_coordinates()[-3], 0.0)),
        Probe2_5D("mid_cross_section", (grid.center[0], 0.0), kind="cross_section", normal=(0.0, 1.0), length=(grid.ny - 2) * grid.dy),
    ]
    x_min = float(grid.x_coordinates()[0])
    x_max = float(grid.x_coordinates()[-1])
    station_span = max(station_max - station_min, 1.0)
    for candidate in rapid_candidates[:4]:
        x = x_min + (candidate.peak_station_m - station_min) / station_span * (x_max - x_min)
        probes.append(Probe2_5D(f"{candidate.rapid_id}_probe", (float(x), 0.0), metadata={"rapid_id": candidate.rapid_id}))
    return tuple(probes)


def _feature_influence(feature: Feature2_5D, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    scale_x = max(feature.length * 0.5, feature.radius, 1.0)
    scale_y = max(feature.width * 0.5, feature.radius, 1.0)
    dx = (x - feature.center[0]) / scale_x
    dy = (y - feature.center[1]) / scale_y
    return np.exp(-(dx**2 + dy**2))


def _rapid_candidates_geojson(
    candidates: tuple[RapidCandidate, ...],
    indicators: tuple[ChannelIndicator, ...],
) -> dict[str, object]:
    features = []
    for candidate in candidates:
        nearest = min(indicators, key=lambda indicator: abs(indicator.station_m - candidate.peak_station_m))
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [nearest.lon, nearest.lat]},
                "properties": candidate.to_json_dict(),
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _corridor_manifest(package: RealWorldCorridorPackage) -> dict[str, object]:
    return {
        "corridor_package_version": "raftsim.real_world_corridor.v0",
        "river_id": package.section.river_id,
        "section_id": package.section.section_id,
        "source_manifest": SOURCE_MANIFEST_FILE,
        "unreal_ready_artifacts": package.unreal_ready_artifacts,
        "flow_presets": [band.flow_band for band in package.flow_bands],
        "validation_matrix": "validation_matrix.json",
        "rapid_candidate_count": len(package.rapid_candidates),
        "confidence": package.source_manifest["confidence"],
        "notes": "Seed Unreal corridor handoff; production export must replace placeholder masks and terrain with extracted geospatial assets.",
    }


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
