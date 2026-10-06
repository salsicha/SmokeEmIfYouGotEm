// Photoreal river-water material (P4 photoreal track). Authors a genuine
// Single Layer Water material with depth-based colour, Fresnel-driven Lumen
// reflection, panned detail-normal ripples over the solver's geometric wave
// normals, and vertex-colour foam. Registered as a console command so it is
// generated headlessly, following the RaftSimEditor raw-expression idiom.

#include "Materials/RaftSimEditorPhotorealWaterMaterials.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionDesaturation.h"
#include "Materials/MaterialExpressionDistance.h"
#include "Materials/MaterialExpressionDivide.h"
#include "Materials/MaterialExpressionDotProduct.h"
#include "Materials/MaterialExpressionFrac.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionMax.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionNormalize.h"
#include "Materials/MaterialExpressionOneMinus.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionTime.h"
#include "Materials/MaterialExpressionPerInstanceCustomData.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionSine.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionShadowReplace.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialExpressionStaticSwitchParameter.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialFunctionInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "Misc/PackageName.h"
#include "AssetCompilingManager.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimPhotorealMaterials
{

// Churn panners (ripple normals, froth, foam lace) run on the shared
// flow-warped clock the water surface actor accumulates each frame, so the
// surface agitation visibly quickens in fast water ("the water doesn't speed
// up going down the rapid" — a rider moves WITH the current, so velocity-true
// UV advection reads near-static from the boat; churn frequency is the speed
// cue the eye actually gets). Bulk downstream advection stays on raw engine
// time: it is already velocity-proportional per vertex and warping it too
// would double-scale the motion. Returns nullptr (raw time) if the shared
// collection is unavailable.
static UMaterialExpression* AddWaveClockTimeExpression(UMaterial* Material)
{
    FString CollectionSummary;
    UMaterialParameterCollection* Collection =
        RaftSimEditorEnvironment::LoadOrCreateRaftFoamOcclusionCollection(
            CollectionSummary);
    if (!Collection)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("Photoreal water: no foam-occlusion collection for the wave ")
            TEXT("clock (%s); panners fall back to engine time."),
            *CollectionSummary);
        return nullptr;
    }
    static const FName ClockName(TEXT("RaftSimWaveClockSeconds"));
    UMaterialExpressionCollectionParameter* Expression =
        NewObject<UMaterialExpressionCollectionParameter>(Material);
    Expression->Collection = Collection;
    Expression->ParameterName = ClockName;
    Expression->ExpressionGUID = FGuid::NewGuid();
    const int32 ParameterIndex = Collection->ScalarParameters.IndexOfByPredicate(
        [](const FCollectionScalarParameter& Parameter)
        {
            return Parameter.ParameterName ==
                FName(TEXT("RaftSimWaveClockSeconds"));
        });
    if (ParameterIndex != INDEX_NONE)
    {
        Expression->ParameterId =
            Collection->ScalarParameters[ParameterIndex].Id;
    }
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}

static UMaterialExpression* AddFoamCollectionScalarExpression(
    UMaterial* Material, const TCHAR* ParameterName)
{
    FString CollectionSummary;
    UMaterialParameterCollection* Collection =
        RaftSimEditorEnvironment::LoadOrCreateRaftFoamOcclusionCollection(
            CollectionSummary);
    if (!Collection)
    {
        return nullptr;
    }
    UMaterialExpressionCollectionParameter* Expression =
        NewObject<UMaterialExpressionCollectionParameter>(Material);
    Expression->Collection = Collection;
    Expression->ParameterName = FName(ParameterName);
    Expression->ExpressionGUID = FGuid::NewGuid();
    const int32 ParameterIndex =
        Collection->ScalarParameters.IndexOfByPredicate(
            [ParameterName](const FCollectionScalarParameter& Parameter)
            {
                return Parameter.ParameterName == FName(ParameterName);
            });
    if (ParameterIndex == INDEX_NONE)
    {
        return nullptr;
    }
    Expression->ParameterId = Collection->ScalarParameters[ParameterIndex].Id;
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}

// Move every visible water pattern from one continuous current integral.
// Multiplying a changing velocity by absolute material time changes the whole
// UV phase whenever the sampled flow changes; independent panners add a second
// apparent velocity. Both show up as foam that outruns a passive raft and as
// full-pattern flashes at live-window refreshes. The surface actor integrates
// the current once per frame and publishes that displacement in river metres.
static UMaterialExpression* AddCurrentAdvectedCoordinates(
    UMaterial* Material,
    UMaterialExpression* BaseCoordinates,
    float UTiling,
    float VTiling,
    float SlipFactor,
    const TCHAR* Description)
{
    FString CollectionSummary;
    UMaterialParameterCollection* Collection =
        RaftSimEditorEnvironment::LoadOrCreateRaftFoamOcclusionCollection(
            CollectionSummary);
    if (!Collection)
    {
        return BaseCoordinates;
    }

    static const FName AdvectionName(TEXT("RaftSimFoamAdvectionMeters"));
    UMaterialExpressionCollectionParameter* Displacement =
        NewObject<UMaterialExpressionCollectionParameter>(Material);
    Displacement->Collection = Collection;
    Displacement->ParameterName = AdvectionName;
    Displacement->ExpressionGUID = FGuid::NewGuid();
    const int32 ParameterIndex =
        Collection->VectorParameters.IndexOfByPredicate(
            [](const FCollectionVectorParameter& Parameter)
            {
                return Parameter.ParameterName ==
                    FName(TEXT("RaftSimFoamAdvectionMeters"));
            });
    if (ParameterIndex == INDEX_NONE)
    {
        return BaseCoordinates;
    }
    Displacement->ParameterId = Collection->VectorParameters[ParameterIndex].Id;
    Material->GetExpressionCollection().AddExpression(Displacement);

    UMaterialExpressionComponentMask* RiverDisplacement =
        NewObject<UMaterialExpressionComponentMask>(Material);
    RiverDisplacement->Input.Expression = Displacement;
    RiverDisplacement->R = true;
    RiverDisplacement->G = true;
    Material->GetExpressionCollection().AddExpression(RiverDisplacement);

    // UV0 stores river station/lateral divided by three metres. Subtracting
    // accumulated current back-traces the texture, which makes its features
    // travel downstream with the water at exactly the integrated flow speed.
    UMaterialExpressionConstant2Vector* MetersToUv =
        NewObject<UMaterialExpressionConstant2Vector>(Material);
    MetersToUv->R = -UTiling * SlipFactor / 3.0f;
    MetersToUv->G = -VTiling * SlipFactor / 3.0f;
    Material->GetExpressionCollection().AddExpression(MetersToUv);
    UMaterialExpressionMultiply* AdvectionUv =
        NewObject<UMaterialExpressionMultiply>(Material);
    AdvectionUv->A.Expression = RiverDisplacement;
    AdvectionUv->B.Expression = MetersToUv;
    Material->GetExpressionCollection().AddExpression(AdvectionUv);
    UMaterialExpressionAdd* AdvectedCoordinates =
        NewObject<UMaterialExpressionAdd>(Material);
    AdvectedCoordinates->Desc = Description;
    AdvectedCoordinates->A.Expression = BaseCoordinates;
    AdvectedCoordinates->B.Expression = AdvectionUv;
    Material->GetExpressionCollection().AddExpression(AdvectedCoordinates);
    return AdvectedCoordinates;
}

// Foam must travel with the same continuous current integral as the water,
// but its breakup must not inherit one river-aligned frame at every scale.
// Rotating and gently curl-warping the already-advected coordinates keeps the
// physical drift exact while turning long parallel lace ribbons into short,
// intersecting froth cells.  The deformation is deterministic and contains no
// independent panner, so it cannot outrun the raft or reset at a window update.
static UMaterialExpression* AddTurbulentFoamCoordinates(
    UMaterial* Material,
    UMaterialExpression* AdvectedCoordinates,
    float RotationRadians,
    float CurlStrength,
    const TCHAR* Description)
{
    UMaterialExpressionCustom* TurbulentCoordinates =
        NewObject<UMaterialExpressionCustom>(Material);
    TurbulentCoordinates->Description = Description;
    TurbulentCoordinates->OutputType = CMOT_Float2;
    TurbulentCoordinates->Code = FString::Printf(
        TEXT("float c = %.9ff;\n")
        TEXT("float s = %.9ff;\n")
        TEXT("float2 q = UV - 0.5;\n")
        TEXT("q = float2(c * q.x - s * q.y, s * q.x + c * q.y);\n")
        TEXT("float2 curl = float2(\n")
        TEXT("    sin(q.y * 6.2831853 + sin(q.x * 3.71)),\n")
        TEXT("    cos(q.x * 6.2831853 - sin(q.y * 4.13))) * %.9ff;\n")
        TEXT("return q + curl + 0.5;"),
        FMath::Cos(RotationRadians),
        FMath::Sin(RotationRadians),
        CurlStrength);
    FCustomInput UvInput;
    UvInput.InputName = TEXT("UV");
    UvInput.Input.Expression = AdvectedCoordinates;
    TurbulentCoordinates->Inputs.Add(UvInput);
    Material->GetExpressionCollection().AddExpression(TurbulentCoordinates);
    return TurbulentCoordinates;
}

// A broad solver foam value is intentionally continuous across a hydraulic
// feature; using it directly can still turn any detailed lace into long white
// lanes. This deterministic cellular gate partitions that mass into compact
// bubble/boil clusters. It is evaluated on the same advected coordinate field,
// so the clusters are carried by the current rather than panning independently.
static UMaterialExpression* AddCellularFoamPatchMask(
    UMaterial* Material,
    UMaterialExpression* AdvectedCoordinates,
    const TCHAR* Description)
{
    UMaterialExpressionCustom* Cells =
        NewObject<UMaterialExpressionCustom>(Material);
    Cells->Description = Description;
    Cells->OutputType = CMOT_Float1;
    Cells->Code = TEXT(
        "float2 p = UV;\n"
        "float2 baseCell = floor(p);\n"
        "float2 withinCell = frac(p);\n"
        "float nearest = 8.0;\n"
        "[unroll] for (int y = -1; y <= 1; ++y)\n"
        "{\n"
        "  [unroll] for (int x = -1; x <= 1; ++x)\n"
        "  {\n"
        "    float2 lattice = baseCell + float2(x, y);\n"
        "    float2 seed = frac(sin(float2(\n"
        "      dot(lattice, float2(127.1, 311.7)),\n"
        "      dot(lattice, float2(269.5, 183.3)))) * 43758.5453);\n"
        "    float2 delta = float2(x, y) + seed - withinCell;\n"
        "    float edgeWarp = 0.08 * sin(dot(delta, float2(7.31, 5.17)) + seed.x * 6.2831853)\n"
        "                   + 0.05 * sin(dot(p, float2(11.7, -8.3)) + seed.y * 6.2831853);\n"
        "    nearest = min(nearest, length(delta) + edgeWarp);\n"
        "  }\n"
        "}\n"
        "float cluster = 1.0 - smoothstep(0.18, 0.46, nearest);\n"
        "float coarse = 0.5 + 0.5 * sin(p.x * 5.17 + sin(p.y * 4.31));\n"
        "float grain = 0.5 + 0.5 * sin(p.x * 13.7 + sin(p.y * 8.3))\n"
        "                          * sin(p.y * 11.9 - sin(p.x * 6.1));\n"
        "float tornInterior = 0.30 + 0.70 * saturate(0.34 * coarse + 0.86 * grain);\n"
        "return saturate((cluster - 0.16) * 1.36) * tornInterior;");
    FCustomInput UvInput;
    UvInput.InputName = TEXT("UV");
    UvInput.Input.Expression = AdvectedCoordinates;
    Cells->Inputs.Add(UvInput);
    Material->GetExpressionCollection().AddExpression(Cells);
    return Cells;
}

// Voronoi islands read as round paint splotches when the solver foam channel
// is broad.  Whitewater instead forms connected sheets, branching tongues and
// torn seams.  This isotropic, domain-warped web supplies that larger shape;
// the sampled foam lace below still supplies the bubble-scale holes.  Like all
// other presentation detail, it receives the shared current-advected UVs and
// therefore cannot slide independently of the water or the drifting raft.
static UMaterialExpression* AddTurbulentFoamWebMask(
    UMaterial* Material,
    UMaterialExpression* AdvectedCoordinates,
    const TCHAR* Description)
{
    UMaterialExpressionCustom* Web =
        NewObject<UMaterialExpressionCustom>(Material);
    Web->Description = Description;
    Web->OutputType = CMOT_Float1;
    Web->Code = TEXT(
        "float2 p = UV;\n"
        "float2 warp = float2(\n"
        "  sin(p.y * 0.73 + sin(p.x * 0.47)) + 0.55 * sin(dot(p, float2(0.61, -0.39))),\n"
        "  cos(p.x * 0.67 - sin(p.y * 0.43)) + 0.55 * cos(dot(p, float2(0.37, 0.59))));\n"
        "float2 q = p + warp * 0.34;\n"
        "float a = sin(q.x * 1.17 + sin(q.y * 0.83)) * cos(q.y * 1.31 - sin(q.x * 0.71));\n"
        "float b = sin(dot(q, float2(1.43, 1.91)) + sin(q.x * 0.57))\n"
        "        * cos(dot(q, float2(-1.73, 1.09)) - sin(q.y * 0.63));\n"
        "float c = sin(q.x * 3.71 + sin(q.y * 2.87))\n"
        "        * sin(q.y * 3.39 - sin(q.x * 2.53));\n"
        "float sheetField = 0.58 * a + 0.42 * b;\n"
        "float sheet = 1.0 - smoothstep(0.18, 0.66, abs(sheetField));\n"
        "float branchField = abs(sin(q.x * 1.09 + sin(q.y * 1.47))\n"
        "                      + 0.72 * sin(q.y * 1.23 - sin(q.x * 1.61)));\n"
        "float branches = 1.0 - smoothstep(0.24, 0.78, branchField);\n"
        "float grainA = 0.5 + 0.5 * c;\n"
        "float grainB = 0.5 + 0.5 * sin(q.x * 6.31 + sin(q.y * 4.77))\n"
        "                         * sin(q.y * 5.83 - sin(q.x * 4.19));\n"
        "float tornGrain = smoothstep(0.24, 0.78, 0.62 * grainA + 0.38 * grainB);\n"
        "float connectedWeb = saturate(sheet * 0.78 + branches * 0.52);\n"
        "return saturate(connectedWeb * (0.16 + 0.84 * tornGrain));");
    FCustomInput UvInput;
    UvInput.InputName = TEXT("UV");
    UvInput.Input.Expression = AdvectedCoordinates;
    Web->Inputs.Add(UvInput);
    Material->GetExpressionCollection().AddExpression(Web);
    return Web;
}

