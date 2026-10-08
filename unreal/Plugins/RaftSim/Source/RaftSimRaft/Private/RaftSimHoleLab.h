#pragma once

#include "CoreMinimal.h"
#include "RaftSimHolePourOver.h"
#include "RaftSimHoleWave.h"
#include "RaftSimWaterFeatureKinematics.h"
#include "RaftSimWaterRuntimeAdapter.h"

/**
 * The test hole: by default a pour-over 0.8 m high whose face runs over 2 m,
 * across a 2 m/s current 1.8 m deep. It has the shared roller current, the water
 * falling over the crest and its breaking wave, as the game's hull water has
 * them. The crest is at the origin and the current runs along +X; positions
 * are world centimetres. Shared by the test tank (RaftSim.FeatureDemo hole)
 * and the hole tests, so both put a raft in the same hole.
 */
struct FRaftSimHoleLab
{
    static constexpr double CurrentMps = 2.0;
    static constexpr double DepthM = 1.8;

    URaftSimWaterRuntimeAdapter::FSupportBreakingSite Site;
    RaftSimHoleWave::FShape Wave;
    /** The trough's lowest water, under the wave. */
    double ToeM = 0.0;

    /** Wave: the breaking wave drawn (and felt) below the pour-over. */
    explicit FRaftSimHoleLab(const RaftSimHoleWave::FShape& InWave, float CrestHeightM = 0.8f, float CrestLengthM = 2.0f)
        : Wave(InWave)
    {
        Site.RiverCoordinatesMeters = FVector2D::ZeroVector;
        Site.Intensity = 1.0f;
        Site.PhysicalCrestHeightMeters = CrestHeightM;
        Site.PhysicalCrestLengthMeters = CrestLengthM;
        Site.SpillingFraction = 1.0f;
        Site.bLocalEnvelopeCap = true;
        RaftSimHoleWave::ToeM(Wave, [this](double Along, double& OutWaterM)
            { OutWaterM = SurfaceM(FVector(Along * 100.0, 0.0, 0.0)); return true; }, ToeM);
    }

    /** The water's surface: the crest relief the game's hull floats on. */
    double SurfaceM(const FVector& PointCm) const
    {
        const TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites = {Site};
        return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(PointCm.X * 0.01, PointCm.Y * 0.01), Sites, 1.0f, 0.25f);
    }
    /** The current with the shared roller; bSurface takes it at the surface. */
    FVector FlowMps(const FVector& PointCm, bool bSurface) const
    {
        const double Depth = SurfaceM(PointCm) + DepthM;
        const double Z = bSurface ? 1.0 : FMath::Clamp((PointCm.Z * 0.01 + DepthM) / Depth, 0.0, 1.0);
        return FVector(CurrentMps, 0.0, 0.0) +
            RaftSimWaterFeatureKinematics::HoleDelta(PointCm.X * 0.01, PointCm.Y * 0.01, Z, Depth, CurrentMps, 1.0);
    }
    /** The current with the water falling over the pour-over. */
    FVector VelocityMps(const FVector& PointCm, bool bSurface) const
    {
        const FVector Flow = FlowMps(PointCm, bSurface);
        const auto Face = RaftSimHolePourOver::FSite::FromCrestLength(FVector2D::ZeroVector, FVector2D(1.0, 0.0), Site.PhysicalCrestLengthMeters);
        const double Here = SurfaceM(PointCm);
        return RaftSimHolePourOver::Velocity(Face, bSurface ? FVector(PointCm.X * 0.01, PointCm.Y * 0.01, Here) : PointCm * 0.01, Flow, Here,
            FVector::ForwardVector, FVector::RightVector, [this](const FVector2D& Q, double& OutSurfaceM, FVector& OutVelocityMps)
            {
                const FVector Crest(Q.X * 100.0, Q.Y * 100.0, 0.0);
                OutSurfaceM = SurfaceM(Crest);
                OutVelocityMps = FlowMps(Crest, true);
                return true;
            });
    }
    /** What the hull floats on and is carried by: the water, the water
     * falling over the pour-over and the breaking wave's pile. */
    RaftSimHoleWave::FHullWater Hull(const FVector& PointCm) const
    {
        const double Water = SurfaceM(PointCm);
        const FVector Velocity = VelocityMps(PointCm, false);
        RaftSimHoleWave::FHullWater Out;
        RaftSimHoleWave::Apply(Wave, PointCm.X * 0.01, PointCm.Y * 0.01, PointCm.Z * 0.01, ToeM, Water, Velocity,
            FVector::ForwardVector, FVector::RightVector, Out);
        return Out;
    }
};
