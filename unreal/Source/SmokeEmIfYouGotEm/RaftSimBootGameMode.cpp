#include "RaftSimBootGameMode.h"

#include "Blueprint/UserWidget.h"
#include "GameFramework/SpectatorPawn.h"
#include "RaftSimContentLockDirector.h"
#include "RaftSimMainMenuWidget.h"

void ARaftSimFrontendPlayerController::BeginPlay()
{
    Super::BeginPlay();

    if (ARaftSimContentLockDirector::IsPackagedRegressionRequested())
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
    if (ARaftSimContentLockDirector::IsPackagedRegressionRequested())
    {
        GetWorld()->SpawnActor<ARaftSimContentLockDirector>(
            ARaftSimContentLockDirector::StaticClass(), FTransform::Identity);
    }
}
