#include "RaftSimGuidePawn.h"

#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"

ARaftSimGuidePawn::ARaftSimGuidePawn()
{
    PrimaryActorTick.bCanEverTick = true;
    AutoPossessPlayer = EAutoReceiveInput::Player0;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    GuideSeatAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("GuideSeatAnchor"));
    GuideSeatAnchor->SetupAttachment(Root);
    GuideSeatAnchor->SetRelativeLocation(FVector(-180.0f, 0.0f, 45.0f));

    ViewOriginAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("ViewOriginAnchor"));
    ViewOriginAnchor->SetupAttachment(GuideSeatAnchor);

    CameraImpactAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("CameraImpactAnchor"));
    CameraImpactAnchor->SetupAttachment(ViewOriginAnchor);

    LeftHandAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("LeftHandAnchor"));
    LeftHandAnchor->SetupAttachment(ViewOriginAnchor);
    LeftHandAnchor->SetRelativeLocation(FVector(30.0f, -38.0f, -32.0f));

    RightHandAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("RightHandAnchor"));
    RightHandAnchor->SetupAttachment(ViewOriginAnchor);
    RightHandAnchor->SetRelativeLocation(FVector(30.0f, 38.0f, -32.0f));

    PaddleAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("PaddleAnchor"));
    PaddleAnchor->SetupAttachment(ViewOriginAnchor);
    PaddleAnchor->SetRelativeLocation(FVector(25.0f, -65.0f, -20.0f));

    RaftContextAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("RaftContextAnchor"));
    RaftContextAnchor->SetupAttachment(Root);

    RaftBowReferenceAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("RaftBowReferenceAnchor"));
    RaftBowReferenceAnchor->SetupAttachment(RaftContextAnchor);
    RaftBowReferenceAnchor->SetRelativeLocation(FVector(280.0f, 0.0f, 20.0f));

    LeftTubeReferenceAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("LeftTubeReferenceAnchor"));
    LeftTubeReferenceAnchor->SetupAttachment(RaftContextAnchor);
    LeftTubeReferenceAnchor->SetRelativeLocation(FVector(45.0f, -85.0f, 4.0f));

    RightTubeReferenceAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("RightTubeReferenceAnchor"));
    RightTubeReferenceAnchor->SetupAttachment(RaftContextAnchor);
    RightTubeReferenceAnchor->SetRelativeLocation(FVector(45.0f, 85.0f, 4.0f));

    PassengerSilhouetteAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("PassengerSilhouetteAnchor"));
    PassengerSilhouetteAnchor->SetupAttachment(RaftContextAnchor);
    PassengerSilhouetteAnchor->SetRelativeLocation(FVector(70.0f, 0.0f, 50.0f));

    GuideCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("GuideCamera"));
    GuideCamera->SetupAttachment(CameraImpactAnchor);
    GuideCamera->SetRelativeLocation(FVector::ZeroVector);
    GuideCamera->bUsePawnControlRotation = true;
    GuideCamera->SetFieldOfView(90.0f);
}

void ARaftSimGuidePawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateComfortCamera(DeltaSeconds);
}

void ARaftSimGuidePawn::ApplyGuideCameraSettings(const FRaftSimGuideCameraSettings& NewSettings)
{
    CameraSettings = NewSettings;
    UpdateComfortCamera(0.0f);
}

void ARaftSimGuidePawn::RecenterSeatedView()
{
    if (!CameraSettings.bEnableSeatedRecenter || !ViewOriginAnchor)
    {
        return;
    }

    ViewOriginAnchor->SetRelativeLocation(FVector::ZeroVector);
    ViewOriginAnchor->SetRelativeRotation(FRotator::ZeroRotator);
    CameraRuntimeState.bSeatedViewRecentered = true;
}

void ARaftSimGuidePawn::SetAccessibilityComfortMode(bool bEnabled)
{
    CameraRuntimeState.bAccessibilityComfortMode = bEnabled;
    UpdateComfortCamera(0.0f);
}

