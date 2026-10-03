// Audio: the streamed water synth renders the river's scenes offline (still
// pool, current, a rapid heard from 120 m to inside it, paddle and oar
// strokes, hull hits). It checks that nothing repeats (the former mix looped
// a 2 s buffer), nothing clips, louder water is louder, distant water is
// darker, and strokes and hits stand out. The scenes are written as WAVs to
// Saved/RaftSimValidation/audio/water-synth for listening.

#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "RaftSimSynthVoice.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterSynthScenesTest,
    "RaftSim.Audio.WaterSynthScenes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

// Keep these scene helpers scoped in unity builds; SampleRate must not become
// a global declaration that shadows another test's local/parameter names.
namespace RaftSimWaterSynthScenes
{
constexpr int32 SampleRate = 48000;
constexpr int32 Block = 512;

using RaftSimSynth::FVoice;

struct FSceneVoice
{
    TUniquePtr<FVoice> Voice;
    float Gain = 1.0f;
};

/** A scene: voices, a per-block control script, and events. */
struct FSynthScene
{
    FString Name;
    float Seconds = 8.0f;
    TArray<FSceneVoice> Voices;
    TFunction<void(float, TArray<FSceneVoice>&)> Script;
};

FVoice& AddVoice(FSynthScene& Scene, ERaftSimSynthVoiceKind Kind, uint32 Seed, float Gain)
{
    FSceneVoice& Entry = Scene.Voices.AddDefaulted_GetRef();
    Entry.Voice = MakeUnique<FVoice>(Kind, Seed, static_cast<float>(SampleRate));
    Entry.Gain = Gain;
    return *Entry.Voice;
}

void Set(FVoice& Voice, float Level, float Intensity, float Surge = 0.0f, float Distance = 0.0f)
{
    Voice.GetControls().Level = Level;
    Voice.GetControls().Intensity = Intensity;
    Voice.GetControls().Surge = Surge;
    Voice.GetControls().Distance = Distance;
}

TArray<float> Render(FSynthScene& Scene)
{
    const int32 Total = static_cast<int32>(Scene.Seconds * SampleRate);
    TArray<float> Mix;
    Mix.SetNumZeroed(Total);
    TArray<float> Scratch;
    Scratch.SetNumUninitialized(Block);
    bool bFirst = true;
    for (int32 Start = 0; Start < Total; Start += Block)
    {
        const int32 Count = FMath::Min(Block, Total - Start);
        if (Scene.Script)
        {
            Scene.Script(static_cast<float>(Start) / SampleRate, Scene.Voices);
        }
        for (FSceneVoice& Entry : Scene.Voices)
        {
            if (bFirst)
            {
                Entry.Voice->SnapControls();
            }
            Entry.Voice->Render(Scratch.GetData(), Count);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                Mix[Start + Index] += Scratch[Index] * Entry.Gain;
            }
        }
        bFirst = false;
    }
    return Mix;
}

float Rms(const TArray<float>& Samples, int32 Begin, int32 End)
{
    double Sum = 0.0;
    End = FMath::Min(End, Samples.Num());
    for (int32 Index = Begin; Index < End; ++Index)
    {
        Sum += static_cast<double>(Samples[Index]) * Samples[Index];
    }
    return End > Begin ? static_cast<float>(FMath::Sqrt(Sum / (End - Begin))) : 0.0f;
}

/** Normalised correlation of the signal with itself LagSeconds later. */
float LagCorrelation(const TArray<float>& Samples, float StartSeconds, float LengthSeconds, float LagSeconds)
{
    const int32 Begin = static_cast<int32>(StartSeconds * SampleRate);
    const int32 Length = static_cast<int32>(LengthSeconds * SampleRate);
    const int32 Lag = static_cast<int32>(LagSeconds * SampleRate);
    double Cross = 0.0, A = 0.0, B = 0.0;
    for (int32 Index = Begin; Index < Begin + Length && Index + Lag < Samples.Num(); ++Index)
    {
        Cross += static_cast<double>(Samples[Index]) * Samples[Index + Lag];
        A += static_cast<double>(Samples[Index]) * Samples[Index];
        B += static_cast<double>(Samples[Index + Lag]) * Samples[Index + Lag];
    }
    return A > 0.0 && B > 0.0 ? static_cast<float>(Cross / FMath::Sqrt(A * B)) : 0.0f;
}

/** Brightness proxy: the fraction of energy in the sample-to-sample change. */
float Brightness(const TArray<float>& Samples, int32 Begin, int32 End)
{
    double Diff = 0.0, Level = 0.0;
    for (int32 Index = FMath::Max(Begin, 1); Index < FMath::Min(End, Samples.Num()); ++Index)
    {
        const double D = Samples[Index] - Samples[Index - 1];
        Diff += D * D;
        Level += static_cast<double>(Samples[Index]) * Samples[Index];
    }
    return Level > 0.0 ? static_cast<float>(FMath::Sqrt(Diff / Level)) : 0.0f;
}

