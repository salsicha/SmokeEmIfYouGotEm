#include "RaftSimEditorModule.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Commands/UIAction.h"
#include "Framework/Docking/TabManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "ToolMenus.h"
#include "UObject/SavePackage.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SWindow.h"

#define LOCTEXT_NAMESPACE "FRaftSimEditorModule"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditor, Log, All);

namespace
{
static const FName ReplayDebugViewerTabId(TEXT("RaftSim.ReplayDebugViewer"));
static const FName RapidRiverEditorTabId(TEXT("RaftSim.RapidRiverEditor"));
static const FName FeatureTuningEditorTabId(TEXT("RaftSim.FeatureTuningEditor"));
static const FName GeospatialValidatorTabId(TEXT("RaftSim.GeospatialValidator"));
static const FName VerticalSliceLauncherTabId(TEXT("RaftSim.VerticalSliceLauncher"));

FRaftSimEditorToolDescriptor MakeToolDescriptor(
    FName ToolId,
    ERaftSimEditorToolKind ToolKind,
    const FText& DisplayName,
    const FText& Description,
    const FString& SourceManifest,
    const FString& RequiredModule,
    bool bRequiresValidationBeforeExport)
{
    FRaftSimEditorToolDescriptor Descriptor;
    Descriptor.ToolId = ToolId;
    Descriptor.ToolKind = ToolKind;
    Descriptor.DisplayName = DisplayName;
    Descriptor.Description = Description;
    Descriptor.SourceManifest = SourceManifest;
    Descriptor.RequiredModule = RequiredModule;
    Descriptor.bRequiresValidationBeforeExport = bRequiresValidationBeforeExport;
    return Descriptor;
}

FString GetRepoRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("..")));
}

FString GetCaptureRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), TEXT("docs/tool-captures/milestone25a")));
}

FText SeverityText(ERaftSimToolValidationSeverity Severity)
{
    switch (Severity)
    {
        case ERaftSimToolValidationSeverity::Blocking:
            return LOCTEXT("ValidationSeverityBlocking", "Blocking");
        case ERaftSimToolValidationSeverity::Warning:
            return LOCTEXT("ValidationSeverityWarning", "Warning");
        case ERaftSimToolValidationSeverity::Info:
        default:
            return LOCTEXT("ValidationSeverityInfo", "Info");
    }
}

TSharedRef<SWidget> MakePathRow(const FText& Label, const FString& Path)
{
    return SNew(SVerticalBox)
        + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0.0f, 2.0f)
        [
            SNew(STextBlock)
                .Text(Label)
                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 9))
        ]
        + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0.0f, 0.0f, 0.0f, 4.0f)
        [
            SNew(STextBlock)
                .Text(FText::FromString(Path))
                .AutoWrapText(true)
        ];
}

TSharedRef<SWidget> MakeSectionHeader(const FText& Text)
{
    return SNew(STextBlock)
        .Text(Text)
        .Font(FCoreStyle::GetDefaultFontStyle("Bold", 12));
}

void PumpSlateForCapture(int32 FrameCount)
{
    if (!FSlateApplication::IsInitialized())
    {
        return;
    }

    FSlateApplication& SlateApplication = FSlateApplication::Get();
    for (int32 FrameIndex = 0; FrameIndex < FrameCount; ++FrameIndex)
    {
        SlateApplication.PumpMessages();
        SlateApplication.Tick(ESlateTickType::All);
        FPlatformProcess::Sleep(0.03f);
    }
}

template <typename AssetType, typename PopulateFunc>
bool CreateReviewedAsset(const FString& AssetName, PopulateFunc Populate, FString& OutSummary)
{
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Tools/Reviewed/%s"), *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create package %s\n"), *PackagePath);
        return false;
    }

    AssetType* Asset = FindObject<AssetType>(Package, *AssetName);
    if (!Asset)
    {
        Asset = NewObject<AssetType>(Package, *AssetName, RF_Public | RF_Standalone);
        FAssetRegistryModule::AssetCreated(Asset);
    }

    if (!Asset)
    {
        OutSummary += FString::Printf(TEXT("Failed to create asset %s\n"), *AssetName);
        return false;
    }

    Asset->Modify();
    Populate(Asset);
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    const bool bSaved = UPackage::SavePackage(Package, Asset, *Filename, SaveArgs);
    OutSummary += FString::Printf(TEXT("%s %s -> %s\n"), bSaved ? TEXT("Saved") : TEXT("Failed"), *AssetName, *Filename);
    return bSaved;
}

