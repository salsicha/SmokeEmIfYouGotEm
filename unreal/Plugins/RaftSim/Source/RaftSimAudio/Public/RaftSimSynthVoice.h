#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "Sound/SoundWaveProcedural.h"

#include <atomic>

#include "RaftSimSynthVoice.generated.h"

/**
 * What a streamed synth voice sounds like. The water voices are modelled on
 * how moving water makes sound: resonating air bubbles (each a short sine
 * that rises in pitch as it rings down, its pitch set by its radius),
 * broadband turbulence, and the slap of water on the hull.
 */
UENUM()
enum class ERaftSimSynthVoiceKind : uint8
{
    /** Water moving along the hull: wash, gurgling bubbles and laps. */
    NearWater,
    /** Whitewater: a dense bubble cloud, roar, rumble, surges and crashes. */
    Whitewater,
    /** Spray and foam: droplet fizz and patter. */
    Spray,
    /** Blade catches and the pull through the water (paddles and oars). */
    Strokes,
    /** Tube thumps, slaps and rock scrapes. */
    Hull,
    Crew,
    Ambience,
    Music,
    /** A hole: water falling into its trough and the foam pile tumbling back
     * onto it, a deep churning rumble under the roar; its crashes come from
     * the hole's own churn (HoleCrash). */
    HoleChurn
};

/** One-shot sounds a voice can be asked to play. */
enum class ERaftSimSynthEvent : uint8
{
    PaddleCatch,
    OarCatch,
    OarRelease,
    HullThump,
    HullSlap,
    /** A section of a hole's foam pile collapsing onto the incoming water:
     * a deep thump, a heavy wash, a burst of big bubbles and a spray hiss. */
    HoleCrash
};

namespace RaftSimSynth
{
/**
 * A voice's live controls. The game thread writes them; the audio render
 * thread reads them and glides toward them, so changes never step.
 *   Level      output gain, 0..1
 *   Intensity  how hard the water works (flow, aeration, spray, scrape), 0..1
 *   Surge      how unsteady it is (heave for laps, surging in a rapid), 0..1
 *   Distance   metres to the source; distant water loses its highs
 */
struct FControls
{
    std::atomic<float> Level{0.0f};
    std::atomic<float> Intensity{0.0f};
    std::atomic<float> Surge{0.0f};
    std::atomic<float> Distance{0.0f};
};

struct FEvent
{
    ERaftSimSynthEvent Kind = ERaftSimSynthEvent::PaddleCatch;
    float Strength = 1.0f;
};

/**
 * One streamed procedural voice. It never loops: every sample comes from
 * live random processes, so nothing repeats. Render on one thread only.
 */
class RAFTSIMAUDIO_API FVoice
{
public:
    FVoice(ERaftSimSynthVoiceKind InKind, uint32 Seed, float InSampleRate = 48000.0f);
    ~FVoice();

    /** Mono samples into Out (render thread). */
    void Render(float* Out, int32 NumFrames);

    /** Game-thread controls and one-shots. */
    FControls& GetControls() { return Controls; }
    void Trigger(ERaftSimSynthEvent Kind, float Strength);

    ERaftSimSynthVoiceKind GetKind() const { return Kind; }
    uint64 GetRenderedFrameCount() const { return RenderedFrames.load(); }

    /** Validation: snap the glides to their targets (offline renders). */
    void SnapControls();

private:
    struct FState;
    ERaftSimSynthVoiceKind Kind;
    float SampleRate;
    FControls Controls;
    TQueue<FEvent, EQueueMode::Mpsc> Events;
    std::atomic<uint64> RenderedFrames{0};
    TUniquePtr<FState> State;
};

/** Write mono float samples as a 16-bit WAV (validation renders). */
RAFTSIMAUDIO_API bool WriteWav16(const FString& Path, const TArray<float>& Samples, int32 SampleRate);
}

/** A procedural sound wave fed by a streamed synth voice on the audio render thread. */
UCLASS()
class RAFTSIMAUDIO_API URaftSimSynthSoundWave : public USoundWaveProcedural
{
    GENERATED_BODY()

public:
    URaftSimSynthSoundWave(const FObjectInitializer& ObjectInitializer);

    void InitializeVoice(ERaftSimSynthVoiceKind Kind, uint32 Seed);
    RaftSimSynth::FVoice* GetVoice() const { return Voice.Get(); }

    virtual int32 OnGeneratePCMAudio(TArray<uint8>& OutAudio, int32 NumSamples) override;
    virtual Audio::EAudioMixerStreamDataFormat::Type GetGeneratedPCMDataFormat() const override
    {
        return Audio::EAudioMixerStreamDataFormat::Float;
    }

private:
    TSharedPtr<RaftSimSynth::FVoice, ESPMode::ThreadSafe> Voice;
};
