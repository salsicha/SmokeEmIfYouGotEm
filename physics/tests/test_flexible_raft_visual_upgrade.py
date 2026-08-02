import hashlib
import json
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
MESH_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftMesh.cpp"
)
AUTOMATION_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimM5ProductionQualityTest.cpp"
)
ROCK_ACTOR_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimRockObstacleActor.cpp"
)
CAPTURE_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimCaptureCommand.cpp"
)
CAMERA_PRESENTATION_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimCameraPresentation.h"
)
ROCK_MATERIAL_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPhotorealMaterials.cpp"
)
RAFT_MATERIAL_SCRIPT = REPO_ROOT / "unreal/Scripts/create_production_raft_materials.py"
RAFT_ACTOR_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftActor.cpp"
)
RAFT_HEADER_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimRaftActor.h"
)
CREW_AVATAR_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimCrewAvatarActor.cpp"
)
CREW_AVATAR_HEADER = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
    "RaftSimCrewAvatarActor.h"
)
PRODUCTION_RAFT_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/build_production_whitewater_raft.py"
)
PRODUCTION_RAFT_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/import_production_whitewater_raft.py"
)
PRODUCTION_RAFT_MANIFEST = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Rafts/ProductionPaddleRaft/"
    "production_paddle_raft_manifest.json"
)
PRODUCTION_RAFT_ASSET = (
    REPO_ROOT / "unreal/Content/RaftSim/Rafts/Production/"
    "SM_RaftSim_ProductionPaddleRaft.uasset"
)
WATER_VFX_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp"
)
WATER_VFX_HEADER = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterVfxActor.h"
)
DEFAULT_GAME_CONFIG = REPO_ROOT / "unreal/Config/DefaultGame.ini"
DEFAULT_SCALABILITY_CONFIG = REPO_ROOT / "unreal/Config/DefaultScalability.ini"
CONTENT_LOCK_DIRECTOR_SOURCE = (
    REPO_ROOT / "unreal/Source/SmokeEmIfYouGotEm/RaftSimContentLockDirector.cpp"
)
NIAGARA_WATER_VFX_EDITOR_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorNiagaraWaterVfx.cpp"
)
NIAGARA_WATER_VFX_AUTOMATION_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimNiagaraWaterVfxTest.cpp"
)
CONNECTED_WATER_V6_EDITOR_SOURCE = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorConnectedWaterV6Material.cpp"
)
CONNECTED_WATER_V6_AUTHOR_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/create_connected_contact_water_v6_review_material.py"
)
WATER_PARTICLE_ATLAS = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Water/T_RaftSim_WaterParticle_SubUV.png"
)
WATER_PARTICLE_ATLAS_PROVENANCE = WATER_PARTICLE_ATLAS.with_suffix(".provenance.json")
WATER_PARTICLE_ATLAS_GENERATOR = (
    REPO_ROOT / "unreal/Scripts/build_production_water_particle_atlas.py"
)
PHOTOGRAPHIC_WATER_ATLAS_DIR = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Water/PhotographicSubUVV4"
)
PHOTOGRAPHIC_WATER_ATLAS_SOURCE = (
    PHOTOGRAPHIC_WATER_ATLAS_DIR / "T_RaftSim_WhitewaterSubUV_Source_v4.png"
)
PHOTOGRAPHIC_WATER_ATLAS_REVIEW = (
    PHOTOGRAPHIC_WATER_ATLAS_DIR / "T_RaftSim_WaterParticle_SubUV_v4_review.png"
)
PHOTOGRAPHIC_WATER_ATLAS_PROVENANCE = PHOTOGRAPHIC_WATER_ATLAS_REVIEW.with_suffix(
    ".provenance.json"
)
PHOTOGRAPHIC_WATER_ATLAS_GENERATOR = (
    REPO_ROOT / "unreal/Scripts/build_photographic_water_particle_atlas_v4.py"
)
PHOTOGRAPHIC_WATER_ATLAS_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/create_photographic_water_vfx_review.py"
)
PHOTOGRAPHIC_WATER_REVIEW_ASSET_DIR = (
    REPO_ROOT / "unreal/Content/RaftSim/VFX/Water/PhotographicSubUVV4Review"
)
PHOTOGRAPHIC_WATER_REVIEW_EVIDENCE = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_photographic_water_subuv_v4_review.json"
)
PHOTOGRAPHIC_WATER_V5_ATLAS_DIR = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Water/PhotographicSubUVV5"
)
PHOTOGRAPHIC_WATER_V5_SOURCE_PATHS = {
    "spray_foam": PHOTOGRAPHIC_WATER_V5_ATLAS_DIR
    / "T_RaftSim_WhitewaterParticleScale_SprayFoam_Source_v5.png",
    "droplets": PHOTOGRAPHIC_WATER_V5_ATLAS_DIR
    / "T_RaftSim_WhitewaterParticleScale_Droplets_Source_v5.png",
    "aerated_foam": PHOTOGRAPHIC_WATER_V5_ATLAS_DIR
    / "T_RaftSim_WhitewaterParticleScale_AeratedFoam_Source_v5.png",
}
PHOTOGRAPHIC_WATER_V5_ATLAS_REVIEW = (
    PHOTOGRAPHIC_WATER_V5_ATLAS_DIR / "T_RaftSim_WaterParticle_SubUV_v5_review.png"
)
PHOTOGRAPHIC_WATER_V5_MIP_PREVIEW = (
    PHOTOGRAPHIC_WATER_V5_ATLAS_DIR
    / "T_RaftSim_WaterParticle_SubUV_v5_mip32_preview.png"
)
PHOTOGRAPHIC_WATER_V5_ATLAS_PROVENANCE = PHOTOGRAPHIC_WATER_V5_ATLAS_REVIEW.with_suffix(
    ".provenance.json"
)
PHOTOGRAPHIC_WATER_V5_ATLAS_GENERATOR = (
    REPO_ROOT / "unreal/Scripts/build_photographic_water_particle_atlas_v5.py"
)
PHOTOGRAPHIC_WATER_V5_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/create_photographic_water_vfx_v5_review.py"
)
PHOTOGRAPHIC_WATER_V5_REVIEW_ASSET_DIR = (
    REPO_ROOT / "unreal/Content/RaftSim/VFX/Water/PhotographicSubUVV5Review"
)
PHOTOGRAPHIC_WATER_V5_REVIEW_EVIDENCE = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_photographic_water_subuv_v5_review.json"
)
REVIEW_PATH = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_flexible_raft_upgrade_v317_review.json"
)
PRODUCTION_RAFT_REVIEW_PATH = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach/"
    "m9_production_paddle_raft_v12_review.json"
)
PRODUCTION_BOULDER_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/build_production_river_boulder.py"
)
PRODUCTION_BOOT_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/build_production_whitewater_boot.py"
)
PRODUCTION_BOOT_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/import_production_whitewater_boot.py"
)
PRODUCTION_BOOT_MATERIAL_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/create_production_whitewater_boot_materials.py"
)
PRODUCTION_BOOT_MANIFEST = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionRiverBoot/"
    "production_whitewater_river_boot_manifest.json"
)
PRODUCTION_BOOT_ASSET = (
    REPO_ROOT / "unreal/Content/RaftSim/Equipment/Production/"
    "SM_RaftSim_WhitewaterRiverBoot.uasset"
)
PRODUCTION_PFD_BUILD_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/build_production_whitewater_pfd.py"
)
PRODUCTION_PFD_MANIFEST = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/"
    "production_whitewater_pfd_manifest.json"
)
PRODUCTION_PFD_ASSET = (
    REPO_ROOT / "unreal/Content/RaftSim/Equipment/Production/"
    "SM_RaftSim_WhitewaterRescuePfd.uasset"
)
PRODUCTION_BOULDER_IMPORT_SCRIPT = (
    REPO_ROOT / "unreal/Scripts/import_production_river_boulder.py"
)
PRODUCTION_BOULDER_MANIFEST = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Rocks/ProductionRiverBoulder/"
    "production_river_boulder_manifest.json"
)
PRODUCTION_BOULDER_ASSET = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/Rocks/Production/"
    "SM_RaftSim_ProductionRiverBoulder.uasset"
)


def test_flexible_raft_construction_is_surface_projected_and_d4_coupled() -> None:
    source = MESH_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "AppendSideChafeStrip",
        "CircumferentialSegments = 6",
        "AppendSideTubePatch",
        "RadialRings = 3",
        "EvaluatePointDeformation",
        "IBeamRelief",
        "Accumulated face",
    ):
        assert contract in source


