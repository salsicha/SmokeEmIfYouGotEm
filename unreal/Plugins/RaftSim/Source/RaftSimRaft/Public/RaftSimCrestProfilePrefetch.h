#pragma once
#include "RaftSimSurfaceRefinement.h"
#include "Async/Async.h"

// One owned immutable job, never a queue of obsolete hydraulic states. The
// worker owns all coordinates, the key and the pure profile callback; it cannot
// access a component, actor, current mesh or correction history. Destruction or
// reset may discard a job, but cannot invalidate its inputs.
class FRaftSimCrestProfilePrefetch
{
    struct FResult
    {
        TArray<double> Key;
        FRaftSimSurfaceRefinement::FPreparedProfileSamples Samples;
    };
    TFuture<FResult> Pending;
public:
    void Reset(){Pending=TFuture<FResult>();}
    bool IsPending() const{return Pending.IsValid();}
    bool IsReady() const{return Pending.IsValid() && Pending.IsReady();}
    bool Start(const FRaftSimSurfaceRefinement& Source,const TArray<double>& Key,
        const TFunction<float(const FVector2D&)>& Height)
    {
        if(!Height || Key.IsEmpty())return false;
        if(Pending.IsValid())
        {
            if(!Pending.IsReady())return false; // No waiting or unbounded backlog.
            Pending.Get();Pending=TFuture<FResult>();
        }
        auto Coordinates=Source.SnapshotProfileSampleCoordinates();
        int64 Count=0;for(const auto& Batch:Coordinates)Count+=Batch.Num();
        if(Count==0)return false;
        Pending=Async(EAsyncExecution::ThreadPool,
            [Coordinates=MoveTemp(Coordinates),Key,Height]() mutable
            {
                FResult Result;Result.Key=Key;Result.Samples.SetNum(Coordinates.Num());
                // A single background worker avoids nesting a competing
                // all-core ParallelFor during the game's remaining tick.
                for(int32 I=0;I<Coordinates.Num();++I)
                {
                    auto& Samples=Result.Samples[I];Samples.Reserve(Coordinates[I].Num());
                    for(const auto& P:Coordinates[I])Samples.Add(P,{Height(P),0});
                }
                return Result;
            });
        return true;
    }
    bool AdoptIfReady(const TArray<double>& Key,FRaftSimSurfaceRefinement& Destination,
        const TFunction<float(const FVector2D&)>* AuditHeight=nullptr)
    {
        if(!IsReady())return false;
        auto Result=Pending.Consume();
        if(Result.Key!=Key)return false;
        if(AuditHeight)
        {
            int32 Count=0;
            for(const auto& Batch:Result.Samples)for(const auto& Entry:Batch)
            {
                const float Expected=(*AuditHeight)(Entry.Key);
                if(FMemory::Memcmp(&Expected,&Entry.Value.Value,sizeof(float))!=0)
                {
                    UE_LOG(LogTemp,Error,TEXT("CrestPrefetchAudit mismatch frame=%llu"),GFrameCounter);
                    return false; // Reject every prepared value, not just this point.
                }
                ++Count;
            }
            UE_LOG(LogTemp,Display,TEXT("CrestPrefetchAudit exact frame=%llu samples=%d batches=%d"),
                GFrameCounter,Count,Result.Samples.Num());
        }
        Destination.AdoptPreparedProfileSamples(MoveTemp(Result.Samples));
        return true;
    }
};
