import hashlib
import json
from pathlib import Path

from raftsim.editor_source_layout import (
    build_editor_source_inventory,
    read_raftsim_editor_source,
    render_editor_source_inventory_markdown,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "physics/reports/editor_source_inventory"
FROZEN_LEGACY_EXCEPTIONS = {
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorPveEvaluation.cpp",
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp",
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorPhotorealMaterials.cpp",
}
FROZEN_OVERSIZED_IMPLEMENTATION_MAX_LINES = {
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp": 3115,
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorPhotorealMaterials.cpp": 3145,
}


def test_editor_source_set_contains_commands_and_all_river_build_paths():
    inventory = build_editor_source_inventory(REPO_ROOT)
    source = read_raftsim_editor_source(REPO_ROOT)

    assert inventory["registered_console_command_count"] >= 30
    assert len(
        {row["command"] for row in inventory["registered_console_commands"]}
    ) == (inventory["registered_console_command_count"])
    assert inventory["all_river_build_targets_present"] is True
    assert "RaftSim.CreateLandscapeImportCandidateMaps" in source
    assert "RaftSim.CreatePhotorealEnvironmentPreviewMaps" in source
    assert "RaftSim.CaptureSouthForkFullReachEnvironment" in source
    assert "RaftSimCaptureSouthForkFullReachEnvironment" in source


def test_unattended_environment_automation_is_self_terminating():
    module_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/"
        "RaftSimEditorModule.cpp"
    ).read_text(encoding="utf-8")
    automation_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
        "RaftSimEditorEnvironmentAutomation.cpp"
    ).read_text(encoding="utf-8")

    assert "bPhotorealEnvironmentAutomationRequested" in module_source
    assert 'TEXT("unattended")' in module_source
    assert "bUnattendedAutomation && bPhotorealEnvironmentAutomationRequested" in (
        module_source
    )
    assert "FPlatformMisc::RequestExit(!bSucceeded" in automation_source
    assert "FPlatformMisc::RequestExit(true" in automation_source


def test_editor_source_split_keeps_module_and_focused_implementations_bounded():
    inventory = build_editor_source_inventory(REPO_ROOT)
    line_counts = {
        row["path"]: row["line_count"] for row in inventory["implementation_files"]
    }

    module_path = (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp"
    )
    assert line_counts[module_path] <= 1500
    assert not any("EnvironmentLegacy" in path for path in line_counts)
    assert {
        path: line_count
        for path, line_count in line_counts.items()
        if line_count > 3000 and path not in FROZEN_LEGACY_EXCEPTIONS
    } == {}
    assert {
        path: line_counts[path]
        for path, maximum in FROZEN_OVERSIZED_IMPLEMENTATION_MAX_LINES.items()
        if line_counts[path] > maximum
    } == {}

    internal_header = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    )
    assert len(internal_header.read_text(encoding="utf-8").splitlines()) <= 3000

    build_rules = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/RaftSimEditor.Build.cs"
    ).read_text(encoding="utf-8")
    assert "bUseUnity = false;" in build_rules


def test_editor_source_inventory_matches_generator():
    expected = build_editor_source_inventory(REPO_ROOT)

    assert (
        json.loads((REPORT_ROOT / "inventory.json").read_text(encoding="utf-8"))
        == expected
    )
    assert (REPORT_ROOT / "inventory.md").read_text(encoding="utf-8") == (
        render_editor_source_inventory_markdown(expected)
    )


def test_full_reach_generator_stabilizes_external_actor_identity_and_minimap():
    source_path = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    )
    source = source_path.read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")
    assert "SpawnParameters.OverrideActorGuid = SouthForkActorGuid" in source
    assert "SpawnParameters.Name = SouthForkActorObjectName" in source
    assert "ReplaceWorldPartitionMiniMapWithStableActor" in source
    assert 'TEXT("RaftSim_SouthFork_WorldPartitionMiniMap")' in source
    assert 'TEXT("deterministic_actor_object_names"), true' in manifest_source


def test_full_reach_mesh_reuse_preserves_persisted_macro_texture_mips():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    coverage_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainCoverage.cpp"
    ).read_text(encoding="utf-8")
    assert "LoadSouthForkTerrainMacroTextureForReuse" in full_reach_source
    assert "bReuseExistingDetailedTerrainMeshes" in full_reach_source
    assert "bReuseExistingFarFieldMeshes" in full_reach_source
    assert "Reused persisted South Fork macro-albedo texture" in coverage_source
    assert 'TEXT("RaftSimReuseSouthForkMaterials")' in full_reach_source
    assert "Reusing existing validated South Fork materials" in full_reach_source


def test_full_reach_single_layer_water_does_not_shadow_transmitted_riverbed():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    mesh_authoring_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkMeshAuthoring.cpp"
    ).read_text(encoding="utf-8")

    assert full_reach_source.count("ConfigureSouthForkSingleLayerWaterActor(") == 2
    assert "Component->Modify();" in mesh_authoring_source
    assert "Component->SetCastShadow(false);" in mesh_authoring_source
    assert "Actor->MarkPackageDirty();" in mesh_authoring_source
    assert "it is not an opaque" in mesh_authoring_source
    assert mesh_authoring_source.count("ConfigureSouthForkSingleLayerWaterActor(") == 1


def test_derived_bank_review_is_transient_non_authoritative_and_fail_closed():
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkDerivedBankReview.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    assert "RF_Transient" in source
    assert source.count("ECollisionEnabled::NoCollision") >= 3
    assert source.count("SetCanEverAffectNavigation(false)") >= 3
    assert "RaftSimFullReachTerrain" in source
    assert "bCutBank" in source
    assert "GravelBarRowCount" in source
    assert "/Engine/BasicShapes/Cylinder.Cylinder" in source
    assert "M_FirTree01_Bark.M_FirTree01_Bark" in source
    assert "FLinearColor(0.10f, 0.085f, 0.065f, 0.94f)" in source
    assert "FLinearColor(0.22f, 0.215f, 0.155f, 0.0f)" in source
    assert "StripSegmentCount < 1200" in source
    assert "RootSegmentCount < 120" in source
    assert "Actor->Destroy();" in source
    assert "photographic_v198_erosion_deposition_bank_modules" in capture_source


def test_scanned_bank_kit_is_hashed_isolated_transient_and_visually_fail_closed():
    importer = (
        REPO_ROOT / "unreal/Scripts/import_reviewed_south_fork_bank_kit.py"
    ).read_text(encoding="utf-8")
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkScannedBankKitReview.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    manifest_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
        "SouthForkBankKit_2K/polyhaven_south_fork_bank_kit_source_manifest.json"
    )
    report_path = (
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/"
        "polyhaven_south_fork_bank_kit_import_report.json"
    )
    review_path = (
        REPO_ROOT
        / "docs/environment-captures/south_fork_full_reach/"
        "m9_scanned_bank_kit_v199_review.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))

    assert "RAFTSIM_REVIEWED_SOUTH_FORK_BANK_KIT_SOURCE_ROOT" in importer
    assert "Hash mismatch" in importer
    assert "combine_meshes = True" in importer
    assert "flip_green_channel" in importer
    assert "StaticMeshEditorSubsystem" in importer
    assert manifest["source"]["license"] == "CC0 1.0 Universal"
    assert manifest["source"]["public_api_used"] is True
    assert manifest["source"]["publisher_md5_verified_file_count"] == 16
    assert manifest["source"]["source_bundle_committed"] is False
    assert len(manifest["expected_source_files"]) == 16
    assert report["status"] == "isolated_review_candidate_imported"
    assert report["production_promoted"] is False
    assert len(report["verified_source_files"]) == 16
    assert len(report["meshes"]) == 2
    assert len(report["textures"]) == 14
    assert len(report["materials"]) == 4
    for mesh in report["meshes"]:
        assert mesh["nanite_enabled"] is True
        assert mesh["lod0_build_scale"] == [100.0, 100.0, 100.0]
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert "RF_Transient" in source
    assert "ECollisionEnabled::NoCollision" in source
    assert "SetCanEverAffectNavigation(false)" in source
    assert "RaftSimFullReachTerrain" in source
    assert "SM_RockFace01.SM_RockFace01" in source
    assert "SM_TreeStump02.SM_TreeStump02" in source
    assert "RockFaceCount < 55" in source
    assert "StumpCount < 12" in source
    assert "RaftSimScannedBankKitReview" in capture_source
    assert "photographic_v199_scanned_bank_kit" in capture_source
    assert review["status"].endswith("visually_rejected_for_production")
    assert review["manual_review"]["production_promotion"] == "rejected"
    assert review["gate_effect"]["milestone_9"] == (
        "fail_closed_uncommitted_unpushed"
    )


def test_meat_grinder_hero_review_is_hash_gated_dem_grounded_and_non_authoritative():
    importer = (
        REPO_ROOT / "unreal/Scripts/import_reviewed_meat_grinder_hero_asset.py"
    ).read_text(encoding="utf-8")
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkMeatGrinderHeroReview.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
            "MeatGrinderHero_2K/polyhaven_meat_grinder_hero_source_manifest.json"
        ).read_text(encoding="utf-8")
    )
    report = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/photoreal_river_previews/"
            "polyhaven_meat_grinder_hero_import_report.json"
        ).read_text(encoding="utf-8")
    )
    review = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_meat_grinder_hero_v202_review.json"
        ).read_text(encoding="utf-8")
    )

    assert "RAFTSIM_MEAT_GRINDER_HERO_SOURCE_ROOT" in importer
    assert "Hash mismatch" in importer
    assert len(manifest["files"]) == 5
    assert all(row["official_md5"] and row["sha256"] for row in manifest["files"])
    assert manifest["license"]["name"] == "CC0 1.0 Universal"
    assert manifest["review_boundaries"]["station_range_m"] == [620.0, 1320.0]
    assert manifest["review_boundaries"]["production_promoted"] is False
    assert report["status"] == "isolated_review_candidate_imported"
    assert report["production_promoted"] is False
    assert report["meshes"][0]["nanite_enabled"] is True
    assert report["meshes"][0]["lod0_build_scale"] == [1.0, 1.0, 1.0]

    assert "FMeatGrinderTerrainSampler" in source
    assert 'ActorHasTag(TEXT("RaftSimFullReachTerrain"))' in source
    assert "TerrainSampler.FindSurfaceZCm" in source
    assert "TerrainSourceSampleCount < 1500" in source
    assert "ProceduralFallbackSampleCount != 0" in source
    assert "zero procedural bank geometry" in source
    assert "RF_Transient" in source
    assert "ECollisionEnabled::NoCollision" in source
    assert "SetCanEverAffectNavigation(false)" in source
    assert "CreateMeshSection" not in source
    assert "SavePackage" not in source
    assert "RaftSimMeatGrinderHeroReview" in capture_source
    assert "photographic_v202_meat_grinder_dem_aligned_rock_garden" in capture_source

    v202 = review["experiments"][2]
    assert v202["direct_source_height_samples"] == 1760
    assert v202["procedural_fallback_height_samples"] == 0
    assert v202["procedural_bank_triangles"] == 0
    assert review["manual_review"]["production_promotion"] == "rejected"
    assert review["authority"]["collision_changed"] is False
    assert review["authority"]["runtime_package_promoted"] is False
    assert review["gate_effect"]["milestone_9"] == (
        "fail_closed_uncommitted_unpushed"
    )


