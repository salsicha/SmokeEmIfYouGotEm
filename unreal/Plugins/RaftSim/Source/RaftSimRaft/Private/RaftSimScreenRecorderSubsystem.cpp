#include "RaftSimScreenRecorderSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "FrameGrabber.h"
#include "TimerManager.h"
#include "Widgets/SViewport.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "Slate/SceneViewport.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#include <mfapi.h>
#include <mferror.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include "Windows/HideWindowsPlatformTypes.h"
#endif

static TAutoConsoleVariable<FString> CVarRaftSimRecordingDir(
    TEXT("raftsim.RecordingDir"),
    TEXT(""),
    TEXT("Directory for RaftSim debug screen recordings. Empty = the "
         "project's Saved/VideoCaptures folder."));

namespace
{
constexpr double kRecordingFrameRate = 30.0;
constexpr double kRecordingFrameIntervalSeconds = 1.0 / kRecordingFrameRate;
constexpr uint32 kRecordingBitsPerSecond = 12u * 1000u * 1000u;

struct FRecordingFramePayload : IFramePayload
{
    explicit FRecordingFramePayload(double InSeconds) : Seconds(InSeconds) {}
    double Seconds;
};
}

#if PLATFORM_WINDOWS
/**
 * Minimal Media Foundation H.264 writer: BGRA frames in, fragmented-safe
 * MP4 out. Runs entirely on the game thread; the OS sink writer owns its
 * own worker threads, so per-frame WriteSample calls stay cheap at 1080p30.
 */
class FRaftSimWmfVideoEncoder
{
public:
    static FRaftSimWmfVideoEncoder* Create(
        const FString& FilePath, const FIntPoint& Size)
    {
        FRaftSimWmfVideoEncoder* Encoder = new FRaftSimWmfVideoEncoder();
        if (!Encoder->Initialize(FilePath, Size))
        {
            delete Encoder;
            return nullptr;
        }
        return Encoder;
    }

    ~FRaftSimWmfVideoEncoder()
    {
        Finalize();
        if (bStartedMediaFoundation)
        {
            MFShutdown();
        }
    }

    bool WriteFrame(const TArray<FColor>& Pixels, double TimeSeconds, double DurationSeconds)
    {
        if (!SinkWriter || Pixels.Num() < Width * Height)
        {
            return false;
        }
        IMFMediaBuffer* Buffer = nullptr;
        const uint32 FrameBytes = Width * Height * 4;
        if (FAILED(MFCreateMemoryBuffer(FrameBytes, &Buffer)))
        {
            return false;
        }
        uint8* Destination = nullptr;
        bool bWritten = false;
        if (SUCCEEDED(Buffer->Lock(&Destination, nullptr, nullptr)))
        {
            // Media Foundation RGB32 with a positive default stride is
            // bottom-up; the frame grabber hands rows top-down. Flip on
            // copy so the clip is upright everywhere it is played.
            const uint32 RowBytes = Width * 4;
            for (int32 Row = 0; Row < Height; ++Row)
            {
                FMemory::Memcpy(
                    Destination + (Height - 1 - Row) * RowBytes,
                    Pixels.GetData() + Row * Width,
                    RowBytes);
            }
            Buffer->Unlock();
            Buffer->SetCurrentLength(FrameBytes);
            IMFSample* Sample = nullptr;
            if (SUCCEEDED(MFCreateSample(&Sample)))
            {
                Sample->AddBuffer(Buffer);
                Sample->SetSampleTime(
                    static_cast<LONGLONG>(TimeSeconds * 10'000'000.0));
                Sample->SetSampleDuration(static_cast<LONGLONG>(
                    DurationSeconds * 10'000'000.0));
                bWritten =
                    SUCCEEDED(SinkWriter->WriteSample(StreamIndex, Sample));
                Sample->Release();
            }
        }
        Buffer->Release();
        return bWritten;
    }

    void Finalize()
    {
        if (SinkWriter)
        {
            SinkWriter->Finalize();
            SinkWriter->Release();
            SinkWriter = nullptr;
        }
    }

private:
    FRaftSimWmfVideoEncoder() = default;

