#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "RaftSimEditorToolValidation.h"
#include "UObject/Object.h"

#include "RaftSimToolValidationActions.generated.h"

UENUM(BlueprintType)
enum class ERaftSimToolValidationActionKind : uint8
{
    SourceCheck,
    DeterministicExport,
    SolverPackageRegeneration,
    StitchedWindowValidation,
    LiveWaterSmoke,
    RoundTripValidation,
    OpenReport
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimToolValidationAction
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FName ActionId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FName ToolId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    ERaftSimToolValidationActionKind ActionKind = ERaftSimToolValidationActionKind::SourceCheck;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString ReportPath;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString CommandPreview;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    TArray<FString> RequiredEvidence;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    bool bRequiresEditorAutomation = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    bool bBlocksPromotion = true;
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimToolValidationActionResult
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FName ActionId;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    bool bAccepted = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FRaftSimToolValidationMessage Message;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimToolValidationActionRegistry : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString Schema = TEXT("raftsim.unreal.tool_validation_actions.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Tools/tool_validation_actions.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ToolValidation")
    TArray<FRaftSimToolValidationAction> Actions;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimToolValidationActionRunner : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|ToolValidation")
    void Configure(URaftSimToolValidationActionRegistry* InRegistry);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|ToolValidation")
    FRaftSimToolValidationActionResult RunAction(FName ActionId);

    UFUNCTION(BlueprintPure, Category = "RaftSim|ToolValidation")
    bool CanRunAction(FName ActionId) const;

private:
    const FRaftSimToolValidationAction* FindAction(FName ActionId) const;

    UPROPERTY()
    TObjectPtr<URaftSimToolValidationActionRegistry> Registry;
};
