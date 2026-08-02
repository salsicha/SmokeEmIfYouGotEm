from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp"
)
HOST_HEADER = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h"
)
MATERIAL_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPhotorealMaterials.cpp"
)
HELMET_BUILD_SCRIPT = REPO_ROOT / "unreal/Scripts/build_production_whitewater_helmet.py"
HELMET_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/import_production_whitewater_helmet.py"
)
HELMET_MANIFEST_PATH = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet/"
    "production_whitewater_helmet_manifest.json"
)
HELMET_ASSET_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterHelmet.uasset"
)
PFD_BUILD_SCRIPT = REPO_ROOT / "unreal/Scripts/build_production_whitewater_pfd.py"
PFD_IMPORT_SCRIPT = REPO_ROOT / "unreal/Scripts/import_production_whitewater_pfd.py"
PFD_MANIFEST_PATH = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/"
    "production_whitewater_pfd_manifest.json"
)
PFD_ASSET_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Equipment/Production/"
    "SM_RaftSim_WhitewaterRescuePfd.uasset"
)
ROSTER_CAPTURE_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
)
SPLASH_JACKET_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/create_splash_jacket_material.py"
)
REFRESH_UTILITY = REPO_ROOT / "scripts/refresh_pfd_material_parameters.py"
REVIEW_PATH = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_safety_gear_fallback_v306_review.json"
)
CLOTH_WET_REVIEW_PATH = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_cloth_wet_pfd_v1_review.json"
)
INTEGRATED_CARRIER_REVIEW_PATH = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_integrated_soft_carrier_pfd_v3_review.json"
)


