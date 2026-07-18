#include "RaftSimGuidePlayerController.h"

#include "Blueprint/UserWidget.h"
#include "RaftSimRunHudWidget.h"

void ARaftSimGuidePlayerController::BeginPlay()
{
    Super::BeginPlay();

    RunHud = CreateWidget<URaftSimRunHudWidget>(this, URaftSimRunHudWidget::StaticClass());
    if (RunHud != nullptr)
    {
        RunHud->AddToViewport();
    }
    // Game input drives the raft; the HUD is non-interactive.
    SetInputMode(FInputModeGameOnly());
    SetShowMouseCursor(false);
}
