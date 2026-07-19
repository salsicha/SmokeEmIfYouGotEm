#include "RaftSimGuidePawn.h"

#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "EngineUtils.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "RaftSimInputActions.h"
#include "RaftSimRaftActor.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
template <typename T>
T* LoadGeneratedInputAsset(const TCHAR* Path)
{
    ConstructorHelpers::FObjectFinderOptional<T> Finder(Path);
    return Finder.Succeeded() ? Finder.Get() : nullptr;
}
}

ARaftSimGuidePawn::ARaftSimGuidePawn()
{
    PrimaryActorTick.bCanEverTick = true;
    AutoPossessPlayer = EAutoReceiveInput::Player0;

    DefaultMappingContext = LoadGeneratedInputAsset<UInputMappingContext>(
        TEXT("/Game/RaftSim/Input/IMC_RaftSimDefault.IMC_RaftSimDefault"));
    PaddleStrokeAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_PaddleStroke.IA_PaddleStroke"));
    PaddleDrawAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_PaddleDraw.IA_PaddleDraw"));
    LookAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_Look.IA_Look"));
    HighSideAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_HighSide.IA_HighSide"));
    RescueTargetSelectAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_RescueTargetSelect.IA_RescueTargetSelect"));
    RescueReachAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_RescueReachGrab.IA_RescueReachGrab"));
    RescueThrowLineAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_RescueThrowLine.IA_RescueThrowLine"));
    ReseatCrewAction = LoadGeneratedInputAsset<UInputAction>(
        TEXT("/Game/RaftSim/Input/IA_ReseatCrew.IA_ReseatCrew"));

    // Shipping fallback: bind the already-cooked rescue actions even when an
    // older IMC asset is present. The editor bootstrap mirrors these mappings
    // for future regeneration; packaged play does not depend on that command.
    auto MapRescueKey = [this](UInputAction* Action, const FKey& Key, bool bNegate = false)
    {
        if (!DefaultMappingContext || !Action)
        {
            return;
        }
        for (const FEnhancedActionKeyMapping& Existing : DefaultMappingContext->GetMappings())
        {
            if (Existing.Action == Action && Existing.Key == Key)
            {
                return;
            }
        }
        FEnhancedActionKeyMapping& Mapping = DefaultMappingContext->MapKey(Action, Key);
        if (bNegate)
        {
            Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));
        }
    };
    MapRescueKey(RescueTargetSelectAction, EKeys::MouseWheelAxis);
    MapRescueKey(RescueReachAction, EKeys::E);
    MapRescueKey(RescueThrowLineAction, EKeys::R);
    MapRescueKey(ReseatCrewAction, EKeys::F);
    MapRescueKey(RescueTargetSelectAction, EKeys::Gamepad_LeftShoulder, true);
    MapRescueKey(RescueTargetSelectAction, EKeys::Gamepad_RightShoulder);
    MapRescueKey(RescueReachAction, EKeys::Gamepad_FaceButton_Bottom);
    MapRescueKey(RescueThrowLineAction, EKeys::Gamepad_RightTrigger);
    MapRescueKey(ReseatCrewAction, EKeys::Gamepad_FaceButton_Right);
    for (const TCHAR* CommandPath : {
             TEXT("/Game/RaftSim/Input/IA_GuideCommandForwardPaddle.IA_GuideCommandForwardPaddle"),
             TEXT("/Game/RaftSim/Input/IA_GuideCommandBackPaddle.IA_GuideCommandBackPaddle"),
             TEXT("/Game/RaftSim/Input/IA_GuideCommandLeftPaddle.IA_GuideCommandLeftPaddle"),
             TEXT("/Game/RaftSim/Input/IA_GuideCommandRightPaddle.IA_GuideCommandRightPaddle"),
             TEXT("/Game/RaftSim/Input/IA_GuideCommandStop.IA_GuideCommandStop") })
    {
        if (UInputAction* CommandAction = LoadGeneratedInputAsset<UInputAction>(CommandPath))
        {
            GuideCommandActions.Add(CommandAction);
        }
    }

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
    UpdateSwimmingAndRescueAim();
}

