#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

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

private:
    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;

    UPROPERTY()
    TObjectPtr<URaftSimChronoRuntimeAdapter> RaftAdapter;
};
