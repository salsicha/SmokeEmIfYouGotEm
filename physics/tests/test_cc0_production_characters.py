from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Characters/CC0Production"
)
CONTENT_ROOT = REPO_ROOT / "unreal/Content/RaftSim/Characters/Production/CC0"
REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_production_character_fallback_v287_review.json"
)
TAPERED_SHOULDER_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_tapered_shoulder_sleeves_v2_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict[str, object]:
    return json.loads(
        (SOURCE_ROOT / "character_source_manifest.json").read_text(encoding="utf-8")
    )


def test_cc0_character_manifest_freezes_five_distinct_rights_compatible_sources() -> None:
    manifest = _manifest()

    assert manifest["schema_version"] == 2
    assert manifest["license"]["asset_license"] == "mixed_cc0_1_0_and_cc_by_4_0"
    assert manifest["license"]["body_asset_license"] == "CC0-1.0"
    assert manifest["license"]["hair_asset_license"] == "CC-BY-4.0"
    assert manifest["toolchain"]["mpfb"] == "2.0.17"
    assert manifest["toolchain"]["fbx_world_unit"] == "centimeter"
    assert manifest["toolchain"]["body_topology"] == {
        "vertices": 13380,
        "polygons": 13378,
        "bones": 53,
    }
    assert (SOURCE_ROOT / manifest["license"]["bundled_text"]).is_file()
    assert (SOURCE_ROOT / manifest["license"]["hair_source_manifest"]).is_file()

    characters = manifest["characters"]
    assert len(characters) == 5
    assert {row["name"] for row in characters} == {
        "RaftSim_CC0_Guide",
        "RaftSim_CC0_Crew01",
        "RaftSim_CC0_Crew02",
        "RaftSim_CC0_Crew03",
        "RaftSim_CC0_Crew04",
    }
    assert len({json.dumps(row["parameters"], sort_keys=True) for row in characters}) == 5
    assert len({row["fbx_sha256"] for row in characters}) == 5
    assert {row["hair_asset"] for row in characters} == {
        "elvs_grump_hair",
        "elvs_braided_rows",
        "elvs_short_side_do",
    }
    for row in characters:
        fbx = SOURCE_ROOT / "FBX" / f"{row['name']}.fbx"
        preview = SOURCE_ROOT / "Previews" / f"{row['name']}_preview.png"
        assert _sha256(fbx) == row["fbx_sha256"]
        assert _sha256(preview) == row["preview_sha256"]
        assert (SOURCE_ROOT / row["hair_mhclo"]).is_file()
        assert row["hair_vertices"] > 0
        assert row["export_vertices"] > manifest["toolchain"]["body_topology"]["vertices"]
        assert row["export_polygons"] > manifest["toolchain"]["body_topology"]["polygons"]


