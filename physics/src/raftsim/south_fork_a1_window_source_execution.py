"""Execute bounded South Fork A1 full-reach window source pulls."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .south_fork_a1_window_source_pulls import (
    FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
    NAIP_SERVICE_URL,
    THREE_DEP_SERVICE_URL,
)
from .south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
    write_south_fork_a1_window_source_pull_status,
)


FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_pull_execution_plan.json"
)
DEFAULT_MAX_BYTES_PER_FILE = 96 * 1024 * 1024
_ALLOWED_SERVICE_URLS = (THREE_DEP_SERVICE_URL, NAIP_SERVICE_URL)
_SOURCE_PULL_USER_AGENT = "SmokeEmIfYouGotEm-RaftSim-A1-source-pull/1.0"


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_official_url(url: str) -> None:
    if not any(url.startswith(service_url) for service_url in _ALLOWED_SERVICE_URLS):
        raise ValueError(f"Refusing non-approved source-pull URL: {url}")
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Refusing non-HTTPS source-pull URL: {url}")


def build_south_fork_a1_window_source_pull_tasks(
    repo_root: Path,
    *,
    window_ids: set[str] | None = None,
    roles: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return executable DEM/NAIP source-pull task records from the A1 plan."""

    repo_root = repo_root.resolve()
    plan = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH)
    tasks: list[dict[str, Any]] = []
    for window in plan["windows"]:
        window_id = window["window_id"]
        if window_ids is not None and window_id not in window_ids:
            continue
        output_specs = (
            (
                "terrain_dem",
                "USGS 3DEP DEM",
                window["terrain_3dep_export"],
                window["expected_outputs"]["terrain_dem"],
                "tif",
            ),
            (
                "aerial_imagery",
                "USDA NAIP aerial imagery",
                window["aerial_naip_export"],
                window["expected_outputs"]["aerial_imagery"],
                "png",
            ),
        )
        for role, label, export, destination, lfs_extension in output_specs:
            if roles is not None and role not in roles:
                continue
            url = export["query_url"]
            _validate_official_url(url)
            path = repo_root / destination
            tasks.append(
                {
                    "task_id": f"{window_id}:{role}",
                    "window_id": window_id,
                    "display_name": window["display_name"],
                    "role": role,
                    "label": label,
                    "official_export_url": url,
                    "service_url": export["service_url"],
                    "destination": destination,
                    "destination_present": path.is_file(),
                    "destination_sha256": _sha256(path) if path.is_file() else None,
                    "destination_byte_count": path.stat().st_size if path.is_file() else 0,
                    "expected_format": export["format"],
                    "expected_size_px": export["size_px"],
                    "lfs_tracking_required": True,
                    "lfs_extension": lfs_extension,
                    "production_promoted": False,
                }
            )
    return tasks


def build_south_fork_a1_window_source_pull_execution_plan(repo_root: Path) -> dict[str, Any]:
    """Build the executable full-reach source-pull contract without downloading."""

    tasks = build_south_fork_a1_window_source_pull_tasks(repo_root)
    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_execution_plan.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "status": "ready_to_execute_review_gated_source_downloads",
        "production_promoted": False,
        "inputs": {
            "source_pull_plan": FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
            "source_pull_status": FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
        },
        "download_command": (
            "cd physics && UV_CACHE_DIR=/private/tmp/raftsim-uv-cache "
            "uv run python -m raftsim.examples.generate_south_fork_a1_window_source_execution "
            "--repo-root .. --execute"
        ),
        "policy": {
            "allowed_service_urls": list(_ALLOWED_SERVICE_URLS),
            "https_only": True,
            "atomic_partial_downloads": True,
            "overwrite_default": False,
            "max_bytes_per_file": DEFAULT_MAX_BYTES_PER_FILE,
            "lfs_tracking_required": True,
            "lfs_patterns_required": [
                "*.tif",
                "*.tiff",
                "physics/data/real_world/*/production_corridor/full_reach_windows/**/*.png",
            ],
        },
        "summary": {
            "task_count": len(tasks),
            "terrain_task_count": sum(1 for task in tasks if task["role"] == "terrain_dem"),
            "aerial_task_count": sum(1 for task in tasks if task["role"] == "aerial_imagery"),
            "destination_present_count": sum(1 for task in tasks if task["destination_present"]),
            "destination_missing_count": sum(1 for task in tasks if not task["destination_present"]),
        },
        "tasks": tasks,
        "promotion_gate": {
            "can_promote_full_reach_corridor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Run the source-pull command only after reviewing every window bbox against the downstream-anchor decision.",
                "Regenerate the source-pull status report after download so byte counts and SHA-256 hashes are recorded.",
                "Generate per-window manifests and stitched seam-validation previews before Unreal import.",
                "Keep all A1 production gates blocked until geospatial/art/source review passes.",
            ],
        },
    }


