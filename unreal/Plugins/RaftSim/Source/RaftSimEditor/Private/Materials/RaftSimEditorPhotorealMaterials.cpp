// Photoreal river-water material (P4 photoreal track). Authors a genuine
// Single Layer Water material with depth-based colour, Fresnel-driven Lumen
// reflection, panned detail-normal ripples over the solver's geometric wave
// normals, and vertex-colour foam. Registered as a console command so it is
// generated headlessly, following the RaftSimEditor raw-expression idiom.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialFunctionInterface.h"
#include "Misc/PackageName.h"
#include "AssetCompilingManager.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimPhotorealMaterials
{

static UMaterial* BuildPhotorealRiverWaterMaterial()
{
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.M_RaftSim_PhotorealRiverWater");

    UPackage* Package = CreatePackage(PackagePath);
    if (Package == nullptr)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, ObjectPath));
    if (Material == nullptr)
    {
        Material = NewObject<UMaterial>(
            Package, TEXT("M_RaftSim_PhotorealRiverWater"),
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
    UMaterialExpressionVectorParameter* ShallowColor =
        Vector(TEXT("ShallowWaterColor"), FLinearColor(0.009f, 0.043f, 0.040f, 0.0f));
    UMaterialExpressionVectorParameter* DeepColor =
        Vector(TEXT("DeepWaterColor"), FLinearColor(0.002f, 0.014f, 0.019f, 0.0f));
    UMaterialExpressionComponentMask* DepthMask = Mask(VertexColor, false, true, false); // G
    UMaterialExpressionLinearInterpolate* WaterColor = Lerp(ShallowColor, DeepColor, DepthMask);

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
        SurfaceNoise, Scalar(TEXT("CalmSurfaceColorVariation"), 0.16f));
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
    SkyFresnel->Exponent = 4.2f;
    SkyFresnel->BaseReflectFraction = 0.018f;
    UMaterialExpressionMultiply* SkyReflectionAlpha = Mul(
        SkyFresnel, Scalar(TEXT("FallbackSkyReflectionStrength"), 0.46f));
    UMaterialExpressionVectorParameter* ReflectedSkyColor = Vector(
        TEXT("ReflectedSkyColor"), FLinearColor(0.10f, 0.24f, 0.32f, 0.0f));
    UMaterialExpressionLinearInterpolate* ReflectedWaterColor = Lerp(
        VariedWaterColor, ReflectedSkyColor, SkyReflectionAlpha);

    // Foam mask comes in per-vertex (grid resolution) so its edges are blocky;
    // break it up with high-frequency world-space noise so whitewater reads as
    // organic aeration rather than grid rectangles. broken = saturate(foam*(0.55+noise)).
    UMaterialExpressionComponentMask* FoamMask = Mask(VertexColor, true, false, false); // R
    UMaterialExpressionComponentMask* SpeedMask = Mask(VertexColor, false, false, true); // B
    UMaterialExpressionConstant* SpeedBias = NewObject<UMaterialExpressionConstant>(Material);
    SpeedBias->R = -0.12f; Add(SpeedBias);
    UMaterialExpressionAdd* BiasedSpeed = AddNode(SpeedMask, SpeedBias);
    UMaterialExpressionMultiply* ScaledSpeed = Mul(
        BiasedSpeed, Scalar(TEXT("HydraulicWhitewaterGain"), 2.2f));
    UMaterialExpressionClamp* SpeedWhitewater =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    SpeedWhitewater->Input.Expression = ScaledSpeed;
    SpeedWhitewater->MinDefault = 0.0f;
    SpeedWhitewater->MaxDefault = 0.72f;
    UMaterialExpressionAdd* CombinedFoam = AddNode(FoamMask, SpeedWhitewater);
    UMaterialExpressionMultiply* ConditionedFoam = Mul(
        CombinedFoam, Scalar(TEXT("HydraulicFoamIntensity"), 0.44f));
    UMaterialExpressionNoise* FoamNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    FoamNoise->Scale = 0.008f;
    FoamNoise->bTurbulence = true;
    FoamNoise->Levels = 5;
    FoamNoise->OutputMin = 0.05f;
    FoamNoise->OutputMax = 1.35f;
    // broken = saturate(foam * noise): noise spans below and above 1 so foamy
    // cell interiors get torn into streaks/patches rather than solid white.
    UMaterialExpressionMultiply* FoamRaw = Mul(ConditionedFoam, FoamNoise);
    UMaterialExpressionClamp* FoamBroken =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    FoamBroken->Input.Expression = FoamRaw; FoamBroken->MinDefault = 0.0f; FoamBroken->MaxDefault = 1.0f;
    UMaterialExpressionConstant3Vector* FoamColor = Const3(0.86f, 0.91f, 0.94f);
    UMaterialExpressionLinearInterpolate* BaseColor = Lerp(
        ReflectedWaterColor, FoamColor, FoamBroken);

    // --- Detail-normal ripples panned over the geometric wave normal --------
    UTexture2D* DetailNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
             "T_RaftSim_AmericanSouthFork_NormalAtlas.T_RaftSim_AmericanSouthFork_NormalAtlas"));

    UMaterialExpression* FinalNormal = nullptr;
    if (DetailNormal != nullptr)
    {
        UMaterialExpressionTextureCoordinate* UV =
            Cast<UMaterialExpressionTextureCoordinate>(Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        // Full-reach water UVs are authored in approximately three-metre
        // world-space repeats. Keep the material at one repeat so ripple scale
        // is stable across 4 km tiles rather than stretching to hundreds of
        // metres as it did with normalized per-tile UVs.
        UV->UTiling = 1.0f; UV->VTiling = 1.0f;

        auto Ripple = [&](float SpeedX, float SpeedY) -> UMaterialExpression*
        {
            UMaterialExpressionPanner* Pan =
                Cast<UMaterialExpressionPanner>(Add(NewObject<UMaterialExpressionPanner>(Material)));
            Pan->SpeedX = SpeedX; Pan->SpeedY = SpeedY; Pan->Coordinate.Expression = UV;
            UMaterialExpressionTextureSampleParameter2D* Sample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(
                    Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
            Sample->ParameterName = TEXT("RippleNormal");
            Sample->Texture = DetailNormal;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = Pan;
            return Sample;
        };
        UMaterialExpression* N1 = Ripple(0.24f, 0.07f);
        // The previous implementation added two already-normalized terrain
        // normals. That produced a high-frequency white/frosted surface in
        // guide-eye captures. Use the first-party water-normal atlas once and
        // let the solver-authored mesh normal carry the metre-scale current.
        UMaterialExpressionScalarParameter* NormalStrength = Scalar(TEXT("RippleStrength"), 0.0f);
        UMaterialExpressionConstant3Vector* FlatN = Const3(0.0f, 0.0f, 1.0f);
        FinalNormal = Lerp(FlatN, N1, NormalStrength);
    }

    // --- Roughness: glassy water, rougher in foam; Fresnel-lifted specular ---
    UMaterialExpressionScalarParameter* BaseRough = Scalar(TEXT("WaterRoughness"), 0.16f);
    UMaterialExpressionScalarParameter* FoamRoughScale = Scalar(TEXT("FoamRoughness"), 0.55f);
    UMaterialExpressionMultiply* FoamRough = Mul(FoamMask, FoamRoughScale);
    UMaterialExpressionAdd* Roughness = AddNode(BaseRough, FoamRough);

    UMaterialExpressionFresnel* Fresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    Fresnel->Exponent = 5.0f;
    Fresnel->BaseReflectFraction = 0.02f;
    UMaterialExpressionScalarParameter* SpecBase = Scalar(TEXT("Specular"), 0.5f);
    UMaterialExpressionAdd* Specular = AddNode(SpecBase, Mul(Fresnel, Scalar(TEXT("FresnelSpecular"), 0.4f)));

    UMaterialExpressionScalarParameter* Opacity = Scalar(TEXT("WaterOpacity"), 0.46f);
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
    // River-green tuning: green scatters most, red is absorbed with depth.
    UMaterialExpressionSingleLayerWaterMaterialOutput* WaterOutput =
        Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(
            Add(NewObject<UMaterialExpressionSingleLayerWaterMaterialOutput>(Material)));
    UMaterialExpressionVectorParameter* Scattering =
        Vector(TEXT("WaterScattering"), FLinearColor(0.010f, 0.034f, 0.032f, 0.0f));
    UMaterialExpressionVectorParameter* Absorption =
        Vector(TEXT("WaterAbsorption"), FLinearColor(0.24f, 0.11f, 0.085f, 0.0f));
    WaterOutput->ScatteringCoefficients.Expression = Scattering;
    WaterOutput->AbsorptionCoefficients.Expression = Absorption;

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

    UE_LOG(LogTemp, Display, TEXT("RaftSim: M_RaftSim_PhotorealRiverWater saved=%d"), bSaved ? 1 : 0);
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
    UTexture2D* GroundAlbedo = Load2D(*FString::Printf(TEXT("%s/ForestGround03_4K/T_ForestGround03_BaseColor_4K.T_ForestGround03_BaseColor_4K"), PolyHaven));
    UTexture2D* GroundNormal = Load2D(*FString::Printf(TEXT("%s/ForestGround03_4K/T_ForestGround03_NormalGL_4K.T_ForestGround03_NormalGL_4K"), PolyHaven));
    UTexture2D* GroundRough  = Load2D(*FString::Printf(TEXT("%s/ForestGround03_4K/T_ForestGround03_Roughness_4K.T_ForestGround03_Roughness_4K"), PolyHaven));

    const FOutRef RockA = WorldAligned(TEXT("RockAlbedo"), RockAlbedo, SAMPLERTYPE_Color, 1100.0f, false);
    const FOutRef RockN = WorldAligned(TEXT("RockNormal"), RockNormal, SAMPLERTYPE_Normal, 1100.0f, true);
    const FOutRef RockR = WorldAligned(TEXT("RockRough"), RockRough, SAMPLERTYPE_Masks, 1100.0f, false);
    const FOutRef GrA = WorldAligned(TEXT("GroundAlbedo"), GroundAlbedo, SAMPLERTYPE_Color, 900.0f, false);
    const FOutRef GrN = WorldAligned(TEXT("GroundNormal"), GroundNormal, SAMPLERTYPE_Normal, 900.0f, true);
    const FOutRef GrR = WorldAligned(TEXT("GroundRough"), GroundRough, SAMPLERTYPE_Masks, 900.0f, false);

    if (RockA.Expr == nullptr || GrA.Expr == nullptr)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim: terrain textures missing; skipping terrain material"));
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

    // Keep colour continuous across the coarse far-field surface. Slope still
    // selects physically relevant normal and roughness response, while source
    // macro colour and explicit rock instances carry large-scale geology.
    // Blending the rock/ground albedos by per-vertex slope created kilometre-
    // scale pale polygons that no real canyon surface exhibits.
    UMaterialExpression* BaseColor = LerpRefs(GrA, GrA, Flatness);
    UMaterialExpression* Normal = LerpRefs(RockN, GrN, Flatness);
    UMaterialExpression* Roughness = LerpRefs(RockR, GrR, Flatness);

    // M4 full-reach terrain stores the source-conditioned NAIP macro colour in
    // RGB vertex colour and the wet-bank mask in alpha. White vertex colour is
    // the neutral legacy value, so existing local riverbed meshes retain their
    // world-aligned material while the production corridor gains continuous
    // aerial-scale variation without allocating thirteen giant drape textures.
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

    // Nanite preserves the collision geometry and vertex buffer, but its
    // procedural conversion path does not reliably expose painted RGB vertex
    // color to every raster/material permutation. Full-reach detailed tiles
    // therefore bind their authoritative macro-albedo ribbon as a compact
    // per-tile texture. Far-field and legacy meshes retain the vertex-color
    // path through the default zero switch value.
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
    UMaterialExpressionVectorParameter* CanyonEdgeTone =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    CanyonEdgeTone->ParameterName = TEXT("CanyonEdgeMacroColor");
    CanyonEdgeTone->DefaultValue = FLinearColor(0.055f, 0.080f, 0.040f, 1.0f);
    CanyonEdgeTone->Group = TEXT("RaftSimPhotorealTerrain");
    Add(CanyonEdgeTone);
    UMaterialExpressionLinearInterpolate* EdgeMatchedSourceMacro =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    EdgeMatchedSourceMacro->A.Expression = ResolvedSourceMacro;
    EdgeMatchedSourceMacro->B.Expression = CanyonEdgeTone;
    EdgeMatchedSourceMacro->Alpha.Expression = ResolvedEdgeMask;
    Add(EdgeMatchedSourceMacro);

    UMaterialExpressionScalarParameter* MacroInfluence =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    MacroInfluence->ParameterName = TEXT("SourceMacroInfluence");
    // Preserve the authoritative aerial-scale hue while allowing the reviewed
    // rock/forest albedo to provide the missing sub-meter soil, scree, and
    // litter structure. A value of 1.0 reduced the production terrain to a
    // smooth vertex-color drape even though its normal map still had detail.
    MacroInfluence->DefaultValue = 0.86f;
    MacroInfluence->Group = TEXT("RaftSimPhotorealTerrain");
    Add(MacroInfluence);
    UMaterialExpressionLinearInterpolate* SourceConditionedBase =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SourceConditionedBase->A.Expression = BaseColor;
    SourceConditionedBase->B.Expression = EdgeMatchedSourceMacro;
    SourceConditionedBase->Alpha.Expression = MacroInfluence;
    Add(SourceConditionedBase);

    // The captured aerial macro is exposed for image analysis rather than a
    // game renderer. Bring it into the luminance range of a sunlit Sierra
    // canyon while retaining its measured hue and large-scale variation.
    UMaterialExpressionConstant3Vector* TerrainTone =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    TerrainTone->Constant = FLinearColor(0.82f, 0.86f, 0.78f, 1.0f);
    Add(TerrainTone);
    UMaterialExpressionMultiply* TonedBase = NewObject<UMaterialExpressionMultiply>(Material);
    TonedBase->A.Expression = SourceConditionedBase;
    TonedBase->B.Expression = TerrainTone;
    Add(TonedBase);

    UMaterialExpressionConstant3Vector* WetDarkColor =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    WetDarkColor->Constant = FLinearColor(0.38f, 0.42f, 0.40f, 1.0f);
    Add(WetDarkColor);
    UMaterialExpressionMultiply* WetDarkBase = NewObject<UMaterialExpressionMultiply>(Material);
    WetDarkBase->A.Expression = TonedBase;
    WetDarkBase->B.Expression = WetDarkColor;
    Add(WetDarkBase);
    UMaterialExpressionLinearInterpolate* WetAwareBase =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    WetAwareBase->A.Expression = TonedBase;
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

    UMaterialExpressionScalarParameter* Specular = NewObject<UMaterialExpressionScalarParameter>(Material);
    Specular->ParameterName = TEXT("TerrainSpecular"); Specular->DefaultValue = 0.25f;
    Specular->Group = TEXT("RaftSimPhotorealTerrain"); Add(Specular);

    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, WetAwareBase);
    Ed->Roughness.Connect(0, WetAwareRoughness);
    Ed->Specular.Connect(0, Specular);
    Ed->Normal.Connect(0, Normal);

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

static UMaterial* BuildSprayMistMaterial()
{
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
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, TEXT("M_RaftSim_SprayMist"),
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Translucent;
    Material->TwoSided = true;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);

    UMaterialExpressionConstant3Vector* Color =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    Color->Constant = FLinearColor(0.68f, 0.83f, 0.88f, 1.0f);
    Material->GetExpressionCollection().AddExpression(Color);
    UMaterialExpressionConstant* Opacity = NewObject<UMaterialExpressionConstant>(Material);
    Opacity->R = 0.055f;
    Material->GetExpressionCollection().AddExpression(Opacity);
    UMaterialExpressionConstant* Roughness = NewObject<UMaterialExpressionConstant>(Material);
    Roughness->R = 0.06f;
    Material->GetExpressionCollection().AddExpression(Roughness);
    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, Color);
    Ed->EmissiveColor.Connect(0, Color);
    Ed->Opacity.Connect(0, Opacity);
    Ed->Roughness.Connect(0, Roughness);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
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
    BuildPhotorealRiverWaterMaterial();
    BuildPhotorealTerrainMaterial();
    // Raft: charcoal PVC tubes (two-sided for the swept mesh) + grippy dark floor.
    BuildSolidMaterial(TEXT("M_RaftSim_RaftTube"), FLinearColor(0.05f, 0.055f, 0.075f, 1.0f), 0.42f, 0.0f, /*bTwoSided=*/true);
    BuildSolidMaterial(TEXT("M_RaftSim_RaftFloor"), FLinearColor(0.02f, 0.022f, 0.026f, 1.0f), 0.8f, 0.0f, /*bTwoSided=*/true);
    // Crew: PFD colour variants, helmet, skin, splash jacket, paddle.
    BuildSolidMaterial(TEXT("M_RaftSim_CrewPFD"), FLinearColor(0.78f, 0.22f, 0.02f, 1.0f), 0.6f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_PFD_Red"), FLinearColor(0.62f, 0.03f, 0.03f, 1.0f), 0.6f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_PFD_Yellow"), FLinearColor(0.85f, 0.68f, 0.03f, 1.0f), 0.6f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_PFD_Blue"), FLinearColor(0.03f, 0.20f, 0.55f, 1.0f), 0.6f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_Helmet"), FLinearColor(0.90f, 0.90f, 0.93f, 1.0f), 0.22f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_Skin"), FLinearColor(0.58f, 0.40f, 0.30f, 1.0f), 0.55f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_Wetsuit"), FLinearColor(0.015f, 0.018f, 0.025f, 1.0f), 0.5f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_PaddleShaft"), FLinearColor(0.04f, 0.04f, 0.05f, 1.0f), 0.35f, 0.1f);
    BuildSolidMaterial(TEXT("M_RaftSim_PaddleBlade"), FLinearColor(0.86f, 0.30f, 0.02f, 1.0f), 0.4f, 0.0f);
    // Full-reach environment infrastructure and hydraulic atmosphere.
    BuildSolidMaterial(TEXT("M_RaftSim_Asphalt"), FLinearColor(0.035f, 0.038f, 0.04f, 1.0f), 0.92f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_Timber"), FLinearColor(0.22f, 0.11f, 0.045f, 1.0f), 0.72f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_GalvanizedSteel"), FLinearColor(0.32f, 0.35f, 0.37f, 1.0f), 0.36f, 0.72f);
    BuildSolidMaterial(TEXT("M_RaftSim_WeatheredConcrete"), FLinearColor(0.29f, 0.28f, 0.25f, 1.0f), 0.86f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_RiverBoulder"), FLinearColor(0.34f, 0.30f, 0.23f, 1.0f), 0.88f, 0.0f);
    BuildSprayMistMaterial();
    PromoteReviewedEnvironmentMaterials();
}

static FAutoConsoleCommand GCreatePhotorealMaterialsCommand(
    TEXT("RaftSim.CreatePhotorealMaterials"),
    TEXT("Author the photoreal single-layer river-water material "
         "(/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater)."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreatePhotorealMaterials));

static FAutoConsoleCommand GPromoteReviewedEnvironmentMaterialsCommand(
    TEXT("RaftSim.PromoteReviewedEnvironmentMaterials"),
    TEXT("Save reviewed foliage/rock materials with Nanite and HISM usage enabled."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandlePromoteReviewedEnvironmentMaterials));

} // namespace RaftSimPhotorealMaterials