def test_project_owned_production_raft_source_and_runtime_boundary_are_locked() -> None:
    build_source = PRODUCTION_RAFT_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_source = PRODUCTION_RAFT_IMPORT_SCRIPT.read_text(encoding="utf-8")
    mesh_source = MESH_SOURCE.read_text(encoding="utf-8")
    automation_source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    actor_source = RAFT_ACTOR_SOURCE.read_text(encoding="utf-8")
    actor_header = RAFT_HEADER_SOURCE.read_text(encoding="utf-8")
    manifest = json.loads(PRODUCTION_RAFT_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["material_slots"] == [
        "RaftTube",
        "RaftFloor",
        "RaftRigging",
        "RaftMetal",
        "RaftRubber",
    ]
    assert manifest["construction"] == {
        "nominal_length_m": 4.3,
        "nominal_width_m": 2.0,
        "nominal_side_tube_diameter_m": 0.544,
        "main_chambers": 4,
        "thwarts": 2,
        "d_rings": 12,
        "carry_handles": 4,
        "tube_valves": 4,
        "floor_pressure_relief_valves": 1,
        "self_bailing_drain_recesses": 8,
    }
    assert all(
        reference["asset_content_copied"] is False
        for reference in manifest["reference_only_sources"]
    )
    assert 18_000 <= manifest["polygon_count"] <= 60_000
    assert 18_000 <= manifest["vertex_count"] <= 60_000
    assert 420.0 <= manifest["dimensions_cm"][0] <= 450.0
    assert 195.0 <= manifest["dimensions_cm"][1] <= 220.0
    for key in ("fbx", "blend"):
        source_asset = REPO_ROOT / manifest[key]
        assert (
            hashlib.sha256(source_asset.read_bytes()).hexdigest()
            == manifest[f"{key}_sha256"]
        )
    assert PRODUCTION_RAFT_ASSET.is_file()

    for contract in (
        "superellipse_path",
        "InflatedSelfBailingFloor",
        "MainChamberSeam_",
        "PerimeterGrabLine",
        "StainlessDRing_",
        "DrainGrommet_",
    ):
        assert contract in build_source
    assert 'mesh.set_editor_property("allow_cpu_access", True)' in import_source
    assert "nanite.enabled = False" in import_source
    assert "ExtractProductionRaftRestMesh" in mesh_source
    assert "DeformProductionRaftRestMesh" in mesh_source
    assert "OffsetGradientX" in mesh_source
    assert "ContactCenterCm" in mesh_source
    assert "1.0f - 0.95f * Shape.CompressionRatio" in mesh_source
    assert "0.75f, 1.0f" in mesh_source
    assert "LightingGradientScale = 0.52f" in mesh_source
    assert "TransformDirection" in mesh_source
    assert "BentSection.Normals" in automation_source
    assert (
        "production raft lighting frame follows the D4 contact field"
        in automation_source
    )
    assert (
        "production wrap projection stays within a 90 cm visual bound"
        in automation_source
    )
    assert "GetFlexibleVisualSegments()" in actor_source
    assert "SM_RaftSim_ProductionPaddleRaft" in actor_source
    assert "bCreateCollision=*/false" in actor_source
    assert "HasProductionWhitewaterRaft" in actor_header


def test_raft_art_review_mode_is_explicitly_evidence_only() -> None:
    source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    assert "RaftSimRaftArtReview" in source
    assert "renderer evidence only and never changes a gameplay path" in source
    assert "M5_RaftConstruction.png" in source
    assert "M5_RescueProduction.png" in source


def test_production_rescue_pfd_uses_integrated_soft_carrier_source_art() -> None:
    build_source = PRODUCTION_PFD_BUILD_SCRIPT.read_text(encoding="utf-8")
    manifest = json.loads(PRODUCTION_PFD_MANIFEST.read_text(encoding="utf-8"))

    assert "GENERATOR_VERSION = 10" in build_source
    assert '"FrontCarrier_' in build_source
    assert '"RearCarrier"' in build_source
    assert '"ProtectiveBackUpperCell"' in build_source
    assert '"ProtectiveBackLumbarCell"' in build_source
    assert "lateral_wrap_depth=3.8" in build_source
    assert "former single\n    # 31.5 x 42 cm plate" in build_source
    assert "ShoulderFoamBand" not in build_source
    assert manifest["generator_version"] == 10
    assert manifest["construction"]["front_carrier_panels"] == 2
    assert manifest["construction"]["back_carrier_panels"] == 1
    assert manifest["construction"]["back_panels"] == 2
    assert manifest["construction"]["rear_flex_channels"] == 1
    assert manifest["soft_geometry"]["flat_exterior_foam_faces"] == 0
    assert manifest["soft_geometry"]["outline_corner_rounding_passes"] == 4
    assert manifest["soft_geometry"]["carrier_shell_thickness_cm"] == 0.9
    assert manifest["soft_geometry"]["front_panel_foam_thickness_cm"] == 4.2
    assert manifest["soft_geometry"]["front_panel_crown_depth_cm"] == 1.25
    assert manifest["soft_geometry"]["front_panel_lateral_wrap_depth_cm"] == 2.4
    assert manifest["soft_geometry"]["back_panel_foam_thickness_cm"] == 3.2
    assert manifest["soft_geometry"]["back_panel_crown_depth_cm"] == 1.6
    assert manifest["soft_geometry"]["back_panel_lateral_wrap_depth_cm"] == 3.8
    assert manifest["construction"]["side_wings"] == 0
    assert manifest["construction"]["side_webbing_connectors"] == 6
    assert manifest["soft_geometry"]["rigid_side_foam_wings"] == 0
    assert manifest["soft_geometry"]["rescue_belt_profile"] == (
        "flat torso-following webbing"
    )
    assert manifest["soft_geometry"]["duplicate_tubular_side_adjustment_runs"] == 0
    assert manifest["soft_geometry"]["front_pocket_flat_exterior_faces"] == 0
    assert manifest["construction"]["shoulder_foam_pads"] == 0
    assert manifest["construction"]["shoulder_webbing_runs"] == 2
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    for key in ("fbx", "blend"):
        source_asset = REPO_ROOT / manifest[key]
        assert (
            hashlib.sha256(source_asset.read_bytes()).hexdigest()
            == manifest[f"{key}_sha256"]
        )
    assert PRODUCTION_PFD_ASSET.is_file()


def test_named_rapid_wrap_evidence_uses_production_runtime_authority() -> None:
    rock_source = ROCK_ACTOR_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "UProceduralMeshComponent",
        'CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"))',
        "RockMesh->SetupAttachment(SceneRoot)",
        "ReviewedRockVisual->SetupAttachment(SceneRoot)",
        "ProductionRockVisual->SetupAttachment(SceneRoot)",
        "UStaticMeshComponent",
        "CreateMeshSection_LinearColor",
        "ECollisionEnabled::NoCollision",
        "M_RaftSim_RiverBoulder",
        "SM_RaftSim_ProductionRiverBoulder",
        "HasProductionRiverBoulder",
        "ContactRadiusM * 100.0f",
        "RockMossSet01_1K",
        "SM_RockMossSet01_rock_moss_set_01_rock03",
        "ReviewedRockVisual->SetVisibility(true, false)",
        "RockMesh->SetMeshSectionVisible(0, false)",
        "RockMesh->SetMeshSectionVisible(0, true)",
        "bPreferReviewedVisual",
        "ReviewedRockVisual->MarkRenderStateDirty()",
        "SetReviewedVisualMeshForDiagnostics",
        "ReviewedRockVisual->EmptyOverrideMaterials()",
        "ReviewedRockVisual->SetCastShadow(false)",
        "ReviewedRockVisual->GetNumMaterials()",
        "ReviewedRockVisual->SetMaterial(MaterialIndex, SharedRockMaterial.Object)",
        "BoulderSegments = 48",
        "BoulderLatitudeDivisions = 18",
        "Normals[VertexIndex] *= -1.0f",
        "Tangents[VertexIndex].bFlipTangentY",
        "VerticalRadiusCm * 0.98f",
        "CrownProfile",
        "FMath::Cos(Phi)), 0.72f",
        "FLinearColor(0.24f, 0.23f, 0.20f, 0.0f)",
    ):
        assert contract in rock_source
    assert "not represented as site-specific geology" in rock_source


