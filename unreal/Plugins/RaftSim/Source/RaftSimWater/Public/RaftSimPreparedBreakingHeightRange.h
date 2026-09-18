#pragma once
#include "RaftSimBreakingHeightRange.h"

// Immutable preparation only. Queries retain the reference arithmetic and
// original site order; no range, height, coordinate or profile-age approximation.
class FRaftSimPreparedBreakingHeightRange
{
    struct FSite
    {
        FVector2D RiverCoordinatesMeters,FlowDirection,AbsDirection;
        double CoordinateMagnitude,LateralWidth;
        float Lift,Length;
        bool bLocalCap;
    };
    TArray<FSite> Sites;
    bool bValid=true;
    float GlobalCap=0.f;
    // Query centers inside this finite domain and half extents <= 8 m have
    // a bounded reference roundoff pad. Other queries use the full scan.
    FBox2D QueryDomain=FBox2D(ForceInit);
    TArray<TArray<FSite>> Tiles;
    FIntPoint TileOrigin=FIntPoint::ZeroValue,TileSize=FIntPoint::ZeroValue;
    bool bIndexed=false;
    void BuildIndex()
    {
        if(Sites.IsEmpty())return;
        for(const auto& S:Sites)QueryDomain+=S.RiverCoordinatesMeters;
        QueryDomain=QueryDomain.ExpandBy(256.);
        const double Magnitude=FMath::Max(QueryDomain.Min.GetAbsMax(),QueryDomain.Max.GetAbsMax());
        if(!FMath::IsFinite(Magnitude) || Magnitude>1.e8)return;
        const FVector2D Center=QueryDomain.GetCenter(),Half=QueryDomain.GetExtent();
        TArray<FIntPoint> Lows,Highs;
        FIntPoint Low(MAX_int32,MAX_int32),High(MIN_int32,MIN_int32);
        int64 Entries=0;
        for(const auto& S:Sites)
        {
            if(S.Lift==0.f){Lows.Emplace(0,0);Highs.Emplace(-1,-1);continue;}
            const FVector2D Local=RaftSimWaterFlowFrame::ToLocal(Center-S.RiverCoordinatesMeters,S.FlowDirection);
            const double DRadius=S.AbsDirection.X*Half.X+S.AbsDirection.Y*Half.Y;
            const double ARadius=S.AbsDirection.Y*Half.X+S.AbsDirection.X*Half.Y;
            const double QueryRadius=8.*(S.AbsDirection.X+S.AbsDirection.Y);
            // Upper-bound EVERY reference pad for eligible query rectangles.
            // The extra margins cover index construction/inversion roundoff;
            // they enlarge candidate membership only, never the range value.
            const double Pad=(1.e-5*(1.+FMath::Abs(Local.X)+FMath::Abs(Local.Y)+DRadius+ARadius+2.*QueryRadius)
                +1.e-12*(Magnitude+S.CoordinateMagnitude))*1.01+.001;
            FBox2D Support(ForceInit);
            const double Norm=S.FlowDirection.SizeSquared();
            // Match the reference's TWO independent projected-interval
            // tests, including their false-positive corner intersections.
            // Bounding only actual rectangle/support intersection would drop
            // some reference roundoff cushions and change the returned width.
            for(double D:{double(-3.f*S.Length)-Pad-QueryRadius,double(7.f*S.Length)+Pad+QueryRadius})
                for(double A:{-12.-Pad-QueryRadius,12.+Pad+QueryRadius})
                    Support+=S.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),S.FlowDirection)/Norm;
            Support=Support.ExpandBy(.01); // Index arithmetic only, not range values.
            const FIntPoint A(FMath::FloorToInt(Support.Min.X/8.),FMath::FloorToInt(Support.Min.Y/8.));
            const FIntPoint B(FMath::FloorToInt(Support.Max.X/8.),FMath::FloorToInt(Support.Max.Y/8.));
            Entries+=(int64(B.X)-A.X+1)*(int64(B.Y)-A.Y+1);
            if(Entries>65536)return;
            Lows.Add(A);Highs.Add(B);
            Low.X=FMath::Min(Low.X,A.X);Low.Y=FMath::Min(Low.Y,A.Y);
            High.X=FMath::Max(High.X,B.X);High.Y=FMath::Max(High.Y,B.Y);
        }
        if(!Entries){bIndexed=true;return;}
        const int64 Width=int64(High.X)-Low.X+1,Height=int64(High.Y)-Low.Y+1;
        if(Width*Height>65536)return;
        TileOrigin=Low;TileSize=FIntPoint(int32(Width),int32(Height));
        Tiles.SetNum(int32(Width*Height));
        for(int32 I=0;I<Sites.Num();++I)
            for(int32 Y=Lows[I].Y;Y<=Highs[I].Y;++Y)for(int32 X=Lows[I].X;X<=Highs[I].X;++X)
                Tiles[(Y-Low.Y)*TileSize.X+X-Low.X].Add(Sites[I]);
        bIndexed=true; // Every subset preserves original accumulation order.
    }
