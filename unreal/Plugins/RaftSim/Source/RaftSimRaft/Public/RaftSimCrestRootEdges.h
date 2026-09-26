#pragma once
#include "RaftSimIndexedEdgeMap.h"

// Cache incidence, not selected edges or heights. Root triangle connectivity
// usually outlives moving shoreline coordinates and current selection masks.
// Each triangle corner identifies its outgoing edge; shared/reversed edges
// address the same slot. Current midpoint IDs are reset on EVERY preparation.
class FRaftSimCrestRootEdges
{
    TArray<int32> CachedTriangles,CornerEdges,Values;
    int32 CachedVertexCount=INDEX_NONE,Inserted=0;
public:
    uint64 Builds=0,Reuses=0;
    void Reset()
    {CachedVertexCount=INDEX_NONE;CachedTriangles.Reset();CornerEdges.Reset();Values.Reset();Inserted=0;}
    void Prepare(const TArray<int32>& Triangles,int32 VertexCount)
    {
        if(CachedVertexCount!=VertexCount || CachedTriangles!=Triangles)
        {
            FRaftSimIndexedEdgeMap Edges(VertexCount);
            CornerEdges.SetNumUninitialized(Triangles.Num());
            int32 Count=0;
            for(int32 I=0;I<Triangles.Num();I+=3)for(int32 E=0;E<3;++E)
            {
                const int32 A=Triangles[I+E],B=Triangles[I+(E+1)%3];
                const uint64 Key=(uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));
                const int32 Slot=Edges.FindOrAdd(Key,Count);
                if(Slot==Count)++Count;
                CornerEdges[I+E]=Slot;
            }
            Values.SetNumUninitialized(Count);
            CachedTriangles=Triangles;CachedVertexCount=VertexCount;++Builds;
        }
        else ++Reuses;
        for(auto& Value:Values)Value=INDEX_NONE;
        Inserted=0;
    }
    const int32* Find(uint64 Corner) const
    {
        const int32& Value=Values[CornerEdges[int32(Corner)]];
        return Value==INDEX_NONE ? nullptr : &Value;
    }
    bool Contains(uint64 Corner) const{return Find(Corner)!=nullptr;}
    void Add(uint64 Corner,int32 Value)
    {
        int32& Slot=Values[CornerEdges[int32(Corner)]];
        Inserted+=Slot==INDEX_NONE;Slot=Value;
    }
    bool IsEmpty() const{return Inserted==0;}
    uint64 GetAllocatedSize() const
    {return CachedTriangles.GetAllocatedSize()+CornerEdges.GetAllocatedSize()+Values.GetAllocatedSize();}
};
