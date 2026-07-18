#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"

#include "RaftSimGuidePlayerController.generated.h"

class URaftSimRunHudWidget;

/** In-run controller: creates the HUD and holds game input focus. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimGuidePlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

    URaftSimRunHudWidget* GetRunHud() const { return RunHud; }

protected:
    UPROPERTY()
    TObjectPtr<URaftSimRunHudWidget> RunHud;
};
