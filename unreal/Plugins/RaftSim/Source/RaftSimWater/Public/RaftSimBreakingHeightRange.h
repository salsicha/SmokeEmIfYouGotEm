#pragma once
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"

// Conservative range width of the existing physical crest over a rectangle.
// The range contains zero: positive crest/tails and negative toe are bounded
// separately, so the final local/global owner clamp cannot enlarge it. This
// never returns a replacement height. Unsupported input disables the shortcut.
namespace RaftSimBreakingHeightRange
{
inline float WidthMeters(TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites,
    const FBox2D& Bounds)
{
    if(!Bounds.bIsValid || Bounds.Min.ContainsNaN() || Bounds.Max.ContainsNaN())return MAX_flt;
    const FVector2D Center=Bounds.GetCenter(),Half=Bounds.GetExtent();
    double Sum=0.;
    const auto Nearest=[](double Low,double High)
    {return Low>0. ? Low : (High<0. ? -High : 0.);};
    const auto Gaussian=[&](double Low,double High,double Offset,float Scale)
    {
        const double Distance=Nearest(Low-Offset,High-Offset)/double(Scale);
        return FMath::Exp(-Distance*Distance);
    };
    for(const auto& Site:Sites)
    {
        const double Norm=Site.FlowDirection.SizeSquared();
        if(!FMath::IsFinite(Site.PhysicalCrestHeightMeters) || Site.PhysicalCrestHeightMeters<0.f ||
            !FMath::IsFinite(Site.PhysicalCrestLengthMeters) || Site.RiverCoordinatesMeters.ContainsNaN() ||
            !FMath::IsFinite(Norm) || Norm<.25 || Norm>4.)return MAX_flt;
        const float Lift=FMath::Clamp(Site.PhysicalCrestHeightMeters,0.f,1.2f);
        if(Lift==0.f)continue;
        const float L=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
        const FVector2D Local=RaftSimWaterFlowFrame::ToLocal(Center-Site.RiverCoordinatesMeters,Site.FlowDirection);
        const double DRadius=FMath::Abs(Site.FlowDirection.X)*Half.X+FMath::Abs(Site.FlowDirection.Y)*Half.Y;
        const double ARadius=FMath::Abs(Site.FlowDirection.Y)*Half.X+FMath::Abs(Site.FlowDirection.X)*Half.Y;
        // Cover double coordinate arithmetic, float conversion, and the
        // profile's float quadratic bend before bounding each exponential.
        const double Pad=1.e-5*(1.+FMath::Abs(Local.X)+FMath::Abs(Local.Y)+DRadius+ARadius)+
            1.e-12*(Center.GetAbsMax()+Site.RiverCoordinatesMeters.GetAbsMax());
        const double DLow=Local.X-DRadius-Pad,DHigh=Local.X+DRadius+Pad;
        const double ALow=Local.Y-ARadius-Pad,AHigh=Local.Y+ARadius+Pad;
        if(DHigh<-3.f*L || DLow>7.f*L || ALow>12.f || AHigh<-12.f)continue;
        const double AMin=Nearest(ALow,AHigh),AMax=FMath::Max(FMath::Abs(ALow),FMath::Abs(AHigh));
        const double BendPad=Pad*(1.+AMax);
        const double Low=DLow-double(.035f)*AMax*AMax-BendPad;
        const double High=DHigh-double(.035f)*AMin*AMin+BendPad;
        // On the rising half the Gaussian width is L; on the falling half
        // it is .42*L. If the interval crosses zero its maximum is exactly 1.
        const double Crest=Low<=0. && High>=0. ? 1. : Gaussian(Low,High,0.,High<0. ? L : .42f*L);
        const double Toe=.32f*Gaussian(Low,High,.95f*L,.5f*L);
        const double TailA=.35f*Gaussian(Low,High,2.8f*L,.75f*L);
        const double TailB=.16f*Gaussian(Low,High,5.1f*L,L);
        const double Lateral=FMath::Exp(-FMath::Square(AMin/double(FMath::Clamp(L,3.f,5.f))));
        // Smooth edge envelopes are in [0,1]; omitting them is conservative.
        // Relative/absolute cushions cover float exp/product/sum rounding.
        Sum+=double(Lift)*(Crest+Toe+TailA+TailB)*Lateral*1.0001+1.e-6;
        if(!FMath::IsFinite(Sum) || Sum>MAX_flt/2.)return MAX_flt;
    }
    return float(Sum*1.0001+1.e-6);
}
}
