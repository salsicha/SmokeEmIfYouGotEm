#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimRaftPatchSampler.generated.h"

UENUM(BlueprintType)
enum class ERaftSimPatchRole : uint8
{
    Tube,
    Floor,
    Stern,
    Bow,
    PaddleBlade
};

UENUM(BlueprintType)
enum class ERaftSimPatchForceChannel : uint8
{
    Buoyancy,
    Drag,
    AddedMass,
    SurfaceSlope,
    EddyLineShear,
    BoilUpwelling,
    Paddle
};

USTRUCT(BlueprintType)
struct FRaftSimRaftPatchDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    FName PatchId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    ERaftSimPatchRole Role = ERaftSimPatchRole::Tube;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    FVector LocalPositionMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    FVector LocalNormal = FVector::UpVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    float AreaSquareMeters = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    TArray<ERaftSimPatchForceChannel> ForceChannels;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftPatchSample
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    FName PatchId;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    FVector WorldPosition = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    FVector WorldVelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    FRaftSimWaterSample Water;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    float AreaSquareMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Patch")
    TArray<ERaftSimPatchForceChannel> ForceChannels;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimRaftPatchLayout : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Patch")
    TArray<FRaftSimRaftPatchDefinition> OrderedPatches;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimRaftPatchSampler : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Patch")
    void Configure(URaftSimRaftPatchLayout* InLayout);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Patch")
    int32 BuildPatchSamples(
        URaftSimWaterRuntimeAdapter* WaterRuntime,
        const FTransform& RaftWorldTransform,
        const FVector& RaftLinearVelocityMetersPerSecond,
        TArray<FRaftSimRaftPatchSample>& OutSamples
    ) const;

private:
    UPROPERTY()
    TObjectPtr<URaftSimRaftPatchLayout> Layout;
};
