#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimVerticalSliceEnvironmentConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimEnvironmentLayerKind : uint8
{
    Landscape,
    RiverBanks,
    RocksAndBoulders,
    Foliage,
    DriftwoodAndDebris,
    AccessAndHumanContext,
    LightingAndWeather,
    AudioOcclusionGeometry,
    WaterReadabilitySupport
};

USTRUCT(BlueprintType)
struct FRaftSimEnvironmentLayerRecipe
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FName LayerId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    ERaftSimEnvironmentLayerKind LayerKind = ERaftSimEnvironmentLayerKind::Landscape;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    TArray<FString> TargetSystems;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    TArray<FName> RequiredMasks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    float TargetDensity = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bPhotorealReferenceRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bProtectWaterReadability = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRightsProvenanceRequired = true;
};

USTRUCT(BlueprintType)
struct FRaftSimEnvironmentQualityBudget
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FName TargetPlatform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    int32 TargetFrameRate = 60;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    float MaxVisibleFoliageInstances = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    float MaxVisibleNaniteTrianglesMillions = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    float MaxGpuFrameMilliseconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRequiresGuideSeatCapture = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimVerticalSliceEnvironmentConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString Schema = TEXT("raftsim.unreal.vertical_slice_environment.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString Map = TEXT("/Game/RaftSim/Maps/L_RaftSimBoot");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString CorridorPackage = TEXT("physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString PhotorealStackManifest = TEXT("unreal/Content/RaftSim/Rendering/photoreal_stack.manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    FString PresentationCueManifest = TEXT("unreal/Content/RaftSim/Rendering/telemetry_presentation_cues.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    TArray<FRaftSimEnvironmentLayerRecipe> Layers;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    TArray<FRaftSimEnvironmentQualityBudget> QualityBudgets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRequirePhotorealReferenceBoard = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRequireDenseRiverbankFoliagePass = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRequireGuideSeatReadabilityCapture = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bRequirePerformanceCapture = true;
};
