#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimNetworkedCrewEvaluationGate.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimNetworkedCrewPrerequisite
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FName GateId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString EvidenceArtifact;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString RequiredStatus;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    bool bBlocksHumanCrewPrototype = true;
};

USTRUCT(BlueprintType)
struct FRaftSimNetworkedCrewExperimentSlice
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FName SliceId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FName> AllowedModes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FName> RequiredValidationTargets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    bool bInternetPlayAllowed = false;
};

UCLASS(BlueprintType)
class RAFTSIMNETWORK_API URaftSimNetworkedCrewEvaluationGate : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString Schema = TEXT("raftsim.unreal.networked_crew_evaluation_gate.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    FString GateStatus = TEXT("blocked_until_single_player_systems_stable");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FRaftSimNetworkedCrewPrerequisite> Prerequisites;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FRaftSimNetworkedCrewExperimentSlice> ExperimentSlices;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Network")
    bool bAllowNetworkedHumanCrewEvaluation = false;
};
