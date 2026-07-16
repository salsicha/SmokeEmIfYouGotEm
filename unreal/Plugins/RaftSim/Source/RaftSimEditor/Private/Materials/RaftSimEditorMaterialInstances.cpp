#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
TArray<FRaftSimFirstPartyMaterialInstanceCandidateSpec> GetFirstPartyMaterialInstanceCandidateSpecs()
{
    struct FRecipeSpec
    {
        const TCHAR* RecipeId;
        const TCHAR* RecipeAssetName;
        const TCHAR* ParentMaterialObjectPath;
        int32 AtlasTileIndex;
        float AtlasBlendWeight;
        float NormalIntensity;
        float RoughnessScale;
        float HeightScale;
        FLinearColor PreviewColor;
        float VertexColorWeight;
        float RoughnessFloor;
        float EmissiveFillScale;
        float SpecularLevel;
        FLinearColor SourceConditionedZoneWeights;
        float SourceConditionedMacroAlbedoWeight;
        float SourceConditionedSurfaceResponseWeight;
        float SourceConditionedNormalDetailWeight;
    };

    const FRecipeSpec RecipeSpecs[] = {
        {
            TEXT("terrain_bank_layered_material"),
            TEXT("TerrainBank"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            0,
            0.16f,
            0.22f,
            0.92f,
            0.08f,
            FLinearColor(0.34f, 0.32f, 0.24f),
            1.0f,
            0.72f,
            0.42f,
            0.0f,
            FLinearColor(1.0f, 0.0f, 0.0f, 0.0f),
            0.28f,
            0.22f,
            0.16f,
        },
        {
            TEXT("wet_boulder_contact_material_set"),
            TEXT("WetBoulderContact"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            1,
            0.18f,
            0.30f,
            0.64f,
            0.10f,
            FLinearColor(0.24f, 0.23f, 0.20f),
            1.0f,
            0.66f,
            0.42f,
            0.0f,
            FLinearColor(1.0f, 0.0f, 0.0f, 0.0f),
            0.08f,
            0.10f,
            0.12f,
        },
        {
            TEXT("biome_foliage_groundcover_materials"),
            TEXT("BiomeFoliageGroundcover"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            2,
            0.14f,
            0.18f,
            0.78f,
            0.06f,
            FLinearColor(0.055f, 0.15f, 0.055f),
            0.72f,
            0.68f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 1.0f, 0.0f, 0.0f),
            0.20f,
            0.12f,
            0.08f,
        },
        {
            TEXT("flow_dependent_water_surface_material"),
            TEXT("FlowDependentWaterSurface"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview.M_RaftSim_VertexColorWaterPreview"),
            3,
            0.0f,
            0.32f,
            0.18f,
            0.0f,
            FLinearColor(0.095f, 0.300f, 0.170f),
            1.0f,
            0.28f,
            0.26f,
            0.22f,
            FLinearColor(0.0f, 0.0f, 1.0f, 0.0f),
            0.0f,
            0.0f,
            0.0f,
        },
        {
            TEXT("foam_spray_mist_atmosphere_materials"),
            TEXT("FoamSprayMistAtmosphere"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            4,
            0.10f,
            0.06f,
            0.40f,
            0.015f,
            FLinearColor(0.78f, 0.84f, 0.75f),
            0.0f,
            0.74f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 0.0f, 1.0f, 0.0f),
            0.04f,
            0.04f,
            0.01f,
        },
        {
            TEXT("raft_foreground_review_materials"),
            TEXT("RaftForegroundReview"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            5,
            0.16f,
            0.10f,
            0.56f,
            0.035f,
            FLinearColor(0.680f, 0.220f, 0.080f),
            1.0f,
            0.70f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 0.0f, 0.0f, 0.0f),
            0.0f,
            0.0f,
            0.0f,
        },
    };

    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
        {TEXT("zambezi_batoka_gorge"), TEXT("Zambezi")},
        {TEXT("futaleufu_terminator"), TEXT("Futaleufu")},
        {TEXT("chilko_river_lava_canyon"), TEXT("Chilko")},
    };

    TArray<FRaftSimFirstPartyMaterialInstanceCandidateSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        for (const FRecipeSpec& RecipeSpec : RecipeSpecs)
        {
            FRaftSimFirstPartyMaterialInstanceCandidateSpec Spec;
            Spec.RiverId = RiverSpec.RiverId;
            Spec.RiverAssetName = RiverSpec.RiverAssetName;
            Spec.RecipeId = RecipeSpec.RecipeId;
            Spec.RecipeAssetName = RecipeSpec.RecipeAssetName;
            Spec.ParentMaterialObjectPath = RecipeSpec.ParentMaterialObjectPath;
            Spec.AtlasTileIndex = RecipeSpec.AtlasTileIndex;
            Spec.AtlasBlendWeight = RecipeSpec.AtlasBlendWeight;
            Spec.NormalIntensity = RecipeSpec.NormalIntensity;
            Spec.RoughnessScale = RecipeSpec.RoughnessScale;
            Spec.HeightScale = RecipeSpec.HeightScale;
            Spec.PreviewColor = RecipeSpec.PreviewColor;
            Spec.VertexColorWeight = RecipeSpec.VertexColorWeight;
            Spec.RoughnessFloor = RecipeSpec.RoughnessFloor;
            Spec.EmissiveFillScale = RecipeSpec.EmissiveFillScale;
            Spec.SpecularLevel = RecipeSpec.SpecularLevel;
            Spec.SourceConditionedZoneWeights = RecipeSpec.SourceConditionedZoneWeights;
            Spec.SourceConditionedMacroAlbedoWeight = RecipeSpec.SourceConditionedMacroAlbedoWeight;
            Spec.SourceConditionedSurfaceResponseWeight = RecipeSpec.SourceConditionedSurfaceResponseWeight;
            Spec.SourceConditionedNormalDetailWeight = RecipeSpec.SourceConditionedNormalDetailWeight;
            if (FCString::Strcmp(RecipeSpec.RecipeId, TEXT("terrain_bank_layered_material")) == 0)
            {
                if (FCString::Strcmp(RiverSpec.RiverId, TEXT("colorado_river")) == 0)
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(4.5f, 4.5f, 0.41f, 0.13f);
                    Spec.TerrainDetailAlbedoWeight = 0.76f;
                    Spec.TerrainDetailNormalWeight = 0.22f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.24f;
                }
                else if (FCString::Strcmp(RiverSpec.RiverId, TEXT("pacuare")) == 0)
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(5.0f, 5.0f, 0.29f, 0.47f);
                    Spec.TerrainDetailAlbedoWeight = 0.74f;
                    Spec.TerrainDetailNormalWeight = 0.18f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.20f;
                }
                else
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(5.0f, 5.0f, 0.17f, 0.31f);
                    Spec.TerrainDetailAlbedoWeight = 0.74f;
                    Spec.TerrainDetailNormalWeight = 0.20f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.22f;
                }
            }
            else if (FCString::Strcmp(RecipeSpec.RecipeId, TEXT("flow_dependent_water_surface_material")) == 0)
            {
                const FRaftSimPreviewWaterMaterialResponse WaterResponse =
                    GetPreviewWaterMaterialResponse(RiverSpec.RiverId);
                Spec.RoughnessScale = WaterResponse.RoughnessScale;
                Spec.RoughnessFloor = WaterResponse.RoughnessFloor;
                Spec.EmissiveFillScale = WaterResponse.EmissiveFillScale;
                Spec.SpecularLevel = WaterResponse.SpecularLevel;
                Spec.NormalIntensity = WaterResponse.NormalIntensity;
            }
            Specs.Add(Spec);
        }
    }

    return Specs;
}

