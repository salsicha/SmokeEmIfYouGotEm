#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimAlphaSystemsConfig.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimRaftHandlingProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName ProfileId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float MassKg = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float LengthM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float WidthM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float Stability = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float Maneuverability = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float MomentumRetention = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> ValidationFixtures;
};

USTRUCT(BlueprintType)
struct FRaftSimPassengerArchetype
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName ArchetypeId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float StartingTrust = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float StartingFear = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float StartingFatigue = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float StartingSkill = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> GameplayTraits;
};

USTRUCT(BlueprintType)
struct FRaftSimCrewProgressionRule
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName RuleId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName Trigger;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float TrustDelta = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float FearDelta = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float FatigueDelta = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    float SkillDelta = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimTrainingLesson
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName LessonId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName RiverId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> RequiredSystems;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> CompletionTelemetry;
};

USTRUCT(BlueprintType)
struct FRaftSimChallengeVariant
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName VariantId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> AllowedRivers;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> ScoringAxes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    bool bRequiresValidatedWaterAndRaftFixtures = true;
};

USTRUCT(BlueprintType)
struct FRaftSimGeneratedRapidExperiment
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FName ExperimentId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> SupportedFeatureKinds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FName> RequiredValidationReports;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    bool bPlayableUntilValidationPasses = false;
};

UCLASS(BlueprintType)
class RAFTSIMRAFT_API URaftSimAlphaSystemsConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    FString Schema = TEXT("raftsim.unreal.alpha_systems_progression.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimRaftHandlingProfile> RaftHandlingProfiles;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimPassengerArchetype> PassengerArchetypes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimCrewProgressionRule> CrewProgressionRules;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimTrainingLesson> TrainingLessons;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimChallengeVariant> ChallengeVariants;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|AlphaSystems")
    TArray<FRaftSimGeneratedRapidExperiment> GeneratedRapidExperiments;
};
