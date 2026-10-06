#include "RaftSimWildlifeCalls.h"

namespace RaftSimWildlife
{
namespace
{
constexpr float TwoPi = 6.28318530718f;
constexpr int32 MaxNotes = 48;

struct FBandpass
{
    float B0 = 0.0f, B2 = 0.0f, A1 = 0.0f, A2 = 0.0f, Z1 = 0.0f, Z2 = 0.0f;
    bool bActive = false;
    void Set(float Fc, float Q, float Fs, bool bLowpass = false)
    {
        bActive = Fc > 0.0f;
        if (!bActive)
        {
            return;
        }
        Fc = FMath::Clamp(Fc, 20.0f, 0.45f * Fs);
        const float W0 = TwoPi * Fc / Fs;
        const float CosW = FMath::Cos(W0);
        const float Alpha = FMath::Sin(W0) / (2.0f * FMath::Max(Q, 0.1f));
        const float A0 = 1.0f + Alpha;
        if (bLowpass)
        {
            // Stored as a low-pass: b0 = b2, b1 = 2 b0.
            B0 = (1.0f - CosW) * 0.5f / A0;
            B2 = -1.0f;
        }
        else
        {
            B0 = Alpha / A0;
            B2 = 0.0f;
        }
        A1 = -2.0f * CosW / A0;
        A2 = (1.0f - Alpha) / A0;
    }
    float Process(float X)
    {
        if (!bActive)
        {
            return X;
        }
        float Y;
        if (B2 < 0.0f)
        {
            Y = B0 * X + Z1;
            Z1 = 2.0f * B0 * X - A1 * Y + Z2;
            Z2 = B0 * X - A2 * Y;
        }
        else
        {
            Y = B0 * X + Z1;
            Z1 = -A1 * Y + Z2;
            Z2 = -B0 * X - A2 * Y;
        }
        return Y;
    }
};

struct FActiveNote
{
    FCallNote Note;
    int64 StartSample = 0;
    int32 LengthSamples = 0;
    float Gain = 1.0f;
    double Phase = 0.0;
    double VibratoPhase = 0.0;
    double TremoloPhase = 0.0;
    FBandpass Formant[3];
    FBandpass NoiseLow;
    float Jitter = 0.0f;
    float JitterTarget = 0.0f;
    int32 JitterCountdown = 0;
};

float SoftClip(float X)
{
    X = FMath::Clamp(X, -3.0f, 3.0f);
    return X * (27.0f + X * X) / (27.0f + 9.0f * X * X);
}

/** PolyBLEP sawtooth: a band-limited buzz for voiced animal calls. */
float BlepSaw(double Phase, float Dt)
{
    const float T = static_cast<float>(Phase);
    float Saw = 2.0f * T - 1.0f;
    if (T < Dt)
    {
        const float X = T / Dt;
        Saw -= X + X - X * X - 1.0f;
    }
    else if (T > 1.0f - Dt)
    {
        const float X = (T - 1.0f) / Dt;
        Saw -= X * X + X + X + 1.0f;
    }
    return Saw;
}

float Rand(FRandomStream& R, float Min, float Max)
{
    return R.FRandRange(Min, Max);
}

FCallNote Tone(float Start, float Duration, float F0Start, float F0End, float Amp = 1.0f)
{
    FCallNote Note;
    Note.Start = Start;
    Note.Duration = Duration;
    Note.F0Start = F0Start;
    Note.F0End = F0End;
    Note.Amp = Amp;
    return Note;
}

FCallNote Buzz(float Start, float Duration, float F0Start, float F0End, float F1, float F2, float F3,
    float Noise, float Amp = 1.0f)
{
    FCallNote Note = Tone(Start, Duration, F0Start, F0End, Amp);
    Note.bBuzz = true;
    Note.F1 = F1;
    Note.F2 = F2;
    Note.F3 = F3;
    Note.Noise = Noise;
    return Note;
}
}

TArray<FCallNote> BuildCall(ERaftSimWildlifeCall Call, FRandomStream& R)
{
    // Figures follow docs/river-wildlife-reference.md (published acoustics
    // where they exist, estimates from recordings where not).
    TArray<FCallNote> Notes;
    switch (Call)
    {
        case ERaftSimWildlifeCall::BaldEagle:
        {
            // Not the red-tailed hawk's scream: a weak, thin, high piping,
            // 3-5 kHz. Either the chatter (a few spaced notes, then a quick
            // descending run at ~10 a second) or the peal (gull-like rising
            // notes ending in a voice break).
            float T = 0.0f;
            if (R.FRand() < 0.65f)
            {
                const int32 Intro = R.RandRange(3, 4);
                for (int32 Index = 0; Index < Intro; ++Index)
                {
                    FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.08f, 0.1f), Rand(R, 3300.0f, 3500.0f), Rand(R, 3600.0f, 3800.0f), 0.8f));
                    Note.H2 = 0.1f;
                    T += Rand(R, 0.35f, 0.7f);
                }
                const int32 Run = R.RandRange(6, 9);
                for (int32 Index = 0; Index < Run; ++Index)
                {
                    const float Pitch = FMath::Lerp(4600.0f, 3200.0f, Index / static_cast<float>(Run));
                    FCallNote& Note = Notes.Add_GetRef(Tone(T, 0.06f, Pitch * 1.03f, Pitch * 0.95f, 0.9f));
                    Note.H2 = 0.1f;
                    Note.Attack = 0.005f;
                    Note.Release = 0.02f;
                    T += Rand(R, 0.085f, 0.11f);
                }
            }
            else
            {
                const int32 Count = R.RandRange(3, 5);
                for (int32 Index = 0; Index < Count; ++Index)
                {
                    FCallNote& Note = Notes.Add_GetRef(Tone(T, Index == Count - 1 ? 0.3f : 0.5f, Rand(R, 2900.0f, 3100.0f), Rand(R, 3300.0f, 3500.0f)));
                    Note.H2 = 0.25f;
                    T += Index == Count - 1 ? 0.3f : 0.65f;
                }
                FCallNote& Break = Notes.Add_GetRef(Tone(T, 0.2f, 2700.0f, 2500.0f, 0.8f));
                Break.H2 = 0.3f;
            }
            break;
        }
        case ERaftSimWildlifeCall::Osprey:
        {
            // Short clear whistles, "cheep" or "yewk", 2-4 a second, the run
            // rising then falling.
            const int32 Count = R.RandRange(5, 10);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float Arc = FMath::Sin(PI * Index / FMath::Max(Count - 1, 1));
                const float Pitch = 2300.0f + 1300.0f * Arc;
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.1f, 0.18f), Pitch * 0.92f, Pitch, 0.6f + 0.4f * Arc));
                Note.H2 = 0.15f;
                Note.Curve = 0.7f;
                T += Rand(R, 0.27f, 0.4f);
            }
            break;
        }
        case ERaftSimWildlifeCall::CanyonWren:
        {
            // The canyon's signature: 2.7-3.2 s of clear downslurred whistles
            // stepping from 5-6 kHz down to ~2 kHz, quickening, then a few
            // harsher notes.
            const int32 Count = R.RandRange(12, 18);
            float T = 0.0f;
            float Pitch = Rand(R, 5000.0f, 6000.0f);
            const float Step = FMath::Pow(Rand(R, 1900.0f, 2200.0f) / Pitch, 1.0f / (Count - 1));
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.05f, 0.09f), Pitch * 1.06f, Pitch * 0.88f));
                Note.Attack = 0.006f;
                Note.Release = 0.02f;
                const float Progress = Index / static_cast<float>(Count);
                T += FMath::Lerp(0.24f, 0.12f, Progress);
                Pitch *= Step;
            }
            const int32 Harsh = R.RandRange(2, 4);
            for (int32 Index = 0; Index < Harsh; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Buzz(T + 0.1f, 0.12f, 1900.0f, 1700.0f, 2500.0f, 4200.0f, 0.0f, 0.4f, 0.6f));
                Note.TremoloHz = 70.0f;
                Note.TremoloDepth = 0.5f;
                T += 0.17f;
            }
            break;
        }
        case ERaftSimWildlifeCall::CommonRaven:
        {
            // Deep, rough croaks in runs of 2-5 (F0 ~450-650 Hz, harmonics to
            // ~4 kHz), and now and then a hollow knock.
            const int32 Count = R.RandRange(2, 5);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float F0 = Rand(R, 420.0f, 650.0f);
                FCallNote& Note = Notes.Add_GetRef(Buzz(T, Rand(R, 0.2f, 0.45f), F0 * 1.08f, F0 * 0.85f,
                    Rand(R, 850.0f, 1000.0f), Rand(R, 1700.0f, 1900.0f), 3000.0f, 0.25f));
                Note.Jitter = 0.05f;
                Note.Attack = 0.025f;
                Note.Release = 0.08f;
                T += Note.Duration + Rand(R, 0.25f, 0.5f);
            }
            if (R.FRand() < 0.3f)
            {
                FCallNote& Knock = Notes.Add_GetRef(Tone(T, 0.05f, 1100.0f, 950.0f, 0.7f));
                Knock.H2 = 0.5f;
                Knock.Attack = 0.002f;
            }
            break;
        }
        case ERaftSimWildlifeCall::GreatBlueHeron:
        {
            // One to four hoarse, broadband "fraaank"s.
            const int32 Count = R.RandRange(1, 4);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Buzz(T, Rand(R, 0.3f, 0.8f), Rand(R, 150.0f, 180.0f), 115.0f,
                    500.0f, 1100.0f, 1500.0f, 0.55f));
                Note.FormantQ = 3.0f;
                Note.Jitter = 0.06f;
                Note.Attack = 0.04f;
                Note.Release = 0.2f;
                T += Note.Duration + Rand(R, 0.3f, 0.6f);
            }
            break;
        }
        case ERaftSimWildlifeCall::BeltedKingfisher:
        {
            // A long, dry, mechanical rattle along the river.
            FCallNote& Note = Notes.Add_GetRef(Buzz(0.0f, Rand(R, 1.0f, 1.6f), 2400.0f, 2200.0f, 3000.0f, 4500.0f, 0.0f, 0.7f, 0.8f));
            Note.FormantQ = 3.0f;
            Note.TremoloHz = Rand(R, 16.0f, 20.0f);
            Note.TremoloDepth = 0.95f;
            break;
        }
        case ERaftSimWildlifeCall::RingedKingfisher:
        {
            // A lower, slower rattle (8-12 clicks a second, 2-5 kHz) with a
            // "klek" or two; it cuts through the rapids.
            float T = 0.0f;
            const int32 Kleks = R.RandRange(0, 2);
            for (int32 Index = 0; Index < Kleks; ++Index)
            {
                FCallNote& Klek = Notes.Add_GetRef(Tone(T, 0.06f, 3000.0f, 2700.0f, 0.8f));
                Klek.H2 = 0.4f;
                T += 0.25f;
            }
            FCallNote& Rattle = Notes.Add_GetRef(Buzz(T, Rand(R, 1.0f, 2.6f), 2600.0f, 2300.0f, 3200.0f, 4600.0f, 0.0f, 0.6f));
            Rattle.FormantQ = 3.0f;
            Rattle.TremoloHz = Rand(R, 8.0f, 12.0f);
            Rattle.TremoloDepth = 0.95f;
            break;
        }
        case ERaftSimWildlifeCall::MantledHowler:
        {
            // Grunting barks, then roars: each about 2.2 s of ~6 syllables
            // alternating out- and in-breath, rough (HNR ~8 dB), F0 112 Hz,
            // formants from 413 Hz spaced 624 Hz apart, loudest 73 % through
            // (Bergman et al. 2016). Carries over 2 km.
            float T = 0.0f;
            const int32 Barks = R.RandRange(2, 4);
            for (int32 Index = 0; Index < Barks; ++Index)
            {
                FCallNote& Bark = Notes.Add_GetRef(Buzz(T, 0.15f, 100.0f, 130.0f, 413.0f, 1037.0f, 1661.0f, 0.5f, 0.5f));
                Bark.FormantQ = 4.0f;
                Bark.Jitter = 0.08f;
                T += Rand(R, 0.35f, 0.6f);
            }
            const int32 Roars = R.RandRange(1, 2);
            for (int32 Roar = 0; Roar < Roars; ++Roar)
            {
                const float Length = Rand(R, 1.9f, 2.5f);
                constexpr int32 Syllables = 6;
                for (int32 Index = 0; Index < Syllables; ++Index)
                {
                    const float Where = Index / static_cast<float>(Syllables - 1);
                    const float Swell = 0.35f + 0.65f * FMath::Max(0.0f, 1.0f - FMath::Abs(Where - 0.73f) / 0.73f);
                    const bool bOut = Index % 2 == 0;
                    const float F0 = (bOut ? 112.0f : 96.0f) * Rand(R, 0.92f, 1.08f);
                    FCallNote& Syllable = Notes.Add_GetRef(Buzz(T + Index * Length / Syllables, Length / Syllables * 1.1f,
                        F0, F0 * 0.95f, 413.0f, 1037.0f, 1661.0f, bOut ? 0.35f : 0.55f, Swell * (bOut ? 1.0f : 0.6f)));
                    Syllable.FormantQ = 4.0f;
                    Syllable.Jitter = 0.08f;
                    Syllable.Attack = 0.05f;
                    Syllable.Release = 0.07f;
                }
                T += Length + Rand(R, 0.8f, 2.0f);
            }
            break;
        }
        case ERaftSimWildlifeCall::KeelBilledToucan:
        {
            // Frog-like "krrrk"s, steadily repeated about once a second:
            // 0.2-0.4 s trains of 30-50 pulses a second, 0.5-2 kHz.
            const int32 Count = R.RandRange(4, 10);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Buzz(Index * Rand(R, 0.85f, 1.15f), Rand(R, 0.2f, 0.4f), Rand(R, 550.0f, 700.0f), 520.0f,
                    900.0f, 1600.0f, 0.0f, 0.15f, 0.8f));
                Note.TremoloHz = Rand(R, 30.0f, 50.0f);
                Note.TremoloDepth = 0.9f;
            }
            break;
        }
        case ERaftSimWildlifeCall::MontezumaOropendola:
        {
            // Quiet bubbly notes rising 250-900 Hz, an overtone-rich upslur
            // climbing past 8 kHz, then the loud, long downslurred note.
            float T = 0.0f;
            const int32 Bubbles = R.RandRange(3, 5);
            for (int32 Index = 0; Index < Bubbles; ++Index)
            {
                const float Pitch = FMath::Lerp(250.0f, 900.0f, Index / static_cast<float>(Bubbles - 1));
                FCallNote& Bubble = Notes.Add_GetRef(Tone(T, 0.06f, Pitch * 0.9f, Pitch * 1.2f, 0.35f));
                Bubble.H2 = 0.3f;
                T += 0.09f;
            }
            FCallNote& Rise = Notes.Add_GetRef(Tone(T, 0.16f, 1500.0f, Rand(R, 7800.0f, 8800.0f), 0.6f));
            Rise.H2 = 0.3f;
            Rise.Curve = 0.8f;
            T += 0.2f;
            FCallNote& Fall = Notes.Add_GetRef(Tone(T, Rand(R, 0.5f, 0.75f), Rand(R, 2000.0f, 2400.0f), Rand(R, 550.0f, 700.0f)));
            Fall.H2 = 0.35f;
            Fall.H3 = 0.12f;
            Fall.Curve = 0.7f;
            Fall.Release = 0.15f;
            break;
        }
        case ERaftSimWildlifeCall::TorrentDuck:
        {
            // The male's clear "wheet", rising 3.5-4.5 kHz, every 1-3 s: it
            // carries over rapids noise, which sits below 1.5 kHz.
            float T = 0.0f;
            const int32 Count = R.RandRange(2, 4);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.2f, 0.4f), Rand(R, 3400.0f, 3600.0f), Rand(R, 4300.0f, 4600.0f)));
                Note.Curve = 0.6f;
                Note.H2 = 0.1f;
                T += Rand(R, 1.0f, 2.5f);
            }
            break;
        }
        case ERaftSimWildlifeCall::AfricanFishEagle:
        {
            // "Weee-ah, kyow-kyow-kyow" with the head thrown back, as a duet:
            // the partner answers 0.2-0.5 s later, 10-20 % lower.
            auto Phrase = [&R, &Notes](float Start, float Pitch, float Amp)
            {
                FCallNote& Up = Notes.Add_GetRef(Tone(Start, 0.35f, 1600.0f * Pitch, 2200.0f * Pitch, Amp));
                Up.Curve = 0.5f;
                Notes.Add(Tone(Start + 0.35f, 0.4f, 2200.0f * Pitch, 1400.0f * Pitch, Amp));
                float T = Start + 0.95f;
                const int32 Kyows = R.RandRange(3, 5);
                for (int32 Index = 0; Index < Kyows; ++Index)
                {
                    Notes.Add(Tone(T, 0.17f, 1750.0f * Pitch, 1250.0f * Pitch, Amp * 0.85f));
                    T += 0.25f;
                }
            };
            Phrase(0.0f, 1.0f, 1.0f);
            if (R.FRand() < 0.7f)
            {
                Phrase(Rand(R, 0.2f, 0.5f), Rand(R, 0.8f, 0.9f), 0.8f);
            }
            for (FCallNote& Note : Notes)
            {
                Note.H2 = 0.35f;
                Note.H3 = 0.15f;
                Note.VibratoHz = 12.0f;
                Note.VibratoDepth = 0.02f;
            }
            break;
        }
        case ERaftSimWildlifeCall::Hippo:
        {
            // A wheezing in-breath, then a run of deep resonant honks.
            FCallNote& Wheeze = Notes.Add_GetRef(Tone(0.0f, 0.5f, 100.0f, 100.0f, 0.5f));
            Wheeze.Noise = 1.0f;
            Wheeze.NoiseLowpass = 1200.0f;
            Wheeze.Attack = 0.15f;
            Wheeze.Release = 0.1f;
            float T = 0.55f;
            const int32 Honks = R.RandRange(4, 7);
            for (int32 Index = 0; Index < Honks; ++Index)
            {
                const float F0 = Rand(R, 85.0f, 110.0f);
                FCallNote& Honk = Notes.Add_GetRef(Buzz(T, Rand(R, 0.35f, 0.5f), F0, F0 * 0.8f, 280.0f, 700.0f, 1500.0f, 0.25f,
                    0.6f + 0.4f * Index / Honks));
                Honk.FormantQ = 3.0f;
                Honk.Jitter = 0.05f;
                Honk.Attack = 0.04f;
                Honk.Release = 0.12f;
                T += Rand(R, 0.45f, 0.6f);
            }
            break;
        }
        case ERaftSimWildlifeCall::ChacmaBaboon:
        {
            // The "wa-hoo": a loud "wa" bark (F0 ~300-330 Hz, 320-470 ms,
            // peak energy ~740 Hz), a short gap, and a quieter "hoo"
            // (116-214 ms) that is sometimes dropped (Fischer et al. 2002).
            const int32 Count = R.RandRange(1, 3);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float F0 = Rand(R, 295.0f, 330.0f);
                FCallNote& Wa = Notes.Add_GetRef(Buzz(T, Rand(R, 0.32f, 0.47f), F0 * 0.95f, F0 * 1.05f, 740.0f, 1300.0f, 2500.0f, 0.25f));
                Wa.Curve = 0.5f;
                Wa.Jitter = 0.03f;
                Wa.Release = 0.06f;
                if (R.FRand() < 0.7f)
                {
                    FCallNote& Hoo = Notes.Add_GetRef(Buzz(T + Wa.Duration + 0.05f, Rand(R, 0.12f, 0.21f), F0 * 0.85f, F0 * 0.7f,
                        650.0f, 1100.0f, 2300.0f, 0.2f, 0.6f));
                    Hoo.Release = 0.08f;
                }
                T += Rand(R, 1.5f, 2.5f);
            }
            break;
        }
        case ERaftSimWildlifeCall::Cicadas:
        {
            // A long, pulsing buzz that swells and fades: 3-7 kHz.
            FCallNote& Note = Notes.Add_GetRef(Tone(0.0f, Rand(R, 4.0f, 9.0f), 100.0f, 100.0f, 0.5f));
            Note.Noise = 1.0f;
            Note.F1 = Rand(R, 3200.0f, 6400.0f);
            Note.F2 = Note.F1 * 1.35f;
            Note.FormantQ = 6.0f;
            Note.TremoloHz = Rand(R, 100.0f, 160.0f);
            Note.TremoloDepth = 0.8f;
            Note.Attack = 0.8f;
            Note.Release = 1.2f;
            break;
        }
        case ERaftSimWildlifeCall::TrumpeterHornbill:
        {
            // "Nhaa nhaa ha-ha-ha": a loud nasal wail like a crying baby,
            // F0 0.6-1.2 kHz, notes 0.3-0.8 s in series of 3-8.
            const int32 Count = R.RandRange(3, 8);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const bool bLong = Index < 2;
                const float F0 = Rand(R, 650.0f, 900.0f);
                FCallNote& Note = Notes.Add_GetRef(Buzz(T, bLong ? Rand(R, 0.55f, 0.8f) : Rand(R, 0.3f, 0.4f), F0, F0 * 0.82f,
                    1100.0f, 2400.0f, 3400.0f, 0.08f));
                Note.FormantQ = 5.0f;
                Note.VibratoHz = 6.0f;
                Note.VibratoDepth = 0.03f;
                Note.Release = 0.12f;
                T += Note.Duration + Rand(R, 0.12f, 0.25f);
            }
            break;
        }
        case ERaftSimWildlifeCall::AmericanDipper:
        {
            // A loud, varied song of whistles and trills, sung over white water.
            float T = 0.0f;
            const int32 Count = R.RandRange(8, 14);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float Pitch = Rand(R, 2500.0f, 5000.0f);
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.05f, 0.12f), Pitch, Pitch * Rand(R, 0.8f, 1.2f), 0.8f));
                if (R.FRand() < 0.3f)
                {
                    Note.TremoloHz = 30.0f;
                    Note.TremoloDepth = 0.7f;
                    Note.Duration = 0.25f;
                }
                T += Note.Duration + Rand(R, 0.03f, 0.08f);
            }
            break;
        }
        case ERaftSimWildlifeCall::Chucao:
        {
            // Soft churrs bracketing 4-5 loud, clear, higher notes:
            // "chuu, chu-chu-chu-caou", 1.5-2.5 s.
            auto Churr = [&Notes](float Start)
            {
                FCallNote& Note = Notes.Add_GetRef(Buzz(Start, 0.3f, 320.0f, 300.0f, 900.0f, 1800.0f, 0.0f, 0.3f, 0.35f));
                Note.TremoloHz = 25.0f;
                Note.TremoloDepth = 0.8f;
            };
            Churr(0.0f);
            float T = 0.4f;
            const int32 Count = R.RandRange(3, 4);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Index == 0 ? 0.2f : 0.11f, Rand(R, 2100.0f, 2400.0f), 2000.0f));
                Note.H2 = 0.3f;
                T += Index == 0 ? 0.3f : 0.19f;
            }
            FCallNote& Caou = Notes.Add_GetRef(Tone(T, 0.32f, 2500.0f, 1400.0f));
            Caou.H2 = 0.35f;
            Caou.Curve = 1.3f;
            Churr(T + 0.45f);
            break;
        }
        case ERaftSimWildlifeCall::AustralParakeet:
        {
            // A flock's nasal, grating "grrreh"s.
            const int32 Count = R.RandRange(4, 9);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Buzz(Index * Rand(R, 0.15f, 0.3f), Rand(R, 0.1f, 0.2f), Rand(R, 1100.0f, 1400.0f),
                    Rand(R, 1000.0f, 1300.0f), 2500.0f, 4000.0f, 0.0f, 0.3f, 0.7f));
                Note.TremoloHz = 30.0f;
                Note.TremoloDepth = 0.5f;
            }
            break;
        }
        case ERaftSimWildlifeCall::RedShoulderedHawk:
        {
            // "Kee-aah", repeated 5-12 times about once a second: a short
            // rise then a long downslur, ~1.5-3 kHz.
            const int32 Count = R.RandRange(5, 12);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float T = Index * Rand(R, 0.85f, 1.1f);
                FCallNote& Kee = Notes.Add_GetRef(Tone(T, 0.08f, 2400.0f, 3000.0f, 0.8f));
                Kee.H2 = 0.3f;
                FCallNote& Aah = Notes.Add_GetRef(Tone(T + 0.08f, Rand(R, 0.25f, 0.4f), 3000.0f, 1700.0f));
                Aah.H2 = 0.3f;
                Aah.Curve = 1.3f;
            }
            break;
        }
        case ERaftSimWildlifeCall::AcornWoodpecker:
        {
            // A family's nasal "waka-waka" bursts, overlapping.
            for (int32 Bird = 0; Bird < R.RandRange(1, 3); ++Bird)
            {
                float T = Bird * Rand(R, 0.3f, 0.6f);
                const float F0 = Rand(R, 650.0f, 800.0f);
                const int32 Units = R.RandRange(3, 6);
                for (int32 Index = 0; Index < Units; ++Index)
                {
                    Notes.Add(Buzz(T, 0.06f, F0 * 1.15f, F0 * 1.1f, 1300.0f, 2400.0f, 0.0f, 0.1f, 0.7f));
                    Notes.Add(Buzz(T + 0.065f, 0.06f, F0, F0 * 0.9f, 1200.0f, 2200.0f, 0.0f, 0.1f, 0.7f));
                    T += 0.17f;
                }
            }
            break;
        }
        case ERaftSimWildlifeCall::Sunbittern:
        {
            // A long, high, thin "wuuuu" whistle, often given twice.
            const int32 Count = R.RandRange(1, 2);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float Pitch = Rand(R, 1800.0f, 2500.0f);
                FCallNote& Note = Notes.Add_GetRef(Tone(Index * 2.6f, Rand(R, 1.5f, 2.3f), Pitch, Pitch * Rand(R, 1.0f, 1.08f), 0.8f));
                Note.VibratoHz = 5.0f;
                Note.VibratoDepth = 0.01f;
                Note.Attack = 0.15f;
                Note.Release = 0.3f;
            }
            break;
        }
        case ERaftSimWildlifeCall::BlackFacedIbis:
        {
            // Loud, metallic trumpeting honks, 2-6 at 2-4 a second, often
            // from two birds at once.
            for (int32 Bird = 0; Bird < R.RandRange(1, 2); ++Bird)
            {
                float T = Bird * Rand(R, 0.1f, 0.3f);
                const float F0 = Rand(R, 850.0f, 1300.0f);
                const int32 Count = R.RandRange(2, 6);
                for (int32 Index = 0; Index < Count; ++Index)
                {
                    FCallNote& Note = Notes.Add_GetRef(Buzz(T, Rand(R, 0.15f, 0.3f), F0, F0 * 0.92f, 1700.0f, 3100.0f, 4300.0f, 0.1f, 0.8f));
                    Note.FormantQ = 7.0f;
                    T += Rand(R, 0.25f, 0.45f);
                }
            }
            break;
        }
        case ERaftSimWildlifeCall::SouthernLapwing:
        {
            // A strident "keh-keh-keh" run, 4-8 notes a second, escalating.
            const int32 Count = R.RandRange(6, 14);
            float T = 0.0f;
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float Pitch = Rand(R, 2200.0f, 2800.0f) * (1.0f + 0.1f * Index / Count);
                FCallNote& Note = Notes.Add_GetRef(Tone(T, Rand(R, 0.08f, 0.14f), Pitch, Pitch * 0.9f, 0.6f + 0.4f * Index / Count));
                Note.H2 = 0.5f;
                Note.H3 = 0.3f;
                Note.Attack = 0.008f;
                T += Rand(R, 0.13f, 0.22f);
            }
            break;
        }
        case ERaftSimWildlifeCall::RockPratincole:
        {
            // Thin "kek" notes at 5-8 a second, 3-5 kHz: high enough to
            // carry over the rapids.
            const int32 Count = R.RandRange(4, 10);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                FCallNote& Note = Notes.Add_GetRef(Tone(Index * Rand(R, 0.13f, 0.19f), Rand(R, 0.04f, 0.08f), Rand(R, 3700.0f, 4500.0f),
                    Rand(R, 3200.0f, 3800.0f), 0.7f));
                Note.H2 = 0.2f;
                Note.Attack = 0.005f;
            }
            break;
        }
        case ERaftSimWildlifeCall::RedWingedStarling:
        {
            // The gorge walls' whistled "cher-leeeoo", from a flock.
            for (int32 Bird = 0; Bird < R.RandRange(1, 3); ++Bird)
            {
                const float T = Bird * Rand(R, 0.4f, 1.2f);
                FCallNote& Cher = Notes.Add_GetRef(Tone(T, 0.12f, Rand(R, 2100.0f, 2300.0f), 2600.0f, 0.7f));
                Cher.H2 = 0.15f;
                FCallNote& Leeoo = Notes.Add_GetRef(Tone(T + 0.15f, Rand(R, 0.45f, 0.6f), Rand(R, 3100.0f, 3400.0f), Rand(R, 1700.0f, 1900.0f)));
                Leeoo.H2 = 0.15f;
                Leeoo.Curve = 1.4f;
            }
            break;
        }
        case ERaftSimWildlifeCall::SalmonSplash:
        {
            // A leap: the burst as the fish breaks the surface, and the
            // slap as it falls back.
            FCallNote& Out = Notes.Add_GetRef(Tone(0.0f, Rand(R, 0.15f, 0.3f), 100.0f, 100.0f, 0.8f));
            Out.Noise = 1.0f;
            Out.NoiseLowpass = 6000.0f;
            Out.Attack = 0.004f;
            Out.Release = 0.15f;
            FCallNote& Back = Notes.Add_GetRef(Tone(0.7f, Rand(R, 0.1f, 0.2f), 100.0f, 100.0f, 1.0f));
            Back.Noise = 1.0f;
            Back.NoiseLowpass = 3500.0f;
            Back.Attack = 0.003f;
            Back.Release = 0.1f;
            break;
        }
        case ERaftSimWildlifeCall::BighornClash:
        {
            // Rams' horns meeting: a sharp crack and its echoes off the walls.
            const int32 Clashes = R.RandRange(1, 2);
            for (int32 Index = 0; Index < Clashes; ++Index)
            {
                const float T = Index * Rand(R, 0.9f, 1.5f);
                const float Echoes[3][2] = {{0.0f, 1.0f}, {0.28f, 0.45f}, {0.65f, 0.22f}};
                for (const auto& Echo : Echoes)
                {
                    FCallNote& Crack = Notes.Add_GetRef(Tone(T + Echo[0], 0.03f, 100.0f, 100.0f, Echo[1]));
                    Crack.Noise = 1.0f;
                    Crack.NoiseLowpass = Echo[0] > 0.0f ? 2500.0f : 0.0f;
                    Crack.Attack = 0.001f;
                    Crack.Release = 0.025f;
                }
            }
            break;
        }
        case ERaftSimWildlifeCall::None:
        default:
            break;
    }
    return Notes;
}