bool CreateOrUpdateFirstPartyMaterialInstanceCandidateAsset(
    const FRaftSimFirstPartyMaterialInstanceCandidateSpec& Spec,
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary)
{
    UMaterialInterface* ParentMaterial = LoadPreviewMaterial(*Spec.ParentMaterialObjectPath);
    if (!ParentMaterial)
    {
        OutSummary += FString::Printf(
            TEXT("Missing parent material for candidate %s: %s\n"),
            *Spec.GetMaterialInstancePath(),
            *Spec.ParentMaterialObjectPath);
        return false;
    }

    const FString PackagePath = Spec.GetMaterialInstancePath();
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);

    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create material instance package %s\n"), *PackagePath);
        return false;
    }

    UMaterialInstanceConstant* Instance =
        Cast<UMaterialInstanceConstant>(StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Instance);
    }
    if (!Instance)
    {
        OutSummary += FString::Printf(TEXT("Failed to create material instance candidate %s\n"), *ObjectPath);
        return false;
    }

    const int32 AtlasColumn = Spec.AtlasTileIndex % 3;
    const int32 AtlasRow = Spec.AtlasTileIndex / 3;
    const FLinearColor AtlasTileOriginScale(
        static_cast<float>(AtlasColumn) / 3.0f,
        static_cast<float>(AtlasRow) / 2.0f,
        1.0f / 3.0f,
        1.0f / 2.0f);

    Instance->Modify();
    Instance->SetParentEditorOnly(ParentMaterial);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileOriginScale")),
        AtlasTileOriginScale);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileOrigin")),
        FLinearColor(AtlasTileOriginScale.R, AtlasTileOriginScale.G, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileScale")),
        FLinearColor(AtlasTileOriginScale.B, AtlasTileOriginScale.A, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("PreviewColor")),
        Spec.PreviewColor);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedZoneWeights")),
        Spec.SourceConditionedZoneWeights);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvScaleOffset")),
        Spec.TerrainDetailUvScaleOffset);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvScale")),
        FLinearColor(Spec.TerrainDetailUvScaleOffset.R, Spec.TerrainDetailUvScaleOffset.G, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvOffset")),
        FLinearColor(Spec.TerrainDetailUvScaleOffset.B, Spec.TerrainDetailUvScaleOffset.A, 0.0f, 0.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileIndex")),
        static_cast<float>(Spec.AtlasTileIndex));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasBlendWeight")),
        Spec.AtlasBlendWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("NormalIntensity")),
        Spec.NormalIntensity);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RoughnessScale")),
        Spec.RoughnessScale);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RoughnessFloor")),
        Spec.RoughnessFloor);
    if (Spec.RecipeId == TEXT("flow_dependent_water_surface_material"))
    {
        Instance->SetScalarParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("EmissiveFillScale")),
            Spec.EmissiveFillScale);
        Instance->SetScalarParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("SpecularLevel")),
            Spec.SpecularLevel);
    }
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HeightScale")),
        Spec.HeightScale);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VertexColorWeight")),
        Spec.VertexColorWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ReviewAssetOnlyNotLifelike")),
        1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedMacroAlbedoWeight")),
        Spec.SourceConditionedMacroAlbedoWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedSurfaceResponseWeight")),
        Spec.SourceConditionedSurfaceResponseWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedNormalDetailWeight")),
        Spec.SourceConditionedNormalDetailWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailAlbedoWeight")),
        Spec.TerrainDetailAlbedoWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailNormalWeight")),
        Spec.TerrainDetailNormalWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailSurfaceResponseWeight")),
        Spec.TerrainDetailSurfaceResponseWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedMaterialAssignmentReviewOnlyNotLifelike")),
        1.0f);

    bool bAllTexturesBound = true;
    auto BindTextureParameter = [&TextureAssetsByKey, &Spec, &Instance, &OutSummary, &bAllTexturesBound](
                                    const TCHAR* ParameterName,
                                    const TCHAR* MapKey)
    {
        UTexture2D* const* Texture = TextureAssetsByKey.Find(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, MapKey));
        if (!Texture || !*Texture)
        {
            OutSummary += FString::Printf(
                TEXT("Missing first-party material texture asset for %s parameter %s (%s/%s)\n"),
                *Spec.GetMaterialInstancePath(),
                ParameterName,
                *Spec.RiverId,
                MapKey);
            bAllTexturesBound = false;
            return;
        }

        Instance->SetTextureParameterValueEditorOnly(FMaterialParameterInfo(FName(ParameterName)), *Texture);
    };

    BindTextureParameter(TEXT("AlbedoAtlas"), TEXT("AlbedoAtlas"));
    BindTextureParameter(TEXT("NormalAtlas"), TEXT("NormalAtlas"));
    BindTextureParameter(TEXT("AORoughnessHeightAtlas"), TEXT("AORoughnessHeightAtlas"));
    BindTextureParameter(TEXT("SourceConditionedMacroAlbedo"), TEXT("SourceConditionedMacroAlbedo"));
    BindTextureParameter(TEXT("SourceConditionedMaterialZones"), TEXT("SourceConditionedMaterialZones"));
    BindTextureParameter(TEXT("SourceConditionedAORoughnessHeight"), TEXT("SourceConditionedAORoughnessHeight"));
    BindTextureParameter(TEXT("SourceConditionedNormalDetail"), TEXT("SourceConditionedNormalDetail"));
    BindTextureParameter(TEXT("TerrainDetailAlbedo"), TEXT("TerrainDetailAlbedo"));
    BindTextureParameter(TEXT("TerrainDetailNormal"), TEXT("TerrainDetailNormal"));
    BindTextureParameter(TEXT("TerrainDetailAORoughnessHeight"), TEXT("TerrainDetailAORoughnessHeight"));
    if (!bAllTexturesBound)
    {
        return false;
    }

    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    const bool bSaved = UPackage::SavePackage(Package, Instance, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party material instance review asset %s (%s/%s) -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *ObjectPath,
        *Spec.RiverId,
        *Spec.RecipeId,
        *Filename);
    return bSaved;
}

