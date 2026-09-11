#pragma once

#include "CoreMinimal.h"

/** Bounded, presentation-only Lagrangian fragments. Metres/seconds throughout.
 * The supplied carrier defines attachment; this is not a liquid-volume solver,
 * particle collision against arbitrary solids, or an added raft force. */
struct FRaftSimSecondaryWater
{
    static constexpr int32 Capacity = 128;
    static constexpr double StepSeconds = 1.0 / 60.0;
    static constexpr double Gravity = 9.80665;
    struct FCarrier
    {
        double HeightM = 0;
        FVector VelocityMps = FVector::ZeroVector;
        bool IsFinite() const { return FMath::IsFinite(HeightM) && !VelocityMps.ContainsNaN(); }
    };
    struct FParticle
    {
        FVector PositionM = FVector::ZeroVector;
        FVector PreviousPositionM = FVector::ZeroVector;
        FVector VelocityMps = FVector::ZeroVector;
        double Age = 0, FoamAge = 0;
        double RadiusM = 0.025;
        uint64 BirthId = 0;
        bool bAlive = false, bFoam = false;
    };
    using FSampler = TFunctionRef<bool(const FVector&, FCarrier&)>;
    FParticle Particles[Capacity];
    uint64 Spawned = 0, Returned = 0, Rejected = 0, Expired = 0;

    bool Spawn(const FVector& PositionM, const FVector& RelativeEjectionMps,
        double RadiusM, FSampler Sample)
    {
        FCarrier Carrier;
        if (PositionM.ContainsNaN() || RelativeEjectionMps.ContainsNaN() ||
            !FMath::IsFinite(RadiusM) || RadiusM <= 0 ||
            !Sample(PositionM, Carrier) || !Carrier.IsFinite()) return false;
        for (FParticle& P : Particles)
        {
            if (P.bAlive) continue;
            P = FParticle();
            // Birth state is latched, not recalculated from the emitter's
            // current transform on subsequent frames.
            P.PositionM = FVector(PositionM.X, PositionM.Y, Carrier.HeightM + RadiusM);
            P.PreviousPositionM = P.PositionM;
            P.VelocityMps = Carrier.VelocityMps + RelativeEjectionMps;
            P.RadiusM = RadiusM;
            P.BirthId = ++Spawned;
            P.bAlive = true;
            return true;
        }
        return false; // Saturation drops emission, never evicts living particles.
    }

    void Step(double Dt, FSampler Sample)
    {
        check(Dt > 0 && Dt <= StepSeconds + 1.e-9);
        for (FParticle& P : Particles)
        {
            if (!P.bAlive) continue;
            P.PreviousPositionM = P.PositionM;
            P.Age += Dt;
            if (P.Age >= 3.0 || (P.bFoam && P.FoamAge >= 0.8))
            { P.bAlive = false; ++Expired; continue; }
            FCarrier Before, After;
            if (!Sample(P.PositionM, Before) || !Before.IsFinite())
            { P.bAlive = false; ++Rejected; continue; }
            FVector Next;
            if (P.bFoam)
            {
                FCarrier Mid;
                const FVector MidPoint = P.PositionM + Before.VelocityMps * (Dt * 0.5);
                if (!Sample(MidPoint, Mid) || !Mid.IsFinite())
                { P.bAlive = false; ++Rejected; continue; }
                Next = P.PositionM + Mid.VelocityMps * Dt;
                P.VelocityMps = Mid.VelocityMps;
                P.FoamAge += Dt;
            }
            else
            {
                // Exact constant-gravity trajectory: no frame-rate-dependent
                // drag toward the changing emitter, no artificial upstream jet.
                Next = P.PositionM + P.VelocityMps * Dt - FVector(0, 0, 0.5 * Gravity * Dt * Dt);
                P.VelocityMps.Z -= Gravity * Dt;
            }
            if (!Sample(Next, After) || !After.IsFinite() || Next.ContainsNaN())
            { P.bAlive = false; ++Rejected; continue; }
            if (!P.bFoam && Next.Z - P.RadiusM <= After.HeightM)
            {
                P.bFoam = true;
                P.FoamAge = 0;
                P.VelocityMps = After.VelocityMps;
                ++Returned;
            }
            // Surface foam is advected at liquid speed. It protrudes by less
            // than a particle radius and shrinks continuously before expiry.
            if (P.bFoam) Next.Z = After.HeightM;
            P.PositionM = Next;
        }
    }

    int32 AliveCount() const
    {
        int32 Count = 0;
        for (const FParticle& P : Particles) Count += P.bAlive;
        return Count;
    }
};
