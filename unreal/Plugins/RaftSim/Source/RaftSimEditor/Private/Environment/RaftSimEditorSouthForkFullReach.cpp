#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SphereReflectionCapture.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RenderingThread.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "StaticMeshResources.h"
#include "UObject/SavePackage.h"
#include "WorldPartition/HLOD/HLODLayer.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/WorldPartitionMiniMap.h"
#include "WorldPartition/WorldPartitionRuntimeHash.h"
namespace RaftSimEditorEnvironment { namespace {
constexpr TCHAR EnvironmentManifestRelativePath[] = TEXT(
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
         "photoreal_environment/manifest.json");
constexpr TCHAR FullReachMapPackagePath[] = TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
constexpr TCHAR FullReachInstancedHlodLayerPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach_HLODLayer_Instanced");
constexpr TCHAR CaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach");
constexpr float DetailedTerrainHalfWidthM = 112.0f;
constexpr float DetailedPineAnalogRiverDistanceM = 1100.0f;
void SetSpatiallyLoadedIfAllowed(AActor* Actor, bool bSpatiallyLoaded);
struct FSouthForkCoordinatePoint
{
    double StationM = 0.0;
    FVector2D CenterM = FVector2D::ZeroVector;
    FVector2D LeftNormal = FVector2D::UnitY();
};
struct FSouthForkGray16Image
{
    int32 Width = 0;
    int32 Height = 0;
    TArray<uint16> Values;
};
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
template <typename T>
T* SpawnStableSouthForkActor(
    UWorld* World, const FTransform& Transform, const FString& Label)
{
    if (!World)
    {
        return nullptr;
    }
    FActorSpawnParameters SpawnParameters;
    SpawnParameters.InitialActorLabel = Label;
    SpawnParameters.OverrideActorGuid = SouthForkActorGuid(T::StaticClass(), Label);
    // External actor package paths are derived from the actor object path, not
    // from ActorGuid. Give every generated actor a cross-process-stable object
    // name as well as a stable GUID so repeated builds reuse the same packages.
    SpawnParameters.Name = SouthForkActorObjectName(T::StaticClass(), Label);
    return World->SpawnActor<T>(T::StaticClass(), Transform, SpawnParameters);
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
    bool bEnableDensityScaling = false,
    bool bCastShadow = true)
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
} // namespace

bool BuildSouthForkFullReachEnvironment(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;
    TSharedPtr<FJsonObject> EnvironmentRoot;
    if (!LoadJsonObject(EnvironmentManifestRelativePath, EnvironmentRoot))
    {
        OutSummary += TEXT("Could not load the M4 South Fork environment manifest.\n");
        return false;
    }
    FString EnvironmentSchema;
    if (!EnvironmentRoot->TryGetStringField(TEXT("schema"), EnvironmentSchema) ||
        EnvironmentSchema != TEXT("raftsim.south_fork.photoreal_environment.v1"))
    {
        OutSummary += TEXT("The South Fork environment schema is unsupported.\n");
        return false;
    }

    TArray<FSouthForkCoordinatePoint> CoordinatePoints;
    float VerticalDatumM = 0.0f;
    FString CoordinateMapPath;
    if (!ParseCoordinateMap(
            EnvironmentRoot, CoordinatePoints, VerticalDatumM, CoordinateMapPath))
    {
        OutSummary += TEXT("Could not parse the full-reach curved coordinate map.\n");
        return false;
    }
    const bool bReuseExistingDetailedMeshes = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkFullReachMeshes"));
    const bool bReuseExistingDetailedTerrainMeshes = bReuseExistingDetailedMeshes ||
        FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimReuseSouthForkDetailedTerrainMeshes"));
    const bool bReuseExistingWaterMeshes = bReuseExistingDetailedMeshes || FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkWaterMeshes"));
    const bool bRebuildFarFieldMeshes = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimRebuildSouthForkFarFieldMeshes"));
    const bool bReuseExistingFarFieldMeshes = !bRebuildFarFieldMeshes &&
        (bReuseExistingDetailedMeshes || FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimReuseSouthForkFarFieldMeshes")));
    const bool bRebuildFarFieldMacroTextures = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimRebuildSouthForkFarFieldMacroTextures"));
    const bool bReuseExistingMaterials = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkMaterials"));
    if (bReuseExistingDetailedMeshes)
    {
        OutSummary += TEXT(
            "Reusing existing hash-validated detailed South Fork terrain and water meshes.\n");
    }
    if (bRebuildFarFieldMacroTextures)
    {
        OutSummary += TEXT(
            "Rebuilding South Fork far-field macro textures while reusing geometry.\n");
    }
    if (bRebuildFarFieldMeshes)
    {
        OutSummary += TEXT(
            "Rebuilding South Fork far-field horizon geometry while reusing detailed terrain and water.\n");
    }

    const TSharedPtr<FJsonObject>* UnrealImport = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* TileValues = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("unreal_import"), UnrealImport) ||
        UnrealImport == nullptr ||
        !(*UnrealImport)->TryGetArrayField(TEXT("tiles"), TileValues) ||
        TileValues == nullptr || TileValues->Num() != 13)
    {
        OutSummary += TEXT("The full-reach manifest does not contain thirteen Unreal tiles.\n");
        return false;
    }