bool CreateFirstPartyMaterialInstanceCandidateAssets(FString& OutSummary)
{
    bool bAllSaved = true;
    TMap<FString, UTexture2D*> TextureAssetsByKey;
    LoadOrCreatePreviewColorMaterial();
    LoadOrCreatePreviewTerrainVertexColorMaterial();
    LoadOrCreatePreviewTranslucentColorMaterial();
    LoadOrCreatePreviewWaterVertexColorMaterial();
    bAllSaved &= CreateFirstPartyMaterialTextureAtlasAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= CreateSourceConditionedMaterialTextureAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= CreateProductionDetailMaterialTextureAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= LoadOrCreateFirstPartyAtlasSampleReviewMaterial(TextureAssetsByKey, OutSummary) != nullptr;

    for (const FRaftSimFirstPartyMaterialInstanceCandidateSpec& Spec : GetFirstPartyMaterialInstanceCandidateSpecs())
    {
        bAllSaved &= CreateOrUpdateFirstPartyMaterialInstanceCandidateAsset(Spec, TextureAssetsByKey, OutSummary);
    }

    return bAllSaved;
}

FString GetFirstPartyMaterialRiverAssetName(const FString& RiverId)
{
    if (RiverId == TEXT("american_south_fork"))
    {
        return TEXT("AmericanSouthFork");
    }
    if (RiverId == TEXT("colorado_river"))
    {
        return TEXT("ColoradoRiver");
    }
    if (RiverId == TEXT("pacuare"))
    {
        return TEXT("Pacuare");
    }
    if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        return TEXT("Zambezi");
    }
    if (RiverId == TEXT("futaleufu_terminator"))
    {
        return TEXT("Futaleufu");
    }
    if (RiverId == TEXT("chilko_river_lava_canyon"))
    {
        return TEXT("Chilko");
    }

    return FString();
}

