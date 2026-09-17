#pragma once
#include "CoreMinimal.h"

// One exact box per selection batch, alive only for ONE immutable profile
// build. No quantization, approximate lookup or cross-profile value reuse.
struct FRaftSimCrestRangeMemo
{
    FBox2D LastBox{ForceInit};
    float LastWidth=0.f;
    bool bHasValue=false;

    float Width(const FBox2D& Box,TFunctionRef<float(const FBox2D&)> Evaluate)
    {
        if(bHasValue && LastBox==Box)return LastWidth;
        LastWidth=Evaluate(Box);LastBox=Box;bHasValue=true;
        return LastWidth;
    }
};
