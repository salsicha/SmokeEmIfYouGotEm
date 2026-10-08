#pragma once

#include "CoreMinimal.h"

/**
 * The water falling over a hole's pour-over, as the hull feels it.
 *
 * Water going over a hole's crest falls into the trough. Like any falling
 * sheet it keeps the speed U it came over the crest with and gains only
 * downward speed from the drop, sqrt(2 g dh): it drives what it lands on
 * down, at sqrt(U^2 + 2 g dh) in all. Below the trough the hole's breaking
 * wave rolls back upstream at the surface (RaftSimHoleWave.h), so a raft
 * without way on is stopped there and pushed back into this falling water.
 * A tube under it is driven down, and anyone sitting there is hit by it. The
 * raft's own drag, upper-face and swamping loads do the rest: no force,
 * torque or flip is prescribed here.
 *
 * The drop is measured on the water surface the hull already floats on (the
 * surface at the crest of the same flow line against the surface here), so
 * the falling water is exactly as strong as the rendered and supporting
 * surface says the water falls, and absent where that surface is flat.
 */
namespace RaftSimHolePourOver
{
/** One hole's pour-over in a horizontal frame, in metres. */
struct FSite
{
    /** Where the water goes over, on the centre line. */
    FVector2D CrestM = FVector2D::ZeroVector;
    /** Unit vector downstream. */
    FVector2D Downstream = FVector2D(1.0, 0.0);
    /** From the crest to the foot of the face, along the flow. */
    double FaceLengthM = 1.9;
    /** The crest bows downstream away from the centre line: the face starts
     * this many metres per square metre across further downstream. */
    double CrestBowPerSquareMeter = 0.035;
    /** No falling water beyond this far either side of the centre line. */
    double HalfWidthM = 12.0;

    /** A hole whose crest the hull's surface relief draws from its physical
     * height and length: the face runs to the toe of that relief. */
    static FSite FromCrestLength(const FVector2D& CrestM, const FVector2D& Downstream, double CrestLengthM)
    {
        FSite Site;
        Site.CrestM = CrestM;
        Site.Downstream = Downstream.GetSafeNormal();
        Site.FaceLengthM = 0.95 * FMath::Clamp(CrestLengthM, 2.0, 7.0);
        return Site;
    }
};

/** Thickness of the falling sheet: points deeper than this below the
 * surface keep the water's own flow. */
constexpr double SheetThicknessM = 0.6;

/** Water surface height (m) and velocity (m/s) at a horizontal point (m). */
using FSampleAt = TFunctionRef<bool(const FVector2D& PointM, double& OutSurfaceM, FVector& OutVelocityMps)>;

/**
 * The velocity of the water at PointM (metres, Z up), given the water's own
 * velocity there (BaseVelocityMps) and its surface height (SurfaceHereM).
 * Outside the face, or where the surface does not drop, returns the base
 * velocity unchanged. Downstream3 is the site's downstream direction in the
 * same 3D frame as the velocities (horizontal, unit), Across3 its left.
 */
inline FVector Velocity(const FSite& Site, const FVector& PointM, const FVector& BaseVelocityMps,
    double SurfaceHereM, const FVector& Downstream3, const FVector& Across3, FSampleAt SampleAt)
{
    const FVector2D Relative = FVector2D(PointM.X, PointM.Y) - Site.CrestM;
    const FVector2D Left(-Site.Downstream.Y, Site.Downstream.X);
    const double Across = FVector2D::DotProduct(Relative, Left);
    const double Bow = Site.CrestBowPerSquareMeter * Across * Across;
    const double Along = FVector2D::DotProduct(Relative, Site.Downstream) - Bow;
    if (FMath::Abs(Across) > Site.HalfWidthM || Along <= 0.0 || Along >= 1.15 * Site.FaceLengthM)
    {
        return BaseVelocityMps;
    }
    // Falling water fills the sheet down from the surface; deeper water and
    // anything above the surface (a tube top, a paddler) meet it at its top.
    const double Depth = SurfaceHereM - PointM.Z;
    const double InSheet = 1.0 - FMath::SmoothStep(SheetThicknessM, SheetThicknessM + 0.3, Depth);
    if (InSheet <= 0.0)
    {
        return BaseVelocityMps;
    }
    double CrestSurfaceM = 0.0;
    FVector CrestVelocityMps = FVector::ZeroVector;
    const FVector2D CrestPointM = Site.CrestM + Site.Downstream * Bow + Left * Across;
    if (!SampleAt(CrestPointM, CrestSurfaceM, CrestVelocityMps))
    {
        return BaseVelocityMps;
    }
    const double DropM = CrestSurfaceM - SurfaceHereM;
    // A face too low to fall is just water.
    const double Falls = FMath::SmoothStep(0.05, 0.2, DropM);
    if (Falls <= 0.0)
    {
        return BaseVelocityMps;
    }
    const double ApproachMps = FMath::Max(FVector::DotProduct(CrestVelocityMps, Downstream3), 0.0);
    // Free fall from the crest: the speed it came over with, and down. Sent
    // down the face at full speed instead, it shoved a raft in the trough
    // back out of the hole rather than driving its tube under. Across the
    // flow the water keeps its own speed.
    const FVector Falling = Downstream3 * ApproachMps - FVector::UpVector * FMath::Sqrt(2.0 * 9.81 * DropM) +
        Across3 * FVector::DotProduct(BaseVelocityMps, Across3);
    // Over the crest the sheet gathers. At the foot of the face it dives
    // under the breaking wave's pile (RaftSimHoleWave.h), whose own water
    // rolls back upstream on top: carried on along the surface, the sheet
    // swept a stopped raft straight through the hole.
    const double OnFace = FMath::SmoothStep(0.0, 0.15 * Site.FaceLengthM, Along) *
        (1.0 - FMath::SmoothStep(Site.FaceLengthM, 1.15 * Site.FaceLengthM, Along));
    return FMath::Lerp(BaseVelocityMps, Falling, Falls * OnFace * InSheet);
}
}
