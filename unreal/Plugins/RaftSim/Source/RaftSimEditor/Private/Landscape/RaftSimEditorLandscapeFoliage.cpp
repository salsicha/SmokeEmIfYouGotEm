#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

namespace RaftSimEditorEnvironment
{
using namespace LandscapeFoliage;

UMaterialInstanceConstant* LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const TCHAR* FoliageType,
    const TCHAR* SourceParentObjectPath,
    const FLinearColor& FrontTint,
    const FLinearColor& BackTint,
    const FLinearColor& TransmissionTint,
    float RoughnessStrength,
    float NormalStrength,
    FString& OutSummary)
{
    UMaterialInterface* SourceParent = LoadObject<UMaterialInterface>(nullptr, SourceParentObjectPath);
    const FString RiverAssetName = GetFirstPartyMaterialRiverAssetName(Spec.RiverId);
    if (!SourceParent || RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Failed to load %s foliage parent for %s.\n"),
            FoliageType,
            *Spec.RiverId);
        return nullptr;
    }

    const FString AssetName = FString::Printf(
        TEXT("MI_RaftSim_%s_%s_BiomeFoliageCandidate"),
        *RiverAssetName,
        FoliageType);
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }

    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(SourceParent);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("BaseColor Tint Leaves")),
        FrontTint);
    for (const TCHAR* ParameterName : {
             TEXT("BaseColor Tint Leaf Backside"),
             TEXT("Tint Leaf Backside")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            BackTint);
    }
    for (const TCHAR* ParameterName : {
             TEXT("Translucency Tint Leaves"),
             TEXT("Translucency Tint"),
             TEXT("Tint Translucency")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            TransmissionTint);
    }
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaves Strength")),
        RoughnessStrength);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaf Backside")),
        FMath::Clamp(RoughnessStrength + 0.06f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Min")),
        FMath::Clamp(RoughnessStrength - 0.12f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Normal Strength")),
        NormalStrength);
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save %s.\n"), *ObjectPath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Built %s %s texture-preserving foliage candidate (roughness %.3f, normal %.3f).\n"),
        *Spec.RiverId,
        FoliageType,
        RoughnessStrength,
        NormalStrength);
    return Instance;
}

int32 BindLandscapeCandidateFoliageMaterial(
    UHierarchicalInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* FoliageMaterial)
{
    if (!Component || !Mesh || !FoliageMaterial)
    {
        return 0;
    }

    int32 BoundSlotCount = 0;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* SourceMaterial = Mesh->GetMaterial(MaterialIndex);
        const bool bIsFoliageSlot =
            SlotName.Equals(TEXT("TwoSided"), ESearchCase::IgnoreCase) ||
            (SourceMaterial && SourceMaterial->GetName().Contains(TEXT("Foliage"), ESearchCase::IgnoreCase));
        if (bIsFoliageSlot)
        {
            Component->SetMaterial(MaterialIndex, FoliageMaterial);
            ++BoundSlotCount;
        }
    }
    return BoundSlotCount;
}

