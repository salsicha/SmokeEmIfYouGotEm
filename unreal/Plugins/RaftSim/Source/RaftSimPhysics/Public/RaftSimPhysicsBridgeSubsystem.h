#pragma once

#include "CoreMinimal.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimPhysicsBridgeSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimPhysicsTickInput
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    float FrameDeltaSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FVector GuidePaddleIntent = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    int32 DeterministicFrame = 0;
};

USTRUCT(BlueprintType)
struct FRaftSimPhysicsTickOutput
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Physics")
    int32 CommittedPhysicsFrame = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Physics")
    float SimTimeSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Physics")
    FRaftSimRaftKinematicState RaftState;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Physics")
    int32 WaterSamplesApplied = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Physics")
    int32 ContactEvents = 0;
};

UCLASS()
class RAFTSIMPHYSICS_API URaftSimPhysicsBridgeSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Physics")
    void ConfigureBridge(
        const FRaftSimWaterRuntimeConfig& WaterConfig,
        const FRaftSimRaftBodyConfig& RaftConfig,
        float InWaterStepSeconds = 1.0f / 60.0f,
        float InChronoSubstepSeconds = 1.0f / 120.0f
    );

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Physics")
    FRaftSimPhysicsTickOutput TickBridge(const FRaftSimPhysicsTickInput& Input);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Physics")
    const FRaftSimPhysicsTickOutput& GetLastOutput() const { return LastOutput; }

private:
    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterRuntime;

    UPROPERTY()
    TObjectPtr<URaftSimChronoRuntimeAdapter> RaftRuntime;

    UPROPERTY()
    FRaftSimPhysicsTickOutput LastOutput;

    float WaterStepSeconds = 1.0f / 60.0f;
    float ChronoSubstepSeconds = 1.0f / 120.0f;
    float AccumulatedSeconds = 0.0f;
    int32 PhysicsFrame = 0;

    void RunOneFixedWaterTick();
};
