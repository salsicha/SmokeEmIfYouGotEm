#pragma once
#include "CoreMinimal.h"
#include <atomic>

// One immutable profile epoch, shared by its parallel refinement queries.
// This diagnostic compares EVERY actual query, not a separate sample lattice.
// Destruction happens only after all captured query functions release it.
struct FRaftSimFineCrestIndexAudit
{
    const uint64 Frame=GFrameCounter;
    std::atomic<uint64> Queries{0},Mismatches{0};
    void Compare(float Reference,float Candidate)
    {
        Queries.fetch_add(1,std::memory_order_relaxed);
        if(!FMath::IsFinite(Reference) || Reference!=Candidate)
            Mismatches.fetch_add(1,std::memory_order_relaxed);
    }
    ~FRaftSimFineCrestIndexAudit()
    {
        UE_LOG(LogTemp,Display,TEXT("FINE_CREST_INDEX_EPOCH frame=%llu queries=%llu mismatches=%llu"),
            Frame,Queries.load(std::memory_order_relaxed),Mismatches.load(std::memory_order_relaxed));
    }
};
