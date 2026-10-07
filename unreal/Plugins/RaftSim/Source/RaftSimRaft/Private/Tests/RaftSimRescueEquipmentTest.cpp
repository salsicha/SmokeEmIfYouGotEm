#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "UObject/Script.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Serialization/BufferArchive.h"
#include "HAL/FileManager.h"
#include "RenderingThread.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRescueEquipmentTest,"RaftSim.Rescue.Equipment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRescueEquipmentTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard Guard;
    UWorld* World=nullptr;
    for (const auto& C:GEngine->GetWorldContexts()) if(C.WorldType==EWorldType::Editor) {World=C.World();break;}
    if (!TestNotNull(TEXT("editor world"),World)) return false;
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>();
    AActor* Camera=nullptr;
    ON_SCOPE_EXIT {
        if(Camera)World->DestroyActor(Camera);
        for(TActorIterator<ARaftSimCrewAvatarActor> It(World);It;++It)if(It->GetOwner()==Raft)World->DestroyActor(*It);
        World->DestroyActor(Raft);FlushRenderingCommands();
    };
    const bool bOar=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRescueOar"));
    if(bOar)Raft->SetRaftRigForValidation(ERaftSimRaftRig::ColoradoOarRig);
    Raft->InitializeCrewSeatingForValidation();
    auto* Runtime=NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    FRaftSimFlexParameters Flex;Flex.MassKg=220.;Flex.PassengerCount=bOar?0:4;
    const int32 CrewCount=bOar?1:5;
    FRaftSimRaftBodyConfig Body;Body.Runtime=ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg=Flex.TotalMassKg();Body.InertiaTensorKgM2=FVector(300,400,700);
    Runtime->ConfigureRaftBody(Body);
    Runtime->ConfigureFlexibleRaftModel(Flex,RaftSimFlex::BuildDefaultCrewSeats(Flex),18000.,true);
    if(!TestTrue(TEXT("actual production hull bound"),Raft->BindIsolatedFeatureHull(Runtime)))return false;
    Runtime->SetWaterSurfaceSampler([](const FVector&,float& H){H=0.f;return true;});
    Runtime->SetFlexibleWaterFieldSampler([](const FVector&,FRaftSimFlexUniformWater& W){W={};W.bWet=true;return true;});
    FString Dir;FParse::Value(FCommandLine::Get(),TEXT("RaftSimRescueCaptureDir="),Dir);
    USceneCaptureComponent2D* Capture=nullptr;UTextureRenderTarget2D* Target=nullptr;
    if(!Dir.IsEmpty())
    {
        if(!TestFalse(TEXT("fresh captures only"),IFileManager::Get().DirectoryExists(*Dir)))return false;
        IFileManager::Get().MakeDirectory(*Dir,true);
        Camera=World->SpawnActor<AActor>();Capture=NewObject<USceneCaptureComponent2D>(Camera);Camera->SetRootComponent(Capture);
        Target=NewObject<UTextureRenderTarget2D>(Capture);Target->RenderTargetFormat=RTF_RGBA8;
        Target->InitAutoFormat(960,720);Target->UpdateResourceImmediate(true);
        Capture->TextureTarget=Target;Capture->CaptureSource=SCS_FinalColorLDR;
        Capture->bCaptureEveryFrame=false;Capture->bCaptureOnMovement=false;
        Capture->ShowFlags.SetLighting(false);Capture->FOVAngle=55;Capture->RegisterComponent();
    }
    const auto Save=[&](const FString& Name) {
        if(!Capture)return;
        const FVector Eye=Raft->GetActorLocation()+FVector(750,950,650);
        Capture->SetWorldLocationAndRotation(Eye,(Raft->GetActorLocation()+FVector(0,0,60)-Eye).Rotation());
        Capture->CaptureScene();FlushRenderingCommands();FBufferArchive Bytes;
        TestTrue(TEXT("actual engine capture"),FImageUtils::ExportRenderTarget2DAsPNG(Target,Bytes) &&
            FFileHelper::SaveArrayToFile(Bytes,*FPaths::Combine(Dir,Name+TEXT(".png"))));
    };
    // Normal throw API, with a real swimmer and hand-anchored line.
    if(!bOar)
    {
    Raft->SpawnSwimmers(2,false);
    Raft->Swimmers[0].SwimmerWorldPositionMeters=FVector(-1.5,5,0);
    TestEqual(TEXT("first fallen passenger selected"),Raft->SelectedSwimmerIndex,0);
    Raft->AimRescue(Raft->Swimmers[0].SwimmerWorldPositionMeters-Raft->GetRescueHandWorldM());
    TestTrue(TEXT("pre-emergency cast starts"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    Raft->HandleHighSideResponse(1);
    Raft->UpdateCrew(.1f);
    TestFalse(TEXT("high-side releases the rescue rope"),Raft->IsGuideRescuing());
    TestEqual(TEXT("interrupted rescue retains swimmers"),Raft->GetSwimmerCount(),2);
    TestFalse(TEXT("cannot throw during high-side transfer"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    for(int I=0;I<180;++I)Raft->UpdateCrew(1.f/60.f);
    TestFalse(TEXT("guide has returned before retry"),Raft->FindAvatar(TEXT("guide"))->HasHighSideTransfer());
    Raft->AimRescue(FVector(0,-1,0));
    TestFalse(TEXT("bad aim rejected"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    Raft->AimRescue(Raft->Swimmers[0].SwimmerWorldPositionMeters-Raft->GetRescueHandWorldM());
    TestTrue(TEXT("aimed throw starts"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    TestFalse(TEXT("duplicate cast rejected"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    const auto TargetId=Raft->RescueInteraction.TargetPassengerId;
    Raft->SelectRescueTarget(1);
    TestEqual(TEXT("connected rescue retains target"),Raft->RescueInteraction.TargetPassengerId,TargetId);
    float MaxPullStep=0;
    for(int I=0;I<450;++I)
    {
        const FVector Before=Raft->Swimmers[0].SwimmerWorldPositionMeters;
        Raft->UpdateCrew(1.f/60.f);Raft->UpdateRescueInteraction(1.f/60.f);
        for(auto A:Raft->CrewAvatars)if(A)A->Tick(1.f/60.f);
        Raft->UpdateRescueLineVisual();
        MaxPullStep=FMath::Max(MaxPullStep,float(FVector::Distance(Before,Raft->Swimmers[0].SwimmerWorldPositionMeters)));
        if(I%6==0)Save(FString::Printf(TEXT("throw_%03d"),I/6));
    }
    AddInfo(FString::Printf(TEXT("HAUL_MAX_STEP metres=%.9f"),MaxPullStep));
    TestTrue(TEXT("no timer teleport during haul"),MaxPullStep<=1.4f/60.f+.001f);
    TestEqual(TEXT("haul reaches boarding gate"),Raft->RescueInteraction.Phase,ERaftSimRescueInteractionPhase::ReadyForReentry);
    TestTrue(TEXT("selected swimmer boards"),Raft->RequestSelectedReentry());
    TestEqual(TEXT("other swimmer still needs rescue"),Raft->GetSwimmerCount(),1);
    // Flight is ballistic/authored and non-homing; a target can leave its catch area.
    FRaftSimSwimmingSkillProfile Skill;
    auto Cast=URaftSimSwimmerRescueLibrary::BeginRescueInteraction(TEXT("p"),ERaftSimRescueMethod::ThrowLine,
        FVector::ZeroVector,FVector(5,0,0),FVector::ForwardVector,true,0,Skill);
    Cast=URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(Cast,FVector::ZeroVector,FVector(5,0,0),.2f);
    TestTrue(TEXT("bag actually in flight"),Cast.LineEndWorldMeters.Z>.5 && Cast.LineEndWorldMeters.X<5);
    Cast=URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(Cast,FVector::ZeroVector,FVector(5,4,0),.25f);
    TestEqual(TEXT("moving target can miss the cast"),Cast.Phase,ERaftSimRescueInteractionPhase::Failed);
    }
    for(int Side : {-1,1})
    {
        Raft->TryRestoreCheckpoint(FTransform(FVector(0,0,20)));
        FRaftSimRaftKinematicState State;
        State.WorldTransform=FTransform(FRotator(0,0,180),FVector(0,0,20));
        State.LinearVelocityMetersPerSecond=FVector(.3,0,0);
        Runtime->SetKinematicState(State);Raft->SetActorTransform(State.WorldTransform);Raft->EnterCapsize();
        const int Guide=Raft->FindSwimmerIndex(TEXT("guide"));
        Raft->Swimmers[Guide].SwimmerWorldPositionMeters=FVector(30,0,0);
        Raft->RequestReflip();TestFalse(TEXT("cannot reflip remotely"),Raft->IsFlipLineActive());
        Raft->Swimmers[Guide].SwimmerWorldPositionMeters=FVector(0,Side*1.6,0);
        const FTransform Before=Raft->GetActorTransform();
        Raft->RequestReflip();
        if(!TestTrue(TEXT("nearby guide starts climb"),Raft->IsFlipLineActive()))return false;
        TestTrue(TEXT("request preserves boat transform"),Before.Equals(Raft->GetActorTransform()));
        TestEqual(TEXT("no passengers auto-reseated"),Raft->GetSwimmerCount(),CrewCount);
        TSet<ERaftSimFlipLinePhase> Seen;
        for(int I=0;I<960 && Raft->IsFlipLineActive();++I)
        {
            Runtime->StepRaftDynamics(1.f/60.f);
            Raft->SetActorTransform(Runtime->GetKinematicState().WorldTransform);
            Raft->DriftSwimmers(1.f/60.f);
            Raft->UpdateFlipLine(1.f/60.f);Raft->UpdateRescueLineVisual();
            for(auto A:Raft->CrewAvatars)if(A)A->Tick(1.f/60.f);
            Seen.Add(Raft->GetFlipLinePhase());
            if(Side==1 && I%6==0)Save(FString::Printf(TEXT("flip_%03d"),I/6));
        }
        AddInfo(FString::Printf(TEXT("FLIP_LINE side=%d phase=%d up_z=%.5f position=%s"),Side,
            int(Raft->GetFlipLinePhase()),Raft->GetActorUpVector().Z,*Raft->GetActorLocation().ToString()));
        TestTrue(TEXT("climb hook cross pull all visited"),Seen.Contains(ERaftSimFlipLinePhase::Climbing) &&
            Seen.Contains(ERaftSimFlipLinePhase::Attaching) && Seen.Contains(ERaftSimFlipLinePhase::Crossing) && Seen.Contains(ERaftSimFlipLinePhase::Pulling));
        TestEqual(TEXT("physical righting completes"),Raft->GetFlipLinePhase(),ERaftSimFlipLinePhase::Completed);
        TestTrue(TEXT("integrated hull actually upright"),Raft->GetActorUpVector().Z>.65f);
        TestEqual(TEXT("production hull has all faces"),Runtime->GetHullGeometry().Faces.Num(),40232);
        TestEqual(TEXT("righting preserves all swimmers"),Raft->GetSwimmerCount(),CrewCount);
        TestFalse(TEXT("guide cannot self throw"),Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
        bool Boarded=false;
        for(int I=0;I<300 && !Boarded;++I)
        {
            Raft->DriftSwimmers(1.f/60.f);
            if(I%12==0)
            {
                FVector P;Raft->GetSwimmerWorldPosition(TEXT("guide"),P);
                Raft->ApplySwimmerStroke(TEXT("guide"),Raft->GetActorLocation()-P,.4f);
                Boarded=Raft->RequestSelectedReentry();
            }
        }
        TestTrue(TEXT("guide swims back and boards with ordinary controls"),Boarded);
        TestEqual(TEXT("guide boarding leaves other passengers in water"),Raft->GetSwimmerCount(),CrewCount-1);
    }
    // Regression: a wave can right an empty raft without a guide action.
    // Reconciliation must neither move the hull nor restore its occupants.
    Raft->CancelFlipLine();
    Raft->RaftMode=ERaftSimRaftMode::Capsized;
    Runtime->SetFlexibleCapsized(true);
    Raft->SetActorRotation(FRotator::ZeroRotator);
    const FTransform NaturalUpright=Raft->GetActorTransform();
    Raft->UpdateCapsizeLoop(0.f);
    TestEqual(TEXT("naturally upright boat permits boarding"),Raft->GetRaftMode(),ERaftSimRaftMode::Upright);
    TestTrue(TEXT("natural righting mode update cannot move hull"),NaturalUpright.Equals(Raft->GetActorTransform()));
    TestEqual(TEXT("natural righting never auto-seats passengers"),Raft->GetSwimmerCount(),CrewCount-1);
    return true;
}
#endif