    if (bReuseExistingMaterials)
    {
        OutSummary += TEXT(
            "Reusing existing validated South Fork materials without regeneration.\n");
    }
    else
    {
        IConsoleManager::Get().ProcessUserConsoleInput(
            TEXT("RaftSim.CreatePhotorealMaterials"), *GLog, nullptr);
    }
    UMaterialInterface* TerrainMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    UMaterialInterface* WaterMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
             "M_RaftSim_PhotorealRiverWater"));
    if (!TerrainMaterial || !WaterMaterial || !LoadSouthForkProductionWaterPresentation(WaterMaterial, OutSummary))
    {
        OutSummary += TEXT("Photoreal terrain or water material is unavailable.\n");
        return false;
    }
    // This is generated source-of-truth, not a hand-authored material. Rebuild
    // it on non-reuse passes so an older candidate asset cannot silently keep
    // a stale blend mode or disconnected vertex-alpha opacity graph.
    UMaterialInterface* WhitewaterFoamMaterial = bReuseExistingMaterials
        ? LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
                 "M_RaftSim_SolverFieldFoamCandidate."
                 "M_RaftSim_SolverFieldFoamCandidate"))
        : LoadOrCreateLandscapeCandidateSolverFoamMaterial(OutSummary);
    if (!WhitewaterFoamMaterial)
    {
        WhitewaterFoamMaterial =
            LoadOrCreateLandscapeCandidateSolverFoamMaterial(OutSummary);
    }
    if (!WhitewaterFoamMaterial)
    {
        OutSummary += TEXT(
            "The solver-masked whitewater overlay material is unavailable.\n");
        return false;
    }

    UWorld* World = GEditor ? GEditor->NewMap(/*bIsPartitionedWorld=*/true) : nullptr;
    if (!World || !World->GetWorldPartition())
    {
        OutSummary += TEXT("Failed to create a World Partition map.\n");
        return false;
    }
    if (!ReplaceWorldPartitionMiniMapWithStableActor(World, OutSummary))
    {
        return false;
    }

    // Establish the destination map package before assigning the project HLOD
    // layer. SaveMap duplicates a partitioned world's default HLOD setup when
    // it renames a transient map. Assigning the layer first therefore produces
    // a map-prefixed duplicate whose path is not registered with the runtime
    // hash partition policy, and the commandlet silently rejects every actor as
    // having an invalid layer. The empty bootstrap save prevents that Save-As
    // duplication; the populated save below is then an ordinary in-place save.
    World->GetWorldPartition()->SetDefaultHLODLayer(nullptr);
    if (!SaveFullReachWorld(World))
    {
        OutSummary += TEXT("Failed to establish the full-reach map package.\n");
        return false;
    }
    UHLODLayer* InstancedHlodLayer = ConfigureSouthForkInstancedHlodLayer(OutSummary);
    if (!InstancedHlodLayer)
    {
        return false;
    }
    UWorldPartition* WorldPartition = World->GetWorldPartition();
    WorldPartition->SetDefaultHLODLayer(InstancedHlodLayer);

    // Runtime Hash Set snapshots its valid HLOD partitions when it is created.
    // This new map was bootstrapped with no HLOD layer to avoid Save-As asset
    // duplication, so replace the still-empty hash now and let it initialize
    // against the terminal project layer. Without this, explicit layer
    // validation removes HLOD eligibility from every spatial actor.
    UWorldPartitionRuntimeHash* PreviousRuntimeHash = WorldPartition->RuntimeHash;
    if (!PreviousRuntimeHash)
    {
        OutSummary += TEXT("The full-reach World Partition runtime hash is unavailable.\n");
        return false;
    }
    WorldPartition->RuntimeHash = NewObject<UWorldPartitionRuntimeHash>(
        WorldPartition,
        PreviousRuntimeHash->GetClass(),
        NAME_None,
        RF_Transactional);
    if (!WorldPartition->RuntimeHash)
    {
        OutSummary += TEXT("Failed to rebuild the full-reach runtime hash for HLOD.\n");
        return false;
    }
    WorldPartition->RuntimeHash->SetDefaultValues();
    OutSummary += TEXT(
        "Rebuilt the empty runtime hash against the terminal South Fork HLOD layer.\n");
    World->GetWorldSettings()->DefaultGameMode = LoadClass<AGameModeBase>(
        nullptr, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    AddSouthForkLighting(World);

    FSouthForkFullReachBuildMetrics Metrics;
    Metrics.MedianCenterWaterLocalZCm.Init(-BIG_NUMBER, CoordinatePoints.Num());

    // Detailed foliage reaches the fold-safe +/-112 m ribbon. Keep the
    // far-field dressing outside the water while retaining a slight overlap.
    // Every far-field patch carries the generator's exact route-distance
    // raster, including its non-navigational endpoint continuation.
    constexpr float FarFieldRiverExclusionM = 106.0f;
    UStaticMesh* PineMeshes[3] = {};
    UStaticMesh* GeneratedInteriorLiveOakMesh = nullptr;
    UStaticMesh* GeneratedWhiteAlderMesh = nullptr;
    UStaticMesh* GeneratedDeerbrushMesh = nullptr;
    const bool bGeneratedCanopyReady = CreateSouthForkGeneratedCanopyAssets(
        World, PineMeshes[0], PineMeshes[1], PineMeshes[2],
        GeneratedInteriorLiveOakMesh, GeneratedWhiteAlderMesh,
        GeneratedDeerbrushMesh, OutSummary);
    if (!bGeneratedCanopyReady)
    {
        OutSummary += TEXT(
            "Generated canopy authoring failed; refusing to promote a rejected review asset as a visible fallback.\n");
        return false;
    }
    UStaticMesh* DetailedPineMeshes[3] = {
        LoadObject<UStaticMesh>(nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
                 "SM_PineTree01_pine_tree_01_a_LOD0."
                 "SM_PineTree01_pine_tree_01_a_LOD0")),
        LoadObject<UStaticMesh>(nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
                 "SM_PineTree01_pine_tree_01_b_LOD0."
                 "SM_PineTree01_pine_tree_01_b_LOD0")),
        LoadObject<UStaticMesh>(nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
                 "SM_PineTree01_pine_tree_01_c_LOD0."
                 "SM_PineTree01_pine_tree_01_c_LOD0"))};
    const bool bDetailedPineAnalogReady = DetailedPineMeshes[0] &&
        DetailedPineMeshes[1] && DetailedPineMeshes[2];
    if (!bDetailedPineAnalogReady)
    {
        DetailedPineMeshes[0] = PineMeshes[0];
        DetailedPineMeshes[1] = PineMeshes[1];
        DetailedPineMeshes[2] = PineMeshes[2];
    }
    OutSummary += bDetailedPineAnalogReady
        ? TEXT("Using rights-reviewed three-variant 3D pine analogs in the detailed corridor; ecology and guide promotion remain pending.\n")
        : TEXT("Detailed 3D pine analog unavailable; retained project-owned Ponderosa cards.\n");
    // Project-owned Ponderosa cards remain the far-field representation; the
    // registered aerial macro already carries most distant canopy detail.
    UStaticMesh* BroadleafMesh = GeneratedInteriorLiveOakMesh;
    UStaticMesh* RiparianMesh = GeneratedWhiteAlderMesh;
    UStaticMesh* FarBroadleafMesh = GeneratedInteriorLiveOakMesh
        ? GeneratedInteriorLiveOakMesh
        : BroadleafMesh;
    UStaticMesh* ShrubMesh = GeneratedDeerbrushMesh;
    constexpr int32 ScannedGroundCoverVariantCount = 8;
    constexpr int32 ScannedGroundCoverComponentCount =
        ScannedGroundCoverVariantCount * 2;
    UStaticMesh* ScannedGroundCoverMeshes[ScannedGroundCoverVariantCount] = {
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_dead_a."
                 "SM_GrassBermuda01_grass_bermuda_01_dead_a")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_dead_b."
                 "SM_GrassBermuda01_grass_bermuda_01_dead_b")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_flattened_a."
                 "SM_GrassBermuda01_grass_bermuda_01_flattened_a")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_medium_a."
                 "SM_GrassBermuda01_grass_bermuda_01_medium_a")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_medium_c."
                 "SM_GrassBermuda01_grass_bermuda_01_medium_c")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_medium_d."
                 "SM_GrassBermuda01_grass_bermuda_01_medium_d")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_medium_f."
                 "SM_GrassBermuda01_grass_bermuda_01_medium_f")),
        LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/"
                 "SM_GrassBermuda01_grass_bermuda_01_small_c."
                 "SM_GrassBermuda01_grass_bermuda_01_small_c"))};
    for (UStaticMesh* ScannedGroundCoverMesh : ScannedGroundCoverMeshes)
    {
        if (!ScannedGroundCoverMesh)
        {
            OutSummary += TEXT(
                "Rights-reviewed CC0 scanned ground-cover family is incomplete; refusing a procedural fallback.\n");
            return false;
        }
    }
    OutSummary += TEXT(
        "Using eight rights-reviewed CC0 scanned grass forms for source-conditioned ground-cover morphology; species and ecology authority remain with project data.\n");
    UStaticMesh* ProductionRockMesh = nullptr;
    UMaterialInterface* ProductionRockMaterial = nullptr;
    if (!LoadSouthForkProductionRockPresentation(
            ProductionRockMesh, ProductionRockMaterial, OutSummary))
    {
        return false;
    }
    UStaticMesh* RockMeshes[6] = {ProductionRockMesh, ProductionRockMesh, ProductionRockMesh,
        ProductionRockMesh, ProductionRockMesh, ProductionRockMesh};
    UMaterialInterface* ReviewedRockMaterial = ProductionRockMaterial;
    UStaticMesh* ShoreCobbleMeshes[3] = {};
    if (!CreateSouthForkShoreCobbleAssets(World, ReviewedRockMaterial,
            bReuseExistingDetailedMeshes, ShoreCobbleMeshes, OutSummary)) return false;
    UStaticMesh* GroundCoverMesh = nullptr;
    UMaterialInterface* GroundCoverMaterial = nullptr;
    if (!CreateSouthForkGroundCoverAssets(
            World, /*bReuseExistingAssets=*/true,
            GroundCoverMesh, GroundCoverMaterial, OutSummary))
    {
        return false;
    }
    UStaticMesh* SprayMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UMaterialInterface* SprayMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist."
             "M_RaftSim_SprayMist"));
    TSharedPtr<FJsonObject> BoulderRoot;
    TArray<TSharedPtr<FJsonValue>> EmptyBoulders;
    const TArray<TSharedPtr<FJsonValue>>* BoulderValues = &EmptyBoulders;
    const TSharedPtr<FJsonObject>* BoulderArtifact = nullptr;
    FString BoulderPath;
    if (EnvironmentRoot->TryGetObjectField(TEXT("boulder_catalog"), BoulderArtifact) &&
        BoulderArtifact != nullptr &&
        (*BoulderArtifact)->TryGetStringField(TEXT("path"), BoulderPath) &&
        LoadJsonObject(BoulderPath, BoulderRoot))
    {
        BoulderRoot->TryGetArrayField(TEXT("boulders"), BoulderValues);
    }
    TArray<FSouthForkBoulderPresentationFootprint> AcceptedBoulderPresentationFootprints;
    for (int32 TileOrdinal = 0; TileOrdinal < TileValues->Num(); ++TileOrdinal)
    {
        const TSharedPtr<FJsonObject>* Tile = nullptr;
        if (!(*TileValues)[TileOrdinal]->TryGetObject(Tile) || Tile == nullptr)
        {
            return false;
        }
        FString TileId;
        const TArray<TSharedPtr<FJsonValue>>* RowRange = nullptr;
        const TSharedPtr<FJsonObject>* TerrainArtifact = nullptr;
        const TSharedPtr<FJsonObject>* TerrainEncoding = nullptr;
        const TSharedPtr<FJsonObject>* MacroArtifact = nullptr;
        const TSharedPtr<FJsonObject>* VfxArtifact = nullptr;
        if (!(*Tile)->TryGetStringField(TEXT("tile_id"), TileId) ||
            !(*Tile)->TryGetArrayField(TEXT("row_range"), RowRange) ||
            RowRange == nullptr || RowRange->Num() != 2 ||
            !(*Tile)->TryGetObjectField(TEXT("terrain_height"), TerrainArtifact) ||
            !(*Tile)->TryGetObjectField(TEXT("terrain_height_encoding"), TerrainEncoding) ||
            !(*Tile)->TryGetObjectField(TEXT("macro_albedo"), MacroArtifact) ||
            !(*Tile)->TryGetObjectField(TEXT("water_vfx_zones"), VfxArtifact))
        {
            return false;
        }
        const int32 GlobalRowStart = static_cast<int32>((*RowRange)[0]->AsNumber());
        FString TerrainPath;
        FString MacroPath;
        FString VfxPath;
        (*TerrainArtifact)->TryGetStringField(TEXT("path"), TerrainPath);
        (*MacroArtifact)->TryGetStringField(TEXT("path"), MacroPath);
        (*VfxArtifact)->TryGetStringField(TEXT("path"), VfxPath);
        double TerrainMinimumM = 0.0;
        double TerrainMaximumM = 0.0;
        (*TerrainEncoding)->TryGetNumberField(TEXT("minimum_elevation_m"), TerrainMinimumM);
        (*TerrainEncoding)->TryGetNumberField(TEXT("maximum_elevation_m"), TerrainMaximumM);
        FSouthForkGray16Image TerrainHeight;
        FRaftSimPreviewImage MacroImage;
        FRaftSimPreviewImage VfxImage;
        if (!LoadGray16Png(TerrainPath, TerrainHeight) ||
            !LoadPreviewPngImage(MacroPath, MacroImage) ||
            !LoadPreviewPngImage(VfxPath, VfxImage) ||
            TerrainHeight.Width != MacroImage.Width ||
            TerrainHeight.Height != MacroImage.Height ||
            VfxImage.Width != TerrainHeight.Width ||
            VfxImage.Height != TerrainHeight.Height)
        {
            OutSummary += FString::Printf(TEXT("Failed to decode tile %s.\n"), *TileId);
            return false;
        }
        UTexture2D* TileMacroTexture = bReuseExistingDetailedTerrainMeshes
            ? LoadSouthForkTerrainMacroTextureForReuse(TileId, OutSummary)
            : CreateSouthForkTerrainMacroTexture(TileId, MacroPath, OutSummary);
        UMaterialInstanceConstant* TileTerrainMaterial =
            CreateSouthForkTerrainMaterialInstance(
                TileId, TerrainMaterial, TileMacroTexture,
                /*bUseCorridorEdgeBlend=*/true, OutSummary);
        if (!TileMacroTexture || !TileTerrainMaterial)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create textured Nanite terrain material for %s.\n"),
                *TileId);
            return false;
        }
        const int32 Width = TerrainHeight.Width;
        const int32 Height = TerrainHeight.Height;
        const int32 CenterCoordinateIndex = FMath::Clamp(
            GlobalRowStart + Height / 2, 0, CoordinatePoints.Num() - 1);
        const FVector2D TileOriginM = CoordinatePoints[CenterCoordinateIndex].CenterM;

        TArray<FVector> TerrainVertices;
        TArray<FVector2D> TerrainUvs;
        TArray<FLinearColor> TerrainColors;
        TerrainVertices.SetNum(Width * Height);
        TerrainUvs.SetNum(Width * Height);
        TerrainColors.SetNum(Width * Height);
        for (int32 Row = 0; Row < Height; ++Row)
        {
            const int32 CoordinateIndex = FMath::Clamp(
                GlobalRowStart + Row, 0, CoordinatePoints.Num() - 1);
            const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
            for (int32 Column = 0; Column < Width; ++Column)
            {
                const int32 Index = Row * Width + Column;
                const float LateralM = -256.0f + 4.0f * Column;
                const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                const float ElevationM = DecodeSouthForkHeightM(
                    TerrainHeight.Values[Index], TerrainMinimumM, TerrainMaximumM);
                TerrainVertices[Index] = FVector(
                    (WorldM.X - TileOriginM.X) * 100.0f,
                    (WorldM.Y - TileOriginM.Y) * 100.0f,
                    (ElevationM - VerticalDatumM) * 100.0f);
                TerrainUvs[Index] = FVector2D(
                    static_cast<float>(Column) / FMath::Max(Width - 1, 1),
                    static_cast<float>(Row) / FMath::Max(Height - 1, 1));
                TerrainColors[Index] = DecodeSouthForkPreviewSrgbColor(MacroImage.Pixels[Index]);
                TerrainColors[Index].A = VfxImage.Pixels[Index].R;
            }
        }
        TArray<int32> TerrainTriangles;
        TerrainTriangles.Reserve((Width - 1) * (Height - 1) * 6);
        for (int32 Row = 0; Row < Height - 1; ++Row)
        {
            for (int32 Column = 0; Column < Width - 1; ++Column)
            {
                const float CellCenterLateralM = -256.0f + (Column + 0.5f) * 4.0f;
                if (FMath::Abs(CellCenterLateralM) > DetailedTerrainHalfWidthM)
                {
                    continue;
                }
                const int32 I0 = Row * Width + Column;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + Width;
                const int32 I3 = I2 + 1;
                TerrainTriangles.Append({I0, I1, I2, I1, I3, I2});
            }
        }
        // A four-metre DEM grid needs a wider presentation derivative than a
        // triangle face normal. Preserve the source elevations and collision,
        // but remove visible diagonal facets from lighting and material blend.
        TArray<FVector> TerrainNormals =
            BuildSouthForkSmoothedTerrainPresentationNormals(
                TerrainVertices, Width, Height, /*Radius=*/2);
        if (TerrainNormals.Num() != TerrainVertices.Num())
        {
            TerrainNormals = ComputePreviewMeshNormals(
                TerrainVertices, TerrainTriangles);
        }
        const TArray<FProcMeshTangent> TerrainTangents =
            BuildSouthForkFlowTangents(TerrainVertices, Width, Height);
        const FString TerrainAssetPath = FString::Printf(TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/SM_%s_Terrain"), *TileId);
        UStaticMesh* TerrainMesh = bReuseExistingDetailedTerrainMeshes
            ? LoadSouthForkStaticMeshAsset(TerrainAssetPath)
            : nullptr;
        if (!TerrainMesh)
        {
            TerrainMesh = CreateSouthForkMeshAsset(
                World, TerrainAssetPath, TileId + TEXT("_Terrain"),
                TerrainVertices, TerrainTriangles, TerrainNormals,
                TerrainUvs, TerrainColors, TerrainTangents,
                TileTerrainMaterial,
                /*bEnableNanite=*/true,
                /*bComplexCollision=*/true, OutSummary);
        }
        if (!TerrainMesh || !PlaceSouthForkStaticMeshActor(
                World, TerrainMesh, TileTerrainMaterial,
                TEXT("RaftSim_SouthFork_Terrain_") + TileId,
                FTransform(FVector(
                    TileOriginM.X * 100.0f,
                    TileOriginM.Y * 100.0f,
                    0.0f)),
                TEXT("RaftSimFullReachTerrain"),
                ECollisionEnabled::QueryAndPhysics))
        {
            return false;
        }
        if (TileOrdinal == 0)
        {
            LogStaticMeshVertexColorSummary(TEXT("detailed_terrain_00"), TerrainMesh);
        }
        ++Metrics.TerrainTileCount;
        Metrics.TerrainTriangleCount += TerrainTriangles.Num() / 3;
        if (!AddSouthForkBankMicroreliefPresentationPatches(
                World, TileId, GlobalRowStart, TileOriginM,
                CoordinatePoints, Width, Height,
                TerrainVertices, TerrainUvs, TerrainColors, TerrainNormals,
                VfxImage, TileTerrainMaterial,
                bReuseExistingDetailedTerrainMeshes,
                Metrics, OutSummary))
        {
            OutSummary += FString::Printf(
                TEXT("Failed to add dry-bank microrelief presentation for %s.\n"),
                *TileId);
            return false;
        }
        // Source-masked CC0/project-owned ecology, boulders, and aeration are
        // stored per tile as HISM clusters so World Partition can stream them.
        AActor* DressingActor = CreateInstancingActor(
            World, TEXT("RaftSim_SouthFork_Dressing_") + TileId,
            TEXT("RaftSimFullReachDressing"));
        USceneComponent* DressingRoot = DressingActor ? DressingActor->GetRootComponent() : nullptr;
        UHierarchicalInstancedStaticMeshComponent* Conifers[3] = {
            AddHism(DressingActor, DressingRoot, TEXT("ConiferA"), DetailedPineMeshes[0], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics),
            AddHism(DressingActor, DressingRoot, TEXT("ConiferB"), DetailedPineMeshes[1], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics),
            AddHism(DressingActor, DressingRoot, TEXT("ConiferC"), DetailedPineMeshes[2], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics)};
        UHierarchicalInstancedStaticMeshComponent* Broadleaf = AddHism(
            DressingActor, DressingRoot, TEXT("OakBroadleafProxy"), BroadleafMesh, nullptr,
            220000, 550000, ECollisionEnabled::QueryAndPhysics);
        UHierarchicalInstancedStaticMeshComponent* Riparian = AddHism(
            DressingActor, DressingRoot, TEXT("WhiteAlderRiparian"), RiparianMesh, nullptr,
            160000, 420000, ECollisionEnabled::QueryAndPhysics,
            /*bEnableDensityScaling=*/false, /*bCastShadow=*/true);
        UHierarchicalInstancedStaticMeshComponent* Understory = AddHism(
            DressingActor, DressingRoot, TEXT("Understory"), ShrubMesh, nullptr,
            90000, 250000, ECollisionEnabled::NoCollision);
        UHierarchicalInstancedStaticMeshComponent* GroundCover = AddHism(
            DressingActor, DressingRoot, TEXT("DryGrassGroundCover"),
            GroundCoverMesh, GroundCoverMaterial,
            /*CullStartCm=*/0, /*CullEndCm=*/140000,
            ECollisionEnabled::NoCollision,
            /*bEnableDensityScaling=*/false, /*bCastShadow=*/false);
        UHierarchicalInstancedStaticMeshComponent*
            ScannedGroundCoverComponents[ScannedGroundCoverComponentCount] = {};
        for (int32 VariantIndex = 0;
             VariantIndex < ScannedGroundCoverComponentCount; ++VariantIndex)
        {
            const bool bSatellite =
                VariantIndex >= ScannedGroundCoverVariantCount;
            const int32 MeshVariantIndex =
                VariantIndex % ScannedGroundCoverVariantCount;
            const FString ComponentName = bSatellite
                ? FString::Printf(
                    TEXT("Cc0ScannedGroundCoverSatellite%02d"),
                    MeshVariantIndex + 1)
                : FString::Printf(
                    TEXT("Cc0ScannedGroundCoverPrimary%02d"),
                    MeshVariantIndex + 1);
            ScannedGroundCoverComponents[VariantIndex] = AddHism(
                DressingActor, DressingRoot, *ComponentName,
                ScannedGroundCoverMeshes[MeshVariantIndex], nullptr,
                /*CullStartCm=*/0, /*CullEndCm=*/140000,
                ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/false, /*bCastShadow=*/false);
        }
        UHierarchicalInstancedStaticMeshComponent* Spray = AddHism(
            DressingActor, DressingRoot, TEXT("SolverAuthoredSprayMist"),
            SprayMesh, SprayMaterial, 90000, 260000,
            ECollisionEnabled::NoCollision);
        UHierarchicalInstancedStaticMeshComponent* RockComponents[6] = {};
        UHierarchicalInstancedStaticMeshComponent* ScenicRockComponents[6] = {};
        for (int32 RockIndex = 0; RockIndex < 6; ++RockIndex)
        {
            RockComponents[RockIndex] = AddHism(
                DressingActor, DressingRoot,
                *FString::Printf(TEXT("Boulder%02d"), RockIndex + 1),
                RockMeshes[RockIndex], ReviewedRockMaterial, 180000, 500000,
                ECollisionEnabled::QueryAndPhysics,
                /*bEnableDensityScaling=*/false,
                /*bCastShadow=*/true);
            ScenicRockComponents[RockIndex] = AddHism(
                DressingActor, DressingRoot,
                *FString::Printf(TEXT("ScenicBankRock%02d"), RockIndex + 1),
                RockMeshes[RockIndex], ReviewedRockMaterial, 140000, 420000,
                ECollisionEnabled::NoCollision);
        }
        UHierarchicalInstancedStaticMeshComponent* ShoreCobbleComponents[3] = {};
        CreateSouthForkShoreCobbleComponents(DressingActor, DressingRoot,
            ShoreCobbleMeshes, ShoreCobbleComponents);
        const TSharedPtr<FJsonObject>* VegetationArtifact = nullptr;
        FString VegetationPath;
        FRaftSimPreviewImage VegetationImage;
        if (!(*Tile)->TryGetObjectField(
                TEXT("vegetation_species_density"), VegetationArtifact) ||
            VegetationArtifact == nullptr ||
            !(*VegetationArtifact)->TryGetStringField(TEXT("path"), VegetationPath) ||
            !LoadPreviewPngImage(VegetationPath, VegetationImage) ||
            VegetationImage.Width != Width || VegetationImage.Height != Height)
        {
            return false;
        }
        for (int32 Row = 2; Row < Height - 2; Row += 2)
        {
            const int32 CoordinateIndex = GlobalRowStart + Row;
            if (!CoordinatePoints.IsValidIndex(CoordinateIndex))
            {
                continue;
            }
            const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
            for (int32 Column = 2; Column < Width - 2; ++Column)
            {
                const int32 Index = Row * Width + Column;
                const float LateralM = -256.0f + 4.0f * Column;
                // Only the scanned, non-colliding ground-cover layer may
                // inspect the 14--24 m dry transition bench. The wet/VFX
                // mask below still rejects water, and every larger ecology,
                // cobble, and rock layer retains its later 34 m gate.
                if (FMath::Abs(LateralM) < 14.0f ||
                    FMath::Abs(LateralM) > DetailedTerrainHalfWidthM ||
                    VfxImage.Pixels[Index].A > 0.1f)
                {
                    continue;
                }
                const FLinearColor Density = VegetationImage.Pixels[Index];
                const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                const float ElevationM = DecodeSouthForkHeightM(
                    TerrainHeight.Values[Index], TerrainMinimumM, TerrainMaximumM);
                FVector Location(
                    WorldM.X * 100.0f, WorldM.Y * 100.0f,
                    (ElevationM - VerticalDatumM) * 100.0f);
                // The source products do not resolve individual bank stones.
                // Add explicitly non-colliding deterministic scree where the
                // near-bank terrain is exposed; collision-authority boulders
                // remain exclusively sourced from the catalog below.
                const int32 LeftHeightIndex = Row * Width + FMath::Max(Column - 1, 0);
                const int32 RightHeightIndex = Row * Width + FMath::Min(Column + 1, Width - 1);
                const float LateralSlope = FMath::Abs(
                    DecodeSouthForkHeightM(TerrainHeight.Values[RightHeightIndex], TerrainMinimumM, TerrainMaximumM) -
                    DecodeSouthForkHeightM(TerrainHeight.Values[LeftHeightIndex], TerrainMinimumM, TerrainMaximumM)) / 8.0f;
                const float BankDistanceM = FMath::Abs(LateralM);
                const bool bPrimaryEcologySample = Column % 2 == 0;
                if (bPrimaryEcologySample)
                {
                    Metrics.GroundCoverInstanceCount +=
                        AddSouthForkGroundCoverInstances(
                            GroundCover, Location, TerrainNormals[Index],
                            Point.LeftNormal, CoordinateIndex, Column,
                            BankDistanceM, LateralSlope, Density);
                }
                if (bPrimaryEcologySample || BankDistanceM < 34.0f)
                {
                    Metrics.Cc0ScannedGroundCoverInstanceCount +=
                        AddSouthForkScannedGroundCoverInstances(
                            ScannedGroundCoverComponents,
                            ScannedGroundCoverComponentCount,
                            Location, TerrainNormals[Index], Point.LeftNormal,
                            CoordinateIndex, Column, BankDistanceM,
                            LateralSlope, Density);
                }
                // Interleaved four-metre samples exist only to resolve the
                // dry scanned shoreline underlayer. All legacy ecology,
                // cobble, rock, and infrastructure retain the eight-metre
                // sampling lattice.
                if (!bPrimaryEcologySample)
                {
                    continue;
                }
                // Preserve the reviewed minimum distance for trees, cobble,
                // and larger rocks. The non-colliding grass presentation may
                // extend into the 24--34 m transition bench.
                if (BankDistanceM < 34.0f)
                {
                    continue;
                }
                Metrics.ShoreCobbleInstanceCount += AddSouthForkShoreCobbleInstances(
                    ShoreCobbleComponents, Location, Point.LeftNormal, CoordinateIndex, Column, BankDistanceM, LateralSlope);
                Metrics.FoliageInstanceCount += AddSouthForkBankUnderstoryInstance(Understory,
                    Location, Point.LeftNormal, CoordinateIndex, Column, BankDistanceM, LateralSlope, Density);
                const float ScenicRockProbability =
                    (BankDistanceM >= 36.0f && BankDistanceM <= 92.0f)
                    ? FMath::Clamp(0.035f + LateralSlope * 0.18f, 0.035f, 0.22f)
                    : 0.0f;
                if (StableUnitRandom(CoordinateIndex, Column, 47) < ScenicRockProbability)
                {
                    const int32 RockIndex =
                        FMath::Abs(CoordinateIndex * 3 + Column * 11) % 6;
                    if (ScenicRockComponents[RockIndex])
                    {
                        const float RockScale = FMath::Lerp(
                            0.48f, 1.62f,
                            StableUnitRandom(CoordinateIndex, Column, 53));
                        ScenicRockComponents[RockIndex]->AddInstance(
                            FTransform(
                                FRotator(
                                    StableUnitRandom(CoordinateIndex, Column, 59) * 22.0f - 11.0f,
                                    StableUnitRandom(CoordinateIndex, Column, 61) * 360.0f,
                                    StableUnitRandom(CoordinateIndex, Column, 67) * 18.0f - 9.0f),
                                // The reviewed meshes have an imported base
                                // roughly 0.65 m below their pivot.  The old
                                // 0.22 m lift buried most scenic instances and
                                // left the intended talus invisible.
                                Location + FVector(0.0f, 0.0f, RockScale * 64.0f),
                                FVector(RockScale)),
                            /*bWorldSpace=*/true);
                        ++Metrics.ScenicRockInstanceCount;
                    }
                }
                const float Selection = StableUnitRandom(CoordinateIndex, Column, 19);
                UHierarchicalInstancedStaticMeshComponent* Target = nullptr;
                float Probability = 0.0f;
                float BaseScale = 1.0f;
                SelectSouthForkDetailedFoliage(Conifers, Broadleaf, Riparian, Understory,
                    Density, LateralM, CoordinateIndex, Column, Target, Probability, BaseScale);
                if (Target == Understory && LateralSlope > 0.38f)
                {
                    // Upright chaparral cards are not credible on cliff faces
                    // and can silhouette above a coarse DEM ridge. Reserve
                    // this ecology for benches and moderate dry banks.
                    continue;
                }
                // Aerial density is authoritative at the corridor scale, but
                // individual stems are unresolved. Modulate its point sample
                // with a continuous, deterministic patch field so the 8 m
                // candidate lattice forms natural groves and openings instead
                // of evenly spaced rows along both banks.
                const float DetailedFoliagePatchNoise = 0.5f + 0.5f *
                    FMath::PerlinNoise2D(FVector2D(Location.X, Location.Y) / 36000.0f);
                Probability = FMath::Clamp(
                    Probability * FMath::Lerp(0.58f, 1.36f, DetailedFoliagePatchNoise),
                    0.0f, 0.92f);
                if (Target && Selection < Probability)
                {
                    const float Scale = BaseScale *
                        FMath::Lerp(0.78f, 1.22f,
                            StableUnitRandom(CoordinateIndex, Column, 23));
                    const float Yaw = StableUnitRandom(CoordinateIndex, Column, 29) * 360.0f;
                    FVector InstanceScale(Scale);
                    if (Target == Broadleaf || Target == Riparian)
                    {
                        InstanceScale.X *= FMath::Lerp(
                            0.82f, 1.16f,
                            StableUnitRandom(CoordinateIndex, Column, 31));
                        InstanceScale.Y *= FMath::Lerp(
                            0.84f, 1.14f,
                            StableUnitRandom(CoordinateIndex, Column, 37));
                        InstanceScale.Z *= FMath::Lerp(
                            0.86f, 1.18f,
                            StableUnitRandom(CoordinateIndex, Column, 43));
                    }
                    const FVector GroundedLocation = Target == Understory
                        ? Location - FVector(0.0f, 0.0f, Scale * 24.0f)
                        : Location;
                    const FVector AlongRiver = CoordinateTangent(
                        CoordinatePoints, CoordinateIndex);
                    const FVector AcrossRiver(
                        Point.LeftNormal.X, Point.LeftNormal.Y, 0.0f);
                    const float AlongJitterCm = FMath::Lerp(
                        -280.0f, 280.0f,
                        StableUnitRandom(CoordinateIndex, Column, 109));
                    const float AcrossJitterCm = FMath::Lerp(
                        -250.0f, 250.0f,
                        StableUnitRandom(CoordinateIndex, Column, 113));
                    const FVector NaturalizedLocation = GroundedLocation +
                        AlongRiver * AlongJitterCm + AcrossRiver * AcrossJitterCm;
                    Target->AddInstance(
                        FTransform(FRotator(0.0f, Yaw, 0.0f), NaturalizedLocation,
                            InstanceScale),
                        /*bWorldSpace=*/true);
                    ++Metrics.FoliageInstanceCount;
                }
            }
        }

        if (BoulderValues)
        {
            for (const TSharedPtr<FJsonValue>& BoulderValue : *BoulderValues)
            {
                const TSharedPtr<FJsonObject>* Boulder = nullptr;
                if (!BoulderValue->TryGetObject(Boulder) || Boulder == nullptr)
                {
                    continue;
                }
                double StationM = 0.0;
                double LateralM = 0.0;
                double RadiusM = 1.0;
                double HeightM = 1.0;
                (*Boulder)->TryGetNumberField(TEXT("station_m"), StationM);
                (*Boulder)->TryGetNumberField(TEXT("lateral_offset_m"), LateralM);
                (*Boulder)->TryGetNumberField(TEXT("radius_m"), RadiusM);
                (*Boulder)->TryGetNumberField(TEXT("height_m"), HeightM);
                const int32 CoordinateIndex = ClosestCoordinateIndex(
                    CoordinatePoints, StationM);
                if (CoordinateIndex < GlobalRowStart ||
                    CoordinateIndex >= GlobalRowStart + Height)
                {
                    continue;
                }
                const int32 LocalRow = CoordinateIndex - GlobalRowStart;
                const int32 Column = FMath::Clamp(
                    FMath::RoundToInt((static_cast<float>(LateralM) + 256.0f) / 4.0f),
                    0, Width - 1);
                const int32 HeightIndex = LocalRow * Width + Column;
                const float PresentationStationM = static_cast<float>(StationM);
                const float PresentationLateralM = static_cast<float>(LateralM);
                const float PresentationRadiusM = static_cast<float>(RadiusM);
                const bool bOverlapsAcceptedPresentation =
                    ShouldSuppressSouthForkBoulderPresentation(
                        AcceptedBoulderPresentationFootprints, PresentationStationM,
                        PresentationLateralM, PresentationRadiusM);
                if (bOverlapsAcceptedPresentation)
                {
                    ++Metrics.BoulderOverlapSuppressedInstanceCount;
                    continue;
                }
                const float BedM = DecodeSouthForkHeightM(
                    TerrainHeight.Values[HeightIndex], TerrainMinimumM, TerrainMaximumM);
                const FVector2D WorldM = CoordinateWorldM(
                    CoordinatePoints[CoordinateIndex], static_cast<float>(LateralM));
                const int32 RockIndex =
                    FMath::Abs(CoordinateIndex + Column * 7) % 6;
                if (RockComponents[RockIndex])
                {
                    // Fit source bounds to the catalog and embed the watertight base by 12%.
                    const float ScaleXY = PresentationRadiusM * 0.8481f;
                    const float ScaleZ = static_cast<float>(HeightM) * 0.7045f;
                    RockComponents[RockIndex]->AddInstance(
                        FTransform(
                            FRotator(
                                StableUnitRandom(CoordinateIndex, Column, 31) * 18.0f - 9.0f,
                                StableUnitRandom(CoordinateIndex, Column, 37) * 360.0f,
                                StableUnitRandom(CoordinateIndex, Column, 41) * 14.0f - 7.0f),
                            FVector(
                                WorldM.X * 100.0f, WorldM.Y * 100.0f,
                                (BedM - VerticalDatumM +
                                    static_cast<float>(HeightM) * 0.386f) * 100.0f),
                            FVector(ScaleXY, ScaleXY, ScaleZ)),
                        /*bWorldSpace=*/true);
                    AcceptedBoulderPresentationFootprints.Add(
                        FSouthForkBoulderPresentationFootprint{
                            PresentationStationM, PresentationLateralM,
                            PresentationRadiusM});
                    ++Metrics.BoulderInstanceCount;
                }
            }
        }

        const TSharedPtr<FJsonObject>* WaterBands = nullptr;
        if (!(*Tile)->TryGetObjectField(TEXT("water_bands"), WaterBands) ||
            WaterBands == nullptr)
        {
            return false;
        }
        const TSharedPtr<FJsonObject>* WaterEncoding = nullptr;
        if (!(*Tile)->TryGetObjectField(TEXT("water_height_encoding"), WaterEncoding) ||
            WaterEncoding == nullptr)
        {
            return false;
        }
        double WaterMinimumM = 0.0;
        double WaterMaximumM = 0.0;
        (*WaterEncoding)->TryGetNumberField(TEXT("minimum_elevation_m"), WaterMinimumM);
        (*WaterEncoding)->TryGetNumberField(TEXT("maximum_elevation_m"), WaterMaximumM);
        const TCHAR* FlowBands[] = {
            TEXT("low_runnable"), TEXT("median_runnable"), TEXT("high_runnable")};
        for (const TCHAR* FlowBand : FlowBands)
        {
            const TSharedPtr<FJsonObject>* Band = nullptr;
            const TSharedPtr<FJsonObject>* SurfaceArtifact = nullptr;
            const TSharedPtr<FJsonObject>* PresentationArtifact = nullptr;
            FString SurfacePath;
            FString PresentationPath;
            if (!(*WaterBands)->TryGetObjectField(FlowBand, Band) || Band == nullptr ||
                !(*Band)->TryGetObjectField(TEXT("surface_height"), SurfaceArtifact) ||
                !(*Band)->TryGetObjectField(TEXT("presentation"), PresentationArtifact) ||
                !(*SurfaceArtifact)->TryGetStringField(TEXT("path"), SurfacePath) ||
                !(*PresentationArtifact)->TryGetStringField(TEXT("path"), PresentationPath))
            {
                return false;
            }
            FSouthForkGray16Image WaterHeight;
            FRaftSimPreviewImage Presentation;
            if (!LoadGray16Png(SurfacePath, WaterHeight) ||
                !LoadPreviewPngImage(PresentationPath, Presentation) ||
                WaterHeight.Width != Presentation.Width ||
                WaterHeight.Height != Presentation.Height ||
                WaterHeight.Height != Height)
            {
                return false;
            }
            const int32 WaterWidth = WaterHeight.Width;
            TArray<FVector> WaterVertices;
            TArray<FVector2D> WaterUvs;
            TArray<FLinearColor> WaterColors;
            TArray<float> WaterShorelineDepthsM;
            WaterVertices.SetNum(WaterWidth * Height);
            WaterUvs.SetNum(WaterWidth * Height);
            WaterColors.SetNum(WaterWidth * Height);
            WaterShorelineDepthsM.SetNum(WaterWidth * Height);
            for (int32 Row = 0; Row < Height; ++Row)
            {
                const int32 CoordinateIndex = FMath::Clamp(
                    GlobalRowStart + Row, 0, CoordinatePoints.Num() - 1);
                const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
                TArray<float> RowSurfaceElevationsM;
                TArray<FLinearColor> RowHydraulicPresentation;
                int32 LeftWetColumn = INDEX_NONE;
                int32 RightWetColumn = INDEX_NONE;
                if (!PrepareSouthForkWaterSurfaceRow(
                        WaterHeight.Values, Presentation.Pixels, WaterWidth, Row,
                        WaterMinimumM, WaterMaximumM, RowSurfaceElevationsM,
                        RowHydraulicPresentation, LeftWetColumn, RightWetColumn)) return false;
                for (int32 Column = 0; Column < WaterWidth; ++Column)
                {
                    const int32 Index = Row * WaterWidth + Column;
                    const float LateralM = -40.0f + 4.0f * Column;
                    const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                    const float ElevationM = RowSurfaceElevationsM[Column];
                    const int32 TerrainColumn = FMath::Clamp(
                        FMath::RoundToInt((LateralM + 256.0f) / 4.0f), 0, TerrainHeight.Width - 1);
                    const float TerrainElevationM = DecodeSouthForkHeightM(
                        TerrainHeight.Values[Row * TerrainHeight.Width + TerrainColumn], TerrainMinimumM, TerrainMaximumM);
                    const float ShorelineDepthM = ElevationM - TerrainElevationM;
                    FLinearColor HydraulicPresentation =
                        RowHydraulicPresentation[Column];
                    const bool bTouchesSolverWetChannel =
                        Column == LeftWetColumn - 1 ||
                        Column == RightWetColumn + 1;
                    if (bTouchesSolverWetChannel)
                    {
                        HydraulicPresentation = CompleteSouthForkShorelinePresentation(
                            HydraulicPresentation, ShorelineDepthM,
                            Metrics.ProceduralShorelineCompletionVertexCount);
                    }
                    const float HydraulicEnergy = FMath::Clamp(
                        HydraulicPresentation.R * 0.72f +
                        HydraulicPresentation.B * 0.48f,
                        0.0f, 1.0f);
                    // Presentation-only sub-grid surface displacement. The
                    // fixed-step shallow-water arrays remain authoritative;
                    // this deterministic visual layer resolves ripples and
                    // standing-wave shoulders below the 4 m solver mesh.
                    const float WavePhaseA =
                        Point.StationM * 0.19f + LateralM * 0.61f;
                    const float WavePhaseB =
                        Point.StationM * 0.071f - LateralM * 0.37f;
                    const float VisualDisplacementM =
                        0.018f * FMath::Sin(WavePhaseA) +
                        HydraulicEnergy *
                            (0.16f * FMath::Sin(WavePhaseA) +
                             0.09f * FMath::Sin(WavePhaseB));
                    WaterVertices[Index] = FVector(
                        (WorldM.X - TileOriginM.X) * 100.0f,
                        (WorldM.Y - TileOriginM.Y) * 100.0f,
                        (ElevationM + VisualDisplacementM - VerticalDatumM) * 100.0f);
                    WaterUvs[Index] = FVector2D(
                        Point.StationM / 3.0f,
                        LateralM / 3.0f);
                    WaterColors[Index] = HydraulicPresentation;
                    WaterShorelineDepthsM[Index] = ShorelineDepthM;
                }
                if (FCString::Strcmp(FlowBand, TEXT("median_runnable")) == 0)
                {
                    Metrics.MedianCenterWaterLocalZCm[CoordinateIndex] =
                        WaterVertices[Row * WaterWidth + WaterWidth / 2].Z;
                }
            }
            if (!SmoothSouthForkWaterVisibilityLongitudinally(
                    4, WaterWidth, Height, WaterColors)) return false;
            int32 WaterPresentationWidth = WaterWidth, WaterPresentationHeight = Height;
            if (!RefineSouthForkWaterPresentationGrid(2, WaterPresentationWidth, WaterPresentationHeight,
                    WaterVertices, WaterUvs, WaterColors,
                    WaterShorelineDepthsM)) return false;
            float MaximumMicroReliefCm = 0.0f;
            if (!ApplySouthForkWaterPresentationMicroRelief(
                    WaterVertices, WaterUvs, WaterColors,
                    WaterShorelineDepthsM, MaximumMicroReliefCm))
            {
                OutSummary += FString::Printf(
                    TEXT("Failed to apply visual water micro-relief for %s %s.\n"),
                    *TileId, FlowBand);
                return false;
            }
            TArray<FVector> TerrainClippedWaterVertices;
            TArray<int32> WaterTriangles;
            TArray<FVector2D> TerrainClippedWaterUvs;
            TArray<FLinearColor> TerrainClippedWaterColors;
            TArray<FVector> WaterNormals;
            TArray<FProcMeshTangent> WaterTangents;
            if (!BuildSouthForkTerrainClippedWaterGeometry(
                    WaterVertices, WaterUvs, WaterColors,
                    WaterShorelineDepthsM,
                    WaterPresentationWidth, WaterPresentationHeight,
                    TerrainClippedWaterVertices, WaterTriangles,
                    TerrainClippedWaterUvs, TerrainClippedWaterColors,
                    WaterNormals, WaterTangents,
                    Metrics.ProceduralShorelineTransitionCellCount))
            {
                OutSummary += FString::Printf(
                    TEXT("Failed to terrain-clip water geometry for %s %s.\n"),
                    *TileId, FlowBand);
                return false;
            }
            const FString WaterAssetPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/SM_%s_Water_%s"), *TileId, FlowBand);
            UStaticMesh* WaterMesh = bReuseExistingWaterMeshes
                ? LoadSouthForkStaticMeshAsset(WaterAssetPath)
                : nullptr;
            if (!WaterMesh)
            {
                WaterMesh = CreateSouthForkMeshAsset(
                    World, WaterAssetPath,
                    FString::Printf(TEXT("%s_Water_%s"), *TileId, FlowBand),
                    TerrainClippedWaterVertices, WaterTriangles, WaterNormals,
                    TerrainClippedWaterUvs, TerrainClippedWaterColors,
                    WaterTangents, WaterMaterial,
                    /*bEnableNanite=*/false,
                    /*bComplexCollision=*/false, OutSummary);
            }
            AStaticMeshActor* WaterActor = WaterMesh ? PlaceSouthForkStaticMeshActor(
                World, WaterMesh, WaterMaterial,
                FString::Printf(TEXT("RaftSim_SouthFork_Water_%s_%s"), *TileId, FlowBand),
                FTransform(FVector(TileOriginM.X * 100.0f, TileOriginM.Y * 100.0f, 0.0f)),
                *FString::Printf(TEXT("RaftSimFlowBand_%s"), FlowBand),
                ECollisionEnabled::NoCollision) : nullptr;
            if (!WaterActor)
            {
                return false;
            }
            ConfigureSouthForkSingleLayerWaterActor(WaterActor);
            const bool bMedian = FCString::Strcmp(FlowBand, TEXT("median_runnable")) == 0;
            WaterActor->SetActorHiddenInGame(!bMedian);
            ++Metrics.WaterTileCount;
            Metrics.WaterTriangleCount += WaterTriangles.Num() / 3;

            // The broad Single Layer Water material retains the solver foam
            // channel, but a grazing guide-eye view can flatten its strongest
            // cells into the base surface. Author a second, non-colliding
            // one-metre aerated sheet only over positive solver-derived or
            // review-gated guide-feature-conditioned triangles. This
            // gives those cells bounded geometric volume while calm water,
            // collision, hydraulic state, and gameplay remain unchanged.
            TArray<FVector> WhitewaterVertices;
            TArray<int32> WhitewaterTriangles;
            TArray<FVector2D> WhitewaterUvs;
            TArray<FLinearColor> WhitewaterColors;
            int32 WhitewaterPresentationWidth = 0;
            int32 WhitewaterPresentationHeight = 0;
            if (!BuildSouthForkRefinedWhitewaterOverlayGeometry(
                    WaterVertices, WaterUvs, WaterColors,
                    WaterShorelineDepthsM,
                    WaterPresentationWidth, WaterPresentationHeight,
                    WhitewaterVertices, WhitewaterTriangles, WhitewaterUvs,
                    WhitewaterColors, WhitewaterPresentationWidth,
                    WhitewaterPresentationHeight))
            {
                return false;
            }
            if (!WhitewaterTriangles.IsEmpty())
            {
                const FString WhitewaterAssetPath = FString::Printf(
                    TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
                         "SM_%s_WhitewaterFoam_%s"),
                    *TileId,
                    FlowBand);
                UStaticMesh* WhitewaterMesh = bReuseExistingWaterMeshes
                    ? LoadSouthForkStaticMeshAsset(WhitewaterAssetPath)
                    : nullptr;
                if (!WhitewaterMesh)
                {
                    const TArray<FVector> WhitewaterNormals =
                        ComputePreviewMeshNormals(
                            WhitewaterVertices, WhitewaterTriangles);
                    WhitewaterMesh = CreateSouthForkMeshAsset(
                        World,
                        WhitewaterAssetPath,
                        FString::Printf(
                            TEXT("%s_WhitewaterFoam_%s"), *TileId, FlowBand),
                        WhitewaterVertices,
                        WhitewaterTriangles,
                        WhitewaterNormals,
                        WhitewaterUvs,
                        WhitewaterColors,
                        BuildSouthForkFlowTangents(
                            WhitewaterVertices,
                            WhitewaterPresentationWidth,
                            WhitewaterPresentationHeight),
                        WhitewaterFoamMaterial,
                        /*bEnableNanite=*/false,
                        /*bComplexCollision=*/false,
                        OutSummary);
                }
                AStaticMeshActor* WhitewaterActor = WhitewaterMesh
                    ? PlaceSouthForkStaticMeshActor(
                        World,
                        WhitewaterMesh,
                        WhitewaterFoamMaterial,
                        FString::Printf(
                            TEXT("RaftSim_SouthFork_WhitewaterFoam_%s_%s"),
                            *TileId,
                            FlowBand),
                        FTransform(FVector(
                            TileOriginM.X * 100.0f,
                            TileOriginM.Y * 100.0f,
                            0.0f)),
                        *FString::Printf(TEXT("RaftSimFlowBand_%s"), FlowBand),
                        ECollisionEnabled::NoCollision)
                    : nullptr;
                if (!WhitewaterActor)
                {
                    return false;
                }
                WhitewaterActor->Tags.AddUnique(
                    FName(TEXT("RaftSimSolverFoamOverlay")));
                WhitewaterActor->SetActorHiddenInGame(!bMedian);
                UStaticMeshComponent* WhitewaterComponent =
                    WhitewaterActor->GetStaticMeshComponent();
                WhitewaterComponent->SetCastShadow(false);
                WhitewaterComponent->TranslucencySortPriority = 2;
                ++Metrics.WhitewaterFoamActorCount;
                Metrics.WhitewaterFoamTriangleCount +=
                    WhitewaterTriangles.Num() / 3;
            }
        }

        if (Spray)
        {
            for (int32 Row = 4; Row < Height - 4; Row += 12)
            {
                const int32 CoordinateIndex = GlobalRowStart + Row;
                if (!CoordinatePoints.IsValidIndex(CoordinateIndex))
                {
                    continue;
                }
                const int32 VfxCenterIndex = Row * Width + Width / 2;
                const FLinearColor Zone = VfxImage.Pixels[VfxCenterIndex];
                if (Zone.G < 0.5f && Zone.B < 0.25f)
                {
                    continue;
                }
                const float SurfaceZCm = Metrics.MedianCenterWaterLocalZCm.IsValidIndex(CoordinateIndex)
                    ? Metrics.MedianCenterWaterLocalZCm[CoordinateIndex]
                    : TerrainVertices[Row * Width + Width / 2].Z + 120.0f;
                for (int32 Particle = 0; Particle < 3; ++Particle)
                {
                    const float LateralM = FMath::Lerp(
                        -18.0f, 18.0f,
                        StableUnitRandom(CoordinateIndex, Particle, 43));
                    const FVector2D WorldM = CoordinateWorldM(
                        CoordinatePoints[CoordinateIndex], LateralM);
                    const float Scale = FMath::Lerp(
                        0.012f, 0.045f,
                        StableUnitRandom(CoordinateIndex, Particle, 47));
                    Spray->AddInstance(
                        FTransform(
                            FRotator::ZeroRotator,
                            FVector(
                                WorldM.X * 100.0f, WorldM.Y * 100.0f,
                                SurfaceZCm + FMath::Lerp(35.0f, 190.0f,
                                    StableUnitRandom(CoordinateIndex, Particle, 53))),
                            FVector(Scale, Scale, Scale * 1.8f)),
                        /*bWorldSpace=*/true);
                    ++Metrics.SprayMistInstanceCount;
                }
            }
        }
    }

    // Each of the five camera windows is guaranteed coverage. A window that
    // crosses a source-tile seam emits one presentation patch per tile so it
    // can preserve the source registration and world-space noise phase.
    if (Metrics.BankMicroreliefPatchCount < 5 ||
        Metrics.BankMicroreliefPatchCount > 10 ||
        Metrics.BankMicroreliefVertexCount < 120000 ||
        Metrics.BankMicroreliefTriangleCount < 180000 ||
        Metrics.BankMicroreliefMaximumDisplacementCm <= 8.0f ||
        Metrics.BankMicroreliefMaximumDisplacementCm > 42.0f)
    {
        OutSummary += FString::Printf(
            TEXT("South Fork bank-microrelief gate failed: patches=%d vertices=%lld "
                 "triangles=%lld maximum=%.2f cm.\n"),
            Metrics.BankMicroreliefPatchCount,
            Metrics.BankMicroreliefVertexCount,
            Metrics.BankMicroreliefTriangleCount,
            Metrics.BankMicroreliefMaximumDisplacementCm);
        return false;
    }

    if (!CreateTerminalVisualWater(
            World, CoordinatePoints, Metrics.MedianCenterWaterLocalZCm.Last(),
            WaterMaterial, bReuseExistingWaterMeshes, Metrics, OutSummary))
    {
        OutSummary += TEXT("Failed to create the Salmon Falls visual water continuation.\n");
        return false;
    }

    const TSharedPtr<FJsonObject>* FarFieldRoot = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* FarFieldPatchValues = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("far_field"), FarFieldRoot) ||
        FarFieldRoot == nullptr ||
        !(*FarFieldRoot)->TryGetArrayField(TEXT("patches"), FarFieldPatchValues) ||
        FarFieldPatchValues == nullptr || FarFieldPatchValues->Num() != 8)
    {
        OutSummary += TEXT("The South Fork far-field geography is incomplete.\n");
        return false;
    }
    for (int32 PatchOrdinal = 0; PatchOrdinal < FarFieldPatchValues->Num(); ++PatchOrdinal)
    {
        const TSharedPtr<FJsonObject>* Patch = nullptr;
        const TArray<TSharedPtr<FJsonValue>>* Bounds = nullptr;
        const TSharedPtr<FJsonObject>* HeightArtifact = nullptr;
        const TSharedPtr<FJsonObject>* HeightEncoding = nullptr;
        const TSharedPtr<FJsonObject>* MacroArtifact = nullptr;
        const TSharedPtr<FJsonObject>* MaskArtifact = nullptr;
        const TSharedPtr<FJsonObject>* OwnershipArtifact = nullptr;
        const TSharedPtr<FJsonObject>* RiverDistanceArtifact = nullptr;
        FString PatchId;
        FString HeightPath;
        FString MacroPath;
        FString MaskPath;
        FString OwnershipPath;
        FString RiverDistancePath;
        if (!(*FarFieldPatchValues)[PatchOrdinal]->TryGetObject(Patch) || Patch == nullptr ||
            !(*Patch)->TryGetStringField(TEXT("patch_id"), PatchId) ||
            !(*Patch)->TryGetArrayField(TEXT("bounds_local_m"), Bounds) ||
            Bounds == nullptr || Bounds->Num() != 4 ||
            !(*Patch)->TryGetObjectField(TEXT("height"), HeightArtifact) ||
            !(*Patch)->TryGetObjectField(TEXT("height_encoding"), HeightEncoding) ||
            !(*Patch)->TryGetObjectField(TEXT("macro_albedo"), MacroArtifact) ||
            !(*Patch)->TryGetObjectField(TEXT("corridor_exclusion_mask"), MaskArtifact) ||
            !(*Patch)->TryGetObjectField(
                TEXT("source_window_ownership_mask"), OwnershipArtifact) ||
            !(*Patch)->TryGetObjectField(
                TEXT("river_distance_to_route"), RiverDistanceArtifact) ||
            !(*HeightArtifact)->TryGetStringField(TEXT("path"), HeightPath) ||
            !(*MacroArtifact)->TryGetStringField(TEXT("path"), MacroPath) ||
            !(*MaskArtifact)->TryGetStringField(TEXT("path"), MaskPath) ||
            !(*OwnershipArtifact)->TryGetStringField(TEXT("path"), OwnershipPath) ||
            !(*RiverDistanceArtifact)->TryGetStringField(
                TEXT("path"), RiverDistancePath))
        {
            return false;
        }
        double MinimumElevationM = 0.0;
        double MaximumElevationM = 0.0;
        (*HeightEncoding)->TryGetNumberField(
            TEXT("minimum_elevation_m"), MinimumElevationM);
        (*HeightEncoding)->TryGetNumberField(
            TEXT("maximum_elevation_m"), MaximumElevationM);
        FSouthForkGray16Image HeightImage;
        FRaftSimPreviewImage MacroImage;
        FRaftSimPreviewImage MaskImage;
        FRaftSimPreviewImage OwnershipImage;
        FSouthForkGray16Image RiverDistanceImage;
        if (!LoadGray16Png(HeightPath, HeightImage) ||
            !LoadPreviewPngImage(MacroPath, MacroImage) ||
            !LoadPreviewPngImage(MaskPath, MaskImage) ||
            !LoadPreviewPngImage(OwnershipPath, OwnershipImage) ||
            !LoadGray16Png(RiverDistancePath, RiverDistanceImage) ||
            MacroImage.Width <= 0 || MacroImage.Height <= 0 ||
            MaskImage.Width != HeightImage.Width ||
            MaskImage.Height != HeightImage.Height ||
            OwnershipImage.Width != HeightImage.Width ||
            OwnershipImage.Height != HeightImage.Height ||
            RiverDistanceImage.Width != HeightImage.Width ||
            RiverDistanceImage.Height != HeightImage.Height)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to decode far-field patch %s.\n"), *PatchId);
            return false;
        }
        UTexture2D* PatchMacroTexture =
            bReuseExistingFarFieldMeshes && !bRebuildFarFieldMacroTextures
            ? LoadSouthForkTerrainMacroTextureForReuse(PatchId, OutSummary)
            : CreateSouthForkTerrainMacroTexture(PatchId, MacroPath, OutSummary);
        UMaterialInstanceConstant* PatchTerrainMaterial =
            CreateSouthForkTerrainMaterialInstance(
                PatchId, TerrainMaterial, PatchMacroTexture,
                /*bUseCorridorEdgeBlend=*/false, OutSummary);
        if (!PatchMacroTexture || !PatchTerrainMaterial)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create source-draped far-field material for %s.\n"),
                *PatchId);
            return false;
        }
        const double MinimumX = (*Bounds)[0]->AsNumber();
        const double MinimumY = (*Bounds)[1]->AsNumber();
        const double MaximumX = (*Bounds)[2]->AsNumber();
        const double MaximumY = (*Bounds)[3]->AsNumber();
        const FVector2D PatchOriginM(
            0.5 * (MinimumX + MaximumX), 0.5 * (MinimumY + MaximumY));
        const int32 Width = HeightImage.Width;
        const int32 Height = HeightImage.Height;
        const double HeightCellWidthM =
            (MaximumX - MinimumX) / FMath::Max(Width - 1, 1);
        const double HeightCellHeightM =
            (MaximumY - MinimumY) / FMath::Max(Height - 1, 1);
        const auto SampleMacroAtUv = [&MacroImage](double U, double V)
        {
            const int32 MacroColumn = FMath::Clamp(
                FMath::RoundToInt(U * FMath::Max(MacroImage.Width - 1, 0)),
                0, MacroImage.Width - 1);
            const int32 MacroRow = FMath::Clamp(
                FMath::RoundToInt(V * FMath::Max(MacroImage.Height - 1, 0)),
                0, MacroImage.Height - 1);
            return MacroImage.Pixels[MacroRow * MacroImage.Width + MacroColumn];
        };
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        TArray<float> SourceElevationsM;
        Vertices.SetNum(Width * Height);
        Uvs.SetNum(Width * Height);
        Colors.SetNum(Width * Height);
        SourceElevationsM.SetNumUninitialized(Width * Height);
        for (int32 Index = 0; Index < SourceElevationsM.Num(); ++Index)
        {
            SourceElevationsM[Index] = DecodeSouthForkHeightM(
                HeightImage.Values[Index], MinimumElevationM, MaximumElevationM);
        }
        for (int32 Row = 0; Row < Height; ++Row)
        {
            const double RowT = static_cast<double>(Row) / FMath::Max(Height - 1, 1);
            const double WorldY = FMath::Lerp(MaximumY, MinimumY, RowT);
            for (int32 Column = 0; Column < Width; ++Column)
            {
                const double ColumnT =
                    static_cast<double>(Column) / FMath::Max(Width - 1, 1);
                const double WorldX = FMath::Lerp(MinimumX, MaximumX, ColumnT);
                const int32 Index = Row * Width + Column;
                const int32 LeftColumn = FMath::Max(Column - 1, 0);
                const int32 RightColumn = FMath::Min(Column + 1, Width - 1);
                const int32 NorthRow = FMath::Max(Row - 1, 0);
                const int32 SouthRow = FMath::Min(Row + 1, Height - 1);
                const float GradientX =
                    (SourceElevationsM[Row * Width + RightColumn] -
                     SourceElevationsM[Row * Width + LeftColumn]) /
                    FMath::Max(
                        static_cast<float>((RightColumn - LeftColumn) * HeightCellWidthM),
                        0.01f);
                const float GradientY =
                    (SourceElevationsM[NorthRow * Width + Column] -
                     SourceElevationsM[SouthRow * Width + Column]) /
                    FMath::Max(
                        static_cast<float>((SouthRow - NorthRow) * HeightCellHeightM),
                        0.01f);
                const float SourceSlope = FMath::Sqrt(
                    GradientX * GradientX + GradientY * GradientY);
                const float ElevationM = SourceElevationsM[Index] +
                    ComputeSouthForkFarFieldCorridorReliefWeight(
                        MaskImage, Row, Column) * ComputeSouthForkInferredFarFieldReliefM(
                            WorldX, WorldY, SourceSlope);
                Vertices[Index] = FVector(
                    (WorldX - PatchOriginM.X) * 100.0,
                    (WorldY - PatchOriginM.Y) * 100.0,
                    (ElevationM - VerticalDatumM) * 100.0f - 75.0f);
                Uvs[Index] = FVector2D(ColumnT, RowT);
                Colors[Index] = DecodeSouthForkPreviewSrgbColor(
                    SampleMacroAtUv(ColumnT, RowT));
                Colors[Index].A = 0.0f;
            }
        }
        TArray<int32> Triangles;
        for (int32 Row = 0; Row < Height - 1; ++Row)
        {
            for (int32 Column = 0; Column < Width - 1; ++Column)
            {
                const int32 I0 = Row * Width + Column;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + Width;
                const int32 I3 = I2 + 1;
                // Clip each triangle independently. The former two-of-four
                // cell rule emitted both triangles when only two corners were
                // visible, so masked corridor vertices could remain connected
                // to high valley vertices. Those long sloping faces appeared
                // as suspended terrain shelves above the guide-eye camera.
                const auto IsOwnedAndVisible =
                    [&OwnershipImage, &MaskImage](int32 VertexIndex)
                {
                    return OwnershipImage.Pixels[VertexIndex].R > 0.5f &&
                        MaskImage.Pixels[VertexIndex].R > 0.5f;
                };
                if (IsOwnedAndVisible(I0) && IsOwnedAndVisible(I1) &&
                    IsOwnedAndVisible(I2))
                {
                    Triangles.Append({I0, I1, I2});
                }
                if (IsOwnedAndVisible(I1) && IsOwnedAndVisible(I3) &&
                    IsOwnedAndVisible(I2))
                {
                    Triangles.Append({I1, I3, I2});
                }
            }
        }

        const FString AssetPath = FString::Printf(
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/FarField/SM_%s"),
            *PatchId);
        const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        const TArray<FProcMeshTangent> Tangents =
            BuildSouthForkFlowTangents(Vertices, Width, Height);
        UStaticMesh* Mesh = bReuseExistingFarFieldMeshes
            ? LoadSouthForkStaticMeshAsset(AssetPath)
            : nullptr;
        if (!Mesh)
        {
            Mesh = CreateSouthForkMeshAsset(
                World, AssetPath, PatchId, Vertices, Triangles, Normals, Uvs,
                Colors, Tangents, PatchTerrainMaterial,
                /*bEnableNanite=*/true,
                /*bComplexCollision=*/false, OutSummary,
                /*bPreserveNaniteFallbackTopology=*/true);
        }
        if (PatchOrdinal == 0)
        {
            LogStaticMeshVertexColorSummary(TEXT("far_field_00"), Mesh);
        }
        if (!Mesh || !ConfigureSouthForkFarFieldTerrainActor(PlaceSouthForkStaticMeshActor(
                World, Mesh, PatchTerrainMaterial,
                TEXT("RaftSim_SouthFork_FarField_") + PatchId,
                FTransform(FVector(PatchOriginM.X * 100.0, PatchOriginM.Y * 100.0, 0.0)),
                TEXT("RaftSimFullReachFarField"), ECollisionEnabled::NoCollision)))
        {
            return false;
        }
        ++Metrics.FarFieldPatchCount;
        Metrics.FarFieldTriangleCount += Triangles.Num() / 3;

        AActor* FarDressing = CreateInstancingActor(
            World, TEXT("RaftSim_SouthFork_FarFieldDressing_") + PatchId,
            TEXT("RaftSimFullReachFarFieldDressing"));
        USceneComponent* FarRoot = FarDressing ? FarDressing->GetRootComponent() : nullptr;
        // A single repeated full-tree card on every far-field sample produced an
        // unmistakable plantation/grid silhouette. Use the three actual
        // project-owned Ponderosa crown/height profiles directly; the former
        // FarConiferCard component duplicated profile A and left 93.3% of the
        // visible population on one silhouette. The current cards retain each
        // full source photograph on two crossed planes; imported broadleaf
        // comparison assets remain isolated because they exposed pale
        // silhouettes in this rig.
        // At the High/60% production baseline, a twelve-metre crown reaches
        // roughly one output pixel at six kilometres. Fade generated clusters at
        // that screen-space limit instead of rasterizing masked planes out to
        // nine kilometres. Their NAIP source macro already contains canopy
        // colour and sun shadows, so suppressing a second dynamic card shadow
        // avoids dark repeated stamps rather than removing geographic detail.
        // Far-field HISMs also opt into the existing High=0.75/Epic=1.0
        // foliage policy; detailed corridor foliage remains full density.
        UHierarchicalInstancedStaticMeshComponent* FarConifers[3] = {
            AddHism(FarDressing, FarRoot, TEXT("FarConiferA"), PineMeshes[0],
                nullptr, 360000, 600000, ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/false),
            AddHism(FarDressing, FarRoot, TEXT("FarConiferB"), PineMeshes[1],
                nullptr, 300000, 520000, ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/false),
            AddHism(FarDressing, FarRoot, TEXT("FarConiferC"), PineMeshes[2],
                nullptr, 300000, 520000, ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/false)};
        // The project-owned radial cards are appropriate once a crown is a
        // a few pixels high, but their intersecting planes are conspicuous on
        // the first canyon walls where a mature tree still projects at
        // double-digit pixel height. Reuse
        // the same rights-reviewed 3D pine analogs already assigned to the
        // detailed corridor for the immediate, non-colliding far-field bank.
        // Placement below switches between these and the cards by measured
        // river distance, so no source-tree sample is duplicated.
        UHierarchicalInstancedStaticMeshComponent* NearBankConifers[3] = {
            AddHism(FarDressing, FarRoot, TEXT("NearBankConiferA"),
                DetailedPineMeshes[0], nullptr, 300000, 520000,
                ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/true),
            AddHism(FarDressing, FarRoot, TEXT("NearBankConiferB"),
                DetailedPineMeshes[1], nullptr, 300000, 520000,
                ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/true),
            AddHism(FarDressing, FarRoot, TEXT("NearBankConiferC"),
                DetailedPineMeshes[2], nullptr, 300000, 520000,
                ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/true)};
        UHierarchicalInstancedStaticMeshComponent* FarBroadleaves[1] = {
            AddHism(FarDressing, FarRoot, TEXT("FarBroadleafCard"), FarBroadleafMesh,
                nullptr, 320000, 540000, ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/false)};
        UHierarchicalInstancedStaticMeshComponent* FarUnderstory = AddHism(
            FarDressing, FarRoot, TEXT("FarDryBankUnderstory"), ShrubMesh,
            nullptr, 80000, 240000, ECollisionEnabled::NoCollision,
            /*bEnableDensityScaling=*/true, /*bCastShadow=*/false);
        UHierarchicalInstancedStaticMeshComponent* FarScenicRocks[6] = {};
        for (int32 RockIndex = 0; RockIndex < 6; ++RockIndex)
        {
            FarScenicRocks[RockIndex] = AddHism(
                FarDressing, FarRoot,
                *FString::Printf(TEXT("FarScenicBankRock%02d"), RockIndex + 1),
                RockMeshes[RockIndex], ReviewedRockMaterial,
                120000, 360000, ECollisionEnabled::NoCollision,
                /*bEnableDensityScaling=*/true, /*bCastShadow=*/true);
        }
        // The stitched path uses a 20 m global grid. Keep foliage on a 40 m
        // candidate lattice regardless of streaming-tile width: width-based
        // selection made these smaller tiles four times denser than the
        // accepted population and nearly doubled total HISM count. The macro
        // terrain already carries intervening canopy colour and shadows.
        const int32 FarFoliageStride = 2;
        const double FarCellWidthM = FarFoliageStride *
            (MaximumX - MinimumX) / FMath::Max(Width - 1, 1);
        const double FarCellHeightM = FarFoliageStride *
            (MaximumY - MinimumY) / FMath::Max(Height - 1, 1);
        for (int32 Row = FarFoliageStride;
             Row < Height - FarFoliageStride;
             Row += FarFoliageStride)
        {
            const double RowT = static_cast<double>(Row) / FMath::Max(Height - 1, 1);
            const double WorldY = FMath::Lerp(MaximumY, MinimumY, RowT);
            for (int32 Column = FarFoliageStride;
                 Column < Width - FarFoliageStride;
                 Column += FarFoliageStride)
            {
                const int32 Index = Row * Width + Column;
                if (MaskImage.Pixels[Index].R <= 0.5f ||
                    OwnershipImage.Pixels[Index].R <= 0.5f)
                {
                    continue;
                }
                const double ColumnT =
                    static_cast<double>(Column) / FMath::Max(Width - 1, 1);
                const double GridWorldX =
                    FMath::Lerp(MinimumX, MaximumX, ColumnT);
                const FLinearColor Color = SampleMacroAtUv(ColumnT, RowT);
                const float Greenness = Color.G - 0.5f * (Color.R + Color.B);
                const float Probability = FMath::Clamp(
                    0.36f + Greenness * 1.6f, 0.12f, 0.86f);
                const float FarFoliagePatchNoise = 0.5f + 0.5f *
                    FMath::PerlinNoise2D(
                        FVector2D(
                            static_cast<float>(GridWorldX),
                            static_cast<float>(WorldY)) /
                            420.0f +
                        FVector2D(
                            static_cast<float>(PatchOrdinal) * 7.13f,
                            static_cast<float>(PatchOrdinal) * -5.71f));
                const float ClusteredProbability = FMath::Clamp(
                    Probability * FMath::Lerp(0.42f, 1.58f, FarFoliagePatchNoise),
                    0.04f, 0.94f);
                // The aerial macro represents broad land cover but cannot
                // supply guide-eye parallax. Add a sparse, deterministic layer
                // of low dry-bank understory and non-colliding stones on the
                // same world-space lattice. Their short cull ranges keep them
                // out of the distant macro and break up only otherwise-bare
                // immediate canyon walls.
                const double GroundJitterX = FMath::Lerp(
                    -0.38 * FarCellWidthM, 0.38 * FarCellWidthM,
                    StableUnitRandom(Row, Column, PatchOrdinal + 131));
                const double GroundJitterY = FMath::Lerp(
                    -0.38 * FarCellHeightM, 0.38 * FarCellHeightM,
                    StableUnitRandom(Row, Column, PatchOrdinal + 137));
                const double GroundWorldX = GridWorldX + GroundJitterX;
                const double GroundWorldY = WorldY + GroundJitterY;
                const float CenterElevationM = SourceElevationsM[Index];
                const float ElevationLeftM =
                    SourceElevationsM[Index - FarFoliageStride];
                const float ElevationRightM =
                    SourceElevationsM[Index + FarFoliageStride];
                const float ElevationNorthM =
                    SourceElevationsM[Index - Width * FarFoliageStride];
                const float ElevationSouthM =
                    SourceElevationsM[Index + Width * FarFoliageStride];
                const double CenterGradientX =
                    (ElevationRightM - ElevationLeftM) /
                    FMath::Max(2.0 * FarCellWidthM, 0.01);
                const double CenterGradientY =
                    (ElevationNorthM - ElevationSouthM) /
                    FMath::Max(2.0 * FarCellHeightM, 0.01);
                const float CenterSourceSlope = FMath::Sqrt(
                    static_cast<float>(
                        CenterGradientX * CenterGradientX +
                        CenterGradientY * CenterGradientY));
                const float GroundElevationM = CenterElevationM +
                    static_cast<float>(
                        CenterGradientX * GroundJitterX +
                        CenterGradientY * GroundJitterY) +
                    ComputeSouthForkFarFieldCorridorReliefWeight(
                        MaskImage, Row, Column) *
                        ComputeSouthForkInferredFarFieldReliefM(
                            GroundWorldX, GroundWorldY, CenterSourceSlope);
                const float GroundRiverDistanceM =
                    RiverDistanceImage.Values[Index] * 0.1f;
                if (GroundRiverDistanceM >= FarFieldRiverExclusionM)
                {
                    float NearBankAlpha = FMath::Clamp(
                        (320.0f - GroundRiverDistanceM) /
                            (320.0f - FarFieldRiverExclusionM),
                        0.0f, 1.0f);
                    NearBankAlpha = NearBankAlpha * NearBankAlpha *
                        (3.0f - 2.0f * NearBankAlpha);
                    const float UnderstoryProbability = FMath::Clamp(
                        0.055f - Greenness * 0.22f +
                            NearBankAlpha * 0.30f,
                        0.03f, 0.40f);
                    if (FarUnderstory && CenterSourceSlope <= 0.38f && StableUnitRandom(
                            PatchOrdinal * 911 + Row, Column, 139) <
                        UnderstoryProbability)
                    {
                        const float Scale = FMath::Lerp(
                            0.42f, 1.05f,
                            StableUnitRandom(Row, Column, PatchOrdinal + 149));
                        FarUnderstory->AddInstance(
                            FTransform(
                                FRotator(
                                    0.0f,
                                    StableUnitRandom(
                                        Row, Column, PatchOrdinal + 151) * 360.0f,
                                    0.0f),
                                FVector(
                                    GroundWorldX * 100.0,
                                    GroundWorldY * 100.0,
                                    (GroundElevationM - VerticalDatumM) * 100.0f -
                                        Scale * 24.0f),
                                FVector(
                                    Scale * FMath::Lerp(
                                        0.78f, 1.24f,
                                        StableUnitRandom(
                                            Row, Column, PatchOrdinal + 157)),
                                    Scale,
                                    Scale * FMath::Lerp(
                                        0.72f, 1.18f,
                                        StableUnitRandom(
                                            Row, Column, PatchOrdinal + 163)))),
                            /*bWorldSpace=*/true);
                        ++Metrics.FarFieldFoliageInstanceCount;
                    }
                    const float ScenicRockProbability = FMath::Clamp(
                        0.014f + CenterSourceSlope * 0.08f -
                            Greenness * 0.03f + NearBankAlpha * 0.22f,
                        0.01f, 0.34f);
                    if (StableUnitRandom(
                            PatchOrdinal * 919 + Row, Column, 167) <
                        ScenicRockProbability)
                    {
                        const int32 RockIndex =
                            FMath::Abs(PatchOrdinal * 17 + Row * 5 + Column) % 6;
                        if (FarScenicRocks[RockIndex])
                        {
                            const float RockScale = FMath::Lerp(
                                0.28f,
                                FMath::Lerp(0.76f, 1.70f, NearBankAlpha),
                                StableUnitRandom(
                                    Row, Column, PatchOrdinal + 173));
                            FarScenicRocks[RockIndex]->AddInstance(
                                FTransform(
                                    FRotator(
                                        StableUnitRandom(
                                            Row, Column, PatchOrdinal + 179) * 18.0f - 9.0f,
                                        StableUnitRandom(
                                            Row, Column, PatchOrdinal + 181) * 360.0f,
                                        StableUnitRandom(
                                            Row, Column, PatchOrdinal + 191) * 14.0f - 7.0f),
                                    FVector(
                                        GroundWorldX * 100.0,
                                        GroundWorldY * 100.0,
                                        (GroundElevationM - VerticalDatumM) * 100.0f +
                                            RockScale * 64.0f),
                                    FVector(RockScale)),
                                /*bWorldSpace=*/true);
                            ++Metrics.ScenicRockInstanceCount;
                        }
                    }
                }
                // Two half-probability candidates preserve the expected V13
                // population while allowing deterministic gaps and pairs.
                // The previous one-candidate rule approached one tree per
                // raster cell in dense source cover and exposed the sampling
                // lattice as a plantation on distant hills.
                for (int32 FoliageCandidate = 0; FoliageCandidate < 2;
                     ++FoliageCandidate)
                {
                    const int32 CandidateColumn = Column + FoliageCandidate * 4093;
                    if (StableUnitRandom(
                            PatchOrdinal * 997 + Row, CandidateColumn, 71) >
                        ClusteredProbability * 0.5f)
                    {
                        continue;
                    }
                    const double JitterX = FMath::Lerp(
                        -0.46 * FarCellWidthM, 0.46 * FarCellWidthM,
                        StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 73));
                    const double JitterY = FMath::Lerp(
                        -0.46 * FarCellHeightM, 0.46 * FarCellHeightM,
                        StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 79));
                    const double WorldX = GridWorldX + JitterX;
                    const double JitteredWorldY = WorldY + JitterY;
                    const float TreeRiverDistanceM =
                        RiverDistanceImage.Values[Index] * 0.1f;
                    if (TreeRiverDistanceM < FarFieldRiverExclusionM)
                    {
                        continue;
                    }
                    const double GradientX =
                        (ElevationRightM - ElevationLeftM) /
                        FMath::Max(2.0 * FarCellWidthM, 0.01);
                    // Raster rows progress from maximum Y toward minimum Y.
                    const double GradientY =
                        (ElevationNorthM - ElevationSouthM) /
                        FMath::Max(2.0 * FarCellHeightM, 0.01);
                    const float BaseElevationM = CenterElevationM +
                        static_cast<float>(GradientX * JitterX + GradientY * JitterY);
                    const float SourceSlope = FMath::Sqrt(
                        static_cast<float>(GradientX * GradientX + GradientY * GradientY));
                    // The shared-grid generator emits route distance at every
                    // far-field vertex. Sampling the same candidate vertex is
                    // deterministic across tile seams and avoids the old
                    // authoring-only bucket query, whose +/-3-bucket search
                    // silently returned infinity beyond roughly 500 m.
                    const float ElevationM = BaseElevationM +
                        ComputeSouthForkFarFieldCorridorReliefWeight(
                            MaskImage, Row, Column) *
                            ComputeSouthForkInferredFarFieldReliefM(
                                WorldX, JitteredWorldY, SourceSlope);
                    const bool bChooseConifer = Greenness > 0.025f;
                    const float VariantSelection =
                        StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 97);
                    int32 VariantIndex = 0;
                    UHierarchicalInstancedStaticMeshComponent* Target = nullptr;
                    bool bUsesDetailedPineAnalog = false;
                    if (bChooseConifer)
                    {
                        // Balance mature, intermediate, and younger Ponderosa
                        // age/profile classes while retaining a mature-tree
                        // plurality. All three are project-owned radial-card
                        // meshes derived from independent sources.
                        VariantIndex = VariantSelection < 0.44f
                            ? 0
                            : (VariantSelection < 0.74f ? 1 : 2);
                        Target = FarConifers[VariantIndex];
                    }
                    else
                    {
                        // Tree Small 02 remains useful import-pipeline evidence,
                        // but its human review explicitly rejected its pale,
                        // sparse canopy and regular repetition for production.
                        // Keep all broadleaves on the source-backed live-oak
                        // volume and vary the crown profile per instance below.
                        Target = FarBroadleaves[0];
                    }
                    if (bChooseConifer &&
                        TreeRiverDistanceM <= DetailedPineAnalogRiverDistanceM &&
                        NearBankConifers[VariantIndex])
                    {
                        Target = NearBankConifers[VariantIndex];
                        bUsesDetailedPineAnalog = true;
                    }
                    if (!Target)
                    {
                        continue;
                    }
                    const float Yaw = StableUnitRandom(
                        Row, CandidateColumn, PatchOrdinal + 83) * 360.0f;
                    float MinimumScale = 0.74f;
                    float MaximumScale = 1.38f;
                    if (bChooseConifer)
                    {
                        if (VariantIndex == 0)
                        {
                            MinimumScale = 0.78f;
                            MaximumScale = 1.34f;
                        }
                        else if (VariantIndex == 1)
                        {
                            MinimumScale = 0.68f;
                            MaximumScale = 1.18f;
                        }
                        else
                        {
                            MinimumScale = 0.58f;
                            MaximumScale = 1.04f;
                        }
                    }
                    const float Scale = FMath::Lerp(
                        MinimumScale, MaximumScale,
                        StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 89));
                    FVector CrownProfileScale = FVector::OneVector;
                    if (bChooseConifer)
                    {
                        if (VariantIndex == 0)
                        {
                            CrownProfileScale = FVector(0.94f, 1.04f, 1.08f);
                        }
                        else if (VariantIndex == 1)
                        {
                            CrownProfileScale = FVector(1.05f, 0.96f, 1.00f);
                        }
                        else
                        {
                            CrownProfileScale = FVector(1.10f, 1.02f, 0.92f);
                        }
                    }
                    else
                    {
                        const float CrownProfile = StableUnitRandom(
                            Row, CandidateColumn, PatchOrdinal + 127);
                        if (CrownProfile < 0.333333f)
                        {
                            CrownProfileScale = FVector(1.14f, 0.94f, 0.88f);
                        }
                        else if (CrownProfile < 0.666667f)
                        {
                            CrownProfileScale = FVector(0.92f, 1.10f, 0.93f);
                        }
                        else
                        {
                            CrownProfileScale = FVector(0.86f, 0.92f, 1.13f);
                        }
                    }
                    const FVector InstanceScale(
                        Scale * FMath::Lerp(
                            0.82f, 1.18f,
                            StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 101)) *
                            CrownProfileScale.X,
                        Scale * FMath::Lerp(
                            0.84f, 1.16f,
                            StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 103)) *
                            CrownProfileScale.Y,
                        Scale * FMath::Lerp(
                            0.88f, 1.16f,
                            StableUnitRandom(Row, CandidateColumn, PatchOrdinal + 107)) *
                            CrownProfileScale.Z);
                    const float LeanDegrees = bChooseConifer ? 2.5f : 4.0f;
                    Target->AddInstance(
                        FTransform(
                            FRotator(
                                FMath::Lerp(
                                    -LeanDegrees, LeanDegrees,
                                    StableUnitRandom(
                                        Row, CandidateColumn, PatchOrdinal + 109)),
                                Yaw,
                                FMath::Lerp(
                                    -LeanDegrees, LeanDegrees,
                                    StableUnitRandom(
                                        Row, CandidateColumn, PatchOrdinal + 113))),
                            FVector(
                                WorldX * 100.0, JitteredWorldY * 100.0,
                                (ElevationM - VerticalDatumM) * 100.0f),
                            InstanceScale),
                        /*bWorldSpace=*/true);
                    if (bChooseConifer)
                    {
                        if (bUsesDetailedPineAnalog)
                        {
                            ++Metrics.FarFieldDetailedPineInstanceCount;
                        }
                        else
                        {
                            ++Metrics.FarFieldPineCardInstanceCount;
                        }
                    }
                    ++Metrics.FarFieldFoliageInstanceCount;
                }
            }
        }
    }

    // Runtime configuration and the playable start are stationed on the same
    // curved map as terrain, water, captures, and physics.
    constexpr float StartStationM = 120.0f;
    const int32 StartIndex = ClosestCoordinateIndex(CoordinatePoints, StartStationM);
    const FVector2D StartWorldM = CoordinateWorldM(CoordinatePoints[StartIndex], 0.0f);
    const FVector StartTangent = CoordinateTangent(CoordinatePoints, StartIndex);
    const float StartWaterZCm = Metrics.MedianCenterWaterLocalZCm[StartIndex] > -BIG_NUMBER * 0.5f
        ? Metrics.MedianCenterWaterLocalZCm[StartIndex]
        : 52000.0f;
    ARaftSimRiverWaterConfig* WaterConfig =
        SpawnStableSouthForkActor<ARaftSimRiverWaterConfig>(
            World, FTransform::Identity,
            TEXT("RaftSim_SouthFork_FullReachWaterConfig"));
    if (!WaterConfig)
    {
        return false;
    }
    WaterConfig->SetActorLabel(TEXT("RaftSim_SouthFork_FullReachWaterConfig"));
    WaterConfig->CookedFieldsDir =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/"
             "full_reach_transit_seed");
    WaterConfig->FlowBand = TEXT("median_runnable");
    WaterConfig->WindowCenterM = FVector2D(StartStationM, 0.0f);
    WaterConfig->CoordinateMapPath = CoordinateMapPath;
    WaterConfig->StreamingManifestPath =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/"
             "full_hydraulics/streaming_manifest.json");
    WaterConfig->bEnableMovingWindowStreaming = true;
    WaterConfig->MovingWindowStationExtentM = 320.0f;
    WaterConfig->MovingWindowLateralExtentM = 80.0f;
    WaterConfig->MovingWindowAdvanceM = 80.0f;
    WaterConfig->bMapProvidesTerrain = true;
    SetSpatiallyLoadedIfAllowed(WaterConfig, false);

    const FRotator StartRotation = StartTangent.Rotation();
    ARaftSimRaftActor* Raft = SpawnStableSouthForkActor<ARaftSimRaftActor>(
        World,
        FTransform(
            StartRotation,
            FVector(
                StartWorldM.X * 100.0f,
                StartWorldM.Y * 100.0f,
                StartWaterZCm + 58.0f)),
        TEXT("RaftSim_SouthFork_PlayerRaft"));
    if (Raft)
    {
        Raft->SetActorLabel(TEXT("RaftSim_SouthFork_PlayerRaft"));
        SetSpatiallyLoadedIfAllowed(Raft, false);
    }
    APlayerStart* PlayerStart = SpawnStableSouthForkActor<APlayerStart>(
        World,
        FTransform(
            StartRotation,
            FVector(
                (StartWorldM.X - StartTangent.X * 4.0f) * 100.0f,
                (StartWorldM.Y - StartTangent.Y * 4.0f) * 100.0f,
                StartWaterZCm + 170.0f)),
        TEXT("RaftSim_SouthFork_PlayerStart"));
    if (PlayerStart)
    {
        PlayerStart->SetActorLabel(TEXT("RaftSim_SouthFork_PlayerStart"));
        SetSpatiallyLoadedIfAllowed(PlayerStart, false);
    }

    // Finished procedural access context. The bridge and landings are tagged
    // as game-context infill and never presented as real navigation guidance.
    UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* Timber = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber"));
    UMaterialInterface* Steel = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel."
             "M_RaftSim_GalvanizedSteel"));
    UMaterialInterface* Asphalt = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Asphalt.M_RaftSim_Asphalt"));
    UMaterialInterface* Concrete = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_WeatheredConcrete."
             "M_RaftSim_WeatheredConcrete"));
    auto AddInfrastructureCube = [&](const FString& Label, const FVector& Location,
                                     const FRotator& Rotation, const FVector& Scale,
                                     UMaterialInterface* Material)
    {
        AStaticMeshActor* Actor = PlaceSouthForkStaticMeshActor(
            World, CubeMesh, Material, Label,
            FTransform(Rotation, Location, Scale),
            TEXT("RaftSimProceduralInfrastructureNotForNavigation"),
            ECollisionEnabled::QueryAndPhysics);
        if (Actor)
        {
            ++Metrics.InfrastructureActorCount;
        }
        return Actor;
    };
    auto AddInfrastructureBeam = [&](const FString& Label, const FVector& Start,
                                     const FVector& End, float ThicknessCm,
                                     UMaterialInterface* Material)
    {
        const FVector Delta = End - Start;
        const float LengthCm = Delta.Size();
        if (LengthCm < 1.0f)
        {
            return static_cast<AStaticMeshActor*>(nullptr);
        }
        return AddInfrastructureCube(
            Label, (Start + End) * 0.5f, Delta.Rotation(),
            FVector(LengthCm / 100.0f, ThicknessCm / 100.0f,
                    ThicknessCm / 100.0f),
            Material);
    };
    const int32 BridgeIndex = ClosestCoordinateIndex(CoordinatePoints, 5200.0);
    const FVector BridgeTangent = CoordinateTangent(CoordinatePoints, BridgeIndex);
    const FVector2D BridgeWorldM = CoordinateWorldM(CoordinatePoints[BridgeIndex], 0.0f);
    const float BridgeWaterZCm = Metrics.MedianCenterWaterLocalZCm[BridgeIndex];
    const FVector BridgeCenter(
        BridgeWorldM.X * 100.0f, BridgeWorldM.Y * 100.0f, BridgeWaterZCm + 560.0f);
    const FVector BridgeNormal(
        CoordinatePoints[BridgeIndex].LeftNormal.X,
        CoordinatePoints[BridgeIndex].LeftNormal.Y, 0.0f);
    const FRotator BridgeRotation = BridgeNormal.Rotation();
    AddInfrastructureCube(
        TEXT("RaftSim_ColomaContextBridge_Deck_Procedural"), BridgeCenter,
        BridgeRotation, FVector(74.0f, 4.8f, 0.55f), Timber);
    for (float Side : {-1.0f, 1.0f})
    {
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_UpperRail_%d"), Side > 0 ? 1 : 0),
            BridgeCenter + BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 190.0f),
            BridgeRotation, FVector(74.0f, 0.12f, 0.14f), Steel);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_LowerRail_%d"), Side > 0 ? 1 : 0),
            BridgeCenter + BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 72.0f),
            BridgeRotation, FVector(74.0f, 0.10f, 0.10f), Steel);

        // A deterministic through-truss silhouette gives the procedural
        // crossing believable structure at guide-eye distance. It is context
        // infill only; labels and tags continue to prohibit navigational use.
        constexpr float HalfSpanCm = 3500.0f;
        constexpr float BayCm = 500.0f;
        for (int32 Bay = 0; Bay <= 14; ++Bay)
        {
            const float AlongCm = -HalfSpanCm + Bay * BayCm;
            const FVector PostCenter =
                BridgeCenter + BridgeNormal * AlongCm +
                BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 128.0f);
            AddInfrastructureCube(
                FString::Printf(
                    TEXT("RaftSim_ColomaBridge_TrussPost_%d_%02d"),
                    Side > 0 ? 1 : 0, Bay),
                PostCenter, BridgeRotation, FVector(0.09f, 0.09f, 1.28f), Steel);
            if (Bay < 14)
            {
                const bool bRises = (Bay % 2) == 0;
                const FVector BayStart =
                    BridgeCenter + BridgeNormal * AlongCm +
                    BridgeTangent * Side * 225.0f +
                    FVector(0.0f, 0.0f, bRises ? 48.0f : 202.0f);
                const FVector BayEnd =
                    BridgeCenter + BridgeNormal * (AlongCm + BayCm) +
                    BridgeTangent * Side * 225.0f +
                    FVector(0.0f, 0.0f, bRises ? 202.0f : 48.0f);
                AddInfrastructureBeam(
                    FString::Printf(
                        TEXT("RaftSim_ColomaBridge_TrussDiagonal_%d_%02d"),
                        Side > 0 ? 1 : 0, Bay),
                    BayStart, BayEnd, 12.0f, Steel);
            }
        }
    }
    for (float Lateral : {-24.0f, 0.0f, 24.0f})
    {
        const FVector2D PierWorldM = CoordinateWorldM(
            CoordinatePoints[BridgeIndex], Lateral);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_Pier_%d"),
                FMath::RoundToInt(Lateral)),
            FVector(PierWorldM.X * 100.0f, PierWorldM.Y * 100.0f,
                BridgeWaterZCm + 250.0f),
            BridgeRotation, FVector(1.7f, 1.7f, 5.0f),
            Concrete ? Concrete : Steel);
    }
    struct FAccessSite
    {
        const TCHAR* Label;
        float StationM;
        float LateralM;
    };
    const FAccessSite AccessSites[] = {
        {TEXT("ChiliBarPutIn"), 0.0f, 58.0f},
        {TEXT("ColomaAccess"), 5200.0f, -62.0f},
        {TEXT("SalmonFallsTakeout"), 49077.732f, 54.0f}};
    for (const FAccessSite& Site : AccessSites)
    {
        const int32 SiteIndex = ClosestCoordinateIndex(CoordinatePoints, Site.StationM);
        const FVector SiteTangent = CoordinateTangent(CoordinatePoints, SiteIndex);
        const FVector2D SiteWorldM = CoordinateWorldM(
            CoordinatePoints[SiteIndex], Site.LateralM);
        const float SiteZCm = Metrics.MedianCenterWaterLocalZCm[SiteIndex] > -BIG_NUMBER * 0.5f
            ? Metrics.MedianCenterWaterLocalZCm[SiteIndex] + 130.0f
            : 500.0f;
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_%s_GravelRamp_Procedural"), Site.Label),
            FVector(SiteWorldM.X * 100.0f, SiteWorldM.Y * 100.0f, SiteZCm),
            SiteTangent.Rotation(), FVector(22.0f, 7.0f, 0.28f), Asphalt);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_%s_SignPost_NotForNavigation"), Site.Label),
            FVector(
                (SiteWorldM.X + CoordinatePoints[SiteIndex].LeftNormal.X * 5.0f) * 100.0f,
                (SiteWorldM.Y + CoordinatePoints[SiteIndex].LeftNormal.Y * 5.0f) * 100.0f,
                SiteZCm + 160.0f),
            SiteTangent.Rotation(), FVector(0.14f, 0.14f, 3.2f), Timber);
    }

    // Single Layer Water normally receives the canyon through the temporal
    // reflection history of the player's view. Deterministic captures and a
    // freshly loaded packaged map do not have that history yet, so a bare
    // skylight makes calm reaches read as a flat blue-gray card. Cover the
    // 49 km reach with overlapping, static local probes whose cubemaps are
    // baked after all source-backed and procedural environment actors exist.
    // These affect reflected radiance only; solver water vertices, collision,
    // flow fields, and gameplay forces remain unchanged.
    constexpr int32 ReflectionProbeCount = 13;
    const float LastStationM = CoordinatePoints.Last().StationM;
    for (int32 ProbeIndex = 0; ProbeIndex < ReflectionProbeCount; ++ProbeIndex)
    {
        const float ProbeStationM = LastStationM *
            (static_cast<float>(ProbeIndex) + 0.5f) /
            static_cast<float>(ReflectionProbeCount);
        const int32 CoordinateIndex = ClosestCoordinateIndex(
            CoordinatePoints, ProbeStationM);
        const FVector2D ProbeWorldM = CoordinateWorldM(
            CoordinatePoints[CoordinateIndex], 0.0f);
        const float ProbeWaterZCm =
            Metrics.MedianCenterWaterLocalZCm[CoordinateIndex] > -BIG_NUMBER * 0.5f
            ? Metrics.MedianCenterWaterLocalZCm[CoordinateIndex]
            : 500.0f;
        const FString ProbeLabel = FString::Printf(
            TEXT("RaftSim_SouthFork_ReflectionProbe_%02d"), ProbeIndex + 1);
        ASphereReflectionCapture* Probe =
            SpawnStableSouthForkActor<ASphereReflectionCapture>(
                World,
                FTransform(FVector(
                    ProbeWorldM.X * 100.0f,
                    ProbeWorldM.Y * 100.0f,
                    ProbeWaterZCm + 180.0f)),
                ProbeLabel);
        USphereReflectionCaptureComponent* ProbeComponent = Probe
            ? Cast<USphereReflectionCaptureComponent>(Probe->GetCaptureComponent())
            : nullptr;
        if (!Probe || !ProbeComponent)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create river reflection probe %d.\n"),
                ProbeIndex + 1);
            return false;
        }
        Probe->SetActorLabel(ProbeLabel);
        ProbeComponent->InfluenceRadius = 230000.0f;
        ProbeComponent->Brightness = 0.92f;
        ProbeComponent->MarkDirtyForRecapture();
        SetSpatiallyLoadedIfAllowed(Probe, false);
        ++Metrics.ReflectionProbeCount;
    }
    UReflectionCaptureComponent::UpdateReflectionCaptureContents(
        World, TEXT("RaftSim South Fork full-reach environment build"));
    FlushRenderingCommands();
    OutSummary += FString::Printf(
        TEXT("Captured %d overlapping South Fork local reflection probes.\n"),
        Metrics.ReflectionProbeCount);

    if (!ValidateStableSouthForkActorIdentities(World, Metrics, OutSummary))
    {
        OutSummary += TEXT("Failed to assign stable full-reach actor identities.\n");
        return false;
    }

    if (!SaveFullReachWorld(World))
    {
        OutSummary += TEXT("Failed to save the full-reach gameplay map.\n");
        return false;
    }

    // A capture-only isolation switch makes visual regressions attributable
    // without changing the saved gameplay map. It is intentionally omitted
    // from normal builds and only hides far-field actors after the map save.
    const bool bDiagnosticHideFarField = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkFarField"));
    const bool bDiagnosticHideWater = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkWater"));
    const bool bDiagnosticHideDetailedDressing = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkDetailedDressing"));
    const bool bDiagnosticHideDetailedRocks = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkDetailedRocks"));
    int32 DiagnosticHideDetailedRockVariant = 0;
    FParse::Value(
        FCommandLine::Get(),
        TEXT("RaftSimDiagnosticHideSouthForkDetailedRockVariant="),
        DiagnosticHideDetailedRockVariant);
    TArray<TWeakObjectPtr<AActor>> DiagnosticHiddenActors;
    TArray<TWeakObjectPtr<UHierarchicalInstancedStaticMeshComponent>>
        DiagnosticHiddenComponents;
    if (bDiagnosticHideFarField || bDiagnosticHideWater ||
        bDiagnosticHideDetailedDressing || bDiagnosticHideDetailedRocks ||
        DiagnosticHideDetailedRockVariant > 0)
    {
        const FName FarFieldTag(TEXT("RaftSimFullReachFarField"));
        const FName FarFieldDressingTag(TEXT("RaftSimFullReachFarFieldDressing"));
        const FName DetailedDressingTag(TEXT("RaftSimFullReachDressing"));
        const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            const bool bHideActor = Actor && (
                (bDiagnosticHideFarField &&
                    (Actor->ActorHasTag(FarFieldTag) ||
                     Actor->ActorHasTag(FarFieldDressingTag))) ||
                (bDiagnosticHideWater && Actor->ActorHasTag(MedianWaterTag)) ||
                (bDiagnosticHideDetailedDressing &&
                    Actor->ActorHasTag(DetailedDressingTag)));
            if (bHideActor)
            {
                Actor->SetActorHiddenInGame(true);
                DiagnosticHiddenActors.Add(Actor);
            }
            if (Actor &&
                (bDiagnosticHideDetailedRocks ||
                 DiagnosticHideDetailedRockVariant > 0) &&
                Actor->ActorHasTag(DetailedDressingTag))
            {
                TInlineComponentArray<UHierarchicalInstancedStaticMeshComponent*>
                    Components(Actor);
                for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
                {
                    const FString Name = Component ? Component->GetName() : FString();
                    const bool bIsRock =
                        Name.StartsWith(TEXT("Boulder")) ||
                        Name.StartsWith(TEXT("ScenicBankRock"));
                    const FString VariantSuffix = FString::Printf(
                        TEXT("%02d"), DiagnosticHideDetailedRockVariant);
                    const bool bMatchesVariant =
                        DiagnosticHideDetailedRockVariant > 0 &&
                        Name.EndsWith(VariantSuffix);
                    if (Component && bIsRock &&
                        (bDiagnosticHideDetailedRocks || bMatchesVariant))
                    {
                        Component->SetVisibility(false, true);
                        DiagnosticHiddenComponents.Add(Component);
                    }
                }
            }
        }
        OutSummary += FString::Printf(
            TEXT("Capture diagnostic hid %d actors and %d components after map save (far field %s, water %s, detailed dressing %s, detailed rocks %s, rock variant %d).\n"),
            DiagnosticHiddenActors.Num(),
            DiagnosticHiddenComponents.Num(),
            bDiagnosticHideFarField ? TEXT("yes") : TEXT("no"),
            bDiagnosticHideWater ? TEXT("yes") : TEXT("no"),
            bDiagnosticHideDetailedDressing ? TEXT("yes") : TEXT("no"),
            bDiagnosticHideDetailedRocks ? TEXT("yes") : TEXT("no"),
            DiagnosticHideDetailedRockVariant);
    }

    const struct FCaptureSpec
    {
        const TCHAR* Id;
        float StationM;
        float LateralM;
        float HeightM;
        bool bLookUpstream;
    } CaptureSpecs[] = {
        {TEXT("chili_bar_launch_downstream"), 120.0f, -4.0f, 2.4f, false},
        {TEXT("meat_grinder_guide_eye"), 944.0f, 1.0f, 2.0f, false},
        {TEXT("troublemaker_approach"), 8328.0f, -2.0f, 2.2f, false},
        {TEXT("coloma_bridge_context"), 5100.0f, 8.0f, 3.0f, false},
        {TEXT("salmon_falls_takeout"), 48940.0f, 2.0f, 2.5f, true}};
    TArray<FString> CapturePaths;
    bool bAllCapturesSaved = true;
    for (const FCaptureSpec& Spec : CaptureSpecs)
    {
        const int32 Index = ClosestCoordinateIndex(CoordinatePoints, Spec.StationM);
        const FVector2D WorldM = CoordinateWorldM(CoordinatePoints[Index], Spec.LateralM);
        const FVector Tangent = CoordinateTangent(CoordinatePoints, Index);
        const FVector CaptureTangent = Spec.bLookUpstream ? -Tangent : Tangent;
        const float SurfaceZCm = Metrics.MedianCenterWaterLocalZCm[Index] > -BIG_NUMBER * 0.5f
            ? Metrics.MedianCenterWaterLocalZCm[Index]
            : 500.0f;
        OutSummary += FString::Printf(
            TEXT("Capture diagnostic %s: station %.1f m, coordinate row %d, "
                 "world XY (%.1f, %.1f) m, decoded surface %.3f m absolute "
                 "(local Z %.1f cm).\n"),
            Spec.Id, Spec.StationM, Index, WorldM.X, WorldM.Y,
            VerticalDatumM + SurfaceZCm / 100.0f, SurfaceZCm);
        FString CapturePath;
        bAllCapturesSaved &= CaptureSouthForkView(
            World, Spec.Id,
            FVector(WorldM.X * 100.0f, WorldM.Y * 100.0f,
                SurfaceZCm + Spec.HeightM * 100.0f),
            FRotator(-5.0f, CaptureTangent.Rotation().Yaw, 0.0f),
            CapturePath, OutSummary);
        CapturePaths.Add(CapturePath);
    }
    for (const TWeakObjectPtr<AActor>& Actor : DiagnosticHiddenActors)
    {
        if (Actor.IsValid())
        {
            Actor->SetActorHiddenInGame(false);
        }
    }
    for (const TWeakObjectPtr<UHierarchicalInstancedStaticMeshComponent>& Component :
         DiagnosticHiddenComponents)
    {
        if (Component.IsValid())
        {
            Component->SetVisibility(true, true);
        }
    }

    return WriteSouthForkFullReachBuildManifest(
        World, Metrics, bReuseExistingDetailedMeshes, bAllCapturesSaved,
        CapturePaths, OutSummary);
}

