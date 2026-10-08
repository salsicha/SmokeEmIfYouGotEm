#include "RaftSimSynthVoice.h"

#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace RaftSimSynth
{
namespace
{
constexpr float TwoPi = 6.28318530718f;
// Coefficients and bubble pitches are refreshed every block of samples.
constexpr int32 BlockFrames = 32;

struct FRng
{
    uint32 S;
    explicit FRng(uint32 Seed) : S(Seed != 0 ? Seed : 0x9e3779b9u) {}
    uint32 Next()
    {
        S ^= S << 13;
        S ^= S >> 17;
        S ^= S << 5;
        return S;
    }
    float Uniform() { return static_cast<float>(Next() >> 8) * (1.0f / 16777216.0f); }
    float Bipolar() { return Uniform() * 2.0f - 1.0f; }
    float Range(float Min, float Max) { return Min + (Max - Min) * Uniform(); }
};

/** One-pole glide toward a target (parameter smoothing). */
struct FGlide
{
    float Value = 0.0f;
    float Coef = 1.0f;
    void Init(float TauSeconds, float Fs, float Initial)
    {
        Coef = 1.0f - FMath::Exp(-1.0f / FMath::Max(TauSeconds * Fs, 1.0f));
        Value = Initial;
    }
    float Step(float Target)
    {
        Value += Coef * (Target - Value);
        return Value;
    }
};

/** RBJ biquad, transposed direct form II. */
struct FBiquad
{
    enum class EType : uint8 { Lowpass, Highpass, Bandpass };
    float B0 = 1.0f, B1 = 0.0f, B2 = 0.0f, A1 = 0.0f, A2 = 0.0f, Z1 = 0.0f, Z2 = 0.0f;

    void Set(EType Type, float Fc, float Q, float Fs)
    {
        Fc = FMath::Clamp(Fc, 10.0f, 0.45f * Fs);
        const float W0 = TwoPi * Fc / Fs;
        const float CosW = FMath::Cos(W0);
        const float Alpha = FMath::Sin(W0) / (2.0f * FMath::Max(Q, 0.05f));
        const float A0 = 1.0f + Alpha;
        switch (Type)
        {
            case EType::Lowpass:
                B0 = (1.0f - CosW) * 0.5f;
                B1 = 1.0f - CosW;
                B2 = B0;
                break;
            case EType::Highpass:
                B0 = (1.0f + CosW) * 0.5f;
                B1 = -(1.0f + CosW);
                B2 = B0;
                break;
            case EType::Bandpass:
                B0 = Alpha;
                B1 = 0.0f;
                B2 = -Alpha;
                break;
        }
        A1 = -2.0f * CosW;
        A2 = 1.0f - Alpha;
        B0 /= A0;
        B1 /= A0;
        B2 /= A0;
        A1 /= A0;
        A2 /= A0;
    }
    float Process(float X)
    {
        const float Y = B0 * X + Z1;
        Z1 = B1 * X - A1 * Y + Z2;
        Z2 = B2 * X - A2 * Y;
        return Y;
    }
};

/** Pink noise (Paul Kellet's refined filter), about unit RMS for unit white. */
struct FPink
{
    float P0 = 0, P1 = 0, P2 = 0, P3 = 0, P4 = 0, P5 = 0, P6 = 0;
    float Process(float White)
    {
        P0 = 0.99886f * P0 + White * 0.0555179f;
        P1 = 0.99332f * P1 + White * 0.0750759f;
        P2 = 0.96900f * P2 + White * 0.1538520f;
        P3 = 0.86650f * P3 + White * 0.3104856f;
        P4 = 0.55000f * P4 + White * 0.5329522f;
        P5 = -0.7616f * P5 - White * 0.0168980f;
        const float Pink = P0 + P1 + P2 + P3 + P4 + P5 + P6 + White * 0.5362f;
        P6 = White * 0.115926f;
        return Pink * 0.2f;
    }
};

/** Smooth random wander at about Rate Hz, -1..1. */
struct FDrift
{
    float From = 0.0f, To = 0.0f, Phase = 1.0f, Step = 0.0f;
    float Process(FRng& Rng, float Rate, float Fs)
    {
        Phase += Step;
        if (Phase >= 1.0f)
        {
            Phase -= 1.0f;
            From = To;
            To = Rng.Bipolar();
            // Each segment's length varies, so the wander has no period.
            Step = Rate * Rng.Range(0.6f, 1.4f) / Fs;
        }
        const float T = Phase * Phase * (3.0f - 2.0f * Phase);
        return From + (To - From) * T;
    }
};

/**
 * A resonating air bubble (Minnaert): a sine at f0 = 3.26 / r (r in metres)
 * that rings down with damping d = 0.13 / r + 0.0072 r^-1.5 and rises in
 * pitch as it goes, f(t) = f0 (1 + sigma d t) (van den Doel 2005). Run as a
 * complex rotator so a sample costs one complex multiply; it starts at zero
 * phase, so it never clicks.
 */
struct FBubble
{
    float Re = 1.0f, Im = 0.0f, WRe = 1.0f, WIm = 0.0f;
    float F0 = 0.0f, ChirpPerSecond = 0.0f, Decay = 1.0f, Amp = 0.0f, Time = 0.0f;
    int32 Remaining = 0;
    int32 UntilUpdate = 0;

    void UpdateRotator(float Fs)
    {
        const float Freq = FMath::Min(F0 * (1.0f + ChirpPerSecond * Time), 16000.0f);
        const float Angle = TwoPi * Freq / Fs;
        const float Radius = FMath::Exp(-Decay / Fs);
        WRe = Radius * FMath::Cos(Angle);
        WIm = Radius * FMath::Sin(Angle);
    }
};

class FBubbleCloud
{
public:
    void Init(int32 MaxVoices) { Pool.SetNum(MaxVoices); }

    /** Radii follow a power law (many small bubbles, few large). */
    void Spawn(FRng& Rng, float RadiusMinMm, float RadiusMaxMm, float Sigma, float Gain, float Fs)
    {
        int32 Slot = Active;
        if (Active >= Pool.Num())
        {
            // Steal the most nearly finished bubble.
            Slot = 0;
            for (int32 Index = 1; Index < Active; ++Index)
            {
                if (Pool[Index].Remaining < Pool[Slot].Remaining)
                {
                    Slot = Index;
                }
            }
        }
        else
        {
            ++Active;
        }
        constexpr float OneMinusBeta = -1.5f;
        const float A = FMath::Pow(RadiusMinMm, OneMinusBeta);
        const float B = FMath::Pow(RadiusMaxMm, OneMinusBeta);
        const float RadiusMm = FMath::Pow(A + Rng.Uniform() * (B - A), 1.0f / OneMinusBeta);
        const float RadiusM = RadiusMm * 0.001f;
        FBubble& Bubble = Pool[Slot];
        Bubble.F0 = 3.26f / RadiusM;
        Bubble.Decay = 0.13f / RadiusM + 0.0072f * FMath::Pow(RadiusM, -1.5f);
        Bubble.ChirpPerSecond = Sigma * Bubble.Decay;
        Bubble.Amp = Gain * FMath::Clamp(FMath::Pow(RadiusMm / 3.0f, 0.9f), 0.08f, 2.5f) * Rng.Range(0.5f, 1.0f);
        Bubble.Re = 1.0f;
        Bubble.Im = 0.0f;
        Bubble.Time = 0.0f;
        Bubble.Remaining = static_cast<int32>(6.9f / Bubble.Decay * Fs);
        Bubble.UntilUpdate = BlockFrames;
        Bubble.UpdateRotator(Fs);
    }

    float Process(float Fs)
    {
        float Sum = 0.0f;
        for (int32 Index = 0; Index < Active; ++Index)
        {
            FBubble& Bubble = Pool[Index];
            const float Re = Bubble.Re * Bubble.WRe - Bubble.Im * Bubble.WIm;
            const float Im = Bubble.Re * Bubble.WIm + Bubble.Im * Bubble.WRe;
            Bubble.Re = Re;
            Bubble.Im = Im;
            Sum += Im * Bubble.Amp;
            if (--Bubble.UntilUpdate <= 0)
            {
                Bubble.Time += BlockFrames / Fs;
                Bubble.UntilUpdate = BlockFrames;
                Bubble.UpdateRotator(Fs);
            }
            if (--Bubble.Remaining <= 0)
            {
                Pool[Index] = Pool[Active - 1];
                --Active;
                --Index;
            }
        }
        return Sum;
    }

private:
    TArray<FBubble> Pool;
    int32 Active = 0;
};

/** A filtered noise burst with a raised-cosine attack and exponential decay. */
struct FBurst
{
    FBiquad Filter;
    float Gain = 0.0f;
    float DecayCoef = 0.0f;
    float Envelope = 0.0f;
    int32 AttackFrames = 0;
    int32 Age = 0;
    bool bActive = false;

    void Start(FBiquad::EType Type, float Fc, float Q, float AttackSeconds, float DecaySeconds, float InGain, float Fs)
    {
        Filter = FBiquad();
        Filter.Set(Type, Fc, Q, Fs);
        Gain = InGain;
        AttackFrames = FMath::Max(1, static_cast<int32>(AttackSeconds * Fs));
        DecayCoef = FMath::Exp(-1.0f / FMath::Max(DecaySeconds * Fs, 1.0f));
        Envelope = 0.0f;
        Age = 0;
        bActive = true;
    }
    float Process(float Noise)
    {
        if (!bActive)
        {
            return 0.0f;
        }
        if (Age < AttackFrames)
        {
            Envelope = 0.5f - 0.5f * FMath::Cos(PI * static_cast<float>(Age) / static_cast<float>(AttackFrames));
        }
        else
        {
            Envelope *= DecayCoef;
            if (Envelope < 1.0e-4f)
            {
                bActive = false;
            }
        }
        ++Age;
        return Filter.Process(Noise) * Envelope * Gain;
    }
};

struct FBurstBank
{
    FBurst Bursts[6];
    FBurst& Next()
    {
        for (FBurst& Burst : Bursts)
        {
            if (!Burst.bActive)
            {
                return Burst;
            }
        }
        // All busy: reuse the quietest.
        FBurst* Quietest = &Bursts[0];
        for (FBurst& Burst : Bursts)
        {
            if (Burst.Envelope < Quietest->Envelope)
            {
                Quietest = &Burst;
            }
        }
        return *Quietest;
    }
    float Process(FRng& Rng)
    {
        float Sum = 0.0f;
        for (FBurst& Burst : Bursts)
        {
            if (Burst.bActive)
            {
                Sum += Burst.Process(Rng.Bipolar());
            }
        }
        return Sum;
    }
};

/** Soft limiter (tanh-like) so stacked transients never hard-clip. */
float SoftClip(float X)
{
    X = FMath::Clamp(X, -3.0f, 3.0f);
    return X * (27.0f + X * X) / (27.0f + 9.0f * X * X);
}
}

struct FVoice::FState
{
    explicit FState(uint32 Seed) : Rng(Seed) {}
    FRng Rng;
    FGlide Level, Intensity, Surge, Distance;
    FPink Pink;
    float Brown = 0.0f;
    FBiquad ToneLow, ToneHigh, RumbleLow, Scrape, DistanceLow;
    FDrift SlowSurge, FastSurge, Crackle, Roughness;
    FBubbleCloud Bubbles;
    FBurstBank Bursts;
    int32 UntilBlock = 0;
    // Stroke voice: the pull through the water after a catch, and a short
    // run of bubbles shed by the blade.
    float DriveEnvelope = 0.0f;
    float DriveDecay = 0.0f;
    float BladeBubbleRate = 0.0f;
    FBiquad DriveFilter;
    // Hull thump: a low gliding sine, the inflated tube's own resonance.
    float ThumpAmp = 0.0f, ThumpTime = 0.0f, ThumpPhase = 0.0f;
    // Crew, ambience and music keep their former character, streamed.
    double Time = 0.0;
    double MusicPhase[3] = {0.0, 0.0, 0.0};
};

FVoice::FVoice(ERaftSimSynthVoiceKind InKind, uint32 Seed, float InSampleRate)
    : Kind(InKind), SampleRate(InSampleRate), State(MakeUnique<FState>(Seed * 2654435761u + 12345u))
{
    State->Level.Init(0.12f, SampleRate, 0.0f);
    State->Intensity.Init(0.25f, SampleRate, 0.0f);
    State->Surge.Init(0.4f, SampleRate, 0.0f);
    State->Distance.Init(0.6f, SampleRate, 0.0f);
    State->Bubbles.Init(Kind == ERaftSimSynthVoiceKind::Whitewater || Kind == ERaftSimSynthVoiceKind::HoleChurn ? 128 : 64);
    State->DriveFilter.Set(FBiquad::EType::Bandpass, 380.0f, 0.7f, SampleRate);
}

FVoice::~FVoice() = default;

void FVoice::SnapControls()
{
    State->Level.Value = Controls.Level.load();
    State->Intensity.Value = Controls.Intensity.load();
    State->Surge.Value = Controls.Surge.load();
    State->Distance.Value = Controls.Distance.load();
}

void FVoice::Trigger(ERaftSimSynthEvent EventKind, float Strength)
{
    Events.Enqueue(FEvent{EventKind, FMath::Clamp(Strength, 0.0f, 1.5f)});
}

void FVoice::Render(float* Out, int32 NumFrames)
{
    FState& S = *State;
    FRng& Rng = S.Rng;
    const float Fs = SampleRate;
    const float LevelTarget = FMath::Clamp(Controls.Level.load(std::memory_order_relaxed), 0.0f, 2.0f);
    const float IntensityTarget = FMath::Clamp(Controls.Intensity.load(std::memory_order_relaxed), 0.0f, 1.0f);
    const float SurgeTarget = FMath::Clamp(Controls.Surge.load(std::memory_order_relaxed), 0.0f, 1.0f);
    const float DistanceTarget = FMath::Max(Controls.Distance.load(std::memory_order_relaxed), 0.0f);

    FEvent Event;
    while (Events.Dequeue(Event))
    {
        const float Strength = Event.Strength;
        switch (Event.Kind)
        {
            case ERaftSimSynthEvent::PaddleCatch:
            case ERaftSimSynthEvent::OarCatch:
            {
                const bool bOar = Event.Kind == ERaftSimSynthEvent::OarCatch;
                // The blade's entry: a soft "thwup" as it cuts in...
                S.Bursts.Next().Start(FBiquad::EType::Bandpass, Rng.Range(380.0f, 560.0f), 0.9f,
                    0.004f, 0.045f, 0.6f * Strength, Fs);
                // ...the air it drags down closing as one deep bloop...
                S.Bubbles.Spawn(Rng, bOar ? 7.0f : 5.0f, bOar ? 11.0f : 8.0f, 1.1f, 0.4f * Strength, Fs);
                // ...then the pull: a low swish and a run of shed bubbles.
                S.DriveEnvelope = Strength;
                S.DriveDecay = FMath::Exp(-1.0f / ((bOar ? 0.6f : 0.42f) * Fs));
                S.DriveFilter.Set(FBiquad::EType::Bandpass, bOar ? 300.0f : 400.0f, 0.7f, Fs);
                S.BladeBubbleRate = (bOar ? 70.0f : 55.0f) * Strength;
                break;
            }
            case ERaftSimSynthEvent::OarRelease:
                // The blade lifting out: drips and a light splash.
                S.Bursts.Next().Start(FBiquad::EType::Highpass, 2200.0f, 0.7f, 0.002f, 0.035f, 0.35f * Strength, Fs);
                for (int32 Drop = 0; Drop < 6; ++Drop)
                {
                    S.Bubbles.Spawn(Rng, 0.5f, 1.6f, 0.4f, 0.25f * Strength, Fs);
                }
                break;
            case ERaftSimSynthEvent::HullThump:
                S.ThumpAmp = FMath::Max(S.ThumpAmp * 0.5f, 0.0f) + 0.6f * Strength;
                S.ThumpTime = 0.0f;
                S.Bursts.Next().Start(FBiquad::EType::Lowpass, 380.0f, 0.7f, 0.002f, 0.05f, 0.7f * Strength, Fs);
                break;
            case ERaftSimSynthEvent::HoleCrash:
                // The pile's top slamming down: the trough's deep thump, a
                // heavy wash rolling over, big bubbles closing as the air is
                // driven under, and spray hissing off the top.
                S.ThumpAmp = FMath::Max(S.ThumpAmp * 0.4f, 0.0f) + 0.45f * Strength;
                S.ThumpTime = 0.0f;
                S.Bursts.Next().Start(FBiquad::EType::Lowpass, Rng.Range(900.0f, 1500.0f), 0.6f,
                    Rng.Range(0.05f, 0.09f), Rng.Range(0.5f, 0.9f), 0.85f * Strength, Fs);
                S.Bursts.Next().Start(FBiquad::EType::Highpass, Rng.Range(2400.0f, 3200.0f), 0.7f,
                    0.02f, Rng.Range(0.25f, 0.4f), 0.3f * Strength, Fs);
                for (int32 Bubble = 0; Bubble < 24; ++Bubble)
                {
                    S.Bubbles.Spawn(Rng, 1.5f, 8.0f, 0.15f, 0.12f * Strength, Fs);
                }
                break;
            case ERaftSimSynthEvent::HullSlap:
                S.Bursts.Next().Start(FBiquad::EType::Bandpass, Rng.Range(800.0f, 1400.0f), 0.8f,
                    0.001f, 0.035f, 0.6f * Strength, Fs);
                for (int32 Bubble = 0; Bubble < 5; ++Bubble)
                {
                    S.Bubbles.Spawn(Rng, 1.0f, 5.0f, 0.2f, 0.3f * Strength, Fs);
                }
                break;
        }
    }

    for (int32 Frame = 0; Frame < NumFrames; ++Frame)
    {
        const float Level = S.Level.Step(LevelTarget);
        const float I = S.Intensity.Step(IntensityTarget);
        const float Surge = S.Surge.Step(SurgeTarget);
        const float Distance = S.Distance.Step(DistanceTarget);
        if (--S.UntilBlock <= 0)
        {
            S.UntilBlock = BlockFrames;
            // Tone filters follow the water. Distant water loses its highs
            // to the air and the canyon: by 100 m the roar is a low rumble.
            const float DistanceCut = 300.0f + 18000.0f * FMath::Exp(-Distance / 45.0f);
            S.DistanceLow.Set(FBiquad::EType::Lowpass, DistanceCut, 0.707f, Fs);
            switch (Kind)
            {
                case ERaftSimSynthVoiceKind::NearWater:
                    S.ToneLow.Set(FBiquad::EType::Lowpass, 1000.0f + 3600.0f * I, 0.6f, Fs);
                    S.ToneHigh.Set(FBiquad::EType::Highpass, 140.0f, 0.6f, Fs);
                    break;
                case ERaftSimSynthVoiceKind::Whitewater:
                    S.ToneLow.Set(FBiquad::EType::Lowpass, 1600.0f + 5400.0f * I, 0.6f, Fs);
                    S.ToneHigh.Set(FBiquad::EType::Highpass, 55.0f, 0.6f, Fs);
                    S.RumbleLow.Set(FBiquad::EType::Lowpass, 130.0f, 0.7f, Fs);
                    break;
                case ERaftSimSynthVoiceKind::Spray:
                    S.ToneHigh.Set(FBiquad::EType::Highpass, 2800.0f, 0.6f, Fs);
                    break;
                case ERaftSimSynthVoiceKind::HoleChurn:
                    S.ToneLow.Set(FBiquad::EType::Lowpass, 1200.0f + 3800.0f * I, 0.6f, Fs);
                    S.ToneHigh.Set(FBiquad::EType::Highpass, 40.0f, 0.6f, Fs);
                    S.RumbleLow.Set(FBiquad::EType::Lowpass, 110.0f, 0.7f, Fs);
                    break;
                case ERaftSimSynthVoiceKind::Hull:
                    S.Scrape.Set(FBiquad::EType::Bandpass, 650.0f + 400.0f * I, 0.9f, Fs);
                    break;
                default:
                    break;
            }
        }
        const float White = Rng.Bipolar();
        S.Brown = S.Brown * 0.996f + White * 0.06f;
        float Signal = 0.0f;
        switch (Kind)
        {
            case ERaftSimSynthVoiceKind::NearWater:
            {
                // Water running along the tubes: a soft wash whose brightness
                // and level follow how fast the water moves past the hull...
                const float Wash = S.ToneLow.Process(S.ToneHigh.Process(S.Pink.Process(White))) *
                    (0.06f + 0.5f * I) * (1.0f + 0.3f * S.SlowSurge.Process(Rng, 0.4f, Fs));
                // ...gurgling bubbles where it folds over itself...
                const float GurgleRate = 4.0f + 220.0f * FMath::Pow(I, 1.3f) + 30.0f * Surge;
                if (Rng.Uniform() < GurgleRate / Fs)
                {
                    S.Bubbles.Spawn(Rng, 0.9f, 7.0f, 0.12f, 0.2f, Fs);
                }
                // ...and laps: low slaps of water on the tube as the boat
                // heaves, each releasing a few bubbles.
                const float LapRate = 0.2f + 1.4f * Surge + 0.7f * I;
                if (Rng.Uniform() < LapRate / Fs)
                {
                    S.Bursts.Next().Start(FBiquad::EType::Bandpass, Rng.Range(130.0f, 380.0f), 1.3f,
                        Rng.Range(0.025f, 0.05f), Rng.Range(0.10f, 0.22f),
                        Rng.Range(0.5f, 1.0f) * (0.3f + 0.7f * Surge) * 1.6f, Fs);
                    const int32 LapBubbles = 1 + static_cast<int32>(Rng.Uniform() * 4.0f);
                    for (int32 Bubble = 0; Bubble < LapBubbles; ++Bubble)
                    {
                        S.Bubbles.Spawn(Rng, 3.0f, 8.0f, 0.15f, 0.25f, Fs);
                    }
                }
                Signal = Wash + 0.5f * S.Bubbles.Process(Fs) + S.Bursts.Process(Rng);
                break;
            }
            case ERaftSimSynthVoiceKind::Whitewater:
            {
                // Aerated water: a dense cloud of small bubbles over a broad
                // roar, a low rumble from the big hydraulics, unsteady surges,
                // and waves breaking now and then.
                const float BubbleRate = 120.0f + 2600.0f * I;
                const float Spawns = BubbleRate / Fs;
                if (Rng.Uniform() < Spawns)
                {
                    S.Bubbles.Spawn(Rng, 0.6f, 6.0f, 0.1f, 0.065f, Fs);
                }
                const float Roar = S.ToneLow.Process(S.ToneHigh.Process(S.Pink.Process(White))) * 0.5f;
                const float Rumble = S.RumbleLow.Process(S.Brown) * (0.4f + 0.6f * I) * 0.17f;
                const float SurgeDepth = 0.2f + 0.45f * Surge;
                const float SurgeGain = FMath::Max(0.25f, 1.0f +
                    SurgeDepth * (S.SlowSurge.Process(Rng, 0.18f, Fs) + 0.6f * S.FastSurge.Process(Rng, 0.6f, Fs)));
                const float CrackleGain = 1.0f + 0.15f * S.Crackle.Process(Rng, 9.0f, Fs);
                const float CrashRate = 0.4f + 1.6f * I;
                if (Rng.Uniform() < CrashRate / Fs)
                {
                    S.Bursts.Next().Start(FBiquad::EType::Lowpass, Rng.Range(1800.0f, 3200.0f), 0.6f,
                        Rng.Range(0.05f, 0.09f), Rng.Range(0.35f, 0.6f), Rng.Range(0.6f, 1.0f) * 0.6f, Fs);
                }
                Signal = (Roar * CrackleGain + Rumble) * SurgeGain + S.Bubbles.Process(Fs) + S.Bursts.Process(Rng);
                Signal *= (0.35f + 0.65f * I) * 0.8f;
                break;
            }
            case ERaftSimSynthVoiceKind::HoleChurn:
            {
                // A hole: darker than open whitewater, with a heavy low churn
                // that throbs as the pile works (Surge follows its crashes),
                // big bubbles from the air driven under, and rare stray
                // breaks; its real crashes arrive as HoleCrash events.
                if (Rng.Uniform() < (90.0f + 1800.0f * I) / Fs)
                {
                    S.Bubbles.Spawn(Rng, 0.8f, 9.0f, 0.1f, 0.07f, Fs);
                }
                const float Roar = S.ToneLow.Process(S.ToneHigh.Process(S.Pink.Process(White))) * 0.45f;
                const float Throb = 1.0f + (0.25f + 0.5f * Surge) *
                    (S.SlowSurge.Process(Rng, 0.25f, Fs) + 0.7f * S.FastSurge.Process(Rng, 1.1f, Fs));
                const float Rumble = S.RumbleLow.Process(S.Brown) * (0.6f + 0.6f * I) * 0.3f * FMath::Max(0.3f, Throb);
                if (Rng.Uniform() < (0.15f + 0.35f * I) / Fs)
                {
                    S.Bursts.Next().Start(FBiquad::EType::Lowpass, Rng.Range(1400.0f, 2400.0f), 0.6f,
                        Rng.Range(0.05f, 0.09f), Rng.Range(0.3f, 0.5f), Rng.Range(0.4f, 0.7f) * 0.5f, Fs);
                }
                float Thump = 0.0f;
                if (S.ThumpAmp > 1.0e-4f)
                {
                    const float Freq = 42.0f + 34.0f * FMath::Exp(-S.ThumpTime / 0.08f);
                    S.ThumpPhase = FMath::Fmod(S.ThumpPhase + Freq / Fs, 1.0f);
                    Thump = FMath::Sin(TwoPi * S.ThumpPhase) * S.ThumpAmp * FMath::Exp(-S.ThumpTime / 0.22f);
                    S.ThumpTime += 1.0f / Fs;
                    if (S.ThumpTime > 1.5f)
                    {
                        S.ThumpAmp = 0.0f;
                    }
                }
                Signal = Roar * FMath::Max(0.4f, Throb) + Rumble + Thump + S.Bubbles.Process(Fs) + S.Bursts.Process(Rng);
                Signal *= (0.35f + 0.65f * I) * 0.8f;
                break;
            }
            case ERaftSimSynthVoiceKind::Spray:
            {
                // Spray and foam: thousands of tiny bubbles and droplets, a
                // crackling fizz, and drops pattering on the boat.
                if (Rng.Uniform() < (20.0f + 2200.0f * I) / Fs)
                {
                    S.Bubbles.Spawn(Rng, 0.25f, 1.2f, 0.3f, 0.3f, Fs);
                }
                const float Fizz = S.ToneHigh.Process(White) * (0.5f + 0.5f * FMath::Abs(S.Crackle.Process(Rng, 30.0f, Fs))) * I;
                if (Rng.Uniform() < (4.0f + 90.0f * I) / Fs)
                {
                    S.Bursts.Next().Start(FBiquad::EType::Highpass, 1800.0f, 0.7f, 0.001f, 0.003f,
                        Rng.Range(0.3f, 0.8f), Fs);
                }
                Signal = 0.08f * Fizz + S.Bubbles.Process(Fs) + 0.3f * S.Bursts.Process(Rng);
                break;
            }
            case ERaftSimSynthVoiceKind::Strokes:
            {
                if (S.BladeBubbleRate > 0.5f && Rng.Uniform() < S.BladeBubbleRate / Fs)
                {
                    S.Bubbles.Spawn(Rng, 1.0f, 4.5f, 0.2f, 0.25f, Fs);
                }
                S.BladeBubbleRate *= FMath::Exp(-1.0f / (0.3f * Fs));
                const float Drive = S.DriveFilter.Process(S.Pink.Process(White)) * S.DriveEnvelope * 0.8f;
                S.DriveEnvelope *= S.DriveDecay;
                Signal = Drive + S.Bubbles.Process(Fs) + S.Bursts.Process(Rng);
                break;
            }
            case ERaftSimSynthVoiceKind::Hull:
            {
                // The tube's own resonance under a hit: a low thud gliding
                // down in pitch.
                float Thump = 0.0f;
                if (S.ThumpAmp > 1.0e-4f)
                {
                    const float Freq = 52.0f + 58.0f * FMath::Exp(-S.ThumpTime / 0.06f);
                    S.ThumpPhase = FMath::Fmod(S.ThumpPhase + Freq / Fs, 1.0f);
                    Thump = FMath::Sin(TwoPi * S.ThumpPhase) * S.ThumpAmp * FMath::Exp(-S.ThumpTime / 0.14f);
                    S.ThumpTime += 1.0f / Fs;
                    if (S.ThumpTime > 1.0f)
                    {
                        S.ThumpAmp = 0.0f;
                    }
                }
                // Rubber dragging over rock: rough band-limited noise.
                const float Rough = 0.4f + 0.6f * FMath::Abs(S.Roughness.Process(Rng, 25.0f, Fs));
                const float ScrapeSound = S.Scrape.Process(White + 0.5f * S.Brown) * Rough * I;
                Signal = Thump + ScrapeSound + S.Bubbles.Process(Fs) + S.Bursts.Process(Rng);
                break;
            }
            case ERaftSimSynthVoiceKind::Crew:
            {
                const double Phase = FMath::Fmod(S.Time, 2.0);
                const float VoiceGate = FMath::Pow(FMath::Max(0.0f, static_cast<float>(FMath::Sin(PI * Phase))), 3.0f);
                Signal = VoiceGate * (FMath::Sin(TwoPi * static_cast<float>(FMath::Fmod(168.0 * S.Time, 1.0))) * 0.33f +
                    FMath::Sin(TwoPi * static_cast<float>(FMath::Fmod(252.0 * S.Time, 1.0))) * 0.19f + S.Brown * 0.08f);
                break;
            }
            case ERaftSimSynthVoiceKind::Ambience:
            {
                // Sparse, pitch- and time-varied birds over a soft bed; the
                // per-second hash runs on unbounded time, so it never loops.
                const int64 SecondIndex = static_cast<int64>(S.Time);
                const float Hash = FMath::Frac(
                    FMath::Sin(static_cast<float>(SecondIndex % 100003) * 12.9898f + 4.233f) * 43758.547f);
                float Bird = 0.0f;
                if (Hash < 0.30f)
                {
                    const float ChirpStart = 0.15f + 0.55f * FMath::Frac(Hash * 11.7f);
                    const float ChirpPhase = static_cast<float>(S.Time - static_cast<double>(SecondIndex)) - ChirpStart;
                    constexpr float ChirpLengthSeconds = 0.16f;
                    if (ChirpPhase > 0.0f && ChirpPhase < ChirpLengthSeconds)
                    {
                        const float Envelope = FMath::Square(FMath::Sin(PI * ChirpPhase / ChirpLengthSeconds));
                        const float PitchHz = 950.0f + 650.0f * FMath::Frac(Hash * 7.31f);
                        Bird = Envelope * FMath::Sin(TwoPi * PitchHz * ChirpPhase) * 0.09f;
                    }
                }
                Signal = S.Brown * 0.18f + Bird;
                break;
            }
            case ERaftSimSynthVoiceKind::Music:
            {
                static constexpr double Frequencies[3] = {73.42, 110.0, 146.84};
                static constexpr float Gains[3] = {0.22f, 0.14f, 0.1f};
                for (int32 Partial = 0; Partial < 3; ++Partial)
                {
                    S.MusicPhase[Partial] = FMath::Fmod(S.MusicPhase[Partial] + Frequencies[Partial] / Fs, 1.0);
                    Signal += FMath::Sin(TwoPi * static_cast<float>(S.MusicPhase[Partial])) * Gains[Partial];
                }
                break;
            }
        }
        if (Distance > 1.0f)
        {
            Signal = S.DistanceLow.Process(Signal);
        }
        S.Time += 1.0 / Fs;
        Out[Frame] = SoftClip(Signal * Level);
    }
    RenderedFrames.fetch_add(static_cast<uint64>(NumFrames), std::memory_order_relaxed);
}

bool WriteWav16(const FString& Path, const TArray<float>& Samples, int32 InSampleRate)
{
    TArray<uint8> Bytes;
    const uint32 DataBytes = static_cast<uint32>(Samples.Num() * 2);
    auto Put32 = [&Bytes](uint32 Value) { Bytes.Append(reinterpret_cast<const uint8*>(&Value), 4); };
    auto Put16 = [&Bytes](uint16 Value) { Bytes.Append(reinterpret_cast<const uint8*>(&Value), 2); };
    Bytes.Append(reinterpret_cast<const uint8*>("RIFF"), 4);
    Put32(36 + DataBytes);
    Bytes.Append(reinterpret_cast<const uint8*>("WAVEfmt "), 8);
    Put32(16);
    Put16(1);
    Put16(1);
    Put32(static_cast<uint32>(InSampleRate));
    Put32(static_cast<uint32>(InSampleRate * 2));
    Put16(2);
    Put16(16);
    Bytes.Append(reinterpret_cast<const uint8*>("data"), 4);
    Put32(DataBytes);
    for (const float Sample : Samples)
    {
        Put16(static_cast<uint16>(static_cast<int16>(FMath::Clamp(Sample, -1.0f, 1.0f) * 32767.0f)));
    }
    return FFileHelper::SaveArrayToFile(Bytes, *Path);
}
}

URaftSimSynthSoundWave::URaftSimSynthSoundWave(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    SetSampleRate(48000);
    NumChannels = 1;
    Duration = INDEFINITELY_LOOPING_DURATION;
    bLooping = false;
    SoundGroup = SOUNDGROUP_Default;
    SampleByteSize = 4;
}

void URaftSimSynthSoundWave::InitializeVoice(ERaftSimSynthVoiceKind Kind, uint32 Seed)
{
    Voice = MakeShared<RaftSimSynth::FVoice, ESPMode::ThreadSafe>(Kind, Seed, 48000.0f);
}

int32 URaftSimSynthSoundWave::OnGeneratePCMAudio(TArray<uint8>& OutAudio, int32 NumSamples)
{
    if (!Voice.IsValid() || NumSamples <= 0)
    {
        return 0;
    }
    OutAudio.SetNumUninitialized(NumSamples * static_cast<int32>(sizeof(float)), EAllowShrinking::No);
    Voice->Render(reinterpret_cast<float*>(OutAudio.GetData()), NumSamples);
    return NumSamples;
}
