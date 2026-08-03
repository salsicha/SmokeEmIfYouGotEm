#include "Camera/CameraComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Materials/Material.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimCrewStateContracts.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimMannyCrewVisualActor.h"
#include "RaftSimMetaHumanCrewVisualActor.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRaftCondition.h"
#include "RaftSimRaftMesh.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Tests/AutomationCommon.h"
#include "TextureCompiler.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS

namespace
{
void FinishTextureCompilation(UTexture2D* Texture)
{
#if WITH_EDITOR
    if (Texture)
    {
        TArray<UTexture*> Textures{Texture};
        FTextureCompilingManager::Get().FinishCompilation(Textures);
        Texture->BlockOnAnyAsyncBuild();
    }
#endif
}

bool PoseIsFinite(const FRaftSimCrewAvatarPose& Pose)
{
    return !Pose.TorsoCenterCm.ContainsNaN() && !Pose.HeadCenterCm.ContainsNaN() &&
        !Pose.LeftHandCm.ContainsNaN() && !Pose.RightHandCm.ContainsNaN() &&
        !Pose.LeftFootCm.ContainsNaN() && !Pose.RightFootCm.ContainsNaN() &&
        !Pose.PaddleTopCm.ContainsNaN() && !Pose.PaddleBottomCm.ContainsNaN();
}

float RingPolygonArea(const TArray<FVector>& Vertices, int32 Start, int32 Count)
{
    FVector AreaVector = FVector::ZeroVector;
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const FVector& A = Vertices[Start + Index];
        const FVector& B = Vertices[Start + (Index + 1) % Count];
        AreaVector += FVector::CrossProduct(A, B);
    }
    return 0.5f * AreaVector.Size();
}

UWorld* GetM5GameWorld()
{
    UWorld* Newest = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            Newest = Context.World();
        }
    }
    return Newest;
}

