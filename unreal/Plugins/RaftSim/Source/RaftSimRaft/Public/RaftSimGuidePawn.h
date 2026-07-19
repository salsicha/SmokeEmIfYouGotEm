#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"

#include "RaftSimGuidePawn.generated.h"

class ARaftSimRaftActor;
class UCameraComponent;
class UInputAction;
class UInputMappingContext;
class USceneComponent;
struct FInputActionValue;

UENUM(BlueprintType)
enum class ERaftSimGuideMobilityMode : uint8
{
    InRaft,
    Swimming,
    Reboarding
};

USTRUCT(BlueprintType)
struct FRaftSimGuideCameraSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableSeatedRecenter = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableVRComfortVignette = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableHorizonStabilization = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableImpactFiltering = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableHapticImpactPulses = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bShowHandsPaddleAndRaftContext = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float MotionIntensity = 0.65f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float AccessibilityMotionScale = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float ImpactFilterSpeed = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float HorizonStabilizationStrength = 0.75f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float ComfortVignetteStrength = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float HapticImpactThreshold = 0.25f;
};

USTRUCT(BlueprintType)
struct FRaftSimGuideCameraRuntimeState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    bool bSeatedViewRecentered = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    bool bAccessibilityComfortMode = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    FVector FilteredImpactOffsetCm = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    FRotator FilteredImpactRotation = FRotator::ZeroRotator;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    float CurrentVignetteStrength = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    float PendingHapticAmplitude = 0.0f;

    FVector TargetImpactOffsetCm = FVector::ZeroVector;
    FRotator TargetImpactRotation = FRotator::ZeroRotator;
};

UCLASS()
class RAFTSIMRAFT_API ARaftSimGuidePawn : public APawn
{
    GENERATED_BODY()

public:
    ARaftSimGuidePawn();

    virtual void Tick(float DeltaSeconds) override;
    virtual void BeginPlay() override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    UCameraComponent* GetGuideCamera() const { return GuideCamera; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetGuideSeatAnchor() const { return GuideSeatAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetViewOriginAnchor() const { return ViewOriginAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetLeftHandAnchor() const { return LeftHandAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetRightHandAnchor() const { return RightHandAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetPaddleAnchor() const { return PaddleAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetRaftBowReferenceAnchor() const { return RaftBowReferenceAnchor; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    FRaftSimGuideCameraSettings GetCameraSettings() const { return CameraSettings; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    FRaftSimGuideCameraRuntimeState GetCameraRuntimeState() const { return CameraRuntimeState; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCamera")
    void ApplyGuideCameraSettings(const FRaftSimGuideCameraSettings& NewSettings);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCamera")
    void RecenterSeatedView();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCamera")
    void SetAccessibilityComfortMode(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCamera")
    void ApplyRaftImpactCue(FVector LocalOffsetCm, FRotator LocalRotation, float NormalizedIntensity);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCamera")
    float ConsumePendingHapticPulse();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Guide")
    ERaftSimGuideMobilityMode GetMobilityMode() const { return MobilityMode; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Input")
    bool HasCompleteRescueInputBindings() const;

protected:
    float GetEffectiveMotionIntensity() const;
    void UpdateComfortCamera(float DeltaSeconds);

    void HandlePaddleStroke(const FInputActionValue& Value);
    void HandleTurnStroke(const FInputActionValue& Value);
    void HandleLook(const FInputActionValue& Value);
    void HandleHighSide(const FInputActionValue& Value);
    void HandleGuideCommand(FName CommandActionName);
    void HandleRescueTargetSelect(const FInputActionValue& Value);
    void HandleRescueReach(const FInputActionValue& Value);
    void HandleRescueThrowLine(const FInputActionValue& Value);
    void HandleReseatCrew(const FInputActionValue& Value);
    void UpdateSwimmingAndRescueAim();
    ARaftSimRaftActor* ResolveRaft();

    /** Mapping context and actions are generated assets under /Game/RaftSim/Input. */
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputMappingContext> DefaultMappingContext;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> PaddleStrokeAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> PaddleDrawAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> LookAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> HighSideAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> RescueTargetSelectAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> RescueReachAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> RescueThrowLineAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TObjectPtr<UInputAction> ReseatCrewAction;

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Input")
    TArray<TObjectPtr<UInputAction>> GuideCommandActions;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> AttachedRaft;

    /** Seconds between accepted paddle strokes (stroke cadence limit). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Input")
    float StrokeCooldownSeconds = 0.45f;

    float LastStrokeTimeSeconds = -1.0f;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Guide")
    ERaftSimGuideMobilityMode MobilityMode = ERaftSimGuideMobilityMode::InRaft;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> GuideSeatAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> ViewOriginAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> CameraImpactAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> LeftHandAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> RightHandAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> PaddleAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> RaftContextAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> RaftBowReferenceAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> LeftTubeReferenceAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> RightTubeReferenceAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> PassengerSilhouetteAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<UCameraComponent> GuideCamera;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    FRaftSimGuideCameraSettings CameraSettings;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    FRaftSimGuideCameraRuntimeState CameraRuntimeState;
};
