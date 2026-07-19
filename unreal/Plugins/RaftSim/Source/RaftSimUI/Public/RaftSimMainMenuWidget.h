#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "RaftSimVerticalSliceFrontend.h"

#include "RaftSimMainMenuWidget.generated.h"

class UButton;
class UTextBlock;
class UVerticalBox;

/**
 * Complete programmatic front end. It keeps every path keyboard/gamepad
 * focusable and uses the versioned save as the single source of truth.
 */
UCLASS()
class RAFTSIMUI_API URaftSimMainMenuWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Frontend")
    ERaftSimGameMode GetSelectedMode() const { return SelectedMode; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Frontend")
    FName GetSelectedScenarioId() const;

    /** Focus target for keyboard/gamepad UI-only input. */
    UWidget* GetDefaultFocusWidget() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    void BuildWidgetTree();

    UFUNCTION()
    void HandleStart();
    UFUNCTION()
    void HandleCycleMode();
    UFUNCTION()
    void HandlePreviousScenario();
    UFUNCTION()
    void HandleNextScenario();

    UFUNCTION()
    void HandleToggleSubtitles();
    UFUNCTION()
    void HandleCycleUiScale();
    UFUNCTION()
    void HandleCycleColorCues();
    UFUNCTION()
    void HandleCycleMotion();
    UFUNCTION()
    void HandleCycleInteraction();
    UFUNCTION()
    void HandleCycleAssist();
    UFUNCTION()
    void HandleToggleGhostRoute();
    UFUNCTION()
    void HandleRebindPause();
    UFUNCTION()
    void HandleRestoreDefaults();
    UFUNCTION()
    void HandleCredits();
    UFUNCTION()
    void HandleLegal();

    UFUNCTION()
    void HandleQuit();

    void RefreshFromSave();
    void SelectNextScenario(int32 Direction);
    bool IsScenarioVisible(int32 Index) const;
    UButton* MakeMenuButton(UVerticalBox* Parent, const FText& Label, FName ClickHandlerName);

    UPROPERTY()
    TObjectPtr<UTextBlock> ModeText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ScenarioText;

    UPROPERTY()
    TObjectPtr<UTextBlock> BriefingText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ProfileText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SettingsSummaryText;

    UPROPERTY()
    TObjectPtr<UTextBlock> InformationText;

    UPROPERTY()
    TObjectPtr<UButton> StartButton;

    TArray<FRaftSimCareerScenarioDefinition> ScenarioCatalog;
    ERaftSimGameMode SelectedMode = ERaftSimGameMode::TrainingEddy;
    int32 SelectedScenarioIndex = 0;
    bool bModeInitialized = false;

};