    bool Initialize(const FString& FilePath, const FIntPoint& Size)
    {
        // H.264 requires even dimensions; the viewport is trimmed to match.
        Width = Size.X & ~1;
        Height = Size.Y & ~1;
        if (Width <= 0 || Height <= 0)
        {
            return false;
        }
        if (FAILED(MFStartup(MF_VERSION, MFSTARTUP_LITE)))
        {
            return false;
        }
        bStartedMediaFoundation = true;

        IMFAttributes* WriterAttributes = nullptr;
        MFCreateAttributes(&WriterAttributes, 1);
        if (WriterAttributes)
        {
            WriterAttributes->SetUINT32(
                MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS, 1);
        }
        const bool bWriterCreated = SUCCEEDED(MFCreateSinkWriterFromURL(
            *FilePath, nullptr, WriterAttributes, &SinkWriter));
        if (WriterAttributes)
        {
            WriterAttributes->Release();
        }
        if (!bWriterCreated)
        {
            return false;
        }

        IMFMediaType* OutputType = nullptr;
        MFCreateMediaType(&OutputType);
        OutputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
        OutputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_H264);
        OutputType->SetUINT32(MF_MT_AVG_BITRATE, kRecordingBitsPerSecond);
        OutputType->SetUINT32(
            MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
        MFSetAttributeSize(OutputType, MF_MT_FRAME_SIZE, Width, Height);
        MFSetAttributeRatio(
            OutputType, MF_MT_FRAME_RATE,
            static_cast<UINT32>(kRecordingFrameRate), 1);
        MFSetAttributeRatio(OutputType, MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
        const bool bOutputSet = SUCCEEDED(
            SinkWriter->AddStream(OutputType, &StreamIndex));
        OutputType->Release();

        IMFMediaType* InputType = nullptr;
        MFCreateMediaType(&InputType);
        InputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
        InputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_RGB32);
        InputType->SetUINT32(
            MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
        MFSetAttributeSize(InputType, MF_MT_FRAME_SIZE, Width, Height);
        MFSetAttributeRatio(
            InputType, MF_MT_FRAME_RATE,
            static_cast<UINT32>(kRecordingFrameRate), 1);
        MFSetAttributeRatio(InputType, MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
        const bool bInputSet = SUCCEEDED(SinkWriter->SetInputMediaType(
            StreamIndex, InputType, nullptr));
        InputType->Release();

        if (!bOutputSet || !bInputSet ||
            FAILED(SinkWriter->BeginWriting()))
        {
            SinkWriter->Release();
            SinkWriter = nullptr;
            return false;
        }
        return true;
    }

public:
    int32 Width = 0;
    int32 Height = 0;

private:
    IMFSinkWriter* SinkWriter = nullptr;
    DWORD StreamIndex = 0;
    bool bStartedMediaFoundation = false;
};
#else
class FRaftSimWmfVideoEncoder
{
public:
    static FRaftSimWmfVideoEncoder* Create(const FString&, const FIntPoint&)
    {
        return nullptr;
    }
    bool WriteFrame(const TArray<FColor>&, double, double) { return false; }
    void Finalize() {}
    int32 Width = 0;
    int32 Height = 0;
};
#endif

void URaftSimScreenRecorderSubsystem::Initialize(
    FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateUObject(
            this, &URaftSimScreenRecorderSubsystem::PumpCapturedFrames));
}

void URaftSimScreenRecorderSubsystem::Deinitialize()
{
    StopRecording();
    if (TickerHandle.IsValid())
    {
        FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
        TickerHandle.Reset();
    }
    Super::Deinitialize();
}

void URaftSimScreenRecorderSubsystem::ToggleRecording()
{
    if (IsRecording())
    {
        StopRecording();
    }
    else
    {
        StartRecording();
    }
}

bool URaftSimScreenRecorderSubsystem::StartRecording()
{
    if (IsRecording())
    {
        return true;
    }
    // Resolve the game's scene viewport through its Slate widget so the
    // same path serves a standalone -game window AND play-in-editor (the
    // first cut read UGameEngine::SceneViewport, which is null in PIE —
    // "I get recording unavailable: no standalone game viewport",
    // 2026-09-02). Game viewport widgets always host an FSceneViewport.
    TSharedPtr<FSceneViewport> SceneViewport;
    if (UGameViewportClient* ViewportClient =
            GetGameInstance() ? GetGameInstance()->GetGameViewportClient()
                              : nullptr)
    {
        if (TSharedPtr<SViewport> ViewportWidget =
                ViewportClient->GetGameViewportWidget())
        {
            SceneViewport = StaticCastSharedPtr<FSceneViewport>(
                ViewportWidget->GetViewportInterface().Pin());
        }
    }
    if (!SceneViewport.IsValid())
    {
        ShowStatus(
            TEXT("Recording unavailable: the game viewport is not ready "
                 "yet."),
            FColor::Orange);
        return false;
    }
    const FIntPoint ViewportSize = SceneViewport->GetSize();
    CaptureSize = FIntPoint(ViewportSize.X & ~1, ViewportSize.Y & ~1);
    if (CaptureSize.X <= 0 || CaptureSize.Y <= 0)
    {
        return false;
    }

    FString Directory = CVarRaftSimRecordingDir.GetValueOnGameThread();
    if (Directory.IsEmpty())
    {
        Directory = FPaths::VideoCaptureDir();
    }
    IFileManager::Get().MakeDirectory(*Directory, true);
    ActiveClipPath = FPaths::ConvertRelativePathToFull(
        Directory /
        FString::Printf(
            TEXT("RaftSim_%s.mp4"),
            *FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S"))));

    Encoder = FRaftSimWmfVideoEncoder::Create(ActiveClipPath, CaptureSize);
    if (!Encoder)
    {
        ShowStatus(
            TEXT("Recording failed to start: could not open the H.264 "
                 "writer."),
            FColor::Red);
        return false;
    }

    FrameGrabber =
        new FFrameGrabber(SceneViewport.ToSharedRef(), CaptureSize);
    FrameGrabber->StartCapturingFrames();
    RecordingStartSeconds = FPlatformTime::Seconds();
    NextFrameDueSeconds = RecordingStartSeconds;
    EncodedFrameCount = 0;
    PendingPixels.Reset();
    PendingFrameSeconds = FirstFrameSeconds = -1.0;
    EncodedDurationSeconds = 0.0;
    ShowStatus(
        FString::Printf(TEXT("REC ● %s"), *ActiveClipPath),
        FColor::Red);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim recording started: %s (%dx%d; target %.0f fps, actual capture-time timestamps)"),
        *ActiveClipPath, CaptureSize.X, CaptureSize.Y, kRecordingFrameRate);
    return true;
}

void URaftSimScreenRecorderSubsystem::StopRecording()
{
    if (!IsRecording())
    {
        return;
    }
    FrameGrabber->StopCapturingFrames();
    // Finish render-thread readbacks before draining the last frames.
    // Request timestamps travel with each frame; readback latency must not
    // become playback time, nor may a hitch be hidden by frameCount / 30.
    FrameGrabber->Shutdown();
    for (FCapturedFrameData& Frame : FrameGrabber->GetCapturedFrames())
    {
        QueueCapturedFrame(MoveTemp(Frame));
    }
    WritePendingFrame(FPlatformTime::Seconds() - RecordingStartSeconds);
    PendingPixels.Reset();
    PendingFrameSeconds = -1.0;
    delete FrameGrabber;
    FrameGrabber = nullptr;
    Encoder->Finalize();
    delete Encoder;
    Encoder = nullptr;
    const double DurationSeconds = EncodedDurationSeconds;
    ShowStatus(
        FString::Printf(
            TEXT("Recording saved (%.1f s): %s"),
            DurationSeconds, *ActiveClipPath),
        FColor::Green);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim recording saved: %s (%lld source_frames, %.3f s; encoder may repeat frames to preserve duration)"),
        *ActiveClipPath, EncodedFrameCount, DurationSeconds);
}

void URaftSimScreenRecorderSubsystem::WritePendingFrame(double EndSeconds)
{
    if (!Encoder || PendingFrameSeconds < 0.0 || PendingPixels.IsEmpty()) return;
    const double Duration = FMath::Max(EndSeconds-PendingFrameSeconds, 0.0001);
    const double PresentationSeconds = PendingFrameSeconds-FirstFrameSeconds;
    if (Encoder->WriteFrame(PendingPixels, PresentationSeconds, Duration))
    {
        ++EncodedFrameCount;
        EncodedDurationSeconds = PresentationSeconds + Duration;
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim recording failed to encode frame at %.6f s"), PresentationSeconds);
    }
}

void URaftSimScreenRecorderSubsystem::QueueCapturedFrame(FCapturedFrameData&& Frame)
{
    const FRecordingFramePayload* Payload = Frame.GetPayload<FRecordingFramePayload>();
    if (!Payload || !FMath::IsFinite(Payload->Seconds) || Payload->Seconds < 0.0 ||
        (PendingFrameSeconds >= 0.0 && Payload->Seconds <= PendingFrameSeconds))
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim recording rejected missing or non-increasing capture timestamp"));
        return;
    }
    if (FirstFrameSeconds < 0.0) FirstFrameSeconds = Payload->Seconds;
    WritePendingFrame(Payload->Seconds);
    PendingFrameSeconds = Payload->Seconds;
    PendingPixels = MoveTemp(Frame.ColorBuffer);
}

