#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimRapidRiverEditorConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRiverAnnotationGeometryKind : uint8
{
    StationPin,
    ReachSpan,
    DropSpan,
    Polygon,
    RaftLine
};

UENUM(BlueprintType)
enum class ERaftSimRiverExpectedOutcome : uint8
{
    Surf,
    Flush,
    Pin,
    Release,
    Flip
};

USTRUCT(BlueprintType)
struct FRaftSimRiverEditorRightsProvenance
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString SourceId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString LicenseOrTerms;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString Attribution;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString PermissionStatus;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    float Confidence = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverEditorEvidenceRef
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FName LayerId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<FString> SourceIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<FString> Artifacts;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverAnnotationTemplate
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FName TemplateId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    ERaftSimRiverAnnotationGeometryKind GeometryKind = ERaftSimRiverAnnotationGeometryKind::StationPin;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<ERaftSimRiverExpectedOutcome> ExpectedOutcomes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<FString> RequiredFields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    bool bRequiresRightsProvenance = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    bool bRequiresConfidence = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimRapidRiverEditorConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString Schema = TEXT("raftsim.unreal.rapid_river_editor.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString SourceWorkflow = TEXT("physics/data/real_world/south_fork_american_chili_bar/rapid_review_editor_workflow.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    FString TraceableRiverDataAssets = TEXT("unreal/Content/RaftSim/River/traceable_river_data_assets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<FName> RequiredEvidenceLayers;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    TArray<FRaftSimRiverAnnotationTemplate> AnnotationTemplates;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    bool bRequireRightsProvenanceBeforeExport = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RiverEditor")
    bool bRequireExpectedOutcomeBeforeGameplayTuning = true;
};
