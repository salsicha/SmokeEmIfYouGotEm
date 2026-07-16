#include "RaftSimEditorModule.h"

#include "Algo/AllOf.h"
#include "Algo/AnyOf.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetCompilingManager.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/DynamicMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Dom/JsonObject.h"
#include "UDynamicMesh.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkyLight.h"
#include "Engine/SphereReflectionCapture.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Commands/UIAction.h"
#include "Framework/Docking/TabManager.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerStart.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformMisc.h"
#include "ImageUtils.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Landscape.h"
#include "LandscapeComponent.h"
#include "LandscapeEditorModule.h"
#include "LandscapeFileFormatInterface.h"
#include "LandscapeNaniteComponent.h"
#include "LandscapeProxy.h"
#include "GeometryScript/MeshAssetFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshMaterialFunctions.h"
#include "Materials/MaterialExpressionLandscapeLayerCoords.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionCameraPositionWS.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionFrac.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionOneMinus.h"
#include "Materials/MaterialExpressionObjectPositionWS.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionTwoSidedSign.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialFunctionInterface.h"
#include "MaterialShared.h"
#include "MeshUtilities.h"
#include "MeshDescription.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Modules/ModuleManager.h"
#include "NaniteSceneProxy.h"
#include "PlanarCut.h"
#include "PCGGraph.h"
#include "PCGDefaultExecutionSource.h"
#include "PCGData.h"
#include "PCGEdge.h"
#include "PCGNode.h"
#include "PCGPin.h"
#include "PCGSettings.h"
#include "ProceduralMeshComponent.h"
#include "ProceduralMeshConversion.h"
#include "ProceduralVegetation.h"
#include "DataTypes/PVFoliageInfo.h"
#include "DataTypes/PVMeshData.h"
#include "Facades/PVFoliageFacade.h"
#include "GeometryCollection/GeometryCollection.h"
#include "Utils/PVFloatRamp.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "Subsystems/IPCGBaseSubsystem.h"
#include "ToolMenus.h"
#include "TextureCompiler.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "RenderingThread.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ShaderCompiler.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Input/SSearchBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"
#include "Widgets/SWindow.h"

#define LOCTEXT_NAMESPACE "FRaftSimEditorTools"

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
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    AssetType* Asset = LoadObject<AssetType>(nullptr, *ObjectPath);
    UPackage* Package = Asset ? Asset->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create package %s\n"), *PackagePath);
        return false;
    }

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

struct FRaftSimNamedRapidFilterOption
{
    FString Label;
    FString Value;
};

struct FRaftSimNamedRapidEditorRow
{
    FString RiverId;
    FString RiverDisplayName;
    FString PortfolioRole;
    FString FeatureId;
    FString DisplayName;
    FString DifficultyLabel;
    FString Priority;
    FString StationKind;
    FString GeometryStatus;
    FString MapGeometryStatus;
    FString GuideStatus;
    FString ExecutionStatus;
    FString FeatureTags;
    double StationMeters = 0.0;
    TMap<FString, int32> RunCountsByFlow;
};

struct FRaftSimNamedRapidRunAggregate
{
    TMap<FString, int32> RunCountsByFlow;
    FString ExecutionStatus;
};

struct FRaftSimNamedRapidPanelState : public TSharedFromThis<FRaftSimNamedRapidPanelState>
{
    TArray<TSharedPtr<FRaftSimNamedRapidEditorRow>> AllRows;
    TArray<TSharedPtr<FRaftSimNamedRapidEditorRow>> FilteredRows;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> RiverOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> FlowOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> PriorityOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> StationOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> GeometryOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> GuideOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> ExecutionOptions;
    TArray<TSharedPtr<FRaftSimNamedRapidFilterOption>> PortfolioOptions;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedRiver;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedFlow;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedPriority;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedStation;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedGeometry;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedGuide;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedExecution;
    TSharedPtr<FRaftSimNamedRapidFilterOption> SelectedPortfolio;
    TSharedPtr<SListView<TSharedPtr<FRaftSimNamedRapidEditorRow>>> ListView;
    FString SearchText;
    FString LoadError;
    int32 SourceRunCount = 0;
    int32 RunnableRiverCount = 0;
    int32 AdditionalActiveEnvironmentCount = 0;