float NextCallInterval(ERaftSimWildlifeCall Call, FRandomStream& R)
{
    switch (Call)
    {
        case ERaftSimWildlifeCall::BaldEagle: return Rand(R, 25.0f, 70.0f);
        case ERaftSimWildlifeCall::Osprey: return Rand(R, 12.0f, 35.0f);
        case ERaftSimWildlifeCall::CanyonWren: return Rand(R, 18.0f, 40.0f);
        case ERaftSimWildlifeCall::CommonRaven: return Rand(R, 10.0f, 30.0f);
        case ERaftSimWildlifeCall::GreatBlueHeron: return Rand(R, 40.0f, 120.0f);
        case ERaftSimWildlifeCall::BeltedKingfisher: return Rand(R, 15.0f, 45.0f);
        case ERaftSimWildlifeCall::RingedKingfisher: return Rand(R, 15.0f, 45.0f);
        case ERaftSimWildlifeCall::MantledHowler: return Rand(R, 20.0f, 45.0f);
        case ERaftSimWildlifeCall::KeelBilledToucan: return Rand(R, 8.0f, 25.0f);
        case ERaftSimWildlifeCall::MontezumaOropendola: return Rand(R, 5.0f, 18.0f);
        case ERaftSimWildlifeCall::TorrentDuck: return Rand(R, 10.0f, 30.0f);
        case ERaftSimWildlifeCall::AfricanFishEagle: return Rand(R, 25.0f, 70.0f);
        case ERaftSimWildlifeCall::Hippo: return Rand(R, 20.0f, 60.0f);
        case ERaftSimWildlifeCall::ChacmaBaboon: return Rand(R, 15.0f, 50.0f);
        case ERaftSimWildlifeCall::Cicadas: return Rand(R, 3.0f, 8.0f);
        case ERaftSimWildlifeCall::TrumpeterHornbill: return Rand(R, 15.0f, 40.0f);
        case ERaftSimWildlifeCall::AmericanDipper: return Rand(R, 10.0f, 25.0f);
        case ERaftSimWildlifeCall::Chucao: return Rand(R, 10.0f, 30.0f);
        case ERaftSimWildlifeCall::AustralParakeet: return Rand(R, 8.0f, 20.0f);
        case ERaftSimWildlifeCall::RedShoulderedHawk: return Rand(R, 20.0f, 60.0f);
        case ERaftSimWildlifeCall::AcornWoodpecker: return Rand(R, 8.0f, 25.0f);
        case ERaftSimWildlifeCall::Sunbittern: return Rand(R, 30.0f, 90.0f);
        case ERaftSimWildlifeCall::BlackFacedIbis: return Rand(R, 12.0f, 35.0f);
        case ERaftSimWildlifeCall::SouthernLapwing: return Rand(R, 10.0f, 30.0f);
        case ERaftSimWildlifeCall::RockPratincole: return Rand(R, 10.0f, 30.0f);
        case ERaftSimWildlifeCall::RedWingedStarling: return Rand(R, 8.0f, 25.0f);
        case ERaftSimWildlifeCall::BighornClash: return Rand(R, 30.0f, 120.0f);
        default: return 60.0f;
    }
}

