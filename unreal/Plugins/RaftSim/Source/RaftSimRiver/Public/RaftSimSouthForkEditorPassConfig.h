#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimSouthForkEditorPassConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimSouthForkReviewStatus : uint8
{
    SeedReviewedNeedsHumanSignoff,
    GuideAccepted,
    Rejected,
    Deferred
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkFlowReviewBand
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString Season;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    float DischargeM3s = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FName> ValidationOverlayIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bRequiresOutcomeReview = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkGuideFeedbackAnnotation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName AnnotationId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FString> GuideFeedback;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FName> ExpectedOutcomes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bFootageTimecodesRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bHumanGuideSignoffRequired = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkReviewedRapid
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName RapidId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    ERaftSimSouthForkReviewStatus ReviewStatus = ERaftSimSouthForkReviewStatus::SeedReviewedNeedsHumanSignoff;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    float PeakStationM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FVector2D StationSpanM = FVector2D::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FVector2D MapFocusLonLat = FVector2D::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FName> ReviewedLabels;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FName> ExpectedOutcomes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FRaftSimSouthForkFlowReviewBand> FlowReview;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FRaftSimSouthForkGuideFeedbackAnnotation> GuideFeedbackAnnotations;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bAcceptedForEditorPass = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bRightsProvenanceRequired = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkValidationOverlay
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName OverlayId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FName SolverMode;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString ScenarioPackage;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString Manifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString Fields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString Probes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString ConservationSummary;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bStitchedWholeWindowRequired = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimSouthForkEditorPassConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString Schema = TEXT("raftsim.unreal.south_fork_editor_pass.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString SourceManifest = TEXT("physics/data/real_world/south_fork_american_chili_bar/source_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString CorridorPackage = TEXT("physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString FlowPresets = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString RapidRiverEditor = TEXT("unreal/Content/RaftSim/River/rapid_river_editor.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    FString FeatureTuningEditor = TEXT("unreal/Content/RaftSim/River/feature_tuning_editor.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FRaftSimSouthForkReviewedRapid> ReviewedRapids;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    TArray<FRaftSimSouthForkValidationOverlay> ValidationOverlays;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bRequireGuideFeedbackAnnotations = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bRequireLowMedianHighFlowPresets = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bRequireStitchedValidationOverlays = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkEditor")
    bool bFieldMediaManifestReferencesOnlyUntilRightsClear = true;
};
