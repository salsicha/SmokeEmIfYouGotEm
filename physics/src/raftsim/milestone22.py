"""Milestone 22 Unreal raft/contact gameplay integration contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA = (
    "raftsim.unreal.raft_contact_authority_integration.v2"
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
MILESTONE22_SWIMMING_SKILL_SCHEMA = "raftsim.unreal.swimming_skill_assignment.v1"
MILESTONE22_SWIMMING_SKILL_STATUS = (
    "passenger_swimming_skill_assignment_ready_for_run_setup"
)
MILESTONE22_SWIMMER_RESCUE_SCHEMA = "raftsim.unreal.swimmer_rescue_gameplay.v1"
MILESTONE22_SWIMMER_RESCUE_STATUS = (
    "swimmer_drift_rescue_and_recovery_ready_for_runtime_wiring"
)
MILESTONE22_GAMEPLAY_SCORING_SCHEMA = "raftsim.unreal.gameplay_telemetry_scoring.v1"
MILESTONE22_GAMEPLAY_SCORING_STATUS = (
    "gameplay_telemetry_and_scoring_ready_for_vertical_slice"
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

    live_water_approved = bool(report_lock.get("passed")) and bool(
        report_lock.get("production_use", {}).get(
            "live_water_unreal_bridge_foundation_unblocked"
        )
    )
    manifest: dict[str, Any] = {
        "schema": MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA,
        "status": (
            MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS
            if live_water_approved
            else "raft_contact_integrated_over_frozen_water_live_custom_water_blocked"
        ),
        "custom_water_evidence": {
            "candidate_authority": water_authority,
            "live_water_approved": live_water_approved,
            "operating_mode": (
                "live_custom_cxx_water"
                if live_water_approved
                else "frozen_validation_snapshot_only"
            ),
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


def write_raft_contact_authority_integration(
    repo_root: Path,
    output_path: Path | None = None,
) -> Milestone22ManifestBuild:
    """Generate the authority manifest from the current report lock and selection."""

    root = repo_root.resolve()
    generated = build_raft_contact_authority_integration(root)
    target = output_path or (
        root / "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return generated


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
        "water_authority": authority["custom_water_evidence"]["candidate_authority"],
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


def build_swimming_skill_assignment_manifest(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 passenger swimming-skill assignment manifest."""

    repo_root = repo_root.resolve()
    personas_path = repo_root / "unreal/Content/RaftSim/AI/crew_personas.json"
    safety_states_path = (
        repo_root / "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
    )

    personas = _load_json(personas_path)
    safety_states = _load_json(safety_states_path)

    skill_levels = [
        {
            "skill_id": "non_swimmer",
            "display_name": "Non-swimmer",
            "self_rescue_allowed": False,
            "panic_scalar": 1.0,
            "rescue_priority": 1.0,
            "pull_in_difficulty": 1.2,
            "time_to_critical_seconds": 8.0,
        },
        {
            "skill_id": "weak_swimmer",
            "display_name": "Weak swimmer",
            "self_rescue_allowed": True,
            "panic_scalar": 0.75,
            "rescue_priority": 0.8,
            "pull_in_difficulty": 1.05,
            "time_to_critical_seconds": 14.0,
        },
        {
            "skill_id": "average_swimmer",
            "display_name": "Average swimmer",
            "self_rescue_allowed": True,
            "panic_scalar": 0.45,
            "rescue_priority": 0.55,
            "pull_in_difficulty": 0.9,
            "time_to_critical_seconds": 22.0,
        },
        {
            "skill_id": "strong_swimmer",
            "display_name": "Strong swimmer",
            "self_rescue_allowed": True,
            "panic_scalar": 0.25,
            "rescue_priority": 0.35,
            "pull_in_difficulty": 0.75,
            "time_to_critical_seconds": 32.0,
        },
    ]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_SWIMMING_SKILL_SCHEMA,
        "status": MILESTONE22_SWIMMING_SKILL_STATUS,
        "source_manifests": {
            "crew_personas": "unreal/Content/RaftSim/AI/crew_personas.json",
            "crew_overboard_safety_states": (
                "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
            ),
        },
        "runtime_contract": {
            "module": "RaftSimCrew",
            "skill_enum": "ERaftSimSwimmingSkillLevel",
            "profile_struct": "FRaftSimSwimmingSkillProfile",
            "assignment_struct": "FRaftSimPassengerSwimmingSkillAssignment",
            "assignment_library": (
                "URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue"
            ),
        },
        "assignment_policy": {
            "mode": "per_run_seeded_random_or_roster_override",
            "deterministic_seed_sources": [
                "run_seed",
                "river_id",
                "section_id",
                "passenger_id",
                "seat_id",
            ],
            "default_distribution": {
                "non_swimmer": 0.15,
                "weak_swimmer": 0.25,
                "average_swimmer": 0.45,
                "strong_swimmer": 0.15,
            },
            "record_assignment_in_replay": True,
        },
        "skill_levels": skill_levels,
        "roster_entries": [
            {
                "passenger_id": persona["passenger_id"],
                "display_name": persona["display_name"],
                "roster_override_allowed": True,
                "default_assignment": "per_run_seeded_random",
            }
            for persona in personas["personas"]
        ],
        "gameplay_effects": {
            "non_swimmers_cannot_self_rescue": True,
            "affects_panic": True,
            "affects_rescue_priority": True,
            "affects_pull_in_difficulty": True,
            "affects_safety_score": True,
            "linked_safety_state_schema": safety_states["schema"],
        },
        "telemetry_fields": [
            "passenger_id",
            "seat_id",
            "skill_level",
            "assigned_from_roster",
            "assignment_seed",
            "self_rescue_allowed",
            "panic_scalar",
            "rescue_priority",
            "pull_in_difficulty",
            "time_to_critical_seconds",
        ],
        "pass_policy": {
            "non_swimmer_skill_level_required": True,
            "non_swimmers_cannot_self_rescue": True,
            "assignments_are_seeded_or_roster_recorded": True,
            "skill_affects_rescue_priority_and_safety_scoring": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)


