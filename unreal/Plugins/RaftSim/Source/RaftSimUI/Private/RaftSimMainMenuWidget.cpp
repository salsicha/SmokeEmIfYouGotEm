#include "RaftSimMainMenuWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/AudioComponent.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/Paths.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimRiverBackdrop.h"
#include "RaftSimUIArt.h"
#include "RaftSimUITheme.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Sound/SoundWaveProcedural.h"
#include "TimerManager.h"
#include "UnrealClient.h"

using namespace RaftSimUITheme;

namespace
{

FText ModeName(ERaftSimGameMode Mode)
{
    switch (Mode)
    {
        case ERaftSimGameMode::GuidedDescent:
            return NSLOCTEXT("RaftSim", "GuidedDescent", "Guided Descent Career");
        case ERaftSimGameMode::FreeRun:
            return NSLOCTEXT("RaftSim", "FreeRun", "Free Run");
        default:
            return NSLOCTEXT("RaftSim", "TrainingEddy", "Training Eddy");
    }
}

struct FRunButtonSpec
{
    const TCHAR* ScenarioId;
    const TCHAR* Label;
    ERaftSimGameMode Mode;
};

// River cards on the main screen, in menu order. Anything else in the catalog
// that is a reference/challenge run (section 10+) or training is appended
// with its catalog display name, so a new river map shows up without touching
// this list.
const FRunButtonSpec RunButtonSpecs[] = {
    {TEXT("south_fork_full_descent"), TEXT("South Fork American: Chili Bar to Salmon Falls"),
        ERaftSimGameMode::FreeRun},
    {TEXT("hance_challenge"), TEXT("Colorado, Grand Canyon: Hance"), ERaftSimGameMode::FreeRun},
    {TEXT("upper_huacas_challenge"), TEXT("Pacuare: Upper Huacas"), ERaftSimGameMode::FreeRun},
    {TEXT("futaleufu_continuous"), TEXT("Futaleufu: Rio Azul to the Pasarela"), ERaftSimGameMode::FreeRun},
    {TEXT("lava_canyon_challenge"), TEXT("Chilko: Lava Canyon"), ERaftSimGameMode::FreeRun},
    {TEXT("zambezi_reference_run"),
        TEXT("Zambezi, Batoka Gorge: Boiling Pot to Mukuni Beach"), ERaftSimGameMode::FreeRun},
    {TEXT("training_eddy_basics"), TEXT("Training Eddy: Guide School (flat-water tank)"),
        ERaftSimGameMode::TrainingEddy},
};

const TCHAR* GuideTips[] = {
    TEXT("Find the downstream V. Leave room for a recovery eddy."),
    TEXT("Call the high side early; a late call is a swim."),
    TEXT("Scout what you cannot see. The river does not wait."),
    TEXT("Angle into the current, not against it."),
};

bool IsStandaloneRun(const FRaftSimCareerScenarioDefinition& Scenario)
{
    return Scenario.bTraining || Scenario.bFullDescent || Scenario.SectionIndex >= 10;
}

TArray<uint8> BuildMenuConfirmTone()
{
    constexpr int32 UiSampleRate = 48000;
    constexpr float DurationSeconds = 0.11f;
    const int32 SampleCount = FMath::RoundToInt(UiSampleRate * DurationSeconds);
    TArray<int16> Samples;
    Samples.SetNumUninitialized(SampleCount);
    for (int32 Index = 0; Index < SampleCount; ++Index)
    {
        const float T = static_cast<float>(Index) / UiSampleRate;
        const float Envelope = FMath::Sin(PI * FMath::Clamp(T / DurationSeconds, 0.0f, 1.0f));
        const float Signal = (FMath::Sin(2.0f * PI * 659.25f * T) * 0.55f +
            FMath::Sin(2.0f * PI * 987.77f * T) * 0.25f) * Envelope;
        Samples[Index] = static_cast<int16>(Signal * 32767.0f);
    }
    TArray<uint8> Bytes;
    Bytes.SetNumUninitialized(Samples.Num() * sizeof(int16));
    FMemory::Memcpy(Bytes.GetData(), Samples.GetData(), Bytes.Num());
    return Bytes;
}

template <typename TSlot>
TSlot* Fill(TSlot* Slot)
{
    Slot->SetHorizontalAlignment(HAlign_Fill);
    Slot->SetVerticalAlignment(VAlign_Fill);
    return Slot;
}

UCanvasPanelSlot* Place(UCanvasPanel* Canvas, UWidget* Widget, const FAnchors& Anchors, int32 Z = 0)
{
    UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Widget);
    Slot->SetAnchors(Anchors);
    Slot->SetOffsets(FMargin(0));
    Slot->SetZOrder(Z);
    return Slot;
}
}

void URaftSimMenuRunButton::HandleClicked()
{
    if (URaftSimMainMenuWidget* Menu = Owner.Get())
    {
        Menu->StartScenario(ScenarioId, Mode);
    }
}

UWidget* URaftSimMainMenuWidget::GetDefaultFocusWidget() const
{
    if (IsIntroVisible()) return IntroButton;
    if (ActiveScreen == ERaftSimMenuScreen::Career) return FirstCareerButton;
    if (ActiveScreen == ERaftSimMenuScreen::Settings) return FirstSettingsButton;
    return FirstRunButton != nullptr ? FirstRunButton.Get() : StartButton.Get();
}

URaftSimMainMenuWidget* URaftSimMainMenuWidget::FindInWorld(UWorld* World)
{
    if (World == nullptr)
    {
        return nullptr;
    }
    TArray<UUserWidget*> Widgets;
    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(
        World, Widgets, URaftSimMainMenuWidget::StaticClass(), false);
    for (UUserWidget* Widget : Widgets)
    {
        if (URaftSimMainMenuWidget* Menu = Cast<URaftSimMainMenuWidget>(Widget))
        {
            return Menu;
        }
    }
    return nullptr;
}

TSharedRef<SWidget> URaftSimMainMenuWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

UTextBlock* URaftSimMainMenuWidget::MakeText(const FText& Text, const FSlateFontInfo& Font,
    FLinearColor Color, bool bShadow)
{
    UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Block->SetText(Text);
    Style(Block, Font, Color, bShadow);
    return Block;
}

