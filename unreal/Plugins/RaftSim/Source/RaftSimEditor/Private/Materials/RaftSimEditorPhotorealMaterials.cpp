// Photoreal river-water material (P4 photoreal track). Authors a genuine
// Single Layer Water material with depth-based colour, Fresnel-driven Lumen
// reflection, panned detail-normal ripples over the solver's geometric wave
// normals, and vertex-colour foam. Registered as a console command so it is
// generated headlessly, following the RaftSimEditor raw-expression idiom.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/RaftSimEditorOfflineMetaHumanMaterial.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionComponentMask.h"
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
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionPerInstanceCustomData.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionScalarParameter.h"
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
#include "Misc/PackageName.h"
#include "AssetCompilingManager.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimPhotorealMaterials
{
static UMaterial* BuildPhotorealRiverWaterMaterial(
    const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater"),
    const TCHAR* ObjectName = TEXT("M_RaftSim_PhotorealRiverWater"))
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
    UMaterialExpressionLinearInterpolate* DepthWaterColor =
        Lerp(ShallowColor, DeepColor, DepthMask);

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
    UTexture2D* FoamLaceTexture = LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FoamLace.T_RaftSim_SouthForkWater_FoamLace"));
    if (FoamLaceTexture != nullptr)
    {
        UMaterialExpressionTextureCoordinate* FoamUv = Cast<
            UMaterialExpressionTextureCoordinate>(Add(
                NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        // One tile covers 7.1 m downstream and 3.2 m across the channel.
        FoamUv->UTiling = 0.42f; FoamUv->VTiling = 0.93f;
        UMaterialExpressionPanner* FoamPan = Cast<UMaterialExpressionPanner>(
            Add(NewObject<UMaterialExpressionPanner>(Material)));
        FoamPan->SpeedX = 0.018f; FoamPan->SpeedY = 0.0f;
        FoamPan->Coordinate.Expression = FoamUv;
        UMaterialExpressionTextureSampleParameter2D* FoamLaceSample = Cast<
            UMaterialExpressionTextureSampleParameter2D>(Add(
                NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        FoamLaceSample->ParameterName = TEXT("WhitewaterFoamLace");
        FoamLaceSample->Texture = FoamLaceTexture; FoamLaceSample->SamplerType = SAMPLERTYPE_Masks;
        FoamLaceSample->Coordinates.Expression = FoamPan; FoamLaceSample->Group = TEXT("RaftSimPhotorealWater");
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
    UMaterialExpressionConstant3Vector* FoamColor = Const3(0.48f, 0.53f, 0.52f);
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
        auto Ripple = [&](UMaterialExpression* Coordinates,
                          const TCHAR* ParameterName,
                          float SpeedX,
                          float SpeedY) -> UMaterialExpression*
        {
            UMaterialExpressionPanner* Pan =
                Cast<UMaterialExpressionPanner>(Add(NewObject<UMaterialExpressionPanner>(Material)));
            Pan->SpeedX = SpeedX;
            Pan->SpeedY = SpeedY;
            Pan->Coordinate.Expression = Coordinates;
            UMaterialExpressionTextureSampleParameter2D* Sample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            Sample->ParameterName = ParameterName;
            Sample->Texture = DetailNormal;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = Pan;
            Sample->Group = TEXT("RaftSimPhotorealWater");
            return Sample;
        };
        UMaterialExpression* PrimaryNormal = Ripple(
            UV, TEXT("WaterFlowNormalPrimary"), 0.105f, 0.018f);
        UMaterialExpression* CrossNormal = Ripple(
            CrossUv, TEXT("WaterFlowNormalCross"), -0.036f, 0.081f);
        UMaterialExpression* CrossPerturbation = AddNode(
            CrossNormal, Const3(0.0f, 0.0f, -1.0f));
        UMaterialExpressionNormalize* CombinedNormal =
            Cast<UMaterialExpressionNormalize>(
                Add(NewObject<UMaterialExpressionNormalize>(Material)));
        CombinedNormal->VectorInput.Expression = AddNode(
            PrimaryNormal, CrossPerturbation);
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
        NormalStrength->MaxDefault = 0.14f;
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
            Mul(NormalStrength, Scalar(TEXT("RippleGrazingFloor"), 0.25f)),
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
            Mul(GrazingFilteredNormalStrength, Scalar(TEXT("SlickNormalFloor"), 0.30f)),
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

    UMaterialExpressionFresnel* Fresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    Fresnel->Exponent = 5.0f;
    Fresnel->BaseReflectFraction = 0.02f;
    UMaterialExpressionScalarParameter* SpecBase = Scalar(TEXT("Specular"), 0.34f);
    UMaterialExpressionAdd* Specular = AddNode(SpecBase, Mul(Fresnel, Scalar(TEXT("FresnelSpecular"), 0.18f)));

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
        Lerp(ShallowOpacity, DeepOpacity, DepthMask);
    UMaterialExpressionScalarParameter* FoamOpacity =
        Scalar(TEXT("FoamWaterOpacity"), 0.90f);
    UMaterialExpressionLinearInterpolate* Opacity =
        Lerp(DepthOpacity, FoamOpacity, FoamBroken);
    UMaterialExpressionScalarParameter* Metallic = Scalar(TEXT("Metallic"), 0.0f);

    // --- Wire the material outputs ------------------------------------------
    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, BaseColor);
    Ed->Metallic.Connect(0, Metallic);
    Ed->Specular.Connect(0, Specular);
    Ed->Roughness.Connect(0, Roughness);
    Ed->Opacity.Connect(0, Opacity);
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

// ---------------------------------------------------------------------------
// Photoreal terrain (riverbed + banks) material: world-aligned (triplanar) rock
// on the steep canyon walls blended into forest ground on the flatter benches,
// keyed by world-space slope. Triplanar projection means it needs no UVs, so it
// renders correctly on the procedural riverbed mesh (the landscape terrain
// material relies on LandscapeLayerCoords, which are null off a landscape).
// ---------------------------------------------------------------------------
struct FOutRef
{
    UMaterialExpression* Expr = nullptr;
    int32 OutputIndex = 0;
};

static UMaterial* BuildPhotorealTerrainMaterial()
{
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain.M_RaftSim_PhotorealRiverTerrain");

    UPackage* Package = CreatePackage(PackagePath);
    if (Package == nullptr)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, ObjectPath));
    if (Material == nullptr)
    {
        Material = NewObject<UMaterial>(
            Package, TEXT("M_RaftSim_PhotorealRiverTerrain"),
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (Material == nullptr)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->SetMaterialUsage(MATUSAGE_Nanite);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    // WorldAlignedNormal outputs a world-space normal.
    Material->bTangentSpaceNormal = false;

    auto Add = [Material](UMaterialExpression* E) { Material->GetExpressionCollection().AddExpression(E); return E; };
    auto Load2D = [](const TCHAR* Path) { return LoadObject<UTexture2D>(nullptr, Path); };

    // World-aligned projection of one texture at a given world tile size.
    auto WorldAligned = [&](const TCHAR* ParamName, UTexture2D* Texture,
                            EMaterialSamplerType Sampler, float TileCm, bool bNormal) -> FOutRef
    {
        FOutRef Result;
        if (Texture == nullptr)
        {
            return Result;
        }
        UMaterialExpressionTextureObjectParameter* TexObj =
            NewObject<UMaterialExpressionTextureObjectParameter>(Material);
        TexObj->ParameterName = ParamName;
        TexObj->Texture = Texture;
        TexObj->SamplerType = Sampler;
        TexObj->Group = TEXT("RaftSimPhotorealTerrain");
        Add(TexObj);

        UMaterialExpressionConstant3Vector* Size = NewObject<UMaterialExpressionConstant3Vector>(Material);
        Size->Constant = FLinearColor(TileCm, TileCm, TileCm, 1.0f);
        Add(Size);

        const TCHAR* FunctionPath = bNormal
            ? TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal.WorldAlignedNormal")
            : TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture");
        UMaterialFunctionInterface* Function =
            LoadObject<UMaterialFunctionInterface>(nullptr, FunctionPath);
        UMaterialExpressionMaterialFunctionCall* Call =
            NewObject<UMaterialExpressionMaterialFunctionCall>(Material);
        Add(Call);
        if (Function == nullptr || !Call->SetMaterialFunction(Function))
        {
            return Result;
        }
        for (int32 i = 0; i < Call->FunctionInputs.Num(); ++i)
        {
            const FString Name = Call->GetInputName(i).ToString();
            if (Name.Contains(TEXT("TextureObject"), ESearchCase::IgnoreCase))
            {
                Call->FunctionInputs[i].Input.Expression = TexObj;
            }
            else if (Name.Contains(TEXT("TextureSize"), ESearchCase::IgnoreCase) ||
                     Name.Contains(TEXT("WorldSize"), ESearchCase::IgnoreCase))
            {
                Call->FunctionInputs[i].Input.Expression = Size;
            }
        }
        Result.Expr = Call;
        for (int32 i = 0; i < Call->FunctionOutputs.Num(); ++i)
        {
            if (Call->FunctionOutputs[i].Output.OutputName.ToString().Equals(
                    TEXT("XYZ Texture"), ESearchCase::IgnoreCase))
            {
                Result.OutputIndex = i;
                break;
            }
        }
        return Result;
    };

    auto LerpRefs = [&](const FOutRef& A, const FOutRef& B, UMaterialExpression* Alpha) -> UMaterialExpression*
    {
        UMaterialExpressionLinearInterpolate* L = NewObject<UMaterialExpressionLinearInterpolate>(Material);
        L->A.Expression = A.Expr; L->A.OutputIndex = A.OutputIndex;
        L->B.Expression = B.Expr; L->B.OutputIndex = B.OutputIndex;
        L->Alpha.Expression = Alpha;
        Add(L); return L;
    };

    const TCHAR* PolyHaven = TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven");
    UTexture2D* RockAlbedo = Load2D(*FString::Printf(TEXT("%s/RockGround_4K/T_RockGround_BaseColor_4K.T_RockGround_BaseColor_4K"), PolyHaven));
    UTexture2D* RockNormal = Load2D(*FString::Printf(TEXT("%s/RockGround_4K/T_RockGround_NormalGL_4K.T_RockGround_NormalGL_4K"), PolyHaven));
    UTexture2D* RockRough  = Load2D(*FString::Printf(TEXT("%s/RockGround_4K/T_RockGround_Roughness_4K.T_RockGround_Roughness_4K"), PolyHaven));
    const TCHAR* ProductionDetail =
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
    UTexture2D* GroundAlbedo = Load2D(*FString::Printf(
        TEXT("%s/T_RaftSim_AmericanSouthFork_TerrainDetailAlbedo."
             "T_RaftSim_AmericanSouthFork_TerrainDetailAlbedo"),
        ProductionDetail));
    UTexture2D* GroundNormal = Load2D(*FString::Printf(
        TEXT("%s/T_RaftSim_AmericanSouthFork_TerrainDetailNormal."
             "T_RaftSim_AmericanSouthFork_TerrainDetailNormal"),
        ProductionDetail));
    UTexture2D* GroundPacked = Load2D(*FString::Printf(
        TEXT("%s/T_RaftSim_AmericanSouthFork_TerrainDetailAORoughnessHeight."
             "T_RaftSim_AmericanSouthFork_TerrainDetailAORoughnessHeight"),
        ProductionDetail));

    // Preserve the physical widths published with the reviewed CC0 sources:
    // Rock Ground spans 1.5 m and Forest Ground 03 spans 2.0 m. The previous
    // 9-11 m projection enlarged individual stones and litter several-fold,
    // producing the broad smeared ground visible in guide-eye captures.
    constexpr float RockGroundPhysicalWidthCm = 150.0f;
    // The project-owned South Fork bank scan represents roughly one metre of
    // compacted gravel, granite fragments, and pine litter.  Projecting it at
    // that physical width keeps needles and cobbles at human scale in the
    // guide-eye views instead of enlarging them into terrain-sized motifs.
    constexpr float SouthForkBankPhysicalWidthCm = 320.0f;
    const FOutRef RockA = WorldAligned(TEXT("RockAlbedo"), RockAlbedo, SAMPLERTYPE_Color, RockGroundPhysicalWidthCm, false);
    const FOutRef RockN = WorldAligned(TEXT("RockNormal"), RockNormal, SAMPLERTYPE_Normal, RockGroundPhysicalWidthCm, true);
    const FOutRef RockR = WorldAligned(TEXT("RockRough"), RockRough, SAMPLERTYPE_Masks, RockGroundPhysicalWidthCm, false);
    const FOutRef GrA = WorldAligned(TEXT("GroundAlbedo"), GroundAlbedo, SAMPLERTYPE_Color, SouthForkBankPhysicalWidthCm, false);
    const FOutRef GrN = WorldAligned(TEXT("GroundNormal"), GroundNormal, SAMPLERTYPE_Normal, SouthForkBankPhysicalWidthCm, true);
    const FOutRef GrPacked = WorldAligned(TEXT("GroundPacked"), GroundPacked, SAMPLERTYPE_Masks, SouthForkBankPhysicalWidthCm, false);

    UMaterialExpressionComponentMask* GroundRoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    GroundRoughnessMask->Input.Expression = GrPacked.Expr;
    GroundRoughnessMask->Input.OutputIndex = GrPacked.OutputIndex;
    GroundRoughnessMask->R = false;
    GroundRoughnessMask->G = true;
    GroundRoughnessMask->B = false;
    GroundRoughnessMask->A = false;
    Add(GroundRoughnessMask);
    const FOutRef GrR{GroundRoughnessMask, 0};

    if (RockA.Expr == nullptr || RockN.Expr == nullptr || RockR.Expr == nullptr ||
        GrA.Expr == nullptr || GrN.Expr == nullptr || GrPacked.Expr == nullptr)
    {
        UE_LOG(
            LogTemp, Warning,
            TEXT("RaftSim: one or more reviewed terrain albedo/normal/roughness textures "
                 "are missing; skipping terrain material"));
        return nullptr;
    }

    // Slope key: world up-ness (VertexNormalWS.Z). Flat benches -> ground,
    // steep walls -> rock. Sharpened and clamped to [0,1].
    UMaterialExpressionVertexNormalWS* VN =
        Cast<UMaterialExpressionVertexNormalWS>(Add(NewObject<UMaterialExpressionVertexNormalWS>(Material)));
    UMaterialExpressionComponentMask* UpMask = NewObject<UMaterialExpressionComponentMask>(Material);
    UpMask->Input.Expression = VN; UpMask->R = false; UpMask->G = false; UpMask->B = true; UpMask->A = false;
    Add(UpMask);
    // flatness = clamp((up - 0.72) * 6, 0, 1)
    UMaterialExpressionConstant* Bias = NewObject<UMaterialExpressionConstant>(Material);
    Bias->R = -0.72f; Add(Bias);
    UMaterialExpressionAdd* Shifted = NewObject<UMaterialExpressionAdd>(Material);
    Shifted->A.Expression = UpMask; Shifted->B.Expression = Bias; Add(Shifted);
    UMaterialExpressionMultiply* Sharpen = NewObject<UMaterialExpressionMultiply>(Material);
    Sharpen->A.Expression = Shifted; Sharpen->ConstB = 6.0f; Add(Sharpen);
    UMaterialExpressionClamp* Flatness =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    Flatness->Input.Expression = Sharpen; Flatness->MinDefault = 0.0f; Flatness->MaxDefault = 1.0f;

    // M4 full-reach terrain stores source-conditioned NAIP macro colour in
    // RGB vertex colour and the wet-bank mask in alpha. Nanite does not expose
    // painted RGB reliably in every material permutation, so production tiles
    // also bind the registered macro as a compact texture. Resolve the source
    // once and reuse it for both broad colour and geologic exposure.
    UMaterialExpressionVertexColor* VertexMacro =
        Cast<UMaterialExpressionVertexColor>(Add(NewObject<UMaterialExpressionVertexColor>(Material)));
    UMaterialExpressionComponentMask* VertexMacroRgb =
        NewObject<UMaterialExpressionComponentMask>(Material);
    VertexMacroRgb->Input.Expression = VertexMacro;
    VertexMacroRgb->R = true;
    VertexMacroRgb->G = true;
    VertexMacroRgb->B = true;
    VertexMacroRgb->A = false;
    Add(VertexMacroRgb);
    UMaterialExpressionMultiply* BrightenedMacro = NewObject<UMaterialExpressionMultiply>(Material);
    BrightenedMacro->A.Expression = VertexMacroRgb;
    BrightenedMacro->ConstB = 1.0f;
    Add(BrightenedMacro);
    UMaterialExpressionSaturate* BoundedMacro =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    BoundedMacro->Input.Expression = BrightenedMacro;

    UMaterialExpressionTextureCoordinate* MacroUv =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    MacroUv->CoordinateIndex = 0;
    UMaterialExpressionTextureSampleParameter2D* SourceMacroTexture =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    SourceMacroTexture->ParameterName = TEXT("SourceMacroTexture");
    SourceMacroTexture->Texture = GroundAlbedo;
    SourceMacroTexture->SamplerType = SAMPLERTYPE_Color;
    SourceMacroTexture->Coordinates.Expression = MacroUv;
    UMaterialExpressionScalarParameter* UseSourceMacroTexture =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    UseSourceMacroTexture->ParameterName = TEXT("UseSourceMacroTexture");
    UseSourceMacroTexture->DefaultValue = 0.0f;
    UseSourceMacroTexture->Group = TEXT("RaftSimPhotorealTerrain");
    Add(UseSourceMacroTexture);
    UMaterialExpressionLinearInterpolate* ResolvedSourceMacro =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ResolvedSourceMacro->A.Expression = BoundedMacro;
    ResolvedSourceMacro->B.Expression = SourceMacroTexture;
    ResolvedSourceMacro->Alpha.Expression = UseSourceMacroTexture;
    Add(ResolvedSourceMacro);

    // Preserve continuous source colour while restoring visible geology. A
    // direct rock/ground slope lerp exposed the coarse far-field triangles as
    // kilometre-scale pale polygons. The old four-octave per-pixel noise hid
    // those facets but was one of the most expensive operations over the large
    // visible hills. Use the already sampled registered macro instead: red
    // dominance raises exposed soil/rock while green dominance suppresses it
    // under canopy. This is cheaper and ties breakup to source geography.
    UMaterialExpressionMultiply* InvertedFlatness =
        NewObject<UMaterialExpressionMultiply>(Material);
    InvertedFlatness->A.Expression = Flatness;
    InvertedFlatness->ConstB = -1.0f;
    Add(InvertedFlatness);
    UMaterialExpressionAdd* Steepness = NewObject<UMaterialExpressionAdd>(Material);
    Steepness->A.Expression = InvertedFlatness;
    Steepness->ConstB = 1.0f;
    Add(Steepness);
    UMaterialExpressionComponentMask* MacroRed =
        NewObject<UMaterialExpressionComponentMask>(Material);
    MacroRed->Input.Expression = ResolvedSourceMacro;
    MacroRed->R = true;
    MacroRed->G = MacroRed->B = MacroRed->A = false;
    Add(MacroRed);
    UMaterialExpressionComponentMask* MacroGreen =
        NewObject<UMaterialExpressionComponentMask>(Material);
    MacroGreen->Input.Expression = ResolvedSourceMacro;
    MacroGreen->R = false;
    MacroGreen->G = true;
    MacroGreen->B = MacroGreen->A = false;
    Add(MacroGreen);
    UMaterialExpressionMultiply* InvertedMacroGreen =
        NewObject<UMaterialExpressionMultiply>(Material);
    InvertedMacroGreen->A.Expression = MacroGreen;
    InvertedMacroGreen->ConstB = -1.0f;
    Add(InvertedMacroGreen);
    UMaterialExpressionAdd* RedMinusGreen = NewObject<UMaterialExpressionAdd>(Material);
    RedMinusGreen->A.Expression = MacroRed;
    RedMinusGreen->B.Expression = InvertedMacroGreen;
    Add(RedMinusGreen);
    UMaterialExpressionMultiply* GeologicSignalGain =
        NewObject<UMaterialExpressionMultiply>(Material);
    GeologicSignalGain->A.Expression = RedMinusGreen;
    GeologicSignalGain->ConstB = 4.0f;
    Add(GeologicSignalGain);
    UMaterialExpressionAdd* GeologicSignalBias = NewObject<UMaterialExpressionAdd>(Material);
    GeologicSignalBias->A.Expression = GeologicSignalGain;
    GeologicSignalBias->ConstB = 0.55f;
    Add(GeologicSignalBias);
    UMaterialExpressionSaturate* SourceGeologicSignal =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    SourceGeologicSignal->Input.Expression = GeologicSignalBias;
    UMaterialExpressionMultiply* ScaledSourceGeologicSignal =
        NewObject<UMaterialExpressionMultiply>(Material);
    ScaledSourceGeologicSignal->A.Expression = SourceGeologicSignal;
    ScaledSourceGeologicSignal->ConstB = 0.72f;
    Add(ScaledSourceGeologicSignal);
    UMaterialExpressionAdd* RockBreakup = NewObject<UMaterialExpressionAdd>(Material);
    RockBreakup->A.Expression = ScaledSourceGeologicSignal;
    RockBreakup->ConstB = 0.28f;
    Add(RockBreakup);
    UMaterialExpressionMultiply* BrokenSteepness =
        NewObject<UMaterialExpressionMultiply>(Material);
    BrokenSteepness->A.Expression = Steepness;
    BrokenSteepness->B.Expression = RockBreakup;
    Add(BrokenSteepness);
    UMaterialExpressionScalarParameter* RockAlbedoStrength =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    RockAlbedoStrength->ParameterName = TEXT("RockAlbedoStrength");
    RockAlbedoStrength->DefaultValue = 0.90f;
    RockAlbedoStrength->Group = TEXT("RaftSimPhotorealTerrain");
    Add(RockAlbedoStrength);
    UMaterialExpressionMultiply* ScaledRockMask =
        NewObject<UMaterialExpressionMultiply>(Material);
    ScaledRockMask->A.Expression = BrokenSteepness;
    ScaledRockMask->B.Expression = RockAlbedoStrength;
    Add(ScaledRockMask);
    UMaterialExpressionClamp* RockAlbedoMask =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    RockAlbedoMask->Input.Expression = ScaledRockMask;
    RockAlbedoMask->MinDefault = 0.0f;
    RockAlbedoMask->MaxDefault = 0.92f;

    UMaterialExpression* BaseColor = LerpRefs(GrA, RockA, RockAlbedoMask);
    UMaterialExpression* Normal = LerpRefs(RockN, GrN, Flatness);
    UMaterialExpression* Roughness = LerpRefs(RockR, GrR, Flatness);

    // The reviewed 1.5-2.0 m triplanar maps are valuable in the detailed
    // corridor, but cannot resolve on hills several kilometres from the guide.
    // Static switches let far-field instances compile those six world-aligned
    // texture functions out instead of merely lerping away their results after
    // paying the sample cost. Registered macro colour and geometric normals
    // remain authoritative in the far field; legacy/local users keep the full
    // detail path through the true defaults.
    UMaterialExpressionStaticSwitchParameter* UseTerrainMicroAlbedo =
        NewObject<UMaterialExpressionStaticSwitchParameter>(Material);
    UMaterialExpressionConstant3Vector* FarFieldDryGroundColor =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    FarFieldDryGroundColor->Constant = FLinearColor(0.42f, 0.28f, 0.14f, 1.0f);
    Add(FarFieldDryGroundColor);
    UseTerrainMicroAlbedo->ParameterName = TEXT("UseTerrainMicroAlbedo");
    UseTerrainMicroAlbedo->DefaultValue = true;
    UseTerrainMicroAlbedo->A.Expression = BaseColor;
    UseTerrainMicroAlbedo->B.Expression = FarFieldDryGroundColor;
    Add(UseTerrainMicroAlbedo);
    UMaterialExpressionStaticSwitchParameter* UseTerrainMicroNormal =
        NewObject<UMaterialExpressionStaticSwitchParameter>(Material);
    UseTerrainMicroNormal->ParameterName = TEXT("UseTerrainMicroNormal");
    UseTerrainMicroNormal->DefaultValue = true;
    UseTerrainMicroNormal->A.Expression = Normal;
    UseTerrainMicroNormal->B.Expression = VN;
    Add(UseTerrainMicroNormal);
    UMaterialExpressionConstant* FarFieldRoughness =
        NewObject<UMaterialExpressionConstant>(Material);
    FarFieldRoughness->R = 0.82f;
    Add(FarFieldRoughness);
    UMaterialExpressionStaticSwitchParameter* UseTerrainMicroRoughness =
        NewObject<UMaterialExpressionStaticSwitchParameter>(Material);
    UseTerrainMicroRoughness->ParameterName = TEXT("UseTerrainMicroRoughness");
    UseTerrainMicroRoughness->DefaultValue = true;
    UseTerrainMicroRoughness->A.Expression = Roughness;
    UseTerrainMicroRoughness->B.Expression = FarFieldRoughness;
    Add(UseTerrainMicroRoughness);

    // The detailed curvilinear ribbon is intentionally bounded to +/-64 m so
    // it cannot fold over in tight bends. Blend from the exposed bank toward
    // wooded canyon tone used by the source-backed far field, masking small
    // exposure differences between independent NAIP window products without
    // changing height, collision, or the inner gameplay corridor.
    UMaterialExpressionComponentMask* MacroU =
        NewObject<UMaterialExpressionComponentMask>(Material);
    MacroU->Input.Expression = MacroUv;
    MacroU->R = true;
    MacroU->G = MacroU->B = MacroU->A = false;
    Add(MacroU);
    UMaterialExpressionAdd* CenteredMacroU = NewObject<UMaterialExpressionAdd>(Material);
    CenteredMacroU->A.Expression = MacroU;
    CenteredMacroU->ConstB = -0.5f;
    Add(CenteredMacroU);
    UMaterialExpressionAbs* AbsoluteMacroU =
        Cast<UMaterialExpressionAbs>(Add(NewObject<UMaterialExpressionAbs>(Material)));
    AbsoluteMacroU->Input.Expression = CenteredMacroU;
    UMaterialExpressionAdd* EdgeStart = NewObject<UMaterialExpressionAdd>(Material);
    EdgeStart->A.Expression = AbsoluteMacroU;
    EdgeStart->ConstB = -0.045f;
    Add(EdgeStart);
    UMaterialExpressionMultiply* EdgeGain = NewObject<UMaterialExpressionMultiply>(Material);
    EdgeGain->A.Expression = EdgeStart;
    EdgeGain->ConstB = 12.5f;
    Add(EdgeGain);
    UMaterialExpressionSaturate* EdgeMask =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    EdgeMask->Input.Expression = EdgeGain;
    UMaterialExpressionMultiply* TexturedEdgeMask = NewObject<UMaterialExpressionMultiply>(Material);
    TexturedEdgeMask->A.Expression = EdgeMask;
    TexturedEdgeMask->B.Expression = UseSourceMacroTexture;
    Add(TexturedEdgeMask);
    UMaterialExpressionScalarParameter* UseCorridorEdgeBlend =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    UseCorridorEdgeBlend->ParameterName = TEXT("UseCorridorEdgeBlend");
    UseCorridorEdgeBlend->DefaultValue = 1.0f;
    UseCorridorEdgeBlend->Group = TEXT("RaftSimPhotorealTerrain");
    Add(UseCorridorEdgeBlend);
    UMaterialExpressionMultiply* ResolvedEdgeMask =
        NewObject<UMaterialExpressionMultiply>(Material);
    ResolvedEdgeMask->A.Expression = TexturedEdgeMask;
    ResolvedEdgeMask->B.Expression = UseCorridorEdgeBlend;
    Add(ResolvedEdgeMask);
    UMaterialExpressionScalarParameter* MacroInfluence =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    MacroInfluence->ParameterName = TEXT("SourceMacroInfluence");
    // Preserve the authoritative aerial-scale hue while allowing the reviewed
    // rock/forest albedo to provide the missing sub-meter soil, scree, and
    // litter structure. A value of 1.0 reduced the production terrain to a
    // smooth vertex-color drape even though its normal map still had detail.
    MacroInfluence->DefaultValue = 0.64f;
    MacroInfluence->Group = TEXT("RaftSimPhotorealTerrain");
    Add(MacroInfluence);
    UMaterialExpressionConstant* FullMacroInfluence =
        NewObject<UMaterialExpressionConstant>(Material);
    FullMacroInfluence->R = 1.0f;
    Add(FullMacroInfluence);
    UMaterialExpressionLinearInterpolate* ResolvedMacroInfluence =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ResolvedMacroInfluence->A.Expression = MacroInfluence;
    ResolvedMacroInfluence->B.Expression = FullMacroInfluence;
    ResolvedMacroInfluence->Alpha.Expression = ResolvedEdgeMask;
    Add(ResolvedMacroInfluence);
    UMaterialExpressionLinearInterpolate* SourceConditionedBase =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SourceConditionedBase->A.Expression = UseTerrainMicroAlbedo;
    SourceConditionedBase->B.Expression = ResolvedSourceMacro;
    SourceConditionedBase->Alpha.Expression = ResolvedMacroInfluence;
    Add(SourceConditionedBase);

    // The captured aerial macro is exposed for image analysis rather than a
    // game renderer. Bring it into the luminance range of a sunlit Sierra
    // canyon while retaining its measured hue and large-scale variation.
    UMaterialExpressionVectorParameter* TerrainTone =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    TerrainTone->ParameterName = TEXT("SourceMacroTone");
    TerrainTone->Group = TEXT("RaftSimPhotorealTerrain");
    // Keep USGS/NAIP hue relationships intact.  The former red-heavy
    // multiplier turned both source macro imagery and neutral rock albedo into
    // a uniform orange-beige sheet in every fixed camera.
    TerrainTone->DefaultValue = FLinearColor(0.72f, 0.78f, 0.70f, 1.0f);
    Add(TerrainTone);
    UMaterialExpressionVectorParameter* FarFieldTerrainTone =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    FarFieldTerrainTone->ParameterName = TEXT("FarFieldSourceMacroTone");
    FarFieldTerrainTone->DefaultValue = FLinearColor(0.62f, 0.68f, 0.60f, 1.0f);
    FarFieldTerrainTone->Group = TEXT("RaftSimPhotorealTerrain");
    Add(FarFieldTerrainTone);
    UMaterialExpressionLinearInterpolate* ResolvedTerrainTone =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ResolvedTerrainTone->A.Expression = TerrainTone;
    ResolvedTerrainTone->B.Expression = FarFieldTerrainTone;
    ResolvedTerrainTone->Alpha.Expression = ResolvedEdgeMask;
    Add(ResolvedTerrainTone);
    UMaterialExpressionMultiply* TonedBase = NewObject<UMaterialExpressionMultiply>(Material);
    TonedBase->A.Expression = SourceConditionedBase;
    TonedBase->B.Expression = ResolvedTerrainTone;
    Add(TonedBase);

    // The runnable Chili Bar-to-Folsom terrain uses this parent rather than
    // the review Landscape material. Apply the same world-space foothill
    // model at a subtler strength so registered NAIP colour remains dominant
    // while broad repeated ground tiles no longer read as a smooth plate.
    UMaterialExpression* OrganicTonedBase =
        RaftSimEditorEnvironment::BuildSouthForkOrganicFoothillBaseColor(
            Material,
            TonedBase,
            0.30f);
    if (!OrganicTonedBase)
    {
        OrganicTonedBase = TonedBase;
    }

    UMaterialExpressionConstant3Vector* WetDarkColor =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    WetDarkColor->Constant = FLinearColor(0.38f, 0.42f, 0.40f, 1.0f);
    Add(WetDarkColor);
    UMaterialExpressionMultiply* WetDarkBase = NewObject<UMaterialExpressionMultiply>(Material);
    WetDarkBase->A.Expression = OrganicTonedBase;
    WetDarkBase->B.Expression = WetDarkColor;
    Add(WetDarkBase);
    UMaterialExpressionLinearInterpolate* WetAwareBase =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    WetAwareBase->A.Expression = OrganicTonedBase;
    WetAwareBase->B.Expression = WetDarkBase;
    WetAwareBase->Alpha.Expression = VertexMacro;
    WetAwareBase->Alpha.OutputIndex = 4; // dedicated vertex-alpha output
    Add(WetAwareBase);

    UMaterialExpressionConstant* WetRoughness = NewObject<UMaterialExpressionConstant>(Material);
    WetRoughness->R = 0.18f;
    Add(WetRoughness);
    UMaterialExpressionLinearInterpolate* WetAwareRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    WetAwareRoughness->A.Expression = Roughness;
    WetAwareRoughness->B.Expression = WetRoughness;
    WetAwareRoughness->Alpha.Expression = VertexMacro;
    WetAwareRoughness->Alpha.OutputIndex = 4;
    Add(WetAwareRoughness);
    UseTerrainMicroRoughness->A.Expression = WetAwareRoughness;

    UMaterialExpressionScalarParameter* Specular = NewObject<UMaterialExpressionScalarParameter>(Material);
    Specular->ParameterName = TEXT("TerrainSpecular"); Specular->DefaultValue = 0.25f;
    Specular->Group = TEXT("RaftSimPhotorealTerrain"); Add(Specular);

    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, WetAwareBase);
    Ed->Roughness.Connect(0, UseTerrainMicroRoughness);
    Ed->Specular.Connect(0, Specular);
    Ed->Normal.Connect(0, UseTerrainMicroNormal);

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

    UE_LOG(LogTemp, Display, TEXT("RaftSim: M_RaftSim_PhotorealRiverTerrain saved=%d"), bSaved ? 1 : 0);
    return Material;
}

// A simple solid-colour lit material (raft tubes, crew PFDs) so the gameplay
// props read as real objects rather than the default checkerboard.
static UMaterial* BuildSolidMaterial(
    const TCHAR* AssetName, const FLinearColor& Color, float Roughness, float Metallic,
    bool bTwoSided = false)
{
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Materials/%s"), AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (Package == nullptr)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, *ObjectPath));
    if (Material == nullptr)
    {
        Material = NewObject<UMaterial>(Package, AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (Material == nullptr)
    {
        return nullptr;
    }
    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = bTwoSided;
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);
    Material->SetMaterialUsage(MATUSAGE_Nanite);

    UMaterialExpressionConstant3Vector* BaseColor = NewObject<UMaterialExpressionConstant3Vector>(Material);
    BaseColor->Constant = Color;
    Material->GetExpressionCollection().AddExpression(BaseColor);
    UMaterialExpressionConstant* Rough = NewObject<UMaterialExpressionConstant>(Material);
    Rough->R = Roughness;
    Material->GetExpressionCollection().AddExpression(Rough);
    UMaterialExpressionConstant* Metal = NewObject<UMaterialExpressionConstant>(Material);
    Metal->R = Metallic;
    Material->GetExpressionCollection().AddExpression(Metal);

    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Expression = nullptr;
    Ed->Roughness.Expression = nullptr;
    Ed->Metallic.Expression = nullptr;
    Ed->Specular.Expression = nullptr;
    Ed->Normal.Expression = nullptr;
    Ed->AmbientOcclusion.Expression = nullptr;
    Ed->EmissiveColor.Expression = nullptr;
    Ed->BaseColor.Connect(0, BaseColor);
    Ed->Roughness.Connect(0, Rough);
    Ed->Metallic.Connect(0, Metal);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        *PackagePath, FPackageName::GetAssetPackageExtension());
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: %s saved=%d"), AssetName, bSaved ? 1 : 0);
    return Material;
}

// Project-owned wet river-rock material for procedural D4 contacts and the
// generated fallback boulder set. The former solid ochre material turned a
// physically useful contact into a flat beige sphere under morning light.
// World-space multi-octave noise gives the same deterministic mesh dark wet
// seams, mineral breakup, and spatially varying roughness without claiming a
// scanned geology source or depending on an external review asset.
static UMaterial* BuildRiverBoulderMaterial(
    const TCHAR* AssetName = TEXT("M_RaftSim_RiverBoulder"),
    const TCHAR* PackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder"),
    const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder.M_RaftSim_RiverBoulder"),
    bool bIncludeReviewedSource = true)
{
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
    // Emptying the expression collection alone leaves the former expression
    // UObjects in the package. That can preserve soft references from an old,
    // disconnected branch and make a clean Shipping cook fail even though the
    // editor preview compiles. Garbage the old exports before rebuilding the
    // graph so regeneration is genuinely authoritative and idempotent.
    for (TObjectPtr<UMaterialExpression>& ExistingExpression :
         Material->GetExpressionCollection().Expressions)
    {
        if (ExistingExpression)
        {
            // Texture-backed parameter expressions can be root-held while the
            // editor finishes an async compile. Release that temporary hold
            // before retiring the old export; MarkAsGarbage asserts on rooted
            // UObjects and previously made this idempotent authoring command
            // crash on its second run.
            if (ExistingExpression->IsRooted())
            {
                ExistingExpression->RemoveFromRoot();
            }
            ExistingExpression->MarkAsGarbage();
        }
    }
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    // The production-default generated boulder is a closed shell. One-sided
    // shading preserves outward geometric normals at the clipped waterline.
    Material->TwoSided = false;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);
    Material->SetMaterialUsage(MATUSAGE_Nanite);

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value)
    {
        UMaterialExpressionConstant* Expression =
            NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        Add(Expression);
        return Expression;
    };
    auto Color = [&](const FLinearColor& Value)
    {
        UMaterialExpressionConstant3Vector* Expression =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        Expression->Constant = Value;
        Add(Expression);
        return Expression;
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B,
                    UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        Add(Expression);
        return Expression;
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };
    auto AddValues = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Expression =
            NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };

    UMaterialExpressionNoise* CoarseMineralNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    CoarseMineralNoise->Scale = 0.016f;
    CoarseMineralNoise->Levels = 4;
    CoarseMineralNoise->bTurbulence = true;
    CoarseMineralNoise->OutputMin = 0.0f;
    CoarseMineralNoise->OutputMax = 1.0f;

    UMaterialExpressionNoise* FineMineralNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    FineMineralNoise->Scale = 0.055f;
    FineMineralNoise->Levels = 3;
    FineMineralNoise->bTurbulence = true;
    FineMineralNoise->OutputMin = 0.0f;
    FineMineralNoise->OutputMax = 1.0f;

    UMaterialExpression* RockBaseColor = nullptr;
    UMaterialExpression* RockRoughness = nullptr;
    UMaterialExpression* RockNormal = nullptr;
    UMaterialExpression* RockOcclusion = Lerp(
        Constant(0.72f), Constant(1.0f), FineMineralNoise);

    // The shared material serves two deliberately distinct visual sources.
    // Generated D4 shells write vertex alpha zero and stay entirely on this
    // project-owned mineral-noise branch. The reviewed static scan supplies
    // the default alpha-one vertex value and may use its UV-authored textures
    // only in the explicit renderer diagnostic path.
    const FLinearColor DarkMineral = bIncludeReviewedSource
        ? FLinearColor(0.090f, 0.101f, 0.105f, 1.0f)
        : FLinearColor(0.003f, 0.004f, 0.005f, 1.0f);
    const FLinearColor MidMineral = bIncludeReviewedSource
        ? FLinearColor(0.220f, 0.208f, 0.188f, 1.0f)
        : FLinearColor(0.012f, 0.011f, 0.010f, 1.0f);
    const FLinearColor LightMineral = bIncludeReviewedSource
        ? FLinearColor(0.340f, 0.308f, 0.264f, 1.0f)
        : FLinearColor(0.028f, 0.025f, 0.021f, 1.0f);
    UMaterialExpressionLinearInterpolate* ProceduralMineralColor = Lerp(
        Color(DarkMineral),
        Color(MidMineral),
        CoarseMineralNoise);
    UMaterialExpression* ProceduralBaseColor = Lerp(
        ProceduralMineralColor,
        Color(LightMineral),
        FineMineralNoise);
    UMaterialExpression* ProceduralRoughness = Lerp(
        Constant(bIncludeReviewedSource ? 0.34f : 0.82f),
        Constant(bIncludeReviewedSource ? 0.72f : 0.96f),
        CoarseMineralNoise);
    UMaterialExpressionVertexColor* VisualSourceVertexColor =
        Cast<UMaterialExpressionVertexColor>(
            Add(NewObject<UMaterialExpressionVertexColor>(Material)));
    UMaterialExpressionScalarParameter* VisualSourceBlend =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    VisualSourceBlend->ParameterName = TEXT("RockVisualSourceBlend");
    VisualSourceBlend->DefaultValue = 1.0f;
    VisualSourceBlend->Group = TEXT("RaftSimRiverBoulder");
    Add(VisualSourceBlend);
    UMaterialExpressionMultiply* SelectedVisualSource =
        Multiply(VisualSourceVertexColor, VisualSourceBlend);
    SelectedVisualSource->A.OutputIndex = 4;

    // The visual shell can use this already hash-reviewed CC0 generic-rock
    // scan. It is an appearance analog, not South Fork geology authority. The
    // material asset is still project-owned and the deterministic noise branch
    // below remains a complete fallback when those optional source textures are
    // absent during authoring.
    UTexture2D* ReviewedBaseColor = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockMossSet01_1K/T_RockMossSet01_BaseColor_1K."
             "T_RockMossSet01_BaseColor_1K"));
    UTexture2D* ReviewedRoughness = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockMossSet01_1K/T_RockMossSet01_Roughness_1K."
             "T_RockMossSet01_Roughness_1K"));
    UTexture2D* ReviewedNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockMossSet01_1K/T_RockMossSet01_NormalGL_1K."
             "T_RockMossSet01_NormalGL_1K"));
    if (bIncludeReviewedSource && ReviewedBaseColor && ReviewedRoughness)
    {
        // The full-strength reviewed diffuse is mossy/ochre and failed the wet
        // South Fork read. Retain its real mineral-scale variation while
        // removing most source hue, applying a neutral cool mineral tint, and
        // bounding macro brightness with project-authored deterministic noise.
        // The prior 0.20 tint crushed shaded faces to black in the renderer
        // acceptance frame; this range remains wet and dark without discarding
        // physically useful midtone structure.
        UMaterialExpressionTextureSampleParameter2D* BaseColorSample =
            Cast<UMaterialExpressionTextureSampleParameter2D>(
                Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        BaseColorSample->ParameterName = TEXT("ReviewedRockBaseColor");
        BaseColorSample->Texture = ReviewedBaseColor;
        BaseColorSample->SamplerType = SAMPLERTYPE_Color;
        BaseColorSample->Group = TEXT("RaftSimRiverBoulder");
        UMaterialExpressionDesaturation* DesaturatedBase =
            Cast<UMaterialExpressionDesaturation>(
                Add(NewObject<UMaterialExpressionDesaturation>(Material)));
        DesaturatedBase->Input.Expression = BaseColorSample;
        DesaturatedBase->Fraction.Expression = Constant(0.80f);
        UMaterialExpression* TintedBase = Multiply(
            DesaturatedBase,
            Color(FLinearColor(0.54f, 0.57f, 0.59f, 1.0f)));
        UMaterialExpression* ReviewedTintedBaseColor = Multiply(
            TintedBase,
            Lerp(Constant(0.78f), Constant(1.08f), CoarseMineralNoise));

        UMaterialExpressionTextureSampleParameter2D* RoughnessSample =
            Cast<UMaterialExpressionTextureSampleParameter2D>(
                Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        RoughnessSample->ParameterName = TEXT("ReviewedRockRoughness");
        RoughnessSample->Texture = ReviewedRoughness;
        RoughnessSample->SamplerType = SAMPLERTYPE_Masks;
        RoughnessSample->Group = TEXT("RaftSimRiverBoulder");
        UMaterialExpressionMultiply* ScaledRoughness =
            Multiply(RoughnessSample, Constant(0.52f));
        ScaledRoughness->A.OutputIndex = 1;
        UMaterialExpression* ReviewedRockRoughness =
            AddValues(ScaledRoughness, Constant(0.20f));
        UMaterialExpressionLinearInterpolate* BaseColorSourceBlend = Lerp(
            ProceduralBaseColor, ReviewedTintedBaseColor, SelectedVisualSource);
        RockBaseColor = BaseColorSourceBlend;
        UMaterialExpressionLinearInterpolate* RoughnessSourceBlend = Lerp(
            ProceduralRoughness, ReviewedRockRoughness, SelectedVisualSource);
        RockRoughness = RoughnessSourceBlend;

        if (ReviewedNormal)
        {
            UMaterialExpressionTextureSampleParameter2D* NormalSample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            NormalSample->ParameterName = TEXT("ReviewedRockNormal");
            NormalSample->Texture = ReviewedNormal;
            NormalSample->SamplerType = SAMPLERTYPE_Normal;
            NormalSample->Group = TEXT("RaftSimRiverBoulder");
            UMaterialExpressionLinearInterpolate* NormalSourceBlend = Lerp(
                Color(FLinearColor(0.5f, 0.5f, 1.0f, 1.0f)),
                NormalSample,
                SelectedVisualSource);
            RockNormal = NormalSourceBlend;
        }
    }
    else
    {
        RockBaseColor = ProceduralBaseColor;
        RockRoughness = ProceduralRoughness;
    }

    // --- Solver-driven waterline wet band ---------------------------------
    // Real river rock carries a dark, glossy wet band at and below the water
    // surface. Individual rock actors may write the sampled live surface into
    // RockWaterlineZCm. Instanced talus instead supplies the conditioned local
    // visual surface through custom-data channel zero. Max resolves those two
    // bindings while both fail-safe defaults remain far below any reach. This
    // keeps unset rocks dry and lets one HISM material follow a curved profile
    // without inventing a single flat river plane. A small world-space noise
    // breaks the resulting line so it never reads as a ruler.
    UMaterialExpressionScalarParameter* WaterlineZ = NewObject<UMaterialExpressionScalarParameter>(Material);
    WaterlineZ->ParameterName = TEXT("RockWaterlineZCm");
    WaterlineZ->DefaultValue = -1.0e7f;
    WaterlineZ->Group = TEXT("RaftSimRiverBoulder");
    Add(WaterlineZ);
    UMaterialExpressionPerInstanceCustomData* PerInstanceWaterlineZ =
        NewObject<UMaterialExpressionPerInstanceCustomData>(Material);
    PerInstanceWaterlineZ->DataIndex = 0;
    PerInstanceWaterlineZ->ConstDefaultValue = -1.0e7f;
    Add(PerInstanceWaterlineZ);
    UMaterialExpressionMax* ResolvedWaterlineZ =
        NewObject<UMaterialExpressionMax>(Material);
    ResolvedWaterlineZ->A.Expression = WaterlineZ;
    ResolvedWaterlineZ->B.Expression = PerInstanceWaterlineZ;
    Add(ResolvedWaterlineZ);
    UMaterialExpressionScalarParameter* WetBandWidth = NewObject<UMaterialExpressionScalarParameter>(Material);
    WetBandWidth->ParameterName = TEXT("RockWetBandWidthCm");
    WetBandWidth->DefaultValue = 55.0f;
    WetBandWidth->Group = TEXT("RaftSimRiverBoulder");
    Add(WetBandWidth);

    UMaterialExpressionWorldPosition* WetWorldPosition =
        Cast<UMaterialExpressionWorldPosition>(Add(NewObject<UMaterialExpressionWorldPosition>(Material)));
    UMaterialExpressionComponentMask* WorldZ = NewObject<UMaterialExpressionComponentMask>(Material);
    WorldZ->Input.Expression = WetWorldPosition;
    WorldZ->R = false; WorldZ->G = false; WorldZ->B = true; WorldZ->A = false;
    Add(WorldZ);

    UMaterialExpressionNoise* WetlineNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    WetlineNoise->Scale = 0.045f;
    WetlineNoise->Levels = 3;
    WetlineNoise->bTurbulence = true;
    WetlineNoise->OutputMin = -18.0f;
    WetlineNoise->OutputMax = 18.0f;

    // height above waterline (cm), jittered: WorldZ - WaterlineZ + noise
    UMaterialExpressionSubtract* HeightAbove = NewObject<UMaterialExpressionSubtract>(Material);
    HeightAbove->A.Expression = WorldZ;
    HeightAbove->B.Expression = ResolvedWaterlineZ;
    Add(HeightAbove);
    UMaterialExpressionAdd* JitteredHeight = NewObject<UMaterialExpressionAdd>(Material);
    JitteredHeight->A.Expression = HeightAbove;
    JitteredHeight->B.Expression = WetlineNoise;
    Add(JitteredHeight);
    UMaterialExpressionDivide* BandFraction = NewObject<UMaterialExpressionDivide>(Material);
    BandFraction->A.Expression = JitteredHeight;
    BandFraction->B.Expression = WetBandWidth;
    Add(BandFraction);
    UMaterialExpressionOneMinus* InvertedBand = NewObject<UMaterialExpressionOneMinus>(Material);
    InvertedBand->Input.Expression = BandFraction;
    Add(InvertedBand);
    UMaterialExpressionClamp* WetMask =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    WetMask->Input.Expression = InvertedBand;
    WetMask->MinDefault = 0.0f;
    WetMask->MaxDefault = 1.0f;

    // Wet rock: darkened, slightly cool albedo and a hard roughness drop.
    UMaterialExpressionMultiply* DarkenedBase = NewObject<UMaterialExpressionMultiply>(Material);
    DarkenedBase->A.Expression = RockBaseColor;
    DarkenedBase->B.Expression = Color(FLinearColor(0.44f, 0.46f, 0.50f, 1.0f));
    Add(DarkenedBase);
    UMaterialExpressionLinearInterpolate* WetBaseColor =
        Lerp(RockBaseColor, DarkenedBase, WetMask);
    UMaterialExpressionLinearInterpolate* WetRoughness =
        Lerp(RockRoughness, Constant(bIncludeReviewedSource ? 0.16f : 0.46f), WetMask);
    UMaterialExpressionLinearInterpolate* WetSpecular =
        Lerp(
            Constant(bIncludeReviewedSource ? 0.26f : 0.08f),
            Constant(bIncludeReviewedSource ? 0.42f : 0.14f),
            WetMask);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, WetBaseColor);
    EditorData->Roughness.Connect(0, WetRoughness);
    EditorData->Specular.Connect(0, WetSpecular);
    EditorData->AmbientOcclusion.Connect(0, RockOcclusion);
    if (RockNormal)
    {
        EditorData->Normal.Connect(0, RockNormal);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim: %s wet mineral material saved=%d"),
        AssetName, bSaved ? 1 : 0);
    return bSaved ? Material : nullptr;
}