def test_river_small_rocks_review_is_hash_gated_isolated_and_visually_rejected():
    importer = (
        REPO_ROOT / "unreal/Scripts/import_reviewed_river_small_rocks_asset.py"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    displaced_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkDisplacedGravelReview.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
            "RiverSmallRocks_2K/polyhaven_river_small_rocks_source_manifest.json"
        ).read_text(encoding="utf-8")
    )
    report = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/photoreal_river_previews/"
            "polyhaven_river_small_rocks_import_report.json"
        ).read_text(encoding="utf-8")
    )
    review = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_river_small_rocks_v207_review.json"
        ).read_text(encoding="utf-8")
    )

    assert "RAFTSIM_RIVER_SMALL_ROCKS_SOURCE_ROOT" in importer
    assert "Hash mismatch" in importer
    assert len(manifest["files"]) == 4
    assert all(row["official_md5"] and row["sha256"] for row in manifest["files"])
    assert manifest["license"]["name"] == "CC0 1.0 Universal"
    assert manifest["review_boundaries"]["physical_repeat_m"] == 2.9
    assert manifest["review_boundaries"]["displacement_geometry_review_only"] is True
    assert manifest["review_boundaries"]["production_promoted"] is False
    assert report["status"] == "isolated_review_candidate_imported"
    assert report["production_promoted"] is False
    assert len(report["textures"]) == 4
    assert all(row["width"] == row["height"] == 2048 for row in report["textures"])
    assert report["textures"][1]["flip_green_channel"] is True
    assert "TC_GRAYSCALE" in report["textures"][3]["compression_settings"]

    assert "RaftSimRiverSmallRocksReview" in capture_source
    assert "Texture->Source.GetSizeX()" in capture_source
    assert "Texture->Source.GetSizeY()" in capture_source
    assert 'TEXT("SourceMacroInfluence"), 0.30f' in capture_source
    assert 'TEXT("UseCorridorEdgeBlend"), 0.0f' in capture_source
    assert "photographic_v205_meat_grinder_river_small_rocks_exposed" in capture_source
    assert "RaftSimDisplacedGravelBarReview" in capture_source
    assert "photographic_v207_meat_grinder_displaced_gravel_bar_corrected" in (
        capture_source
    )
    assert "SavePackage" not in capture_source

    assert "T_RiverSmallRocks_Displacement_2K" in displaced_source
    assert "Displacement->Source.GetMipData" in displaced_source
    assert "FindDisplacedGravelTerrainSurfaceZCm" in displaced_source
    assert "AcceptedRows < 800" in displaced_source
    assert "TerrainTraceHits < 10000" in displaced_source
    assert "ECollisionEnabled::NoCollision" in displaced_source
    assert "SetCanEverAffectNavigation(false)" in displaced_source
    assert "bCreateCollision=*/false" in displaced_source
    assert "SavePackage" not in displaced_source

    assert len(review["experiments"]) == 4
    assert review["experiments"][0]["manual_result"] == (
        "rejected_as_visually_ineffective"
    )
    assert review["experiments"][1]["manual_result"] == "rejected"
    assert review["experiments"][2]["coverage"]["dem_terrain_trace_hits"] == 21736
    assert review["experiments"][3]["manual_result"] == (
        "rejected_and_geometry_tuning_stopped"
    )
    assert review["manual_review"]["production_promotion"] == "rejected"
    assert review["authority"]["collision_changed"] is False
    assert review["authority"]["runtime_package_promoted"] is False
    assert review["gate_effect"]["milestone_9"] == (
        "fail_closed_uncommitted_unpushed"
    )


def test_live_oak_branch_atlas_v2_review_is_isolated_and_fail_closed():
    canopy_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
            "interior_live_oak_branch_atlas_v2_manifest.json"
        ).read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_branch_atlas_v2_v209_review.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["schema"] == (
        "raftsim.unreal.south_fork_live_oak_branch_atlas.v2"
    )
    assert manifest["production_promoted"] is False
    assert manifest["status"] == "m9_review_only_visual_promotion_rejected"
    assert manifest["integration"]["active_candidate"] is False
    assert manifest["source"]["referenced_images"] == []
    assert manifest["atlas"]["occupied_tiles"] == list(range(12))
    assert manifest["atlas"]["reserved_transparent_tiles"] == list(range(12, 16))
    assert manifest["authority"] == {
        "affects_ecology_classification": False,
        "affects_instance_placement": False,
        "affects_collision": False,
        "affects_hydraulics": False,
    }
    for source_name in (
        "T_InteriorLiveOak_BranchAtlasV2_AlbedoOpacity.png",
        "T_InteriorLiveOak_BranchAtlasV2_Normal.png",
        "T_InteriorLiveOak_BranchAtlasV2_AORoughnessSubsurface.png",
    ):
        assert source_name in canopy_source
        assert (
            REPO_ROOT
            / "unreal/SourceArt/RaftSim/Environment/GeneratedCanopy"
            / source_name
        ).is_file()
    assert "RaftSimOnlyLiveOakBranchAtlasV2Review" in canopy_source
    assert "ExpandedReviewBranchCardCount = 48" in canopy_source
    assert "SouthForkInteriorLiveOakAtlasV2Review_ConnectedCrownV2" in (
        capture_source
    )
    assert "RaftSimLiveOakBranchAtlasV2Review" in capture_source
    assert "RaftSimLiveOakBranchAtlasV2ExpandedReview" in capture_source
    assert "photographic_v208_live_oak_branch_atlas_v2" in capture_source
    assert "photographic_v209_live_oak_branch_atlas_v2_expanded" in capture_source
    assert 'Name != TEXT("OakBroadleafProxy")' in capture_source
    assert 'Name != TEXT("FarBroadleafCard")' in capture_source
    assert "no map, collision, ecology" in capture_source
    assert ledger["status"] == (
        "project_owned_source_retained_but_v208_and_v209_visual_promotion_rejected"
    )
    assert [row["manual_result"] for row in ledger["experiments"]] == [
        "rejected_as_visually_ineffective",
        "rejected_and_canopy_card_scalar_tuning_stopped",
    ]
    assert ledger["source_bundle"]["referenced_images"] == []
    assert ledger["authority"]["map_saved"] is False
    assert ledger["authority"]["runtime_package_promoted"] is False
    assert ledger["gate_effect"]["milestone_9"] == (
        "fail_closed_uncommitted_unpushed"
    )
    for version in ("v208", "v209"):
        for capture_name, expected_sha256 in ledger["capture_sha256"][
            version
        ].items():
            capture_directory = next(
                row["capture_directory"]
                for row in ledger["experiments"]
                if f"v{row['version']}" == version
            )
            capture_path = REPO_ROOT / capture_directory / f"{capture_name}.png"
            assert capture_path.is_file()
            assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
                expected_sha256
            )


def test_live_oak_true_woody_v1_review_is_isolated_and_fail_closed():
    canopy_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    texture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorMaterialTextures.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
            "interior_live_oak_woody_canopy_v1_manifest.json"
        ).read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_true_woody_v210_review.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["schema"] == (
        "raftsim.unreal.south_fork_live_oak_woody_canopy.v1"
    )
    assert manifest["status"] == (
        "m9_review_only_woody_canopy_visual_promotion_rejected"
    )
    assert manifest["production_promoted"] is False
    assert manifest["integration"]["active_candidate"] is False
    assert manifest["integration"]["photoreal_accepted"] is False
    assert manifest["source"]["referenced_images"] == []
    assert manifest["geometry_contract"]["true_woody_topology"] is True
    assert manifest["geometry_contract"]["billboard_core"] is False
    assert all(value is False for value in manifest["authority"].values())
    assert "RaftSimOnlyLiveOakWoodyCanopyV1Review" in canopy_source
    assert "RaftSimLiveOakWoodyCanopyV1Review" in capture_source
    assert "photographic_v210_live_oak_true_woody_v1" in capture_source
    assert "woody_segments=%d" in canopy_source
    assert "terminal_branches=%d" in canopy_source
    assert "leaf_cards=%d" in canopy_source
    assert "billboard_core=0" in canopy_source
    assert "BeginCachePlatformData" in texture_source
    assert "FinishCachePlatformData" in texture_source

    asset_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Canopy"
    )
    asset_paths = {
        "bark_albedo_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_BarkAlbedo.uasset",
        "bark_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_BarkNormal.uasset",
        "bark_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_BarkAORoughnessHeight.uasset",
        "leaf_albedo_opacity_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_AlbedoOpacity.uasset",
        "leaf_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_Normal.uasset",
        "leaf_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_AORoughnessSubsurface.uasset",
        "bark_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_Bark.uasset",
        "leaf_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakWoodyV1Review_BranchAtlasV1.uasset",
        "mesh": asset_root
        / "Meshes/SM_RaftSim_SouthForkInteriorLiveOakWoodyV1_OpenGrownMature.uasset",
    }
    for key, path in asset_paths.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            ledger["authoring"]["asset_hashes"][key]
        )

    capture_root = REPO_ROOT / ledger["capture"]["directory"]
    for filename, expected_sha256 in ledger["capture"]["hashes"].items():
        capture_path = capture_root / filename
        assert capture_path.is_file()
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert ledger["status"] == (
        "visual_promotion_rejected_technical_scaffold_retained"
    )
    assert ledger["authoring"]["mesh"]["woody_segments"] == 72
    assert ledger["authoring"]["mesh"]["terminal_branches"] == 45
    assert ledger["authoring"]["mesh"]["leaf_cards"] == 90
    assert ledger["authoring"]["mesh"]["billboard_core"] == 0
    assert ledger["capture"]["saved_map_changed"] is False
    assert ledger["milestone_gate"]["m9_passed"] is False
    assert ledger["milestone_gate"]["commit_allowed"] is False
    assert ledger["milestone_gate"]["push_allowed"] is False


def test_live_oak_dense_woody_v2_review_is_isolated_and_fail_closed():
    canopy_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
            "interior_live_oak_leaf_clusters_v3_manifest.json"
        ).read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_dense_woody_v211_review.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["schema"] == (
        "raftsim.unreal.south_fork_live_oak_leaf_clusters.v3"
    )
    assert manifest["status"] == (
        "m9_review_only_dense_leaf_clusters_v3_visual_promotion_rejected"
    )
    assert manifest["production_promoted"] is False
    assert manifest["integration"]["active_candidate"] is False
    assert manifest["source"]["referenced_images"] == []
    assert manifest["atlas"]["occupied_tiles"] == list(range(4))
    assert manifest["atlas"]["reserved_transparent_tiles"] == list(range(4, 16))
    assert manifest["atlas"]["occupied_band_opaque_pixel_count"] == 399118
    assert manifest["atlas"]["reserved_band_opaque_pixel_count"] == 0
    assert all(value is False for value in manifest["authority"].values())
    assert "RaftSimOnlyLiveOakDenseWoodyV2Review" in canopy_source
    assert "T_InteriorLiveOak_LeafClustersV3_AlbedoOpacity.png" in canopy_source
    assert "T_InteriorLiveOak_LeafClustersV3_Normal.png" in canopy_source
    assert "T_InteriorLiveOak_LeafClustersV3_AORoughnessSubsurface.png" in (
        canopy_source
    )
    assert "LeafAtlasTileCount=*/4" in canopy_source
    assert "LeafCardScale=*/1.12f" in canopy_source
    assert "RaftSimLiveOakDenseWoodyV2Review" in capture_source
    assert "photographic_v211_live_oak_dense_woody_v2" in capture_source

    asset_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Canopy"
    )
    asset_paths = {
        "bark_albedo_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_BarkAlbedo.uasset",
        "bark_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_BarkNormal.uasset",
        "bark_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_BarkAORoughnessHeight.uasset",
        "leaf_albedo_opacity_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_AlbedoOpacity.uasset",
        "leaf_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_Normal.uasset",
        "leaf_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_AORoughnessSubsurface.uasset",
        "bark_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_Bark.uasset",
        "leaf_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2Review_BranchAtlasV1.uasset",
        "mesh": asset_root
        / "Meshes/SM_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2_OpenGrownMature.uasset",
    }
    for key, path in asset_paths.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            ledger["authoring"]["asset_hashes"][key]
        )

    capture_root = REPO_ROOT / ledger["capture"]["directory"]
    for filename, expected_sha256 in ledger["capture"]["hashes"].items():
        capture_path = capture_root / filename
        assert capture_path.is_file()
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert ledger["status"] == (
        "visual_promotion_rejected_stronger_technical_source_retained"
    )
    assert ledger["capture"]["saved_map_changed"] is False
    assert ledger["milestone_gate"]["m9_passed"] is False
    assert ledger["milestone_gate"]["commit_allowed"] is False
    assert ledger["milestone_gate"]["push_allowed"] is False