def test_production_boulder_source_import_and_runtime_boundary_are_fail_closed() -> (
    None
):
    assert PRODUCTION_BOULDER_BUILD_SCRIPT.is_file()
    assert PRODUCTION_BOULDER_IMPORT_SCRIPT.is_file()
    assert PRODUCTION_BOULDER_MANIFEST.is_file()
    manifest = json.loads(PRODUCTION_BOULDER_MANIFEST.read_text(encoding="utf-8"))
    fbx_path = REPO_ROOT / manifest["fbx"]
    blend_path = REPO_ROOT / manifest["blend"]
    assert hashlib.sha256(fbx_path.read_bytes()).hexdigest() == manifest["fbx_sha256"]
    assert (
        hashlib.sha256(blend_path.read_bytes()).hexdigest() == manifest["blend_sha256"]
    )
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["polygon_count"] == 81_920
    assert manifest["construction"]["closed_watertight_shells"] == 1
    assert manifest["construction"]["physical_fracture_bands"] == 3
    assert manifest["vertex_color_alpha"] == 0.0

    build_source = PRODUCTION_BOULDER_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_source = PRODUCTION_BOULDER_IMPORT_SCRIPT.read_text(encoding="utf-8")
    rock_source = ROCK_ACTOR_SOURCE.read_text(encoding="utf-8")
    assert "fracture_depth" in build_source
    assert "primitive_ico_sphere_add(subdivisions=7" in build_source
    assert "unreal.VertexColorImportOption.REPLACE" in import_source
    assert "nanite.enabled = True" in import_source
    assert "SetCollisionEnabled(ECollisionEnabled::NoCollision)" in rock_source
    assert "TargetHorizontalExtentCm = HorizontalRadiusCm * 0.96f" in rock_source
    assert 'SetScalarParameterValue(TEXT("RockVisualSourceBlend"), 0.0f)' in rock_source
    automation_source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    assert "project-owned production river boulder exists" in automation_source
    assert "production river boulder has a Nanite render resource" in automation_source

    capture_source = CAPTURE_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "M9_MeatGrinderD4Wrap",
        "full_hydraulics/rapids/meat_grinder/cooked",
        ": 960.0f",
        "Rock->ConfigureContact(1.20f, 0.82f)",
        'DiagnosticFloat(TEXT("rockx="), -100.0f)',
        'DiagnosticFloat(TEXT("rocky="), -130.0f)',
        'DiagnosticFloat(TEXT("rockz="), -20.0f)',
        "contactLocalCm=%s",
        "Raft->GetActiveWaterContactCount()",
        "Raft->GetWrappingRockContactCount()",
        "Raft->GetPinnedRockObstacleCount()",
        "Raft->GetRecoveringRockContactCount()",
        "Raft->GetMaximumWaterContactIndentationM()",
        "Raft->GetSurfaceWetness()",
        "rockVisual=%s",
        "materialSlots=%d",
        "Component->IsRenderStateCreated()",
        "Component->ShouldRender()",
        "Component->GetMaterial(MaterialIndex)",
        "ProceduralRock->IsMeshSectionVisible(0)",
        "finalFrame",
        "relativeToRaftCm=%s",
        "0.03f",
        'CameraPreset == TEXT("contact_port")',
        'CameraPreset == TEXT("wrap_hero")',
        'CameraPreset == TEXT("river_action")',
        "FVector(-680.0f, -520.0f, 245.0f)",
        "FVector(260.0f, 0.0f, 55.0f)",
        "CameraOffset = FVector(360.0f, -350.0f, 275.0f)",
        "LookAtOffset = FVector(15.0f, -20.0f, 35.0f)",
        "LookAtOffset = FVector(-80.0f, -130.0f, 60.0f)",
        'HasDiagnosticMode(TEXT("reviewedrock"))',
        'DiagnosticString(TEXT("rockmesh="))',
        "Rock->SetReviewedVisualMeshForDiagnostics",
        "Rock->SetPreferReviewedVisual(bReviewedRockDiagnostic)",
    ):
        assert contract in capture_source
    assert "SetFlexibleVisualSegments" not in capture_source


def test_contact_rock_material_supports_both_reviewed_and_fallback_shells() -> None:
    source = ROCK_MATERIAL_SOURCE.read_text(encoding="utf-8")
    marker = "static UMaterial* BuildRiverBoulderMaterial("
    assert marker in source
    boulder_source = source.split(marker, 1)[1].split("static UMaterial*", 1)[0]
    assert "Material->TwoSided = false" in boulder_source
    assert (
        "Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes)" in boulder_source
    )
    assert "Material->SetMaterialUsage(MATUSAGE_StaticMesh)" in boulder_source
    assert "Material->SetMaterialUsage(MATUSAGE_Nanite)" in boulder_source
    assert "MATUSAGE_ProceduralMesh" not in boulder_source
    assert "T_RockMossSet01_BaseColor_1K" in boulder_source
    assert "ExistingExpression->IsRooted()" in boulder_source
    assert "ExistingExpression->RemoveFromRoot()" in boulder_source
    assert "ExistingExpression->MarkAsGarbage()" in boulder_source
    assert "DesaturatedBase->Fraction.Expression = Constant(0.80f)" in boulder_source
    assert "FLinearColor(0.54f, 0.57f, 0.59f" in boulder_source
    assert 'TEXT("ReviewedRockNormal")' in boulder_source
    assert "EditorData->Normal.Connect(0, RockNormal)" in boulder_source
    assert "VisualSourceVertexColor" in boulder_source
    assert "ProceduralBaseColor, ReviewedTintedBaseColor" in boulder_source
    assert "FLinearColor(0.090f, 0.101f, 0.105f" in boulder_source
    assert "FLinearColor(0.340f, 0.308f, 0.264f" in boulder_source
    assert (
        "It is an appearance analog, not South Fork geology authority" in boulder_source
    )
    assert 'TEXT("RockVisualSourceBlend")' in boulder_source
    assert "VisualSourceBlend->DefaultValue = 1.0f" in boulder_source
    assert "SelectedVisualSource->A.OutputIndex = 4" in boulder_source
    assert "bIncludeReviewedSource && ReviewedBaseColor" in boulder_source
    assert "UMaterialExpressionPerInstanceCustomData" in boulder_source
    assert "PerInstanceWaterlineZ->DataIndex = 0" in boulder_source
    assert "PerInstanceWaterlineZ->ConstDefaultValue = -1.0e7f" in boulder_source
    assert "UMaterialExpressionMax" in boulder_source
    assert "HeightAbove->B.Expression = ResolvedWaterlineZ" in boulder_source
    assert "RaftSim.CreateReviewedRiverBoulderMaterial" in source
    assert 'TEXT("M_RaftSim_ProductionRiverBoulder")' in source
    assert "/*bIncludeReviewedSource=*/false" in source


def test_production_contact_rock_uses_south_fork_world_aligned_dressing() -> None:
    rock_actor_source = ROCK_ACTOR_SOURCE.read_text(encoding="utf-8")
    dressing_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorSouthForkBoulderMaterial.cpp"
    ).read_text(encoding="utf-8")

    assert "MI_RaftSim_SouthForkProductionBoulder" in rock_actor_source
    assert "ProductionRockVisual->SetMaterial" in rock_actor_source
    assert 'TEXT("RockWaterlineZCm")' in dressing_source
    assert 'TEXT("RockWetBandWidthCm")' in dressing_source
    assert "WorldAlignedTexture.WorldAlignedTexture" in dressing_source
    assert "WorldAlignedNormal.WorldAlignedNormal" in dressing_source
    assert "EditorData->BaseColor.Connect(0, WaterlineAlbedo)" in dressing_source
    assert "EditorData->Roughness.Connect(0, WaterlineRoughness)" in dressing_source


def test_runtime_camera_uses_bounded_local_exposure_without_simulation_authority() -> (
    None
):
    source = CAMERA_PRESENTATION_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "float ExposureBias = 1.25f",
        "Settings.AutoExposureMethod = AEM_Manual",
        "Settings.LocalExposureMethod = ELocalExposureMethod::Bilateral",
        "Settings.LocalExposureHighlightContrastScale = 0.78f",
        "Settings.LocalExposureShadowContrastScale = 0.72f",
        "Settings.LocalExposureDetailStrength = 1.0f",
        "Settings.LocalExposureBlurredLuminanceBlend = 0.50f",
        "Settings.LocalExposureBlurredLuminanceKernelSizePercent = 50.0f",
    ):
        assert contract in source
    capture_source = CAPTURE_SOURCE.read_text(encoding="utf-8")
    assert 'DiagnosticFloat(TEXT("exposure="), 1.25f)' in capture_source


def test_production_raft_wet_film_is_focused_and_d4_visual_only() -> None:
    source = ROCK_MATERIAL_SOURCE.read_text(encoding="utf-8")
    assert "static void BuildProductionRaftMaterials()" in source
    assert "SaturatedRoughnessScale=*/0.46f" in source
    assert "SaturatedRoughnessMax=*/0.40f" in source
    assert "Material->SetMaterialUsage(MATUSAGE_StaticMesh)" in source
    assert 'TEXT("RaftSim.CreateProductionRaftMaterials")' in source
    script = RAFT_MATERIAL_SCRIPT.read_text(encoding="utf-8")
    assert 'COMMAND = "RaftSim.CreateProductionRaftMaterials"' in script
    assert "CreateRaftCrewMaterials" not in script
    actor_source = RAFT_ACTOR_SOURCE.read_text(encoding="utf-8")
    assert "SurfaceWetness * 0.42f" in actor_source
    assert "0.0f, 0.50f" in actor_source
    assert 'TEXT("Wetness"), PresentationWetness' in actor_source
    assert "SurfaceWetness remains the full physical/telemetry signal" in actor_source
    assert "M_RaftSim_RaftFloorReadable" in actor_source
    assert 'TEXT("TextileTiling"), 7.5f' in actor_source
    assert 'TEXT("TextileNormalStrength"), 0.42f' in actor_source
    assert 'TEXT("FloorShadowFill"), 0.28f' in actor_source
    mesh_source = MESH_SOURCE.read_text(encoding="utf-8")
    assert "const float IBeamRelief = Tr * 0.095f" in mesh_source


