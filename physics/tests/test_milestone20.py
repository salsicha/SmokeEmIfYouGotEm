import json
from pathlib import Path

from raftsim.milestone20 import (
    MILESTONE16_READINESS_ARTIFACTS,
    MILESTONE16_SOURCE_REPORTS,
    MILESTONE20_REPORT_SET_LOCK_DECISION,
    MILESTONE20_REPORT_SET_LOCK_SCHEMA,
    MILESTONE20_SUPPORTING_ARTIFACTS,
    MILESTONE20_TRACEABLE_DATA_ASSETS_SCHEMA,
    MILESTONE20_UNREAL_REGRESSION_IMPORT_SCHEMA,
    build_traceable_unreal_data_assets,
    build_unreal_regression_fixture_import,
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
LIVE_WATER_BRIDGE_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/live_water_bridge.json"
WATER_RUNTIME_CANDIDATE_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Physics/water_runtime_candidate.json"
)
FIXED_STEP_BRIDGE_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/fixed_step_bridge.json"
RENDER_INTERPOLATION_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Physics/fixed_step_render_interpolation.json"
)
WATER_REGRESSION_IMPORT_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json"
)
WATER_REGRESSION_IMPORT_TEST_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimWaterRegressionImportTest.cpp"
)
TRACEABLE_DATA_ASSETS_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/River/traceable_river_data_assets.json"
)
TRACEABLE_DATA_ASSET_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimGeo/Public/RaftSimTraceableRiverDataAsset.h"
)
LIVE_WATER_DEBUG_VIEWS_PATH = REPO_ROOT / "unreal/Content/RaftSim/Debug/live_water_debug_views.json"
WATER_DEBUG_VIEWS_HEADER_PATH = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimDebug/Public/RaftSimWaterDebugViews.h"
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
    assert foundation["project"]["traceable_river_data_assets"] == (
        "unreal/Content/RaftSim/River/traceable_river_data_assets.json"
    )
    assert foundation["project"]["live_water_debug_views"] == (
        "unreal/Content/RaftSim/Debug/live_water_debug_views.json"
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


def test_live_water_bridge_manifest_uses_locked_report_and_water_module():
    report_lock = json.loads(REPORT_SET_LOCK_PATH.read_text(encoding="utf-8"))
    live_bridge = json.loads(LIVE_WATER_BRIDGE_PATH.read_text(encoding="utf-8"))
    candidate = json.loads(WATER_RUNTIME_CANDIDATE_PATH.read_text(encoding="utf-8"))
    fixed_step = json.loads(FIXED_STEP_BRIDGE_PATH.read_text(encoding="utf-8"))
    interpolation = json.loads(RENDER_INTERPOLATION_PATH.read_text(encoding="utf-8"))

    assert live_bridge["schema"] == "raftsim.unreal.live_water_bridge.v1"
    assert live_bridge["accepted_report_set_lock"]["manifest"] == (
        "physics/reports/milestone20/report_set_lock.json"
    )
    assert live_bridge["accepted_report_set_lock"]["lock_hash"] == report_lock["lock"]["lock_hash"]
    assert live_bridge["accepted_report_set_lock"]["required"] is True
    assert live_bridge["regression_fixture_import"] == (
        "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json"
    )
    assert live_bridge["water_runtime"]["module"] == "RaftSimWater"
    assert live_bridge["water_runtime"]["authority"] == "custom_cxx_shallow_water_solver"
    assert live_bridge["fixed_step_scheduling"]["subsystem"] == "URaftSimPhysicsBridgeSubsystem"
    assert live_bridge["deterministic_capture"]["enabled_by_default"] is True
    assert live_bridge["render_interpolation"]["enabled_by_default"] is True

    assert candidate["unreal_adapter"]["module"] == "RaftSimWater"
    assert candidate["accepted_report_set_lock"]["lock_hash"] == report_lock["lock"]["lock_hash"]
    assert fixed_step["authority"]["water_module"] == "RaftSimWater"
    assert fixed_step["accepted_report_set_lock"] == "physics/reports/milestone20/report_set_lock.json"
    assert fixed_step["deterministic_capture"]["enabled"] is True
    assert interpolation["water_runtime_adapter"] == "URaftSimWaterRuntimeAdapter"


def test_live_water_adapter_lives_in_water_module_with_manifest_capture_contract():
    water_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimWater/Public/RaftSimWaterRuntimeAdapter.h"
    )
    water_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimWater/Private/RaftSimWaterRuntimeAdapter.cpp"
    )
    old_physics_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimWaterRuntimeAdapter.h"
    )
    physics_build = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/RaftSimPhysics.Build.cs"
    ).read_text(encoding="utf-8")
    water_build = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimWater/RaftSimWater.Build.cs"
    ).read_text(encoding="utf-8")
    header_text = water_header.read_text(encoding="utf-8")
    cpp_text = water_cpp.read_text(encoding="utf-8")

    assert water_header.exists()
    assert water_cpp.exists()
    assert not old_physics_header.exists()
    assert "RaftSimWater" in physics_build
    assert "RAFTSIM_WATER_RUNTIME_NAME" in water_build
    assert "physics/cpp/include" in water_build
    assert "FRaftSimWaterReportManifestState" in header_text
    assert "FRaftSimWaterDeterministicCaptureState" in header_text
    assert "AcceptedReportSetManifestPath" in header_text
    assert "ExpectedReportSetLockHash" in header_text
    assert "bEnableRenderInterpolation" in header_text
    assert "LoadAcceptedReportManifest" in cpp_text
    assert "AppendDeterministicCaptureFrame" in cpp_text
    assert "ResolveRepoRelativePath" in cpp_text


