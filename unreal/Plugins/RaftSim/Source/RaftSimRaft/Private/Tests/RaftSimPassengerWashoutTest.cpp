#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPassengerWashoutTest,"RaftSim.Rescue.PassengerWashout",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimPassengerWashoutTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard Guard;
    UWorld* World=nullptr;
    for(const auto& C:GEngine->GetWorldContexts())if(C.WorldType==EWorldType::Editor){World=C.World();break;}
    if(!TestNotNull(TEXT("editor world"),World))return false;
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>();
    ON_SCOPE_EXIT {
        for(TActorIterator<ARaftSimCrewAvatarActor> It(World);It;++It)if(It->GetOwner()==Raft)World->DestroyActor(*It);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Runtime=NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    FRaftSimFlexParameters Flex;Flex.MassKg=220.;Flex.PassengerCount=4;
    FRaftSimRaftBodyConfig Body;Body.Runtime=ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg=Flex.TotalMassKg();Body.InertiaTensorKgM2=FVector(300,400,700);
    Runtime->ConfigureRaftBody(Body);
    Runtime->ConfigureFlexibleRaftModel(Flex,RaftSimFlex::BuildDefaultCrewSeats(Flex),18000.,true);
    if(!TestTrue(TEXT("actual production hull"),Raft->BindIsolatedFeatureHull(Runtime)))return false;
    Runtime->SetWaterSurfaceSampler([](const FVector&,float& H){H=0;return true;});
    FVector ImpactHip;double Depth=.3;FVector Flow(0,3,0);bool Wet=true;
    const auto AimWave=[&](FName Id) {
        const auto* A=Raft->FindAvatar(Id);const auto& P=A->GetPublishedCrewPose();
        ImpactHip=A->GetActorTransform().TransformPosition((P.LeftHipCm+P.RightHipCm)*.5);
    };
    Runtime->SetFlexibleWaterFieldSampler([&](const FVector& P,FRaftSimFlexUniformWater& W) {
        W={};W.bWet=Wet;W.SurfaceHeightM=0.;
        if(FVector::DistSquared2D(P,ImpactHip)<25.){W.SurfaceHeightM=ImpactHip.Z*.01+Depth;W.VelocityMps=Flow;}
        return true;
    });
    const auto Pulse=[&](int Steps,float Dt=1.f/60.f){for(int I=0;I<Steps;++I)Raft->UpdatePassengerWashouts(Dt);};
    const FName Victim(TEXT("paddler_3"));AimWave(Victim);
    Wet=false;Pulse(120);TestEqual(TEXT("dry field cannot eject"),Raft->GetSwimmerCount(),0);
    Wet=true;Depth=.1;Flow=FVector(0,8,0);Pulse(120);
    TestEqual(TEXT("shallow splash cannot eject"),Raft->GetSwimmerCount(),0);
    Depth=.3;Flow=FVector::ZeroVector;Pulse(120);
    TestEqual(TEXT("still pool cannot eject"),Raft->GetSwimmerCount(),0);
    Flow=FVector(0,6,0);auto State=Runtime->GetKinematicState();State.LinearVelocityMetersPerSecond=Flow;
    Runtime->SetKinematicState(State);Pulse(120);
    TestEqual(TEXT("fast current carried with boat cannot eject"),Raft->GetSwimmerCount(),0);
    State.LinearVelocityMetersPerSecond=FVector::ZeroVector;Runtime->SetKinematicState(State);
    Pulse(1,2.f);TestEqual(TEXT("one stalled frame cannot manufacture sustained impact"),Raft->GetSwimmerCount(),0);
    Wet=false;Pulse(30);Wet=true;Flow=FVector(0,3,0);
    Pulse(3);Wet=false;Pulse(30);Wet=true;Pulse(3);
    TestEqual(TEXT("isolated small splashes recover grip"),Raft->GetSwimmerCount(),0);
    Wet=false;Pulse(30);Wet=true;

    auto* Passenger=Raft->FindAvatar(Victim);Passenger->SetAvatarAction(ERaftSimCrewAvatarAction::Brace);AimWave(Victim);
    Pulse(24);TestEqual(TEXT("braced passenger withstands moderate breaker"),Raft->GetSwimmerCount(),0);
    Wet=false;Pulse(60);Wet=true;Passenger->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);AimWave(Victim);
    const FVector Release=Passenger->GetActorLocation()*.01;
    const FTransform BoatBefore=Raft->GetActorTransform();Pulse(24);
    TestEqual(TEXT("only exposed seat is washed out"),Raft->GetSwimmerCount(),1);
    if(!TestTrue(TEXT("correct passenger, not first roster entry"),Raft->IsPassengerSwimming(Victim)))return false;
    TestFalse(TEXT("guide stays aboard"),Raft->IsPassengerSwimming(TEXT("guide")));
    TestEqual(TEXT("boat need not flip"),Raft->GetRaftMode(),ERaftSimRaftMode::Upright);
    TestTrue(TEXT("ejection cannot alter boat pose"),BoatBefore.Equals(Raft->GetActorTransform()));
    TestNull(TEXT("swimmer detached from seat"),Passenger->GetAttachParentActor());
    TestEqual(TEXT("swimming animation"),Passenger->GetAvatarAction(),ERaftSimCrewAvatarAction::Swimming);
    const auto& Swimmer=Raft->Swimmers[0];
    TestTrue(TEXT("release retains actual height before buoyant resurfacing"),FMath::IsNearlyEqual(Swimmer.SwimmerWorldPositionMeters.Z,Release.Z));
    TestTrue(TEXT("water supplies release momentum"),Swimmer.SwimmerDriftVelocityMetersPerSecond.Y>1.);
    Pulse(120);TestEqual(TEXT("cannot duplicate a detached passenger"),Raft->GetSwimmerCount(),1);

    // A second washout must not sever a rope already cast to the first swimmer.
    Raft->AimRescue(Raft->Swimmers[0].SwimmerWorldPositionMeters-Raft->GetRescueHandWorldM());
    TestTrue(TEXT("washed-out passenger accepts normal throw bag"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    const auto Connected=Raft->GetRescueInteractionState();
    auto* Second=Raft->FindAvatar(TEXT("paddler_2"));Second->SetAvatarAction(ERaftSimCrewAvatarAction::Brace);
    AimWave(TEXT("paddler_2"));Depth=.6;Flow=FVector(0,6,0);Pulse(20);
    TestEqual(TEXT("severe sustained water can overcome brace"),Raft->GetSwimmerCount(),2);
    TestEqual(TEXT("new washout keeps current rescue target"),Raft->GetRescueInteractionState().TargetPassengerId,Connected.TargetPassengerId);
    TestEqual(TEXT("new washout keeps current rescue phase"),Raft->GetRescueInteractionState().Phase,Connected.Phase);
    TestEqual(TEXT("new washout preserves first swimmer clock"),Raft->Swimmers[0].TimeInWaterSeconds,0.f);
    Wet=false;Runtime->StepRaftDynamics(1.f/120.f);
    TestTrue(TEXT("two lost passengers remove 150kg from physical crew load"),
        FMath::IsNearlyEqual(Runtime->GetLastFlexibleStepTelemetry().OccupiedCrewMassKg,235.));
    TestEqual(TEXT("full production hull retained"),Runtime->GetHullGeometry().Faces.Num(),38344);
    // Use normal water drift, haul and boarding after the breaker has passed.
    Wet=true;ImpactHip=FVector(100000,0,0);Flow=FVector::ZeroVector;
    for(int I=0;I<900 && Raft->GetRescueInteractionState().Phase!=ERaftSimRescueInteractionPhase::ReadyForReentry;++I)
    {Raft->DriftSwimmers(1.f/60.f);Raft->UpdateRescueInteraction(1.f/60.f);}
    TestTrue(TEXT("washed-out passenger can be hauled and boarded"),Raft->RequestSelectedReentry());
    TestEqual(TEXT("second swimmer still needs separate rescue"),Raft->GetSwimmerCount(),1);
    Raft->TryRestoreCheckpoint(FTransform::Identity);
    TestEqual(TEXT("checkpoint clears all accumulated exposure"),Raft->PassengerWashImpulseNs.Num(),0);
    TestEqual(TEXT("checkpoint restores crew"),Raft->GetSwimmerCount(),0);
    return true;
}
#endif
