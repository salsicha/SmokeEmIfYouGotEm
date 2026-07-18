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
};
