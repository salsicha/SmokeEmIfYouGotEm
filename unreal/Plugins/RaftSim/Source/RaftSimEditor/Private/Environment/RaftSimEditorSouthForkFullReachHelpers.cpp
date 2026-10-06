#include "Environment/RaftSimEditorSouthForkFullReachInternal.h"

namespace RaftSimEditorEnvironment::SouthForkFullReach
{
FString AbsoluteRepoPath(const FString& RelativePath)
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
}
FGuid SouthForkActorGuid(UClass* ActorClass, const FString& Label)
{
    const FString StableKey = FString::Printf(
        TEXT("%s|%s|%s"),
        FullReachMapPackagePath,
        ActorClass ? *ActorClass->GetPathName() : TEXT("None"),
        *Label);
    return FGuid::NewDeterministicGuid(StableKey);
}
FName SouthForkActorObjectName(UClass* ActorClass, const FString& Label)
{
    return FName(*FString::Printf(
        TEXT("RaftSim_%s"),
        *SouthForkActorGuid(ActorClass, Label).ToString(EGuidFormats::Digits)));
}
bool ReplaceWorldPartitionMiniMapWithStableActor(UWorld* World, FString& OutSummary)
{
    TArray<AWorldPartitionMiniMap*> ExistingMiniMaps;
    for (TActorIterator<AWorldPartitionMiniMap> It(World); It; ++It)
    {
        ExistingMiniMaps.Add(*It);
    }
    for (AWorldPartitionMiniMap* MiniMap : ExistingMiniMaps)
    {
        if (!World->DestroyActor(MiniMap))
        {
            OutSummary += TEXT("Failed to remove the editor-created World Partition minimap.\n");
            return false;
        }
    }

    AWorldPartitionMiniMap* MiniMap =
        SpawnStableSouthForkActor<AWorldPartitionMiniMap>(
            World,
            FTransform::Identity,
            TEXT("RaftSim_SouthFork_WorldPartitionMiniMap"));
    if (!MiniMap)
    {
        OutSummary += TEXT("Failed to create the deterministic World Partition minimap.\n");
        return false;
    }
    MiniMap->SetActorLabel(TEXT("RaftSim_SouthFork_WorldPartitionMiniMap"));
    SetSpatiallyLoadedIfAllowed(MiniMap, false);
    return true;
}
bool LoadJsonObject(const FString& RelativePath, TSharedPtr<FJsonObject>& OutRoot)
{
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *AbsoluteRepoPath(RelativePath)))
    {
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    return FJsonSerializer::Deserialize(Reader, OutRoot) && OutRoot.IsValid();
}
bool LoadGray16Png(const FString& RelativePath, FSouthForkGray16Image& OutImage)
{
    OutImage = FSouthForkGray16Image();
    TArray<uint8> Compressed;
    const FString AbsolutePath = AbsoluteRepoPath(RelativePath);
    if (!FFileHelper::LoadFileToArray(Compressed, *AbsolutePath))
    {
        return false;
    }
    IImageWrapperModule& WrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
    TSharedPtr<IImageWrapper> Wrapper =
        WrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!Wrapper.IsValid() ||
        !Wrapper->SetCompressed(Compressed.GetData(), Compressed.Num()))
    {
        return false;
    }
    TArray<uint8> Raw;
    if (!Wrapper->GetRaw(ERGBFormat::Gray, 16, Raw))
    {
        return false;
    }
    OutImage.Width = Wrapper->GetWidth();
    OutImage.Height = Wrapper->GetHeight();
    if (OutImage.Width <= 0 || OutImage.Height <= 0 ||
        Raw.Num() != OutImage.Width * OutImage.Height * 2)
    {
        return false;
    }
    OutImage.Values.SetNumUninitialized(OutImage.Width * OutImage.Height);
    FMemory::Memcpy(
        OutImage.Values.GetData(), Raw.GetData(),
        OutImage.Values.Num() * static_cast<int32>(sizeof(uint16)));
    // IImageWrapper returns host-order Gray16 samples. Keep this copy explicit:
    // applying PNG's network byte order a second time creates saw-tooth cliffs.
    int64 LargeNeighborJumpCount = 0;
    int64 NeighborPairCount = 0;
    for (int32 Y = 0; Y < OutImage.Height; ++Y)
    {
        for (int32 X = 0; X < OutImage.Width; ++X)
        {
            const int32 Index = Y * OutImage.Width + X;
            if (X + 1 < OutImage.Width)
            {
                LargeNeighborJumpCount += FMath::Abs(
                    static_cast<int32>(OutImage.Values[Index]) -
                    static_cast<int32>(OutImage.Values[Index + 1])) > 20000;
                ++NeighborPairCount;
            }
            if (Y + 1 < OutImage.Height)
            {
                LargeNeighborJumpCount += FMath::Abs(
                    static_cast<int32>(OutImage.Values[Index]) -
                    static_cast<int32>(OutImage.Values[Index + OutImage.Width])) > 20000;
                ++NeighborPairCount;
            }
        }
    }
    if (NeighborPairCount > 0 &&
        static_cast<double>(LargeNeighborJumpCount) / NeighborPairCount > 0.005)
    {
        UE_LOG(
            LogRaftSimEditorEnvironment, Error,
            TEXT("Rejected discontinuous 16-bit height product: %s"),
            *AbsolutePath);
        OutImage = FSouthForkGray16Image();
        return false;
    }
    return true;
}
bool ParseCoordinateMap(
    const TSharedPtr<FJsonObject>& EnvironmentRoot,
    TArray<FSouthForkCoordinatePoint>& OutPoints,
    float& OutVerticalDatumM,
    FString& OutCoordinateMapPath)
{
    const TSharedPtr<FJsonObject>* CoordinateArtifact = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("coordinate_map"), CoordinateArtifact) ||
        CoordinateArtifact == nullptr ||
        !(*CoordinateArtifact)->TryGetStringField(TEXT("path"), OutCoordinateMapPath))
    {
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    if (!LoadJsonObject(OutCoordinateMapPath, Root))
    {
        return false;
    }
    FString Schema;
    double VerticalDatumM = 0.0;
    const TArray<TSharedPtr<FJsonValue>>* PointValues = nullptr;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.curved_river_coordinate_map.v1") ||
        !Root->TryGetNumberField(TEXT("vertical_datum_m"), VerticalDatumM) ||
        !Root->TryGetArrayField(TEXT("points"), PointValues) || PointValues == nullptr)
    {
        return false;
    }
    OutPoints.Reset(PointValues->Num());
    OutPoints.Reserve(PointValues->Num());
    for (const TSharedPtr<FJsonValue>& Value : *PointValues)
    {
        const TArray<TSharedPtr<FJsonValue>>* Point = nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Point) ||
            Point == nullptr || Point->Num() != 5)
        {
            return false;
        }
        FSouthForkCoordinatePoint Parsed;
        Parsed.StationM = (*Point)[0]->AsNumber();
        Parsed.CenterM = FVector2D((*Point)[1]->AsNumber(), (*Point)[2]->AsNumber());
        Parsed.LeftNormal = FVector2D(
            (*Point)[3]->AsNumber(), (*Point)[4]->AsNumber()).GetSafeNormal();
        OutPoints.Add(Parsed);
    }
    if (OutPoints.Num() < 2)
    {
        return false;
    }
    double WorldLengthM = 0.0;
    for (int32 Index = 1; Index < OutPoints.Num(); ++Index)
    {
        if (OutPoints[Index].StationM <= OutPoints[Index - 1].StationM)
        {
            return false;
        }
        const double CenterStepM = FVector2D::Distance(
            OutPoints[Index - 1].CenterM, OutPoints[Index].CenterM);
        WorldLengthM += CenterStepM;
        constexpr float CorridorHalfWidthM = 256.0f;
        const FVector2D PreviousLeft = OutPoints[Index - 1].CenterM +
            OutPoints[Index - 1].LeftNormal * CorridorHalfWidthM;
        const FVector2D CurrentLeft = OutPoints[Index].CenterM +
            OutPoints[Index].LeftNormal * CorridorHalfWidthM;
        const FVector2D PreviousRight = OutPoints[Index - 1].CenterM -
            OutPoints[Index - 1].LeftNormal * CorridorHalfWidthM;
        const FVector2D CurrentRight = OutPoints[Index].CenterM -
            OutPoints[Index].LeftNormal * CorridorHalfWidthM;
        const double CorridorEdgeStepM = FMath::Max(
            FVector2D::Distance(PreviousLeft, CurrentLeft),
            FVector2D::Distance(PreviousRight, CurrentRight));
        if (CorridorEdgeStepM > 16.0)
        {
            UE_LOG(
                LogRaftSimEditorEnvironment, Error,
                TEXT("Coordinate-map frame folds the terrain corridor at row %d: "
                     "edge step %.3f m for center step %.3f m."),
                Index, CorridorEdgeStepM, CenterStepM);
            return false;
        }
    }
    const double StationLengthM =
        OutPoints.Last().StationM - OutPoints[0].StationM;
    if (StationLengthM <= 0.0 ||
        FMath::Abs(WorldLengthM - StationLengthM) / StationLengthM > 0.005)
    {
        UE_LOG(
            LogRaftSimEditorEnvironment, Error,
            TEXT("Coordinate-map world length %.3f m does not match station length %.3f m."),
            WorldLengthM, StationLengthM);
        return false;
    }
    OutVerticalDatumM = static_cast<float>(VerticalDatumM);
    return true;
}

