#include "RaftSimFlexibleRaftModel.h"

namespace RaftSimFlex
{

namespace
{

constexpr double Epsilon = 1.0e-12;

double ClampDouble(double Value, double Low, double High)
{
    return FMath::Min(FMath::Max(Value, Low), High);
}

// _xy_normal (flexible_raft_d4.py): planar normal with (1,0,0) fallback.
FVector XyNormal(const FVector& Vector)
{
    const double Length = FMath::Sqrt(Vector.X * Vector.X + Vector.Y * Vector.Y);
    if (Length <= 1.0e-9)
    {
        return FVector(1.0, 0.0, 0.0);
    }
    return FVector(Vector.X / Length, Vector.Y / Length, 0.0);
}

double XyDistance(const FVector& First, const FVector& Second)
{
    const double Dx = First.X - Second.X;
    const double Dy = First.Y - Second.Y;
    return FMath::Sqrt(Dx * Dx + Dy * Dy);
}

// _build_segment (flexible_raft_d1.py).
FRaftSimFlexTubeSegment BuildSegment(
    const FString& SegmentId,
    const FVector& LocalPosition,
    const FVector& OutwardNormal,
    double TributaryLengthM,
    double TubeRadiusM,
    double NominalPressurePa)
{
    const double RestVolume = UE_DOUBLE_PI * TubeRadiusM * TubeRadiusM * TributaryLengthM;
    const double ContactArea = FMath::Max(0.08, TubeRadiusM * TributaryLengthM * 0.55);

    FRaftSimFlexTubeSegment Segment;
    Segment.SegmentId = SegmentId;
    Segment.LocalPosition = LocalPosition;
    Segment.OutwardNormal = OutwardNormal.GetSafeNormal();
    Segment.TributaryLengthM = TributaryLengthM;
    Segment.RestVolumeM3 = RestVolume;
    Segment.ContactAreaM2 = ContactArea;
    Segment.NominalPressurePa = NominalPressurePa;
    Segment.ComplianceM3PerPa = FMath::Max(3.0e-8, RestVolume * 2.5e-6);
    return Segment;
}

double SeatForceN(
    double MassKg,
    double GravityMagnitude,
    bool bBrace,
    bool bRecovery,
    double BraceDownforceFraction,
    double RecoveryDownforceFraction)
{
    double Multiplier = 1.0;
    if (bBrace)
    {
        Multiplier += BraceDownforceFraction;
    }
    if (bRecovery)
    {
        Multiplier += RecoveryDownforceFraction;
    }
    return MassKg * GravityMagnitude * Multiplier;
}

double MaxFreeboardForPrefix(const TArray<FRaftSimFlexSegmentResponse>& Responses, const TCHAR* Prefix)
{
    double MaxLoss = 0.0;
    for (const FRaftSimFlexSegmentResponse& Response : Responses)
    {
        if (Response.SegmentId.StartsWith(Prefix, ESearchCase::CaseSensitive))
        {
            MaxLoss = FMath::Max(MaxLoss, Response.FreeboardLossM);
        }
    }
    return MaxLoss;
}

double SumFreeboardForPrefix(const TArray<FRaftSimFlexSegmentResponse>& Responses, const TCHAR* Prefix)
{
    double TotalLoss = 0.0;
    for (const FRaftSimFlexSegmentResponse& Response : Responses)
    {
        if (Response.SegmentId.StartsWith(Prefix, ESearchCase::CaseSensitive))
        {
            TotalLoss += Response.FreeboardLossM;
        }
    }
    return TotalLoss;
}

// _contact_payload (flexible_raft_d4.py).
FRaftSimFlexRockContact BuildContact(
    const FRaftSimFlexSeatLoadSolve& SeatTubeSolve,
    const FRaftSimFlexRockObstacle& Obstacle,
    const FRaftSimFlexTubeSegment& Segment,
    const FRaftSimFlexSegmentResponse& Response,
    double ClearanceM,
    double PenetrationM,
    double PreviousIndentationM,
    double Dt,
    double MaxIndentationM,
    double TubeContactStiffnessNM,
    double ContactDampingNSM,
    double PressureReleaseAreaM2,
    double RecoveryRatePerS,
    double WrapSupportScale,
    int32 ObstacleContactCount,
    bool bRecovering,
    bool bRigidBaseline)
{
    const double RecoveryFactor = FMath::Max(0.0, 1.0 - RecoveryRatePerS * Dt);
    const double RecoveredPrevious = bRigidBaseline
        ? 0.0
        : FMath::Min(MaxIndentationM, FMath::Max(0.0, PreviousIndentationM) * RecoveryFactor);
    const double Indentation = FMath::Min(MaxIndentationM, FMath::Max(PenetrationM, RecoveredPrevious));
    const FVector Normal = XyNormal(Segment.LocalPosition - Obstacle.LocalPosition);
    const FVector WorldNormal = SeatTubeSolve.RigidState.Orientation.RotateVector(Normal);
    const double ApproachSpeed = FMath::Max(
        0.0,
        -FVector::DotProduct(SeatTubeSolve.RigidState.PointVelocity(Segment.LocalPosition), WorldNormal));
    const double DampingForce = bRecovering ? 0.0 : ContactDampingNSM * ApproachSpeed;
    const double NormalForce = Indentation * TubeContactStiffnessNM + DampingForce;
    const double FrictionForce = NormalForce * Obstacle.FrictionCoefficient;
    const bool bWrapping = !bRigidBaseline && ObstacleContactCount >= 3 && !bRecovering;
    const double WrapSupport = bWrapping
        ? NormalForce * WrapSupportScale * static_cast<double>(FMath::Max(0, ObstacleContactCount - 1))
        : 0.0;
    const double HoldingForce = bRecovering ? 0.0 : FrictionForce + WrapSupport;
    const double PressureSupport = bRigidBaseline ? 0.0 : Response.PressurePa * PressureReleaseAreaM2;
    const double ReleaseResistance = FMath::Max(0.0, HoldingForce - PressureSupport);
    const double ReleaseAuthority = SeatTubeSolve.CrewTelemetry.RecoveryThresholds.ReleaseThresholdN;
    const double ReleaseMargin = ReleaseAuthority - ReleaseResistance;

    FRaftSimFlexRockContact Contact;
    Contact.ObstacleId = Obstacle.ObstacleId;
    Contact.SegmentId = Segment.SegmentId;
    Contact.LocalPosition = Segment.LocalPosition;
    Contact.ObstacleLocalPosition = Obstacle.LocalPosition;
    Contact.ContactNormalLocal = Normal;
    Contact.ClearanceM = ClearanceM;
    Contact.PenetrationM = PenetrationM;
    Contact.RecoveredPreviousIndentationM = RecoveredPrevious;
    Contact.IndentationM = Indentation;
    Contact.PressurePa = Response.PressurePa;
    Contact.PressureReleaseSupportN = PressureSupport;
    Contact.NormalForceN = NormalForce;
    Contact.DampingForceN = DampingForce;
    Contact.FrictionForceN = FrictionForce;
    Contact.WrapSupportN = WrapSupport;
    Contact.HoldingForceN = HoldingForce;
    Contact.ReleaseResistanceN = ReleaseResistance;
    Contact.ReleaseAuthorityN = ReleaseAuthority;
    Contact.ReleaseMarginN = ReleaseMargin;
    Contact.bWrapping = bWrapping;
    Contact.bPinned = ReleaseMargin < 0.0 && !bRecovering;
    Contact.bRecovering = bRecovering;
    return Contact;
}

} // namespace

TArray<FRaftSimFlexTubeSegment> BuildDefaultCompliantTubeLayout(
    const FRaftSimFlexParameters& Parameters,
    int32 SegmentCountPerSide,
    int32 SegmentCountPerEnd,
    double NominalPressurePa)
{
    TArray<FRaftSimFlexTubeSegment> Layout;
    if (SegmentCountPerSide <= 0 || SegmentCountPerEnd <= 0)
    {
        return Layout;
    }

    const double HalfLength = Parameters.LengthM * 0.5;
    const double HalfWidth = Parameters.WidthM * 0.5;
    const double SideStep = Parameters.LengthM / static_cast<double>(SegmentCountPerSide);
    const double EndStep = Parameters.WidthM / static_cast<double>(SegmentCountPerEnd);

    for (int32 Index = 0; Index < SegmentCountPerSide; ++Index)
    {
        const double X = -HalfLength + SideStep * (static_cast<double>(Index) + 0.5);
        Layout.Add(BuildSegment(
            FString::Printf(TEXT("port_%d"), Index),
            FVector(X, -HalfWidth, 0.0),
            FVector(0.0, -1.0, 0.0),
            SideStep,
            Parameters.TubeRadiusM,
            NominalPressurePa));
    }
    for (int32 Index = 0; Index < SegmentCountPerEnd; ++Index)
    {
        const double Y = -HalfWidth + EndStep * (static_cast<double>(Index) + 0.5);
        Layout.Add(BuildSegment(
            FString::Printf(TEXT("bow_%d"), Index),
            FVector(HalfLength, Y, 0.0),
            FVector(1.0, 0.0, 0.0),
            EndStep,
            Parameters.TubeRadiusM,
            NominalPressurePa));
    }
    for (int32 Index = SegmentCountPerSide - 1; Index >= 0; --Index)
    {
        const double X = -HalfLength + SideStep * (static_cast<double>(Index) + 0.5);
        Layout.Add(BuildSegment(
            FString::Printf(TEXT("starboard_%d"), Index),
            FVector(X, HalfWidth, 0.0),
            FVector(0.0, 1.0, 0.0),
            SideStep,
            Parameters.TubeRadiusM,
            NominalPressurePa));
    }
    for (int32 Index = SegmentCountPerEnd - 1; Index >= 0; --Index)
    {
        const double Y = -HalfWidth + EndStep * (static_cast<double>(Index) + 0.5);
        Layout.Add(BuildSegment(
            FString::Printf(TEXT("stern_%d"), Index),
            FVector(-HalfLength, Y, 0.0),
            FVector(-1.0, 0.0, 0.0),
            EndStep,
            Parameters.TubeRadiusM,
            NominalPressurePa));
    }
    return Layout;
}

TArray<FRaftSimFlexCrewSeat> BuildDefaultCrewSeats(const FRaftSimFlexParameters& Parameters)
{
    TArray<FRaftSimFlexCrewSeat> Seats;

    FRaftSimFlexCrewSeat Guide;
    Guide.SeatId = TEXT("guide");
    Guide.LocalPosition = FVector(-Parameters.LengthM * 0.42, 0.0, 0.15);
    Guide.OccupantMassKg = Parameters.GuideMassKg;
    Guide.Role = TEXT("guide");
    Seats.Add(Guide);

    // _passenger_offsets (raft_coupling2_5d.py).
    if (Parameters.PassengerCount > 0)
    {
        const int32 Rows = FMath::Max(1, (Parameters.PassengerCount + 1) / 2);
        const double UsableLength = Parameters.LengthM * 0.58;
        const double StartX = -UsableLength * 0.35;
        const double Step = UsableLength / static_cast<double>(FMath::Max(Rows - 1, 1));
        const double SideY = Parameters.WidthM * 0.32;
        for (int32 Index = 0; Index < Parameters.PassengerCount; ++Index)
        {
            const int32 Row = Index / 2;
            const double Side = (Index % 2 == 0) ? -1.0 : 1.0;
            FRaftSimFlexCrewSeat Seat;
            Seat.SeatId = FString::Printf(TEXT("passenger_%d"), Index);
            Seat.LocalPosition = FVector(StartX + Row * Step, Side * SideY, 0.12);
            Seat.OccupantMassKg = Parameters.PassengerMassKg;
            Seat.Role = TEXT("passenger");
            Seats.Add(Seat);
        }
    }
    return Seats;
}

int32 NearestSegmentIndex(const TArray<FRaftSimFlexTubeSegment>& Layout, const FVector& Position)
{
    int32 BestIndex = 0;
    double BestDistanceSquared = TNumericLimits<double>::Max();
    for (int32 Index = 0; Index < Layout.Num(); ++Index)
    {
        const FVector Delta = Layout[Index].LocalPosition - Position;
        const double DistanceSquared = FVector::DotProduct(Delta, Delta);
        if (DistanceSquared < BestDistanceSquared)
        {
            BestDistanceSquared = DistanceSquared;
            BestIndex = Index;
        }
    }
    return BestIndex;
}

FRaftSimFlexTubeSolve SolveCompliantTubeD1(
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    const TArray<FRaftSimFlexTubeLoad>& Loads,
    EModelMode Mode,
    double MaxSegmentVolumeLossFraction,
    double MaxFreeboardLossM)
{
    FRaftSimFlexTubeSolve Solve;
    const int32 SegmentCount = Layout.Num();
    if (SegmentCount == 0)
    {
        return Solve;
    }

    TArray<double> DirectLoads;
    TArray<double> LacingLoads;
    TArray<double> FloorLoads;
    TArray<double> FrameLoads;
    DirectLoads.SetNumZeroed(SegmentCount);
    LacingLoads.SetNumZeroed(SegmentCount);
    FloorLoads.SetNumZeroed(SegmentCount);
    FrameLoads.SetNumZeroed(SegmentCount);

    double TotalAppliedLoad = 0.0;
    for (const FRaftSimFlexTubeLoad& Load : Loads)
    {
        const int32 Target = NearestSegmentIndex(Layout, Load.LocalPosition);
        const FRaftSimFlexTubeSegment& Segment = Layout[Target];
        const double DirectFraction =
            1.0
            - Segment.FloorCouplingFraction
            - Segment.LacingCouplingFraction
            - Segment.FrameCouplingFraction;
        TotalAppliedLoad += Load.ForceN;
        DirectLoads[Target] += Load.ForceN * DirectFraction;

        const int32 PreviousIndex = (Target - 1 + SegmentCount) % SegmentCount;
        const int32 NextIndex = (Target + 1) % SegmentCount;
        const double LacingShare = Load.ForceN * Segment.LacingCouplingFraction * 0.5;
        LacingLoads[PreviousIndex] += LacingShare;
        LacingLoads[NextIndex] += LacingShare;

        const double FloorShare = Load.ForceN * Segment.FloorCouplingFraction / static_cast<double>(SegmentCount);
        for (int32 Index = 0; Index < SegmentCount; ++Index)
        {
            FloorLoads[Index] += FloorShare;
        }

        const int32 OppositeIndex = (Target + SegmentCount / 2) % SegmentCount;
        const double FrameShare = Load.ForceN * Segment.FrameCouplingFraction * 0.5;
        FrameLoads[Target] += FrameShare;
        FrameLoads[OppositeIndex] += FrameShare;
    }

    Solve.SegmentResponses.Reserve(SegmentCount);
    for (int32 Index = 0; Index < SegmentCount; ++Index)
    {
        const FRaftSimFlexTubeSegment& Segment = Layout[Index];
        const double EffectiveLoad =
            DirectLoads[Index] + LacingLoads[Index] + FloorLoads[Index] + FrameLoads[Index];
        const double PressureDelta = EffectiveLoad / Segment.ContactAreaM2;

        double VolumeLoss = 0.0;
        double Compression = 0.0;
        bool bBounded = false;
        if (Mode == EModelMode::Compliant)
        {
            const double UnboundedVolumeLoss = Segment.ComplianceM3PerPa * PressureDelta;
            const double MaxVolumeLoss = Segment.RestVolumeM3 * MaxSegmentVolumeLossFraction;
            VolumeLoss = FMath::Min(UnboundedVolumeLoss, MaxVolumeLoss);
            const double UnboundedCompression = VolumeLoss / Segment.ContactAreaM2;
            Compression = FMath::Min(UnboundedCompression, MaxFreeboardLossM);
            bBounded =
                UnboundedVolumeLoss > MaxVolumeLoss + Epsilon
                || UnboundedCompression > MaxFreeboardLossM + Epsilon;
        }

        FRaftSimFlexSegmentResponse Response;
        Response.SegmentId = Segment.SegmentId;
        Response.LocalPosition = Segment.LocalPosition;
        Response.DirectLoadN = DirectLoads[Index];
        Response.ReceivedLacingLoadN = LacingLoads[Index];
        Response.FloorLoadN = FloorLoads[Index];
        Response.FrameLoadN = FrameLoads[Index];
        Response.EffectiveLoadN = EffectiveLoad;
        Response.PressurePa = Segment.NominalPressurePa + PressureDelta;
        Response.PressureDeltaPa = PressureDelta;
        Response.VolumeM3 = Segment.RestVolumeM3 - VolumeLoss;
        Response.VolumeLossM3 = VolumeLoss;
        Response.CompressionM = Compression;
        Response.FreeboardLossM = Compression;
        Response.bBounded = bBounded;
        Solve.SegmentResponses.Add(Response);
    }

    Solve.TotalAppliedLoadN = TotalAppliedLoad;
    for (const FRaftSimFlexSegmentResponse& Response : Solve.SegmentResponses)
    {
        Solve.TotalEffectiveTubeLoadN += Response.EffectiveLoadN;
        Solve.TotalVolumeLossM3 += Response.VolumeLossM3;
        Solve.MaxFreeboardLossM = FMath::Max(Solve.MaxFreeboardLossM, Response.FreeboardLossM);
        Solve.MaxPressureDeltaPa = FMath::Max(Solve.MaxPressureDeltaPa, Response.PressureDeltaPa);
        Solve.RollLoadBiasNm += Response.EffectiveLoadN * Response.LocalPosition.Y;
        Solve.PitchLoadBiasNm += Response.EffectiveLoadN * Response.LocalPosition.X;
        if (Response.bBounded)
        {
            ++Solve.BoundedSegmentCount;
        }
    }
    return Solve;
}

FRaftSimFlexCrewTelemetry EvaluateCrewWeightDistribution(
    double TotalMassKg,
    const FVector& Gravity,
    const TArray<FRaftSimFlexCrewSeat>& Seats,
    const TArray<FRaftSimFlexCrewAction>& Actions,
    double RaftLengthM,
    double RaftWidthM,
    double MaxLeanOffsetM,
    double HighSideOffsetM,
    double BraceCenterDropM,
    double BasePinThresholdN,
    double BaseFlipThresholdNm,
    double BaseReleaseThresholdN)
{
    FRaftSimFlexCrewTelemetry Telemetry;

    TMap<FString, FRaftSimFlexCrewAction> ActionsBySeat;
    for (const FRaftSimFlexCrewAction& Action : Actions)
    {
        ActionsBySeat.Add(Action.SeatId, Action);
    }

    double AllCrewMass = 0.0;
    for (const FRaftSimFlexCrewSeat& Seat : Seats)
    {
        AllCrewMass += Seat.OccupantMassKg;
    }
    const double RaftBaseMass = FMath::Max(0.0, TotalMassKg - AllCrewMass);

    double OccupiedMass = 0.0;
    FVector WeightedCrewPosition = FVector::ZeroVector;

    for (const FRaftSimFlexCrewSeat& Seat : Seats)
    {
        FRaftSimFlexCrewAction Action;
        Action.SeatId = Seat.SeatId;
        if (const FRaftSimFlexCrewAction* Found = ActionsBySeat.Find(Seat.SeatId))
        {
            Action = *Found;
        }

        // _clamped_offset (raft_coupling2_5d.py).
        FVector LeanOffset = Action.LeanOffset;
        bool bLeanWasClamped = false;
        const double LeanMagnitude = LeanOffset.Length();
        if (LeanMagnitude > MaxLeanOffsetM)
        {
            LeanOffset = (LeanOffset / LeanMagnitude) * MaxLeanOffsetM;
            bLeanWasClamped = true;
        }

        const FVector HighSideOffset(0.0, static_cast<double>(Action.HighSideDirection) * HighSideOffsetM, 0.0);
        const FVector BraceOffset(0.0, 0.0, Action.bBrace ? -BraceCenterDropM : 0.0);
        const FVector ActionOffset = LeanOffset + HighSideOffset + BraceOffset;
        const FVector EffectivePosition = Seat.LocalPosition + ActionOffset;
        const bool bActionIsActive =
            LeanOffset.Length() > 1.0e-9
            || Action.HighSideDirection != 0
            || Action.bBrace
            || Action.bRecovery;

        if (Seat.bOccupied)
        {
            OccupiedMass += Seat.OccupantMassKg;
            WeightedCrewPosition += EffectivePosition * Seat.OccupantMassKg;
            if (bActionIsActive)
            {
                ++Telemetry.ActiveActionCount;
            }
            if (Action.HighSideDirection != 0)
            {
                ++Telemetry.HighSideCount;
            }
            if (Action.bBrace)
            {
                ++Telemetry.BraceCount;
            }
            if (Action.bRecovery)
            {
                ++Telemetry.RecoveryCount;
            }
            ++Telemetry.OccupiedSeatCount;
        }

        FRaftSimFlexSeatTelemetry SeatTelemetry;
        SeatTelemetry.SeatId = Seat.SeatId;
        SeatTelemetry.Role = Seat.Role;
        SeatTelemetry.bOccupied = Seat.bOccupied;
        SeatTelemetry.MassKg = Seat.bOccupied ? Seat.OccupantMassKg : 0.0;
        SeatTelemetry.BaseLocalPosition = Seat.LocalPosition;
        SeatTelemetry.ActionOffset = Seat.bOccupied ? ActionOffset : FVector::ZeroVector;
        SeatTelemetry.EffectiveLocalPosition = Seat.bOccupied ? EffectivePosition : Seat.LocalPosition;
        SeatTelemetry.HighSideDirection = Seat.bOccupied ? Action.HighSideDirection : 0;
        SeatTelemetry.bBrace = Seat.bOccupied ? Action.bBrace : false;
        SeatTelemetry.bRecovery = Seat.bOccupied ? Action.bRecovery : false;
        SeatTelemetry.bLeanWasClamped = Seat.bOccupied ? bLeanWasClamped : false;
        Telemetry.SeatTelemetry.Add(SeatTelemetry);
    }

    const FVector CrewCg = OccupiedMass > 0.0 ? WeightedCrewPosition / OccupiedMass : FVector::ZeroVector;
    const double LoadedMass = RaftBaseMass + OccupiedMass;
    const FVector CombinedCg = LoadedMass > 0.0 ? WeightedCrewPosition / LoadedMass : FVector::ZeroVector;
    const double GravityMagnitude = Gravity.Length() > 1.0e-9 ? Gravity.Length() : 9.81;

    Telemetry.RaftBaseMassKg = RaftBaseMass;
    Telemetry.TotalCrewMassKg = OccupiedMass;
    Telemetry.TotalLoadedMassKg = LoadedMass;
    Telemetry.CrewCenterOfGravityOffset = CrewCg;
    Telemetry.CombinedCenterOfGravityOffset = CombinedCg;
    Telemetry.RollMomentNm = LoadedMass * GravityMagnitude * CombinedCg.Y;
    Telemetry.PitchMomentNm = LoadedMass * GravityMagnitude * CombinedCg.X;

    // _crew_contact_loading bias terms (raft_coupling2_5d.py).
    const double HalfWidth = FMath::Max(RaftWidthM * 0.5, 1.0e-6);
    const double HalfLength = FMath::Max(RaftLengthM * 0.5, 1.0e-6);
    Telemetry.LateralBias = ClampDouble(CombinedCg.Y / HalfWidth, -0.95, 0.95);
    Telemetry.LongitudinalBias = ClampDouble(CombinedCg.X / HalfLength, -0.95, 0.95);

    // _crew_recovery_thresholds (raft_coupling2_5d.py).
    const double Denominator = static_cast<double>(FMath::Max(Telemetry.OccupiedSeatCount, 1));
    const double HighSideRatio = static_cast<double>(Telemetry.HighSideCount) / Denominator;
    const double BraceRatio = static_cast<double>(Telemetry.BraceCount) / Denominator;
    const double RecoveryRatio = static_cast<double>(Telemetry.RecoveryCount) / Denominator;
    const double LateralAuthority = FMath::Abs(Telemetry.LateralBias);
    const double PinMultiplier =
        1.0 + 0.10 * BraceRatio + 0.10 * HighSideRatio + FMath::Min(0.20, LateralAuthority * 0.20);
    const double FlipMultiplier =
        1.0 + 0.20 * HighSideRatio + 0.04 * BraceRatio + FMath::Min(0.35, LateralAuthority * 0.35);
    const double ReleaseMultiplier = FMath::Max(
        0.65,
        1.0
        - 0.12 * HighSideRatio
        - 0.10 * BraceRatio
        - 0.08 * RecoveryRatio
        - FMath::Min(0.18, LateralAuthority * 0.18));

    Telemetry.RecoveryThresholds.PinThresholdN = BasePinThresholdN * PinMultiplier;
    Telemetry.RecoveryThresholds.FlipThresholdNm = BaseFlipThresholdNm * FlipMultiplier;
    Telemetry.RecoveryThresholds.ReleaseThresholdN = BaseReleaseThresholdN * ReleaseMultiplier;
    Telemetry.RecoveryThresholds.PinThresholdMultiplier = PinMultiplier;
    Telemetry.RecoveryThresholds.FlipThresholdMultiplier = FlipMultiplier;
    Telemetry.RecoveryThresholds.ReleaseThresholdMultiplier = ReleaseMultiplier;
    return Telemetry;
}

FRaftSimFlexSeatLoadSolve SolveSeatLoadCoupledTubeD2(
    const FRaftSimFlexRigidState& RigidState,
    const FRaftSimFlexParameters& Parameters,
    const TArray<FRaftSimFlexCrewSeat>& Seats,
    const TArray<FRaftSimFlexCrewAction>& Actions,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    EModelMode Mode,
    double TotalMassKg,
    const FVector& Gravity,
    double BraceDownforceFraction,
    double RecoveryDownforceFraction)
{
    FRaftSimFlexSeatLoadSolve Solve;
    Solve.RigidState = RigidState;

    const double ResolvedTotalMass = TotalMassKg > 0.0 ? TotalMassKg : Parameters.TotalMassKg();
    Solve.CrewTelemetry = EvaluateCrewWeightDistribution(
        ResolvedTotalMass,
        Gravity,
        Seats,
        Actions,
        Parameters.LengthM,
        Parameters.WidthM);

    const double GravityMagnitude = Gravity.Length() > 1.0e-9 ? Gravity.Length() : 9.81;

    TArray<FRaftSimFlexTubeLoad> Loads;
    for (const FRaftSimFlexSeatTelemetry& Seat : Solve.CrewTelemetry.SeatTelemetry)
    {
        if (!Seat.bOccupied)
        {
            continue;
        }
        FRaftSimFlexTubeLoad Load;
        Load.LoadId = FString::Printf(TEXT("seat:%s"), *Seat.SeatId);
        Load.LocalPosition = Seat.EffectiveLocalPosition;
        Load.ForceN = SeatForceN(
            Seat.MassKg,
            GravityMagnitude,
            Seat.bBrace,
            Seat.bRecovery,
            BraceDownforceFraction,
            RecoveryDownforceFraction);
        Loads.Add(Load);
    }

    Solve.TubeSolve = SolveCompliantTubeD1(Layout, Loads, Mode);

    for (const FRaftSimFlexSeatTelemetry& Seat : Solve.CrewTelemetry.SeatTelemetry)
    {
        if (!Seat.bOccupied)
        {
            continue;
        }
        const int32 TargetIndex = NearestSegmentIndex(Layout, Seat.EffectiveLocalPosition);
        FRaftSimFlexSeatTubeLoad SeatLoad;
        SeatLoad.SeatId = Seat.SeatId;
        SeatLoad.Role = Seat.Role;
        SeatLoad.MassKg = Seat.MassKg;
        SeatLoad.ForceN = SeatForceN(
            Seat.MassKg,
            GravityMagnitude,
            Seat.bBrace,
            Seat.bRecovery,
            BraceDownforceFraction,
            RecoveryDownforceFraction);
        SeatLoad.EffectiveLocalPosition = Seat.EffectiveLocalPosition;
        SeatLoad.TargetSegmentId = Layout[TargetIndex].SegmentId;
        SeatLoad.TargetFreeboardLossM = Solve.TubeSolve.SegmentResponses[TargetIndex].FreeboardLossM;
        Solve.SeatLoads.Add(SeatLoad);
        Solve.MaxSeatFreeboardLossM = FMath::Max(Solve.MaxSeatFreeboardLossM, SeatLoad.TargetFreeboardLossM);
    }

    Solve.PortFreeboardLossM = MaxFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("port_"));
    Solve.StarboardFreeboardLossM = MaxFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("starboard_"));
    Solve.SternFreeboardLossM = MaxFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("stern_"));
    Solve.BowFreeboardLossM = MaxFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("bow_"));
    Solve.PortTotalFreeboardLossM = SumFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("port_"));
    Solve.StarboardTotalFreeboardLossM = SumFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("starboard_"));
    Solve.SternTotalFreeboardLossM = SumFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("stern_"));
    Solve.BowTotalFreeboardLossM = SumFreeboardForPrefix(Solve.TubeSolve.SegmentResponses, TEXT("bow_"));
    return Solve;
}

