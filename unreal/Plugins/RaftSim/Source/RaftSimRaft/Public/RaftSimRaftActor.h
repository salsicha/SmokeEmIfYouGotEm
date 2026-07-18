#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimCrewStateContracts.h"

#include "RaftSimRaftActor.generated.h"

class UStaticMeshComponent;
class USceneComponent;
class URaftSimChronoRuntimeAdapter;
class URaftSimPhysicsBridgeSubsystem;

/** Which side of the raft a paddle stroke acts on. */
UENUM(BlueprintType)
enum class ERaftSimPaddleSide : uint8
{
    Port,
    Starboard,
    Both
};

/** Capsize lifecycle of the raft. */
UENUM(BlueprintType)
enum class ERaftSimRaftMode : uint8
{
    /** Right-side up and under control. */
    Upright,
    /** Flipped by overwash/roll; crew are swimmers. */
    Capsized,
    /** Re-righted; draining retained water and reseating recovered swimmers. */
    Recovering
};

/** Guide paddle commands issued to the AI crew. */
UENUM(BlueprintType)
enum class ERaftSimCrewCommand : uint8
{
    Rest,
    AllForward,
    AllBackward,
    TurnLeft,
    TurnRight,
    Stop,
    GetDown,
    HighSide
};

/**
 * The floating raft, driven by the authoritative physics bridge (A-3): the
 * actor configures the bridge subsystem from its properties, routes paddle
 * impulses into the raft dynamics adapter, and mirrors the adapter's
 * kinematic state onto its transform. All integration happens inside
 * URaftSimChronoRuntimeAdapter::StepRaftDynamics (buoyancy support stage +
 * flexible-raft D1-D4) on the bridge's fixed 120 Hz substep.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimRaftActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRaftActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Apply one paddle stroke impulse. ForwardScale in [-1, 1]; negative = back-paddle. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void ApplyPaddleStroke(ERaftSimPaddleSide Side, float ForwardScale);

    /** Sweep/draw stroke that mostly yaws the raft. TurnScale in [-1, 1]; positive turns bow starboard. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void ApplyTurnStroke(float TurnScale);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft")
    USceneComponent* GetSternSeatAttachPoint() const { return SternSeatAttachPoint; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft")
    FVector GetRaftVelocity() const;

    // --- Flip / swim / recover loop (P2) ---------------------------------

    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft")
    ERaftSimRaftMode GetRaftMode() const { return RaftMode; }

    /** Number of crew currently in the water as swimmers. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Raft")
    int32 GetSwimmerCount() const { return Swimmers.Num(); }

    /** Guide's request to re-right a capsized raft (bound to a recovery input). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void RequestReflip();

    /**
     * Timed high-side response: shift crew weight to the given side (+1 = starboard,
     * -1 = port) to counter an incoming roll. Feeds the D2 crew action into the
     * flexible-raft model, reducing the D3 flip moment when timed into a hit.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void HandleHighSideResponse(int32 Direction);

    /**
     * Test/authoring hook: impose a strong uniform overwash surface (meters) on
     * the flexible-raft model so a flip can be provoked deterministically. Pass
     * a negative value to clear it.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void ForceOverwashForTesting(float SurfaceHeightM, FVector FlowVelocityMps);

    /** Crew size seeded as swimmers on capsize (guide + paddlers). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Raft")
    void SetCrewSize(int32 InCrewSize) { CrewSize = FMath::Clamp(InCrewSize, 0, 8); }

    /** Issue a paddle command to the crew (routed from the guide's input). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew")
    void IssueCrewCommand(ERaftSimCrewCommand Command);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew")
    ERaftSimCrewCommand GetActiveCrewCommand() const { return ActiveCrewCommand; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Raft")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Raft")
    TObjectPtr<UStaticMeshComponent> HullMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Raft")
    TObjectPtr<USceneComponent> SternSeatAttachPoint;

    /** Raft dry mass in kilograms (14 ft paddle raft + gear). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float MassKg = 220.0f;

    /** Tube radius in meters; controls buoyancy saturation depth. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float TubeRadiusM = 0.28f;

    /** Hull footprint length in meters (14 ft paddle raft). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float FootprintLengthM = 4.3f;

    /** Hull footprint width in meters. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float FootprintWidthM = 2.0f;

    /** Total buoyancy at full submersion as a multiple of weight. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float BuoyancyWeightMultiple = 2.6f;

    /** Linear drag coefficient (quadratic in speed) per submerged fraction. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float LinearDragCoefficient = 45.0f;

    /** Angular damping factor per second. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float AngularDampingPerSecond = 1.4f;

    /**
     * Vertical (heave) damping in N·s/m applied per submerged fraction.
     * ~0.5 of critical damping for the tube-buoyancy spring, so the raft
     * settles onto the waterline in a couple of oscillations.
     */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float HeaveDampingNsPerM = 1500.0f;

    /** Impulse in Newton-seconds delivered by one full paddle stroke. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float PaddleStrokeImpulseNs = 260.0f;

    /** Fixed physics substep in seconds (120 Hz), forwarded to the bridge. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float FixedSubstepSeconds = 1.0f / 120.0f;

    /** Roll angle (degrees) past which the raft is considered capsized. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float CapsizeRollDegrees = 100.0f;

    /** Seconds a negative flip margin must persist before the raft capsizes. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float CapsizeLatchSeconds = 0.35f;

    /** Reach radius (meters) within which a swimmer can be reseated. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    float SwimmerReseatReachM = 3.0f;

    /** Crew seeded as swimmers on capsize (guide + 4 paddlers by default). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Raft")
    int32 CrewSize = 5;

    /** Number of AI paddlers (guide excluded). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Crew")
    int32 PaddlerCount = 4;

    /** Crew stroke cadence in seconds. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Crew")
    float CrewStrokeIntervalSeconds = 0.8f;

    /** Crew reaction latency to a new command (seconds). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Crew")
    float CrewReactionSeconds = 0.4f;

private:
    void UpdateCapsizeLoop(float DeltaSeconds);
    void EnterCapsize();
    void DriftSwimmers(float DeltaSeconds);
    void TryReseatSwimmers();
    void UpdateCrew(float DeltaSeconds);
    void SpawnCrewVisuals();
    FVector SampleWaterVelocityMps(const FVector& WorldLocationCm) const;

    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;

    UPROPERTY()
    TObjectPtr<URaftSimChronoRuntimeAdapter> RaftAdapter;

    UPROPERTY()
    ERaftSimRaftMode RaftMode = ERaftSimRaftMode::Upright;

    /** Crew currently in the water (crew library rescue frames). */
    UPROPERTY()
    TArray<FRaftSimSwimmerRescueFrame> Swimmers;

    /** Visual spheres for in-water swimmers, parallel to Swimmers. */
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> SwimmerMeshes;

    /** Transform to respawn the raft at when recovery completes / is requested. */
    FTransform CheckpointTransform = FTransform::Identity;

    /** Raft location at the moment of capsize; re-flip rights the boat here. */
    FVector CapsizeLocation = FVector::ZeroVector;

    float FlipRiskLatchSeconds = 0.0f;
    bool bReflipRequested = false;

    // Crew state.
    UPROPERTY()
    ERaftSimCrewCommand ActiveCrewCommand = ERaftSimCrewCommand::Rest;

    UPROPERTY()
    ERaftSimCrewCommand PendingCrewCommand = ERaftSimCrewCommand::Rest;

    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> CrewMeshes;

    float CrewReactionRemaining = 0.0f;
    float CrewStrokeTimer = 0.0f;
};