int32 ClosestCoordinateIndex(
    const TArray<FSouthForkCoordinatePoint>& Points, double StationM)
{
    int32 Low = 0;
    int32 High = Points.Num() - 1;
    while (Low + 1 < High)
    {
        const int32 Mid = Low + (High - Low) / 2;
        if (Points[Mid].StationM <= StationM)
        {
            Low = Mid;
        }
        else
        {
            High = Mid;
        }
    }
    return FMath::Abs(Points[Low].StationM - StationM) <=
            FMath::Abs(Points[High].StationM - StationM)
        ? Low
        : High;
}

FVector2D CoordinateWorldM(
    const FSouthForkCoordinatePoint& Point, float LateralM)
{
    return Point.CenterM + Point.LeftNormal * LateralM;
}

FVector CoordinateTangent(const TArray<FSouthForkCoordinatePoint>& Points, int32 Index)
{
    if (!Points.IsValidIndex(Index))
    {
        return FVector::ForwardVector;
    }
    // The terrain cross-sections use the conditioned frame stored in the
    // coordinate map. Camera and infrastructure orientation must use that
    // same frame; differentiating the unsmoothed NHD vertices can disagree by
    // more than 50 degrees at digitization corners and looks straight across
    // a bank ribbon instead of down the channel.
    const FVector2D Normal = Points[Index].LeftNormal.GetSafeNormal();
    const FVector2D Tangent(Normal.Y, -Normal.X);
    return FVector(Tangent.X, Tangent.Y, 0.0f);
}