// Surface-lit alpha overlay for the moving solver mesh. The authored river
// directly beneath it already supplies the Single Layer Water volume, so this
// material carries only the live surface response: solver depth/foam vertex
// channels, geometric normals, and a restrained animated micro-normal. It has
// no refraction or water-volume output and therefore cannot double the volume.
static UMaterial* BuildLiveRiverSurfaceMaterial()
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

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Translucent;
    Material->TranslucencyLightingMode = TLM_SurfacePerPixelLighting;
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
    UMaterialExpressionComponentMask* StationEdgeCoverage =
        Mask(VertexColor, true, false, false);
    // VertexColor's default expression output is RGB. Alpha is UE's dedicated
    // scalar output 4, so select it before applying the component mask. Trying
    // to mask A from output 0 compiles in C++ but fails the Metal material.
    StationEdgeCoverage->Input.OutputIndex = 4;

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

    UMaterialExpressionNoise* FoamNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    FoamNoise->Scale = 0.009f;
    FoamNoise->bTurbulence = true;
    FoamNoise->Levels = 4;
    FoamNoise->OutputMin = 0.20f;
    FoamNoise->OutputMax = 1.20f;
    UMaterialExpressionMultiply* FoamRaw = Mul(
        Mul(FoamMask, FoamNoise), Scalar(TEXT("LiveFoamIntensity"), 0.52f));
    UMaterialExpressionClamp* Foam =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    Foam->Input.Expression = FoamRaw;
    Foam->MinDefault = 0.0f;
    Foam->MaxDefault = 1.0f;
    UMaterialExpressionLinearInterpolate* BaseColor = Lerp(
        ReflectedDepthColor, Const3(0.70f, 0.74f, 0.74f), Foam);

    UMaterialExpressionLinearInterpolate* Roughness = Lerp(
        Scalar(TEXT("LiveWaterRoughness"), 0.085f),
        Scalar(TEXT("LiveFoamRoughness"), 0.58f),
        Foam);

    UMaterialExpression* FinalNormal = nullptr;
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
        auto Ripple = [&](UMaterialExpression* Coordinates,
                          const TCHAR* ParameterName,
                          float SpeedX,
                          float SpeedY) -> UMaterialExpression*
        {
            UMaterialExpressionPanner* Pan =
                Cast<UMaterialExpressionPanner>(
                    Add(NewObject<UMaterialExpressionPanner>(Material)));
            Pan->SpeedX = SpeedX;
            Pan->SpeedY = SpeedY;
            Pan->Coordinate.Expression = Coordinates;
            UMaterialExpressionTextureSampleParameter2D* Sample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            Sample->ParameterName = ParameterName;
            Sample->Texture = DetailNormal;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = Pan;
            return Sample;
        };
        UMaterialExpression* PrimaryNormal = Ripple(
            UV, TEXT("LiveWaterFlowNormalPrimary"), 0.082f, 0.014f);
        UMaterialExpression* CrossNormal = Ripple(
            CrossUv, TEXT("LiveWaterFlowNormalCross"), -0.029f, 0.071f);
        UMaterialExpression* CrossPerturbation = AddNode(
            CrossNormal, Const3(0.0f, 0.0f, -1.0f));
        UMaterialExpressionNormalize* CombinedNormal =
            Cast<UMaterialExpressionNormalize>(
                Add(NewObject<UMaterialExpressionNormalize>(Material)));
        CombinedNormal->VectorInput.Expression = AddNode(
            PrimaryNormal, CrossPerturbation);
        UMaterialExpressionScalarParameter* LiveNormalStrength =
            Scalar(TEXT("LiveRippleStrength"), 0.18f);
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
                Scalar(TEXT("LiveRippleGrazingFloor"), 0.50f)),
            LiveRippleGrazingFresnel);
        FinalNormal = Lerp(
            LiveFlatN,
            CombinedNormal,
            LiveGrazingFilteredNormalStrength);
    }

    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, BaseColor);
    Ed->Roughness.Connect(0, Roughness);
    Ed->Specular.Connect(0, Scalar(TEXT("LiveWaterSpecular"), 0.48f));

    // Calm reaches gain their colour and volumetric response from the authored
    // surface directly below. Retain a bounded share of the live mesh there
    // for resolved geometry/normals, then ramp to full live-surface coverage
    // from the real solver foam and speed channels. This is presentation-only:
    // it neither modifies nor resamples the hydraulic grid or its wet/dry mask.
    // A normalized speed channel is non-zero even in ordinary downstream
    // current. Feeding it directly into opacity made the full moving window
    // an olive translucent sheet and hid the reflected Single Layer Water
    // underneath. Gate speed below approximately 2.2 m/s, while retaining
    // immediate coverage from real solver foam and full coverage through
    // genuinely fast water.
    UMaterialExpressionSaturate* SpeedCoverage =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    SpeedCoverage->Input.Expression = Mul(
        AddNode(
            SpeedMask,
            Scalar(TEXT("HydraulicCoverageSpeedThresholdBias"), -0.28f)),
        Scalar(TEXT("HydraulicCoverageSpeedGain"), 2.2f));
    UMaterialExpressionSaturate* HydraulicActivity =
        Cast<UMaterialExpressionSaturate>(Add(NewObject<UMaterialExpressionSaturate>(Material)));
    HydraulicActivity->Input.Expression = AddNode(
        Mul(FoamMask, Scalar(TEXT("HydraulicCoverageFoamGain"), 0.95f)),
        SpeedCoverage);
    UMaterialExpressionLinearInterpolate* HydraulicCoverage = Lerp(
        Scalar(TEXT("CalmLiveSurfaceCoverage"), 0.0f),
        Scalar(TEXT("ActiveLiveSurfaceCoverage"), 0.03f),
        HydraulicActivity);
    UMaterialExpressionMultiply* HydraulicSurfaceCoverage = Mul(
        StationEdgeCoverage, HydraulicCoverage);
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
        HydraulicSurfaceCoverage, WetCoverage);
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

