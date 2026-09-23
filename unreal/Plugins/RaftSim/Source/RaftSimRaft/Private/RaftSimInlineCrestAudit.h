#pragma once
#include "CoreMinimal.h"
#include <atomic>

// Audit every query through the actual immutable refinement profile, including
// concurrent workers. No instrumentation in ordinary candidate timing runs.
struct FRaftSimInlineCrestAudit
{
    static uint64 NextEpoch()
    {static std::atomic<uint64> Next{0};return Next.fetch_add(1,std::memory_order_relaxed);}
    const uint64 Epoch=NextEpoch();
    const TCHAR* Label;
    explicit FRaftSimInlineCrestAudit(const TCHAR* InLabel=TEXT("INLINE_CREST_EPOCH")):Label(InLabel) {}
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
        if(FCString::Strcmp(Label,TEXT("PREPARED_CREST_EPOCH"))==0)
        {
            UE_LOG(LogTemp,Display,TEXT("PREPARED_CREST_EPOCH epoch=%llu frame=%llu queries=%llu mismatches=%llu"),
                Epoch,Frame,Queries.load(std::memory_order_relaxed),Mismatches.load(std::memory_order_relaxed));
            return;
        }
        UE_LOG(LogTemp,Display,TEXT("%s frame=%llu queries=%llu mismatches=%llu"),
            Label,Frame,Queries.load(std::memory_order_relaxed),Mismatches.load(std::memory_order_relaxed));
    }
};
