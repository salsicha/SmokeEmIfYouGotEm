"""Build the Pacuare B2 photoreal asset-selection manifest."""

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


PACUARE_B2_ASSET_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/asset_intake/"
    "pacuare_b2_asset_selection_manifest.json"
)
PACUARE_B2_ASSET_SELECTION_SCHEMA = "raftsim.photoreal.pacuare_asset_selection_b2.v1"
PACUARE_RIVER_ID = "pacuare_river_costa_rica"


def build_pacuare_b2_asset_selection() -> dict[str, Any]:
    """Build the first Pacuare B2 item-level asset-selection package."""

    river = RIVER_ASSET_NEEDS[PACUARE_RIVER_ID]
    candidate_assets = _candidate_assets()
    coverage = _asset_need_coverage(candidate_assets)
    return {
        "schema": PACUARE_B2_ASSET_SELECTION_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": PACUARE_RIVER_ID,
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
                "CC0 mossy rock, moss, and tropical shrub candidates still need downloaded source hashes and importer reports.",
                "Pacuare rainforest species identity, canopy layering, lianas, epiphytes, and protected-area ecology still need guide/ecology review.",
                "Waterfall side-stream, spray, mist, and wet-wall assets still need exact local-only or first-party selections.",
                "No isolated turntable, 60 m, 150 m, map-check, desktop, or VR evidence exists for the new selections.",
            ],
            "next_required_actions": [
                "Download the selected CC0 candidates into reviewed source roots and hash every source file.",
                "Pick exact local-only Fab or first-party hero assets for canopy strata, lianas, epiphytes, waterfalls, spray, and mist.",
                "Run the B1 importer command for each selected asset set and write fail-closed import reports.",
                "Capture isolated turntable plus 60 m and 150 m river-distance evidence before any corridor substitution.",
                "Record guide, ecology, art, rights, protected-area, hazard-readability, and desktop/VR performance reviews.",
            ],
        },
    }


def write_pacuare_b2_asset_selection(repo_root: Path) -> Path:
    payload = build_pacuare_b2_asset_selection()
    path = repo_root / PACUARE_B2_ASSET_SELECTION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _candidate_assets() -> list[dict[str, Any]]:
    return [
        _poly_haven_candidate(
            candidate_id="polyhaven_pachira_aquatica_01",
            asset_need_id="multi_strata_tropical_canopy",
            asset_url="https://polyhaven.com/a/pachira_aquatica_01",
            role="tropical_shrub_and_broadleaf_structure_trial",
            notes=(
                "Selected as a rights-clear tropical broadleaf shrub/understory "
                "structure candidate; not Costa Rica rainforest species authority "
                "and not sufficient as a full multi-strata canopy."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_mossy_rock",
            asset_need_id="mossy_basalt_andesite_boulders",
            asset_url="https://polyhaven.com/a/mossy_rock",
            role="mossy_wet_rock_surface_material_trial",
            notes=(
                "Selected for moss, lichen, cracks, and wet-rock surface review; "
                "not basalt/andesite geology authority for Pacuare boulders."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_rock_moss_set_02",
            asset_need_id="mossy_basalt_andesite_boulders",
            asset_url="https://polyhaven.com/a/rock_moss_set_02",
            role="moss_covered_boulder_geometry_trial",
            notes=(
                "Selected as a generic mossy boulder geometry candidate for "
                "isolated scale and material review; exact Pacuare lithology is "
                "still blocked on source and guide review."
            ),
        ),
        _poly_haven_candidate(
            candidate_id="polyhaven_moss_01",
            asset_need_id="rainforest_floor_and_lianas",
            asset_url="https://polyhaven.com/a/moss_01",
            role="rainforest_floor_moss_groundcover_trial",
            notes=(
                "Selected for dense mossy ground-cover review near wet banks and "
                "boulders; it does not replace lianas, epiphytes, roots, or leaf "
                "litter hero assets."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_pacuare_multi_strata_rainforest_canopy_slot",
            asset_need_id="multi_strata_tropical_canopy",
            search_url=(
                "https://www.fab.com/search?q=tropical%20rainforest%20canopy%20jungle%20foliage"
            ),
            role="rainforest_canopy_exact_item_selection_required",
            notes=(
                "Needed for layered canopy, large leaf massing, trunk density, "
                "and humid gorge silhouette where CC0 analogs are insufficient."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_pacuare_mossy_basalt_andesite_boulder_slot",
            asset_need_id="mossy_basalt_andesite_boulders",
            search_url="https://www.fab.com/search?q=mossy%20basalt%20andesite%20boulder",
            role="mossy_river_boulder_exact_item_selection_required",
            notes=(
                "Needed for river-scale wet boulder shapes and dark volcanic "
                "stone identity; exact item-level license review remains open."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_pacuare_waterfall_mist_vfx_slot",
            asset_need_id="waterfall_side_stream_assets",
            search_url="https://www.fab.com/search?q=waterfall%20mist%20spray%20vfx",
            role="waterfall_spray_mist_exact_item_selection_required",
            notes=(
                "Needed for side-stream waterfalls, plunge mist, wet wall sheets, "
                "and spray cards/Niagara systems before corridor substitution."
            ),
        ),
        _fab_local_only_slot(
            candidate_id="fab_pacuare_lianas_epiphytes_understory_slot",
            asset_need_id="rainforest_floor_and_lianas",
            search_url=(
                "https://www.fab.com/search?q=liana%20vine%20epiphyte%20rainforest%20understory"
            ),
            role="lianas_epiphytes_understory_exact_item_selection_required",
            notes=(
                "Needed for hanging vines, epiphytes, roots, leaf litter, and "
                "understory breakup; exact item-level license review is open."
            ),
        ),
        {
            "candidate_id": "first_party_pacuare_biome_fallback_v1",
            "asset_need_id": "all_pacuare_asset_needs",
            "source_family": "First-party procedural",
            "asset_url": "source_manifest://first_party_pacuare_biome_fallback_v1",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "status": "required_fallback_until_external_assets_pass",
            "role": "missing_external_asset_fallback",
            "notes": (
                "Fallback must remain available for rainforest canopy, wet rocks, "
                "side-stream waterfalls, mist, and lianas whenever local-only Fab "
                "binaries are absent or CC0 candidates fail review."
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
            "guide, ecology, art, rights, protected-area, and hazard-readability review",
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
            "guide, ecology, art, rights, protected-area, and hazard-readability review",
        ],
        "notes": notes,
    }


def _asset_need_coverage(
    candidate_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = []
    for asset_need_id, use in RIVER_ASSET_NEEDS[PACUARE_RIVER_ID]["asset_needs"]:
        candidates = [
            candidate
            for candidate in candidate_assets
            if candidate["asset_need_id"] in (asset_need_id, "all_pacuare_asset_needs")
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