public:
    bool IsIndexed() const{return bIndexed;}
    explicit FRaftSimPreparedBreakingHeightRange(
        TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Input)
    {
        Sites.Reserve(Input.Num());
        for(const auto& S:Input)
        {
            const double Norm=S.FlowDirection.SizeSquared();
            if(!FMath::IsFinite(S.PhysicalCrestHeightMeters) || S.PhysicalCrestHeightMeters<0.f ||
                !FMath::IsFinite(S.PhysicalCrestLengthMeters) || S.RiverCoordinatesMeters.ContainsNaN() ||
                !FMath::IsFinite(Norm) || Norm<.25 || Norm>4.)
            {bValid=false;Sites.Reset();return;}
            const float Length=FMath::Clamp(S.PhysicalCrestLengthMeters,2.f,7.f);
            if(!S.bLocalEnvelopeCap)GlobalCap=FMath::Max(GlobalCap,FMath::Clamp(S.PhysicalCrestHeightMeters,0.f,1.2f));
            Sites.Add({S.RiverCoordinatesMeters,S.FlowDirection,
                FVector2D(FMath::Abs(S.FlowDirection.X),FMath::Abs(S.FlowDirection.Y)),
                S.RiverCoordinatesMeters.GetAbsMax(),double(FMath::Clamp(Length,3.f,5.f)),
                FMath::Clamp(S.PhysicalCrestHeightMeters,0.f,1.2f),Length,S.bLocalEnvelopeCap});
        }
        BuildIndex();
    }
