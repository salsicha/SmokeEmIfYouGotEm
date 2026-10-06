#pragma once
#include "CoreMinimal.h"
#include "RaftSimCoordinateMap.h"
#include "Containers/SparseSet.h"

// Retain exact lookup bindings, never heights across profile epochs. Each
// instance has one worker owner. Sparse-set handles survive growth/rehashing;
// a full coordinate comparison guards every handle before it is reused.
class FRaftSimBoundCoordinateMemo
{
    struct FSample { FVector2D Position; float Value=0; uint64 Epoch=0; };
    struct FKeys : BaseKeyFuncs<FSample,FVector2D,false>
    {
        static const FVector2D& GetSetKey(const FSample& Sample) { return Sample.Position; }
        static bool Matches(const FVector2D& A,const FVector2D& B) { return A==B; }
        static uint32 GetKeyHash(const FVector2D& P) { return TRaftSimCoordinateKeyFuncs<int32>::GetKeyHash(P); }
    };
    // Explicit sparse storage: never compact/remove individual elements, so
    // adding or rehashing cannot invalidate an existing binding. The position
    // is the hash key AND handle guard; no second copy of every key is needed.
    TSparseSet<FSample,FKeys> Samples;
    TArray<FSetElementId> Bindings;
public:
    void Prepare(int32 Count)
    {
        if(Bindings.Num()!=Count) Bindings.Init(FSetElementId(),Count);
    }
    void Reset()
    {
        Samples.Reset(); Bindings.Reset();
    }
    int32 Num() const { return Samples.Num(); }
    SIZE_T GetAllocatedSize() const
    { return Samples.GetAllocatedSize()+Bindings.GetAllocatedSize(); }

    template<typename THeight>
    float Value(const FVector2D& P,int32 Binding,uint64 Epoch,THeight Height)
    {
        check(Bindings.IsValidIndex(Binding) && Epoch!=0);
        FSetElementId Index=Bindings[Binding];
        if(!Samples.IsValidId(Index) || Samples[Index].Position!=P)
        {
            Index=Samples.FindId(P);
            if(!Index.IsValidId())
            {
                // Preserve the existing 4096-coordinate cap. Invalidate ALL
                // handles before indices can be reused for different points.
                if(Samples.Num()>=4096)
                {
                    Samples.Reset();
                    Bindings.Init(FSetElementId(),Bindings.Num());
                }
                Index=Samples.Add(FSample{P,0,0});
            }
            Bindings[Binding]=Index;
        }
        auto& Sample=Samples[Index];
        if(Sample.Epoch!=Epoch) { Sample.Value=Height(P); Sample.Epoch=Epoch; }
        return Sample.Value;
    }
};
