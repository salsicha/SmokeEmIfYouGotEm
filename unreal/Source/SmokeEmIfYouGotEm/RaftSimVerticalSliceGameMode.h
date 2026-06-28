#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"

#include "RaftSimVerticalSliceGameMode.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimRapidScoreBreakdown
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float Safety = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float LineChoice = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float BoatAngle = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float PaddleEfficiency = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float CrewTrust = 0.0f;

    float Total() const { return Safety + LineChoice + BoatAngle + PaddleEfficiency + CrewTrust; }
};

UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimVerticalSliceGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ARaftSimVerticalSliceGameMode();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void RestartRapid();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void SetReplayEnabled(bool bInReplayEnabled);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void SetDebugForceVisualizationEnabled(bool bInEnabled);

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    const FRaftSimRapidScoreBreakdown& GetCurrentScore() const { return CurrentScore; }

private:
    UPROPERTY()
    FRaftSimRapidScoreBreakdown CurrentScore;

    bool bReplayEnabled = true;
    bool bDebugForceVisualizationEnabled = true;
};