UMaterial* BuildPhotorealRiverWaterMaterial(const TCHAR* PackagePath, const TCHAR* ObjectName)
{
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), PackagePath, ObjectName);

    UPackage* Package = CreatePackage(PackagePath);
    if (Package == nullptr)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(
        UMaterial::StaticClass(), nullptr, *ObjectPath));
    if (Material == nullptr)
    {
        Material = NewObject<UMaterial>(
            Package, FName(ObjectName),
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (Material == nullptr)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_SingleLayerWater);
    Material->BlendMode = BLEND_Opaque;
    // Water must remain readable both from the guide position and during a
    // flip/underwater recovery. Full-reach meshes still author their front
    // faces toward the guide side for correct Single Layer Water shading.
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;
    Material->SetMaterialUsage(MATUSAGE_Water);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);

    auto Add = [Material](UMaterialExpression* E) { Material->GetExpressionCollection().AddExpression(E); return E; };
    auto Scalar = [&](const TCHAR* Name, float V)
    {
        UMaterialExpressionScalarParameter* P = NewObject<UMaterialExpressionScalarParameter>(Material);
        P->ParameterName = Name; P->DefaultValue = V; P->Group = TEXT("RaftSimPhotorealWater");
        Add(P); return P;
    };
    auto Vector = [&](const TCHAR* Name, const FLinearColor& V)
    {
        UMaterialExpressionVectorParameter* P = NewObject<UMaterialExpressionVectorParameter>(Material);
        P->ParameterName = Name; P->DefaultValue = V; P->Group = TEXT("RaftSimPhotorealWater");
        Add(P); return P;
    };
    auto Const3 = [&](float R, float G, float B)
    {
        UMaterialExpressionConstant3Vector* C = NewObject<UMaterialExpressionConstant3Vector>(Material);
        C->Constant = FLinearColor(R, G, B, 0.0f); Add(C); return C;
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B, UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* L = NewObject<UMaterialExpressionLinearInterpolate>(Material);
        L->A.Expression = A; L->B.Expression = B; L->Alpha.Expression = Alpha; Add(L); return L;
    };
    auto Mask = [&](UMaterialExpression* In, bool R, bool G, bool B)
    {
        UMaterialExpressionComponentMask* M = NewObject<UMaterialExpressionComponentMask>(Material);
        M->Input.Expression = In; M->R = R; M->G = G; M->B = B; M->A = false; Add(M); return M;
    };
    auto Mul = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* M = NewObject<UMaterialExpressionMultiply>(Material);
        M->A.Expression = A; M->B.Expression = B; Add(M); return M;
    };
    auto AddNode = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* N = NewObject<UMaterialExpressionAdd>(Material);
        N->A.Expression = A; N->B.Expression = B; Add(N); return N;
    };

    UMaterialExpressionVertexColor* VertexColor = Cast<UMaterialExpressionVertexColor>(
        Add(NewObject<UMaterialExpressionVertexColor>(Material)));

    // --- Base colour: depth-tinted river green, whitening into foam ---------
    // Calm and runnable South Fork reference photography is dark neutral
    // gray-green with narrow blue sky reflections, not the saturated emerald
    // pool produced by the previous green-weighted volume coefficients. Keep
    // this base dark and nearly neutral; physically shaded reflection and
    // solver-authored foam provide the lift.  The former near-black values
    // disappeared in deterministic offscreen captures even though the live
    // viewport retained temporal reflections, so preserve a measured amount
    // of gray-green body colour in the capture-safe path.
    UMaterialExpressionVectorParameter* ShallowColor =
        Vector(TEXT("ShallowWaterColor"), FLinearColor(0.018f, 0.035f, 0.040f, 0.0f));
    UMaterialExpressionVectorParameter* DeepColor =
        Vector(TEXT("DeepWaterColor"), FLinearColor(0.006f, 0.015f, 0.021f, 0.0f));
    UMaterialExpressionComponentMask* DepthMask = Mask(VertexColor, false, true, false); // G
    // Level-tracking tiles shade by their LIVE depth, not the cooked one:
    // when the release wave stands the sheet half a metre above its cooked
    // level, VC.G still says "ankle deep", so every depth-driven response
    // (body colour, opacity, shore de-gloss) rendered the raised water as
    // a pale shallow membrane hovering over the flooded bar ("water
    // texture is missing", station 920 at live +0.5 m). The published
    // delta corrects the basis wherever ApplyLiveLevelShoreClip is on;
    // the carrier keeps it at 0 and is untouched.
    UMaterialExpression* EffectiveDepthMask = DepthMask;
    if (UMaterialExpression* EarlyLevelDeltaM = AddFoamCollectionScalarExpression(
            Material, TEXT("RaftSimLiveWaterLevelDeltaM")))
    {
        UMaterialExpressionScalarParameter* EarlyClipEnabled =
            Scalar(TEXT("ApplyLiveLevelShoreClip"), 0.0f);
        UMaterialExpressionConstant* InverseDepthBasis =
            NewObject<UMaterialExpressionConstant>(Material);
        InverseDepthBasis->R = 1.0f / 2.5f;
        Add(InverseDepthBasis);
        UMaterialExpressionSaturate* LiveDepthMask =
            NewObject<UMaterialExpressionSaturate>(Material);
        LiveDepthMask->Input.Expression = AddNode(
            DepthMask,
            Mul(Mul(EarlyLevelDeltaM, InverseDepthBasis), EarlyClipEnabled));
        Add(LiveDepthMask);
        EffectiveDepthMask = LiveDepthMask;
    }
    UMaterialExpressionLinearInterpolate* DepthWaterColor =
        Lerp(ShallowColor, DeepColor, EffectiveDepthMask);

    // Natural optical variation: a real river drifts between olive, green and
    // gray-teal at the tens-of-metres scale (upwelling, dissolved load, bed
    // changes). One very-low-frequency world-space noise blends the depth
    // colour toward a relative olive shift of itself, so long reaches never
    // render as a single uniform colour sheet. The shift is multiplicative,
    // which preserves the shallow/deep depth relationship.
    UMaterialExpressionNoise* ReachHueNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    ReachHueNoise->Scale = 0.00055f;
    ReachHueNoise->bTurbulence = true;
    ReachHueNoise->Levels = 2;
    ReachHueNoise->OutputMin = 0.0f;
    ReachHueNoise->OutputMax = 1.0f;
    UMaterialExpressionMultiply* OliveShiftedColor = Mul(
        DepthWaterColor, Const3(1.16f, 1.10f, 0.74f));
    UMaterialExpressionMultiply* ReachHueAlpha = Mul(
        ReachHueNoise, Scalar(TEXT("ReachHueVariation"), 0.16f));
    UMaterialExpressionLinearInterpolate* WaterColor =
        Lerp(DepthWaterColor, OliveShiftedColor, ReachHueAlpha);

    // Scene captures do not have the guide camera's full temporal reflection
    // history. Preserve readable metre-scale surface modulation in calm water
    // without inventing foam or changing the hydraulic geometry.
    UMaterialExpressionNoise* SurfaceNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    SurfaceNoise->Scale = 0.0045f;
    SurfaceNoise->bTurbulence = true;
    SurfaceNoise->Levels = 3;
    SurfaceNoise->OutputMin = 0.0f;
    SurfaceNoise->OutputMax = 1.0f;
    UMaterialExpressionMultiply* SurfaceVariationAlpha = Mul(
        SurfaceNoise, Scalar(TEXT("CalmSurfaceColorVariation"), 0.11f));
    UMaterialExpressionMultiply* SunlitWater = Mul(
        ShallowColor, Const3(1.28f, 1.20f, 1.12f));
    UMaterialExpressionLinearInterpolate* VariedWaterColor = Lerp(
        WaterColor, SunlitWater, SurfaceVariationAlpha);

    // Scene-capture and scalability paths do not always retain the temporal
    // sky-reflection history used by Single Layer Water. Add a restrained
    // Fresnel sky tint to the physically shaded base so calm pools still read
    // as reflective water instead of a flat teal card. This remains
    // view-dependent and does not replace the real reflection environment.
    UMaterialExpressionFresnel* SkyFresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    SkyFresnel->Exponent = 3.2f;
    SkyFresnel->BaseReflectFraction = 0.040f;
    UMaterialExpressionMultiply* SkyReflectionAlpha = Mul(
        SkyFresnel, Scalar(TEXT("FallbackSkyReflectionStrength"), 0.32f));
    // At guide-eye grazing angles the fallback sky term can dominate the
    // darker body colour and erase the metre-scale variation above, leaving
    // calm reaches as a uniform gray card. Reuse that already-evaluated noise
    // to vary only the fallback reflection energy. This adds no sampler or
    // geometry cost and cannot invent foam or alter solver-authored flow.
    UMaterialExpression* SkyReflectionVariation = AddNode(
        Scalar(TEXT("FallbackSkyReflectionFloor"), 0.72f),
        Mul(
            SurfaceNoise,
            Scalar(TEXT("FallbackSkyReflectionVariation"), 0.28f)));
    UMaterialExpressionMultiply* VariedSkyReflectionAlpha = Mul(
        SkyReflectionAlpha, SkyReflectionVariation);
    UMaterialExpressionVectorParameter* ReflectedSkyColor = Vector(
        TEXT("ReflectedSkyColor"), FLinearColor(0.065f, 0.095f, 0.13f, 0.0f));
    UMaterialExpressionLinearInterpolate* ReflectedWaterColor = Lerp(
        VariedWaterColor, ReflectedSkyColor, VariedSkyReflectionAlpha);

    // Foam mask comes in per-vertex (grid resolution), but the old world-space
    // noise turned broad solver masks into closed cellular cracks. Multiply the
    // same authoritative mask by a project-owned flow-aligned lace field. This
    // changes only surface presentation: no texture value can create foam where
    // the conditioned solver mask is zero.
    UMaterialExpressionComponentMask* FoamMask = Mask(VertexColor, true, false, false); // R
    UMaterialExpressionComponentMask* SpeedMask = Mask(VertexColor, false, false, true); // B
    UMaterialExpressionConstant* SpeedBias = NewObject<UMaterialExpressionConstant>(Material);
    SpeedBias->R = -0.12f; Add(SpeedBias);
    UMaterialExpressionAdd* BiasedSpeed = AddNode(SpeedMask, SpeedBias);
    UMaterialExpressionMultiply* ScaledSpeed = Mul(
        BiasedSpeed, Scalar(TEXT("HydraulicWhitewaterGain"), 0.42f));
    UMaterialExpressionClamp* SpeedWhitewater =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    SpeedWhitewater->Input.Expression = ScaledSpeed;
    SpeedWhitewater->MinDefault = 0.0f;
    SpeedWhitewater->MaxDefault = 0.12f;
    UMaterialExpressionAdd* CombinedFoam = AddNode(FoamMask, SpeedWhitewater);
    UMaterialExpressionMultiply* ConditionedFoam = Mul(
        CombinedFoam, Scalar(TEXT("HydraulicFoamIntensity"), 1.0f));
    UMaterialExpressionConstant* NegativeFoamThreshold =
        NewObject<UMaterialExpressionConstant>(Material);
    NegativeFoamThreshold->R = -0.28f;
    Add(NegativeFoamThreshold);
    UMaterialExpressionMultiply* ThresholdedFoamRaw = Mul(
        AddNode(ConditionedFoam, NegativeFoamThreshold),
        Scalar(TEXT("HydraulicFoamCoverageGain"), 0.95f));
    UMaterialExpressionClamp* ThresholdedFoam =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    ThresholdedFoam->Input.Expression = ThresholdedFoamRaw;
    ThresholdedFoam->MinDefault = 0.0f;
    ThresholdedFoam->MaxDefault = 1.0f;
    UMaterialExpression* FoamBreakupSource = nullptr;
    // 2026-08-06 named human review: "the waves have no white froth." Break
    // the solver foam mask up with the river-specific organic lace, an
    // independent dense mask, and a bubble-scale organic sample at three
    // incommensurate tilings. Sparse foam shows their perforated intersection;
    // saturated foam clots the larger scales but never fills the small water
    // pockets solid. The first-party single-lace sample remains the first
    // fallback, then procedural noise.
    UTexture2D* FoamLaceTexture = LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FoamLace.T_RaftSim_SouthForkWater_FoamLace"));
    // Independent rotation, scale, curl, and thresholding turn a second sample
    // of the project-owned lace into the dense cellular layer. Keeping both
    // samples on this proven texture also avoids an optional CC0 texture
    // reference that can be unresolved during headless shader compilation.
    UTexture2D* FrothLaceDense = FoamLaceTexture;
    if (FoamLaceTexture != nullptr && FrothLaceDense != nullptr)
    {
        auto FrothSample = [&](UTexture2D* Texture, const TCHAR* ParameterName,
                               float Tiling, float RotationRadians,
                               float CurlStrength) -> UMaterialExpression* {
            UMaterialExpressionTextureCoordinate* FrothUv = Cast<
                UMaterialExpressionTextureCoordinate>(Add(
                    NewObject<UMaterialExpressionTextureCoordinate>(Material)));
            FrothUv->UTiling = Tiling;
            FrothUv->VTiling = Tiling;
            UMaterialExpressionTextureSampleParameter2D* FrothSampleNode = Cast<
                UMaterialExpressionTextureSampleParameter2D>(Add(
                    NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            FrothSampleNode->ParameterName = ParameterName;
            FrothSampleNode->Texture = Texture;
            FrothSampleNode->SamplerType = SAMPLERTYPE_Masks;
            FrothSampleNode->Coordinates.Expression = AddTurbulentFoamCoordinates(
                Material,
                AddCurrentAdvectedCoordinates(
                    Material, FrothUv, Tiling, Tiling, 1.0f,
                    TEXT("RaftSimUnifiedCurrentFoamFroth")),
                RotationRadians,
                CurlStrength,
                TEXT("RaftSimIsotropicFoamPatchCoordinates"));
            FrothSampleNode->Group = TEXT("RaftSimPhotorealWater");
            return Mask(FrothSampleNode, true, false, false);
        };
        auto CutFroth = [&](UMaterialExpression* Sample,
                            const TCHAR* BiasName, float Bias,
                            const TCHAR* GainName, float Gain)
            -> UMaterialExpression* {
            UMaterialExpressionSaturate* Cut = Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
            Cut->Input.Expression = Mul(
                AddNode(Sample, Scalar(BiasName, -Bias)),
                Scalar(GainName, Gain));
            return Cut;
        };
        UMaterialExpression* LaceLight = CutFroth(FrothSample(
            FoamLaceTexture, TEXT("WhitewaterFoamLace"),
            0.78f, 0.35f, 0.085f),
            TEXT("WhitewaterFrothLightCutBias"), 0.22f,
            TEXT("WhitewaterFrothLightCutGain"), 1.72f);
        UMaterialExpression* LaceDense = CutFroth(FrothSample(
            FrothLaceDense, TEXT("WhitewaterFrothLaceDense"),
            1.37f, -0.62f, 0.060f),
            TEXT("WhitewaterFrothDenseCutBias"), 0.20f,
            TEXT("WhitewaterFrothDenseCutGain"), 1.62f);
        UMaterialExpression* BubbleCells = CutFroth(FrothSample(
            FoamLaceTexture, TEXT("WhitewaterFrothBubbleCells"),
            3.20f, 1.02f, 0.032f),
            TEXT("WhitewaterFrothBubbleCutBias"), 0.16f,
            TEXT("WhitewaterFrothBubbleCutGain"), 1.48f);
        UMaterialExpression* BubblePerforation = Lerp(
            Scalar(TEXT("WhitewaterFrothBubbleHoleFloor"), 0.045f),
            Scalar(TEXT("WhitewaterFrothBubbleSolid"), 1.0f),
            BubbleCells);
        UMaterialExpressionSaturate* ClottedFroth =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        ClottedFroth->Input.Expression = Mul(
            Mul(
                AddNode(
                    Mul(LaceLight,
                        Scalar(TEXT("WhitewaterFrothLightPatchWeight"), 0.72f)),
                    Mul(LaceDense,
                        Scalar(TEXT("WhitewaterFrothDensePatchWeight"), 0.58f))),
                BubblePerforation),
            Scalar(TEXT("WhitewaterFrothPatchContrast"), 1.18f));
        UMaterialExpressionSaturate* FrothKnee =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        FrothKnee->Input.Expression = Mul(
            ThresholdedFoam, Scalar(TEXT("WhitewaterFrothKneeGain"), 1.60f));
        FoamBreakupSource = Lerp(
            Mul(Mul(LaceLight, LaceDense), BubblePerforation),
            ClottedFroth,
            FrothKnee);
    }
    else if (FoamLaceTexture != nullptr)
    {
        UMaterialExpressionTextureCoordinate* FoamUv = Cast<
            UMaterialExpressionTextureCoordinate>(Add(
                NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        // One tile covers 7.1 m downstream and 3.2 m across the channel.
        FoamUv->UTiling = 0.42f; FoamUv->VTiling = 0.93f;
        UMaterialExpressionTextureSampleParameter2D* FoamLaceSample = Cast<
            UMaterialExpressionTextureSampleParameter2D>(Add(
                NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        FoamLaceSample->ParameterName = TEXT("WhitewaterFoamLace");
        FoamLaceSample->Texture = FoamLaceTexture; FoamLaceSample->SamplerType = SAMPLERTYPE_Masks;
        FoamLaceSample->Coordinates.Expression = AddCurrentAdvectedCoordinates(
            Material, FoamUv, 0.42f, 0.93f, 1.0f,
            TEXT("RaftSimUnifiedCurrentFoamFallback"));
        FoamLaceSample->Group = TEXT("RaftSimPhotorealWater");
        FoamBreakupSource = Mask(FoamLaceSample, true, false, false);
    }
    else
    {
        // Solver-masked fallback keeps the material buildable after import errors.
        UMaterialExpressionNoise* FoamNoise = Cast<UMaterialExpressionNoise>(Add(
            NewObject<UMaterialExpressionNoise>(Material)));
        FoamNoise->Scale = 0.045f; FoamNoise->bTurbulence = true; FoamNoise->Levels = 5;
        FoamNoise->OutputMin = 0.0f; FoamNoise->OutputMax = 1.0f;
        FoamBreakupSource = FoamNoise;
    }
    UMaterialExpressionTextureCoordinate* FoamPatchUv = Cast<
        UMaterialExpressionTextureCoordinate>(Add(
            NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    FoamPatchUv->UTiling = 4.20f;
    FoamPatchUv->VTiling = 4.20f;
    UMaterialExpression* FoamPatchCells = AddTurbulentFoamWebMask(
        Material,
        AddTurbulentFoamCoordinates(
            Material,
            AddCurrentAdvectedCoordinates(
                Material, FoamPatchUv, 4.20f, 4.20f, 1.0f,
                TEXT("RaftSimUnifiedCurrentFoamPatchAdvection")),
            0.81f,
            0.060f,
            TEXT("RaftSimSolverFoamWebCurl")),
        TEXT("RaftSimSolverFoamConnectedWebGate"));
    UMaterialExpression* CompactFoamGate = Lerp(
        Scalar(TEXT("WhitewaterFrothPatchOutsideFloor"), 0.02f),
        Scalar(TEXT("WhitewaterFrothPatchInside"), 1.0f),
        FoamPatchCells);
    // Preserve torn lace throughout the roller. The former solid-cell refill
    // erased the internal holes and made each Voronoi island a white blob.
    // A non-zero web floor keeps adjacent tongues visually connected while
    // the solver mask remains the sole authority for where foam can exist.
    FoamBreakupSource = Mul(
        Lerp(
            Scalar(TEXT("WhitewaterFrothLaceModulationFloor"), 0.18f),
            Scalar(TEXT("WhitewaterFrothLaceModulationCeiling"), 1.0f),
            FoamBreakupSource),
        CompactFoamGate);
    UMaterialExpressionMultiply* FoamColorBreakupContrast = Mul(
        AddNode(FoamBreakupSource,
            Scalar(TEXT("HydraulicFoamColorBreakupBias"), 0.0f)),
        Scalar(TEXT("HydraulicFoamColorBreakupGain"), 0.78f));
    UMaterialExpressionClamp* FoamColorBreakup =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    FoamColorBreakup->Input.Expression = FoamColorBreakupContrast;
    FoamColorBreakup->MinDefault = 0.0f; FoamColorBreakup->MaxDefault = 1.0f;
    UMaterialExpressionMultiply* BoostedFoamColorCore = Mul(
        ThresholdedFoam,
        Scalar(TEXT("HydraulicFoamColorCoreGain"), 1.25f));
    UMaterialExpressionClamp* FoamColorCore =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    FoamColorCore->Input.Expression = BoostedFoamColorCore;
    FoamColorCore->MinDefault = 0.0f; FoamColorCore->MaxDefault = 1.0f;
    UMaterialExpressionMultiply* FoamRaw = Mul(FoamColorCore, FoamColorBreakup);
    UMaterialExpressionClamp* FoamBroken =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    FoamBroken->Input.Expression = FoamRaw; FoamBroken->MinDefault = 0.0f; FoamBroken->MaxDefault = 1.0f;
    // Froth is bright aerated white, not 48% gray — the gray constant was a
    // major cause of the "no white froth" review verdict.
    UMaterialExpressionVectorParameter* FoamColor =
        Cast<UMaterialExpressionVectorParameter>(
            Add(NewObject<UMaterialExpressionVectorParameter>(Material)));
    FoamColor->ParameterName = TEXT("WhitewaterFrothColor");
    FoamColor->DefaultValue = FLinearColor(0.88f, 0.91f, 0.92f, 1.0f);
    FoamColor->Group = TEXT("RaftSimPhotorealWater");
    UMaterialExpressionLinearInterpolate* BaseColor = Lerp(
        ReflectedWaterColor, FoamColor, FoamBroken);
    // --- Detail-normal ripples panned over the geometric wave normal --------
    UTexture2D* DetailNormal = LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FlowNormal.T_RaftSim_SouthForkWater_FlowNormal"));
    UMaterialExpression* FinalNormal = nullptr;
    // Slick/riffle patch mask; built with the detail normal, reused by the
    // roughness section so slicks stay glassy while riffled patches keep grain.
    UMaterialExpression* RiffleMask = nullptr;
    // Flow-streak lane field (-1..1); built beside the advected UVs, applied
    // by the roughness section so moving matte lanes carry the current cue.
    UMaterialExpression* FlowStreakField = nullptr;
    // Drift-foam fleck mask (0..1): sparse aperiodic lace strands advected
    // with the current. Periodic lanes and ripple shimmer are directionally
    // ambiguous to the eye (the aperture problem) — trackable flecks sliding
    // downstream are what makes real rivers read as flowing.
    UMaterialExpression* DriftFleckMask = nullptr;
    if (DetailNormal != nullptr)
    {
        UMaterialExpressionTextureCoordinate* UV =
            Cast<UMaterialExpressionTextureCoordinate>(Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        // Full-reach water UVs advance once every three metres. Keep the
        // project-owned fine-ripple field near that scale and let hydraulic
        // activity, rather than an unconditional normal gain, decide how much
        // of it reaches the shaded surface.
        UV->UTiling = 0.62f;
        UV->VTiling = 0.90f;
        UMaterialExpressionTextureCoordinate* CrossUv =
            Cast<UMaterialExpressionTextureCoordinate>(
                Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        CrossUv->UTiling = 1.31f;
        CrossUv->VTiling = 1.72f;
        // Surface detail ADVECTS with the local current instead of crawling
        // at a fixed rate: vertex colour B is speed/8 m/s and one UV tile is
        // three metres, so offsetting U by time * (B*8/3) * tiling moves the
        // ripple field downstream at the water's own speed. Drifting with
        // the current now keeps the pattern with the boat while the banks
        // slide by — the 2026-08-10 report ("the surface stays still while
        // the boat moves forward") was this missing advection.
        const auto Const = [&](float Value) -> UMaterialExpression*
        {
            UMaterialExpressionConstant* C =
                NewObject<UMaterialExpressionConstant>(Material);
            C->R = Value;
            Add(C);
            return C;
        };
        // All surface channels share the actor's continuous current integral.
        // There is no wrapping phase or velocity*absolute-time product, so a
        // flow change cannot reset the pattern and produce a white flash.
        UMaterialExpression* PhaseA = Const(0.0f);
        UMaterialExpression* PhaseB = PhaseA;
        UMaterialExpression* CycleAlpha = PhaseA;
        const auto FlowAdvectedAt = [&](UMaterialExpression* Base,
                                        float UTilingValue,
                                        float VTilingValue,
                                        float SlipFactor,
                                        UMaterialExpression*)
            -> UMaterialExpression*
        {
            return AddCurrentAdvectedCoordinates(
                Material, Base, UTilingValue, VTilingValue, SlipFactor,
                TEXT("RaftSimUnifiedCurrentWaterSurface"));
        };
        UMaterialExpression* FlowUvA =
            FlowAdvectedAt(UV, 0.62f, 0.90f, 1.0f, PhaseA);
        UMaterialExpression* FlowUvB = FlowUvA;
        UMaterialExpression* FlowCrossUvA =
            FlowAdvectedAt(CrossUv, 1.31f, 1.72f, 0.85f, PhaseA);
        UMaterialExpression* FlowCrossUvB = FlowCrossUvA;
        // Trackable roughness patches replace the former pairs of long sine
        // lanes. Those lanes survived the grazing reflection as bright,
        // parallel paint strokes. Compact advected cells still reveal the
        // current's motion, but have finite length in every direction.
        FlowStreakField = AddCellularFoamPatchMask(
            Material,
            AddTurbulentFoamCoordinates(
                Material, FlowUvA, 0.73f, 0.085f,
                TEXT("RaftSimWaterRoughnessPatchCoordinates")),
            TEXT("RaftSimWaterRoughnessPatchField"));
        if (FoamLaceTexture != nullptr)
        {
            // Two lace samples at incommensurate world scales (~14 m and
            // ~5.7 m repeats), both back-traced by the local current, so
            // their product is an aperiodic strand field that translates at
            // the water's own speed. Gain/bias carve it down to sparse
            // drift strands; squaring softens the cut edge.
            const auto DriftLace = [&](const TCHAR* ParameterName,
                                       float TilingValue,
                                       float RotationRadians,
                                       float CurlStrength,
                                       UMaterialExpression* Phase)
                -> UMaterialExpression*
            {
                UMaterialExpressionTextureCoordinate* LaceUv =
                    Cast<UMaterialExpressionTextureCoordinate>(Add(
                        NewObject<UMaterialExpressionTextureCoordinate>(
                            Material)));
                LaceUv->UTiling = TilingValue;
                LaceUv->VTiling = TilingValue;
                UMaterialExpressionTextureSampleParameter2D* Sample =
                    Cast<UMaterialExpressionTextureSampleParameter2D>(Add(
                        NewObject<UMaterialExpressionTextureSampleParameter2D>(
                            Material)));
                Sample->ParameterName = ParameterName;
                Sample->Texture = FoamLaceTexture;
                Sample->SamplerType = SAMPLERTYPE_Masks;
                Sample->Coordinates.Expression = AddTurbulentFoamCoordinates(
                    Material,
                    FlowAdvectedAt(
                        LaceUv, TilingValue, TilingValue, 1.0f, Phase),
                    RotationRadians,
                    CurlStrength,
                    TEXT("RaftSimCompactDriftFoamCoordinates"));
                Sample->Group = TEXT("RaftSimPhotorealWater");
                return Mask(Sample, true, false, false);
            };
            const auto DriftMaskAt =
                [&](UMaterialExpression* Phase,
                    const TCHAR* NameA,
                    const TCHAR* NameB) -> UMaterialExpression*
            {
                UMaterialExpression* StrandProduct = Mul(
                    DriftLace(NameA, 0.84f, 0.43f, 0.060f, Phase),
                    DriftLace(NameB, 1.75f, -0.79f, 0.035f, Phase));
                UMaterialExpressionSaturate* StrandCut =
                    NewObject<UMaterialExpressionSaturate>(Material);
                StrandCut->Input.Expression = AddNode(
                    Mul(StrandProduct, Scalar(TEXT("DriftFoamGain"), 5.0f)),
                    Mul(Const(-1.0f), Scalar(TEXT("DriftFoamBias"), 0.45f)));
                Add(StrandCut);
                return Mul(StrandCut, StrandCut);
            };
            // Bubbles are born at breaking water — holes, rock wakes — not
            // wherever water merely moves. Gate on the solver aeration
            // channel (VC.R carries Froude + breaking-evidence foam), with
            // only a high-speed residual for fast unbroken chutes. Flats
            // (0.7-0.9 m/s, zero aeration) carry no drift foam at all.
            UMaterialExpressionSaturate* ChuteGate =
                NewObject<UMaterialExpressionSaturate>(Material);
            ChuteGate->Input.Expression = AddNode(
                SpeedMask,
                Mul(Const(-1.0f),
                    Scalar(TEXT("DriftFoamSpeedFloor"), 0.22f)));
            Add(ChuteGate);
            UMaterialExpressionSaturate* DriftGate =
                NewObject<UMaterialExpressionSaturate>(Material);
            DriftGate->Input.Expression = AddNode(
                Mul(FoamMask,
                    Scalar(TEXT("DriftFoamAerationGain"), 3.0f)),
                Mul(ChuteGate,
                    Scalar(TEXT("DriftFoamSpeedGain"), 2.5f)));
            Add(DriftGate);
            // Vertex alpha is the solver wet mask: shoreline-completed and
            // dry-leveled skirt vertices carry foam-adjacent presentation
            // values but must never froth on land. Geometry upness kills
            // the strands on the near-vertical film the mesh interpolates
            // across exposed boulders.
            // VertexColor's default output is RGB (float3); wet lives on
            // the node's dedicated alpha output pin (output index 4).
            UMaterialExpressionComponentMask* WetGate =
                NewObject<UMaterialExpressionComponentMask>(Material);
            WetGate->R = true;
            WetGate->G = false;
            WetGate->B = false;
            WetGate->A = false;
            WetGate->Input.Connect(4, VertexColor);
            Add(WetGate);
            UMaterialExpressionVertexNormalWS* GeoNormal =
                NewObject<UMaterialExpressionVertexNormalWS>(Material);
            Add(GeoNormal);
            UMaterialExpressionSaturate* UpGate =
                NewObject<UMaterialExpressionSaturate>(Material);
            UpGate->Input.Expression = Mul(
                AddNode(
                    Mask(GeoNormal, false, false, true),
                    Const(-0.7f)),
                Const(5.0f));
            Add(UpGate);
            // Depth gate: the cook's foam Froude floors depth at 0.05 m,
            // so ankle-deep bank margins score whitewater-level Froude and
            // draw phantom foam strips that read as white on the shoreline
            // sand. Real foam needs real water under it (~0.25 m onset).
            UMaterialExpressionSaturate* DepthGate =
                NewObject<UMaterialExpressionSaturate>(Material);
            DepthGate->Input.Expression = Mul(
                AddNode(
                    DepthMask,
                    Mul(Const(-1.0f),
                        Scalar(TEXT("DriftFoamDepthFloor"), 0.06f))),
                Scalar(TEXT("DriftFoamDepthGain"), 9.0f));
            Add(DepthGate);
            DriftFleckMask = Mul(
                Mul(
                    Mul(
                        Lerp(
                            DriftMaskAt(PhaseA,
                                        TEXT("DriftFoamLaceA0"),
                                        TEXT("DriftFoamLaceB0")),
                            DriftMaskAt(PhaseB,
                                        TEXT("DriftFoamLaceA1"),
                                        TEXT("DriftFoamLaceB1")),
                            CycleAlpha),
                        DriftGate),
                    CompactFoamGate),
                Mul(Mul(WetGate, UpGate), DepthGate));
        }
        auto Ripple = [&](UMaterialExpression* Coordinates,
                          const TCHAR* ParameterName,
                          float SpeedX,
                          float SpeedY) -> UMaterialExpression*
        {
            UMaterialExpressionTextureSampleParameter2D* Sample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            Sample->ParameterName = ParameterName;
            Sample->Texture = DetailNormal;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = Coordinates;
            Sample->Group = TEXT("RaftSimPhotorealWater");
            return Sample;
        };
        // Residual panner speeds are only the churn RELATIVE to the moving
        // water; bulk downstream motion comes from the cycled advected UVs
        // (each phase pair crossfaded so the reset jump never shows).
        UMaterialExpression* PrimaryNormal = Lerp(
            Ripple(FlowUvA, TEXT("WaterFlowNormalPrimaryA"), 0.020f, 0.012f),
            Ripple(FlowUvB, TEXT("WaterFlowNormalPrimaryB"), 0.020f, 0.012f),
            CycleAlpha);
        UMaterialExpression* CrossNormal = Lerp(
            Ripple(FlowCrossUvA, TEXT("WaterFlowNormalCrossA"), -0.014f, 0.026f),
            Ripple(FlowCrossUvB, TEXT("WaterFlowNormalCrossB"), -0.014f, 0.026f),
            CycleAlpha);
        UMaterialExpression* CrossPerturbation = AddNode(
            CrossNormal, Const3(0.0f, 0.0f, -1.0f));
        // Third, fine octave (~0.75 m repeat): the two base octaves repeat
        // at ~5 m and ~2.3 m, leaving the first few metres around the
        // camera with no detail frequency at all — the near-field water
        // stayed a smooth mirror sheet regardless of normal strength.
        UMaterialExpressionTextureCoordinate* FineUvCoord =
            Cast<UMaterialExpressionTextureCoordinate>(Add(
                NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        FineUvCoord->UTiling = 4.0f;
        FineUvCoord->VTiling = 5.3f;
        UMaterialExpression* FineUvA =
            FlowAdvectedAt(FineUvCoord, 4.0f, 5.3f, 1.0f, PhaseA);
        UMaterialExpression* FineUvB = FineUvA;
        UMaterialExpression* FineNormal = Lerp(
            Ripple(FineUvA, TEXT("WaterFlowNormalFineA"), 0.031f, -0.022f),
            Ripple(FineUvB, TEXT("WaterFlowNormalFineB"), 0.031f, -0.022f),
            CycleAlpha);
        UMaterialExpression* FinePerturbation = AddNode(
            Mul(FineNormal, Const3(0.6f, 0.6f, 0.6f)),
            Const3(0.0f, 0.0f, -0.6f));
        // Analytic wave normals: texture-sourced ripples mip-collapse to a
        // flat mirror at grazing angles no matter their strength — the
        // near-field water around a chase camera stayed one smooth pale
        // sheet through every texture-side fix. Procedural sine slopes
        // have no mips and survive every angle; they ride the same cycled
        // advected UVs, so they translate with the current like the rest
        // of the surface detail.
        const auto AnalyticSlopeAt =
            [&](UMaterialExpression* Uv) -> UMaterialExpression*
        {
            const auto SlopeWave = [&](float CyclesU, float CyclesV,
                                       float Amplitude)
                -> UMaterialExpression*
            {
                UMaterialExpressionSine* WaveSine =
                    NewObject<UMaterialExpressionSine>(Material);
                WaveSine->Period = 1.0f;
                WaveSine->Input.Expression = AddNode(
                    AddNode(
                        Mul(Mask(Uv, true, false, false), Const(CyclesU)),
                        Mul(Mask(Uv, false, true, false), Const(CyclesV))),
                    Const(0.25f));
                Add(WaveSine);
                UMaterialExpressionAppendVector* SlopeDir =
                    Cast<UMaterialExpressionAppendVector>(Add(
                        NewObject<UMaterialExpressionAppendVector>(
                            Material)));
                const float Norm = FMath::Sqrt(
                    CyclesU * CyclesU + CyclesV * CyclesV);
                SlopeDir->A.Expression = Const(CyclesU / Norm * Amplitude);
                SlopeDir->B.Expression = Const(CyclesV / Norm * Amplitude);
                return Mul(WaveSine, SlopeDir);
            };
            // Balanced crossing directions form short, interacting chop.
            // The previous two nearly downstream directions produced long
            // specular ribbons that viewers understandably read as white
            // streaks rather than wave faces.
            UMaterialExpression* CrossingChop = AddNode(
                AddNode(
                    SlopeWave(2.6f, 1.8f, 0.18f),
                    SlopeWave(-1.4f, 3.2f, 0.16f)),
                AddNode(
                    SlopeWave(4.1f, -2.7f, 0.12f),
                    SlopeWave(0.8f, 5.3f, 0.10f)));
            UMaterialExpression* ChopCells = AddCellularFoamPatchMask(
                Material,
                AddTurbulentFoamCoordinates(
                    Material, Uv, -0.51f, 0.075f,
                    TEXT("RaftSimCrossingChopPatchCoordinates")),
                TEXT("RaftSimCrossingChopPatchField"));
            return Mul(
                CrossingChop,
                Lerp(Const(0.22f), Const(1.0f), ChopCells));
        };
        // The analytic sinusoids are only a bounded anti-mip fallback. At full
        // amplitude their infinite phase lines become bright perspective
        // streaks and cross-channel bars. Real rapid shape is supplied by the
        // solver/obstacle geometry; retain only a faint, parameterized residue
        // for platforms that completely lose the normal-map mip.
        UMaterialExpression* AnalyticSlopeXy = Mul(
            Lerp(AnalyticSlopeAt(FlowUvA), AnalyticSlopeAt(FlowUvB), CycleAlpha),
            Scalar(TEXT("AnalyticChopStrength"), 0.08f));
        UMaterialExpressionAppendVector* AnalyticSlope3 =
            Cast<UMaterialExpressionAppendVector>(Add(
                NewObject<UMaterialExpressionAppendVector>(Material)));
        AnalyticSlope3->A.Expression = AnalyticSlopeXy;
        AnalyticSlope3->B.Expression = Const(0.0f);
        // Steepness boost: the authored flow-normal texture averages only
        // ±6% slope, and grazing-angle foreshortening crushes that to a
        // perfect mirror — the sky corridor between the tree reflections
        // rendered as one smooth white sheet no strength scalar could
        // break. Amplifying the tangent XY of the sampled ripples steepens
        // the actual wave slopes so the grazing reflection shatters into
        // moving glints.
        UMaterialExpression* SteepenedRipples = Mul(
            AddNode(
                AddNode(AddNode(PrimaryNormal, CrossPerturbation),
                        FinePerturbation),
                AnalyticSlope3),
            Const3(1.0f, 1.0f, 0.0f));
        UMaterialExpression* RippleXy = Mul(
            SteepenedRipples,
            Scalar(TEXT("FlowNormalSteepness"), 2.8f));
        UMaterialExpressionNormalize* CombinedNormal =
            Cast<UMaterialExpressionNormalize>(
                Add(NewObject<UMaterialExpressionNormalize>(Material)));
        CombinedNormal->VectorInput.Expression = AddNode(
            RippleXy, Const3(0.0f, 0.0f, 1.0f));
        // A single 0.22 normal scalar previously gave ordinary current nearly
        // the same microfacet energy as aerated rapids. At guide-eye grazing
        // angles that field converged into camera-radial grooves. Keep calm
        // water subtle and add bounded normal response only from solver-authored
        // foam and speed channels.
        UMaterialExpression* HydraulicNormalStrength = AddNode(
            AddNode(
                Scalar(TEXT("CalmRippleStrength"), 0.035f),
                Mul(FoamMask, Scalar(TEXT("FoamRippleStrength"), 0.085f))),
            Mul(SpeedMask, Scalar(TEXT("FlowRippleStrength"), 0.045f)));
        UMaterialExpressionClamp* NormalStrength =
            Cast<UMaterialExpressionClamp>(
                Add(NewObject<UMaterialExpressionClamp>(Material)));
        NormalStrength->Input.Expression = HydraulicNormalStrength;
        NormalStrength->MinDefault = 0.0f;
        // Ceiling raised 0.14 -> 0.30 (2026-08-14): at 0.14 the presentation
        // ripple weights saturated everywhere, erasing the calm-vs-rapid
        // contrast they encode. Grazing and slick filters below remain the
        // anti-groove guards; the ceiling only bounds worst-case aeration.
        NormalStrength->MaxDefault = 0.30f;
        // Repeated normal detail can collapse into long view-aligned specular
        // streaks when a guide-eye camera sees the river at a grazing angle.
        // Preserve the authored ripple response nearby and at steeper views,
        // but converge toward a small physical rough-water floor as Fresnel
        // approaches one. Hydraulic mesh displacement and foam are unchanged.
        UMaterialExpressionConstant3Vector* FlatN = Const3(0.0f, 0.0f, 1.0f);
        UMaterialExpressionFresnel* RippleGrazingFresnel =
            Cast<UMaterialExpressionFresnel>(
                Add(NewObject<UMaterialExpressionFresnel>(Material)));
        RippleGrazingFresnel->Exponent = 1.4f;
        RippleGrazingFresnel->BaseReflectFraction = 0.0f;
        RippleGrazingFresnel->Normal.Expression = FlatN;
        UMaterialExpression* GrazingFilteredNormalStrength = Lerp(
            NormalStrength,
            // Raised 0.25 -> 0.80 (2026-08-16): the low floor stripped
            // nearly all wave normals from the grazing zone, so the sky
            // corridor between the tree-line reflections rendered as one
            // smooth white sheet from chase cameras ("broad white texture,
            // no wave"). The camera-radial grooves this floor guarded
            // against came from the unbounded advection shear, fixed by
            // flowmap cycling — the heavy guard is no longer needed.
            Mul(NormalStrength, Scalar(TEXT("RippleGrazingFloor"), 0.12f)),
            RippleGrazingFresnel);
        // Wind-riffle patches vs slicks: real rivers alternate between glassy
        // slicks and wind/current-textured patches at the ten-metre scale —
        // the single most recognisable natural variation on moving water. One
        // low-frequency world-space mask suppresses the detail ripple inside
        // slicks (the same mask glosses roughness below). Contrast-remapped so
        // patches have readable edges rather than a smooth gradient.
        UMaterialExpressionNoise* RifflePatchNoise =
            Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
        RifflePatchNoise->Scale = 0.00085f;
        RifflePatchNoise->bTurbulence = true;
        RifflePatchNoise->Levels = 2;
        RifflePatchNoise->OutputMin = -0.9f;
        RifflePatchNoise->OutputMax = 2.1f;
        UMaterialExpressionClamp* RiffleMaskClamp =
            Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
        RiffleMaskClamp->Input.Expression = RifflePatchNoise;
        RiffleMaskClamp->MinDefault = 0.0f;
        RiffleMaskClamp->MaxDefault = 1.0f;
        RiffleMask = RiffleMaskClamp;
        UMaterialExpression* SlickFilteredNormalStrength = Lerp(
            Mul(GrazingFilteredNormalStrength, Scalar(TEXT("SlickNormalFloor"), 0.55f)),
            GrazingFilteredNormalStrength,
            RiffleMask);
        FinalNormal = Lerp(FlatN, CombinedNormal, SlickFilteredNormalStrength);

    }

    // --- Roughness: glassy water, rougher in foam; Fresnel-lifted specular ---
    // Slicks read glassier than riffled patches; foam stays rough either way.
    UMaterialExpressionScalarParameter* BaseRough = Scalar(TEXT("WaterRoughness"), 0.24f);
    UMaterialExpression* PatchedRough = BaseRough;
    if (RiffleMask != nullptr)
    {
        PatchedRough = Lerp(
            Mul(BaseRough, Scalar(TEXT("SlickRoughnessScale"), 0.45f)),
            BaseRough,
            RiffleMask);
    }
    UMaterialExpressionScalarParameter* FoamRoughScale = Scalar(TEXT("FoamRoughness"), 0.55f);
    UMaterialExpressionMultiply* FoamRough = Mul(FoamBroken, FoamRoughScale);
    UMaterialExpressionAdd* Roughness = AddNode(PatchedRough, FoamRough);

    // --- Flow streaks: moving roughness lanes riding the advected UVs so
    // current reads on glassy water. A boat held against the current must
    // see the surface slide downstream; the flow-normal texture's ~6% slopes
    // vanish under the fresnel mirror, but matte streaks crossing that
    // mirror do not. Amplitude scales with the vertex speed channel so
    // pools stay glass.
    if (FlowStreakField != nullptr)
    {
        // SpeedMask is speed/8 m/s; ordinary current sits near 0.1 and
        // would mute the lanes to nothing if used raw. Saturate a 5x gain
        // instead so the gate reaches full strength by ~1.6 m/s while dead
        // pools still zero out.
        UMaterialExpressionSaturate* StreakSpeedGate =
            NewObject<UMaterialExpressionSaturate>(Material);
        StreakSpeedGate->Input.Expression = Mul(
            SpeedMask, Scalar(TEXT("FlowStreakSpeedGain"), 5.0f));
        Add(StreakSpeedGate);
        // No grazing fade here — analytic roughness lanes are the ONE
        // texture that survives grazing angles (reflection-based detail
        // cannot: the mirror shows the featureless horizon sky, and
        // re-aiming rays inside a uniform region changes nothing).
        Roughness = AddNode(
            Roughness,
            Mul(FlowStreakField,
                Mul(StreakSpeedGate,
                    Scalar(TEXT("FlowStreakRoughness"), 0.22f))));
    }
    // Grazing roughness boost: diffuse the near-field mirror so the pale
    // sky corridor between the tree-line reflections stops rendering as
    // one smooth white sheet ("broad white texture" from chase cameras).
    // A rougher grazing surface blends sky with surroundings and lets the
    // lane texture carry the water read.
    {
        UMaterialExpressionFresnel* GrazingRoughFresnel =
            Cast<UMaterialExpressionFresnel>(
                Add(NewObject<UMaterialExpressionFresnel>(Material)));
        GrazingRoughFresnel->Exponent = 2.2f;
        GrazingRoughFresnel->BaseReflectFraction = 0.0f;
        GrazingRoughFresnel->Normal.Expression = Const3(0.0f, 0.0f, 1.0f);
        Roughness = AddNode(
            Roughness,
            Mul(GrazingRoughFresnel,
                Scalar(TEXT("GrazingRoughnessBoost"), 0.22f)));
    }
    if (DriftFleckMask != nullptr)
    {
        Roughness = AddNode(
            Roughness,
            Mul(DriftFleckMask, Scalar(TEXT("DriftFoamRoughness"), 0.45f)));
    }

    UMaterialExpressionFresnel* Fresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    Fresnel->Exponent = 5.0f;
    Fresnel->BaseReflectFraction = 0.02f;
    UMaterialExpressionScalarParameter* SpecBase = Scalar(TEXT("Specular"), 0.34f);
    UMaterialExpression* Specular = AddNode(
        SpecBase, Mul(Fresnel, Scalar(TEXT("FresnelSpecular"), 0.18f)));
    if (DriftFleckMask != nullptr)
    {
        // Foam occludes the mirror: a scattering white patch has almost no
        // coherent specular, and suppressing it here is what finally makes
        // the strands sit ON the surface instead of shading beneath the
        // grazing-angle reflection.
        Specular = Lerp(
            Specular,
            Scalar(TEXT("DriftFoamSpecular"), 0.03f),
            DriftFleckMask);
    }

    // Shallow-margin de-gloss: the terrain-clipped shoreline keeps water down
    // to a few millimetres of depth, and Single Layer Water renders that
    // margin with no volume tint at all — a pure mirror coat over the visible
    // bank. On a gentle bank the sub-decimetre zone is metres wide, so every
    // shore wears a broad glossy film ("I still see the shiny texture on the
    // shore", player screenshots 2026-08-27/28), strongest at the grazing
    // angles a seated guide actually sees. Real ankle-deep water over
    // sediment reads as damp ground, not chrome. Drive the margin toward a
    // matte wet-sediment response with the same solver-authored depth channel
    // the foam gates use (VC.G = depth / 2.5 m): matte below ~7 cm of water,
    // authored gloss restored by ~20 cm.
    UMaterialExpressionConstant* ShoreMarginMinusOne =
        NewObject<UMaterialExpressionConstant>(Material);
    ShoreMarginMinusOne->R = -1.0f;
    Add(ShoreMarginMinusOne);
    UMaterialExpressionSaturate* WetMarginGate =
        NewObject<UMaterialExpressionSaturate>(Material);
    WetMarginGate->Input.Expression = Mul(
        AddNode(
            EffectiveDepthMask,
            Mul(ShoreMarginMinusOne,
                Scalar(TEXT("ShoreMarginDepthFloor"), 0.028f))),
        Scalar(TEXT("ShoreMarginDepthGain"), 18.0f));
    Add(WetMarginGate);
    UMaterialExpression* RoughnessOutput = Lerp(
        Scalar(TEXT("ShoreMarginRoughness"), 0.58f),
        Roughness,
        WetMarginGate);
    Specular = Lerp(
        Scalar(TEXT("ShoreMarginSpecular"), 0.07f),
        Specular,
        WetMarginGate);

    // Single Layer Water opacity controls how much light enters the volume.
    // A low global value exposed the pale riverbed across the full guide view,
    // making the moving normal atlas read as a frosted sheet. Preserve useful
    // shallow-water visibility, but use the solver-authored depth channel to
    // attenuate deeper runs and make aerated whitewater nearly opaque.
    UMaterialExpressionScalarParameter* ShallowOpacity =
        Scalar(TEXT("ShallowWaterOpacity"), 0.62f);
    UMaterialExpressionScalarParameter* DeepOpacity =
        Scalar(TEXT("DeepWaterOpacity"), 0.80f);
    UMaterialExpressionLinearInterpolate* DepthOpacity =
        Lerp(ShallowOpacity, DeepOpacity, EffectiveDepthMask);
    UMaterialExpressionScalarParameter* FoamOpacity =
        Scalar(TEXT("FoamWaterOpacity"), 0.90f);
    UMaterialExpressionLinearInterpolate* Opacity =
        Lerp(DepthOpacity, FoamOpacity, FoamBroken);
    UMaterialExpressionScalarParameter* Metallic = Scalar(TEXT("Metallic"), 0.0f);

    // --- Wire the material outputs ------------------------------------------
    UMaterialExpression* BaseColorOut = BaseColor;
    if (DriftFleckMask != nullptr)
    {
        // Drift strands tint toward the froth colour so the trackable
        // features are visible in any light, not only in specular zones.
        // Kept modest: in Single Layer Water the base colour shades under
        // the reflection layer and reads as submerged — the surface-foam
        // read comes from the emissive term wired below, which composites
        // on top of the mirror the way real drift foam occludes it.
        BaseColorOut = Lerp(
            BaseColorOut,
            FoamColor,
            Mul(DriftFleckMask, Scalar(TEXT("DriftFoamOpacity"), 0.35f)));
    }
    // Boat-wake surface response: UV2 carries the carrier's actual signed
    // wake field (x = coverage, y = signed height / 11 cm). The Kelvin arms
    // displace this mesh and their slopes are already folded into the
    // vertex normals, so the ripple reads through moving specular — the
    // material adds only the faintest gloss break so the arcs stay legible
    // when the reflection happens to be featureless. The first pass used
    // 0.30 roughness plus a foam-colour tint, and under a bright sky those
    // bands read as white aerated water ("the wake is appearing as white
    // aerated water, it should just be a ripple", player recording
    // 2026-08-31); a displacement wake must stay a clear lateral wave, so
    // there is no colour term at all now.
    UMaterialExpressionTextureCoordinate* BoatWakeUv =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    BoatWakeUv->CoordinateIndex = 2;
    BoatWakeUv->Desc = TEXT("RaftSimBoatWakeGeometryUV2");
    UMaterialExpressionComponentMask* BoatWakeCoverage =
        Mask(BoatWakeUv, true, false, false);
    RoughnessOutput = AddNode(
        RoughnessOutput,
        Mul(BoatWakeCoverage, Scalar(TEXT("BoatWakeRoughness"), 0.06f)));
    // Live-level shore clip (static tiles only): the terrain-clipped water
    // meshes are cooked at one flow band, but the release schedule moves
    // the live level through the day, so on a low morning their glossy
    // sheet kept rendering metres above the real waterline ("the shiny
    // water texture runs over the left bank ... the shiny surface and the
    // water coloured surface meet the bank at different places",
    // 2026-09-01). The runtime publishes live-minus-cooked level near the
    // raft; recompute this pixel's cooked depth (VC.G stores depth/2.5 on
    // the static cook) against today's level and retire everything the
    // cook placed above it — transmissive, matte, colourless, so the bank
    // simply shows through. The live carrier follows the solver by
    // construction and keeps the clip disabled via its dynamic instance.
    UMaterialExpression* OpacityOut = Opacity;
    if (UMaterialExpression* LiveLevelDeltaM = AddFoamCollectionScalarExpression(
            Material, TEXT("RaftSimLiveWaterLevelDeltaM")))
    {
        UMaterialExpressionScalarParameter* ShoreClipEnabled =
            Scalar(TEXT("ApplyLiveLevelShoreClip"), 0.0f);
        UMaterialExpressionConstant* CookedDepthBasis =
            NewObject<UMaterialExpressionConstant>(Material);
        CookedDepthBasis->R = 2.5f;
        Add(CookedDepthBasis);
        UMaterialExpressionConstant* ClipFeatherInv =
            NewObject<UMaterialExpressionConstant>(Material);
        ClipFeatherInv->R = 1.0f / 0.06f;
        Add(ClipFeatherInv);
        UMaterialExpressionConstant* FullyKept =
            NewObject<UMaterialExpressionConstant>(Material);
        FullyKept->R = 1.0f;
        Add(FullyKept);
        UMaterialExpressionSaturate* LiveDepthGate =
            NewObject<UMaterialExpressionSaturate>(Material);
        LiveDepthGate->Input.Expression = Mul(
            AddNode(Mul(DepthMask, CookedDepthBasis), LiveLevelDeltaM),
            ClipFeatherInv);
        Add(LiveDepthGate);
        UMaterialExpressionLinearInterpolate* ShoreClipAlpha =
            Lerp(FullyKept, LiveDepthGate, ShoreClipEnabled);
        OpacityOut = Mul(OpacityOut, ShoreClipAlpha);
        Specular = Mul(Specular, ShoreClipAlpha);
        UMaterialExpressionConstant* DrainedRoughness =
            NewObject<UMaterialExpressionConstant>(Material);
        DrainedRoughness->R = 0.9f;
        Add(DrainedRoughness);
        RoughnessOutput = Lerp(DrainedRoughness, RoughnessOutput, ShoreClipAlpha);
        BaseColorOut = Mul(BaseColorOut, ShoreClipAlpha);
        if (DriftFleckMask != nullptr)
        {
            DriftFleckMask = Mul(DriftFleckMask, ShoreClipAlpha);
        }
    }
    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, BaseColorOut);
    // A displacement-hull boat wake carries NO whitening: a paddled raft
    // pushes water aside without aerating it, so white stays exclusive to
    // breaking water (solver aeration: rapids and obstruction wakes). The
    // boat wake lives as geometry plus the roughness/tint response above.
    if (DriftFleckMask != nullptr)
    {
        Ed->EmissiveColor.Connect(
            0,
            Mul(FoamColor,
                Mul(DriftFleckMask,
                    Scalar(TEXT("DriftFoamSurfaceGlow"), 0.40f))));
    }
    Ed->Metallic.Connect(0, Metallic);
    Ed->Specular.Connect(0, Specular);
    Ed->Roughness.Connect(0, RoughnessOutput);
    Ed->Opacity.Connect(0, OpacityOut);
    if (FinalNormal != nullptr)
    {
        Ed->Normal.Connect(0, FinalNormal);
    }

    // Single Layer Water requires the SingleLayerWaterMaterialOutput node,
    // which supplies the volumetric scattering/absorption of the water body.
    UMaterialExpressionSingleLayerWaterMaterialOutput* WaterOutput =
        Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(
            Add(NewObject<UMaterialExpressionSingleLayerWaterMaterialOutput>(Material)));
    // Coefficients are inverse centimetres. These values attenuate over metres
    // while holding the green/blue channels close enough to reproduce the
    // source river's gray-green appearance. All three channels remain strong
    // enough to hide the pale procedural riverbed in guide-eye views; red
    // still falls off first and blue carries slightly farther, but no channel
    // is allowed to turn a calm pool into tropical emerald or cyan water.
    UMaterialExpressionVectorParameter* Scattering =
        Vector(TEXT("WaterScattering"), FLinearColor(0.00012f, 0.00014f, 0.00016f, 0.0f));
    UMaterialExpressionVectorParameter* Absorption =
        Vector(TEXT("WaterAbsorption"), FLinearColor(0.0065f, 0.0052f, 0.0046f, 0.0f));
    UMaterialExpressionScalarParameter* PhaseG = Scalar(TEXT("WaterPhaseG"), 0.15f);
    UMaterialExpressionVectorParameter* BehindWaterScale = Vector(
        TEXT("RiverbedColorScale"), FLinearColor(0.16f, 0.17f, 0.17f, 0.0f));
    // Aeration: entrained bubbles scatter light strongly, so whitewater is
    // milky through the water BODY, not only painted on the surface. Blend the
    // volumetric scattering toward a near-white aerated coefficient wherever
    // the surface carries foam (with a smaller fast-water contribution), so a
    // hole's white pile keeps its optical depth when a swimmer or the camera
    // looks into it. Per-pixel, presentation only.
    UMaterialExpressionVectorParameter* AeratedScattering = Vector(
        TEXT("AeratedWaterScattering"), FLinearColor(0.052f, 0.058f, 0.060f, 0.0f));
    UMaterialExpressionMultiply* SpeedAeration =
        Mul(SpeedMask, Scalar(TEXT("SpeedAerationFraction"), 0.22f));
    UMaterialExpressionAdd* AerationRaw = AddNode(FoamBroken, SpeedAeration);
    UMaterialExpressionClamp* AerationMask =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    AerationMask->Input.Expression = AerationRaw;
    AerationMask->MinDefault = 0.0f;
    AerationMask->MaxDefault = 1.0f;
    UMaterialExpressionLinearInterpolate* AeratedScatteringBlend =
        Lerp(Scattering, AeratedScattering, AerationMask);
    WaterOutput->ScatteringCoefficients.Expression = AeratedScatteringBlend;
    WaterOutput->AbsorptionCoefficients.Expression = Absorption;
    WaterOutput->PhaseG.Expression = PhaseG;
    WaterOutput->ColorScaleBehindWater.Expression = BehindWaterScale;

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    FAssetCompilingManager::Get().FinishAllCompilation();

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim: %s saved=%d"),
        ObjectName,
        bSaved ? 1 : 0);
    return Material;
}

UMaterial* BuildLiveRiverSurfaceMaterial()
{
    static const TCHAR* AssetName = TEXT("M_RaftSim_LiveRiverSurface");
    static const TCHAR* PackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface.M_RaftSim_LiveRiverSurface");
    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, ObjectPath));
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (!Material)
    {
        return nullptr;
    }

    UMaterialParameterCollection* FoamOcclusionCollection =
        LoadObject<UMaterialParameterCollection>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/MPC_RaftSim_RaftFoamOcclusion."
                 "MPC_RaftSim_RaftFoamOcclusion"));
    if (!FoamOcclusionCollection)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim: live river material is missing raft occlusion parameters"));
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Translucent;
    // Volumetric non-directional, deliberately NOT per-pixel surface
    // lighting: the overlay floats just above the authored water, and with
    // per-pixel lighting it received its own crisp copy of every dynamic
    // shadow — crew shadows projected twice at offset heights whenever the
    // two surfaces diverged. The single true shadow belongs to the opaque
    // Single Layer Water underneath; the overlay's froth reads through its
    // emissive term regardless.
    Material->TranslucencyLightingMode = TLM_VolumetricNonDirectional;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);

    auto Add = [&](UMaterialExpression* Expression) -> UMaterialExpression*
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Const3 = [&](float R, float G, float B) -> UMaterialExpressionConstant3Vector*
    {
        UMaterialExpressionConstant3Vector* Expression =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        Expression->Constant = FLinearColor(R, G, B, 1.0f);
        return Cast<UMaterialExpressionConstant3Vector>(Add(Expression));
    };
    auto Vector = [&](const TCHAR* Name, const FLinearColor& Value)
        -> UMaterialExpressionVectorParameter*
    {
        UMaterialExpressionVectorParameter* Expression =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimLiveWater");
        return Cast<UMaterialExpressionVectorParameter>(Add(Expression));
    };
    auto Scalar = [&](const TCHAR* Name, float Value) -> UMaterialExpressionScalarParameter*
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimLiveWater");
        return Cast<UMaterialExpressionScalarParameter>(Add(Expression));
    };
    auto Mask = [&](UMaterialExpression* Input, bool R, bool G, bool B, bool A = false)
        -> UMaterialExpressionComponentMask*
    {
        UMaterialExpressionComponentMask* Expression =
            NewObject<UMaterialExpressionComponentMask>(Material);
        Expression->Input.Expression = Input;
        Expression->R = R;
        Expression->G = G;
        Expression->B = B;
        Expression->A = A;
        return Cast<UMaterialExpressionComponentMask>(Add(Expression));
    };
    auto Mul = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionMultiply*
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionMultiply>(Add(Expression));
    };
    auto AddNode = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionAdd*
    {
        UMaterialExpressionAdd* Expression = NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionAdd>(Add(Expression));
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B, UMaterialExpression* Alpha)
        -> UMaterialExpressionLinearInterpolate*
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        return Cast<UMaterialExpressionLinearInterpolate>(Add(Expression));
    };

    UMaterialExpressionVertexColor* VertexColor =
        Cast<UMaterialExpressionVertexColor>(Add(NewObject<UMaterialExpressionVertexColor>(Material)));
    UMaterialExpressionComponentMask* FoamMask = Mask(VertexColor, true, false, false);
    UMaterialExpressionComponentMask* DepthMask = Mask(VertexColor, false, true, false);
    UMaterialExpressionComponentMask* SpeedMask = Mask(VertexColor, false, false, true);
    // UV2.x is a localized scalar derived from the actual signed wake
    // displacement on the procedural mesh. It only reveals that displaced
    // geometry; no wake image, normal map, or screen-space decal is sampled.
    UMaterialExpressionTextureCoordinate* PaddleWakeMeshData =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    PaddleWakeMeshData->CoordinateIndex = 2;
    PaddleWakeMeshData->Desc = TEXT("RaftSimPaddleWakeGeometryUV2");
    UMaterialExpressionComponentMask* PaddleWakeCoverage =
        Mask(PaddleWakeMeshData, true, false, false);
    UMaterialExpressionComponentMask* PaddleWakeSignedHeight =
        Mask(PaddleWakeMeshData, false, true, false);
    UMaterialExpressionComponentMask* StationEdgeCoverage =
        Mask(VertexColor, true, false, false);
    // VertexColor's default expression output is RGB. Alpha is UE's dedicated
    // scalar output 4, so select it before applying the component mask. Trying
    // to mask A from output 0 compiles in C++ but fails the Metal material.
    StationEdgeCoverage->Input.OutputIndex = 4;
    // The live detail layer is translucent and spans the moving solver window.
    // Without a per-pixel hull cutout Unreal can sort that whole component in
    // front of the raft, making a correctly buoyant boat look submerged. Reuse
    // the runtime foam-occlusion transform, but fit this ellipse to the actual
    // 4.3 x 2.0 m tube silhouette so advecting detail remains visible beside it.
    auto CollectionParameter =
        [Material, FoamOcclusionCollection, &Add](FName Name, bool bScalar)
            -> UMaterialExpressionCollectionParameter*
    {
        UMaterialExpressionCollectionParameter* Expression =
            NewObject<UMaterialExpressionCollectionParameter>(Material);
        Expression->Collection = FoamOcclusionCollection;
        Expression->ParameterName = Name;
        Expression->ExpressionGUID = FGuid::NewGuid();
        const int32 ParameterIndex = bScalar
            ? FoamOcclusionCollection->ScalarParameters.IndexOfByPredicate(
                [Name](const FCollectionScalarParameter& Parameter)
                {
                    return Parameter.ParameterName == Name;
                })
            : FoamOcclusionCollection->VectorParameters.IndexOfByPredicate(
                [Name](const FCollectionVectorParameter& Parameter)
                {
                    return Parameter.ParameterName == Name;
                });
        if (ParameterIndex != INDEX_NONE)
        {
            Expression->ParameterId = bScalar
                ? FoamOcclusionCollection->ScalarParameters[ParameterIndex].Id
                : FoamOcclusionCollection->VectorParameters[ParameterIndex].Id;
        }
        return Cast<UMaterialExpressionCollectionParameter>(Add(Expression));
    };
    UMaterialExpressionWorldPosition* RaftMaskWorldPosition =
        Cast<UMaterialExpressionWorldPosition>(
            Add(NewObject<UMaterialExpressionWorldPosition>(Material)));
    UMaterialExpressionCollectionParameter* RaftMaskEnabled =
        CollectionParameter(TEXT("RaftFoamExclusionEnabled"), true);
    UMaterialExpressionCollectionParameter* RaftMaskCenter =
        CollectionParameter(
            TEXT("RaftFoamExclusionCenterAndHalfWidthCm"), false);
    UMaterialExpressionCollectionParameter* RaftMaskForward =
        CollectionParameter(
            TEXT("RaftFoamExclusionForwardAndHalfLengthCm"), false);
    UMaterialExpressionCustom* RaftHullExclusion =
        Cast<UMaterialExpressionCustom>(
            Add(NewObject<UMaterialExpressionCustom>(Material)));
    RaftHullExclusion->Description =
        TEXT("RaftSimLiveSurfaceRaftHullExclusion");
    RaftHullExclusion->OutputType = CMOT_Float1;
    RaftHullExclusion->Code = TEXT(
        "float2 Delta = WorldPosition.xy - CenterAndHalfWidth.xy;\n"
        "float2 Forward = normalize(ForwardAndHalfLength.xy + float2(1e-5, 0.0));\n"
        "float Along = dot(Delta, Forward) / max(ForwardAndHalfLength.w * 0.72, 1.0);\n"
        "float Across = dot(Delta, float2(-Forward.y, Forward.x)) / max(CenterAndHalfWidth.w * 0.58, 1.0);\n"
        "float EllipseSquared = Along * Along + Across * Across;\n"
        "float OutsideHull = smoothstep(0.72, 1.30, EllipseSquared);\n"
        "return lerp(1.0, OutsideHull, saturate(Enabled));");
    auto AddRaftMaskInput = [RaftHullExclusion](
        FName Name, UMaterialExpression* Expression)
    {
        FCustomInput Input;
        Input.InputName = Name;
        Input.Input.Expression = Expression;
        RaftHullExclusion->Inputs.Add(Input);
    };
    AddRaftMaskInput(TEXT("WorldPosition"), RaftMaskWorldPosition);
    AddRaftMaskInput(TEXT("CenterAndHalfWidth"), RaftMaskCenter);
    AddRaftMaskInput(TEXT("ForwardAndHalfLength"), RaftMaskForward);
    AddRaftMaskInput(TEXT("Enabled"), RaftMaskEnabled);

    // The underlying authored Single Layer Water includes volume scattering
    // and scene reflection, while this non-transmitting solver overlay is an
    // ordinary surface-lit alpha overlay. Its previous near-black constants made the
    // moving 240 m window visibly darker than the same river immediately
    // beyond it. These calibrated gray-green surface-radiance values and a
    // restrained Fresnel sky response match the underlying water without
    // reintroducing a second transmitting volume.
    UMaterialExpressionLinearInterpolate* DepthColor = Lerp(
        Vector(
            TEXT("LiveShallowSurfaceColor"),
            FLinearColor(0.115f, 0.185f, 0.175f, 1.0f)),
        Vector(
            TEXT("LiveDeepSurfaceColor"),
            FLinearColor(0.035f, 0.080f, 0.095f, 1.0f)),
        DepthMask);
    UMaterialExpressionFresnel* LiveSkyFresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    LiveSkyFresnel->Exponent = 4.2f;
    LiveSkyFresnel->BaseReflectFraction = 0.018f;
    UMaterialExpressionMultiply* LiveSkyReflectionAlpha = Mul(
        LiveSkyFresnel, Scalar(TEXT("LiveSkyReflectionStrength"), 0.62f));
    UMaterialExpressionLinearInterpolate* ReflectedDepthColor = Lerp(
        DepthColor,
        Vector(
            TEXT("LiveReflectedSkyColor"),
            FLinearColor(0.160f, 0.230f, 0.280f, 1.0f)),
        LiveSkyReflectionAlpha);

    // Whitewater froth: the 2026-08-06 named human review rejected the flat
    // noise-tinted foam ("waves have no white froth"). Break the solver's
    // advected foam channel up with the river-specific organic lace and an
    // independent CC0 dense mask at three incommensurate tilings (kills the
    // visible repeat), and let coverage swing from open lace to clotted froth
    // as the channel saturates. Null-guarded: absent textures degrade to the
    // previous procedural-noise path.
    UMaterialExpression* FoamPattern = nullptr;
    UMaterialExpression* FrothCellVariation = nullptr;
    UTexture2D* FrothLaceLight = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
             "Textures/T_RaftSim_SouthForkWater_FoamLace."
             "T_RaftSim_SouthForkWater_FoamLace"));
    // The dense scale is a separately transformed sample of the same verified
    // project-owned lace. Its incommensurate rotation and cutoff make it
    // statistically independent without relying on an optional texture asset.
    UTexture2D* FrothLaceDense = FrothLaceLight;
    if (FrothLaceLight != nullptr && FrothLaceDense != nullptr)
    {
        auto FrothSample = [&](UTexture2D* Texture, const TCHAR* ParameterName,
                               float Tiling, float RotationRadians,
                               float CurlStrength) -> UMaterialExpression* {
            UMaterialExpressionTextureCoordinate* FrothUv =
                Cast<UMaterialExpressionTextureCoordinate>(
                    Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
            FrothUv->UTiling = Tiling;
            FrothUv->VTiling = Tiling;
            UMaterialExpressionTextureSampleParameter2D* FrothSampleNode =
                Cast<UMaterialExpressionTextureSampleParameter2D>(Add(
                    NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            FrothSampleNode->ParameterName = ParameterName;
            FrothSampleNode->Texture = Texture;
            FrothSampleNode->SamplerType = SAMPLERTYPE_Masks;
            FrothSampleNode->Coordinates.Expression = AddTurbulentFoamCoordinates(
                Material,
                AddCurrentAdvectedCoordinates(
                    Material, FrothUv, Tiling, Tiling, 1.0f,
                    TEXT("RaftSimUnifiedCurrentLiveFroth")),
                RotationRadians,
                CurlStrength,
                TEXT("RaftSimIsotropicLiveFoamPatchCoordinates"));
            return Mask(FrothSampleNode, true, false, false);
        };
        auto CutFroth = [&](UMaterialExpression* Sample,
                            const TCHAR* BiasName, float Bias,
                            const TCHAR* GainName, float Gain)
            -> UMaterialExpression* {
            UMaterialExpressionSaturate* Cut = Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
            Cut->Input.Expression = Mul(
                AddNode(Sample, Scalar(BiasName, -Bias)),
                Scalar(GainName, Gain));
            return Cut;
        };
        UMaterialExpression* LaceLight = CutFroth(FrothSample(
            FrothLaceLight, TEXT("WhitewaterFrothLaceLight"),
            0.78f, 0.35f, 0.085f),
            TEXT("WhitewaterFrothLightCutBias"), 0.22f,
            TEXT("WhitewaterFrothLightCutGain"), 1.72f);
        UMaterialExpression* LaceDense = CutFroth(FrothSample(
            FrothLaceDense, TEXT("WhitewaterFrothLaceDense"),
            1.37f, -0.62f, 0.060f),
            TEXT("WhitewaterFrothDenseCutBias"), 0.20f,
            TEXT("WhitewaterFrothDenseCutGain"), 1.62f);
        UMaterialExpression* BubbleCells = CutFroth(FrothSample(
            FrothLaceLight, TEXT("WhitewaterFrothBubbleCells"),
            3.20f, 1.02f, 0.032f),
            TEXT("WhitewaterFrothBubbleCutBias"), 0.16f,
            TEXT("WhitewaterFrothBubbleCutGain"), 1.48f);

        // Three current-advected scales keep the white body legible without
        // letting strong solver foam collapse into a featureless card. The
        // broad vertex channel supplies the roller mass, intersecting lace
        // tears medium openings through it, and a third incommensurate sample
        // perforates that lace with bubble-sized dark water windows.
        UMaterialExpression* BubblePerforation = Lerp(
            Scalar(TEXT("WhitewaterFrothBubbleHoleFloor"), 0.08f),
            Scalar(TEXT("WhitewaterFrothBubbleSolid"), 1.0f),
            BubbleCells);
        UMaterialExpression* TornLace = Mul(
            Mul(LaceLight, LaceDense), BubblePerforation);
        UMaterialExpressionSaturate* ClottedFroth =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        ClottedFroth->Input.Expression = Mul(
            Mul(
                AddNode(
                    Mul(LaceLight,
                        Scalar(TEXT("WhitewaterFrothLightFill"), 0.68f)),
                    Mul(LaceDense,
                        Scalar(TEXT("WhitewaterFrothDenseFill"), 0.56f))),
                BubblePerforation),
            Scalar(TEXT("WhitewaterFrothPatchContrast"), 1.18f));
        UMaterialExpressionSaturate* FrothCoreFill =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        // Even fully aerated vertices retain at least 42% of the torn-lace
        // response. That preserves dark holes throughout a roller instead of
        // filling the complete moving-grid cell solid white.
        FrothCoreFill->Input.Expression = Mul(
            FoamMask, Scalar(TEXT("WhitewaterFrothCoreFill"), 0.58f));
        FoamPattern = Lerp(TornLace, ClottedFroth, FrothCoreFill);
        FrothCellVariation = Lerp(
            TornLace,
            BubblePerforation,
            Scalar(TEXT("UnifiedSurfaceFeatureScaleBlend"), 0.55f));
    }
    else
    {
        UMaterialExpressionNoise* FoamNoise =
            Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
        FoamNoise->Scale = 0.009f;
        FoamNoise->bTurbulence = true;
        FoamNoise->Levels = 4;
        FoamNoise->OutputMin = 0.20f;
        FoamNoise->OutputMax = 1.20f;
        FoamPattern = FoamNoise;
    }
    UMaterialExpressionTextureCoordinate* FoamPatchUv =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    FoamPatchUv->UTiling = 4.20f;
    FoamPatchUv->VTiling = 4.20f;
    UMaterialExpression* FoamPatchCells = AddTurbulentFoamWebMask(
        Material,
        AddTurbulentFoamCoordinates(
            Material,
            AddCurrentAdvectedCoordinates(
                Material, FoamPatchUv, 4.20f, 4.20f, 1.0f,
                TEXT("RaftSimUnifiedCurrentLiveFoamPatchAdvection")),
            0.81f,
            0.060f,
            TEXT("RaftSimLiveFoamWebCurl")),
        TEXT("RaftSimLiveFoamConnectedWebGate"));
    UMaterialExpression* CompactFoamGate = Lerp(
        Scalar(TEXT("WhitewaterFrothPatchOutsideFloor"), 0.02f),
        Scalar(TEXT("WhitewaterFrothPatchInside"), 1.0f),
        FoamPatchCells);
    FoamPattern = Mul(
        Lerp(
            Scalar(TEXT("WhitewaterFrothLaceModulationFloor"), 0.18f),
            Scalar(TEXT("WhitewaterFrothLaceModulationCeiling"), 1.0f),
            FoamPattern),
        CompactFoamGate);
    if (FrothCellVariation != nullptr)
    {
        FrothCellVariation = Mul(FrothCellVariation, CompactFoamGate);
    }
    UMaterialExpressionMultiply* FoamRaw = Mul(
        Mul(FoamMask, FoamPattern), Scalar(TEXT("LiveFoamIntensity"), 1.70f));
    UMaterialExpressionClamp* Foam =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    Foam->Input.Expression = FoamRaw;
    Foam->MinDefault = 0.0f;
    Foam->MaxDefault = 1.0f;
    UMaterialExpression* FoamToneAlpha = FoamPattern;
    if (FrothCellVariation != nullptr)
    {
        UMaterialExpressionSaturate* MultiscaleTone =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        MultiscaleTone->Input.Expression = AddNode(
            Mul(FoamPattern,
                Scalar(TEXT("WhitewaterFrothLaceToneWeight"), 0.72f)),
            Mul(FrothCellVariation,
                Scalar(TEXT("WhitewaterFrothBubbleToneWeight"), 0.28f)));
        FoamToneAlpha = MultiscaleTone;
    }
    UMaterialExpression* FoamColor = Lerp(
        Vector(
            TEXT("WhitewaterFrothShadowColor"),
            FLinearColor(0.57f, 0.66f, 0.69f, 1.0f)),
        Vector(
            TEXT("WhitewaterFrothColor"),
            FLinearColor(0.92f, 0.95f, 0.96f, 1.0f)),
        FoamToneAlpha);
    UMaterialExpressionLinearInterpolate* BaseColor = Lerp(
        ReflectedDepthColor, FoamColor, Foam);

    UMaterialExpression* FoamRoughness =
        Scalar(TEXT("LiveFoamRoughness"), 0.58f);
    if (FrothCellVariation != nullptr)
    {
        FoamRoughness = Lerp(
            Scalar(TEXT("LiveFoamRoughnessOpenCell"), 0.43f),
            Scalar(TEXT("LiveFoamRoughnessBubble"), 0.72f),
            FrothCellVariation);
    }
    UMaterialExpressionLinearInterpolate* Roughness = Lerp(
        Scalar(TEXT("LiveWaterRoughness"), 0.085f),
        FoamRoughness,
        Foam);

    UMaterialExpression* FinalNormal = nullptr;
    UMaterialExpression* RoughnessOutput = Roughness;
    UMaterialExpression* BaseColorOutput = BaseColor;
    // Crest/trough contrast is derived from UV2.y, the normalized signed
    // vertex displacement. It is physical-height shading, not a wake bitmap.
    BaseColorOutput = Mul(
        BaseColorOutput,
        AddNode(
            Scalar(TEXT("LivePaddleWakeHeightMidpoint"), 1.0f),
            Mul(
                PaddleWakeSignedHeight,
                Scalar(TEXT("LivePaddleWakeHeightContrast"), 0.35f))));
    UMaterialExpression* EmissiveOutput = nullptr;
    UMaterialExpression* FleckOutput = nullptr;
    UTexture2D* DetailNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FlowNormal."
             "T_RaftSim_SouthForkWater_FlowNormal"));
    if (DetailNormal)
    {
        UMaterialExpressionTextureCoordinate* UV =
            Cast<UMaterialExpressionTextureCoordinate>(
                Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        UV->UTiling = 0.74f;
        UV->VTiling = 1.02f;
        UMaterialExpressionTextureCoordinate* CrossUv =
            Cast<UMaterialExpressionTextureCoordinate>(
                Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        CrossUv->UTiling = 1.48f;
        CrossUv->VTiling = 1.33f;

        // UV1 remains the local solver velocity and only gates how strongly
        // flow detail appears. It no longer participates in UV phase, so a
        // velocity update cannot move or flash the texture discontinuously.
        UMaterialExpressionTextureCoordinate* FlowVelocityMps =
            Cast<UMaterialExpressionTextureCoordinate>(
                Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        FlowVelocityMps->CoordinateIndex = 1;
        FlowVelocityMps->Desc = TEXT("RaftSimSolverVelocityMagnitudeUV1");

        const auto ConstOf = [&](float Value) -> UMaterialExpression*
        {
            UMaterialExpressionConstant* C =
                NewObject<UMaterialExpressionConstant>(Material);
            C->R = Value;
            Add(C);
            return C;
        };
        UMaterialExpression* PhaseA = ConstOf(0.0f);
        UMaterialExpression* PhaseB = PhaseA;
        UMaterialExpression* CycleAlpha = PhaseA;
        const auto FlowAdvectedAt = [&](UMaterialExpression* Base,
                                        float UTiling,
                                        float VTiling,
                                        const TCHAR* Description,
                                        UMaterialExpression*)
            -> UMaterialExpression*
        {
            return AddCurrentAdvectedCoordinates(
                Material, Base, UTiling, VTiling, 1.0f, Description);
        };
        UMaterialExpression* FlowUvA = FlowAdvectedAt(
            UV, 0.74f, 1.02f,
            TEXT("RaftSimUnifiedCurrentWaterSurface"), PhaseA);
        UMaterialExpression* FlowUvB = FlowUvA;
        UMaterialExpression* FlowCrossUvA = FlowAdvectedAt(
            CrossUv, 1.48f, 1.33f,
            TEXT("RaftSimUnifiedCurrentWaterSurface"), PhaseA);
        UMaterialExpression* FlowCrossUvB = FlowCrossUvA;
        auto Ripple = [&](UMaterialExpression* Coordinates,
                          const TCHAR* ParameterName,
                          float SpeedX,
                          float SpeedY) -> UMaterialExpression*
        {
            UMaterialExpressionTextureSampleParameter2D* Sample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            Sample->ParameterName = ParameterName;
            Sample->Texture = DetailNormal;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = Coordinates;
            return Sample;
        };
        // Both normal scales use the same integrated-current coordinates.
        // Their former residual panners are intentionally gone: independent
        // phase motion made the surface appear to slip past a drifting raft.
        UMaterialExpression* PrimaryNormal = Lerp(
            Ripple(FlowUvA, TEXT("LiveWaterFlowNormalPrimaryA"),
                   0.006f, 0.003f),
            Ripple(FlowUvB, TEXT("LiveWaterFlowNormalPrimaryB"),
                   0.006f, 0.003f),
            CycleAlpha);
        UMaterialExpression* CrossNormal = Lerp(
            Ripple(FlowCrossUvA, TEXT("LiveWaterFlowNormalCrossA"),
                   -0.004f, 0.010f),
            Ripple(FlowCrossUvB, TEXT("LiveWaterFlowNormalCrossB"),
                   -0.004f, 0.010f),
            CycleAlpha);
        UMaterialExpression* CrossPerturbation = AddNode(
            CrossNormal, Const3(0.0f, 0.0f, -1.0f));
        UMaterialExpressionNormalize* CombinedNormal =
            Cast<UMaterialExpressionNormalize>(
                Add(NewObject<UMaterialExpressionNormalize>(Material)));
        CombinedNormal->VectorInput.Expression = AddNode(
            PrimaryNormal, CrossPerturbation);
        UMaterialExpressionScalarParameter* LiveNormalStrength =
            Scalar(TEXT("LiveRippleStrength"), 0.10f);
        UMaterialExpressionConstant3Vector* LiveFlatN =
            Const3(0.0f, 0.0f, 1.0f);
        UMaterialExpressionFresnel* LiveRippleGrazingFresnel =
            Cast<UMaterialExpressionFresnel>(
                Add(NewObject<UMaterialExpressionFresnel>(Material)));
        LiveRippleGrazingFresnel->Exponent = 1.4f;
        LiveRippleGrazingFresnel->BaseReflectFraction = 0.0f;
        LiveRippleGrazingFresnel->Normal.Expression = LiveFlatN;
        UMaterialExpression* LiveGrazingFilteredNormalStrength = Lerp(
            LiveNormalStrength,
            Mul(
                LiveNormalStrength,
                Scalar(TEXT("LiveRippleGrazingFloor"), 0.15f)),
            LiveRippleGrazingFresnel);
        FinalNormal = Lerp(
            LiveFlatN,
            CombinedNormal,
            LiveGrazingFilteredNormalStrength);

        // Compact roughness cells sampled at the same current-advected
        // coordinates as the ripple normals. These keep a trackable motion
        // cue without reintroducing long matte or bright flow stripes.
        {
            const auto ConstExpr = [&](float Value) -> UMaterialExpression*
            {
                UMaterialExpressionConstant* C =
                    NewObject<UMaterialExpressionConstant>(Material);
                C->R = Value;
                Add(C);
                return C;
            };
            UMaterialExpression* StreakField = AddCellularFoamPatchMask(
                Material,
                AddTurbulentFoamCoordinates(
                    Material, FlowUvA, 0.67f, 0.080f,
                    TEXT("RaftSimLiveWaterRoughnessPatchCoordinates")),
                TEXT("RaftSimLiveWaterRoughnessPatchField"));
            UMaterialExpressionDotProduct* SpeedSquared =
                NewObject<UMaterialExpressionDotProduct>(Material);
            SpeedSquared->A.Expression = FlowVelocityMps;
            SpeedSquared->B.Expression = FlowVelocityMps;
            Add(SpeedSquared);
            UMaterialExpressionSaturate* SpeedGate =
                NewObject<UMaterialExpressionSaturate>(Material);
            SpeedGate->Input.Expression =
                Mul(SpeedSquared, ConstExpr(0.5f));
            Add(SpeedGate);
            UMaterialExpression* GatedField = Mul(StreakField, SpeedGate);
            RoughnessOutput = AddNode(
                Roughness,
                Mul(GatedField,
                    Scalar(TEXT("LiveFlowStreakRoughness"), 0.20f)));
            // Roughness lanes need reflection contrast to show; under a
            // diffuse sky they vanish. A few percent of matching albedo
            // modulation keeps the lanes readable in any light without
            // painting visible stripes on still frames.
            BaseColorOutput = Mul(
                BaseColor,
                AddNode(
                    ConstExpr(1.0f),
                    Mul(GatedField,
                        Scalar(TEXT("LiveFlowStreakTint"), 0.05f))));
            // Drift-foam strands: sparse aperiodic lace advected at solver
            // speed — the trackable features that make current readable.
            // Same construction as the band parent; see the note there.
            UTexture2D* DriftLaceTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
                     "Textures/T_RaftSim_SouthForkWater_FoamLace."
                     "T_RaftSim_SouthForkWater_FoamLace"));
            if (DriftLaceTexture != nullptr)
            {
                const auto DriftLace = [&](const TCHAR* ParameterName,
                                           float TilingValue,
                                           float RotationRadians,
                                           float CurlStrength,
                                           UMaterialExpression* Phase)
                    -> UMaterialExpression*
                {
                    UMaterialExpressionTextureCoordinate* LaceUv =
                        Cast<UMaterialExpressionTextureCoordinate>(Add(
                            NewObject<UMaterialExpressionTextureCoordinate>(
                                Material)));
                    LaceUv->UTiling = TilingValue;
                    LaceUv->VTiling = TilingValue;
                    UMaterialExpressionTextureSampleParameter2D* Sample =
                        Cast<UMaterialExpressionTextureSampleParameter2D>(
                            Add(NewObject<
                                UMaterialExpressionTextureSampleParameter2D>(
                                Material)));
                    Sample->ParameterName = ParameterName;
                    Sample->Texture = DriftLaceTexture;
                    Sample->SamplerType = SAMPLERTYPE_Masks;
                    Sample->Coordinates.Expression = AddTurbulentFoamCoordinates(
                        Material,
                        FlowAdvectedAt(
                            LaceUv, TilingValue, TilingValue,
                            TEXT("RaftSimLiveDriftLaceAdvection"), Phase),
                        RotationRadians,
                        CurlStrength,
                        TEXT("RaftSimCompactLiveDriftFoamCoordinates"));
                    UMaterialExpressionComponentMask* Red =
                        Cast<UMaterialExpressionComponentMask>(Add(
                            NewObject<UMaterialExpressionComponentMask>(
                                Material)));
                    Red->R = true;
                    Red->G = false;
                    Red->B = false;
                    Red->A = false;
                    Red->Input.Expression = Sample;
                    return Red;
                };
                const auto DriftMaskAt =
                    [&](UMaterialExpression* Phase,
                        const TCHAR* NameA,
                        const TCHAR* NameB) -> UMaterialExpression*
                {
                    UMaterialExpression* StrandProduct = Mul(
                        DriftLace(NameA, 0.84f, 0.43f, 0.060f, Phase),
                        DriftLace(NameB, 1.75f, -0.79f, 0.035f, Phase));
                    UMaterialExpressionSaturate* StrandCut =
                        NewObject<UMaterialExpressionSaturate>(Material);
                    StrandCut->Input.Expression = AddNode(
                        Mul(StrandProduct,
                            Scalar(TEXT("LiveDriftFoamGain"), 5.0f)),
                        Mul(ConstExpr(-1.0f),
                            Scalar(TEXT("LiveDriftFoamBias"), 0.45f)));
                    Add(StrandCut);
                    return Mul(StrandCut, StrandCut);
                };
                // Aeration-born bubbles, as on the band parent: solver foam
                // (VC.R) is the source; a residual only above ~1.6 m/s
                // covers fast unbroken chutes. Flat reaches stay clean.
                UMaterialExpressionSaturate* ChuteGate =
                    NewObject<UMaterialExpressionSaturate>(Material);
                ChuteGate->Input.Expression = Mul(
                    AddNode(
                        SpeedSquared,
                        Mul(ConstExpr(-1.0f),
                            Scalar(TEXT("LiveDriftFoamSpeedFloorSq"),
                                   2.56f))),
                    Scalar(TEXT("LiveDriftFoamSpeedGain"), 0.8f));
                Add(ChuteGate);
                UMaterialExpressionSaturate* DriftGate =
                    NewObject<UMaterialExpressionSaturate>(Material);
                DriftGate->Input.Expression = AddNode(
                    Mul(FoamMask,
                        Scalar(TEXT("LiveDriftFoamAerationGain"), 3.0f)),
                    ChuteGate);
                Add(DriftGate);
                // Wet (vertex alpha) and geometry-upness gates — see the
                // band parent note: no froth on dry-leveled skirts or on
                // the near-vertical film across exposed rock.
                // Alpha rides VertexColor's dedicated output pin — the
                // default output is float3 RGB. See the band parent note.
                UMaterialExpressionComponentMask* WetGate =
                    NewObject<UMaterialExpressionComponentMask>(Material);
                WetGate->R = true;
                WetGate->G = false;
                WetGate->B = false;
                WetGate->A = false;
                WetGate->Input.Connect(4, VertexColor);
                Add(WetGate);
                UMaterialExpressionVertexNormalWS* GeoNormal =
                    NewObject<UMaterialExpressionVertexNormalWS>(Material);
                Add(GeoNormal);
                UMaterialExpressionSaturate* UpGate =
                    NewObject<UMaterialExpressionSaturate>(Material);
                UpGate->Input.Expression = Mul(
                    AddNode(
                        Mask(GeoNormal, false, false, true),
                        ConstExpr(-0.7f)),
                    ConstExpr(5.0f));
                Add(UpGate);
                // Depth gate against shallow-margin phantom foam — see the
                // band parent note.
                UMaterialExpressionSaturate* DepthGate =
                    NewObject<UMaterialExpressionSaturate>(Material);
                DepthGate->Input.Expression = Mul(
                    AddNode(
                        DepthMask,
                        Mul(ConstExpr(-1.0f),
                            Scalar(TEXT("LiveDriftFoamDepthFloor"),
                                   0.06f))),
                    Scalar(TEXT("LiveDriftFoamDepthGain"), 9.0f));
                Add(DepthGate);
                UMaterialExpression* Fleck = Mul(
                    Mul(
                        Mul(
                            Lerp(
                                DriftMaskAt(PhaseA,
                                            TEXT("LiveDriftFoamLaceA0"),
                                            TEXT("LiveDriftFoamLaceB0")),
                                DriftMaskAt(PhaseB,
                                            TEXT("LiveDriftFoamLaceA1"),
                                            TEXT("LiveDriftFoamLaceB1")),
                                CycleAlpha),
                            DriftGate),
                        CompactFoamGate),
                    Mul(Mul(WetGate, UpGate), DepthGate));
                FleckOutput = Fleck;
                RoughnessOutput = AddNode(
                    RoughnessOutput,
                    Mul(Fleck,
                        Scalar(TEXT("LiveDriftFoamRoughness"), 0.45f)));
                BaseColorOutput = Lerp(
                    BaseColorOutput,
                    Const3(0.88f, 0.91f, 0.92f),
                    Mul(Fleck,
                        Scalar(TEXT("LiveDriftFoamOpacity"), 0.35f)));
                // Surface read: emissive composites over the reflection
                // layer, so the strands sit ON the water instead of
                // shading beneath its mirror. See the band parent note.
                EmissiveOutput = Mul(
                    Const3(0.88f, 0.91f, 0.92f),
                    Mul(Fleck,
                        Scalar(TEXT("LiveDriftFoamSurfaceGlow"), 0.40f)));
            }
        }
    }

    // Bright sky reflection can drive the nearly opaque unified carrier close
    // to one flat value even outside foam. Reuse the same river-space,
    // current-advected multiscale field as restrained tone structure, gated by
    // the solver's real speed and aeration channels. This provides trackable
    // moving cells and torn lanes without a panner, second sheet, periodic
    // cross-channel stripe, or moving-grid phase reset.
    if (FrothCellVariation != nullptr)
    {
        UMaterialExpressionSaturate* SurfaceFeatureActivity =
            Cast<UMaterialExpressionSaturate>(
                Add(NewObject<UMaterialExpressionSaturate>(Material)));
        SurfaceFeatureActivity->Input.Expression = AddNode(
            Mul(SpeedMask,
                Scalar(TEXT("UnifiedSurfaceFeatureSpeedGain"), 4.5f)),
            Mul(FoamMask,
                Scalar(TEXT("UnifiedSurfaceFeatureFoamGain"), 1.5f)));
        UMaterialExpression* SurfaceFeatureTone = Lerp(
            Scalar(TEXT("UnifiedSurfaceFeatureDark"), 0.92f),
            Scalar(TEXT("UnifiedSurfaceFeatureBright"), 1.02f),
            FrothCellVariation);
        UMaterialExpression* SurfaceFeatureBlend = Mul(
            SurfaceFeatureActivity,
            Scalar(TEXT("UnifiedSurfaceFeatureStrength"), 0.22f));
        BaseColorOutput = Mul(
            BaseColorOutput,
            Lerp(
                Scalar(TEXT("UnifiedSurfaceFeatureIdentity"), 1.0f),
                SurfaceFeatureTone,
                SurfaceFeatureBlend));
        RoughnessOutput = Lerp(
            RoughnessOutput,
            AddNode(
                RoughnessOutput,
                Mul(FrothCellVariation,
                    Scalar(TEXT("UnifiedSurfaceFeatureRoughness"), 0.035f))),
            SurfaceFeatureBlend);
    }

    // Solver foam still needs a bounded direct channel so sparse obstruction
    // wakes cannot disappear between lace openings. Keep that insurance small
    // and let the three-scale pattern supply nearly all brightness; the old
    // 45% constant floor was the source of smooth homogeneous white regions.
    {
        UMaterialExpression* GlowTexture =
            Scalar(TEXT("LiveSolverFoamGlowFloor"), 0.08f);
        if (FoamPattern != nullptr)
        {
            GlowTexture = AddNode(
                GlowTexture,
                Mul(FoamPattern,
                    Scalar(TEXT("LiveSolverFoamGlowPatternGain"), 0.92f)));
        }
        UMaterialExpression* SolverFoamGlow = Mul(
            Const3(0.88f, 0.91f, 0.92f),
            Mul(Mul(FoamMask, GlowTexture),
                Scalar(TEXT("LiveSolverFoamGlow"), 0.55f)));
        EmissiveOutput = EmissiveOutput != nullptr
            ? AddNode(EmissiveOutput, SolverFoamGlow)
            : SolverFoamGlow;
    }
    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, BaseColorOutput);
    Ed->Roughness.Connect(0, RoughnessOutput);
    if (EmissiveOutput != nullptr)
    {
        Ed->EmissiveColor.Connect(0, EmissiveOutput);
    }
    UMaterialExpression* SpecularOutput =
        Scalar(TEXT("LiveWaterSpecular"), 0.48f);
    if (FleckOutput != nullptr)
    {
        // Foam occludes the mirror — see the band parent note.
        SpecularOutput = Lerp(
            SpecularOutput,
            Scalar(TEXT("LiveDriftFoamSpecular"), 0.03f),
            FleckOutput);
    }
    Ed->Specular.Connect(0, SpecularOutput);

    // Calm reaches gain their colour and volumetric response from the authored
    // surface directly below. Retain a bounded share of the live mesh there
    // for resolved geometry/normals, then ramp to full live-surface coverage
    // from the real solver foam and speed channels. This is presentation-only:
    // it neither modifies nor resamples the hydraulic grid or its wet/dry mask.
    // Let ordinary current begin revealing the advected detail above 0.24 m/s;
    // the bounded runtime coverage and wet/station feathers keep this from
    // becoming the former rectangular olive sheet over authored water.
    UMaterialExpressionSaturate* SpeedCoverage =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    SpeedCoverage->Input.Expression = Mul(
        AddNode(
            SpeedMask,
            // Reviewed value (-0.28): the 2026-07-30 bulk commit retuned this
            // to -0.03, which engages hydraulic/whitewater coverage at nearly
            // any water speed — the played result is a white haze hovering
            // over slow water and margins ("haze over the river", 2026-08-14).
            Scalar(TEXT("HydraulicCoverageSpeedThresholdBias"), -0.28f)),
        Scalar(TEXT("HydraulicCoverageSpeedGain"), 3.2f));
    UMaterialExpressionSaturate* HydraulicActivity =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    HydraulicActivity->Input.Expression = AddNode(
        Mul(FoamMask, Scalar(TEXT("HydraulicCoverageFoamGain"), 0.95f)),
        SpeedCoverage);
    UMaterialExpressionLinearInterpolate* HydraulicCoverage = Lerp(
        Scalar(TEXT("CalmLiveSurfaceCoverage"), 0.0f),
        Scalar(TEXT("ActiveLiveSurfaceCoverage"), 0.03f),
        HydraulicActivity);
    // Froth must be visible to read as whitewater: aerated cells push the
    // overlay toward opaque white while calm water keeps the old subtle
    // coverage. Foam here is the textured, clamped froth term above.
    UMaterialExpressionSaturate* CoverageWithFroth =
        Cast<UMaterialExpressionSaturate>(
            Add(NewObject<UMaterialExpressionSaturate>(Material)));
    // Raw solver foam must also open the sheet directly: the textured froth
    // term is pattern-multiplied (sparse lace, mean ~0.16), so wake and
    // obstruction foam raised opacity by only a few percent and the foam
    // glow blended to nothing (verified: 50+ wake vertices, no pixels).
    CoverageWithFroth->Input.Expression = AddNode(
        AddNode(
            AddNode(
                HydraulicCoverage,
                Mul(Foam, Scalar(TEXT("WhitewaterFrothOpacityGain"), 1.28f))),
            Mul(FoamMask, Scalar(TEXT("SolverFoamOpacityGain"), 0.12f))),
        // Bounded reveal of the real displaced mesh. This is deliberately
        // water-coloured and foam-independent so it reads as a ripple, not
        // a return of the white wake streaks.
        Mul(
            PaddleWakeCoverage,
            Scalar(TEXT("LivePaddleWakeGeometryCoverage"), 0.24f)));
    UMaterialExpressionMultiply* HydraulicSurfaceCoverage = Mul(
        StationEdgeCoverage, CoverageWithFroth);
    // Older live detail skins retained calm alpha on the dry vertices of the
    // rectangular solver grid. Keep the shared behavior as the default, but
    // expose a river-local depth mask so Lava Canyon can fade the detail skin
    // to zero before the wet/dry boundary instead of drawing water over land.
    UMaterialExpressionSaturate* WetDepthCoverage =
        Cast<UMaterialExpressionSaturate>(
            Add(NewObject<UMaterialExpressionSaturate>(Material)));
    WetDepthCoverage->Input.Expression = Mul(
        DepthMask,
        Scalar(TEXT("LiveWetCoverageDepthGain"), 32.0f));
    UMaterialExpression* WetCoverage = Lerp(
        Scalar(TEXT("LiveWetCoverageIdentity"), 1.0f),
        WetDepthCoverage,
        Scalar(TEXT("LiveWetCoverageEnable"), 0.0f));
    UMaterialExpressionMultiply* SurfaceCoverage = Mul(
        Mul(HydraulicSurfaceCoverage, WetCoverage),
        RaftHullExclusion);
    // Continuous alpha is essential for still captures and lower temporal-AA
    // histories: a masked temporal dither exposed a conspicuous stipple field
    // across otherwise calm water. This ordinary surface translucency does not
    // write refraction or Single Layer Water volume data.
    Ed->Opacity.Connect(0, SurfaceCoverage);
    if (FinalNormal)
    {
        Ed->Normal.Connect(0, FinalNormal);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: %s saved=%d"), AssetName, bSaved ? 1 : 0);
    return Material;
}

// Texture-free surface response for the physically displaced paddle wake.
// The draw section contains only signed bilateral-ripple triangles, while
// UV2.y carries their mesh displacement for crest/trough colour response.
// No bitmap, normal map, noise, decal, foam, or screen-space wake is sampled.
UMaterial* BuildPaddleWakeRippleMaterial()
{
    static const TCHAR* AssetName = TEXT("M_RaftSim_PaddleWakeRipple");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleWakeRipple");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleWakeRipple."
             "M_RaftSim_PaddleWakeRipple");
    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, ObjectPath));
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Translucent;
    Material->TranslucencyLightingMode = TLM_SurfacePerPixelLighting;
    Material->SetShadingModel(MSM_Unlit);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;

    auto Add = [Material](UMaterialExpression* Expression)
        -> UMaterialExpression*
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value) -> UMaterialExpressionConstant*
    {
        UMaterialExpressionConstant* Expression =
            NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        return Cast<UMaterialExpressionConstant>(Add(Expression));
    };
    auto Vector = [&](const TCHAR* Name, const FLinearColor& Value)
        -> UMaterialExpressionVectorParameter*
    {
        UMaterialExpressionVectorParameter* Expression =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimPaddleWake");
        return Cast<UMaterialExpressionVectorParameter>(Add(Expression));
    };
    auto Scalar = [&](const TCHAR* Name, float Value)
        -> UMaterialExpressionScalarParameter*
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimPaddleWake");
        return Cast<UMaterialExpressionScalarParameter>(Add(Expression));
    };
    auto Mask = [&](UMaterialExpression* Input, bool R, bool G, bool B,
                    bool A = false) -> UMaterialExpressionComponentMask*
    {
        UMaterialExpressionComponentMask* Expression =
            NewObject<UMaterialExpressionComponentMask>(Material);
        Expression->Input.Expression = Input;
        Expression->R = R;
        Expression->G = G;
        Expression->B = B;
        Expression->A = A;
        return Cast<UMaterialExpressionComponentMask>(Add(Expression));
    };
    auto AddNode = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionAdd*
    {
        UMaterialExpressionAdd* Expression =
            NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionAdd>(Add(Expression));
    };
    auto Mul = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionMultiply*
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionMultiply>(Add(Expression));
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B,
                    UMaterialExpression* Alpha)
        -> UMaterialExpressionLinearInterpolate*
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        return Cast<UMaterialExpressionLinearInterpolate>(Add(Expression));
    };

    UMaterialExpressionVertexColor* VertexColor =
        Cast<UMaterialExpressionVertexColor>(
            Add(NewObject<UMaterialExpressionVertexColor>(Material)));
    UMaterialExpressionComponentMask* RippleCoverage =
        Mask(VertexColor, true, false, false);
    RippleCoverage->Input.OutputIndex = 4;

    UMaterialExpressionTextureCoordinate* WakeMeshData =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    WakeMeshData->CoordinateIndex = 2;
    WakeMeshData->Desc = TEXT("RaftSimSignedPaddleWakeGeometryUV2");
    UMaterialExpressionComponentMask* SignedHeight =
        Mask(WakeMeshData, false, true, false);
    UMaterialExpressionSaturate* Height01 =
        Cast<UMaterialExpressionSaturate>(
            Add(NewObject<UMaterialExpressionSaturate>(Material)));
    Height01->Input.Expression = AddNode(
        Constant(0.5f), Mul(SignedHeight, Constant(0.5f)));

    UMaterialExpression* RippleBody = Lerp(
        Vector(TEXT("PaddleWakeTroughColor"),
            FLinearColor(0.025f, 0.058f, 0.072f, 1.0f)),
        Vector(TEXT("PaddleWakeCrestColor"),
            FLinearColor(0.135f, 0.225f, 0.220f, 1.0f)),
        Height01);
    UMaterialExpressionFresnel* Fresnel =
        Cast<UMaterialExpressionFresnel>(
            Add(NewObject<UMaterialExpressionFresnel>(Material)));
    Fresnel->Exponent = 3.6f;
    Fresnel->BaseReflectFraction = 0.025f;
    UMaterialExpression* ReflectedRipple = Lerp(
        RippleBody,
        Vector(TEXT("PaddleWakeReflectedSkyColor"),
            FLinearColor(0.16f, 0.23f, 0.28f, 1.0f)),
        Mul(Fresnel, Scalar(TEXT("PaddleWakeReflectionStrength"), 0.85f)));

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->EmissiveColor.Connect(0, ReflectedRipple);
    EditorData->Opacity.Connect(
        0, Mul(RippleCoverage, Scalar(TEXT("PaddleWakeOpacity"), 0.70f)));

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved =
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim: %s texture-free ripple material saved=%d"),
        AssetName, bSaved ? 1 : 0);
    return bSaved ? Material : nullptr;
}

// One draw-call face material: RGB vertex colour carries deterministic skin,
// sclera, iris, brow, and lip colour while vertex alpha separates soft skin
// from the harder facial details for subsurface and roughness response.
} // namespace RaftSimPhotorealMaterials
