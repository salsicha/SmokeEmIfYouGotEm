"""Milestone 22 Unreal raft/contact gameplay integration contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA = (
    "raftsim.unreal.raft_contact_authority_integration.v1"
)
MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS = (
    "custom_reduced_authority_integrated_over_approved_custom_cxx_water"
)


@dataclass(frozen=True)
class Milestone22ManifestBuild:
    manifest: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_raft_contact_authority_integration(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the text-first Unreal authority integration manifest."""

    repo_root = repo_root.resolve()
    report_lock_path = repo_root / "physics/reports/milestone20/report_set_lock.json"
    authority_selection_path = (
        repo_root / "physics/reports/milestone19/runtime_authority_selection.json"
    )
    comparison_path = repo_root / "physics/reports/milestone19/chaos_vs_jolt_comparison.json"

    report_lock = _load_json(report_lock_path)
    authority_selection = _load_json(authority_selection_path)
    comparison = _load_json(comparison_path)

    selected_runtime = authority_selection["selected_runtime"]
    water_authority = authority_selection["water_authority"]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA,
        "status": MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS,
        "approved_custom_water": {
            "authority": water_authority,
            "accepted_report_set_lock": "physics/reports/milestone20/report_set_lock.json",
            "lock_hash": report_lock["lock"]["lock_hash"],
            "source_gate_report": report_lock["source_gate"]["report"],
            "source_gate_passed": report_lock["source_gate"]["passed"],
            "live_water_bridge_manifest": (
                "unreal/Content/RaftSim/Physics/live_water_bridge.json"
            ),
            "water_runtime_adapter": "URaftSimWaterRuntimeAdapter",
        },
        "selected_raft_contact_authority": {
            "runtime": selected_runtime,
            "selection_report": (
                "physics/reports/milestone19/runtime_authority_selection.json"
            ),
            "selection_decision": authority_selection["decision"],
            "selection_scope": authority_selection["selection_scope"],
            "chaos_or_jolt_authority_selection_allowed": (
                authority_selection["chaos_or_jolt_authority_selection_allowed"]
            ),
            "comparison_report": authority_selection["comparison_report"],
            "comparison_measured_evidence_available": comparison[
                "measured_evidence_available"
            ],
        },
        "unreal_bridge": {
            "subsystem": "URaftSimPhysicsBridgeSubsystem",
            "fixed_step_bridge_manifest": (
                "unreal/Content/RaftSim/Physics/fixed_step_bridge.json"
            ),
            "raft_runtime_adapter": "URaftSimChronoRuntimeAdapter",
            "legacy_adapter_note": (
                "The adapter class name is retained for compatibility, but its "
                "default runtime is CustomReducedRigidBody for Milestone 22."
            ),
            "water_step_seconds": 0.0166666667,
            "raft_contact_substep_seconds": 0.0083333333,
            "render_tick_may_advance_authority": False,
            "tick_order": [
                "collect_deterministic_inputs",
                "advance_custom_water_solver",
                "sample_water_snapshot_for_raft_patches",
                "apply_forces_to_selected_raft_runtime",
                "step_selected_runtime_substeps",
                "collect_contact_and_force_telemetry",
                "publish_authoritative_raft_state",
            ],
        },
        "chaos_policy": {
            "role": "visual_and_non_authoritative_only",
            "may_drive_scoring_critical_outcomes": False,
            "allowed": [
                "loose_visual_props",
                "splash_debris",
                "background_ropes",
                "shoreline_clutter",
                "non_scoring_breakables",
                "visual_crew_ragdolls",
            ],
            "blocked_until_fixture_suite_passes": [
                "raft_transform_authority",
                "raft_rock_collision_response",
                "raft_bed_grounding",
                "water_force_integration",
                "scoring_critical_rescue_outcomes",
            ],
        },
        "telemetry_contract": {
            "deterministic_capture": (
                "Saved/Automation/RaftSim/Water/live_water_capture.jsonl"
            ),
            "required_fields": [
                "runtime_id",
                "water_frame",
                "raft_pose",
                "linear_velocity",
                "angular_velocity",
                "water_sample_count",
                "contact_event_count",
                "contact_loading",
                "force_breakdown",
                "authority_policy_hash",
            ],
        },
        "replacement_gates": authority_selection["replacement_conditions"],
        "pass_policy": {
            "custom_water_report_lock_required": True,
            "custom_water_source_gate_must_pass": True,
            "selected_runtime_must_match_authority_selection_report": True,
            "chaos_must_remain_visual_only_until_measured_fixture_pass": True,
            "render_interpolation_must_consume_authoritative_state": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)

