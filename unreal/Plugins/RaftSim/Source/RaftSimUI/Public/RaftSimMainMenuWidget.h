#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "RaftSimVerticalSliceFrontend.h"

#include "RaftSimMainMenuWidget.generated.h"

class UAudioComponent;
class UButton;
class UTextBlock;
class UVerticalBox;
class USoundWaveProcedural;
class URaftSimMainMenuWidget;

/** The three screens of the programmatic front end. */
UENUM(BlueprintType)
enum class ERaftSimMenuScreen : uint8
{
    Main,
    Career,
    Settings
};

/**
 * One river button on the main screen: a catalogued run launched in a fixed
 * game mode. UButton::OnClicked carries no payload, so each button owns a
 * tiny proxy that knows which run it starts.
 */
UCLASS()
class RAFTSIMUI_API URaftSimMenuRunButton : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION()
    void HandleClicked();

    UPROPERTY()
    TWeakObjectPtr<URaftSimMainMenuWidget> Owner;

    UPROPERTY()
    FName ScenarioId;

    UPROPERTY()
    TObjectPtr<UButton> Button;

    ERaftSimGameMode Mode = ERaftSimGameMode::FreeRun;
};

/**
 * Complete programmatic front end. Main screen: one button per river run
 * plus Career, Settings and Quit. Career screen: the guided-descent mode and
 * section selector. Settings screen: accessibility, assists, bindings,
 * credits and legal. Every path stays keyboard/gamepad focusable and the
 * versioned save is the single source of truth.
 */
UCLASS()
class RAFTSIMUI_API URaftSimMainMenuWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Frontend")
    ERaftSimGameMode GetSelectedMode() const { return SelectedMode; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Frontend")
    FName GetSelectedScenarioId() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Frontend")
    ERaftSimMenuScreen GetActiveScreen() const { return ActiveScreen; }

    /** Shows one screen and moves keyboard/gamepad focus to its first button. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Frontend")
    void ShowScreen(ERaftSimMenuScreen Screen);

    /** Launches a catalogued run in the given mode (the river buttons' path). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Frontend")
    void StartScenario(FName ScenarioId, ERaftSimGameMode Mode);

    /** Number of river/run buttons on the main screen (review and tests). */
    int32 GetRunButtonCount() const { return RunButtons.Num(); }

    /** Focus target for keyboard/gamepad UI-only input. */
    UWidget* GetDefaultFocusWidget() const;

    /** The fronted menu of a world, if one is in its viewport. */
    static URaftSimMainMenuWidget* FindInWorld(UWorld* World);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnPreviewKeyDown(
        const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
    void BuildWidgetTree();
    void BuildRunButtons(UVerticalBox* Parent);

    UFUNCTION()
    void HandleStart();
    UFUNCTION()
    void HandleMenuAudioCue();
    UFUNCTION()
    void OpenPendingLevel();
    UFUNCTION()
    void HandleCycleMode();
    UFUNCTION()
    void HandlePreviousScenario();
    UFUNCTION()
    void HandleNextScenario();
    UFUNCTION()
    void HandleOpenCareer();
    UFUNCTION()
    void HandleOpenSettings();
    UFUNCTION()
    void HandleBack();

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
    void SetRunButtonsEnabled(bool bEnabled);
    UButton* MakeMenuButton(UVerticalBox* Parent, const FText& Label, FName ClickHandlerName);
    UButton* MakeButtonWithTarget(
        UVerticalBox* Parent, const FText& Label, UObject* Target, FName ClickHandlerName);

    UPROPERTY()
    TObjectPtr<UVerticalBox> MainPanel;

    UPROPERTY()
    TObjectPtr<UVerticalBox> CareerPanel;

    UPROPERTY()
    TObjectPtr<UVerticalBox> SettingsPanel;

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

    UPROPERTY()
    TObjectPtr<UButton> FirstRunButton;

    UPROPERTY()
    TObjectPtr<UButton> FirstCareerButton;

    UPROPERTY()
    TObjectPtr<UButton> FirstSettingsButton;

    UPROPERTY()
    TArray<TObjectPtr<URaftSimMenuRunButton>> RunButtons;

    UPROPERTY()
    TObjectPtr<USoundWaveProcedural> MenuConfirmTone;

    // Single persistent player for MenuConfirmTone. USoundWaveProcedural's
    // AudioBuffer is single-consumer: every PlaySound2D spawns another
    // never-finishing mixer source over the same wave, and parallel source
    // rendering then races RemoveAt on the shared buffer (Array RangeCheck
    // crash, first hit on the 2026-08-07 Linux playtest during travel).
    // Clicks only QueueAudio into this one always-playing component.
    UPROPERTY()
    TObjectPtr<UAudioComponent> MenuAudioComponent;

    TArray<FRaftSimCareerScenarioDefinition> ScenarioCatalog;
    ERaftSimGameMode SelectedMode = ERaftSimGameMode::TrainingEddy;
    ERaftSimMenuScreen ActiveScreen = ERaftSimMenuScreen::Main;
    int32 SelectedScenarioIndex = 0;
    bool bModeInitialized = false;
    FName PendingLevelName;
    FTimerHandle PendingTravelTimer;
    TArray<uint8> MenuConfirmPcm;
};
