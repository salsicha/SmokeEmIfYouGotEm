#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "RaftSimLandscapePatchLibrary.generated.h"
class ALandscapeProxy;

/** Small, compare-before-write source-height changes; never rebuilds a map. */
UCLASS()
class RAFTSIMEDITOR_API URaftSimLandscapePatchLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Applies ONLY differing pixels, preserving all unrelated terrain edits.
     * Refuses mismatched source heights, dimensions, a game world, or >4096
     * changed pixels. Does not save: caller reviews and saves exact packages. */
    UFUNCTION(BlueprintCallable, Category="RaftSim|Authoring")
    static FString ApplyHeightfieldPatch(ALandscapeProxy* Landscape,
        const FString& BeforePng, const FString& AfterPng);
};