float ComputeSouthForkSignedCurvaturePerM(
    const TArray<FSouthForkCoordinatePoint>& Points, int32 Index)
{
    // Signed heading change per meter (positive = turning river-left),
    // smoothed over ~±40 m so digitization corners don't spike the bend
    // superelevation term.
    const int32 Count = Points.Num();
    const int32 I0 = FMath::Clamp(Index - 10, 0, Count - 1);
    const int32 I1 = FMath::Clamp(Index + 10, 0, Count - 1);
    if (I1 <= I0 + 1)
    {
        return 0.0f;
    }
    const FVector T0 = CoordinateTangent(Points, I0);
    const FVector T1 = CoordinateTangent(Points, I1);
    const float DeltaHeadingRad = FMath::FindDeltaAngleRadians(
        FMath::Atan2(T0.Y, T0.X), FMath::Atan2(T1.Y, T1.X));
    const float DeltaStationM = static_cast<float>(
        Points[I1].StationM - Points[I0].StationM);
    if (DeltaStationM < 1.0f)
    {
        return 0.0f;
    }
    return DeltaHeadingRad / DeltaStationM;
}
void SetSpatiallyLoadedIfAllowed(AActor* Actor, bool bSpatiallyLoaded)
{
    if (Actor && Actor->CanChangeIsSpatiallyLoadedFlag())
    {
        Actor->SetIsSpatiallyLoaded(bSpatiallyLoaded);
    }
}
bool CreateTerminalVisualWater(
    UWorld* World, const TArray<FSouthForkCoordinatePoint>& Points, float WaterZCm,
    UMaterialInterface* Material, bool bReuseMesh,
    FSouthForkFullReachBuildMetrics& Metrics, FString& OutSummary)
{
    constexpr int32 Rows = 37, Columns = 11;
    constexpr float LengthM = 1800.0f;
    if (!World || Points.IsEmpty() || !FMath::IsFinite(WaterZCm)) return false;
    const FSouthForkCoordinatePoint& End = Points.Last();
    const FVector2D Normal = End.LeftNormal.GetSafeNormal();
    const FVector2D Tangent(Normal.Y, -Normal.X);
    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> Colors;
    Vertices.Reserve(Rows * Columns); UVs.Reserve(Rows * Columns);
    Colors.Reserve(Rows * Columns);
    for (int32 Row = 0; Row < Rows; ++Row)
    {
        const float DistanceM = LengthM * Row / (Rows - 1);
        const float Widen = FMath::SmoothStep(
            0.0f, 1.0f, FMath::Min(DistanceM / 520.0f, 1.0f));
        const float HalfWidthM = FMath::Lerp(40.0f, 92.0f, Widen);
        for (int32 Column = 0; Column < Columns; ++Column)
        {
            const float LateralM = FMath::Lerp(
                -HalfWidthM, HalfWidthM, static_cast<float>(Column) / (Columns - 1));
            Vertices.Add(FVector(
                (Tangent.X * DistanceM + Normal.X * LateralM) * 100.0f,
                (Tangent.Y * DistanceM + Normal.Y * LateralM) * 100.0f, WaterZCm));
            UVs.Add(FVector2D((End.StationM + DistanceM) / 3.0f, LateralM / 3.0f));
            Colors.Add(FLinearColor(0.0f, 0.52f, 0.035f, 1.0f));
        }
    }
    TArray<int32> Triangles;
    for (int32 Row = 0; Row < Rows - 1; ++Row)
        for (int32 Column = 0; Column < Columns - 1; ++Column)
        {
            const int32 I0 = Row * Columns + Column, I2 = I0 + Columns;
            Triangles.Append({I0, I0 + 1, I2, I0 + 1, I2 + 1, I2});
        }
    const FString AssetPath = TEXT(
        "/Game/RaftSim/Environment/SouthForkFullReach/Water/SM_SalmonFalls_VisualContinuation");
    UStaticMesh* Mesh = bReuseMesh ? LoadSouthForkStaticMeshAsset(AssetPath) : nullptr;
    if (!Mesh)
        Mesh = CreateSouthForkMeshAsset(
            World, AssetPath, TEXT("SalmonFalls_VisualContinuation"), Vertices,
            Triangles, ComputePreviewMeshNormals(Vertices, Triangles), UVs, Colors,
            BuildSouthForkFlowTangents(Vertices, Columns, Rows), Material, false, false, OutSummary);
    AStaticMeshActor* Actor = Mesh ? PlaceSouthForkStaticMeshActor(
        World, Mesh, Material, TEXT("RaftSim_SalmonFalls_VisualWaterContinuation"),
        FTransform(FVector(End.CenterM.X * 100.0f, End.CenterM.Y * 100.0f, 0.0f)),
        FName(TEXT("RaftSimFlowBand_median_runnable")), ECollisionEnabled::NoCollision) : nullptr;
    if (!Actor) return false;
    ConfigureSouthForkSingleLayerWaterActor(Actor);
    Actor->Tags.AddUnique(FName(TEXT("RaftSimVisualOnlyNotForNavigation")));
    Metrics.TerminalVisualWaterActorCount = 1;
    Metrics.TerminalVisualWaterTriangleCount = Triangles.Num() / 3;
    return true;
}

