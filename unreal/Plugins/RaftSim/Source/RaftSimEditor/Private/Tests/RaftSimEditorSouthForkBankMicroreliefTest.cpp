#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkBankMicroreliefTest,
    "RaftSim.M9.EBankMicroreliefPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkBankMicroreliefTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimEditorEnvironment;

    const FSouthForkBankMicroreliefSample Dry =
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 42.0f,
            0.16f, 0.0f, 120.0f);
    const FSouthForkBankMicroreliefSample Repeated =
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 42.0f,
            0.16f, 0.0f, 120.0f);
    TestTrue(TEXT("Representative dry bank receives microrelief"), Dry.bEligible);
    TestTrue(
        TEXT("Bank microrelief is deterministic"),
        Dry.bEligible == Repeated.bEligible &&
            Dry.VerticalDisplacementCm == Repeated.VerticalDisplacementCm &&
            Dry.CombinedFade == Repeated.CombinedFade);
    TestTrue(
        TEXT("Bank microrelief stays inside the forty-two-centimetre cap"),
        Dry.VerticalDisplacementCm > 0.0f &&
            Dry.VerticalDisplacementCm <= 42.0f);

    TestFalse(
        TEXT("Wet cells cannot receive bank microrelief"),
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 42.0f,
            0.16f, 0.11f, 120.0f).bEligible);
    TestFalse(
        TEXT("The live river corridor remains excluded"),
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 12.0f,
            0.16f, 0.0f, 120.0f).bEligible);
    TestFalse(
        TEXT("The outer source-ribbon seam remains excluded"),
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 113.0f,
            0.16f, 0.0f, 120.0f).bEligible);
    TestFalse(
        TEXT("Patch endpoints fade completely into source terrain"),
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 42.0f,
            0.16f, 0.0f, 0.0f).bEligible);
    TestFalse(
        TEXT("Implausibly steep source faces remain unmodified"),
        ComputeSouthForkBankMicroreliefSample(
            -13542.75, 812.25, 944.0f, 42.0f,
            0.59f, 0.0f, 120.0f).bEligible);

    const TSharedRef<FJsonObject> Manifest =
        BuildSouthForkBankMicroreliefManifest();
    TestEqual(
        TEXT("Manifest records the two-metre presentation spacing"),
        Manifest->GetNumberField(TEXT("presentation_spacing_m")), 2.0);
    TestEqual(
        TEXT("Manifest records the hard displacement cap"),
        Manifest->GetNumberField(TEXT("maximum_vertical_displacement_cm")),
        42.0);
    TestFalse(
        TEXT("Manifest excludes gameplay collision"),
        Manifest->GetBoolField(TEXT("affects_gameplay_collision")));
    TestFalse(
        TEXT("Manifest excludes hydraulic authority"),
        Manifest->GetBoolField(TEXT("affects_hydraulics")));
    return !HasAnyErrors();
}

#endif
