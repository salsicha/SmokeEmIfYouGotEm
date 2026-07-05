#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimChronoRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRaftDynamicsRuntime : uint8
{
    ProjectChrono,
    CustomReducedRigidBody,
    UnrealChaos,
    Jolt
};

USTRUCT(BlueprintType)
struct FRaftSimRaftAuthorityIntegrationPolicy
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    ERaftSimRaftDynamicsRuntime SelectedRuntime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString WaterAuthority = TEXT("custom_cxx_shallow_water_solver");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString AuthoritySelectionReport = TEXT("physics/reports/milestone19/runtime_authority_selection.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString AcceptedWaterReportSetLock = TEXT("physics/reports/milestone20/report_set_lock.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bCustomWaterReportLockRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bChaosMayDriveScoringCriticalPhysics = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bRenderTickMayAdvanceAuthority = false;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftBodyConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    ERaftSimRaftDynamicsRuntime Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;

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

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Physics")
    void ConfigureAuthorityIntegrationPolicy(const FRaftSimRaftAuthorityIntegrationPolicy& InPolicy);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Physics")
    const FRaftSimRaftAuthorityIntegrationPolicy& GetAuthorityIntegrationPolicy() const
    {
        return AuthorityIntegrationPolicy;
    }

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
    FRaftSimRaftAuthorityIntegrationPolicy AuthorityIntegrationPolicy;

    UPROPERTY()
    FRaftSimRaftKinematicState KinematicState;
};
