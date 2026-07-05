#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimColoradoRowingRouteConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimColoradoRowingControlKind : uint8
{
    Pull,
    BackRow,
    FerryAngle,
    SpinCorrection,
    PassengerTrim,
    RescueAssist
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoFlowBand
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    float DischargeM3s = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString ExpectedRowingBehavior;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bRequiresGaugeHistoryReplacement = true;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoRowingControl
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName ControlId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    ERaftSimColoradoRowingControlKind ControlKind = ERaftSimColoradoRowingControlKind::Pull;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString GameplayRole;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> InputAxes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> Telemetry;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoRouteSegment
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName SegmentId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> ReviewFocus;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString Status;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoValidationAnnotationNeed
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName NeedId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName GeometryKind;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FString> RequiredSources;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> ReviewFields;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoLargeVolumeReadingCue
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName CueId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName CueKind;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString GameplayDecision;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString FlowBandResponse;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> ValidationSignals;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoCanyonPacingCheckpoint
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName CheckpointId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName SegmentId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString GameplayRole;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    float ExpectedRunTimeMinutes = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    float RescueWindowSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> ReviewSignals;
};

USTRUCT(BlueprintType)
struct FRaftSimColoradoGuideReviewAnnotation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName AnnotationId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FName GeometryKind;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FString> RequiredSources;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FName> ReviewFields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bBlocksPlayableSignoff = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimColoradoRowingRouteConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString Schema = TEXT("raftsim.unreal.colorado_rowing_route.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString SourceManifest = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/source_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString FlowPresets = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/flow_presets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString PutIn = TEXT("Lees Ferry");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    FString TakeOut = TEXT("Diamond Creek");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoRouteSegment> RouteSegments;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoFlowBand> FlowBands;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoRowingControl> RowingFrameControls;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoValidationAnnotationNeed> ValidationAnnotationNeeds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoLargeVolumeReadingCue> LargeVolumeReadingCues;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoCanyonPacingCheckpoint> CanyonPacingCheckpoints;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    TArray<FRaftSimColoradoGuideReviewAnnotation> GuideReviewAnnotations;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bDirectManualRowingControlsRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bPassengerPaddleVoiceCommandsEnabled = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    float DefaultLongWaterRescueWindowSeconds = 55.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bOarRigGuideSignoffRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bFieldMediaTimecodesRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bRightsClearedGuideNotesRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ColoradoRowing")
    bool bRequiresGaugeHistoryReplacement = true;
};
