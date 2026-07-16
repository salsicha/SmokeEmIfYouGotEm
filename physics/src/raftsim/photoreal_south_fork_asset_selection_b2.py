"""Build the South Fork B2 photoreal asset-selection manifest."""

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


SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/asset_intake/"
    "south_fork_b2_asset_selection_manifest.json"
)
SOUTH_FORK_B2_ASSET_SELECTION_SCHEMA = (
    "raftsim.photoreal.south_fork_asset_selection_b2.v1"
)
SOUTH_FORK_RIVER_ID = "south_fork_american_chili_bar"


def build_south_fork_b2_asset_selection() -> dict[str, Any]:
    """Build the first South Fork B2 item-level asset-selection package."""

    river = RIVER_ASSET_NEEDS[SOUTH_FORK_RIVER_ID]
    candidate_assets = _candidate_assets()
    coverage = _asset_need_coverage(candidate_assets)
    return {
        "schema": SOUTH_FORK_B2_ASSET_SELECTION_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": SOUTH_FORK_RIVER_ID,
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
                "CC0 candidates still need downloaded source hashes and importer reports.",
                "Sierra foothill hero foliage still needs exact item-level local-only or first-party selections.",
                "Previous Poly Haven fir and Tree Small 02 trials are retained as rejected evidence, not promoted assets.",
                "No isolated turntable, 60 m, 150 m, map-check, desktop, or VR evidence exists for the new selections.",
            ],
            "next_required_actions": [
                "Download the selected CC0 candidates into reviewed source roots and hash every source file.",
                "Pick exact local-only Fab or first-party hero foliage assets for blue/interior live oak, gray pine, and chaparral massing.",
                "Run the B1 importer command for each selected asset set and write fail-closed import reports.",
                "Capture isolated turntable plus 60 m and 150 m river-distance evidence before any corridor substitution.",
                "Record ecology, guide, art, rights, hazard-readability, and desktop/VR performance reviews.",
            ],
        },
    }


def write_south_fork_b2_asset_selection(repo_root: Path) -> Path:
    payload = build_south_fork_b2_asset_selection()
    path = repo_root / SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _candidate_assets() -> list[dict[str, Any]]:
    return [
        _poly_haven_candidate(
            candidate_id="polyhaven_rock_01",
            asset_need_id="granite_metamorphic_boulders",
            asset_url="https://polyhaven.com/a/rock_01",
            role="weathered_gray_rock_surface_material_trial",
            notes=(
                "Selected as a rights-clear generic gray/weathered rock material "
                "candidate for boulder and bank-surface shader trials; not geology "
                "authority for final South Fork rocks."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_leafy_grass",
            asset_need_id="dry_grass_bank_materials",
            asset_url="https://polyhaven.com/a/leafy_grass",
            role="leaf_litter_and_grass_bank_surface_trial",
            notes=(
                "Selected for near-bank ground material review where summer-dry "
                "grass, leaf litter, and small twigs are needed under the source drape."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_grass_medium_01",
            asset_need_id="dry_grass_bank_materials",
            asset_url="https://polyhaven.com/a/grass_medium_01",
            role="grass_tuft_geometry_trial_primary",
            notes=(
                "Selected as a CC0 ground-cover geometry candidate; foliage "
                "alpha must remain non-Nanite unless measured review proves otherwise."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_grass_medium_02",
            asset_need_id="chaparral_shrub_understory",
            asset_url="https://polyhaven.com/a/grass_medium_02",
            role="low_understory_grass_geometry_trial_secondary",
            notes=(
                "Selected as a secondary low-understory breakup candidate, not as "
                "a chaparral shrub replacement."
            ),
        ),
        {
            "candidate_id": "polyhaven_fir_tree_01_1k",
            "asset_need_id": "sierra_oak_gray_pine_foliage",
            "source_family": "Poly Haven",
            "asset_url": "https://polyhaven.com/a/fir_tree_01",
            "license_class": "cc0_committable_after_hash_and_attribution_snapshot",
            "repo_binary_policy": "already_reviewed_keep_existing_evidence_only",
            "status": "rejected_visual_promotion_retain_as_import_pipeline_evidence",
            "role": "rejected_conifer_pipeline_checkpoint",
            "review_evidence": (
                "docs/environment-captures/photoreal_river_previews/"
                "landscape_candidates/polyhaven_fir_tree_01_visual_comparison_review.json"
            ),
            "notes": (
                "Previous isolated South Fork comparison removed the worst PVE "
                "conifer silhouettes but read as sparse poles at gameplay distance."
            ),
        },
        {
            "candidate_id": "polyhaven_tree_small_02_1k",
            "asset_need_id": "sierra_oak_gray_pine_foliage",
            "source_family": "Poly Haven",
            "asset_url": "https://polyhaven.com/a/tree_small_02",
            "license_class": "cc0_committable_after_hash_and_attribution_snapshot",
            "repo_binary_policy": "already_reviewed_keep_existing_evidence_only",
            "status": "rejected_visual_promotion_retain_as_import_pipeline_evidence",
            "role": "rejected_broadleaf_structure_analog_checkpoint",
            "review_evidence": (
                "docs/environment-captures/photoreal_river_previews/"
                "landscape_candidates/polyhaven_tree_small_02_visual_comparison_review.json"
            ),
            "notes": (
                "Previous isolated South Fork comparison validated the import path "
                "but rejected the pale sparse canopy and non-native identity."
            ),
        },
        _fab_local_only_slot(
            candidate_id="fab_blue_oak_gray_pine_hero_foliage_slot",
            asset_need_id="sierra_oak_gray_pine_foliage",
            search_url="https://www.fab.com/search?q=california%20oak%20gray%20pine",
            role="hero_foliage_exact_item_selection_required",
            notes=(
                "Poly Haven does not cover the needed blue/interior live oak plus "
                "gray pine species mix. Exact Fab items must be selected locally, "
                "license-recorded, and kept out of the public repo unless the item "
                "terms prove redistributable."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_chaparral_shrub_understory_slot",
            asset_need_id="chaparral_shrub_understory",
            search_url="https://www.fab.com/search?q=chaparral%20shrub%20scrub",
            role="chaparral_exact_item_selection_required",
            notes=(
                "Needed for manzanita/ceanothus/buckbrush-style bank breakup and "
                "dry scrub massing; exact item-level license review is still open."
            ),
        ),
        {
            "candidate_id": "first_party_south_fork_biome_fallback_v1",
            "asset_need_id": "all_south_fork_asset_needs",
            "source_family": "First-party procedural",
            "asset_url": "source_manifest://first_party_south_fork_biome_fallback_v1",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "status": "required_fallback_until_external_assets_pass",
            "role": "missing_external_asset_fallback",
            "notes": (
                "Fallback must remain available whenever local-only Fab binaries "
                "are absent or CC0 candidates fail visual/performance review."
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
            "art, ecology, guide, rights, and hazard-readability review",
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
            "art, ecology, guide, rights, and hazard-readability review",
        ],
        "notes": notes,
    }


def _asset_need_coverage(
    candidate_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = []
    for asset_need_id, use in RIVER_ASSET_NEEDS[SOUTH_FORK_RIVER_ID]["asset_needs"]:
        candidates = [
            candidate
            for candidate in candidate_assets
            if candidate["asset_need_id"] in (asset_need_id, "all_south_fork_asset_needs")
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