template<bool Tight=false>
float WidthMeters(const FBox2D& Bounds) const
{
    if(!bValid || !Bounds.bIsValid || Bounds.Min.ContainsNaN() || Bounds.Max.ContainsNaN())return MAX_flt;
    const FVector2D Center=Bounds.GetCenter(),Half=Bounds.GetExtent();
    const TArray<FSite>* Active=&Sites;
    static const TArray<FSite> Empty;
    if(bIndexed && Half.X>=0. && Half.Y>=0. && Half.X<=8. && Half.Y<=8. &&
        Center.X>=QueryDomain.Min.X && Center.Y>=QueryDomain.Min.Y &&
        Center.X<=QueryDomain.Max.X && Center.Y<=QueryDomain.Max.Y)
    {
        const int32 X=FMath::FloorToInt(Center.X/8.)-TileOrigin.X;
        const int32 Y=FMath::FloorToInt(Center.Y/8.)-TileOrigin.Y;
        Active=X>=0 && Y>=0 && X<TileSize.X && Y<TileSize.Y ? &Tiles[Y*TileSize.X+X] : &Empty;
    }
    double Sum=0.;
    double Lower=0.,Upper=0.,CapLower=GlobalCap,CapUpper=GlobalCap;
    const auto Nearest=[](double Low,double High)
    {return Low>0. ? Low : (High<0. ? -High : 0.);};
    const auto Gaussian=[&](double Low,double High,double Offset,float Scale)
    {
        const double Distance=Nearest(Low-Offset,High-Offset)/double(Scale);
        return FMath::Exp(-Distance*Distance);
    };
    for(const auto& Site:*Active)
    {
        const float Lift=Site.Lift,L=Site.Length;
        if(Lift==0.f)continue;
        const FVector2D Local=RaftSimWaterFlowFrame::ToLocal(Center-Site.RiverCoordinatesMeters,Site.FlowDirection);
        const double DRadius=Site.AbsDirection.X*Half.X+Site.AbsDirection.Y*Half.Y;
        const double ARadius=Site.AbsDirection.Y*Half.X+Site.AbsDirection.X*Half.Y;
        // Cover double coordinate arithmetic, float conversion, and the
        // profile's float quadratic bend before bounding each exponential.
        const double Pad=1.e-5*(1.+FMath::Abs(Local.X)+FMath::Abs(Local.Y)+DRadius+ARadius)+
            1.e-12*(Center.GetAbsMax()+Site.CoordinateMagnitude);
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
        const double Lateral=FMath::Exp(-FMath::Square(AMin/Site.LateralWidth));
        // Smooth edge envelopes are in [0,1]; omitting them is conservative.
        // Relative/absolute cushions cover float exp/product/sum rounding.
        Sum+=double(Lift)*(Crest+Toe+TailA+TailB)*Lateral*1.0001+1.e-6;
        if constexpr(Tight)
        {
            // Unlike the original zero-containing range, enclose the local
            // value of each signed term. All endpoints include the SAME input
            // and bend roundoff padding above. These bounds never replace a
            // sampled height or change an interpolation/selection tolerance.
            const auto GaussianMinimum=[](double A,double B,double Offset,float Scale)
            {
                const double Distance=FMath::Max(FMath::Abs(A-Offset),FMath::Abs(B-Offset))/double(Scale);
                return FMath::Exp(-Distance*Distance);
            };
            const auto CrestEnd=[&](double X)
            {const double Width=X<0. ? double(L) : double(.42f*L);return FMath::Exp(-FMath::Square(X/Width));};
            const double CrestMin=FMath::Min(CrestEnd(Low),CrestEnd(High));
            const double ToeMin=.32f*GaussianMinimum(Low,High,.95f*L,.5f*L);
            const double TailAMin=.35f*GaussianMinimum(Low,High,2.8f*L,.75f*L);
            const double TailBMin=.16f*GaussianMinimum(Low,High,5.1f*L,L);
            const auto Step=[](double A,double B,double X)
            {const double T=FMath::Clamp((X-A)/(B-A),0.,1.);return T*T*(3.-2.*T);};
            const double EdgeLow=Step(-3.f*L,-2.f*L,DLow)*(1.-Step(6.f*L,7.f*L,DHigh));
            const double EdgeHigh=Step(-3.f*L,-2.f*L,DHigh)*(1.-Step(6.f*L,7.f*L,DLow));
            const double LateralLow=FMath::Exp(-FMath::Square(AMax/Site.LateralWidth))*(1.-Step(10.,12.,AMax));
            const double LateralHigh=Lateral*(1.-Step(10.,12.,AMin));
            const double EnvelopeLow=FMath::Max(0.,EdgeLow*LateralLow-1.e-5);
            const double EnvelopeHigh=FMath::Min(1.,EdgeHigh*LateralHigh+1.e-5);
            const double WaveLow=CrestMin-Toe+TailAMin+TailBMin;
            const double WaveHigh=Crest-ToeMin+TailA+TailB;
            const double Products[]={WaveLow*EnvelopeLow,WaveLow*EnvelopeHigh,
                                     WaveHigh*EnvelopeLow,WaveHigh*EnvelopeHigh};
            double TermLow=Products[0],TermHigh=Products[0];
            for(int32 I=1;I<4;++I){TermLow=FMath::Min(TermLow,Products[I]);TermHigh=FMath::Max(TermHigh,Products[I]);}
            // Exp, smoothstep, float products and ordered float accumulation
            // all receive an explicit absolute/relative cushion. Cap and sum
            // dependence is deliberately discarded to enlarge the enclosure.
            const double Roundoff=double(Lift)*1.e-4+1.e-6;
            Lower+=double(Lift)*TermLow-Roundoff;
            Upper+=double(Lift)*TermHigh+Roundoff;
            if(Site.bLocalCap)
            {
                CapLower=FMath::Max(CapLower,FMath::Max(0.,double(Lift)*EnvelopeLow-Roundoff));
                CapUpper=FMath::Max(CapUpper,double(Lift)*EnvelopeHigh+Roundoff);
            }
        }
        if(!FMath::IsFinite(Sum) || Sum>MAX_flt/2.)return MAX_flt;
    }
    const float Original=float(Sum*1.0001+1.e-6);
    if constexpr(Tight)
    {
        // clamp(t,-c,c) is monotone in t, but not in c for both signs.
        // Its extrema on the interval product occur at these four corners.
        const double Low=FMath::Min(FMath::Clamp(Lower,-CapLower,CapLower),FMath::Clamp(Lower,-CapUpper,CapUpper));
        const double High=FMath::Max(FMath::Clamp(Upper,-CapLower,CapLower),FMath::Clamp(Upper,-CapUpper,CapUpper));
        const double Width=(High-Low)*1.0001+2.e-6;
        if(FMath::IsFinite(Width) && Width>=0.)return FMath::Min(Original,float(Width));
    }
    return Original;
}
};
