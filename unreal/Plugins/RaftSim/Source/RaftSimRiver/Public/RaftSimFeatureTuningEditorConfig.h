#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimFeatureTuningEditorConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRiverFeatureTuningKind : uint8
{
    Hole,
    Boil,
    Lateral,
    EddyLine,
    WaveTrain,
    ShallowShelf,
    BoulderPushDamping,
    PinRelease,
    Flip
};

UENUM(BlueprintType)
enum class ERaftSimRiverFeatureTuningDomain : uint8
{
    SolverState,
    RaftCoupling,
    VisualOnly,
    AudioOnly
};

USTRUCT(BlueprintType)
struct FRaftSimRiverFeatureFlowBandSample
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float GainMultiplier = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float SouthForkActivationScale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float EffectiveDefaultGain = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float StickinessFactor = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float WashoutFactor = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverFeatureTuningRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    ERaftSimRiverFeatureTuningKind FeatureKind = ERaftSimRiverFeatureTuningKind::Hole;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FName ReviewLabel;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FName FlowResponseCurveId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float DefaultGain = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float MinGain = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float MaxGain = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<ERaftSimRiverFeatureTuningDomain> EditorDomains;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FRaftSimRiverFeatureFlowBandSample> FlowBandSamples;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FName> TunableParameters;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FString> SolverStateEffects;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FString> RaftCouplingEffects;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FString> VisualOnlyParameters;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FString> AudioOnlyParameters;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bEnabledByDefault = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bManifestRecordingRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bGeoClawComparisonRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bConservationGuardRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bHideConservationFailures = false;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverVisualAudioOnlyControl
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FName ControlId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    ERaftSimRiverFeatureTuningKind FeatureKind = ERaftSimRiverFeatureTuningKind::Hole;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    ERaftSimRiverFeatureTuningDomain Domain = ERaftSimRiverFeatureTuningDomain::VisualOnly;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    float DefaultValue = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bEffectiveOnSolverState = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bEffectiveOnRaftCoupling = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bManifestRecordingRequired = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimFeatureTuningEditorConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FString Schema = TEXT("raftsim.unreal.feature_tuning_editor.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FString FeatureForcingDefaults = TEXT("physics/config/feature_forcing_defaults.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FString FlowPresets = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    FString RapidReviewFlowDifficultyMapping = TEXT("physics/data/real_world/south_fork_american_chili_bar/rapid_review_flow_difficulty_mapping.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FRaftSimRiverFeatureTuningRecord> FeatureTuningRecords;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    TArray<FRaftSimRiverVisualAudioOnlyControl> VisualAudioOnlyControls;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bFeatureForcingEnabledByDefault = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bKeepDefaultGainsLow = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bManifestRecordEveryEdit = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bRequireGeoClawComparisonBeforeSignoff = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuning")
    bool bRejectConservationFailureMasking = true;
};
