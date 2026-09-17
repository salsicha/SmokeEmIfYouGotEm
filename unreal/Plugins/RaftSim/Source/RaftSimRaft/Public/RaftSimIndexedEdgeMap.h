#pragma once
#include "CoreMinimal.h"

// Canonical edges between this level's immutable indexed vertices. Meshes
// normally have few edges per lower endpoint, so direct indexing avoids a
// hash lookup. Limit each chain to eight; unusual/nonmanifold fans spill to
// the ordinary map instead of turning lookup into a linear vertex-degree scan.
// No iteration order is exposed: assembly retains its original triangle order.
class FRaftSimIndexedEdgeMap
{
    struct FEntry { uint32 Other; int32 Value,Next; };
    TArray<int32> Heads;
    TArray<FEntry> Entries;
    TMap<uint64,int32> Overflow;
public:
    explicit FRaftSimIndexedEdgeMap(int32 VertexCount) { Heads.Init(INDEX_NONE,VertexCount); }
    const int32* Find(uint64 Key) const
    {
        const uint32 Lower=uint32(Key>>32),Other=uint32(Key);
        check(Lower<uint32(Heads.Num()));
        int32 Count=0;
        for(int32 I=Heads[Lower];I!=INDEX_NONE;I=Entries[I].Next)
        {
            if(Entries[I].Other==Other)return &Entries[I].Value;
            ++Count;
        }
        return Count==8 ? Overflow.Find(Key) : nullptr;
    }
    bool Contains(uint64 Key) const { return Find(Key)!=nullptr; }
    bool IsEmpty() const { return Entries.IsEmpty() && Overflow.IsEmpty(); }
    int32& FindOrAdd(uint64 Key,int32 Default=0)
    {
        const uint32 Lower=uint32(Key>>32),Other=uint32(Key);
        check(Lower<uint32(Heads.Num()));
        int32 Count=0;
        for(int32 I=Heads[Lower];I!=INDEX_NONE;I=Entries[I].Next)
        {
            if(Entries[I].Other==Other)return Entries[I].Value;
            ++Count;
        }
        if(Count==8)return Overflow.FindOrAdd(Key,Default);
        const int32 Index=Entries.Add(FEntry{Other,Default,Heads[Lower]});
        Heads[Lower]=Index;
        return Entries[Index].Value;
    }
    void Add(uint64 Key,int32 Value)
    {
        const uint32 Lower=uint32(Key>>32),Other=uint32(Key);
        check(Lower<uint32(Heads.Num()));
        int32 Count=0;
        for(int32 I=Heads[Lower];I!=INDEX_NONE;I=Entries[I].Next)
        {
            if(Entries[I].Other==Other){Entries[I].Value=Value;return;}
            ++Count;
        }
        if(Count==8){Overflow.Add(Key,Value);return;}
        const int32 Index=Entries.Add(FEntry{Other,Value,Heads[Lower]});
        Heads[Lower]=Index;
    }
};
