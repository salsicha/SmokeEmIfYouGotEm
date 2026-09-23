#include "Misc/AutomationTest.h"
#include "../RaftSimPythonStartupPolicy.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPythonStartupPolicyTest,
    "RaftSim.Project.PythonStartupPolicy", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimPythonStartupPolicyTest::RunTest(const FString&)
{
    using namespace RaftSimPythonStartupPolicy;
    TestTrue(TEXT("Editor-hosted game excludes editor-only startup"), DisableDefault(true, true, false));
    TestFalse(TEXT("Interactive editor and PIE retain Python"), DisableDefault(true, false, false));
    TestFalse(TEXT("Editor commandlets retain Python"), DisableDefault(true, false, true));
    TestFalse(TEXT("Commandlets take precedence over game mode"), DisableDefault(true, true, true));
    for (bool Game : {false, true})
        for (bool Commandlet : {false, true})
            TestFalse(TEXT("Packaged builds have no Python policy"), DisableDefault(false, Game, Commandlet));
    return !HasAnyErrors();
}
#endif
