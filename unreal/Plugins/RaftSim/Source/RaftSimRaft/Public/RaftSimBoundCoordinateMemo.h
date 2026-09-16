#pragma once
#include "CoreMinimal.h"
#include "RaftSimCoordinateMap.h"

// Retain exact lookup bindings, never heights across profile epochs. Each
// instance has one worker owner. Integer handles survive array/map relocation;
// a full coordinate comparison guards every handle before it is reused.
class FRaftSimBoundCoordinateMemo
{
    struct FSample { FVector2D Position; float Value=0; uint64 Epoch=0; };
    TRaftSimCoordinateMap<int32> Lookup;
    TArray<FSample> Samples;
    TArray<int32> Bindings;
public:
    void Prepare(int32 Count)
    {
        if(Bindings.Num()!=Count) Bindings.Init(INDEX_NONE,Count);
    }
    void Reset()
    {
        Lookup.Reset(); Samples.Reset(); Bindings.Reset();
    }
    int32 Num() const { return Samples.Num(); }
    SIZE_T GetAllocatedSize() const
    { return Lookup.GetAllocatedSize()+Samples.GetAllocatedSize()+Bindings.GetAllocatedSize(); }

    template<typename THeight>
    float Value(const FVector2D& P,int32 Binding,uint64 Epoch,THeight Height)
    {
        check(Bindings.IsValidIndex(Binding) && Epoch!=0);
        int32 Index=Bindings[Binding];
        if(!Samples.IsValidIndex(Index) || Samples[Index].Position!=P)
        {
            if(const int32* Found=Lookup.Find(P)) Index=*Found;
            else
            {
                // Preserve the existing 4096-coordinate cap. Invalidate ALL
                // handles before indices can be reused for different points.
                if(Samples.Num()>=4096)
                {
                    Lookup.Reset(); Samples.Reset();
                    Bindings.Init(INDEX_NONE,Bindings.Num());
                }
                Index=Samples.Add({P,0,0}); Lookup.Add(P,Index);
            }
            Bindings[Binding]=Index;
        }
        auto& Sample=Samples[Index];
        if(Sample.Epoch!=Epoch) { Sample.Value=Height(P); Sample.Epoch=Epoch; }
        return Sample.Value;
    }
};
