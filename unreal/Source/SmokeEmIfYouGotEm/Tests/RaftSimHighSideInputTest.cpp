#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "InputKeyEventArgs.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "UnrealClient.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "RaftSimRaftActor.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimCrewAvatarActor.h"
#include "../RaftSimGuidePlayerController.h"
#include "../RaftSimRunHudWidget.h"

#if WITH_AUTOMATION_TESTS
namespace
{
class FHighSideKeys : public IAutomationLatentCommand
{
public:
    explicit FHighSideKeys(FAutomationTestBase* InTest) : Test(InTest) {}
    bool Update() override
    {
        UWorld* World=nullptr;
        for(const auto& Context:GEngine->GetWorldContexts())
            if(Context.WorldType==EWorldType::PIE || Context.WorldType==EWorldType::Game)
                {World=Context.World();break;}
        if(!World){Test->AddError(TEXT("No production game world"));return true;}
        auto* PC=Cast<ARaftSimGuidePlayerController>(UGameplayStatics::GetPlayerController(World,0));
        ARaftSimRaftActor* Raft=nullptr;
        for(TActorIterator<ARaftSimRaftActor> It(World);It;++It){Raft=*It;break;}
        if(!PC || !Raft || !PC->GetRunHud()){Test->AddError(TEXT("Missing playable raft/controller/HUD"));return true;}
        const double Now=World->GetTimeSeconds();
        const auto Key=[PC](FKey K,EInputEvent Event)
            {PC->InputKey(FInputKeyEventArgs::CreateSimulated(K,Event,Event==IE_Released?0.f:1.f));};
        const auto Capture=[&](const TCHAR* Name)
        {
            FString Dir;
            if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimHighSideEvidenceDir="),Dir))
            {IFileManager::Get().MakeDirectory(*Dir,true);FScreenshotRequest::RequestScreenshot(Dir/Name,true,false);}
        };
        if (Phase>=2 && Phase<=4 && Now>=NextCapture)
        {
            Capture(*FString::Printf(TEXT("transfer-%03d.png"),CaptureIndex++));
            NextCapture=Now+.099;
        }
        if(Now<Next)return false;
        const auto CheckPose=[&]()
        {
            Test->TestEqual(TEXT("normal input issues high-side"),Raft->GetActiveCrewCommand(),ERaftSimCrewCommand::HighSide);
            Test->TestEqual(TEXT("held key triggers once, not once per frame"),Raft->GetHighSideResponseCount(),InitialCount+1);
            Test->TestTrue(TEXT("high-side does not open the command panel"),PC->GetRunHud()->GetVisibleOverlay()!=ERaftSimHudOverlay::CommandWheel);
            int32 Count=0;
            for(TActorIterator<ARaftSimCrewAvatarActor> It(World);It;++It)
            {
                if(It->GetAttachParentActor()!=Raft)continue;
                ++Count;
                const auto Action=It->GetAvatarAction();
                Test->TestTrue(TEXT("attached character receives high-side animation"),
                    Action==ERaftSimCrewAvatarAction::HighSidePort || Action==ERaftSimCrewAvatarAction::HighSideStarboard);
                if(const FVector* Before=NeutralTorso.Find(It->GetFName()))
                {
                    const FVector Root=Raft->GetActorTransform().InverseTransformPosition(It->GetActorLocation());
                    const FVector Shift=Root-*Before;
                    const double Side=Action==ERaftSimCrewAvatarAction::HighSidePort?-1.:1.;
                    Test->TestTrue(TEXT("all characters reach the commanded tube"),!Shift.ContainsNaN() && FMath::IsNearlyEqual(Root.Y,Side*(Raft->IsSoloOarRig()?82.:62.),.5));
                    Test->TestTrue(TEXT("production whole-body transfer is active"),It->HasHighSideTransfer());
                }
                else Test->AddError(TEXT("Missing neutral character pose"));
            }
            Test->TestEqual(TEXT("every attached crew member is checked"),Count,Raft->GetCrewAvatarCount());
            Test->TestTrue(TEXT("real crew present"),Count>0);
        };
        switch(Phase)
        {
            case 0:
                Test->TestEqual(TEXT("requested production rig loaded"),Raft->IsSoloOarRig(),FParse::Param(FCommandLine::Get(),TEXT("RaftSimHighSideOar")));
                if(auto* Guide=Cast<ARaftSimGuidePawn>(PC->GetPawn()))
                {
                    // Inspection camera only; normal body/input physics stay active.
                    Guide->SetChaseCameraAllowed(true);
                    if(!Guide->IsChaseCameraActive())Guide->ToggleChaseCamera();
                }
                Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
                if (auto* Camera=World->SpawnActor<ACameraActor>())
                {
                    Camera->AttachToActor(Raft,FAttachmentTransformRules::KeepRelativeTransform);
                    const FVector Offset(-580,-680,620);
                    Camera->SetActorRelativeLocation(Offset);
                    Camera->SetActorRelativeRotation((FVector(0,0,40)-Offset).Rotation());
                    Camera->GetCameraComponent()->SetFieldOfView(48.f);
                    PC->SetViewTarget(Camera);
                }
                break;
            case 1:
                for(TActorIterator<ARaftSimCrewAvatarActor> It(World);It;++It)
                    if(It->GetAttachParentActor()==Raft)NeutralTorso.Add(It->GetFName(),Raft->GetActorTransform().InverseTransformPosition(It->GetActorLocation()));
                InitialCount=Raft->GetHighSideResponseCount();Key(EKeys::SpaceBar,IE_Pressed);
                break;
            case 2:
                CheckPose();Capture(TEXT("keyboard-high-side.png"));Key(EKeys::SpaceBar,IE_Released);
                break;
            case 3:
                // Screenshot requests render later. Keep the pose/menu unchanged
                // for a whole phase before issuing the next input.
                Key(EKeys::One,IE_Pressed);
                break;
            case 4:
                Test->TestEqual(TEXT("ordinary forward command exits high-side"),Raft->GetActiveCrewCommand(),ERaftSimCrewCommand::AllForward);
                Key(EKeys::One,IE_Released);
                InitialCount=Raft->GetHighSideResponseCount();Key(EKeys::Gamepad_FaceButton_Left,IE_Pressed);
                break;
            case 5:
                CheckPose();Capture(TEXT("gamepad-high-side.png"));Key(EKeys::Gamepad_FaceButton_Left,IE_Released);
                break;
            case 6:
                InitialCount=Raft->GetHighSideResponseCount();Key(EKeys::Gamepad_Special_Left,IE_Pressed);
                break;
            case 7:
                Test->TestTrue(TEXT("View/Select opens command panel"),PC->GetRunHud()->GetVisibleOverlay()==ERaftSimHudOverlay::CommandWheel);
                Test->TestEqual(TEXT("opening commands does not high-side"),Raft->GetHighSideResponseCount(),InitialCount);
                Capture(TEXT("command-panel.png"));Key(EKeys::Gamepad_Special_Left,IE_Released);
                break;
            case 8:
                Key(EKeys::Gamepad_Special_Left,IE_Pressed);
                break;
            case 9:
                Test->TestTrue(TEXT("View/Select closes command panel"),PC->GetRunHud()->GetVisibleOverlay()!=ERaftSimHudOverlay::CommandWheel);
                Key(EKeys::Gamepad_Special_Left,IE_Released);Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
                return true;
        }
        ++Phase;Next=Now+1.;return false;
    }
private:
    FAutomationTestBase* Test;
    int32 Phase=0,InitialCount=0;
    double Next=0,NextCapture=0;
    int32 CaptureIndex=0;
    TMap<FName,FVector> NeutralTorso;
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHighSideInputTest,"RaftSim.Input.HighSideLiveKeys",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimHighSideInputTest::RunTest(const FString&)
{
    if(!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")))
        {AddError(TEXT("Ephemeral profile required for input validation"));return false;}
    const bool Oar=FParse::Param(FCommandLine::Get(),TEXT("RaftSimHighSideOar"));
    if(!AutomationOpenMap(Oar?TEXT("/Game/RaftSim/Maps/L_Hance"):TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"),true))return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(5.f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FHighSideKeys>(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.f));
    return true;
}
#endif
