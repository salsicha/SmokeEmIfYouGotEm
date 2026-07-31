#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionDivide.h"
#include "Materials/MaterialExpressionNoise.h"
#include "UObject/SavePackage.h"

namespace RaftSimEditorEnvironment
{
namespace
{
struct FWorldAlignedOutput
{
    UMaterialExpression* Expression = nullptr;
    int32 OutputIndex = 0;
};

FWorldAlignedOutput AddWorldAlignedProjection(
    UMaterial* Material,
    const TCHAR* ParameterName,
    UTexture2D* Texture,
    EMaterialSamplerType SamplerType,
    float TextureSizeCm,
    bool bNormalProjection)
{
    FWorldAlignedOutput Result;
    if (!Material || !Texture)
    {
        return Result;
    }

    UMaterialExpressionTextureObjectParameter* TextureObject =
        NewObject<UMaterialExpressionTextureObjectParameter>(Material);
    TextureObject->ParameterName = ParameterName;
    TextureObject->Texture = Texture;
    TextureObject->SamplerType = SamplerType;
    TextureObject->Group = TEXT("SouthForkBoulderDressing");
    Material->GetExpressionCollection().AddExpression(TextureObject);

    UMaterialExpressionConstant3Vector* TextureSize =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    TextureSize->Constant = FLinearColor(
        TextureSizeCm, TextureSizeCm, TextureSizeCm, 1.0f);
    Material->GetExpressionCollection().AddExpression(TextureSize);

    const TCHAR* FunctionPath = bNormalProjection
        ? TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
               "WorldAlignedNormal.WorldAlignedNormal")
        : TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
               "WorldAlignedTexture.WorldAlignedTexture");
    UMaterialFunctionInterface* ProjectionFunction =
        LoadObject<UMaterialFunctionInterface>(nullptr, FunctionPath);
    UMaterialExpressionMaterialFunctionCall* ProjectionCall =
        NewObject<UMaterialExpressionMaterialFunctionCall>(Material);
    Material->GetExpressionCollection().AddExpression(ProjectionCall);
    if (!ProjectionFunction ||
        !ProjectionCall->SetMaterialFunction(ProjectionFunction))
    {
        return Result;
    }

    for (int32 InputIndex = 0;
         InputIndex < ProjectionCall->FunctionInputs.Num(); ++InputIndex)
    {
        const FString InputName =
            ProjectionCall->GetInputName(InputIndex).ToString();
        FExpressionInput& Input =
            ProjectionCall->FunctionInputs[InputIndex].Input;
        if (InputName.Contains(TEXT("TextureObject"), ESearchCase::IgnoreCase))
        {
            Input.Expression = TextureObject;
        }
        else if (InputName.Contains(TEXT("TextureSize"), ESearchCase::IgnoreCase))
        {
            Input.Expression = TextureSize;
        }
    }
    for (int32 OutputIndex = 0;
         OutputIndex < ProjectionCall->FunctionOutputs.Num(); ++OutputIndex)
    {
        const FString OutputName = ProjectionCall->FunctionOutputs[OutputIndex]
            .Output.OutputName.ToString();
        if (OutputName.Equals(TEXT("XYZ Texture"), ESearchCase::IgnoreCase))
        {
            Result.Expression = ProjectionCall;
            Result.OutputIndex = OutputIndex;
            break;
        }
    }
    return Result;
}
} // namespace

