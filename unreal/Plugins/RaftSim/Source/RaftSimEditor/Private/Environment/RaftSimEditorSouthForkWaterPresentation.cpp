#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
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
        OpticalDepthResponse->Base.Expression = SolverDepthMask;
        OpticalDepthResponse->Exponent.Expression = ResponseExponent;
        Material->GetExpressionCollection().AddExpression(
            OpticalDepthResponse);

        int32 RewiredDepthBlends = 0;
        for (const TObjectPtr<UMaterialExpression>& Expression :
             Material->GetExpressionCollection().Expressions)
        {
            UMaterialExpressionLinearInterpolate* DepthBlend =
                Cast<UMaterialExpressionLinearInterpolate>(Expression.Get());
            if (!DepthBlend ||
                DepthBlend->Alpha.Expression != SolverDepthMask)
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
    for (UMaterialExpression* Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (Expression &&
            Expression->Desc == TEXT("RaftSimTravelingBakeWaveWPO"))
        {
            bHasTravelingWaveOffset = true;
            break;
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
        // Boat wake as geometry: the same analytic V-arm field the base
        // colour draws also lifts the surface, so the wake is water, not a
        // decal. Reads the raft state the surface actor pushes into the
        // shared collection every tick.
        UMaterialExpression* WakeReliefMeters = nullptr;
        if (UMaterialParameterCollection* WakeCollection =
                LoadOrCreateRaftFoamOcclusionCollection(OutSummary))
        {
            UMaterialExpression* WakeBoatS = AddRaftWaterCollectionParameter(
                Material, WakeCollection,
                TEXT("RaftSimWakeBoatStationM"), true);
            UMaterialExpression* WakeBoatL = AddRaftWaterCollectionParameter(
                Material, WakeCollection,
                TEXT("RaftSimWakeBoatLateralM"), true);
            UMaterialExpression* WakeVelS = AddRaftWaterCollectionParameter(
                Material, WakeCollection,
                TEXT("RaftSimWakeBoatVelStationMps"), true);
            UMaterialExpression* WakeVelL = AddRaftWaterCollectionParameter(
                Material, WakeCollection,
                TEXT("RaftSimWakeBoatVelLateralMps"), true);
            UMaterialExpression* WakeEnable = AddRaftWaterCollectionParameter(
                Material, WakeCollection,
                TEXT("RaftSimWakeBoatEnable"), true);
            if (WakeBoatS && WakeBoatL && WakeVelS && WakeVelL && WakeEnable)
            {
                UMaterialExpressionCustom* WakeReliefNode =
                    NewObject<UMaterialExpressionCustom>(Material);
                WakeReliefNode->Description =
                    TEXT("RaftSimBoatWakeRelief");
                WakeReliefNode->OutputType = CMOT_Float1;
                WakeReliefNode->Code = TEXT(
                    "float2 rel = float2(S - BoatS, L - BoatL);\n"
                    "float2 rv = float2(VelS - WaterSpeed, VelL);\n"
                    "float sp = max(length(rv), 1e-4);\n"
                    "float2 dir = -rv / sp;\n"
                    "float along = dot(rel, dir);\n"
                    "float perp = length(rel - along * dir);\n"
                    "float speedF = saturate((sp - 0.05) / 1.4);\n"
                    "float age = sqrt(saturate(1.0 - along / 24.0));\n"
                    "float armOff = abs(perp - along * 0.53);\n"
                    "float arm = saturate(1.0 - armOff / 1.6) * age;\n"
                    "float hollow = saturate(1.0 - perp /\n"
                    "    (0.9 + along * 0.08)) * age;\n"
                    "float gate = step(0.5, Enable) * step(0.12, sp) *\n"
                    "    step(0.5, along) * step(along, 24.0);\n"
                    // Subtle heave only: the 4 m band mesh can only
                    // express broad smooth displacement, and at chase-
                    // camera grazing angles a tall smooth arm mirrors the
                    // sky as one white sheet. The visible wave train
                    // rides per-pixel normals in the surface material.
                    "return (0.07 * arm - 0.03 * hollow) *\n"
                    "    speedF * gate;\n");
                WakeReliefNode->Inputs.Empty();
                const auto AddWakeReliefInput =
                    [WakeReliefNode](
                        const TCHAR* Name, UMaterialExpression* Expr)
                {
                    FCustomInput Input;
                    Input.InputName = FName(Name);
                    Input.Input.Expression = Expr;
                    WakeReliefNode->Inputs.Add(Input);
                };
                AddWakeReliefInput(TEXT("S"), StationM);
                AddWakeReliefInput(TEXT("L"), LateralM);
                AddWakeReliefInput(TEXT("BoatS"), WakeBoatS);
                AddWakeReliefInput(TEXT("BoatL"), WakeBoatL);
                AddWakeReliefInput(TEXT("VelS"), WakeVelS);
                AddWakeReliefInput(TEXT("VelL"), WakeVelL);
                AddWakeReliefInput(TEXT("Enable"), WakeEnable);
                AddWakeReliefInput(
                    TEXT("WaterSpeed"), ScaleBy(EnergyB, 8.0f));
                AddExpr(WakeReliefNode);
                WakeReliefMeters = WakeReliefNode;
            }
        }
        if (WakeReliefMeters != nullptr)
        {
            DeltaMeters = AddPair(DeltaMeters, WakeReliefMeters);
        }
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
        if (UMaterialEditorOnlyData* WpoEditorData = Material->GetEditorOnlyData())
        {
            WpoEditorData->WorldPositionOffset.Connect(0, Offset);
            bNeedsSave = true;
        }
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
    // Ripple perceptibility retuned 2026-08-14 (fourth "water doesn't look
    // like it is moving" report, this time with an in-game screenshot and a
    // held-boat-on-slope experiment). The parent clamps summed normal
    // strength (ceiling now 0.30, was 0.14 — the old ceiling silently
    // saturated every prior retune). These weights keep calm water just
    // grained while fast water climbs toward the ceiling, and the parent's
    // FlowStreakRoughness lanes supply the directional downstream cue the
    // ripple amplitude alone cannot.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmRippleStrength")), 0.12f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowRippleStrength")), 0.30f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamRippleStrength")), 0.25f);
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
