#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "StaticMeshResources.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr float HeroStartStationM = 620.0f;
constexpr float HeroFullWeightStartStationM = 700.0f;
constexpr float HeroFullWeightEndStationM = 1240.0f;
constexpr float HeroEndStationM = 1320.0f;
constexpr int32 HeroProfileColumnCount = 10;

struct FMeatGrinderWaterBoundary
{
    float StationM = 0.0f;
    float MinimumLateralM = BIG_NUMBER;
    float MaximumLateralM = -BIG_NUMBER;
    FVector MinimumWorldCm = FVector::ZeroVector;
    FVector MaximumWorldCm = FVector::ZeroVector;
};

struct FMeatGrinderBankRow
{
    float StationM = 0.0f;
    FVector Positions[HeroProfileColumnCount] = {};
    FVector Along = FVector::ForwardVector;
};

constexpr float HeroTerrainSampleCellCm = 800.0f;

struct FMeatGrinderTerrainSampler
{
    TMap<FIntPoint, TArray<FVector>> Buckets;
    int32 SourceActorCount = 0;
    int32 SourceVertexCount = 0;

    static FIntPoint BucketKey(const FVector& Position)
    {
        return FIntPoint(
            FMath::FloorToInt(Position.X / HeroTerrainSampleCellCm),
            FMath::FloorToInt(Position.Y / HeroTerrainSampleCellCm));
    }

    void Build(UWorld* World, const FBox2D& WorldBounds)
    {
        Buckets.Reset();
        SourceActorCount = 0;
        SourceVertexCount = 0;
        if (!World || !WorldBounds.bIsValid)
        {
            return;
        }
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
        {
            AStaticMeshActor* Actor = *It;
            if (!Actor || !Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")))
            {
                continue;
            }
            UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
            UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
            const FStaticMeshRenderData* RenderData =
                Mesh ? Mesh->GetRenderData() : nullptr;
            if (!Component || !RenderData || RenderData->LODResources.IsEmpty())
            {
                continue;
            }
            ++SourceActorCount;
            const FPositionVertexBuffer& Positions =
                RenderData->LODResources[0].VertexBuffers.PositionVertexBuffer;
            const FTransform ComponentTransform = Component->GetComponentTransform();
            for (uint32 VertexIndex = 0;
                 VertexIndex < Positions.GetNumVertices();
                 ++VertexIndex)
            {
                const FVector WorldPosition = ComponentTransform.TransformPosition(
                    FVector(Positions.VertexPosition(VertexIndex)));
                if (!WorldBounds.IsInsideOrOn(FVector2D(
                        WorldPosition.X, WorldPosition.Y)))
                {
                    continue;
                }
                Buckets.FindOrAdd(BucketKey(WorldPosition)).Add(WorldPosition);
                ++SourceVertexCount;
            }
        }
    }

    bool FindSurfaceZCm(const FVector& Position, float& OutSurfaceZCm) const
    {
        const FIntPoint CenterKey = BucketKey(Position);
        float BestDistanceSquared = FMath::Square(1000.0f);
        bool bFound = false;
        for (int32 YOffset = -1; YOffset <= 1; ++YOffset)
        {
            for (int32 XOffset = -1; XOffset <= 1; ++XOffset)
            {
                const TArray<FVector>* Samples = Buckets.Find(
                    CenterKey + FIntPoint(XOffset, YOffset));
                if (!Samples)
                {
                    continue;
                }
                for (const FVector& Sample : *Samples)
                {
                    const float DistanceSquared = FVector::DistSquared2D(
                        Position, Sample);
                    if (DistanceSquared < BestDistanceSquared)
                    {
                        BestDistanceSquared = DistanceSquared;
                        OutSurfaceZCm = static_cast<float>(Sample.Z);
                        bFound = true;
                    }
                }
            }
        }
        return bFound;
    }
};

float HeroUnitRandom(int32 StationKey, int32 SideIndex, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(StationKey) * 0x9E3779B9u;
    Hash ^= static_cast<uint32>(SideIndex + 1) * 0x85EBCA6Bu;
    Hash ^= static_cast<uint32>(Salt) * 0xC2B2AE35u;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

float MeatGrinderHeroWeight(float StationM)
{
    const float Entrance = FMath::SmoothStep(
        HeroStartStationM, HeroFullWeightStartStationM, StationM);
    const float Exit = 1.0f - FMath::SmoothStep(
        HeroFullWeightEndStationM, HeroEndStationM, StationM);
    return FMath::Clamp(Entrance * Exit, 0.0f, 1.0f);
}

UHierarchicalInstancedStaticMeshComponent* CreateHeroHism(
    AActor* Owner,
    USceneComponent* Root,
    const FName Name,
    UStaticMesh* Mesh,
    int32 StartCullDistanceCm,
    int32 EndCullDistanceCm)
{
    UHierarchicalInstancedStaticMeshComponent* Component =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(
            Owner, Name, RF_Transient);
    if (!Component)
    {
        return nullptr;
    }
    Owner->AddInstanceComponent(Component);
    Component->SetupAttachment(Root);
    Component->SetStaticMesh(Mesh);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetCullDistances(StartCullDistanceCm, EndCullDistanceCm);
    Component->bEnableDensityScaling = false;
    Component->RegisterComponent();
    return Component;
}

} // namespace

bool ConfigureSouthForkMeatGrinderHeroReview(
    UWorld* World,
    TArray<TWeakObjectPtr<AActor>>& OutActors,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("Meat Grinder hero review has no loaded world.\n");
        return false;
    }

