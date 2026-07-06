#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "RaftSimRapidRiverEditorConfig.h"
#include "UObject/Object.h"

#include "RaftSimRapidRiverEditorShell.generated.h"

UENUM(BlueprintType)
enum class ERaftSimToolValidationSeverity : uint8
{
    Info,
    Warning,
    Blocking
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimToolValidationMessage
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FName MessageId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    ERaftSimToolValidationSeverity Severity = ERaftSimToolValidationSeverity::Info;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FText Summary;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString SourcePath;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    bool bBlocksExport = false;
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimRiverEditorShellEvidenceRef
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FName EvidenceId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString LayerId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString RightsStatus;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    float Confidence = 0.0f;
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimRiverEditorShellAnnotation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FName AnnotationId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    ERaftSimRiverAnnotationGeometryKind GeometryKind = ERaftSimRiverAnnotationGeometryKind::StationPin;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    float StationStartMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    float StationEndMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    TArray<ERaftSimRiverExpectedOutcome> ExpectedOutcomes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    TArray<FRaftSimRiverEditorShellEvidenceRef> Evidence;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FText GuideNote;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    bool bRightsCleared = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    bool bHasValidationOverlay = false;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimRapidRiverEditorShellConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString Schema = TEXT("raftsim.unreal.rapid_river_editor_shell.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Tools/rapid_river_editor_shell.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString RapidRiverEditorManifest = TEXT("unreal/Content/RaftSim/River/rapid_river_editor.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString SouthForkEditorPassManifest = TEXT("unreal/Content/RaftSim/River/south_fork_first_river_editor_pass.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString TraceableRiverDataAssetsManifest = TEXT("unreal/Content/RaftSim/River/traceable_river_data_assets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    FString RoundTripValidationManifest = TEXT("unreal/Content/RaftSim/River/round_trip_validation.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    TArray<FName> RequiredPanelIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    TArray<FRaftSimRiverEditorShellAnnotation> SampleAnnotations;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditorShell")
    TArray<FRaftSimToolValidationMessage> ValidationMessages;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimRapidRiverEditorShellViewModel : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|RiverEditorShell")
    void Configure(URaftSimRapidRiverEditorShellConfig* InConfig);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|RiverEditorShell")
    bool SelectAnnotation(FName AnnotationId);

    UFUNCTION(BlueprintPure, Category = "RaftSim|RiverEditorShell")
    FName GetSelectedAnnotationId() const { return SelectedAnnotationId; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|RiverEditorShell")
    bool CanExport() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|RiverEditorShell")
    TArray<FRaftSimToolValidationMessage> GetExportBlockers() const;

private:
    const FRaftSimRiverEditorShellAnnotation* FindAnnotation(FName AnnotationId) const;

    UPROPERTY()
    TObjectPtr<URaftSimRapidRiverEditorShellConfig> Config;

    UPROPERTY()
    FName SelectedAnnotationId;
};
