// Regenerates the South Fork support band fields (baked water elevation +
// band energy per flow band) beside the cooked flow fields. Run after any
// water-band rebake so rigid raft support keeps mirroring exactly what the
// authored band water renders.

#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimExportSouthForkSupportBandFieldsTest,
    "RaftSim.Tools.ExportSouthForkSupportBandFields",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimExportSouthForkSupportBandFieldsTest::RunTest(const FString&)
{
    FString Summary;
    const bool bExported =
        RaftSimEditorEnvironment::ExportSouthForkSupportBandFields(Summary);
    AddInfo(Summary);
    TestTrue(TEXT("all three flow bands exported"), bExported);
    return bExported;
}

#endif // WITH_AUTOMATION_TESTS