def test_cc_by_hair_sources_and_attribution_are_hash_locked() -> None:
    manifest = _manifest()
    source_manifest = json.loads(
        (SOURCE_ROOT / manifest["license"]["hair_source_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    pack = source_manifest["source_pack"]
    assert pack["author"] == "Elvaerwyn"
    assert pack["license"] == "CC-BY-4.0"
    assert pack["catalog_url"].endswith("/hair02.html")
    assert pack["download_sha256"] == (
        "c681e5efd37df4007a52253a8d071aedbfe3b614f199d8dae4ae76d5bd7d95c9"
    )
    assets = source_manifest["assets"]
    assert {row["name"] for row in assets} == {
        "elvs_grump_hair",
        "elvs_braided_rows",
        "elvs_short_side_do",
        "elvs_braid_bun",
    }
    assert next(row for row in assets if row["name"] == "elvs_braid_bun")[
        "review_status"
    ] == "source_retained_not_imported_helmet_intersection_rejected"
    for asset in assets:
        for row in asset["files"]:
            path = SOURCE_ROOT / "Hair/Hair02" / row["path"]
            assert path.stat().st_size == row["bytes"]
            assert _sha256(path) == row["sha256"]

    credits = (REPO_ROOT / "CREDITS.md").read_text(encoding="utf-8")
    assert "Elvaerwyn" in credits
    assert "Hair02" in credits
    assert "CC BY 4.0" in credits


def test_cc0_atlas_hashes_and_license_are_reproducible() -> None:
    manifest = _manifest()
    atlases = manifest["source_atlases"]

    assert len(atlases) == 6
    assert all(row["source"].startswith("https://github.com/makehumancommunity/") for row in atlases)
    for row in atlases:
        atlas = SOURCE_ROOT / row["file"]
        assert atlas.stat().st_size == row["bytes"]
        assert _sha256(atlas) == row["sha256_lfs_oid"]


def test_cc0_generator_bakes_mesh_and_rest_bones_to_centimeters() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/build_cc0_production_character.py"
    ).read_text(encoding="utf-8")

    assert 'bpy.ops.object.join()' in source
    assert 'meters_to_centimeters = Matrix.Scale(100.0, 4)' in source
    assert 'body.data.transform(meters_to_centimeters)' in source
    assert 'rig.data.transform(meters_to_centimeters)' in source
    assert 'length_unit = "CENTIMETERS"' in source
    assert 'apply_scale_options="FBX_SCALE_ALL"' in source
    assert 'global_scale=1.0' in source
    assert '_bind_rigid_mesh(eyes, rig, "head")' in source
    assert '_bind_rigid_mesh(brow, rig, "head")' in source
    assert 'HumanService.add_mhclo_asset(' in source
    assert 'asset_type="Hair"' in source
    assert 'interpolate_weights=True' in source
    assert '_find_exported_hair(source_hair, rig)' in source


def test_cc0_importer_is_hash_tracked_scale_validated_and_idempotent() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/import_cc0_production_characters.py"
    ).read_text(encoding="utf-8")

    assert 'SOURCE_SHA256_METADATA_TAG = "RaftSimSourceSHA256"' in source
    assert 'MIN_PRODUCTION_BODY_HEIGHT_CM = 140.0' in source
    assert 'MAX_PRODUCTION_BODY_HEIGHT_CM = 220.0' in source
    assert 'MIN_REFERENCE_HEAD_HEIGHT_CM = 120.0' in source
    assert 'MAX_REFERENCE_HEAD_HEIGHT_CM = 220.0' in source
    assert '"_Eyes" in name or "_Brow_" in name' in source
    assert 'unreal.EditorAssetLibrary.set_metadata_tag(' in source
    assert 'MATUSAGE_SKELETAL_MESH' in source
    assert 'subsystem.regenerate_lod(mesh, 3, True, False)' in source
    assert '"hair" in normalized' in source
    assert 'unreal.TextureCompressionSettings.TC_NORMALMAP' in source
    assert 'unreal.BlendMode.BLEND_MASKED' in source
    assert 'unreal.MaterialEditingLibrary.delete_all_material_expressions(material)' in source
    assert 'rough.r = 0.68' in source
    assert 'build_materials(textures, rebuild_hair=replace_existing)' in source
    assert 'materials[f"hair_{variant}"]' in source


def test_cc0_production_skin_builder_preserves_atlases_and_adds_physical_response() -> None:
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealMaterials.cpp"
    ).read_text(encoding="utf-8")
    script = (
        REPO_ROOT / "unreal/Scripts/create_production_cc0_skin_materials.py"
    ).read_text(encoding="utf-8")

    assert "static void BuildProductionCC0SkinMaterials()" in source
    assert 'TEXT("M_RaftSim_CC0_Guide_Skin")' in source
    assert 'TEXT("M_RaftSim_CC0_Crew04_Skin")' in source
    assert 'TEXT("T_RaftSim_CC0_LightMale")' in source
    assert 'TEXT("T_RaftSim_CC0_DarkFemale")' in source
    assert "Material->SetShadingModel(MSM_PreintegratedSkin)" in source
    assert "Material->SetMaterialUsage(MATUSAGE_SkeletalMesh)" in source
    assert "MicroUv->UTiling = 36.0f" in source
    assert "MicroUv->VTiling = 36.0f" in source
    assert "BoundedMicroGain->MinDefault = 0.95f" in source
    assert "BoundedMicroGain->MaxDefault = 1.05f" in source
    assert "Constant(0.46f), Constant(0.58f), MicroMask" in source
    assert "Constant(0.16f)" in source
    assert "EditorData->Opacity.Connect(0, Constant(0.94f))" in source
    assert 'TEXT("RaftSim.CreateProductionCC0SkinMaterials")' in source
    assert 'COMMAND = "RaftSim.CreateProductionCC0SkinMaterials"' in script


