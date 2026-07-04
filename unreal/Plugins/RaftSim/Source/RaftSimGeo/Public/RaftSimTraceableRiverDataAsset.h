#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimTraceableRiverDataAsset.generated.h"

UENUM(BlueprintType)
enum class ERaftSimTraceableRiverDataKind : uint8
{
    SolverNeutralScenarioCollection,
    ReachLocalGridWithStitchedValidation,
    GeospatialSourceManifest,
    UnrealCorridorPackage
};

USTRUCT(BlueprintType)
struct FRaftSimTraceableSourcePath
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    FString SourcePath;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    FString SchemaVersion;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    bool bRequired = true;
};

UCLASS(BlueprintType)
class RAFTSIMGEO_API URaftSimTraceableRiverDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    FName AssetId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    ERaftSimTraceableRiverDataKind Kind = ERaftSimTraceableRiverDataKind::SolverNeutralScenarioCollection;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    FString AcceptedReportSetLockPath = TEXT("physics/reports/milestone20/report_set_lock.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    FString AcceptedReportSetLockHash;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    TArray<FRaftSimTraceableSourcePath> SourcePaths;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    bool bRequiresStitchedWholeWindowValidation = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Traceability")
    bool bPreserveSourceProvenance = true;
};