UMaterialInterface* LoadFirstPartyMaterialInstanceCandidate(const FString& RiverId, const TCHAR* RecipeAssetName)
{
    const FString RiverAssetName = GetFirstPartyMaterialRiverAssetName(RiverId);
    if (RiverAssetName.IsEmpty())
    {
        return nullptr;
    }

    const FString MaterialPath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/MaterialInstances/MI_RaftSim_%s_%s_AtlasCandidate.MI_RaftSim_%s_%s_AtlasCandidate"),
        *RiverAssetName,
        RecipeAssetName,
        *RiverAssetName,
        RecipeAssetName);
    return LoadPreviewMaterial(*MaterialPath);
}

                                              
 
                                              
                                                    
                                                          
                                                            
                                                       

                                                  
     
                                                                                                                                
     
  

FRaftSimFirstPartyMaterialAssignmentSet LoadFirstPartyMaterialAssignmentSetForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    FString& OutSummary)
{
    FRaftSimFirstPartyMaterialAssignmentSet Assignments;
    Assignments.TerrainBank = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("TerrainBank"));
    Assignments.WetBoulderContact = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("WetBoulderContact"));
    Assignments.BiomeFoliageGroundcover =
        LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("BiomeFoliageGroundcover"));
    Assignments.FlowDependentWaterSurface =
        LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("FlowDependentWaterSurface"));
    Assignments.RaftForegroundReview = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("RaftForegroundReview"));

    OutSummary += FString::Printf(
        TEXT("%s review material-instance scene assignment set for %s.\n"),
        Assignments.IsCompleteForDurableSurfaceReview() ? TEXT("Loaded") : TEXT("Incomplete"),
        *Spec.RiverId);
    return Assignments;
}

