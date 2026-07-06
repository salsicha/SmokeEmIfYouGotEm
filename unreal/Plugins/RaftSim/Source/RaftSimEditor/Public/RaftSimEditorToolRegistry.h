#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimEditorToolRegistry.generated.h"

UENUM(BlueprintType)
enum class ERaftSimEditorToolKind : uint8
{
    ReplayDebugViewer,
    RapidRiverEditor,
    FeatureTuningEditor,
    GeospatialValidator,
    VerticalSliceLauncher
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimEditorToolDescriptor
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FName ToolId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    ERaftSimEditorToolKind ToolKind = ERaftSimEditorToolKind::ReplayDebugViewer;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FText Description;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FString SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FString RequiredModule;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    bool bRequiresValidationBeforeExport = true;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimEditorToolRegistry : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FString Schema = TEXT("raftsim.unreal.polished_tool_registry.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Tools/polished_tool_registry.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|EditorTools")
    TArray<FRaftSimEditorToolDescriptor> Tools;
};

namespace RaftSimEditorTools
{
    static constexpr const TCHAR* ToolRegistryManifestPath =
        TEXT("unreal/Content/RaftSim/Tools/polished_tool_registry.json");
}
