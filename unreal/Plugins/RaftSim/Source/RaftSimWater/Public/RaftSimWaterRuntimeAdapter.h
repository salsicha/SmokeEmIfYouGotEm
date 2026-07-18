#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimLiveWaterWindow.h"
#include "Templates/UniquePtr.h"

#include "RaftSimWaterRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimWaterRuntimeStatus : uint8
{
    Uninitialized,
    ScenarioBound,
    Running,
    Faulted
};

USTRUCT(BlueprintType)
struct FRaftSimWaterReportManifestState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString ManifestPath;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString LockHash;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 LockedArtifactCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bLoaded = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bAccepted = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bLiveWaterBridgeUnblocked = false;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterDeterministicCaptureState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString CapturePath;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString LastFrameHash;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 CapturedFrameCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bEnabled = false;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterRuntimeConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString RuntimeName = TEXT(RAFTSIM_WATER_RUNTIME_NAME);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString ScenarioPackagePath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString AcceptedReportSetManifestPath = TEXT("physics/reports/milestone20/report_set_lock.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString ExpectedReportSetLockHash;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString DeterministicCapturePath = TEXT("Saved/Automation/RaftSim/Water/live_water_capture.jsonl");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    float FixedStepSeconds = 1.0f / 60.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    int32 DeterministicSeed = 20;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bUseFiniteVolumeMode = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bRequireAcceptedReportManifest = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bEnableDeterministicCapture = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bEnableRenderInterpolation = true;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterSample
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector WorldPosition = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float SurfaceHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float BedHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float DepthMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector VelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector SurfaceNormal = FVector::UpVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bWet = false;
};

UCLASS(BlueprintType)
class RAFTSIMWATER_API URaftSimWaterRuntimeAdapter : public UObject
{
    GENERATED_BODY()

public:
    virtual ~URaftSimWaterRuntimeAdapter() override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    void Configure(const FRaftSimWaterRuntimeConfig& InConfig);

    /**
     * Configure a live flat-tank solver window (genuine FV solver, order 2,
     * calibrations disabled). Dev water for the P1/P2 test tank; river
     * windows replace this in P2 slice three. No-op without the solver lib.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool ConfigureDevTankWindow(
        FVector2D WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
        float SurfaceHeightM, float DepthM);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    bool HasLiveWindow() const;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool LoadAcceptedReportManifest(const FString& ManifestPath);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterRuntimeConfig& GetConfig() const { return Config; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterReportManifestState& GetReportManifestState() const { return ReportManifestState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterDeterministicCaptureState& GetCaptureState() const { return CaptureState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    ERaftSimWaterRuntimeStatus GetStatus() const { return Status; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    int32 GetCommittedWaterFrame() const { return CommittedWaterFrame; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    float GetSimTimeSeconds() const { return static_cast<float>(SimTimeSeconds); }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool StepWater(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool SampleWaterAtWorldPosition(const FVector& WorldPosition, FRaftSimWaterSample& OutSample) const;

private:
    UPROPERTY()
    FRaftSimWaterRuntimeConfig Config;

    UPROPERTY()
    FRaftSimWaterReportManifestState ReportManifestState;

    UPROPERTY()
    FRaftSimWaterDeterministicCaptureState CaptureState;

    UPROPERTY()
    ERaftSimWaterRuntimeStatus Status = ERaftSimWaterRuntimeStatus::Uninitialized;

    int32 CommittedWaterFrame = 0;
    double SimTimeSeconds = 0.0;

    FString BuildDeterministicFrameHash() const;
    void AppendDeterministicCaptureFrame();
    FString ResolveRepoRelativePath(const FString& Path) const;

    TUniquePtr<FRaftSimLiveWaterWindow> LiveWindow;
};