UHierarchicalInstancedStaticMeshComponent* AddHism(
    AActor* Owner,
    USceneComponent* Root,
    const FName Name,
    UStaticMesh* Mesh,
    UMaterialInterface* OverrideMaterial,
    int32 CullStartCm,
    int32 CullEndCm,
    ECollisionEnabled::Type Collision,
    bool bEnableDensityScaling,
    bool bCastShadow)
{
    if (!Owner || !Mesh)
    {
        return nullptr;
    }
    UHierarchicalInstancedStaticMeshComponent* Component =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(Owner, Name);
    Owner->AddInstanceComponent(Component);
    Component->SetupAttachment(Root);
    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(Collision);
    Component->SetCullDistances(CullStartCm, CullEndCm);
    Component->bEnableDensityScaling = bEnableDensityScaling;
    Component->SetCastShadow(bCastShadow);
    if (OverrideMaterial)
    {
        Component->SetMaterial(0, OverrideMaterial);
    }
    Component->RegisterComponent();
    return Component;
}

AActor* CreateInstancingActor(UWorld* World, const FString& Label, FName Tag)
{
    AActor* Actor = SpawnStableSouthForkActor<AActor>(
        World, FTransform::Identity, Label);
    if (!Actor)
    {
        return nullptr;
    }
    // Generated actors are deliberately stable across commandlet runs so their
    // World Partition packages and GUIDs do not churn. Rebuild their component
    // graph from scratch, however: Unreal preserves removed named subobjects in
    // an existing external-actor package unless the authoring pass explicitly
    // destroys them. Clearing here prevents retired scatter layers (and old
    // instance populations) from surviving a deterministic content rebuild.
    TInlineComponentArray<UActorComponent*> ExistingComponents(Actor);
    USceneComponent* ExistingRoot = Actor->GetRootComponent();
    for (UActorComponent* Component : ExistingComponents)
    {
        if (Component && Component != ExistingRoot)
        {
            Component->DestroyComponent();
        }
    }
    if (ExistingRoot)
    {
        Actor->SetRootComponent(nullptr);
        ExistingRoot->DestroyComponent();
    }
    Actor->SetActorLabel(Label);
    Actor->Tags.AddUnique(Tag);
    SetSpatiallyLoadedIfAllowed(Actor, true);
    USceneComponent* Root = NewObject<USceneComponent>(Actor, TEXT("Root"));
    Actor->AddInstanceComponent(Root);
    Root->SetMobility(EComponentMobility::Static);
    Root->RegisterComponent();
    Actor->SetRootComponent(Root);
    return Actor;
}

float StableUnitRandom(int32 A, int32 B, int32 C)
{
    uint32 Value = static_cast<uint32>(A) * 73856093u;
    Value ^= static_cast<uint32>(B) * 19349663u;
    Value ^= static_cast<uint32>(C) * 83492791u;
    Value ^= Value >> 13;
    Value *= 1274126177u;
    Value ^= Value >> 16;
    return static_cast<float>(Value & 0x00FFFFFFu) / 16777215.0f;
}

