#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "ContentStreaming.h"
#include "RaftSimRiverWaterConfig.h"
#include "StaticMeshResources.h"
#include "WorldPartition/HLOD/HLODActor.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR CaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach");
constexpr TCHAR PhotographicCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic");
constexpr TCHAR VolumetricBroadleafCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v169_broadleaf");
constexpr TCHAR SourceHlodExclusiveCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v180_source_hlod_exclusive");
constexpr TCHAR SolverDerivedAerationCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v181_solver_derived_aeration");
constexpr TCHAR SolverGatedBreakingReliefCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v182_solver_gated_breaking_relief");
constexpr TCHAR GuideFeatureBreakingReliefCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v183_guide_feature_breaking_relief");
constexpr TCHAR RefinedGuideFeatureFoamCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v184_refined_guide_feature_foam");
constexpr TCHAR TerrainDetailV2ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v189_riverbank_detail_v2");
constexpr TCHAR PolyHavenShoreRockReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v190_scan_rock_bank_morphology");
constexpr TCHAR EmbeddedBankRockReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v194_dense_embedded_bank_rock_fabric");
constexpr TCHAR DerivedBankMorphologyReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v198_erosion_deposition_bank_modules");
constexpr TCHAR ScannedBankKitReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v199_scanned_bank_kit");
constexpr TCHAR MeatGrinderHeroReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v202_meat_grinder_dem_aligned_rock_garden");
constexpr TCHAR RiverSmallRocksReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v205_meat_grinder_river_small_rocks_exposed");
constexpr TCHAR DisplacedGravelBarReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v207_meat_grinder_displaced_gravel_bar_corrected");
constexpr TCHAR LiveOakBranchAtlasV2ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v208_live_oak_branch_atlas_v2");
constexpr TCHAR LiveOakBranchAtlasV2ExpandedReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v209_live_oak_branch_atlas_v2_expanded");
constexpr TCHAR LiveOakWoodyCanopyV1ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v210_live_oak_true_woody_v1");
constexpr TCHAR LiveOakDenseWoodyV2ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v211_live_oak_dense_woody_v2");
constexpr TCHAR LiveOakCrownFamilyV3ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v212_live_oak_crown_family_v3");
constexpr TCHAR LiveOakIslandTreeMorphologyReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v213_live_oak_cc0_island_tree_morphology");
constexpr TCHAR LiveOakIslandTreeMaterialV1ReviewCaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach/photographic_v214_live_oak_cc0_island_tree_material_v1");

FString AbsoluteCapturePath(const FString& RelativePath)
{
    return FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), RelativePath));
}

float SouthForkBankRockReviewUnitRandom(
    const FVector& WorldLocation,
    int32 InstanceIndex,
    int32 Salt)
{
    const int32 QuantizedX = FMath::RoundToInt(WorldLocation.X * 0.01f);
    const int32 QuantizedY = FMath::RoundToInt(WorldLocation.Y * 0.01f);
    uint32 Hash = static_cast<uint32>(QuantizedX) * 0x9E3779B9u;
    Hash ^= static_cast<uint32>(QuantizedY) * 0x85EBCA6Bu;
    Hash ^= static_cast<uint32>(InstanceIndex) * 0xC2B2AE35u;
    Hash ^= static_cast<uint32>(Salt) * 0x27D4EB2Fu;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

}

bool ConfigureSouthForkTerrainDetailV2Review(
    UWorld* World,
    TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>&
        OutMaterialStates,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("South Fork terrain-detail v2 review has no loaded world.\n");
        return false;
    }

    const bool bRiverSmallRocksReview = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimRiverSmallRocksReview"));

    struct FReviewTextureSpec
    {
        const TCHAR* MapKey;
        const TCHAR* MapKind;
        const TCHAR* SourceRelativePath;
        TextureCompressionSettings CompressionSettings;
        bool bSRGB;
        TextureGroup LODGroup;
    };
    const FReviewTextureSpec TextureSpecs[] = {
        {
            TEXT("Albedo"), TEXT("terrain_detail_v2_review_albedo"),
            TEXT("unreal/Content/RaftSim/Rendering/ReviewTerrainTextures/"
                 "SouthForkDetailV2/american_south_fork_terrain_bank_detail_v2_albedo.png"),
            TC_Default, true, TEXTUREGROUP_World,
        },
        {
            TEXT("Normal"), TEXT("terrain_detail_v2_review_normal"),
            TEXT("unreal/Content/RaftSim/Rendering/ReviewTerrainTextures/"
                 "SouthForkDetailV2/american_south_fork_terrain_bank_detail_v2_normal.png"),
            TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap,
        },
        {
            TEXT("Packed"), TEXT("terrain_detail_v2_review_ao_roughness_height"),
            TEXT("unreal/Content/RaftSim/Rendering/ReviewTerrainTextures/"
                 "SouthForkDetailV2/american_south_fork_terrain_bank_detail_v2_ao_roughness_height.png"),
            TC_Masks, false, TEXTUREGROUP_World,
        },
    };

    TMap<FString, UTexture2D*> ReviewTextures;
    if (bRiverSmallRocksReview)
    {
        const TCHAR* ObjectPaths[] = {
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "RiverSmallRocks_2K/T_RiverSmallRocks_BaseColor_2K."
                 "T_RiverSmallRocks_BaseColor_2K"),
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "RiverSmallRocks_2K/T_RiverSmallRocks_NormalGL_2K."
                 "T_RiverSmallRocks_NormalGL_2K"),
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "RiverSmallRocks_2K/T_RiverSmallRocks_ARM_2K."
                 "T_RiverSmallRocks_ARM_2K")};
        const TCHAR* MapKeys[] = {TEXT("Albedo"), TEXT("Normal"), TEXT("Packed")};
        for (int32 TextureIndex = 0;
             TextureIndex < UE_ARRAY_COUNT(ObjectPaths);
             ++TextureIndex)
        {
            UTexture2D* Texture = LoadObject<UTexture2D>(
                nullptr, ObjectPaths[TextureIndex]);
            if (!Texture)
            {
                OutSummary += FString::Printf(
                    TEXT("River Small Rocks review texture is missing: %s.\n"),
                    ObjectPaths[TextureIndex]);
                return false;
            }
            const int32 SourceSizeX = Texture->Source.GetSizeX();
            const int32 SourceSizeY = Texture->Source.GetSizeY();
            if (SourceSizeX != 2048 || SourceSizeY != 2048)
            {
                OutSummary += FString::Printf(
                    TEXT("River Small Rocks review texture has invalid source "
                         "dimensions %dx%d (expected 2048x2048): %s.\n"),
                    SourceSizeX,
                    SourceSizeY,
                    ObjectPaths[TextureIndex]);
                return false;
            }
            Texture->SetForceMipLevelsToBeResident(120.0f);
            ReviewTextures.Add(MapKeys[TextureIndex], Texture);
        }
    }
    else
    {
        for (const FReviewTextureSpec& SourceSpec : TextureSpecs)
        {
            FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
            Spec.RiverId = TEXT("american_south_fork_detail_v2_review");
            Spec.RiverAssetName = TEXT("SouthForkTerrainDetailV2Review");
            Spec.MapKey = SourceSpec.MapKey;
            Spec.MapKind = SourceSpec.MapKind;
            Spec.SourceRelativePath = SourceSpec.SourceRelativePath;
            Spec.TextureAssetRootPackagePath =
                TEXT("/Game/RaftSim/Rendering/ReviewTerrainTextures/"
                     "SouthForkDetailV2/Textures");
            Spec.CompressionSettings = SourceSpec.CompressionSettings;
            Spec.bSRGB = SourceSpec.bSRGB;
            Spec.LODGroup = SourceSpec.LODGroup;
            bool bSaved = false;
            UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
                Spec, OutSummary, bSaved);
            if (!Texture || !bSaved ||
                !RebuildAndValidateFirstPartyTexturePlatformData(
                    Texture, Spec, OutSummary))
            {
                OutSummary += FString::Printf(
                    TEXT("Failed to create South Fork terrain-detail v2 review %s.\n"),
                    SourceSpec.MapKey);
                return false;
            }
            Texture->SetForceMipLevelsToBeResident(120.0f);
            ReviewTextures.Add(SourceSpec.MapKey, Texture);
        }
    }
    FlushRenderingCommands();

    UTexture2D* Albedo = ReviewTextures.FindRef(TEXT("Albedo"));
    UTexture2D* Normal = ReviewTextures.FindRef(TEXT("Normal"));
    UTexture2D* Packed = ReviewTextures.FindRef(TEXT("Packed"));
    if (!Albedo || !Normal || !Packed)
    {
        OutSummary += TEXT("South Fork terrain-detail v2 review textures are incomplete.\n");
        return false;
    }

    int32 OverriddenComponentCount = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Actor = *It;
        if (!Actor || !Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")))
        {
            continue;
        }
        UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
        UMaterialInterface* OriginalMaterial = Component
            ? Component->GetMaterial(0)
            : nullptr;
        UMaterialInstanceDynamic* ReviewMaterial = OriginalMaterial
            ? UMaterialInstanceDynamic::Create(OriginalMaterial, Component)
            : nullptr;
        if (!Component || !OriginalMaterial || !ReviewMaterial)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to override terrain-detail v2 on %s.\n"),
                Actor ? *Actor->GetActorLabel() : TEXT("missing actor"));
            RestoreSouthForkTerrainDetailV2Review(OutMaterialStates);
            return false;
        }
        OutMaterialStates.Emplace(Component, OriginalMaterial);
        ReviewMaterial->SetTextureParameterValue(TEXT("GroundAlbedo"), Albedo);
        ReviewMaterial->SetTextureParameterValue(TEXT("GroundNormal"), Normal);
        ReviewMaterial->SetTextureParameterValue(TEXT("GroundPacked"), Packed);
        if (bRiverSmallRocksReview)
        {
            // v204 proved the scan was almost completely hidden by the
            // production aerial macro (0.03-0.58 mean RGB levels of change in
            // the fixed views). Expose enough of the rights-reviewed 2.9 m
            // surface to judge it honestly while keeping this override
            // transient and outside every saved material or map package.
            ReviewMaterial->SetScalarParameterValue(
                TEXT("SourceMacroInfluence"), 0.30f);
            ReviewMaterial->SetScalarParameterValue(
                TEXT("UseCorridorEdgeBlend"), 0.0f);
        }
        Component->SetMaterial(0, ReviewMaterial);
        ++OverriddenComponentCount;
    }
    if (OverriddenComponentCount != 13)
    {
        OutSummary += FString::Printf(
            TEXT("South Fork terrain-detail v2 review expected 13 detailed terrain "
                 "components but found %d.\n"),
            OverriddenComponentCount);
        RestoreSouthForkTerrainDetailV2Review(OutMaterialStates);
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Transiently bound %s to %d detailed terrain components; no map or "
             "material package was changed.\n"),
        bRiverSmallRocksReview
            ? TEXT("rights-reviewed 2.9 m Poly Haven River Small Rocks textures")
            : TEXT("South Fork terrain-detail v2 review textures"),
        OverriddenComponentCount);
    return true;
}