FRaftSimReplayDebugBookmark MakeBookmark(const TCHAR* Id, const TCHAR* Label, float TimeSeconds, TArray<FName> Tags)
{
    FRaftSimReplayDebugBookmark Bookmark;
    Bookmark.BookmarkId = FName(Id);
    Bookmark.DisplayName = FText::FromString(FString(Label));
    Bookmark.TimeSeconds = TimeSeconds;
    Bookmark.Tags = MoveTemp(Tags);
    return Bookmark;
}

FRaftSimReplayDebugOverlayToggle MakeOverlay(
    ERaftSimWaterDebugView View,
    const TCHAR* Id,
    const TCHAR* Label,
    bool bDefaultEnabled)
{
    FRaftSimReplayDebugOverlayToggle Overlay;
    Overlay.View = View;
    Overlay.OverlayId = FName(Id);
    Overlay.DisplayName = FText::FromString(FString(Label));
    Overlay.bDefaultEnabled = bDefaultEnabled;
    return Overlay;
}

FRaftSimToolValidationMessage MakeValidationMessage(
    const TCHAR* Id,
    ERaftSimToolValidationSeverity Severity,
    const TCHAR* Summary,
    const FString& SourcePath,
    bool bBlocksExport)
{
    FRaftSimToolValidationMessage Message;
    Message.MessageId = FName(Id);
    Message.Severity = Severity;
    Message.Summary = FText::FromString(FString(Summary));
    Message.SourcePath = SourcePath;
    Message.bBlocksExport = bBlocksExport;
    return Message;
}
} // namespace

void FRaftSimEditorModule::StartupModule()
{
    RegisterToolTabs();

    OpenToolConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.OpenTool"),
        TEXT("Open one RaftSim editor tool tab by tool id."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleOpenToolCommand));
    OpenAllToolsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.OpenAllTools"),
        TEXT("Open every RaftSim editor tool tab."),
        FConsoleCommandWithArgsDelegate::CreateLambda([this](const TArray<FString>&) { OpenAllTools(); }));
    CreateReviewedDataAssetsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateReviewedDataAssets"),
        TEXT("Create reviewed RaftSim tool DataAssets from source-controlled manifests."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCreateReviewedDataAssetsCommand));
    CaptureToolEvidenceConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CaptureToolEvidence"),
        TEXT("Open RaftSim tool tabs and capture screenshot evidence."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCaptureToolEvidenceCommand));

    UToolMenus::RegisterStartupCallback(
        FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FRaftSimEditorModule::RegisterMenus));
}

void FRaftSimEditorModule::ShutdownModule()
{
    OpenToolConsoleCommand.Reset();
    OpenAllToolsConsoleCommand.Reset();
    CreateReviewedDataAssetsConsoleCommand.Reset();
    CaptureToolEvidenceConsoleCommand.Reset();
    UnregisterToolTabs();

    if (UObjectInitialized())
    {
        UToolMenus::UnRegisterStartupCallback(this);
        UToolMenus::UnregisterOwner(this);
    }
}

void FRaftSimEditorModule::RegisterMenus()
{
    FToolMenuOwnerScoped OwnerScoped(this);

    UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu(TEXT("LevelEditor.MainMenu"));
    if (!MainMenu)
    {
        return;
    }

    FToolMenuSection& Section = MainMenu->FindOrAddSection(TEXT("RaftSimTools"));
    Section.AddSubMenu(
        TEXT("RaftSimToolsSubMenu"),
        LOCTEXT("RaftSimToolsLabel", "RaftSim Tools"),
        LOCTEXT("RaftSimToolsTooltip", "Open RaftSim validation, replay, river authoring, and playtest tools."),
        FNewToolMenuDelegate::CreateRaw(this, &FRaftSimEditorModule::PopulateRaftSimToolsMenu));
}

void FRaftSimEditorModule::RegisterToolTabs()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        const FName TabId = GetTabIdForTool(Descriptor.ToolId);
        FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
            TabId,
            FOnSpawnTab::CreateRaw(this, &FRaftSimEditorModule::SpawnToolTab, Descriptor.ToolId))
            .SetDisplayName(Descriptor.DisplayName)
            .SetTooltipText(Descriptor.Description)
            .SetMenuType(ETabSpawnerMenuType::Hidden);
    }
}

