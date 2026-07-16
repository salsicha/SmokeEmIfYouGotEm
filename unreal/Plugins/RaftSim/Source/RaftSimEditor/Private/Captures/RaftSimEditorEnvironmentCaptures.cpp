#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void AddPreviewCameraAndStart(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }
    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(Spec.RiverId);

    ACameraActor* Camera = Cast<ACameraActor>(
        GEditor->AddActor(World->GetCurrentLevel(), ACameraActor::StaticClass(), FTransform(FRotator(-13.5f, 0.0f, 0.0f), FVector(-5250.0f, GetPreviewRiverCenterY(Spec, -5250.0f), 140.0f))));
    if (Camera)
    {
        Camera->SetActorLabel(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"));
        Camera->GetCameraComponent()->FieldOfView = Spec.bDesertCanyon ? 66.0f : 68.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_VignetteIntensity = true;
        Camera->GetCameraComponent()->PostProcessSettings.VignetteIntensity = CaptureSettings.Vignette;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_Sharpen = true;
        Camera->GetCameraComponent()->PostProcessSettings.Sharpen = CaptureSettings.Sharpen;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_ColorSaturation = true;
        Camera->GetCameraComponent()->PostProcessSettings.ColorSaturation =
            FVector4(
                CaptureSettings.Saturation,
                CaptureSettings.Saturation,
                CaptureSettings.Saturation,
                1.0f);
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_ColorContrast = true;
        Camera->GetCameraComponent()->PostProcessSettings.ColorContrast =
            FVector4(
                CaptureSettings.Contrast,
                CaptureSettings.Contrast,
                CaptureSettings.Contrast,
                1.0f);
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureMethod = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureMethod = AEM_Manual;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureBias = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureBias =
            CaptureSettings.ExposureBias;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = 0;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensity = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensity =
            CaptureSettings.FilmGrainIntensity;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityShadows = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityShadows = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityMidtones = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityMidtones = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityHighlights = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityHighlights = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainScale = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainScale = FVector2f(1.0f, 1.0f);
        GEditor->SelectActor(Camera, true, false, true);
    }

    const float RiverEyeCameraX = Spec.bDesertCanyon ? -3620.0f : -5250.0f;
    const float RiverEyeCameraY = GetPreviewRiverCenterY(Spec, RiverEyeCameraX);
    const float RiverEyeTargetX = RiverEyeCameraX + (Spec.bHasWaterfalls ? 7200.0f : 6400.0f);
    const float RiverEyeTargetY = GetPreviewRiverCenterY(Spec, RiverEyeTargetX);
    const float RiverEyeCenterlineFollowingYawDeg =
        FMath::RadiansToDegrees(FMath::Atan2(RiverEyeTargetY - RiverEyeCameraY, RiverEyeTargetX - RiverEyeCameraX));
    ACameraActor* RiverEyeCamera = Cast<ACameraActor>(
        GEditor->AddActor(
            World->GetCurrentLevel(),
            ACameraActor::StaticClass(),
            FTransform(
                FRotator(Spec.bDesertCanyon ? -10.5f : -12.75f, RiverEyeCenterlineFollowingYawDeg, 0.0f),
                FVector(
                    RiverEyeCameraX,
                    RiverEyeCameraY,
                    Spec.bDesertCanyon ? 152.0f : 162.0f))));
    if (RiverEyeCamera)
    {
        RiverEyeCamera->SetActorLabel(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"));
        RiverEyeCamera->GetCameraComponent()->FieldOfView =
            Spec.bDesertCanyon ? 64.0f : 66.0f;
        if (Camera && Camera->GetCameraComponent())
        {
            RiverEyeCamera->GetCameraComponent()->PostProcessSettings =
                Camera->GetCameraComponent()->PostProcessSettings;
            RiverEyeCamera->GetCameraComponent()->PostProcessBlendWeight =
                Camera->GetCameraComponent()->PostProcessBlendWeight;
        }
    }

    if (Spec.RiverId == TEXT("american_south_fork"))
    {
        constexpr float SolverRapidCameraX = 240.0f;
        constexpr float SolverRapidTargetX = 4740.0f;
        const float SolverRapidCameraY = GetPreviewRiverCenterY(Spec, SolverRapidCameraX);
        const float SolverRapidTargetY = GetPreviewRiverCenterY(Spec, SolverRapidTargetX);
        const float SolverRapidYawDeg = FMath::RadiansToDegrees(
            FMath::Atan2(
                SolverRapidTargetY - SolverRapidCameraY,
                SolverRapidTargetX - SolverRapidCameraX));
        ACameraActor* SolverRapidCamera = Cast<ACameraActor>(
            GEditor->AddActor(
                World->GetCurrentLevel(),
                ACameraActor::StaticClass(),
                FTransform(
                    FRotator(-9.5f, SolverRapidYawDeg, 0.0f),
                    FVector(SolverRapidCameraX, SolverRapidCameraY, 168.0f))));
        if (SolverRapidCamera)
        {
            SolverRapidCamera->SetActorLabel(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"));
            SolverRapidCamera->GetCameraComponent()->FieldOfView = 70.0f;
            if (RiverEyeCamera && RiverEyeCamera->GetCameraComponent())
            {
                SolverRapidCamera->GetCameraComponent()->PostProcessSettings =
                    RiverEyeCamera->GetCameraComponent()->PostProcessSettings;
                SolverRapidCamera->GetCameraComponent()->PostProcessBlendWeight =
                    RiverEyeCamera->GetCameraComponent()->PostProcessBlendWeight;
            }
        }
    }

    APlayerStart* PlayerStart = Cast<APlayerStart>(
        GEditor->AddActor(World->GetCurrentLevel(), APlayerStart::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(-5350.0f, GetPreviewRiverCenterY(Spec, -5350.0f), 120.0f))));
    if (PlayerStart)
    {
        PlayerStart->SetActorLabel(TEXT("RaftSim_GuideSeat_PlayerStart"));
    }

}

bool SavePreviewWorld(UWorld* World, const FString& PackagePath, FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("No world to save.\n");
        return false;
    }

    World->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetMapPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    const bool bSaved = FEditorFileUtils::SaveMap(World, Filename);
    OutSummary += FString::Printf(TEXT("%s %s -> %s\n"), bSaved ? TEXT("Saved") : TEXT("Failed"), *PackagePath, *Filename);
    return bSaved;
}

FString GetPreviewCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews"),
        Spec.RiverId + TEXT("_") + CaptureId + TEXT(".png"));
}

FString GetPreviewFlowVariantCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews/flow_variants"),
        Spec.RiverId + TEXT("_") + Spec.FlowBandId + TEXT("_") + CaptureId + TEXT(".png"));
}

FString GetPreviewFidelityNote(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    const FString AtlasApplicationNote = TEXT("; first-party material texture atlas albedo tiles are sampled into terrain, primary boulder, and foliage vertex colors, while raft/oar atlas materials remain available for future foreground-art approval and river water keeps generated vertex-current color with review-material atlas/source texture weights culled to avoid repeated corridor-map tile artifacts; normal plus packed AO/roughness/height atlases drive bounded preview material response for non-water surfaces; first-party generated close-range terrain albedo, normal, and packed AO/roughness/height detail textures now use dedicated per-river tiled UV scale and bounded terrain-only blends beneath the corridor-scale source drape; source DEM/heightfield geometry uses bilinear sampling, bounded center-seam feathering, meter-scale macro relief, multi-scale local erosion residuals, and reduced normal flattening as the authoritative preview terrain mesh; the authoritative river ribbon preserves normals from its flow-dependent wave geometry, samples tile-safe first-party water normal detail, and uses river-specific bounded emissive, roughness, specular, and normal response instead of a flat up-normal high-roughness surface; water, boulder, foliage, and raft review material instances remain assigned, while source-baked terrain stays on its proven lit vertex-color material after the loaded atlas terrain candidate rendered black; lifelike-candidate maps skip placeholder raft/oar proxy generation and capture exports still cull any legacy foreground raft/oar proxies until approved production foreground art exists; all detail assets, source-derived terrain, and water light-response values remain candidate-only until Landscape/Nanite and WaterBody/custom shader promotion, reflection/refraction, capture, art, guide/geospatial, hazard readability, rights/provenance, and desktop/VR performance review pass");
    if (!Spec.SourceDrapeDescription.IsEmpty())
    {
        return Spec.SourceDrapeDescription + AtlasApplicationNote;
    }

    return FString(TEXT("source-aware procedural blockout with generated valley, river, foam, rocks, foliage, and raft proxies; not yet production photoreal")) +
        AtlasApplicationNote;
}

ACameraActor* FindPreviewCaptureCamera(UWorld* World, const FString& PreferredCameraLabel)
{
    ACameraActor* FallbackCamera = nullptr;
    for (TActorIterator<ACameraActor> It(World); It; ++It)
    {
        ACameraActor* Camera = *It;
        if (!FallbackCamera)
        {
            FallbackCamera = Camera;
        }

        if (Camera && Camera->GetActorLabel() == PreferredCameraLabel)
        {
            return Camera;
        }
    }

    return FallbackCamera;
}