def test_cc0_runtime_prefers_packaged_bodies_and_keeps_quality_assertions() -> None:
    host = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCrewAvatarActor.cpp"
    ).read_text(encoding="utf-8")
    adapter = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCC0CrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    automation = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimM5ProductionQualityTest.cpp"
    ).read_text(encoding="utf-8")

    assert "ARaftSimCC0CrewVisualActor::StaticClass()->GetPathName()" in host
    assert host.index("ARaftSimCC0CrewVisualActor::StaticClass()->GetPathName()") < host.index(
        "ARaftSimMannyCrewVisualActor::StaticClass()->GetPathName()"
    )
    assert "UPoseableMeshComponent" in adapter
    assert "SetBoneTransformByName" in adapter
    assert "Body->AllocateTransformData()" in adapter
    assert "Body->RefreshBoneTransforms()" in adapter
    assert "ApplyProductionBodyMaterialOverrides(Body, Mesh)" in adapter
    assert "M_RaftSim_Wetsuit.M_RaftSim_Wetsuit" in adapter
    assert 'SlotName.Contains(TEXT("Wetsuit")' in adapter
    assert "Body->SetMaterial(MaterialIndex, ProductionWetsuit)" in adapter
    assert "Body->GetParentBone(BoneName)" in adapter
    assert "Reference->GetLocation() - ReferenceParent->GetLocation()" in adapter
    assert "arbitrary local" in adapter
    assert "Reference->GetRotation().RotateVector(FVector::UpVector)" not in adapter
    assert "ShiftLaterally(Pose.LeftShoulderCm, 30.0f)" in host
    assert "ShiftLaterally(Pose.RightShoulderCm, 30.0f)" in host
    assert "ShiftLaterally(Pose.LeftHipCm, 28.0f)" in host
    assert "ShiftLaterally(Pose.RightHipCm, 28.0f)" in host
    assert "Part == Pelvis || Part == Torso ||" in host
    assert "Part == LeftThigh || Part == RightThigh" in host
    assert "Part == LeftShoulderSleeve || Part == RightShoulderSleeve" in host
    assert "kProductionShoulderSleeveRadiusCm = 5.2f" in host
    assert "kProductionShoulderSleeveArmFraction = 1.0f" in host
    assert "BuildUnitAnatomicalShoulderSleeveMesh(" in host
    assert "constexpr int32 Rings = 18" in host
    assert "constexpr int32 Sides = 28" in host
    assert "0.20f * Deltoid" in host
    assert "0.045f * CuffRoll" in host
    assert 'TEXT("LeftShoulderSleeve"), Jacket ? Jacket : Wetsuit' in host
    assert 'TEXT("RightShoulderSleeve"), Jacket ? Jacket : Wetsuit' in host
    assert "Pose.LeftShoulderCm, LeftElbow, kProductionShoulderSleeveArmFraction" in host
    assert "Pose.RightShoulderCm, RightElbow, kProductionShoulderSleeveArmFraction" in host
    assert "Pose.LeftShoulderCm,\n        LeftShoulderSleeveEnd" in host
    assert "Pose.RightShoulderCm,\n        RightShoulderSleeveEnd" in host
    assert "HasVisibleShoulderSilhouette() const" in host
    assert "GetMinimumShoulderSleeveVertexCount() const" in host
    assert "GetMinimumShoulderSleeveVertexCount() >= 550" in host
    assert "GetMaximumShoulderSleeveAnchorErrorCm() const" in host
    assert "ExtentCm.X >= 4.7f" in host
    assert "ExtentCm.Y >= 4.7f" in host
    assert "ExtentCm.Z >= 5.6f" in host
    assert "ExtentCm.Z > ExtentCm.X" in host
    assert "HasVisibleWaistHipSilhouette() const" in host
    assert "GetWaistHipCenterErrorCm() const" in host
    assert "IsWaistHipMaterialOpaque() const" in host
    assert "Material->GetBlendMode() == BLEND_Opaque" in host
    assert "GetMaximumHipThighBridgeCoverageErrorCm() const" in host
    assert "kProductionHipThighBridgeStartFraction = -0.15f" in host
    assert "kProductionHipThighBridgeEndFraction = 1.06f" in host
    assert "kProductionHipThighBridgeRadiusCm = 8.0f" in host
    assert "BuildUnitHipThighBridgeMesh(" in host
    assert "LeftBridgeSection->ProcVertexBuffer.Num() >= 350" in host
    assert "RightBridgeSection->ProcVertexBuffer.Num() >= 350" in host
    assert "DistanceToBridgeCentreline" in host
    assert "HasContinuousThighKneeSilhouette() const" in host
    assert "GetMaximumThighKneeBridgeCoverageErrorCm() const" in host
    assert "ThighExtentCm.X >= 7.2f" in host
    assert "ThighExtentCm.Y >= 7.2f" in host
    assert "ThighExtentCm.Z >= 15.5f" in host
    assert "BuildUnitSeatedPelvisMesh(" in host
    assert "full waist-to-glute-to-thigh bridge" in host
    assert "kProductionSeatedPelvisReferenceExtentCm(15.0f, 23.0f, 15.0f)" in host
    assert "FMath::Exp(-FMath::Square((Z + 0.35f) / 0.5f))" in host
    assert "SaddleLift = LowerFit" in host
    assert "ExtentCm.X >= 14.0f" in host
    assert "ExtentCm.Y >= 21.0f" in host
    assert "ExtentCm.Z >= 13.8f" in host
    assert "ShiftLaterally(Pose.LeftKneeCm, 22.0f)" in host
    assert "ShiftLaterally(Pose.RightKneeCm, 22.0f)" in host
    assert "ShiftLaterally(Pose.LeftFootCm, 14.0f)" in host
    assert "ShiftLaterally(Pose.RightFootCm, 14.0f)" in host
    assert "const FVector ProductionSkullCenterOffsetCm = bUsingProductionVisual" in host
    assert "constexpr float kProductionHelmetReferenceFit = 0.96f;" in host
    assert "const float CollarFit = bUsingProductionVisual ? 1.28f : 1.0f;" in host
    assert "kProductionHelmetSkullCenterOffsetCm(0.0f, 0.0f, 9.5f)" in host
    assert "kProductionHelmetShellOffsetCm(2.5f, 0.0f, 0.0f)" in host
    assert "kProductionHelmetRetentionOffsetCm(0.0f, 0.0f, 3.0f)" in host
    assert "FVector(0.0f, 0.0f, -4.0f)" in host
    assert "TorsoRotation.RotateVector(ProductionSkullCenterOffsetCm)" in host
    assert "static constexpr float BodyScale = 1.0f;" in (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimCC0CrewVisualActor.h"
    ).read_text(encoding="utf-8")
    assert 'TEXT("Manny fallback is absent with packaged CC0 bodies")' in automation
    assert 'TEXT("five rigged crew bodies spawned")' in automation
    assert "It->GetProceduralBodyPartCount() >= 28" in automation
    assert "It->HasVisibleShoulderSilhouette()" in automation
    assert "ShoulderSleeveVertexCount >= 550" in automation
    assert "ShoulderAnchorErrorCm <= 0.25f" in automation
    assert "It->IsWaistHipMaterialOpaque()" in automation
    assert "HipThighCoverageErrorCm <= 0.25f" in automation
    assert "It->HasContinuousThighKneeSilhouette()" in automation
    assert "ThighKneeCoverageErrorCm <= 0.25f" in automation
    assert "T_RaftSim_Hair_BraidedRows_N" in automation
    assert "has a named hair slot" in automation
    assert "Mesh->GetMaterials().Num()" in automation
    assert "MATUSAGE_SkeletalMesh" in automation


