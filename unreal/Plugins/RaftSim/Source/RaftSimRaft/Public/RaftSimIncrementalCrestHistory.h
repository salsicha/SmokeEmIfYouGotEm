#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

// Candidate: update exact-coordinate ownership only where coordinates move.
// Sorted intrusive lists preserve the original LAST-index-wins TMap semantics,
// including duplicate targets/boundaries. Values still evolve on every call.
class FRaftSimIncrementalCrestHistory
{
    TArray<FVector2D> XY;
    TArray<int32> Owners,LinkPrev,LinkNext;
    TArray<float> Previous,Next;
    TMap<FVector2D,int32> Lookup;
public:
    int32 ChangedCoordinates=0;
    bool bIncrementalUpdate=false;
    void Reset()
    {
        XY.Reset();Owners.Reset();LinkPrev.Reset();LinkNext.Reset();
        Previous.Reset();Next.Reset();Lookup.Reset();
        ChangedCoordinates=0;bIncrementalUpdate=false;
    }
    bool Apply(TArray<FProcMeshVertex>& Vertices,int32 SourceCount,
        TConstArrayView<uint8> Boundary,TConstArrayView<float> Targets,float Alpha,
        TArray<float>& Rendered,bool bAllowDense=true)
    {
        const int32 Count=Vertices.Num()-SourceCount;
        check(SourceCount>=0 && Count>=0 && Boundary.Num()==Count && Targets.Num()==Vertices.Num());
        const bool SameCount=XY.Num()==Count;
        TArray<int32> Changed;
        if(SameCount)for(int32 I=0;I<Count;++I)
        {
            const auto& P=Vertices[SourceCount+I].Position;
            if(XY[I]!=FVector2D(P.X,P.Y))Changed.Add(I);
        }
        ChangedCoordinates=SameCount ? Changed.Num() : Count;
        const bool Same=SameCount && Changed.IsEmpty();
        Next.SetNumUninitialized(Count,EAllowShrinking::No);
        Rendered.Init(0,Vertices.Num());
        for(int32 I=0;I<Count;++I)
        {
            auto& P=Vertices[SourceCount+I].Position;
            const FVector2D Key(P.X,P.Y);
            // Unchanged nodes can use PREVIOUS ownership even when a different
            // node moves into/out of their group in this call. Rebind only after
            // all old values have been consumed, never during this loop.
            const int32* Owner=bAllowDense && (Same || (SameCount && XY[I]==Key)) ? &Owners[I] : Lookup.Find(Key);
            const float Old=Owner ? Previous[*Owner] : 0.f;
            const float Correction=Boundary[I] ? 0.f : FMath::Lerp(Old,Targets[SourceCount+I],Alpha);
            P.Z+=Correction;Next[I]=Correction;Rendered[SourceCount+I]=Correction;
        }
        bIncrementalUpdate=!Same && SameCount && Changed.Num()<=Count/4;
        if(bIncrementalUpdate)
        {
            TSet<FVector2D> Dirty;
            for(int32 I:Changed)
            {
                Dirty.Add(XY[I]);
                const int32 Before=LinkPrev[I],After=LinkNext[I];
                if(Before!=INDEX_NONE)LinkNext[Before]=After;
                if(After!=INDEX_NONE)LinkPrev[After]=Before;
                else if(Before!=INDEX_NONE)Lookup.FindChecked(XY[I])=Before;
                else Lookup.Remove(XY[I]);
            }
            for(int32 I:Changed)
            {
                const auto& P=Vertices[SourceCount+I].Position;
                XY[I]=FVector2D(P.X,P.Y);Dirty.Add(XY[I]);
                const int32* Last=Lookup.Find(XY[I]);
                int32 Before=Last ? *Last : INDEX_NONE,After=INDEX_NONE;
                while(Before!=INDEX_NONE && Before>I){After=Before;Before=LinkPrev[Before];}
                LinkPrev[I]=Before;LinkNext[I]=After;
                if(Before!=INDEX_NONE)LinkNext[Before]=I;
                if(After!=INDEX_NONE)LinkPrev[After]=I;
                else Lookup.Add(XY[I],I);
            }
            for(const auto& Key:Dirty)if(const int32* Last=Lookup.Find(Key))
                for(int32 I=*Last;I!=INDEX_NONE;I=LinkPrev[I])Owners[I]=*Last;
        }
        else if(!Same)
        {
            // Large regroupings use the original linear rebuild, rather than
            // repeated sorted insertion. This threshold changes work only.
            XY.SetNumUninitialized(Count,EAllowShrinking::No);
            Owners.SetNumUninitialized(Count,EAllowShrinking::No);
            LinkPrev.SetNumUninitialized(Count,EAllowShrinking::No);
            LinkNext.Init(INDEX_NONE,Count);Lookup.Reset();Lookup.Reserve(Count);
            for(int32 I=0;I<Count;++I)
            {
                const auto& P=Vertices[SourceCount+I].Position;XY[I]=FVector2D(P.X,P.Y);
                const int32* Last=Lookup.Find(XY[I]);LinkPrev[I]=Last ? *Last : INDEX_NONE;
                if(Last)LinkNext[*Last]=I;
                Lookup.Add(XY[I],I);
            }
            for(const auto& Pair:Lookup)
                for(int32 I=Pair.Value;I!=INDEX_NONE;I=LinkPrev[I])Owners[I]=Pair.Value;
        }
        Swap(Previous,Next);
        return bAllowDense && Same;
    }
};
