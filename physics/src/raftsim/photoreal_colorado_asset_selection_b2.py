"""Build the Colorado Grand Canyon B2 photoreal asset-selection manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_asset_intake_b1 import (
    B1_ASSET_INTAKE_RELATIVE_PATH,
    FAB_EULA_URL,
    POLY_HAVEN_LICENSE_URL,
    RIVER_ASSET_NEEDS,
)
from .photoreal_asset_set_intake_b1 import B1_ASSET_SET_INTAKE_RELATIVE_PATH


COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/asset_intake/"
    "colorado_b2_asset_selection_manifest.json"
)
COLORADO_B2_ASSET_SELECTION_SCHEMA = "raftsim.photoreal.colorado_asset_selection_b2.v1"
COLORADO_RIVER_ID = "colorado_river_grand_canyon_rowing"


def build_colorado_b2_asset_selection() -> dict[str, Any]:
    """Build the first Colorado B2 item-level asset-selection package."""

    river = RIVER_ASSET_NEEDS[COLORADO_RIVER_ID]
    candidate_assets = _candidate_assets()
    coverage = _asset_need_coverage(candidate_assets)
    return {
        "schema": COLORADO_B2_ASSET_SELECTION_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": COLORADO_RIVER_ID,
        "display_name": river["display_name"],
        "biome": river["biome"],
        "status": "b2_item_selection_started_no_assets_imported_no_promotion",
        "source_contracts": {
            "b1_asset_intake": B1_ASSET_INTAKE_RELATIVE_PATH,
            "b1_asset_set_commands": B1_ASSET_SET_INTAKE_RELATIVE_PATH,
        },
        "production_promoted": False,
        "assets_downloaded": False,
        "assets_imported": False,
        "corridor_substitution_allowed": False,
        "asset_need_count": len(river["asset_needs"]),
        "candidate_asset_count": len(candidate_assets),
        "asset_need_coverage": coverage,
        "candidate_assets": candidate_assets,
        "license_sources_checked": [
            {
                "source_family": "Poly Haven",
                "url": POLY_HAVEN_LICENSE_URL,
                "checked_on": "2026-07-16",
                "decision": (
                    "CC0 Poly Haven candidates may be committed only after exact "
                    "asset URLs, downloaded source-file hashes, import settings, "
                    "and isolated review evidence are recorded."
                ),
            },
            {
                "source_family": "Fab",
                "url": FAB_EULA_URL,
                "checked_on": "2026-07-16",
                "decision": (
                    "Fab Standard candidates remain local-only selection slots in "
                    "this public repo unless item terms explicitly prove broader "
                    "redistribution rights."
                ),
            },
        ],
        "promotion_gate": {
            "b2_selection_manifest_recorded": True,
            "can_download_cc0_candidates": True,
            "can_import_isolated_review_assets": False,
            "can_substitute_corridor_assets": False,
            "can_request_human_lifelike_review": False,
            "blocking_reasons": [
                "CC0 canyon-wall and sand candidates still need downloaded source hashes and importer reports.",
                "Grand Canyon stratigraphy still needs exact source-conditioned materials and geospatial/art review.",
                "Tamarisk, willow, cactus, desert scrub, and Lava Falls basalt still need exact local-only or first-party selections.",
                "No isolated turntable, 60 m, 150 m, map-check, desktop, or VR evidence exists for the new selections.",
            ],
            "next_required_actions": [
                "Download the selected CC0 candidates into reviewed source roots and hash every source file.",
                "Pick exact local-only Fab or first-party hero assets for tamarisk, willow, cactus, desert scrub, and Lava Falls basalt.",
                "Run the B1 importer command for each selected asset set and write fail-closed import reports.",
                "Capture isolated turntable plus 60 m and 150 m river-distance evidence before any corridor substitution.",
                "Record oarsman, guide, ecology, art, rights, hazard-readability, and desktop/VR performance reviews.",
            ],
        },
    }


def write_colorado_b2_asset_selection(repo_root: Path) -> Path:
    payload = build_colorado_b2_asset_selection()
    path = repo_root / COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _candidate_assets() -> list[dict[str, Any]]:
    return [
        _poly_haven_candidate(
            candidate_id="polyhaven_rock_face",
            asset_need_id="grand_canyon_layered_cliff_materials",
            asset_url="https://polyhaven.com/a/rock_face",
            role="reddish_brown_cliff_face_material_trial",
            notes=(
                "Selected as a rights-clear generic red-brown cliff-face material "
                "candidate for isolated canyon-wall shader trials; not Grand "
                "Canyon stratigraphy authority."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_rock_06",
            asset_need_id="grand_canyon_layered_cliff_materials",
            asset_url="https://polyhaven.com/a/rock_06",
            role="yellow_brown_striated_cliff_detail_trial",
            notes=(
                "Selected for striated yellow-brown rock detail review where "
                "layering cues are needed; exact Grand Canyon formation identity "
                "must still come from source-conditioned first-party or reviewed "
                "local-only assets."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_aerial_rocks_02",
            asset_need_id="grand_canyon_layered_cliff_materials",
            asset_url="https://polyhaven.com/a/aerial_rocks_02",
            role="large_scale_rough_cliff_macro_material_trial",
            notes=(
                "Selected as a 50 m rough-cliff macro material candidate for "
                "distance breakup; not a Grand Canyon geology or color authority."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_aerial_beach_03",
            asset_need_id="sand_beach_materials",
            asset_url="https://polyhaven.com/a/aerial_beach_03",
            role="large_scale_brown_sandbar_material_trial",
            notes=(
                "Selected as a rights-clear broad sandbar/beach surface candidate "
                "for camp-beach and bar-edge isolated review."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_sand_01",
            asset_need_id="sand_beach_materials",
            asset_url="https://polyhaven.com/a/sand_01",
            role="close_range_compacted_sand_clay_material_trial",
            notes=(
                "Selected for near-field compacted sand/clay detail; Grand Canyon "
                "camp-beach color and wet/dry response still need source review."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_grand_canyon_layered_cliff_hero_slot",
            asset_need_id="grand_canyon_layered_cliff_materials",
            search_url=(
                "https://www.fab.com/search?q=grand%20canyon%20sandstone%20cliff%20megascans"
            ),
            role="hero_canyon_wall_exact_item_selection_required",
            notes=(
                "Needed for signature layered canyon walls where generic Poly "
                "Haven materials cannot carry the formation-specific identity."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_desert_scrub_tamarisk_willow_cactus_slot",
            asset_need_id="desert_scrub_riparian_foliage",
            search_url=(
                "https://www.fab.com/search?q=desert%20scrub%20willow%20tamarisk%20cactus"
            ),
            role="riparian_desert_foliage_exact_item_selection_required",
            notes=(
                "Needed for tamarisk/willow/cactus bank silhouettes and sparse "
                "desert-scrub massing; exact item-level license review is open."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_lava_falls_basalt_slot",
            asset_need_id="lava_falls_basalt",
            search_url="https://www.fab.com/search?q=basalt%20lava%20rock%20megascans",
            role="lava_falls_basalt_exact_item_selection_required",
            notes=(
                "Needed for Lava Falls dark volcanic rock identity; no generic "
                "asset may be promoted as rapid-specific basalt without guide, "
                "art, geospatial, and rights review."
            ),
        ),
        {
            "candidate_id": "first_party_colorado_biome_fallback_v1",
            "asset_need_id": "all_colorado_asset_needs",
            "source_family": "First-party procedural",
            "asset_url": "source_manifest://first_party_colorado_biome_fallback_v1",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "status": "required_fallback_until_external_assets_pass",
            "role": "missing_external_asset_fallback",
            "notes": (
                "Fallback must remain available for canyon walls, sand beaches, "
                "riparian/desert foliage, and Lava Falls basalt whenever local-only "
                "Fab binaries are absent or CC0 candidates fail review."
            ),
        },
    ]


def _poly_haven_candidate(
    *,
    candidate_id: str,
    asset_need_id: str,
    asset_url: str,
    role: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "asset_need_id": asset_need_id,
        "source_family": "Poly Haven",
        "asset_url": asset_url,
        "license_class": "cc0_committable_after_hash_and_attribution_snapshot",
        "repo_binary_policy": "may_commit_source_or_derived_binaries_if_size_is_approved",
        "status": "selected_for_download_hash_import_and_isolated_review",
        "role": role,
        "required_before_import": [
            "download source bundle from exact asset URL",
            "record file list and SHA-256 hashes",
            "record source resolution/format choices",
            "record importer settings and Unreal destination path",
        ],
        "required_before_promotion": [
            "isolated turntable capture",
            "60 m river-distance capture",
            "150 m river-distance capture",
            "map-check zero errors",
            "desktop and VR performance measurements",
            "art, ecology, guide/oarsman, rights, and hazard-readability review",
        ],
        "notes": notes,
    }


def _fab_local_only_slot(
    *,
    candidate_id: str,
    asset_need_id: str,
    search_url: str,
    role: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "asset_need_id": asset_need_id,
        "source_family": "Fab",
        "asset_url": search_url,
        "license_class": "fab_standard_local_only_until_item_terms_prove_redistributable",
        "repo_binary_policy": "do_not_commit_source_binaries",
        "status": "local_only_exact_item_selection_pending",
        "role": role,
        "required_before_import": [
            "select exact Fab item URL",
            "record publisher, license tier, and acquisition date",
            "store source binaries only in reviewed local source root",
            "record source-file hashes in committed manifest without committing binaries",
        ],
        "required_before_promotion": [
            "isolated turntable capture",
            "60 m river-distance capture",
            "150 m river-distance capture",
            "map-check zero errors",
            "desktop and VR performance measurements",
            "art, ecology, guide/oarsman, rights, and hazard-readability review",
        ],
        "notes": notes,
    }


def _asset_need_coverage(
    candidate_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = []
    for asset_need_id, use in RIVER_ASSET_NEEDS[COLORADO_RIVER_ID]["asset_needs"]:
        candidates = [
            candidate
            for candidate in candidate_assets
            if candidate["asset_need_id"] in (asset_need_id, "all_colorado_asset_needs")
        ]
        coverage.append(
            {
                "asset_need_id": asset_need_id,
                "use": use,
                "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
                "selected_candidate_count": len(candidates),
                "has_cc0_download_candidate": any(
                    candidate["source_family"] == "Poly Haven"
                    and candidate["status"].startswith("selected_for_download")
                    for candidate in candidates
                ),
                "has_local_only_selection_slot": any(
                    candidate["source_family"] == "Fab" for candidate in candidates
                ),
                "has_first_party_fallback": any(
                    candidate["source_family"] == "First-party procedural"
                    for candidate in candidates
                ),
                "promotion_status": "blocked_pending_source_hashes_import_captures_and_reviews",
            }
        )
    return coverage
