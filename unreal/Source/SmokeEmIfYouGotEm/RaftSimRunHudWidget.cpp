#include "RaftSimRunHudWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "EngineUtils.h"
#include "RaftSimRunManager.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRaftActor.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimTrainingDirector.h"
#include "RaftSimVerticalSliceFrontend.h"

namespace
{
UTextBlock* AddText(UWidgetTree* Tree, UCanvasPanel* Canvas, const FVector2D& Pos, int32 FontSize)
{
    UTextBlock* Text = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Text);
    Slot->SetPosition(Pos);
    Slot->SetAutoSize(true);
    FSlateFontInfo Font = Text->GetFont();
    Font.Size = FontSize;
    Text->SetFont(Font);
    return Text;
}

void SetTextRegion(UTextBlock* Text, const FVector2D& Size, float WrapAt)
{
    if (Text == nullptr)
    {
        return;
    }
    if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Text->Slot))
    {
        Slot->SetAutoSize(false);
        Slot->SetSize(Size);
    }
    Text->SetAutoWrapText(true);
    Text->SetWrapTextAt(WrapAt);
}
}

TSharedRef<SWidget> URaftSimRunHudWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

void URaftSimRunHudWidget::BuildWidgetTree()
{
    if (WidgetTree == nullptr || WidgetTree->RootWidget != nullptr)
    {
        return;
    }
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;

    StatusText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 30.0f), 22);
    ScoreText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 70.0f), 22);
    ProgressText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 110.0f), 20);
    EnvironmentText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 150.0f), 17);
    TrainingText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 185.0f), 20);
    RescueText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 580.0f), 19);
    SubtitleText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 640.0f), 24);
    OverlayText = AddText(WidgetTree, Canvas, FVector2D(330.0f, 225.0f), 26);
    TransitionText = AddText(WidgetTree, Canvas, FVector2D(150.0f, 760.0f), 32);
    // Explicit regions avoid the auto-size/auto-wrap feedback loop that can
    // collapse dynamic UMG text to a word-wide column on portrait displays.
    SetTextRegion(TrainingText, FVector2D(260.0f, 400.0f), 260.0f);
    SetTextRegion(RescueText, FVector2D(940.0f, 80.0f), 940.0f);
    SetTextRegion(SubtitleText, FVector2D(940.0f, 120.0f), 940.0f);
    SetTextRegion(OverlayText, FVector2D(680.0f, 440.0f), 680.0f);
    SetTextRegion(TransitionText, FVector2D(780.0f, 240.0f), 780.0f);
    SubtitleText->SetText(FText::GetEmpty());
    OverlayText->SetText(FText::GetEmpty());
    TransitionText->SetText(FText::GetEmpty());
}

void URaftSimRunHudWidget::NativeConstruct()
{
    Super::NativeConstruct();

    if (TActorIterator<ARaftSimRunManager> It(GetWorld()); It)
    {
        RunManager = *It;
    }
    if (TActorIterator<ARaftSimTrainingDirector> It(GetWorld()); It)
    {
        TrainingDirector = *It;
    }
    if (TActorIterator<ARaftSimPresentationDirector> It(GetWorld()); It)
    {
        PresentationDirector = *It;
    }
    if (const URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr)
        {
            const auto& Settings = Save->GetSave()->Settings;
            if (UWidget* RootWidget = WidgetTree ? WidgetTree->RootWidget : nullptr)
            {
                RootWidget->SetRenderScale(FVector2D(Settings.UiScale));
            }
            const FLinearColor Cue = Settings.ColorCueMode == ERaftSimColorCueMode::Monochrome
                ? FLinearColor::White
                : Settings.ColorCueMode == ERaftSimColorCueMode::DeuteranopiaSafe ||
                    Settings.ColorCueMode == ERaftSimColorCueMode::ProtanopiaSafe
                    ? FLinearColor(0.2f, 0.75f, 1.0f)
                    : FLinearColor(0.15f, 1.0f, 0.55f);
            ProgressText->SetColorAndOpacity(FSlateColor(Cue));
        }
    }
}

