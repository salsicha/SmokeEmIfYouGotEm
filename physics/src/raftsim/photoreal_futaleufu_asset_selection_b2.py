"""Build the Futaleufu B2 photoreal asset-selection manifest."""

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


FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/asset_intake/"
    "futaleufu_b2_asset_selection_manifest.json"
)
FUTALEUFU_B2_ASSET_SELECTION_SCHEMA = (
    "raftsim.photoreal.futaleufu_asset_selection_b2.v1"
)
FUTALEUFU_RIVER_ID = "futaleufu_river_chile"


def build_futaleufu_b2_asset_selection() -> dict[str, Any]:
    """Build the first Futaleufu B2 item-level asset-selection package."""

    river = RIVER_ASSET_NEEDS[FUTALEUFU_RIVER_ID]
    candidate_assets = _candidate_assets()
    coverage = _asset_need_coverage(candidate_assets)
    return {
        "schema": FUTALEUFU_B2_ASSET_SELECTION_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": FUTALEUFU_RIVER_ID,
        "display_name": river["display_name"],
        "biome": river["biome"],
        "status": "b2_item_selection_started_no_assets_imported_no_promotion",
        "source_contracts": {
            "b1_asset_intake": B1_ASSET_INTAKE_RELATIVE_PATH,
            "b1_asset_set_commands": B1_ASSET_SET_INTAKE_RELATIVE_PATH,
            "canopy_strategy_checkpoint": "docs/futaleufu-canopy-strategy-review.md",
            "retained_review_history": "physics/reports/canopy_strategy/futaleufu_review_history.json",
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
                "Nothofagus/coigue hero canopy still needs an owner ecology-analog decision and exact local-only or first-party assets.",
                "CC0 fern, river-rock, dry-riverbed, and mountainside candidates still need downloaded source hashes and importer reports.",
                "Retained project-owned near-bank sapling/fern strata are not hero-canopy approval and still need corridor-distance review.",
                "No isolated turntable, 60 m, 150 m, map-check, desktop, or VR evidence exists for the new selections.",
            ],
            "next_required_actions": [
                "Record the owner canopy-source/analog decision before any Nothofagus or coigue replacement is promoted.",
                "Download the selected CC0 candidates into reviewed source roots and hash every source file.",
                "Pick exact local-only Fab or first-party hero assets for temperate-rainforest canopy, granite boulders, and turquoise wet banks.",
                "Run the B1 importer command for each selected asset set and write fail-closed import reports.",
                "Record guide, ecology, art, rights, hazard-readability, and desktop/VR performance reviews.",
            ],
        },
    }