def test_production_river_boot_replaces_only_the_procedural_footwear_overlay() -> None:
    manifest = json.loads(PRODUCTION_BOOT_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["ownership"] == (
        "Project-owned deterministic source art; no external mesh or texture input."
    )
    assert manifest["source_inputs"] == []
    assert manifest["material_slots"] == [
        "BootUpper",
        "BootSole",
        "BootReinforcement",
    ]
    assert manifest["construction"] == {
        "outsole_lugs": 12,
        "vamp_drain_bands": 3,
        "pull_tabs": 1,
    }
    assert manifest["vertex_count"] >= 4_000
    assert manifest["polygon_count"] >= 4_000
    fbx_path = REPO_ROOT / manifest["fbx"]
    assert hashlib.sha256(fbx_path.read_bytes()).hexdigest() == manifest["fbx_sha256"]
    assert PRODUCTION_BOOT_ASSET.is_file()

    build_source = PRODUCTION_BOOT_BUILD_SCRIPT.read_text(encoding="utf-8")
    import_source = PRODUCTION_BOOT_IMPORT_SCRIPT.read_text(encoding="utf-8")
    material_source = PRODUCTION_BOOT_MATERIAL_SCRIPT.read_text(encoding="utf-8")
    assert "Visual-only river footwear" in build_source
    assert "outsole_lugs" in build_source
    assert "nanite.enabled = True" in import_source
    assert "existing_nanite.enabled = False" in import_source
    assert "Production river boot must retain twelve outsole lugs" in import_source
    assert "M_RaftSim_RiverBootUpper" in import_source
    assert "M_RaftSim_RiverBootRubber" in import_source
    assert "T_RaftSim_WetsuitNeoprene_Albedo" in material_source
    assert "T_RaftSim_WetsuitNeoprene_Normal" in material_source
    assert "T_RaftSim_WetsuitNeoprene_AORoughnessHeight" in material_source
    assert "MATUSAGE_NANITE" in material_source
    assert 'get_editor_property("used_with_nanite")' in material_source
    assert '"nanite_usage_persisted"' in material_source
    assert "Visual materials only" in material_source

    raft_source = CREW_AVATAR_SOURCE.read_text(encoding="utf-8")
    raft_header = CREW_AVATAR_HEADER.read_text(encoding="utf-8")
    for contract in (
        "ProductionLeftBoot",
        "ProductionRightBoot",
        "HasProductionRiverBoots()",
        "HasFittedUprightProductionRiverBoots()",
        "bReplacedBootLayer",
        "SM_RaftSim_WhitewaterRiverBoot",
        "kProductionRiverBootPresentationScale(0.88f, 0.92f, 0.68f)",
        "FRotationMatrix::MakeFromXZ(ToeForward, FVector::UpVector)",
        "PlaceProductionBoot(ProductionLeftBoot, Pose.LeftFootCm)",
        "PlaceProductionBoot(ProductionRightBoot, Pose.RightFootCm)",
        "SourceSoleZCm * Profile.Z",
        "SetCollisionEnabled(ECollisionEnabled::NoCollision)",
    ):
        assert contract in raft_source or contract in raft_header
    assert "the single animation authority" in raft_source


def test_contact_water_cards_follow_d4_segment_authority() -> None:
    raft_source = RAFT_ACTOR_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "GetDominantWaterContactPresentation",
        "GetFlexibleVisualSegments()",
        "Segment.IndentationM > OutIndentationM",
        "Dominant->LocalPositionM * 100.0f",
        "Dominant->ContactNormalLocal",
    ):
        assert contract in raft_source

    vfx_source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    vfx_header = WATER_VFX_HEADER.read_text(encoding="utf-8")
    for contract in (
        "IsProductionNiagaraReady",
        "GetProductionNiagaraComponentCount",
        "GetActiveRapidAerosolNiagaraCount",
    ):
        assert contract in vfx_header
    for contract in (
        "UInstancedStaticMeshComponent",
        "UProceduralMeshComponent",
        "UNiagaraComponent",
        'TEXT("User.SpawnRate")',
        "NS_RaftSim_SolverSpray",
        "NS_RaftSim_ContactDroplets",
        "NS_RaftSim_AeratedMist",
        "NS_RaftSim_RapidAerosol",
        "NS_RaftSim_RapidRoller",
        "SetBreakingRollerVolumeRenderingEnabled",
        "ActiveRapidRollerNiagaraCount",
        "ParticleSurfaceCenter",
        "MakeCameraFacingCardRotation",
        "ConfigureVfxComponent(SprayInstances, PlaneMesh, Material)",
        "ConfigureVfxComponent(MistInstances, PlaneMesh, Material)",
        "ConfigureVfxComponent(DropletInstances, PlaneMesh, Material)",
        "GetDominantWaterContactPresentation",
        "ImpactDirection",
        "ImpactFoamCount",
        "0.61803398875f",
        "PhaseJitter",
        "TurbulentAcross",
        "JetReach",
        "JetHeight",
        "SprayInstances, 0.115f",
        "MistInstances, 0.032f",
        "RapidAerosolInstances, 0.024f",
        "DropletInstances, 0.18f",
        "74.0f * LastPresentationState.Spray",
        "112.0f * LastPresentationState.Droplets",
        "28.0f * VisibleMist",
        "VfxOpacity",
        "VfxColor",
        "VfxRoughness",
        "GetImpactFoamInstanceCount",
        "(CameraLocation - Location).GetSafeNormal()",
        "UpdateContactWaterPatch",
        "OutwardPresentationOffsetCm",
        "ContactPatchCenter",
        "ContactOutward * OutwardPresentationOffsetCm",
        "LongitudinalVertexCount = 9",
        "LateralVertexCount = 7",
        "ContactWaterPatch->SetCollisionEnabled(ECollisionEnabled::NoCollision)",
        "ContactWaterPatchTriangleCount = PatchTriangles.Num() / 3",
        'TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip."',
        'TEXT("BreakingFoamOpacity"), 0.58f',
        'TEXT("BreakingFoamCoreGain"), 0.62f',
        "AeratedCore,",
        "Loading them through ConstructorHelpers here",
        "BeginPlay performs the same bounded loads after engine/module startup",
        "LoadObject<UNiagaraSystem>",
        "if (!Component->HasBegunPlay())",
        "Component->SetAutoActivate(false)",
        "MaxActiveRapidNiagaraSites = 2",
        "RapidNiagaraCullDistanceCm = 12000.0f",
        "RankedSiteIndices.Sort",
        "FMath::Lerp(6.0f, 28.0f, Intensity) * DistanceDensity",
        "FMath::Lerp(24.0f, 90.0f, Intensity) * DistanceDensity",
        "156.0f * LastPresentationState.Spray",
        "176.0f * LastPresentationState.Droplets",
        "34.0f * NiagaraVisibleMist",
    ):
        assert contract in vfx_source
    assert "ConstructorHelpers::FObjectFinder<UNiagaraSystem>" not in vfx_source
    assert "/Engine/BasicShapes/Sphere.Sphere" not in vfx_source
    assert (
        '+DirectoriesToAlwaysCook=(Path="/Game/RaftSim/VFX/Water")'
        in DEFAULT_GAME_CONFIG.read_text(encoding="utf-8")
    )

    material_source = ROCK_MATERIAL_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "static UMaterial* BuildSprayMistMaterial()",
        "TLM_VolumetricNonDirectional",
        "UMaterialExpressionDotProduct",
        "RadiusSquared",
        "RadialMask",
        "SoftRadialMask",
        "TriangleWave",
        "UMaterialExpressionFrac",
        "BreakupPattern",
        "SprayBreakup",
        "UMaterialExpressionVertexColor",
        'Scalar(TEXT("VfxNoiseScale"), 6.5f)',
        'Scalar(TEXT("VfxBreakupGain"), 0.45f)',
        'Scalar(TEXT("VfxBreakupFloor"), 0.55f)',
        'Scalar(TEXT("VfxOpacity"), 0.22f)',
    ):
        assert contract in material_source

    capture_source = CAPTURE_SOURCE.read_text(encoding="utf-8")
    assert "contactPatchTriangles=%d contactPatchVisible=%d" in capture_source
    assert "GetContactWaterPatchTriangleCount()" in capture_source
    assert "IsContactWaterPatchVisible()" in capture_source


