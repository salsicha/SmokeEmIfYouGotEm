#include "RaftSimGuidePlayerController.h"

#include "Blueprint/UserWidget.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerInput.h"
#include "HighResScreenshot.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRunHudWidget.h"
#include "RaftSimRunManager.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimTrainingDirector.h"
#include "RaftSimVerticalSliceFrontend.h"

namespace
{
template <typename T>
T* FindActor(UWorld* World)
{
    if (World != nullptr)
    {
        if (TActorIterator<T> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}
}

void ARaftSimGuidePlayerController::BeginPlay()
{
    Super::BeginPlay();

    RunHud = CreateWidget<URaftSimRunHudWidget>(this, URaftSimRunHudWidget::StaticClass());
    if (RunHud != nullptr)
    {
        RunHud->AddToViewport();
        if (const URaftSimSaveSubsystem* Save = GetGameInstance()
                ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
        {
            FRaftSimCareerScenarioDefinition Scenario;
            if (Save->GetSave() != nullptr && URaftSimProgressionLibrary::FindScenario(
                    Save->GetSave()->Selection.ScenarioId, Scenario))
            {
                RunHud->BeginScenarioPresentation(Scenario.DisplayName, Scenario.Briefing);
            }
        }
    }
    // Game input drives the raft; the HUD is non-interactive.
    SetInputMode(FInputModeGameOnly());
    SetShowMouseCursor(false);
    PrimaryActorTick.bTickEvenWhenPaused = true;
    ApplySavedSettings();
    if (ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(GetPawn()))
    {
        Guide->BeginScenarioCameraPresentation();
    }
}

void ARaftSimGuidePlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    if (InputComponent == nullptr)
    {
        return;
    }
    FKey PauseKey = EKeys::Escape;
    if (const URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        if (Save->GetSave() != nullptr)
        {
            if (const FName* SavedKey = Save->GetSave()->InputBindings.Find(TEXT("Pause")))
            {
                const FKey Candidate(*SavedKey);
                if (Candidate.IsValid())
                {
                    PauseKey = Candidate;
                }
            }
        }
    }
    InputComponent->BindKey(PauseKey, IE_Pressed, this, &ARaftSimGuidePlayerController::TogglePauseMenu);
    InputComponent->BindKey(EKeys::Gamepad_Special_Right, IE_Pressed, this, &ARaftSimGuidePlayerController::TogglePauseMenu);
    InputComponent->BindKey(EKeys::Tab, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleCommandWheel);
    InputComponent->BindKey(EKeys::Tab, IE_Released, this, &ARaftSimGuidePlayerController::CloseCommandWheel);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Left, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleCommandWheel);
    InputComponent->BindKey(EKeys::M, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleScoutBoard);
    InputComponent->BindKey(EKeys::Gamepad_DPad_Down, IE_Pressed, this, &ARaftSimGuidePlayerController::HandleGamepadDPadDown);
    InputComponent->BindKey(EKeys::P, IE_Pressed, this, &ARaftSimGuidePlayerController::TogglePhotoMode);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Top, IE_Pressed, this, &ARaftSimGuidePlayerController::TogglePhotoMode);
    InputComponent->BindKey(EKeys::F9, IE_Pressed, this, &ARaftSimGuidePlayerController::CapturePhoto);
    InputComponent->BindKey(EKeys::Gamepad_RightTrigger, IE_Pressed, this, &ARaftSimGuidePlayerController::CapturePhoto);
    InputComponent->BindKey(EKeys::BackSpace, IE_Pressed, this, &ARaftSimGuidePlayerController::RestartCheckpoint);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Bottom, IE_Pressed, this, &ARaftSimGuidePlayerController::HandleGamepadFaceButtonBottom);
    InputComponent->BindKey(EKeys::Home, IE_Pressed, this, &ARaftSimGuidePlayerController::ReturnToMainMenu);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Right, IE_Pressed, this, &ARaftSimGuidePlayerController::ReturnToMainMenu);
    InputComponent->BindKey(EKeys::V, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleReview);
    InputComponent->BindKey(EKeys::Gamepad_LeftTrigger, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleReview);
    InputComponent->BindKey(EKeys::C, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleChaseCamera);
    InputComponent->BindKey(EKeys::Gamepad_RightThumbstick, IE_Pressed, this, &ARaftSimGuidePlayerController::ToggleChaseCamera);
    InputComponent->BindKey(EKeys::T, IE_Pressed, this, &ARaftSimGuidePlayerController::CycleWeatherVariant);
    InputComponent->BindKey(EKeys::Gamepad_LeftThumbstick, IE_Pressed, this, &ARaftSimGuidePlayerController::CycleWeatherVariant);
    InputComponent->BindKey(EKeys::One, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandForward);
    InputComponent->BindKey(EKeys::Two, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandBackward);
    InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandLeft);
    InputComponent->BindKey(EKeys::Four, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandRight);
    InputComponent->BindKey(EKeys::Five, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandStop);
    InputComponent->BindKey(EKeys::Gamepad_DPad_Up, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandForward);
    InputComponent->BindKey(EKeys::Gamepad_DPad_Left, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandLeft);
    InputComponent->BindKey(EKeys::Gamepad_DPad_Right, IE_Pressed, this, &ARaftSimGuidePlayerController::CommandRight);
    InputComponent->BindAxisKey(EKeys::MouseX, this, &ARaftSimGuidePlayerController::PhotoLookYaw);
    InputComponent->BindAxisKey(EKeys::MouseY, this, &ARaftSimGuidePlayerController::PhotoLookPitch);
    InputComponent->BindAxisKey(EKeys::Gamepad_RightX, this, &ARaftSimGuidePlayerController::PhotoLookYaw);
    InputComponent->BindAxisKey(EKeys::Gamepad_RightY, this, &ARaftSimGuidePlayerController::PhotoLookPitch);
}

