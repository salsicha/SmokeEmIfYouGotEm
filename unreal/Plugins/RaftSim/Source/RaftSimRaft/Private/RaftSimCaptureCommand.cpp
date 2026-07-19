// Headless visual-verification helper (P4 photoreal track). Registers
// `RaftSim.CaptureAfter <seconds> [label]`, which — after letting the live
// water and terrain build for a few in-game seconds — requests a screenshot of
// the game viewport backbuffer and then requests exit. Uses FScreenshotRequest
// (the automation path) rather than the HighResShot console command, which does
// not write offscreen on Metal. Driven via a single -ExecCmds command to avoid
// the multi-command no-op pitfall.

#include "Engine/Engine.h"
#include "Engine/World.h"
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

    TWeakObjectPtr<UWorld> WeakWorld(World);
    FTimerHandle Handle;
    World->GetTimerManager().SetTimer(
        Handle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath]()
        {
            UWorld* W = WeakWorld.Get();
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

    UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureAfter: capturing in %.1fs -> %s"),
           Delay, *OutPath);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureAfterCommand(
    TEXT("RaftSim.CaptureAfter"),
    TEXT("After N in-game seconds, screenshot the viewport and exit. "
         "Usage: RaftSim.CaptureAfter <seconds> [label]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureAfter));

} // namespace RaftSimCaptureCommand
