#pragma once
#include "CoreMinimal.h"

// Cache cell ownership only. Current triangle indices are always republished;
// neither coordinates nor evolving vertex/crest attributes are cached here.
class RAFTSIMRAFT_API FRaftSimCrestPublicationCache
{
public:
    void Publish(const TArray<int32>& Triangles,const TArray<int32>& Origins,
        const TArray<int32>& SourceOffsets,TArray<uint32>& Indices,TArray<int32>& Offsets);
    void Reset();
    bool WasReused() const { return bReused; }
private:
    TArray<int32> CachedOrigins,CachedSourceOffsets,CachedOffsets;
    bool bValid=false,bReused=false;
};
