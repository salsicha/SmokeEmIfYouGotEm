#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "RaftSimEditorToolValidation.h"
#include "RaftSimFeatureTuningEditorConfig.h"
#include "UObject/Object.h"

#include "RaftSimFeatureTuningEditorShell.generated.h"

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimFeatureTuningShellFlowPoint
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float GainMultiplier = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float StickinessFactor = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float WashoutFactor = 0.0f;
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimFeatureTuningShellControl
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FName ControlId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    ERaftSimRiverFeatureTuningKind FeatureKind = ERaftSimRiverFeatureTuningKind::Hole;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    ERaftSimRiverFeatureTuningDomain Domain = ERaftSimRiverFeatureTuningDomain::VisualOnly;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float MinValue = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float MaxValue = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    float DefaultValue = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bEnabledByDefault = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bAffectsSolverState = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bAffectsRaftCoupling = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bManifestRecordingRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bHasManifestRecord = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bGeoClawComparisonRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bConservationGuardRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bCanHideConservationFailures = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    TArray<FRaftSimFeatureTuningShellFlowPoint> FlowPoints;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimFeatureTuningEditorShellConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FString Schema = TEXT("raftsim.unreal.feature_tuning_editor_shell.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Tools/feature_tuning_editor_shell.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FString FeatureTuningManifest = TEXT("unreal/Content/RaftSim/River/feature_tuning_editor.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FString FeatureForcingDefaults = TEXT("physics/config/feature_forcing_defaults.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    FString FlowPresets = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    TArray<FName> RequiredPanelIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    TArray<FRaftSimFeatureTuningShellControl> Controls;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    TArray<FRaftSimToolValidationMessage> ValidationMessages;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|FeatureTuningShell")
    bool bFeatureForcingEnabledByDefault = false;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimFeatureTuningEditorShellViewModel : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|FeatureTuningShell")
    void Configure(URaftSimFeatureTuningEditorShellConfig* InConfig);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|FeatureTuningShell")
    bool SelectControl(FName ControlId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|FeatureTuningShell")
    bool SetControlValue(FName ControlId, float NewValue);

    UFUNCTION(BlueprintPure, Category = "RaftSim|FeatureTuningShell")
    float GetControlValue(FName ControlId) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|FeatureTuningShell")
    bool HasControlChanged(FName ControlId) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|FeatureTuningShell")
    bool CanExport() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|FeatureTuningShell")
    TArray<FRaftSimToolValidationMessage> GetExportBlockers() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|FeatureTuningShell")
    FName GetSelectedControlId() const { return SelectedControlId; }

private:
    const FRaftSimFeatureTuningShellControl* FindControl(FName ControlId) const;

    UPROPERTY()
    TObjectPtr<URaftSimFeatureTuningEditorShellConfig> Config;

    UPROPERTY()
    TMap<FName, float> CurrentValues;

    UPROPERTY()
    FName SelectedControlId;
};