bool CapturePreviewImageForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& CaptureRoot,
    FString& OutRelativeCapturePath,
    const FString& CameraLabel,
    const FString& CaptureId,
    const FString& CaptureDescription,
    bool bHideForegroundRaftProxies,
    FString& OutSummary,
    const TFunction<bool(UWorld*, ACameraActor*, FString&)>& WorldSetup)
{
    const FString MapFilename =
        FPackageName::LongPackageNameToFilename(Spec.MapPackagePath, FPackageName::GetMapPackageExtension());
    if (!FPaths::FileExists(MapFilename))
    {
        OutSummary += FString::Printf(TEXT("Missing preview map for capture: %s\n"), *MapFilename);
        return false;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::LoadMap(MapFilename);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to load preview map for capture: %s\n"), *Spec.MapPackagePath);
        return false;
    }

    FlushAsyncLoading();
    World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    for (TActorIterator<ALandscapeProxy> It(World); It; ++It)
    {
        ALandscapeProxy* LandscapeProxy = *It;
        if (LandscapeProxy)
        {
            LandscapeProxy->RecreateComponentsState();
        }
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    if (GEditor)
    {
        GEditor->SelectNone(false, true, false);
    }

    ACameraActor* Camera = FindPreviewCaptureCamera(World, CameraLabel);
    if (!Camera || !Camera->GetCameraComponent())
    {
        OutSummary += FString::Printf(TEXT("No %s capture camera found in %s\n"), *CaptureDescription, *Spec.MapPackagePath);
        return false;
    }

    if (WorldSetup && !WorldSetup(World, Camera, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Capture world setup failed for %s.\n"),
            *CaptureDescription);
        return false;
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();

    UTextureRenderTarget2D* RenderTarget =
        NewObject<UTextureRenderTarget2D>(GetTransientPackage(), NAME_None, RF_Transient);
    if (!RenderTarget)
    {
        OutSummary += FString::Printf(TEXT("Failed to allocate render target for %s\n"), *Spec.RiverId);
        return false;
    }

    constexpr int32 CaptureWidth = 1280;
    constexpr int32 CaptureHeight = 720;
    RenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    RenderTarget->ClearColor = FLinearColor::Black;
    RenderTarget->InitAutoFormat(CaptureWidth, CaptureHeight);
    RenderTarget->UpdateResourceImmediate(true);

    ASceneCapture2D* SceneCapture =
        World->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), Camera->GetActorLocation(), Camera->GetActorRotation());
    if (!SceneCapture || !SceneCapture->GetCaptureComponent2D())
    {
        OutSummary += FString::Printf(TEXT("Failed to spawn scene capture for %s\n"), *Spec.RiverId);
        return false;
    }

    USceneCaptureComponent2D* CaptureComponent = SceneCapture->GetCaptureComponent2D();
    FMinimalViewInfo CameraView;
    Camera->GetCameraComponent()->GetCameraView(0.0f, CameraView);
    CaptureComponent->SetCameraView(CameraView);
    CaptureComponent->PostProcessSettings = Camera->GetCameraComponent()->PostProcessSettings;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionIntensity = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionIntensity = 100.0f;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionQuality = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionQuality = 100.0f;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionMaxRoughness = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionMaxRoughness = 0.85f;
    CaptureComponent->PostProcessBlendWeight = 1.0f;
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->CaptureSource = SCS_FinalColorLDR;
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    CaptureComponent->bAlwaysPersistRenderingState = true;
    CaptureComponent->ShowFlags.SetScreenSpaceReflections(true);
    CaptureComponent->ShowFlags.SetReflectionEnvironment(true);
    CaptureComponent->ShowFlags.SetSelection(false);
    CaptureComponent->ShowFlags.SetModeWidgets(false);
    CaptureComponent->ShowFlags.SetCompositeEditorPrimitives(false);
    if (Spec.bDeterministicValidationCapture)
    {
        CaptureComponent->ShowFlags.SetLighting(false);
        CaptureComponent->ShowFlags.SetPostProcessing(false);
        CaptureComponent->ShowFlags.SetAtmosphere(false);
        CaptureComponent->ShowFlags.SetFog(false);
        CaptureComponent->ShowFlags.SetAntiAliasing(false);
        CaptureComponent->ShowFlags.SetTemporalAA(false);
        CaptureComponent->ShowFlags.SetMotionBlur(false);
        CaptureComponent->ShowFlags.SetEyeAdaptation(false);
        CaptureComponent->ShowFlags.SetAmbientOcclusion(false);
        CaptureComponent->ShowFlags.SetGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenReflections(false);
        CaptureComponent->ShowFlags.SetScreenSpaceReflections(false);
        CaptureComponent->ShowFlags.SetReflectionEnvironment(false);
    }

    struct FForegroundRaftProxyHiddenState
    {
        struct FComponentHiddenState
        {
            UPrimitiveComponent* Component = nullptr;
            bool bWasVisible = true;
            bool bWasHiddenInGame = false;
        };

        AActor* Actor = nullptr;
        bool bWasHiddenInGame = false;
        bool bWasTemporarilyHiddenInEditor = false;
        FVector OriginalLocation = FVector::ZeroVector;
        TArray<FComponentHiddenState> ComponentStates;
    };
    TArray<FForegroundRaftProxyHiddenState> ForegroundRaftProxyHiddenStates;
    auto RestoreForegroundRaftProxyVisibility = [&ForegroundRaftProxyHiddenStates]()
    {
        for (const FForegroundRaftProxyHiddenState& HiddenState : ForegroundRaftProxyHiddenStates)
        {
            if (HiddenState.Actor)
            {
                HiddenState.Actor->SetActorLocation(HiddenState.OriginalLocation, false, nullptr, ETeleportType::TeleportPhysics);
                HiddenState.Actor->SetActorHiddenInGame(HiddenState.bWasHiddenInGame);
                HiddenState.Actor->SetIsTemporarilyHiddenInEditor(HiddenState.bWasTemporarilyHiddenInEditor);
            }
            for (const FForegroundRaftProxyHiddenState::FComponentHiddenState& ComponentState : HiddenState.ComponentStates)
            {
                if (ComponentState.Component)
                {
                    ComponentState.Component->SetVisibility(ComponentState.bWasVisible, true);
                    ComponentState.Component->SetHiddenInGame(ComponentState.bWasHiddenInGame, true);
                }
            }
        }
    };
    int32 CulledReviewOnlyForegroundActorCount = 0;
    int32 CulledReviewOnlyForegroundComponentCount = 0;
    if (bHideForegroundRaftProxies)
    {
        const FName ForegroundRaftProxyTag(TEXT("RaftSim_ForegroundRaft"));
        auto HasReviewOnlyForegroundToken = [](const FString& Value)
        {
            return Value.Contains(TEXT("RaftSim_ForegroundRaft_")) ||
                Value.Contains(TEXT("ForegroundRaft")) ||
                Value.Contains(TEXT("RaftForegroundReview")) ||
                Value.Contains(TEXT("OarBlade")) ||
                Value.Contains(TEXT("OarShaft"));
        };
        auto HasReviewOnlyNearFieldToken = [](const FString& Value)
        {
            return Value.Contains(TEXT("RaftSim_NearFieldRiverbedDebrisDressing_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldRiverbedPebbleDressing_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldPhotorealBankShelf_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldCaptureQualityWetRock_"));
        };
        auto ComponentUsesReviewOnlyForegroundMaterial = [&HasReviewOnlyForegroundToken](UPrimitiveComponent* PrimitiveComponent)
        {
            UMeshComponent* MeshComponent = Cast<UMeshComponent>(PrimitiveComponent);
            if (!MeshComponent)
            {
                return false;
            }
            const int32 MaterialCount = MeshComponent->GetNumMaterials();
            for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
            {
                UMaterialInterface* Material = MeshComponent->GetMaterial(MaterialIndex);
                if (Material &&
                    (HasReviewOnlyForegroundToken(Material->GetName()) ||
                     HasReviewOnlyForegroundToken(Material->GetPathName())))
                {
                    return true;
                }
            }
            return false;
        };
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor)
            {
                continue;
            }

            const FString ActorLabel = Actor->GetActorLabel();
            const FString ActorName = Actor->GetName();
            const bool bIsReviewOnlyActor =
                Actor->ActorHasTag(ForegroundRaftProxyTag) ||
                HasReviewOnlyForegroundToken(ActorLabel) ||
                HasReviewOnlyForegroundToken(ActorName) ||
                HasReviewOnlyNearFieldToken(ActorLabel) ||
                HasReviewOnlyNearFieldToken(ActorName);

            TArray<UPrimitiveComponent*> PrimitiveComponents;
            Actor->GetComponents<UPrimitiveComponent>(PrimitiveComponents);
            TArray<UPrimitiveComponent*> ComponentsToHide;
            for (UPrimitiveComponent* PrimitiveComponent : PrimitiveComponents)
            {
                if (!PrimitiveComponent)
                {
                    continue;
                }

                const bool bIsReviewOnlyComponent =
                    bIsReviewOnlyActor ||
                    HasReviewOnlyForegroundToken(PrimitiveComponent->GetName()) ||
                    HasReviewOnlyForegroundToken(PrimitiveComponent->GetPathName()) ||
                    ComponentUsesReviewOnlyForegroundMaterial(PrimitiveComponent);
                if (bIsReviewOnlyComponent)
                {
                    ComponentsToHide.Add(PrimitiveComponent);
                }
            }

            if (ComponentsToHide.IsEmpty())
            {
                continue;
            }

            const bool bHideWholeActor = bIsReviewOnlyActor || ComponentsToHide.Num() == PrimitiveComponents.Num();
            if (bHideWholeActor)
            {
                CaptureComponent->HideActorComponents(Actor);
                CaptureComponent->HiddenActors.AddUnique(Actor);
                ++CulledReviewOnlyForegroundActorCount;
            }

            FForegroundRaftProxyHiddenState HiddenState;
            HiddenState.Actor = Actor;
            HiddenState.bWasHiddenInGame = Actor->IsHidden();
            HiddenState.bWasTemporarilyHiddenInEditor = Actor->IsTemporarilyHiddenInEditor(false);
            HiddenState.OriginalLocation = Actor->GetActorLocation();
            for (UPrimitiveComponent* PrimitiveComponent : ComponentsToHide)
            {
                if (PrimitiveComponent)
                {
                    CaptureComponent->HideComponent(PrimitiveComponent);
                    HiddenState.ComponentStates.Add(
                        {PrimitiveComponent, PrimitiveComponent->IsVisible(), PrimitiveComponent->bHiddenInGame});
                    PrimitiveComponent->SetVisibility(false, true);
                    PrimitiveComponent->SetHiddenInGame(true, true);
                    ++CulledReviewOnlyForegroundComponentCount;
                }
            }

            ForegroundRaftProxyHiddenStates.Add(MoveTemp(HiddenState));
            if (bHideWholeActor)
            {
                Actor->SetActorHiddenInGame(true);
                Actor->SetIsTemporarilyHiddenInEditor(true);
                Actor->SetActorLocation(
                    Actor->GetActorLocation() + FVector(0.0f, 0.0f, -100000.0f),
                    false,
                    nullptr,
                    ETeleportType::TeleportPhysics);
            }
        }
        OutSummary += FString::Printf(
            TEXT("Culled %d review-only foreground/near-field actors and %d primitive components for %s capture.\n"),
            CulledReviewOnlyForegroundActorCount,
            CulledReviewOnlyForegroundComponentCount,
            *Spec.RiverId);
    }
    const bool bUseTemporaryRiverEyeCenterArtifactCover = false;
    AActor* RiverEyeCenterArtifactCoverActor = bHideForegroundRaftProxies && bUseTemporaryRiverEyeCenterArtifactCover
        ? AddPreviewRiverEyeCenterArtifactCover(World, Spec)
        : nullptr;
    auto DestroyRiverEyeCenterArtifactCover = [&RiverEyeCenterArtifactCoverActor]()
    {
        if (RiverEyeCenterArtifactCoverActor)
        {
            RiverEyeCenterArtifactCoverActor->Destroy();
            RiverEyeCenterArtifactCoverActor = nullptr;
        }
    };
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    for (TActorIterator<ALandscapeProxy> It(World); It; ++It)
    {
        ALandscapeProxy* LandscapeProxy = *It;
        if (LandscapeProxy)
        {
            LandscapeProxy->RecreateComponentsState();
        }
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    FPlatformProcess::Sleep(0.03f);
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();

    FTextureRenderTargetResource* RenderTargetResource = RenderTarget->GameThread_GetRenderTargetResource();
    TArray<FColor> ImageData;
    if (!RenderTargetResource || !RenderTargetResource->ReadPixels(ImageData) ||
        ImageData.Num() != CaptureWidth * CaptureHeight)
    {
        DestroyRiverEyeCenterArtifactCover();
        RestoreForegroundRaftProxyVisibility();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += FString::Printf(TEXT("Failed to read rendered pixels for %s\n"), *Spec.RiverId);
        return false;
    }

    const bool bApplyFirstPartyCaptureFilmGrainDither = false;
    const uint32 FirstPartyCaptureFilmGrainDitherSeed =
        GetTypeHash(Spec.RiverId) ^ (GetTypeHash(CaptureId) * 16777619u);
    for (int32 PixelIndex = 0; PixelIndex < ImageData.Num(); ++PixelIndex)
    {
        FColor& Pixel = ImageData[PixelIndex];
        Pixel.A = 255;
        if (bApplyFirstPartyCaptureFilmGrainDither)
        {
            const int32 PixelX = PixelIndex % CaptureWidth;
            const int32 PixelY = PixelIndex / CaptureWidth;
            const uint32 DitherCellX = static_cast<uint32>(PixelX / 4);
            const uint32 DitherCellY = static_cast<uint32>(PixelY / 4);
            uint32 DitherHash =
                FirstPartyCaptureFilmGrainDitherSeed ^
                (DitherCellX * 73856093u) ^
                (DitherCellY * 19349663u);
            DitherHash ^= (DitherHash >> 13);
            DitherHash *= 1274126177u;
            DitherHash ^= (DitherHash >> 16);

            const int32 FirstPartyCaptureFilmGrainDitherStrength =
                bHideForegroundRaftProxies ? 13 : 9;
            const int32 RedOffset =
                (static_cast<int32>(DitherHash & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            const int32 GreenOffset =
                (static_cast<int32>((DitherHash >> 5) & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            const int32 BlueOffset =
                (static_cast<int32>((DitherHash >> 10) & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            Pixel.R = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.R) + RedOffset, 0, 255));
            Pixel.G = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.G) + GreenOffset, 0, 255));
            Pixel.B = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.B) + BlueOffset, 0, 255));
        }
    }

    TArray64<uint8> CompressedPng;
    FImageUtils::PNGCompressImageArray(CaptureWidth, CaptureHeight, MakeArrayView(ImageData), CompressedPng);

    if (OutRelativeCapturePath.IsEmpty())
    {
        OutRelativeCapturePath = GetPreviewCaptureRelativePath(Spec, CaptureId);
    }
    const FString AbsoluteCapturePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), OutRelativeCapturePath));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsoluteCapturePath), true);
    const bool bSaved = FFileHelper::SaveArrayToFile(CompressedPng, *AbsoluteCapturePath);

    DestroyRiverEyeCenterArtifactCover();
    RestoreForegroundRaftProxyVisibility();
    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();

    OutSummary += FString::Printf(
        TEXT("%s rendered %s capture for %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *CaptureDescription,
        *Spec.DisplayName,
        *AbsoluteCapturePath);
    return bSaved;
}