void RestoreSouthForkTerrainDetailV2Review(
    const TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>&
        MaterialStates)
{
    for (const TPair<TWeakObjectPtr<UStaticMeshComponent>,
                     TWeakObjectPtr<UMaterialInterface>>& Pair : MaterialStates)
    {
        if (Pair.Key.IsValid())
        {
            Pair.Key->SetMaterial(0, Pair.Value.Get());
        }
    }
}

bool ConfigureSouthForkPolyHavenShoreRockReview(
    UWorld* World,
    TArray<FSouthForkShoreRockReviewComponentState>& OutStates,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("South Fork scan-rock bank review has no loaded world.\n");
        return false;
    }
    UStaticMesh* ReviewMeshes[6] = {};
    for (int32 MeshIndex = 0; MeshIndex < 6; ++MeshIndex)
    {
        const FString AssetName = FString::Printf(
            TEXT("SM_RockMossSet01_rock_moss_set_01_rock%02d"), MeshIndex + 1);
        const FString ObjectPath = FString::Printf(
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "RockMossSet01_1K/%s.%s"),
            *AssetName, *AssetName);
        ReviewMeshes[MeshIndex] = LoadObject<UStaticMesh>(nullptr, *ObjectPath);
        if (!ReviewMeshes[MeshIndex])
        {
            OutSummary += FString::Printf(
                TEXT("Missing Poly Haven scan-rock review mesh %s.\n"),
                *ObjectPath);
            return false;
        }
    }

    const bool bEmbeddedBankRockReview = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimEmbeddedBankRockReview"));
    int32 ScenicRockComponentCount = 0;
    int32 ShoreCobbleComponentCount = 0;
    int32 ShoreCobbleInstanceCount = 0;
    int32 VisibleEmbeddedRockCount = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        TInlineComponentArray<UHierarchicalInstancedStaticMeshComponent*> Components(*It);
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (!Component)
            {
                continue;
            }
            const FString Name = Component->GetName();
            int32 ReviewMeshIndex = INDEX_NONE;
            if (Name.StartsWith(TEXT("ScenicBankRock")) && Name.Len() >= 2)
            {
                ReviewMeshIndex = FCString::Atoi(*Name.Right(2)) - 1;
                ++ScenicRockComponentCount;
            }
            else if (Name.StartsWith(TEXT("ShoreCobble")) && !Name.IsEmpty())
            {
                ReviewMeshIndex = static_cast<int32>(Name[Name.Len() - 1] - TCHAR('A'));
                ++ShoreCobbleComponentCount;
            }
            if (ReviewMeshIndex < 0 || ReviewMeshIndex >= 6 ||
                !ReviewMeshes[ReviewMeshIndex])
            {
                if (ReviewMeshIndex != INDEX_NONE)
                {
                    RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                    OutSummary += FString::Printf(
                        TEXT("Invalid scan-rock review component mapping for %s.\n"),
                        *Name);
                    return false;
                }
                continue;
            }
            FSouthForkShoreRockReviewComponentState& State =
                OutStates.Emplace_GetRef();
            State.Component = Component;
            State.OriginalMesh = Component->GetStaticMesh();
            State.OriginalOverrideMaterials.Reserve(
                Component->OverrideMaterials.Num());
            for (UMaterialInterface* OriginalOverride :
                 Component->OverrideMaterials)
            {
                State.OriginalOverrideMaterials.Add(OriginalOverride);
            }
            TArray<FTransform> ReviewTransforms;
            const bool bIsShoreCobble = Name.StartsWith(TEXT("ShoreCobble"));
            if (bEmbeddedBankRockReview && bIsShoreCobble)
            {
                const int32 InstanceCount = Component->GetInstanceCount();
                ShoreCobbleInstanceCount += InstanceCount;
                State.OriginalWorldTransforms.Reserve(InstanceCount);
                ReviewTransforms.Reserve(InstanceCount);
                FBox EffectiveDonorBounds =
                    ReviewMeshes[ReviewMeshIndex]->GetBoundingBox();
                if (EffectiveDonorBounds.GetSize().Z < 100.0f &&
                    ReviewMeshes[ReviewMeshIndex]->GetNumSourceModels() > 0)
                {
                    const FVector BuildScale =
                        ReviewMeshes[ReviewMeshIndex]->GetSourceModel(0)
                            .BuildSettings.BuildScale3D;
                    EffectiveDonorBounds = FBox(
                        EffectiveDonorBounds.Min * BuildScale,
                        EffectiveDonorBounds.Max * BuildScale);
                }
                const FVector EffectiveDonorSizeCm =
                    EffectiveDonorBounds.GetSize();
                const float EffectiveDonorLongestCm = FMath::Max3(
                    EffectiveDonorSizeCm.X,
                    EffectiveDonorSizeCm.Y,
                    EffectiveDonorSizeCm.Z);
                if (EffectiveDonorLongestCm <= UE_KINDA_SMALL_NUMBER ||
                    EffectiveDonorBounds.Min.Z >= 0.0f)
                {
                    RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                    OutSummary += FString::Printf(
                        TEXT("Invalid effective scan-rock donor bounds for %s.\n"),
                        *Name);
                    return false;
                }
                for (int32 InstanceIndex = 0;
                     InstanceIndex < InstanceCount;
                     ++InstanceIndex)
                {
                    FTransform OriginalWorldTransform;
                    if (!Component->GetInstanceTransform(
                            InstanceIndex, OriginalWorldTransform,
                            /*bWorldSpace=*/true))
                    {
                        RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                        OutSummary += FString::Printf(
                            TEXT("Could not read scan-rock review transform %s[%d].\n"),
                            *Name, InstanceIndex);
                        return false;
                    }
                    State.OriginalWorldTransforms.Add(OriginalWorldTransform);
                    FTransform ReviewTransform = OriginalWorldTransform;
                    const FVector Location = OriginalWorldTransform.GetLocation();
                    const float WorldXMetres = Location.X * 0.01f;
                    const float WorldYMetres = Location.Y * 0.01f;
                    const float MacroPatch = FMath::Clamp(
                        0.50f +
                        0.27f * FMath::Sin(
                            WorldXMetres * 0.021f + WorldYMetres * 0.013f) +
                        0.18f * FMath::Sin(
                            WorldXMetres * 0.009f - WorldYMetres * 0.026f +
                            ReviewMeshIndex * 0.71f),
                        0.0f, 1.0f);
                    const float PatchWeight = FMath::SmoothStep(
                        0.28f, 0.86f, MacroPatch);
                    const float KeepProbability = FMath::Lerp(
                        0.48f, 0.96f, PatchWeight * PatchWeight);
                    const float Selection = SouthForkBankRockReviewUnitRandom(
                        Location, InstanceIndex, 401 + ReviewMeshIndex * 17);
                    if (Selection > KeepProbability)
                    {
                        ReviewTransform.SetScale3D(FVector(0.001f));
                    }
                    else
                    {
                        const float SizeRandom =
                            SouthForkBankRockReviewUnitRandom(
                                Location, InstanceIndex,
                                433 + ReviewMeshIndex * 19);
                        const float TargetLongestCm = FMath::Lerp(
                            25.0f, 190.0f,
                            FMath::Pow(SizeRandom, 1.65f));
                        const float UniformScale =
                            TargetLongestCm / EffectiveDonorLongestCm;
                        const float AspectX = FMath::Lerp(
                            0.82f, 1.24f,
                            SouthForkBankRockReviewUnitRandom(
                                Location, InstanceIndex, 457));
                        const float AspectY = FMath::Lerp(
                            0.84f, 1.20f,
                            SouthForkBankRockReviewUnitRandom(
                                Location, InstanceIndex, 461));
                        const float AspectZ = FMath::Lerp(
                            0.52f, 0.82f,
                            SouthForkBankRockReviewUnitRandom(
                                Location, InstanceIndex, 463));
                        ReviewTransform.SetScale3D(FVector(
                            UniformScale * AspectX,
                            UniformScale * AspectY,
                            UniformScale * AspectZ));
                        FVector EmbeddedLocation = Location;
                        const float EffectiveHeightCm =
                            EffectiveDonorSizeCm.Z *
                            ReviewTransform.GetScale3D().Z;
                        const float BaseOffsetCm =
                            -EffectiveDonorBounds.Min.Z *
                            ReviewTransform.GetScale3D().Z;
                        EmbeddedLocation.Z += BaseOffsetCm;
                        EmbeddedLocation.Z -= EffectiveHeightCm * FMath::Lerp(
                            0.10f, 0.24f,
                            SouthForkBankRockReviewUnitRandom(
                                Location, InstanceIndex, 467));
                        ReviewTransform.SetLocation(EmbeddedLocation);
                        ++VisibleEmbeddedRockCount;
                    }
                    ReviewTransforms.Add(ReviewTransform);
                }
            }
            Component->SetStaticMesh(ReviewMeshes[ReviewMeshIndex]);
            if (ReviewTransforms.Num() > 0 &&
                !Component->BatchUpdateInstancesTransforms(
                    0, ReviewTransforms,
                    /*bWorldSpace=*/true,
                    /*bMarkRenderStateDirty=*/true,
                    /*bTeleport=*/true))
            {
                RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                OutSummary += FString::Printf(
                    TEXT("Could not apply clustered embedded-rock transforms to %s.\n"),
                    *Name);
                return false;
            }
        }
    }
    if (ScenicRockComponentCount != 78 || ShoreCobbleComponentCount != 39)
    {
        RestoreSouthForkPolyHavenShoreRockReview(OutStates);
        OutSummary += FString::Printf(
            TEXT("South Fork scan-rock review expected 78 scenic-rock and 39 "
                 "shore-cobble components but found %d and %d.\n"),
            ScenicRockComponentCount, ShoreCobbleComponentCount);
        return false;
    }
    if (bEmbeddedBankRockReview &&
        (ShoreCobbleInstanceCount != 15702 ||
         VisibleEmbeddedRockCount < 8000 ||
         VisibleEmbeddedRockCount > 15500))
    {
        RestoreSouthForkPolyHavenShoreRockReview(OutStates);
        OutSummary += FString::Printf(
            TEXT("Dense embedded-rock review expected 15,702 shore candidates "
                 "and 8,000-15,500 visible instances but found %d and %d.\n"),
            ShoreCobbleInstanceCount, VisibleEmbeddedRockCount);
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Transiently assigned six rights-reviewed CC0 scan-rock morphology "
             "donors to %d non-colliding scenic-rock and %d non-colliding "
             "shore-cobble components; no map or mesh package was changed.\n"),
        ScenicRockComponentCount, ShoreCobbleComponentCount);
    if (bEmbeddedBankRockReview)
    {
        OutSummary += FString::Printf(
            TEXT("Transiently retained %d of %d shore candidates as a dense embedded "
                 "0.25-1.90 m scan-rock fabric with LOD0 build-scale and base-pivot correction; "
                 "collision, hydraulics, navigation, "
                 "map packages, and mesh packages remain unchanged.\n"),
            VisibleEmbeddedRockCount, ShoreCobbleInstanceCount);
    }
    return true;
}