float Peak(const TArray<float>& Samples)
{
    float Max = 0.0f;
    for (const float Sample : Samples)
    {
        Max = FMath::Max(Max, FMath::Abs(Sample));
    }
    return Max;
}
}

bool FRaftSimWaterSynthScenesTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimWaterSynthScenes;
    const FString OutputDir = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("RaftSimValidation"), TEXT("audio"), TEXT("water-synth"));
    TMap<FString, TArray<float>> Rendered;

    // A still pool: the hull rocking gently, a few laps and gurgles.
    {
        FSynthScene Scene{TEXT("still_pool")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 1, 1.0f), 0.8f, 0.04f, 0.15f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 2, 1.0f), 0.8f, 0.04f, 0.15f);
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // A moving current: water running past the tubes.
    {
        FSynthScene Scene{TEXT("moving_current")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 3, 1.0f), 0.8f, 0.45f, 0.3f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 4, 1.0f), 0.8f, 0.45f, 0.3f);
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // A rapid heard from 120 m away, closing to 10 m over 10 s and holding
    // there, over a moving current.
    {
        FSynthScene Scene{TEXT("rapid_approach"), 12.0f};
        AddVoice(Scene, ERaftSimSynthVoiceKind::Whitewater, 5, 1.0f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 6, 1.0f), 0.8f, 0.35f, 0.3f);
        Scene.Script = [](float Time, TArray<FSceneVoice>& Voices)
        {
            const float Alpha = FMath::Clamp(Time / 10.0f, 0.0f, 1.0f);
            const float Distance = FMath::Lerp(120.0f, 10.0f, Alpha);
            // Natural falloff, as the distant emitter's attenuation applies.
            const float Falloff = FMath::Clamp(12.0f / Distance, 0.06f, 1.0f);
            Set(*Voices[0].Voice, Falloff, 0.85f, 0.6f, Distance);
        };
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // Inside the rapid: whitewater all round, the hull heaving, spray.
    {
        FSynthScene Scene{TEXT("inside_rapid")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::Whitewater, 7, 1.0f), 0.9f, 0.9f, 0.7f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::Whitewater, 8, 1.0f), 0.9f, 0.9f, 0.7f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 9, 1.0f), 0.8f, 0.85f, 0.85f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::Spray, 10, 1.0f), 0.7f, 0.7f);
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // Paddle strokes in a calm reach: a catch every 0.8 s.
    {
        FSynthScene Scene{TEXT("paddle_strokes")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 11, 1.0f), 0.8f, 0.2f, 0.25f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::Strokes, 12, 1.0f), 0.8f, 0.0f);
        TSharedRef<float> Next = MakeShared<float>(0.5f);
        Scene.Script = [Next](float Time, TArray<FSceneVoice>& Voices)
        {
            if (Time >= *Next)
            {
                Voices[1].Voice->Trigger(ERaftSimSynthEvent::PaddleCatch, 1.0f);
                *Next += 0.8f;
            }
        };
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // An oar rower: a catch every 1.4 s and the blades lifting out.
    {
        FSynthScene Scene{TEXT("oar_strokes")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 13, 1.0f), 0.8f, 0.2f, 0.25f);
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::Strokes, 14, 1.0f), 0.8f, 0.0f);
        TSharedRef<float> Next = MakeShared<float>(0.5f);
        TSharedRef<float> Release = MakeShared<float>(0.5f + 0.63f);
        Scene.Script = [Next, Release](float Time, TArray<FSceneVoice>& Voices)
        {
            if (Time >= *Next)
            {
                Voices[1].Voice->Trigger(ERaftSimSynthEvent::OarCatch, 1.0f);
                *Next += 1.4f;
            }
            if (Time >= *Release)
            {
                Voices[1].Voice->Trigger(ERaftSimSynthEvent::OarRelease, 1.0f);
                *Release += 1.4f;
            }
        };
        Rendered.Add(Scene.Name, Render(Scene));
    }
    // Hull hits: wave slams, slaps, and a rock scrape building up.
    {
        FSynthScene Scene{TEXT("hull_hits")};
        Set(AddVoice(Scene, ERaftSimSynthVoiceKind::NearWater, 15, 1.0f), 0.8f, 0.4f, 0.5f);
        AddVoice(Scene, ERaftSimSynthVoiceKind::Hull, 16, 1.0f);
        TSharedRef<int32> Fired = MakeShared<int32>(0);
        Scene.Script = [Fired](float Time, TArray<FSceneVoice>& Voices)
        {
            const float Scrape = Time > 5.0f ? FMath::Clamp((Time - 5.0f) / 1.5f, 0.0f, 1.0f) : 0.0f;
            Set(*Voices[1].Voice, 0.9f, Scrape);
            static const float Times[] = {0.6f, 1.9f, 3.1f, 4.0f};
            while (*Fired < 4 && Time >= Times[*Fired])
            {
                Voices[1].Voice->Trigger(
                    *Fired % 2 == 0 ? ERaftSimSynthEvent::HullThump : ERaftSimSynthEvent::HullSlap, 1.0f);
                ++*Fired;
            }
        };
        Rendered.Add(Scene.Name, Render(Scene));
    }

    for (const TPair<FString, TArray<float>>& Scene : Rendered)
    {
        const TArray<float>& Samples = Scene.Value;
        const FString Path = FPaths::Combine(OutputDir, Scene.Key + TEXT(".wav"));
        TestTrue(FString::Printf(TEXT("%s wav written"), *Scene.Key),
            RaftSimSynth::WriteWav16(Path, Samples, SampleRate));
        bool bFinite = true;
        for (const float Sample : Samples)
        {
            bFinite &= FMath::IsFinite(Sample);
        }
        TestTrue(FString::Printf(TEXT("%s is finite"), *Scene.Key), bFinite);
        const float ScenePeak = Peak(Samples);
        const float SceneRms = Rms(Samples, 0, Samples.Num());
        // The former mix replayed the same 2 s buffer: a lag of 2 s (or any
        // other) correlated almost perfectly. Streamed water never repeats.
        const float Repeat = FMath::Max3(
            FMath::Abs(LagCorrelation(Samples, 1.0f, 3.0f, 2.0f)),
            FMath::Abs(LagCorrelation(Samples, 1.0f, 3.0f, 1.0f)),
            FMath::Abs(LagCorrelation(Samples, 1.0f, 3.0f, 0.5f)));
        AddInfo(FString::Printf(TEXT("%s: rms=%.4f peak=%.3f brightness=%.3f repeat=%.3f"),
            *Scene.Key, SceneRms, ScenePeak, Brightness(Samples, 0, Samples.Num()), Repeat));
        TestTrue(FString::Printf(TEXT("%s does not clip (peak %.3f)"), *Scene.Key, ScenePeak), ScenePeak < 0.99f);
        if (!Scene.Key.Contains(TEXT("strokes")))
        {
            TestTrue(FString::Printf(TEXT("%s never repeats (lag correlation %.3f)"), *Scene.Key, Repeat), Repeat < 0.08f);
        }
    }

    const float Pool = Rms(Rendered[TEXT("still_pool")], 0, 8 * SampleRate);
    const float Current = Rms(Rendered[TEXT("moving_current")], 0, 8 * SampleRate);
    const float Rapid = Rms(Rendered[TEXT("inside_rapid")], 0, 8 * SampleRate);
    TestTrue(FString::Printf(TEXT("a still pool is quiet but not silent (rms %.4f)"), Pool), Pool > 0.004f && Pool < 0.06f);
    TestTrue(FString::Printf(TEXT("moving water is louder than a pool (%.4f > %.4f)"), Current, Pool), Current > Pool * 1.6f);
    TestTrue(FString::Printf(TEXT("a rapid is far louder than moving water (%.4f > %.4f)"), Rapid, Current), Rapid > Current * 2.0f);
    TestTrue(FString::Printf(TEXT("inside a rapid is loud, not saturated (rms %.4f)"), Rapid), Rapid > 0.08f && Rapid < 0.45f);

    const TArray<float>& Approach = Rendered[TEXT("rapid_approach")];
    const float FarRms = Rms(Approach, 0, 2 * SampleRate);
    const float NearRms = Rms(Approach, 10 * SampleRate, 12 * SampleRate);
    const float FarBright = Brightness(Approach, 0, 2 * SampleRate);
    const float NearBright = Brightness(Approach, 10 * SampleRate, 12 * SampleRate);
    // Over the steady current under it, a rapid closing from 120 m to 10 m
    // lifts the whole scene by more than 3.5 dB.
    TestTrue(FString::Printf(TEXT("an approaching rapid grows louder (%.4f -> %.4f)"), FarRms, NearRms), NearRms > FarRms * 1.5f);
    TestTrue(FString::Printf(TEXT("a distant rapid is darker than a near one (%.3f < %.3f)"), FarBright, NearBright),
        FarBright < NearBright * 0.85f);

    // Each stroke stands out of the water around it.
    const TArray<float>& Strokes = Rendered[TEXT("paddle_strokes")];
    const float Before = Rms(Strokes, static_cast<int32>(0.1f * SampleRate), static_cast<int32>(0.45f * SampleRate));
    const float Catch = Rms(Strokes, static_cast<int32>(0.5f * SampleRate), static_cast<int32>(0.75f * SampleRate));
    TestTrue(FString::Printf(TEXT("a paddle catch stands out (%.4f vs %.4f)"), Catch, Before), Catch > Before * 1.5f);
    const TArray<float>& Hits = Rendered[TEXT("hull_hits")];
    const float Calm = Rms(Hits, static_cast<int32>(0.1f * SampleRate), static_cast<int32>(0.55f * SampleRate));
    const float Thump = Rms(Hits, static_cast<int32>(0.6f * SampleRate), static_cast<int32>(0.85f * SampleRate));
    TestTrue(FString::Printf(TEXT("a hull thump stands out (%.4f vs %.4f)"), Thump, Calm), Thump > Calm * 1.5f);
    return true;
}

#endif