void FRaftSimEditorModule::UnregisterToolTabs()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(GetTabIdForTool(Descriptor.ToolId));
    }
}

void FRaftSimEditorModule::PopulateRaftSimToolsMenu(UToolMenu* Menu)
{
    if (!Menu)
    {
        return;
    }

    FToolMenuSection& ToolSection =
        Menu->AddSection(TEXT("RaftSimToolSurfaces"), LOCTEXT("RaftSimToolSurfaces", "Tool Surfaces"));

    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        ToolSection.AddMenuEntry(
            Descriptor.ToolId,
            Descriptor.DisplayName,
            Descriptor.Description,
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateRaw(this, &FRaftSimEditorModule::LaunchTool, Descriptor.ToolId)));
    }

    FToolMenuSection& UtilitySection =
        Menu->AddSection(TEXT("RaftSimToolUtilities"), LOCTEXT("RaftSimToolUtilities", "Utilities"));
    UtilitySection.AddMenuEntry(
        TEXT("OpenAllRaftSimTools"),
        LOCTEXT("OpenAllRaftSimTools", "Open All Tool Tabs"),
        LOCTEXT("OpenAllRaftSimToolsTooltip", "Open every RaftSim tool surface for review or screenshot capture."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateRaw(this, &FRaftSimEditorModule::OpenAllTools)));
    UtilitySection.AddMenuEntry(
        TEXT("CreateReviewedRaftSimDataAssets"),
        LOCTEXT("CreateReviewedRaftSimDataAssets", "Create Reviewed Tool DataAssets"),
        LOCTEXT("CreateReviewedRaftSimDataAssetsTooltip", "Generate reviewed DataAssets from the source-controlled tool manifests."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreateReviewedToolDataAssets(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CaptureRaftSimToolEvidence"),
        LOCTEXT("CaptureRaftSimToolEvidence", "Capture Tool Screenshots"),
        LOCTEXT("CaptureRaftSimToolEvidenceTooltip", "Capture screenshot evidence for all currently open RaftSim tool tabs."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CaptureToolEvidence(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
}

void FRaftSimEditorModule::LaunchTool(FName ToolId)
{
    const FName TabId = GetTabIdForTool(ToolId);
    TSharedPtr<SDockTab> Tab = FGlobalTabmanager::Get()->TryInvokeTab(TabId);
    if (Tab.IsValid())
    {
        OpenedToolTabs.Add(ToolId, Tab);
    }

    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("RaftSim editor tool opened: %s. Registry manifest: %s"),
        *ToolId.ToString(),
        RaftSimEditorTools::ToolRegistryManifestPath);
}

void FRaftSimEditorModule::OpenAllTools()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        LaunchTool(Descriptor.ToolId);
    }
}

void FRaftSimEditorModule::HandleOpenToolCommand(const TArray<FString>& Args)
{
    if (Args.IsEmpty())
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("RaftSim.OpenTool requires a tool id."));
        return;
    }

    LaunchTool(FName(*Args[0]));
}

