#pragma once

#include "CoreMinimal.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimPhysicsClockSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimPoseHistorySample
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    int32 PhysicsFrame = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    float TimeSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    FRaftSimRaftKinematicState RaftState;
};

USTRUCT(BlueprintType)
struct FRaftSimInterpolatedPose
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    FTransform Transform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    float Alpha = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    int32 FromFrame = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|PhysicsClock")
    int32 ToFrame = 0;
};

UCLASS()
class RAFTSIMPHYSICS_API URaftSimPhysicsClockSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|PhysicsClock")
    void CommitPhysicsPose(const FRaftSimPoseHistorySample& Sample);

    UFUNCTION(BlueprintPure, Category = "RaftSim|PhysicsClock")
    FRaftSimInterpolatedPose InterpolateForRender(float RenderTimeSeconds) const;

private:
    UPROPERTY()
    FRaftSimPoseHistorySample PreviousSample;

    UPROPERTY()
    FRaftSimPoseHistorySample CurrentSample;

    bool bHasPrevious = false;
    bool bHasCurrent = false;
};
