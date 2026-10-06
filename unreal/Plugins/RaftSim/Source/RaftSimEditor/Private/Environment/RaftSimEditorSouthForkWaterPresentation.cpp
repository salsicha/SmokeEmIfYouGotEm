#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionPower.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSine.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTime.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialParameterCollection.h"

namespace RaftSimEditorEnvironment
{
namespace
{
static const TCHAR* kRaftLocalGpuFluidWpoCode = TEXT(
    "float2 stationaryP = UV * 3.0;\n"
    "float2 advectedP = stationaryP - FlowDisplacement.xy;\n"
    "float halfWindowCm = max(WindowMeters * 50.0, 1000.0);\n"
    "float localWindow = 1.0 - smoothstep(halfWindowCm * 0.82, halfWindowCm, distance(WorldPosition.xy, RaftCenter.xy));\n"
    // Speed alone is not whitewater. The old speed term activated this
    // multi-band displacement across every ordinary current, producing the
    // broad pale chevrons/bars seen in the approach pool. Vertex foam already
    // contains solver slope and hydraulic-feature energy, so it confines 3D
    // boiling to water that is actually working.
    // Foam can persist in ankle-deep margins after a crest passes. It is not
    // permission to lift that shallow margin into an airborne shore blob.
    "float depthGate = smoothstep(0.10, 0.60, max(DepthNorm, 0.0) * 4.0);\n"
    "float rapid = smoothstep(0.025, 0.42, Foam) * saturate(Wet) * depthGate * localWindow;\n"
    // Rotated value-noise fields replace the former sum of long sine phase
    // lines. Those phase lines were mathematically continuous but still had
    // infinite parallel crests, which reflected as horizontal and vertical
    // bars from a guide-eye camera. Two non-commensurate rotations produce
    // compact, irregular upwellings with no privileged river/grid axis.
    "float2 anchorA = float2(0.731 * stationaryP.x + 0.682 * stationaryP.y, -0.682 * stationaryP.x + 0.731 * stationaryP.y) * 0.205;\n"
    "float2 anchorAi = floor(anchorA);\n"
    "float2 anchorAf = frac(anchorA);\n"
    "float2 anchorAs = anchorAf * anchorAf * (3.0 - 2.0 * anchorAf);\n"
    "float anchorA00 = frac(sin(dot(anchorAi + float2(0.0, 0.0), float2(127.1, 311.7))) * 43758.5453);\n"
    "float anchorA10 = frac(sin(dot(anchorAi + float2(1.0, 0.0), float2(127.1, 311.7))) * 43758.5453);\n"
    "float anchorA01 = frac(sin(dot(anchorAi + float2(0.0, 1.0), float2(127.1, 311.7))) * 43758.5453);\n"
    "float anchorA11 = frac(sin(dot(anchorAi + float2(1.0, 1.0), float2(127.1, 311.7))) * 43758.5453);\n"
    "float anchorNoiseA = lerp(lerp(anchorA00, anchorA10, anchorAs.x), lerp(anchorA01, anchorA11, anchorAs.x), anchorAs.y);\n"
    "float2 anchorB = float2(-0.417 * stationaryP.x + 0.909 * stationaryP.y, -0.909 * stationaryP.x - 0.417 * stationaryP.y) * 0.397 + float2(17.31, -9.17);\n"
    "float2 anchorBi = floor(anchorB);\n"
    "float2 anchorBf = frac(anchorB);\n"
    "float2 anchorBs = anchorBf * anchorBf * (3.0 - 2.0 * anchorBf);\n"
    "float anchorB00 = frac(sin(dot(anchorBi + float2(0.0, 0.0), float2(269.5, 183.3))) * 24634.6345);\n"
    "float anchorB10 = frac(sin(dot(anchorBi + float2(1.0, 0.0), float2(269.5, 183.3))) * 24634.6345);\n"
    "float anchorB01 = frac(sin(dot(anchorBi + float2(0.0, 1.0), float2(269.5, 183.3))) * 24634.6345);\n"
    "float anchorB11 = frac(sin(dot(anchorBi + float2(1.0, 1.0), float2(269.5, 183.3))) * 24634.6345);\n"
    "float anchorNoiseB = lerp(lerp(anchorB00, anchorB10, anchorBs.x), lerp(anchorB01, anchorB11, anchorBs.x), anchorBs.y);\n"
    "float anchorNoise = saturate(0.64 * anchorNoiseA + 0.36 * anchorNoiseB);\n"
    "float crestCluster = pow(saturate((anchorNoise - 0.43) * 1.82), 2.6);\n"
    "float anchorTrough = pow(saturate((0.46 - anchorNoise) * 1.95), 2.2);\n"
    "float crestBreath = 0.90 + 0.10 * sin(WaveClock * 0.71 + anchorNoiseB * 6.2831853);\n"
    "float2 boilA = float2(0.847 * advectedP.x - 0.532 * advectedP.y, 0.532 * advectedP.x + 0.847 * advectedP.y) * 0.315 + float2(-4.11, 13.73);\n"
    "float2 boilAi = floor(boilA);\n"
    "float2 boilAf = frac(boilA);\n"
    "float2 boilAs = boilAf * boilAf * (3.0 - 2.0 * boilAf);\n"
    "float boilA00 = frac(sin(dot(boilAi + float2(0.0, 0.0), float2(157.7, 113.5))) * 31973.417);\n"
    "float boilA10 = frac(sin(dot(boilAi + float2(1.0, 0.0), float2(157.7, 113.5))) * 31973.417);\n"
    "float boilA01 = frac(sin(dot(boilAi + float2(0.0, 1.0), float2(157.7, 113.5))) * 31973.417);\n"
    "float boilA11 = frac(sin(dot(boilAi + float2(1.0, 1.0), float2(157.7, 113.5))) * 31973.417);\n"
    "float boilNoiseA = lerp(lerp(boilA00, boilA10, boilAs.x), lerp(boilA01, boilA11, boilAs.x), boilAs.y);\n"
    "float2 boilB = float2(-0.615 * advectedP.x - 0.789 * advectedP.y, 0.789 * advectedP.x - 0.615 * advectedP.y) * 0.611 + float2(8.37, 2.91);\n"
    "float2 boilBi = floor(boilB);\n"
    "float2 boilBf = frac(boilB);\n"
    "float2 boilBs = boilBf * boilBf * (3.0 - 2.0 * boilBf);\n"
    "float boilB00 = frac(sin(dot(boilBi + float2(0.0, 0.0), float2(101.3, 271.9))) * 41719.213);\n"
    "float boilB10 = frac(sin(dot(boilBi + float2(1.0, 0.0), float2(101.3, 271.9))) * 41719.213);\n"
    "float boilB01 = frac(sin(dot(boilBi + float2(0.0, 1.0), float2(101.3, 271.9))) * 41719.213);\n"
    "float boilB11 = frac(sin(dot(boilBi + float2(1.0, 1.0), float2(101.3, 271.9))) * 41719.213);\n"
    "float boilNoiseB = lerp(lerp(boilB00, boilB10, boilBs.x), lerp(boilB01, boilB11, boilBs.x), boilBs.y);\n"
    // Noise is advected, so multiplying it by elapsed time makes its temporal
    // derivative grow for the entire run. Use bounded phase offsets instead:
    // the boils must not accelerate into flicker as a session gets older.
    "float boilPhase = WaveClock * 1.70 + 2.90 * boilNoiseB + 6.2831853 * boilNoiseA;\n"
    "float boilPulse = sin(boilPhase);\n"
    "float splashPulse = pow(saturate(0.5 + 0.5 * sin(boilPhase * 1.73 + anchorNoiseA * 4.7)), 6.0);\n"
    // Full-scale relief remains bounded and foam-gated. Solver/obstacle
    // geometry owns coherent standing-wave crests; this layer supplies only
    // compact crest clusters, recirculating boils, and transient splashes.
    "float anchoredRelief = crestBreath * (0.72 * crestCluster - 0.20 * anchorTrough);\n"
    "float carriedBoils = 0.25 * (boilNoiseA - 0.5) * (0.45 + boilNoiseB) + 0.17 * boilPulse * (0.30 + 0.70 * boilNoiseB) + 0.20 * splashPulse;\n"
    "float displacementM = clamp(rapid * (anchoredRelief + carriedBoils), -0.50, 0.78);\n"
    "return float3(0.0, 0.0, displacementM * 100.0 * Strength);");

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
        "M_RaftSim_SouthForkRaftTransmissionWaterV4");
    static const TCHAR* ObjectName =
        TEXT("M_RaftSim_SouthForkRaftTransmissionWaterV4");
    static const TCHAR* ObjectPath = TEXT(
        "/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
        "M_RaftSim_SouthForkRaftTransmissionWaterV4."
        "M_RaftSim_SouthForkRaftTransmissionWaterV4");

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
    bool bHasBankCoverageGraph = false;
    bool bHasBankOpticalCoverageGraph = false;
    bool bHasOpticalDepthResponseGraph = false;
    UMaterialExpressionCustom* InteriorMaskExpression = nullptr;
    UMaterialExpression* BankCoverageScaleExpression = nullptr;
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
        if (Expression &&
            Expression->Desc == TEXT("RaftSimLiveVolumeBankCoverage"))
        {
            bHasBankCoverageGraph = true;
            BankCoverageScaleExpression = Expression.Get();
        }
        if (Expression &&
            Expression->Desc == TEXT("RaftSimLiveVolumeBankOpticalCoverage"))
        {
            bHasBankOpticalCoverageGraph = true;
        }
        if (Expression &&
            Expression->Desc == TEXT("RaftSimOpticalDepthResponse"))
        {
            bHasOpticalDepthResponseGraph = true;
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

    if (!bHasOpticalDepthResponseGraph)
    {
        // Solver depth is packed as depth / 4 m in vertex green. Feeding that
        // value directly into a linear shallow/deep blend leaves a one-metre
        // bank shelf only 25% attenuated and produces a broad pale rail in
        // guide-eye views. Remap only the material response with a parameterized
        // power curve. The default exponent of one is identity; clear-water
        // rivers opt into a sub-linear exponent so optical density accumulates
        // rapidly after the genuinely shallow edge while retaining bed detail
        // in the first few centimetres. Hydraulic depth and every gameplay
        // consumer remain untouched.
        UMaterialExpressionComponentMask* SolverDepthMask = nullptr;
        for (const TObjectPtr<UMaterialExpression>& Expression :
             Material->GetExpressionCollection().Expressions)
        {
            UMaterialExpressionComponentMask* Candidate =
                Cast<UMaterialExpressionComponentMask>(Expression.Get());
            if (!Candidate || Candidate->R || !Candidate->G || Candidate->B ||
                Candidate->A || Candidate->Input.OutputIndex != 0 ||
                !Cast<UMaterialExpressionVertexColor>(
                    Candidate->Input.Expression))
            {
                continue;
            }
            SolverDepthMask = Candidate;
            break;
        }
        if (!SolverDepthMask)
        {
            OutSummary += TEXT(
                "The raft-transmission water lacks the solver depth channel "
                "required for nonlinear optical attenuation.\n");
            return nullptr;
        }

        // The colour/opacity lerps no longer key on the raw mask: the base
        // graph wraps it in the live-level EffectiveDepthMask (a Saturate
        // over DepthMask + delta) so level-tracking tiles shade by their
        // real depth. Interpose the power response on whatever expression
        // the depth blends actually share — the raw mask on legacy parents,
        // the effective mask on current ones. Matching only the raw mask
        // found 0 of 2 blends and silently aborted every V4 regeneration
        // after the effective mask landed (discovered when the V4 asset
        // vanished from the working tree, 2026-09-02).
        const auto UsesSolverDepth =
            [SolverDepthMask](UMaterialExpression* Alpha) -> bool
        {
            if (Alpha == SolverDepthMask)
            {
                return true;
            }
            if (UMaterialExpressionSaturate* Saturated =
                    Cast<UMaterialExpressionSaturate>(Alpha))
            {
                if (UMaterialExpressionAdd* Sum = Cast<UMaterialExpressionAdd>(
                        Saturated->Input.Expression))
                {
                    return Sum->A.Expression == SolverDepthMask ||
                        Sum->B.Expression == SolverDepthMask;
                }
            }
            return false;
        };
        UMaterialExpression* SharedDepthAlpha = nullptr;
        for (const TObjectPtr<UMaterialExpression>& Expression :
             Material->GetExpressionCollection().Expressions)
        {
            UMaterialExpressionLinearInterpolate* DepthBlend =
                Cast<UMaterialExpressionLinearInterpolate>(Expression.Get());
            if (DepthBlend && UsesSolverDepth(DepthBlend->Alpha.Expression))
            {
                SharedDepthAlpha = DepthBlend->Alpha.Expression;
                break;
            }
        }

        Material->Modify();
        UMaterialExpressionScalarParameter* ResponseExponent =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        ResponseExponent->ParameterName =
            TEXT("OpticalDepthResponseExponent");
        ResponseExponent->DefaultValue = 1.0f;
        ResponseExponent->Group = TEXT("RaftSimOpticalDepth");
        Material->GetExpressionCollection().AddExpression(ResponseExponent);
        UMaterialExpressionPower* OpticalDepthResponse =
            NewObject<UMaterialExpressionPower>(Material);
        OpticalDepthResponse->Desc = TEXT("RaftSimOpticalDepthResponse");
        OpticalDepthResponse->Base.Expression =
            SharedDepthAlpha ? SharedDepthAlpha : SolverDepthMask;
        OpticalDepthResponse->Exponent.Expression = ResponseExponent;
        Material->GetExpressionCollection().AddExpression(
            OpticalDepthResponse);

        int32 RewiredDepthBlends = 0;
        for (const TObjectPtr<UMaterialExpression>& Expression :
             Material->GetExpressionCollection().Expressions)
        {
            UMaterialExpressionLinearInterpolate* DepthBlend =
                Cast<UMaterialExpressionLinearInterpolate>(Expression.Get());
            if (!DepthBlend || DepthBlend->Alpha.Expression == nullptr ||
                DepthBlend->Alpha.Expression !=
                    OpticalDepthResponse->Base.Expression)
            {
                continue;
            }
            DepthBlend->Alpha.Expression = OpticalDepthResponse;
            ++RewiredDepthBlends;
        }
        if (RewiredDepthBlends < 2)
        {
            OutSummary += FString::Printf(
                TEXT("The raft-transmission water exposed only %d of the two "
                     "required depth colour/opacity blends.\n"),
                RewiredDepthBlends);
            return nullptr;
        }
        bNeedsSave = true;
    }

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
            OutSummary += FString::Printf(
                TEXT("The South Fork source water lacks an opacity, volume ")
                TEXT("output, or raft presentation collection required for ")
                TEXT("interior transmission (editor_data=%d opacity=%d ")
                TEXT("behind_scale=%d water_output=%d collection=%d).\n"),
                EditorData != nullptr,
                OriginalOpacity != nullptr,
                OriginalBehindWaterScale != nullptr,
                WaterOutput != nullptr,
                Collection != nullptr);
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

    if (!bHasBankCoverageGraph)
    {
        UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
        UMaterialExpression* OriginalOpacity =
            EditorData ? EditorData->Opacity.Expression : nullptr;
        if (!EditorData || !OriginalOpacity)
        {
            OutSummary += TEXT(
                "The raft-transmission water lacks an opacity graph required "
                "for live wet-cell bank coverage.\n");
            return nullptr;
        }

        // The procedural volume core already writes a smooth station/lateral
        // wet-cell coverage into vertex alpha. V1 ignored that channel and
        // ended the opaque Single Layer Water body on a hard rectangular cell
        // edge. Consume the same coverage here. The scalar floor defaults to
        // zero but remains explicit for bounded diagnostics.
        Material->Modify();
        UMaterialExpressionVertexColor* VertexColor =
            NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);
        UMaterialExpressionComponentMask* Coverage =
            NewObject<UMaterialExpressionComponentMask>(Material);
        Coverage->Input.Expression = VertexColor;
        Coverage->Input.OutputIndex = 4;
        Coverage->R = true;
        Coverage->G = false;
        Coverage->B = false;
        Coverage->A = false;
        Material->GetExpressionCollection().AddExpression(Coverage);
        UMaterialExpressionScalarParameter* CoverageFloor =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        CoverageFloor->ParameterName = TEXT("LiveVolumeBankCoverageFloor");
        CoverageFloor->DefaultValue = 0.0f;
        CoverageFloor->Group = TEXT("RaftSimLiveVolumeBankCoverage");
        Material->GetExpressionCollection().AddExpression(CoverageFloor);
        UMaterialExpressionConstant* FullCoverage =
            NewObject<UMaterialExpressionConstant>(Material);
        FullCoverage->R = 1.0f;
        Material->GetExpressionCollection().AddExpression(FullCoverage);
        UMaterialExpressionLinearInterpolate* CoverageScale =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        CoverageScale->Desc = TEXT("RaftSimLiveVolumeBankCoverage");
        CoverageScale->A.Expression = CoverageFloor;
        CoverageScale->B.Expression = FullCoverage;
        CoverageScale->Alpha.Expression = Coverage;
        Material->GetExpressionCollection().AddExpression(CoverageScale);
        BankCoverageScaleExpression = CoverageScale;
        UMaterialExpressionMultiply* FeatheredOpacity =
            NewObject<UMaterialExpressionMultiply>(Material);
        FeatheredOpacity->A.Expression = OriginalOpacity;
        FeatheredOpacity->B.Expression = CoverageScale;
        Material->GetExpressionCollection().AddExpression(FeatheredOpacity);
        EditorData->Opacity.Connect(0, FeatheredOpacity);
        bNeedsSave = true;
    }

