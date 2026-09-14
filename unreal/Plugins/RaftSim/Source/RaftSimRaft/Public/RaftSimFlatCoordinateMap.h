#pragma once
#include "RaftSimCoordinateMap.h"

// Batch-owned exact lookup. Dense entries retain full double keys and values;
// open-addressed integer buckets avoid the node-chain lookup of TMap. No key
// quantization or value reuse policy lives here. Callers still own epochs.
template<typename Value>
class TRaftSimFlatCoordinateMap
{
    struct FEntry { FVector2D Key; Value Data; };
    TArray<FEntry> Entries;
    TArray<int32> Buckets;
    uint32 Slot(const FVector2D& Key) const
    { return TRaftSimCoordinateKeyFuncs<Value>::GetKeyHash(Key)&uint32(Buckets.Num()-1); }
    void Rehash(int32 Count)
    {
        Buckets.Init(INDEX_NONE,Count);
        for(int32 I=0;I<Entries.Num();++I)
        {
            uint32 S=Slot(Entries[I].Key);
            while(Buckets[S]!=INDEX_NONE) S=(S+1)&uint32(Count-1);
            Buckets[S]=I;
        }
    }
public:
    int32 Num() const { return Entries.Num(); }
    uint64 GetAllocatedSize() const { return Entries.GetAllocatedSize()+Buckets.GetAllocatedSize(); }
    void Reset()
    {
        Entries.Reset();
        for(auto& Bucket:Buckets)Bucket=INDEX_NONE;
    }
    Value* Find(const FVector2D& Key)
    {
        if(Buckets.IsEmpty())return nullptr;
        uint32 S=Slot(Key);
        for(;;)
        {
            const int32 I=Buckets[S];
            if(I==INDEX_NONE)return nullptr;
            if(Entries[I].Key==Key)return &Entries[I].Data;
            S=(S+1)&uint32(Buckets.Num()-1);
        }
    }
    Value& FindOrAdd(const FVector2D& Key,int32 EntryLimit=MAX_int32)
    {
        check(EntryLimit>0);
        uint32 S=0;
        if(!Buckets.IsEmpty())
        {
            S=Slot(Key);
            while(Buckets[S]!=INDEX_NONE)
            {
                const int32 I=Buckets[S];
                if(Entries[I].Key==Key)return Entries[I].Data;
                S=(S+1)&uint32(Buckets.Num()-1);
            }
        }
        // Like the original caller: reset only on an absent key at the cap,
        // never evict a hit. The returned default value has no valid epoch.
        if(Entries.Num()>=EntryLimit){Reset();S=Slot(Key);}
        // Always leave an empty bucket, including after growth or reset.
        if((Entries.Num()+1)*2>Buckets.Num())
        {Rehash(FMath::Max(16,Buckets.Num()*2));S=Slot(Key);}
        while(Buckets[S]!=INDEX_NONE)S=(S+1)&uint32(Buckets.Num()-1);
        const int32 I=Entries.Add({Key,Value{}});
        Buckets[S]=I;
        return Entries[I].Data;
    }
    void Add(const FVector2D& Key,const Value& Data) { FindOrAdd(Key)=Data; }
};
