"""Build B1 idempotent photoreal asset-set intake command manifests."""

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


B1_ASSET_SET_INTAKE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_asset_set_intake_b1.json"
)


def build_photoreal_asset_set_intake_b1(repo_root: Path) -> dict[str, Any]:
    """Build one idempotent intake command contract for every B1 asset set."""

    asset_sets = [
        _asset_set_command(river_id, river, asset_need_id, use, repo_root)
        for river_id, river in RIVER_ASSET_NEEDS.items()
        for asset_need_id, use in river["asset_needs"]
    ]
    return {
        "schema": "raftsim.photoreal.asset_set_intake_b1.v1",
        "generated_on": "2026-07-16",
        "status": "idempotent_asset_set_intake_commands_recorded_not_assets_imported",
        "source_contract": B1_ASSET_INTAKE_RELATIVE_PATH,
        "production_promoted": False,
        "assets_imported": False,
        "asset_set_count": len(asset_sets),
        "license_sources": [
            {"source_family": "Fab", "url": FAB_EULA_URL},
            {"source_family": "Poly Haven", "url": POLY_HAVEN_LICENSE_URL},
        ],
        "global_importer_hardening": {
            "hash_locked_report_required": True,
            "alpha_opacity_textures_as_masks": True,
            "masked_foliage_nanite_disabled_by_default": True,
            "nanite_preserve_area_only_for_reviewed_opaque_woody_or_rock": True,
            "procedural_fallback_required": True,
            "turntable_capture_required": True,
            "river_distance_captures_required_m": [60, 150],
            "map_check_zero_errors_required": True,
            "desktop_and_vr_performance_review_required": True,
            "may_commit_fab_standard_source_binaries": False,
        },
        "unreal_command_contract": {
            "runner": "UnrealEditor-Cmd",
            "project": "unreal/RaftSim.uproject",
            "script_argument": "-ExecutePythonScript",
            "existing_importer_script_candidates": [
                "unreal/Scripts/import_reviewed_biome_asset.py",
                "unreal/Scripts/import_reviewed_rock_asset.py",
                "unreal/Scripts/import_reviewed_rock_ground_detail_asset.py",
                "unreal/Scripts/import_reviewed_terrain_detail_asset.py",
            ],
            "command_status": (
                "generated_per_asset_set_command_shape; selected item-level "
                "asset may still require a specialized importer binding before execution"
            ),
        },
        "asset_sets": asset_sets,
        "promotion_gate": {
            "b1_hardening_complete_for_planning": True,
            "can_promote_any_river_asset_set": False,
            "next_required_actions": [
                "Pick item-level assets for B2 per river.",
                "Bind the correct existing or specialized Unreal importer script.",
                "Fill source hash expectations from reviewed local or CC0 sources.",
                "Run the generated command and attach isolated review captures.",
            ],
        },
    }


