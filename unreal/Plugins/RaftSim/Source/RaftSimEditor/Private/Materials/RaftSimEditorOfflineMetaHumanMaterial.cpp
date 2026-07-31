#include "Materials/RaftSimEditorOfflineMetaHumanMaterial.h"

#include "AssetCompilingManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionClamp.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionIf.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSetMaterialAttributes.h"
#include "Materials/MaterialExpressionTransformPosition.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimPhotorealMaterials
{

// Self-contained technical skin for the offline MetaHuman core archetype.
// This combines only project-owned microdetail maps and does not synthesize a
// likeness or invoke any MetaHuman cloud service.
UMaterial* BuildOfflineMetaHumanSkinMaterial()
{
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_MetaHuman_Skin");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_MetaHuman_Skin."
             "M_RaftSim_MetaHuman_Skin");
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
            Package,
            TEXT("M_RaftSim_MetaHuman_Skin"),
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
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
    if (!Material || !MicroAlbedo || !MicroNormal)
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim: missing offline MetaHuman skin inputs"));
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;
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

    UMaterialExpressionVectorParameter* SkinTone =
        Cast<UMaterialExpressionVectorParameter>(
            Add(NewObject<UMaterialExpressionVectorParameter>(Material)));
    SkinTone->ParameterName = TEXT("SkinTone");
    SkinTone->DefaultValue = FLinearColor(0.54f, 0.31f, 0.20f, 1.0f);
    SkinTone->Group = TEXT("RaftSimMetaHumanSkin");

    UMaterialExpressionTextureCoordinate* MicroUv =
        Cast<UMaterialExpressionTextureCoordinate>(
            Add(NewObject<UMaterialExpressionTextureCoordinate>(Material)));
    MicroUv->UTiling = 34.0f;
    MicroUv->VTiling = 34.0f;

    UMaterialExpressionTextureSampleParameter2D* MicroAlbedoSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    MicroAlbedoSample->ParameterName = TEXT("SkinMicroAlbedo");
    MicroAlbedoSample->Texture = MicroAlbedo;
    MicroAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    MicroAlbedoSample->Coordinates.Expression = MicroUv;
    MicroAlbedoSample->Group = TEXT("RaftSimMetaHumanSkin");

    UMaterialExpressionMultiply* MicroGain =
        Cast<UMaterialExpressionMultiply>(Multiply(MicroAlbedoSample, Constant(2.0f)));
    UMaterialExpressionClamp* BoundedMicroGain =
        Cast<UMaterialExpressionClamp>(Add(NewObject<UMaterialExpressionClamp>(Material)));
    BoundedMicroGain->Input.Expression = MicroGain;
    BoundedMicroGain->MinDefault = 0.96f;
    BoundedMicroGain->MaxDefault = 1.04f;
    UMaterialExpressionMultiply* DetailedBase =
        Cast<UMaterialExpressionMultiply>(Multiply(SkinTone, BoundedMicroGain));

    UMaterialExpressionComponentMask* MicroMask =
        Cast<UMaterialExpressionComponentMask>(
            Add(NewObject<UMaterialExpressionComponentMask>(Material)));
    MicroMask->Input.Expression = MicroAlbedoSample;
    MicroMask->R = true;
    UMaterialExpressionLinearInterpolate* Roughness =
        Cast<UMaterialExpressionLinearInterpolate>(
            Lerp(Constant(0.44f), Constant(0.56f), MicroMask));

    UMaterialExpressionTextureSampleParameter2D* MicroNormalSample =
        Cast<UMaterialExpressionTextureSampleParameter2D>(
            Add(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material)));
    MicroNormalSample->ParameterName = TEXT("SkinMicroNormal");
    MicroNormalSample->Texture = MicroNormal;
    MicroNormalSample->SamplerType = SAMPLERTYPE_Normal;
    MicroNormalSample->Coordinates.Expression = MicroUv;
    MicroNormalSample->Group = TEXT("RaftSimMetaHumanSkin");
    UMaterialExpressionLinearInterpolate* DetailedNormal =
        Cast<UMaterialExpressionLinearInterpolate>(Lerp(
            Constant3(FLinearColor(0.0f, 0.0f, 1.0f, 1.0f)),
            MicroNormalSample,
            Constant(0.22f)));

    UMaterialExpressionMultiply* ScatterColor =
        Cast<UMaterialExpressionMultiply>(Multiply(
            SkinTone,
            Constant3(FLinearColor(0.19f, 0.13f, 0.105f, 1.0f))));
    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, DetailedBase);
    EditorData->Roughness.Connect(0, Roughness);
    EditorData->Specular.Connect(0, Constant(0.31f));
    EditorData->SubsurfaceColor.Connect(0, ScatterColor);
    EditorData->Opacity.Connect(0, Constant(0.90f));
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
        TEXT("RaftSim: offline MetaHuman skin saved=%d"),
        bSaved ? 1 : 0);
    return Material;
}

