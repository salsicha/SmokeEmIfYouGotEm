#pragma once
#include "CoreMinimal.h"
#include "Misc/Parse.h"

namespace RaftSimFaceOrdering
{
// Qualified exact ordering is the normal path. The original sort remains an
// explicit diagnostic control; it takes precedence over the legacy opt-in.
inline bool UsesRadixLandscapeOrder(const TCHAR* CommandLine)
{
    return !FParse::Param(CommandLine,TEXT("RaftSimReferenceLandscapeOrder"));
}

// Exact ascending signed-integer order, including duplicates and the complete
// int32 domain. No face removal, altered collision bounds, or order relaxation.
// Scratch belongs to the caller/query; no mutable shared state in a const tree.
inline void Radix(TArray<int32>& Values,TArray<int32>& Scratch)
{
    check(&Values!=&Scratch);
    if(Values.Num()<2)return;
    const auto Key=[](int32 Value){return uint32(Value)^0x80000000u;};
    const uint32 First=Key(Values[0]);uint32 Variation=0;
    for(const int32 Value:Values)Variation|=Key(Value)^First;
    if(!Variation)return;
    Scratch.SetNumUninitialized(Values.Num());
    int32* Source=Values.GetData();int32* Destination=Scratch.GetData();
    for(uint32 Shift=0;Shift<32;Shift+=8)
    {
        if(!(Variation&(0xffu<<Shift)))continue;
        int32 Counts[256]={};
        for(int32 I=0;I<Values.Num();++I)++Counts[(Key(Source[I])>>Shift)&0xffu];
        int32 Offset=0;
        for(int32 I=0;I<256;++I){const int32 Count=Counts[I];Counts[I]=Offset;Offset+=Count;}
        for(int32 I=0;I<Values.Num();++I)
        {
            const int32 Value=Source[I];Destination[Counts[(Key(Value)>>Shift)&0xffu]++]=Value;
        }
        Swap(Source,Destination);
    }
    if(Source!=Values.GetData())FMemory::Memcpy(Values.GetData(),Source,Values.Num()*sizeof(int32));
}
}