void ARaftSimGuidePawn::UpdateSwimmingAndRescueAim()
{
    ARaftSimRaftActor* Raft = ResolveRaft();
    if (!Raft)
    {
        return;
    }
    Raft->AimRescue(GuideCamera ? GuideCamera->GetForwardVector() : GetActorForwardVector());
    FVector GuideSwimmerCm;
    if (Raft->GetSwimmerWorldPosition(TEXT("guide"), GuideSwimmerCm))
    {
        if (MobilityMode == ERaftSimGuideMobilityMode::InRaft)
        {
            DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        }
        MobilityMode = ERaftSimGuideMobilityMode::Swimming;
        SetActorLocation(GuideSwimmerCm + FVector(0.0f, 0.0f, 18.0f));
    }
    else if (MobilityMode != ERaftSimGuideMobilityMode::InRaft)
    {
        MobilityMode = ERaftSimGuideMobilityMode::Reboarding;
        AttachToComponent(
            Raft->GetSternSeatAttachPoint(),
            FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        MobilityMode = ERaftSimGuideMobilityMode::InRaft;
    }
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

bool ARaftSimGuidePawn::HasCompleteRescueInputBindings() const
{
    if (!DefaultMappingContext || !RescueTargetSelectAction || !RescueReachAction ||
        !RescueThrowLineAction || !ReseatCrewAction)
    {
        return false;
    }
    TSet<const UInputAction*> Bound;
    for (const FEnhancedActionKeyMapping& Mapping : DefaultMappingContext->GetMappings())
    {
        if (Mapping.Action == RescueTargetSelectAction || Mapping.Action == RescueReachAction ||
            Mapping.Action == RescueThrowLineAction || Mapping.Action == ReseatCrewAction)
        {
            Bound.Add(Mapping.Action);
        }
    }
    return Bound.Num() == 4;
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

void ARaftSimGuidePawn::BeginPlay()
{
    Super::BeginPlay();

    if (const APlayerController* PlayerController = Cast<APlayerController>(GetController()))
    {
        if (UEnhancedInputLocalPlayerSubsystem* InputSubsystem =
                ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(
                    PlayerController->GetLocalPlayer()))
        {
            if (DefaultMappingContext != nullptr)
            {
                InputSubsystem->AddMappingContext(DefaultMappingContext, 0);
            }
        }
    }

    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        AttachToComponent(
            Raft->GetSternSeatAttachPoint(),
            FAttachmentTransformRules::SnapToTargetNotIncludingScale);
    }
}

ARaftSimRaftActor* ARaftSimGuidePawn::ResolveRaft()
{
    if (AttachedRaft != nullptr)
    {
        return AttachedRaft;
    }
    if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
    {
        AttachedRaft = *It;
    }
    return AttachedRaft;
}

void ARaftSimGuidePawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(PlayerInputComponent);
    if (EnhancedInput == nullptr)
    {
        return;
    }

    if (PaddleStrokeAction != nullptr)
    {
        EnhancedInput->BindAction(
            PaddleStrokeAction, ETriggerEvent::Triggered, this,
            &ARaftSimGuidePawn::HandlePaddleStroke);
    }
    if (PaddleDrawAction != nullptr)
    {
        EnhancedInput->BindAction(
            PaddleDrawAction, ETriggerEvent::Triggered, this,
            &ARaftSimGuidePawn::HandleTurnStroke);
    }
    if (LookAction != nullptr)
    {
        EnhancedInput->BindAction(
            LookAction, ETriggerEvent::Triggered, this, &ARaftSimGuidePawn::HandleLook);
    }
    if (HighSideAction != nullptr)
    {
        EnhancedInput->BindAction(
            HighSideAction, ETriggerEvent::Started, this, &ARaftSimGuidePawn::HandleHighSide);
    }
    if (RescueTargetSelectAction != nullptr)
    {
        EnhancedInput->BindAction(
            RescueTargetSelectAction, ETriggerEvent::Triggered, this,
            &ARaftSimGuidePawn::HandleRescueTargetSelect);
    }
    if (RescueReachAction != nullptr)
    {
        EnhancedInput->BindAction(
            RescueReachAction, ETriggerEvent::Started, this,
            &ARaftSimGuidePawn::HandleRescueReach);
    }
    if (RescueThrowLineAction != nullptr)
    {
        EnhancedInput->BindAction(
            RescueThrowLineAction, ETriggerEvent::Started, this,
            &ARaftSimGuidePawn::HandleRescueThrowLine);
    }
    if (ReseatCrewAction != nullptr)
    {
        EnhancedInput->BindAction(
            ReseatCrewAction, ETriggerEvent::Started, this,
            &ARaftSimGuidePawn::HandleReseatCrew);
    }
    for (const TObjectPtr<UInputAction>& CommandAction : GuideCommandActions)
    {
        if (CommandAction != nullptr)
        {
            EnhancedInput->BindActionValueLambda(
                CommandAction, ETriggerEvent::Started,
                [this, ActionName = CommandAction.GetFName()](const FInputActionValue&)
                { HandleGuideCommand(ActionName); });
        }
    }
}

void ARaftSimGuidePawn::HandlePaddleStroke(const FInputActionValue& Value)
{
    const float Now = GetWorld()->GetTimeSeconds();
    if (Now - LastStrokeTimeSeconds < StrokeCooldownSeconds)
    {
        return;
    }
    const FVector Axis = Value.Get<FVector>();
    if (FMath::Abs(Axis.X) < 0.2f)
    {
        return;
    }
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        LastStrokeTimeSeconds = Now;
        if (MobilityMode == ERaftSimGuideMobilityMode::Swimming)
        {
            const FVector SwimDirection = GuideCamera
                ? GuideCamera->GetForwardVector()
                : GetActorForwardVector();
            Raft->ApplySwimmerStroke(TEXT("guide"), SwimDirection * FMath::Sign(Axis.X));
            return;
        }
        Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both, Axis.X);
        ApplyRaftImpactCue(
            FVector(0.0f, 0.0f, -2.0f), FRotator(-0.6f * Axis.X, 0.0f, 0.0f), 0.18f);
    }
}

