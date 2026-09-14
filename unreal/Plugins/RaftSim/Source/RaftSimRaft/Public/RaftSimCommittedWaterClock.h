#pragma once
#include "CoreMinimal.h"

// Follow successfully committed water duration, not rendered-frame duration.
// Spatial field handoffs do not reset the adapter's committed timeline. A full
// runtime reconfigure/regression is not silently interpreted as elapsed time.
struct FRaftSimCommittedWaterClock
{
    double Origin=0,Last=0;
    bool Initialize(double Seconds)
    {
        if(!FMath::IsFinite(Seconds) || Seconds<0)return false;
        Origin=Last=Seconds;return true;
    }
    bool Observe(double Seconds,double& Delta)
    {
        Delta=0;
        if(!FMath::IsFinite(Seconds) || Seconds<Last)return false;
        Delta=Seconds-Last;Last=Seconds;return true;
    }
    double TargetSeconds() const{return Last-Origin;}
};