void URaftSimMainMenuWidget::BuildWidgetTree()
{
    if (WidgetTree == nullptr || WidgetTree->RootWidget != nullptr)
    {
        return;
    }
    if (ScenarioCatalog.IsEmpty())
    {
        ScenarioCatalog = URaftSimProgressionLibrary::GetScenarioCatalog();
    }
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;

    // Living painted valley behind everything, shaded where the text sits.
    URaftSimRiverBackdrop* Backdrop = WidgetTree->ConstructWidget<URaftSimRiverBackdrop>();
    Backdrop->SetVisibility(ESlateVisibility::HitTestInvisible);
    Backdrop->SetShade(0.62f, 0.34f, 0.16f);
    PaintedArt.Add(Backdrop);
    Place(Canvas, Backdrop, FAnchors(0, 0, 1, 1));

    // --- Brand.
    HeroColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    Place(Canvas, HeroColumn, FAnchors(0.045f, 0.055f, 0.36f, 0.36f));
    HeroColumn->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "ExpeditionLabel", "WHITEWATER GUIDE SIMULATOR"), Label(14), Gold()));
    UTextBlock* Brand = MakeText(NSLOCTEXT("RaftSim", "Brand", "RAFT SIM"), Display(70), Paper(), true);
    HeroColumn->AddChildToVerticalBox(Brand)->SetPadding(FMargin(0, -6, 0, -10));
    HeroColumn->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "Tagline", "Read the water. Find your line."), Strong(20), Paper(), true));

    // --- Navigation.
    NavColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    Place(Canvas, NavColumn, FAnchors(0.045f, 0.38f, 0.275f, 0.82f));
    MakeNavButton(NavColumn, NSLOCTEXT("RaftSim", "NavRivers", "RIVERS"),
        NSLOCTEXT("RaftSim", "NavRiversSub", "Choose a run and set out"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleBack));
    MakeNavButton(NavColumn, NSLOCTEXT("RaftSim", "OpenCareer", "EXPEDITION"),
        NSLOCTEXT("RaftSim", "NavCareerSub", "Guided descent career"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleOpenCareer));
    MakeNavButton(NavColumn, NSLOCTEXT("RaftSim", "OpenSettings", "SETTINGS"),
        NSLOCTEXT("RaftSim", "NavSettingsSub", "Comfort, accessibility, controls"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleOpenSettings));
    MakeNavButton(NavColumn, NSLOCTEXT("RaftSim", "Quit", "QUIT"),
        NSLOCTEXT("RaftSim", "NavQuitSub", "Back to dry land"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleQuit));

    ProfileChip = WidgetTree->ConstructWidget<UBorder>();
    ProfileChip->SetBrush(Rounded(FLinearColor(0.0f, 0.0f, 0.0f, 0.45f), 8.0f, FLinearColor(1, 1, 1, 0.08f), 1.0f));
    ProfileChip->SetPadding(FMargin(14, 9));
    ProfileText = MakeText(FText::GetEmpty(), Label(13), Gold());
    ProfileChip->SetContent(ProfileText);
    Place(Canvas, ProfileChip, FAnchors(0.045f, 0.835f, 0.275f, 0.835f))->SetAutoSize(true);

    // --- Content: one card for the active screen.
    MenuCard = WidgetTree->ConstructWidget<UBorder>();
    MenuCard->SetBrush(None());
    MenuCard->SetPadding(FMargin(0));
    Place(Canvas, MenuCard, FAnchors(0.315f, 0.055f, 0.955f, 0.905f));
    MenuScroll = WidgetTree->ConstructWidget<UScrollBox>();
    MenuScroll->SetScrollbarThickness(FVector2D(4, 4));
    MenuScroll->SetScrollWhenFocusChanges(EScrollWhenFocusChanges::AnimatedScroll);
    MenuScroll->SetNavigationDestination(EDescendantScrollDestination::IntoView);
    MenuCard->SetContent(MenuScroll);
    UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    MenuScroll->AddChild(Column);

    // Main screen: a card per river, then the focused river's details.
    MainPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(MainPanel);
    UHorizontalBox* MainHeader = WidgetTree->ConstructWidget<UHorizontalBox>();
    MainPanel->AddChildToVerticalBox(MainHeader)->SetPadding(FMargin(6, 0, 6, 10));
    MainHeader->AddChildToHorizontalBox(MakeText(
        NSLOCTEXT("RaftSim", "RiversHeading", "CHOOSE YOUR RIVER"), Label(30), Paper(), true))
        ->SetVerticalAlignment(VAlign_Bottom);
    RunHintText = MakeText(
        NSLOCTEXT("RaftSim", "RunHint", "FREE RUN  ·  SET OUT AT YOUR OWN PACE"), Label(12), Muted());
    UHorizontalBoxSlot* HintSlot = MainHeader->AddChildToHorizontalBox(RunHintText);
    HintSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    HintSlot->SetHorizontalAlignment(HAlign_Right);
    HintSlot->SetVerticalAlignment(VAlign_Bottom);
    HintSlot->SetPadding(FMargin(0, 0, 0, 6));
    RiverGrid = WidgetTree->ConstructWidget<UUniformGridPanel>();
    RiverGrid->SetSlotPadding(FMargin(6));
    RiverGrid->SetMinDesiredSlotHeight(196.0f);
    MainPanel->AddChildToVerticalBox(RiverGrid);
    BuildRunButtons(MainPanel);

    UBorder* Details = WidgetTree->ConstructWidget<UBorder>();
    Details->SetBrush(Rounded(FLinearColor(0.0f, 0.0f, 0.0f, 0.55f), 10.0f, FLinearColor(1, 1, 1, 0.08f), 1.0f));
    Details->SetPadding(FMargin(22, 16));
    MainPanel->AddChildToVerticalBox(Details)->SetPadding(FMargin(6, 12, 6, 0));
    UHorizontalBox* DetailRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    Details->SetContent(DetailRow);
    UVerticalBox* DetailText = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailRow->AddChildToHorizontalBox(DetailText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UHorizontalBox* TitleRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    DetailText->AddChildToVerticalBox(TitleRow);
    DetailTitle = MakeText(FText::GetEmpty(), Display(30), Paper());
    TitleRow->AddChildToHorizontalBox(DetailTitle)->SetVerticalAlignment(VAlign_Center);
    UBorder* GradeChip = WidgetTree->ConstructWidget<UBorder>();
    GradeChip->SetBrush(Rounded(Gold(), 4.0f));
    GradeChip->SetPadding(FMargin(8, 2));
    DetailGrade = MakeText(FText::GetEmpty(), Label(13), Ink());
    GradeChip->SetContent(DetailGrade);
    UHorizontalBoxSlot* ChipSlot = TitleRow->AddChildToHorizontalBox(GradeChip);
    ChipSlot->SetVerticalAlignment(VAlign_Center);
    ChipSlot->SetPadding(FMargin(14, 0, 0, 0));
    DetailPlace = MakeText(FText::GetEmpty(), Label(13), River());
    DetailText->AddChildToVerticalBox(DetailPlace)->SetPadding(FMargin(0, 2, 0, 4));
    DetailHook = MakeText(FText::GetEmpty(), Body(16), Paper());
    DetailHook->SetAutoWrapText(true);
    DetailText->AddChildToVerticalBox(DetailHook);
    UVerticalBox* LaunchHint = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBoxSlot* LaunchSlot = DetailRow->AddChildToHorizontalBox(LaunchHint);
    LaunchSlot->SetVerticalAlignment(VAlign_Center);
    LaunchSlot->SetPadding(FMargin(18, 0, 0, 0));
    UTextBlock* LaunchKey = MakeText(NSLOCTEXT("RaftSim", "LaunchKey", "ENTER  /  A"), Label(13), Muted());
    LaunchKey->SetJustification(ETextJustify::Right);
    LaunchHint->AddChildToVerticalBox(LaunchKey);
    UTextBlock* LaunchVerb = MakeText(NSLOCTEXT("RaftSim", "LaunchVerb", "SET OUT"), Label(24), Gold());
    LaunchVerb->SetJustification(ETextJustify::Right);
    LaunchHint->AddChildToVerticalBox(LaunchVerb);

    // --- Expedition (career) screen.
    CareerPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(CareerPanel);
    CareerPanel->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "CareerHeading", "EXPEDITION"), Label(30), Paper(), true))
        ->SetPadding(FMargin(6, 0, 6, 0));
    CareerPanel->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "CareerSub", "A guided descent career: earn your licence one section at a time."),
        Body(15), Muted()))->SetPadding(FMargin(6, 0, 6, 12));
    UHorizontalBox* ModeRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    CareerPanel->AddChildToVerticalBox(ModeRow)->SetPadding(FMargin(6, 0, 6, 10));
    ModeText = MakeText(FText::GetEmpty(), Label(16), Paper());
    FirstCareerButton = MakeStyledButton(ModeText, RowLook(), this,
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMode), ModeText, Paper(), Gold());
    ModeRow->AddChildToHorizontalBox(FirstCareerButton);

    UBorder* RunFrame = WidgetTree->ConstructWidget<UBorder>();
    RunFrame->SetBrush(Rounded(FLinearColor(0, 0, 0, 0.6f), 10.0f, FLinearColor(1, 1, 1, 0.10f), 1.0f));
    RunFrame->SetPadding(FMargin(3));
    CareerPanel->AddChildToVerticalBox(RunFrame)->SetPadding(FMargin(6, 0, 6, 0));
    UOverlay* RunOverlay = WidgetTree->ConstructWidget<UOverlay>();
    RunFrame->SetContent(RunOverlay);
    USizeBox* ArtSize = WidgetTree->ConstructWidget<USizeBox>();
    ArtSize->SetHeightOverride(250.0f);
    CareerArt = WidgetTree->ConstructWidget<URaftSimRiverBackdrop>();
    CareerArt->SetShade(0.0f, 0.70f, 0.0f);
    CareerArt->SetVisibility(ESlateVisibility::HitTestInvisible);
    PaintedArt.Add(CareerArt);
    ArtSize->AddChild(CareerArt);
    Fill(RunOverlay->AddChildToOverlay(ArtSize));
    UVerticalBox* RunWords = WidgetTree->ConstructWidget<UVerticalBox>();
    UOverlaySlot* WordsSlot = RunOverlay->AddChildToOverlay(RunWords);
    WordsSlot->SetVerticalAlignment(VAlign_Bottom);
    WordsSlot->SetHorizontalAlignment(HAlign_Fill);
    WordsSlot->SetPadding(FMargin(20, 0, 20, 16));
    CareerStatus = MakeText(FText::GetEmpty(), Label(13), Gold());
    RunWords->AddChildToVerticalBox(CareerStatus);
    ScenarioText = MakeText(FText::GetEmpty(), Display(30), Paper(), true);
    RunWords->AddChildToVerticalBox(ScenarioText);
    BriefingText = MakeText(FText::GetEmpty(), Body(16), Paper(), true);
    BriefingText->SetAutoWrapText(true);
    RunWords->AddChildToVerticalBox(BriefingText);

    UHorizontalBox* CareerActions = WidgetTree->ConstructWidget<UHorizontalBox>();
    CareerPanel->AddChildToVerticalBox(CareerActions)->SetPadding(FMargin(6, 12, 6, 0));
    MakeActionButton(CareerActions, NSLOCTEXT("RaftSim", "PreviousScenario", "‹  PREVIOUS"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandlePreviousScenario), false);
    MakeActionButton(CareerActions, NSLOCTEXT("RaftSim", "NextScenario", "NEXT  ›"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleNextScenario), false);
    UHorizontalBoxSlot* GapSlot = CareerActions->AddChildToHorizontalBox(WidgetTree->ConstructWidget<USpacer>());
    GapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    StartButton = MakeActionButton(CareerActions, NSLOCTEXT("RaftSim", "StartSelected", "SET OUT"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleStart), true);
    MakeActionButton(CareerActions, NSLOCTEXT("RaftSim", "BackFromCareer", "BACK"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleBack), false);

    // --- Settings screen: each row shows its live value.
    SettingsPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(SettingsPanel);
    SettingsPanel->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "SettingsHeading", "SETTINGS"), Label(30), Paper(), true))
        ->SetPadding(FMargin(6, 0, 6, 10));
    UVerticalBox* Rows = WidgetTree->ConstructWidget<UVerticalBox>();
    SettingsPanel->AddChildToVerticalBox(Rows)->SetPadding(FMargin(6, 0, 6, 0));
    FirstSettingsButton = MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "Subtitles", "Subtitles & captions"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleSubtitles));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "UiScale", "Interface & text size"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleUiScale));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "ColorCues", "Colour-safe cues"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleColorCues));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "MotionComfort", "Motion comfort"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMotion));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "InteractionStyle", "Crew command input"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleInteraction));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "AssistLevel", "Difficulty & assists"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleAssist));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "GhostRoute", "Route ghost"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleGhostRoute));
    MakeSettingRow(Rows, NSLOCTEXT("RaftSim", "RebindPause", "Pause key"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRebindPause));
    UHorizontalBox* SettingActions = WidgetTree->ConstructWidget<UHorizontalBox>();
    SettingsPanel->AddChildToVerticalBox(SettingActions)->SetPadding(FMargin(6, 12, 6, 0));
    MakeActionButton(SettingActions, NSLOCTEXT("RaftSim", "Defaults", "RESTORE DEFAULTS"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRestoreDefaults), false);
    MakeActionButton(SettingActions, NSLOCTEXT("RaftSim", "Credits", "CREDITS"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCredits), false);
    MakeActionButton(SettingActions, NSLOCTEXT("RaftSim", "Legal", "LEGAL"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleLegal), false);
    UHorizontalBoxSlot* SettingGap = SettingActions->AddChildToHorizontalBox(WidgetTree->ConstructWidget<USpacer>());
    SettingGap->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    MakeActionButton(SettingActions, NSLOCTEXT("RaftSim", "BackFromSettings", "BACK"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleBack), true);
    SettingsSummaryText = MakeText(NSLOCTEXT("RaftSim", "SettingsAutosave",
        "Changes save automatically to your guide profile."), Body(13), Muted());
    SettingsSummaryText->SetAutoWrapText(true);
    SettingsPanel->AddChildToVerticalBox(SettingsSummaryText)->SetPadding(FMargin(8, 12, 6, 0));

    // Shared notice line under every screen (notices, credits, legal).
    InformationText = MakeText(FText::GetEmpty(), Body(15), Gold());
    InformationText->SetAutoWrapText(true);
    Column->AddChildToVerticalBox(InformationText)->SetPadding(FMargin(8, 12, 6, 0));

    // --- Controller / keyboard prompts.
    UHorizontalBox* Prompts = WidgetTree->ConstructWidget<UHorizontalBox>();
    Place(Canvas, Prompts, FAnchors(0.045f, 0.935f, 0.955f, 0.935f))->SetAutoSize(true);
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "PromptMoveKey", "ARROWS / D-PAD"),
        NSLOCTEXT("RaftSim", "PromptMove", "NAVIGATE"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "PromptSelectKey", "ENTER / A"),
        NSLOCTEXT("RaftSim", "PromptSelect", "SELECT"));
    AddPrompt(Prompts, NSLOCTEXT("RaftSim", "PromptBackKey", "ESC / B"),
        NSLOCTEXT("RaftSim", "PromptBack", "BACK"));

    // --- Title sequence on first entry to the front end in this process. The
    // full-screen button makes skipping equally accessible to pointer and pad.
    IntroCanvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    Place(Canvas, IntroCanvas, FAnchors(0, 0, 1, 1), 10);
    URaftSimRiverBackdrop* IntroArt = WidgetTree->ConstructWidget<URaftSimRiverBackdrop>();
    IntroArt->SetShade(0.0f, 0.55f, 0.35f);
    IntroArt->SetVisibility(ESlateVisibility::HitTestInvisible);
    PaintedArt.Add(IntroArt);
    Place(IntroCanvas, IntroArt, FAnchors(0, 0, 1, 1));
    IntroButton = WidgetTree->ConstructWidget<UButton>();
    IntroButton->SetStyle(MakeStyle(None(), None(), None(), FMargin(0)));
    IntroButton->OnClicked.AddDynamic(this, &URaftSimMainMenuWidget::DismissIntro);
    Place(IntroCanvas, IntroButton, FAnchors(0, 0, 1, 1));
    UVerticalBox* IntroWords = WidgetTree->ConstructWidget<UVerticalBox>();
    UButtonSlot* IntroWordsSlot = CastChecked<UButtonSlot>(IntroButton->AddChild(IntroWords));
    IntroWordsSlot->SetHorizontalAlignment(HAlign_Center);
    IntroWordsSlot->SetVerticalAlignment(VAlign_Bottom);
    IntroWordsSlot->SetPadding(FMargin(0, 0, 0, 90));
    auto Centered = [this, IntroWords](UTextBlock* Text, FMargin Gap)
    {
        Text->SetJustification(ETextJustify::Center);
        IntroWords->AddChildToVerticalBox(Text)->SetPadding(Gap);
    };
    Centered(MakeText(NSLOCTEXT("RaftSim", "IntroKicker", "A WHITEWATER EXPEDITION"), Label(18), Gold(), true),
        FMargin(0));
    Centered(MakeText(NSLOCTEXT("RaftSim", "IntroTitle", "RAFT SIM"), Display(128), Paper(), true),
        FMargin(0, -10, 0, -14));
    Centered(MakeText(NSLOCTEXT("RaftSim", "IntroTag", "Six rivers. One crew. Read the water."),
        Strong(24), Paper(), true), FMargin(0, 0, 0, 34));
    IntroPrompt = MakeText(NSLOCTEXT("RaftSim", "IntroSkip", "PRESS ANY KEY"), Label(16), Paper(), true);
    Centered(IntroPrompt, FMargin(0));

    // --- Setting-out screen, shown in the chosen river's colours while the map loads.
    LoadingCanvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    Place(Canvas, LoadingCanvas, FAnchors(0, 0, 1, 1), 20);
    LoadingArt = WidgetTree->ConstructWidget<URaftSimRiverBackdrop>();
    LoadingArt->SetShade(0.55f, 0.50f, 0.0f);
    PaintedArt.Add(LoadingArt);
    Place(LoadingCanvas, LoadingArt, FAnchors(0, 0, 1, 1));
    UVerticalBox* LoadingWords = WidgetTree->ConstructWidget<UVerticalBox>();
    Place(LoadingCanvas, LoadingWords, FAnchors(0.06f, 0.56f, 0.70f, 0.95f));
    LoadingWords->AddChildToVerticalBox(MakeText(
        NSLOCTEXT("RaftSim", "SettingOut", "SETTING OUT"), Label(16), Gold(), true));
    LoadingTitle = MakeText(FText::GetEmpty(), Display(64), Paper(), true);
    LoadingWords->AddChildToVerticalBox(LoadingTitle)->SetPadding(FMargin(0, -4, 0, -6));
    LoadingPlace = MakeText(FText::GetEmpty(), Label(18), River(), true);
    LoadingWords->AddChildToVerticalBox(LoadingPlace)->SetPadding(FMargin(0, 0, 0, 18));
    UTextBlock* Tip = MakeText(FText::FromString(FString(TEXT("GUIDE TIP  ·  ")) +
        GuideTips[FMath::RandRange(0, int32(UE_ARRAY_COUNT(GuideTips)) - 1)]), Body(18), Paper(), true);
    Tip->SetAutoWrapText(true);
    LoadingWords->AddChildToVerticalBox(Tip);
    LoadingProgress = MakeText(NSLOCTEXT("RaftSim", "LoadingRiver", "PREPARING THE RIVER AND YOUR CREW"),
        Label(14), Muted(), true);
    LoadingWords->AddChildToVerticalBox(LoadingProgress)->SetPadding(FMargin(0, 18, 0, 0));
    LoadingCanvas->SetVisibility(ESlateVisibility::Collapsed);

    CareerPanel->SetVisibility(ESlateVisibility::Collapsed);
    SettingsPanel->SetVisibility(ESlateVisibility::Collapsed);
    ActiveScreen = ERaftSimMenuScreen::Main;
}