def test_live_oak_crown_family_v3_review_is_isolated_and_fail_closed():
    canopy_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    texture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorMaterialTextures.cpp"
    ).read_text(encoding="utf-8")
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_crown_family_v212_review.json"
        ).read_text(encoding="utf-8")
    )

    assert ledger["schema"] == (
        "raftsim.review.south_fork_live_oak_crown_family.v212"
    )
    assert ledger["status"] == (
        "visual_promotion_rejected_variant_lod_infrastructure_retained"
    )
    assert ledger["production_promoted"] is False
    assert ledger["photoreal_accepted"] is False
    assert "RaftSimOnlyLiveOakCrownFamilyV3Review" in canopy_source
    assert "RaftSimLiveOakCrownFamilyV3Review" in capture_source
    assert "photographic_v212_live_oak_crown_family_v3" in capture_source
    assert "ConfigureSouthForkLiveOakReviewLods" in canopy_source
    assert "EStaticMeshReductionTerimationCriterion::Triangles" in canopy_source
    assert "screen_sizes=1.00/0.34/0.12" in canopy_source
    assert "bCalibratedReviewLighting" in canopy_source
    assert "AmbientOcclusionFloor->R = 0.62f" in canopy_source
    assert "NormalDetail->R = 0.64f" in canopy_source
    assert "Spec.MapKey == TEXT(\"AlbedoOpacity\")" in texture_source
    assert "StableComponentId" in capture_source
    assert "GetTypeHash(StableComponentId)" in capture_source
    assert "Crown-family V3 stable distribution" in capture_source
    assert "no map, collision, ecology" in capture_source

    assert set(ledger["authoring"]["forms"]) == {
        "spreading_mature",
        "compact_river_edge",
        "asymmetric_competition",
    }
    for form in ledger["authoring"]["forms"].values():
        lod_triangles = form["lod_triangles"]
        assert len(lod_triangles) == 3
        assert lod_triangles[0] > lod_triangles[1] > lod_triangles[2] > 0
    assert ledger["authoring"]["lod_screen_sizes"] == [1.0, 0.34, 0.12]
    material = ledger["authoring"]["shared_material_contract"]
    assert material["shading_model"] == "TwoSidedFoliage"
    assert material["emissive_compensation"] is False
    assert material["dithered_lod_transition"] is True

    distribution = ledger["capture"]["component_level_distribution"]
    assert sum(
        distribution[key]["components"]
        for key in (
            "spreading_mature",
            "compact_river_edge",
            "asymmetric_competition",
        )
    ) == ledger["capture"]["transient_component_swaps"] == 21
    assert sum(
        distribution[key]["instances"]
        for key in (
            "spreading_mature",
            "compact_river_edge",
            "asymmetric_competition",
        )
    ) == ledger["capture"]["transient_instance_swaps"] == 24830
    assert distribution["per_instance_selection_supported"] is False

    asset_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Canopy"
    )
    asset_paths = {
        "bark_albedo_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_BarkAlbedo.uasset",
        "bark_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_BarkNormal.uasset",
        "bark_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_BarkAORoughnessHeight.uasset",
        "leaf_albedo_opacity_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_AlbedoOpacity.uasset",
        "leaf_normal_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_Normal.uasset",
        "leaf_packed_texture": asset_root
        / "Textures/T_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_AORoughnessSubsurface.uasset",
        "bark_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_Bark.uasset",
        "leaf_material": asset_root
        / "Materials/M_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3Review_BranchAtlasV1.uasset",
        "spreading_mature_mesh": asset_root
        / "Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_SpreadingMature.uasset",
        "compact_river_edge_mesh": asset_root
        / "Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_CompactRiverEdge.uasset",
        "asymmetric_competition_mesh": asset_root
        / "Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_AsymmetricCompetition.uasset",
    }
    for key, path in asset_paths.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            ledger["authoring"]["asset_hashes"][key]
        )

    capture_root = REPO_ROOT / ledger["capture"]["directory"]
    for filename, expected_sha256 in ledger["capture"]["hashes"].items():
        capture_path = capture_root / filename
        assert capture_path.is_file()
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert ledger["capture"]["saved_map_changed"] is False
    assert all(value is False for value in ledger["authority"].values())
    assert ledger["milestone_gate"]["m9_passed"] is False
    assert ledger["milestone_gate"]["commit_allowed"] is False
    assert ledger["milestone_gate"]["push_allowed"] is False


def test_live_oak_cc0_island_tree_morphology_review_is_isolated_and_fail_closed():
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    asset_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
        "FutaleufuIslandTreeSet_1K"
    )
    source_manifest_path = (
        asset_root / "polyhaven_futaleufu_island_tree_set_source_manifest.json"
    )
    import_report_path = (
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/"
        "polyhaven_futaleufu_island_tree_set_import_report.json"
    )
    prior_review_path = (
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "polyhaven_futaleufu_island_tree_set_visual_comparison_review.json"
    )
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_cc0_island_tree_morphology_v213_review.json"
        ).read_text(encoding="utf-8")
    )
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    import_report = json.loads(import_report_path.read_text(encoding="utf-8"))
    prior_review = json.loads(prior_review_path.read_text(encoding="utf-8"))

    assert ledger["schema"] == (
        "raftsim.review.south_fork_live_oak_cc0_morphology.v213"
    )
    assert ledger["status"] == (
        "technical_trial_validated_visual_promotion_rejected_"
        "material_and_distance_instability"
    )
    assert ledger["production_promoted"] is False
    assert ledger["photoreal_accepted"] is False
    assert ledger["species_identity_approved"] is False
    assert source_manifest["status"] == (
        "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert {source["license"] for source in source_manifest["sources"]} == {
        "CC0 1.0 Universal"
    }
    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 33
    assert len(import_report["meshes"]) == 3
    assert all(mesh["nanite_enabled"] for mesh in import_report["meshes"])
    assert prior_review["production_promoted"] is False
    assert prior_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )

    assert "RaftSimLiveOakIslandTreeMorphologyReview" in capture_source
    assert (
        "photographic_v213_live_oak_cc0_island_tree_morphology"
        in capture_source
    )
    assert "FutaleufuIslandTreeSet_1K/SM_IslandTree01" in capture_source
    assert "FutaleufuIslandTreeSet_1K/SM_IslandTree02" in capture_source
    assert "FutaleufuIslandTreeSet_1K/SM_IslandTree03" in capture_source
    assert "TargetCrownWidthCm = 1250.0f" in capture_source
    assert "TargetTreeHeightCm = 920.0f" in capture_source
    assert "ReviewMesh->GetStaticMaterials().Num() != 3" in capture_source
    assert "State.OriginalWorldTransforms.Add" in capture_source
    assert "BatchUpdateInstancesTransforms" in capture_source
    assert "SwappedComponentCount == 21" in capture_source
    assert "SwappedInstanceCount == 24830" in capture_source
    assert "donor materials were preserved" in capture_source
    assert "species/ecology authority remains false" in capture_source

    assert hashlib.sha256(source_manifest_path.read_bytes()).hexdigest() == (
        ledger["inputs"]["source_bundle"]["source_manifest_sha256"]
    )
    assert hashlib.sha256(import_report_path.read_bytes()).hexdigest() == (
        ledger["inputs"]["source_bundle"]["import_report_sha256"]
    )
    assert hashlib.sha256(prior_review_path.read_bytes()).hexdigest() == (
        ledger["inputs"]["source_bundle"]["prior_futaleufu_visual_review_sha256"]
    )

    forms = ledger["donor_contract"]["forms"]
    for form_name, form in forms.items():
        tree_number = form_name[-2:]
        mesh_path = asset_root / f"SM_IslandTree{tree_number}.uasset"
        assert mesh_path.is_file()
        assert hashlib.sha256(mesh_path.read_bytes()).hexdigest() == (
            form["mesh_sha256"]
        )
        for material_role, expected_sha256 in form["material_hashes"].items():
            role_token = {
                "trunk": "Trunk",
                "leaves": "Leaves",
                "branches": "Branches",
            }[material_role]
            material_path = (
                asset_root / f"M_IslandTree{tree_number}_{role_token}.uasset"
            )
            assert material_path.is_file()
            assert hashlib.sha256(material_path.read_bytes()).hexdigest() == (
                expected_sha256
            )

    distribution = ledger["integration"]["component_level_distribution"]
    assert sum(
        distribution[key]["components"]
        for key in ("island_tree_01", "island_tree_02", "island_tree_03")
    ) == ledger["integration"]["population_gate"]["components"] == 21
    assert sum(
        distribution[key]["instances"]
        for key in ("island_tree_01", "island_tree_02", "island_tree_03")
    ) == ledger["integration"]["population_gate"]["instances"] == 24830
    assert distribution["per_instance_selection_supported"] is False
    assert ledger["integration"]["all_original_world_transforms_restored"] is True
    assert ledger["integration"]["all_original_meshes_restored"] is True
    assert ledger["integration"]["saved_map_changed"] is False

    capture_root = REPO_ROOT / ledger["capture"]["directory"]
    for filename, expected_sha256 in ledger["capture"]["hashes"].items():
        capture_path = capture_root / filename
        assert capture_path.is_file()
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert all(value is False for value in ledger["authority"].values())
    assert ledger["milestone_gate"]["m9_passed"] is False
    assert ledger["milestone_gate"]["commit_allowed"] is False
    assert ledger["milestone_gate"]["push_allowed"] is False


def test_live_oak_cc0_island_tree_material_v1_review_is_isolated_and_fail_closed():
    canopy_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")
    internal_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    ).read_text(encoding="utf-8")
    ledger = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_live_oak_cc0_island_tree_material_v214_review.json"
        ).read_text(encoding="utf-8")
    )

    assert ledger["schema"] == (
        "raftsim.review.south_fork_live_oak_cc0_material.v214"
    )
    assert ledger["status"] == (
        "technical_material_override_validated_visual_promotion_rejected_"
        "ineffective"
    )
    assert ledger["production_promoted"] is False
    assert ledger["photoreal_accepted"] is False
    assert ledger["species_identity_approved"] is False
    assert "RaftSimOnlyLiveOakIslandTreeMaterialV1Review" in canopy_source
    assert "CreateSouthForkIslandTreeFoliageMaterialV1Review" in canopy_source
    assert "PlatformData->SizeX != 1024" in canopy_source
    assert "PlatformData->Mips.Num() < 10" in canopy_source
    assert "OpacityCoverageScale->R = 2.0f" in canopy_source
    assert "Material->OpacityMaskClipValue = 0.30f" in canopy_source
    assert "NormalDetail->R = 0.55f" in canopy_source
    assert "AmbientOcclusion->R = 0.78f" in canopy_source
    assert "RoughnessMinimum->R = 0.45f" in canopy_source
    assert "RoughnessMaximum->R = 0.85f" in canopy_source
    assert "no emissive compensation" in canopy_source
    assert "RaftSimLiveOakIslandTreeMaterialV1Review" in capture_source
    assert (
        "photographic_v214_live_oak_cc0_island_tree_material_v1"
        in capture_source
    )
    assert "Component->SetMaterial(1, IslandTreeLeafReviewMaterial)" in capture_source
    assert "OriginalOverrideMaterials" in internal_header
    assert "State.OriginalOverrideMaterials.Add" in capture_source
    assert "State.Component->EmptyOverrideMaterials()" in capture_source
    assert "only leaf slot 1 received the isolated V1 override" in capture_source

    material = ledger["authoring"]["material_contract"]
    assert material["shading_model"] == "TwoSidedFoliage"
    assert material["blend_mode"] == "Masked"
    assert material["opacity_coverage_scale"] == 2.0
    assert material["opacity_mask_clip"] == 0.30
    assert material["tangent_normal_detail"] == 0.55
    assert material["ambient_occlusion"] == 0.78
    assert material["emissive_compensation"] is False
    assert material["override_slot"] == 1
    assert material["trunk_slot_override"] is False
    assert material["branch_slot_override"] is False

    material_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
        "M_RaftSim_SouthForkInteriorLiveOakIslandTreeMaterialV1Review_Leaves.uasset"
    )
    assert material_path.is_file()
    assert hashlib.sha256(material_path.read_bytes()).hexdigest() == (
        ledger["authoring"]["material_sha256"]
    )
    texture_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
        "FutaleufuIslandTreeSet_1K"
    )
    texture_paths = {
        "albedo_sha256": texture_root
        / "T_IslandTree01_IslandTree01LeavesDiff1K.uasset",
        "opacity_sha256": texture_root
        / "T_IslandTree01_IslandTree01LeavesAlpha1K.uasset",
        "normal_sha256": texture_root
        / "T_IslandTree01_IslandTree01LeavesNorGl1K.uasset",
        "roughness_sha256": texture_root
        / "T_IslandTree01_IslandTree01LeavesRough1K.uasset",
    }
    for hash_key, texture_path in texture_paths.items():
        assert texture_path.is_file()
        assert hashlib.sha256(texture_path.read_bytes()).hexdigest() == (
            ledger["authoring"]["source_textures"][hash_key]
        )
    assert ledger["authoring"]["source_textures"]["packages_modified"] is False

    comparison = ledger["capture"]["comparison_to_v213"]
    assert comparison["mean_absolute_rgb_average"] == 0.021596
    assert comparison["percent_pixels_any_channel_gt_8_average"] == 0.089062
    assert len(comparison["byte_identical_views"]) == 3
    capture_root = REPO_ROOT / ledger["capture"]["directory"]
    for filename, expected_sha256 in ledger["capture"]["hashes"].items():
        capture_path = capture_root / filename
        assert capture_path.is_file()
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            expected_sha256
        )

    assert ledger["integration"]["all_original_world_transforms_restored"] is True
    assert ledger["integration"]["all_original_meshes_restored"] is True
    assert (
        ledger["integration"]["all_original_material_override_arrays_restored"]
        is True
    )
    assert ledger["integration"]["saved_map_changed"] is False
    assert all(value is False for value in ledger["authority"].values())
    assert ledger["milestone_gate"]["m9_passed"] is False
    assert ledger["milestone_gate"]["commit_allowed"] is False
    assert ledger["milestone_gate"]["push_allowed"] is False


