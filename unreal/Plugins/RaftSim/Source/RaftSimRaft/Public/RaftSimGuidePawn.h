#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"

#include "RaftSimGuidePawn.generated.h"

class UCameraComponent;
class USceneComponent;

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

protected:
    float GetEffectiveMotionIntensity() const;
    void UpdateComfortCamera(float DeltaSeconds);

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