void ARaftSimGuidePlayerController::ApplySavedSettings()
{
    const URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(GetPawn());
    if (Save == nullptr || Save->GetSave() == nullptr || Guide == nullptr)
    {
        return;
    }
    const auto& S = Save->GetSave()->Settings;
    FRaftSimGuideCameraSettings Camera = Guide->GetCameraSettings();
    Camera.MotionIntensity = S.bCameraShakeEnabled ? S.MotionIntensity * S.CameraShakeScale : 0.0f;
    Camera.bEnableVRComfortVignette = S.bVignetteEnabled;
    Camera.ComfortVignetteStrength = S.VignetteStrength;
    Guide->ApplyGuideCameraSettings(Camera);
    Guide->SetAccessibilityComfortMode(S.AssistLevel == ERaftSimAssistLevel::Relaxed);
    Guide->SetChaseCameraAllowed(Save->GetSave()->ActiveGameMode == ERaftSimGameMode::FreeRun);
    for (const TPair<FName, FName>& Binding : Save->GetSave()->InputBindings)
    {
        Guide->ApplyRuntimeKeyBinding(Binding.Key, FKey(Binding.Value));
    }
}

void ARaftSimGuidePlayerController::ToggleChaseCamera()
{
    if (bPauseVisible || bScoutVisible || bPhotoMode)
    {
        return;
    }
    if (ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(GetPawn()))
    {
        if (Guide->ToggleChaseCamera() && RunHud)
        {
            RunHud->ShowSubtitle(
                Guide->IsChaseCameraActive()
                    ? NSLOCTEXT("RaftSim", "ChaseCameraOn", "Free Run chase camera")
                    : NSLOCTEXT("RaftSim", "GuideCameraOn", "Stern guide camera"),
                1.8f);
        }
    }
}

