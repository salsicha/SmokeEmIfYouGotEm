#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRiverWaterConfig.generated.h"

/**
 * Placed in a river map to tell the water runtime to load a cooked steady-state
 * flow window (raftsim.cooked_flow_fields.v1) instead of the dev flat tank. The
 * raft resolves this at BeginPlay and calls ConfigureRiverWindow.
 */
UCLASS()
class RAFTSIMWATER_API ARaftSimRiverWaterConfig : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRiverWaterConfig();

    /** Repo-relative directory of the cooked_flow_fields manifest. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FString CookedFieldsDir =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/scenario_troublemaker/"
             "cooked_flow_fields");

    /** Flow band id to load (low_runnable / median_runnable / high_runnable). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FName FlowBand = TEXT("median_runnable");

    /** World-space window centre in meters (XY). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FVector2D WindowCenterM = FVector2D::ZeroVector;

    /** Window extent in meters (square). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    float WindowExtentM = 600.0f;

    /** Optional dense station/lateral-to-curved-world coordinate map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    FString CoordinateMapPath;

    /** M3 full-reach moving-window manifest. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    FString StreamingManifestPath;

    /** Follow the raft and swap overlapping transit/named-rapid solver crops. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    bool bEnableMovingWindowStreaming = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "80.0"))
    float MovingWindowStationExtentM = 320.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "40.0"))
    float MovingWindowLateralExtentM = 80.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "8.0"))
    float MovingWindowAdvanceM = 80.0f;

    /** Full-reach production terrain exists in the map; suppress local bed proxy. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bMapProvidesTerrain = false;
};
