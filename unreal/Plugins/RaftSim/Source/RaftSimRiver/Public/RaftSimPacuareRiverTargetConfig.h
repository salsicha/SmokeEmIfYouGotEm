#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimPacuareRiverTargetConfig.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimPacuareRainFedFlowBand
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName FlowBand;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString RelativeFlow;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString ExpectedGameplayBehavior;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    bool bRequiresHydrologyReview = true;
};

USTRUCT(BlueprintType)
struct FRaftSimPacuareFidelityNeed
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName NeedId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName NeedKind;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString FidelityGoal;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FString> RequiredSources;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString ReviewStatus;
};

USTRUCT(BlueprintType)
struct FRaftSimPacuareGuideAnnotationNeed
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName AnnotationId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName GeometryKind;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FString> RequiredSources;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FName> ReviewFields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    bool bBlocksSolverGeneration = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimPacuareRiverTargetConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString Schema = TEXT("raftsim.unreal.pacuare_river_target.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString SourceManifest = TEXT("physics/data/real_world/pacuare_river_costa_rica/source_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString FlowPresets = TEXT("physics/data/real_world/pacuare_river_costa_rica/flow_presets.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName RiverId = TEXT("pacuare");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FName SectionId = TEXT("lower_pacuare_planning_corridor");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString SectionName = TEXT("Lower Pacuare Planning Corridor");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    FString RouteStyle = TEXT("guided_paddle_raft");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FRaftSimPacuareRainFedFlowBand> RainFedFlowBands;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FRaftSimPacuareFidelityNeed> RainforestGorgeFidelityNeeds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    TArray<FRaftSimPacuareGuideAnnotationNeed> GuideAnnotationNeeds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    bool bHydrologyGaugeSourceReviewRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    bool bProtectedAreaSourceRightsReviewRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Pacuare")
    bool bRightsClearedGuideAndFieldMediaRequired = true;
};