def test_metahuman_roster_is_local_assembled_complete_and_fail_closed() -> None:
    host = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCrewAvatarActor.cpp"
    ).read_text(encoding="utf-8")
    adapter = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimMetaHumanCrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    automation = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimM5ProductionQualityTest.cpp"
    ).read_text(encoding="utf-8")
    project = (REPO_ROOT / "unreal/SmokeEmIfYouGotEm.uproject").read_text(
        encoding="utf-8"
    )
    plugin = (
        REPO_ROOT / "unreal/Plugins/RaftSim/RaftSim.uplugin"
    ).read_text(encoding="utf-8")
    game_config = (
        REPO_ROOT / "unreal/Config/DefaultGame.ini"
    ).read_text(encoding="utf-8")
    engine_config = (
        REPO_ROOT / "unreal/Config/DefaultEngine.ini"
    ).read_text(encoding="utf-8")
    authoring = (
        REPO_ROOT / "unreal/Scripts/build_metahuman_production_characters.py"
    ).read_text(encoding="utf-8")
    capture = (
        REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
    ).read_text(encoding="utf-8")
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    builder = (
        REPO_ROOT / "unreal/Scripts/create_offline_metahuman_skin_material.py"
    ).read_text(encoding="utf-8")
    material_authoring = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorOfflineMetaHumanMaterial.cpp"
    ).read_text(encoding="utf-8")

    assert "ARaftSimMetaHumanCrewVisualActor::AreAllProductionCharactersAvailable()" in host
    assert "ARaftSimMetaHumanCrewVisualActor::StaticClass()->GetPathName()" in host
    assert "TryActivateCC0FallbackVisual()" in host
    assert "InitializeAvatarVisual()" in host
    assert "GetProductionVisualActor() const" in host
    assert "AlignProductionHeadgearToSolvedHead()" in host
    assert "MetaHumanVisual->GetSolvedHeadWorldLocation()" in host
    assert 'f"{stem}_full_profile"' in capture
    assert 'f"{stem}_full_rear"' in capture
    assert "GetProductionHelmetHeadErrorCm() const" in host
    assert "GetProductionHelmetForwardAlignment() const" in host
    assert "GetProductionHelmetFitScale() const" in host
    assert "actor.has_visible_shoulder_silhouette()" in capture
    assert "actor.is_waist_hip_material_opaque()" in capture
    assert "actor.get_minimum_hip_thigh_bridge_extent_cm()" in capture
    assert "actor.get_maximum_hip_thigh_bridge_coverage_error_cm()" in capture
    assert "actor.has_continuous_thigh_knee_silhouette()" in capture
    assert "actor.get_maximum_thigh_knee_bridge_coverage_error_cm()" in capture
    assert "actor.get_minimum_shoulder_sleeve_extent_cm()" in capture
    assert "actor.get_minimum_shoulder_sleeve_vertex_count()" in capture
    assert "actor.get_maximum_shoulder_sleeve_anchor_error_cm()" in capture
    assert "GetSolvedFaceForwardWorldVector() const" in adapter
    assert "GetSolvedFaceUpWorldVector() const" in adapter
    assert "GetRecommendedWhitewaterHelmetScale() const" in adapter
    assert "FRotationMatrix::MakeFromXZ" in host
    assert "HelmetForwardAlignment >= 0.98f" in automation
    assert "HelmetFitScale >= 0.90f && HelmetFitScale <= 1.02f" in automation
    assert "HelmetHeadErrorCm <= 1.0f" in automation
    assert "It->HasVisibleWaistHipSilhouette()" in automation
    assert "WaistHipCenterErrorCm <= 0.1f" in automation
    assert "ARaftSimCC0CrewVisualActor::StaticClass()" in host
    assert "MetaHumanVisual && !MetaHumanVisual->IsBodyReady()" in host
    assert '"/Game/RaftSim/Characters/Production/MetaHumans"' in adapter
    assert "for (int32 RosterIndex = 0; RosterIndex < 5; ++RosterIndex)" in adapter
    assert "UChildActorComponent" in adapter
    assert "SetLeaderPoseComponent(Body, true, false)" in adapter
    assert "AssembledFace->SetLeaderPoseComponent(nullptr, true, false)" in adapter
    assert "AssembledFace->SetAnimationMode(EAnimationMode::AnimationSingleNode)" in adapter
    assert "UpdateRigidAssembledFace()" in adapter
    assert "ReferenceAssembledFaceHeadComponentTransform" in adapter
    assert "AssembledFace->SetWorldTransform" in adapter
    assert "if (Component == AssembledFace)" in adapter
    assert "IsAssembledWardrobeSuppressedForSafetyGear() const" in adapter
    assert "IsAssembledBodyUsingWetsuit() const" in adapter
    assert "bAssembledFaceUsesCroppedSkin" in adapter
    assert "IsAssembledFaceUsingCroppedSkin() const" in (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimMetaHumanCrewVisualActor.h"
    ).read_text(encoding="utf-8")
    assert "AssembledBody->SetMaterial(MaterialIndex, ProductionWetsuit)" in adapter
    assert "bAssembledWardrobeSuppressedForSafetyGear &= !Component->IsVisible()" in adapter
    assert "bHasWardrobe && bHasHair && ReviewedHairMesh" in adapter
    assert "bHasEyebrows && bHasEyelashes" in adapter
    assert "FaceCandidate->GetMaterial(MaterialIndex)" in adapter
    assert 'TEXT("Eyelash"), ESearchCase::IgnoreCase' in adapter
    assert "Component->SetUseCards(true)" in adapter
    assert "Component->SetForcedLOD(5)" in adapter
    assert "SynchronizeAssembledFollowers()" in adapter
    assert "Component->TickAnimation(0.0f, false)" in adapter
    assert "GetAssembledCharacterActor() const" in adapter
    assert "GetAssembledHairForcedLOD() const" in adapter
    assert "ReviewedHairMesh = Source.ImportedMesh" in adapter
    assert 'TEXT("AssembledHairMeshFallback")' in adapter
    assert "HairMeshFallback->SetWorldTransform" in adapter
    assert "GetHairMeshFallbackHeadErrorCm() const" in adapter
    assert "GetSolvedHeadWorldLocation() const" in adapter
    assert "IsHairMeshFallbackSuppressedForHelmet() const" in adapter
    assert "IsAssembledHairGroomSuppressedForHelmet() const" in adapter
    assert "AreAssembledGroomsSuppressedForGameplay() const" in adapter
    assert "AssembledFace->SetBoundsScale(8.0f)" in adapter
    assert "AssembledBody->SetVisibility(true, false)" in adapter
    assert "HairMesh->GetBounds().Origin" in adapter
    assert "HairMeshFallback->UpdateBounds()" in adapter
    assert "ReferenceHead->GetRotation().Inverse()" in adapter
    assert "Component->SetVisibility(false, true)" in adapter
    assert "if (bProductionRosterDeclared)" in adapter
    assert '"/MetaHumanCharacter/Body/IdentityTemplate/SKM_Body.SKM_Body"' in adapter
    assert '"/MetaHumanCharacter/Face/SKM_Face.SKM_Face"' in adapter
    assert "M_RaftSim_MetaHuman_Skin.M_RaftSim_MetaHuman_Skin" in adapter
    assert "Body->AllocateTransformData()" in adapter
    assert "Face->AllocateTransformData()" in adapter
    assert "Body->RefreshBoneTransforms()" in adapter
    assert "Face->RefreshBoneTransforms()" in adapter
    assert "HasCompleteAssembledPresentation()" in automation
    assert "HasArticulatedPaddleGripRig()" in automation
    assert "ApplyPaddleGripPose(Pose)" in adapter
    assert "ResolvePaddleGripWristCm" in adapter
    assert "middle_metacarpal_%s" in adapter
    assert "GetMaximumPaddleGripAnchorErrorCm()" in automation
    assert "GetMaximumPaddleGripContactErrorCm()" in automation
    assert "ApplyFingerChainAroundGrip" in adapter
    assert "MeasurePaddleFingerContactErrorCm" in adapter
    assert "WrapAnglesDegrees[] = {50.0f, 68.0f, 52.0f}" in adapter
    assert "JointRadiiCm[] = {3.2f, 2.65f, 2.35f}" in adapter
    assert "get_maximum_paddle_grip_contact_error_cm()" in capture
    assert "runtime_paddle_grip_contact_error_cm" in capture
    assert "%s_metacarpal_%s" in adapter
    assert "ThumbCurlDegrees" in adapter
    assert "{58.0f, 72.0f, 50.0f}" in adapter
    assert "{34.0f, 50.0f, 38.0f}" in adapter
    assert 'TEXT("assembled roster is all-or-nothing")' in automation
    assert "EvidenceSettings.AutoExposureBias = -1.25f" in automation
    assert '"Name": "MetaHumanCharacter"' in project
    assert '"Name": "HairStrands"' in plugin
    assert "+DirectoriesToAlwaysCook=(Path=\"/Game/RaftSim/Characters/Production\")" in game_config
    assert "-TargetedRHIs=SF_METAL_SM5" in engine_config
    assert "+TargetedRHIs=SF_METAL_SM6" in engine_config
    assert "MetaHumanCharacterEditorSubsystem" in authoring
    assert "request_auto_rigging" in authoring
    assert "request_texture_sources" in authoring
    assert "partial_roster_assembled_clean_editor_restart_required" in authoring
    assert 'if character_record["status"] == "assembled"' in authoring
    assert "RAFTSIM_METAHUMAN_REBUILD_TARGET" in authoring
    assert "Unknown MetaHuman rebuild target" in authoring
    assert "PRODUCTION_QUALITY = unreal.MetaHumanQualityLevel.HIGH" in authoring
    assert "runtime_cloud_dependency\": False" in authoring
    assert '"public_repository_asset_binaries": False' in authoring
    assert "raise\n    finally:\n        write_report(report)" in authoring
    assert "required_grooms = {\"hair\", \"eyebrows\"}" in capture
    assert "has_face_eyelash_material" in capture
    assert "wardrobe_mesh_count < 1" in capture
    assert "or missing_grooms" in capture
    assert "or not has_eyelash_representation" in capture
    assert "AutomationLibrary.finish_loading_before_screenshot()" in capture
    assert "portrait_target = visual_actor.get_solved_head_world_location()" in capture
    assert '"solved_head_world_cm"' in capture
    assert 'execute_console_command(world, "r.HairStrands.Strands 1")' in capture
    assert 'execute_console_command(world, "r.HairStrands.Cards 1")' in capture
    assert 'world, "r.HairStrands.UseCardsInsteadOfStrands 0"' in capture
    assert 'execute_console_command(world, "r.HairStrands.MinLOD 0")' in capture
    assert "actor.initialize_avatar_visual()" in capture
    assert "actor.configure_appearance(variant_index, 0, is_guide)" in capture
    assert "actor.get_production_visual_actor()" in capture
    assert "visual_actor.get_assembled_character_actor()" in capture
    assert "visual_actor.is_using_hair_mesh_fallback()" in capture
    assert "visual_actor.is_assembled_face_using_cropped_skin()" in capture
    assert '"runtime_assembled_face_uses_cropped_skin"' in capture
    assert "visual_actor.get_hair_mesh_fallback_head_error_cm() > 1.0" in capture
    assert "actor.get_production_helmet_head_error_cm() > 1.0" in capture
    assert '"runtime_helmet_head_error_cm"' in capture
    assert '"runtime_helmet_forward_alignment"' in capture
    assert '"runtime_helmet_fit_scale"' in capture
    assert 'f"{stem}_profile"' in capture
    assert 'f"{stem}_rear"' in capture
    assert '"profile_capture_sha256"' in capture
    assert '"rear_capture_sha256"' in capture
    assert "actor.has_layered_commercial_safety_gear()" in capture
    assert "origin.x + 430.0" in capture
    assert 'asset.get_editor_property("hair_groups_meshes")' in capture
    assert "runtime_hair_forced_lod != 5" in capture
    assert "raise\n    finally:\n        write_report(report)" in capture
    assert "request_auto_rigging" not in adapter
    assert "request_texture_sources" not in adapter
    assert "request_auto_rigging" not in host
    assert "request_texture_sources" not in host
    assert "unreal/Content/RaftSim/Characters/Authoring/MetaHumans/" in gitignore
    assert "unreal/Content/RaftSim/Characters/Production/MetaHumans/" in gitignore
    assert '"RaftSim.CreateOfflineMetaHumanSkinMaterial"' in builder
    assert "UMaterial* BuildOfflineMetaHumanSkinMaterial()" in material_authoring
    assert "MSM_PreintegratedSkin" in material_authoring
    assert "MATUSAGE_SkeletalMesh" in material_authoring
    assert "SkinMicroAlbedo" in material_authoring
    assert "SkinMicroNormal" in material_authoring
    assert "bHasFaceCropGraph" in material_authoring
    assert 'Expression->Desc == TEXT("RaftSimFaceCropMaterialAttributes")' in (
        material_authoring
    )


