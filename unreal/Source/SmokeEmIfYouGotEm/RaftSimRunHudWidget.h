#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"

#include "RaftSimRunHudWidget.generated.h"

class UTextBlock;
class UBorder;
class UButton;
class UVerticalBox;
class UHorizontalBox;
class UScaleBox;
class USizeBox;
class UCanvasPanel;
class UWidget;
class URaftSimHudArt;
class ARaftSimRunManager;
class ARaftSimTrainingDirector;
class ARaftSimPresentationDirector;
class ARaftSimRaftActor;
struct FRaftSimRapidTitle;

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
 * In-run HUD: river and timer card, route ribbon, conditions, control prompts,
 * crew-call subtitles and rescue alerts; plus the command wheel, scout board,
 * pause menu and photo/replay overlays. Programmatic UMG so it stays
 * C++-diffable; painted graphics come from RaftSimHudArt.
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

    /** Play the cinematic name card for a rapid now (also used by reviews). */
    void ShowRapidTitle(const FRaftSimRapidTitle& Rapid);

    /** The rapid whose name card is on screen, or empty. */
    FString GetVisibleRapidTitleId() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    void BuildWidgetTree();
    UTextBlock* MakeText(const FSlateFontInfo& Font, FLinearColor Color, bool bShadow = true);
    void AddPrompt(UHorizontalBox* Bar, const FText& Key, const FText& Action);
    void SetPlayHudVisible(bool bVisible);
    UFUNCTION() void ResumeRun();
    UFUNCTION() void RestartRun();
    UFUNCTION() void LeaveRun();
    UFUNCTION() void OpenPhotoMode();

    UPROPERTY() TObjectPtr<UBorder> StatusCard;
    UPROPERTY() TObjectPtr<UBorder> OverlayCard;
    UPROPERTY() TObjectPtr<UScaleBox> OverlayBounds;
    UPROPERTY() TObjectPtr<UVerticalBox> PauseActions;
    UPROPERTY() TObjectPtr<UButton> ResumeButton;
    UPROPERTY() TObjectPtr<UBorder> SubtitleCard;
    UPROPERTY() TObjectPtr<UBorder> RescueCard;
    UPROPERTY() TObjectPtr<UWidget> RouteBlock;
    UPROPERTY() TObjectPtr<URaftSimHudArt> RouteRibbon;
    UPROPERTY() TObjectPtr<UBorder> ConditionsCard;
    UPROPERTY() TObjectPtr<UWidget> PromptBar;
    UPROPERTY() TObjectPtr<UWidget> PausePanel;
    UPROPERTY() TObjectPtr<UWidget> WheelPanel;
    UPROPERTY() TObjectPtr<UBorder> PhotoChip;
    UPROPERTY() TObjectPtr<URaftSimHudArt> EdgeShade;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> PauseLabels;

    UPROPERTY() TObjectPtr<UTextBlock> RiverText;
    UPROPERTY() TObjectPtr<UTextBlock> StateText;
    UPROPERTY() TObjectPtr<UBorder> StateChip;
    UPROPERTY() TObjectPtr<UTextBlock> StatusText;
    UPROPERTY() TObjectPtr<UTextBlock> StatsText;
    UPROPERTY() TObjectPtr<UTextBlock> EnergyText;
    UPROPERTY() TObjectPtr<UTextBlock> ScoreText;
    UPROPERTY() TObjectPtr<UTextBlock> SubtitleText;
    UPROPERTY() TObjectPtr<UTextBlock> ProgressText;
    UPROPERTY() TObjectPtr<UTextBlock> EnvironmentText;
    UPROPERTY() TObjectPtr<UTextBlock> ClockText;
    UPROPERTY() TObjectPtr<UTextBlock> TrainingText;
    UPROPERTY() TObjectPtr<UBorder> TrainingCard;
    UPROPERTY() TObjectPtr<UTextBlock> OverlayTitle;
    UPROPERTY() TObjectPtr<UTextBlock> OverlayText;
    UPROPERTY() TObjectPtr<UTextBlock> RescueText;
    UPROPERTY() TObjectPtr<UTextBlock> PauseRiverText;
    UPROPERTY() TObjectPtr<UTextBlock> PauseStatsText;
    UPROPERTY() TObjectPtr<UTextBlock> TransitionKicker;
    UPROPERTY() TObjectPtr<UTextBlock> TransitionTitle;

    UPROPERTY()
    TObjectPtr<UTextBlock> TransitionText;

    UPROPERTY()
    TObjectPtr<UScaleBox> TransitionBounds;

    UPROPERTY()
    TObjectPtr<USizeBox> TransitionWrap;

    FVector2D LastTransitionViewport = FVector2D::ZeroVector;
    float AppliedUiScale = 1.0f;

    UPROPERTY()
    TObjectPtr<ARaftSimRunManager> RunManager;

    UPROPERTY()
    TObjectPtr<ARaftSimTrainingDirector> TrainingDirector;

    UPROPERTY()
    TObjectPtr<ARaftSimPresentationDirector> PresentationDirector;

    // Cinematic rapid name card.
    void UpdateRapidTitle(float DeltaSeconds);
    UPROPERTY() TObjectPtr<URaftSimHudArt> RapidBand;
    UPROPERTY() TObjectPtr<UVerticalBox> RapidColumn;
    UPROPERTY() TObjectPtr<UTextBlock> RapidKicker;
    UPROPERTY() TObjectPtr<UTextBlock> RapidName;
    UPROPERTY() TObjectPtr<UTextBlock> RapidGrade;
    UPROPERTY() TObjectPtr<URaftSimHudArt> RapidRule;
    TWeakObjectPtr<ARaftSimRaftActor> RapidRaft;
    TArray<const FRaftSimRapidTitle*> RapidTitles;
    TArray<bool> RapidTitleShown;
    const FRaftSimRapidTitle* ActiveRapidTitle = nullptr;
    bool bRapidTitlesResolved = false;
    float RapidTitleElapsed = -1.0f;

    float SubtitleRemaining = 0.0f;
    float TransitionRemaining = 0.0f;
    float HudClock = 0.0f;
    uint8 LastObservedRunState = 255;
    ERaftSimHudOverlay VisibleOverlay = ERaftSimHudOverlay::None;
};