bool CaptureSettledSouthForkFullReachEnvironment(FString& OutSummary)
{
    TSharedPtr<FJsonObject> EnvironmentRoot;
    TArray<FSouthForkCoordinatePoint> CoordinatePoints;
    float VerticalDatumM = 0.0f;
    FString CoordinateMapPath;
    if (!LoadJsonObject(EnvironmentManifestRelativePath, EnvironmentRoot) ||
        !ParseCoordinateMap(
            EnvironmentRoot, CoordinatePoints, VerticalDatumM, CoordinateMapPath))
    {
        OutSummary += TEXT("Could not parse the fixed South Fork capture coordinates.\n");
        return false;
    }

    const FString MapFilename = FPackageName::LongPackageNameToFilename(
        FullReachMapPackagePath, FPackageName::GetMapPackageExtension());
    UWorld* World = UEditorLoadingAndSavingUtils::LoadMap(MapFilename);
    UWorldPartition* WorldPartition = World ? World->GetWorldPartition() : nullptr;
    if (!World || !WorldPartition || !WorldPartition->IsInitialized())
    {
        OutSummary += TEXT("Could not load the settled South Fork World Partition map.\n");
        return false;
    }

    // Keep hard references alive for the complete evidence set. This loads
    // the immutable saved map exactly once and avoids generator/package-order
    // changes between nominal capture repeats.
    TArray<FWorldPartitionReference> LoadedActorReferences;
    WorldPartition->LoadAllActors(LoadedActorReferences);
    FlushAsyncLoading();
    World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    TArray<TPair<TWeakObjectPtr<UPrimitiveComponent>, bool>> SourceCaptureVisibilityStates;
    ConfigureSouthForkSettledSourceCaptureVisibility(
        World, SourceCaptureVisibilityStates, OutSummary);
    TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>
        TerrainDetailV2ReviewMaterialStates;
    TArray<FSouthForkShoreRockReviewComponentState>
        PolyHavenShoreRockReviewStates;
    TArray<TWeakObjectPtr<AActor>> DerivedBankMorphologyReviewActors;
    if (!ConfigureSouthForkFullReachReviewLayers(
            World, TerrainDetailV2ReviewMaterialStates,
            PolyHavenShoreRockReviewStates,
            DerivedBankMorphologyReviewActors, OutSummary))
    {
        RestoreSouthForkSettledSourceCaptureVisibility(
            SourceCaptureVisibilityStates);
        return false;
    }
    // Review-only isolation switch: hide the broad Single Layer Water actors
    // while retaining the solver-foam actors. This never mutates the saved
    // map and makes placement/coverage failures distinguishable from
    // translucency-compositing failures in offscreen evidence captures.
    TArray<TWeakObjectPtr<AActor>> DiagnosticHiddenBaseWaterActors;
    TArray<TWeakObjectPtr<AActor>> DiagnosticHiddenFarFieldActors;
    TArray<TWeakObjectPtr<AActor>> DiagnosticHiddenBankMicroreliefActors;
    TArray<TPair<TWeakObjectPtr<UStaticMeshComponent>, TWeakObjectPtr<UMaterialInterface>>>
        DiagnosticOpaqueFoamMaterials;
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimDiagnosticHideSouthForkBankMicrorelief")))
    {
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
        {
            AStaticMeshActor* Actor = *It;
            if (Actor && Actor->ActorHasTag(
                    TEXT("RaftSimSouthForkDryBankMicroreliefV1")))
            {
                Actor->SetActorHiddenInGame(true);
                DiagnosticHiddenBankMicroreliefActors.Add(Actor);
            }
        }
        OutSummary += FString::Printf(
            TEXT("Settled-map diagnostic hid %d dry-bank microrelief actors.\n"),
            DiagnosticHiddenBankMicroreliefActors.Num());
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkFarField")))
    {
        const FName FarFieldTag(TEXT("RaftSimFullReachFarField"));
        const FName FarFieldDressingTag(TEXT("RaftSimFullReachFarFieldDressing"));
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor &&
                (Actor->ActorHasTag(FarFieldTag) ||
                 Actor->ActorHasTag(FarFieldDressingTag)))
            {
                Actor->SetActorHiddenInGame(true);
                DiagnosticHiddenFarFieldActors.Add(Actor);
            }
        }
        OutSummary += FString::Printf(
            TEXT("Settled-map diagnostic hid %d far-field actors.\n"),
            DiagnosticHiddenFarFieldActors.Num());
    }
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkBaseWater")))
    {
        const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
        const FName SolverFoamTag(TEXT("RaftSimSolverFoamOverlay"));
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
        {
            AStaticMeshActor* Actor = *It;
            if (Actor && Actor->ActorHasTag(MedianWaterTag) &&
                !Actor->ActorHasTag(SolverFoamTag))
            {
                Actor->SetActorHiddenInGame(true);
                DiagnosticHiddenBaseWaterActors.Add(Actor);
            }
        }
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
        {
            AStaticMeshActor* Actor = *It;
            if (!Actor || !Actor->ActorHasTag(MedianWaterTag) ||
                !Actor->ActorHasTag(SolverFoamTag))
            {
                continue;
            }
            UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
            UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
            UMaterialInterface* Material = Component ? Component->GetMaterial(0) : nullptr;
            if (Component && FParse::Param(
                    FCommandLine::Get(),
                    TEXT("RaftSimDiagnosticOpaqueSouthForkSolverFoam")))
            {
                DiagnosticOpaqueFoamMaterials.Emplace(Component, Material);
                Component->SetMaterial(0, UMaterial::GetDefaultMaterial(MD_Surface));
            }
            const FBoxSphereBounds Bounds = Component
                ? Component->Bounds
                : FBoxSphereBounds(EForceInit::ForceInit);
            UE_LOG(
                LogRaftSimEditorEnvironment,
                Display,
                TEXT("Solver-foam render audit %s: actor_hidden=%s component_visible=%s "
                     "mesh=%s material=%s bounds_origin=(%.1f,%.1f,%.1f) "
                     "bounds_extent=(%.1f,%.1f,%.1f)"),
                *Actor->GetActorLabel(),
                Actor->IsHidden() ? TEXT("true") : TEXT("false"),
                Component && Component->IsVisible() ? TEXT("true") : TEXT("false"),
                Mesh ? *Mesh->GetPathName() : TEXT("none"),
                Material ? *Material->GetPathName() : TEXT("none"),
                Bounds.Origin.X,
                Bounds.Origin.Y,
                Bounds.Origin.Z,
                Bounds.BoxExtent.X,
                Bounds.BoxExtent.Y,
                Bounds.BoxExtent.Z);
            LogStaticMeshVertexColorSummary(Actor->GetActorLabel(), Mesh);
        }
        OutSummary += FString::Printf(
            TEXT("Settled-map diagnostic hid %d base-water actors while retaining "
                 "solver-foam overlays.\n"),
            DiagnosticHiddenBaseWaterActors.Num());
    }

    const struct FCaptureSpec
    {
        const TCHAR* Id;
        float StationM;
        float LateralM;
        float HeightM;
        bool bLookUpstream;
    } CaptureSpecs[] = {
        {TEXT("chili_bar_launch_downstream"), 120.0f, -4.0f, 2.4f, false},
        {TEXT("meat_grinder_guide_eye"), 944.0f, 1.0f, 2.0f, false},
        {TEXT("troublemaker_approach"), 8328.0f, -2.0f, 2.2f, false},
        {TEXT("coloma_bridge_context"), 5100.0f, 8.0f, 3.0f, false},
        {TEXT("salmon_falls_takeout"), 48940.0f, 2.0f, 2.5f, true}};
    bool bAllCapturesSaved = true;
    for (const FCaptureSpec& Spec : CaptureSpecs)
    {
        const int32 Index = ClosestCoordinateIndex(CoordinatePoints, Spec.StationM);
        const FVector2D WorldM = CoordinateWorldM(CoordinatePoints[Index], Spec.LateralM);
        const FVector2D CenterlineWorldM = CoordinateWorldM(CoordinatePoints[Index], 0.0f);
        const FVector Tangent = CoordinateTangent(CoordinatePoints, Index);
        float SurfaceZCm = 0.0f;
        if (!FindSouthForkMedianWaterSurfaceLocalZCm(World, CenterlineWorldM, SurfaceZCm))
        {
            OutSummary += FString::Printf(
                TEXT("Could not resolve settled median water beneath capture %s.\n"),
                Spec.Id);
            for (const TWeakObjectPtr<AActor>& Actor :
                 DiagnosticHiddenBankMicroreliefActors)
            {
                if (Actor.IsValid())
                {
                    Actor->SetActorHiddenInGame(false);
                }
            }
            for (const TWeakObjectPtr<AActor>& Actor :
                 DiagnosticHiddenFarFieldActors)
            {
                if (Actor.IsValid())
                {
                    Actor->SetActorHiddenInGame(false);
                }
            }
            RestoreSouthForkSettledSourceCaptureVisibility(
                SourceCaptureVisibilityStates);
            RestoreSouthForkFullReachReviewLayers(
                TerrainDetailV2ReviewMaterialStates,
                PolyHavenShoreRockReviewStates,
                DerivedBankMorphologyReviewActors);
            return false;
        }
        const FVector CaptureTangent = Spec.bLookUpstream ? -Tangent : Tangent;
        FString CapturePath;
        bAllCapturesSaved &= CaptureSouthForkView(
            World, Spec.Id,
            FVector(
                WorldM.X * 100.0f, WorldM.Y * 100.0f,
                SurfaceZCm + Spec.HeightM * 100.0f),
            FRotator(-5.0f, CaptureTangent.Rotation().Yaw, 0.0f),
            CapturePath, OutSummary);
    }
    for (const TWeakObjectPtr<AActor>& Actor :
         DiagnosticHiddenBankMicroreliefActors)
    {
        if (Actor.IsValid())
        {
            Actor->SetActorHiddenInGame(false);
        }
    }
    for (const TWeakObjectPtr<AActor>& Actor : DiagnosticHiddenFarFieldActors)
    {
        if (Actor.IsValid())
        {
            Actor->SetActorHiddenInGame(false);
        }
    }
    for (const TWeakObjectPtr<AActor>& Actor : DiagnosticHiddenBaseWaterActors)
    {
        if (Actor.IsValid())
        {
            Actor->SetActorHiddenInGame(false);
        }
    }
    for (const TPair<TWeakObjectPtr<UStaticMeshComponent>,
                     TWeakObjectPtr<UMaterialInterface>>& Pair :
         DiagnosticOpaqueFoamMaterials)
    {
        if (Pair.Key.IsValid())
        {
            Pair.Key->SetMaterial(0, Pair.Value.Get());
        }
    }
    RestoreSouthForkSettledSourceCaptureVisibility(
        SourceCaptureVisibilityStates);
    RestoreSouthForkFullReachReviewLayers(
        TerrainDetailV2ReviewMaterialStates,
        PolyHavenShoreRockReviewStates,
        DerivedBankMorphologyReviewActors);
    OutSummary += FString::Printf(
        TEXT("Settled-map capture loaded %d World Partition actor references without regeneration.\n"),
        LoadedActorReferences.Num());
    return bAllCapturesSaved;
}

} // namespace RaftSimEditorEnvironment

bool FRaftSimEditorModule::CreateSouthForkFullReachEnvironment(FString& OutSummary)
{
    return RaftSimEditorEnvironment::BuildSouthForkFullReachEnvironment(OutSummary);
}
bool FRaftSimEditorModule::CaptureSouthForkFullReachEnvironment(FString& OutSummary)
{
    return RaftSimEditorEnvironment::CaptureSettledSouthForkFullReachEnvironment(OutSummary);
}
