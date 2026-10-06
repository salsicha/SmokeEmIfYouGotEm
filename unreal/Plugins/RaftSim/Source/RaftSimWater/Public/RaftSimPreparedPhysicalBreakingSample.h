#pragma once
#include "RaftSimPhysicalBreakingSample.h"

// Immutable per-profile constants only. Keep each original float multiply,
// division, exponential and ordered sum; never replace division by a reciprocal.
namespace RaftSimPreparedPhysicalBreakingSample
{
struct FSite
{
    FVector2D Origin,Direction;
    float Lift,Length,Low,LowFade,HighFade,High,DownWidth,LateralWidth;
    float ToeCenter,ToeWidth,TailACenter,TailAWidth,TailBCenter,Spilling;
    bool LocalCap;
    explicit FSite(const URaftSimWaterRuntimeAdapter::FSupportBreakingSite& S)
        : Origin(S.RiverCoordinatesMeters),Direction(S.FlowDirection),
          Lift(FMath::Clamp(S.PhysicalCrestHeightMeters,0.f,1.2f)),
          Length(FMath::Clamp(S.PhysicalCrestLengthMeters,2.f,7.f)),
          Low(-3.f*Length),LowFade(-2.f*Length),HighFade(6.f*Length),High(7.f*Length),
          DownWidth(.42f*Length),LateralWidth(FMath::Clamp(Length,3.f,5.f)),
          ToeCenter(.95f*Length),ToeWidth(.5f*Length),TailACenter(2.8f*Length),
          TailAWidth(.75f*Length),TailBCenter(5.1f*Length),
          Spilling(FMath::Clamp(S.SpillingFraction,0.f,1.f)),LocalCap(S.bLocalEnvelopeCap) {}
};

template<bool WithFoam>
float Evaluate(const FVector2D& P,TConstArrayView<FSite> Sites,float GlobalCap,float* Foam)
{
    if constexpr(WithFoam)*Foam=0.f;
    float Total=0.f,Cap=GlobalCap;
    for(const auto& S:Sites)
    {
        const FVector2D Relative=RaftSimWaterFlowFrame::ToLocal(P-S.Origin,S.Direction);
        if(!S.LocalCap)Cap=FMath::Max(Cap,S.Lift);
        const float Across=Relative.Y,Downstream=Relative.X;
        if((S.Lift<=0.f && !WithFoam) || FMath::Abs(Across)>12.f || Downstream<S.Low || Downstream>S.High)continue;
        const float Along=Downstream-.035f*Across*Across;
        const float Width=Along<0.f ? S.Length : S.DownWidth;
        const float Crest=FMath::Exp(-FMath::Square(Along/Width));
        const float Edge=FMath::SmoothStep(S.Low,S.LowFade,Downstream)*(1.f-FMath::SmoothStep(S.HighFade,S.High,Downstream));
        const float Lateral=FMath::Exp(-FMath::Square(Across/S.LateralWidth))*(1.f-FMath::SmoothStep(10.f,12.f,FMath::Abs(Across)));
        const float Toe=.32f*FMath::Exp(-FMath::Square((Along-S.ToeCenter)/S.ToeWidth));
        const float TailA=.35f*FMath::Exp(-FMath::Square((Along-S.TailACenter)/S.TailAWidth));
        const float TailB=.16f*FMath::Exp(-FMath::Square((Along-S.TailBCenter)/S.Length));
        if(S.LocalCap)Cap=FMath::Max(Cap,S.Lift*Edge*Lateral);
        Total+=S.Lift*(Crest-Toe+TailA+TailB)*Edge*Lateral;
        if constexpr(WithFoam)*Foam=FMath::Max(*Foam,.85f*FMath::SmoothStep(.65f,.95f,Crest)*Edge*Lateral*S.Spilling);
    }
    return FMath::Clamp(Total,-Cap,Cap);
}
}
