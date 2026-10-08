#pragma once
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFeatureKinematics.h"
#include "RaftSimRapidFeature.h"

// Authored gameplay reconstruction, NOT surveyed hydraulics or extra solver
// forcing. Positions follow the committed observed_rapids catalogues. These
// named features must share the existing render/foam/hull crest and roller
// kernels: never a boat-only force or a class-dependent flip probability.
// Sources: hance_observed_rapids.json (Emilio's / Giants / bottom hole) and
// batoka_run_observed_rapids.json (Director's / Crease / Land of the Giants).
namespace RaftSimRapidChallengeProfiles
{
using FFeature = FRaftSimRapidFeature;

inline bool IsValid(const FFeature& F)
{
    return FMath::IsFinite(F.Station) && FMath::IsFinite(F.Lateral) &&
        FMath::IsFinite(F.AngleDegrees) && FMath::IsFinite(F.Height) &&
        FMath::IsFinite(F.Length) && FMath::IsFinite(F.Spill) &&
        F.Height>0.f && F.Height<=1.2f && F.Length>=2.f && F.Length<=7.f &&
        F.Spill>=0.f && F.Spill<=1.f;
}

// Both adapters MUST already use the same geographic world origin/CRS.
// Transfer centre and physical orientation, not a constant station offset.
// Amplitude, wavelength, spilling and the shared kernel remain unchanged.
inline bool Register(const URaftSimWaterRuntimeAdapter& Source,
    const URaftSimWaterRuntimeAdapter& Target,const TArray<FFeature>& Input,
    TArray<FFeature>& Output,FString& Error)
{
    Output.Reset(); Error.Reset();
    if (!Source.HasRiverCoordinateMap() || !Target.HasRiverCoordinateMap() ||
        Source.HasCartesianWaterCoordinates() || Target.HasCartesianWaterCoordinates())
    { Error=TEXT("Rapid registration requires two curved coordinate charts");return false; }
    TArray<FFeature> Candidate;
    for(const auto& F:Input)
    {
        FVector Position,ST,SL,TT,TL,Check;
        FVector2D SourceRoundtrip,Registered;
        if(!IsValid(F) || !Source.RiverToWorldPosition({F.Station,F.Lateral},0.f,Position) ||
            !Source.WorldToRiverCoordinates(Position,SourceRoundtrip,ST,SL) ||
            !SourceRoundtrip.Equals({F.Station,F.Lateral},.0001) ||
            !Target.WorldToRiverCoordinates(Position,Registered,TT,TL) ||
            !Target.RiverToWorldPosition(Registered,0.f,Check) ||
            FVector::DistSquared2D(Position,Check)>1.)
        { Error=TEXT("Rapid feature is invalid, ambiguous or outside the target chart");return false; }
        const double Angle=FMath::DegreesToRadians(F.AngleDegrees);
        const FVector WorldDirection=ST*FMath::Cos(Angle)+SL*FMath::Sin(Angle);
        FFeature Moved=F;
        Moved.Station=Registered.X;Moved.Lateral=Registered.Y;
        Moved.AngleDegrees=FMath::RadiansToDegrees(FMath::Atan2(
            FVector::DotProduct(WorldDirection,TL),FVector::DotProduct(WorldDirection,TT)));
        if(!IsValid(Moved)) { Error=TEXT("Nonfinite registered rapid");return false; }
        Candidate.Add(Moved);
    }
    Output=MoveTemp(Candidate);return true;
}
// Conservative projection of the EXISTING compact relief footprint. This is
// for observation coverage, not a new navigation gate or a boat-only force.
inline bool OverlapsReach(const FFeature& F,double Start,double Finish)
{
    const double A=FMath::DegreesToRadians(F.AngleDegrees);
    const double C=FMath::Cos(A),S=FMath::Sin(A),L=FMath::Clamp(F.Length,2.f,7.f);
    const double X0=-3.*L*C,X1=7.*L*C,W=12.*FMath::Abs(S);
    return F.Station+FMath::Max(X0,X1)+W>=Start && F.Station+FMath::Min(X0,X1)-W<=Finish;
}
inline bool InsideReliefFootprint(const FFeature& F,const FVector2D& P)
{
    const double A=FMath::DegreesToRadians(F.AngleDegrees),C=FMath::Cos(A),S=FMath::Sin(A);
    const FVector2D R=P-FVector2D(F.Station,F.Lateral);
    const double Along=R.X*C+R.Y*S,Across=-R.X*S+R.Y*C,L=FMath::Clamp(F.Length,2.f,7.f);
    return FMath::Abs(Across)<=12. && Along>=-3.*L && Along<=7.*L;
}
inline bool HasProfile(const FString& Map)
{
    return RaftSimWaterFeatureKinematics::IsPlayableRiver(Map) &&
        (Map.EndsWith(TEXT("L_Hance")) || Map.EndsWith(TEXT("L_Zambezi")) ||
         Map.EndsWith(TEXT("L_UpperHuacas")) || Map.EndsWith(TEXT("L_Terminator")) ||
         Map.EndsWith(TEXT("L_LavaCanyon")) || Map.EndsWith(TEXT("L_Colorado_BadgerCreek")) ||
         Map.EndsWith(TEXT("L_Colorado_HouseRock")) || Map.EndsWith(TEXT("L_Colorado_SoapCreek")) ||
         Map.EndsWith(TEXT("L_Colorado_Georgie")) || Map.EndsWith(TEXT("L_Colorado_Unkar")));
}
inline TArray<FFeature> BuildFeatures(const FString& Map)
{
    if(!HasProfile(Map))return {};
    TArray<FFeature> Result;
    if(Map.EndsWith(TEXT("L_Colorado_Unkar")))
    {
        // Unkar's v3 USGS-registered chart: upper drop ~740-980 m, then
        // a quieter reach. Positive lateral is river LEFT. Guides describe
        // left-wall hydraulics, a centre tongue and a timely move right,
        // but not onto the shallow right margin. These dimensions are
        // authored 8000-cfs hypotheses, not measured rocks or currents.
        // See unkar_profile_evidence_2026_10_07.json. Keep the later drop
        // beyond 1100 m separate; never carry rapid froth across the pool.
        Result={{776,24,0,1.f,3.f,.9f},{782,28,0,.9f,3.f,.85f},
                {828,12,-25,.75f,4.f,.55f}};
        for(double Station:{848.,882.,916.,950.})
            for(double Lateral:{0.,6.,12.})
                Result.Add({Station,Lateral,0.,.65f,4.f,.35f});
    }
    if(Map.EndsWith(TEXT("L_Colorado_Georgie")))
    {
        // Georgie / 24 Mile, NOT the separate 24 1/2 Mile rapid downstream.
        // The v3 USGS-registered chart places the drop at 780-840 m.
        // Guide descriptions distinguish a standing wave/left lateral from
        // the far-right hole, with a lower-energy seam between them. Positive
        // lateral is river left. These bounded dimensions are authored, not
        // surveyed hydraulics; no pin-rock geometry is invented here.
        // See georgie_profile_evidence_2026_10_07.json.
        Result={{826,-18,0,1.05f,3.f,.95f},
                {822,0,0,1.f,4.f,.55f},{822,6,0,1.f,4.f,.55f},
                {820,12,-25,.8f,4.f,.55f}};
        for(double Station:{850.,874.})
            for(double Lateral:{0.,6.})
                Result.Add({Station,Lateral,0.,.55f,4.f,.3f});
    }
    if(Map.EndsWith(TEXT("L_Colorado_SoapCreek")))
    {
        // Post-2015 guide accounts describe a right-of-centre entry, with
        // stronger centre/left waves and holes. Coordinates use the v5 Soap
        // source chart, NOT Badger's local axis or global guide-mile offsets.
        // These dimensions are authored 8000-cfs hypotheses, not surveyed
        // boulders. See soap_creek_profile_evidence_2026_10_07.json. In this
        // east/north chart positive lateral is river LEFT.
        Result={{790,0,0,.85f,3.f,.85f},{790,6,0,.85f,3.f,.85f},
                {850,8,0,1.f,3.5f,.9f},{850,14,0,1.f,3.5f,.9f},
                {926,6,0,.9f,3.f,.8f},{926,12,0,.9f,3.f,.8f}};
        // The right approach still meets lower train waves; preserving a
        // tongue does not mean making the whole preferred route flat water.
        for(double Station:{988.,1020.,1052.,1084.})
            for(double Lateral:{-12.,-6.,0.})
                Result.Add({Station,Lateral,0.,.65f,4.f,.35f});
    }
    if(Map.EndsWith(TEXT("L_Colorado_HouseRock")))
    {
        // GoRafting House Rock: debris fan pushes toward left-side bottom
        // hydraulics; a shallow right passage remains, with a real risk of
        // bank contact if overdone. USGS's registered 2021 drop is 730-1000 m.
        // Dimensions are authored hypotheses, not surveyed individual holes.
        // The negative diagonal normal produces a LEFTWARD near-surface
        // return in the same kernel used by hulls, visible relief and foam.
        Result={{842,6,-30,.8f,4.f,.75f},
                {882,10,0,1.2f,3.f,1.f},{882,16,0,1.2f,3.f,1.f},
                {910,10,0,1.1f,3.f,1.f},{910,16,0,1.1f,3.f,1.f}};
        for(double Station:{948.,972.})
            for(double Lateral:{-6.,0.,6.})
                Result.Add({Station,Lateral,0.,.75f,4.f,.4f});
    }
    if(Map.EndsWith(TEXT("L_Colorado_BadgerCreek")))
    {
        // GoRafting's Badger entry describes an upper-right hydraulic and
        // a tongue to its left followed by waves. USGS 2021 profile locates
        // this drop at roughly 750-1000 m in the registered construction
        // window. Footprints/amplitudes BELOW are authored hypotheses at
        // 8000 cfs, not surveyed obstacle dimensions or class acceptance.
        // Preserve the broad left tongue; do not manufacture a slalom.
        Result={{790,-24,0,1.f,3.f,1.f},{790,-18,0,1.f,3.f,1.f}};
        for(int32 Wave=0;Wave<5;++Wave)
            for(double Lateral:{-6.,0.,6.})
                Result.Add({842.+24.*Wave,Lateral,0.,.75f,4.f,.40f});
    }
    if(Map.EndsWith(TEXT("L_Hance")))Result = {
        {755,-13,0,1.0f,3.f,1.f},{755,-7,0,1.0f,3.f,1.f},
        {850,-10,35,.8f,4.f,.65f},{850,-4,35,.8f,4.f,.65f},
        {895,-4,0,.65f,3.f,.8f},{895,3,0,.65f,3.f,.8f}};
    if(Map.EndsWith(TEXT("L_Zambezi")))
    {
        Result={
        // The near-surface roller opposes this normal. A negative normal
        // angle therefore pushes river-left, toward the catalogued Crease.
        // Using +35 for this normal reversed the documented leftward shove.
        {6140,-18,-35,1.1f,4.f,.85f},{6140,-12,-35,1.1f,4.f,.85f},
        {6180,19,0,1.1f,3.f,1.f},{6180,25,0,1.1f,3.f,1.f}};
        // The catalogue describes a 36 m-wide six-wave train. One centre
        // site only supplied a 9.6 m-wide roller and let the -12 m control
        // bypass its physical current. Tile the EXISTING shared kernel
        // across an authored approximation of that width; retain its local
        // crest cap, depth/wet gates and compact pool release.
        for(int32 Wave=0;Wave<6;++Wave)
            for(double Lateral:{-12.,-6.,0.,6.,12.})
                Result.Add({6360.+16.*Wave,Lateral,0.,.9f,5.f,.45f});
    }
#include "RaftSimNamedRapidProfiles.inl"
    return Result;
}
// Called by both the production surface refresh and the native boat driver.
// Do not allocate/copy the whole river catalogue every physics/render frame.
inline const TArray<FFeature>& Features(const FString& Map)
{
    static const TArray<FFeature> Empty;
    if(!HasProfile(Map))return Empty;
    static const TArray<FFeature> Hance=BuildFeatures(TEXT("L_Hance"));
    static const TArray<FFeature> Zambezi=BuildFeatures(TEXT("L_Zambezi"));
    static const TArray<FFeature> Pacuare=BuildFeatures(TEXT("L_UpperHuacas"));
    static const TArray<FFeature> Futa=BuildFeatures(TEXT("L_Terminator"));
    static const TArray<FFeature> Chilko=BuildFeatures(TEXT("L_LavaCanyon"));
    static const TArray<FFeature> Badger=BuildFeatures(TEXT("L_Colorado_BadgerCreek"));
    static const TArray<FFeature> HouseRock=BuildFeatures(TEXT("L_Colorado_HouseRock"));
    static const TArray<FFeature> SoapCreek=BuildFeatures(TEXT("L_Colorado_SoapCreek"));
    static const TArray<FFeature> Georgie=BuildFeatures(TEXT("L_Colorado_Georgie"));
    static const TArray<FFeature> Unkar=BuildFeatures(TEXT("L_Colorado_Unkar"));
    if(Map.EndsWith(TEXT("L_Hance")))return Hance;
    if(Map.EndsWith(TEXT("L_Zambezi")))return Zambezi;
    if(Map.EndsWith(TEXT("L_UpperHuacas")))return Pacuare;
    if(Map.EndsWith(TEXT("L_Terminator")))return Futa;
    if(Map.EndsWith(TEXT("L_Colorado_BadgerCreek")))return Badger;
    if(Map.EndsWith(TEXT("L_Colorado_HouseRock")))return HouseRock;
    if(Map.EndsWith(TEXT("L_Colorado_SoapCreek")))return SoapCreek;
    if(Map.EndsWith(TEXT("L_Colorado_Georgie")))return Georgie;
    if(Map.EndsWith(TEXT("L_Colorado_Unkar")))return Unkar;
    return Chilko;
}

template<typename FSampler>
inline int32 Append(const TArray<FFeature>& Profile, const FBox2D& VisibleBounds,
    FSampler&& Sample, TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite>& Sites)
{
    int32 Added=0;
    for(const auto& F:Profile)
    {
        const FVector2D P(F.Station,F.Lateral);
        if(!VisibleBounds.ExpandBy(40.).IsInside(P))continue;
        FRaftSimWaterSample W;
        if(!Sample(P,W) || !W.bWet || !FMath::IsFinite(W.DepthMeters) || W.DepthMeters<.35f ||
            W.VelocityMetersPerSecond.ContainsNaN() || W.VelocityMetersPerSecond.X<.75f)continue;
        // Replace a local detector duplicate, do not pile a second crest on
        // top. All unrelated measured/live sites are retained.
        Sites.RemoveAll([&](const auto& S){return (S.RiverCoordinatesMeters-P).SizeSquared()<9.;});
        auto& S=Sites.AddDefaulted_GetRef();S.RiverCoordinatesMeters=P;
        const double A=FMath::DegreesToRadians(F.AngleDegrees);
        S.FlowDirection=FVector2D(FMath::Cos(A),FMath::Sin(A));
        S.Intensity=1.f;S.PhysicalCrestHeightMeters=FMath::Min(F.Height,.6f*W.DepthMeters);
        S.PhysicalCrestLengthMeters=F.Length;S.SpillingFraction=F.Spill;
        S.bLocalEnvelopeCap=true;++Added;
    }
    return Added;
}

template<typename FSampler>
inline int32 Append(const FString& Map,const FBox2D& Bounds,FSampler&& Sample,
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite>& Sites)
{
    return Append(Features(Map),Bounds,Forward<FSampler>(Sample),Sites);
}
}
