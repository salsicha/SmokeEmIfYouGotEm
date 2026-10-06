#pragma once
#include "CoreMinimal.h"
#include "RenderGraphBuilder.h"

struct FRaftSimLiquidOwnerGraphHistory
{
    FRDGBufferRef Clock=nullptr;
    FRDGTextureRef Foam=nullptr;
    uint32 SecondarySteps=0;
};

// A render graph may contain multiple ticks AND multiple independent liquid
// owners. Reuse intermediate resources only for the same attachment generation.
// A fresh attachment gets a new ID even if its Niagara system is recycled.
// Unique storage keeps references stable if another owner is added mid-graph.
struct FRaftSimLiquidGraphHistories
{
    FRaftSimLiquidOwnerGraphHistory& ForOwner(uint64 Attachment)
    {
        check(Attachment!=0);
        auto& Entry=Owners.FindOrAdd(Attachment);
        if (!Entry) Entry=MakeUnique<FRaftSimLiquidOwnerGraphHistory>();
        return *Entry;
    }
private:
    TMap<uint64,TUniquePtr<FRaftSimLiquidOwnerGraphHistory>> Owners;
};
RDG_REGISTER_BLACKBOARD_STRUCT(FRaftSimLiquidGraphHistories);