def test_full_reach_boulder_dressing_uses_bounded_project_owned_presentation():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    editor_source = read_raftsim_editor_source(REPO_ROOT)
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")
    assert "LoadSouthForkProductionRockPresentation" in full_reach_source
    assert "SM_RaftSim_ProductionRiverBoulder" in editor_source
    assert "M_RaftSim_ProductionRiverBoulder" in editor_source
    assert "M_RaftSim_RiverBoulder" in editor_source
    assert "MI_RaftSim_SouthForkProductionBoulder" in editor_source
    assert "M_RaftSim_SouthForkBoulderDressing" in editor_source
    assert 'TEXT("RockWaterlineZCm")' in editor_source
    assert 'TEXT("RockWetBandWidthCm")' in editor_source
    assert "WaterlineAlbedo" in editor_source
    assert "WaterlineRoughness" in editor_source
    assert 'TEXT("BoulderAlbedoScale")), 0.70f' in editor_source
    assert "WorldAlignedTexture.WorldAlignedTexture" in editor_source
    assert "WorldAlignedNormal.WorldAlignedNormal" in editor_source
    assert (
        "RockGroundPhysicalWidthCm" in editor_source or "150.0f, false" in editor_source
    )
    assert "invalid external scan bounds" in editor_source
    assert "AcceptedBoulderPresentationFootprints" in full_reach_source
    assert "0.55f * (RadiusM + Accepted.RadiusM)" in editor_source
    assert "PresentationRadiusM * 0.8481f" in full_reach_source
    assert "static_cast<float>(HeightM) * 0.386f" in full_reach_source
    assert "Metrics.BoulderOverlapSuppressedInstanceCount" in full_reach_source
    assert 'TEXT("boulder_overlap_suppressed_instances")' in manifest_source


def test_full_reach_shore_cobbles_are_bounded_visual_only_procedural_infill():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    cobble_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkShoreCobbleDressing.cpp"
    ).read_text(encoding="utf-8")
    foliage_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFoliageSelection.cpp"
    ).read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")

    assert "CreateSouthForkShoreCobbleAssets" in full_reach_source
    assert "AddSouthForkShoreCobbleInstances" in full_reach_source
    assert "SM_RaftSim_SouthForkShoreCobble_%c" in cobble_source
    assert "BankDistanceM < 36.0f || BankDistanceM > 64.0f" in cobble_source
    assert "SetCollisionEnabled(ECollisionEnabled::NoCollision)" in cobble_source
    assert "SetCanEverAffectNavigation(false)" in cobble_source
    assert "bEnableNanite=*/false" in cobble_source
    assert "AddSouthForkBankUnderstoryInstance" in full_reach_source
    assert "SourceVegetationSignal" in cobble_source
    assert "BankDistanceM < 34.0f || BankDistanceM > 108.0f" in cobble_source
    assert "LateralSlope > 0.40f" in cobble_source
    assert "PatchNoise" in cobble_source
    assert "OuterBankFade" in cobble_source
    assert "SelectSouthForkDetailedFoliage" in full_reach_source
    assert "bUseWhiteAlder" in foliage_source
    assert "< 0.70f" in foliage_source
    assert "FoliageVariantRandom" in foliage_source
    assert "not a claim about a surveyed stem" in foliage_source
    assert "ShoreCobbleInstanceCount" in full_reach_source
    assert 'TEXT("procedural_noncolliding_shore_cobble_instances")' in manifest_source


def test_full_reach_ground_cover_breaks_up_repeated_terrain_without_gameplay_collision():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    ground_cover_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkGroundCover.cpp"
    ).read_text(encoding="utf-8")
    terrain_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainCoverage.cpp"
    ).read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")

    assert "CreateSouthForkGroundCoverAssets" in full_reach_source
    assert "DryGrassGroundCover" in full_reach_source
    assert "AddSouthForkGroundCoverInstances" in full_reach_source
    assert "BuildSouthForkSmoothedTerrainPresentationNormals" in full_reach_source
    assert "SM_RaftSim_SouthForkGrassTuft_A" in ground_cover_source
    assert "MSM_TwoSidedFoliage" in ground_cover_source
    assert "FMath::PerlinNoise2D" in ground_cover_source
    assert "constexpr int32 BladeCount = 52" in ground_cover_source
    assert "constexpr int32 LowLeafCount = 10" in ground_cover_source
    assert "BankDistanceM < 22.0f || BankDistanceM > 118.0f" in ground_cover_source
    assert "LateralSlope > 0.40f" in ground_cover_source
    assert "OuterBankFade" in ground_cover_source
    assert "ECollisionEnabled::NoCollision" in full_reach_source
    assert "SurfaceNormal.X * Jitter.X" in ground_cover_source
    assert "bUseCorridorEdgeBlend ? 0.44f : 0.92f" in terrain_source
    assert "GroundCoverInstanceCount" in full_reach_source
    assert (
        'TEXT("procedural_noncolliding_ground_cover_instances")'
        in manifest_source
    )


def test_live_breaking_water_uses_sparse_foam_and_feathered_moderate_arches():
    source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimWaterSurfaceActor.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCaptureCommand.cpp"
    ).read_text(encoding="utf-8")

    assert "ArchProfile" in source
    assert "(SafeIntensity - 0.55f) / 0.30f" in source
    assert 'TEXT("BreakingWaterOpacity"), 0.035f' in source
    assert 'TEXT("BreakingFoamOpacity"), 0.86f' in source
    assert 'TEXT("BreakingFoamIntensityGain"), 0.62f' in source
    assert 'TEXT("PrimaryLaceGain"), 0.45f' in source
    assert 'TEXT("DetailLaceGain"), 0.20f' in source
    assert "EdgeTaper * ProfileFeather" in source
    assert "ArchTravelCm = FMath::Lerp(280.0f, 380.0f" in source
    assert "SignedAcross * 13.1f" in source
    assert "CrestDistance = (CurlT - 0.28f) / 0.12f" in source
    assert "DownstreamShoulder" in source
    assert "CrestCore" in source
    assert 'TEXT("BreakingFoamCoreGain"), 1.25f' in source
    assert "ArchHeightCm = FMath::Lerp(30.0f, 105.0f" in source
    assert "CrestFragmentation" in source
    assert "SignedAcross * 17.3f" in source
    assert "NextProfile.X - PreviousProfile.X" in source
    assert 'TEXT("ActiveLiveSurfaceCoverage")' in source
    assert "ResolvedActiveLiveSurfaceCoverage" in source
    assert "constexpr int32 kAcrossSegments = 16" in source
    assert "constexpr int32 kCurlSegments = 16" in source
    assert "Downstream * 650.0f - Across * 160.0f" in capture_source
    assert 'CameraPreset.StartsWith(TEXT("breaking_water"))' in capture_source
    assert 'HasDiagnosticMode(TEXT("nobreakinglip"))' in capture_source
    assert 'HasDiagnosticMode(TEXT("nobreakingroller"))' in capture_source
    assert 'Component->GetName() == TEXT("BreakingLipMesh")' in capture_source
    assert 'Component->GetName() == TEXT("BreakingRollerVolumeMesh")' in capture_source
    assert "HideBreakingWaterPresentationComponents(" in capture_source
    assert "this exact screenshot callback" in capture_source
    assert "rapidRollerEmitters=%d" in capture_source
    assert 'HasDiagnosticMode(TEXT("norapidaerosol"))' in capture_source
    assert 'HasDiagnosticMode(TEXT("norapidroller"))' in capture_source
    assert "HideRapidNiagaraPresentationComponents(" in capture_source
    assert 'DiagnosticFloat(TEXT("terrainmacro="), -1.0f)' in capture_source
    assert 'TEXT("SourceMacroInfluence")' in capture_source
    assert 'DiagnosticFloat(TEXT("waterdetail="), -1.0f)' in capture_source
    assert 'TEXT("CalmRippleStrength")' in capture_source
    assert 'TEXT("FlowRippleStrength")' in capture_source
    assert 'TEXT("FoamRippleStrength")' in capture_source
    breaking_material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorBreakingWaterMaterial.cpp"
    ).read_text(encoding="utf-8")
    assert "FoamCoverage = Multiply(Foam, Foam)" in breaking_material_source