ARaftSimRaftActor* FindM5Raft()
{
    if (UWorld* World = GetM5GameWorld())
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

ARaftSimGuidePawn* FindM5Guide()
{
    if (UWorld* World = GetM5GameWorld())
    {
        if (TActorIterator<ARaftSimGuidePawn> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5CrewAvatarPoseTest,
    "RaftSim.M5.CrewAvatarPoseProduction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5CrewAvatarPoseTest::RunTest(const FString&)
{
    UStaticMesh* ProductionHelmet = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterHelmet."
             "SM_RaftSim_WhitewaterHelmet"));
    TestNotNull(TEXT("project-owned production whitewater helmet exists"), ProductionHelmet);
    if (ProductionHelmet)
    {
        const FVector DimensionsCm = ProductionHelmet->GetBoundingBox().GetSize();
        TestEqual(TEXT("production helmet has four authored material slots"),
                  ProductionHelmet->GetStaticMaterials().Num(), 4);
        TestTrue(TEXT("production helmet has plausible centimetre bounds"),
                 DimensionsCm.GetMin() >= 24.0f && DimensionsCm.GetMax() <= 35.0f);
        TestTrue(TEXT("production helmet has a Nanite render resource"),
                 ProductionHelmet->HasValidNaniteData());
    }
    UStaticMesh* ProductionPfd = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterRescuePfd."
             "SM_RaftSim_WhitewaterRescuePfd"));
    TestNotNull(TEXT("project-owned production whitewater rescue PFD exists"), ProductionPfd);
    if (ProductionPfd)
    {
        const FVector DimensionsCm = ProductionPfd->GetBoundingBox().GetSize();
        TestEqual(TEXT("production rescue PFD has five authored material slots"),
                  ProductionPfd->GetStaticMaterials().Num(), 5);
        TestTrue(TEXT("production rescue PFD has plausible centimetre bounds"),
                 DimensionsCm.X >= 32.0f && DimensionsCm.X <= 44.0f &&
                 DimensionsCm.Y >= 32.0f && DimensionsCm.Y <= 44.0f &&
                 DimensionsCm.Z >= 40.0f && DimensionsCm.Z <= 56.0f);
        TestTrue(TEXT("production rescue PFD has a Nanite render resource"),
                 ProductionPfd->HasValidNaniteData());
    }
    UStaticMesh* ProductionRiverBoot = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterRiverBoot."
             "SM_RaftSim_WhitewaterRiverBoot"));
    TestNotNull(TEXT("project-owned production whitewater river boot exists"),
                ProductionRiverBoot);
    if (ProductionRiverBoot)
    {
        const FVector DimensionsCm = ProductionRiverBoot->GetBoundingBox().GetSize();
        TestEqual(TEXT("production river boot has three authored material slots"),
                  ProductionRiverBoot->GetStaticMaterials().Num(), 3);
        if (ProductionRiverBoot->GetStaticMaterials().Num() == 3)
        {
            const TArray<FStaticMaterial>& BootMaterials =
                ProductionRiverBoot->GetStaticMaterials();
            TestTrue(TEXT("production river boot upper uses its dedicated PBR material"),
                     BootMaterials[0].MaterialInterface &&
                         BootMaterials[0].MaterialInterface->GetPathName().Contains(
                             TEXT("M_RaftSim_RiverBootUpper")));
            TestTrue(TEXT("production river boot sole uses dedicated rubber"),
                     BootMaterials[1].MaterialInterface &&
                         BootMaterials[1].MaterialInterface->GetPathName().Contains(
                             TEXT("M_RaftSim_RiverBootRubber")));
            TestTrue(TEXT("production river boot rand uses dedicated rubber"),
                     BootMaterials[2].MaterialInterface &&
                         BootMaterials[2].MaterialInterface->GetPathName().Contains(
                             TEXT("M_RaftSim_RiverBootRubber")));
        }
        TestTrue(TEXT("production river boot has plausible centimetre bounds"),
                 DimensionsCm.X >= 30.0f && DimensionsCm.X <= 36.0f &&
                 DimensionsCm.Y >= 12.0f && DimensionsCm.Y <= 15.0f &&
                 DimensionsCm.Z >= 22.0f && DimensionsCm.Z <= 25.0f);
        TestTrue(TEXT("production river boot retains a nontrivial Nanite fallback"),
                 ProductionRiverBoot->GetNumTriangles(0) >= 1500);
        TestTrue(TEXT("production river boot has a Nanite render resource"),
                 ProductionRiverBoot->HasValidNaniteData());
    }
    UStaticMesh* ProductionBoulder = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/Rocks/Production/"
             "SM_RaftSim_ProductionRiverBoulder."
             "SM_RaftSim_ProductionRiverBoulder"));
    TestNotNull(TEXT("project-owned production river boulder exists"), ProductionBoulder);
    if (ProductionBoulder)
    {
        const FVector DimensionsCm = ProductionBoulder->GetBoundingBox().GetSize();
        TestEqual(TEXT("production river boulder has one authored material slot"),
                  ProductionBoulder->GetStaticMaterials().Num(), 1);
        TestTrue(TEXT("production river boulder has plausible contact-envelope bounds"),
                 DimensionsCm.X >= 205.0f && DimensionsCm.X <= 240.0f &&
                 DimensionsCm.Y >= 190.0f && DimensionsCm.Y <= 225.0f &&
                 DimensionsCm.Z >= 160.0f && DimensionsCm.Z <= 200.0f);
        TestTrue(TEXT("production river boulder has a Nanite render resource"),
                 ProductionBoulder->HasValidNaniteData());
    }
    UTexture2D* SkinAlbedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailAlbedo."
             "T_RaftSim_CrewSkin_MicrodetailAlbedo"));
    UTexture2D* SkinNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Characters/Textures/"
             "T_RaftSim_CrewSkin_MicrodetailNormal."
             "T_RaftSim_CrewSkin_MicrodetailNormal"));
    TestNotNull(TEXT("synthetic skin micro-albedo texture exists"), SkinAlbedo);
    TestNotNull(TEXT("synthetic skin micro-normal texture exists"), SkinNormal);
    FinishTextureCompilation(SkinAlbedo);
    FinishTextureCompilation(SkinNormal);
    if (SkinAlbedo)
    {
        TestEqual(
            TEXT("skin albedo width"),
            SkinAlbedo->GetSizeX(),
            1024);
        TestEqual(
            TEXT("skin albedo height"),
            SkinAlbedo->GetSizeY(),
            1024);
        TestTrue(TEXT("skin albedo uses sRGB"), SkinAlbedo->SRGB);
        TestEqual(
            TEXT("skin albedo uses character LOD group"),
            SkinAlbedo->LODGroup,
            TEXTUREGROUP_Character);
    }
    if (SkinNormal)
    {
        TestEqual(
            TEXT("skin normal width"),
            SkinNormal->GetSizeX(),
            1024);
        TestEqual(
            TEXT("skin normal height"),
            SkinNormal->GetSizeY(),
            1024);
        TestFalse(TEXT("skin normal disables sRGB"), SkinNormal->SRGB);
        TestEqual(
            TEXT("skin normal compression"),
            SkinNormal->CompressionSettings,
            TC_Normalmap);
    }

    static const TCHAR* CC0MaterialPaths[] = {
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Guide_Skin."
             "M_RaftSim_CC0_Guide_Skin"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew01_Skin."
             "M_RaftSim_CC0_Crew01_Skin"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew02_Skin."
             "M_RaftSim_CC0_Crew02_Skin"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew03_Skin."
             "M_RaftSim_CC0_Crew03_Skin"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew04_Skin."
             "M_RaftSim_CC0_Crew04_Skin"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Guide_Hair."
             "M_RaftSim_CC0_Guide_Hair"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew01_Hair."
             "M_RaftSim_CC0_Crew01_Hair"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew02_Hair."
             "M_RaftSim_CC0_Crew02_Hair"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew03_Hair."
             "M_RaftSim_CC0_Crew03_Hair"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Crew04_Hair."
             "M_RaftSim_CC0_Crew04_Hair"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Eyes."
             "M_RaftSim_CC0_Eyes"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Wetsuit."
             "M_RaftSim_CC0_Wetsuit"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/M_RaftSim_CC0_Brows."
             "M_RaftSim_CC0_Brows"),
        TEXT("/Game/RaftSim/Characters/Production/CC0/Materials/"
             "M_RaftSim_CC0_HelmetContainedHairHidden."
             "M_RaftSim_CC0_HelmetContainedHairHidden")};
    for (const TCHAR* MaterialPath : CC0MaterialPaths)
    {
        UMaterial* Material = LoadObject<UMaterial>(nullptr, MaterialPath);
        TestNotNull(FString::Printf(TEXT("CC0 material exists: %s"), MaterialPath), Material);
        if (Material)
        {
            TestTrue(
                FString::Printf(TEXT("CC0 material has SkeletalMesh usage: %s"), MaterialPath),
            Material->GetUsageByFlag(MATUSAGE_SkeletalMesh));
            if (FString(MaterialPath).Contains(TEXT("_Skin.")))
            {
                TestTrue(
                    FString::Printf(
                        TEXT("CC0 skin uses preintegrated scattering: %s"),
                        MaterialPath),
                    Material->GetShadingModels().HasShadingModel(
                        MSM_PreintegratedSkin));
            }
            if (FString(MaterialPath).Contains(TEXT("_Eyes.")))
            {
                TestTrue(
                    TEXT("CC0 eyes use a corneal clear-coat shading layer"),
                    Material->GetShadingModels().HasShadingModel(MSM_ClearCoat));
                TestEqual(
                    TEXT("CC0 eye surface remains opaque"),
                    Material->GetBlendMode(),
                    BLEND_Opaque);
                TestFalse(
                    TEXT("CC0 helper-eye shell retains reviewed outward winding"),
                    Material->IsTwoSided());
            }
        }
    }

    struct FHairTextureExpectation
    {
        const TCHAR* AssetName;
        bool bNormal;
    };
    static const FHairTextureExpectation HairTextures[] = {
        {TEXT("T_RaftSim_Hair_Grump_D"), false},
        {TEXT("T_RaftSim_Hair_BraidedRows_D"), false},
        {TEXT("T_RaftSim_Hair_BraidedRows_N"), true},
        {TEXT("T_RaftSim_Hair_ShortSide_D"), false},
    };
    for (const FHairTextureExpectation& Expected : HairTextures)
    {
        const FString ObjectPath = FString::Printf(
            TEXT("/Game/RaftSim/Characters/Production/CC0/Textures/%s.%s"),
            Expected.AssetName,
            Expected.AssetName);
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
        TestNotNull(
            FString::Printf(TEXT("rights-compatible hair texture exists: %s"), Expected.AssetName),
            Texture);
        if (Texture)
        {
            FinishTextureCompilation(Texture);
            TestTrue(
                FString::Printf(TEXT("%s is at least 1K"), Expected.AssetName),
                Texture->GetSizeX() >= 1024 && Texture->GetSizeY() >= 1024);
            TestEqual(
                FString::Printf(TEXT("%s sRGB"), Expected.AssetName),
                Texture->SRGB,
                !Expected.bNormal);
            if (Expected.bNormal)
            {
                TestEqual(
                    FString::Printf(TEXT("%s normal compression"), Expected.AssetName),
                    Texture->CompressionSettings,
                    TC_Normalmap);
            }
        }
    }

    static const TCHAR* CharacterVariants[] = {
        TEXT("Guide"), TEXT("Crew01"), TEXT("Crew02"), TEXT("Crew03"), TEXT("Crew04")};
    for (const TCHAR* Variant : CharacterVariants)
    {
        const FString AssetName = FString::Printf(TEXT("SK_RaftSim_CC0_%s"), Variant);
        const FString ObjectPath = FString::Printf(
            TEXT("/Game/RaftSim/Characters/Production/CC0/%s.%s"), *AssetName, *AssetName);
        USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *ObjectPath);
        TestNotNull(FString::Printf(TEXT("production character exists: %s"), Variant), Mesh);
        if (!Mesh)
        {
            continue;
        }
        TestEqual(
            FString::Printf(TEXT("%s has skin, wetsuit, hair, eyes, and brows"), Variant),
            Mesh->GetMaterials().Num(),
            5);
        const FSkeletalMaterial* HairSlot = Mesh->GetMaterials().FindByPredicate(
            [](const FSkeletalMaterial& Slot)
            {
                return Slot.MaterialSlotName.ToString().Contains(TEXT("Hair"));
            });
        TestNotNull(FString::Printf(TEXT("%s has a named hair slot"), Variant), HairSlot);
        if (HairSlot)
        {
            TestNotNull(
                FString::Printf(TEXT("%s hair slot has a generated material"), Variant),
                HairSlot->MaterialInterface.Get());
            if (HairSlot->MaterialInterface)
            {
                TestTrue(
                    FString::Printf(TEXT("%s helmet-contained hair is suppressed"), Variant),
                    HairSlot->MaterialInterface->GetPathName().Contains(
                        TEXT("M_RaftSim_CC0_HelmetContainedHairHidden")));
            }
        }

        FSkeletalMeshRenderData* RenderData = Mesh->GetResourceForRendering();
        TestNotNull(
            FString::Printf(TEXT("%s has cooked skeletal render data"), Variant),
            RenderData);
        if (RenderData && !RenderData->LODRenderData.IsEmpty())
        {
            const int32 HeadBoneIndex =
                Mesh->GetRefSkeleton().FindBoneIndex(TEXT("head"));
            TestTrue(
                FString::Printf(TEXT("%s has a head bone"), Variant),
                HeadBoneIndex != INDEX_NONE);
            const FSkeletalMeshLODRenderData& LODData = RenderData->LODRenderData[0];
            const FSkinWeightVertexBuffer* SkinWeights =
                LODData.GetSkinWeightVertexBuffer();
            TestNotNull(
                FString::Printf(TEXT("%s has LOD0 skin weights"), Variant),
                SkinWeights);
            if (HeadBoneIndex != INDEX_NONE && SkinWeights)
            {
                const auto DominantSkeletonBone = [SkinWeights](
                    const FSkelMeshRenderSection& Section,
                    uint32 VertexIndex)
                {
                    uint16 DominantWeight = 0;
                    int32 DominantBone = INDEX_NONE;
                    for (uint32 InfluenceIndex = 0;
                         InfluenceIndex < SkinWeights->GetMaxBoneInfluences();
                         ++InfluenceIndex)
                    {
                        const uint32 LocalBoneIndex =
                            SkinWeights->GetBoneIndex(VertexIndex, InfluenceIndex);
                        if (!Section.BoneMap.IsValidIndex(LocalBoneIndex))
                        {
                            continue;
                        }
                        const uint16 Weight =
                            SkinWeights->GetBoneWeight(VertexIndex, InfluenceIndex);
                        if (Weight > DominantWeight)
                        {
                            DominantWeight = Weight;
                            DominantBone = Section.BoneMap[LocalBoneIndex];
                        }
                    }
                    return DominantBone;
                };
                struct FSkinVertex
                {
                    uint32 VertexIndex = 0;
                    const FSkelMeshRenderSection* Section = nullptr;
                };
                TArray<FSkinVertex> SkinVertices;
                for (const FSkelMeshRenderSection& Section : LODData.RenderSections)
                {
                    if (!Mesh->GetMaterials().IsValidIndex(Section.MaterialIndex) ||
                        !Mesh->GetMaterials()[Section.MaterialIndex]
                             .MaterialSlotName.ToString()
                             .Contains(TEXT("Skin"), ESearchCase::IgnoreCase))
                    {
                        continue;
                    }
                    const uint32 EndVertex =
                        Section.BaseVertexIndex + Section.NumVertices;
                    for (uint32 VertexIndex = Section.BaseVertexIndex;
                         VertexIndex < EndVertex;
                         ++VertexIndex)
                    {
                        SkinVertices.Add({VertexIndex, &Section});
                    }
                }
                TestTrue(
                    FString::Printf(TEXT("%s has Skin-section LOD0 vertices"), Variant),
                    !SkinVertices.IsEmpty());
                for (const FSkelMeshRenderSection& Section : LODData.RenderSections)
                {
                    if (!Mesh->GetMaterials().IsValidIndex(Section.MaterialIndex))
                    {
                        continue;
                    }
                    const FString SlotName = Mesh->GetMaterials()[Section.MaterialIndex]
                        .MaterialSlotName.ToString();
                    if (!SlotName.Contains(TEXT("Eyes"), ESearchCase::IgnoreCase) &&
                        !SlotName.Contains(TEXT("Brows"), ESearchCase::IgnoreCase))
                    {
                        continue;
                    }
                    int32 HeadDominantVertices = 0;
                    int32 NearestSkinHeadDominantVertices = 0;
                    int32 ValidVertices = 0;
                    float MaximumReferenceSeparationCm = 0.0f;
                    TArray<float> ReferenceSeparationsCm;
                    FBox DetailBounds(EForceInit::ForceInit);
                    const uint32 EndVertex =
                        Section.BaseVertexIndex + Section.NumVertices;
                    for (uint32 VertexIndex = Section.BaseVertexIndex;
                         VertexIndex < EndVertex;
                         ++VertexIndex)
                    {
                        const int32 DetailDominantBone =
                            DominantSkeletonBone(Section, VertexIndex);
                        if (DetailDominantBone != INDEX_NONE)
                        {
                            ++ValidVertices;
                            if (DetailDominantBone == HeadBoneIndex)
                            {
                                ++HeadDominantVertices;
                            }
                        }
                        const FVector DetailPosition(
                            LODData.StaticVertexBuffers.PositionVertexBuffer
                                .VertexPosition(VertexIndex));
                        DetailBounds += DetailPosition;
                        const FSkinVertex* NearestSkin = nullptr;
                        float NearestDistanceSquared = TNumericLimits<float>::Max();
                        for (const FSkinVertex& SkinVertex : SkinVertices)
                        {
                            const FVector SkinPosition(
                                LODData.StaticVertexBuffers.PositionVertexBuffer
                                    .VertexPosition(SkinVertex.VertexIndex));
                            const float DistanceSquared = FVector::DistSquared(
                                DetailPosition, SkinPosition);
                            if (DistanceSquared < NearestDistanceSquared)
                            {
                                NearestDistanceSquared = DistanceSquared;
                                NearestSkin = &SkinVertex;
                            }
                        }
                        if (NearestSkin &&
                            DominantSkeletonBone(
                                *NearestSkin->Section,
                                NearestSkin->VertexIndex) == HeadBoneIndex)
                        {
                            ++NearestSkinHeadDominantVertices;
                        }
                        MaximumReferenceSeparationCm = FMath::Max(
                            MaximumReferenceSeparationCm,
                            FMath::Sqrt(NearestDistanceSquared));
                        ReferenceSeparationsCm.Add(FMath::Sqrt(NearestDistanceSquared));
                    }
                    TestEqual(
                        FString::Printf(
                            TEXT("%s %s section has a valid dominant bone for every vertex"),
                            Variant,
                            *SlotName),
                        ValidVertices,
                        static_cast<int32>(Section.NumVertices));
                    TestEqual(
                        FString::Printf(
                            TEXT("%s %s section is rigidly head-dominant after import"),
                            Variant,
                            *SlotName),
                        HeadDominantVertices,
                        static_cast<int32>(Section.NumVertices));
                    TestEqual(
                        FString::Printf(
                            TEXT("%s %s detail is paired to head-dominant facial Skin"),
                            Variant,
                            *SlotName),
                        NearestSkinHeadDominantVertices,
                        static_cast<int32>(Section.NumVertices));
                    ReferenceSeparationsCm.Sort();
                    const float MedianReferenceSeparationCm = ReferenceSeparationsCm[
                        ReferenceSeparationsCm.Num() / 2];
                    const float P95ReferenceSeparationCm = ReferenceSeparationsCm[
                        FMath::Min(
                            ReferenceSeparationsCm.Num() - 1,
                            FMath::RoundToInt(
                                (ReferenceSeparationsCm.Num() - 1) * 0.95f))];
                    AddInfo(FString::Printf(
                        TEXT("%s %s detail bounds min=%s max=%s separation "
                             "median=%.3f p95=%.3f max=%.3f cm"),
                        Variant,
                        *SlotName,
                        *DetailBounds.Min.ToCompactString(),
                        *DetailBounds.Max.ToCompactString(),
                        MedianReferenceSeparationCm,
                        P95ReferenceSeparationCm,
                        MaximumReferenceSeparationCm));
                    TestTrue(
                        FString::Printf(
                            TEXT("%s %s reference p95 separation is at most 1.25 cm "
                                 "(median=%.3f p95=%.3f max=%.3f cm)"),
                            Variant,
                            *SlotName,
                            MedianReferenceSeparationCm,
                            P95ReferenceSeparationCm,
                            MaximumReferenceSeparationCm),
                        P95ReferenceSeparationCm <= 1.25f);
                }
            }
        }
    }

    struct FTextileTextureExpectation
    {
        const TCHAR* TextileName;
        const TCHAR* MapKey;
        bool bSRGB;
        TextureCompressionSettings Compression;
    };
    static const FTextileTextureExpectation TextileTextures[] = {
        {TEXT("RaftCoatedFabric"), TEXT("Albedo"), true, TC_Default},
        {TEXT("RaftCoatedFabric"), TEXT("Normal"), false, TC_Normalmap},
        {TEXT("RaftCoatedFabric"), TEXT("AORoughnessHeight"), false, TC_Masks},
        {TEXT("PfdRipstop"), TEXT("Albedo"), true, TC_Default},
        {TEXT("PfdRipstop"), TEXT("Normal"), false, TC_Normalmap},
        {TEXT("PfdRipstop"), TEXT("AORoughnessHeight"), false, TC_Masks},
        {TEXT("WetsuitNeoprene"), TEXT("Albedo"), true, TC_Default},
        {TEXT("WetsuitNeoprene"), TEXT("Normal"), false, TC_Normalmap},
        {TEXT("WetsuitNeoprene"), TEXT("AORoughnessHeight"), false, TC_Masks},
    };
    for (const FTextileTextureExpectation& Expected : TextileTextures)
    {
        const FString AssetName = FString::Printf(
            TEXT("T_RaftSim_%s_%s"), Expected.TextileName, Expected.MapKey);
        const FString ObjectPath = FString::Printf(
            TEXT("/Game/RaftSim/Equipment/Textures/%s.%s"), *AssetName, *AssetName);
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
        TestNotNull(
            FString::Printf(TEXT("generated textile exists: %s"), *AssetName),
            Texture);
        if (Texture)
        {
            FinishTextureCompilation(Texture);
            TestEqual(
                FString::Printf(TEXT("%s width"), *AssetName),
                Texture->GetSizeX(),
                1024);
            TestEqual(
                FString::Printf(TEXT("%s height"), *AssetName),
                Texture->GetSizeY(),
                1024);
            TestEqual(
                FString::Printf(TEXT("%s sRGB"), *AssetName),
                Texture->SRGB,
                Expected.bSRGB);
            TestEqual(
                FString::Printf(TEXT("%s compression"), *AssetName),
                Texture->CompressionSettings,
                Expected.Compression);
            TestEqual(
                FString::Printf(TEXT("%s wraps X"), *AssetName),
                Texture->AddressX,
                TA_Wrap);
            TestEqual(
                FString::Printf(TEXT("%s wraps Y"), *AssetName),
                Texture->AddressY,
                TA_Wrap);
        }
    }
    static const TCHAR* PfdMaterialPaths[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue")};
    for (const TCHAR* MaterialPath : PfdMaterialPaths)
    {
        UMaterial* Material = LoadObject<UMaterial>(nullptr, MaterialPath);
        TestNotNull(
            FString::Printf(TEXT("production PFD material exists: %s"), MaterialPath),
            Material);
        if (Material)
        {
            TestTrue(
                FString::Printf(TEXT("PFD shell uses Cloth shading: %s"), MaterialPath),
                Material->GetShadingModels().HasShadingModel(MSM_Cloth));
            TestTrue(
                FString::Printf(TEXT("PFD shell retains Nanite usage: %s"), MaterialPath),
                Material->GetUsageByFlag(MATUSAGE_Nanite));
        }
    }
    constexpr int32 ActionCount = static_cast<int32>(ERaftSimCrewAvatarAction::Reentry) + 1;
    TSet<FString> PoseFingerprints;
    for (int32 ActionIndex = 0; ActionIndex < ActionCount; ++ActionIndex)
    {
        const ERaftSimCrewAvatarAction Action =
            static_cast<ERaftSimCrewAvatarAction>(ActionIndex);
        const FRaftSimCrewAvatarPose Pose =
            URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, 0.31f, -1);
        TestTrue(
            FString::Printf(TEXT("action %d pose is finite"), ActionIndex),
            PoseIsFinite(Pose));
        PoseFingerprints.Add(FString::Printf(
            TEXT("%.1f|%.1f|%.1f|%.1f|%.1f|%d"),
            Pose.TorsoCenterCm.X,
            Pose.TorsoCenterCm.Y,
            Pose.TorsoRotation.Pitch,
            Pose.LeftHandCm.X,
            Pose.RightHandCm.Y,
            Pose.bShowPaddle ? 1 : 0));
    }
    TestTrue(TEXT("animation library exposes distinct production poses"), PoseFingerprints.Num() >= 9);

    const FRaftSimCrewAvatarPose Swim = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::Swimming, 0.25f, 1);
    const FRaftSimCrewAvatarPose HighSide = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::HighSidePort, 0.25f, 1);
    const FRaftSimCrewAvatarPose PortSeatHighSide =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            ERaftSimCrewAvatarAction::HighSidePort, 0.25f, -1);
    const FRaftSimCrewAvatarPose Seated = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::SeatedIdle, 0.25f, 1);
    const FRaftSimCrewAvatarPose Forward = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.25f, 1);
    const FRaftSimCrewAvatarPose ForwardCatch = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.0f, 1);
    const FRaftSimCrewAvatarPose ForwardFinish = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.58f, 1);
    const FRaftSimCrewAvatarPose ForwardRecovery = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.79f, 1);
    const FRaftSimCrewAvatarPose ForwardCycleSeam = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.9999f, 1);
    const FRaftSimCrewAvatarPose PortForward = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.25f, -1);
    const FRaftSimCrewAvatarPose StarboardForward = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::ForwardStroke, 0.25f, 1);
    TestFalse(TEXT("swimming hides the paddle"), Swim.bShowPaddle);
    TestTrue(TEXT("high-side retains the emergency paddle"), HighSide.bShowPaddle);
    TestTrue(
        TEXT("high-side keeps both hands on the paddle shaft"),
        FMath::PointDistToSegment(
            HighSide.LeftHandCm,
            HighSide.PaddleTopCm,
            HighSide.PaddleBottomCm) <= 0.5f &&
            FMath::PointDistToSegment(
                HighSide.RightHandCm,
                HighSide.PaddleTopCm,
                HighSide.PaddleBottomCm) <= 0.5f);
    TestTrue(
        TEXT("high-side keeps both seat-side blades low and outside the raft"),
        PortSeatHighSide.PaddleBottomCm.Y < 0.0f &&
            HighSide.PaddleBottomCm.Y > 0.0f &&
            PortSeatHighSide.PaddleBottomCm.Z <= -10.0f &&
            HighSide.PaddleBottomCm.Z <= -10.0f);
    TestTrue(TEXT("high-side visibly shifts the torso"), FMath::Abs(HighSide.TorsoCenterCm.Y) > 25.0f);
    TestTrue(
        TEXT("forward stroke articulates the upper body around the waist"),
        FVector::Distance(Forward.HeadCenterCm, Seated.HeadCenterCm) > 4.0f &&
            FVector::Distance(Forward.LeftShoulderCm, Seated.LeftShoulderCm) > 2.0f);
    TestTrue(
        TEXT("forward stroke has distinct catch and power-finish landmarks"),
        ForwardCatch.PaddleTopCm.X - ForwardFinish.PaddleTopCm.X >= 25.0f &&
            ForwardFinish.PaddleBottomCm.X - ForwardCatch.PaddleBottomCm.X >= 35.0f);
    TestTrue(
        TEXT("forward recovery lifts the blade clear of the planted power path"),
        ForwardRecovery.PaddleBottomCm.Z - ForwardCatch.PaddleBottomCm.Z >= 24.0f);
    TestTrue(
        TEXT("forward stroke remains continuous across the normalized cycle seam"),
        FVector::Distance(ForwardCycleSeam.PaddleTopCm, ForwardCatch.PaddleTopCm) < 0.1f &&
            FVector::Distance(ForwardCycleSeam.PaddleBottomCm, ForwardCatch.PaddleBottomCm) <
                0.1f);
    for (const FRaftSimCrewAvatarPose* StrokePose :
         {&ForwardCatch, &ForwardFinish, &ForwardRecovery})
    {
        TestTrue(
            TEXT("forward stroke keeps both solved hands on the visible paddle shaft"),
            FMath::PointDistToSegment(
                StrokePose->LeftHandCm,
                StrokePose->PaddleTopCm,
                StrokePose->PaddleBottomCm) <= 0.5f &&
                FMath::PointDistToSegment(
                    StrokePose->RightHandCm,
                    StrokePose->PaddleTopCm,
                StrokePose->PaddleBottomCm) <= 0.5f);
    }
    TestTrue(
        TEXT("port and starboard forward-stroke blades stay outboard of their seats"),
        PortForward.PaddleBottomCm.Y < 0.0f &&
            StarboardForward.PaddleBottomCm.Y > 0.0f &&
            PortForward.PaddleTopCm.Y > 0.0f &&
            StarboardForward.PaddleTopCm.Y < 0.0f);
    TestTrue(
        TEXT("port and starboard paddle endpoints are true lateral mirrors"),
        FMath::IsNearlyEqual(
            PortForward.PaddleTopCm.Y,
            -StarboardForward.PaddleTopCm.Y,
            0.01f) &&
            FMath::IsNearlyEqual(
                PortForward.PaddleBottomCm.Y,
                -StarboardForward.PaddleBottomCm.Y,
                0.01f));
    TestTrue(
        TEXT("mirrored forward grips put the anatomical outboard hand down-shaft"),
        FVector::Distance(PortForward.RightHandCm, PortForward.PaddleTopCm) <= 0.5f &&
            FVector::Distance(
                StarboardForward.LeftHandCm,
                StarboardForward.PaddleTopCm) <= 0.5f &&
            FMath::PointDistToSegment(
                PortForward.LeftHandCm,
                PortForward.PaddleTopCm,
                PortForward.PaddleBottomCm) <= 0.5f &&
            FMath::PointDistToSegment(
                StarboardForward.RightHandCm,
                StarboardForward.PaddleTopCm,
                StarboardForward.PaddleBottomCm) <= 0.5f);
    TSet<int32> CrewTimingOffsetsMillis;
    for (int32 Variant = 0; Variant < 4; ++Variant)
    {
        const float Offset =
            URaftSimCrewAvatarPoseLibrary::GetDeterministicTimingOffset(Variant, false);
        TestTrue(TEXT("paddler timing offset stays within trained-crew tolerance"),
                 FMath::Abs(Offset) <= 0.04f);
        CrewTimingOffsetsMillis.Add(FMath::RoundToInt(Offset * 1000.0f));
    }
    const float GuideTimingOffset =
        URaftSimCrewAvatarPoseLibrary::GetDeterministicTimingOffset(0, true);
    TestTrue(TEXT("guide timing offset stays within coordinated cadence tolerance"),
             FMath::Abs(GuideTimingOffset) <= 0.05f);
    CrewTimingOffsetsMillis.Add(FMath::RoundToInt(GuideTimingOffset * 1000.0f));
    TestEqual(TEXT("all five crew timing offsets are deterministic and distinct"),
              CrewTimingOffsetsMillis.Num(), 5);
    const float TorsoShift = HighSide.TorsoCenterCm.Y - Seated.TorsoCenterCm.Y;
    const auto RelativeShift = [&HighSide, &Seated](
        FVector FRaftSimCrewAvatarPose::* Member)
    {
        return (HighSide.*Member).Y - (Seated.*Member).Y;
    };
    const float LeftShoulderArticulationCm = FMath::Abs(
        RelativeShift(&FRaftSimCrewAvatarPose::LeftShoulderCm) - TorsoShift);
    const float RightShoulderArticulationCm = FMath::Abs(
        RelativeShift(&FRaftSimCrewAvatarPose::RightShoulderCm) - TorsoShift);
    TestTrue(
        FString::Printf(
            TEXT("high-side shoulders follow the torso with a coherent anatomical lean "
                 "(left=%.2f cm right=%.2f cm)"),
            LeftShoulderArticulationCm,
            RightShoulderArticulationCm),
        LeftShoulderArticulationCm >= 5.0f &&
            RightShoulderArticulationCm >= 5.0f &&
            // A rigid 34 cm shoulder span rolled 28 degrees produces about
            // 3.98 cm of unequal world-Y travel between its endpoints.
            FMath::Abs(
                LeftShoulderArticulationCm - RightShoulderArticulationCm) <= 4.5f);
    TestTrue(
        TEXT("high-side head visibly leans beyond the translated PFD centre"),
        FMath::Abs(HighSide.HeadCenterCm.Y - HighSide.TorsoCenterCm.Y) >= 10.0f);
    TestTrue(
        TEXT("high-side pelvis follows the torso and attached PFD"),
        FMath::Abs(RelativeShift(&FRaftSimCrewAvatarPose::LeftHipCm)) >=
            FMath::Abs(TorsoShift) * 0.80f &&
            FMath::Abs(RelativeShift(&FRaftSimCrewAvatarPose::RightHipCm)) >=
                FMath::Abs(TorsoShift) * 0.80f);
    TestTrue(
        TEXT("high-side knees follow the commanded side"),
        FMath::Sign(RelativeShift(&FRaftSimCrewAvatarPose::LeftKneeCm)) ==
            FMath::Sign(TorsoShift) &&
            FMath::Sign(RelativeShift(&FRaftSimCrewAvatarPose::RightKneeCm)) ==
                FMath::Sign(TorsoShift));
    TestTrue(
        TEXT("high-side boots remain planted but do not stay on the rejected pose"),
        FMath::Abs(RelativeShift(&FRaftSimCrewAvatarPose::LeftFootCm)) >= 12.0f &&
            FMath::Abs(RelativeShift(&FRaftSimCrewAvatarPose::RightFootCm)) >= 12.0f &&
            FMath::Abs(RelativeShift(&FRaftSimCrewAvatarPose::LeftFootCm)) <
                FMath::Abs(TorsoShift));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5AimedRescueTest,
    "RaftSim.M5.AimedRescuePaths",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5AimedRescueTest::RunTest(const FString&)
{
    const FRaftSimSwimmingSkillProfile Skill =
        URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(
            ERaftSimSwimmingSkillLevel::AverageSwimmer);
    const FVector Start(0.0f, 0.0f, 0.0f);
    const FVector Target(5.0f, 0.0f, 0.0f);
    FRaftSimRescueInteractionState State =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"),
            ERaftSimRescueMethod::ThrowLine,
            Start,
            Target,
            FVector::ForwardVector,
            true,
            4.0f,
            Skill);
    TestEqual(
        TEXT("aligned throw enters flight"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::LineInFlight));
    TestTrue(TEXT("throw line is visible"), State.bLineVisible);

    for (int32 Step = 0; Step < 28; ++Step)
    {
        State = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
            State, Start, Target, 0.25f);
    }
    TestEqual(
        TEXT("elapsed-time pull reaches re-entry"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    State = URaftSimSwimmerRescueLibrary::CompleteReseat(State, 0.9f);
    TestEqual(
        TEXT("tube-side reseat completes"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Completed));
    TestFalse(TEXT("line is stowed after reseat"), State.bLineVisible);

    auto TestContactRescue = [this, &Skill, &Start](
        const TCHAR* Label,
        ERaftSimRescueMethod Method,
        float DistanceM,
        int32 PullSteps)
    {
        FRaftSimRescueInteractionState ContactState =
            URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
                TEXT("paddler_contact"), Method, Start, FVector(DistanceM, 0.0f, 0.0f),
                FVector::ForwardVector, true, 2.0f, Skill);
        TestEqual(
            FString::Printf(TEXT("%s establishes contact"), Label),
            static_cast<int32>(ContactState.Phase),
            static_cast<int32>(ERaftSimRescueInteractionPhase::Pulling));
        for (int32 Step = 0; Step < PullSteps; ++Step)
        {
            ContactState = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
                ContactState, Start, FVector(DistanceM, 0.0f, 0.0f), 0.25f);
        }
        TestEqual(
            FString::Printf(TEXT("%s completes its calibrated pull"), Label),
            static_cast<int32>(ContactState.Phase),
            static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    };
    TestContactRescue(TEXT("reach grab"), ERaftSimRescueMethod::ReachGrab, 1.0f, 10);
    TestContactRescue(TEXT("paddle grab"), ERaftSimRescueMethod::PaddleGrab, 1.8f, 14);

    const FRaftSimRescueInteractionState BadAim =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"), ERaftSimRescueMethod::ThrowLine,
            Start, Target, -FVector::ForwardVector, true, 4.0f, Skill);
    TestEqual(
        TEXT("bad throw remains in aiming feedback"),
        static_cast<int32>(BadAim.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Aiming));
    const FRaftSimRescueInteractionState OutOfRange =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"), ERaftSimRescueMethod::PaddleGrab,
            Start, Target, FVector::ForwardVector, true, 4.0f, Skill);
    TestEqual(
        TEXT("paddle grab enforces its physical reach"),
        static_cast<int32>(OutOfRange.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Failed));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5FlexibleFabricConditionTest,
    "RaftSim.M5.FlexibleFabricCondition",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5FlexibleFabricConditionTest::RunTest(const FString&)
{
    FRaftSimFlexVisualSegmentState Contact;
    Contact.SegmentId = TEXT("port_mid_wrap");
    Contact.LocalPositionM = FVector(0.6f, -0.72f, 0.28f);
    Contact.ContactNormalLocal = FVector(0.0f, 1.0f, 0.0f);
    Contact.CompressionM = 0.07;
    Contact.IndentationM = 0.14;
    Contact.FreeboardLossM = 0.05;
    Contact.bWrapping = true;
    Contact.bPinned = true;

    UStaticMesh* ProductionRaft = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft."
             "SM_RaftSim_ProductionPaddleRaft"));
    TestNotNull(TEXT("production paddle-raft rest mesh loads"), ProductionRaft);
    if (ProductionRaft)
    {
        TestEqual(TEXT("production raft has five material slots"),
                  ProductionRaft->GetStaticMaterials().Num(), 5);
        TestTrue(TEXT("production raft retains CPU-readable cooked topology"),
                 ProductionRaft->bAllowCPUAccess);
        TestTrue(TEXT("production raft has authored high-detail topology"),
                 ProductionRaft->GetNumTriangles(0) >= 30000);

        TArray<RaftSimRaftMesh::FMeshData> ProductionRest;
        TArray<RaftSimRaftMesh::FMeshData> ProductionBent;
        TestTrue(TEXT("production raft rest topology extracts"),
                 RaftSimRaftMesh::ExtractProductionRaftRestMesh(
                     ProductionRaft, ProductionRest));
        TestEqual(TEXT("production raft extraction preserves five sections"),
                  ProductionRest.Num(), 5);
        if (ProductionRest.Num() == 5)
        {
            RaftSimRaftMesh::DeformProductionRaftRestMesh(
                ProductionRest, 0.28f, {Contact}, {}, ProductionBent);
            RaftSimRaftMesh::FProductionRaftDeformationCache ProductionCache;
            TArray<RaftSimRaftMesh::FMeshData> ProductionCached;
            RaftSimRaftMesh::DeformProductionRaftRestMesh(
                ProductionRest, 0.28f, {Contact}, {}, ProductionCached,
                &ProductionCache);
            // Exercise the persistent-buffer path as it runs after warmup.
            RaftSimRaftMesh::DeformProductionRaftRestMesh(
                ProductionRest, 0.28f, {Contact}, {}, ProductionCached,
                &ProductionCache);
            TestEqual(TEXT("production deformation preserves section count"),
                      ProductionBent.Num(), ProductionRest.Num());
            float ProductionMaximumMoveCm = 0.0f;
            float ProductionMaximumNormalDelta = 0.0f;
            bool bProductionFiniteAndStable = ProductionBent.Num() == ProductionRest.Num();
            for (int32 SectionIndex = 0;
                 bProductionFiniteAndStable && SectionIndex < ProductionRest.Num();
                 ++SectionIndex)
            {
                const RaftSimRaftMesh::FMeshData& RestSection =
                    ProductionRest[SectionIndex];
                const RaftSimRaftMesh::FMeshData& BentSection =
                    ProductionBent[SectionIndex];
                bProductionFiniteAndStable &=
                    !RestSection.Vertices.IsEmpty() &&
                    BentSection.Vertices.Num() == RestSection.Vertices.Num() &&
                    BentSection.Normals.Num() == RestSection.Normals.Num() &&
                    BentSection.Tangents.Num() == RestSection.Tangents.Num() &&
                    BentSection.Triangles == RestSection.Triangles &&
                    ProductionCached.IsValidIndex(SectionIndex) &&
                    ProductionCached[SectionIndex].Triangles == RestSection.Triangles &&
                    ProductionCached[SectionIndex].UVs == RestSection.UVs;
                for (int32 VertexIndex = 0;
                     bProductionFiniteAndStable &&
                     VertexIndex < RestSection.Vertices.Num();
                     ++VertexIndex)
                {
                    bProductionFiniteAndStable &=
                        !BentSection.Vertices[VertexIndex].ContainsNaN() &&
                        !BentSection.Normals[VertexIndex].ContainsNaN() &&
                        !BentSection.Tangents[VertexIndex].TangentX.ContainsNaN() &&
                        FMath::IsNearlyEqual(
                            BentSection.Normals[VertexIndex].SizeSquared(), 1.0f, 0.02f) &&
                        FMath::IsNearlyEqual(
                            BentSection.Tangents[VertexIndex].TangentX.SizeSquared(),
                            1.0f,
                            0.02f) &&
                        ProductionCached[SectionIndex].Vertices[VertexIndex].Equals(
                            BentSection.Vertices[VertexIndex], 1.0e-3f) &&
                        ProductionCached[SectionIndex].Normals[VertexIndex].Equals(
                            BentSection.Normals[VertexIndex], 1.0e-3f) &&
                        ProductionCached[SectionIndex].Tangents[VertexIndex].TangentX.Equals(
                            BentSection.Tangents[VertexIndex].TangentX, 1.0e-3f);
                    ProductionMaximumMoveCm = FMath::Max(
                        ProductionMaximumMoveCm,
                        FVector::Distance(
                            RestSection.Vertices[VertexIndex],
                            BentSection.Vertices[VertexIndex]));
                    ProductionMaximumNormalDelta = FMath::Max(
                        ProductionMaximumNormalDelta,
                        1.0f - FVector::DotProduct(
                            RestSection.Normals[VertexIndex],
                            BentSection.Normals[VertexIndex]));
                }
            }
            TestTrue(TEXT("production topology stays finite and indexed through D4"),
                     bProductionFiniteAndStable);
            TestTrue(TEXT("production deformation cache binds authored vertices"),
                     ProductionCache.Sections.Num() == ProductionRest.Num() &&
                     !ProductionCache.Sections[0].Influences.IsEmpty());
            TestTrue(TEXT("production raft visibly follows the D4 contact field"),
                     ProductionMaximumMoveCm > 8.0f);
            TestTrue(TEXT("production wrap projection stays within a 90 cm visual bound"),
                     ProductionMaximumMoveCm < 90.0f);
            TestTrue(TEXT("production raft lighting frame follows the D4 contact field"),
                     ProductionMaximumNormalDelta > 0.01f);
        }
    }

    RaftSimRaftMesh::FMeshData RestTubes, RestFloor, RestRigging, RestMetal, RestRubber;
    RaftSimRaftMesh::FMeshData BentTubes, BentFloor, BentRigging, BentMetal, BentRubber;
    RaftSimRaftMesh::BuildInflatableRaft(
        4.3f, 2.0f, 0.28f, RestTubes, RestFloor, {}, {}, &RestRigging,
        &RestMetal, &RestRubber);
    RaftSimRaftMesh::BuildInflatableRaft(
        4.3f, 2.0f, 0.28f, BentTubes, BentFloor, {Contact}, {}, &BentRigging,
        &BentMetal, &BentRubber);
    TestEqual(TEXT("tube topology remains stable"), BentTubes.Vertices.Num(), RestTubes.Vertices.Num());
    TestEqual(TEXT("floor topology remains stable"), BentFloor.Vertices.Num(), RestFloor.Vertices.Num());
    TestEqual(TEXT("rigging topology remains stable"), BentRigging.Vertices.Num(), RestRigging.Vertices.Num());
    TestEqual(TEXT("D-ring topology remains stable"), BentMetal.Vertices.Num(), RestMetal.Vertices.Num());
    TestEqual(TEXT("rubber-detail topology remains stable"), BentRubber.Vertices.Num(), RestRubber.Vertices.Num());
    TestTrue(TEXT("commercial raft has perimeter rigging"), RestRigging.Vertices.Num() > 500);
    TestTrue(TEXT("commercial raft has four modeled D-rings"), RestMetal.Vertices.Num() >= 384);
    TestTrue(TEXT("commercial raft has chafe strips pads collars welds valves and handles"),
             RestRubber.Vertices.Num() >= 850);
    TestTrue(TEXT("self-bailing floor has non-planar I-beam relief"),
             RestFloor.Vertices[0].Z > RestFloor.Vertices[17].Z + 0.5f);

    float MaxTubeMove = 0.0f;
    float MaxThwartMove = 0.0f;
    float MaxFloorMove = 0.0f;
    float MaxRiggingMove = 0.0f;
    float MaxMetalMove = 0.0f;
    float MaxRubberMove = 0.0f;
    bool bFinite = true;
    for (int32 Index = 0; Index < RestTubes.Vertices.Num(); ++Index)
    {
        bFinite &= !BentTubes.Vertices[Index].ContainsNaN();
        const float Move = FVector::Distance(RestTubes.Vertices[Index], BentTubes.Vertices[Index]);
        MaxTubeMove = FMath::Max(MaxTubeMove, Move);
        if (Index >= RestTubes.Vertices.Num() - 220)
        {
            MaxThwartMove = FMath::Max(MaxThwartMove, Move);
        }
    }
    for (int32 Index = 0; Index < RestFloor.Vertices.Num(); ++Index)
    {
        bFinite &= !BentFloor.Vertices[Index].ContainsNaN();
        MaxFloorMove = FMath::Max(
            MaxFloorMove,
            FVector::Distance(RestFloor.Vertices[Index], BentFloor.Vertices[Index]));
    }
    for (int32 Index = 0; Index < RestRigging.Vertices.Num(); ++Index)
    {
        bFinite &= !BentRigging.Vertices[Index].ContainsNaN();
        MaxRiggingMove = FMath::Max(
            MaxRiggingMove,
            FVector::Distance(RestRigging.Vertices[Index], BentRigging.Vertices[Index]));
    }
    for (int32 Index = 0; Index < RestMetal.Vertices.Num(); ++Index)
    {
        bFinite &= !BentMetal.Vertices[Index].ContainsNaN();
        MaxMetalMove = FMath::Max(
            MaxMetalMove,
            FVector::Distance(RestMetal.Vertices[Index], BentMetal.Vertices[Index]));
    }
    for (int32 Index = 0; Index < RestRubber.Vertices.Num(); ++Index)
    {
        bFinite &= !BentRubber.Vertices[Index].ContainsNaN();
        MaxRubberMove = FMath::Max(
            MaxRubberMove,
            FVector::Distance(RestRubber.Vertices[Index], BentRubber.Vertices[Index]));
    }
    TestTrue(TEXT("deformed fabric remains finite"), bFinite);
    TestTrue(TEXT("wrap creates a visible tube fold"), MaxTubeMove > 8.0f);
    TestTrue(TEXT("thwarts couple to the fold"), MaxThwartMove > 0.5f);
    TestTrue(TEXT("floor couples to the fold"), MaxFloorMove > 0.5f);
    TestTrue(TEXT("grab line couples to the fold"), MaxRiggingMove > 0.5f);
    TestTrue(TEXT("D-rings couple to the fold"), MaxMetalMove > 0.25f);
    TestTrue(TEXT("reinforcement construction couples to the fold"), MaxRubberMove > 0.5f);

    // The first swept ring has eighteen vertices. Reciprocal contact axes
    // preserve its polygonal cross-sectional area within discretization error.
    const float RestArea = RingPolygonArea(RestTubes.Vertices, 0, 18);
    const float BentArea = RingPolygonArea(BentTubes.Vertices, 0, 18);
    TestTrue(
        FString::Printf(TEXT("inflated cross-section conserves area (ratio %.3f)"), BentArea / RestArea),
        FMath::Abs(BentArea / RestArea - 1.0f) < 0.06f);

    FRaftSimRaftConditionState Condition;
    FRaftSimRaftContactExposure Exposure;
    Exposure.DeltaSeconds = 0.25f;
    Exposure.MaximumIndentationM = 0.18f;
    Exposure.ContactCount = 5;
    Exposure.WrappingContactCount = 4;
    Exposure.PinnedObstacleCount = 1;
    for (int32 Step = 0; Step < 48; ++Step)
    {
        Condition = URaftSimRaftConditionLibrary::AdvanceCondition(Condition, Exposure);
    }
    TestTrue(TEXT("sustained pin damages fabric"), Condition.FabricIntegrity < 0.75f);
    TestTrue(TEXT("sustained deep pin leaks pressure"), Condition.PressureFraction < 0.90f);
    TestTrue(TEXT("wrap event is edge-counted once"), Condition.WrapEventCount == 1);
    TestTrue(
        TEXT("condition advances to punctured or critical"),
        Condition.DamageState == ERaftSimRaftDamageState::Punctured ||
            Condition.DamageState == ERaftSimRaftDamageState::Critical);
    const FRaftSimRaftConditionState Repaired =
        URaftSimRaftConditionLibrary::ApplyCheckpointRepair(Condition);
    TestEqual(TEXT("field repair restores nominal pressure"), Repaired.PressureFraction, 1.0f);
    TestTrue(TEXT("field repair preserves the crease history"),
             Repaired.PermanentCreaseAmplitudeM > 0.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5RuntimeRescueLoopTest,
    "RaftSim.M5.RuntimeRescueLoop",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM5StartRescueCommand, FAutomationTestBase*, Test);