// One draw-call face material: RGB vertex colour carries deterministic skin,
// sclera, iris, brow, and lip colour while vertex alpha separates soft skin
// from the harder facial details for subsurface and roughness response.
static UMaterial* BuildCrewFaceMaterial()
{
    static const TCHAR* PackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_Face");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Face.M_RaftSim_Face");
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
            Package, TEXT("M_RaftSim_Face"), RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;
    Material->SetShadingModel(MSM_PreintegratedSkin);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value)
    {
        UMaterialExpressionConstant* Expression = NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        Add(Expression);
        return Expression;
    };
    auto Constant3 = [&](const FLinearColor& Value)
    {
        UMaterialExpressionConstant3Vector* Expression =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        Expression->Constant = Value;
        Add(Expression);
        return Expression;
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Expression = NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B, UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        Add(Expression);
        return Expression;
    };

    UMaterialExpressionVertexColor* VertexColor =
        Cast<UMaterialExpressionVertexColor>(Add(NewObject<UMaterialExpressionVertexColor>(Material)));
    UMaterialExpressionComponentMask* SkinMask =
        Cast<UMaterialExpressionComponentMask>(Add(NewObject<UMaterialExpressionComponentMask>(Material)));
    SkinMask->Input.Expression = VertexColor;
    // VertexColor output 0 is RGB in UE 5.8; alpha is the dedicated output 4.
    // Reading A from output 0 previews in the editor but fails Metal cooking.
    SkinMask->Input.OutputIndex = 4;
    SkinMask->R = true;
    SkinMask->G = false;
    SkinMask->B = false;
    SkinMask->A = false;

    UMaterialExpressionNoise* PoreNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    PoreNoise->Scale = 0.045f;
    PoreNoise->Levels = 3;
    PoreNoise->bTurbulence = true;
    PoreNoise->OutputMin = 0.0f;
    PoreNoise->OutputMax = 1.0f;
    UMaterialExpressionMultiply* DarkSkin = Multiply(
        VertexColor, Constant3(FLinearColor(0.88f, 0.84f, 0.80f, 1.0f)));
    UMaterialExpressionMultiply* LightSkin = Multiply(
        VertexColor, Constant3(FLinearColor(1.04f, 1.00f, 0.96f, 1.0f)));
    UMaterialExpression* SkinVariation = Lerp(DarkSkin, LightSkin, PoreNoise);

    UTexture2D* SkinAlbedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailAlbedo."
             "T_RaftSim_CrewSkin_MicrodetailAlbedo"));
    UTexture2D* SkinNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailNormal."
             "T_RaftSim_CrewSkin_MicrodetailNormal"));
    UMaterialExpressionTextureCoordinate* SkinUv = nullptr;
    if (SkinAlbedo || SkinNormal)
    {
        SkinUv = Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        SkinUv->UTiling = 1.4f;
        SkinUv->VTiling = 1.8f;
    }
    if (SkinAlbedo && SkinUv)
    {
        UMaterialExpressionTextureSampleParameter2D* SkinAlbedoSample =
            Cast<UMaterialExpressionTextureSampleParameter2D>(
                Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        SkinAlbedoSample->ParameterName = TEXT("SkinMicroAlbedo");
        SkinAlbedoSample->Texture = SkinAlbedo;
        SkinAlbedoSample->SamplerType = SAMPLERTYPE_Color;
        SkinAlbedoSample->Coordinates.Expression = SkinUv;
        SkinAlbedoSample->Group = TEXT("RaftSimCrewFace");
        UMaterialExpressionLinearInterpolate* TexturedVariation =
            Lerp(DarkSkin, LightSkin, SkinAlbedoSample);
        // Use the source texture's red channel as a neutral variation mask;
        // deterministic vertex colour remains the four-tone skin authority.
        TexturedVariation->Alpha.OutputIndex = 1;
        SkinVariation = TexturedVariation;
    }
    // Hard facial details keep their authored sclera/iris/brow/lip colours;
    // texture variation is restricted to vertices whose alpha marks skin.
    UMaterialExpressionLinearInterpolate* VariedBase =
        Lerp(VertexColor, SkinVariation, SkinMask);

    UMaterialExpressionLinearInterpolate* SkinRoughness = Lerp(
        Constant(0.43f), Constant(0.57f), PoreNoise);
    UMaterialExpressionLinearInterpolate* Roughness = Lerp(
        Constant(0.28f), SkinRoughness, SkinMask);
    UMaterialExpressionLinearInterpolate* Specular = Lerp(
        Constant(0.48f), Constant(0.34f), SkinMask);
    UMaterialExpressionMultiply* ScatterColor = Multiply(
        VertexColor, Constant3(FLinearColor(0.68f, 0.30f, 0.20f, 1.0f)));
    UMaterialExpressionMultiply* MaskedScatter = Multiply(ScatterColor, SkinMask);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, VariedBase);
    EditorData->Roughness.Connect(0, Roughness);
    EditorData->Specular.Connect(0, Specular);
    EditorData->SubsurfaceColor.Connect(0, MaskedScatter);
    if (SkinNormal && SkinUv)
    {
        UMaterialExpressionTextureSampleParameter2D* SkinNormalSample =
            Cast<UMaterialExpressionTextureSampleParameter2D>(
                Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
        SkinNormalSample->ParameterName = TEXT("SkinMicroNormal");
        SkinNormalSample->Texture = SkinNormal;
        SkinNormalSample->SamplerType = SAMPLERTYPE_Normal;
        SkinNormalSample->Coordinates.Expression = SkinUv;
        SkinNormalSample->Group = TEXT("RaftSimCrewFace");
        UMaterialExpression* NormalAmount = Multiply(SkinMask, Constant(0.42f));
        UMaterialExpression* FinalNormal = Lerp(
            Constant3(FLinearColor(0.0f, 0.0f, 1.0f, 1.0f)),
            SkinNormalSample,
            NormalAmount);
        EditorData->Normal.Connect(0, FinalNormal);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: M_RaftSim_Face saved=%d"), bSaved ? 1 : 0);
    return Material;
}

// Preserve the rights-tracked MakeHuman atlases and skeletal material slots,
// but give the imported production bodies a physically differentiated skin
// response. The original importer authored only Base Color plus one constant
// roughness value, which flattened the facial and hand detail already present
// in the 2K public-domain atlases. This focused builder touches only the five
// skin material packages; body geometry, rigging, pose and gameplay authority
// remain unchanged.
static UMaterial* BuildProductionCC0SkinMaterial(
    const TCHAR* AssetName,
    const TCHAR* AtlasAssetName,
    const FLinearColor& AtlasReflectanceCalibration)
{
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/%s"), AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, *ObjectPath));
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

    const FString AtlasObjectPath = FString::Printf(
        TEXT("/Game/RaftSim/Characters/Production/CC0/Textures/%s.%s"),
        AtlasAssetName,
        AtlasAssetName);
    UTexture2D* Atlas = LoadObject<UTexture2D>(nullptr, *AtlasObjectPath);
    UTexture2D* MicroAlbedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailAlbedo."
             "T_RaftSim_CrewSkin_MicrodetailAlbedo"));
    UTexture2D* MicroNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailNormal."
             "T_RaftSim_CrewSkin_MicrodetailNormal"));
    if (!Atlas || !MicroAlbedo || !MicroNormal)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("RaftSim: missing production CC0 skin inputs for %s (%s)"),
            AssetName,
            *AtlasObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;
    // The source atlases span materially different photographed exposure and
    // white-balance brackets. Broad Subsurface shading amplified those
    // differences: the three light atlases clipped toward white under the
    // fixed roster rig while DarkFemale shifted orange. Preintegrated Skin
    // keeps the lightweight fallback suitable for skeletal rendering and lets
    // the atlas-specific reflectance calibration below remain authoritative.
    Material->SetShadingModel(MSM_PreintegratedSkin);
    Material->SetMaterialUsage(MATUSAGE_SkeletalMesh);

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value)
    {
        UMaterialExpressionConstant* Expression =
            NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        Add(Expression);
        return Expression;
    };
    auto Constant3 = [&](const FLinearColor& Value)
    {
        UMaterialExpressionConstant3Vector* Expression =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        Expression->Constant = Value;
        Add(Expression);
        return Expression;
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B, UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        Add(Expression);
        return Expression;
    };

    UMaterialExpressionTextureSampleParameter2D* AtlasSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    AtlasSample->ParameterName = TEXT("LicensedSkinAtlas");
    AtlasSample->Texture = Atlas;
    AtlasSample->SamplerType = SAMPLERTYPE_Color;
    AtlasSample->Group = TEXT("RaftSimCC0Skin");

    UMaterialExpressionConstant3Vector* ReflectanceCalibration =
        Cast<UMaterialExpressionConstant3Vector>(
            Constant3(AtlasReflectanceCalibration));
    ReflectanceCalibration->Desc = TEXT("AtlasReflectanceCalibration");
    UMaterialExpressionMultiply* CalibratedAtlas =
        Cast<UMaterialExpressionMultiply>(Multiply(
            AtlasSample,
            ReflectanceCalibration));

    UMaterialExpressionTextureCoordinate* MicroUv =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    MicroUv->UTiling = 36.0f;
    MicroUv->VTiling = 36.0f;

    UMaterialExpressionTextureSampleParameter2D* MicroAlbedoSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    MicroAlbedoSample->ParameterName = TEXT("SkinMicroAlbedo");
    MicroAlbedoSample->Texture = MicroAlbedo;
    MicroAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    MicroAlbedoSample->Coordinates.Expression = MicroUv;
    MicroAlbedoSample->Group = TEXT("RaftSimCC0Skin");

    UMaterialExpressionMultiply* MicroGain =
        Cast<UMaterialExpressionMultiply>(Multiply(MicroAlbedoSample, Constant(2.0f)));
    UMaterialExpressionClamp* BoundedMicroGain =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    BoundedMicroGain->Input.Expression = MicroGain;
    BoundedMicroGain->MinDefault = 0.95f;
    BoundedMicroGain->MaxDefault = 1.05f;
    UMaterialExpressionMultiply* DetailedBase =
        Cast<UMaterialExpressionMultiply>(Multiply(CalibratedAtlas, BoundedMicroGain));

    UMaterialExpressionComponentMask* MicroMask =
        Cast<UMaterialExpressionComponentMask>(
            Add(NewObject<UMaterialExpressionComponentMask>(Material)));
    MicroMask->Input.Expression = MicroAlbedoSample;
    MicroMask->R = true;
    UMaterialExpressionLinearInterpolate* Roughness =
        Cast<UMaterialExpressionLinearInterpolate>(
            Lerp(Constant(0.46f), Constant(0.58f), MicroMask));

    UMaterialExpressionTextureSampleParameter2D* MicroNormalSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    MicroNormalSample->ParameterName = TEXT("SkinMicroNormal");
    MicroNormalSample->Texture = MicroNormal;
    MicroNormalSample->SamplerType = SAMPLERTYPE_Normal;
    MicroNormalSample->Coordinates.Expression = MicroUv;
    MicroNormalSample->Group = TEXT("RaftSimCC0Skin");
    UMaterialExpressionLinearInterpolate* DetailedNormal =
        Cast<UMaterialExpressionLinearInterpolate>(Lerp(
            Constant3(FLinearColor(0.0f, 0.0f, 1.0f, 1.0f)),
            MicroNormalSample,
            Constant(0.16f)));

    UMaterialExpressionMultiply* ScatterColor =
        Cast<UMaterialExpressionMultiply>(Multiply(
            CalibratedAtlas,
            Constant3(FLinearColor(0.18f, 0.13f, 0.11f, 1.0f))));
    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, DetailedBase);
    EditorData->Roughness.Connect(0, Roughness);
    EditorData->Specular.Connect(0, Constant(0.32f));
    EditorData->SubsurfaceColor.Connect(0, ScatterColor);
    // Opaque skin shading reuses Opacity as the preintegrated scattering
    // width. Keep it near one so the atlas colour remains authoritative and
    // the earlier orange transmission regression cannot dominate hands.
    EditorData->Opacity.Connect(0, Constant(0.94f));
    EditorData->Normal.Connect(0, DetailedNormal);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim: production CC0 skin %s saved=%d"),
        AssetName,
        bSaved ? 1 : 0);
    return Material;
}

