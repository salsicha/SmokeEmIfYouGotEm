#include "RaftSimRunHudWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "EngineUtils.h"
#include "RaftSimRunManager.h"
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
    TrainingText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 150.0f), 20);
    RescueText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 580.0f), 19);
    SubtitleText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 640.0f), 24);
    OverlayText = AddText(WidgetTree, Canvas, FVector2D(330.0f, 190.0f), 26);
    // Explicit regions avoid the auto-size/auto-wrap feedback loop that can
    // collapse dynamic UMG text to a word-wide column on portrait displays.
    SetTextRegion(TrainingText, FVector2D(260.0f, 400.0f), 260.0f);
    SetTextRegion(RescueText, FVector2D(940.0f, 80.0f), 940.0f);
    SetTextRegion(SubtitleText, FVector2D(940.0f, 120.0f), 940.0f);
    SetTextRegion(OverlayText, FVector2D(680.0f, 440.0f), 680.0f);
    SubtitleText->SetText(FText::GetEmpty());
    OverlayText->SetText(FText::GetEmpty());
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

    if (RunManager != nullptr && StatusText != nullptr)
    {
        const TCHAR* StateName = TEXT("Ready");
        switch (RunManager->GetRunState())
        {
            case ERaftSimRunState::Running: StateName = TEXT("Running"); break;
            case ERaftSimRunState::Finished: StateName = TEXT("Finished"); break;
            default: break;
        }
        StatusText->SetText(FText::FromString(FString::Printf(
            TEXT("%s   t=%.1fs   incidents=%d   swimmers=%d   station=%.0fm"),
            StateName, RunManager->GetRunTimeSeconds(),
            RunManager->GetSafetyIncidentCount(), RunManager->GetSwimCount(),
            RunManager->GetCurrentStationM())));
        ProgressText->SetText(FText::FromString(FString::Printf(
            TEXT("Run progress %.0f%%   Scout M / D-pad Down   Commands Tab / gamepad X"),
            RunManager->GetProgressFraction() * 100.0f)));

        if (RunManager->GetRunState() == ERaftSimRunState::Finished)
        {
            ScoreText->SetText(RunManager->GetAfterActionSummary());
        }
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
}