bool URaftSimScreenRecorderSubsystem::PumpCapturedFrames(float)
{
    if (!IsRecording())
    {
        return true;
    }
    // The game viewport disappearing mid-clip (window closed, PIE session
    // ended) ends the recording cleanly instead of writing garbage.
    if (!GetGameInstance() || !GetGameInstance()->GetGameViewportClient())
    {
        StopRecording();
        return true;
    }
    // FApp's cached frame clock predates blocking encoder startup. Reading
    // the monotonic clock here avoids manufacturing a long first-frame hold.
    const double NowSeconds = FPlatformTime::Seconds();
    if (NowSeconds >= NextFrameDueSeconds)
    {
        FrameGrabber->CaptureThisFrame(MakeShared<FRecordingFramePayload, ESPMode::ThreadSafe>(
            NowSeconds - RecordingStartSeconds));
        // Catch up in whole intervals so a hitch does not queue a burst.
        NextFrameDueSeconds = FMath::Max(
            NextFrameDueSeconds + kRecordingFrameIntervalSeconds,
            NowSeconds - kRecordingFrameIntervalSeconds);
    }
    for (FCapturedFrameData& Frame : FrameGrabber->GetCapturedFrames())
    {
        QueueCapturedFrame(MoveTemp(Frame));
    }
    return true;
}

