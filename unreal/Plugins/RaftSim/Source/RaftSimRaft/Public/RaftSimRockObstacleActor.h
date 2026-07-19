#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRockObstacleActor.generated.h"

class UStaticMeshComponent;

/**
 * Runtime-authoritative contact proxy for a rock that can wrap or pin the raft.
 * The visible mesh and the D4 obstacle share this actor transform and radius;
 * decorative rocks without this actor never silently influence raft physics.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimRockObstacleActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRockObstacleActor();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Contact")
    float GetContactRadiusM() const { return ContactRadiusM; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Contact")
    float GetContactFriction() const { return FrictionCoefficient; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Contact")
    void ConfigureContact(float InRadiusM, float InFrictionCoefficient);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TObjectPtr<UStaticMeshComponent> RockMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact", meta = (ClampMin = "0.1"))
    float ContactRadiusM = 0.9f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact", meta = (ClampMin = "0.0", ClampMax = "2.0"))
    float FrictionCoefficient = 0.72f;

private:
    void RefreshVisualScale();
};
