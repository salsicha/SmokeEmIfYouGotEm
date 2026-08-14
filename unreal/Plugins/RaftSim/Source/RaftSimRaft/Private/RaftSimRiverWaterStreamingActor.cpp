#include "RaftSimRiverWaterStreamingActor.h"

#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

ARaftSimRiverWaterStreamingActor::ARaftSimRiverWaterStreamingActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.2f;
}

void ARaftSimRiverWaterStreamingActor::BeginPlay()
{
    Super::BeginPlay();
    TActorIterator<ARaftSimRiverWaterConfig> ConfigIt(GetWorld());
    if (ConfigIt)
    {
        RiverConfig = *ConfigIt;
    }
    TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
    if (RaftIt)
    {
        Raft = *RaftIt;
    }
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }
    if (!RiverConfig || !Raft || !WaterAdapter || !LoadStreamingManifest())
    {
        // Four preconditions, one silent early-out: this actor spent its
        // life impossible to distinguish from working (2026-08-10 audit).
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim river streaming disabled: config=%d raft=%d ")
            TEXT("water=%d manifest=%d"),
            RiverConfig != nullptr, Raft != nullptr, WaterAdapter != nullptr,
            RiverConfig != nullptr && Raft != nullptr && WaterAdapter != nullptr);
        SetActorTickEnabled(false);
        return;
    }
    CachedFlowBand = RiverConfig->FlowBand;
    CachedMovingWindowAdvanceM = RiverConfig->MovingWindowAdvanceM;
    CachedMovingWindowStationExtentM = RiverConfig->MovingWindowStationExtentM;
    CachedMovingWindowLateralExtentM = RiverConfig->MovingWindowLateralExtentM;
    ApplyStaticFlowBandVisibility();
    UpdateWaterWindow(/*bForce=*/true);
}

bool ARaftSimRiverWaterStreamingActor::LoadStreamingManifest()
{
    if (!RiverConfig || RiverConfig->StreamingManifestPath.IsEmpty())
    {
        return false;
    }
    const FString FullPath = URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        RiverConfig->StreamingManifestPath);
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *FullPath))
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim streaming manifest not found: %s"), *FullPath);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        return false;
    }
    FString Schema;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.south_fork.moving_water_streaming.v1"))
    {
        return false;
    }

    const TSharedPtr<FJsonObject>* Transit = nullptr;
    FString TransitManifestPath;
    if (!Root->TryGetObjectField(TEXT("full_reach_transit_seed"), Transit) ||
        Transit == nullptr || !(*Transit)->TryGetStringField(
            TEXT("cooked_fields_manifest"), TransitManifestPath))
    {
        return false;
    }
    TransitFieldsDirectory = FPaths::GetPath(TransitManifestPath);

    const TArray<TSharedPtr<FJsonValue>>* Windows = nullptr;
    if (!Root->TryGetArrayField(TEXT("windows"), Windows) || Windows == nullptr)
    {
        return false;
    }
    SourceWindows.Reset();
    for (const TSharedPtr<FJsonValue>& Value : *Windows)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        if (!Value.IsValid() || !Value->TryGetObject(Object) || Object == nullptr)
        {
            continue;
        }
        FString ManifestPath;
        FString WindowId;
        const TArray<TSharedPtr<FJsonValue>>* Range = nullptr;
        if (!(*Object)->TryGetStringField(TEXT("cooked_fields_manifest"), ManifestPath) ||
            !(*Object)->TryGetStringField(TEXT("window_id"), WindowId) ||
            !(*Object)->TryGetArrayField(TEXT("station_range_m"), Range) ||
            Range == nullptr || Range->Num() != 2)
        {
            continue;
        }
        FSourceWindow Window;
        Window.FieldsDirectory = FPaths::GetPath(ManifestPath);
        Window.WindowId = WindowId;
        Window.StartStationM = static_cast<float>((*Range)[0]->AsNumber());
        Window.EndStationM = static_cast<float>((*Range)[1]->AsNumber());
        Window.CenterStationM = 0.5f * (Window.StartStationM + Window.EndStationM);
        Window.bNamedRapid = true;
        SourceWindows.Add(MoveTemp(Window));
    }
    return !TransitFieldsDirectory.IsEmpty() && !SourceWindows.IsEmpty();
}

const ARaftSimRiverWaterStreamingActor::FSourceWindow*
ARaftSimRiverWaterStreamingActor::SelectSource(float StationM) const
{
    const FSourceWindow* Best = nullptr;
    float BestCenterDistance = BIG_NUMBER;
    for (const FSourceWindow& Window : SourceWindows)
    {
        if (StationM < Window.StartStationM || StationM > Window.EndStationM)
        {
            continue;
        }
        const float CenterDistance = FMath::Abs(StationM - Window.CenterStationM);
        if (CenterDistance < BestCenterDistance)
        {
            Best = &Window;
            BestCenterDistance = CenterDistance;
        }
    }
    return Best;
}

