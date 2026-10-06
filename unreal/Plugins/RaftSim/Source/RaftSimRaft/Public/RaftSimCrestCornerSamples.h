#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"

// One build only: points are append-only across its refinement levels. A
// sampling barrier makes indexed corner values immutable during selection.
class FRaftSimCrestCornerSamples
{
public:
    uint64 SampleCount=0,ReadCount=0;
    void Prepare(const TArray<FVector2D>& Points,const TArray<int32>& Triangles,
        TFunctionRef<float(const FVector2D&)> HeightCm,TConstArrayView<FBox2D> Regions,
        const FBox2D* DetailWindow,float DetailSpanCm)
    {
        CurrentTriangles=&Triangles;
        Values.SetNumUninitialized(Points.Num());
        Ready.SetNumZeroed(Points.Num());
        TArray<int32> Pending;
        for(int32 T=0;T<Triangles.Num();T+=3)
        {
            const int32 A=Triangles[T],B=Triangles[T+1],C=Triangles[T+2];
            FBox2D Bounds(ForceInit);Bounds+=Points[A];Bounds+=Points[B];Bounds+=Points[C];
            // These exact early exits also precede corner reads in selection.
            if(DetailWindow && DetailSpanCm>0 && Bounds.Intersect(*DetailWindow) &&
                FMath::Max(Bounds.GetSize().X,Bounds.GetSize().Y)>DetailSpanCm)continue;
            if(!Regions.IsEmpty())
            {
                bool Intersects=false;
                for(const auto& Region:Regions)if(Bounds.Intersect(Region)){Intersects=true;break;}
                if(!Intersects)continue;
            }
            ReadCount+=3;
            for(const int32 Node:{A,B,C})if(!Ready[Node])
            {Ready[Node]=1;Pending.Add(Node);}
        }
        SampleCount+=Pending.Num();
        ParallelFor(TEXT("RaftSimCrestCornerSamples"),Pending.Num(),128,[&](int32 I)
        {const int32 Node=Pending[I];Values[Node]=HeightCm(Points[Node]);},EParallelForFlags::Unbalanced);
    }
    float Get(int32 Triangle,int32 Corner) const
    {
        check(CurrentTriangles && Corner>=0 && Corner<3);
        const int32 Node=(*CurrentTriangles)[Triangle*3+Corner];
        check(Ready[Node]);
        return Values[Node];
    }
private:
    TArray<float> Values;
    TArray<uint8> Ready;
    const TArray<int32>* CurrentTriangles=nullptr;
};