void ARaftSimGuidePawn::HandleTurnStroke(const FInputActionValue& Value)
{
    const FVector2D Axis = Value.Get<FVector2D>();
    if (FMath::Abs(Axis.X) < 0.2f)
    {
        return;
    }
    const float Now = GetWorld()->GetTimeSeconds();
    if (Now - LastStrokeTimeSeconds < StrokeCooldownSeconds)
    {
        return;
    }
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        LastStrokeTimeSeconds = Now;
        Raft->ApplyTurnStroke(Axis.X);
    }
}

void ARaftSimGuidePawn::HandleLook(const FInputActionValue& Value)
{
    const FVector2D Axis = Value.Get<FVector2D>();
    AddControllerYawInput(Axis.X);
    AddControllerPitchInput(Axis.Y);
}

void ARaftSimGuidePawn::HandleHighSide(const FInputActionValue&)
{
    ApplyRaftImpactCue(FVector(0.0f, 0.0f, -4.0f), FRotator::ZeroRotator, 0.4f);
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        // Context-sensitive: re-right a capsized raft, otherwise high-side to
        // the raft's current lean direction to fight the incoming roll.
        if (Raft->GetRaftMode() == ERaftSimRaftMode::Capsized)
        {
            Raft->RequestReflip();
        }
        else
        {
            const float Roll = Raft->GetActorRotation().Roll;
            Raft->HandleHighSideResponse(Roll >= 0.0f ? -1 : 1);
        }
    }
}

void ARaftSimGuidePawn::HandleGuideCommand(FName CommandActionName)
{
    ARaftSimRaftActor* Raft = ResolveRaft();
    if (Raft == nullptr)
    {
        return;
    }
    ERaftSimCrewCommand Command = ERaftSimCrewCommand::Rest;
    const FString Name = CommandActionName.ToString();
    if (Name.Contains(TEXT("ForwardPaddle"))) { Command = ERaftSimCrewCommand::AllForward; }
    else if (Name.Contains(TEXT("BackPaddle"))) { Command = ERaftSimCrewCommand::AllBackward; }
    else if (Name.Contains(TEXT("LeftPaddle"))) { Command = ERaftSimCrewCommand::TurnLeft; }
    else if (Name.Contains(TEXT("RightPaddle"))) { Command = ERaftSimCrewCommand::TurnRight; }
    else if (Name.Contains(TEXT("Stop"))) { Command = ERaftSimCrewCommand::Stop; }
    Raft->IssueCrewCommand(Command);
}

void ARaftSimGuidePawn::HandleRescueTargetSelect(const FInputActionValue& Value)
{
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        const float Direction = Value.Get<float>();
        if (FMath::Abs(Direction) >= 0.2f)
        {
            Raft->SelectRescueTarget(Direction);
        }
    }
}

void ARaftSimGuidePawn::HandleRescueReach(const FInputActionValue&)
{
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        const FRaftSimRescueInteractionState State = Raft->GetRescueInteractionState();
        const ERaftSimRescueMethod Method = State.DistanceMeters > 1.2f
            ? ERaftSimRescueMethod::PaddleGrab
            : ERaftSimRescueMethod::ReachGrab;
        if (!Raft->BeginRescue(Method) && Method == ERaftSimRescueMethod::ReachGrab)
        {
            Raft->BeginRescue(ERaftSimRescueMethod::PaddleGrab);
        }
    }
}

void ARaftSimGuidePawn::HandleRescueThrowLine(const FInputActionValue&)
{
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine);
    }
}

void ARaftSimGuidePawn::HandleReseatCrew(const FInputActionValue&)
{
    if (ARaftSimRaftActor* Raft = ResolveRaft())
    {
        Raft->RequestSelectedReentry();
    }
}
