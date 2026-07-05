import json
from pathlib import Path

from raftsim.milestone22 import (
    MILESTONE22_CREW_SAFETY_SCHEMA,
    MILESTONE22_CREW_SAFETY_STATUS,
    MILESTONE22_CREW_WEIGHT_SCHEMA,
    MILESTONE22_CREW_WEIGHT_STATUS,
    MILESTONE22_CONTACT_TELEMETRY_SCHEMA,
    MILESTONE22_CONTACT_TELEMETRY_STATUS,
    MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA,
    MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS,
    MILESTONE22_SWIMMER_RESCUE_SCHEMA,
    MILESTONE22_SWIMMER_RESCUE_STATUS,
    MILESTONE22_SWIMMING_SKILL_SCHEMA,
    MILESTONE22_SWIMMING_SKILL_STATUS,
    build_crew_overboard_safety_states_manifest,
    build_crew_weight_distribution_manifest,
    build_raft_contact_authority_integration,
    build_raft_contact_response_telemetry,
    build_swimmer_rescue_gameplay_manifest,
    build_swimming_skill_assignment_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_INTEGRATION_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json"
)
REPORT_SET_LOCK_PATH = REPO_ROOT / "physics/reports/milestone20/report_set_lock.json"
AUTHORITY_SELECTION_PATH = (
    REPO_ROOT / "physics/reports/milestone19/runtime_authority_selection.json"
)
PHYSICS_AUTHORITY_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Physics/physics_authority_policy.json"
)
RAFT_RUNTIME_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/raft_dynamics_runtime.json"
FIXED_STEP_BRIDGE_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/fixed_step_bridge.json"
CONTACT_TELEMETRY_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Physics/raft_contact_response_telemetry.json"
)
CREW_WEIGHT_DISTRIBUTION_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Crew/crew_weight_distribution.json"
)
CREW_SAFETY_STATES_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json"
)
SWIMMING_SKILL_ASSIGNMENT_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Crew/swimming_skill_assignment.json"
)
SWIMMER_RESCUE_GAMEPLAY_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Crew/swimmer_rescue_gameplay.json"
)
PHYSICS_BRIDGE_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimPhysicsBridgeSubsystem.h"
)
RAFT_RUNTIME_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimChronoRuntimeAdapter.h"
)


