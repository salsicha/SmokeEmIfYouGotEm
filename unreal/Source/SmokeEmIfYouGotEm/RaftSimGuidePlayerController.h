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
    virtual void SetupInputComponent() override;
    virtual void PlayerTick(float DeltaTime) override;

    URaftSimRunHudWidget* GetRunHud() const { return RunHud; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Shell")
    bool IsPhotoModeActive() const { return bPhotoMode; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Shell")
    bool IsScoutBoardVisible() const { return bScoutVisible; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Shell")
    void TogglePauseMenu();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Shell")
    void ToggleScoutBoard();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Shell")
    void TogglePhotoMode();

protected:
    UPROPERTY()
    TObjectPtr<URaftSimRunHudWidget> RunHud;

private:
    void ToggleCommandWheel();
    void CloseCommandWheel();
    void HandleGamepadDPadDown();
    void HandleGamepadFaceButtonBottom();
    void ToggleReview();
    void RestartCheckpoint();
    void ReturnToMainMenu();
    void CapturePhoto();
    void CommandForward();
    void CommandBackward();
    void CommandLeft();
    void CommandRight();
    void CommandStop();
    void ApplyCommand(int32 CommandIndex);
    void PhotoLookYaw(float Value);
    void PhotoLookPitch(float Value);
    void ApplySavedSettings();

    bool bPauseVisible = false;
    bool bScoutVisible = false;
    bool bCommandWheelVisible = false;
    bool bPhotoMode = false;
    bool bReviewVisible = false;
    bool bRestoreHudAfterCapture = false;
};