def build_swimmer_rescue_gameplay_manifest(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 swimmer drift and rescue gameplay manifest."""

    repo_root = repo_root.resolve()
    safety_states_path = (
        repo_root / "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
    )
    swimming_skill_path = (
        repo_root / "unreal/Content/RaftSim/Crew/swimming_skill_assignment.json"
    )
    input_actions_path = repo_root / "unreal/Content/RaftSim/Input/enhanced_input_actions.json"
    voice_grammar_path = repo_root / "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"

    safety_states = _load_json(safety_states_path)
    swimming_skill = _load_json(swimming_skill_path)
    input_actions = _load_json(input_actions_path)
    voice_grammar = _load_json(voice_grammar_path)

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_SWIMMER_RESCUE_SCHEMA,
        "status": MILESTONE22_SWIMMER_RESCUE_STATUS,
        "source_manifests": {
            "crew_overboard_safety_states": (
                "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
            ),
            "swimming_skill_assignment": (
                "unreal/Content/RaftSim/Crew/swimming_skill_assignment.json"
            ),
            "input_actions": "unreal/Content/RaftSim/Input/enhanced_input_actions.json",
            "voice_command_grammar": (
                "unreal/Content/RaftSim/AI/guide_voice_command_grammar.json"
            ),
        },
        "runtime_contract": {
            "module": "RaftSimCrew",
            "rescue_method_enum": "ERaftSimRescueMethod",
            "swimmer_frame_struct": "FRaftSimSwimmerRescueFrame",
            "rescue_attempt_struct": "FRaftSimRescueAttempt",
            "rescue_library": "URaftSimSwimmerRescueLibrary",
        },
        "swimmer_model": {
            "drift_source": "custom_cxx_water_velocity_sample_plus_swimmer_drag",
            "visibility_factors": [
                "distance_from_raft",
                "foam_or_spray_occlusion",
                "guide_line_of_sight",
                "callout_recentness",
            ],
            "callout_priorities": [
                "non_swimmer",
                "long_time_in_water",
                "approaching_hazard",
                "low_visibility",
            ],
        },
        "rescue_methods": [
            {
                "method": "reach_grab",
                "max_distance_m": 1.2,
                "requires_throw_line": False,
                "pull_in_seconds": 2.5,
            },
            {
                "method": "paddle_grab",
                "max_distance_m": 2.0,
                "requires_throw_line": False,
                "pull_in_seconds": 3.5,
            },
            {
                "method": "throw_line",
                "max_distance_m": 8.0,
                "requires_throw_line": True,
                "pull_in_seconds": 6.0,
            },
        ],
        "input_and_voice_coverage": {
            "input_action_ids": [
                action["action_id"] for action in input_actions["actions"]
            ],
            "voice_intents": [
                command["crew_intent"] for command in voice_grammar["commands"]
            ],
        },
        "recovery_effects": {
            "successful_rescue_transitions": ["rescue_targeted", "rescued", "reseated_recovered"],
            "failed_rescue_transitions": ["swimming", "failed_rescue"],
            "fatigue_delta_on_success": 0.08,
            "fatigue_delta_on_failure": 0.35,
            "trust_delta_on_success": 0.08,
            "trust_delta_on_failure": -0.25,
            "non_swimmer_priority_uses_skill_schema": swimming_skill["schema"],
            "linked_safety_state_schema": safety_states["schema"],
        },
        "telemetry_fields": [
            "passenger_id",
            "swimmer_world_position_m",
            "swimmer_drift_velocity_mps",
            "visibility_score",
            "callout_priority",
            "rescue_target_rank",
            "rescue_method",
            "throw_line_available",
            "time_in_water_seconds",
            "rescue_window_seconds",
            "pull_in_progress",
            "reseat_recovery_seconds",
            "fatigue_delta",
            "trust_delta",
            "failed_rescue_reason",
        ],
        "pass_policy": {
            "swimmer_drift_is_water_velocity_driven": True,
            "target_selection_prioritizes_non_swimmers_and_low_visibility": True,
            "reach_paddle_and_throw_line_methods_are_supported": True,
            "pull_in_reseat_and_failed_rescue_emit_telemetry": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)


def build_gameplay_telemetry_scoring_manifest(repo_root: Path) -> Milestone22ManifestBuild:
    """Build the Milestone 22 gameplay telemetry and scoring manifest."""

    repo_root = repo_root.resolve()
    source_paths = {
        "authority_integration": (
            repo_root / "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
        ),
        "contact_response": (
            repo_root / "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
        ),
        "crew_weight_distribution": (
            repo_root / "unreal/Content/RaftSim/Crew/crew_weight_distribution.json"
        ),
        "crew_safety_states": (
            repo_root / "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
        ),
        "swimming_skill_assignment": (
            repo_root / "unreal/Content/RaftSim/Crew/swimming_skill_assignment.json"
        ),
        "swimmer_rescue_gameplay": (
            repo_root / "unreal/Content/RaftSim/Crew/swimmer_rescue_gameplay.json"
        ),
    }
    sources = {key: _load_json(path) for key, path in source_paths.items()}

    telemetry_categories = [
        {
            "category_id": "safety",
            "fields": [
                "safety_incident_count",
                "failed_rescue_count",
                "contact_loading_peak_n",
            ],
        },
        {
            "category_id": "line_choice",
            "fields": ["clean_line_ratio", "hazard_avoidance_ratio", "eddy_recovery_used"],
        },
        {
            "category_id": "boat_angle",
            "fields": ["mean_angle_error_degrees", "max_angle_error_degrees"],
        },
        {
            "category_id": "paddle_efficiency",
            "fields": ["useful_paddle_impulse_ratio", "missed_stroke_count"],
        },
        {
            "category_id": "command_timing",
            "fields": ["mean_command_latency_seconds", "late_command_count"],
        },
        {
            "category_id": "high_side_brace_timing",
            "fields": ["timing_error_seconds", "successful_counterplay_count"],
        },
        {
            "category_id": "swims_and_rescue",
            "fields": [
                "swim_count",
                "rescue_method",
                "time_in_water_seconds",
                "crew_recovery_seconds",
            ],
        },
    ]

    manifest: dict[str, Any] = {
        "schema": MILESTONE22_GAMEPLAY_SCORING_SCHEMA,
        "status": MILESTONE22_GAMEPLAY_SCORING_STATUS,
        "source_manifests": {
            "authority_integration": (
                "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
            ),
            "contact_response": (
                "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
            ),
            "crew_weight_distribution": (
                "unreal/Content/RaftSim/Crew/crew_weight_distribution.json"
            ),
            "crew_safety_states": (
                "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
            ),
            "swimming_skill_assignment": (
                "unreal/Content/RaftSim/Crew/swimming_skill_assignment.json"
            ),
            "swimmer_rescue_gameplay": (
                "unreal/Content/RaftSim/Crew/swimmer_rescue_gameplay.json"
            ),
        },
        "runtime_contract": {
            "module": "RaftSimCrew",
            "signals_struct": "FRaftSimGameplayScoringSignals",
            "breakdown_struct": "FRaftSimGameplayScoreBreakdown",
            "scoring_library": "URaftSimGameplayScoringLibrary::EvaluateGameplayScore",
        },
        "telemetry_categories": telemetry_categories,
        "score_weights": {
            "safety": 0.30,
            "line_choice": 0.18,
            "boat_angle": 0.14,
            "paddle_efficiency": 0.12,
            "command_timing": 0.10,
            "high_side_brace_timing": 0.08,
            "swims_and_rescue": 0.08,
        },
        "score_inputs": [
            "safety_incident_count",
            "clean_line_ratio",
            "mean_angle_error_degrees",
            "useful_paddle_impulse_ratio",
            "mean_command_latency_seconds",
            "high_side_brace_timing_error_seconds",
            "swim_count",
            "rescue_method",
            "time_in_water_seconds",
            "crew_recovery_seconds",
            "failed_rescue_count",
        ],
        "source_contract_summary": {
            key: value["schema"] for key, value in sources.items()
        },
        "pass_policy": {
            "all_milestone22_gameplay_systems_feed_scoring": True,
            "safety_and_failed_rescue_can_dominate_score": True,
            "line_choice_boat_angle_and_paddle_efficiency_are_separate": True,
            "command_timing_and_high_side_brace_timing_are_recorded": True,
            "swims_rescue_method_time_in_water_and_recovery_are_scored": True,
        },
    }
    return Milestone22ManifestBuild(manifest=manifest)


def write_gameplay_telemetry_scoring_manifest(
    repo_root: Path,
    output_path: Path | None = None,
) -> Milestone22ManifestBuild:
    """Generate the gameplay scoring manifest from the current Milestone 22 contracts."""

    root = repo_root.resolve()
    generated = build_gameplay_telemetry_scoring_manifest(root)
    target = output_path or (
        root / "unreal/Content/RaftSim/Crew/gameplay_telemetry_scoring.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(generated.manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return generated
