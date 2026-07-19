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
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealClient.h"

namespace RaftSimCaptureCommand
{

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

} // namespace RaftSimCaptureCommand
