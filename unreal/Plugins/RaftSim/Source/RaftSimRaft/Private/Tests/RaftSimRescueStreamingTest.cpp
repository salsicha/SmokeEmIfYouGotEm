#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRescueStreamingComponent.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRescueStreamingTest,
    "RaftSim.Continuous.RescueStreamingSources",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRescueStreamingTest::RunTest(const FString&)
{
    UWorld* World = nullptr;
    for (const auto& C : GEngine->GetWorldContexts())
        if (C.WorldType == EWorldType::Editor) { World = C.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft actor"), Raft)) return false;
    ON_SCOPE_EXIT { World->DestroyActor(Raft); };
    auto* Provider = NewObject<URaftSimRescueStreamingComponent>(Raft);
    Raft->SetActorLocation(FVector(30000000., -12000000., 62000.));
    FRaftSimSwimmerRescueFrame Swimmer;
    Swimmer.PassengerId = TEXT("guide");
    Swimmer.SwimmerWorldPositionMeters = FVector(300024., -120016., 619.);
    Raft->Swimmers.Add(Swimmer);
    Swimmer.PassengerId = TEXT("paddler_1");
    Swimmer.SwimmerWorldPositionMeters.X += 1500.; // Well beyond raft/camera radius.
    Raft->Swimmers.Add(Swimmer);
    TArray<FWorldPartitionStreamingSource> Sources;
    TestTrue(TEXT("live provider yields sources"), Provider->GetStreamingSources(Sources));
    TestEqual(TEXT("raft and each separated swimmer"), Sources.Num(), 3);
    if (Sources.Num() != 3) return false;
    TestTrue(TEXT("large world origin preserved"), Sources[0].Location.Equals(Raft->GetActorLocation(), .001));
    FVector GuideCm; Raft->GetSwimmerWorldPosition(TEXT("guide"), GuideCm);
    TestTrue(TEXT("production metres-to-world-cm conversion"), Sources[1].Location.Equals(GuideCm, .001));
    TestTrue(TEXT("distant swimmer independent of raft"),
        FVector::Dist2D(Sources[2].Location, Sources[0].Location) > Sources[0].Shapes[0].Radius);
    const FName RemainingName = Sources[2].Name;
    for (const auto& Source : Sources)
    {
        TestTrue(TEXT("activated collision terrain requested"), Source.TargetState == EStreamingSourceTargetState::Activated);
        TestTrue(TEXT("slow-load protection"), Source.bBlockOnSlowLoading);
        TestTrue(TEXT("terrain source is two-dimensional"), Source.bForce2D);
        TestFalse(TEXT("explicit bounded radius"), Source.Shapes[0].bUseGridLoadingRange);
    }
    TestEqual(TEXT("query leaves rescue state intact"), Raft->GetSwimmerCount(), 2);
    Raft->Swimmers.RemoveAt(0); Sources.Reset();
    Provider->GetStreamingSources(Sources);
    TestEqual(TEXT("rescued swimmer stops loading independent cells"), Sources.Num(), 2);
    TestEqual(TEXT("remaining swimmer source identity is stable"), Sources[1].Name, RemainingName);
    Raft->Swimmers.Reset(); Sources.Reset(); Provider->GetStreamingSources(Sources);
    TestEqual(TEXT("raft source persists after recovery"), Sources.Num(), 1);
    return true;
}
#endif
