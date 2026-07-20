#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"

#include "RaftSimBootGameMode.generated.h"

class URaftSimMainMenuWidget;

/** Player controller for the boot/menu level: creates the main menu and enters UI input mode. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimFrontendPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

protected:
    UPROPERTY()
    TObjectPtr<URaftSimMainMenuWidget> MainMenuWidget;
};

/** Game mode for L_RaftSimBoot: no pawn, menu-driving player controller. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimBootGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ARaftSimBootGameMode();
    virtual void BeginPlay() override;
};
