#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RaftSimCrewAvatarActor.h"

#include "RaftSimOarRig.generated.h"

class ARaftSimRaftActor;
class UMaterialInterface;
class UProceduralMeshComponent;

/** How a raft is crewed and driven. */
UENUM(BlueprintType)
enum class ERaftSimRaftRig : uint8
{
    /** Resolve from the map: oar rigs on the Colorado and Zambezi maps. */
    Auto,
    /** A guide and four paddlers on crew commands. */
    PaddleCrew,
    /** One rower on a centre-mounted oar frame (Grand Canyon expedition rig). */
    ColoradoOarRig,
    /** One rower on a centre-mounted oar frame (Zambezi day boat). */
    ZambeziOarRig
};

/** One oar's stroke state. Push drives the boat downstream (bow first);
 * pull drives it upstream (the rower's main stroke and the back-ferry). */
USTRUCT()
struct FRaftSimOarState
{
    GENERATED_BODY()

    /** 0..1 through the current stroke; meaningless while resting. */
    float Phase = 0.0f;
    /** +1 push, -1 pull, 0 resting. */
    float Direction = 0.0f;
    /** The last stroke's direction, which the oar eases to rest from. */
    float LastDirection = 1.0f;
    /** 0..1 strength of the stroke in progress. */
    float Effort = 0.0f;
    /** Rest blend: 1 fully at rest, 0 fully in a stroke. */
    float RestBlend = 1.0f;
    /** Presentation angles in degrees: sweep (blade toward the bow is
     * positive), blade drop below the oarlock, and feather (90 = flat). */
    float SweepDeg = -8.0f;
    float DropDeg = 20.0f;
    float FeatherDeg = 90.0f;
};

/**
 * A single rower's centre-mounted oar rig on the raft (docs/oar-rig-reference.md):
 * the aluminium frame, oar towers and oarlocks, the seat and foot bar,
 * the load (dry boxes, cooler, dry bags and cam straps on the Colorado), and
 * two oars that move with the strokes. Each oar stroke drives the hull
 * through its blade: a push or pull along the bow axis at the blade's
 * station abeam, so two oars together drive the boat and opposite oars
 * pivot it. The rower (the raft's guide avatar) is posed every frame with
 * both hands on the oar handles.
 */
UCLASS(ClassGroup = RaftSim)
class RAFTSIMRAFT_API URaftSimOarRigComponent : public UActorComponent
{
    GENERATED_BODY()
    friend class FRaftSimOarCommandParityTest;

public:
    URaftSimOarRigComponent();

    /** Build the rig on the raft's visual (its local frame, cm). */
    void Build(ERaftSimRaftRig InRig, UProceduralMeshComponent* RaftVisual, const FBox& HullBoundsCm);

    /** Rower's seat origin in raft-actor space: the avatar origin that puts
     * its seated pelvis (lowest contact, avatar-local) on the seat pad. */
    FVector GetRowerSeatOriginActorCm(float SeatedPelvisBottomLocalZCm) const;

    /** Load carried on a rig (frame, seat, gear), kg. */
    static float GetRigLoadKg(ERaftSimRaftRig InRig);

    /** True for the single-rower oar rigs. */
    static bool IsOarRig(ERaftSimRaftRig InRig)
    {
        return InRig == ERaftSimRaftRig::ColoradoOarRig || InRig == ERaftSimRaftRig::ZambeziOarRig;
    }

    /** Player intent for each oar, -1 pull .. +1 push. */
    void SetOarIntents(float Left, float Right);

    /** Advance strokes, drive the hull and pose the rower. */
    void TickRig(float DeltaSeconds, ARaftSimRaftActor* Raft, ARaftSimCrewAvatarActor* Rower, bool bRowerAboard);

    const FRaftSimOarState& GetOar(bool bLeft) const { return bLeft ? LeftOar : RightOar; }
    int32 GetCompletedStrokeCount() const { return CompletedStrokeCount; }
    /** Blades entering and leaving the water, per oar (audio cues). */
    int32 GetCatchCount(bool bLeft) const { return CatchCounts[bLeft ? 0 : 1]; }
    int32 GetReleaseCount(bool bLeft) const { return ReleaseCounts[bLeft ? 0 : 1]; }
    float GetLastCatchEffort(bool bLeft) const { return bLeft ? LeftOar.Effort : RightOar.Effort; }
    bool IsBuilt() const { return Frame != nullptr; }
    ERaftSimRaftRig GetRig() const { return Rig; }

    /** Pose both oars at fixed angles and the rower with them (review
     * captures; no impulses). */
    void PoseForValidation(float Phase, float LeftDirection, float RightDirection,
        ARaftSimCrewAvatarActor* Rower);

    /** Frame geometry, raft-visual local cm. An 8.5 ft oar for a 14 ft
     * boat; the inboard is a little under a third so the handle ends clear
     * each other on this narrower frame (about 19 cm apart at rest). */
    static constexpr float RailHalfWidthCm = 70.0f;
    static constexpr float TowerOffsetCm = 9.0f;
    static constexpr float TowerHeightCm = 33.0f;
    static constexpr float OarLengthCm = 260.0f;
    static constexpr float OarInboardCm = 74.0f;
    static constexpr float BladeLengthCm = 66.0f;
    static constexpr float BladeWidthCm = 17.0f;
    static constexpr float StrokeSeconds = 1.4f;

private:
    void BuildFrameAndLoad(const FBox& HullBoundsCm);
    void BuildOars();
    void UpdateOarPresentation(bool bLeft, const FRaftSimOarState& Oar);
    void PresentOar(bool bLeft, float WaterLocalZ);
    float GetFootBarLocalZ() const;
    void AdvanceOar(FRaftSimOarState& Oar, float Intent, float DeltaSeconds,
        ARaftSimRaftActor* Raft, bool bLeft, bool bDrive);
    void PoseRower(ARaftSimCrewAvatarActor* Rower, bool bApplyNow) const;
    FVector GetOarlockLocalCm(bool bLeft) const;
    FVector GetOarDirection(bool bLeft, const FRaftSimOarState& Oar) const;
    float SampleWaterLocalZ(bool bLeft, const FRaftSimOarState& Oar) const;
    float FloorAtLocalCm(float LocalX, const FBox& HullBoundsCm) const;
    UMaterialInterface* Tinted(const TCHAR* Path, const FLinearColor& Tint);

    UPROPERTY(Transient)
    TObjectPtr<UProceduralMeshComponent> Frame;

    UPROPERTY(Transient)
    TObjectPtr<UProceduralMeshComponent> LeftOarMesh;

    UPROPERTY(Transient)
    TObjectPtr<UProceduralMeshComponent> RightOarMesh;

    UPROPERTY(Transient)
    TObjectPtr<UProceduralMeshComponent> Visual;

    ERaftSimRaftRig Rig = ERaftSimRaftRig::PaddleCrew;
    FRaftSimOarState LeftOar;
    FRaftSimOarState RightOar;
    float LeftIntent = 0.0f;
    float RightIntent = 0.0f;
    float RailTopZ = 56.5f;
    float SeatTopZ = 76.5f;
    float FloorZ = 18.0f;
    float LastLeftWaterZ = 42.0f;
    float LastRightWaterZ = 42.0f;
    int32 CompletedStrokeCount = 0;
    int32 CatchCounts[2] = {0, 0};
    int32 ReleaseCounts[2] = {0, 0};
};