def test_connected_contact_water_v6_is_opt_in_noncolliding_and_solver_shaped() -> None:
    source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    header = WATER_VFX_HEADER.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")

    for contract in (
        "RaftSimConnectedContactWaterV6Review",
        "bConnectedContactWaterV6ReviewRequested",
        "UpdateConnectedContactWaterV6Review",
        "HideConnectedContactWaterV6Review",
        "AcrossVertexCount = 11",
        "ArcVertexCount = 9",
        "solver-sampled D4 shoulder",
        "ExposedSurfaceCenterCm",
        "ExposedOutward * 115.0f * ContactScale",
        "WaterAdapter->SampleWaterAtWorldPosition",
        "ConnectedContactWaterV6TriangleCount = Triangles.Num() / 3",
        "ConnectedContactWaterV6Review->SetVisibility(true, true)",
        "connected V6 and photographic atlas review switches cannot be combined",
        "photographic breakup over this",
        "solver-shaped sheet",
    ):
        assert contract in source
    assert (
        "ConnectedContactWaterV6Review->SetCollisionEnabled(\n"
        "        ECollisionEnabled::NoCollision)"
    ) in source
    assert "bool bConnectedContactWaterV6Review = false;" in header
    assert "GetConnectedContactWaterV6TriangleCount" in header
    assert "IsConnectedContactWaterV6Visible" in header
    assert "changes no forces, collision, water samples, map state" in source
    assert "connectedV6Triangles=%d connectedV6Visible=%d" in capture
    assert "GetConnectedContactWaterV6TriangleCount()" in capture
    assert "IsConnectedContactWaterV6Visible()" in capture

    editor_source = CONNECTED_WATER_V6_EDITOR_SOURCE.read_text(encoding="utf-8")
    author_source = CONNECTED_WATER_V6_AUTHOR_SCRIPT.read_text(encoding="utf-8")
    for contract in (
        "RaftSim.CreateConnectedContactWaterV6ReviewMaterial",
        "M_RaftSim_ConnectedContactWater_V6Review",
        "T_RaftSim_WaterParticleV5Review_SubUV",
        "Frames 11 and 12 are broad aerated-foam donors",
        "ConnectedPhotoBreakupA",
        "ConnectedPhotoBreakupB",
        "PhotographicBreakupGain",
        "ConnectedFoamLace",
        "EdgeFeather",
    ):
        assert contract in editor_source or contract in author_source
    assert "neither frame defines the" in editor_source
    assert "mesh boundary or authorizes an event" in editor_source
    assert "REQUIRED_TEXTURES" in author_source


def test_connected_contact_water_v7_separates_attachment_crest_and_breakup() -> None:
    source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    header = WATER_VFX_HEADER.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")

    for contract in (
        "RaftSimConnectedContactWaterV7Review",
        "bConnectedContactWaterV7ReviewRequested",
        "UpdateConnectedContactWaterV7Review",
        "HideConnectedContactWaterV7Review",
        "presentation-only three-layer solver-contoured contact volume",
        "section 0 is a mask-independent surface attachment",
        "section 1 is an",
        "section 2 is a pair of smaller breakup lobes",
        "BuildLayer(",
        "0, 9, 6",
        "1, 11, 7",
        "2, 13, 5",
        "AttachmentTriangles + CrestTriangles + BreakupTriangles",
        "WaterAdapter->SampleWaterAtWorldPosition",
        "ConnectedContactWaterV7Review->SetVisibility(true, true)",
        "connected V6/V7/V8/V10 and photographic review switches are mutually exclusive",
        "Layer 0 is a horizontal, mask-independent attachment body",
        "Layer 1",
        "Layer 2 supplies two",
    ):
        assert contract in source
    assert (
        "ConnectedContactWaterV7Review->SetCollisionEnabled(\n"
        "        ECollisionEnabled::NoCollision)"
    ) in source
    assert "bool bConnectedContactWaterV7Review = false;" in header
    assert "GetConnectedContactWaterV7TriangleCount" in header
    assert "IsConnectedContactWaterV7Visible" in header
    assert "changes no forces, collision, water samples, map state" in source
    assert "connectedV7Triangles=%d connectedV7Visible=%d" in capture
    assert "GetConnectedContactWaterV7TriangleCount()" in capture
    assert "IsConnectedContactWaterV7Visible()" in capture
    assert "0, 0.14f, 0.16f, 0.06f, 0.0f" in source
    assert "1, 0.040f, 0.80f, 0.10f, 0.0f" in source
    assert "2, 0.008f, 0.86f, 0.060f, 0.32f" in source


def test_connected_contact_water_v8_uses_closed_irregular_lobes() -> None:
    source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    header = WATER_VFX_HEADER.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")

    for contract in (
        "RaftSimConnectedContactWaterV8Review",
        "bConnectedContactWaterV8ReviewRequested",
        "UpdateConnectedContactWaterV8Review",
        "HideConnectedContactWaterV8Review",
        "sampled attachment plus six short closed",
        "there is no shared vertical",
        "constexpr int32 LobeCount = 6",
        "constexpr int32 AlongSegments = 8",
        "constexpr int32 RadialSegments = 8",
        "AcrossOffsets[LobeCount]",
        "LengthScales[LobeCount]",
        "RadiusScales[LobeCount]",
        "PhaseOffsets[LobeCount]",
        "SampleWaterAtWorldPosition",
        "AttachmentTriangles.Num() / 3 + LobeTriangleTotal",
        "ConnectedContactWaterV8Review->SetVisibility(true, true)",
        "ConnectedReviewRequestCount > 1",
        "connected V6/V7/V8/V10 and photographic review switches are mutually exclusive",
        "separate closed bodies carry aeration",
    ):
        assert contract in source
    assert (
        "ConnectedContactWaterV8Review->SetCollisionEnabled(\n"
        "        ECollisionEnabled::NoCollision)"
    ) in source
    assert "bool bConnectedContactWaterV8Review = false;" in header
    assert "GetConnectedContactWaterV8TriangleCount" in header
    assert "IsConnectedContactWaterV8Visible" in header
    assert "changes no forces, collision, water" in source
    assert "connectedV8Triangles=%d connectedV8Visible=%d" in capture
    assert "GetConnectedContactWaterV8TriangleCount()" in capture
    assert "IsConnectedContactWaterV8Visible()" in capture
    assert "ConfigureV8Section(0, 0.10f, 0.13f" in source
    assert "SectionIndex, 0.028f, 0.38f" in source


def test_depth_bearing_contact_water_v10_is_closed_cached_and_d4_gated() -> None:
    source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    header = WATER_VFX_HEADER.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")

    for contract in (
        "RaftSimDepthBearingContactWaterV10Review",
        "DepthBearingContactWaterV10FrameCount = 6",
        "DepthBearingContactWaterV10FrameSeconds = 0.12f",
        "EvaluateDepthBearingContactWaterV10Field",
        "BuildDepthBearingContactWaterV10Cache",
        "marching tetrahedra",
        "two overlapping asymmetric shoulders",
        "DepthBearingContactWaterV10Review->CreateMeshSection_LinearColor",
        "DepthBearingContactWaterV10Review->SetCollisionEnabled",
        "ECollisionEnabled::NoCollision",
        "DepthBearingContactWaterV10Review->SetCanEverAffectNavigation(false)",
        "GetDominantWaterContactPresentation",
        "UpdateDepthBearingContactWaterV10Review",
        "no force, collision",
        "RaftSimDepthBearingContactWaterV10Frame=",
        "SetMeshSectionVisible",
        "DepthBearingContactWaterV10DepthCm >= 100.0f",
        "RaftSimDepthBearingContactWaterV10OpaqueDiagnostic",
        "M_RaftSim_BreakingWaterLip",
        "WorldGridMaterial",
        "WarpedY",
        "TopEnvelope",
        "ClosedVolumeCoverage",
        "VisibleCoverage",
        "connected V6/V7/V8/V10 and photographic review switches are mutually exclusive",
    ):
        assert contract in source
    for contract in (
        "GetDepthBearingContactWaterV10TriangleCount",
        "GetDepthBearingContactWaterV10CachedFrameCount",
        "GetDepthBearingContactWaterV10CurrentFrame",
        "GetDepthBearingContactWaterV10DepthCm",
        "bool bDepthBearingContactWaterV10Review = false;",
    ):
        assert contract in header
    for contract in (
        "depthV10Triangles=%d depthV10Visible=%d",
        "depthV10Frames=%d depthV10Frame=%d",
        "depthV10DepthCm=%.2f",
        "GetDepthBearingContactWaterV10CachedFrameCount()",
    ):
        assert contract in capture
    assert "BuildDepthBearingContactWaterV10Cache()" in source
    assert "bDepthBearingContactWaterV10Review = false" in source


