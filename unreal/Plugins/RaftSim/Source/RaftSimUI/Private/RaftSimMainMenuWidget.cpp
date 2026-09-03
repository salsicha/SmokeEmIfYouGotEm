#include "RaftSimMainMenuWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/AudioComponent.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/Paths.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Sound/SoundWaveProcedural.h"
#include "TimerManager.h"
#include "UnrealClient.h"

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

// River-facing labels for the main screen, in menu order. Anything else in
// the catalog that is a reference/challenge run (section 10+) or training is
// appended with its catalog display name, so a new river map shows up
// without touching this list.
const FRunButtonSpec RunButtonSpecs[] = {
    {TEXT("south_fork_full_descent"), TEXT("South Fork American: Chili Bar to Salmon Falls"),
        ERaftSimGameMode::FreeRun},
    {TEXT("troublemaker_challenge"), TEXT("South Fork American: Troublemaker Rapid"),
        ERaftSimGameMode::FreeRun},
    {TEXT("hance_challenge"), TEXT("Colorado, Grand Canyon: Hance"), ERaftSimGameMode::FreeRun},
    {TEXT("upper_huacas_challenge"), TEXT("Pacuare: Upper Huacas"), ERaftSimGameMode::FreeRun},
    {TEXT("terminator_challenge"), TEXT("Futaleufu: Terminator"), ERaftSimGameMode::FreeRun},
    {TEXT("lava_canyon_challenge"), TEXT("Chilko: Lava Canyon"), ERaftSimGameMode::FreeRun},
    {TEXT("zambezi_reference_run"),
        TEXT("Zambezi, Batoka Gorge: Boiling Pot to Mukuni Beach"), ERaftSimGameMode::FreeRun},
    {TEXT("training_eddy_basics"), TEXT("Training Eddy: Guide School (flat-water tank)"),
        ERaftSimGameMode::TrainingEddy},
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

UTextBlock* MakeHeading(UWidgetTree* Tree, UVerticalBox* Parent, const FText& Text, int32 Size)
{
    UTextBlock* Heading = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Heading->SetText(Text);
    FSlateFontInfo Font = Heading->GetFont();
    Font.Size = Size;
    Heading->SetFont(Font);
    UVerticalBoxSlot* HeadingSlot = Parent->AddChildToVerticalBox(Heading);
    HeadingSlot->SetPadding(FMargin(0.0f, 18.0f, 0.0f, 4.0f));
    return Heading;
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

    UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
    UCanvasPanelSlot* ScrollSlot = Canvas->AddChildToCanvas(Scroll);
    ScrollSlot->SetAnchors(FAnchors(0.16f, 0.04f, 0.84f, 0.96f));
    ScrollSlot->SetOffsets(FMargin(0.0f));
    UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Scroll->AddChild(Column);

    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(NSLOCTEXT("RaftSim", "MainMenuTitle", "RaftSim"));
    FSlateFontInfo TitleFont = Title->GetFont();
    TitleFont.Size = 64;
    Title->SetFont(TitleFont);
    Column->AddChildToVerticalBox(Title);

    UTextBlock* Subtitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Subtitle->SetText(
        NSLOCTEXT("RaftSim", "MainMenuSubtitle", "Whitewater Guide Simulator"));
    Column->AddChildToVerticalBox(Subtitle);

    ProfileText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Column->AddChildToVerticalBox(ProfileText);

    // --- Main screen: one button per river run, then Career / Settings / Quit.
    MainPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(MainPanel);
    MakeHeading(WidgetTree, MainPanel,
        NSLOCTEXT("RaftSim", "RiversHeading", "Rivers - pick a run"), 28);
    BuildRunButtons(MainPanel);
    MakeHeading(WidgetTree, MainPanel, FText::GetEmpty(), 10);
    MakeMenuButton(MainPanel, NSLOCTEXT("RaftSim", "OpenCareer", "Guided Descent Career..."),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleOpenCareer));
    MakeMenuButton(MainPanel, NSLOCTEXT("RaftSim", "OpenSettings", "Settings..."),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleOpenSettings));
    MakeMenuButton(
        MainPanel, NSLOCTEXT("RaftSim", "Quit", "Quit"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleQuit));

    // --- Career screen: the guided-descent mode and section selector.
    CareerPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(CareerPanel);
    MakeHeading(WidgetTree, CareerPanel,
        NSLOCTEXT("RaftSim", "CareerHeading", "Guided Descent Career"), 28);
    ModeText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    CareerPanel->AddChildToVerticalBox(ModeText);
    ScenarioText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    CareerPanel->AddChildToVerticalBox(ScenarioText);
    BriefingText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    BriefingText->SetAutoWrapText(true);
    CareerPanel->AddChildToVerticalBox(BriefingText);
    FirstCareerButton = MakeMenuButton(CareerPanel, NSLOCTEXT("RaftSim", "CycleMode", "Change Mode"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMode));
    MakeMenuButton(CareerPanel, NSLOCTEXT("RaftSim", "PreviousScenario", "Previous Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandlePreviousScenario));
    MakeMenuButton(CareerPanel, NSLOCTEXT("RaftSim", "NextScenario", "Next Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleNextScenario));
    StartButton = MakeMenuButton(CareerPanel, NSLOCTEXT("RaftSim", "StartSelected", "Start Selected Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleStart));
    MakeMenuButton(CareerPanel, NSLOCTEXT("RaftSim", "BackFromCareer", "Back"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleBack));

    // --- Settings screen.
    SettingsPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Column->AddChildToVerticalBox(SettingsPanel);
    MakeHeading(WidgetTree, SettingsPanel, NSLOCTEXT("RaftSim", "SettingsHeading", "Settings"), 28);
    FirstSettingsButton = MakeMenuButton(SettingsPanel,
        NSLOCTEXT("RaftSim", "Subtitles", "Toggle Subtitles + Captions"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleSubtitles));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "UiScale", "Cycle UI / Text Size"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleUiScale));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "ColorCues", "Cycle Color-Safe Cues"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleColorCues));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "MotionComfort", "Cycle Motion Comfort"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMotion));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "InteractionStyle", "Hold / Toggle Controls"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleInteraction));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "AssistLevel", "Cycle Difficulty + Assists"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleAssist));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "GhostRoute", "Toggle Ghost / Route Assist"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleGhostRoute));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "RebindPause", "Rebind Pause: Escape / Pause"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRebindPause));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "Defaults", "Restore Settings Defaults"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRestoreDefaults));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "Credits", "Credits"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCredits));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "Legal", "Legal + Data Notice"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleLegal));
    MakeMenuButton(SettingsPanel, NSLOCTEXT("RaftSim", "BackFromSettings", "Back"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleBack));
    SettingsSummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    SettingsSummaryText->SetText(FText::GetEmpty());
    SettingsSummaryText->SetAutoWrapText(true);
    UVerticalBoxSlot* SummarySlot = SettingsPanel->AddChildToVerticalBox(SettingsSummaryText);
    SummarySlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));

    // Shared status line under every screen (loading, notices, credits).
    InformationText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    InformationText->SetAutoWrapText(true);
    UVerticalBoxSlot* InformationSlot = Column->AddChildToVerticalBox(InformationText);
    InformationSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));

    CareerPanel->SetVisibility(ESlateVisibility::Collapsed);
    SettingsPanel->SetVisibility(ESlateVisibility::Collapsed);
    ActiveScreen = ERaftSimMenuScreen::Main;
}