def write_south_fork_a1_window_source_pull_execution_plan(repo_root: Path) -> Path:
    payload = build_south_fork_a1_window_source_pull_execution_plan(repo_root)
    path = repo_root / FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def execute_south_fork_a1_window_source_pulls(
    repo_root: Path,
    *,
    window_ids: set[str] | None = None,
    roles: set[str] | None = None,
    overwrite: bool = False,
    max_bytes_per_file: int = DEFAULT_MAX_BYTES_PER_FILE,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Download selected source files and refresh the filesystem-backed status."""

    repo_root = repo_root.resolve()
    tasks = build_south_fork_a1_window_source_pull_tasks(
        repo_root,
        window_ids=window_ids,
        roles=roles,
    )
    results = []
    for task in tasks:
        destination = repo_root / task["destination"]
        if destination.exists() and not overwrite:
            results.append(
                {
                    **task,
                    "status": "skipped_existing",
                    "downloaded": False,
                    "sha256": task["destination_sha256"],
                    "byte_count": task["destination_byte_count"],
                }
            )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = _download_task(
                task,
                destination,
                max_bytes_per_file=max_bytes_per_file,
                opener=opener,
            )
        except (OSError, URLError, ValueError) as exc:
            result = {
                **task,
                "status": "failed",
                "downloaded": False,
                "error": str(exc),
                "sha256": None,
                "byte_count": 0,
            }
        results.append(result)

    status_path = write_south_fork_a1_window_source_pull_status(repo_root)
    failed_count = sum(1 for result in results if result["status"] == "failed")
    downloaded_count = sum(1 for result in results if result["status"] == "downloaded")
    skipped_count = sum(1 for result in results if result["status"] == "skipped_existing")
    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_execution_report.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "status": "failed" if failed_count else "completed",
        "production_promoted": False,
        "summary": {
            "task_count": len(results),
            "downloaded_count": downloaded_count,
            "skipped_existing_count": skipped_count,
            "failed_count": failed_count,
        },
        "status_artifact": str(status_path.relative_to(repo_root)),
        "results": results,
    }


def _download_task(
    task: dict[str, Any],
    destination: Path,
    *,
    max_bytes_per_file: int,
    opener: Callable[..., Any],
) -> dict[str, Any]:
    request = Request(
        task["official_export_url"],
        headers={"User-Agent": _SOURCE_PULL_USER_AGENT},
    )
    partial_path: Path | None = None
    try:
        with opener(request, timeout=60) as response:
            with tempfile.NamedTemporaryFile(
                "wb",
                delete=False,
                dir=str(destination.parent),
                prefix=f".{destination.name}.",
                suffix=".partial",
            ) as partial:
                partial_path = Path(partial.name)
                byte_count = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    byte_count += len(chunk)
                    if byte_count > max_bytes_per_file:
                        raise ValueError(
                            f"{task['task_id']} exceeded max_bytes_per_file={max_bytes_per_file}"
                        )
                    partial.write(chunk)
        if partial_path is None:
            raise ValueError(f"{task['task_id']} did not create a partial download file")
        shutil.move(str(partial_path), destination)
    except Exception:
        if partial_path is not None and partial_path.exists():
            partial_path.unlink()
        raise
    return {
        **task,
        "status": "downloaded",
        "downloaded": True,
        "byte_count": destination.stat().st_size,
        "sha256": _sha256(destination),
    }
