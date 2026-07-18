// D6 measured-results export: runs the seven committed D6 fixtures
// (physics/data/calibration/flexible_raft_d6_fixture_input_package.json)
// through the C++ D1-D4 flexible-raft port and writes measured-results
// sidecars for both D6 targets:
//   - project_chrono_or_reviewed_compliant_model  (compliant C++ port)
//   - unreal_chaos_rigid_baseline                 (rigid baseline pass)
// plus per-fixture telemetry files hashed with SHA-256 for provenance.

#pragma once

#include "CoreMinimal.h"

struct RAFTSIMPHYSICS_API FRaftSimD6MeasuredExportResult
{
    bool bSuccess = false;
    FString ErrorMessage;
    FString CompliantSidecarPath;
    FString ChaosBaselineSidecarPath;
    FString SummaryPath;
    int32 FixtureCount = 0;
    int32 CompliantFilledCount = 0;
    int32 BaselineFilledCount = 0;
};

namespace RaftSimFlexD6
{

// RepoRootDir is the repository root (the directory containing physics/ and
// unreal/). Outputs are written under physics/reports/d6/ue/.
RAFTSIMPHYSICS_API FRaftSimD6MeasuredExportResult RunMeasuredExport(const FString& RepoRootDir);

} // namespace RaftSimFlexD6
