#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimEncounterVolume.generated.h"

class UBoxComponent;

/** What a rapid-encounter volume represents (release-1.0-plan.md A-6). */
UENUM(BlueprintType)
enum class ERaftSimEncounterKind : uint8
{
    /** Eddy above the rapid: run start line + checkpoint respawn. */
    ScoutEddy,
    /** A cataloged hole/hazard: overlapping it off-line is a safety incident. */
    Hazard,
    /** The clean-line corridor: staying inside preserves the clean-line ratio. */
    Line,
    /** End of the rapid: crossing finishes the run. */
    Finish
};

/** A trigger box marking a feature of a named-rapid encounter. */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimEncounterVolume : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimEncounterVolume();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Encounter")
    ERaftSimEncounterKind Kind = ERaftSimEncounterKind::Hazard;

    /** Catalog sub-feature id this volume represents (e.g. "the_gut"). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Encounter")
    FName FeatureId;

    UBoxComponent* GetTrigger() const { return Trigger; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Encounter")
    TObjectPtr<UBoxComponent> Trigger;
};