bool FRaftSimM5StartRescueCommand::Update()
{
    const bool bRaftArtReview =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimRaftArtReview"));
    ARaftSimRaftActor* Raft = FindM5Raft();
    if (!Raft)
    {
        Test->AddError(TEXT("M5 test tank has no raft"));
        return true;
    }
    Test->TestEqual(TEXT("five crew avatars spawned"), Raft->GetCrewAvatarCount(), 5);
    Test->TestTrue(TEXT("authored production raft drives the collisionless D4 visual"),
                   Raft->HasProductionWhitewaterRaft());
    Test->TestFalse(TEXT("raft orientation is finite before rescue"),
                    Raft->GetActorQuat().ContainsNaN());
    Test->TestFalse(TEXT("raft position is finite before rescue"),
                    Raft->GetActorLocation().ContainsNaN());
    ARaftSimGuidePawn* Guide = FindM5Guide();
    Test->TestNotNull(TEXT("test tank has guide pawn"), Guide);
    if (Guide)
    {
        Test->TestTrue(TEXT("shipping rescue input bindings are complete"),
                       Guide->HasCompleteRescueInputBindings());
    }
    Raft->ForceCrewOverboardForTesting(1);
    FVector TargetCm;
    if (!Raft->GetSwimmerWorldPosition(TEXT("paddler_1"), TargetCm))
    {
        Test->AddError(TEXT("forced passenger did not become a swimmer"));
        return true;
    }
    Test->TestFalse(TEXT("spawned swimmer position is finite"), TargetCm.ContainsNaN());
    TSet<FString> BodyProfiles;
    TSet<FString> SkinTones;
    int32 RiggedBodyCount = 0;
    const bool bForceCC0Review =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimForceCC0Review"));
    if (bForceCC0Review)
    {
        for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
        {
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s activates the packaged CC0 validation path"),
                    *It->GetName()),
                It->ActivateCC0FallbackForValidation());
        }
    }
    const bool bAssembledMetaHumanRoster =
        ARaftSimMetaHumanCrewVisualActor::AreAllProductionCharactersAvailable();
    const bool bExpectCC0Roster =
        bForceCC0Review || !bAssembledMetaHumanRoster;
    int32 CC0BodyCount = 0;
    for (TActorIterator<ARaftSimCC0CrewVisualActor> It(GetM5GameWorld()); It; ++It)
    {
        ++CC0BodyCount;
        ++RiggedBodyCount;
        Test->TestTrue(
            FString::Printf(TEXT("CC0 crew body %s loaded"), *It->GetName()),
            It->IsBodyReady());
        Test->TestTrue(
            FString::Printf(TEXT("CC0 crew body %s has finite pose"), *It->GetName()),
            It->HasFinitePose());
        Test->TestTrue(
            FString::Printf(TEXT("CC0 crew body %s selected packaged mesh"), *It->GetName()),
            It->GetSelectedMeshPath().Contains(TEXT("/Production/CC0/SK_RaftSim_CC0_")));
    }
    Test->TestEqual(
        TEXT("CC0 roster is used exactly when assembled production art is unavailable"),
        CC0BodyCount,
        bExpectCC0Roster ? 5 : 0);
    int32 MetaHumanBodyCount = 0;
    for (TActorIterator<ARaftSimMetaHumanCrewVisualActor> It(GetM5GameWorld()); It; ++It)
    {
        ++MetaHumanBodyCount;
        ++RiggedBodyCount;
        Test->TestTrue(
            FString::Printf(TEXT("assembled MetaHuman crew %s loaded"), *It->GetName()),
            It->IsBodyReady());
        Test->TestTrue(
            FString::Printf(TEXT("MetaHuman crew %s has finite pose"), *It->GetName()),
            It->HasFinitePose());
        Test->TestTrue(
            FString::Printf(TEXT("MetaHuman crew %s renders an assembled character"), *It->GetName()),
            It->IsUsingAssembledCharacter());
        Test->TestTrue(
            FString::Printf(
                TEXT("MetaHuman crew %s retains wardrobe, hair, brows, and lashes"),
                *It->GetName()),
            It->HasCompleteAssembledPresentation());
        Test->TestTrue(
            FString::Printf(
                TEXT("MetaHuman crew %s exposes articulated paddle-grip digits"),
                *It->GetName()),
            It->HasArticulatedPaddleGripRig());
        Test->TestTrue(
            FString::Printf(
                TEXT("MetaHuman crew %s keeps its palm on the solved grip "
                     "(error %.3f cm)"),
                *It->GetName(),
                It->GetMaximumPaddleGripAnchorErrorCm()),
            It->GetMaximumPaddleGripAnchorErrorCm() <= 0.25f);
        Test->TestTrue(
            FString::Printf(
                TEXT("MetaHuman crew %s centres its closed fingers on the solved grip "
                     "(error %.3f cm)"),
                *It->GetName(),
                It->GetMaximumPaddleGripContactErrorCm()),
            It->GetMaximumPaddleGripContactErrorCm() <= 0.25f);
    }
    Test->TestEqual(
        TEXT("assembled roster is all-or-nothing"),
        MetaHumanBodyCount,
        bExpectCC0Roster ? 0 : 5);
    int32 MannyBodyCount = 0;
    for (TActorIterator<ARaftSimMannyCrewVisualActor> It(GetM5GameWorld()); It; ++It)
    {
        ++MannyBodyCount;
        ++RiggedBodyCount;
        Test->TestTrue(
            FString::Printf(TEXT("rigged crew body %s loaded"), *It->GetName()),
            It->IsBodyReady());
        Test->TestTrue(
            FString::Printf(TEXT("rigged crew body %s has finite pose"), *It->GetName()),
            It->HasFinitePose());
    }
    Test->TestEqual(TEXT("Manny fallback is absent with packaged CC0 bodies"), MannyBodyCount, 0);
    Test->TestEqual(TEXT("five rigged crew bodies spawned"), RiggedBodyCount, 5);
    int32 SwimmingPfdCount = 0;
    for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
    {
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s has layered production gear"), *It->GetName()),
            It->GetProceduralBodyPartCount() >= 28 && It->HasLayeredCommercialSafetyGear() &&
            It->HasCommercialPaddleSilhouette() &&
                It->HasBatchedFacialFeatures());
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s uses the production whitewater helmet"), *It->GetName()),
            It->HasProductionWhitewaterHelmet());
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s uses the production whitewater rescue PFD"), *It->GetName()),
            It->HasProductionWhitewaterPfd());
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s owns a live PFD material response"), *It->GetName()),
            It->HasLivePfdMaterialResponse());
        Test->TestTrue(
            FString::Printf(
                TEXT("avatar %s owns a live splash-jacket cloth response"),
                *It->GetName()),
            It->HasLiveSplashJacketMaterialResponse());
        const float PfdWetness = It->GetPfdPresentationWetness();
        Test->TestTrue(
            FString::Printf(
                TEXT("avatar %s keeps bounded presentation PFD wetness (%.4f)"),
                *It->GetName(),
                PfdWetness),
            PfdWetness >= 0.0f && PfdWetness <= 0.84f);
        if (It->GetAvatarAction() == ERaftSimCrewAvatarAction::Swimming)
        {
            ++SwimmingPfdCount;
            Test->TestTrue(
                FString::Printf(
                    TEXT("swimming avatar %s immediately saturates its PFD (%.4f)"),
                    *It->GetName(),
                    PfdWetness),
                PfdWetness >= 0.82f);
        }
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s uses two production river boots"), *It->GetName()),
            It->HasProductionRiverBoots());
        Test->TestTrue(
            FString::Printf(
                TEXT("avatar %s keeps both fitted production boots sole-down"),
                *It->GetName()),
            It->HasFittedUprightProductionRiverBoots());
        Test->TestEqual(
            FString::Printf(TEXT("avatar %s facial batching count"), *It->GetName()),
            It->GetBatchedFacialSubmeshCount(),
            17);
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s starts rescue with finite transforms"), *It->GetName()),
            It->HasFiniteVisualTransforms());
        Test->TestEqual(
            FString::Printf(TEXT("avatar %s has one exclusive visual path"), *It->GetName()),
            It->IsUsingProductionVisual(),
            !It->UsesProjectOwnedProceduralGeometry());
        Test->TestFalse(
            FString::Printf(TEXT("avatar %s exposes a deterministic production class slot"), *It->GetName()),
            It->GetProductionVisualClassPath().IsEmpty());
        if (Cast<ARaftSimCC0CrewVisualActor>(It->GetProductionVisualActor()))
        {
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s gives its complete CC0 mesh exclusive body ownership"),
                    *It->GetName()),
                It->HasExclusiveCC0BodyOwnership());
            const float HelmetHeadErrorCm = It->GetProductionHelmetHeadErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps helmet on the rendered CC0 face "
                         "(error %.3f cm)"),
                    *It->GetName(),
                    HelmetHeadErrorCm),
                HelmetHeadErrorCm <= 1.0f);
            const float HelmetForwardAlignment =
                It->GetProductionHelmetForwardAlignment();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s points the CC0 helmet brow with the rendered face "
                         "(alignment %.4f)"),
                    *It->GetName(),
                    HelmetForwardAlignment),
                HelmetForwardAlignment >= 0.98f);
            const float HelmetFitScale = It->GetProductionHelmetFitScale();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s uses a bounded CC0 helmet fit (scale %.4f)"),
                    *It->GetName(),
                    HelmetFitScale),
                HelmetFitScale >= 0.90f && HelmetFitScale <= 1.02f);
        }
        else if (Cast<ARaftSimMetaHumanCrewVisualActor>(It->GetProductionVisualActor()))
        {
            const float HelmetHeadErrorCm =
                It->GetProductionHelmetHeadErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps helmet on the solved production head "
                         "(error %.3f cm)"),
                    *It->GetName(),
                    HelmetHeadErrorCm),
                HelmetHeadErrorCm <= 1.0f);
            const float HelmetForwardAlignment =
                It->GetProductionHelmetForwardAlignment();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s points the helmet brow with the rendered face "
                         "(alignment %.4f)"),
                    *It->GetName(),
                    HelmetForwardAlignment),
                HelmetForwardAlignment >= 0.98f);
            const float HelmetFitScale = It->GetProductionHelmetFitScale();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s uses a bounded identity-calibrated helmet fit "
                         "(scale %.4f)"),
                    *It->GetName(),
                    HelmetFitScale),
                HelmetFitScale >= 0.90f && HelmetFitScale <= 1.02f);
            const float PfdTorsoErrorCm = It->GetProductionPfdTorsoErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps rescue PFD on the solved torso "
                         "(error %.3f cm)"),
                    *It->GetName(),
                    PfdTorsoErrorCm),
                PfdTorsoErrorCm <= 1.0f);
            const FVector WaistHipExtentCm = It->GetWaistHipExtentCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s retains a visible seated waist/hip silhouette "
                         "(extent %s)"),
                    *It->GetName(),
                    *WaistHipExtentCm.ToCompactString()),
                It->HasVisibleWaistHipSilhouette());
            const float WaistHipCenterErrorCm =
                It->GetWaistHipCenterErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps the visible pelvis on the solved hip centre "
                         "(error %.3f cm)"),
                    *It->GetName(),
                    WaistHipCenterErrorCm),
                WaistHipCenterErrorCm <= 0.1f);
            const FVector HipThighBridgeExtentCm =
                It->GetMinimumHipThighBridgeExtentCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps opaque wetsuit thigh roots under the pelvis "
                         "(minimum extent %s)"),
                    *It->GetName(),
                    *HipThighBridgeExtentCm.ToCompactString()),
                It->IsWaistHipMaterialOpaque() &&
                    HipThighBridgeExtentCm.X >= 7.2f &&
                    HipThighBridgeExtentCm.Y >= 7.2f &&
                    HipThighBridgeExtentCm.Z >= 15.5f);
            const float HipThighCoverageErrorCm =
                It->GetMaximumHipThighBridgeCoverageErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s buries both profile hip junctions inside their "
                         "bridges (maximum centreline error %.3f cm)"),
                    *It->GetName(),
                    HipThighCoverageErrorCm),
                HipThighCoverageErrorCm <= 0.25f);
            const float ThighKneeCoverageErrorCm =
                It->GetMaximumThighKneeBridgeCoverageErrorCm();
            const int32 ThighMeshVertexCount =
                It->GetMinimumThighMeshVertexCount();
            const float ThighForwardAlignment =
                It->GetMinimumThighForwardAlignment();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s carries directional anatomical thighs through "
                         "both solved knees (minimum %d vertices, anterior alignment "
                         "%.3f, maximum centreline error %.3f cm)"),
                    *It->GetName(),
                    ThighMeshVertexCount,
                    ThighForwardAlignment,
                    ThighKneeCoverageErrorCm),
                It->HasContinuousThighKneeSilhouette() &&
                    ThighMeshVertexCount >= 650 &&
                    ThighForwardAlignment >= 0.98f &&
                    ThighKneeCoverageErrorCm <= 0.25f);
            const FVector ShoulderSleeveExtentCm =
                It->GetMinimumShoulderSleeveExtentCm();
            const int32 ShoulderSleeveVertexCount =
                It->GetMinimumShoulderSleeveVertexCount();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s retains folded cloth shoulders between the PFD and "
                         "arms (minimum extent %s, %d vertices)"),
                    *It->GetName(),
                    *ShoulderSleeveExtentCm.ToCompactString(),
                    ShoulderSleeveVertexCount),
                It->HasVisibleShoulderSilhouette() &&
                    ShoulderSleeveVertexCount >= 1000);
            const float ShoulderAnchorErrorCm =
                It->GetMaximumShoulderSleeveAnchorErrorCm();
            Test->TestTrue(
                FString::Printf(
                    TEXT("avatar %s keeps both deltoids on the solved shoulder joints "
                         "(maximum error %.3f cm)"),
                    *It->GetName(),
                    ShoulderAnchorErrorCm),
                ShoulderAnchorErrorCm <= 0.25f);
        }
        BodyProfiles.Add(It->GetBodyProportionScale().ToCompactString());
        SkinTones.Add(It->GetSkinTone().ToString());
    }
    Test->TestEqual(
        TEXT("exactly one forced swimmer owns the drenched PFD response"),
        SwimmingPfdCount,
        1);
    Test->TestTrue(TEXT("crew exposes at least four deterministic body profiles"),
                   BodyProfiles.Num() >= 4);
    Test->TestTrue(TEXT("crew exposes at least four deterministic skin tones"),
                   SkinTones.Num() >= 4);
    Raft->AimRescue(TargetCm - Raft->GetActorLocation());
    Test->TestTrue(TEXT("aimed throw-line starts"), Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    if (bRaftArtReview)
    {
        // Keep the normal rescue test and its assertions intact, but remove
        // crew occlusion from an explicitly requested art-review frame. This
        // is renderer evidence only and never changes a gameplay path.
        for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
        {
            It->SetActorHiddenInGame(true);
        }
        for (TActorIterator<ARaftSimCC0CrewVisualActor> It(GetM5GameWorld()); It; ++It)
        {
            It->SetActorHiddenInGame(true);
        }
        for (TActorIterator<ARaftSimMetaHumanCrewVisualActor> It(GetM5GameWorld()); It; ++It)
        {
            It->SetActorHiddenInGame(true);
        }
    }
    if (Guide && Guide->GetGuideCamera())
    {
        Guide->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        // The production guide camera is comfort-filtered every pawn tick.
        // Freeze that runtime controller and make this evidence camera absolute
        // so the screenshot remains on the crew-facing side of the raft.
        Guide->SetActorTickEnabled(false);
        UCameraComponent* Camera = Guide->GetGuideCamera();
        Camera->bUsePawnControlRotation = false;
        Camera->SetUsingAbsoluteLocation(true);
        Camera->SetUsingAbsoluteRotation(true);
        // The empty test tank is intentionally much brighter than the shipping
        // canyon. Override the runtime +1.75 EV bias only for this evidence
        // camera so white ground/sky cannot clip the raft, faces and PPE.
        FPostProcessSettings& EvidenceSettings = Camera->PostProcessSettings;
        EvidenceSettings.bOverride_AutoExposureMethod = true;
        EvidenceSettings.AutoExposureMethod = AEM_Manual;
        EvidenceSettings.bOverride_AutoExposureBias = true;
        EvidenceSettings.AutoExposureBias = -1.25f;
        EvidenceSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        EvidenceSettings.AutoExposureApplyPhysicalCameraExposure = 0;
        Camera->PostProcessBlendWeight = 1.0f;
        const FVector ViewLocation = Raft->GetActorLocation() +
            Raft->GetActorForwardVector() * (bRaftArtReview ? 700.0f : 440.0f) +
            Raft->GetActorRightVector() * (bRaftArtReview ? 450.0f : 220.0f) +
            FVector(0.0f, 0.0f, bRaftArtReview ? 175.0f : 180.0f);
        Camera->SetWorldLocationAndRotation(
            ViewLocation,
            (Raft->GetActorLocation() +
             FVector(20.0f, 0.0f, bRaftArtReview ? 38.0f : 55.0f) - ViewLocation).Rotation());
        if (bRaftArtReview)
        {
            Camera->SetFieldOfView(58.0f);
        }
        Camera->Activate(true);
        if (APlayerController* PlayerController = GetM5GameWorld()->GetFirstPlayerController())
        {
            PlayerController->SetViewTarget(Guide);
        }
    }
    FScreenshotRequest::RequestScreenshot(
        bRaftArtReview ? TEXT("M5_RaftConstruction.png") : TEXT("M5_RescueProduction.png"),
        false,
        false);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM5FinishRescueCommand, FAutomationTestBase*, Test);
