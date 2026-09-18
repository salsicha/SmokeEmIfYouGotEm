#include "RaftSimWaterModule.h"

#include "Modules/ModuleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/AutomationTest.h"
#if RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"
#endif

namespace
{
bool ParseSolverLanes(const FString& Text, unsigned& Lanes)
{
    // FParse's integer overload accepts suffixes; reject malformed overrides.
    if (Text.IsEmpty() || Text.Len()>2) return false;
    unsigned Value=0;
    for (TCHAR C:Text)
    {
        if (C<TEXT('0') || C>TEXT('9')) return false;
        Value=10*Value+unsigned(C-TEXT('0'));
    }
    if (Value<1 || Value>64) return false;
    Lanes=Value;
    return true;
}
}

void FRaftSimWaterModule::StartupModule()
{
#if RAFTSIM_HAS_LIVE_SOLVER
    UE_LOG(LogTemp, Display, TEXT("RaftSim live-water solver archive: %hs"), RAFTSIM_LIVE_SOLVER_BUILD_SHA256);
#if !UE_BUILD_SHIPPING
    FString Requested;
    if (FParse::Value(FCommandLine::Get(),TEXT("RaftSimSolverLanes="),Requested))
    {
        unsigned Lanes=0;
        if (!ParseSolverLanes(Requested,Lanes))
        {
            UE_LOG(LogTemp,Fatal,TEXT("RaftSimSolverLanes requires an integer from 1 to 64"));
            return;
        }
        // Configure before any solver construction; never resize a live pool.
        raftsim::configure_solver_workers(Lanes);
        UE_LOG(LogTemp,Display,TEXT("RaftSim live-water solver lane limit: %u (diagnostic override)"),Lanes);
    }
    else
#endif
    {
        UE_LOG(LogTemp,Display,TEXT("RaftSim live-water solver lane limit: 4 (default)"));
    }
#endif
}

void FRaftSimWaterModule::ShutdownModule()
{
#if RAFTSIM_HAS_LIVE_SOLVER
    // Join outside DllMain: waiting for thread detach under the Windows loader
    // lock can deadlock module unloading even after the last water step.
    raftsim::shutdown_solver_workers();
    UE_LOG(LogTemp, Display, TEXT("RaftSim live-water solver workers joined before module unload"));
#endif
}

IMPLEMENT_MODULE(FRaftSimWaterModule, RaftSimWater)

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSolverLaneOptionTest,"RaftSim.Water.SolverLaneOption",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSolverLaneOptionTest::RunTest(const FString&)
{
    for (unsigned Expected=1;Expected<=64;++Expected)
    {
        unsigned Actual=0;
        TestTrue(TEXT("valid bounded lane count"),ParseSolverLanes(FString::FromInt(Expected),Actual));
        TestEqual(TEXT("exact count"),Actual,Expected);
    }
    for (const TCHAR* Text:{TEXT(""),TEXT("0"),TEXT("65"),TEXT("-1"),TEXT("+8"),
                          TEXT("8.0"),TEXT("8x"),TEXT(" 8"),TEXT("8 "),TEXT("999999999999")})
    {
        unsigned Actual=37;
        TestFalse(TEXT("invalid count rejected"),ParseSolverLanes(Text,Actual));
        TestEqual(TEXT("rejection does not publish a count"),Actual,37u);
    }
    return !HasAnyErrors();
}
#endif