void URaftSimMainMenuWidget::BuildRunButtons(UVerticalBox* Parent)
{
    RunButtons.Reset();
    FirstRunButton = nullptr;
    TSet<FName> Placed;
    auto AddRunButton = [this, &Placed](
                            const FRaftSimCareerScenarioDefinition& Scenario,
                            const FText& FallbackLabel, ERaftSimGameMode Mode)
    {
        const RaftSimUIArt::FRiverCard Info = RaftSimUIArt::RiverCardFor(Scenario.ScenarioId, FallbackLabel);
        URaftSimMenuRunButton* Proxy = NewObject<URaftSimMenuRunButton>(this);
        Proxy->Owner = this;
        Proxy->ScenarioId = Scenario.ScenarioId;
        Proxy->Mode = Mode;

        // Card: painted river, then grade chip, name and place over a shaded foot.
        UOverlay* Card = WidgetTree->ConstructWidget<UOverlay>();
        URaftSimRiverBackdrop* Art = WidgetTree->ConstructWidget<URaftSimRiverBackdrop>();
        Art->SetLandscape(Info.Art);
        Art->SetShade(0.0f, 0.62f, 0.0f);
        Art->SetVisibility(ESlateVisibility::HitTestInvisible);
        PaintedArt.Add(Art);
        Fill(Card->AddChildToOverlay(Art));
        UVerticalBox* Words = WidgetTree->ConstructWidget<UVerticalBox>();
        UOverlaySlot* WordsSlot = Card->AddChildToOverlay(Words);
        WordsSlot->SetVerticalAlignment(VAlign_Bottom);
        WordsSlot->SetHorizontalAlignment(HAlign_Fill);
        WordsSlot->SetPadding(FMargin(12, 0, 12, 10));
        UTextBlock* Grade = MakeText(Info.Grade, Label(11), Gold(), true);
        Words->AddChildToVerticalBox(Grade);
        UTextBlock* Title = MakeText(Info.Title, Font("Black", 17, 20), Paper(), true);
        Title->SetAutoWrapText(true);
        Words->AddChildToVerticalBox(Title);
        UTextBlock* Where = MakeText(Info.Place, Body(11), FLinearColor(0.78f, 0.84f, 0.80f), true);
        Where->SetAutoWrapText(true);
        Words->AddChildToVerticalBox(Where);

        Proxy->Button = MakeStyledButton(Card, CardLook(), Proxy,
            GET_FUNCTION_NAME_CHECKED(URaftSimMenuRunButton, HandleClicked), Title, Paper(), FLinearColor::White);
        const int32 Index = RunButtons.Num();
        UUniformGridSlot* GridSlot = RiverGrid->AddChildToUniformGrid(Proxy->Button, Index / 4, Index % 4);
        GridSlot->SetHorizontalAlignment(HAlign_Fill);
        GridSlot->SetVerticalAlignment(VAlign_Fill);
        RunButtons.Add(Proxy);
        Placed.Add(Scenario.ScenarioId);
        if (FirstRunButton == nullptr)
        {
            FirstRunButton = Proxy->Button;
        }
    };
    for (const FRunButtonSpec& Spec : RunButtonSpecs)
    {
        const FName ScenarioId(Spec.ScenarioId);
        const FRaftSimCareerScenarioDefinition* Scenario = ScenarioCatalog.FindByPredicate(
            [ScenarioId](const FRaftSimCareerScenarioDefinition& Candidate)
            { return Candidate.ScenarioId == ScenarioId; });
        if (Scenario != nullptr)
        {
            AddRunButton(*Scenario, FText::FromString(Spec.Label), Spec.Mode);
        }
    }
    for (const FRaftSimCareerScenarioDefinition& Scenario : ScenarioCatalog)
    {
        if (!Placed.Contains(Scenario.ScenarioId) && IsStandaloneRun(Scenario))
        {
            AddRunButton(Scenario, Scenario.DisplayName,
                Scenario.bTraining ? ERaftSimGameMode::TrainingEddy : ERaftSimGameMode::FreeRun);
        }
    }
    if (!RunButtons.IsEmpty())
    {
        UpdateRiverDetails(RunButtons[0]);
    }
}