    const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
    const FName SolverFoamTag(TEXT("RaftSimSolverFoamOverlay"));
    TMap<int32, FMeatGrinderWaterBoundary> BoundaryByStation;
    int32 MedianWaterActorCount = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Actor = *It;
        if (!Actor || !Actor->ActorHasTag(MedianWaterTag) ||
            Actor->ActorHasTag(SolverFoamTag))
        {
            continue;
        }
        UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
        UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        const FStaticMeshRenderData* RenderData =
            Mesh ? Mesh->GetRenderData() : nullptr;
        if (!Component || !RenderData || RenderData->LODResources.IsEmpty())
        {
            continue;
        }
        const FStaticMeshLODResources& Lod = RenderData->LODResources[0];
        if (Lod.VertexBuffers.StaticMeshVertexBuffer.GetNumTexCoords() < 1)
        {
            continue;
        }
        const FIndexArrayView Indices = Lod.IndexBuffer.GetArrayView();
        TSet<uint32> ReferencedVertices;
        ReferencedVertices.Reserve(Indices.Num());
        for (int32 Index = 0; Index < Indices.Num(); ++Index)
        {
            ReferencedVertices.Add(Indices[Index]);
        }
        const FPositionVertexBuffer& Positions =
            Lod.VertexBuffers.PositionVertexBuffer;
        const FStaticMeshVertexBuffer& VertexBuffer =
            Lod.VertexBuffers.StaticMeshVertexBuffer;
        const FTransform ComponentTransform = Component->GetComponentTransform();
        for (const uint32 VertexIndex : ReferencedVertices)
        {
            if (VertexIndex >= Positions.GetNumVertices())
            {
                continue;
            }
            const FVector2f Uv = VertexBuffer.GetVertexUV(VertexIndex, 0);
            const float StationM = Uv.X * 3.0f;
            const float LateralM = Uv.Y * 3.0f;
            if (!FMath::IsFinite(StationM) || !FMath::IsFinite(LateralM) ||
                FMath::Abs(LateralM) > 45.0f)
            {
                continue;
            }
            const int32 StationKey = FMath::RoundToInt(StationM * 4.0f);
            FMeatGrinderWaterBoundary& Boundary =
                BoundaryByStation.FindOrAdd(StationKey);
            Boundary.StationM = StationM;
            const FVector WorldPosition = ComponentTransform.TransformPosition(
                FVector(Positions.VertexPosition(VertexIndex)));
            if (LateralM < Boundary.MinimumLateralM)
            {
                Boundary.MinimumLateralM = LateralM;
                Boundary.MinimumWorldCm = WorldPosition;
            }
            if (LateralM > Boundary.MaximumLateralM)
            {
                Boundary.MaximumLateralM = LateralM;
                Boundary.MaximumWorldCm = WorldPosition;
            }
        }
        ++MedianWaterActorCount;
    }

    TArray<int32> StationKeys;
    BoundaryByStation.GetKeys(StationKeys);
    StationKeys.Sort();
    if (MedianWaterActorCount < 13 || StationKeys.Num() < 5000)
    {
        OutSummary += FString::Printf(
            TEXT("Meat Grinder hero review expected at least 13 median-water "
                 "actors and 5,000 station samples but found %d and %d.\n"),
            MedianWaterActorCount, StationKeys.Num());
        return false;
    }

    UStaticMesh* BoulderMesh = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "MeatGrinderHero_2K/SM_Boulder01.SM_Boulder01"));
    UStaticMesh* PineMeshes[3] = {
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "PineTree01_1K/SM_PineTree01_pine_tree_01_a_LOD0."
                 "SM_PineTree01_pine_tree_01_a_LOD0")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "PineTree01_1K/SM_PineTree01_pine_tree_01_b_LOD0."
                 "SM_PineTree01_pine_tree_01_b_LOD0")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                 "PineTree01_1K/SM_PineTree01_pine_tree_01_c_LOD0."
                 "SM_PineTree01_pine_tree_01_c_LOD0"))};
    if (!BoulderMesh ||
        !PineMeshes[0] || !PineMeshes[1] || !PineMeshes[2])
    {
        OutSummary += TEXT("Meat Grinder hero review assets are unavailable.\n");
        return false;
    }

    FBox2D HeroWorldBounds(EForceInit::ForceInit);
    for (const TPair<int32, FMeatGrinderWaterBoundary>& Pair : BoundaryByStation)
    {
        const FMeatGrinderWaterBoundary& Boundary = Pair.Value;
        if (Boundary.StationM < HeroStartStationM ||
            Boundary.StationM > HeroEndStationM)
        {
            continue;
        }
        const FVector Center =
            (Boundary.MinimumWorldCm + Boundary.MaximumWorldCm) * 0.5f;
        HeroWorldBounds += FVector2D(Center.X, Center.Y);
    }
    HeroWorldBounds = HeroWorldBounds.ExpandBy(14000.0);
    FMeatGrinderTerrainSampler TerrainSampler;
    TerrainSampler.Build(World, HeroWorldBounds);
    if (TerrainSampler.SourceActorCount < 1 ||
        TerrainSampler.SourceVertexCount < 10000)
    {
        OutSummary += FString::Printf(
            TEXT("Meat Grinder hero review could not index the settled DEM "
                 "terrain: %d actors and %d local vertices.\n"),
            TerrainSampler.SourceActorCount,
            TerrainSampler.SourceVertexCount);
        return false;
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.ObjectFlags = RF_Transient;
    AActor* ReviewActor = World->SpawnActor<AActor>(
        AActor::StaticClass(), FTransform::Identity, SpawnParameters);
    if (!ReviewActor)
    {
        return false;
    }
    ReviewActor->SetActorLabel(TEXT("RaftSim_MeatGrinderHeroReview"));
    USceneComponent* Root = NewObject<USceneComponent>(
        ReviewActor, TEXT("MeatGrinderHeroReviewRoot"), RF_Transient);
    ReviewActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    ReviewActor->SetRootComponent(Root);

    UHierarchicalInstancedStaticMeshComponent* Boulders = CreateHeroHism(
        ReviewActor, Root, TEXT("MeatGrinderHeroBoulders"),
        BoulderMesh, 160000, 520000);
    UHierarchicalInstancedStaticMeshComponent* Pines[3] = {
        CreateHeroHism(
            ReviewActor, Root, TEXT("MeatGrinderHeroPinesA"),
            PineMeshes[0], 200000, 520000),
        CreateHeroHism(
            ReviewActor, Root, TEXT("MeatGrinderHeroPinesB"),
            PineMeshes[1], 200000, 520000),
        CreateHeroHism(
            ReviewActor, Root, TEXT("MeatGrinderHeroPinesC"),
            PineMeshes[2], 200000, 520000)};
    if (!Boulders || !Pines[0] || !Pines[1] || !Pines[2])
    {
        ReviewActor->Destroy();
        return false;
    }
    OutActors.Add(ReviewActor);

    const float ProfileWidthsCm[HeroProfileColumnCount] = {
        20.0f, 200.0f, 500.0f, 1000.0f, 1800.0f,
        2800.0f, 3800.0f, 4800.0f, 5900.0f, 7000.0f};
    // This fallback is retained only as an explicit fail-closed diagnostic.
    // v202 reads settled source-mesh vertices directly, so capture visibility
    // cannot force the review onto an averaged or invented bank profile.
    const float RightSourceProfileRiseM[HeroProfileColumnCount] = {
        -0.05f, 0.14f, 0.28f, 0.55f, 1.10f,
        2.05f, 3.55f, 5.35f, 7.35f, 9.55f};
    const float LeftSourceProfileRiseM[HeroProfileColumnCount] = {
        -0.05f, 0.12f, 0.25f, 0.52f, 1.05f,
        1.95f, 3.45f, 5.25f, 7.25f, 9.65f};

    TArray<FMeatGrinderBankRow> RowsBySide[2];
    int32 TerrainSourceSampleCount = 0;
    int32 ProceduralFallbackSampleCount = 0;
    int32 BankBoulderCount = 0;
    int32 PineCount = 0;
    float MinimumWetSpanM = BIG_NUMBER;
    float MaximumWetSpanM = 0.0f;
    float LastAcceptedStationM = -BIG_NUMBER;
    for (int32 OrderedIndex = 0;
         OrderedIndex < StationKeys.Num();
         ++OrderedIndex)
    {
        const int32 StationKey = StationKeys[OrderedIndex];
        const FMeatGrinderWaterBoundary* Boundary =
            BoundaryByStation.Find(StationKey);
        if (!Boundary ||
            Boundary->StationM < HeroStartStationM ||
            Boundary->StationM > HeroEndStationM ||
            Boundary->MaximumLateralM - Boundary->MinimumLateralM < 15.0f ||
            Boundary->StationM - LastAcceptedStationM < 7.5f)
        {
            continue;
        }
        LastAcceptedStationM = Boundary->StationM;
        const float WetSpanM =
            Boundary->MaximumLateralM - Boundary->MinimumLateralM;
        MinimumWetSpanM = FMath::Min(MinimumWetSpanM, WetSpanM);
        MaximumWetSpanM = FMath::Max(MaximumWetSpanM, WetSpanM);

        const FVector Center =
            (Boundary->MinimumWorldCm + Boundary->MaximumWorldCm) * 0.5f;
        const FMeatGrinderWaterBoundary* PreviousBoundary =
            BoundaryByStation.Find(
                StationKeys[FMath::Max(0, OrderedIndex - 4)]);
        const FMeatGrinderWaterBoundary* NextBoundary =
            BoundaryByStation.Find(
                StationKeys[FMath::Min(StationKeys.Num() - 1, OrderedIndex + 4)]);
        const FVector PreviousCenter = PreviousBoundary
            ? (PreviousBoundary->MinimumWorldCm +
               PreviousBoundary->MaximumWorldCm) * 0.5f
            : Center;
        const FVector NextCenter = NextBoundary
            ? (NextBoundary->MinimumWorldCm +
               NextBoundary->MaximumWorldCm) * 0.5f
            : Center;
        FVector Along = NextCenter - PreviousCenter;
        Along.Z = 0.0f;
        Along = Along.GetSafeNormal();
        if (Along.IsNearlyZero())
        {
            continue;
        }

        const FVector BoundaryPositions[2] = {
            Boundary->MinimumWorldCm,
            Boundary->MaximumWorldCm};
        const float HeroWeight = MeatGrinderHeroWeight(Boundary->StationM);
        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
        {
            FVector Outward = BoundaryPositions[SideIndex] - Center;
            Outward.Z = 0.0f;
            Outward = Outward.GetSafeNormal();
            if (Outward.IsNearlyZero())
            {
                continue;
            }
            const float* SourceProfileRiseM = SideIndex == 0
                ? RightSourceProfileRiseM
                : LeftSourceProfileRiseM;
            FMeatGrinderBankRow Row;
            Row.StationM = Boundary->StationM;
            Row.Along = Along;
            for (int32 ColumnIndex = 0;
                 ColumnIndex < HeroProfileColumnCount;
                 ++ColumnIndex)
            {
                FVector Position = BoundaryPositions[SideIndex] +
                    Outward * ProfileWidthsCm[ColumnIndex];
                float TerrainZCm = BoundaryPositions[SideIndex].Z;
                if (TerrainSampler.FindSurfaceZCm(Position, TerrainZCm))
                {
                    ++TerrainSourceSampleCount;
                }
                else
                {
                    TerrainZCm = BoundaryPositions[SideIndex].Z +
                        SourceProfileRiseM[ColumnIndex] * 100.0f;
                    ++ProceduralFallbackSampleCount;
                }
                Position.Z = TerrainZCm + 3.0f;
                Row.Positions[ColumnIndex] = Position;
            }
            RowsBySide[SideIndex].Add(Row);

            if (HeroWeight > 0.72f &&
                FMath::Fmod(Boundary->StationM + SideIndex * 8.0f, 20.0f) < 8.1f)
            {
                const int32 BoulderAttempts = SideIndex == 0 ? 2 : 1;
                for (int32 Attempt = 0; Attempt < BoulderAttempts; ++Attempt)
                {
                    const float Across = FMath::Lerp(
                        0.04f, SideIndex == 0 ? 0.64f : 0.76f,
                        HeroUnitRandom(StationKey, SideIndex, 101 + Attempt * 29));
                    FVector Location = FMath::Lerp(
                        Row.Positions[1], Row.Positions[5], Across);
                    Location += Along * FMath::Lerp(
                        -310.0f, 310.0f,
                        HeroUnitRandom(StationKey, SideIndex, 107 + Attempt * 31));
                    const float Scale = FMath::Lerp(
                        0.88f, 1.82f,
                        HeroUnitRandom(StationKey, SideIndex, 113 + Attempt * 37));
                    Location.Z -= 31.0f * Scale;
                    Boulders->AddInstance(
                        FTransform(
                            FRotator(
                                FMath::Lerp(-8.0f, 8.0f,
                                    HeroUnitRandom(
                                        StationKey, SideIndex, 127 + Attempt * 41)),
                                Along.Rotation().Yaw + FMath::Lerp(
                                    -75.0f, 75.0f,
                                    HeroUnitRandom(
                                        StationKey, SideIndex, 131 + Attempt * 43)),
                                FMath::Lerp(-6.0f, 6.0f,
                                    HeroUnitRandom(
                                        StationKey, SideIndex, 137 + Attempt * 47))),
                            Location,
                            FVector(
                                Scale,
                                Scale * FMath::Lerp(
                                    0.82f, 1.18f,
                                    HeroUnitRandom(
                                        StationKey, SideIndex, 139 + Attempt * 53)),
                                Scale * FMath::Lerp(
                                    0.78f, 1.12f,
                                    HeroUnitRandom(
                                        StationKey, SideIndex, 149 + Attempt * 59)))),
                        /*bWorldSpace=*/true);
                    ++BankBoulderCount;
                }
            }

            if (HeroWeight > 0.55f &&
                FMath::Fmod(Boundary->StationM + SideIndex * 12.0f, 32.0f) < 8.1f)
            {
                const int32 PineAttempts = SideIndex == 0 ? 2 : 1;
                for (int32 Attempt = 0; Attempt < PineAttempts; ++Attempt)
                {
                    const int32 MeshIndex = FMath::Clamp(
                        FMath::FloorToInt(
                            HeroUnitRandom(
                                StationKey, SideIndex, 163 + Attempt * 17) * 3.0f),
                        0, 2);
                    const float Across = FMath::Lerp(
                        0.18f, 0.86f,
                        HeroUnitRandom(
                            StationKey, SideIndex, 167 + Attempt * 19));
                    FVector Location = FMath::Lerp(
                        Row.Positions[6], Row.Positions[8], Across);
                    Location += Along * FMath::Lerp(
                        -620.0f, 620.0f,
                        HeroUnitRandom(
                            StationKey, SideIndex, 173 + Attempt * 23));
                    const float Scale = FMath::Lerp(
                        0.84f, 1.24f,
                        HeroUnitRandom(
                            StationKey, SideIndex, 179 + Attempt * 31));
                    Pines[MeshIndex]->AddInstance(
                        FTransform(
                            FRotator(
                                0.0f,
                                HeroUnitRandom(
                                    StationKey, SideIndex, 181 + Attempt * 37) * 360.0f,
                                0.0f),
                            Location,
                            FVector(Scale)),
                        /*bWorldSpace=*/true);
                    ++PineCount;
                }
            }

        }
    }

    struct FChannelBoulderSpec
    {
        float StationM;
        float AcrossFromRight;
        float Scale;
        float SubmergeCm;
        float YawOffsetDegrees;
    };
    const FChannelBoulderSpec ChannelSpecs[] = {
        {824.0f, 0.70f, 1.42f, 58.0f, -18.0f},
        {888.0f, 0.44f, 1.58f, 64.0f, 31.0f},
        {1008.0f, 0.09f, 2.35f, 76.0f, -9.0f},
        {1080.0f, 0.66f, 1.72f, 68.0f, 22.0f},
        {1144.0f, 0.31f, 1.36f, 54.0f, -34.0f}};
    int32 ChannelBoulderCount = 0;
    for (const FChannelBoulderSpec& Spec : ChannelSpecs)
    {
        const int32 TargetKey = FMath::RoundToInt(Spec.StationM * 4.0f);
        const int32* ClosestKey = StationKeys.FindByPredicate(
            [TargetKey](int32 Candidate)
            {
                return FMath::Abs(Candidate - TargetKey) <= 8;
            });
        const FMeatGrinderWaterBoundary* Boundary = ClosestKey
            ? BoundaryByStation.Find(*ClosestKey)
            : nullptr;
        if (!Boundary)
        {
            continue;
        }
        FVector Along = FVector::ForwardVector;
        const int32 KeyIndex = StationKeys.IndexOfByKey(*ClosestKey);
        if (KeyIndex != INDEX_NONE)
        {
            const FMeatGrinderWaterBoundary* Previous = BoundaryByStation.Find(
                StationKeys[FMath::Max(0, KeyIndex - 4)]);
            const FMeatGrinderWaterBoundary* Next = BoundaryByStation.Find(
                StationKeys[FMath::Min(StationKeys.Num() - 1, KeyIndex + 4)]);
            if (Previous && Next)
            {
                const FVector PreviousCenter =
                    (Previous->MinimumWorldCm + Previous->MaximumWorldCm) * 0.5f;
                const FVector NextCenter =
                    (Next->MinimumWorldCm + Next->MaximumWorldCm) * 0.5f;
                Along = NextCenter - PreviousCenter;
                Along.Z = 0.0f;
                Along = Along.GetSafeNormal();
            }
        }
        FVector Location = FMath::Lerp(
            Boundary->MinimumWorldCm,
            Boundary->MaximumWorldCm,
            Spec.AcrossFromRight);
        Location.Z -= Spec.SubmergeCm;
        Boulders->AddInstance(
            FTransform(
                FRotator(
                    -4.0f,
                    Along.Rotation().Yaw + Spec.YawOffsetDegrees,
                    3.0f),
                Location,
                FVector(Spec.Scale, Spec.Scale * 1.08f, Spec.Scale * 0.94f)),
            /*bWorldSpace=*/true);
        ++ChannelBoulderCount;
    }

    if (TerrainSourceSampleCount < 1500 ||
        ProceduralFallbackSampleCount != 0 ||
        BankBoulderCount < 45 || PineCount < 35 ||
        ChannelBoulderCount != UE_ARRAY_COUNT(ChannelSpecs))
    {
        ReviewActor->Destroy();
        OutSummary += FString::Printf(
            TEXT("Meat Grinder hero review expected at least 1,500 direct "
                 "source-terrain samples, zero procedural fallbacks, 45 bank "
                 "boulders, 35 pines, and %d channel boulders but built %d, "
                 "%d, %d, %d, and %d.\n"),
            UE_ARRAY_COUNT(ChannelSpecs), TerrainSourceSampleCount,
            ProceduralFallbackSampleCount,
            BankBoulderCount, PineCount,
            ChannelBoulderCount);
        return false;
    }

    OutSummary += FString::Printf(
        TEXT("Transient Meat Grinder hero rock garden built %.0f-%.0f m from "
             "%d median-water actors: wet span %.1f-%.1f m, %d direct "
             "settled-DEM mesh samples from %d terrain actors (%d indexed "
             "local vertices), zero procedural bank geometry, zero fallback "
             "height samples, %d publisher-scale bank boulders, %d guide-line "
             "channel boulders including the near-right-bank wrap-hazard "
             "benchmark, and %d detailed pines. Authoritative terrain remains "
             "visible and unchanged; review dressing is transient, non-"
             "colliding, non-navigable, and unsaved.\n"),
        HeroStartStationM, HeroEndStationM, MedianWaterActorCount,
        MinimumWetSpanM, MaximumWetSpanM, TerrainSourceSampleCount,
        TerrainSampler.SourceActorCount, TerrainSampler.SourceVertexCount,
        BankBoulderCount,
        ChannelBoulderCount, PineCount);
    return true;
}
} // namespace RaftSimEditorEnvironment
