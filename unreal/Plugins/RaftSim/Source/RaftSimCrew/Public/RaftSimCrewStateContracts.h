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

UENUM(BlueprintType)
enum class ERaftSimSwimmingSkillLevel : uint8
{
    NonSwimmer,
    WeakSwimmer,
    AverageSwimmer,
    StrongSwimmer
};

UENUM(BlueprintType)
enum class ERaftSimRescueMethod : uint8
{
    None,
    ReachGrab,
    PaddleGrab,
    ThrowLine
};

/** Player-facing lifecycle for an aimed rescue. */
UENUM(BlueprintType)
enum class ERaftSimRescueInteractionPhase : uint8
{
    Idle,
    Aiming,
    LineInFlight,
    Pulling,
    ReadyForReentry,
    Reseating,
    Completed,
    Failed
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

USTRUCT(BlueprintType)
struct FRaftSimSwimmingSkillProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimSwimmingSkillLevel SkillLevel = ERaftSimSwimmingSkillLevel::AverageSwimmer;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bSelfRescueAllowed = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float PanicScalar = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float RescuePriority = 0.55f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float PullInDifficulty = 0.9f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TimeToCriticalSeconds = 22.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimPassengerSwimmingSkillAssignment
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bAssignedFromRoster = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    int32 AssignmentSeed = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FRaftSimSwimmingSkillProfile Profile;
};

USTRUCT(BlueprintType)
struct FRaftSimSwimmerRescueFrame
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FVector SwimmerWorldPositionMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FVector SwimmerDriftVelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float VisibilityScore = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float CalloutPriority = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    int32 RescueTargetRank = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimRescueMethod RescueMethod = ERaftSimRescueMethod::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bThrowLineAvailable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TimeInWaterSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float RescueWindowSeconds = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float PullInProgress = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float ReseatRecoverySeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float FatigueDelta = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TrustDelta = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName FailedRescueReason;
};

USTRUCT(BlueprintType)
struct FRaftSimRescueAttempt
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    ERaftSimRescueMethod Method = ERaftSimRescueMethod::ReachGrab;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float DistanceMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bThrowLineAvailable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float TimeInWaterSeconds = 0.0f;
};

/**
 * Deterministic runtime state shared by flat-screen, gamepad, and VR rescue
 * input. Positions are world meters. FeedbackCode is stable UI/audio data,
 * not localized display text.
 */
USTRUCT(BlueprintType)
struct FRaftSimRescueInteractionState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    ERaftSimRescueInteractionPhase Phase = ERaftSimRescueInteractionPhase::Idle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    FName TargetPassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    ERaftSimRescueMethod Method = ERaftSimRescueMethod::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    FVector LineStartWorldMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    FVector LineEndWorldMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    float DistanceMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    float AimAlignment = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    float PullProgress = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    float PhaseElapsedSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    bool bLineVisible = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Rescue")
    FName FeedbackCode = TEXT("rescue_idle");
};

USTRUCT(BlueprintType)
struct FRaftSimGameplayScoringSignals
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    int32 SafetyIncidentCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float CleanLineRatio = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float MeanBoatAngleErrorDegrees = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float UsefulPaddleImpulseRatio = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float MeanCommandLatencySeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float HighSideBraceTimingErrorSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    int32 SwimCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    ERaftSimRescueMethod RescueMethod = ERaftSimRescueMethod::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float TimeInWaterSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    float CrewRecoverySeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Scoring")
    int32 FailedRescueCount = 0;
};

USTRUCT(BlueprintType)
struct FRaftSimGameplayScoreBreakdown
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float SafetyScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float LineChoiceScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float BoatAngleScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float PaddleEfficiencyScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float CommandTimingScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float HighSideBraceTimingScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float SwimRescueScore = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Scoring")
    float TotalScore = 0.0f;
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

UCLASS()
class RAFTSIMCREW_API URaftSimSwimmingSkillLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew")
    static FRaftSimSwimmingSkillProfile MakeSwimmingSkillProfile(
        ERaftSimSwimmingSkillLevel SkillLevel
    );

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    static FRaftSimPassengerSwimmingSkillAssignment AssignSwimmingSkillFromNormalizedValue(
        FName PassengerId,
        FName SeatId,
        float NormalizedValue,
        int32 AssignmentSeed,
        bool bAssignedFromRoster = false
    );
};

UCLASS()
class RAFTSIMCREW_API URaftSimSwimmerRescueLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    static FRaftSimSwimmerRescueFrame IntegrateSwimmerDrift(
        const FRaftSimSwimmerRescueFrame& CurrentFrame,
        FVector WaterVelocityMetersPerSecond,
        float DeltaSeconds
    );

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    static FRaftSimSwimmerRescueFrame EvaluateRescueAttempt(
        const FRaftSimSwimmerRescueFrame& CurrentFrame,
        const FRaftSimRescueAttempt& Attempt,
        const FRaftSimSwimmingSkillProfile& SkillProfile
    );

    /** Validate range/aim and begin an explicit player rescue interaction. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Rescue")
    static FRaftSimRescueInteractionState BeginRescueInteraction(
        FName TargetPassengerId,
        ERaftSimRescueMethod Method,
        FVector LineStartWorldMeters,
        FVector TargetWorldMeters,
        FVector AimDirection,
        bool bThrowLineAvailable,
        float TimeInWaterSeconds,
        const FRaftSimSwimmingSkillProfile& SkillProfile
    );

    /** Advance throw flight and pull-in using real elapsed seconds. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Rescue")
    static FRaftSimRescueInteractionState AdvanceRescueInteraction(
        const FRaftSimRescueInteractionState& CurrentState,
        FVector LineStartWorldMeters,
        FVector TargetWorldMeters,
        float DeltaSeconds
    );

    /** Complete the deliberate tube-side re-entry step. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Rescue")
    static FRaftSimRescueInteractionState CompleteReseat(
        const FRaftSimRescueInteractionState& CurrentState,
        float DistanceToRaftMeters
    );
};

UCLASS()
class RAFTSIMCREW_API URaftSimGameplayScoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Scoring")
    static FRaftSimGameplayScoreBreakdown EvaluateGameplayScore(
        const FRaftSimGameplayScoringSignals& Signals
    );
};
