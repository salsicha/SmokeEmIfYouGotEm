#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimContentLockDirector.generated.h"

/**
 * Runtime validation entry point shared by editor automation and installed
 * Development builds. It exercises every South Fork rapid/flow cook through
 * the shipping water adapter and emits machine-readable content-lock evidence.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimContentLockDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimContentLockDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    static bool IsPackagedRegressionRequested();
    static bool IsPerformanceCaptureRequested();

    /** Run the complete 20-rapid x 3-flow matrix without requiring a world. */
    static bool RunRapidMatrixRegression(FString& OutReportJson);

    void StartPerformanceCapture(
        float DurationSeconds, float WarmupSeconds,
        const FString& OutputPath = FString(), bool bExitWhenComplete = false);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Validation")
    bool IsPerformanceCaptureComplete() const { return bPerformanceCaptureComplete; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Validation")
    bool DidPerformanceCapturePass() const { return bPerformanceCapturePassed; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Validation")
    float GetPerformanceP95FrameMilliseconds() const { return PerformanceP95FrameMilliseconds; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Validation")
    int32 GetPerformanceHitchCount() const { return PerformanceHitchCount; }

private:
    void FinishPerformanceCapture();
    FString ResolveOutputPath(const FString& RequestedPath, const TCHAR* DefaultName) const;

    bool bCapturingPerformance = false;
    bool bPerformanceCaptureComplete = false;
    bool bPerformanceCapturePassed = false;
    bool bExitAfterPerformanceCapture = false;
    bool bProfileGpuAtWarmupEnd = false;
    float PerformanceWarmupRemaining = 0.0f;
    float PerformanceCaptureRemaining = 0.0f;
    float PerformanceP95FrameMilliseconds = 0.0f;
    float PerformanceP95WallClockMilliseconds = 0.0f;
    float LastGameDeltaMilliseconds = 0.0f;
    double LastPerformanceTickSeconds = 0.0;
    int32 PerformanceHitchCount = 0;
    FString PerformanceOutputPath;
    TArray<float> CapturedWorkloadFrameMilliseconds;
    TArray<float> CapturedWallClockFrameMilliseconds;
    TArray<float> CapturedGameThreadMilliseconds;
    TArray<float> CapturedRenderThreadMilliseconds;
    TArray<float> CapturedGpuMilliseconds;
};
