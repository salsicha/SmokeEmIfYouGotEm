#include "RaftSimTrialStallRecovery.h"
#include "Misc/AutomationTest.h"
#include "Serialization/JsonSerializer.h"
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTrialStallRecoveryTest,
    "RaftSim.Review.TrialStallRecovery",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimTrialStallRecoveryTest::RunTest(const FString&)
{
    FRaftSimTrialStallRecovery Policy;
    const auto Read=[&](const FString& Json){TSharedPtr<FJsonObject> Row;
        return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Row)&&Policy.Read(*Row);};
    TestTrue(TEXT("default remains unchanged"),Read(TEXT("{}")));
    TestFalse(TEXT("no unrequested rest"),Policy.TryStart(1500,30,200,true));
    TestTrue(TEXT("explicit finite policy"),Read(TEXT("{\"stall_recovery\":{\"after_station_m\":1380,\"stall_seconds\":15,\"rest_seconds\":12,\"lookahead_m\":45}}")));
    TestFalse(TEXT("never alters the earlier mistake"),Policy.TryStart(1300,30,200,true));
    TestFalse(TEXT("does not interrupt actual progress"),Policy.TryStart(1466,10,200,true));
    TestFalse(TEXT("swimmers/capsize forbid this rest policy"),Policy.TryStart(1466,20,200,false));
    TestTrue(TEXT("one ordinary rest request after the recorded stall"),Policy.TryStart(1466,20,200,true));
    TestTrue(TEXT("rest begins immediately"),Policy.IsResting(200));
    TestTrue(TEXT("bounded rest"),Policy.IsResting(211.999));
    TestTrue(TEXT("then normal exit steering"),Policy.IsExiting(212));
    TestFalse(TEXT("never endlessly restarts"),Policy.TryStart(1466,60,230,true));
    TestTrue(TEXT("fresh trial resets policy"),Read(TEXT("{}")));
    TestEqual(TEXT("no inherited start time"),Policy.StartedAt,-1.);
    for(const FString Json:{TEXT("{\"stall_recovery\":4}"),TEXT("{\"stall_recovery\":{}}"),
        TEXT("{\"stall_recovery\":{\"after_station_m\":1380,\"stall_seconds\":15,\"rest_seconds\":-1,\"lookahead_m\":45}}"),
        TEXT("{\"stall_recovery\":{\"after_station_m\":1380,\"stall_seconds\":15,\"rest_seconds\":12,\"lookahead_m\":1000}}")})
        TestFalse(TEXT("malformed/unbounded policy rejected"),Read(Json));
    return !HasAnyErrors();
}
#endif