def test_unreal_regression_fixture_import_matches_generator():
    expected = build_unreal_regression_fixture_import(REPO_ROOT).manifest
    committed = json.loads(WATER_REGRESSION_IMPORT_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE20_UNREAL_REGRESSION_IMPORT_SCHEMA
    assert committed["status"] == "ready_for_unreal_automation_execution"


def test_unreal_regression_fixture_import_covers_milestone16_17_18():
    manifest = json.loads(WATER_REGRESSION_IMPORT_PATH.read_text(encoding="utf-8"))
    source = manifest["source_milestones"]
    report_lock = json.loads(REPORT_SET_LOCK_PATH.read_text(encoding="utf-8"))

    assert manifest["accepted_report_set_lock"]["lock_hash"] == report_lock["lock"]["lock_hash"]
    assert manifest["automation_module"] == "RaftSimAutomation"
    assert manifest["live_water_bridge_manifest"] == (
        "unreal/Content/RaftSim/Physics/live_water_bridge.json"
    )
    assert manifest["comparison_modes"] == [
        "replayed_water_field_vs_accepted_cpp_output",
        "live_water_field_vs_accepted_cpp_output",
    ]
    assert manifest["total_fixture_count"] == 109
    assert source["milestone16"]["fixture_count"] == 98
    assert source["milestone16"]["categories"] == {
        "geoclaw_cpp": 40,
        "geometry_validation": 8,
        "raft_coupling": 50,
    }
    assert source["milestone17"]["fixture_count"] == 7
    assert source["milestone17"]["passed_count"] == 7
    assert source["milestone18"]["fixture_count"] == 4
    assert {
        fixture["fixture_id"] for fixture in source["milestone18"]["fixtures"]
    } == {
        "milestone18/remaining_geometry_closure",
        "milestone18/geoclaw_cpp_failure_triage_matrix",
        "milestone18/pin_release_fixture",
        "milestone18/raft_coupling_agreement_closure",
    }
    assert manifest["pass_policy"]["replayed_fields_must_match_accepted_cpp_outputs"] is True
    assert manifest["pass_policy"]["live_fields_must_match_accepted_cpp_outputs"] is True


def test_unreal_automation_test_loads_regression_import_manifest():
    test_text = WATER_REGRESSION_IMPORT_TEST_PATH.read_text(encoding="utf-8")

    assert "RaftSim/Automation/water_regression_fixture_import.json" in test_text
    assert "raftsim.unreal.regression_fixture_import.v1" in test_text
    assert "total_fixture_count" in test_text
    assert "Milestone 16 fixture count" in test_text


def test_traceable_unreal_data_assets_match_generator():
    expected = build_traceable_unreal_data_assets(REPO_ROOT).manifest
    committed = json.loads(TRACEABLE_DATA_ASSETS_PATH.read_text(encoding="utf-8"))

    assert committed == expected
    assert committed["schema"] == MILESTONE20_TRACEABLE_DATA_ASSETS_SCHEMA
    assert committed["status"] == "ready_for_unreal_data_asset_loading"


def test_traceable_unreal_data_assets_cover_required_source_kinds():
    manifest = json.loads(TRACEABLE_DATA_ASSETS_PATH.read_text(encoding="utf-8"))
    report_lock = json.loads(REPORT_SET_LOCK_PATH.read_text(encoding="utf-8"))
    assets = {asset["asset_id"]: asset for asset in manifest["data_assets"]}
    kinds = {asset["kind"] for asset in assets.values()}

    assert manifest["accepted_report_set_lock"]["lock_hash"] == report_lock["lock"]["lock_hash"]
    assert manifest["asset_class"] == "URaftSimTraceableRiverDataAsset"
    assert manifest["asset_count"] == 9
    assert {
        "solver_neutral_scenario_collection",
        "reach_local_grid_with_stitched_validation",
        "geospatial_source_manifest",
        "unreal_corridor_package",
    }.issubset(kinds)
    assert assets["solver_neutral_milestone16_registry"]["fixture_count"] == 98
    assert assets["south_fork_american_source_manifest"]["kind"] == "geospatial_source_manifest"
    assert assets["south_fork_american_unreal_corridor_package"]["kind"] == (
        "unreal_corridor_package"
    )

    cascading_assets = [
        asset
        for asset in assets.values()
        if asset["kind"] == "reach_local_grid_with_stitched_validation"
    ]
    assert len(cascading_assets) == 6
    for asset in cascading_assets:
        assert asset["reach_local_grid_count"] == 7
        assert asset["ghost_zone_policy"]["max_upstream_ghost_cells"] == 2
        assert asset["ghost_zone_policy"]["max_downstream_ghost_cells"] == 2
        assert asset["stitched_validation"]["required"] is True
        assert asset["stitched_validation"]["schema_version"] == (
            "raftsim.stitched_whole_window_validation.v0"
        )
        for path in asset["source_paths"]:
            assert (REPO_ROOT / path).exists()
        for key in ("manifest", "fields", "conservation_summary", "probes"):
            assert (REPO_ROOT / asset["stitched_validation"][key]).exists()


def test_traceable_river_data_asset_contract_exists():
    header_text = TRACEABLE_DATA_ASSET_HEADER_PATH.read_text(encoding="utf-8")

    assert "URaftSimTraceableRiverDataAsset" in header_text
    assert "ERaftSimTraceableRiverDataKind" in header_text
    assert "FRaftSimTraceableSourcePath" in header_text
    assert "bRequiresStitchedWholeWindowValidation" in header_text
    assert "AcceptedReportSetLockHash" in header_text


def test_live_water_debug_views_cover_required_overlays():
    manifest = json.loads(LIVE_WATER_DEBUG_VIEWS_PATH.read_text(encoding="utf-8"))
    view_ids = {view["view_id"] for view in manifest["views"]}

    assert manifest["schema"] == "raftsim.unreal.live_water_debug_views.v1"
    assert manifest["module"] == "RaftSimDebug"
    assert manifest["view_set_class"] == "URaftSimWaterDebugViewSet"
    assert manifest["view_model_class"] == "URaftSimWaterDebugViewModel"
    assert manifest["capture_policy"]["include_in_live_water_smoke_suite"] is True
    assert view_ids == {
        "depth",
        "velocity",
        "froude",
        "wet_dry_mask",
        "feature_tags",
        "conservation_deltas",
        "raft_trajectory",
        "contact_probes",
        "runtime_budgets",
    }
    assert manifest["source_manifests"]["traceable_river_data_assets"] == (
        "unreal/Content/RaftSim/River/traceable_river_data_assets.json"
    )
    assert manifest["source_manifests"]["runtime_budgets"] == "physics/config/runtime_budgets.json"
    for view in manifest["views"]:
        assert view["telemetry_fields"]
        assert view["render_mode"]


def test_live_water_debug_view_contract_matches_manifest():
    header_text = WATER_DEBUG_VIEWS_HEADER_PATH.read_text(encoding="utf-8")
    build_text = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimDebug/RaftSimDebug.Build.cs"
    ).read_text(encoding="utf-8")

    for enum_value in (
        "Depth",
        "Velocity",
        "Froude",
        "WetDryMask",
        "FeatureTags",
        "ConservationDeltas",
        "RaftTrajectory",
        "ContactProbes",
        "RuntimeBudgets",
    ):
        assert enum_value in header_text
    assert "URaftSimWaterDebugViewSet" in header_text
    assert "URaftSimWaterDebugViewModel" in header_text
    assert "SetViewEnabled" in header_text
    assert "IsViewEnabled" in header_text
    assert "RaftSimWater" in build_text
    assert "RaftSimGeo" in build_text
