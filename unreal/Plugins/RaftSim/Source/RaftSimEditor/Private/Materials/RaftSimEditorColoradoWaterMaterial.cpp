#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"

namespace RaftSimEditorEnvironment
{
namespace
{
template <typename ExpressionType>
ExpressionType* AddColoradoWaterExpression(UMaterial* Material)
{
    ExpressionType* Expression = NewObject<ExpressionType>(Material);
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}
} // namespace

UMaterial* LoadOrCreateColoradoHanceWaterParent(FString& OutSummary)
{
    if (!RaftSimPhotorealMaterials::BuildColoradoHanceWaterTextureAssets())
    {
        OutSummary += TEXT(
            "Failed to create the Colorado Hance river-local water textures.\n");
        return nullptr;
    }
    static const FString MaterialPackagePath =
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
             "M_RaftSim_Colorado_HanceDefaultLitWater");
    static const FString MaterialObjectName =
        TEXT("M_RaftSim_Colorado_HanceDefaultLitWater");
    const FString MaterialObjectPath = FString::Printf(
        TEXT("%s.%s"), *MaterialPackagePath, *MaterialObjectName);

    UPackage* Package = CreatePackage(*MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the Colorado Hance water package.\n");
        return nullptr;
    }

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(
        UMaterial::StaticClass(), nullptr, *MaterialObjectPath));
    if (!Material)
    {
        Material = FindObject<UMaterial>(Package, *MaterialObjectName);
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *MaterialObjectName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += TEXT("Failed to create the Colorado Hance water material.\n");
        return nullptr;
    }

    UTexture2D* DefaultNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal."
             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal"));
    if (!DefaultNormalTexture)
    {
        OutSummary += TEXT("Failed to load the Colorado water normal fallback.\n");
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Translucent;
    Material->TranslucencyLightingMode = TLM_SurfacePerPixelLighting;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;

    auto Scalar = [Material](const TCHAR* Name, float Value)
    {
        UMaterialExpressionScalarParameter* Parameter =
            AddColoradoWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ColoradoHanceWaterV2");
        return Parameter;
    };
    auto Vector = [Material](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            AddColoradoWaterExpression<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ColoradoHanceWaterV2");
        return Parameter;
    };
    auto Constant = [Material](float Value)
    {
        UMaterialExpressionConstant* Result =
            AddColoradoWaterExpression<UMaterialExpressionConstant>(Material);
        Result->R = Value;
        return Result;
    };
    auto Multiply = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Result =
            AddColoradoWaterExpression<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Add = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Result =
            AddColoradoWaterExpression<UMaterialExpressionAdd>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Lerp = [Material](
                    UMaterialExpression* A,
                    UMaterialExpression* B,
                    UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Result =
            AddColoradoWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Result->Alpha.Expression = Alpha;
        return Result;
    };

    // The Hance moderate-release cooked field already authors the ribbon's
    // geometry and vertex color on the CPU. This material adds river-local
    // optics only and never samples the South Fork shader field a second time.
    UMaterialExpressionVertexColor* VertexColor =
        AddColoradoWaterExpression<UMaterialExpressionVertexColor>(Material);
    UMaterialExpressionComponentMask* VertexOpacity =
        AddColoradoWaterExpression<UMaterialExpressionComponentMask>(Material);
    VertexOpacity->Input.Expression = VertexColor;
    VertexOpacity->Input.OutputIndex = 4;
    VertexOpacity->R = true;
    UMaterialExpression* PhysicalSurfaceTint = Lerp(
        Vector(TEXT("SurfaceTint"), FLinearColor(0.072f, 0.115f, 0.088f, 0.0f)),
        VertexColor,
        Scalar(TEXT("VertexTintWeight"), 0.74f));
    UMaterialExpression* BaseColor = Multiply(
        PhysicalSurfaceTint,
        Scalar(TEXT("BaseColorScale"), 1.06f));

    UMaterialExpressionNoise* ReachVariation =
        AddColoradoWaterExpression<UMaterialExpressionNoise>(Material);
    ReachVariation->Scale = 0.00029f;
    ReachVariation->bTurbulence = true;
    ReachVariation->Levels = 3;
    ReachVariation->OutputMin = 0.0f;
    ReachVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* SurfaceVariation =
        AddColoradoWaterExpression<UMaterialExpressionNoise>(Material);
    SurfaceVariation->Scale = 0.00141f;
    SurfaceVariation->bTurbulence = true;
    SurfaceVariation->Levels = 2;
    SurfaceVariation->OutputMin = 0.0f;
    SurfaceVariation->OutputMax = 1.0f;
    UMaterialExpression* VariationField = Add(
        Multiply(ReachVariation, Constant(0.62f)),
        Multiply(SurfaceVariation, Constant(0.38f)));
    UMaterialExpression* PatternedColor = Lerp(
        Multiply(BaseColor, Constant(0.78f)),
        Multiply(BaseColor, Constant(1.22f)),
        VariationField);
    UMaterialExpression* OpticallyVariedBaseColor = Lerp(
        BaseColor,
        PatternedColor,
        Scalar(TEXT("SurfaceVariationStrength"), 0.32f));

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter = Vector(
        TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.0f, 0.0f, 0.0f));
    UMaterialExpressionVectorParameter* AtlasTileScaleParameter = Vector(
        TEXT("AtlasTileScale"), FLinearColor(1.0f, 1.0f, 0.0f, 0.0f));
    UMaterialExpressionComponentMask* AtlasTileOrigin =
        AddColoradoWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasTileOrigin->R = true;
    AtlasTileOrigin->G = true;
    UMaterialExpressionComponentMask* AtlasTileScale =
        AddColoradoWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileScale->Input.Expression = AtlasTileScaleParameter;
    AtlasTileScale->R = true;
    AtlasTileScale->G = true;

    auto AddNormalSample =
        [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](
            float UTiling,
            float VTiling,
            float SpeedX,
            float SpeedY) -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* TexCoord =
            AddColoradoWaterExpression<UMaterialExpressionTextureCoordinate>(Material);
        TexCoord->UTiling = UTiling;
        TexCoord->VTiling = VTiling;
        UMaterialExpressionPanner* Panner =
            AddColoradoWaterExpression<UMaterialExpressionPanner>(Material);
        Panner->SpeedX = SpeedX;
        Panner->SpeedY = SpeedY;
        Panner->Coordinate.Expression = TexCoord;
        UMaterialExpressionFrac* WrappedUv =
            AddColoradoWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUv->Input.Expression = Panner;
        UMaterialExpressionMultiply* ScaledUv =
            AddColoradoWaterExpression<UMaterialExpressionMultiply>(Material);
        ScaledUv->A.Expression = WrappedUv;
        ScaledUv->B.Expression = AtlasTileScale;
        UMaterialExpressionAdd* AtlasUv =
            AddColoradoWaterExpression<UMaterialExpressionAdd>(Material);
        AtlasUv->A.Expression = ScaledUv;
        AtlasUv->B.Expression = AtlasTileOrigin;
        UMaterialExpressionTextureSampleParameter2D* Sample =
            AddColoradoWaterExpression<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = TEXT("WaterNormalAtlas");
        Sample->Texture = DefaultNormalTexture;
        Sample->SamplerType = SAMPLERTYPE_Normal;
        Sample->Coordinates.Expression = AtlasUv;
        Sample->Group = TEXT("ColoradoHanceWaterV2");
        return Sample;
    };

    UMaterialExpression* NormalA = AddNormalSample(0.57f, 1.59f, 0.030f, 0.007f);
    UMaterialExpression* NormalB = AddNormalSample(1.19f, 2.83f, -0.014f, 0.022f);
    UMaterialExpressionConstant3Vector* FlatNormal =
        AddColoradoWaterExpression<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 0.0f);
    UMaterialExpression* WaterNormal = Lerp(
        FlatNormal,
        Lerp(NormalA, NormalB, Constant(0.48f)),
        Scalar(TEXT("NormalIntensity"), 0.30f));

    UMaterialExpression* BaseEmissive = Multiply(
        OpticallyVariedBaseColor,
        Scalar(TEXT("EmissiveFillScale"), 0.20f));
    UMaterialExpressionFresnel* ReflectionFresnel =
        AddColoradoWaterExpression<UMaterialExpressionFresnel>(Material);
    ReflectionFresnel->Exponent = 5.0f;
    ReflectionFresnel->BaseReflectFraction = 0.02f;
    UMaterialExpression* ReflectionFill = Multiply(
        Vector(TEXT("ReflectionTint"), FLinearColor(0.28f, 0.40f, 0.46f, 0.0f)),
        Multiply(
            ReflectionFresnel,
            Scalar(TEXT("ReflectionFillIntensity"), 0.14f)));
    UMaterialExpressionScalarParameter* Roughness =
        Scalar(TEXT("Roughness"), 0.25f);
    UMaterialExpressionScalarParameter* Specular =
        Scalar(TEXT("Specular"), 0.46f);

    // Compatibility parameters remain inspectable but unbound. CPU-authored
    // vertex color is the only cooked-field source on this capture ribbon.
    Scalar(TEXT("SolverFieldEnable"), 0.0f);
    Scalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    Scalar(TEXT("SolverDepthColorWeight"), 0.0f);
    Scalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    Scalar(TEXT("SolverFroudeAerationWeight"), 0.0f);
    Scalar(TEXT("SolverSpeedVisualGain"), 0.0f);
    Scalar(TEXT("SolverFroudeVisualGain"), 0.0f);
    Vector(TEXT("SolverDeepWaterTint"), FLinearColor(0.050f, 0.065f, 0.046f, 0.0f));
    Vector(TEXT("SolverAerationTint"), FLinearColor(0.84f, 0.82f, 0.74f, 0.0f));
    UMaterialExpressionScalarParameter* Opacity =
        Scalar(TEXT("Opacity"), 0.90f);
    UMaterialExpression* DepthTransmittingOpacity = Multiply(
        VertexOpacity, Opacity);
    UMaterialExpressionScalarParameter* RefractionIor =
        Scalar(TEXT("RefractionIor"), 1.333f);
    Scalar(TEXT("PhaseG"), 0.08f);
    Vector(TEXT("ScatteringCoefficients"), FLinearColor(0.0042f, 0.0023f, 0.0007f, 0.0f));
    Vector(TEXT("AbsorptionCoefficients"), FLinearColor(0.0014f, 0.0022f, 0.0040f, 0.0f));
    Vector(TEXT("ColorScaleBehindWater"), FLinearColor(0.84f, 0.76f, 0.62f, 0.0f));

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->BaseColor, OpticallyVariedBaseColor);
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->EmissiveColor, Add(BaseEmissive, ReflectionFill));
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, WaterNormal);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
        ConnectPreviewMaterialScalarInput(
            EditorOnlyData->Opacity, DepthTransmittingOpacity);
        ConnectPreviewMaterialScalarInput(
            EditorOnlyData->Refraction, RefractionIor);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_Water))
    {
        OutSummary += TEXT("Failed to enable Water usage for Colorado Hance water.\n");
        return nullptr;
    }
    Material->PostEditChange();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        MaterialPackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += TEXT("Failed to save the Colorado Hance water material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    OutSummary += TEXT(
        "Built Colorado Hance transmitting Default Lit water V2 with a "
        "river-local first-party flow normal, depth/bank-conditioned vertex "
        "opacity, physical IOR, native two-scale moving normals, CPU-authored "
        "cooked-field color authority, and no displacement.\n");
    return Material;
}

