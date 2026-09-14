#include "Misc/AutomationTest.h"
#include "RaftSimCommittedWaterClock.h"
#include "RaftSimFoamEvolution.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFoamEvolutionTest,"RaftSim.Water.FoamCommittedEvolution",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimFoamEvolutionTest::RunTest(const FString&)
{
    FRaftSimCommittedWaterClock Clock;TestTrue(TEXT("attach at current water time"),Clock.Initialize(5.));
    auto Candidate=Clock;double Delta=99;
    TestTrue(TEXT("unchanged source holds"),Candidate.Observe(5.,Delta));
    TestEqual(TEXT("no invented initialization interval"),Delta,0.);
    TestEqual(TEXT("held existing foam neither generated nor attenuated"),
        RaftSimFoamEvolution::Resolve(.7f,1.f,0.f,1.f,.2f,true),.7f);
    TestEqual(TEXT("empty new field cannot generate before time advances"),
        RaftSimFoamEvolution::Resolve(0.f,1.f,0.f,0.f,1.f,true),0.f);
    TestTrue(TEXT("long accepted interval remains available"),Candidate.Observe(5.75,Delta));
    TestEqual(TEXT("no half-second duration clipping"),Delta,.75);
    TestEqual(TEXT("abandoned candidate cannot consume field time"),Clock.Last,5.);
    Clock=Candidate;TestEqual(TEXT("clock publishes with successful field"),Clock.Last,5.75);
    TestFalse(TEXT("regressed source refused"),Candidate.Observe(5.,Delta));
    TestEqual(TEXT("rejection preserves last field time"),Candidate.Last,5.75);
    TestFalse(TEXT("invalid source refused"),Candidate.Observe(std::numeric_limits<double>::quiet_NaN(),Delta));

    for(float Dt : {1.f/60.f,.1f,.75f})for(float Old : {0.f,.2f,.8f})for(float Source : {0.f,.4f,1.f})
    {
        const float Decayed=Old*FMath::Pow(.5f,Dt/4.f),Attack=1.f-FMath::Exp(-Dt/.22f);
        float Reference=FMath::Clamp(Source>Decayed ? FMath::Lerp(Decayed,Source,FMath::Clamp(Attack,0.f,1.f)) : Decayed,0.f,1.f);
        Reference*=1.f-.9f*FMath::Min(.3f,1.f);Reference*=.75f;
        TestEqual(TEXT("positive-time generation/release formula unchanged"),
            RaftSimFoamEvolution::Resolve(Decayed,Source,Attack,.3f,.75f,false),Reference);
    }
    const TArray<float> Field={.1f,.2f,.3f,.4f,.5f,.6f,.7f,.8f,.9f};
    for(int32 Y=0;Y<3;++Y)for(int32 X=0;X<3;++X)
        TestEqual(TEXT("held remap includes exact last row and column"),RaftSimFoamEvolution::RemapHeld(Field,3,3,X,Y),Field[Y*3+X]);
    TestEqual(TEXT("overlap samples known old field"),RaftSimFoamEvolution::RemapHeld(Field,3,3,.5f,.5f),
        FMath::Lerp(FMath::Lerp(Field[0],Field[1],.5f),FMath::Lerp(Field[3],Field[4],.5f),.5f));
    for(const auto P : {FVector2f(-.01f,1),FVector2f(2.01f,1),FVector2f(1,-.01f),FVector2f(1,2.01f)})
        TestEqual(TEXT("new domain cannot inherit extrapolated edge foam"),RaftSimFoamEvolution::RemapHeld(Field,3,3,P.X,P.Y),0.f);
    return true;
}
#endif
