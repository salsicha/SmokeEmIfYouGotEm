#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr int32 ShoreCobbleVariantCount = 3;

FString ShoreCobbleAssetPath(int32 VariantIndex)
{
    return FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Meshes/"
             "SM_RaftSim_SouthForkShoreCobble_%c"),
        TCHAR('A' + VariantIndex));
}

float ShoreUnitRandom(int32 CoordinateIndex, int32 Column, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(CoordinateIndex) * 0x9E3779B9u;
    Hash ^= static_cast<uint32>(Column) * 0x85EBCA6Bu;
    Hash ^= static_cast<uint32>(Salt) * 0xC2B2AE35u;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

UStaticMesh* BuildShoreCobbleAsset(
    UWorld* World,
    int32 VariantIndex,
    UMaterialInterface* Material,
    FString& OutSummary)
{
    if (!World || !Material || VariantIndex < 0 ||
        VariantIndex >= ShoreCobbleVariantCount)
    {
        return nullptr;
    }

    constexpr int32 SegmentCount = 16;
    constexpr int32 RingCount = 8;
    const FVector VariantShape = VariantIndex == 0
        ? FVector(56.0f, 43.0f, 38.0f)
        : (VariantIndex == 1
            ? FVector(47.0f, 58.0f, 31.0f)
            : FVector(62.0f, 39.0f, 27.0f));
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    Vertices.Reserve(2 + (RingCount - 1) * SegmentCount);
    Normals.Reserve(Vertices.Max());
    Uvs.Reserve(Vertices.Max());
    Colors.Reserve(Vertices.Max());
    Tangents.Reserve(Vertices.Max());

    auto AddVertex = [&](const FVector& Position, const FVector& Normal,
                         const FVector2D& Uv, const FVector& Tangent)
    {
        Vertices.Add(Position);
        Normals.Add(Normal.GetSafeNormal());
        Uvs.Add(Uv);
        Colors.Add(FLinearColor::White);
        Tangents.Add(FProcMeshTangent(Tangent.GetSafeNormal(), false));
    };

    AddVertex(FVector::ZeroVector, FVector(0.0f, 0.0f, -1.0f),
        FVector2D(0.5f, 1.0f), FVector::ForwardVector);
    for (int32 Ring = 1; Ring < RingCount; ++Ring)
    {
        const float RingT = static_cast<float>(Ring) / RingCount;
        const float Latitude = -0.5f * PI + RingT * PI;
        const float Radial = FMath::Cos(Latitude);
        const float UnitZ = FMath::Sin(Latitude);
        for (int32 Segment = 0; Segment < SegmentCount; ++Segment)
        {
            const float SegmentT = static_cast<float>(Segment) / SegmentCount;
            const float Longitude = SegmentT * UE_TWO_PI;
            const float EdgeNoise = 1.0f +
                0.095f * FMath::Sin(
                    Longitude * (3.0f + VariantIndex) + Ring * 0.73f) +
                0.055f * FMath::Sin(Longitude * 7.0f - Ring * 0.41f);
            const float UnitX = Radial * FMath::Cos(Longitude) * EdgeNoise;
            const float UnitY = Radial * FMath::Sin(Longitude) * EdgeNoise;
            const FVector Position(
                UnitX * VariantShape.X,
                UnitY * VariantShape.Y,
                (UnitZ + 1.0f) * VariantShape.Z);
            const FVector Normal(
                UnitX / VariantShape.X,
                UnitY / VariantShape.Y,
                UnitZ / VariantShape.Z);
            const FVector Tangent(
                -FMath::Sin(Longitude), FMath::Cos(Longitude), 0.0f);
            AddVertex(Position, Normal, FVector2D(SegmentT, 1.0f - RingT), Tangent);
        }
    }
    const int32 TopIndex = Vertices.Num();
    AddVertex(FVector(0.0f, 0.0f, 2.0f * VariantShape.Z), FVector::UpVector,
        FVector2D(0.5f, 0.0f), FVector::ForwardVector);

    const int32 FirstRingStart = 1;
    for (int32 Segment = 0; Segment < SegmentCount; ++Segment)
    {
        const int32 Next = (Segment + 1) % SegmentCount;
        Triangles.Append({0, FirstRingStart + Next, FirstRingStart + Segment});
    }
    for (int32 Ring = 0; Ring < RingCount - 2; ++Ring)
    {
        const int32 LowerStart = FirstRingStart + Ring * SegmentCount;
        const int32 UpperStart = LowerStart + SegmentCount;
        for (int32 Segment = 0; Segment < SegmentCount; ++Segment)
        {
            const int32 Next = (Segment + 1) % SegmentCount;
            Triangles.Append({
                LowerStart + Segment, UpperStart + Next, UpperStart + Segment,
                LowerStart + Segment, LowerStart + Next, UpperStart + Next});
        }
    }
    const int32 LastRingStart = FirstRingStart + (RingCount - 2) * SegmentCount;
    for (int32 Segment = 0; Segment < SegmentCount; ++Segment)
    {
        const int32 Next = (Segment + 1) % SegmentCount;
        Triangles.Append({LastRingStart + Segment, LastRingStart + Next, TopIndex});
    }

    AActor* TemporaryActor = World->SpawnActor<AActor>(
        AActor::StaticClass(), FTransform::Identity);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    TemporaryActor->SetActorLabel(FString::Printf(
        TEXT("SouthForkShoreCobble%c_BuildSource"), TCHAR('A' + VariantIndex)));
    USceneComponent* Root = NewObject<USceneComponent>(TemporaryActor, TEXT("Root"));
    TemporaryActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    TemporaryActor->SetRootComponent(Root);
    UProceduralMeshComponent* Procedural =
        NewObject<UProceduralMeshComponent>(TemporaryActor, TEXT("SourceMesh"));
    TemporaryActor->AddInstanceComponent(Procedural);
    Procedural->SetupAttachment(Root);
    Procedural->RegisterComponent();
    Procedural->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, Uvs, Colors, Tangents,
        /*bCreateCollision=*/false);
    Procedural->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Procedural->SetMaterial(0, Material);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor, ShoreCobbleAssetPath(VariantIndex), Material,
        /*bEnableNanite=*/false, ENaniteShapePreservation::None, OutSummary);
    TemporaryActor->Destroy();
    return Mesh;
}
} // namespace