def test_production_niagara_particle_atlas_is_owned_and_profile_partitioned() -> None:
    editor_source = NIAGARA_WATER_VFX_EDITOR_SOURCE.read_text(encoding="utf-8")
    automation_source = NIAGARA_WATER_VFX_AUTOMATION_SOURCE.read_text(encoding="utf-8")
    generator_source = WATER_PARTICLE_ATLAS_GENERATOR.read_text(encoding="utf-8")
    for contract in (
        "M_RaftSim_NiagaraWaterParticle",
        "T_RaftSim_WaterParticle_SubUV.png",
        "UMaterialExpressionParticleSubUV",
        "UMaterialExpressionDepthFade",
        "ParticleAtlasGridSize = 4",
        "ENSMSubUVAnimation_Mode::DirectSet",
        "SubUv->FrameIndex.Mode = ENiagaraDistributionMode::UniformRange",
        "Sprite->SubImageSize",
        "ParticleDepthFadeCm",
    ):
        assert contract in editor_source
    assert "FTextureCompilingManager::Get().FinishCompilation" in automation_source
    assert "ParticleAtlas->BlockOnAnyAsyncBuild()" in automation_source
    m5_automation_source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    assert "void FinishTextureCompilation(UTexture2D* Texture)" in m5_automation_source
    assert "FTextureCompilingManager::Get().FinishCompilation" in m5_automation_source
    assert "solver/contact state remains the sole emission source" in generator_source

    provenance = json.loads(WATER_PARTICLE_ATLAS_PROVENANCE.read_text(encoding="utf-8"))
    assert provenance["ownership"] == "project_owned_first_party_procedural"
    assert provenance["external_source_input"] is False
    assert provenance["authoritative_geography_claim"] is False
    assert provenance["grid"] == [4, 4]
    assert provenance["cell_dimensions_px"] == [512, 512]
    assert provenance["frame_ranges"] == {
        "solver_spray": [0, 5],
        "contact_droplets": [6, 10],
        "aerated_mist": [11, 13],
        "rapid_aerosol": [14, 15],
    }
    assert (
        hashlib.sha256(WATER_PARTICLE_ATLAS.read_bytes()).hexdigest()
        == provenance["sha256"]
    )
    with Image.open(WATER_PARTICLE_ATLAS) as atlas:
        assert atlas.size == (2048, 2048)
        assert atlas.mode == "L"


