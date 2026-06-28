#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimCrewConversation.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimPassengerPersona
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PassengerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float Trust = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float Fear = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float Fatigue = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    float Skill = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    TArray<FName> DialogueTraits;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewConversationState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName ConversationStateId = TEXT("calm");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName RecentEventId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bGameplayCritical = false;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimCrewPersonaSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Crew")
    TArray<FRaftSimPassengerPersona> Personas;
};
