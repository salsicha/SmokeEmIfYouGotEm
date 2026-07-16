"""Build South Fork A1 full-reach per-window source manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_corridor_windows import (
    FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_window_source_pulls import (
    FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
)
from .south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
    write_south_fork_a1_window_source_pull_status,
)


FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_manifest_index.json"
)

_USGS_3DEP_RIGHTS = {
    "rights": "U.S. Public Domain; credit U.S. Geological Survey",
    "rights_url": (
        "https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map"
    ),
    "attribution": "U.S. Geological Survey 3D Elevation Program",
}
_USDA_NAIP_RIGHTS = {
    "rights": "U.S. Public Domain; credit USDA/FSA/APFO NAIP",
    "rights_url": (
        "https://agdatacommons.nal.usda.gov/articles/dataset/"
        "NAIP_Digital_Ortho_Photo_Image_Geospatial_Data_Presentation_Form_remote-sensing_image/"
        "24664908"
    ),
    "attribution": "USDA/FSA/APFO National Agriculture Imagery Program",
}


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _window_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["window_id"]: item for item in items}


def _pixel_resolution_m(bounds_epsg3857: list[float], size_px: list[int]) -> list[float]:
    width_m = float(bounds_epsg3857[2]) - float(bounds_epsg3857[0])
    height_m = float(bounds_epsg3857[3]) - float(bounds_epsg3857[1])
    return [
        round(width_m / max(int(size_px[0]), 1), 6),
        round(height_m / max(int(size_px[1]), 1), 6),
    ]


def _source_artifact(
    *,
    record: dict[str, Any],
    export: dict[str, Any],
    rights: dict[str, str],
    bounds_epsg3857: list[float],
    source_kind: str,
) -> dict[str, Any]:
    if not record["present"]:
        raise ValueError(f"Missing source file for {source_kind}: {record['relative_path']}")
    return {
        "source_kind": source_kind,
        "path": record["relative_path"],
        "sha256": record["sha256"],
        "byte_count": record["byte_count"],
        "dimensions": export["size_px"],
        "pixel_resolution_m_approx": _pixel_resolution_m(bounds_epsg3857, export["size_px"]),
        "coordinate_reference_system": "EPSG:3857 Web Mercator export grid",
        "source_bounds_epsg3857": bounds_epsg3857,
        "service_url": export["service_url"],
        "official_export_url": export["query_url"],
        "format": export["format"],
        **rights,
    }


def _build_window_manifest(
    *,
    plan_window: dict[str, Any],
    corridor_window: dict[str, Any],
    status_window: dict[str, Any],
) -> dict[str, Any]:
    window_id = plan_window["window_id"]
    bounds_epsg3857 = plan_window["bounds_epsg3857_buffered"]
    terrain = _source_artifact(
        record=status_window["terrain_dem"],
        export=plan_window["terrain_3dep_export"],
        rights=_USGS_3DEP_RIGHTS,
        bounds_epsg3857=bounds_epsg3857,
        source_kind="terrain_dem",
    )
    aerial = _source_artifact(
        record=status_window["aerial_imagery"],
        export=plan_window["aerial_naip_export"],
        rights=_USDA_NAIP_RIGHTS,
        bounds_epsg3857=bounds_epsg3857,
        source_kind="aerial_imagery",
    )
    return {
        "schema": "raftsim.south_fork.a1_full_reach_window_source_manifest.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": "south_fork_american_chili_bar",
        "window_id": window_id,
        "display_name": plan_window["display_name"],
        "status": "source_files_attached_derivatives_pending_review_gated",
        "production_promoted": False,
        "station_range_m": {
            "start": plan_window["station_start_m"],
            "end": plan_window["station_end_m"],
            "length": round(plan_window["station_end_m"] - plan_window["station_start_m"], 6),
        },
        "bounds": {
            "wgs84": plan_window["bounds_wgs84"],
            "epsg3857_buffered": bounds_epsg3857,
            "buffer_m": plan_window["buffer_m"],
        },
        "source_artifacts": {
            "dem": terrain,
            "aerial": aerial,
        },
        "source_policy": {
            "authority": "official_source_files_for_review_not_final_game_geometry",
            "download_review": (
                "Source files were pulled through the bounded A1 executor from the "
                "recorded official URLs and are hash-locked here for review."
            ),
            "redistribution_basis": "U.S. public-domain government source files with required attribution.",
            "do_not_promote_from_source_files_alone": True,
        },
        "derivative_targets": {
            "heightfield": (
                "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                f"full_reach_windows/{window_id}/derived/heightfield_2017.png"
            ),
            "hillshade": (
                "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                f"full_reach_windows/{window_id}/derived/hillshade_2048.png"
            ),
            "naip_centerline_preview": (
                "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                f"full_reach_windows/{window_id}/derived/naip_centerline_preview_2048.png"
            ),
            "window_stitched_edge_report": (
                "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                f"full_reach_windows/{window_id}/review/stitched_edge_report.json"
            ),
        },
        "window_requirements": {
            "rapid_names": corridor_window["rapid_names"],
            "rapid_count": corridor_window["rapid_count"],
            "required_source_classes": corridor_window["required_source_classes"],
            "requires_bank_cross_section_interpretation": True,
            "requires_stitched_validation_preview": True,
        },
        "promotion_gate": {
            "can_generate_window_derivatives": True,
            "can_enter_stitched_validation_review": True,
            "can_import_unreal_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
            "exit_criteria": [
                "Generate review derivatives from the hash-locked DEM and NAIP source files.",
                "Validate seams against adjacent window derivatives and the whole-window route.",
                "Attach bank/cross-section interpretation and guide/geospatial review.",
                "Resolve exact downstream anchor before final cropping or Unreal import.",
            ],
        },
    }


def build_south_fork_a1_full_reach_window_source_manifests(
    repo_root: Path,
) -> dict[str, Any]:
    """Build all per-window source manifests and a deterministic index."""

    repo_root = repo_root.resolve()
    pull_plan = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH)
    corridor_manifest = _load_json(repo_root, FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH)
    status = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH)
    corridor_by_id = _window_by_id(corridor_manifest["windows"])
    status_by_id = _window_by_id(status["windows"])
    manifests = [
        _build_window_manifest(
            plan_window=window,
            corridor_window=corridor_by_id[window["window_id"]],
            status_window=status_by_id[window["window_id"]],
        )
        for window in pull_plan["windows"]
    ]
    return {
        "schema": "raftsim.south_fork.a1_full_reach_window_source_manifest_index.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": pull_plan["river_id"],
        "status": "per_window_source_manifests_generated_stitched_validation_pending",
        "production_promoted": False,
        "inputs": {
            "corridor_window_manifest": FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
            "source_pull_plan": FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
            "source_pull_status": FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
        },
        "summary": {
            "window_count": len(manifests),
            "source_manifest_count": len(manifests),
            "all_sources_present": all(
                manifest["source_artifacts"]["dem"]["sha256"]
                and manifest["source_artifacts"]["aerial"]["sha256"]
                for manifest in manifests
            ),
            "can_enter_stitched_validation_review": True,
            "can_promote_full_reach_corridor": False,
        },
        "window_manifests": [
            {
                "window_id": manifest["window_id"],
                "display_name": manifest["display_name"],
                "manifest_path": (
                    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                    f"full_reach_windows/{manifest['window_id']}/manifest.json"
                ),
                "terrain_sha256": manifest["source_artifacts"]["dem"]["sha256"],
                "aerial_sha256": manifest["source_artifacts"]["aerial"]["sha256"],
                "can_enter_stitched_validation_review": manifest["promotion_gate"][
                    "can_enter_stitched_validation_review"
                ],
                "production_promoted": False,
            }
            for manifest in manifests
        ],
        "promotion_gate": {
            "can_promote_full_reach_corridor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Generate per-window derivatives and seam reports from these source manifests.",
                "Build stitched whole-window validation previews across all six windows.",
                "Resolve exact downstream anchor before final crop, Unreal import, or rapid binding.",
            ],
        },
        "manifests": manifests,
    }


def write_south_fork_a1_full_reach_window_source_manifests(repo_root: Path) -> list[Path]:
    payload = build_south_fork_a1_full_reach_window_source_manifests(repo_root)
    repo_root = repo_root.resolve()
    written: list[Path] = []
    for manifest in payload["manifests"]:
        path = (
            repo_root
            / "physics/data/real_world/south_fork_american_chili_bar/production_corridor"
            / "full_reach_windows"
            / manifest["window_id"]
            / "manifest.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)

    index_payload = {key: value for key, value in payload.items() if key != "manifests"}
    index_path = repo_root / FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(index_path)
    write_south_fork_a1_window_source_pull_status(repo_root)
    return written
