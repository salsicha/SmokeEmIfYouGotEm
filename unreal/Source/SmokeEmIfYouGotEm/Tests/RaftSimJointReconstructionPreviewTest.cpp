#include "Misc/AutomationTest.h"
#include "../RaftSimJointReconstructionPreview.h"
#include "RaftSimLiveWaterWindow.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "WorldPartition/WorldPartitionStreamingSource.h"

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
    FWorldPartitionStreamingSource Source;
    const FBox Bounds(FVector(-200.,-400.,10.),FVector(400.,400.,90.));
    TestTrue(TEXT("Verified bounds define residency"),MakeTerrainResidencySource(Bounds,Source));
    TestEqual(TEXT("World-space center retains coordinate signs"),Source.Location,FVector(100.,0.,50.));
    TestTrue(TEXT("Source activates collision before play"),Source.TargetState==EStreamingSourceTargetState::Activated);
    TestTrue(TEXT("Residency independent of terrain height"),Source.bForce2D);
    TestTrue(TEXT("No global grid-range change"),Source.Shapes.Num()==1 && !Source.Shapes[0].bUseGridLoadingRange);
    TestTrue(TEXT("All footprint corners covered"),Source.Shapes.Num()==1 && Source.Shapes[0].Radius>=500.);
    TestTrue(TEXT("Block on incomplete source loading"),Source.bBlockOnSlowLoading);
    TestFalse(TEXT("Invalid bounds rejected"),MakeTerrainResidencySource(FBox(ForceInit),Source));
    TestFalse(TEXT("Degenerate footprint rejected"),MakeTerrainResidencySource(FBox(FVector::ZeroVector,FVector::ZeroVector),Source));
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Ground=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.SM_TroublemakerCapturedGround"));
    if (!TestNotNull(TEXT("Independent unrelated fixture"),Cube) ||
        !TestNotNull(TEXT("Captured full-fallback fixture"),Ground)) return false;
    if (const auto* Data=Cube->GetRenderData())
        AddInfo(FString::Printf(TEXT("Engine cube: collision LOD=%d render LODs=%d first triangles=%u"),
            Cube->LODForCollision,Data->LODResources.Num(),Data->LODResources.IsEmpty()?0:Data->LODResources[0].GetNumTriangles()));
    TestTrue(TEXT("Complete sole collision LOD accepted"),HasFullTerrainFallback(Ground,803842));
    TestFalse(TEXT("Missing terrain rejected"),HasFullTerrainFallback(nullptr,12));
    TestFalse(TEXT("Zero triangle contract rejected"),HasFullTerrainFallback(Ground,0));
    TestFalse(TEXT("Negative triangle contract rejected"),HasFullTerrainFallback(Ground,-12));
    TestFalse(TEXT("Reduced or mismatched fallback rejected"),HasFullTerrainFallback(Ground,803843));
    TestFalse(TEXT("Captured terrain count cannot qualify an unrelated cube"),HasFullTerrainFallback(Cube,803842));
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
