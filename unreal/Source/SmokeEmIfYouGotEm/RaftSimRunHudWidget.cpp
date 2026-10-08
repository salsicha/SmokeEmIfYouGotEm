#include "RaftSimRunHudWidget.h"
#include "RaftSimCrewRoster.h"

#include "Blueprint/WidgetTree.h"
#include "Components/BackgroundBlur.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/ScaleBox.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "RaftSimHudArt.h"
#include "RaftSimUIArt.h"
#include "RaftSimUITheme.h"
#include "RaftSimGuidePlayerController.h"
#include "RaftSimTransitionLayout.h"
#include "EngineUtils.h"
#include "RaftSimRunManager.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRapidTitles.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimTrainingDirector.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Containers/Ticker.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

using namespace RaftSimUITheme;

namespace
{
UCanvasPanelSlot* Pin(UCanvasPanel* Canvas, UWidget* Widget, FAnchors Anchors, FVector2D Alignment,
    FVector2D Position, FVector2D Size = FVector2D::ZeroVector)
{
    UCanvasPanelSlot* CanvasSlot = Canvas->AddChildToCanvas(Widget);
    CanvasSlot->SetAnchors(Anchors);
    CanvasSlot->SetAlignment(Alignment);
    CanvasSlot->SetPosition(Position);
    if (Size.IsZero())
    {
        CanvasSlot->SetAutoSize(true);
    }
    else
    {
        CanvasSlot->SetSize(Size);
    }
    return CanvasSlot;
}

FSlateBrush HudPanel()
{
    return Rounded(FLinearColor(0.004f, 0.012f, 0.014f, 0.62f), 10.0f, FLinearColor(1, 1, 1, 0.08f), 1.0f);
}

FString Clock(float Seconds)
{
    const int32 Whole = FMath::Max(0, FMath::FloorToInt(Seconds));
    return FString::Printf(TEXT("%02d:%02d"), Whole / 60, Whole % 60);
}
}

TSharedRef<SWidget> URaftSimRunHudWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

UTextBlock* URaftSimRunHudWidget::MakeText(const FSlateFontInfo& Font, FLinearColor Color, bool bShadow)
{
    UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Style(Block, Font, Color, bShadow);
    return Block;
}

void URaftSimRunHudWidget::AddPrompt(UHorizontalBox* Bar, const FText& Key, const FText& Action)
{
    UBorder* KeyChip = WidgetTree->ConstructWidget<UBorder>();
    KeyChip->SetBrush(Rounded(FLinearColor(0, 0, 0, 0.55f), 4.0f, FLinearColor(1, 1, 1, 0.40f), 1.0f));
    KeyChip->SetPadding(FMargin(7, 1));
    UTextBlock* KeyText = MakeText(Label(11), Paper(), false);
    KeyText->SetText(Key);
    KeyChip->SetContent(KeyText);
    Bar->AddChildToHorizontalBox(KeyChip)->SetVerticalAlignment(VAlign_Center);
    UTextBlock* ActionText = MakeText(Label(12), Paper());
    ActionText->SetText(Action);
    UHorizontalBoxSlot* ActionSlot = Bar->AddChildToHorizontalBox(ActionText);
    ActionSlot->SetVerticalAlignment(VAlign_Center);
    ActionSlot->SetPadding(FMargin(6, 0, 18, 0));
}

