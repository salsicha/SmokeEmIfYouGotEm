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
    Strainer,
    WaterFeature
};

UENUM(BlueprintType)
enum class ERaftSimContactOutcome : uint8
{
    None,
    Deflect,
    Bounce,
    Scrape,
    Ground,
    Pivot,
    Pin,
    Release,
    Surf,
    Flush,
    FlipRisk,
    Flip,
    Recovered
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
    float StickSlipVelocityMetersPerSecond = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    float ContactHysteresisMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TArray<FName> TelemetryTags;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftContactTelemetryEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FName EventId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FName RuntimeId = TEXT("CustomReducedRigidBody");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    int32 Frame = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FName ContactFamily;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    ERaftSimContactSurfaceClass SurfaceClass = ERaftSimContactSurfaceClass::Rock;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    ERaftSimContactOutcome Outcome = ERaftSimContactOutcome::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FName FeatureId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FName RaftPatchId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FVector ContactPointWorldMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    FVector ContactNormal = FVector::UpVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float PenetrationDepthMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float NormalImpulseNewtonSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float TangentImpulseNewtonSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float Restitution = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float NormalStiffness = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float NormalDamping = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float TangentialFriction = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float RollingFriction = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    bool bStickSlipActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float ContactLoadingNewtons = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float ReleaseThresholdNewtons = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float ReleaseRatio = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Contact")
    float RollMomentNewtonMeters = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftContactRuntimeSummary
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Contact")
    int32 EventCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Contact")
    int32 PinOrReleaseEventCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Contact")
    int32 SurfFlushOrFlipEventCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Contact")
    float MaxContactLoadingNewtons = 0.0f;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimContactMaterialSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TArray<FRaftSimContactMaterialPreset> Presets;
};
