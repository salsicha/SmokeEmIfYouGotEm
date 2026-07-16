#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
bool BuildLandscapeImportCandidateMap(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary)
{
    const int32 LandscapeSize = Candidate.LandscapeSize;
    const int32 LandscapeQuads = LandscapeSize - 1;
    const int32 NumSubsections = Candidate.bPhysicalScaleSourceCorridor ? 2 : 1;
    constexpr int32 SubsectionSizeQuads = 63;
    constexpr float MinX = -5800.0f;

    const FString HeightfieldAbsolutePath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), Candidate.HeightfieldRelativePath));
    if (!FPaths::FileExists(HeightfieldAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing Landscape heightfield: %s\n"), *HeightfieldAbsolutePath);
        return false;
    }

    ILandscapeEditorModule& LandscapeEditorModule =
        FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
    const ILandscapeHeightmapFileFormat* HeightmapFormat =
        LandscapeEditorModule.GetHeightmapFormatByExtension(TEXT(".png"));
    if (!HeightmapFormat)
    {
        OutSummary += TEXT("Unreal LandscapeEditor did not register a PNG heightmap importer.\n");
        return false;
    }

    const FLandscapeHeightmapInfo HeightmapInfo = HeightmapFormat->Validate(*HeightfieldAbsolutePath);
    if (HeightmapInfo.ResultCode == ELandscapeImportResult::Error)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield validation failed for %s: %s\n"),
            *Candidate.PreviewSpec.RiverId,
            *HeightmapInfo.ErrorMessage.ToString());
        return false;
    }

    const FLandscapeFileResolution ExpectedResolution(LandscapeSize, LandscapeSize);
    if (!HeightmapInfo.PossibleResolutions.Contains(ExpectedResolution))
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield %s does not advertise the required %dx%d resolution.\n"),
            *Candidate.HeightfieldRelativePath,
            LandscapeSize,
            LandscapeSize);
        return false;
    }

    FLandscapeHeightmapImportData ImportedHeightmap =
        HeightmapFormat->Import(*HeightfieldAbsolutePath, ExpectedResolution);
    if (ImportedHeightmap.ResultCode == ELandscapeImportResult::Error ||
        ImportedHeightmap.Data.Num() != LandscapeSize * LandscapeSize)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield import failed for %s: %s (%d samples).\n"),
            *Candidate.PreviewSpec.RiverId,
            *ImportedHeightmap.ErrorMessage.ToString(),
            ImportedHeightmap.Data.Num());
        return false;
    }

    OutResult.SourceHeightMin = MAX_uint16;
    OutResult.SourceHeightMax = 0;
    for (uint16 Height : ImportedHeightmap.Data)
    {
        OutResult.SourceHeightMin = FMath::Min(OutResult.SourceHeightMin, Height);
        OutResult.SourceHeightMax = FMath::Max(OutResult.SourceHeightMax, Height);
    }
    const int32 SourceRange = static_cast<int32>(OutResult.SourceHeightMax) -
        static_cast<int32>(OutResult.SourceHeightMin);
    if (Candidate.bApplyPreviewAnalyticChannelBurn)
    {
        OutResult.ChannelFloor = static_cast<uint16>(FMath::Clamp(
            static_cast<int32>(OutResult.SourceHeightMin) +
                FMath::RoundToInt(static_cast<float>(SourceRange) * 0.12f),
            0,
            65535));
        ApplyPreviewOnlyLandscapeChannelBurn(
            Candidate,
            OutResult.ChannelFloor,
            ImportedHeightmap.Data,
            OutResult.ChannelModifiedSampleCount);
    }
    else
    {
        OutResult.ChannelFloor = OutResult.SourceHeightMin;
        OutResult.ChannelModifiedSampleCount = 0;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to create Landscape candidate map for %s.\n"), *Candidate.PreviewSpec.RiverId);
        return false;
    }

    UMaterialInterface* LandscapeMaterial = LoadOrCreateLandscapeCandidateMaterial(Candidate, OutSummary);
    if (!LandscapeMaterial)
    {
        return false;
    }
    UMaterialInterface* CandidateWaterMaterial =
        LoadOrCreateLandscapeCandidateWaterMaterial(
            Candidate.PreviewSpec,
            OutSummary,
            !Candidate.bUseSolverVisualizationFields);
    if (!CandidateWaterMaterial)
    {
        return false;
    }
    const FRaftSimLandscapeCandidateWaterSettings CandidateWaterSettings =
        GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
    FRaftSimPreviewImage SolverVisualizationFields;
    const FRaftSimPreviewImage* SolverVisualizationFieldsPtr = nullptr;
    UMaterialInterface* SolverFoamMaterial = nullptr;
    if (Candidate.bUseSolverVisualizationFields && CandidateWaterSettings.SolverFieldEnable > 0.5f)
    {
        const FString SolverFieldImage =
            TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                 "american_south_fork_median_cpp_solver_depth_speed_froude_v1.png");
        if (!LoadPreviewPngImage(SolverFieldImage, SolverVisualizationFields))
        {
            OutSummary += FString::Printf(
                TEXT("Failed to load solver render-geometry fields for %s.\n"),
                *Candidate.PreviewSpec.RiverId);
            return false;
        }
        SolverVisualizationFieldsPtr = &SolverVisualizationFields;
        SolverFoamMaterial = LoadOrCreateLandscapeCandidateSolverFoamMaterial(OutSummary);
        if (!SolverFoamMaterial)
        {
            return false;
        }
    }
    const float ScaleX = Candidate.HorizontalSpanXCm / static_cast<float>(LandscapeQuads);
    const float ScaleY = Candidate.HorizontalSpanYCm / static_cast<float>(LandscapeQuads);
    const float ScaleZ = Candidate.TargetReliefCm / 512.0f;
    const float EncodedChannelFloorCm =
        (static_cast<float>(OutResult.ChannelFloor) - 32768.0f) / 128.0f * ScaleZ;
    const float ChannelBedWorldZ = Candidate.bPhysicalScaleSourceCorridor
        ? 0.0f
        : Candidate.PreviewSpec.FlowWaterLevelOffsetCm - 24.0f;
    OutResult.LandscapeLocation = FVector(
        MinX,
        -Candidate.HorizontalSpanYCm * 0.5f,
        ChannelBedWorldZ - EncodedChannelFloorCm);
    OutResult.LandscapeScale = FVector(ScaleX, ScaleY, ScaleZ);

    ALandscape* Landscape = World->SpawnActor<ALandscape>(
        OutResult.LandscapeLocation,
        FRotator::ZeroRotator);
    if (!Landscape)
    {
        OutSummary += FString::Printf(TEXT("Failed to spawn ALandscape for %s.\n"), *Candidate.PreviewSpec.RiverId);
        return false;
    }

    Landscape->SetActorScale3D(OutResult.LandscapeScale);
    Landscape->LandscapeMaterial = LandscapeMaterial;
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        Landscape->MaxLODLevel = 0;
    }
    if (FBoolProperty* EnableNaniteProperty =
            FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(), TEXT("bEnableNanite")))
    {
        EnableNaniteProperty->SetPropertyValue_InContainer(
            Landscape,
            Candidate.bEnableLandscapeNanite);
    }
    else
    {
        OutSummary += TEXT("Unable to find the reflected Landscape Nanite setting.\n");
        return false;
    }
    Landscape->StaticLightingLOD = 0;
    Landscape->SetActorLabel(FString::Printf(
        TEXT("RaftSim_SourceLandscapeCandidate_%s"),
        *Candidate.PreviewSpec.RiverId));

    TMap<FGuid, TArray<uint16>> HeightDataPerLayers;
    HeightDataPerLayers.Add(FGuid(), MoveTemp(ImportedHeightmap.Data));
    TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerDataPerLayers;
    MaterialLayerDataPerLayers.Add(FGuid(), TArray<FLandscapeImportLayerInfo>());
    Landscape->Import(
        FGuid::NewGuid(),
        0,
        0,
        LandscapeQuads,
        LandscapeQuads,
        NumSubsections,
        SubsectionSizeQuads,
        HeightDataPerLayers,
        *HeightfieldAbsolutePath,
        MaterialLayerDataPerLayers,
        ELandscapeImportAlphamapType::Additive,
        TArrayView<const FLandscapeLayer>());
    Landscape->LandscapeMaterial = LandscapeMaterial;
    for (ULandscapeComponent* LandscapeComponent : Landscape->LandscapeComponents)
    {
        if (LandscapeComponent)
        {
            LandscapeComponent->OverrideMaterial = LandscapeMaterial;
            if (Candidate.bPhysicalScaleSourceCorridor)
            {
                LandscapeComponent->SetForcedLOD(0);
            }
            LandscapeComponent->MarkRenderStateDirty();
        }
    }
    Landscape->UpdateAllComponentMaterialInstances(true);
    Landscape->RecreateComponentsState();
    Landscape->PostEditChange();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }

    OutResult.MaterialBoundComponentCount = 0;
    for (ULandscapeComponent* LandscapeComponent : Landscape->LandscapeComponents)
    {
        if (!LandscapeComponent || LandscapeComponent->GetLandscapeMaterial() != LandscapeMaterial ||
            LandscapeComponent->GetMaterialInstanceCount() < 1)
        {
            continue;
        }

        UMaterialInstance* ComponentMaterial = LandscapeComponent->GetMaterialInstance(0);
        if (ComponentMaterial && ComponentMaterial->IsChildOf(LandscapeMaterial))
        {
            ++OutResult.MaterialBoundComponentCount;
        }
    }
    OutResult.bMaterialBindingsValidated =
        OutResult.MaterialBoundComponentCount == Landscape->LandscapeComponents.Num();
    if (!OutResult.bMaterialBindingsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape material binding validation failed for %s: %d/%d components use %s.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.MaterialBoundComponentCount,
            Landscape->LandscapeComponents.Num(),
            *LandscapeMaterial->GetPathName());
        return false;
    }
    if (!AddLandscapeCandidateBiomeDressing(World, Landscape, Candidate, OutResult, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing validation failed for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    if (Candidate.bPhysicalScaleSourceCorridor &&
        !AddLandscapeCandidatePhysicalBankCorridorMesh(World, Landscape, Candidate, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Dense physical bank corridor mesh generation failed for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        Landscape->SetActorHiddenInGame(true);
        for (ULandscapeComponent* LandscapeComponent : Landscape->LandscapeComponents)
        {
            if (LandscapeComponent)
            {
                LandscapeComponent->SetVisibility(false, true);
                LandscapeComponent->SetHiddenInGame(true, true);
            }
        }
        OutSummary += TEXT(
            "Physical source Landscape remains the collision and height-query authority; "
            "dense source-terrain tiles are the non-colliding render surface.\n");
    }
    AddPreviewLightRig(World, Candidate.PreviewSpec);
    AActor* WaterActor = Candidate.bPhysicalScaleSourceCorridor
        ? AddLandscapeCandidatePhysicalRiverRibbon(
              World,
              Landscape,
              Candidate,
              CandidateWaterMaterial,
              OutSummary)
        : AddPreviewRiverRibbonMesh(
              World,
              Candidate.PreviewSpec,
              nullptr,
              nullptr,
              nullptr,
              CandidateWaterMaterial,
              SolverVisualizationFieldsPtr,
              SolverFoamMaterial);
    OutResult.WaterMaterialPath = CandidateWaterMaterial->GetPathName();
    if (WaterActor)
    {
        if (UProceduralMeshComponent* WaterComponent =
                WaterActor->FindComponentByClass<UProceduralMeshComponent>())
        {
            if (WaterComponent->GetMaterial(0) == CandidateWaterMaterial)
            {
                OutResult.WaterMaterialBoundComponentCount = 1;
            }
        }
    }
    OutResult.bSolverSurfaceWaterMaterialBound =
        OutResult.WaterMaterialBoundComponentCount == 1 &&
        CandidateWaterMaterial->GetShadingModels().HasShadingModel(MSM_DefaultLit);
    if (!OutResult.bSolverSurfaceWaterMaterialBound)
    {
        OutSummary += FString::Printf(
            TEXT("Solver-surface water material binding failed for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    AddPreviewCameraAndStart(World, Candidate.PreviewSpec);
    RepositionLandscapeCandidatePhysicalCameras(World, Landscape, Candidate, OutSummary);

    OutSummary += FString::Printf(
        TEXT("Imported %s as a %d-component ALandscape candidate; preview channel burn modified %d samples.\n"),
        *Candidate.HeightfieldRelativePath,
        Landscape->LandscapeComponents.Num(),
        OutResult.ChannelModifiedSampleCount);
    const bool bSaved = SavePreviewWorld(World, Candidate.MapPackagePath, OutSummary);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    OutResult.bNaniteRepresentationBuilt = !Candidate.bEnableLandscapeNanite ||
        Landscape->IsNaniteMeshUpToDate();
    if (Candidate.bEnableLandscapeNanite && !OutResult.bNaniteRepresentationBuilt)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape Nanite representation is not up to date for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
    }

    OutResult.NaniteComponentCount = Landscape->NaniteComponents.Num();
    for (ULandscapeNaniteComponent* NaniteComponent : Landscape->NaniteComponents)
    {
        UStaticMesh* NaniteMesh = NaniteComponent ? NaniteComponent->GetStaticMesh() : nullptr;
        if (!NaniteMesh)
        {
            continue;
        }

        for (const FStaticMaterial& StaticMaterial : NaniteMesh->GetStaticMaterials())
        {
            ++OutResult.NaniteMaterialSlotCount;
            UMaterialInterface* SlotMaterial = StaticMaterial.MaterialInterface;
            UMaterialInstance* SlotMaterialInstance = Cast<UMaterialInstance>(SlotMaterial);
            if (SlotMaterial == LandscapeMaterial ||
                (SlotMaterialInstance && SlotMaterialInstance->IsChildOf(LandscapeMaterial)))
            {
                ++OutResult.NaniteMaterialBoundSlotCount;
            }
        }

        Nanite::FMaterialAudit MaterialAudit;
        Nanite::AuditMaterials(NaniteComponent, MaterialAudit, false);
        for (const Nanite::FMaterialAuditEntry& Entry : MaterialAudit.Entries)
        {
            if (Entry.bHasAnyError)
            {
                ++OutResult.NaniteMaterialAuditErrorCount;
                OutSummary += FString::Printf(
                    TEXT("Nanite material audit rejected %s slot %d for %s: null=%d blend=%d shading=%d usage=%d.\n"),
                    Entry.Material ? *Entry.Material->GetPathName() : TEXT("<null>"),
                    Entry.MaterialIndex,
                    *Candidate.PreviewSpec.RiverId,
                    Entry.bHasNullMaterial,
                    Entry.bHasUnsupportedBlendMode,
                    Entry.bHasUnsupportedShadingModel,
                    Entry.bHasInvalidUsage);
            }
        }
    }
    OutResult.bNaniteMaterialBindingsValidated = !Candidate.bEnableLandscapeNanite ||
        (OutResult.NaniteComponentCount > 0 &&
         OutResult.NaniteMaterialSlotCount > 0 &&
         OutResult.NaniteMaterialBoundSlotCount == OutResult.NaniteMaterialSlotCount &&
         OutResult.NaniteMaterialAuditErrorCount == 0);
    OutSummary += FString::Printf(
        TEXT("Landscape material audit for %s: %d/%d source components and %d/%d Nanite slots use %s; %d Nanite audit errors.\n"),
        *Candidate.PreviewSpec.RiverId,
        OutResult.MaterialBoundComponentCount,
        Landscape->LandscapeComponents.Num(),
        OutResult.NaniteMaterialBoundSlotCount,
        OutResult.NaniteMaterialSlotCount,
        *LandscapeMaterial->GetPathName(),
        OutResult.NaniteMaterialAuditErrorCount);
    if (Candidate.bEnableLandscapeNanite && !OutResult.bNaniteMaterialBindingsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape Nanite material binding validation failed for %s across %d Nanite components.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.NaniteComponentCount);
    }
    return bSaved && OutResult.bNaniteRepresentationBuilt && OutResult.bMaterialBindingsValidated &&
        OutResult.bDressingValidated && OutResult.bSolverSurfaceWaterMaterialBound &&
        OutResult.bNaniteMaterialBindingsValidated;
}

bool BuildPreviewMapForSpec(const FRaftSimEnvironmentPreviewSpec& Spec, FString& OutSummary)
{
    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to create blank map for %s\n"), *Spec.RiverId);
        return false;
    }

    UStaticMesh* CubeMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    UStaticMesh* SphereMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UStaticMesh* CylinderMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    const bool bUseFirstPartyProceduralFoliageOnly = true;
    UStaticMesh* PcgTreeMeshA = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_01.PCG_Tree_01"));
    UStaticMesh* PcgTreeMeshB = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_02.PCG_Tree_02"));
    UStaticMesh* PcgTreeMeshC = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_03.PCG_Tree_03"));
    UStaticMesh* PcgSeedlingMesh = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Seedling_01.PCG_Seedling_01"));

    FRaftSimPreviewImage AerialDrape;
    const FRaftSimPreviewImage* AerialDrapePtr = nullptr;
    if (!Spec.AerialDrapeImage.IsEmpty() && LoadPreviewPngImage(Spec.AerialDrapeImage, AerialDrape))
    {
        AerialDrapePtr = &AerialDrape;
    }
    FRaftSimPreviewImage TerrainRelief;
    const FRaftSimPreviewImage* TerrainReliefPtr = nullptr;
    if (!Spec.TerrainReliefImage.IsEmpty() && LoadPreviewPngImage(Spec.TerrainReliefImage, TerrainRelief))
    {
        TerrainReliefPtr = &TerrainRelief;
    }
    FRaftSimPreviewImage HeightfieldPreview;
    const FRaftSimPreviewImage* HeightfieldPreviewPtr = nullptr;
    if (!Spec.HeightfieldPreviewImage.IsEmpty() && LoadPreviewPngImage(Spec.HeightfieldPreviewImage, HeightfieldPreview))
    {
        HeightfieldPreviewPtr = &HeightfieldPreview;
    }
    FRaftSimPreviewImage WaterMask;
    const FRaftSimPreviewImage* WaterMaskPtr = nullptr;
    if (!Spec.WaterMaskImage.IsEmpty() && LoadPreviewPngImage(Spec.WaterMaskImage, WaterMask))
    {
        WaterMaskPtr = &WaterMask;
    }
    FRaftSimPreviewImage VegetationMask;
    const FRaftSimPreviewImage* VegetationMaskPtr = nullptr;
    if (!Spec.VegetationMaskImage.IsEmpty() && LoadPreviewPngImage(Spec.VegetationMaskImage, VegetationMask))
    {
        VegetationMaskPtr = &VegetationMask;
    }
    FRaftSimPreviewImage MaterialAtlasAlbedo;
    const FRaftSimPreviewImage* MaterialAtlasAlbedoPtr = nullptr;
    const FString MaterialAtlasAlbedoPath = GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasAlbedoPath, MaterialAtlasAlbedo))
    {
        MaterialAtlasAlbedoPtr = &MaterialAtlasAlbedo;
    }
    FRaftSimPreviewImage MaterialAtlasNormal;
    const FRaftSimPreviewImage* MaterialAtlasNormalPtr = nullptr;
    const FString MaterialAtlasNormalPath = GetFirstPartyMaterialTextureAtlasNormalRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasNormalPath, MaterialAtlasNormal))
    {
        MaterialAtlasNormalPtr = &MaterialAtlasNormal;
    }
    FRaftSimPreviewImage MaterialAtlasPacked;
    const FRaftSimPreviewImage* MaterialAtlasPackedPtr = nullptr;
    const FString MaterialAtlasPackedPath = GetFirstPartyMaterialTextureAtlasPackedRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasPackedPath, MaterialAtlasPacked))
    {
        MaterialAtlasPackedPtr = &MaterialAtlasPacked;
    }
    const FRaftSimFirstPartyMaterialAssignmentSet FirstPartyMaterialAssignments =
        LoadFirstPartyMaterialAssignmentSetForSpec(Spec, OutSummary);

    AddPreviewLightRig(World, Spec);

    AddPreviewTerrainMesh(
        World,
        Spec,
        AerialDrapePtr,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        MaterialAtlasAlbedoPtr,
        MaterialAtlasNormalPtr,
        MaterialAtlasPackedPtr);
    AddPreviewRiverRibbonMesh(World, Spec, MaterialAtlasAlbedoPtr, MaterialAtlasNormalPtr, MaterialAtlasPackedPtr);
    const bool bCreateLegacyTerrainOverlayProxyGeometry = false;
    if (bCreateLegacyTerrainOverlayProxyGeometry)
    {
        AddPreviewAerialDrapeTiles(
            World,
            Spec,
            AerialDrapePtr,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewWetBankDressing(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr);
        AddPreviewIrregularShorelineEdgeBreakupDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceAwareBankBreakupDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewTerrainMaterialLayerDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewLandscapeNaniteMaterialScaffoldDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewTerrainErosionRillDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceMaskedBankBarMicrogeometryDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceMaskedShorelineLipOverhangDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewProceduralBankTextureCards(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr,
            PlaneMesh);
        AddPreviewNearFieldPhotorealReviewDressing(
            World,
            Spec,
            AerialDrapePtr,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped legacy terrain/bank overlay proxy geometry for %s; the textured terrain mesh is authoritative.\n"),
            *Spec.RiverId);
    }
    AddPreviewProceduralEnvironmentDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr, SphereMesh);
    AddPreviewBiomeBankEcologyDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CubeMesh,
        CylinderMesh,
        PlaneMesh);
    AddPreviewBiomeFoliageSilhouetteDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CylinderMesh,
        PlaneMesh);
    AddPreviewDenseBiomeFoliageLayerDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CylinderMesh,
        PlaneMesh);
    AddPreviewInstancedProceduralFoliageEquivalentDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        SphereMesh,
        CylinderMesh);
    AddPreviewFoliageCrownDepthAndLeafletBreakupDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr);
    const bool bCreateLegacyWaterOverlayProxyGeometry = false;
    if (bCreateLegacyWaterOverlayProxyGeometry)
    {
        AddPreviewWaterSurfaceDetail(World, Spec);
        AddPreviewFlowBandTextureDetail(World, Spec);
        AddPreviewWaterSurfaceChopAndTurbidityDetail(World, Spec);
        AddPreviewWaterShaderDepthReflectionScaffoldDetail(World, Spec);
        AddPreviewShallowWaterClarityAndAerationDetail(World, Spec, WaterMaskPtr, PlaneMesh);
        AddPreviewWaterMicroRippleGlintDetail(World, Spec, PlaneMesh);
        AddPreviewFoamAndHydraulics(World, Spec);
        AddPreviewFlowDependentHydraulicAerationAndSprayDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            PlaneMesh,
            SphereMesh);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped legacy water overlay proxy geometry for %s; integrated base-water relief and color remain active.\n"),
            *Spec.RiverId);
    }
    AddPreviewSurfaceAtmosphereAndSprayDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);
    AddPreviewWaterfallAndPlungeMistDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh, CubeMesh);
    AddPreviewRiverAtmosphericBackdropDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);
    AddPreviewSourceAwareSkyGradientLayer(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    for (int32 BoulderIndex = 0; BoulderIndex < Spec.BoulderCount; ++BoulderIndex)
    {
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = -3600.0f + static_cast<float>(BoulderIndex) * (28200.0f / FMath::Max(1, Spec.BoulderCount));
        const float BaseOffset = ActiveRiverHalfWidth * (0.32f + 0.55f * FMath::Abs(FMath::Sin(static_cast<float>(BoulderIndex) * 1.91f)));
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
        float BestBoulderScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 145.0f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.67f + static_cast<float>(CandidateIndex) * 1.21f);
            const float CandidateOffset = BaseOffset + Side * 125.0f * (static_cast<float>(CandidateIndex) - 2.0f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
            const float Score = WaterT * 1.15f - VegetationT * 0.70f +
                0.05f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.97f + static_cast<float>(CandidateIndex));
            if (Score > BestBoulderScore)
            {
                BestBoulderScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }
        float BoulderCenterY = GetPreviewRiverCenterY(Spec, X);
        float BoulderLateralOffset = Y - BoulderCenterY;
        const bool bNearCameraReviewBoulder = X < 3600.0f;
        if (bNearCameraReviewBoulder && FMath::Abs(BoulderLateralOffset) < ActiveRiverHalfWidth * 0.78f)
        {
            const float ReviewClearanceSide = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
            X += Spec.bDesertCanyon ? 1420.0f : 1160.0f;
            BoulderCenterY = GetPreviewRiverCenterY(Spec, X);
            BoulderLateralOffset =
                ReviewClearanceSide * ActiveRiverHalfWidth * (Spec.bDesertCanyon ? 0.96f : 0.88f);
            Y = BoulderCenterY + BoulderLateralOffset;
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr, HeightfieldPreviewPtr);
        const float BaseScale = Spec.bDesertCanyon ? 1.6f : 1.0f + 0.35f * static_cast<float>(BoulderIndex % 3);
        const float Scale = BaseScale * (bNearCameraReviewBoulder ? (Spec.bDesertCanyon ? 0.50f : 0.44f) : 1.0f);
        const float BoulderWaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, X, Y);
        const float BoulderVegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, X, Y);
        const FLinearColor BoulderBaseColor = ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.90f : 0.78f);
        FLinearColor UnadjustedBoulderColor = FMath::Lerp(
            BoulderBaseColor,
            FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.46f), ScalePreviewColor(Spec.WaterColor, 0.34f), 0.30f),
            FMath::Clamp(BoulderWaterT * 0.36f, 0.0f, 0.42f));
        UnadjustedBoulderColor = ApplyFirstPartyMaterialAtlasTint(
            Spec,
            MaterialAtlasAlbedoPtr,
            WetBoulderContactMaterialTile,
            UnadjustedBoulderColor,
            X * 0.0021f + static_cast<float>(BoulderIndex) * 0.137f,
            Y * 0.0033f + BoulderWaterT * 0.29f + BoulderVegetationT * 0.41f,
            FMath::Clamp(0.14f + BoulderWaterT * 0.08f + BoulderVegetationT * 0.03f, 0.0f, 0.24f));
        UnadjustedBoulderColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
            Spec,
            MaterialAtlasNormalPtr,
            MaterialAtlasPackedPtr,
            WetBoulderContactMaterialTile,
            UnadjustedBoulderColor,
            X * 0.0021f + static_cast<float>(BoulderIndex) * 0.137f,
            Y * 0.0033f + BoulderWaterT * 0.29f + BoulderVegetationT * 0.41f,
            FMath::Clamp(0.14f + BoulderWaterT * 0.08f + BoulderVegetationT * 0.03f, 0.0f, 0.24f));
        const FLinearColor BoulderColor =
            bNearCameraReviewBoulder ? ScalePreviewColor(UnadjustedBoulderColor, Spec.bDesertCanyon ? 0.56f : 0.48f) : UnadjustedBoulderColor;
        const FVector BoulderScale(Scale * 1.18f, Scale * 0.92f, Scale * 0.54f);
        const FVector BoulderLocation(X, Y, FMath::Max(20.0f, TerrainZ + 18.0f + 8.0f * static_cast<float>(BoulderIndex % 4)));
        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceAwareBoulder_%02d_%s"), BoulderIndex, *Spec.RiverId),
            BoulderLocation,
            static_cast<float>(BoulderIndex * 31),
            BoulderScale,
            BoulderColor,
            BoulderIndex + 3900);
        AddPreviewBoulderSurfaceVariationDetail(
            World,
            Spec,
            BoulderLocation,
            static_cast<float>(BoulderIndex * 31),
            BoulderScale,
            BoulderIndex,
            BoulderWaterT,
            BoulderVegetationT,
            bNearCameraReviewBoulder);
        const float ContactFoamStrength =
            FMath::Clamp(0.45f + BoulderWaterT * 0.55f + Spec.FlowFoamScale * 0.20f, 0.0f, 1.0f);
        if (ContactFoamStrength > 0.52f)
        {
            const float ContactLength = (Spec.bDesertCanyon ? 420.0f : 330.0f) * FMath::Max(0.55f, Spec.FlowFoamScale);
            const float ContactWidth = (Spec.bDesertCanyon ? 26.0f : 34.0f) * ContactFoamStrength;
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_BoulderContactFoam_%02d_%s"), BoulderIndex, *Spec.RiverId),
                X - ContactLength * 0.34f,
                ContactLength,
                BoulderLateralOffset,
                ContactWidth,
                static_cast<float>(BoulderIndex) * 0.59f,
                Spec.bDesertCanyon ? FLinearColor(0.78f, 0.78f, 0.68f) : FLinearColor(0.86f, 0.94f, 0.88f));
        }
    }

    const float RemainingBlockyFoliageProxyCull =
        Spec.bDesertCanyon ? 0.46f : (Spec.bHasWaterfalls ? 0.38f : 0.42f);
    const int32 VisibleFoliageCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(Spec.FoliageCount) * RemainingBlockyFoliageProxyCull));
    for (int32 FoliageIndex = 0; FoliageIndex < VisibleFoliageCount; ++FoliageIndex)
    {
        const float Side = (FoliageIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BankOffset = Spec.bDesertCanyon ? ActiveRiverHalfWidth + 1350.0f : ActiveRiverHalfWidth + 620.0f;
        const float FoliageT = static_cast<float>(FoliageIndex) / static_cast<float>(FMath::Max(1, VisibleFoliageCount - 1));
        const float BaseX = FMath::Lerp(850.0f, 25800.0f, FoliageT);
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * (BankOffset + 210.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 1.31f));
        float BestFoliageScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 210.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.49f + static_cast<float>(CandidateIndex) * 1.51f);
            const float CandidateOffset = BankOffset +
                300.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.83f + static_cast<float>(CandidateIndex) * 0.91f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
            const float Score = VegetationT * (Spec.bDesertCanyon ? 0.65f : 1.45f) - WaterT * 1.10f +
                0.05f * FMath::Sin(static_cast<float>(FoliageIndex) * 1.17f + static_cast<float>(CandidateIndex));
            if (Score > BestFoliageScore)
            {
                BestFoliageScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr, HeightfieldPreviewPtr);
        const float Height = Spec.bHasWaterfalls ? 2.35f + 0.28f * static_cast<float>(FoliageIndex % 5) : (Spec.bDesertCanyon ? 0.50f : 1.45f + 0.18f * static_cast<float>(FoliageIndex % 3));
        const float CanopyWidth = Spec.bHasWaterfalls ? 1.35f + 0.18f * static_cast<float>(FoliageIndex % 4) : (Spec.bDesertCanyon ? 0.55f : 0.92f + 0.10f * static_cast<float>(FoliageIndex % 3));
        const float FirstPartyProceduralCanopyHeightCm = Spec.bDesertCanyon
            ? 92.0f + 10.0f * static_cast<float>(FoliageIndex % 3)
            : (Spec.bHasWaterfalls ? 405.0f + 34.0f * static_cast<float>(FoliageIndex % 5)
                                    : 278.0f + 22.0f * static_cast<float>(FoliageIndex % 4));
        const float FirstPartyProceduralTrunkHeightCm = Spec.bDesertCanyon
            ? 78.0f + 8.0f * static_cast<float>(FoliageIndex % 3)
            : (Spec.bHasWaterfalls ? 330.0f + 28.0f * static_cast<float>(FoliageIndex % 5)
                                    : 218.0f + 18.0f * static_cast<float>(FoliageIndex % 4));
        const float FirstPartyProceduralCanopyBlobDemotion =
            Spec.bDesertCanyon ? 0.64f : (Spec.bHasWaterfalls ? 0.46f : 0.52f);
        const float FoliageCardSilhouetteDemotion =
            Spec.bDesertCanyon ? 0.48f : (Spec.bHasWaterfalls ? 0.34f : 0.40f);
        const float FirstPartyProceduralCanopyWidthScale =
            (Spec.bDesertCanyon ? 1.0f : (Spec.bHasWaterfalls ? 1.22f : 1.16f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float FirstPartyProceduralCanopyVerticalScale =
            (Spec.bDesertCanyon ? 1.0f : (Spec.bHasWaterfalls ? 1.26f : 1.18f)) * (Spec.bHasWaterfalls ? 0.82f : 0.88f);
        const float FirstPartyProceduralCrownZ = TerrainZ + FirstPartyProceduralCanopyHeightCm;
        const float FirstPartyProceduralTrunkCenterZ = TerrainZ + FirstPartyProceduralTrunkHeightCm * 0.50f;
        const float FoliageMaskT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, X, Y);
        const FLinearColor CanopyColor = Spec.bDesertCanyon
            ? FLinearColor(0.22f, 0.28f, 0.13f)
            : FLinearColor(
                  FMath::Clamp(Spec.FoliageColor.R + 0.025f * static_cast<float>(FoliageIndex % 3), 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.G + 0.035f * static_cast<float>((FoliageIndex + 1) % 4) + FoliageMaskT * 0.035f, 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.B + 0.025f * static_cast<float>((FoliageIndex + 2) % 3), 0.0f, 1.0f));
        const FLinearColor FirstPartyProceduralCanopyToneAnchor = Spec.bDesertCanyon
            ? FLinearColor(0.18f, 0.21f, 0.105f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.120f, 0.038f)
                                    : FLinearColor(0.085f, 0.175f, 0.055f));
        const float FirstPartyProceduralCanopyToneCompression =
            Spec.bDesertCanyon ? 0.20f : (Spec.bHasWaterfalls ? 0.54f : 0.42f);
        FLinearColor FirstPartyProceduralCanopyToneColor = ScalePreviewColor(
            FMath::Lerp(CanopyColor, FirstPartyProceduralCanopyToneAnchor, FirstPartyProceduralCanopyToneCompression),
            Spec.bDesertCanyon ? 0.94f : (Spec.bHasWaterfalls ? 0.80f : 0.84f));
        FirstPartyProceduralCanopyToneColor = ApplyFirstPartyMaterialAtlasTint(
            Spec,
            MaterialAtlasAlbedoPtr,
            BiomeFoliageGroundcoverMaterialTile,
            FirstPartyProceduralCanopyToneColor,
            X * 0.0017f + static_cast<float>(FoliageIndex) * 0.071f,
            Y * 0.0024f + FoliageMaskT * 0.36f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.18f : 0.15f));
        FirstPartyProceduralCanopyToneColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
            Spec,
            MaterialAtlasNormalPtr,
            MaterialAtlasPackedPtr,
            BiomeFoliageGroundcoverMaterialTile,
            FirstPartyProceduralCanopyToneColor,
            X * 0.0017f + static_cast<float>(FoliageIndex) * 0.071f,
            Y * 0.0024f + FoliageMaskT * 0.36f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.18f : 0.15f));
        const FLinearColor FirstPartyProceduralCanopyShadowColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.62f)
            : FMath::Lerp(
                  FirstPartyProceduralCanopyToneColor,
                  Spec.bHasWaterfalls ? FLinearColor(0.006f, 0.032f, 0.014f) : FLinearColor(0.030f, 0.060f, 0.024f),
                  Spec.bHasWaterfalls ? 0.46f : 0.34f);
        UStaticMesh* PcgFoliageMesh = nullptr;
        if (Spec.bDesertCanyon)
        {
            PcgFoliageMesh = PcgSeedlingMesh;
        }
        else if (FoliageIndex % 3 == 0)
        {
            PcgFoliageMesh = PcgTreeMeshA;
        }
        else if (FoliageIndex % 3 == 1)
        {
            PcgFoliageMesh = PcgTreeMeshB ? PcgTreeMeshB : PcgTreeMeshA;
        }
        else
        {
            PcgFoliageMesh = PcgTreeMeshC ? PcgTreeMeshC : PcgTreeMeshA;
        }

        if (PcgFoliageMesh)
        {
            const float BaseScale = Spec.bHasWaterfalls
                ? 0.30f + 0.035f * static_cast<float>(FoliageIndex % 4)
                : (Spec.bDesertCanyon ? 0.30f + 0.035f * static_cast<float>(FoliageIndex % 3) : 0.27f + 0.03f * static_cast<float>(FoliageIndex % 3));
            AddPreviewMeshActor(
                World,
                PcgFoliageMesh,
                FString::Printf(TEXT("RaftSim_SourceAwareFoliage_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ),
                FRotator(0.0f, static_cast<float>((FoliageIndex * 43) % 360), 0.0f),
                FVector(BaseScale, BaseScale, BaseScale * (Spec.bHasWaterfalls ? 1.22f : 1.0f)),
                FirstPartyProceduralCanopyToneColor);

            const int32 SupplementalLeafLobes = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
            const float CrownZ = TerrainZ + (Spec.bHasWaterfalls ? 305.0f : (Spec.bDesertCanyon ? 82.0f : 205.0f));
            for (int32 LobeIndex = 0; LobeIndex < SupplementalLeafLobes; ++LobeIndex)
            {
                const float AngleRadians = FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 61 + LobeIndex * 127) % 360));
                const float Radius = Spec.bDesertCanyon ? 24.0f : (Spec.bHasWaterfalls ? 84.0f : 58.0f);
                const FVector ClusterLocation(
                    X + FMath::Cos(AngleRadians) * Radius,
                    Y + FMath::Sin(AngleRadians) * Radius,
                    CrownZ + 24.0f * FMath::Sin(static_cast<float>(LobeIndex) * 1.17f));
                const FVector ClusterScale = Spec.bDesertCanyon
                    ? FVector(0.20f, 0.15f, 0.090f)
                    : (Spec.bHasWaterfalls ? FVector(0.70f, 0.52f, 0.34f) : FVector(0.44f, 0.34f, 0.22f));
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_ProceduralLeafClusterSupplement_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    ClusterLocation,
                    static_cast<float>((FoliageIndex * 43 + LobeIndex * 31) % 360),
                    ClusterScale,
                    ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.86f + 0.035f * static_cast<float>(LobeIndex)),
                    FoliageIndex * 19 + LobeIndex + 6100,
                    Spec.bHasWaterfalls);
            }
        }
        else
        {
            AddPreviewMeshActor(
                World,
                CylinderMesh,
                FString::Printf(TEXT("RaftSim_FoliageTrunk_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, FirstPartyProceduralTrunkCenterZ),
                FRotator::ZeroRotator,
                FVector(
                    Spec.bDesertCanyon ? 0.11f : (Spec.bHasWaterfalls ? 0.16f : 0.145f),
                    Spec.bDesertCanyon ? 0.11f : (Spec.bHasWaterfalls ? 0.16f : 0.145f),
                    FirstPartyProceduralTrunkHeightCm * 0.010f),
                Spec.bDesertCanyon ? FLinearColor(0.21f, 0.18f, 0.10f) : FLinearColor(0.20f, 0.12f, 0.07f));

            const int32 CanopyLobes = Spec.bHasWaterfalls ? 3 : (Spec.bDesertCanyon ? 2 : 2);
            for (int32 LobeIndex = 0; LobeIndex < CanopyLobes; ++LobeIndex)
            {
                const float AngleRadians = FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 47 + LobeIndex * 83) % 360));
                const float Radius = ((LobeIndex == 0) ? 0.0f : (Spec.bHasWaterfalls ? 112.0f : 76.0f)) * FirstPartyProceduralCanopyBlobDemotion;
                const float LobeX = X + FMath::Cos(AngleRadians) * Radius;
                const float LobeY = Y + FMath::Sin(AngleRadians) * Radius;
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_FoliageCanopy_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    FVector(LobeX, LobeY, FirstPartyProceduralCrownZ + 26.0f * static_cast<float>(LobeIndex % 3)),
                    static_cast<float>((FoliageIndex * 47 + LobeIndex * 19) % 360),
                    FVector(
                        CanopyWidth * FirstPartyProceduralCanopyWidthScale * (1.08f - 0.08f * static_cast<float>(LobeIndex % 2)),
                        CanopyWidth * FirstPartyProceduralCanopyWidthScale * (0.82f + 0.07f * static_cast<float>(LobeIndex % 3)),
                        Height * FirstPartyProceduralCanopyVerticalScale * (Spec.bHasWaterfalls ? 0.36f : 0.30f)),
                    LobeIndex == 0 ? FirstPartyProceduralCanopyShadowColor : FirstPartyProceduralCanopyToneColor,
                    FoliageIndex * 23 + LobeIndex + 6700,
                    Spec.bHasWaterfalls);
            }
        }

        const int32 OrganicLeafSprayCount = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
        for (int32 SprayIndex = 0; SprayIndex < OrganicLeafSprayCount; ++SprayIndex)
        {
            const float SprayAngleRadians =
                FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 71 + SprayIndex * 113) % 360));
            const float SprayRadius = (Spec.bDesertCanyon ? 46.0f : (Spec.bHasWaterfalls ? 132.0f : 88.0f)) * FirstPartyProceduralCanopyBlobDemotion;
            const FVector SprayLocation(
                X + FMath::Cos(SprayAngleRadians) * SprayRadius,
                Y + FMath::Sin(SprayAngleRadians) * SprayRadius,
                FirstPartyProceduralCrownZ + (Spec.bHasWaterfalls ? 42.0f : 22.0f) * static_cast<float>(SprayIndex));
            const FVector SprayScale = Spec.bDesertCanyon
                ? FVector(0.28f, 0.20f, 0.090f)
                : (Spec.bHasWaterfalls ? FVector(1.18f, 0.84f, 0.54f) * FoliageCardSilhouetteDemotion : FVector(0.76f, 0.54f, 0.32f) * FoliageCardSilhouetteDemotion);
            AddPreviewOrganicLeafSprayActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicCanopyLeafSpray_%02d_%02d_%s"), FoliageIndex, SprayIndex, *Spec.RiverId),
                SprayLocation,
                static_cast<float>((FoliageIndex * 59 + SprayIndex * 37) % 360),
                SprayScale,
                ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.70f + 0.045f * static_cast<float>(SprayIndex % 4)),
                FoliageIndex * 41 + SprayIndex + 8300,
                Spec.bHasWaterfalls);
        }

        if (!Spec.bDesertCanyon)
        {
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicBranchFrondSupplement_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(
                    X + Side * (Spec.bHasWaterfalls ? 42.0f : 30.0f),
                    Y - Side * (Spec.bHasWaterfalls ? 58.0f : 38.0f),
                    FirstPartyProceduralCrownZ - (Spec.bHasWaterfalls ? 46.0f : 32.0f)),
                static_cast<float>((FoliageIndex * 67 + 19) % 360),
                FVector(
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.94f : 0.74f) * FoliageCardSilhouetteDemotion,
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.78f : 0.60f) * FoliageCardSilhouetteDemotion,
                    Height * (Spec.bHasWaterfalls ? 0.46f : 0.32f) * (Spec.bHasWaterfalls ? 0.84f : 0.88f)),
                ScalePreviewColor(FirstPartyProceduralCanopyShadowColor, Spec.bHasWaterfalls ? 0.92f : 0.88f),
                FoliageIndex * 71 + 13600,
                Spec.bHasWaterfalls,
                false);
            AddPreviewFineTwigCanopyLaceActor(
                World,
                FString::Printf(TEXT("RaftSim_FineTwigCanopyLace_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(
                    X - Side * (Spec.bHasWaterfalls ? 28.0f : 18.0f),
                    Y + Side * (Spec.bHasWaterfalls ? 34.0f : 22.0f),
                    FirstPartyProceduralCrownZ + (Spec.bHasWaterfalls ? 34.0f : 20.0f)),
                static_cast<float>((FoliageIndex * 73 + 11) % 360),
                FVector(
                    CanopyWidth * (Spec.bHasWaterfalls ? 1.08f : 0.82f) * FoliageCardSilhouetteDemotion,
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.88f : 0.66f) * FoliageCardSilhouetteDemotion,
                    Height * (Spec.bHasWaterfalls ? 0.52f : 0.36f) * (Spec.bHasWaterfalls ? 0.84f : 0.88f)),
                ScalePreviewColor(FirstPartyProceduralCanopyToneColor, Spec.bHasWaterfalls ? 0.68f : 0.66f),
                FoliageIndex * 83 + 15100,
                Spec.bHasWaterfalls);
        }

        if (!Spec.bDesertCanyon && FoliageIndex % 2 == 0)
        {
            const int32 UnderstoryClusterCount = Spec.bHasWaterfalls ? 3 : 2;
            for (int32 UnderstoryIndex = 0; UnderstoryIndex < UnderstoryClusterCount; ++UnderstoryIndex)
            {
                const float Phase = static_cast<float>(FoliageIndex) * 0.77f + static_cast<float>(UnderstoryIndex) * 1.93f;
                float UnderstoryX = X + 95.0f * FMath::Cos(Phase) + 70.0f * static_cast<float>(UnderstoryIndex);
                float UnderstoryY =
                    Y - Side * (155.0f + 70.0f * static_cast<float>(UnderstoryIndex)) + 54.0f * FMath::Sin(Phase);
                float BestUnderstoryScore = -1000.0f;
                for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
                {
                    const float CandidateX = UnderstoryX + 72.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.31f);
                    const float CandidateY = UnderstoryY + Side * 86.0f * FMath::Cos(Phase * 0.73f + static_cast<float>(CandidateIndex) * 1.17f);
                    const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
                    const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
                    const float Score = VegetationT * 1.30f - WaterT * 0.95f +
                        0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
                    if (Score > BestUnderstoryScore)
                    {
                        BestUnderstoryScore = Score;
                        UnderstoryX = CandidateX;
                        UnderstoryY = CandidateY;
                    }
                }
                const float UnderstoryZ = GetPreviewTerrainHeightCm(Spec, UnderstoryX, UnderstoryY, TerrainReliefPtr, HeightfieldPreviewPtr);
                const float UnderstoryMaskT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, UnderstoryX, UnderstoryY);
                const FLinearColor UnderstoryColor = FMath::Lerp(
                    FirstPartyProceduralCanopyShadowColor,
                    Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.20f, 0.07f) : FLinearColor(0.13f, 0.26f, 0.10f),
                    FMath::Clamp(0.22f + UnderstoryMaskT * 0.14f, 0.22f, 0.42f));
                if (PcgSeedlingMesh)
                {
                    const float SeedlingScale = Spec.bHasWaterfalls ? 0.24f + 0.03f * static_cast<float>(UnderstoryIndex) : 0.18f;
                    AddPreviewMeshActor(
                        World,
                        PcgSeedlingMesh,
                        FString::Printf(TEXT("RaftSim_SourceAwareUnderstory_%02d_%02d_%s"), FoliageIndex, UnderstoryIndex, *Spec.RiverId),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ),
                        FRotator(0.0f, static_cast<float>((FoliageIndex * 29 + UnderstoryIndex * 67) % 360), 0.0f),
                        FVector(SeedlingScale, SeedlingScale, SeedlingScale * (Spec.bHasWaterfalls ? 1.16f : 0.94f)),
                        UnderstoryColor);
                }
                else
                {
                    AddPreviewProceduralLeafClusterActor(
                        World,
                        FString::Printf(TEXT("RaftSim_Understory_%02d_%02d_%s"), FoliageIndex, UnderstoryIndex, *Spec.RiverId),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ + 30.0f),
                        static_cast<float>((FoliageIndex * 29 + UnderstoryIndex * 67) % 360),
                        FVector(0.48f, 0.36f, 0.22f),
                        UnderstoryColor,
                        FoliageIndex * 31 + UnderstoryIndex + 7100,
                        Spec.bHasWaterfalls);
                }
            }
        }
        else if (Spec.bDesertCanyon && FoliageIndex % 2 == 0)
        {
            const float ScrubX = X + 130.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.53f);
            const float ScrubY = Y - Side * (310.0f + 80.0f * FMath::Cos(static_cast<float>(FoliageIndex) * 0.41f));
            const float ScrubZ = GetPreviewTerrainHeightCm(Spec, ScrubX, ScrubY, TerrainReliefPtr, HeightfieldPreviewPtr);
            const FLinearColor ScrubColor = FLinearColor(0.24f, 0.27f, 0.15f);
            if (PcgSeedlingMesh)
            {
                AddPreviewMeshActor(
                    World,
                    PcgSeedlingMesh,
                    FString::Printf(TEXT("RaftSim_CanyonScrub_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(ScrubX, ScrubY, ScrubZ),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 37) % 360), 0.0f),
                    FVector(0.10f, 0.10f, 0.08f),
                    ScrubColor);
            }
            else
            {
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_CanyonScrub_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(ScrubX, ScrubY, ScrubZ + 18.0f),
                    static_cast<float>((FoliageIndex * 37) % 360),
                    FVector(0.24f, 0.18f, 0.12f),
                    ScrubColor,
                    FoliageIndex + 7500,
                    false);
            }
        }
    }

    const bool bCreateReviewOnlyForegroundRaftProxyInLifelikeCandidateMaps = false;
    if (bCreateReviewOnlyForegroundRaftProxyInLifelikeCandidateMaps)
    {
        AddPreviewRaftForeground(World, Spec, CubeMesh, CylinderMesh, MaterialAtlasAlbedoPtr);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped review-only foreground raft/oar proxy generation for %s lifelike-candidate map.\n"),
            *Spec.RiverId);
    }
    const int32 AssignedReviewMaterialComponentCount = FirstPartyMaterialAssignments.IsCompleteForDurableSurfaceReview()
        ? AssignFirstPartyMaterialInstancesToPreviewScene(World, Spec, FirstPartyMaterialAssignments, OutSummary)
        : 0;
    AddPreviewCameraAndStart(World, Spec);
    if (!FirstPartyMaterialAssignments.IsCompleteForDurableSurfaceReview() || AssignedReviewMaterialComponentCount <= 0)
    {
        OutSummary += FString::Printf(
            TEXT("Failed first-party review material-instance scene assignment gate for %s.\n"),
            *Spec.RiverId);
        return false;
    }
    return SavePreviewWorld(World, Spec.MapPackagePath, OutSummary);
}
} // namespace RaftSimEditorEnvironment