bool ConfigureFutaleufuComplementaryTransitionCapture(
    UWorld* LoadedWorld,
    ACameraActor* CaptureCamera,
    const FString& AuthorityMode,
    float SourceCoverage,
    FString& SetupSummary,
    float PatternSize,
    float TransitionMode)
{
    AActor* SourceTrunkActor = nullptr;
    AActor* SourceFoliageActor = nullptr;
    AActor* LoadedAtlasActor = nullptr;
    for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor)
        {
            continue;
        }
        const FString Label = Actor->GetActorLabel();
        if (Label == TEXT("RaftSim_PveReview_Trunk"))
        {
            SourceTrunkActor = Actor;
        }
        else if (Label == TEXT("RaftSim_PveReview_Foliage"))
        {
            SourceFoliageActor = Actor;
        }
        else if (Label == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            LoadedAtlasActor = Actor;
        }
        else if (Label == TEXT("RaftSim_PveCypressMergedGeometryHlod"))
        {
            Actor->SetActorHiddenInGame(true);
        }
        else if (Label == TEXT("RaftSim_PveCypressMergedGeometrySplitHlod"))
        {
            Actor->SetActorHiddenInGame(true);
        }
        else if (Label == TEXT("RaftSim_PveCypressVolumetricFarProxy") ||
                 Label == TEXT("RaftSim_PveCypressNaniteWholeTree"))
        {
            Actor->SetActorHiddenInGame(true);
        }
    }
    if (!SourceTrunkActor || !SourceFoliageActor || !LoadedAtlasActor || !CaptureCamera)
    {
        SetupSummary += TEXT(
            "Complementary transition setup could not resolve source, HLOD, and camera actors.\n");
        return false;
    }
    const bool bSourceOnly = AuthorityMode == TEXT("source_only");
    const bool bHlodOnly = AuthorityMode == TEXT("hlod_only");
    const bool bCombined = AuthorityMode == TEXT("combined");
    const bool bShowSource = bSourceOnly || bCombined;
    const bool bShowHlod = bHlodOnly || bCombined;
    SourceCoverage = bSourceOnly ? 1.0f : (bHlodOnly ? 0.0f : SourceCoverage);
    auto SetCoverage = [SourceCoverage, PatternSize, TransitionMode](AActor* Actor)
    {
        TInlineComponentArray<UMeshComponent*> MeshComponents;
        Actor->GetComponents(MeshComponents);
        bool bUpdated = false;
        for (UMeshComponent* Component : MeshComponents)
        {
            if (!Component)
            {
                continue;
            }
            for (int32 MaterialIndex = 0;
                 MaterialIndex < Component->GetNumMaterials();
                 ++MaterialIndex)
            {
                UMaterialInstanceDynamic* DynamicMaterial =
                    Cast<UMaterialInstanceDynamic>(Component->GetMaterial(MaterialIndex));
                if (!DynamicMaterial)
                {
                    DynamicMaterial =
                        Component->CreateDynamicMaterialInstance(MaterialIndex);
                }
                if (DynamicMaterial)
                {
                    DynamicMaterial->SetScalarParameterValue(
                        TEXT("ComplementarySourceCoverage"),
                        SourceCoverage);
                    DynamicMaterial->SetScalarParameterValue(
                        TEXT("ComplementaryPatternSize"),
                        PatternSize);
                    DynamicMaterial->SetScalarParameterValue(
                        TEXT("ComplementaryTransitionMode"),
                        TransitionMode);
                    bUpdated = true;
                }
            }
        }
        return bUpdated;
    };
    const bool bSourceMaterialsUpdated =
        SetCoverage(SourceTrunkActor) && SetCoverage(SourceFoliageActor);
    const bool bHlodMaterialUpdated = SetCoverage(LoadedAtlasActor);
    SourceTrunkActor->SetActorHiddenInGame(!bShowSource);
    SourceFoliageActor->SetActorHiddenInGame(!bShowSource);
    LoadedAtlasActor->SetActorHiddenInGame(!bShowHlod);
    const float HorizontalDistanceCm = FVector::Dist2D(
        CaptureCamera->GetActorLocation(),
        LoadedAtlasActor->GetActorLocation());
    SetupSummary += FString::Printf(
        TEXT("Complementary transition %s at %.3f m radial distance sets source coverage %.4f with %s ownership (legacy pattern %.0fx%.0f) and visibility source=%s HLOD=%s.\n"),
        *AuthorityMode,
        HorizontalDistanceCm / 100.0f,
        SourceCoverage,
        TransitionMode >= 0.5f ? TEXT("temporal-AA") : TEXT("ordered"),
        PatternSize,
        PatternSize,
        bShowSource ? TEXT("true") : TEXT("false"),
        bShowHlod ? TEXT("true") : TEXT("false"));
    return bSourceMaterialsUpdated && bHlodMaterialUpdated &&
        (bSourceOnly || bHlodOnly || bCombined);
}

