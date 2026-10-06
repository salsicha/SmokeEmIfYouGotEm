#include "Misc/AutomationTest.h"
#include "RaftSimPhysicalEddyExposure.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPhysicalEddyExposureTest,"RaftSim.P2.PhysicalEddyExposure",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimPhysicalEddyExposureTest::RunTest(const FString&)
{
    for (double Datum:{0.,220.,800.})
    {
        // Reproduce the adapter's absolute-to-world height conversion. Datum
        // changes alone must not change ownership of the same world rock.
        const double Surface=(Datum+7.5)-Datum;
        TestTrue(TEXT("exposed captured ground remains an owner"),
            RaftSimPhysicalEddyExposure::IsExposed(800.,Surface));
        TestFalse(TEXT("submerged physical bed is not an exposed rock"),
            RaftSimPhysicalEddyExposure::IsExposed(700.,Surface));
        TestTrue(TEXT("actual equality follows existing exposure boundary"),
            RaftSimPhysicalEddyExposure::IsExposed(750.,Surface));
    }
    TestTrue(TEXT("negative world elevations retain their frame"),
        RaftSimPhysicalEddyExposure::IsExposed(-100.,-2.));
    TestFalse(TEXT("nonfinite ground is unknown, never an owner"),
        RaftSimPhysicalEddyExposure::IsExposed(std::numeric_limits<double>::infinity(),7.5));
    TestFalse(TEXT("nonfinite water is unknown, never an owner"),
        RaftSimPhysicalEddyExposure::IsExposed(800.,std::numeric_limits<double>::quiet_NaN()));
    return true;
}
#endif
