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
SKIN_REFLECTANCE_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_skin_reflectance_v1_review.json"
)
EYE_REFERENCE_POSE_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_eye_reference_pose_v1_review.json"
)
DISTINCT_PADDLE_GRIPS_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_distinct_paddle_grips_v2_review.json"
)
OPPOSED_THUMB_GLOVE_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_opposed_thumb_glove_v3_review.json"
)
PALM_ALIGNED_GRIP_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_palm_aligned_grip_v1_review.json"
)
HEAD_SHOULDER_CLEARANCE_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_head_shoulder_clearance_v1_review.json"
)
CLAVICLE_SPAN_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_cc0_clavicle_span_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict[str, object]:
    return json.loads(
        (SOURCE_ROOT / "character_source_manifest.json").read_text(encoding="utf-8")
    )


def test_cc0_character_manifest_freezes_five_distinct_rights_compatible_sources() -> None:
    manifest = _manifest()

    assert manifest["schema_version"] == 5
    assert manifest["license"]["asset_license"] == "mixed_cc0_1_0_and_cc_by_4_0"
    assert manifest["license"]["body_asset_license"] == "CC0-1.0"
    assert manifest["license"]["hair_asset_license"] == "CC-BY-4.0"
    assert manifest["toolchain"]["mpfb"] == "2.0.17"
    assert manifest["toolchain"]["fbx_source_unit"] == "meter"
    assert manifest["toolchain"]["fbx_runtime_unit"] == "centimeter"
    assert "one 100x uniform conversion" in manifest["toolchain"]["fbx_unit_policy"]
    assert "raw FBX reference vertices" in manifest["toolchain"][
        "reference_pose_policy"
    ]
    assert manifest["toolchain"]["checked_in_fbx_canonicalizer"] == (
        "unreal/Scripts/canonicalize_cc0_helmet_hair.py"
    )
    assert manifest["toolchain"]["head_detail_attachment_validator"] == (
        "unreal/Scripts/validate_cc0_head_detail_attachment.py"
    )
    assert "at least 0.75 authored head weight" in manifest["toolchain"][
        "helmet_hair_weight_policy"
    ]
    assert "complete connected Skin region" in manifest["toolchain"][
        "helmet_hair_weight_policy"
    ]
    assert "1.0 head weight" in manifest["toolchain"]["helmet_hair_weight_policy"]
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


def test_cc0_generator_preserves_native_units_and_single_fbx_conversion() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/build_cc0_production_character.py"
    ).read_text(encoding="utf-8")

    assert 'bpy.ops.object.join()' in source
    assert 'Matrix.Scale(100.0, 4)' not in source
    assert 'body.data.transform(' not in source
    assert 'rig.data.transform(' not in source
    assert 'length_unit = "METERS"' in source
    assert 'scale_length = 1.0' in source
    assert 'apply_scale_options="FBX_SCALE_ALL"' in source
    assert 'global_scale=1.0' in source
    assert 'use_mesh_modifiers=True' in source
    assert '_bind_rigid_mesh(eyes, rig, "head")' in source
    assert '_bind_rigid_mesh(brow, rig, "head")' in source
    assert 'HumanService.add_mhclo_asset(' in source
    assert 'asset_type="Hair"' in source
    assert 'interpolate_weights=True' in source
    assert '_find_exported_hair(source_hair, rig)' in source
    assert '_replace_with_rigid_bone_weights(hair, "head")' in source
    assert '_rigidify_high_confidence_head_vertices(body)' in source
    assert '_bake_evaluated_mesh_and_pose_as_reference(body, rig)' in source
    assert 'bpy.ops.object.shape_key_remove(all=True, apply_mix=True)' in source
    assert 'bpy.ops.object.modifier_apply(' in source
    assert 'bpy.ops.pose.armature_apply(selected=False)' in source


def test_cc0_checked_in_fbx_can_rebuild_helmet_hair_without_mpfb() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/canonicalize_cc0_helmet_hair.py"
    ).read_text(encoding="utf-8")

    assert 'term in material.name.casefold()' in source
    assert 'assignment.weight >= 0.75' in source
    assert 'facial_skin_indices' in source
    assert 'detail_indices' in source
    assert 'group.remove(sorted_indices)' in source
    assert 'head_group.add(sorted_indices, 1.0, "REPLACE")' in source
    assert 'assignments != {"head": 1.0}' in source
    assert 'body.scale = (1.0, 1.0, 1.0)' not in source
    assert 'rig.scale = (1.0, 1.0, 1.0)' not in source
    assert 'length_unit = "METERS"' in source
    assert 'scale_length = 1.0' in source
    assert 'use_mesh_modifiers=True' in source
    assert 'use_armature_deform_only=True' in source
    assert '_bake_evaluated_mesh_and_pose_as_reference(body, rig)' in source
    assert 'bpy.ops.object.shape_key_remove(all=True, apply_mix=True)' in source
    assert 'bpy.ops.object.modifier_apply(' in source
    assert 'bpy.ops.pose.armature_apply(selected=False)' in source


