#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimRaftCondition.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRaftDamageState : uint8
{
    Intact,
    Creased,
    Abraded,
    Punctured,
    Critical
};

USTRUCT(BlueprintType)
struct FRaftSimRaftContactExposure
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    float DeltaSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    float MaximumIndentationM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    int32 ContactCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    int32 WrappingContactCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    int32 PinnedObstacleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Raft|Condition")
    float RetainedWaterMassKg = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftConditionState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    ERaftSimRaftDamageState DamageState = ERaftSimRaftDamageState::Intact;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    float FabricIntegrity = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    float PressureFraction = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    float PermanentCreaseAmplitudeM = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    float SevereContactExposureSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    int32 WrapEventCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Raft|Condition")
    int32 PinEventCount = 0;

    bool bWasWrapping = false;
    bool bWasPinned = false;
};

UCLASS()
class RAFTSIMRAFT_API URaftSimRaftConditionLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Calibrated, frame-rate-independent fabric exposure and pressure loss. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft|Condition")
    static FRaftSimRaftConditionState AdvanceCondition(
        const FRaftSimRaftConditionState& Current,
        const FRaftSimRaftContactExposure& Exposure);

    /** Field repair restores pressure but preserves a visible history crease. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft|Condition")
    static FRaftSimRaftConditionState ApplyCheckpointRepair(
        const FRaftSimRaftConditionState& Current);
};
