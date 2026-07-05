#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimReachLocalStreamingConfig.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimReachLocalGridWindow
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FName ReachId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    int32 UpstreamGhostCells = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    int32 DownstreamGhostCells = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    int32 GridNx = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    int32 GridNy = 0;
};

USTRUCT(BlueprintType)
struct FRaftSimReachStreamingWindow
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FName WindowId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FString ScenarioPackage;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    TArray<FName> ReachIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    TArray<FRaftSimReachLocalGridWindow> ReachLocalGrids;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FString StitchedValidationManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    bool bRequiresStitchedWholeWindowValidation = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimReachLocalStreamingConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FString Schema = TEXT("raftsim.unreal.reach_local_streaming.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    FString TraceableRiverDataAssets = TEXT("unreal/Content/RaftSim/River/traceable_river_data_assets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    TArray<FRaftSimReachStreamingWindow> PlayableWindows;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    bool bRequireOverlapGhostZones = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReachStreaming")
    bool bRejectIsolatedReachValidationForSignoff = true;
};
