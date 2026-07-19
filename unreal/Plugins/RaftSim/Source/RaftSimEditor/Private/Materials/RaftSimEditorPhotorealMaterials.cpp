// Photoreal river-water material (P4 photoreal track). Authors a genuine
// Single Layer Water material with depth-based colour, Fresnel-driven Lumen
// reflection, panned detail-normal ripples over the solver's geometric wave
// normals, and vertex-colour foam. Registered as a console command so it is
// generated headlessly, following the RaftSimEditor raw-expression idiom.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
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
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;
    bool bNeedsRecompile = false;
    Material->SetMaterialUsage(bNeedsRecompile, MATUSAGE_Water);

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
        Vector(TEXT("ShallowWaterColor"), FLinearColor(0.018f, 0.110f, 0.098f, 0.0f));
    UMaterialExpressionVectorParameter* DeepColor =
        Vector(TEXT("DeepWaterColor"), FLinearColor(0.003f, 0.030f, 0.038f, 0.0f));
    UMaterialExpressionComponentMask* DepthMask = Mask(VertexColor, false, true, false); // G
    UMaterialExpressionLinearInterpolate* WaterColor = Lerp(ShallowColor, DeepColor, DepthMask);

    // Foam mask comes in per-vertex (grid resolution) so its edges are blocky;
    // break it up with high-frequency world-space noise so whitewater reads as
    // organic aeration rather than grid rectangles. broken = saturate(foam*(0.55+noise)).
    UMaterialExpressionComponentMask* FoamMask = Mask(VertexColor, true, false, false); // R
    UMaterialExpressionNoise* FoamNoise =
        Cast<UMaterialExpressionNoise>(Add(NewObject<UMaterialExpressionNoise>(Material)));
    FoamNoise->Scale = 0.05f;
    FoamNoise->bTurbulence = true;
    FoamNoise->Levels = 5;
    FoamNoise->OutputMin = 0.05f;
    FoamNoise->OutputMax = 1.35f;
    // broken = saturate(foam * noise): noise spans below and above 1 so foamy
    // cell interiors get torn into streaks/patches rather than solid white.
    UMaterialExpressionMultiply* FoamRaw = Mul(FoamMask, FoamNoise);
    UMaterialExpressionClamp* FoamBroken =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    FoamBroken->Input.Expression = FoamRaw; FoamBroken->MinDefault = 0.0f; FoamBroken->MaxDefault = 1.0f;
    UMaterialExpressionConstant3Vector* FoamColor = Const3(0.86f, 0.91f, 0.94f);
    UMaterialExpressionLinearInterpolate* BaseColor = Lerp(WaterColor, FoamColor, FoamBroken);

    // --- Detail-normal ripples panned over the geometric wave normal --------
    UTexture2D* DetailNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/"
             "T_RaftSim_AmericanSouthFork_TerrainDetailNormal.T_RaftSim_AmericanSouthFork_TerrainDetailNormal"));

    UMaterialExpression* FinalNormal = nullptr;
    if (DetailNormal != nullptr)
    {
        UMaterialExpressionTextureCoordinate* UV =
            Cast<UMaterialExpressionTextureCoordinate>(Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
        UV->UTiling = 14.0f; UV->VTiling = 14.0f;

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
        UMaterialExpression* N1 = Ripple(0.028f, 0.010f);
        UMaterialExpression* N2 = Ripple(-0.017f, 0.022f);
        UMaterialExpressionAdd* SumN = AddNode(N1, N2);
        UMaterialExpressionScalarParameter* NormalStrength = Scalar(TEXT("RippleStrength"), 0.35f);
        UMaterialExpressionConstant3Vector* FlatN = Const3(0.0f, 0.0f, 1.0f);
        FinalNormal = Lerp(FlatN, SumN, NormalStrength);
    }

    // --- Roughness: glassy water, rougher in foam; Fresnel-lifted specular ---
    UMaterialExpressionScalarParameter* BaseRough = Scalar(TEXT("WaterRoughness"), 0.045f);
    UMaterialExpressionScalarParameter* FoamRoughScale = Scalar(TEXT("FoamRoughness"), 0.55f);
    UMaterialExpressionMultiply* FoamRough = Mul(FoamMask, FoamRoughScale);
    UMaterialExpressionAdd* Roughness = AddNode(BaseRough, FoamRough);

    UMaterialExpressionFresnel* Fresnel =
        Cast<UMaterialExpressionFresnel>(Add(NewObject<UMaterialExpressionFresnel>(Material)));
    Fresnel->Exponent = 5.0f;
    Fresnel->BaseReflectFraction = 0.02f;
    UMaterialExpressionScalarParameter* SpecBase = Scalar(TEXT("Specular"), 0.5f);
    UMaterialExpressionAdd* Specular = AddNode(SpecBase, Mul(Fresnel, Scalar(TEXT("FresnelSpecular"), 0.4f)));

    UMaterialExpressionScalarParameter* Opacity = Scalar(TEXT("WaterOpacity"), 0.82f);
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
        Vector(TEXT("WaterScattering"), FLinearColor(0.06f, 0.16f, 0.18f, 0.0f));
    UMaterialExpressionVectorParameter* Absorption =
        Vector(TEXT("WaterAbsorption"), FLinearColor(0.90f, 0.42f, 0.36f, 0.0f));
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

    const FOutRef RockA = WorldAligned(TEXT("RockAlbedo"), RockAlbedo, SAMPLERTYPE_Color, 700.0f, false);
    const FOutRef RockN = WorldAligned(TEXT("RockNormal"), RockNormal, SAMPLERTYPE_Normal, 700.0f, true);
    const FOutRef RockR = WorldAligned(TEXT("RockRough"), RockRough, SAMPLERTYPE_Masks, 700.0f, false);
    const FOutRef GrA = WorldAligned(TEXT("GroundAlbedo"), GroundAlbedo, SAMPLERTYPE_Color, 450.0f, false);
    const FOutRef GrN = WorldAligned(TEXT("GroundNormal"), GroundNormal, SAMPLERTYPE_Normal, 450.0f, true);
    const FOutRef GrR = WorldAligned(TEXT("GroundRough"), GroundRough, SAMPLERTYPE_Masks, 450.0f, false);

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

    UMaterialExpression* BaseColor = LerpRefs(RockA, GrA, Flatness);
    UMaterialExpression* Normal = LerpRefs(RockN, GrN, Flatness);
    UMaterialExpression* Roughness = LerpRefs(RockR, GrR, Flatness);

    UMaterialExpressionScalarParameter* Specular = NewObject<UMaterialExpressionScalarParameter>(Material);
    Specular->ParameterName = TEXT("TerrainSpecular"); Specular->DefaultValue = 0.25f;
    Specular->Group = TEXT("RaftSimPhotorealTerrain"); Add(Specular);

    UMaterialEditorOnlyData* Ed = Material->GetEditorOnlyData();
    Ed->BaseColor.Connect(0, BaseColor);
    Ed->Roughness.Connect(0, Roughness);
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
    const TCHAR* AssetName, const FLinearColor& Color, float Roughness, float Metallic)
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

static void HandleCreatePhotorealMaterials(const TArray<FString>&)
{
    BuildPhotorealRiverWaterMaterial();
    BuildPhotorealTerrainMaterial();
    // Charcoal PVC raft tubes and a safety-orange crew PFD.
    BuildSolidMaterial(TEXT("M_RaftSim_RaftTube"), FLinearColor(0.045f, 0.05f, 0.06f, 1.0f), 0.55f, 0.0f);
    BuildSolidMaterial(TEXT("M_RaftSim_CrewPFD"), FLinearColor(0.75f, 0.20f, 0.03f, 1.0f), 0.6f, 0.0f);
}

static FAutoConsoleCommand GCreatePhotorealMaterialsCommand(
    TEXT("RaftSim.CreatePhotorealMaterials"),
    TEXT("Author the photoreal single-layer river-water material "
         "(/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater)."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreatePhotorealMaterials));

} // namespace RaftSimPhotorealMaterials
