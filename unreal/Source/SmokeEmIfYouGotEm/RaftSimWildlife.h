#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimWildlifeCalls.h"

#include "RaftSimWildlife.generated.h"

class ARaftSimRaftActor;
class UAudioComponent;
class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UProceduralMeshComponent;
class URaftSimCallSoundWave;
class URaftSimPhysicsBridgeSubsystem;

/** Animals along the rivers (docs/river-wildlife-reference.md). */
UENUM(BlueprintType)
enum class ERaftSimWildlifeSpecies : uint8
{
    BaldEagle,
    Osprey,
    TurkeyVulture,
    CaliforniaCondor,
    AndeanCondor,
    AfricanFishEagle,
    VerreauxsEagle,
    CommonRaven,
    GreatBlueHeron,
    CommonMerganser,
    TorrentDuck,
    HarlequinDuck,
    MantledHowler,
    KeelBilledToucan,
    MontezumaOropendola,
    DesertBighorn,
    BlackTailedDeer,
    GrizzlyBear,
    ChacmaBaboon,
    Hippopotamus,
    NileCrocodile,
    SockeyeSalmon,
    AustralParakeet,
    TrumpeterHornbill,
    Sunbittern,
    FasciatedTigerHeron,
    BlackFacedIbis,
    SouthernLapwing,
    RockPratincole,
    // Heard, not seen.
    CanyonWren,
    AmericanDipper,
    Chucao,
    Cicadas,
    RedShoulderedHawk,
    AcornWoodpecker,
    RingedKingfisher,
    BeltedKingfisher,
    RedWingedStarling
};

/** Where on the river an animal lives. */
enum class ERaftSimWildlifeHabitat : uint8
{
    Sky,
    Canopy,
    Bank,
    Cliff,
    Pool,
    Rapid,
    Shore,
    /** On a rock standing out of the river (the rapids' boulders). */
    Rock,
    Voice
};

/** How an animal is built and moves. */
enum class ERaftSimWildlifeBody : uint8
{
    Soarer,
    Flapper,
    Heron,
    Duck,
    Monkey,
    PerchedBird,
    Quadruped,
    Hippo,
    Crocodile,
    Fish,
    None
};

struct FRaftSimWildlifeSpeciesInfo
{
    ERaftSimWildlifeSpecies Species = ERaftSimWildlifeSpecies::BaldEagle;
    ERaftSimWildlifeHabitat Habitat = ERaftSimWildlifeHabitat::Sky;
    ERaftSimWildlifeBody Body = ERaftSimWildlifeBody::Soarer;
    ERaftSimWildlifeCall Call = ERaftSimWildlifeCall::None;
    /** Wingspan for birds, body length for everything else, metres. */
    float SizeMeters = 2.0f;
    /** Colours: main body, head/neck, wings/limbs, accents (tail, bill, markings). */
    FLinearColor Body0 = FLinearColor(0.1f, 0.07f, 0.04f);
    FLinearColor Head = FLinearColor(0.1f, 0.07f, 0.04f);
    FLinearColor Limbs = FLinearColor(0.1f, 0.07f, 0.04f);
    FLinearColor Accent = FLinearColor(0.5f, 0.4f, 0.1f);
    /** Underside (seen from below on birds overhead). */
    FLinearColor Under = FLinearColor(0.1f, 0.07f, 0.04f);
    FLinearColor Tail = FLinearColor(0.1f, 0.07f, 0.04f);
    /** Wing dihedral when soaring, degrees (vultures hold a strong V). */
    float DihedralDeg = 4.0f;
    /** How many are about at once near the boat, and group size. */
    int32 MaxNearby = 1;
    int32 GroupMin = 1;
    int32 GroupMax = 1;
    /** Height above the water, metres (sky and canopy). */
    float AltitudeMin = 30.0f;
    float AltitudeMax = 90.0f;
    /** Chance a sighting is offered when one is due (rare animals low). */
    float SpawnChance = 0.7f;
    /** A mother with her young: the group after the first are ducklings. */
    bool bBrood = false;
};

/** The species table for one river (map). Empty off the river maps. */
SMOKEEMIFYOUGOTEM_API TArray<FRaftSimWildlifeSpeciesInfo> GetRiverWildlife(const FString& MapName);
SMOKEEMIFYOUGOTEM_API FRaftSimWildlifeSpeciesInfo GetWildlifeSpeciesInfo(ERaftSimWildlifeSpecies Species);

/**
 * One animal: a low-poly body built from shaded primitives (body, head,
 * wings or limbs, tail), animated procedurally for its kind (soaring
 * circles and flaps, wading, swimming, walking, surfacing), calling with
 * its synthesized voice from where it is.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimWildlifeCreature : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimWildlifeCreature();

    virtual void Tick(float DeltaSeconds) override;

    /** Build the animal at its spot. WaterZ is the water surface (cm) near it. */
    void Configure(ERaftSimWildlifeSpecies InSpecies, const FVector& HomeCm, const FVector& RiverDirection,
        float WaterZCm, uint32 Seed, const FVector& Facing);

    /** Validation: build the animal and pose it (no simulation, no calls). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Wildlife")
    void ConfigureForReview(ERaftSimWildlifeSpecies InSpecies, FVector HomeCm, float WaterZCm, float AnimationTime);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Wildlife")
    void CallNow();

    ERaftSimWildlifeSpecies GetSpecies() const { return Species; }
    int32 GetCallCount() const { return CallCount; }
    /** The raft drew close; flighty animals react. */
    void NotifyRaftDistance(float DistanceMeters, const FVector& RaftLocationCm);
    bool WantsRemoval() const { return bWantsRemoval; }

