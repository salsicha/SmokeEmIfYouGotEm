"""Build the Chilko B2 photoreal asset-selection manifest."""

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


CHILKO_B2_ASSET_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_lava_canyon/asset_intake/"
    "chilko_b2_asset_selection_manifest.json"
)
CHILKO_B2_ASSET_SELECTION_SCHEMA = "raftsim.photoreal.chilko_asset_selection_b2.v1"
CHILKO_RIVER_ID = "chilko_river_lava_canyon"


def build_chilko_b2_asset_selection() -> dict[str, Any]:
    """Build the first Chilko B2 item-level asset-selection package."""

    river = RIVER_ASSET_NEEDS[CHILKO_RIVER_ID]
    candidate_assets = _candidate_assets()
    coverage = _asset_need_coverage(candidate_assets)
    return {
        "schema": CHILKO_B2_ASSET_SELECTION_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": CHILKO_RIVER_ID,
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
                "CC0 conifer, volcanic-rock, river-rock, and dry-riverbed candidates still need downloaded source hashes and importer reports.",
                "Lodgepole/spruce/aspen species mix and glacial-blue wet-bank identity still need exact source-conditioned review.",
                "Volcanic Rock Tiles is a texture candidate only and is not Lava Canyon geometry or geology authority.",
                "No isolated turntable, 60 m, 150 m, map-check, desktop, or VR evidence exists for the new selections.",
            ],
            "next_required_actions": [
                "Download the selected CC0 candidates into reviewed source roots and hash every source file.",
                "Pick exact local-only Fab or first-party hero assets for lodgepole, spruce, aspen, volcanic canyon rock, and cold-water gravel/debris.",
                "Run the B1 importer command for each selected asset set and write fail-closed import reports.",
                "Capture isolated turntable plus 60 m and 150 m river-distance evidence before any corridor substitution.",
                "Record guide, ecology, art, rights, hazard-readability, and desktop/VR performance reviews.",
            ],
        },
    }


def write_chilko_b2_asset_selection(repo_root: Path) -> Path:
    payload = build_chilko_b2_asset_selection()
    path = repo_root / CHILKO_B2_ASSET_SELECTION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _candidate_assets() -> list[dict[str, Any]]:
    return [
        _poly_haven_candidate(
            candidate_id="polyhaven_pine_sapling_small",
            asset_need_id="lodgepole_spruce_aspen_foliage",
            asset_url="https://polyhaven.com/a/pine_sapling_small",
            role="cc0_young_conifer_structure_trial",
            notes=(
                "Selected as a rights-clear young conifer structure candidate; "
                "not lodgepole pine, spruce, or aspen species authority."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_fir_sapling",
            asset_need_id="lodgepole_spruce_aspen_foliage",
            asset_url="https://polyhaven.com/a/fir_sapling",
            role="cc0_conifer_understory_variation_trial",
            notes=(
                "Selected as a conifer sapling variation for isolated review; "
                "masked foliage must stay non-Nanite unless measured review passes."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_volcanic_rock_tiles",
            asset_need_id="volcanic_canyon_rock",
            asset_url="https://polyhaven.com/a/volcanic_rock_tiles",
            role="dark_pitted_volcanic_surface_material_trial",
            notes=(
                "Selected as a dark volcanic surface material candidate; not Lava "
                "Canyon geometry, wall stratigraphy, or natural talus authority."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_dry_riverbed_rock",
            asset_need_id="cold_water_debris_and_gravel",
            asset_url="https://polyhaven.com/a/dry_riverbed_rock",
            role="weathered_cold_bank_rock_material_trial",
            notes=(
                "Selected for weathered bank and gravel material review; cold-water "
                "debris scale and distribution still need corridor source review."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_river_small_rocks",
            asset_need_id="glacial_blue_wet_bank_materials",
            asset_url="https://polyhaven.com/a/river_small_rocks",
            role="wet_bank_pebble_rock_material_trial",
            notes=(
                "Selected for wet-bank pebble and broken-rock detail under the "
                "glacial-blue water support path; not river color or hydrology authority."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_chilko_lodgepole_spruce_aspen_foliage_slot",
            asset_need_id="lodgepole_spruce_aspen_foliage",
            search_url=(
                "https://www.fab.com/search?q=lodgepole%20spruce%20aspen%20forest%20foliage"
            ),
            role="interior_bc_foliage_exact_item_selection_required",
            notes=(
                "Needed for lodgepole/spruce/aspen mix, age variation, burned or "
                "regenerating stands, and corridor silhouette."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_chilko_glacial_blue_wet_bank_slot",
            asset_need_id="glacial_blue_wet_bank_materials",
            search_url="https://www.fab.com/search?q=glacial%20river%20wet%20bank%20rock",
            role="glacial_wet_bank_exact_item_selection_required",
            notes=(
                "Needed for wet/dry bank response, glacial-blue water support, "
                "and source-conditioned bank material variation."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_chilko_lava_canyon_volcanic_rock_slot",
            asset_need_id="volcanic_canyon_rock",
            search_url="https://www.fab.com/search?q=volcanic%20basalt%20canyon%20rock",
            role="lava_canyon_volcanic_rock_exact_item_selection_required",
            notes=(
                "Needed for Lava Canyon volcanic walls, talus, hoodoo-like forms, "
                "and source-matched rock identity."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_chilko_cold_water_debris_gravel_slot",
            asset_need_id="cold_water_debris_and_gravel",
            search_url="https://www.fab.com/search?q=cold%20river%20gravel%20debris%20driftwood",
            role="cold_water_gravel_debris_exact_item_selection_required",
            notes=(
                "Needed for cold-water gravel bars, debris, driftwood, and near-bank "
                "scale cues that generic materials cannot validate alone."
            ),
        ),
        {
            "candidate_id": "first_party_chilko_biome_fallback_v1",
            "asset_need_id": "all_chilko_asset_needs",
            "source_family": "First-party procedural",
            "asset_url": "source_manifest://first_party_chilko_biome_fallback_v1",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "status": "required_fallback_until_external_assets_pass",
            "role": "missing_external_asset_fallback",
            "notes": (
                "Fallback must remain available for interior BC foliage, glacial "
                "wet banks, volcanic canyon rock, and cold-water debris whenever "
                "local-only Fab binaries are absent or CC0 candidates fail review."
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
            "guide, ecology, art, rights, and hazard-readability review",
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
            "guide, ecology, art, rights, and hazard-readability review",
        ],
        "notes": notes,
    }


def _asset_need_coverage(
    candidate_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = []
    for asset_need_id, use in RIVER_ASSET_NEEDS[CHILKO_RIVER_ID]["asset_needs"]:
        candidates = [
            candidate
            for candidate in candidate_assets
            if candidate["asset_need_id"] in (asset_need_id, "all_chilko_asset_needs")
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
