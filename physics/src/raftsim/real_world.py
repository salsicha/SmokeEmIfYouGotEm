"""Real-world river content helpers for source manifests and 2.5D seeds."""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Literal

import numpy as np

from .cascading import (
    CaliforniaPoolDropParameters2_5D,
    CascadingScenarioPackage2_5D,
    DropTransitionMetadata2_5D,
    ReachMetadata2_5D,
    generate_california_pool_drop_cascading_scenario2_5d,
    write_unreal_cascading_corridor_metadata,
)
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

DataCategory = Literal[
    "elevation",
    "hydrography",
    "imagery",
    "gauge",
    "guide_reference",
    "field_media",
    "derived_source_masks",
    "derived_heightfield_candidate",
]
DifficultyPreset = Literal["beginner", "intermediate", "advanced", "expert"]
SourceStatus = Literal[
    "planned",
    "metadata_ready",
    "downloaded",
    "derived",
    "reviewed",
    "generated_review_gated_preview_masks",
    "generated_review_gated_import_candidate",
]
RapidReviewLayerKind = Literal["raster", "vector", "table", "manifest", "annotation", "reference"]
RapidReviewPanelKind = Literal["map", "profile", "hydrology", "evidence", "annotation_form"]

SOURCE_MANIFEST_FILE = "source_manifest.json"
CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION = "raftsim.candidate_river_inventory.v0"
CANDIDATE_RIVER_INVENTORY_FILE = "candidate_river_inventory.json"
COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION = "raftsim.course_elevation_extraction.v0"
COURSE_ELEVATION_EXTRACTION_FILE = "course_elevation_extraction.json"
RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION = "raftsim.rapid_review_flow_difficulty_mapping.v0"
RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE = "rapid_review_flow_difficulty_mapping.json"
RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION = "raftsim.rapid_review_editor_workflow.v0"
RAPID_REVIEW_EDITOR_WORKFLOW_FILE = "rapid_review_editor_workflow.json"
PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION = "raftsim.production_import_pilot.v0"
PRODUCTION_ENVIRONMENT_GAP_REGISTER_SCHEMA_VERSION = "raftsim.production_environment_gap_register.v0"
PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE = "production_environment_gap_register.json"
SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE = "production_source_gate_review.json"
REFERENCE_MEDIA_ANNOTATIONS_FILE = "review/production_import_pilot/reference_annotations.geojson"
REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE = "field_media/production_import_pilot/rights_manifest.json"
REFERENCE_MEDIA_TARGET_STATION_FRACTIONS = {
    "south_fork_guide_seat_boulder_garden": 0.12,
    "south_fork_late_summer_exposed_rocks": 0.46,
    "south_fork_high_flow_foam_lines": 0.74,
    "colorado_river_eye_canyon_scale": 0.08,
    "colorado_release_wet_banks_and_sandbars": 0.44,
    "colorado_long_swimmer_rescue_visibility": 0.72,
    "pacuare_rainforest_gorge_density": 0.18,
    "pacuare_waterfalls_mist_wet_rock": 0.56,
    "pacuare_canopy_rescue_readability": 0.82,
}
SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE = "hydrology/cdec_terms_flags_and_station_relation_review.json"
SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE = "hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json"
SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE = (
    "hydrology/production_import_pilot/cdec_seasonal_window_review_wy2026_to_2026-07-06.json"
)
SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE = (
    "hydrology/production_import_pilot/cdec_multiyear_flow_review_2021-10-01_2026-07-06.json"
)
SOUTH_FORK_FLOW_BAND_REVIEW_FILE = "hydrology/production_import_pilot/flow_band_review.json"
SOUTH_FORK_NHD_HU8_MANIFEST_FILE = "hydrography/nhd_hu8_18020129_bbox_extract_manifest.json"
SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE = "hydrography/nhd_hu8_18020129_flowline_bbox_extract.geojson"
SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE = "hydrography/nhd_hu8_18020129_support_layers_bbox_extract.geojson"
SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE = "hydrography/nhd_hu8_18020129_mainstem_candidate_manifest.json"
SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE = "hydrography/nhd_hu8_18020129_south_fork_mainstem_candidate.geojson"
SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE = "hydrography/nhd_hu8_18020129_mainstem_stationing_candidate.json"
SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE = "hydrography/nhd_hu8_18020129_cross_section_seed_manifest.json"
SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE = "hydrography/nhd_hu8_18020129_cross_section_seed_candidates.geojson"
SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE = "hydrography/nhd_hu8_18020129_naip_dem_alignment_diagnostic.json"
SOUTH_FORK_NHD_WATER_PRIOR_MANIFEST_FILE = "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json"
SOUTH_FORK_NHD_WATER_PRIOR_FILE = "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png"
SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE = (
    "hydrography/production_import_pilot/hydrography_draft_manifest.json"
)
SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE = "hydrography/production_import_pilot/centerline.geojson"
SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE = "hydrography/production_import_pilot/banks.geojson"
SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE = "hydrography/production_import_pilot/cross_sections.geojson"
SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE = "review/production_import_pilot/access_publication_sensitivity_review.json"
SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE = "review/production_import_pilot/source_metadata_review.json"
SOUTH_FORK_ACCESS_POINTS_FILE = "review/production_import_pilot/access_points.geojson"
SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE = "review/production_import_pilot/no_publish_sensitive_polygons.geojson"
SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE = "review/production_import_pilot/evacuation_and_rescue_routes.geojson"
SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE = "production_import_pilot.json"
COLORADO_PRODUCTION_IMPORT_PILOT_FILE = "production_import_pilot.json"
COLORADO_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE = "production_import_pilot_pull_manifest.json"
COLORADO_NHD_HU8_MANIFEST_FILE = "hydrography/nhd_hu8_lees_ferry_bbox_extract_manifest.json"
COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE = "hydrography/nhd_hu8_lees_ferry_flowline_bbox_extract.geojson"
COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE = "hydrography/nhd_hu8_lees_ferry_support_layers_bbox_extract.geojson"
COLORADO_NHD_MAINSTEM_MANIFEST_FILE = "hydrography/nhd_hu8_lees_ferry_mainstem_candidate_manifest.json"
COLORADO_NHD_MAINSTEM_CANDIDATE_FILE = "hydrography/nhd_hu8_lees_ferry_colorado_mainstem_candidate.geojson"
COLORADO_NHD_MAINSTEM_STATIONING_FILE = "hydrography/nhd_hu8_lees_ferry_mainstem_stationing_candidate.json"
COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE = "hydrography/nhd_hu8_lees_ferry_cross_section_seed_manifest.json"
COLORADO_NHD_CROSS_SECTION_SEED_FILE = "hydrography/nhd_hu8_lees_ferry_cross_section_seed_candidates.geojson"
COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE = "hydrography/nhd_hu8_lees_ferry_naip_dem_alignment_diagnostic.json"
COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE = "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json"
COLORADO_NHD_WATER_PRIOR_FILE = "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png"
COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE = (
    "hydrography/production_import_pilot/hydrography_draft_manifest.json"
)
COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE = "hydrography/production_import_pilot/centerline.geojson"
COLORADO_PRODUCTION_BANKS_DRAFT_FILE = "hydrography/production_import_pilot/banks.geojson"
COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE = "hydrography/production_import_pilot/cross_sections.geojson"
COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE = "hydrography/production_import_pilot/river_mile_markers.geojson"
COLORADO_PRODUCTION_SANDBARS_FILE = "hydrography/production_import_pilot/sandbars.geojson"
COLORADO_USBR_TOTAL_RELEASE_FILE = "hydrology/production_import_pilot/usbr_glen_canyon_total_release_daily.json"
COLORADO_USBR_RELEASE_CONTEXT_FILE = "hydrology/production_import_pilot/usbr_glen_canyon_release_context.json"
COLORADO_RELEASE_BAND_REVIEW_FILE = "hydrology/production_import_pilot/release_band_review.json"
COLORADO_ACCESS_PUBLICATION_REVIEW_FILE = "review/production_import_pilot/access_publication_sensitivity_review.json"
COLORADO_SOURCE_METADATA_REVIEW_FILE = "review/production_import_pilot/source_metadata_review.json"
COLORADO_ACCESS_POINTS_FILE = "review/production_import_pilot/access_points.geojson"
COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE = "review/production_import_pilot/no_publish_sensitive_polygons.geojson"
COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE = "review/production_import_pilot/camps_and_beaches_review.geojson"
COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE = "review/production_import_pilot/oarsman_route_publication_notes.json"
PACUARE_PRODUCTION_IMPORT_PILOT_FILE = "production_import_pilot.json"
PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE = (
    "hydrography/production_import_pilot/preview_centerline_scaffold_manifest.json"
)
PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE = "hydrography/production_import_pilot/preview_centerline_scaffold.geojson"
PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE = "hydrography/production_import_pilot/preview_stationing_scaffold.json"
PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE = "hydrography/production_import_pilot/centerline.geojson"
PACUARE_PRODUCTION_BANKS_DRAFT_FILE = "hydrography/production_import_pilot/banks.geojson"
PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE = "hydrography/production_import_pilot/rapid_and_access_stationing.geojson"
PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE = "hydrography/production_import_pilot/official_source_access_plan.json"
PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE = (
    "hydrography/production_import_pilot/direccion_de_agua_sinigirh_wms_getcapabilities.xml"
)
PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE = (
    "hydrography/production_import_pilot/direccion_de_agua_sinigirh_wms_capabilities_summary.json"
)
PACUARE_SNIT_OGC_CATALOG_FILE = "hydrography/production_import_pilot/snit_ogc_services_catalog.html"
PACUARE_SNIT_CONFIG_FILE = "hydrography/production_import_pilot/snit_config_ssnit.js"
PACUARE_SNIT_LAYER_LIST_SCRIPT_FILE = "hydrography/production_import_pilot/snit_ico_servicios_ogc_lista_capas.js"
PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE = "hydrography/production_import_pilot/snit_layer_catalog_summary.json"
PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE = "hydrography/production_import_pilot/snit_layer_metadata_summary.json"
PACUARE_RAINFALL_STATION_REVIEW_FILE = "hydrology/production_import_pilot/rainfall_station_review.json"
PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE = "hydrology/production_import_pilot/discharge_or_stage_station_review.json"
PACUARE_FLASH_RESPONSE_REVIEW_FILE = "hydrology/production_import_pilot/flash_response_review.json"
PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE = (
    "review/production_import_pilot/protected_area_publication_sensitivity.json"
)
PACUARE_ACCESS_CONSERVATION_POLICY_FILE = "review/production_import_pilot/access_and_conservation_policy.json"
PACUARE_SOURCE_METADATA_REVIEW_FILE = "review/production_import_pilot/source_metadata_review.json"
PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE = "imagery/production_import_pilot/cloud_screened_scene_index.json"
PACUARE_CLOUD_SHADOW_REVIEW_FILE = "imagery/production_import_pilot/cloud_shadow_review.json"
PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE = (
    "imagery/production_import_pilot/high_resolution_scene_metadata_review.json"
)
PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE = (
    "imagery/production_import_pilot/landsat_product_access_gate_review.json"
)
PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE = "imagery/production_import_pilot/sentinel_cog_thumbnail_review.json"
PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE = "imagery/production_import_pilot/sentinel_cog_access_probe.json"
PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE = "imagery/production_import_pilot/sentinel_tci_review_preview.json"
PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250119_tci_review_1024.png"
)
PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_tci_16phr_review_preview.json"
)
PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250119_tci_review_1024.png"
)
PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_corridor_tile_coverage_review.json"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_corridor_bbox_clip_review.json"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250119_corridor_bbox_clip_review.png"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250119_corridor_bbox_clip_review.png"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_corridor_bbox_scl_qa_review.json"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250119_corridor_bbox_scl_qa_review.png"
)
PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250119_corridor_bbox_scl_qa_review.png"
)
PACUARE_SENTINEL_CLEANER_SCENE_SEARCH_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_cleaner_scene_search_review.json"
)
PACUARE_SENTINEL_20250320_SCL_QA_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20250320_corridor_bbox_scl_qa_review.json"
)
PACUARE_SENTINEL_20250320_SCL_QA_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250320_corridor_bbox_scl_qa_review.png"
)
PACUARE_SENTINEL_20250320_SCL_QA_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250320_corridor_bbox_scl_qa_review.png"
)
PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20250320_corridor_bbox_clip_review.json"
)
PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250320_corridor_bbox_clip_review.png"
)
PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250320_corridor_bbox_clip_review.png"
)
PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20250320_draft_bank_window_review.json"
)
PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250320_draft_bank_window_clip_review.png"
)
PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250320_draft_bank_window_clip_review.png"
)
PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20250320_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20250320_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_PROBE_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20250305_draft_bank_window_scl_probe.json"
)
PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2c_17pkm_20250305_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2c_16phr_20250305_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_PROBE_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20240204_draft_bank_window_scl_probe.json"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20240204_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20240204_draft_bank_window_scl_qa_review.png"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_REVIEW_FILE = (
    "imagery/production_import_pilot/sentinel_20240204_draft_bank_window_tci_review.json"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_17PKM_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_17pkm_20240204_draft_bank_window_clip_review.png"
)
PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_16PHR_IMAGE_FILE = (
    "imagery/production_import_pilot/sentinel_s2b_16phr_20240204_draft_bank_window_clip_review.png"
)
SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE = "production_import_pilot_pull_manifest.json"
SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE = "production_import_pilot_derivatives_manifest.json"
DISCHARGE_CFS_TO_M3S = 0.028316846592
DIFFICULTY_PRESETS: tuple[DifficultyPreset, ...] = ("beginner", "intermediate", "advanced", "expert")


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
class CourseElevationSample:
    station_m: float
    lon: float
    lat: float
    elevation_m: float
    channel_width_m: float
    local_drop_m: float
    cumulative_drop_m: float
    gradient: float
    left_bank_offset_m: float
    right_bank_offset_m: float
    constriction_score: float
    roughness_score: float
    rapid_score: float
    signals: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "station_m": self.station_m,
            "lon": self.lon,
            "lat": self.lat,
            "elevation_m": self.elevation_m,
            "channel_width_m": self.channel_width_m,
            "local_drop_m": self.local_drop_m,
            "cumulative_drop_m": self.cumulative_drop_m,
            "gradient": self.gradient,
            "left_bank_offset_m": self.left_bank_offset_m,
            "right_bank_offset_m": self.right_bank_offset_m,
            "constriction_score": self.constriction_score,
            "roughness_score": self.roughness_score,
            "rapid_score": self.rapid_score,
            "signals": list(self.signals),
        }


@dataclass(frozen=True, slots=True)
class CourseElevationExtraction:
    river_id: str
    section_id: str
    source_manifest: str
    source_artifacts: dict[str, object]
    samples: tuple[CourseElevationSample, ...]
    summary: dict[str, object]
    cross_section_prototypes: tuple[dict[str, object], ...]
    provenance: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION,
            "river_id": self.river_id,
            "section_id": self.section_id,
            "source_manifest": self.source_manifest,
            "source_artifacts": self.source_artifacts,
            "summary": self.summary,
            "samples": [sample.to_json_dict() for sample in self.samples],
            "cross_section_prototypes": list(self.cross_section_prototypes),
            "provenance": self.provenance,
        }


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
class RapidReviewLayer:
    layer_id: str
    display_name: str
    layer_kind: RapidReviewLayerKind
    artifact_path: str
    source_ids: tuple[str, ...]
    display_role: str
    visible_by_default: bool = True
    required_for_review: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return {
            "layer_id": self.layer_id,
            "display_name": self.display_name,
            "layer_kind": self.layer_kind,
            "artifact_path": self.artifact_path,
            "source_ids": list(self.source_ids),
            "display_role": self.display_role,
            "visible_by_default": self.visible_by_default,
            "required_for_review": self.required_for_review,
        }


@dataclass(frozen=True, slots=True)
class RapidReviewPanel:
    panel_id: str
    title: str
    panel_kind: RapidReviewPanelKind
    layer_ids: tuple[str, ...]
    purpose: str
    editable_fields: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "panel_kind": self.panel_kind,
            "layer_ids": list(self.layer_ids),
            "purpose": self.purpose,
            "editable_fields": list(self.editable_fields),
        }


@dataclass(frozen=True, slots=True)
class RapidReviewItem:
    review_item_id: str
    rapid_id: str
    station_range_m: tuple[float, float]
    peak_station_m: float
    map_focus_wgs84: tuple[float, float]
    candidate_tags: tuple[str, ...]
    signals: tuple[str, ...]
    confidence: float
    evidence_refs: dict[str, object]
    cross_section_summary: dict[str, float]
    gauge_context: dict[str, object]
    guide_notes: tuple[str, ...]
    required_actions: tuple[str, ...]
    editable_fields: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "review_item_id": self.review_item_id,
            "rapid_id": self.rapid_id,
            "station_range_m": {
                "start": self.station_range_m[0],
                "end": self.station_range_m[1],
            },
            "peak_station_m": self.peak_station_m,
            "map_focus_wgs84": {
                "lon": self.map_focus_wgs84[0],
                "lat": self.map_focus_wgs84[1],
            },
            "candidate_tags": list(self.candidate_tags),
            "signals": list(self.signals),
            "confidence": self.confidence,
            "evidence_refs": self.evidence_refs,
            "cross_section_summary": self.cross_section_summary,
            "gauge_context": self.gauge_context,
            "guide_notes": list(self.guide_notes),
            "required_actions": list(self.required_actions),
            "editable_fields": list(self.editable_fields),
        }


@dataclass(frozen=True, slots=True)
class RapidReviewEditorWorkflow:
    river_id: str
    section_id: str
    source_manifest: str
    layers: tuple[RapidReviewLayer, ...]
    panels: tuple[RapidReviewPanel, ...]
    review_items: tuple[RapidReviewItem, ...]
    label_catalog: tuple[RapidReviewLabel, ...]
    save_targets: tuple[str, ...]
    export_targets: tuple[str, ...]
    quality_gates: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        required_layer_ids = [layer.layer_id for layer in self.layers if layer.required_for_review]
        return {
            "schema_version": RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION,
            "river_id": self.river_id,
            "section_id": self.section_id,
            "source_manifest": self.source_manifest,
            "view_id": "rapid_review_one_view",
            "required_layer_ids": required_layer_ids,
            "layers": [layer.to_json_dict() for layer in self.layers],
            "panels": [panel.to_json_dict() for panel in self.panels],
            "review_items": [item.to_json_dict() for item in self.review_items],
            "label_catalog": [label.to_json_dict() for label in self.label_catalog],
            "save_targets": list(self.save_targets),
            "export_targets": list(self.export_targets),
            "quality_gates": list(self.quality_gates),
        }


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
class RapidReviewFlowDifficultyMapping:
    river_id: str
    section_id: str
    source_manifest: str
    label_catalog: tuple[RapidReviewLabel, ...]
    flow_bands: tuple[FlowBand, ...]
    difficulty_presets: tuple[dict[str, object], ...]
    label_flow_responses: tuple[dict[str, object], ...]
    parameter_matrix: tuple[dict[str, object], ...]
    review_requirements: tuple[str, ...]
    provenance: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION,
            "river_id": self.river_id,
            "section_id": self.section_id,
            "source_manifest": self.source_manifest,
            "label_catalog": [label.to_json_dict() for label in self.label_catalog],
            "flow_bands": [band.to_json_dict() for band in self.flow_bands],
            "difficulty_presets": list(self.difficulty_presets),
            "label_flow_responses": list(self.label_flow_responses),
            "parameter_matrix": list(self.parameter_matrix),
            "review_requirements": list(self.review_requirements),
            "provenance": self.provenance,
        }


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