def test_full_reach_procedurally_completes_only_bounded_submerged_shoreline_holes():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    coverage_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainCoverage.cpp"
    ).read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")
    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorMaterialsBase.cpp"
    ).read_text(encoding="utf-8")

    assert "CompleteSouthForkShorelinePresentation(" in full_reach_source
    assert "ElevationM - TerrainElevationM" in full_reach_source
    assert "Metrics.ProceduralShorelineCompletionVertexCount" in full_reach_source
    assert "MinimumCompletedShorelineDepthM = 0.03f" in coverage_source
    assert "MaximumCompletedShorelineDepthM = 0.25f" in coverage_source
    assert "HydraulicPresentation.A <= 0.5f" in coverage_source
    assert (
        "ShorelineDepthM >= SouthForkMinimumCompletedShorelineDepthM" in coverage_source
    )
    assert (
        "ShorelineDepthM <= SouthForkMaximumCompletedShorelineDepthM" in coverage_source
    )
    assert "HydraulicPresentation.A = 1.0f" in coverage_source
    assert "++InOutCompletionVertexCount" in coverage_source
    assert "authoritative solver arrays" in coverage_source
    assert "nor adds collision" in coverage_source
    assert "bAnyWetVertex" in coverage_source
    assert "bAllWetVertices" in coverage_source
    assert "five-centimetre terrain-clipped bank skirt" in coverage_source
    assert "++InOutTransitionCellCount" in coverage_source
    assert "BuildSouthForkTerrainClippedWaterGeometry(" in full_reach_source
    assert "SouthForkMinimumVisibleWaterDepthM = 0.005f" in coverage_source
    assert "Vertex.Color.A - 0.5f" in coverage_source
    assert (
        "Vertex.ShorelineDepthM -\n                            "
        "SouthForkMinimumVisibleWaterDepthM" in coverage_source
    )
    assert "TerrainClippedWaterVertices" in full_reach_source
    assert "RefineSouthForkWaterPresentationGrid(2" in full_reach_source
    assert "ApplySouthForkWaterPresentationMicroRelief" in full_reach_source
    assert "ComputeSouthForkAeratedWaterOverlaySample" in coverage_source
    assert "M_RaftSim_SolverFieldFoamCandidate" in full_reach_source
    assert "Material->BlendMode = BLEND_Masked" in material_source
    assert "Material->OpacityMaskClipValue = 0.18f" in material_source
    assert "EditorOnlyData->OpacityMask.Expression = FoamMaskExpression" in (
        material_source
    )
    assert 'TEXT("SolverOverlayFoamLace")' in material_source
    assert "SolverMaskedLace->A.Expression = VertexColor" in material_source
    assert "SolverMaskedLace->A.OutputIndex = 4" in material_source
    assert "SolverMaskedLace->B.Expression = FoamLaceSample" in material_source
    assert "SolverMaskedLace->B.OutputIndex = 1" in material_source
    assert "MPC_RaftSim_RaftFoamOcclusion" in material_source
    assert 'TEXT("RaftFoamExclusionEnabled")' in material_source
    assert 'TEXT("RaftFoamExclusionCenterAndHalfWidthCm")' in material_source
    assert 'TEXT("RaftFoamExclusionForwardAndHalfLengthCm")' in material_source
    assert 'TEXT("RaftInteriorWaterTransmissionEnabled")' in material_source
    assert 'TEXT("RaftInteriorWaterCenterAndHalfWidthCm")' in material_source
    assert 'TEXT("RaftInteriorWaterForwardAndHalfLengthCm")' in material_source
    assert "FLinearColor(0.0f, 0.0f, 0.0f, 82.0f)" in material_source
    assert "FLinearColor(1.0f, 0.0f, 0.0f, 215.0f)" in material_source
    assert "Raft and crew foam-layer exclusion" in material_source
    assert "smoothstep(0.62, 1.0, EllipseSquared)" in material_source
    assert "OcclusionSafeFoamMask->A.Expression = FoamMaskExpression" in (
        material_source
    )
    assert "Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes)" in (
        material_source
    )
    assert "RaftSimSolverFoamOverlay" in full_reach_source
    assert "MaximumOpacity >= 0.025f" in coverage_source
    assert "MeanOpacity >= 0.006f" in coverage_source
    assert "ActiveCells.Init(0, CellCount)" in coverage_source
    assert "OverlayCells.Init(0, CellCount)" in coverage_source
    assert "constexpr int32 TransparentPaddingCells = 2" in coverage_source
    assert "HydraulicPresentation[VertexIndex].A < 0.90f" in coverage_source
    assert "ShorelineDepthsM[VertexIndex] <= 0.10f" in coverage_source
    assert "OutTriangles.Append({I0, I1, I2, I1, I3, I2})" in coverage_source
    assert "SolverFoam <= 0.0f" in coverage_source
    assert "Sample.VerticalDisplacementCm" in coverage_source
    assert "Sample.VerticalDisplacementCm = FMath::Clamp(" in coverage_source
    assert "14.0f);" in coverage_source
    assert 'TEXT("solver_and_guide_conditioned_whitewater_foam_overlays")' in (
        manifest_source
    )
    assert 'TEXT("whitewater_foam_overlays_affect_hydraulics"), false' in (
        manifest_source
    )
    assert "const float CalmReliefM" in coverage_source
    assert "const float HydraulicReliefM" in coverage_source
    assert "const float BreakingReliefM" in coverage_source
    assert "0.260f * FMath::Sin(" in coverage_source
    assert "0.160f * FMath::Sin(" in coverage_source
    assert "RefinedWidth = (SourceWidth - 1) * SubdivisionFactor + 1" in coverage_source
    assert "BuildSouthForkRefinedWhitewaterOverlayGeometry" in full_reach_source
    assert "BuildSouthForkRefinedWhitewaterOverlayGeometry" in coverage_source
    assert "one-metre refined non-colliding" in manifest_source
    assert "complete paired quads" in manifest_source
    assert 'TEXT("whitewater_foam_complete_paired_quad_topology"), true' in (
        manifest_source
    )
    assert "capped at 0.14 m" in manifest_source
    assert 'FMaterialParameterInfo(TEXT("TerrainSpecular"))' in coverage_source
    assert "bUseCorridorEdgeBlend ? 0.0f : 0.12f" in coverage_source
    assert "reflected the sky a" in coverage_source
    assert "second time" in coverage_source
    assert "LoadSouthForkProductionWaterPresentation(WaterMaterial" in full_reach_source
    water_presentation_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkWaterPresentation.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("ShallowWaterOpacity")), 0.76f' in water_presentation_source
    assert 'TEXT("DeepWaterOpacity")), 0.82f' in water_presentation_source
    assert 'TEXT("HydraulicFoamIntensity")), 0.0f' in water_presentation_source
    assert 'TEXT("HydraulicFoamCoverageGain")), 0.82f' in water_presentation_source
    assert 'TEXT("WaterRoughness")), 0.24f' in water_presentation_source
    assert 'TEXT("Specular")), 0.28f' in water_presentation_source
    assert 'TEXT("FresnelSpecular")), 0.18f' in water_presentation_source
    assert 'TEXT("FallbackSkyReflectionStrength")), 0.28f' in water_presentation_source
    assert 'TEXT("CalmSurfaceColorVariation")), 0.14f' in water_presentation_source
    assert 'TEXT("FallbackSkyReflectionFloor")), 0.68f' in water_presentation_source
    assert 'TEXT("FallbackSkyReflectionVariation")), 0.32f' in water_presentation_source
    assert 'TEXT("CalmRippleStrength")), 0.055f' in water_presentation_source
    assert 'TEXT("FlowRippleStrength")), 0.075f' in water_presentation_source
    assert 'TEXT("FoamRippleStrength")), 0.110f' in water_presentation_source
    assert "M_RaftSim_SouthForkRaftTransmissionWater" in water_presentation_source
    assert "RaftSimRaftInteriorWaterTransmission" in water_presentation_source
    assert "RaftSimRaftInteriorWaterOpticalDepth" in water_presentation_source
    assert "RaftSimOpticalDepthResponse" in water_presentation_source
    assert "OpticalDepthResponseExponent" in water_presentation_source
    assert "DepthBlend->Alpha.Expression = OpticalDepthResponse" in (
        water_presentation_source
    )
    assert "pow(Along, 4.0) + pow(Across, 4.0)" in water_presentation_source
    assert 'TEXT("RaftInteriorSurfaceOpacityScale")), 0.0f' in (
        water_presentation_source
    )
    assert 'TEXT("RaftInteriorOpticalDepthScale")), 0.0f' in (
        water_presentation_source
    )
    assert "FLinearColor(1.0f, 1.0f, 1.0f, 0.0f)" in water_presentation_source
    assert "LoadOrCreateReadableRaftFloorMaterial" in water_presentation_source
    assert "M_RaftSim_RaftFloorReadable" in material_source
    assert 'TEXT("FloorShadowFill")' in material_source
    assert "ShadowFill->DefaultValue = 0.28f" in material_source
    water_surface_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimWaterSurfaceActor.cpp"
    ).read_text(encoding="utf-8")
    water_surface_header = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimWaterSurfaceActor.h"
    ).read_text(encoding="utf-8")
    assert "UpdateRaftFoamExclusionParameters" in water_surface_source
    assert "RaftFoamExclusionHalfWidthCm = 190.0f" in water_surface_source
    assert "RaftFoamExclusionHalfLengthCm = 320.0f" in water_surface_source
    assert 'TEXT("RaftFoamExclusionEnabled"), 1.0f' in water_surface_source
    assert "RaftInteriorWaterHalfWidthCm = 82.0f" in water_surface_source
    assert "RaftInteriorWaterHalfLengthCm = 215.0f" in water_surface_source
    assert 'TEXT("RaftInteriorWaterTransmissionEnabled"), 1.0f' in (
        water_surface_source
    )
    assert "TObjectPtr<UMaterialParameterCollection>" in water_surface_header
    assert "TObjectPtr<ARaftSimRaftActor> FoamOcclusionRaft" in (
        water_surface_header
    )
    assert 'TEXT("ShallowWaterColor"))' in water_presentation_source
    assert "FLinearColor(0.026f, 0.050f, 0.058f, 0.0f)" in water_presentation_source
    assert 'TEXT("DeepWaterColor"))' in water_presentation_source
    assert "FLinearColor(0.010f, 0.024f, 0.032f, 0.0f)" in water_presentation_source
    assert 'TEXT("ReflectedSkyColor"))' in water_presentation_source
    assert "FLinearColor(0.100f, 0.160f, 0.220f, 0.0f)" in water_presentation_source
    assert 'TEXT("WaterScattering"))' in water_presentation_source
    assert (
        "FLinearColor(0.00018f, 0.00023f, 0.00028f, 0.0f)" in water_presentation_source
    )
    assert 'TEXT("WaterAbsorption"))' in water_presentation_source
    assert "FLinearColor(0.0055f, 0.0044f, 0.0038f, 0.0f)" in water_presentation_source
    assert 'TEXT("RiverbedColorScale"))' in water_presentation_source
    assert "FLinearColor(0.22f, 0.23f, 0.23f, 0.0f)" in water_presentation_source
    assert "MinimumHalfWidthCm = FMath::Lerp(" in (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimWaterSurfaceActor.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("procedural_shoreline_completion_applied")' in manifest_source
    assert 'TEXT("procedural_shoreline_completion_vertices")' in manifest_source
    assert 'TEXT("procedural_shoreline_transition_cells")' in manifest_source
    assert "visual only, no collision or hydraulics" in manifest_source


def test_full_reach_fixed_captures_lock_time_and_temporal_history():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCapture.cpp"
    ).read_text(encoding="utf-8")

    assert 'TEXT("r.Tonemapper.GrainQuantization")' in capture_source
    assert "GrainQuantizationVariable->Set(0, ECVF_SetByCode)" in capture_source
    assert capture_source.count("RestoreCaptureVariables();") == 2
    assert "Component->PostProcessSettings.FilmGrainIntensity = 0.0f" in capture_source
    assert 'TEXT("r.Test.OverrideTimeMaterialExpressions")' in capture_source
    assert "MaterialTimeVariable->Set(1.0f, ECVF_SetByCode)" in capture_source
    assert "Component->ShowFlags.SetTemporalAA(false)" in capture_source
    assert "Component->ShowFlags.SetMotionBlur(false)" in capture_source
    assert "Component->ShowFlags.SetEyeAdaptation(false)" in capture_source
    assert "Component->ShowFlags.SetLumenGlobalIllumination(false)" in capture_source
    assert "Component->ShowFlags.SetLumenReflections(false)" in capture_source
    assert 'TEXT("RaftSimPhotographicSouthForkCapture")' in capture_source
    assert 'TEXT("RaftSimVolumetricBroadleafReviewCapture")' in capture_source
    assert "PhotographicCaptureDirectoryRelativePath" in capture_source
    assert "VolumetricBroadleafCaptureDirectoryRelativePath" in capture_source
    assert "photographic_v169_broadleaf" in capture_source
    assert "Component->ShowFlags.SetTemporalAA(true)" in capture_source
    assert "Component->ShowFlags.SetLumenGlobalIllumination(true)" in capture_source
    assert "Component->ShowFlags.SetLumenReflections(true)" in capture_source
    assert "const int32 SettleFrameCount = bPhotographicCapture ? 12 : 1" in (
        capture_source
    )
    assert "no actor, package, material, or gameplay authority is written" in (
        capture_source
    )
    assert "WorldPartition->LoadAllActors(LoadedActorReferences)" in full_reach_source
    assert "TActorIterator<AWorldPartitionHLOD>" in capture_source
    assert "Component->SetVisibility(false, true)" in capture_source
    assert 'TEXT("RaftSimFlowBand_%s")' in capture_source
    assert "Component->SetVisibility(bIsActiveFlowBand, true)" in capture_source
    assert "RestoreSouthForkSettledSourceCaptureVisibility" in full_reach_source
    assert 'TEXT("RaftSimSourceHlodExclusiveWaterReview")' in capture_source
    assert "photographic_v180_source_hlod_exclusive" in capture_source
    assert 'TEXT("RaftSimSolverDerivedAerationReview")' in capture_source
    assert "photographic_v181_solver_derived_aeration" in capture_source
    assert 'TEXT("RaftSimSolverGatedBreakingReliefReview")' in capture_source
    assert "photographic_v182_solver_gated_breaking_relief" in capture_source
    assert 'TEXT("RaftSimGuideFeatureBreakingReliefReview")' in capture_source
    assert "photographic_v183_guide_feature_breaking_relief" in capture_source
    assert 'TEXT("RaftSimRefinedGuideFeatureFoamReview")' in capture_source
    assert "photographic_v184_refined_guide_feature_foam" in capture_source
    assert full_reach_source.count(
        '{TEXT("troublemaker_approach"), 8328.0f, -2.0f, 2.2f, false}'
    ) == 2
    assert "FindSouthForkMedianWaterSurfaceLocalZCm" in full_reach_source
    assert "without regeneration" in full_reach_source


def test_generated_canopy_provenance_matches_three_independent_ponderosa_sources():
    source_root = REPO_ROOT / "unreal/SourceArt/RaftSim/Environment/GeneratedCanopy"
    provenance = json.loads(
        (source_root / "provenance.json").read_text(encoding="utf-8")
    )
    ponderosa = [
        asset
        for asset in provenance["assets"]
        if asset["species"] == "Pinus ponderosa"
        and asset["profile"].endswith("_photoreal_v2")
    ]

    assert {asset["profile"] for asset in ponderosa} == {
        "mature_photoreal_v2",
        "intermediate_photoreal_v2",
        "young_photoreal_v2",
    }
    assert len({asset["chroma_sha256"] for asset in ponderosa}) == 3
    assert len({asset["alpha_sha256"] for asset in ponderosa}) == 3
    for asset in ponderosa:
        chroma = source_root / asset["chroma_source"]
        alpha = source_root / asset["alpha_source"]
        assert hashlib.sha256(chroma.read_bytes()).hexdigest() == asset["chroma_sha256"]
        assert hashlib.sha256(alpha.read_bytes()).hexdigest() == asset["alpha_sha256"]

    white_alder = next(
        asset
        for asset in provenance["assets"]
        if asset["species"] == "Alnus rhombifolia"
        and asset["profile"].endswith("_photoreal_v2")
    )
    assert white_alder["profile"] == "mature_riparian_photoreal_v2"
    for key, hash_key in (
        ("chroma_source", "chroma_sha256"),
        ("alpha_source", "alpha_sha256"),
    ):
        source = source_root / white_alder[key]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == white_alder[hash_key]

    editor_source = read_raftsim_editor_source(REPO_ROOT)
    assert "T_WhiteAlder_PhotorealV2.png" in editor_source
    assert 'TEXT("SouthForkWhiteAlder")' in editor_source
    assert 'TEXT("WhiteAlderRiparian"), RiparianMesh' in editor_source
    assert "/*bEnableDensityScaling=*/false, /*bCastShadow=*/true);" in editor_source
    assert "MSM_TwoSidedFoliage" in editor_source
    assert "EditorOnlyData->SubsurfaceColor" in editor_source
    assert "bUseAlderAmbientFill" not in editor_source
    assert 'TEXT("WillowAlderProxy"), BroadleafMesh' not in editor_source