void URaftSimMainMenuWidget::NativeConstruct()
{
    Super::NativeConstruct();

    if (ScenarioCatalog.IsEmpty())
    {
        ScenarioCatalog = URaftSimProgressionLibrary::GetScenarioCatalog();
    }
    if (MenuConfirmTone == nullptr)
    {
        MenuConfirmPcm = BuildMenuConfirmTone();
        MenuConfirmTone = NewObject<USoundWaveProcedural>(this);
        MenuConfirmTone->SetSampleRate(48000);
        MenuConfirmTone->NumChannels = 1;
        MenuConfirmTone->Duration = 0.11f;
        MenuConfirmTone->SoundGroup = SOUNDGROUP_UI;
        MenuConfirmTone->bLooping = false;
    }
    if (MenuAudioComponent == nullptr)
    {
        // One play for the widget's whole life; the source renders silence
        // between clicks. Null in no-audio-device runs (-nullrhi automation).
        MenuAudioComponent = UGameplayStatics::CreateSound2D(
            this, MenuConfirmTone, 0.28f, 1.0f, 0.0f, nullptr,
            /*bPersistAcrossLevelTransition=*/false, /*bAutoDestroy=*/false);
        if (MenuAudioComponent != nullptr)
        {
            MenuAudioComponent->Play();
        }
    }
    RefreshFromSave();
    static bool bIntroPlayed = false;
    if (bIntroPlayed || bReduceMotion) DismissIntro();
    bIntroPlayed = true;
    if (UWidget* Focus = GetDefaultFocusWidget())
    {
        Focus->SetKeyboardFocus();
    }
}

UButton* URaftSimMainMenuWidget::MakeStyledButton(UWidget* Content,
    const RaftSimUITheme::FButtonLook& Look, UObject* Target, FName ClickHandlerName,
    UTextBlock* LabelText, FLinearColor LabelRest, FLinearColor LabelFocus)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    Button->SetStyle(Look.Normal);
    auto* ContentSlot = CastChecked<UButtonSlot>(Button->AddChild(Content));
    ContentSlot->SetHorizontalAlignment(HAlign_Fill);
    ContentSlot->SetVerticalAlignment(VAlign_Fill);
    ContentSlot->SetPadding(FMargin(0));
    StyledButtons.Add(Button);
    StyledButtonLabels.Add(LabelText);
    StyledLooks.Add(Look);
    StyledFocused.Add(255);
    LabelRestColors.Add(LabelRest);
    LabelFocusColors.Add(LabelFocus);
    LabelBaseFonts.Add(LabelText ? LabelText->GetFont() : FSlateFontInfo());

    FScriptDelegate ClickDelegate;
    ClickDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(
        URaftSimMainMenuWidget, HandleMenuAudioCue));
    Button->OnClicked.Add(ClickDelegate);
    ClickDelegate.Unbind();
    ClickDelegate.BindUFunction(Target, ClickHandlerName);
    Button->OnClicked.Add(ClickDelegate);
    return Button;
}