bool AddSouthForkBankMicroreliefPresentationPatches(
    UWorld* World,
    const FString& TileId,
    int32 GlobalRowStart,
    const FVector2D& TileOriginM,
    const TArray<FSouthForkCoordinatePoint>& CoordinatePoints,
    int32 Width,
    int32 Height,
    const TArray<FVector>& SourceVertices,
    const TArray<FVector2D>& SourceUvs,
    const TArray<FLinearColor>& SourceColors,
    const TArray<FVector>& SourceNormals,
    const FRaftSimPreviewImage& VfxImage,
    UMaterialInterface* TerrainMaterial,
    bool bReuseExistingMeshes,
    FSouthForkFullReachBuildMetrics& Metrics,
    FString& OutSummary)
{
    if (!World || !TerrainMaterial || Width < 2 || Height < 2 ||
        SourceVertices.Num() != Width * Height ||
        SourceUvs.Num() != SourceVertices.Num() ||
        SourceColors.Num() != SourceVertices.Num() ||
        SourceNormals.Num() != SourceVertices.Num() ||
        VfxImage.Pixels.Num() != SourceVertices.Num())
    {
        return false;
    }

    constexpr float ReviewStationsM[] = {
        120.0f, 944.0f, 5100.0f, 8328.0f, 48940.0f};
    constexpr float PatchHalfLengthM = 360.0f;
    constexpr int32 SubdivisionFactor = 2;
    constexpr int32 FirstSourceColumn = 36; // -112 m
    constexpr int32 LastSourceColumn = 92;  // +112 m
    static_assert(LastSourceColumn - FirstSourceColumn == 56);

    auto Bilinear = [](const auto& V00, const auto& V01,
                       const auto& V10, const auto& V11,
                       float ColumnAlpha, float RowAlpha)
    {
        return FMath::Lerp(
            FMath::Lerp(V00, V01, ColumnAlpha),
            FMath::Lerp(V10, V11, ColumnAlpha), RowAlpha);
    };

    for (int32 ReviewIndex = 0;
         ReviewIndex < UE_ARRAY_COUNT(ReviewStationsM);
         ++ReviewIndex)
    {
        const float ReviewStationM = ReviewStationsM[ReviewIndex];
        int32 FirstSourceRow = INDEX_NONE;
        int32 LastSourceRow = INDEX_NONE;
        for (int32 SourceRow = 0; SourceRow < Height; ++SourceRow)
        {
            const int32 CoordinateIndex = GlobalRowStart + SourceRow;
            if (!CoordinatePoints.IsValidIndex(CoordinateIndex) ||
                FMath::Abs(
                    static_cast<float>(CoordinatePoints[CoordinateIndex].StationM) -
                    ReviewStationM) > PatchHalfLengthM)
            {
                continue;
            }
            if (FirstSourceRow == INDEX_NONE)
            {
                FirstSourceRow = SourceRow;
            }
            LastSourceRow = SourceRow;
        }
        if (FirstSourceRow == INDEX_NONE ||
            LastSourceRow - FirstSourceRow < 2)
        {
            continue;
        }

        FirstSourceRow = FMath::Max(FirstSourceRow - 1, 0);
        LastSourceRow = FMath::Min(LastSourceRow + 1, Height - 1);
        const int32 PatchWidth =
            (LastSourceColumn - FirstSourceColumn) * SubdivisionFactor + 1;
        const int32 PatchHeight =
            (LastSourceRow - FirstSourceRow) * SubdivisionFactor + 1;
        const int32 PatchVertexCount = PatchWidth * PatchHeight;
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        TArray<uint8> Eligible;
        Vertices.SetNumUninitialized(PatchVertexCount);
        Uvs.SetNumUninitialized(PatchVertexCount);
        Colors.SetNumUninitialized(PatchVertexCount);
        Eligible.Init(0, PatchVertexCount);
        float PatchMaximumDisplacementCm = 0.0f;

        for (int32 PatchRow = 0; PatchRow < PatchHeight; ++PatchRow)
        {
            const float SourceRowCoordinate =
                FirstSourceRow +
                static_cast<float>(PatchRow) / SubdivisionFactor;
            const int32 SourceRow0 = FMath::Clamp(
                FMath::FloorToInt(SourceRowCoordinate), 0, Height - 1);
            const int32 SourceRow1 = FMath::Min(SourceRow0 + 1, Height - 1);
            const float RowAlpha = SourceRowCoordinate - SourceRow0;
            const int32 CoordinateIndex0 = FMath::Clamp(
                GlobalRowStart + SourceRow0, 0, CoordinatePoints.Num() - 1);
            const int32 CoordinateIndex1 = FMath::Clamp(
                GlobalRowStart + SourceRow1, 0, CoordinatePoints.Num() - 1);
            const float StationM = FMath::Lerp(
                static_cast<float>(CoordinatePoints[CoordinateIndex0].StationM),
                static_cast<float>(CoordinatePoints[CoordinateIndex1].StationM),
                RowAlpha);
            const float AlongEdgeDistanceM = FMath::Min(
                PatchRow * (4.0f / SubdivisionFactor),
                (PatchHeight - 1 - PatchRow) *
                    (4.0f / SubdivisionFactor));

            for (int32 PatchColumn = 0;
                 PatchColumn < PatchWidth;
                 ++PatchColumn)
            {
                const float SourceColumnCoordinate =
                    FirstSourceColumn +
                    static_cast<float>(PatchColumn) / SubdivisionFactor;
                const int32 SourceColumn0 = FMath::Clamp(
                    FMath::FloorToInt(SourceColumnCoordinate), 0, Width - 1);
                const int32 SourceColumn1 = FMath::Min(
                    SourceColumn0 + 1, Width - 1);
                const float ColumnAlpha =
                    SourceColumnCoordinate - SourceColumn0;
                const int32 I00 = SourceRow0 * Width + SourceColumn0;
                const int32 I01 = SourceRow0 * Width + SourceColumn1;
                const int32 I10 = SourceRow1 * Width + SourceColumn0;
                const int32 I11 = SourceRow1 * Width + SourceColumn1;
                const int32 Destination = PatchRow * PatchWidth + PatchColumn;
                FVector Position = Bilinear(
                    SourceVertices[I00], SourceVertices[I01],
                    SourceVertices[I10], SourceVertices[I11],
                    ColumnAlpha, RowAlpha);
                Uvs[Destination] = Bilinear(
                    SourceUvs[I00], SourceUvs[I01],
                    SourceUvs[I10], SourceUvs[I11],
                    ColumnAlpha, RowAlpha);
                Colors[Destination] = Bilinear(
                    SourceColors[I00], SourceColors[I01],
                    SourceColors[I10], SourceColors[I11],
                    ColumnAlpha, RowAlpha);
                const FVector SourceNormal = Bilinear(
                    SourceNormals[I00], SourceNormals[I01],
                    SourceNormals[I10], SourceNormals[I11],
                    ColumnAlpha, RowAlpha).GetSafeNormal(
                        UE_SMALL_NUMBER, FVector::UpVector);
                const FLinearColor Vfx = Bilinear(
                    VfxImage.Pixels[I00], VfxImage.Pixels[I01],
                    VfxImage.Pixels[I10], VfxImage.Pixels[I11],
                    ColumnAlpha, RowAlpha);
                const float LateralM =
                    -256.0f + 4.0f * SourceColumnCoordinate;
                const FVector2D WorldM(
                    Position.X / 100.0f + TileOriginM.X,
                    Position.Y / 100.0f + TileOriginM.Y);
                const float SourceSlope = FMath::Clamp(
                    1.0f - SourceNormal.Z, 0.0f, 1.0f);
                const float WetMask = FMath::Max(Vfx.R, Vfx.A);
                const FSouthForkBankMicroreliefSample Sample =
                    ComputeSouthForkBankMicroreliefSample(
                        WorldM.X, WorldM.Y, StationM, LateralM,
                        SourceSlope, WetMask, AlongEdgeDistanceM);
                if (Sample.bEligible)
                {
                    Position.Z += Sample.VerticalDisplacementCm;
                    Eligible[Destination] = 1;
                    PatchMaximumDisplacementCm = FMath::Max(
                        PatchMaximumDisplacementCm,
                        Sample.VerticalDisplacementCm);
                }
                Vertices[Destination] = Position;
            }
        }

        TArray<int32> Triangles;
        Triangles.Reserve((PatchWidth - 1) * (PatchHeight - 1) * 6);
        for (int32 Row = 0; Row < PatchHeight - 1; ++Row)
        {
            for (int32 Column = 0; Column < PatchWidth - 1; ++Column)
            {
                const int32 I0 = Row * PatchWidth + Column;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + PatchWidth;
                const int32 I3 = I2 + 1;
                if (Eligible[I0] == 0 || Eligible[I1] == 0 ||
                    Eligible[I2] == 0 || Eligible[I3] == 0)
                {
                    continue;
                }
                Triangles.Append({I0, I1, I2, I1, I3, I2});
            }
        }
        if (Triangles.Num() < 1500)
        {
            OutSummary += FString::Printf(
                TEXT("South Fork bank-microrelief patch at %.0f m emitted only %d triangles.\n"),
                ReviewStationM, Triangles.Num() / 3);
            return false;
        }

        const TArray<FVector> Normals =
            ComputePreviewMeshNormals(Vertices, Triangles);
        const TArray<FProcMeshTangent> Tangents =
            BuildSouthForkFlowTangents(Vertices, PatchWidth, PatchHeight);
        const FString AssetPath = FString::Printf(
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/Presentation/"
                 "SM_%s_BankMicroreliefV1_%05d"),
            *TileId, FMath::RoundToInt(ReviewStationM));
        UStaticMesh* Mesh = bReuseExistingMeshes
            ? LoadSouthForkStaticMeshAsset(AssetPath)
            : nullptr;
        if (!Mesh)
        {
            Mesh = CreateSouthForkMeshAsset(
                World, AssetPath,
                FString::Printf(
                    TEXT("%s_BankMicroreliefV1_%05d"),
                    *TileId, FMath::RoundToInt(ReviewStationM)),
                Vertices, Triangles, Normals, Uvs, Colors, Tangents,
                TerrainMaterial,
                /*bEnableNanite=*/true,
                /*bComplexCollision=*/false,
                OutSummary);
        }
        AStaticMeshActor* Actor = Mesh
            ? PlaceSouthForkStaticMeshActor(
                World, Mesh, TerrainMaterial,
                FString::Printf(
                    TEXT("RaftSim_SouthFork_%s_BankMicroreliefV1_%05d"),
                    *TileId,
                    FMath::RoundToInt(ReviewStationM)),
                FTransform(FVector(
                    TileOriginM.X * 100.0f,
                    TileOriginM.Y * 100.0f,
                    0.0f)),
                TEXT("RaftSimFullReachTerrainPresentationV1"),
                ECollisionEnabled::NoCollision)
            : nullptr;
        UStaticMeshComponent* Component = Actor
            ? Actor->GetStaticMeshComponent()
            : nullptr;
        if (!Component)
        {
            return false;
        }
        Component->SetCanEverAffectNavigation(false);
        // This is a visual derivative over the collision-authoritative DEM.
        // It contributes geometric normals, but casting onto the source mesh
        // would reveal the centimetre-scale separation as a dark shelf.
        Component->SetCastShadow(false);
        Actor->Tags.AddUnique(TEXT("RaftSimSouthForkDryBankMicroreliefV1"));
        ++Metrics.BankMicroreliefPatchCount;
        Metrics.BankMicroreliefVertexCount += Vertices.Num();
        Metrics.BankMicroreliefTriangleCount += Triangles.Num() / 3;
        Metrics.BankMicroreliefMaximumDisplacementCm = FMath::Max(
            Metrics.BankMicroreliefMaximumDisplacementCm,
            PatchMaximumDisplacementCm);
    }
    return true;
}

