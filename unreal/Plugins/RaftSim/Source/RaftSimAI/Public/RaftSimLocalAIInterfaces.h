#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"

#include "RaftSimLocalAIInterfaces.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimRecognizedSpeech
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    FString Transcript;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    float Confidence = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    float LatencyMs = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewDialogueRequest
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    FName SpeakerId;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    FName ConversationState;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|AI")
    FString PromptContext;
};

UINTERFACE(BlueprintType)
class RAFTSIMAI_API URaftSimSpeechRecognizer : public UInterface
{
    GENERATED_BODY()
};

class RAFTSIMAI_API IRaftSimSpeechRecognizer
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = "RaftSim|AI")
    FRaftSimRecognizedSpeech RecognizeBufferedSpeech();
};

UINTERFACE(BlueprintType)
class RAFTSIMAI_API URaftSimCrewDialogueProvider : public UInterface
{
    GENERATED_BODY()
};

class RAFTSIMAI_API IRaftSimCrewDialogueProvider
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = "RaftSim|AI")
    FString GenerateCrewLine(const FRaftSimCrewDialogueRequest& Request);
};