def test_raft_contact_authority_integration_manifest_matches_generator():
    expected = build_raft_contact_authority_integration(REPO_ROOT).manifest
    committed = json.loads(AUTHORITY_INTEGRATION_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA
    assert committed["status"] == MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS


def test_raft_contact_authority_integration_uses_approved_custom_water_and_runtime():
    manifest = json.loads(AUTHORITY_INTEGRATION_PATH.read_text(encoding="utf-8"))
    report_lock = json.loads(REPORT_SET_LOCK_PATH.read_text(encoding="utf-8"))
    authority_selection = json.loads(AUTHORITY_SELECTION_PATH.read_text(encoding="utf-8"))
    physics_authority = json.loads(PHYSICS_AUTHORITY_PATH.read_text(encoding="utf-8"))
    raft_runtime = json.loads(RAFT_RUNTIME_PATH.read_text(encoding="utf-8"))
    fixed_step = json.loads(FIXED_STEP_BRIDGE_PATH.read_text(encoding="utf-8"))

    assert manifest["approved_custom_water"]["authority"] == (
        "custom_cxx_shallow_water_solver"
    )
    assert manifest["approved_custom_water"]["lock_hash"] == report_lock["lock"][
        "lock_hash"
    ]
    assert manifest["approved_custom_water"]["source_gate_passed"] is True
    assert {
        manifest["selected_raft_contact_authority"]["runtime"],
        authority_selection["selected_runtime"],
        physics_authority["authoritative"]["raft_kinematics"],
        physics_authority["authoritative"]["contacts"],
        raft_runtime["selected_runtime"],
        fixed_step["authority"]["raft_kinematics"],
    } == {"CustomReducedRigidBody"}
    assert manifest["pass_policy"]["custom_water_report_lock_required"] is True
    assert manifest["pass_policy"]["selected_runtime_must_match_authority_selection_report"] is True


def test_chaos_stays_visual_only_until_authority_fixture_pass():
    manifest = json.loads(AUTHORITY_INTEGRATION_PATH.read_text(encoding="utf-8"))
    chaos_policy = manifest["chaos_policy"]

    assert chaos_policy["role"] == "visual_and_non_authoritative_only"
    assert chaos_policy["may_drive_scoring_critical_outcomes"] is False
    assert "visual_crew_ragdolls" in chaos_policy["allowed"]
    assert "raft_transform_authority" in chaos_policy[
        "blocked_until_fixture_suite_passes"
    ]
    assert "scoring_critical_rescue_outcomes" in chaos_policy[
        "blocked_until_fixture_suite_passes"
    ]
    assert manifest["pass_policy"][
        "chaos_must_remain_visual_only_until_measured_fixture_pass"
    ] is True


def test_unreal_bridge_exposes_milestone22_authority_policy_contract():
    bridge_header = PHYSICS_BRIDGE_HEADER_PATH.read_text(encoding="utf-8")
    raft_header = RAFT_RUNTIME_HEADER_PATH.read_text(encoding="utf-8")

    assert "FRaftSimRaftAuthorityIntegrationPolicy" in raft_header
    assert "bChaosMayDriveScoringCriticalPhysics" in raft_header
    assert "SelectedRuntime" in raft_header
    assert "CustomReducedRigidBody" in raft_header
    assert "GetAuthorityIntegrationPolicy" in bridge_header
    assert "AuthorityIntegrationPolicy" in bridge_header


def test_raft_contact_response_telemetry_manifest_matches_generator():
    expected = build_raft_contact_response_telemetry(REPO_ROOT).manifest
    committed = json.loads(CONTACT_TELEMETRY_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_CONTACT_TELEMETRY_SCHEMA
    assert committed["status"] == MILESTONE22_CONTACT_TELEMETRY_STATUS


def test_raft_contact_response_telemetry_covers_milestone22_contact_families():
    manifest = json.loads(CONTACT_TELEMETRY_PATH.read_text(encoding="utf-8"))
    family_ids = {family["family_id"] for family in manifest["contact_families"]}

    assert family_ids == {
        "raft_rock",
        "bank_scrape",
        "ledge_launch",
        "shallow_shelf",
        "bed_grounding",
        "boulder_garden",
        "pin_release",
        "surf_flush",
        "flip",
    }
    for family in manifest["contact_families"]:
        assert family["feature_types"]
        assert family["material_presets"]
        assert family["expected_outcomes"]


def test_raft_contact_response_telemetry_requires_material_and_release_fields():
    manifest = json.loads(CONTACT_TELEMETRY_PATH.read_text(encoding="utf-8"))
    fields = set(manifest["telemetry_schema"]["required_fields"])

    assert {
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
    }.issubset(fields)
    assert manifest["runtime_thresholds"]["pin_release_requires_release_threshold"] is True
    assert manifest["runtime_thresholds"]["flip_requires_roll_moment_and_recovery_window"] is True


def test_unreal_contact_contract_exposes_authoritative_telemetry_events():
    contact_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimContactMaterials.h"
    ).read_text(encoding="utf-8")
    bridge_header = PHYSICS_BRIDGE_HEADER_PATH.read_text(encoding="utf-8")

    assert "ERaftSimContactOutcome" in contact_header
    assert "FRaftSimRaftContactTelemetryEvent" in contact_header
    assert "FRaftSimRaftContactRuntimeSummary" in contact_header
    for field in (
        "Restitution",
        "NormalDamping",
        "TangentialFriction",
        "bStickSlipActive",
        "ContactLoadingNewtons",
        "ReleaseThresholdNewtons",
        "ReleaseRatio",
        "RollMomentNewtonMeters",
    ):
        assert field in contact_header
    assert "ContactTelemetryEvents" in bridge_header
    assert "RecordContactTelemetryEvent" in bridge_header


def test_crew_weight_distribution_manifest_matches_generator():
    expected = build_crew_weight_distribution_manifest(REPO_ROOT).manifest
    committed = json.loads(CREW_WEIGHT_DISTRIBUTION_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_CREW_WEIGHT_SCHEMA
    assert committed["status"] == MILESTONE22_CREW_WEIGHT_STATUS


def test_crew_weight_distribution_manifest_covers_seats_and_weight_shift_actions():
    manifest = json.loads(CREW_WEIGHT_DISTRIBUTION_PATH.read_text(encoding="utf-8"))
    seat_ids = {seat["seat_id"] for seat in manifest["seating_model"]["seats"]}
    action_ids = {action["action_id"] for action in manifest["weight_shift_actions"]}

    assert manifest["seating_model"]["seat_count"] == 6
    assert {"stern_guide", "bow_left", "bow_right", "mid_left", "mid_right"}.issubset(
        seat_ids
    )
    assert action_ids == {
        "brace",
        "lean_left",
        "lean_right",
        "high_side_left",
        "high_side_right",
    }
    assert manifest["outcome_coupling"]["uses_contact_families"] == [
        "pin_release",
        "surf_flush",
        "flip",
    ]


def test_crew_weight_distribution_has_input_and_voice_coverage():
    manifest = json.loads(CREW_WEIGHT_DISTRIBUTION_PATH.read_text(encoding="utf-8"))
    coverage = manifest["source_action_coverage"]

    assert "PaddleBrace" in coverage["input_action_ids"]
    assert "HighSide" in coverage["input_action_ids"]
    assert "CrewLean" in coverage["input_action_ids"]
    assert "crew_brace" in coverage["voice_intents"]
    assert "crew_high_side" in coverage["voice_intents"]
    assert "crew_lean_left" in coverage["voice_intents"]
    assert "crew_lean_right" in coverage["voice_intents"]


def test_unreal_crew_weight_distribution_contract_exposes_cog_and_outcome_modifiers():
    header_text = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimCrew/Public/RaftSimCrewStateContracts.h"
    ).read_text(encoding="utf-8")

    assert "ERaftSimCrewWeightShiftAction" in header_text
    assert "FRaftSimCrewSeatOccupancy" in header_text
    assert "FRaftSimCrewWeightShiftCommand" in header_text
    assert "FRaftSimCrewWeightDistributionFrame" in header_text
    assert "URaftSimCrewWeightDistributionLibrary" in header_text
    for field in (
        "CenterOfGravityLocalMeters",
        "RollMomentNewtonMeters",
        "PinLoadModifier",
        "FlipRiskModifier",
        "ReleaseAssistModifier",
    ):
        assert field in header_text


def test_crew_overboard_safety_states_manifest_matches_generator():
    expected = build_crew_overboard_safety_states_manifest(REPO_ROOT).manifest
    committed = json.loads(CREW_SAFETY_STATES_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_CREW_SAFETY_SCHEMA
    assert committed["status"] == MILESTONE22_CREW_SAFETY_STATUS


def test_crew_overboard_safety_states_cover_required_state_machine():
    manifest = json.loads(CREW_SAFETY_STATES_PATH.read_text(encoding="utf-8"))
    state_ids = {state["state_id"] for state in manifest["states"]}
    transitions = {
        (transition["from"], transition["to"])
        for transition in manifest["allowed_transitions"]
    }

    assert state_ids == {
        "seated",
        "at_risk",
        "falling_ejected",
        "swimming",
        "rescue_targeted",
        "rescued",
        "reseated_recovered",
        "failed_rescue",
    }
    assert ("at_risk", "falling_ejected") in transitions
    assert ("falling_ejected", "swimming") in transitions
    assert ("swimming", "rescue_targeted") in transitions
    assert ("rescue_targeted", "rescued") in transitions
    assert ("rescued", "reseated_recovered") in transitions
    assert ("swimming", "failed_rescue") in transitions


def test_crew_overboard_safety_states_require_transition_telemetry():
    manifest = json.loads(CREW_SAFETY_STATES_PATH.read_text(encoding="utf-8"))
    fields = set(manifest["telemetry_fields"])

    assert {
        "passenger_id",
        "seat_id",
        "previous_state",
        "current_state",
        "transition_reason",
        "time_in_water_seconds",
        "rescue_target_priority",
        "failed_rescue_reason",
    }.issubset(fields)
    assert manifest["pass_policy"]["failed_rescue_is_terminal_until_reset"] is True
    assert manifest["source_contract_summary"]["voice_rescue_intents"] == [
        "crew_rescue",
        "crew_recovery",
    ]


def test_unreal_crew_safety_state_contract_exposes_overboard_state_machine():
    header_text = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimCrew/Public/RaftSimCrewStateContracts.h"
    ).read_text(encoding="utf-8")

    assert "ERaftSimCrewSafetyState" in header_text
    for state in (
        "Seated",
        "AtRisk",
        "FallingEjected",
        "Swimming",
        "RescueTargeted",
        "Rescued",
        "ReseatedRecovered",
        "FailedRescue",
    ):
        assert state in header_text
    assert "FRaftSimCrewSafetyStateFrame" in header_text
    assert "FRaftSimCrewSafetyTransition" in header_text
    assert "CanTransitionSafetyState" in header_text


def test_swimming_skill_assignment_manifest_matches_generator():
    expected = build_swimming_skill_assignment_manifest(REPO_ROOT).manifest
    committed = json.loads(SWIMMING_SKILL_ASSIGNMENT_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_SWIMMING_SKILL_SCHEMA
    assert committed["status"] == MILESTONE22_SWIMMING_SKILL_STATUS


def test_swimming_skill_assignment_manifest_covers_non_swimmers_and_roster_policy():
    manifest = json.loads(SWIMMING_SKILL_ASSIGNMENT_PATH.read_text(encoding="utf-8"))
    levels = {level["skill_id"]: level for level in manifest["skill_levels"]}

    assert set(levels) == {
        "non_swimmer",
        "weak_swimmer",
        "average_swimmer",
        "strong_swimmer",
    }
    assert levels["non_swimmer"]["self_rescue_allowed"] is False
    assert levels["non_swimmer"]["rescue_priority"] == 1.0
    assert manifest["assignment_policy"]["mode"] == "per_run_seeded_random_or_roster_override"
    assert manifest["assignment_policy"]["record_assignment_in_replay"] is True
    assert len(manifest["roster_entries"]) >= 3


def test_swimming_skill_assignment_manifest_records_gameplay_and_telemetry_effects():
    manifest = json.loads(SWIMMING_SKILL_ASSIGNMENT_PATH.read_text(encoding="utf-8"))
    fields = set(manifest["telemetry_fields"])

    assert manifest["gameplay_effects"]["non_swimmers_cannot_self_rescue"] is True
    assert manifest["gameplay_effects"]["affects_rescue_priority"] is True
    assert manifest["gameplay_effects"]["affects_safety_score"] is True
    assert {
        "skill_level",
        "assigned_from_roster",
        "assignment_seed",
        "self_rescue_allowed",
        "panic_scalar",
        "rescue_priority",
        "pull_in_difficulty",
        "time_to_critical_seconds",
    }.issubset(fields)


def test_unreal_swimming_skill_contract_exposes_non_swimmer_assignment():
    header_text = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimCrew/Public/RaftSimCrewStateContracts.h"
    ).read_text(encoding="utf-8")

    assert "ERaftSimSwimmingSkillLevel" in header_text
    assert "NonSwimmer" in header_text
    assert "FRaftSimSwimmingSkillProfile" in header_text
    assert "FRaftSimPassengerSwimmingSkillAssignment" in header_text
    assert "URaftSimSwimmingSkillLibrary" in header_text
    assert "bSelfRescueAllowed" in header_text
    assert "AssignSwimmingSkillFromNormalizedValue" in header_text


def test_swimmer_rescue_gameplay_manifest_matches_generator():
    expected = build_swimmer_rescue_gameplay_manifest(REPO_ROOT).manifest
    committed = json.loads(SWIMMER_RESCUE_GAMEPLAY_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE22_SWIMMER_RESCUE_SCHEMA
    assert committed["status"] == MILESTONE22_SWIMMER_RESCUE_STATUS


def test_swimmer_rescue_gameplay_manifest_covers_methods_and_outcomes():
    manifest = json.loads(SWIMMER_RESCUE_GAMEPLAY_PATH.read_text(encoding="utf-8"))
    methods = {method["method"]: method for method in manifest["rescue_methods"]}

    assert set(methods) == {"reach_grab", "paddle_grab", "throw_line"}
    assert methods["throw_line"]["requires_throw_line"] is True
    assert methods["reach_grab"]["max_distance_m"] < methods["throw_line"]["max_distance_m"]
    assert manifest["recovery_effects"]["successful_rescue_transitions"] == [
        "rescue_targeted",
        "rescued",
        "reseated_recovered",
    ]
    assert manifest["recovery_effects"]["failed_rescue_transitions"] == [
        "swimming",
        "failed_rescue",
    ]


def test_swimmer_rescue_gameplay_manifest_has_input_voice_and_telemetry_coverage():
    manifest = json.loads(SWIMMER_RESCUE_GAMEPLAY_PATH.read_text(encoding="utf-8"))
    coverage = manifest["input_and_voice_coverage"]
    fields = set(manifest["telemetry_fields"])

    assert "RescueTargetSelect" in coverage["input_action_ids"]
    assert "RescueReachGrab" in coverage["input_action_ids"]
    assert "RescueThrowLine" in coverage["input_action_ids"]
    assert "ReseatCrew" in coverage["input_action_ids"]
    assert "crew_rescue" in coverage["voice_intents"]
    assert "crew_recovery" in coverage["voice_intents"]
    assert {
        "swimmer_world_position_m",
        "swimmer_drift_velocity_mps",
        "visibility_score",
        "callout_priority",
        "rescue_target_rank",
        "rescue_method",
        "pull_in_progress",
        "reseat_recovery_seconds",
        "fatigue_delta",
        "trust_delta",
        "failed_rescue_reason",
    }.issubset(fields)


def test_unreal_swimmer_rescue_contract_exposes_drift_and_rescue_attempts():
    header_text = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimCrew/Public/RaftSimCrewStateContracts.h"
    ).read_text(encoding="utf-8")

    assert "ERaftSimRescueMethod" in header_text
    assert "FRaftSimSwimmerRescueFrame" in header_text
    assert "FRaftSimRescueAttempt" in header_text
    assert "URaftSimSwimmerRescueLibrary" in header_text
    assert "IntegrateSwimmerDrift" in header_text
    assert "EvaluateRescueAttempt" in header_text
    for field in (
        "SwimmerWorldPositionMeters",
        "SwimmerDriftVelocityMetersPerSecond",
        "VisibilityScore",
        "CalloutPriority",
        "PullInProgress",
        "FatigueDelta",
        "TrustDelta",
    ):
        assert field in header_text
