#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WorldPartition/WorldPartitionStreamingSource.h"
#include "RaftSimRescueStreamingComponent.generated.h"

/** Keeps collision terrain near the raft AND separated swimmers resident.
 * Does not own, recreate, teleport or advance raft/rescue/water state. */
UCLASS()
class RAFTSIMRAFT_API URaftSimRescueStreamingComponent : public UActorComponent,
    public IWorldPartitionStreamingSourceProvider
{
    GENERATED_BODY()
public:
    URaftSimRescueStreamingComponent();
    virtual bool GetStreamingSources(TArray<FWorldPartitionStreamingSource>& Sources) const override;
    virtual const UObject* GetStreamingSourceOwner() const override { return this; }
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
};
