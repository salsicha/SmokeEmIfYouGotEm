#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

bool FRaftSimEditorModule::CreateFutaleufuCordilleraCypressFamily(FString& OutSummary)
{
    return CreateFutaleufuCordilleraCypressReview(false, false, OutSummary);
}

bool FRaftSimEditorModule::CreateFutaleufuCordilleraCypressOpaqueNearReview(
    FString& OutSummary)
{
    return CreateFutaleufuCordilleraCypressReview(true, false, OutSummary);
}

bool FRaftSimEditorModule::CreateFutaleufuCordilleraCypressVolumetricNearReview(
    FString& OutSummary)
{
    return CreateFutaleufuCordilleraCypressReview(true, true, OutSummary);
}

bool FRaftSimEditorModule::CreateFutaleufuCordilleraCypressReview(
    bool bOpaqueNearGeometry,
    bool bVolumetricNearGeometry,
    FString& OutSummary)
{
    OutSummary.Reset();
    TMap<FString, UTexture2D*> Textures;
    if (!CreateFutaleufuCordilleraCypressTextureAssets(Textures, OutSummary))
    {
        OutSummary += TEXT("Cordilleran-cypress texture creation failed; geometry was not authored.\n");
        return false;
    }
    UMaterial* BarkMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCordilleraCypress_Bark"), false, Textures, OutSummary);
    UMaterial* NearSprayMaterial = bOpaqueNearGeometry
        ? CreateOrUpdateFutaleufuCypressNearSprayMaterial(
              bVolumetricNearGeometry
                  ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V15_VolumetricNearGeometry")
                  : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V14_OpaqueNearGeometry"),
              OutSummary,
              bVolumetricNearGeometry)
        : CreateOrUpdateFutaleufuNativeCanopyMaterial(
              TEXT("M_RaftSim_FutaleufuCordilleraCypress_V12_NearSprays"),
              true,
              Textures,
              OutSummary,
              false,
              TEXT("Near"));
    UMaterial* FarSprayMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCordilleraCypress_V12_FarSprays"),
        true,
        Textures,
        OutSummary,
        false,
        TEXT("Far"));
    if (!BarkMaterial || !NearSprayMaterial || !FarSprayMaterial)
    {
        return false;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += TEXT("Could not create the isolated cordilleran-cypress review map.\n");
        return false;
    }

    struct FCypressRuntime
    {
        FFutaleufuCordilleraCypressForm Form;
        FVector WorldOffset = FVector::ZeroVector;
        TArray<FVector> WoodyVertices;
        TArray<int32> WoodyTriangles;
        TArray<FVector> WoodyNormals;
        TArray<FVector2D> WoodyUVs;
        TArray<FVector> NearSprayVertices;
        TArray<int32> NearSprayTriangles;
        TArray<FVector> NearSprayNormals;
        TArray<FVector2D> NearSprayUVs;
        TArray<FVector> SprayVertices;
        TArray<int32> SprayTriangles;
        TArray<FVector> SprayNormals;
        TArray<FVector2D> SprayUVs;
        FVector CloseupCamera = FVector::ZeroVector;
        FVector CloseupTarget = FVector::ZeroVector;
        FString WoodyPackagePath;
        FString NearSprayPackagePath;
        FString SprayPackagePath;
        UStaticMesh* WoodyMesh = nullptr;
        UStaticMesh* NearSprayMesh = nullptr;
        UStaticMesh* SprayMesh = nullptr;
        AStaticMeshActor* NearSprayActor = nullptr;
        AStaticMeshActor* FarSprayActor = nullptr;
    };
    auto MakeForm = [](
                        const TCHAR* Id,
                        const TCHAR* DisplayName,
                        const TCHAR* AssetToken,
                        const TCHAR* LifeStage,
                        int32 SeedOffset,
                        int32 BranchCount,
                        float HeightCm,
                        float BaseRadiusCm,
                        float CrownBaseCm,
                        float CrownRadiusCm,
                        float BranchUplift,
                        float Asymmetry)
    {
        FFutaleufuCordilleraCypressForm Form;
        Form.Id = Id;
        Form.DisplayName = DisplayName;
        Form.AssetToken = AssetToken;
        Form.LifeStage = LifeStage;
        Form.SeedOffset = SeedOffset;
        Form.BranchCount = BranchCount;
        Form.HeightCm = HeightCm;
        Form.BaseRadiusCm = BaseRadiusCm;
        Form.CrownBaseCm = CrownBaseCm;
        Form.CrownRadiusCm = CrownRadiusCm;
        Form.BranchUplift = BranchUplift;
        Form.Asymmetry = Asymmetry;
        return Form;
    };

    TArray<FCypressRuntime> Variants;
    Variants.SetNum(8);
    Variants[0].Form = MakeForm(
        TEXT("open_grown_conical"), TEXT("open-grown conical adult"), TEXT("OpenGrownConicalAdult"),
        TEXT("adult"), 18427, 46, 2400.0f, 82.0f, 360.0f, 620.0f, 1.0f, 1.10f);
    Variants[1].Form = MakeForm(
        TEXT("closed_grove_columnar"), TEXT("closed-grove columnar adult"), TEXT("ClosedGroveColumnarAdult"),
        TEXT("adult"), 22409, 44, 2500.0f, 68.0f, 650.0f, 390.0f, 1.16f, 0.82f);
    Variants[1].Form.SuppressedSectorCenterDegrees = 245.0f;
    Variants[1].Form.SuppressedSectorHalfWidthDegrees = 48.0f;
    Variants[1].Form.SuppressedSectorLengthScale = 0.52f;
    Variants[2].Form = MakeForm(
        TEXT("rocky_slope_asymmetric"), TEXT("rocky-slope asymmetric adult"), TEXT("RockySlopeAsymmetricAdult"),
        TEXT("adult"), 26407, 40, 2100.0f, 72.0f, 450.0f, 540.0f, 1.08f, 1.48f);
    Variants[2].Form.TrunkLeanTopCm = FVector2D(175.0f, -95.0f);
    Variants[2].Form.SuppressedSectorCenterDegrees = 190.0f;
    Variants[2].Form.SuppressedSectorHalfWidthDegrees = 72.0f;
    Variants[2].Form.SuppressedSectorLengthScale = 0.28f;
    Variants[3].Form = MakeForm(
        TEXT("storm_damaged"), TEXT("storm-damaged adult"), TEXT("StormDamagedAdult"),
        TEXT("adult"), 30403, 42, 2050.0f, 76.0f, 390.0f, 560.0f, 0.94f, 1.32f);
    Variants[3].Form.TrunkLeanTopCm = FVector2D(-80.0f, 60.0f);
    Variants[3].Form.DamageModulo = 5;
    Variants[3].Form.DamageRemainder = 2;
    Variants[3].Form.DamagedBranchLengthScale = 0.30f;
    Variants[3].Form.CrownGapCenterT = 0.58f;
    Variants[3].Form.CrownGapHalfWidthT = 0.075f;
    Variants[3].Form.CrownGapLengthScale = 0.42f;
    Variants[4].Form = MakeForm(
        TEXT("coigue_transition_edge"), TEXT("coigue-transition edge adult"), TEXT("CoigueTransitionEdgeAdult"),
        TEXT("adult"), 34403, 43, 2300.0f, 74.0f, 520.0f, 520.0f, 1.12f, 1.36f);
    Variants[4].Form.TrunkLeanTopCm = FVector2D(95.0f, 120.0f);
    Variants[4].Form.SuppressedSectorCenterDegrees = 60.0f;
    Variants[4].Form.SuppressedSectorHalfWidthDegrees = 64.0f;
    Variants[4].Form.SuppressedSectorLengthScale = 0.22f;
    Variants[5].Form = MakeForm(
        TEXT("grove_intermediate"), TEXT("grove intermediate"), TEXT("GroveIntermediate"),
        TEXT("intermediate"), 38401, 30, 1300.0f, 38.0f, 260.0f, 290.0f, 1.0f, 0.92f);
    Variants[6].Form = MakeForm(
        TEXT("suppressed_intermediate"), TEXT("suppressed intermediate"), TEXT("SuppressedIntermediate"),
        TEXT("intermediate"), 42397, 24, 850.0f, 24.0f, 300.0f, 165.0f, 1.18f, 0.78f);
    Variants[6].Form.TrunkLeanTopCm = FVector2D(45.0f, 20.0f);
    Variants[6].Form.SuppressedSectorCenterDegrees = 210.0f;
    Variants[6].Form.SuppressedSectorHalfWidthDegrees = 95.0f;
    Variants[6].Form.SuppressedSectorLengthScale = 0.36f;
    Variants[7].Form = MakeForm(
        TEXT("released_intermediate"), TEXT("released intermediate"), TEXT("ReleasedIntermediate"),
        TEXT("intermediate"), 46381, 34, 1500.0f, 44.0f, 250.0f, 370.0f, 1.05f, 1.52f);
    Variants[7].Form.TrunkLeanTopCm = FVector2D(-70.0f, 85.0f);
    Variants[7].Form.CrownGapCenterT = 0.38f;
    Variants[7].Form.CrownGapHalfWidthT = 0.06f;
    Variants[7].Form.CrownGapLengthScale = 0.56f;
    for (int32 VariantIndex = 0; VariantIndex < Variants.Num(); ++VariantIndex)
    {
        Variants[VariantIndex].WorldOffset = FVector(VariantIndex * 500000.0f, 0.0f, 0.0f);
    }

    static const FString MeshRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
             "CordilleraCypress/Meshes/");
    bool bActorsComplete = true;
    for (FCypressRuntime& Variant : Variants)
    {
        BuildFutaleufuCordilleraCypressGeometry(
            Variant.Form,
            bOpaqueNearGeometry,
            bVolumetricNearGeometry,
            Variant.WoodyVertices,
            Variant.WoodyTriangles,
            Variant.WoodyNormals,
            Variant.WoodyUVs,
            Variant.NearSprayVertices,
            Variant.NearSprayTriangles,
            Variant.NearSprayNormals,
            Variant.NearSprayUVs,
            Variant.SprayVertices,
            Variant.SprayTriangles,
            Variant.SprayNormals,
            Variant.SprayUVs,
            Variant.CloseupCamera,
            Variant.CloseupTarget);
        const FString ProceduralStem = FString::Printf(
            TEXT("RaftSim_FutaleufuCordilleraCypress_%s_Procedural"),
            *Variant.Form.AssetToken);
        AActor* WoodyProceduralActor = AddPreviewProceduralMeshActor(
            World,
            ProceduralStem + TEXT("_Woody"),
            Variant.WoodyVertices,
            Variant.WoodyTriangles,
            Variant.WoodyNormals,
            Variant.WoodyUVs,
            FLinearColor::White,
            BarkMaterial,
            nullptr,
            false);
        AActor* NearSprayProceduralActor = AddPreviewProceduralMeshActor(
            World,
            ProceduralStem + TEXT("_NearTexturedSprays"),
            Variant.NearSprayVertices,
            Variant.NearSprayTriangles,
            Variant.NearSprayNormals,
            Variant.NearSprayUVs,
            FLinearColor::White,
            NearSprayMaterial,
            nullptr,
            false);
        AActor* SprayProceduralActor = AddPreviewProceduralMeshActor(
            World,
            ProceduralStem + TEXT("_Sprays"),
            Variant.SprayVertices,
            Variant.SprayTriangles,
            Variant.SprayNormals,
            Variant.SprayUVs,
            FLinearColor::White,
            FarSprayMaterial,
            nullptr,
            false);
        if (!WoodyProceduralActor || !NearSprayProceduralActor || !SprayProceduralActor)
        {
            OutSummary += FString::Printf(
                TEXT("Could not construct the %s procedural mesh actors.\n"),
                *Variant.Form.DisplayName);
            return false;
        }
        const FString AssetStem = FString::Printf(
            TEXT("SM_RaftSim_FutaleufuCordilleraCypress_%s_%s"),
            *Variant.Form.AssetToken,
            bVolumetricNearGeometry
                ? TEXT("V15")
                : (bOpaqueNearGeometry ? TEXT("V14") : TEXT("V12")));
        Variant.WoodyPackagePath = MeshRoot + AssetStem + TEXT("_Woody");
        Variant.NearSprayPackagePath = MeshRoot + AssetStem +
            (bVolumetricNearGeometry
                 ? TEXT("_NearVolumetricScaleLeafClusters")
                 : (bOpaqueNearGeometry
                        ? TEXT("_NearOpaqueScaleLeafClusters")
                        : TEXT("_NearTexturedSprays")));
        Variant.SprayPackagePath = MeshRoot + AssetStem + TEXT("_FarSprays");
        Variant.WoodyMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            WoodyProceduralActor,
            Variant.WoodyPackagePath,
            BarkMaterial,
            bVolumetricNearGeometry,
            ENaniteShapePreservation::None,
            OutSummary);
        Variant.NearSprayMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            NearSprayProceduralActor,
            Variant.NearSprayPackagePath,
            NearSprayMaterial,
            false,
            ENaniteShapePreservation::None,
            OutSummary);
        Variant.SprayMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            SprayProceduralActor,
            Variant.SprayPackagePath,
            FarSprayMaterial,
            false,
            ENaniteShapePreservation::None,
            OutSummary);
        WoodyProceduralActor->Destroy();
        NearSprayProceduralActor->Destroy();
        SprayProceduralActor->Destroy();
        if (!Variant.WoodyMesh || !Variant.NearSprayMesh || !Variant.SprayMesh)
        {
            return false;
        }

        const FTransform VariantTransform(FRotator::ZeroRotator, Variant.WorldOffset);
        AStaticMeshActor* WoodyActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        AStaticMeshActor* NearSprayActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        AStaticMeshActor* SprayActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        Variant.NearSprayActor = NearSprayActor;
        Variant.FarSprayActor = SprayActor;
        bActorsComplete &= WoodyActor && NearSprayActor && SprayActor;
        if (!WoodyActor || !NearSprayActor || !SprayActor)
        {
            continue;
        }
        WoodyActor->SetActorLabel(FString::Printf(
            TEXT("RaftSim_FutaleufuCordilleraCypress_%s_Woody"),
            *Variant.Form.AssetToken));
        WoodyActor->GetStaticMeshComponent()->SetStaticMesh(Variant.WoodyMesh);
        WoodyActor->GetStaticMeshComponent()->SetMaterial(0, BarkMaterial);
        WoodyActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        WoodyActor->GetStaticMeshComponent()->SetCastShadow(true);
        NearSprayActor->SetActorLabel(FString::Printf(
            TEXT("RaftSim_FutaleufuCordilleraCypress_%s_%s"),
            *Variant.Form.AssetToken,
            bVolumetricNearGeometry
                ? TEXT("NearVolumetricScaleLeafClusters")
                : (bOpaqueNearGeometry
                       ? TEXT("NearOpaqueScaleLeafClusters")
                       : TEXT("NearTexturedSprays"))));
        NearSprayActor->GetStaticMeshComponent()->SetStaticMesh(Variant.NearSprayMesh);
        NearSprayActor->GetStaticMeshComponent()->SetMaterial(0, NearSprayMaterial);
        NearSprayActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        NearSprayActor->GetStaticMeshComponent()->SetCastShadow(false);
        NearSprayActor->GetStaticMeshComponent()->SetCullDistance(2800.0f);
        SprayActor->SetActorLabel(FString::Printf(
            TEXT("RaftSim_FutaleufuCordilleraCypress_%s_FarSprays"),
            *Variant.Form.AssetToken));
        SprayActor->GetStaticMeshComponent()->SetStaticMesh(Variant.SprayMesh);
        SprayActor->GetStaticMeshComponent()->SetMaterial(0, FarSprayMaterial);
        SprayActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        SprayActor->GetStaticMeshComponent()->SetCastShadow(false);
        SprayActor->GetStaticMeshComponent()->MinDrawDistance = 2800.0f;
        SprayActor->GetStaticMeshComponent()->bCastDynamicShadow = false;
        SprayActor->GetStaticMeshComponent()->bCastStaticShadow = false;
        SprayActor->GetStaticMeshComponent()->bCastContactShadow = false;
        SprayActor->GetStaticMeshComponent()->bAffectDistanceFieldLighting = false;
        SprayActor->GetStaticMeshComponent()->bAffectDynamicIndirectLighting = false;
    }

    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    bool bGroundComplete = PlaneMesh != nullptr;
    for (const FCypressRuntime& Variant : Variants)
    {
        AStaticMeshActor* GroundActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                Variant.WorldOffset + FVector(0.0f, 0.0f, -4.0f),
                FVector(150.0f, 150.0f, 1.0f)));
        bGroundComplete &= GroundActor && GroundActor->GetStaticMeshComponent();
        if (GroundActor && GroundActor->GetStaticMeshComponent())
        {
            GroundActor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_FutaleufuCordilleraCypress_%s_NeutralGround"),
                *Variant.Form.AssetToken));
            GroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
            GroundActor->GetStaticMeshComponent()->SetMaterial(0, LoadPreviewBaseMaterial());
            GroundActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    }

    FRaftSimEnvironmentPreviewSpec ReviewSpec;
    ReviewSpec.RiverId = TEXT("futaleufu_cordillera_cypress");
    ReviewSpec.DisplayName = TEXT("Futaleufu project-owned cordilleran-cypress family");
    ReviewSpec.MapPackagePath =
        bVolumetricNearGeometry
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
                   "L_FutaleufuCordilleraCypress_V15_VolumetricNearGeometryReview")
            : bOpaqueNearGeometry
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
                   "L_FutaleufuCordilleraCypress_V14_OpaqueNearGeometryReview")
            : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
                   "L_FutaleufuCordilleraCypress_V12_SparseBranchSprayReview");
    ReviewSpec.FoliageColor = FLinearColor(0.13f, 0.28f, 0.10f);
    ReviewSpec.RockColor = FLinearColor(0.31f, 0.30f, 0.27f);
    AddPreviewLightRig(World, ReviewSpec);
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        if (It->GetLightComponent())
        {
            It->GetLightComponent()->SetIntensity(1.55f);
            It->GetLightComponent()->RecaptureSky();
        }
    }
    ADirectionalLight* FillLight = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(), FTransform(FRotator(-30.0f, 38.0f, 0.0f)));
    if (FillLight && FillLight->GetLightComponent())
    {
        FillLight->SetActorLabel(TEXT("RaftSim_CordilleraCypress_NeutralFill"));
        FillLight->GetLightComponent()->SetIntensity(0.62f);
        FillLight->GetLightComponent()->SetLightColor(FLinearColor(0.96f, 0.99f, 1.0f));
        FillLight->GetLightComponent()->SetCastShadows(false);
    }

    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(TEXT("futaleufu_terminator"));
    auto AddReviewCamera = [World, CaptureSettings](
                               const FString& Label,
                               const FVector& Location,
                               const FVector& Target,
                               float FieldOfView)
    {
        ACameraActor* Camera = World->SpawnActor<ACameraActor>(
            ACameraActor::StaticClass(),
            FTransform((Target - Location).Rotation(), Location));
        if (!Camera || !Camera->GetCameraComponent())
        {
            return false;
        }
        Camera->SetActorLabel(Label);
        UCameraComponent* CameraComponent = Camera->GetCameraComponent();
        CameraComponent->FieldOfView = FieldOfView;
        FPostProcessSettings& Settings = CameraComponent->PostProcessSettings;
        Settings.bOverride_AutoExposureMethod = true;
        Settings.AutoExposureMethod = AEM_Manual;
        Settings.bOverride_AutoExposureBias = true;
        Settings.AutoExposureBias = CaptureSettings.ExposureBias;
        Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Settings.AutoExposureApplyPhysicalCameraExposure = 0;
        Settings.bOverride_ColorSaturation = true;
        Settings.ColorSaturation = FVector4(
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            1.0f);
        Settings.bOverride_ColorContrast = true;
        Settings.ColorContrast = FVector4(
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            1.0f);
        Settings.bOverride_Sharpen = true;
        Settings.Sharpen = CaptureSettings.Sharpen;
        Settings.bOverride_FilmGrainIntensity = true;
        Settings.FilmGrainIntensity = 0.0f;
        return true;
    };

    struct FCypressCaptureRequest
    {
        FString RelativePath;
        FString CameraLabel;
        FString CaptureId;
        FString Description;
        FString AuthorityMode = TEXT("combined");
        bool bCaptured = false;
    };
    TArray<FCypressCaptureRequest> CaptureRequests;
    bool bCamerasComplete = true;
    const TCHAR* CaptureVersion = bVolumetricNearGeometry
        ? TEXT("v15")
        : (bOpaqueNearGeometry ? TEXT("v14") : TEXT("v12"));
    for (const FCypressRuntime& Variant : Variants)
    {
        const FVector CrownTarget = Variant.WorldOffset + FVector(
            0.0f,
            0.0f,
            Variant.Form.CrownBaseCm +
                (Variant.Form.HeightCm - Variant.Form.CrownBaseCm) * 0.46f);
        struct FViewDefinition
        {
            const TCHAR* CameraSuffix;
            const TCHAR* CaptureSuffix;
            const TCHAR* Description;
            FVector Location;
            FVector Target;
            float FieldOfView;
        };
        const FViewDefinition Views[] = {
            {TEXT("Turntable035"), TEXT("turntable_azimuth_035"), TEXT("turntable azimuth 35"),
             Variant.WorldOffset + FVector(-5600.0f, -3920.0f, 1420.0f), CrownTarget, 48.0f},
            {TEXT("Turntable145"), TEXT("turntable_azimuth_145"), TEXT("turntable azimuth 145"),
             Variant.WorldOffset + FVector(5600.0f, -3920.0f, 1420.0f), CrownTarget, 48.0f},
            {TEXT("BarkSprayCloseup"), TEXT("bark_spray_closeup"), TEXT("bark and spray closeup"),
             Variant.WorldOffset + Variant.CloseupCamera,
             Variant.WorldOffset + Variant.CloseupTarget, 38.0f},
            {TEXT("RiverDistance60m"), TEXT("river_distance_60m"), TEXT("60 m river-distance proxy"),
             Variant.WorldOffset + FVector(-6000.0f, -700.0f, 1450.0f), CrownTarget, 43.0f},
            {TEXT("RiverDistance150m"), TEXT("river_distance_150m"), TEXT("150 m river-distance proxy"),
             Variant.WorldOffset + FVector(-15000.0f, -1200.0f, 1550.0f), CrownTarget, 24.0f}};
        for (const FViewDefinition& View : Views)
        {
            FCypressCaptureRequest Request;
            Request.CameraLabel = FString::Printf(
                TEXT("RaftSim_CordilleraCypress_%s_%s"),
                *Variant.Form.AssetToken,
                View.CameraSuffix);
            Request.CaptureId = Variant.Form.Id + TEXT("_") + View.CaptureSuffix;
            Request.RelativePath = FString::Printf(
                TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                     "futaleufu_cordillera_cypress_%s_%s_%s.png"),
                CaptureVersion,
                *Variant.Form.Id,
                View.CaptureSuffix);
            if (Request.CaptureId.Contains(TEXT("bark_spray_closeup")) ||
                (bVolumetricNearGeometry &&
                 (Request.CaptureId.Contains(TEXT("turntable")) ||
                  Request.CaptureId.Contains(TEXT("river_distance_60m")))))
            {
                Request.AuthorityMode = TEXT("near_only");
            }
            Request.Description = FString::Printf(
                TEXT("cordilleran cypress %s %s"),
                *Variant.Form.DisplayName,
                View.Description);
            bCamerasComplete &= AddReviewCamera(
                Request.CameraLabel,
                View.Location,
                View.Target,
                View.FieldOfView);
            CaptureRequests.Add(MoveTemp(Request));
        }
        if (Variant.Form.Id == TEXT("open_grown_conical") ||
            Variant.Form.Id == TEXT("closed_grove_columnar") ||
            Variant.Form.Id == TEXT("grove_intermediate"))
        {
            const float TransitionDistancesCm[] = {2000.0f, 2800.0f, 3600.0f};
            const TCHAR* TransitionTokens[] = {TEXT("20m"), TEXT("28m"), TEXT("36m")};
            const TCHAR* AuthorityTokens[] = {
                TEXT("near_only"), TEXT("far_only"), TEXT("combined")};
            for (int32 TransitionIndex = 0; TransitionIndex < 3; ++TransitionIndex)
            {
                for (int32 AuthorityIndex = 0; AuthorityIndex < 3; ++AuthorityIndex)
                {
                    FCypressCaptureRequest Request;
                    Request.AuthorityMode = AuthorityTokens[AuthorityIndex];
                    Request.CameraLabel = FString::Printf(
                        TEXT("RaftSim_CordilleraCypress_%s_Handoff%s_%s"),
                        *Variant.Form.AssetToken,
                        TransitionTokens[TransitionIndex],
                        AuthorityTokens[AuthorityIndex]);
                    Request.CaptureId = FString::Printf(
                        TEXT("%s_handoff_%s_%s"),
                        *Variant.Form.Id,
                        TransitionTokens[TransitionIndex],
                        AuthorityTokens[AuthorityIndex]);
                    Request.RelativePath = FString::Printf(
                        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                             "futaleufu_cordillera_cypress_%s_%s_handoff_%s_%s.png"),
                        CaptureVersion,
                        *Variant.Form.Id,
                        TransitionTokens[TransitionIndex],
                        AuthorityTokens[AuthorityIndex]);
                    Request.Description = FString::Printf(
                        TEXT("cordilleran cypress %s handoff %s authority %s"),
                        *Variant.Form.DisplayName,
                        TransitionTokens[TransitionIndex],
                        AuthorityTokens[AuthorityIndex]);
                    const FVector CameraLocation = Variant.WorldOffset + FVector(
                        -TransitionDistancesCm[TransitionIndex], -420.0f, 1280.0f);
                    bCamerasComplete &= AddReviewCamera(
                        Request.CameraLabel, CameraLocation, CrownTarget, 44.0f);
                    CaptureRequests.Add(MoveTemp(Request));
                }
            }
        }
    }

    bool bGeometryValidated = true;
    for (const FCypressRuntime& Variant : Variants)
    {
        const FVector WoodyBounds = Variant.WoodyMesh->GetBoundingBox().GetSize();
        const FVector NearSprayBounds = Variant.NearSprayMesh->GetBoundingBox().GetSize();
        const FVector SprayBounds = Variant.SprayMesh->GetBoundingBox().GetSize();
        const int32 NearTriangleCount = Variant.NearSprayTriangles.Num() / 3;
        bGeometryValidated &=
            Variant.Form.HeightCm >= 250.0f &&
            Variant.Form.HeightCm <= 2500.0f &&
            Variant.WoodyMesh->GetNumVertices(0) > 500 &&
            Variant.NearSprayMesh->GetNumVertices(0) > 500 &&
            Variant.SprayMesh->GetNumVertices(0) > 500 &&
            Variant.NearSprayTriangles.Num() % 3 == 0 &&
            (bVolumetricNearGeometry
                 ? (NearTriangleCount >= 150000 &&
                    NearTriangleCount <= 400000 &&
                    NearTriangleCount % 256 == 0)
                 : (NearTriangleCount >= 800 &&
                    NearTriangleCount <= 1900 &&
                    (!bOpaqueNearGeometry || NearTriangleCount % 6 == 0))) &&
            Variant.SprayTriangles.Num() % 6 == 0 &&
            WoodyBounds.Z >= Variant.Form.HeightCm * 0.92f &&
            NearSprayBounds.X >= Variant.Form.CrownRadiusCm * 0.65f &&
            SprayBounds.X >= Variant.Form.CrownRadiusCm * 0.65f &&
            Variant.WoodyMesh->IsNaniteEnabled() == bVolumetricNearGeometry &&
            !Variant.NearSprayMesh->IsNaniteEnabled() &&
            !Variant.SprayMesh->IsNaniteEnabled();
    }
    const bool bSceneComplete =
        bActorsComplete && bGroundComplete && FillLight && FillLight->GetLightComponent() &&
        bCamerasComplete && bGeometryValidated && CaptureRequests.Num() == 67;
    FString MapSummary;
    const bool bMapSaved = bSceneComplete &&
        SavePreviewWorld(World, ReviewSpec.MapPackagePath, MapSummary);
    OutSummary += MapSummary;

    bool bCaptured = bMapSaved;
    if (bMapSaved)
    {
        for (FCypressCaptureRequest& Request : CaptureRequests)
        {
            const FString AuthorityMode = Request.AuthorityMode;
            Request.bCaptured = CapturePreviewImageForSpec(
                ReviewSpec,
                GetRepoRoot(),
                Request.RelativePath,
                Request.CameraLabel,
                Request.CaptureId,
                Request.Description,
                false,
                OutSummary,
                [AuthorityMode, bOpaqueNearGeometry, bVolumetricNearGeometry](
                    UWorld* CaptureWorld,
                    ACameraActor* CaptureCamera,
                    FString& SetupSummary)
                {
                    const bool bNearOnly = AuthorityMode == TEXT("near_only");
                    const bool bFarOnly = AuthorityMode == TEXT("far_only");
                    constexpr bool bNearRepresentationEligible = false;
                    constexpr float ActorRootSelectionDistanceCm = 2800.0f;
                    int32 NearActorCount = 0;
                    int32 FarActorCount = 0;
                    for (TActorIterator<AStaticMeshActor> It(CaptureWorld); It; ++It)
                    {
                        AStaticMeshActor* Actor = *It;
                        UStaticMeshComponent* Component =
                            Actor ? Actor->GetStaticMeshComponent() : nullptr;
                        if (!Actor || !Component)
                        {
                            continue;
                        }
                        const FString Label = Actor->GetActorLabel();
                        const bool bNearActor = bVolumetricNearGeometry
                            ? Label.Contains(TEXT("_NearVolumetricScaleLeafClusters"))
                            : (bOpaqueNearGeometry
                                   ? Label.Contains(TEXT("_NearOpaqueScaleLeafClusters"))
                                   : Label.Contains(TEXT("_NearTexturedSprays")));
                        if (bNearActor)
                        {
                            ++NearActorCount;
                            const float RootDistance = CaptureCamera
                                ? FVector::Distance(
                                      CaptureCamera->GetActorLocation(), Actor->GetActorLocation())
                                : TNumericLimits<float>::Max();
                            const bool bCombinedSelectsNear =
                                !bNearOnly && !bFarOnly && bNearRepresentationEligible &&
                                RootDistance < ActorRootSelectionDistanceCm;
                            const bool bShowNear = bNearOnly || bCombinedSelectsNear;
                            Actor->SetActorHiddenInGame(!bShowNear);
                            Component->SetVisibility(bShowNear, true);
                            Component->SetCullDistance(0.0f);
                        }
                        else if (Label.Contains(TEXT("_FarSprays")))
                        {
                            ++FarActorCount;
                            const float RootDistance = CaptureCamera
                                ? FVector::Distance(
                                      CaptureCamera->GetActorLocation(), Actor->GetActorLocation())
                                : TNumericLimits<float>::Max();
                            const bool bCombinedSelectsNear =
                                !bNearOnly && !bFarOnly && bNearRepresentationEligible &&
                                RootDistance < ActorRootSelectionDistanceCm;
                            const bool bShowFar = bFarOnly || (!bNearOnly && !bCombinedSelectsNear);
                            Actor->SetActorHiddenInGame(!bShowFar);
                            Component->SetVisibility(bShowFar, true);
                            Component->MinDrawDistance = 0.0f;
                        }
                    }
                    const bool bComplete = NearActorCount == 8 && FarActorCount == 8;
                    if (!bComplete)
                    {
                        SetupSummary += FString::Printf(
                            TEXT("Cypress authority setup found %d near and %d far actors; expected 8 each.\n"),
                            NearActorCount,
                            FarActorCount);
                    }
                    return bComplete;
                });
            bCaptured &= Request.bCaptured;
        }
    }

    TSharedRef<FJsonObject> ReportObject = MakeShared<FJsonObject>();
    ReportObject->SetStringField(
        TEXT("schema"),
        bVolumetricNearGeometry
            ? TEXT("raftsim.unreal.futaleufu_cordillera_cypress_volumetric_near_family.v15")
            : bOpaqueNearGeometry
            ? TEXT("raftsim.unreal.futaleufu_cordillera_cypress_opaque_near_family.v14")
            : TEXT("raftsim.unreal.futaleufu_cordillera_cypress_isolated_family.v12"));
    ReportObject->SetStringField(
        TEXT("status"),
        bCaptured
            ? (bVolumetricNearGeometry
                   ? TEXT("v15_volumetric_scale_leaf_family_captured_pending_human_review")
                   : bOpaqueNearGeometry
                   ? TEXT("v14_opaque_connected_scale_leaf_family_captured_pending_human_review")
                   : TEXT("v12_sparse_branch_scale_near_candidate_family_captured_pending_human_review"))
            : TEXT("isolated_unreal_family_capture_incomplete"));
    ReportObject->SetBoolField(TEXT("production_promoted"), false);
    ReportObject->SetBoolField(TEXT("corridor_substitution_performed"), false);
    ReportObject->SetStringField(TEXT("species"), TEXT("Austrocedrus chilensis"));
    ReportObject->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    ReportObject->SetStringField(TEXT("map_asset"), ReviewSpec.MapPackagePath);
    ReportObject->SetBoolField(TEXT("map_saved"), bMapSaved);
    ReportObject->SetBoolField(TEXT("geometry_contract_passed"), bGeometryValidated);
    ReportObject->SetNumberField(TEXT("form_count"), Variants.Num());
    ReportObject->SetNumberField(TEXT("adult_form_count"), 5);
    ReportObject->SetNumberField(TEXT("intermediate_form_count"), 3);
    ReportObject->SetStringField(
        TEXT("authoring_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/"
             "FutaleufuNativeCanopy/CordilleraCypress/"
             "futaleufu_cordillera_cypress_authoring_manifest.json"));
    ReportObject->SetStringField(
        TEXT("texture_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/"
             "FutaleufuNativeCanopy/CordilleraCypress/"
             "futaleufu_cordillera_cypress_v10_texture_manifest.json"));
    ReportObject->SetStringField(
        TEXT("far_texture_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/"
             "FutaleufuNativeCanopy/CordilleraCypress/"
             "futaleufu_cordillera_cypress_texture_manifest.json"));
    ReportObject->SetStringField(
        TEXT("foliage_representation"),
        bVolumetricNearGeometry
            ? TEXT("V15 adds project-owned connected brown central and secondary twigs carrying eight overlapping fusiform opaque scale-leaf volumes on a deterministic 50 percent sample of branch systems; V10 far atlas geometry remains separate and actor-root fallback remains authoritative pending review")
            : bOpaqueNearGeometry
            ? TEXT("V14 retains the V10 primary distribution but replaces masked whole-spray cards with one project-owned welded three-lobe opaque six-triangle scale-leaf cluster attached directly to a deterministic 11 percent sample of branch systems; V10 far atlas geometry remains separate and actor-root fallback remains authoritative pending review")
            : TEXT("V12 restored V10 primary distribution with one enlarged flattened V10 broad-spray card on a deterministic 34 percent sample of terminal systems; retained V3 far atlas and geometry remain separate and actor-root fallback remains authoritative"));
    if (bVolumetricNearGeometry)
    {
        ReportObject->SetNumberField(TEXT("near_scale_leaf_volumes_per_selected_branch_system"), 8);
        ReportObject->SetNumberField(TEXT("near_triangles_per_selected_branch_system"), 256);
        ReportObject->SetNumberField(TEXT("near_branch_system_sampling_probability"), 0.50f);
        ReportObject->SetNumberField(TEXT("provisional_near_source_triangle_floor"), 150000);
        ReportObject->SetNumberField(TEXT("provisional_near_source_triangle_ceiling"), 400000);
        ReportObject->SetBoolField(TEXT("masked_whole_spray_cards_used"), false);
        ReportObject->SetBoolField(TEXT("direct_fir_geometry_copied"), false);
        ReportObject->SetBoolField(TEXT("rounded_fusiform_scale_leaf_volumes"), true);
        ReportObject->SetBoolField(TEXT("woody_nanite_enabled"), true);
        ReportObject->SetBoolField(TEXT("micro_foliage_nanite_enabled"), false);
        ReportObject->SetStringField(TEXT("nanite_shape_preservation"), TEXT("None"));
        ReportObject->SetStringField(
            TEXT("nanite_shape_preservation_reason"),
            TEXT("PreserveArea expanded thin open twig and scale-leaf segments into visible shards during the first V15 diagnostic render"));
        ReportObject->SetStringField(
            TEXT("micro_foliage_raster_reason"),
            TEXT("Nanite culled most tiny disconnected scale-leaf volumes during the dense V15 diagnostic render; woody geometry remains Nanite while micro-foliage uses the traditional near raster path"));
        ReportObject->SetStringField(
            TEXT("resource_contract"),
            TEXT("provisional 150k-400k traditional-raster micro-foliage gate with Nanite woody geometry pending packaged desktop and target-VR profiling"));
        ReportObject->SetStringField(
            TEXT("fixed_near_evidence_authority"),
            TEXT("near-only at turntable, exterior closeup, and 60 m; 150 m remains combined far fallback"));
    }
    else if (bOpaqueNearGeometry)
    {
        ReportObject->SetNumberField(TEXT("near_opaque_clusters_per_selected_branch_system"), 1);
        ReportObject->SetNumberField(TEXT("near_triangles_per_opaque_cluster"), 6);
        ReportObject->SetNumberField(TEXT("near_branch_system_sampling_probability"), 0.11f);
        ReportObject->SetNumberField(TEXT("near_source_triangle_ceiling"), 1900);
        ReportObject->SetBoolField(TEXT("masked_whole_spray_cards_used"), false);
        ReportObject->SetBoolField(TEXT("direct_fir_geometry_copied"), false);
        ReportObject->SetStringField(
            TEXT("retained_resource_contract"),
            TEXT("V12 886-1890 near-source triangle envelope with fewer welded six-triangle opaque clusters replacing two-triangle cards"));
    }
    else
    {
        ReportObject->SetNumberField(TEXT("near_textured_cards_per_selected_terminal_system"), 1);
        ReportObject->SetNumberField(TEXT("near_terminal_system_sampling_probability"), 0.34f);
    }
    ReportObject->SetNumberField(TEXT("far_cards_per_terminal_cluster"), 3);
    ReportObject->SetNumberField(TEXT("near_max_draw_distance_cm"), 2800.0f);
    ReportObject->SetNumberField(TEXT("far_min_draw_distance_cm"), 2800.0f);
    ReportObject->SetNumberField(TEXT("fixed_family_capture_count"), 40);
    ReportObject->SetNumberField(TEXT("handoff_capture_count"), 27);
    ReportObject->SetNumberField(TEXT("handoff_authority_modes_per_distance"), 3);
    ReportObject->SetStringField(TEXT("combined_authority"), TEXT("camera_to_actor_root_distance"));
    ReportObject->SetNumberField(TEXT("actor_root_selection_distance_cm"), 2800.0f);
    ReportObject->SetBoolField(TEXT("near_representation_eligible"), false);
    ReportObject->SetStringField(
        TEXT("ineligible_near_fallback"), TEXT("far silhouette remains authoritative at all distances"));
    ReportObject->SetStringField(
        TEXT("near_candidate_closeup_authority"), TEXT("near_only"));
    ReportObject->SetStringField(
        TEXT("shadow_policy"),
        bVolumetricNearGeometry
            ? TEXT("initial isolated volumetric-foliage shadows disabled until morphology and silhouette pass; bounded shadows remain a separate gate")
            : bOpaqueNearGeometry
            ? TEXT("initial isolated opaque-cluster shadows disabled so topology and silhouette are reviewed before a bounded shadow pass")
            : TEXT("initial isolated spray shadows disabled; production shadow treatment remains gated by V23"));

    TArray<TSharedPtr<FJsonValue>> FormValues;
    for (const FCypressRuntime& Variant : Variants)
    {
        TSharedRef<FJsonObject> FormObject = MakeShared<FJsonObject>();
        FormObject->SetStringField(TEXT("id"), Variant.Form.Id);
        FormObject->SetStringField(TEXT("display_name"), Variant.Form.DisplayName);
        FormObject->SetStringField(TEXT("life_stage"), Variant.Form.LifeStage);
        FormObject->SetNumberField(TEXT("seed_offset"), Variant.Form.SeedOffset);
        FormObject->SetNumberField(TEXT("height_cm"), Variant.Form.HeightCm);
        FormObject->SetNumberField(TEXT("base_radius_cm"), Variant.Form.BaseRadiusCm);
        FormObject->SetNumberField(TEXT("crown_base_cm"), Variant.Form.CrownBaseCm);
        FormObject->SetNumberField(TEXT("crown_radius_cm"), Variant.Form.CrownRadiusCm);
        FormObject->SetNumberField(TEXT("branch_count"), Variant.Form.BranchCount);
        FormObject->SetStringField(TEXT("woody_asset"), Variant.WoodyPackagePath);
        FormObject->SetStringField(
            bVolumetricNearGeometry
                ? TEXT("near_volumetric_scale_leaf_asset")
                : (bOpaqueNearGeometry
                       ? TEXT("near_opaque_scale_leaf_asset")
                       : TEXT("near_textured_spray_asset")),
            Variant.NearSprayPackagePath);
        FormObject->SetStringField(TEXT("far_spray_asset"), Variant.SprayPackagePath);
        FormObject->SetNumberField(TEXT("woody_source_vertices"), Variant.WoodyVertices.Num());
        FormObject->SetNumberField(TEXT("woody_source_triangles"), Variant.WoodyTriangles.Num() / 3);
        FormObject->SetNumberField(
            bVolumetricNearGeometry
                ? TEXT("near_volumetric_scale_leaf_source_vertices")
                : bOpaqueNearGeometry
                ? TEXT("near_opaque_scale_leaf_source_vertices")
                : TEXT("near_textured_spray_source_vertices"),
            Variant.NearSprayVertices.Num());
        FormObject->SetNumberField(
            bVolumetricNearGeometry
                ? TEXT("near_volumetric_scale_leaf_source_triangles")
                : bOpaqueNearGeometry
                ? TEXT("near_opaque_scale_leaf_source_triangles")
                : TEXT("near_textured_spray_source_triangles"),
            Variant.NearSprayTriangles.Num() / 3);
        FormObject->SetNumberField(
            bVolumetricNearGeometry
                ? TEXT("near_volumetric_scale_leaf_source_branch_systems")
                : bOpaqueNearGeometry
                ? TEXT("near_opaque_scale_leaf_source_clusters")
                : TEXT("near_textured_spray_source_cards"),
            bVolumetricNearGeometry
                ? Variant.NearSprayTriangles.Num() / (256 * 3)
                : (bOpaqueNearGeometry
                       ? Variant.NearSprayTriangles.Num() / 18
                       : Variant.NearSprayTriangles.Num() / 6));
        FormObject->SetNumberField(TEXT("far_spray_source_cards"), Variant.SprayTriangles.Num() / 6);
        FormObject->SetNumberField(TEXT("far_spray_source_triangles"), Variant.SprayTriangles.Num() / 3);
        FormObject->SetBoolField(TEXT("woody_nanite_enabled"), Variant.WoodyMesh->IsNaniteEnabled());
        FormObject->SetBoolField(
            bVolumetricNearGeometry
                ? TEXT("near_volumetric_scale_leaf_nanite_enabled")
                : bOpaqueNearGeometry
                ? TEXT("near_opaque_scale_leaf_nanite_enabled")
                : TEXT("near_textured_spray_nanite_enabled"),
            Variant.NearSprayMesh->IsNaniteEnabled());
        FormObject->SetBoolField(TEXT("far_spray_nanite_enabled"), Variant.SprayMesh->IsNaniteEnabled());
        FormValues.Add(MakeShared<FJsonValueObject>(FormObject));
    }
    ReportObject->SetArrayField(TEXT("forms"), FormValues);

    TArray<TSharedPtr<FJsonValue>> CaptureValues;
    for (const FCypressCaptureRequest& Request : CaptureRequests)
    {
        TSharedRef<FJsonObject> CaptureObject = MakeShared<FJsonObject>();
        CaptureObject->SetStringField(TEXT("path"), Request.RelativePath);
        CaptureObject->SetStringField(TEXT("camera"), Request.CameraLabel);
        CaptureObject->SetStringField(TEXT("capture_id"), Request.CaptureId);
        CaptureObject->SetStringField(TEXT("authority_mode"), Request.AuthorityMode);
        CaptureObject->SetBoolField(TEXT("captured"), Request.bCaptured);
        CaptureValues.Add(MakeShared<FJsonValueObject>(CaptureObject));
    }
    ReportObject->SetArrayField(TEXT("captures"), CaptureValues);
    ReportObject->SetStringField(
        TEXT("promotion_boundary"),
        TEXT("human visual acceptance, temporal wind, LOD, mixed-ecology corridor, true-north placement, packaged desktop, and on-device VR evidence remain required"));

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(ReportObject, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportPath = FPaths::Combine(
        GetRepoRoot(),
        bVolumetricNearGeometry
            ? TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                   "futaleufu_cordillera_cypress_v15_volumetric_near_family_report.json")
            : bOpaqueNearGeometry
            ? TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                   "futaleufu_cordillera_cypress_v14_opaque_near_family_report.json")
            : TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                   "futaleufu_cordillera_cypress_v12_isolated_family_report.json"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    const bool bReportSaved = bSerialized &&
        FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s cordilleran-cypress isolated family report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CreateFutaleufuCordilleraCypressDonorReview(FString& OutSummary)
{
    OutSummary.Reset();
    constexpr float DonorEffectiveScale = 100.0f;
    constexpr float DonorCullingBoundsScale = 220.0f;
    if (!GEditor)
    {
        OutSummary += TEXT("No editor is available for the cypress morphology-donor review.\n");
        return false;
    }

    struct FDonorRuntime
    {
        FString Id;
        FString AssetPath;
        FVector WorldOffset = FVector::ZeroVector;
        UStaticMesh* Mesh = nullptr;
        AStaticMeshActor* Actor = nullptr;
        FBox Bounds = FBox(EForceInit::ForceInit);
        FBox WorldBounds = FBox(EForceInit::ForceInit);
    };
    TArray<FDonorRuntime> Donors = {
        {TEXT("polyhaven_fir_a"),
         TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
              "SM_FirTree01_fir_tree_01_a_LOD0.SM_FirTree01_fir_tree_01_a_LOD0"),
         FVector(0.0f, 0.0f, 0.0f)},
        {TEXT("polyhaven_fir_b"),
         TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
              "SM_FirTree01_fir_tree_01_b_LOD0.SM_FirTree01_fir_tree_01_b_LOD0"),
         FVector(500000.0f, 0.0f, 0.0f)},
        {TEXT("polyhaven_fir_c"),
         TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
              "SM_FirTree01_fir_tree_01_c_LOD0.SM_FirTree01_fir_tree_01_c_LOD0"),
         FVector(1000000.0f, 0.0f, 0.0f)}};

    bool bAssetsValid = true;
    for (FDonorRuntime& Donor : Donors)
    {
        Donor.Mesh = LoadObject<UStaticMesh>(nullptr, *Donor.AssetPath);
        bAssetsValid &= Donor.Mesh != nullptr;
        if (!Donor.Mesh)
        {
            OutSummary += FString::Printf(TEXT("Missing morphology-donor mesh: %s\n"), *Donor.AssetPath);
            continue;
        }
        Donor.Bounds = Donor.Mesh->GetBoundingBox();
        bool bOriginalMaterialsValid = Donor.Mesh->GetStaticMaterials().Num() >= 3;
        for (int32 MaterialIndex = 0; MaterialIndex < Donor.Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
        {
            bOriginalMaterialsValid &= Donor.Mesh->GetMaterial(MaterialIndex) != nullptr;
        }
        const bool bDonorValid =
            Donor.Mesh->IsNaniteEnabled() && Donor.Mesh->GetNumVertices(0) > 0 &&
            Donor.Mesh->GetNumTriangles(0) > 0 &&
            Donor.Bounds.GetSize().Z * DonorEffectiveScale >= 1200.0f &&
            Donor.Bounds.GetSize().Z * DonorEffectiveScale <= 2200.0f &&
            bOriginalMaterialsValid;
        bAssetsValid &= bDonorValid;
        OutSummary += FString::Printf(
            TEXT("V13 donor %s: valid=%s nanite=%s vertices=%u triangles=%u "
                 "raw_height=%.3f effective_height_cm=%.3f material_slots=%d "
                 "original_materials=%s.\n"),
            *Donor.Id,
            bDonorValid ? TEXT("true") : TEXT("false"),
            Donor.Mesh->IsNaniteEnabled() ? TEXT("true") : TEXT("false"),
            Donor.Mesh->GetNumVertices(0),
            Donor.Mesh->GetNumTriangles(0),
            Donor.Bounds.GetSize().Z,
            Donor.Bounds.GetSize().Z * DonorEffectiveScale,
            Donor.Mesh->GetStaticMaterials().Num(),
            bOriginalMaterialsValid ? TEXT("true") : TEXT("false"));
    }
    if (!bAssetsValid)
    {
        OutSummary += TEXT("The rights-reviewed donor assets failed their Nanite, scale, geometry, or original-material contract.\n");
        return false;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += TEXT("Could not create the isolated morphology-donor review map.\n");
        return false;
    }

    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    bool bSceneComplete = PlaneMesh != nullptr;
    for (FDonorRuntime& Donor : Donors)
    {
        Donor.Actor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(FRotator::ZeroRotator, Donor.WorldOffset));
        bSceneComplete &= Donor.Actor && Donor.Actor->GetStaticMeshComponent();
        if (Donor.Actor && Donor.Actor->GetStaticMeshComponent())
        {
            Donor.Actor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_FutaleufuCypressDonor_%s_OriginalFirGeometry"),
                *Donor.Id));
            Donor.Actor->GetStaticMeshComponent()->SetStaticMesh(Donor.Mesh);
            Donor.Actor->SetActorScale3D(FVector::OneVector);
            Donor.Actor->GetStaticMeshComponent()->SetBoundsScale(DonorCullingBoundsScale);
            Donor.Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Static);
            Donor.Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Donor.Actor->GetStaticMeshComponent()->UpdateBounds();
            Donor.WorldBounds = Donor.Actor->GetComponentsBoundingBox(true);
            OutSummary += FString::Printf(
                TEXT("V13 donor %s expanded culling bounds: center=(%.3f, %.3f, %.3f) "
                     "size=(%.3f, %.3f, %.3f).\n"),
                *Donor.Id,
                Donor.WorldBounds.GetCenter().X,
                Donor.WorldBounds.GetCenter().Y,
                Donor.WorldBounds.GetCenter().Z,
                Donor.WorldBounds.GetSize().X,
                Donor.WorldBounds.GetSize().Y,
                Donor.WorldBounds.GetSize().Z);
        }

        AStaticMeshActor* GroundActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                Donor.WorldOffset + FVector(0.0f, 0.0f, -10.0f),
                FVector(120.0f, 120.0f, 1.0f)));
        bSceneComplete &= GroundActor && GroundActor->GetStaticMeshComponent();
        if (GroundActor && GroundActor->GetStaticMeshComponent())
        {
            GroundActor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_FutaleufuCypressDonor_%s_NeutralGround"),
                *Donor.Id));
            GroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
            GroundActor->GetStaticMeshComponent()->SetMaterial(0, LoadPreviewBaseMaterial());
            GroundActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    }

    FRaftSimEnvironmentPreviewSpec ReviewSpec;
    ReviewSpec.RiverId = TEXT("futaleufu_terminator");
    ReviewSpec.DisplayName = TEXT("Futaleufu non-native morphology-donor comparison");
    ReviewSpec.MapPackagePath =
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
             "L_FutaleufuCordilleraCypress_V13_FirMorphologyDonorReview");
    ReviewSpec.FoliageColor = FLinearColor(0.13f, 0.28f, 0.10f);
    ReviewSpec.RockColor = FLinearColor(0.31f, 0.30f, 0.27f);
    AddPreviewLightRig(World, ReviewSpec);
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        if (It->GetLightComponent())
        {
            It->GetLightComponent()->SetIntensity(1.55f);
            It->GetLightComponent()->RecaptureSky();
        }
    }
    ADirectionalLight* FillLight = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(), FTransform(FRotator(-30.0f, 38.0f, 0.0f)));
    bSceneComplete &= FillLight && FillLight->GetLightComponent();
    if (FillLight && FillLight->GetLightComponent())
    {
        FillLight->SetActorLabel(TEXT("RaftSim_FutaleufuCypressDonor_NeutralFill"));
        FillLight->GetLightComponent()->SetIntensity(0.62f);
        FillLight->GetLightComponent()->SetLightColor(FLinearColor(0.96f, 0.99f, 1.0f));
        FillLight->GetLightComponent()->SetCastShadows(false);
    }

    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(TEXT("futaleufu_terminator"));
    auto AddReviewCamera = [World, CaptureSettings](
                               const FString& Label,
                               const FVector& Location,
                               const FVector& Target,
                               float FieldOfView)
    {
        ACameraActor* Camera = World->SpawnActor<ACameraActor>(
            ACameraActor::StaticClass(),
            FTransform((Target - Location).Rotation(), Location));
        if (!Camera || !Camera->GetCameraComponent())
        {
            return false;
        }
        Camera->SetActorLabel(Label);
        UCameraComponent* CameraComponent = Camera->GetCameraComponent();
        CameraComponent->FieldOfView = FieldOfView;
        FPostProcessSettings& Settings = CameraComponent->PostProcessSettings;
        Settings.bOverride_AutoExposureMethod = true;
        Settings.AutoExposureMethod = AEM_Manual;
        Settings.bOverride_AutoExposureBias = true;
        Settings.AutoExposureBias = CaptureSettings.ExposureBias;
        Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Settings.AutoExposureApplyPhysicalCameraExposure = 0;
        Settings.bOverride_ColorSaturation = true;
        Settings.ColorSaturation = FVector4(
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            1.0f);
        Settings.bOverride_ColorContrast = true;
        Settings.ColorContrast = FVector4(
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            1.0f);
        Settings.bOverride_Sharpen = true;
        Settings.Sharpen = CaptureSettings.Sharpen;
        Settings.bOverride_FilmGrainIntensity = true;
        Settings.FilmGrainIntensity = 0.0f;
        return true;
    };

    struct FDonorCaptureRequest
    {
        FString RelativePath;
        FString CameraLabel;
        FString CaptureId;
        FString Description;
        bool bCaptured = false;
    };
    TArray<FDonorCaptureRequest> CaptureRequests;
    for (const FDonorRuntime& Donor : Donors)
    {
        const FVector Size = Donor.Bounds.GetSize() * DonorEffectiveScale;
        const FVector LocalCenter = Donor.Bounds.GetCenter() * DonorEffectiveScale;
        const FVector CrownTarget = Donor.WorldOffset + FVector(
            LocalCenter.X,
            LocalCenter.Y,
            Donor.Bounds.Min.Z * DonorEffectiveScale + Size.Z * 0.57f);
        const float TurntableDistance = FMath::Max(Size.Z * 1.75f, FMath::Max(Size.X, Size.Y) * 3.2f);
        const FVector CloseupTarget = Donor.WorldOffset + FVector(
            Donor.Bounds.Min.X * DonorEffectiveScale + Size.X * 0.30f,
            Donor.Bounds.Min.Y * DonorEffectiveScale + Size.Y * 0.30f,
            Donor.Bounds.Min.Z * DonorEffectiveScale + Size.Z * 0.54f);
        struct FViewDefinition
        {
            const TCHAR* Suffix;
            const TCHAR* Description;
            FVector Location;
            FVector Target;
            float FieldOfView;
        };
        const FViewDefinition Views[] = {
            {TEXT("turntable_azimuth_035"), TEXT("turntable azimuth 35"),
             CrownTarget + FVector(
                 -TurntableDistance * FMath::Cos(FMath::DegreesToRadians(35.0f)),
                 -TurntableDistance * FMath::Sin(FMath::DegreesToRadians(35.0f)),
                 Size.Z * 0.08f), CrownTarget, 46.0f},
            {TEXT("turntable_azimuth_145"), TEXT("turntable azimuth 145"),
             CrownTarget + FVector(
                 -TurntableDistance * FMath::Cos(FMath::DegreesToRadians(145.0f)),
                 -TurntableDistance * FMath::Sin(FMath::DegreesToRadians(145.0f)),
                 Size.Z * 0.08f), CrownTarget, 46.0f},
            {TEXT("branch_closeup"), TEXT("exterior branch-hierarchy closeup"),
             CloseupTarget + FVector(-Size.X * 1.45f, -Size.Y * 0.80f, Size.Z * 0.05f),
             CloseupTarget, 38.0f},
            {TEXT("river_distance_60m"), TEXT("60 m river-distance proxy"),
             CrownTarget + FVector(-6000.0f, -700.0f, Size.Z * 0.05f), CrownTarget, 18.0f}};
        for (const FViewDefinition& View : Views)
        {
            FDonorCaptureRequest Request;
            Request.CameraLabel = FString::Printf(
                TEXT("RaftSim_FutaleufuCypressDonor_%s_%s"), *Donor.Id, View.Suffix);
            Request.CaptureId = Donor.Id + TEXT("_") + View.Suffix;
            Request.RelativePath = FString::Printf(
                TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                     "futaleufu_cordillera_cypress_v13_%s_%s.png"),
                *Donor.Id,
                View.Suffix);
            Request.Description = FString::Printf(
                TEXT("non-native CC0 fir morphology donor %s %s"),
                *Donor.Id,
                View.Description);
            bSceneComplete &= AddReviewCamera(
                Request.CameraLabel,
                View.Location,
                View.Target,
                View.FieldOfView);
            CaptureRequests.Add(MoveTemp(Request));
        }
    }
    bSceneComplete &= CaptureRequests.Num() == 12;

    FString MapSummary;
    const bool bMapSaved = bSceneComplete &&
        SavePreviewWorld(World, ReviewSpec.MapPackagePath, MapSummary);
    OutSummary += MapSummary;
    bool bCaptured = bMapSaved;
    if (bMapSaved)
    {
        for (FDonorCaptureRequest& Request : CaptureRequests)
        {
            Request.bCaptured = CapturePreviewImageForSpec(
                ReviewSpec,
                GetRepoRoot(),
                Request.RelativePath,
                Request.CameraLabel,
                Request.CaptureId,
                Request.Description,
                false,
                OutSummary,
                [ExpectedCameraLabel = Request.CameraLabel](
                    UWorld*, ACameraActor* Camera, FString& SetupSummary)
                {
                    const FString ActualLabel = Camera ? Camera->GetActorLabel() : TEXT("");
                    const bool bExactCamera = ActualLabel == ExpectedCameraLabel;
                    if (!bExactCamera)
                    {
                        SetupSummary += FString::Printf(
                            TEXT("V13 expected camera '%s' but capture selected '%s'.\n"),
                            *ExpectedCameraLabel,
                            *ActualLabel);
                    }
                    return bExactCamera;
                });
            bCaptured &= Request.bCaptured;
        }
    }

    TSharedRef<FJsonObject> ReportObject = MakeShared<FJsonObject>();
    ReportObject->SetStringField(
        TEXT("schema"), TEXT("raftsim.unreal.futaleufu_cordillera_cypress_morphology_donor.v13"));
    ReportObject->SetStringField(
        TEXT("status"),
        bCaptured
            ? TEXT("v13_non_native_cc0_morphology_donor_captured_pending_human_review")
            : TEXT("v13_morphology_donor_capture_incomplete"));
    ReportObject->SetBoolField(TEXT("production_promoted"), false);
    ReportObject->SetBoolField(TEXT("corridor_substitution_performed"), false);
    ReportObject->SetBoolField(TEXT("native_species_claim"), false);
    ReportObject->SetStringField(TEXT("source_species"), TEXT("fir tree; exact species not accepted as Austrocedrus chilensis"));
    ReportObject->SetStringField(TEXT("intended_use"), TEXT("connected branch-hierarchy and close-range geometry morphology donor only"));
    ReportObject->SetStringField(TEXT("license"), TEXT("CC0 1.0"));
    ReportObject->SetStringField(
        TEXT("source_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
             "polyhaven_fir_tree_01_source_manifest.json"));
    ReportObject->SetStringField(
        TEXT("import_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/"
             "polyhaven_fir_tree_01_import_report.json"));
    ReportObject->SetStringField(TEXT("map_asset"), ReviewSpec.MapPackagePath);
    ReportObject->SetBoolField(TEXT("map_saved"), bMapSaved);
    ReportObject->SetBoolField(TEXT("original_materials_retained"), true);
    ReportObject->SetNumberField(TEXT("raw_bounds_to_effective_scale"), DonorEffectiveScale);
    ReportObject->SetNumberField(TEXT("review_culling_bounds_scale"), DonorCullingBoundsScale);
    ReportObject->SetStringField(
        TEXT("legacy_import_bounds_note"),
        TEXT("BuildScale3D 100 affects rendered Nanite geometry but persisted mesh/component bounds remain pre-build-scale; the isolated review uses actor scale 1 plus expanded culling bounds and does not mutate source assets"));
    ReportObject->SetNumberField(TEXT("capture_count"), CaptureRequests.Num());

    TArray<TSharedPtr<FJsonValue>> DonorValues;
    for (const FDonorRuntime& Donor : Donors)
    {
        TSharedRef<FJsonObject> DonorObject = MakeShared<FJsonObject>();
        DonorObject->SetStringField(TEXT("id"), Donor.Id);
        DonorObject->SetStringField(TEXT("asset"), Donor.AssetPath);
        DonorObject->SetBoolField(TEXT("nanite_enabled"), Donor.Mesh->IsNaniteEnabled());
        DonorObject->SetNumberField(TEXT("render_vertices"), Donor.Mesh->GetNumVertices(0));
        DonorObject->SetNumberField(TEXT("render_triangles"), Donor.Mesh->GetNumTriangles(0));
        DonorObject->SetNumberField(TEXT("material_slot_count"), Donor.Mesh->GetStaticMaterials().Num());
        TArray<TSharedPtr<FJsonValue>> BoundsSizeValues;
        const FVector RawBoundsSize = Donor.Bounds.GetSize();
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(RawBoundsSize.X));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(RawBoundsSize.Y));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(RawBoundsSize.Z));
        DonorObject->SetArrayField(TEXT("raw_bounds_size"), BoundsSizeValues);
        BoundsSizeValues.Reset();
        const FVector EffectiveBoundsSize = RawBoundsSize * DonorEffectiveScale;
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(EffectiveBoundsSize.X));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(EffectiveBoundsSize.Y));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(EffectiveBoundsSize.Z));
        DonorObject->SetArrayField(TEXT("bounds_size_cm"), BoundsSizeValues);
        BoundsSizeValues.Reset();
        const FVector WorldBoundsSize = Donor.WorldBounds.GetSize();
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(WorldBoundsSize.X));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(WorldBoundsSize.Y));
        BoundsSizeValues.Add(MakeShared<FJsonValueNumber>(WorldBoundsSize.Z));
        DonorObject->SetNumberField(TEXT("review_actor_scale"), 1.0f);
        DonorObject->SetArrayField(TEXT("review_culling_bounds_size_cm"), BoundsSizeValues);
        TArray<TSharedPtr<FJsonValue>> MaterialValues;
        for (int32 MaterialIndex = 0; MaterialIndex < Donor.Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
        {
            TSharedRef<FJsonObject> MaterialObject = MakeShared<FJsonObject>();
            MaterialObject->SetNumberField(TEXT("index"), MaterialIndex);
            MaterialObject->SetStringField(
                TEXT("slot_name"),
                Donor.Mesh->GetStaticMaterials()[MaterialIndex].MaterialSlotName.ToString());
            UMaterialInterface* Material = Donor.Mesh->GetMaterial(MaterialIndex);
            MaterialObject->SetStringField(
                TEXT("material"), Material ? Material->GetPathName() : TEXT(""));
            MaterialValues.Add(MakeShared<FJsonValueObject>(MaterialObject));
        }
        DonorObject->SetArrayField(TEXT("material_slots"), MaterialValues);
        DonorValues.Add(MakeShared<FJsonValueObject>(DonorObject));
    }
    ReportObject->SetArrayField(TEXT("donors"), DonorValues);

    TArray<TSharedPtr<FJsonValue>> CaptureValues;
    for (const FDonorCaptureRequest& Request : CaptureRequests)
    {
        TSharedRef<FJsonObject> CaptureObject = MakeShared<FJsonObject>();
        CaptureObject->SetStringField(TEXT("path"), Request.RelativePath);
        CaptureObject->SetStringField(TEXT("camera"), Request.CameraLabel);
        CaptureObject->SetStringField(TEXT("capture_id"), Request.CaptureId);
        CaptureObject->SetBoolField(TEXT("captured"), Request.bCaptured);
        CaptureValues.Add(MakeShared<FJsonValueObject>(CaptureObject));
    }
    ReportObject->SetArrayField(TEXT("captures"), CaptureValues);
    ReportObject->SetStringField(
        TEXT("decision_boundary"),
        TEXT("compare connected branch hierarchy and close-range geometric breakup against V10 and V12; either reconstruct project-owned Austrocedrus geometry from source morphology constraints or reject donor use and author opaque geometric branchlets plus scale-leaf clusters"));

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(ReportObject, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportPath = FPaths::Combine(
        GetRepoRoot(),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "futaleufu_cordillera_cypress_v13_morphology_donor_report.json"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    const bool bReportSaved = bSerialized &&
        FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s cypress morphology-donor report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bCaptured && bReportSaved;
}

void FRaftSimEditorModule::HandleCreateFutaleufuNativeCanopyPrototypeCommand(const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateFutaleufuNativeCanopyPrototype(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditorEnvironment, Display, TEXT("Futaleufu native-canopy prototype completed.\n%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditorEnvironment, Error, TEXT("Futaleufu native-canopy prototype failed.\n%s"), *Summary);
    }
}

bool FRaftSimEditorModule::CreateFutaleufuNativeCanopyPrototype(FString& OutSummary)
{
    OutSummary.Reset();
    TMap<FString, UTexture2D*> Textures;
    if (!CreateFutaleufuNativeCanopyTextureAssets(Textures, OutSummary))
    {
        OutSummary += TEXT("Native-canopy texture creation failed; geometry was not authored.\n");
        return false;
    }
    UMaterial* BarkMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Bark"), false, Textures, OutSummary);
    UMaterial* LeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"), true, Textures, OutSummary);
    if (!BarkMaterial || !LeafMaterial)
    {
        return false;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += TEXT("Could not create the isolated native-canopy review map.\n");
        return false;
    }

    struct FFutaleufuCoigueRuntime
    {
        FFutaleufuCoigueCrownForm Form;
        FVector WorldOffset = FVector::ZeroVector;
        TArray<FVector> TrunkVertices;
        TArray<int32> TrunkTriangles;
        TArray<FVector> TrunkNormals;
        TArray<FVector2D> TrunkUVs;
        TArray<FVector> BranchletVertices;
        TArray<int32> BranchletTriangles;
        TArray<FVector> BranchletNormals;
        TArray<FVector2D> BranchletUVs;
        TArray<FVector> LeafVertices;
        TArray<int32> LeafTriangles;
        TArray<FVector> LeafNormals;
        TArray<FVector2D> LeafUVs;
        TArray<FVector> FarLeafVertices;
        TArray<int32> FarLeafTriangles;
        TArray<FVector> FarLeafNormals;
        TArray<FVector2D> FarLeafUVs;
        TArray<FVector> RuntimeFarLeafVertices;
        TArray<int32> RuntimeFarLeafTriangles;
        TArray<FVector> RuntimeFarLeafNormals;
        TArray<FVector2D> RuntimeFarLeafUVs;
        FVector CloseupCamera = FVector::ZeroVector;
        FVector CloseupTarget = FVector::ZeroVector;
        FFutaleufuCoigueRoutingMetrics RoutingMetrics;
        FString TrunkPackagePath;
        FString LeafPackagePath;
        FString BranchletPackagePath;
        FString FarLeafPackagePath;
        FString RuntimeFarLeafPackagePath;
        UStaticMesh* TrunkMesh = nullptr;
        UStaticMesh* LeafMesh = nullptr;
        UStaticMesh* BranchletMesh = nullptr;
        UStaticMesh* FarLeafMesh = nullptr;
        UStaticMesh* RuntimeFarLeafMesh = nullptr;
    };

    auto MakeCrownForm = [](
                             const TCHAR* Id,
                             const TCHAR* DisplayName,
                             const TCHAR* AssetToken,
                             const TCHAR* LifeStage,
                             int32 SeedOffset,
                             int32 MainBranchCount,
                             int32 FarAnchorCount,
                             float TrunkHeightScale,
                             float TrunkRadiusScale,
                             float CrownBaseZCm,
                             float CrownSpanZCm,
                             float CrownWidthScale,
                             float BranchUpliftScale,
                             float AsymmetryScale)
    {
        FFutaleufuCoigueCrownForm Form;
        Form.Id = Id;
        Form.DisplayName = DisplayName;
        Form.AssetToken = AssetToken;
        Form.LifeStage = LifeStage;
        Form.SeedOffset = SeedOffset;
        Form.MainBranchCount = MainBranchCount;
        Form.FarCrownVolumeAnchorCount = FarAnchorCount;
        Form.TrunkHeightScale = TrunkHeightScale;
        Form.TrunkRadiusScale = TrunkRadiusScale;
        Form.CrownBaseZCm = CrownBaseZCm;
        Form.CrownSpanZCm = CrownSpanZCm;
        Form.CrownWidthScale = CrownWidthScale;
        Form.BranchUpliftScale = BranchUpliftScale;
        Form.AsymmetryScale = AsymmetryScale;
        return Form;
    };

    TArray<FFutaleufuCoigueRuntime> Variants;
    Variants.SetNum(8);
    Variants[0].Form = MakeCrownForm(
        TEXT("open_grown_adult"), TEXT("open-grown adult"), TEXT("AdultPrototype"),
        TEXT("adult"), 0, 26, 370, 1.0f, 1.0f, 950.0f, 1560.0f, 1.0f, 1.0f, 1.0f);
    Variants[1].Form = MakeCrownForm(
        TEXT("forest_grown_adult"), TEXT("forest-grown adult"), TEXT("ForestGrownAdultPrototype"),
        TEXT("adult"), 3907, 22, 280, 1.12f, 0.78f, 1440.0f, 1510.0f, 0.64f, 1.28f, 1.08f);
    Variants[2].Form = MakeCrownForm(
        TEXT("storm_damaged_adult"), TEXT("storm-damaged adult"), TEXT("StormDamagedAdultPrototype"),
        TEXT("adult"), 5903, 25, 330, 0.98f, 0.94f, 1050.0f, 1550.0f, 0.90f, 1.05f, 1.30f);
    Variants[2].Form.TrunkLeanTopCm = FVector2D(-60.0f, 35.0f);
    Variants[2].Form.CrownGapCenterT = 0.62f;
    Variants[2].Form.CrownGapHalfWidthT = 0.09f;
    Variants[2].Form.CrownGapLengthScale = 0.50f;
    Variants[2].Form.DamageModulo = 4;
    Variants[2].Form.DamageRemainder = 1;
    Variants[2].Form.DamagedBranchLengthScale = 0.38f;
    Variants[3].Form = MakeCrownForm(
        TEXT("competition_lean_adult"), TEXT("competition-lean adult"), TEXT("CompetitionLeanAdultPrototype"),
        TEXT("adult"), 7901, 24, 310, 1.10f, 0.82f, 1280.0f, 1530.0f, 0.72f, 1.20f, 1.40f);
    Variants[3].Form.TrunkLeanTopCm = FVector2D(260.0f, -150.0f);
    Variants[3].Form.SuppressedSectorCenterDegrees = 210.0f;
    Variants[3].Form.SuppressedSectorHalfWidthDegrees = 70.0f;
    Variants[3].Form.SuppressedSectorLengthScale = 0.28f;
    Variants[4].Form = MakeCrownForm(
        TEXT("crown_gap_adult"), TEXT("crown-gap adult"), TEXT("CrownGapAdultPrototype"),
        TEXT("adult"), 9901, 25, 340, 1.02f, 0.90f, 1100.0f, 1500.0f, 0.88f, 1.08f, 1.55f);
    Variants[4].Form.TrunkLeanTopCm = FVector2D(45.0f, 70.0f);
    Variants[4].Form.SuppressedSectorCenterDegrees = 40.0f;
    Variants[4].Form.SuppressedSectorHalfWidthDegrees = 45.0f;
    Variants[4].Form.SuppressedSectorLengthScale = 0.15f;
    Variants[4].Form.CrownGapCenterT = 0.45f;
    Variants[4].Form.CrownGapHalfWidthT = 0.07f;
    Variants[4].Form.CrownGapLengthScale = 0.32f;
    Variants[5].Form = MakeCrownForm(
        TEXT("intermediate"), TEXT("intermediate form"), TEXT("IntermediatePrototype"),
        TEXT("intermediate"), 1907, 24, 320, 1.02f, 0.86f, 1140.0f, 1500.0f, 0.82f, 1.12f, 1.24f);
    Variants[6].Form = MakeCrownForm(
        TEXT("intermediate_suppressed"), TEXT("suppressed intermediate"), TEXT("SuppressedIntermediatePrototype"),
        TEXT("intermediate"), 11903, 20, 250, 0.78f, 0.58f, 960.0f, 1120.0f, 0.48f, 1.35f, 0.95f);
    Variants[6].Form.TrunkLeanTopCm = FVector2D(90.0f, 40.0f);
    Variants[6].Form.SuppressedSectorCenterDegrees = 170.0f;
    Variants[6].Form.SuppressedSectorHalfWidthDegrees = 90.0f;
    Variants[6].Form.SuppressedSectorLengthScale = 0.40f;
    Variants[7].Form = MakeCrownForm(
        TEXT("intermediate_released"), TEXT("released intermediate"), TEXT("ReleasedIntermediatePrototype"),
        TEXT("intermediate"), 13901, 23, 300, 0.90f, 0.68f, 940.0f, 1340.0f, 0.76f, 1.18f, 1.70f);
    Variants[7].Form.TrunkLeanTopCm = FVector2D(-120.0f, 100.0f);
    Variants[7].Form.SuppressedSectorCenterDegrees = 280.0f;
    Variants[7].Form.SuppressedSectorHalfWidthDegrees = 55.0f;
    Variants[7].Form.SuppressedSectorLengthScale = 0.45f;
    for (int32 VariantIndex = 0; VariantIndex < Variants.Num(); ++VariantIndex)
    {
        Variants[VariantIndex].WorldOffset = FVector(VariantIndex * 500000.0f, 0.0f, 0.0f);
    }

    static const FString MeshRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Meshes/");
    bool bVariantActorsComplete = true;
    for (FFutaleufuCoigueRuntime& Variant : Variants)
    {
        BuildFutaleufuCoiguePrototypeGeometry(
            Variant.Form,
            Variant.TrunkVertices,
            Variant.TrunkTriangles,
            Variant.TrunkNormals,
            Variant.TrunkUVs,
            Variant.BranchletVertices,
            Variant.BranchletTriangles,
            Variant.BranchletNormals,
            Variant.BranchletUVs,
            Variant.LeafVertices,
            Variant.LeafTriangles,
            Variant.LeafNormals,
            Variant.LeafUVs,
            Variant.FarLeafVertices,
            Variant.FarLeafTriangles,
            Variant.FarLeafNormals,
            Variant.FarLeafUVs,
            Variant.CloseupCamera,
            Variant.CloseupTarget,
            Variant.RoutingMetrics);
        BuildReducedNativeCanopyCardGeometry(
            Variant.FarLeafVertices,
            Variant.FarLeafTriangles,
            Variant.FarLeafNormals,
            Variant.FarLeafUVs,
            6,
            1.28f,
            Variant.RuntimeFarLeafVertices,
            Variant.RuntimeFarLeafTriangles,
            Variant.RuntimeFarLeafNormals,
            Variant.RuntimeFarLeafUVs);

        const FString ProceduralStem = FString::Printf(
            TEXT("RaftSim_FutaleufuCoigue_%s_Procedural"), *Variant.Form.AssetToken);
        AActor* TrunkProceduralActor = AddPreviewProceduralMeshActor(
            World, *(ProceduralStem + TEXT("Trunk")),
            Variant.TrunkVertices, Variant.TrunkTriangles, Variant.TrunkNormals, Variant.TrunkUVs,
            FLinearColor::White, BarkMaterial, nullptr, false);
        AActor* LeafProceduralActor = AddPreviewProceduralMeshActor(
            World, *(ProceduralStem + TEXT("Leaves")),
            Variant.LeafVertices, Variant.LeafTriangles, Variant.LeafNormals, Variant.LeafUVs,
            FLinearColor::White, LeafMaterial, nullptr, false);
        AActor* BranchletProceduralActor = AddPreviewProceduralMeshActor(
            World, *(ProceduralStem + TEXT("Branchlets")),
            Variant.BranchletVertices, Variant.BranchletTriangles,
            Variant.BranchletNormals, Variant.BranchletUVs,
            FLinearColor::White, BarkMaterial, nullptr, false);
        AActor* FarLeafProceduralActor = AddPreviewProceduralMeshActor(
            World, *(ProceduralStem + TEXT("LeavesFar")),
            Variant.FarLeafVertices, Variant.FarLeafTriangles,
            Variant.FarLeafNormals, Variant.FarLeafUVs,
            FLinearColor::White, LeafMaterial, nullptr, false);
        AActor* RuntimeFarLeafProceduralActor = AddPreviewProceduralMeshActor(
            World, *(ProceduralStem + TEXT("LeavesFarRuntime")),
            Variant.RuntimeFarLeafVertices, Variant.RuntimeFarLeafTriangles,
            Variant.RuntimeFarLeafNormals, Variant.RuntimeFarLeafUVs,
            FLinearColor::White, LeafMaterial, nullptr, false);
        if (!TrunkProceduralActor || !BranchletProceduralActor ||
            !LeafProceduralActor || !FarLeafProceduralActor || !RuntimeFarLeafProceduralActor)
        {
            OutSummary += FString::Printf(
                TEXT("Could not construct all %s procedural mesh actors.\n"),
                *Variant.Form.DisplayName);
            return false;
        }

        const FString AssetStem = FString::Printf(
            TEXT("SM_RaftSim_FutaleufuCoigue_%s"), *Variant.Form.AssetToken);
        Variant.TrunkPackagePath = MeshRoot + AssetStem + TEXT("_Trunk");
        Variant.LeafPackagePath = MeshRoot + AssetStem + TEXT("_Leaves");
        Variant.BranchletPackagePath = MeshRoot + AssetStem + TEXT("_Branchlets");
        Variant.FarLeafPackagePath = MeshRoot + AssetStem + TEXT("_LeavesFar");
        Variant.RuntimeFarLeafPackagePath = MeshRoot + AssetStem + TEXT("_LeavesFarRuntime");
        Variant.TrunkMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            TrunkProceduralActor, Variant.TrunkPackagePath, BarkMaterial, false,
            ENaniteShapePreservation::None, OutSummary);
        Variant.LeafMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            LeafProceduralActor, Variant.LeafPackagePath, LeafMaterial, false,
            ENaniteShapePreservation::None, OutSummary);
        Variant.BranchletMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            BranchletProceduralActor, Variant.BranchletPackagePath, BarkMaterial, false,
            ENaniteShapePreservation::None, OutSummary);
        Variant.FarLeafMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            FarLeafProceduralActor, Variant.FarLeafPackagePath, LeafMaterial, false,
            ENaniteShapePreservation::None, OutSummary);
        Variant.RuntimeFarLeafMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            RuntimeFarLeafProceduralActor, Variant.RuntimeFarLeafPackagePath, LeafMaterial, false,
            ENaniteShapePreservation::None, OutSummary);
        TrunkProceduralActor->Destroy();
        BranchletProceduralActor->Destroy();
        LeafProceduralActor->Destroy();
        FarLeafProceduralActor->Destroy();
        RuntimeFarLeafProceduralActor->Destroy();
        if (!Variant.TrunkMesh || !Variant.BranchletMesh ||
            !Variant.LeafMesh || !Variant.FarLeafMesh || !Variant.RuntimeFarLeafMesh)
        {
            return false;
        }

        const FTransform VariantTransform(FRotator::ZeroRotator, Variant.WorldOffset);
        AStaticMeshActor* TrunkActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        AStaticMeshActor* LeafActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        AStaticMeshActor* BranchletActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        AStaticMeshActor* FarLeafActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), VariantTransform);
        if (!TrunkActor || !BranchletActor || !LeafActor || !FarLeafActor)
        {
            OutSummary += FString::Printf(
                TEXT("Could not place all %s static mesh review actors.\n"),
                *Variant.Form.DisplayName);
            return false;
        }

        auto ConfigureActor = [](
                                  AStaticMeshActor* Actor,
                                  const FString& Label,
                                  UStaticMesh* Mesh,
                                  UMaterialInterface* Material)
        {
            Actor->SetActorLabel(Label);
            Actor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
            Actor->GetStaticMeshComponent()->SetMaterial(0, Material);
            Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Static);
            Actor->GetStaticMeshComponent()->SetCastShadow(true);
        };
        const FString ActorStem = FString::Printf(
            TEXT("RaftSim_FutaleufuCoigue_%s"), *Variant.Form.AssetToken);
        ConfigureActor(TrunkActor, ActorStem + TEXT("_Trunk"), Variant.TrunkMesh, BarkMaterial);
        ConfigureActor(BranchletActor, ActorStem + TEXT("_Branchlets"), Variant.BranchletMesh, BarkMaterial);
        ConfigureActor(LeafActor, ActorStem + TEXT("_Leaves"), Variant.LeafMesh, LeafMaterial);
        ConfigureActor(FarLeafActor, ActorStem + TEXT("_LeavesFar"), Variant.FarLeafMesh, LeafMaterial);
        BranchletActor->GetStaticMeshComponent()->SetCullDistance(3600.0f);
        LeafActor->GetStaticMeshComponent()->SetCullDistance(3600.0f);
        FarLeafActor->GetStaticMeshComponent()->MinDrawDistance = 2800.0f;
        FarLeafActor->GetStaticMeshComponent()->MarkRenderStateDirty();
        bVariantActorsComplete &= TrunkActor && BranchletActor && LeafActor && FarLeafActor;
    }

    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    bool bGroundActorsComplete = PlaneMesh != nullptr;
    for (const FFutaleufuCoigueRuntime& Variant : Variants)
    {
        AStaticMeshActor* GroundActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                Variant.WorldOffset + FVector(0.0f, 0.0f, -4.0f),
                FVector(180.0f, 180.0f, 1.0f)));
        bGroundActorsComplete &= GroundActor && GroundActor->GetStaticMeshComponent();
        if (GroundActor && GroundActor->GetStaticMeshComponent())
        {
            GroundActor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_FutaleufuCoigue_%s_NeutralGround"),
                *Variant.Form.AssetToken));
            GroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
            GroundActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            GroundActor->GetStaticMeshComponent()->SetMaterial(0, LoadPreviewBaseMaterial());
        }
    }

    FRaftSimEnvironmentPreviewSpec ReviewSpec;
    ReviewSpec.RiverId = TEXT("futaleufu_terminator");
    ReviewSpec.DisplayName = TEXT("Futaleufu project-owned coigue crown-form family");
    ReviewSpec.MapPackagePath =
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
             "L_FutaleufuCoigue_CrownFormFamily_IsolatedReview");
    ReviewSpec.FoliageColor = FLinearColor(0.12f, 0.28f, 0.10f);
    ReviewSpec.RockColor = FLinearColor(0.31f, 0.30f, 0.27f);
    AddPreviewLightRig(World, ReviewSpec);
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        if (It->GetLightComponent())
        {
            It->GetLightComponent()->SetIntensity(1.65f);
            It->GetLightComponent()->RecaptureSky();
        }
    }
    ADirectionalLight* ReviewFill = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FTransform(FRotator(-32.0f, 42.0f, 0.0f)));
    if (ReviewFill && ReviewFill->GetLightComponent())
    {
        ReviewFill->SetActorLabel(TEXT("RaftSim_Coigue_NeutralFrontFill"));
        ReviewFill->GetLightComponent()->SetIntensity(0.75f);
        ReviewFill->GetLightComponent()->SetLightColor(FLinearColor(0.94f, 0.98f, 1.0f));
        ReviewFill->GetLightComponent()->SetCastShadows(false);
    }
    ADirectionalLight* ReviewBackFill = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FTransform(FRotator(-28.0f, -138.0f, 0.0f)));
    if (ReviewBackFill && ReviewBackFill->GetLightComponent())
    {
        ReviewBackFill->SetActorLabel(TEXT("RaftSim_Coigue_NeutralBackFill"));
        ReviewBackFill->GetLightComponent()->SetIntensity(0.38f);
        ReviewBackFill->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.96f, 0.90f));
        ReviewBackFill->GetLightComponent()->SetCastShadows(false);
    }
    const bool bReviewLightRigComplete =
        ReviewFill && ReviewFill->GetLightComponent() &&
        ReviewBackFill && ReviewBackFill->GetLightComponent();

    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(ReviewSpec.RiverId);
    auto AddReviewCamera = [World, CaptureSettings](
                               const TCHAR* Label,
                               const FVector& Location,
                               const FVector& Target,
                               float FieldOfView)
    {
        ACameraActor* Camera = World->SpawnActor<ACameraActor>(
            ACameraActor::StaticClass(), FTransform((Target - Location).Rotation(), Location));
        if (!Camera || !Camera->GetCameraComponent())
        {
            return false;
        }
        Camera->SetActorLabel(Label);
        UCameraComponent* CameraComponent = Camera->GetCameraComponent();
        CameraComponent->FieldOfView = FieldOfView;
        FPostProcessSettings& Settings = CameraComponent->PostProcessSettings;
        Settings.bOverride_AutoExposureMethod = true;
        Settings.AutoExposureMethod = AEM_Manual;
        Settings.bOverride_AutoExposureBias = true;
        Settings.AutoExposureBias = CaptureSettings.ExposureBias;
        Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Settings.AutoExposureApplyPhysicalCameraExposure = 0;
        Settings.bOverride_ColorSaturation = true;
        Settings.ColorSaturation = FVector4(
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            1.0f);
        Settings.bOverride_ColorContrast = true;
        Settings.ColorContrast = FVector4(
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            1.0f);
        Settings.bOverride_Sharpen = true;
        Settings.Sharpen = CaptureSettings.Sharpen;
        Settings.bOverride_FilmGrainIntensity = true;
        Settings.FilmGrainIntensity = 0.0f;
        return true;
    };

    struct FNativeCanopyCaptureRequest
    {
        FString RelativePath;
        FString CameraLabel;
        FString CaptureId;
        FString Description;
        double CaptureWallTimeMs = 0.0;
        double GameThreadFrameTimeMs = 0.0;
        double RenderThreadFrameTimeMs = 0.0;
        double GpuFrameTimeMs = 0.0;
        bool bCaptured = false;
    };
    TArray<FNativeCanopyCaptureRequest> CaptureRequests;
    bool bCamerasComplete = true;
    for (const FFutaleufuCoigueRuntime& Variant : Variants)
    {
        const FVector CrownTarget = Variant.WorldOffset + FVector(
            0.0f,
            0.0f,
            Variant.Form.CrownBaseZCm + Variant.Form.CrownSpanZCm * 0.32f);
        const FString LabelStem = FString::Printf(
            TEXT("RaftSim_Coigue_%s"), *Variant.Form.AssetToken);
        const FString CaptureStem = Variant.Form.Id;
        struct FViewDefinition
        {
            const TCHAR* Suffix;
            const TCHAR* CaptureSuffix;
            const TCHAR* Description;
            FVector Location;
            FVector Target;
            float FieldOfView;
        };
        const FViewDefinition Views[] = {
            {TEXT("_Turntable_Azimuth035"), TEXT("turntable_azimuth_035"),
             TEXT("turntable azimuth 35"),
             Variant.WorldOffset + FVector(-6900.0f, -4830.0f, 1650.0f), CrownTarget, 52.0f},
            {TEXT("_Turntable_Azimuth145"), TEXT("turntable_azimuth_145"),
             TEXT("turntable azimuth 145"),
             Variant.WorldOffset + FVector(6900.0f, -4830.0f, 1650.0f), CrownTarget, 52.0f},
            {TEXT("_BarkLeafCloseup"), TEXT("bark_leaf_closeup"),
             TEXT("bark and leaf closeup"),
             Variant.WorldOffset + Variant.CloseupCamera,
             Variant.WorldOffset + Variant.CloseupTarget, 40.0f},
            {TEXT("_RiverDistance60m"), TEXT("river_distance_60m"),
             TEXT("60 m river-distance proxy"),
             Variant.WorldOffset + FVector(-6000.0f, -800.0f, 1550.0f), CrownTarget, 48.0f},
            {TEXT("_RiverDistance150m"), TEXT("river_distance_150m"),
             TEXT("150 m river-distance proxy"),
             Variant.WorldOffset + FVector(-15000.0f, -1600.0f, 1700.0f), CrownTarget, 28.0f}};
        for (const FViewDefinition& View : Views)
        {
            FNativeCanopyCaptureRequest Request;
            Request.CameraLabel = LabelStem + View.Suffix;
            Request.CaptureId = CaptureStem + TEXT("_") + View.CaptureSuffix;
            Request.RelativePath = FString::Printf(
                TEXT("unreal/Saved/RaftSimNativeCanopyReview/FutaleufuCoigue/%s/%s.png"),
                *CaptureStem,
                View.CaptureSuffix);
            Request.Description = FString::Printf(
                TEXT("coigue %s %s"), *Variant.Form.DisplayName, View.Description);
            bCamerasComplete &= AddReviewCamera(
                *Request.CameraLabel, View.Location, View.Target, View.FieldOfView);
            CaptureRequests.Add(MoveTemp(Request));
        }
    }

    bool bGeometryValidated = true;
    for (const FFutaleufuCoigueRuntime& Variant : Variants)
    {
        bGeometryValidated &=
            !Variant.TrunkMesh->IsNaniteEnabled() &&
            !Variant.BranchletMesh->IsNaniteEnabled() &&
            !Variant.LeafMesh->IsNaniteEnabled() &&
            !Variant.FarLeafMesh->IsNaniteEnabled() &&
            !Variant.RuntimeFarLeafMesh->IsNaniteEnabled() &&
            Variant.TrunkMesh->GetNaniteSettings().ShapePreservation == ENaniteShapePreservation::None &&
            Variant.LeafMesh->GetNaniteSettings().ShapePreservation == ENaniteShapePreservation::None &&
            Variant.TrunkMesh->GetNumVertices(0) > 500 &&
            Variant.BranchletMesh->GetNumVertices(0) > 5000 &&
            Variant.LeafMesh->GetNumVertices(0) > 500 &&
            Variant.FarLeafMesh->GetNumVertices(0) > 5000 &&
            Variant.RuntimeFarLeafMesh->GetNumVertices(0) > 1000 &&
            Variant.RuntimeFarLeafMesh->GetNumTriangles(0) * 5 <
                Variant.FarLeafMesh->GetNumTriangles(0) &&
            Variant.TrunkMesh->GetBoundingBox().GetSize().Z >= 2000.0f &&
            Variant.LeafMesh->GetBoundingBox().GetSize().X >= 650.0f &&
            Variant.FarLeafMesh->GetBoundingBox().GetSize().X >= 650.0f &&
            Variant.RuntimeFarLeafMesh->GetBoundingBox().GetSize().X >= 650.0f;
    }
    const bool bSceneComplete =
        bGeometryValidated && bVariantActorsComplete && bGroundActorsComplete &&
        bReviewLightRigComplete && bCamerasComplete && CaptureRequests.Num() == Variants.Num() * 5;
    FString MapSummary;
    const bool bMapSaved = bSceneComplete &&
        SavePreviewWorld(World, ReviewSpec.MapPackagePath, MapSummary);
    OutSummary += MapSummary;

    bool bCaptured = bMapSaved;
    if (bMapSaved)
    {
        const FString CaptureRoot = FPaths::Combine(
            FPaths::ProjectSavedDir(), TEXT("RaftSimNativeCanopyReview/FutaleufuCoigue"));
        for (FNativeCanopyCaptureRequest& Request : CaptureRequests)
        {
            const double CaptureStartSeconds = FPlatformTime::Seconds();
            Request.bCaptured = CapturePreviewImageForSpec(
                ReviewSpec,
                CaptureRoot,
                Request.RelativePath,
                Request.CameraLabel,
                Request.CaptureId,
                Request.Description,
                false,
                OutSummary);
            Request.CaptureWallTimeMs =
                (FPlatformTime::Seconds() - CaptureStartSeconds) * 1000.0;
            FlushRenderingCommands();
            const double CycleToMilliseconds = FPlatformTime::GetSecondsPerCycle() * 1000.0;
            Request.GameThreadFrameTimeMs = GGameThreadTime * CycleToMilliseconds;
            Request.RenderThreadFrameTimeMs = GRenderThreadTime * CycleToMilliseconds;
            Request.GpuFrameTimeMs = RHIGetGPUFrameCycles() * CycleToMilliseconds;
            bCaptured &= Request.bCaptured;
        }
    }

    FRaftSimEnvironmentPreviewSpec RuntimeBenchmarkSpec = ReviewSpec;
    RuntimeBenchmarkSpec.DisplayName =
        TEXT("Futaleufu coigue 512-tree far-corridor HISM benchmark");
    RuntimeBenchmarkSpec.MapPackagePath =
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FutaleufuNativeCanopy/"
             "L_FutaleufuCoigue_RuntimeFarLod_HismBenchmark");
    UWorld* RuntimeBenchmarkWorld = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    bool bRuntimeBenchmarkComplete = RuntimeBenchmarkWorld != nullptr && PlaneMesh != nullptr;
    TArray<UHierarchicalInstancedStaticMeshComponent*> RuntimeTrunkComponents;
    TArray<UHierarchicalInstancedStaticMeshComponent*> RuntimeCrownComponents;
    RuntimeTrunkComponents.SetNum(Variants.Num());
    RuntimeCrownComponents.SetNum(Variants.Num());
    if (RuntimeBenchmarkWorld)
    {
        AddPreviewLightRig(RuntimeBenchmarkWorld, RuntimeBenchmarkSpec);
        AStaticMeshActor* RuntimeGroundActor = RuntimeBenchmarkWorld->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                FVector(22000.0f, 0.0f, -6.0f),
                FVector(720.0f, 320.0f, 1.0f)));
        bRuntimeBenchmarkComplete &=
            RuntimeGroundActor && RuntimeGroundActor->GetStaticMeshComponent();
        if (RuntimeGroundActor && RuntimeGroundActor->GetStaticMeshComponent())
        {
            RuntimeGroundActor->SetActorLabel(TEXT("RaftSim_CoigueRuntimeBenchmark_Ground"));
            RuntimeGroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
            RuntimeGroundActor->GetStaticMeshComponent()->SetMaterial(0, LoadPreviewBaseMaterial());
            RuntimeGroundActor->GetStaticMeshComponent()->SetCollisionEnabled(
                ECollisionEnabled::NoCollision);
        }

        for (int32 VariantIndex = 0; VariantIndex < Variants.Num(); ++VariantIndex)
        {
            const FFutaleufuCoigueRuntime& Variant = Variants[VariantIndex];
            RuntimeTrunkComponents[VariantIndex] = AddLandscapeCandidateInstancedMeshComponent(
                RuntimeBenchmarkWorld,
                Variant.TrunkMesh,
                FString::Printf(
                    TEXT("RaftSim_CoigueRuntimeBenchmark_%s_Trunks"),
                    *Variant.Form.AssetToken),
                true,
                BarkMaterial);
            RuntimeCrownComponents[VariantIndex] = AddLandscapeCandidateInstancedMeshComponent(
                RuntimeBenchmarkWorld,
                Variant.RuntimeFarLeafMesh,
                FString::Printf(
                    TEXT("RaftSim_CoigueRuntimeBenchmark_%s_Crowns"),
                    *Variant.Form.AssetToken),
                true,
                LeafMaterial);
            bRuntimeBenchmarkComplete &=
                RuntimeTrunkComponents[VariantIndex] && RuntimeCrownComponents[VariantIndex];
        }

        constexpr int32 RuntimeTreeCount = 512;
        constexpr int32 RuntimeColumnCount = 32;
        for (int32 TreeIndex = 0; TreeIndex < RuntimeTreeCount; ++TreeIndex)
        {
            const int32 VariantIndex = TreeIndex % Variants.Num();
            const int32 Column = TreeIndex % RuntimeColumnCount;
            const int32 Row = TreeIndex / RuntimeColumnCount;
            const float NoiseA = FMath::Frac(FMath::Sin(TreeIndex * 12.9898f) * 43758.5453f);
            const float NoiseB = FMath::Frac(FMath::Sin((TreeIndex + 71) * 78.233f) * 24634.6345f);
            const float X = Column * 1800.0f + (NoiseA - 0.5f) * 520.0f;
            const float Y = (Row - 7.5f) * 1700.0f + (NoiseB - 0.5f) * 460.0f;
            const float UniformScale = 0.82f + 0.34f * FMath::Abs(NoiseA);
            const FRotator Rotation(0.0f, FMath::Fmod(TreeIndex * 137.50776f, 360.0f), 0.0f);
            const FFutaleufuCoigueRuntime& Variant = Variants[VariantIndex];
            const FBox TrunkBounds = Variant.TrunkMesh->GetBoundingBox();
            const float SharedGroundPivotZ = -TrunkBounds.Min.Z * UniformScale;
            RuntimeTrunkComponents[VariantIndex]->AddInstance(
                FTransform(
                    Rotation,
                    FVector(X, Y, SharedGroundPivotZ),
                    FVector(UniformScale)),
                true);
            RuntimeCrownComponents[VariantIndex]->AddInstance(
                FTransform(
                    Rotation,
                    FVector(X, Y, SharedGroundPivotZ),
                    FVector(UniformScale)),
                true);
        }

        const FVector RuntimeCameraLocation(-9500.0f, 0.0f, 1650.0f);
        const FVector RuntimeCameraTarget(34000.0f, 0.0f, 1550.0f);
        ACameraActor* RuntimeCamera = RuntimeBenchmarkWorld->SpawnActor<ACameraActor>(
            ACameraActor::StaticClass(),
            FTransform(
                (RuntimeCameraTarget - RuntimeCameraLocation).Rotation(),
                RuntimeCameraLocation));
        bRuntimeBenchmarkComplete &= RuntimeCamera && RuntimeCamera->GetCameraComponent();
        if (RuntimeCamera && RuntimeCamera->GetCameraComponent())
        {
            RuntimeCamera->SetActorLabel(TEXT("RaftSim_CoigueRuntimeBenchmark_Camera"));
            RuntimeCamera->GetCameraComponent()->FieldOfView = 62.0f;
            FPostProcessSettings& Settings =
                RuntimeCamera->GetCameraComponent()->PostProcessSettings;
            Settings.bOverride_AutoExposureMethod = true;
            Settings.AutoExposureMethod = AEM_Manual;
            Settings.bOverride_AutoExposureBias = true;
            Settings.AutoExposureBias = 0.0f;
            Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
            Settings.AutoExposureApplyPhysicalCameraExposure = 0;
            Settings.bOverride_FilmGrainIntensity = true;
            Settings.FilmGrainIntensity = 0.0f;
        }
    }

    FString RuntimeBenchmarkMapSummary;
    const bool bRuntimeBenchmarkMapSaved = bRuntimeBenchmarkComplete &&
        SavePreviewWorld(
            RuntimeBenchmarkWorld,
            RuntimeBenchmarkSpec.MapPackagePath,
            RuntimeBenchmarkMapSummary);
    OutSummary += RuntimeBenchmarkMapSummary;
    FString RuntimeBenchmarkCapturePath =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "futaleufu_coigue_runtime_far_lod_hism_512_tree.png");
    const bool bRuntimeBenchmarkCaptured = bRuntimeBenchmarkMapSaved &&
        CapturePreviewImageForSpec(
            RuntimeBenchmarkSpec,
            FPaths::Combine(
                GetRepoRoot(),
                TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates")),
            RuntimeBenchmarkCapturePath,
            TEXT("RaftSim_CoigueRuntimeBenchmark_Camera"),
            TEXT("coigue_runtime_far_lod_hism_512_tree"),
            TEXT("Futaleufu coigue 512-tree far-corridor HISM benchmark"),
            false,
            OutSummary);
    bCaptured &= bRuntimeBenchmarkCaptured;

    const FString ReportRelativePath =
        TEXT("docs/environment-captures/photoreal_river_previews/"
             "futaleufu_native_canopy_coigue_prototype_report.json");
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    auto VectorArray = [](const FVector& Value)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        Values.Add(MakeShared<FJsonValueNumber>(Value.X));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Y));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Z));
        return Values;
    };
    auto NumberArray = [](std::initializer_list<double> Numbers)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        for (double Number : Numbers)
        {
            Values.Add(MakeShared<FJsonValueNumber>(Number));
        }
        return Values;
    };

    TSharedRef<FJsonObject> ReportObject = MakeShared<FJsonObject>();
    ReportObject->SetStringField(
        TEXT("schema"), TEXT("raftsim.unreal.futaleufu_native_canopy_prototype_review.v7"));
    ReportObject->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    ReportObject->SetStringField(TEXT("species"), TEXT("Nothofagus dombeyi"));
    ReportObject->SetStringField(
        TEXT("prototype_revision"), TEXT("v12_far_corridor_lod_and_hism_density_benchmark"));
    ReportObject->SetStringField(
        TEXT("status"),
        bCaptured
            ? TEXT("isolated_eight_form_forty_view_and_512_tree_runtime_lod_capture_ready_for_human_review")
            : TEXT("prototype_generation_or_capture_failed"));
    ReportObject->SetBoolField(TEXT("production_promoted"), false);
    ReportObject->SetStringField(TEXT("map_asset"), ReviewSpec.MapPackagePath);
    ReportObject->SetNumberField(TEXT("texture_count"), Textures.Num());
    ReportObject->SetNumberField(TEXT("material_count"), 2);
    TSharedRef<FJsonObject> PhotometryObject = MakeShared<FJsonObject>();
    PhotometryObject->SetStringField(
        TEXT("method"),
        TEXT("fixed exposure with bounded bidirectional neutral studio fills and material response; no emissive fill"));
    PhotometryObject->SetNumberField(TEXT("skylight_intensity"), 1.65);
    PhotometryObject->SetNumberField(TEXT("front_fill_intensity"), 0.75);
    PhotometryObject->SetNumberField(TEXT("back_fill_intensity"), 0.38);
    PhotometryObject->SetBoolField(TEXT("fill_lights_cast_shadows"), false);
    PhotometryObject->SetBoolField(TEXT("emissive_fill"), false);
    PhotometryObject->SetNumberField(TEXT("bark_base_color_scale"), 1.72);
    PhotometryObject->SetNumberField(TEXT("bark_ao_influence"), 0.28);
    PhotometryObject->SetNumberField(TEXT("leaf_base_color_scale"), 1.18);
    PhotometryObject->SetNumberField(TEXT("leaf_ao_influence"), 0.55);
    PhotometryObject->SetArrayField(TEXT("leaf_transmission_tint"), NumberArray({0.55, 0.78, 0.36}));
    PhotometryObject->SetStringField(
        TEXT("exposed_parameters"),
        TEXT("BarkBaseColorScale, BarkAOInfluence, LeafBaseColorScale, LeafAOInfluence, LeafTransmissionTint"));
    ReportObject->SetObjectField(TEXT("photometry"), PhotometryObject);
    ReportObject->SetStringField(
        TEXT("family_scope"),
        TEXT("five independent adult and three independent intermediate crown-form prototypes; species-count authoring threshold met"));

    TArray<TSharedPtr<FJsonValue>> CrownFormValues;
    for (const FFutaleufuCoigueRuntime& Variant : Variants)
    {
        TSharedRef<FJsonObject> FormObject = MakeShared<FJsonObject>();
        FormObject->SetStringField(TEXT("id"), Variant.Form.Id);
        FormObject->SetStringField(TEXT("display_name"), Variant.Form.DisplayName);
        FormObject->SetStringField(TEXT("life_stage"), Variant.Form.LifeStage);
        FormObject->SetNumberField(TEXT("seed_offset"), Variant.Form.SeedOffset);
        FormObject->SetNumberField(TEXT("trunk_height_scale"), Variant.Form.TrunkHeightScale);
        FormObject->SetNumberField(TEXT("trunk_radius_scale"), Variant.Form.TrunkRadiusScale);
        FormObject->SetNumberField(TEXT("crown_base_z_cm"), Variant.Form.CrownBaseZCm);
        FormObject->SetNumberField(TEXT("crown_span_z_cm"), Variant.Form.CrownSpanZCm);
        FormObject->SetNumberField(TEXT("crown_width_scale"), Variant.Form.CrownWidthScale);
        FormObject->SetNumberField(TEXT("branch_uplift_scale"), Variant.Form.BranchUpliftScale);
        FormObject->SetNumberField(TEXT("asymmetry_scale"), Variant.Form.AsymmetryScale);
        FormObject->SetArrayField(
            TEXT("trunk_lean_top_cm"),
            NumberArray({Variant.Form.TrunkLeanTopCm.X, Variant.Form.TrunkLeanTopCm.Y}));
        FormObject->SetNumberField(
            TEXT("suppressed_sector_center_degrees"), Variant.Form.SuppressedSectorCenterDegrees);
        FormObject->SetNumberField(
            TEXT("suppressed_sector_half_width_degrees"), Variant.Form.SuppressedSectorHalfWidthDegrees);
        FormObject->SetNumberField(
            TEXT("suppressed_sector_length_scale"), Variant.Form.SuppressedSectorLengthScale);
        FormObject->SetNumberField(TEXT("crown_gap_center_t"), Variant.Form.CrownGapCenterT);
        FormObject->SetNumberField(TEXT("crown_gap_half_width_t"), Variant.Form.CrownGapHalfWidthT);
        FormObject->SetNumberField(TEXT("crown_gap_length_scale"), Variant.Form.CrownGapLengthScale);
        FormObject->SetNumberField(TEXT("damage_modulo"), Variant.Form.DamageModulo);
        FormObject->SetNumberField(TEXT("damage_remainder"), Variant.Form.DamageRemainder);
        FormObject->SetNumberField(
            TEXT("damaged_branch_length_scale"), Variant.Form.DamagedBranchLengthScale);

        TSharedRef<FJsonObject> TopologyObject = MakeShared<FJsonObject>();
        const int32 NearLeafCardCount = Variant.LeafTriangles.Num() / 6;
        const int32 NearAnchorCount = NearLeafCardCount /
            (FutaleufuCoigueBranchletsPerParentShoot * FutaleufuCoigueAttachedLeavesPerBranchlet);
        int32 DamagedBranchCount = 0;
        if (Variant.Form.DamageModulo > 0)
        {
            for (int32 BranchIndex = 0; BranchIndex < Variant.Form.MainBranchCount; ++BranchIndex)
            {
                DamagedBranchCount +=
                    (BranchIndex + Variant.Form.SeedOffset) % Variant.Form.DamageModulo ==
                            Variant.Form.DamageRemainder
                        ? 1
                        : 0;
            }
        }
        TopologyObject->SetNumberField(TEXT("main_branches"), Variant.Form.MainBranchCount);
        TopologyObject->SetNumberField(TEXT("deterministically_damaged_branches"), DamagedBranchCount);
        TopologyObject->SetNumberField(TEXT("near_foliage_anchors"), NearAnchorCount);
        TopologyObject->SetNumberField(TEXT("parent_shoots"), NearAnchorCount);
        TopologyObject->SetNumberField(TEXT("far_only_apical_anchors"), 24);
        TopologyObject->SetNumberField(
            TEXT("far_only_interior_crown_anchors"), Variant.Form.FarCrownVolumeAnchorCount);
        TopologyObject->SetNumberField(
            TEXT("branchlets_per_parent_shoot"), FutaleufuCoigueBranchletsPerParentShoot);
        TopologyObject->SetNumberField(
            TEXT("tertiary_branches_per_branchlet"), FutaleufuCoigueTertiaryBranchesPerBranchlet);
        TopologyObject->SetNumberField(
            TEXT("attached_leaf_cards_per_branchlet"), FutaleufuCoigueAttachedLeavesPerBranchlet);
        TopologyObject->SetNumberField(TEXT("petioles_per_leaf"), 1);
        TopologyObject->SetNumberField(TEXT("floating_near_card_count"), 0);
        FormObject->SetObjectField(TEXT("topology"), TopologyObject);

        TSharedRef<FJsonObject> RoutingObject = MakeShared<FJsonObject>();
        RoutingObject->SetNumberField(TEXT("required_near_branchlet_clearance_cm"), 1.2);
        RoutingObject->SetNumberField(TEXT("required_near_tertiary_clearance_cm"), 0.6);
        RoutingObject->SetNumberField(
            TEXT("minimum_near_branchlet_clearance_cm"),
            Variant.RoutingMetrics.MinNearBranchletClearanceCm);
        RoutingObject->SetNumberField(
            TEXT("minimum_near_tertiary_clearance_cm"),
            Variant.RoutingMetrics.MinNearTertiaryClearanceCm);
        RoutingObject->SetNumberField(
            TEXT("rerouted_branchlet_count"), Variant.RoutingMetrics.ReroutedBranchletCount);
        RoutingObject->SetNumberField(
            TEXT("rerouted_tertiary_count"), Variant.RoutingMetrics.ReroutedTertiaryCount);
        RoutingObject->SetNumberField(
            TEXT("unresolved_branchlet_clearance_count"),
            Variant.RoutingMetrics.UnresolvedBranchletClearanceCount);
        RoutingObject->SetNumberField(
            TEXT("unresolved_tertiary_clearance_count"),
            Variant.RoutingMetrics.UnresolvedTertiaryClearanceCount);
        RoutingObject->SetBoolField(
            TEXT("near_clearance_contract_passed"),
            Variant.RoutingMetrics.UnresolvedBranchletClearanceCount == 0 &&
                Variant.RoutingMetrics.UnresolvedTertiaryClearanceCount == 0);
        FormObject->SetObjectField(TEXT("routing"), RoutingObject);

        auto MakeMeshObject = [&VectorArray](
                                  const FString& Asset,
                                  UStaticMesh* Mesh,
                                  int32 SourceVertices,
                                  int32 SourceTriangles,
                                  int32 SourceCards)
        {
            TSharedRef<FJsonObject> MeshObject = MakeShared<FJsonObject>();
            MeshObject->SetStringField(TEXT("asset"), Asset);
            MeshObject->SetNumberField(TEXT("source_vertices"), SourceVertices);
            MeshObject->SetNumberField(TEXT("source_triangles"), SourceTriangles);
            if (SourceCards >= 0)
            {
                MeshObject->SetNumberField(TEXT("source_card_count"), SourceCards);
            }
            MeshObject->SetNumberField(TEXT("render_vertices"), Mesh->GetNumVertices(0));
            MeshObject->SetNumberField(TEXT("render_triangles"), Mesh->GetNumTriangles(0));
            MeshObject->SetNumberField(
                TEXT("exclusive_resource_bytes"),
                static_cast<double>(Mesh->GetResourceSizeBytes(EResourceSizeMode::Exclusive)));
            MeshObject->SetArrayField(TEXT("bounds_cm"), VectorArray(Mesh->GetBoundingBox().GetSize()));
            MeshObject->SetBoolField(TEXT("nanite_enabled"), Mesh->IsNaniteEnabled());
            return MeshObject;
        };
        FormObject->SetObjectField(
            TEXT("trunk"),
            MakeMeshObject(
                Variant.TrunkPackagePath, Variant.TrunkMesh,
                Variant.TrunkVertices.Num(), Variant.TrunkTriangles.Num() / 3, -1));
        FormObject->SetObjectField(
            TEXT("branchlets"),
            MakeMeshObject(
                Variant.BranchletPackagePath, Variant.BranchletMesh,
                Variant.BranchletVertices.Num(), Variant.BranchletTriangles.Num() / 3, -1));
        FormObject->SetObjectField(
            TEXT("foliage"),
            MakeMeshObject(
                Variant.LeafPackagePath, Variant.LeafMesh,
                Variant.LeafVertices.Num(), Variant.LeafTriangles.Num() / 3,
                Variant.LeafTriangles.Num() / 6));
        FormObject->SetObjectField(
            TEXT("far_foliage"),
            MakeMeshObject(
                Variant.FarLeafPackagePath, Variant.FarLeafMesh,
                Variant.FarLeafVertices.Num(), Variant.FarLeafTriangles.Num() / 3,
                Variant.FarLeafTriangles.Num() / 6));
        FormObject->SetObjectField(
            TEXT("runtime_far_foliage"),
            MakeMeshObject(
                Variant.RuntimeFarLeafPackagePath, Variant.RuntimeFarLeafMesh,
                Variant.RuntimeFarLeafVertices.Num(),
                Variant.RuntimeFarLeafTriangles.Num() / 3,
                Variant.RuntimeFarLeafTriangles.Num() / 6));
        CrownFormValues.Add(MakeShared<FJsonValueObject>(FormObject));
    }
    ReportObject->SetArrayField(TEXT("crown_forms"), CrownFormValues);

    TSharedRef<FJsonObject> LeafContractObject = MakeShared<FJsonObject>();
    LeafContractObject->SetStringField(TEXT("atlas"), TEXT("4x4_v2"));
    LeafContractObject->SetNumberField(TEXT("single_leaf_tiles"), 12);
    LeafContractObject->SetNumberField(TEXT("tiny_twig_tiles"), 4);
    LeafContractObject->SetArrayField(TEXT("visible_leaf_length_cm"), NumberArray({2.0, 3.5}));
    LeafContractObject->SetArrayField(
        TEXT("padding_aware_single_leaf_card_cm"), NumberArray({2.8, 5.8}));
    LeafContractObject->SetNumberField(TEXT("parent_shoot_length_cm"), 56.0);
    LeafContractObject->SetArrayField(TEXT("branchlet_length_cm"), NumberArray({24.0, 40.0}));
    LeafContractObject->SetArrayField(
        TEXT("padding_aware_far_twig_card_cm"), NumberArray({36.0, 80.0}));
    LeafContractObject->SetArrayField(TEXT("primary_tip_radius_cm"), NumberArray({7.0, 3.2, 0.8}));
    LeafContractObject->SetArrayField(
        TEXT("terminal_twig_collar_radius_cm"), NumberArray({3.2, 1.4, 0.72}));
    LeafContractObject->SetArrayField(TEXT("parent_shoot_radius_cm"), NumberArray({0.74, 0.20}));
    LeafContractObject->SetStringField(
        TEXT("near_representation"),
        TEXT("continuous_limb_to_collar_to_parent_shoot_to_branchlet_to_tertiary_to_petiole_hierarchy"));
    LeafContractObject->SetStringField(
        TEXT("far_representation"), TEXT("branch_sprays_plus_irregular_interior_crown_volume"));
    TArray<TSharedPtr<FJsonValue>> WindParameters;
    WindParameters.Add(MakeShared<FJsonValueString>(TEXT("WindIntensity")));
    WindParameters.Add(MakeShared<FJsonValueString>(TEXT("WindWeight")));
    WindParameters.Add(MakeShared<FJsonValueString>(TEXT("WindSpeed")));
    LeafContractObject->SetArrayField(TEXT("wind_parameters"), WindParameters);
    ReportObject->SetObjectField(TEXT("leaf_contract"), LeafContractObject);

    TSharedRef<FJsonObject> LodObject = MakeShared<FJsonObject>();
    LodObject->SetNumberField(TEXT("near_leaf_max_draw_distance_cm"), 3600.0);
    LodObject->SetNumberField(TEXT("far_crown_min_draw_distance_cm"), 2800.0);
    LodObject->SetNumberField(TEXT("overlap_cm"), 800.0);
    LodObject->SetNumberField(TEXT("runtime_far_card_stride"), 6);
    LodObject->SetNumberField(TEXT("runtime_far_card_scale"), 1.28);
    LodObject->SetStringField(
        TEXT("status"),
        TEXT("full_isolated_near_and_far_assets_retained_plus_reduced_far_corridor_lod_candidate"));
    ReportObject->SetObjectField(TEXT("lod_handoff"), LodObject);

    TSharedRef<FJsonObject> CaptureGateObject = MakeShared<FJsonObject>();
    CaptureGateObject->SetStringField(
        TEXT("status"),
        bCaptured
            ? TEXT("forty_isolated_views_and_512_tree_runtime_benchmark_captured")
            : TEXT("capture_failed"));
    CaptureGateObject->SetNumberField(TEXT("views_per_form"), 5);
    CaptureGateObject->SetNumberField(TEXT("form_count"), Variants.Num());
    CaptureGateObject->SetStringField(
        TEXT("git_policy"), TEXT("generated map and captures remain local until human review"));
    TArray<TSharedPtr<FJsonValue>> CaptureValues;
    for (const FNativeCanopyCaptureRequest& Request : CaptureRequests)
    {
        CaptureValues.Add(MakeShared<FJsonValueString>(Request.RelativePath));
    }
    CaptureGateObject->SetArrayField(TEXT("captures"), CaptureValues);
    ReportObject->SetObjectField(TEXT("capture_gate"), CaptureGateObject);

    TSharedRef<FJsonObject> RuntimeBenchmarkObject = MakeShared<FJsonObject>();
    RuntimeBenchmarkObject->SetStringField(
        TEXT("map_asset"), RuntimeBenchmarkSpec.MapPackagePath);
    RuntimeBenchmarkObject->SetStringField(TEXT("capture"), RuntimeBenchmarkCapturePath);
    RuntimeBenchmarkObject->SetNumberField(TEXT("tree_instance_count"), 512);
    RuntimeBenchmarkObject->SetNumberField(TEXT("crown_form_count"), Variants.Num());
    RuntimeBenchmarkObject->SetNumberField(TEXT("hism_component_count"), Variants.Num() * 2);
    RuntimeBenchmarkObject->SetBoolField(TEXT("map_saved"), bRuntimeBenchmarkMapSaved);
    RuntimeBenchmarkObject->SetBoolField(TEXT("capture_saved"), bRuntimeBenchmarkCaptured);
    RuntimeBenchmarkObject->SetStringField(
        TEXT("scope"),
        TEXT("offscreen Metal authoring density and silhouette evidence; not packaged frame-time, draw-call, overdraw, streaming, culling, or VR proof"));
    ReportObject->SetObjectField(TEXT("runtime_far_lod_hism_benchmark"), RuntimeBenchmarkObject);

    auto AddTimingSummary = [](TSharedRef<FJsonObject> Target, const TCHAR* Field, TArray<double> Values)
    {
        Values.Sort();
        TSharedRef<FJsonObject> Summary = MakeShared<FJsonObject>();
        if (Values.IsEmpty())
        {
            Summary->SetNumberField(TEXT("sample_count"), 0);
        }
        else
        {
            const int32 Middle = Values.Num() / 2;
            const double Median = Values.Num() % 2 == 0
                ? (Values[Middle - 1] + Values[Middle]) * 0.5
                : Values[Middle];
            Summary->SetNumberField(TEXT("sample_count"), Values.Num());
            Summary->SetNumberField(TEXT("minimum_ms"), Values[0]);
            Summary->SetNumberField(TEXT("median_ms"), Median);
            Summary->SetNumberField(TEXT("maximum_ms"), Values.Last());
        }
        Target->SetObjectField(Field, Summary);
    };
    TArray<double> CaptureWallTimes;
    TArray<double> GameThreadFrameTimes;
    TArray<double> RenderThreadFrameTimes;
    TArray<double> GpuFrameTimes;
    TArray<TSharedPtr<FJsonValue>> CaptureTimingValues;
    for (const FNativeCanopyCaptureRequest& Request : CaptureRequests)
    {
        if (Request.bCaptured)
        {
            CaptureWallTimes.Add(Request.CaptureWallTimeMs);
            GameThreadFrameTimes.Add(Request.GameThreadFrameTimeMs);
            RenderThreadFrameTimes.Add(Request.RenderThreadFrameTimeMs);
            GpuFrameTimes.Add(Request.GpuFrameTimeMs);
        }
        TSharedRef<FJsonObject> Timing = MakeShared<FJsonObject>();
        Timing->SetStringField(TEXT("capture"), Request.RelativePath);
        Timing->SetBoolField(TEXT("captured"), Request.bCaptured);
        Timing->SetNumberField(TEXT("capture_wall_time_ms"), Request.CaptureWallTimeMs);
        Timing->SetNumberField(TEXT("game_thread_frame_time_ms"), Request.GameThreadFrameTimeMs);
        Timing->SetNumberField(TEXT("render_thread_frame_time_ms"), Request.RenderThreadFrameTimeMs);
        Timing->SetNumberField(TEXT("gpu_frame_time_ms"), Request.GpuFrameTimeMs);
        CaptureTimingValues.Add(MakeShared<FJsonValueObject>(Timing));
    }
    uint64 FamilyExclusiveResourceBytes = 0;
    int64 FamilyRenderVertices = 0;
    int64 FamilyRenderTriangles = 0;
    uint64 RuntimeFarFamilyExclusiveResourceBytes = 0;
    int64 RuntimeFarFamilyRenderVertices = 0;
    int64 RuntimeFarFamilyRenderTriangles = 0;
    for (const FFutaleufuCoigueRuntime& Variant : Variants)
    {
        UStaticMesh* Meshes[] = {
            Variant.TrunkMesh, Variant.BranchletMesh, Variant.LeafMesh, Variant.FarLeafMesh};
        for (UStaticMesh* Mesh : Meshes)
        {
            FamilyExclusiveResourceBytes +=
                Mesh->GetResourceSizeBytes(EResourceSizeMode::Exclusive);
            FamilyRenderVertices += Mesh->GetNumVertices(0);
            FamilyRenderTriangles += Mesh->GetNumTriangles(0);
        }
        UStaticMesh* RuntimeMeshes[] = {
            Variant.TrunkMesh, Variant.RuntimeFarLeafMesh};
        for (UStaticMesh* Mesh : RuntimeMeshes)
        {
            RuntimeFarFamilyExclusiveResourceBytes +=
                Mesh->GetResourceSizeBytes(EResourceSizeMode::Exclusive);
            RuntimeFarFamilyRenderVertices += Mesh->GetNumVertices(0);
            RuntimeFarFamilyRenderTriangles += Mesh->GetNumTriangles(0);
        }
    }
    TSharedRef<FJsonObject> PerformanceObject = MakeShared<FJsonObject>();
    PerformanceObject->SetStringField(
        TEXT("measurement_scope"),
        TEXT("UE 5.8 Metal offscreen isolated-review capture plus 512-tree HISM authoring density map; not gameplay, packaged-build frame time, or VR evidence"));
    PerformanceObject->SetNumberField(
        TEXT("family_exclusive_resource_bytes"), static_cast<double>(FamilyExclusiveResourceBytes));
    PerformanceObject->SetNumberField(
        TEXT("family_render_vertices_lod0"), static_cast<double>(FamilyRenderVertices));
    PerformanceObject->SetNumberField(
        TEXT("family_render_triangles_lod0"), static_cast<double>(FamilyRenderTriangles));
    PerformanceObject->SetNumberField(
        TEXT("runtime_far_family_exclusive_resource_bytes"),
        static_cast<double>(RuntimeFarFamilyExclusiveResourceBytes));
    PerformanceObject->SetNumberField(
        TEXT("runtime_far_family_render_vertices_lod0"),
        static_cast<double>(RuntimeFarFamilyRenderVertices));
    PerformanceObject->SetNumberField(
        TEXT("runtime_far_family_render_triangles_lod0"),
        static_cast<double>(RuntimeFarFamilyRenderTriangles));
    PerformanceObject->SetNumberField(
        TEXT("runtime_far_family_resource_reduction_fraction"),
        FamilyExclusiveResourceBytes > 0
            ? 1.0 - static_cast<double>(RuntimeFarFamilyExclusiveResourceBytes) /
                static_cast<double>(FamilyExclusiveResourceBytes)
            : 0.0);
    PerformanceObject->SetNumberField(TEXT("static_mesh_assets"), Variants.Num() * 5);
    PerformanceObject->SetNumberField(TEXT("near_tree_material_sections"), 3);
    PerformanceObject->SetNumberField(TEXT("far_tree_material_sections"), 2);
    PerformanceObject->SetStringField(
        TEXT("unmeasured_gates"),
        TEXT("packaged desktop and VR frame time, masked overdraw, motion vectors, draw-call submission, streaming, culling, near-to-far transition, and full mixed-ecology corridor density"));
    auto HasVariablePositiveSamples = [](const TArray<double>& Values)
    {
        if (Values.Num() < 2 || Algo::AnyOf(Values, [](double Value) { return Value <= 0.0; }))
        {
            return false;
        }
        double Minimum = Values[0];
        double Maximum = Values[0];
        for (double Value : Values)
        {
            Minimum = FMath::Min(Minimum, Value);
            Maximum = FMath::Max(Maximum, Value);
        }
        return Maximum - Minimum > 0.0001;
    };
    const bool bCaptureWallTimeValid =
        CaptureWallTimes.Num() == CaptureRequests.Num() &&
        !Algo::AnyOf(CaptureWallTimes, [](double Value) { return Value <= 0.0; });
    const bool bFrameCycleCountersValid =
        HasVariablePositiveSamples(GameThreadFrameTimes) &&
        HasVariablePositiveSamples(RenderThreadFrameTimes) &&
        HasVariablePositiveSamples(GpuFrameTimes);
    PerformanceObject->SetBoolField(TEXT("capture_wall_time_valid"), bCaptureWallTimeValid);
    PerformanceObject->SetBoolField(
        TEXT("frame_cycle_counters_valid"), bFrameCycleCountersValid);
    PerformanceObject->SetStringField(
        TEXT("frame_cycle_validation"),
        bFrameCycleCountersValid
            ? TEXT("all counters are positive and vary across the forty rendered samples")
            : TEXT("rejected: offscreen editor counters must be positive and vary across samples; use a packaged on-device benchmark for production frame-time evidence"));
    AddTimingSummary(PerformanceObject, TEXT("capture_wall_time"), CaptureWallTimes);
    AddTimingSummary(PerformanceObject, TEXT("game_thread_frame_time"), GameThreadFrameTimes);
    AddTimingSummary(PerformanceObject, TEXT("render_thread_frame_time"), RenderThreadFrameTimes);
    AddTimingSummary(PerformanceObject, TEXT("gpu_frame_time"), GpuFrameTimes);
    PerformanceObject->SetArrayField(TEXT("capture_samples"), CaptureTimingValues);
    ReportObject->SetObjectField(TEXT("performance_instrumentation"), PerformanceObject);
    ReportObject->SetStringField(
        TEXT("promotion_boundary"),
        TEXT("isolated human visual acceptance, temporal wind, packaged desktop and VR corridor performance, and ecology gates are required before corridor substitution"));

    FString Report;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&Report);
    const bool bSerialized = FJsonSerializer::Serialize(ReportObject, Writer);
    Report += TEXT("\n");
    const bool bReportSaved = bSerialized && FFileHelper::SaveStringToFile(Report, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s native-canopy prototype report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bCaptured && bReportSaved;
}