void RestoreSouthForkPolyHavenShoreRockReview(
    const TArray<FSouthForkShoreRockReviewComponentState>& States)
{
    for (const FSouthForkShoreRockReviewComponentState& State : States)
    {
        if (State.Component.IsValid())
        {
            if (State.OriginalWorldTransforms.Num() > 0)
            {
                State.Component->BatchUpdateInstancesTransforms(
                    0, State.OriginalWorldTransforms,
                    /*bWorldSpace=*/true,
                    /*bMarkRenderStateDirty=*/true,
                    /*bTeleport=*/true);
            }
            State.Component->SetStaticMesh(State.OriginalMesh.Get());
            State.Component->EmptyOverrideMaterials();
            for (int32 MaterialIndex = 0;
                 MaterialIndex < State.OriginalOverrideMaterials.Num();
                 ++MaterialIndex)
            {
                State.Component->SetMaterial(
                    MaterialIndex,
                    State.OriginalOverrideMaterials[MaterialIndex].Get());
            }
        }
    }
}

bool ConfigureSouthForkLiveOakBranchAtlasV2Review(
    UWorld* World,
    bool bTrueWoodyV1Review,
    bool bDenseWoodyV2Review,
    bool bCrownFamilyV3Review,
    bool bIslandTreeMorphologyReview,
    bool bIslandTreeMaterialV1Review,
    TArray<FSouthForkShoreRockReviewComponentState>& OutStates,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("Live-oak review has no loaded world.\n");
        return false;
    }
    if (bIslandTreeMorphologyReview && bIslandTreeMaterialV1Review)
    {
        OutSummary += TEXT(
            "Select only one island-tree review material baseline per capture.\n");
        return false;
    }
    const bool bAnyIslandTreeReview =
        bIslandTreeMorphologyReview || bIslandTreeMaterialV1Review;
    const TCHAR* ReviewMeshObjectPath = bAnyIslandTreeReview
        ? TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
               "FutaleufuIslandTreeSet_1K/SM_IslandTree01.SM_IslandTree01")
        : bCrownFamilyV3Review
            ? TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                   "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_SpreadingMature."
                   "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_SpreadingMature")
        : bDenseWoodyV2Review
            ? TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                   "SM_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2_OpenGrownMature."
                   "SM_RaftSim_SouthForkInteriorLiveOakDenseWoodyV2_OpenGrownMature")
            : bTrueWoodyV1Review
                ? TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                       "SM_RaftSim_SouthForkInteriorLiveOakWoodyV1_OpenGrownMature."
                       "SM_RaftSim_SouthForkInteriorLiveOakWoodyV1_OpenGrownMature")
                : TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                       "SM_RaftSim_SouthForkInteriorLiveOakAtlasV2Review_ConnectedCrownV2."
                       "SM_RaftSim_SouthForkInteriorLiveOakAtlasV2Review_ConnectedCrownV2");
    TArray<UStaticMesh*> ReviewMeshes;
    ReviewMeshes.Add(LoadObject<UStaticMesh>(nullptr, ReviewMeshObjectPath));
    if (bAnyIslandTreeReview)
    {
        ReviewMeshes.Add(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "FutaleufuIslandTreeSet_1K/SM_IslandTree02.SM_IslandTree02")));
        ReviewMeshes.Add(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "FutaleufuIslandTreeSet_1K/SM_IslandTree03.SM_IslandTree03")));
    }
    else if (bCrownFamilyV3Review)
    {
        ReviewMeshes.Add(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                 "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_CompactRiverEdge."
                 "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_CompactRiverEdge")));
        ReviewMeshes.Add(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
                 "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_AsymmetricCompetition."
                 "SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_AsymmetricCompetition")));
    }
    if (ReviewMeshes.Contains(nullptr))
    {
        OutSummary += FString::Printf(
            TEXT("Live-oak review mesh is unavailable; %s\n"),
            bAnyIslandTreeReview
                ? TEXT("the isolated rights-reviewed Poly Haven CC0 donor set "
                       "must be imported before capture.")
                : *FString::Printf(
                    TEXT("run RaftSim.RefreshSouthForkGeneratedCanopyAssets with "
                         "%s first."),
                    bCrownFamilyV3Review
                ? TEXT("-RaftSimOnlyLiveOakCrownFamilyV3Review")
                : bDenseWoodyV2Review
                ? TEXT("-RaftSimOnlyLiveOakDenseWoodyV2Review")
                : bTrueWoodyV1Review
                    ? TEXT("-RaftSimOnlyLiveOakWoodyCanopyV1Review")
                    : TEXT("-RaftSimOnlyLiveOakBranchAtlasV2Review")));
        return false;
    }
    UMaterialInterface* IslandTreeLeafReviewMaterial = nullptr;
    if (bIslandTreeMaterialV1Review)
    {
        IslandTreeLeafReviewMaterial = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
                 "M_RaftSim_SouthForkInteriorLiveOakIslandTreeMaterialV1Review_Leaves."
                 "M_RaftSim_SouthForkInteriorLiveOakIslandTreeMaterialV1Review_Leaves"));
        if (!IslandTreeLeafReviewMaterial)
        {
            OutSummary += TEXT(
                "Island-tree foliage material V1 review asset is unavailable; "
                "run RaftSim.RefreshSouthForkGeneratedCanopyAssets with "
                "-RaftSimOnlyLiveOakIslandTreeMaterialV1Review first.\n");
            return false;
        }
    }
    TArray<FVector> ReviewMeshEnvelopeScales;
    TArray<FBox> ReviewMeshEffectiveBounds;
    ReviewMeshEnvelopeScales.Init(FVector::OneVector, ReviewMeshes.Num());
    ReviewMeshEffectiveBounds.SetNum(ReviewMeshes.Num());
    if (bAnyIslandTreeReview)
    {
        // These rights-reviewed CC0 meshes are morphology donors only. They do
        // not claim surveyed Quercus wislizeni identity or ecology authority.
        // Match the production proxy's 12.5 m wide / 9.2 m tall authoring
        // envelope without altering the donor meshes or their source materials.
        constexpr float TargetCrownWidthCm = 1250.0f;
        constexpr float TargetTreeHeightCm = 920.0f;
        for (int32 MeshIndex = 0; MeshIndex < ReviewMeshes.Num(); ++MeshIndex)
        {
            UStaticMesh* ReviewMesh = ReviewMeshes[MeshIndex];
            FBox EffectiveBounds = ReviewMesh->GetBoundingBox();
            if (EffectiveBounds.GetSize().Z < 100.0f &&
                ReviewMesh->GetNumSourceModels() > 0)
            {
                const FVector BuildScale =
                    ReviewMesh->GetSourceModel(0).BuildSettings.BuildScale3D;
                EffectiveBounds = FBox(
                    EffectiveBounds.Min * BuildScale,
                    EffectiveBounds.Max * BuildScale);
            }
            const FVector EffectiveSize = EffectiveBounds.GetSize();
            const float HorizontalWidthCm = FMath::Max(
                EffectiveSize.X, EffectiveSize.Y);
            if (HorizontalWidthCm < 700.0f ||
                HorizontalWidthCm > 1400.0f ||
                EffectiveSize.Z < 600.0f ||
                EffectiveSize.Z > 1400.0f ||
                EffectiveBounds.Min.Z > 10.0f ||
                ReviewMesh->GetStaticMaterials().Num() != 3 ||
                !ReviewMesh->GetStaticMaterials()[1]
                    .MaterialSlotName.ToString().Contains(TEXT("leaves"),
                        ESearchCase::IgnoreCase) ||
                !ReviewMesh->GetStaticMaterials()[2]
                    .MaterialSlotName.ToString().Contains(TEXT("branches"),
                        ESearchCase::IgnoreCase))
            {
                OutSummary += FString::Printf(
                    TEXT("CC0 island-tree donor %d failed the physical-bounds, "
                         "grounded-pivot, or three-material-role gate: "
                         "size=(%.2f,%.2f,%.2f) min_z=%.2f materials=%d.\n"),
                    MeshIndex + 1,
                    EffectiveSize.X, EffectiveSize.Y, EffectiveSize.Z,
                    EffectiveBounds.Min.Z,
                    ReviewMesh->GetStaticMaterials().Num());
                return false;
            }
            const float HorizontalScale =
                TargetCrownWidthCm / HorizontalWidthCm;
            const float VerticalScale =
                TargetTreeHeightCm / EffectiveSize.Z;
            if (HorizontalScale < 0.80f || HorizontalScale > 1.80f ||
                VerticalScale < 0.65f || VerticalScale > 1.50f)
            {
                OutSummary += FString::Printf(
                    TEXT("CC0 island-tree donor %d needs an unsafe review "
                         "normalization scale (xy=%.4f z=%.4f).\n"),
                    MeshIndex + 1, HorizontalScale, VerticalScale);
                return false;
            }
            ReviewMeshEnvelopeScales[MeshIndex] = FVector(
                HorizontalScale, HorizontalScale, VerticalScale);
            ReviewMeshEffectiveBounds[MeshIndex] = EffectiveBounds;
        }
    }
    int32 SwappedComponentCount = 0;
    int32 SwappedInstanceCount = 0;
    TArray<int32> VariantComponentCounts;
    TArray<int32> VariantInstanceCounts;
    VariantComponentCounts.Init(0, ReviewMeshes.Num());
    VariantInstanceCounts.Init(0, ReviewMeshes.Num());
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        TInlineComponentArray<UHierarchicalInstancedStaticMeshComponent*>
            Components(*It);
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (!Component)
            {
                continue;
            }
            const FString Name = Component->GetName();
            if (Name != TEXT("OakBroadleafProxy") &&
                Name != TEXT("FarBroadleafCard"))
            {
                continue;
            }
            FSouthForkShoreRockReviewComponentState& State =
                OutStates.Emplace_GetRef();
            State.Component = Component;
            State.OriginalMesh = Component->GetStaticMesh();
            State.OriginalOverrideMaterials.Reserve(
                Component->OverrideMaterials.Num());
            for (UMaterialInterface* OriginalOverride :
                 Component->OverrideMaterials)
            {
                State.OriginalOverrideMaterials.Add(OriginalOverride);
            }
            const FString StableComponentId = FString::Printf(
                TEXT("%s|%s"), *It->GetPathName(), *Name);
            const bool bDistributedFamilyReview =
                bCrownFamilyV3Review || bAnyIslandTreeReview;
            const int32 VariantIndex = bDistributedFamilyReview
                ? static_cast<int32>(GetTypeHash(StableComponentId) %
                    static_cast<uint32>(ReviewMeshes.Num()))
                : 0;
            TArray<FTransform> ReviewTransforms;
            if (bAnyIslandTreeReview)
            {
                const int32 InstanceCount = Component->GetInstanceCount();
                State.OriginalWorldTransforms.Reserve(InstanceCount);
                ReviewTransforms.Reserve(InstanceCount);
                for (int32 InstanceIndex = 0;
                     InstanceIndex < InstanceCount;
                     ++InstanceIndex)
                {
                    FTransform OriginalWorldTransform;
                    if (!Component->GetInstanceTransform(
                            InstanceIndex, OriginalWorldTransform,
                            /*bWorldSpace=*/true))
                    {
                        OutSummary += FString::Printf(
                            TEXT("Could not read CC0 island-tree review "
                                 "transform %s[%d].\n"),
                            *Name, InstanceIndex);
                        RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                        return false;
                    }
                    State.OriginalWorldTransforms.Add(OriginalWorldTransform);
                    FTransform ReviewTransform = OriginalWorldTransform;
                    const FVector NormalizedScale =
                        OriginalWorldTransform.GetScale3D() *
                        ReviewMeshEnvelopeScales[VariantIndex];
                    ReviewTransform.SetScale3D(NormalizedScale);
                    const float GroundCorrectionCm =
                        -ReviewMeshEffectiveBounds[VariantIndex].Min.Z *
                        NormalizedScale.Z;
                    ReviewTransform.AddToTranslation(
                        OriginalWorldTransform.GetRotation().RotateVector(
                            FVector(0.0f, 0.0f, GroundCorrectionCm)));
                    ReviewTransforms.Add(ReviewTransform);
                }
            }
            Component->SetStaticMesh(ReviewMeshes[VariantIndex]);
            if (bIslandTreeMaterialV1Review)
            {
                Component->SetMaterial(1, IslandTreeLeafReviewMaterial);
            }
            if (ReviewTransforms.Num() > 0 &&
                !Component->BatchUpdateInstancesTransforms(
                    0, ReviewTransforms,
                    /*bWorldSpace=*/true,
                    /*bMarkRenderStateDirty=*/true,
                    /*bTeleport=*/true))
            {
                OutSummary += FString::Printf(
                    TEXT("Could not apply scale-normalized CC0 island-tree "
                         "review transforms to %s.\n"),
                    *Name);
                RestoreSouthForkPolyHavenShoreRockReview(OutStates);
                return false;
            }
            ++SwappedComponentCount;
            const int32 InstanceCount = Component->GetInstanceCount();
            SwappedInstanceCount += InstanceCount;
            ++VariantComponentCounts[VariantIndex];
            VariantInstanceCounts[VariantIndex] += InstanceCount;
        }
    }
    const bool bEveryCrownFamilyVariantUsed =
        !(bCrownFamilyV3Review || bAnyIslandTreeReview) ||
        Algo::AllOf(
            VariantComponentCounts,
            [](int32 Count) { return Count > 0; });
    const bool bIslandTreePopulationMatches = !bAnyIslandTreeReview ||
        (SwappedComponentCount == 21 && SwappedInstanceCount == 24830);
    if (SwappedComponentCount < 13 || SwappedInstanceCount <= 0 ||
        !bIslandTreePopulationMatches ||
        !bEveryCrownFamilyVariantUsed)
    {
        OutSummary += FString::Printf(
            TEXT("Live-oak review expected at least 13 source "
                 "components with instances but found %d components and %d "
                 "instances; distributed_variant_coverage=%d "
                 "island_tree_population_match=%d.\n"),
            SwappedComponentCount,
            SwappedInstanceCount,
            bEveryCrownFamilyVariantUsed ? 1 : 0,
            bIslandTreePopulationMatches ? 1 : 0);
        RestoreSouthForkPolyHavenShoreRockReview(OutStates);
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Transiently bound the %s live-oak representation to %d source "
             "components (%d instances); no map, collision, ecology, or "
             "hydraulic package was changed.\n"),
        bIslandTreeMaterialV1Review
            ? TEXT("scale-normalized, calibrated-leaf-material, "
                   "deterministically component-distributed CC0 island-tree "
                   "morphology-donor")
        : bIslandTreeMorphologyReview
            ? TEXT("scale-normalized, deterministically component-distributed "
                   "CC0 island-tree morphology-donor")
        : bCrownFamilyV3Review
            ? TEXT("deterministically component-distributed crown-family V3")
            : bDenseWoodyV2Review
            ? TEXT("dense-woody V2")
            : bTrueWoodyV1Review
                ? TEXT("true-woody V1")
                : TEXT("V2 branch-atlas"),
        SwappedComponentCount,
        SwappedInstanceCount);
    if (bCrownFamilyV3Review || bAnyIslandTreeReview)
    {
        if (bAnyIslandTreeReview)
        {
            OutSummary += FString::Printf(
                TEXT("CC0 island-tree morphology-donor stable distribution: "
                     "form_01=%d/%d form_02=%d/%d form_03=%d/%d "
                     "(components/instances).\n"),
                VariantComponentCounts[0], VariantInstanceCounts[0],
                VariantComponentCounts[1], VariantInstanceCounts[1],
                VariantComponentCounts[2], VariantInstanceCounts[2]);
        }
        else
        {
            OutSummary += FString::Printf(
                TEXT("Crown-family V3 stable distribution: "
                     "form_01=%d/%d form_02=%d/%d form_03=%d/%d "
                     "(components/instances).\n"),
                VariantComponentCounts[0], VariantInstanceCounts[0],
                VariantComponentCounts[1], VariantInstanceCounts[1],
                VariantComponentCounts[2], VariantInstanceCounts[2]);
        }
        if (bAnyIslandTreeReview)
        {
            OutSummary += FString::Printf(
                TEXT("CC0 island-tree envelope normalization (xy/z): "
                     "tree_01=%.4f/%.4f tree_02=%.4f/%.4f "
                     "tree_03=%.4f/%.4f; material_state=%s; "
                     "species/ecology authority remains false.\n"),
                ReviewMeshEnvelopeScales[0].X,
                ReviewMeshEnvelopeScales[0].Z,
                ReviewMeshEnvelopeScales[1].X,
                ReviewMeshEnvelopeScales[1].Z,
                ReviewMeshEnvelopeScales[2].X,
                ReviewMeshEnvelopeScales[2].Z,
                bIslandTreeMaterialV1Review
                    ? TEXT("only leaf slot 1 received the isolated V1 override")
                    : TEXT("all donor materials were preserved"));
        }
    }
    return true;
}

