#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRiverWaterStreamingActor.generated.h"

class ARaftSimRaftActor;
class ARaftSimRiverWaterConfig;
class URaftSimWaterRuntimeAdapter;

/**
 * Runtime controller for the M3 full-reach streaming manifest. It follows the
 * raft in curved world space, projects it to station/lateral coordinates, and
 * swaps overlapping transit or named-rapid solver crops without resetting the
 * water clock, raft, or gameplay state.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimRiverWaterStreamingActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRiverWaterStreamingActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Streaming")
    int32 GetSuccessfulHandoffCount() const { return SuccessfulHandoffCount; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Streaming")
    FString GetActiveFieldsDirectory() const { return ActiveFieldsDirectory; }

private:
    struct FSourceWindow
    {
        FString FieldsDirectory;
        FString WindowId;
        float StartStationM = 0.0f;
        float EndStationM = 0.0f;
        float CenterStationM = 0.0f;
        bool bNamedRapid = false;
    };

    bool LoadStreamingManifest();
    const FSourceWindow* SelectSource(float StationM) const;
    bool UpdateWaterWindow(bool bForce);
    void ApplyStaticFlowBandVisibility() const;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;

    UPROPERTY()
    TObjectPtr<ARaftSimRiverWaterConfig> RiverConfig;

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    TArray<FSourceWindow> SourceWindows;
    FString TransitFieldsDirectory;
    FString ActiveFieldsDirectory;
    float LastWindowCenterStationM = -BIG_NUMBER;
    float TimeSinceUpdateSeconds = 0.0f;
    int32 SuccessfulHandoffCount = 0;
};