    void ApplyFilters()
    {
        FilteredRows.Reset();
        for (const TSharedPtr<FRaftSimNamedRapidEditorRow>& Row : AllRows)
        {
            if (!Row)
            {
                continue;
            }
            if (SelectedRiver.IsValid() && !SelectedRiver->Value.IsEmpty() && Row->RiverId != SelectedRiver->Value)
            {
                continue;
            }
            if (SelectedPortfolio.IsValid() && !SelectedPortfolio->Value.IsEmpty() &&
                Row->PortfolioRole != SelectedPortfolio->Value)
            {
                continue;
            }
            if (SelectedPriority.IsValid() && !SelectedPriority->Value.IsEmpty() && Row->Priority != SelectedPriority->Value)
            {
                continue;
            }
            if (SelectedStation.IsValid() && SelectedStation->Value == TEXT("published") &&
                !Row->StationKind.StartsWith(TEXT("published_")))
            {
                continue;
            }
            if (SelectedStation.IsValid() && SelectedStation->Value == TEXT("provisional") &&
                !Row->StationKind.StartsWith(TEXT("provisional_")))
            {
                continue;
            }
            if (SelectedGeometry.IsValid() && SelectedGeometry->Value.StartsWith(TEXT("exact:")) &&
                Row->GeometryStatus != SelectedGeometry->Value.RightChop(6))
            {
                continue;
            }
            if (SelectedGeometry.IsValid() && SelectedGeometry->Value.StartsWith(TEXT("map:")) &&
                Row->MapGeometryStatus != SelectedGeometry->Value.RightChop(4))
            {
                continue;
            }
            if (SelectedGuide.IsValid() && !SelectedGuide->Value.IsEmpty() && Row->GuideStatus != SelectedGuide->Value)
            {
                continue;
            }
            if (SelectedExecution.IsValid() && !SelectedExecution->Value.IsEmpty() &&
                Row->ExecutionStatus != SelectedExecution->Value)
            {
                continue;
            }
            if (SelectedFlow.IsValid() && !SelectedFlow->Value.IsEmpty() &&
                Row->RunCountsByFlow.FindRef(SelectedFlow->Value) == 0)
            {
                continue;
            }
            if (!SearchText.IsEmpty())
            {
                const FString SearchCorpus = FString::Printf(
                    TEXT("%s %s %s %s %s %s"),
                    *Row->DisplayName,
                    *Row->FeatureId,
                    *Row->RiverDisplayName,
                    *Row->PortfolioRole,
                    *Row->DifficultyLabel,
                    *Row->FeatureTags);
                if (!SearchCorpus.Contains(SearchText, ESearchCase::IgnoreCase))
                {
                    continue;
                }
            }
            FilteredRows.Add(Row);
        }
        if (ListView.IsValid())
        {
            ListView->RequestListRefresh();
        }
    }

    int32 DisplayedRunCount() const
    {
        int32 Count = 0;
        for (const TSharedPtr<FRaftSimNamedRapidEditorRow>& Row : FilteredRows)
        {
            if (!Row)
            {
                continue;
            }
            if (SelectedFlow.IsValid() && !SelectedFlow->Value.IsEmpty())
            {
                Count += Row->RunCountsByFlow.FindRef(SelectedFlow->Value);
            }
            else
            {
                for (const TPair<FString, int32>& Pair : Row->RunCountsByFlow)
                {
                    Count += Pair.Value;
                }
            }
        }
        return Count;
    }
};

TSharedPtr<FRaftSimNamedRapidFilterOption> MakeNamedRapidFilterOption(const TCHAR* Label, const TCHAR* Value)
{
    TSharedPtr<FRaftSimNamedRapidFilterOption> Option = MakeShared<FRaftSimNamedRapidFilterOption>();
    Option->Label = Label;
    Option->Value = Value;
    return Option;
}

bool LoadJsonObjectFromRepo(const FString& RelativePath, TSharedPtr<FJsonObject>& OutObject, FString& OutError)
{
    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *AbsolutePath))
    {
        OutError = FString::Printf(TEXT("Could not read %s"), *RelativePath);
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!FJsonSerializer::Deserialize(Reader, OutObject) || !OutObject.IsValid())
    {
        OutError = FString::Printf(TEXT("Could not parse %s"), *RelativePath);
        return false;
    }
    return true;
}

