// Flexible-raft quasi-static reference models D1-D4, ported from the Python
// reference stack (physics/src/raftsim/flexible_raft_d1..d4.py) for the A-3
// engine port (docs/release-1.0-plan.md section 5 A-3 / section 7 P2).
//
// The math mirrors the Python functions' inputs, outputs, and clamp constants
// exactly. Deterministic, double precision, no RNG. Evaluation order matters:
// nearest-segment selection is first-wins on exact ties, matching Python min().

#pragma once

#include "CoreMinimal.h"

// Raft parameters mirrored from RaftParameters2_5D (scenario2_5d.py).
struct RAFTSIMPHYSICS_API FRaftSimFlexParameters
{
    double MassKg = 420.0;
    double LengthM = 4.3;
    double WidthM = 1.9;
    double TubeRadiusM = 0.28;
    double GuideMassKg = 85.0;
    double PassengerMassKg = 75.0;
    int32 PassengerCount = 6;

    double TotalMassKg() const
    {
        return MassKg + GuideMassKg + PassengerMassKg * static_cast<double>(PassengerCount);
    }
};

// Rigid 6-DoF raft state mirrored from RaftState6DoF (raft_coupling2_5d.py).
// Positions in meters, velocities in m/s, angular velocity in rad/s.
struct RAFTSIMPHYSICS_API FRaftSimFlexRigidState
{
    FVector Position = FVector::ZeroVector;
    FQuat Orientation = FQuat::Identity;
    FVector LinearVelocity = FVector::ZeroVector;
    FVector AngularVelocity = FVector::ZeroVector;

    FVector WorldPoint(const FVector& LocalPoint) const
    {
        return Position + Orientation.RotateVector(LocalPoint);
    }

    FVector PointVelocity(const FVector& LocalPoint) const
    {
        const FVector WorldOffset = Orientation.RotateVector(LocalPoint);
        return LinearVelocity + FVector::CrossProduct(AngularVelocity, WorldOffset);
    }
};

// --- D1: pressure/volume-compliant perimeter tube ---------------------------

