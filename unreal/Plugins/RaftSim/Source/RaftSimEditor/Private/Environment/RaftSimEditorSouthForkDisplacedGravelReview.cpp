#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "StaticMeshResources.h"

namespace RaftSimEditorEnvironment
{
namespace
{
struct FDisplacedGravelWaterBoundary
{
    float StationM = 0.0f;
    float MinimumLateralM = BIG_NUMBER;
    float MaximumLateralM = -BIG_NUMBER;
    FVector MinimumWorldCm = FVector::ZeroVector;
    FVector MaximumWorldCm = FVector::ZeroVector;
};

bool FindDisplacedGravelTerrainSurfaceZCm(
    UWorld* World,
    const FVector& XYAndReferenceZ,
    float& OutSurfaceZCm)
{
    TArray<FHitResult> Hits;
    FCollisionQueryParams QueryParams(
        SCENE_QUERY_STAT(RaftSimDisplacedGravelTerrainSurface),
        /*bTraceComplex=*/true);
    const FVector Start(
        XYAndReferenceZ.X,
        XYAndReferenceZ.Y,
        XYAndReferenceZ.Z + 12000.0f);
    const FVector End(
        XYAndReferenceZ.X,
        XYAndReferenceZ.Y,
        XYAndReferenceZ.Z - 12000.0f);
    if (!World || !World->LineTraceMultiByChannel(
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

float SampleDisplacedGravelHeight(
    const TArray64<uint8>& Bytes,
    int32 Width,
    int32 Height,
    int64 BytesPerPixel,
    float U,
    float V)
{
    float WrappedU = FMath::Frac(U);
    float WrappedV = FMath::Frac(V);
    if (WrappedU < 0.0f)
    {
        WrappedU += 1.0f;
    }
    if (WrappedV < 0.0f)
    {
        WrappedV += 1.0f;
    }
    const float X = WrappedU * static_cast<float>(Width - 1);
    const float Y = WrappedV * static_cast<float>(Height - 1);
    const int32 X0 = FMath::FloorToInt(X);
    const int32 Y0 = FMath::FloorToInt(Y);
    const int32 X1 = (X0 + 1) % Width;
    const int32 Y1 = (Y0 + 1) % Height;
    const float Tx = X - static_cast<float>(X0);
    const float Ty = Y - static_cast<float>(Y0);
    auto Read = [&Bytes, Width, BytesPerPixel](int32 PixelX, int32 PixelY)
    {
        const int64 Offset =
            (static_cast<int64>(PixelY) * Width + PixelX) * BytesPerPixel;
        return static_cast<float>(Bytes[Offset]);
    };
    const float A = FMath::Lerp(Read(X0, Y0), Read(X1, Y0), Tx);
    const float B = FMath::Lerp(Read(X0, Y1), Read(X1, Y1), Tx);
    return FMath::Lerp(A, B, Ty);
}

UMaterialInterface* CreateDisplacedGravelMaterial(AActor* Owner)
{
    UMaterialInterface* Parent = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    UTexture2D* Albedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RiverSmallRocks_2K/T_RiverSmallRocks_BaseColor_2K."
             "T_RiverSmallRocks_BaseColor_2K"));
    UTexture2D* Normal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RiverSmallRocks_2K/T_RiverSmallRocks_NormalGL_2K."
             "T_RiverSmallRocks_NormalGL_2K"));
    UTexture2D* Packed = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RiverSmallRocks_2K/T_RiverSmallRocks_ARM_2K."
             "T_RiverSmallRocks_ARM_2K"));
    UMaterialInstanceDynamic* Material = Parent
        ? UMaterialInstanceDynamic::Create(Parent, Owner)
        : nullptr;
    if (!Material || !Albedo || !Normal || !Packed)
    {
        return nullptr;
    }
    Material->SetTextureParameterValue(TEXT("GroundAlbedo"), Albedo);
    Material->SetTextureParameterValue(TEXT("GroundNormal"), Normal);
    Material->SetTextureParameterValue(TEXT("GroundPacked"), Packed);
    Material->SetScalarParameterValue(TEXT("UseSourceMacroTexture"), 0.0f);
    Material->SetScalarParameterValue(TEXT("UseCorridorEdgeBlend"), 0.0f);
    Material->SetScalarParameterValue(TEXT("SourceMacroInfluence"), 0.42f);
    Material->SetScalarParameterValue(TEXT("RockAlbedoStrength"), 0.30f);
    Material->SetScalarParameterValue(TEXT("TerrainSpecular"), 0.02f);
    Material->SetVectorParameterValue(
        TEXT("SourceMacroTone"), FLinearColor(0.50f, 0.52f, 0.48f, 1.0f));
    return Material;
}
} // namespace

