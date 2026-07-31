#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "StaticMeshResources.h"

namespace RaftSimEditorEnvironment
{
namespace
{
struct FScannedBankWaterBoundary
{
    float StationM = 0.0f;
    float MinimumLateralM = BIG_NUMBER;
    float MaximumLateralM = -BIG_NUMBER;
    FVector MinimumWorldCm = FVector::ZeroVector;
    FVector MaximumWorldCm = FVector::ZeroVector;
};

float ScannedBankUnitRandom(int32 StationKey, int32 SideIndex, int32 Salt)
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

bool FindScannedBankTerrainSurface(
    UWorld* World,
    const FVector& XYAndReferenceZ,
    FVector& OutSurfaceWorldCm,
    FVector& OutSurfaceNormal)
{
    if (!World)
    {
        return false;
    }
    TArray<FHitResult> Hits;
    FCollisionQueryParams QueryParams(
        SCENE_QUERY_STAT(RaftSimScannedBankTerrainSurface),
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
            OutSurfaceWorldCm = Hit.ImpactPoint;
            OutSurfaceNormal = Hit.ImpactNormal.GetSafeNormal();
            return true;
        }
    }
    return false;
}

UHierarchicalInstancedStaticMeshComponent* CreateScannedBankComponent(
    AActor* Owner,
    USceneComponent* Root,
    const FName Name,
    UStaticMesh* Mesh,
    UMaterialInterface* Material,
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
    if (Material)
    {
        Component->SetMaterial(0, Material);
    }
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetCullDistances(StartCullDistanceCm, EndCullDistanceCm);
    Component->bEnableDensityScaling = false;
    Component->RegisterComponent();
    return Component;
}

bool IsNearScannedBankReviewStation(float StationM, float& OutWeight)
{
    const float ReviewStationsM[] = {
        120.0f, 944.0f, 5100.0f, 8328.0f, 48940.0f};
    OutWeight = 0.0f;
    for (const float ReviewStationM : ReviewStationsM)
    {
        const float DistanceM = FMath::Abs(StationM - ReviewStationM);
        if (DistanceM < 260.0f)
        {
            OutWeight = FMath::Max(
                OutWeight,
                1.0f - FMath::SmoothStep(150.0f, 260.0f, DistanceM));
        }
    }
    return OutWeight > 0.0f;
}
} // namespace