static UMaterial* BuildProductionCC0EyeMaterial()
{
    const TCHAR* AssetName = TEXT("M_RaftSim_CC0_Eyes");
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/%s"), AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, *ObjectPath));
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    UTexture2D* EyeAtlas = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Production/CC0/Textures/"
             "T_RaftSim_CC0_BrownEye.T_RaftSim_CC0_BrownEye"));
    if (!Material || !EyeAtlas)
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim: missing production CC0 eye inputs"));
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    // The source-level FBX attachment gate now preserves the reviewed outward
    // winding and coherent inverse-bind matrices. Keep the ocular surface
    // one-sided so backfaces cannot mask a future geometry regression.
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;
    // The joined FBX eye surfaces already retain open-lid geometry and the
    // hash-locked MakeHuman iris/sclera UVs. Clear Coat represents the smooth
    // tear-film/cornea layer without changing the source atlas or adding a
    // detached procedural eyeball.
    Material->SetShadingModel(MSM_ClearCoat);
    Material->SetMaterialUsage(MATUSAGE_SkeletalMesh);

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value)
    {
        UMaterialExpressionConstant* Expression =
            NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        Add(Expression);
        return Expression;
    };

    UMaterialExpressionTextureSampleParameter2D* AtlasSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    AtlasSample->ParameterName = TEXT("LicensedEyeAtlas");
    AtlasSample->Texture = EyeAtlas;
    AtlasSample->SamplerType = SAMPLERTYPE_Color;
    AtlasSample->Group = TEXT("RaftSimCC0Eyes");

    UMaterialExpressionMultiply* CalibratedAtlas =
        Cast<UMaterialExpressionMultiply>(
            Add(NewObject<UMaterialExpressionMultiply>(Material)));
    CalibratedAtlas->A.Expression = AtlasSample;
    CalibratedAtlas->B.Expression = Constant(0.82f);
    CalibratedAtlas->Desc = TEXT("SourceEyeAtlasReflectanceCalibration");

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, CalibratedAtlas);
    EditorData->Roughness.Connect(0, Constant(0.24f));
    EditorData->Specular.Connect(0, Constant(0.50f));
    EditorData->ClearCoat.Connect(0, Constant(1.0f));
    EditorData->ClearCoatRoughness.Connect(0, Constant(0.04f));
    EditorData->AmbientOcclusion.Connect(0, Constant(0.86f));

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim: production CC0 eye material saved=%d"),
        bSaved ? 1 : 0);
    return Material;
}

