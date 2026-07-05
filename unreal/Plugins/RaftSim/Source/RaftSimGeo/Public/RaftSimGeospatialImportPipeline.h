#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimGeospatialImportPipeline.generated.h"

UENUM(BlueprintType)
enum class ERaftSimGeospatialImportCategory : uint8
{
    SourceManifest,
    VectorAnnotation,
    Raster,
    PointCloud,
    GaugeHistory,
    SolverPackage,
    UnrealCorridorExport
};

USTRUCT(BlueprintType)
struct FRaftSimGeospatialImportStage
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    FName StageId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    ERaftSimGeospatialImportCategory Category = ERaftSimGeospatialImportCategory::SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    TArray<FString> CanonicalFormats;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    TArray<FString> RequiredMetadata;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    TArray<FString> SourcePaths;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    FString UnrealConversionTarget;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    bool bRequiresCrs = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    bool bRequiresSourceManifest = true;
};

UCLASS(BlueprintType)
class RAFTSIMGEO_API URaftSimGeospatialImportPipelineConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    FString Schema = TEXT("raftsim.unreal.geospatial_import_pipeline.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    FString FormatContract = TEXT("physics/config/geospatial_format_contract.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    FString SourceManifest = TEXT("physics/data/real_world/south_fork_american_chili_bar/source_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    TArray<FRaftSimGeospatialImportStage> ImportStages;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    bool bSourceManifestRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    bool bRejectShapefileAsCanonical = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|GeoImport")
    bool bTrackTransformChanges = true;
};