TSharedRef<SWidget> BuildNamedRapidReviewPanel()
{
    constexpr const TCHAR* MarkerManifest = TEXT("unreal/Content/RaftSim/River/named_rapid_editor_markers.json");
    constexpr const TCHAR* RunManifest = TEXT("unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json");
    TSharedPtr<FRaftSimNamedRapidPanelState> State = MakeShared<FRaftSimNamedRapidPanelState>();

    TSharedPtr<FJsonObject> MarkerRoot;
    TSharedPtr<FJsonObject> RunRoot;
    if (!LoadJsonObjectFromRepo(MarkerManifest, MarkerRoot, State->LoadError) ||
        !LoadJsonObjectFromRepo(RunManifest, RunRoot, State->LoadError))
    {
        return SNew(SBorder)
            .Padding(8.0f)
            [SNew(STextBlock).Text(FText::FromString(State->LoadError)).AutoWrapText(true)];
    }

    TMap<FString, FRaftSimNamedRapidRunAggregate> RunAggregates;
    const TArray<TSharedPtr<FJsonValue>>* Runs = nullptr;
    if (RunRoot->TryGetArrayField(TEXT("runs"), Runs) && Runs)
    {
        State->SourceRunCount = Runs->Num();
        for (const TSharedPtr<FJsonValue>& RunValue : *Runs)
        {
            const TSharedPtr<FJsonObject> Run = RunValue->AsObject();
            if (!Run.IsValid())
            {
                continue;
            }
            const FString FeatureId = Run->GetStringField(TEXT("feature_id"));
            const FString FlowBand = Run->GetStringField(TEXT("flow_band"));
            FRaftSimNamedRapidRunAggregate& Aggregate = RunAggregates.FindOrAdd(FeatureId);
            ++Aggregate.RunCountsByFlow.FindOrAdd(FlowBand);
            Aggregate.ExecutionStatus = Run->GetStringField(TEXT("execution_status"));
        }
    }

    State->RiverOptions.Add(MakeNamedRapidFilterOption(TEXT("All rivers"), TEXT("")));
    const TArray<TSharedPtr<FJsonValue>>* Rivers = nullptr;
    if (MarkerRoot->TryGetArrayField(TEXT("rivers"), Rivers) && Rivers)
    {
        for (const TSharedPtr<FJsonValue>& RiverValue : *Rivers)
        {
            const TSharedPtr<FJsonObject> River = RiverValue->AsObject();
            if (!River.IsValid())
            {
                continue;
            }
            const FString RiverId = River->GetStringField(TEXT("river_id"));
            const FString RiverDisplayName = River->GetStringField(TEXT("display_name"));
            const FString PortfolioRole = River->GetStringField(TEXT("portfolio_role"));
            if (PortfolioRole == TEXT("runnable_river"))
            {
                ++State->RunnableRiverCount;
            }
            else if (PortfolioRole == TEXT("additional_active_environment"))
            {
                ++State->AdditionalActiveEnvironmentCount;
            }
            TSharedPtr<FRaftSimNamedRapidFilterOption> RiverOption = MakeShared<FRaftSimNamedRapidFilterOption>();
            RiverOption->Label = RiverDisplayName;
            RiverOption->Value = RiverId;
            State->RiverOptions.Add(RiverOption);

            const TArray<TSharedPtr<FJsonValue>>* Markers = nullptr;
            if (!River->TryGetArrayField(TEXT("markers"), Markers) || !Markers)
            {
                continue;
            }
            for (const TSharedPtr<FJsonValue>& MarkerValue : *Markers)
            {
                const TSharedPtr<FJsonObject> Marker = MarkerValue->AsObject();
                if (!Marker.IsValid())
                {
                    continue;
                }
                TSharedPtr<FRaftSimNamedRapidEditorRow> Row = MakeShared<FRaftSimNamedRapidEditorRow>();
                Row->RiverId = RiverId;
                Row->RiverDisplayName = RiverDisplayName;
                Row->PortfolioRole = PortfolioRole;
                Row->FeatureId = Marker->GetStringField(TEXT("feature_id"));
                Row->DisplayName = Marker->GetStringField(TEXT("display_name"));
                Row->DifficultyLabel = Marker->GetStringField(TEXT("difficulty_label"));
                Row->Priority = Marker->GetStringField(TEXT("review_priority"));
                Row->GeometryStatus = Marker->GetStringField(TEXT("exact_geometry_status"));
                Row->MapGeometryStatus = Marker->GetStringField(TEXT("editor_map_geometry_status"));
                Row->GuideStatus = Marker->GetStringField(TEXT("guide_review_status"));
                TArray<FString> FeatureTags;
                Marker->TryGetStringArrayField(TEXT("feature_tags"), FeatureTags);
                Row->FeatureTags = FString::Join(FeatureTags, TEXT(", "));
                const TSharedPtr<FJsonObject> Stationing = Marker->GetObjectField(TEXT("stationing"));
                Row->StationKind = Stationing->GetStringField(TEXT("station_kind"));
                Row->StationMeters = Stationing->GetNumberField(TEXT("station_m"));
                if (const FRaftSimNamedRapidRunAggregate* Aggregate = RunAggregates.Find(Row->FeatureId))
                {
                    Row->RunCountsByFlow = Aggregate->RunCountsByFlow;
                    Row->ExecutionStatus = Aggregate->ExecutionStatus;
                }
                State->AllRows.Add(Row);
            }
        }
    }

    State->FlowOptions = {
        MakeNamedRapidFilterOption(TEXT("All flow bands"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Low review"), TEXT("low_review")),
        MakeNamedRapidFilterOption(TEXT("Reference review"), TEXT("reference_review")),
        MakeNamedRapidFilterOption(TEXT("High review"), TEXT("high_review"))};
    State->PriorityOptions = {
        MakeNamedRapidFilterOption(TEXT("All priorities"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Critical"), TEXT("critical")),
        MakeNamedRapidFilterOption(TEXT("High"), TEXT("high")),
        MakeNamedRapidFilterOption(TEXT("Medium"), TEXT("medium"))};
    State->StationOptions = {
        MakeNamedRapidFilterOption(TEXT("All station authority"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Published station"), TEXT("published")),
        MakeNamedRapidFilterOption(TEXT("Provisional station"), TEXT("provisional"))};
    State->GeometryOptions = {
        MakeNamedRapidFilterOption(TEXT("All geometry status"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Exact geometry required"), TEXT("exact:required_before_production")),
        MakeNamedRapidFilterOption(TEXT("Candidate map projection"), TEXT("map:candidate_centerline_projection_not_exact")),
        MakeNamedRapidFilterOption(TEXT("Map geometry unavailable"), TEXT("map:unavailable_outside_current_candidate_centerline"))};
    State->GuideOptions = {
        MakeNamedRapidFilterOption(TEXT("All guide status"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Guide review required"), TEXT("required"))};
    State->ExecutionOptions = {
        MakeNamedRapidFilterOption(TEXT("All execution status"), TEXT("")),
        MakeNamedRapidFilterOption(
            TEXT("Blocked pending geometry/water/line"),
            TEXT("blocked_until_exact_geometry_validated_cpp_window_and_guide_line"))};
    State->PortfolioOptions = {
        MakeNamedRapidFilterOption(TEXT("All portfolio roles"), TEXT("")),
        MakeNamedRapidFilterOption(TEXT("Runnable rivers"), TEXT("runnable_river")),
        MakeNamedRapidFilterOption(
            TEXT("Additional active environments"),
            TEXT("additional_active_environment"))};
    State->SelectedRiver = State->RiverOptions[0];
    State->SelectedFlow = State->FlowOptions[0];
    State->SelectedPriority = State->PriorityOptions[0];
    State->SelectedStation = State->StationOptions[0];
    State->SelectedGeometry = State->GeometryOptions[0];
    State->SelectedGuide = State->GuideOptions[0];
    State->SelectedExecution = State->ExecutionOptions[0];
    State->SelectedPortfolio = State->PortfolioOptions[0];
    State->ApplyFilters();

    const auto GenerateOptionWidget = [](TSharedPtr<FRaftSimNamedRapidFilterOption> Option)
    {
        return SNew(STextBlock).Text(FText::FromString(Option.IsValid() ? Option->Label : TEXT("")));
    };
    const auto MakeComboContent = [](const TSharedPtr<FRaftSimNamedRapidFilterOption>& Selected)
    {
        return FText::FromString(Selected.IsValid() ? Selected->Label : TEXT(""));
    };

    TSharedRef<SUniformGridPanel> FilterGrid = SNew(SUniformGridPanel).SlotPadding(FMargin(3.0f));
    FilterGrid->AddSlot(0, 0)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->RiverOptions)
            .InitiallySelectedItem(State->SelectedRiver)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedRiver = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedRiver); })]];
    FilterGrid->AddSlot(1, 0)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->FlowOptions)
            .InitiallySelectedItem(State->SelectedFlow)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedFlow = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedFlow); })]];
    FilterGrid->AddSlot(2, 0)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->PriorityOptions)
            .InitiallySelectedItem(State->SelectedPriority)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedPriority = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedPriority); })]];
    FilterGrid->AddSlot(0, 1)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->StationOptions)
            .InitiallySelectedItem(State->SelectedStation)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedStation = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedStation); })]];
    FilterGrid->AddSlot(1, 1)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->GeometryOptions)
            .InitiallySelectedItem(State->SelectedGeometry)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedGeometry = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedGeometry); })]];
    FilterGrid->AddSlot(2, 1)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->GuideOptions)
            .InitiallySelectedItem(State->SelectedGuide)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedGuide = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedGuide); })]];
    FilterGrid->AddSlot(0, 2)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->ExecutionOptions)
            .InitiallySelectedItem(State->SelectedExecution)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedExecution = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedExecution); })]];
    FilterGrid->AddSlot(1, 2)[
        SNew(SComboBox<TSharedPtr<FRaftSimNamedRapidFilterOption>>)
            .OptionsSource(&State->PortfolioOptions)
            .InitiallySelectedItem(State->SelectedPortfolio)
            .OnGenerateWidget_Lambda(GenerateOptionWidget)
            .OnSelectionChanged_Lambda([State](TSharedPtr<FRaftSimNamedRapidFilterOption> Value, ESelectInfo::Type) { State->SelectedPortfolio = Value; State->ApplyFilters(); })
            [SNew(STextBlock).Text_Lambda([State, MakeComboContent]() { return MakeComboContent(State->SelectedPortfolio); })]];

    return SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 6.0f)[
            SNew(STextBlock)
                .Text_Lambda([State]()
                {
                    const TCHAR* EnvironmentSuffix =
                        State->AdditionalActiveEnvironmentCount == 1 ? TEXT("") : TEXT("s");
                    return FText::FromString(FString::Printf(
                        TEXT("Portfolio: %d runnable rivers / %d additional active environment%s | Showing %d of %d named rapids and %d of %d review runs"),
                        State->RunnableRiverCount,
                        State->AdditionalActiveEnvironmentCount,
                        EnvironmentSuffix,
                        State->FilteredRows.Num(),
                        State->AllRows.Num(),
                        State->DisplayedRunCount(),
                        State->SourceRunCount));
                })]
        + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 2.0f)[
            SNew(SSearchBox)
                .HintText(LOCTEXT("NamedRapidSearchHint", "Search rapid, river, class, or feature tag"))
                .OnTextChanged_Lambda([State](const FText& Value) { State->SearchText = Value.ToString(); State->ApplyFilters(); })]
        + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 2.0f)[FilterGrid]
        + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 4.0f)[
            SNew(SBox)
                .HeightOverride(520.0f)
                [SAssignNew(State->ListView, SListView<TSharedPtr<FRaftSimNamedRapidEditorRow>>)
                    .ListItemsSource(&State->FilteredRows)
                    .SelectionMode(ESelectionMode::Single)
                    .OnGenerateRow_Lambda(
                        [State](TSharedPtr<FRaftSimNamedRapidEditorRow> Row, const TSharedRef<STableViewBase>& OwnerTable)
                        {
                            const bool bProvisional = Row->StationKind.StartsWith(TEXT("provisional_"));
                            const TCHAR* PortfolioLabel = Row->PortfolioRole == TEXT("runnable_river")
                                ? TEXT("RUNNABLE")
                                : TEXT("ADDITIONAL ACTIVE ENVIRONMENT");
                            const FString FlowFilter = State->SelectedFlow.IsValid() ? State->SelectedFlow->Value : FString();
                            int32 VisibleRuns = 0;
                            if (!FlowFilter.IsEmpty())
                            {
                                VisibleRuns = Row->RunCountsByFlow.FindRef(FlowFilter);
                            }
                            else
                            {
                                for (const TPair<FString, int32>& Pair : Row->RunCountsByFlow)
                                {
                                    VisibleRuns += Pair.Value;
                                }
                            }
                            return SNew(STableRow<TSharedPtr<FRaftSimNamedRapidEditorRow>>, OwnerTable)
                                [SNew(SBorder)
                                    .Padding(6.0f)
                                    .BorderBackgroundColor(bProvisional ? FLinearColor(0.30f, 0.16f, 0.04f, 0.75f) : FLinearColor(0.05f, 0.16f, 0.10f, 0.60f))
                                    [SNew(SVerticalBox)
                                        + SVerticalBox::Slot().AutoHeight()[
                                            SNew(STextBlock)
                                                .Text(FText::FromString(FString::Printf(
                                                    TEXT("%s  |  %s  |  %s"),
                                                    *Row->DisplayName,
                                                    *Row->RiverDisplayName,
                                                    PortfolioLabel)))
                                                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 10))]
                                        + SVerticalBox::Slot().AutoHeight()[
                                            SNew(STextBlock)
                                                .Text(FText::FromString(FString::Printf(
                                                    TEXT("%s | %s priority | %.1f m | %s | %d runs"),
                                                    *Row->DifficultyLabel,
                                                    *Row->Priority,
                                                    Row->StationMeters,
                                                    bProvisional ? TEXT("PROVISIONAL STATION") : TEXT("published station"),
                                                    VisibleRuns)))]
                                        + SVerticalBox::Slot().AutoHeight()[
                                            SNew(STextBlock).Text(FText::FromString(Row->FeatureTags)).AutoWrapText(true)]
                                        + SVerticalBox::Slot().AutoHeight()[
                                            SNew(STextBlock)
                                                .Text(FText::FromString(FString::Printf(
                                                    TEXT("Exact geometry: %s | Map: %s | Guide: %s | Execution: %s"),
                                                    *Row->GeometryStatus,
                                                    *Row->MapGeometryStatus,
                                                    *Row->GuideStatus,
                                                    *Row->ExecutionStatus)))
                                                .AutoWrapText(true)]]];
                        })]];
}
} // namespace

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
    UtilitySection.AddMenuEntry(
        TEXT("CreatePhotorealEnvironmentPreviewMaps"),
        LOCTEXT("CreatePhotorealEnvironmentPreviewMaps", "Create River Preview Maps"),
        LOCTEXT("CreatePhotorealEnvironmentPreviewMapsTooltip", "Generate source-aware procedural Unreal preview maps for South Fork, Colorado, and Pacuare."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreatePhotorealEnvironmentPreviewMaps(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CapturePhotorealEnvironmentPreviews"),
        LOCTEXT("CapturePhotorealEnvironmentPreviews", "Capture River Preview Evidence"),
        LOCTEXT("CapturePhotorealEnvironmentPreviewsTooltip", "Record capture evidence placeholders for generated river environment previews."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CapturePhotorealEnvironmentPreviews(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CreateLandscapeImportCandidateMaps"),
        LOCTEXT("CreateLandscapeImportCandidateMaps", "Create Source Landscape Candidates"),
        LOCTEXT("CreateLandscapeImportCandidateMapsTooltip", "Import the review-gated source DEMs into isolated Landscape candidate maps and capture geometry-review evidence."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreateLandscapeImportCandidateMaps(Summary);
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
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("NamedRapidMarkers", "Named Rapid Markers"), TEXT("unreal/Content/RaftSim/River/named_rapid_editor_markers.json"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("NamedRapidGeometry", "Candidate Marker Geometry"), TEXT("unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("NamedRapidRuns", "Simulator Review Runs"), TEXT("unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json"))];
        Body->AddSlot().AutoHeight().Padding(0.0f, 8.0f, 0.0f, 0.0f)[MakeSectionHeader(LOCTEXT("NamedRapidBrowserHeader", "Named Rapid Review Browser"))];
        Body->AddSlot().AutoHeight()[BuildNamedRapidReviewPanel()];
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
            Asset->NamedRapidEditorMarkersManifest = TEXT("unreal/Content/RaftSim/River/named_rapid_editor_markers.json");
            Asset->NamedRapidEditorGeometryManifest = TEXT("unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson");
            Asset->NamedRapidSimulatorReviewRunsManifest = TEXT("unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json");
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

        Tab->ActivateInParent(ETabActivationCause::SetDirectly);
        PumpSlateForCapture(4);

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

#undef LOCTEXT_NAMESPACE
