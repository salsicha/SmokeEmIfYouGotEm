#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimCrewStateContracts.generated.h"

namespace RaftSimCrew
{
    static constexpr const TCHAR* SafetyStateSchema = TEXT("raftsim.crew.safety_state.v1");
    static constexpr const TCHAR* SwimmingSkillPolicy = TEXT("assigned_per_run_or_roster_entry");
}

UENUM(BlueprintType)
enum class ERaftSimCrewWeightShiftAction : uint8
{
    None,
    Brace,
    LeanLeft,
    LeanRight,
    HighSideLeft,
    HighSideRight,
    HoldOn,
    RecoverSeated
};

UENUM(BlueprintType)
enum class ERaftSimCrewSafetyState : uint8
{
    Seated,
    AtRisk,
    FallingEjected,
    Swimming,
    RescueTargeted,
    Rescued,
    ReseatedRecovered,
    FailedRescue
};

USTRUCT(BlueprintType)
struct FRaftSimCrewSeatOccupancy
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bOccupied = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float PassengerMassKg = 82.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FVector LocalSeatPositionMeters = FVector::ZeroVector;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewWeightShiftCommand
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimCrewWeightShiftAction Action = ERaftSimCrewWeightShiftAction::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float NormalizedIntensity = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float DurationSeconds = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewWeightDistributionFrame
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    float TotalMassKg = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    FVector CenterOfGravityLocalMeters = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    float RollMomentNewtonMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    float PinLoadModifier = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    float FlipRiskModifier = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    float ReleaseAssistModifier = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    int32 BraceCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    int32 HighSideCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew")
    int32 LeanCount = 0;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewSafetyStateFrame
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimCrewSafetyState CurrentState = ERaftSimCrewSafetyState::Seated;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TimeInStateSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TimeInWaterSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float RescueTargetPriority = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName FailedRescueReason;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewSafetyTransition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimCrewSafetyState PreviousState = ERaftSimCrewSafetyState::Seated;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimCrewSafetyState NextState = ERaftSimCrewSafetyState::Seated;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName TransitionReason;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SourceContactEventId;
};

UCLASS()
class RAFTSIMCREW_API URaftSimCrewWeightDistributionLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    static FRaftSimCrewWeightDistributionFrame EvaluateWeightDistribution(
        const TArray<FRaftSimCrewSeatOccupancy>& Seats,
        const TArray<FRaftSimCrewWeightShiftCommand>& Commands
    );
};

UCLASS()
class RAFTSIMCREW_API URaftSimCrewSafetyStateLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew")
    static bool CanTransitionSafetyState(
        ERaftSimCrewSafetyState PreviousState,
        ERaftSimCrewSafetyState NextState
    );

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    static FRaftSimCrewSafetyStateFrame ApplySafetyTransition(
        const FRaftSimCrewSafetyStateFrame& CurrentFrame,
        const FRaftSimCrewSafetyTransition& Transition
    );
};