    if (!bHasBankOpticalCoverageGraph && BankCoverageScaleExpression &&
        WaterOutput)
    {
        UMaterialExpression* OriginalScattering =
            WaterOutput->ScatteringCoefficients.Expression;
        UMaterialExpression* OriginalAbsorption =
            WaterOutput->AbsorptionCoefficients.Expression;
        UMaterialExpression* OriginalBehindWaterScale =
            WaterOutput->ColorScaleBehindWater.Expression;
        if (!OriginalScattering || !OriginalAbsorption ||
            !OriginalBehindWaterScale)
        {
            OutSummary += TEXT(
                "The raft-transmission water lacks optical inputs required "
                "for complete live wet-cell bank coverage.\n");
            return nullptr;
        }

        // Single Layer Water evaluates its optical volume independently of
        // ordinary surface opacity. V1 faded the surface at the sampled bank,
        // but scattering, absorption, and behind-water colour remained active
        // and left a pale rectangular shallow-water rail. Reuse the exact same
        // solver-owned vertex coverage for every optical term: coefficients
        // fade to zero and behind-water colour returns to identity at the dry
        // edge. This is a material-only presentation change; it cannot widen
        // the wet topology or alter water samples, collision, or raft forces.
        Material->Modify();
        UMaterialExpressionMultiply* CoveredScattering =
            NewObject<UMaterialExpressionMultiply>(Material);
        CoveredScattering->Desc =
            TEXT("RaftSimLiveVolumeBankOpticalCoverage");
        CoveredScattering->A.Expression = OriginalScattering;
        CoveredScattering->B.Expression = BankCoverageScaleExpression;
        Material->GetExpressionCollection().AddExpression(CoveredScattering);
        UMaterialExpressionMultiply* CoveredAbsorption =
            NewObject<UMaterialExpressionMultiply>(Material);
        CoveredAbsorption->A.Expression = OriginalAbsorption;
        CoveredAbsorption->B.Expression = BankCoverageScaleExpression;
        Material->GetExpressionCollection().AddExpression(CoveredAbsorption);
        UMaterialExpressionConstant3Vector* IdentityBehindWater =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        IdentityBehindWater->Constant =
            FLinearColor(1.0f, 1.0f, 1.0f, 0.0f);
        Material->GetExpressionCollection().AddExpression(IdentityBehindWater);
        UMaterialExpressionLinearInterpolate* CoveredBehindWaterScale =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        CoveredBehindWaterScale->A.Expression = IdentityBehindWater;
        CoveredBehindWaterScale->B.Expression = OriginalBehindWaterScale;
        CoveredBehindWaterScale->Alpha.Expression =
            BankCoverageScaleExpression;
        Material->GetExpressionCollection().AddExpression(
            CoveredBehindWaterScale);
        WaterOutput->ScatteringCoefficients.Expression = CoveredScattering;
        WaterOutput->AbsorptionCoefficients.Expression = CoveredAbsorption;
        WaterOutput->ColorScaleBehindWater.Expression =
            CoveredBehindWaterScale;
        bNeedsSave = true;
    }

