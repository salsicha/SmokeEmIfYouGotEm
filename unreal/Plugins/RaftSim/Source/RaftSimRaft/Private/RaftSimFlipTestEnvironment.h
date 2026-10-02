#pragma once
#include "CoreMinimal.h"

// Authored laboratory waves, not surveyed hydraulics or a solved fluid field.
// Rendering and production hull samplers consume this exact moving surface.
namespace RaftSimFlipTestEnvironment
{
struct FScene
{
    FString Name;
    double AmplitudeM=0.,WidthM=1.,SpeedMps=2.,AngleRadians=PI*.5;
    bool bShear=false;
    bool bHydraulic=false,bObstacle=false;
    double BreakingJetMps=0.;
    bool bPinnedBreaker=false;
    // Explicit initial-condition controls, not a claim that the authored
    // field generated this incoming roll. Native forces own all later motion.
    double InitialRollDegrees=0.,InitialRollRateRadS=0.;
    bool bPillowRock=false;
    double PillowCurrentMps=8.;
    bool Wet(const FVector& P) const
    {return !bObstacle || FMath::Abs(P.X)>60. || FMath::Abs(P.Y)>120.;}
    double Surface(const FVector& P,double Seconds) const
    {
        const double Along=(P.X*FMath::Cos(AngleRadians)+P.Y*FMath::Sin(AngleRadians))*.01;
        // Stationary upstream pillow at a sloped, bed-connected rock. This is
        // an authored qualitative control, not measured rock hydraulics.
        if(bPillowRock)return (PillowCurrentMps>0. ? .8 : 0.)*FMath::Exp(-FMath::Square((P.X*.01+.6)/1.25)-FMath::Square(P.Y*.01/3.));
        if(bPinnedBreaker)return .9*FMath::Exp(-FMath::Square((Along+2.6)/.9));
        if(bHydraulic)return .55*FMath::Exp(-FMath::Square((Along+1.)/.7))-.45*FMath::Exp(-FMath::Square((Along-1.)/.7));
        const double WaveCenter=-6.+SpeedMps*FMath::Max(Seconds-2.,0.);
        if(Seconds<2. || Seconds>9.)return 0.;
        const double Envelope=FMath::Clamp((Seconds-2.)/.5,0.,1.)*FMath::Clamp((9.-Seconds)/.5,0.,1.);
        return AmplitudeM*Envelope*FMath::Exp(-.5*FMath::Square((Along-WaveCenter)/WidthM));
    }
    FVector Velocity(const FVector& P,double Seconds) const
    {
        if(bShear)return FVector(1.5*FMath::Tanh(P.Y*.01/.7),0,0);
        if(bHydraulic)
        {
            const double Along=(P.X*FMath::Cos(AngleRadians)+P.Y*FMath::Sin(AngleRadians))*.01;
            // Finite-depth 2-D streamfunction psi=Q*s+A(x)*s^2*(1-s).
            // Constant psi at the bed and stationary surface makes both
            // impermeable. The old depth-independent downflow could drag
            // even a fully submerged inflated raft indefinitely downward.
            constexpr double Bed=-2.,Q=7.,Eps=.001;
            const double Height=Surface(P,Seconds),Depth=Height-Bed;
            const FVector Axis(FMath::Cos(AngleRadians),FMath::Sin(AngleRadians),0.);
            const double S=FMath::Clamp((P.Z*.01-Bed)/Depth,0.,1.);
            const double Hx=(Surface(P+Axis*(100.*Eps),Seconds)-Surface(P-Axis*(100.*Eps),Seconds))/(2.*Eps);
            const double A=11.*FMath::Exp(-FMath::Square(Along/1.1));
            const double Ax=-2.*Along/(1.1*1.1)*A;
            const double F=S*S*(1.-S),DF=2.*S-3.*S*S;
            const double U=(Q+A*DF)/Depth;
            const double W=U*S*Hx-Ax*F;
            return FVector(FMath::Cos(AngleRadians)*U,FMath::Sin(AngleRadians)*U,W);
        }
        if(bObstacle)
        {
            if(!Wet(P))return FVector::ZeroVector;
            const double X=P.X*.01,Y=P.Y*.01;
            const double Dx=FMath::Max(FMath::Abs(X)-.6,0.),Dy=FMath::Max(FMath::Abs(Y)-1.2,0.);
            const double D=FMath::Sqrt(Dx*Dx+Dy*Dy),S=FMath::Clamp(D/2.,0.,1.);
            const double F=S*S*S*(10.-15.*S+6.*S*S),DF=15.*S*S*(1.-S)*(1.-S);
            // Horizontal discharge streamfunction: no normal rock flux.
            // Dividing discharge by local depth and w=s*u.grad(H) supplies
            // an incompressible steady depth-column extension with bed and
            // surface tangency, not a solved turbulent breaker.
            const double Flux=2.*(bPillowRock ? PillowCurrentMps : (bPinnedBreaker ? 8. : 2.8)),Depth=Surface(P,Seconds)+2.;
            FVector V(Flux*(F+Y*DF*FMath::Sign(Y)*Dy/D)/Depth,
                -Flux*Y*DF*FMath::Sign(X)*Dx/D/Depth,0.);
            constexpr double Eps=.001;
            const double Hx=(Surface(P+FVector(Eps*100,0,0),Seconds)-Surface(P-FVector(Eps*100,0,0),Seconds))/(2.*Eps);
            const double Hy=(Surface(P+FVector(0,Eps*100,0),Seconds)-Surface(P-FVector(0,Eps*100,0),Seconds))/(2.*Eps);
            V.Z=FMath::Clamp((P.Z*.01+2.)/Depth,0.,1.)*(V.X*Hx+V.Y*Hy);
            return V;
        }
        // Linear long-wave orbital velocity: perturbation carried with crest,
        // vertical component is its time derivative. Finite authored control,
        // not a claim of nonlinear breaking-wave conservation.
        constexpr double Eps=.001;
        const double H=Surface(P,Seconds);
        const double Vertical=(Surface(P,Seconds+Eps)-Surface(P,Seconds-Eps))/(2.*Eps);
        const double Jet=AmplitudeM>0. ? BreakingJetMps*H/AmplitudeM : 0.;
        return FVector(FMath::Cos(AngleRadians),FMath::Sin(AngleRadians),0)*(SpeedMps*H/2.+Jet)+FVector(0,0,Vertical);
    }
};
inline TArray<FScene> Scenes()
{
    return {{TEXT("calm")},
        {TEXT("small_broadside"),.25,1.4,2.,PI*.5},
        {TEXT("large_broadside"),1.6,.65,3.,PI*.5},
        {TEXT("large_broadside_mirror"),1.6,.65,3.,-PI*.5},
        {TEXT("large_bow_on"),1.6,.65,3.,0.},
        {TEXT("eddy_line"),0.,1.,2.,PI*.5,true},
        {TEXT("hydraulic_broadside"),0.,1.,2.,PI*.5,false,true},
        {TEXT("rock_oblique"),0.,1.,2.,0.,false,false,true},
        {TEXT("breaking_broadside"),1.6,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_mirror"),1.6,.65,3.,-PI*.5,false,false,false,5.6},
        // Upright-start severity controls. Only the visible crest height changes;
        // pressure law, drag, loading, initial angular momentum and gates do not.
        // Authored extreme waves, not measured real-river flip thresholds.
        {TEXT("breaking_broadside_1p8m"),1.8,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_2m"),2.,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_2p4m"),2.4,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_2p4m_mirror"),2.4,.65,3.,-PI*.5,false,false,false,5.6},
        {TEXT("breaking_bow_on_2p4m"),2.4,.65,3.,0.,false,false,false,5.6},
        {TEXT("breaking_broadside_2p8m"),2.8,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_3p2m"),3.2,.65,3.,PI*.5,false,false,false,5.6},
        {TEXT("breaking_broadside_3p2m_mirror"),3.2,.65,3.,-PI*.5,false,false,false,5.6},
        {TEXT("breaking_bow_on_3p2m"),3.2,.65,3.,0.,false,false,false,5.6},
        {TEXT("pinned_breaker"),0.,1.,2.,0.,false,false,true,0.,true},
        {TEXT("rock_pillow_broadside"),0.,1.,2.,0.,false,false,true,0.,false,0.,0.,true,8.},
        {TEXT("rock_pillow_calm"),0.,1.,2.,0.,false,false,true,0.,false,0.,0.,true,0.},
        {TEXT("rolling_entry_control"),0.,1.,2.,PI*.5,false,false,false,0.,false,30.,.5},
        {TEXT("rolling_entry_port"),0.,1.,2.,PI*.5,false,false,false,0.,false,75.,5.},
        {TEXT("rolling_entry_starboard"),0.,1.,2.,PI*.5,false,false,false,0.,false,-75.,-5.}};
}
}