def write_futaleufu_b2_asset_selection(repo_root: Path) -> Path:
    payload = build_futaleufu_b2_asset_selection()
    path = repo_root / FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _candidate_assets() -> list[dict[str, Any]]:
    return [
        _fab_local_only_slot(
            candidate_id="fab_futaleufu_nothofagus_coigue_canopy_slot",
            asset_need_id="nothofagus_coigue_canopy_or_reviewed_analog",
            search_url=(
                "https://www.fab.com/search?q=nothofagus%20coigue%20temperate%20rainforest%20tree"
            ),
            role="hero_canopy_exact_item_or_reviewed_analog_selection_required",
            notes=(
                "Needed for the hero canopy pivot. Any non-native analog requires "
                "the owner ecology-analog decision and item-level rights review."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_fern_02",
            asset_need_id="near_bank_sapling_fern_strata",
            asset_url="https://polyhaven.com/a/fern_02",
            role="cc0_fern_understory_geometry_trial",
            notes=(
                "Selected as a rights-clear fern clump candidate for near-bank "
                "understory density; not a replacement for Nothofagus/coigue canopy."
            ),
        ),
        _project_owned_candidate(
            candidate_id="project_owned_futaleufu_sapling_fern_strata_v1",
            asset_need_id="near_bank_sapling_fern_strata",
            role="retained_validated_near_bank_strata_candidate",
            notes=(
                "Retains the project-owned sapling/fern near-bank strata as review "
                "evidence and fallback dressing while hero canopy sourcing moves "
                "to reviewed external or first-party assets."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_mountainside",
            asset_need_id="patagonian_granite_boulders",
            asset_url="https://polyhaven.com/a/mountainside",
            role="lichen_layered_boulder_and_cliff_geometry_trial",
            notes=(
                "Selected for rugged lichen and boulder-form review; not Patagonia "
                "granite geology authority."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_dry_riverbed_rock",
            asset_need_id="patagonian_granite_boulders",
            asset_url="https://polyhaven.com/a/dry_riverbed_rock",
            role="weathered_riverbed_rock_material_trial",
            notes=(
                "Selected for weathered riverbed rock material detail; exact "
                "Futaleufu granite color, wetness, and scale remain source-blocked."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_river_small_rocks",
            asset_need_id="turquoise_wet_bank_materials",
            asset_url="https://polyhaven.com/a/river_small_rocks",
            role="wet_bank_pebble_and_rock_ground_material_trial",
            notes=(
                "Selected for wet-bank pebble and broken-rock detail under the "
                "turquoise-water grading path; not water color or hydrology authority."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_futaleufu_patagonian_granite_boulder_slot",
            asset_need_id="patagonian_granite_boulders",
            search_url="https://www.fab.com/search?q=patagonia%20granite%20boulder%20river",
            role="granite_boulder_exact_item_selection_required",
            notes=(
                "Needed for river-scale granite boulders and boulder-garden shapes "
                "that generic CC0 materials cannot validate alone."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_futaleufu_turquoise_wet_bank_slot",
            asset_need_id="turquoise_wet_bank_materials",
            search_url=(
                "https://www.fab.com/search?q=wet%20river%20bank%20rock%20glacial%20turquoise"
            ),
            role="wet_bank_material_and_color_support_exact_item_required",
            notes=(
                "Needed for wet/dry bank material response and turquoise-water "
                "support assets before corridor substitution."
            ),
        ),
        {
            "candidate_id": "first_party_futaleufu_biome_fallback_v1",
            "asset_need_id": "all_futaleufu_asset_needs",
            "source_family": "First-party procedural",
            "asset_url": "source_manifest://first_party_futaleufu_biome_fallback_v1",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "status": "required_fallback_until_external_assets_pass",
            "role": "missing_external_asset_fallback",
            "notes": (
                "Fallback must remain available for hero canopy, near-bank strata, "
                "granite boulders, and turquoise wet-bank support whenever "
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


def _project_owned_candidate(
    *,
    candidate_id: str,
    asset_need_id: str,
    role: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "asset_need_id": asset_need_id,
        "source_family": "Project-owned procedural",
        "asset_url": "source_manifest://futaleufu_retained_near_bank_strata",
        "license_class": "first_party_committable",
        "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
        "status": "retained_review_evidence_not_production_promoted",
        "role": role,
        "review_evidence": "physics/reports/canopy_strategy/futaleufu_review_history.json",
        "required_before_promotion": [
            "owner canopy-source decision recorded",
            "isolated 60 m and 150 m corridor-distance captures",
            "desktop and VR performance measurements",
            "guide, ecology, art, rights, and hazard-readability review",
        ],
        "notes": notes,
    }


def _asset_need_coverage(
    candidate_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = []
    for asset_need_id, use in RIVER_ASSET_NEEDS[FUTALEUFU_RIVER_ID]["asset_needs"]:
        candidates = [
            candidate
            for candidate in candidate_assets
            if candidate["asset_need_id"] in (asset_need_id, "all_futaleufu_asset_needs")
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
                "has_project_owned_review_candidate": any(
                    candidate["source_family"] == "Project-owned procedural"
                    for candidate in candidates
                ),
                "has_first_party_fallback": any(
                    candidate["source_family"] == "First-party procedural"
                    for candidate in candidates
                ),
                "promotion_status": "blocked_pending_source_hashes_import_captures_and_reviews",
            }
        )
    return coverage