private:
    UProceduralMeshComponent* AddPart(const TCHAR* Name, USceneComponent* Parent, const FVector& OffsetCm);
    void BuildBody();
    void Animate(float Time, float DeltaSeconds);
    UMaterialInterface* Tint(const FLinearColor& Color, bool bGlossy = false);
    float SampleWaterZ(const FVector& WorldCm, bool* bOutWet = nullptr) const;

    UPROPERTY()
    TObjectPtr<USceneComponent> Root;
    UPROPERTY()
    TObjectPtr<USceneComponent> Pivot;
    UPROPERTY()
    TObjectPtr<UProceduralMeshComponent> BodyPart;
    UPROPERTY()
    TObjectPtr<UProceduralMeshComponent> HeadPart;
    UPROPERTY()
    TObjectPtr<UProceduralMeshComponent> JawPart;
    UPROPERTY()
    TObjectPtr<UProceduralMeshComponent> TailPart;
    UPROPERTY()
    TArray<TObjectPtr<UProceduralMeshComponent>> WingParts;
    UPROPERTY()
    TArray<TObjectPtr<UProceduralMeshComponent>> LegParts;
    UPROPERTY()
    TObjectPtr<UAudioComponent> Voice;
    UPROPERTY()
    TObjectPtr<URaftSimCallSoundWave> VoiceWave;
    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;

    ERaftSimWildlifeSpecies Species = ERaftSimWildlifeSpecies::BaldEagle;
    FRaftSimWildlifeSpeciesInfo Info;
    FRandomStream Random;
    FVector Home = FVector::ZeroVector;
    FVector River = FVector::ForwardVector;
    float WaterZ = 0.0f;
    float Time = 0.0f;
    float NextCall = 10.0f;
    int32 CallCount = 0;
    // Soaring: the circle and its drift.
    float CircleRadius = 4000.0f;
    float CircleAngle = 0.0f;
    float CircleDirection = 1.0f;
    float Altitude = 5000.0f;
    float FlapUntil = 0.0f;
    float NextFlap = 5.0f;
    float Lifetime = 120.0f;
    // Flushed or diving animals.
    bool bFlying = false;
    bool bSubmerged = false;
    float StateUntil = 0.0f;
    FVector Velocity = FVector::ZeroVector;
    float Heading = 0.0f;
    bool bWantsRemoval = false;
    bool bReview = false;
};

/**
 * Keeps each river's wildlife about the raft: eagles over the South Fork,
 * condors in Grand Canyon, howler monkeys and toucans on the Pacuare, hippos
 * and crocodiles on the Zambezi, and so on. Animals appear ahead in their
 * habitat (sky over the river, trees on the bank, cliffs, calm pools,
 * rapids), live their lives, call, and are removed once far behind.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimWildlifeDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimWildlifeDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    int32 GetLiveCreatureCount() const { return Creatures.Num(); }

    /** Review: after DelaySeconds, bring out every species of this river near
     * the raft and photograph each from close by (Saved/Screenshots). */
    void StartShowcase(const FString& Label, float DelaySeconds, bool bExitWhenDone);
    int32 GetSpawnedCount() const { return SpawnedCount; }
    const TArray<FRaftSimWildlifeSpeciesInfo>& GetSpeciesTable() const { return Table; }

private:
    bool TrySpawn(const FRaftSimWildlifeSpeciesInfo& Entry);
    bool FindPlacement(const FRaftSimWildlifeSpeciesInfo& Entry, FVector& OutCm, float& OutWaterZ);
    bool FindWaterEdge(const FVector& FromCm, const FVector& Lateral, FVector& OutEdgeCm, float& OutWaterZ) const;
    bool TraceGround(const FVector& AtCm, float& OutZ) const;
    bool FindTreeTop(const FVector& NearCm, float Radius, FVector& OutCm) const;
    bool FindRockTop(const FVector& NearCm, float Radius, float WaterZ, FVector& OutCm);
    bool SampleWater(const FVector& AtCm, float& OutZ, float& OutSpeed, float& OutDepth, FVector& OutVelocity) const;
    void TickShowcase(float DeltaSeconds);

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;
    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;
    UPROPERTY()
    TArray<TObjectPtr<ARaftSimWildlifeCreature>> Creatures;

    TArray<FRaftSimWildlifeSpeciesInfo> Table;
    TArray<TWeakObjectPtr<UInstancedStaticMeshComponent>> Trees;
    TArray<TWeakObjectPtr<AActor>> Rocks;
    bool bRocksGathered = false;
    FRandomStream Random;
    FVector LastFacing = FVector::ZeroVector;
    float SpawnSeconds = 1.0f;
    int32 NextEntry = 0;
    int32 SpawnedCount = 0;
    bool bTreesGathered = false;
    // Showcase review state.
    bool bShowcase = false;
    bool bShowcaseSpawned = false;
    bool bShowcaseExit = false;
    FString ShowcaseLabel;
    float ShowcaseTimer = 0.0f;
    int32 ShowcaseIndex = 0;
    bool bShowcaseFramed = false;
    TArray<TWeakObjectPtr<ARaftSimWildlifeCreature>> ShowcaseSubjects;
    TWeakObjectPtr<class ACameraActor> ShowcaseCamera;
};
