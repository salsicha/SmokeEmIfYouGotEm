"""Build the B2 per-river asset-promotion readiness report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_import_capture_review import (
    B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
    build_b2_import_capture_review_ledger,
    build_b2_import_capture_review_validation_report,
)
from .photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    SELECTION_BUILDERS,
    build_b2_source_acquisition_preflight,
)
from .photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_hash_report_template,
    build_b2_source_hash_validation_report,
)
from .photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
    build_b2_source_storage_decision,
)


B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_asset_promotion_readiness_report.json"
)
B2_ASSET_PROMOTION_READINESS_SCHEMA = (
    "raftsim.photoreal.b2_asset_promotion_readiness_report.v1"
)


def build_b2_asset_promotion_readiness_report() -> dict[str, Any]:
    """Build the current per-river B2 promotion-readiness rollup."""

    preflight = build_b2_source_acquisition_preflight()
    storage = build_b2_source_storage_decision()
    source_hash_template = build_b2_source_hash_report_template()
    source_hash_validation = build_b2_source_hash_validation_report(
        source_hash_template
    )
    import_ledger = build_b2_import_capture_review_ledger()
    import_validation = build_b2_import_capture_review_validation_report(
        import_ledger
    )
    source_records_by_river = _source_hash_records_by_river(source_hash_template)
    import_records_by_river = _import_records_by_river(import_ledger)
    source_failures_by_river = _failures_by_river(
        source_hash_validation["failing_record_ids"]
    )
    import_failures_by_river = _failures_by_river(
        import_validation["failing_record_ids"]
    )
    manifests = [_manifest_summary(short_id, path, build()) for short_id, path, build in SELECTION_BUILDERS]
    rivers = [
        _river_readiness(
            manifest,
            source_records_by_river.get(manifest["river_id"], []),
            import_records_by_river.get(manifest["river_id"], []),
            source_failures_by_river.get(manifest["river_id"], []),
            import_failures_by_river.get(manifest["river_id"], []),
        )
        for manifest in manifests
    ]
    ready_count = sum(1 for river in rivers if river["promotion_ready"])
    return {
        "schema": B2_ASSET_PROMOTION_READINESS_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "b2_asset_promotion_readiness_blocked_missing_source_import_capture_review_evidence",
        "production_promoted": False,
        "source_artifacts": {
            "source_acquisition_preflight": B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
            "source_storage_decision": B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
            "source_hash_report_template": B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
            "source_hash_validation_report": B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
            "import_capture_review_ledger": B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
            "import_capture_review_validation_report": B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
        },
        "global_gate_status": {
            "source_downloads_allowed_now": storage["current_operating_mode"][
                "downloads_allowed_now"
            ],
            "source_binaries_allowed_in_repo_now": storage[
                "current_operating_mode"
            ]["source_binaries_allowed_in_repo_now"],
            "source_hashes_valid": source_hash_validation["source_hashes_valid"],
            "import_capture_reviews_valid": import_validation[
                "import_reviews_valid"
            ],
            "can_promote_any_b2_asset_set": False,
        },
        "summary": {
            "river_count": len(rivers),
            "ready_river_count": ready_count,
            "blocked_river_count": len(rivers) - ready_count,
            "selection_manifest_count": preflight["selection_manifest_count"],
            "source_hash_record_count": source_hash_validation["summary"][
                "required_hash_record_count"
            ],
            "source_hash_failing_record_count": source_hash_validation[
                "failing_record_count"
            ],
            "import_review_record_count": import_validation["summary"][
                "import_review_record_count"
            ],
            "import_review_failing_record_count": import_validation[
                "failing_record_count"
            ],
        },
        "rivers": rivers,
        "promotion_gate": {
            "can_mark_south_fork_b2_complete": False,
            "can_mark_colorado_b2_complete": False,
            "can_mark_pacuare_b2_complete": False,
            "can_mark_futaleufu_b2_complete": False,
            "can_mark_chilko_b2_complete": False,
            "can_run_corridor_substitution": False,
            "complete_when": [
                "the per-river source-hash records validate",
                "the per-river import/capture review records validate",
                "the river-specific ecology/guide/art/rights/hazard/performance reviews pass",
                "corridor substitution is explicitly enabled by the river manifest",
                "the full per-river asset set is manually approved for promotion",
            ],
        },
    }


def write_b2_asset_promotion_readiness_report(repo_root: Path) -> Path:
    payload = build_b2_asset_promotion_readiness_report()
    path = repo_root / B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _manifest_summary(
    short_id: str,
    relative_path: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "short_id": short_id,
        "relative_path": relative_path,
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "candidate_asset_count": manifest["candidate_asset_count"],
        "production_promoted": manifest["production_promoted"],
        "assets_downloaded": manifest["assets_downloaded"],
        "assets_imported": manifest["assets_imported"],
        "corridor_substitution_allowed": manifest["corridor_substitution_allowed"],
    }


def _river_readiness(
    manifest: dict[str, Any],
    source_records: list[dict[str, Any]],
    import_records: list[dict[str, Any]],
    source_failures: list[str],
    import_failures: list[str],
) -> dict[str, Any]:
    gates = {
        "selection_manifest_not_promoted": not manifest["production_promoted"],
        "source_assets_downloaded": manifest["assets_downloaded"],
        "source_assets_imported": manifest["assets_imported"],
        "source_hash_records_valid": not source_failures and bool(source_records),
        "import_capture_reviews_valid": not import_failures and bool(import_records),
        "corridor_substitution_allowed": manifest["corridor_substitution_allowed"],
        "desktop_vr_performance_reviewed": False,
        "human_ecology_guide_art_rights_hazard_reviewed": False,
    }
    promotion_ready = (
        gates["source_assets_downloaded"]
        and gates["source_assets_imported"]
        and gates["source_hash_records_valid"]
        and gates["import_capture_reviews_valid"]
        and gates["corridor_substitution_allowed"]
        and gates["desktop_vr_performance_reviewed"]
        and gates["human_ecology_guide_art_rights_hazard_reviewed"]
    )
    return {
        "river_id": manifest["river_id"],
        "display_name": manifest["display_name"],
        "selection_manifest": manifest["relative_path"],
        "candidate_asset_count": manifest["candidate_asset_count"],
        "source_hash_record_count": len(source_records),
        "source_hash_failing_record_count": len(source_failures),
        "import_review_record_count": len(import_records),
        "import_review_failing_record_count": len(import_failures),
        "gate_status": gates,
        "promotion_ready": promotion_ready,
        "blocking_reasons": _blocking_reasons(gates, source_failures, import_failures),
        "next_required_actions": [
            "Fill and validate source hash records for every selected source candidate.",
            "Attach Unreal import reports and hash-locked isolated captures.",
            "Pass rights, ecology/guide, art, technical-art, hazard, and desktop/VR performance review.",
            "Enable corridor substitution only after reviewed source evidence and river-specific approval exist.",
        ],
    }


def _blocking_reasons(
    gates: dict[str, bool],
    source_failures: list[str],
    import_failures: list[str],
) -> list[str]:
    reasons = []
    if not gates["source_assets_downloaded"]:
        reasons.append("source_assets_not_downloaded_or_recorded")
    if not gates["source_assets_imported"]:
        reasons.append("source_assets_not_imported")
    if source_failures:
        reasons.append("source_hash_records_have_failures")
    if import_failures:
        reasons.append("import_capture_review_records_have_failures")
    if not gates["corridor_substitution_allowed"]:
        reasons.append("corridor_substitution_not_allowed")
    if not gates["desktop_vr_performance_reviewed"]:
        reasons.append("desktop_vr_performance_review_missing")
    if not gates["human_ecology_guide_art_rights_hazard_reviewed"]:
        reasons.append("human_domain_reviews_missing")
    return reasons


def _source_hash_records_by_river(
    source_hash_template: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    records_by_river: dict[str, list[dict[str, Any]]] = {}
    for group in (
        source_hash_template["cc0_hash_records"],
        source_hash_template["fab_local_only_hash_records"],
        source_hash_template["first_party_recipe_hash_records"],
    ):
        for record in group:
            records_by_river.setdefault(record["river_id"], []).append(record)
    return records_by_river


def _import_records_by_river(
    import_ledger: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    records_by_river: dict[str, list[dict[str, Any]]] = {}
    for record in import_ledger["records"]:
        records_by_river.setdefault(record["river_id"], []).append(record)
    return records_by_river


def _failures_by_river(failing_record_ids: list[str]) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    for record_id in failing_record_ids:
        river_id = record_id.split(":", maxsplit=1)[0]
        failures.setdefault(river_id, []).append(record_id)
    return failures
