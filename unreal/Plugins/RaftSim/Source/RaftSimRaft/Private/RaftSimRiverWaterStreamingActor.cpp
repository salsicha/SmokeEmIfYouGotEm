#include "RaftSimRiverWaterStreamingActor.h"

#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
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
        SetActorTickEnabled(false);
        return;
    }
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
    if (!Raft || !RiverConfig || !WaterAdapter)
    {
        return false;
    }
    FVector2D RiverPosition;
    FVector Tangent;
    FVector LeftNormal;
    if (!WaterAdapter->WorldToRiverCoordinates(
            Raft->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
    {
        return false;
    }
    const FSourceWindow* RapidWindow = SelectSource(RiverPosition.X);
    const FString DesiredDirectory = RapidWindow
        ? RapidWindow->FieldsDirectory
        : TransitFieldsDirectory;
    const bool bSourceChanged = DesiredDirectory != ActiveFieldsDirectory;
    if (!bForce && !bSourceChanged &&
        FMath::Abs(RiverPosition.X - LastWindowCenterStationM) < RiverConfig->MovingWindowAdvanceM)
    {
        return true;
    }
    const FVector2D Extent(
        RiverConfig->MovingWindowStationExtentM,
        RiverConfig->MovingWindowLateralExtentM);
    if (!WaterAdapter->ConfigureMovingRiverWindow(
            DesiredDirectory, RiverConfig->FlowBand.ToString(),
            FVector2D(RiverPosition.X, 0.0f), Extent,
            /*RoughnessManning=*/0.041f))
    {
        return false;
    }
    ActiveFieldsDirectory = DesiredDirectory;
    LastWindowCenterStationM = RiverPosition.X;
    ++SuccessfulHandoffCount;
    return true;
}

void ARaftSimRiverWaterStreamingActor::ApplyStaticFlowBandVisibility() const
{
    if (!RiverConfig)
    {
        return;
    }
    const FName ActiveTag(*FString::Printf(
        TEXT("RaftSimFlowBand_%s"), *RiverConfig->FlowBand.ToString()));
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        bool bIsBandPresentation = false;
        bool bActiveBand = false;
        for (const FName& Tag : Actor->Tags)
        {
            if (Tag.ToString().StartsWith(TEXT("RaftSimFlowBand_")))
            {
                bIsBandPresentation = true;
                bActiveBand |= Tag == ActiveTag;
            }
        }
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
}
