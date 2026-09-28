#include "Misc/AutomationTest.h"
#include "RaftSimSprayEmitterAnchor.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSprayEmitterAnchorTest,
    "RaftSim.M4.SprayEmitterAnchor",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSprayEmitterAnchorTest::RunTest(const FString&)
{
    const FVector Centre(1250.,-840.,190.);
    for(const FVector Flow:{FVector(1,0,0),FVector(0,-1,0),FVector(.6,.8,0),FVector(-.6,.8,0)})
    {
        const FVector Across(-Flow.Y,Flow.X,0);
        const auto Height=[&](const FVector& P)
        {
            const FVector Delta=P-Centre;
            const double Along=FVector::DotProduct(Delta,Flow);
            return Centre.Z+.24*Along+.03*FVector::DotProduct(Delta,Across)+.001*Along*Along;
        };
        const FVector Proposed[3]={Centre+Flow*35.+FVector(0,0,6),
            Centre-Flow*12.+FVector(0,0,3),Centre-Flow*12.+Across*10.2+FVector(0,0,3)};
        const double Clearances[3]={6.,3.,3.};
        for(int32 I=0;I<3;++I)
        {
            FVector Actual=Proposed[I];int32 Calls=0;
            const auto Sample=[&](const FVector& P,FVector& Out)
            {
                ++Calls;
                TestTrue(TEXT("queries the actual shifted source position"),P==Proposed[I]);
                // Returned XY is not used to slide the source across the river.
                Out=FVector(P.X+1.,P.Y-1.,Height(P));return true;
            };
            TestTrue(TEXT("wet shifted source attached"),RaftSimSprayEmitterAnchor::Attach(Actual,Clearances[I],Sample));
            TestEqual(TEXT("one carrier query per emitter"),Calls,1);
            TestEqual(TEXT("world X retained"),Actual.X,Proposed[I].X);
            TestEqual(TEXT("world Y retained"),Actual.Y,Proposed[I].Y);
            TestTrue(TEXT("clearance uses height at emitter, not site centre"),
                FMath::IsNearlyEqual(Actual.Z,Height(Proposed[I])+Clearances[I],1.e-10));
            TestTrue(TEXT("fixture detects old centre-height error"),FMath::Abs(Actual.Z-Proposed[I].Z)>1.);
        }
    }
    const double NaN=std::numeric_limits<double>::quiet_NaN();
    const auto Wet=[](const FVector& P,FVector& Out){Out=FVector(P.X,P.Y,42.);return true;};
    for(double Clearance:{-1.,NaN,std::numeric_limits<double>::infinity()})
    {
        FVector P=Centre;
        TestFalse(TEXT("invalid clearance rejected"),RaftSimSprayEmitterAnchor::Attach(P,Clearance,Wet));
        TestTrue(TEXT("invalid clearance leaves origin unchanged"),P==Centre);
    }
    for(bool bUnavailable:{false,true})
    {
        FVector P=Centre;
        const auto Invalid=[&](const FVector&,FVector& Out){Out=FVector(0,0,NaN);return !bUnavailable;};
        TestFalse(TEXT("dry, unavailable or nonfinite carrier rejects"),RaftSimSprayEmitterAnchor::Attach(P,3.,Invalid));
        TestTrue(TEXT("failed query cannot alter origin"),P==Centre);
    }
    FVector Bad(NaN,0,0);
    TestFalse(TEXT("nonfinite source rejects"),RaftSimSprayEmitterAnchor::Attach(Bad,3.,Wet));
    FVector ZeroClearance=Centre;
    TestTrue(TEXT("zero clearance is valid"),RaftSimSprayEmitterAnchor::Attach(ZeroClearance,0.,Wet));
    TestEqual(TEXT("zero clearance lands on the sampled carrier"),ZeroClearance.Z,42.);
    AddInfo(TEXT("Source-centre placement fixture only; not particle collision or visual acceptance."));
    return !HasAnyErrors();
}
#endif