bool ConfigureSouthForkFullReachReviewLayers(
    UWorld* World,
    TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>&
        OutTerrainMaterialStates,
    TArray<FSouthForkShoreRockReviewComponentState>& OutRockStates,
    TArray<TWeakObjectPtr<AActor>>& OutDerivedBankActors,
    FString& OutSummary)
{
    if ((FParse::Param(FCommandLine::Get(), TEXT("RaftSimTerrainDetailV2Review")) ||
         FParse::Param(FCommandLine::Get(), TEXT("RaftSimRiverSmallRocksReview"))) &&
        !ConfigureSouthForkTerrainDetailV2Review(
            World, OutTerrainMaterialStates, OutSummary))
    {
        return false;
    }
    if ((FParse::Param(FCommandLine::Get(), TEXT("RaftSimPolyHavenShoreRockReview")) ||
         FParse::Param(FCommandLine::Get(), TEXT("RaftSimEmbeddedBankRockReview"))) &&
        !ConfigureSouthForkPolyHavenShoreRockReview(
            World, OutRockStates, OutSummary))
    {
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    if ((FParse::Param(
             FCommandLine::Get(), TEXT("RaftSimLiveOakBranchAtlasV2Review")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakBranchAtlasV2ExpandedReview")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakWoodyCanopyV1Review")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakDenseWoodyV2Review")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakCrownFamilyV3Review")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakIslandTreeMorphologyReview")) ||
         FParse::Param(
             FCommandLine::Get(),
             TEXT("RaftSimLiveOakIslandTreeMaterialV1Review"))) &&
        !ConfigureSouthForkLiveOakBranchAtlasV2Review(
            World,
            FParse::Param(
                FCommandLine::Get(),
                TEXT("RaftSimLiveOakWoodyCanopyV1Review")),
            FParse::Param(
                FCommandLine::Get(),
                TEXT("RaftSimLiveOakDenseWoodyV2Review")),
            FParse::Param(
                FCommandLine::Get(),
                TEXT("RaftSimLiveOakCrownFamilyV3Review")),
            FParse::Param(
                FCommandLine::Get(),
                TEXT("RaftSimLiveOakIslandTreeMorphologyReview")),
            FParse::Param(
                FCommandLine::Get(),
                TEXT("RaftSimLiveOakIslandTreeMaterialV1Review")),
            OutRockStates,
            OutSummary))
    {
        RestoreSouthForkPolyHavenShoreRockReview(OutRockStates);
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimDerivedBankMorphologyReview")) &&
        !ConfigureSouthForkDerivedBankMorphologyReview(
            World, OutDerivedBankActors, OutSummary))
    {
        RestoreSouthForkPolyHavenShoreRockReview(OutRockStates);
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimScannedBankKitReview")) &&
        !ConfigureSouthForkScannedBankKitReview(
            World, OutDerivedBankActors, OutSummary))
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutDerivedBankActors);
        RestoreSouthForkPolyHavenShoreRockReview(OutRockStates);
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimMeatGrinderHeroReview")) &&
        !ConfigureSouthForkMeatGrinderHeroReview(
            World, OutDerivedBankActors, OutSummary))
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutDerivedBankActors);
        RestoreSouthForkPolyHavenShoreRockReview(OutRockStates);
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimDisplacedGravelBarReview")) &&
        !ConfigureSouthForkDisplacedGravelBarReview(
            World, OutDerivedBankActors, OutSummary))
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutDerivedBankActors);
        RestoreSouthForkPolyHavenShoreRockReview(OutRockStates);
        RestoreSouthForkTerrainDetailV2Review(OutTerrainMaterialStates);
        return false;
    }
    return true;
}

