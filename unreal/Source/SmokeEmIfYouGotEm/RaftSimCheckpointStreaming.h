#pragma once

#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "WorldPartition/WorldPartitionStreamingSource.h"
#include "WorldPartition/WorldPartitionSubsystem.h"

namespace RaftSimCheckpointStreaming
{
// Preserve player grid/shape/range policy. This temporary destination source
// handles an intentional checkpoint discontinuity, not ordinary downstream travel.
inline bool MakeDestinationSources(const TArray<FWorldPartitionStreamingSource>& PlayerSources,
    const FTransform& Destination,TArray<FWorldPartitionStreamingSource>& OutSources)
{
    OutSources.Reset();
    if (PlayerSources.IsEmpty() || !Destination.IsValid()) return false;
    OutSources=PlayerSources;
    for (int32 Index=0; Index<OutSources.Num(); ++Index)
    {
        auto& Source=OutSources[Index];
        Source.Name=FName(*FString::Printf(TEXT("RaftSimCheckpointDestination_%d"),Index));
        Source.Location=Destination.GetLocation();
        Source.Rotation=Destination.Rotator();
        Source.TargetState=EStreamingSourceTargetState::Activated;
        Source.bBlockOnSlowLoading=true;
        Source.Velocity=FVector::ZeroVector;
        Source.bUseVelocityContributionToCellsSorting=false;
    }
    return true;
}

class FScopedDestination final : public IWorldPartitionStreamingSourceProvider
{
public:
    FScopedDestination(UWorldPartitionSubsystem* InSubsystem,TArray<FWorldPartitionStreamingSource>&& InSources)
        : Subsystem(InSubsystem),Sources(MoveTemp(InSources))
    { Subsystem->RegisterStreamingSourceProvider(this); }
    ~FScopedDestination() { Subsystem->UnregisterStreamingSourceProvider(this); }
    bool GetStreamingSources(TArray<FWorldPartitionStreamingSource>& OutSources) const override
    { OutSources.Append(Sources);return !Sources.IsEmpty(); }
    const UObject* GetStreamingSourceOwner() const override { return Subsystem; }
    FScopedDestination(const FScopedDestination&)=delete;
    FScopedDestination& operator=(const FScopedDestination&)=delete;
private:
    UWorldPartitionSubsystem* Subsystem;
    TArray<FWorldPartitionStreamingSource> Sources;
};

inline bool Prepare(UWorld* World,const FTransform& Destination)
{
    if (!World || !Destination.IsValid()) return false;
    if (!World->GetWorldPartition()) return true;
    auto* Partition=World->GetSubsystem<UWorldPartitionSubsystem>();
    auto* Player=World->GetFirstPlayerController();
    TArray<FWorldPartitionStreamingSource> PlayerSources,DestinationSources;
    if (!Partition || !Player || !Player->GetStreamingSources(PlayerSources) ||
        !MakeDestinationSources(PlayerSources,Destination,DestinationSources)) return false;
    const double Start=FPlatformTime::Seconds();
    const int32 SourceCount=DestinationSources.Num();
    FScopedDestination Source(Partition,MoveTemp(DestinationSources));
    // Complete cell activation before reseeding water or moving the raft. The
    // camera's normal source still points at the old location during this tick.
    // Scope exit unregisters the extra provider; no permanent residency/range change.
    World->BlockTillLevelStreamingCompleted();
    const bool bReady=Partition->IsStreamingCompleted(&Source);
    UE_LOG(LogTemp,Display,TEXT("CHECKPOINT_TERRAIN_PREPARED game_frame=%llu sources=%d activated=%d seconds=%.6f destination_cm=%s"),
        GFrameCounter,SourceCount,bReady,FPlatformTime::Seconds()-Start,*Destination.GetLocation().ToString());
    return bReady;
}
}
