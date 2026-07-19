#include "RaftSimMainMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"

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
}

UWidget* URaftSimMainMenuWidget::GetDefaultFocusWidget() const
{
    return StartButton.Get();
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
    ModeText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Column->AddChildToVerticalBox(ModeText);
    ScenarioText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Column->AddChildToVerticalBox(ScenarioText);
    BriefingText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    BriefingText->SetAutoWrapText(true);
    Column->AddChildToVerticalBox(BriefingText);

    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "CycleMode", "Change Mode"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMode));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "PreviousScenario", "Previous Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandlePreviousScenario));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "NextScenario", "Next Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleNextScenario));
    StartButton = MakeMenuButton(Column, NSLOCTEXT("RaftSim", "StartSelected", "Start Selected Run"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleStart));

    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "Subtitles", "Toggle Subtitles + Captions"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleSubtitles));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "UiScale", "Cycle UI / Text Size"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleUiScale));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "ColorCues", "Cycle Color-Safe Cues"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleColorCues));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "MotionComfort", "Cycle Motion Comfort"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleMotion));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "InteractionStyle", "Hold / Toggle Controls"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleInteraction));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "AssistLevel", "Cycle Difficulty + Assists"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCycleAssist));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "GhostRoute", "Toggle Ghost / Route Assist"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleGhostRoute));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "RebindPause", "Rebind Pause: Escape / Pause"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRebindPause));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "Defaults", "Restore Settings Defaults"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRestoreDefaults));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "Credits", "Credits"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleCredits));
    MakeMenuButton(Column, NSLOCTEXT("RaftSim", "Legal", "Legal + Data Notice"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleLegal));
    MakeMenuButton(
        Column, NSLOCTEXT("RaftSim", "Quit", "Quit"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleQuit));

    SettingsSummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    SettingsSummaryText->SetText(FText::GetEmpty());
    SettingsSummaryText->SetAutoWrapText(true);
    Column->AddChildToVerticalBox(SettingsSummaryText);
    InformationText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    InformationText->SetAutoWrapText(true);
    Column->AddChildToVerticalBox(InformationText);
}

void URaftSimMainMenuWidget::NativeConstruct()
{
    Super::NativeConstruct();

    ScenarioCatalog = URaftSimProgressionLibrary::GetScenarioCatalog();
    RefreshFromSave();
    if (StartButton != nullptr)
    {
        StartButton->SetKeyboardFocus();
    }
}

UButton* URaftSimMainMenuWidget::MakeMenuButton(
    UVerticalBox* Parent, const FText& Label, FName ClickHandlerName)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* ButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    ButtonText->SetText(Label);
    Button->AddChild(ButtonText);

    FScriptDelegate ClickDelegate;
    ClickDelegate.BindUFunction(this, ClickHandlerName);
    Button->OnClicked.Add(ClickDelegate);

    UVerticalBoxSlot* ButtonSlot = Parent->AddChildToVerticalBox(Button);
    ButtonSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));
    return Button;
}

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

void URaftSimMainMenuWidget::RefreshFromSave()
{
    URaftSimSaveSubsystem* SaveSubsystem = GetGameInstance()
        ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr;
    URaftSimVerticalSliceSaveGame* Save = SaveSubsystem ? SaveSubsystem->GetSave() : nullptr;
    if (Save != nullptr)
    {
        if (!bModeInitialized)
        {
            SelectedMode = Save->ActiveGameMode;
            bModeInitialized = true;
        }
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
        bUnlocked ? NSLOCTEXT("RaftSim", "Unlocked", "ready") : NSLOCTEXT("RaftSim", "Locked", "license locked")));
    BriefingText->SetText(Scenario.Briefing);
    if (StartButton)
    {
        StartButton->SetIsEnabled(bUnlocked);
    }
    if (Save)
    {
        ProfileText->SetText(FText::Format(
            NSLOCTEXT("RaftSim", "ProfileLine", "License: {0}   XP {1}   completed {2}"),
            URaftSimProgressionLibrary::LicenseDisplayName(Save->LicenseTier),
            FText::AsNumber(Save->CareerXp), FText::AsNumber(Save->CareerStats.CompletedRuns)));
        const FRaftSimVerticalSliceUserSettings& S = Save->Settings;
        SettingsSummaryText->SetText(FText::FromString(FString::Printf(
            TEXT("Subtitles %s | UI %.0f%% | text %.0f%% | motion %.0f%% | assist %d | ghost %s"),
            S.bSubtitlesEnabled ? TEXT("on") : TEXT("off"), S.UiScale * 100.0f,
            S.TextScale * 100.0f, S.MotionIntensity * 100.0f,
            static_cast<int32>(S.AssistLevel), S.bGhostEnabled ? TEXT("on") : TEXT("off"))));
    }
}

void URaftSimMainMenuWidget::HandleStart()
{
    if (!ScenarioCatalog.IsValidIndex(SelectedScenarioIndex))
    {
        return;
    }
    URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    const FRaftSimCareerScenarioDefinition& Scenario = ScenarioCatalog[SelectedScenarioIndex];
    if (Save && Save->BeginSession(SelectedMode, Scenario.ScenarioId))
    {
        UGameplayStatics::OpenLevel(this, Scenario.LevelName);
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
