#pragma once
#include "RaftSimCrewStateContracts.h"

// Reduced PFD resurfacing candidate. Native rescue metadata is retained;
// release momentum is not overwritten by the Eulerian current. The 0.8 m/s2
// net buoyant acceleration and 2/s wet drag are authored, not measured kit.
inline FRaftSimSwimmerRescueFrame RaftSimAdvanceSubmergedSwimmer(
    const FRaftSimSwimmerRescueFrame& Current,const FVector& WaterVelocity,
    double SurfaceM,double Dt)
{
    auto Next=URaftSimSwimmerRescueLibrary::IntegrateSwimmerDrift(Current,WaterVelocity,float(Dt));
    if(!FMath::IsFinite(SurfaceM) || !FMath::IsFinite(Dt) || Dt<=0. || Dt>.25 ||
       WaterVelocity.ContainsNaN() || Current.SwimmerWorldPositionMeters.ContainsNaN() ||
       Current.SwimmerDriftVelocityMetersPerSecond.ContainsNaN())return Current;
    FVector P=Current.SwimmerWorldPositionMeters,V=Current.SwimmerDriftVelocityMetersPerSecond;
    const int32 Steps=FMath::CeilToInt(Dt*120.);const double H=Dt/Steps;
    for(int32 I=0;I<Steps;++I)
    {
        const bool Floating=Current.TimeInWaterSeconds>0. && FMath::Abs(P.Z-SurfaceM)<.002 && V.Z>=WaterVelocity.Z;
        const bool Below=P.Z<SurfaceM;
        const double Drag=Below || Floating ? 2. : .1;
        const FVector A(0,0,Floating ? 0. : (Below ? .8 : -9.80665));
        const double E=FMath::Exp(-Drag*H);
        const FVector Equilibrium=WaterVelocity+A/Drag;
        const FVector Before=P;
        P+=Equilibrium*H+(V-Equilibrium)*((1.-E)/Drag);
        V=Equilibrium+(V-Equilibrium)*E;
        if(Floating || (Before.Z<SurfaceM && P.Z>=SurfaceM && V.Z>WaterVelocity.Z))
        {P.Z=SurfaceM;V.Z=WaterVelocity.Z;}
    }
    Next.SwimmerWorldPositionMeters=P;Next.SwimmerDriftVelocityMetersPerSecond=V;
    return Next;
}
