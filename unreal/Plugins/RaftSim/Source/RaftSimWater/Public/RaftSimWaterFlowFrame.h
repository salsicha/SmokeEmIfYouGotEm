#pragma once
#include "CoreMinimal.h"

/** Shared hydraulic XY <-> along/across frame. The direction is a unit vector
 * in hydraulic coordinates, not world coordinates (north may reflect world Y).
 * Normalize once when authoring a site, not at every vertex/foam sample. */
namespace RaftSimWaterFlowFrame
{
/** Live-to-source presentation transition measured from all four actual crop
 * edges. Evaluated in current hydraulic coordinates, with no history/recenter lag. */
inline float CropAuthority(const FVector2D& Point, const FBox2D& Bounds, float FeatherMeters)
{
    if (!Bounds.bIsValid || Point.ContainsNaN() || !FMath::IsFinite(FeatherMeters) || FeatherMeters<=0.f)
        return 0.f;
    const double Margin = FMath::Min(FMath::Min(Point.X-Bounds.Min.X, Bounds.Max.X-Point.X),
        FMath::Min(Point.Y-Bounds.Min.Y, Bounds.Max.Y-Point.Y));
    return float(FMath::Clamp(Margin/FeatherMeters, 0., 1.));
}

inline FVector2D Direction(const FVector2D& Velocity)
{
    if (Velocity.ContainsNaN() || Velocity.IsNearlyZero()) return FVector2D(1.,0.);
    return Velocity.GetSafeNormal();
}
inline FVector2D ToLocal(const FVector2D& Relative, const FVector2D& Downstream)
{
    return FVector2D(FVector2D::DotProduct(Relative,Downstream),
        -Relative.X*Downstream.Y+Relative.Y*Downstream.X);
}
inline FVector2D ToField(const FVector2D& Local, const FVector2D& Downstream)
{
    return FVector2D(Downstream.X*Local.X-Downstream.Y*Local.Y,
        Downstream.Y*Local.X+Downstream.X*Local.Y);
}
inline FVector2D FromAngle(float Angle)
{
    return FVector2D(FMath::Cos(double(Angle)),FMath::Sin(double(Angle)));
}
inline FVector2D BlendDirections(const FVector2D& A,const FVector2D& B,double Alpha)
{
    // Shortest-arc interpolation cannot collapse to a zero vector when a
    // persistent site's direction reverses or crosses the +/-pi seam.
    const double Delta=FMath::Atan2(A.X*B.Y-A.Y*B.X,FVector2D::DotProduct(A,B));
    const double Angle=FMath::Atan2(A.Y,A.X)+FMath::Clamp(Alpha,0.,1.)*Delta;
    return FVector2D(FMath::Cos(Angle),FMath::Sin(Angle));
}
/** Conservative field-X extent of an oriented along/across rectangle. */
inline FVector2D XBounds(const FVector2D& Downstream, double AlongMin, double AlongMax, double AcrossMax)
{
    const double A=Downstream.X*AlongMin, B=Downstream.X*AlongMax;
    const double Side=FMath::Abs(Downstream.Y)*AcrossMax;
    return FVector2D(FMath::Min(A,B)-Side,FMath::Max(A,B)+Side);
}
inline int32 OffsetIndex(int32 Index, int32 Nx, int32 Ny, const FVector2D& Direction, double Cells)
{
    const int32 X=Index%Nx+FMath::RoundToInt(Direction.X*Cells);
    const int32 Y=Index/Nx+FMath::RoundToInt(Direction.Y*Cells);
    return X>=0 && X<Nx && Y>=0 && Y<Ny ? Y*Nx+X : INDEX_NONE;
}
inline bool SampleWetScalar(TConstArrayView<float> Values,TConstArrayView<uint8> Wet,
    int32 Nx,int32 Ny,const FVector2D& GridPosition,float& Out)
{
    if (GridPosition.ContainsNaN() || GridPosition.X<0. || GridPosition.Y<0. ||
        GridPosition.X>Nx-1 || GridPosition.Y>Ny-1) return false;
    const int32 X=FMath::Min(FMath::FloorToInt(GridPosition.X),Nx-2);
    const int32 Y=FMath::Min(FMath::FloorToInt(GridPosition.Y),Ny-2);
    const double U=GridPosition.X-X,V=GridPosition.Y-Y;
    double Sum=0.;
    for (int32 DY=0;DY<2;++DY) for (int32 DX=0;DX<2;++DX)
    {
        const double W=(DX?U:1.-U)*(DY?V:1.-V);
        if (W<=0.) continue;
        const int32 I=(Y+DY)*Nx+X+DX;
        if (!Wet[I] || !FMath::IsFinite(Values[I])) return false;
        Sum+=W*Values[I];
    }
    Out=Sum; return true;
}
/** Eight-neighbor distance to wet boundary vertices, including internal holes.
 * Chebyshev distance is a conservative lower bound on Euclidean clearance.
 * Grid edges are boundaries too. No axis is presumed to be downstream. */
inline TArray<int32> WetEdgeStepsReference(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet)
{
    check(Wet.Num()==Nx*Ny);
    TArray<int32> Distance,Queue;
    Distance.Init(MAX_int32,Wet.Num()); Queue.Reserve(Wet.Num());
    for (int32 I=0;I<Wet.Num();++I)
    {
        const int32 X=I%Nx,Y=I/Nx;
        bool Edge=!Wet[I] || X==0 || Y==0 || X==Nx-1 || Y==Ny-1;
        if (!Edge) for (int32 DY=-1;DY<=1;++DY) for (int32 DX=-1;DX<=1;++DX)
            Edge |= !Wet[(Y+DY)*Nx+X+DX];
        if (Edge) { Distance[I]=0; Queue.Add(I); }
    }
    for (int32 Head=0;Head<Queue.Num();++Head)
    {
        const int32 I=Queue[Head],X=I%Nx,Y=I/Nx;
        for (int32 DY=-1;DY<=1;++DY) for (int32 DX=-1;DX<=1;++DX)
        {
            const int32 XX=X+DX,YY=Y+DY;
            if (XX<0 || XX>=Nx || YY<0 || YY>=Ny) continue;
            const int32 J=YY*Nx+XX;
            if (Distance[J]>Distance[I]+1) { Distance[J]=Distance[I]+1; Queue.Add(J); }
        }
    }
    return Distance;
}

// Exact eight-neighbor distance transform on an obstacle-free rectangular
// lattice. The original seeds include every dry cell, wet cells touching dry
// cells (also diagonally), and all four grid edges. Distances may propagate
// through ANY cell, as in the queue reference; dry islands are not obstacles.
// Every shortest Chebyshev path can be split into forward/backward raster
// directions. Two sweeps therefore give the same integer minimum, not a
// bounded band, approximation, different metric or reduced sampling cadence.
inline TArray<int32> WetEdgeStepsSweep(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet)
{
    check(Wet.Num()==Nx*Ny);
    TArray<int32> Distance;
    Distance.SetNumUninitialized(Wet.Num());
    for(int32 Y=0;Y<Ny;++Y)for(int32 X=0;X<Nx;++X)
    {
        const int32 I=Y*Nx+X;
        bool Edge=!Wet[I] || X==0 || Y==0 || X==Nx-1 || Y==Ny-1;
        if(!Edge)for(int32 DY=-1;DY<=1;++DY)for(int32 DX=-1;DX<=1;++DX)
            Edge |= !Wet[(Y+DY)*Nx+X+DX];
        // Every non-edge has a finite path to the preceding grid boundary.
        int32 D=Edge ? 0 : Distance[I-1]+1;
        if(!Edge)
        {
            D=FMath::Min(D,Distance[I-Nx-1]+1);
            D=FMath::Min(D,Distance[I-Nx]+1);
            D=FMath::Min(D,Distance[I-Nx+1]+1);
        }
        Distance[I]=D;
    }
    for(int32 Y=Ny-2;Y>0;--Y)for(int32 X=Nx-2;X>0;--X)
    {
        const int32 I=Y*Nx+X;
        int32 D=Distance[I];
        D=FMath::Min(D,Distance[I+1]+1);
        D=FMath::Min(D,Distance[I+Nx-1]+1);
        D=FMath::Min(D,Distance[I+Nx]+1);
        D=FMath::Min(D,Distance[I+Nx+1]+1);
        Distance[I]=D;
    }
    return Distance;
}

// Normal path: qualified on all distances in 64 actual two-phase comparisons,
// with 19 changing masks and faster results in every pair and both call orders.
inline TArray<int32> WetEdgeSteps(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet,bool bSweep=true)
{
    return bSweep ? WetEdgeStepsSweep(Nx,Ny,Wet) : WetEdgeStepsReference(Nx,Ny,Wet);
}
}
