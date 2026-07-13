#pragma once

#include "Containers/Ticker.h"
#include "HAL/IConsoleManager.h"
#include "Modules/ModuleInterface.h"

class SDockTab;
class SWidget;
class FSpawnTabArgs;
class UToolMenu;
class UPCGDefaultExecutionSource;
class UProceduralVegetation;
struct FPCGDataCollection;
struct FManagedArrayCollection;
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
    void HandleCaptureZambeziCliffComparisonCommand(const TArray<FString>& Args);
    void HandleCreateZambeziBatokaBasaltFamilyCommand(const TArray<FString>& Args);
    void HandleCaptureZambeziBatokaBasaltCorridorComparisonCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyCorridorComparisonCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyRenderDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyOpacityDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyLightingDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyReflectanceDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyShadingModelDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyMipPaddingDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsCommand(const TArray<FString>& Args);
    void HandleCaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsCommand(const TArray<FString>& Args);
    void HandleInspectProceduralVegetationSampleCommand(const TArray<FString>& Args);
    void HandleEvaluateProceduralBeechCandidateCommand(const TArray<FString>& Args);
    void HandleCreateFutaleufuNativeCanopyPrototypeCommand(const TArray<FString>& Args);
    void HandleCreateFutaleufuCordilleraCypressFamilyCommand(const TArray<FString>& Args);
    void HandleCreateFutaleufuCordilleraCypressDonorReviewCommand(const TArray<FString>& Args);
    void HandleProceduralBeechPostProcess(const FPCGDataCollection& OutputData);
    bool TickProceduralBeechCandidate(float DeltaSeconds);
    void FinishProceduralBeechCandidate(bool bSuccess, const FString& Summary);
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
    bool CaptureZambeziCliffComparison(FString& OutSummary);
    bool CreateZambeziBatokaBasaltFamily(FString& OutSummary);
    bool CaptureZambeziBatokaBasaltCorridorComparison(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyCorridorComparison(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyRenderDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyOpacityDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyLightingDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyReflectanceDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyShadingModelDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyMipPaddingDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics(FString& OutSummary);
    bool CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics(FString& OutSummary);
    bool CreateFutaleufuNativeCanopyPrototype(FString& OutSummary);
    bool CreateFutaleufuCordilleraCypressFamily(FString& OutSummary);
    bool CreateFutaleufuCordilleraCypressDonorReview(FString& OutSummary);

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
    TUniquePtr<FAutoConsoleCommand> CaptureZambeziCliffComparisonConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateZambeziBatokaBasaltFamilyConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureZambeziBatokaBasaltCorridorComparisonConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyCorridorComparisonConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyRenderDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyOpacityDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyLightingDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyReflectanceDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyShadingModelDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyMipPaddingDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> InspectProceduralVegetationSampleConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> EvaluateProceduralBeechCandidateConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateFutaleufuNativeCanopyPrototypeConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateFutaleufuCordilleraCypressFamilyConsoleCommand;
    TUniquePtr<FAutoConsoleCommand> CreateFutaleufuCordilleraCypressDonorReviewConsoleCommand;
    FDelegateHandle PhotorealEnvironmentAutomationPostEngineInitHandle;
    FTSTicker::FDelegateHandle PhotorealEnvironmentAutomationTickerHandle;
    FTSTicker::FDelegateHandle ProceduralBeechCandidateTickerHandle;
    UPCGDefaultExecutionSource* ProceduralBeechExecutionSource = nullptr;
    UProceduralVegetation* ProceduralBeechCandidateAsset = nullptr;
    UObject* ProceduralBeechGrowthAsset = nullptr;
    TSharedPtr<FManagedArrayCollection> ProceduralBeechOutputCollection;
    FString ProceduralBeechVariant;
    double ProceduralBeechStartSeconds = 0.0;
    bool bCreatePhotorealEnvironmentPreviewMapsOnStartup = false;
    bool bCapturePhotorealEnvironmentPreviewsOnStartup = false;
    bool bCreateLandscapeImportCandidateMapsOnStartup = false;
    bool bCreateZambeziBatokaBasaltFamilyOnStartup = false;
    bool bCaptureZambeziBatokaBasaltCorridorComparisonOnStartup = false;
    bool bCreateFutaleufuCordilleraCypressFamilyOnStartup = false;
    bool bCreateFutaleufuCordilleraCypressDonorReviewOnStartup = false;
    bool bExitAfterPhotorealEnvironmentAutomation = false;
    int32 PhotorealEnvironmentAutomationStartupAttempts = 0;
};