UButton* URaftSimMainMenuWidget::MakeNavButton(
    UVerticalBox* Parent, const FText& Title, const FText& Subtitle, FName Handler)
{
    UVerticalBox* Words = WidgetTree->ConstructWidget<UVerticalBox>();
    UTextBlock* TitleText = MakeText(Title, Label(26), Paper(), true);
    Words->AddChildToVerticalBox(TitleText);
    Words->AddChildToVerticalBox(MakeText(Subtitle, Body(13), Muted()))->SetPadding(FMargin(0, -3, 0, 0));
    UButton* Button = MakeStyledButton(Words, NavLook(), this, Handler, TitleText, Paper(), Gold());
    Parent->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 4));
    NavButtons.Add(Button);
    return Button;
}

UButton* URaftSimMainMenuWidget::MakeSettingRow(UVerticalBox* Parent, const FText& Title, FName Handler)
{
    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    UTextBlock* TitleText = MakeText(Title, Strong(17), Paper());
    UHorizontalBoxSlot* TitleSlot = Row->AddChildToHorizontalBox(TitleText);
    TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    TitleSlot->SetVerticalAlignment(VAlign_Center);
    UBorder* Chip = WidgetTree->ConstructWidget<UBorder>();
    Chip->SetBrush(Rounded(FLinearColor(0.0f, 0.0f, 0.0f, 0.45f), 5.0f, River(), 1.0f));
    Chip->SetPadding(FMargin(12, 3));
    UTextBlock* Value = MakeText(FText::GetEmpty(), Label(14), River());
    Chip->SetContent(Value);
    UHorizontalBoxSlot* ChipSlot = Row->AddChildToHorizontalBox(Chip);
    ChipSlot->SetVerticalAlignment(VAlign_Center);
    SettingValues.Add(Value);
    UButton* Button = MakeStyledButton(Row, RowLook(), this, Handler, TitleText, Paper(), Gold());
    Parent->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 3));
    return Button;
}

UButton* URaftSimMainMenuWidget::MakeActionButton(
    UPanelWidget* Parent, const FText& LabelValue, FName Handler, bool bPrimary)
{
    UTextBlock* Text = MakeText(LabelValue, Label(16), bPrimary ? Ink() : Paper());
    Text->SetJustification(ETextJustify::Center);
    UButton* Button = MakeStyledButton(Text, bPrimary ? PrimaryLook() : RowLook(), this, Handler, Text,
        bPrimary ? Ink() : Paper(), bPrimary ? Ink() : Gold());
    UPanelSlot* PanelSlot = Parent->AddChild(Button);
    if (UHorizontalBoxSlot* Row = Cast<UHorizontalBoxSlot>(PanelSlot))
    {
        Row->SetPadding(FMargin(0, 0, 8, 0));
        Row->SetVerticalAlignment(VAlign_Center);
    }
    return Button;
}

void URaftSimMainMenuWidget::AddPrompt(UHorizontalBox* Bar, const FText& Key, const FText& Action)
{
    UBorder* KeyChip = WidgetTree->ConstructWidget<UBorder>();
    KeyChip->SetBrush(Rounded(FLinearColor(0, 0, 0, 0.5f), 4.0f, FLinearColor(1, 1, 1, 0.35f), 1.0f));
    KeyChip->SetPadding(FMargin(7, 1));
    KeyChip->SetContent(MakeText(Key, Label(11), Paper()));
    UHorizontalBoxSlot* KeySlot = Bar->AddChildToHorizontalBox(KeyChip);
    KeySlot->SetVerticalAlignment(VAlign_Center);
    UHorizontalBoxSlot* ActionSlot = Bar->AddChildToHorizontalBox(MakeText(Action, Label(12), Muted()));
    ActionSlot->SetVerticalAlignment(VAlign_Center);
    ActionSlot->SetPadding(FMargin(8, 0, 26, 0));
}

UButton* URaftSimMainMenuWidget::MakeMenuButton(
    UVerticalBox* Parent, const FText& LabelValue, FName ClickHandlerName)
{
    return MakeButtonWithTarget(Parent, LabelValue, this, ClickHandlerName);
}

UButton* URaftSimMainMenuWidget::MakeButtonWithTarget(
    UVerticalBox* Parent, const FText& LabelValue, UObject* Target, FName ClickHandlerName)
{
    UTextBlock* Text = MakeText(LabelValue, Strong(17), Paper());
    UButton* Button = MakeStyledButton(Text, RowLook(), Target, ClickHandlerName, Text, Paper(), Gold());
    Parent->AddChildToVerticalBox(Button)->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
    return Button;
}

void URaftSimMainMenuWidget::HandleMenuAudioCue()
{
    if (MenuConfirmTone == nullptr || MenuConfirmPcm.IsEmpty() ||
        MenuAudioComponent == nullptr)
    {
        return;
    }
    if (!MenuAudioComponent->IsPlaying())
    {
        // Restart before queueing: overlap on an empty buffer is harmless,
        // overlap on a filled one is the RemoveAt race this replaced.
        MenuAudioComponent->Play();
    }
    if (MenuConfirmTone->GetAvailableAudioByteCount() < MenuConfirmPcm.Num() / 2)
    {
        MenuConfirmTone->QueueAudio(MenuConfirmPcm.GetData(), MenuConfirmPcm.Num());
    }
}

void URaftSimMainMenuWidget::NativeDestruct()
{
    if (MenuAudioComponent != nullptr)
    {
        MenuAudioComponent->Stop();
        MenuAudioComponent = nullptr;
    }
    Super::NativeDestruct();
}

bool URaftSimMainMenuWidget::IsIntroVisible() const
{
    return IntroCanvas && IntroCanvas->GetVisibility() != ESlateVisibility::Collapsed;
}

void URaftSimMainMenuWidget::DismissIntro()
{
    if (!IsIntroVisible()) return;
    IntroCanvas->SetVisibility(ESlateVisibility::Collapsed);
    if (UWidget* Focus = GetDefaultFocusWidget()) Focus->SetKeyboardFocus();
}

void URaftSimMainMenuWidget::UpdateRiverDetails(const URaftSimMenuRunButton* Proxy)
{
    if (Proxy == nullptr || DetailTitle == nullptr || DetailedRun.Get() == Proxy)
    {
        return;
    }
    DetailedRun = Proxy;
    const FRaftSimCareerScenarioDefinition* Scenario = ScenarioCatalog.FindByPredicate(
        [Proxy](const FRaftSimCareerScenarioDefinition& Candidate)
        { return Candidate.ScenarioId == Proxy->ScenarioId; });
    const RaftSimUIArt::FRiverCard Info = RaftSimUIArt::RiverCardFor(
        Proxy->ScenarioId, Scenario ? Scenario->DisplayName : FText::GetEmpty());
    DetailTitle->SetText(Info.Title);
    DetailGrade->SetText(Info.Grade);
    DetailPlace->SetText(FText::FromString(Info.Place.ToString().ToUpper()));
    DetailHook->SetText(Info.Hook.IsEmpty() && Scenario ? Scenario->Briefing : Info.Hook);
}

void URaftSimMainMenuWidget::ApplyLayout(bool bCompact)
{
    HeroColumn->SetVisibility(bCompact ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible);
    ProfileChip->SetVisibility(bCompact ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible);
    RunHintText->SetVisibility(bCompact ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible);
    CastChecked<UCanvasPanelSlot>(NavColumn->Slot)->SetAnchors(bCompact
        ? FAnchors(0.035f, 0.05f, 0.30f, 0.60f) : FAnchors(0.045f, 0.38f, 0.275f, 0.82f));
    CastChecked<UCanvasPanelSlot>(NavColumn->Slot)->SetOffsets(FMargin(0));
    CastChecked<UCanvasPanelSlot>(MenuCard->Slot)->SetAnchors(bCompact
        ? FAnchors(0.32f, 0.04f, 0.965f, 0.905f) : FAnchors(0.315f, 0.055f, 0.955f, 0.905f));
    CastChecked<UCanvasPanelSlot>(MenuCard->Slot)->SetOffsets(FMargin(0));
    const int32 Columns = bCompact ? 2 : 4;
    int32 Index = 0;
    for (URaftSimMenuRunButton* Proxy : RunButtons)
    {
        if (Proxy && Proxy->Button)
        {
            if (UUniformGridSlot* GridSlot = Cast<UUniformGridSlot>(Proxy->Button->Slot))
            {
                GridSlot->SetRow(Index / Columns);
                GridSlot->SetColumn(Index % Columns);
            }
        }
        ++Index;
    }
    if (!PaintedArt.IsEmpty() && PaintedArt[0])
    {
        PaintedArt[0]->SetShade(bCompact ? 0.95f : 0.62f, 0.34f, 0.16f);
    }
}

