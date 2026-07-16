#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

void FRaftSimEditorModule::HandlePhotorealEnvironmentAutomationStartup()
{
    if (PhotorealEnvironmentAutomationPostEngineInitHandle.IsValid())
    {
        FCoreDelegates::GetOnPostEngineInit().Remove(PhotorealEnvironmentAutomationPostEngineInitHandle);
        PhotorealEnvironmentAutomationPostEngineInitHandle.Reset();
    }

    PhotorealEnvironmentAutomationTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateRaw(this, &FRaftSimEditorModule::TickPhotorealEnvironmentAutomationStartup),
        0.5f);
}

bool FRaftSimEditorModule::TickPhotorealEnvironmentAutomationStartup(float)
{
    ++PhotorealEnvironmentAutomationStartupAttempts;
    if (!GEditor || !GEditor->GetEditorWorldContext().World())
    {
        if (PhotorealEnvironmentAutomationStartupAttempts < 120)
        {
            return true;
        }

        UE_LOG(LogRaftSimEditorEnvironment, Error, TEXT("Timed out waiting for an editor world before photoreal environment automation."));
        if (bExitAfterPhotorealEnvironmentAutomation)
        {
            FPlatformMisc::RequestExit(true, TEXT("RaftSim photoreal environment automation timed out"));
        }
        return false;
    }

    PhotorealEnvironmentAutomationTickerHandle.Reset();

    FString Summary;
    bool bSucceeded = true;

    if (bCreatePhotorealEnvironmentPreviewMapsOnStartup)
    {
        bSucceeded &= CreatePhotorealEnvironmentPreviewMaps(Summary);
    }

    if (bCapturePhotorealEnvironmentPreviewsOnStartup)
    {
        bSucceeded &= CapturePhotorealEnvironmentPreviews(Summary);
    }

    if (bCreateLandscapeImportCandidateMapsOnStartup)
    {
        bSucceeded &= CreateLandscapeImportCandidateMaps(Summary);
    }

    if (bCreateZambeziBatokaBasaltFamilyOnStartup)
    {
        bSucceeded &= CreateZambeziBatokaBasaltFamily(Summary);
    }

    if (bCaptureZambeziBatokaBasaltCorridorComparisonOnStartup)
    {
        bSucceeded &= CaptureZambeziBatokaBasaltCorridorComparison(Summary);
    }

    if (bCaptureZambeziBatokaTerrainIntegratedComparisonOnStartup)
    {
        bSucceeded &= CaptureZambeziBatokaTerrainIntegratedComparison(Summary);
    }

    if (bCaptureZambeziBatokaWorldAlignedTerrainComparisonOnStartup)
    {
        bSucceeded &= CaptureZambeziBatokaWorldAlignedTerrainComparison(Summary);
    }

    if (bCaptureZambeziBatokaVisualMorphologyComparisonOnStartup)
    {
        bSucceeded &= CaptureZambeziBatokaVisualMorphologyComparison(Summary);
    }

    if (bCaptureFutaleufuDenseCanopyComparisonOnStartup)
    {
        bSucceeded &= CaptureFutaleufuDenseCanopyComparison(Summary);
    }

    if (bCaptureFutaleufuAreaSampledCanopyComparisonOnStartup)
    {
        bSucceeded &= CaptureFutaleufuAreaSampledCanopyComparison(Summary);
    }

    if (bCaptureFutaleufuWorldStableCanopyComparisonOnStartup)
    {
        bSucceeded &= CaptureFutaleufuWorldStableCanopyComparison(Summary);
    }

    if (bCreateFutaleufuCordilleraCypressFamilyOnStartup)
    {
        bSucceeded &= CreateFutaleufuCordilleraCypressFamily(Summary);
    }

    if (bCreateFutaleufuCordilleraCypressOpaqueNearReviewOnStartup)
    {
        bSucceeded &= CreateFutaleufuCordilleraCypressOpaqueNearReview(Summary);
    }

    if (bCreateFutaleufuCordilleraCypressVolumetricNearReviewOnStartup)
    {
        bSucceeded &= CreateFutaleufuCordilleraCypressVolumetricNearReview(Summary);
    }

    if (bCreateFutaleufuCordilleraCypressDonorReviewOnStartup)
    {
        bSucceeded &= CreateFutaleufuCordilleraCypressDonorReview(Summary);
    }

    UE_LOG(LogRaftSimEditorEnvironment, Display, TEXT("%s"), *Summary);

    if (bExitAfterPhotorealEnvironmentAutomation)
    {
        FPlatformMisc::RequestExit(!bSucceeded, TEXT("RaftSim photoreal environment automation complete"));
    }

    return false;
}

bool FRaftSimEditorModule::CreatePhotorealEnvironmentPreviewMaps(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString SourcePlanRelativePath = GetPhotorealRiverSourcePlanRelativePath();
    const FString SourcePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourcePlanRelativePath));
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

    if (!FPaths::FileExists(SourcePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing photoreal river source plan: %s\n"), *SourcePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralAssetPlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural environment asset plan: %s\n"), *ProceduralAssetPlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralMaterialRecipePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural material recipe plan: %s\n"), *ProceduralMaterialRecipePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialTextureAtlasManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material texture atlas manifest: %s\n"), *MaterialTextureAtlasManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(SourceConditionedMaterialMapManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing source-conditioned material map manifest: %s\n"),
            *SourceConditionedMaterialMapManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProductionDetailTextureManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing first-party production detail texture manifest: %s\n"),
            *ProductionDetailTextureManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialInstanceCandidateManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material instance candidate manifest: %s\n"), *MaterialInstanceCandidateManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }

    OutSummary += FString::Printf(TEXT("Using photoreal river source plan: %s\n"), *SourcePlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural environment asset plan: %s\n"), *ProceduralAssetPlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural material recipe plan: %s\n"), *ProceduralMaterialRecipePlanRelativePath);
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

    bool bAllSaved = CreateFirstPartyMaterialInstanceCandidateAssets(OutSummary);
    for (const FRaftSimEnvironmentPreviewSpec& Spec : GetEnvironmentPreviewSpecs())
    {
        OutSummary += FString::Printf(TEXT("Generating %s preview map.\n"), *Spec.DisplayName);
        bAllSaved &= BuildPreviewMapForSpec(Spec, OutSummary);
    }

    return bAllSaved;
}