void ARaftSimGuidePawn::ApplyRaftImpactCue(FVector LocalOffsetCm, FRotator LocalRotation, float NormalizedIntensity)
{
    const float ClampedIntensity = FMath::Clamp(NormalizedIntensity, 0.0f, 1.0f);
    const float EffectiveIntensity = GetEffectiveMotionIntensity() * ClampedIntensity;

    if (CameraSettings.bEnableImpactFiltering)
    {
        CameraRuntimeState.TargetImpactOffsetCm = LocalOffsetCm * EffectiveIntensity;
        CameraRuntimeState.TargetImpactRotation = LocalRotation * EffectiveIntensity;
    }
    else
    {
        CameraRuntimeState.FilteredImpactOffsetCm = LocalOffsetCm * EffectiveIntensity;
        CameraRuntimeState.FilteredImpactRotation = LocalRotation * EffectiveIntensity;
        CameraRuntimeState.TargetImpactOffsetCm = FVector::ZeroVector;
        CameraRuntimeState.TargetImpactRotation = FRotator::ZeroRotator;
    }

    if (CameraSettings.bEnableHapticImpactPulses && ClampedIntensity >= CameraSettings.HapticImpactThreshold)
    {
        CameraRuntimeState.PendingHapticAmplitude = FMath::Max(CameraRuntimeState.PendingHapticAmplitude, ClampedIntensity);
    }
}

float ARaftSimGuidePawn::ConsumePendingHapticPulse()
{
    const float Pulse = CameraRuntimeState.PendingHapticAmplitude;
    CameraRuntimeState.PendingHapticAmplitude = 0.0f;
    return Pulse;
}

float ARaftSimGuidePawn::GetEffectiveMotionIntensity() const
{
    const float BaseIntensity = FMath::Clamp(CameraSettings.MotionIntensity, 0.0f, 1.0f);
    if (!CameraRuntimeState.bAccessibilityComfortMode)
    {
        return BaseIntensity;
    }
    return BaseIntensity * FMath::Clamp(CameraSettings.AccessibilityMotionScale, 0.0f, 1.0f);
}

void ARaftSimGuidePawn::UpdateComfortCamera(float DeltaSeconds)
{
    const float FilterSpeed = FMath::Max(CameraSettings.ImpactFilterSpeed, 0.0f);

    if (DeltaSeconds > 0.0f && CameraSettings.bEnableImpactFiltering)
    {
        CameraRuntimeState.FilteredImpactOffsetCm = FMath::VInterpTo(
            CameraRuntimeState.FilteredImpactOffsetCm,
            CameraRuntimeState.TargetImpactOffsetCm,
            DeltaSeconds,
            FilterSpeed
        );
        CameraRuntimeState.FilteredImpactRotation = FMath::RInterpTo(
            CameraRuntimeState.FilteredImpactRotation,
            CameraRuntimeState.TargetImpactRotation,
            DeltaSeconds,
            FilterSpeed
        );
        CameraRuntimeState.TargetImpactOffsetCm = FMath::VInterpTo(
            CameraRuntimeState.TargetImpactOffsetCm,
            FVector::ZeroVector,
            DeltaSeconds,
            FilterSpeed * 0.5f
        );
        CameraRuntimeState.TargetImpactRotation = FMath::RInterpTo(
            CameraRuntimeState.TargetImpactRotation,
            FRotator::ZeroRotator,
            DeltaSeconds,
            FilterSpeed * 0.5f
        );
    }

    FRotator StabilizedRotation = CameraRuntimeState.FilteredImpactRotation;
    if (CameraSettings.bEnableHorizonStabilization)
    {
        const float Stabilization = FMath::Clamp(CameraSettings.HorizonStabilizationStrength, 0.0f, 1.0f);
        StabilizedRotation.Pitch *= 1.0f - Stabilization;
        StabilizedRotation.Roll *= 1.0f - Stabilization;
    }

    if (CameraImpactAnchor)
    {
        CameraImpactAnchor->SetRelativeLocation(CameraRuntimeState.FilteredImpactOffsetCm);
        CameraImpactAnchor->SetRelativeRotation(StabilizedRotation);
    }

    const float ImpactMagnitude = FMath::Clamp(
        CameraRuntimeState.FilteredImpactOffsetCm.Size() / 20.0f,
        0.0f,
        1.0f
    );
    CameraRuntimeState.CurrentVignetteStrength = CameraSettings.bEnableVRComfortVignette
        ? CameraSettings.ComfortVignetteStrength * ImpactMagnitude
        : 0.0f;
}