static void BuildProductionCC0SkinMaterials()
{
    struct FSkinSpec
    {
        const TCHAR* AssetName;
        const TCHAR* AtlasAssetName;
        FLinearColor AtlasReflectanceCalibration;
    };
    static const FSkinSpec SkinSpecs[] = {
        // These bounded linear-space gains normalize the five hash-locked
        // photographic atlases into one renderer bracket. They do not change
        // identity, hue family, texture pixels, or source provenance.
        {TEXT("M_RaftSim_CC0_Guide_Skin"), TEXT("T_RaftSim_CC0_LightMale"),
         FLinearColor(0.36f, 0.36f, 0.36f, 1.0f)},
        {TEXT("M_RaftSim_CC0_Crew01_Skin"), TEXT("T_RaftSim_CC0_DarkMale"),
         FLinearColor(0.72f, 0.72f, 0.72f, 1.0f)},
        {TEXT("M_RaftSim_CC0_Crew02_Skin"), TEXT("T_RaftSim_CC0_AsianMale"),
         FLinearColor(0.48f, 0.48f, 0.48f, 1.0f)},
        {TEXT("M_RaftSim_CC0_Crew03_Skin"), TEXT("T_RaftSim_CC0_LightFemale"),
         FLinearColor(0.42f, 0.42f, 0.42f, 1.0f)},
        {TEXT("M_RaftSim_CC0_Crew04_Skin"), TEXT("T_RaftSim_CC0_DarkFemale"),
         FLinearColor(0.72f, 0.72f, 0.72f, 1.0f)},
    };
    for (const FSkinSpec& SkinSpec : SkinSpecs)
    {
        BuildProductionCC0SkinMaterial(
            SkinSpec.AssetName,
            SkinSpec.AtlasAssetName,
            SkinSpec.AtlasReflectanceCalibration);
    }
    BuildProductionCC0EyeMaterial();
}