void URaftSimMainMenuWidget::ShowLoading(const FRaftSimCareerScenarioDefinition& Scenario)
{
    const RaftSimUIArt::FRiverCard Info = RaftSimUIArt::RiverCardFor(Scenario.ScenarioId, Scenario.DisplayName);
    LoadingArt->SetLandscape(Info.Art);
    LoadingTitle->SetText(Info.Title);
    LoadingPlace->SetText(FText::FromString(Info.Place.ToString().ToUpper()));
    LoadingElapsed = 0.0f;
    LoadingCanvas->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void URaftSimMainMenuWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    if (IsIntroVisible())
    {
        IntroElapsed += DeltaSeconds;
        const float Fade = FMath::Clamp((3.6f - IntroElapsed) / 0.7f, 0.0f, 1.0f);
        IntroCanvas->SetRenderOpacity(Fade);
        if (IntroButton && IntroButton->GetContent())
        {
            IntroButton->GetContent()->SetRenderOpacity(FMath::Clamp(IntroElapsed / 0.8f, 0.0f, 1.0f));
            IntroButton->GetContent()->SetRenderTranslation(FVector2D(0,
                18.0f * (1.0f - FMath::Clamp(IntroElapsed / 1.4f, 0.0f, 1.0f))));
        }
        if (IntroPrompt)
        {
            IntroPrompt->SetRenderOpacity(0.45f + 0.55f * (0.5f + 0.5f * FMath::Sin(IntroElapsed * 4.0f)));
        }
        if (IntroElapsed >= 3.6f) DismissIntro();
    }
    if (LoadingCanvas && LoadingCanvas->GetVisibility() != ESlateVisibility::Collapsed && LoadingProgress)
    {
        LoadingElapsed += DeltaSeconds;
        const int32 Dots = int32(LoadingElapsed * 3.0f) % 4;
        LoadingProgress->SetText(FText::FromString(
            FString(TEXT("PREPARING THE RIVER AND YOUR CREW")) + FString::ChrN(Dots, TEXT('.'))));
    }
    const FVector2D Size = Geometry.GetLocalSize();
    if (Size.X > 0 && Size.Y > 0 && !Size.Equals(LastMenuSize))
    {
        ApplyLayout(Size.X < 1000.0 || Size.X / Size.Y < 1.25);
        LastMenuSize = Size;
    }
    // Slate's button style has no focused brush: swap the whole look when
    // keyboard/gamepad focus moves so focus is as visible as pointer hover.
    for (int32 Index = 0; Index < StyledButtons.Num(); ++Index)
    {
        UButton* Button = StyledButtons[Index];
        if (Button == nullptr) continue;
        const bool bFocused = Button->HasKeyboardFocus() || Button->HasUserFocus(GetOwningPlayer());
        const uint8 State = bFocused ? 2 : Button->IsHovered() ? 1 : 0;
        if (State != StyledFocused[Index])
        {
            StyledFocused[Index] = State;
            Button->SetStyle(State == 2 ? StyledLooks[Index].Focused : StyledLooks[Index].Normal);
            if (UTextBlock* LabelText = StyledButtonLabels[Index])
            {
                LabelText->SetColorAndOpacity(State > 0 ? LabelFocusColors[Index] : LabelRestColors[Index]);
            }
        }
    }
    for (URaftSimMenuRunButton* Proxy : RunButtons)
    {
        if (Proxy == nullptr || Proxy->Button == nullptr) continue;
        const bool bActive = Proxy->Button->HasKeyboardFocus() ||
            Proxy->Button->HasUserFocus(GetOwningPlayer()) || Proxy->Button->IsHovered();
        const float Target = bActive && !bReduceMotion ? 1.035f : 1.0f;
        const float Current = Proxy->Button->GetRenderTransform().Scale.X;
        const float Next = FMath::FInterpTo(Current, Target, DeltaSeconds, 14.0f);
        if (!FMath::IsNearlyEqual(Current, Next, 1.0e-4f))
        {
            Proxy->Button->SetRenderScale(FVector2D(Next, Next));
        }
        if (bActive)
        {
            UpdateRiverDetails(Proxy);
        }
    }
}

FReply URaftSimMainMenuWidget::NativeOnPreviewKeyDown(
    const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
    // Escape and the gamepad's B/Circle step back to the main screen from
    // the career and settings screens, matching the on-screen Back buttons.
    const FKey Key = InKeyEvent.GetKey();
    if (IsIntroVisible())
    {
        DismissIntro();
        return FReply::Handled();
    }
    if (ActiveScreen != ERaftSimMenuScreen::Main &&
        (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right))
    {
        ShowScreen(ERaftSimMenuScreen::Main);
        return FReply::Handled();
    }
    return Super::NativeOnPreviewKeyDown(InGeometry, InKeyEvent);
}

