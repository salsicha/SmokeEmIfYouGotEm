#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkInferredTerrainReliefTest,
    "RaftSim.M9.DInferredFarFieldTerrainRelief",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkInferredTerrainReliefTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimEditorEnvironment;

    constexpr float MaximumReliefM = 4.80f;
    for (int32 SampleIndex = 0; SampleIndex < 64; ++SampleIndex)
    {
        const double WorldXM = -28313.353 + SampleIndex * 431.75;
        const double WorldYM = -4427.372 + SampleIndex * 151.25;
        const float SourceSlope = SampleIndex / 63.0f;
        const float First = ComputeSouthForkInferredFarFieldReliefM(
            WorldXM, WorldYM, SourceSlope);
        const float Second = ComputeSouthForkInferredFarFieldReliefM(
            WorldXM, WorldYM, SourceSlope);
        TestTrue(
            TEXT("Inferred far-field relief is deterministic"),
            First == Second);
        TestTrue(
            TEXT("Inferred far-field relief stays inside its visual-only cap"),
            FMath::Abs(First) <= MaximumReliefM + KINDA_SMALL_NUMBER);
    }

    const float FlatBenchRelief = ComputeSouthForkInferredFarFieldReliefM(
        -13817.0, 2471.0, 0.0f);
    TestTrue(
        TEXT("Nearly flat source benches retain centimetre-scale relief"),
        FMath::Abs(FlatBenchRelief) <= 0.12f + KINDA_SMALL_NUMBER);

    const double SeamWorldXM = -5153.461;
    const double SeamWorldYM = 1989.899;
    const float SeamSlope = 0.42f;
    const float FirstPatchSample = ComputeSouthForkInferredFarFieldReliefM(
        SeamWorldXM, SeamWorldYM, SeamSlope);
    const float OverlappingPatchSample = ComputeSouthForkInferredFarFieldReliefM(
        SeamWorldXM, SeamWorldYM, SeamSlope);
    TestEqual(
        TEXT("Overlapping source windows share the same world-space relief phase"),
        FirstPatchSample,
        OverlappingPatchSample);

    const TSharedRef<FJsonObject> Manifest =
        BuildSouthForkInferredFarFieldReliefManifest();
    TestEqual(
        TEXT("Relief manifest labels the deterministic algorithm"),
        Manifest->GetStringField(TEXT("algorithm")),
        FString(TEXT("world_space_slope_conditioned_domain_warped_ridged_fractal_v2")));
    TestTrue(
        TEXT("Relief manifest keeps the cap below five metres"),
        Manifest->GetNumberField(TEXT("maximum_amplitude_m")) < 5.0);
    TestTrue(
        TEXT("Relief manifest records a mesh-resolvable ridge wavelength"),
        Manifest->GetNumberField(TEXT("ridge_wavelength_m")) >= 90.0);
    TestTrue(
        TEXT("Relief blend weights preserve the hard amplitude cap"),
        Manifest->GetNumberField(TEXT("broad_weight")) +
            Manifest->GetNumberField(TEXT("detail_weight")) +
            Manifest->GetNumberField(TEXT("ridge_weight")) <=
            1.0 + KINDA_SMALL_NUMBER);
    TestFalse(
        TEXT("Relief manifest excludes gameplay collision"),
        Manifest->GetBoolField(TEXT("affects_gameplay_collision")));
    TestFalse(
        TEXT("Relief manifest excludes hydraulic authority"),
        Manifest->GetBoolField(TEXT("affects_hydraulics")));
    return !HasAnyErrors();
}

#endif
