#pragma once
#include "RaftSimWaterRuntimeAdapter.h"

// Resolve the mapped takeout cross-section with the production inverse chart.
// Geographic source-chainage is deliberately NOT an input. This is not proof
// of a wet bank approach, surveyed ramp bounds, or successful docking.
namespace RaftSimGeographicTakeout
{
inline bool Resolve(const URaftSimWaterRuntimeAdapter& Adapter,
    const FVector2D& TakeoutWorldCm,const FVector2D& RapidWorldCm,
    const FVector2D& CookedStations,double Start,FVector2D& Finish,FString& Error)
{
    Finish=FVector2D::ZeroVector;Error.Reset();
    if(!Adapter.HasRiverCoordinateMap() || Adapter.HasCartesianWaterCoordinates() ||
        TakeoutWorldCm.ContainsNaN() || RapidWorldCm.ContainsNaN() || CookedStations.ContainsNaN() ||
        !FMath::IsFinite(Start) || CookedStations.Y<=CookedStations.X)
    {Error=TEXT("Invalid geographic takeout frame or cooked interval");return false;}
    FVector2D Points[2];int32 I=0;
    for(const FVector2D P:{TakeoutWorldCm,RapidWorldCm})
    {
        FVector T,L,Back;const FVector World(P.X,P.Y,0.);
        if(!Adapter.WorldToRiverCoordinates(World,Points[I],T,L) || Points[I].ContainsNaN() ||
            FMath::Abs(Points[I].Y)>100. ||
            !Adapter.RiverToWorldPosition(Points[I],0.f,Back) || FVector::DistSquared2D(World,Back)>1.)
        {Error=TEXT("Takeout point outside chart or native round trip exceeds one cm");return false;}
        ++I;
    }
    if(Points[0].Y<=0. || Points[1].X<=Points[0].X || Points[0].X<=Start ||
        Points[0].X<=CookedStations.X+10. || Points[0].X>=CookedStations.Y-10.)
    {Error=TEXT("Takeout must be river-left, upstream of rapid and inside actual cooked coverage");return false;}
    Finish=Points[0];return true;
}
}