bool FRaftSimEditorModule::CreateLandscapeImportCandidateMaps(
    FString& OutSummary,
    const FString& RiverIdFilter)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString CandidateCaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CandidateCaptureRoot = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), CandidateCaptureRelativeRoot));
    IFileManager::Get().MakeDirectory(*CandidateCaptureRoot, true);

    const FString SolverVisualizationManifestRelativePath =
        GetSolverVisualizationFieldManifestRelativePath();
    const FString SolverVisualizationManifestAbsolutePath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), SolverVisualizationManifestRelativePath));
    if (!FPaths::FileExists(SolverVisualizationManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing validated solver visualization field manifest: %s\n"),
            *SolverVisualizationManifestAbsolutePath);
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Using validated solver visualization field manifest: %s\n"),
        *SolverVisualizationManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using solver visualization Texture2D asset root: %s\n"),
        *GetSolverVisualizationFieldTextureAssetRootRelativePath());

    FString EntriesJson;
    TMap<FString, UTexture2D*> SourceTextureAssetsByKey;
    bool bAllSucceeded =
        CreateFirstPartyMaterialTextureAtlasAssets(
            SourceTextureAssetsByKey,
            OutSummary,
            RiverIdFilter);
    bAllSucceeded &=
        CreateSourceConditionedMaterialTextureAssets(
            SourceTextureAssetsByKey,
            OutSummary,
            RiverIdFilter);
    bAllSucceeded &=
        CreateProductionDetailMaterialTextureAssets(
            SourceTextureAssetsByKey,
            OutSummary,
            RiverIdFilter);
    bAllSucceeded &= CreateSolverVisualizationFieldTextureAssets(OutSummary);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    if (!RiverIdFilter.IsEmpty())
    {
        Candidates = Candidates.FilterByPredicate(
            [&RiverIdFilter](const FRaftSimLandscapeImportCandidateSpec& Candidate)
            {
                return Candidate.PreviewSpec.RiverId == RiverIdFilter;
            });
        if (Candidates.IsEmpty())
        {
            OutSummary += FString::Printf(
                TEXT("No source Landscape candidate is registered for river_id %s.\n"),
                *RiverIdFilter);
            return false;
        }
        OutSummary += FString::Printf(
            TEXT("Limiting source Landscape creation to river_id %s.\n"),
            *RiverIdFilter);
    }
    for (int32 Index = 0; Index < Candidates.Num(); ++Index)
    {
        const FRaftSimLandscapeImportCandidateSpec& Candidate = Candidates[Index];
        const FString HeightfieldManifestAbsolutePath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(GetRepoRoot(), Candidate.HeightfieldManifestRelativePath));
        const FString ImportContractAbsolutePath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(GetRepoRoot(), Candidate.ImportContractRelativePath));
        const bool bSourceContractsPresent =
            FPaths::FileExists(HeightfieldManifestAbsolutePath) && FPaths::FileExists(ImportContractAbsolutePath);
        if (!bSourceContractsPresent)
        {
            OutSummary += FString::Printf(
                TEXT("Missing source Landscape manifest or import contract for %s.\n"),
                *Candidate.PreviewSpec.RiverId);
        }

        FRaftSimLandscapeImportCandidateResult Result;
        const bool bMapBuilt = bSourceContractsPresent &&
            BuildLandscapeImportCandidateMap(Candidate, Result, OutSummary);

        FString GuideSeatCapturePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate,
            TEXT("guide_seat_downstream"));
        FString RiverEyeCapturePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate,
            TEXT("river_eye_downstream"));
        const bool bGuideSeatCaptured = bMapBuilt && CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CandidateCaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_guide_seat_downstream"),
            TEXT("source Landscape candidate guide-seat downstream"),
            true,
            OutSummary);
        const bool bRiverEyeCaptured = bMapBuilt && CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CandidateCaptureRoot,
            RiverEyeCapturePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_river_eye_downstream"),
            TEXT("source Landscape candidate river-eye downstream"),
            true,
            OutSummary);
        FString SolverRapidCapturePath;
        bool bSolverRapidCaptured = true;
        if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            SolverRapidCapturePath = GetLandscapeCandidateCaptureRelativePath(
                Candidate,
                TEXT("solver_rapid_river_eye_downstream"));
            bSolverRapidCaptured = bMapBuilt && CapturePreviewImageForSpec(
                Candidate.PreviewSpec,
                CandidateCaptureRoot,
                SolverRapidCapturePath,
                TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"),
                TEXT("landscape_candidate_solver_rapid_river_eye_downstream"),
                TEXT("source Landscape candidate solver-rapid river-eye downstream"),
                true,
                OutSummary);
        }
        const bool bCandidateSucceeded =
            bSourceContractsPresent && bMapBuilt && bGuideSeatCaptured && bRiverEyeCaptured && bSolverRapidCaptured;
        bAllSucceeded &= bCandidateSucceeded;
        FRaftSimLandscapeMaterialCandidateSettings MaterialSettings =
            GetLandscapeMaterialCandidateSettings(Candidate.PreviewSpec.RiverId);
        if (Candidate.bPhysicalScaleSourceCorridor)
        {
            MaterialSettings.MacroMappingScale = static_cast<float>(Candidate.LandscapeSize - 1);
            if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
            {
                MaterialSettings.DetailMappingScale = 96.0f;
                MaterialSettings.DetailAlbedoWeight = 0.10f;
                MaterialSettings.DetailNormalWeight = 0.22f;
                MaterialSettings.DetailSurfaceResponseWeight = 0.18f;
                MaterialSettings.RiverbedBlendWeight = 0.18f;
                MaterialSettings.WetBankBlendWeight = 0.24f;
            }
        }
        FRaftSimLandscapeCandidateWaterSettings WaterSettings =
            GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
        if (!Candidate.bUseSolverVisualizationFields &&
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            WaterSettings.BaseColorScale = 1.00f;
            WaterSettings.SurfaceTint = FLinearColor(0.025f, 0.120f, 0.100f);
            WaterSettings.VertexTintWeight = 0.72f;
            WaterSettings.EmissiveFillScale = 0.080f;
            WaterSettings.ReflectionFillIntensity = 0.26f;
            WaterSettings.ReflectionTint = FLinearColor(0.36f, 0.52f, 0.60f);
            WaterSettings.Roughness = 0.14f;
            WaterSettings.Specular = 0.65f;
            WaterSettings.NormalIntensity = 0.60f;
            WaterSettings.SolverFieldEnable = 0.0f;
            WaterSettings.SolverMacroNormalWeight = 0.0f;
            WaterSettings.SolverDepthColorWeight = 0.0f;
            WaterSettings.SolverFieldRoughnessWeight = 0.0f;
            WaterSettings.SolverFroudeAerationWeight = 0.0f;
        }
        const FRaftSimPhotographicCaptureSettings CaptureSettings =
            GetPhotographicCaptureSettings(Candidate.PreviewSpec.RiverId);
        const FRaftSimLandscapeCandidateFoliageSettings FoliageSettings =
            GetLandscapeCandidateFoliageSettings(Candidate.PreviewSpec.RiverId);
        const FString RiverAssetName =
            GetFirstPartyMaterialRiverAssetName(Candidate.PreviewSpec.RiverId);
        const int32 CandidateNumSubsections = Candidate.bPhysicalScaleSourceCorridor ? 2 : 1;
        constexpr int32 CandidateSubsectionSizeQuads = 63;
        const int32 CandidateComponentCountAxis =
            (Candidate.LandscapeSize - 1) /
            (CandidateNumSubsections * CandidateSubsectionSizeQuads);
        const bool bHasSolverVisualizationFields =
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") &&
            Candidate.bUseSolverVisualizationFields;
        const bool bHasManifestConditionedPhysicalChannel =
            Candidate.bPhysicalScaleSourceCorridor;

        EntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"source_heightfield\": \"%s\",\n")
            TEXT("      \"source_heightfield_manifest\": \"%s\",\n")
            TEXT("      \"unreal_import_contract\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"solver_rapid_river_eye_capture\": \"%s\",\n")
            TEXT("      \"solver_rapid_capture_status\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"photographic_capture_status\": \"river_specific_recorded_capture_photometry_no_camera_film_grain\",\n")
            TEXT("      \"photographic_sun_intensity\": %.6f,\n")
            TEXT("      \"photographic_skylight_intensity\": %.6f,\n")
            TEXT("      \"photographic_fog_density\": %.6f,\n")
            TEXT("      \"photographic_exposure_bias\": %.6f,\n")
            TEXT("      \"photographic_saturation\": %.6f,\n")
            TEXT("      \"photographic_contrast\": %.6f,\n")
            TEXT("      \"photographic_sharpen\": %.6f,\n")
            TEXT("      \"photographic_vignette\": %.6f,\n")
            TEXT("      \"photographic_film_grain_intensity\": %.6f,\n")
            TEXT("      \"heightfield_format\": \"16-bit grayscale PNG\",\n")
            TEXT("      \"heightfield_width_px\": %d,\n")
            TEXT("      \"heightfield_height_px\": %d,\n")
            TEXT("      \"component_count_x\": %d,\n")
            TEXT("      \"component_count_y\": %d,\n")
            TEXT("      \"component_count_total\": %d,\n")
            TEXT("      \"num_subsections\": %d,\n")
            TEXT("      \"subsection_size_quads\": 63,\n")
            TEXT("      \"source_height_min_uint16\": %u,\n")
            TEXT("      \"source_height_max_uint16\": %u,\n")
            TEXT("      \"preview_channel_floor_uint16\": %u,\n")
            TEXT("      \"preview_channel_modified_sample_count\": %d,\n")
            TEXT("      \"channel_burn_policy\": \"%s\",\n")
            TEXT("      \"channel_burn_promotion_status\": \"%s\",\n")
            TEXT("      \"landscape_location_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_scale\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"horizontal_span_x_cm\": %.3f,\n")
            TEXT("      \"horizontal_span_y_cm\": %.3f,\n")
            TEXT("      \"target_relief_cm\": %.3f,\n")
            TEXT("      \"landscape_material_status\": \"source_conditioned_macro_zones_plus_first_party_close_range_detail_review_candidate\",\n")
            TEXT("      \"landscape_material_texture_asset_count\": 7,\n")
            TEXT("      \"landscape_material_zone_parameter\": \"SourceConditionedMaterialZones\",\n")
            TEXT("      \"landscape_material_zone_semantics\": \"rgb_r_terrain_wet_bank_g_vegetation_b_visible_water\",\n")
            TEXT("      \"landscape_material_macro_mapping_scale\": %.3f,\n")
            TEXT("      \"landscape_material_detail_mapping_scale\": %.3f,\n")
            TEXT("      \"landscape_material_detail_albedo_weight\": %.3f,\n")
            TEXT("      \"landscape_material_detail_normal_weight\": %.3f,\n")
            TEXT("      \"landscape_material_detail_surface_response_weight\": %.3f,\n")
            TEXT("      \"landscape_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"landscape_material_specular_level\": %.3f,\n")
            TEXT("      \"landscape_material_riverbed_blend_weight\": %.3f,\n")
            TEXT("      \"landscape_material_wet_bank_blend_weight\": %.3f,\n")
            TEXT("      \"landscape_material_wet_bank_artifact_suppression_gain\": 2.400,\n")
            TEXT("      \"landscape_material_riverbed_roughness\": %.3f,\n")
            TEXT("      \"landscape_material_riverbed_color_scale\": [%.3f, %.3f, %.3f],\n")
            TEXT("      \"landscape_material_wet_bank_color_scale\": [%.3f, %.3f, %.3f],\n")
            TEXT("      \"landscape_material_zone_conditioning_policy\": \"source_visible_water_darkens_submerged_riverbed_and_feathered_source_water_edge_conditions_wet_bank_without_changing_landscape_geometry_or_solver_authority\",\n")
            TEXT("      \"landscape_material_wet_bank_artifact_policy\": \"saturate_existing_source_feather_band_to_suppress_bright_albedo_rails_without_widening_water_mask_or_adding_geometry\",\n")
            TEXT("      \"landscape_material_promotion_status\": \"review_only_not_lifelike_not_gameplay_promoted\",\n")
            TEXT("      \"landscape_dressing_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_boulder_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_source_species_skeletal_mesh_count\": %d,\n")
            TEXT("      \"landscape_dressing_converted_species_static_mesh_count\": %d,\n")
            TEXT("      \"landscape_dressing_external_review_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_external_review_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_rock_mesh_count\": %d,\n")
            TEXT("      \"landscape_dressing_external_review_rock_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_rock_asset_root\": \"/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K\",\n")
            TEXT("      \"landscape_dressing_external_review_rock_source_manifest\": \"unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/polyhaven_rock_moss_set_01_source_manifest.json\",\n")
            TEXT("      \"landscape_dressing_external_review_pine_mesh_count\": %d,\n")
            TEXT("      \"landscape_dressing_external_review_pine_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_pine_asset_root\": \"/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K\",\n")
            TEXT("      \"landscape_dressing_external_review_pine_assets\": [\"/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/SM_PineTree01_pine_tree_01_a_LOD0\", \"/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/SM_PineTree01_pine_tree_01_b_LOD0\", \"/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/SM_PineTree01_pine_tree_01_c_LOD0\"],\n")
            TEXT("      \"landscape_dressing_external_review_pine_source_manifest\": \"unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/polyhaven_pine_tree_01_source_manifest.json\",\n")
            TEXT("      \"landscape_dressing_external_review_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_source_manifest\": \"unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/polyhaven_fir_tree_01_source_manifest.json\",\n")
            TEXT("      \"landscape_dressing_external_review_broadleaf_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_broadleaf_source_manifest\": \"unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/polyhaven_tree_small_02_source_manifest.json\",\n")
            TEXT("      \"landscape_dressing_external_review_conifer_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_external_review_conifer_source_manifest\": \"unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/polyhaven_fir_tree_01_source_manifest.json\",\n")
            TEXT("      \"landscape_dressing_source_species_skeletal_assets\": [\"/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/PVE_Deciduous_Tree_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/PVE_Conifer_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/Deciduous_Shrub_01/PVE_Deciduous_Shrub_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/PVE_Plant_01\"],\n")
            TEXT("      \"landscape_dressing_converted_species_static_assets\": [\"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static\"],\n")
            TEXT("      \"landscape_dressing_broadleaf_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_conifer_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_shrub_asset\": \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static\",\n")
            TEXT("      \"landscape_dressing_understory_asset\": \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static\",\n")
            TEXT("      \"landscape_dressing_trunk_asset\": null,\n")
            TEXT("      \"landscape_dressing_instance_implementation\": \"%s\",\n")
            TEXT("      \"landscape_dressing_boulder_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_foliage_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_canopy_tree_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_understory_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_trunk_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_source_mask_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_foliage_material_bound_slot_count\": %d,\n")
            TEXT("      \"landscape_dressing_native_foliage_material_fallback_slot_count\": %d,\n")
            TEXT("      \"landscape_dressing_broadleaf_material_asset\": \"/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Broadleaf_BiomeFoliageCandidate\",\n")
            TEXT("      \"landscape_dressing_conifer_material_asset\": \"/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Conifer_BiomeFoliageCandidate\",\n")
            TEXT("      \"landscape_dressing_understory_material_asset\": \"/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Understory_BiomeFoliageCandidate\",\n")
            TEXT("      \"landscape_dressing_broadleaf_front_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_broadleaf_back_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_broadleaf_transmission_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_front_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_back_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_transmission_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_foliage_roughness_strength\": %.6f,\n")
            TEXT("      \"landscape_dressing_foliage_normal_strength\": %.6f,\n")
            TEXT("      \"procedural_vegetation_editor_plugin_enabled\": true,\n")
            TEXT("      \"nanite_foliage_project_setting_enabled\": true,\n")
            TEXT("      \"landscape_dressing_boulder_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_broadleaf_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_conifer_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_understory_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_promotion_status\": \"%s\",\n")
            TEXT("      \"water_material_status\": \"%s\",\n")
            TEXT("      \"water_material_asset\": \"%s\",\n")
            TEXT("      \"water_material_parent\": \"/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate\",\n")
            TEXT("      \"water_shading_model\": \"DefaultLit\",\n")
            TEXT("      \"water_blend_mode\": \"Opaque\",\n")
            TEXT("      \"water_custom_output\": \"none_surface_only_solver_conditioned_shading\",\n")
            TEXT("      \"water_volume_parameter_status\": \"inactive_single_layer_evaluation_values_retained_in_manifest_only\",\n")
            TEXT("      \"water_normal_source\": \"river_specific_first_party_normal_atlas_plus_optional_validated_cpp_solver_macro_normal\",\n")
            TEXT("      \"water_solver_visualization_field_status\": \"%s\",\n")
            TEXT("      \"water_solver_visualization_field_manifest\": \"%s\",\n")
            TEXT("      \"water_solver_visualization_field_texture_count\": %d,\n")
            TEXT("      \"water_solver_visualization_field_feature_strength_scale\": %s,\n")
            TEXT("      \"water_solver_visualization_field_enable\": %.6f,\n")
            TEXT("      \"water_solver_macro_normal_weight\": %.6f,\n")
            TEXT("      \"water_solver_depth_color_weight\": %.6f,\n")
            TEXT("      \"water_solver_field_roughness_weight\": %.6f,\n")
            TEXT("      \"water_solver_froude_aeration_weight\": %.6f,\n")
            TEXT("      \"water_solver_speed_visual_gain\": %.6f,\n")
            TEXT("      \"water_solver_froude_visual_gain\": %.6f,\n")
            TEXT("      \"water_solver_surface_relief_scale\": %.6f,\n")
            TEXT("      \"water_solver_surface_relief_cap_cm\": %.6f,\n")
            TEXT("      \"water_solver_analytic_displacement_residual_scale\": %.6f,\n")
            TEXT("      \"water_solver_render_geometry_collision_enabled\": false,\n")
            TEXT("      \"water_solver_foam_status\": \"%s\",\n")
            TEXT("      \"water_solver_foam_material\": \"/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate\",\n")
            TEXT("      \"water_solver_foam_max_opacity\": %.6f,\n")
            TEXT("      \"water_solver_foam_surface_offset_cm\": %.6f,\n")
            TEXT("      \"water_solver_visualization_authority\": \"review_only_noncolliding_render_geometry_and_material_derivative_does_not_change_solver_collision_raft_forces_or_feature_forcing\",\n")
            TEXT("      \"water_material_bound_component_count\": %d,\n")
            TEXT("      \"water_base_color_scale\": %.6f,\n")
            TEXT("      \"water_surface_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_vertex_tint_weight\": %.6f,\n")
            TEXT("      \"water_emissive_fill_scale\": %.6f,\n")
            TEXT("      \"water_reflection_fill_intensity\": %.6f,\n")
            TEXT("      \"water_reflection_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_roughness\": %.6f,\n")
            TEXT("      \"water_specular\": %.6f,\n")
            TEXT("      \"water_surface_opacity\": %.6f,\n")
            TEXT("      \"water_normal_intensity\": %.6f,\n")
            TEXT("      \"water_normal_atlas_sampling_policy\": \"half_period_dual_sample_crossfade_prevents_frac_tile_boundaries\",\n")
            TEXT("      \"water_normal_atlas_phase_offset\": 0.500000,\n")
            TEXT("      \"water_inactive_single_layer_refraction_ior\": %.6f,\n")
            TEXT("      \"water_inactive_single_layer_phase_g\": %.6f,\n")
            TEXT("      \"water_inactive_single_layer_scattering_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_inactive_single_layer_absorption_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_inactive_single_layer_color_scale_behind_water\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_render_width_scale\": %.6f,\n")
            TEXT("      \"water_render_normal_up_blend\": %.6f,\n")
            TEXT("      \"water_render_displacement_scale\": %.6f,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_enabled\": false,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_policy\": \"disabled_for_solver_surface_water_candidates_legacy_diagnostic_branch_retained\",\n")
            TEXT("      \"water_geometry_authority\": \"custom_cpp_solver_informed_ribbon_geometry_and_vertex_flow_cues_no_visual_forcing_authority\",\n")
            TEXT("      \"waterbody_dependency\": \"none_default_lit_solver_surface_runs_on_generated_procedural_mesh_ribbon\",\n")
            TEXT("      \"water_reflection_capture_policy\": \"default_lit_surface_uses_movable_skylight_runtime_corridor_sphere_capture_screen_space_reflections_and_bounded_fresnel_sky_fill\",\n")
            TEXT("      \"water_material_promotion_status\": \"review_only_requires_visual_guide_solver_hazard_and_performance_validation\",\n")
            TEXT("      \"material_usage_contract\": \"%s\",\n")
            TEXT("      \"material_bound_component_count\": %d,\n")
            TEXT("      \"material_binding_status\": \"%s\",\n")
            TEXT("      \"nanite_enabled\": %s,\n")
            TEXT("      \"nanite_component_count\": %d,\n")
            TEXT("      \"nanite_material_slot_count\": %d,\n")
            TEXT("      \"nanite_material_bound_slot_count\": %d,\n")
            TEXT("      \"nanite_material_audit_error_count\": %d,\n")
            TEXT("      \"nanite_representation_status\": \"%s\",\n")
            TEXT("      \"capture_shader_warmup_policy\": \"render_then_finish_compilation_recreate_landscape_components_render_again\",\n")
            TEXT("      \"promotion_status\": \"review_gated_isolated_candidate_not_enabled_for_gameplay_or_active_previews\"\n")
            TEXT("    }"),
            Index == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(Candidate.PreviewSpec.RiverId),
            *EscapeRaftSimJsonString(Candidate.PreviewSpec.DisplayName),
            *EscapeRaftSimJsonString(Candidate.HeightfieldRelativePath),
            *EscapeRaftSimJsonString(Candidate.HeightfieldManifestRelativePath),
            *EscapeRaftSimJsonString(Candidate.ImportContractRelativePath),
            *EscapeRaftSimJsonString(Candidate.MapPackagePath),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(RiverEyeCapturePath),
            *EscapeRaftSimJsonString(SolverRapidCapturePath),
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
                ? (bSolverRapidCaptured
                       ? (bHasSolverVisualizationFields
                              ? TEXT("captured_at_validated_median_field_high_froude_approach")
                              : TEXT("captured_physical_corridor_midreach_geometry_review_without_solver_field"))
                       : TEXT("solver_rapid_capture_failed"))
                : TEXT("not_available_without_river_specific_validated_solver_field"),
            bCandidateSucceeded ? TEXT("captured_source_landscape_import_candidate") : TEXT("candidate_generation_or_capture_failed"),
            CaptureSettings.SunIntensity,
            CaptureSettings.SkyLightIntensity,
            CaptureSettings.FogDensity,
            CaptureSettings.ExposureBias,
            CaptureSettings.Saturation,
            CaptureSettings.Contrast,
            CaptureSettings.Sharpen,
            CaptureSettings.Vignette,
            CaptureSettings.FilmGrainIntensity,
            Candidate.LandscapeSize,
            Candidate.LandscapeSize,
            CandidateComponentCountAxis,
            CandidateComponentCountAxis,
            CandidateComponentCountAxis * CandidateComponentCountAxis,
            CandidateNumSubsections,
            static_cast<uint32>(Result.SourceHeightMin),
            static_cast<uint32>(Result.SourceHeightMax),
            static_cast<uint32>(Result.ChannelFloor),
            Result.ChannelModifiedSampleCount,
            bHasManifestConditionedPhysicalChannel
                ? TEXT("source_manifest_recorded_bounded_hydrologic_channel_conditioning")
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("source_dem_unconditioned_channel_pending_manifest_recorded_hydrologic_conditioning")
                       : TEXT("preview_only_analytic_channel_burn_for_landscape_import_validation")),
            bHasManifestConditionedPhysicalChannel
                ? TEXT("review_gated_derived_geometry_not_solver_or_surveyed_bathymetry")
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("conditioning_required_before_lifelike_review")
                       : TEXT("not_solver_geometry_not_geospatially_approved_not_for_gameplay")),
            Result.LandscapeLocation.X,
            Result.LandscapeLocation.Y,
            Result.LandscapeLocation.Z,
            Result.LandscapeScale.X,
            Result.LandscapeScale.Y,
            Result.LandscapeScale.Z,
            Candidate.HorizontalSpanXCm,
            Candidate.HorizontalSpanYCm,
            Candidate.TargetReliefCm,
            MaterialSettings.MacroMappingScale,
            MaterialSettings.DetailMappingScale,
            MaterialSettings.DetailAlbedoWeight,
            MaterialSettings.DetailNormalWeight,
            MaterialSettings.DetailSurfaceResponseWeight,
            MaterialSettings.EmissiveFillScale,
            MaterialSettings.SpecularLevel,
            MaterialSettings.RiverbedBlendWeight,
            MaterialSettings.WetBankBlendWeight,
            MaterialSettings.RiverbedRoughness,
            MaterialSettings.RiverbedColorScale.R,
            MaterialSettings.RiverbedColorScale.G,
            MaterialSettings.RiverbedColorScale.B,
            MaterialSettings.WetBankColorScale.R,
            MaterialSettings.WetBankColorScale.G,
            MaterialSettings.WetBankColorScale.B,
            Result.bDressingValidated
                ? (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("source_mask_placed_complete_pve_species_and_rights_reviewed_rock_comparison_captured")
                       : TEXT("source_mask_placed_complete_pve_species_and_dense_irregular_rock_evaluation_captured"))
                : TEXT("dressing_generation_or_validation_failed"),
            Result.DressingAssetCount,
            Result.DressingExternalRockMeshCount == 6
                ? TEXT("rights_reviewed_cc0_poly_haven_rock_moss_set_01_six_variant_nanite_visual_comparison")
                : TEXT("first_party_8_ring_20_segment_irregular_procedural_mesh_with_river_specific_lit_color"),
            Result.DressingSourceSkeletalMeshCount,
            Result.DressingConvertedStaticMeshCount,
            Result.DressingExternalReviewAssetCount,
            Result.DressingExternalRockMeshCount == 6 && Result.DressingExternalPineMeshCount == 3
                ? TEXT("rights_reviewed_cc0_six_rock_and_three_pine_sets_loaded_with_explicit_materials_for_isolated_south_fork_visual_comparison")
                : (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("rights_reviewed_cc0_six_rock_set_loaded_with_explicit_materials_for_isolated_river_visual_comparison")
                       : (Result.bDressingExternalBroadleafReviewAssetLoaded &&
                           Result.bDressingExternalConiferReviewAssetLoaded
                       ? (Result.bDressingExternalBroadleafMaterialsValidated &&
                                  Result.bDressingExternalConiferMaterialsValidated
                              ? TEXT("rights_reviewed_cc0_broadleaf_analog_and_fir_loaded_with_explicit_materials_for_isolated_south_fork_visual_comparison")
                              : TEXT("rights_reviewed_cc0_tree_assets_loaded_but_material_validation_failed"))
                       : TEXT("no_external_review_asset_selected_for_this_river"))),
            Result.DressingExternalRockMeshCount,
            Result.bDressingExternalRockMaterialsValidated
                ? TEXT("six_meshes_nanite_and_material_validated_visual_comparison_only")
                : TEXT("no_reviewed_rock_asset_selected_for_this_river"),
            Result.DressingExternalPineMeshCount,
            Result.bDressingExternalPineMaterialsValidated
                ? TEXT("three_meshes_physical_scale_nanite_and_materials_validated_sparse_visual_comparison_only")
                : TEXT("no_reviewed_pine_asset_selected_for_this_river"),
            *EscapeRaftSimJsonString(
                Result.bDressingExternalConiferReviewAssetLoaded
                    ? Result.DressingConiferAssetPath
                    : FString()),
            *EscapeRaftSimJsonString(
                Result.bDressingExternalBroadleafReviewAssetLoaded
                    ? Result.DressingBroadleafAssetPath
                    : FString()),
            *EscapeRaftSimJsonString(
                Result.bDressingExternalConiferReviewAssetLoaded
                    ? Result.DressingConiferAssetPath
                    : FString()),
            *EscapeRaftSimJsonString(Result.DressingBroadleafAssetPath),
            *EscapeRaftSimJsonString(Result.DressingConiferAssetPath),
            Result.DressingExternalRockMeshCount == 6 && Result.DressingExternalPineMeshCount == 3
                ? TEXT("complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_nanite_rock_and_sparse_three_variant_pine_hierarchical_instancing")
                : (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_nanite_rock_hierarchical_instancing")
                       : (Result.bDressingExternalBroadleafReviewAssetLoaded &&
                           Result.bDressingExternalConiferReviewAssetLoaded
                       ? TEXT("complete_pve_shrub_understory_plus_rights_reviewed_broadleaf_and_fir_hierarchical_instancing_and_dense_irregular_procedural_boulders")
                       : TEXT("complete_pve_species_skeletal_to_static_conversion_plus_hierarchical_instancing_and_dense_irregular_procedural_boulders"))),
            Result.DressingBoulderInstanceCount,
            Result.DressingFoliageInstanceCount,
            Result.DressingCanopyTreeInstanceCount,
            Result.DressingUnderstoryInstanceCount,
            Result.DressingTrunkInstanceCount,
            Result.bDressingSourceMasksLoaded
                ? TEXT("water_and_vegetation_masks_loaded_and_used_for_candidate_selection")
                : TEXT("required_source_masks_missing"),
            Result.bDressingFoliageMaterialsValidated
                ? TEXT("three_river_specific_texture_preserving_two_sided_foliage_slots_bound_one_complete_species_native_material_retained")
                : TEXT("foliage_material_generation_or_binding_failed"),
            Result.DressingFoliageMaterialAssetCount,
            Result.DressingFoliageMaterialBoundSlotCount,
            Result.DressingNativeFoliageMaterialFallbackSlotCount,
            *RiverAssetName,
            *RiverAssetName,
            *RiverAssetName,
            FoliageSettings.BroadleafFrontTint.R,
            FoliageSettings.BroadleafFrontTint.G,
            FoliageSettings.BroadleafFrontTint.B,
            FoliageSettings.BroadleafBackTint.R,
            FoliageSettings.BroadleafBackTint.G,
            FoliageSettings.BroadleafBackTint.B,
            FoliageSettings.BroadleafTransmissionTint.R,
            FoliageSettings.BroadleafTransmissionTint.G,
            FoliageSettings.BroadleafTransmissionTint.B,
            FoliageSettings.ConiferFrontTint.R,
            FoliageSettings.ConiferFrontTint.G,
            FoliageSettings.ConiferFrontTint.B,
            FoliageSettings.ConiferBackTint.R,
            FoliageSettings.ConiferBackTint.G,
            FoliageSettings.ConiferBackTint.B,
            FoliageSettings.ConiferTransmissionTint.R,
            FoliageSettings.ConiferTransmissionTint.G,
            FoliageSettings.ConiferTransmissionTint.B,
            FoliageSettings.RoughnessStrength,
            FoliageSettings.NormalStrength,
            Result.bDressingBoulderMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bDressingBroadleafMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bDressingConiferMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bDressingUnderstoryMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.DressingExternalRockMeshCount == 6 && Result.DressingExternalPineMeshCount == 3
                ? TEXT("rights_reviewed_rock_and_pine_visual_comparison_only_not_geology_ecology_guide_performance_or_gameplay_promoted")
                : (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("rights_reviewed_rock_visual_comparison_only_not_geology_ecology_guide_performance_or_gameplay_promoted")
                       : (Result.bDressingExternalBroadleafReviewAssetLoaded &&
                           Result.bDressingExternalConiferReviewAssetLoaded
                       ? TEXT("rights_reviewed_broadleaf_analog_and_fir_visual_comparison_only_not_species_guide_performance_or_gameplay_promoted")
                       : TEXT("complete_pve_sample_species_geometry_evaluation_only_requires_biome_specific_pve_exports_production_rock_asset_guide_and_performance_review"))),
            Result.bSolverSurfaceWaterMaterialBound
                ? TEXT("solver_surface_default_lit_candidate_bound_and_captured")
                : TEXT("solver_surface_water_generation_or_binding_failed"),
            *EscapeRaftSimJsonString(Result.WaterMaterialPath),
            bHasSolverVisualizationFields
                ? TEXT("validated_cpp_solver_visualization_fields_bound_review_only")
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("disabled_for_physical_corridor_until_solver_grid_georeferencing_is_validated")
                       : TEXT("not_available_for_river_no_cross_river_field_reuse")),
            *EscapeRaftSimJsonString(GetSolverVisualizationFieldManifestRelativePath()),
            bHasSolverVisualizationFields ? 2 : 0,
            bHasSolverVisualizationFields ? TEXT("0") : TEXT("null"),
            WaterSettings.SolverFieldEnable,
            WaterSettings.SolverMacroNormalWeight,
            WaterSettings.SolverDepthColorWeight,
            WaterSettings.SolverFieldRoughnessWeight,
            WaterSettings.SolverFroudeAerationWeight,
            WaterSettings.SolverSpeedVisualGain,
            WaterSettings.SolverFroudeVisualGain,
            WaterSettings.SolverSurfaceReliefScale,
            WaterSettings.SolverSurfaceReliefScale * 400.0f,
            bHasSolverVisualizationFields ? 0.42f : 1.0f,
            bHasSolverVisualizationFields
                ? TEXT("validated_speed_froude_masked_noncolliding_translucent_surface_bound")
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("disabled_until_physical_corridor_solver_grid_georeferencing_is_validated")
                       : TEXT("not_available_without_river_specific_validated_solver_field")),
            bHasSolverVisualizationFields ? 0.72f : 0.0f,
            bHasSolverVisualizationFields ? 1.4f : 0.0f,
            Result.WaterMaterialBoundComponentCount,
            WaterSettings.BaseColorScale,
            WaterSettings.SurfaceTint.R,
            WaterSettings.SurfaceTint.G,
            WaterSettings.SurfaceTint.B,
            WaterSettings.VertexTintWeight,
            WaterSettings.EmissiveFillScale,
            WaterSettings.ReflectionFillIntensity,
            WaterSettings.ReflectionTint.R,
            WaterSettings.ReflectionTint.G,
            WaterSettings.ReflectionTint.B,
            WaterSettings.Roughness,
            WaterSettings.Specular,
            1.0f,
            WaterSettings.NormalIntensity,
            WaterSettings.RefractionIor,
            WaterSettings.PhaseG,
            WaterSettings.ScatteringCoefficients.R,
            WaterSettings.ScatteringCoefficients.G,
            WaterSettings.ScatteringCoefficients.B,
            WaterSettings.AbsorptionCoefficients.R,
            WaterSettings.AbsorptionCoefficients.G,
            WaterSettings.AbsorptionCoefficients.B,
            WaterSettings.ColorScaleBehindWater.R,
            WaterSettings.ColorScaleBehindWater.G,
            WaterSettings.ColorScaleBehindWater.B,
            WaterSettings.RenderWidthScale,
            WaterSettings.RenderNormalUpBlend,
            WaterSettings.RenderDisplacementScale,
            Candidate.bEnableLandscapeNanite
                ? TEXT("nanite_and_static_lighting")
                : TEXT("static_lighting_non_nanite_physical_corridor_review"),
            Result.MaterialBoundComponentCount,
            Result.bMaterialBindingsValidated ? TEXT("all_source_components_bound") : TEXT("source_component_binding_failed"),
            Candidate.bEnableLandscapeNanite ? TEXT("true") : TEXT("false"),
            Result.NaniteComponentCount,
            Result.NaniteMaterialSlotCount,
            Result.NaniteMaterialBoundSlotCount,
            Result.NaniteMaterialAuditErrorCount,
            Candidate.bEnableLandscapeNanite
                ? (Result.bNaniteRepresentationBuilt
                       ? TEXT("enabled_and_built_up_to_date")
                       : TEXT("enabled_candidate_build_failed_or_stale"))
                : TEXT("disabled_for_physical_corridor_after_captured_nanite_hole_regression"));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.landscape_import_candidate_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"isolated_source_landscape_import_geometry_review\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"canonical_importer\": \"Unreal LandscapeEditor PNG heightmap file format\",\n")
        TEXT("  \"candidate_policy\": \"Source DEM values remain authoritative outside explicitly manifest-recorded bounded channel conditioning; candidates cannot replace gameplay or active preview terrain until CRS, vertical datum, hydrologic conditioning, guide, solver, capture, representation, and performance gates pass.\",\n")
        TEXT("  \"candidates\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        bAllSucceeded
            ? (RiverIdFilter.IsEmpty()
                   ? TEXT("six_source_landscape_candidates_captured_review_gated")
                   : TEXT("requested_source_landscape_candidate_captured_review_gated"))
            : TEXT("one_or_more_landscape_candidates_failed"),
        *EntriesJson);
    const FString ManifestFilename = RiverIdFilter.IsEmpty()
        ? TEXT("landscape_candidate_manifest.json")
        : FString::Printf(TEXT("landscape_candidate_manifest_%s.json"), *RiverIdFilter);
    const FString ManifestPath = FPaths::Combine(CandidateCaptureRoot, ManifestFilename);
    const bool bManifestSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s source Landscape candidate manifest -> %s\n"),
        bManifestSaved ? TEXT("Saved") : TEXT("Failed"),
        *ManifestPath);
    return bAllSucceeded && bManifestSaved;
}
