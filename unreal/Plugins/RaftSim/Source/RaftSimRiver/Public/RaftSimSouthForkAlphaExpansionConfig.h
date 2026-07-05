#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimSouthForkAlphaExpansionConfig.generated.h"

UENUM(BlueprintType)
enum class ERaftSimSouthForkContentNodeKind : uint8
{
    ScoutEddy,
    Rapid,
    RecoveryPool,
    Access,
    DebriefPool
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkLinkedContentNode
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName NodeId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName RapidId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    ERaftSimSouthForkContentNodeKind NodeKind = ERaftSimSouthForkContentNodeKind::Rapid;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FVector2D StationSpanM = FVector2D::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> UpstreamNodeIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> DownstreamNodeIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> GameplayRoles;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> GuideFidelityNoteIds;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkSeasonalFlowVariant
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName FlowVariantId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName SeasonId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    float DischargeCfs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> ExpectedFeatureChanges;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    bool bRequiresValidationBeforePlayable = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkDifficultyPreset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName DifficultyId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> EnabledContentNodeIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FName> CrewAndRescueModifiers;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    bool bRequiresGuideReview = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSouthForkGuideFidelityNote
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName NoteId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FName AppliesToNodeId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FString> RequiredEvidence;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    bool bRightsClearedMediaRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    bool bHumanGuideSignoffRequired = true;
};

UCLASS(BlueprintType)
class RAFTSIMRIVER_API URaftSimSouthForkAlphaExpansionConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FString Schema = TEXT("raftsim.unreal.south_fork_alpha_content_expansion.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FString EditorPass = TEXT("unreal/Content/RaftSim/River/south_fork_first_river_editor_pass.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    FString RapidRiverEditor = TEXT("unreal/Content/RaftSim/River/rapid_river_editor.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FRaftSimSouthForkLinkedContentNode> LinkedContentNodes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FRaftSimSouthForkSeasonalFlowVariant> SeasonalFlowVariants;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FRaftSimSouthForkDifficultyPreset> DifficultyPresets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SouthForkAlpha")
    TArray<FRaftSimSouthForkGuideFidelityNote> GuideFidelityNotes;
};
