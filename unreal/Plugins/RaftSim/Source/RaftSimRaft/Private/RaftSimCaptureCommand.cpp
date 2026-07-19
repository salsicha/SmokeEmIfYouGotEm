// Headless visual-verification helper (P4 photoreal track). Registers
// `RaftSim.CaptureAfter <seconds> [label] [x y z pitch yaw]`. After letting the
// live water and terrain build for a few in-game seconds it optionally places a
// camera (when the 5 pose args are supplied) and makes it the view target, then
// screenshots the viewport backbuffer and requests exit. Uses FScreenshotRequest
// (the automation path) rather than the HighResShot console command, which does
// not write offscreen on Metal. Driven via a single -ExecCmds command to avoid
// the multi-command no-op pitfall.

#include "Camera/CameraActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "TimerManager.h"
#include "UnrealClient.h"

namespace RaftSimCaptureCommand
{

static ARaftSimRaftActor* FindRaft(UWorld* World)
{
    if (World != nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

static void HandleCaptureAfter(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const float Delay = Args.Num() > 0 ? FMath::Max(FCString::Atof(*Args[0]), 0.1f) : 3.0f;
    const FString Label = Args.Num() > 1 ? Args[1] : TEXT("RaftSimCapture");
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));

    // Optional camera pose: x y z pitch yaw (world cm / degrees).
    bool bHasCamera = false;
    FVector CamLoc = FVector::ZeroVector;
    FRotator CamRot = FRotator::ZeroRotator;
    if (Args.Num() >= 7)
    {
        CamLoc = FVector(FCString::Atof(*Args[2]), FCString::Atof(*Args[3]), FCString::Atof(*Args[4]));
        CamRot = FRotator(FCString::Atof(*Args[5]), FCString::Atof(*Args[6]), 0.0f);
        bHasCamera = true;
    }

    TWeakObjectPtr<UWorld> WeakWorld(World);
    FTimerHandle Handle;
    World->GetTimerManager().SetTimer(
        Handle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath, bHasCamera, CamLoc, CamRot]()
        {
            UWorld* W = WeakWorld.Get();
            if (W != nullptr && bHasCamera)
            {
                ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                    ACameraActor::StaticClass(), CamLoc, CamRot);
                if (Cam != nullptr)
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
            }
            FScreenshotRequest::RequestScreenshot(
                OutPath, /*bShowUI=*/false, /*bAddFilenameSuffix=*/false);
            UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureAfter: requested screenshot -> %s"),
                   *OutPath);