bool CreateSouthForkShoreCobbleAssets(
    UWorld* World,
    UMaterialInterface* Material,
    bool bReuseExistingAssets,
    UStaticMesh* (&OutMeshes)[3],
    FString& OutSummary)
{
    for (int32 VariantIndex = 0; VariantIndex < ShoreCobbleVariantCount;
         ++VariantIndex)
    {
        OutMeshes[VariantIndex] = bReuseExistingAssets
            ? LoadObject<UStaticMesh>(nullptr, *FString::Printf(
                TEXT("%s.%s"), *ShoreCobbleAssetPath(VariantIndex),
                *FPackageName::GetLongPackageAssetName(
                    ShoreCobbleAssetPath(VariantIndex))))
            : nullptr;
        if (!OutMeshes[VariantIndex])
        {
            OutMeshes[VariantIndex] = BuildShoreCobbleAsset(
                World, VariantIndex, Material, OutSummary);
        }
        if (!OutMeshes[VariantIndex])
        {
            OutSummary += TEXT("Failed to build procedural South Fork shore cobbles.\n");
            return false;
        }
    }
    OutSummary += TEXT(
        "Prepared three project-owned, non-colliding procedural shore-cobble variants.\n");
    return true;
}

void CreateSouthForkShoreCobbleComponents(
    AActor* Owner,
    USceneComponent* Root,
    UStaticMesh* const* Meshes,
    UHierarchicalInstancedStaticMeshComponent* (&OutComponents)[3])
{
    if (!Owner || !Root || !Meshes)
    {
        return;
    }
    for (int32 VariantIndex = 0; VariantIndex < ShoreCobbleVariantCount;
         ++VariantIndex)
    {
        OutComponents[VariantIndex] =
            NewObject<UHierarchicalInstancedStaticMeshComponent>(
                Owner, *FString::Printf(
                    TEXT("ShoreCobble%c"), TCHAR('A' + VariantIndex)));
        UHierarchicalInstancedStaticMeshComponent* Component =
            OutComponents[VariantIndex];
        Owner->AddInstanceComponent(Component);
        Component->SetupAttachment(Root);
        Component->SetStaticMesh(Meshes[VariantIndex]);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
        Component->SetCullDistances(90000, 220000);
        Component->bEnableDensityScaling = false;
        Component->RegisterComponent();
    }
}

