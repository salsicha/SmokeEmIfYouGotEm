import json
from pathlib import Path

from raftsim.milestone22 import (
    MILESTONE22_CONTACT_TELEMETRY_SCHEMA,
    MILESTONE22_CONTACT_TELEMETRY_STATUS,
    MILESTONE22_RAFT_CONTACT_AUTHORITY_SCHEMA,
    MILESTONE22_RAFT_CONTACT_AUTHORITY_STATUS,
    build_raft_contact_authority_integration,
    build_raft_contact_response_telemetry,
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