void FRaftSimEditorModule::HandleCreateReviewedDataAssetsCommand(const TArray<FString>&)
{
    FString Summary;
    CreateReviewedToolDataAssets(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCaptureToolEvidenceCommand(const TArray<FString>&)
{
    FString Summary;
    CaptureToolEvidence(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::ExecuteValidationAction(FName ActionId)
{
    const FRaftSimToolValidationAction* Action = RaftSimEditorValidation::FindDefaultValidationAction(ActionId);
    if (!Action)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("Unknown RaftSim validation action: %s"), *ActionId.ToString());
        return;
    }

    const FRaftSimToolValidationActionResult Result = RaftSimEditorValidation::ExecuteAction(*Action);
    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("Validation action %s: %s"),
        *ActionId.ToString(),
        *Result.Message.Summary.ToString());
}

const TArray<FRaftSimEditorToolDescriptor>& FRaftSimEditorModule::GetToolDescriptors()
{
    if (ToolDescriptors.IsEmpty())
    {
        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("ReplayDebugViewer"),
            ERaftSimEditorToolKind::ReplayDebugViewer,
            LOCTEXT("ReplayDebugViewerLabel", "Replay + Debug Viewer"),
            LOCTEXT("ReplayDebugViewerTooltip", "Review replay bookmarks, water fields, contacts, and runtime overlays."),
            TEXT("unreal/Content/RaftSim/Tools/replay_debug_viewer.json"),
            TEXT("RaftSimDebug"),
            false));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("RapidRiverEditor"),
            ERaftSimEditorToolKind::RapidRiverEditor,
            LOCTEXT("RapidRiverEditorLabel", "Rapid/River Editor"),
            LOCTEXT("RapidRiverEditorTooltip", "Author river annotations, source evidence, expected raft outcomes, and export readiness."),
            TEXT("unreal/Content/RaftSim/Tools/rapid_river_editor_shell.json"),
            TEXT("RaftSimRiver"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("FeatureTuningEditor"),
            ERaftSimEditorToolKind::FeatureTuningEditor,
            LOCTEXT("FeatureTuningEditorLabel", "Feature Tuning Editor"),
            LOCTEXT("FeatureTuningEditorTooltip", "Tune flow-dependent feature forcing and presentation cues with validation guards."),
            TEXT("unreal/Content/RaftSim/Tools/feature_tuning_editor_shell.json"),
            TEXT("RaftSimRiver"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("GeospatialValidator"),
            ERaftSimEditorToolKind::GeospatialValidator,
            LOCTEXT("GeospatialValidatorLabel", "Geospatial Import/Export Validator"),
            LOCTEXT("GeospatialValidatorTooltip", "Check source manifests, CRS, reach-local grids, stitched exports, and solver regeneration."),
            TEXT("unreal/Content/RaftSim/River/geospatial_import_pipeline.json"),
            TEXT("RaftSimGeo"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("VerticalSliceLauncher"),
            ERaftSimEditorToolKind::VerticalSliceLauncher,
            LOCTEXT("VerticalSliceLauncherLabel", "Vertical Slice Playtest Launcher"),
            LOCTEXT("VerticalSliceLauncherTooltip", "Launch the selected South Fork vertical-slice scenario and capture review evidence."),
            TEXT("unreal/Content/RaftSim/VerticalSlice/first_rapid_vertical_slice.json"),
            TEXT("RaftSimUI"),
            false));
    }

    return ToolDescriptors;
}

const FRaftSimEditorToolDescriptor* FRaftSimEditorModule::FindToolDescriptor(FName ToolId)
{
    return GetToolDescriptors().FindByPredicate(
        [ToolId](const FRaftSimEditorToolDescriptor& Descriptor)
        {
            return Descriptor.ToolId == ToolId;
        });
}

FName FRaftSimEditorModule::GetTabIdForTool(FName ToolId) const
{
    if (ToolId == TEXT("ReplayDebugViewer"))
    {
        return ReplayDebugViewerTabId;
    }
    if (ToolId == TEXT("RapidRiverEditor"))
    {
        return RapidRiverEditorTabId;
    }
    if (ToolId == TEXT("FeatureTuningEditor"))
    {
        return FeatureTuningEditorTabId;
    }
    if (ToolId == TEXT("GeospatialValidator"))
    {
        return GeospatialValidatorTabId;
    }
    if (ToolId == TEXT("VerticalSliceLauncher"))
    {
        return VerticalSliceLauncherTabId;
    }

    return ReplayDebugViewerTabId;
}

TSharedRef<SDockTab> FRaftSimEditorModule::SpawnToolTab(const FSpawnTabArgs& Args, FName ToolId)
{
    const FRaftSimEditorToolDescriptor* Descriptor = FindToolDescriptor(ToolId);

    TSharedRef<SDockTab> Tab = SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        .Label(Descriptor ? Descriptor->DisplayName : FText::FromName(ToolId));

    if (Descriptor)
    {
        TSharedRef<SWidget> ToolPanel = BuildToolPanel(*Descriptor);
        Tab->SetContent(ToolPanel);
        OpenedToolTabs.Add(ToolId, Tab);
        OpenedToolPanels.Add(ToolId, ToolPanel);
    }
    else
    {
        Tab->SetContent(
            SNew(STextBlock)
                .Text(FText::Format(LOCTEXT("UnknownRaftSimTool", "Unknown RaftSim tool: {0}"), FText::FromName(ToolId))));
    }

    return Tab;
}