def test_safety_gear_geometry_and_material_contracts_are_source_locked() -> None:
    host = HOST_SOURCE.read_text(encoding="utf-8")
    host_header = HOST_HEADER.read_text(encoding="utf-8")
    material = MATERIAL_SOURCE.read_text(encoding="utf-8")
    refresh = REFRESH_UTILITY.read_text(encoding="utf-8")

    assert "AppendTaperedSafetyPanelInstance" in host
    assert "HasVertices(Pfd, 800)" in host
    assert "HasVertices(PfdRearWebbing, 1000)" in host
    assert "HasVertices(PfdBelt, 400)" in host
    assert "HasVertices(PfdBuckle, 300)" in host
    assert "HasVertices(Helmet, 250)" in host
    assert "HasVertices(HelmetRim, 400)" in host
    assert "HasVertices(HelmetRetention, 800)" in host
    assert "bGuide" in host
    assert "M_RaftSim_GuideHelmet" in host
    assert "M_RaftSim_Helmet" in host
    assert "M_RaftSim_Helmet_Red" in host
    assert "M_RaftSim_Helmet_Yellow" in host
    assert "M_RaftSim_Helmet_White" in host
    assert "constexpr int32 Rings = 20" in host
    assert "constexpr int32 Sides = 32" in host
    assert "HasProductionWhitewaterHelmet" in host
    assert "SM_RaftSim_WhitewaterHelmet" in host
    assert "HasProductionWhitewaterPfd" in host
    assert "HasLivePfdMaterialResponse" in host
    assert "HasLivePfdMaterialResponse" in host_header
    assert "GetPfdPresentationWetness" in host_header
    assert "PfdShellMaterialInstance" in host
    assert "OwningRaft->GetSurfaceWetness() * 0.46f" in host
    assert "PfdPresentationWetness, 0.84f" in host
    assert "HasLiveSplashJacketMaterialResponse" in host
    assert "HasLiveSplashJacketMaterialResponse" in host_header
    assert "SplashJacketMaterialInstance" in host
    assert "GetProductionPfdTorsoErrorCm" in host
    assert "SM_RaftSim_WhitewaterRescuePfd" in host
    assert "bReplacedPfdLayer" in host
    assert "UStaticMeshComponent" in host

    assert "static void BuildPfdMaterials()" in material
    assert "static void BuildHelmetMaterials()" in material
    assert "static UMaterial* BuildSplashJacketMaterial()" in material
    assert "BuildPfdShellMaterial(" in material
    assert 'TEXT("M_RaftSim_PFD_Yellow")' in material
    assert 'TEXT("PfdRipstop")' in material
    assert "/*Roughness=*/0.68f" in material
    assert "/*RoughnessVariation=*/0.10f" in material
    assert "/*TextureTiling=*/1.15f" in material
    assert "/*TextileNormalStrength=*/0.22f" in material
    assert "/*bUseClothShading=*/true" in material
    assert "/*SaturatedRoughnessScale=*/0.52f" in material
    assert "/*SaturatedRoughnessMax=*/0.40f" in material
    assert "/*DrySpecularValue=*/0.24f" in material
    assert "/*WetSpecularValue=*/0.42f" in material
    assert "WetCloth->R = 0.16f" in material
    assert "Material->SetShadingModel(bUseClothShading ? MSM_Cloth" in material
    assert "EditorData->SubsurfaceColor.Connect(0, FuzzColor)" in material
    assert "EditorData->ClearCoat.Connect(0, RuntimeCloth)" in material
    assert 'TEXT("M_RaftSim_Helmet")' in material
    assert 'TEXT("M_RaftSim_Helmet_Red")' in material
    assert 'TEXT("M_RaftSim_Helmet_Yellow")' in material
    assert 'TEXT("M_RaftSim_Helmet_White")' in material
    assert "/*bTwoSided=*/true" in material
    assert 'TEXT("RaftSim.CreateProductionHelmetMaterials")' in material
    assert 'TEXT("RaftSim.CreateSplashJacketMaterial")' in material
    assert 'TEXT("M_RaftSim_SplashJacket")' in material
    assert "/*Roughness=*/0.72f" in material
    assert "/*RoughnessVariation=*/0.08f" in material
    assert "/*TextureTiling=*/1.45f" in material
    assert "/*TextileNormalStrength=*/0.20f" in material
    assert "/*SaturatedRoughnessScale=*/0.56f" in material
    assert "/*SaturatedRoughnessMax=*/0.44f" in material
    assert "/*DrySpecularValue=*/0.20f" in material
    assert "/*WetSpecularValue=*/0.38f" in material
    assert "Material->SetMaterialUsage(MATUSAGE_Nanite)" in material
    assert "M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing" in material
    assert "M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft" in material
    assert 'get_editor_property("used_with_nanite")' in (
        REPO_ROOT / "unreal/Scripts/create_production_helmet_materials.py"
    ).read_text(encoding="utf-8")
    assert '"RaftSim.CreateProductionPfdMaterials"' in refresh
    assert "get_material_used_textures(material)" in refresh
    assert 'get_editor_property("two_sided")' in refresh
    assert 'get_editor_property("used_with_nanite")' in refresh
    assert "EXPECTED_TEXTURE_NAMES" in refresh
    assert "does not use the complete PFD ripstop set" in refresh
    assert "unreal.MaterialShadingModel.MSM_CLOTH" in refresh
    assert "unreal.MaterialShadingModel.MSM_CLOTH" in (
        REPO_ROOT / "unreal/Scripts/create_production_pfd_materials.py"
    ).read_text(encoding="utf-8")
    splash_jacket_build = SPLASH_JACKET_BUILD_SCRIPT.read_text(encoding="utf-8")
    assert '"RaftSim.CreateSplashJacketMaterial"' in splash_jacket_build
    assert "EXPECTED_TEXTURE_NAMES" in splash_jacket_build
    assert "get_material_used_textures(material)" in splash_jacket_build
    assert "unreal.MaterialShadingModel.MSM_CLOTH" in splash_jacket_build
    assert "T_RaftSim_PfdRipstop_Albedo" in splash_jacket_build
    assert "T_RaftSim_PfdRipstop_Normal" in splash_jacket_build
    assert "T_RaftSim_PfdRipstop_AORoughnessHeight" in splash_jacket_build


