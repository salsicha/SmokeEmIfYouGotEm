#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "RaftSimGroundSourceLibrary.generated.h"

class UStaticMesh;

UCLASS()
class RAFTSIMPHYSICS_API URaftSimGroundSourceLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Same collision-provider API used by the ground sweep, including in cooked
    // builds. Does not change assets, collision settings or a running world.
    UFUNCTION(BlueprintCallable,Category="RaftSim|Validation")
    static FString AuditCollisionSource(UStaticMesh* Mesh);
};
