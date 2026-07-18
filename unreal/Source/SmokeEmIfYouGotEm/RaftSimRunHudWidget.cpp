#include "RaftSimRunHudWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "EngineUtils.h"
#include "RaftSimRunManager.h"

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
}

void URaftSimRunHudWidget::NativeConstruct()
{
    Super::NativeConstruct();

    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;

    StatusText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 30.0f), 22);
    ScoreText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 70.0f), 22);
    SubtitleText = AddText(WidgetTree, Canvas, FVector2D(40.0f, 640.0f), 24);
    SubtitleText->SetText(FText::GetEmpty());

    if (TActorIterator<ARaftSimRunManager> It(GetWorld()); It)
    {
        RunManager = *It;
    }
}

void URaftSimRunHudWidget::ShowSubtitle(const FText& Line, float DurationSeconds)
{
    if (SubtitleText != nullptr)
    {
        SubtitleText->SetText(Line);
        SubtitleRemaining = DurationSeconds;
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
            TEXT("%s   t=%.1fs   incidents=%d   swimmers=%d"),
            StateName, RunManager->GetRunTimeSeconds(),
            RunManager->GetSafetyIncidentCount(), RunManager->GetSwimCount())));

        if (RunManager->GetRunState() == ERaftSimRunState::Finished)
        {
            ScoreText->SetText(FText::FromString(FString::Printf(
                TEXT("Score: %.0f   (safety %.0f, line %.0f)"),
                RunManager->GetFinalScore().TotalScore,
                RunManager->GetFinalScore().SafetyScore,
                RunManager->GetFinalScore().LineChoiceScore)));
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