void URaftSimScreenRecorderSubsystem::ShowStatus(
    const FString& Message, const FColor& Color) const
{
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(
            reinterpret_cast<uint64>(this), 6.0f, Color, Message);
    }
}

static FAutoConsoleCommandWithWorldAndArgs GToggleRecordingCommand(
    TEXT("RaftSim.ToggleRecording"),
    TEXT("Start or stop the debug screen recording (also bound to F9). "
         "Optional argument: seconds to wait before toggling (lets boot-time "
         "ExecCmds start a clip after the viewport exists). Clips are "
         "written to Saved/VideoCaptures or raftsim.RecordingDir."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World || !World->GetGameInstance())
            {
                return;
            }
            const auto Toggle = [WeakWorld = MakeWeakObjectPtr(World)]()
            {
                if (!WeakWorld.IsValid() ||
                    !WeakWorld->GetGameInstance())
                {
                    return;
                }
                if (URaftSimScreenRecorderSubsystem* Recorder =
                        WeakWorld->GetGameInstance()
                            ->GetSubsystem<URaftSimScreenRecorderSubsystem>())
                {
                    Recorder->ToggleRecording();
                }
            };
            const float DelaySeconds =
                Args.Num() > 0 ? FCString::Atof(*Args[0]) : 0.0f;
            if (DelaySeconds > 0.0f)
            {
                FTimerHandle Unused;
                World->GetTimerManager().SetTimer(
                    Unused,
                    FTimerDelegate::CreateLambda(Toggle),
                    DelaySeconds,
                    false);
            }
            else
            {
                Toggle();
            }
        }));