void AddSouthForkLighting(UWorld* World)
{
    ADirectionalLight* Sun = SpawnStableSouthForkActor<ADirectionalLight>(
        World,
        FTransform(FRotator(-42.0f, -128.0f, 0.0f)),
        TEXT("RaftSim_SouthFork_Sun"));
    if (Sun)
    {
        Sun->SetActorLabel(TEXT("RaftSim_SouthFork_Sun"));
        // Bright, clear Sierra summer daylight with enough direct energy to
        // retain terrain relief after the deterministic capture path disables
        // eye adaptation and Lumen. Keep this below the earlier blown-out
        // review bracket while lifting the retained V2 canopy out of silhouette.
        Sun->GetLightComponent()->SetIntensity(8.2f);
        Sun->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.97f, 0.91f));
        Sun->GetLightComponent()->SetCastShadows(true);
        if (UDirectionalLightComponent* SunComponent = Sun->GetComponent())
        {
            SunComponent->SetAtmosphereSunLight(true);
            SunComponent->SetAtmosphereSunLightIndex(0);
        }
        SetSpatiallyLoadedIfAllowed(Sun, false);
    }
    ASkyLight* Sky = SpawnStableSouthForkActor<ASkyLight>(
        World, FTransform::Identity, TEXT("RaftSim_SouthFork_SkyLight"));
    if (Sky)
    {
        Sky->SetActorLabel(TEXT("RaftSim_SouthFork_SkyLight"));
        // Open canyon sky contributes strong diffuse fill. This value is
        // intentionally lower than the direct sun, but high enough to keep
        // shaded riparian trunks and leaf masses readable from guide height.
        Sky->GetLightComponent()->SetIntensity(1.45f);
        Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
        Sky->GetLightComponent()->SetRealTimeCaptureEnabled(false);
        SetSpatiallyLoadedIfAllowed(Sky, false);
    }
    ASkyAtmosphere* Atmosphere = SpawnStableSouthForkActor<ASkyAtmosphere>(
        World, FTransform::Identity, TEXT("RaftSim_SouthFork_SkyAtmosphere"));
    if (Atmosphere)
    {
        Atmosphere->SetActorLabel(TEXT("RaftSim_SouthFork_SkyAtmosphere"));
        SetSpatiallyLoadedIfAllowed(Atmosphere, false);
    }
    AExponentialHeightFog* Fog = SpawnStableSouthForkActor<AExponentialHeightFog>(
        World, FTransform::Identity, TEXT("RaftSim_SouthFork_RiverMist"));
    if (Fog)
    {
        Fog->SetActorLabel(TEXT("RaftSim_SouthFork_RiverMist"));
        Fog->GetComponent()->SetFogDensity(0.006f);
        Fog->GetComponent()->SetFogHeightFalloff(0.18f);
        Fog->GetComponent()->SetVolumetricFog(true);
        SetSpatiallyLoadedIfAllowed(Fog, false);
    }
    // The default engine cloud volume requires temporal accumulation that is
    // unavailable in the deterministic commandlet capture path. Keep the
    // production South Fork condition as a plausible clear summer sky; an
    // explicit review flag can still enable cloud experiments without letting
    // their checker-pattern fallback enter release evidence.
    AVolumetricCloud* Clouds = FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimEnableSouthForkClouds"))
        ? SpawnStableSouthForkActor<AVolumetricCloud>(
            World, FTransform::Identity, TEXT("RaftSim_SouthFork_SeasonalClouds"))
        : nullptr;
    if (Clouds)
    {
        Clouds->SetActorLabel(TEXT("RaftSim_SouthFork_SeasonalClouds"));
        if (UVolumetricCloudComponent* Cloud =
                Clouds->FindComponentByClass<UVolumetricCloudComponent>())
        {
            // One-twelfth of the normal ray-march budget produced a visible
            // checker/stipple pattern in every release camera. Preserve a
            // bounded half-resolution volumetric budget, including reflection
            // and shadow paths, so the sky reads as cloud volume rather than
            // sparse screen-space particles.
            Cloud->SetViewSampleCountScale(0.5f);
            Cloud->SetReflectionViewSampleCountScale(0.5f);
            Cloud->SetShadowViewSampleCountScale(0.5f);
            Cloud->SetShadowReflectionViewSampleCountScale(0.5f);
        }
        SetSpatiallyLoadedIfAllowed(Clouds, false);
    }
    // Capture after atmosphere and clouds exist. The previous creation order
    // left the non-realtime skylight with an incomplete environment, flattening
    // terrain values and starving SingleLayerWater of coherent sky lighting.
    if (Sky && Sky->GetLightComponent())
    {
        Sky->GetLightComponent()->RecaptureSky();
    }
    APostProcessVolume* Post = SpawnStableSouthForkActor<APostProcessVolume>(
        World, FTransform::Identity, TEXT("RaftSim_SouthFork_LumenColorGrade"));
    if (Post)
    {
        Post->SetActorLabel(TEXT("RaftSim_SouthFork_LumenColorGrade"));
        Post->bUnbound = true;
        Post->Settings.bOverride_AutoExposureBias = true;
        Post->Settings.AutoExposureBias = 0.30f;
        Post->Settings.bOverride_BloomIntensity = true;
        Post->Settings.BloomIntensity = 0.24f;
        Post->Settings.bOverride_LumenReflectionQuality = true;
        Post->Settings.LumenReflectionQuality = 2.0f;
        Post->Settings.bOverride_LumenFinalGatherQuality = true;
        Post->Settings.LumenFinalGatherQuality = 2.0f;
        SetSpatiallyLoadedIfAllowed(Post, false);
    }
}

