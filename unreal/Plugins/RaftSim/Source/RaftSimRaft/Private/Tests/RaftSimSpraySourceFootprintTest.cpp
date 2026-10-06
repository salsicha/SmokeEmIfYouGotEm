#include "Misc/AutomationTest.h"
#include "RaftSimSpraySourceFootprint.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSpraySourceFootprintTest,
    "RaftSim.M4.SpraySourceFootprint",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSpraySourceFootprintTest::RunTest(const FString&)
{
    const FVector2D Centre(-5430.,3600.);
    for (const FVector2D Flow:{FVector2D(1,0),FVector2D(0,-1),FVector2D(.6,.8),FVector2D(-.6,.8)})
    {
        const FVector2D Across(-Flow.Y,Flow.X);
        TArray<FVector2D> Queries;
        FVector Actual;
        const auto Wet=[&](const FVector2D& P,FVector& Out)
        {Queries.Add(P);Out=FVector(P.X*100,-P.Y*100,150.+P.X*.01);return true;};
        TestTrue(TEXT("wet current-oriented source accepted"),RaftSimSpraySourceFootprint::Sample(Centre,Flow,Wet,Actual));
        TestEqual(TEXT("centre, original boundaries and offset-aware outer probes"),Queries.Num(),15);
        TestTrue(TEXT("actual centre height and reflected world placement retained"),Actual==FVector(Centre.X*100,-Centre.Y*100,150.+Centre.X*.01));
        for (double D:{-1.05,-.8,0.,.8,1.05}) for (double A:{-1.5,0.,1.5})
            TestTrue(TEXT("flow-oriented footprint includes each corner and edge midpoint"),
                Queries.ContainsByPredicate([&](const FVector2D& P){return P.Equals(Centre+Flow*D+Across*A,1.e-9);}));
        for (int32 Failed=0;Failed<15;++Failed)
        {
            int32 Call=0;
            const auto Dry=[&](const FVector2D& P,FVector& Out)
            {Out=FVector(P,999);return Call++!=Failed;};
            Actual=FVector(1,2,3);
            TestFalse(TEXT("any dry/missing centre, edge or corner rejects"),RaftSimSpraySourceFootprint::Sample(Centre,Flow,Dry,Actual));
            TestTrue(TEXT("failed source cannot publish a stale anchor"),Actual==FVector::ZeroVector);
        }
    }
    FVector Out;
    const auto Unused=[](const FVector2D&,FVector& P){P=FVector::ZeroVector;return true;};
    TestFalse(TEXT("no arbitrary flow orientation for stationary source"),RaftSimSpraySourceFootprint::Sample(Centre,FVector2D::ZeroVector,Unused,Out));
    return !HasAnyErrors();
}
#endif