UMaterialInstanceConstant* LoadOrCreateColoradoHanceLiveWaterInstance(
    FString& OutSummary)
{
    if (!RaftSimPhotorealMaterials::BuildColoradoHanceWaterTextureAssets())
    {
        OutSummary += TEXT(
            "Failed to create Colorado Hance live-water texture assets.\n");
        return nullptr;
    }

    static const TCHAR* PackagePath = TEXT(
        "/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
        "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2");
    static const TCHAR* AssetName =
        TEXT("MI_RaftSim_ColoradoHance_LiveVolumeWaterV2");
    static const TCHAR* ObjectPath = TEXT(
        "/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
        "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2."
        "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2");
    UMaterialInterface* SharedTransmissionParent = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "M_RaftSim_SouthForkRaftTransmissionWaterV4."
             "M_RaftSim_SouthForkRaftTransmissionWaterV4"));
    UTexture2D* FlowNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal."
             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal"));
    UTexture2D* FoamLace = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
             "T_RaftSim_ColoradoHanceWaterV1_FoamLace."
             "T_RaftSim_ColoradoHanceWaterV1_FoamLace"));
    UPackage* Package = CreatePackage(PackagePath);
    if (!SharedTransmissionParent || !FlowNormal || !FoamLace || !Package)
    {
        OutSummary += TEXT(
            "Colorado Hance live-water parent or river-local texture is missing.\n");
        return nullptr;
    }

    UMaterialInstanceConstant* Instance =
        LoadObject<UMaterialInstanceConstant>(nullptr, ObjectPath);
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        OutSummary += TEXT(
            "Failed to create the Colorado Hance live-water material instance.\n");
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(SharedTransmissionParent);
    Instance->ClearParameterValuesEditorOnly();
    auto SetScalar = [Instance](const TCHAR* Name, float Value)
    {
        Instance->SetScalarParameterValueEditorOnly(
            FMaterialParameterInfo(Name), Value);
    };
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterFlowNormalPrimary")), FlowNormal);
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterFlowNormalCross")), FlowNormal);
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WhitewaterFoamLace")), FoamLace);
    // The lace remains an optical breakup input. The shared parent multiplies
    // it by solver-authored speed/foam fields, so it cannot paint hydraulic
    // features into calm water or dry cells.
    SetScalar(TEXT("HydraulicFoamCoverageGain"), 0.68f);
    SetScalar(TEXT("HydraulicFoamColorBreakupGain"), 0.60f);
    SetScalar(TEXT("HydraulicFoamColorCoreGain"), 0.72f);
    SetScalar(TEXT("SpeedAerationFraction"), 0.14f);
    SetScalar(TEXT("FoamRoughness"), 0.66f);
    SetScalar(TEXT("ReachHueVariation"), 0.08f);
    SetScalar(TEXT("CalmSurfaceColorVariation"), 0.10f);
    SetScalar(TEXT("FallbackSkyReflectionFloor"), 0.58f);
    SetScalar(TEXT("FallbackSkyReflectionVariation"), 0.30f);
    // 2026-08-06 named human review: Hance read as "brown water or no
    // water" — the flattened surface texture let the sediment bed dominate.
    // Raise normal/ripple energy and lift the surface response over the bed
    // so the interface reads as liquid; the sediment tint itself is a
    // river-identity decision left to the Colorado-specific review.
    SetScalar(TEXT("RippleGrazingFloor"), 0.55f);
    SetScalar(TEXT("SlickNormalFloor"), 0.55f);
    SetScalar(TEXT("OpticalDepthResponseExponent"), 0.45f);
    Instance->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += TEXT(
            "Failed to save the Colorado Hance live-water material instance.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Built Colorado Hance river-local live-volume water V2 with "
        "project-owned flow-normal and solver-masked foam-lace textures.\n");
    return Instance;
}