TSharedRef<SWidget> FRaftSimEditorModule::BuildToolPanel(const FRaftSimEditorToolDescriptor& Descriptor)
{
    TSharedRef<SVerticalBox> Root = SNew(SVerticalBox);

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 10.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.DisplayName)
            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 16))
    ];

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 0.0f, 12.0f, 8.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.Description)
            .AutoWrapText(true)
    ];

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 0.0f, 12.0f, 8.0f)
    [
        MakePathRow(LOCTEXT("ToolSourceManifest", "Source Manifest"), Descriptor.SourceManifest)
    ];

    Root->AddSlot()
        .FillHeight(1.0f)
        .Padding(12.0f, 0.0f)
    [
        SNew(SScrollBox)
        + SScrollBox::Slot()
        [
            BuildToolSpecificBody(Descriptor)
        ]
    ];

    TSharedRef<SUniformGridPanel> ButtonGrid = SNew(SUniformGridPanel).SlotPadding(FMargin(4.0f));
    const TArray<FRaftSimToolValidationAction> Actions = RaftSimEditorValidation::BuildDefaultValidationActions();
    for (int32 Index = 0; Index < Actions.Num(); ++Index)
    {
        const FRaftSimToolValidationAction& Action = Actions[Index];
        ButtonGrid->AddSlot(Index % 4, Index / 4)
        [
            SNew(SButton)
                .Text(Action.DisplayName)
                .ToolTipText(FText::FromString(Action.CommandPreview))
                .OnClicked_Lambda(
                    [this, ActionId = Action.ActionId]()
                    {
                        ExecuteValidationAction(ActionId);
                        return FReply::Handled();
                    })
        ];
    }

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 8.0f)
    [
        SNew(SBorder)
            .Padding(8.0f)
        [
            SNew(SVerticalBox)
            + SVerticalBox::Slot()
                .AutoHeight()
                .Padding(0.0f, 0.0f, 0.0f, 6.0f)
            [
                MakeSectionHeader(LOCTEXT("ValidationActionsHeader", "Validation Actions"))
            ]
            + SVerticalBox::Slot()
                .AutoHeight()
            [
                ButtonGrid
            ]
        ]
    ];

    return Root;
}

TSharedRef<SWidget> FRaftSimEditorModule::BuildToolSpecificBody(const FRaftSimEditorToolDescriptor& Descriptor)
{
    TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);

    Body->AddSlot()
        .AutoHeight()
        .Padding(0.0f, 4.0f)
    [
        MakeSectionHeader(LOCTEXT("ToolReadinessHeader", "Readiness"))
    ];

    Body->AddSlot()
        .AutoHeight()
        .Padding(0.0f, 2.0f, 0.0f, 8.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.bRequiresValidationBeforeExport
                ? LOCTEXT("ToolRequiresValidation", "Exports are blocked until validation actions and source evidence pass.")
                : LOCTEXT("ToolReviewOnly", "This tool is review/playtest oriented and does not export authoritative river data."))
            .AutoWrapText(true)
    ];

    if (Descriptor.ToolId == TEXT("ReplayDebugViewer"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("ReplayTimelineHeader", "Timeline And Overlays"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("ReplayManifest", "Replay Manifest"), TEXT("physics/data/readiness/milestone_10/unreal_visualization/manifest.json"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("DebugManifest", "Debug Views"), TEXT("unreal/Content/RaftSim/Debug/live_water_debug_views.json"))];
        Body->AddSlot().AutoHeight().Padding(0.0f, 6.0f)[SNew(STextBlock).Text(LOCTEXT("ReplayOverlayList", "Default overlays: depth, velocity, raft trajectory, contact probes, and runtime budgets. Optional overlays: Froude, wet/dry mask, feature tags, and conservation deltas.")).AutoWrapText(true)];
    }
    else if (Descriptor.ToolId == TEXT("RapidRiverEditor"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("RiverEditorPanelsHeader", "Authoring Panels"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("RiverEditorPanels", "Map view, annotation list, evidence refs, guide notes, expected outcomes, source provenance, validation warnings, and export readiness.")).AutoWrapText(true)];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("SouthForkPass", "South Fork Sample"), TEXT("unreal/Content/RaftSim/River/south_fork_first_river_editor_pass.json"))];
    }
    else if (Descriptor.ToolId == TEXT("FeatureTuningEditor"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("FeatureTuningControlsHeader", "Feature Tuning Controls"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("FeatureTuningControls", "Controls separate solver-state, raft-coupling, visual-only, and audio-only domains. Physics-facing edits require manifest records, GeoClaw comparison, and conservation guards.")).AutoWrapText(true)];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("FeatureDefaults", "Feature Defaults"), TEXT("physics/config/feature_forcing_defaults.json"))];
    }
    else if (Descriptor.ToolId == TEXT("GeospatialValidator"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("GeospatialValidationHeader", "Geospatial Validation"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("GeospatialValidation", "Validates source manifests, CRS/transform metadata, reach-local grids, stitched whole-window outputs, and solver package regeneration evidence.")).AutoWrapText(true)];
    }
    else if (Descriptor.ToolId == TEXT("VerticalSliceLauncher"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("VerticalSliceHeader", "Vertical Slice Review"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("VerticalSliceReview", "Launches the selected South Fork scenario after replay/debug and validation evidence is clean. Current launcher exposes acceptance reports and playtest evidence hooks.")).AutoWrapText(true)];
    }

    Body->AddSlot().AutoHeight().Padding(0.0f, 10.0f)[SNew(SSeparator)];
    Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("CommandLineHeader", "Command Line Hooks"))];
    Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("CommandLineHooks", "Use RaftSim.OpenAllTools, RaftSim.CreateReviewedDataAssets, and RaftSim.CaptureToolEvidence from the Unreal console or ExecCmds for repeatable review runs.")).AutoWrapText(true)];

    return Body;
}

