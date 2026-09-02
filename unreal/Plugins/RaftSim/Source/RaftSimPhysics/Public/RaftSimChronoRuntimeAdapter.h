#pragma once

#include "CoreMinimal.h"
#include "RaftSimFlexibleRaftModel.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimChronoRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimRaftDynamicsRuntime : uint8
{
    ProjectChrono,
    CustomReducedRigidBody,
    UnrealChaos,
    Jolt
};

USTRUCT(BlueprintType)
struct FRaftSimRaftAuthorityIntegrationPolicy
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    ERaftSimRaftDynamicsRuntime SelectedRuntime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString WaterAuthority = TEXT("custom_cxx_shallow_water_solver");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString AuthoritySelectionReport = TEXT("physics/reports/milestone19/runtime_authority_selection.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    FString AcceptedWaterReportSetLock = TEXT("physics/reports/milestone20/report_set_lock.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bCustomWaterReportLockRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bChaosMayDriveScoringCriticalPhysics = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Physics")
    bool bRenderTickMayAdvanceAuthority = false;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftBodyConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    ERaftSimRaftDynamicsRuntime Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float MassKg = 170.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    FVector InertiaTensorKgM2 = FVector(220.0f, 620.0f, 700.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float TubeRadiusMeters = 0.32f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float LengthMeters = 4.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float WidthMeters = 2.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    bool bEnableCompliantContacts = true;

    /** Total buoyancy at full tube submersion as a multiple of weight. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float BuoyancyWeightMultiple = 2.6f;

    /** Hull-water drag coefficient applied per submerged fraction. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float LinearDragCoefficient = 650.0f;

    /**
     * Reference speed used to retain viscous hull resistance near rest.
     * Above this speed the same term remains purely quadratic.
     * 1.5 welded the hull to the local streamline: with the blunt 9000
     * coefficient the lateral relative velocity decayed in ~0.1 s, so a
     * drifting raft tracked a bend's turning water to within 0.1 degree
     * and never carried to the outside of the turn (drift telemetry,
     * 2026-09-02). 0.25 overshot the other way — a free drift lagged the
     * turning water by 1-2.5 degrees even on gentle pool reaches and
     * beached itself on the outside bank within minutes ("while drifting
     * the boat moves sideways across the river and runs into the left
     * shore"). 0.55 keeps a clearly visible outside set in real bends
     * while a hands-off pool drift stays in the channel; the >=1.5 m/s
     * capture regime that keeps advected froth behind the boat is
     * numerically unchanged.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float LowSpeedDragReferenceMps = 0.35f;

    /**
     * Slow-water counterpart to LowSpeedDragReferenceMps: the effective
     * floor blends from this value in still water down to
     * LowSpeedDragReferenceMps once the sampled current reaches ~2 m/s.
     * Resolves the tension between two field reports: a soft constant
     * floor let a hands-off pool drift wander into the bank ("the boat
     * still drifts into the left riverbank"), while a stiff one welded
     * the hull to the streamline through bends ("the boat should be
     * pushed to the outside of the turn"). Slow pools now track the
     * channel; fast water frees the hull's inertia to carry outside.
     * Fixtures that pin LowSpeedDragReferenceMps at the legacy 1.5 get a
     * constant 1.5 floor (the max of both ends), preserving their
     * behaviour exactly.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float SlowWaterDragReferenceMps = 1.2f;

    /**
     * Drag coefficient for the bow-first slicing component of relative
     * flow. The blunt coefficient above must stay large so an overtaking
     * current captures the hull promptly (2026-08 requirement: advected
     * froth must never pass the boat), but applying it to forward motion
     * THROUGH the water erased paddle glide — the hull snapped back to
     * water speed the instant blades left the water. A hull slices
     * bow-first with far less resistance than it is bluntly pushed, so the
     * forward component drags at this smaller coefficient and a stroke
     * coasts down over a couple of seconds.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float ForwardSlicingDragCoefficient = 1400.0f;

    /**
     * Vertical (heave) damping in N·s/m applied per submerged fraction:
     * roughly half of critical for the tube-buoyancy spring, so the raft
     * settles onto the waterline in a couple of oscillations.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float HeaveDampingNsPerM = 1500.0f;

    /** Angular damping factor per second. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Chrono")
    float AngularDampingPerSecond = 1.4f;
};

USTRUCT(BlueprintType)
struct FRaftSimRaftKinematicState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FVector LinearVelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Chrono")
    FVector AngularVelocityRadiansPerSecond = FVector::ZeroVector;
};

// Per-substep telemetry from the quasi-static flexible-raft evaluation
// (D1-D4 port). Reference-only until the D6 promotion gate clears; the
// force/moment modifiers are applied to the adapter's kinematic state.
struct FRaftSimFlexStepTelemetry
{
    bool bEvaluated = false;
    double MaxFreeboardLossM = 0.0;
    double PortTotalFreeboardLossM = 0.0;
    double StarboardTotalFreeboardLossM = 0.0;
    double TubeRollLoadBiasNm = 0.0;
    double TubePitchLoadBiasNm = 0.0;
    double TotalRetainedWaterMassKg = 0.0;
    double RetainedWaterRollMomentNm = 0.0;
    double OvertoppingDynamicRollMomentNm = 0.0;
    double ReferenceFlipThresholdNm = 0.0;
    double ReferenceFlipMarginNm = 0.0;
    bool bReferenceFlipRisk = false;
    bool bUsedLiveWaterField = false;
    bool bUsedUniformWaterOverride = false;
    int32 LiveWaterSampleCount = 0;
    int32 LiveWetSampleCount = 0;
    int32 ContactCount = 0;
    int32 WrappingContactCount = 0;
    int32 PinnedObstacleCount = 0;
    int32 RecoveringContactCount = 0;
    double MaxIndentationM = 0.0;
    double MinReleaseMarginN = 0.0;
    FVector AppliedForceN = FVector::ZeroVector;
    FVector AppliedTorqueNm = FVector::ZeroVector;
};

// Per-segment shape state exported by the authoritative D1-D4 solve for the
// runtime inflatable mesh. Positions and deformation distances are in meters
// in raft-local space. This is presentation data derived from the same solve
// that applies forces; it is not a second visual-only contact simulation.
struct RAFTSIMPHYSICS_API FRaftSimFlexVisualSegmentState
{
    FString SegmentId;
    FVector LocalPositionM = FVector::ZeroVector;
    FVector ContactNormalLocal = FVector::ZeroVector;
    double CompressionM = 0.0;
    double FreeboardLossM = 0.0;
    double IndentationM = 0.0;
    bool bWrapping = false;
    bool bPinned = false;
    bool bRecovering = false;
};

UCLASS(BlueprintType)
class RAFTSIMPHYSICS_API URaftSimChronoRuntimeAdapter : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    void ConfigureRaftBody(const FRaftSimRaftBodyConfig& InConfig);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Chrono")
    const FRaftSimRaftBodyConfig& GetRaftBodyConfig() const { return RaftConfig; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Physics")
    void ConfigureAuthorityIntegrationPolicy(const FRaftSimRaftAuthorityIntegrationPolicy& InPolicy);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Physics")
    const FRaftSimRaftAuthorityIntegrationPolicy& GetAuthorityIntegrationPolicy() const
    {
        return AuthorityIntegrationPolicy;
    }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    void SetKinematicState(const FRaftSimRaftKinematicState& InState);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Chrono")
    const FRaftSimRaftKinematicState& GetKinematicState() const { return KinematicState; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    bool StepRaftDynamics(float SubstepSeconds);

    /**
     * Queue an external (paddle) impulse for the next substep: linear in
     * Newton-seconds (world space), angular in Newton-meter-seconds.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Chrono")
    void AddExternalImpulse(FVector LinearImpulseNs, FVector AngularImpulseNms);

    /**
     * Bind the water-surface probe the buoyancy support stage samples:
     * given a world position in centimeters, writes the wet surface height in
     * centimeters and returns true, or returns false where the water is dry.
     * With a sampler bound, the CustomReducedRigidBody quasi-static step
     * integrates gravity, multi-point tube buoyancy, drag, and heave damping
     * in addition to the D1-D4 modifiers.
     */
    void SetWaterSurfaceSampler(
        TFunction<bool(const FVector& WorldPositionCm, float& OutWaterSurfaceZCm)> InSampler);

    /** Tube support points whose water cell sampled dry on the last support
     * pass — the direct instrument for fall-through-the-wet-mask sinks. */
    int32 GetLastDrySupportPointCount() const { return LastDrySupportPointCount; }

    /**
     * Bind the authoritative terrain height sampled below each tube point.
     * The selected reduced runtime resolves the contact; the callback only
     * supplies world-space ground height and normal from Landscape or the
     * solver bed. This keeps visual/query collision from becoming a second
     * rigid-body authority.
     */
    void SetGroundSurfaceSampler(
        TFunction<bool(
            const FVector& WorldPositionCm,
            float& OutGroundZCm,
            FVector& OutGroundNormal)> InSampler);

    int32 GetLastGroundedSupportPointCount() const
    {
        return LastGroundedSupportPointCount;
    }

    float GetLastMaximumGroundPenetrationMeters() const
    {
        return LastMaximumGroundPenetrationM;
    }

    /**
     * Bind full live-water samples for D3. The adapter evaluates this at each
     * deformed tube segment in world centimetres and passes the resulting
     * surface/velocity field into the authoritative overwash solve.
     */
    void SetFlexibleWaterFieldSampler(
        TFunction<bool(
            const FVector& WorldPositionCm,
            FRaftSimFlexUniformWater& OutWater)> InSampler);

    // --- Flexible-raft model (D1-D4 port; CustomReducedRigidBody path) ------

    // Stand up the quasi-static flexible model behind the adapter. Seats may be
    // empty (no crew loads). The tube layout is rebuilt from the parameters.
    void ConfigureFlexibleRaftModel(
        const FRaftSimFlexParameters& InParameters,
        const TArray<FRaftSimFlexCrewSeat>& InSeats,
        double NominalPressurePa = 18000.0);

    void SetFlexibleCrewActions(const TArray<FRaftSimFlexCrewAction>& InActions);

    // Deterministic uniform D3 override used by fixtures/tests. When disabled,
    // the live per-segment sampler drives D3 and missing/dry samples drain.
    void SetFlexibleUniformWater(const FRaftSimFlexUniformWater& InWater, bool bInEnabled);

    /**
     * Switch the flexible solve between crewed-upright and empty-capsized
     * loading. Capsizing ejects crew and drains open-floor overwash, while D4
     * rock contact and indentation memory remain authoritative.
     */
    void SetFlexibleCapsized(bool bInCapsized);

    bool IsFlexibleCapsized() const { return bFlexCapsized; }

    void SetFlexibleRockObstacles(const TArray<FRaftSimFlexRockObstacle>& InObstacles);

    /** Persistent damage modifiers from the shipping raft-condition model. */
    void SetFlexibleConditionModifiers(float PressureFraction, float FabricIntegrity);

    float GetFlexiblePressureFraction() const { return FlexPressureFraction; }
    float GetFlexibleFabricIntegrity() const { return FlexFabricIntegrity; }

    // Clear retained-water and indentation memory (deterministic restart).
    void ResetFlexiblePersistentState();

    bool IsFlexibleModelConfigured() const { return FlexLayout.Num() > 0; }

    const FRaftSimFlexStepTelemetry& GetLastFlexibleStepTelemetry() const
    {
        return LastFlexStepTelemetry;
    }

    const TMap<FString, double>& GetFlexibleRetainedVolumeBySegment() const
    {
        return RetainedVolumeBySegment;
    }

    const TMap<FString, double>& GetFlexibleIndentationBySegment() const
    {
        return IndentationBySegment;
    }

    const TArray<FRaftSimFlexVisualSegmentState>& GetFlexibleVisualSegments() const
    {
        return LastFlexVisualSegments;
    }

private:
    UPROPERTY()
    FRaftSimRaftBodyConfig RaftConfig;

    UPROPERTY()
    FRaftSimRaftAuthorityIntegrationPolicy AuthorityIntegrationPolicy;

    UPROPERTY()
    FRaftSimRaftKinematicState KinematicState;

    // Buoyancy support stage (plain C++ members; deterministic).
    TFunction<bool(const FVector& WorldPositionCm, float& OutWaterSurfaceZCm)> WaterSurfaceSampler;
    int32 LastDrySupportPointCount = 0;
    float LastWetSupportSurfaceZCm = 0.0f;
    bool bHasLastWetSupportSurface = false;
    FVector LastWetWaterVelocityMps = FVector::ZeroVector;
    TFunction<bool(
        const FVector& WorldPositionCm,
        float& OutGroundZCm,
        FVector& OutGroundNormal)> GroundSurfaceSampler;
    int32 LastGroundedSupportPointCount = 0;
    float LastMaximumGroundPenetrationM = 0.0f;
    TFunction<bool(
        const FVector& WorldPositionCm,
        FRaftSimFlexUniformWater& OutWater)> FlexibleWaterFieldSampler;
    TArray<FVector> TubeSamplePointsM;
    float FlexPressureFraction = 1.0f;
    float FlexFabricIntegrity = 1.0f;
    FVector PendingLinearImpulseNs = FVector::ZeroVector;
    FVector PendingAngularImpulseNms = FVector::ZeroVector;

    // Flexible-raft model state (plain C++ members; deterministic).
    FRaftSimFlexParameters FlexParameters;
    TArray<FRaftSimFlexTubeSegment> FlexLayout;
    TArray<FRaftSimFlexCrewSeat> FlexSeats;
    TArray<FRaftSimFlexCrewSeat> FlexCapsizedSeats;
    TArray<FRaftSimFlexCrewAction> FlexActions;
    TArray<FRaftSimFlexRockObstacle> FlexObstacles;
    FRaftSimFlexUniformWater FlexWater;
    bool bFlexUniformWaterOverrideEnabled = false;
    bool bFlexCapsized = false;
    // Reused at the 120 Hz physics rate. Keeping this allocation resident
    // avoids per-substep map churn while preserving SegmentId-keyed D3 input.
    TMap<FString, FRaftSimFlexUniformWater> LiveWaterBySegmentScratch;
    TMap<FString, double> RetainedVolumeBySegment;
    TMap<FString, double> IndentationBySegment;
    FRaftSimFlexStepTelemetry LastFlexStepTelemetry;
    TArray<FRaftSimFlexVisualSegmentState> LastFlexVisualSegments;

    bool StepFlexibleRaftDynamics(double SubstepSeconds);
};