void URaftSimRunHudWidget::BuildWidgetTree()
{
    if (WidgetTree == nullptr || WidgetTree->RootWidget != nullptr)
    {
        return;
    }
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;

    EdgeShade = WidgetTree->ConstructWidget<URaftSimHudArt>();
    EdgeShade->SetKind(ERaftSimHudArtKind::Shade);
    EdgeShade->SetVisibility(ESlateVisibility::HitTestInvisible);
    UCanvasPanelSlot* ShadeSlot = Canvas->AddChildToCanvas(EdgeShade);
    ShadeSlot->SetAnchors(FAnchors(0, 0, 1, 1));
    ShadeSlot->SetOffsets(FMargin(0));

    // --- River and run card (top left).
    StatusCard = WidgetTree->ConstructWidget<UBorder>();
    StatusCard->SetBrush(HudPanel());
    StatusCard->SetPadding(FMargin(18, 11, 22, 13));
    Pin(Canvas, StatusCard, FAnchors(0, 0), FVector2D::ZeroVector, FVector2D(24, 20));
    UVerticalBox* RunColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    StatusCard->SetContent(RunColumn);
    UHorizontalBox* RiverRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    RunColumn->AddChildToVerticalBox(RiverRow);
    RiverText = MakeText(Label(13), Gold());
    RiverRow->AddChildToHorizontalBox(RiverText)->SetVerticalAlignment(VAlign_Center);
    StateChip = WidgetTree->ConstructWidget<UBorder>();
    StateChip->SetBrush(Rounded(River(), 4.0f));
    StateChip->SetPadding(FMargin(7, 0));
    StateText = MakeText(Label(11), Ink(), false);
    StateChip->SetContent(StateText);
    UHorizontalBoxSlot* ChipSlot = RiverRow->AddChildToHorizontalBox(StateChip);
    ChipSlot->SetVerticalAlignment(VAlign_Center);
    ChipSlot->SetPadding(FMargin(10, 0, 0, 0));
    StatusText = MakeText(Display(38), Paper());
    RunColumn->AddChildToVerticalBox(StatusText)->SetPadding(FMargin(0, -4, 0, -4));
    StatsText = MakeText(Label(13), FLinearColor(0.80f, 0.86f, 0.82f));
    RunColumn->AddChildToVerticalBox(StatsText);
    // Crew energy: paddling tires the crew; a rest brings them back.
    EnergyText = MakeText(Label(13), FLinearColor(0.62f, 0.86f, 0.58f));
    RunColumn->AddChildToVerticalBox(EnergyText)->SetPadding(FMargin(0, 3, 0, 0));
    ScoreText = MakeText(Body(14), Gold());
    ScoreText->SetAutoWrapText(true);
    ScoreText->SetWrapTextAt(420.0f);
    RunColumn->AddChildToVerticalBox(ScoreText)->SetPadding(FMargin(0, 6, 0, 0));

    // --- Route ribbon (top centre).
    UBorder* RoutePanel = WidgetTree->ConstructWidget<UBorder>();
    RoutePanel->SetBrush(HudPanel());
    RoutePanel->SetPadding(FMargin(16, 6, 16, 8));
    RouteBlock = RoutePanel;
    Pin(Canvas, RoutePanel, FAnchors(0.5f, 0.0f), FVector2D(0.5f, 0.0f), FVector2D(0, 20), FVector2D(560, 70));
    UVerticalBox* Route = WidgetTree->ConstructWidget<UVerticalBox>();
    RoutePanel->SetContent(Route);
    USizeBox* RibbonSize = WidgetTree->ConstructWidget<USizeBox>();
    RibbonSize->SetHeightOverride(32.0f);
    RouteRibbon = WidgetTree->ConstructWidget<URaftSimHudArt>();
    RouteRibbon->SetKind(ERaftSimHudArtKind::RouteRibbon);
    RibbonSize->AddChild(RouteRibbon);
    Route->AddChildToVerticalBox(RibbonSize);
    ProgressText = MakeText(Label(12), Paper());
    ProgressText->SetJustification(ETextJustify::Center);
    Route->AddChildToVerticalBox(ProgressText)->SetHorizontalAlignment(HAlign_Center);

    // --- Conditions (top right).
    ConditionsCard = WidgetTree->ConstructWidget<UBorder>();
    ConditionsCard->SetBrush(HudPanel());
    ConditionsCard->SetPadding(FMargin(18, 9, 18, 11));
    Pin(Canvas, ConditionsCard, FAnchors(1.0f, 0.0f), FVector2D(1.0f, 0.0f), FVector2D(-24, 20));
    UVerticalBox* Conditions = WidgetTree->ConstructWidget<UVerticalBox>();
    ConditionsCard->SetContent(Conditions);
    EnvironmentText = MakeText(Label(13), Gold());
    EnvironmentText->SetJustification(ETextJustify::Right);
    Conditions->AddChildToVerticalBox(EnvironmentText)->SetHorizontalAlignment(HAlign_Right);
    ClockText = MakeText(Display(26), Paper());
    ClockText->SetJustification(ETextJustify::Right);
    Conditions->AddChildToVerticalBox(ClockText)->SetHorizontalAlignment(HAlign_Right);

    // --- Guide school drill card.
    TrainingCard = WidgetTree->ConstructWidget<UBorder>();
    TrainingCard->SetBrush(HudPanel());
    TrainingCard->SetPadding(FMargin(16, 10));
    Pin(Canvas, TrainingCard, FAnchors(0, 0), FVector2D::ZeroVector, FVector2D(24, 182), FVector2D(380, 150));
    TrainingText = MakeText(Strong(16), Paper());
    TrainingText->SetAutoWrapText(true);
    TrainingCard->SetContent(TrainingText);

    // --- Control prompts (bottom right).
    UHorizontalBox* Prompts = WidgetTree->ConstructWidget<UHorizontalBox>();
    PromptBar = Prompts;
    Pin(Canvas, Prompts, FAnchors(1.0f, 1.0f), FVector2D(1.0f, 1.0f), FVector2D(-12, -20));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyHighSide", "SPACE / X"), NSLOCTEXT("RaftSim", "HudHighSide", "HIGH SIDE"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyCrew", "TAB / VIEW"), NSLOCTEXT("RaftSim", "HudCrew", "CREW CALLS"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyScout", "M"), NSLOCTEXT("RaftSim", "HudScout", "SCOUT"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyCamera", "C"), NSLOCTEXT("RaftSim", "HudCamera", "CAMERA"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyWeather", "T"), NSLOCTEXT("RaftSim", "HudWeather", "WEATHER"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "HudKeyPause", "ESC / P"), NSLOCTEXT("RaftSim", "HudPause", "PAUSE"));

    // --- Rescue alert and crew-call subtitles.
    RescueCard = WidgetTree->ConstructWidget<UBorder>();
    RescueCard->SetBrush(Rounded(FLinearColor(0.32f, 0.05f, 0.02f, 0.88f), 10.0f, Danger(), 2.0f));
    RescueCard->SetPadding(FMargin(20, 10));
    Pin(Canvas, RescueCard, FAnchors(0.5f, 0.0f), FVector2D(0.5f, 0.0f), FVector2D(0, 100), FVector2D(820, 56));
    RescueText = MakeText(Label(17), Paper());
    RescueText->SetJustification(ETextJustify::Center);
    RescueCard->SetContent(RescueText);
    SubtitleCard = WidgetTree->ConstructWidget<UBorder>();
    SubtitleCard->SetBrush(Rounded(FLinearColor(0.0f, 0.0f, 0.0f, 0.66f), 24.0f));
    SubtitleCard->SetPadding(FMargin(26, 10));
    SubtitleCard->SetHorizontalAlignment(HAlign_Center);
    SubtitleCard->SetVerticalAlignment(VAlign_Center);
    Pin(Canvas, SubtitleCard, FAnchors(0.5f, 1.0f), FVector2D(0.5f, 1.0f), FVector2D(0, -64), FVector2D(820, 64));
    SubtitleText = MakeText(Strong(20), Paper());
    SubtitleText->SetJustification(ETextJustify::Center);
    SubtitleText->SetAutoWrapText(true);
    SubtitleCard->SetContent(SubtitleText);

    // --- Rapid name card: a feathered band across the upper river view, the
    // river in small amber capitals, the rapid's name tracking in wide, an
    // amber rule drawing out beneath it and the catalogued class.
    RapidBand = WidgetTree->ConstructWidget<URaftSimHudArt>();
    RapidBand->SetKind(ERaftSimHudArtKind::TitleBand);
    UCanvasPanelSlot* BandSlot = Canvas->AddChildToCanvas(RapidBand);
    BandSlot->SetAnchors(FAnchors(0.0f, 0.38f, 1.0f, 0.38f));
    BandSlot->SetOffsets(FMargin(0.0f, -118.0f, 0.0f, 236.0f));
    RapidBand->SetVisibility(ESlateVisibility::Collapsed);
    RapidColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    Pin(Canvas, RapidColumn, FAnchors(0.5f, 0.38f), FVector2D(0.5f, 0.5f), FVector2D::ZeroVector);
    RapidKicker = MakeText(Label(15), Gold());
    RapidKicker->SetJustification(ETextJustify::Center);
    RapidColumn->AddChildToVerticalBox(RapidKicker)->SetHorizontalAlignment(HAlign_Center);
    RapidName = MakeText(Display(66), Paper());
    RapidName->SetJustification(ETextJustify::Center);
    RapidName->SetShadowColorAndOpacity(FLinearColor(0, 0, 0, 0.85f));
    RapidName->SetShadowOffset(FVector2D(0, 3));
    RapidColumn->AddChildToVerticalBox(RapidName)->SetHorizontalAlignment(HAlign_Center);
    USizeBox* RuleBox = WidgetTree->ConstructWidget<USizeBox>();
    RuleBox->SetWidthOverride(620.0f);
    RuleBox->SetHeightOverride(16.0f);
    RapidRule = WidgetTree->ConstructWidget<URaftSimHudArt>();
    RapidRule->SetKind(ERaftSimHudArtKind::TitleRule);
    RapidRule->SetAccent(Gold());
    RuleBox->AddChild(RapidRule);
    RapidColumn->AddChildToVerticalBox(RuleBox)->SetHorizontalAlignment(HAlign_Center);
    RapidGrade = MakeText(Label(17), Paper());
    RapidGrade->SetJustification(ETextJustify::Center);
    RapidColumn->AddChildToVerticalBox(RapidGrade)->SetHorizontalAlignment(HAlign_Center);
    RapidColumn->SetVisibility(ESlateVisibility::Collapsed);

    // --- Scout / replay / photo information card.
    OverlayBounds = WidgetTree->ConstructWidget<UScaleBox>();
    OverlayBounds->SetStretch(EStretch::ScaleToFit);
    OverlayBounds->SetStretchDirection(EStretchDirection::DownOnly);
    UCanvasPanelSlot* OverlaySlot = Pin(Canvas, OverlayBounds, FAnchors(0.5f), FVector2D(0.5f),
        FVector2D::ZeroVector, FVector2D(740, 560));
    OverlaySlot->SetZOrder(5);
    auto* OverlayWidth = WidgetTree->ConstructWidget<USizeBox>();
    OverlayWidth->SetWidthOverride(700);
    OverlayBounds->AddChild(OverlayWidth);
    OverlayCard = WidgetTree->ConstructWidget<UBorder>();
    OverlayCard->SetBrush(Rounded(FLinearColor(0.006f, 0.016f, 0.018f, 0.90f), 12.0f, Gold(), 1.5f));
    OverlayCard->SetPadding(FMargin(34, 26));
    OverlayWidth->AddChild(OverlayCard);
    auto* OverlayColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    OverlayCard->SetContent(OverlayColumn);
    OverlayTitle = MakeText(Label(28), Gold());
    OverlayColumn->AddChildToVerticalBox(OverlayTitle)->SetPadding(FMargin(0, 0, 0, 8));
    OverlayText = MakeText(Body(19), Paper(), false);
    OverlayText->SetAutoWrapText(false);
    OverlayText->SetWrapTextAt(632);
    OverlayColumn->AddChildToVerticalBox(OverlayText);
    OverlayBounds->SetVisibility(ESlateVisibility::Collapsed);

    PhotoChip = WidgetTree->ConstructWidget<UBorder>();
    PhotoChip->SetBrush(HudPanel());
    PhotoChip->SetPadding(FMargin(18, 8));
    Pin(Canvas, PhotoChip, FAnchors(0.5f, 0.0f), FVector2D(0.5f, 0.0f), FVector2D(0, 22));
    UTextBlock* PhotoText = MakeText(Label(14), Paper());
    PhotoText->SetText(NSLOCTEXT("RaftSim", "PhotoChip",
        "PHOTO MODE   ·   F9 / RT  CAPTURE   ·   O / Y  RETURN"));
    PhotoChip->SetContent(PhotoText);
    PhotoChip->SetVisibility(ESlateVisibility::Collapsed);

    // --- Crew call wheel.
    USizeBox* Wheel = WidgetTree->ConstructWidget<USizeBox>();
    WheelPanel = Wheel;
    Wheel->SetWidthOverride(460.0f);
    Wheel->SetHeightOverride(460.0f);
    Pin(Canvas, Wheel, FAnchors(0.5f), FVector2D(0.5f), FVector2D::ZeroVector, FVector2D(460, 460))->SetZOrder(5);
    UOverlay* WheelStack = WidgetTree->ConstructWidget<UOverlay>();
    Wheel->AddChild(WheelStack);
    URaftSimHudArt* WheelArt = WidgetTree->ConstructWidget<URaftSimHudArt>();
    WheelArt->SetKind(ERaftSimHudArtKind::CommandWheel);
    UOverlaySlot* WheelArtSlot = WheelStack->AddChildToOverlay(WheelArt);
    WheelArtSlot->SetHorizontalAlignment(HAlign_Fill);
    WheelArtSlot->SetVerticalAlignment(VAlign_Fill);
    UCanvasPanel* WheelLabels = WidgetTree->ConstructWidget<UCanvasPanel>();
    UOverlaySlot* LabelsSlot = WheelStack->AddChildToOverlay(WheelLabels);
    LabelsSlot->SetHorizontalAlignment(HAlign_Fill);
    LabelsSlot->SetVerticalAlignment(VAlign_Fill);
    auto WheelLabel = [this, WheelLabels](FVector2D At, const FText& Call, const FText& Key)
    {
        UVerticalBox* Words = WidgetTree->ConstructWidget<UVerticalBox>();
        UTextBlock* CallText = MakeText(Font("BoldCondensed", 16, 40), Paper());
        CallText->SetText(Call);
        CallText->SetJustification(ETextJustify::Center);
        Words->AddChildToVerticalBox(CallText)->SetHorizontalAlignment(HAlign_Center);
        UTextBlock* KeyText = MakeText(Label(11), Gold());
        KeyText->SetText(Key);
        KeyText->SetJustification(ETextJustify::Center);
        Words->AddChildToVerticalBox(KeyText)->SetHorizontalAlignment(HAlign_Center);
        Pin(WheelLabels, Words, FAnchors(0, 0), FVector2D(0.5f), At);
    };
    // Each call sits mid-petal, between the stop disc and the rim.
    WheelLabel(FVector2D(230, 80), NSLOCTEXT("RaftSim", "CallForward", "ALL FORWARD"),
        NSLOCTEXT("RaftSim", "KeyForward", "1  ·  D-PAD UP"));
    WheelLabel(FVector2D(366, 230), NSLOCTEXT("RaftSim", "CallRight", "TURN RIGHT"),
        NSLOCTEXT("RaftSim", "KeyRight", "4  ·  RIGHT"));
    WheelLabel(FVector2D(230, 380), NSLOCTEXT("RaftSim", "CallBack", "BACK PADDLE"),
        NSLOCTEXT("RaftSim", "KeyBack", "2  ·  D-PAD DOWN"));
    WheelLabel(FVector2D(94, 230), NSLOCTEXT("RaftSim", "CallLeft", "TURN LEFT"),
        NSLOCTEXT("RaftSim", "KeyLeft", "3  ·  LEFT"));
    WheelLabel(FVector2D(230, 230), NSLOCTEXT("RaftSim", "CallStop", "STOP"),
        NSLOCTEXT("RaftSim", "KeyStop", "5  ·  A"));
    // Off the petals, in the corner: the recall after a high-side.
    WheelLabel(FVector2D(392, 420), NSLOCTEXT("RaftSim", "CallSeats", "BACK TO SEATS"),
        NSLOCTEXT("RaftSim", "KeySeats", "6  ·  B"));
    WheelPanel->SetVisibility(ESlateVisibility::Collapsed);

    // --- Pause: the river blurs behind a guide's notebook of choices.
    UBackgroundBlur* Blur = WidgetTree->ConstructWidget<UBackgroundBlur>();
    PausePanel = Blur;
    Blur->SetBlurStrength(7.0f);
    Blur->SetHorizontalAlignment(HAlign_Fill);
    Blur->SetVerticalAlignment(VAlign_Fill);
    UCanvasPanelSlot* PauseSlot = Canvas->AddChildToCanvas(Blur);
    PauseSlot->SetAnchors(FAnchors(0, 0, 1, 1));
    PauseSlot->SetOffsets(FMargin(0));
    PauseSlot->SetZOrder(8);
    UBorder* PauseTint = WidgetTree->ConstructWidget<UBorder>();
    PauseTint->SetBrushColor(FLinearColor(0.004f, 0.012f, 0.014f, 0.62f));
    PauseTint->SetPadding(FMargin(96, 60));
    PauseTint->SetHorizontalAlignment(HAlign_Left);
    PauseTint->SetVerticalAlignment(VAlign_Center);
    Blur->SetContent(PauseTint);
    UVerticalBox* PauseColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    PauseTint->SetContent(PauseColumn);
    UTextBlock* PausedTitle = MakeText(Display(80), Paper());
    PausedTitle->SetText(NSLOCTEXT("RaftSim", "PausedTitle", "PAUSED"));
    PauseColumn->AddChildToVerticalBox(PausedTitle)->SetPadding(FMargin(0, 0, 0, -8));
    PauseRiverText = MakeText(Label(17), Gold());
    PauseColumn->AddChildToVerticalBox(PauseRiverText);
    PauseStatsText = MakeText(Body(17), FLinearColor(0.80f, 0.86f, 0.82f));
    PauseColumn->AddChildToVerticalBox(PauseStatsText)->SetPadding(FMargin(0, 2, 0, 24));
    USizeBox* ActionWidth = WidgetTree->ConstructWidget<USizeBox>();
    ActionWidth->SetWidthOverride(440.0f);
    PauseColumn->AddChildToVerticalBox(ActionWidth);
    PauseActions = WidgetTree->ConstructWidget<UVerticalBox>();
    ActionWidth->AddChild(PauseActions);
    auto Action = [this](const FText& LabelText, FName Handler)
    {
        auto* Button = WidgetTree->ConstructWidget<UButton>();
        Button->SetStyle(RowLook(10.0f).Normal);
        auto* Text = MakeText(Label(22), Paper(), false);
        Text->SetText(LabelText);
        auto* LabelSlot = CastChecked<UButtonSlot>(Button->AddChild(Text));
        LabelSlot->SetHorizontalAlignment(HAlign_Left);
        LabelSlot->SetPadding(FMargin(10, 4));
        FScriptDelegate Delegate;
        Delegate.BindUFunction(this, Handler);
        Button->OnClicked.Add(Delegate);
        PauseActions->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 5));
        PauseLabels.Add(Text);
        return Button;
    };
    ResumeButton = Action(NSLOCTEXT("RaftSim", "ResumeAction", "RESUME RIVER"), GET_FUNCTION_NAME_CHECKED(URaftSimRunHudWidget, ResumeRun));
    Action(NSLOCTEXT("RaftSim", "PhotoAction", "PHOTO MODE"), GET_FUNCTION_NAME_CHECKED(URaftSimRunHudWidget, OpenPhotoMode));
    Action(NSLOCTEXT("RaftSim", "RestartAction", "RESTART CHECKPOINT"), GET_FUNCTION_NAME_CHECKED(URaftSimRunHudWidget, RestartRun));
    Action(NSLOCTEXT("RaftSim", "LeaveAction", "RETURN TO RIVERS"), GET_FUNCTION_NAME_CHECKED(URaftSimRunHudWidget, LeaveRun));
    UHorizontalBox* PauseHints = WidgetTree->ConstructWidget<UHorizontalBox>();
    PauseColumn->AddChildToVerticalBox(PauseHints)->SetPadding(FMargin(0, 22, 0, 0));
    AddPrompt(PauseHints, NSLOCTEXT("RaftSim", "PauseKeyResume", "ESC / P / MENU"), NSLOCTEXT("RaftSim", "PauseResume", "RESUME"));
    AddPrompt(PauseHints, NSLOCTEXT("RaftSim", "PauseKeyLeave", "HOME / B"), NSLOCTEXT("RaftSim", "PauseLeave", "LEAVE"));
    PausePanel->SetVisibility(ESlateVisibility::Collapsed);

    // --- Scenario title card (lower left).
    TransitionBounds = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());
    TransitionBounds->SetStretch(EStretch::ScaleToFit);
    TransitionBounds->SetStretchDirection(EStretchDirection::DownOnly);
    UCanvasPanelSlot* TransitionSlot = Canvas->AddChildToCanvas(TransitionBounds);
    TransitionSlot->SetAnchors(FAnchors(0.0f, 1.0f));
    TransitionSlot->SetAlignment(FVector2D(0.0f, 1.0f));
    TransitionSlot->SetPosition(FVector2D(40.0f, -40.0f));
    TransitionSlot->SetSize(FVector2D(780.0f, 400.0f));
    TransitionWrap = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
    TransitionWrap->SetWidthOverride(780.0f);
    UScaleBoxSlot* FitSlot = CastChecked<UScaleBoxSlot>(TransitionBounds->AddChild(TransitionWrap));
    FitSlot->SetHorizontalAlignment(HAlign_Left);
    FitSlot->SetVerticalAlignment(VAlign_Bottom);
    UVerticalBox* TitleCard = WidgetTree->ConstructWidget<UVerticalBox>();
    TransitionWrap->AddChild(TitleCard);
    TransitionKicker = MakeText(Label(16), Gold());
    TitleCard->AddChildToVerticalBox(TransitionKicker);
    TransitionTitle = MakeText(Display(52), Paper());
    TransitionTitle->SetAutoWrapText(false);
    TransitionTitle->SetWrapTextAt(780.0f);
    TitleCard->AddChildToVerticalBox(TransitionTitle)->SetPadding(FMargin(0, -6, 0, 2));
    TransitionText = MakeText(Strong(20), Paper());
    TransitionText->SetShadowColorAndOpacity(FLinearColor(0, 0, 0, 0.9f));
    // Fixed wrap width produces a stable desired height; ScaleBox fits the
    // entire card only when necessary, without truncation or scroll controls.
    TransitionText->SetAutoWrapText(false);
    TransitionText->SetWrapTextAt(780.0f);
    TitleCard->AddChildToVerticalBox(TransitionText);
    SubtitleText->SetText(FText::GetEmpty());
    OverlayText->SetText(FText::GetEmpty());
    TransitionText->SetText(FText::GetEmpty());
    TrainingText->SetText(FText::GetEmpty());
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
            AppliedUiScale = FMath::Clamp(Settings.UiScale, 0.75f, 1.5f);
            // Scale text within the safe viewport; scaling the whole canvas
            // about its centre pushes anchored controls off the screen.
            const float TextScale = FMath::Clamp(Settings.TextScale, 0.85f, 1.35f);
            for (auto* Text : {StatusText.Get(), StatsText.Get(), EnergyText.Get(), RiverText.Get(), ProgressText.Get(),
                     EnvironmentText.Get(), ClockText.Get(), ScoreText.Get(), TrainingText.Get(),
                     SubtitleText.Get(), RescueText.Get()})
            {
                auto Font = Text->GetFont();
                Font.Size = FMath::RoundToInt(Font.Size * TextScale);
                Text->SetFont(Font);
            }
            AppliedUiScale = 1.0f;
            const FLinearColor Cue = Settings.ColorCueMode == ERaftSimColorCueMode::Monochrome
                ? FLinearColor::White
                : Settings.ColorCueMode == ERaftSimColorCueMode::DeuteranopiaSafe ||
                    Settings.ColorCueMode == ERaftSimColorCueMode::ProtanopiaSafe
                    ? FLinearColor(0.2f, 0.75f, 1.0f)
                    : River();
            RouteRibbon->SetAccent(Cue);
            StateChip->SetBrush(Rounded(Cue, 4.0f));
        }
    }
}