bool SetFutaleufuMergedGeometryHlodBracketMode(
    UWorld* World,
    bool bShowFlatAtlas,
    bool bShowMergedGeometry,
    FString& OutSummary)
{
    AActor* FlatAtlasActor = nullptr;
    AActor* MergedGeometryActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor)
        {
            continue;
        }
        const FString Label = Actor->GetActorLabel();
        if (Label == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            FlatAtlasActor = Actor;
        }
        else if (Label == TEXT("RaftSim_PveCypressMergedGeometryHlod"))
        {
            MergedGeometryActor = Actor;
        }
    }
    if (!FlatAtlasActor || !MergedGeometryActor)
    {
        OutSummary += TEXT(
            "V42 merged-geometry bracket could not resolve both HLOD actors.\n");
        return false;
    }
    FlatAtlasActor->SetActorHiddenInGame(!bShowFlatAtlas);
    MergedGeometryActor->SetActorHiddenInGame(!bShowMergedGeometry);
    return true;
}

bool SetFutaleufuMergedGeometryComponentParityMode(
    UWorld* World,
    bool bShowSingleComponent,
    bool bShowSplitComponents,
    bool bBarkCastsShadow,
    FString& OutSummary)
{
    AActor* FlatAtlasActor = nullptr;
    AActor* SingleComponentActor = nullptr;
    AActor* SplitComponentActor = nullptr;
    UMeshComponent* SingleMergedComponent = nullptr;
    UMeshComponent* SplitBarkComponent = nullptr;
    UMeshComponent* SplitFoliageComponent = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor)
        {
            continue;
        }
        const FString Label = Actor->GetActorLabel();
        if (Label == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            FlatAtlasActor = Actor;
        }
        else if (Label == TEXT("RaftSim_PveCypressMergedGeometryHlod"))
        {
            SingleComponentActor = Actor;
            SingleMergedComponent = Actor->FindComponentByClass<UMeshComponent>();
        }
        else if (Label == TEXT("RaftSim_PveCypressMergedGeometrySplitHlod"))
        {
            SplitComponentActor = Actor;
            TInlineComponentArray<UMeshComponent*> Components;
            Actor->GetComponents(Components);
            for (UMeshComponent* Component : Components)
            {
                if (!Component)
                {
                    continue;
                }
                if (Component->ComponentTags.Contains(
                        TEXT("RaftSimMergedGeometrySplitBark")))
                {
                    SplitBarkComponent = Component;
                }
                else if (Component->ComponentTags.Contains(
                             TEXT("RaftSimMergedGeometrySplitFoliage")))
                {
                    SplitFoliageComponent = Component;
                }
            }
        }
    }
    if (!FlatAtlasActor || !SingleComponentActor || !SingleMergedComponent ||
        !SplitComponentActor || !SplitBarkComponent || !SplitFoliageComponent)
    {
        OutSummary += TEXT(
            "V43 merged-component parity bracket could not resolve the flat, single, and split HLOD actors.\n");
        return false;
    }

    auto SetSourceMaterialState = [](UMeshComponent* Component)
    {
        bool bUpdated = false;
        for (int32 MaterialIndex = 0;
             MaterialIndex < Component->GetNumMaterials();
             ++MaterialIndex)
        {
            UMaterialInstanceDynamic* DynamicMaterial =
                Cast<UMaterialInstanceDynamic>(Component->GetMaterial(MaterialIndex));
            if (!DynamicMaterial)
            {
                DynamicMaterial = Component->CreateDynamicMaterialInstance(MaterialIndex);
            }
            if (DynamicMaterial)
            {
                DynamicMaterial->SetScalarParameterValue(
                    TEXT("ComplementarySourceCoverage"),
                    1.0f);
                DynamicMaterial->SetScalarParameterValue(
                    TEXT("ComplementaryPatternSize"),
                    8.0f);
                DynamicMaterial->SetScalarParameterValue(
                    TEXT("ComplementaryTransitionMode"),
                    1.0f);
                bUpdated = true;
            }
        }
        return bUpdated;
    };
    if (!SetSourceMaterialState(SingleMergedComponent) ||
        !SetSourceMaterialState(SplitBarkComponent) ||
        !SetSourceMaterialState(SplitFoliageComponent))
    {
        OutSummary += TEXT(
            "V43 merged-component parity bracket could not align source material state on all exact-geometry controls.\n");
        return false;
    }

    FlatAtlasActor->SetActorHiddenInGame(true);
    SingleComponentActor->SetActorHiddenInGame(!bShowSingleComponent);
    SplitComponentActor->SetActorHiddenInGame(!bShowSplitComponents);
    SplitBarkComponent->SetCastShadow(bBarkCastsShadow);
    SplitBarkComponent->bCastStaticShadow = bBarkCastsShadow;
    SplitBarkComponent->bCastDynamicShadow = bBarkCastsShadow;
    SplitFoliageComponent->SetCastShadow(false);
    SplitFoliageComponent->bCastStaticShadow = false;
    SplitFoliageComponent->bCastDynamicShadow = false;
    SplitFoliageComponent->SetCastContactShadow(false);
    SplitBarkComponent->MarkRenderStateDirty();
    SplitFoliageComponent->MarkRenderStateDirty();
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    return true;
}

bool SetFutaleufuHlodAtlasFrameOverride(
    UWorld* World,
    float FrameOverride,
    FString& OutSummary)
{
    AActor* HlodActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (*It && It->GetActorLabel() == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            HlodActor = *It;
            break;
        }
    }
    if (!HlodActor)
    {
        OutSummary += TEXT("V38 frame search could not resolve the HLOD actor.\n");
        return false;
    }

    TInlineComponentArray<UMeshComponent*> MeshComponents;
    HlodActor->GetComponents(MeshComponents);
    bool bUpdated = false;
    for (UMeshComponent* Component : MeshComponents)
    {
        if (!Component)
        {
            continue;
        }
        for (int32 MaterialIndex = 0;
             MaterialIndex < Component->GetNumMaterials();
             ++MaterialIndex)
        {
            UMaterialInstanceDynamic* DynamicMaterial =
                Cast<UMaterialInstanceDynamic>(Component->GetMaterial(MaterialIndex));
            if (!DynamicMaterial)
            {
                DynamicMaterial = Component->CreateDynamicMaterialInstance(MaterialIndex);
            }
            if (DynamicMaterial)
            {
                DynamicMaterial->SetScalarParameterValue(
                    TEXT("AtlasFrameOverride"),
                    FrameOverride);
                bUpdated = true;
            }
        }
    }
    return bUpdated;
}

bool SetFutaleufuHlodSplitShadingOverrides(
    UWorld* World,
    float TrunkGainMultiplier,
    float FoliageGainMultiplier,
    float TrunkRoughness,
    float FoliageRoughness,
    float TrunkSpecular,
    float FoliageSpecular,
    FString& OutSummary)
{
    AActor* HlodActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (*It && It->GetActorLabel() == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            HlodActor = *It;
            break;
        }
    }
    if (!HlodActor)
    {
        OutSummary += TEXT("V39 split-shading search could not resolve the HLOD actor.\n");
        return false;
    }

    TInlineComponentArray<UMeshComponent*> MeshComponents;
    HlodActor->GetComponents(MeshComponents);
    bool bUpdated = false;
    for (UMeshComponent* Component : MeshComponents)
    {
        if (!Component)
        {
            continue;
        }
        for (int32 MaterialIndex = 0;
             MaterialIndex < Component->GetNumMaterials();
             ++MaterialIndex)
        {
            UMaterialInstanceDynamic* DynamicMaterial =
                Cast<UMaterialInstanceDynamic>(Component->GetMaterial(MaterialIndex));
            if (!DynamicMaterial)
            {
                DynamicMaterial = Component->CreateDynamicMaterialInstance(MaterialIndex);
            }
            if (!DynamicMaterial)
            {
                continue;
            }
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasTrunkGainMultiplier"),
                TrunkGainMultiplier);
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasFoliageGainMultiplier"),
                FoliageGainMultiplier);
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasTrunkRoughness"),
                TrunkRoughness);
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasFoliageRoughness"),
                FoliageRoughness);
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasTrunkSpecular"),
                TrunkSpecular);
            DynamicMaterial->SetScalarParameterValue(
                TEXT("AtlasFoliageSpecular"),
                FoliageSpecular);
            bUpdated = true;
        }
    }
    return bUpdated;
}

bool SetFutaleufuHlodProxyLayerMode(
    UWorld* World,
    bool bUseDualLayer,
    FString& OutSummary)
{
    AActor* HlodActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (*It && It->GetActorLabel() == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            HlodActor = *It;
            break;
        }
    }
    if (!HlodActor)
    {
        OutSummary += TEXT("V40 dual-layer review could not resolve the HLOD actor.\n");
        return false;
    }

    int32 CombinedLayerCount = 0;
    int32 TrunkLayerCount = 0;
    int32 FoliageLayerCount = 0;
    TInlineComponentArray<UMeshComponent*> MeshComponents;
    HlodActor->GetComponents(MeshComponents);
    for (UMeshComponent* Component : MeshComponents)
    {
        if (!Component)
        {
            continue;
        }
        if (Component->ComponentHasTag(TEXT("RaftSimHlodCombinedLayer")))
        {
            Component->SetVisibility(!bUseDualLayer, true);
            ++CombinedLayerCount;
        }
        else if (Component->ComponentHasTag(TEXT("RaftSimHlodTrunkLayer")))
        {
            Component->SetVisibility(bUseDualLayer, true);
            ++TrunkLayerCount;
        }
        else if (Component->ComponentHasTag(TEXT("RaftSimHlodFoliageLayer")))
        {
            Component->SetVisibility(bUseDualLayer, true);
            ++FoliageLayerCount;
        }
    }
    return CombinedLayerCount == 1 && TrunkLayerCount == 1 &&
        FoliageLayerCount == 1;
}

