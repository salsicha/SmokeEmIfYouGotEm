#pragma once
#include "RaftSimHullContact.h"
#include "Algo/Sort.h"

// Acceleration ONLY: leaves retain original face IDs and exact source vertices.
// A rigid node is rejected only by an endpoint bounding-box / ground-plane
// separation proof with the integrator's complete curved-path clearance.
// Changed/deforming geometry falls back to the exhaustive original query.
namespace RaftSimFlipHullBroadphase
{
struct FNode {FBox Box{ForceInit};int32 Begin=0,Count=0,Left=INDEX_NONE,Right=INDEX_NONE;};
struct FCache {TArray<FVector> Vertices;TArray<FIntVector> Faces;TArray<int32> Ids;TArray<FNode> Nodes;};
inline TArray<int32> Candidates(const FRaftSimHullArcPath* Arc,TConstArrayView<FIntVector> Faces,
    TConstArrayView<FVector> Ground,TConstArrayView<FIntVector> GroundFaces,double SkinCm,double ClearanceCm)
{
    TArray<int32> Result;
    if(!Arc || Arc->Before->VerticesM!=Arc->After->VerticesM)
    {for(int32 I=0;I<Faces.Num();++I)Result.Add(I);return Result;}
    static thread_local FCache Cache;
    if(Cache.Vertices!=Arc->Before->VerticesM || Cache.Faces!=Arc->Before->Faces)
    {
        Cache.Vertices=Arc->Before->VerticesM;Cache.Faces=Arc->Before->Faces;Cache.Ids.Reset();Cache.Nodes.Reset();
        for(int32 I=0;I<Faces.Num();++I)Cache.Ids.Add(I);
        TFunction<int32(int32,int32)> Build=[&](int32 Begin,int32 Count)
        {
            FNode Node;Node.Begin=Begin;Node.Count=Count;
            for(int32 I=Begin;I<Begin+Count;++I)for(int32 K=0;K<3;++K)Node.Box+=Cache.Vertices[Cache.Faces[Cache.Ids[I]][K]];
            const int32 Index=Cache.Nodes.Add(Node);
            if(Count>24)
            {
                const FVector Size=Node.Box.GetSize();const int32 Axis=Size.X>Size.Y ? (Size.X>Size.Z?0:2) : (Size.Y>Size.Z?1:2);
                const auto Center=[&](int32 F){const auto T=Cache.Faces[F];return (Cache.Vertices[T.X][Axis]+Cache.Vertices[T.Y][Axis]+Cache.Vertices[T.Z][Axis])/3.;};
                Algo::Sort(MakeArrayView(Cache.Ids.GetData()+Begin,Count),[&](int32 A,int32 B){return Center(A)<Center(B);});
                const int32 Half=Count/2;const int32 Left=Build(Begin,Half),Right=Build(Begin+Half,Count-Half);
                Cache.Nodes[Index].Left=Left;Cache.Nodes[Index].Right=Right;
            }
            return Index;
        };
        Build(0,Faces.Num());
    }
    auto End=Arc->State;RaftSimSweptGround::Advance(End,Arc->Interval);
    TFunction<void(int32)> Collect=[&](int32 Index)
    {
        const auto& Node=Cache.Nodes[Index];FVector Corners[16];FBox Bounds(ForceInit);
        for(int32 I=0;I<8;++I)
        {
            const FVector Local(I&1?Node.Box.Max.X:Node.Box.Min.X,I&2?Node.Box.Max.Y:Node.Box.Min.Y,I&4?Node.Box.Max.Z:Node.Box.Min.Z);
            Corners[I]=Arc->State.WorldPoint(Local);Corners[I+8]=End.WorldPoint(Local);Bounds+=Corners[I];Bounds+=Corners[I+8];
        }
        Bounds=Bounds.ExpandBy(SkinCm*.01);bool Possible=false;
        for(const auto& F:GroundFaces)
        {
            const FVector A=Ground[F.X]*.01,B=Ground[F.Y]*.01,C=Ground[F.Z]*.01;
            FBox GB(ForceInit);GB+=A;GB+=B;GB+=C;if(!Bounds.Intersect(GB))continue;
            const FVector N=FVector::CrossProduct(B-A,C-A).GetSafeNormal();
            double Minimum=DBL_MAX,Maximum=-DBL_MAX;
            for(const auto& P:Corners){const double D=FVector::DotProduct(P-A,N);Minimum=FMath::Min(Minimum,D);Maximum=FMath::Max(Maximum,D);}
            if(N.IsNearlyZero() || (Minimum<=SkinCm*.01 && Maximum>=-SkinCm*.01)){Possible=true;break;}
        }
        if(!Possible)return;
        if(Node.Left==INDEX_NONE)
        {for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)Result.Add(Cache.Ids[I]);}
        else {Collect(Node.Left);Collect(Node.Right);}
    };
    if(Cache.Nodes.Num())Collect(0);
    Result.Sort(); // Preserve original triangle tie-breaking, not BVH order.
    return Result;
}
}
