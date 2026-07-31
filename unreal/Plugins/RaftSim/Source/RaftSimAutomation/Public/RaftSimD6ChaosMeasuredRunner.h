// Genuine Unreal Chaos D6 baseline measurement runner.
//
// This development-only runner creates transient UWorld physics scenes,
// advances real simulated rigid bodies, and exports the seven committed D6
// fixture results. It intentionally cannot promote D6: the independent
// compliant-model target and manual review remain separate fail-closed gates.

#pragma once

#include "CoreMinimal.h"

struct RAFTSIMAUTOMATION_API FRaftSimD6ChaosMeasuredRunResult
{
    bool bSuccess = false;
    FString ErrorMessage;
    FString SummaryPath;
    FString SidecarPath;
    int32 FixtureCount = 0;
    int32 FilledFixtureCount = 0;
    int32 InvalidFixtureCount = 0;
};

namespace RaftSimD6Chaos
{

// RepoRootDir is the repository root containing physics/ and unreal/.
// Outputs are written to the paths declared by the committed D6 Chaos
// fixture contract under physics/reports/d6/chaos/.
RAFTSIMAUTOMATION_API FRaftSimD6ChaosMeasuredRunResult RunMeasuredExport(
    const FString& RepoRootDir);

} // namespace RaftSimD6Chaos
