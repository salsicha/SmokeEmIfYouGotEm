#pragma once

#include "CoreMinimal.h"

/**
 * A hole's breaking wave: the pile of white water standing across the trough
 * below the pour-over, perpetually crashing back upstream without moving.
 * One shape, drawn by the hole's churn and felt by the hull.
 *
 * The pile's water rolls upstream over it: up its back, over the crest and
 * down its curling front into the trough, where it meets the water falling
 * over the pour-over. A raft drifting in climbs the front, is pushed back
 * down it by the pile's water and its slope, and slides back into the trough
 * under the falling water. A raft with enough way on (a crew paddling
 * forward) carries over the crest and down the back, out of the hole. No
 * force or flip is prescribed: the hull's own buoyancy, drag and upper-face
 * loads meet this water.
 *
 * Positions are metres in a hole's flow frame: Along downstream from the
 * pour-over's crest, Across to its left.
 */
namespace RaftSimHoleWave
{
struct FShape
{
    /** Crest of the pile above the trough's lowest water. */
    double HeightM = 0.75;
    /** From PlungeOffsetM to the boil line behind the pile. */
    double LengthM = 4.0;
    /** How far past the pour-over's crest the pile's front may fall. */
    double PlungeOffsetM = 0.3;
    /** Where the crest stands, from PlungeOffsetM (0) to the boil line (1). */
    double CrestPosition = 0.5;
    /** How far the lip throws out upstream before it falls. */
    double ThrowM = 0.45;
    /** The pile dies away beyond this far either side of the centre line. */
    double HalfWidthM = 3.3;
    /** The pile bows downstream away from the centre line, as the crest does. */
    double CrestBowPerSquareMeter = 0.035;
    /** How fast its water rolls upstream over it. */
    double RollMps = 1.7;
    /** 0..1: how strongly the hole breaks. Scales the pile and its roll. */
    double Intensity = 1.0;
    /** The white water is part air: it bears a hull like solid water this
     * share of its depth. */
    double BearingFraction = 0.3;
    /** Under the white water the solid water runs back upstream too, down
     * to this depth below the water's own surface: the roller. */
    double ReturnDepthM = 0.6;

    /** The pile below a pour-over CrestHeightM high whose face runs over
     * CrestLengthM (the crest relief's own dimensions). */
    static FShape ForCrest(double CrestHeightM, double CrestLengthM, double Intensity)
    {
        FShape Shape;
        const double Length = FMath::Clamp(CrestLengthM, 2.0, 7.0);
        Shape.HeightM = 0.94 * FMath::Clamp(CrestHeightM, 0.0, 1.2);
        Shape.LengthM = 2.0 * Length;
        Shape.PlungeOffsetM = 0.15 * Length;
        Shape.ThrowM = 0.6 * Shape.HeightM;
        Shape.HalfWidthM = 1.1 * FMath::Clamp(Length, 3.0, 5.0);
        Shape.Intensity = FMath::Clamp(Intensity, 0.0, 1.0);
        // A breaking wave's water moves at about its wave speed, sqrt(g H),
        // and its roller is about as deep as the wave is high: a bigger
        // hole holds harder, not just falls harder.
        Shape.RollMps = 0.62 * FMath::Sqrt(9.81 * Shape.HeightM);
        Shape.ReturnDepthM = 0.8 * Shape.HeightM;
        return Shape;
    }

    /** A river hole site's pile: its crest relief's physical height and face
     * length, as strong as it breaks (intensity times spilling fraction). A
     * legacy lattice crest carries no physical height (negative): a modest
     * pile. Drawn and felt alike. */
    static FShape ForSite(double PhysicalCrestHeightM, double CrestLengthM, double Strength)
    {
        return ForCrest(PhysicalCrestHeightM >= 0.0 ? PhysicalCrestHeightM : 0.55, CrestLengthM, Strength);
    }

    double Lateral(double Across) const
    {
        return FMath::Exp(-FMath::Pow(FMath::Abs(Across) / (0.8 * HalfWidthM), 4.0));
    }
    double Bow(double Across) const { return CrestBowPerSquareMeter * Across * Across; }
    double CrestAlong() const { return PlungeOffsetM + CrestPosition * LengthM; }
    double BoilAlong() const { return PlungeOffsetM + LengthM; }
    /** Where the curling front lands, on the centre line. */
    double PlungeAlong(double Across = 0.0) const
    {
        return FMath::Max(CrestAlong() - ThrowM * Lateral(Across) - 0.12, 0.5 * PlungeOffsetM);
    }

