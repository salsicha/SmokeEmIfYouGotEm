#pragma once
#include "CoreMinimal.h"
#include "RaftSimIndexedEdgeMap.h"

namespace RaftSimCrestBoundaries
{
inline uint64 Key(int32 A,int32 B)
{ return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); }

// Frozen original algorithm. Boundary membership is combinatorial, not a
// geometric tolerance, and repeated/nonmanifold edges must remain nonboundary.
inline void Reference(const TArray<int32>& Triangles,const TArray<FIntPoint>& Parents,
    int32 SourceCount,TArray<uint8>& Result)
{
    TMap<uint64,int32> Uses;
    for(int32 T=0;T<Triangles.Num();T+=3)for(int32 E=0;E<3;++E)
        ++Uses.FindOrAdd(Key(Triangles[T+E],Triangles[T+(E+1)%3]));
    TSet<uint64> Boundary;
    for(const auto& E:Uses)if(E.Value==1)Boundary.Add(E.Key);
    Result.Init(0,Parents.Num());
    for(int32 I=0;I<Parents.Num();++I)
    {
        const auto P=Parents[I];const int32 Node=SourceCount+I;
        const uint64 K=Key(P.X,P.Y);
        if(Boundary.Contains(K))
        {
            Result[I]=1;Boundary.Remove(K);
            Boundary.Add(Key(P.X,Node));Boundary.Add(Key(Node,P.Y));
        }
    }
}

// Same ordered edge consumption/subdivision. Root use counts and propagated
// boundary markers share one bounded indexed lookup; zero means consumed.
// Never retain values across topology changes or classify by a spatial epsilon.
inline void Indexed(const TArray<int32>& Triangles,const TArray<FIntPoint>& Parents,
    int32 SourceCount,TArray<uint8>& Result)
{
    FRaftSimIndexedEdgeMap Uses(SourceCount+Parents.Num());
    for(int32 T=0;T<Triangles.Num();T+=3)for(int32 E=0;E<3;++E)
        ++Uses.FindOrAdd(Key(Triangles[T+E],Triangles[T+(E+1)%3]));
    Result.Init(0,Parents.Num());
    for(int32 I=0;I<Parents.Num();++I)
    {
        const auto P=Parents[I];const int32 Node=SourceCount+I;
        const uint64 K=Key(P.X,P.Y);const int32* Count=Uses.Find(K);
        if(Count && *Count==1)
        {
            Result[I]=1;Uses.Add(K,0);
            Uses.Add(Key(P.X,Node),1);Uses.Add(Key(Node,P.Y),1);
        }
    }
}
}
