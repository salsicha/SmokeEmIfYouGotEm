#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "UObject/Object.h"

#include "RaftSimWaterDebugViews.generated.h"

UENUM(BlueprintType)
enum class ERaftSimWaterDebugView : uint8
{
    Depth,
    Velocity,
    Froude,
    WetDryMask,
    FeatureTags,
    ConservationDeltas,
    RaftTrajectory,
    ContactProbes,
    RuntimeBudgets
};

USTRUCT(BlueprintType)
struct FRaftSimWaterDebugViewDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    ERaftSimWaterDebugView View = ERaftSimWaterDebugView::Depth;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    FName ViewId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    FString RenderMode;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    TArray<FName> TelemetryFields;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    bool bDefaultEnabled = false;
};

UCLASS(BlueprintType)
class RAFTSIMDEBUG_API URaftSimWaterDebugViewSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Debug/live_water_debug_views.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Debug")
    TArray<FRaftSimWaterDebugViewDefinition> Views;
};

UCLASS(BlueprintType)
class RAFTSIMDEBUG_API URaftSimWaterDebugViewModel : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Debug")
    void Configure(URaftSimWaterDebugViewSet* InViewSet);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Debug")
    void SetViewEnabled(ERaftSimWaterDebugView View, bool bEnabled);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Debug")
    bool IsViewEnabled(ERaftSimWaterDebugView View) const;

private:
    UPROPERTY()
    TObjectPtr<URaftSimWaterDebugViewSet> ViewSet;

    UPROPERTY()
    TMap<ERaftSimWaterDebugView, bool> EnabledViews;
};
