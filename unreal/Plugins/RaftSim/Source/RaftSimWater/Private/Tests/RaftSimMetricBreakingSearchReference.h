#pragma once
#include "RaftSimWaterFlowFrame.h"

// Frozen v10 path-first reference, for differential testing of endpoint rejection.
// This is not a second production detection model.
namespace RaftSimMetricBreakingSearchReference
{
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
    int32 Previous=Index;
    for(int32 Step=1;Step<=Far;++Step)
    {
        const int32 I=RaftSimWaterFlowFrame::OffsetIndex(Index,Nx,Ny,Downstream,-Step);
        if(I==INDEX_NONE || !Wet[I] || !FMath::IsFinite(Froude[I]))return INDEX_NONE;
        const int32 X=I%Nx,Y=I/Nx,PX=Previous%Nx,PY=Previous/Nx;
        if(I!=Previous)
        {
            if(X!=PX && Y!=PY && (!Wet[PY*Nx+X] || !Wet[Y*Nx+PX]))return INDEX_NONE;
            const FVector2D Direction=GetDirection(I);
            if(Direction.ContainsNaN() || FVector2D::DotProduct(Downstream,Direction)<.9)return INDEX_NONE;
            Previous=I;
        }
        if(Step<=ExistingFarCells || (Step!=Near && Step!=Far))continue;
        const double DX=double(X-Index%Nx)*Spacing,DY=double(Y-Index/Nx)*Spacing;
        if(DX*DX+DY*DY>36.+1.e-6)continue;
        if(Froude[I]>=1.12f)return I;
    }
    return INDEX_NONE;
}
}
