#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"

// Scheduling only: immutable edge IDs are assigned by the original serial
// insertion pass. Prefixes preserve source/child order and cache metadata.
namespace RaftSimParallelCrestEmission
{
template<class TEdges,class TAlternate>
void Build(const TArray<int32>& Source,const TArray<int32>& Owners,const TEdges& Edges,
    bool ShortGreen,TAlternate Alternate,TArray<int32>& Output,TArray<int32>& OutputOwners,
    TArray<FIntVector>& GreenVertices,TArray<uint8>& GreenAlternate)
{
    struct FTriangle
    {
        int32 V[3],M[3],Count,Start=0,ChildOffset=0,GreenOffset=INDEX_NONE;
        bool OtherDiagonal=false;
    };
    const int32 Count=Source.Num()/3;
    TArray<FTriangle> Work;Work.SetNumUninitialized(Count);
    const int32 Batches=FMath::DivideAndRoundUp(Count,256);
    const auto Parallel=[&](auto Operation)
    {
        ParallelFor(TEXT("RaftSimCrestEmission"),Batches,1,[&](int32 Batch)
        {
            for(int32 T=Batch*256;T<FMath::Min((Batch+1)*256,Count);++T)Operation(T);
        },EParallelForFlags::Unbalanced);
    };
    Parallel([&](int32 T)
    {
        auto& W=Work[T];W.Count=0;W.Start=0;W.OtherDiagonal=false;
        for(int32 E=0;E<3;++E)W.V[E]=Source[T*3+E];
        for(int32 E=0;E<3;++E)
        {
            const int32 A=W.V[E],B=W.V[(E+1)%3];
            const uint64 Key=(uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));
            const int32* Found=Edges.Find(Key);W.M[E]=Found ? *Found : INDEX_NONE;
            W.Count+=Found ? 1 : 0;
        }
        if(W.Count==1)while(W.M[W.Start]==INDEX_NONE)++W.Start;
        else if(W.Count==2)
        {
            while(W.M[W.Start]==INDEX_NONE || W.M[(W.Start+1)%3]==INDEX_NONE)++W.Start;
            if(ShortGreen)W.OtherDiagonal=Alternate(W.V[W.Start],W.V[(W.Start+1)%3],W.V[(W.Start+2)%3]);
        }
    });
    int32 Children=0,Greens=0;
    for(auto& W:Work)
    {
        W.ChildOffset=Children;Children+=W.Count+1;
        W.GreenOffset=ShortGreen && W.Count==2 ? Greens++ : INDEX_NONE;
    }
    Output.SetNumUninitialized(Children*3);OutputOwners.SetNumUninitialized(Children);
    GreenVertices.SetNumUninitialized(Greens);GreenAlternate.SetNumUninitialized(Greens);
    Parallel([&](int32 T)
    {
        const auto& W=Work[T];int32 Child=W.ChildOffset;
        const auto Add=[&](int32 A,int32 B,int32 C)
        {Output[Child*3]=A;Output[Child*3+1]=B;Output[Child*3+2]=C;OutputOwners[Child++]=Owners[T];};
        if(W.Count==0){Add(W.V[0],W.V[1],W.V[2]);return;}
        if(W.Count==3)
        {
            Add(W.V[0],W.M[0],W.M[2]);Add(W.M[0],W.V[1],W.M[1]);
            Add(W.M[2],W.M[1],W.V[2]);Add(W.M[0],W.M[1],W.M[2]);return;
        }
        const int32 A=W.V[W.Start],B=W.V[(W.Start+1)%3],C=W.V[(W.Start+2)%3],AB=W.M[W.Start];
        if(W.Count==1){Add(A,AB,C);Add(AB,B,C);return;}
        const int32 BC=W.M[(W.Start+1)%3];Add(B,BC,AB);
        if(W.GreenOffset!=INDEX_NONE)
        {GreenVertices[W.GreenOffset]=FIntVector(A,B,C);GreenAlternate[W.GreenOffset]=W.OtherDiagonal;}
        if(W.OtherDiagonal){Add(A,AB,BC);Add(A,BC,C);}
        else {Add(A,AB,C);Add(AB,BC,C);}
    });
}
}
