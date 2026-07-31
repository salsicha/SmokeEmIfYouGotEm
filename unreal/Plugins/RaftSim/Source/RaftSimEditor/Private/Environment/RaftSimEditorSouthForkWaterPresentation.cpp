#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
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
    UMaterialInterface* Parent = InOutMaterial;
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
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicWhitewaterGain")), 0.30f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HydraulicFoamIntensity")), 0.88f);
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
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("CalmRippleStrength")), 0.055f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FlowRippleStrength")), 0.075f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FoamRippleStrength")), 0.110f);
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
        "shallow/deep transmission and unchanged solver authority.\n");
    return true;
}

} // namespace RaftSimEditorEnvironment