def test_photographic_water_atlas_v4_is_owned_padded_and_review_only() -> None:
    provenance = json.loads(
        PHOTOGRAPHIC_WATER_ATLAS_PROVENANCE.read_text(encoding="utf-8")
    )
    review_evidence = json.loads(
        PHOTOGRAPHIC_WATER_REVIEW_EVIDENCE.read_text(encoding="utf-8")
    )
    generator_source = PHOTOGRAPHIC_WATER_ATLAS_GENERATOR.read_text(encoding="utf-8")
    editor_source = NIAGARA_WATER_VFX_EDITOR_SOURCE.read_text(encoding="utf-8")
    runtime_source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    import_source = PHOTOGRAPHIC_WATER_ATLAS_IMPORT_SCRIPT.read_text(encoding="utf-8")

    assert provenance["ownership"] == "project_owned_first_party_image_generation"
    assert provenance["image_generation_mode"] == "built_in_imagegen"
    assert provenance["external_source_input"] is False
    assert provenance["authoritative_geography_claim"] is False
    assert provenance["usage"].startswith("Review-only presentation atlas")
    assert review_evidence["passed"] is False
    assert review_evidence["promotion_allowed"] is False
    assert review_evidence["decision"] == (
        "retain_production_atlas_reject_current_photographic_candidate"
    )
    assert review_evidence["authoritative_geography_claim"] is False
    assert review_evidence["production"]["selected"] is True
    assert review_evidence["isolation"]["default_switch_state"] is False
    assert (
        review_evidence["isolation"]["solver_contact_emission_authority_changed"]
        is False
    )
    assert (
        review_evidence["isolation"][
            "current_review_assets_restored_to_unscaled_profiles"
        ]
        is True
    )
    assert provenance["dimensions_px"] == [2048, 2048]
    assert provenance["grid"] == [4, 4]
    assert provenance["cell_dimensions_px"] == [512, 512]
    assert provenance["minimum_black_padding_px"] >= 77
    assert provenance["minimum_black_padding_fraction"] >= 0.15
    assert provenance["frame_ranges"] == {
        "solver_spray": [0, 5],
        "contact_droplets": [6, 10],
        "aerated_mist": [11, 13],
        "rapid_aerosol": [14, 15],
    }
    assert provenance["source_frame_for_target"] == [
        0,
        1,
        2,
        3,
        4,
        5,
        8,
        9,
        10,
        11,
        6,
        12,
        13,
        14,
        15,
        7,
    ]
    assert (
        "high-speed macro photography of real cold freshwater"
        in provenance["source_prompt"]
    )
    assert "review-only photographic" in generator_source
    assert "solver/contact state remains the sole authority" in generator_source.lower()
    for contract in (
        "RaftSim.CreatePhotographicV4ReviewNiagaraWaterVfxSystems",
        "T_RaftSim_WaterParticle_SubUV_v4_review.png",
        "M_RaftSim_NiagaraWaterParticle_V4Review",
        "NS_RaftSim_SolverSpray_V4Review",
        "PhotographicSubUVV4Review",
    ):
        assert contract in editor_source or contract in import_source
    assert "RaftSimPhotographicWaterAtlasV4Review" in runtime_source
    assert "Production maps/assets remain byte-identical" in runtime_source
    assert 'TEXT("/Game/RaftSim/VFX/Water/%s.%s")' in runtime_source
    assert "isolated review complete" in import_source
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_ATLAS_SOURCE.read_bytes()).hexdigest()
        == (provenance["source_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_ATLAS_REVIEW.read_bytes()).hexdigest()
        == (provenance["sha256"])
    )
    assert (
        hashlib.sha256(WATER_PARTICLE_ATLAS.read_bytes()).hexdigest()
        == (review_evidence["production"]["source_atlas_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_ATLAS_SOURCE.read_bytes()).hexdigest()
        == (review_evidence["candidate_source"]["generated_source_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_ATLAS_REVIEW.read_bytes()).hexdigest()
        == (review_evidence["candidate_source"]["derived_review_atlas_sha256"])
    )
    for relative_path, expected_sha256 in review_evidence["isolation"][
        "current_review_asset_sha256"
    ].items():
        asset_path = PHOTOGRAPHIC_WATER_REVIEW_ASSET_DIR / relative_path
        assert asset_path.is_file()
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == expected_sha256
    for relative_path, expected_sha256 in review_evidence["production"][
        "runtime_asset_sha256"
    ].items():
        asset_path = REPO_ROOT / relative_path
        assert asset_path.is_file()
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == expected_sha256

    with Image.open(PHOTOGRAPHIC_WATER_ATLAS_REVIEW) as atlas:
        assert atlas.size == (2048, 2048)
        assert atlas.mode == "L"
        frame_hashes = set()
        for frame in range(16):
            row, column = divmod(frame, 4)
            cell = atlas.crop(
                (
                    column * 512,
                    row * 512,
                    (column + 1) * 512,
                    (row + 1) * 512,
                )
            )
            for edge in (
                cell.crop((0, 0, 77, 512)),
                cell.crop((435, 0, 512, 512)),
                cell.crop((0, 0, 512, 77)),
                cell.crop((0, 435, 512, 512)),
            ):
                assert edge.getextrema() == (0, 0)
            histogram = cell.histogram()
            assert sum(histogram[5:]) > 2_500
            assert cell.getextrema()[1] >= 180
            frame_hashes.add(hashlib.sha256(cell.tobytes()).hexdigest())
        assert len(frame_hashes) == 16


def test_photographic_water_atlas_v5_is_particle_scale_mip_safe_and_isolated() -> None:
    provenance = json.loads(
        PHOTOGRAPHIC_WATER_V5_ATLAS_PROVENANCE.read_text(encoding="utf-8")
    )
    review_evidence = json.loads(
        PHOTOGRAPHIC_WATER_V5_REVIEW_EVIDENCE.read_text(encoding="utf-8")
    )
    generator_source = PHOTOGRAPHIC_WATER_V5_ATLAS_GENERATOR.read_text(encoding="utf-8")
    import_source = PHOTOGRAPHIC_WATER_V5_IMPORT_SCRIPT.read_text(encoding="utf-8")
    editor_source = NIAGARA_WATER_VFX_EDITOR_SOURCE.read_text(encoding="utf-8")
    runtime_source = WATER_VFX_SOURCE.read_text(encoding="utf-8")
    capture_source = CAPTURE_SOURCE.read_text(encoding="utf-8")

    assert provenance["ownership"] == "project_owned_first_party_image_generation"
    assert provenance["image_generation_mode"] == "built_in_imagegen"
    assert provenance["external_source_input"] is False
    assert provenance["authoritative_geography_claim"] is False
    assert provenance["usage"].startswith("Review-only particle-scale")
    assert review_evidence["passed"] is False
    assert review_evidence["promotion_allowed"] is False
    assert review_evidence["decision"] == (
        "retain_production_atlas_reject_current_photographic_v5_candidate"
    )
    assert review_evidence["production"]["selected"] is True
    assert review_evidence["isolation"]["default_switch_state"] is False
    assert review_evidence["isolation"]["production_assets_modified_by_review"] is False
    assert (
        review_evidence["isolation"]["solver_contact_emission_authority_changed"]
        is False
    )
    assert (
        review_evidence["isolation"]["world_space_sprite_dimensions_changed"] is False
    )
    assert provenance["dimensions_px"] == [2048, 2048]
    assert provenance["grid"] == [4, 4]
    assert provenance["cell_dimensions_px"] == [512, 512]
    assert provenance["minimum_black_padding_px"] >= 93
    assert provenance["minimum_black_padding_fraction"] >= 0.18
    assert provenance["mip_review_size_px"] == 32
    assert provenance["frame_ranges"] == {
        "solver_spray": [0, 5],
        "contact_droplets": [6, 10],
        "aerated_mist": [11, 13],
        "rapid_aerosol": [14, 15],
    }
    assert [
        (record["source"], record["source_frame"])
        for record in provenance["frame_sources"]
    ] == [
        ("spray_foam", 0),
        ("spray_foam", 1),
        ("spray_foam", 2),
        ("spray_foam", 3),
        ("spray_foam", 6),
        ("spray_foam", 7),
        ("droplets", 2),
        ("droplets", 3),
        ("droplets", 4),
        ("droplets", 6),
        ("droplets", 8),
        ("aerated_foam", 0),
        ("aerated_foam", 1),
        ("aerated_foam", 2),
        ("aerated_foam", 8),
        ("aerated_foam", 10),
    ]
    assert provenance["spray_foam_source_regions_px"] == {
        "0": [20, 60, 345, 260],
        "1": [340, 60, 635, 250],
        "2": [640, 60, 950, 250],
        "3": [940, 60, 1240, 245],
        "6": [630, 300, 940, 520],
        "7": [940, 320, 1240, 520],
    }
    for source_name, source_path in PHOTOGRAPHIC_WATER_V5_SOURCE_PATHS.items():
        source_record = provenance["sources"][source_name]
        assert source_record["dimensions_px"] == [1254, 1254]
        assert (
            hashlib.sha256(source_path.read_bytes()).hexdigest()
            == source_record["sha256"]
        )
        prompt = source_record["prompt"]
        assert "particle" in prompt.lower() or "mip-safe" in prompt.lower()
        assert "authoritative geography" not in prompt.lower()
    assert "solver/contact state remains the sole authority" in generator_source.lower()
    assert "SPRAY_FOAM_SOURCE_REGIONS" in generator_source
    for contract in (
        "RaftSim.CreatePhotographicV5ReviewNiagaraWaterVfxSystems",
        "T_RaftSim_WaterParticle_SubUV_v5_review.png",
        "M_RaftSim_NiagaraWaterParticle_V5Review",
        "PhotographicSubUVV5Review",
    ):
        assert contract in editor_source or contract in import_source
    assert "NS_RaftSim_SolverSpray_V5Review" in import_source
    assert "production-scale sprites survive the material path" in editor_source
    assert "AuthoredProfile.Color.A = 0.16f" in editor_source
    assert "AuthoredProfile.Color.A = 0.14f" in editor_source
    assert "AuthoredProfile.Color.A = 0.78f" in editor_source
    assert "AuthoredProfile.Color.A = 0.88f" in editor_source
    assert "RaftSimPhotographicWaterAtlasV5Review" in runtime_source
    assert "failing closed to production assets" in runtime_source
    assert "Production maps/assets remain byte-identical" in runtime_source
    assert 'CameraPreset == TEXT("particle_macro")' in capture_source
    assert "production-scale 2-6 cm spray" in capture_source
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_V5_ATLAS_REVIEW.read_bytes()).hexdigest()
        == (provenance["sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_V5_MIP_PREVIEW.read_bytes()).hexdigest()
        == (provenance["mip_review_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_V5_ATLAS_PROVENANCE.read_bytes()).hexdigest()
        == (review_evidence["candidate_source"]["provenance_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_V5_ATLAS_GENERATOR.read_bytes()).hexdigest()
        == (review_evidence["candidate_source"]["generator_sha256"])
    )
    assert (
        hashlib.sha256(PHOTOGRAPHIC_WATER_V5_IMPORT_SCRIPT.read_bytes()).hexdigest()
        == (review_evidence["isolation"]["author_script_sha256"])
    )
    for relative_path, expected_sha256 in review_evidence["isolation"][
        "current_review_asset_sha256"
    ].items():
        asset_path = PHOTOGRAPHIC_WATER_V5_REVIEW_ASSET_DIR / relative_path
        assert asset_path.is_file()
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == expected_sha256
    for relative_path, expected_sha256 in review_evidence["production"][
        "runtime_asset_sha256"
    ].items():
        asset_path = REPO_ROOT / relative_path
        assert asset_path.is_file()
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == expected_sha256
    for section_name in (
        "initial_contact",
        "matched_particle_macro",
        "calibrated_gameplay_views",
        "expanded_mist_mip_view",
    ):
        section = review_evidence["native_renderer_review"][section_name]
        for key, value in section.items():
            if key.endswith("capture"):
                capture_path = REPO_ROOT / value
                assert capture_path.is_file()
                assert (
                    hashlib.sha256(capture_path.read_bytes()).hexdigest()
                    == section[f"{key}_sha256"]
                )
    assert len(provenance["mip_metrics"]) == 16
    assert all(metric["border_max"] == 0 for metric in provenance["mip_metrics"])
    assert all(
        metric["active_pixels_gt_8"] >= 50 for metric in provenance["mip_metrics"]
    )

    with Image.open(PHOTOGRAPHIC_WATER_V5_ATLAS_REVIEW) as atlas:
        assert atlas.size == (2048, 2048)
        assert atlas.mode == "L"
        mip_hashes = set()
        for frame in range(16):
            row, column = divmod(frame, 4)
            cell = atlas.crop(
                (
                    column * 512,
                    row * 512,
                    (column + 1) * 512,
                    (row + 1) * 512,
                )
            )
            for edge in (
                cell.crop((0, 0, 93, 512)),
                cell.crop((419, 0, 512, 512)),
                cell.crop((0, 0, 512, 93)),
                cell.crop((0, 419, 512, 512)),
            ):
                assert edge.getextrema() == (0, 0)
            mip = cell.resize((32, 32), resample=Image.Resampling.LANCZOS)
            assert mip.getextrema()[1] >= 200
            mip_hashes.add(hashlib.sha256(mip.tobytes()).hexdigest())
        assert len(mip_hashes) == 16


def test_packaged_performance_probe_records_and_applies_renderer_state_post_travel() -> (
    None
):
    source = CONTENT_LOCK_DIRECTOR_SOURCE.read_text(encoding="utf-8")
    for contract in (
        "ApplyBoundedIntegerConsoleVariable",
        "RaftSimPerformanceAntiAliasingMethod=",
        "RaftSimPerformanceBloomQuality=",
        "RaftSimPerformanceSkeletalMeshLodBias=",
        "RaftSimPerformanceViewDistanceQuality=",
        "RaftSimPerformanceAntiAliasingQuality=",
        "RaftSimPerformanceGlobalIlluminationQuality=",
        "RaftSimPerformanceReflectionQuality=",
        "RaftSimPerformanceShadowQuality=",
        "RaftSimPerformancePostProcessQuality=",
        "RaftSimPerformanceEffectsQuality=",
        "RaftSimPerformanceFoliageQuality=",
        "RaftSimPerformanceTextureQuality=",
        "RaftSimPerformanceShadingQuality=",
        "RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled=",
        "RaftSimPerformanceNaniteEnabled=",
        "RaftSimPerformanceVolumetricCloudEnabled=",
        "RaftSimPerformanceDisableSkeletalMeshes",
        "RaftSimPerformanceCharacterBodyOnlyShadows",
        "EngineShowFlags.SetSkeletalMeshes(false)",
        'TEXT("character_body_only_shadows")',
        'TEXT("skeletal_meshes_rendered")',
        'TEXT("anti_aliasing_method"), TEXT("r.AntiAliasingMethod")',
        'TEXT("bloom_quality"), TEXT("r.BloomQuality")',
        'TEXT("skeletal_mesh_lod_bias"), TEXT("r.SkeletalMeshLODBias")',
        'TEXT("lumen_final_gather_method"), TEXT("r.Lumen.FinalGatherMethod")',
        'TEXT("lumen_translucency_radiance_cache_enabled")',
        'TEXT("r.Lumen.TranslucencyReflections.RadianceCache")',
        'TEXT("translucency_lighting_volume_mark_voxels_enabled")',
        'TEXT("r.TranslucencyLightingVolume.MarkVoxels")',
        'TEXT("mean_gpu_ms"), Gpu.Mean',
        'TEXT("render_offscreen")',
        'TEXT("offscreen_engineering_diagnostic")',
        'TEXT("normal_windowed_player_presentation")',
        'TEXT("release_performance_qualification_eligible")',
        'TEXT("release_performance_qualified")',
        'TEXT("performance_profile_requirement_passed")',
        'TEXT("view_distance_quality"), TEXT("sg.ViewDistanceQuality")',
        'TEXT("anti_aliasing_quality"), TEXT("sg.AntiAliasingQuality")',
        'TEXT("texture_quality"), TEXT("sg.TextureQuality")',
        'TEXT("shading_quality"), TEXT("sg.ShadingQuality")',
    ):
        assert contract in source

    mac_rc = (REPO_ROOT / "unreal/Scripts/build_mac_rc.sh").read_text(encoding="utf-8")
    scalability = DEFAULT_SCALABILITY_CONFIG.read_text(encoding="utf-8")
    assert "[ReflectionQuality@2]" in scalability
    assert "r.Lumen.TranslucencyReflections.RadianceCache=0" in scalability
    assert '-UserDir="$FRESH_PROFILE_ROOT"' in mac_rc
    assert mac_rc.count("assert_no_competing_unreal_processes") >= 3
    assert "ps -axo pid=,ucomm=,command=" in mac_rc
    assert '$2 == "UnrealEditor"' in mac_rc
    assert '$2 == "UnrealEditor-Cmd"' in mac_rc
    for contract in (
        "RaftSimPerformanceViewDistanceQuality=2",
        "RaftSimPerformanceAntiAliasingQuality=2",
        "RaftSimPerformanceGlobalIlluminationQuality=2",
        "RaftSimPerformanceReflectionQuality=2",
        "RaftSimPerformanceShadowQuality=2",
        "RaftSimPerformancePostProcessQuality=2",
        "RaftSimPerformanceTextureQuality=2",
        "RaftSimPerformanceEffectsQuality=2",
        "RaftSimPerformanceFoliageQuality=2",
        "RaftSimPerformanceShadingQuality=2",
        "RaftSimPerformanceAntiAliasingMethod=4",
        "RaftSimPerformanceBloomQuality=5",
        "RaftSimPerformanceSkeletalMeshLodBias=0",
        "RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled=0",
        "RaftSimPerformanceNaniteEnabled=1",
        "RaftSimPerformanceVolumetricCloudEnabled=1",
    ):
        assert contract in mac_rc

    windows_rc = (REPO_ROOT / "unreal/Scripts/build_win_rc.ps1").read_text(
        encoding="utf-8"
    )
    assert windows_rc.count("Assert-NoCompetingUnrealProcesses") >= 3
    assert '"-UserDir=$FreshProfileRoot"' in windows_rc
    for contract in (
        "RaftSimPerformanceScreenPercentage=75",
        "RaftSimPerformanceViewDistanceQuality=2",
        "RaftSimPerformanceAntiAliasingQuality=2",
        "RaftSimPerformanceGlobalIlluminationQuality=2",
        "RaftSimPerformanceReflectionQuality=2",
        "RaftSimPerformanceShadowQuality=2",
        "RaftSimPerformancePostProcessQuality=2",
        "RaftSimPerformanceTextureQuality=2",
        "RaftSimPerformanceEffectsQuality=2",
        "RaftSimPerformanceFoliageQuality=2",
        "RaftSimPerformanceShadingQuality=2",
        "RaftSimPerformanceAntiAliasingMethod=4",
        "RaftSimPerformanceBloomQuality=5",
        "RaftSimPerformanceSkeletalMeshLodBias=0",
        "RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled=0",
        "RaftSimPerformanceNaniteEnabled=1",
        "RaftSimPerformanceVolumetricCloudEnabled=1",
    ):
        assert contract in windows_rc

    meta_human = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimMetaHumanCrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    avatar = CREW_AVATAR_SOURCE.read_text(encoding="utf-8")
    assert "SetBodyOnlyShadowMode" in meta_human
    assert "AssembledBody->SetCastShadow(true)" in meta_human
    assert "AssembledFace->SetCastShadow(!bEnabled)" in meta_human
    assert "SetProductionBodyOnlyShadowMode" in avatar

    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")
    assert 'HasDiagnosticMode(TEXT("taa"))' in capture
    assert 'HasDiagnosticMode(TEXT("nobloom"))' in capture
    assert 'HasDiagnosticMode(TEXT("nocloud"))' in capture
    assert 'TEXT("r.AntiAliasingMethod"), 2' in capture
    assert 'TEXT("r.BloomQuality"), 0' in capture
    assert 'TEXT("r.VolumetricCloud"), 0' in capture
    for contract in (
        'DiagnosticFloat(TEXT("waterfoam="), -1.0f)',
        'DiagnosticFloat(TEXT("waterfoamcore="), -1.0f)',
        'DiagnosticFloat(TEXT("waterfoamlace="), -1.0f)',
        'DiagnosticFloat(TEXT("waterroughness="), -1.0f)',
        'DiagnosticFloat(TEXT("waterspecular="), -1.0f)',
        'DiagnosticFloat(TEXT("livewaterroughness="), -1.0f)',
        'DiagnosticFloat(TEXT("livewaterspecular="), -1.0f)',
        'TEXT("HydraulicFoamIntensity")',
        'TEXT("HydraulicFoamColorCoreGain")',
        'TEXT("HydraulicFoamColorBreakupGain")',
        'TEXT("WaterRoughness")',
        'TEXT("Specular")',
        'TEXT("LiveWaterRoughness")',
        'TEXT("LiveWaterSpecular")',
    ):
        assert contract in capture


def test_shared_crew_pose_articulates_upper_body_without_moving_gameplay_authority() -> (
    None
):
    source = CREW_AVATAR_SOURCE.read_text(encoding="utf-8")

    assert "ApplyWaistPivotedUpperBodyArticulation" in source
    assert "RotateAroundPivot(Pose.LeftShoulderCm)" in source
    assert "RotateAroundPivot(Pose.RightShoulderCm)" in source
    assert "RotateAroundPivot(Pose.HeadCenterCm)" in source
    assert "leaving solved hand, paddle, hip, knee, and" in source
    assert "already-articulated pose" in source


def test_flexible_raft_review_is_fail_closed_and_capture_locked() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["status"] == "technical_upgrade_accepted_photoreal_art_rejected"
    assert review["implementation"]["physics_authority"] == "D4 flexible segment state"
    assert review["implementation"]["rigid_replacement_mesh_used"] is False
    assert review["renderer_evidence"]["human_approved"] is False
    assert review["named_art_reviewer"] is None
    assert review["named_guide_reviewer"] is None
    for evidence_key in ("renderer_evidence", "in_river_renderer_evidence"):
        evidence = review[evidence_key]
        capture = REPO_ROOT / evidence["capture"]
        assert (
            hashlib.sha256(capture.read_bytes()).hexdigest()
            == evidence["capture_sha256"]
        )
        assert evidence["human_approved"] is False


def test_production_raft_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(PRODUCTION_RAFT_REVIEW_PATH.read_text(encoding="utf-8"))
    capture = REPO_ROOT / review["renderer_evidence"]["capture"]
    manifest = json.loads(PRODUCTION_RAFT_MANIFEST.read_text(encoding="utf-8"))

    assert review["status"] == "technical_upgrade_accepted_photoreal_art_rejected"
    assert review["human_approved"] is False
    assert review["named_art_reviewer"] is None
    assert review["named_guide_reviewer"] is None
    assert review["marketing_approved"] is False
    assert review["release_media_approved"] is False
    assert review["runtime_asset"]["collision_enabled"] is False
    assert review["runtime_asset"]["authored_lod0_triangles"] == 38344
    assert review["source"]["fbx_sha256"] == manifest["fbx_sha256"]
    assert review["source"]["blend_sha256"] == manifest["blend_sha256"]
    assert review["automation"]["succeeded"] == 3
    assert review["automation"]["succeeded_with_warnings"] == 1
    assert review["automation"]["failed"] == 0
    assert capture.is_file()
    assert (
        hashlib.sha256(capture.read_bytes()).hexdigest()
        == review["renderer_evidence"]["capture_sha256"]
    )
