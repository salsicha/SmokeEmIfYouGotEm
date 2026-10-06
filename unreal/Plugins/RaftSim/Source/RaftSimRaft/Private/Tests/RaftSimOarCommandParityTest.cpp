#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "RaftSimRaftActor.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewSeatLayout.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimOarCommandParityTest,
    "RaftSim.Input.OarCommandParity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimOarCommandParityTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("isolated game world"), World)) return false;
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    ON_SCOPE_EXIT { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); World->RemoveFromRoot(); };
    for (const auto Rig : {ERaftSimRaftRig::ColoradoOarRig, ERaftSimRaftRig::ZambeziOarRig})
    {
        auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
        auto* Pawn = World->SpawnActor<ARaftSimGuidePawn>();
        if (!TestNotNull(TEXT("raft"), Raft) || !TestNotNull(TEXT("guide"), Pawn)) return false;
        Raft->SetRaftRigForValidation(Rig);
        Raft->InitializeCrewSeatingForValidation();
        auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
        Raft->RaftAdapter = Adapter;
        FRaftSimRaftBodyConfig Body;
        Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
        Adapter->ConfigureRaftBody(Body);
        FRaftSimFlexParameters Flex;
        Flex.PassengerCount = 0;
        Flex.GuideMassKg = 85.;
        Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimCrewSeatLayout::BuildOarRowerSeats(Flex));
        AddInfo(TEXT("Blade impulse fixture uses the real flexible integrator and one rower; river-water validation is a separate map trial."));
        auto* Oars = Raft->GetOarRig();
        if (!TestNotNull(TEXT("real oar component"), Oars) || !TestTrue(TEXT("real rig is built"), Oars->IsBuilt())) return false;
        TestEqual(TEXT("one rower, no hidden paddlers"), Raft->CrewAvatars.Num(), 1);
        struct FCase { const TCHAR* Action; ERaftSimCrewCommand Command; FVector2D Intents; };
        const FCase Cases[] = {
            {TEXT("IA_GuideCommandForwardPaddle"), ERaftSimCrewCommand::AllForward, {1,1}},
            {TEXT("IA_GuideCommandBackPaddle"), ERaftSimCrewCommand::AllBackward, {-1,-1}},
            {TEXT("IA_GuideCommandLeftPaddle"), ERaftSimCrewCommand::TurnLeft, {-1,1}},
            {TEXT("IA_GuideCommandRightPaddle"), ERaftSimCrewCommand::TurnRight, {1,-1}}
        };
        for (const FCase& C : Cases)
        {
            Oars->LeftOar = FRaftSimOarState{}; Oars->RightOar = FRaftSimOarState{};
            FRaftSimRaftKinematicState State; State.WorldTransform = FTransform::Identity;
            Adapter->SetKinematicState(State);
            Pawn->HandleGuideCommand(FName(C.Action));
            TestEqual(TEXT("shared bound action reaches oar rig"), Raft->GetActiveCrewCommand(), C.Command);
            // Pawn sends this on every idle frame: it must not erase the order.
            Pawn->UpdateOarInputs();
            TestTrue(TEXT("idle keys preserve standing command"), Raft->ResolveOarCommandIntents().Equals(C.Intents));
            for (int32 I=0; I<50; ++I)
            {
                Raft->UpdateCrew(.01f);
                Oars->TickRig(.01f, Raft, Raft->FindAvatar(TEXT("guide")), true);
                TestTrue(TEXT("real flexible dynamics advances"), Adapter->StepRaftDynamics(.01f));
            }
            TestEqual(TEXT("left blade actually strokes"), Oars->GetOar(true).Direction, float(C.Intents.X));
            TestEqual(TEXT("right blade actually strokes"), Oars->GetOar(false).Direction, float(C.Intents.Y));
            const auto& Moved = Adapter->GetKinematicState();
            if (C.Intents.X == C.Intents.Y)
                TestTrue(FString::Printf(TEXT("actual %s blade impulses propel (vx=%.3f)"), C.Action, Moved.LinearVelocityMetersPerSecond.X), Moved.LinearVelocityMetersPerSecond.X*C.Intents.X > .01);
            else
                TestTrue(FString::Printf(TEXT("actual %s opposed blades turn (yaw rate=%.3f)"), C.Action, Moved.AngularVelocityRadiansPerSecond.Z), Moved.AngularVelocityRadiansPerSecond.Z*C.Intents.X > .001);
        }
        Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
        Raft->SetOarIntents(-1,-1);
        TestTrue(TEXT("held manual row overrides order"), Raft->ResolveOarCommandIntents().Equals(FVector2D(-1,-1)));
        Raft->SetOarIntents(0,0);
        TestTrue(TEXT("release restores order"), Raft->ResolveOarCommandIntents().Equals(FVector2D(1,1)));
        Raft->ApplyGuideSteerStroke(1);
        TestTrue(TEXT("personal steering biases real blades"), Raft->ResolveOarCommandIntents().Equals(FVector2D(1,0)));
        Raft->UpdateCrew(.8f);
        TestTrue(TEXT("steering tap expires"), Raft->ResolveOarCommandIntents().Equals(FVector2D(1,1)));
        Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both,-1);
        TestTrue(TEXT("shared back stroke works"), Raft->ResolveOarCommandIntents().Equals(FVector2D(-1,-1)));
        Raft->UpdateCrew(.8f);
        TestTrue(TEXT("stroke tap expires"), Raft->ResolveOarCommandIntents().IsNearlyZero());
        Raft->ApplyTurnStroke(-1);
        TestTrue(TEXT("shared turn stroke works"), Raft->ResolveOarCommandIntents().Equals(FVector2D(-1,1)));
        Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
        TestTrue(TEXT("rest cancels transient input"), Raft->ResolveOarCommandIntents().IsNearlyZero());
        Raft->HandleHighSideResponse(-1);
        TestEqual(TEXT("rower visibly high-sides"), Raft->FindAvatar(TEXT("guide"))->GetAvatarAction(), ERaftSimCrewAvatarAction::HighSidePort);
        TestTrue(TEXT("bracing stops blade drive"), Raft->ResolveOarCommandIntents().IsNearlyZero());
        Raft->UpdateCrew(.8f);
        const auto* HighSideRower = Raft->FindAvatar(TEXT("guide"));
        TestTrue(TEXT("single rower reaches the tube"),FMath::IsNearlyEqual(
            Raft->GetActorTransform().InverseTransformPosition(HighSideRower->GetActorLocation()).Y,-82.,.01));
        AddInfo(FString::Printf(TEXT("Rower landing local=%s hip=%s foot=%s"),
            *Raft->GetActorTransform().InverseTransformPosition(HighSideRower->GetActorLocation()).ToString(),
            *HighSideRower->GetPublishedCrewPose().LeftHipCm.ToString(),
            *HighSideRower->GetPublishedCrewPose().LeftFootCm.ToString()));
        TestTrue(TEXT("rower landing uses rendered support"),HighSideRower->HasPlantedRenderedFeet());
        TestTrue(TEXT("rower pelvis lands on tube, not below it"),
            FMath::Abs(Raft->GetCrewSeatContactClearanceCm(Raft->FindAvatar(TEXT("guide")))+1.f)<4.f);
        TestFalse(TEXT("rower does not conjure a hand paddle"),HighSideRower->GetPublishedCrewPose().bShowPaddle);
        Raft->IssueCrewCommand(ERaftSimCrewCommand::GetDown); Raft->UpdateCrew(.01f);
        TestEqual(TEXT("rower visibly braces"), Raft->FindAvatar(TEXT("guide"))->GetAvatarAction(), ERaftSimCrewAvatarAction::Brace);

        Oars->LeftOar = FRaftSimOarState{}; Oars->RightOar = FRaftSimOarState{};
        FRaftSimRaftKinematicState Moving; Moving.WorldTransform = FTransform::Identity;
        Moving.LinearVelocityMetersPerSecond = FVector(.5,0,0); Adapter->SetKinematicState(Moving);
        Pawn->HandleGuideCommand(TEXT("IA_GuideCommandStop"));
        TestTrue(TEXT("stop selects opposing blades"), Raft->ResolveOarCommandIntents().Equals(FVector2D(-1,-1)));
        for (int32 I=0; I<180; ++I)
        {
            Raft->UpdateCrew(.01f); Oars->TickRig(.01f,Raft,Raft->FindAvatar(TEXT("guide")),true);
            Adapter->StepRaftDynamics(.01f);
            TestTrue(TEXT("stop never reverses forward way"), Adapter->GetKinematicState().LinearVelocityMetersPerSecond.X >= -1.e-5);
        }
        TestTrue(TEXT("stop sheds forward speed"), Adapter->GetKinematicState().LinearVelocityMetersPerSecond.X < .5);
        Raft->ResetMotionForTesting();
        TestTrue(TEXT("reset clears all oar commands"), Raft->ResolveOarCommandIntents().IsNearlyZero());
        for (const auto& Avatar : Raft->CrewAvatars) World->DestroyActor(Avatar.Get());
        World->DestroyActor(Pawn); World->DestroyActor(Raft);
    }
    return true;
}
#endif
