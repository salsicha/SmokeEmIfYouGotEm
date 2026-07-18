#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimCrewStateContracts.h"

#include "RaftSimRunManager.generated.h"

class ARaftSimRaftActor;
class ARaftSimEncounterVolume;

/** Lifecycle of a scored rapid run. */
UENUM(BlueprintType)
enum class ERaftSimRunState : uint8
{
    Ready,
    Running,
    Finished
};

/**
 * Drives a scored descent of a named rapid (release-1.0-plan.md A-6): starts
 * when the raft leaves the scout eddy, accumulates clean-line / swim / angle
 * signals from the raft and encounter volumes, finishes at the Finish volume
 * (or a fallback finish line), scores via the crew scoring library, and saves
 * the best result. Works with no volumes as a plain distance/time trial so it
 * is exercisable in the test tank.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimRunManager : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRunManager();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Run")
    ERaftSimRunState GetRunState() const { return RunState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Run")
    float GetRunTimeSeconds() const { return RunTimeSeconds; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Run")
    int32 GetSafetyIncidentCount() const { return SafetyIncidents; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Run")
    int32 GetSwimCount() const { return SwimCount; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Run")
    FRaftSimGameplayScoreBreakdown GetFinalScore() const { return FinalScore; }

    /** Scenario id used as the save key (e.g. "troublemaker"). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Run")
    FName ScenarioId = TEXT("test_tank_run");

    /** Downstream is +X (the raft's forward / paddle direction). Finish X (cm). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Run")
    float FinishLineX = 4000.0f;

    /** World-X past which the run auto-starts when no Scout volume exists (cm). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Run")
    float StartLineX = -4000.0f;

protected:
    void StartRun();
    void FinishRun();
    void AccumulateSignals(float DeltaSeconds);

    UPROPERTY()
    ERaftSimRunState RunState = ERaftSimRunState::Ready;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;

    UPROPERTY()
    TArray<TObjectPtr<ARaftSimEncounterVolume>> Volumes;

    float RunTimeSeconds = 0.0f;
    int32 SafetyIncidents = 0;
    int32 SwimCount = 0;
    int32 LastSwimmerCount = 0;
    float AngleErrorAccumDeg = 0.0f;
    float AngleSampleSeconds = 0.0f;
    FRaftSimGameplayScoreBreakdown FinalScore;
};