// Project-owned scan-derived textile response shared by current procedural
// geometry and future replacement meshes. The neutral maps preserve runtime
// tinting while adding physically scaled weave, micro-normal, AO and roughness.
static UMaterial* BuildTexturedRaftMaterial(
    const TCHAR* AssetName,
    const TCHAR* TextileName,
    const FLinearColor& Color,
    float Roughness,
    float RoughnessVariation,
    float TextureTiling,
    float TextileNormalStrength,
    bool bTwoSided,
    bool bSkeletalMesh = false,
    float SaturatedRoughnessScale = 0.34f,
    float SaturatedRoughnessMax = 0.32f,
    bool bUseTextileAlbedo = true,
    bool bUseAmbientOcclusion = true,
    bool bUseClothShading = false,
    float DrySpecularValue = 0.28f,
    float WetSpecularValue = 0.56f,
    bool bUseDynamicPaddleGloveZones = false)
{
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Materials/%s"), AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, *ObjectPath));
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
    Material->SetShadingModel(bUseClothShading ? MSM_Cloth : MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = bTwoSided;
    Material->bTangentSpaceNormal = true;
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    // UProceduralMeshComponent renders through the local/static mesh vertex
    // factory in UE 5.8. Freshly regenerated raft packages otherwise fall
    // back to the white default material even though older cached packages
    // happened to retain the required permutation.
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);
    Material->SetMaterialUsage(MATUSAGE_Nanite);
    if (bSkeletalMesh)
    {
        Material->SetMaterialUsage(MATUSAGE_SkeletalMesh);
    }

    const FString TextureRoot = FString::Printf(
        TEXT("/Game/RaftSim/Equipment/Textures/T_RaftSim_%s"), TextileName);
    // Use the stable helper naming contract authored above.
    const FString AlbedoObjectPath = FString::Printf(
        TEXT("%s_Albedo.T_RaftSim_%s_Albedo"), *TextureRoot, TextileName);
    const FString NormalObjectPath = FString::Printf(
        TEXT("%s_Normal.T_RaftSim_%s_Normal"), *TextureRoot, TextileName);
    const FString PackedObjectPath = FString::Printf(
        TEXT("%s_AORoughnessHeight.T_RaftSim_%s_AORoughnessHeight"),
        *TextureRoot, TextileName);
    UTexture2D* AlbedoTexture = LoadObject<UTexture2D>(nullptr, *AlbedoObjectPath);
    UTexture2D* NormalTexture = LoadObject<UTexture2D>(nullptr, *NormalObjectPath);
    UTexture2D* PackedTexture = LoadObject<UTexture2D>(nullptr, *PackedObjectPath);
    if (!AlbedoTexture || !NormalTexture || !PackedTexture)
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim: missing generated textile maps for %s (%s, %s, %s)"),
            TextileName, *AlbedoObjectPath, *NormalObjectPath, *PackedObjectPath);
        return nullptr;
    }

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionConstant3Vector* Base =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    Base->Constant = Color;
    Add(Base);

    UMaterialExpressionTextureCoordinate* TextureUv =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    Add(TextureUv);
    UMaterialExpressionScalarParameter* Tiling =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    Tiling->ParameterName = TEXT("TextileTiling");
    Tiling->DefaultValue = TextureTiling;
    Tiling->Group = TEXT("RaftSimEquipmentTextile");
    Add(Tiling);
    UMaterialExpressionMultiply* ScaledUv = NewObject<UMaterialExpressionMultiply>(Material);
    ScaledUv->A.Expression = TextureUv;
    ScaledUv->B.Expression = Tiling;
    Add(ScaledUv);

    UMaterialExpressionTextureSampleParameter2D* AlbedoSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    AlbedoSample->ParameterName = TEXT("TextileAlbedo");
    AlbedoSample->Texture = AlbedoTexture;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    AlbedoSample->Coordinates.Expression = ScaledUv;
    AlbedoSample->Group = TEXT("RaftSimEquipmentTextile");
    Add(AlbedoSample);
    UMaterialExpressionConstant* AlbedoGain = NewObject<UMaterialExpressionConstant>(Material);
    AlbedoGain->R = 1.47f;
    Add(AlbedoGain);
    UMaterialExpressionMultiply* NeutralAlbedo = NewObject<UMaterialExpressionMultiply>(Material);
    NeutralAlbedo->A.Expression = AlbedoSample;
    NeutralAlbedo->B.Expression = AlbedoGain;
    Add(NeutralAlbedo);
    UMaterialExpressionMultiply* TexturedColor = NewObject<UMaterialExpressionMultiply>(Material);
    TexturedColor->A.Expression = Base;
    TexturedColor->B.Expression = NeutralAlbedo;
    Add(TexturedColor);

    // Runtime water contact drives this parameter on the production raft.
    // Wet coated fabric darkens through absorption and loses broad dry diffuse
    // response while retaining its authored textile microdetail.
    UMaterialExpressionScalarParameter* Wetness =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    Wetness->ParameterName = TEXT("Wetness");
    Wetness->DefaultValue = 0.0f;
    Wetness->Group = TEXT("RaftSimRuntime");
    Add(Wetness);
    UMaterialExpressionConstant3Vector* WetTint =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    WetTint->Constant = FLinearColor(0.56f, 0.63f, 0.70f, 1.0f);
    Add(WetTint);
    UMaterialExpressionMultiply* WetTexturedColor =
        NewObject<UMaterialExpressionMultiply>(Material);
    UMaterialExpression* DryColor = bUseTextileAlbedo
        ? static_cast<UMaterialExpression*>(TexturedColor)
        : static_cast<UMaterialExpression*>(Base);
    WetTexturedColor->A.Expression = DryColor;
    WetTexturedColor->B.Expression = WetTint;
    Add(WetTexturedColor);
    UMaterialExpressionLinearInterpolate* RuntimeWetColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RuntimeWetColor->A.Expression = DryColor;
    RuntimeWetColor->B.Expression = WetTexturedColor;
    RuntimeWetColor->Alpha.Expression = Wetness;
    Add(RuntimeWetColor);

    UMaterialExpressionTextureSampleParameter2D* PackedSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    PackedSample->ParameterName = TEXT("TextileAORoughnessHeight");
    PackedSample->Texture = PackedTexture;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;
    PackedSample->Coordinates.Expression = ScaledUv;
    PackedSample->Group = TEXT("RaftSimEquipmentTextile");
    Add(PackedSample);
    UMaterialExpressionComponentMask* AoMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    AoMask->Input.Expression = PackedSample;
    AoMask->R = true;
    Add(AoMask);
    UMaterialExpressionComponentMask* RoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    RoughnessMask->Input.Expression = PackedSample;
    RoughnessMask->G = true;
    Add(RoughnessMask);

    UMaterialExpressionConstant* DryRough = NewObject<UMaterialExpressionConstant>(Material);
    DryRough->R = FMath::Clamp(Roughness + RoughnessVariation, 0.0f, 1.0f);
    Add(DryRough);
    UMaterialExpressionConstant* WetRough = NewObject<UMaterialExpressionConstant>(Material);
    WetRough->R = FMath::Clamp(Roughness - RoughnessVariation, 0.0f, 1.0f);
    Add(WetRough);
    UMaterialExpressionLinearInterpolate* VariedRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    VariedRoughness->A.Expression = DryRough;
    VariedRoughness->B.Expression = WetRough;
    VariedRoughness->Alpha.Expression = RoughnessMask;
    Add(VariedRoughness);
    UMaterialExpressionConstant* SaturatedRoughness =
        NewObject<UMaterialExpressionConstant>(Material);
    SaturatedRoughness->R = FMath::Clamp(
        Roughness * SaturatedRoughnessScale, 0.08f, SaturatedRoughnessMax);
    Add(SaturatedRoughness);
    UMaterialExpressionLinearInterpolate* RuntimeWetRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RuntimeWetRoughness->A.Expression = RoughnessVariation > UE_SMALL_NUMBER
        ? static_cast<UMaterialExpression*>(VariedRoughness)
        : static_cast<UMaterialExpression*>(DryRough);
    RuntimeWetRoughness->B.Expression = SaturatedRoughness;
    RuntimeWetRoughness->Alpha.Expression = Wetness;
    Add(RuntimeWetRoughness);
    UMaterialExpressionConstant* DrySpecular = NewObject<UMaterialExpressionConstant>(Material);
    DrySpecular->R = FMath::Clamp(DrySpecularValue, 0.0f, 1.0f);
    Add(DrySpecular);
    UMaterialExpressionConstant* WetSpecular = NewObject<UMaterialExpressionConstant>(Material);
    WetSpecular->R = FMath::Clamp(WetSpecularValue, 0.0f, 1.0f);
    Add(WetSpecular);
    UMaterialExpressionLinearInterpolate* RuntimeWetSpecular =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RuntimeWetSpecular->A.Expression = DrySpecular;
    RuntimeWetSpecular->B.Expression = WetSpecular;
    RuntimeWetSpecular->Alpha.Expression = Wetness;
    Add(RuntimeWetSpecular);

    UMaterialExpression* PresentationBaseColor = RuntimeWetColor;
    UMaterialExpression* PresentationRoughness = RuntimeWetRoughness;
    UMaterialExpression* PresentationSpecular = RuntimeWetSpecular;
    if (bUseDynamicPaddleGloveZones)
    {
        // The optimized MetaHuman rafting body is deliberately one material
        // section, so assigning a second hand slot would require destructive
        // mesh reauthoring. Two pose-driven world-space zones instead isolate
        // the existing skinned hand topology as fitted charcoal neoprene
        // gloves. A feathered wrist transition avoids a spherical cutoff and
        // follows every live stroke because gameplay updates both centres
        // from the solved middle-metacarpal bones.
        UMaterialExpressionWorldPosition* WorldPosition =
            NewObject<UMaterialExpressionWorldPosition>(Material);
        Add(WorldPosition);
        UMaterialExpressionScalarParameter* GloveRadius =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        GloveRadius->ParameterName = TEXT("PaddleGloveRadiusCm");
        GloveRadius->DefaultValue = 8.75f;
        GloveRadius->Group = TEXT("RaftSimPaddleGloves");
        Add(GloveRadius);
        UMaterialExpressionScalarParameter* GloveFeather =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        GloveFeather->ParameterName = TEXT("PaddleGloveFeatherCm");
        GloveFeather->DefaultValue = 1.25f;
        GloveFeather->Group = TEXT("RaftSimPaddleGloves");
        Add(GloveFeather);

        const auto BuildGloveMask = [&](const TCHAR* ParameterName)
            -> UMaterialExpressionSaturate*
        {
            UMaterialExpressionVectorParameter* Center =
                NewObject<UMaterialExpressionVectorParameter>(Material);
            Center->ParameterName = ParameterName;
            Center->DefaultValue = FLinearColor(1.0e7f, 1.0e7f, 1.0e7f, 1.0f);
            Center->Group = TEXT("RaftSimPaddleGloves");
            Add(Center);
            UMaterialExpressionComponentMask* CenterXyz =
                NewObject<UMaterialExpressionComponentMask>(Material);
            CenterXyz->Input.Expression = Center;
            CenterXyz->R = true;
            CenterXyz->G = true;
            CenterXyz->B = true;
            Add(CenterXyz);
            UMaterialExpressionDistance* Distance =
                NewObject<UMaterialExpressionDistance>(Material);
            Distance->A.Expression = WorldPosition;
            Distance->B.Expression = CenterXyz;
            Add(Distance);
            UMaterialExpressionSubtract* InsideDistance =
                NewObject<UMaterialExpressionSubtract>(Material);
            InsideDistance->A.Expression = GloveRadius;
            InsideDistance->B.Expression = Distance;
            Add(InsideDistance);
            UMaterialExpressionDivide* FeatheredDistance =
                NewObject<UMaterialExpressionDivide>(Material);
            FeatheredDistance->A.Expression = InsideDistance;
            FeatheredDistance->B.Expression = GloveFeather;
            Add(FeatheredDistance);
            UMaterialExpressionSaturate* Mask =
                NewObject<UMaterialExpressionSaturate>(Material);
            Mask->Input.Expression = FeatheredDistance;
            Add(Mask);
            return Mask;
        };
        UMaterialExpressionSaturate* LeftGloveMask =
            BuildGloveMask(TEXT("LeftPaddleGloveCenterWS"));
        UMaterialExpressionSaturate* RightGloveMask =
            BuildGloveMask(TEXT("RightPaddleGloveCenterWS"));
        UMaterialExpressionAdd* CombinedGloveMasks =
            NewObject<UMaterialExpressionAdd>(Material);
        CombinedGloveMasks->A.Expression = LeftGloveMask;
        CombinedGloveMasks->B.Expression = RightGloveMask;
        Add(CombinedGloveMasks);
        UMaterialExpressionSaturate* GloveMask =
            NewObject<UMaterialExpressionSaturate>(Material);
        GloveMask->Input.Expression = CombinedGloveMasks;
        Add(GloveMask);

        UMaterialExpressionConstant3Vector* DryGloveColor =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        DryGloveColor->Constant = FLinearColor(0.022f, 0.029f, 0.038f, 1.0f);
        Add(DryGloveColor);
        UMaterialExpressionConstant3Vector* WetGloveTint =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        WetGloveTint->Constant = FLinearColor(0.62f, 0.68f, 0.74f, 1.0f);
        Add(WetGloveTint);
        UMaterialExpressionMultiply* WetGloveColor =
            NewObject<UMaterialExpressionMultiply>(Material);
        WetGloveColor->A.Expression = DryGloveColor;
        WetGloveColor->B.Expression = WetGloveTint;
        Add(WetGloveColor);
        UMaterialExpressionLinearInterpolate* RuntimeGloveColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        RuntimeGloveColor->A.Expression = DryGloveColor;
        RuntimeGloveColor->B.Expression = WetGloveColor;
        RuntimeGloveColor->Alpha.Expression = Wetness;
        Add(RuntimeGloveColor);
        UMaterialExpressionLinearInterpolate* GloveBaseColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        GloveBaseColor->A.Expression = RuntimeWetColor;
        GloveBaseColor->B.Expression = RuntimeGloveColor;
        GloveBaseColor->Alpha.Expression = GloveMask;
        Add(GloveBaseColor);

        UMaterialExpressionConstant* DryGloveRoughness =
            NewObject<UMaterialExpressionConstant>(Material);
        DryGloveRoughness->R = 0.66f;
        Add(DryGloveRoughness);
        UMaterialExpressionConstant* WetGloveRoughness =
            NewObject<UMaterialExpressionConstant>(Material);
        WetGloveRoughness->R = 0.36f;
        Add(WetGloveRoughness);
        UMaterialExpressionLinearInterpolate* RuntimeGloveRoughness =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        RuntimeGloveRoughness->A.Expression = DryGloveRoughness;
        RuntimeGloveRoughness->B.Expression = WetGloveRoughness;
        RuntimeGloveRoughness->Alpha.Expression = Wetness;
        Add(RuntimeGloveRoughness);
        UMaterialExpressionLinearInterpolate* GloveRoughness =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        GloveRoughness->A.Expression = RuntimeWetRoughness;
        GloveRoughness->B.Expression = RuntimeGloveRoughness;
        GloveRoughness->Alpha.Expression = GloveMask;
        Add(GloveRoughness);

        UMaterialExpressionConstant* DryGloveSpecular =
            NewObject<UMaterialExpressionConstant>(Material);
        DryGloveSpecular->R = 0.30f;
        Add(DryGloveSpecular);
        UMaterialExpressionConstant* WetGloveSpecular =
            NewObject<UMaterialExpressionConstant>(Material);
        WetGloveSpecular->R = 0.48f;
        Add(WetGloveSpecular);
        UMaterialExpressionLinearInterpolate* RuntimeGloveSpecular =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        RuntimeGloveSpecular->A.Expression = DryGloveSpecular;
        RuntimeGloveSpecular->B.Expression = WetGloveSpecular;
        RuntimeGloveSpecular->Alpha.Expression = Wetness;
        Add(RuntimeGloveSpecular);
        UMaterialExpressionLinearInterpolate* GloveSpecular =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        GloveSpecular->A.Expression = RuntimeWetSpecular;
        GloveSpecular->B.Expression = RuntimeGloveSpecular;
        GloveSpecular->Alpha.Expression = GloveMask;
        Add(GloveSpecular);

        PresentationBaseColor = GloveBaseColor;
        PresentationRoughness = GloveRoughness;
        PresentationSpecular = GloveSpecular;
    }

    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    NormalSample->ParameterName = TEXT("TextileNormal");
    NormalSample->Texture = NormalTexture;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = ScaledUv;
    NormalSample->Group = TEXT("RaftSimEquipmentTextile");
    Add(NormalSample);
    UMaterialExpressionConstant3Vector* FlatNormal =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 1.0f);
    Add(FlatNormal);
    UMaterialExpressionScalarParameter* NormalStrength =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    NormalStrength->ParameterName = TEXT("TextileNormalStrength");
    NormalStrength->DefaultValue = TextileNormalStrength;
    NormalStrength->Group = TEXT("RaftSimEquipmentTextile");
    Add(NormalStrength);
    UMaterialExpressionLinearInterpolate* BlendedNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    BlendedNormal->A.Expression = FlatNormal;
    BlendedNormal->B.Expression = NormalSample;
    BlendedNormal->Alpha.Expression = NormalStrength;
    Add(BlendedNormal);

    UMaterialExpressionConstant* Metallic = NewObject<UMaterialExpressionConstant>(Material);
    Metallic->R = 0.0f;
    Add(Metallic);
    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, PresentationBaseColor);
    EditorData->Roughness.Connect(0, PresentationRoughness);
    EditorData->Specular.Connect(0, PresentationSpecular);
    EditorData->Metallic.Connect(0, Metallic);
    // Emptying the expression collection does not clear serialized material
    // property inputs on an existing asset. Disconnect the prior normal graph
    // before conditionally wiring the replacement; otherwise a zero-strength
    // rebuild retains an orphaned scan-normal input and renders identically to
    // the old material.
    EditorData->Normal.Expression = nullptr;
    EditorData->Normal.OutputIndex = 0;
    // Cloth reuses the serialized Subsurface Color and Clear Coat inputs as
    // Fuzz Color and Cloth amount. Clear both inputs on every rebuild so a
    // material that changes shading model cannot retain orphaned expressions.
    EditorData->SubsurfaceColor.Expression = nullptr;
    EditorData->SubsurfaceColor.OutputIndex = 0;
    EditorData->ClearCoat.Expression = nullptr;
    EditorData->ClearCoat.OutputIndex = 0;
    if (TextileNormalStrength > UE_SMALL_NUMBER)
    {
        EditorData->Normal.Connect(0, BlendedNormal);
    }
    if (bUseClothShading)
    {
        // A restrained, shell-coloured grazing response separates woven nylon
        // from molded plastic without adding an emissive halo. Drenching lays
        // the short fibres down while the existing wet color, roughness and
        // specular paths retain the water-film response.
        UMaterialExpressionConstant3Vector* FuzzGain =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        FuzzGain->Constant = FLinearColor(0.36f, 0.38f, 0.41f, 1.0f);
        Add(FuzzGain);
        UMaterialExpressionMultiply* FuzzColor =
            NewObject<UMaterialExpressionMultiply>(Material);
        FuzzColor->A.Expression = RuntimeWetColor;
        FuzzColor->B.Expression = FuzzGain;
        Add(FuzzColor);
        EditorData->SubsurfaceColor.Connect(0, FuzzColor);

        UMaterialExpressionConstant* DryCloth =
            NewObject<UMaterialExpressionConstant>(Material);
        DryCloth->R = 0.42f;
        Add(DryCloth);
        UMaterialExpressionConstant* WetCloth =
            NewObject<UMaterialExpressionConstant>(Material);
        WetCloth->R = 0.16f;
        Add(WetCloth);
        UMaterialExpressionLinearInterpolate* RuntimeCloth =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        RuntimeCloth->A.Expression = DryCloth;
        RuntimeCloth->B.Expression = WetCloth;
        RuntimeCloth->Alpha.Expression = Wetness;
        Add(RuntimeCloth);
        EditorData->ClearCoat.Connect(0, RuntimeCloth);
    }
    if (bUseAmbientOcclusion)
    {
        EditorData->AmbientOcclusion.Connect(0, AoMask);
    }
    else
    {
        UMaterialExpressionConstant* NeutralAo =
            NewObject<UMaterialExpressionConstant>(Material);
        NeutralAo->R = 1.0f;
        Add(NeutralAo);
        EditorData->AmbientOcclusion.Connect(0, NeutralAo);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        *PackagePath, FPackageName::GetAssetPackageExtension());
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: textured %s saved=%d"), AssetName, bSaved ? 1 : 0);
    return Material;
}