def test_photoreal_materials_preserve_physical_detail_scale_and_natural_water_normals():
    source_path = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    )
    source = source_path.read_text(encoding="utf-8")
    source += (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealTextureAssets.cpp"
    ).read_text(encoding="utf-8")

    assert "RockGroundPhysicalWidthCm = 150.0f" in source
    assert "SouthForkBankPhysicalWidthCm = 320.0f" in source
    assert 'TEXT("RockNormal")' in source
    assert 'TEXT("GroundNormal")' in source
    assert 'TEXT("RockRough")' in source
    assert 'TEXT("GroundPacked")' in source
    assert (
        'FlowNormalSpec.MapKind = TEXT("project_owned_multiscale_river_flow_normal")'
        in source
    )
    assert "FlowNormalSpec.AddressX = TA_Mirror" in source
    assert "FlowNormalSpec.AddressY = TA_Mirror" in source
    assert 'TEXT("WaterFlowNormalPrimary")' in source
    assert 'TEXT("WaterFlowNormalCross")' in source
    assert "CombinedNormal->VectorInput.Expression" in source
    assert "UV->UTiling = 0.62f" in source
    assert "UV->VTiling = 0.90f" in source
    assert "CrossUv->UTiling = 1.31f" in source
    assert "CrossUv->VTiling = 1.72f" in source
    assert 'Scalar(TEXT("CalmRippleStrength"), 0.035f)' in source
    assert 'Scalar(TEXT("FoamRippleStrength"), 0.085f)' in source
    assert 'Scalar(TEXT("FlowRippleStrength"), 0.045f)' in source
    assert "NormalStrength->MaxDefault = 0.14f" in source
    assert 'Scalar(TEXT("RippleGrazingFloor"), 0.25f)' in source
    assert "GrazingFilteredNormalStrength" in source
    assert "RippleGrazingFresnel->Normal.Expression = FlatN" in source
    assert 'Scalar(TEXT("WaterRoughness"), 0.24f)' in source
    assert 'Scalar(TEXT("ShallowWaterOpacity"), 0.62f)' in source
    assert 'Scalar(TEXT("DeepWaterOpacity"), 0.80f)' in source
    assert 'Scalar(TEXT("FoamWaterOpacity"), 0.90f)' in source
    assert "Lerp(ShallowOpacity, DeepOpacity, DepthMask)" in source
    assert "Lerp(DepthOpacity, FoamOpacity, FoamBroken)" in source
    assert 'Scalar(TEXT("FallbackSkyReflectionStrength"), 0.32f)' in source
    assert 'Scalar(TEXT("FallbackSkyReflectionFloor"), 0.72f)' in source
    assert 'Scalar(TEXT("FallbackSkyReflectionVariation"), 0.28f)' in source
    assert "SkyReflectionAlpha, SkyReflectionVariation" in source
    assert 'Scalar(TEXT("WaterPhaseG"), 0.15f)' in source
    assert 'Scalar(TEXT("HydraulicWhitewaterGain"), 0.42f)' in source
    assert 'Scalar(TEXT("HydraulicFoamIntensity"), 1.0f)' in source
    assert "SpeedWhitewater->MaxDefault = 0.12f" in source
    assert "NegativeFoamThreshold->R = -0.28f" in source
    assert 'Scalar(TEXT("HydraulicFoamCoverageGain"), 0.95f)' in source
    assert "FoamNoise->Scale = 0.045f" in source
    assert "FoamNoise->OutputMin = 0.0f" in source
    assert "FoamNoise->OutputMax = 1.0f" in source
    assert 'Scalar(TEXT("HydraulicFoamColorBreakupBias"), 0.0f)' in source
    assert 'Scalar(TEXT("HydraulicFoamColorBreakupGain"), 0.78f)' in source
    assert 'Scalar(TEXT("HydraulicFoamColorCoreGain"), 1.25f)' in source
    assert "Const3(0.48f, 0.53f, 0.52f)" in source
    assert (
        "UMaterialExpressionMultiply* FoamRaw = Mul(FoamColorCore, FoamColorBreakup)"
        in source
    )
    assert 'Mul(FoamMask, Scalar(TEXT("FoamRippleStrength"), 0.085f))' in source
    assert "UMaterialExpressionMultiply* FoamRough = Mul(FoamBroken" in source
    assert "BuildRiverBoulderMaterial()" in source
    assert "ExistingExpression->MarkAsGarbage()" in source
    assert 'TEXT("RaftSim.CreateRiverBoulderMaterial")' in source
    assert 'TEXT("RaftSim.CreateProductionCrewWetsuitMaterial")' in source
    assert "BuildProductionCrewWetsuitMaterial()" in source
    assert 'TEXT("RaftSim.CreateProductionRaftMaterials")' in source
    assert "BuildProductionRaftMaterials()" in source
    assert 'TEXT("RaftSim.CreateProductionCC0SkinMaterials")' in source
    assert "BuildProductionCC0SkinMaterials()" in source
    assert "Material->SetMaterialUsage(MATUSAGE_SkeletalMesh)" in source
    assert "CoarseMineralNoise->Scale = 0.016f" in source
    assert "FineMineralNoise->Scale = 0.055f" in source
    assert 'TEXT("ReviewedRockRoughness")' in source
    assert 'TEXT("ReviewedRockBaseColor")' in source
    assert "removing most source hue" in source
    assert 'TEXT("ReviewedRockBaseColor")' in source
    assert 'TEXT("ReviewedRockNormal")' in source
    assert "It is an appearance analog, not South Fork geology authority" in source
    assert "wet mineral material saved=%d" in source
    assert 'TEXT("ShallowWaterColor"), FLinearColor(0.018f, 0.035f, 0.040f' in source
    assert 'TEXT("DeepWaterColor"), FLinearColor(0.006f, 0.015f, 0.021f' in source
    assert "FLinearColor(0.16f, 0.17f, 0.17f" in source
    assert "FLinearColor(0.00012f, 0.00014f, 0.00016f" in source
    assert "FLinearColor(0.0065f, 0.0052f, 0.0046f" in source
    assert "MacroInfluence->DefaultValue = 0.64f" in source


def test_live_water_surface_avoids_double_volume_transmission():
    source_path = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimWaterSurfaceActor.cpp"
    )
    source = source_path.read_text(encoding="utf-8")

    assert "M_RaftSim_LiveRiverSurface.M_RaftSim_LiveRiverSurface" in source
    assert "SurfaceMesh->SetMaterial(0, WaterMaterial)" in source
    assert 'TEXT("ActiveLiveSurfaceCoverage")' in source
    assert "ResolvedActiveLiveSurfaceCoverage" in source
    assert 'TEXT("LiveWaterSpecular")' in source
    assert "RiverWaterConfig->LiveSurfaceSpecular" in source
    assert "CreateDynamicMaterialInstance(0, WaterMaterial)" in source

    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("M_RaftSim_LiveRiverSurface")' in material_source
    assert "BuildLiveRiverSurfaceMaterial()" in material_source
    assert 'TEXT("RaftSim.CreateLiveRiverSurfaceMaterial")' in material_source
    assert "CreateLiveRiverSurfaceMaterial(FString& OutSummary)" in material_source
    module_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/"
        "RaftSimEditorModule.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("RaftSimCreateLiveRiverSurfaceMaterial")' in module_source
    environment_automation_source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
        "RaftSimEditorEnvironmentAutomation.cpp"
    ).read_text(encoding="utf-8")
    assert "if (RiverIdFilter.IsEmpty())" in environment_automation_source
    assert "Reusing reviewed shared solver-field textures" in (
        environment_automation_source
    )
    assert 'Scalar(TEXT("LiveFoamIntensity"), 0.52f)' in material_source
    assert 'Scalar(TEXT("LiveWaterRoughness"), 0.085f)' in material_source
    assert 'Scalar(TEXT("LiveRippleStrength"), 0.18f)' in material_source
    assert 'TEXT("LiveShallowSurfaceColor")' in material_source
    assert "FLinearColor(0.115f, 0.185f, 0.175f" in material_source
    assert 'TEXT("LiveDeepSurfaceColor")' in material_source
    assert "FLinearColor(0.035f, 0.080f, 0.095f" in material_source
    assert 'Scalar(TEXT("LiveSkyReflectionStrength"), 0.62f)' in material_source
    assert 'Scalar(TEXT("CalmLiveSurfaceCoverage"), 0.0f)' in material_source
    assert 'Scalar(TEXT("ActiveLiveSurfaceCoverage"), 0.03f)' in material_source
    assert 'Scalar(TEXT("HydraulicCoverageFoamGain"), 0.95f)' in material_source
    assert (
        'Scalar(TEXT("HydraulicCoverageSpeedThresholdBias"), -0.28f)' in material_source
    )
    assert 'Scalar(TEXT("HydraulicCoverageSpeedGain"), 2.2f)' in material_source
    assert "SpeedCoverage" in material_source
    assert "StationEdgeCoverage, HydraulicCoverage" in material_source
    assert "StationEdgeCoverage->Input.OutputIndex = 4" in material_source
    assert 'TEXT("LiveWaterFlowNormalPrimary")' in material_source
    assert 'TEXT("LiveWaterFlowNormalCross")' in material_source
    assert 'TEXT("LiveRippleGrazingFloor")' in material_source
    assert "LiveGrazingFilteredNormalStrength" in material_source
    assert "LiveRippleGrazingFresnel->Normal.Expression = LiveFlatN" in (
        material_source
    )
    assert "Material->BlendMode = BLEND_Translucent" in material_source
    assert "Material->TranslucencyLightingMode = TLM_SurfacePerPixelLighting" in (
        material_source
    )
    assert "DitherTemporalAA.DitherTemporalAA" not in material_source
    assert "Ed->Opacity.Connect(0, SurfaceCoverage)" in material_source

    header_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimWaterSurfaceActor.h"
    ).read_text(encoding="utf-8")
    assert "CurvedGridEdgeBlendMeters = 36.0f" in header_source
    assert "CurvedGridLateralEdgeBlendMeters = 9.0f" in header_source
    assert "SurfaceMesh->SetCastShadow(false)" in source
    assert "ComputeStationEdgeCoverage" in source
    assert "LinearCoverage * LinearCoverage * (3.0f - 2.0f * LinearCoverage)" in source
    assert 'TEXT("BreakingLipMesh")' in source
    assert "ComputeBreakingLipProfileCentimeters" in source
    assert "const float ArchTravelCm" in source
    assert "const float ArchHeightCm" in source
    assert "const FVector2D ArchProfile" in source
    assert "FMath::Lerp(ArchProfile, CurlProfile, CurlBlend)" in source
    assert "ComputePresentationSurfaceEdgeClearanceMeters" in source
    assert "PresentationCoverage < kMinimumFullCoverage" in source
    assert "BreakingSiteInteriorClearanceMeters" in source
    assert "edge_rejected_sites=%d" in source
    assert "RebuildBreakingLipMesh" in source
    assert (
        "BreakingLipMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in source
    )
    assert "BreakingLipMesh->SetCastShadow(false)" in source
    assert "constexpr int32 kAcrossSegments = 16" in source
    assert "constexpr int32 kCurlSegments = 16" in source
    assert "BreakingLipTriangleCount = LipTriangles.Num() / 3" in source
    assert 'TEXT("BreakingRollerVolumeMesh")' in source
    assert "ComputeBreakingRollerVolumeProfileCentimeters" in source
    assert "RebuildBreakingRollerVolumeMesh" in source
    assert "HideBreakingRollerVolumeMesh" in source
    assert (
        "BreakingRollerVolumeMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)"
        in source
    )
    assert "BreakingRollerVolumeMesh->SetCastShadow(false)" in source
    assert "constexpr int32 kMaximumRollerSites = 3" in source
    assert "constexpr int32 kLayerCount = 1" in source
    assert "constexpr int32 kAcrossSegments = 18" in source
    assert "constexpr int32 kLoopSegments = 14" in source
    assert "const float ProfileLoopT = FMath::Lerp(0.48f, 1.0f, LoopT)" in source
    assert "BreakingRollerVolumeMesh->SetMaterial(0, RapidFoamMaterial)" in source
    assert 'TEXT("SolverOverlayFoamLace")' in source
    assert "BreakingRollerVolumeTriangleCount = RollerTriangles.Num() / 3" in source
    assert source.count("M_RaftSim_BreakingWaterLip") >= 2
    assert "PresentationCoverage = 0.0f" in header_source
    assert "RiverCoordinatesMeters = FVector2D::ZeroVector" in header_source
    assert "PresentationEdgeClearanceMeters = 0.0f" in header_source
    assert "BreakingSiteInteriorClearanceMeters = 15.0f" in header_source

    breaking_material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorBreakingWaterMaterial.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("RaftSim.CreateBreakingWaterLipMaterial")' in breaking_material_source
    assert 'TEXT("M_RaftSim_BreakingWaterLip")' in breaking_material_source
    assert "Material->BlendMode = BLEND_Translucent" in breaking_material_source
    assert "T_RaftSim_SouthForkWater_FoamLace" in breaking_material_source
    assert "T_RaftSim_SouthForkWater_FlowNormal" in breaking_material_source
    assert "Material->TwoSided = true" in breaking_material_source
    assert "Sample->SamplerType = SAMPLERTYPE_Masks" in breaking_material_source
    assert "EdgeFeather->Input.OutputIndex = 4" in breaking_material_source
    assert 'Scalar(TEXT("BreakingFoamCoreGain"), 0.70f)' in (breaking_material_source)
    assert 'Scalar(TEXT("BreakingWaterOpacity"), 0.38f)' in breaking_material_source
    assert 'Scalar(TEXT("BreakingFoamOpacity"), 0.84f)' in breaking_material_source

    breaking_material_script = (
        REPO_ROOT / "unreal/Scripts/create_breaking_water_lip_material.py"
    ).read_text(encoding="utf-8")
    assert 'COMMAND = "RaftSim.CreateBreakingWaterLipMaterial"' in (
        breaking_material_script
    )
    assert "M_RaftSim_BreakingWaterLip" in breaking_material_script
    assert "unreal.BlendMode.BLEND_TRANSLUCENT" in breaking_material_script
    assert "T_RaftSim_SouthForkWater_FoamLace" in breaking_material_script
    assert "T_RaftSim_SouthForkWater_FlowNormal" in breaking_material_script

    capture_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCaptureCommand.cpp"
    ).read_text(encoding="utf-8")
    assert "ResolveBreakingWaterEvidenceCameraPose" in capture_source
    assert "breakingRollerTriangles=%d" in capture_source
    assert "breakingRollerVisible=%d" in capture_source
    assert 'CameraPreset.StartsWith(TEXT("breaking_water"))' in capture_source


