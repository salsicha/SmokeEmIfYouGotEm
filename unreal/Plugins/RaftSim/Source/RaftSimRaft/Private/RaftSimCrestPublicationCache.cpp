#include "RaftSimCrestPublicationCache.h"
#include "RaftSimCrestTopologyPublish.h"

void FRaftSimCrestPublicationCache::Reset()
{
    CachedOrigins.Reset();CachedSourceOffsets.Reset();CachedOffsets.Reset();
    bValid=false;bReused=false;
}

void FRaftSimCrestPublicationCache::Publish(const TArray<int32>& Triangles,
    const TArray<int32>& Origins,const TArray<int32>& SourceOffsets,
    TArray<uint32>& Indices,TArray<int32>& Offsets)
{
    // Compare complete integer keys, not a hash or an assumed topology epoch.
    // This also preserves the reference's behavior for unordered ownership.
    bReused=bValid && CachedOrigins==Origins && CachedSourceOffsets==SourceOffsets;
    if (bReused)
    {
        static_assert(sizeof(int32)==sizeof(uint32));
        Indices.SetNumUninitialized(Triangles.Num());
        if (!Triangles.IsEmpty())FMemory::Memcpy(Indices.GetData(),Triangles.GetData(),SIZE_T(Triangles.Num())*sizeof(int32));
        Offsets=CachedOffsets;
        return;
    }
    RaftSimCrestTopologyPublish::Partitioned(Triangles,Origins,SourceOffsets,Indices,Offsets);
    CachedOrigins=Origins;CachedSourceOffsets=SourceOffsets;CachedOffsets=Offsets;bValid=true;
}