bool ConfigureSouthForkScannedBankKitReview(
    UWorld* World,
    TArray<TWeakObjectPtr<AActor>>& OutActors,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("South Fork scanned bank-kit review has no loaded world.\n");
        return false;
    }

    const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
    const FName SolverFoamTag(TEXT("RaftSimSolverFoamOverlay"));
    TMap<int32, FScannedBankWaterBoundary> BoundaryByStation;
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
            FScannedBankWaterBoundary& Boundary =
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
            TEXT("Scanned bank-kit review expected at least 13 median-water actors "
                 "and 5,000 station samples but found %d and %d.\n"),
            MedianWaterActorCount, StationKeys.Num());
        return false;
    }

    const FString BankKitRoot =
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "SouthForkBankKit_2K/");
    UStaticMesh* RockFaceMesh = LoadObject<UStaticMesh>(
        nullptr, *(BankKitRoot + TEXT("SM_RockFace01.SM_RockFace01")));
    UStaticMesh* StumpMesh = LoadObject<UStaticMesh>(
        nullptr, *(BankKitRoot + TEXT("SM_TreeStump02.SM_TreeStump02")));
    UStaticMesh* PlaneMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));
    UMaterialInterface* RootsMaterial = LoadObject<UMaterialInterface>(
        nullptr, *(BankKitRoot + TEXT("M_Roots_ReviewLit.M_Roots_ReviewLit")));
    UMaterialInterface* GravelMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        *(BankKitRoot + TEXT("M_RockyGravel_ReviewLit.M_RockyGravel_ReviewLit")));
    if (!RockFaceMesh || !StumpMesh || !PlaneMesh ||
        !RootsMaterial || !GravelMaterial)
    {
        OutSummary += TEXT("South Fork scanned bank-kit review assets are unavailable.\n");
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
    ReviewActor->SetActorLabel(TEXT("RaftSim_ScannedBankKitReview"));
    USceneComponent* Root = NewObject<USceneComponent>(
        ReviewActor, TEXT("ScannedBankKitReviewRoot"), RF_Transient);
    ReviewActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    ReviewActor->SetRootComponent(Root);
    OutActors.Add(ReviewActor);

    UHierarchicalInstancedStaticMeshComponent* RockFaces =
        CreateScannedBankComponent(
            ReviewActor, Root, TEXT("ScannedBankRockFaces"),
            RockFaceMesh, nullptr, 180000, 520000);
    UHierarchicalInstancedStaticMeshComponent* Stumps =
        CreateScannedBankComponent(
            ReviewActor, Root, TEXT("ScannedBankRootWads"),
            StumpMesh, nullptr, 140000, 420000);
    UHierarchicalInstancedStaticMeshComponent* RootPatches =
        CreateScannedBankComponent(
            ReviewActor, Root, TEXT("ScannedBankRootSurfacePatches"),
            PlaneMesh, RootsMaterial, 120000, 360000);
    UHierarchicalInstancedStaticMeshComponent* GravelPatches =
        CreateScannedBankComponent(
            ReviewActor, Root, TEXT("ScannedBankGravelSurfacePatches"),
            PlaneMesh, GravelMaterial, 120000, 360000);
    if (!RockFaces || !Stumps || !RootPatches || !GravelPatches)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        return false;
    }

    int32 RockFaceCount = 0;
    int32 StumpCount = 0;
    int32 RootPatchCount = 0;
    int32 GravelPatchCount = 0;
    int32 TerrainTraceHitCount = 0;
    float LastAcceptedStationM = -BIG_NUMBER;
    for (int32 OrderedIndex = 0; OrderedIndex < StationKeys.Num(); ++OrderedIndex)
    {
        const int32 StationKey = StationKeys[OrderedIndex];
        const FScannedBankWaterBoundary* Boundary =
            BoundaryByStation.Find(StationKey);
        float StationReviewWeight = 0.0f;
        if (!Boundary ||
            Boundary->MaximumLateralM - Boundary->MinimumLateralM < 18.0f ||
            Boundary->StationM - LastAcceptedStationM < 9.0f ||
            !IsNearScannedBankReviewStation(
                Boundary->StationM, StationReviewWeight))
        {
            continue;
        }
        LastAcceptedStationM = Boundary->StationM;
        const FVector Center =
            (Boundary->MinimumWorldCm + Boundary->MaximumWorldCm) * 0.5;
        const FScannedBankWaterBoundary* PreviousBoundary =
            BoundaryByStation.Find(
                StationKeys[FMath::Max(0, OrderedIndex - 4)]);
        const FScannedBankWaterBoundary* NextBoundary =
            BoundaryByStation.Find(
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
        FVector Along = NextCenter - PreviousCenter;
        Along.Z = 0.0f;
        Along = Along.GetSafeNormal();
        if (Along.IsNearlyZero())
        {
            continue;
        }
        const FVector Curvature = Outgoing - Incoming;
        const FVector BoundaryPositions[2] = {
            Boundary->MinimumWorldCm,
            Boundary->MaximumWorldCm};
        FVector OutwardBySide[2];
        float CurvatureBySide[2] = {};
        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
        {
            OutwardBySide[SideIndex] = BoundaryPositions[SideIndex] - Center;
            OutwardBySide[SideIndex].Z = 0.0f;
            OutwardBySide[SideIndex] = OutwardBySide[SideIndex].GetSafeNormal();
            CurvatureBySide[SideIndex] = FVector::DotProduct(
                Curvature, OutwardBySide[SideIndex]);
        }
        int32 CutBankSide = CurvatureBySide[0] < CurvatureBySide[1] ? 0 : 1;
        if (FMath::Abs(CurvatureBySide[0] - CurvatureBySide[1]) < 0.004f)
        {
            CutBankSide = ScannedBankUnitRandom(
                StationKey / 16, 0, 31) < 0.5f ? 0 : 1;
        }

        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
        {
            const FVector Outward = OutwardBySide[SideIndex];
            if (Outward.IsNearlyZero())
            {
                continue;
            }
            const bool bCutBank = SideIndex == CutBankSide;
            const float Selection = ScannedBankUnitRandom(
                StationKey / 36, SideIndex, 41);
            if (bCutBank && Selection < 0.72f)
            {
                const float OffsetCm = FMath::Lerp(
                    160.0f, 310.0f,
                    ScannedBankUnitRandom(StationKey, SideIndex, 43));
                FVector Surface;
                FVector SurfaceNormal;
                if (FindScannedBankTerrainSurface(
                        World,
                        BoundaryPositions[SideIndex] + Outward * OffsetCm,
                        Surface, SurfaceNormal))
                {
                    ++TerrainTraceHitCount;
                    const float UniformScale = FMath::Lerp(
                        0.48f, 0.76f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 47));
                    const FRotator Rotation(
                        FMath::Lerp(-7.0f, 9.0f,
                            ScannedBankUnitRandom(StationKey, SideIndex, 53)),
                        Along.Rotation().Yaw +
                            FMath::Lerp(-13.0f, 13.0f,
                                ScannedBankUnitRandom(StationKey, SideIndex, 59)),
                        FMath::Lerp(-5.0f, 5.0f,
                            ScannedBankUnitRandom(StationKey, SideIndex, 61)));
                    Surface.Z = FMath::Max(
                        Surface.Z, BoundaryPositions[SideIndex].Z - 70.0f);
                    Surface.Z -= FMath::Lerp(
                        90.0f, 150.0f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 67));
                    RockFaces->AddInstance(
                        FTransform(
                            Rotation,
                            Surface,
                            FVector(
                                UniformScale,
                                UniformScale * FMath::Lerp(0.48f, 0.70f,
                                    ScannedBankUnitRandom(
                                        StationKey, SideIndex, 71)),
                                UniformScale)),
                        /*bWorldSpace=*/true);
                    ++RockFaceCount;
                }
            }
            if (bCutBank &&
                ScannedBankUnitRandom(
                    StationKey / 120, SideIndex, 73) < 0.34f)
            {
                const float OffsetCm = FMath::Lerp(
                    260.0f, 480.0f,
                    ScannedBankUnitRandom(StationKey, SideIndex, 79));
                FVector Surface;
                FVector SurfaceNormal;
                if (FindScannedBankTerrainSurface(
                        World,
                        BoundaryPositions[SideIndex] + Outward * OffsetCm,
                        Surface, SurfaceNormal))
                {
                    ++TerrainTraceHitCount;
                    const float Scale = FMath::Lerp(
                        0.88f, 1.34f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 83));
                    const FVector TiltAxis = FVector::CrossProduct(
                        FVector::UpVector, Outward).GetSafeNormal();
                    const FQuat Tilt(
                        TiltAxis,
                        FMath::DegreesToRadians(FMath::Lerp(
                            18.0f, 42.0f,
                            ScannedBankUnitRandom(StationKey, SideIndex, 89))));
                    const FQuat Yaw(
                        FVector::UpVector,
                        FMath::DegreesToRadians(
                            ScannedBankUnitRandom(
                                StationKey, SideIndex, 97) * 360.0f));
                    Surface.Z -= 8.0f;
                    Stumps->AddInstance(
                        FTransform(Yaw * Tilt, Surface, FVector(Scale)),
                        /*bWorldSpace=*/true);
                    ++StumpCount;
                }
            }

            const bool bPlaceSurfacePatch =
                ScannedBankUnitRandom(
                    StationKey / 48, SideIndex, bCutBank ? 101 : 103) <
                FMath::Lerp(0.34f, 0.62f, StationReviewWeight);
            if (bPlaceSurfacePatch)
            {
                const float OffsetCm = bCutBank
                    ? FMath::Lerp(330.0f, 560.0f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 107))
                    : FMath::Lerp(280.0f, 720.0f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 109));
                FVector Surface;
                FVector SurfaceNormal;
                if (FindScannedBankTerrainSurface(
                        World,
                        BoundaryPositions[SideIndex] + Outward * OffsetCm,
                        Surface, SurfaceNormal))
                {
                    ++TerrainTraceHitCount;
                    const FQuat SurfaceRotation = FQuat::FindBetweenNormals(
                        FVector::UpVector, SurfaceNormal);
                    const FQuat Yaw(
                        FVector::UpVector,
                        FMath::DegreesToRadians(
                            ScannedBankUnitRandom(
                                StationKey, SideIndex, 113) * 360.0f));
                    const float ScaleX = FMath::Lerp(
                        1.7f, 3.2f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 127));
                    const float ScaleY = FMath::Lerp(
                        1.3f, 2.5f,
                        ScannedBankUnitRandom(StationKey, SideIndex, 131));
                    Surface += SurfaceNormal * 1.2f;
                    UHierarchicalInstancedStaticMeshComponent* Patches =
                        bCutBank ? RootPatches : GravelPatches;
                    Patches->AddInstance(
                        FTransform(
                            Yaw * SurfaceRotation,
                            Surface,
                            FVector(ScaleX, ScaleY, 1.0f)),
                        /*bWorldSpace=*/true);
                    if (bCutBank)
                    {
                        ++RootPatchCount;
                    }
                    else
                    {
                        ++GravelPatchCount;
                    }
                }
            }
        }
    }

    if (RockFaceCount < 55 || StumpCount < 12 ||
        RootPatchCount < 35 || GravelPatchCount < 35 ||
        TerrainTraceHitCount < 140)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += FString::Printf(
            TEXT("Scanned bank-kit review expected at least 55 rock faces, 12 "
                 "stumps, 35 root patches, 35 gravel patches, and 140 terrain "
                 "trace hits but built %d, %d, %d, %d, and %d.\n"),
            RockFaceCount, StumpCount, RootPatchCount, GravelPatchCount,
            TerrainTraceHitCount);
        return false;
    }

    OutSummary += FString::Printf(
        TEXT("Transiently placed %d publisher-scale Rock Face 01 scans, %d Tree "
             "Stump 02 exposed-root scans, %d roots surface patches, and %d "
             "rocky-gravel patches from %d median-water actors and %d terrain "
             "trace hits near five fixed review stations; every component is "
             "non-colliding, non-navigable, transient, and unsaved, and water, "
             "hydraulics, gameplay, source terrain, and maps remain unchanged.\n"),
        RockFaceCount, StumpCount, RootPatchCount, GravelPatchCount,
        MedianWaterActorCount, TerrainTraceHitCount);
    return true;
}
} // namespace RaftSimEditorEnvironment
