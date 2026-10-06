// Rendered review of the throw-bag and flip-line choreography in the normal
// game world: a real overboard swimmer, an aimed throw, the haul and the PFD
// pull-in; then a water-generated capsize, the guide's swim back, the flip
// line and the guide climbing in. Frames are written only when
// -RaftSimRescueReviewDir= is given; the phase checks always run.
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimFlipTestEnvironment.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRescueChoreographyReviewTest,
    "RaftSim.Rescue.ChoreographyReview",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::ProductFilter)
namespace
{
UWorld* FindGameWorld()
{
    for (const auto& Context : GEngine->GetWorldContexts())
        if (Context.World() && (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
            return Context.World();
    return nullptr;
}

class FRescueChoreographyReview final : public IAutomationLatentCommand
{
public:
    explicit FRescueChoreographyReview(FAutomationTestBase* InTest) : Test(InTest) {}

    bool Update() override
    {
        UWorld* World = FindGameWorld();
        ARaftSimRaftActor* Raft = nullptr;
        if (World) for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It) { Raft = *It; break; }
        APlayerController* Player = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
        if (!Raft || !Player) { Test->AddError(TEXT("Missing playable raft/controller")); return true; }
        const double Now = World->GetTimeSeconds();
        if (StageStart < 0.) StageStart = Now;
        const double T = Now - StageStart;
        const auto NextStage = [&]() { ++Stage; StageStart = Now; };
        // A world camera that follows the boat without rolling with it.
        if (!Camera)
        {
            Camera = World->SpawnActor<ACameraActor>();
            Camera->GetCameraComponent()->SetFieldOfView(55.f);
            Player->SetViewTarget(Camera);
        }
        const FVector Focus = Raft->GetActorLocation() + FVector(0, 0, 40);
        const FVector Eye = Focus + (bHighSideDone ? FVector(-620.f, -820.f, 640.f) : FVector(-380.f, -520.f, 380.f));
        Camera->SetActorLocationAndRotation(Eye, (Focus - Eye).Rotation());
        FString Dir;
        const bool bCapture = FParse::Value(FCommandLine::Get(), TEXT("RaftSimRescueReviewDir="), Dir);
        const auto Capture = [&](const TCHAR* Prefix, double Interval)
        {
            if (!bCapture || Now < NextCapture) return;
            IFileManager::Get().MakeDirectory(*Dir, true);
            FScreenshotRequest::RequestScreenshot(Dir / FString::Printf(TEXT("%s-%03d.png"), Prefix, Shot++), true, false);
            NextCapture = Now + Interval;
        };
        auto* Bridge = Raft->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
        auto* Runtime = Bridge ? Bridge->GetRaftRuntime() : nullptr;
        if (!bHighSideDone)
        {
            // High-side toward the camera, every frame of the leap and hold,
            // then the scramble back on "Back to your seats!".
            if (HighSideStage == 0) { Raft->HandleHighSideResponse(-1); HighSideStart = Now; HighSideStage = 1; }
            else if (HighSideStage == 1)
            {
                Capture(TEXT("highside"), 1. / 30.);
                if (Now - HighSideStart > 1.6) { Raft->IssueCrewCommand(ERaftSimCrewCommand::Seats); HighSideStart = Now; HighSideStage = 2; }
            }
            else
            {
                Capture(TEXT("highreturn"), 1. / 30.);
                if (Now - HighSideStart > 2.4)
                {
                    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
                    bHighSideDone = true;
                    StageStart = Now;
                }
            }
            return false;
        }
        switch (Stage)
        {
        case 0:
            // One passenger overboard, then swum out abeam to throwing range.
            Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
            Raft->ForceCrewOverboardForTesting(1);
            for (int32 I = 1; I <= 4 && Swimmer.IsNone(); ++I)
            {
                const FName Id(*FString::Printf(TEXT("paddler_%d"), I));
                if (Raft->IsPassengerSwimming(Id)) Swimmer = Id;
            }
            if (!Test->TestFalse(TEXT("a passenger is in the water"), Swimmer.IsNone())) return true;
            NextStage();
            break;
        case 1:
        {
            FVector P;
            if (Raft->GetSwimmerWorldPosition(Swimmer, P))
            {
                const FVector Spot = Raft->GetActorLocation() - Raft->GetActorRightVector() * 520.f - Raft->GetActorForwardVector() * 60.f;
                const FVector To = Spot - P;
                if (To.Size2D() > 20.f) Raft->ApplySwimmerStroke(Swimmer, To, FMath::Min(.12f, float(To.Size2D() * .01)));
            }
            if (T > 2.5) NextStage();
            break;
        }
        case 2:
        {
            FVector P;
            Raft->GetSwimmerWorldPosition(Swimmer, P);
            Raft->AimRescue(P - Raft->GetRescueHandWorldM() * 100.);
            Test->TestTrue(TEXT("aimed throw-bag rescue starts"), Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
            NextStage();
            break;
        }
        case 3:
            Capture(TEXT("throw"), .1);
            if (Raft->GetRescueInteractionState().Phase == ERaftSimRescueInteractionPhase::ReadyForReentry && T > 1.)
            {
                Test->TestTrue(TEXT("hauled swimmer boards"), Raft->RequestSelectedReentry());
                NextStage();
            }
            else if (T > 20.) { Test->AddError(TEXT("Haul did not reach the tube")); return true; }
            break;
        case 4:
            Capture(TEXT("pullin"), .1);
            if (!Raft->IsAssistedBoardingActive() && T > .5) NextStage();
            else if (T > 8.) { Test->AddError(TEXT("Pull-in and crawl to the seat did not finish")); return true; }
            break;
        case 5:
        {
            // The same breaking broadside the flip regression uses.
            if (!Runtime) { Test->AddError(TEXT("Physics bridge missing")); return true; }
            const auto Scenes = RaftSimFlipTestEnvironment::Scenes();
            const auto Wave = *Scenes.FindByPredicate([](const auto& S) { return S.Name == TEXT("breaking_broadside_3p2m"); });
            const double Started = Now;
            const FVector Origin(Raft->GetActorLocation().X, Raft->GetActorLocation().Y, 0.);
            const TWeakObjectPtr<UWorld> WeakWorld(World);
            Runtime->SetFlexibleUniformWater(FRaftSimFlexUniformWater{}, false);
            Runtime->SetWaterSurfaceSampler([Wave, Started, Origin, WeakWorld](const FVector& P, float& Height)
            { if (!WeakWorld.IsValid()) return false; Height = Wave.Surface(P - Origin, WeakWorld->GetTimeSeconds() - Started) * 100. + Origin.Z; return true; });
            Runtime->SetFlexibleWaterFieldSampler([Wave, Started, Origin, WeakWorld](const FVector& P, FRaftSimFlexUniformWater& W)
            { if (!WeakWorld.IsValid()) return false; const double Seconds = WeakWorld->GetTimeSeconds() - Started;
              W.bWet = Wave.Wet(P - Origin); W.SurfaceHeightM = Wave.Surface(P - Origin, Seconds) + Origin.Z * .01;
              W.VelocityMps = Wave.Velocity(P - Origin, Seconds); return true; });
            NextStage();
            break;
        }
        case 6:
            Capture(TEXT("capsize"), .2);
            if (Raft->GetRaftMode() == ERaftSimRaftMode::Capsized && Raft->GetActorUpVector().Z < -.8f && Runtime)
            {
                Runtime->SetWaterSurfaceSampler([](const FVector&, float& H) { H = 0.f; return true; });
                Runtime->SetFlexibleWaterFieldSampler([](const FVector&, FRaftSimFlexUniformWater& W) { W = {}; W.bWet = true; return true; });
                NextStage();
            }
            else if (T > 15.) { Test->AddError(TEXT("No physical capsize")); return true; }
            break;
        case 7:
        {
            Capture(TEXT("swim"), .2);
            FVector Guide;
            if (Now >= NextStroke && Raft->GetSwimmerWorldPosition(TEXT("guide"), Guide))
            {
                NextStroke = Now + .3;
                Raft->ApplySwimmerStroke(TEXT("guide"), Raft->GetActorLocation() - Guide, .45f);
                Raft->RequestReflip();
            }
            if (Raft->IsFlipLineActive()) NextStage();
            else if (T > 20.) { Test->AddError(TEXT("Guide never started the flip line")); return true; }
            break;
        }
        case 8:
            Capture(TEXT("flipline"), .12);
            if (Raft->GetFlipLinePhase() == ERaftSimFlipLinePhase::Completed && T > 1.)
            {
                Test->TestTrue(TEXT("flip line rights the hull"), Raft->GetActorUpVector().Z > .65f);
                NextStage();
            }
            else if (Raft->GetFlipLinePhase() == ERaftSimFlipLinePhase::Failed || T > 25.)
            { Test->AddError(TEXT("Flip line did not complete")); return true; }
            break;
        case 9:
        {
            Capture(TEXT("climbin"), .12);
            FVector Guide;
            if (Now >= NextStroke && Raft->GetSwimmerWorldPosition(TEXT("guide"), Guide))
            {
                NextStroke = Now + .3;
                Raft->ApplySwimmerStroke(TEXT("guide"), Raft->GetActorLocation() - Guide, .4f);
                Raft->RequestSelectedReentry();
            }
            if (!Raft->IsPassengerSwimming(TEXT("guide")) && !Raft->IsAssistedBoardingActive() && T > 1.) NextStage();
            else if (T > 20.) { Test->AddError(TEXT("Guide never climbed back in")); return true; }
            break;
        }
        default:
            Test->AddInfo(FString::Printf(TEXT("RESCUE_REVIEW frames=%d swimmers_left=%d"), Shot, Raft->GetSwimmerCount()));
            return true;
        }
        return false;
    }

private:
    FAutomationTestBase* Test;
    int32 Stage = 0;
    int32 HighSideStage = 0;
    bool bHighSideDone = false;
    double HighSideStart = 0.;
    int32 Shot = 0;
    double StageStart = -1.;
    double NextCapture = 0.;
    double NextStroke = 0.;
    FName Swimmer;
    ACameraActor* Camera = nullptr;
};
}

bool FRaftSimRescueChoreographyReviewTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"))) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRescueChoreographyReview>(this));
    return true;
}
#endif
