#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPairedFeatureSurfaceTransportTest,
    "RaftSim.M3.PairedFeatureSurfaceTransport",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimPairedFeatureSurfaceTransportTest::RunTest(const FString&)
{
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;Config.bEnableDeterministicCapture=false;Water->Configure(Config);
    if(!Water->ConfigureRiverCoordinateMap(TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")))return false;
    const FVector2D Center(-5417.,3614.);
    if(!Water->ConfigureRiverWindow(TEXT("tmp/cartesian-runtime-crop-fixture-v1/valid"),TEXT("analytic"),Center,FVector2D(24.,22.),.035f,false))return false;
    Water->ConfigureRaftSupportSurface(true,0,0,0);Water->ConfigureFeatureKinematics(true);
    auto* Owner=NewObject<URaftSimWaterRuntimeAdapter>();int32 Calls=0;
    Water->SetFeatureSurfaceTransportSampler(Owner,[&](const FVector2D&,FVector2D& V,float& Weight){++Calls;V=FVector2D(-.7,1.25);Weight=1;return true;});
    FVector P;FRaftSimWaterSample Support,Interaction;
    if(!Water->RiverToWorldPosition(Center,322.,P) || !Water->SampleRaftSupportSurfaceAtWorldPosition(P,Support) || !Support.bWet)return false;
    P.Z=Support.SurfaceHeightMeters*100.;FVector2D Coordinates;FVector Tangent,Left;
    Water->WorldToRiverCoordinates(P,Coordinates,Tangent,Left);
    if(!Water->SampleRaftInteractionWaterAtWorldPosition(P,Interaction))return false;
    const FVector Expected=Tangent*(-.7)+Left*1.25;
    TestTrue(TEXT("public hull consumes retained displayed flow in actual Cartesian north-reflected map"),(Interaction.VelocityMetersPerSecond-Expected).Size()<1.e-5);
    TestTrue(TEXT("callback actually sampled"),Calls>0);
    Water->SetRaftSupportCarrierSampler(Owner,[](const FVector&,float& H,bool& Wet){H=322;Wet=false;return true;});
    const int32 BeforeDry=Calls;Water->SampleRaftInteractionWaterAtWorldPosition(P,Interaction);
    TestFalse(TEXT("paired current cannot wet a clipped bank"),Interaction.bWet);
    TestEqual(TEXT("dry carrier never requests a flow"),Calls,BeforeDry);
    Water->ClearRaftSupportCarrierSampler(Owner);Owner->MarkAsGarbage();const int32 BeforeExpired=Calls;
    Water->SampleRaftInteractionWaterAtWorldPosition(P,Interaction);
    TestEqual(TEXT("expired weak source is never sampled"),Calls,BeforeExpired);
    TestTrue(TEXT("expired source restores ordinary current"),(Interaction.VelocityMetersPerSecond-Support.VelocityMetersPerSecond).Size()<1.e-5);
    return !HasAnyErrors();
}
#endif