void RestoreSouthForkFullReachReviewLayers(
    const TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>&
        TerrainMaterialStates,
    const TArray<FSouthForkShoreRockReviewComponentState>& RockStates,
    const TArray<TWeakObjectPtr<AActor>>& DerivedBankActors)
{
    RestoreSouthForkDerivedBankMorphologyReview(DerivedBankActors);
    RestoreSouthForkPolyHavenShoreRockReview(RockStates);
    RestoreSouthForkTerrainDetailV2Review(TerrainMaterialStates);
}

void ConfigureSouthForkSettledSourceCaptureVisibility(
    UWorld* World,
    TArray<TPair<TWeakObjectPtr<UPrimitiveComponent>, bool>>& OutVisibilityStates,
    FString& OutSummary)
{
    // LoadAllActors brings source actors and HLOD proxies into the editor
    // world together. Runtime World Partition selects only one representation;
    // explicitly reproduce that contract for settled source captures.
    int32 HiddenHlodComponentCount = 0;
    for (TActorIterator<AWorldPartitionHLOD> It(World); It; ++It)
    {
        TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents(*It);
        for (UPrimitiveComponent* Component : PrimitiveComponents)
        {
            if (Component)
            {
                OutVisibilityStates.Emplace(Component, Component->IsVisible());
                Component->SetVisibility(false, true);
                ++HiddenHlodComponentCount;
            }
        }
    }

    FName ActiveFlowBandTag(TEXT("RaftSimFlowBand_median_runnable"));
    for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
    {
        if (*It)
        {
            ActiveFlowBandTag = FName(*FString::Printf(
                TEXT("RaftSimFlowBand_%s"), *It->FlowBand.ToString()));
            break;
        }
    }
    int32 FlowBandComponentCount = 0;
    int32 HiddenInactiveFlowBandComponentCount = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        bool bIsFlowBandPresentation = false;
        bool bIsActiveFlowBand = false;
        for (const FName& Tag : Actor->Tags)
        {
            if (Tag.ToString().StartsWith(TEXT("RaftSimFlowBand_")))
            {
                bIsFlowBandPresentation = true;
                bIsActiveFlowBand |= Tag == ActiveFlowBandTag;
            }
        }
        if (!bIsFlowBandPresentation)
        {
            continue;
        }
        TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents(Actor);
        for (UPrimitiveComponent* Component : PrimitiveComponents)
        {
            if (Component)
            {
                OutVisibilityStates.Emplace(Component, Component->IsVisible());
                Component->SetVisibility(bIsActiveFlowBand, true);
                ++FlowBandComponentCount;
                HiddenInactiveFlowBandComponentCount += bIsActiveFlowBand ? 0 : 1;
            }
        }
    }
    OutSummary += FString::Printf(
        TEXT("Settled source capture isolated %d HLOD primitive components and "
             "selected %s across %d flow-band components (%d inactive).\n"),
        HiddenHlodComponentCount,
        *ActiveFlowBandTag.ToString(),
        FlowBandComponentCount,
        HiddenInactiveFlowBandComponentCount);
}

