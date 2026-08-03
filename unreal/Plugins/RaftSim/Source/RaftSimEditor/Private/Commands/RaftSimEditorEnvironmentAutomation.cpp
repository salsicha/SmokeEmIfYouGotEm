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
        bSucceeded &= CreateLandscapeImportCandidateMaps(
            Summary,
            LandscapeImportCandidateRiverFilter);
    }

    if (bCreatePhotorealRiverWaterMaterialOnStartup)
    {
        bSucceeded &= RaftSimPhotorealMaterials::CreatePhotorealRiverWaterMaterial(Summary);
    }

    if (bCreateLiveRiverSurfaceMaterialOnStartup)
    {
        bSucceeded &= RaftSimPhotorealMaterials::CreateLiveRiverSurfaceMaterial(Summary);
    }

    if (bCreateWaterVfxMaterialOnStartup)
    {
        bSucceeded &= RaftSimPhotorealMaterials::CreateWaterVfxMaterial(Summary);
    }

    if (bCreateSouthForkFullReachEnvironmentOnStartup)
    {
        bSucceeded &= CreateSouthForkFullReachEnvironment(Summary);
    }

    if (bCaptureSouthForkFullReachEnvironmentOnStartup)
    {
        bSucceeded &= CaptureSouthForkFullReachEnvironment(Summary);
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
    if (RiverIdFilter.IsEmpty())
    {
        bAllSucceeded &= CreateSolverVisualizationFieldTextureAssets(OutSummary);
    }
    else
    {
        OutSummary += TEXT(
            "Reusing reviewed shared solver-field textures for filtered river generation.\n");
    }
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
            BuildLandscapeImportCandidateMap(
                Candidate,
                Result,
                OutSummary,
                !RiverIdFilter.IsEmpty());

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
        const bool bHasRiverSpecificSolverVisualization =
            Candidate.bUseSolverVisualizationFields &&
            (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ||
             !Candidate.SolverVisualizationFieldRelativePath.IsEmpty());
        if (bHasRiverSpecificSolverVisualization)
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
        if ((Candidate.PreviewSpec.RiverId == TEXT("colorado_river") ||
             Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator") ||
             Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon")) &&
            Candidate.bUseSolverVisualizationFields &&
            !Candidate.SolverVisualizationFieldRelativePath.IsEmpty())
        {
            // These reach-local packed fields are already sampled into capture
            // geometry and vertex colours. Their materials must not re-sample
            // the shared South Fork fallback texture on top of those results.
            WaterSettings.SolverFieldEnable = 0.0f;
            WaterSettings.SolverMacroNormalWeight = 0.0f;
            WaterSettings.SolverDepthColorWeight = 0.0f;
            WaterSettings.SolverFieldRoughnessWeight = 0.0f;
            WaterSettings.SolverFroudeAerationWeight = 0.0f;
            WaterSettings.SolverSpeedVisualGain = 0.0f;
            WaterSettings.SolverFroudeVisualGain = 0.0f;
        }
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
            bHasRiverSpecificSolverVisualization;
        const bool bPacuareSolverVisualization =
            bHasSolverVisualizationFields &&
            Candidate.PreviewSpec.RiverId == TEXT("pacuare");
        const bool bColoradoHanceSolverVisualization =
            bHasSolverVisualizationFields &&
            Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
        const bool bChilkoLavaCanyonSolverVisualization =
            bHasSolverVisualizationFields &&
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const bool bFutaleufuTerminatorSolverVisualization =
            bHasSolverVisualizationFields &&
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
        const FString CandidateSolverVisualizationManifest =
            bPacuareSolverVisualization
            ? TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                   "pacuare_upper_huacas_rainfed_visualization_manifest.json")
            : (bColoradoHanceSolverVisualization
                   ? TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                          "colorado_hance_moderate_visualization_manifest.json")
                   : (bChilkoLavaCanyonSolverVisualization
                          ? TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                                 "chilko_lava_canyon_median_visualization_manifest.json")
                          : (bFutaleufuTerminatorSolverVisualization
                                 ? TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                                        "futaleufu_terminator_median_visualization_manifest.json")
                                 : GetSolverVisualizationFieldManifestRelativePath())));
        const bool bHasManifestConditionedPhysicalChannel =
            Candidate.bPhysicalScaleSourceCorridor;
        const bool bUsesOpaqueVolumetricVegetation =
            Result.bDressingUsesOpaqueVolumetricVegetation;
        const bool bUsesZambeziDefaultLitWater =
            Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
        const bool bUsesPacuareRainforestDefaultLitWater =
            Candidate.PreviewSpec.RiverId == TEXT("pacuare");
        const bool bUsesColoradoHanceDefaultLitWater =
            Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
        const bool bUsesFutaleufuTerminatorDefaultLitWater =
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
        const bool bUsesChilkoLavaCanyonDefaultLitWater =
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const bool bUsesSingleLayerWater = false;
        const bool bUsesTransmittingDefaultLitWater =
            bUsesColoradoHanceDefaultLitWater ||
            bUsesFutaleufuTerminatorDefaultLitWater;
        const bool bUsesPacuareOrganicRainforestSurface =
            Candidate.PreviewSpec.RiverId == TEXT("pacuare");
        const bool bUsesSouthForkOrganicFoothillSurface =
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork");
        const bool bUsesColoradoOrganicHanceSurface =
            Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
        const bool bUsesFutaleufuOrganicTemperateSurface =
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
        const bool bUsesChilkoOrganicLavaCanyonSurface =
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const bool bUsesDefaultLitLandscape =
            bUsesSouthForkOrganicFoothillSurface ||
            bUsesPacuareOrganicRainforestSurface ||
            Candidate.PreviewSpec.RiverId == TEXT("colorado_river") ||
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator") ||
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const bool bUsesReachLocalReferenceGameplay =
            Candidate.PreviewSpec.RiverId == TEXT("pacuare") ||
            Candidate.PreviewSpec.RiverId == TEXT("colorado_river") ||
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator") ||
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const FString WaterMaterialParentPath = bUsesZambeziDefaultLitWater
            ? TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Materials/M_RaftSim_Zambezi_DefaultLitWater")
            : (bUsesPacuareRainforestDefaultLitWater
                   ? TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Materials/M_RaftSim_Pacuare_RainforestDefaultLitWater")
                   : (bUsesColoradoHanceDefaultLitWater
                          ? TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/M_RaftSim_Colorado_HanceDefaultLitWater")
                          : (bUsesFutaleufuTerminatorDefaultLitWater
                          ? TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/M_RaftSim_Futaleufu_TerminatorDefaultLitWater")
                          : (bUsesChilkoLavaCanyonDefaultLitWater
                                 ? TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Materials/M_RaftSim_Chilko_LavaCanyonDefaultLitWater")
                                 : TEXT("/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate")))));
        const FString WaterSingleLayerParameterKeyPrefix =
            bUsesSingleLayerWater
            ? TEXT("water_single_layer")
            : bUsesTransmittingDefaultLitWater
            ? TEXT("water_transmission")
            : TEXT("water_inactive_single_layer");
        const FString WaterSingleLayerParametersJson = FString::Printf(
            TEXT("      \"%s_refraction_ior\": %.6f,\n")
            TEXT("      \"%s_phase_g\": %.6f,\n")
            TEXT("      \"%s_scattering_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"%s_absorption_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"%s_color_scale_behind_water\": [%.6f, %.6f, %.6f],\n"),
            *WaterSingleLayerParameterKeyPrefix,
            WaterSettings.RefractionIor,
            *WaterSingleLayerParameterKeyPrefix,
            WaterSettings.PhaseG,
            *WaterSingleLayerParameterKeyPrefix,
            WaterSettings.ScatteringCoefficients.R,
            WaterSettings.ScatteringCoefficients.G,
            WaterSettings.ScatteringCoefficients.B,
            *WaterSingleLayerParameterKeyPrefix,
            WaterSettings.AbsorptionCoefficients.R,
            WaterSettings.AbsorptionCoefficients.G,
            WaterSettings.AbsorptionCoefficients.B,
            *WaterSingleLayerParameterKeyPrefix,
            WaterSettings.ColorScaleBehindWater.R,
            WaterSettings.ColorScaleBehindWater.G,
            WaterSettings.ColorScaleBehindWater.B);
        const FString WaterNormalProjectionManifestJson = bUsesZambeziDefaultLitWater
            ? TEXT(
                  "      \"water_normal_primary_uv_tiling\": [2.400000, 6.200000],\n"
                  "      \"water_normal_secondary_uv_tiling\": [4.100000, 10.300000],\n"
                  "      \"water_normal_secondary_coordinate_policy\": \"uv_axes_swapped_for_cross_current_breakup\",\n")
            : bUsesColoradoHanceDefaultLitWater
            ? TEXT(
                  "      \"water_normal_primary_uv_tiling\": [0.570000, 1.590000],\n"
                  "      \"water_normal_secondary_uv_tiling\": [1.190000, 2.830000],\n"
                  "      \"water_normal_secondary_coordinate_policy\": \"shared_uv_axes_opposed_flow\",\n")
            : TEXT(
                  "      \"water_normal_primary_uv_tiling\": [0.730000, 2.150000],\n"
                  "      \"water_normal_secondary_uv_tiling\": [1.110000, 3.300000],\n"
                  "      \"water_normal_secondary_coordinate_policy\": \"shared_uv_axes\",\n");
        const FString WaterNormalSamplingPolicy =
            bUsesColoradoHanceDefaultLitWater
            ? TEXT("river_local_mirrored_dual_scale_uv_samples")
            : TEXT("half_period_dual_sample_crossfade_prevents_frac_tile_boundaries");
        const FString DressingSourceSpeciesJson = bUsesOpaqueVolumetricVegetation
            ? TEXT("[]")
            : TEXT("[\"/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/PVE_Deciduous_Tree_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/PVE_Conifer_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/Deciduous_Shrub_01/PVE_Deciduous_Shrub_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/PVE_Plant_01\"]");
        const FString DressingConvertedSpeciesJson =
            bUsesOpaqueVolumetricVegetation
            ? ((bUsesFutaleufuOrganicTemperateSurface ||
                bUsesChilkoOrganicLavaCanyonSurface)
                   ? FString::Printf(
                         TEXT("[\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\"]"),
                         *EscapeRaftSimJsonString(Result.DressingBroadleafAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingBroadleafVariantAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingConiferAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingConiferVariantAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingShrubAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingShrubVariantAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingUnderstoryAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingUnderstoryVariantAssetPath))
                   : FString::Printf(
                         TEXT("[\"%s\", \"%s\", \"%s\", \"%s\"]"),
                         *EscapeRaftSimJsonString(Result.DressingBroadleafAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingConiferAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingShrubAssetPath),
                         *EscapeRaftSimJsonString(Result.DressingUnderstoryAssetPath)))
            : TEXT("[\"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static\", \"/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static\"]");
        const FString DefaultBroadleafMaterialAsset = FString::Printf(
            TEXT("/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Broadleaf_BiomeFoliageCandidate"),
            *RiverAssetName);
        const FString DefaultConiferMaterialAsset = FString::Printf(
            TEXT("/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Conifer_BiomeFoliageCandidate"),
            *RiverAssetName);
        const FString DefaultUnderstoryMaterialAsset = FString::Printf(
            TEXT("/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Understory_BiomeFoliageCandidate"),
            *RiverAssetName);
        const FString PacuareWaterDecisionJson = bUsesPacuareRainforestDefaultLitWater
            ? TEXT(
                  "      \"water_single_layer_capture_decision\": \"rejected_on_pacuare_after_direct_material_isolation_and_procedural_reference_infill_bathymetry_bracket\",\n"
                  "      \"water_single_layer_failure_artifact\": \"hard_near_camera_horizontal_depth_composition_band\",\n"
                  "      \"water_conditioned_bathymetry_bracket_status\": \"rejected_did_not_remove_foreground_band_or_river_right_white_patch\",\n"
                  "      \"water_conditioned_bathymetry_active\": false,\n"
                  "      \"water_conditioned_bathymetry_authority\": \"none_rejected_procedural_reference_infill_was_never_collision_solver_survey_or_promoted_geometry\",\n")
            : TEXT(
                  "      \"water_single_layer_capture_decision\": \"not_re_evaluated_by_pacuare_bracket\",\n"
                  "      \"water_single_layer_failure_artifact\": null,\n"
                  "      \"water_conditioned_bathymetry_bracket_status\": \"not_active_for_river\",\n"
                  "      \"water_conditioned_bathymetry_active\": false,\n"
                  "      \"water_conditioned_bathymetry_authority\": \"none\",\n");

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
            TEXT("      \"world_vertical_offset_cm\": %.3f,\n")
            TEXT("      \"source_aligned_centerline\": \"%s\",\n")
            TEXT("      \"terrain_render_authority\": \"%s\",\n")
            TEXT("      \"runnable_gameplay_status\": \"%s\",\n")
            TEXT("      \"landscape_material_status\": \"source_conditioned_macro_zones_plus_first_party_close_range_detail_review_candidate\",\n")
            TEXT("      \"landscape_material_shading_model\": \"%s\",\n")
            TEXT("      \"landscape_material_organic_surface_status\": \"%s\",\n")
            TEXT("      \"landscape_material_organic_world_noise_scales_per_cm\": %s,\n")
            TEXT("      \"landscape_material_geometry_authority_status\": \"shade_only_no_world_position_offset_no_collision_or_solver_change\",\n")
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
            TEXT("      \"landscape_dressing_source_species_skeletal_assets\": %s,\n")
            TEXT("      \"landscape_dressing_converted_species_static_assets\": %s,\n")
            TEXT("      \"landscape_dressing_broadleaf_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_conifer_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_shrub_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_understory_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_broadleaf_variant_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_conifer_variant_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_shrub_variant_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_understory_variant_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_temperate_morphology_mesh_count\": %d,\n")
            TEXT("      \"landscape_dressing_trunk_asset\": null,\n")
            TEXT("      \"landscape_dressing_instance_implementation\": \"%s\",\n")
            TEXT("      \"landscape_dressing_boulder_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_temperate_waterline_authority\": \"presentation_only_procedural_source_gap_fill_no_lithology_collision_bathymetry_hydraulic_or_raft_force_authority\",\n")
            TEXT("      \"landscape_dressing_temperate_waterline_target_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_rejected_placement_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_minimum_centerline_distance_cm\": %.3f,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_maximum_slope_degrees\": %.3f,\n")
            TEXT("      \"landscape_dressing_temperate_waterline_target_height_range_m\": [0.22, 2.60],\n")
            TEXT("      \"landscape_dressing_temperate_waterline_placement_contract\": \"deterministic_72_candidate_source_landscape_search_across_both_full_route_banks_outside_complete_visible_water_width_with_full_centerline_clearance_dry_height_and_hard_slope_gates\",\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_authority\": \"presentation_only_procedural_source_gap_fill_no_species_survey_collision_hydraulic_or_raft_force_authority\",\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_target_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_rejected_placement_count\": %d,\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_minimum_centerline_distance_cm\": %.3f,\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_maximum_slope_degrees\": %.3f,\n")
            TEXT("      \"landscape_dressing_temperate_near_bank_placement_contract\": \"deterministic_64_candidate_source_landscape_search_across_both_full_route_dry_banks_outside_complete_visible_water_width_with_full_centerline_clearance_dry_height_and_hard_slope_gates\",\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_authority\": \"presentation_only_generic_rock_analog_no_lithology_collision_hydraulic_or_raft_force_authority\",\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_target_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_rejected_placement_count\": %d,\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_maximum_slope_degrees\": %.3f,\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_target_height_range_m\": [0.95, 5.20],\n")
            TEXT("      \"landscape_dressing_runnable_launch_talus_placement_contract\": \"deterministic_128_candidate_search_approximately_118m_to_993m_downstream_with_full_route_clearance_dry_height_and_hard_slope_gates\",\n")
            TEXT("      \"landscape_dressing_foliage_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_canopy_tree_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_understory_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_trunk_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_source_mask_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_foliage_material_bound_slot_count\": %d,\n")
            TEXT("      \"landscape_dressing_native_foliage_material_fallback_slot_count\": %d,\n")
            TEXT("      \"landscape_dressing_broadleaf_material_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_conifer_material_asset\": \"%s\",\n")
            TEXT("      \"landscape_dressing_understory_material_asset\": \"%s\",\n")
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
            TEXT("%s")
            TEXT("      \"water_material_status\": \"%s\",\n")
            TEXT("      \"water_material_asset\": \"%s\",\n")
            TEXT("      \"water_material_parent\": \"%s\",\n")
            TEXT("      \"water_shading_model\": \"%s\",\n")
            TEXT("      \"water_blend_mode\": \"%s\",\n")
            TEXT("      \"water_custom_output\": \"%s\",\n")
            TEXT("      \"water_volume_parameter_status\": \"%s\",\n")
            TEXT("      \"water_normal_source\": \"river_specific_first_party_normal_atlas_or_standalone_texture_plus_cpu_authored_reach_local_or_validated_shader_solver_field\",\n")
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
            TEXT("      \"water_surface_variation_strength\": %.6f,\n")
            TEXT("      \"water_normal_atlas_sampling_policy\": \"%s\",\n")
            TEXT("      \"water_normal_atlas_phase_offset\": %.6f,\n")
            TEXT("%s")
            TEXT("%s")
            TEXT("      \"water_render_width_scale\": %.6f,\n")
            TEXT("      \"water_render_normal_up_blend\": %.6f,\n")
            TEXT("      \"water_render_displacement_scale\": %.6f,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_enabled\": false,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_policy\": \"disabled_for_solver_surface_water_candidates_legacy_diagnostic_branch_retained\",\n")
            TEXT("      \"water_geometry_authority\": \"custom_cpp_solver_informed_ribbon_geometry_and_vertex_flow_cues_no_visual_forcing_authority\",\n")
            TEXT("      \"waterbody_dependency\": \"%s\",\n")
            TEXT("      \"water_reflection_capture_policy\": \"%s\",\n")
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
            TEXT("      \"promotion_status\": \"%s\"\n")
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
            bHasRiverSpecificSolverVisualization
                ? (bSolverRapidCaptured
                       ? (bPacuareSolverVisualization
                              ? TEXT("captured_at_upper_huacas_cooked_field_hydraulic_crux")
                              : TEXT("captured_at_validated_median_field_high_froude_approach"))
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
            Candidate.WorldVerticalOffsetCm,
            *EscapeRaftSimJsonString(Candidate.LocalCenterlineRelativePath),
            Candidate.bUseDensePhysicalTerrainRenderSurface
                ? TEXT("hidden_landscape_collision_and_height_query_plus_noncolliding_dense_render_tiles")
                : TEXT("visible_reach_local_landscape_owns_rendering_collision_and_height_queries"),
            bUsesReachLocalReferenceGameplay
                ? (Candidate.PreviewSpec.RiverId == TEXT("pacuare")
                       ? TEXT("reference_runnable_upper_huacas_live_cooked_water_player_raft_and_game_mode")
                       : (Candidate.PreviewSpec.RiverId == TEXT("colorado_river")
                              ? TEXT("reference_runnable_colorado_hance_live_cooked_water_player_raft_and_game_mode")
                              : (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator")
                                     ? TEXT("reference_runnable_futaleufu_terminator_live_cooked_water_player_raft_and_game_mode")
                                     : TEXT("reference_runnable_chilko_lava_canyon_live_cooked_water_player_raft_and_game_mode"))))
                : (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge")
                       ? TEXT("reference_runnable_full_corridor_live_cooked_water_player_raft_and_game_mode")
                       : TEXT("capture_candidate_only")),
            bUsesDefaultLitLandscape
                ? TEXT("DefaultLit")
                : TEXT("Unlit"),
            bUsesSouthForkOrganicFoothillSurface
                ? TEXT("south_fork_v1_three_scale_world_space_dry_grass_oak_litter_granitic_soil_and_slope_aware_weathered_granite_response")
                : (bUsesPacuareOrganicRainforestSurface
                ? TEXT("pacuare_v1_three_scale_world_space_canopy_soil_moss_leaf_litter_and_slope_aware_wet_rock_response")
                : (bUsesColoradoOrganicHanceSurface
                       ? TEXT("colorado_hance_v1_four_scale_world_space_sandy_bench_weathered_iron_cliff_dark_rock_talus_and_fine_grain_response")
                       : (bUsesFutaleufuOrganicTemperateSurface
                       ? TEXT("futaleufu_v1_three_scale_world_space_forest_floor_moss_leaf_litter_and_slope_aware_wet_granite_response")
                       : (bUsesChilkoOrganicLavaCanyonSurface
                              ? TEXT("chilko_v1_four_scale_world_space_open_bench_dry_grass_mineral_soil_slope_aware_basalt_and_scree_response")
                              : TEXT("not_enabled_for_this_river"))))),
            bUsesSouthForkOrganicFoothillSurface
                ? TEXT("[0.000130, 0.000730, 0.003100]")
                : (bUsesPacuareOrganicRainforestSurface
                ? TEXT("[0.000210, 0.000950, 0.003500]")
                : (bUsesColoradoOrganicHanceSurface
                       ? TEXT("[0.000140, 0.000530, 0.002300, 0.006800]")
                       : (bUsesFutaleufuOrganicTemperateSurface
                       ? TEXT("[0.000180, 0.000710, 0.004200]")
                       : (bUsesChilkoOrganicLavaCanyonSurface
                              ? TEXT("[0.000160, 0.000590, 0.002700, 0.007900]")
                              : TEXT("[]"))))),
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
                ? (bUsesOpaqueVolumetricVegetation
                       ? TEXT("source_mask_placed_project_owned_opaque_volumetric_vegetation_and_rock_dressing_captured")
                       : bUsesColoradoOrganicHanceSurface
                       ? TEXT("source_grounded_project_owned_opaque_hance_dryland_ground_cover_shrubs_and_rock_dressing_captured_zero_legacy_pve_instances")
                       : Result.DressingExternalRockMeshCount == 6
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
            *DressingSourceSpeciesJson,
            *DressingConvertedSpeciesJson,
            *EscapeRaftSimJsonString(Result.DressingBroadleafAssetPath),
            *EscapeRaftSimJsonString(Result.DressingConiferAssetPath),
            *EscapeRaftSimJsonString(Result.DressingShrubAssetPath),
            *EscapeRaftSimJsonString(Result.DressingUnderstoryAssetPath),
            *EscapeRaftSimJsonString(Result.DressingBroadleafVariantAssetPath),
            *EscapeRaftSimJsonString(Result.DressingConiferVariantAssetPath),
            *EscapeRaftSimJsonString(Result.DressingShrubVariantAssetPath),
            *EscapeRaftSimJsonString(Result.DressingUnderstoryVariantAssetPath),
            (bUsesFutaleufuOrganicTemperateSurface ||
             bUsesChilkoOrganicLavaCanyonSurface)
                ? 8
                : 0,
            bUsesOpaqueVolumetricVegetation
                ? TEXT("project_owned_opaque_volumetric_nanite_species_hierarchical_instancing_plus_river_specific_rock_dressing")
                : bUsesColoradoOrganicHanceSurface
                ? TEXT("project_owned_opaque_hance_dryland_ground_cover_and_shrub_hierarchical_instancing_zero_legacy_pve_instances_plus_dense_irregular_procedural_boulders")
                : Result.DressingExternalRockMeshCount == 6 && Result.DressingExternalPineMeshCount == 3
                ? TEXT("complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_nanite_rock_and_sparse_three_variant_pine_hierarchical_instancing")
                : (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_nanite_rock_hierarchical_instancing")
                       : (Result.bDressingExternalBroadleafReviewAssetLoaded &&
                           Result.bDressingExternalConiferReviewAssetLoaded
                       ? TEXT("complete_pve_shrub_understory_plus_rights_reviewed_broadleaf_and_fir_hierarchical_instancing_and_dense_irregular_procedural_boulders")
                       : TEXT("complete_pve_species_skeletal_to_static_conversion_plus_hierarchical_instancing_and_dense_irregular_procedural_boulders"))),
            Result.DressingBoulderInstanceCount,
            Result.DressingTemperateWaterlineTargetInstanceCount > 0
                ? TEXT("source_grounded_rights_reviewed_cc0_six_variant_organic_waterline_structure_v1_captured")
                : TEXT("not_enabled_for_this_river"),
            Result.DressingTemperateWaterlineTargetInstanceCount,
            Result.DressingTemperateWaterlineInstanceCount,
            Result.DressingTemperateWaterlineRejectedPlacementCount,
            Result.DressingTemperateWaterlineMinimumCenterlineDistanceCm,
            Result.DressingTemperateWaterlineMaximumSlopeDegrees,
            Result.DressingTemperateNearBankTargetInstanceCount > 0
                ? TEXT("source_grounded_dry_bank_grass_forb_shrub_ecology_v4_captured")
                : TEXT("not_enabled_for_this_river"),
            Result.DressingTemperateNearBankTargetInstanceCount,
            Result.DressingTemperateNearBankInstanceCount,
            Result.DressingTemperateNearBankRejectedPlacementCount,
            Result.DressingTemperateNearBankMinimumCenterlineDistanceCm,
            Result.DressingTemperateNearBankMaximumSlopeDegrees,
            Result.DressingRunnableLaunchTalusTargetInstanceCount > 0
                ? TEXT("source_grounded_rights_reviewed_cc0_six_variant_launch_talus_captured")
                : TEXT("not_enabled_for_this_river"),
            Result.DressingRunnableLaunchTalusTargetInstanceCount,
            Result.DressingRunnableLaunchTalusInstanceCount,
            Result.DressingRunnableLaunchTalusRejectedPlacementCount,
            Result.DressingRunnableLaunchTalusMaximumSlopeDegrees,
            Result.DressingFoliageInstanceCount,
            Result.DressingCanopyTreeInstanceCount,
            Result.DressingUnderstoryInstanceCount,
            Result.DressingTrunkInstanceCount,
            Result.bDressingSourceMasksLoaded
                ? TEXT("water_and_vegetation_masks_loaded_and_used_for_candidate_selection")
                : TEXT("required_source_masks_missing"),
            Result.bDressingFoliageMaterialsValidated
                ? (bUsesOpaqueVolumetricVegetation
                       ? ((bUsesFutaleufuOrganicTemperateSurface ||
                           bUsesChilkoOrganicLavaCanyonSurface)
                              ? TEXT("one_project_owned_opaque_one_sided_vertex_color_material_bound_to_eight_volumetric_morphology_meshes_no_alpha_cards")
                              : TEXT("one_project_owned_opaque_one_sided_vertex_color_material_bound_to_four_volumetric_species_no_alpha_cards"))
                       : bUsesColoradoOrganicHanceSurface
                       ? TEXT("three_legacy_pve_material_assets_retained_with_zero_instances_plus_one_project_owned_opaque_one_sided_hance_dryland_material_bound_to_ground_cover_and_shrub_forms")
                       : TEXT("three_river_specific_texture_preserving_two_sided_foliage_slots_bound_one_complete_species_native_material_retained"))
                : TEXT("foliage_material_generation_or_binding_failed"),
            Result.DressingFoliageMaterialAssetCount,
            Result.DressingFoliageMaterialBoundSlotCount,
            Result.DressingNativeFoliageMaterialFallbackSlotCount,
            *EscapeRaftSimJsonString(
                bUsesOpaqueVolumetricVegetation
                    ? Result.DressingFoliageMaterialAssetPath
                    : DefaultBroadleafMaterialAsset),
            *EscapeRaftSimJsonString(
                bUsesOpaqueVolumetricVegetation
                    ? Result.DressingFoliageMaterialAssetPath
                    : DefaultConiferMaterialAsset),
            *EscapeRaftSimJsonString(
                bUsesOpaqueVolumetricVegetation
                    ? Result.DressingFoliageMaterialAssetPath
                    : DefaultUnderstoryMaterialAsset),
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
            bUsesOpaqueVolumetricVegetation
                ? TEXT("opaque_volumetric_procedural_fallback_removes_alpha_card_artifacts_but_requires_species_ecology_guide_visual_and_performance_review")
                : bUsesColoradoOrganicHanceSurface
                ? TEXT("opaque_hance_dryland_gap_fill_replaces_the_legacy_bench_band_but_requires_exact_species_ecology_guide_visual_and_performance_review")
                : Result.DressingExternalRockMeshCount == 6 && Result.DressingExternalPineMeshCount == 3
                ? TEXT("rights_reviewed_rock_and_pine_visual_comparison_only_not_geology_ecology_guide_performance_or_gameplay_promoted")
                : (Result.DressingExternalRockMeshCount == 6
                       ? TEXT("rights_reviewed_rock_visual_comparison_only_not_geology_ecology_guide_performance_or_gameplay_promoted")
                       : (Result.bDressingExternalBroadleafReviewAssetLoaded &&
                           Result.bDressingExternalConiferReviewAssetLoaded
                       ? TEXT("rights_reviewed_broadleaf_analog_and_fir_visual_comparison_only_not_species_guide_performance_or_gameplay_promoted")
                       : TEXT("complete_pve_sample_species_geometry_evaluation_only_requires_biome_specific_pve_exports_production_rock_asset_guide_and_performance_review"))),
            *PacuareWaterDecisionJson,
            Result.bSolverSurfaceWaterMaterialBound
                ? (bUsesZambeziDefaultLitWater
                       ? TEXT("zambezi_default_lit_moving_surface_candidate_bound_after_single_layer_capture_rejection")
                       : (bUsesPacuareRainforestDefaultLitWater
                              ? TEXT("pacuare_rainforest_default_lit_candidate_bound_after_single_layer_capture_rejection")
                              : (bUsesColoradoHanceDefaultLitWater
                                     ? TEXT("colorado_hance_transmitting_default_lit_river_local_normal_candidate_bound_cpu_depth_bank_opacity_and_cooked_field_color")
                                     : (bUsesFutaleufuTerminatorDefaultLitWater
                                     ? TEXT("futaleufu_terminator_transmitting_default_lit_river_local_normal_candidate_bound_cpu_depth_bank_opacity_and_cooked_field_color")
                                     : (bUsesChilkoLavaCanyonDefaultLitWater
                                            ? TEXT("chilko_lava_canyon_default_lit_native_moving_normal_candidate_bound_cpu_cooked_field_color")
                                            : TEXT("solver_surface_default_lit_candidate_bound_and_captured"))))))
                : TEXT("solver_surface_water_generation_or_binding_failed"),
            *EscapeRaftSimJsonString(Result.WaterMaterialPath),
            *EscapeRaftSimJsonString(WaterMaterialParentPath),
            bUsesSingleLayerWater ? TEXT("SingleLayerWater") : TEXT("DefaultLit"),
            bUsesTransmittingDefaultLitWater
                ? TEXT("Translucent")
                : TEXT("Opaque"),
            bUsesSingleLayerWater
                ? TEXT("SingleLayerWaterMaterialOutput_scattering_absorption_phase_and_behind_water_scale")
                : (bUsesTransmittingDefaultLitWater
                       ? TEXT("none_default_lit_depth_bank_transmission_and_physical_ior")
                       : TEXT("none_surface_only_solver_conditioned_shading")),
            bUsesSingleLayerWater
                ? TEXT("active_on_zambezi_isolated_parent")
                : bUsesTransmittingDefaultLitWater
                ? TEXT("active_default_lit_transmission_parameters_and_refraction")
                : TEXT("inactive_single_layer_evaluation_values_retained_in_manifest_only"),
            bHasSolverVisualizationFields
                ? (bPacuareSolverVisualization
                       ? TEXT("pacuare_cooked_field_capture_visualization_bound_review_only_not_production_promoted")
                       : bColoradoHanceSolverVisualization
                       ? TEXT("colorado_hance_cooked_field_capture_visualization_bound_review_only_not_production_promoted")
                       : bChilkoLavaCanyonSolverVisualization
                       ? TEXT("chilko_lava_canyon_cooked_field_capture_visualization_bound_review_only_not_production_promoted")
                       : bFutaleufuTerminatorSolverVisualization
                       ? TEXT("futaleufu_terminator_cooked_field_capture_visualization_bound_review_only_not_production_promoted")
                       : TEXT("validated_cpp_solver_visualization_fields_bound_review_only"))
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("disabled_for_physical_corridor_until_solver_grid_georeferencing_is_validated")
                       : TEXT("not_available_for_river_no_cross_river_field_reuse")),
            *EscapeRaftSimJsonString(CandidateSolverVisualizationManifest),
            bHasSolverVisualizationFields
                ? (!Candidate.SolverVisualizationFieldRelativePath.IsEmpty() ? 1 : 2)
                : 0,
            bHasSolverVisualizationFields ? TEXT("0") : TEXT("null"),
            WaterSettings.SolverFieldEnable,
            WaterSettings.SolverMacroNormalWeight,
            WaterSettings.SolverDepthColorWeight,
            WaterSettings.SolverFieldRoughnessWeight,
            WaterSettings.SolverFroudeAerationWeight,
            WaterSettings.SolverSpeedVisualGain,
            WaterSettings.SolverFroudeVisualGain,
            WaterSettings.SolverSurfaceReliefScale,
            Candidate.SolverVisualizationSurfaceReliefCapM * 100.0f *
                WaterSettings.SolverSurfaceReliefScale,
            bHasSolverVisualizationFields ? 0.22f : 1.0f,
            bHasSolverVisualizationFields
                ? (!Candidate.SolverVisualizationFieldRelativePath.IsEmpty()
                       ? TEXT("capture_only_cooked_speed_froude_masked_noncolliding_surface_bound_hidden_in_game")
                       : TEXT("validated_speed_froude_masked_noncolliding_translucent_surface_bound"))
                : (Candidate.bPhysicalScaleSourceCorridor
                       ? TEXT("disabled_until_physical_corridor_solver_grid_georeferencing_is_validated")
                       : TEXT("not_available_without_river_specific_validated_solver_field")),
            bHasSolverVisualizationFields
                ? (!Candidate.SolverVisualizationFieldRelativePath.IsEmpty() ? 0.94f : 0.72f)
                : 0.0f,
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
            (bUsesSingleLayerWater || bUsesTransmittingDefaultLitWater)
                ? WaterSettings.Opacity
                : 1.0f,
            WaterSettings.NormalIntensity,
            WaterSettings.SurfaceVariationStrength,
            *WaterNormalSamplingPolicy,
            bUsesColoradoHanceDefaultLitWater ? 0.0f : 0.5f,
            *WaterNormalProjectionManifestJson,
            *WaterSingleLayerParametersJson,
            WaterSettings.RenderWidthScale,
            WaterSettings.RenderNormalUpBlend,
            WaterSettings.RenderDisplacementScale,
            bUsesSingleLayerWater
                ? TEXT("none_single_layer_water_runs_on_generated_procedural_mesh_ribbon")
                : TEXT("none_default_lit_solver_surface_runs_on_generated_procedural_mesh_ribbon"),
            bUsesSingleLayerWater
                ? TEXT("single_layer_water_uses_movable_skylight_runtime_corridor_sphere_capture_screen_space_reflections_volume_transmission_and_bounded_fresnel_sky_fill")
                : TEXT("default_lit_surface_uses_movable_skylight_runtime_corridor_sphere_capture_screen_space_reflections_and_bounded_fresnel_sky_fill"),
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
                : TEXT("disabled_for_physical_corridor_after_captured_nanite_hole_regression"),
            bUsesReachLocalReferenceGameplay || bUsesZambeziDefaultLitWater
                ? TEXT("reference_runnable_gameplay_photoreal_and_production_promotion_review_gated")
                : TEXT("review_gated_isolated_candidate_not_enabled_for_gameplay_or_active_previews"));
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
