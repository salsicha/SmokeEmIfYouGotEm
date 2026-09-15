#pragma once
#include "CoreMinimal.h"

// In-memory lookup only. Original uint64 edge identity/equality and insertion
// order are unchanged. Grid edges correlate the high and low 32-bit halves;
// avalanche before bucket selection instead of low + 23*high.
inline uint32 RaftSimEdgeHash(uint64 Key)
{
    Key^=Key>>33;Key*=0xff51afd7ed558ccdull;
    Key^=Key>>33;Key*=0xc4ceb9fe1a85ec53ull;Key^=Key>>33;
    return uint32(Key)^uint32(Key>>32);
}

template<typename Value>
struct TRaftSimEdgeMapKeys : TDefaultMapHashableKeyFuncs<uint64,Value,false>
{
    static uint32 GetKeyHash(uint64 Key) { return RaftSimEdgeHash(Key); }
};

template<typename Value>
using TRaftSimEdgeMap=TMap<uint64,Value,FDefaultSetAllocator,TRaftSimEdgeMapKeys<Value>>;
