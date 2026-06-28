#include "RaftSimReplaySubsystem.h"

#include "Misc/Paths.h"

bool URaftSimReplaySubsystem::LoadReplayManifest(const FString& ManifestPath)
{
    PlaybackState.ReplayManifestPath = ManifestPath;
    PlaybackState.CurrentFrameIndex = 0;
    PlaybackState.bLoaded = !ManifestPath.IsEmpty();
    PlaybackState.bPlaying = false;
    AccumulatorSeconds = 0.0f;
    return PlaybackState.bLoaded;
}

void URaftSimReplaySubsystem::SetPlaying(bool bInPlaying)
{
    PlaybackState.bPlaying = bInPlaying && PlaybackState.bLoaded;
}

FRaftSimReplayFrame URaftSimReplaySubsystem::AdvanceReplay(float DeltaSeconds)
{
    if (!PlaybackState.bLoaded || !PlaybackState.bPlaying)
    {
        return FRaftSimReplayFrame();
    }

    AccumulatorSeconds += FMath::Max(DeltaSeconds, 0.0f);
    while (AccumulatorSeconds >= FixedFrameSeconds)
    {
        AccumulatorSeconds -= FixedFrameSeconds;
        ++PlaybackState.CurrentFrameIndex;
    }

    FRaftSimReplayFrame Frame;
    Frame.FrameIndex = PlaybackState.CurrentFrameIndex;
    Frame.TimeSeconds = PlaybackState.CurrentFrameIndex * FixedFrameSeconds;
    Frame.RaftState.WorldTransform.SetLocation(FVector(Frame.TimeSeconds * 100.0f, 0.0f, 0.0f));
    return Frame;
}
