#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "StaticMeshResources.h"

namespace RaftSimEditorEnvironment
{
namespace
{
struct FSouthForkWaterBoundaryPair
{
    float StationM = 0.0f;
    float MinimumLateralM = BIG_NUMBER;
    float MaximumLateralM = -BIG_NUMBER;
    FVector MinimumWorldCm = FVector::ZeroVector;
    FVector MaximumWorldCm = FVector::ZeroVector;
};

struct FSouthForkBankReviewRow
{
    float StationM = 0.0f;
    FVector Positions[5] = {};
    FLinearColor Colors[5] = {};
    FVector Along = FVector::ForwardVector;
    bool bCutBank = false;
    float MorphologyWeight = 0.0f;
};

float DerivedBankUnitRandom(int32 StationKey, int32 SideIndex, int32 Salt)
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

bool FindDetailedTerrainSurfaceZCm(
    UWorld* World,
    const FVector& XYAndReferenceZ,
    float& OutSurfaceZCm)
{
    if (!World)
    {
        return false;
    }
    TArray<FHitResult> Hits;
    FCollisionQueryParams QueryParams(
        SCENE_QUERY_STAT(RaftSimDerivedBankTerrainSurface),
        /*bTraceComplex=*/true);
    const FVector Start(
        XYAndReferenceZ.X, XYAndReferenceZ.Y,
        XYAndReferenceZ.Z + 12000.0f);
    const FVector End(
        XYAndReferenceZ.X, XYAndReferenceZ.Y,
        XYAndReferenceZ.Z - 12000.0f);
    if (!World->LineTraceMultiByChannel(
            Hits, Start, End, ECC_Visibility, QueryParams))
    {
        return false;
    }
    for (const FHitResult& Hit : Hits)
    {
        const AActor* Actor = Hit.GetActor();
        if (Actor && Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")))
        {
            OutSurfaceZCm = static_cast<float>(Hit.ImpactPoint.Z);
            return true;
        }
    }
    return false;
}

UMaterialInterface* CreateDerivedBankTerrainMaterial(AActor* Owner)
{
    UMaterialInterface* Parent = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    UMaterialInstanceDynamic* Material = Parent
        ? UMaterialInstanceDynamic::Create(Parent, Owner)
        : nullptr;
    if (!Material)
    {
        return nullptr;
    }
    UTexture2D* Albedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/ReviewTerrainTextures/SouthForkDetailV2/Textures/"
             "T_RaftSim_SouthForkTerrainDetailV2Review_Albedo."
             "T_RaftSim_SouthForkTerrainDetailV2Review_Albedo"));
    UTexture2D* Normal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/ReviewTerrainTextures/SouthForkDetailV2/Textures/"
             "T_RaftSim_SouthForkTerrainDetailV2Review_Normal."
             "T_RaftSim_SouthForkTerrainDetailV2Review_Normal"));
    UTexture2D* Packed = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/ReviewTerrainTextures/SouthForkDetailV2/Textures/"
             "T_RaftSim_SouthForkTerrainDetailV2Review_Packed."
             "T_RaftSim_SouthForkTerrainDetailV2Review_Packed"));
    if (!Albedo || !Normal || !Packed)
    {
        return nullptr;
    }
    Material->SetTextureParameterValue(TEXT("GroundAlbedo"), Albedo);
    Material->SetTextureParameterValue(TEXT("GroundNormal"), Normal);
    Material->SetTextureParameterValue(TEXT("GroundPacked"), Packed);
    Material->SetScalarParameterValue(TEXT("UseSourceMacroTexture"), 0.0f);
    Material->SetScalarParameterValue(TEXT("UseCorridorEdgeBlend"), 0.0f);
    Material->SetScalarParameterValue(TEXT("SourceMacroInfluence"), 0.0f);
    Material->SetScalarParameterValue(TEXT("RockAlbedoStrength"), 0.44f);
    Material->SetScalarParameterValue(TEXT("TerrainSpecular"), 0.02f);
    return Material;
}

