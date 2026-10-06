#pragma once
#include "CoreMinimal.h"
#include "RaftSimWaterRuntimeAdapter.h"

namespace RaftSimWaterSmoothing
{
inline int32 OpticalPassCount(bool bNativeMean, bool bNeedsOptical, int32 Configured)
{
    return bNativeMean && !bNeedsOptical ? 0 : Configured;
}

// Same Jacobi stencil and wet-neighbour rejection as the original carrier.
// Zero optical passes means that output has no consumer; hydraulic analysis
// still receives all its original passes. The caller restores native stage.
inline void Apply(TArray<float>& Surface, const TArray<uint8>& Wet,
    int32 Nx,int32 Ny,int32 Stride,float Strength,int32 OpticalPasses,
    int32 HydraulicPasses,TArray<float>& Hydraulic)
{
    check(Surface.Num()==Nx*Ny && Wet.Num()==Surface.Num() && Stride>0);
    check(OpticalPasses>=0 && HydraulicPasses>0);
    Hydraulic=Surface;
    const int32 Passes=FMath::Max(OpticalPasses,HydraulicPasses);
    TArray<float> Optical;
    for (int32 Pass=0;Pass<Passes;++Pass)
    {
        const TArray<float> Previous=Surface;
        for (int32 Y=Stride;Y<Ny-Stride;++Y) for (int32 X=Stride;X<Nx-Stride;++X)
        {
            const int32 I=Y*Nx+X,U=I-Stride,D=I+Stride,R=I-Stride*Nx,L=I+Stride*Nx;
            if (!Wet[I] || !Wet[U] || !Wet[D] || !Wet[R] || !Wet[L]) continue;
            Surface[I]=URaftSimWaterRuntimeAdapter::ComputeCoupledSmoothedSurfaceHeightMeters(
                Previous[I],Previous[U],Previous[D],Previous[R],Previous[L],Strength);
        }
        if (Pass+1==HydraulicPasses) Hydraulic=Surface;
        if (Pass+1==OpticalPasses && OpticalPasses<Passes) Optical=Surface;
    }
    if (!Optical.IsEmpty()) Surface=MoveTemp(Optical);
}
}