def write_photoreal_asset_set_intake_b1(repo_root: Path) -> Path:
    """Write the B1 per-asset-set intake command manifest."""

    payload = build_photoreal_asset_set_intake_b1(repo_root)
    path = repo_root / B1_ASSET_SET_INTAKE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _asset_set_command(
    river_id: str,
    river: dict[str, Any],
    asset_need_id: str,
    use: str,
    repo_root: Path,
) -> dict[str, Any]:
    env_prefix = _env_prefix(river_id, asset_need_id)
    report_path = (
        f"Saved/RaftSim/AssetIntake/{river_id}/{asset_need_id}_import_report.json"
    )
    source_manifest = (
        f"physics/data/real_world/{river_id}/asset_intake/{asset_need_id}_source_manifest.json"
    )
    review_report = (
        f"docs/environment-captures/photoreal_river_previews/asset_intake/"
        f"{river_id}_{asset_need_id}_review.json"
    )
    importer_script = _importer_script_for(asset_need_id)
    return {
        "asset_set_id": f"{river_id}:{asset_need_id}",
        "river_id": river_id,
        "display_name": river["display_name"],
        "biome": river["biome"],
        "asset_need_id": asset_need_id,
        "use": use,
        "status": "intake_command_recorded_no_asset_selected",
        "license_boundary": {
            "fab_standard": "local_only_source_binaries_until_item_terms_prove_redistributable",
            "poly_haven": "cc0_committable_after_hash_and_license_snapshot",
            "first_party": "committable_with_recipe_seed_tool_version_and_hashes",
        },
        "environment": {
            "source_root_env": f"{env_prefix}_SOURCE_ROOT",
            "report_path_env": f"{env_prefix}_REPORT_PATH",
            "reimport_env": f"{env_prefix}_REIMPORT",
            "default_report_path": report_path,
        },
        "planned_outputs": {
            "source_manifest": source_manifest,
            "isolated_review_report": review_report,
            "unreal_destination_root": (
                f"/Game/RaftSim/Environment/ExternalReview/"
                f"{_pascal_case(river_id)}/{_pascal_case(asset_need_id)}"
            ),
        },
        "command": {
            "working_directory": "unreal",
            "script": importer_script,
            "template": (
                f"{env_prefix}_SOURCE_ROOT=/path/to/reviewed/source "
                f"{env_prefix}_REPORT_PATH={report_path} "
                "UnrealEditor-Cmd RaftSim.uproject "
                f"-ExecutePythonScript=Scripts/{Path(importer_script).name}"
            ),
            "idempotency": [
                "verify source hashes before import",
                "reuse existing imported assets unless reimport env is set to 1",
                "write report on success and failure",
                "never promote into corridor maps from this command alone",
            ],
        },
        "importer_hardening": {
            "alpha_opacity_textures_as_masks": True,
            "masked_foliage_nanite_disabled_by_default": "foliage" in asset_need_id
            or "canopy" in asset_need_id
            or "forest" in asset_need_id
            or "shrub" in asset_need_id
            or "lianas" in asset_need_id,
            "nanite_preserve_area_only_for_reviewed_opaque_woody_or_rock": True,
            "procedural_fallback_required": True,
            "isolated_gate_required": [
                "turntable",
                "60m_river_distance",
                "150m_river_distance",
                "map_check_zero_errors",
                "desktop_and_vr_performance_review",
            ],
        },
        "source_candidates": _source_candidates(asset_need_id),
        "promotion_allowed": False,
    }


def _source_candidates(asset_need_id: str) -> list[dict[str, Any]]:
    search_term = asset_need_id.replace("_", " ")
    return [
        {
            "source_family": "Fab",
            "source_url": f"https://www.fab.com/search?q={search_term.replace(' ', '%20')}",
            "license_class": "fab_standard_local_only_until_item_terms_prove_redistributable",
            "repo_binary_policy": "do_not_commit_source_binaries",
        },
        {
            "source_family": "Poly Haven",
            "source_url": f"https://polyhaven.com/all?q={search_term.replace(' ', '+')}",
            "license_class": "cc0_committable_after_hash_and_attribution_snapshot",
            "repo_binary_policy": "may_commit_source_or_derived_binaries_if_size_is_approved",
        },
        {
            "source_family": "First-party procedural",
            "source_url": "source_manifest://first_party_procedural_environment_assets",
            "license_class": "first_party_committable",
            "repo_binary_policy": "may_commit_generated_outputs_when_manifested",
        },
    ]


def _importer_script_for(asset_need_id: str) -> str:
    if any(token in asset_need_id for token in ("boulder", "rock", "basalt", "granite")):
        return "unreal/Scripts/import_reviewed_rock_asset.py"
    if any(token in asset_need_id for token in ("grass", "ground", "sand", "bank", "beach")):
        return "unreal/Scripts/import_reviewed_rock_ground_detail_asset.py"
    if any(token in asset_need_id for token in ("cliff", "canyon")):
        return "unreal/Scripts/import_reviewed_terrain_detail_asset.py"
    return "unreal/Scripts/import_reviewed_biome_asset.py"


def _env_prefix(river_id: str, asset_need_id: str) -> str:
    return "RAFTSIM_REVIEWED_" + _env_token(f"{river_id}_{asset_need_id}")


def _env_token(value: str) -> str:
    return "".join(character.upper() if character.isalnum() else "_" for character in value)


def _pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)
