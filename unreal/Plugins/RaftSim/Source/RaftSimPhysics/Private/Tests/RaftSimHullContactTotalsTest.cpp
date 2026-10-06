#include "RaftSimHullContact.h"
#include "Misc/AutomationTest.h"
#include "Components/StaticMeshComponent.h"
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullContactTotalsTest,"RaftSim.Physics.CommittedHullContactTotals",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimHullContactTotalsTest::RunTest(const FString&)
{
    FRaftSimHullContactTotals T;FRaftSimHullContactResult R;R.Impulses=4;
    T.AddCommitted(R,.01);
    TestEqual(TEXT("rejected steps never contribute"),T.Steps,uint64(0));
    R.bCompleted=true;R.DissipatedJ=2;
    T.AddCommitted(R,.01);T.AddCommitted(R,.01);
    R.Impulses=0;T.AddCommitted(R,.01);
    TestEqual(TEXT("all successful steps"),T.Steps,uint64(3));
    TestEqual(TEXT("contacts survive subsequent empty frame"),T.Impulses,uint64(8));
    TestEqual(TEXT("contact-step duration not total time"),T.ContactStepSeconds,.02);
    TestEqual(TEXT("only contact-step energy"),T.DissipatedJ,4.);
    T.AddCommitted(R,-.01);TestEqual(TEXT("invalid interval ignored"),T.Steps,uint64(3));
    auto* A=NewObject<UStaticMeshComponent>();auto* B=NewObject<UStaticMeshComponent>();
    FRaftSimHullContactResult Owned;
    Owned.Impulses=3;Owned.RecordOwnerImpulse(A);Owned.RecordOwnerImpulse(A);Owned.RecordOwnerImpulse(B);
    T.AddCommitted(Owned,.01);
    TestEqual(TEXT("refused owner impulses never commit"),T.OwnerImpulses.Num(),0);
    Owned.bCompleted=true;T.AddCommitted(Owned,.01);
    TestEqual(TEXT("actual first owner, not all nearby rocks"),T.OwnerImpulses.FindRef(A),uint64(2));
    TestEqual(TEXT("different owner remains separate"),T.OwnerImpulses.FindRef(B),uint64(1));
    Owned.OwnerImpulses.Reset();Owned.Impulses=1;T.AddCommitted(Owned,.01);
    TestEqual(TEXT("unattributed ground contact is not assigned to a rock"),T.OwnerImpulses.FindRef(A),uint64(2));
    return true;
}
#endif