void URaftSimMainMenuWidget::ShowScreen(ERaftSimMenuScreen Screen)
{
    DismissIntro();
    ActiveScreen = Screen;
    if (MenuScroll) MenuScroll->ScrollToStart();
    if (MainPanel)
    {
        MainPanel->SetVisibility(Screen == ERaftSimMenuScreen::Main
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    if (CareerPanel)
    {
        CareerPanel->SetVisibility(Screen == ERaftSimMenuScreen::Career
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    if (SettingsPanel)
    {
        SettingsPanel->SetVisibility(Screen == ERaftSimMenuScreen::Settings
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    // The nav entry for the open screen keeps a quiet amber marker.
    for (int32 Index = 0; Index < NavButtons.Num(); ++Index)
    {
        const int32 ScreenIndex = Index == 0 ? int32(ERaftSimMenuScreen::Main)
            : Index == 1 ? int32(ERaftSimMenuScreen::Career)
            : Index == 2 ? int32(ERaftSimMenuScreen::Settings) : -1;
        const int32 Styled = StyledButtons.IndexOfByKey(NavButtons[Index]);
        if (Styled != INDEX_NONE && StyledButtonLabels[Styled])
        {
            LabelRestColors[Styled] = ScreenIndex == int32(Screen) ? Gold() : Paper();
            StyledButtonLabels[Styled]->SetColorAndOpacity(LabelRestColors[Styled]);
            StyledFocused[Styled] = 255;
        }
    }
    UButton* Focus = nullptr;
    switch (Screen)
    {
        case ERaftSimMenuScreen::Career: Focus = FirstCareerButton; break;
        case ERaftSimMenuScreen::Settings: Focus = FirstSettingsButton; break;
        default: Focus = FirstRunButton; break;
    }
    if (Focus != nullptr)
    {
        Focus->SetKeyboardFocus();
    }
    if (InformationText && Screen != ERaftSimMenuScreen::Settings && PendingLevelName.IsNone())
    {
        InformationText->SetText(FText::GetEmpty());
    }
}

void URaftSimMainMenuWidget::HandleOpenCareer() { ShowScreen(ERaftSimMenuScreen::Career); }
void URaftSimMainMenuWidget::HandleOpenSettings() { ShowScreen(ERaftSimMenuScreen::Settings); }
void URaftSimMainMenuWidget::HandleBack() { ShowScreen(ERaftSimMenuScreen::Main); }

FName URaftSimMainMenuWidget::GetSelectedScenarioId() const
{
    return ScenarioCatalog.IsValidIndex(SelectedScenarioIndex)
        ? ScenarioCatalog[SelectedScenarioIndex].ScenarioId
        : NAME_None;
}

bool URaftSimMainMenuWidget::IsScenarioVisible(int32 Index) const
{
    if (!ScenarioCatalog.IsValidIndex(Index))
    {
        return false;
    }
    const FRaftSimCareerScenarioDefinition& Scenario = ScenarioCatalog[Index];
    if (SelectedMode == ERaftSimGameMode::TrainingEddy)
    {
        return Scenario.bTraining;
    }
    if (SelectedMode == ERaftSimGameMode::GuidedDescent)
    {
        return Scenario.SectionIndex >= 1 && Scenario.SectionIndex <= 5;
    }
    return true;
}

void URaftSimMainMenuWidget::SelectNextScenario(int32 Direction)
{
    if (ScenarioCatalog.IsEmpty())
    {
        return;
    }
    for (int32 Step = 0; Step < ScenarioCatalog.Num(); ++Step)
    {
        SelectedScenarioIndex = (SelectedScenarioIndex + Direction + ScenarioCatalog.Num()) %
            ScenarioCatalog.Num();
        if (IsScenarioVisible(SelectedScenarioIndex))
        {
            break;
        }
    }
    RefreshFromSave();
}

void URaftSimMainMenuWidget::SetRunButtonsEnabled(bool bEnabled)
{
    for (URaftSimMenuRunButton* Proxy : RunButtons)
    {
        if (Proxy && Proxy->Button)
        {
            Proxy->Button->SetIsEnabled(bEnabled);
        }
    }
}

void URaftSimMainMenuWidget::RefreshFromSave()
{
    URaftSimSaveSubsystem* SaveSubsystem = GetGameInstance()
        ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr;
    URaftSimVerticalSliceSaveGame* Save = SaveSubsystem ? SaveSubsystem->GetSave() : nullptr;
    if (Save != nullptr)
    {
        // Adopt the saved mode and selection once, at first open. Re-running
        // the selection restore on every refresh snapped the run back to the
        // save after each Next/Previous click whenever the saved run was
        // visible - in Free Run (everything visible) the buttons went dead
        // (2026-08-07 playtest).
        if (!bModeInitialized)
        {
            SelectedMode = Save->ActiveGameMode;
            bModeInitialized = true;
            for (int32 Index = 0; Index < ScenarioCatalog.Num(); ++Index)
            {
                if (ScenarioCatalog[Index].ScenarioId == Save->Selection.ScenarioId &&
                    IsScenarioVisible(Index))
                {
                    SelectedScenarioIndex = Index;
                    break;
                }
            }
        }
    }
    if (!IsScenarioVisible(SelectedScenarioIndex))
    {
        SelectNextScenario(1);
        return;
    }
    const FRaftSimCareerScenarioDefinition& Scenario = ScenarioCatalog[SelectedScenarioIndex];
    const bool bUnlocked = SaveSubsystem &&
        SaveSubsystem->IsScenarioUnlocked(Scenario.ScenarioId, SelectedMode);
    ModeText->SetText(FText::Format(NSLOCTEXT("RaftSim", "ModeLine", "MODE  ·  {0}  ›"),
        FText::FromString(ModeName(SelectedMode).ToString().ToUpper())));
    ScenarioText->SetText(Scenario.DisplayName);
    CareerStatus->SetText(bUnlocked ? NSLOCTEXT("RaftSim", "Unlocked", "READY TO RUN")
        : FText::Format(NSLOCTEXT("RaftSim", "Unavailable", "LOCKED  ·  REQUIRES {0}"),
            FText::FromString(URaftSimProgressionLibrary::LicenseDisplayName(Scenario.RequiredLicense)
                .ToString().ToUpper())));
    CareerStatus->SetColorAndOpacity(bUnlocked ? Gold() : Danger());
    BriefingText->SetText(Scenario.Briefing);
    if (CareerArt)
    {
        CareerArt->SetLandscape(RaftSimUIArt::RiverCardFor(Scenario.ScenarioId, Scenario.DisplayName).Art);
    }
    if (StartButton)
    {
        StartButton->SetIsEnabled(bUnlocked && PendingLevelName.IsNone());
    }
    for (URaftSimMenuRunButton* Proxy : RunButtons)
    {
        if (Proxy && Proxy->Button)
        {
            Proxy->Button->SetIsEnabled(PendingLevelName.IsNone() && SaveSubsystem &&
                SaveSubsystem->IsScenarioUnlocked(Proxy->ScenarioId, Proxy->Mode));
        }
    }
    if (Save)
    {
        ProfileText->SetText(FText::Format(
            NSLOCTEXT("RaftSim", "ProfileLine", "{0}   ·   XP {1}   ·   {2} RUNS"),
            FText::FromString(URaftSimProgressionLibrary::LicenseDisplayName(Save->LicenseTier)
                .ToString().ToUpper()),
            FText::AsNumber(Save->CareerXp), FText::AsNumber(Save->CareerStats.CompletedRuns)));
        const FRaftSimVerticalSliceUserSettings& S = Save->Settings;
        bReduceMotion = S.MotionIntensity <= 0.01f;
        for (URaftSimRiverBackdrop* Art : PaintedArt)
        {
            if (Art) Art->SetAnimated(!bReduceMotion);
        }
        MenuScroll->SetScrollWhenFocusChanges(bReduceMotion
            ? EScrollWhenFocusChanges::InstantScroll : EScrollWhenFocusChanges::AnimatedScroll);
        MenuTextScale = FMath::Clamp(S.TextScale, 0.85f, 1.35f);
        for (int32 Index = 0; Index < StyledButtonLabels.Num(); ++Index)
        {
            if (UTextBlock* LabelText = StyledButtonLabels[Index])
            {
                FSlateFontInfo Scaled = LabelBaseFonts[Index];
                Scaled.Size = FMath::RoundToInt(Scaled.Size * MenuTextScale);
                LabelText->SetFont(Scaled);
            }
        }
        const FName* PauseKey = Save->InputBindings.Find(TEXT("Pause"));
        const FString Values[] = {
            S.bSubtitlesEnabled ? TEXT("ON") : TEXT("OFF"),
            FString::Printf(TEXT("%.0f%%"), S.UiScale * 100.0f),
            UEnum::GetDisplayValueAsText(S.ColorCueMode).ToString().ToUpper(),
            S.MotionIntensity <= 0.01f ? FString(TEXT("STILL"))
                : FString::Printf(TEXT("%.0f%%"), S.MotionIntensity * 100.0f),
            S.CommandWheelStyle == ERaftSimInteractionStyle::Hold ? TEXT("HOLD") : TEXT("TOGGLE"),
            UEnum::GetDisplayValueAsText(S.AssistLevel).ToString().ToUpper(),
            S.bGhostEnabled ? TEXT("ON") : TEXT("OFF"),
            (PauseKey ? PauseKey->ToString() : FString(TEXT("Escape"))).ToUpper(),
        };
        for (int32 Index = 0; Index < SettingValues.Num() && Index < int32(UE_ARRAY_COUNT(Values)); ++Index)
        {
            SettingValues[Index]->SetText(FText::FromString(Values[Index]));
        }
    }
}

void URaftSimMainMenuWidget::StartScenario(FName ScenarioId, ERaftSimGameMode Mode)
{
    DismissIntro();
    if (!PendingLevelName.IsNone())
    {
        return; // a travel is already queued
    }
    const int32 Index = ScenarioCatalog.IndexOfByPredicate(
        [ScenarioId](const FRaftSimCareerScenarioDefinition& Candidate)
        { return Candidate.ScenarioId == ScenarioId; });
    if (Index == INDEX_NONE || GetGameInstance() == nullptr)
    {
        return;
    }
    URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    const FRaftSimCareerScenarioDefinition& Scenario = ScenarioCatalog[Index];
    if (Save == nullptr || !Save->BeginSession(Mode, ScenarioId))
    {
        InformationText->SetText(FText::Format(
            NSLOCTEXT("RaftSim", "RunUnavailable", "{0} is not available in {1}."),
            Scenario.DisplayName, ModeName(Mode)));
        return;
    }
    SelectedMode = Mode;
    SelectedScenarioIndex = Index;
    PendingLevelName = Scenario.LevelName;
    MainPanel->SetVisibility(ESlateVisibility::Collapsed);
    CareerPanel->SetVisibility(ESlateVisibility::Collapsed);
    SettingsPanel->SetVisibility(ESlateVisibility::Collapsed);
    SetRunButtonsEnabled(false);
    if (StartButton)
    {
        StartButton->SetIsEnabled(false);
    }
    InformationText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "LoadingRun", "SETTING OUT  ·  {0}"), Scenario.DisplayName));
    ShowLoading(Scenario);
    // A few frames of the setting-out card render before the blocking map load.
    GetWorld()->GetTimerManager().SetTimer(
        PendingTravelTimer, this, &URaftSimMainMenuWidget::OpenPendingLevel, 0.30f, false);
}

void URaftSimMainMenuWidget::HandleStart()
{
    if (ScenarioCatalog.IsValidIndex(SelectedScenarioIndex))
    {
        StartScenario(ScenarioCatalog[SelectedScenarioIndex].ScenarioId, SelectedMode);
    }
}

void URaftSimMainMenuWidget::OpenPendingLevel()
{
    if (!PendingLevelName.IsNone())
    {
        UGameplayStatics::OpenLevel(this, PendingLevelName);
    }
}

void URaftSimMainMenuWidget::HandleCycleMode()
{
    SelectedMode = static_cast<ERaftSimGameMode>((static_cast<int32>(SelectedMode) + 1) % 3);
    SelectNextScenario(1);
}

void URaftSimMainMenuWidget::HandlePreviousScenario() { SelectNextScenario(-1); }
void URaftSimMainMenuWidget::HandleNextScenario() { SelectNextScenario(1); }

void URaftSimMainMenuWidget::HandleToggleSubtitles()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->GetSave()->Settings.bSubtitlesEnabled = !Save->GetSave()->Settings.bSubtitlesEnabled;
        Save->GetSave()->Settings.bCaptionsEnabled = Save->GetSave()->Settings.bSubtitlesEnabled;
        Save->SaveCurrent();
        RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleCycleUiScale()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        FRaftSimVerticalSliceUserSettings& S = Save->GetSave()->Settings;
        S.UiScale = S.UiScale >= 1.45f ? 0.75f : S.UiScale + 0.25f;
        S.TextScale = S.UiScale >= 1.25f ? 1.35f : S.UiScale;
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleCycleColorCues()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        auto& S = Save->GetSave()->Settings;
        S.ColorCueMode = static_cast<ERaftSimColorCueMode>((static_cast<int32>(S.ColorCueMode) + 1) % 5);
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleCycleMotion()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        auto& S = Save->GetSave()->Settings;
        S.MotionIntensity = S.MotionIntensity > 0.1f ? FMath::Max(0.0f, S.MotionIntensity - 0.25f) : 1.0f;
        S.CameraShakeScale = S.MotionIntensity;
        S.bCameraShakeEnabled = S.MotionIntensity > 0.0f;
        S.bVignetteEnabled = S.MotionIntensity > 0.5f;
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleCycleInteraction()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        auto& S = Save->GetSave()->Settings;
        S.CommandWheelStyle = S.CommandWheelStyle == ERaftSimInteractionStyle::Hold
            ? ERaftSimInteractionStyle::Toggle : ERaftSimInteractionStyle::Hold;
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleCycleAssist()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        auto& S = Save->GetSave()->Settings;
        S.AssistLevel = static_cast<ERaftSimAssistLevel>((static_cast<int32>(S.AssistLevel) + 1) % 3);
        S.bRouteAssistEnabled = S.AssistLevel != ERaftSimAssistLevel::Authentic;
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleToggleGhostRoute()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        auto& S = Save->GetSave()->Settings;
        S.bGhostEnabled = !S.bGhostEnabled;
        S.bRouteAssistEnabled = S.bGhostEnabled;
        Save->SaveCurrent(); RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleRebindPause()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        const FName* Existing = Save->GetSave()->InputBindings.Find(TEXT("Pause"));
        Save->RebindAction(TEXT("Pause"), Existing && *Existing == TEXT("Escape") ? TEXT("Pause") : TEXT("Escape"));
        InformationText->SetText(NSLOCTEXT("RaftSim", "RebindApplied", "Pause binding saved. Gamepad Menu remains available."));
        RefreshFromSave();
    }
}

void URaftSimMainMenuWidget::HandleRestoreDefaults()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->RestoreDefaultSettings(); RefreshFromSave();
        InformationText->SetText(NSLOCTEXT("RaftSim", "DefaultsRestored", "Settings restored to defaults."));
    }
}

