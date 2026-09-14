#pragma once
#include "CoreMinimal.h"

// A bounded work queue, not a timestep/quality reduction. Wall-time debt is
// retained as elapsed time until a complete fixed tick succeeds, never clipped.
struct FRaftSimFixedStepClock
{
    double RequestedSeconds=0,CommittedSeconds=0,BacklogSeconds=0;
    uint64 CommittedTicks=0;
    void Reset(){*this=FRaftSimFixedStepClock();}
    template<typename Tick>
    bool Advance(double FrameSeconds,double StepSeconds,int32 MaximumTicks,Tick&& RunTick,int32& Completed)
    {
        Completed=0;
        if(!FMath::IsFinite(FrameSeconds) || FrameSeconds<0 || !FMath::IsFinite(StepSeconds) || StepSeconds<=0 || MaximumTicks<1 ||
            !FMath::IsFinite(RequestedSeconds+FrameSeconds) || !FMath::IsFinite(BacklogSeconds+FrameSeconds))return false;
        RequestedSeconds+=FrameSeconds;BacklogSeconds+=FrameSeconds;
        while(Completed<MaximumTicks && BacklogSeconds>=StepSeconds)
        {
            if(!FMath::IsFinite(CommittedSeconds+StepSeconds) || CommittedSeconds+StepSeconds==CommittedSeconds ||
                BacklogSeconds-StepSeconds==BacklogSeconds || CommittedTicks==MAX_uint64)return false;
            if(!RunTick())return false;
            BacklogSeconds-=StepSeconds;CommittedSeconds+=StepSeconds;++CommittedTicks;++Completed;
        }
        return true;
    }
};