struct RAFTSIMPHYSICS_API FRaftSimFlexTubeSegment
{
    FString SegmentId;
    FVector LocalPosition = FVector::ZeroVector;
    FVector OutwardNormal = FVector(1.0, 0.0, 0.0);
    double TributaryLengthM = 1.0;
    double RestVolumeM3 = 0.1;
    double ContactAreaM2 = 0.1;
    double NominalPressurePa = 18000.0;
    double ComplianceM3PerPa = 3.0e-8;
    double FloorCouplingFraction = 0.16;
    double LacingCouplingFraction = 0.12;
    double FrameCouplingFraction = 0.07;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexTubeLoad
{
    FString LoadId;
    FVector LocalPosition = FVector::ZeroVector;
    double ForceN = 0.0;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexSegmentResponse
{
    FString SegmentId;
    FVector LocalPosition = FVector::ZeroVector;
    double DirectLoadN = 0.0;
    double ReceivedLacingLoadN = 0.0;
    double FloorLoadN = 0.0;
    double FrameLoadN = 0.0;
    double EffectiveLoadN = 0.0;
    double PressurePa = 0.0;
    double PressureDeltaPa = 0.0;
    double VolumeM3 = 0.0;
    double VolumeLossM3 = 0.0;
    double CompressionM = 0.0;
    double FreeboardLossM = 0.0;
    bool bBounded = false;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexTubeSolve
{
    TArray<FRaftSimFlexSegmentResponse> SegmentResponses;
    double TotalAppliedLoadN = 0.0;
    double TotalEffectiveTubeLoadN = 0.0;
    double TotalVolumeLossM3 = 0.0;
    double MaxFreeboardLossM = 0.0;
    double MaxPressureDeltaPa = 0.0;
    double RollLoadBiasNm = 0.0;
    double PitchLoadBiasNm = 0.0;
    int32 BoundedSegmentCount = 0;
};

// --- Crew (evaluate_crew_weight_distribution2_5d subset used by D2-D4) ------

struct RAFTSIMPHYSICS_API FRaftSimFlexCrewSeat
{
    FString SeatId;
    FVector LocalPosition = FVector::ZeroVector;
    double OccupantMassKg = 0.0;
    bool bOccupied = true;
    FString Role = TEXT("passenger");
};

struct RAFTSIMPHYSICS_API FRaftSimFlexCrewAction
{
    FString SeatId;
    FVector LeanOffset = FVector::ZeroVector;
    int32 HighSideDirection = 0;
    bool bBrace = false;
    bool bRecovery = false;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexSeatTelemetry
{
    FString SeatId;
    FString Role;
    bool bOccupied = false;
    double MassKg = 0.0;
    FVector BaseLocalPosition = FVector::ZeroVector;
    FVector ActionOffset = FVector::ZeroVector;
    FVector EffectiveLocalPosition = FVector::ZeroVector;
    int32 HighSideDirection = 0;
    bool bBrace = false;
    bool bRecovery = false;
    bool bLeanWasClamped = false;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexRecoveryThresholds
{
    double PinThresholdN = 3200.0;
    double FlipThresholdNm = 1800.0;
    double ReleaseThresholdN = 2600.0;
    double PinThresholdMultiplier = 1.0;
    double FlipThresholdMultiplier = 1.0;
    double ReleaseThresholdMultiplier = 1.0;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexCrewTelemetry
{
    TArray<FRaftSimFlexSeatTelemetry> SeatTelemetry;
    int32 OccupiedSeatCount = 0;
    int32 ActiveActionCount = 0;
    int32 HighSideCount = 0;
    int32 BraceCount = 0;
    int32 RecoveryCount = 0;
    double RaftBaseMassKg = 0.0;
    double TotalCrewMassKg = 0.0;
    double TotalLoadedMassKg = 0.0;
    FVector CrewCenterOfGravityOffset = FVector::ZeroVector;
    FVector CombinedCenterOfGravityOffset = FVector::ZeroVector;
    double RollMomentNm = 0.0;
    double PitchMomentNm = 0.0;
    double LateralBias = 0.0;
    double LongitudinalBias = 0.0;
    FRaftSimFlexRecoveryThresholds RecoveryThresholds;
};

// --- D2: seat-load coupling --------------------------------------------------

struct RAFTSIMPHYSICS_API FRaftSimFlexSeatTubeLoad
{
    FString SeatId;
    FString Role;
    double MassKg = 0.0;
    double ForceN = 0.0;
    FVector EffectiveLocalPosition = FVector::ZeroVector;
    FString TargetSegmentId;
    double TargetFreeboardLossM = 0.0;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexSeatLoadSolve
{
    FRaftSimFlexCrewTelemetry CrewTelemetry;
    FRaftSimFlexRigidState RigidState;
    FRaftSimFlexTubeSolve TubeSolve;
    TArray<FRaftSimFlexSeatTubeLoad> SeatLoads;
    double PortFreeboardLossM = 0.0;
    double StarboardFreeboardLossM = 0.0;
    double SternFreeboardLossM = 0.0;
    double BowFreeboardLossM = 0.0;
    double PortTotalFreeboardLossM = 0.0;
    double StarboardTotalFreeboardLossM = 0.0;
    double SternTotalFreeboardLossM = 0.0;
    double BowTotalFreeboardLossM = 0.0;
    double MaxSeatFreeboardLossM = 0.0;
};

// --- D3: overwash / flip risk ------------------------------------------------

// Uniform synthetic water field matching the D6 fixture inputs
// (field_kind == "synthetic_uniform"). A dry field (bWet=false) drains
// retained water without adding flux.
struct RAFTSIMPHYSICS_API FRaftSimFlexUniformWater
{
    double SurfaceHeightM = 0.0;
    FVector VelocityMps = FVector::ZeroVector;
    bool bWet = true;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexSegmentOverwash
{
    FString SegmentId;
    FVector LocalPosition = FVector::ZeroVector;
    double WaterSurfaceM = 0.0;
    double DepressedTubeTopM = 0.0;
    double OvertoppingDepthM = 0.0;
    double IncomingSpeedMps = 0.0;
    double OvertoppingFluxM3S = 0.0;
    double DrainageFluxM3S = 0.0;
    double RetainedWaterVolumeM3 = 0.0;
    double RetainedWaterMassKg = 0.0;
    double RetainedWaterRollMomentNm = 0.0;
    double RetainedWaterPitchMomentNm = 0.0;
    bool bUpstreamExposed = false;
    bool bWet = false;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexOverwashSolve
{
    TArray<FRaftSimFlexSegmentOverwash> SegmentOverwash;
    double TotalOvertoppingFluxM3S = 0.0;
    double TotalDrainageFluxM3S = 0.0;
    double TotalRetainedWaterVolumeM3 = 0.0;
    double TotalRetainedWaterMassKg = 0.0;
    double RetainedWaterRollMomentNm = 0.0;
    double RetainedWaterPitchMomentNm = 0.0;
    double ReferenceFlipThresholdNm = 0.0;
    double ReferenceFlipMarginNm = 0.0;
    bool bReferenceFlipRisk = false;
};

// --- D4: rock contact / wrap / pin / release --------------------------------

struct RAFTSIMPHYSICS_API FRaftSimFlexRockObstacle
{
    FString ObstacleId;
    FVector LocalPosition = FVector::ZeroVector;
    double RadiusM = 0.1;
    double FrictionCoefficient = 0.72;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexRockContact
{
    FString ObstacleId;
    FString SegmentId;
    FVector LocalPosition = FVector::ZeroVector;
    FVector ObstacleLocalPosition = FVector::ZeroVector;
    FVector ContactNormalLocal = FVector(1.0, 0.0, 0.0);
    double ClearanceM = 0.0;
    double PenetrationM = 0.0;
    double RecoveredPreviousIndentationM = 0.0;
    double IndentationM = 0.0;
    double PressurePa = 0.0;
    double PressureReleaseSupportN = 0.0;
    double NormalForceN = 0.0;
    double DampingForceN = 0.0;
    double FrictionForceN = 0.0;
    double WrapSupportN = 0.0;
    double HoldingForceN = 0.0;
    double ReleaseResistanceN = 0.0;
    double ReleaseAuthorityN = 0.0;
    double ReleaseMarginN = 0.0;
    bool bWrapping = false;
    bool bPinned = false;
    bool bRecovering = false;
};

struct RAFTSIMPHYSICS_API FRaftSimFlexRockContactSolve
{
    TArray<FRaftSimFlexRockContact> Contacts;
    double TotalHoldingForceN = 0.0;
    double MaxIndentationM = 0.0;
    double MinReleaseMarginN = 0.0;
    int32 PinnedObstacleCount = 0;
    int32 WrappingContactCount = 0;
    int32 RecoveringContactCount = 0;
};

namespace RaftSimFlex
{

// Model mode: Compliant mirrors the Python D1-D4 reference exactly. The rigid
// baseline is the same fixture pass measured through a rigid tube (no
// compliance, no pressure-release support, no wrap support, no indentation
// memory) for the D6 unreal_chaos_rigid_baseline delta-recording target.
enum class EModelMode : uint8
{
    Compliant,
    RigidBaseline,
};

// build_default_compliant_tube_layout_d1 (flexible_raft_d1.py).
RAFTSIMPHYSICS_API TArray<FRaftSimFlexTubeSegment> BuildDefaultCompliantTubeLayout(
    const FRaftSimFlexParameters& Parameters,
    int32 SegmentCountPerSide = 4,
    int32 SegmentCountPerEnd = 2,
    double NominalPressurePa = 18000.0);

// build_default_crew_seats2_5d (raft_coupling2_5d.py).
RAFTSIMPHYSICS_API TArray<FRaftSimFlexCrewSeat> BuildDefaultCrewSeats(
    const FRaftSimFlexParameters& Parameters);

// _nearest_segment_index: strict-less first-wins over the layout order.
RAFTSIMPHYSICS_API int32 NearestSegmentIndex(
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    const FVector& Position);

// solve_compliant_tube_d1 (flexible_raft_d1.py).
RAFTSIMPHYSICS_API FRaftSimFlexTubeSolve SolveCompliantTubeD1(
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    const TArray<FRaftSimFlexTubeLoad>& Loads,
    EModelMode Mode = EModelMode::Compliant,
    double MaxSegmentVolumeLossFraction = 0.18,
    double MaxFreeboardLossM = 0.28);

// evaluate_crew_weight_distribution2_5d (raft_coupling2_5d.py), restricted to
// the caller-supplied raft length/width path used by D2.
RAFTSIMPHYSICS_API FRaftSimFlexCrewTelemetry EvaluateCrewWeightDistribution(
    double TotalMassKg,
    const FVector& Gravity,
    const TArray<FRaftSimFlexCrewSeat>& Seats,
    const TArray<FRaftSimFlexCrewAction>& Actions,
    double RaftLengthM,
    double RaftWidthM,
    double MaxLeanOffsetM = 0.55,
    double HighSideOffsetM = 0.45,
    double BraceCenterDropM = 0.04,
    double BasePinThresholdN = 3200.0,
    double BaseFlipThresholdNm = 1800.0,
    double BaseReleaseThresholdN = 2600.0);

// solve_seat_load_coupled_tube_d2 (flexible_raft_d2.py).
RAFTSIMPHYSICS_API FRaftSimFlexSeatLoadSolve SolveSeatLoadCoupledTubeD2(
    const FRaftSimFlexRigidState& RigidState,
    const FRaftSimFlexParameters& Parameters,
    const TArray<FRaftSimFlexCrewSeat>& Seats,
    const TArray<FRaftSimFlexCrewAction>& Actions,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    EModelMode Mode = EModelMode::Compliant,
    double TotalMassKg = -1.0,
    const FVector& Gravity = FVector(0.0, 0.0, -9.81),
    double BraceDownforceFraction = 0.08,
    double RecoveryDownforceFraction = 0.04);

// evaluate_overwash_flip_d3 (flexible_raft_d3.py) with the synthetic uniform
// water field used by the D6 fixture inputs.
RAFTSIMPHYSICS_API FRaftSimFlexOverwashSolve EvaluateOverwashFlipD3(
    const FRaftSimFlexSeatLoadSolve& SeatTubeSolve,
    const FRaftSimFlexUniformWater& Water,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    const TMap<FString, double>* PreviousRetainedVolumeBySegment = nullptr,
    double Dt = 1.0 / 30.0,
    double BaseTubeTopFreeboardM = 0.16,
    double FluxCoefficient = 0.65,
    double DrainageRatePerS = 0.55,
    double WaterDensityKgM3 = 1000.0,
    double GravityMps2 = 9.81);

// evaluate_rock_contact_wrap_pin_d4 (flexible_raft_d4.py).
RAFTSIMPHYSICS_API FRaftSimFlexRockContactSolve EvaluateRockContactWrapPinD4(
    const FRaftSimFlexSeatLoadSolve& SeatTubeSolve,
    const TArray<FRaftSimFlexRockObstacle>& Obstacles,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    double TubeRadiusM,
    const TMap<FString, double>* PreviousIndentationBySegment = nullptr,
    EModelMode Mode = EModelMode::Compliant,
    double Dt = 1.0 / 30.0,
    double MaxIndentationM = 0.22,
    double TubeContactStiffnessNM = 30000.0,
    double ContactDampingNSM = 850.0,
    double PressureReleaseAreaM2 = 0.018,
    double RecoveryRatePerS = 2.4,
    double WrapSupportScale = 0.32);

} // namespace RaftSimFlex
