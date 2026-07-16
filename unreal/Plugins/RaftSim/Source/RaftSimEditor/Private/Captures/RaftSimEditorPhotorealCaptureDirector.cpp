#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

bool FRaftSimEditorModule::CapturePhotorealEnvironmentPreviews(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString CaptureRoot = GetEnvironmentCaptureRoot();
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    const FString SourcePlanRelativePath = GetPhotorealRiverSourcePlanRelativePath();
    const FString ProceduralAssetPlanRelativePath = GetFirstPartyProceduralEnvironmentAssetPlanRelativePath();
    const FString ProceduralAssetPlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralAssetPlanRelativePath));
    const FString ProceduralMaterialRecipePlanRelativePath = GetFirstPartyProceduralMaterialRecipePlanRelativePath();
    const FString ProceduralMaterialRecipePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralMaterialRecipePlanRelativePath));
    const FString MaterialTextureAtlasManifestRelativePath = GetFirstPartyMaterialTextureAtlasManifestRelativePath();
    const FString MaterialTextureAtlasManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialTextureAtlasManifestRelativePath));
    const FString SourceConditionedMaterialMapManifestRelativePath = GetSourceConditionedMaterialMapManifestRelativePath();
    const FString SourceConditionedMaterialMapManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourceConditionedMaterialMapManifestRelativePath));
    const FString ProductionDetailTextureManifestRelativePath = GetProductionDetailTextureManifestRelativePath();
    const FString ProductionDetailTextureManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProductionDetailTextureManifestRelativePath));
    const FString MaterialInstanceCandidateManifestRelativePath = GetFirstPartyMaterialInstanceCandidateManifestRelativePath();
    const FString MaterialInstanceCandidateManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialInstanceCandidateManifestRelativePath));
    const FString MaterialTextureAssetRootRelativePath = GetFirstPartyMaterialTextureAssetRootRelativePath();
    const FString SourceConditionedMaterialTextureAssetRootRelativePath =
        GetSourceConditionedMaterialTextureAssetRootRelativePath();
    const FString ProductionDetailTextureAssetRootRelativePath = GetProductionDetailTextureAssetRootRelativePath();
    const FString MaterialShaderParentRelativePath = GetFirstPartyAtlasSampleReviewMaterialRelativePath();
    const FString MaterialInstanceReviewAssetRootRelativePath = GetFirstPartyMaterialInstanceReviewAssetRootRelativePath();
    const FString GeospatialAttachmentLedgerRelativePath = GetProductionGeospatialAttachmentLedgerRelativePath();
    const FString GeospatialAttachmentLedgerAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), GeospatialAttachmentLedgerRelativePath));

    if (!FPaths::FileExists(ProceduralAssetPlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural environment asset plan for capture: %s\n"), *ProceduralAssetPlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralMaterialRecipePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural material recipe plan for capture: %s\n"), *ProceduralMaterialRecipePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialTextureAtlasManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material texture atlas manifest for capture: %s\n"), *MaterialTextureAtlasManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(SourceConditionedMaterialMapManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing source-conditioned material map manifest for capture: %s\n"),
            *SourceConditionedMaterialMapManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProductionDetailTextureManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing first-party production detail texture manifest for capture: %s\n"),
            *ProductionDetailTextureManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialInstanceCandidateManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material instance candidate manifest for capture: %s\n"), *MaterialInstanceCandidateManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger for capture: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }
    OutSummary += FString::Printf(TEXT("Using first-party material texture atlas manifest: %s\n"), *MaterialTextureAtlasManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material map manifest: %s\n"),
        *SourceConditionedMaterialMapManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture manifest: %s\n"),
        *ProductionDetailTextureManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance candidate manifest: %s\n"), *MaterialInstanceCandidateManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material texture asset root: %s\n"), *MaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material texture asset root: %s\n"),
        *SourceConditionedMaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture asset root: %s\n"),
        *ProductionDetailTextureAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party atlas sampler review material: %s\n"), *MaterialShaderParentRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance review asset root: %s\n"), *MaterialInstanceReviewAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerRelativePath);

    FString EntriesJson;
    bool bAllCaptured = true;
    const bool bCullReviewOnlyForegroundRaftForGuideSeatCaptures = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> Specs = GetEnvironmentPreviewSpecs();
    for (int32 Index = 0; Index < Specs.Num(); ++Index)
    {
        const FRaftSimEnvironmentPreviewSpec& Spec = Specs[Index];
        const FRaftSimPreviewWaterMaterialResponse WaterResponse = GetPreviewWaterMaterialResponse(Spec.RiverId);
        FString GuideSeatCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("guide_seat_downstream"));
        FString RiverEyeCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("river_eye_downstream"));
        const bool bGuideSeatCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("guide_seat_downstream"),
            TEXT("guide-seat downstream"),
            bCullReviewOnlyForegroundRaftForGuideSeatCaptures,
            OutSummary);
        const bool bRiverEyeCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            RiverEyeCapturePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            TEXT("river_eye_downstream"),
            TEXT("river-eye downstream"),
            true,
            OutSummary);
        bAllCaptured &= bGuideSeatCaptured && bRiverEyeCaptured;
        const FString FlowReferenceDischargeJson = Spec.FlowReferenceDischargeCfs >= 0.0f
            ? FString::Printf(TEXT("%.1f"), Spec.FlowReferenceDischargeCfs)
            : FString(TEXT("null"));

        EntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"source_manifest\": \"%s\",\n")
            TEXT("      \"flow_band_id\": \"%s\",\n")
            TEXT("      \"flow_band_display_name\": \"%s\",\n")
            TEXT("      \"flow_band_source\": \"%s\",\n")
            TEXT("      \"flow_reference_discharge_cfs\": %s,\n")
            TEXT("      \"flow_visual_width_scale\": %.3f,\n")
            TEXT("      \"flow_visual_foam_scale\": %.3f,\n")
            TEXT("      \"flow_visual_wet_bank_scale\": %.3f,\n")
            TEXT("      \"flow_visual_current_cue_scale\": %.3f,\n")
            TEXT("      \"flow_visual_water_level_offset_cm\": %.3f,\n")
            TEXT("      \"flow_visual_note\": \"%s\",\n")
            TEXT("      \"capture\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"aerial_drape_image\": \"%s\",\n")
            TEXT("      \"terrain_relief_image\": \"%s\",\n")
            TEXT("      \"heightfield_preview_image\": \"%s\",\n")
            TEXT("      \"source_terrain_macro_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_local_relief_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_seam_feather_uv\": %.5f,\n")
            TEXT("      \"source_terrain_normal_softening_blend\": %.3f,\n")
            TEXT("      \"water_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_floor\": %.3f,\n")
            TEXT("      \"water_material_specular_level\": %.3f,\n")
            TEXT("      \"water_material_normal_intensity\": %.3f,\n")
            TEXT("      \"water_mesh_normal_up_blend\": %.3f,\n")
            TEXT("      \"water_mask_image\": \"%s\",\n")
            TEXT("      \"vegetation_mask_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_macro_albedo_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_material_zones_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_ao_roughness_height_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_normal_detail_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_albedo_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_normal_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_ao_roughness_height_image\": \"%s\",\n")
            TEXT("      \"elevation_sample\": \"%s\",\n")
            TEXT("      \"fidelity_note\": \"%s\",\n")
            TEXT("      \"first_party_material_instance_scene_assignment_status\": \"%s\"\n")
            TEXT("    }"),
            Index == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(Spec.RiverId),
            *EscapeRaftSimJsonString(Spec.DisplayName),
            *EscapeRaftSimJsonString(Spec.MapPackagePath),
            *EscapeRaftSimJsonString(Spec.SourceManifest),
            *EscapeRaftSimJsonString(Spec.FlowBandId),
            *EscapeRaftSimJsonString(Spec.FlowBandDisplayName),
            *EscapeRaftSimJsonString(Spec.FlowBandSource),
            *FlowReferenceDischargeJson,
            Spec.FlowWidthScale,
            Spec.FlowFoamScale,
            Spec.FlowWetBankScale,
            Spec.FlowCurrentCueScale,
            Spec.FlowWaterLevelOffsetCm,
            *EscapeRaftSimJsonString(Spec.FlowVisualDescription),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(RiverEyeCapturePath),
            bGuideSeatCaptured && bRiverEyeCaptured && !Spec.SourceDrapeDescription.IsEmpty() ? TEXT("captured_source_derived_guide_and_river_eye_preview_renders") : (bGuideSeatCaptured && bRiverEyeCaptured ? TEXT("captured_procedural_guide_and_river_eye_blockout_renders") : TEXT("capture_failed")),
            *EscapeRaftSimJsonString(Spec.AerialDrapeImage),
            *EscapeRaftSimJsonString(Spec.TerrainReliefImage),
            *EscapeRaftSimJsonString(Spec.HeightfieldPreviewImage),
            Spec.HeightfieldPreviewAmplitudeCm,
            Spec.HeightfieldLocalReliefAmplitudeCm,
            Spec.HeightfieldSeamFeatherUv,
            Spec.TerrainNormalSofteningBlend,
            WaterResponse.EmissiveFillScale,
            WaterResponse.RoughnessScale,
            WaterResponse.RoughnessFloor,
            WaterResponse.SpecularLevel,
            WaterResponse.NormalIntensity,
            WaterResponse.MeshNormalUpBlend,
            *EscapeRaftSimJsonString(Spec.WaterMaskImage),
            *EscapeRaftSimJsonString(Spec.VegetationMaskImage),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedMacroAlbedo"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedMaterialZones"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedAORoughnessHeight"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedNormalDetail"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailAlbedo"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailNormal"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailAORoughnessHeight"))),
            *EscapeRaftSimJsonString(Spec.ElevationSample),
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(Spec)),
            *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceSceneAssignmentStatus()));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"guide_seat_and_river_eye_downstream_unreal_preview\",\n")
        TEXT("  \"source_plan\": \"%s\",\n")
        TEXT("  \"procedural_asset_plan\": \"%s\",\n")
        TEXT("  \"procedural_material_recipe_plan\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_atlas_manifest\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_map_manifest\": \"%s\",\n")
        TEXT("  \"production_detail_texture_manifest\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_candidate_manifest\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_asset_root\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_asset_status\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_texture_asset_root\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_texture_asset_status\": \"%s\",\n")
        TEXT("  \"production_detail_texture_asset_root\": \"%s\",\n")
        TEXT("  \"production_detail_texture_asset_status\": \"%s\",\n")
        TEXT("  \"first_party_atlas_sampler_review_material\": \"%s\",\n")
        TEXT("  \"first_party_atlas_sampler_review_material_status\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_review_asset_root\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_review_asset_status\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_scene_assignment_status\": \"%s\",\n")
        TEXT("  \"geospatial_attachment_ledger\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(SourcePlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralAssetPlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralMaterialRecipePlanRelativePath),
        *EscapeRaftSimJsonString(MaterialTextureAtlasManifestRelativePath),
        *EscapeRaftSimJsonString(SourceConditionedMaterialMapManifestRelativePath),
        *EscapeRaftSimJsonString(ProductionDetailTextureManifestRelativePath),
        *EscapeRaftSimJsonString(MaterialInstanceCandidateManifestRelativePath),
        *EscapeRaftSimJsonString(MaterialTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialTextureAssetStatus()),
        *EscapeRaftSimJsonString(SourceConditionedMaterialTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetSourceConditionedMaterialTextureAssetStatus()),
        *EscapeRaftSimJsonString(ProductionDetailTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetProductionDetailTextureAssetStatus()),
        *EscapeRaftSimJsonString(MaterialShaderParentRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyAtlasSampleReviewMaterialStatus()),
        *EscapeRaftSimJsonString(MaterialInstanceReviewAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceReviewAssetStatus()),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceSceneAssignmentStatus()),
        *EscapeRaftSimJsonString(GeospatialAttachmentLedgerRelativePath),
        bAllCaptured ? TEXT("south_fork_colorado_and_pacuare_source_draped_guide_and_river_eye_previews_available; photoreal source_data_and_asset_replacement_required") : TEXT("one_or_more_captures_failed"),
        *EntriesJson);

    const FString ManifestPath = FPaths::Combine(CaptureRoot, TEXT("environment_capture_manifest.json"));
    const bool bSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s environment preview capture manifest -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *ManifestPath);

    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimSkipPhotorealFlowVariantCaptures")))
    {
        OutSummary += TEXT("Skipped flow-variant environment captures for this base-capture iteration.\n");
        return bAllCaptured && bSaved;
    }

    const FString FlowVariantCapturePlanRelativePath = GetPhotorealFlowVariantCapturePlanRelativePath();
    const FString FlowVariantCapturePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), FlowVariantCapturePlanRelativePath));
    bool bFlowVariantCapturePlanAvailable = FPaths::FileExists(FlowVariantCapturePlanAbsolutePath);
    if (!bFlowVariantCapturePlanAvailable)
    {
        OutSummary += FString::Printf(TEXT("Missing flow-variant capture plan: %s\n"), *FlowVariantCapturePlanAbsolutePath);
    }
    else
    {
        OutSummary += FString::Printf(TEXT("Using photoreal flow-variant capture plan: %s\n"), *FlowVariantCapturePlanRelativePath);
    }

    FString FlowVariantEntriesJson;
    bool bAllFlowVariantCaptured = bFlowVariantCapturePlanAvailable;
    const bool bCullReviewOnlyForegroundRaftForFlowVariantGuideSeatCaptures = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> FlowVariantSpecs = GetEnvironmentPreviewFlowVariantSpecs();
    for (int32 VariantIndex = 0; VariantIndex < FlowVariantSpecs.Num(); ++VariantIndex)
    {
        const FRaftSimEnvironmentPreviewSpec& VariantSpec = FlowVariantSpecs[VariantIndex];
        const FRaftSimPreviewWaterMaterialResponse VariantWaterResponse =
            GetPreviewWaterMaterialResponse(VariantSpec.RiverId);
        OutSummary += FString::Printf(
            TEXT("Generating %s %s flow-variant preview map.\n"),
            *VariantSpec.DisplayName,
            *VariantSpec.FlowBandId);
        const bool bVariantMapBuilt = BuildPreviewMapForSpec(VariantSpec, OutSummary);

        FString GuideSeatVariantCapturePath =
            GetPreviewFlowVariantCaptureRelativePath(VariantSpec, TEXT("guide_seat_downstream"));
        FString RiverEyeVariantCapturePath =
            GetPreviewFlowVariantCaptureRelativePath(VariantSpec, TEXT("river_eye_downstream"));
        const bool bGuideSeatVariantCaptured =
            bVariantMapBuilt &&
            CapturePreviewImageForSpec(
                VariantSpec,
                CaptureRoot,
                GuideSeatVariantCapturePath,
                TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
                TEXT("guide_seat_downstream"),
                TEXT("flow-variant guide-seat downstream"),
                bCullReviewOnlyForegroundRaftForFlowVariantGuideSeatCaptures,
                OutSummary);
        const bool bRiverEyeVariantCaptured =
            bVariantMapBuilt &&
            CapturePreviewImageForSpec(
                VariantSpec,
                CaptureRoot,
                RiverEyeVariantCapturePath,
                TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
                TEXT("river_eye_downstream"),
                TEXT("flow-variant river-eye downstream"),
                true,
                OutSummary);
        bAllFlowVariantCaptured &= bGuideSeatVariantCaptured && bRiverEyeVariantCaptured;
        const FString VariantFlowReferenceDischargeJson = VariantSpec.FlowReferenceDischargeCfs >= 0.0f
            ? FString::Printf(TEXT("%.1f"), VariantSpec.FlowReferenceDischargeCfs)
            : FString(TEXT("null"));

        FlowVariantEntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"source_manifest\": \"%s\",\n")
            TEXT("      \"flow_band_id\": \"%s\",\n")
            TEXT("      \"flow_band_display_name\": \"%s\",\n")
            TEXT("      \"flow_band_source\": \"%s\",\n")
            TEXT("      \"flow_reference_discharge_cfs\": %s,\n")
            TEXT("      \"flow_visual_width_scale\": %.3f,\n")
            TEXT("      \"flow_visual_foam_scale\": %.3f,\n")
            TEXT("      \"flow_visual_wet_bank_scale\": %.3f,\n")
            TEXT("      \"flow_visual_current_cue_scale\": %.3f,\n")
            TEXT("      \"flow_visual_water_level_offset_cm\": %.3f,\n")
            TEXT("      \"flow_visual_note\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"source_terrain_macro_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_local_relief_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_seam_feather_uv\": %.5f,\n")
            TEXT("      \"source_terrain_normal_softening_blend\": %.3f,\n")
            TEXT("      \"water_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_floor\": %.3f,\n")
            TEXT("      \"water_material_specular_level\": %.3f,\n")
            TEXT("      \"water_material_normal_intensity\": %.3f,\n")
            TEXT("      \"water_mesh_normal_up_blend\": %.3f,\n")
            TEXT("      \"fidelity_note\": \"%s\"\n")
            TEXT("    }"),
            VariantIndex == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(VariantSpec.RiverId),
            *EscapeRaftSimJsonString(VariantSpec.DisplayName),
            *EscapeRaftSimJsonString(VariantSpec.MapPackagePath),
            *EscapeRaftSimJsonString(VariantSpec.SourceManifest),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandId),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandDisplayName),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandSource),
            *VariantFlowReferenceDischargeJson,
            VariantSpec.FlowWidthScale,
            VariantSpec.FlowFoamScale,
            VariantSpec.FlowWetBankScale,
            VariantSpec.FlowCurrentCueScale,
            VariantSpec.FlowWaterLevelOffsetCm,
            *EscapeRaftSimJsonString(VariantSpec.FlowVisualDescription),
            *EscapeRaftSimJsonString(GuideSeatVariantCapturePath),
            *EscapeRaftSimJsonString(RiverEyeVariantCapturePath),
            bGuideSeatVariantCaptured && bRiverEyeVariantCaptured ? TEXT("captured_band_named_flow_variant_preview_renders") : TEXT("capture_failed"),
            VariantSpec.HeightfieldPreviewAmplitudeCm,
            VariantSpec.HeightfieldLocalReliefAmplitudeCm,
            VariantSpec.HeightfieldSeamFeatherUv,
            VariantSpec.TerrainNormalSofteningBlend,
            VariantWaterResponse.EmissiveFillScale,
            VariantWaterResponse.RoughnessScale,
            VariantWaterResponse.RoughnessFloor,
            VariantWaterResponse.SpecularLevel,
            VariantWaterResponse.NormalIntensity,
            VariantWaterResponse.MeshNormalUpBlend,
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(VariantSpec)));
    }

    const FString FlowVariantManifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_flow_variant_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"band_named_guide_seat_and_river_eye_downstream_unreal_preview\",\n")
        TEXT("  \"source_capture_manifest\": \"docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json\",\n")
        TEXT("  \"source_flow_variant_capture_plan\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(FlowVariantCapturePlanRelativePath),
        bAllFlowVariantCaptured ? TEXT("all_band_named_flow_variant_previews_captured_not_lifelike_approved") : TEXT("one_or_more_flow_variant_captures_failed"),
        *FlowVariantEntriesJson);

    const FString FlowVariantManifestPath = FPaths::Combine(CaptureRoot, TEXT("flow_variant_capture_manifest.json"));
    const bool bFlowVariantManifestSaved = FFileHelper::SaveStringToFile(FlowVariantManifest, *FlowVariantManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s flow-variant environment preview capture manifest -> %s\n"),
        bFlowVariantManifestSaved ? TEXT("Saved") : TEXT("Failed"),
        *FlowVariantManifestPath);

    return bSaved && bAllCaptured && bFlowVariantManifestSaved && bAllFlowVariantCaptured;
}