static void HandleRefreshColoradoHanceWaterMaterials(const TArray<FString>&)
{
    FString Summary;
    bool bCaptureSucceeded = false;
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate :
         GetLandscapeImportCandidateSpecs())
    {
        if (Candidate.PreviewSpec.RiverId != TEXT("colorado_river"))
        {
            continue;
        }
        bCaptureSucceeded = LoadOrCreateLandscapeCandidateWaterMaterial(
            Candidate.PreviewSpec,
            Summary,
            true) != nullptr;
        break;
    }
    const bool bLiveSucceeded =
        LoadOrCreateColoradoHanceLiveWaterInstance(Summary) != nullptr;
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim.RefreshColoradoHanceWaterMaterials: capture=%d live=%d\n%s"),
        bCaptureSucceeded ? 1 : 0,
        bLiveSucceeded ? 1 : 0,
        *Summary);
}

static FAutoConsoleCommand GRefreshColoradoHanceWaterMaterialsCommand(
    TEXT("RaftSim.RefreshColoradoHanceWaterMaterials"),
    TEXT("Regenerate only Colorado Hance river-local capture and live water "
         "materials/textures; do not rebuild or save the map."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleRefreshColoradoHanceWaterMaterials));

bool CaptureColoradoHanceWaterReview(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;
    bool bCaptured = false;
    const FString CaptureRoot = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            GetRepoRoot(),
            TEXT("docs/environment-captures/photoreal_river_previews/"
                 "landscape_candidates")));
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate :
         GetLandscapeImportCandidateSpecs())
    {
        if (Candidate.PreviewSpec.RiverId != TEXT("colorado_river"))
        {
            continue;
        }
        FString GuidePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate, TEXT("guide_seat_downstream"));
        FString RiverEyePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate, TEXT("river_eye_downstream"));
        FString RapidPath = GetLandscapeCandidateCaptureRelativePath(
            Candidate, TEXT("solver_rapid_river_eye_downstream"));
        const bool bGuide = CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CaptureRoot,
            GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_guide_seat_downstream"),
            TEXT("Colorado Hance transmitting-water guide-seat downstream"),
            true,
            OutSummary);
        const bool bRiverEye = CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CaptureRoot,
            RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_river_eye_downstream"),
            TEXT("Colorado Hance transmitting-water river-eye downstream"),
            true,
            OutSummary);
        const bool bRapid = CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CaptureRoot,
            RapidPath,
            TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"),
            TEXT("landscape_candidate_solver_rapid_river_eye_downstream"),
            TEXT("Colorado Hance transmitting-water rapid river-eye"),
            true,
            OutSummary);
        bCaptured = bGuide && bRiverEye && bRapid;
        break;
    }
    return bCaptured;
}

static void HandleCaptureColoradoHanceWaterReview(const TArray<FString>&)
{
    FString Summary;
    const bool bCaptured = CaptureColoradoHanceWaterReview(Summary);
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim.CaptureColoradoHanceWaterReview: succeeded=%d\n%s"),
        bCaptured ? 1 : 0,
        *Summary);
}

static FAutoConsoleCommand GCaptureColoradoHanceWaterReviewCommand(
    TEXT("RaftSim.CaptureColoradoHanceWaterReview"),
    TEXT("Capture the three saved Hance review cameras without rebuilding or "
         "saving the map."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCaptureColoradoHanceWaterReview));
} // namespace RaftSimEditorEnvironment
