#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRouteGhostActor.generated.h"

class UProceduralMeshComponent;

/** Thin non-colliding ribbon following the player's best prior route. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimRouteGhostActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRouteGhostActor();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Assist")
    void SetRoute(const TArray<FVector>& WorldPoints);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Assist")
    int32 GetRoutePointCount() const { return RoutePointCount; }

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UProceduralMeshComponent> Ribbon;

    int32 RoutePointCount = 0;
};