FRaftSimFlexOverwashSolve EvaluateOverwashFlipD3(
    const FRaftSimFlexSeatLoadSolve& SeatTubeSolve,
    const FRaftSimFlexUniformWater& Water,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    const TMap<FString, double>* PreviousRetainedVolumeBySegment,
    double Dt,
    double BaseTubeTopFreeboardM,
    double FluxCoefficient,
    double DrainageRatePerS,
    double WaterDensityKgM3,
    double GravityMps2)
{
    FRaftSimFlexOverwashSolve Solve;
    if (Dt <= 0.0)
    {
        return Solve;
    }

    TMap<FString, const FRaftSimFlexSegmentResponse*> ResponsesById;
    for (const FRaftSimFlexSegmentResponse& Response : SeatTubeSolve.TubeSolve.SegmentResponses)
    {
        ResponsesById.Add(Response.SegmentId, &Response);
    }

    const FRaftSimFlexRigidState& RigidState = SeatTubeSolve.RigidState;
    for (const FRaftSimFlexTubeSegment& Segment : Layout)
    {
        const FRaftSimFlexSegmentResponse* const* FoundResponse = ResponsesById.Find(Segment.SegmentId);
        if (FoundResponse == nullptr)
        {
            continue;
        }
        const FRaftSimFlexSegmentResponse& Response = **FoundResponse;

        const FVector WorldPosition = RigidState.WorldPoint(Response.LocalPosition);
        const FVector WorldNormal = RigidState.Orientation.RotateVector(Segment.OutwardNormal).GetSafeNormal();
        const FVector RelativeWaterVelocity =
            Water.VelocityMps - RigidState.PointVelocity(Response.LocalPosition);
        const double IncomingSpeed = FMath::Max(0.0, -FVector::DotProduct(RelativeWaterVelocity, WorldNormal));
        const double DepressedTubeTop = WorldPosition.Z + BaseTubeTopFreeboardM - Response.FreeboardLossM;
        const double OvertoppingDepth = FMath::Max(0.0, Water.SurfaceHeightM - DepressedTubeTop);
        const bool bUpstreamExposed = Water.bWet && IncomingSpeed > 1.0e-6 && OvertoppingDepth > 1.0e-6;
        const double Flux = bUpstreamExposed
            ? FluxCoefficient * OvertoppingDepth * IncomingSpeed * Segment.TributaryLengthM
            : 0.0;

        double PreviousVolume = 0.0;
        if (PreviousRetainedVolumeBySegment != nullptr)
        {
            if (const double* Found = PreviousRetainedVolumeBySegment->Find(Segment.SegmentId))
            {
                PreviousVolume = FMath::Max(0.0, *Found);
            }
        }
        const double DrainageFlux = FMath::Min(PreviousVolume / Dt, PreviousVolume * DrainageRatePerS);
        const double RetainedVolume = FMath::Max(0.0, PreviousVolume + Flux * Dt - DrainageFlux * Dt);
        const double RetainedMass = RetainedVolume * WaterDensityKgM3;
        const double VerticalLoad = RetainedMass * GravityMps2;

        FRaftSimFlexSegmentOverwash Overwash;
        Overwash.SegmentId = Segment.SegmentId;
        Overwash.LocalPosition = Response.LocalPosition;
        Overwash.WaterSurfaceM = Water.SurfaceHeightM;
        Overwash.DepressedTubeTopM = DepressedTubeTop;
        Overwash.OvertoppingDepthM = OvertoppingDepth;
        Overwash.IncomingSpeedMps = IncomingSpeed;
        Overwash.OvertoppingFluxM3S = Flux;
        Overwash.DrainageFluxM3S = DrainageFlux;
        Overwash.RetainedWaterVolumeM3 = RetainedVolume;
        Overwash.RetainedWaterMassKg = RetainedMass;
        Overwash.RetainedWaterRollMomentNm = VerticalLoad * Response.LocalPosition.Y;
        Overwash.RetainedWaterPitchMomentNm = VerticalLoad * Response.LocalPosition.X;
        Overwash.bUpstreamExposed = bUpstreamExposed;
        Overwash.bWet = Water.bWet;
        Solve.SegmentOverwash.Add(Overwash);
    }

    for (const FRaftSimFlexSegmentOverwash& Segment : Solve.SegmentOverwash)
    {
        Solve.TotalOvertoppingFluxM3S += Segment.OvertoppingFluxM3S;
        Solve.TotalDrainageFluxM3S += Segment.DrainageFluxM3S;
        Solve.TotalRetainedWaterVolumeM3 += Segment.RetainedWaterVolumeM3;
        Solve.TotalRetainedWaterMassKg += Segment.RetainedWaterMassKg;
        Solve.RetainedWaterRollMomentNm += Segment.RetainedWaterRollMomentNm;
        Solve.RetainedWaterPitchMomentNm += Segment.RetainedWaterPitchMomentNm;
    }

    Solve.ReferenceFlipThresholdNm = SeatTubeSolve.CrewTelemetry.RecoveryThresholds.FlipThresholdNm;
    Solve.ReferenceFlipMarginNm =
        Solve.ReferenceFlipThresholdNm - FMath::Abs(Solve.RetainedWaterRollMomentNm);
    Solve.bReferenceFlipRisk = Solve.ReferenceFlipMarginNm < 0.0;
    return Solve;
}

