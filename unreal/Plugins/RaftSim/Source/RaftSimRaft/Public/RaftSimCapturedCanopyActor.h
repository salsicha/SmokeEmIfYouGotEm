#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimCapturedCanopyActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;

/** Saved, evidence-constrained bank canopy. No random runtime scattering.
 * Visual crown/trunk approximations are not hydraulic or collision authority.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimCapturedCanopyActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimCapturedCanopyActor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Captured Canopy")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CanopyA;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Captured Canopy")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CanopyB;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Captured Canopy")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CanopyC;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Captured Canopy")
    FString PlacementSourceSha256;
};
