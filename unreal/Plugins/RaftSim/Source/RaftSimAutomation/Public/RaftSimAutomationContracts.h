#pragma once

#include "CoreMinimal.h"

namespace RaftSimAutomation
{
    static constexpr const TCHAR* Milestone20SmokeSuiteSchema =
        TEXT("raftsim.unreal.live_water_smoke_suite.v1");
    static constexpr const TCHAR* AcceptedReportSetLockPath =
        TEXT("physics/reports/milestone20/report_set_lock.json");

    static constexpr const TCHAR* Milestone23VerticalSliceGateSchema =
        TEXT("raftsim.unreal.vertical_slice_acceptance_gate.v1");
    static constexpr const TCHAR* Milestone23VerticalSliceGatePath =
        TEXT("unreal/Content/RaftSim/Automation/vertical_slice_acceptance_gate.json");

    static constexpr const TCHAR* Milestone25APolishedToolingGateSchema =
        TEXT("raftsim.unreal.polished_tooling_slice_gate.v1");
    static constexpr const TCHAR* Milestone25APolishedToolingGatePath =
        TEXT("unreal/Content/RaftSim/Automation/polished_tooling_slice_gate.json");
}
