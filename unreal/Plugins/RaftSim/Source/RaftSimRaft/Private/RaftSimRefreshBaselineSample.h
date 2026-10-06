#pragma once

#include "RaftSimWaterRuntimeAdapter.h"

// One immutable Cartesian baseline query at ONE vertex during ONE refresh.
// Stack-owned by the combined sampling task; never retained across coordinates,
// source replacement, recentering, simulation steps or refreshes. Invalid and
// dry results are authoritative too. Each caller receives its own value copy.
class FRaftSimRefreshBaselineSample
{
public:
    template<class FQuery>
    bool Read(FQuery&& Query, FRaftSimWaterSample& Out)
    {
        if (!bQueried)
        {
            bValid=Query(Value);
            bQueried=true;
        }
        Out=Value;
        return bValid;
    }
private:
    FRaftSimWaterSample Value;
    bool bQueried=false;
    bool bValid=false;
};