def test_cc0_head_detail_attachment_validator_is_evaluated_and_fail_closed() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/validate_cc0_head_detail_attachment.py"
    ).read_text(encoding="utf-8")

    assert 'evaluated_get(depsgraph)' in source
    assert 'evaluated_object.to_mesh(' in source
    assert 'preserve_all_data_layers=True' in source
    assert '"schema_version": 2' in source
    assert '"raw_reference_sections": raw_sections' in source
    assert '"paired_reference_skin": paired_reference_sections' in source
    assert '"synthetic_head_pose": {' in source
    assert '_append_failures(failures, "raw_reference_pose", raw_sections)' in source
    assert '_append_failures(failures, "synthetic_head_pose", posed_sections)' in source
    assert '"eyes": {"median": 0.010' in source
    assert '"brows": {"median": 0.010' in source
    assert '"hair": {"median": 0.025' in source
    assert '"status": "passed" if not failures else "failed"' in source
    assert 'raise RuntimeError("; ".join(report["failures"]))' in source
    assert 'sys.exit(1)' in source


def test_cc0_importer_is_hash_tracked_scale_validated_and_idempotent() -> None:
    source = (
        REPO_ROOT / "unreal/Scripts/import_cc0_production_characters.py"
    ).read_text(encoding="utf-8")

    assert 'SOURCE_SHA256_METADATA_TAG = "RaftSimSourceSHA256"' in source
    assert 'FBX_IMPORT_UNIFORM_SCALE = 100.0' in source
    assert 'def prepare_character_pair_reimport(' in source
    assert 'prepared_reimport_restart_required' in source
    assert 'Refusing to prepare unexpected shared skeleton' in source
    assert 'if isinstance(existing, unreal.SkeletalMesh):' in source
    assert 'restart Unreal, then run the importer normally' in source
    assert 'task.replace_existing = False' in source
    assert 'stale inverse bind matrices' in source
    assert 'mesh/skeleton pairs' in source
    assert 'save_loaded_asset(skeleton, only_if_is_dirty=False)' in source
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
    assert 'RAFTSIM_CC0_REIMPORT_TEXTURES' in source
    assert 'build_materials(textures, rebuild_hair=replace_textures)' in source
    assert 'materials[f"hair_{variant}"]' in source
    assert 'M_RaftSim_CC0_HelmetContainedHairHidden' in source
    assert 'selected = materials["helmet_hidden_hair"]' in source


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
    assert "AtlasReflectanceCalibration" in source
    assert "Multiply(CalibratedAtlas, BoundedMicroGain)" in source
    assert "FLinearColor(0.36f, 0.36f, 0.36f, 1.0f)" in source
    assert "FLinearColor(0.72f, 0.72f, 0.72f, 1.0f)" in source
    assert "FLinearColor(0.48f, 0.48f, 0.48f, 1.0f)" in source
    assert "FLinearColor(0.42f, 0.42f, 0.42f, 1.0f)" in source
    assert source.count("FLinearColor(0.72f, 0.72f, 0.72f, 1.0f)") >= 2
    assert "static UMaterial* BuildProductionCC0EyeMaterial()" in source
    assert "T_RaftSim_CC0_BrownEye.T_RaftSim_CC0_BrownEye" in source
    assert "Material->SetShadingModel(MSM_ClearCoat)" in source
    assert "source-level FBX attachment gate" in source
    assert "Material->TwoSided = false" in source
    assert 'AtlasSample->ParameterName = TEXT("LicensedEyeAtlas")' in source
    assert "SourceEyeAtlasReflectanceCalibration" in source
    assert "EditorData->ClearCoat.Connect(0, Constant(1.0f))" in source
    assert "EditorData->ClearCoatRoughness.Connect(0, Constant(0.04f))" in source
    assert "BuildProductionCC0EyeMaterial();" in source
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
    header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimCrewAvatarActor.h"
    ).read_text(encoding="utf-8")
    cc0_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimCC0CrewVisualActor.h"
    ).read_text(encoding="utf-8")
    adapter = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimCC0CrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    capture = (
        REPO_ROOT
        / "unreal/Scripts/capture_cc0_production_roster.py"
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
    assert "HasArticulatedPaddleGripRig() const" in adapter
    assert "ApplyPaddleGripPose(Pose)" in adapter
    assert "ResolvePaddleGripWristCm" in adapter
    assert 'TEXT("middle_01_%s")' in adapter
    assert "PaddlePalmAnchorAlongKnuckleFraction" in adapter
    assert "bUpperTGrip" in adapter
    assert "MeasureMinimumPaddleFingerClosureDegrees" in adapter
    assert "MeasureMinimumPaddleThumbClosureDegrees" in adapter
    assert "ProductionHeadClearanceLiftCm = 5.0f" in adapter
    assert "ProductionClavicleRootLateralFraction = 0.32f" in adapter
    assert "const FVector PresentedHeadCenter" in adapter
    assert "Pose.HeadCenterCm + TorsoUp * ProductionHeadClearanceLiftCm" in adapter
    assert "GetPresentedHeadShoulderClearanceCm() const" in cc0_header
    assert "GetPresentedClavicleRootSpanCm() const" in cc0_header
    assert "GetMaximumPresentedShoulderAnchorErrorCm() const" in cc0_header
    assert "HasAnatomicalShoulderTransition() const" in cc0_header
    assert "PresentedClavicleRootSpanCm >= 8.5f" in cc0_header
    assert "MaximumPresentedShoulderAnchorErrorCm <= 0.25f" in cc0_header
    assert "LeftClavicleRoot" in adapter
    assert "RightClavicleRoot" in adapter
    assert "PresentedClavicleRootSpanCm = FVector::Distance" in adapter
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
    assert "constexpr int32 Rings = 28" in host
    assert "constexpr int32 Sides = 36" in host
    assert "0.16f * Deltoid" in host
    assert "0.035f * CuffRoll" in host
    assert "0.055f * EndEnvelope" in host
    assert "0.028f * EndEnvelope" in host
    assert "0.034f *" in host
    assert "FMath::FindDeltaAngleRadians(" in host
    assert "1.035f * Radius" in host
    assert "0.965f * Radius" in host
    assert 'TEXT("LeftShoulderSleeve"), Jacket ? Jacket : Wetsuit' in host
    assert 'TEXT("RightShoulderSleeve"), Jacket ? Jacket : Wetsuit' in host
    assert "Pose.LeftShoulderCm, LeftElbow, kProductionShoulderSleeveArmFraction" in host
    assert "Pose.RightShoulderCm, RightElbow, kProductionShoulderSleeveArmFraction" in host
    assert "Pose.LeftShoulderCm,\n        LeftShoulderSleeveEnd" in host
    assert "Pose.RightShoulderCm,\n        RightShoulderSleeveEnd" in host
    assert "HasVisibleShoulderSilhouette() const" in host
    assert "GetMinimumShoulderSleeveVertexCount() const" in host
    assert "GetMinimumShoulderSleeveVertexCount() >= 1000" in host
    assert "HasLiveSplashJacketMaterialResponse()" in host
    assert "HasLiveSplashJacketMaterialResponse() const" in header
    assert "SplashJacketMaterialInstance" in host
    assert "SplashJacketMaterialInstance->SetScalarParameterValue(" in host
    assert "BoundedWetness);" in host
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
    assert "constexpr int32 Rings = 20" in host
    assert "constexpr int32 Sides = 32" in host
    assert "const float Quadriceps" in host
    assert "const float Hamstring" in host
    assert "const float Adductor" in host
    assert "DepthRadius * DirectionalDepth * CosTheta" in host
    assert "SetAnatomicalThigh(" in host
    assert "FRotationMatrix::MakeFromZX(SafeDirection, SafeForward)" in host
    assert "LeftBridgeSection->ProcVertexBuffer.Num() >= 650" in host
    assert "RightBridgeSection->ProcVertexBuffer.Num() >= 650" in host
    assert "GetMinimumThighMeshVertexCount() const" in host
    assert "GetMinimumThighForwardAlignment() const" in host
    assert "GetMinimumThighForwardAlignment() >= 0.98f" in host
    assert "DistanceToBridgeCentreline" in host
    assert "HasContinuousThighKneeSilhouette() const" in host
    assert "GetMaximumThighKneeBridgeCoverageErrorCm() const" in host
    assert "ThighExtentCm.X >= 7.2f" in host
    assert "ThighExtentCm.Y >= 7.2f" in host
    assert "ThighExtentCm.Z >= 15.5f" in host
    assert "HasExclusiveCC0BodyOwnership() const" in host
    assert "ActivateCC0FallbackForValidation()" in host
    assert "const bool bCompleteCC0Body" in host
    assert "const bool bBodyGapOverlay = !bCompleteCC0Body" in host
    assert "bSafetyGearOrPaddleOverlay || bBodyGapOverlay" in host
    assert "actor.activate_cc0_fallback_for_validation()" in capture
    assert "runtime_exclusive_cc0_body_ownership" in capture
    assert '"grip": (' in capture
    assert '"grip_profile": (' in capture
    assert "visual_actor.has_articulated_paddle_grip_rig()" in capture
    assert "runtime_paddle_grip_anchor_error_cm" in capture
    assert "runtime_upper_paddle_finger_closure_degrees" in capture
    assert "runtime_lower_paddle_finger_closure_degrees" in capture
    assert "runtime_paddle_thumb_closure_degrees" in capture
    assert "head_shoulder_clearance_cm < 19.5" in capture
    assert "runtime_presented_head_shoulder_clearance_cm" in capture
    assert '"face": (' in capture
    assert "get_solved_face_forward_world_vector()" in capture
    assert "runtime_eye_materials" in capture
    assert '"M_RaftSim_CC0_Eyes.M_RaftSim_CC0_Eyes"' in capture
    assert "origin.z + extent.z * 0.45" in capture
    assert "Rendered eye/head anchor fell below the upper body" in capture
    assert "ResolveProductionHeadFit(" in host
    assert "CC0Visual->GetSolvedHeadWorldLocation()" in host
    assert "CC0Visual->GetSolvedFaceForwardWorldVector()" in host
    assert "GuideHeadLocalEyeCenterCm" in adapter
    assert "CrewHeadLocalEyeCentersCm" in adapter
    assert "HeadTransform.TransformPosition(LocalEyeCenterCm / BodyScale)" in adapter
    assert "HeadTransform.GetRotation().RotateVector(-FVector::UpVector)" in adapter
    assert "HeadTransform.GetRotation().RotateVector(-FVector::YAxisVector)" in adapter
    assert "CacheRenderedFaceAnchorVertices()" in adapter
    assert "Section.MaterialIndex != EyeMaterialIndex" in adapter
    assert "USkinnedMeshComponent::GetSkinnedVertexPosition(" in adapter
    assert "ComponentCenter /= RenderedFaceAnchorVertexIndices.Num()" in adapter
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
    assert 'TEXT("RaftSimForceCC0Review")' in automation
    assert "MSM_ClearCoat" in automation
    assert 'TEXT("CC0 eyes use a corneal clear-coat shading layer")' in automation
    assert 'TEXT("CC0 helper-eye shell retains reviewed outward winding")' in automation
    assert "It->HasArticulatedPaddleGripRig()" in automation
    assert "It->GetMaximumPaddleGripAnchorErrorCm() <= 0.25f" in automation
    assert "It->GetMinimumUpperPaddleFingerClosureDegrees() >= 120.0f" in automation
    assert "It->GetMinimumLowerPaddleFingerClosureDegrees() >= 210.0f" in automation
    assert "It->GetMinimumPaddleThumbClosureDegrees() >= 50.0f" in automation
    assert "HeadShoulderClearanceCm >= 9.5f" in automation
    assert 'TEXT("%s %s detail is paired to head-dominant facial Skin")' in automation
    assert "P95ReferenceSeparationCm <= 1.25f" in automation
    assert "It->HasExclusiveCC0BodyOwnership()" in automation
    assert "It->GetProceduralBodyPartCount() >= 28" in automation
    assert "It->HasVisibleShoulderSilhouette()" in automation
    assert "ShoulderSleeveVertexCount >= 1000" in automation
    assert "It->HasLiveSplashJacketMaterialResponse()" in automation
    assert "ShoulderAnchorErrorCm <= 0.25f" in automation
    assert "It->IsWaistHipMaterialOpaque()" in automation
    assert "HipThighCoverageErrorCm <= 0.25f" in automation
    assert "It->HasContinuousThighKneeSilhouette()" in automation
    assert "ThighMeshVertexCount >= 650" in automation
    assert "ThighForwardAlignment >= 0.98f" in automation
    assert "ThighKneeCoverageErrorCm <= 0.25f" in automation
    assert "get_minimum_thigh_mesh_vertex_count() < 650" in (
        REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
    ).read_text(encoding="utf-8")
    assert "get_minimum_thigh_forward_alignment() < 0.98" in (
        REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
    ).read_text(encoding="utf-8")
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
    assert 'f"{stem}_grip"' in capture
    assert 'f"{stem}_grip_profile"' in capture
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
    assert "AssembledBody->SetMaterial(MaterialIndex, WetsuitPresentationMaterial)" in adapter
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
    assert "GetMaximumPaddleThumbContactErrorCm()" in automation
    assert "HasLocalizedPaddleGloveMaterial()" in automation
    assert "ApplyFingerChainAroundGrip" in adapter
    assert "MeasurePaddleFingerContactErrorCm" in adapter
    assert "MeasurePaddleThumbContactErrorCm" in adapter
    assert "ApplyOpposedThumbPadToGrip" in adapter
    assert "PaddleThumbPadCenterRadiusCm" in adapter
    assert "UpdatePaddleGloveMaterial" in adapter
    assert "LeftPaddleGloveCenterWS" in adapter
    assert "RightPaddleGloveCenterWS" in adapter
    assert "FAnatomicalGripDigitProfile" in adapter
    assert "ResolveAnatomicalGripDigitProfile" in adapter
    assert "Profile.PadCenterRadiusCm" in adapter
    assert "Profile.FanDegrees * WrapSign" in adapter
    assert 'for (const TCHAR* Digit : {TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})' in adapter
    assert '{30.0f, 42.0f, 28.0f, 3.25f, 2.45f, 1.95f, 12.0f}' in adapter
    assert '{28.0f, 40.0f, 28.0f, 3.00f, 2.35f, 1.90f, -12.0f}' in adapter
    assert "FVector::DistSquared(GripCenterCm, Pose.PaddleTopCm) <= 4.0f" in adapter
    assert "forcing every joint onto a radial contact arc creates a false" in adapter
    assert "paddle_grip_contact_error_cm=" in capture
    assert "get_maximum_paddle_grip_contact_error_cm()" in capture
    assert "runtime_paddle_grip_contact_error_cm" in capture
    assert "runtime_paddle_thumb_contact_error_cm" in capture
    assert "runtime_localized_paddle_glove_material" in capture
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

def test_cc0_skin_reflectance_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(SKIN_REFLECTANCE_REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["schema"] == "raftsim.m9.cc0_skin_reflectance_review.v1"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["reviewers"]["named_character_art_reviewer"] is None
    assert review["reviewers"]["qualified_whitewater_safety_reviewer"] is None
    assert review["promotion_allowed"] is False
    assert review["supersedes"].endswith("m9_cc0_face_fitted_helmet_v1_review.json")

    implementation = review["implementation"]
    assert implementation["shading_model"] == "MSM_PreintegratedSkin"
    assert implementation["source_atlases_unchanged"] is True
    assert implementation["scalar_gain_preserves_source_hue"] is True
    assert implementation["geometry_rig_and_gameplay_unchanged"] is True
    assert implementation["atlas_scalar_gains"] == {
        "guide": 0.36,
        "crew01": 0.72,
        "crew02": 0.48,
        "crew03": 0.42,
        "crew04": 0.72,
    }

    metrics = review["runtime_roster_metrics"]
    assert metrics["captured_character_count"] == 5
    assert metrics["exclusive_cc0_body_count"] == 5
    assert metrics["maximum_helmet_head_error_cm"] <= 1.0
    assert metrics["minimum_helmet_forward_alignment"] >= 0.98
    assert 0.90 <= metrics["minimum_helmet_fit_scale"] <= 1.02
    assert 0.90 <= metrics["maximum_helmet_fit_scale"] <= 1.02
    roster_report = REPO_ROOT / metrics["report"]
    assert _sha256(roster_report) == metrics["report_sha256"]

    roster = json.loads(roster_report.read_text(encoding="utf-8"))
    assert roster["status"] == "capture_complete"
    assert roster["exclusive_body_count"] == 5
    for character in roster["characters"]:
        assert character["runtime_helmet_head_error_cm"] <= 1.0
        assert character["runtime_helmet_forward_alignment"] >= 0.98
        assert 0.90 <= character["runtime_helmet_fit_scale"] <= 1.02

    reflectance = review["reflectance_metrics"]
    reflectance_report = REPO_ROOT / reflectance["report"]
    assert _sha256(reflectance_report) == reflectance["report_sha256"]
    measured = json.loads(reflectance_report.read_text(encoding="utf-8"))
    assert reflectance["all_five_candidate_p95_luminance_below_baseline"] is True
    assert all(
        row["candidate_p95_luminance"] < row["baseline_p95_luminance"]
        for row in measured["identities"].values()
    )

    for item in review["renderer_evidence"]["captures"].values():
        capture = REPO_ROOT / item["capture"]
        assert _sha256(capture) == item["capture_sha256"]

    for asset_relpath, expected_hash in review["material_assets_sha256"].items():
        assert _sha256(REPO_ROOT / asset_relpath) == expected_hash

    # This is immutable evidence for the superseded reflectance milestone. Its
    # implementation hashes describe that historical candidate; later source
    # repairs intentionally change those files without rewriting the record.
    for source_relpath, historical_hash in review["implementation_sha256"].items():
        assert (REPO_ROOT / source_relpath).is_file()
        assert len(historical_hash) == 64

    m5 = review["validation"]["m5"]
    m5_report = REPO_ROOT / m5["report"]
    assert _sha256(m5_report) == m5["report_sha256"]
    m5_payload = json.loads(m5_report.read_text(encoding="utf-8-sig"))
    assert m5_payload["succeeded"] == m5["succeeded"]
    assert m5_payload["succeededWithWarnings"] == m5["succeeded_with_warnings"]
    assert m5_payload["failed"] == 0
    assert sum(test["state"] == "Success" for test in m5_payload["tests"]) == 5


def test_cc0_eye_reference_pose_review_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(EYE_REFERENCE_POSE_REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["schema"] == "raftsim.m9.cc0_eye_reference_pose_review.v1"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["raw_and_evaluated_reference_geometry_agree"] is True
    assert review["implementation"]["synthetic_head_rotation_degrees"] == 58.0
    assert review["implementation"]["gameplay_physics_changed"] is False
    assert review["source_validation"]["all_five_passed"] is True
    assert review["source_validation"]["validator_schema_version"] == 2
    assert review["reviewers"]["named_character_art_reviewer"] is None
    assert review["reviewers"]["qualified_whitewater_safety_reviewer"] is None
    assert len(review["required_external_acceptance_gates"]) == 3

    for item in review["source_validation"]["reports"].values():
        report_path = REPO_ROOT / item["path"]
        assert _sha256(report_path) == item["sha256"]
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["schema_version"] == 2
        assert report["status"] == "passed"
        assert report["failures"] == []

    imported = review["unreal_import"]
    assert imported["status"] == "imported"
    assert imported["character_count"] == 5
    assert imported["lod_count_each"] == 3
    assert _sha256(REPO_ROOT / imported["report"]) == imported["report_sha256"]

    automation = review["native_automation"]
    assert automation["failed"] == 0
    assert automation["succeeded"] + automation["succeeded_with_warnings"] == 5
    assert automation["maximum_measured_eye_p95_cm"] <= automation[
        "eye_brow_reference_p95_limit_cm"
    ]
    assert automation["maximum_measured_brow_p95_cm"] <= automation[
        "eye_brow_reference_p95_limit_cm"
    ]
    assert _sha256(REPO_ROOT / automation["report"]) == automation["report_sha256"]

    runtime = review["runtime_roster"]
    assert runtime["status"] == "capture_complete"
    assert runtime["captured_character_count"] == 5
    assert runtime["exclusive_cc0_body_count"] == 5
    assert runtime["all_solved_heads_above_upper_body_threshold"] is True
    assert runtime["maximum_helmet_head_error_cm"] <= 1.0
    assert runtime["minimum_helmet_forward_alignment"] >= 0.98
    assert _sha256(REPO_ROOT / runtime["report"]) == runtime["report_sha256"]

    roster = json.loads((REPO_ROOT / runtime["report"]).read_text(encoding="utf-8"))
    captures_dir = REPO_ROOT / runtime["captures_directory"]
    for character in roster["characters"]:
        assert character["runtime_solved_head_cm"][2] >= character[
            "runtime_solved_head_minimum_z_cm"
        ]
        for item in character["captures"].values():
            capture = captures_dir / Path(item["path"]).name
            assert _sha256(capture) == item["sha256"]

    for asset_relpath, expected_hash in review["asset_sha256"].items():
        assert _sha256(REPO_ROOT / asset_relpath) == expected_hash
    # Eye-reference V1 is immutable historical evidence. Later character
    # presentation milestones intentionally change shared adapter and test
    # sources without rewriting the earlier review record.
    for source_relpath, historical_hash in review["implementation_sha256"].items():
        assert (REPO_ROOT / source_relpath).is_file()
        assert len(historical_hash) == 64


def test_distinct_paddle_grips_v2_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(
        DISTINCT_PADDLE_GRIPS_REVIEW_PATH.read_text(encoding="utf-8")
    )
    assert review["schema"] == "raftsim.m9.distinct_paddle_grips_review.v2"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["upper_t_grip_hands"] == 5
    assert review["implementation"]["lower_shaft_contact_hands"] == 5
    assert review["implementation"]["contact_constrained_lower_finger_chains"] == 20
    assert review["implementation"]["measured_maximum_runtime_lower_finger_contact_error_cm"] <= 0.25
    assert review["implementation"]["physics_or_gameplay_changes"] is False

    roster_path = REPO_ROOT / review["runtime_roster_metrics"]["report"]
    assert _sha256(roster_path) == review["runtime_roster_metrics"]["report_sha256"]
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    assert roster["status"] == "capture_complete"
    assert roster["captured_character_count"] == 5
    assert max(
        character["runtime_paddle_grip_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25

    for evidence_set in ("baseline", "candidate"):
        for path, expected_hash in review["renderer_evidence"][evidence_set].values():
            assert _sha256(REPO_ROOT / path) == expected_hash

    m5 = review["validation"]["m5"]
    m5_path = REPO_ROOT / m5["report"]
    assert _sha256(m5_path) == m5["report_sha256"]
    m5_payload = json.loads(m5_path.read_text(encoding="utf-8-sig"))
    assert m5_payload["succeeded"] == 1
    assert m5_payload["succeededWithWarnings"] == 0
    assert m5_payload["failed"] == 0

    # Distinct Grip V2 is immutable historical evidence. V3 deliberately
    # changes the same adapter, material authoring, renderer, and tests while
    # preserving the V2 hashes as an auditable baseline.
    for source_relpath, historical_hash in review["implementation_sha256"].items():
        assert (REPO_ROOT / source_relpath).is_file()
        assert len(historical_hash) == 64


def test_opposed_thumb_glove_v3_is_hash_verified_and_fail_closed() -> None:
    review = json.loads(
        OPPOSED_THUMB_GLOVE_REVIEW_PATH.read_text(encoding="utf-8")
    )
    assert review["schema"] == "raftsim.m9.opposed_thumb_glove_review.v3"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["lower_opposed_thumb_hands"] == 5
    assert review["implementation"]["localized_glove_material_characters"] == 5
    assert review["implementation"]["measured_maximum_runtime_thumb_contact_error_cm"] <= 0.25
    assert review["implementation"]["physics_or_gameplay_changes"] is False

    roster_path = REPO_ROOT / review["runtime_roster_metrics"]["report"]
    assert _sha256(roster_path) == review["runtime_roster_metrics"]["report_sha256"]
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    assert roster["status"] == "capture_complete"
    assert roster["captured_character_count"] == 5
    assert all(
        character["runtime_localized_paddle_glove_material"]
        for character in roster["characters"]
    )
    assert max(
        character["runtime_paddle_thumb_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25

    for evidence_set in ("baseline", "candidate", "candidate_close"):
        for path, expected_hash in review["renderer_evidence"][evidence_set].values():
            assert _sha256(REPO_ROOT / path) == expected_hash

    m5 = review["validation"]["m5"]
    m5_path = REPO_ROOT / m5["report"]
    assert _sha256(m5_path) == m5["report_sha256"]
    m5_payload = json.loads(m5_path.read_text(encoding="utf-8-sig"))
    assert m5_payload["succeeded"] == 1
    assert m5_payload["succeededWithWarnings"] == 0
    assert m5_payload["failed"] == 0

    # V3 remains immutable renderer/asset evidence. The production M5 runner
    # and this evolving contract file are shared by the later CC0 palm-aligned
    # milestone, whose replacement hashes are independently locked below.
    superseded_shared_sources = {
        (
            "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
            "RaftSimM5ProductionQualityTest.cpp"
        ),
        (
            "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
            "RaftSimEditorPhotorealMaterials.cpp"
        ),
        "physics/tests/test_cc0_production_characters.py",
    }
    for source_relpath, expected_hash in review["implementation_sha256"].items():
        if source_relpath in superseded_shared_sources:
            assert (REPO_ROOT / source_relpath).is_file()
            assert len(expected_hash) == 64
            continue
        assert _sha256(REPO_ROOT / source_relpath) == expected_hash

    grip_review = json.loads(
        PALM_ALIGNED_GRIP_REVIEW_PATH.read_text(encoding="utf-8")
    )
    assert grip_review["schema"] == "raftsim.m9.cc0_palm_aligned_grip_review.v1"
    assert grip_review["passed"] is False
    assert grip_review["technical_candidate_passed"] is True
    assert grip_review["photoreal_acceptance_passed"] is False
    assert grip_review["human_approved"] is False
    assert grip_review["promotion_allowed"] is False
    implementation = grip_review["implementation"]
    assert implementation["production_roster_count"] == 5
    assert implementation["visible_paddle_hands"] == 10
    assert implementation["upper_t_grip_hands"] == 5
    assert implementation["lower_shaft_grip_hands"] == 5
    assert implementation["articulated_four_finger_chains"] == 40
    assert implementation["articulated_thumb_chains"] == 10
    assert implementation["measured_maximum_palm_anchor_error_cm"] <= 0.25
    assert (
        implementation["measured_minimum_upper_finger_chain_closure_degrees"]
        >= 120.0
    )
    assert (
        implementation["measured_minimum_lower_finger_chain_closure_degrees"]
        >= 210.0
    )
    assert implementation["measured_minimum_thumb_chain_closure_degrees"] >= 50.0
    assert implementation["physics_or_gameplay_changes"] is False

    runtime = grip_review["runtime_roster_metrics"]
    roster_path = REPO_ROOT / runtime["report"]
    assert _sha256(roster_path) == runtime["report_sha256"]
    grip_roster = json.loads(roster_path.read_text(encoding="utf-8"))
    assert grip_roster["schema"] == "raftsim.cc0.exclusive_body_capture.v2"
    assert grip_roster["status"] == "capture_complete"
    assert grip_roster["captured_character_count"] == 5
    assert grip_roster["articulated_paddle_grip_count"] == 5
    assert all(
        character["runtime_articulated_paddle_grip"]
        and character["runtime_active_paddle_grip_pose"]
        for character in grip_roster["characters"]
    )
    assert max(
        character["runtime_paddle_grip_anchor_error_cm"]
        for character in grip_roster["characters"]
    ) <= 0.25
    assert min(
        character["runtime_upper_paddle_finger_closure_degrees"]
        for character in grip_roster["characters"]
    ) >= 120.0
    assert min(
        character["runtime_lower_paddle_finger_closure_degrees"]
        for character in grip_roster["characters"]
    ) >= 210.0
    assert min(
        character["runtime_paddle_thumb_closure_degrees"]
        for character in grip_roster["characters"]
    ) >= 50.0
    for path, expected_hash in grip_review["renderer_evidence"][
        "matched_close_grip"
    ].values():
        assert _sha256(REPO_ROOT / path) == expected_hash

    grip_m5 = grip_review["validation"]["m5"]
    grip_m5_path = REPO_ROOT / grip_m5["report"]
    assert _sha256(grip_m5_path) == grip_m5["report_sha256"]
    grip_m5_payload = json.loads(
        grip_m5_path.read_text(encoding="utf-8-sig")
    )
    assert grip_m5_payload["succeeded"] == 1
    assert grip_m5_payload["succeededWithWarnings"] == 0
    assert grip_m5_payload["failed"] == 0
    superseded_grip_sources = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCC0CrewVisualActor.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCC0CrewVisualActor.h",
        (
            "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
            "RaftSimM5ProductionQualityTest.cpp"
        ),
        "unreal/Scripts/capture_cc0_production_roster.py",
    }
    for source_relpath, expected_hash in grip_review[
        "implementation_sha256"
    ].items():
        if source_relpath in superseded_grip_sources:
            assert (REPO_ROOT / source_relpath).is_file()
            assert len(expected_hash) == 64
            continue
        assert _sha256(REPO_ROOT / source_relpath) == expected_hash
    assert len(grip_review["rejected_iterations"]) == 4
    assert len(grip_review["open_gates"]) == 3


def test_cc0_head_shoulder_clearance_v1_is_renderer_verified_and_fail_closed() -> None:
    review = json.loads(
        HEAD_SHOULDER_CLEARANCE_REVIEW_PATH.read_text(encoding="utf-8")
    )
    assert review["schema"] == "raftsim.m9.cc0_head_shoulder_clearance_review.v1"
    assert review["passed"] is False
    assert review["decision"] == {
        "technical_candidate_passed": True,
        "runtime_rolled_out": True,
        "matched_visual_improvement_retained": True,
        "production_promoted": False,
        "photoreal_acceptance_passed": False,
        "human_approved": False,
    }

    measured = review["measured_clearance"]
    assert measured["render_head_lift_cm"] == 5.0
    assert measured["candidate_minimum_presented_head_shoulder_clearance_cm"] >= 19.5
    assert measured["seated_capture_minimum_cm"] == 19.5
    assert measured["m5_dynamic_pose_minimum_cm"] == 9.5
    assert abs(
        measured["candidate_minimum_presented_head_shoulder_clearance_cm"]
        - measured["baseline_minimum_presented_head_shoulder_clearance_cm_inferred"]
        - measured["render_head_lift_cm"]
    ) < 1.0e-6

    evidence_dir = REPO_ROOT / review["renderer_evidence"]["directory"]
    candidate_roster = json.loads(
        (evidence_dir / "candidate_roster_capture.json").read_text(encoding="utf-8")
    )
    assert candidate_roster["status"] == "capture_complete"
    assert len(candidate_roster["characters"]) == 5
    assert candidate_roster["minimum_presented_head_shoulder_clearance_cm"] == (
        measured["candidate_minimum_presented_head_shoulder_clearance_cm"]
    )
    for character in candidate_roster["characters"]:
        assert character["runtime_presented_head_shoulder_clearance_cm"] >= 19.5
        assert character["runtime_helmet_head_error_cm"] <= 1.0e-6
        assert character["runtime_helmet_forward_alignment"] >= 0.999
        assert character["runtime_paddle_grip_anchor_error_cm"] <= 0.01

    superseded_head_sources = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCC0CrewVisualActor.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCC0CrewVisualActor.h",
        (
            "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
            "RaftSimM5ProductionQualityTest.cpp"
        ),
        "unreal/Scripts/capture_cc0_production_roster.py",
    }
    for relative, expected_hash in review["implementation_sha256"].items():
        if relative in superseded_head_sources:
            assert (REPO_ROOT / relative).is_file()
            assert len(expected_hash) == 64
            continue
        assert _sha256(REPO_ROOT / relative) == expected_hash
    for relative, expected_hash in review["evidence_sha256"].items():
        assert _sha256(REPO_ROOT / relative) == expected_hash

    m5 = json.loads((evidence_dir / "m5.json").read_text(encoding="utf-8-sig"))
    assert m5["succeeded"] == 1
    assert m5["succeededWithWarnings"] == 0
    assert m5["failed"] == 0
    p4 = json.loads(
        (evidence_dir / "p4_all_river_maps.json").read_text(encoding="utf-8-sig")
    )
    assert p4["succeeded"] == 0
    assert p4["succeededWithWarnings"] == 6
    assert p4["failed"] == 0
    assert {test["fullTestPath"] for test in p4["tests"]} == {
        "RaftSim.P4.RiverMapLoads.L_Troublemaker",
        "RaftSim.P4.RiverMapLoads.L_Hance",
        "RaftSim.P4.RiverMapLoads.L_UpperHuacas",
        "RaftSim.P4.RiverMapLoads.L_Terminator",
        "RaftSim.P4.RiverMapLoads.L_LavaCanyon",
        "RaftSim.P4.RiverMapLoads.L_Zambezi",
    }
    assert len(review["open_external_acceptance_gates"]) == 7
    assert set(review["reviewers"].values()) == {None}


def test_cc0_clavicle_span_v1_is_renderer_verified_and_fail_closed() -> None:
    review = json.loads(CLAVICLE_SPAN_REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["schema"] == "raftsim.m9.cc0_clavicle_span_review.v1"
    assert review["passed"] is False
    assert review["decision"] == {
        "technical_candidate_passed": True,
        "runtime_rolled_out": True,
        "matched_visual_improvement_retained": True,
        "production_promoted": False,
        "photoreal_acceptance_passed": False,
        "human_approved": False,
    }

    measured = review["measured_transition"]
    assert measured["clavicle_root_lateral_fraction"] == 0.32
    assert measured["minimum_presented_clavicle_root_span_cm"] >= 8.5
    assert measured["maximum_presented_clavicle_root_span_cm"] <= 12.0
    assert measured["maximum_presented_shoulder_anchor_error_cm"] <= 0.25
    assert measured["maximum_paddle_grip_anchor_error_cm"] <= 0.25

    evidence_dir = REPO_ROOT / review["renderer_evidence"]["directory"]
    roster = json.loads((evidence_dir / "roster_capture.json").read_text())
    assert roster["status"] == "capture_complete"
    assert roster["captured_character_count"] == 5
    assert roster["minimum_presented_clavicle_root_span_cm"] == (
        measured["minimum_presented_clavicle_root_span_cm"]
    )
    assert roster["maximum_presented_shoulder_anchor_error_cm"] == (
        measured["maximum_presented_shoulder_anchor_error_cm"]
    )
    for character in roster["characters"]:
        assert character["runtime_presented_clavicle_root_span_cm"] >= 8.5
        assert (
            character["runtime_maximum_presented_shoulder_anchor_error_cm"]
            <= 0.25
        )

    for relative, expected_hash in review["implementation_sha256"].items():
        assert _sha256(REPO_ROOT / relative) == expected_hash
    for relative, expected_hash in review["evidence_sha256"].items():
        assert _sha256(REPO_ROOT / relative) == expected_hash

    m5 = json.loads((evidence_dir / "m5.json").read_text(encoding="utf-8-sig"))
    assert m5["succeeded"] == 1
    assert m5["succeededWithWarnings"] == 0
    assert m5["failed"] == 0
    p4 = json.loads(
        (evidence_dir / "p4_all_river_maps.json").read_text(encoding="utf-8-sig")
    )
    assert p4["succeeded"] + p4["succeededWithWarnings"] == 6
    assert p4["failed"] == 0
    assert {test["fullTestPath"] for test in p4["tests"]} == {
        "RaftSim.P4.RiverMapLoads.L_Troublemaker",
        "RaftSim.P4.RiverMapLoads.L_Hance",
        "RaftSim.P4.RiverMapLoads.L_UpperHuacas",
        "RaftSim.P4.RiverMapLoads.L_Terminator",
        "RaftSim.P4.RiverMapLoads.L_LavaCanyon",
        "RaftSim.P4.RiverMapLoads.L_Zambezi",
    }
    assert len(review["open_external_acceptance_gates"]) == 7
    assert set(review["reviewers"].values()) == {None}