bool FRaftSimEditorModule::CreateReviewedToolDataAssets(FString& OutSummary)
{
    bool bAllSaved = true;

    bAllSaved &= CreateReviewedAsset<URaftSimEditorToolRegistry>(
        TEXT("DA_RaftSimToolRegistry"),
        [this](URaftSimEditorToolRegistry* Asset)
        {
            Asset->Tools = GetToolDescriptors();
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimReplayDebugViewerConfig>(
        TEXT("DA_ReplayDebugViewer"),
        [](URaftSimReplayDebugViewerConfig* Asset)
        {
            Asset->Bookmarks = {
                MakeBookmark(TEXT("entry"), TEXT("Entry"), 0.0f, {TEXT("line_choice"), TEXT("initial_raft_pose")}),
                MakeBookmark(TEXT("first_contact_window"), TEXT("First Contact Window"), 1.0f / 60.0f, {TEXT("raft_contact"), TEXT("force_sample")}),
                MakeBookmark(TEXT("force_peak_review"), TEXT("Force Peak Review"), 0.05f, {TEXT("buoyancy"), TEXT("drag"), TEXT("contact_probe")}),
                MakeBookmark(TEXT("exit_pose"), TEXT("Exit Pose"), 4.0f / 60.0f, {TEXT("finish"), TEXT("runtime_budget")})};
            Asset->Overlays = {
                MakeOverlay(ERaftSimWaterDebugView::Depth, TEXT("depth"), TEXT("Depth"), true),
                MakeOverlay(ERaftSimWaterDebugView::Velocity, TEXT("velocity"), TEXT("Velocity"), true),
                MakeOverlay(ERaftSimWaterDebugView::Froude, TEXT("froude"), TEXT("Froude"), false),
                MakeOverlay(ERaftSimWaterDebugView::WetDryMask, TEXT("wet_dry_mask"), TEXT("Wet/Dry Mask"), false),
                MakeOverlay(ERaftSimWaterDebugView::FeatureTags, TEXT("feature_tags"), TEXT("Feature Tags"), false),
                MakeOverlay(ERaftSimWaterDebugView::ConservationDeltas, TEXT("conservation_deltas"), TEXT("Conservation Deltas"), false),
                MakeOverlay(ERaftSimWaterDebugView::RaftTrajectory, TEXT("raft_trajectory"), TEXT("Raft Trajectory"), true),
                MakeOverlay(ERaftSimWaterDebugView::ContactProbes, TEXT("contact_probes"), TEXT("Contact Probes"), true),
                MakeOverlay(ERaftSimWaterDebugView::RuntimeBudgets, TEXT("runtime_budgets"), TEXT("Runtime Budgets"), true)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimRapidRiverEditorShellConfig>(
        TEXT("DA_RapidRiverEditorShell"),
        [](URaftSimRapidRiverEditorShellConfig* Asset)
        {
            Asset->RequiredPanelIds = {
                TEXT("map_view"),
                TEXT("annotation_list"),
                TEXT("evidence_refs"),
                TEXT("guide_notes"),
                TEXT("expected_outcomes"),
                TEXT("source_provenance"),
                TEXT("validation_warnings"),
                TEXT("export_readiness")};

            FRaftSimRiverEditorShellEvidenceRef Evidence;
            Evidence.EvidenceId = TEXT("round_trip_validation");
            Evidence.LayerId = TEXT("stitched_validation_overlay");
            Evidence.SourceManifest = TEXT("unreal/Content/RaftSim/River/round_trip_validation.json");
            Evidence.RightsStatus = TEXT("internal_validation_artifact");
            Evidence.Confidence = 0.7f;

            FRaftSimRiverEditorShellAnnotation Annotation;
            Annotation.AnnotationId = TEXT("first_technical_raft_line");
            Annotation.DisplayName = FText::FromString(TEXT("First Technical Raft Line"));
            Annotation.GeometryKind = ERaftSimRiverAnnotationGeometryKind::RaftLine;
            Annotation.StationStartMeters = 90.0f;
            Annotation.StationEndMeters = 135.0f;
            Annotation.ExpectedOutcomes = {
                ERaftSimRiverExpectedOutcome::Surf,
                ERaftSimRiverExpectedOutcome::Flush,
                ERaftSimRiverExpectedOutcome::Pin,
                ERaftSimRiverExpectedOutcome::Release,
                ERaftSimRiverExpectedOutcome::Flip};
            Annotation.Evidence = {Evidence};
            Annotation.GuideNote = FText::FromString(TEXT("Reviewed shell sample for surf/flush/pin/release/flip trajectory review."));
            Annotation.bRightsCleared = true;
            Annotation.bHasValidationOverlay = true;
            Asset->SampleAnnotations = {Annotation};
            Asset->ValidationMessages = {
                MakeValidationMessage(
                    TEXT("stitched_export_required"),
                    ERaftSimToolValidationSeverity::Warning,
                    TEXT("Every playable window must preserve stitched whole-window validation outputs."),
                    TEXT("unreal/Content/RaftSim/River/reach_local_streaming.json"),
                    false)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimFeatureTuningEditorShellConfig>(
        TEXT("DA_FeatureTuningEditorShell"),
        [](URaftSimFeatureTuningEditorShellConfig* Asset)
        {
            Asset->RequiredPanelIds = {
                TEXT("flow_band_curve_editor"),
                TEXT("feature_gain_bounds"),
                TEXT("hole_stickiness_washout"),
                TEXT("eddy_lateral_wave_train_tuning"),
                TEXT("boulder_shelf_pin_release_tuning"),
                TEXT("visual_audio_only_tuning"),
                TEXT("manifest_recording_and_validation")};

            FRaftSimFeatureTuningShellControl Hole;
            Hole.ControlId = TEXT("hole_retention_gain");
            Hole.DisplayName = FText::FromString(TEXT("Hole Retention Gain"));
            Hole.FeatureKind = ERaftSimRiverFeatureTuningKind::Hole;
            Hole.Domain = ERaftSimRiverFeatureTuningDomain::SolverState;
            Hole.DefaultValue = 0.05f;
            Hole.bAffectsSolverState = true;
            Hole.bAffectsRaftCoupling = true;
            Hole.bGeoClawComparisonRequired = true;
            Hole.bConservationGuardRequired = true;

            FRaftSimFeatureTuningShellControl Foam;
            Foam.ControlId = TEXT("wave_train_foam_density");
            Foam.DisplayName = FText::FromString(TEXT("Wave Train Foam Density"));
            Foam.FeatureKind = ERaftSimRiverFeatureTuningKind::WaveTrain;
            Foam.Domain = ERaftSimRiverFeatureTuningDomain::VisualOnly;
            Foam.DefaultValue = 0.25f;
            Foam.bEnabledByDefault = true;
            Foam.bGeoClawComparisonRequired = false;
            Foam.bConservationGuardRequired = false;
            Asset->Controls = {Hole, Foam};
            Asset->ValidationMessages = {
                MakeValidationMessage(
                    TEXT("physics_edits_require_geoclaw"),
                    ERaftSimToolValidationSeverity::Warning,
                    TEXT("Changed physics-facing controls must be manifest-recorded, GeoClaw-compared, and conservation-guarded."),
                    TEXT("unreal/Content/RaftSim/River/feature_tuning_editor.json"),
                    false)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimToolValidationActionRegistry>(
        TEXT("DA_ToolValidationActions"),
        [](URaftSimToolValidationActionRegistry* Asset)
        {
            Asset->Actions = RaftSimEditorValidation::BuildDefaultValidationActions();
        },
        OutSummary);

    return bAllSaved;
}

bool FRaftSimEditorModule::CaptureToolEvidence(FString& OutSummary)
{
    OpenAllTools();
    PumpSlateForCapture(12);

    const FString CaptureRoot = GetCaptureRoot();
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    TArray<FString> CapturedFiles;
    bool bAllCaptured = true;

    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        TSharedPtr<SDockTab> Tab = OpenedToolTabs.FindRef(Descriptor.ToolId).Pin();
        if (!Tab.IsValid())
        {
            Tab = FGlobalTabmanager::Get()->TryInvokeTab(GetTabIdForTool(Descriptor.ToolId));
        }

        if (!Tab.IsValid())
        {
            bAllCaptured = false;
            OutSummary += FString::Printf(TEXT("No tab available for %s\n"), *Descriptor.ToolId.ToString());
            continue;
        }

        TSharedPtr<SWidget> ToolPanel = OpenedToolPanels.FindRef(Descriptor.ToolId).Pin();
        const TSharedRef<SWidget> CaptureTarget = ToolPanel.IsValid() ? ToolPanel.ToSharedRef() : Tab.ToSharedRef();

        FString ScreenshotPath;
        const FString BaseFileName = FPaths::Combine(CaptureRoot, Descriptor.ToolId.ToString());
        const bool bCaptured = SaveWidgetScreenshot(CaptureTarget, BaseFileName, ScreenshotPath);
        bAllCaptured &= bCaptured;
        if (bCaptured)
        {
            FString CapturedPath = ScreenshotPath;
            FString RepoRootWithSlash = GetRepoRoot();
            if (!RepoRootWithSlash.EndsWith(TEXT("/")) && !RepoRootWithSlash.EndsWith(TEXT("\\")))
            {
                RepoRootWithSlash += TEXT("/");
            }
            FPaths::MakePathRelativeTo(CapturedPath, *RepoRootWithSlash);
            CapturedFiles.Add(CapturedPath);
            OutSummary += FString::Printf(TEXT("Captured %s\n"), *ScreenshotPath);
        }
        else
        {
            OutSummary += FString::Printf(TEXT("Failed to capture %s\n"), *Descriptor.ToolId.ToString());
        }
    }

    FString FilesJson;
    for (int32 Index = 0; Index < CapturedFiles.Num(); ++Index)
    {
        FilesJson += FString::Printf(
            TEXT("%s\"%s\""),
            Index == 0 ? TEXT("") : TEXT(", "),
            *CapturedFiles[Index].Replace(TEXT("\\"), TEXT("\\\\")));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.tool_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"slate_screenshot_sequence\",\n")
        TEXT("  \"video_capture_status\": \"not_recorded; automated Slate screenshots captured; video requires native recorder integration or macOS Screen Recording permission\",\n")
        TEXT("  \"captured_files\": [%s]\n")
        TEXT("}\n"),
        *FilesJson);
    FFileHelper::SaveStringToFile(Manifest, *FPaths::Combine(CaptureRoot, TEXT("tool_capture_manifest.json")));

    return bAllCaptured;
}

bool FRaftSimEditorModule::SaveWidgetScreenshot(
    const TSharedRef<SWidget>& Widget,
    const FString& BaseFileName,
    FString& OutPath) const
{
    if (!FSlateApplication::IsInitialized())
    {
        return false;
    }

    auto CaptureWidget = [&BaseFileName, &OutPath](const TSharedRef<SWidget>& TargetWidget) -> bool
    {
        PumpSlateForCapture(2);

        TArray<FColor> ImageData;
        FIntVector ImageSize;
        if (!FSlateApplication::Get().TakeScreenshot(TargetWidget, ImageData, ImageSize) || ImageData.IsEmpty() ||
            ImageSize.X <= 0 || ImageSize.Y <= 0)
        {
            return false;
        }

        TArray64<uint8> CompressedPng;
        FImageUtils::PNGCompressImageArray(ImageSize.X, ImageSize.Y, MakeArrayView(ImageData), CompressedPng);
        OutPath = BaseFileName + TEXT(".png");
        return FFileHelper::SaveArrayToFile(CompressedPng, *OutPath);
    };

    if (CaptureWidget(Widget))
    {
        return true;
    }

    TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(Widget);
    return ParentWindow.IsValid() ? CaptureWidget(ParentWindow.ToSharedRef()) : false;
}

IMPLEMENT_MODULE(FRaftSimEditorModule, RaftSimEditor)

#undef LOCTEXT_NAMESPACE