@dataclass(frozen=True, slots=True)
class CandidateRiverInventoryPackage:
    inventory_id: str
    sections: tuple[CandidateRiverSection, ...]
    primary_river_id: str
    primary_section_id: str
    source_catalog_file: str
    section_source_manifests: tuple[dict[str, object], ...]
    selection_criteria: tuple[str, ...]
    next_review_actions: tuple[str, ...]
    provenance: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION,
            "inventory_id": self.inventory_id,
            "primary_section": {
                "river_id": self.primary_river_id,
                "section_id": self.primary_section_id,
            },
            "source_catalog": self.source_catalog_file,
            "section_count": len(self.sections),
            "sections": [section.to_json_dict() for section in self.sections],
            "section_source_manifests": list(self.section_source_manifests),
            "selection_criteria": list(self.selection_criteria),
            "next_review_actions": list(self.next_review_actions),
            "provenance": self.provenance,
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
            river_id="colorado_grand_canyon_rowing",
            river_name="Colorado River",
            section_id="lees_ferry_to_diamond_creek",
            section_name="Grand Canyon Rowing Route",
            region="Arizona Grand Canyon",
            country="US",
            bounds_wgs84=BoundsWGS84(-113.55, 35.75, -111.55, 36.95),
            difficulty_range=("class_iii", "class_v"),
            playable_reason="Second runnable river target with oar-rig rowing, large-volume current reading, canyon pacing, and longer rescue windows.",
            data_priorities=("usgs_gauge_09380000", "usgs_gauge_09402500", "nps_permit_context", "3dep_dem_research", "guide_reference_review"),
            gauge_candidates=(
                "USGS 09380000 Colorado River at Lees Ferry, AZ",
                "USGS 09402500 Colorado River near Grand Canyon, AZ",
            ),
            notes="Second real-world target after the South Fork baseline; source manifest and planning flow bands are drafted in Milestone 21.",
        ),
        CandidateRiverSection(
            river_id="pacuare",
            river_name="Pacuare River",
            section_id="lower_pacuare_planning_corridor",
            section_name="Lower Pacuare Planning Corridor",
            region="Costa Rica Caribbean slope",
            country="CR",
            bounds_wgs84=BoundsWGS84(-83.75, 9.72, -83.42, 10.12),
            difficulty_range=("class_iii", "class_iv"),
            playable_reason="Third runnable river target with tropical rainforest whitewater, rain-fed flow variability, steep-walled gorges, and a distinct international rafting biome.",
            data_priorities=(
                "dem_source_research",
                "osm_hydrography_access",
                "costa_rica_hydrology_gauge_search",
                "sinac_protected_area_review",
                "guide_reference_review",
                "field_media_rights_review",
            ),
            gauge_candidates=("Costa Rica hydrology gauge search for the Rio Pacuare basin",),
            notes="Third runnable river target after South Fork American and Colorado rowing; planning bounds, source manifest, flow bands, and guide annotations must be replaced with reviewed Costa Rica data before solver generation.",
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


def build_candidate_river_inventory_package(
    sections: tuple[CandidateRiverSection, ...] | None = None,
) -> CandidateRiverInventoryPackage:
    """Build the first candidate river inventory with source-manifest linkage."""

    inventory_sections = sections or default_candidate_river_inventory()
    if not inventory_sections:
        raise ValueError("candidate river inventory requires at least one section.")
    primary = inventory_sections[0]
    return CandidateRiverInventoryPackage(
        inventory_id="raftsim.real_world_candidate_river_inventory.v0",
        sections=inventory_sections,
        primary_river_id=primary.river_id,
        primary_section_id=primary.section_id,
        source_catalog_file="source_catalog.json",
        section_source_manifests=tuple(
            _candidate_section_source_manifest_link(section, primary)
            for section in inventory_sections
        ),
        selection_criteria=(
            "Commercial or instructional whitewater value with known playable lines.",
            "Public or metadata-ready elevation, hydrography, imagery, and gauge data.",
            "Distinct seasonal flow bands that can change the nature of rapids.",
            "Enough guide/reference context to sanity-check surf, flush, pin, flip, access, and safety outcomes.",
            "Representative geography spread for future rendering, hydrology, and difficulty coverage.",
        ),
        next_review_actions=(
            "Verify planning bounds and gauge candidates before production extraction.",
            "Replace seed DEM/imagery/guide placeholders with pulled source products and reviewed annotations.",
            "Draft source manifests for planned sections before generating solver packages from them.",
            "Keep rights/provenance separate from third-party media until redistribution permissions are explicit.",
        ),
        provenance={
            "generated_by": "raftsim.real_world.build_candidate_river_inventory_package",
            "processing_version": "milestone_17_inventory_seed.v0",
            "review_status": "draft_inventory_with_two_drafted_source_manifests_and_pacuare_planned_third",
        },
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
            source_id="cdec_cbr",
            category="gauge",
            provider="California Data Exchange Center / California Department of Water Resources",
            title="American River at Chili Bar CBR flow and stage",
            url="https://cdec.water.ca.gov/dynamicapp/staMeta?station_id=CBR",
            license_or_terms="Use under California Department of Water Resources Conditions of Use; preserve station, sensor, timestamp, flag, and retrieval metadata.",
            attribution="Credit California Data Exchange Center / California Department of Water Resources and record CBR station and sensor numbers.",
            access_notes="Use as the primary South Fork modern flow/stage candidate only after flag, no-data, station relation, release context, and guide review are attached.",
            use_in_pipeline=("modern_flow_stage_window", "flow_band_review", "release_pulse_context", "season_windows"),
        ),
        SourceCatalogEntry(
            source_id="cdec_a25_powerhouse_context",
            category="gauge",
            provider="California Data Exchange Center / California Department of Water Resources",
            title="Chili Bar Powerhouse A25 release-operation context",
            url="https://cdec.water.ca.gov/dynamicapp/staMeta?station_id=A25",
            license_or_terms="Use under California Department of Water Resources Conditions of Use; preserve station, sensor, timestamp, flag, and retrieval metadata.",
            attribution="Credit California Data Exchange Center / California Department of Water Resources and record A25 station and sensor numbers.",
            access_notes="Use as release-operation context only unless hydrologic routing and guide review confirm direct relation to raftable reach flow.",
            use_in_pipeline=("release_operation_context", "flow_band_review", "season_windows"),
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
            source_id="ca_state_parks_marshall_gold_discovery",
            category="access",
            provider="California State Parks",
            title="Marshall Gold Discovery State Historic Park",
            url="https://www.parks.ca.gov/?page_id=484",
            license_or_terms="Official park and access context; media, maps, restrictions, and concession references need item-level review before redistribution or in-game use.",
            attribution="Credit California State Parks and Marshall Gold Discovery State Historic Park for official park/access facts used in review manifests.",
            access_notes="Use as the downstream Coloma/state-park source lead, including map, concessionaire, flow-link, water-safety, and restriction review.",
            use_in_pipeline=("access_context", "publication_sensitivity", "guide_reference_leads", "capture_review"),
        ),
        SourceCatalogEntry(
            source_id="el_dorado_county_gis",
            category="access",
            provider="El Dorado County",
            title="El Dorado County GIS Viewer and planning-source leads",
            url="https://www.eldoradocounty.ca.gov/",
            license_or_terms="Official county GIS/planning context; exact datasets, parcel/use restrictions, and redistribution terms must be checked per layer.",
            attribution="Credit El Dorado County for county GIS and planning source layers when used.",
            access_notes="Use for public/private land, road, parcel, river-management, evacuation, and access review leads before route publication.",
            use_in_pipeline=("access_context", "parcel_land_status", "evacuation_review", "publication_sensitivity"),
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
            url=(
                "https://tnmaccess.nationalmap.gov/api/v1/products?"
                f"datasets=Elevation%20Products%20(3D%20Elevation%20Program%20Products%20and%20Services)&bbox={bbox}"
            ),
            target_artifact="terrain/3dep_dem_tiles",
            status="metadata_ready",
            notes=(
                "Representative bounding-box query for DEM discovery; if TNM product metadata is empty, use the official "
                "USGS 3DEP ImageServer/WCS path and record the zero-hit query in the production source-pull manifest."
            ),
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
            fetch_id="sfa_nhd_hu8_18020129_bbox_extract",
            category="hydrography",
            source_id="usgs_3dhp_nhd",
            url="https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/Shape/NHD_H_18020129_HU8_Shape.zip",
            target_artifact=SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
            status="downloaded",
            notes=(
                "Selected HU8 18020129 after comparing adjacent HU8 18020128 against the pilot bbox. "
                "The attached GeoJSON extract is bbox-intersected source evidence, not an ordered production centerline."
            ),
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
            url=f"https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Imagery%20-%20NAIP%20(1%20meter%20to%20.5%20foot)&bbox={bbox}",
            target_artifact="imagery/naip_tiles",
            status="planned",
            notes=(
                "Use most recent leaf-on/low-shadow NAIP where available, then compare with historic imagery at known "
                "gauge values. If TNM product metadata is empty, switch to an official NAIP/USDA image service or index."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_3dep_chili_bar_corridor_sample",
            category="elevation",
            source_id="usgs_3dep",
            url=(
                "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?"
                "bbox=-13458526.4369%2C4684496.9368%2C-13438488.9286%2C4697349.7027&bboxSR=3857&"
                "imageSR=3857&size=512%2C512&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&f=image"
            ),
            target_artifact="terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
            status="downloaded",
            notes="Larger official USGS 3DEP ImageServer export for active Unreal preview relief; still not a complete conditioned corridor DEM.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_naip_chili_bar_corridor_sample",
            category="imagery",
            source_id="usda_naip",
            url=(
                "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer/exportImage?"
                "bbox=-13458526.4369%2C4684496.9368%2C-13438488.9286%2C4697349.7027&bboxSR=3857&"
                "imageSR=3857&size=1024%2C1024&format=png&f=image"
            ),
            target_artifact="imagery/usda_naip_chili_bar_corridor_sample_1024.png",
            status="downloaded",
            notes="Larger official USDA/APFO NAIP ImageServer export for active Unreal preview drape; still not a complete production orthomosaic.",
        ),
        RemoteFetchSpec(
            fetch_id="sfa_naip_chili_bar_corridor_masks",
            category="derived_source_masks",
            source_id="usda_naip_chili_bar_corridor_sample_1024",
            url="physics/src/raftsim/geospatial_preview.py",
            target_artifact=(
                "imagery/usda_naip_chili_bar_corridor_water_mask_1024.png; "
                "imagery/usda_naip_chili_bar_corridor_vegetation_mask_1024.png; "
                "imagery/usda_naip_chili_bar_corridor_masks_manifest.json"
            ),
            status="generated_review_gated_preview_masks",
            notes=(
                "Review-gated preview water and vegetation masks generated from the active 1024px USDA/APFO NAIP drape "
                "plus a bounded generated-preview channel prior. These masks are sampled by Unreal preview terrain/drape "
                "coloring but are not final segmentation, bank polygons, or production masks."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_access_publication_sensitivity_review",
            category="access_and_publication_review",
            source_id="ca_state_parks_marshall_gold_discovery",
            url="https://www.parks.ca.gov/?page_id=484",
            target_artifact=SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
            status="official_source_lead_attached_review_required",
            notes=(
                "Records current State Parks Marshall Gold Discovery access/publication source evidence plus county GIS "
                "and land-manager follow-up leads. This is not access geometry, private/public land authority, or "
                "permission to publish sensitive route details."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_3dep_chili_bar_corridor_heightfield_candidate",
            category="derived_heightfield_candidate",
            source_id="usgs_3dep_chili_bar_corridor_sample_512",
            url="physics/src/raftsim/geospatial_preview.py",
            target_artifact="terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png",
            status="generated_review_gated_import_candidate",
            notes=(
                "Review-gated 1009px 16-bit normalized PNG generated from the official USGS 3DEP corridor sample for Unreal "
                "Landscape import tests. This is not a complete reviewed corridor DEM, reprojected final terrain, hydrologically "
                "conditioned surface, or production Landscape replacement."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_nwis_daily_discharge",
            category="gauge",
            source_id="usgs_nwis",
            url="https://waterservices.usgs.gov/nwis/dv/?format=json&sites=11445500&parameterCd=00060&startDT=1951-01-01&endDT=1995-12-31",
            target_artifact="hydrology/usgs_11445500_daily_discharge.json",
            status="downloaded",
            notes=(
                "Historical daily discharge query for preliminary flow percentiles. Add modern gauge/release context, "
                "instantaneous values, and stage parameter 00065 when building final presets."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_cdec_cbr_event_flow_stage_window",
            category="gauge",
            source_id="cdec_cbr",
            url="https://cdec.water.ca.gov/dynamicapp/req/JSONDataServlet?Stations=CBR&SensorNums=20&dur_code=E&Start=2026-07-05T00:00&End=2026-07-06T23:59",
            target_artifact="hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
            status="downloaded",
            notes=(
                "First reproducible CDEC CBR event-window flow/stage pull for South Fork modern flow review. "
                "Use with the paired stage request and terms/flag review before deriving gameplay bands."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_cdec_terms_flags_station_relation_review",
            category="gauge",
            source_id="cdec_cbr",
            url="https://cdec.water.ca.gov/reportapp/javareports?name=FlagList",
            target_artifact=SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
            status="reviewed",
            notes=(
                "Records DWR Conditions of Use, CDEC FlagList definitions, API documentation links, and the current "
                "CBR/A25 station-to-reach interpretation for review-gated South Fork flow-band promotion."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_cdec_cbr_a25_flow_context_30d",
            category="gauge",
            source_id="cdec_cbr",
            url="https://cdec.water.ca.gov/dynamicapp/req/JSONDataServlet?Stations=CBR&SensorNums=20&dur_code=E&Start=2026-06-07T00:00&End=2026-07-06T23:59",
            target_artifact=SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
            status="downloaded",
            notes=(
                "Compact 30-day CBR flow/stage and A25 daily powerhouse-generation context window. Use for review "
                "discussion only until broader seasonal windows, routing, release interpretation, and guide signoff pass."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_cdec_cbr_a25_seasonal_window_wy2026_to_2026_07_06",
            category="gauge",
            source_id="cdec_cbr",
            url="https://cdec.water.ca.gov/dynamicapp/req/JSONDataServlet?Stations=CBR&SensorNums=20&dur_code=E&Start=2025-10-01T00:00&End=2026-07-06T23:59",
            target_artifact=SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
            status="downloaded",
            notes=(
                "Water-year-to-date CBR flow/stage and A25 daily powerhouse-generation review artifact. Use for "
                "seasonal flow discussion only until multi-year windows, routing, release interpretation, legal "
                "signoff, and guide validation pass."
            ),
        ),
        RemoteFetchSpec(
            fetch_id="sfa_cdec_cbr_multiyear_flow_review_2021_10_01_2026_07_06",
            category="gauge",
            source_id="cdec_cbr",
            url="https://cdec.water.ca.gov/dynamicapp/req/JSONDataServlet?Stations=CBR&SensorNums=20&dur_code=E&Start=2021-10-01T00:00&End=2026-07-06T23:59",
            target_artifact=SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
            status="downloaded",
            notes=(
                "Compact multi-year CBR event-flow review artifact covering four complete water years plus partial "
                "WY2026. Use for representative seasonal-flow discussion only; high-flow peaks, A25 routing, legal "
                "signoff, station-to-rapid relation, and guide validation still block visual/gameplay promotion."
            ),
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


def _web_mercator_xy(lon: float, lat: float) -> tuple[float, float]:
    radius_m = 6378137.0
    clipped_lat = max(-85.05112878, min(85.05112878, lat))
    x = radius_m * math.radians(lon)
    y = radius_m * math.log(math.tan(math.pi / 4.0 + math.radians(clipped_lat) / 2.0))
    return x, y


def _service_tile_grid(bounds: BoundsWGS84, columns: int, rows: int, tile_prefix: str) -> list[dict[str, object]]:
    min_x, min_y = _web_mercator_xy(bounds.min_lon, bounds.min_lat)
    max_x, max_y = _web_mercator_xy(bounds.max_lon, bounds.max_lat)
    tiles: list[dict[str, object]] = []
    for row in range(rows):
        for column in range(columns):
            tile_min_lon = bounds.min_lon + (bounds.max_lon - bounds.min_lon) * column / columns
            tile_max_lon = bounds.min_lon + (bounds.max_lon - bounds.min_lon) * (column + 1) / columns
            tile_min_lat = bounds.min_lat + (bounds.max_lat - bounds.min_lat) * row / rows
            tile_max_lat = bounds.min_lat + (bounds.max_lat - bounds.min_lat) * (row + 1) / rows
            tile_min_x = min_x + (max_x - min_x) * column / columns
            tile_max_x = min_x + (max_x - min_x) * (column + 1) / columns
            tile_min_y = min_y + (max_y - min_y) * row / rows
            tile_max_y = min_y + (max_y - min_y) * (row + 1) / rows
            bbox_3857 = f"{tile_min_x:.4f}%2C{tile_min_y:.4f}%2C{tile_max_x:.4f}%2C{tile_max_y:.4f}"
            tile_id = f"{tile_prefix}_tile_r{row}_c{column}"
            tiles.append(
                {
                    "tile_id": tile_id,
                    "row": row,
                    "column": column,
                    "status": "planned_not_downloaded",
                    "bbox_wgs84": {
                        "min_lon": round(tile_min_lon, 8),
                        "min_lat": round(tile_min_lat, 8),
                        "max_lon": round(tile_max_lon, 8),
                        "max_lat": round(tile_max_lat, 8),
                    },
                    "bbox_epsg3857": {
                        "xmin": round(tile_min_x, 4),
                        "ymin": round(tile_min_y, 4),
                        "xmax": round(tile_max_x, 4),
                        "ymax": round(tile_max_y, 4),
                    },
                    "download_specs": {
                        "3dep_dem_export": {
                            "provider": "USGS 3D Elevation Program ImageServer",
                            "format": "GeoTIFF_F32",
                            "size_px": [1024, 1024],
                            "url": (
                                "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?"
                                f"bbox={bbox_3857}&bboxSR=3857&imageSR=3857&size=1024%2C1024&"
                                "format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&f=image"
                            ),
                            "target_artifact": f"terrain/production_import_pilot/3dep_tiles/{tile_id}.tif",
                        },
                        "naip_export": {
                            "provider": "USDA/APFO NAIP ImageServer",
                            "format": "PNG_RGB",
                            "size_px": [2048, 2048],
                            "url": (
                                "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer/exportImage?"
                                f"bbox={bbox_3857}&bboxSR=3857&imageSR=3857&size=2048%2C2048&format=png&f=image"
                            ),
                            "target_artifact": f"imagery/production_import_pilot/naip_tiles/{tile_id}.png",
                        },
                    },
                }
            )
    return tiles


def build_south_fork_production_import_pilot(section: CandidateRiverSection | None = None) -> dict[str, object]:
    """Build the first executable production-source import recipe for South Fork.

    The recipe is intentionally still planned/review-gated. It converts the broad
    production-data TODO into a deterministic official-service tile plan without
    pretending the current preview samples are production terrain or imagery.
    """

    target = section or south_fork_american_section()
    columns = 2
    rows = 2
    return {
        "schema": PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION,
        "pilot_id": "south_fork_chili_bar_official_service_tile_pilot",
        "river_id": target.river_id,
        "section_id": target.section_id,
        "status": "planned_review_gated_not_downloaded",
        "source_manifest": SOURCE_MANIFEST_FILE,
        "readiness_manifest": "../production_geospatial_source_readiness.json",
        "bounds_wgs84": target.bounds_wgs84.to_json_dict(),
        "working_crs_decision": {
            "status": "required_before_unreal_promotion",
            "candidate": "local_projected_corridor_crs_derived_from_epsg4326_bounds",
            "required_review": [
                "horizontal CRS and units",
                "vertical datum handling for DEM elevations",
                "Unreal origin and scale transform",
                "round-trip error budget against source coordinates",
            ],
        },
        "tile_grid": {
            "columns": columns,
            "rows": rows,
            "source_crs": "EPSG:4326",
            "service_crs": "EPSG:3857",
            "tiles": _service_tile_grid(target.bounds_wgs84, columns, rows, "sfa_chili_bar"),
        },
        "required_source_classes": [
            {
                "class_id": "terrain_dem_or_lidar",
                "status": "pilot_urls_planned",
                "source_ids": ["usgs_3dep"],
                "target_outputs": [
                    "terrain/production_import_pilot/3dep_tiles",
                    "terrain/production_import_pilot/dem_relief_2048.png",
                    "terrain/production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot_derivatives_manifest.json",
                    SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": "Download tiles, mosaic/clip, review voids and artifacts, hydrologically condition, burn the channel, and compare slope/banks to guide-reviewed rapids.",
            },
            {
                "class_id": "hydrography_and_centerline",
                "status": "nhd_hu8_alignment_diagnostic_attached_review_pending",
                "source_ids": ["usgs_3dhp_nhd"],
                "target_outputs": [
                    SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                    SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                    SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                    SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                    SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                    SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                    SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                    SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
                    SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                ],
                "promotion_gate": "Use the attached NHD HU8 extract, derived mainstem candidate, stationing, cross-section seed lines, and preview alignment diagnostic as source evidence, then confirm direction, reproject, improve NAIP/DEM alignment, hand-review banks/rapid stations, and keep OSM only as supplemental access context.",
            },
            {
                "class_id": "aerial_or_satellite_imagery",
                "status": "pilot_urls_planned",
                "source_ids": ["usda_naip", "landsat"],
                "target_outputs": [
                    "imagery/production_import_pilot/naip_tiles",
                    "imagery/production_import_pilot/source_drape_4096.png",
                    "production_import_pilot_derivatives_manifest.json",
                    SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": "Attach acquisition year/date, resolution, CRS, attribution, and scene/tile metadata; use Landsat only for seasonal comparison unless resolution is adequate for masks.",
            },
            {
                "class_id": "water_and_vegetation_masks",
                "status": "requires_new_derivatives_from_pilot_imagery_and_hydrography",
                "source_ids": ["usda_naip", "usgs_3dhp_nhd", "guide_review"],
                "target_outputs": [
                    "imagery/production_import_pilot/water_mask_2048.png",
                    "imagery/production_import_pilot/vegetation_mask_2048.png",
                    "imagery/production_import_pilot/source_masks_manifest.json",
                    SOUTH_FORK_NHD_WATER_PRIOR_MANIFEST_FILE,
                    SOUTH_FORK_NHD_WATER_PRIOR_FILE,
                ],
                "promotion_gate": "Derive masks from reviewed imagery and hydrography, then manually review water edge, seasonal exposure, vegetation, and hazard visibility.",
            },
            {
                "class_id": "seasonal_flow_or_release_history",
                "status": "historical_daily_discharge_usgs_iv_diagnostic_and_cdec_cbr_window_attached_review_pending",
                "source_ids": ["usgs_water_services", "cdec_cbr", "cdec_a25_powerhouse_context", "guide_review"],
                "target_outputs": [
                    "hydrology/usgs_11445500_instantaneous_discharge_stage_p30d_diagnostic.json",
                    "hydrology/south_fork_modern_flow_source_selection.json",
                    "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                    SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                    SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                    SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
                    SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
                    SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
                ],
                "promotion_gate": "Use CDEC CBR as the primary modern flow/stage candidate after the USGS 11445500 IV diagnostic; the first terms/flag/station review, 30-day CBR/A25 context, water-year-to-date seasonal review, and multi-year CBR flow context are attached, but A25 routing, high-flow peak review, legal/redistribution signoff, station-to-reach relation, and guide review are still required before low/median/high visual variants are promoted.",
            },
            {
                "class_id": "protected_area_and_access_context",
                "status": "official_state_park_and_county_gis_leads_attached_review_required",
                "source_ids": [
                    "ca_state_parks_marshall_gold_discovery",
                    "el_dorado_county_gis",
                    "official_land_access_review",
                    "guide_review",
                ],
                "target_outputs": [
                    SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
                    SOUTH_FORK_ACCESS_POINTS_FILE,
                    SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                    SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
                ],
                "promotion_gate": "Review put-ins, take-outs, private/public land, evacuation points, sensitive locations, and what may appear in screenshots or maps.",
            },
            {
                "class_id": "guide_and_reference_media_annotations",
                "status": "link_seeds_attached_no_media_rights",
                "source_ids": ["reference_media_link_manifest", "first_party_field_capture", "explicit_guide_or_outfitter_permission"],
                "target_outputs": [
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                ],
                "promotion_gate": "Attach creator/date/reach/flow/weather/permission before using photos or footage for material, texture, or in-game reference.",
            },
        ],
        "unreal_import_targets": {
            "heightfield_import_contract": "unreal/Content/RaftSim/River/south_fork_heightfield_import_test.json",
            "preview_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview",
            "future_production_map": "/Game/RaftSim/Maps/Production/L_SouthForkAmerican_ChiliBar",
            "review_captures": [
                "docs/environment-captures/photoreal_river_previews/american_south_fork_guide_seat_downstream.png",
                "docs/environment-captures/photoreal_river_previews/american_south_fork_river_eye_downstream.png",
            ],
        },
        "acceptance_gate": [
            "All planned pilot downloads have source metadata, checksums, CRS, acquisition dates, and attribution.",
            "Conditioned heightfield and masks are generated from the pilot tiles and reviewed against hydrography and guide notes.",
            "Unreal preview map can be regenerated from pilot artifacts with hazards, swimmer rescue targets, and water-readability cues still visible.",
            "Screenshots look materially closer to the real South Fork corridor without claiming final photoreal approval.",
        ],
        "provenance": {
            "generated_by": "raftsim.real_world.build_south_fork_production_import_pilot",
            "processing_version": "milestone_26_south_fork_import_pilot.v0",
            "review_status": "recipe_only_downloads_and_imports_pending",
        },
    }


def build_south_fork_production_source_gate_review(section: CandidateRiverSection | None = None) -> dict[str, object]:
    """Summarize whether attached South Fork source data is ready for production promotion."""

    target = section or south_fork_american_section()

    gate_items = [
        {
            "source_class": "terrain_dem_or_lidar",
            "preview_evidence_status": "attached_review_gated",
            "attached_artifacts": [
                "terrain/production_import_pilot/3dep_tiles",
                "terrain/production_import_pilot/dem_relief_2048.png",
                "terrain/production_import_pilot/heightfield_candidate_2017.png",
                SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE,
                SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE,
                SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
            ],
            "promotion_blockers": [
                "full corridor mosaic and clip",
                "full-corridor source metadata and acquisition review beyond the pilot tile envelope",
                "void/artifact review",
                "hydrologic conditioning",
                "channel burning",
                "guide/geospatial approval",
            ],
            "next_decision": "Select conditioned production Landscape/Nanite terrain path after CRS, vertical datum, and channel-burning review.",
        },
        {
            "source_class": "aerial_or_satellite_imagery",
            "preview_evidence_status": "attached_review_gated",
            "attached_artifacts": [
                "imagery/production_import_pilot/naip_tiles",
                "imagery/production_import_pilot/source_drape_4096.png",
                "imagery/production_import_pilot/water_mask_2048.png",
                "imagery/production_import_pilot/vegetation_mask_2048.png",
                "imagery/production_import_pilot/source_masks_manifest.json",
                SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
            ],
            "promotion_blockers": [
                "full-corridor tile acquisition year/date review beyond the pilot tile envelope",
                "orthomosaic or service-derivative metadata review",
                "water/vegetation mask QA against hydrography and visible banks",
                "seasonal exposed-bar and wet-edge review",
                "attribution and redistribution signoff",
            ],
            "next_decision": "Promote only after source drape and masks are accepted as production derivatives or replaced by better imagery.",
        },
        {
            "source_class": "hydrography_and_centerline",
            "preview_evidence_status": "attached_review_gated",
            "attached_artifacts": [
                SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
                SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
                SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
            ],
            "promotion_blockers": [
                "flow direction confirmation",
                "working CRS transform review",
                "bank and wetted-width correction",
                "rapid, eddy, recovery, and swimmer-rescue station review",
                "guide validation against footage or field notes",
            ],
            "next_decision": "Use the attached NHD-derived overlays for editor review, not solver authority, until guide-reviewed banks and stationing pass.",
        },
        {
            "source_class": "seasonal_flow_or_release_history",
            "preview_evidence_status": "attached_review_gated",
            "attached_artifacts": [
                "hydrology/usgs_11445500_daily_discharge.json",
                "hydrology/usgs_11445500_instantaneous_discharge_stage_p30d_diagnostic.json",
                "hydrology/south_fork_modern_flow_source_selection.json",
                "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
                SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
                SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
            ],
            "promotion_blockers": [
                "A25 flag/routing interpretation",
                "official high-flow peak/outlier interpretation for flood-event samples",
                "station-to-reach lag and routing review",
                "legal/redistribution signoff",
                "guide/outfitter validation for low, median, high, and unsafe flows",
            ],
            "next_decision": "Keep flow-band visuals as review presets until seasonal windows and guide validation support retuning.",
        },
        {
            "source_class": "protected_area_and_access_context",
            "preview_evidence_status": "attached_review_gated",
            "attached_artifacts": [
                SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
                SOUTH_FORK_ACCESS_POINTS_FILE,
                SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
            ],
            "promotion_blockers": [
                "exact access geometry and current restriction review",
                "parcel/public-private land status",
                "evacuation route authority",
                "sensitive-location screenshot policy",
                "guide/local approval",
            ],
            "next_decision": "Treat access and no-publish geometry as editor seeds until official layer selection and local review pass.",
        },
        {
            "source_class": "guide_and_reference_media_annotations",
            "preview_evidence_status": "link_scaffold_attached_no_media_rights",
            "attached_artifacts": [
                REFERENCE_MEDIA_ANNOTATIONS_FILE,
                REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
            ],
            "promotion_blockers": [
                "item-level creator/date/reach/flow/weather metadata",
                "explicit permission or compatible license",
                "no scraping or packaged social media without rights",
                "guide review for visual fidelity and raft outcomes",
                "field capture or outfitter-approved reference set",
            ],
            "next_decision": "Use links only as review annotations until first-party or permissioned media can influence production art.",
        },
    ]

    return {
        "schema": "raftsim.south_fork_production_source_gate_review.v1",
        "generated_on": "2026-07-06",
        "river_id": target.river_id,
        "section_id": target.section_id,
        "status": "source_data_attached_for_preview_but_blocked_from_lifelike_promotion",
        "source_manifest": SOURCE_MANIFEST_FILE,
        "gap_register": f"../{PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE}",
        "readiness_manifest": "../production_geospatial_source_readiness.json",
        "active_unreal_preview_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview",
        "promotion_decision": {
            "decision": "do_not_promote_to_production_or_lifelike",
            "reason": "Every source class has useful preview evidence, but guide/geospatial/rights/seasonal-flow review is still open.",
            "can_drive_next_renderer_iteration": True,
            "can_drive_production_terrain_or_water": False,
        },
        "source_gate_items": gate_items,
        "next_checkpoint_recommendation": [
            "Resolve A25 flags/routing, official high-flow event interpretation, station-to-reach timing, legal/redistribution signoff, and guide/outfitter validation before tuning flow variants.",
            "Run guide/geospatial review on NHD-derived centerline, banks, cross sections, eddy/recovery zones, and source masks.",
            "Attach permissioned or first-party South Fork reference photos/footage before photoreal material promotion.",
        ],
    }


def colorado_lees_ferry_import_pilot_bounds() -> BoundsWGS84:
    """Return the current Lees Ferry official-service pilot bounds.

    These bounds intentionally match the existing Colorado preview source pull,
    not the full Lees Ferry-to-Diamond Creek rowing route. Expanding the canyon
    corridor needs river-mile stationing, tiling, and publication review first.
    """

    return BoundsWGS84(min_lon=-111.66, min_lat=36.80, max_lon=-111.54, max_lat=36.90)


def build_colorado_production_import_pilot(bounds: BoundsWGS84 | None = None) -> dict[str, object]:
    """Build the Colorado/Lees Ferry production-source import pilot recipe."""

    target_bounds = bounds or colorado_lees_ferry_import_pilot_bounds()
    columns = 2
    rows = 2
    return {
        "schema": PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION,
        "pilot_id": "colorado_lees_ferry_official_service_tile_pilot",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "route_style": "rowing_oar_rig",
        "status": "planned_review_gated_not_downloaded",
        "source_manifest": SOURCE_MANIFEST_FILE,
        "readiness_manifest": "../production_geospatial_source_readiness.json",
        "bounds_wgs84": target_bounds.to_json_dict(),
        "corridor_scope": {
            "status": "lees_ferry_pilot_slice_not_full_canyon_route",
            "reason": (
                "The pilot reuses the existing official-service sample area near Lees Ferry to prove the canyon import "
                "workflow before expanding river-mile tiles through the full rowing route."
            ),
            "full_route_requires": [
                "river-mile stationing",
                "canyon-local projected CRS",
                "Grand Canyon publication and sensitivity review",
                "guide or oarsman validation",
            ],
        },
        "working_crs_decision": {
            "status": "required_before_unreal_promotion",
            "candidate": "river_mile_stationed_canyon_local_projected_crs_derived_from_epsg4326_bounds",
            "required_review": [
                "horizontal CRS and units",
                "vertical datum handling for canyon DEM elevations",
                "river-mile stationing and downstream transform",
                "Unreal origin and scale transform",
                "round-trip error budget against source coordinates",
                "publication sensitivity for route detail and camps/access context",
            ],
        },
        "tile_grid": {
            "columns": columns,
            "rows": rows,
            "source_crs": "EPSG:4326",
            "service_crs": "EPSG:3857",
            "tiles": _service_tile_grid(target_bounds, columns, rows, "colorado_lees_ferry"),
        },
        "required_source_classes": [
            {
                "class_id": "terrain_dem_or_lidar",
                "status": "pilot_urls_planned",
                "source_ids": ["usgs_3dep"],
                "target_outputs": [
                    "terrain/production_import_pilot/3dep_tiles",
                    "terrain/production_import_pilot/dem_relief_2048.png",
                    "terrain/production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot_derivatives_manifest.json",
                    COLORADO_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Download tiles, mosaic/clip, select canyon CRS, review voids and vertical datum, hydrologically "
                    "condition, burn the channel, and compare canyon walls, shelves, and rapid approaches to river-mile "
                    "references plus guide/oarsman notes."
                ),
            },
            {
                "class_id": "hydrography_and_centerline",
                "status": "nhd_hu8_alignment_diagnostic_attached_review_pending",
                "source_ids": ["usgs_3dhp_nhd", "nps_grand_canyon", "gcmrc_or_river_mile_context"],
                "target_outputs": [
                    COLORADO_NHD_HU8_MANIFEST_FILE,
                    COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                    COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE,
                    COLORADO_NHD_MAINSTEM_MANIFEST_FILE,
                    COLORADO_NHD_MAINSTEM_CANDIDATE_FILE,
                    COLORADO_NHD_MAINSTEM_STATIONING_FILE,
                    COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                    COLORADO_NHD_CROSS_SECTION_SEED_FILE,
                    COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                    COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                    COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    COLORADO_PRODUCTION_BANKS_DRAFT_FILE,
                    COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                    COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE,
                    COLORADO_PRODUCTION_SANDBARS_FILE,
                ],
                "promotion_gate": (
                    "Use the attached stitched NHD HU8 source overlay, exact-graph mainstem candidate, preview "
                    "metric stationing/cross-section seeds, and preview alignment diagnostic as official flowline "
                    "context, then review the line against visible river edge, river-mile stations, sandbars, eddies, "
                    "camps/access sensitivity, and oar-line notes before using the data as authoritative gameplay "
                    "geometry."
                ),
            },
            {
                "class_id": "aerial_or_satellite_imagery",
                "status": "pilot_urls_planned",
                "source_ids": ["usda_naip", "landsat"],
                "target_outputs": [
                    "imagery/production_import_pilot/naip_tiles",
                    "imagery/production_import_pilot/source_drape_4096.png",
                    "production_import_pilot_derivatives_manifest.json",
                    COLORADO_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Attach acquisition year/date, resolution, CRS, attribution, terms, canyon color review, and Landsat "
                    "seasonal context before replacing the current preview drape."
                ),
            },
            {
                "class_id": "water_and_vegetation_masks",
                "status": "nhd_water_prior_attached_release_sandbar_masks_pending",
                "source_ids": ["usda_naip", "landsat", "usgs_3dhp_nhd", "usbr_glen_canyon_release_context", "guide_review"],
                "target_outputs": [
                    "imagery/production_import_pilot/water_mask_2048.png",
                    "imagery/production_import_pilot/vegetation_mask_2048.png",
                    COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE,
                    COLORADO_NHD_WATER_PRIOR_FILE,
                    "imagery/production_import_pilot/sandbar_wet_bank_mask_2048.png",
                    "imagery/production_import_pilot/source_masks_manifest.json",
                ],
                "promotion_gate": (
                    "Derive masks from reviewed imagery, hydrography, release-band context, and the NHD prior as an "
                    "editor aid, then manually review water edge, exposed sandbars, wet rock, tamarisk/cottonwood/scrub, "
                    "and release-dependent visibility."
                ),
            },
            {
                "class_id": "seasonal_flow_or_release_history",
                "status": "usgs_daily_discharge_and_usbr_release_context_attached_review_pending",
                "source_ids": [
                    "usgs_water_services",
                    "usgs_09380000_lees_ferry",
                    "usgs_09402500_near_grand_canyon",
                    "usbr_glen_canyon_release_context",
                ],
                "target_outputs": [
                    "hydrology/production_import_pilot/usgs_09380000_instantaneous_discharge.json",
                    "hydrology/production_import_pilot/usgs_09402500_instantaneous_discharge.json",
                    COLORADO_USBR_TOTAL_RELEASE_FILE,
                    COLORADO_USBR_RELEASE_CONTEXT_FILE,
                    COLORADO_RELEASE_BAND_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Use the attached Reclamation daily total-release series as review-gated context, confirm units and terms, "
                    "compare with hourly/subdaily patterns plus Lees Ferry and downstream USGS gauges, then record guide/"
                    "oarsman review for low, moderate, high, and special-release visual/gameplay bands."
                ),
            },
            {
                "class_id": "protected_area_and_access_context",
                "status": "official_nps_access_publication_leads_attached_review_required",
                "source_ids": [
                    "nps_grand_canyon_river_trips_permits",
                    "nps_grand_canyon_noncommercial_river_trip_links",
                    "nps_grand_canyon_lees_ferry_diamond_creek_overview",
                    "nps_grand_canyon_noncommercial_river_trip_regulations_pdf",
                    "guide_review",
                ],
                "target_outputs": [
                    COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
                    COLORADO_ACCESS_POINTS_FILE,
                    COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                    COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
                    COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE,
                ],
                "promotion_gate": (
                    "Use the attached NPS source-lead review only as publication/access context; exact launch, take-out, "
                    "camp/beach, sensitive-resource, permit-text, and screenshot-safety review must pass before committing "
                    "detailed route packages."
                ),
            },
            {
                "class_id": "guide_and_reference_media_annotations",
                "status": "link_seeds_attached_no_media_rights",
                "source_ids": [
                    "reference_media_link_manifest",
                    "first_party_field_capture",
                    "explicit_oarsman_or_outfitter_permission",
                    "nps_grand_canyon",
                ],
                "target_outputs": [
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                ],
                "promotion_gate": (
                    "Attach creator, date, reach or river mile, flow/release context, permission, attribution, and allowed "
                    "asset uses before photos or footage drive textures, materials, or gameplay tuning."
                ),
            },
        ],
        "unreal_import_targets": {
            "heightfield_import_contract": "unreal/Content/RaftSim/River/colorado_heightfield_import_test.json",
            "preview_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview",
            "future_production_map": "/Game/RaftSim/Maps/Production/L_ColoradoGrandCanyon_LeesFerryRowing",
            "review_captures": [
                "docs/environment-captures/photoreal_river_previews/colorado_river_guide_seat_downstream.png",
                "docs/environment-captures/photoreal_river_previews/colorado_river_river_eye_downstream.png",
            ],
        },
        "acceptance_gate": [
            "All planned pilot downloads have source metadata, checksums, CRS, acquisition dates, and attribution.",
            "Conditioned heightfield and masks are generated from the pilot tiles and reviewed against hydrography, release bands, river-mile context, and guide/oarsman notes.",
            "Unreal preview map can be regenerated from pilot artifacts with big-water readability, rowing sightlines, sandbars, swimmer rescue targets, and canyon-scale depth still visible.",
            "Screenshots look materially closer to the real Lees Ferry/Grand Canyon corridor without claiming final photoreal approval.",
        ],
        "provenance": {
            "generated_by": "raftsim.real_world.build_colorado_production_import_pilot",
            "processing_version": "milestone_26_colorado_import_pilot.v0",
            "review_status": "recipe_only_downloads_and_imports_pending",
        },
    }


def build_colorado_release_band_review(
    flow_presets: dict[str, object],
    usbr_total_release: dict[str, object],
    release_context: dict[str, object],
) -> dict[str, object]:
    """Compare Colorado rowing planning bands to attached USBR Glen Canyon release history."""

    rows: list[tuple[date, float]] = []
    for raw_date, raw_value in usbr_total_release["data"]:
        if raw_value is None:
            continue
        rows.append((date.fromisoformat(raw_date), float(raw_value)))
    if not rows:
        raise ValueError("USBR release series has no valid daily values")

    latest_date = max(row_date for row_date, _value in rows)
    last_365_start = latest_date - timedelta(days=365)
    windows = {
        "all_available": rows,
        "post_2000_operations": [(row_date, value) for row_date, value in rows if row_date >= date(2000, 1, 1)],
        "last_365_available_days": [(row_date, value) for row_date, value in rows if row_date >= last_365_start],
        "water_year_2026_to_date": [(row_date, value) for row_date, value in rows if row_date >= date(2025, 10, 1)],
    }

    def summarize_window(window_rows: list[tuple[date, float]], threshold_cfs: float) -> dict[str, object]:
        values = np.asarray([value for _row_date, value in window_rows], dtype=np.float64)
        days_ge = [(row_date, value) for row_date, value in window_rows if value >= threshold_cfs]
        peak_examples = sorted(days_ge, key=lambda item: item[1], reverse=True)[:8]
        return {
            "day_count": len(window_rows),
            "days_ge_planning_flow": len(days_ge),
            "fraction_ge_planning_flow": round(len(days_ge) / max(len(window_rows), 1), 6),
            "min_cfs": round(float(np.min(values)), 3),
            "median_cfs": round(float(np.median(values)), 3),
            "mean_cfs": round(float(np.mean(values)), 3),
            "max_cfs": round(float(np.max(values)), 3),
            "peak_examples": [
                {"date": row_date.isoformat(), "release_cfs": round(value, 3)} for row_date, value in peak_examples
            ],
        }

    reviewed_bands: list[dict[str, object]] = []
    for band in flow_presets["flow_bands"]:
        threshold_cfs = float(band["discharge_cfs"])
        window_summaries = {
            window_name: summarize_window(window_rows, threshold_cfs)
            for window_name, window_rows in windows.items()
            if window_rows
        }
        wy_days = window_summaries["water_year_2026_to_date"]["days_ge_planning_flow"]
        if wy_days > 0:
            evidence_status = "observed_in_water_year_2026_daily_release_context_not_subdaily_validation"
        else:
            evidence_status = "not_observed_in_water_year_2026_daily_release_context"
        reviewed_bands.append(
            {
                "flow_band": band["flow_band"],
                "display_name": band["display_name"],
                "planning_discharge_cfs": threshold_cfs,
                "planning_discharge_m3s": band["discharge_m3s"],
                "expected_rowing_behavior": band["expected_rowing_behavior"],
                "review_priority": band["review_priority"],
                "window_summaries": window_summaries,
                "evidence_status": evidence_status,
                "promotion_decision": "blocked_pending_units_subdaily_release_routing_sandbar_wet_bank_oarsman_review",
                "review_use": (
                    "Use as a release-band discussion aid only; do not retune water level, sandbar exposure, wave trains, "
                    "boils, swimmer drift, or rowing gameplay from daily release totals alone."
                ),
            }
        )

    return {
        "schema": "raftsim.colorado_release_band_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "review_gated_do_not_promote_release_bands",
        "inputs": {
            "flow_presets": "physics/data/real_world/colorado_river_grand_canyon_rowing/flow_presets.json",
            "usbr_total_release": "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrology/production_import_pilot/usbr_glen_canyon_total_release_daily.json",
            "release_context": "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrology/production_import_pilot/usbr_glen_canyon_release_context.json",
            "lees_ferry_gauge": "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrology/usgs_09380000_daily_discharge.json",
            "downstream_gauge": "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrology/usgs_09402500_daily_discharge.json",
        },
        "release_context_summary": {
            "all_available": release_context["usbr_total_release_summary"]["all_available"],
            "post_2000_operations": release_context["usbr_total_release_summary"]["post_2000_operations"],
            "last_365_available_days": release_context["usbr_total_release_summary"]["last_365_available_days"],
            "water_year_2026_to_date": release_context["usbr_total_release_summary"]["water_year_2026_to_date"],
            "release_visual_band_candidates": release_context["release_visual_band_candidates"],
            "daily_comparison_ids": [comparison["comparison_id"] for comparison in release_context["daily_comparisons"]],
        },
        "reviewed_bands": reviewed_bands,
        "promotion_blockers": [
            "The USBR dashboard/JSON still needs explicit unit metadata and terms confirmation before final flow bands.",
            "Daily total releases do not capture hourly/subdaily hydropower fluctuations, downstream routing, tributary inflow, or side storage.",
            "River-mile travel-time review, sandbar/wet-bank masks, oar-line annotations, and guide/oarsman validation remain open.",
            "The current 18000 cfs high-release planning band is not observed in water-year 2026 to date and needs separate high-release evidence.",
        ],
        "allowed_use": [
            "editor release-band review",
            "sandbar and wet-bank planning",
            "guide/oarsman discussion",
            "future low/moderate/high release visual variant planning",
        ],
        "forbidden_use": [
            "final release-band promotion",
            "claiming accepted river-mile hydrology",
            "production lifelike water approval",
            "hiding water-simulation conservation failures with visuals or forcing",
        ],
    }


def build_colorado_access_publication_review() -> dict[str, object]:
    """Build the review-gated Colorado/Grand Canyon access and publication source artifact."""

    return {
        "schema": "raftsim.colorado_access_publication_sensitivity_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "official_nps_river_access_publication_leads_attached_review_gated",
        "scope": (
            "Grand Canyon route access, launch/take-out context, noncommercial trip regulations, camps/beaches, "
            "river-mile publication sensitivity, media/source-use caveats, and oarsman review planning for the "
            "Colorado River rowing production environment pilot."
        ),
        "sources_checked": [
            {
                "source_id": "nps_grand_canyon_river_trips_permits",
                "provider": "National Park Service Grand Canyon",
                "url": "https://www.nps.gov/grca/planyourvisit/whitewater-rafting.htm",
                "retrieved_on": "2026-07-06",
                "page_updated": "2026-06-03",
                "http_status": 200,
                "review_status": "official_page_reviewed",
                "evidence": [
                    "NPS River Trips / Permits page covers Colorado River trip planning through Grand Canyon.",
                    "Page links commercial and noncommercial trip context, Lees Ferry to Diamond Creek overview, and river trip regulations.",
                    "Use as official route/access/publication context only; do not import page media, maps, or geometry as production assets.",
                ],
                "artifact_use": "official Grand Canyon river-trip source lead for route access and publication review",
                "blocked_from": [
                    "permit or legal advice",
                    "final put-in or take-out geometry",
                    "shipping NPS page media, maps, or screenshots as art assets",
                    "claiming camps, beaches, or sensitive locations are publication-cleared",
                ],
            },
            {
                "source_id": "nps_grand_canyon_noncommercial_river_trip_links",
                "provider": "National Park Service Grand Canyon",
                "url": "https://www.nps.gov/grca/planyourvisit/noncommercial-riv-docs.htm",
                "retrieved_on": "2026-07-06",
                "page_updated": "2026-05-08",
                "http_status": 200,
                "review_status": "official_page_reviewed",
                "evidence": [
                    "Page lists Lees Ferry as a starting location and Diamond Creek/Pearce Ferry as take-out locations for noncommercial support review.",
                    "Page links noncommercial river trip regulations and related official trip documents.",
                    "Use as a source-lead index only until the exact documents, dates, terms, and human review are recorded.",
                ],
                "artifact_use": "launch/take-out document index and regulation-source lead",
                "blocked_from": [
                    "current permit availability claims",
                    "operational instructions",
                    "exact trip logistics or fees in gameplay text",
                ],
            },
            {
                "source_id": "nps_grand_canyon_lees_ferry_diamond_creek_overview",
                "provider": "National Park Service Grand Canyon",
                "url": "https://www.nps.gov/grca/planyourvisit/overview-lees-ferry-diamond-ck.htm",
                "retrieved_on": "2026-07-06",
                "page_updated": "2025-06-06",
                "http_status": 200,
                "review_status": "official_page_reviewed",
                "evidence": [
                    "Overview page provides Lees Ferry to Diamond Creek route, river-mile, camping/beach, and take-out context.",
                    "Use for station-aware review planning, not as final river-mile geometry or a camps/beaches publication clearance.",
                ],
                "artifact_use": "river-mile, camp/beach, and take-out context lead for manual editor annotations",
                "blocked_from": [
                    "final river-mile stationing",
                    "publishing detailed camp or beach locations without sensitivity review",
                    "using page photos or maps as texture or art inputs",
                ],
            },
            {
                "source_id": "nps_grand_canyon_noncommercial_river_trip_regulations_pdf",
                "provider": "National Park Service Grand Canyon",
                "url": "https://www.nps.gov/grca/planyourvisit/upload/Noncommercial_River_Trip_Regulations.pdf",
                "retrieved_on": "2026-07-06",
                "document_revision": "2024-12-20",
                "http_status": "linked_from_official_page_not_imported",
                "review_status": "official_pdf_lead_attached_manual_review_required",
                "evidence": [
                    "Linked by NPS as the revised noncommercial river trip regulations PDF.",
                    "The PDF is not vendored, parsed, or treated as a game instruction source by this artifact.",
                ],
                "artifact_use": "manual policy and publication-sensitivity review lead",
                "blocked_from": [
                    "quoting or reproducing regulation text",
                    "in-game legal guidance",
                    "route package promotion without human review",
                ],
            },
        ],
        "station_review_zones": [
            {
                "zone_id": "lees_ferry_launch_review_zone",
                "river_mile_range": [0.0, 1.0],
                "review_status": "official_nps_launch_context_attached_geometry_pending",
                "needs": [
                    "exact launch, rigging, parking, and staging geometry from approved source layers",
                    "river-mile zero and local working-CRS confirmation",
                    "permit/trip-document date review before any game-facing wording",
                    "oarsman validation of launch sightlines and traffic flow",
                ],
            },
            {
                "zone_id": "grand_canyon_camps_beaches_sensitive_context_review_zone",
                "river_mile_range": [1.0, 224.0],
                "review_status": "route_context_leads_attached_publication_sensitivity_pending",
                "needs": [
                    "camp/beach/sandbar publication-sensitivity review",
                    "sensitive-resource and cultural-resource screening before detailed screenshots",
                    "river-mile stationing and release-dependent wet-bank/sandbar review",
                    "guide/oarsman notes for scouting, rescue, and long swimmer drift",
                ],
            },
            {
                "zone_id": "diamond_creek_takeout_review_zone",
                "river_mile_range": [224.0, 226.0],
                "review_status": "official_nps_takeout_context_attached_geometry_pending",
                "needs": [
                    "exact take-out and road/access geometry from approved sources",
                    "current access, fee, and operating-constraint review",
                    "publication sensitivity and screenshot framing review",
                    "oarsman validation before production route package promotion",
                ],
            },
        ],
        "required_editor_annotations": [
            COLORADO_ACCESS_POINTS_FILE,
            COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
            COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
            COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE,
        ],
        "allowed_use": [
            "source-lead triage",
            "station-aware route annotation planning",
            "publication-sensitivity checklist gating",
            "preventing detailed Grand Canyon map or screenshot publication before review",
        ],
        "forbidden_use": [
            "permit or legal advice",
            "final put-in or take-out geometry",
            "current operation, fee, or access claims without day-of source review",
            "publishing camps, beaches, sensitive resources, or detailed access geometry without review",
            "using NPS media, PDFs, maps, or screenshots as texture or art assets",
        ],
        "promotion_blockers": [
            "Exact launch, take-out, staging, road, river-mile, camp, beach, and sensitive-location geometries are not attached.",
            "NPS document dates and operational constraints must be manually reviewed before any game-facing route language.",
            "Cultural-resource, camp/beach, and sensitive-location publication rules need human review before detailed screenshots.",
            "Guide/oarsman review is required before access, scouting, rescue, or rowing-route gameplay uses these zones.",
        ],
    }


def build_reference_media_annotations_geojson(
    river_id: str,
    review_queue: dict[str, object],
    stationing: dict[str, object] | None = None,
    stationing_source: str | None = None,
) -> dict[str, object]:
    """Build link-only station-aware media review annotations for a river."""

    targets = [target for target in review_queue["review_targets"] if target["river_id"] == river_id]
    if not targets:
        raise ValueError(f"No reference media review targets found for river_id={river_id!r}")

    station_samples = list(stationing.get("station_samples", [])) if stationing else []
    station_end_m = float(station_samples[-1]["station_m"]) if station_samples else None

    def station_sample_for_target(target_id: str) -> dict[str, object] | None:
        if not station_samples or station_end_m is None:
            return None
        fraction = REFERENCE_MEDIA_TARGET_STATION_FRACTIONS.get(target_id, 0.5)
        target_station = station_end_m * fraction
        return min(station_samples, key=lambda sample: abs(float(sample["station_m"]) - target_station))

    features: list[dict[str, object]] = []
    for index, target in enumerate(targets):
        station_sample = station_sample_for_target(target["target_id"])
        geometry = None
        station_properties: dict[str, object] = {
            "stationing_status": "anchor_hint_only_needs_editor_station_or_geometry",
            "station_source": None,
            "station_m": None,
            "station_sample_index": None,
        }
        if station_sample is not None:
            geometry = {
                "type": "Point",
                "coordinates": [station_sample["lon"], station_sample["lat"]],
            }
            station_properties = {
                "stationing_status": "review_seed_from_existing_stationing_scaffold_not_authoritative",
                "station_source": stationing_source or "provided_stationing_scaffold",
                "station_m": station_sample["station_m"],
                "station_sample_index": station_sample["sample_index"],
                "station_seed_fraction": REFERENCE_MEDIA_TARGET_STATION_FRACTIONS.get(target["target_id"], 0.5),
            }
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "annotation_id": target["target_id"],
                    "river_id": river_id,
                    "target_id": target["target_id"],
                    "anchor_hint": target["anchor_hint"],
                    "feature_role": "link_only_reference_media_review_target",
                    **station_properties,
                    "review_status": "candidate_links_only_no_media_downloaded",
                    "rights_status": target["rights_status"],
                    "visual_questions": target["visual_questions"],
                    "candidate_source_ids": target["candidate_source_ids"],
                    "flow_context_needed": target["flow_context_needed"],
                    "source_review_queue_index": index,
                    "promotion_gate": (
                        "Attach creator, URL, date, approximate station/reach, observed flow or weather context, "
                        "license or written permission, attribution, and guide/outfitter approval before this "
                        "reference can drive production art, water, or gameplay tuning."
                    ),
                    "blocked_use_before_rights_clear": [
                        "media download or scraping",
                        "texture, photogrammetry, or material extraction",
                        "AI training or generated-asset prompting from third-party media",
                        "marketing or public screenshot claims based on unreviewed media",
                    ],
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "schema": "raftsim.reference_media_annotations.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": river_id,
        "status": (
            "link_only_annotation_targets_with_review_seed_geometry_no_media_downloaded"
            if station_samples
            else "link_only_annotation_targets_no_media_downloaded"
        ),
        "source_review_queue": "physics/data/real_world/reference_media_review_queue.json",
        "stationing_source": stationing_source,
        "rights_manifest": REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
        "policy": review_queue["policy"],
        "features": features,
    }


def build_reference_media_rights_manifest(
    river_id: str,
    link_manifest: dict[str, object],
    review_queue: dict[str, object],
) -> dict[str, object]:
    """Build a link-only media rights manifest for a river's review targets."""

    river_entry = next((river for river in link_manifest["rivers"] if river["river_id"] == river_id), None)
    if river_entry is None:
        raise ValueError(f"No reference media link manifest entry found for river_id={river_id!r}")
    targets = [target for target in review_queue["review_targets"] if target["river_id"] == river_id]
    if not targets:
        raise ValueError(f"No reference media review targets found for river_id={river_id!r}")

    candidate_links = []
    for link in river_entry["candidate_links"]:
        candidate_links.append(
            {
                "source_id": link["source_id"],
                "source_type": link["source_type"],
                "provider": link["provider"],
                "url": link["url"],
                "rights_status": link["rights_status"],
                "allowed_before_rights_clear": [
                    "manual visual comparison",
                    "guide/outfitter discussion",
                    "permission outreach planning",
                    "internal station annotation placeholders",
                ],
                "blocked_before_rights_clear": [
                    "download",
                    "scrape",
                    "vendor",
                    "train_on",
                    "texture_or_material_derivation",
                    "photogrammetry",
                    "packaged_media",
                    "marketing_or_public_promo_use",
                ],
                "notes": link["notes"],
            }
        )

    return {
        "schema": "raftsim.reference_media_rights_manifest.v1",
        "generated_on": "2026-07-06",
        "river_id": river_id,
        "section_id": river_entry["section_id"],
        "status": "candidate_links_only_no_media_downloaded_no_rights_cleared",
        "source_link_manifest": "physics/data/real_world/reference_media_link_manifest.json",
        "source_review_queue": "physics/data/real_world/reference_media_review_queue.json",
        "reference_annotations": REFERENCE_MEDIA_ANNOTATIONS_FILE,
        "policy": {
            "storage": link_manifest["policy"]["storage"],
            "shipping_rule": link_manifest["policy"]["shipping_rule"],
            "social_rule": link_manifest["policy"]["social_rule"],
            "review_queue_promotion_gate": review_queue["policy"]["promotion_gate"],
            "blocked_use_before_rights_clear": review_queue["policy"]["blocked_use_before_rights_clear"],
        },
        "rights_summary": {
            "candidate_link_count": len(candidate_links),
            "review_target_count": len(targets),
            "promoted_item_count": 0,
            "media_files_downloaded": 0,
            "rights_cleared_for_asset_use": 0,
            "status": "no_media_or_rights_promoted",
        },
        "candidate_links": candidate_links,
        "review_targets": [
            {
                "target_id": target["target_id"],
                "anchor_hint": target["anchor_hint"],
                "candidate_source_ids": target["candidate_source_ids"],
                "flow_context_needed": target["flow_context_needed"],
                "rights_status": target["rights_status"],
                "annotation_outputs": target["annotation_outputs"],
            }
            for target in targets
        ],
        "promoted_items": [],
        "required_fields_before_promotion": [
            "creator_or_rights_holder",
            "source_url",
            "capture_or_publication_date",
            "approximate_station_or_reach",
            "observed_flow_or_release_or_rain_context",
            "license_or_written_permission",
            "attribution_text",
            "allowed_game_uses",
            "guide_or_outfitter_review_notes",
        ],
        "forbidden_use": [
            "using public social media as source textures or training data",
            "downloading thumbnails, videos, captions, comments, or audio without rights",
            "claiming photoreal fidelity from unreviewed media",
            "shipping third-party media or derived assets without explicit rights",
        ],
    }


def build_pacuare_rainfall_station_review(
    rainfall_context: dict[str, object],
    gauge_search: dict[str, object],
    snit_layer_catalog_summary: dict[str, object],
    snit_layer_metadata_summary: dict[str, object],
) -> dict[str, object]:
    """Summarize Pacuare rainfall and rain-station candidates from archived metadata."""

    metadata_layers = {
        layer["candidate_id"]: layer
        for layer in snit_layer_metadata_summary["metadata_layers"]
        if "candidate_id" in layer
    }
    review_nodes = {
        "snit_imn": "rainfall_climatology_context",
        "snit_senara_estaciones": "rain_station_discovery",
        "snit_senara_recarga": "recharge_context_not_station_authority",
    }
    candidate_layers: list[dict[str, object]] = []
    for node in snit_layer_catalog_summary["node_layer_archives"]:
        node_id = node["node_id"]
        if node_id not in review_nodes:
            continue
        for layer in node.get("selected_candidate_layers", []):
            metadata = next(
                (
                    metadata_layer
                    for metadata_layer in metadata_layers.values()
                    if metadata_layer.get("selected_layer_name") == layer.get("name")
                    or metadata_layer.get("distribution_layer") == layer.get("layer")
                ),
                None,
            )
            candidate_layers.append(
                {
                    "candidate_id": layer["name"].lower().replace(" ", "_").replace(":", "_"),
                    "source_node_id": node_id,
                    "review_role": review_nodes[node_id],
                    "name": layer["name"],
                    "layer": layer["layer"],
                    "institution": layer.get("institution"),
                    "publication_or_catalog_date": layer.get("publication_or_catalog_date"),
                    "wfs_available": bool(layer.get("wfs_available")),
                    "has_metadata": bool(layer.get("has_metadata")),
                    "metadata_file": metadata.get("metadata_file") if metadata else None,
                    "metadata_terms_status": metadata.get("terms_status") if metadata else "metadata_not_attached",
                    "abstract": layer.get("abstract"),
                    "feature_download_status": layer.get("feature_download_status", "not_downloaded_metadata_only"),
                    "promotion_gate": layer.get(
                        "promotion_gate",
                        "Review terms, CRS, attributes, layer extent, Pacuare corridor intersection, and guide/local interpretation before import or gameplay use.",
                    ),
                }
            )

    return {
        "schema": "raftsim.pacuare_rainfall_station_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "metadata_only_rainfall_station_candidates_attached_numeric_flow_blocked",
        "inputs": {
            "rainfall_context": "physics/data/real_world/pacuare_river_costa_rica/hydrology/rainfall_context.json",
            "gauge_search": "physics/data/real_world/pacuare_river_costa_rica/hydrology/costa_rica_gauge_search.json",
            "snit_layer_catalog_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/snit_layer_catalog_summary.json",
            "snit_layer_metadata_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/snit_layer_metadata_summary.json",
        },
        "policy": {
            "feature_downloads_performed": False,
            "station_time_series_imported": False,
            "numeric_flow_bands_promoted": False,
            "use_as_metadata_review_only": True,
        },
        "candidate_layers": candidate_layers,
        "candidate_layer_summary": {
            "candidate_layer_count": len(candidate_layers),
            "wfs_available_count": sum(1 for layer in candidate_layers if layer["wfs_available"]),
            "metadata_attached_count": sum(1 for layer in candidate_layers if layer["has_metadata"]),
            "imn_precipitation_layers": sum(1 for layer in candidate_layers if layer["source_node_id"] == "snit_imn"),
            "senara_station_layers": sum(
                1 for layer in candidate_layers if layer["source_node_id"] == "snit_senara_estaciones"
            ),
        },
        "flow_band_questions": [
            {
                "flow_band": item["flow_band"],
                "needed_evidence": item["needed_evidence"],
                "review_status": "blocked_until_station_ids_records_basin_relation_and_guide_review",
            }
            for item in rainfall_context["seasonal_context_to_resolve"]
        ],
        "needed_station_metadata": gauge_search["needed_station_metadata"],
        "next_actions": [
            "Select exact IMN/SENARA rainfall or station layers and record terms, CRS, attributes, and units.",
            "Pull only approved station features or time-series metadata after terms and attribution are clear.",
            "Relate candidate stations to the lower Pacuare basin and corridor before tuning rain-fed flow bands.",
            "Add discharge/stage station review and flash-response review before any Pacuare numeric flow or water visual promotion.",
        ],
        "promotion_blockers": [
            "No station IDs, coordinates, variables, units, time zones, temporal coverage, or quality flags are attached yet.",
            "No rainfall, discharge, stage, or flash-response time series are imported.",
            "Layer bboxes and WFS availability are discovery metadata, not proof of Pacuare-basin relevance.",
            "Guide/outfitter review is required before rain-fed flow bands change gameplay, hazards, swimmer rescue timing, or visuals.",
        ],
        "allowed_use": [
            "rainfall station source triage",
            "Pacuare hydrology annotation planning",
            "future dry/runnable/high/flash flow-band evidence checklist",
        ],
        "forbidden_use": [
            "numeric Pacuare flow-band promotion",
            "production water-level or foam tuning",
            "claiming accepted station-to-corridor hydrology",
            "shipping flash-response scenarios without station records and guide review",
        ],
    }


def build_pacuare_discharge_stage_station_review(
    gauge_search: dict[str, object],
    da_sinigirh_summary: dict[str, object],
    snit_layer_catalog_summary: dict[str, object],
) -> dict[str, object]:
    """Summarize Pacuare discharge/stage station candidates from archived official metadata."""

    target_layer_names = {
        "Aguas:DA_AFOROS",
        "Aguas:JASEC_ESTACIONES_HIDROMETRICAS",
        "Aguas:DA_UNIDADES_HIDROLOGICAS",
    }
    da_candidates = [
        layer
        for layer in da_sinigirh_summary["selected_candidate_layers"]
        if layer["name"] in target_layer_names
    ]
    snit_da_layers: list[dict[str, object]] = []
    for node in snit_layer_catalog_summary["node_layer_archives"]:
        if node["node_id"] != "snit_direccion_de_agua":
            continue
        snit_da_layers = [
            layer
            for layer in node.get("selected_candidate_layers", [])
            if layer.get("layer") in target_layer_names
        ]
        break

    return {
        "schema": "raftsim.pacuare_discharge_stage_station_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "metadata_only_discharge_stage_candidates_attached_numeric_flow_blocked",
        "inputs": {
            "gauge_search": "physics/data/real_world/pacuare_river_costa_rica/hydrology/costa_rica_gauge_search.json",
            "da_sinigirh_wms_capabilities_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/direccion_de_agua_sinigirh_wms_capabilities_summary.json",
            "snit_layer_catalog_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/snit_layer_catalog_summary.json",
        },
        "policy": {
            "feature_downloads_performed": False,
            "station_time_series_imported": False,
            "numeric_flow_bands_promoted": False,
            "use_as_metadata_review_only": True,
        },
        "da_sinigirh_candidates": da_candidates,
        "snit_direccion_de_agua_candidates": snit_da_layers,
        "candidate_summary": {
            "da_sinigirh_candidate_count": len(da_candidates),
            "snit_direccion_de_agua_candidate_count": len(snit_da_layers),
            "primary_station_candidate_layers": [
                "Aguas:DA_AFOROS",
                "Aguas:JASEC_ESTACIONES_HIDROMETRICAS",
            ],
            "basin_relation_candidate_layers": ["Aguas:DA_UNIDADES_HIDROLOGICAS"],
            "wfs_feature_access_advertised_count": sum(1 for layer in snit_da_layers if layer.get("wfs_available")),
        },
        "needed_station_metadata": gauge_search["needed_station_metadata"],
        "gameplay_questions_to_answer": gauge_search["gameplay_questions_to_answer"],
        "next_actions": [
            "Confirm layer-specific terms, attributes, CRS axis order, and whether station feature access is public.",
            "Identify whether DA_AFOROS or JASEC_ESTACIONES_HIDROMETRICAS intersects the Pacuare basin.",
            "Record station ids, variables, units, time zone, coverage, quality flags, and basin relation before numeric flow tuning.",
            "Pair station review with rainfall and flash-response review plus guide/outfitter validation before water visuals change.",
        ],
        "promotion_blockers": [
            "No station feature records, station ids, variables, units, time zones, or time series are attached.",
            "Layer bboxes are broad service extents and do not prove Pacuare-basin relevance.",
            "DA/SINIGIRH selected WMS candidates advertise metadata only; no WFS or time-series payload is archived by this artifact.",
            "Guide/outfitter review is required before stage/discharge evidence changes hazards, swimmer drift, rescue timing, or visuals.",
        ],
        "allowed_use": [
            "discharge and stage station source triage",
            "Pacuare basin-relation planning",
            "future flow-band evidence checklist",
        ],
        "forbidden_use": [
            "numeric Pacuare flow-band promotion",
            "production water-level or foam tuning",
            "claiming accepted station-to-corridor hydrology",
            "shipping high-water or flash-response scenarios without station records and guide review",
        ],
    }


def build_pacuare_flash_response_review(
    rainfall_context: dict[str, object],
    rainfall_station_review: dict[str, object],
    discharge_stage_review: dict[str, object],
    da_sinigirh_summary: dict[str, object],
    snit_layer_catalog_summary: dict[str, object],
) -> dict[str, object]:
    """Summarize metadata-only Pacuare flash-response review blockers."""

    flash_band = next(
        item
        for item in rainfall_context["seasonal_context_to_resolve"]
        if item["flow_band"] == "flash_response_review_only"
    )
    da_basin_candidates = [
        layer
        for layer in da_sinigirh_summary["selected_candidate_layers"]
        if layer["name"] in {"Aguas:DA_UNIDADES_HIDROLOGICAS", "Aguas:DA_Cuencas_Hidrograficas_CR"}
    ]
    snit_context_layers: list[dict[str, object]] = []
    for node in snit_layer_catalog_summary["node_layer_archives"]:
        if node["node_id"] not in {"snit_direccion_de_agua", "snit_senara_recarga"}:
            continue
        for layer in node.get("selected_candidate_layers", []):
            if layer.get("layer") in {
                "Aguas:DA_UNIDADES_HIDROLOGICAS",
                "Recarga_Siquirres_SIRGAS",
            }:
                snit_context_layers.append(layer)

    return {
        "schema": "raftsim.pacuare_flash_response_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "metadata_only_flash_response_context_attached_model_blocked",
        "inputs": {
            "rainfall_context": "physics/data/real_world/pacuare_river_costa_rica/hydrology/rainfall_context.json",
            "rainfall_station_review": "physics/data/real_world/pacuare_river_costa_rica/hydrology/production_import_pilot/rainfall_station_review.json",
            "discharge_stage_station_review": "physics/data/real_world/pacuare_river_costa_rica/hydrology/production_import_pilot/discharge_or_stage_station_review.json",
            "da_sinigirh_wms_capabilities_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/direccion_de_agua_sinigirh_wms_capabilities_summary.json",
            "snit_layer_catalog_summary": "physics/data/real_world/pacuare_river_costa_rica/hydrography/production_import_pilot/snit_layer_catalog_summary.json",
        },
        "policy": {
            "feature_downloads_performed": False,
            "station_time_series_imported": False,
            "lag_model_built": False,
            "flash_gameplay_promoted": False,
            "use_as_metadata_review_only": True,
        },
        "flash_flow_band_question": {
            "flow_band": flash_band["flow_band"],
            "needed_evidence": flash_band["needed_evidence"],
            "review_status": "blocked_until_rainfall_stage_lag_station_records_and_guide_review",
        },
        "rainfall_review_summary": rainfall_station_review["candidate_layer_summary"],
        "discharge_stage_review_summary": discharge_stage_review["candidate_summary"],
        "basin_and_recharge_context_candidates": {
            "da_sinigirh_candidates": da_basin_candidates,
            "snit_context_layers": snit_context_layers,
        },
        "next_actions": [
            "Select station features and time series only after terms, CRS, attributes, and attribution are clear.",
            "Relate rainfall and discharge/stage stations to the lower Pacuare basin and review upstream lag.",
            "Define review-only unsafe flash-rise criteria before exposing flash scenarios in gameplay.",
            "Ask guide/outfitter reviewers to annotate visible warning signs, no-go cues, swimmer rescue limits, and evacuation constraints.",
        ],
        "promotion_blockers": [
            "No rainfall-to-stage or rainfall-to-discharge lag evidence is attached.",
            "No station time series, station coordinates, basin relation, or quality flags are attached.",
            "Basin/recharge layers are metadata leads only and do not establish runoff response.",
            "Flash scenarios remain review-only until guide/outfitter safety review and rescue/readability gates pass.",
        ],
        "allowed_use": [
            "flash-response source triage",
            "future unsafe-flow checklist planning",
            "guide/outfitter annotation queue",
        ],
        "forbidden_use": [
            "numeric flash-response tuning",
            "production high-water or flood visuals",
            "unsafe/no-go gameplay authority",
            "claiming accepted Pacuare rainfall-to-stage lag",
        ],
    }


def _pacuare_protected_access_candidate_layers(
    snit_layer_catalog_summary: dict[str, object],
) -> list[dict[str, object]]:
    """Return metadata-only SNIT layer leads relevant to protected/access review."""

    candidate_layers = snit_layer_catalog_summary.get("selected_candidate_layers", [])
    review_tokens = (
        "sinac",
        "senara",
        "proteg",
        "forestal",
        "corredor",
        "humedal",
        "recarga",
        "vulnerabilidad",
    )
    selected: list[dict[str, object]] = []
    for layer in candidate_layers:
        haystack = " ".join(
            str(layer.get(key, ""))
            for key in ("name", "layer", "institution", "node_name", "target_use", "review_reason")
        ).lower()
        if not any(token in haystack for token in review_tokens):
            continue
        selected.append(
            {
                "name": layer.get("name"),
                "layer": layer.get("layer"),
                "institution": layer.get("institution"),
                "node_name": layer.get("node_name"),
                "publication_or_catalog_date": layer.get("publication_or_catalog_date"),
                "wms_available": layer.get("wms_available"),
                "wfs_available": layer.get("wfs_available"),
                "feature_download_status": layer.get("feature_download_status", "not_downloaded_metadata_only"),
                "review_reason": layer.get("review_reason"),
                "promotion_gate": layer.get(
                    "promotion_gate",
                    "Review terms, CRS, attributes, Pacuare corridor intersection, and local sensitivity before import.",
                ),
            }
        )
    return selected


def _pacuare_protected_access_metadata_layers(
    snit_layer_metadata_summary: dict[str, object],
) -> list[dict[str, object]]:
    """Return selected metadata rows for protected/access source-rights decisions."""

    metadata_layers = snit_layer_metadata_summary.get("metadata_layers", [])
    review_prefixes = ("sinac_", "senara_")
    selected: list[dict[str, object]] = []
    for layer in metadata_layers:
        candidate_id = str(layer.get("candidate_id", ""))
        if not candidate_id.startswith(review_prefixes):
            continue
        selected.append(
            {
                "candidate_id": layer.get("candidate_id"),
                "node_id": layer.get("node_id"),
                "selected_layer_name": layer.get("selected_layer_name"),
                "metadata_title": layer.get("metadata_title"),
                "crs": layer.get("crs"),
                "terms_status": layer.get("terms_status"),
                "feature_download_status": layer.get("feature_download_status"),
                "promotion_gate": layer.get("promotion_gate"),
            }
        )
    return selected


def build_pacuare_protected_area_publication_sensitivity(
    access_constraints: dict[str, object],
    sinac_source_rights: dict[str, object],
    snit_layer_catalog_summary: dict[str, object],
    snit_layer_metadata_summary: dict[str, object],
) -> dict[str, object]:
    """Build the review-gated Pacuare protected-area publication policy artifact."""

    candidate_layers = _pacuare_protected_access_candidate_layers(snit_layer_catalog_summary)
    metadata_layers = _pacuare_protected_access_metadata_layers(snit_layer_metadata_summary)
    rainforest_target = next(
        (
            target
            for target in snit_layer_catalog_summary.get("candidate_review_targets", [])
            if "protected" in str(target.get("target", "")).lower()
            or "rainforest" in str(target.get("target", "")).lower()
        ),
        {},
    )
    return {
        "schema": "raftsim.pacuare_protected_area_publication_sensitivity.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "metadata_only_protected_area_publication_policy_attached_review_gated",
        "inputs": {
            "access_constraints": "physics/data/real_world/pacuare_river_costa_rica/review/access_and_conservation_constraints.json",
            "sinac_source_rights": "physics/data/real_world/pacuare_river_costa_rica/review/sinac_protected_area_source_rights.json",
            "snit_layer_catalog_summary": (
                "physics/data/real_world/pacuare_river_costa_rica/"
                + PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE
            ),
            "snit_layer_metadata_summary": (
                "physics/data/real_world/pacuare_river_costa_rica/"
                + PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE
            ),
        },
        "input_statuses": {
            "access_constraints": access_constraints.get("status"),
            "sinac_source_rights": sinac_source_rights.get("status"),
            "snit_layer_catalog_summary": snit_layer_catalog_summary.get("status"),
            "snit_layer_metadata_summary": snit_layer_metadata_summary.get("status"),
        },
        "policy": {
            "feature_downloads_performed": False,
            "protected_area_geometry_imported": False,
            "access_geometry_imported": False,
            "map_tiles_imported": False,
            "media_downloaded": False,
            "publish_detailed_route_packages": False,
            "publish_sensitive_polygons": False,
            "use_as_publication_gate_only": True,
        },
        "protected_context_summary": {
            "candidate_layer_count": len(candidate_layers),
            "metadata_layer_count": len(metadata_layers),
            "catalog_review_target": rainforest_target.get("target"),
            "catalog_target_outputs": rainforest_target.get("target_outputs", []),
            "metadata_review_findings": snit_layer_metadata_summary.get("review_findings", []),
        },
        "candidate_layers": candidate_layers,
        "metadata_layers": metadata_layers,
        "publication_sensitivity_zones": [
            {
                "zone_id": "upper_access_and_rainforest_approach_review_zone",
                "station_range_m_preview": [0.0, 10000.0],
                "review_status": "preview_stationing_only_sensitive_context_pending",
                "needs": [
                    "official protected-area/access layer intersection after terms review",
                    "local guide/outfitter review before access labels or route screenshots",
                    "generalized screenshot framing until sensitive polygons are approved",
                ],
            },
            {
                "zone_id": "central_gorge_habitat_and_rescue_visibility_review_zone",
                "station_range_m_preview": [10000.0, 33000.0],
                "review_status": "rainforest_gorge_publication_sensitivity_pending",
                "needs": [
                    "SINAC/SENARA forest, wetland, corridor, recharge, and vulnerability terms review",
                    "no-publish polygon screening before detailed gorge captures",
                    "rescue, swimmer, and guide-sightline annotation without exposing sensitive locations",
                ],
            },
            {
                "zone_id": "downstream_takeout_and_community_access_review_zone",
                "station_range_m_preview": [33000.0, 45650.0],
                "review_status": "access_and_community_context_pending",
                "needs": [
                    "approved put-in, take-out, road, bridge, and evacuation annotations",
                    "local publication-risk review before detailed route or access geometry",
                    "flow-dependent access and evacuation interpretation for rainfed/high-water variants",
                ],
            },
        ],
        "required_editor_annotations": [
            "review/production_import_pilot/no_publish_sensitive_polygons.geojson",
            "review/production_import_pilot/access_points.geojson",
            "review/production_import_pilot/evacuation_and_rescue_routes.geojson",
            "review/production_import_pilot/conservation_sensitive_reaches.geojson",
            "review/production_import_pilot/guide_publication_notes.json",
        ],
        "allowed_use": [
            "protected-area and conservation source triage",
            "station-aware annotation planning",
            "publication-sensitivity checklist gating",
            "preventing detailed Pacuare screenshots or route packages before review",
        ],
        "forbidden_use": [
            "final access geometry",
            "route publication authority",
            "protected-area clearance",
            "shipping detailed screenshots that reveal sensitive access or conservation locations without review",
            "using SNIT, SINAC, SENARA, or guide/social media maps, tiles, photos, or screenshots as texture or art assets",
        ],
        "promotion_blockers": [
            "No protected-area, forest-cover, wetland, corridor, recharge, access, or no-publish geometries are imported.",
            "SNIT/SINAC/SENARA layer terms, attribution, CRS, attributes, and redistribution limits still need final review.",
            "Pacuare corridor intersections and sensitive-location policy are not approved.",
            "Local guide/outfitter and conservation review is required before public route details or detailed screenshots.",
        ],
    }


def build_pacuare_access_conservation_policy(
    access_constraints: dict[str, object],
    sinac_source_rights: dict[str, object],
    snit_layer_catalog_summary: dict[str, object],
    snit_layer_metadata_summary: dict[str, object],
) -> dict[str, object]:
    """Build the Pacuare access/conservation policy artifact for editor tooling."""

    candidate_layers = _pacuare_protected_access_candidate_layers(snit_layer_catalog_summary)
    metadata_layers = _pacuare_protected_access_metadata_layers(snit_layer_metadata_summary)
    return {
        "schema": "raftsim.pacuare_access_and_conservation_policy.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "access_conservation_policy_attached_no_geometry_review_gated",
        "inputs": {
            "access_constraints": "physics/data/real_world/pacuare_river_costa_rica/review/access_and_conservation_constraints.json",
            "sinac_source_rights": "physics/data/real_world/pacuare_river_costa_rica/review/sinac_protected_area_source_rights.json",
            "snit_layer_catalog_summary": (
                "physics/data/real_world/pacuare_river_costa_rica/"
                + PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE
            ),
            "snit_layer_metadata_summary": (
                "physics/data/real_world/pacuare_river_costa_rica/"
                + PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE
            ),
        },
        "policy": {
            "use_generalized_access_language_until_review": True,
            "do_not_ship_exact_access_or_evacuations_without_review": True,
            "do_not_publish_sensitive_conservation_locations": True,
            "social_and_outfitter_media_remain_link_only_without_item_rights": True,
            "flow_dependent_access_review_required": True,
            "procedural_generation_must_not_hide_missing_source_review": True,
        },
        "constraint_categories": access_constraints.get("constraint_categories", []),
        "source_rights_policy": sinac_source_rights.get("policy", {}),
        "source_rights_questions": sinac_source_rights.get("review_questions", []),
        "candidate_layer_summary": {
            "candidate_layer_count": len(candidate_layers),
            "metadata_layer_count": len(metadata_layers),
            "copyright_or_ip_restricted_metadata_layers": sum(
                1
                for layer in metadata_layers
                if "copyright" in str(layer.get("terms_status", ""))
                or "ip_restrictions" in str(layer.get("terms_status", ""))
            ),
            "unrestricted_claim_review_required_layers": sum(
                1 for layer in metadata_layers if "unrestricted" in str(layer.get("terms_status", ""))
            ),
        },
        "candidate_layers": candidate_layers,
        "metadata_layer_terms": [
            {
                "candidate_id": layer.get("candidate_id"),
                "selected_layer_name": layer.get("selected_layer_name"),
                "terms_status": layer.get("terms_status"),
                "promotion_gate": layer.get("promotion_gate"),
            }
            for layer in metadata_layers
        ],
        "editor_workflow": [
            {
                "step": "annotate_generalized_access_points",
                "required_output": "review/production_import_pilot/access_points.geojson",
                "review_gate": "Use approved first-party, official, or guide-reviewed geometry only; keep coordinates generalized for public previews until cleared.",
            },
            {
                "step": "annotate_no_publish_and_sensitive_conservation_areas",
                "required_output": "review/production_import_pilot/no_publish_sensitive_polygons.geojson",
                "review_gate": "Do not expose exact protected, cultural, habitat, access, or rescue-sensitive geometry in screenshots or packaged maps.",
            },
            {
                "step": "annotate_evacuation_rescue_and_flow_variant_constraints",
                "required_output": "review/production_import_pilot/evacuation_and_rescue_routes.geojson",
                "review_gate": "Review access and rescue feasibility separately for clear-season, rainfed-runnable, rainy-season-high, and flash-response conditions.",
            },
            {
                "step": "record_local_guide_and_conservation_signoff",
                "required_output": "review/production_import_pilot/guide_publication_notes.json",
                "review_gate": "Capture reviewer, date, flow/rain context, publication limits, and allowed gameplay/art uses before promotion.",
            },
        ],
        "required_editor_annotations": [
            "review/production_import_pilot/access_points.geojson",
            "review/production_import_pilot/no_publish_sensitive_polygons.geojson",
            "review/production_import_pilot/evacuation_and_rescue_routes.geojson",
            "review/production_import_pilot/conservation_sensitive_reaches.geojson",
            "review/production_import_pilot/guide_publication_notes.json",
        ],
        "allowed_use": [
            "editor access and conservation checklist",
            "guide/outfitter review queue",
            "flow-dependent access and evacuation planning",
            "procedural rainforest dressing boundaries",
        ],
        "forbidden_use": [
            "final access geometry",
            "evacuation or rescue route authority",
            "route publication authority",
            "claiming protected-area clearance",
            "shipping public route-detail screenshots without local and conservation review",
        ],
        "promotion_blockers": [
            "Exact put-in, take-out, bridge, road, trail, evacuation, and rescue geometries are not attached.",
            "Protected-area, corridor, wetland, forest, recharge, and vulnerability layer intersections are metadata leads only.",
            "Flow-dependent access and rescue behavior is not validated against rainfall/stage history or guide review.",
            "Item-level rights for guide, outfitter, public, or social media references are not attached.",
        ],
        "publication_gate": access_constraints.get("publication_gate", []),
    }


def pacuare_import_pilot_bounds() -> BoundsWGS84:
    """Return the current lower Pacuare planning bounds for production source review."""

    return BoundsWGS84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12)


def build_pacuare_production_import_pilot(bounds: BoundsWGS84 | None = None) -> dict[str, object]:
    """Build the Pacuare production-source import pilot recipe."""

    target_bounds = bounds or pacuare_import_pilot_bounds()
    return {
        "schema": PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION,
        "pilot_id": "pacuare_lower_pacuare_public_global_source_pilot",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "route_style": "guided_paddle_raft",
        "status": "planned_review_gated_source_selection_pending",
        "source_manifest": SOURCE_MANIFEST_FILE,
        "readiness_manifest": "../production_geospatial_source_readiness.json",
        "bounds_wgs84": target_bounds.to_json_dict(),
        "corridor_scope": {
            "status": "draft_lower_pacuare_planning_bounds_not_surveyed_route",
            "reason": (
                "The pilot starts from attached public/global DEM and cloud-screened preview imagery while authoritative "
                "Costa Rica hydrography, rainfall/flow, access, protected-area, and guide/outfitter review are secured."
            ),
            "full_route_requires": [
                "Costa Rica working CRS selection",
                "official hydrography and access layer review",
                "rainfall/flow station authority review",
                "protected-area and publication sensitivity review",
                "first-party or permissioned field-media validation",
            ],
        },
        "working_crs_decision": {
            "status": "required_before_unreal_promotion",
            "candidate": "costa_rica_projected_corridor_crs_derived_from_reviewed_epsg4326_bounds",
            "required_review": [
                "horizontal CRS and units",
                "vertical datum handling for DEM elevations",
                "Unreal origin and scale transform",
                "round-trip error budget against source coordinates",
                "protected-area/access publication constraints",
            ],
        },
        "seed_products": [
            {
                "product_id": "copernicus_dem_glo30_public_tiles",
                "status": "downloaded_review_gated_seed",
                "source_ids": ["copernicus_dem"],
                "artifacts": [
                    "terrain/copernicus_dem_glo30_N09_W084.tif",
                    "terrain/copernicus_dem_glo30_N10_W084.tif",
                    "terrain/pacuare_dem_relief_preview_1024.png",
                    "terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png",
                ],
                "limits": "Global DEM tiles are useful for gorge-scale preview relief but are not clipped, void-reviewed, hydrologically conditioned, channel-burned, or locally datum-reviewed.",
            },
            {
                "product_id": "nasa_gibs_modis_demshade_preview_drape",
                "status": "downloaded_cloud_screened_preview_seed",
                "source_ids": ["nasa_gibs", "copernicus_dem"],
                "artifacts": [
                    "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_1024.png",
                    "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png",
                    "imagery/pacuare_nasa_gibs_2025-04-02_water_mask_1024.png",
                    "imagery/pacuare_nasa_gibs_2025-04-02_vegetation_mask_1024.png",
                ],
                "limits": "MODIS/GIBS is coarse and partly cloudy; it is only a source-aware preview seed until higher-resolution cloud-screened imagery or first-party/permissioned aerial reference is approved.",
            },
            {
                "product_id": "pacuare_unreal_preview_centerline_scaffold",
                "status": "generated_review_gated_preview_route_not_official_hydrography",
                "source_ids": ["unreal_preview_curve", "pacuare_production_import_pilot_masks"],
                "artifacts": [
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
                    PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
                ],
                "limits": (
                    "Deterministic scaffold from the current Unreal Pacuare preview curve and draft WGS84 bounds; "
                    "use for annotation placement and procedural dressing only until official hydrography, CRS, "
                    "banks, rapid/access stationing, and guide/outfitter review replace or validate it."
                ),
            },
            {
                "product_id": "pacuare_official_source_access_plan",
                "status": "official_service_catalogs_recorded_layer_download_pending",
                "source_ids": [
                    "snit_cr_idecori",
                    "minae_direccion_agua",
                    "imn_costa_rica",
                    "sinac_minae",
                    "senara_costa_rica",
                    "ice_hydromet",
                ],
                "artifacts": [
                    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE,
                    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                    PACUARE_SNIT_OGC_CATALOG_FILE,
                    PACUARE_SNIT_CONFIG_FILE,
                    PACUARE_SNIT_LAYER_LIST_SCRIPT_FILE,
                    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                ],
                "limits": (
                    "Records official Costa Rica service catalogs, archived Direccion de Agua WMS capabilities metadata, "
                    "archived SNIT node layer-list metadata, selected per-layer SNIT metadata JSON, candidate layer "
                    "names, terms status, CRS leads, and review gates only; no SNIT/Direccion de Agua/SINIGIRH features are "
                    "downloaded, clipped, or promoted by this plan."
                ),
            },
        ],
        "required_source_classes": [
            {
                "class_id": "terrain_dem_or_lidar",
                "status": "global_dem_seed_attached_local_source_review_pending",
                "source_ids": ["copernicus_dem", "snit_cr_idecori", "opentopography"],
                "target_outputs": [
                    "terrain/production_import_pilot/reviewed_dem_tiles",
                    "terrain/production_import_pilot/dem_relief_2048.png",
                    "terrain/production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot_derivatives_manifest.json",
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Select local or best-available terrain source, record product ids/terms/CRS/vertical datum, clip to "
                    "corridor, void-review, hydrologically condition, burn the river channel, and compare gorge form to "
                    "guide-reviewed field references."
                ),
            },
            {
                "class_id": "hydrography_and_centerline",
                "status": "preview_centerline_scaffold_attached_official_hydrography_pending",
                "source_ids": ["snit_cr_idecori", "minae_direccion_agua", "hydrosheds", "osm"],
                "target_outputs": [
                    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
                    PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
                    PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    PACUARE_PRODUCTION_BANKS_DRAFT_FILE,
                    "hydrography/production_import_pilot/tributaries.geojson",
                    PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE,
                ],
                "promotion_gate": (
                    "Confirm exact official Costa Rica layers, terms, CRS, and attribution; use HydroSHEDS/OSM only as "
                    "review seeds until aligned to visible imagery and guide-reviewed rapid/access annotations."
                ),
            },
            {
                "class_id": "aerial_or_satellite_imagery",
                "status": "coarse_preview_seed_attached_high_resolution_cloud_screening_pending",
                "source_ids": ["copernicus_sentinel", "landsat", "nasa_gibs", "snit_cr_idecori", "first_party_aerial"],
                "target_outputs": [
                    PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE,
                    "imagery/production_import_pilot/source_drape_4096.png",
                    PACUARE_CLOUD_SHADOW_REVIEW_FILE,
                    PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE,
                    PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CLEANER_SCENE_SEARCH_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_16PHR_IMAGE_FILE,
                    "production_import_pilot_derivatives_manifest.json",
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Attach scene ids, acquisition dates, cloud score, CRS, resolution, terms, and attribution; prefer "
                    "cloud-free Sentinel/Landsat/local orthophoto or first-party/permissioned aerial reference before "
                    "using imagery for production masks or photoreal materials."
                ),
            },
            {
                "class_id": "water_and_vegetation_masks",
                "status": "coarse_preview_masks_attached_production_segmentation_pending",
                "source_ids": ["copernicus_sentinel", "landsat", "hydrography_review", "guide_review"],
                "target_outputs": [
                    "imagery/production_import_pilot/water_mask_2048.png",
                    "imagery/production_import_pilot/vegetation_mask_2048.png",
                    "imagery/production_import_pilot/canopy_shadow_mask_2048.png",
                    "imagery/production_import_pilot/wet_rock_waterfall_mist_mask_2048.png",
                    "imagery/production_import_pilot/source_masks_manifest.json",
                    PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE,
                    PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CLEANER_SCENE_SEARCH_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_16PHR_IMAGE_FILE,
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Derive masks only after higher-resolution imagery and hydrography are reviewed; manually check "
                    "river edge, wet rock, waterfalls, mist, canopy shadow, exposed shelves, and rain/flow variants."
                ),
            },
            {
                "class_id": "seasonal_flow_or_release_history",
                "status": "relative_flow_bands_attached_numeric_authority_pending",
                "source_ids": ["imn_costa_rica", "ice_hydromet", "minae_direccion_agua", "guide_review"],
                "target_outputs": [
                    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                    PACUARE_RAINFALL_STATION_REVIEW_FILE,
                    PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE,
                    PACUARE_FLASH_RESPONSE_REVIEW_FILE,
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                    "hydrology/production_import_pilot/flow_band_review.json",
                ],
                "promotion_gate": (
                    "Attach station ids, variables, units, time zone, access terms, rainfall/flow coverage, and guide "
                    "review before converting relative clear-season/rainfed/rainy-season/flash-response bands into "
                    "numeric gameplay and visual presets."
                ),
            },
            {
                "class_id": "protected_area_and_access_context",
                "status": "review_manifests_attached_publication_not_cleared",
                "source_ids": ["sinac_minae", "snit_cr_idecori", "guide_review"],
                "target_outputs": [
                    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                    PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE,
                    PACUARE_ACCESS_CONSERVATION_POLICY_FILE,
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Record exact layers, terms, sensitive-location policy, access constraints, and screenshot/publication "
                    "limits before committing detailed route packages or public-facing captures."
                ),
            },
            {
                "class_id": "guide_and_reference_media_annotations",
                "status": "link_seeds_attached_no_media_rights",
                "source_ids": ["reference_media_link_manifest", "first_party_field_capture", "explicit_outfitter_or_guide_permission"],
                "target_outputs": [
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                ],
                "promotion_gate": (
                    "Attach creator, date, reach, rain/flow context, permission, attribution, and allowed asset uses before "
                    "photos or footage drive rainforest materials, water color, waterfalls, mist, or rapid behavior."
                ),
            },
        ],
        "procedural_generation_plan": {
            "status": "allowed_only_as_manifest_recorded_review_gated_fill",
            "allowed_layers": [
                "rainforest canopy density",
                "leaf litter",
                "wet rocks",
                "waterfall mist",
                "spray",
                "river-surface color variation",
                "distant gorge closure",
            ],
            "limits": [
                "must record source inputs and tuning parameters",
                "must not hide missing hydrography, flow, or conservation failures",
                "must remain separable from reviewed geospatial products",
                "must be replaceable by first-party or rights-cleared field references",
            ],
        },
        "unreal_import_targets": {
            "heightfield_import_contract": "unreal/Content/RaftSim/River/pacuare_heightfield_import_test.json",
            "preview_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview",
            "future_production_map": "/Game/RaftSim/Maps/Production/L_PacuareRainforest_LowerPacuare",
            "review_captures": [
                "docs/environment-captures/photoreal_river_previews/pacuare_guide_seat_downstream.png",
                "docs/environment-captures/photoreal_river_previews/pacuare_river_eye_downstream.png",
            ],
        },
        "acceptance_gate": [
            "All production source products have source metadata, checksums, CRS, acquisition dates, terms, and attribution.",
            "Conditioned heightfield and masks are generated from reviewed terrain, imagery, hydrography, and rain/flow context.",
            "Procedural rainforest, waterfall, mist, wet-rock, and canopy layers record source inputs and remain review-gated.",
            "Unreal preview map can be regenerated from pilot artifacts with water readability, rescue targets, and protected-area constraints preserved.",
            "Screenshots look materially closer to the real Pacuare corridor without claiming final photoreal approval.",
        ],
        "provenance": {
            "generated_by": "raftsim.real_world.build_pacuare_production_import_pilot",
            "processing_version": "milestone_26_pacuare_import_pilot.v0",
            "review_status": "recipe_only_source_selection_and_imports_pending",
        },
    }


def build_production_environment_gap_register() -> dict[str, object]:
    """Build the machine-checkable gap register for lifelike river environments."""

    source_classes = [
        "terrain_dem_or_lidar",
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "water_and_vegetation_masks",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
        "production_art_assets_or_first_party_procedural_equivalents",
        "unreal_lifelike_capture_and_performance_evidence",
    ]
    reviewed_source_leads = [
        {
            "source_id": "usgs_3dep",
            "provider": "USGS 3D Elevation Program",
            "review_date": "2026-07-06",
            "url": "https://www.usgs.gov/3d-elevation-program",
            "why_it_matters": "Primary U.S. DEM/lidar source for South Fork and Colorado terrain, slope, banks, and Unreal Landscape conditioning.",
            "use_gate": "Record product id, acquisition date, CRS, vertical datum, void review, hydrologic conditioning, channel burning, attribution, and package/LFS policy before production terrain use.",
        },
        {
            "source_id": "usgs_3dhp",
            "provider": "USGS 3D Hydrography Program",
            "review_date": "2026-07-06",
            "url": "https://www.usgs.gov/3d-hydrography-program",
            "why_it_matters": "Primary U.S. hydrography successor path for flowlines, drainage context, tributaries, and river/bank alignment.",
            "use_gate": "Clip selected products into the river corridor and compare to imagery, DEM-derived channels, and guide-reviewed rapid/eddy annotations before gameplay authority.",
        },
        {
            "source_id": "usgs_water_services",
            "provider": "USGS Water Services",
            "review_date": "2026-07-06",
            "url": "https://waterservices.usgs.gov/",
            "why_it_matters": "Daily and instantaneous discharge/stage source for South Fork and Colorado seasonal or release-band visuals.",
            "use_gate": "Attach station metadata, variables, units, quality flags, temporal coverage, and guide/release interpretation before final flow bands.",
        },
        {
            "source_id": "ca_state_parks_marshall_gold_discovery",
            "provider": "California State Parks",
            "review_date": "2026-07-06",
            "url": "https://www.parks.ca.gov/?page_id=484",
            "why_it_matters": "Official downstream Coloma/state-park access, map, concession, water-safety, and publication-sensitivity source lead for the South Fork pilot.",
            "use_gate": "Use as source-review evidence only until exact access geometry, current restrictions, publication sensitivity, media rights, and guide/outfitter review are attached.",
        },
        {
            "source_id": "el_dorado_county_gis",
            "provider": "El Dorado County",
            "review_date": "2026-07-06",
            "url": "https://experience.arcgis.com/experience/58a5b752c549418285583fc4c0301c29",
            "why_it_matters": "Official county GIS lead for parcels, roads, public/private land, access, evacuation, and route-publication context.",
            "use_gate": "Select exact layers and terms before importing geometries or using county context as access, parcel, or emergency-route authority.",
        },
        {
            "source_id": "copernicus_data_space",
            "provider": "Copernicus Data Space Ecosystem",
            "review_date": "2026-07-06",
            "url": "https://dataspace.copernicus.eu/",
            "why_it_matters": "Primary candidate for Pacuare Sentinel scene discovery, cloud screening, river color, vegetation masks, and wet/rain seasonal review.",
            "use_gate": "Record scene ids, acquisition dates, cloud score, processing level, CRS, terms, and attribution before derivatives drive production masks or materials.",
        },
        {
            "source_id": "snit_cr_idecori",
            "provider": "Sistema Nacional de Informacion Territorial de Costa Rica / IDECORI",
            "review_date": "2026-07-06",
            "url": "https://www.snitcr.go.cr/",
            "why_it_matters": "Official Costa Rica layer portal for Pacuare hydrography, terrain, protected-area, access, and possible imagery context.",
            "use_gate": "Record exact service/layer names, CRS, responsible institution, terms, attribution, and publication sensitivity before importing any layer.",
        },
        {
            "source_id": "hydrosheds",
            "provider": "HydroSHEDS",
            "review_date": "2026-07-06",
            "url": "https://www.hydrosheds.org/",
            "why_it_matters": "Global catchment and river-network fallback for Pacuare basin context while official Costa Rica layers are reviewed.",
            "use_gate": "Use as a review seed only until aligned against official hydrography, visible imagery, and guide/outfitter stationing.",
        },
        {
            "source_id": "opentopography",
            "provider": "OpenTopography",
            "review_date": "2026-07-06",
            "url": "https://opentopography.org/",
            "why_it_matters": "Candidate high-resolution topography and hydrologic-conditioning tool path for U.S. and Pacuare terrain if dataset terms allow.",
            "use_gate": "Confirm API key, dataset license, citation, redistribution limits, and derivative rights before importing terrain or conditioning outputs.",
        },
        {
            "source_id": "nps_grand_canyon_media",
            "provider": "National Park Service Grand Canyon Photos & Multimedia",
            "review_date": "2026-07-06",
            "url": "https://www.nps.gov/grca/learn/photosmultimedia/index.htm",
            "why_it_matters": "Preferred official-media lead for Colorado canyon wall, river, sandbar, b-roll, and atmosphere reference.",
            "use_gate": "Record item-level public-domain or Creative Commons status, credit, date, location, and allowed use before any media becomes production reference or asset input.",
        },
        {
            "source_id": "nps_grand_canyon_river_trips_permits",
            "provider": "National Park Service Grand Canyon River Trips / Permits",
            "review_date": "2026-07-06",
            "url": "https://www.nps.gov/grca/planyourvisit/whitewater-rafting.htm",
            "why_it_matters": "Official Colorado River trip, route, and permit-context source lead for Grand Canyon route/access review.",
            "use_gate": "Use as source triage only until exact launch/take-out geometry, document dates, access constraints, publication sensitivity, and oarsman review are attached.",
        },
        {
            "source_id": "nps_grand_canyon_noncommercial_river_trip_links",
            "provider": "National Park Service Grand Canyon Noncommercial River Trip Helpful Links",
            "review_date": "2026-07-06",
            "url": "https://www.nps.gov/grca/planyourvisit/noncommercial-riv-docs.htm",
            "why_it_matters": "Official document index for Lees Ferry starts, Diamond Creek/Pearce Ferry take-outs, and noncommercial river trip regulations.",
            "use_gate": "Keep linked regulations and support pages in manual review; do not present permit/legal guidance or import page/PDF content as game assets.",
        },
    ]

    return {
        "schema": PRODUCTION_ENVIRONMENT_GAP_REGISTER_SCHEMA_VERSION,
        "generated_on": "2026-07-06",
        "status": "active_goal_gap_register_all_rivers_preview_only_not_lifelike",
        "goal": (
            "Drive South Fork American, Colorado River, and Pacuare from source-aware Unreal previews to complete "
            "photoreal river environments by tracking maps, seasonal flows, aerial imagery, rights-reviewed reference "
            "media, additional source data, procedural substitutes, lifelike captures, and performance evidence."
        ),
        "blocking_rule": (
            "No river can be marked production-playable or lifelike until every P0 source-data, visual-replacement, "
            "rights-review, guide-review, capture, and performance gate for that river is closed."
        ),
        "policy": {
            "official_open_sources_first": True,
            "social_media_reference_only_until_explicit_item_rights_clear": True,
            "do_not_download_scrape_train_on_or_package_third_party_media_without_rights": True,
            "procedural_generation_allowed_when_manifest_recorded": True,
            "procedural_generation_must_not_hide_hazards_rescue_targets_or_physics_failures": True,
            "lifetime_goal_requires_lifelike_unreal_screenshots": True,
        },
        "source_classes": source_classes,
        "canonical_inputs": {
            "photoreal_environment_sources": "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json",
            "first_party_procedural_environment_assets": "unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json",
            "geospatial_readiness": "physics/data/real_world/production_geospatial_source_readiness.json",
            "reference_media_links": "physics/data/real_world/reference_media_link_manifest.json",
            "art_asset_source_research": "unreal/Content/RaftSim/Rendering/art_asset_source_research.json",
            "capture_manifest": "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json",
        },
        "reviewed_source_leads_2026_07_06": reviewed_source_leads,
        "global_visual_replacement_targets": [
            {
                "target": "terrain_and_banks",
                "required_before_lifelike": [
                    "conditioned source heightfields or approved procedural terrain",
                    "bank breaklines and channel burning",
                    "biome-specific terrain material layering",
                    "first_party_procedural_asset_recipe_coverage_or_rights_cleared_equivalent_assets",
                    "source-aligned wet/dry and exposed-bar masks",
                ],
            },
            {
                "target": "rocks_boulders_and_riverbed",
                "required_before_lifelike": [
                    "rights-cleared or first-party rock/boulder assets",
                    "wetness and moss/sediment material variants",
                    "mask-aware placement that preserves hazard readability",
                    "river-specific scale and abrasion review",
                ],
            },
            {
                "target": "foliage_and_ecology",
                "required_before_lifelike": [
                    "biome-specific trees, seedlings, shrubs, grasses, tropical canopy, and deadfall",
                    "density masks from reviewed imagery or first-party procedural rules",
                    "seasonal and flow-bank exposure variants",
                    "performance-scalable Nanite/PCG or instancing path",
                ],
            },
            {
                "target": "water_foam_spray_mist_and_wetness",
                "required_before_lifelike": [
                    "production water shader with reflections, depth color, turbidity, and solver/current cues",
                    "foam, boil, wave-train, hole, eddy-line, lateral, spray, and mist layers",
                    "flow-band dependency from validated hydrology and gameplay tuning",
                    "no visual forcing that hides conservation or physics failures",
                ],
            },
            {
                "target": "lighting_atmosphere_and_capture",
                "required_before_lifelike": [
                    "river-specific time-of-day and weather presets",
                    "HDRI or first-party sky/atmosphere setup with rights recorded",
                    "manual exposure/camera language matching guide-seat review",
                    "desktop and VR performance captures with settings recorded",
                ],
            },
        ],
        "rivers": [
            {
                "river_id": "american_south_fork",
                "display_name": "South Fork American River, Chili Bar to Coloma",
                "readiness": "preview_only_not_lifelike",
                "active_unreal_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview",
                "current_strength": "strongest solver/source seed; official pilot DEM/NAIP tiles and derivatives are attached for a small corridor slice.",
                "attached_preview_inputs": [
                    SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE,
                    "production_import_pilot/3dep_tiles",
                    "production_import_pilot/naip_tiles",
                    "production_import_pilot/source_drape_4096.png",
                    "production_import_pilot/dem_relief_2048.png",
                    "production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot/water_mask_2048.png",
                    "production_import_pilot/vegetation_mask_2048.png",
                    SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
                    SOUTH_FORK_NHD_WATER_PRIOR_MANIFEST_FILE,
                    SOUTH_FORK_NHD_WATER_PRIOR_FILE,
                    SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                    SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                    SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                    SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                    SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                    SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                    SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                    SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                    SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
                    SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                    "hydrology/usgs_11445500_daily_discharge.json",
                    "hydrology/usgs_11445500_instantaneous_discharge_stage_p30d_diagnostic.json",
                    "hydrology/south_fork_modern_flow_source_selection.json",
                    "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                    SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                    SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                    SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
                    SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
                    SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
                    SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
                    SOUTH_FORK_ACCESS_POINTS_FILE,
                    SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                    SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
                    "reference_media_link_manifest.json",
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                ],
                "p0_next_pulls_or_attachments": [
                    {
                        "source_class": "hydrography_and_centerline",
                        "required_artifacts": [
                            SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                            SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                            SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                            SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                            SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                            SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                            SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                            SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                            SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                            SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                            SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
                            SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
                            SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                        ],
                        "source_leads": ["usgs_3dhp", "usgs_3dep", "guide_review"],
                        "promotion_gate": "Promote the attached NHD HU8 source extract and derived mainstem candidate only after direction, working CRS, NAIP, DEM relief, rapid stations, and guide-reviewed eddy/recovery geometry are confirmed.",
                    },
                    {
                        "source_class": "seasonal_flow_or_release_history",
                        "required_artifacts": [
                            "hydrology/south_fork_modern_flow_source_selection.json",
                            "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                            SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                            SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                            SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
                            SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
                            SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
                        ],
                        "source_leads": ["cdec_cbr", "cdec_a25_powerhouse_context", "usgs_water_services", "guide_review"],
                        "promotion_gate": (
                            "USGS 11445500 returned no P30D instantaneous time series on 2026-07-06, and CDEC CBR now "
                            "has a first reproducible event-window pull, terms/flag/station review, 30-day CBR/A25 "
                            "context window, water-year-to-date seasonal review, and multi-year CBR flow context; tie "
                            "low/median/high visual variants to A25 routing, high-flow event interpretation, legal/"
                            "redistribution signoff, station-to-reach review, and guide notes."
                        ),
                    },
                    {
                        "source_class": "guide_and_reference_media_annotations",
                        "required_artifacts": [
                            REFERENCE_MEDIA_ANNOTATIONS_FILE,
                            REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                        ],
                        "source_leads": ["first_party_field_capture", "explicit_guide_or_outfitter_permission", "reference_media_link_manifest"],
                        "promotion_gate": "Attach creator/date/reach/flow/weather/permission before photos or footage influence production art.",
                    },
                    {
                        "source_class": "protected_area_and_access_context",
                        "required_artifacts": [
                            SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
                            SOUTH_FORK_ACCESS_POINTS_FILE,
                            SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                            SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
                        ],
                        "source_leads": [
                            "ca_state_parks_marshall_gold_discovery",
                            "el_dorado_county_gis",
                            "guide_review",
                        ],
                        "promotion_gate": "Use the attached State Parks/county GIS review as source-lead evidence only; exact access, land-status, evacuation, and publication-sensitivity geometries still need official layer selection and guide/local review.",
                    },
                ],
                "procedural_generation_allowlist": [
                    "Sierra foothill riparian scatter and grass/scrub fill from source masks",
                    "granite/metamorphic boulder variants from first-party procedural materials",
                    "flow-band foam/wet-rock cues driven by USGS 11445500 review",
                ],
                "completion_gate": "Guide-seat and river-eye captures read as the South Fork corridor at reviewed low/median/high flow bands, with swimmer/rescue targets and rapid hazards still readable.",
            },
            {
                "river_id": "colorado_river",
                "display_name": "Colorado River, Grand Canyon Lees Ferry rowing prototype",
                "readiness": "preview_only_not_lifelike",
                "active_unreal_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview",
                "current_strength": "Lees Ferry pilot tiles and derivatives are attached; daily USGS gauge histories exist, but full canyon stationing and release-aware masks are still missing.",
                "attached_preview_inputs": [
                    "production_import_pilot/3dep_tiles",
                    "production_import_pilot/naip_tiles",
                    "production_import_pilot/source_drape_4096.png",
                    "production_import_pilot/dem_relief_2048.png",
                    "production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot/water_mask_2048.png",
                    "production_import_pilot/vegetation_mask_2048.png",
                    COLORADO_SOURCE_METADATA_REVIEW_FILE,
                    COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE,
                    COLORADO_NHD_WATER_PRIOR_FILE,
                    COLORADO_NHD_HU8_MANIFEST_FILE,
                    COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                    COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE,
                    COLORADO_NHD_MAINSTEM_MANIFEST_FILE,
                    COLORADO_NHD_MAINSTEM_CANDIDATE_FILE,
                    COLORADO_NHD_MAINSTEM_STATIONING_FILE,
                    COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                    COLORADO_NHD_CROSS_SECTION_SEED_FILE,
                    COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                    COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                    COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    COLORADO_PRODUCTION_BANKS_DRAFT_FILE,
                    COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                    COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE,
                    COLORADO_PRODUCTION_SANDBARS_FILE,
                    "hydrology/usgs_09380000_daily_discharge.json",
                    "hydrology/usgs_09402500_daily_discharge.json",
                    COLORADO_USBR_TOTAL_RELEASE_FILE,
                    COLORADO_USBR_RELEASE_CONTEXT_FILE,
                    COLORADO_RELEASE_BAND_REVIEW_FILE,
                    COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
                    COLORADO_ACCESS_POINTS_FILE,
                    COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                    COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
                    COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE,
                    "reference_media_link_manifest.json",
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                ],
                "p0_next_pulls_or_attachments": [
                    {
                        "source_class": "hydrography_and_centerline",
                        "required_artifacts": [
                            COLORADO_NHD_HU8_MANIFEST_FILE,
                            COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                            COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE,
                            COLORADO_NHD_MAINSTEM_MANIFEST_FILE,
                            COLORADO_NHD_MAINSTEM_CANDIDATE_FILE,
                            COLORADO_NHD_MAINSTEM_STATIONING_FILE,
                            COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                            COLORADO_NHD_CROSS_SECTION_SEED_FILE,
                            COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                            COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                            COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE,
                            COLORADO_PRODUCTION_BANKS_DRAFT_FILE,
                            COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
                            COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE,
                            COLORADO_PRODUCTION_SANDBARS_FILE,
                        ],
                        "source_leads": ["usgs_3dhp", "nps_grand_canyon_media", "gcmrc_or_river_mile_context"],
                        "promotion_gate": "Promote the attached stitched NHD HU8 source overlay, exact-graph mainstem candidate, preview metric stationing, cross-section seeds, and preview alignment diagnostic only after river mile stationing, visible flowline/water-edge alignment, exposed sandbars, eddies, camps/access sensitivity, and oarsman review pass.",
                    },
                    {
                        "source_class": "seasonal_flow_or_release_history",
                        "required_artifacts": [
                            COLORADO_USBR_TOTAL_RELEASE_FILE,
                            COLORADO_USBR_RELEASE_CONTEXT_FILE,
                            COLORADO_RELEASE_BAND_REVIEW_FILE,
                        ],
                        "source_leads": ["usgs_water_services", "usbr_glen_canyon_release_context", "guide_review"],
                        "promotion_gate": "Use the attached Reclamation daily total-release context as review-gated evidence, then add hourly/subdaily release patterns, final unit/terms confirmation, Lees Ferry/downstream gauge comparisons, and oarsman review before final release-dependent visuals.",
                    },
                    {
                        "source_class": "guide_and_reference_media_annotations",
                        "required_artifacts": [
                            REFERENCE_MEDIA_ANNOTATIONS_FILE,
                            REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                        ],
                        "source_leads": ["nps_grand_canyon_media", "first_party_field_capture", "explicit_oarsman_or_outfitter_permission"],
                        "promotion_gate": "Use official/public-domain media only after item metadata review; attach oarsman sightline notes before art or gameplay tuning.",
                    },
                    {
                        "source_class": "protected_area_and_access_context",
                        "required_artifacts": [
                            COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
                            COLORADO_ACCESS_POINTS_FILE,
                            COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                            COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
                            COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE,
                        ],
                        "source_leads": [
                            "nps_grand_canyon_river_trips_permits",
                            "nps_grand_canyon_noncommercial_river_trip_links",
                            "nps_grand_canyon_lees_ferry_diamond_creek_overview",
                            "nps_grand_canyon_noncommercial_river_trip_regulations_pdf",
                            "guide_review",
                        ],
                        "promotion_gate": "Use the attached NPS access/publication review as source-lead evidence only; exact launch/take-out, camp/beach, sensitive-location, river-mile publication, and route-language review still block detailed maps and screenshots.",
                    },
                ],
                "procedural_generation_allowlist": [
                    "canyon strata breakup from DEM relief, source drapes, and first-party procedural materials",
                    "sparse desert riparian scrub and tamarisk/cottonwood placeholders from masks",
                    "sandbar, wet-bank, boil, and big-water wave-train cues driven by release-band review",
                ],
                "completion_gate": "Captures read as Grand Canyon big-water rowing, with river-mile scale, canyon atmosphere, sandbar/wet-bank variation, oar-rig sightlines, and rescue visibility intact.",
            },
            {
                "river_id": "pacuare",
                "display_name": "Pacuare River, Costa Rica lower planning corridor",
                "readiness": "preview_only_not_lifelike",
                "active_unreal_map": "/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview",
                "current_strength": "Copernicus DEM and NASA GIBS/Copernicus preview derivatives are normalized into the production folder shape, and a deterministic Unreal-curve centerline/stationing scaffold exists for annotation placement; imagery is still coarse/cloudy and local hydrology/hydrography are not authoritative.",
                "attached_preview_inputs": [
                    "terrain/copernicus_dem_glo30_N09_W084.tif",
                    "terrain/copernicus_dem_glo30_N10_W084.tif",
                    "production_import_pilot/source_drape_4096.png",
                    "production_import_pilot/dem_relief_2048.png",
                    "production_import_pilot/heightfield_candidate_2017.png",
                    "production_import_pilot/water_mask_2048.png",
                    "production_import_pilot/vegetation_mask_2048.png",
                    PACUARE_SOURCE_METADATA_REVIEW_FILE,
                    PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE,
                    PACUARE_CLOUD_SHADOW_REVIEW_FILE,
                    PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE,
                    PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE,
                    PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE,
                    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_CLEANER_SCENE_SEARCH_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_SCL_QA_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_REVIEW_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_REVIEW_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_17PKM_IMAGE_FILE,
                    PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_16PHR_IMAGE_FILE,
                    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
                    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
                    PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
                    PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE,
                    PACUARE_PRODUCTION_BANKS_DRAFT_FILE,
                    PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE,
                    "hydrology/costa_rica_gauge_search.json",
                    "hydrology/rainfall_context.json",
                    PACUARE_RAINFALL_STATION_REVIEW_FILE,
                    PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE,
                    PACUARE_FLASH_RESPONSE_REVIEW_FILE,
                    PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE,
                    PACUARE_ACCESS_CONSERVATION_POLICY_FILE,
                    "review/sinac_protected_area_source_rights.json",
                    "review/access_and_conservation_constraints.json",
                    "reference_media_link_manifest.json",
                    REFERENCE_MEDIA_ANNOTATIONS_FILE,
                    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                ],
                "p0_next_pulls_or_attachments": [
                    {
                        "source_class": "hydrography_and_centerline",
                        "required_artifacts": [
                            PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                            PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                            PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                            PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                            PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
                            PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
                            PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
                            PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE,
                            PACUARE_PRODUCTION_BANKS_DRAFT_FILE,
                            PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE,
                        ],
                        "source_leads": ["snit_cr_idecori", "hydrosheds", "guide_review"],
                        "promotion_gate": "Use the attached Unreal-curve scaffold only for review overlays/procedural dressing; confirm exact official Costa Rica layers and use HydroSHEDS/OSM only as fallback seeds until guide/outfitter stationing approves the route.",
                    },
                    {
                        "source_class": "aerial_or_satellite_imagery",
                        "required_artifacts": [
                            PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE,
                            "imagery/production_import_pilot/source_drape_4096.png",
                            PACUARE_CLOUD_SHADOW_REVIEW_FILE,
                            PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE,
                            PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE,
                            PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE,
                            PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE,
                            PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE,
                            PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE,
                            PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE,
                            PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE,
                            PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_CLEANER_SCENE_SEARCH_REVIEW_FILE,
                            PACUARE_SENTINEL_20250320_SCL_QA_REVIEW_FILE,
                            PACUARE_SENTINEL_20250320_SCL_QA_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_SCL_QA_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_REVIEW_FILE,
                            PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_TCI_BBOX_CLIP_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_REVIEW_FILE,
                            PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_TCI_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20250320_DRAFT_BANK_WINDOW_SCL_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                            PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20250305_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_PROBE_REVIEW_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_SCL_16PHR_IMAGE_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_REVIEW_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_17PKM_IMAGE_FILE,
                            PACUARE_SENTINEL_20240204_DRAFT_BANK_TCI_16PHR_IMAGE_FILE,
                        ],
                        "source_leads": ["copernicus_data_space", "landsat", "snit_cr_idecori", "first_party_aerial"],
                        "promotion_gate": "Replace the MODIS/GIBS proxy drape with cloud-screened Sentinel/Landsat/local orthophoto or first-party/permissioned aerial reference only after the draft-bank strip cloud/shadow block is resolved by cleaner route-local coverage than March 20/March 5/February 4 TCI or exact native-CRS route/bank clips, SCL-masked stitched raster reads, terms review, and guide/geospatial approval.",
                    },
                    {
                        "source_class": "seasonal_flow_or_release_history",
                        "required_artifacts": [
                            PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                            PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
                            PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                            PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                            PACUARE_RAINFALL_STATION_REVIEW_FILE,
                            PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE,
                            PACUARE_FLASH_RESPONSE_REVIEW_FILE,
                        ],
                        "source_leads": ["imn_costa_rica", "ice_hydromet", "minae_direccion_agua", "guide_review"],
                        "promotion_gate": "Use the SNIT node layer-list summary as discovery metadata for IMN precipitation, SENARA station, and Direccion de Agua aforo candidates, but keep relative flow bands until station variables, units, time zones, access terms, rainfall/flow coverage, Pacuare basin relation, and guide review are attached.",
                    },
                    {
                        "source_class": "protected_area_and_access_context",
                        "required_artifacts": [
                            PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
                            PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
                            PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
                            PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE,
                            PACUARE_ACCESS_CONSERVATION_POLICY_FILE,
                        ],
                        "source_leads": ["sinac_minae", "senara_costa_rica", "guide_review"],
                        "promotion_gate": "Use the SNIT SINAC/SENARA layer lists only as metadata leads until protected-area, forest-cover, wetland, recharge, access, and sensitive-location terms clear public screenshots and route-detail publication.",
                    },
                    {
                        "source_class": "guide_and_reference_media_annotations",
                        "required_artifacts": [
                            REFERENCE_MEDIA_ANNOTATIONS_FILE,
                            REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
                        ],
                        "source_leads": ["first_party_field_capture", "explicit_outfitter_or_guide_permission", "reference_media_link_manifest"],
                        "promotion_gate": "Attach permissioned rainforest, waterfall, canopy, mist, water-color, and rapid-behavior references before production art promotion.",
                    },
                ],
                "procedural_generation_allowlist": [
                    "rainforest canopy density and understory as first-party PCG until field or rights-cleared references exist",
                    "wet rocks, waterfalls, spray, and mist as separately toggleable layers with source/tuning manifests",
                    "tropical humidity and cloud-shadow variants that do not hide rescue targets or rapid geometry",
                ],
                "completion_gate": "Captures read as a humid Pacuare rainforest gorge with believable canopy, waterfalls/mist, wet rocks, rainfed flow variation, and rescue readability under foliage.",
            },
        ],
        "next_checkpoint_order": [
            "Close South Fork hydrography/flow/media annotations enough to test a true source-conditioned terrain and material pass.",
            "Close Colorado river-mile/release/media annotations before expanding beyond the Lees Ferry pilot slice.",
            "Close Pacuare official hydrography, cloud-screened imagery, rainfall/flow, and protected-area review before claiming local fidelity.",
            "Replace proxy art using rights-cleared assets or first-party procedural equivalents and regenerate guide-seat plus river-eye captures after each river pass.",
            "Add desktop and VR performance evidence before any river leaves preview-only status.",
        ],
    }


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
            "elevation": [
                "terrain/3dep_dem_tiles",
                "terrain/tnm_3dep_dem_products.json",
                "terrain/usgs_3dep_chili_bar_sample_256.tif",
                "terrain/usgs_3dep_chili_bar_relief_preview_512.png",
                "terrain/usgs_3dep_chili_bar_relief_preview_manifest.json",
                "terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
                "terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png",
                "terrain/usgs_3dep_chili_bar_corridor_heightfield_manifest.json",
                "terrain/usgs_3dep_chili_bar_corridor_relief_preview_1024.png",
                "terrain/usgs_3dep_chili_bar_corridor_relief_preview_manifest.json",
                "terrain/production_import_pilot/3dep_tiles",
                "terrain/production_import_pilot/dem_relief_2048.png",
                "terrain/production_import_pilot/heightfield_candidate_2017.png",
                COURSE_ELEVATION_EXTRACTION_FILE,
                "terrain/solver_bed_grid.npy",
            ],
            "hydrography": [
                "hydrography/tnm_nhd_products.json",
                SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
                SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
                SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
                SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
            ],
            "imagery": [
                "imagery/tnm_naip_products.json",
                "imagery/usda_naip_chili_bar_sample_512.png",
                "imagery/usda_naip_chili_bar_corridor_sample_1024.png",
                "imagery/usda_naip_chili_bar_corridor_water_mask_1024.png",
                "imagery/usda_naip_chili_bar_corridor_vegetation_mask_1024.png",
                "imagery/usda_naip_chili_bar_corridor_masks_manifest.json",
                "imagery/production_import_pilot/naip_tiles",
                "imagery/production_import_pilot/source_drape_4096.png",
                "imagery/production_import_pilot/water_mask_2048.png",
                "imagery/production_import_pilot/vegetation_mask_2048.png",
                "imagery/production_import_pilot/source_masks_manifest.json",
                SOUTH_FORK_NHD_WATER_PRIOR_MANIFEST_FILE,
                SOUTH_FORK_NHD_WATER_PRIOR_FILE,
                "imagery/naip_tiles",
                "imagery/water_mask.tif",
                "imagery/foam_texture_mask.tif",
            ],
            "gauges": [
                "hydrology/usgs_11445500_daily_discharge.json",
                "hydrology/usgs_11445500_instantaneous_discharge_stage_p30d_diagnostic.json",
                "hydrology/south_fork_modern_flow_source_selection.json",
                "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
                SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
                SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
                "hydrology/flow_presets.json",
            ],
            "guide_references": [
                "review/guide_reference_index.json",
                "review/rapid_review_labels.json",
                RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
                RAPID_REVIEW_EDITOR_WORKFLOW_FILE,
                REFERENCE_MEDIA_ANNOTATIONS_FILE,
            ],
            "access_and_protected_context": [
                SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
                SOUTH_FORK_ACCESS_POINTS_FILE,
                SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
                SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
            ],
            "field_media": ["field_media/README.md", REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE],
            "solver": ["scenario/scenario.json", "scenario/bed.npy", "scenario/initial_state.npz"],
            "source_pulls": [
                "production_source_pull_manifest.json",
                SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE,
                SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE,
                SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE,
                SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE,
                SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
            ],
            "validation": ["validation_matrix.json"],
            "unreal": ["unreal/corridor_package_manifest.json"],
        },
        "provenance": {
            "generated_by": "raftsim.real_world.build_source_manifest",
            "processing_version": "milestone_9_seed.v0",
            "review_status": "seed_data_with_initial_official_source_slice_needs_human_geospatial_review",
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


def build_south_fork_access_publication_review() -> dict[str, object]:
    """Build the review-gated South Fork access and publication-sensitivity source artifact."""

    return {
        "schema": "raftsim.south_fork_access_publication_sensitivity_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "official_state_park_and_county_gis_leads_attached_review_gated",
        "scope": (
            "Access, public/private land, emergency/evacuation, concession/outfitter, and publication-sensitivity "
            "source review for the South Fork American Chili Bar to Coloma production environment pilot."
        ),
        "sources_checked": [
            {
                "source_id": "ca_state_parks_marshall_gold_discovery",
                "provider": "California State Parks",
                "url": "https://www.parks.ca.gov/?page_id=484",
                "retrieved_on": "2026-07-06",
                "http_status": 200,
                "review_status": "official_page_reviewed",
                "evidence": [
                    "Page identifies Marshall Gold Discovery State Historic Park in Coloma on the South Fork of the American River.",
                    "Page links an official ArcGIS park map and PDF tour map for local park/access review.",
                    "Page includes current restrictions, water-safety language, concessionaire links, and a river-flow lead.",
                    "Page describes Coloma/Highway 49 location context and park visitor/contact information.",
                ],
                "artifact_use": "downstream Coloma/state-park access and publication-sensitivity source lead",
                "blocked_from": [
                    "final take-out geometry",
                    "redistributing park media or map assets",
                    "claiming current operating restrictions without manual day-of review",
                ],
            },
            {
                "source_id": "ca_state_parks_marshall_arcgis_map",
                "provider": "California State Parks ArcGIS",
                "url": "https://csparks.maps.arcgis.com/apps/instant/basic/index.html?appid=065b067caa204e8da48d4b53c9483ab0&UNITNBR=304",
                "retrieved_on": "2026-07-06",
                "http_status": "linked_from_official_page_not_imported",
                "review_status": "candidate_map_layer_manual_review_required",
                "evidence": [
                    "Linked from the official Marshall Gold Discovery State Historic Park page as the park map.",
                    "No ArcGIS layer geometry, screenshots, or tiles are imported into the repository by this artifact.",
                ],
                "artifact_use": "manual park-boundary/access overlay review lead",
                "blocked_from": ["shipping map layer", "texture or asset derivation", "route-publication authority"],
            },
            {
                "source_id": "el_dorado_county_gis",
                "provider": "El Dorado County",
                "url": "https://experience.arcgis.com/experience/58a5b752c549418285583fc4c0301c29",
                "retrieved_on": "2026-07-06",
                "http_status": "linked_from_county_planning_page_not_imported",
                "review_status": "official_county_gis_lead_attached",
                "evidence": [
                    "The fetched El Dorado County planning page links the county GIS Viewer as a geospatial data and mapping platform.",
                    "The legacy river-management URL used for this check did not expose South Fork-specific river-management content in the fetched HTML.",
                ],
                "artifact_use": "public/private land, parcel, road, evacuation, and publication-sensitivity source lead",
                "blocked_from": ["parcel authority", "emergency route authority", "final access geometry"],
            },
            {
                "source_id": "blm_cronan_ranch_legacy_candidate",
                "provider": "Bureau of Land Management",
                "url": "https://www.blm.gov/visit/cronan-ranch-regional-trails-park",
                "retrieved_on": "2026-07-06",
                "http_status": 404,
                "review_status": "legacy_candidate_rejected_needs_research",
                "evidence": [
                    "Candidate URL returned 404 during this review and is not accepted as an attached source.",
                    "Find the current BLM or partner land-manager page before using Cronan/Henningsen/Lotus context.",
                ],
                "artifact_use": "negative source-lead evidence",
                "blocked_from": ["access claims", "land-manager attribution", "publication sensitivity decisions"],
            },
        ],
        "station_review_zones": [
            {
                "zone_id": "upstream_chili_bar_put_in_review_zone",
                "station_range_m": [0.0, 600.0],
                "review_status": "candidate_only_no_official_geometry_attached",
                "needs": [
                    "exact put-in ownership and access rules",
                    "commercial/private launch constraints",
                    "parking and road approach source layer",
                    "guide validation before publishing map detail",
                ],
            },
            {
                "zone_id": "mid_reach_land_status_and_rescue_review_zone",
                "station_range_m": [600.0, 4200.0],
                "review_status": "requires_county_parcel_land_manager_and_guide_review",
                "needs": [
                    "public/private parcel review",
                    "evacuation and road/trail access context",
                    "sensitive-location and cultural-resource screening",
                    "rapid rescue visibility notes",
                ],
            },
            {
                "zone_id": "coloma_marshall_gold_downstream_review_zone",
                "station_range_m": [4200.0, 5200.0],
                "review_status": "official_state_park_source_lead_attached_geometry_pending",
                "needs": [
                    "official park-boundary and access overlay review",
                    "take-out and visitor-flow validation",
                    "publication/cultural-resource sensitivity check",
                    "concession/outfitter guide review",
                ],
            },
        ],
        "required_editor_annotations": [
            SOUTH_FORK_ACCESS_POINTS_FILE,
            SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
            SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
            "review/production_import_pilot/guide_access_notes.json",
        ],
        "allowed_use": [
            "source-lead triage",
            "station-aware annotation planning",
            "publication-sensitivity checklist gating",
            "preventing over-detailed preview map publication before review",
        ],
        "forbidden_use": [
            "final access geometry",
            "public/private land authority",
            "evacuation or rescue route authority",
            "shipping screenshots that reveal sensitive route/access details without review",
            "using State Parks gallery media, maps, or third-party concession media as texture or art assets",
        ],
        "promotion_blockers": [
            "Exact put-in, take-out, parking, road, trail, and evacuation geometries are not attached.",
            "El Dorado County river-management, parcel, and public/private land layers still need exact source selection and terms review.",
            "Cultural-resource, private-property, and sensitive-location publication rules need human review before route-detail screenshots.",
            "Guide/outfitter review is required before access, scouting, rescue, or passenger-dropoff gameplay uses these zones.",
        ],
    }


def _station_sample_near(stationing: dict[str, object], station_m: float) -> dict[str, object]:
    samples = stationing.get("station_samples", [])
    if not samples:
        raise ValueError("Stationing must include station_samples")
    return min(samples, key=lambda sample: abs(float(sample["station_m"]) - station_m))


def _stationed_point(
    stationing: dict[str, object],
    station_m: float,
    *,
    offset_left_m: float = 0.0,
    offset_downstream_m: float = 0.0,
) -> tuple[list[float], dict[str, object]]:
    sample = _station_sample_near(stationing, station_m)
    lat = float(sample["lat"])
    lon = float(sample["lon"])
    east_m = float(sample.get("left_normal_east", 0.0)) * offset_left_m
    east_m += float(sample.get("tangent_east", 0.0)) * offset_downstream_m
    north_m = float(sample.get("left_normal_north", 0.0)) * offset_left_m
    north_m += float(sample.get("tangent_north", 0.0)) * offset_downstream_m
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = max(1.0, 111_320.0 * math.cos(math.radians(lat)))
    return (
        [round(lon + east_m / meters_per_degree_lon, 7), round(lat + north_m / meters_per_degree_lat, 7)],
        {
            "station_m": sample["station_m"],
            "station_sample_index": sample["sample_index"],
            "station_lon": sample["lon"],
            "station_lat": sample["lat"],
            "offset_left_m": offset_left_m,
            "offset_downstream_m": offset_downstream_m,
        },
    )


def _south_fork_access_zone(access_review: dict[str, object], zone_id: str) -> dict[str, object]:
    for zone in access_review["station_review_zones"]:
        if zone["zone_id"] == zone_id:
            return zone
    raise ValueError(f"Missing South Fork access zone {zone_id!r}")


def _south_fork_access_annotation_policy() -> dict[str, object]:
    return {
        "geometry_authority": "review_seed_from_nhd_stationing_not_official_access_geometry",
        "allowed_use": [
            "editor annotation placement",
            "guide/local review queue",
            "publication-sensitivity checklist",
            "future official layer comparison",
        ],
        "forbidden_use": [
            "final access geometry",
            "public/private land authority",
            "emergency or evacuation route authority",
            "shipping detailed route screenshots without review",
        ],
    }


def build_south_fork_access_points_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build review-only South Fork access point annotation seeds."""

    definitions = [
        (
            "chili_bar_put_in_review_seed",
            "upstream_chili_bar_put_in_review_zone",
            0.0,
            45.0,
            "put_in_review_seed",
        ),
        (
            "mid_reach_emergency_access_review_seed",
            "mid_reach_land_status_and_rescue_review_zone",
            2600.0,
            -70.0,
            "emergency_access_review_seed",
        ),
        (
            "coloma_takeout_review_seed",
            "coloma_marshall_gold_downstream_review_zone",
            5200.0,
            55.0,
            "takeout_review_seed",
        ),
    ]
    features: list[dict[str, object]] = []
    for annotation_id, zone_id, station_m, offset_left_m, role in definitions:
        zone = _south_fork_access_zone(access_review, zone_id)
        coordinates, station_properties = _stationed_point(stationing, station_m, offset_left_m=offset_left_m)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coordinates},
                "properties": {
                    "annotation_id": annotation_id,
                    "river_id": "american_south_fork",
                    "section_id": "chili_bar_to_coloma",
                    "feature_role": role,
                    "source_review_zone": zone_id,
                    "review_status": zone["review_status"],
                    "needs": zone["needs"],
                    "stationing_status": "review_seed_from_nhd_stationing_candidate_not_authoritative",
                    **station_properties,
                    "promotion_gate": (
                        "Replace or approve this seed with official access, land-status, road/trail, and guide/local "
                        "review before using it as gameplay access, rescue, or publication geometry."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork_access_points.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "review_seed_access_points_not_authoritative_geometry",
        "source_access_review": SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _south_fork_access_annotation_policy(),
        "features": features,
    }


def build_south_fork_no_publish_sensitive_polygons_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build coarse no-publish/sensitive-location polygons for editor review."""

    zone_widths = {
        "upstream_chili_bar_put_in_review_zone": 180.0,
        "mid_reach_land_status_and_rescue_review_zone": 260.0,
        "coloma_marshall_gold_downstream_review_zone": 220.0,
    }
    features: list[dict[str, object]] = []
    for zone in access_review["station_review_zones"]:
        start_m, end_m = zone["station_range_m"]
        half_width = zone_widths.get(zone["zone_id"], 200.0)
        start_left, start_props = _stationed_point(stationing, start_m, offset_left_m=half_width)
        end_left, _ = _stationed_point(stationing, end_m, offset_left_m=half_width)
        end_right, end_props = _stationed_point(stationing, end_m, offset_left_m=-half_width)
        start_right, _ = _stationed_point(stationing, start_m, offset_left_m=-half_width)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[start_left, end_left, end_right, start_right, start_left]],
                },
                "properties": {
                    "annotation_id": f"{zone['zone_id']}_no_publish_review_seed",
                    "river_id": "american_south_fork",
                    "section_id": "chili_bar_to_coloma",
                    "feature_role": "no_publish_sensitive_context_review_seed",
                    "source_review_zone": zone["zone_id"],
                    "review_status": zone["review_status"],
                    "needs": zone["needs"],
                    "station_start_m": start_props["station_m"],
                    "station_end_m": end_props["station_m"],
                    "half_width_m": half_width,
                    "stationing_status": "coarse_buffer_from_nhd_stationing_candidate_not_sensitive_polygon_authority",
                    "promotion_gate": (
                        "Use only as an editor reminder to screen cultural, private-property, access, and safety-sensitive "
                        "details; replace with reviewed no-publish geometry before public route screenshots."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork_no_publish_sensitive_polygons.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "coarse_review_seed_no_publish_polygons_not_authoritative",
        "source_access_review": SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _south_fork_access_annotation_policy(),
        "features": features,
    }


def build_south_fork_evacuation_rescue_routes_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build review-only South Fork evacuation/rescue route seed lines."""

    features: list[dict[str, object]] = []
    for zone in access_review["station_review_zones"]:
        start_m, end_m = zone["station_range_m"]
        mid_m = (float(start_m) + float(end_m)) / 2.0
        coordinates = [
            _stationed_point(stationing, start_m, offset_left_m=-95.0)[0],
            _stationed_point(stationing, mid_m, offset_left_m=-120.0)[0],
            _stationed_point(stationing, end_m, offset_left_m=-95.0)[0],
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "annotation_id": f"{zone['zone_id']}_evacuation_rescue_review_seed",
                    "river_id": "american_south_fork",
                    "section_id": "chili_bar_to_coloma",
                    "feature_role": "evacuation_rescue_route_review_seed",
                    "source_review_zone": zone["zone_id"],
                    "review_status": zone["review_status"],
                    "needs": zone["needs"],
                    "station_range_m": zone["station_range_m"],
                    "stationing_status": "coarse_offset_line_from_nhd_stationing_candidate_not_route_authority",
                    "promotion_gate": (
                        "Replace with official road/trail/access layers, emergency/local review, and guide validation "
                        "before using as rescue, evacuation, passenger-dropoff, or gameplay route geometry."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork_evacuation_rescue_routes.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "coarse_review_seed_evacuation_rescue_routes_not_authoritative",
        "source_access_review": SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _south_fork_access_annotation_policy(),
        "features": features,
    }


def build_colorado_river_mile_markers_geojson(stationing: dict[str, object]) -> dict[str, object]:
    """Build preview river-mile marker seeds from Colorado NHD stationing."""

    mile_m = 1609.344
    length_m = float(stationing["summary"]["length_m_geodesic_vertices"])
    marker_count = int(length_m // mile_m) + 1
    features: list[dict[str, object]] = []
    for mile in range(marker_count):
        station_m = mile * mile_m
        coordinates, station_properties = _stationed_point(stationing, station_m)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coordinates},
                "properties": {
                    "annotation_id": f"colorado_preview_river_mile_{mile:03d}",
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "preview_river_mile_marker_review_seed",
                    "preview_river_mile": mile,
                    "review_status": "nhd_stationing_preview_not_official_grand_canyon_river_mile",
                    "stationing_status": "review_seed_from_nhd_stationing_candidate_not_authoritative",
                    **station_properties,
                    "promotion_gate": (
                        "Replace or approve against official Grand Canyon river-mile stationing, NPS/GCMRC context, "
                        "release-aware water edge review, and oarsman validation before production route use."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.colorado_river_mile_markers.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "preview_river_mile_markers_from_nhd_stationing_not_official",
        "stationing_source": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "policy": {
            "geometry_authority": "review_seed_from_nhd_stationing_not_official_river_miles",
            "allowed_use": [
                "editor route orientation",
                "oarsman review queue",
                "future NPS/GCMRC river-mile comparison",
            ],
            "forbidden_use": [
                "official Grand Canyon river-mile stationing",
                "permit or route-publication authority",
                "production gameplay distance claims",
            ],
        },
        "features": features,
    }


def build_colorado_sandbar_review_seeds_geojson(stationing: dict[str, object]) -> dict[str, object]:
    """Build release-sensitive Colorado sandbar review seed polygons."""

    seed_definitions = [
        ("lees_ferry_margin_sandbar_review_seed", 1600.0, "river_left", 1),
        ("paria_context_sandbar_review_seed", 4500.0, "river_right", -1),
        ("cathedral_wash_margin_sandbar_review_seed", 7800.0, "river_left", 1),
        ("marble_canyon_bend_sandbar_review_seed", 11800.0, "river_right", -1),
        ("rowing_recovery_bar_review_seed", 16600.0, "river_left", 1),
        ("downstream_wet_bank_sandbar_review_seed", 21000.0, "river_right", -1),
    ]
    features: list[dict[str, object]] = []
    for annotation_id, station_m, side_label, side in seed_definitions:
        upstream_inner, upstream_props = _stationed_point(
            stationing,
            station_m,
            offset_left_m=side * 80.0,
            offset_downstream_m=-180.0,
        )
        downstream_inner, _ = _stationed_point(
            stationing,
            station_m,
            offset_left_m=side * 80.0,
            offset_downstream_m=180.0,
        )
        downstream_outer, downstream_props = _stationed_point(
            stationing,
            station_m,
            offset_left_m=side * 220.0,
            offset_downstream_m=180.0,
        )
        upstream_outer, _ = _stationed_point(
            stationing,
            station_m,
            offset_left_m=side * 220.0,
            offset_downstream_m=-180.0,
        )
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[upstream_inner, downstream_inner, downstream_outer, upstream_outer, upstream_inner]],
                },
                "properties": {
                    "annotation_id": annotation_id,
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "release_sensitive_sandbar_review_seed",
                    "river_side_hint": side_label,
                    "station_m": upstream_props["station_m"],
                    "station_sample_index": upstream_props["station_sample_index"],
                    "station_end_m": downstream_props["station_m"],
                    "review_status": "preview_sandbar_seed_not_geomorphic_boundary_or_camp_beach_authority",
                    "stationing_status": "coarse_polygon_from_nhd_stationing_candidate_not_sandbar_authority",
                    "flow_dependency": (
                        "Review exposed/wet/submerged state across low, moderate, high, and subdaily release variants "
                        "before using this as art, rowing, camp/beach, or rescue geometry."
                    ),
                    "promotion_gate": (
                        "Replace or approve against visible imagery, DEM relief, release-band history, NPS/GCMRC or "
                        "guide/oarsman review, and access/publication sensitivity before production use."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.colorado_sandbar_review_seeds.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "release_sensitive_sandbar_review_seeds_not_authoritative",
        "stationing_source": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "policy": {
            "geometry_authority": "review_seed_from_nhd_stationing_not_geomorphic_or_camp_boundary",
            "allowed_use": [
                "editor sandbar and wet-bank review",
                "release-band visual planning",
                "oarsman review queue",
            ],
            "forbidden_use": [
                "camp or beach publication authority",
                "final sandbar geometry",
                "release-dependent gameplay clearance",
            ],
        },
        "features": features,
    }


def _colorado_access_zone(access_review: dict[str, object], zone_id: str) -> dict[str, object]:
    for zone in access_review["station_review_zones"]:
        if zone["zone_id"] == zone_id:
            return zone
    raise ValueError(f"Missing Colorado access zone {zone_id!r}")


def _colorado_access_annotation_policy() -> dict[str, object]:
    return {
        "geometry_authority": "review_seed_from_nhd_stationing_not_official_nps_access_or_camp_geometry",
        "allowed_use": [
            "editor access and publication review",
            "oarsman route-note placement",
            "future NPS/GCMRC/manual layer comparison",
        ],
        "forbidden_use": [
            "permit or legal advice",
            "final launch, take-out, camp, beach, or road geometry",
            "public camp/beach/sensitive-resource publication",
            "production route authority",
        ],
    }


def build_colorado_access_points_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build review-only Colorado access point annotation seeds."""

    launch_zone = _colorado_access_zone(access_review, "lees_ferry_launch_review_zone")
    route_zone = _colorado_access_zone(access_review, "grand_canyon_camps_beaches_sensitive_context_review_zone")
    takeout_zone = _colorado_access_zone(access_review, "diamond_creek_takeout_review_zone")
    launch_coords, launch_props = _stationed_point(stationing, 0.0, offset_left_m=80.0)
    scout_coords, scout_props = _stationed_point(stationing, 12000.0, offset_left_m=-120.0)
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.colorado_access_points.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "review_seed_access_points_not_authoritative_geometry",
        "source_access_review": COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _colorado_access_annotation_policy(),
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": launch_coords},
                "properties": {
                    "annotation_id": "lees_ferry_launch_access_review_seed",
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "launch_access_review_seed",
                    "source_review_zone": launch_zone["zone_id"],
                    "review_status": launch_zone["review_status"],
                    "needs": launch_zone["needs"],
                    "stationing_status": "review_seed_from_nhd_stationing_candidate_not_authoritative",
                    **launch_props,
                    "promotion_gate": "Replace with official launch, rigging, parking, staging, and oarsman-reviewed geometry before production use.",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": scout_coords},
                "properties": {
                    "annotation_id": "lees_ferry_slice_route_context_review_seed",
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "route_context_access_review_seed",
                    "source_review_zone": route_zone["zone_id"],
                    "review_status": route_zone["review_status"],
                    "needs": route_zone["needs"],
                    "stationing_status": "review_seed_from_nhd_stationing_candidate_not_authoritative",
                    **scout_props,
                    "promotion_gate": "Use as an editor note only until camp/beach/sensitive-resource and oarsman review assigns real geometry.",
                },
            },
            {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "annotation_id": "diamond_creek_takeout_outside_pilot_review_placeholder",
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "out_of_pilot_takeout_review_placeholder",
                    "source_review_zone": takeout_zone["zone_id"],
                    "review_status": takeout_zone["review_status"],
                    "needs": takeout_zone["needs"],
                    "stationing_status": "outside_lees_ferry_pilot_slice_no_geometry_seeded",
                    "promotion_gate": "Do not create take-out geometry until full-route stationing and approved access sources are attached.",
                },
            },
        ],
    }


def build_colorado_no_publish_sensitive_polygons_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build coarse Colorado no-publish publication-sensitivity review polygons."""

    launch_zone = _colorado_access_zone(access_review, "lees_ferry_launch_review_zone")
    route_zone = _colorado_access_zone(access_review, "grand_canyon_camps_beaches_sensitive_context_review_zone")
    takeout_zone = _colorado_access_zone(access_review, "diamond_creek_takeout_review_zone")

    def polygon_for(annotation_id: str, zone: dict[str, object], start_m: float, end_m: float, half_width_m: float) -> dict[str, object]:
        start_left, start_props = _stationed_point(stationing, start_m, offset_left_m=half_width_m)
        end_left, _ = _stationed_point(stationing, end_m, offset_left_m=half_width_m)
        end_right, end_props = _stationed_point(stationing, end_m, offset_left_m=-half_width_m)
        start_right, _ = _stationed_point(stationing, start_m, offset_left_m=-half_width_m)
        return {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[start_left, end_left, end_right, start_right, start_left]]},
            "properties": {
                "annotation_id": annotation_id,
                "river_id": "colorado_river",
                "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                "feature_role": "no_publish_sensitive_context_review_seed",
                "source_review_zone": zone["zone_id"],
                "review_status": zone["review_status"],
                "needs": zone["needs"],
                "station_start_m": start_props["station_m"],
                "station_end_m": end_props["station_m"],
                "half_width_m": half_width_m,
                "stationing_status": "coarse_buffer_from_nhd_stationing_candidate_not_publication_boundary",
                "promotion_gate": "Replace with reviewed camp/beach, cultural-resource, sensitive-location, and screenshot-safety rules before public route captures.",
            },
        }

    return {
        "type": "FeatureCollection",
        "schema": "raftsim.colorado_no_publish_sensitive_polygons.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "coarse_review_seed_no_publish_polygons_not_authoritative",
        "source_access_review": COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _colorado_access_annotation_policy(),
        "features": [
            polygon_for("lees_ferry_launch_no_publish_review_seed", launch_zone, 0.0, 1609.344, 320.0),
            polygon_for("lees_ferry_slice_route_no_publish_review_seed", route_zone, 1609.344, 24223.694, 420.0),
            {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "annotation_id": "diamond_creek_takeout_no_publish_outside_pilot_placeholder",
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "out_of_pilot_no_publish_review_placeholder",
                    "source_review_zone": takeout_zone["zone_id"],
                    "review_status": takeout_zone["review_status"],
                    "needs": takeout_zone["needs"],
                    "stationing_status": "outside_lees_ferry_pilot_slice_no_geometry_seeded",
                    "promotion_gate": "No Diamond Creek publication geometry is seeded in the Lees Ferry pilot slice.",
                },
            },
        ],
    }


def build_colorado_camps_and_beaches_review_geojson(
    access_review: dict[str, object],
    stationing: dict[str, object],
) -> dict[str, object]:
    """Build Colorado camps/beaches review seed polygons."""

    route_zone = _colorado_access_zone(access_review, "grand_canyon_camps_beaches_sensitive_context_review_zone")
    seed_definitions = [
        ("lees_ferry_slice_beach_review_seed_01", 4200.0, "river_right", -1),
        ("lees_ferry_slice_beach_review_seed_02", 8200.0, "river_left", 1),
        ("lees_ferry_slice_beach_review_seed_03", 13200.0, "river_right", -1),
        ("lees_ferry_slice_beach_review_seed_04", 18800.0, "river_left", 1),
    ]
    features: list[dict[str, object]] = []
    for annotation_id, station_m, side_label, side in seed_definitions:
        upstream_inner, props = _stationed_point(stationing, station_m, offset_left_m=side * 90.0, offset_downstream_m=-140.0)
        downstream_inner, _ = _stationed_point(stationing, station_m, offset_left_m=side * 90.0, offset_downstream_m=140.0)
        downstream_outer, _ = _stationed_point(stationing, station_m, offset_left_m=side * 260.0, offset_downstream_m=140.0)
        upstream_outer, _ = _stationed_point(stationing, station_m, offset_left_m=side * 260.0, offset_downstream_m=-140.0)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[upstream_inner, downstream_inner, downstream_outer, upstream_outer, upstream_inner]],
                },
                "properties": {
                    "annotation_id": annotation_id,
                    "river_id": "colorado_river",
                    "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
                    "feature_role": "camp_beach_publication_review_seed",
                    "river_side_hint": side_label,
                    "source_review_zone": route_zone["zone_id"],
                    "review_status": "preview_beach_seed_not_camp_beach_or_publication_authority",
                    "needs": route_zone["needs"],
                    "station_m": props["station_m"],
                    "station_sample_index": props["station_sample_index"],
                    "stationing_status": "coarse_polygon_from_nhd_stationing_candidate_not_camp_beach_authority",
                    "promotion_gate": "Replace with approved camp/beach/sandbar review, release context, and oarsman notes before production or public screenshots.",
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.colorado_camps_and_beaches_review.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "camp_beach_review_seeds_not_authoritative",
        "source_access_review": COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
        "stationing_source": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "policy": _colorado_access_annotation_policy(),
        "features": features,
    }


def build_colorado_oarsman_route_publication_notes(
    access_review: dict[str, object],
    river_mile_markers: dict[str, object],
    sandbars: dict[str, object],
    camps_and_beaches: dict[str, object],
) -> dict[str, object]:
    """Build review-gated Colorado oarsman publication notes."""

    return {
        "schema": "raftsim.colorado_oarsman_route_publication_notes.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "oarsman_publication_notes_template_attached_review_required",
        "inputs": {
            "access_publication_review": COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
            "river_mile_markers": COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE,
            "sandbars": COLORADO_PRODUCTION_SANDBARS_FILE,
            "camps_and_beaches_review": COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
        },
        "source_review_zones": access_review["station_review_zones"],
        "review_overlay_summary": {
            "preview_river_mile_marker_count": len(river_mile_markers["features"]),
            "sandbar_review_seed_count": len(sandbars["features"]),
            "camp_beach_review_seed_count": len(camps_and_beaches["features"]),
        },
        "required_oarsman_fields": [
            "reviewer_name_or_role",
            "review_date",
            "flow_or_release_context",
            "launch_and_rigging_sightline_notes",
            "sandbar_wet_bank_release_notes",
            "camp_beach_publication_limits",
            "long_swimmer_and_rescue_visibility_notes",
            "screenshot_or_map_detail_limits",
        ],
        "allowed_use": [
            "oarsman review checklist",
            "publication-sensitivity handoff",
            "future river-mile and release-aware route validation",
        ],
        "forbidden_use": [
            "permit or legal advice",
            "current access operation claims",
            "camp/beach publication clearance",
            "final river-mile or route authority",
        ],
        "promotion_blockers": [
            "No completed oarsman reviewer identity, date, flow/release context, or approval is attached.",
            "River-mile markers, sandbars, camps, beaches, and access points are review seeds only.",
            "NPS/current operating constraints and sensitive-resource publication rules still need human review before public route detail.",
        ],
    }


def _pacuare_station_sample_near(stationing: dict[str, object], station_m: float) -> dict[str, object]:
    samples = stationing.get("station_samples", [])
    if not samples:
        raise ValueError("Pacuare stationing must include station_samples")
    return min(samples, key=lambda sample: abs(float(sample["station_m"]) - station_m))


def _pacuare_stationed_point(
    stationing: dict[str, object],
    station_m: float,
    *,
    offset_left_m: float = 0.0,
    offset_downstream_m: float = 0.0,
) -> tuple[list[float], dict[str, object]]:
    sample = _pacuare_station_sample_near(stationing, station_m)
    lat = float(sample["lat"])
    lon = float(sample["lon"])
    left_east, left_north = sample["river_left_normal_local_m"]
    tangent_east, tangent_north = sample["downstream_tangent_local_m"]
    east_m = float(left_east) * offset_left_m + float(tangent_east) * offset_downstream_m
    north_m = float(left_north) * offset_left_m + float(tangent_north) * offset_downstream_m
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = max(1.0, 111_320.0 * math.cos(math.radians(lat)))
    return (
        [round(lon + east_m / meters_per_degree_lon, 7), round(lat + north_m / meters_per_degree_lat, 7)],
        {
            "station_m": sample["station_m"],
            "station_sample_index": sample["sample_index"],
            "station_lon": sample["lon"],
            "station_lat": sample["lat"],
            "offset_left_m": offset_left_m,
            "offset_downstream_m": offset_downstream_m,
        },
    )


def build_pacuare_production_centerline_draft_geojson(preview_centerline: dict[str, object]) -> dict[str, object]:
    """Build the Pacuare production-import centerline review draft from the preview scaffold."""

    source_feature = preview_centerline["features"][0]
    return {
        "type": "FeatureCollection",
        "name": "pacuare_production_centerline_draft_from_preview_scaffold",
        "schema": "raftsim.pacuare_production_centerline_draft.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "draft_from_preview_scaffold_review_required_not_official_hydrography",
        "source_centerline": PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
        "features": [
            {
                "type": "Feature",
                "geometry": source_feature["geometry"],
                "properties": {
                    "river_id": "pacuare",
                    "section_id": "lower_pacuare_planning_corridor",
                    "feature_role": "production_import_centerline_review_draft",
                    "status": "draft_from_preview_scaffold_review_gated_not_final_centerline",
                    "source_status": source_feature["properties"]["status"],
                    "stationing": PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
                    "promotion_gate": (
                        "Replace or approve against official Costa Rica hydrography, working CRS, imagery/DEM alignment, "
                        "banks, rapid/access stationing, protected-area review, and guide/outfitter validation before "
                        "solver or Unreal production use."
                    ),
                },
            }
        ],
    }


def build_pacuare_production_banks_draft_geojson(stationing: dict[str, object]) -> dict[str, object]:
    """Build Pacuare bank review draft lines from preview stationing normals."""

    bank_features: list[dict[str, object]] = []
    for side_label, side, offset_m in (("river_left", 1.0, 55.0), ("river_right", -1.0, -55.0)):
        coordinates = [
            _pacuare_stationed_point(stationing, sample["station_m"], offset_left_m=offset_m)[0]
            for sample in stationing["station_samples"]
        ]
        bank_features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "bank_id": f"pacuare_{side_label}_preview_bank_offset",
                    "river_id": "pacuare",
                    "section_id": "lower_pacuare_planning_corridor",
                    "feature_role": "production_import_bank_review_draft",
                    "river_side": side_label,
                    "offset_m_from_preview_centerline": abs(offset_m) * side,
                    "status": "draft_offset_from_preview_stationing_not_bank_or_wetted_width",
                    "promotion_gate": (
                        "Replace with bank/wetted-width geometry from official hydrography, conditioned DEM, "
                        "cloud-screened imagery, flow review, and guide/outfitter validation."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "pacuare_production_bank_review_drafts",
        "schema": "raftsim.pacuare_production_banks_draft.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "draft_bank_offsets_from_preview_stationing_review_required",
        "stationing_source": PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
        "features": bank_features,
    }


def build_pacuare_rapid_access_stationing_draft_geojson(stationing: dict[str, object]) -> dict[str, object]:
    """Build Pacuare rapid/access station review points from preview stationing."""

    definitions = [
        ("pacuare_upper_access_review_seed", 0.0, "access_review_seed", 70.0),
        ("pacuare_rainforest_entry_wave_train_review_seed", 8500.0, "rapid_review_seed", 0.0),
        ("pacuare_gorge_hole_lateral_review_seed", 17000.0, "rapid_feature_review_seed", -40.0),
        ("pacuare_waterfall_mist_reference_review_seed", 24500.0, "environment_reference_review_seed", 85.0),
        ("pacuare_rescue_visibility_review_seed", 32500.0, "rescue_review_seed", -80.0),
        ("pacuare_downstream_takeout_review_seed", 43000.0, "access_review_seed", 65.0),
    ]
    features: list[dict[str, object]] = []
    for annotation_id, station_m, role, offset_left_m in definitions:
        coordinates, station_props = _pacuare_stationed_point(stationing, station_m, offset_left_m=offset_left_m)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coordinates},
                "properties": {
                    "annotation_id": annotation_id,
                    "river_id": "pacuare",
                    "section_id": "lower_pacuare_planning_corridor",
                    "feature_role": role,
                    "review_status": "preview_stationing_seed_not_official_rapid_or_access_geometry",
                    "stationing_status": "derived_from_unreal_preview_scaffold_not_authoritative",
                    **station_props,
                    "promotion_gate": (
                        "Replace with official hydrography/access stationing, flow/rain context, protected-area review, "
                        "and guide/outfitter validation before gameplay or public route use."
                    ),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.pacuare_rapid_access_stationing_draft.geojson.v1",
        "generated_on": "2026-07-06",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "status": "preview_rapid_access_stationing_review_seeds_not_authoritative",
        "stationing_source": PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
        "features": features,
    }


def build_south_fork_flow_band_review(
    flow_presets: dict[str, object],
    cdec_flow_context: dict[str, object],
    source_selection: dict[str, object],
) -> dict[str, object]:
    """Compare South Fork planning flow bands to the attached CDEC review window."""

    daily_rows = cdec_flow_context["daily_cbr_flow_stage_summary"]
    valid_rows = [row for row in daily_rows if row.get("flow_valid_count", 0) > 0]
    peak_values = [float(row["flow_peak_cfs"]) for row in valid_rows if row.get("flow_peak_cfs") is not None]
    median_values = [float(row["flow_median_cfs"]) for row in valid_rows if row.get("flow_median_cfs") is not None]
    stage_peaks = [float(row["stage_peak_ft"]) for row in valid_rows if row.get("stage_peak_ft") is not None]
    total_valid_samples = int(sum(int(row.get("flow_valid_count", 0)) for row in valid_rows))
    observed_max_cfs = max(peak_values) if peak_values else 0.0

    def observed_hours(row: dict[str, object], threshold_cfs: float) -> float:
        if math.isclose(threshold_cfs, 900.0):
            return float(row.get("hours_flow_ge_low_runnable_900_cfs", 0.0) or 0.0)
        if math.isclose(threshold_cfs, 1600.0):
            return float(row.get("hours_flow_ge_median_runnable_1600_cfs", 0.0) or 0.0)
        if threshold_cfs > observed_max_cfs:
            return 0.0
        return 0.0

    reviewed_bands: list[dict[str, object]] = []
    for band in flow_presets["flow_bands"]:
        threshold_cfs = float(band["discharge_cfs"])
        peak_rows = [row for row in valid_rows if float(row.get("flow_peak_cfs") or 0.0) >= threshold_cfs]
        median_rows = [row for row in valid_rows if float(row.get("flow_median_cfs") or 0.0) >= threshold_cfs]
        hours_ge_threshold = round(sum(observed_hours(row, threshold_cfs) for row in valid_rows), 3)
        peak_dates = [
            {
                "date_local": row["date_local"],
                "flow_peak_cfs": row["flow_peak_cfs"],
                "flow_peak_time_local": row["flow_peak_time_local"],
                "stage_peak_ft": row["stage_peak_ft"],
            }
            for row in sorted(peak_rows, key=lambda item: float(item.get("flow_peak_cfs") or 0.0), reverse=True)[:8]
        ]
        if peak_rows:
            evidence_status = "observed_as_short_release_window_not_seasonal_validation"
        else:
            evidence_status = "not_observed_in_attached_30_day_context"
        reviewed_bands.append(
            {
                "flow_band": band["flow_band"],
                "season": band["season"],
                "planning_discharge_cfs": threshold_cfs,
                "planning_discharge_m3s": band["discharge_m3s"],
                "planning_notes": band["notes"],
                "planning_confidence": band["confidence"],
                "observed_peak_days_ge_planning_flow": len(peak_rows),
                "observed_median_days_ge_planning_flow": len(median_rows),
                "observed_hours_ge_planning_flow": hours_ge_threshold,
                "observed_peak_dates": peak_dates,
                "evidence_status": evidence_status,
                "promotion_decision": "blocked_pending_broader_windows_release_context_station_routing_guide_review",
                "review_use": (
                    "Use as a visual/gameplay discussion aid only; do not retune solver presets, holes, wave trains, "
                    "wet banks, or lifelike water appearance from this 30-day window alone."
                ),
            }
        )

    return {
        "schema": "raftsim.south_fork_flow_band_review.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "review_gated_do_not_promote_presets",
        "inputs": {
            "flow_presets": "physics/data/real_world/south_fork_american_chili_bar/flow_presets.json",
            "cdec_context": "physics/data/real_world/south_fork_american_chili_bar/hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json",
            "source_selection": "physics/data/real_world/south_fork_american_chili_bar/hydrology/south_fork_modern_flow_source_selection.json",
            "terms_flags_station_relation_review": "physics/data/real_world/south_fork_american_chili_bar/hydrology/cdec_terms_flags_and_station_relation_review.json",
        },
        "cdec_window_summary": {
            "requested_start": cdec_flow_context["request_window"]["requested_start"],
            "requested_end": cdec_flow_context["request_window"]["requested_end"],
            "valid_sample_count": total_valid_samples,
            "valid_day_count": len(valid_rows),
            "flow_min_cfs": min(float(row["flow_min_cfs"]) for row in valid_rows),
            "flow_median_of_daily_medians_cfs": round(float(np.median(median_values)), 3),
            "flow_peak_max_cfs": observed_max_cfs,
            "stage_peak_max_ft": max(stage_peaks) if stage_peaks else None,
            "days_peak_ge_900_cfs": sum(1 for row in valid_rows if float(row.get("flow_peak_cfs") or 0.0) >= 900.0),
            "days_peak_ge_1600_cfs": sum(1 for row in valid_rows if float(row.get("flow_peak_cfs") or 0.0) >= 1600.0),
            "days_peak_ge_3000_cfs": sum(1 for row in valid_rows if float(row.get("flow_peak_cfs") or 0.0) >= 3000.0),
            "total_hours_ge_900_cfs": round(sum(float(row.get("hours_flow_ge_low_runnable_900_cfs", 0.0) or 0.0) for row in valid_rows), 3),
            "total_hours_ge_1600_cfs": round(sum(float(row.get("hours_flow_ge_median_runnable_1600_cfs", 0.0) or 0.0) for row in valid_rows), 3),
            "a25_valid_daily_generation_samples": source_selection["cdec_30_day_context_window"]["summary"][
                "a25_valid_daily_generation_samples"
            ],
            "a25_unlisted_flags_observed": source_selection["cdec_30_day_context_window"]["summary"][
                "a25_unlisted_flags_observed"
            ],
        },
        "reviewed_bands": reviewed_bands,
        "promotion_blockers": [
            "Attached evidence is a 30-day early-summer CDEC context window, not representative seasonal coverage.",
            "A25 X-flag meaning and station-to-reach release routing are unresolved.",
            "Legal/redistribution signoff, guide/outfitter validation, and hydrologic station-to-rapid relation remain open.",
            "High-flow planning at 3000 cfs was not observed in the attached window and needs separate runoff/release evidence.",
        ],
        "allowed_use": [
            "editor flow-band review",
            "guide discussion",
            "future low/median/high visual variant planning",
            "identifying missing seasonal CDEC/A25 pulls",
        ],
        "forbidden_use": [
            "final preset retuning",
            "claiming accepted seasonal flow bands",
            "hiding water-simulation conservation failures with visuals or forcing",
            "production lifelike water approval",
        ],
    }


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
                                "difficulty_presets": list(DIFFICULTY_PRESETS),
                                "flow_difficulty_mapping": RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
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


def build_rapid_review_flow_difficulty_mapping(
    package: RealWorldCorridorPackage | None = None,
) -> RapidReviewFlowDifficultyMapping:
    """Expose label-specific flow response and difficulty tuning controls."""

    target = package or build_real_world_corridor_package()
    labels = default_manual_rapid_review_labels()
    representative_width = float(np.mean([station.channel_width_m for station in target.centerline]))
    return RapidReviewFlowDifficultyMapping(
        river_id=target.section.river_id,
        section_id=target.section.section_id,
        source_manifest=SOURCE_MANIFEST_FILE,
        label_catalog=labels,
        flow_bands=target.flow_bands,
        difficulty_presets=_rapid_review_difficulty_presets(),
        label_flow_responses=tuple(
            _rapid_review_label_flow_response(label, target.flow_bands)
            for label in labels
        ),
        parameter_matrix=_rapid_review_parameter_matrix(
            target.section,
            target.flow_bands,
            representative_width,
        ),
        review_requirements=(
            "Every accepted rapid label must name the flow band and difficulty presets it was reviewed against.",
            "Hole, lateral, eddy-line, boulder, shelf, pin, release, and flip behavior must stay flow-dependent; fixed gains are review failures.",
            "Gameplay forcing can be tuned from this mapping only after GeoClaw/C++ conservation and feature validation pass for the same flow band.",
            "Guide feedback, footage, imagery, and gauge context must remain source-manifest linked with rights/provenance before production use.",
        ),
        provenance={
            "generated_by": "raftsim.real_world.build_rapid_review_flow_difficulty_mapping",
            "processing_version": "milestone_17_flow_difficulty_mapping_seed.v0",
            "review_status": "seed_mapping_needs_gauge_history_and_guide_review",
            "source_limitations": (
                "Uses preliminary South Fork flow bands and hand-authored label response curves; "
                "production mapping must be calibrated against gauge history, footage, guide feedback, "
                "GeoClaw/C++ validation, and game-feel review."
            ),
        },
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
            "course_elevation_extraction": COURSE_ELEVATION_EXTRACTION_FILE,
            "rapids": "review/rapid_candidates.geojson",
            "hazards": "review/rapid_review_labels.json",
            "rapid_review_editor_workflow": RAPID_REVIEW_EDITOR_WORKFLOW_FILE,
            "rapid_review_flow_difficulty_mapping": RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
            "flow_presets": "hydrology/flow_presets.json",
            "validation_matrix": "validation_matrix.json",
            "confidence_metadata": "confidence.json",
        },
    )


def build_course_elevation_extraction(
    package: RealWorldCorridorPackage | None = None,
) -> CourseElevationExtraction:
    """Build the first section-level course/elevation extraction artifact."""

    target = package or build_real_world_corridor_package()
    centerline = tuple(sorted(target.centerline, key=lambda station: station.station_m))
    indicators = tuple(sorted(target.indicators, key=lambda indicator: indicator.station_m))
    if not centerline:
        raise ValueError("Course/elevation extraction requires centerline stations.")
    if not indicators:
        raise ValueError("Course/elevation extraction requires channel indicators.")
    station_start = centerline[0].station_m
    station_end = centerline[-1].station_m
    length_m = station_end - station_start
    if length_m <= 0.0:
        raise ValueError("Course/elevation extraction requires a positive station span.")

    samples: list[CourseElevationSample] = []
    start_elevation = centerline[0].elevation_m
    previous_elevation = start_elevation
    for station in centerline:
        indicator = min(indicators, key=lambda item: abs(item.station_m - station.station_m))
        local_drop = max(0.0, previous_elevation - station.elevation_m)
        samples.append(
            CourseElevationSample(
                station_m=station.station_m,
                lon=station.lon,
                lat=station.lat,
                elevation_m=station.elevation_m,
                channel_width_m=station.channel_width_m,
                local_drop_m=local_drop,
                cumulative_drop_m=max(0.0, start_elevation - station.elevation_m),
                gradient=indicator.gradient,
                left_bank_offset_m=indicator.left_bank_offset_m,
                right_bank_offset_m=indicator.right_bank_offset_m,
                constriction_score=indicator.constriction_score,
                roughness_score=indicator.roughness_score,
                rapid_score=indicator.rapid_score,
                signals=indicator.signals,
            )
        )
        previous_elevation = station.elevation_m

    elevations = np.asarray([station.elevation_m for station in centerline], dtype=np.float64)
    widths = np.asarray([station.channel_width_m for station in centerline], dtype=np.float64)
    gradients = np.asarray([indicator.gradient for indicator in indicators], dtype=np.float64)
    total_drop = max(0.0, float(elevations[0] - elevations[-1]))
    cross_sections = tuple(
        _course_elevation_cross_section_prototype(target, indicator, index + 1)
        for index, indicator in enumerate(indicators)
    )
    summary = {
        "station_start_m": station_start,
        "station_end_m": station_end,
        "length_m": length_m,
        "elevation_start_m": float(elevations[0]),
        "elevation_end_m": float(elevations[-1]),
        "total_drop_m": total_drop,
        "mean_gradient": total_drop / length_m,
        "max_local_gradient": float(np.max(gradients)),
        "min_local_gradient": float(np.min(gradients)),
        "min_channel_width_m": float(np.min(widths)),
        "max_channel_width_m": float(np.max(widths)),
        "mean_channel_width_m": float(np.mean(widths)),
        "sample_count": len(samples),
        "cross_section_prototype_count": len(cross_sections),
        "rapid_candidate_count": len(target.rapid_candidates),
    }
    return CourseElevationExtraction(
        river_id=target.section.river_id,
        section_id=target.section.section_id,
        source_manifest=SOURCE_MANIFEST_FILE,
        source_artifacts={
            "source_manifest": SOURCE_MANIFEST_FILE,
            "dem_lidar": "terrain/3dep_dem_tiles",
            "flowlines": "hydrography/centerline.geojson",
            "banks": "hydrography/banks.geojson",
            "cross_sections": "hydrography/cross_sections.geojson",
            "solver_bed_grid": "terrain/solver_bed_grid.npy",
            "course_elevation_extraction": COURSE_ELEVATION_EXTRACTION_FILE,
        },
        samples=tuple(samples),
        summary=summary,
        cross_section_prototypes=cross_sections,
        provenance={
            "generated_by": "raftsim.real_world.build_course_elevation_extraction",
            "processing_version": "milestone_17_course_elevation_seed.v0",
            "extraction_method": "seed_centerline_station_interpolation_with_indicator_cross_sections",
            "review_status": "prototype_needs_real_dem_lidar_hydrography_pull",
            "source_limitations": (
                "Uses coarse planning stations and derived indicators only; production extraction must replace "
                "these with CRS-recorded DEM/lidar, flowline, bank, water-mask, and cross-section measurements."
            ),
        },
    )


def build_rapid_review_editor_workflow(
    package: RealWorldCorridorPackage | None = None,
) -> RapidReviewEditorWorkflow:
    """Build the first one-view rapid review/editor workflow payload."""

    target = package or build_real_world_corridor_package()
    return RapidReviewEditorWorkflow(
        river_id=target.section.river_id,
        section_id=target.section.section_id,
        source_manifest=SOURCE_MANIFEST_FILE,
        layers=_rapid_review_layers(),
        panels=_rapid_review_panels(),
        review_items=tuple(_rapid_review_item(target, candidate) for candidate in target.rapid_candidates),
        label_catalog=default_manual_rapid_review_labels(),
        save_targets=(
            "review/rapid_candidates.geojson",
            "review/river_validation_annotations.geojson",
            "review/feature_annotations.geojson",
            "scenario/source_manifest_links.json",
        ),
        export_targets=(
            "python_scenario_generation",
            "geoclaw_cpp_validation_reports",
            "unreal_data_assets",
        ),
        quality_gates=(
            "Every accepted rapid has DEM/lidar, imagery, flowline, cross-section, gauge, source-manifest, candidate-tag, and guide-note context visible in the one-view layout.",
            "Every accepted annotation records rights/provenance before it can feed validation or Unreal data assets.",
            "Guidebook text, third-party imagery, and field media remain referenced through manifests unless redistribution rights are explicit.",
        ),
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


def generate_south_fork_american_cascading_scenario2_5d(
    selection: PlayerSelection | None = None,
    *,
    nx: int = 112,
    ny: int = 40,
    dx: float = 4.0,
    dy: float = 2.0,
    duration: float = 8.0,
) -> CascadingScenarioPackage2_5D:
    """Generate a South Fork American pool-drop cascading seed package."""

    chosen = selection or default_player_selections()[1]
    section = south_fork_american_section()
    centerline = south_fork_american_centerline_stations()
    indicators = extract_channel_indicators(centerline)
    rapid_candidates = identify_candidate_rapids(indicators)
    representative_width = float(np.mean([station.channel_width_m for station in centerline]))
    preset = adaptive_solver_parameters(chosen, representative_width_m=representative_width)
    median_discharge = _flow_band_by_name("median_runnable").discharge_cfs
    flow_discharge = _flow_band_by_name(chosen.flow_band).discharge_cfs
    flow_factor = max(0.35, flow_discharge / max(median_discharge, 1.0))
    cascade_params = CaliforniaPoolDropParameters2_5D(
        seed=_south_fork_cascading_seed(chosen),
        nx=nx,
        ny=ny,
        dx=dx,
        dy=dy,
        base_width=representative_width * (0.92 + 0.04 * min(flow_factor, 1.8)),
        base_depth=preset.initial_depth_m,
        inflow_speed=preset.downstream_velocity_mps,
        difficulty=_south_fork_cascading_difficulty(chosen, flow_factor),
        duration=duration,
    )
    base = generate_california_pool_drop_cascading_scenario2_5d(cascade_params)
    station_min = centerline[0].station_m
    station_max = centerline[-1].station_m
    reaches = _south_fork_cascading_reaches(
        base.reaches,
        base.scenario.grid,
        indicators,
        rapid_candidates,
        station_min,
        station_max,
    )
    drop_transitions = tuple(
        _south_fork_cascading_drop_transition(
            transition,
            base.scenario.grid,
            centerline,
            rapid_candidates,
            preset,
            chosen,
            station_min,
            station_max,
        )
        for transition in base.drop_transitions
    )
    metadata = ScenarioMetadata2_5D(
        scenario_id=f"{chosen.river_id}_{chosen.section_id}_{chosen.flow_band}_{chosen.difficulty}_cascading",
        scenario_type="real_world",
        seed=cascade_params.seed,
        generator="raftsim.real_world.cascading",
        generator_version="milestone_15_sfa_seed.v0",
        description=(
            "South Fork American seed cascading package with variable pool/drop reaches, "
            "source-station metadata, and rapid/drop transition annotations."
        ),
        river_id=section.river_id,
        section_id=section.section_id,
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
            "base_generator": "raftsim.cascading.generate_california_pool_drop_cascading_scenario2_5d",
            "rapid_candidate_count": len(rapid_candidates),
            "reach_sequence": "pool,tongue,drop,wave_train,eddy_recovery,boulder_garden,pool",
            "flow_preset_confidence": preset.confidence_score,
        },
    )
    boundaries = (
        BoundaryCondition2_5D(
            "west",
            "inflow",
            depth=preset.initial_depth_m,
            velocity=(preset.downstream_velocity_mps, 0.0),
            metadata={"flow_band": chosen.flow_band, "discharge_m3s": preset.boundary_inflow_m3s},
        ),
        BoundaryCondition2_5D(
            "east",
            "outflow",
            stage=preset.initial_depth_m + preset.outflow_stage_bias_m,
            metadata={"flow_band": chosen.flow_band},
        ),
        BoundaryCondition2_5D("south", "bank"),
        BoundaryCondition2_5D("north", "bank"),
    )
    source_features = _features_from_rapid_candidates(
        rapid_candidates,
        base.scenario.grid,
        station_min,
        station_max,
        preset,
    )
    scenario = replace(
        base.scenario,
        metadata=metadata,
        boundaries=boundaries,
        features=(*base.scenario.features, *source_features),
        raft=RaftParameters2_5D(drag_coefficient=1.25 * preset.raft_drag_coefficient_scale),
        roughness=preset.roughness_manning_n,
    )
    return CascadingScenarioPackage2_5D(
        scenario=scenario,
        reaches=reaches,
        drop_transitions=drop_transitions,
        pool_controls=base.pool_controls,
        reach_local_grids=base.reach_local_grids,
        reach_id_grid=base.reach_id_grid,
        drop_transition_id_grid=base.drop_transition_id_grid,
    )


def generate_south_fork_american_cascading_seed_scenarios(
    *,
    nx: int = 112,
    ny: int = 40,
    dx: float = 4.0,
    dy: float = 2.0,
    duration: float = 8.0,
) -> tuple[CascadingScenarioPackage2_5D, ...]:
    """Generate low, median, and high runnable South Fork cascading seed packages."""

    return tuple(
        generate_south_fork_american_cascading_scenario2_5d(
            selection,
            nx=nx,
            ny=ny,
            dx=dx,
            dy=dy,
            duration=duration,
        )
        for selection in default_player_selections()
    )


def write_real_world_seed_package(directory: str | Path) -> Path:
    """Write manifest, review data, flow presets, and a shared scenario package."""

    output_dir = Path(directory)
    data_dir = output_dir / "south_fork_american_chili_bar"
    scenario_dir = data_dir / "scenario"
    data_dir.mkdir(parents=True, exist_ok=True)
    package = build_real_world_corridor_package()
    inventory = build_candidate_river_inventory_package()
    _write_json(output_dir / CANDIDATE_RIVER_INVENTORY_FILE, inventory.to_json_dict())
    _write_json(output_dir / "candidate_rivers.json", {"sections": [section.to_json_dict() for section in default_candidate_river_inventory()]})
    _write_json(output_dir / "source_catalog.json", {"sources": [source.to_json_dict() for source in default_source_catalog()]})
    _write_json(output_dir / "rapid_review_labels.json", {"labels": [label.to_json_dict() for label in default_manual_rapid_review_labels()]})
    _write_json(output_dir / "player_selection_model.json", build_player_selection_model())
    _write_json(output_dir / PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE, build_production_environment_gap_register())
    _write_json(data_dir / SOURCE_MANIFEST_FILE, package.source_manifest)
    _write_json(data_dir / "river_course.json", package.to_json_dict())
    _write_json(data_dir / COURSE_ELEVATION_EXTRACTION_FILE, build_course_elevation_extraction(package).to_json_dict())
    _write_json(
        data_dir / RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
        build_rapid_review_flow_difficulty_mapping(package).to_json_dict(),
    )
    _write_json(data_dir / "flow_presets.json", {"flow_bands": [band.to_json_dict() for band in package.flow_bands]})
    _write_json(data_dir / "rapid_candidates.geojson", _rapid_candidates_geojson(package.rapid_candidates, package.indicators))
    _write_json(data_dir / RAPID_REVIEW_EDITOR_WORKFLOW_FILE, build_rapid_review_editor_workflow(package).to_json_dict())
    _write_json(data_dir / "corridor_package_manifest.json", _corridor_manifest(package))
    _write_json(data_dir / SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE, build_south_fork_access_publication_review())
    _write_json(data_dir / SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE, build_south_fork_production_import_pilot(package.section))
    _write_json(
        data_dir / SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE,
        build_south_fork_production_source_gate_review(package.section),
    )
    generate_real_world_scenario2_5d().write_package(scenario_dir)
    cascading_dir = data_dir / "cascading_scenarios"
    for cascading_package in generate_south_fork_american_cascading_seed_scenarios():
        cascading_scenario_dir = cascading_package.write_package(cascading_dir / cascading_package.scenario.metadata.scenario_id)
        write_unreal_cascading_corridor_metadata(cascading_package, cascading_scenario_dir / "unreal_corridor_metadata")
    return data_dir


def _candidate_section_source_manifest_link(
    section: CandidateRiverSection,
    primary: CandidateRiverSection,
) -> dict[str, object]:
    is_primary = section.river_id == primary.river_id and section.section_id == primary.section_id
    is_colorado_rowing = (
        section.river_id == "colorado_grand_canyon_rowing"
        and section.section_id == "lees_ferry_to_diamond_creek"
    )
    manifest_path = None
    manifest_id = None
    required_before_generation = "Draft a source manifest before generating solver or Unreal packages."
    status = "planned"
    if is_primary:
        manifest_path = f"south_fork_american_chili_bar/{SOURCE_MANIFEST_FILE}"
        manifest_id = f"{section.river_id}.{section.section_id}.source_manifest.v0"
        required_before_generation = "Use the drafted source manifest for the seed South Fork package."
        status = "drafted"
    elif is_colorado_rowing:
        manifest_path = "colorado_river_grand_canyon_rowing/source_manifest.json"
        manifest_id = "colorado_river.grand_canyon_lees_ferry_to_diamond_creek_rowing.source_manifest.v0"
        required_before_generation = "Use the Milestone 21 Colorado rowing draft source manifest before generating solver or Unreal packages."
        status = "drafted"
    return {
        "river_id": section.river_id,
        "section_id": section.section_id,
        "source_manifest_status": status,
        "source_manifest_path": manifest_path,
        "source_manifest_id": manifest_id,
        "required_before_generation": required_before_generation,
    }


def _rapid_review_difficulty_presets() -> tuple[dict[str, object], ...]:
    return (
        {
            "difficulty": "beginner",
            "feature_gain_scale": 0.72,
            "crew_timing_window": "wide",
            "gameplay_intent": "Training-oriented lines with clearer recovery, lower flip likelihood, and forgiving raft response.",
            "review_focus": [
                "recovery_pools",
                "clear_tongues",
                "visible_shallow_hazards",
                "access_and_portage_context",
            ],
            "expected_outcome_bias": ["flush", "recover", "guided_avoidance"],
        },
        {
            "difficulty": "intermediate",
            "feature_gain_scale": 1.0,
            "crew_timing_window": "normal",
            "gameplay_intent": "Default commercial-style run with useful holes, waves, laterals, eddies, and recoverable mistakes.",
            "review_focus": [
                "wave_trains",
                "sticky_holes_at_reviewed_flows",
                "eddy_line_choices",
                "boulder_avoidance",
            ],
            "expected_outcome_bias": ["clean_line", "surf", "flush", "brief_pin"],
        },
        {
            "difficulty": "advanced",
            "feature_gain_scale": 1.18,
            "crew_timing_window": "tight",
            "gameplay_intent": "Stronger hydraulics and consequences that require line choice, bracing, and high-side timing.",
            "review_focus": [
                "lateral_hits",
                "keeper_holes",
                "pin_release_windows",
                "crew_weight_distribution",
            ],
            "expected_outcome_bias": ["surf", "pin", "release", "flip_if_mishandled"],
        },
        {
            "difficulty": "expert",
            "feature_gain_scale": 1.35,
            "crew_timing_window": "very_tight",
            "gameplay_intent": "High-consequence tuning where poor angle, missed brace, or late high-side can produce pins or flips.",
            "review_focus": [
                "high_consequence_holes",
                "rock_push_and_damping",
                "flip_thresholds",
                "rescue_or_recovery_windows",
            ],
            "expected_outcome_bias": ["pin", "release", "flip", "swimmer_recovery"],
        },
    )


def _rapid_review_label_flow_response(
    label: RapidReviewLabel,
    flow_bands: tuple[FlowBand, ...],
) -> dict[str, object]:
    return {
        "label": label.label,
        "category": label.category,
        "solver_tags": list(label.solver_tags),
        "requires_human_review": label.requires_human_review,
        "tuning_parameters": _rapid_review_label_tuning_parameters(label.label),
        "expected_raft_outcomes": _rapid_review_label_outcomes(label.label),
        "flow_responses": [
            {
                "flow_band": band.flow_band,
                "season": band.season,
                "discharge_cfs": band.discharge_cfs,
                "activation_scale": _rapid_review_label_flow_scale(label.label, band.flow_band),
                "review_priority": _rapid_review_label_review_priority(label, band.flow_band),
                "expected_behavior": _rapid_review_label_flow_note(label.label, band.flow_band),
            }
            for band in flow_bands
        ],
    }


def _rapid_review_parameter_matrix(
    section: CandidateRiverSection,
    flow_bands: tuple[FlowBand, ...],
    representative_width_m: float,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for band in flow_bands:
        for difficulty in DIFFICULTY_PRESETS:
            selection = PlayerSelection(
                region=section.region,
                river_id=section.river_id,
                section_id=section.section_id,
                season=band.season,
                flow_band=band.flow_band,
                difficulty=difficulty,
                raft_setup="standard_14ft_paddle_raft",
            )
            preset = adaptive_solver_parameters(
                selection,
                flow_bands=flow_bands,
                representative_width_m=representative_width_m,
            )
            rows.append(
                {
                    "season": band.season,
                    "flow_band": band.flow_band,
                    "difficulty": difficulty,
                    "discharge_cfs": band.discharge_cfs,
                    "discharge_m3s": band.discharge_m3s,
                    "flow_percentile_mid": float(np.mean(band.percentile_range)),
                    "parameters": {
                        "boundary_inflow_m3s": preset.boundary_inflow_m3s,
                        "initial_depth_m": preset.initial_depth_m,
                        "downstream_velocity_mps": preset.downstream_velocity_mps,
                        "downstream_momentum_scale": preset.downstream_momentum_scale,
                        "roughness_manning_n": preset.roughness_manning_n,
                        "aeration_turbulence_scale": preset.aeration_turbulence_scale,
                        "hole_retention_strength": preset.hole_retention_strength,
                        "wave_train_strength": preset.wave_train_strength,
                        "eddy_line_shear": preset.eddy_line_shear,
                        "boil_strength": preset.boil_strength,
                        "shallow_hazard_threshold_m": preset.shallow_hazard_threshold_m,
                        "hazard_activation_scale": preset.hazard_activation_scale,
                        "raft_drag_coefficient_scale": preset.raft_drag_coefficient_scale,
                        "paddle_catch_scale": preset.paddle_catch_scale,
                        "damping_scale": preset.damping_scale,
                    },
                    "review_controls": {
                        "feature_gain_scale": _difficulty_feature_gain_scale(difficulty),
                        "crew_timing_window": _difficulty_crew_timing_window(difficulty),
                        "must_record_expected_outcomes": True,
                        "must_validate_conservation_before_forcing": True,
                    },
                }
            )
    return tuple(rows)


def _rapid_review_label_flow_scale(label: str, flow_band: str) -> float:
    default = {
        "low_runnable": 0.75,
        "median_runnable": 1.0,
        "high_runnable": 1.15,
    }
    curves = {
        "pool": {"low_runnable": 1.05, "median_runnable": 1.0, "high_runnable": 0.78},
        "riffle": {"low_runnable": 1.15, "median_runnable": 0.95, "high_runnable": 0.70},
        "wave_train": {"low_runnable": 0.58, "median_runnable": 1.0, "high_runnable": 1.35},
        "hole": {"low_runnable": 0.35, "median_runnable": 1.0, "high_runnable": 0.65},
        "ledge": {"low_runnable": 0.72, "median_runnable": 1.0, "high_runnable": 1.10},
        "lateral": {"low_runnable": 0.55, "median_runnable": 1.0, "high_runnable": 1.30},
        "eddy": {"low_runnable": 1.05, "median_runnable": 1.0, "high_runnable": 0.82},
        "eddy_line": {"low_runnable": 0.70, "median_runnable": 1.0, "high_runnable": 1.25},
        "strainer": {"low_runnable": 1.15, "median_runnable": 1.0, "high_runnable": 1.30},
        "portage": {"low_runnable": 1.0, "median_runnable": 1.0, "high_runnable": 1.25},
        "access_point": {"low_runnable": 1.0, "median_runnable": 1.0, "high_runnable": 0.90},
        "boulder_garden": {"low_runnable": 1.25, "median_runnable": 1.0, "high_runnable": 0.72},
        "constriction": {"low_runnable": 0.78, "median_runnable": 1.0, "high_runnable": 1.22},
    }
    return curves.get(label, default).get(flow_band, 1.0)


def _rapid_review_label_flow_note(label: str, flow_band: str) -> str:
    notes = {
        "hole": {
            "low_runnable": "Usually a shallow drop or rough tongue; keep retention low and verify it is not a fake keeper.",
            "median_runnable": "Primary sticky-hole review band; tune surf/flush/pin/release outcomes against guide and footage evidence.",
            "high_runnable": "May become aerated or wash out; reduce retention unless reviewed evidence shows a keeper at this flow.",
        },
        "boulder_garden": {
            "low_runnable": "Rocks expose and pin risk rises; tune rock push, damping, shallow shelves, and crew high-side timing.",
            "median_runnable": "Default line-choice and collision review band.",
            "high_runnable": "More rocks cover over; emphasize powerful laterals, hidden impacts, and faster recovery windows.",
        },
        "wave_train": {
            "low_runnable": "Small waves or riffles; keep amplitude modest.",
            "median_runnable": "Default standing-wave spacing and raft timing review band.",
            "high_runnable": "Larger wave train with stronger momentum, splash, aeration, and flip consequences.",
        },
        "lateral": {
            "low_runnable": "Often weak or rock-controlled; verify it is not just bank roughness.",
            "median_runnable": "Default cross-current hit and recovery review band.",
            "high_runnable": "Strong lateral push; tune angle, brace timing, and flip-risk escalation.",
        },
        "eddy_line": {
            "low_runnable": "Lower shear, useful training target.",
            "median_runnable": "Default ferry, peel-out, and recovery review band.",
            "high_runnable": "Sharper shear with stronger catch/flip consequences.",
        },
    }
    fallback = {
        "low_runnable": "Low-flow review should emphasize exposed geometry, slower recovery, and shallow hazards.",
        "median_runnable": "Median-flow review is the default tuning baseline.",
        "high_runnable": "High-flow review should emphasize stronger momentum, faster decisions, and washed-out or covered features.",
    }
    return notes.get(label, fallback).get(flow_band, fallback.get(flow_band, "Review against the selected flow band."))


def _rapid_review_label_review_priority(label: RapidReviewLabel, flow_band: str) -> str:
    scale = _rapid_review_label_flow_scale(label.label, flow_band)
    if label.category == "hazard" or scale >= 1.18:
        return "high"
    if scale >= 0.80 or label.requires_human_review:
        return "medium"
    return "low"


def _rapid_review_label_tuning_parameters(label: str) -> list[str]:
    mapping = {
        "pool": ["damping_scale", "outflow_stage_bias_m"],
        "riffle": ["roughness_manning_n", "shallow_hazard_threshold_m"],
        "wave_train": ["wave_train_strength", "aeration_turbulence_scale"],
        "hole": ["hole_retention_strength", "boil_strength", "hazard_activation_scale"],
        "ledge": ["hazard_activation_scale", "wave_train_strength", "boil_strength"],
        "lateral": ["eddy_line_shear", "downstream_momentum_scale", "hazard_activation_scale"],
        "eddy": ["damping_scale", "eddy_line_shear"],
        "eddy_line": ["eddy_line_shear", "damping_scale", "raft_drag_coefficient_scale"],
        "strainer": ["hazard_activation_scale", "raft_drag_coefficient_scale"],
        "portage": ["hazard_activation_scale"],
        "access_point": ["confidence_score"],
        "boulder_garden": ["shallow_hazard_threshold_m", "hazard_activation_scale", "damping_scale"],
        "constriction": ["downstream_momentum_scale", "wave_train_strength", "eddy_line_shear"],
    }
    return mapping.get(label, ["hazard_activation_scale"])


def _rapid_review_label_outcomes(label: str) -> list[str]:
    mapping = {
        "pool": ["recover", "regroup", "set_safety"],
        "riffle": ["clean_line", "shallow_scrape"],
        "wave_train": ["clean_line", "splash", "brief_surf", "flip_if_sideways"],
        "hole": ["surf", "flush", "pin", "release", "flip_if_mishandled"],
        "ledge": ["boof_or_drop", "lateral_hit", "hole_or_wave_train"],
        "lateral": ["angle_correction", "brace", "flip_if_mishandled"],
        "eddy": ["catch_eddy", "recover", "missed_eddy"],
        "eddy_line": ["peel_out", "ferry", "spin_or_flip_if_mishandled"],
        "strainer": ["avoid", "portage", "failed_line_hazard"],
        "portage": ["scout", "avoid", "walk_around"],
        "access_point": ["put_in", "take_out", "scout"],
        "boulder_garden": ["clean_line", "rock_bump", "pin", "release", "crew_overboard"],
        "constriction": ["accelerate", "wave_train", "lateral_hit", "hole_if_controlled"],
    }
    return mapping.get(label, ["review_required"])


def _difficulty_feature_gain_scale(difficulty: DifficultyPreset) -> float:
    return {
        "beginner": 0.72,
        "intermediate": 1.0,
        "advanced": 1.18,
        "expert": 1.35,
    }[difficulty]


def _difficulty_crew_timing_window(difficulty: DifficultyPreset) -> str:
    return {
        "beginner": "wide",
        "intermediate": "normal",
        "advanced": "tight",
        "expert": "very_tight",
    }[difficulty]


def _rapid_review_layers() -> tuple[RapidReviewLayer, ...]:
    return (
        RapidReviewLayer(
            "dem_lidar",
            "DEM/Lidar Terrain",
            "raster",
            "terrain/3dep_dem_tiles",
            ("usgs_3dep", "usgs_tnm"),
            "Elevation, slope, bank breaks, boulder shadows, and terrain confidence backdrop.",
        ),
        RapidReviewLayer(
            "aerial_satellite_imagery",
            "Aerial/Satellite Imagery",
            "raster",
            "imagery/naip_tiles",
            ("usda_naip",),
            "Visible channel, banks, boulders, foam texture, water masks, and access context.",
        ),
        RapidReviewLayer(
            "flowlines",
            "Flowlines And Centerline",
            "vector",
            SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
            ("usgs_3dhp_nhd", "osm"),
            "Derived NHD mainstem candidate, source flowlines, future reviewed centerline, stationing, flow direction, and named/access hydrography context.",
        ),
        RapidReviewLayer(
            "cross_sections",
            "Cross Sections",
            "vector",
            SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
            ("usgs_3dep", "usgs_3dhp_nhd"),
            "Review-gated cross-section seed lines, future bank offsets, width, slope, constriction, and solver section sampling.",
        ),
        RapidReviewLayer(
            "gauge_history",
            "Gauge History",
            "table",
            "hydrology/usgs_11445500_daily_discharge.json",
            ("usgs_nwis", "noaa_nwps_nwm", "usgs_streamstats"),
            "Flow bands, discharge/stage context, season notes, and validation-flow selection.",
        ),
        RapidReviewLayer(
            "flow_difficulty_mapping",
            "Flow/Difficulty Mapping",
            "table",
            RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
            ("usgs_nwis", "guide_references"),
            "Label-specific flow response, difficulty controls, solver parameters, and expected raft outcomes.",
        ),
        RapidReviewLayer(
            "source_manifest",
            "Source Manifest",
            "manifest",
            SOURCE_MANIFEST_FILE,
            ("usgs_3dep", "usgs_3dhp_nhd", "usda_naip", "usgs_nwis", "guide_references"),
            "Provenance, rights, artifact paths, confidence, and source-status review.",
        ),
        RapidReviewLayer(
            "candidate_tags",
            "Candidate Tags",
            "annotation",
            "review/rapid_candidates.geojson",
            ("guide_references",),
            "Automated slope/constriction/roughness/imagery tags and human review labels.",
        ),
        RapidReviewLayer(
            "guide_notes",
            "Guide Notes",
            "reference",
            "review/guide_reference_index.json",
            ("guide_references", "field_media"),
            "Guide feedback, footage pointers, scout notes, expected outcomes, and review status.",
        ),
        RapidReviewLayer(
            "validation_annotations",
            "Validation Annotations",
            "annotation",
            "review/river_validation_annotations.geojson",
            ("guide_references", "field_media"),
            "Accepted pins, spans, polygons, raft lines, expected outcomes, and rights metadata.",
            visible_by_default=False,
            required_for_review=False,
        ),
    )


def _rapid_review_panels() -> tuple[RapidReviewPanel, ...]:
    return (
        RapidReviewPanel(
            "one_view_map",
            "Map Review",
            "map",
            (
                "dem_lidar",
                "aerial_satellite_imagery",
                "flowlines",
                "cross_sections",
                "candidate_tags",
                "guide_notes",
                "validation_annotations",
            ),
            "Primary rapid-design view with terrain, imagery, hydrography, candidates, and evidence overlays.",
        ),
        RapidReviewPanel(
            "station_profile",
            "Station Profile",
            "profile",
            ("dem_lidar", "flowlines", "cross_sections", "candidate_tags"),
            "Longitudinal elevation/gradient profile plus selected cross-section context.",
        ),
        RapidReviewPanel(
            "flow_and_sources",
            "Flow And Sources",
            "hydrology",
            ("gauge_history", "flow_difficulty_mapping", "source_manifest", "guide_notes"),
            "Gauge bands, source provenance, rights, and confidence for the selected candidate.",
        ),
        RapidReviewPanel(
            "annotation_editor",
            "Annotation Editor",
            "annotation_form",
            ("candidate_tags", "guide_notes", "validation_annotations"),
            "Manual edits for labels, boundaries, raft lines, expected outcomes, confidence, and rights.",
            editable_fields=(
                "review_labels",
                "station_range_m",
                "geometry",
                "expected_outcome",
                "guide_feedback",
                "flow_context",
                "rights_provenance",
                "confidence",
            ),
        ),
    )


def _rapid_review_item(package: RealWorldCorridorPackage, candidate: RapidCandidate) -> RapidReviewItem:
    nearest_indicator = min(package.indicators, key=lambda indicator: abs(indicator.station_m - candidate.peak_station_m))
    return RapidReviewItem(
        review_item_id=f"{candidate.rapid_id}_review",
        rapid_id=candidate.rapid_id,
        station_range_m=(candidate.start_station_m, candidate.end_station_m),
        peak_station_m=candidate.peak_station_m,
        map_focus_wgs84=(nearest_indicator.lon, nearest_indicator.lat),
        candidate_tags=candidate.suggested_labels,
        signals=candidate.signals,
        confidence=candidate.confidence,
        evidence_refs=_rapid_review_evidence_refs(candidate),
        cross_section_summary=_rapid_review_cross_section_summary(nearest_indicator),
        gauge_context=_rapid_review_gauge_context(package),
        guide_notes=_rapid_review_guide_notes(candidate),
        required_actions=(
            "Confirm or edit rapid boundary station range.",
            "Classify water features and hazards from the label catalog.",
            "Attach guide feedback, footage/timecode references, and rights/provenance before acceptance.",
            "Record expected raft outcomes such as surf, flush, pin, release, flip, or clean line.",
            "Mark whether the annotation feeds gameplay tuning, physics validation, visual/audio fidelity, or all three.",
        ),
        editable_fields=(
            "review_labels",
            "station_range_m",
            "point_span_polygon_geometry",
            "raft_line_geometry",
            "footage_timecodes",
            "aerial_imagery_date_tile",
            "guide_feedback",
            "expected_outcome",
            "rights_provenance",
            "confidence",
        ),
    )


def _rapid_review_evidence_refs(candidate: RapidCandidate) -> dict[str, object]:
    return {
        "dem_lidar": {
            "layer_id": "dem_lidar",
            "artifacts": ["terrain/3dep_dem_tiles", "terrain/solver_bed_grid.npy"],
            "source_ids": ["usgs_3dep", "usgs_tnm"],
        },
        "aerial_satellite_imagery": {
            "layer_id": "aerial_satellite_imagery",
            "artifacts": ["imagery/naip_tiles", "imagery/water_mask.tif", "imagery/foam_texture_mask.tif"],
            "source_ids": ["usda_naip"],
        },
        "flowlines": {
            "layer_id": "flowlines",
            "artifacts": [
                SOUTH_FORK_NHD_HU8_MANIFEST_FILE,
                SOUTH_FORK_NHD_HU8_FLOWLINE_EXTRACT_FILE,
                SOUTH_FORK_NHD_HU8_SUPPORT_EXTRACT_FILE,
                SOUTH_FORK_NHD_MAINSTEM_MANIFEST_FILE,
                SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
                SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
                "hydrography/centerline.geojson",
                "hydrography/banks.geojson",
            ],
            "source_ids": ["usgs_3dhp_nhd", "osm"],
        },
        "cross_sections": {
            "layer_id": "cross_sections",
            "artifacts": [
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
                SOUTH_FORK_NHD_CROSS_SECTION_SEED_FILE,
                SOUTH_FORK_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
                "hydrography/cross_sections.geojson",
            ],
            "source_ids": ["usgs_3dep", "usgs_3dhp_nhd"],
        },
        "gauge_history": {
            "layer_id": "gauge_history",
            "artifacts": [
                "hydrology/usgs_11445500_daily_discharge.json",
                "hydrology/usgs_11445500_instantaneous_discharge_stage_p30d_diagnostic.json",
                "hydrology/south_fork_modern_flow_source_selection.json",
                "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json",
                SOUTH_FORK_CDEC_TERMS_FLAGS_REVIEW_FILE,
                SOUTH_FORK_CDEC_FLOW_CONTEXT_FILE,
                "hydrology/flow_presets.json",
            ],
            "source_ids": ["usgs_nwis", "cdec_cbr", "cdec_a25_powerhouse_context", "noaa_nwps_nwm", "usgs_streamstats"],
        },
        "flow_difficulty_mapping": {
            "layer_id": "flow_difficulty_mapping",
            "artifacts": [RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE],
            "source_ids": ["usgs_nwis", "guide_references"],
        },
        "source_manifest": {
            "layer_id": "source_manifest",
            "artifacts": [SOURCE_MANIFEST_FILE],
            "source_ids": ["source_manifest"],
        },
        "candidate_tags": {
            "layer_id": "candidate_tags",
            "artifacts": ["review/rapid_candidates.geojson"],
            "candidate_id": candidate.rapid_id,
            "tags": list(candidate.suggested_labels),
            "signals": list(candidate.signals),
        },
        "guide_notes": {
            "layer_id": "guide_notes",
            "artifacts": ["review/guide_reference_index.json", "review/rapid_review_labels.json"],
            "source_ids": ["guide_references", "field_media"],
        },
    }


def _rapid_review_cross_section_summary(indicator: ChannelIndicator) -> dict[str, float]:
    return {
        "station_m": indicator.station_m,
        "center_lon": indicator.lon,
        "center_lat": indicator.lat,
        "channel_width_m": indicator.channel_width_m,
        "left_bank_offset_m": indicator.left_bank_offset_m,
        "right_bank_offset_m": indicator.right_bank_offset_m,
        "gradient": indicator.gradient,
        "constriction_score": indicator.constriction_score,
        "roughness_score": indicator.roughness_score,
        "rapid_score": indicator.rapid_score,
    }


def _course_elevation_cross_section_prototype(
    package: RealWorldCorridorPackage,
    indicator: ChannelIndicator,
    index: int,
) -> dict[str, object]:
    overlapping = [
        candidate
        for candidate in package.rapid_candidates
        if candidate.start_station_m <= indicator.station_m <= candidate.end_station_m
    ]
    nearest = (
        min(
            package.rapid_candidates,
            key=lambda candidate: abs(candidate.peak_station_m - indicator.station_m),
        )
        if package.rapid_candidates
        else None
    )
    labels = sorted({label for candidate in overlapping for label in candidate.suggested_labels})
    return {
        "cross_section_id": f"course_section_{index:03d}",
        "station_m": indicator.station_m,
        "center_wgs84": {"lon": indicator.lon, "lat": indicator.lat},
        "local_axis": {
            "downstream_m": indicator.station_m,
            "left_m_positive": True,
            "right_m_negative": True,
        },
        "channel_width_m": indicator.channel_width_m,
        "bank_offsets_m": {
            "left": indicator.left_bank_offset_m,
            "right": indicator.right_bank_offset_m,
        },
        "elevation_m": indicator.elevation_m,
        "gradient": indicator.gradient,
        "constriction_score": indicator.constriction_score,
        "roughness_score": indicator.roughness_score,
        "rapid_score": indicator.rapid_score,
        "rapid_candidate_ids": [candidate.rapid_id for candidate in overlapping],
        "nearest_rapid_candidate_id": nearest.rapid_id if nearest is not None else None,
        "suggested_labels": labels,
        "signals": list(indicator.signals),
        "authoring_status": "prototype_requires_dem_lidar_bank_review",
    }


def _rapid_review_gauge_context(package: RealWorldCorridorPackage) -> dict[str, object]:
    return {
        "gauge_candidates": list(package.section.gauge_candidates),
        "default_flow_band": "median_runnable",
        "flow_bands": [
            {
                "flow_band": band.flow_band,
                "season": band.season,
                "discharge_cfs": band.discharge_cfs,
                "discharge_m3s": band.discharge_m3s,
                "runnable": band.runnable,
                "confidence": band.confidence,
            }
            for band in package.flow_bands
        ],
    }


def _rapid_review_guide_notes(candidate: RapidCandidate) -> tuple[str, ...]:
    notes = [
        "Human guide review pending; keep copyrighted guidebook text and third-party media out of the repo unless rights are explicit.",
    ]
    if "guide_note" in candidate.signals:
        notes.append("Seed guide-note signal is present near this candidate; reviewer must attach citation, flow context, and derived guidance.")
    if "access_point" in candidate.signals:
        notes.append("Access or scout context may be nearby; verify put-in/take-out, trail, road, and safety notes.")
    if candidate.confidence < 0.65:
        notes.append("Candidate confidence is still low enough that a reviewer should confirm boundaries and labels before solver tuning.")
    return tuple(notes)


def _south_fork_cascading_seed(selection: PlayerSelection) -> int:
    flow_seed = {
        "low_runnable": 101,
        "median_runnable": 202,
        "high_runnable": 303,
    }[selection.flow_band]
    difficulty_seed = {
        "beginner": 7,
        "intermediate": 13,
        "advanced": 19,
        "expert": 29,
    }[selection.difficulty]
    return 1500 + flow_seed + difficulty_seed


def _south_fork_cascading_difficulty(selection: PlayerSelection, flow_factor: float) -> float:
    base = {
        "beginner": 0.32,
        "intermediate": 0.54,
        "advanced": 0.74,
        "expert": 0.88,
    }[selection.difficulty]
    return _clamp01(base + 0.12 * (flow_factor - 1.0))


def _south_fork_cascading_reaches(
    reaches: tuple[ReachMetadata2_5D, ...],
    grid: GridSpec2_5D,
    indicators: tuple[ChannelIndicator, ...],
    rapid_candidates: tuple[RapidCandidate, ...],
    station_min: float,
    station_max: float,
) -> tuple[ReachMetadata2_5D, ...]:
    updated: list[ReachMetadata2_5D] = []
    for reach in reaches:
        source_start = _source_station_for_solver_station(grid, reach.station_start, station_min, station_max)
        source_end = _source_station_for_solver_station(grid, reach.station_end, station_min, station_max)
        source_mid = (source_start + source_end) * 0.5
        roughness = _interp_indicator_value(indicators, "roughness_score", source_mid)
        boulder_density = _interp_centerline_value(south_fork_american_centerline_stations(), "boulder_density", source_mid)
        overlapping_candidates = tuple(
            candidate.rapid_id
            for candidate in rapid_candidates
            if candidate.end_station_m >= source_start and candidate.start_station_m <= source_end
        )
        metadata = {
            **reach.metadata,
            "river_id": "american_south_fork",
            "section_id": "chili_bar_to_coloma",
            "source_station_start_m": source_start,
            "source_station_end_m": source_end,
            "source_gradient_start": _interp_indicator_value(indicators, "gradient", source_start),
            "source_gradient_end": _interp_indicator_value(indicators, "gradient", source_end),
            "source_channel_width_start_m": _interp_indicator_value(indicators, "channel_width_m", source_start),
            "source_channel_width_end_m": _interp_indicator_value(indicators, "channel_width_m", source_end),
            "source_roughness_score": roughness,
            "source_rapid_candidates": ",".join(overlapping_candidates),
        }
        updated.append(
            replace(
                reach,
                bed_roughness=max(reach.bed_roughness, 0.032 + 0.026 * roughness),
                boulder_density=max(reach.boulder_density, _clamp01(boulder_density)),
                confidence_score=min(reach.confidence_score, 0.60),
                metadata=metadata,
            )
        )
    return tuple(updated)


def _south_fork_cascading_drop_transition(
    transition: DropTransitionMetadata2_5D,
    grid: GridSpec2_5D,
    centerline: tuple[CenterlineStation, ...],
    rapid_candidates: tuple[RapidCandidate, ...],
    preset: SolverParameterPreset,
    selection: PlayerSelection,
    station_min: float,
    station_max: float,
) -> DropTransitionMetadata2_5D:
    source_crest = _source_station_for_solver_station(grid, transition.crest_station, station_min, station_max)
    nearest = min(rapid_candidates, key=lambda candidate: abs(candidate.peak_station_m - source_crest)) if rapid_candidates else None
    source_fall = 0.0
    rapid_id = ""
    candidate_tags: tuple[str, ...] = ()
    if nearest is not None:
        rapid_id = nearest.rapid_id
        candidate_tags = nearest.suggested_labels
        fallback_window = max(120.0, (station_max - station_min) * 0.035)
        fall_start = max(station_min, min(nearest.start_station_m, nearest.peak_station_m - fallback_window))
        fall_end = min(station_max, max(nearest.end_station_m, nearest.peak_station_m + fallback_window))
        upstream_elevation = _interp_centerline_value(centerline, "elevation_m", fall_start)
        downstream_elevation = _interp_centerline_value(centerline, "elevation_m", fall_end)
        source_fall = max(0.0, upstream_elevation - downstream_elevation)
    hazard_tags = tuple(sorted(set((*transition.hazard_tags, *candidate_tags))))
    metadata = {
        **transition.metadata,
        "river_id": selection.river_id,
        "section_id": selection.section_id,
        "flow_band": selection.flow_band,
        "difficulty": selection.difficulty,
        "source_rapid_id": rapid_id,
        "source_crest_station_m": source_crest,
        "source_elevation_fall_m": source_fall,
        "gauge_source": "USGS 11445500 South Fork American River near Lotus, CA",
    }
    return replace(
        transition,
        recirculation_risk=max(transition.recirculation_risk, min(1.0, preset.hole_retention_strength * 0.46)),
        aeration_proxy=max(transition.aeration_proxy, min(1.0, preset.aeration_turbulence_scale * 0.42)),
        turbulence_proxy=max(transition.turbulence_proxy, min(1.0, preset.aeration_turbulence_scale * 0.48)),
        hazard_tags=hazard_tags,
        metadata=metadata,
    )


def _source_station_for_solver_station(
    grid: GridSpec2_5D,
    solver_station: float,
    station_min: float,
    station_max: float,
) -> float:
    solver_start = float(grid.x_coordinates()[0])
    solver_end = float(grid.x_coordinates()[-1])
    fraction = (solver_station - solver_start) / max(solver_end - solver_start, 1.0)
    return station_min + _clamp01(fraction) * (station_max - station_min)


def _interp_indicator_value(indicators: tuple[ChannelIndicator, ...], field_name: str, station_m: float) -> float:
    stations = np.asarray([indicator.station_m for indicator in indicators], dtype=np.float64)
    values = np.asarray([float(getattr(indicator, field_name)) for indicator in indicators], dtype=np.float64)
    return float(np.interp(station_m, stations, values))


def _interp_centerline_value(centerline: tuple[CenterlineStation, ...], field_name: str, station_m: float) -> float:
    stations = np.asarray([station.station_m for station in centerline], dtype=np.float64)
    values = np.asarray([float(getattr(station, field_name)) for station in centerline], dtype=np.float64)
    return float(np.interp(station_m, stations, values))


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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
