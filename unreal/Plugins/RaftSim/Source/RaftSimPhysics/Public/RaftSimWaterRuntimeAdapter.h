#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimWaterRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimWaterRuntimeStatus : uint8
{
    Uninitialized,
    ScenarioBound,
    Running,
    Faulted
};

USTRUCT(BlueprintType)
struct FRaftSimWaterRuntimeConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString RuntimeName = TEXT(RAFTSIM_WATER_RUNTIME_NAME);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString ScenarioPackagePath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    float FixedStepSeconds = 1.0f / 60.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bUseFiniteVolumeMode = true;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterSample
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector WorldPosition = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float SurfaceHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float BedHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float DepthMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector VelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector SurfaceNormal = FVector::UpVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bWet = false;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimWaterRuntimeAdapter : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    void Configure(const FRaftSimWaterRuntimeConfig& InConfig);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterRuntimeConfig& GetConfig() const { return Config; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    ERaftSimWaterRuntimeStatus GetStatus() const { return Status; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool StepWater(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool SampleWaterAtWorldPosition(const FVector& WorldPosition, FRaftSimWaterSample& OutSample) const;

private:
    UPROPERTY()
    FRaftSimWaterRuntimeConfig Config;

    UPROPERTY()
    ERaftSimWaterRuntimeStatus Status = ERaftSimWaterRuntimeStatus::Uninitialized;

    double SimTimeSeconds = 0.0;
};
