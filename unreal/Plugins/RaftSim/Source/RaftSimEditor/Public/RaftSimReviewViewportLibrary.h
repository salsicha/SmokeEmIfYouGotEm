#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "RaftSimReviewViewportLibrary.generated.h"

/** Ephemeral review presentation only; never changes saved editor preferences. */
UCLASS()
class RAFTSIMEDITOR_API URaftSimReviewViewportLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="RaftSim|Review")
    static bool SetOffscreenPlayViewportSize(UObject* WorldContext, int32 Width, int32 Height);
};