void URaftSimRunHudWidget::BeginScenarioPresentation(const FText& Title, const FText& Briefing)
{
    if (TransitionText == nullptr)
    {
        return;
    }
    TransitionText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "ScenarioTransition", "{0}\n{1}\n\nGuide from the stern • Tab: crew calls • M: scout • E/R/F: rescue"),
        Title, Briefing));
    TransitionText->SetRenderOpacity(0.0f);
    TransitionRemaining = 5.0f;
}

void URaftSimRunHudWidget::ShowSubtitle(const FText& Line, float DurationSeconds)
{
    if (const URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr && !Save->GetSave()->Settings.bSubtitlesEnabled)
        {
            return;
        }
    }
    if (SubtitleText != nullptr)
    {
        SubtitleText->SetText(Line);
        SubtitleRemaining = DurationSeconds;
    }
}

void URaftSimRunHudWidget::ShowOverlay(ERaftSimHudOverlay Overlay)
{
    VisibleOverlay = Overlay;
    if (OverlayText == nullptr)
    {
        return;
    }
    switch (Overlay)
    {
        case ERaftSimHudOverlay::CommandWheel:
            OverlayText->SetText(NSLOCTEXT("RaftSim", "CommandWheelOverlay",
                "COMMAND WHEEL\n1 / D-pad Up — ALL FORWARD\n2 / D-pad Down — BACK PADDLE\n3 / D-pad Left — TURN LEFT\n4 / D-pad Right — TURN RIGHT\n5 / gamepad A — STOP"));
            break;
        case ERaftSimHudOverlay::ScoutBoard:
            OverlayText->SetText(NSLOCTEXT("RaftSim", "ScoutOverlay",
                "SCOUT BOARD\nRead the tongue and downstream V.\nMark laterals, holes, rocks, strainers, and recovery eddies.\nCyan ghost = your best prior route. Amber cues = inferred/procedural geography.\nM / D-pad Down closes scout."));
            break;
        case ERaftSimHudOverlay::Pause:
            OverlayText->SetText(NSLOCTEXT("RaftSim", "PauseOverlay",
                "PAUSED\nEscape / gamepad Menu — Resume\nBackspace / gamepad A — Restart checkpoint\nHome / gamepad B — Main menu\nP / gamepad Y — Photo mode"));
            break;
        case ERaftSimHudOverlay::PhotoMode:
            OverlayText->SetText(NSLOCTEXT("RaftSim", "PhotoOverlay",
                "PHOTO MODE\nHUD hidden for captures. Look controls remain active.\nF9 / gamepad Right Trigger — Capture\nP / gamepad Y — Return"));
            break;
        case ERaftSimHudOverlay::ReplayReview:
            OverlayText->SetText(RunManager
                ? FText::Format(NSLOCTEXT("RaftSim", "ReviewOverlay",
                    "AFTER-ACTION REVIEW\n{0}\nCyan route: best prior line. Compare entry angle, incidents, and recovery choices.\nV / gamepad Left Trigger — close"),
                    RunManager->GetAfterActionSummary())
                : NSLOCTEXT("RaftSim", "ReviewUnavailable", "AFTER-ACTION REVIEW unavailable"));
            break;
        default:
            OverlayText->SetText(FText::GetEmpty());
            break;
    }
}

void URaftSimRunHudWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);

    if (RunManager == nullptr)
    {
        if (TActorIterator<ARaftSimRunManager> It(GetWorld()); It)
        {
            RunManager = *It;
        }
    }
    if (TrainingDirector == nullptr)
    {
        if (TActorIterator<ARaftSimTrainingDirector> It(GetWorld()); It)
        {
            TrainingDirector = *It;
        }
    }
    if (PresentationDirector == nullptr)
    {
        if (TActorIterator<ARaftSimPresentationDirector> It(GetWorld()); It)
        {
            PresentationDirector = *It;
        }
    }

    if (RunManager != nullptr && StatusText != nullptr)
    {
        const TCHAR* StateName = TEXT("READY");
        switch (RunManager->GetRunState())
        {
            case ERaftSimRunState::Running: StateName = TEXT("RUN IN PROGRESS"); break;
            case ERaftSimRunState::Finished: StateName = TEXT("RUN COMPLETE"); break;
            default: break;
        }
        const int32 ElapsedSeconds = FMath::Max(0, FMath::FloorToInt(RunManager->GetRunTimeSeconds()));
        StatusText->SetText(FText::FromString(FString::Printf(
            TEXT("%s  •  %02d:%02d  •  %d incidents  •  %d swimmers  •  river km %.2f"),
            StateName, ElapsedSeconds / 60, ElapsedSeconds % 60,
            RunManager->GetSafetyIncidentCount(), RunManager->GetSwimCount(),
            RunManager->GetCurrentStationM() / 1000.0f)));
        ProgressText->SetText(FText::FromString(FString::Printf(
            TEXT("%.0f%% complete  •  M / D-pad Down: scout  •  Tab / X: crew commands"),
            RunManager->GetProgressFraction() * 100.0f)));

        const uint8 RunStateValue = static_cast<uint8>(RunManager->GetRunState());
        if (LastObservedRunState != RunStateValue)
        {
            if (RunManager->GetRunState() == ERaftSimRunState::Finished && TransitionText != nullptr)
            {
                TransitionText->SetText(FText::Format(
                    NSLOCTEXT("RaftSim", "RunCompleteTransition", "RUN COMPLETE\n{0}\n\nV / Left Trigger: review route"),
                    RunManager->GetAfterActionSummary()));
                TransitionText->SetRenderOpacity(1.0f);
                TransitionRemaining = 5.0f;
            }
            LastObservedRunState = RunStateValue;
        }

        if (RunManager->GetRunState() == ERaftSimRunState::Finished)
        {
            ScoreText->SetText(RunManager->GetAfterActionSummary());
        }
    }

    if (EnvironmentText != nullptr && PresentationDirector != nullptr)
    {
        const FRaftSimPresentationEnvironmentState Environment =
            PresentationDirector->GetEnvironmentState();
        EnvironmentText->SetText(FText::Format(
            NSLOCTEXT("RaftSim", "EnvironmentHud", "{0} • {1}h • T / L3 weather • C / R3 camera"),
            PresentationDirector->GetWeatherDisplayName(),
            FText::FromString(FString::Printf(TEXT("%.1f"), Environment.TimeOfDayHours))));
    }

    if (TrainingText != nullptr)
    {
        TrainingText->SetText(TrainingDirector != nullptr
            ? FText::Format(NSLOCTEXT("RaftSim", "TrainingHud", "TRAINING {0}/{1}: {2}"),
                FText::AsNumber(TrainingDirector->GetCompletedDrillCount()),
                FText::AsNumber(TrainingDirector->GetTotalDrillCount()),
                TrainingDirector->GetCurrentPrompt())
            : FText::GetEmpty());
    }
    if (RescueText != nullptr)
    {
        ARaftSimRaftActor* Raft = nullptr;
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
        {
            Raft = *It;
        }
        if (Raft != nullptr && Raft->GetSwimmerCount() > 0)
        {
            const FRaftSimRescueInteractionState Rescue = Raft->GetRescueInteractionState();
            RescueText->SetText(FText::FromString(FString::Printf(
                TEXT("RESCUE — target %s | distance %.1fm | %s | E reach, R throw, F reseat"),
                *Rescue.TargetPassengerId.ToString(), Rescue.DistanceMeters,
                *Rescue.FeedbackCode.ToString())));
        }
        else
        {
            RescueText->SetText(FText::GetEmpty());
        }
    }

    if (SubtitleRemaining > 0.0f)
    {
        SubtitleRemaining -= DeltaSeconds;
        if (SubtitleRemaining <= 0.0f && SubtitleText != nullptr)
        {
            SubtitleText->SetText(FText::GetEmpty());
        }
    }
    if (TransitionRemaining > 0.0f && TransitionText != nullptr)
    {
        TransitionRemaining -= DeltaSeconds;
        const float Elapsed = 5.0f - TransitionRemaining;
        const float FadeIn = FMath::Clamp(Elapsed / 0.4f, 0.0f, 1.0f);
        const float FadeOut = FMath::Clamp(TransitionRemaining / 1.2f, 0.0f, 1.0f);
        TransitionText->SetRenderOpacity(FMath::Min(FadeIn, FadeOut));
        if (TransitionRemaining <= 0.0f)
        {
            TransitionText->SetText(FText::GetEmpty());
        }
    }
}
