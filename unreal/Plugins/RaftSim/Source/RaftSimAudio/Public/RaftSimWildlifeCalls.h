#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "Sound/SoundWaveProcedural.h"

#include <atomic>

#include "RaftSimWildlifeCalls.generated.h"

/** The animal calls the river's wildlife makes, synthesized (see docs/river-wildlife-reference.md). */
UENUM(BlueprintType)
enum class ERaftSimWildlifeCall : uint8
{
    None,
    BaldEagle,
    Osprey,
    CanyonWren,
    CommonRaven,
    GreatBlueHeron,
    BeltedKingfisher,
    MantledHowler,
    KeelBilledToucan,
    MontezumaOropendola,
    TorrentDuck,
    AfricanFishEagle,
    Hippo,
    ChacmaBaboon,
    Cicadas,
    TrumpeterHornbill,
    AmericanDipper,
    Chucao,
    AustralParakeet,
    RedShoulderedHawk,
    AcornWoodpecker,
    Sunbittern,
    RingedKingfisher,
    BlackFacedIbis,
    SouthernLapwing,
    RockPratincole,
    RedWingedStarling,
    SalmonSplash,
    BighornClash
};

namespace RaftSimWildlife
{
/**
 * One note of a call. A note is either a tone (a sine with a few harmonics:
 * bird whistles, chirps and songs) or a buzz (a band-limited pulse through
 * up to three formants: mammal roars, grunts, honks and croaks), with
 * optional breath/roar noise, a pitch path, vibrato, jitter and tremolo
 * (rattles and trills).
 */
struct FCallNote
{
    float Start = 0.0f;
    float Duration = 0.2f;
    float F0Start = 1000.0f;
    float F0End = 1000.0f;
    /** Pitch path shape: 1 linear, >1 holds then moves late, <1 moves early. */
    float Curve = 1.0f;
    float VibratoHz = 0.0f;
    float VibratoDepth = 0.0f;
    /** Random pitch wander, as a fraction of F0 (rough, animal voices). */
    float Jitter = 0.0f;
    float H2 = 0.0f;
    float H3 = 0.0f;
    float H4 = 0.0f;
    bool bBuzz = false;
    float Noise = 0.0f;
    float F1 = 0.0f;
    float F2 = 0.0f;
    float F3 = 0.0f;
    float FormantQ = 4.0f;
    /** Low-pass for the noise part (Hz; 0 leaves it broadband). */
    float NoiseLowpass = 0.0f;
    float Attack = 0.01f;
    float Release = 0.03f;
    float Amp = 1.0f;
    float TremoloHz = 0.0f;
    float TremoloDepth = 0.0f;
};

/** Build one call (with natural variation) as notes. */
RAFTSIMAUDIO_API TArray<FCallNote> BuildCall(ERaftSimWildlifeCall Call, FRandomStream& Random);

/** Seconds between calls for a calling animal (random within the species' habit). */
RAFTSIMAUDIO_API float NextCallInterval(ERaftSimWildlifeCall Call, FRandomStream& Random);

/** How far the call carries: full level within InnerMeters, fading out by FalloffMeters beyond. */
RAFTSIMAUDIO_API void GetCallRange(ERaftSimWildlifeCall Call, float& InnerMeters, float& FalloffMeters);

/** A voice that plays queued calls, rendered on the audio render thread. */
class RAFTSIMAUDIO_API FCallVoice
{
public:
    explicit FCallVoice(uint32 Seed, float InSampleRate = 48000.0f);
    ~FCallVoice();

    void Render(float* Out, int32 NumFrames);
    /** Game thread: start a call now. */
    void Play(TArray<FCallNote>&& Notes, float Gain);
    bool IsSilent() const { return ActiveNotes.load() == 0; }

private:
    struct FState;
    float SampleRate;
    TQueue<TPair<TArray<FCallNote>, float>, EQueueMode::Mpsc> Pending;
    std::atomic<int32> ActiveNotes{0};
    TUniquePtr<FState> State;
};

/** Render a call offline (validation and review). */
RAFTSIMAUDIO_API TArray<float> RenderCallOffline(ERaftSimWildlifeCall Call, uint32 Seed, float Seconds, int32 SampleRate = 48000);
}

/** A procedural sound wave that plays an animal's calls. */
UCLASS()
class RAFTSIMAUDIO_API URaftSimCallSoundWave : public USoundWaveProcedural
{
    GENERATED_BODY()

public:
    URaftSimCallSoundWave(const FObjectInitializer& ObjectInitializer);

    void InitializeVoice(uint32 Seed);
    RaftSimWildlife::FCallVoice* GetVoice() const { return Voice.Get(); }

    virtual int32 OnGeneratePCMAudio(TArray<uint8>& OutAudio, int32 NumSamples) override;
    virtual Audio::EAudioMixerStreamDataFormat::Type GetGeneratedPCMDataFormat() const override
    {
        return Audio::EAudioMixerStreamDataFormat::Float;
    }

private:
    TSharedPtr<RaftSimWildlife::FCallVoice, ESPMode::ThreadSafe> Voice;
};
