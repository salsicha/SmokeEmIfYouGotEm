#pragma once
#include "CoreMinimal.h"
#include "RaftSimWaterFlowFrame.h"

namespace RaftSimMetricBreakingSearch
{
// Extension only: callers retain their original near detections and all
// intensity/shoreline/dedup gates. The 3/6 m span is an authored detection
// scale, not a surveyed wavelength. Never bridge a dry/source-exterior cell
// or a turning/reversed current to manufacture a jump.
template<class DirectionAt>
int32 Find(int32 Index,int32 Nx,int32 Ny,float Spacing,int32 ExistingFarCells,
    const FVector2D& Downstream,TConstArrayView<uint8> Wet,
    TConstArrayView<float> Froude,DirectionAt&& GetDirection)
{
    if(Nx<2 || Ny<2 || Wet.Num()!=Nx*Ny || Froude.Num()!=Wet.Num() ||
        Index<0 || Index>=Wet.Num() || !Wet[Index] ||
        !FMath::IsFinite(Spacing) || Spacing<=0.f || ExistingFarCells<1 ||
        Downstream.ContainsNaN() || FMath::Abs(Downstream.SizeSquared()-1.)>1.e-4 ||
        !FMath::IsFinite(Froude[Index]) || Froude[Index]>.94f)return INDEX_NONE;
    const int32 Near=FMath::Max(1,FMath::RoundToInt(3.f/Spacing));
    const int32 Far=FMath::FloorToInt(6.f/Spacing);
    if(Far<=ExistingFarCells)return INDEX_NONE;
    // A valid path cannot turn an ineligible endpoint into a transition.
    // Reject impossible searches before computing intermediate directions;
    // surviving endpoints still pass every original path/corner check below.
    const auto EligibleEndpoint=[&](int32 Step)
    {
        if(Step<=ExistingFarCells || Step>Far)return false;
        const int32 I=RaftSimWaterFlowFrame::OffsetIndex(Index,Nx,Ny,Downstream,-Step);
        if(I==INDEX_NONE || !Wet[I] || !FMath::IsFinite(Froude[I]) || Froude[I]<1.12f)return false;
        const double DX=double(I%Nx-Index%Nx)*Spacing,DY=double(I/Nx-Index/Nx)*Spacing;
        return DX*DX+DY*DY<=36.+1.e-6;
    };
    if(!EligibleEndpoint(Near) && !EligibleEndpoint(Far))return INDEX_NONE;
    int32 Previous=Index;
    for(int32 Step=1;Step<=Far;++Step)
    {
        const int32 I=RaftSimWaterFlowFrame::OffsetIndex(Index,Nx,Ny,Downstream,-Step);
        if(I==INDEX_NONE || !Wet[I] || !FMath::IsFinite(Froude[I]))return INDEX_NONE;
        const int32 X=I%Nx,Y=I/Nx,PX=Previous%Nx,PY=Previous/Nx;
        if(I!=Previous)
        {
            // A diagonal step must not cut the corner of a dry island.
            if(X!=PX && Y!=PY && (!Wet[PY*Nx+X] || !Wet[Y*Nx+PX]))return INDEX_NONE;
            const FVector2D Direction=GetDirection(I);
            if(Direction.ContainsNaN() || FVector2D::DotProduct(Downstream,Direction)<.9)return INDEX_NONE;
            Previous=I;
        }
        // An oblique ray can round successive steps onto the same cell.
        // Reuse its path validation, but still test a metric endpoint here.
        if(Step<=ExistingFarCells || (Step!=Near && Step!=Far))continue;
        // Rounding an oblique offset can exceed six metres. Reject it rather
        // than silently enlarge the physical search radius.
        const double DX=double(X-Index%Nx)*Spacing,DY=double(Y-Index/Nx)*Spacing;
        if(DX*DX+DY*DY>36.+1.e-6)continue;
        if(Froude[I]>=1.12f)return I;
    }
    return INDEX_NONE;
}
}