UMaterial* BuildCroppedMetaHumanFaceMaterial()
{
    static const TCHAR* SourcePath = TEXT(
        "/Game/RaftSim/Characters/Production/MetaHumans/Common/Lookdev_UHM/"
        "Skin/Materials/M_skin_unified_baked.M_skin_unified_baked");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_MetaHuman_FaceCroppedV2");
    static const TCHAR* ObjectName = TEXT("M_RaftSim_MetaHuman_FaceCroppedV2");
    static const TCHAR* ObjectPath = TEXT(
        "/Game/RaftSim/Materials/M_RaftSim_MetaHuman_FaceCroppedV2."
        "M_RaftSim_MetaHuman_FaceCroppedV2");

    UMaterial* Source = LoadObject<UMaterial>(nullptr, SourcePath);
    UPackage* Package = CreatePackage(PackagePath);
    if (!Source || !Package)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("RaftSim: installed baked MetaHuman face shader is unavailable"));
        return nullptr;
    }

    UMaterial* Material = LoadObject<UMaterial>(nullptr, ObjectPath);
    if (!Material)
    {
        Material = DuplicateObject<UMaterial>(Source, Package, ObjectName);
        if (!Material)
        {
            return nullptr;
        }
        Material->SetFlags(RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }

    Material->Modify();
    Material->BlendMode = BLEND_Masked;
    Material->OpacityMaskClipValue = 0.5f;
    Material->SetMaterialUsage(MATUSAGE_SkeletalMesh);

    bool bHasFaceCropGraph = false;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (Expression &&
            Expression->Desc == TEXT("RaftSimFaceCropMaterialAttributes"))
        {
            bHasFaceCropGraph = true;
            break;
        }
    }
    if (!bHasFaceCropGraph)
    {
    // Keep the complete installed baked-skin graph. This is the sole added
    // branch: pixels at or above the runtime crop height remain opaque; the
    // shoulder apron intended for conventional MetaHuman wardrobe disappears.
    UMaterialExpressionWorldPosition* WorldPosition =
        NewObject<UMaterialExpressionWorldPosition>(Material);
    WorldPosition->Desc = TEXT("RaftSimFaceCropWorldPosition");
    WorldPosition->WorldPositionShaderOffset = WPT_ExcludeAllShaderOffsets;
    Material->GetExpressionCollection().AddExpression(WorldPosition);

    UMaterialExpressionTransformPosition* LocalPosition =
        NewObject<UMaterialExpressionTransformPosition>(Material);
    LocalPosition->Desc = TEXT("RaftSimFaceCropLocalPosition");
    LocalPosition->Input.Expression = WorldPosition;
    LocalPosition->TransformSourceType = TRANSFORMPOSSOURCE_World;
    LocalPosition->TransformType = TRANSFORMPOSSOURCE_Local;
    Material->GetExpressionCollection().AddExpression(LocalPosition);

    UMaterialExpressionComponentMask* Height =
        NewObject<UMaterialExpressionComponentMask>(Material);
    Height->Desc = TEXT("RaftSimFaceCropHeightChannel");
    Height->Input.Expression = LocalPosition;
    Height->B = true;
    Material->GetExpressionCollection().AddExpression(Height);

    UMaterialExpressionScalarParameter* CropHeight =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    CropHeight->Desc = TEXT("RaftSimFaceCropHeightParameter");
    CropHeight->ParameterName = TEXT("RaftSimFaceCropHeightCm");
    CropHeight->DefaultValue = 130.0f;
    CropHeight->Group = TEXT("RaftSimMetaHumanComposition");
    Material->GetExpressionCollection().AddExpression(CropHeight);

    UMaterialExpressionConstant* Opaque =
        NewObject<UMaterialExpressionConstant>(Material);
    Opaque->R = 1.0f;
    Opaque->Desc = TEXT("RaftSimFaceCropOpaque");
    Material->GetExpressionCollection().AddExpression(Opaque);
    UMaterialExpressionConstant* Transparent =
        NewObject<UMaterialExpressionConstant>(Material);
    Transparent->R = 0.0f;
    Transparent->Desc = TEXT("RaftSimFaceCropTransparent");
    Material->GetExpressionCollection().AddExpression(Transparent);

    UMaterialExpressionIf* Crop = NewObject<UMaterialExpressionIf>(Material);
    Crop->Desc = TEXT("RaftSimFaceCropCompare");
    Crop->A.Expression = Height;
    Crop->B.Expression = CropHeight;
    Crop->AGreaterThanB.Expression = Opaque;
    Crop->AEqualsB.Expression = Opaque;
    Crop->ALessThanB.Expression = Transparent;
    Material->GetExpressionCollection().AddExpression(Crop);
    Material->GetEditorOnlyData()->OpacityMask.Connect(0, Crop);
    FExpressionInput OriginalMaterialAttributes =
        Material->GetEditorOnlyData()->MaterialAttributes;
    if (OriginalMaterialAttributes.Expression)
    {
        UMaterialExpressionSetMaterialAttributes* CroppedAttributes =
            NewObject<UMaterialExpressionSetMaterialAttributes>(Material);
        CroppedAttributes->Desc = TEXT("RaftSimFaceCropMaterialAttributes");
        CroppedAttributes->Inputs[0] = OriginalMaterialAttributes;
        CroppedAttributes->ConnectInputAttribute(MP_OpacityMask, Crop);
        Material->GetExpressionCollection().AddExpression(CroppedAttributes);
        Material->GetEditorOnlyData()->MaterialAttributes.Connect(
            0, CroppedAttributes);
    }
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
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim: cropped MetaHuman face material saved=%d"),
        bSaved ? 1 : 0);
    if (!bSaved)
    {
        return nullptr;
    }

    auto DuplicateInstance = [](
                                 const FString& SourceObjectPath,
                                 const FString& TargetPackagePath,
                                 const FString& TargetObjectName,
                                 UMaterialInterface* Parent)
        -> UMaterialInstanceConstant*
    {
        UMaterialInstanceConstant* SourceInstance =
            LoadObject<UMaterialInstanceConstant>(nullptr, *SourceObjectPath);
        UPackage* TargetPackage = CreatePackage(*TargetPackagePath);
        if (!SourceInstance || !TargetPackage || !Parent)
        {
            return nullptr;
        }
        const FString TargetObjectPath = FString::Printf(
            TEXT("%s.%s"), *TargetPackagePath, *TargetObjectName);
        UMaterialInstanceConstant* TargetInstance =
            LoadObject<UMaterialInstanceConstant>(nullptr, *TargetObjectPath);
        if (!TargetInstance)
        {
            TargetInstance = DuplicateObject<UMaterialInstanceConstant>(
                SourceInstance, TargetPackage, *TargetObjectName);
            if (!TargetInstance)
            {
                return nullptr;
            }
            TargetInstance->SetFlags(
                RF_Public | RF_Standalone | RF_Transactional);
            FAssetRegistryModule::AssetCreated(TargetInstance);
        }
        TargetInstance->Modify();
        TargetInstance->CopyMaterialUniformParametersEditorOnly(
            SourceInstance, true);
        TargetInstance->SetParentEditorOnly(Parent);
        TargetInstance->PostEditChange();
        TargetPackage->MarkPackageDirty();
        return TargetInstance;
    };
    auto SaveInstance = [&SaveArgs](
                            const FString& PackagePathToSave,
                            UMaterialInstanceConstant* Instance)
    {
        if (!Instance)
        {
            return false;
        }
        UPackage* InstancePackage = Instance->GetOutermost();
        const FString InstanceFilename = FPackageName::LongPackageNameToFilename(
            PackagePathToSave, FPackageName::GetAssetPackageExtension());
        return UPackage::SavePackage(
            InstancePackage, Instance, *InstanceFilename, SaveArgs);
    };

    const FString ChainRoot =
        TEXT("/Game/RaftSim/Materials/MetaHumanFaceCropV2");
    const FString SourceCommonRoot = TEXT(
        "/Game/RaftSim/Characters/Production/MetaHumans/Common/Lookdev_UHM/"
        "Skin/Materials/Baked");
    UMaterialInstanceConstant* CroppedLod0 = DuplicateInstance(
        SourceCommonRoot + TEXT("/MI_Head_Baked_LOD0_VT.MI_Head_Baked_LOD0_VT"),
        ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD0"),
        TEXT("MI_RaftSim_MetaHuman_FaceCropped_LOD0"),
        Material);
    UMaterialInstanceConstant* CroppedLod1 = DuplicateInstance(
        SourceCommonRoot + TEXT("/MI_Head_Baked_LOD1_VT.MI_Head_Baked_LOD1_VT"),
        ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD1"),
        TEXT("MI_RaftSim_MetaHuman_FaceCropped_LOD1"),
        CroppedLod0);
    UMaterialInstanceConstant* CroppedLod2 = DuplicateInstance(
        SourceCommonRoot + TEXT("/MI_Head_Baked_LOD2_VT.MI_Head_Baked_LOD2_VT"),
        ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD2"),
        TEXT("MI_RaftSim_MetaHuman_FaceCropped_LOD2"),
        CroppedLod1);
    if (!CroppedLod0 || !CroppedLod1 || !CroppedLod2)
    {
        return nullptr;
    }

    TArray<TPair<FString, UMaterialInstanceConstant*>> InstancesToSave = {
        {ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD0"), CroppedLod0},
        {ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD1"), CroppedLod1},
        {ChainRoot + TEXT("/MI_RaftSim_MetaHuman_FaceCropped_LOD2"), CroppedLod2}};
    const TArray<FString> CharacterNames = {
        TEXT("MHC_RaftSim_Guide"),
        TEXT("MHC_RaftSim_Crew_01"),
        TEXT("MHC_RaftSim_Crew_02"),
        TEXT("MHC_RaftSim_Crew_03"),
        TEXT("MHC_RaftSim_Crew_04")};
    for (const FString& CharacterName : CharacterNames)
    {
        const FString SourceRoot = FString::Printf(
            TEXT("/Game/RaftSim/Characters/Production/MetaHumans/%s/Face/Materials"),
            *CharacterName);
        const FString TargetRoot = ChainRoot + TEXT("/") + CharacterName;
        const FString Lod3Name = FString::Printf(
            TEXT("MI_%s_FaceCropped_LOD3"), *CharacterName);
        UMaterialInstanceConstant* CroppedLod3 = DuplicateInstance(
            SourceRoot + TEXT("/MI_Face_Skin_Baked_LOD3_VT."
                              "MI_Face_Skin_Baked_LOD3_VT"),
            TargetRoot + TEXT("/") + Lod3Name,
            Lod3Name,
            CroppedLod2);
        const FString Lod5Name = FString::Printf(
            TEXT("MI_%s_FaceCropped_LOD5to7"), *CharacterName);
        UMaterialInstanceConstant* CroppedLod5 = DuplicateInstance(
            SourceRoot + TEXT("/MI_Face_Skin_Baked_LOD5to7_VT."
                              "MI_Face_Skin_Baked_LOD5to7_VT"),
            TargetRoot + TEXT("/") + Lod5Name,
            Lod5Name,
            CroppedLod3);
        if (!CroppedLod3 || !CroppedLod5)
        {
            return nullptr;
        }
        InstancesToSave.Add({TargetRoot + TEXT("/") + Lod3Name, CroppedLod3});
        InstancesToSave.Add({TargetRoot + TEXT("/") + Lod5Name, CroppedLod5});
    }

    FAssetCompilingManager::Get().FinishAllCompilation();
    bool bSavedAllInstances = true;
    for (const TPair<FString, UMaterialInstanceConstant*>& Instance : InstancesToSave)
    {
        bSavedAllInstances &= SaveInstance(Instance.Key, Instance.Value);
    }
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim: cropped MetaHuman face instance chain saved=%d count=%d"),
        bSavedAllInstances ? 1 : 0,
        InstancesToSave.Num());
    return bSavedAllInstances ? Material : nullptr;
}

} // namespace RaftSimPhotorealMaterials
