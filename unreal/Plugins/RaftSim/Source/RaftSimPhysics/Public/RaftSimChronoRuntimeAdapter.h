#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimChronoRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRaftDynamicsRuntime : uint8
{
    ProjectChrono,
    CustomReducedRigidBody
};

USTRUCT(BlueprintType)
struct FRaftSimRaftBodyConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    ERaftSimRaftDynamicsRuntime Runtime = ERaftSimRaftDynamicsRuntime::ProjectChrono;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float MassKg = 170.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    FVector InertiaTensorKgM2 = FVector(220.0f, 620.0f, 700.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float TubeRadiusMeters = 0.32f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float LengthMeters = 4.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float WidthMeters = 2.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    bool bEnableCompliantContacts = true;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftKinematicState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FVector LinearVelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FVector AngularVelocityRadiansPerSecond = FVector::ZeroVector;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimChronoRuntimeAdapter : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    void ConfigureRaftBody(const FRaftSimRaftBodyConfig& InConfig);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Chrono")
    const FRaftSimRaftBodyConfig& GetRaftBodyConfig() const { return RaftConfig; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    void SetKinematicState(const FRaftSimRaftKinematicState& InState);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Chrono")
    const FRaftSimRaftKinematicState& GetKinematicState() const { return KinematicState; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    bool StepRaftDynamics(float SubstepSeconds);

private:
    UPROPERTY()
    FRaftSimRaftBodyConfig RaftConfig;

    UPROPERTY()
    FRaftSimRaftKinematicState KinematicState;
};