void ARaftSimGuidePlayerController::CycleWeatherVariant()
{
    if (bPauseVisible || bScoutVisible || bPhotoMode)
    {
        return;
    }
    if (ARaftSimPresentationDirector* Presentation =
            FindActor<ARaftSimPresentationDirector>(GetWorld()))
    {
        Presentation->CycleWeatherVariant();
        if (RunHud)
        {
            RunHud->ShowSubtitle(FText::Format(
                NSLOCTEXT("RaftSim", "WeatherChanged", "Weather: {0}"),
                Presentation->GetWeatherDisplayName()), 2.2f);
        }
    }
}

void ARaftSimGuidePlayerController::PlayerTick(float DeltaTime)
{
    Super::PlayerTick(DeltaTime);
    if (bRestoreHudAfterCapture && RunHud != nullptr)
    {
        RunHud->SetVisibility(ESlateVisibility::HitTestInvisible);
        bRestoreHudAfterCapture = false;
    }
}

void ARaftSimGuidePlayerController::TogglePauseMenu()
{
    if (bPhotoMode)
    {
        TogglePhotoMode();
        return;
    }
    bPauseVisible = !bPauseVisible;
    UGameplayStatics::SetGamePaused(this, bPauseVisible);
    if (RunHud)
    {
        RunHud->ShowOverlay(bPauseVisible ? ERaftSimHudOverlay::Pause : ERaftSimHudOverlay::None);
    }
    if (bPauseVisible)
    {
        SetInputMode(FInputModeGameAndUI());
    }
    else
    {
        SetInputMode(FInputModeGameOnly());
    }
    SetShowMouseCursor(bPauseVisible);
}

void ARaftSimGuidePlayerController::ToggleScoutBoard()
{
    if (bPauseVisible || bPhotoMode)
    {
        return;
    }
    bScoutVisible = !bScoutVisible;
    UGameplayStatics::SetGamePaused(this, bScoutVisible);
    if (RunHud)
    {
        RunHud->ShowOverlay(bScoutVisible ? ERaftSimHudOverlay::ScoutBoard : ERaftSimHudOverlay::None);
    }
    if (bScoutVisible)
    {
        if (ARaftSimTrainingDirector* Training = FindActor<ARaftSimTrainingDirector>(GetWorld()))
        {
            Training->NotifyScoutReviewed();
        }
    }
}

void ARaftSimGuidePlayerController::ToggleCommandWheel()
{
    if (bPauseVisible || bScoutVisible || bPhotoMode)
    {
        return;
    }
    bCommandWheelVisible = !bCommandWheelVisible;
    if (RunHud)
    {
        RunHud->ShowOverlay(bCommandWheelVisible ? ERaftSimHudOverlay::CommandWheel : ERaftSimHudOverlay::None);
    }
}

void ARaftSimGuidePlayerController::CloseCommandWheel()
{
    const URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    const bool bHold = Save && Save->GetSave() &&
        Save->GetSave()->Settings.CommandWheelStyle == ERaftSimInteractionStyle::Hold;
    if (bHold && bCommandWheelVisible)
    {
        bCommandWheelVisible = false;
        if (RunHud) RunHud->ShowOverlay(ERaftSimHudOverlay::None);
    }
}

void ARaftSimGuidePlayerController::HandleGamepadDPadDown()
{
    if (bCommandWheelVisible)
    {
        CommandBackward();
        return;
    }
    ToggleScoutBoard();
}

void ARaftSimGuidePlayerController::HandleGamepadFaceButtonBottom()
{
    if (bCommandWheelVisible)
    {
        CommandStop();
        return;
    }
    RestartCheckpoint();
}

void ARaftSimGuidePlayerController::TogglePhotoMode()
{
    if (!bPhotoMode && bScoutVisible)
    {
        ToggleScoutBoard();
    }
    bPhotoMode = !bPhotoMode;
    bPauseVisible = false;
    UGameplayStatics::SetGamePaused(this, bPhotoMode);
    if (RunHud)
    {
        RunHud->ShowOverlay(bPhotoMode ? ERaftSimHudOverlay::PhotoMode : ERaftSimHudOverlay::None);
    }
    SetShowMouseCursor(false);
    SetInputMode(FInputModeGameOnly());
}

