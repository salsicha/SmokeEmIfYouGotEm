#pragma once

#include "CoreMinimal.h"
#include "RaftSimFlexibleRaftModel.h"
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

// Per-substep telemetry from the quasi-static flexible-raft evaluation
// (D1-D4 port). Reference-only until the D6 promotion gate clears; the
// force/moment modifiers are applied to the adapter's kinematic state.
struct FRaftSimFlexStepTelemetry
{
    bool bEvaluated = false;
    double MaxFreeboardLossM = 0.0;
    double PortTotalFreeboardLossM = 0.0;
    double StarboardTotalFreeboardLossM = 0.0;
    double TubeRollLoadBiasNm = 0.0;
    double TubePitchLoadBiasNm = 0.0;
    double TotalRetainedWaterMassKg = 0.0;
    double RetainedWaterRollMomentNm = 0.0;
    double ReferenceFlipThresholdNm = 0.0;
    double ReferenceFlipMarginNm = 0.0;
    bool bReferenceFlipRisk = false;
    int32 ContactCount = 0;
    int32 WrappingContactCount = 0;
    int32 PinnedObstacleCount = 0;
    int32 RecoveringContactCount = 0;
    double MaxIndentationM = 0.0;
    double MinReleaseMarginN = 0.0;
    FVector AppliedForceN = FVector::ZeroVector;
    FVector AppliedTorqueNm = FVector::ZeroVector;
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

    // --- Flexible-raft model (D1-D4 port; CustomReducedRigidBody path) ------

    // Stand up the quasi-static flexible model behind the adapter. Seats may be
    // empty (no crew loads). The tube layout is rebuilt from the parameters.
    void ConfigureFlexibleRaftModel(
        const FRaftSimFlexParameters& InParameters,
        const TArray<FRaftSimFlexCrewSeat>& InSeats,
        double NominalPressurePa = 18000.0);

    void SetFlexibleCrewActions(const TArray<FRaftSimFlexCrewAction>& InActions);

    // Uniform water descriptor for D3 overwash sampling. Disabled by default;
    // when disabled, retained deck water still drains deterministically.
    void SetFlexibleUniformWater(const FRaftSimFlexUniformWater& InWater, bool bInEnabled);

    void SetFlexibleRockObstacles(const TArray<FRaftSimFlexRockObstacle>& InObstacles);

    // Clear retained-water and indentation memory (deterministic restart).
    void ResetFlexiblePersistentState();

    bool IsFlexibleModelConfigured() const { return FlexLayout.Num() > 0; }

    const FRaftSimFlexStepTelemetry& GetLastFlexibleStepTelemetry() const
    {
        return LastFlexStepTelemetry;
    }

    const TMap<FString, double>& GetFlexibleRetainedVolumeBySegment() const
    {
        return RetainedVolumeBySegment;
    }

    const TMap<FString, double>& GetFlexibleIndentationBySegment() const
    {
        return IndentationBySegment;
    }

private:
    UPROPERTY()
    FRaftSimRaftBodyConfig RaftConfig;

    UPROPERTY()
    FRaftSimRaftAuthorityIntegrationPolicy AuthorityIntegrationPolicy;

    UPROPERTY()
    FRaftSimRaftKinematicState KinematicState;

    // Flexible-raft model state (plain C++ members; deterministic).
    FRaftSimFlexParameters FlexParameters;
    TArray<FRaftSimFlexTubeSegment> FlexLayout;
    TArray<FRaftSimFlexCrewSeat> FlexSeats;
    TArray<FRaftSimFlexCrewAction> FlexActions;
    TArray<FRaftSimFlexRockObstacle> FlexObstacles;
    FRaftSimFlexUniformWater FlexWater;
    bool bFlexWaterEnabled = false;
    TMap<FString, double> RetainedVolumeBySegment;
    TMap<FString, double> IndentationBySegment;
    FRaftSimFlexStepTelemetry LastFlexStepTelemetry;

    bool StepFlexibleRaftDynamics(double SubstepSeconds);
};
