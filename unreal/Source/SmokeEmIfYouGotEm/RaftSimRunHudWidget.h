#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"

#include "RaftSimRunHudWidget.generated.h"

class UTextBlock;
class ARaftSimRunManager;
class ARaftSimTrainingDirector;
class ARaftSimPresentationDirector;

UENUM(BlueprintType)
enum class ERaftSimHudOverlay : uint8
{
    None,
    CommandWheel,
    ScoutBoard,
    Pause,
    PhotoMode,
    ReplayReview
};

/**
 * In-run HUD (P3 HUD v1): run state + timer, speed, crew/swimmer status, score,
 * and a subtitle line. Programmatic UMG so it stays C++-diffable.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API URaftSimRunHudWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;

    /** Show a transient subtitle (command callouts, crew barks). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|HUD")
    void ShowSubtitle(const FText& Line, float DurationSeconds = 3.0f);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|HUD")
    void ShowOverlay(ERaftSimHudOverlay Overlay);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|HUD")
    void BeginScenarioPresentation(const FText& Title, const FText& Briefing);

    UFUNCTION(BlueprintPure, Category = "RaftSim|HUD")
    ERaftSimHudOverlay GetVisibleOverlay() const { return VisibleOverlay; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|HUD")
    bool IsScenarioTransitionVisible() const { return TransitionRemaining > 0.0f; }

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    void BuildWidgetTree();

    UPROPERTY()
    TObjectPtr<UTextBlock> StatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ScoreText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SubtitleText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ProgressText;

    UPROPERTY()
    TObjectPtr<UTextBlock> EnvironmentText;

    UPROPERTY()
    TObjectPtr<UTextBlock> TrainingText;

    UPROPERTY()
    TObjectPtr<UTextBlock> OverlayText;

    UPROPERTY()
    TObjectPtr<UTextBlock> RescueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> TransitionText;

    UPROPERTY()
    TObjectPtr<ARaftSimRunManager> RunManager;

    UPROPERTY()
    TObjectPtr<ARaftSimTrainingDirector> TrainingDirector;

    UPROPERTY()
    TObjectPtr<ARaftSimPresentationDirector> PresentationDirector;

    float SubtitleRemaining = 0.0f;
    float TransitionRemaining = 0.0f;
    uint8 LastObservedRunState = 255;
    ERaftSimHudOverlay VisibleOverlay = ERaftSimHudOverlay::None;
};