UMaterialInterface* SelectFirstPartyMaterialForPreviewActor(
    const FString& ActorLabel,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments)
{
    if (ActorLabel.StartsWith(TEXT("RaftSim_ProceduralValleyTerrain_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_SourceAerialDrapeMicroTile_")))
    {
        return nullptr;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_ProceduralRiverRibbon_")))
    {
        return Assignments.FlowDependentWaterSurface;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareBoulder_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_BoulderSurfaceVariation_")))
    {
        return Assignments.WetBoulderContact;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareFoliage_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FoliageTrunk_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FoliageCanopy_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_ProceduralLeafClusterSupplement_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_OrganicCanopyLeafSpray_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_OrganicBranchFrondSupplement_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FineTwigCanopyLace_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareUnderstory_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_Understory_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_CanyonScrub_")))
    {
        return Assignments.BiomeFoliageGroundcover;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_ForegroundRaft_")))
    {
        return Assignments.RaftForegroundReview;
    }

    return nullptr;
}

int32 AssignFirstPartyMaterialInstancesToPreviewScene(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments,
    FString& OutSummary)
{
    if (!World)
    {
        return 0;
    }

    int32 AssignedComponentCount = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor)
        {
            continue;
        }

        UMaterialInterface* Material = SelectFirstPartyMaterialForPreviewActor(Actor->GetActorLabel(), Assignments);
        if (!Material)
        {
            continue;
        }

        TArray<UMeshComponent*> MeshComponents;
        Actor->GetComponents<UMeshComponent>(MeshComponents);
        for (UMeshComponent* MeshComponent : MeshComponents)
        {
            if (!MeshComponent)
            {
                continue;
            }

            const int32 MaterialCount = FMath::Max(1, MeshComponent->GetNumMaterials());
            for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
            {
                MeshComponent->SetMaterial(MaterialIndex, Material);
            }
            ++AssignedComponentCount;
        }
    }

    OutSummary += FString::Printf(
        TEXT("Assigned %d review material-instance surface components in %s (%s).\n"),
        AssignedComponentCount,
        *Spec.RiverId,
        *GetFirstPartyMaterialInstanceSceneAssignmentStatus());
    return AssignedComponentCount;
}
} // namespace RaftSimEditorEnvironment
