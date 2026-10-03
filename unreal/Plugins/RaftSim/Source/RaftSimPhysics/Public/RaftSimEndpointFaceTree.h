#pragma once
#include "CoreMinimal.h"
#include "Algo/Sort.h"

// Broad phase for the EXISTING endpoint-triangle sweep. Refit every original
// face from both current endpoints and the caller's existing curved-path skin.
// No rest-pose/rigid assumption, reduced hull, tolerance, or new contact rule.
// Queries return exactly the original AABB-overlapping face IDs, in ascending
// order, preserving the exhaustive narrow phase's first-hit ties and failures.
struct FRaftSimEndpointFaceTree
{
    struct FNode { FBox Bounds{ForceInit}; int32 Begin=0,Count=0,Left=INDEX_NONE,Right=INDEX_NONE; };
    TArray<FIntVector> Topology;
    TArray<int32> FaceIds;
    TArray<FBox> VertexEndpointBounds;
    TArray<FBox> FaceBounds;
    TArray<FNode> Nodes;
    int32 VertexCount=0;

    bool Refit(TConstArrayView<FVector> StartCm,TConstArrayView<FVector> EndCm,
        TConstArrayView<FIntVector> Faces,double SkinCm,bool bAlreadyMeters=false)
    {
        if(StartCm.IsEmpty() || StartCm.Num()!=EndCm.Num() || Faces.IsEmpty() ||
            !FMath::IsFinite(SkinCm) || SkinCm<=0.)return false;
        VertexEndpointBounds.SetNumUninitialized(StartCm.Num());
        for(int32 I=0;I<StartCm.Num();++I)
        {
            if(StartCm[I].ContainsNaN() || EndCm[I].ContainsNaN())return false;
            // The same two points and arithmetic as the original face loop,
            // evaluated once per original vertex instead of at every incident
            // face. Refreshed on EVERY call, including arbitrary deformation.
            FBox Box(ForceInit);
            if(bAlreadyMeters){Box+=StartCm[I];Box+=EndCm[I];}
            else {Box+=StartCm[I]*.01;Box+=EndCm[I]*.01;}
            VertexEndpointBounds[I]=Box;
        }
        FaceBounds.SetNumUninitialized(Faces.Num());
        for(int32 I=0;I<Faces.Num();++I)
        {
            FBox Box(ForceInit);
            for(int32 J=0;J<3;++J)
            {
                const int32 V=Faces[I][J];
                if(!StartCm.IsValidIndex(V))return false;
                // Union the same six endpoints; every original face and index
                // is still inspected, in the original order. No rigid/rest
                // shape approximation or inherited previous-pose bounds.
                Box+=VertexEndpointBounds[V];
            }
            FaceBounds[I]=Box.ExpandBy(bAlreadyMeters?SkinCm:SkinCm*.01);
        }
        const bool SameTopology=VertexCount==StartCm.Num() && Topology.Num()==Faces.Num() &&
            FMemory::Memcmp(Topology.GetData(),Faces.GetData(),Faces.Num()*sizeof(FIntVector))==0;
        if(!SameTopology)
        {
            VertexCount=StartCm.Num();Topology.Reset(Faces.Num());Topology.Append(Faces.GetData(),Faces.Num());
            FaceIds.Reset(Faces.Num());Nodes.Reset();
            for(int32 I=0;I<Faces.Num();++I)FaceIds.Add(I);
            TFunction<int32(int32,int32)> Add=[&](int32 Begin,int32 Count)
            {
                FNode Node;Node.Begin=Begin;Node.Count=Count;
                for(int32 I=Begin;I<Begin+Count;++I)Node.Bounds+=FaceBounds[FaceIds[I]];
                const int32 Index=Nodes.Add(Node);
                if(Count>24)
                {
                    const FVector Size=Node.Bounds.GetSize();
                    const int32 Axis=Size.X>Size.Y?(Size.X>Size.Z?0:2):(Size.Y>Size.Z?1:2);
                    Algo::Sort(MakeArrayView(FaceIds.GetData()+Begin,Count),[&](int32 A,int32 B)
                        {return FaceBounds[A].GetCenter()[Axis]<FaceBounds[B].GetCenter()[Axis];});
                    const int32 ChildLeft=Add(Begin,Count/2),ChildRight=Add(Begin+Count/2,Count-Count/2);
                    Nodes[Index].Left=ChildLeft;Nodes[Index].Right=ChildRight;
                }
                return Index;
            };
            Add(0,Faces.Num());
        }
        else
        {
            // Parents precede children. Reverse order refits every leaf and
            // then unions its exact children, even after arbitrary deformation.
            for(int32 Index=Nodes.Num()-1;Index>=0;--Index)
            {
                auto& Node=Nodes[Index];Node.Bounds=FBox(ForceInit);
                if(Node.Left==INDEX_NONE)
                    for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)Node.Bounds+=FaceBounds[FaceIds[I]];
                else {Node.Bounds+=Nodes[Node.Left].Bounds;Node.Bounds+=Nodes[Node.Right].Bounds;}
            }
        }
        return true;
    }

    // Separate collection from ordering so native profiling can measure the
    // two costs independently. Unordered results never enter narrow phase.
    void GatherCandidates(const FBox& GroundBounds,TArray<int32>& Result) const
    {
        Result.Reset();if(Nodes.IsEmpty())return;
        TArray<int32,TInlineAllocator<64>> Pending;Pending.Add(0);
        while(!Pending.IsEmpty())
        {
            const auto& Node=Nodes[Pending.Pop(EAllowShrinking::No)];
            if(!Node.Bounds.Intersect(GroundBounds))continue;
            if(Node.Left==INDEX_NONE)
                for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)
                {
                    const int32 Face=FaceIds[I];
                    if(FaceBounds[Face].Intersect(GroundBounds))Result.Add(Face);
                }
            else {Pending.Add(Node.Left);Pending.Add(Node.Right);}
        }
    }

    void Candidates(const FBox& GroundBounds,TArray<int32>& Result) const
    {
        GatherCandidates(GroundBounds,Result);Result.Sort();
    }

    // Captured mesh ground has its own immutable tree. Reject only groups
    // whose complete endpoint enclosure misses that tree; original per-face
    // bounds and triangle sweeps still run, in original order, afterward.
    template<class Overlap>
    void CandidateGroups(Overlap&& HasGround,TArray<int32>& Result) const
    {
        Result.Reset();if(Nodes.IsEmpty())return;
        TArray<int32,TInlineAllocator<64>> Pending;Pending.Add(0);
        while(!Pending.IsEmpty())
        {
            const auto& Node=Nodes[Pending.Pop(EAllowShrinking::No)];
            if(!HasGround(Node.Bounds))continue;
            if(Node.Left==INDEX_NONE)
                for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)Result.Add(FaceIds[I]);
            else {Pending.Add(Node.Left);Pending.Add(Node.Right);}
        }
        Result.Sort();
    }
};