void URaftSimMainMenuWidget::BuildRunButtons(UVerticalBox* Parent)
{
    RunButtons.Reset();
    FirstRunButton = nullptr;
    TSet<FName> Placed;
    auto AddRunButton = [this, Parent, &Placed](
                            const FRaftSimCareerScenarioDefinition& Scenario,
                            const FText& Label, ERaftSimGameMode Mode)
    {
        URaftSimMenuRunButton* Proxy = NewObject<URaftSimMenuRunButton>(this);
        Proxy->Owner = this;
        Proxy->ScenarioId = Scenario.ScenarioId;
        Proxy->Mode = Mode;
        Proxy->Button = MakeButtonWithTarget(Parent, Label, Proxy,
            GET_FUNCTION_NAME_CHECKED(URaftSimMenuRunButton, HandleClicked));
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
    if (UWidget* Focus = GetDefaultFocusWidget())
    {
        Focus->SetKeyboardFocus();
    }
}

UButton* URaftSimMainMenuWidget::MakeMenuButton(
    UVerticalBox* Parent, const FText& Label, FName ClickHandlerName)
{
    return MakeButtonWithTarget(Parent, Label, this, ClickHandlerName);
}

UButton* URaftSimMainMenuWidget::MakeButtonWithTarget(
    UVerticalBox* Parent, const FText& Label, UObject* Target, FName ClickHandlerName)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* ButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    ButtonText->SetText(Label);
    Button->AddChild(ButtonText);

    FScriptDelegate ClickDelegate;
    ClickDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(
        URaftSimMainMenuWidget, HandleMenuAudioCue));
    Button->OnClicked.Add(ClickDelegate);
    ClickDelegate.Unbind();
    ClickDelegate.BindUFunction(Target, ClickHandlerName);
    Button->OnClicked.Add(ClickDelegate);

    UVerticalBoxSlot* ButtonSlot = Parent->AddChildToVerticalBox(Button);
    ButtonSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));
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

