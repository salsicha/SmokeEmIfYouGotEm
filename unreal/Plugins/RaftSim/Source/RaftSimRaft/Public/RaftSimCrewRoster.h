#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimCrewRoster.generated.h"

/** How well a person copes in moving water once they are out of the raft. */
UENUM(BlueprintType)
enum class ERaftSimCrewSwimAbility : uint8
{
    Weak,
    Average,
    Strong
};

/**
 * One person in the raft: who they are, how they look on the river and how
 * they talk. The four paddlers keep their seats and CC0 bodies (paddler_1 ..
 * paddler_4 use Crew01 .. Crew04); the guide is the stern seat. Gear colours
 * tint the shared helmet, PFD and wetsuit materials (their BaseTint
 * parameter); accessories are small procedural props fitted to the solved
 * face and chest frames. Presentation only: masses, seats and paddling
 * cadence stay shared so the crew still paddles in time.
 */
USTRUCT(BlueprintType)
struct RAFTSIMRAFT_API FRaftSimCrewIdentity
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FName PassengerId;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FText DisplayName;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FText FirstName;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") int32 Age = 30;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FText Hometown;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FText Occupation;
    /** One line on how they behave on the water. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew") FText Personality;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor HelmetColor = FLinearColor::White;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor PfdColor = FLinearColor::Red;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor WetsuitTint = FLinearColor::Black;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor JacketColor = FLinearColor::Blue;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") bool bWearsSunglasses = false;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor EyewearFrameColor = FLinearColor::Black;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") FLinearColor LensColor = FLinearColor::Black;
    /** Clear prescription lenses rather than dark sunglasses. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") bool bClearLenses = false;
    /** Rescue whistle and river knife clipped to the PFD (the guide). */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Look") bool bRescueKit = false;

    /** 0 calm .. 1 frightened; shapes chatter and bracing. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Personality") float Nerves = 0.3f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Personality") ERaftSimCrewSwimAbility SwimAbility =
        ERaftSimCrewSwimAbility::Average;
    /** Idle gaze while seated: how far they look about (deg either side), how
     * long they hold a look (s), and how far they drop their eyes toward the
     * water ahead (deg). Paddling narrows it; bracing and swimming stop it. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Personality") float GazeRangeDeg = 18.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Personality") float GazeHoldSeconds = 3.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Personality") float GazeDownDeg = 0.0f;

    /** Chatter by situation; one is picked at random when the moment comes. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Voice") TArray<FText> BigWaterLines;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Voice") TArray<FText> CleanRunLines;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Voice") TArray<FText> OverboardLines;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Voice") TArray<FText> RescuedLines;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Crew|Voice") TArray<FText> FlipLines;
};

UCLASS()
class RAFTSIMRAFT_API URaftSimCrewRoster : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** The guide and four paddlers, guide first. */
    static const TArray<FRaftSimCrewIdentity>& GetRoster();

    /** Identity for a passenger id (paddler_1..4, guide); the guide if unknown. */
    static const FRaftSimCrewIdentity& GetIdentity(FName PassengerId);

    /** Identity for a crew avatar's appearance variant. */
    static const FRaftSimCrewIdentity& GetIdentityForVariant(int32 VariantIndex, bool bGuide);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew")
    static FText GetDisplayName(FName PassengerId);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew")
    static FText GetFirstName(FName PassengerId);
};
