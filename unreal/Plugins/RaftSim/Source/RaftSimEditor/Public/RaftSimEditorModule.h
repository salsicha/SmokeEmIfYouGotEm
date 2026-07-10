#pragma once

#include "Containers/Ticker.h"
#include "HAL/IConsoleManager.h"
#include "Modules/ModuleInterface.h"

class SDockTab;
class SWidget;
class FSpawnTabArgs;
class UToolMenu;
struct FRaftSimEditorToolDescriptor;

class FRaftSimEditorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

private:
    void RegisterMenus();
    void RegisterToolTabs();
    void UnregisterToolTabs();
    void PopulateRaftSimToolsMenu(UToolMenu* Menu);
    void LaunchTool(FName ToolId);
    void OpenAllTools();
    void HandleOpenToolCommand(const TArray<FString>& Args);
    void HandleCreateReviewedDataAssetsCommand(const TArray<FString>& Args);
    void HandleCaptureToolEvidenceCommand(const TArray<FString>& Args);
    void HandleCreatePhotorealEnvironmentPreviewMapsCommand(const TArray<FString>& Args);
    void HandleCapturePhotorealEnvironmentPreviewsCommand(const TArray<FString>& Args);
    void HandleCreateLandscapeImportCandidateMapsCommand(const TArray<FString>& Args);
    void HandlePhotorealEnvironmentAutomationStartup();
    bool TickPhotorealEnvironmentAutomationStartup(float DeltaSeconds);
    void ExecuteValidationAction(FName ActionId);
    const TArray<FRaftSimEditorToolDescriptor>& GetToolDescriptors();
    const FRaftSimEditorToolDescriptor* FindToolDescriptor(FName ToolId);
    FName GetTabIdForTool(FName ToolId) const;
    TSharedRef<SDockTab> SpawnToolTab(const FSpawnTabArgs& Args, FName ToolId);
    TSharedRef<SWidget> BuildToolPanel(const FRaftSimEditorToolDescriptor& Descriptor);
    TSharedRef<SWidget> BuildToolSpecificBody(const FRaftSimEditorToolDescriptor& Descriptor);
    bool CreateReviewedToolDataAssets(FString& OutSummary);
    bool CaptureToolEvidence(FString& OutSummary);
    bool SaveWidgetScreenshot(const TSharedRef<SWidget>& Widget, const FString& BaseFileName, FString& OutPath) const;
    bool CreatePhotorealEnvironmentPreviewMaps(FString& OutSummary);
    bool CapturePhotorealEnvironmentPreviews(FString& OutSummary);
    bool CreateLandscapeImportCandidateMaps(FString& OutSummary);

    TArray<FRaftSimEditorToolDescriptor> ToolDescriptors;
    TMap<FName, TWeakPtr<SDockTab>> OpenedToolTabs;
    TMap<FName, TWeakPtr<SWidget>> OpenedToolPanels;
    TUniquePtr<FAutoConsoleCommand> OpenToolConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> OpenAllToolsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateReviewedDataAssetsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureToolEvidenceConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreatePhotorealEnvironmentPreviewMapsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CapturePhotorealEnvironmentPreviewsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateLandscapeImportCandidateMapsConsoleCommand;
    FDelegateHandle PhotorealEnvironmentAutomationPostEngineInitHandle;
    FTSTicker::FDelegateHandle PhotorealEnvironmentAutomationTickerHandle;
    bool bCreatePhotorealEnvironmentPreviewMapsOnStartup = false;
    bool bCapturePhotorealEnvironmentPreviewsOnStartup = false;
    bool bCreateLandscapeImportCandidateMapsOnStartup = false;
    bool bExitAfterPhotorealEnvironmentAutomation = false;
    int32 PhotorealEnvironmentAutomationStartupAttempts = 0;
};