    /** Height of the pile's top above the trough's lowest water: the upper
     * envelope of the curl, rising steeply from where its front lands to the
     * crest and falling away down its back to the boil line. */
    double TopAboveToe(double Along, double Across) const
    {
        const double Lat = Lateral(Across);
        if (Lat < 0.01 || Intensity <= 0.0)
        {
            return 0.0;
        }
        const double A = Along - Bow(Across);
        const double Crest = CrestAlong(), Boil = BoilAlong(), Plunge = PlungeAlong(Across);
        if (A <= Plunge || A >= Boil)
        {
            return 0.0;
        }
        const double Height = HeightM * Intensity * Lat;
        if (A < Crest)
        {
            return Height * FMath::SmoothStep(Plunge, Crest - 0.3 * ThrowM * Lat, A);
        }
        return Height * (1.0 - FMath::Pow((A - Crest) / (Boil - Crest), 1.6));
    }
};

/** The trough's lowest water: the least of the water on the centre line
 * where the front lands, under the lip and under the crest. WaterAt gives
 * the water's surface (m) Along the centre line, false where dry. */
inline bool ToeM(const FShape& Shape, TFunctionRef<bool(double Along, double& OutWaterM)> WaterAt, double& OutToeM)
{
    const double Plunge = Shape.PlungeAlong(), Crest = Shape.CrestAlong();
    bool bAny = false;
    OutToeM = TNumericLimits<double>::Max();
    for (const double Along : {Plunge, 0.5 * (Plunge + Crest), Crest})
    {
        double WaterM = 0.0;
        if (WaterAt(Along, WaterM))
        {
            OutToeM = FMath::Min(OutToeM, WaterM);
            bAny = true;
        }
    }
    return bAny;
}

/** What the hull meets at a point. */
struct FHullWater
{
    /** The surface it floats on: the water, or the pile where it stands higher. */
    double SurfaceM = 0.0;
    FVector VelocityMps = FVector::ZeroVector;
    /** Slope of the pile's rise over the water (world X, Y): the hull is
     * pushed down it. Zero off the pile. */
    FVector2D Slope = FVector2D::ZeroVector;
};

/**
 * The hull's water at a point Along/Across of a hole, PointZM high, where the
 * water's own surface is WaterM and velocity BaseVelocityMps, and the
 * trough's lowest water is ToeM. Downstream3/Across3 are the hole's flow
 * frame in world space (horizontal, unit). Returns false off the pile, with
 * Out holding the water unchanged.
 *
 * The white water is mostly air: a hull sinks into it rather than riding up
 * on it, and the water running back upstream in the roller under it is what
 * stops a boat. Riding high on a pile that bore it like solid water, a
 * drifting raft's bow stood up and the stern, still in the current, walked
 * it over the top.
 */
inline bool Apply(const FShape& Shape, double Along, double Across, double PointZM, double ToeM, double WaterM,
    const FVector& BaseVelocityMps, const FVector& Downstream3, const FVector& Across3, FHullWater& Out)
{
    Out.SurfaceM = WaterM;
    Out.VelocityMps = BaseVelocityMps;
    Out.Slope = FVector2D::ZeroVector;
    const double AboveToe = Shape.TopAboveToe(Along, Across);
    if (AboveToe <= 0.0)
    {
        return false;
    }
    const double Rise = Shape.BearingFraction * (ToeM + AboveToe - WaterM);
    constexpr double Step = 0.05;
    const double AlongRise = (Shape.TopAboveToe(Along + Step, Across) - Shape.TopAboveToe(Along - Step, Across)) / (2.0 * Step);
    if (Rise > 0.0)
    {
        Out.SurfaceM = WaterM + Rise;
        // The pile's slope, from its own shape: steep up its front, gently
        // down its back.
        const double AcrossRise = (Shape.TopAboveToe(Along, Across + Step) - Shape.TopAboveToe(Along, Across - Step)) / (2.0 * Step);
        const FVector World = (Downstream3 * AlongRise + Across3 * AcrossRise) * Shape.BearingFraction;
        Out.Slope = FVector2D(World.X, World.Y);
    }
    // Its water rolls upstream along its top (up the back, over the crest,
    // down the front) and runs back upstream under it. Deeper than that the
    // hole's own current takes over.
    const FVector Rolling = (-Downstream3 - FVector::UpVector * AlongRise).GetSafeNormal() *
        (Shape.RollMps * Shape.Intensity * Shape.Lateral(Across)) + Across3 * FVector::DotProduct(BaseVelocityMps, Across3);
    const double InRoller = FMath::SmoothStep(WaterM - Shape.ReturnDepthM, WaterM - 0.5 * Shape.ReturnDepthM, PointZM);
    Out.VelocityMps = FMath::Lerp(BaseVelocityMps, Rolling, InRoller);
    return true;
}
}
