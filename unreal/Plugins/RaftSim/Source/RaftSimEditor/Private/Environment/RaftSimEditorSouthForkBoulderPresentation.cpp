#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
bool LoadSouthForkProductionRockPresentation(
    UStaticMesh*& OutMesh,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMesh = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/Rocks/Production/"
             "SM_RaftSim_ProductionRiverBoulder."
             "SM_RaftSim_ProductionRiverBoulder"));
    UMaterialInterface* MineralParent =
        BuildSouthForkBoulderDressingMaterial(OutSummary);
    if (!OutMesh || !MineralParent)
    {
        OutSummary += TEXT(
            "Project-owned production river-boulder mesh or material is unavailable; "
            "refusing to rebuild full-reach presentation with invalid external scan bounds.\n");
        return false;
    }

    static const TCHAR* AssetName =
        TEXT("MI_RaftSim_SouthForkProductionBoulder");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
             "MI_RaftSim_SouthForkProductionBoulder");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
             "MI_RaftSim_SouthForkProductionBoulder."
             "MI_RaftSim_SouthForkProductionBoulder");
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
            "Could not create the bounded South Fork production-boulder material instance.\n");
        return false;
    }
    Instance->Modify();
    Instance->SetParentEditorOnly(MineralParent);
    // The dedicated dressing parent is already independent of imported UVs and
    // optional scan materials. Keep its calibrated source-scale controls in
    // the instance so lighting brackets can remain non-destructive.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("BoulderDetailWeight")), 0.34f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("BoulderAlbedoScale")), 0.70f);
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
            "Could not save the bounded South Fork production-boulder material instance.\n");
        return false;
    }
    OutMaterial = Instance;
    OutSummary += TEXT(
        "Using the project-owned closed production river boulder with rights-tracked "
        "world-aligned PBR dressing; malformed scans and generated UV seams are excluded.\n");
    return true;
}

bool ShouldSuppressSouthForkBoulderPresentation(
    const TArray<FSouthForkBoulderPresentationFootprint>& AcceptedFootprints,
    float StationM,
    float LateralM,
    float RadiusM)
{
    return Algo::AnyOf(
        AcceptedFootprints,
        [StationM, LateralM, RadiusM](
            const FSouthForkBoulderPresentationFootprint& Accepted)
        {
            const float StationDeltaM = StationM - Accepted.StationM;
            const float LateralDeltaM = LateralM - Accepted.LateralM;
            const float CenterDistanceM = FMath::Sqrt(
                StationDeltaM * StationDeltaM + LateralDeltaM * LateralDeltaM);
            return CenterDistanceM < 0.55f * (RadiusM + Accepted.RadiusM);
        });
}
} // namespace RaftSimEditorEnvironment
