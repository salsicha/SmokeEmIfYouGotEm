#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimSelectionViewModels.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimFlowBandOption
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    FName FlowBandId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    FName SeasonId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    float Confidence = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverSectionOption
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    FName RiverId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    FName SectionId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    TArray<FName> DifficultyPresets;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    TArray<FName> RaftSetups;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Selection")
    TArray<FRaftSimFlowBandOption> FlowBands;
};

UCLASS(BlueprintType)
class RAFTSIMUI_API URaftSimSelectionViewModel : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Selection")
    TArray<FRaftSimRiverSectionOption> Sections;
};
