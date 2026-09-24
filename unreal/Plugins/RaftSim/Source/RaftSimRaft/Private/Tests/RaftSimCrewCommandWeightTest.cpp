#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewSeatLayout.h"
#include "HAL/IConsoleManager.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewCommandWeightTest,
    "RaftSim.Crew.CommandsShareVisibleAndPhysicalSeats",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewCommandWeightTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            if (It->GetOwner() == Raft) Owned.Add(*It);
        for (AActor* Actor : Owned) World->DestroyActor(Actor);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Raft->RaftAdapter = Adapter;
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Adapter->ConfigureRaftBody(Body);
    FRaftSimFlexParameters Flex;
    Flex.PassengerCount = Raft->PaddlerCount;
    Flex.GuideMassKg = 85.0;
    Flex.PassengerMassKg = 75.0;
    const bool bLeftGuide = IConsoleManager::Get().FindConsoleVariable(
        TEXT("raftsim.GuideLeftHanded"))->GetInt() != 0;
    const auto Seats = RaftSimCrewSeatLayout::BuildNormalSeats(Flex, bLeftGuide);
    const auto ReferenceSeats = RaftSimFlex::BuildDefaultCrewSeats(Flex);
    TestTrue(TEXT("reference guide remains centred for independent D6 fixtures"),
        ReferenceSeats[0].LocalPosition.Y == 0.);
    for (int32 Index = 0; Index < Seats.Num(); ++Index)
    {
        const FName Id = Index == 0 ? FName(TEXT("guide"))
            : FName(*FString::Printf(TEXT("paddler_%d"), Index));
        const auto* Avatar = Raft->FindAvatar(Id);
        if (!TestNotNull(TEXT("normal anchor has rendered avatar"), Avatar)) continue;
        const FVector RenderM = Raft->GetActorTransform().InverseTransformPosition(
            Avatar->GetActorLocation()) * .01;
        TestTrue(TEXT("physical anchor X matches actual attached avatar"),
            FMath::IsNearlyEqual(Seats[Index].LocalPosition.X, RenderM.X, 1.e-6));
        TestTrue(TEXT("physical anchor Y matches actual attached avatar"),
            FMath::IsNearlyEqual(Seats[Index].LocalPosition.Y, RenderM.Y, 1.e-6));
        TestEqual(TEXT("vertical load remains explicitly inferred"),
            Seats[Index].LocalPosition.Z, ReferenceSeats[Index].LocalPosition.Z);
    }
    const auto Left = RaftSimCrewSeatLayout::BuildNormalSeats(Flex, true);
    const auto Right = RaftSimCrewSeatLayout::BuildNormalSeats(Flex, false);
    TestTrue(TEXT("handed guide load mirrors across the raft"),
        Left[0].LocalPosition.Equals(FVector(-1.55, -.62, .15), 1.e-6) &&
        Right[0].LocalPosition.Equals(FVector(-1.55, .62, .15), 1.e-6));
    const auto LeftWeight = RaftSimFlex::EvaluateCrewWeightDistribution(Flex.TotalMassKg(),
        FVector(0, 0, -9.81), Left, {}, Flex.LengthM, Flex.WidthM);
    const auto RightWeight = RaftSimFlex::EvaluateCrewWeightDistribution(Flex.TotalMassKg(),
        FVector(0, 0, -9.81), Right, {}, Flex.LengthM, Flex.WidthM);
    TestTrue(TEXT("mirrored guide changes actual weight moment, not just a label"),
        FMath::IsNearlyEqual(LeftWeight.RollMomentNm, -RightWeight.RollMomentNm, 1.e-6) &&
        FMath::Abs(LeftWeight.RollMomentNm) > 100.);
    Adapter->ConfigureFlexibleRaftModel(Flex, Seats);
    const int32 CrewCount = Raft->CrewAvatars.Num();
    TestEqual(TEXT("fixture has four paddlers and guide"), CrewCount, 5);
    const auto Weight = [&]() {
        return RaftSimFlex::EvaluateCrewWeightDistribution(Flex.TotalMassKg(),
            FVector(0, 0, -9.81), Seats, Adapter->FlexActions, Flex.LengthM, Flex.WidthM);
    };
    const auto CheckAll = [&](ERaftSimCrewAvatarAction Expected, int32 Direction) {
        TestEqual(TEXT("one physical action per attached crew member"), Adapter->FlexActions.Num(), CrewCount);
        TSet<FString> Ids;
        for (int32 Index = 0; Index < CrewCount; ++Index)
        {
            TestEqual(TEXT("normal command sets visible action"), Raft->CrewAvatars[Index]->GetAvatarAction(), Expected);
            const FString Id = Index == CrewCount - 1 ? TEXT("guide")
                : FString::Printf(TEXT("passenger_%d"), Index);
            const auto* Action = Adapter->FlexActions.FindByPredicate(
                [&](const auto& Candidate) { return Candidate.SeatId == Id; });
            if (!TestNotNull(TEXT("exact physical seat id"), Action)) continue;
            Ids.Add(Action->SeatId);
            TestEqual(TEXT("visible/physical side agrees"), Action->HighSideDirection, Direction);
            TestEqual(TEXT("brace belongs only to high-side mapping"), Action->bBrace, Direction != 0);
            if (Direction == 0)
                TestTrue(TEXT("get-down retains existing physical drop"),
                    Action->LeanOffset.Equals(FVector(0, 0, -.15), 1.e-7));
        }
        TestEqual(TEXT("no duplicate seat actions"), Ids.Num(), CrewCount);
        const auto Telemetry = Weight();
        TestEqual(TEXT("all occupied masses receive actions"), Telemetry.ActiveActionCount, CrewCount);
        TestEqual(TEXT("physical high-side participation"), Telemetry.HighSideCount, Direction ? CrewCount : 0);
        TestTrue(TEXT("crew mass is unchanged"), FMath::IsNearlyEqual(Telemetry.TotalCrewMassKg, 385.0));
        TestTrue(TEXT("adapter consumes command on a real physics step"), Adapter->StepRaftDynamics(1.f / 120.f));
        TestTrue(TEXT("flex model evaluated"), Adapter->GetLastFlexibleStepTelemetry().bEvaluated);
        TestFalse(TEXT("finite applied moment"), Adapter->GetLastFlexibleStepTelemetry().AppliedTorqueNm.ContainsNaN());
    };

    Raft->SetActorRotation(FRotator(0, 0, 10));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::HighSide);
    Raft->UpdateCrew(.001f);
    TestEqual(TEXT("reaction delay does not shift physical masses early"), Adapter->FlexActions.Num(), 0);
    Raft->UpdateCrew(Raft->CrewReactionSeconds + .01f);
    CheckAll(ERaftSimCrewAvatarAction::HighSidePort, -1);
    const double PortMoment = Weight().RollMomentNm;
    Raft->SetActorRotation(FRotator(0, 0, -10));
    Raft->UpdateCrew(.01f);
    CheckAll(ERaftSimCrewAvatarAction::HighSidePort, -1);
    Raft->IssueCrewCommand(ERaftSimCrewCommand::HighSide);
    Raft->UpdateCrew(.01f);
    CheckAll(ERaftSimCrewAvatarAction::HighSideStarboard, 1);
    TestTrue(TEXT("full-crew physical moment reverses"), PortMoment < 0 && Weight().RollMomentNm > 0);

    // The guide's personal stroke overrides both representations until expiry.
    Raft->GuideStrokeAction = ERaftSimCrewAvatarAction::ForwardStroke;
    Raft->GuideStrokeActionSeconds = .5f;
    Raft->UpdateCrew(.1f);
    TestEqual(TEXT("guide stroke is visible"), Raft->CrewAvatars.Last()->GetAvatarAction(),
        ERaftSimCrewAvatarAction::ForwardStroke);
    TestEqual(TEXT("only paddlers shift during guide stroke"), Adapter->FlexActions.Num(), CrewCount - 1);
    TestFalse(TEXT("no invisible guide weight shift"), Adapter->FlexActions.ContainsByPredicate(
        [](const auto& Action) { return Action.SeatId == TEXT("guide"); }));
    Raft->UpdateCrew(.5f);
    CheckAll(ERaftSimCrewAvatarAction::HighSideStarboard, 1);

    auto* Detached = Raft->CrewAvatars[0].Get();
    Detached->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    Detached->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
    Raft->UpdateCrew(.01f);
    TestEqual(TEXT("detached avatar retains swimming"), Detached->GetAvatarAction(), ERaftSimCrewAvatarAction::Swimming);
    TestFalse(TEXT("detached paddler gets no weight-shift action"), Adapter->FlexActions.ContainsByPredicate(
        [](const auto& Action) { return Action.SeatId == TEXT("passenger_0"); }));
    Detached->AttachToActor(Raft, FAttachmentTransformRules::KeepWorldTransform);

    Raft->IssueCrewCommand(ERaftSimCrewCommand::GetDown);
    Raft->UpdateCrew(Raft->CrewReactionSeconds + .01f);
    CheckAll(ERaftSimCrewAvatarAction::Brace, 0);
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    Raft->UpdateCrew(Raft->CrewReactionSeconds + .01f);
    TestEqual(TEXT("rest clears old actions"), Adapter->FlexActions.Num(), 0);
    TestEqual(TEXT("rest removes all active weight shifts"), Weight().ActiveActionCount, 0);
    for (auto* Avatar : TArray<ARaftSimCrewAvatarActor*>{Detached, Raft->CrewAvatars.Last().Get()})
        TestEqual(TEXT("rest is visible"), Avatar->GetAvatarAction(), ERaftSimCrewAvatarAction::SeatedIdle);

    const int32 ResponseCount = Raft->GetHighSideResponseCount();
    Raft->HandleHighSideResponse(-7);
    CheckAll(ERaftSimCrewAvatarAction::HighSidePort, -1);
    Raft->UpdateCrew(.01f);
    CheckAll(ERaftSimCrewAvatarAction::HighSidePort, -1);
    TestEqual(TEXT("dedicated key persists and records once"), Raft->GetHighSideResponseCount(), ResponseCount + 1);
    Raft->HandleHighSideResponse(0);
    TestEqual(TEXT("zero direction ignored"), Raft->GetHighSideResponseCount(), ResponseCount + 1);
    Raft->HandleHighSideResponse(9);
    CheckAll(ERaftSimCrewAvatarAction::HighSideStarboard, 1);
    Raft->RaftMode = ERaftSimRaftMode::Capsized;
    Raft->HandleHighSideResponse(-1);
    TestEqual(TEXT("capsized input is not a seated crew response"), Raft->GetHighSideResponseCount(), ResponseCount + 2);
    return true;
}
#endif