FReply URaftSimMainMenuWidget::NativeOnPreviewKeyDown(
    const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
    // Escape and the gamepad's B/Circle step back to the main screen from
    // the career and settings screens, matching the on-screen Back buttons.
    const FKey Key = InKeyEvent.GetKey();
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
    ActiveScreen = Screen;
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
    ModeText->SetText(FText::Format(NSLOCTEXT("RaftSim", "ModeLine", "Mode: {0}"), ModeName(SelectedMode)));
    ScenarioText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "ScenarioLine", "Run: {0}  [{1}]"), Scenario.DisplayName,
        bUnlocked ? NSLOCTEXT("RaftSim", "Unlocked", "ready")
                  : NSLOCTEXT("RaftSim", "Unavailable", "unavailable")));
    BriefingText->SetText(Scenario.Briefing);
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
            NSLOCTEXT("RaftSim", "ProfileLine", "Guide rank: {0}   XP {1}   completed {2}"),
            URaftSimProgressionLibrary::LicenseDisplayName(Save->LicenseTier),
            FText::AsNumber(Save->CareerXp), FText::AsNumber(Save->CareerStats.CompletedRuns)));
        const FRaftSimVerticalSliceUserSettings& S = Save->Settings;
        const FName* PauseKey = Save->InputBindings.Find(TEXT("Pause"));
        SettingsSummaryText->SetText(FText::FromString(FString::Printf(
            TEXT("Subtitles %s | UI %.0f%% | text %.0f%% | colour cues %d | motion %.0f%% | controls %s | assist %d | ghost %s | pause %s"),
            S.bSubtitlesEnabled ? TEXT("on") : TEXT("off"), S.UiScale * 100.0f,
            S.TextScale * 100.0f, static_cast<int32>(S.ColorCueMode),
            S.MotionIntensity * 100.0f,
            S.CommandWheelStyle == ERaftSimInteractionStyle::Hold ? TEXT("hold") : TEXT("toggle"),
            static_cast<int32>(S.AssistLevel), S.bGhostEnabled ? TEXT("on") : TEXT("off"),
            PauseKey ? *PauseKey->ToString() : TEXT("Escape"))));
    }
}

void URaftSimMainMenuWidget::StartScenario(FName ScenarioId, ERaftSimGameMode Mode)
{
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
    SetRunButtonsEnabled(false);
    if (StartButton)
    {
        StartButton->SetIsEnabled(false);
    }
    InformationText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "LoadingRun", "LOADING - {0}\nPreparing live water, crew, weather, and checkpoint..."),
        Scenario.DisplayName));
    GetWorld()->GetTimerManager().SetTimer(
        PendingTravelTimer, this, &URaftSimMainMenuWidget::OpenPendingLevel, 0.18f, false);
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
// Review hook: RaftSim.MenuScreen <main|career|settings> [capture=<label>]
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
    Menu->ShowScreen(Screen);
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
                2.0f, false);
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