int32 AddSouthForkShoreCobbleInstances(
    UHierarchicalInstancedStaticMeshComponent* const* Components,
    const FVector& GroundLocation,
    const FVector2D& LeftNormal,
    int32 CoordinateIndex,
    int32 Column,
    float BankDistanceM,
    float LateralSlope)
{
    if (!Components || (CoordinateIndex & 3) != 0 ||
        BankDistanceM < 36.0f || BankDistanceM > 64.0f)
    {
        return 0;
    }
    const float BankT = FMath::Clamp((BankDistanceM - 36.0f) / 28.0f, 0.0f, 1.0f);
    const float Probability = FMath::Clamp(
        FMath::Lerp(0.86f, 0.28f, BankT) + LateralSlope * 0.08f,
        0.22f, 0.90f);
    if (ShoreUnitRandom(CoordinateIndex, Column, 211) > Probability)
    {
        return 0;
    }

    const FVector Across(LeftNormal.X, LeftNormal.Y, 0.0f);
    const FVector Along(Across.Y, -Across.X, 0.0f);
    const int32 ClusterCount =
        ShoreUnitRandom(CoordinateIndex, Column, 223) < 0.34f ? 2 : 1;
    int32 AddedCount = 0;
    for (int32 ClusterIndex = 0; ClusterIndex < ClusterCount; ++ClusterIndex)
    {
        const int32 Salt = 227 + ClusterIndex * 31;
        const int32 VariantIndex = FMath::Clamp(
            FMath::FloorToInt(
                ShoreUnitRandom(CoordinateIndex, Column, Salt) *
                ShoreCobbleVariantCount),
            0, ShoreCobbleVariantCount - 1);
        UHierarchicalInstancedStaticMeshComponent* Component =
            Components[VariantIndex];
        if (!Component)
        {
            continue;
        }
        const float Scale = FMath::Lerp(
            0.11f, 0.43f,
            FMath::Pow(
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 2), 1.55f));
        const FVector Jitter =
            Along * FMath::Lerp(
                -560.0f, 560.0f,
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 3)) +
            Across * FMath::Lerp(
                -280.0f, 280.0f,
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 5));
        const FVector InstanceScale(
            Scale * FMath::Lerp(
                0.74f, 1.34f,
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 7)),
            Scale * FMath::Lerp(
                0.76f, 1.30f,
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 11)),
            Scale * FMath::Lerp(
                0.58f, 1.04f,
                ShoreUnitRandom(CoordinateIndex, Column, Salt + 13)));
        Component->AddInstance(
            FTransform(
                FRotator(
                    FMath::Lerp(
                        -8.0f, 8.0f,
                        ShoreUnitRandom(CoordinateIndex, Column, Salt + 17)),
                    ShoreUnitRandom(CoordinateIndex, Column, Salt + 19) * 360.0f,
                    FMath::Lerp(
                        -7.0f, 7.0f,
                        ShoreUnitRandom(CoordinateIndex, Column, Salt + 23))),
                GroundLocation + Jitter + FVector(0.0f, 0.0f, Scale * 4.0f),
                InstanceScale),
            /*bWorldSpace=*/true);
        ++AddedCount;
    }
    return AddedCount;
}

int32 AddSouthForkBankUnderstoryInstance(
    UHierarchicalInstancedStaticMeshComponent* Understory,
    const FVector& GroundLocation,
    const FVector2D& LeftNormal,
    int32 CoordinateIndex,
    int32 Column,
    float BankDistanceM,
    float LateralSlope,
    const FLinearColor& SourceDensity)
{
    if (!Understory || (CoordinateIndex & 1) != 0 ||
        BankDistanceM < 34.0f || BankDistanceM > 108.0f ||
        LateralSlope > 0.40f)
    {
        return 0;
    }
    const float SourceVegetationSignal = FMath::Max(
        SourceDensity.A,
        SourceDensity.R * 0.20f + SourceDensity.G * 0.46f +
            SourceDensity.B * 0.34f);
    const float PatchNoise = 0.5f + 0.5f * FMath::PerlinNoise2D(
        FVector2D(GroundLocation.X, GroundLocation.Y) / 44000.0f +
        FVector2D(3.7f, -6.1f));
    const float ShoreFade = FMath::SmoothStep(
        34.0f, 44.0f, BankDistanceM);
    const float OuterBankFade = 1.0f - FMath::SmoothStep(
        94.0f, 108.0f, BankDistanceM);
    const float Probability = FMath::Clamp(
        (0.18f + SourceVegetationSignal * 0.42f) *
            FMath::Lerp(0.52f, 1.46f, PatchNoise) *
            ShoreFade * OuterBankFade,
        0.0f, 0.68f);
    if (ShoreUnitRandom(CoordinateIndex, Column, 307) > Probability)
    {
        return 0;
    }

    const FVector Across(LeftNormal.X, LeftNormal.Y, 0.0f);
    const FVector Along(Across.Y, -Across.X, 0.0f);
    const float Scale = FMath::Lerp(
        0.82f, 1.58f,
        ShoreUnitRandom(CoordinateIndex, Column, 311));
    const FVector Jitter =
        Along * FMath::Lerp(
            -340.0f, 340.0f,
            ShoreUnitRandom(CoordinateIndex, Column, 313)) +
        Across * FMath::Lerp(
            -220.0f, 220.0f,
            ShoreUnitRandom(CoordinateIndex, Column, 317));
    const FVector ProfileScale(
        Scale * FMath::Lerp(
            0.78f, 1.38f,
            ShoreUnitRandom(CoordinateIndex, Column, 319)),
        Scale * FMath::Lerp(
            0.80f, 1.30f,
            ShoreUnitRandom(CoordinateIndex, Column, 323)),
        Scale * FMath::Lerp(
            0.64f, 1.12f,
            ShoreUnitRandom(CoordinateIndex, Column, 331)));
    Understory->AddInstance(
        FTransform(
            FRotator(
                0.0f,
                ShoreUnitRandom(CoordinateIndex, Column, 337) * 360.0f,
                0.0f),
            GroundLocation + Jitter - FVector(0.0f, 0.0f, Scale * 24.0f),
            ProfileScale),
        /*bWorldSpace=*/true);
    return 1;
}
} // namespace RaftSimEditorEnvironment