void RestoreSouthForkSettledSourceCaptureVisibility(
    const TArray<TPair<TWeakObjectPtr<UPrimitiveComponent>, bool>>& VisibilityStates)
{
    for (const TPair<TWeakObjectPtr<UPrimitiveComponent>, bool>& Pair : VisibilityStates)
    {
        if (Pair.Key.IsValid())
        {
            Pair.Key->SetVisibility(Pair.Value, true);
        }
    }
}

bool FindSouthForkMedianWaterSurfaceLocalZCm(
    UWorld* World,
    const FVector2D& WorldLocationM,
    float& OutSurfaceLocalZCm)
{
    if (!World)
    {
        return false;
    }

    const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
    const FVector2D TargetCm = WorldLocationM * 100.0;
    double BestDistanceSquaredCm = TNumericLimits<double>::Max();
    bool bFound = false;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Actor = *It;
        UStaticMeshComponent* Component = Actor
            ? Actor->GetStaticMeshComponent()
            : nullptr;
        UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        const FStaticMeshRenderData* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
        if (!Actor || !Actor->ActorHasTag(MedianWaterTag) ||
            !RenderData || RenderData->LODResources.IsEmpty())
        {
            continue;
        }

        const FPositionVertexBuffer& Positions =
            RenderData->LODResources[0].VertexBuffers.PositionVertexBuffer;
        const FTransform ComponentTransform = Component->GetComponentTransform();
        for (uint32 VertexIndex = 0;
             VertexIndex < Positions.GetNumVertices();
             ++VertexIndex)
        {
            const FVector WorldPositionCm = ComponentTransform.TransformPosition(
                FVector(Positions.VertexPosition(VertexIndex)));
            const double DistanceSquaredCm = FVector2D::DistSquared(
                FVector2D(WorldPositionCm.X, WorldPositionCm.Y), TargetCm);
            if (DistanceSquaredCm < BestDistanceSquaredCm)
            {
                BestDistanceSquaredCm = DistanceSquaredCm;
                OutSurfaceLocalZCm = static_cast<float>(WorldPositionCm.Z);
                bFound = true;
            }
        }
    }

    // The authored solver grid is four metres. A valid centerline sample must
    // resolve within two diagonal cells; otherwise the map is incomplete or
    // the fixed capture recipe no longer matches its source coordinate map.
    constexpr double MaximumSampleDistanceCm = 1200.0;
    return bFound &&
        BestDistanceSquaredCm <= MaximumSampleDistanceCm * MaximumSampleDistanceCm;
}

