from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp"
)
MATERIAL_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPhotorealMaterials.cpp"
)
HELMET_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/build_production_whitewater_helmet.py"
)
HELMET_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/import_production_whitewater_helmet.py"
)
HELMET_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet/"
    "production_whitewater_helmet_manifest.json"
)
HELMET_ASSET_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterHelmet.uasset"
)
PFD_BUILD_SCRIPT = REPO_ROOT / "unreal/Scripts/build_production_whitewater_pfd.py"
PFD_IMPORT_SCRIPT = REPO_ROOT / "unreal/Scripts/import_production_whitewater_pfd.py"
PFD_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/"
    "production_whitewater_pfd_manifest.json"
)
PFD_ASSET_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Equipment/Production/"
    "SM_RaftSim_WhitewaterRescuePfd.uasset"
)
ROSTER_CAPTURE_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
)
REFRESH_UTILITY = REPO_ROOT / "scripts/refresh_pfd_material_parameters.py"
REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_safety_gear_fallback_v306_review.json"
)


def test_safety_gear_geometry_and_material_contracts_are_source_locked() -> None:
    host = HOST_SOURCE.read_text(encoding="utf-8")
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
    assert "GetProductionPfdTorsoErrorCm" in host
    assert "SM_RaftSim_WhitewaterRescuePfd" in host
    assert "bReplacedPfdLayer" in host
    assert "UStaticMeshComponent" in host

    assert "static void BuildPfdMaterials()" in material
    assert "static void BuildHelmetMaterials()" in material
    assert 'BuildTexturedRaftMaterial(TEXT("M_RaftSim_PFD_Yellow")' in material
    assert 'TEXT("PfdRipstop")' in material
    assert "0.74f, 0.07f, 1.5f, 0.16f" in material
    assert 'TEXT("M_RaftSim_Helmet")' in material
    assert 'TEXT("M_RaftSim_Helmet_Red")' in material
    assert 'TEXT("M_RaftSim_Helmet_Yellow")' in material
    assert 'TEXT("M_RaftSim_Helmet_White")' in material
    assert "/*bTwoSided=*/true" in material
    assert 'TEXT("RaftSim.CreateProductionHelmetMaterials")' in material
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


def test_project_owned_production_helmet_source_and_import_are_hash_locked() -> None:
    build_script = HELMET_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_script = HELMET_IMPORT_SCRIPT.read_text(encoding="utf-8")
    manifest = json.loads(HELMET_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "cut_vents" in build_script
    assert "LowerEdgeGasket" in build_script
    assert "RetentionWebbing" in build_script
    assert 'EXPECTED_SLOTS = ["HelmetShell", "HelmetLiner", "HelmetWebbing", "HelmetHardware"]' in import_script
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
    assert '"PfdShell"' in build_script
    assert 'EXPECTED_SLOTS = [' in import_script
    assert '"PfdReflective"' in import_script
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["construction"]["front_foam_panels"] == 4
    assert manifest["construction"]["adjustment_points"] == 8
    assert manifest["construction"]["front_backup_webbing_runs"] == 2
    assert manifest["construction"]["quick_release_rescue_belts"] == 1
    assert manifest["construction"]["rescue_tether_rings"] == 1
    assert manifest["material_slots"] == [
        "PfdShell",
        "PfdWebbing",
        "PfdHardware",
        "PfdReflective",
        "PfdLabel",
    ]
    assert 10_000 <= manifest["vertex_count"] <= 20_000
    assert 10_000 <= manifest["polygon_count"] <= 20_000
    fbx = REPO_ROOT / manifest["fbx"]
    blend = REPO_ROOT / manifest["blend"]
    assert hashlib.sha256(fbx.read_bytes()).hexdigest() == manifest["fbx_sha256"]
    assert hashlib.sha256(blend.read_bytes()).hexdigest() == manifest["blend_sha256"]
    assert PFD_ASSET_PATH.is_file()
    roster_capture = ROSTER_CAPTURE_SCRIPT.read_text(encoding="utf-8")
    assert "actor.has_production_whitewater_pfd()" in roster_capture
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