UMaterialInterface* BuildSouthForkBoulderDressingMaterial(FString& OutSummary)
{
    static const TCHAR* AssetName =
        TEXT("M_RaftSim_SouthForkBoulderDressing");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
             "M_RaftSim_SouthForkBoulderDressing");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
             "M_RaftSim_SouthForkBoulderDressing."
             "M_RaftSim_SouthForkBoulderDressing");
    UTexture2D* Albedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockGround_4K/T_RockGround_BaseColor_4K."
             "T_RockGround_BaseColor_4K"));
    UTexture2D* Normal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockGround_4K/T_RockGround_NormalGL_4K."
             "T_RockGround_NormalGL_4K"));
    UTexture2D* Roughness = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockGround_4K/T_RockGround_Roughness_4K."
             "T_RockGround_Roughness_4K"));
    if (!Albedo || !Normal || !Roughness)
    {
        OutSummary += TEXT(
            "Rights-tracked RockGround PBR inputs are unavailable for South Fork boulder dressing.\n");
        return nullptr;
    }

    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = LoadObject<UMaterial>(nullptr, ObjectPath);
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
    for (TObjectPtr<UMaterialExpression>& ExistingExpression :
         Material->GetExpressionCollection().Expressions)
    {
        if (ExistingExpression)
        {
            if (ExistingExpression->IsRooted())
            {
                ExistingExpression->RemoveFromRoot();
            }
            ExistingExpression->MarkAsGarbage();
        }
    }
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);
    Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes);
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
    auto Multiply = [&](UMaterialExpression* A, int32 AOutput,
                        UMaterialExpression* B, int32 BOutput = 0)
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->A.OutputIndex = AOutput;
        Expression->B.Expression = B;
        Expression->B.OutputIndex = BOutput;
        Add(Expression);
        return Expression;
    };
    auto Lerp = [&](UMaterialExpression* A, int32 AOutput,
                    UMaterialExpression* B, int32 BOutput,
                    UMaterialExpression* Alpha, int32 AlphaOutput = 0)
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->A.OutputIndex = AOutput;
        Expression->B.Expression = B;
        Expression->B.OutputIndex = BOutput;
        Expression->Alpha.Expression = Alpha;
        Expression->Alpha.OutputIndex = AlphaOutput;
        Add(Expression);
        return Expression;
    };

    // The source declares a 1.5 m physical width. Blend a broader projection
    // into that native scale so large rocks keep macro variation without UV
    // stretching or the rejected smart-UV seams.
    const FWorldAlignedOutput MacroAlbedo = AddWorldAlignedProjection(
        Material, TEXT("SouthForkBoulderMacroAlbedo"), Albedo,
        SAMPLERTYPE_Color, 600.0f, false);
    const FWorldAlignedOutput DetailAlbedo = AddWorldAlignedProjection(
        Material, TEXT("SouthForkBoulderDetailAlbedo"), Albedo,
        SAMPLERTYPE_Color, 150.0f, false);
    const FWorldAlignedOutput DetailNormal = AddWorldAlignedProjection(
        Material, TEXT("SouthForkBoulderDetailNormal"), Normal,
        SAMPLERTYPE_Normal, 150.0f, true);
    const FWorldAlignedOutput DetailRoughness = AddWorldAlignedProjection(
        Material, TEXT("SouthForkBoulderDetailRoughness"), Roughness,
        SAMPLERTYPE_Masks, 150.0f, false);
    if (!MacroAlbedo.Expression || !DetailAlbedo.Expression ||
        !DetailNormal.Expression || !DetailRoughness.Expression)
    {
        OutSummary += TEXT(
            "World-aligned South Fork boulder projection functions could not be built.\n");
        return nullptr;
    }

    UMaterialExpressionScalarParameter* DetailWeight =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    DetailWeight->ParameterName = TEXT("BoulderDetailWeight");
    DetailWeight->DefaultValue = 0.34f;
    DetailWeight->Group = TEXT("SouthForkBoulderDressing");
    Add(DetailWeight);
    UMaterialExpressionLinearInterpolate* TwoScaleAlbedo = Lerp(
        MacroAlbedo.Expression, MacroAlbedo.OutputIndex,
        DetailAlbedo.Expression, DetailAlbedo.OutputIndex,
        DetailWeight);

    UMaterialExpressionVectorParameter* MineralTint =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    MineralTint->ParameterName = TEXT("BoulderMineralTint");
    MineralTint->DefaultValue = FLinearColor(0.54f, 0.50f, 0.45f, 1.0f);
    MineralTint->Group = TEXT("SouthForkBoulderDressing");
    Add(MineralTint);
    UMaterialExpressionScalarParameter* AlbedoScale =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    AlbedoScale->ParameterName = TEXT("BoulderAlbedoScale");
    AlbedoScale->DefaultValue = 0.70f;
    AlbedoScale->Group = TEXT("SouthForkBoulderDressing");
    Add(AlbedoScale);
    UMaterialExpressionMultiply* TintedAlbedo = Multiply(
        TwoScaleAlbedo, 0, MineralTint);
    UMaterialExpressionMultiply* FinalAlbedo = Multiply(
        TintedAlbedo, 0, AlbedoScale);

    UMaterialExpressionComponentMask* RoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    RoughnessMask->Input.Expression = DetailRoughness.Expression;
    RoughnessMask->Input.OutputIndex = DetailRoughness.OutputIndex;
    RoughnessMask->R = true;
    Add(RoughnessMask);
    UMaterialExpressionLinearInterpolate* FinalRoughness = Lerp(
        Constant(0.56f), 0,
        Constant(0.88f), 0,
        RoughnessMask);

    // Keep the production contact rock on the same solver-sampled wet/dry
    // boundary as the fallback material. The runtime rock actor writes the
    // live local surface elevation into RockWaterlineZCm; the very low default
    // leaves scenic dressing dry when it is not attached to a contact actor.
    UMaterialExpressionScalarParameter* WaterlineZ =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    WaterlineZ->ParameterName = TEXT("RockWaterlineZCm");
    WaterlineZ->DefaultValue = -1.0e7f;
    WaterlineZ->Group = TEXT("SouthForkBoulderDressing");
    Add(WaterlineZ);
    UMaterialExpressionScalarParameter* WetBandWidth =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    WetBandWidth->ParameterName = TEXT("RockWetBandWidthCm");
    WetBandWidth->DefaultValue = 55.0f;
    WetBandWidth->Group = TEXT("SouthForkBoulderDressing");
    Add(WetBandWidth);

    UMaterialExpressionWorldPosition* WetWorldPosition =
        NewObject<UMaterialExpressionWorldPosition>(Material);
    Add(WetWorldPosition);
    UMaterialExpressionComponentMask* WorldZ =
        NewObject<UMaterialExpressionComponentMask>(Material);
    WorldZ->Input.Expression = WetWorldPosition;
    WorldZ->B = true;
    Add(WorldZ);
    UMaterialExpressionNoise* WetlineNoise =
        NewObject<UMaterialExpressionNoise>(Material);
    WetlineNoise->Scale = 0.045f;
    WetlineNoise->Levels = 3;
    WetlineNoise->bTurbulence = true;
    WetlineNoise->OutputMin = -18.0f;
    WetlineNoise->OutputMax = 18.0f;
    Add(WetlineNoise);
    UMaterialExpressionSubtract* HeightAbove =
        NewObject<UMaterialExpressionSubtract>(Material);
    HeightAbove->A.Expression = WorldZ;
    HeightAbove->B.Expression = WaterlineZ;
    Add(HeightAbove);
    UMaterialExpressionAdd* JitteredHeight =
        NewObject<UMaterialExpressionAdd>(Material);
    JitteredHeight->A.Expression = HeightAbove;
    JitteredHeight->B.Expression = WetlineNoise;
    Add(JitteredHeight);
    UMaterialExpressionDivide* BandFraction =
        NewObject<UMaterialExpressionDivide>(Material);
    BandFraction->A.Expression = JitteredHeight;
    BandFraction->B.Expression = WetBandWidth;
    Add(BandFraction);
    UMaterialExpressionOneMinus* InvertedBand =
        NewObject<UMaterialExpressionOneMinus>(Material);
    InvertedBand->Input.Expression = BandFraction;
    Add(InvertedBand);
    UMaterialExpressionClamp* WetMask =
        NewObject<UMaterialExpressionClamp>(Material);
    WetMask->Input.Expression = InvertedBand;
    WetMask->MinDefault = 0.0f;
    WetMask->MaxDefault = 1.0f;
    Add(WetMask);

    UMaterialExpressionVectorParameter* WetTint =
        NewObject<UMaterialExpressionVectorParameter>(Material);
    WetTint->ParameterName = TEXT("BoulderWetTint");
    WetTint->DefaultValue = FLinearColor(0.48f, 0.50f, 0.53f, 1.0f);
    WetTint->Group = TEXT("SouthForkBoulderDressing");
    Add(WetTint);
    UMaterialExpressionMultiply* WetAlbedo = Multiply(
        FinalAlbedo, 0, WetTint);
    UMaterialExpressionLinearInterpolate* WaterlineAlbedo = Lerp(
        FinalAlbedo, 0, WetAlbedo, 0, WetMask);
    UMaterialExpressionLinearInterpolate* WaterlineRoughness = Lerp(
        FinalRoughness, 0, Constant(0.30f), 0, WetMask);
    UMaterialExpressionLinearInterpolate* WaterlineSpecular = Lerp(
        Constant(0.20f), 0, Constant(0.34f), 0, WetMask);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, WaterlineAlbedo);
    EditorData->Normal.Connect(
        DetailNormal.OutputIndex, DetailNormal.Expression);
    EditorData->Roughness.Connect(0, WaterlineRoughness);
    EditorData->Specular.Connect(0, WaterlineSpecular);
    EditorData->AmbientOcclusion.Connect(0, Constant(0.88f));

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += TEXT(
            "Could not save the South Fork world-aligned boulder dressing material.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Built the rights-tracked two-scale world-aligned South Fork boulder dressing material.\n");
    return Material;
}
} // namespace RaftSimEditorEnvironment
