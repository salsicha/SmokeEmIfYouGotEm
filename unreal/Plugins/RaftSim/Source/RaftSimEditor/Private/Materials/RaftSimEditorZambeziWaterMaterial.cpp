#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceConstant.h"

namespace RaftSimEditorEnvironment
{

UMaterialInstanceConstant* LoadOrCreateZambeziBatokaLiveWaterInstance(
    FString& OutSummary)
{
    if (!RaftSimPhotorealMaterials::BuildZambeziBatokaWaterTextureAssets())
    {
        OutSummary += TEXT(
            "Failed to create Zambezi Batoka live-water texture assets.\n");
        return nullptr;
    }

    static const TCHAR* PackagePath = TEXT(
        "/Game/RaftSim/Environment/ZambeziRun/Water/Materials/"
        "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV1");
    static const TCHAR* AssetName =
        TEXT("MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV1");
    static const TCHAR* ObjectPath = TEXT(
        "/Game/RaftSim/Environment/ZambeziRun/Water/Materials/"
        "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV1."
        "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV1");
    UMaterialInterface* SharedTransmissionParent = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "M_RaftSim_SouthForkRaftTransmissionWater."
             "M_RaftSim_SouthForkRaftTransmissionWater"));
    UTexture2D* FlowNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures/"
             "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal."
             "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal"));
    UTexture2D* FoamLace = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures/"
             "T_RaftSim_ZambeziBatokaWaterV1_FoamLace."
             "T_RaftSim_ZambeziBatokaWaterV1_FoamLace"));
    UPackage* Package = CreatePackage(PackagePath);
    if (!SharedTransmissionParent || !FlowNormal || !FoamLace || !Package)
    {
        OutSummary += TEXT(
            "Zambezi Batoka live-water parent or river-local texture is missing.\n");
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
            "Failed to create the Zambezi Batoka live-water material instance.\n");
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
    // This is only visual breakup. The shared parent multiplies the lace by
    // live solver foam/speed channels, so the texture cannot create a rapid,
    // wet a dry cell, or change any raft-facing hydraulic value.
    SetScalar(TEXT("HydraulicFoamCoverageGain"), 0.78f);
    SetScalar(TEXT("HydraulicFoamColorBreakupGain"), 0.66f);
    SetScalar(TEXT("HydraulicFoamColorCoreGain"), 0.80f);
    SetScalar(TEXT("SpeedAerationFraction"), 0.18f);
    SetScalar(TEXT("FoamRoughness"), 0.70f);
    SetScalar(TEXT("ReachHueVariation"), 0.10f);
    SetScalar(TEXT("CalmSurfaceColorVariation"), 0.12f);
    SetScalar(TEXT("FallbackSkyReflectionFloor"), 0.54f);
    SetScalar(TEXT("FallbackSkyReflectionVariation"), 0.30f);
    SetScalar(TEXT("RippleGrazingFloor"), 0.40f);
    SetScalar(TEXT("SlickNormalFloor"), 0.32f);
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
            "Failed to save the Zambezi Batoka live-water material instance.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Built Zambezi Batoka river-local live-volume water V1 with "
        "project-owned flow-normal and solver-masked foam-lace textures.\n");
    return Instance;
}

} // namespace RaftSimEditorEnvironment