def test_cc0_assets_and_renderer_review_remain_fail_closed() -> None:
    for variant in ("Guide", "Crew01", "Crew02", "Crew03", "Crew04"):
        assert (CONTENT_ROOT / f"SK_RaftSim_CC0_{variant}.uasset").is_file()
        assert (CONTENT_ROOT / f"SK_RaftSim_CC0_{variant}_Skeleton.uasset").is_file()

    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    capture = REPO_ROOT / review["renderer_evidence"]["capture"]
    assert review["status"] == "technical_fallback_accepted_photoreal_art_rejected"
    assert review["renderer_evidence"]["result"] == "Success"
    assert review["renderer_evidence"]["human_approved"] is False
    assert review["named_art_reviewer"] is None
    assert review["unreal_import"]["unchanged_package_saves"] == 0
    assert review["automation_evidence"]["passed"] == 4
    assert review["automation_evidence"]["failed"] == 0
    assert _sha256(capture) == review["renderer_evidence"]["capture_sha256"]

def test_tapered_shoulder_sleeves_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(TAPERED_SHOULDER_REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["schema"] == "raftsim.m9.tapered_shoulder_sleeves_review.v2"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["named_character_art_reviewer"] is None
    assert review["named_guide_reviewer"] is None
    assert review["promotion_allowed"] is False
    assert review["supersedes"].endswith("m9_visible_shoulders_v1_review.json")

    metrics = review["runtime_roster_metrics"]
    assert metrics["captured_character_count"] == 5
    assert metrics["characters_with_visible_shoulder_silhouette"] == 5
    assert metrics["minimum_sleeve_vertex_count"] >= 550
    assert metrics["maximum_shoulder_anchor_error_cm"] <= 0.25
    roster_report = REPO_ROOT / metrics["report"]
    assert _sha256(roster_report) == metrics["report_sha256"]

    for item in review["renderer_evidence"]["captures"].values():
        capture = REPO_ROOT / item["capture"]
        assert _sha256(capture) == item["capture_sha256"]

    for source_relpath, expected_hash in review["implementation_sha256"].items():
        assert _sha256(REPO_ROOT / source_relpath) == expected_hash

    m5 = review["validation"]["m5"]
    m5_report = REPO_ROOT / m5["report"]
    assert _sha256(m5_report) == m5["report_sha256"]
    m5_payload = json.loads(m5_report.read_text(encoding="utf-8-sig"))
    assert m5_payload["succeeded"] == 1
    assert m5_payload["failed"] == 0
    assert m5_payload["tests"][0]["state"] == "Success"
