#pragma once

#include "CoreMinimal.h"

namespace RaftSimWetSurfaceInterpolation
{
// Point reconstruction only: never modifies FV cell averages, wet masks or time.
// Dry terrain has no free surface to interpolate. In mixed footprints use the
// positive-depth donors to cap only dry elevations ABOVE their weighted stage.
// Lower dry terrain retains the original wetting-front interpolation. Intersect
// the resulting stage with the unchanged bilinear bed. Entirely wet footprints keep
// the existing sampler, including its normal convention. No depth floor or
// film-removal threshold is introduced here; exactly zero depth is absent water.
inline bool ResolveMixed(const double (&Bed)[4],const double (&H)[4],
    const bool (&Available)[4],double Fx,double Fy,double SampleBed,
    double CellX,double CellY,double& Depth,double& Surface,FVector& Normal)
{
    bool HasDry=false;
    for (int32 I=0; I<4; ++I) HasDry |= Available[I] && H[I]==0.;
    if (!HasDry) return false;
    const double W[4]={(1.-Fx)*(1.-Fy),Fx*(1.-Fy),(1.-Fx)*Fy,Fx*Fy};
    const double Wx[4]={-(1.-Fy),1.-Fy,-Fy,Fy};
    const double Wy[4]={-(1.-Fx),-Fx,1.-Fx,Fx};
    double Weight=0.,WeightedStage=0.,DxWeight=0.,DyWeight=0.,DxStage=0.,DyStage=0.;
    for (int32 I=0; I<4; ++I) if (Available[I] && H[I]>0.)
    {
        const double Eta=Bed[I]+H[I];
        Weight+=W[I]; WeightedStage+=W[I]*Eta;
        DxWeight+=Wx[I]; DyWeight+=Wy[I];
        DxStage+=Wx[I]*Eta; DyStage+=Wy[I]*Eta;
    }
    Depth=0.; Surface=SampleBed; Normal=FVector::UpVector;
    if (Weight>0.)
    {
        const double WetEta=WeightedStage/Weight;
        const double DxWetEta=(DxStage-WetEta*DxWeight)/Weight;
        const double DyWetEta=(DyStage-WetEta*DyWeight)/Weight;
        double Eta=WeightedStage,DxEta=DxStage,DyEta=DyStage;
        for (int32 I=0; I<4; ++I) if (Available[I] && H[I]==0.)
        {
            const bool Capped=Bed[I]>WetEta;
            const double DryEta=Capped ? WetEta : Bed[I];
            Eta+=W[I]*DryEta;
            DxEta+=Wx[I]*DryEta+(Capped ? W[I]*DxWetEta : 0.);
            DyEta+=Wy[I]*DryEta+(Capped ? W[I]*DyWetEta : 0.);
        }
        Depth=FMath::Max(Eta-SampleBed,0.);
        Surface=SampleBed+Depth;
        if (Depth>0.) Normal=FVector(
            -DxEta/CellX,-DyEta/CellY,1.).GetSafeNormal();
    }
    return true;
}
}
