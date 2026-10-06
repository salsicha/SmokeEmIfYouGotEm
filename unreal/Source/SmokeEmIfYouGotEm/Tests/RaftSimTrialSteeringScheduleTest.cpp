#include "RaftSimTrialSteeringSchedule.h"
#include "Misc/AutomationTest.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTrialSteeringScheduleTest,
    "RaftSim.Review.TrialSteeringSchedule",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimTrialSteeringScheduleTest::RunTest(const FString&)
{
    FRaftSimTrialSteeringSchedule Schedule;
    const auto Read=[&](const FString& Json)
    {
        TSharedPtr<FJsonObject> Row;
        return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Row)&&Schedule.Read(*Row);
    };
    TestTrue(TEXT("parse linked timing"),Read(TEXT("{\"steering_start_m\":1950,\"steering_end_m\":2085,\"steering_blackouts\":[[2010,2038]]}")));
    TestTrue(TEXT("before steering begins"),Schedule.Suppressed(1949));
    TestFalse(TEXT("first obstacle preparation enabled"),Schedule.Suppressed(2009.99));
    TestTrue(TEXT("second preparation omitted at inclusive start"),Schedule.Suppressed(2010));
    TestTrue(TEXT("no holding-lane correction during blackout"),Schedule.Suppressed(2037.99));
    TestFalse(TEXT("late recovery enabled at exclusive end"),Schedule.Suppressed(2038));
    TestTrue(TEXT("first-only cutoff is inclusive"),Schedule.Suppressed(2085));
    TestTrue(TEXT("fresh trial resets previous timing"),Read(TEXT("{}")));
    TestFalse(TEXT("no inherited blackout"),Schedule.Suppressed(2020));
    TestTrue(TEXT("named decision timing parses"),Read(TEXT("{\"mistake_trigger_m\":2010}")));
    TestEqual(TEXT("second-rock decision, not generic checkpoint"),Schedule.MistakeTrigger.GetValue(),2010.);
    TestFalse(TEXT("non-numeric decision timing rejected"),Read(TEXT("{\"mistake_trigger_m\":\"bad\"}")));
    TestTrue(TEXT("fresh trial resets named decision timing"),Read(TEXT("{}")));
    TestFalse(TEXT("decision timing not inherited"),Schedule.MistakeTrigger.IsSet());
    TestTrue(TEXT("absent steering parses"),Read(TEXT("{\"disable_steering\":true}")));
    TestTrue(TEXT("absent means no correction"),Schedule.Suppressed(2020));
    for(const FString Json:{TEXT("{\"steering_blackouts\":4}"),TEXT("{\"steering_blackouts\":[[20,10]]}"),
        TEXT("{\"steering_blackouts\":[[10,10]]}"),TEXT("{\"steering_blackouts\":[[10]]}"),
        TEXT("{\"steering_blackouts\":[[\"bad\",20]]}"),TEXT("{\"steering_start_m\":20,\"steering_end_m\":10}")})
        TestFalse(TEXT("malformed timing rejected, never silently ignored"),Read(Json));
    return !HasAnyErrors();
}
#endif
