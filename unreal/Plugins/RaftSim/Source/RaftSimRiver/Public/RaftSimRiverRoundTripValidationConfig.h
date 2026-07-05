#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimRiverRoundTripValidationConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRiverRoundTripTargetKind : uint8
{
    SolverPackages,
    GeoClawCppComparisonInputs,
    FidelityReviewOverlays
};

USTRUCT(BlueprintType)
struct FRaftSimRiverRoundTripOverlay
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FName OverlayId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FName SolverMode;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Manifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Fields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Probes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString ConservationSummary;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverRoundTripMetadataGuards
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FName> Crs;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FName> Provenance;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FName> FlowResponseMetadata;
};

USTRUCT(BlueprintType)
struct FRaftSimRiverRoundTripCase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FName CaseId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> SourceUnrealAssets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> SourceManifests;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> SolverPackages;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> GeoClawCppComparisonInputs;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FRaftSimRiverRoundTripOverlay> FidelityReviewOverlays;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FRaftSimRiverRoundTripMetadataGuards MetadataGuards;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FName> LossChecks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Status;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimRiverRoundTripValidationConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString Schema = TEXT("raftsim.unreal.river_round_trip_validation.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString CanonicalFormatContract = TEXT("physics/config/geospatial_format_contract.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    FString GeospatialImportPipeline = TEXT("unreal/Content/RaftSim/River/geospatial_import_pipeline.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<ERaftSimRiverRoundTripTargetKind> RequiredTargetKinds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> SourceUnrealAssets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FString> RegenerationSteps;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    TArray<FRaftSimRiverRoundTripCase> RoundTripCases;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    bool bRequireCrsPreservation = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    bool bRequireProvenancePreservation = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    bool bRequireFlowResponseMetadataPreservation = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|RoundTrip")
    bool bRejectIsolatedReachLocalSignoff = true;
};