def test_project_owned_production_helmet_source_and_import_are_hash_locked() -> None:
    build_script = HELMET_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_script = HELMET_IMPORT_SCRIPT.read_text(encoding="utf-8")
    manifest = json.loads(HELMET_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "cut_vents" in build_script
    assert "LowerEdgeGasket" in build_script
    assert "RetentionWebbing" in build_script
    assert (
        'EXPECTED_SLOTS = ["HelmetShell", "HelmetLiner", "HelmetWebbing", "HelmetHardware"]'
        in import_script
    )
    assert "DirectoriesToAlwaysCook" not in import_script
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["physical_cut_through_vents"] == 6
    assert manifest["retention_anchor_count"] == 4
    assert 8_000 <= manifest["polygon_count"] <= 20_000
    assert 8_000 <= manifest["vertex_count"] <= 20_000
    fbx = REPO_ROOT / manifest["fbx"]
    blend = REPO_ROOT / manifest["blend"]
    assert hashlib.sha256(fbx.read_bytes()).hexdigest() == manifest["fbx_sha256"]
    assert hashlib.sha256(blend.read_bytes()).hexdigest() == manifest["blend_sha256"]
    assert HELMET_ASSET_PATH.is_file()
    roster_capture = ROSTER_CAPTURE_SCRIPT.read_text(encoding="utf-8")
    assert "actor.has_production_whitewater_helmet()" in roster_capture
    assert '"runtime_production_whitewater_helmet"' in roster_capture


def test_project_owned_production_pfd_source_and_import_are_hash_locked() -> None:
    build_script = PFD_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_script = PFD_IMPORT_SCRIPT.read_text(encoding="utf-8")
    manifest = json.loads(PFD_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "front_foam_panels" in build_script
    assert "quick_release_rescue_belts" in build_script
    assert "rescue_tether_rings" in build_script
    assert "ShoulderFoamBand" not in build_script
    assert "add_swept_shoulder_bridge" not in build_script
    assert "add_crowned_foam_panel" in build_script
    assert "rounded_outline" in build_script
    assert '"PfdShell"' in build_script
    assert "EXPECTED_SLOTS = [" in import_script
    assert '"PfdReflective"' in import_script
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["construction"]["front_carrier_panels"] == 2
    assert manifest["construction"]["back_carrier_panels"] == 1
    assert manifest["construction"]["front_foam_panels"] == 4
    assert manifest["construction"]["shoulder_foam_pads"] == 0
    assert manifest["construction"]["shoulder_webbing_runs"] == 2
    assert manifest["construction"]["adjustment_points"] == 8
    assert manifest["construction"]["front_backup_webbing_runs"] == 4
    assert manifest["construction"]["quick_release_rescue_belts"] == 1
    assert manifest["construction"]["rescue_tether_rings"] == 1
    assert manifest["soft_geometry"] == {
        "outline_corner_rounding": "four-pass closed Chaikin",
        "outline_corner_rounding_passes": 4,
        "flat_exterior_foam_faces": 0,
        "carrier_shell_thickness_cm": 0.9,
        "front_panel_foam_thickness_cm": 4.2,
        "front_panel_edge_roll_cm": 1.0,
        "front_panel_crown_depth_cm": 1.25,
        "front_panel_lateral_wrap_depth_cm": 2.4,
        "back_panel_foam_thickness_cm": 3.2,
        "back_panel_edge_roll_cm": 0.92,
        "back_panel_crown_depth_cm": 1.6,
        "back_panel_lateral_wrap_depth_cm": 3.8,
        "rigid_side_foam_wings": 0,
        "side_webbing_connector_thickness_cm": 0.36,
        "front_pocket_flat_exterior_faces": 0,
        "front_pocket_crown_depth_cm": 0.18,
        "rescue_belt_profile": "flat torso-following webbing",
        "rescue_belt_thickness_cm": 0.36,
        "duplicate_tubular_side_adjustment_runs": 0,
        "smooth_shaded": True,
    }
    assert manifest["construction"]["back_panels"] == 2
    assert manifest["construction"]["rear_flex_channels"] == 1
    assert manifest["material_slots"] == [
        "PfdShell",
        "PfdWebbing",
        "PfdHardware",
        "PfdReflective",
        "PfdLabel",
    ]
    assert 10_000 <= manifest["vertex_count"] <= 25_000
    assert 10_000 <= manifest["polygon_count"] <= 25_000
    fbx = REPO_ROOT / manifest["fbx"]
    blend = REPO_ROOT / manifest["blend"]
    assert hashlib.sha256(fbx.read_bytes()).hexdigest() == manifest["fbx_sha256"]
    assert hashlib.sha256(blend.read_bytes()).hexdigest() == manifest["blend_sha256"]
    assert PFD_ASSET_PATH.is_file()
    roster_capture = ROSTER_CAPTURE_SCRIPT.read_text(encoding="utf-8")
    assert "actor.has_production_whitewater_pfd()" in roster_capture
    assert "actor.has_live_pfd_material_response()" in roster_capture
    assert "actor.get_pfd_presentation_wetness()" in roster_capture
    assert "unreal.RaftSimCrewAvatarAction.SWIMMING" in roster_capture
    assert "unreal.RaftSimCrewAvatarAction.SEATED_IDLE" in roster_capture
    assert 'f"{stem}_pfd_dry"' in roster_capture
    assert 'f"{stem}_pfd_wet"' in roster_capture
    assert "actor.get_production_pfd_torso_error_cm() > 1.0" in roster_capture
    assert '"runtime_production_whitewater_pfd"' in roster_capture
    assert '"runtime_pfd_torso_error_cm"' in roster_capture


def test_safety_gear_renderer_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    capture = REPO_ROOT / review["renderer_evidence"]["capture"]

    assert review["status"] == "technical_upgrade_accepted_photoreal_art_rejected"
    assert review["renderer_evidence"]["result"] == "Success"
    assert review["renderer_evidence"]["human_approved"] is False
    assert review["automation_evidence"]["passed"] == 4
    assert review["automation_evidence"]["failed"] == 0
    assert review["named_art_reviewer"] is None
    assert capture.is_file()
    assert (
        hashlib.sha256(capture.read_bytes()).hexdigest()
        == review["renderer_evidence"]["capture_sha256"]
    )


def test_cloth_wet_pfd_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(CLOTH_WET_REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["shading_model"] == "MSM_Cloth"
    assert review["implementation"]["physics_authority_changed"] is False
    assert review["runtime_roster_metrics"]["captured_character_count"] == 5
    assert (
        review["runtime_roster_metrics"]["characters_with_live_material_response"] == 5
    )
    assert review["validation"]["m5_results"]["failed"] == 0
    for evidence in review["renderer_evidence"].values():
        if not isinstance(evidence, dict) or "capture" not in evidence:
            continue
        capture = REPO_ROOT / evidence["capture"]
        assert capture.is_file()
        assert (
            hashlib.sha256(capture.read_bytes()).hexdigest()
            == evidence["capture_sha256"]
        )
    for asset in review["runtime_assets"]:
        path = REPO_ROOT / asset["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]


def test_integrated_soft_carrier_pfd_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(INTEGRATED_CARRIER_REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["construction"]["side_wings"] == 0
    assert review["construction"]["side_webbing_connectors"] == 6
    assert review["construction"]["shoulder_foam_pads"] == 0
    assert review["soft_geometry"]["duplicate_tubular_side_adjustment_runs"] == 0
    assert review["runtime_roster_metrics"]["captured_character_count"] == 5
    assert review["runtime_roster_metrics"]["characters_using_production_pfd"] == 5
    assert review["runtime_roster_metrics"]["maximum_runtime_torso_error_cm"] == 0.0
    assert review["reviewers"]["named_character_art_reviewer"] is None
    assert review["reviewers"]["qualified_whitewater_safety_reviewer"] is None
    assert review["reviewers"]["human_approved"] is False

    hash_locked_paths = [
        (review["source"]["generator"], review["source"]["generator_sha256"]),
        (review["source"]["importer"], review["source"]["importer_sha256"]),
        (review["source"]["manifest"], review["source"]["manifest_sha256"]),
        (review["source"]["fbx"], review["source"]["fbx_sha256"]),
        (review["source"]["blend"], review["source"]["blend_sha256"]),
        (review["runtime_asset"]["uasset"], review["runtime_asset"]["uasset_sha256"]),
        (
            review["runtime_asset"]["import_report"],
            review["runtime_asset"]["import_report_sha256"],
        ),
        (
            review["runtime_roster_metrics"]["source_report"],
            review["runtime_roster_metrics"]["source_report_sha256"],
        ),
        (review["validation"]["m5_report"], review["validation"]["m5_report_sha256"]),
    ]
    for relative_path, expected_hash in hash_locked_paths:
        path = REPO_ROOT / relative_path
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash

    for evidence in review["renderer_evidence"].values():
        if not isinstance(evidence, dict) or "capture" not in evidence:
            continue
        capture = REPO_ROOT / evidence["capture"]
        assert capture.is_file()
        assert (
            hashlib.sha256(capture.read_bytes()).hexdigest()
            == evidence["capture_sha256"]
        )

    m5 = json.loads(
        (REPO_ROOT / review["validation"]["m5_report"]).read_text(encoding="utf-8-sig")
    )
    assert m5["succeeded"] == 1
    assert m5["failed"] == 0