def test_broad_water_uses_project_owned_flow_aligned_solver_masked_foam_lace():
    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    texture_asset_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealTextureAssets.cpp"
    ).read_text(encoding="utf-8")
    generator_path = (
        REPO_ROOT / "unreal/Scripts/build_production_whitewater_foam_texture.py"
    )
    texture_path = (
        REPO_ROOT / "unreal/SourceArt/RaftSim/Water/"
        "T_RaftSim_SouthForkWater_FoamLace.png"
    )
    provenance_path = texture_path.with_suffix(".provenance.json")

    assert generator_path.is_file()
    assert texture_path.is_file()
    assert provenance_path.is_file()
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["generator_version"] == (
        "raftsim-production-whitewater-foam-lace-v4"
    )
    assert provenance["ownership"] == "project_owned_first_party_procedural"
    assert provenance["external_source_input"] is False
    assert provenance["authoritative_geography_claim"] is False
    assert provenance["dimensions_px"] == [1024, 1024]
    assert provenance["random_seed"] == 20260728
    assert provenance["multiscale_octaves"] == 5
    assert provenance["authored_polyline_count"] == 0
    assert hashlib.sha256(texture_path.read_bytes()).hexdigest() == provenance["sha256"]

    assert 'FoamLaceSpec.MapKey = TEXT("FoamLace")' in texture_asset_source
    assert (
        'FoamLaceSpec.MapKind = TEXT("project_owned_flow_aligned_whitewater_foam_breakup")'
        in texture_asset_source
    )
    assert "T_RaftSim_SouthForkWater_FoamLace" in material_source
    assert 'FoamLaceSample->ParameterName = TEXT("WhitewaterFoamLace")' in (
        material_source
    )
    assert "FoamUv->UTiling = 0.42f" in material_source
    assert "FoamUv->VTiling = 0.93f" in material_source
    assert "FoamPan->SpeedX = 0.018f" in material_source
    assert "FoamBreakupSource = Mask(FoamLaceSample, true, false, false)" in (
        material_source
    )
    assert 'Scalar(TEXT("HydraulicFoamColorBreakupBias"), 0.0f)' in (material_source)
    assert 'Scalar(TEXT("HydraulicFoamColorBreakupGain"), 0.78f)' in (material_source)
    assert "UMaterialExpressionMultiply* FoamRough = Mul(FoamBroken" in (
        material_source
    )


def test_water_presentation_material_regeneration_does_not_touch_boulder_package():
    script = (
        REPO_ROOT / "unreal/Scripts/create_water_presentation_materials.py"
    ).read_text(encoding="utf-8")

    assert '"RaftSim.CreatePhotorealRiverWaterMaterial"' in script
    assert '"RaftSim.CreateWaterVfxMaterial"' in script
    assert "RaftSim.CreateRiverBoulderMaterial" not in script
    assert "delete_asset" not in script


def test_river_water_visual_experiments_use_an_isolated_preview_package():
    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    capture_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCaptureCommand.cpp"
    ).read_text(encoding="utf-8")

    assert 'TEXT("RaftSim.CreatePhotorealRiverWaterPreviewMaterial")' in material_source
    assert (
        "/Game/RaftSim/Experiments/M_RaftSim_PhotorealRiverWater_Preview"
        in material_source
    )
    assert (
        "Visual experiments must never resave the reviewed production package"
        in material_source
    )
    assert 'DiagnosticString(TEXT("watermaterial="))' in capture_source
    assert "AuthoredWaterMaterialOverride->GetPathName()" in capture_source
    assert "WaterComponent->SetMaterial(" in capture_source
    assert '"[watermaterial=/Game/path.Asset]"' in capture_source

    audit_script = (
        REPO_ROOT / "unreal/Scripts/audit_water_material_parity.py"
    ).read_text(encoding="utf-8")
    assert '"read_only": True' in audit_script
    assert "get_material_expressions" in audit_script
    assert "get_inputs_for_material_expression" in audit_script
    assert "save_asset" not in audit_script
    assert "structurally_equal" in audit_script


def test_rigged_mannequin_fallback_preserves_project_owned_rafting_gear():
    raft_source_root = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft"
    host_source = (raft_source_root / "Private/RaftSimCrewAvatarActor.cpp").read_text(
        encoding="utf-8"
    )
    rig_source = (
        raft_source_root / "Private/RaftSimMannyCrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    rig_header = (raft_source_root / "Public/RaftSimMannyCrewVisualActor.h").read_text(
        encoding="utf-8"
    )

    assert "IRaftSimCrewProductionVisual" in rig_header
    assert "UPoseableMeshComponent" in rig_header
    assert "SKM_Manny_Simple.SKM_Manny_Simple" in rig_source
    assert "URaftSimCrewAvatarPoseLibrary::EvaluatePose" in rig_source
    assert "UMaterialInstanceDynamic::Create" in rig_source
    assert 'TEXT("Paint Tint")' in rig_source
    for bone_name in (
        "spine_03",
        "upperarm_l",
        "lowerarm_l",
        "thigh_l",
        "calf_l",
        "upperarm_r",
        "lowerarm_r",
        "thigh_r",
        "calf_r",
    ):
        assert f'TEXT("{bone_name}")' in rig_source
    assert "ARaftSimMannyCrewVisualActor::StaticClass()->GetPathName()" in host_source
    assert "Part == Pfd || Part == PfdRearWebbing" in host_source
    assert "Part == PfdBuckle || Part == Helmet" in host_source
    assert "Part == LeftBoot || Part == RightBoot" in host_source
    assert "Part == PaddleShaft || Part == PaddleBlade" in host_source
    assert "Part == Head ||" not in host_source
    assert "Part == LeftHand || Part == RightHand" not in host_source