FRaftSimFlexRockContactSolve EvaluateRockContactWrapPinD4(
    const FRaftSimFlexSeatLoadSolve& SeatTubeSolve,
    const TArray<FRaftSimFlexRockObstacle>& Obstacles,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    double TubeRadiusM,
    const TMap<FString, double>* PreviousIndentationBySegment,
    EModelMode Mode,
    double Dt,
    double MaxIndentationM,
    double TubeContactStiffnessNM,
    double ContactDampingNSM,
    double PressureReleaseAreaM2,
    double RecoveryRatePerS,
    double WrapSupportScale)
{
    FRaftSimFlexRockContactSolve Solve;
    if (Dt <= 0.0 || TubeRadiusM <= 0.0)
    {
        return Solve;
    }
    const bool bRigidBaseline = Mode == EModelMode::RigidBaseline;

    TMap<FString, const FRaftSimFlexSegmentResponse*> ResponsesById;
    for (const FRaftSimFlexSegmentResponse& Response : SeatTubeSolve.TubeSolve.SegmentResponses)
    {
        ResponsesById.Add(Response.SegmentId, &Response);
    }

    struct FContactCandidate
    {
        const FRaftSimFlexRockObstacle* Obstacle = nullptr;
        const FRaftSimFlexTubeSegment* Segment = nullptr;
        double ClearanceM = 0.0;
        double PenetrationM = 0.0;
    };
    TArray<FContactCandidate> Candidates;
    TSet<FString> TouchedSegmentIds;
    for (const FRaftSimFlexRockObstacle& Obstacle : Obstacles)
    {
        for (const FRaftSimFlexTubeSegment& Segment : Layout)
        {
            const double Distance = XyDistance(Segment.LocalPosition, Obstacle.LocalPosition);
            const double Clearance = Distance - (TubeRadiusM + Obstacle.RadiusM);
            const double Penetration = FMath::Max(0.0, -Clearance);
            if (Penetration <= 0.0)
            {
                continue;
            }
            Candidates.Add({&Obstacle, &Segment, Clearance, Penetration});
            TouchedSegmentIds.Add(Segment.SegmentId);
        }
    }

    TMap<FString, int32> ObstacleContactCounts;
    for (const FContactCandidate& Candidate : Candidates)
    {
        ObstacleContactCounts.FindOrAdd(Candidate.Obstacle->ObstacleId) += 1;
    }

    auto PreviousIndentation = [PreviousIndentationBySegment](const FString& SegmentId) -> double
    {
        if (PreviousIndentationBySegment != nullptr)
        {
            if (const double* Found = PreviousIndentationBySegment->Find(SegmentId))
            {
                return *Found;
            }
        }
        return 0.0;
    };

    for (const FContactCandidate& Candidate : Candidates)
    {
        const FRaftSimFlexSegmentResponse* const* FoundResponse =
            ResponsesById.Find(Candidate.Segment->SegmentId);
        if (FoundResponse == nullptr)
        {
            continue;
        }
        Solve.Contacts.Add(BuildContact(
            SeatTubeSolve,
            *Candidate.Obstacle,
            *Candidate.Segment,
            **FoundResponse,
            Candidate.ClearanceM,
            Candidate.PenetrationM,
            PreviousIndentation(Candidate.Segment->SegmentId),
            Dt,
            MaxIndentationM,
            TubeContactStiffnessNM,
            ContactDampingNSM,
            PressureReleaseAreaM2,
            RecoveryRatePerS,
            WrapSupportScale,
            ObstacleContactCounts.FindChecked(Candidate.Obstacle->ObstacleId),
            /*bRecovering=*/false,
            bRigidBaseline));
    }

    // Post-contact shape recovery for previously indented, untouched segments
    // (compliant reference only: the rigid baseline has no indentation memory).
    if (!bRigidBaseline)
    {
        for (const FRaftSimFlexTubeSegment& Segment : Layout)
        {
            if (TouchedSegmentIds.Contains(Segment.SegmentId))
            {
                continue;
            }
            const double Previous = PreviousIndentation(Segment.SegmentId);
            if (Previous <= 0.0)
            {
                continue;
            }
            const FRaftSimFlexSegmentResponse* const* FoundResponse = ResponsesById.Find(Segment.SegmentId);
            if (FoundResponse == nullptr)
            {
                continue;
            }
            FRaftSimFlexRockObstacle RecoveryObstacle;
            RecoveryObstacle.ObstacleId = TEXT("shape_recovery");
            RecoveryObstacle.LocalPosition = Segment.LocalPosition;
            RecoveryObstacle.RadiusM = 0.01;
            RecoveryObstacle.FrictionCoefficient = 0.0;
            Solve.Contacts.Add(BuildContact(
                SeatTubeSolve,
                RecoveryObstacle,
                Segment,
                **FoundResponse,
                /*ClearanceM=*/0.0,
                /*PenetrationM=*/0.0,
                Previous,
                Dt,
                MaxIndentationM,
                TubeContactStiffnessNM,
                /*ContactDampingNSM=*/0.0,
                PressureReleaseAreaM2,
                RecoveryRatePerS,
                /*WrapSupportScale=*/0.0,
                /*ObstacleContactCount=*/1,
                /*bRecovering=*/true,
                bRigidBaseline));
        }
    }

    TSet<FString> PinnedObstacles;
    bool bFirstMargin = true;
    for (const FRaftSimFlexRockContact& Contact : Solve.Contacts)
    {
        Solve.TotalHoldingForceN += Contact.HoldingForceN;
        Solve.MaxIndentationM = FMath::Max(Solve.MaxIndentationM, Contact.IndentationM);
        if (bFirstMargin || Contact.ReleaseMarginN < Solve.MinReleaseMarginN)
        {
            Solve.MinReleaseMarginN = Contact.ReleaseMarginN;
            bFirstMargin = false;
        }
        if (Contact.bWrapping)
        {
            ++Solve.WrappingContactCount;
        }
        if (Contact.bRecovering)
        {
            ++Solve.RecoveringContactCount;
        }
        if (Contact.bPinned && !Contact.bRecovering)
        {
            PinnedObstacles.Add(Contact.ObstacleId);
        }
    }
    if (Solve.Contacts.Num() == 0)
    {
        Solve.MinReleaseMarginN = 0.0;
    }
    Solve.PinnedObstacleCount = PinnedObstacles.Num();
    return Solve;
}

} // namespace RaftSimFlex
