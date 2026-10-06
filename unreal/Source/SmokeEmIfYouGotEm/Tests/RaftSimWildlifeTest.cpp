// Wildlife: every river map has its animals, and every animal's synthesized
// call is audible, unclipped and in its own register (a hippo's honk far
// below a canyon wren's song). The calls are written as WAVs to
// Saved/RaftSimValidation/audio/wildlife for listening.

#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "RaftSimSynthVoice.h"
#include "RaftSimWildlifeCalls.h"

#include "../RaftSimWildlife.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWildlifeCallsTest,
    "RaftSim.Wildlife.CallsAndRivers",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{
/** Rough pitch register: zero crossings of the sounding part. */
float CrossingHz(const TArray<float>& Samples, int32 SampleRate)
{
    int32 Crossings = 0;
    int32 Sounding = 0;
    for (int32 Index = 1; Index < Samples.Num(); ++Index)
    {
        if (FMath::Abs(Samples[Index]) > 0.01f)
        {
            ++Sounding;
            Crossings += (Samples[Index] >= 0.0f) != (Samples[Index - 1] >= 0.0f) ? 1 : 0;
        }
    }
    return Sounding > 0 ? 0.5f * Crossings * SampleRate / Sounding : 0.0f;
}
}

bool FRaftSimWildlifeCallsTest::RunTest(const FString& Parameters)
{
    constexpr int32 SampleRate = 48000;
    const FString OutputDir = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("RaftSimValidation"), TEXT("audio"), TEXT("wildlife"));
    const UEnum* Calls = StaticEnum<ERaftSimWildlifeCall>();
    TMap<ERaftSimWildlifeCall, float> Register;
    for (int32 Index = 0; Index < Calls->NumEnums() - 1; ++Index)
    {
        const ERaftSimWildlifeCall Call = static_cast<ERaftSimWildlifeCall>(Calls->GetValueByIndex(Index));
        if (Call == ERaftSimWildlifeCall::None)
        {
            continue;
        }
        const FString Name = Calls->GetNameStringByIndex(Index);
        const TArray<float> Samples = RaftSimWildlife::RenderCallOffline(Call, 11u, 12.0f, SampleRate);
        double Energy = 0.0;
        float Peak = 0.0f;
        bool bFinite = true;
        for (const float Sample : Samples)
        {
            Energy += static_cast<double>(Sample) * Sample;
            Peak = FMath::Max(Peak, FMath::Abs(Sample));
            bFinite &= FMath::IsFinite(Sample);
        }
        const float Rms = static_cast<float>(FMath::Sqrt(Energy / FMath::Max(Samples.Num(), 1)));
        const float Hz = CrossingHz(Samples, SampleRate);
        Register.Add(Call, Hz);
        AddInfo(FString::Printf(TEXT("%s: rms=%.4f peak=%.3f register=%.0f Hz"), *Name, Rms, Peak, Hz));
        TestTrue(FString::Printf(TEXT("%s is finite"), *Name), bFinite);
        TestTrue(FString::Printf(TEXT("%s is audible (rms %.4f)"), *Name, Rms), Rms > 0.004f);
        TestTrue(FString::Printf(TEXT("%s does not clip (peak %.3f)"), *Name, Peak), Peak < 0.99f);
        TestTrue(FString::Printf(TEXT("%s wav written"), *Name),
            RaftSimSynth::WriteWav16(FPaths::Combine(OutputDir, Name + TEXT(".wav")), Samples, SampleRate));
    }
    // Low voices are low and whistles are high.
    TestTrue(TEXT("a hippo's honk sits below a howler's roar"),
        Register[ERaftSimWildlifeCall::Hippo] < Register[ERaftSimWildlifeCall::MantledHowler]);
    TestTrue(TEXT("a howler's roar sits below an eagle's whistle"),
        Register[ERaftSimWildlifeCall::MantledHowler] < Register[ERaftSimWildlifeCall::BaldEagle]);
    TestTrue(TEXT("a raven's croak sits below a canyon wren's song"),
        Register[ERaftSimWildlifeCall::CommonRaven] < Register[ERaftSimWildlifeCall::CanyonWren]);

    // Every river map carries its animals; other maps none.
    auto Has = [](const FString& Map, ERaftSimWildlifeSpecies Species)
    {
        for (const FRaftSimWildlifeSpeciesInfo& Info : GetRiverWildlife(Map))
        {
            if (Info.Species == Species)
            {
                return true;
            }
        }
        return false;
    };
    TestTrue(TEXT("bald eagles over the South Fork"), Has(TEXT("L_SouthForkAmerican_FullReach"), ERaftSimWildlifeSpecies::BaldEagle));
    TestTrue(TEXT("condors in Grand Canyon"), Has(TEXT("L_Hance"), ERaftSimWildlifeSpecies::CaliforniaCondor));
    TestTrue(TEXT("howler monkeys on the Pacuare"), Has(TEXT("L_UpperHuacas"), ERaftSimWildlifeSpecies::MantledHowler));
    TestTrue(TEXT("torrent ducks on the Futaleufu"), Has(TEXT("L_Terminator"), ERaftSimWildlifeSpecies::TorrentDuck));
    TestTrue(TEXT("sockeye leaping in the Chilko's Lava Canyon"), Has(TEXT("L_LavaCanyon"), ERaftSimWildlifeSpecies::SockeyeSalmon));
    TestTrue(TEXT("baboons on the Batoka Gorge walls"), Has(TEXT("UEDPIE_0_L_Zambezi"), ERaftSimWildlifeSpecies::ChacmaBaboon));
    // Hippos live above Victoria Falls, not on the Batoka rapids
    // (docs/river-wildlife-reference.md).
    TestFalse(TEXT("no hippos on the Batoka rapids"), Has(TEXT("L_Zambezi"), ERaftSimWildlifeSpecies::Hippopotamus) ||
        Has(TEXT("L_ZambeziUpperGorge"), ERaftSimWildlifeSpecies::Hippopotamus));
    TestTrue(TEXT("no wildlife on test tanks"), GetRiverWildlife(TEXT("L_TestTank")).IsEmpty());
    for (const TCHAR* Map : {TEXT("L_SouthForkAmerican_FullReach"), TEXT("L_SouthFork_Troublemaker"), TEXT("L_Hance"),
             TEXT("L_UpperHuacas"), TEXT("L_Terminator"), TEXT("L_LavaCanyon"), TEXT("L_Zambezi"), TEXT("L_ZambeziUpperGorge")})
    {
        const TArray<FRaftSimWildlifeSpeciesInfo> Table = GetRiverWildlife(Map);
        TestTrue(FString::Printf(TEXT("%s has 4 or more species"), Map), Table.Num() >= 4);
        for (const FRaftSimWildlifeSpeciesInfo& Info : Table)
        {
            TestTrue(FString::Printf(TEXT("%s species sized and numbered"), Map),
                Info.SizeMeters > 0.0f && Info.MaxNearby >= 1 && Info.GroupMax >= Info.GroupMin);
        }
    }
    return true;
}

#endif