bool ValidateLandscapeCandidateReviewedFirMaterials(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return false;
    }

    bool bHasReviewedBark = false;
    bool bHasReviewedNeedles = false;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }

        bHasReviewedBark |=
            SlotName.Contains(TEXT("bark"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_FirTree01_Bark"));
        bHasReviewedNeedles |=
            SlotName.Contains(TEXT("twig"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_FirTree01_Needles"));
    }
    return bHasReviewedBark && bHasReviewedNeedles;
}

bool ValidateLandscapeCandidateReviewedBroadleafMaterials(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return false;
    }

    bool bHasReviewedTrunk = false;
    bool bHasReviewedBranches = false;
    bool bHasReviewedLeaves = false;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }

        bHasReviewedTrunk |=
            SlotName.Contains(TEXT("trunk"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Trunk"));
        bHasReviewedBranches |=
            SlotName.Contains(TEXT("branch"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Branches"));
        bHasReviewedLeaves |=
            SlotName.Contains(TEXT("leaves"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Leaves"));
    }
    return bHasReviewedTrunk && bHasReviewedBranches && bHasReviewedLeaves;
}

bool ValidateLandscapeCandidateReviewedRockMaterial(UStaticMesh* Mesh)
{
    if (!Mesh || Mesh->GetStaticMaterials().Num() < 1)
    {
        return false;
    }
    UMaterialInterface* Material = Mesh->GetMaterial(0);
    return Material &&
        Material->GetPathName().Contains(TEXT("M_RockMossSet01")) &&
        Mesh->IsNaniteEnabled();
}

bool ValidateLandscapeCandidateReviewedPineMaterials(UStaticMesh* Mesh)
{
    if (!Mesh || !Mesh->IsNaniteEnabled())
    {
        return false;
    }
    bool bHasNeedles = false;
    bool bHasWood = false;
    for (int32 MaterialIndex = 0; MaterialIndex < Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
    {
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }
        const FString Path = Material->GetPathName();
        bHasNeedles |= Path.Contains(TEXT("M_PineTree01_Needles"));
        bHasWood |= Path.Contains(TEXT("M_PineTree01_Bark")) ||
            Path.Contains(TEXT("M_PineTree01_Trunk"));
    }
    return bHasNeedles && bHasWood;
}

bool ValidateFutaleufuScannedUnderstoryMaterials(UStaticMesh* Mesh)
{
    if (!Mesh || !Mesh->IsNaniteEnabled() ||
        Mesh->GetStaticMaterials().IsEmpty())
    {
        return false;
    }

    const bool bFirSapling = Mesh->GetName().StartsWith(TEXT("SM_FirSapling_"));
    const bool bFern = Mesh->GetName().StartsWith(TEXT("SM_Fern02_"));
    if (!bFirSapling && !bFern)
    {
        return false;
    }

    bool bHasExpectedMaterial = false;
    for (int32 MaterialIndex = 0;
         MaterialIndex < Mesh->GetStaticMaterials().Num();
         ++MaterialIndex)
    {
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            return false;
        }
        const FString MaterialPath = Material->GetPathName();
        if (!MaterialPath.Contains(
                TEXT("/FutaleufuTemperateForestSet_1K/")))
        {
            return false;
        }
        bHasExpectedMaterial |= bFirSapling
            ? MaterialPath.Contains(TEXT("M_FirSapling_"))
            : MaterialPath.Contains(TEXT("M_Fern02_Fronds"));
    }
    return bHasExpectedMaterial;
}

FBox GetLandscapeCandidateEffectiveMeshBounds(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return FBox(EForceInit::ForceInit);
    }

    const FBox RawBounds = Mesh->GetBoundingBox();
    if (RawBounds.GetSize().Z >= 100.0f || Mesh->GetNumSourceModels() == 0)
    {
        return RawBounds;
    }

    const FVector BuildScale = Mesh->GetSourceModel(0).BuildSettings.BuildScale3D;
    return FBox(RawBounds.Min * BuildScale, RawBounds.Max * BuildScale);
}

UStaticMesh* LoadOrCreateLandscapeCandidatePveStaticMesh(
    UWorld* World,
    const TCHAR* SourceSkeletalMeshPath,
    const TCHAR* OutputPackagePath,
    FString& OutSummary)
{
    if (!World)
    {
        return nullptr;
    }

    const FString AssetName = FPackageName::GetLongPackageAssetName(OutputPackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), OutputPackagePath, *AssetName);
    if (UStaticMesh* ExistingMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
    {
        return ExistingMesh;
    }

    USkeletalMesh* SourceMesh = LoadObject<USkeletalMesh>(nullptr, SourceSkeletalMeshPath);
    if (!SourceMesh)
    {
        OutSummary += FString::Printf(
            TEXT("Could not load complete PVE source species mesh %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    ASkeletalMeshActor* ConversionActor = World->SpawnActor<ASkeletalMeshActor>(
        ASkeletalMeshActor::StaticClass(),
        FTransform::Identity);
    if (!ConversionActor)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create the PVE static-mesh conversion actor for %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    USkeletalMeshComponent* SourceComponent = ConversionActor->GetSkeletalMeshComponent();
    SourceComponent->SetSkeletalMeshAsset(SourceMesh);
    SourceComponent->SetWorldTransform(FTransform::Identity);
    SourceComponent->RefreshBoneTransforms();
    SourceComponent->UpdateComponentToWorld();
    SourceComponent->MarkRenderStateDirty();
    FlushRenderingCommands();

    IMeshUtilities& MeshUtilities =
        FModuleManager::Get().LoadModuleChecked<IMeshUtilities>(TEXT("MeshUtilities"));
    TArray<UMeshComponent*> ComponentsToConvert;
    ComponentsToConvert.Add(SourceComponent);
    UStaticMesh* ConvertedMesh = MeshUtilities.ConvertMeshesToStaticMesh(
        ComponentsToConvert,
        FTransform::Identity,
        OutputPackagePath);
    ConversionActor->Destroy();
    if (!ConvertedMesh)
    {
        OutSummary += FString::Printf(
            TEXT("Failed to convert complete PVE source species mesh %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    ConvertedMesh->Modify();
    ConvertedMesh->GetNaniteSettings().bEnabled = true;
    ConvertedMesh->Build(false);
    ConvertedMesh->PostEditChange();
    ConvertedMesh->MarkPackageDirty();

    UPackage* Package = ConvertedMesh->GetOutermost();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(OutputPackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, ConvertedMesh, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save converted PVE species mesh %s.\n"),
            OutputPackagePath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Converted complete PVE source species %s -> %s with Nanite enabled.\n"),
        SourceSkeletalMeshPath,
        OutputPackagePath);
    return ConvertedMesh;
}






















































bool AddLandscapeCandidateBiomeDressing(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary)
{
    if (!World || !Landscape)
    {
        return false;
    }

    static const TCHAR* BroadleafSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/PVE_Deciduous_Tree_01.PVE_Deciduous_Tree_01");
    static const TCHAR* ConiferSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/PVE_Conifer_01.PVE_Conifer_01");
    static const TCHAR* ShrubSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Deciduous_Shrub_01/PVE_Deciduous_Shrub_01.PVE_Deciduous_Shrub_01");
    static const TCHAR* UnderstorySourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/PVE_Plant_01.PVE_Plant_01");

    const bool bSouthFork = Candidate.PreviewSpec.RiverId == TEXT("american_south_fork");
    const bool bZambezi = Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
    const bool bPacuare = Candidate.PreviewSpec.RiverId == TEXT("pacuare");
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bChilko =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const bool bColoradoHance =
        Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    const bool bOpaqueTemperate = bFutaleufu || bChilko;
    const bool bUsesOpaqueVolumetricVegetation =
        bZambezi || bPacuare || bOpaqueTemperate;
    TArray<UStaticMesh*> ReviewedRockMeshes;
    if (bSouthFork || bZambezi || bPacuare || bFutaleufu || bChilko)
    {
        for (int32 RockIndex = 1; RockIndex <= 6; ++RockIndex)
        {
            const FString AssetName = FString::Printf(
                TEXT("SM_RockMossSet01_rock_moss_set_01_rock%02d"),
                RockIndex);
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/%s.%s"),
                *AssetName,
                *AssetName);
            if (UStaticMesh* RockMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                ReviewedRockMeshes.Add(RockMesh);
            }
        }
        OutResult.DressingExternalRockMeshCount = ReviewedRockMeshes.Num();
        OutResult.DressingExternalReviewAssetCount += ReviewedRockMeshes.Num();
        OutResult.bDressingExternalRockMaterialsValidated =
            ReviewedRockMeshes.Num() == 6 &&
            Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
            {
                return ValidateLandscapeCandidateReviewedRockMaterial(Mesh);
            });
        if (!OutResult.bDressingExternalRockMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s reviewed rock comparison loaded %d/6 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                ReviewedRockMeshes.Num());
            return false;
        }
    }

    TArray<UStaticMesh*> ReviewedPineMeshes;
    if (bSouthFork)
    {
        constexpr TCHAR VariantLabels[] = {TEXT('a'), TEXT('b'), TEXT('c')};
        for (const TCHAR VariantLabel : VariantLabels)
        {
            const FString AssetName = FString::Printf(
                TEXT("SM_PineTree01_pine_tree_01_%c_LOD0"),
                VariantLabel);
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/%s.%s"),
                *AssetName,
                *AssetName);
            if (UStaticMesh* PineMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                ReviewedPineMeshes.Add(PineMesh);
            }
        }
        OutResult.DressingExternalPineMeshCount = ReviewedPineMeshes.Num();
        OutResult.DressingExternalReviewAssetCount += ReviewedPineMeshes.Num();
        OutResult.bDressingExternalPineMaterialsValidated =
            ReviewedPineMeshes.Num() == 3 &&
            Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
            {
                return ValidateLandscapeCandidateReviewedPineMaterials(Mesh);
            });
        if (!OutResult.bDressingExternalPineMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s reviewed pine comparison loaded %d/3 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                ReviewedPineMeshes.Num());
            return false;
        }
    }

    TArray<UStaticMesh*> FutaleufuScannedUnderstoryMeshes;
    if ((bFutaleufu || bPacuare) &&
        !RaftSimPhotorealMaterials::
            PromoteReviewedScannedUnderstoryMaterials(OutSummary))
    {
        return false;
    }
    if (bFutaleufu)
    {
        static const TCHAR* AssetNames[] = {
            TEXT("SM_FirSapling_fir_sapling_a"),
            TEXT("SM_FirSapling_fir_sapling_b"),
            TEXT("SM_FirSapling_fir_sapling_c"),
            TEXT("SM_Fern02_fern_02_a"),
            TEXT("SM_Fern02_fern_02_b"),
            TEXT("SM_Fern02_fern_02_c"),
            TEXT("SM_Fern02_fern_02_d")};
        for (const TCHAR* AssetName : AssetNames)
        {
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FutaleufuTemperateForestSet_1K/%s.%s"),
                AssetName,
                AssetName);
            if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                FutaleufuScannedUnderstoryMeshes.Add(Mesh);
            }
        }
        OutResult.DressingFutaleufuScannedUnderstoryMeshCount =
            FutaleufuScannedUnderstoryMeshes.Num();
        OutResult.DressingExternalReviewAssetCount +=
            FutaleufuScannedUnderstoryMeshes.Num();
        OutResult.bDressingFutaleufuScannedUnderstoryMaterialsValidated =
            FutaleufuScannedUnderstoryMeshes.Num() == 7 &&
            Algo::AllOf(
                FutaleufuScannedUnderstoryMeshes,
                [](UStaticMesh* Mesh)
                {
                    return ValidateFutaleufuScannedUnderstoryMaterials(Mesh);
                });
        if (!OutResult.bDressingFutaleufuScannedUnderstoryMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s scanned near-bank understory loaded %d/7 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                FutaleufuScannedUnderstoryMeshes.Num());
            return false;
        }
    }

    TArray<UStaticMesh*> PacuareScannedFernMeshes;
    if (bPacuare)
    {
        static const TCHAR* AssetNames[] = {
            TEXT("SM_Fern02_fern_02_a"),
            TEXT("SM_Fern02_fern_02_b"),
            TEXT("SM_Fern02_fern_02_c"),
            TEXT("SM_Fern02_fern_02_d")};
        for (const TCHAR* AssetName : AssetNames)
        {
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FutaleufuTemperateForestSet_1K/%s.%s"),
                AssetName,
                AssetName);
            if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                PacuareScannedFernMeshes.Add(Mesh);
            }
        }
        OutResult.DressingPacuareScannedFernMeshCount =
            PacuareScannedFernMeshes.Num();
        OutResult.DressingExternalReviewAssetCount +=
            PacuareScannedFernMeshes.Num();
        OutResult.bDressingPacuareScannedFernMaterialsValidated =
            PacuareScannedFernMeshes.Num() == 4 &&
            Algo::AllOf(
                PacuareScannedFernMeshes,
                [](UStaticMesh* Mesh)
                {
                    return Mesh &&
                        Mesh->GetName().StartsWith(TEXT("SM_Fern02_")) &&
                        ValidateFutaleufuScannedUnderstoryMaterials(Mesh);
                });
        if (!OutResult.bDressingPacuareScannedFernMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s scanned fern morphology loaded %d/4 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                PacuareScannedFernMeshes.Num());
            return false;
        }
    }

    UStaticMesh* BroadleafTreeMesh = nullptr;
    UStaticMesh* ConiferTreeMesh = nullptr;
    UStaticMesh* ShrubMesh = nullptr;
    UStaticMesh* UnderstoryMesh = nullptr;
    UStaticMesh* ZambeziGroundCoverMeshB = nullptr;
    UStaticMesh* TemperateBroadleafTreeMeshB = nullptr;
    UStaticMesh* TemperateConiferTreeMeshB = nullptr;
    UStaticMesh* TemperateShrubMeshB = nullptr;
    UStaticMesh* TemperateUnderstoryMeshB = nullptr;
    TArray<UStaticMesh*> PacuareForestFloorMeshes;
    UMaterialInterface* ZambeziOpaqueVegetationMaterial = nullptr;
    UMaterialInterface* PacuareOpaqueRainforestVegetationMaterial = nullptr;
    UMaterialInterface* TemperateOpaqueVegetationMaterial = nullptr;
    UMaterialInterface* ChilkoMutedGroundCoverMaterial = nullptr;
    UStaticMesh* HanceDrylandShrubMeshA = nullptr;
    UStaticMesh* HanceDrylandShrubMeshB = nullptr;
    UStaticMesh* HanceDrylandGroundCoverMeshA = nullptr;
    UStaticMesh* HanceDrylandGroundCoverMeshB = nullptr;
    UMaterialInterface* HanceDrylandVegetationMaterial = nullptr;
    if (bZambezi)
    {
        if (!CreateZambeziOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
                ZambeziGroundCoverMeshB,
                ZambeziOpaqueVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            ZambeziOpaqueVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
    }
    else if (bPacuare)
    {
        if (!CreatePacuareOpaqueRainforestVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
                PacuareOpaqueRainforestVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        if (!CreatePacuareForestFloorAssets(
                World,
                PacuareOpaqueRainforestVegetationMaterial,
                PacuareForestFloorMeshes,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingPacuareForestFloorMeshCount =
            PacuareForestFloorMeshes.Num();
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            PacuareOpaqueRainforestVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
    }
    else if (bOpaqueTemperate)
    {
        if (!CreateTemperateOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                TemperateBroadleafTreeMeshB,
                ConiferTreeMesh,
                TemperateConiferTreeMeshB,
                ShrubMesh,
                TemperateShrubMeshB,
                UnderstoryMesh,
                TemperateUnderstoryMeshB,
                TemperateOpaqueVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingBroadleafVariantAssetPath =
            TemperateBroadleafTreeMeshB->GetPathName();
        OutResult.DressingConiferVariantAssetPath =
            TemperateConiferTreeMeshB->GetPathName();
        OutResult.DressingShrubVariantAssetPath =
            TemperateShrubMeshB->GetPathName();
        OutResult.DressingUnderstoryVariantAssetPath =
            TemperateUnderstoryMeshB->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            TemperateOpaqueVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
        if (bChilko)
        {
            ChilkoMutedGroundCoverMaterial =
                CreateChilkoMutedGroundCoverMaterial(
                    TemperateOpaqueVegetationMaterial,
                    OutSummary);
            if (!ChilkoMutedGroundCoverMaterial)
            {
                return false;
            }
            OutResult.DressingUnderstoryFoliageMaterialAssetPath =
                ChilkoMutedGroundCoverMaterial->GetPathName();
        }
    }
    else
    {
        for (const TCHAR* SourcePath :
             {BroadleafSourcePath, ConiferSourcePath, ShrubSourcePath, UnderstorySourcePath})
        {
            OutResult.DressingSourceSkeletalMeshCount +=
                LoadObject<USkeletalMesh>(nullptr, SourcePath) ? 1 : 0;
        }

        BroadleafTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            BroadleafSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static"),
            OutSummary);
        ConiferTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            ConiferSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static"),
            OutSummary);
        ShrubMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            ShrubSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static"),
            OutSummary);
        UnderstoryMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            UnderstorySourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static"),
            OutSummary);
    }
    TArray<UStaticMesh*> ConvertedSpeciesMeshes = {
        BroadleafTreeMesh,
        ConiferTreeMesh,
        ShrubMesh,
        UnderstoryMesh};
    if (bOpaqueTemperate)
    {
        ConvertedSpeciesMeshes.Append({
            TemperateBroadleafTreeMeshB,
            TemperateConiferTreeMeshB,
            TemperateShrubMeshB,
            TemperateUnderstoryMeshB});
    }
    for (UStaticMesh* Mesh : ConvertedSpeciesMeshes)
    {
        OutResult.DressingAssetCount += Mesh ? 1 : 0;
        OutResult.DressingConvertedStaticMeshCount += Mesh ? 1 : 0;
    }
    OutResult.DressingAssetCount += ReviewedRockMeshes.Num() +
        ReviewedPineMeshes.Num() + FutaleufuScannedUnderstoryMeshes.Num() +
        PacuareScannedFernMeshes.Num() + PacuareForestFloorMeshes.Num();
    if (bColoradoHance)
    {
        if (!CreateHanceOpaqueDrylandVegetationAssets(
                World,
                HanceDrylandShrubMeshA,
                HanceDrylandShrubMeshB,
                HanceDrylandGroundCoverMeshA,
                HanceDrylandGroundCoverMeshB,
                HanceDrylandVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingAssetCount += 4;
        OutResult.DressingShrubAssetPath =
            HanceDrylandShrubMeshA->GetPathName();
        OutResult.DressingShrubVariantAssetPath =
            HanceDrylandShrubMeshB->GetPathName();
        OutResult.DressingUnderstoryAssetPath =
            HanceDrylandGroundCoverMeshA->GetPathName();
        OutResult.DressingUnderstoryVariantAssetPath =
            HanceDrylandGroundCoverMeshB->GetPathName();
    }
    OutResult.bDressingAssetsLoaded = bUsesOpaqueVolumetricVegetation
        ? OutResult.DressingSourceSkeletalMeshCount == 0 &&
            OutResult.DressingConvertedStaticMeshCount ==
                (bOpaqueTemperate ? 8 : 4) &&
            ValidateZambeziOpaqueVegetationMaterial(
                bZambezi
                    ? ZambeziOpaqueVegetationMaterial
                    : (bPacuare
                           ? PacuareOpaqueRainforestVegetationMaterial
                           : TemperateOpaqueVegetationMaterial)) &&
            (!bPacuare ||
             (PacuareForestFloorMeshes.Num() == 4 &&
              Algo::AllOf(PacuareForestFloorMeshes, [](UStaticMesh* Mesh)
              {
                  return Mesh && Mesh->IsNaniteEnabled();
              })))
        : OutResult.DressingSourceSkeletalMeshCount == 4 &&
            OutResult.DressingConvertedStaticMeshCount == 4;
    if (!OutResult.bDressingAssetsLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d source and %d/%d converted species meshes.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.DressingSourceSkeletalMeshCount,
            OutResult.DressingConvertedStaticMeshCount,
            bOpaqueTemperate ? 8 : 4);
        return false;
    }

    if (bSouthFork)
    {
        OutSummary += TEXT(
            "South Fork physical corridor excludes the previously rejected Poly Haven fir and "
            "small broadleaf candidates "
            "after their recorded not-lifelike visual rejection; converted PVE species remain the "
            "temporary non-production fallback. The rights-reviewed six-variant mossy rock set and "
            "three-variant dense pine set are enabled only for this isolated visual comparison.\n");
    }
    else if (bZambezi)
    {
        OutSummary += FString::Printf(
            TEXT("%s uses the rights-reviewed CC0 rock set only as an isolated river-specific visual "
                 "evaluation. Rejected tree candidates and the evaluated alpha-card savanna pack "
                 "remain excluded; four project-owned opaque volumetric vegetation forms replace "
                 "the PVE cards without claiming exact species, lifelike, or gameplay promotion.\n"),
            *Candidate.PreviewSpec.RiverId);
    }
    else if (bPacuare)
    {
        OutSummary += TEXT(
            "Pacuare replaces the repeated PVE alpha-card banks with two "
            "project-owned solid canopy forms plus opaque riparian shrub and "
            "ground-cover meshes. Four solid folded-leaf, root, and deadwood "
            "forms add bounded source-grounded forest-floor structure. The "
            "source-mask and slope-screened family is "
            "procedural rainforest infill, not exact species, ecology, or "
            "photoreal approval.\n");
    }
    else if (bOpaqueTemperate)
    {
        OutSummary += FString::Printf(
            TEXT("%s replaces repeated alpha-card PVE banks with eight project-owned "
                 "opaque volumetric temperate meshes: two deterministic morphologies "
                 "for each conifer, broadleaf, shrub, and ground-cover form. The family is procedural infill, "
                 "not exact-species or photoreal approval.\n"),
            *Candidate.PreviewSpec.RiverId);
    }
    else if (bColoradoHance)
    {
        OutSummary += TEXT(
            "Colorado Hance retains its four legacy PVE evaluation assets for "
            "compatibility but places zero legacy instances; two project-owned "
            "opaque dryland forms provide the countable ground-cover and shrub "
            "layers without the former horizontal PVE bench band. The added "
            "family is procedural gap fill, not exact-species, "
            "ecology, surveyed-terrain, or photoreal approval.\n");
    }

    OutResult.bDressingBoulderMeshNaniteEnabled =
        ReviewedRockMeshes.Num() == 6 &&
        Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
        {
            return Mesh && Mesh->IsNaniteEnabled();
        });
    OutResult.bDressingBroadleafMeshNaniteEnabled =
        BroadleafTreeMesh->IsNaniteEnabled() && ShrubMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate ||
         (TemperateBroadleafTreeMeshB->IsNaniteEnabled() &&
          TemperateShrubMeshB->IsNaniteEnabled()));
    OutResult.bDressingConiferMeshNaniteEnabled =
        ConiferTreeMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate || TemperateConiferTreeMeshB->IsNaniteEnabled()) &&
        (ReviewedPineMeshes.IsEmpty() ||
         Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
         {
             return Mesh && Mesh->IsNaniteEnabled();
         }));
    OutResult.bDressingUnderstoryMeshNaniteEnabled =
        UnderstoryMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate || TemperateUnderstoryMeshB->IsNaniteEnabled());

    FRaftSimPreviewImage WaterMask;
    FRaftSimPreviewImage VegetationMask;
    const bool bWaterMaskLoaded =
        !Candidate.PreviewSpec.WaterMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.WaterMaskImage, WaterMask);
    const bool bVegetationMaskLoaded =
        !Candidate.PreviewSpec.VegetationMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.VegetationMaskImage, VegetationMask);
    OutResult.bDressingSourceMasksLoaded = bWaterMaskLoaded && bVegetationMaskLoaded;
    if (!OutResult.bDressingSourceMasksLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s requires both water and vegetation masks.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }

    const FRaftSimEnvironmentPreviewSpec& Spec = Candidate.PreviewSpec;
    const FRaftSimLandscapeCandidateFoliageSettings FoliageSettings =
        GetLandscapeCandidateFoliageSettings(Spec.RiverId);
    UMaterialInterface* OpaqueVegetationMaterial = bZambezi
        ? ZambeziOpaqueVegetationMaterial
        : (bPacuare
               ? PacuareOpaqueRainforestVegetationMaterial
               : TemperateOpaqueVegetationMaterial);
    UMaterialInterface* BroadleafFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* ConiferFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* UnderstoryFoliageMaterial = OpaqueVegetationMaterial;
    if (bChilko)
    {
        UnderstoryFoliageMaterial = ChilkoMutedGroundCoverMaterial;
    }
    if (!bUsesOpaqueVolumetricVegetation)
    {
        BroadleafFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Broadleaf"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Materials/MI_LeafTree_01_Foliage.MI_LeafTree_01_Foliage"),
                FoliageSettings.BroadleafFrontTint,
                FoliageSettings.BroadleafBackTint,
                FoliageSettings.BroadleafTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
        ConiferFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Conifer"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/Materials/MI_Conifer_Foliage_01.MI_Conifer_Foliage_01"),
                FoliageSettings.ConiferFrontTint,
                FoliageSettings.ConiferBackTint,
                FoliageSettings.ConiferTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
        UnderstoryFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Understory"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/Materials/MI_PVE_Plant_01.MI_PVE_Plant_01"),
                FoliageSettings.BroadleafFrontTint,
                FoliageSettings.BroadleafBackTint,
                FoliageSettings.BroadleafTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
    }
    OutResult.DressingFoliageMaterialAssetCount = (bUsesOpaqueVolumetricVegetation
        ? (OpaqueVegetationMaterial ? 1 : 0) +
            (bChilko && ChilkoMutedGroundCoverMaterial ? 1 : 0)
        : (BroadleafFoliageMaterial ? 1 : 0) +
            (ConiferFoliageMaterial ? 1 : 0) +
            (UnderstoryFoliageMaterial ? 1 : 0)) +
        (bColoradoHance && HanceDrylandVegetationMaterial ? 1 : 0);
    const int32 ExpectedFoliageMaterialAssetCount =
        (bUsesOpaqueVolumetricVegetation ? (bChilko ? 2 : 1) : 3) +
        (bColoradoHance ? 1 : 0);
    if (OutResult.DressingFoliageMaterialAssetCount !=
        ExpectedFoliageMaterialAssetCount)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/%d required foliage materials.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialAssetCount,
            ExpectedFoliageMaterialAssetCount);
        return false;
    }
    const FString BroadleafComponentName =
        bZambezi
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bPacuare
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueCanopyA_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bOpaqueTemperate
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ReviewedBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PveWholeBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId);
    UHierarchicalInstancedStaticMeshComponent* BroadleafTreeInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            BroadleafTreeMesh,
            BroadleafComponentName,
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    const FString ConiferComponentName =
        bZambezi
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bPacuare
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueCanopyB_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bOpaqueTemperate
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueConifer_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ReviewedFirConifer_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PveWholeConifer_%s"),
                  *Candidate.PreviewSpec.RiverId);
    UHierarchicalInstancedStaticMeshComponent* ConiferTreeInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ConiferTreeMesh,
            ConiferComponentName,
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* ShrubInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ShrubMesh,
            bZambezi
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueThornScrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bPacuare
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueRiparianShrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bOpaqueTemperate
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueShrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PveWholeShrub_%s"),
                      *Candidate.PreviewSpec.RiverId),
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* UnderstoryInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            UnderstoryMesh,
            bZambezi
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bPacuare
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bOpaqueTemperate
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PveWholeUnderstory_%s"),
                      *Candidate.PreviewSpec.RiverId),
            true,
            bUsesOpaqueVolumetricVegetation ? UnderstoryFoliageMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* TemperateBroadleafTreeInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateBroadleafTreeMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueBroadleafB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateConiferTreeInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateConiferTreeMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueConiferB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateShrubInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateShrubMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueShrubB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateUnderstoryInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateUnderstoryMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueGroundCoverB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              bChilko
                  ? ChilkoMutedGroundCoverMaterial
                  : TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandGroundCoverInstancesA =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandGroundCoverMeshA,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandGroundCoverA"),
              false,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandGroundCoverInstancesB =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandGroundCoverMeshB,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandGroundCoverB"),
              false,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandShrubInstancesA =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandShrubMeshA,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandShrubA"),
              true,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandShrubInstancesB =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandShrubMeshB,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandShrubB"),
              true,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* ZambeziBankMosaicInstances =
        bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOrganicBankMosaic_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraRiparianTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              BroadleafTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraUmbrellaTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ConiferTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraThornScrubInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraThornScrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchGroundCoverInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchGroundCover_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchGroundCoverInstancesB = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ZambeziGroundCoverMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchGroundCoverB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchRiparianTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              BroadleafTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchUmbrellaTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ConiferTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchThornScrubInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchThornScrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    TArray<UHierarchicalInstancedStaticMeshComponent*> ReviewedRockInstances;
    for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
    {
        ReviewedRockInstances.Add(AddLandscapeCandidateInstancedMeshComponent(
            World,
            ReviewedRockMeshes[RockIndex],
            FString::Printf(
                TEXT("RaftSim_LandscapeCandidate_ReviewedRock%02d_%s"),
                RockIndex + 1,
                *Candidate.PreviewSpec.RiverId),
            true));
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        TemperateWaterlineStructureInstances;
    if (bOpaqueTemperate)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            TemperateWaterlineStructureInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_TemperateWaterlineStructureRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ChilkoOrganicShorelineGravelInstances;
    if (bChilko)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            ChilkoOrganicShorelineGravelInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGravelRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ChilkoOrganicShorelineGroundCoverInstances;
    if (bChilko)
    {
        ChilkoOrganicShorelineGroundCoverInstances = {
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                UnderstoryMesh,
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGroundCoverA_%s"),
                    *Candidate.PreviewSpec.RiverId),
                false,
                ChilkoMutedGroundCoverMaterial),
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                TemperateUnderstoryMeshB,
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGroundCoverB_%s"),
                    *Candidate.PreviewSpec.RiverId),
                false,
                ChilkoMutedGroundCoverMaterial)};
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        PacuareOrganicShorelineRockInstances;
    if (bPacuare)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            PacuareOrganicShorelineRockInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    UHierarchicalInstancedStaticMeshComponent*
        PacuareOrganicShorelineGroundCoverInstances = bPacuare
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineGroundCover_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              PacuareOpaqueRainforestVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        PacuareOrganicShorelineShrubInstances = bPacuare
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineShrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              PacuareOpaqueRainforestVegetationMaterial)
        : nullptr;
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        PacuareScannedFernInstances;
    for (int32 MeshIndex = 0;
         MeshIndex < PacuareScannedFernMeshes.Num();
         ++MeshIndex)
    {
        PacuareScannedFernInstances.Add(
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                PacuareScannedFernMeshes[MeshIndex],
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_PacuareScannedFern%02d_%s"),
                    MeshIndex + 1,
                    *Candidate.PreviewSpec.RiverId),
                false));
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        PacuareForestFloorInstances;
    for (int32 MeshIndex = 0;
         MeshIndex < PacuareForestFloorMeshes.Num();
         ++MeshIndex)
    {
        PacuareForestFloorInstances.Add(
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                PacuareForestFloorMeshes[MeshIndex],
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_PacuareForestFloor%02d_%s"),
                    MeshIndex + 1,
                    *Candidate.PreviewSpec.RiverId),
                MeshIndex >= 2,
                PacuareOpaqueRainforestVegetationMaterial));
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ZambeziRunnableLaunchTalusInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ZambeziDryScarpOutcropInstances;
    UMaterialInstanceConstant* ZambeziRunnableLaunchTalusMaterial = bZambezi
        ? LoadOrCreateZambeziRunnableLaunchTalusMaterial(OutSummary)
        : nullptr;
    if (bZambezi)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            UHierarchicalInstancedStaticMeshComponent* TalusComponent =
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchTalusRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true,
                    ZambeziRunnableLaunchTalusMaterial);
            if (TalusComponent)
            {
                TalusComponent->SetNumCustomDataFloats(1);
            }
            ZambeziRunnableLaunchTalusInstances.Add(TalusComponent);

            UHierarchicalInstancedStaticMeshComponent* OutcropComponent =
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_ZambeziDryScarpOutcropRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    false,
                    ZambeziRunnableLaunchTalusMaterial);
            if (OutcropComponent)
            {
                OutcropComponent->SetNumCustomDataFloats(1);
            }
            ZambeziDryScarpOutcropInstances.Add(OutcropComponent);
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*> ReviewedPineInstances;
    for (int32 PineIndex = 0; PineIndex < ReviewedPineMeshes.Num(); ++PineIndex)
    {
        ReviewedPineInstances.Add(AddLandscapeCandidateInstancedMeshComponent(
            World,
            ReviewedPineMeshes[PineIndex],
            FString::Printf(
                TEXT("RaftSim_LandscapeCandidate_ReviewedPine%02d_%s"),
                PineIndex + 1,
                *Candidate.PreviewSpec.RiverId),
            true));
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        FutaleufuScannedUnderstoryInstances;
    for (int32 MeshIndex = 0;
         MeshIndex < FutaleufuScannedUnderstoryMeshes.Num();
         ++MeshIndex)
    {
        FutaleufuScannedUnderstoryInstances.Add(
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                FutaleufuScannedUnderstoryMeshes[MeshIndex],
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_FutaleufuScannedUnderstory%02d_%s"),
                    MeshIndex + 1,
                    *Candidate.PreviewSpec.RiverId),
                MeshIndex < 3));
    }
    if (!BroadleafTreeInstances || !ConiferTreeInstances ||
        !ShrubInstances || !UnderstoryInstances ||
        (bOpaqueTemperate &&
         (!TemperateBroadleafTreeInstancesB ||
          !TemperateConiferTreeInstancesB ||
          !TemperateShrubInstancesB ||
          !TemperateUnderstoryInstancesB)) ||
        (bColoradoHance &&
         (!HanceDrylandGroundCoverInstancesA ||
          !HanceDrylandGroundCoverInstancesB ||
          !HanceDrylandShrubInstancesA ||
          !HanceDrylandShrubInstancesB)) ||
        (bZambezi && !ZambeziBankMosaicInstances) ||
        (bZambezi &&
         (!ZambeziCameraRiparianTreeInstances ||
          !ZambeziCameraUmbrellaTreeInstances ||
          !ZambeziCameraThornScrubInstances ||
          !ZambeziRunnableLaunchGroundCoverInstances ||
          !ZambeziRunnableLaunchGroundCoverInstancesB ||
          !ZambeziRunnableLaunchRiparianTreeInstances ||
          !ZambeziRunnableLaunchUmbrellaTreeInstances ||
          !ZambeziRunnableLaunchThornScrubInstances ||
          !ZambeziRunnableLaunchTalusMaterial)) ||
        Algo::AnyOf(ReviewedRockInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }) ||
        Algo::AnyOf(
            TemperateWaterlineStructureInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            ChilkoOrganicShorelineGravelInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            ChilkoOrganicShorelineGroundCoverInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            PacuareOrganicShorelineRockInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        (bPacuare &&
         (!PacuareOrganicShorelineGroundCoverInstances ||
          !PacuareOrganicShorelineShrubInstances)) ||
        Algo::AnyOf(
            PacuareScannedFernInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            PacuareForestFloorInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            ZambeziRunnableLaunchTalusInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(ReviewedPineInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }) ||
        Algo::AnyOf(
            FutaleufuScannedUnderstoryInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            })
        )
    {
        OutSummary += FString::Printf(
            TEXT("Failed to create one or more Landscape biome dressing instance components for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    if (bFutaleufu)
    {
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             FutaleufuScannedUnderstoryInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimFutaleufuTerminatorRun"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimFutaleufuScannedNearBankUnderstoryV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimFutaleufuScannedNearBankUnderstoryV1"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        }
    }
    if (bColoradoHance)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            HanceDrylandGroundCoverInstancesA,
            HanceDrylandGroundCoverInstancesB,
            HanceDrylandShrubInstancesA,
            HanceDrylandShrubInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimColoradoHanceRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimHanceOpaqueDrylandVegetationV2"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOfficialReferenceConstrainedProceduralGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoGeographyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimHanceOpaqueDrylandVegetationV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            GroundCoverComponents = {
                HanceDrylandGroundCoverInstancesA,
                HanceDrylandGroundCoverInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* GroundCover :
             GroundCoverComponents)
        {
            GroundCover->SetCastShadow(false);
            GroundCover->ComponentTags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
    }
    if (bOpaqueTemperate || bPacuare)
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        if (bOpaqueTemperate)
        {
            Components.Append({
                TemperateBroadleafTreeInstancesB,
                TemperateConiferTreeInstancesB,
                TemperateShrubInstancesB,
                TemperateUnderstoryInstancesB});
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimOpaqueVolumetricVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    bPacuare
                        ? TEXT("RaftSimPacuareUpperHuacasRun")
                        : (bChilko
                               ? TEXT("RaftSimChilkoLavaCanyonRun")
                               : TEXT("RaftSimFutaleufuTerminatorRun")));
                if (bPacuare)
                {
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimPacuareOpaqueRainforestV1"));
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                }
                if (bOpaqueTemperate)
                {
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimTemperateBankEcologyV4"));
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimTemperateMorphologyVariantFamily"));
                }
            }
            if (Component)
            {
                // Solid procedural lobes are a fail-closed replacement for
                // rejected alpha cards, not transmissive leaf clusters. Their
                // aggregate canopy shadows otherwise form a near-black bank
                // wall, so this fallback family does not cast scene shadows.
                Component->SetCastShadow(false);
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOpaqueVolumetricVegetation"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOpaqueFallbackShadowSuppressed"));
                if (bPacuare)
                {
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimPacuareOpaqueRainforestV1"));
                }
                if (bOpaqueTemperate)
                {
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimTemperateBankEcologyV4"));
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimTemperateMorphologyVariantFamily"));
                }
            }
        }
        UnderstoryInstances->SetCastShadow(false);
        TArray<UHierarchicalInstancedStaticMeshComponent*> GroundCoverComponents = {
            UnderstoryInstances};
        if (bOpaqueTemperate)
        {
            TemperateUnderstoryInstancesB->SetCastShadow(false);
            GroundCoverComponents.Add(TemperateUnderstoryInstancesB);
        }
        for (UHierarchicalInstancedStaticMeshComponent* GroundCoverComponent :
             GroundCoverComponents)
        {
            if (AActor* GroundOwner = GroundCoverComponent
                    ? GroundCoverComponent->GetOwner()
                    : nullptr)
            {
                GroundOwner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
                GroundOwner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                if (bChilko)
                {
                    GroundOwner->Tags.AddUnique(
                        TEXT("RaftSimChilkoMutedGroundCoverV3"));
                }
            }
            GroundCoverComponent->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankGroundCover"));
            if (bChilko)
            {
                GroundCoverComponent->ComponentTags.AddUnique(
                    TEXT("RaftSimChilkoMutedGroundCoverV3"));
            }
        }
    }
    if (bOpaqueTemperate)
    {
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             TemperateWaterlineStructureInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    bChilko
                        ? TEXT("RaftSimChilkoLavaCanyonRun")
                        : TEXT("RaftSimFutaleufuTerminatorRun"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimTemperateWaterlineStructureV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimTemperateWaterlineStructureV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOutsideProtectedSolverStrip"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
            }
        }
    }
    if (bChilko)
    {
        auto TagChilkoShorelineComponent = [](
            UHierarchicalInstancedStaticMeshComponent* Component,
            FName FamilyTag)
        {
            if (!Component)
            {
                return;
            }
            if (AActor* Owner = Component->GetOwner())
            {
                Owner->Tags.AddUnique(TEXT("RaftSimChilkoLavaCanyonRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimChilkoOrganicShorelineV2"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoShorelineNaturalismV3"));
                Owner->Tags.AddUnique(FamilyTag);
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoOrganicShorelineV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoShorelineNaturalismV3"));
            Component->ComponentTags.AddUnique(FamilyTag);
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        };
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGravelInstances)
        {
            TagChilkoShorelineComponent(
                Component,
                TEXT("RaftSimChilkoShorelineGravel"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoSortedGravelScaleV3"));
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGroundCoverInstances)
        {
            TagChilkoShorelineComponent(
                Component,
                TEXT("RaftSimChilkoShorelineGroundCover"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoMutedGroundCoverV3"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankGroundCover"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoMutedGroundCoverV3"));
        }
    }
    if (bPacuare)
    {
        auto TagPacuareShorelineComponent = [](
            UHierarchicalInstancedStaticMeshComponent* Component,
            FName FamilyTag)
        {
            if (!Component)
            {
                return;
            }
            if (AActor* Owner = Component->GetOwner())
            {
                Owner->Tags.AddUnique(TEXT("RaftSimPacuareUpperHuacasRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimPacuareOrganicShorelineV1"));
                Owner->Tags.AddUnique(FamilyTag);
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimPacuareOrganicShorelineV1"));
            Component->ComponentTags.AddUnique(FamilyTag);
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        };
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareOrganicShorelineRockInstances)
        {
            TagPacuareShorelineComponent(
                Component,
                TEXT("RaftSimPacuareShorelineMossRock"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
            }
        }
        TagPacuareShorelineComponent(
            PacuareOrganicShorelineGroundCoverInstances,
            TEXT("RaftSimPacuareShorelineGroundCover"));
        TagPacuareShorelineComponent(
            PacuareOrganicShorelineShrubInstances,
            TEXT("RaftSimPacuareShorelineShrub"));
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareScannedFernInstances)
        {
            TagPacuareShorelineComponent(
                Component,
                TEXT("RaftSimPacuareShorelineGroundCover"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPacuareScannedFernUnderstoryV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimPacuareScannedFernUnderstoryV1"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
            Component->SetCastShadow(false);
        }
        for (int32 ComponentIndex = 0;
             ComponentIndex < PacuareForestFloorInstances.Num();
             ++ComponentIndex)
        {
            UHierarchicalInstancedStaticMeshComponent* Component =
                PacuareForestFloorInstances[ComponentIndex];
            const FName FamilyTag = ComponentIndex < 2
                ? FName(TEXT("RaftSimPacuareFoldedLeafLitter"))
                : (ComponentIndex == 2
                       ? FName(TEXT("RaftSimPacuareButtressRoot"))
                       : FName(TEXT("RaftSimPacuareDeadwood")));
            TagPacuareShorelineComponent(Component, FamilyTag);
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimPacuareForestFloorV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralInfill"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoTerrainCollisionOrWaterAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimPacuareForestFloorV1"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimProceduralInfill"));
            if (ComponentIndex < 2)
            {
                Component->SetCastShadow(false);
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            PacuareEcologyComponents = {
                PacuareOrganicShorelineGroundCoverInstances,
                PacuareOrganicShorelineShrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareEcologyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
            }
        }
        PacuareOrganicShorelineGroundCoverInstances->SetCastShadow(false);
        if (AActor* Owner =
                PacuareOrganicShorelineGroundCoverInstances->GetOwner())
        {
            Owner->Tags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
        PacuareOrganicShorelineGroundCoverInstances->ComponentTags.AddUnique(
            TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
    }
    if (bZambezi)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances,
            ZambeziBankMosaicInstances,
            ZambeziCameraRiparianTreeInstances,
            ZambeziCameraUmbrellaTreeInstances,
            ZambeziCameraThornScrubInstances,
            ZambeziRunnableLaunchGroundCoverInstances,
            ZambeziRunnableLaunchGroundCoverInstancesB,
            ZambeziRunnableLaunchRiparianTreeInstances,
            ZambeziRunnableLaunchUmbrellaTreeInstances,
            ZambeziRunnableLaunchThornScrubInstances};
        const TArray<UStaticMesh*> Meshes = {
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh,
            UnderstoryMesh,
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh,
            ZambeziGroundCoverMeshB,
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh};
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziOpaqueVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimOpaqueVolumetricVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziOpaqueVegetation"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziRunnableLaunchTalusInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchTalusV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziBasaltAnalogMaterialV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimProjectOwnedMineralRetone"));
                Owner->Tags.AddUnique(TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralGeologyFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimDryBankPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimConditionedWaterlineWetBankV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimPerInstanceConditionedWaterline"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralWetBankNoMeasuredAuthority"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchTalusV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziBasaltAnalogMaterialV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimConditionedWaterlineWetBankV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimPerInstanceConditionedWaterline"));
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziDryScarpOutcropInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziDryScarpOutcropV20"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziBasaltAnalogMaterialV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimProjectOwnedMineralRetone"));
                Owner->Tags.AddUnique(TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralGeologyFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimUpperDryScarpPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimPerInstanceConditionedWaterline"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziDryScarpOutcropV20"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimPerInstanceConditionedWaterline"));
            }
        }
        if (AActor* MosaicOwner = ZambeziBankMosaicInstances
                ? ZambeziBankMosaicInstances->GetOwner()
                : nullptr)
        {
            MosaicOwner->Tags.AddUnique(TEXT("RaftSimOrganicBankMosaic"));
            MosaicOwner->Tags.AddUnique(TEXT("RaftSimCameraVisibleBankCover"));
        }
        if (ZambeziBankMosaicInstances)
        {
            UnderstoryInstances->SetCastShadow(false);
            ZambeziBankMosaicInstances->SetCastShadow(false);
            ZambeziBankMosaicInstances->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankMosaic"));
            ZambeziBankMosaicInstances->ComponentTags.AddUnique(
                TEXT("RaftSimCameraVisibleBankCover"));
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            CameraWoodyComponents = {
                ZambeziCameraRiparianTreeInstances,
                ZambeziCameraUmbrellaTreeInstances,
                ZambeziCameraThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             CameraWoodyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    TEXT("RaftSimCameraVisibleWoodyEcology"));
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicWoodyBankLayer"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling24Degrees"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimCameraVisibleWoodyEcology"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOrganicWoodyBankLayer"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling24Degrees"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchComponents = {
                ZambeziRunnableLaunchGroundCoverInstances,
                ZambeziRunnableLaunchGroundCoverInstancesB,
                ZambeziRunnableLaunchRiparianTreeInstances,
                ZambeziRunnableLaunchUmbrellaTreeInstances,
                ZambeziRunnableLaunchThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankEcologyV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziLowerEnergyLaunchEcologyV18"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziElevationStratifiedEcologyV19"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimEcologyStratumCustomDataV1"));
            }
            if (Component)
            {
                Component->SetCullDistances(0, 120000);
                Component->SetNumCustomDataFloats(1);
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchBankEcologyV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziLowerEnergyLaunchEcologyV18"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziElevationStratifiedEcologyV19"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimEcologyStratumCustomDataV1"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchGroundCoverComponents = {
                ZambeziRunnableLaunchGroundCoverInstances,
                ZambeziRunnableLaunchGroundCoverInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchGroundCoverComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankCover"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOrganicGroundCoverMorphologyV2"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchBankCover"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOrganicGroundCoverMorphologyV2"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchWoodyComponents = {
                ZambeziRunnableLaunchRiparianTreeInstances,
                ZambeziRunnableLaunchUmbrellaTreeInstances,
                ZambeziRunnableLaunchThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchWoodyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchWoodyEcology"));
                Owner->Tags.AddUnique(TEXT("RaftSimWoodySlopeCeiling34Degrees"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziLaunchCameraFaceMosaicV19"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyEcology"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling34Degrees"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziLaunchCameraFaceMosaicV19"));
            }
        }
        OutResult.DressingFoliageMaterialBoundSlotCount = 0;
        for (UStaticMesh* Mesh : Meshes)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                Mesh && Mesh->GetStaticMaterials().Num() == 1 &&
                    Mesh->GetMaterial(0) == ZambeziOpaqueVegetationMaterial
                ? 1
                : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount = 0;
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount == 13 &&
            ValidateZambeziOpaqueVegetationMaterial(
                ZambeziOpaqueVegetationMaterial) &&
            Algo::AllOf(
                Components,
                [ZambeziOpaqueVegetationMaterial](
                    UHierarchicalInstancedStaticMeshComponent* Component)
                {
                    return Component &&
                        Component->GetCollisionEnabled() ==
                            ECollisionEnabled::NoCollision &&
                        Component->GetMaterial(0) ==
                            ZambeziOpaqueVegetationMaterial;
                });
    }
    else if (bOpaqueTemperate || bPacuare)
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        TArray<UStaticMesh*> Meshes = {
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh};
        if (bOpaqueTemperate)
        {
            Components.Append({
                TemperateBroadleafTreeInstancesB,
                TemperateConiferTreeInstancesB,
                TemperateShrubInstancesB,
                TemperateUnderstoryInstancesB});
            Meshes.Append({
                TemperateBroadleafTreeMeshB,
                TemperateConiferTreeMeshB,
                TemperateShrubMeshB,
                TemperateUnderstoryMeshB});
        }
        OutResult.DressingFoliageMaterialBoundSlotCount = 0;
        for (UStaticMesh* Mesh : Meshes)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                Mesh && Mesh->GetStaticMaterials().Num() == 1 &&
                    Mesh->GetMaterial(0) == OpaqueVegetationMaterial
                ? 1
                : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount = 0;
        UMaterialInstanceConstant* ChilkoGroundCoverInstance =
            Cast<UMaterialInstanceConstant>(ChilkoMutedGroundCoverMaterial);
        FLinearColor ChilkoGroundCoverColorScale = FLinearColor::Black;
        float ChilkoGroundCoverShadowFillScale = 0.0f;
        const bool bChilkoGroundCoverMaterialValidated = !bChilko ||
            (ChilkoGroundCoverInstance &&
             ChilkoGroundCoverInstance->Parent == OpaqueVegetationMaterial &&
             ChilkoGroundCoverInstance->GetVectorParameterValue(
                 FMaterialParameterInfo(TEXT("VegetationColorScale")),
                 ChilkoGroundCoverColorScale) &&
             ChilkoGroundCoverInstance->GetScalarParameterValue(
                 FMaterialParameterInfo(TEXT("VegetationShadowFillScale")),
                 ChilkoGroundCoverShadowFillScale) &&
             ChilkoGroundCoverColorScale.Equals(
                 FLinearColor(0.62f, 0.38f, 0.24f, 1.0f),
                 0.001f) &&
             FMath::IsNearlyEqual(
                 ChilkoGroundCoverShadowFillScale,
                 0.28f,
                 0.001f));
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount ==
                (bOpaqueTemperate ? 8 : 4) &&
            ValidateZambeziOpaqueVegetationMaterial(
                OpaqueVegetationMaterial) &&
            bChilkoGroundCoverMaterialValidated &&
            Algo::AllOf(
                Components,
                [bChilko,
                 OpaqueVegetationMaterial,
                 ChilkoMutedGroundCoverMaterial,
                 UnderstoryInstances,
                 TemperateUnderstoryInstancesB](
                    UHierarchicalInstancedStaticMeshComponent* Component)
                {
                    UMaterialInterface* ExpectedMaterial =
                        bChilko &&
                            (Component == UnderstoryInstances ||
                             Component == TemperateUnderstoryInstancesB)
                        ? ChilkoMutedGroundCoverMaterial
                        : OpaqueVegetationMaterial;
                    return Component &&
                        Component->GetCollisionEnabled() ==
                            ECollisionEnabled::NoCollision &&
                        Component->GetMaterial(0) ==
                            ExpectedMaterial;
                }) &&
            (!bPacuare ||
             (PacuareOrganicShorelineGroundCoverInstances &&
              PacuareOrganicShorelineGroundCoverInstances->GetCollisionEnabled() ==
                  ECollisionEnabled::NoCollision &&
              PacuareOrganicShorelineGroundCoverInstances->GetMaterial(0) ==
                  OpaqueVegetationMaterial &&
              PacuareOrganicShorelineShrubInstances &&
              PacuareOrganicShorelineShrubInstances->GetCollisionEnabled() ==
                  ECollisionEnabled::NoCollision &&
              PacuareOrganicShorelineShrubInstances->GetMaterial(0) ==
                  OpaqueVegetationMaterial &&
              PacuareScannedFernInstances.Num() == 4 &&
              Algo::AllOf(
                  PacuareScannedFernInstances,
                  [](UHierarchicalInstancedStaticMeshComponent* Component)
                  {
                      return Component &&
                          Component->GetCollisionEnabled() ==
                              ECollisionEnabled::NoCollision &&
                          ValidateFutaleufuScannedUnderstoryMaterials(
                              Component->GetStaticMesh());
                  })));
    }
    else
    {
        OutResult.DressingFoliageMaterialBoundSlotCount =
            BindLandscapeCandidateFoliageMaterial(
                BroadleafTreeInstances,
                BroadleafTreeMesh,
                BroadleafFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                ConiferTreeInstances,
                ConiferTreeMesh,
                ConiferFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                ShrubInstances,
                ShrubMesh,
                BroadleafFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                UnderstoryInstances,
                UnderstoryMesh,
                UnderstoryFoliageMaterial);
        if (OutResult.bDressingExternalConiferReviewAssetLoaded)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                OutResult.bDressingExternalConiferMaterialsValidated ? 1 : 0;
        }
        if (OutResult.bDressingExternalBroadleafReviewAssetLoaded)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                OutResult.bDressingExternalBroadleafMaterialsValidated ? 1 : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount =
            FMath::Max(0, 4 - OutResult.DressingFoliageMaterialBoundSlotCount);
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount >= 3 &&
            (!OutResult.bDressingExternalBroadleafReviewAssetLoaded ||
             OutResult.bDressingExternalBroadleafMaterialsValidated) &&
            (!OutResult.bDressingExternalConiferReviewAssetLoaded ||
             OutResult.bDressingExternalConiferMaterialsValidated);
    }
    if (bColoradoHance)
    {
        const bool bHanceOpaqueDrylandValidated =
            ValidateZambeziOpaqueVegetationMaterial(
                HanceDrylandVegetationMaterial) &&
            HanceDrylandShrubMeshA &&
            HanceDrylandShrubMeshA->GetStaticMaterials().Num() == 1 &&
            HanceDrylandShrubMeshA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubMeshB &&
            HanceDrylandShrubMeshB->GetStaticMaterials().Num() == 1 &&
            HanceDrylandShrubMeshB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverMeshA &&
            HanceDrylandGroundCoverMeshA->GetStaticMaterials().Num() == 1 &&
            HanceDrylandGroundCoverMeshA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverMeshB &&
            HanceDrylandGroundCoverMeshB->GetStaticMaterials().Num() == 1 &&
            HanceDrylandGroundCoverMeshB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverInstancesA->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandGroundCoverInstancesA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverInstancesB->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandGroundCoverInstancesB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubInstancesA->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandShrubInstancesA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubInstancesB->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandShrubInstancesB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial;
        OutResult.DressingFoliageMaterialBoundSlotCount +=
            bHanceOpaqueDrylandValidated ? 4 : 0;
        OutResult.bDressingFoliageMaterialsValidated &=
            bHanceOpaqueDrylandValidated;
    }
    if (!OutResult.bDressingFoliageMaterialsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s bound %d foliage slots; material contract failed.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialBoundSlotCount);
        return false;
    }

    return AddLandscapeCandidatePlacements({
        World,
        Landscape,
        Candidate,
        OutResult,
        OutSummary,
        bPacuare,
        bFutaleufu,
        bChilko,
        bColoradoHance,
        bOpaqueTemperate,
        bUsesOpaqueVolumetricVegetation,
        ReviewedRockMeshes,
        ReviewedPineMeshes,
        FutaleufuScannedUnderstoryMeshes,
        PacuareScannedFernMeshes,
        BroadleafTreeMesh,
        ConiferTreeMesh,
        ShrubMesh,
        UnderstoryMesh,
        ZambeziGroundCoverMeshB,
        TemperateBroadleafTreeMeshB,
        TemperateConiferTreeMeshB,
        TemperateShrubMeshB,
        TemperateUnderstoryMeshB,
        PacuareForestFloorMeshes,
        HanceDrylandShrubMeshA,
        HanceDrylandShrubMeshB,
        HanceDrylandGroundCoverMeshA,
        HanceDrylandGroundCoverMeshB,
        WaterMask,
        VegetationMask,
        Spec,
        BroadleafTreeInstances,
        ConiferTreeInstances,
        ShrubInstances,
        UnderstoryInstances,
        TemperateBroadleafTreeInstancesB,
        TemperateConiferTreeInstancesB,
        TemperateShrubInstancesB,
        TemperateUnderstoryInstancesB,
        HanceDrylandGroundCoverInstancesA,
        HanceDrylandGroundCoverInstancesB,
        HanceDrylandShrubInstancesA,
        HanceDrylandShrubInstancesB,
        ZambeziBankMosaicInstances,
        ZambeziCameraRiparianTreeInstances,
        ZambeziCameraUmbrellaTreeInstances,
        ZambeziCameraThornScrubInstances,
        ZambeziRunnableLaunchGroundCoverInstances,
        ZambeziRunnableLaunchGroundCoverInstancesB,
        ZambeziRunnableLaunchRiparianTreeInstances,
        ZambeziRunnableLaunchUmbrellaTreeInstances,
        ZambeziRunnableLaunchThornScrubInstances,
        ReviewedRockInstances,
        TemperateWaterlineStructureInstances,
        ChilkoOrganicShorelineGravelInstances,
        ChilkoOrganicShorelineGroundCoverInstances,
        PacuareOrganicShorelineRockInstances,
        PacuareOrganicShorelineGroundCoverInstances,
        PacuareOrganicShorelineShrubInstances,
        PacuareScannedFernInstances,
        PacuareForestFloorInstances,
        ZambeziRunnableLaunchTalusInstances,
        ZambeziDryScarpOutcropInstances,
        ReviewedPineInstances,
        FutaleufuScannedUnderstoryInstances});
}
} // namespace RaftSimEditorEnvironment
