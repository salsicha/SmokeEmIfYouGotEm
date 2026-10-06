#pragma once
#include "RaftSimHullContact.h"
#include "Algo/Sort.h"

// Exact immutable original-face hierarchy. Node boxes contain every original
// source vertex; the query adds the integrator's whole curved-path enclosure.
// Deformation never inherits a rigid proof and falls back to all source faces.
struct FRaftSimHullFaceTree
{
    struct FNode{FBox Box{ForceInit};int32 Begin=0,Count=0,Left=INDEX_NONE,Right=INDEX_NONE;};
    TArray<FVector> Vertices;TArray<FIntVector> Faces;TArray<int32> Ids;TArray<FNode> Nodes;
    void Build(const FRaftSimHullGeometry& H)
    {
        Vertices=H.VerticesM;Faces=H.Faces;Ids.Reset();Nodes.Reset();
        for(int32 I=0;I<Faces.Num();++I)Ids.Add(I);
        TFunction<int32(int32,int32)> Add=[&](int32 Begin,int32 Count)
        {
            FNode N;N.Begin=Begin;N.Count=Count;
            for(int32 I=Begin;I<Begin+Count;++I)for(int32 J=0;J<3;++J)N.Box+=Vertices[Faces[Ids[I]][J]];
            const int32 Index=Nodes.Add(N);
            if(Count>24)
            {
                const auto Size=N.Box.GetSize();const int32 Axis=Size.X>Size.Y?(Size.X>Size.Z?0:2):(Size.Y>Size.Z?1:2);
                const auto Center=[&](int32 I){const auto F=Faces[I];return (Vertices[F.X][Axis]+Vertices[F.Y][Axis]+Vertices[F.Z][Axis])/3.;};
                Algo::Sort(MakeArrayView(Ids.GetData()+Begin,Count),[&](int32 A,int32 B){return Center(A)<Center(B);});
                const int32 Left=Add(Begin,Count/2),Right=Add(Begin+Count/2,Count-Count/2);
                Nodes[Index].Left=Left;Nodes[Index].Right=Right;
            }
            return Index;
        };
        if(Faces.Num())Add(0,Faces.Num());
    }
    template<class Overlap>
    TArray<int32> Candidates(const FRaftSimHullArcPath& Arc,double SkinM,const FVector& OriginM,Overlap&& HasGround)
    {
        TArray<int32> Result;
        if(Arc.Before->VerticesM!=Arc.After->VerticesM)
        {for(int32 I=0;I<Arc.Before->Faces.Num();++I)Result.Add(I);return Result;}
        if(Vertices!=Arc.Before->VerticesM || Faces!=Arc.Before->Faces)Build(*Arc.Before);
        auto End=Arc.State;RaftSimSweptGround::Advance(End,Arc.Interval);
        TFunction<void(int32)> Visit=[&](int32 Index)
        {
            const auto& N=Nodes[Index];FBox Box(ForceInit);
            for(int32 I=0;I<8;++I)
            {
                const FVector P(I&1?N.Box.Max.X:N.Box.Min.X,I&2?N.Box.Max.Y:N.Box.Min.Y,I&4?N.Box.Max.Z:N.Box.Min.Z);
                Box+=Arc.State.WorldPoint(P)-OriginM;Box+=End.WorldPoint(P)-OriginM;
            }
            if(!HasGround(Box.ExpandBy(SkinM+1.e-10)))return;
            if(N.Left==INDEX_NONE){for(int32 I=N.Begin;I<N.Begin+N.Count;++I)Result.Add(Ids[I]);}
            else{Visit(N.Left);Visit(N.Right);}
        };
        if(Nodes.Num())Visit(0);Result.Sort();return Result;
    }
};
