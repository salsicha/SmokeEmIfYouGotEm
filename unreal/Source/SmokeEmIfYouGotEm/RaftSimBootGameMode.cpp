#include "RaftSimBootGameMode.h"

#include "Blueprint/UserWidget.h"
#include "GameFramework/SpectatorPawn.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimContentLockDirector.h"
#include "RaftSimMainMenuWidget.h"

void ARaftSimFrontendPlayerController::BeginPlay()
{
    Super::BeginPlay();

    if (ARaftSimContentLockDirector::IsPackagedRegressionRequested() ||
        ARaftSimContentLockDirector::IsReleaseCandidateQARequested() ||
        ARaftSimContentLockDirector::IsFreshProfileQARequested() ||
        ARaftSimContentLockDirector::IsPerformanceCaptureRequested())
    {
        return;
    }

    MainMenuWidget = CreateWidget<URaftSimMainMenuWidget>(this, URaftSimMainMenuWidget::StaticClass());
    if (MainMenuWidget != nullptr)
    {
        MainMenuWidget->AddToViewport();
        FInputModeUIOnly InputMode;
        if (UWidget* FocusTarget = MainMenuWidget->GetDefaultFocusWidget())
        {
            InputMode.SetWidgetToFocus(FocusTarget->TakeWidget());
        }
        SetInputMode(InputMode);
        SetShowMouseCursor(true);
    }
}

ARaftSimBootGameMode::ARaftSimBootGameMode()
{
    PlayerControllerClass = ARaftSimFrontendPlayerController::StaticClass();
    DefaultPawnClass = ASpectatorPawn::StaticClass();
}

void ARaftSimBootGameMode::BeginPlay()
{
    Super::BeginPlay();
    if (ARaftSimContentLockDirector::IsPerformanceCaptureRequested())
    {
        FString TravelMap;
        if (FParse::Value(
                FCommandLine::Get(), TEXT("RaftSimPerformanceTravelMap="), TravelMap) &&
            !TravelMap.IsEmpty())
        {
            UGameplayStatics::OpenLevel(this, FName(*TravelMap));
            return;
        }
    }
    if (ARaftSimContentLockDirector::IsPackagedRegressionRequested() ||
        ARaftSimContentLockDirector::IsReleaseCandidateQARequested() ||
        ARaftSimContentLockDirector::IsFreshProfileQARequested() ||
        ARaftSimContentLockDirector::IsPerformanceCaptureRequested())
    {
        GetWorld()->SpawnActor<ARaftSimContentLockDirector>(
            ARaftSimContentLockDirector::StaticClass(), FTransform::Identity);
    }
}
