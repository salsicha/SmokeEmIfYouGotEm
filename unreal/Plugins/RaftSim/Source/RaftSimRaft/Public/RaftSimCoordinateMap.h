#pragma once
#include "CoreMinimal.h"

// In-memory lookup only: preserve the complete double coordinates and exact
// FVector2D equality. No rounding, welding, interpolation or persisted hash.
// The engine's default FVector2D hash uses a general memory CRC. These fixed
// two-word keys can be mixed directly without its byte-table lookups.
template<typename Value>
struct TRaftSimCoordinateKeyFuncs : TDefaultMapKeyFuncs<FVector2D,Value,false>
{
    static uint64 Mix(uint64 H)
    {
        H^=H>>30;H*=0xbf58476d1ce4e5b9ull;
        H^=H>>27;H*=0x94d049bb133111ebull;
        return H^(H>>31);
    }
    static uint32 GetKeyHash(const FVector2D& P)
    {
        // Numeric equality identifies both signed zeroes. All other bits,
        // including subnormal coordinates, remain in the key and the hash.
        const double X=P.X==0. ? 0. : P.X,Y=P.Y==0. ? 0. : P.Y;
        uint64 XB,YB;FMemory::Memcpy(&XB,&X,sizeof(XB));FMemory::Memcpy(&YB,&Y,sizeof(YB));
        const uint64 H=Mix(Mix(XB)^YB^0x9e3779b97f4a7c15ull);
        return uint32(H)^uint32(H>>32);
    }
};

template<typename Value>
using TRaftSimCoordinateMap=TMap<FVector2D,Value,FDefaultSetAllocator,TRaftSimCoordinateKeyFuncs<Value>>;