void URaftSimRunHudWidget::BeginScenarioPresentation(const FText& Title, const FText& Briefing)
{
    if (TransitionText == nullptr)
    {
        return;
    }
    TransitionKicker->SetText(NSLOCTEXT("RaftSim", "NowRunning", "NOW RUNNING"));
    TransitionTitle->SetText(Title);
    TransitionText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "ScenarioTransition", "{0}\n\nGuide from the stern · Tab: crew calls · M: scout · E/R/F: rescue"),
        Briefing));
    TransitionWrap->SetRenderOpacity(0.0f);
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
    const bool bCard = Overlay == ERaftSimHudOverlay::ScoutBoard || Overlay == ERaftSimHudOverlay::ReplayReview;
    if (OverlayBounds) OverlayBounds->SetVisibility(bCard
        ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
    if (PausePanel) PausePanel->SetVisibility(Overlay == ERaftSimHudOverlay::Pause
        ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (WheelPanel) WheelPanel->SetVisibility(Overlay == ERaftSimHudOverlay::CommandWheel
        ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (PhotoChip) PhotoChip->SetVisibility(Overlay == ERaftSimHudOverlay::PhotoMode
        ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (PauseActions) PauseActions->SetVisibility(Overlay == ERaftSimHudOverlay::Pause
        ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (Overlay == ERaftSimHudOverlay::Pause)
    {
        if (RunManager)
        {
            PauseRiverText->SetText(RiverText->GetText());
            PauseStatsText->SetText(FText::FromString(FString::Printf(
                TEXT("%s on the water   ·   %.0f%% of the run   ·   %d swims   ·   %d incidents"),
                *Clock(RunManager->GetRunTimeSeconds()), RunManager->GetProgressFraction() * 100.0f,
                RunManager->GetSwimCount(), RunManager->GetSafetyIncidentCount())));
        }
        if (ResumeButton) ResumeButton->SetKeyboardFocus();
    }
    if (OverlayText == nullptr)
    {
        return;
    }
    switch (Overlay)
    {
        case ERaftSimHudOverlay::ScoutBoard:
            OverlayTitle->SetText(NSLOCTEXT("RaftSim", "ScoutTitle", "SCOUT THE RAPID"));
            OverlayText->SetText(NSLOCTEXT("RaftSim", "ScoutOverlay",
                "Read the tongue and the downstream V.\nMark laterals, holes, rocks, strainers and recovery eddies.\n\nCyan ghost: your best prior line.\nAmber cues: inferred or procedural geography.\n\nM / D-pad Down closes the scout."));
            break;
        case ERaftSimHudOverlay::ReplayReview:
            OverlayTitle->SetText(NSLOCTEXT("RaftSim", "ReviewTitle", "AFTER-ACTION REVIEW"));
            OverlayText->SetText(RunManager
                ? FText::Format(NSLOCTEXT("RaftSim", "ReviewOverlay",
                    "{0}\n\nCyan route: your best prior line. Compare entry angle, incidents and recovery choices.\n\nV / Left Trigger closes the review."),
                    RunManager->GetAfterActionSummary())
                : NSLOCTEXT("RaftSim", "ReviewUnavailable", "No run has been recorded yet."));
            break;
        case ERaftSimHudOverlay::Pause:
            OverlayText->SetText(NSLOCTEXT("RaftSim", "PauseOverlay", "The river will wait."));
            break;
        default:
            OverlayTitle->SetText(FText::GetEmpty());
            OverlayText->SetText(FText::GetEmpty());
            break;
    }
}

void URaftSimRunHudWidget::ResumeRun()
{
    if (auto* Controller = Cast<ARaftSimGuidePlayerController>(GetOwningPlayer())) Controller->TogglePauseMenu();
}
void URaftSimRunHudWidget::RestartRun()
{
    if (auto* Controller = Cast<ARaftSimGuidePlayerController>(GetOwningPlayer())) Controller->RestartCheckpoint();
}
void URaftSimRunHudWidget::LeaveRun()
{
    if (auto* Controller = Cast<ARaftSimGuidePlayerController>(GetOwningPlayer())) Controller->ReturnToMainMenu();
}
void URaftSimRunHudWidget::OpenPhotoMode()
{
    if (auto* Controller = Cast<ARaftSimGuidePlayerController>(GetOwningPlayer())) Controller->TogglePhotoMode();
}

void URaftSimRunHudWidget::SetPlayHudVisible(bool bVisible)
{
    const ESlateVisibility Shown = bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
    StatusCard->SetVisibility(Shown);
    RouteBlock->SetVisibility(Shown);
    ConditionsCard->SetVisibility(Shown);
    PromptBar->SetVisibility(Shown);
    EdgeShade->SetVisibility(VisibleOverlay == ERaftSimHudOverlay::PhotoMode
        ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    TrainingCard->SetVisibility(bVisible && !TrainingText->GetText().IsEmpty() ? Shown : ESlateVisibility::Collapsed);
}

void URaftSimRunHudWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    HudClock += DeltaSeconds;

    const FVector2D Viewport = Geometry.GetLocalSize();
    if (Viewport.X > 0 && Viewport.Y > 0)
    {
        CastChecked<UCanvasPanelSlot>(OverlayBounds->Slot)->SetSize(FVector2D(
            FMath::Min(740.0, Viewport.X - 32.0), FMath::Min(560.0, Viewport.Y - 32.0)));
        CastChecked<UCanvasPanelSlot>(RouteBlock->Slot)->SetSize(FVector2D(
            FMath::Clamp(Viewport.X - 900.0, 260.0, 560.0), 70.0));
        for (auto* Card : {SubtitleCard.Get(), RescueCard.Get()})
        {
            auto* CardSlot = CastChecked<UCanvasPanelSlot>(Card->Slot);
            CardSlot->SetSize(FVector2D(FMath::Min(820.0, Viewport.X - 48.0), CardSlot->GetSize().Y));
        }
        // Narrow screens keep the run card and pause, and drop the prompt strip.
        PromptBar->SetRenderOpacity(Viewport.X < 1100.0 ? 0.0f : 1.0f);
    }
    SetPlayHudVisible(VisibleOverlay == ERaftSimHudOverlay::None);
    TransitionBounds->SetVisibility(VisibleOverlay == ERaftSimHudOverlay::None && TransitionRemaining > 0
        ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    for (int32 Index = 0; Index < PauseLabels.Num(); ++Index)
    {
        if (auto* Button = Cast<UButton>(PauseActions->GetChildAt(Index)))
        {
            const bool bLit = Button->HasKeyboardFocus() || Button->IsHovered();
            const bool bWasLit = PauseLabels[Index]->GetColorAndOpacity().GetSpecifiedColor().Equals(Gold());
            if (bLit != bWasLit)
            {
                Button->SetStyle(bLit ? RowLook(10.0f).Focused : RowLook(10.0f).Normal);
                PauseLabels[Index]->SetColorAndOpacity(bLit ? Gold() : Paper());
            }
        }
    }
    if (TransitionBounds && Viewport.X > 0.0 && Viewport.Y > 0.0 &&
        !Viewport.Equals(LastTransitionViewport))
    {
        const auto Region = RaftSimTransitionLayout::Resolve(Viewport, AppliedUiScale);
        UCanvasPanelSlot* TransitionSlot = CastChecked<UCanvasPanelSlot>(TransitionBounds->Slot);
        TransitionSlot->SetPosition(Region.Position);
        TransitionSlot->SetSize(Region.Size);
        TransitionWrap->SetWidthOverride(Region.Size.X);
        TransitionText->SetWrapTextAt(Region.Size.X);
        TransitionTitle->SetWrapTextAt(Region.Size.X);
        LastTransitionViewport = Viewport;
    }

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
        if (RiverText->GetText().IsEmpty())
        {
            FRaftSimCareerScenarioDefinition Scenario;
            const bool bKnown = URaftSimProgressionLibrary::FindScenario(RunManager->ScenarioId, Scenario);
            const FText Title = RaftSimUIArt::RiverCardFor(RunManager->ScenarioId,
                bKnown ? Scenario.DisplayName : NSLOCTEXT("RaftSim", "OpenWater", "Open water")).Title;
            RiverText->SetText(FText::FromString(Title.ToString().ToUpper()));
        }
        const ERaftSimRunState State = RunManager->GetRunState();
        StateText->SetText(State == ERaftSimRunState::Running
            ? NSLOCTEXT("RaftSim", "StateRunning", "ON THE WATER")
            : State == ERaftSimRunState::Finished
                ? NSLOCTEXT("RaftSim", "StateFinished", "RUN COMPLETE")
                : NSLOCTEXT("RaftSim", "StateReady", "READY"));
        StatusText->SetText(FText::FromString(Clock(RunManager->GetRunTimeSeconds())));
        StatsText->SetText(FText::FromString(FString::Printf(TEXT("%d SWIMS   ·   %d INCIDENTS"),
            RunManager->GetSwimCount(), RunManager->GetSafetyIncidentCount())));
        if (EnergyText != nullptr)
        {
            const ARaftSimRaftActor* EnergyRaft = nullptr;
            if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It) EnergyRaft = *It;
            if (EnergyRaft != nullptr)
            {
                const float Energy = EnergyRaft->GetCrewEnergy();
                const int32 Bars = FMath::Clamp(FMath::RoundToInt(Energy * 10.0f), 0, 10);
                FString Line = FString::Printf(TEXT("CREW ENERGY  %s%s  %d%%"),
                    *FString::ChrN(Bars, TEXT('|')), *FString::ChrN(10 - Bars, TEXT('.')),
                    FMath::RoundToInt(Energy * 100.0f));
                float Tired = 1.0f;
                const FName Weakest = EnergyRaft->GetMostTiredPaddler(Tired);
                if (!Weakest.IsNone() && Tired < 0.35f)
                {
                    Line += FString::Printf(TEXT("   ·   %s IS SPENT - CALL A REST"),
                        *URaftSimCrewRoster::GetFirstName(Weakest).ToString().ToUpper());
                }
                EnergyText->SetText(FText::FromString(Line));
                EnergyText->SetColorAndOpacity(FSlateColor(Energy > 0.6f ? FLinearColor(0.62f, 0.86f, 0.58f)
                    : (Energy > 0.3f ? Gold() : Danger())));
            }
        }
        RouteRibbon->SetProgress(RunManager->GetProgressFraction());
        const float StationKm = RunManager->GetCurrentStationM() / 1000.0f;
        const float LengthKm = RunManager->StartStationM >= 0.0f && RunManager->FinishStationM > RunManager->StartStationM
            ? (RunManager->FinishStationM - RunManager->StartStationM) / 1000.0f : -1.0f;
        const float TravelledKm = LengthKm > 0.0f
            ? FMath::Clamp(StationKm - RunManager->StartStationM / 1000.0f, 0.0f, LengthKm) : StationKm;
        ProgressText->SetText(FText::FromString(LengthKm > 0.0f
            ? FString::Printf(TEXT("%.0f%%   ·   KM %.2f OF %.1f"),
                RunManager->GetProgressFraction() * 100.0f, TravelledKm, LengthKm)
            : FString::Printf(TEXT("%.0f%%   ·   KM %.2f"), RunManager->GetProgressFraction() * 100.0f, StationKm)));

        const uint8 RunStateValue = static_cast<uint8>(State);
        if (LastObservedRunState != RunStateValue)
        {
            if (State == ERaftSimRunState::Finished && TransitionText != nullptr)
            {
                const ERaftSimMedal Medal = RunManager->GetAwardedMedal();
                TransitionKicker->SetText(Medal == ERaftSimMedal::None
                    ? NSLOCTEXT("RaftSim", "FinishedKicker", "TAKE-OUT REACHED")
                    : FText::Format(NSLOCTEXT("RaftSim", "MedalKicker", "{0} MEDAL"),
                        FText::FromString(UEnum::GetDisplayValueAsText(Medal).ToString().ToUpper())));
                TransitionTitle->SetText(NSLOCTEXT("RaftSim", "RunCompleteTitle", "RUN COMPLETE"));
                TransitionText->SetText(FText::Format(
                    NSLOCTEXT("RaftSim", "RunCompleteTransition", "{0}\n\nV / Left Trigger: review route"),
                    RunManager->GetAfterActionSummary()));
                TransitionWrap->SetRenderOpacity(1.0f);
                TransitionRemaining = 5.0f;
            }
            LastObservedRunState = RunStateValue;
        }
        ScoreText->SetText(State == ERaftSimRunState::Finished
            ? RunManager->GetAfterActionSummary() : FText::GetEmpty());
        ScoreText->SetVisibility(ScoreText->GetText().IsEmpty()
            ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    }

    if (EnvironmentText != nullptr && PresentationDirector != nullptr)
    {
        const FRaftSimPresentationEnvironmentState Environment =
            PresentationDirector->GetEnvironmentState();
        EnvironmentText->SetText(FText::FromString(
            PresentationDirector->GetWeatherDisplayName().ToString().ToUpper()));
        const float Hours = FMath::Fmod(FMath::Max(Environment.TimeOfDayHours, 0.0f), 24.0f);
        ClockText->SetText(FText::FromString(FString::Printf(TEXT("%02d:%02d"),
            FMath::FloorToInt(Hours), FMath::FloorToInt(FMath::Frac(Hours) * 60.0f))));
    }
    ConditionsCard->SetRenderOpacity(PresentationDirector != nullptr ? 1.0f : 0.0f);

    if (TrainingText != nullptr)
    {
        TrainingText->SetText(TrainingDirector != nullptr
            ? FText::Format(NSLOCTEXT("RaftSim", "TrainingHud", "GUIDE SCHOOL  {0}/{1}\n{2}"),
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
        if (Raft != nullptr && (Raft->GetSwimmerCount() > 0 || Raft->IsAssistedBoardingActive()))
        {
            const FRaftSimRescueInteractionState Rescue = Raft->GetRescueInteractionState();
            // Swimmers by name (URaftSimCrewRoster), not their seat ids.
            RescueText->SetText(FText::FromString(FString::Printf(
                TEXT("SWIMMER  ·  %s  ·  %.1f M  ·  %s   |   E REACH   R THROW   F RESEAT"),
                *URaftSimCrewRoster::GetDisplayName(Rescue.TargetPassengerId).ToString().ToUpper(),
                Rescue.DistanceMeters, *Rescue.FeedbackCode.ToString().ToUpper())));
            if (Raft->GetRaftMode() == ERaftSimRaftMode::Capsized)
                RescueText->SetText(Raft->GetFlipLinePrompt());
            else if (Raft->IsPassengerSwimming(TEXT("guide")))
                RescueText->SetText(FText::FromString(TEXT("SWIM TO THE RAFT - aim and W / left stick to swim; F / B to climb in at the tube")));
            else if (Rescue.FeedbackCode == TEXT("rescue_finish_high_side_first"))
                RescueText->SetText(FText::FromString(TEXT("CREW ON THE HIGH SIDE - call BACK TO YOUR SEATS (6) before throwing the bag")));
            else if (const FText Stage = Raft->GetRescuePrompt(); !Stage.IsEmpty())
                RescueText->SetText(Stage);
        }
        else if (Raft != nullptr && Raft->GetRaftMode() == ERaftSimRaftMode::Upright &&
            Raft->GetActiveCrewCommand() == ERaftSimCrewCommand::HighSide &&
            Raft->GetPendingCrewCommand() == ERaftSimCrewCommand::HighSide)
        {
            RescueText->SetText(NSLOCTEXT("RaftSim", "HudHighSideHold",
                "CREW ON THE HIGH SIDE   ·   6  /  WHEEL + B   BACK TO YOUR SEATS"));
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
    SubtitleCard->SetVisibility(!SubtitleText->GetText().IsEmpty() && TransitionRemaining <= 0 &&
        VisibleOverlay != ERaftSimHudOverlay::PhotoMode
        ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    const bool bRescue = !RescueText->GetText().IsEmpty() && VisibleOverlay == ERaftSimHudOverlay::None;
    RescueCard->SetVisibility(bRescue ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (bRescue)
    {
        RescueCard->SetRenderOpacity(0.78f + 0.22f * FMath::Sin(HudClock * 6.0f));
    }
    if (TransitionRemaining > 0.0f && TransitionText != nullptr)
    {
        TransitionRemaining -= DeltaSeconds;
        const float Elapsed = 5.0f - TransitionRemaining;
        const float FadeIn = FMath::Clamp(Elapsed / 0.4f, 0.0f, 1.0f);
        const float FadeOut = FMath::Clamp(TransitionRemaining / 1.2f, 0.0f, 1.0f);
        TransitionWrap->SetRenderOpacity(FMath::Min(FadeIn, FadeOut));
        if (TransitionRemaining <= 0.0f)
        {
            TransitionText->SetText(FText::GetEmpty());
            TransitionTitle->SetText(FText::GetEmpty());
            TransitionKicker->SetText(FText::GetEmpty());
        }
    }
    UpdateRapidTitle(DeltaSeconds);
}

namespace
{
constexpr float kRapidTitleSeconds = 5.6f;
constexpr float kRapidTitleOutSeconds = 1.3f;

float EaseOut(float A) { A = FMath::Clamp(A, 0.0f, 1.0f); return 1.0f - (1.0f - A) * (1.0f - A) * (1.0f - A); }
float EaseIn(float A) { A = FMath::Clamp(A, 0.0f, 1.0f); return A * A; }
}

void URaftSimRunHudWidget::ShowRapidTitle(const FRaftSimRapidTitle& Rapid)
{
    if (!RapidName) return;
    ActiveRapidTitle = &Rapid;
    RapidTitleElapsed = 0.0f;
    RapidName->SetText(FText::FromString(FString(Rapid.Name).ToUpper()));
    RapidGrade->SetText(RaftSimRapidTitles::GradeLine(Rapid));
    // The river and run this rapid belongs to, as the scenario card names it.
    const FText River = RiverText ? RiverText->GetText() : FText::GetEmpty();
    RapidKicker->SetText(River.IsEmpty() ? NSLOCTEXT("RaftSim", "RapidAhead", "RAPID AHEAD") : River);
    UE_LOG(LogTemp, Display, TEXT("RAPID_TITLE id=%s name=%s station_m=%.1f control_m=%.1f"), Rapid.Id, Rapid.Name,
        RunManager ? RunManager->GetCurrentStationM() : -1.f, Rapid.ControlStationM);
}

FString URaftSimRunHudWidget::GetVisibleRapidTitleId() const
{
    return ActiveRapidTitle && RapidTitleElapsed >= 0.0f ? FString(ActiveRapidTitle->Id) : FString();
}

void URaftSimRunHudWidget::UpdateRapidTitle(float DeltaSeconds)
{
    if (!RapidName || !GetWorld()) return;
    if (!bRapidTitlesResolved)
    {
        bRapidTitlesResolved = true;
        RapidTitles = RaftSimRapidTitles::ForMap(GetWorld()->GetMapName());
        RapidTitleShown.Init(false, RapidTitles.Num());
    }
    if (!RapidRaft.IsValid())
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It) RapidRaft = *It;

    // Name each rapid once as the boat closes on it: about nine seconds out
    // at the current speed (45-110 m before its main feature). A restart
    // upstream re-arms it; one card at a time, never over the scenario card.
    if (RunManager && RunManager->GetRunState() == ERaftSimRunState::Running && !RapidTitles.IsEmpty())
    {
        const float Station = RunManager->GetCurrentStationM();
        const float Speed = RapidRaft.IsValid() ? float(RapidRaft->GetRaftVelocity().Size2D()) : 2.0f;
        const float Lead = FMath::Clamp(Speed * 9.0f, 45.0f, 110.0f);
        for (int32 Index = 0; Index < RapidTitles.Num(); ++Index)
        {
            const float Control = RapidTitles[Index]->ControlStationM;
            if (Station < Control - Lead - 40.0f) RapidTitleShown[Index] = false;
            else if (!RapidTitleShown[Index] && Station >= Control - Lead && Station < Control + 15.0f &&
                RapidTitleElapsed < 0.0f && TransitionRemaining <= 0.0f && VisibleOverlay == ERaftSimHudOverlay::None)
            {
                RapidTitleShown[Index] = true;
                ShowRapidTitle(*RapidTitles[Index]);
            }
        }
    }

    const bool bVisible = RapidTitleElapsed >= 0.0f && VisibleOverlay == ERaftSimHudOverlay::None;
    RapidBand->SetVisibility(bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    RapidColumn->SetVisibility(bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (RapidTitleElapsed < 0.0f) return;
    // Paused overlays hold the card where it is.
    if (VisibleOverlay == ERaftSimHudOverlay::None) RapidTitleElapsed += DeltaSeconds;
    const float T = RapidTitleElapsed;
    if (T >= kRapidTitleSeconds)
    {
        RapidTitleElapsed = -1.0f;
        ActiveRapidTitle = nullptr;
        return;
    }
    bool bReducedMotion = false;
    if (const URaftSimSaveSubsystem* Save = GetGameInstance() ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
        if (Save->GetSave()) bReducedMotion = Save->GetSave()->Settings.MotionIntensity < 0.05f;

    // In: the band darkens, the name resolves out of wide tracking and
    // settles, the rule draws outward, the class lands last. Hold: a slow
    // push. Out: the name lets go, tracking open again, as everything fades.
    const float Out = 1.0f - EaseIn((T - (kRapidTitleSeconds - kRapidTitleOutSeconds)) / kRapidTitleOutSeconds);
    const float NameIn = EaseOut(T / 1.6f);
    RapidBand->SetRenderOpacity(EaseOut(T / 0.7f) * Out);
    RapidKicker->SetRenderOpacity(EaseOut((T - 0.15f) / 0.6f) * Out);
    RapidName->SetRenderOpacity(EaseOut((T - 0.05f) / 0.9f) * Out);
    RapidGrade->SetRenderOpacity(EaseOut((T - 0.75f) / 0.6f) * Out);
    RapidRule->SetProgress(EaseOut((T - 0.35f) / 1.0f) * (0.35f + 0.65f * Out));
    RapidRule->SetRenderOpacity(Out);
    FSlateFontInfo Font = RapidName->GetFont();
    const float Hold = FMath::Clamp((T - 1.6f) / (kRapidTitleSeconds - 1.6f), 0.0f, 1.0f);
    Font.LetterSpacing = bReducedMotion ? 220 : FMath::RoundToInt(FMath::Lerp(950.0f, 220.0f, NameIn) + 60.0f * Hold + 260.0f * (1.0f - Out));
    RapidName->SetFont(Font);
    FWidgetTransform Transform;
    if (!bReducedMotion)
    {
        Transform.Translation = FVector2D(0.0f, 16.0f * (1.0f - NameIn));
        Transform.Scale = FVector2D(1.0f + 0.04f * Hold);
    }
    RapidName->SetRenderTransform(Transform);
}

#if !UE_BUILD_SHIPPING
// Captures the real game HUD through the same controller actions as player
// input. Core ticker continues while paused; world timers would never fire.
static FAutoConsoleCommandWithWorldAndArgs GReviewHud(
    TEXT("RaftSim.HudScreen"),
    TEXT("Review pause|scout|crew|title|none [capture=label] in the current river."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
        [](const TArray<FString>& Args, UWorld* World)
        {
            auto* PC = Cast<ARaftSimGuidePlayerController>(UGameplayStatics::GetPlayerController(World, 0));
            if (!PC || !PC->GetRunHud() || Args.IsEmpty()) return;
            const TWeakObjectPtr<ARaftSimGuidePlayerController> Controller = PC;
            const FString Screen = Args[0];
            const auto ShowScreen = [Controller, Screen](float)
            {
                if (auto* Player = Controller.Get(); Player && Player->GetRunHud())
                {
                    if (Screen == TEXT("pause")) Player->TogglePauseMenu();
                    else if (Screen == TEXT("scout")) Player->ToggleScoutBoard();
                    else if (Screen == TEXT("title")) Player->GetRunHud()->BeginScenarioPresentation(
                        FText::FromString(TEXT("South Fork American")),
                        FText::FromString(TEXT("Guide the reconstructed 33.2 km playable reach.")));
                    else if (Screen == TEXT("rapid"))
                    {
                        // The first rapid of this river (any rapid if unmapped).
                        const auto Rapids = RaftSimRapidTitles::ForMap(Player->GetWorld()->GetMapName());
                        Player->GetRunHud()->ShowRapidTitle(Rapids.IsEmpty() ? RaftSimRapidTitles::All()[0] : *Rapids[0]);
                    }
                    else Player->GetRunHud()->ShowOverlay(Screen == TEXT("crew")
                        ? ERaftSimHudOverlay::CommandWheel : ERaftSimHudOverlay::None);
                    if (Screen == TEXT("swimmer")) Player->GetRunHud()->ShowSubtitle(
                        FText::FromString(TEXT("Guide: High side! Get down!")), 6.0f);
                }
                return false;
            };
            const bool bCapture = Args.ContainsByPredicate([](const FString& Arg)
            {
                return Arg.StartsWith(TEXT("capture="));
            });
            // Let the actual river initialize and run before freezing it for a
            // capture. An immediate startup pause prevents its first water tick.
            if (bCapture) FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(ShowScreen),
                Screen == TEXT("title") ? 6.5f : 5.0f);
            else ShowScreen(0.0f);
            for (const FString& Arg : Args)
            {
                if (!Arg.StartsWith(TEXT("capture="))) continue;
                const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(),
                    TEXT("Screenshots"), FPaths::GetCleanFilename(Arg.RightChop(8)) + TEXT(".png"));
                FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([Path](float)
                {
                    FScreenshotRequest::RequestScreenshot(Path, true, false);
                    return false;
                }), 8.0f);
                FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
                {
                    FPlatformMisc::RequestExit(false);
                    return false;
                }), 11.0f);
            }
        }));
#endif
