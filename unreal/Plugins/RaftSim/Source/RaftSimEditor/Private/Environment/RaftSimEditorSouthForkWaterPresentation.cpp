#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialParameterCollection.h"

namespace RaftSimEditorEnvironment
{
namespace
{
UMaterialExpressionCollectionParameter* AddRaftWaterCollectionParameter(
    UMaterial* Material,
    UMaterialParameterCollection* Collection,
    FName Name,
    bool bScalar)
{
    UMaterialExpressionCollectionParameter* Expression =
        NewObject<UMaterialExpressionCollectionParameter>(Material);
    Expression->Collection = Collection;
    Expression->ParameterName = Name;
    Expression->ExpressionGUID = FGuid::NewGuid();
    const int32 ParameterIndex = bScalar
        ? Collection->ScalarParameters.IndexOfByPredicate(
              [Name](const FCollectionScalarParameter& Parameter)
              {
                  return Parameter.ParameterName == Name;
              })
        : Collection->VectorParameters.IndexOfByPredicate(
              [Name](const FCollectionVectorParameter& Parameter)
              {
                  return Parameter.ParameterName == Name;
              });
    if (ParameterIndex != INDEX_NONE)
    {
        Expression->ParameterId = bScalar
            ? Collection->ScalarParameters[ParameterIndex].Id
            : Collection->VectorParameters[ParameterIndex].Id;
    }
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}

UMaterial* LoadOrCreateSouthForkRaftTransmissionWaterParent(
    UMaterialInterface* SourceParent,
    FString& OutSummary)
{
    static const TCHAR* PackagePath = TEXT(
        "/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
        "M_RaftSim_SouthForkRaftTransmissionWater");
    static const TCHAR* ObjectName =
        TEXT("M_RaftSim_SouthForkRaftTransmissionWater");
    static const TCHAR* ObjectPath = TEXT(
        "/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
        "M_RaftSim_SouthForkRaftTransmissionWater."
        "M_RaftSim_SouthForkRaftTransmissionWater");

    UMaterial* SourceMaterial = SourceParent ? SourceParent->GetMaterial() : nullptr;
    UPackage* Package = CreatePackage(PackagePath);
    if (!SourceMaterial || !Package)
    {
        OutSummary += TEXT(
            "Could not load the South Fork source water for the raft-interior "
            "transmission parent.\n");
        return nullptr;
    }

    UMaterial* Material = LoadObject<UMaterial>(nullptr, ObjectPath);
    bool bNeedsSave = false;
    if (!Material)
    {
        // Keep the shared photoreal river parent untouched. South Fork owns a
        // derived copy because the moving raft aperture is a corridor/gameplay
        // presentation concern, not a suitable default for every river.
        Material = DuplicateObject<UMaterial>(SourceMaterial, Package, ObjectName);
        if (!Material)
        {
            OutSummary += TEXT(
                "Could not duplicate the South Fork raft-transmission water parent.\n");
            return nullptr;
        }
        Material->SetFlags(RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
        bNeedsSave = true;
    }

    bool bHasTransmissionGraph = false;
    bool bHasInteriorOpticalDepthGraph = false;
    UMaterialExpressionCustom* InteriorMaskExpression = nullptr;
    UMaterialExpressionSingleLayerWaterMaterialOutput* WaterOutput = nullptr;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (Expression &&
            Expression->Desc == TEXT("RaftSimRaftInteriorWaterTransmission"))
        {
            bHasTransmissionGraph = true;
            InteriorMaskExpression = Cast<UMaterialExpressionCustom>(
                Expression.Get());
        }
        if (Expression &&
            Expression->Desc == TEXT("RaftSimRaftInteriorWaterOpticalDepth"))
        {
            bHasInteriorOpticalDepthGraph = true;
        }
        if (!WaterOutput)
        {
            WaterOutput = Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(
                Expression.Get());
        }
    }
    // This helper is an explicit authoring/refresh path. Recompile an already
    // patched parent too, so a newly created platform DDC cannot reach a game
    // capture with Unreal's checkerboard fallback while its first shader map
    // is still pending.
    bNeedsSave = bNeedsSave || bHasTransmissionGraph;

    if (!bHasTransmissionGraph)
    {
        UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
        UMaterialExpression* OriginalOpacity =
            EditorData ? EditorData->Opacity.Expression : nullptr;
        UMaterialExpression* OriginalBehindWaterScale =
            WaterOutput ? WaterOutput->ColorScaleBehindWater.Expression : nullptr;
        UMaterialParameterCollection* Collection =
            LoadOrCreateRaftFoamOcclusionCollection(OutSummary);
        if (!EditorData || !OriginalOpacity || !OriginalBehindWaterScale ||
            !WaterOutput || !Collection)
        {
            OutSummary += TEXT(
                "The South Fork source water lacks an opacity, volume output, "
                "or raft presentation collection required for interior transmission.\n");
            return nullptr;
        }

        Material->Modify();
        UMaterialExpressionWorldPosition* WorldPosition =
            NewObject<UMaterialExpressionWorldPosition>(Material);
        WorldPosition->Desc = TEXT("RaftSimRaftInteriorWaterWorldPosition");
        WorldPosition->WorldPositionShaderOffset = WPT_ExcludeAllShaderOffsets;
        Material->GetExpressionCollection().AddExpression(WorldPosition);
        UMaterialExpressionCollectionParameter* TransmissionEnabled =
            AddRaftWaterCollectionParameter(
                Material,
                Collection,
                TEXT("RaftInteriorWaterTransmissionEnabled"),
                true);
        UMaterialExpressionCollectionParameter* TransmissionCenter =
            AddRaftWaterCollectionParameter(
                Material,
                Collection,
                TEXT("RaftInteriorWaterCenterAndHalfWidthCm"),
                false);
        UMaterialExpressionCollectionParameter* TransmissionForward =
            AddRaftWaterCollectionParameter(
                Material,
                Collection,
                TEXT("RaftInteriorWaterForwardAndHalfLengthCm"),
                false);

        UMaterialExpressionCustom* InteriorMask =
            NewObject<UMaterialExpressionCustom>(Material);
        InteriorMask->Desc = TEXT("RaftSimRaftInteriorWaterTransmission");
        InteriorMask->Description = TEXT(
            "Feathered raft-floor transmission aperture for Single Layer Water");
        InteriorMask->OutputType = CMOT_Float1;
        InteriorMask->Code = TEXT(
            "float2 Delta = WorldPosition.xy - CenterAndHalfWidth.xy;\n"
            "float2 Forward = normalize(ForwardAndHalfLength.xy + float2(1e-5, 0.0));\n"
            "float Along = abs(dot(Delta, Forward)) / max(ForwardAndHalfLength.w, 1.0);\n"
            "float Across = abs(dot(Delta, float2(-Forward.y, Forward.x))) / max(CenterAndHalfWidth.w, 1.0);\n"
            "float RoundedRectangle = pow(Along, 4.0) + pow(Across, 4.0);\n"
            "float InsideFloor = 1.0 - smoothstep(0.62, 1.0, RoundedRectangle);\n"
            "return InsideFloor * saturate(Enabled);");
        auto AddCustomInput = [InteriorMask](
            FName Name, UMaterialExpression* Expression)
        {
            FCustomInput Input;
            Input.InputName = Name;
            Input.Input.Expression = Expression;
            InteriorMask->Inputs.Add(Input);
        };
        AddCustomInput(TEXT("WorldPosition"), WorldPosition);
        AddCustomInput(TEXT("CenterAndHalfWidth"), TransmissionCenter);
        AddCustomInput(TEXT("ForwardAndHalfLength"), TransmissionForward);
        AddCustomInput(TEXT("Enabled"), TransmissionEnabled);
        Material->GetExpressionCollection().AddExpression(InteriorMask);
        InteriorMaskExpression = InteriorMask;

        UMaterialExpressionScalarParameter* InteriorOpacityScale =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        InteriorOpacityScale->ParameterName =
            TEXT("RaftInteriorSurfaceOpacityScale");
        InteriorOpacityScale->DefaultValue = 0.0f;
        InteriorOpacityScale->Group = TEXT("RaftSimRaftInteriorWater");
        Material->GetExpressionCollection().AddExpression(InteriorOpacityScale);
        UMaterialExpressionConstant* FullOpacityScale =
            NewObject<UMaterialExpressionConstant>(Material);
        FullOpacityScale->R = 1.0f;
        Material->GetExpressionCollection().AddExpression(FullOpacityScale);
        UMaterialExpressionLinearInterpolate* SpatialOpacityScale =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        SpatialOpacityScale->A.Expression = FullOpacityScale;
        SpatialOpacityScale->B.Expression = InteriorOpacityScale;
        SpatialOpacityScale->Alpha.Expression = InteriorMask;
        Material->GetExpressionCollection().AddExpression(SpatialOpacityScale);
        UMaterialExpressionMultiply* TransmittingOpacity =
            NewObject<UMaterialExpressionMultiply>(Material);
        TransmittingOpacity->A.Expression = OriginalOpacity;
        TransmittingOpacity->B.Expression = SpatialOpacityScale;
        Material->GetExpressionCollection().AddExpression(TransmittingOpacity);
        EditorData->Opacity.Connect(0, TransmittingOpacity);

        UMaterialExpressionVectorParameter* InteriorBehindWaterScale =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        InteriorBehindWaterScale->ParameterName =
            TEXT("RaftInteriorBehindWaterScale");
        InteriorBehindWaterScale->DefaultValue =
            FLinearColor(1.0f, 1.0f, 1.0f, 0.0f);
        InteriorBehindWaterScale->Group = TEXT("RaftSimRaftInteriorWater");
        Material->GetExpressionCollection().AddExpression(
            InteriorBehindWaterScale);
        UMaterialExpressionLinearInterpolate* SpatialBehindWaterScale =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        SpatialBehindWaterScale->A.Expression = OriginalBehindWaterScale;
        SpatialBehindWaterScale->B.Expression = InteriorBehindWaterScale;
        SpatialBehindWaterScale->Alpha.Expression = InteriorMask;
        Material->GetExpressionCollection().AddExpression(
            SpatialBehindWaterScale);
        WaterOutput->ColorScaleBehindWater.Expression =
            SpatialBehindWaterScale;
        bNeedsSave = true;
    }

    if (!bHasInteriorOpticalDepthGraph && InteriorMaskExpression && WaterOutput)
    {
        UMaterialExpression* OriginalScattering =
            WaterOutput->ScatteringCoefficients.Expression;
        UMaterialExpression* OriginalAbsorption =
            WaterOutput->AbsorptionCoefficients.Expression;
        if (!OriginalScattering || !OriginalAbsorption)
        {
            OutSummary += TEXT(
                "The South Fork water volume lacks scattering or absorption "
                "inputs required for raft-interior optical depth.\n");
            return nullptr;
        }
        // Surface opacity alone does not clear a Single Layer Water volume:
        // its scattering and absorption remain active between the river plane
        // and the submerged raft floor. Attenuate all three optical terms in
        // the same aperture so floor ribs, boots, and retained-water effects
        // remain visible without changing the surrounding river body.
        UMaterialExpressionScalarParameter* InteriorOpticalDepthScale =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        InteriorOpticalDepthScale->ParameterName =
            TEXT("RaftInteriorOpticalDepthScale");
        InteriorOpticalDepthScale->DefaultValue = 0.0f;
        InteriorOpticalDepthScale->Group = TEXT("RaftSimRaftInteriorWater");
        Material->GetExpressionCollection().AddExpression(
            InteriorOpticalDepthScale);
        UMaterialExpressionConstant* FullOpticalDepth =
            NewObject<UMaterialExpressionConstant>(Material);
        FullOpticalDepth->R = 1.0f;
        Material->GetExpressionCollection().AddExpression(FullOpticalDepth);
        UMaterialExpressionLinearInterpolate* SpatialOpticalDepth =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        SpatialOpticalDepth->Desc =
            TEXT("RaftSimRaftInteriorWaterOpticalDepth");
        SpatialOpticalDepth->A.Expression = FullOpticalDepth;
        SpatialOpticalDepth->B.Expression = InteriorOpticalDepthScale;
        SpatialOpticalDepth->Alpha.Expression = InteriorMaskExpression;
        Material->GetExpressionCollection().AddExpression(SpatialOpticalDepth);
        UMaterialExpressionMultiply* TransmittingScattering =
            NewObject<UMaterialExpressionMultiply>(Material);
        TransmittingScattering->A.Expression = OriginalScattering;
        TransmittingScattering->B.Expression = SpatialOpticalDepth;
        Material->GetExpressionCollection().AddExpression(
            TransmittingScattering);
        UMaterialExpressionMultiply* TransmittingAbsorption =
            NewObject<UMaterialExpressionMultiply>(Material);
        TransmittingAbsorption->A.Expression = OriginalAbsorption;
        TransmittingAbsorption->B.Expression = SpatialOpticalDepth;
        Material->GetExpressionCollection().AddExpression(
            TransmittingAbsorption);
        WaterOutput->ScatteringCoefficients.Expression =
            TransmittingScattering;
        WaterOutput->AbsorptionCoefficients.Expression =
            TransmittingAbsorption;
        bNeedsSave = true;
    }

    if (bNeedsSave)
    {
        Material->SetShadingModel(MSM_SingleLayerWater);
        Material->SetMaterialUsage(MATUSAGE_Water);
        Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
        Material->PostEditChange();
        Material->ForceRecompileForRendering();
        FAssetCompilingManager::Get().FinishAllCompilation();
        if (GShaderCompilingManager)
        {
            GShaderCompilingManager->FinishAllCompilation();
        }
        FMaterialResource* MaterialResource =
            Material->GetMaterialResource(GMaxRHIShaderPlatform);
        if (MaterialResource &&
            !MaterialResource->IsGameThreadShaderMapComplete())
        {
            MaterialResource->SubmitCompileJobs_GameThread(
                EShaderCompileJobPriority::High);
            MaterialResource->FinishCompilation();
            if (GShaderCompilingManager)
            {
                GShaderCompilingManager->ProcessAsyncResults(false, true);
            }
        }
        MaterialResource =
            Material->GetMaterialResource(GMaxRHIShaderPlatform);
        if (!MaterialResource ||
            Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
            !MaterialResource->GetCompileErrors().IsEmpty())
        {
            OutSummary += FString::Printf(
                TEXT("South Fork raft-transmission water shader validation "
                     "failed (resource=%d compiling_or_error=%d complete=%d "
                     "valid=%d errors=%d): %s\n"),
                MaterialResource ? 1 : 0,
                Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform)
                    ? 1
                    : 0,
                MaterialResource &&
                        MaterialResource->IsGameThreadShaderMapComplete()
                    ? 1
                    : 0,
                MaterialResource &&
                        MaterialResource->HasValidGameThreadShaderMap()
                    ? 1
                    : 0,
                MaterialResource
                    ? MaterialResource->GetCompileErrors().Num()
                    : -1,
                MaterialResource
                    ? *FString::Join(
                          MaterialResource->GetCompileErrors(), TEXT(" | "))
                    : TEXT("no platform material resource"));
            return nullptr;
        }
        Package->MarkPackageDirty();
        const FString Filename = FPackageName::LongPackageNameToFilename(
            PackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
        {
            OutSummary += TEXT(
                "Could not save the South Fork raft-transmission water parent.\n");
            return nullptr;
        }
    }
    return Material;
}
} // namespace

bool LoadSouthForkProductionWaterPresentation(
    UMaterialInterface*& InOutMaterial,
    FString& OutSummary)
{
    if (!InOutMaterial)
    {
        OutSummary += TEXT(
            "The production river-water parent is unavailable for South Fork calibration.\n");
        return false;
    }
    UMaterialInterface* Parent =
        LoadOrCreateSouthForkRaftTransmissionWaterParent(
            InOutMaterial, OutSummary);
    if (!Parent)
    {
        return false;
    }
    static const TCHAR* AssetName = TEXT("MI_RaftSim_SouthForkProductionWater");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "MI_RaftSim_SouthForkProductionWater");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "MI_RaftSim_SouthForkProductionWater."
             "MI_RaftSim_SouthForkProductionWater");
    UPackage* Package = CreatePackage(PackagePath);
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr, ObjectPath);
    if (!Instance && Package)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package, AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance || !Package)
    {
        OutSummary += TEXT(
            "Could not create the bounded South Fork production-water material instance.\n");
        return false;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(Parent);
    // The parent remains reusable for other rivers. South Fork's shallow
    // gravel bars need a narrower transmission range so a 2 m interpolated
    // solver-depth transition does not expose a bright polygon against the
    // deep channel while still retaining readable submerged geography.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ShallowWaterOpacity")), 0.76f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DeepWaterOpacity")), 0.82f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamWaterOpacity")), 0.91f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorSurfaceOpacityScale")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorOpticalDepthScale")), 0.0f);
    // The fixed environment captures do not retain the guide viewport's full
    // temporal reflection history. Calibrate the South Fork instance toward
    // the gray-green body colour and blue-sky response visible in the source
    // corridor instead of changing the shared parent or hydraulic channels.
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ShallowWaterColor")),
        FLinearColor(0.026f, 0.050f, 0.058f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DeepWaterColor")),
        FLinearColor(0.010f, 0.024f, 0.032f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ReflectedSkyColor")),
        FLinearColor(0.100f, 0.160f, 0.220f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterScattering")),
        FLinearColor(0.00018f, 0.00023f, 0.00028f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterAbsorption")),
        FLinearColor(0.0055f, 0.0044f, 0.0038f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RiverbedColorScale")),
        FLinearColor(0.22f, 0.23f, 0.23f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorBehindWaterScale")),
        FLinearColor(1.0f, 1.0f, 1.0f, 0.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicWhitewaterGain")), 0.30f);
    // Whitewater has one visual owner: the solver-conditioned masked foam
    // sheet. Leaving the same foam in this opaque Single Layer Water parent
    // double-composited it beneath the raised sheet and made aeration look
    // painted over raft tubes and crew. The underlying water keeps depth,
    // transmission, normals, and hydraulics; the dedicated sheet owns foam.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamIntensity")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamCoverageGain")), 0.82f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorBreakupGain")), 0.62f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorCoreGain")), 0.95f);
    // Fast, shallow Sierra water carries a broad distribution of short-wave
    // slopes, but it still retains coherent sky/shore reflection at grazing
    // angles. Keep a moderately rough surface rather than the previous matte
    // 0.38 response, and restore a bounded water-like Fresnel lobe without
    // inventing foam or changing solver-authored vertex channels.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterRoughness")), 0.24f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Specular")), 0.28f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FresnelSpecular")), 0.18f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionStrength")), 0.28f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmSurfaceColorVariation")), 0.14f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionFloor")), 0.68f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionVariation")), 0.32f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmRippleStrength")), 0.055f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowRippleStrength")), 0.075f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamRippleStrength")), 0.110f);
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
            "Could not save the bounded South Fork production-water material instance.\n");
        return false;
    }
    InOutMaterial = Instance;
    OutSummary += TEXT(
        "Using the project-owned South Fork water calibration with bounded "
        "shallow/deep transmission, a raft-floor optical aperture, and "
        "unchanged solver authority.\n");
    return true;
}

static void HandleRefreshSouthForkFoamOcclusionMaterials(
    const TArray<FString>&)
{
    FString Summary;
    UMaterialInterface* WaterMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
             "M_RaftSim_PhotorealRiverWater"));
    const bool bWaterReady = WaterMaterial &&
        LoadSouthForkProductionWaterPresentation(WaterMaterial, Summary);
    UMaterialInterface* FoamMaterial =
        LoadOrCreateLandscapeCandidateSolverFoamMaterial(Summary);
    UMaterialInterface* FloorMaterial =
        LoadOrCreateReadableRaftFloorMaterial(Summary);
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim South Fork material refresh water=%d foam=%d floor=%d\n%s"),
        bWaterReady ? 1 : 0,
        FoamMaterial ? 1 : 0,
        FloorMaterial ? 1 : 0,
        *Summary);
}

static FAutoConsoleCommand GRefreshSouthForkFoamOcclusionMaterialsCommand(
    TEXT("RaftSim.RefreshSouthForkFoamOcclusionMaterials"),
    TEXT("Refresh the South Fork water, foam, raft-floor, and exclusion materials."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleRefreshSouthForkFoamOcclusionMaterials));

} // namespace RaftSimEditorEnvironment