void GetCallRange(ERaftSimWildlifeCall Call, float& InnerMeters, float& FalloffMeters)
{
    switch (Call)
    {
        case ERaftSimWildlifeCall::MantledHowler: InnerMeters = 150.0f; FalloffMeters = 2000.0f; break;
        case ERaftSimWildlifeCall::BighornClash: InnerMeters = 100.0f; FalloffMeters = 1600.0f; break;
        case ERaftSimWildlifeCall::ChacmaBaboon: InnerMeters = 60.0f; FalloffMeters = 1000.0f; break;
        case ERaftSimWildlifeCall::RedShoulderedHawk: InnerMeters = 40.0f; FalloffMeters = 1000.0f; break;
        case ERaftSimWildlifeCall::AfricanFishEagle:
        case ERaftSimWildlifeCall::BlackFacedIbis: InnerMeters = 60.0f; FalloffMeters = 900.0f; break;
        case ERaftSimWildlifeCall::KeelBilledToucan: InnerMeters = 40.0f; FalloffMeters = 800.0f; break;
        case ERaftSimWildlifeCall::Hippo: InnerMeters = 80.0f; FalloffMeters = 800.0f; break;
        case ERaftSimWildlifeCall::SouthernLapwing:
        case ERaftSimWildlifeCall::RedWingedStarling: InnerMeters = 40.0f; FalloffMeters = 600.0f; break;
        case ERaftSimWildlifeCall::TrumpeterHornbill:
        case ERaftSimWildlifeCall::RingedKingfisher: InnerMeters = 35.0f; FalloffMeters = 500.0f; break;
        case ERaftSimWildlifeCall::Osprey:
        case ERaftSimWildlifeCall::CommonRaven:
        case ERaftSimWildlifeCall::MontezumaOropendola:
        case ERaftSimWildlifeCall::Sunbittern:
        case ERaftSimWildlifeCall::Chucao: InnerMeters = 35.0f; FalloffMeters = 400.0f; break;
        case ERaftSimWildlifeCall::BaldEagle: InnerMeters = 30.0f; FalloffMeters = 350.0f; break;
        case ERaftSimWildlifeCall::Cicadas: InnerMeters = 15.0f; FalloffMeters = 150.0f; break;
        case ERaftSimWildlifeCall::SalmonSplash: InnerMeters = 10.0f; FalloffMeters = 120.0f; break;
        default: InnerMeters = 25.0f; FalloffMeters = 260.0f; break;
    }
}

