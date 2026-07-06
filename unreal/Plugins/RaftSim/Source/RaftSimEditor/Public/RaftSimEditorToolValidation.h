#pragma once

#include "CoreMinimal.h"

#include "RaftSimEditorToolValidation.generated.h"

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
