"""Review actual South Fork A1 full-reach window source-pull files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .south_fork_a1_window_source_pulls import (
    FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
)


FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_pull_status.json"
)
FULL_REACH_WINDOW_SOURCE_ROOT_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_windows"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_record(repo_root: Path, relative_path: str, *, role: str, source_url: str | None = None) -> dict[str, Any]:
    path = repo_root / relative_path
    present = path.is_file()
    record: dict[str, Any] = {
        "role": role,
        "relative_path": relative_path,
        "status": "present" if present else "missing",
        "present": present,
    }
    if source_url is not None:
        record["official_export_url"] = source_url
    if present:
        record["byte_count"] = path.stat().st_size
        record["sha256"] = _sha256(path)
    else:
        record["byte_count"] = 0
        record["sha256"] = None
    if path.exists() and not present:
        record["status"] = "unexpected_non_file_path"
    return record


def _unexpected_files(repo_root: Path, expected_paths: set[str]) -> list[str]:
    root = repo_root / FULL_REACH_WINDOW_SOURCE_ROOT_RELATIVE_PATH
    if not root.exists():
        return []
    unexpected = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(repo_root))
        if relative not in expected_paths:
            unexpected.append(relative)
    return sorted(unexpected)


def build_south_fork_a1_window_source_pull_status(repo_root: Path) -> dict[str, Any]:
    """Build a filesystem-backed status report for planned full-reach source pulls."""

    repo_root = repo_root.resolve()
    plan = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH)
    window_reports = []
    expected_paths: set[str] = set()
    source_file_records: list[dict[str, Any]] = []
    window_manifest_records: list[dict[str, Any]] = []
    existing_artifact_records: list[dict[str, Any]] = []
    review_derivative_records: list[dict[str, Any]] = []

    for window in plan["windows"]:
        expected_outputs = window["expected_outputs"]
        terrain = _file_record(
            repo_root,
            expected_outputs["terrain_dem"],
            role="terrain_dem",
            source_url=window["terrain_3dep_export"]["query_url"],
        )
        aerial = _file_record(
            repo_root,
            expected_outputs["aerial_imagery"],
            role="aerial_imagery",
            source_url=window["aerial_naip_export"]["query_url"],
        )
        manifest = _file_record(
            repo_root,
            expected_outputs["window_manifest"],
            role="per_window_manifest",
        )
        source_files = [terrain, aerial]
        source_file_records.extend(source_files)
        window_manifest_records.append(manifest)
        expected_paths.update(record["relative_path"] for record in [terrain, aerial, manifest])

        review_derivatives: list[dict[str, Any]] = []
        if manifest["present"]:
            window_manifest = _load_json(repo_root, manifest["relative_path"])
            for role, relative_path in sorted(window_manifest["derivative_targets"].items()):
                derivative = _file_record(
                    repo_root,
                    relative_path,
                    role=f"review_derivative_{role}",
                )
                review_derivatives.append(derivative)
            review_derivative_records.extend(review_derivatives)
            expected_paths.update(record["relative_path"] for record in review_derivatives)

        existing_artifact = None
        if window.get("existing_artifact"):
            existing_artifact = _file_record(
                repo_root,
                window["existing_artifact"],
                role="existing_pilot_artifact",
            )
            existing_artifact_records.append(existing_artifact)

        source_file_present_count = sum(1 for record in source_files if record["present"])
        if source_file_present_count < len(source_files):
            status = "source_files_missing"
        elif not manifest["present"]:
            status = "source_files_present_window_manifest_missing"
        else:
            status = "source_files_and_window_manifest_present_review_pending"

        window_reports.append(
            {
                "window_id": window["window_id"],
                "display_name": window["display_name"],
                "station_start_m": window["station_start_m"],
                "station_end_m": window["station_end_m"],
                "status": status,
                "source_file_present_count": source_file_present_count,
                "source_file_expected_count": len(source_files),
                "terrain_dem": terrain,
                "aerial_imagery": aerial,
                "window_manifest": manifest,
                "review_derivatives": review_derivatives,
                "review_derivative_present_count": sum(
                    1 for record in review_derivatives if record["present"]
                ),
                "review_derivative_expected_count": len(review_derivatives),
                "existing_artifact": existing_artifact,
                "can_generate_window_derivatives": source_file_present_count == len(source_files),
                "can_enter_stitched_validation": (
                    source_file_present_count == len(source_files) and manifest["present"]
                ),
                "production_promoted": False,
            }
        )

    present_source_count = sum(1 for record in source_file_records if record["present"])
    present_manifest_count = sum(1 for record in window_manifest_records if record["present"])
    unexpected = _unexpected_files(repo_root, expected_paths)
    all_source_files_present = present_source_count == len(source_file_records)
    all_window_manifests_present = present_manifest_count == len(window_manifest_records)
    if all_source_files_present and all_window_manifests_present and not unexpected:
        status = "ready_for_stitched_validation_review"
    elif all_source_files_present and not all_window_manifests_present:
        status = "pending_window_manifests"
    else:
        status = "pending_window_source_files"

    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_status.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": plan["river_id"],
        "status": status,
        "production_promoted": False,
        "inputs": {
            "source_pull_plan": FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
        },
        "source_root": FULL_REACH_WINDOW_SOURCE_ROOT_RELATIVE_PATH,
        "summary": {
            "window_count": len(window_reports),
            "expected_source_file_count": len(source_file_records),
            "present_source_file_count": present_source_count,
            "missing_source_file_count": len(source_file_records) - present_source_count,
            "expected_window_manifest_count": len(window_manifest_records),
            "present_window_manifest_count": present_manifest_count,
            "missing_window_manifest_count": len(window_manifest_records) - present_manifest_count,
            "existing_pilot_artifact_count": len(existing_artifact_records),
            "present_existing_pilot_artifact_count": sum(
                1 for record in existing_artifact_records if record["present"]
            ),
            "expected_review_derivative_count": len(review_derivative_records),
            "present_review_derivative_count": sum(
                1 for record in review_derivative_records if record["present"]
            ),
            "missing_review_derivative_count": sum(
                1 for record in review_derivative_records if not record["present"]
            ),
            "unexpected_file_count": len(unexpected),
            "all_source_files_present": all_source_files_present,
            "all_window_manifests_present": all_window_manifests_present,
        },
        "unexpected_files": unexpected,
        "windows": window_reports,
        "promotion_gate": {
            "can_promote_full_reach_corridor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_enter_stitched_validation_review": (
                all_source_files_present and all_window_manifests_present and not unexpected
            ),
            "exit_criteria": [
                "Download each official 3DEP DEM and NAIP image from the recorded bounded export URLs.",
                "Commit or attach every source file according to rights and LFS policy with byte counts and SHA-256 hashes recorded here.",
                "Generate per-window manifests with source terms, CRS, resolution, bounds, and derivative targets.",
                "Produce stitched validation previews across every window seam.",
                "Pass geospatial/art/source review before any Unreal landscape import or rapid geometry binding.",
            ],
        },
    }


def write_south_fork_a1_window_source_pull_status(repo_root: Path) -> Path:
    payload = build_south_fork_a1_window_source_pull_status(repo_root)
    path = repo_root / FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