void URaftSimMainMenuWidget::HandleCredits()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->GetSave()->bCreditsViewed = true; Save->SaveCurrent();
    }
    InformationText->SetText(NSLOCTEXT("RaftSim", "CreditsBody",
        "RaftSim contributors; Unreal Engine; USGS 3DEP/NHD and USDA NAIP public data; CC0 Poly Haven assets; first-party procedural art, simulation, and audio. Full notices ship in NOTICE.md, LICENSE-CONTENT.md, and the source manifests."));
}

void URaftSimMainMenuWidget::HandleLegal()
{
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->GetSave()->bLegalViewed = true; Save->SaveCurrent();
    }
    InformationText->SetText(NSLOCTEXT("RaftSim", "LegalBody",
        "Game and training simulation only. Procedural terrain, inferred bathymetry, hazards, and guide lines are labeled approximations and must never be used for real-world navigation. See NOTICE.md, LICENSE-CONTENT.md, and source manifests for attribution."));
}

void URaftSimMainMenuWidget::HandleQuit()
{
    UKismetSystemLibrary::QuitGame(
        this, GetOwningPlayer(), EQuitPreference::Quit, /*bIgnorePlatformRestrictions=*/false);
}

// ---------------------------------------------------------------------------
// Review hook: RaftSim.MenuScreen <intro|main|career|settings|loading> [capture=<label>]
// Shows a menu screen in the boot level and optionally screenshots it two
// seconds later and exits (one -ExecCmds entry does the whole review).
// ---------------------------------------------------------------------------

static void HandleMenuScreenCommand(const TArray<FString>& Args, UWorld* World)
{
    URaftSimMainMenuWidget* Menu = URaftSimMainMenuWidget::FindInWorld(World);
    if (Menu == nullptr || Args.Num() < 1)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim.MenuScreen <main|career|settings> [capture=<label>]: no main menu in this world"));
        return;
    }
    ERaftSimMenuScreen Screen = ERaftSimMenuScreen::Main;
    if (Args[0].Equals(TEXT("career"), ESearchCase::IgnoreCase))
    {
        Screen = ERaftSimMenuScreen::Career;
    }
    else if (Args[0].Equals(TEXT("settings"), ESearchCase::IgnoreCase))
    {
        Screen = ERaftSimMenuScreen::Settings;
    }
    const bool bCaptureIntro = Args[0].Equals(TEXT("intro"), ESearchCase::IgnoreCase);
    if (!bCaptureIntro) Menu->ShowScreen(Screen);
    UE_LOG(LogTemp, Display, TEXT("RaftSim.MenuScreen: showing %s (%d run buttons)"),
        *Args[0], Menu->GetRunButtonCount());
    for (int32 Index = 1; Index < Args.Num(); ++Index)
    {
        if (Args[Index].StartsWith(TEXT("start="), ESearchCase::IgnoreCase))
        {
            // Review: press a river button by scenario id (Free Run).
            Menu->StartScenario(FName(*Args[Index].RightChop(6)), ERaftSimGameMode::FreeRun);
            continue;
        }
        if (Args[Index].StartsWith(TEXT("capture="), ESearchCase::IgnoreCase))
        {
            const FString Path = FPaths::Combine(
                FPaths::ProjectSavedDir(), TEXT("Screenshots"), Args[Index].RightChop(8) + TEXT(".png"));
            FTimerHandle CaptureHandle;
            World->GetTimerManager().SetTimer(
                CaptureHandle,
                FTimerDelegate::CreateLambda([Path]()
                {
                    // bInShowUI: the whole point is the widget, not the boot level's sky.
                    FScreenshotRequest::RequestScreenshot(Path, /*bInShowUI=*/true, false);
                }),
                bCaptureIntro ? 1.0f : 2.0f, false);
            FTimerHandle ExitHandle;
            World->GetTimerManager().SetTimer(
                ExitHandle,
                FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                4.5f, false);
        }
    }
}

static FAutoConsoleCommandWithWorldAndArgs GMenuScreenCommand(
    TEXT("RaftSim.MenuScreen"),
    TEXT("Show a main-menu screen (main|career|settings) and optionally capture=<label> it, then exit."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleMenuScreenCommand));