void ARaftSimGuidePlayerController::ToggleReview()
{
    ARaftSimRunManager* Run = FindActor<ARaftSimRunManager>(GetWorld());
    if (Run == nullptr || Run->GetRunState() != ERaftSimRunState::Finished)
    {
        return;
    }
    bReviewVisible = !bReviewVisible;
    if (RunHud)
    {
        RunHud->ShowOverlay(bReviewVisible ? ERaftSimHudOverlay::ReplayReview : ERaftSimHudOverlay::None);
    }
}

void ARaftSimGuidePlayerController::RestartCheckpoint()
{
    if (ARaftSimRunManager* Run = FindActor<ARaftSimRunManager>(GetWorld()))
    {
        UGameplayStatics::SetGamePaused(this, false);
        bPauseVisible = bScoutVisible = bPhotoMode = false;
        Run->RestartRun();
        if (RunHud) RunHud->ShowOverlay(ERaftSimHudOverlay::None);
        SetInputMode(FInputModeGameOnly());
        SetShowMouseCursor(false);
    }
}

void ARaftSimGuidePlayerController::ReturnToMainMenu()
{
    const ARaftSimRunManager* Run = FindActor<ARaftSimRunManager>(GetWorld());
    if (!bPauseVisible && (Run == nullptr || Run->GetRunState() != ERaftSimRunState::Finished))
    {
        return;
    }
    UGameplayStatics::SetGamePaused(this, false);
    UGameplayStatics::OpenLevel(this, TEXT("/Game/RaftSim/Maps/L_RaftSimBoot"));
}

void ARaftSimGuidePlayerController::CapturePhoto()
{
    if (!bPhotoMode)
    {
        return;
    }
    if (RunHud)
    {
        RunHud->SetVisibility(ESlateVisibility::Collapsed);
        bRestoreHudAfterCapture = true;
    }
    FScreenshotRequest::RequestScreenshot(TEXT("RaftSimPhoto.png"), false, false);
}

void ARaftSimGuidePlayerController::ApplyCommand(int32 CommandIndex)
{
    ARaftSimRaftActor* Raft = FindActor<ARaftSimRaftActor>(GetWorld());
    if (Raft == nullptr)
    {
        return;
    }
    static const ERaftSimCrewCommand Commands[] = {
        ERaftSimCrewCommand::AllForward, ERaftSimCrewCommand::AllBackward,
        ERaftSimCrewCommand::TurnLeft, ERaftSimCrewCommand::TurnRight,
        ERaftSimCrewCommand::Stop};
    if (CommandIndex >= 0 && CommandIndex < UE_ARRAY_COUNT(Commands))
    {
        Raft->IssueCrewCommand(Commands[CommandIndex]);
        if (RunHud)
        {
            RunHud->ShowSubtitle(FText::FromString(FString::Printf(
                TEXT("Guide command: %d"), CommandIndex + 1)), 1.5f);
        }
    }
}

void ARaftSimGuidePlayerController::CommandForward() { ApplyCommand(0); }
void ARaftSimGuidePlayerController::CommandBackward() { ApplyCommand(1); }
void ARaftSimGuidePlayerController::CommandLeft() { ApplyCommand(2); }
void ARaftSimGuidePlayerController::CommandRight() { ApplyCommand(3); }
void ARaftSimGuidePlayerController::CommandStop() { ApplyCommand(4); }

void ARaftSimGuidePlayerController::PhotoLookYaw(float Value)
{
    if (bPhotoMode && FMath::Abs(Value) > KINDA_SMALL_NUMBER)
    {
        AddYawInput(Value * 0.5f);
    }
}

void ARaftSimGuidePlayerController::PhotoLookPitch(float Value)
{
    if (bPhotoMode && FMath::Abs(Value) > KINDA_SMALL_NUMBER)
    {
        AddPitchInput(Value * -0.5f);
    }
}