struct FCallVoice::FState
{
    explicit FState(uint32 Seed) : Noise(Seed ? Seed : 0x1234567u) {}
    TArray<FActiveNote> Notes;
    int64 Sample = 0;
    uint32 Noise;
    float NextWhite()
    {
        Noise ^= Noise << 13;
        Noise ^= Noise >> 17;
        Noise ^= Noise << 5;
        return static_cast<float>(Noise >> 8) * (2.0f / 16777216.0f) - 1.0f;
    }
};

FCallVoice::FCallVoice(uint32 Seed, float InSampleRate)
    : SampleRate(InSampleRate), State(MakeUnique<FState>(Seed * 2654435761u + 7u))
{
    State->Notes.Reserve(MaxNotes);
}

FCallVoice::~FCallVoice() = default;

void FCallVoice::Play(TArray<FCallNote>&& Notes, float Gain)
{
    if (!Notes.IsEmpty())
    {
        ActiveNotes.fetch_add(Notes.Num());
        Pending.Enqueue(TPair<TArray<FCallNote>, float>(MoveTemp(Notes), Gain));
    }
}

void FCallVoice::Render(float* Out, int32 NumFrames)
{
    FState& S = *State;
    const float Fs = SampleRate;
    TPair<TArray<FCallNote>, float> Call;
    while (Pending.Dequeue(Call))
    {
        for (const FCallNote& Note : Call.Key)
        {
            if (S.Notes.Num() >= MaxNotes)
            {
                ActiveNotes.fetch_sub(1);
                continue;
            }
            FActiveNote& Active = S.Notes.AddDefaulted_GetRef();
            Active.Note = Note;
            Active.StartSample = S.Sample + static_cast<int64>(Note.Start * Fs);
            Active.LengthSamples = FMath::Max(1, static_cast<int32>(Note.Duration * Fs));
            Active.Gain = Call.Value;
            for (int32 Index = 0; Index < 3; ++Index)
            {
                const float Frequency = Index == 0 ? Note.F1 : (Index == 1 ? Note.F2 : Note.F3);
                Active.Formant[Index].Set(Frequency, Note.FormantQ, Fs);
            }
            Active.NoiseLow.Set(Note.NoiseLowpass, 0.707f, Fs, true);
        }
    }
    FMemory::Memzero(Out, sizeof(float) * NumFrames);
    if (S.Notes.IsEmpty())
    {
        S.Sample += NumFrames;
        return;
    }
    for (int32 Frame = 0; Frame < NumFrames; ++Frame)
    {
        float Sum = 0.0f;
        for (int32 Index = 0; Index < S.Notes.Num(); ++Index)
        {
            FActiveNote& A = S.Notes[Index];
            const int64 Age = S.Sample + Frame - A.StartSample;
            if (Age < 0)
            {
                continue;
            }
            if (Age >= A.LengthSamples)
            {
                S.Notes.RemoveAtSwap(Index, EAllowShrinking::No);
                ActiveNotes.fetch_sub(1);
                --Index;
                continue;
            }
            const FCallNote& N = A.Note;
            const float T = static_cast<float>(Age) / Fs;
            const float Progress = static_cast<float>(Age) / static_cast<float>(A.LengthSamples);
            float F0 = N.F0Start + (N.F0End - N.F0Start) * FMath::Pow(Progress, FMath::Max(N.Curve, 0.05f));
            if (N.VibratoHz > 0.0f)
            {
                A.VibratoPhase = FMath::Fmod(A.VibratoPhase + N.VibratoHz / Fs, 1.0);
                F0 *= 1.0f + N.VibratoDepth * FMath::Sin(TwoPi * static_cast<float>(A.VibratoPhase));
            }
            if (N.Jitter > 0.0f)
            {
                // Rough voices wander a little in pitch, every few ms.
                if (--A.JitterCountdown <= 0)
                {
                    A.JitterCountdown = static_cast<int32>(Fs * 0.004f);
                    A.JitterTarget = S.NextWhite() * N.Jitter;
                }
                A.Jitter += (A.JitterTarget - A.Jitter) * 0.01f;
                F0 *= 1.0f + A.Jitter;
            }
            const float Dt = FMath::Clamp(F0 / Fs, 0.0f, 0.45f);
            A.Phase += Dt;
            A.Phase -= FMath::FloorToDouble(A.Phase);
            float Source;
            if (N.bBuzz)
            {
                Source = BlepSaw(A.Phase, FMath::Max(Dt, 1.0e-5f));
            }
            else
            {
                const float P = TwoPi * static_cast<float>(A.Phase);
                Source = FMath::Sin(P);
                if (N.H2 > 0.0f) Source += N.H2 * FMath::Sin(2.0f * P);
                if (N.H3 > 0.0f) Source += N.H3 * FMath::Sin(3.0f * P);
                if (N.H4 > 0.0f) Source += N.H4 * FMath::Sin(4.0f * P);
            }
            float Signal = Source * (1.0f - N.Noise);
            if (N.Noise > 0.0f)
            {
                Signal += A.NoiseLow.Process(S.NextWhite()) * N.Noise;
            }
            if (A.Formant[0].bActive)
            {
                // Vocal-tract resonances shape the buzz into a voice.
                float Shaped = A.Formant[0].Process(Signal);
                if (A.Formant[1].bActive) Shaped += 0.7f * A.Formant[1].Process(Signal);
                if (A.Formant[2].bActive) Shaped += 0.4f * A.Formant[2].Process(Signal);
                Signal = Shaped * 2.2f;
            }
            float Envelope = 1.0f;
            if (T < N.Attack)
            {
                Envelope = 0.5f - 0.5f * FMath::Cos(PI * T / FMath::Max(N.Attack, 1.0e-4f));
            }
            const float Remaining = N.Duration - T;
            if (Remaining < N.Release)
            {
                Envelope *= 0.5f - 0.5f * FMath::Cos(PI * Remaining / FMath::Max(N.Release, 1.0e-4f));
            }
            if (N.TremoloHz > 0.0f)
            {
                A.TremoloPhase = FMath::Fmod(A.TremoloPhase + N.TremoloHz / Fs, 1.0);
                Envelope *= 1.0f - N.TremoloDepth * (0.5f + 0.5f * FMath::Cos(TwoPi * static_cast<float>(A.TremoloPhase)));
            }
            Sum += Signal * Envelope * N.Amp * A.Gain;
        }
        Out[Frame] = SoftClip(Sum * 0.45f);
    }
    S.Sample += NumFrames;
}

