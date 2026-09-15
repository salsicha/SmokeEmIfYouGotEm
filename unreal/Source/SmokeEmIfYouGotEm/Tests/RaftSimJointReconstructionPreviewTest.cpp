#include "Misc/AutomationTest.h"
#include "../RaftSimJointReconstructionPreview.h"
#include "RaftSimLiveWaterWindow.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimJointPreviewContract,
    "RaftSim.M3.JointReconstructionPreviewContract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)

bool FRaftSimJointPreviewContract::RunTest(const FString&)
{
    using namespace RaftSimJointReconstructionPreview;
    const FString Map=TEXT("L_SouthForkAmerican_FullReach");
    TestTrue(TEXT("Existing South Fork editor preview"),IsAllowed(Map,true,true));
    TestTrue(TEXT("PIE map prefix"),IsAllowed(TEXT("UEDPIE_0_")+Map,true,true));
    TestFalse(TEXT("No real-profile override"),IsAllowed(Map,false,true));
    TestFalse(TEXT("No packaged/shipping override"),IsAllowed(Map,true,false));
    TestFalse(TEXT("Not a standalone Troublemaker scenario"),IsAllowed(TEXT("L_SouthFork_Troublemaker"),true,true));
    TestFalse(TEXT("No other river override"),IsAllowed(TEXT("L_Colorado"),true,true));
    FString Error;
    TestFalse(TEXT("Missing world is side-effect-free failure"),Apply(nullptr,TEXT("tmp/missing.json"),true,Error));
    TestFalse(TEXT("Failure provides evidence"),Error.IsEmpty());
#if RAFTSIM_HAS_LIVE_SOLVER
    TestEqual(TEXT("Portable empty SHA256"),RaftSimCookedArtifactSha256({}),
        FString(TEXT("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")));
    TArray<uint8> Abc={97,98,99};
    TestEqual(TEXT("Portable abc SHA256"),RaftSimCookedArtifactSha256(Abc),
        FString(TEXT("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")));
#endif
    return true;
}
#endif