bool ARaftSimRiverWaterStreamingActor::UpdateWaterWindow(bool bForce)
{
    if (!Raft || !WaterAdapter)
    {
        return false;
    }
    FVector2D RiverPosition;
    FVector Tangent;
    FVector LeftNormal;
    if (!WaterAdapter->WorldToRiverCoordinates(
            Raft->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim river streaming: WorldToRiverCoordinates failed at ")
            TEXT("raft=(%.0f, %.0f, %.0f)"),
            Raft->GetActorLocation().X,
            Raft->GetActorLocation().Y,
            Raft->GetActorLocation().Z);
        return false;
    }
    const FSourceWindow* RapidWindow = SelectSource(RiverPosition.X);
    const FString DesiredDirectory = RapidWindow
        ? RapidWindow->FieldsDirectory
        : TransitFieldsDirectory;
    const bool bSourceChanged = DesiredDirectory != ActiveFieldsDirectory;
    if (!bForce && !bSourceChanged &&
        FMath::Abs(RiverPosition.X - LastWindowCenterStationM) < CachedMovingWindowAdvanceM)
    {
        return true;
    }
    const FVector2D Extent(
        CachedMovingWindowStationExtentM,
        CachedMovingWindowLateralExtentM);
    if (!WaterAdapter->ConfigureMovingRiverWindow(
            DesiredDirectory, CachedFlowBand.ToString(),
            FVector2D(RiverPosition.X, 0.0f), Extent,
            /*RoughnessManning=*/0.041f))
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim river streaming: ConfigureMovingRiverWindow FAILED ")
            TEXT("station=%.1f source=%s"),
            RiverPosition.X,
            *DesiredDirectory);
        return false;
    }
    ActiveFieldsDirectory = DesiredDirectory;
    LastWindowCenterStationM = RiverPosition.X;
    ++SuccessfulHandoffCount;
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim river streaming handoff %d: station=%.1f source=%s"),
        SuccessfulHandoffCount,
        RiverPosition.X,
        *DesiredDirectory);
    return true;
}

void ARaftSimRiverWaterStreamingActor::ApplyStaticFlowBandVisibility() const
{
    // No RiverConfig guard: the placed config actor unloads with its
    // world-partition cell on long rides; CachedFlowBand is captured at
    // BeginPlay. Re-run periodically from Tick — a single BeginPlay pass
    // misses every actor whose cell streams in later ("white foam appears
    // at distance and vanishes as the camera approaches", 2026-08-14).
    static const FName SolverFoamOverlayTag(TEXT("RaftSimSolverFoamOverlay"));
    const FName ActiveTag(*FString::Printf(
        TEXT("RaftSimFlowBand_%s"), *CachedFlowBand.ToString()));
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        bool bIsBandPresentation = false;
        bool bActiveBand = false;
        bool bBakedFoamOverlay = false;
        for (const FName& Tag : Actor->Tags)
        {
            if (Tag == SolverFoamOverlayTag)
            {
                bBakedFoamOverlay = true;
            }
            if (Tag.ToString().StartsWith(TEXT("RaftSimFlowBand_")))
            {
                bIsBandPresentation = true;
                bActiveBand |= Tag == ActiveTag;
            }
        }
        if (bBakedFoamOverlay && !bIsBandPresentation)
        {
            // A foam overlay without a band tag cannot be band-managed;
            // retire it outright (pre-2026-08-14 vintage placements).
            Actor->SetActorHiddenInGame(true);
            continue;
        }
        // Since the 2026-08-14 environment rebake, the foam overlay derives
        // from the same shaped hydraulic fields the raft rides, so it is
        // band-managed like the rest of the water presentation instead of
        // retired (the former blanket hide targeted the old miscalibrated
        // bake that floated over banks).
        if (bIsBandPresentation)
        {
            Actor->SetActorHiddenInGame(!bActiveBand);
        }
    }
}

void ARaftSimRiverWaterStreamingActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TimeSinceUpdateSeconds += DeltaSeconds;
    if (TimeSinceUpdateSeconds >= 0.2f)
    {
        TimeSinceUpdateSeconds = 0.0f;
        UpdateWaterWindow(/*bForce=*/false);
    }
    // World partition streams presentation cells in behind the player; the
    // BeginPlay visibility pass never saw those actors, so re-enforce band
    // and foam-overlay visibility at a low cadence.
    TimeSinceVisibilityReapplySeconds += DeltaSeconds;
    if (TimeSinceVisibilityReapplySeconds >= 2.0f)
    {
        TimeSinceVisibilityReapplySeconds = 0.0f;
        ApplyStaticFlowBandVisibility();
    }
}
