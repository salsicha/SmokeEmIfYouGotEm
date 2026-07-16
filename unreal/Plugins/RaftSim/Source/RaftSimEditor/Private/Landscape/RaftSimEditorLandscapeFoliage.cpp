#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
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
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    TArray<UStaticMesh*> ReviewedRockMeshes;
    if (bSouthFork || bZambezi || bFutaleufu)
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

    for (const TCHAR* SourcePath :
         {BroadleafSourcePath, ConiferSourcePath, ShrubSourcePath, UnderstorySourcePath})
    {
        OutResult.DressingSourceSkeletalMeshCount +=
            LoadObject<USkeletalMesh>(nullptr, SourcePath) ? 1 : 0;
    }

    UStaticMesh* BroadleafTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
        World,
        BroadleafSourcePath,
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static"),
        OutSummary);
    UStaticMesh* ConiferTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
        World,
        ConiferSourcePath,
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static"),
        OutSummary);
    UStaticMesh* ShrubMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
        World,
        ShrubSourcePath,
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static"),
        OutSummary);
    UStaticMesh* UnderstoryMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
        World,
        UnderstorySourcePath,
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static"),
        OutSummary);
    for (UStaticMesh* Mesh : {BroadleafTreeMesh, ConiferTreeMesh, ShrubMesh, UnderstoryMesh})
    {
        OutResult.DressingAssetCount += Mesh ? 1 : 0;
        OutResult.DressingConvertedStaticMeshCount += Mesh ? 1 : 0;
    }
    OutResult.DressingAssetCount += ReviewedRockMeshes.Num() + ReviewedPineMeshes.Num();
    OutResult.bDressingAssetsLoaded =
        OutResult.DressingSourceSkeletalMeshCount == 4 &&
        OutResult.DressingConvertedStaticMeshCount == 4;
    if (!OutResult.bDressingAssetsLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/4 source and %d/4 converted species meshes.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.DressingSourceSkeletalMeshCount,
            OutResult.DressingConvertedStaticMeshCount);
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
                 "evaluation; rejected tree candidates remain excluded and no geology, lifelike, or "
                 "gameplay promotion is implied.\n"),
            *Candidate.PreviewSpec.RiverId);
    }

    OutResult.bDressingBoulderMeshNaniteEnabled =
        ReviewedRockMeshes.Num() == 6 &&
        Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
        {
            return Mesh && Mesh->IsNaniteEnabled();
        });
    OutResult.bDressingBroadleafMeshNaniteEnabled =
        BroadleafTreeMesh->IsNaniteEnabled() && ShrubMesh->IsNaniteEnabled();
    OutResult.bDressingConiferMeshNaniteEnabled =
        ConiferTreeMesh->IsNaniteEnabled() &&
        (ReviewedPineMeshes.IsEmpty() ||
         Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
         {
             return Mesh && Mesh->IsNaniteEnabled();
         }));
    OutResult.bDressingUnderstoryMeshNaniteEnabled = UnderstoryMesh->IsNaniteEnabled();

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
    UMaterialInstanceConstant* BroadleafFoliageMaterial =
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
    UMaterialInstanceConstant* ConiferFoliageMaterial =
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
    UMaterialInstanceConstant* UnderstoryFoliageMaterial =
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
    OutResult.DressingFoliageMaterialAssetCount =
        (BroadleafFoliageMaterial ? 1 : 0) +
        (ConiferFoliageMaterial ? 1 : 0) +
        (UnderstoryFoliageMaterial ? 1 : 0);
    if (OutResult.DressingFoliageMaterialAssetCount != 3)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/3 required foliage materials.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialAssetCount);
        return false;
    }
    const FString BroadleafComponentName =
        Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
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
            true);
    const FString ConiferComponentName =
        Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
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
            true);
    UHierarchicalInstancedStaticMeshComponent* ShrubInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ShrubMesh,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_PveWholeShrub_%s"), *Candidate.PreviewSpec.RiverId),
            true);
    UHierarchicalInstancedStaticMeshComponent* UnderstoryInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            UnderstoryMesh,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_PveWholeUnderstory_%s"), *Candidate.PreviewSpec.RiverId),
            true);
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
    if (!BroadleafTreeInstances || !ConiferTreeInstances ||
        !ShrubInstances || !UnderstoryInstances ||
        Algo::AnyOf(ReviewedRockInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }) ||
        Algo::AnyOf(ReviewedPineInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to create one or more Landscape biome dressing instance components for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
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
    if (!OutResult.bDressingFoliageMaterialsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s bound %d foliage slots; expected at least three complete-species leaf slots.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialBoundSlotCount);
        return false;
    }

    const bool bRainforest = Spec.bHasWaterfalls;
    const bool bZambeziWoodland = Spec.RiverId == TEXT("zambezi_batoka_gorge");
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> PhysicalCenterline;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, PhysicalCenterline, OutSummary))
    {
        return false;
    }
    const bool bPhysicalCorridor = Candidate.bPhysicalScaleSourceCorridor && PhysicalCenterline.Num() >= 2;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float LandscapeHalfWidth = Candidate.HorizontalSpanYCm * 0.5f;
    const float MaxBankOffset = bPhysicalCorridor
        ? FMath::Min(18000.0f, LandscapeHalfWidth - 220.0f)
        : FMath::Max(ActiveRiverHalfWidth + 300.0f, LandscapeHalfWidth - 220.0f);
    auto ResolveLogicalRiverPoint =
        [&Candidate, &PhysicalCenterline, bPhysicalCorridor](float LogicalX, float LateralOffset)
    {
        if (!bPhysicalCorridor)
        {
            return FVector2D(
                LogicalX,
                GetPreviewRiverCenterY(Candidate.PreviewSpec, LogicalX) + LateralOffset);
        }
        const float Progress = FMath::Clamp((LogicalX + 2500.0f) / 27900.0f, 0.0f, 1.0f);
        FVector2D Tangent;
        const FVector2D Center = SampleLandscapeCandidateCenterlineWorld(
            Candidate,
            PhysicalCenterline,
            Progress,
            &Tangent);
        const FVector2D Normal(-Tangent.Y, Tangent.X);
        return Center + Normal * LateralOffset;
    };
    auto GetLandscapeHeight = [Landscape, &Spec](float X, float Y)
    {
        return Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor)
            .Get(Spec.FlowWaterLevelOffsetCm - 24.0f);
    };
    auto AddGroundedInstance = [](UHierarchicalInstancedStaticMeshComponent* Component,
                                  UStaticMesh* Mesh,
                                  const FVector2D& GroundLocation,
                                  float GroundZ,
                                  const FRotator& Rotation,
                                  const FVector& Scale)
    {
        const FBox Bounds = GetLandscapeCandidateEffectiveMeshBounds(Mesh);
        const float GroundedPivotZ = GroundZ - Bounds.Min.Z * Scale.Z;
        Component->AddInstance(
            FTransform(
                Rotation,
                FVector(GroundLocation.X, GroundLocation.Y, GroundedPivotZ),
                Scale),
            true);
    };

    const int32 BoulderCount = bPhysicalCorridor
        ? 180
        : (Spec.bDesertCanyon ? 62 : (bRainforest ? 48 : 44));
    for (int32 BoulderIndex = 0; BoulderIndex < BoulderCount; ++BoulderIndex)
    {
        const float T = (static_cast<float>(BoulderIndex) + 0.5f) / static_cast<float>(BoulderCount);
        const float Phase = static_cast<float>(BoulderIndex) * 1.6180339f;
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const bool bChannelRock = BoulderIndex % 9 == 0;
        const float BaseX = FMath::Lerp(
            bPhysicalCorridor ? 5000.0f : -1600.0f,
            25500.0f,
            T) + 180.0f * FMath::Sin(Phase);
        const float BaseOffset = bChannelRock
            ? ActiveRiverHalfWidth * (0.62f + 0.24f * FMath::Abs(FMath::Sin(Phase * 0.77f)))
            : FMath::Lerp(
                  ActiveRiverHalfWidth + (bPhysicalCorridor && BaseX < 3200.0f ? 900.0f : 260.0f),
                  MaxBankOffset * 0.78f,
                  FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.43f)), 0.72f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 7; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                155.0f * FMath::Sin(Phase * 0.61f + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 135.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f),
                ActiveRiverHalfWidth * 0.20f,
                MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 400.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float TargetWaterT = bChannelRock ? 0.68f : 0.20f;
            const float Score = 1.0f - FMath::Abs(WaterT - TargetWaterT) -
                VegetationT * (bChannelRock ? 0.12f : 0.34f) +
                0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        const float TargetBoulderHeightCm = bPhysicalCorridor
            ? (65.0f + 18.0f * static_cast<float>(BoulderIndex % 6)) *
                (bChannelRock ? 1.05f : 1.0f)
            : (Spec.bDesertCanyon
                   ? 82.0f + 20.0f * static_cast<float>(BoulderIndex % 5)
                   : (bRainforest ? 74.0f + 18.0f * static_cast<float>(BoulderIndex % 5)
                                  : 66.0f + 16.0f * static_cast<float>(BoulderIndex % 5))) *
                (bChannelRock ? 0.72f : 1.0f);
        const float BoulderScaleZ = TargetBoulderHeightCm / 100.0f;
        if (ReviewedRockMeshes.Num() == 6 && ReviewedRockInstances.Num() == 6)
        {
            const int32 VariantIndex = BoulderIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetBoulderHeightCm / MeshHeightCm;
            AddGroundedInstance(
                ReviewedRockInstances[VariantIndex],
                RockMesh,
                FVector2D(BestX, BestY),
                GetLandscapeHeight(BestX, BestY),
                FRotator(
                    bChannelRock ? -5.0f : 2.0f * FMath::Sin(Phase),
                    static_cast<float>((BoulderIndex * 47) % 360),
                    3.0f * FMath::Cos(Phase * 0.73f)),
                FVector(
                    UniformScale * (0.92f + 0.07f * static_cast<float>(BoulderIndex % 4)),
                    UniformScale * (0.88f + 0.06f * static_cast<float>((BoulderIndex + 2) % 5)),
                    UniformScale));
        }
        else
        {
            const FLinearColor BoulderColor = FMath::Lerp(
                ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.70f : 0.52f),
                ScalePreviewColor(Spec.WaterColor, 0.28f),
                bChannelRock ? 0.24f : (bRainforest ? 0.16f : 0.10f));
            AActor* BoulderActor = AddPreviewIrregularRockActor(
                World,
                FString::Printf(TEXT("RaftSim_LandscapeCandidate_IrregularBoulder_%03d_%s"), BoulderIndex, *Spec.RiverId),
                FVector(BestX, BestY, GetLandscapeHeight(BestX, BestY)),
                static_cast<float>((BoulderIndex * 47) % 360),
                FVector(
                    BoulderScaleZ * (1.15f + 0.08f * static_cast<float>(BoulderIndex % 4)),
                    BoulderScaleZ * (0.76f + 0.07f * static_cast<float>((BoulderIndex + 2) % 5)),
                    BoulderScaleZ),
                BoulderColor,
                BoulderIndex + 42000);
            if (BoulderActor)
            {
                if (UProceduralMeshComponent* BoulderComponent =
                        BoulderActor->FindComponentByClass<UProceduralMeshComponent>())
                {
                    BoulderComponent->SetCastShadow(true);
                    BoulderComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                }
            }
        }
        ++OutResult.DressingBoulderInstanceCount;
    }

    const int32 FoliageClusterCount = bPhysicalCorridor
        ? (bZambeziWoodland ? 5600 : (Spec.bDesertCanyon ? 800 : 12000))
        : (Spec.bDesertCanyon ? 110 : (bRainforest ? 420 : 260));
    for (int32 ClusterIndex = 0; ClusterIndex < FoliageClusterCount; ++ClusterIndex)
    {
        const float T = (static_cast<float>(ClusterIndex) + 0.5f) /
            static_cast<float>(FoliageClusterCount);
        const float Phase = static_cast<float>(ClusterIndex) * 1.3247179f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(-2500.0f, 25400.0f, T) + 230.0f * FMath::Sin(Phase * 0.71f);
        const float BaseOffset = FMath::Lerp(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 260.0f : 180.0f),
            MaxBankOffset,
            FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.47f)), bRainforest ? 0.42f : 0.66f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 8; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float NearCameraMinimumOffset = CandidateX < 2600.0f
                ? ActiveRiverHalfWidth + (bRainforest ? 860.0f : (Spec.bDesertCanyon ? 720.0f : 660.0f))
                : ActiveRiverHalfWidth + 120.0f;
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 210.0f * FMath::Sin(Phase * 0.69f + static_cast<float>(CandidateIndex) * 0.89f),
                NearCameraMinimumOffset,
                MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 500.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float Score = VegetationT *
                    (bRainforest ? 1.85f : (bZambeziWoodland ? 1.22f : (Spec.bDesertCanyon ? 0.58f : 1.34f))) -
                WaterT * 1.18f +
                0.07f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.83f);
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        UStaticMesh* SpeciesMesh = UnderstoryMesh;
        UHierarchicalInstancedStaticMeshComponent* SpeciesInstances = UnderstoryInstances;
        bool bCanopyTree = false;
        float TargetHeightCm = 100.0f;
        const bool bNearEvidenceCamera = !bPhysicalCorridor && BaseX < 3800.0f;
        if (bNearEvidenceCamera && !Spec.bDesertCanyon)
        {
            if (ClusterIndex % 2 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = bRainforest
                    ? 220.0f + 28.0f * static_cast<float>(ClusterIndex % 5)
                    : 185.0f + 24.0f * static_cast<float>(ClusterIndex % 5);
            }
            else
            {
                TargetHeightCm = bRainforest
                    ? 128.0f + 18.0f * static_cast<float>(ClusterIndex % 5)
                    : 104.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bZambeziWoodland)
        {
            const int32 SpeciesSelector = ClusterIndex % 8;
            if (SpeciesSelector <= 4)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 720.0f + 72.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 6)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 190.0f + 28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 96.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (Spec.bDesertCanyon)
        {
            if (ClusterIndex % 3 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 165.0f + 24.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 88.0f + 13.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bRainforest)
        {
            const int32 SpeciesSelector = ClusterIndex % 5;
            if (SpeciesSelector <= 2)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 980.0f + 105.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector == 3)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 260.0f + 38.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 145.0f + 22.0f * static_cast<float>(ClusterIndex % 6);
            }
        }
        else
        {
            const int32 SpeciesSelector = ClusterIndex % (bPhysicalCorridor ? 20 : 5);
            if (bPhysicalCorridor && SpeciesSelector == 0 &&
                ReviewedPineMeshes.Num() == 3 && ReviewedPineInstances.Num() == 3)
            {
                const int32 PineVariant = (ClusterIndex / 20) % ReviewedPineMeshes.Num();
                SpeciesMesh = ReviewedPineMeshes[PineVariant];
                SpeciesInstances = ReviewedPineInstances[PineVariant];
                TargetHeightCm = 1350.0f + 95.0f * static_cast<float>((ClusterIndex / 20) % 6);
                bCanopyTree = true;
            }
            else if (!bPhysicalCorridor && SpeciesSelector == 0)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = 940.0f + 92.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
            else if (SpeciesSelector == (bPhysicalCorridor ? 19 : 4))
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 225.0f + 32.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 690.0f + 68.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
        }

        const float MeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(SpeciesMesh).GetSize().Z);
        const float UniformScale = TargetHeightCm / MeshHeightCm;
        const FVector SpeciesScale(
            UniformScale * (0.88f + 0.04f * static_cast<float>(ClusterIndex % 5)),
            UniformScale * (0.90f + 0.035f * static_cast<float>((ClusterIndex + 2) % 5)),
            UniformScale);
        AddGroundedInstance(
            SpeciesInstances,
            SpeciesMesh,
            FVector2D(BestX, BestY),
            GetLandscapeHeight(BestX, BestY),
            FRotator(
                1.4f * FMath::Sin(Phase * 0.73f),
                static_cast<float>((ClusterIndex * 137) % 360),
                1.2f * FMath::Cos(Phase * 0.61f)),
            SpeciesScale);
        ++OutResult.DressingFoliageInstanceCount;
        if (bCanopyTree)
        {
            ++OutResult.DressingCanopyTreeInstanceCount;
        }
        else
        {
            ++OutResult.DressingUnderstoryInstanceCount;
        }
    }

    OutResult.bDressingValidated =
        OutResult.DressingBoulderInstanceCount == BoulderCount &&
        OutResult.DressingFoliageInstanceCount == FoliageClusterCount &&
        ((Spec.bDesertCanyon && !bZambeziWoodland) ||
         OutResult.DressingCanopyTreeInstanceCount > 0) &&
        OutResult.DressingUnderstoryInstanceCount > 0 &&
        OutResult.bDressingFoliageMaterialsValidated;
    OutSummary += FString::Printf(
        TEXT("Landscape biome dressing for %s: %d %s, %d foliage instances (%d canopy, %d understory), %d river-specific PVE foliage slots; Nanite mesh flags boulder=%d broadleaf=%d conifer=%d understory=%d.\n"),
        *Spec.RiverId,
        OutResult.DressingBoulderInstanceCount,
        ReviewedRockMeshes.Num() == 6
            ? TEXT("rights-reviewed six-variant Nanite rock instances")
            : TEXT("dense irregular procedural boulders"),
        OutResult.DressingFoliageInstanceCount,
        OutResult.DressingCanopyTreeInstanceCount,
        OutResult.DressingUnderstoryInstanceCount,
        OutResult.DressingFoliageMaterialBoundSlotCount,
        OutResult.bDressingBoulderMeshNaniteEnabled,
        OutResult.bDressingBroadleafMeshNaniteEnabled,
        OutResult.bDressingConiferMeshNaniteEnabled,
        OutResult.bDressingUnderstoryMeshNaniteEnabled);
    return OutResult.bDressingValidated;
}
} // namespace RaftSimEditorEnvironment