    bool bHasTravelingWaveOffset = false;
    bool bHasTravelingWaveStrengthGate = false;
    bool bHasRaftLocalGpuFluid = false;
    bool bHasLiveLevelSink = false;
    UMaterialExpression* TravelingWaveOffsetExpression = nullptr;
    for (UMaterialExpression* Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (Expression &&
            Expression->Desc == TEXT("RaftSimTravelingBakeWaveWPO"))
        {
            bHasTravelingWaveOffset = true;
            TravelingWaveOffsetExpression = Expression;
        }
        if (Expression &&
            Expression->Desc ==
                TEXT("RaftSimTravelingBakeWaveWPOStrengthGate"))
        {
            bHasTravelingWaveStrengthGate = true;
        }
        if (Expression &&
            (Expression->Desc == TEXT("RaftSimRaftLocalGpuFluidWPOV2") ||
             Expression->Desc == TEXT("RaftSimRaftLocalGpuFluidWPOV3") ||
             Expression->Desc == TEXT("RaftSimRaftLocalGpuFluidWPOV4") ||
             Expression->Desc == TEXT("RaftSimRaftLocalGpuFluidWPOV5")))
        {
            bHasRaftLocalGpuFluid = true;
            if (UMaterialExpressionCustom* ExistingFluid =
                    Cast<UMaterialExpressionCustom>(Expression))
            {
                ExistingFluid->Modify();
                ExistingFluid->Desc = TEXT("RaftSimRaftLocalGpuFluidWPOV5");
                ExistingFluid->Description = TEXT(
                    "Axis-free cellular crest clusters and current-carried boils");
                ExistingFluid->Code = kRaftLocalGpuFluidWpoCode;
                if (!ExistingFluid->Inputs.ContainsByPredicate([](const FCustomInput& Input)
                    { return Input.InputName == TEXT("DepthNorm"); }))
                {
                    const FCustomInput* FoamInput = ExistingFluid->Inputs.FindByPredicate(
                        [](const FCustomInput& Input) { return Input.InputName == TEXT("Foam"); });
                    if (FoamInput && FoamInput->Input.Expression)
                    {
                        FCustomInput DepthInput;
                        DepthInput.InputName = TEXT("DepthNorm");
                        DepthInput.Input.Connect(2, FoamInput->Input.Expression);
                        ExistingFluid->Inputs.Add(DepthInput);
                    }
                }
                bNeedsSave = true;
            }
        }
        if (Expression &&
            Expression->Desc == TEXT("RaftSimLiveLevelSinkWPO"))
        {
            bHasLiveLevelSink = true;
        }
    }
    if (!bHasTravelingWaveOffset)
    {
        // The band meshes bake a deterministic ripple/standing-wave layer
        // into their geometry (RaftSimEditorSouthForkFullReach.cpp:
        // Disp = 0.018*sin(A) + E*(0.16*sin(A) + 0.09*sin(B)), with
        // A = Station*0.19 + Lateral*0.61, B = Station*0.071 - Lateral*0.37,
        // E = clamp(VC.R*0.72 + VC.B*0.48), and UV authored at Station/3,
        // Lateral/3). Static geometry is why four playtests reported "the
        // surface isn't flowing" no matter what the normal layers did.
        // This WPO reconstructs the identical field from UV and vertex
        // colour, subtracts the static bake, and re-adds it time-phased —
        // the same waves, now travelling downstream. No mesh rebuild.
        Material->Modify();
        UMaterialExpressionTextureCoordinate* RawUv =
            NewObject<UMaterialExpressionTextureCoordinate>(Material);
        Material->GetExpressionCollection().AddExpression(RawUv);
        const auto AddExpr = [Material](UMaterialExpression* E)
        {
            Material->GetExpressionCollection().AddExpression(E);
            return E;
        };
        const auto MaskChannel = [&](UMaterialExpression* In, bool bR, bool bG)
        {
            UMaterialExpressionComponentMask* M =
                NewObject<UMaterialExpressionComponentMask>(Material);
            M->Input.Expression = In;
            M->R = bR; M->G = bG; M->B = false; M->A = false;
            AddExpr(M);
            return static_cast<UMaterialExpression*>(M);
        };
        const auto ScaleBy = [&](UMaterialExpression* In, float K)
        {
            UMaterialExpressionConstant* C =
                NewObject<UMaterialExpressionConstant>(Material);
            C->R = K;
            AddExpr(C);
            UMaterialExpressionMultiply* M =
                NewObject<UMaterialExpressionMultiply>(Material);
            M->A.Expression = In;
            M->B.Expression = C;
            AddExpr(M);
            return static_cast<UMaterialExpression*>(M);
        };
        const auto AddPair = [&](UMaterialExpression* A, UMaterialExpression* B)
        {
            UMaterialExpressionAdd* S = NewObject<UMaterialExpressionAdd>(Material);
            S->A.Expression = A;
            S->B.Expression = B;
            AddExpr(S);
            return static_cast<UMaterialExpression*>(S);
        };
        const auto SubtractPair =
            [&](UMaterialExpression* A, UMaterialExpression* B)
        {
            UMaterialExpressionSubtract* S =
                NewObject<UMaterialExpressionSubtract>(Material);
            S->A.Expression = A;
            S->B.Expression = B;
            AddExpr(S);
            return static_cast<UMaterialExpression*>(S);
        };
        const auto SineOf = [&](UMaterialExpression* In)
        {
            UMaterialExpressionSine* S = NewObject<UMaterialExpressionSine>(Material);
            S->Input.Expression = In;
            // The engine Sine node evaluates sin(2*pi*Input/Period); the
            // baked phases are radians, so Period = 2*pi passes through.
            S->Period = 6.2831853f;
            AddExpr(S);
            return static_cast<UMaterialExpression*>(S);
        };
        UMaterialExpression* StationM = ScaleBy(MaskChannel(RawUv, true, false), 3.0f);
        UMaterialExpression* LateralM = ScaleBy(MaskChannel(RawUv, false, true), 3.0f);
        UMaterialExpressionVertexColor* WpoVertexColor =
            NewObject<UMaterialExpressionVertexColor>(Material);
        AddExpr(WpoVertexColor);
        UMaterialExpressionComponentMask* EnergyR =
            NewObject<UMaterialExpressionComponentMask>(Material);
        EnergyR->Input.Expression = WpoVertexColor;
        EnergyR->R = true; EnergyR->G = false; EnergyR->B = false; EnergyR->A = false;
        AddExpr(EnergyR);
        UMaterialExpressionComponentMask* EnergyB =
            NewObject<UMaterialExpressionComponentMask>(Material);
        EnergyB->Input.Expression = WpoVertexColor;
        EnergyB->R = false; EnergyB->G = false; EnergyB->B = true; EnergyB->A = false;
        AddExpr(EnergyB);
        UMaterialExpressionClamp* HydraulicEnergy =
            NewObject<UMaterialExpressionClamp>(Material);
        HydraulicEnergy->Input.Expression = AddPair(
            ScaleBy(EnergyR, 0.72f), ScaleBy(EnergyB, 0.48f));
        HydraulicEnergy->MinDefault = 0.0f;
        HydraulicEnergy->MaxDefault = 1.0f;
        AddExpr(HydraulicEnergy);
        UMaterialExpression* PhaseA0 = AddPair(
            ScaleBy(StationM, 0.19f), ScaleBy(LateralM, 0.61f));
        UMaterialExpression* PhaseB0 = SubtractPair(
            ScaleBy(StationM, 0.071f), ScaleBy(LateralM, 0.37f));
        // Flow-warped clock instead of raw engine time: the runtime pushes an
        // accumulated (speed-scaled) clock through the shared collection so
        // the waves speed up entering rapids and the physics-side phases stay
        // paired. Falls back to engine time if the collection is unavailable.
        UMaterialExpression* WaveTime = nullptr;
        if (UMaterialParameterCollection* WaveClockCollection =
                LoadOrCreateRaftFoamOcclusionCollection(OutSummary))
        {
            WaveTime = AddRaftWaterCollectionParameter(
                Material, WaveClockCollection,
                TEXT("RaftSimWaveClockSeconds"), true);
        }
        if (!WaveTime)
        {
            UMaterialExpressionTime* FallbackTime =
                NewObject<UMaterialExpressionTime>(Material);
            AddExpr(FallbackTime);
            WaveTime = FallbackTime;
        }
        UMaterialExpression* PhaseA1 = SubtractPair(
            PhaseA0, ScaleBy(WaveTime, 0.90f));
        UMaterialExpression* PhaseB1 = SubtractPair(
            PhaseB0, ScaleBy(WaveTime, 0.55f));
        const auto Displacement =
            [&](UMaterialExpression* A, UMaterialExpression* B, float BaseAmp,
                float EnergyAmpScale)
        {
            UMaterialExpression* Hydraulic = AddPair(
                ScaleBy(SineOf(A), 0.16f * EnergyAmpScale),
                ScaleBy(SineOf(B), 0.09f * EnergyAmpScale));
            UMaterialExpressionMultiply* Gated =
                NewObject<UMaterialExpressionMultiply>(Material);
            Gated->A.Expression = Hydraulic;
            Gated->B.Expression = HydraulicEnergy;
            AddExpr(Gated);
            return AddPair(ScaleBy(SineOf(A), BaseAmp), Gated);
        };
        // The static bake (0.018 base, full energetic amplitude) always
        // cancels exactly; the moving replacement carries a stronger calm
        // base (+/-3 cm pools, matched by the physics-side coupling) and a
        // FULL energetic amplitude (was halved 2026-08-14..16 while the
        // physics could not reconstruct the term; the support sampler now
        // carries the identical energetic sines, so both sides scale
        // together — see RaftSimWaterRuntimeAdapter). High-aeration zones
        // (rapids, boulder wakes) roll ~0.2 m crests the hull rides.
        UMaterialExpression* DeltaMeters = SubtractPair(
            Displacement(PhaseA1, PhaseB1, 0.030f, 1.0f),
            Displacement(PhaseA0, PhaseB0, 0.018f, 1.0f));
        UMaterialExpression* DeltaCm = ScaleBy(DeltaMeters, 100.0f);
        UMaterialExpressionConstant3Vector* UpAxis =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        UpAxis->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 0.0f);
        AddExpr(UpAxis);
        UMaterialExpressionMultiply* Offset =
            NewObject<UMaterialExpressionMultiply>(Material);
        Offset->Desc = TEXT("RaftSimTravelingBakeWaveWPO");
        Offset->A.Expression = UpAxis;
        Offset->B.Expression = DeltaCm;
        AddExpr(Offset);
        TravelingWaveOffsetExpression = Offset;
        if (UMaterialEditorOnlyData* WpoEditorData = Material->GetEditorOnlyData())
        {
            WpoEditorData->WorldPositionOffset.Connect(0, Offset);
            bNeedsSave = true;
        }
    }

    if (TravelingWaveOffsetExpression && !bHasTravelingWaveStrengthGate)
    {
        // The same parent serves the static editor-review band and the live
        // solver carrier. The latter already owns physical displacement; let
        // its instance disable this legacy infinite sine train without
        // deleting the authored-review behavior from the parent.
        UMaterialExpressionScalarParameter* Strength =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Strength->ParameterName = TEXT("SouthForkTravelingWaveWPOStrength");
        Strength->DefaultValue = 1.0f;
        Strength->Group = TEXT("RaftSimSouthForkWaterMotion");
        Material->GetExpressionCollection().AddExpression(Strength);
        UMaterialExpressionMultiply* GatedOffset =
            NewObject<UMaterialExpressionMultiply>(Material);
        GatedOffset->Desc =
            TEXT("RaftSimTravelingBakeWaveWPOStrengthGate");
        GatedOffset->A.Expression = TravelingWaveOffsetExpression;
        GatedOffset->B.Expression = Strength;
        Material->GetExpressionCollection().AddExpression(GatedOffset);
        if (UMaterialEditorOnlyData* WpoEditorData = Material->GetEditorOnlyData())
        {
            WpoEditorData->WorldPositionOffset.Connect(0, GatedOffset);
            bNeedsSave = true;
        }
    }

    if (!bHasRaftLocalGpuFluid)
    {
        // A bounded GPU heightfield deforms the SAME solver-owned carrier.
        // UV0 is river station/lateral space and the displacement integral is
        // measured from the local solver current, so the structure advects
        // with a drifting raft. World position and raft centre confine the
        // expensive multi-band field to a 100 m window. Vertex colour gates
        // its sharp crests and recirculating boils to wet, aerated rapid water.
        Material->Modify();
        UMaterialParameterCollection* FlowCollection =
            LoadOrCreateRaftFoamOcclusionCollection(OutSummary);
        if (!FlowCollection)
        {
            OutSummary += TEXT(
                "Could not add current-advected 3D turbulence to the South "
                "Fork water parent.\n");
            return nullptr;
        }

        UMaterialExpressionTextureCoordinate* TurbulenceUv =
            NewObject<UMaterialExpressionTextureCoordinate>(Material);
        Material->GetExpressionCollection().AddExpression(TurbulenceUv);
        UMaterialExpressionVertexColor* TurbulenceVertexColor =
            NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(TurbulenceVertexColor);
        UMaterialExpressionCollectionParameter* FlowDisplacement =
            AddRaftWaterCollectionParameter(
                Material, FlowCollection,
                TEXT("RaftSimFoamAdvectionMeters"), false);
        UMaterialExpressionCollectionParameter* WaveClock =
            AddRaftWaterCollectionParameter(
                Material, FlowCollection,
                TEXT("RaftSimWaveClockSeconds"), true);
        UMaterialExpressionCollectionParameter* RaftCenter =
            AddRaftWaterCollectionParameter(
                Material, FlowCollection,
                TEXT("RaftFoamExclusionCenterAndHalfWidthCm"), false);
        UMaterialExpressionWorldPosition* FluidWorldPosition =
            NewObject<UMaterialExpressionWorldPosition>(Material);
        Material->GetExpressionCollection().AddExpression(FluidWorldPosition);
        UMaterialExpressionScalarParameter* TurbulenceStrength =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        TurbulenceStrength->ParameterName =
            TEXT("RaftSimLocalFluidWPOStrength");
        TurbulenceStrength->DefaultValue = 0.0f;
        TurbulenceStrength->Group = TEXT("RaftSimLocalFluid");
        Material->GetExpressionCollection().AddExpression(TurbulenceStrength);
        UMaterialExpressionScalarParameter* FluidWindowMeters =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        FluidWindowMeters->ParameterName =
            TEXT("RaftSimLocalFluidWindowMeters");
        FluidWindowMeters->DefaultValue = 100.0f;
        FluidWindowMeters->Group = TEXT("RaftSimLocalFluid");
        Material->GetExpressionCollection().AddExpression(FluidWindowMeters);

        UMaterialExpressionCustom* Turbulence =
            NewObject<UMaterialExpressionCustom>(Material);
        Turbulence->Desc = TEXT("RaftSimRaftLocalGpuFluidWPOV5");
        Turbulence->Description = TEXT(
            "Axis-free cellular crest clusters and current-carried boils");
        Turbulence->OutputType = CMOT_Float3;
        Turbulence->Code = kRaftLocalGpuFluidWpoCode;
        const auto AddTurbulenceInput = [Turbulence](
            FName Name, UMaterialExpression* Expression, int32 OutputIndex = 0)
        {
            FCustomInput Input;
            Input.InputName = Name;
            Input.Input.Connect(OutputIndex, Expression);
            Turbulence->Inputs.Add(Input);
        };
        AddTurbulenceInput(TEXT("UV"), TurbulenceUv);
        AddTurbulenceInput(TEXT("Foam"), TurbulenceVertexColor, 1);
        AddTurbulenceInput(TEXT("Speed"), TurbulenceVertexColor, 3);
        AddTurbulenceInput(TEXT("Wet"), TurbulenceVertexColor, 4);
        AddTurbulenceInput(TEXT("DepthNorm"), TurbulenceVertexColor, 2);
        AddTurbulenceInput(TEXT("FlowDisplacement"), FlowDisplacement);
        AddTurbulenceInput(TEXT("WaveClock"), WaveClock);
        AddTurbulenceInput(TEXT("RaftCenter"), RaftCenter);
        AddTurbulenceInput(TEXT("WorldPosition"), FluidWorldPosition);
        AddTurbulenceInput(TEXT("Strength"), TurbulenceStrength);
        AddTurbulenceInput(TEXT("WindowMeters"), FluidWindowMeters);
        Material->GetExpressionCollection().AddExpression(Turbulence);

        if (UMaterialEditorOnlyData* WpoEditorData = Material->GetEditorOnlyData())
        {
            UMaterialExpression* ExistingWpo =
                WpoEditorData->WorldPositionOffset.Expression;
            if (ExistingWpo)
            {
                UMaterialExpressionAdd* CombinedWpo =
                    NewObject<UMaterialExpressionAdd>(Material);
                CombinedWpo->A.Expression = ExistingWpo;
                CombinedWpo->B.Expression = Turbulence;
                Material->GetExpressionCollection().AddExpression(CombinedWpo);
                WpoEditorData->WorldPositionOffset.Connect(0, CombinedWpo);
            }
            else
            {
                WpoEditorData->WorldPositionOffset.Connect(0, Turbulence);
            }
            bNeedsSave = true;
        }
    }

    if (!bHasLiveLevelSink)
    {
        // The band meshes are cooked at ONE flow band while the release
        // schedule moves the live level through the day, so the whole
        // cooked sheet floated (measured 36 cm on a morning run) above the
        // live carrier: two stacked surfaces meeting the bank at different
        // places ("the glossy surface and the water surface are still
        // separate ... the glossy surface still runs over the shore",
        // 2026-09-02 — the pixel-side shore clip alone only retired the
        // sub-threshold margin, not the floating channel sheet). Sink the
        // entire sheet by the published live-minus-cooked delta; where the
        // bank stands taller than the sunk sheet the terrain depth-test
        // hides the edge, which is exactly the live waterline. The solver
        // carrier keeps ApplyLiveLevelShoreClip at 0 and never moves.
        Material->Modify();
        if (UMaterialParameterCollection* SinkCollection =
                LoadOrCreateRaftFoamOcclusionCollection(OutSummary))
        {
            UMaterialExpressionCollectionParameter* LevelDelta =
                AddRaftWaterCollectionParameter(
                    Material, SinkCollection,
                    TEXT("RaftSimLiveWaterLevelDeltaM"), true);
            UMaterialExpressionScalarParameter* SinkEnabled =
                NewObject<UMaterialExpressionScalarParameter>(Material);
            SinkEnabled->ParameterName = TEXT("ApplyLiveLevelShoreClip");
            SinkEnabled->DefaultValue = 0.0f;
            SinkEnabled->Group = TEXT("RaftSimSouthForkWaterMotion");
            Material->GetExpressionCollection().AddExpression(SinkEnabled);
            UMaterialExpressionVertexColor* SinkVertexColor =
                NewObject<UMaterialExpressionVertexColor>(Material);
            Material->GetExpressionCollection().AddExpression(SinkVertexColor);
            UMaterialExpressionCustom* Sink =
                NewObject<UMaterialExpressionCustom>(Material);
            Sink->Desc = TEXT("RaftSimLiveLevelSinkWPO");
            Sink->Description = TEXT(
                "Sink the cooked band sheet to the live water level");
            Sink->OutputType = CMOT_Float3;
            // Sinking (negative delta) applies in full: buried edges are
            // invisible. RAISING must taper to zero at the cooked
            // shoreline — a uniformly raised sheet hangs its rim in
            // mid-air over the bank and floats pale shelves across bars
            // and rock cutouts ("water texture is missing", station 920,
            // measured live +0.51 m over the cooked band on the release
            // wave). Scaling the raise by cooked depth (VC.G stores
            // depth/2.5) tilts the sheet from its pinned shoreline up to
            // the live level in the channel, approximating where the
            // higher waterline meets the sloped bank.
            Sink->Code = TEXT(
                "float OffsetM = clamp(DeltaM, -1.5, 1.5);\n"
                "if (OffsetM > 0.0)\n"
                "{\n"
                "    float CookedDepthM = CookedDepthNorm * 2.5;\n"
                "    OffsetM *= saturate(CookedDepthM / (OffsetM + 0.4));\n"
                "}\n"
                "return float3(0.0, 0.0, OffsetM * 100.0 * Enabled);");
            FCustomInput DeltaInput;
            DeltaInput.InputName = TEXT("DeltaM");
            DeltaInput.Input.Connect(0, LevelDelta);
            Sink->Inputs.Add(DeltaInput);
            FCustomInput EnabledInput;
            EnabledInput.InputName = TEXT("Enabled");
            EnabledInput.Input.Connect(0, SinkEnabled);
            Sink->Inputs.Add(EnabledInput);
            FCustomInput DepthInput;
            DepthInput.InputName = TEXT("CookedDepthNorm");
            DepthInput.Input.Connect(2, SinkVertexColor);
            Sink->Inputs.Add(DepthInput);
            Material->GetExpressionCollection().AddExpression(Sink);
            if (UMaterialEditorOnlyData* WpoEditorData =
                    Material->GetEditorOnlyData())
            {
                if (UMaterialExpression* ExistingWpo =
                        WpoEditorData->WorldPositionOffset.Expression)
                {
                    UMaterialExpressionAdd* CombinedWpo =
                        NewObject<UMaterialExpressionAdd>(Material);
                    CombinedWpo->A.Expression = ExistingWpo;
                    CombinedWpo->B.Expression = Sink;
                    Material->GetExpressionCollection().AddExpression(
                        CombinedWpo);
                    WpoEditorData->WorldPositionOffset.Connect(0, CombinedWpo);
                }
                else
                {
                    WpoEditorData->WorldPositionOffset.Connect(0, Sink);
                }
                bNeedsSave = true;
            }
        }
    }

    // V4 was duplicated before the shared parent's analytic-normal amplitude
    // gate existed. Setting AnalyticChopStrength on its instance did nothing,
    // leaving infinite crossing sine slopes in calm-water reflections. Migrate
    // the actual normal branch, without rebuilding the transmission graph.
    UMaterialExpressionScalarParameter* ChopGate = nullptr;
    UMaterialExpressionScalarParameter* SteepnessParameter = nullptr;
    for (UMaterialExpression* Expression : Material->GetExpressions())
    {
        if (auto* Parameter = Cast<UMaterialExpressionScalarParameter>(Expression))
        {
            if (Parameter->ParameterName == TEXT("AnalyticChopStrength")) ChopGate = Parameter;
            if (Parameter->ParameterName == TEXT("FlowNormalSteepness")) SteepnessParameter = Parameter;
        }
    }
    UMaterialExpressionAppendVector* LegacyAnalyticSlope = nullptr;
    if (!ChopGate && SteepnessParameter)
    {
        for (UMaterialExpression* Expression : Material->GetExpressions())
        {
            auto* Steepness = Cast<UMaterialExpressionMultiply>(Expression);
            if (!Steepness || Steepness->B.Expression != SteepnessParameter) continue;
            auto* XYMask = Cast<UMaterialExpressionMultiply>(Steepness->A.Expression);
            auto* CombinedSlopes = XYMask ? Cast<UMaterialExpressionAdd>(XYMask->A.Expression) : nullptr;
            auto* Analytic = CombinedSlopes ? Cast<UMaterialExpressionAppendVector>(CombinedSlopes->B.Expression) : nullptr;
            auto* ZeroZ = Analytic ? Cast<UMaterialExpressionConstant>(Analytic->B.Expression) : nullptr;
            if (Analytic && ZeroZ && FMath::IsNearlyZero(ZeroZ->R) &&
                Cast<UMaterialExpressionLinearInterpolate>(Analytic->A.Expression))
            {
                LegacyAnalyticSlope = Analytic;
                break;
            }
        }
        if (LegacyAnalyticSlope)
        {
            ChopGate = NewObject<UMaterialExpressionScalarParameter>(Material);
            ChopGate->ParameterName = TEXT("AnalyticChopStrength");
            ChopGate->DefaultValue = 0.0f;
            Material->GetExpressionCollection().AddExpression(ChopGate);
            auto* GatedSlope = NewObject<UMaterialExpressionMultiply>(Material);
            GatedSlope->A = LegacyAnalyticSlope->A;
            GatedSlope->B.Connect(0, ChopGate);
            GatedSlope->Desc = TEXT("RaftSimLegacyAnalyticNormalGate");
            Material->GetExpressionCollection().AddExpression(GatedSlope);
            LegacyAnalyticSlope->A.Connect(0, GatedSlope);
            OutSummary += TEXT("Migrated the legacy ungated analytic water-normal branch.\n");
            bNeedsSave = true;
        }
    }

    // The procedural carrier uploads half-precision vertex UVs. At an 8 km
    // station adjacent rows otherwise quantize to identical values, producing
    // six-metre foam bars. Reconstruct absolute coordinates AFTER interpolation.
    // Static tiles retain their existing coordinates because the origin is zero.
    const TArray<TObjectPtr<UMaterialExpression>> OriginalExpressions(Material->GetExpressions());
    UMaterialExpressionVectorParameter* RiverOrigin = nullptr;
    for (UMaterialExpression* Expression : OriginalExpressions)
    {
        if (auto* Parameter = Cast<UMaterialExpressionVectorParameter>(Expression);
            Parameter && Parameter->ParameterName == TEXT("RaftSimWaterUVOrigin"))
        {
            RiverOrigin = Parameter;
        }
    }
    for (UMaterialExpression* Expression : OriginalExpressions)
    {
        auto* Coordinate = Cast<UMaterialExpressionTextureCoordinate>(Expression);
        if (!Coordinate || Coordinate->CoordinateIndex != 0 ||
            Coordinate->Desc.Contains(TEXT("RaftSimFullPrecisionRiverUV")))
        {
            continue;
        }
        if (!RiverOrigin)
        {
            RiverOrigin = NewObject<UMaterialExpressionVectorParameter>(Material);
            RiverOrigin->ParameterName = TEXT("RaftSimWaterUVOrigin");
            RiverOrigin->DefaultValue = FLinearColor::Transparent;
            Material->GetExpressionCollection().AddExpression(RiverOrigin);
        }
        auto* OriginXY = NewObject<UMaterialExpressionComponentMask>(Material);
        OriginXY->Input.Connect(0, RiverOrigin);
        OriginXY->R = OriginXY->G = true;
        OriginXY->B = OriginXY->A = false;
        Material->GetExpressionCollection().AddExpression(OriginXY);
        auto* Tiling = NewObject<UMaterialExpressionConstant2Vector>(Material);
        Tiling->R = Coordinate->UTiling;
        Tiling->G = Coordinate->VTiling;
        Material->GetExpressionCollection().AddExpression(Tiling);
        auto* ScaledOrigin = NewObject<UMaterialExpressionMultiply>(Material);
        ScaledOrigin->A.Connect(0, OriginXY);
        ScaledOrigin->B.Connect(0, Tiling);
        Material->GetExpressionCollection().AddExpression(ScaledOrigin);
        auto* AbsoluteUV = NewObject<UMaterialExpressionAdd>(Material);
        AbsoluteUV->A.Connect(0, Coordinate);
        AbsoluteUV->B.Connect(0, ScaledOrigin);
        Material->GetExpressionCollection().AddExpression(AbsoluteUV);
        for (UMaterialExpression* Consumer : OriginalExpressions)
        {
            if (!Consumer)
            {
                continue;
            }
            for (FExpressionInputIterator Input{Consumer}; Input; ++Input)
            {
                if (Input->Expression == Coordinate)
                {
                    Input->Expression = AbsoluteUV;
                }
            }
        }
        Coordinate->Desc += TEXT(" RaftSimFullPrecisionRiverUV");
        bNeedsSave = true;
    }

    if (bNeedsSave)
    {
        // Expression edits are not independently represented in shader DDC
        // keys. Invalidate the saved identity and refresh parameter/texture
        // metadata even when deferring shader compilation until next load.
        Material->StateId = FGuid::NewGuid();
        Material->UpdateCachedExpressionData();
        // This existing parent is already configured for Single Layer Water
        // and instanced meshes. Save the serialized expression graph before
        // asking Unreal to rebuild its rendering resources: PostEditChange
        // can otherwise wait on this large parent's shader permutations and
        // prevent the package from ever being written. The next material load
        // performs normal compilation from the newly saved graph.
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
    // The normal playable carrier already consumes this parent. Keep its
    // optical microstructure moving with the integrated current and filtered
    // to the pixel footprint, including after a full material regeneration.
    return LoadOrCreateCurrentGradientWaterParent(Material, PackagePath,
        TEXT("SouthFork"), 0.28f, 0.18f, OutSummary, true);
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
    // The parent remains reusable for other rivers. South Fork runs clear
    // snowmelt over pale granite: outside aerated water the bed must stay
    // legible through the surface, with the green volume tint supplied by
    // absorption rather than an opaque body colour ("river water should be
    // clear and transparent, the colour of the rocks beneath comes
    // through", player reference photo 2026-08-31). Whitewater keeps a
    // near-opaque white body so aeration contrasts with the clear pools.
    // Static tiles retire everything the cook placed above the live level
    // (RaftSimLiveWaterLevelDeltaM); the live carrier keeps this off.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ApplyLiveLevelShoreClip")), 1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ShallowWaterOpacity")), 0.30f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DeepWaterOpacity")), 0.54f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamWaterOpacity")), 0.91f);
    // South Fork's single solver-conforming carrier owns the whitewater. Its
    // lace coordinates consume the same integrated-current displacement as
    // the persistent vertex foam, so retain organic holes without restoring
    // an independently animated drift sheet or a panner that can outrun a
    // passively drifting raft.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorBreakupBias")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorBreakupGain")), 3.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DriftFoamAerationGain")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DriftFoamSpeedGain")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorSurfaceOpacityScale")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorOpticalDepthScale")), 0.0f);
    // The fixed environment captures do not retain the guide viewport's full
    // temporal reflection history. Calibrate the South Fork instance toward
    // the gray-green body colour and blue-sky response visible in the source
    // corridor instead of changing the shared parent or hydraulic channels.
    // Clear-water optics: the diffuse body colour stays close to black (real
    // clear water has almost no diffuse albedo — its colour is volumetric),
    // red is absorbed roughly twice as fast as green so depth reads as the
    // source corridor's emerald rather than gray-teal, scattering is halved
    // so pools do not go milky, and the behind-water bed keeps most of its
    // light so submerged granite stays visible wherever water is not aerated.
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ShallowWaterColor")),
        FLinearColor(0.012f, 0.030f, 0.026f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("DeepWaterColor")),
        FLinearColor(0.006f, 0.020f, 0.019f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ReflectedSkyColor")),
        FLinearColor(0.075f, 0.130f, 0.150f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterScattering")),
        FLinearColor(0.00010f, 0.00028f, 0.00020f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterAbsorption")),
        FLinearColor(0.0066f, 0.0026f, 0.0040f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RiverbedColorScale")),
        FLinearColor(0.60f, 0.64f, 0.58f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RaftInteriorBehindWaterScale")),
        FLinearColor(1.0f, 1.0f, 1.0f, 0.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicWhitewaterGain")), 0.30f);
    // Whitewater has one visual owner: this solver-conforming Single Layer
    // Water carrier. The raised masked sheet is disabled on South Fork, so
    // retain the advected vertex foam here. The breakup shares that field's
    // integrated motion and therefore adds detail without another foam sheet.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamIntensity")), 0.90f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamCoverageGain")), 0.95f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorBreakupGain")), 3.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamColorCoreGain")), 1.25f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WhitewaterFrothLaceModulationFloor")), 0.02f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamRoughness")), 0.80f);
    // Clear pools are glassy: a tight specular lobe reads as real mirror
    // water (dark where it reflects the far bank, bright only in the sun and
    // sky lanes), while the previous 0.24 roughness blurred sky and shore
    // into a uniform pale sheet that swamped the transmission ("river water
    // should be clear and transparent", 2026-08-31). The additive fallback
    // sky term gets the same treatment — it exists for reflection-history-
    // free captures, and at 0.28 it was a constant milky veil over the
    // guide's whole view. Roughness MATCHES the live carrier's 0.20
    // exactly: once the level sink put both sheets at the same height, a
    // 0.15 tile lobe rendered glass-sharp tree reflections against the
    // carrier's softer ones — a visible quality seam at the carrier window
    // edge ("the glossy surface and the water surface still seem
    // different", 2026-09-02).
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterRoughness")), 0.22f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Specular")), 0.28f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FresnelSpecular")), 0.18f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionStrength")), 0.15f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmSurfaceColorVariation")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionFloor")), 1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FallbackSkyReflectionVariation")), 0.0f);
    // Match the precision-correct live carrier. Full-precision static tile UVs
    // now preserve small-scale detail without the former row-collapse bars.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmRippleStrength")), 0.08f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowRippleStrength")), 0.14f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamRippleStrength")), 0.25f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AnalyticChopStrength")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RippleGrazingFloor")), 0.50f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowNormalSteepness")), 2.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SlickNormalFloor")), 0.60f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("LiveFlowStreakRoughness")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("LiveFlowStreakTint")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowStreakRoughness")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowStreakSpeedGain")), 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SouthForkTravelingWaveWPOStrength")), 0.0f);
    // The unified carrier's small-scale current relief is evaluated by the
    // material every rendered frame from river-space UVs and the integrated
    // solver-current displacement. A restrained amplitude retains visible 3D
    // flow while avoiding the vertical stepping caused by resampling animated
    // CPU vertices only at the 15 Hz hydraulic presentation refresh.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SouthForkTurbulenceWPOStrength")), 0.0f);
    // Persist authored overrides without forcing this command to wait on the
    // parent shader map; loading the instance rebuilds its resources normally.
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

static void HandleRefreshAllRiverFluidMaterials(const TArray<FString>&)
{
    FString Summary;
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim all-river fluid material refresh: loading source water"));
    UMaterialInterface* SourceWater = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
             "M_RaftSim_PhotorealRiverWater"));
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim all-river fluid material refresh: rebuilding shared parent"));
    const bool bSharedParentReady = SourceWater &&
        LoadSouthForkProductionWaterPresentation(SourceWater, Summary);
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim all-river fluid material refresh: rebuilding river instances"));
    const bool bPacuareReady =
        LoadOrCreatePacuareUpperHuacasLiveWaterInstance(Summary) != nullptr;
    const bool bFutaleufuReady =
        LoadOrCreateFutaleufuTerminatorLiveWaterInstance(Summary) != nullptr;
    const bool bChilkoReady =
        LoadOrCreateChilkoLavaCanyonLiveWaterInstance(Summary) != nullptr;
    const bool bColoradoReady =
        LoadOrCreateColoradoHanceLiveWaterInstance(Summary) != nullptr;
    const bool bZambeziReady =
        LoadOrCreateZambeziBatokaLiveWaterV2Instance(Summary) != nullptr;
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim all-river fluid material refresh parent=%d pacuare=%d "
             "futaleufu=%d chilko=%d colorado=%d zambezi=%d\n%s"),
        bSharedParentReady ? 1 : 0,
        bPacuareReady ? 1 : 0,
        bFutaleufuReady ? 1 : 0,
        bChilkoReady ? 1 : 0,
        bColoradoReady ? 1 : 0,
        bZambeziReady ? 1 : 0,
        *Summary);
}