bool SetFutaleufuHlodFoliageTransmissionTint(
    UWorld* World,
    const FLinearColor& TransmissionTint,
    FString& OutSummary)
{
    AActor* HlodActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (*It && It->GetActorLabel() == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
        {
            HlodActor = *It;
            break;
        }
    }
    if (!HlodActor)
    {
        OutSummary += TEXT(
            "V40 dual-layer review could not resolve the foliage HLOD actor.\n");
        return false;
    }

    TInlineComponentArray<UMeshComponent*> MeshComponents;
    HlodActor->GetComponents(MeshComponents);
    for (UMeshComponent* Component : MeshComponents)
    {
        if (!Component ||
            !Component->ComponentHasTag(TEXT("RaftSimHlodFoliageLayer")))
        {
            continue;
        }
        UMaterialInstanceDynamic* DynamicMaterial =
            Cast<UMaterialInstanceDynamic>(Component->GetMaterial(0));
        if (!DynamicMaterial)
        {
            DynamicMaterial = Component->CreateDynamicMaterialInstance(0);
        }
        if (DynamicMaterial)
        {
            DynamicMaterial->SetVectorParameterValue(
                TEXT("AtlasFoliageTransmissionTint"),
                TransmissionTint);
            return true;
        }
    }
    OutSummary += TEXT(
        "V40 dual-layer review could not update the foliage transmission material.\n");
    return false;
}

ADirectionalLight* FindFutaleufuTransmissionBracketSun(UWorld* World)
{
    for (TActorIterator<ADirectionalLight> It(World); It; ++It)
    {
        ADirectionalLight* Candidate = *It;
        if (!Candidate)
        {
            continue;
        }
        if (Candidate->GetActorLabel() == TEXT("RaftSim_Sun_LumenPreview"))
        {
            return Candidate;
        }
    }
    return nullptr;
}

bool SetFutaleufuTransmissionBracketLightDirection(
    UWorld* World,
    ACameraActor* ReferenceCamera,
    AActor* HlodActor,
    bool bBacklit,
    FString& OutSummary)
{
    ADirectionalLight* Sun = FindFutaleufuTransmissionBracketSun(World);
    UDirectionalLightComponent* SunComponent = Sun
        ? Cast<UDirectionalLightComponent>(Sun->GetLightComponent())
        : nullptr;
    if (!Sun || !SunComponent || !ReferenceCamera || !HlodActor)
    {
        OutSummary += TEXT(
            "V41 transmission bracket could not resolve the sun, camera, or HLOD actor.\n");
        return false;
    }

    FVector CameraToTree =
        HlodActor->GetActorLocation() - ReferenceCamera->GetActorLocation();
    CameraToTree.Z = 0.0f;
    if (!CameraToTree.Normalize())
    {
        OutSummary += TEXT(
            "V41 transmission bracket found a degenerate camera-to-tree light basis.\n");
        return false;
    }
    const FVector HorizontalTravel = bBacklit ? -CameraToTree : CameraToTree;
    const FVector LightTravelDirection = FVector(
        HorizontalTravel.X,
        HorizontalTravel.Y,
        -0.65f).GetSafeNormal();
    SunComponent->SetMobility(EComponentMobility::Movable);
    Sun->SetActorRotation(LightTravelDirection.Rotation());
    SunComponent->MarkRenderStateDirty();
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    return true;
}

