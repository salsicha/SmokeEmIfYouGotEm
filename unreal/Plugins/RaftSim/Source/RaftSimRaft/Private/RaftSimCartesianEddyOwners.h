#pragma once
#include "CoreMinimal.h"

// Geometry candidates only, not a wet-mask edit or a collider. A caller must
// additionally verify exposed registered physical ground and local wet flow.
namespace RaftSimCartesianEddyOwners
{
struct FIsland { FVector2D Center=FVector2D::ZeroVector; double Radius=0.; TArray<int32> Collar; };
inline TArray<FIsland> Find(TConstArrayView<uint8> Wet,TConstArrayView<uint8> Available,
    TConstArrayView<FVector2D> Coordinates,int32 Width,int32 Height,double Spacing)
{
    TArray<FIsland> Result;
    const int32 N=Width*Height;
    if(Width<3 || Height<3 || Wet.Num()!=N || Available.Num()!=N || Coordinates.Num()!=N || Spacing<=0.)return Result;
    TArray<uint8> Seen;Seen.Init(0,N);
    for(int32 Seed=0;Seed<N;++Seed)
    {
        if(Seen[Seed] || Wet[Seed] || !Available[Seed])continue;
        TArray<int32> Queue;Queue.Add(Seed);Seen[Seed]=1;
        FIsland Island;bool Enclosed=true;double Area=0.;
        for(int32 Head=0;Head<Queue.Num();++Head)
        {
            const int32 I=Queue[Head],X=I%Width,Y=I/Width;
            if(Queue.Num()<=400)
            {
                Island.Center+=Coordinates[I];
                if(X>0 && Y>0 && X<Width-1 && Y<Height-1)
                {
                    const FVector2D A=(Coordinates[I+1]-Coordinates[I-1])*.5;
                    const FVector2D B=(Coordinates[I+Width]-Coordinates[I-Width])*.5;
                    const double CellArea=FMath::Abs(A.X*B.Y-A.Y*B.X);
                    if(!FMath::IsFinite(CellArea) || CellArea<=0.)Enclosed=false;
                    else Area+=CellArea;
                }
            }
            if(X==0 || Y==0 || X==Width-1 || Y==Height-1)Enclosed=false;
            for(const FIntPoint Offset : {FIntPoint(-1,0),FIntPoint(1,0),FIntPoint(0,-1),FIntPoint(0,1)})
            {
                const int32 NX=X+Offset.X,NY=Y+Offset.Y;
                if(NX<0 || NX>=Width || NY<0 || NY>=Height)continue;
                const int32 J=NY*Width+NX;
                if(!Available[J]){Enclosed=false;continue;}
                if(Wet[J]){if(Queue.Num()<=400)Island.Collar.AddUnique(J);continue;}
                if(!Seen[J]){Seen[J]=1;Queue.Add(J);}
            }
        }
        // Large land masses and any bank/crop-connected dry component are
        // not isolated rocks. Radius is an inferred equal-area wake scale,
        // NOT a replacement for the actual captured boundary/contact mesh.
        if(!Enclosed || Queue.Num()>400 || Island.Collar.Num()<4)continue;
        Island.Center/=Queue.Num();
        // Use actual field cell area (also valid for non-square station/lateral
        // grids). The wake radius still does not replace the physical mesh.
        Island.Radius=FMath::Max(.75,FMath::Sqrt(Area/UE_DOUBLE_PI));
        Result.Add(MoveTemp(Island));
    }
    return Result;
}
}