static void BuildPfdMaterials()
{
    // The 1K source contains roughly one hundred woven checks across. One UV
    // repeat over a 30 cm cell therefore lands near a real 3 mm ripstop grid;
    // the previous four repeats produced sub-millimetre shimmer in the guide
    // camera. Keep the weave legible through roughness and a restrained normal
    // rather than high-frequency contrast.
    // The authored replacement PFD now carries a stable tangent/UV field, so
    // use the project-owned 1K ripstop maps at restrained scale. Darker safety
    // tints preserve high visibility without clipping into toy-like neon under
    // the roster and bright-water exposure ranges.
    const auto BuildPfdShellMaterial = [](const TCHAR* AssetName, const FLinearColor& Color)
    {
        return BuildTexturedRaftMaterial(
            AssetName,
            TEXT("PfdRipstop"),
            Color,
            /*Roughness=*/0.68f,
            /*RoughnessVariation=*/0.10f,
            /*TextureTiling=*/1.15f,
            /*TextileNormalStrength=*/0.22f,
            /*bTwoSided=*/false,
            /*bSkeletalMesh=*/false,
            /*SaturatedRoughnessScale=*/0.52f,
            /*SaturatedRoughnessMax=*/0.40f,
            /*bUseTextileAlbedo=*/true,
            /*bUseAmbientOcclusion=*/true,
            /*bUseClothShading=*/true,
            /*DrySpecularValue=*/0.24f,
            /*WetSpecularValue=*/0.42f);
    };
    BuildPfdShellMaterial(
        TEXT("M_RaftSim_CrewPFD"),
        FLinearColor(0.42f, 0.025f, 0.004f, 1.0f));
    BuildPfdShellMaterial(
        TEXT("M_RaftSim_PFD_Red"),
        FLinearColor(0.32f, 0.008f, 0.003f, 1.0f));
    BuildPfdShellMaterial(
        TEXT("M_RaftSim_PFD_Yellow"),
        FLinearColor(0.42f, 0.20f, 0.004f, 1.0f));
    BuildPfdShellMaterial(
        TEXT("M_RaftSim_PFD_Blue"),
        FLinearColor(0.006f, 0.065f, 0.24f, 1.0f));
}

static void BuildHelmetMaterials()
{
    // River helmets are open thin shells, unlike the closed PFD foam cells.
    // They must render from both sides at guide, chase, wrap and swimmer camera
    // angles. The earlier one-sided material disappeared into spikes/flaps in
    // the first production in-river roster capture.
    BuildSolidMaterial(
        TEXT("M_RaftSim_Helmet"),
        FLinearColor(0.035f, 0.10f, 0.20f, 1.0f),
        0.42f,
        0.0f,
        /*bTwoSided=*/true);
    BuildSolidMaterial(
        TEXT("M_RaftSim_Helmet_Red"),
        FLinearColor(0.32f, 0.015f, 0.008f, 1.0f),
        0.42f,
        0.0f,
        /*bTwoSided=*/true);
    BuildSolidMaterial(
        TEXT("M_RaftSim_Helmet_Yellow"),
        FLinearColor(0.55f, 0.25f, 0.006f, 1.0f),
        0.42f,
        0.0f,
        /*bTwoSided=*/true);
    BuildSolidMaterial(
        TEXT("M_RaftSim_Helmet_White"),
        FLinearColor(0.42f, 0.46f, 0.50f, 1.0f),
        0.42f,
        0.0f,
        /*bTwoSided=*/true);
    BuildSolidMaterial(
        TEXT("M_RaftSim_GuideHelmet"),
        FLinearColor(0.42f, 0.18f, 0.005f, 1.0f),
        0.42f,
        0.0f,
        /*bTwoSided=*/true);
}

static UMaterial* BuildProductionCrewWetsuitMaterial()
{
    return BuildTexturedRaftMaterial(
        TEXT("M_RaftSim_Wetsuit"), TEXT("WetsuitNeoprene"),
        FLinearColor(0.012f, 0.018f, 0.025f, 1.0f),
        0.76f, 0.06f, 5.0f, 0.10f,
        /*bTwoSided=*/false,
        /*bSkeletalMesh=*/true,
        /*SaturatedRoughnessScale=*/0.34f,
        /*SaturatedRoughnessMax=*/0.32f,
        /*bUseTextileAlbedo=*/true,
        /*bUseAmbientOcclusion=*/true,
        /*bUseClothShading=*/false,
        /*DrySpecularValue=*/0.28f,
        /*WetSpecularValue=*/0.56f,
        /*bUseDynamicPaddleGloveZones=*/true);
}

static UMaterial* BuildSplashJacketMaterial()
{
    // The upper-arm overlay is a thin woven splash shell, not molded foam.
    // Keep the existing project-owned ripstop source but resolve it at garment
    // scale, use Cloth grazing response, and retain a rougher wet state than
    // the earlier generic material so drenched sleeves do not become plastic.
    return BuildTexturedRaftMaterial(
        TEXT("M_RaftSim_SplashJacket"),
        TEXT("PfdRipstop"),
        FLinearColor(0.015f, 0.15f, 0.24f, 1.0f),
        /*Roughness=*/0.72f,
        /*RoughnessVariation=*/0.08f,
        /*TextureTiling=*/1.45f,
        /*TextileNormalStrength=*/0.20f,
        /*bTwoSided=*/false,
        /*bSkeletalMesh=*/false,
        /*SaturatedRoughnessScale=*/0.56f,
        /*SaturatedRoughnessMax=*/0.44f,
        /*bUseTextileAlbedo=*/true,
        /*bUseAmbientOcclusion=*/true,
        /*bUseClothShading=*/true,
        /*DrySpecularValue=*/0.20f,
        /*WetSpecularValue=*/0.38f);
}

static void BuildProductionRaftMaterials()
{
    // Water contact drives both instances close to full wetness in a rapid.
    // Coated PVC/Hypalon retains a broader micro-rough wet film than neoprene;
    // keep that response scoped to the raft instead of changing shared PFD or
    // character-material defaults.
    BuildTexturedRaftMaterial(
        TEXT("M_RaftSim_RaftTube"), TEXT("RaftCoatedFabric"),
        FLinearColor(0.075f, 0.006f, 0.002f, 1.0f),
        0.82f, 0.10f, 5.0f, 0.38f,
        /*bTwoSided=*/true, /*bSkeletalMesh=*/false,
        /*SaturatedRoughnessScale=*/0.46f,
        /*SaturatedRoughnessMax=*/0.40f);
    BuildTexturedRaftMaterial(
        TEXT("M_RaftSim_RaftFloor"), TEXT("RaftCoatedFabric"),
        FLinearColor(0.008f, 0.012f, 0.014f, 1.0f),
        0.88f, 0.08f, 8.0f, 0.28f,
        /*bTwoSided=*/true, /*bSkeletalMesh=*/false,
        /*SaturatedRoughnessScale=*/0.46f,
        /*SaturatedRoughnessMax=*/0.40f);
}

static void BuildRaftCrewMaterials()
{
    BuildCrewSkinTextureAssets();
    BuildProductionCC0SkinMaterials();
    BuildOfflineMetaHumanSkinMaterial();
    BuildEquipmentTextileTextureAssets();
    // Weathered rescue-orange commercial PVC and a muted safety-yellow grab
    // line keep the craft legible in whitewater without the emissive toy-like
    // response of the previous high-luminance palette.
    BuildProductionRaftMaterials();
    BuildSolidMaterial(
        TEXT("M_RaftSim_RaftRigging"), FLinearColor(0.18f, 0.07f, 0.003f, 1.0f),
        0.84f, 0.0f, /*bTwoSided=*/true);

    // Layered crew gear shares low-cost PBR materials. Brighter splash tops
    // separate articulated limbs from the dark neoprene lower body.
    BuildPfdMaterials();
    BuildHelmetMaterials();
    BuildSolidMaterial(TEXT("M_RaftSim_Skin"), FLinearColor(0.55f, 0.34f, 0.23f, 1.0f), 0.56f, 0.0f);
    BuildCrewFaceMaterial();
    BuildSplashJacketMaterial();
    BuildProductionCrewWetsuitMaterial();
    BuildSolidMaterial(TEXT("M_RaftSim_PFDWebbing"), FLinearColor(0.008f, 0.010f, 0.012f, 1.0f), 0.72f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_BootRubber"), FLinearColor(0.006f, 0.008f, 0.010f, 1.0f), 0.78f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_PaddleShaft"), FLinearColor(0.035f, 0.035f, 0.042f, 1.0f), 0.34f, 0.10f);
    BuildSolidMaterial(TEXT("M_RaftSim_PaddleBlade"), FLinearColor(0.30f, 0.05f, 0.002f, 1.0f), 0.58f, 0.0f);
}

static UMaterial* BuildSprayMistMaterial()
{
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material build begin"));
    static const TCHAR* PackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist.M_RaftSim_SprayMist");
    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, ObjectPath));
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material load complete"));
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, TEXT("M_RaftSim_SprayMist"),
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    Material->Modify();
    Material->GetExpressionCollection().Empty();
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material graph reset"));
    Material->BlendMode = BLEND_Translucent;
    // These cards can overlap more than one hundred times around a hard D4
    // contact. Surface-per-pixel translucency routes every layer through the
    // expensive Lumen surface-lighting path and pushed Shipping p95 over the
    // 16.67 ms frame budget. Spray, mist and aerated contact water need soft
    // volume response rather than a unique specular solve per card, so use the
    // bounded volumetric lighting path shared by production particle systems.
    Material->TranslucencyLightingMode = TLM_VolumetricNonDirectional;
    Material->TwoSided = true;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material usage set"));

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Constant = [&](float Value)
    {
        UMaterialExpressionConstant* Expression =
            NewObject<UMaterialExpressionConstant>(Material);
        Expression->R = Value;
        Add(Expression);
        return Expression;
    };
    auto Scalar = [&](const TCHAR* Name, float Value)
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimWaterVfx");
        Add(Expression);
        return Expression;
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };
    auto AddValues = [&](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Expression =
            NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Add(Expression);
        return Expression;
    };

    UMaterialExpressionVectorParameter* Color =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    Color->ParameterName = TEXT("VfxColor");
    Color->DefaultValue = FLinearColor(0.64f, 0.76f, 0.80f, 1.0f);
    Color->Group = TEXT("RaftSimWaterVfx");
    Add(Color);

    // Every runtime pool uses the inexpensive engine plane. A centered radial
    // falloff removes its rectangular silhouette, while low-level UV-space
    // turbulence perforates each card so compact puffs read as aerated spray
    // rather than translucent circles.
    UMaterialExpressionTextureCoordinate* UV =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    Add(UV);
    UMaterialExpressionConstant2Vector* CenterOffset =
        NewObject<UMaterialExpressionConstant2Vector>(Material);
    CenterOffset->R = -0.5f;
    CenterOffset->G = -0.5f;
    Add(CenterOffset);
    UMaterialExpressionAdd* CenteredUv = AddValues(UV, CenterOffset);
    UMaterialExpressionDotProduct* RadiusSquared =
        NewObject<UMaterialExpressionDotProduct>(Material);
    RadiusSquared->A.Expression = CenteredUv;
    RadiusSquared->B.Expression = CenteredUv;
    Add(RadiusSquared);
    UMaterialExpressionSaturate* RadialMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    RadialMask->Input.Expression = AddValues(
        Multiply(RadiusSquared, Constant(-4.4f)),
        Constant(1.08f));
    Add(RadialMask);

    // This material is shared by every translucent spray, droplet, mist and
    // contact-water pixel. Multi-octave procedural Noise looked organic but
    // made the full-reach Shipping workload GPU-bound. Two crossed triangular
    // UV waves preserve nonuniform breakup without texture fetches, trigonometry
    // or the expensive Noise shader path.
    UMaterialExpression* ScaledUv = Multiply(
        CenteredUv, Scalar(TEXT("VfxNoiseScale"), 6.5f));
    auto Component = [&](UMaterialExpression* Input, bool bRed, bool bGreen)
    {
        UMaterialExpressionComponentMask* Mask =
            NewObject<UMaterialExpressionComponentMask>(Material);
        Mask->Input.Expression = Input;
        Mask->R = bRed;
        Mask->G = bGreen;
        Add(Mask);
        return Mask;
    };
    auto TriangleWave = [&](UMaterialExpression* Input)
    {
        UMaterialExpressionFrac* Fraction =
            NewObject<UMaterialExpressionFrac>(Material);
        Fraction->Input.Expression = Input;
        Add(Fraction);
        UMaterialExpressionAbs* Distance =
            NewObject<UMaterialExpressionAbs>(Material);
        Distance->Input.Expression = AddValues(Fraction, Constant(-0.5f));
        Add(Distance);
        return Multiply(Distance, Constant(2.0f));
    };
    UMaterialExpression* BreakupU = Component(ScaledUv, true, false);
    UMaterialExpression* BreakupV = Component(ScaledUv, false, true);
    UMaterialExpression* WaveA = TriangleWave(AddValues(
        BreakupU, Multiply(BreakupV, Constant(0.73f))));
    UMaterialExpression* WaveB = TriangleWave(AddValues(
        Multiply(BreakupU, Constant(0.61f)),
        Multiply(BreakupV, Constant(-1.17f))));
    UMaterialExpression* BreakupPattern = Multiply(WaveA, WaveB);
    UMaterialExpressionSaturate* SprayBreakup =
        NewObject<UMaterialExpressionSaturate>(Material);
    SprayBreakup->Input.Expression = AddValues(
        Multiply(BreakupPattern, Scalar(TEXT("VfxBreakupGain"), 0.45f)),
        Scalar(TEXT("VfxBreakupFloor"), 0.55f));
    Add(SprayBreakup);
    // Square the radial mask before analytic breakup. This cheap smooth-edge
    // response removes the hard oval perimeter that made equally lit cards
    // read as a dotted necklace around the contact instead of a spray volume.
    UMaterialExpression* SoftRadialMask = Multiply(RadialMask, RadialMask);
    UMaterialExpression* BrokenRadialMask = Multiply(SoftRadialMask, SprayBreakup);
    UMaterialExpressionVertexColor* VertexColor =
        NewObject<UMaterialExpressionVertexColor>(Material);
    Add(VertexColor);
    UMaterialExpressionMultiply* VertexFeather =
        NewObject<UMaterialExpressionMultiply>(Material);
    VertexFeather->A.Expression = BrokenRadialMask;
    VertexFeather->B.Expression = VertexColor;
    VertexFeather->B.OutputIndex = 4;
    Add(VertexFeather);
    UMaterialExpression* Opacity = Multiply(
        VertexFeather,
        Scalar(TEXT("VfxOpacity"), 0.22f));
    UMaterialExpression* Emissive = Multiply(
        Color,
        Scalar(TEXT("VfxEmissive"), 0.025f));
    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, Color);
    Ed->Opacity.Connect(0, Opacity);
    Ed->Roughness.Connect(0, Scalar(TEXT("VfxRoughness"), 0.48f));
    Ed->Specular.Connect(0, Scalar(TEXT("VfxSpecular"), 0.34f));
    Ed->EmissiveColor.Connect(0, Emissive);

    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material graph authored"));
    Material->PostEditChange();
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material PostEditChange complete"));
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display, TEXT("RaftSim: water VFX material saved=%d"), bSaved ? 1 : 0);
    if (!bSaved)
    {
        return nullptr;
    }
    return Material;
}

