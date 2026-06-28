#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimCollisionGeometryBuilder.generated.h"

UENUM(BlueprintType)
enum class ERaftSimCollisionFeatureType : uint8
{
    Rock,
    Bank,
    Ledge,
    Shallow,
    Strainer,
    Riverbed
};

UENUM(BlueprintType)
enum class ERaftSimCollisionPrimitiveType : uint8
{
    Sphere,
    Capsule,
    Box,
    ConvexHull,
    HeightFieldTile
};

USTRUCT(BlueprintType)
struct FRaftSimCollisionFeature
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    FName FeatureId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    ERaftSimCollisionFeatureType FeatureType = ERaftSimCollisionFeatureType::Rock;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    ERaftSimCollisionPrimitiveType PrimitiveType = ERaftSimCollisionPrimitiveType::Sphere;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    FVector ExtentsMeters = FVector(1.0f, 1.0f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Collision")
    FName MaterialPresetId = TEXT("rock_elastic_default");
};

USTRUCT(BlueprintType)
struct FRaftSimCollisionBuildSummary
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Collision")
    int32 TotalFeatures = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Collision")
    int32 RockLikeFeatures = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Collision")
    int32 BedLikeFeatures = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Collision")
    TArray<FName> FeatureIds;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimCollisionGeometryBuilder : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Collision")
    FRaftSimCollisionBuildSummary BuildChronoCollisionSources(const TArray<FRaftSimCollisionFeature>& OrderedFeatures) const;
};
