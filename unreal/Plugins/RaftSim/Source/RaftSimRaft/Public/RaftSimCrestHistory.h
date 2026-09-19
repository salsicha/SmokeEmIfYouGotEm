#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimCoordinateMap.h"
#include "Async/ParallelFor.h"

// Exact-coordinate temporal blending. Stable coordinates use dense indices;
// changed coordinates retain the original last-writer-wins map semantics.
// Only lookup ownership is cached, never the current target or blend result.
template<typename LookupType>
class TRaftSimCrestHistory
{
public:
    bool LastParallelValues=false;
    void Reset()
    { XY.Reset(); Owners.Reset(); Previous.Reset(); Next.Reset(); Lookup.Reset(); LastParallelValues=false; }

    bool Apply(TArray<FProcMeshVertex>& Vertices,int32 SourceCount,
        TConstArrayView<uint8> Boundary,TConstArrayView<float> Targets,float Alpha,
        TArray<float>& Rendered,bool bAllowDense=true,bool bParallel=false)
    {
        const int32 Count=Vertices.Num()-SourceCount;
        check(SourceCount>=0 && Count>=0 && Boundary.Num()==Count && Targets.Num()==Vertices.Num());
        bool Same=bAllowDense && XY.Num()==Count;
        for(int32 I=0;Same && I<Count;++I)
        {
            const auto& P=Vertices[SourceCount+I].Position;
            Same=XY[I]==FVector2D(P.X,P.Y);
        }
        Next.SetNumUninitialized(Count,EAllowShrinking::No);
        Rendered.Init(0,Vertices.Num());
        // Actual-game pairs show a clear gain for mapped history, but not
        // for dense history. Preserve its original serial execution exactly.
        LastParallelValues=bParallel && !Same && Count>0;
        const LookupType& ReadLookup=Lookup;
        const auto ApplyOne=[&](int32 I)
        {
            auto& P=Vertices[SourceCount+I].Position;
            const int32* Owner=Same ? &Owners[I] : ReadLookup.Find(FVector2D(P.X,P.Y));
            const float Old=Owner ? Previous[*Owner] : 0.f;
            const float Correction=Boundary[I] ? 0.f : FMath::Lerp(Old,Targets[SourceCount+I],Alpha);
            P.Z+=Correction;
            Next[I]=Correction; Rendered[SourceCount+I]=Correction;
        };
        if(LastParallelValues)ParallelFor(TEXT("RaftSimCrestHistoryValues"),Count,256,ApplyOne);
        else for(int32 I=0;I<Count;++I)ApplyOne(I);
        if(!Same)
        {
            // Rebuild only after every previous-frame lookup has completed.
            // Duplicate coordinates deliberately refer to the LAST value,
            // exactly as TMap::Add did in the original update loop.
            Lookup.Reset(); Lookup.Reserve(Count);
            XY.SetNumUninitialized(Count,EAllowShrinking::No);
            Owners.SetNumUninitialized(Count,EAllowShrinking::No);
            for(int32 I=0;I<Count;++I)
            {
                const auto& P=Vertices[SourceCount+I].Position;
                XY[I]=FVector2D(P.X,P.Y); Lookup.Add(XY[I],I);
            }
            const auto AssignOwner=[&](int32 I){Owners[I]=ReadLookup.FindChecked(XY[I]);};
            if(LastParallelValues)ParallelFor(TEXT("RaftSimCrestHistoryOwners"),Count,256,AssignOwner);
            else for(int32 I=0;I<Count;++I)AssignOwner(I);
        }
        Swap(Previous,Next);
        return Same;
    }
private:
    TArray<FVector2D> XY;
    TArray<int32> Owners;
    TArray<float> Previous,Next;
    LookupType Lookup;
};

// Actual-input paired timings did not establish a reliable win; keep the
// original map in ordinary gameplay and the candidate explicitly diagnostic.
using FRaftSimCrestHistory=TRaftSimCrestHistory<TMap<FVector2D,int32>>;
using FRaftSimFastCrestHistory=TRaftSimCrestHistory<TRaftSimCoordinateMap<int32>>;