bool SaveFullReachWorld(UWorld* World)
{
    const FString Filename = FPackageName::LongPackageNameToFilename(
        FullReachMapPackagePath, FPackageName::GetMapPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    return FEditorFileUtils::SaveMap(World, Filename);
}

bool ValidateStableSouthForkActorIdentities(
    UWorld* World, FSouthForkFullReachBuildMetrics& Metrics, FString& OutSummary)
{
    if (!World)
    {
        return false;
    }

    TSet<FGuid> AssignedGuids;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || Actor->IsActorBeingDestroyed())
        {
            continue;
        }
        const FString Label = Actor->GetActorLabel();
        if (!Label.StartsWith(TEXT("RaftSim_")))
        {
            continue;
        }
        const FGuid StableGuid = SouthForkActorGuid(Actor->GetClass(), Label);
        const FName StableObjectName = SouthForkActorObjectName(Actor->GetClass(), Label);
        if (!StableGuid.IsValid() || AssignedGuids.Contains(StableGuid) ||
            Actor->GetActorGuid() != StableGuid || Actor->GetFName() != StableObjectName)
        {
            OutSummary += FString::Printf(
                TEXT("Missing, duplicate, or unstable deterministic actor identity for %s.\n"),
                *Label);
            return false;
        }
        AssignedGuids.Add(StableGuid);
    }
    Metrics.StableActorIdentityCount = AssignedGuids.Num();
    OutSummary += FString::Printf(
        TEXT("Validated %d deterministic World Partition actor identities.\n"),
        Metrics.StableActorIdentityCount);
    return Metrics.StableActorIdentityCount > 0;
}

