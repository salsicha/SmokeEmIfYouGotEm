#pragma once
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"

// Specialize the already validated physical-only index path at its caller.
// Preserve the reference's float conversions, operation order and exp calls;
// this is NOT an approximation, new profile or new support cutoff. Legacy or
// invalid inputs must use ComputeCoupledBreakingReliefMeters instead.
namespace RaftSimPhysicalBreakingSample
{
template<bool WithFoam>
FORCEINLINE float Evaluate(const FVector2D& P,
    TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites,
    float GlobalCap,float* Foam)
{
    if constexpr(WithFoam)*Foam=0.f;
    float Total=0.f,Cap=GlobalCap;
    for(const auto& Site:Sites)
    {
        const FVector2D Relative=RaftSimWaterFlowFrame::ToLocal(P-Site.RiverCoordinatesMeters,Site.FlowDirection);
        const float Lift=FMath::Clamp(Site.PhysicalCrestHeightMeters,0.f,1.2f);
        const float Length=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
        if(!Site.bLocalEnvelopeCap)Cap=FMath::Max(Cap,Lift);
        const float Across=Relative.Y,Downstream=Relative.X;
        if((Lift<=0.f && !WithFoam) || FMath::Abs(Across)>12.f ||
            Downstream<-3.f*Length || Downstream>7.f*Length)continue;
        const float Along=Downstream-0.035f*Across*Across;
        const float Width=Along<0.f ? Length : 0.42f*Length;
        const float Crest=FMath::Exp(-FMath::Square(Along/Width));
        const float Edge=FMath::SmoothStep(-3.f*Length,-2.f*Length,Downstream)*
            (1.f-FMath::SmoothStep(6.f*Length,7.f*Length,Downstream));
        const float Lateral=FMath::Exp(-FMath::Square(Across/FMath::Clamp(Length,3.f,5.f)))*
            (1.f-FMath::SmoothStep(10.f,12.f,FMath::Abs(Across)));
        const float Toe=0.32f*FMath::Exp(-FMath::Square((Along-0.95f*Length)/(0.5f*Length)));
        const float TailA=0.35f*FMath::Exp(-FMath::Square((Along-2.8f*Length)/(0.75f*Length)));
        const float TailB=0.16f*FMath::Exp(-FMath::Square((Along-5.1f*Length)/Length));
        if(Site.bLocalEnvelopeCap)Cap=FMath::Max(Cap,Lift*Edge*Lateral);
        Total+=Lift*(Crest-Toe+TailA+TailB)*Edge*Lateral;
        if constexpr(WithFoam)
            *Foam=FMath::Max(*Foam,0.85f*FMath::SmoothStep(0.65f,0.95f,Crest)*Edge*Lateral*
                FMath::Clamp(Site.SpillingFraction,0.f,1.f));
    }
    return FMath::Clamp(Total,-Cap,Cap);
}
}