static FAutoConsoleCommand GRefreshAllRiverFluidMaterialsCommand(
    TEXT("RaftSim.RefreshAllRiverFluidMaterials"),
    TEXT("Refresh the shared bounded GPU fluid parent and every river-local instance."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleRefreshAllRiverFluidMaterials));

static void HandleRefreshSolverCurrentFoamMaterial(
    const TArray<FString>& Arguments)
{
    FString Summary;
    UMaterialInterface* FoamMaterial =
        LoadOrCreateLandscapeCandidateSolverFoamMaterial(Summary);
    // The foam advection field lives in the same parameter collection as the
    // Single Layer Water raft-interior aperture. Adding or reordering a
    // collection parameter invalidates every material shader that consumes
    // that collection, even when the water graph itself did not change. The
    // former foam-only refresh saved the new collection and foam shader but
    // left the sole South Fork water carrier with a stale collection layout;
    // PIE then rendered a completely dry river until another editor process
    // happened to compile the water parent. Refresh and save that dependency
    // in the same transaction so the one-surface carrier is immediately
    // renderable in the current and next run.
    UMaterialInterface* WaterMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
             "M_RaftSim_PhotorealRiverWater"));
    const bool bWaterReady = WaterMaterial &&
        LoadSouthForkProductionWaterPresentation(WaterMaterial, Summary);
    UE_LOG(
        LogRaftSimEditorEnvironment,
        Display,
        TEXT("RaftSim solver-current foam refresh foam=%d water=%d\n%s"),
        FoamMaterial ? 1 : 0,
        bWaterReady ? 1 : 0,
        *Summary);
    if (Arguments.ContainsByPredicate([](const FString& Argument)
        {
            return Argument.Equals(TEXT("Quit"), ESearchCase::IgnoreCase);
        }))
    {
        FPlatformMisc::RequestExit(false);
    }
}