static bool EnableReviewedEnvironmentMaterialUsages(const TCHAR* ObjectPath)
{
    UMaterial* Material = LoadObject<UMaterial>(nullptr, ObjectPath);
    if (!Material)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim: reviewed environment material missing: %s"), ObjectPath);
        return false;
    }
    Material->Modify();
    // UE 5.8's SetUsageByFlag intentionally avoids preview-shader compilation.
    // The package cooker builds the required platform permutations after these
    // persisted flags are saved, which keeps this metadata repair deterministic.
    Material->SetUsageByFlag(MATUSAGE_Nanite, true);
    Material->SetUsageByFlag(MATUSAGE_InstancedStaticMeshes, true);
    const bool bNanite = Material->GetUsageByFlag(MATUSAGE_Nanite);
    const bool bInstances = Material->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes);

    UPackage* Package = Material->GetOutermost();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Package->GetName(), FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim: promoted reviewed material %s Nanite=%d HISM=%d saved=%d"),
        ObjectPath, bNanite ? 1 : 0, bInstances ? 1 : 0, bSaved ? 1 : 0);
    return bNanite && bInstances && bSaved;
}

static void PromoteReviewedEnvironmentMaterials()
{
    for (const TCHAR* MaterialPath : {
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_Bark.M_PineTree01_Bark"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_Needles.M_PineTree01_Needles"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_NeedlesMasked.M_PineTree01_NeedlesMasked"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkA.M_PineTree01_TrunkA"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkB.M_PineTree01_TrunkB"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkC.M_PineTree01_TrunkC"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
             "M_TreeSmall02_Trunk.M_TreeSmall02_Trunk"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
             "M_TreeSmall02_Branches.M_TreeSmall02_Branches"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
             "M_TreeSmall02_Leaves.M_TreeSmall02_Leaves"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/"
             "M_RockMossSet01_ReviewLit.M_RockMossSet01_ReviewLit"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder.M_RaftSim_RiverBoulder")})
    {
        EnableReviewedEnvironmentMaterialUsages(MaterialPath);
    }
}

static void HandlePromoteReviewedEnvironmentMaterials(const TArray<FString>&)
{
    PromoteReviewedEnvironmentMaterials();
}

static void HandleCreatePhotorealMaterials(const TArray<FString>&)
{
    BuildSouthForkWaterTextureAssets();
    BuildPhotorealRiverWaterMaterial();
    BuildPhotorealTerrainMaterial();
    // The live solver mesh rides 2 cm above the authored Single Layer Water.
    // Keep this overlay non-transmitting so the two water volumes are not
    // refracted and scattered twice. Its station ends use continuous alpha;
    // moving geometry normals retain hydraulic shape.
    BuildLiveRiverSurfaceMaterial();
    BuildRaftCrewMaterials();
    // Full-reach environment infrastructure and hydraulic atmosphere.
    BuildSolidMaterial(TEXT("M_RaftSim_Asphalt"), FLinearColor(0.035f, 0.038f, 0.04f, 1.0f), 0.92f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_Timber"), FLinearColor(0.22f, 0.11f, 0.045f, 1.0f), 0.72f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_GalvanizedSteel"), FLinearColor(0.32f, 0.35f, 0.37f, 1.0f), 0.36f, 0.72f);
    BuildSolidMaterial(TEXT("M_RaftSim_WeatheredConcrete"), FLinearColor(0.29f, 0.28f, 0.25f, 1.0f), 0.86f, 0.0f);
    BuildRiverBoulderMaterial();
    BuildSprayMistMaterial();
    PromoteReviewedEnvironmentMaterials();
}

bool CreatePhotorealRiverWaterMaterial(FString& OutSummary)
{
    const bool bTextureSaved = BuildSouthForkWaterTextureAssets();
    UMaterial* Material = BuildPhotorealRiverWaterMaterial();
    const bool bSucceeded = bTextureSaved && Material != nullptr;
    OutSummary += FString::Printf(
        TEXT("South Fork photoreal river-water material authored: %s.\n"),
        bSucceeded ? TEXT("yes") : TEXT("no"));
    return bSucceeded;
}

bool CreateLiveRiverSurfaceMaterial(FString& OutSummary)
{
    UMaterial* Material = BuildLiveRiverSurfaceMaterial();
    const bool bSucceeded = Material != nullptr;
    OutSummary += FString::Printf(
        TEXT("Solver-owned live river-water surface material authored: %s.\n"),
        bSucceeded ? TEXT("yes") : TEXT("no"));
    return bSucceeded;
}

bool CreateWaterVfxMaterial(FString& OutSummary)
{
    const bool bSucceeded = BuildSprayMistMaterial() != nullptr;
    OutSummary += FString::Printf(
        TEXT("Solver-driven soft-card water VFX material authored: %s.\n"),
        bSucceeded ? TEXT("yes") : TEXT("no"));
    return bSucceeded;
}

static void HandleCreatePhotorealRiverWaterMaterial(const TArray<FString>&)
{
    FString Summary;
    CreatePhotorealRiverWaterMaterial(Summary);
    UE_LOG(LogTemp, Display, TEXT("%s"), *Summary);
}

static void HandleCreatePhotorealRiverWaterPreviewMaterial(const TArray<FString>&)
{
    // Visual experiments must never resave the reviewed production package.
    // The preview deliberately reuses the already-authored project-owned flow
    // texture and lives outside the production Materials directory.
    BuildPhotorealRiverWaterMaterial(
        TEXT("/Game/RaftSim/Experiments/M_RaftSim_PhotorealRiverWater_Preview"),
        TEXT("M_RaftSim_PhotorealRiverWater_Preview"));
}

static void HandleCreateRaftCrewMaterials(const TArray<FString>&)
{
    BuildRaftCrewMaterials();
    BuildSprayMistMaterial();
}

static void HandleCreateLiveRiverSurfaceMaterial(const TArray<FString>&)
{
    // Focused material iteration reuses the texture created by the full
    // photoreal bootstrap, avoiding unrelated texture-package resaves.
    FString Summary;
    CreateLiveRiverSurfaceMaterial(Summary);
    UE_LOG(LogTemp, Display, TEXT("%s"), *Summary);
}

static void HandleCreatePhotorealTerrainMaterial(const TArray<FString>&)
{
    BuildPhotorealTerrainMaterial();
}

static void HandleCreateCrewFaceMaterial(const TArray<FString>&)
{
    BuildCrewSkinTextureAssets();
    BuildCrewFaceMaterial();
}

static void HandleCreateProductionCrewWetsuitMaterial(const TArray<FString>&)
{
    // The focused command intentionally reuses the texture assets authored by
    // the full raft/crew bootstrap. Avoid resaving every equipment texture
    // while iterating only the skeletal wetsuit presentation.
    BuildProductionCrewWetsuitMaterial();
}

static void HandleCreateSplashJacketMaterial(const TArray<FString>&)
{
    // Focused sleeve iteration must not resave the raft, PFD, helmet, skin,
    // water-VFX, or shared textile texture packages.
    BuildSplashJacketMaterial();
}

static void HandleCreateProductionPfdMaterials(const TArray<FString>&)
{
    BuildPfdMaterials();
}

static void HandleCreateProductionHelmetMaterials(const TArray<FString>&)
{
    BuildHelmetMaterials();
    // The production static mesh also assigns the existing liner/webbing and
    // buckle hardware materials. Persist their Nanite permutations in the same
    // focused authoring command so runtime never falls back to the default shader.
    EnableReviewedEnvironmentMaterialUsages(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing"));
    EnableReviewedEnvironmentMaterialUsages(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"));
}

static void HandleCreateProductionRaftMaterials(const TArray<FString>&)
{
    // Reuse the existing generated coating textures and touch only the two
    // runtime raft material packages during renderer iteration.
    BuildProductionRaftMaterials();
}

static void HandleCreateProductionCC0SkinMaterials(const TArray<FString>&)
{
    // Reuse the existing rights-tracked variant atlases and project-owned
    // neutral microdetail maps; touch only the five production skin packages.
    BuildProductionCC0SkinMaterials();
}

static void HandleCreateOfflineMetaHumanSkinMaterial(const TArray<FString>&)
{
    // This focused command never calls Epic services. It only combines the
    // installed offline archetype with RaftSim's existing project-owned skin
    // microdetail maps.
    BuildOfflineMetaHumanSkinMaterial();
}

static void HandleCreateCroppedMetaHumanFaceMaterial(const TArray<FString>&)
{
    BuildCroppedMetaHumanFaceMaterial();
}

static void HandleCreateRiverBoulderMaterial(const TArray<FString>&)
{
    BuildRiverBoulderMaterial();
    BuildRiverBoulderMaterial(
        TEXT("M_RaftSim_ProductionRiverBoulder"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_ProductionRiverBoulder"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_ProductionRiverBoulder."
             "M_RaftSim_ProductionRiverBoulder"),
        /*bIncludeReviewedSource=*/false);
}

static void HandleCreateReviewedRiverBoulderMaterial(const TArray<FString>&)
{
    // Focused authoring path for the reviewed parent. This deliberately avoids
    // resaving the separate production fallback while a river-specific visual
    // milestone is being regenerated.
    BuildRiverBoulderMaterial();
}

static void HandleCreateWaterVfxMaterial(const TArray<FString>&)
{
    FString Summary;
    CreateWaterVfxMaterial(Summary);
    UE_LOG(LogTemp, Display, TEXT("%s"), *Summary);
}

static FAutoConsoleCommand GCreatePhotorealMaterialsCommand(
    TEXT("RaftSim.CreatePhotorealMaterials"),
    TEXT("Author the photoreal single-layer river-water material "
         "(/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater)."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreatePhotorealMaterials));

static FAutoConsoleCommand GCreatePhotorealRiverWaterMaterialCommand(
    TEXT("RaftSim.CreatePhotorealRiverWaterMaterial"),
    TEXT("Author only the source/solver-conditioned full-reach river-water material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreatePhotorealRiverWaterMaterial));

static FAutoConsoleCommand GCreatePhotorealRiverWaterPreviewMaterialCommand(
    TEXT("RaftSim.CreatePhotorealRiverWaterPreviewMaterial"),
    TEXT("Author an isolated river-water preview without resaving the reviewed package."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreatePhotorealRiverWaterPreviewMaterial));

static FAutoConsoleCommand GCreateRaftCrewMaterialsCommand(
    TEXT("RaftSim.CreateRaftCrewMaterials"),
    TEXT("Author only the project-owned production raft and crew materials."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateRaftCrewMaterials));

static FAutoConsoleCommand GCreateLiveRiverSurfaceMaterialCommand(
    TEXT("RaftSim.CreateLiveRiverSurfaceMaterial"),
    TEXT("Author only the presentation-safe live solver surface material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateLiveRiverSurfaceMaterial));

static FAutoConsoleCommand GCreatePhotorealTerrainMaterialCommand(
    TEXT("RaftSim.CreatePhotorealTerrainMaterial"),
    TEXT("Author only the source-conditioned South Fork terrain material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreatePhotorealTerrainMaterial));

static FAutoConsoleCommand GCreateCrewFaceMaterialCommand(
    TEXT("RaftSim.CreateCrewFaceMaterial"),
    TEXT("Author only the batched vertex-colour crew face material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateCrewFaceMaterial));

static FAutoConsoleCommand GCreateProductionCrewWetsuitMaterialCommand(
    TEXT("RaftSim.CreateProductionCrewWetsuitMaterial"),
    TEXT("Author the skeletal-compatible generated-neoprene production crew material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateProductionCrewWetsuitMaterial));

static FAutoConsoleCommand GCreateSplashJacketMaterialCommand(
    TEXT("RaftSim.CreateSplashJacketMaterial"),
    TEXT("Author only the folded-sleeve splash-jacket Cloth material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateSplashJacketMaterial));

static FAutoConsoleCommand GCreateProductionPfdMaterialsCommand(
    TEXT("RaftSim.CreateProductionPfdMaterials"),
    TEXT("Author the four stable high-visibility production PFD shaders."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateProductionPfdMaterials));

static FAutoConsoleCommand GCreateProductionHelmetMaterialsCommand(
    TEXT("RaftSim.CreateProductionHelmetMaterials"),
    TEXT("Author the two-sided guide and crew river-helmet shaders."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateProductionHelmetMaterials));

static FAutoConsoleCommand GCreateProductionRaftMaterialsCommand(
    TEXT("RaftSim.CreateProductionRaftMaterials"),
    TEXT("Author only the runtime wet-coated raft tube and floor materials."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateProductionRaftMaterials));

static FAutoConsoleCommand GCreateProductionCC0SkinMaterialsCommand(
    TEXT("RaftSim.CreateProductionCC0SkinMaterials"),
    TEXT("Author only the five licensed-atlas production CC0 skin materials."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateProductionCC0SkinMaterials));

static FAutoConsoleCommand GCreateOfflineMetaHumanSkinMaterialCommand(
    TEXT("RaftSim.CreateOfflineMetaHumanSkinMaterial"),
    TEXT("Author the self-contained skeletal skin for the offline MetaHuman archetype."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateOfflineMetaHumanSkinMaterial));

static FAutoConsoleCommand GCreateCroppedMetaHumanFaceMaterialCommand(
    TEXT("RaftSim.CreateCroppedMetaHumanFaceMaterial"),
    TEXT("Author the baked MetaHuman face shader with a runtime shoulder-apron crop."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateCroppedMetaHumanFaceMaterial));

static FAutoConsoleCommand GCreateRiverBoulderMaterialCommand(
    TEXT("RaftSim.CreateRiverBoulderMaterial"),
    TEXT("Author the project-owned world-space wet river-boulder material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateRiverBoulderMaterial));

static FAutoConsoleCommand GCreateReviewedRiverBoulderMaterialCommand(
    TEXT("RaftSim.CreateReviewedRiverBoulderMaterial"),
    TEXT("Author only the reviewed project-owned wet river-boulder material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateReviewedRiverBoulderMaterial));

static FAutoConsoleCommand GCreateWaterVfxMaterialCommand(
    TEXT("RaftSim.CreateWaterVfxMaterial"),
    TEXT("Author only the solver-driven soft-card spray, mist and impact-foam material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateWaterVfxMaterial));

static FAutoConsoleCommand GPromoteReviewedEnvironmentMaterialsCommand(
    TEXT("RaftSim.PromoteReviewedEnvironmentMaterials"),
    TEXT("Save reviewed foliage/rock materials with Nanite and HISM usage enabled."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandlePromoteReviewedEnvironmentMaterials));

} // namespace RaftSimPhotorealMaterials
