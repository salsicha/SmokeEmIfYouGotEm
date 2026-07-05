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
MILESTONE22_CONTACT_TELEMETRY_SCHEMA = "raftsim.unreal.raft_contact_telemetry.v1"
MILESTONE22_CONTACT_TELEMETRY_STATUS = (
    "contact_families_and_telemetry_ready_for_authoritative_runtime_wiring"
)
MILESTONE22_CREW_WEIGHT_SCHEMA = "raftsim.unreal.crew_weight_distribution.v1"
MILESTONE22_CREW_WEIGHT_STATUS = (
    "crew_seating_weight_shift_and_outcome_modifiers_ready_for_runtime_wiring"
)
MILESTONE22_CREW_SAFETY_SCHEMA = "raftsim.unreal.crew_overboard_safety_states.v1"
MILESTONE22_CREW_SAFETY_STATUS = (
    "crew_overboard_safety_states_ready_for_rescue_gameplay_wiring"
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


def build_raft_contact_response_telemetry(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 raft/contact response telemetry manifest."""

    repo_root = repo_root.resolve()
    authority_integration_path = (
        repo_root / "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
    )
    rock_presets_path = repo_root / "unreal/Content/RaftSim/Physics/rock_contact_presets.json"
    bed_presets_path = repo_root / "unreal/Content/RaftSim/Physics/bed_grounding_presets.json"
    collision_sources_path = (
        repo_root / "unreal/Content/RaftSim/Physics/collision_geometry_sources.json"
    )

    authority = _load_json(authority_integration_path)
    rock_presets = _load_json(rock_presets_path)
    bed_presets = _load_json(bed_presets_path)
    collision_sources = _load_json(collision_sources_path)

    telemetry_fields = [
        "event_id",
        "runtime_id",
        "frame",
        "contact_family",
        "surface_class",
        "feature_id",
        "raft_patch_id",
        "contact_point_world_m",
        "contact_normal",
        "penetration_depth_m",
        "normal_impulse_n_s",
        "tangent_impulse_n_s",
        "restitution",
        "normal_stiffness",
        "normal_damping",
        "tangential_friction",
        "rolling_friction",
        "stick_slip_state",
        "contact_loading_n",
        "release_threshold_n",
        "release_ratio",
        "roll_moment_n_m",
        "outcome",
    ]

    contact_families = [
        {
            "family_id": "raft_rock",
            "feature_types": ["rock"],
            "material_presets": ["rock_elastic_default"],
            "expected_outcomes": ["deflect", "bounce", "scrape", "pin_risk"],
        },
        {
            "family_id": "bank_scrape",
            "feature_types": ["bank"],
            "material_presets": ["bank_elastic_scrape"],
            "expected_outcomes": ["scrape", "deflect", "pin_risk"],
        },
        {
            "family_id": "ledge_launch",
            "feature_types": ["ledge"],
            "material_presets": ["ledge_elastic_launch"],
            "expected_outcomes": ["bounce", "launch", "flip_risk"],
        },
        {
            "family_id": "shallow_shelf",
            "feature_types": ["shallow"],
            "material_presets": ["bed_inelastic_shallow_shelf"],
            "expected_outcomes": ["ground", "pivot", "release", "flip_risk"],
        },
        {
            "family_id": "bed_grounding",
            "feature_types": ["riverbed"],
            "material_presets": ["bed_inelastic_default"],
            "expected_outcomes": ["ground", "scrape", "drag", "unstick"],
        },
        {
            "family_id": "boulder_garden",
            "feature_types": ["rock", "riverbed"],
            "material_presets": ["rock_elastic_default", "bed_inelastic_default"],
            "expected_outcomes": ["multi_contact_loading", "deflect", "pin_risk"],
        },
        {
            "family_id": "pin_release",
            "feature_types": ["rock", "shallow", "strainer"],
            "material_presets": [
                "rock_elastic_default",
                "bed_inelastic_shallow_shelf",
                "strainer_high_friction_pin",
            ],
            "expected_outcomes": ["pin", "hold", "release", "failed_release"],
        },
        {
            "family_id": "surf_flush",
            "feature_types": ["hydraulic_hole", "standing_wave", "eddy_line"],
            "material_presets": ["water_feature_contact"],
            "expected_outcomes": ["surf", "side_surf", "flush", "flip_risk"],
        },
        {
            "family_id": "flip",
            "feature_types": ["rock", "ledge", "shallow", "hydraulic_hole"],
            "material_presets": [
                "rock_elastic_default",
                "ledge_elastic_launch",
                "bed_inelastic_shallow_shelf",
                "water_feature_contact",
            ],
            "expected_outcomes": ["flip_risk", "flip", "recovered_by_high_side"],
        },
    ]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_CONTACT_TELEMETRY_SCHEMA,
        "status": MILESTONE22_CONTACT_TELEMETRY_STATUS,
        "authority_integration": (
            "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
        ),
        "selected_runtime": authority["selected_raft_contact_authority"]["runtime"],
        "water_authority": authority["approved_custom_water"]["authority"],
        "source_manifests": {
            "rock_contact_presets": "unreal/Content/RaftSim/Physics/rock_contact_presets.json",
            "bed_grounding_presets": (
                "unreal/Content/RaftSim/Physics/bed_grounding_presets.json"
            ),
            "collision_geometry_sources": (
                "unreal/Content/RaftSim/Physics/collision_geometry_sources.json"
            ),
        },
        "source_preset_counts": {
            "rock_contact_presets": len(rock_presets["presets"]),
            "bed_grounding_presets": len(bed_presets["presets"]),
            "collision_feature_types": len(collision_sources["feature_types"]),
        },
        "contact_families": contact_families,
        "telemetry_schema": {
            "event_struct": "FRaftSimRaftContactTelemetryEvent",
            "summary_struct": "FRaftSimRaftContactRuntimeSummary",
            "required_fields": telemetry_fields,
        },
        "runtime_thresholds": {
            "pin_release_requires_release_threshold": True,
            "surf_flush_requires_flow_feature_state": True,
            "flip_requires_roll_moment_and_recovery_window": True,
            "stick_slip_requires_velocity_and_hysteresis": True,
        },
        "pass_policy": {
            "all_named_contact_families_present": True,
            "all_events_record_material_response": True,
            "all_release_paths_record_thresholds": True,
            "contact_telemetry_published_with_authoritative_raft_state": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)


def build_crew_weight_distribution_manifest(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 crew weight-distribution gameplay manifest."""

    repo_root = repo_root.resolve()
    crew_seats_path = repo_root / "unreal/Content/RaftSim/Network/crew_seats_roles.json"
    input_actions_path = repo_root / "unreal/Content/RaftSim/Input/enhanced_input_actions.json"
    voice_grammar_path = repo_root / "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"
    contact_telemetry_path = (
        repo_root / "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
    )

    crew_seats = _load_json(crew_seats_path)
    input_actions = _load_json(input_actions_path)
    voice_grammar = _load_json(voice_grammar_path)
    contact_telemetry = _load_json(contact_telemetry_path)

    playable_seats = [
        seat for seat in crew_seats["seats"] if seat["role"] != "spectator_scout"
    ]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_CREW_WEIGHT_SCHEMA,
        "status": MILESTONE22_CREW_WEIGHT_STATUS,
        "source_manifests": {
            "crew_seats_roles": "unreal/Content/RaftSim/Network/crew_seats_roles.json",
            "input_actions": "unreal/Content/RaftSim/Input/enhanced_input_actions.json",
            "voice_command_grammar": (
                "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"
            ),
            "contact_response_telemetry": (
                "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
            ),
        },
        "runtime_contract": {
            "module": "RaftSimCrew",
            "evaluator": "URaftSimCrewWeightDistributionLibrary::EvaluateWeightDistribution",
            "input_structs": [
                "FRaftSimCrewSeatOccupancy",
                "FRaftSimCrewWeightShiftCommand",
            ],
            "output_struct": "FRaftSimCrewWeightDistributionFrame",
            "solver_consumer": "URaftSimPhysicsBridgeSubsystem",
        },
        "seating_model": {
            "seat_count": len(playable_seats),
            "default_passenger_mass_kg": 82.0,
            "seats": [
                {
                    "seat_id": seat["seat_id"],
                    "role": seat["role"],
                    "local_position_m": seat["local_position_m"],
                    "can_be_human": seat["can_be_human"],
                    "can_ai_fill": seat["can_ai_fill"],
                }
                for seat in playable_seats
            ],
        },
        "weight_shift_actions": [
            {
                "action_id": "brace",
                "crew_intent": "crew_brace",
                "cog_offset_m": [0.0, 0.0, -0.12],
                "effect": "lowers_center_of_gravity_and_reduces_flip_risk",
            },
            {
                "action_id": "lean_left",
                "crew_intent": "crew_lean_left",
                "cog_offset_m": [0.0, -0.28, 0.0],
                "effect": "moves_center_of_gravity_left_for_angle_and_pin_control",
            },
            {
                "action_id": "lean_right",
                "crew_intent": "crew_lean_right",
                "cog_offset_m": [0.0, 0.28, 0.0],
                "effect": "moves_center_of_gravity_right_for_angle_and_pin_control",
            },
            {
                "action_id": "high_side_left",
                "crew_intent": "crew_high_side_left",
                "cog_offset_m": [0.0, -0.55, 0.08],
                "effect": "creates_large_lateral_roll_moment_for_pin_flip_release_outcomes",
            },
            {
                "action_id": "high_side_right",
                "crew_intent": "crew_high_side_right",
                "cog_offset_m": [0.0, 0.55, 0.08],
                "effect": "creates_large_lateral_roll_moment_for_pin_flip_release_outcomes",
            },
        ],
        "outcome_coupling": {
            "contact_telemetry_schema": contact_telemetry["schema"],
            "uses_contact_families": ["pin_release", "surf_flush", "flip"],
            "outputs": [
                "center_of_gravity_local_m",
                "roll_moment_n_m",
                "pin_load_modifier",
                "flip_risk_modifier",
                "release_assist_modifier",
                "brace_count",
                "high_side_count",
            ],
        },
        "source_action_coverage": {
            "input_action_ids": [
                action["action_id"] for action in input_actions["actions"]
            ],
            "voice_intents": [
                command["crew_intent"] for command in voice_grammar["commands"]
            ],
        },
        "pass_policy": {
            "all_playable_seats_have_mass_and_local_position": True,
            "brace_lean_and_high_side_shift_center_of_gravity": True,
            "weight_distribution_modifies_pin_flip_release_outcomes": True,
            "deterministic_inputs_and_voice_commands_cover_weight_shift_actions": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)


def build_crew_overboard_safety_states_manifest(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 crew-overboard safety-state manifest."""

    repo_root = repo_root.resolve()
    contact_telemetry_path = (
        repo_root / "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
    )
    crew_weight_path = repo_root / "unreal/Content/RaftSim/Crew/crew_weight_distribution.json"
    voice_grammar_path = repo_root / "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"

    contact_telemetry = _load_json(contact_telemetry_path)
    crew_weight = _load_json(crew_weight_path)
    voice_grammar = _load_json(voice_grammar_path)

    states = [
        {
            "state_id": "seated",
            "description": "Passenger is in an assigned raft seat and can paddle, brace, lean, or high-side.",
        },
        {
            "state_id": "at_risk",
            "description": "Passenger remains in the raft but contact, roll, fear, or missed brace timing makes ejection possible.",
        },
        {
            "state_id": "falling_ejected",
            "description": "Passenger has left the seat and is transitioning toward water contact.",
        },
        {
            "state_id": "swimming",
            "description": "Passenger is in the river and drifting as an active rescue target candidate.",
        },
        {
            "state_id": "rescue_targeted",
            "description": "Guide or crew has selected the swimmer for reach, paddle, throw-line, or pull-in action.",
        },
        {
            "state_id": "rescued",
            "description": "Swimmer is secured at the raft or by a rescue action but not fully re-seated.",
        },
        {
            "state_id": "reseated_recovered",
            "description": "Passenger is back in a usable raft state and can resume crew actions after recovery delay.",
        },
        {
            "state_id": "failed_rescue",
            "description": "Rescue window failed or swimmer left recoverable bounds, causing safety-score collapse.",
        },
    ]

    transitions = [
        ["seated", "at_risk"],
        ["at_risk", "seated"],
        ["at_risk", "falling_ejected"],
        ["falling_ejected", "swimming"],
        ["swimming", "rescue_targeted"],
        ["rescue_targeted", "rescued"],
        ["rescued", "reseated_recovered"],
        ["swimming", "failed_rescue"],
        ["rescue_targeted", "failed_rescue"],
        ["reseated_recovered", "seated"],
    ]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_CREW_SAFETY_SCHEMA,
        "status": MILESTONE22_CREW_SAFETY_STATUS,
        "source_manifests": {
            "contact_response_telemetry": (
                "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
            ),
            "crew_weight_distribution": "unreal/Content/RaftSim/Crew/crew_weight_distribution.json",
            "voice_command_grammar": (
                "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"
            ),
        },
        "runtime_contract": {
            "module": "RaftSimCrew",
            "state_enum": "ERaftSimCrewSafetyState",
            "frame_struct": "FRaftSimCrewSafetyStateFrame",
            "transition_struct": "FRaftSimCrewSafetyTransition",
            "transition_library": "URaftSimCrewSafetyStateLibrary::CanTransitionSafetyState",
        },
        "states": states,
        "allowed_transitions": [
            {"from": source, "to": target} for source, target in transitions
        ],
        "transition_triggers": {
            "at_risk": [
                "contact_loading_n_above_threshold",
                "flip_risk_modifier_above_threshold",
                "missed_brace_or_high_side_window",
            ],
            "falling_ejected": [
                "roll_moment_n_m_above_ejection_threshold",
                "unseated_contact_impulse",
                "failed_hold_on_check",
            ],
            "swimming": ["water_contact_confirmed", "raft_separation_started"],
            "rescue_targeted": ["guide_rescue_intent", "crew_rescue_intent"],
            "rescued": ["reach_grab_success", "paddle_grab_success", "throw_line_success"],
            "reseated_recovered": ["pull_in_complete", "recovery_delay_complete"],
            "failed_rescue": [
                "rescue_window_expired",
                "swimmer_out_of_recoverable_bounds",
                "critical_fatigue_or_panic",
            ],
        },
        "telemetry_fields": [
            "passenger_id",
            "seat_id",
            "previous_state",
            "current_state",
            "transition_reason",
            "source_contact_event_id",
            "center_of_gravity_local_m",
            "time_in_state_seconds",
            "time_in_water_seconds",
            "rescue_target_priority",
            "failed_rescue_reason",
        ],
        "source_contract_summary": {
            "contact_schema": contact_telemetry["schema"],
            "crew_weight_schema": crew_weight["schema"],
            "voice_rescue_intents": [
                command["crew_intent"]
                for command in voice_grammar["commands"]
                if command["crew_intent"] in {"crew_rescue", "crew_recovery"}
            ],
        },
        "pass_policy": {
            "all_required_states_present": True,
            "all_state_changes_emit_transition_telemetry": True,
            "failed_rescue_is_terminal_until_reset": True,
            "recovered_passenger_requires_reseat_before_normal_crew_actions": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)