bool CaptureFutaleufuComplementaryTransitionMotionSequence(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& RelativeCaptureBase,
    const FString& AuthorityMode,
    int32 PatternSize,
    TArray<FString>& OutRelativeCapturePaths,
    FString& OutSummary,
    bool bLitRiverView,
    const TFunction<bool(
        UWorld*,
        ACameraActor*&,
        AActor*&,
        FVector&,
        FVector&,
        FVector&,
        FString&)>& SceneSetup,
    float TransitionMode,
    bool bHlodFrameSearch,
    int32* OutAutomaticHlodFrame,
    bool bHlodSplitShadingSearch,
    bool bHlodDualLayerReview,
    bool bHlodTransmissionLightBracketReview,
    bool bHlodMergedGeometryShapeBracketReview,
    bool bHlodMergedComponentParityReview)
{
    const int32 InitialCapturePathCount = OutRelativeCapturePaths.Num();
    constexpr int32 CaptureWidth = 1280;
    constexpr int32 CaptureHeight = 720;
    constexpr int32 WarmupFrameCount = 8;
    constexpr int32 TransitionFrameCount = 41;
    constexpr int32 CoverageTransitionFrameCount = 31;
    constexpr int32 SettleFrameCount = 8;
    constexpr float FixedDeltaSeconds = 1.0f / 60.0f;
    constexpr float StartRadiusCm = 2300.0f;
    constexpr float CameraStepCm = 10.0f;
    constexpr float LateralOffsetCm = 800.0f;

    const FString MapFilename = FPackageName::LongPackageNameToFilename(
        Spec.MapPackagePath,
        FPackageName::GetMapPackageExtension());
    UWorld* World = FPaths::FileExists(MapFilename)
        ? UEditorLoadingAndSavingUtils::LoadMap(MapFilename)
        : nullptr;
    if (!World)
    {
        OutSummary += FString::Printf(
            TEXT("V34 motion sequence could not load %s for %s.\n"),
            *Spec.MapPackagePath,
            *AuthorityMode);
        return false;
    }

    FlushAsyncLoading();
    World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();

    ACameraActor* ReferenceCamera = nullptr;
    AActor* HlodActor = nullptr;
    FVector MotionForward = FVector::ForwardVector;
    FVector MotionRight = FVector::RightVector;
    FVector ViewTargetOffset = FVector::ZeroVector;
    bool bSceneReady = false;
    if (SceneSetup)
    {
        bSceneReady = SceneSetup(
            World,
            ReferenceCamera,
            HlodActor,
            MotionForward,
            MotionRight,
            ViewTargetOffset,
            OutSummary);
    }
    else
    {
        ReferenceCamera =
            FindPreviewCaptureCamera(World, TEXT("RaftSim_PveTemporal_23m00"));
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (*It && It->GetActorLabel() == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
            {
                HlodActor = *It;
                break;
            }
        }
        bSceneReady = ReferenceCamera && HlodActor;
    }
    MotionForward.Z = 0.0f;
    MotionRight.Z = 0.0f;
    MotionForward.Normalize();
    MotionRight.Normalize();
    if (!bSceneReady || !ReferenceCamera || !ReferenceCamera->GetCameraComponent() ||
        !HlodActor || MotionForward.IsNearlyZero() || MotionRight.IsNearlyZero())
    {
        OutSummary += FString::Printf(
            TEXT("Persistent transition sequence could not resolve its camera, HLOD actor, and motion basis for %s.\n"),
            *AuthorityMode);
        return false;
    }

    UTextureRenderTarget2D* RenderTarget =
        NewObject<UTextureRenderTarget2D>(GetTransientPackage(), NAME_None, RF_Transient);
    if (!RenderTarget)
    {
        OutSummary += TEXT("V34 motion sequence could not allocate a render target.\n");
        return false;
    }
    RenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    RenderTarget->ClearColor = FLinearColor::Black;
    RenderTarget->InitAutoFormat(CaptureWidth, CaptureHeight);
    RenderTarget->UpdateResourceImmediate(true);

    ASceneCapture2D* SceneCapture = World->SpawnActor<ASceneCapture2D>(
        ASceneCapture2D::StaticClass(),
        ReferenceCamera->GetActorLocation(),
        ReferenceCamera->GetActorRotation());
    USceneCaptureComponent2D* CaptureComponent =
        SceneCapture ? SceneCapture->GetCaptureComponent2D() : nullptr;
    if (!SceneCapture || !CaptureComponent)
    {
        RenderTarget->ReleaseResource();
        OutSummary += TEXT("V34 motion sequence could not create a persistent scene capture.\n");
        return false;
    }

    FMinimalViewInfo CameraView;
    ReferenceCamera->GetCameraComponent()->GetCameraView(0.0f, CameraView);
    CaptureComponent->SetCameraView(CameraView);
    CaptureComponent->PostProcessSettings =
        ReferenceCamera->GetCameraComponent()->PostProcessSettings;
    CaptureComponent->PostProcessBlendWeight = 1.0f;
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->CaptureSource = SCS_FinalColorLDR;
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    CaptureComponent->bAlwaysPersistRenderingState = true;
    CaptureComponent->bExcludeFromSceneTextureExtents = !bLitRiverView;
    CaptureComponent->ShowFlags.SetSelection(false);
    CaptureComponent->ShowFlags.SetModeWidgets(false);
    CaptureComponent->ShowFlags.SetCompositeEditorPrimitives(false);
    CaptureComponent->ShowFlags.SetLighting(bLitRiverView);
    CaptureComponent->ShowFlags.SetPostProcessing(true);
    CaptureComponent->ShowFlags.SetAtmosphere(bLitRiverView);
    CaptureComponent->ShowFlags.SetFog(bLitRiverView);
    CaptureComponent->ShowFlags.SetAntiAliasing(true);
    CaptureComponent->ShowFlags.SetTemporalAA(true);
    CaptureComponent->ShowFlags.SetMotionBlur(false);
    CaptureComponent->ShowFlags.SetEyeAdaptation(false);
    CaptureComponent->ShowFlags.SetAmbientOcclusion(bLitRiverView);
    CaptureComponent->ShowFlags.SetGlobalIllumination(bLitRiverView);
    CaptureComponent->ShowFlags.SetLumenGlobalIllumination(bLitRiverView);
    CaptureComponent->ShowFlags.SetLumenReflections(bLitRiverView);
    CaptureComponent->ShowFlags.SetScreenSpaceReflections(bLitRiverView);
    CaptureComponent->ShowFlags.SetReflectionEnvironment(bLitRiverView);
    IConsoleVariable* AntiAliasingMethodVariable =
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"));
    const int32 PreviousAntiAliasingMethod =
        AntiAliasingMethodVariable ? AntiAliasingMethodVariable->GetInt() : -1;
    if (AntiAliasingMethodVariable)
    {
        AntiAliasingMethodVariable->Set(2, ECVF_SetByCode);
    }
    auto RestoreAntiAliasingMethod = [
                                         AntiAliasingMethodVariable,
                                         PreviousAntiAliasingMethod]()
    {
        if (AntiAliasingMethodVariable && PreviousAntiAliasingMethod >= 0)
        {
            AntiAliasingMethodVariable->Set(
                PreviousAntiAliasingMethod,
                ECVF_SetByCode);
        }
    };

    const FVector Target = HlodActor->GetActorLocation();
    const float CameraHeight = ReferenceCamera->GetActorLocation().Z;
    auto SetCameraState = [
                              ReferenceCamera,
                              SceneCapture,
                              Target,
                              ViewTargetOffset,
                              CameraHeight,
                              MotionForward,
                              MotionRight](float RadiusCm)
    {
        const float AxialDistanceCm = FMath::Sqrt(
            FMath::Max(0.0f, FMath::Square(RadiusCm) - FMath::Square(LateralOffsetCm)));
        FVector CameraLocation =
            Target - MotionForward * AxialDistanceCm - MotionRight * LateralOffsetCm;
        CameraLocation.Z = CameraHeight;
        const FRotator CameraRotation =
            (Target + ViewTargetOffset - CameraLocation).Rotation();
        ReferenceCamera->SetActorLocationAndRotation(CameraLocation, CameraRotation);
        SceneCapture->SetActorLocationAndRotation(CameraLocation, CameraRotation);
    };
    auto SetFrameState = [
                             World,
                             ReferenceCamera,
                             AuthorityMode,
                             PatternSize,
                             TransitionMode,
                             &SetCameraState,
                             &OutSummary](float RadiusCm, float SourceCoverage)
    {
        SetCameraState(RadiusCm);
        return ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            AuthorityMode,
            SourceCoverage,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
    };
    auto AdvanceAndCapture = [World, CaptureComponent]()
    {
        World->Tick(LEVELTICK_All, FixedDeltaSeconds);
        World->SendAllEndOfFrameUpdates();
        CaptureComponent->CaptureScene();
        FlushRenderingCommands();
    };
    auto SaveCurrentFrame = [RenderTarget](const FString& RelativeCapturePath)
    {
        FTextureRenderTargetResource* Resource =
            RenderTarget->GameThread_GetRenderTargetResource();
        TArray<FColor> Pixels;
        if (!Resource || !Resource->ReadPixels(Pixels) ||
            Pixels.Num() != CaptureWidth * CaptureHeight)
        {
            return false;
        }
        TArray64<uint8> CompressedPng;
        FImageUtils::PNGCompressImageArray(
            CaptureWidth,
            CaptureHeight,
            MakeArrayView(Pixels),
            CompressedPng);
        const FString AbsoluteCapturePath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(GetRepoRoot(), RelativeCapturePath));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsoluteCapturePath), true);
        return FFileHelper::SaveArrayToFile(CompressedPng, *AbsoluteCapturePath);
    };

    if (bHlodFrameSearch)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        constexpr float AtlasAzimuthOffsetTurns = 16.0f / 360.0f;
        bool bAllSearchFramesSaved = true;
        SetCameraState(SearchRadiusCm);
        const FVector ViewToCamera =
            (ReferenceCamera->GetActorLocation() - Target).GetSafeNormal();
        float NormalizedAzimuth = FMath::Fmod(
            FMath::Atan2(ViewToCamera.Y, ViewToCamera.X) / (2.0f * PI) -
                AtlasAzimuthOffsetTurns + 1.0f,
            1.0f);
        if (NormalizedAzimuth < 0.0f)
        {
            NormalizedAzimuth += 1.0f;
        }
        const int32 AutomaticAzimuthFrame =
            FMath::RoundToInt(NormalizedAzimuth * 8.0f) % 8;
        if (OutAutomaticHlodFrame)
        {
            *OutAutomaticHlodFrame = AutomaticAzimuthFrame;
        }

        bAllSearchFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("source_only"),
            1.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        bAllSearchFramesSaved &=
            SetFutaleufuHlodAtlasFrameOverride(World, -1.0f, OutSummary);
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString SourcePath = FString::Printf(
            TEXT("%s_hlod_frame_search_source_reference.png"),
            *RelativeCaptureBase);
        const bool bSourceSaved = SaveCurrentFrame(SourcePath);
        bAllSearchFramesSaved &= bSourceSaved;
        if (bSourceSaved)
        {
            OutRelativeCapturePaths.Add(SourcePath);
        }

        bAllSearchFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("hlod_only"),
            0.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        for (int32 SearchIndex = -1; SearchIndex < 8; ++SearchIndex)
        {
            bAllSearchFramesSaved &= SetFutaleufuHlodAtlasFrameOverride(
                World,
                static_cast<float>(SearchIndex),
                OutSummary);
            for (int32 WarmupIndex = 0;
                 WarmupIndex < WarmupFrameCount;
                 ++WarmupIndex)
            {
                AdvanceAndCapture();
            }
            const FString SearchPath = SearchIndex < 0
                ? FString::Printf(
                      TEXT("%s_hlod_frame_search_automatic.png"),
                      *RelativeCaptureBase)
                : FString::Printf(
                      TEXT("%s_hlod_frame_search_override_frame%02d.png"),
                      *RelativeCaptureBase,
                      SearchIndex);
            const bool bSearchSaved = SaveCurrentFrame(SearchPath);
            bAllSearchFramesSaved &= bSearchSaved;
            if (bSearchSaved)
            {
                OutRelativeCapturePaths.Add(SearchPath);
            }
        }

        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += FString::Printf(
            TEXT("V38 HLOD frame search saved source, automatic, and eight row-zero override captures at 24.5 m; the material calculation selects automatic frame %d from normalized azimuth %.6f.\n"),
            AutomaticAzimuthFrame,
            NormalizedAzimuth);
        return bAllSearchFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 10;
    }

    if (bHlodSplitShadingSearch)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        constexpr float DefaultRoughness = 0.68f;
        constexpr float DefaultSpecular = 0.18f;
        bool bAllSearchFramesSaved = true;
        SetCameraState(SearchRadiusCm);
        bAllSearchFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("source_only"),
            1.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        bAllSearchFramesSaved &=
            SetFutaleufuHlodAtlasFrameOverride(World, -1.0f, OutSummary);
        bAllSearchFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            DefaultRoughness,
            DefaultRoughness,
            DefaultSpecular,
            DefaultSpecular,
            OutSummary);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString SourcePath = FString::Printf(
            TEXT("%s_hlod_split_shading_source_reference.png"),
            *RelativeCaptureBase);
        const bool bSourceSaved = SaveCurrentFrame(SourcePath);
        bAllSearchFramesSaved &= bSourceSaved;
        if (bSourceSaved)
        {
            OutRelativeCapturePaths.Add(SourcePath);
        }

        bAllSearchFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("hlod_only"),
            0.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        struct FSplitShadingPreset
        {
            const TCHAR* Token;
            float TrunkGain;
            float FoliageGain;
        };
        static const FSplitShadingPreset Presets[] = {
            {TEXT("baseline"), 1.0f, 1.0f},
            {TEXT("foliage_gain_150"), 1.0f, 1.50f},
            {TEXT("foliage_gain_200"), 1.0f, 2.00f},
            {TEXT("foliage_gain_250"), 1.0f, 2.50f},
            {TEXT("trunk_gain_150"), 1.50f, 1.0f},
            {TEXT("trunk_gain_200"), 2.00f, 1.0f},
            {TEXT("trunk_gain_250"), 2.50f, 1.0f},
            {TEXT("balanced_gain_175"), 1.75f, 1.75f},
            {TEXT("balanced_gain_200"), 2.00f, 2.00f},
        };
        for (const FSplitShadingPreset& Preset : Presets)
        {
            bAllSearchFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
                World,
                Preset.TrunkGain,
                Preset.FoliageGain,
                DefaultRoughness,
                DefaultRoughness,
                DefaultSpecular,
                DefaultSpecular,
                OutSummary);
            SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
            for (int32 WarmupIndex = 0;
                 WarmupIndex < WarmupFrameCount;
                 ++WarmupIndex)
            {
                AdvanceAndCapture();
            }
            const FString SearchPath = FString::Printf(
                TEXT("%s_hlod_split_shading_%s.png"),
                *RelativeCaptureBase,
                Preset.Token);
            const bool bSearchSaved = SaveCurrentFrame(SearchPath);
            bAllSearchFramesSaved &= bSearchSaved;
            if (bSearchSaved)
            {
                OutRelativeCapturePaths.Add(SearchPath);
            }
        }
        bAllSearchFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            DefaultRoughness,
            DefaultRoughness,
            DefaultSpecular,
            DefaultSpecular,
            OutSummary);

        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += TEXT(
            "V39 HLOD split-shading search saved one source reference and nine temporally independent exact material-identity gain presets at 24.5 m.\n");
        return bAllSearchFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 10;
    }

    if (bHlodDualLayerReview)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        constexpr float TrunkRoughness = 0.62f;
        constexpr float FoliageRoughness = 0.72f;
        constexpr float TrunkSpecular = 0.12f;
        constexpr float FoliageSpecular = 0.18f;
        const FLinearColor SourceTransmissionTint(0.78f, 1.0f, 0.58f, 1.0f);
        bool bAllFramesSaved = true;
        SetCameraState(SearchRadiusCm);
        bAllFramesSaved &= SetFutaleufuHlodAtlasFrameOverride(
            World,
            -1.0f,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            false,
            OutSummary);
        bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("source_only"),
            1.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString SourcePath = FString::Printf(
            TEXT("%s_hlod_dual_layer_source_reference.png"),
            *RelativeCaptureBase);
        const bool bSourceSaved = SaveCurrentFrame(SourcePath);
        bAllFramesSaved &= bSourceSaved;
        if (bSourceSaved)
        {
            OutRelativeCapturePaths.Add(SourcePath);
        }

        bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
            World,
            ReferenceCamera,
            TEXT("hlod_only"),
            0.0f,
            OutSummary,
            static_cast<float>(PatternSize),
            TransitionMode);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString CombinedPath = FString::Printf(
            TEXT("%s_hlod_dual_layer_combined_default_lit_control.png"),
            *RelativeCaptureBase);
        const bool bCombinedSaved = SaveCurrentFrame(CombinedPath);
        bAllFramesSaved &= bCombinedSaved;
        if (bCombinedSaved)
        {
            OutRelativeCapturePaths.Add(CombinedPath);
        }

        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            true,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            TrunkRoughness,
            FoliageRoughness,
            TrunkSpecular,
            FoliageSpecular,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodFoliageTransmissionTint(
            World,
            FLinearColor::Black,
            OutSummary);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString NoTransmissionPath = FString::Printf(
            TEXT("%s_hlod_dual_layer_two_sided_no_transmission.png"),
            *RelativeCaptureBase);
        const bool bNoTransmissionSaved = SaveCurrentFrame(NoTransmissionPath);
        bAllFramesSaved &= bNoTransmissionSaved;
        if (bNoTransmissionSaved)
        {
            OutRelativeCapturePaths.Add(NoTransmissionPath);
        }

        bAllFramesSaved &= SetFutaleufuHlodFoliageTransmissionTint(
            World,
            SourceTransmissionTint,
            OutSummary);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString SourceTransmissionPath = FString::Printf(
            TEXT("%s_hlod_dual_layer_two_sided_source_transmission.png"),
            *RelativeCaptureBase);
        const bool bSourceTransmissionSaved = SaveCurrentFrame(SourceTransmissionPath);
        bAllFramesSaved &= bSourceTransmissionSaved;
        if (bSourceTransmissionSaved)
        {
            OutRelativeCapturePaths.Add(SourceTransmissionPath);
        }

        bAllFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.5f,
            TrunkRoughness,
            FoliageRoughness,
            TrunkSpecular,
            FoliageSpecular,
            OutSummary);
        SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
        for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
        {
            AdvanceAndCapture();
        }
        const FString SourceTransmissionGainPath = FString::Printf(
            TEXT("%s_hlod_dual_layer_two_sided_source_transmission_foliage_gain_150.png"),
            *RelativeCaptureBase);
        const bool bSourceTransmissionGainSaved =
            SaveCurrentFrame(SourceTransmissionGainPath);
        bAllFramesSaved &= bSourceTransmissionGainSaved;
        if (bSourceTransmissionGainSaved)
        {
            OutRelativeCapturePaths.Add(SourceTransmissionGainPath);
        }

        bAllFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            TrunkRoughness,
            FoliageRoughness,
            TrunkSpecular,
            FoliageSpecular,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            false,
            OutSummary);
        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += TEXT(
            "V40 HLOD dual-layer review saved one source, one combined control, and three temporally independent bark/foliage layer captures at 24.5 m.\n");
        return bAllFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 5;
    }

    if (bHlodTransmissionLightBracketReview)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        constexpr float TrunkRoughness = 0.62f;
        constexpr float FoliageRoughness = 0.72f;
        constexpr float TrunkSpecular = 0.12f;
        constexpr float FoliageSpecular = 0.18f;
        const FLinearColor SourceTransmissionTint(0.78f, 1.0f, 0.58f, 1.0f);
        ADirectionalLight* BracketSun = FindFutaleufuTransmissionBracketSun(World);
        UDirectionalLightComponent* BracketSunComponent = BracketSun
            ? Cast<UDirectionalLightComponent>(BracketSun->GetLightComponent())
            : nullptr;
        if (!BracketSun || !BracketSunComponent)
        {
            RestoreAntiAliasingMethod();
            SceneCapture->Destroy();
            RenderTarget->ReleaseResource();
            OutSummary += TEXT(
                "V41 transmission bracket could not preserve the physical-corridor sun.\n");
            return false;
        }
        const FRotator OriginalSunRotation = BracketSun->GetActorRotation();
        const EComponentMobility::Type OriginalSunMobility =
            BracketSunComponent->Mobility;
        bool bAllFramesSaved = true;
        SetCameraState(SearchRadiusCm);
        bAllFramesSaved &= SetFutaleufuHlodAtlasFrameOverride(
            World,
            -1.0f,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            true,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            TrunkRoughness,
            FoliageRoughness,
            TrunkSpecular,
            FoliageSpecular,
            OutSummary);

        const auto CaptureBracketFrame = [
            &AdvanceAndCapture,
            &SaveCurrentFrame,
            SceneCapture,
            &OutRelativeCapturePaths](const FString& CapturePath)
        {
            SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
            for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
            {
                AdvanceAndCapture();
            }
            const bool bSaved = SaveCurrentFrame(CapturePath);
            if (bSaved)
            {
                OutRelativeCapturePaths.Add(CapturePath);
            }
            return bSaved;
        };
        struct FTransmissionBracketLightPreset
        {
            const TCHAR* Token;
            bool bBacklit;
        };
        static const FTransmissionBracketLightPreset LightPresets[] = {
            {TEXT("frontlit"), false},
            {TEXT("backlit"), true},
        };
        for (const FTransmissionBracketLightPreset& LightPreset : LightPresets)
        {
            bAllFramesSaved &= SetFutaleufuTransmissionBracketLightDirection(
                World,
                ReferenceCamera,
                HlodActor,
                LightPreset.bBacklit,
                OutSummary);
            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("source_only"),
                1.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_transmission_light_bracket_%s_source_reference.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("hlod_only"),
                0.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= SetFutaleufuHlodFoliageTransmissionTint(
                World,
                FLinearColor::Black,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_transmission_light_bracket_%s_two_sided_no_transmission.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= SetFutaleufuHlodFoliageTransmissionTint(
                World,
                SourceTransmissionTint,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_transmission_light_bracket_%s_two_sided_source_transmission.png"),
                *RelativeCaptureBase,
                LightPreset.Token));
        }

        BracketSunComponent->SetMobility(EComponentMobility::Movable);
        BracketSun->SetActorRotation(OriginalSunRotation);
        BracketSunComponent->SetMobility(OriginalSunMobility);
        BracketSunComponent->MarkRenderStateDirty();
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            false,
            OutSummary);
        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += TEXT(
            "V41 HLOD transmission light bracket saved source, no-transmission, and source-transmission captures under fixed frontlight and backlight directions at 24.5 m.\n");
        return bAllFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 6;
    }

    if (bHlodMergedComponentParityReview)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        ADirectionalLight* BracketSun = FindFutaleufuTransmissionBracketSun(World);
        UDirectionalLightComponent* BracketSunComponent = BracketSun
            ? Cast<UDirectionalLightComponent>(BracketSun->GetLightComponent())
            : nullptr;
        if (!BracketSun || !BracketSunComponent)
        {
            RestoreAntiAliasingMethod();
            SceneCapture->Destroy();
            RenderTarget->ReleaseResource();
            OutSummary += TEXT(
                "V43 merged-component parity bracket could not preserve the physical-corridor sun.\n");
            return false;
        }
        const FRotator OriginalSunRotation = BracketSun->GetActorRotation();
        const EComponentMobility::Type OriginalSunMobility =
            BracketSunComponent->Mobility;
        bool bAllFramesSaved = true;
        SetCameraState(SearchRadiusCm);

        const auto CaptureBracketFrame = [
            &AdvanceAndCapture,
            &SaveCurrentFrame,
            SceneCapture,
            &OutRelativeCapturePaths](const FString& CapturePath)
        {
            SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
            for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
            {
                AdvanceAndCapture();
            }
            const bool bSaved = SaveCurrentFrame(CapturePath);
            if (bSaved)
            {
                OutRelativeCapturePaths.Add(CapturePath);
            }
            return bSaved;
        };
        struct FMergedComponentParityLightPreset
        {
            const TCHAR* Token;
            bool bBacklit;
        };
        static const FMergedComponentParityLightPreset LightPresets[] = {
            {TEXT("frontlit"), false},
            {TEXT("backlit"), true},
        };
        for (const FMergedComponentParityLightPreset& LightPreset : LightPresets)
        {
            bAllFramesSaved &= SetFutaleufuTransmissionBracketLightDirection(
                World,
                ReferenceCamera,
                HlodActor,
                LightPreset.bBacklit,
                OutSummary);

            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("source_only"),
                1.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= SetFutaleufuMergedGeometryComponentParityMode(
                World,
                false,
                false,
                false,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_component_parity_%s_source_reference.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("hlod_only"),
                0.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= SetFutaleufuMergedGeometryComponentParityMode(
                World,
                true,
                false,
                false,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_component_parity_%s_merged_single_no_shadow.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= SetFutaleufuMergedGeometryComponentParityMode(
                World,
                false,
                true,
                false,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_component_parity_%s_merged_split_no_shadow.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= SetFutaleufuMergedGeometryComponentParityMode(
                World,
                false,
                true,
                true,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_component_parity_%s_merged_split_source_shadow.png"),
                *RelativeCaptureBase,
                LightPreset.Token));
        }

        BracketSunComponent->SetMobility(EComponentMobility::Movable);
        BracketSun->SetActorRotation(OriginalSunRotation);
        BracketSunComponent->SetMobility(OriginalSunMobility);
        BracketSunComponent->MarkRenderStateDirty();
        bAllFramesSaved &= SetFutaleufuMergedGeometryComponentParityMode(
            World,
            false,
            false,
            false,
            OutSummary);
        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += TEXT(
            "V43 merged-component parity bracket saved source, single-component no-shadow, split-component no-shadow, and split-component source-shadow captures under fixed frontlight and backlight directions at 24.5 m.\n");
        return bAllFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 8;
    }

    if (bHlodMergedGeometryShapeBracketReview)
    {
        constexpr float SearchRadiusCm = 2450.0f;
        constexpr float TrunkRoughness = 0.62f;
        constexpr float FoliageRoughness = 0.72f;
        constexpr float TrunkSpecular = 0.12f;
        constexpr float FoliageSpecular = 0.18f;
        const FLinearColor SourceTransmissionTint(0.78f, 1.0f, 0.58f, 1.0f);
        ADirectionalLight* BracketSun = FindFutaleufuTransmissionBracketSun(World);
        UDirectionalLightComponent* BracketSunComponent = BracketSun
            ? Cast<UDirectionalLightComponent>(BracketSun->GetLightComponent())
            : nullptr;
        if (!BracketSun || !BracketSunComponent)
        {
            RestoreAntiAliasingMethod();
            SceneCapture->Destroy();
            RenderTarget->ReleaseResource();
            OutSummary += TEXT(
                "V42 merged-geometry bracket could not preserve the physical-corridor sun.\n");
            return false;
        }
        const FRotator OriginalSunRotation = BracketSun->GetActorRotation();
        const EComponentMobility::Type OriginalSunMobility =
            BracketSunComponent->Mobility;
        bool bAllFramesSaved = true;
        SetCameraState(SearchRadiusCm);
        bAllFramesSaved &= SetFutaleufuHlodAtlasFrameOverride(
            World,
            -1.0f,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            true,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodSplitShadingOverrides(
            World,
            1.0f,
            1.0f,
            TrunkRoughness,
            FoliageRoughness,
            TrunkSpecular,
            FoliageSpecular,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodFoliageTransmissionTint(
            World,
            SourceTransmissionTint,
            OutSummary);

        const auto CaptureBracketFrame = [
            &AdvanceAndCapture,
            &SaveCurrentFrame,
            SceneCapture,
            &OutRelativeCapturePaths](const FString& CapturePath)
        {
            SceneCapture->GetCaptureComponent2D()->bCameraCutThisFrame = true;
            for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
            {
                AdvanceAndCapture();
            }
            const bool bSaved = SaveCurrentFrame(CapturePath);
            if (bSaved)
            {
                OutRelativeCapturePaths.Add(CapturePath);
            }
            return bSaved;
        };
        struct FMergedGeometryBracketLightPreset
        {
            const TCHAR* Token;
            bool bBacklit;
        };
        static const FMergedGeometryBracketLightPreset LightPresets[] = {
            {TEXT("frontlit"), false},
            {TEXT("backlit"), true},
        };
        for (const FMergedGeometryBracketLightPreset& LightPreset : LightPresets)
        {
            bAllFramesSaved &= SetFutaleufuTransmissionBracketLightDirection(
                World,
                ReferenceCamera,
                HlodActor,
                LightPreset.bBacklit,
                OutSummary);

            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("source_only"),
                1.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= SetFutaleufuMergedGeometryHlodBracketMode(
                World,
                false,
                false,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_geometry_shape_bracket_%s_source_reference.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= ConfigureFutaleufuComplementaryTransitionCapture(
                World,
                ReferenceCamera,
                TEXT("hlod_only"),
                0.0f,
                OutSummary,
                static_cast<float>(PatternSize),
                TransitionMode);
            bAllFramesSaved &= SetFutaleufuMergedGeometryHlodBracketMode(
                World,
                true,
                false,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_geometry_shape_bracket_%s_flat_hlod_control.png"),
                *RelativeCaptureBase,
                LightPreset.Token));

            bAllFramesSaved &= SetFutaleufuMergedGeometryHlodBracketMode(
                World,
                false,
                true,
                OutSummary);
            bAllFramesSaved &= CaptureBracketFrame(FString::Printf(
                TEXT("%s_hlod_merged_geometry_shape_bracket_%s_merged_geometry_hlod.png"),
                *RelativeCaptureBase,
                LightPreset.Token));
        }

        BracketSunComponent->SetMobility(EComponentMobility::Movable);
        BracketSun->SetActorRotation(OriginalSunRotation);
        BracketSunComponent->SetMobility(OriginalSunMobility);
        BracketSunComponent->MarkRenderStateDirty();
        bAllFramesSaved &= SetFutaleufuMergedGeometryHlodBracketMode(
            World,
            true,
            false,
            OutSummary);
        bAllFramesSaved &= SetFutaleufuHlodProxyLayerMode(
            World,
            false,
            OutSummary);
        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += TEXT(
            "V42 merged-geometry HLOD bracket saved source, flat-atlas control, and source-material merged-geometry captures under fixed frontlight and backlight directions at 24.5 m.\n");
        return bAllFramesSaved &&
            OutRelativeCapturePaths.Num() - InitialCapturePathCount == 6;
    }

    bool bAllFramesSaved = true;
    const FString SequenceToken = TransitionMode >= 0.5f
        ? TEXT("motion_temporal_lit_river_view")
        : (bLitRiverView
        ? TEXT("motion_8x8_lit_river_view")
        : (PatternSize >= 8
               ? TEXT("motion_8x8")
               : TEXT("motion")));
    if (!SetFrameState(StartRadiusCm, 1.0f))
    {
        RestoreAntiAliasingMethod();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        return false;
    }
    for (int32 WarmupIndex = 0; WarmupIndex < WarmupFrameCount; ++WarmupIndex)
    {
        AdvanceAndCapture();
    }
    for (int32 FrameIndex = 0; FrameIndex < TransitionFrameCount; ++FrameIndex)
    {
        const float RadiusCm = StartRadiusCm + CameraStepCm * FrameIndex;
        const float SourceCoverage = FrameIndex < CoverageTransitionFrameCount
            ? 1.0f - static_cast<float>(FrameIndex) /
                static_cast<float>(CoverageTransitionFrameCount - 1)
            : 0.0f;
        bAllFramesSaved &= SetFrameState(RadiusCm, SourceCoverage);
        AdvanceAndCapture();
        const int32 RadiusIntegerCm = FMath::RoundToInt(RadiusCm);
        const FString DistanceToken = FString::Printf(
            TEXT("%02dm%02d"),
            RadiusIntegerCm / 100,
            RadiusIntegerCm % 100);
        const FString RelativeCapturePath = FString::Printf(
            TEXT("%s_%s_f%03d_%s_%s.png"),
            *RelativeCaptureBase,
            *SequenceToken,
            FrameIndex,
            *DistanceToken,
            *AuthorityMode);
        const bool bSaved = SaveCurrentFrame(RelativeCapturePath);
        bAllFramesSaved &= bSaved;
        if (bSaved)
        {
            OutRelativeCapturePaths.Add(RelativeCapturePath);
        }
    }
    constexpr float EndRadiusCm =
        StartRadiusCm + CameraStepCm * (TransitionFrameCount - 1);
    for (int32 SettleIndex = 0; SettleIndex < SettleFrameCount; ++SettleIndex)
    {
        bAllFramesSaved &= SetFrameState(EndRadiusCm, 0.0f);
        AdvanceAndCapture();
        const int32 FrameIndex = TransitionFrameCount + SettleIndex;
        const FString RelativeCapturePath = FString::Printf(
            TEXT("%s_%s_f%03d_settle%02d_27m00_%s.png"),
            *RelativeCaptureBase,
            *SequenceToken,
            FrameIndex,
            SettleIndex + 1,
            *AuthorityMode);
        const bool bSaved = SaveCurrentFrame(RelativeCapturePath);
        bAllFramesSaved &= bSaved;
        if (bSaved)
        {
            OutRelativeCapturePaths.Add(RelativeCapturePath);
        }
    }

    RestoreAntiAliasingMethod();
    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();
    OutSummary += FString::Printf(
        TEXT("Persistent same-world %s%s motion sequence saved %d frames with %s complementary ownership, 8 warm-up frames, 41 transition frames, 8 endpoint-settle frames, and a fixed 60 Hz simulation delta.\n"),
        *AuthorityMode,
        bLitRiverView ? TEXT(" lit river-view") : TEXT(""),
        TransitionFrameCount + SettleFrameCount,
        TransitionMode >= 0.5f
            ? TEXT("engine temporal-AA")
            : *FString::Printf(TEXT("a %dx%d ordered pattern"), PatternSize, PatternSize));
    return bAllFramesSaved &&
        OutRelativeCapturePaths.Num() - InitialCapturePathCount ==
            TransitionFrameCount + SettleFrameCount;
}
} // namespace RaftSimEditorEnvironment
