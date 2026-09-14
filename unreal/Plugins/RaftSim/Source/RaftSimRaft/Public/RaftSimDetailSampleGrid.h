#pragma once
#include "CoreMinimal.h"

// A 128x128 half-metre output window sampled from a fixed, world-aligned
// 65x65 one-metre lattice. Moving by one output cell must not change the
// interpolation stencil at a retained world position. This is point sampling,
// not a conservative finite-volume transfer or a finer bathymetry survey.
struct FRaftSimDetailSampleGrid
{
    FVector2f CoarseOriginMeters=FVector2f::ZeroVector;
    FIntPoint HalfCellPhase=FIntPoint::ZeroValue;

    bool Register(FVector2f Origin)
    {
        if(Origin.ContainsNaN())return false;
        const FVector2f Coarse(FMath::FloorToFloat(Origin.X),FMath::FloorToFloat(Origin.Y));
        const FVector2f Phase=(Origin-Coarse)*2.f;
        if((Phase.X!=0 && Phase.X!=1) || (Phase.Y!=0 && Phase.Y!=1))return false;
        CoarseOriginMeters=Coarse;HalfCellPhase=FIntPoint(int32(Phase.X),int32(Phase.Y));
        return true;
    }

    template<class T> T Interpolate(TConstArrayView<T> Samples,int32 X,int32 Y) const
    {
        check(Samples.Num()==65*65 && X>=0 && X<128 && Y>=0 && Y<128);
        const int32 HX=X+HalfCellPhase.X,HY=Y+HalfCellPhase.Y;
        return InterpolateAt<T>(Samples,65,HX,HY);
    }

    // Same fixed world lattice with one COARSE node of halo on every side.
    // Node(0,0) is CoarseOriginMeters-(1,1). Supports actual ghost centres
    // at output indices -1 and128 without clamping to interior samples.
    template<class T> T InterpolateHalo(TConstArrayView<T> Samples,int32 X,int32 Y) const
    {
        check(Samples.Num()==67*67 && X>=-1 && X<=128 && Y>=-1 && Y<=128);
        return InterpolateAt<T>(Samples,67,X+HalfCellPhase.X+2,Y+HalfCellPhase.Y+2);
    }

    // Explicit pressure-stencil capture only: two coarse-node rings cover
    // three fine-cell rings, including corners, for either half-cell phase.
    template<class T> T InterpolatePressureHalo(TConstArrayView<T> Samples,int32 X,int32 Y) const
    {
        check(Samples.Num()==69*69 && X>=-3 && X<=130 && Y>=-3 && Y<=130);
        return InterpolateAt<T>(Samples,69,X+HalfCellPhase.X+4,Y+HalfCellPhase.Y+4);
    }

private:
    template<class T> static T InterpolateAt(TConstArrayView<T> Samples,int32 Stride,int32 HX,int32 HY)
    {
        // The positive phase's final sample is EXACTLY node64, not an
        // extrapolation or a clamped approximation to node63.5.
        const int32 C=FMath::Min(HX/2,Stride-2),R=FMath::Min(HY/2,Stride-2);
        const float Fx=(HX-2*C)*.5f,Fy=(HY-2*R)*.5f;
        // At lattice nodes, copy that node directly. Lerp(A,B,1) can differ
        // from B through cancellation and would break exact overlap at edges.
        const auto Along=[&](int32 Row)
        {
            if(Fx==0)return Samples[Row*Stride+C];
            if(Fx==1)return Samples[Row*Stride+C+1];
            return FMath::Lerp(Samples[Row*Stride+C],Samples[Row*Stride+C+1],Fx);
        };
        if(Fy==0)return Along(R);
        if(Fy==1)return Along(R+1);
        return FMath::Lerp(Along(R),Along(R+1),Fy);
    }
};
