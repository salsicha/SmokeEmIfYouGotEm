#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimContactMaterials.generated.h"

UENUM(BlueprintType)
enum class ERaftSimContactSurfaceClass : uint8
{
    Rock,
    Bank,
    Ledge,
    Riverbed,
    ShallowShelf,
    Strainer
};

USTRUCT(BlueprintType)
struct FRaftSimContactMaterialPreset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    FName PresetId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    ERaftSimContactSurfaceClass SurfaceClass = ERaftSimContactSurfaceClass::Rock;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float Restitution = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float NormalStiffness = 12000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float NormalDamping = 1200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float TangentialFriction = 0.65f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float RollingFriction = 0.05f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TArray<FName> TelemetryTags;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimContactMaterialSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TArray<FRaftSimContactMaterialPreset> Presets;
};
