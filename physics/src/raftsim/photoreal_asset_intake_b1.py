"""Build the B1 photoreal asset survey and intake contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


B1_ASSET_INTAKE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_asset_intake_b1.json"
)

FAB_EULA_URL = "https://www.fab.com/eula"
POLY_HAVEN_LICENSE_URL = "https://polyhaven.com/license"


RIVER_ASSET_NEEDS = {
    "south_fork_american_chili_bar": {
        "display_name": "South Fork American",
        "biome": "Sierra foothill oak woodland, gray pine, chaparral, granite/metamorphic river rock, summer-dry grass banks",
        "asset_needs": [
            ("sierra_oak_gray_pine_foliage", "hero_and_midground_foliage"),
            ("chaparral_shrub_understory", "understory_and_bank_breakup"),
            ("granite_metamorphic_boulders", "riverbed_boulders_and_banks"),
            ("dry_grass_bank_materials", "near_field_ground_materials"),
        ],
    },
    "colorado_river_grand_canyon_rowing": {
        "display_name": "Colorado River Grand Canyon",
        "biome": "layered sandstone, limestone, schist cliffs, desert scrub, tamarisk/willow, sand beaches, basalt at Lava Falls",
        "asset_needs": [
            ("grand_canyon_layered_cliff_materials", "signature_canyon_walls"),
            ("desert_scrub_riparian_foliage", "tamarisk_willow_cactus_bank_set"),
            ("sand_beach_materials", "camp_beaches_and_edging"),
            ("lava_falls_basalt", "rapid_specific_rock_material"),
        ],
    },
    "pacuare_river_costa_rica": {
        "display_name": "Pacuare River",
        "biome": "tropical rainforest canopy, mossy basalt/andesite boulders, waterfalls, mist and atmosphere",
        "asset_needs": [
            ("multi_strata_tropical_canopy", "hero_and_background_rainforest"),
            ("mossy_basalt_andesite_boulders", "riverbed_and_bank_rocks"),
            ("waterfall_side_stream_assets", "side_streams_and_spray_sources"),
            ("rainforest_floor_and_lianas", "near_field_understory"),
        ],
    },
    "futaleufu_river_chile": {
        "display_name": "Futaleufu River",
        "biome": "Patagonian temperate rainforest, Nothofagus/coigue analogs, granite boulders, turquoise water grading",
        "asset_needs": [
            ("nothofagus_coigue_canopy_or_reviewed_analog", "hero_canopy"),
            ("near_bank_sapling_fern_strata", "retained_project_owned_near_bank_strata"),
            ("patagonian_granite_boulders", "riverbed_and_boulder_gardens"),
            ("turquoise_wet_bank_materials", "river_color_and_wet_bank_support"),
        ],
    },
    "chilko_river_lava_canyon": {
        "display_name": "Chilko River",
        "biome": "interior British Columbia lodgepole/spruce/aspen, glacial-blue water, volcanic canyon rock",
        "asset_needs": [
            ("lodgepole_spruce_aspen_foliage", "river_corridor_forest"),
            ("glacial_blue_wet_bank_materials", "water_and_bank_material_support"),
            ("volcanic_canyon_rock", "lava_canyon_rock_materials"),
            ("cold_water_debris_and_gravel", "near_field_banks_and_bars"),
        ],
    },
}


def _source_candidates(asset_need_id: str) -> list[dict[str, Any]]:
    search_term = asset_need_id.replace("_", " ")
    return [
        {
            "source_family": "Fab",
            "source_url": f"https://www.fab.com/search?q={search_term.replace(' ', '%20')}",
            "license_class": "fab_standard_local_only_until_item_terms_prove_redistributable",
            "repo_binary_policy": "do_not_commit_source_binaries",
            "manifest_policy": "commit_url_license_snapshot_hashes_and_local_import_report",
            "reason": (
                "Fab Standard permits project use and collaborator sharing, but "
                "standalone redistribution is not allowed by default."
            ),
        },
        {
            "source_family": "Poly Haven",
            "source_url": f"https://polyhaven.com/all?q={search_term.replace(' ', '+')}",
            "license_class": "cc0_committable_after_hash_and_attribution_snapshot",
            "repo_binary_policy": "may_commit_source_or_derived_binaries_if_size_is_approved",
            "manifest_policy": "commit_license_url_asset_url_hashes_and_import_report",
            "reason": (
                "Poly Haven assets are CC0; still record provenance, hashes, "
                "source URL, and import settings."
            ),
        },
        {
            "source_family": "First-party procedural",
            "source_url": "source_manifest://first_party_procedural_environment_assets",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
            "manifest_policy": "commit_recipe_seed_tool_version_hashes_and_review_report",
            "reason": "Procedural fallback remains required when external assets are absent.",
        },
    ]


def _river_shopping_list(river_id: str, river: dict[str, Any]) -> dict[str, Any]:
    return {
        "river_id": river_id,
        "display_name": river["display_name"],
        "biome": river["biome"],
        "status": "survey_baseline_not_asset_promotion",
        "asset_needs": [
            {
                "asset_need_id": asset_need_id,
                "use": use,
                "source_candidates": _source_candidates(asset_need_id),
                "promotion_gate": [
                    "item-level license review",
                    "hash-locked source manifest",
                    "isolated Unreal import command/report",
                    "turntable plus 60/150 m river-distance captures",
                    "zero map-check errors",
                    "masked-foliage and Nanite settings reviewed",
                    "procedural fallback preserved",
                ],
            }
            for asset_need_id, use in river["asset_needs"]
        ],
    }


def build_photoreal_asset_intake_b1() -> dict[str, Any]:
    """Build the B1 asset-source survey and intake hardening contract."""

    river_lists = [
        _river_shopping_list(river_id, river)
        for river_id, river in RIVER_ASSET_NEEDS.items()
    ]
    return {
        "schema": "raftsim.photoreal.asset_intake_b1.v1",
        "generated_on": "2026-07-16",
        "status": "survey_baseline_and_intake_contract_recorded_not_assets_imported",
        "production_promoted": False,
        "license_sources_checked": [
            {
                "source_family": "Fab",
                "url": FAB_EULA_URL,
                "checked_on": "2026-07-16",
                "decision": (
                    "Fab Standard assets are allowed for project use only through "
                    "local-only source roots unless item terms prove redistributable."
                ),
            },
            {
                "source_family": "Poly Haven",
                "url": POLY_HAVEN_LICENSE_URL,
                "checked_on": "2026-07-16",
                "decision": (
                    "Poly Haven CC0 assets may be committed after source URL, "
                    "license snapshot, hashes, and import reports are recorded."
                ),
            },
        ],
        "license_classes": {
            "cc0_committable_after_hash_and_attribution_snapshot": {
                "may_commit_source_binaries": True,
                "requires_attribution": False,
                "requires_hash_manifest": True,
            },
            "fab_standard_local_only_until_item_terms_prove_redistributable": {
                "may_commit_source_binaries": False,
                "requires_attribution": False,
                "requires_hash_manifest": True,
                "requires_local_source_root": True,
            },
            "first_party_committable": {
                "may_commit_source_binaries": True,
                "requires_recipe_or_prompt_manifest": True,
                "requires_hash_manifest": True,
            },
        },
        "intake_hardening_contract": {
            "existing_local_source_root_pattern": "RAFTSIM_REVIEWED_*_SOURCE_ROOT",
            "existing_report_path_pattern": "RAFTSIM_REVIEWED_*_REPORT_PATH",
            "new_importers_must": [
                "verify every source file hash before import",
                "write an import report even when assets remain local-only",
                "classify alpha/opacity textures as masks",
                "disable Nanite for masked foliage unless a measured review proves otherwise",
                "use Nanite PreserveArea for opaque woody/rock geometry only when captures pass",
                "preserve procedural fallback when external binaries are absent",
                "avoid committing Fab Standard source binaries to the public repo",
            ],
            "isolated_gate_required": [
                "turntable capture",
                "60 m river-distance capture",
                "150 m river-distance capture",
                "map-check zero errors",
                "source/license/hash report",
                "desktop and VR performance review before corridor substitution",
            ],
        },
        "river_shopping_lists": river_lists,
        "zambezi_policy": {
            "river_id": "zambezi_batoka_gorge",
            "portfolio_role": "additional_active_environment_backlogged",
            "decision": (
                "Retain existing evidence and catalog entries only; do no new "
                "Zambezi asset intake while its terrain/centerline source gate is backlogged."
            ),
        },
        "promotion_gate": {
            "b1_complete_for_planning": True,
            "assets_imported": False,
            "can_promote_any_river_asset_set": False,
            "next_required_actions": [
                "Select item-level assets per river from the shopping lists.",
                "Run each selected asset through a reviewed importer with hash reports.",
                "Capture isolated turntable and 60/150 m evidence.",
                "Preserve procedural fallbacks for missing local-only assets.",
            ],
        },
    }


def write_photoreal_asset_intake_b1(repo_root: Path) -> Path:
    payload = build_photoreal_asset_intake_b1()
    path = repo_root / B1_ASSET_INTAKE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
