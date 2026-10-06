#pragma once
#include "RaftSimWaterFlowFrame.h"

// Distances depend only on grid dimensions and every wet-mask byte, not world
// origin, depth, time or current. No checksum can substitute for full equality.
// The caller owns the cache and may borrow Values only until the next Update.
class FRaftSimWetEdgeCache
{
    int32 Width=INDEX_NONE,Height=INDEX_NONE;
    TArray<uint8> Mask;
    TArray<int32> Values;
public:
    void Reset(){Width=Height=INDEX_NONE;Mask.Reset();Values.Reset();}
    bool Matches(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet) const
    {
        return Nx==Width && Ny==Height && Wet.Num()==Mask.Num() &&
            (Wet.IsEmpty() || FMemory::Memcmp(Wet.GetData(),Mask.GetData(),Wet.Num())==0);
    }
    const TArray<int32>& Get() const{return Values;}
    void Store(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet,TArray<int32>&& Result)
    {
        check(Nx>=0 && Ny>=0 && int64(Nx)*Ny==Wet.Num() && Result.Num()==Wet.Num());
        Width=Nx;Height=Ny;Mask.Reset(Wet.Num());Mask.Append(Wet.GetData(),Wet.Num());
        Values=MoveTemp(Result);
    }
};