static FAutoConsoleCommand GRefreshSolverCurrentFoamMaterialCommand(
    TEXT("RaftSim.RefreshSolverCurrentFoamMaterial"),
    TEXT("Refresh the solver foam material, its parameter collection, and "
         "dependent South Fork water carrier shader."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleRefreshSolverCurrentFoamMaterial));

static FAutoConsoleCommand GRefreshSouthForkCurrentNormalsCommand(
    TEXT("RaftSim.RefreshSouthForkCurrentNormals"),
    TEXT("Refresh current normals and transported foam optics on the normal South Fork water parent."),
    FConsoleCommandDelegate::CreateLambda([]()
    {
        const FString Path = TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
            "M_RaftSim_SouthForkRaftTransmissionWaterV4");
        UMaterial* Material = LoadObject<UMaterial>(nullptr,
            *(Path + TEXT(".M_RaftSim_SouthForkRaftTransmissionWaterV4")));
        FString Summary;
        UMaterial* Updated = LoadOrCreateCurrentGradientWaterParent(Material, Path,
            TEXT("SouthFork"), 0.28f, 0.18f, Summary, true);
        UE_LOG(LogRaftSimEditorEnvironment, Display,
            TEXT("South Fork playable water optics saved=%d\n%s"), Updated ? 1 : 0, *Summary);
    }));

} // namespace RaftSimEditorEnvironment