def test_full_reach_far_field_breaks_up_grid_and_repeated_tree_silhouettes():
    source_path = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    )
    source = source_path.read_text(encoding="utf-8")
    terrain_coverage_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainCoverage.cpp"
    ).read_text(encoding="utf-8")
    canopy_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkCanopyAssets.cpp"
    ).read_text(encoding="utf-8")
    mesh_authoring_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkMeshAuthoring.cpp"
    ).read_text(encoding="utf-8")

    for component_name in (
        "FarConiferA",
        "FarConiferB",
        "FarConiferC",
        "FarBroadleafCard",
    ):
        assert f'TEXT("{component_name}")' in source
    assert 'TEXT("FarConiferCard")' not in source
    assert 'TEXT("FarBroadleafReviewed")' not in source
    assert "TreeSmall02_1K" not in source
    assert "PineTree01_1K" in source
    for component_name in (
        "NearBankConiferA",
        "NearBankConiferB",
        "NearBankConiferC",
    ):
        assert f'TEXT("{component_name}")' in source
    assert "FarCellWidthM" in source
    assert "FarCellHeightM" in source
    assert "JitteredWorldY" in source
    assert "GradientX * JitterX + GradientY * JitterY" in source
    assert "-0.46 * FarCellWidthM" in source
    assert "0.46 * FarCellHeightM" in source
    assert "VariantSelection < 0.44f" in source
    assert "VariantSelection < 0.74f" in source
    assert "MinimumScale = 0.58f" in source
    assert "MaximumScale = 1.34f" in source
    assert "CrownProfileScale" in source
    assert "PatchOrdinal + 127" in source
    assert "InstanceScale" in source
    assert "FoliageCandidate < 2" in source
    assert "ClusteredProbability * 0.5f" in source
    assert "DetailedFoliagePatchNoise" in source
    assert "FarFoliagePatchNoise" in source
    assert "NaturalizedLocation" in source
    assert "DetailedPineAnalogRiverDistanceM = 1100.0f" in source
    assert "TreeRiverDistanceM <= DetailedPineAnalogRiverDistanceM" in source
    assert "RiverDistanceImage.Values[Index] * 0.1f" in source
    assert 'TEXT("river_distance_to_route")' in source
    assert "World->FlushLevelStreaming(EFlushLevelStreamingType::Full);" in source
    assert "Texture->SetForceMipLevelsToBeResident(120.0f);" in mesh_authoring_source
    assert "Texture->WaitForStreaming();" in mesh_authoring_source
    assert source.count("DetailedPineMeshes[0], nullptr, 300000, 520000") == 1
    assert source.count("DetailedPineMeshes[1], nullptr, 300000, 520000") == 1
    assert source.count("DetailedPineMeshes[2], nullptr, 300000, 520000") == 1
    assert "FarFieldDetailedPineInstanceCount" in source
    assert "FarFieldPineCardInstanceCount" in source
    assert "Component->bEnableDensityScaling = bEnableDensityScaling;" in source
    assert "Component->SetCastShadow(bCastShadow);" in source
    assert source.count("/*bEnableDensityScaling=*/true") >= 8
    assert source.count("/*bCastShadow=*/false") >= 5
    assert "nullptr, 360000, 600000, ECollisionEnabled::NoCollision" in source
    assert "nullptr, 320000, 540000, ECollisionEnabled::NoCollision" in source
    assert "bUseCorridorEdgeBlend ? 0.44f : 0.92f" in terrain_coverage_source
    assert "bUseCorridorEdgeBlend ? 0.52f : 0.50f" in terrain_coverage_source
    assert 'TEXT("SourceMacroTone")' in terrain_coverage_source
    assert "FLinearColor(0.62f, 0.68f, 0.60f, 1.0f)" in terrain_coverage_source
    assert "Material->OpacityMaskClipValue = 0.20f" in canopy_source
    assert "MSM_TwoSidedFoliage" in canopy_source
    assert "EditorOnlyData->SubsurfaceColor" in canopy_source
    assert "EditorOnlyData->EmissiveColor" not in canopy_source
    assert "FLinearColor(0.82f, 0.86f, 0.74f, 1.0f)" in canopy_source
    assert "FLinearColor(0.80f, 0.86f, 0.72f, 1.0f)" in canopy_source
    assert "FLinearColor(0.70f, 0.78f, 0.62f, 1.0f)" in canopy_source
    assert "FLinearColor(0.050f, 0.085f, 0.025f, 1.0f)" in canopy_source
    assert "FLinearColor(0.070f, 0.115f, 0.035f, 1.0f)" in canopy_source
    assert "FLinearColor(0.060f, 0.100f, 0.030f, 1.0f)" in canopy_source
    assert "UMaterialExpressionPerInstanceRandom" in canopy_source
    assert "EnergyMinimum->R = 0.88f" in canopy_source
    assert "EnergyMaximum->R = 1.14f" in canopy_source
    assert "OpacityMinimum->R = 0.92f" in canopy_source
    assert "OpacityMaximum->R = 1.10f" in canopy_source
    assert "VariedOpacity->A.OutputIndex = 4" in canopy_source
    assert "constexpr int32 PlaneCount = 2;" in canopy_source
    assert "90.0f * static_cast<float>(PlaneIndex)" in canopy_source
    assert "T_PonderosaPine_Mature_PhotorealV2.png" in canopy_source
    assert "T_PonderosaPine_Intermediate_PhotorealV2.png" in canopy_source
    assert "T_PonderosaPine_Young_PhotorealV2.png" in canopy_source
    assert "T_InteriorLiveOak_BranchAtlasV1.png" in canopy_source
    assert "T_InteriorLiveOak_BranchAtlasV1_Normal.png" in canopy_source
    assert "T_InteriorLiveOak_BranchAtlasV1_AORoughnessSubsurface.png" in canopy_source
    for atlas_name in (
        "T_PonderosaPine_BranchAtlasV1",
        "T_WhiteAlder_BranchAtlasV1",
        "T_Deerbrush_BranchAtlasV1",
    ):
        assert f"{atlas_name}.png" in canopy_source
        assert f"{atlas_name}_Normal.png" in canopy_source
        assert f"{atlas_name}_AORoughnessSubsurface.png" in canopy_source
    assert "CreateSouthForkConnectedCrownMesh" in canopy_source
    assert "CreateSouthForkLiveOakConnectedCrownMesh" not in canopy_source
    assert 'TEXT("ConnectedCrownV2")' in canopy_source
    assert 'TEXT("ConnectedCrownV1")' in canopy_source
    assert '"SM_RaftSim_%s_%s"' in canopy_source
    for species_name in (
        "SouthForkPonderosaMature",
        "SouthForkPonderosaIntermediate",
        "SouthForkPonderosaYounger",
        "SouthForkInteriorLiveOak",
        "SouthForkWhiteAlder",
        "SouthForkDeerbrush",
    ):
        assert species_name in canopy_source
    assert canopy_source.count("ESouthForkConnectedCrownForm::Ponderosa,") == 3
    assert canopy_source.count("ESouthForkConnectedCrownForm::BroadTree,") == 3
    assert canopy_source.count("ESouthForkConnectedCrownForm::Shrub,") == 1
    assert "constexpr int32 StandardBranchCardCount = 12;" in canopy_source
    assert "constexpr int32 VolumetricBroadBranchCardCount = 36;" in canopy_source
    assert "const int32 CorePlaneCount = bVolumetricBroadCrown ? 1 : 2;" in canopy_source
    assert '"crown_version=%s core_planes=%d core_triangles=%d "' in canopy_source
    assert '"branch_cards=%d branch_triangles=%d "' in canopy_source
    assert "generated_canopy_branch_albedo_opacity" in canopy_source
    assert "generated_canopy_branch_normal" in canopy_source
    assert "generated_canopy_branch_ao_roughness_subsurface" in canopy_source
    assert '"M_RaftSim_%s_BranchAtlasV1"' in canopy_source
    assert "PonderosaBranchMaterial" in canopy_source
    assert "OakBranchMaterial" in canopy_source
    assert "AlderBranchMaterial" in canopy_source
    assert "DeerbrushBranchMaterial" in canopy_source
    assert "BranchAORoughnessSubsurface" in canopy_source
    assert "cell-bounded nearest-opaque RGB propagation" not in canopy_source
    assert "PonderosaMaterialA" in canopy_source
    assert "PonderosaMaterialB" in canopy_source
    assert "PonderosaMaterialC" in canopy_source
    assert (
        "connected-crown candidates for all six South Fork canopy profiles, "
        "including thirty-six-spray V2 broadleaf volumes"
        in canopy_source
    )
    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("AerialCanopyGroundCorrection")' not in material_source
    assert 'TEXT("SourceMacroContrast")' not in material_source
    assert 'TEXT("GeologicOutcropStrength")' not in material_source
    assert (
        "SourceConditionedBase->B.Expression = ResolvedSourceMacro" in material_source
    )
    assert "ResolvedMacroInfluence->A.Expression = MacroInfluence" in material_source
    assert (
        "ResolvedMacroInfluence->B.Expression = FullMacroInfluence" in material_source
    )
    assert (
        "ResolvedMacroInfluence->Alpha.Expression = ResolvedEdgeMask" in material_source
    )
    assert (
        "SourceConditionedBase->Alpha.Expression = ResolvedMacroInfluence"
        in material_source
    )
    assert 'TerrainTone->ParameterName = TEXT("SourceMacroTone")' in material_source
    assert (
        'FarFieldTerrainTone->ParameterName = TEXT("FarFieldSourceMacroTone")'
        in material_source
    )
    assert "ResolvedTerrainTone->Alpha.Expression = ResolvedEdgeMask" in material_source
    assert "TonedBase->B.Expression = ResolvedTerrainTone" in material_source
    assert "FLinearColor(0.72f, 0.78f, 0.70f, 1.0f)" in material_source
    assert "RockBreakup->Levels = 4" not in material_source
    assert "RedMinusGreen->A.Expression = MacroRed" in material_source
    assert "RedMinusGreen->B.Expression = InvertedMacroGreen" in material_source
    assert "GeologicSignalGain->ConstB = 4.0f" in material_source
    assert "GeologicSignalBias->ConstB = 0.55f" in material_source
    assert "ScaledSourceGeologicSignal->ConstB = 0.72f" in material_source
    assert "RockBreakup->ConstB = 0.28f" in material_source
    for switch_name in (
        "UseTerrainMicroAlbedo",
        "UseTerrainMicroNormal",
        "UseTerrainMicroRoughness",
    ):
        assert f'TEXT("{switch_name}")' in material_source
        assert f'FMaterialParameterInfo(TEXT("{switch_name}"))' in (
            terrain_coverage_source
        )
    assert "FLinearColor(0.42f, 0.28f, 0.14f, 1.0f)" in material_source
    assert "UseTerrainMicroAlbedo->B.Expression = FarFieldDryGroundColor" in (
        material_source
    )
    assert "UseTerrainMicroNormal->B.Expression = VN" in material_source
    assert "FarFieldRoughness->R = 0.82f" in material_source
    assert "UseTerrainMicroRoughness->A.Expression = WetAwareRoughness" in (
        material_source
    )
    assert (
        terrain_coverage_source.count(
            "Instance->SetStaticSwitchParameterValueEditorOnly("
        )
        >= 3
    )
    assert 'TEXT("RaftSim.CreatePhotorealTerrainMaterial")' in material_source


def test_project_owned_equipment_textiles_are_imported_and_material_bound():
    material_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    m5_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimM5ProductionQualityTest.cpp"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (
            REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/GeneratedTextiles/"
            "generated_textile_pbr_manifest.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["schema"] == "raftsim.equipment.generated_textile_pbr.v1"
    assert manifest["status"].endswith("render_reviewed_not_photoreal")
    assert manifest["render_review"].endswith(
        "m9_equipment_textile_fallback_v280_review.json"
    )
    assert len(manifest["assets"]) == 3
    for textile_name in ("RaftCoatedFabric", "PfdRipstop", "WetsuitNeoprene"):
        assert textile_name in material_source
        assert textile_name in m5_source
        for map_key in ("Albedo", "Normal", "AORoughnessHeight"):
            source_path = (
                REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/GeneratedTextiles/"
                f"T_RaftSim_{textile_name}_{map_key}.png"
            )
            assert source_path.is_file()
            assert map_key in material_source
    assert "BuildEquipmentTextileTextureAssets();" in material_source
    assert 'ParameterName = TEXT("TextileAlbedo")' in material_source
    assert 'ParameterName = TEXT("TextileNormal")' in material_source
    assert 'ParameterName = TEXT("TextileAORoughnessHeight")' in material_source
    assert "EditorData->Normal.Connect(0, BlendedNormal)" in material_source
    assert "EditorData->AmbientOcclusion.Connect(0, AoMask)" in material_source
    assert "TC_Masks" in m5_source
    assert "TA_Wrap" in m5_source


def test_full_reach_far_field_adds_bounded_inferred_geomorphology():
    full_reach_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkFullReach.cpp"
    ).read_text(encoding="utf-8")
    relief_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainRelief.cpp"
    ).read_text(encoding="utf-8")
    coverage_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkTerrainCoverage.cpp"
    ).read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBuildManifest.cpp"
    ).read_text(encoding="utf-8")
    assert "InferredFarFieldReliefMinimumAmplitudeM = 0.12f" in relief_source
    assert "InferredFarFieldReliefMaximumAmplitudeM = 4.80f" in relief_source
    assert "InferredFarFieldReliefBroadWavelengthM = 180.0f" in relief_source
    assert "InferredFarFieldReliefDetailWavelengthM = 58.0f" in relief_source
    assert "InferredFarFieldReliefRidgeWavelengthM = 96.0f" in relief_source
    assert "InferredFarFieldReliefDomainWarpWavelengthM = 420.0f" in relief_source
    assert "InferredFarFieldReliefMaximumDomainWarpM = 32.0f" in relief_source
    assert "RidgeAndDrainageRelief" in relief_source
    assert "SampleStableValueNoise2D" in relief_source
    assert "ComputeSouthForkInferredFarFieldReliefM" in relief_source
    assert "SourceElevationsM.SetNumUninitialized" in full_reach_source
    # Geometry, ground dressing, and foliage all sample the same bounded
    # inferred residual so visible instances remain seated on procedural infill.
    assert full_reach_source.count("ComputeSouthForkInferredFarFieldReliefM(") == 3
    assert "BuildSouthForkInferredFarFieldReliefManifest()" in manifest_source
    assert "ComputeSouthForkFarFieldCorridorReliefWeight(" in full_reach_source
    assert "MaskImage, Row, Column" in full_reach_source
    assert "SouthForkFarFieldCorridorReliefTransitionCells = 3" in coverage_source
    assert "Radius - 1" in coverage_source
    assert "CorridorExclusionMask.Pixels" in coverage_source
    assert "Colors[Index].A = 0.0f" in full_reach_source
    assert "ConfigureSouthForkFarFieldTerrainActor(PlaceSouthForkStaticMeshActor(" in (
        full_reach_source
    )
    assert "Actor->GetStaticMeshComponent()->SetCastShadow(false)" in coverage_source
    assert (
        "world_space_slope_conditioned_domain_warped_ridged_fractal_v2" in relief_source
    )
    assert "DetailedTerrainHalfWidthM = 112.0f" in full_reach_source
    assert "FarFieldRiverExclusionM = 106.0f" in full_reach_source
    assert "GroundRiverDistanceM" in full_reach_source
    assert full_reach_source.count("RiverDistanceImage.Values[Index] * 0.1f") >= 2
    assert 'TEXT("affects_gameplay_collision"), false' in relief_source
    assert 'TEXT("affects_hydraulics"), false' in relief_source
    texture_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorMaterialTextures.cpp"
    ).read_text(encoding="utf-8")
    assert 'Spec.RiverId == TEXT("south_fork_full_reach")' in texture_source
    assert 'Spec.MapKey == TEXT("MacroAlbedo")' in texture_source
    assert "bSouthForkTerrainMacroTexture ? TMGS_Sharpen4" in texture_source
    assert "bMaskedCanopyTexture || bSouthForkTerrainMacroTexture" in texture_source


def test_reviewed_rock_baked_scale_preview_isolated_from_production_assets():
    source = (
        REPO_ROOT / "unreal/Scripts/import_reviewed_rock_baked_scale_preview.py"
    ).read_text(encoding="utf-8")

    assert (
        'DESTINATION = "/Game/RaftSim/Experiments/RockMossSet01_BakedScale"' in source
    )
    assert "import_uniform_scale = 100.0" in source
    assert "build_settings.build_scale3d = unreal.Vector(1.0, 1.0, 1.0)" in source
    assert "nanite_settings.enabled = False" in source
    assert "production_promoted" in source
    assert '"scale_conversion_baked_into_reported_bounds": False' in source
    assert '"runtime_diagnostic_normalizes_from_mesh_bounds": True' in source
    assert "disconnect_material_property" in source
    assert "replace_existing = True" in source
    assert 'name = "M_RockMossSet01_PhysicalPreview"' in source
    assert "albedo_scale.r = 0.55" in source
    assert "MP_EMISSIVE_COLOR" not in source
    assert "T_RockMossSet01_BaseColor_PhysicalPreview" in source
    assert "T_RockMossSet01_NormalGL_PhysicalPreview" in source
    assert "T_RockMossSet01_Roughness_PhysicalPreview" in source
    assert 'texture.set_editor_property("srgb", "_diff_" in relative_path)' in source
    assert "save_loaded_asset" in source


def test_reviewed_rock_preview_audit_is_asset_read_only_and_records_uv_material_state():
    source = (REPO_ROOT / "unreal/Scripts/audit_reviewed_rock_preview.py").read_text(
        encoding="utf-8"
    )

    assert '"read_only": True' in source
    assert '"asset_mutation": False' in source
    assert "get_static_mesh_description(0)" in source
    assert "get_vertex_instance_uv" in source
    assert "get_material_property_input_node" in source
    assert "get_material_used_textures" in source
    assert "TextureExporterPNG" in source
    assert "save_loaded_asset" not in source
    assert "set_editor_property" not in source