TArray<float> RenderCallOffline(ERaftSimWildlifeCall Call, uint32 Seed, float Seconds, int32 InSampleRate)
{
    FCallVoice Voice(Seed, static_cast<float>(InSampleRate));
    FRandomStream Random(static_cast<int32>(Seed));
    Voice.Play(BuildCall(Call, Random), 1.0f);
    TArray<float> Samples;
    Samples.SetNumZeroed(static_cast<int32>(Seconds * InSampleRate));
    constexpr int32 Block = 512;
    for (int32 Start = 0; Start < Samples.Num(); Start += Block)
    {
        Voice.Render(Samples.GetData() + Start, FMath::Min(Block, Samples.Num() - Start));
    }
    return Samples;
}
}

URaftSimCallSoundWave::URaftSimCallSoundWave(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    SetSampleRate(48000);
    NumChannels = 1;
    Duration = INDEFINITELY_LOOPING_DURATION;
    bLooping = false;
    SoundGroup = SOUNDGROUP_Default;
    SampleByteSize = 4;
}

void URaftSimCallSoundWave::InitializeVoice(uint32 Seed)
{
    Voice = MakeShared<RaftSimWildlife::FCallVoice, ESPMode::ThreadSafe>(Seed, 48000.0f);
}

int32 URaftSimCallSoundWave::OnGeneratePCMAudio(TArray<uint8>& OutAudio, int32 NumSamples)
{
    if (!Voice.IsValid() || NumSamples <= 0)
    {
        return 0;
    }
    OutAudio.SetNumUninitialized(NumSamples * static_cast<int32>(sizeof(float)), EAllowShrinking::No);
    Voice->Render(reinterpret_cast<float*>(OutAudio.GetData()), NumSamples);
    return NumSamples;
}
