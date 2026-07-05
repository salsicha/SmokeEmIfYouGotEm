#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimGuideCommands.generated.h"

UENUM(BlueprintType)
enum class ERaftSimGuideCommandIntent : uint8
{
    None,
    ForwardPaddle,
    BackPaddle,
    LeftPaddle,
    RightPaddle,
    Stop,
    Brace,
    HoldOn,
    HighSide,
    LeanLeft,
    LeanRight,
    Rescue,
    Recovery
};

USTRUCT(BlueprintType)
struct FRaftSimGuideCommand
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCommand")
    ERaftSimGuideCommandIntent Intent = ERaftSimGuideCommandIntent::None;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCommand")
    FString SourcePhrase;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCommand")
    float Confidence = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCommand")
    FName DeterministicCrewIntent;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|GuideCommand")
    bool bMatchedGrammar = false;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimGuideCommandParser : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|GuideCommand")
    FRaftSimGuideCommand ParseTranscript(const FString& Transcript, float RecognitionConfidence) const;
};
