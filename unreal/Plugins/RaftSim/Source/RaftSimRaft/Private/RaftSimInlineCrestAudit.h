#pragma once
#include "CoreMinimal.h"
#include <atomic>

// Audit every query through the actual immutable refinement profile, including
// concurrent workers. No instrumentation in ordinary candidate timing runs.
struct FRaftSimInlineCrestAudit
{
    const uint64 Frame=GFrameCounter;
    std::atomic<uint64> Queries{0},Mismatches{0};
    void Compare(float Reference,float Candidate)
    {
        Queries.fetch_add(1,std::memory_order_relaxed);
        if(!FMath::IsFinite(Reference) || Reference!=Candidate)
            Mismatches.fetch_add(1,std::memory_order_relaxed);
    }
    ~FRaftSimInlineCrestAudit()
    {
        UE_LOG(LogTemp,Display,TEXT("INLINE_CREST_EPOCH frame=%llu queries=%llu mismatches=%llu"),
            Frame,Queries.load(std::memory_order_relaxed),Mismatches.load(std::memory_order_relaxed));
    }
};