bool FRaftSimM5FinishRescueCommand::Update()
{
    ARaftSimRaftActor* Raft = FindM5Raft();
    if (!Raft)
    {
        Test->AddError(TEXT("raft disappeared during M5 rescue"));
        return true;
    }
    Test->TestEqual(
        TEXT("runtime rescue reached re-entry"),
        static_cast<int32>(Raft->GetRescueInteractionState().Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    Test->TestTrue(TEXT("explicit reseat succeeds"), Raft->RequestSelectedReentry());
    Test->TestEqual(TEXT("no swimmer remains"), Raft->GetSwimmerCount(), 0);
    for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
    {
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s keeps finite render transforms"), *It->GetName()),
            It->HasFiniteVisualTransforms());
    }
    return true;
}

class FRaftSimM5WaitForRescueReadyCommand final : public IAutomationLatentCommand
{
public:
    explicit FRaftSimM5WaitForRescueReadyCommand(FAutomationTestBase* InTest)
        : Test(InTest)
    {
    }

    virtual bool Update() override
    {
        if (StartSeconds <= 0.0)
        {
            StartSeconds = FPlatformTime::Seconds();
        }
        ARaftSimRaftActor* Raft = FindM5Raft();
        if (!Raft)
        {
            Test->AddError(TEXT("raft disappeared while waiting for rescue re-entry"));
            return true;
        }
        if (Raft->GetRescueInteractionState().Phase ==
            ERaftSimRescueInteractionPhase::ReadyForReentry)
        {
            return true;
        }
        if (FPlatformTime::Seconds() - StartSeconds >= 30.0)
        {
            Test->AddError(TEXT("runtime rescue did not reach re-entry within 30 seconds"));
            return true;
        }
        return false;
    }

private:
    FAutomationTestBase* Test = nullptr;
    double StartSeconds = 0.0;
};

bool FRaftSimM5RuntimeRescueLoopTest::RunTest(const FString&)
{
#if PLATFORM_MAC
    // UE 5.8 can tear down an offscreen PIE text-input context after its NSWindow
    // has already gone away. It is unrelated to gameplay and occurs nondeterministically.
    AddExpectedErrorPlain(
        TEXT("LogMacTextInputMethodSystem: Deactivating a context failed when its window couldn't be found."),
        EAutomationExpectedErrorFlags::Contains,
        -1);
#endif
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM5StartRescueCommand(this));
    // Shader compilation and offscreen screenshot readback can collapse frame
    // throughput on a cold run. Wait for the actual rescue phase, not a fixed
    // wall-clock delay that may contain too few simulation ticks.
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM5WaitForRescueReadyCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM5FinishRescueCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
