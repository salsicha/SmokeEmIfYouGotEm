import json
from pathlib import Path

from raftsim.milestone20 import (
    MILESTONE16_READINESS_ARTIFACTS,
    MILESTONE16_SOURCE_REPORTS,
    MILESTONE20_REPORT_SET_LOCK_DECISION,
    MILESTONE20_REPORT_SET_LOCK_SCHEMA,
    MILESTONE20_SUPPORTING_ARTIFACTS,
    build_report_set_lock,
    write_report_set_lock,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_SET_LOCK_PATH = REPO_ROOT / "physics/reports/milestone20/report_set_lock.json"
REPORT_SET_LOCK_MD_PATH = REPO_ROOT / "physics/reports/milestone20/report_set_lock.md"
UNREAL_PROJECT_PATH = REPO_ROOT / "unreal/SmokeEmIfYouGotEm.uproject"
RAFTSIM_PLUGIN_PATH = REPO_ROOT / "unreal/Plugins/RaftSim/RaftSim.uplugin"
PRODUCTION_FOUNDATION_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Production/production_foundation.json"
)
REQUIRED_PRODUCTION_MODULES = {
    "RaftSimCore",
    "RaftSimPhysics",
    "RaftSimWater",
    "RaftSimRiver",
    "RaftSimGeo",
    "RaftSimRaft",
    "RaftSimInput",
    "RaftSimUI",
    "RaftSimDebug",
    "RaftSimAI",
    "RaftSimCrew",
    "RaftSimAudio",
    "RaftSimAutomation",
    "RaftSimNetwork",
}
REQUIRED_PRODUCTION_DOMAINS = {
    "core_game_data",
    "authoritative_water",
    "river_geospatial_content",
    "raft_contact_physics",
    "crew",
    "input",
    "audio",
    "ui",
    "debug",
    "automation",
    "network",
}


def test_build_report_set_lock_covers_milestone16_acceptance_artifacts():
    lock = build_report_set_lock(REPO_ROOT).report
    artifact_paths = {artifact["path"] for artifact in lock["artifacts"]}

    assert lock["schema"] == MILESTONE20_REPORT_SET_LOCK_SCHEMA
    assert lock["decision"] == MILESTONE20_REPORT_SET_LOCK_DECISION
    assert lock["passed"] is True
    assert len(lock["lock"]["lock_hash"]) == 64
    assert lock["lock"]["artifact_count"] == (
        len(MILESTONE16_SOURCE_REPORTS)
        + len(MILESTONE16_READINESS_ARTIFACTS)
        + len(MILESTONE20_SUPPORTING_ARTIFACTS)
    )
    assert set(MILESTONE16_SOURCE_REPORTS).issubset(artifact_paths)
    assert set(MILESTONE16_READINESS_ARTIFACTS).issubset(artifact_paths)
    assert set(MILESTONE20_SUPPORTING_ARTIFACTS).issubset(artifact_paths)


def test_report_set_lock_confirms_all_target_profiles_and_replays():
    lock = build_report_set_lock(REPO_ROOT).report
    confirmation = lock["target_profile_confirmation"]
    profiles = {profile["profile"]: profile for profile in confirmation["profiles"]}

    assert confirmation["run_count"] == 80
    assert confirmation["all_profiles_passed"] is True
    assert set(profiles) == {"desktop", "handheld", "vr"}
    for profile in profiles.values():
        assert profile["record_count"] == 80
        assert profile["passed_count"] == 80
        assert profile["failed_count"] == 0
        assert profile["max_runtime_ms_per_tick"] <= profile["max_runtime_budget_ms"]
    assert confirmation["deterministic_replay"] == {
        "group_count": 40,
        "passed_count": 40,
        "failed_count": 0,
        "passed": True,
    }
    assert confirmation["physical_hardware_capture_status"] == "not_recorded_in_repo"


def test_write_report_set_lock_creates_json_and_markdown(tmp_path):
    output_json = tmp_path / "report_set_lock.json"
    output_md = tmp_path / "report_set_lock.md"

    lock = write_report_set_lock(
        repo_root=REPO_ROOT,
        output_json=output_json,
        output_md=output_md,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert lock.report["passed"] is True
    assert "Milestone 20 Report Set Lock" in output_md.read_text(encoding="utf-8")


def test_committed_report_set_lock_matches_generator():
    expected = build_report_set_lock(REPO_ROOT).report
    committed = json.loads(REPORT_SET_LOCK_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert REPORT_SET_LOCK_MD_PATH.exists()


def test_unreal_production_foundation_matches_locked_project_and_modules():
    foundation = json.loads(PRODUCTION_FOUNDATION_PATH.read_text(encoding="utf-8"))
    uproject = json.loads(UNREAL_PROJECT_PATH.read_text(encoding="utf-8"))
    uplugin = json.loads(RAFTSIM_PLUGIN_PATH.read_text(encoding="utf-8"))
    foundation_modules = {
        module
        for boundary in foundation["module_boundaries"]
        for module in boundary["modules"]
    }
    project_plugins = {plugin["Name"] for plugin in uproject["Plugins"]}

    assert foundation["schema"] == "raftsim.unreal.production_foundation.v1"
    assert foundation["engine"]["engine_association"] == uproject["EngineAssociation"] == "5.8"
    assert foundation["project"]["accepted_water_report_manifest"] == (
        "physics/reports/milestone20/report_set_lock.json"
    )
    assert REPORT_SET_LOCK_PATH.exists()
    assert set(foundation["enabled_project_plugins"]) == project_plugins
    assert foundation_modules == REQUIRED_PRODUCTION_MODULES
    assert {boundary["domain"] for boundary in foundation["module_boundaries"]} == (
        REQUIRED_PRODUCTION_DOMAINS
    )
    assert {module["Name"] for module in uplugin["Modules"]} == REQUIRED_PRODUCTION_MODULES


def test_raftsim_production_modules_have_source_skeletons():
    uplugin = json.loads(RAFTSIM_PLUGIN_PATH.read_text(encoding="utf-8"))
    modules = {module["Name"]: module for module in uplugin["Modules"]}

    assert modules["RaftSimAutomation"]["Type"] == "DeveloperTool"
    for module_name in REQUIRED_PRODUCTION_MODULES:
        module_root = REPO_ROOT / "unreal/Plugins/RaftSim/Source" / module_name
        assert (module_root / f"{module_name}.Build.cs").exists()
        assert (module_root / "Public" / f"{module_name}Module.h").exists()
        assert (module_root / "Private" / f"{module_name}Module.cpp").exists()
