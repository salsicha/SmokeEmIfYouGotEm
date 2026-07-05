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

USTRUCT(BlueprintType)
struct FRaftSimCrewBarkLine
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName BarkId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName ConversationState;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName PriorityLane = TEXT("ambient");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName SpeakerArchetype;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FText Line;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    TArray<FName> Tags;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bMayPlayDuringRapid = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bCanInterruptNonCriticalDialogue = false;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewDialoguePriorityLane
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    FName LaneId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    int32 Priority = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bDeterministicSourceOnly = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Crew")
    bool bInterruptsLowerPriority = false;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimCrewPersonaSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Crew")
    TArray<FRaftSimPassengerPersona> Personas;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimCrewConversationCatalog : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Crew")
    FString Schema = TEXT("raftsim.unreal.crew_conversation_bark_catalog.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Crew")
    TArray<FRaftSimCrewDialoguePriorityLane> PriorityLanes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Crew")
    TArray<FRaftSimCrewBarkLine> BarkLines;
};