bool ConfigureSouthForkDisplacedGravelBarReview(
    UWorld* World,
    TArray<TWeakObjectPtr<AActor>>& OutActors,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("Displaced gravel-bar review has no loaded world.\n");
        return false;
    }

    UTexture2D* Displacement = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RiverSmallRocks_2K/T_RiverSmallRocks_Displacement_2K."
             "T_RiverSmallRocks_Displacement_2K"));
    const int32 TextureWidth = Displacement
        ? Displacement->Source.GetSizeX()
        : 0;
    const int32 TextureHeight = Displacement
        ? Displacement->Source.GetSizeY()
        : 0;
    const int64 BytesPerPixel = Displacement
        ? Displacement->Source.GetBytesPerPixel()
        : 0;
    TArray64<uint8> DisplacementBytes;
    if (!Displacement || TextureWidth != 2048 || TextureHeight != 2048 ||
        BytesPerPixel < 1 ||
        !Displacement->Source.GetMipData(DisplacementBytes, 0) ||
        DisplacementBytes.Num() !=
            static_cast<int64>(TextureWidth) * TextureHeight * BytesPerPixel)
    {
        OutSummary += FString::Printf(
            TEXT("Displaced gravel-bar source is unavailable or invalid: "
                 "%dx%d, %lld bytes per pixel, %lld source bytes.\n"),
            TextureWidth,
            TextureHeight,
            BytesPerPixel,
            DisplacementBytes.Num());
        return false;
    }

    const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
    const FName SolverFoamTag(TEXT("RaftSimSolverFoamOverlay"));
    TMap<int32, FDisplacedGravelWaterBoundary> BoundaryByStation;
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
        UStaticMesh* StaticMesh = Component
            ? Component->GetStaticMesh()
            : nullptr;
        const FStaticMeshRenderData* RenderData = StaticMesh
            ? StaticMesh->GetRenderData()
            : nullptr;
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
                StationM < 768.0f || StationM > 1164.0f ||
                FMath::Abs(LateralM) > 45.0f)
            {
                continue;
            }
            const int32 StationKey = FMath::RoundToInt(StationM * 4.0f);
            FDisplacedGravelWaterBoundary& Boundary =
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
    if (MedianWaterActorCount < 1 || StationKeys.Num() < 80)
    {
        OutSummary += FString::Printf(
            TEXT("Displaced gravel-bar review expected a Meat Grinder water "
                 "window with at least 80 rows but found %d actors and %d rows.\n"),
            MedianWaterActorCount,
            StationKeys.Num());
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
    ReviewActor->SetActorLabel(TEXT("RaftSim_DisplacedGravelBarReview"));
    USceneComponent* Root = NewObject<USceneComponent>(
        ReviewActor, TEXT("DisplacedGravelRoot"), RF_Transient);
    ReviewActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    ReviewActor->SetRootComponent(Root);
    UProceduralMeshComponent* GravelMesh = NewObject<UProceduralMeshComponent>(
        ReviewActor, TEXT("DisplacedGravelMesh"), RF_Transient);
    ReviewActor->AddInstanceComponent(GravelMesh);
    GravelMesh->SetupAttachment(Root);
    GravelMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GravelMesh->SetCanEverAffectNavigation(false);
    GravelMesh->SetCastShadow(true);
    GravelMesh->RegisterComponent();
    OutActors.Add(ReviewActor);

    UMaterialInterface* Material = CreateDisplacedGravelMaterial(ReviewActor);
    if (!Material)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += TEXT("Displaced gravel-bar review material is unavailable.\n");
        return false;
    }

    constexpr int32 AcrossColumnCount = 13;
    constexpr float AcrossWidthCm = 420.0f;
    constexpr float WaterEdgeOffsetCm = 18.0f;
    constexpr float TargetAlongSpacingM = 0.55f;
    constexpr float PhysicalRepeatM = 2.9f;
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    int32 TerrainTraceHits = 0;
    int32 AcceptedRows = 0;
    int32 ConnectedSegments = 0;

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        int32 PreviousRowBase = INDEX_NONE;
        FVector PreviousBoundaryPosition = FVector::ZeroVector;
        float PreviousStationM = -BIG_NUMBER;
        for (int32 KeyIndex = 0; KeyIndex + 1 < StationKeys.Num(); ++KeyIndex)
        {
            const FDisplacedGravelWaterBoundary* BoundaryA =
                BoundaryByStation.Find(StationKeys[KeyIndex]);
            const FDisplacedGravelWaterBoundary* BoundaryB =
                BoundaryByStation.Find(StationKeys[KeyIndex + 1]);
            if (!BoundaryA || !BoundaryB ||
                BoundaryA->MaximumLateralM - BoundaryA->MinimumLateralM < 18.0f ||
                BoundaryB->MaximumLateralM - BoundaryB->MinimumLateralM < 18.0f)
            {
                PreviousRowBase = INDEX_NONE;
                continue;
            }
            const float StationGapM =
                BoundaryB->StationM - BoundaryA->StationM;
            if (StationGapM <= 0.0f || StationGapM > 8.0f)
            {
                PreviousRowBase = INDEX_NONE;
                continue;
            }
            const int32 StepCount = FMath::Max(
                1, FMath::CeilToInt(StationGapM / TargetAlongSpacingM));
            for (int32 StepIndex = 0; StepIndex < StepCount; ++StepIndex)
            {
                const float Alpha =
                    static_cast<float>(StepIndex) / StepCount;
                const float StationM = FMath::Lerp(
                    BoundaryA->StationM, BoundaryB->StationM, Alpha);
                const FVector Minimum = FMath::Lerp(
                    BoundaryA->MinimumWorldCm,
                    BoundaryB->MinimumWorldCm,
                    Alpha);
                const FVector Maximum = FMath::Lerp(
                    BoundaryA->MaximumWorldCm,
                    BoundaryB->MaximumWorldCm,
                    Alpha);
                const FVector Center = (Minimum + Maximum) * 0.5f;
                const FVector BoundaryPosition = SideIndex == 0
                    ? Minimum
                    : Maximum;
                FVector Outward = BoundaryPosition - Center;
                Outward.Z = 0.0f;
                Outward.Normalize();
                FVector Along =
                    BoundaryB->MinimumWorldCm + BoundaryB->MaximumWorldCm -
                    BoundaryA->MinimumWorldCm - BoundaryA->MaximumWorldCm;
                Along.Z = 0.0f;
                Along.Normalize();
                if (Outward.IsNearlyZero() || Along.IsNearlyZero())
                {
                    PreviousRowBase = INDEX_NONE;
                    continue;
                }

                TArray<FVector, TInlineAllocator<AcrossColumnCount>> RowVertices;
                RowVertices.Reserve(AcrossColumnCount);
                bool bCompleteRow = true;
                for (int32 ColumnIndex = 0;
                     ColumnIndex < AcrossColumnCount;
                     ++ColumnIndex)
                {
                    const float AcrossAlpha =
                        static_cast<float>(ColumnIndex) /
                        (AcrossColumnCount - 1);
                    const float AcrossCm = AcrossAlpha * AcrossWidthCm;
                    FVector Position = BoundaryPosition +
                        Outward * (WaterEdgeOffsetCm + AcrossCm);
                    float TerrainZCm = 0.0f;
                    if (!FindDisplacedGravelTerrainSurfaceZCm(
                            World, Position, TerrainZCm))
                    {
                        bCompleteRow = false;
                        break;
                    }
                    ++TerrainTraceHits;
                    const float AlongFade =
                        FMath::SmoothStep(768.0f, 780.0f, StationM) *
                        (1.0f - FMath::SmoothStep(
                            1152.0f, 1164.0f, StationM));
                    const float AcrossFade =
                        FMath::SmoothStep(0.0f, 0.16f, AcrossAlpha) *
                        (1.0f - FMath::SmoothStep(
                            0.78f, 1.0f, AcrossAlpha));
                    const float EdgeFade = AlongFade * AcrossFade;
                    const float SourceHeight = SampleDisplacedGravelHeight(
                        DisplacementBytes,
                        TextureWidth,
                        TextureHeight,
                        BytesPerPixel,
                        StationM / PhysicalRepeatM + SideIndex * 0.37f,
                        AcrossCm * 0.01f / PhysicalRepeatM + SideIndex * 0.19f);
                    const float NormalizedHeight = FMath::Clamp(
                        (SourceHeight - 95.0f) / (177.0f - 95.0f),
                        0.0f,
                        1.0f);
                    // v206 let the underlying DEM occlude low displacement
                    // values, exposing contour-like pale ribbons. Keep the
                    // feathered boundary below the source terrain, but lift
                    // the fully weighted interior by 10-22 cm so the reviewed
                    // scan reads as one continuous non-colliding gravel bar.
                    Position.Z = TerrainZCm - 2.0f +
                        EdgeFade * (12.0f + NormalizedHeight * 12.0f);
                    RowVertices.Add(Position);
                }
                if (!bCompleteRow || RowVertices.Num() != AcrossColumnCount)
                {
                    PreviousRowBase = INDEX_NONE;
                    continue;
                }

                const int32 RowBase = Vertices.Num();
                for (int32 ColumnIndex = 0;
                     ColumnIndex < AcrossColumnCount;
                     ++ColumnIndex)
                {
                    const float AcrossAlpha =
                        static_cast<float>(ColumnIndex) /
                        (AcrossColumnCount - 1);
                    Vertices.Add(RowVertices[ColumnIndex]);
                    Uvs.Add(FVector2D(
                        StationM / PhysicalRepeatM,
                        AcrossAlpha * AcrossWidthCm * 0.01f /
                            PhysicalRepeatM));
                    Colors.Add(FLinearColor(
                        0.34f,
                        0.30f,
                        0.22f,
                        FMath::Lerp(0.82f, 0.0f, AcrossAlpha)));
                    Tangents.Add(FProcMeshTangent(Along, false));
                }
                if (PreviousRowBase != INDEX_NONE &&
                    StationM - PreviousStationM < 1.1f &&
                    FVector::DistSquared2D(
                        BoundaryPosition, PreviousBoundaryPosition) <
                        FMath::Square(180.0f))
                {
                    for (int32 ColumnIndex = 0;
                         ColumnIndex + 1 < AcrossColumnCount;
                         ++ColumnIndex)
                    {
                        const int32 A0 = PreviousRowBase + ColumnIndex;
                        const int32 A1 = A0 + 1;
                        const int32 B0 = RowBase + ColumnIndex;
                        const int32 B1 = B0 + 1;
                        if (SideIndex == 0)
                        {
                            Triangles.Append({A0, A1, B0, A1, B1, B0});
                        }
                        else
                        {
                            Triangles.Append({A0, B0, A1, A1, B0, B1});
                        }
                    }
                    ++ConnectedSegments;
                }
                PreviousRowBase = RowBase;
                PreviousBoundaryPosition = BoundaryPosition;
                PreviousStationM = StationM;
                ++AcceptedRows;
            }
        }
    }

    if (AcceptedRows < 800 || ConnectedSegments < 700 ||
        TerrainTraceHits < 10000 || Triangles.Num() < 16000)
    {
        RestoreSouthForkDerivedBankMorphologyReview(OutActors);
        OutSummary += FString::Printf(
            TEXT("Displaced gravel-bar coverage gate failed: %d rows, %d "
                 "segments, %d terrain hits, and %d triangles.\n"),
            AcceptedRows,
            ConnectedSegments,
            TerrainTraceHits,
            Triangles.Num() / 3);
        return false;
    }

    const TArray<FVector> Normals =
        ComputePreviewMeshNormals(Vertices, Triangles);
    GravelMesh->CreateMeshSection_LinearColor(
        0,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors,
        Tangents,
        /*bCreateCollision=*/false);
    GravelMesh->SetMaterial(0, Material);
    OutSummary += FString::Printf(
        TEXT("Transiently built a 768-1164 m Meat Grinder gravel band from "
             "%d official displacement-driven rows, %d DEM terrain traces, "
             "and %d non-colliding triangles at the published 2.9 m repeat; "
             "collision, hydraulics, water, navigation, maps, materials, and "
             "runtime packages remain unchanged.\n"),
        AcceptedRows,
        TerrainTraceHits,
        Triangles.Num() / 3);
    return true;
}
} // namespace RaftSimEditorEnvironment