void AppendDerivedBankStripSegment(
    const FSouthForkBankReviewRow& Previous,
    const FSouthForkBankReviewRow& Current,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors,
    TArray<FProcMeshTangent>& Tangents,
    bool bReverseWinding)
{
    const int32 BaseVertex = Vertices.Num();
    for (int32 RowIndex = 0; RowIndex < 2; ++RowIndex)
    {
        const FSouthForkBankReviewRow& Row = RowIndex == 0
            ? Previous
            : Current;
        for (int32 ColumnIndex = 0; ColumnIndex < 5; ++ColumnIndex)
        {
            Vertices.Add(Row.Positions[ColumnIndex]);
            Uvs.Add(FVector2D(
                Row.StationM * 0.01f,
                static_cast<float>(ColumnIndex) / 4.0f));
            Colors.Add(Row.Colors[ColumnIndex]);
            Tangents.Add(FProcMeshTangent(Row.Along, false));
        }
    }
    for (int32 ColumnIndex = 0; ColumnIndex < 4; ++ColumnIndex)
    {
        const int32 A = BaseVertex + ColumnIndex;
        const int32 B = A + 1;
        const int32 C = BaseVertex + 5 + ColumnIndex;
        const int32 D = C + 1;
        if (bReverseWinding)
        {
            Triangles.Append({A, B, C, B, D, C});
        }
        else
        {
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}
} // namespace

bool ConfigureSouthForkDerivedBankMorphologyReview(
    UWorld* World,
    TArray<TWeakObjectPtr<AActor>>& OutActors,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("South Fork derived-bank review has no loaded world.\n");
        return false;
    }

    const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
    const FName SolverFoamTag(TEXT("RaftSimSolverFoamOverlay"));
    TMap<int32, FSouthForkWaterBoundaryPair> BoundaryByStation;
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
        const FStaticMeshRenderData* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
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
            FSouthForkWaterBoundaryPair& Boundary =
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
            TEXT("Derived-bank review expected at least 13 median-water actors and "
                 "5,000 station samples but found %d and %d.\n"),
            MedianWaterActorCount, StationKeys.Num());
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
    ReviewActor->SetActorLabel(TEXT("RaftSim_DerivedBankMorphologyReview"));
    USceneComponent* Root = NewObject<USceneComponent>(
        ReviewActor, TEXT("DerivedBankReviewRoot"), RF_Transient);
    ReviewActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    ReviewActor->SetRootComponent(Root);
    UProceduralMeshComponent* BankMesh = NewObject<UProceduralMeshComponent>(
        ReviewActor, TEXT("DerivedBankStrips"), RF_Transient);
    ReviewActor->AddInstanceComponent(BankMesh);
    BankMesh->SetupAttachment(Root);
    BankMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BankMesh->SetCanEverAffectNavigation(false);
    BankMesh->SetCastShadow(true);
    BankMesh->RegisterComponent();
    OutActors.Add(ReviewActor);

    UMaterialInterface* BankMaterial = CreateDerivedBankTerrainMaterial(ReviewActor);
    if (!BankMaterial)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += TEXT("Derived-bank review material is unavailable.\n");
        return false;
    }

    UStaticMesh* ReviewMeshes[6] = {};
    UHierarchicalInstancedStaticMeshComponent* RockComponents[6] = {};
    FBox EffectiveBounds[6];
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
            RestoreSouthForkDerivedBankMorphologyReview(OutActors);
            OutSummary += FString::Printf(
                TEXT("Missing derived-bank scan donor %s.\n"), *ObjectPath);
            return false;
        }
        EffectiveBounds[MeshIndex] = ReviewMeshes[MeshIndex]->GetBoundingBox();
        if (EffectiveBounds[MeshIndex].GetSize().Z < 100.0f &&
            ReviewMeshes[MeshIndex]->GetNumSourceModels() > 0)
        {
            const FVector BuildScale =
                ReviewMeshes[MeshIndex]->GetSourceModel(0)
                    .BuildSettings.BuildScale3D;
            EffectiveBounds[MeshIndex] = FBox(
                EffectiveBounds[MeshIndex].Min * BuildScale,
                EffectiveBounds[MeshIndex].Max * BuildScale);
        }
        RockComponents[MeshIndex] =
            NewObject<UHierarchicalInstancedStaticMeshComponent>(
                ReviewActor,
                *FString::Printf(TEXT("DerivedBankRock%02d"), MeshIndex + 1),
                RF_Transient);
        ReviewActor->AddInstanceComponent(RockComponents[MeshIndex]);
        RockComponents[MeshIndex]->SetupAttachment(Root);
        RockComponents[MeshIndex]->SetStaticMesh(ReviewMeshes[MeshIndex]);
        RockComponents[MeshIndex]->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        RockComponents[MeshIndex]->SetCanEverAffectNavigation(false);
        RockComponents[MeshIndex]->SetCastShadow(true);
        RockComponents[MeshIndex]->SetCullDistances(180000, 480000);
        RockComponents[MeshIndex]->bEnableDensityScaling = false;
        RockComponents[MeshIndex]->RegisterComponent();
    }

    UStaticMesh* RootSegmentMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    UMaterialInterface* RootMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
             "M_FirTree01_Bark.M_FirTree01_Bark"));
    if (!RootSegmentMesh || !RootMaterial)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += TEXT("Derived-bank review root donor or CC0 bark material is unavailable.\n");
        return false;
    }
    UHierarchicalInstancedStaticMeshComponent* RootSegments =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(
            ReviewActor, TEXT("DerivedBankRootSegments"), RF_Transient);
    ReviewActor->AddInstanceComponent(RootSegments);
    RootSegments->SetupAttachment(Root);
    RootSegments->SetStaticMesh(RootSegmentMesh);
    RootSegments->SetMaterial(0, RootMaterial);
    RootSegments->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RootSegments->SetCanEverAffectNavigation(false);
    RootSegments->SetCastShadow(true);
    RootSegments->SetCullDistances(120000, 360000);
    RootSegments->bEnableDensityScaling = false;
    RootSegments->RegisterComponent();
    const FVector RootDonorSize = RootSegmentMesh->GetBoundingBox().GetSize();
    auto AddRootSegment = [RootSegments, RootDonorSize](
                              const FVector& Start,
                              const FVector& End,
                              float DiameterCm)
    {
        const FVector Delta = End - Start;
        const float LengthCm = Delta.Size();
        if (LengthCm < 8.0f)
        {
            return;
        }
        const FQuat Rotation = FQuat::FindBetweenNormals(
            FVector::UpVector, Delta / LengthCm);
        const FVector Scale(
            DiameterCm / FMath::Max(RootDonorSize.X, 1.0f),
            DiameterCm / FMath::Max(RootDonorSize.Y, 1.0f),
            LengthCm / FMath::Max(RootDonorSize.Z, 1.0f));
        RootSegments->AddInstance(
            FTransform(Rotation, (Start + End) * 0.5f, Scale),
            /*bWorldSpace=*/true);
    };

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    TArray<FSouthForkBankReviewRow> RowsBySide[2];
    int32 TerrainTraceHitCount = 0;
    int32 RockInstanceCount = 0;
    int32 RootSegmentCount = 0;
    int32 CutBankRowCount = 0;
    int32 GravelBarRowCount = 0;
    float LastAcceptedStationM = -BIG_NUMBER;
    const float ReviewStationsM[] = {
        120.0f, 944.0f, 5100.0f, 8328.0f, 48940.0f};
    for (int32 OrderedIndex = 0; OrderedIndex < StationKeys.Num(); ++OrderedIndex)
    {
        const int32 StationKey = StationKeys[OrderedIndex];
        const FSouthForkWaterBoundaryPair* Boundary =
            BoundaryByStation.Find(StationKey);
        if (!Boundary ||
            Boundary->MaximumLateralM - Boundary->MinimumLateralM < 18.0f ||
            Boundary->StationM - LastAcceptedStationM < 7.5f)
        {
            continue;
        }
        LastAcceptedStationM = Boundary->StationM;
        const FVector Center =
            (Boundary->MinimumWorldCm + Boundary->MaximumWorldCm) * 0.5;
        const FSouthForkWaterBoundaryPair* PreviousBoundary = BoundaryByStation.Find(
            StationKeys[FMath::Max(0, OrderedIndex - 4)]);
        const FSouthForkWaterBoundaryPair* NextBoundary = BoundaryByStation.Find(
            StationKeys[FMath::Min(StationKeys.Num() - 1, OrderedIndex + 4)]);
        const FVector PreviousCenter = PreviousBoundary
            ? (PreviousBoundary->MinimumWorldCm + PreviousBoundary->MaximumWorldCm) * 0.5
            : Center;
        const FVector NextCenter = NextBoundary
            ? (NextBoundary->MinimumWorldCm + NextBoundary->MaximumWorldCm) * 0.5
            : Center;
        FVector Incoming = Center - PreviousCenter;
        FVector Outgoing = NextCenter - Center;
        Incoming.Z = 0.0f;
        Outgoing.Z = 0.0f;
        Incoming.Normalize();
        Outgoing.Normalize();
        const FVector CurvatureVector = Outgoing - Incoming;
        const FVector BoundaryPositions[2] = {
            Boundary->MinimumWorldCm,
            Boundary->MaximumWorldCm};
        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
        {
            FVector Outward = BoundaryPositions[SideIndex] - Center;
            Outward.Z = 0.0;
            Outward = Outward.GetSafeNormal();
            if (Outward.IsNearlyZero())
            {
                continue;
            }
            const float SideCurvature = FVector::DotProduct(
                CurvatureVector, Outward);
            const bool bCutBank = SideCurvature < -0.0035f ||
                (FMath::Abs(SideCurvature) < 0.0035f &&
                 DerivedBankUnitRandom(StationKey / 32, SideIndex, 61) > 0.73f);
            const float PatchSignal =
                0.56f * FMath::Sin(
                    Boundary->StationM * 0.019f + SideIndex * 2.31f) +
                0.31f * FMath::Sin(
                    Boundary->StationM * 0.047f - SideIndex * 1.17f);
            float MorphologyWeight = FMath::SmoothStep(
                -0.10f, 0.58f, PatchSignal);
            for (const float ReviewStationM : ReviewStationsM)
            {
                const float DistanceM = FMath::Abs(
                    Boundary->StationM - ReviewStationM);
                if (DistanceM < 260.0f)
                {
                    MorphologyWeight = FMath::Max(
                        MorphologyWeight,
                        1.0f - FMath::SmoothStep(
                            70.0f, 260.0f, DistanceM));
                }
            }
            if (MorphologyWeight < 0.08f)
            {
                continue;
            }

            const float Variation = DerivedBankUnitRandom(
                StationKey, SideIndex, 71);
            const float ProfileWidthsCm[4] = {
                bCutBank
                    ? FMath::Lerp(75.0f, 135.0f, Variation)
                    : FMath::Lerp(180.0f, 290.0f, Variation),
                bCutBank
                    ? FMath::Lerp(120.0f, 210.0f, Variation)
                    : FMath::Lerp(390.0f, 610.0f, Variation),
                bCutBank
                    ? FMath::Lerp(310.0f, 520.0f, Variation)
                    : FMath::Lerp(680.0f, 980.0f, Variation),
                bCutBank
                    ? FMath::Lerp(620.0f, 880.0f, Variation)
                    : FMath::Lerp(1040.0f, 1420.0f, Variation)};
            FSouthForkBankReviewRow Row;
            Row.StationM = Boundary->StationM;
            Row.bCutBank = bCutBank;
            Row.MorphologyWeight = MorphologyWeight;
            Row.Positions[0] = BoundaryPositions[SideIndex] +
                Outward * 18.0f - FVector(0.0f, 0.0f, 8.0f);
            const float CutHeightCm = FMath::Lerp(
                105.0f, 245.0f,
                DerivedBankUnitRandom(StationKey / 8, SideIndex, 73));
            for (int32 WidthIndex = 0; WidthIndex < 4; ++WidthIndex)
            {
                FVector Position = BoundaryPositions[SideIndex] +
                    Outward * ProfileWidthsCm[WidthIndex];
                float TerrainZCm = 0.0f;
                if (FindDetailedTerrainSurfaceZCm(World, Position, TerrainZCm))
                {
                    ++TerrainTraceHitCount;
                }
                else
                {
                    TerrainZCm = BoundaryPositions[SideIndex].Z +
                        (bCutBank ? CutHeightCm : 45.0f);
                }
                float ShapedZCm = TerrainZCm + 3.0f;
                if (WidthIndex < 3)
                {
                    const float CutFractions[3] = {0.42f, 1.0f, 0.88f};
                    const float GravelRiseCm[3] = {12.0f, 32.0f, 52.0f};
                    const float TargetZCm = BoundaryPositions[SideIndex].Z +
                        (bCutBank
                            ? CutHeightCm * CutFractions[WidthIndex]
                            : GravelRiseCm[WidthIndex]);
                    ShapedZCm = FMath::Max(TerrainZCm + 3.0f, TargetZCm);
                }
                Position.Z = FMath::Lerp(
                    TerrainZCm + 3.0f, ShapedZCm, MorphologyWeight);
                if (WidthIndex < 3)
                {
                    Position.Z += FMath::Lerp(
                        -7.0f, 11.0f,
                        DerivedBankUnitRandom(
                            StationKey, SideIndex,
                            83 + WidthIndex * 11)) * MorphologyWeight;
                }
                Row.Positions[WidthIndex + 1] = Position;
            }
            const FLinearColor CutColors[5] = {
                FLinearColor(0.10f, 0.085f, 0.065f, 0.94f),
                FLinearColor(0.18f, 0.125f, 0.080f, 0.52f),
                FLinearColor(0.29f, 0.205f, 0.125f, 0.12f),
                FLinearColor(0.24f, 0.205f, 0.145f, 0.02f),
                FLinearColor(0.22f, 0.215f, 0.155f, 0.0f)};
            const FLinearColor GravelColors[5] = {
                FLinearColor(0.11f, 0.10f, 0.085f, 0.94f),
                FLinearColor(0.23f, 0.205f, 0.165f, 0.38f),
                FLinearColor(0.34f, 0.315f, 0.265f, 0.10f),
                FLinearColor(0.30f, 0.285f, 0.230f, 0.02f),
                FLinearColor(0.24f, 0.23f, 0.175f, 0.0f)};
            for (int32 ColumnIndex = 0; ColumnIndex < 5; ++ColumnIndex)
            {
                Row.Colors[ColumnIndex] = bCutBank
                    ? CutColors[ColumnIndex]
                    : GravelColors[ColumnIndex];
            }
            RowsBySide[SideIndex].Add(Row);
            if (bCutBank)
            {
                ++CutBankRowCount;
            }
            else
            {
                ++GravelBarRowCount;
            }

            const int32 RockAttempts = bCutBank ? 1 : 3;
            for (int32 RockAttempt = 0; RockAttempt < RockAttempts; ++RockAttempt)
            {
                const int32 AttemptSalt = RockAttempt * 37;
                if (DerivedBankUnitRandom(
                        StationKey, SideIndex, 101 + AttemptSalt) >
                    MorphologyWeight * (bCutBank ? 0.42f : 0.82f))
                {
                    continue;
                }
                const int32 MeshIndex = FMath::Clamp(
                    FMath::FloorToInt(
                        DerivedBankUnitRandom(
                            StationKey, SideIndex,
                            103 + AttemptSalt) * 6.0f),
                    0, 5);
                const FVector BoundsSize = EffectiveBounds[MeshIndex].GetSize();
                const float LongestCm = FMath::Max3(
                    BoundsSize.X, BoundsSize.Y, BoundsSize.Z);
                const float TargetLongestCm = FMath::Lerp(
                    16.0f, bCutBank ? 82.0f : 118.0f,
                    FMath::Pow(
                        DerivedBankUnitRandom(
                            StationKey, SideIndex,
                            107 + AttemptSalt),
                        1.55f));
                const float UniformScale = TargetLongestCm /
                    FMath::Max(LongestCm, 1.0f);
                const FVector RockScale(
                    UniformScale * FMath::Lerp(
                        0.82f, 1.22f,
                        DerivedBankUnitRandom(
                            StationKey, SideIndex, 109 + AttemptSalt)),
                    UniformScale * FMath::Lerp(
                        0.84f, 1.20f,
                        DerivedBankUnitRandom(
                            StationKey, SideIndex, 113 + AttemptSalt)),
                    UniformScale * FMath::Lerp(
                        0.56f, 0.86f,
                        DerivedBankUnitRandom(
                            StationKey, SideIndex, 127 + AttemptSalt)));
                const float AcrossT = FMath::Lerp(
                    0.05f, bCutBank ? 0.62f : 0.90f,
                    DerivedBankUnitRandom(
                        StationKey, SideIndex, 131 + AttemptSalt));
                FVector RockLocation = FMath::Lerp(
                    Row.Positions[0], Row.Positions[3], AcrossT);
                const float EffectiveHeightCm = BoundsSize.Z * RockScale.Z;
                RockLocation.Z += -EffectiveBounds[MeshIndex].Min.Z * RockScale.Z;
                RockLocation.Z -= EffectiveHeightCm * FMath::Lerp(
                    0.25f, 0.42f,
                    DerivedBankUnitRandom(
                        StationKey, SideIndex, 137 + AttemptSalt));
                FVector Along(-Outward.Y, Outward.X, 0.0f);
                RockLocation += Along * FMath::Lerp(
                    -260.0f, 260.0f,
                    DerivedBankUnitRandom(
                        StationKey, SideIndex, 139 + AttemptSalt));
                RockComponents[MeshIndex]->AddInstance(
                    FTransform(
                        FRotator(
                            FMath::Lerp(-10.0f, 10.0f,
                                DerivedBankUnitRandom(
                                    StationKey, SideIndex, 149 + AttemptSalt)),
                            Along.Rotation().Yaw + FMath::Lerp(-55.0f, 55.0f,
                                DerivedBankUnitRandom(
                                    StationKey, SideIndex, 151 + AttemptSalt)),
                            FMath::Lerp(-8.0f, 8.0f,
                                DerivedBankUnitRandom(
                                    StationKey, SideIndex, 157 + AttemptSalt))),
                        RockLocation,
                        RockScale),
                    /*bWorldSpace=*/true);
                ++RockInstanceCount;
            }

            if (bCutBank && MorphologyWeight > 0.42f &&
                DerivedBankUnitRandom(StationKey, SideIndex, 191) < 0.22f)
            {
                const FVector Along(-Outward.Y, Outward.X, 0.0f);
                const FVector RootStart = FMath::Lerp(
                    Row.Positions[2], Row.Positions[3], 0.35f) +
                    Along * FMath::Lerp(
                        -85.0f, 85.0f,
                        DerivedBankUnitRandom(StationKey, SideIndex, 193));
                const FVector RootJoint = FMath::Lerp(
                    RootStart, Row.Positions[1], 0.58f) +
                    Along * FMath::Lerp(
                        -38.0f, 38.0f,
                        DerivedBankUnitRandom(StationKey, SideIndex, 197)) -
                    Outward * 18.0f;
                const FVector RootEnd = FMath::Lerp(
                    Row.Positions[0], Row.Positions[1], 0.35f) +
                    Along * FMath::Lerp(
                        -65.0f, 65.0f,
                        DerivedBankUnitRandom(StationKey, SideIndex, 199));
                const float RootDiameterCm = FMath::Lerp(
                    4.0f, 10.0f,
                    DerivedBankUnitRandom(StationKey, SideIndex, 211));
                AddRootSegment(RootStart, RootJoint, RootDiameterCm);
                AddRootSegment(RootJoint, RootEnd, RootDiameterCm * 0.72f);
                RootSegmentCount += 2;
            }
        }
    }

    int32 StripSegmentCount = 0;
    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        TArray<FSouthForkBankReviewRow>& Rows = RowsBySide[SideIndex];
        for (int32 RowIndex = 0; RowIndex < Rows.Num(); ++RowIndex)
        {
            const FVector PreviousPosition = Rows[FMath::Max(RowIndex - 1, 0)].Positions[0];
            const FVector NextPosition = Rows[FMath::Min(RowIndex + 1, Rows.Num() - 1)].Positions[0];
            Rows[RowIndex].Along = (NextPosition - PreviousPosition).GetSafeNormal();
        }
        for (int32 RowIndex = 1; RowIndex < Rows.Num(); ++RowIndex)
        {
            const FSouthForkBankReviewRow& Previous = Rows[RowIndex - 1];
            const FSouthForkBankReviewRow& Current = Rows[RowIndex];
            const float StationGapM = Current.StationM - Previous.StationM;
            if (StationGapM <= 0.0f || StationGapM > 20.0f ||
                FVector::DistSquared2D(
                    Previous.Positions[0], Current.Positions[0]) >
                    FMath::Square(3600.0f))
            {
                continue;
            }
            AppendDerivedBankStripSegment(
                Previous, Current,
                Vertices, Triangles, Uvs, Colors, Tangents,
                /*bReverseWinding=*/SideIndex == 0);
            ++StripSegmentCount;
        }
    }
    if (StripSegmentCount < 1200 || RockInstanceCount < 1800 ||
        RootSegmentCount < 120)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += FString::Printf(
            TEXT("Derived-bank module review expected at least 1,200 segments, "
                 "1,800 rocks, and 120 root segments but built %d, %d, and %d.\n"),
            StripSegmentCount, RockInstanceCount, RootSegmentCount);
        return false;
    }
    const TArray<FVector> Normals =
        ComputePreviewMeshNormals(Vertices, Triangles);
    BankMesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, Uvs, Colors, Tangents,
        /*bCreateCollision=*/false);
    BankMesh->SetMaterial(0, BankMaterial);
    OutSummary += FString::Printf(
        TEXT("Transiently derived %d non-colliding erosion/deposition bank-module "
             "segments (%d triangles), %d terrain trace hits, %d cutbank rows, "
             "%d gravel-bar rows, %d 0.16-1.18 m scan-rock instances, and %d "
             "CC0-bark root segments from %d median-water actors and their "
             "station/lateral UVs; "
             "collision, hydraulics, navigation, maps, and asset packages remain "
             "unchanged.\n"),
        StripSegmentCount, Triangles.Num() / 3, TerrainTraceHitCount,
        CutBankRowCount, GravelBarRowCount, RockInstanceCount,
        RootSegmentCount, MedianWaterActorCount);
    return true;
}

void RestoreSouthForkDerivedBankMorphologyReview(
    const TArray<TWeakObjectPtr<AActor>>& Actors)
{
    for (const TWeakObjectPtr<AActor>& Actor : Actors)
    {
        if (Actor.IsValid())
        {
            Actor->Destroy();
        }
    }
}
} // namespace RaftSimEditorEnvironment
