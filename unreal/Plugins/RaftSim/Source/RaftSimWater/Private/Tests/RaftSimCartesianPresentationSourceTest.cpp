#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "Misc/AutomationTest.h"
#include "Async/ParallelFor.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianPresentationSourceTest,
    "RaftSim.M3.CartesianPresentationSource",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianPresentationSourceTest::RunTest(const FString&)
{
    const FString Root = URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(TEXT("tmp/cartesian-atlas-fixture-v1"));
    const FVector2D Origin(-5432., 3600.), Center = Origin + FVector2D(15., 14.);
    FString Error;
    auto Shared = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        Root/TEXT("valid"), TEXT("analytic"), Center, FVector2D(12., 10.), .035f, Error, false);
    if (!TestTrue(*FString::Printf(TEXT("shared presentation fixture loads: %s"), *Error), Shared.IsValid())) return false;
    TestTrue(TEXT("live window retains an immutable presentation source"), Shared->HasSharedPresentationSource());
    FBox2D LiveBounds(ForceInit);
    TestTrue(TEXT("live bounds come from actual solver cells"), Shared->GetFieldBoundsM(LiveBounds));
    TestTrue(TEXT("bounds exclude ghost cells and baseline extent"),
        LiveBounds.Min.Equals(Center-FVector2D(6.,5.)) && LiveBounds.Max.Equals(Center+FVector2D(6.,5.)));
    const FBox2D LargerCrop(FVector2D(-112.,-112.),FVector2D(112.,112.));
    for (const FVector2D Direction : {FVector2D(1.,0.),FVector2D(-1.,0.),FVector2D(0.,1.),FVector2D(0.,-1.)})
    {
        TestEqual(TEXT("four crop edges hand over to the source"),RaftSimWaterFlowFrame::CropAuthority(Direction*112.,LargerCrop,30.f),0.f);
        TestEqual(TEXT("all four handover bands have the same physical width"),RaftSimWaterFlowFrame::CropAuthority(Direction*97.,LargerCrop,30.f),.5f);
        TestEqual(TEXT("deep interior remains fully live"),RaftSimWaterFlowFrame::CropAuthority(Direction*80.,LargerCrop,30.f),1.f);
        TestEqual(TEXT("no live authority outside any crop edge"),RaftSimWaterFlowFrame::CropAuthority(Direction*113.,LargerCrop,30.f),0.f);
    }
    const FBox2D MovedCrop(LargerCrop.Min+FVector2D(-5432.,3600.),LargerCrop.Max+FVector2D(-5432.,3600.));
    TestEqual(TEXT("new north-center position needs no previous-frame authority cache"),
        RaftSimWaterFlowFrame::CropAuthority(FVector2D(-5432.,3697.),MovedCrop,30.f),.5f);
    const auto Bed = [](int32 R, int32 C) { return 100.+.031*R+.017*C+.007*((R+2*C)%5); };
    const auto Depth = [](int32 R, int32 C) { return 1.5+.003*R+.005*C; };
    const auto U = [](int32 R, int32 C) { return -.3+.001*R+.01*((R+C)%3); };
    const auto V = [](int32 R, int32 C) { return .5+.002*C; };
    double MaxScalarError = 0., MaxNormalError = 0.;
    int32 Samples = 0, OutsideLive = 0;
    for (int32 Y=1; Y<=89; ++Y) for (int32 X=1; X<=89; ++X)
    {
        const FVector2D P(X*.25, Y*.25);
        const auto Actual = Shared->SamplePresentationSource(Origin+P);
        if (!TestTrue(TEXT("fractional sample crosses modeled tile seams"), Actual.bValid && Actual.bWet)) return false;
        const int32 C=FMath::FloorToInt(P.X), R=FMath::FloorToInt(P.Y);
        const double Fx=P.X-C, Fy=P.Y-R;
        const auto Interpolate = [&](auto F)
        {
            return (1.-Fy)*((1.-Fx)*F(R,C)+Fx*F(R,C+1)) + Fy*((1.-Fx)*F(R+1,C)+Fx*F(R+1,C+1));
        };
        for (const double Difference : {double(Actual.BedHeightM)-float(Interpolate(Bed)+220.),
            double(Actual.DepthM)-float(Interpolate(Depth)),
            double(Actual.SurfaceHeightM)-float(Interpolate(Bed)+Interpolate(Depth)+220.),
            Actual.VelocityMps.X-float(Interpolate(U)), Actual.VelocityMps.Y-float(Interpolate(V))})
            MaxScalarError=FMath::Max(MaxScalarError,FMath::Abs(Difference));
        const auto Eta = [&](int32 RR, int32 CC) { return Bed(RR,CC)+Depth(RR,CC); };
        const int32 CL=FMath::Max(C-1,0), RD=FMath::Max(R-1,0);
        const FVector ExpectedNormal = FVector(float(-(Eta(R,C+1)-Eta(R,CL))/(C+1-CL)),
            float(-(Eta(R+1,C)-Eta(RD,C))/(R+1-RD)),1.f).GetSafeNormal();
        MaxNormalError=FMath::Max(MaxNormalError,FVector::Distance(Actual.SurfaceNormal,ExpectedNormal));
        OutsideLive += !Shared->Sample(Origin+P).bValid;
        ++Samples;
    }
    TestTrue(TEXT("baseline checks span well beyond the moving live crop"), OutsideLive>4000);
    TestTrue(TEXT("baseline retains actual bed/depth/surface/current, not energy-based guesses"), MaxScalarError<1.e-5);
    TestTrue(TEXT("source normals cross tile seams without a flat fallback"), MaxNormalError<1.e-6);
    for (const FVector2D P : {FVector2D(-.01,10.),FVector2D(23.01,10.),FVector2D(10.,23.01),FVector2D(10000.,10000.)})
        TestFalse(TEXT("missing source is never extrapolated as water"), Shared->SamplePresentationSource(Origin+P).bValid);
    TestTrue(TEXT("last exact physical source cell remains addressable"), Shared->SamplePresentationSource(Origin+FVector2D(23.,23.)).bValid);
    const auto Before = Shared->SamplePresentationSource(Center);
    Shared->Step(.037f);
    const auto After = Shared->SamplePresentationSource(Center);
    TestTrue(TEXT("live solver evolution cannot mutate the presentation snapshot"),
        Before.DepthM==After.DepthM && Before.VelocityMps==After.VelocityMps && Before.SurfaceHeightM==After.SurfaceHeightM);

    auto Island = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        Root/TEXT("dry_island"),TEXT("analytic"),Center,FVector2D(12.,10.),.035f,Error,false);
    if (!TestTrue(TEXT("dry island atlas loads"),Island.IsValid())) return false;
    const auto Dry = Island->SamplePresentationSource(Origin+FVector2D(9.,9.));
    TestTrue(TEXT("modeled internal island is valid dry terrain, not unavailable or synthetic water"),
        Dry.bValid && !Dry.bWet && Dry.DepthM==0.f && Dry.VelocityMps.IsZero() && Dry.BedHeightM==Dry.SurfaceHeightM);
    TestTrue(TEXT("cache replacement cannot change an earlier window's retained source"),
        Shared->SamplePresentationSource(Origin+FVector2D(9.,9.)).bWet);
    auto Hole = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        Root/TEXT("missing_northeast"),TEXT("analytic"),Origin+FVector2D(5.5,5.5),FVector2D(7.,7.),.035f,Error,false);
    if (!TestTrue(*FString::Printf(TEXT("L-shaped atlas with safe live crop loads: %s"),*Error),Hole.IsValid())) return false;
    TestFalse(TEXT("internal missing tile is not filled from a same-column neighbor"),Hole->SamplePresentationSource(Origin+FVector2D(13.,13.)).bValid);
    TestFalse(TEXT("bilinear footprint never bridges missing northeast corner"),Hole->SamplePresentationSource(Origin+FVector2D(11.5,11.5)).bValid);
    TestTrue(TEXT("available leg of L-shaped atlas stays visible outside live crop"),Hole->SamplePresentationSource(Origin+FVector2D(20.,8.)).bValid);

    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false; Config.bEnableDeterministicCapture=false;
    Water->Configure(Config);
    if (!Water->ConfigureRiverCoordinateMap(TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json"))) return false;
    FRaftSimWaterSample Missing;
    TestFalse(TEXT("Cartesian frame with no live data cannot invent default tank water"),Water->SampleWaterFieldAtRiverCoordinates(Center,Missing));
    TestFalse(TEXT("world probes with no live Cartesian data fail closed"),Water->SampleWaterAtWorldPosition(FVector(Center.X*100.,-Center.Y*100.,0.),Missing));
    if (!Water->ConfigureRiverWindow(Root/TEXT("valid"),TEXT("analytic"),Center,FVector2D(12.,10.),.035f,false)) return false;
    FBox2D AdapterBounds(ForceInit);
    TestTrue(TEXT("actual render adapter exposes current live crop bounds"),Water->GetLiveWaterFieldBoundsM(AdapterBounds) && AdapterBounds==LiveBounds);
    // The presentation pass may issue independent Cartesian queries together,
    // but must not change finite-crop authority, missing cells or any channel.
    constexpr int32 BatchN=109;
    TArray<FRaftSimWaterSample> SerialLive,SerialBase,ParallelLive,ParallelBase;
    TArray<uint8> SerialValid,ParallelValid;
    SerialLive.SetNum(BatchN*BatchN); SerialBase.SetNum(BatchN*BatchN);
    ParallelLive.SetNum(BatchN*BatchN); ParallelBase.SetNum(BatchN*BatchN);
    SerialValid.SetNum(BatchN*BatchN); ParallelValid.SetNum(BatchN*BatchN);
    const auto Query=[&](int32 I,TArray<FRaftSimWaterSample>& LiveOut,
        TArray<FRaftSimWaterSample>& BaseOut,TArray<uint8>& Valid)
    {
        const FVector2D P=Origin+FVector2D((I%BatchN)*.25-2.,(I/BatchN)*.25-2.);
        Valid[I]=(Water->SampleWaterFieldAtRiverCoordinates(P,LiveOut[I]) ? 1 : 0) |
            (Water->SamplePresentationBaselineFieldAtRiverCoordinates(P,BaseOut[I]) ? 2 : 0);
    };
    for (int32 I=0; I<SerialLive.Num(); ++I) Query(I,SerialLive,SerialBase,SerialValid);
    ParallelFor(TEXT("RaftSimSourceQueryEquality"),SerialLive.Num(),256,
        [&](int32 I) { Query(I,ParallelLive,ParallelBase,ParallelValid); },EParallelForFlags::Unbalanced);
    const auto Equal=[](const FRaftSimWaterSample& A,const FRaftSimWaterSample& B)
    { return A.WorldPosition==B.WorldPosition && A.SurfaceHeightMeters==B.SurfaceHeightMeters &&
        A.BedHeightMeters==B.BedHeightMeters && A.DepthMeters==B.DepthMeters &&
        A.VelocityMetersPerSecond==B.VelocityMetersPerSecond && A.SurfaceNormal==B.SurfaceNormal && A.bWet==B.bWet; };
    int32 Different=0;
    for (int32 I=0; I<SerialLive.Num(); ++I)
        Different += !(Equal(SerialLive[I],ParallelLive[I]) && Equal(SerialBase[I],ParallelBase[I]) && SerialValid[I]==ParallelValid[I]);
    TestEqual(TEXT("concurrent live and atlas queries are exact across interior, seams, crop and unavailable exterior"),Different,0);
    const FVector2D Outside = Origin+FVector2D(2.,2.);
    FRaftSimWaterSample Baseline, Live;
    TestTrue(TEXT("actual render-baseline API samples the shared source outside the crop"),Water->SamplePresentationBaselineFieldAtRiverCoordinates(Outside,Baseline));
    TestFalse(TEXT("shared presentation never expands field gameplay authority"),Water->SampleWaterFieldAtRiverCoordinates(Outside,Live));
    FVector World;
    Water->RiverToWorldPosition(Outside,322.,World);
    TestFalse(TEXT("shared presentation never supplies off-crop raft physics"),Water->SampleRaftSupportSurfaceAtWorldPosition(World,Live));
    const auto Source=Shared->SamplePresentationSource(Outside);
    TestTrue(TEXT("adapter applies river datum once and retains field north"),
        Baseline.SurfaceHeightMeters==Source.SurfaceHeightM-220.f && Baseline.DepthMeters==Source.DepthM &&
        Baseline.VelocityMetersPerSecond.Y==Source.VelocityMps.Y && Baseline.VelocityMetersPerSecond.Y>0.);
    if (!Water->ConfigureRiverWindow(TEXT("tmp/cartesian-runtime-crop-fixture-v1/valid"),TEXT("analytic"),Center,FVector2D(12.,10.),.035f,false)) return false;
    TestFalse(TEXT("Cartesian window without shared source cannot use legacy energy-derived water"),Water->SamplePresentationBaselineFieldAtRiverCoordinates(Outside,Baseline));
    AddInfo(FString::Printf(TEXT("%d source samples (%d outside live crop), max scalar error %.12g, normal error %.12g; dry island, missing corner, immutable ownership and gameplay separation verified."),Samples,OutsideLive,MaxScalarError,MaxNormalError));
    return !HasAnyErrors();
}
#endif
