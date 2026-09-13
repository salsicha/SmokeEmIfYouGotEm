#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianSupportCouplingTest,
    "RaftSim.M3.CartesianCrestSupportCoupling",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianSupportCouplingTest::RunTest(const FString&)
{
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false; Config.bEnableDeterministicCapture=false;
    Water->Configure(Config);
    if (!TestTrue(TEXT("actual Cartesian coordinate map loads"),Water->ConfigureRiverCoordinateMap(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")))) return false;
    const FVector2D Center(-5417.,3614.);
    if (!TestTrue(TEXT("actual Cartesian MUSCL loader creates the analytic window"),Water->ConfigureRiverWindow(
        TEXT("tmp/cartesian-runtime-crop-fixture-v1/valid"),TEXT("analytic"),Center,FVector2D(24.,22.),.035f,false))) return false;
    Water->ConfigureRaftSupportSurface(true,1.f,0.f,0.f);
    for (const auto Offset:{FVector2D(0,0),FVector2D(2,1),FVector2D(-2,-1)})
    {
        FVector World;FRaftSimWaterSample Raw,Support;
        if (!Water->RiverToWorldPosition(Center+Offset,322.,World) ||
            !Water->SampleWaterFieldAtRiverCoordinates(Center+Offset,Raw) ||
            !Water->SampleRaftSupportSurfaceAtWorldPosition(World,Support))return false;
        TestEqual(TEXT("Cartesian support preserves native mean stage despite optical smoothing setting"),
            Support.SurfaceHeightMeters,Raw.SurfaceHeightMeters);
    }
    Water->ConfigureRaftSupportSurface(true,0.f,0.f,1.f);
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
    auto& Site=Sites.AddDefaulted_GetRef(); Site.RiverCoordinatesMeters=Center;
    Site.PhysicalCrestHeightMeters=.7f; Site.PhysicalCrestLengthMeters=3.f;
    Site.FlowDirection=FVector2D(0.,1.); Site.bLocalEnvelopeCap=true; Site.Intensity=.8f;
    double MaxError=0.;
    for (const FVector2D Offset : {FVector2D(0.,0.),FVector2D(0.,2.),FVector2D(2.,0.),FVector2D(0.,-2.)})
    {
        FVector World;
        if (!Water->RiverToWorldPosition(Center+Offset,322.,World)) return false;
        FRaftSimWaterSample Without,With;
        Water->ConfigureRaftSupportBreakingSites({},.22f,1.f);
        if (!TestTrue(TEXT("base raft support sampled"),Water->SampleRaftSupportSurfaceAtWorldPosition(World,Without))) return false;
        Water->ConfigureRaftSupportBreakingSites(Sites,.22f,1.f);
        if (!TestTrue(TEXT("oriented raft support sampled"),Water->SampleRaftSupportSurfaceAtWorldPosition(World,With))) return false;
        const double Expected=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(Center+Offset,Sites,.22f,1.f);
        const double Actual=double(With.SurfaceHeightMeters)-double(Without.SurfaceHeightMeters);
        MaxError=FMath::Max(MaxError,FMath::Abs(Actual-Expected));
        if (Offset.IsNearlyZero()) TestTrue(TEXT("Cartesian raft support receives the visible crest despite bake-wave being disabled"),Actual>.5);
    }
    TestTrue(TEXT("public world-space support mirrors the oriented profile within source float precision"),MaxError<1.e-4);
    AddInfo(FString::Printf(TEXT("Actual Cartesian loader/coordinate adapter/support path: maximum crest coupling error %.12g m"),MaxError));
    Water->ConfigureRaftSupportBreakingSites({}, .22f, 1.f);
    TArray<URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint> Rocks;
    Rocks.Add({Center, 1.5f});
    double MaxBoulderError = 0.;
    double MaxWrongAxisDifference = 0.;
    int32 NonzeroBoulderSamples = 0;
    for (int32 Y = -6; Y <= 6; ++Y) for (int32 X = -6; X <= 6; ++X)
    {
        const FVector2D P = Center + FVector2D(X*.5, Y*.5);
        FVector World;
        if (!Water->RiverToWorldPosition(P, 322., World)) return false;
        FRaftSimWaterSample Raw, Without, With;
        if (!Water->SampleWaterFieldAtRiverCoordinates(P, Raw)) return false;
        Water->ConfigureRaftSupportBoulderFootprints({});
        if (!Water->SampleRaftSupportSurfaceAtWorldPosition(World, Without)) return false;
        Water->ConfigureRaftSupportBoulderFootprints(Rocks);
        if (!Water->SampleRaftSupportSurfaceAtWorldPosition(World, With)) return false;
        const FVector2D D = RaftSimWaterFlowFrame::Direction(FVector2D(
            Raw.VelocityMetersPerSecond.X, Raw.VelocityMetersPerSecond.Y));
        TestTrue(TEXT("fixture covers reflected north and west flow"), D.X < 0. && D.Y > 0.);
        TestTrue(TEXT("world sampler reflects field north exactly once"),
            FMath::Abs(Without.VelocityMetersPerSecond.Y + Raw.VelocityMetersPerSecond.Y) < 1.e-6);
        const FVector2D R = RaftSimWaterFlowFrame::ToLocal(P - Center, D);
        const float Speed = Raw.VelocityMetersPerSecond.Size2D();
        const float Expected = URaftSimWaterRuntimeAdapter::ComputeCoupledBoulderPillowDisplacementMeters(
            R.X, R.Y, 1.5f, Speed) + URaftSimWaterRuntimeAdapter::ComputeCoupledBoulderWakePresentation(
                R.X, R.Y, 1.5f, Speed, 0.f).X;
        MaxBoulderError = FMath::Max(MaxBoulderError,
            FMath::Abs(double(With.SurfaceHeightMeters) - Without.SurfaceHeightMeters - Expected));
        MaxWrongAxisDifference = FMath::Max(MaxWrongAxisDifference, FMath::Abs(double(Expected) -
            Water->ComputeConfiguredBoulderSupportDisplacementMeters(P, Speed, 0.f)));
        NonzeroBoulderSamples += FMath::Abs(Expected) > .01f;
    }
    TestTrue(TEXT("actual raft support exercises nonzero rock displacement"), NonzeroBoulderSamples > 10);
    TestTrue(TEXT("actual raft support follows hydraulic current rather than field X"), MaxWrongAxisDifference > .04);
    TestTrue(TEXT("world-space raft support carries the same rotated rock geometry"), MaxBoulderError < 1.e-4);
    AddInfo(FString::Printf(TEXT("Actual reflected-north/west-flow boulder support: maximum coupling error %.12g m; old-axis difference %.12g m"), MaxBoulderError, MaxWrongAxisDifference));
    FVector Probe;
    if (!Water->RiverToWorldPosition(Center,322.,Probe)) return false;
    FRaftSimWaterSample Before,After,Raw;
    if (!Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,Before) ||
        !Water->SampleWaterAtWorldPosition(Probe,Raw)) return false;
    // UObject itself is abstract in this engine; use a concrete, inert owner.
    auto* Owner=NewObject<URaftSimWaterRuntimeAdapter>();
    auto* OtherOwner=NewObject<URaftSimWaterRuntimeAdapter>();
    int32 Calls=0; float CarrierHeight=Before.SurfaceHeightMeters+.43f;
    bool bAvailable=true,bWet=true;
    Water->SetRaftSupportCarrierSampler(Owner,[&](const FVector& P,float& H,bool& Wet)
    {
        ++Calls; TestTrue(TEXT("carrier receives unchanged world XY, not reflected twice"),P==Probe);
        H=CarrierHeight; Wet=bWet; return bAvailable;
    });
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("carrier replaces support once without re-adding analytic relief"),After.SurfaceHeightMeters,CarrierHeight);
    TestTrue(TEXT("carrier leaves hydraulic velocity, depth, bed and normal unchanged"),
        After.VelocityMetersPerSecond==Raw.VelocityMetersPerSecond && After.DepthMeters==Raw.DepthMeters &&
        After.BedHeightMeters==Raw.BedHeightMeters && After.SurfaceNormal==Raw.SurfaceNormal);
    bAvailable=false;
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("unavailable carrier retains existing analytic support"),After.SurfaceHeightMeters,Before.SurfaceHeightMeters);
    bAvailable=true; CarrierHeight=std::numeric_limits<float>::quiet_NaN();
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("nonfinite carrier is rejected"),After.SurfaceHeightMeters,Before.SurfaceHeightMeters);
    CarrierHeight=Before.SurfaceHeightMeters+.43f; bWet=false;
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestFalse(TEXT("clipped dry carrier supplies no hull support"),After.bWet);
    Water->SampleWaterAtWorldPosition(Probe,After);
    TestTrue(TEXT("support clipping never changes underlying hydraulic wetness"),After.bWet);
    bWet=true;
    const int32 BeforeOutside=Calls;
    TestFalse(TEXT("provider cannot extend the live hydraulic crop"),Water->SampleRaftSupportSurfaceAtWorldPosition(
        Probe+FVector(100000.,0.,0.),After));
    TestEqual(TEXT("off-crop query never invokes provider"),Calls,BeforeOutside);
    Water->ClearRaftSupportCarrierSampler(OtherOwner);
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("unrelated owner cannot unbind current carrier"),After.SurfaceHeightMeters,CarrierHeight);
    Water->ClearRaftSupportCarrierSampler(Owner);
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("owner teardown restores fallback"),After.SurfaceHeightMeters,Before.SurfaceHeightMeters);
    Water->SetRaftSupportCarrierSampler(Owner,[&](const FVector&,float&,bool&) { ++Calls; return true; });
    Owner->MarkAsGarbage(); const int32 BeforeExpired=Calls;
    Water->SampleRaftSupportSurfaceAtWorldPosition(Probe,After);
    TestEqual(TEXT("expired weak owner is never called"),Calls,BeforeExpired);
    TestEqual(TEXT("expired owner uses fallback"),After.SurfaceHeightMeters,Before.SurfaceHeightMeters);
    return !HasAnyErrors();
}
#endif