bool CaptureSouthForkView(
    UWorld* World,
    const FString& CaptureId,
    const FVector& CameraLocation,
    const FRotator& CameraRotation,
    FString& OutRelativePath,
    FString& OutSummary)
{
    const bool bPhotographicCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimPhotographicSouthForkCapture"));
    const bool bVolumetricBroadleafReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimVolumetricBroadleafReviewCapture"));
    const bool bSourceHlodExclusiveReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimSourceHlodExclusiveWaterReview"));
    const bool bSolverDerivedAerationReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimSolverDerivedAerationReview"));
    const bool bSolverGatedBreakingReliefReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimSolverGatedBreakingReliefReview"));
    const bool bGuideFeatureBreakingReliefReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimGuideFeatureBreakingReliefReview"));
    const bool bRefinedGuideFeatureFoamReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimRefinedGuideFeatureFoamReview"));
    const bool bTerrainDetailV2ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimTerrainDetailV2Review"));
    const bool bPolyHavenShoreRockReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimPolyHavenShoreRockReview"));
    const bool bEmbeddedBankRockReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimEmbeddedBankRockReview"));
    const bool bDerivedBankMorphologyReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDerivedBankMorphologyReview"));
    const bool bScannedBankKitReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimScannedBankKitReview"));
    const bool bMeatGrinderHeroReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimMeatGrinderHeroReview"));
    const bool bRiverSmallRocksReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimRiverSmallRocksReview"));
    const bool bDisplacedGravelBarReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDisplacedGravelBarReview"));
    const bool bLiveOakBranchAtlasV2ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakBranchAtlasV2Review"));
    const bool bLiveOakBranchAtlasV2ExpandedReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakBranchAtlasV2ExpandedReview"));
    const bool bLiveOakWoodyCanopyV1ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakWoodyCanopyV1Review"));
    const bool bLiveOakDenseWoodyV2ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakDenseWoodyV2Review"));
    const bool bLiveOakCrownFamilyV3ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakCrownFamilyV3Review"));
    const bool bLiveOakIslandTreeMorphologyReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakIslandTreeMorphologyReview"));
    const bool bLiveOakIslandTreeMaterialV1ReviewCapture = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimLiveOakIslandTreeMaterialV1Review"));
    FlushAsyncLoading();
    // Settle every streamed resource before fixed-camera evidence so package
    // load completion cannot change distant shelves, materials, or canopy.
    World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    IStreamingManager::Get().StreamAllResources(30.0f);
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    if (!RenderTarget)
    {
        return false;
    }
    constexpr int32 Width = 1280;
    constexpr int32 Height = 720;
    RenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    RenderTarget->ClearColor = FLinearColor::Black;
    RenderTarget->InitAutoFormat(Width, Height);
    RenderTarget->UpdateResourceImmediate(true);
    ASceneCapture2D* Capture = World->SpawnActor<ASceneCapture2D>(
        ASceneCapture2D::StaticClass(), CameraLocation, CameraRotation);
    USceneCaptureComponent2D* Component =
        Capture ? Capture->GetCaptureComponent2D() : nullptr;
    if (!Component)
    {
        RenderTarget->ReleaseResource();
        return false;
    }
    Component->TextureTarget = RenderTarget;
    Component->CaptureSource = SCS_FinalColorLDR;
    Component->FOVAngle = 82.0f;
    Component->bCaptureEveryFrame = false;
    Component->bCaptureOnMovement = false;
    Component->bAlwaysPersistRenderingState = true;
    Component->ShowFlags.SetSelection(false);
    Component->ShowFlags.SetModeWidgets(false);
    Component->ShowFlags.SetCompositeEditorPrimitives(false);
    Component->ShowFlags.SetMotionBlur(false);
    Component->ShowFlags.SetEyeAdaptation(false);
    if (bPhotographicCapture)
    {
        // The byte-repeat capture intentionally removes temporal rendering.
        // Photoreal review needs a separate, opt-in renderer path that shows
        // the same immutable map with its production GI, reflections, AO and
        // temporal edge reconstruction. Keep eye adaptation and motion blur
        // disabled so exposure and geometry remain comparable between views.
        Component->ShowFlags.SetAntiAliasing(true);
        Component->ShowFlags.SetTemporalAA(true);
        Component->ShowFlags.SetAmbientOcclusion(true);
        Component->ShowFlags.SetGlobalIllumination(true);
        Component->ShowFlags.SetLumenGlobalIllumination(true);
        Component->ShowFlags.SetLumenReflections(true);
        Component->ShowFlags.SetScreenSpaceReflections(true);
        Component->ShowFlags.SetReflectionEnvironment(true);
    }
    else
    {
        Component->ShowFlags.SetTemporalAA(false);
        Component->ShowFlags.SetLumenGlobalIllumination(false);
        Component->ShowFlags.SetLumenReflections(false);
    }
    Component->PostProcessSettings.bOverride_FilmGrainIntensity = true;
    Component->PostProcessSettings.FilmGrainIntensity = 0.0f;

    IConsoleVariable* MaterialTimeVariable = IConsoleManager::Get().FindConsoleVariable(
        TEXT("r.Test.OverrideTimeMaterialExpressions"));
    const float PreviousMaterialTime = MaterialTimeVariable
        ? MaterialTimeVariable->GetFloat()
        : -1.0f;
    if (MaterialTimeVariable)
    {
        MaterialTimeVariable->Set(1.0f, ECVF_SetByCode);
    }
    IConsoleVariable* GrainQuantizationVariable =
        IConsoleManager::Get().FindConsoleVariable(
            TEXT("r.Tonemapper.GrainQuantization"));
    const int32 PreviousGrainQuantization = GrainQuantizationVariable
        ? GrainQuantizationVariable->GetInt()
        : -1;
    if (GrainQuantizationVariable)
    {
        GrainQuantizationVariable->Set(0, ECVF_SetByCode);
    }
    auto RestoreCaptureVariables =
        [GrainQuantizationVariable, PreviousGrainQuantization,
         MaterialTimeVariable, PreviousMaterialTime]()
    {
        if (MaterialTimeVariable)
        {
            MaterialTimeVariable->Set(PreviousMaterialTime, ECVF_SetByCode);
        }
        if (GrainQuantizationVariable && PreviousGrainQuantization >= 0)
        {
            GrainQuantizationVariable->Set(
                PreviousGrainQuantization, ECVF_SetByCode);
        }
    };

    const int32 SettleFrameCount = bPhotographicCapture ? 12 : 1;
    for (int32 SettleFrameIndex = 0;
         SettleFrameIndex < SettleFrameCount;
         ++SettleFrameIndex)
    {
        Component->CaptureScene();
        FlushRenderingCommands();
        if (bPhotographicCapture)
        {
            // Persisted scene-capture state needs several rendered frames for
            // TSR and Lumen history to converge. This changes evidence only;
            // no actor, package, material, or gameplay authority is written.
            FPlatformProcess::Sleep(0.016f);
        }
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    FPlatformProcess::Sleep(0.03f);
    Component->CaptureScene();
    FlushRenderingCommands();

    FTextureRenderTargetResource* Resource =
        RenderTarget->GameThread_GetRenderTargetResource();
    TArray<FColor> Pixels;
    const bool bRead = Resource && Resource->ReadPixels(Pixels) &&
        Pixels.Num() == Width * Height;
    if (!bRead)
    {
        RestoreCaptureVariables();
        Capture->Destroy();
        RenderTarget->ReleaseResource();
        return false;
    }
    for (FColor& Pixel : Pixels)
    {
        Pixel.A = 255;
    }
    TArray64<uint8> Compressed;
    FImageUtils::PNGCompressImageArray(
        Width, Height, MakeArrayView(Pixels), Compressed);
    const TCHAR* CaptureDirectory = CaptureDirectoryRelativePath;
    if (bPhotographicCapture)
    {
        CaptureDirectory = PhotographicCaptureDirectoryRelativePath;
    }
    if (bVolumetricBroadleafReviewCapture)
    {
        CaptureDirectory = VolumetricBroadleafCaptureDirectoryRelativePath;
    }
    if (bSourceHlodExclusiveReviewCapture)
    {
        CaptureDirectory = SourceHlodExclusiveCaptureDirectoryRelativePath;
    }
    if (bSolverDerivedAerationReviewCapture)
    {
        CaptureDirectory = SolverDerivedAerationCaptureDirectoryRelativePath;
    }
    if (bSolverGatedBreakingReliefReviewCapture)
    {
        CaptureDirectory = SolverGatedBreakingReliefCaptureDirectoryRelativePath;
    }
    if (bGuideFeatureBreakingReliefReviewCapture)
    {
        CaptureDirectory = GuideFeatureBreakingReliefCaptureDirectoryRelativePath;
    }
    if (bRefinedGuideFeatureFoamReviewCapture)
    {
        CaptureDirectory = RefinedGuideFeatureFoamCaptureDirectoryRelativePath;
    }
    if (bTerrainDetailV2ReviewCapture)
    {
        CaptureDirectory = TerrainDetailV2ReviewCaptureDirectoryRelativePath;
    }
    if (bPolyHavenShoreRockReviewCapture)
    {
        CaptureDirectory = PolyHavenShoreRockReviewCaptureDirectoryRelativePath;
    }
    if (bEmbeddedBankRockReviewCapture)
    {
        CaptureDirectory = EmbeddedBankRockReviewCaptureDirectoryRelativePath;
    }
    if (bDerivedBankMorphologyReviewCapture)
    {
        CaptureDirectory = DerivedBankMorphologyReviewCaptureDirectoryRelativePath;
    }
    if (bScannedBankKitReviewCapture)
    {
        CaptureDirectory = ScannedBankKitReviewCaptureDirectoryRelativePath;
    }
    if (bMeatGrinderHeroReviewCapture)
    {
        CaptureDirectory = MeatGrinderHeroReviewCaptureDirectoryRelativePath;
    }
    if (bRiverSmallRocksReviewCapture)
    {
        CaptureDirectory = RiverSmallRocksReviewCaptureDirectoryRelativePath;
    }
    if (bDisplacedGravelBarReviewCapture)
    {
        CaptureDirectory = DisplacedGravelBarReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakBranchAtlasV2ReviewCapture)
    {
        CaptureDirectory = LiveOakBranchAtlasV2ReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakBranchAtlasV2ExpandedReviewCapture)
    {
        CaptureDirectory =
            LiveOakBranchAtlasV2ExpandedReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakWoodyCanopyV1ReviewCapture)
    {
        CaptureDirectory = LiveOakWoodyCanopyV1ReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakDenseWoodyV2ReviewCapture)
    {
        CaptureDirectory = LiveOakDenseWoodyV2ReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakCrownFamilyV3ReviewCapture)
    {
        CaptureDirectory = LiveOakCrownFamilyV3ReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakIslandTreeMorphologyReviewCapture)
    {
        CaptureDirectory =
            LiveOakIslandTreeMorphologyReviewCaptureDirectoryRelativePath;
    }
    if (bLiveOakIslandTreeMaterialV1ReviewCapture)
    {
        CaptureDirectory =
            LiveOakIslandTreeMaterialV1ReviewCaptureDirectoryRelativePath;
    }
    OutRelativePath = FString::Printf(
        TEXT("%s/%s.png"), CaptureDirectory, *CaptureId);
    const FString AbsolutePath = AbsoluteCapturePath(OutRelativePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsolutePath), true);
    const bool bSaved = FFileHelper::SaveArrayToFile(Compressed, *AbsolutePath);
    RestoreCaptureVariables();
    Capture->Destroy();
    RenderTarget->ReleaseResource();
    OutSummary += FString::Printf(
        TEXT("%s settled-map full-reach %s capture %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        bPhotographicCapture ? TEXT("photographic") : TEXT("deterministic"),
        *CaptureId, *AbsolutePath);
    return bSaved;
}
}
