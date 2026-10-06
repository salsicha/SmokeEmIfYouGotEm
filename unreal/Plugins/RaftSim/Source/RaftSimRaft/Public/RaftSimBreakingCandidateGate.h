#pragma once
#include "CoreMinimal.h"

namespace RaftSimBreakingCandidateGate
{
// Match the original rejection expression, including unordered (NaN) Froude.
// Baseline-only wet cells must not create solver-owned support sites.
inline bool RejectCurrent(uint8 LiveWet, float Froude)
{
    return LiveWet == 0 || Froude > .94f;
}
}