            if (W != nullptr)
            {
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    4.0f, false);
            }
        }),
        Delay, false);

    UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureAfter: capturing in %.1fs -> %s (camera=%d)"),
           Delay, *OutPath, bHasCamera ? 1 : 0);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureAfterCommand(
    TEXT("RaftSim.CaptureAfter"),
    TEXT("After N in-game seconds, optionally place a camera (x y z pitch yaw), "
         "screenshot the viewport and exit. "
         "Usage: RaftSim.CaptureAfter <seconds> [label] [x y z pitch yaw]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureAfter));

// Over-the-shoulder capture: order the crew to paddle downstream so the raft
// runs into the rapid, then place the camera behind the raft's live position
// (it is physics-driven, so it cannot be teleported) looking downstream.
static void HandleCaptureRaft(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const float Delay = Args.Num() > 0 ? FMath::Max(FCString::Atof(*Args[0]), 0.5f) : 14.0f;
    const FString Label = Args.Num() > 1 ? Args[1] : TEXT("RaftSimRaft");
    const float BackM = Args.Num() > 2 ? FCString::Atof(*Args[2]) : 8.0f;
    const float UpM = Args.Num() > 3 ? FCString::Atof(*Args[3]) : 4.0f;
    const float AheadM = Args.Num() > 4 ? FCString::Atof(*Args[4]) : 22.0f;
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));

    TWeakObjectPtr<UWorld> WeakWorld(World);

    // Start the crew paddling downstream once the raft has spawned.
    FTimerHandle PaddleHandle;
    World->GetTimerManager().SetTimer(
        PaddleHandle,
        FTimerDelegate::CreateLambda([WeakWorld]()
        {
            if (ARaftSimRaftActor* Raft = FindRaft(WeakWorld.Get()))
            {
                Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
            }
        }),
        1.0f, false);

    FTimerHandle ShotHandle;
    World->GetTimerManager().SetTimer(
        ShotHandle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath, BackM, UpM, AheadM]()
        {
            UWorld* W = WeakWorld.Get();
            if (ARaftSimRaftActor* Raft = FindRaft(W))
            {
                const FVector RaftLoc = Raft->GetActorLocation();
                FVector Fwd = Raft->GetActorForwardVector();
                Fwd.Z = 0.0f;
                Fwd = Fwd.GetSafeNormal();
                if (Fwd.IsNearlyZero())
                {
                    Fwd = FVector(1.0f, 0.0f, 0.0f);
                }
                const FVector CamLoc =
                    RaftLoc - Fwd * (BackM * 100.0f) + FVector(0.0f, 0.0f, UpM * 100.0f);
                const FVector LookAt =
                    RaftLoc + Fwd * (AheadM * 100.0f) - FVector(0.0f, 0.0f, 150.0f);
                const FRotator CamRot = (LookAt - CamLoc).Rotation();
                if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                        ACameraActor::StaticClass(), CamLoc, CamRot))
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
                UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureRaft: raft at %s"), *RaftLoc.ToString());
            }
            FScreenshotRequest::RequestScreenshot(OutPath, false, false);

            if (W != nullptr)
            {
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    4.0f, false);
            }
        }),
        Delay, false);

    UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureRaft: paddling then shooting in %.1fs -> %s"),
           Delay, *OutPath);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureRaftCommand(
    TEXT("RaftSim.CaptureRaft"),
    TEXT("Paddle the raft downstream into the rapid, then screenshot over its "
         "shoulder. Usage: RaftSim.CaptureRaft <seconds> [label] [backM] [upM] [aheadM]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureRaft));

// Deterministic close-up for M1: place an authoritative D4 rock against the
// port tube, let the fixed-step solve and dynamic mesh settle for a few frames,
// then photograph the actual contact. This is a review/capture hook only; it
// never runs unless explicitly invoked from the console.
static void HandleCaptureWrapTest(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const FString Label = Args.Num() > 0 ? Args[0] : TEXT("M1_FlexibleRaftWrap");
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));
    TWeakObjectPtr<UWorld> WeakWorld(World);

    FTimerHandle ContactHandle;
    World->GetTimerManager().SetTimer(
        ContactHandle,
        FTimerDelegate::CreateLambda([WeakWorld]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            if (W == nullptr || Raft == nullptr)
            {
                return;
            }
            const FVector RockWorld = Raft->GetActorTransform().TransformPosition(
                FVector(0.0f, -100.0f, -20.0f));
            if (ARaftSimRockObstacleActor* Rock = W->SpawnActor<ARaftSimRockObstacleActor>(
                    ARaftSimRockObstacleActor::StaticClass(), RockWorld, FRotator::ZeroRotator))
            {
                Rock->ConfigureContact(1.4f, 0.78f);
            }
        }),
        1.0f,
        false);

    FTimerHandle ShotHandle;
    World->GetTimerManager().SetTimer(
        ShotHandle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath]()
        {
            UWorld* W = WeakWorld.Get();
            if (ARaftSimRaftActor* Raft = FindRaft(W))
            {
                const FVector CamLoc = Raft->GetActorTransform().TransformPosition(
                    FVector(-420.0f, -520.0f, 300.0f));
                const FVector LookAt = Raft->GetActorLocation() + FVector(0.0f, 0.0f, 25.0f);
                if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                        ACameraActor::StaticClass(), CamLoc, (LookAt - CamLoc).Rotation()))
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
            }
            FScreenshotRequest::RequestScreenshot(OutPath, false, false);
            if (W != nullptr)
            {
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    4.0f,
                    false);
            }
        }),
        1.2f,
        false);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureWrapTestCommand(
    TEXT("RaftSim.CaptureWrapTest"),
    TEXT("Place an authoritative D4 rock against the raft and capture the visibly "
         "deformed tube. Usage: RaftSim.CaptureWrapTest [label]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureWrapTest));

} // namespace RaftSimCaptureCommand
