#pragma once

#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimScreenRecorderSubsystem.generated.h"

class FFrameGrabber;
class FRaftSimWmfVideoEncoder;

/**
 * Debug screen recorder: captures the game viewport's back buffer (UI
 * included) and writes an H.264 MP4 through the Windows Media Foundation
 * sink writer. Toggled from the guide pawn's F9 binding or the
 * RaftSim.ToggleRecording console command; clips land in
 * Saved/VideoCaptures (override with raftsim.RecordingDir) so short
 * repro videos no longer depend on an external capture tool.
 */
UCLASS()
class RAFTSIMRAFT_API URaftSimScreenRecorderSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    bool IsRecording() const { return FrameGrabber != nullptr; }
    void ToggleRecording();
    bool StartRecording();
    void StopRecording();

private:
    bool PumpCapturedFrames(float DeltaSeconds);
    void ShowStatus(const FString& Message, const FColor& Color) const;

    // Raw pointers with explicit teardown: UHT's generated vtable-helper
    // constructor instantiates member destructors in gen.cpp, where these
    // forward-declared capture/encoder types are incomplete.
    FFrameGrabber* FrameGrabber = nullptr;
    FRaftSimWmfVideoEncoder* Encoder = nullptr;
    FTSTicker::FDelegateHandle TickerHandle;
    FString ActiveClipPath;
    FIntPoint CaptureSize = FIntPoint::ZeroValue;
    double RecordingStartSeconds = 0.0;
    double NextFrameDueSeconds = 0.0;
    int64 EncodedFrameCount = 0;
};
