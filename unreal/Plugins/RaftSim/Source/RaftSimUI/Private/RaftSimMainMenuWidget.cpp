#include "RaftSimMainMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"

void URaftSimMainMenuWidget::NativeConstruct()
{
    Super::NativeConstruct();

    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;

    UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    UCanvasPanelSlot* ColumnSlot = Canvas->AddChildToCanvas(Column);
    ColumnSlot->SetAnchors(FAnchors(0.5f, 0.5f));
    ColumnSlot->SetAlignment(FVector2D(0.5f, 0.5f));
    ColumnSlot->SetAutoSize(true);

    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(NSLOCTEXT("RaftSim", "MainMenuTitle", "RaftSim"));
    FSlateFontInfo TitleFont = Title->GetFont();
    TitleFont.Size = 64;
    Title->SetFont(TitleFont);
    Column->AddChildToVerticalBox(Title);

    UTextBlock* Subtitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Subtitle->SetText(
        NSLOCTEXT("RaftSim", "MainMenuSubtitle", "Whitewater Guide Simulator — development build"));
    Column->AddChildToVerticalBox(Subtitle);

    MakeMenuButton(
        Column, NSLOCTEXT("RaftSim", "RunTroublemaker", "Run Troublemaker (South Fork)"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleRunTroublemaker));
    MakeMenuButton(
        Column, NSLOCTEXT("RaftSim", "EnterTestTank", "Training Eddy (Test Tank)"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleEnterTestTank));
    MakeMenuButton(
        Column, NSLOCTEXT("RaftSim", "Settings", "Settings"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleToggleSettings));
    MakeMenuButton(
        Column, NSLOCTEXT("RaftSim", "Quit", "Quit"),
        GET_FUNCTION_NAME_CHECKED(URaftSimMainMenuWidget, HandleQuit));

    SettingsSummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    SettingsSummaryText->SetText(FText::GetEmpty());
    Column->AddChildToVerticalBox(SettingsSummaryText);
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

void URaftSimMainMenuWidget::HandleEnterTestTank()
{
    if (URaftSimSaveSubsystem* SaveSubsystem =
            GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        SaveSubsystem->SaveCurrent();
    }
    UGameplayStatics::OpenLevel(this, TestTankLevelName);
}

void URaftSimMainMenuWidget::HandleRunTroublemaker()
{
    if (URaftSimSaveSubsystem* SaveSubsystem =
            GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        SaveSubsystem->SaveCurrent();
    }
    UGameplayStatics::OpenLevel(this, TroublemakerLevelName);
}

void URaftSimMainMenuWidget::HandleToggleSettings()
{
    // P1.5 replaces this with the full settings screen; toggling a persisted
    // flag here proves save round-tripping for the P1 exit gate.
    URaftSimSaveSubsystem* SaveSubsystem =
        GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    if (SaveSubsystem == nullptr || SaveSubsystem->GetSave() == nullptr)
    {
        return;
    }
    FRaftSimVerticalSliceUserSettings& Settings = SaveSubsystem->GetSave()->Settings;
    Settings.bSubtitlesEnabled = !Settings.bSubtitlesEnabled;
    SaveSubsystem->SaveCurrent();
    SettingsSummaryText->SetText(FText::Format(
        NSLOCTEXT("RaftSim", "SubtitlesToggled", "Subtitles: {0} (persisted)"),
        Settings.bSubtitlesEnabled
            ? NSLOCTEXT("RaftSim", "On", "On")
            : NSLOCTEXT("RaftSim", "Off", "Off")));
}

void URaftSimMainMenuWidget::HandleQuit()
{
    UKismetSystemLibrary::QuitGame(
        this, GetOwningPlayer(), EQuitPreference::Quit, /*bIgnorePlatformRestrictions=*/false);
}