UHLODLayer* ConfigureSouthForkInstancedHlodLayer(FString& OutSummary)
{
    const FString AssetName = FPackageName::GetLongPackageAssetName(
        FullReachInstancedHlodLayerPackagePath);
    UHLODLayer* Layer = LoadObject<UHLODLayer>(
        nullptr,
        *FString::Printf(
            TEXT("%s.%s"),
            FullReachInstancedHlodLayerPackagePath,
            *AssetName));
    if (!Layer)
    {
        OutSummary += TEXT(
            "The South Fork instanced HLOD layer asset is unavailable.\n");
        return nullptr;
    }
    Layer->Modify();
    Layer->SetLayerType(EHLODLayerType::Instancing);
    // A merged parent bakes an 8K material atlas for each large cell because
    // this map intentionally uses vertex colour and world-aligned materials.
    // Nanite already handles terrain reduction; an instanced terminal layer
    // provides the required streaming HLOD without destructive rebaking or a
    // multi-hour hierarchy build.
    Layer->SetParentLayer(nullptr);
    Layer->PostEditChange();
    UPackage* Package = Layer->GetOutermost();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Package->GetName(), FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Layer, *Filename, SaveArgs))
    {
        OutSummary += TEXT("Failed to save the bounded South Fork HLOD layer.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Configured the South Fork terminal instanced HLOD layer with no merged-atlas parent.\n");
    return Layer;
}
} // namespace RaftSimEditorEnvironment::SouthForkFullReach
