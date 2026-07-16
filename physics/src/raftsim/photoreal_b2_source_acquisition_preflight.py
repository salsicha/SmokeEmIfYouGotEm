"""Build the B2 photoreal source-acquisition preflight queue."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .photoreal_chilko_asset_selection_b2 import (
    CHILKO_B2_ASSET_SELECTION_RELATIVE_PATH,
    build_chilko_b2_asset_selection,
)
from .photoreal_colorado_asset_selection_b2 import (
    COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH,
    build_colorado_b2_asset_selection,
)
from .photoreal_futaleufu_asset_selection_b2 import (
    FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH,
    build_futaleufu_b2_asset_selection,
)
from .photoreal_pacuare_asset_selection_b2 import (
    PACUARE_B2_ASSET_SELECTION_RELATIVE_PATH,
    build_pacuare_b2_asset_selection,
)
from .photoreal_south_fork_asset_selection_b2 import (
    SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH,
    build_south_fork_b2_asset_selection,
)


B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_acquisition_preflight.json"
)
B2_SOURCE_ACQUISITION_PREFLIGHT_SCHEMA = (
    "raftsim.photoreal.b2_source_acquisition_preflight.v1"
)


_SelectionBuilder = tuple[str, str, Callable[[], dict[str, Any]]]


SELECTION_BUILDERS: tuple[_SelectionBuilder, ...] = (
    (
        "south_fork",
        SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH,
        build_south_fork_b2_asset_selection,
    ),
    (
        "colorado",
        COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH,
        build_colorado_b2_asset_selection,
    ),
    (
        "pacuare",
        PACUARE_B2_ASSET_SELECTION_RELATIVE_PATH,
        build_pacuare_b2_asset_selection,
    ),
    (
        "futaleufu",
        FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH,
        build_futaleufu_b2_asset_selection,
    ),
    (
        "chilko",
        CHILKO_B2_ASSET_SELECTION_RELATIVE_PATH,
        build_chilko_b2_asset_selection,
    ),
)


def build_b2_source_acquisition_preflight() -> dict[str, Any]:
    """Build a non-executable queue for B2 source acquisition."""

    manifests = [
        _manifest_summary(short_id, relative_path, build())
        for short_id, relative_path, build in SELECTION_BUILDERS
    ]
    cc0_tasks = [
        _cc0_download_task(manifest, candidate)
        for manifest in manifests
        for candidate in manifest["candidate_assets"]
        if _is_selected_cc0_download_candidate(candidate)
    ]
    fab_slots = [
        _fab_local_only_slot(manifest, candidate)
        for manifest in manifests
        for candidate in manifest["candidate_assets"]
        if candidate["source_family"] == "Fab"
    ]
    first_party_entries = [
        _first_party_entry(manifest, candidate)
        for manifest in manifests
        for candidate in manifest["candidate_assets"]
        if candidate["source_family"] in (
            "First-party procedural",
            "Project-owned procedural",
        )
    ]

    return {
        "schema": B2_SOURCE_ACQUISITION_PREFLIGHT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "preflight_queue_recorded_downloads_disabled_until_size_and_storage_approval",
        "river_count": len(manifests),
        "selection_manifest_count": len(manifests),
        "candidate_asset_count": sum(
            manifest["candidate_asset_count"] for manifest in manifests
        ),
        "cc0_download_task_count": len(cc0_tasks),
        "fab_local_only_slot_count": len(fab_slots),
        "first_party_entry_count": len(first_party_entries),
        "selection_manifests": [
            {
                "short_id": manifest["short_id"],
                "river_id": manifest["river_id"],
                "display_name": manifest["display_name"],
                "relative_path": manifest["relative_path"],
                "candidate_asset_count": manifest["candidate_asset_count"],
                "production_promoted": manifest["production_promoted"],
            }
            for manifest in manifests
        ],
        "cc0_download_tasks": cc0_tasks,
        "fab_local_only_slots": fab_slots,
        "first_party_entries": first_party_entries,
        "execution_gate": {
            "downloads_allowed_now": False,
            "imports_allowed_now": False,
            "source_binaries_allowed_in_repo_now": False,
            "requires_owner_size_storage_decision": True,
            "requires_lfs_storage_headroom": True,
            "requires_exact_resolution_and_file_selection": True,
            "requires_hash_report_before_commit": True,
            "blocking_reasons": [
                "Selected CC0 assets have exact asset pages but no recorded source-bundle byte sizes, resolution choices, file lists, or hashes.",
                "Several Poly Haven geometry candidates are large enough that committing source bundles needs explicit size/LFS approval.",
                "Fab candidates are local-only selection slots and must not be downloaded into the public repo.",
                "First-party fallbacks are available but do not replace external asset review or human lifelike approval.",
            ],
            "next_required_actions": [
                "For each CC0 task, choose source resolution and exact file formats before downloading.",
                "Record expected byte size and LFS classification, then get owner storage approval before committing source binaries.",
                "Download one approved CC0 task at a time into the river-specific reviewed source root and hash every file.",
                "Keep Fab binaries local-only and commit only URL/license/hash/import reports.",
                "Run isolated import, capture, review, and performance gates before any corridor substitution.",
            ],
        },
    }


def write_b2_source_acquisition_preflight(repo_root: Path) -> Path:
    payload = build_b2_source_acquisition_preflight()
    path = repo_root / B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _manifest_summary(
    short_id: str, relative_path: str, manifest: dict[str, Any]
) -> dict[str, Any]:
    return {
        "short_id": short_id,
        "relative_path": relative_path,
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "production_promoted": manifest["production_promoted"],
        "assets_downloaded": manifest["assets_downloaded"],
        "assets_imported": manifest["assets_imported"],
        "corridor_substitution_allowed": manifest["corridor_substitution_allowed"],
        "candidate_asset_count": manifest["candidate_asset_count"],
        "candidate_assets": manifest["candidate_assets"],
    }


def _is_selected_cc0_download_candidate(candidate: dict[str, Any]) -> bool:
    return (
        candidate["source_family"] == "Poly Haven"
        and candidate["status"] == "selected_for_download_hash_import_and_isolated_review"
    )


def _cc0_download_task(
    manifest: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    return {
        "task_id": (
            f"{manifest['river_id']}:{candidate['candidate_id']}:"
            "cc0_source_download_preflight"
        ),
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "selection_manifest": manifest["relative_path"],
        "candidate_id": candidate["candidate_id"],
        "asset_need_id": candidate["asset_need_id"],
        "asset_url": candidate["asset_url"],
        "license_class": candidate["license_class"],
        "repo_binary_policy": candidate["repo_binary_policy"],
        "planned_source_root_env": _source_root_env(manifest["river_id"]),
        "execution_allowed": False,
        "repo_commit_allowed_now": False,
        "required_before_execute": [
            "choose exact resolution and file formats",
            "record expected byte size before download",
            "record LFS classification and retention policy",
            "record owner storage approval for source binaries",
            "record target reviewed source root",
        ],
        "required_before_commit": [
            "record file list",
            "record SHA-256 hash for every source file",
            "record import settings and Unreal destination path",
            "record license snapshot URL",
            "run isolated import and capture gates",
        ],
        "blocked_reason": (
            "Exact file sizes, selected source formats, hashes, and owner "
            "storage/LFS approval are not recorded yet."
        ),
    }


def _fab_local_only_slot(
    manifest: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    return {
        "slot_id": f"{manifest['river_id']}:{candidate['candidate_id']}:fab_local_only",
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "selection_manifest": manifest["relative_path"],
        "candidate_id": candidate["candidate_id"],
        "asset_need_id": candidate["asset_need_id"],
        "asset_url": candidate["asset_url"],
        "license_class": candidate["license_class"],
        "repo_binary_policy": candidate["repo_binary_policy"],
        "download_into_public_repo_allowed": False,
        "commit_source_binaries_allowed": False,
        "required_before_local_import": candidate.get("required_before_import", []),
        "blocked_reason": (
            "Fab Standard items stay local-only until exact item terms prove "
            "redistribution rights."
        ),
    }


def _first_party_entry(
    manifest: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    return {
        "entry_id": f"{manifest['river_id']}:{candidate['candidate_id']}:first_party",
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "selection_manifest": manifest["relative_path"],
        "candidate_id": candidate["candidate_id"],
        "asset_need_id": candidate["asset_need_id"],
        "source_family": candidate["source_family"],
        "asset_url": candidate["asset_url"],
        "license_class": candidate["license_class"],
        "status": candidate["status"],
        "repo_binary_policy": candidate["repo_binary_policy"],
        "can_cover_external_asset_gap": True,
        "can_replace_human_lifelike_review": False,
    }


def _source_root_env(river_id: str) -> str:
    normalized = "".join(
        character.upper() if character.isalnum() else "_"
        for character in river_id
    )
    return f"RAFTSIM_REVIEWED_{normalized}_B2_SOURCE_ROOT"
