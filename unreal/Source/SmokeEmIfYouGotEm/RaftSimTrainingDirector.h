#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimTrainingDirector.generated.h"

class ARaftSimRaftActor;

UENUM(BlueprintType)
enum class ERaftSimTrainingState : uint8
{
    Inactive,
    Briefing,
    Practicing,
    DrillComplete,
    CourseComplete
};

/** Measured Training Eddy course; every drill is completed by live raft actions. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimTrainingDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimTrainingDirector();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Training")
    void NotifyScoutReviewed();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Training")
    ERaftSimTrainingState GetTrainingState() const { return State; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Training")
    FName GetCurrentDrillId() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Training")
    FText GetCurrentPrompt() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Training")
    int32 GetCompletedDrillCount() const { return CurrentDrillIndex; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Training")
    int32 GetTotalDrillCount() const { return DrillIds.Num(); }

private:
    void BeginCurrentDrill();
    void CompleteCurrentDrill();

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;

    UPROPERTY()
    ERaftSimTrainingState State = ERaftSimTrainingState::Inactive;

    TArray<FName> DrillIds;
    int32 CurrentDrillIndex = 0;
    float TransitionRemaining = 0.0f;
    bool bSawPaddle = false;
    bool bSawForward = false;
    bool bSawStopAfterForward = false;
    bool bSawTurn = false;
    bool bScoutReviewed = false;
    bool bRescueDrillSpawned = false;
    int32 InitialPaddleCount = 0;
    int32 InitialHighSideCount = 0;
    int32 InitialRescueCount = 0;
};
