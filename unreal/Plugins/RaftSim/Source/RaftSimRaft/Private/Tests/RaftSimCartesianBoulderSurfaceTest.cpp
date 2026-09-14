#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianBoulderSurfaceTest,
    "RaftSim.M4.CartesianBoulderSurface",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianBoulderSurfaceTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("isolated carrier world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Surface = World->SpawnActor<ARaftSimWaterSurfaceActor>();
    if (!TestNotNull(TEXT("actual surface actor"), Surface)) return false;
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>(Surface);
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Water->Configure(Config);
    if (!TestTrue(TEXT("actual full-river Cartesian frame"), Water->ConfigureRiverCoordinateMap(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")))) return false;
    const FVector2D Center(-5417., 3614.);
    if (!TestTrue(TEXT("actual live Cartesian crop"), Water->ConfigureRiverWindow(
        TEXT("tmp/cartesian-runtime-crop-fixture-v1/valid"), TEXT("analytic"),
        Center, FVector2D(24., 22.), .035f, false))) return false;
    Surface->WaterAdapter = Water;
    Surface->VertexSpacingMeters = .5f;
    Surface->CurvedGridLengthMeters = 22.f;
    Surface->CurvedGridWidthMeters = 20.f;
    Surface->bFixedCurvedGrid = true;
    Surface->FixedCurvedGridCenterStationMeters = Center.X;
    Surface->FixedCartesianGridCenterNorthMeters = Center.Y;
    Surface->BuildGrid();
    Surface->ResolvedPresentationHydraulicReliefScale = 0.f;
    Surface->ResolvedPresentationStandingWaveScale = 0.f;
    Surface->RefreshSurface();
    // Seed a directional dye-like foam ramp, then exercise the actual
    // semi-Lagrangian refresh. A field/world double reflection samples the
    // opposite north neighbor and must fail this independent expectation.
    const FVector2D FoamOrigin = Surface->RiverCoordinatesM[0];
    for (int32 I = 0; I < Surface->FoamField.Num(); ++I)
    {
        const FVector2D R = Surface->RiverCoordinatesM[I] - FoamOrigin;
        Surface->FoamField[I] = .2 + .003*R.X + .012*R.Y;
    }
    const auto HeldFoam=Surface->FoamField;
    Surface->LastRefreshRealSeconds=FPlatformTime::Seconds()-1234.;
    Surface->RefreshSurface();
    TestTrue(TEXT("actual Cartesian refresh holds all foam bits despite elapsed wall time"),
        HeldFoam.Num()==Surface->FoamField.Num() && FMemory::Memcmp(HeldFoam.GetData(),
            Surface->FoamField.GetData(),HeldFoam.Num()*sizeof(float))==0);
    const double BeforeWater=Water->GetCommittedStepSeconds();
    for(int32 Step=0;Step<12;++Step)
        if(!TestTrue(TEXT("actual native water advances foam interval"),Water->StepWater(1.f/60.f)))return false;
    Surface->RefreshSurface();
    const float Dt=float(Water->GetCommittedStepSeconds()-BeforeWater);
    TestEqual(TEXT("actual foam clock publishes current committed water time"),Surface->FoamWaterClock.Last,Water->GetCommittedStepSeconds());
    TestTrue(TEXT("foam interval comes from accepted native steps"),Dt>.19f && Dt<.21f);
    const float Decay = FMath::Pow(.5f, Dt / FMath::Max(Surface->FoamHalfLifeSeconds, .5f));
    double MaxFoamError = 0., WrongNorthDifference = 0.;
    const int32 FoamNx = Surface->GridStationN, FoamNy = Surface->GridLateralN;
    for (int32 Y = 7; Y < FoamNy-7; ++Y) for (int32 X = 7; X < FoamNx-7; ++X)
    {
        const int32 I = Y*FoamNx + X;
        FRaftSimWaterSample Sample;
        if (!Water->SampleWaterFieldAtRiverCoordinates(Surface->RiverCoordinatesM[I], Sample)) return false;
        const FVector2D R = Surface->RiverCoordinatesM[I] - FoamOrigin;
        const FVector V = Sample.VelocityMetersPerSecond;
        const double Expected = (.2 + .003*(R.X - V.X*Dt) + .012*(R.Y - V.Y*Dt))*Decay;
        const double Wrong = (.2 + .003*(R.X - V.X*Dt) + .012*(R.Y + V.Y*Dt))*Decay;
        MaxFoamError = FMath::Max(MaxFoamError, FMath::Abs(Surface->FoamField[I] - Expected));
        WrongNorthDifference = FMath::Max(WrongNorthDifference, FMath::Abs(Expected - Wrong));
    }
    TestTrue(TEXT("actual foam backtrace uses field north without a second reflection"), MaxFoamError < 1.e-6);
    TestTrue(TEXT("foam fixture distinguishes reflected from actual north transport"), WrongNorthDifference > .001);
    // Isolate rock relief at the SAME advanced water state, not a pre-step mean.
    const auto WithoutRocks=Surface->Vertices;
    Surface->BoulderFootprintsSLR = {FVector3f(Center.X, Center.Y, 1.5f)};
    Surface->RefreshSurface();
    TestEqual(TEXT("actual render window retains exposed test rock"), Surface->WindowBoulderFootprintsSLR.Num(), 1);
    TestEqual(TEXT("render forwards obstruction to rigid support"), Water->GetRaftSupportBoulderFootprintCount(), 1);
    const int32 Nx = Surface->GridStationN, Ny = Surface->GridLateralN;
    TArray<uint8> Wet;
    Wet.Init(1, Nx*Ny);
    const auto Clearance = RaftSimWaterFlowFrame::WetEdgeSteps(Nx, Ny, Wet);
    double MaxErrorM = 0., MaxWrongAxisDifferenceM = 0.;
    int32 NonzeroSamples = 0;
    for (int32 I = 0; I < Surface->Vertices.Num(); ++I)
    {
        const FVector2D P = Surface->RiverCoordinatesM[I];
        FRaftSimWaterSample Sample;
        if (!TestTrue(TEXT("carrier vertex has authoritative live sample"),
            Water->SampleWaterFieldAtRiverCoordinates(P, Sample) && Sample.bWet)) return false;
        if (FVector2D::Distance(P, Center) < 1.5*.7) continue; // Intentional rock cutout, not a height wave.
        const FVector2D D = RaftSimWaterFlowFrame::Direction(FVector2D(
            Sample.VelocityMetersPerSecond.X, Sample.VelocityMetersPerSecond.Y));
        const FVector2D R = RaftSimWaterFlowFrame::ToLocal(P - Center, D);
        const float Speed = Sample.VelocityMetersPerSecond.Size2D();
        const float Shore = ARaftSimWaterSurfaceActor::ComputePresentationShoreDisplacementWeight(
            Clearance[I], 0, 2*Clearance[I], Surface->ResolvedVertexSpacingMeters);
        const float Expected = (Water->ComputeCoupledBoulderPillowDisplacementMeters(R.X, R.Y, 1.5f, Speed) +
            Water->ComputeCoupledBoulderWakePresentation(R.X, R.Y, 1.5f, Speed, 0.f).X) * Shore;
        const double Actual = (Surface->Vertices[I].Z - WithoutRocks[I].Z)*.01;
        MaxErrorM = FMath::Max(MaxErrorM, FMath::Abs(Actual - Expected));
        MaxWrongAxisDifferenceM = FMath::Max(MaxWrongAxisDifferenceM, FMath::Abs(double(Expected) -
            Water->ComputeConfiguredBoulderSupportDisplacementMeters(P, Speed, 0.f)*Shore));
        NonzeroSamples += FMath::Abs(Expected) > .01f;
    }
    TestTrue(TEXT("actual carrier moves at pillow and wake vertices"), NonzeroSamples > 10);
    TestTrue(TEXT("actual carrier uses current direction, not the old field-X axis"), MaxWrongAxisDifferenceM > .04);
    TestTrue(TEXT("actual carrier refresh emits the signed oriented rock profile"), MaxErrorM < 1.e-4);
    TestTrue(TEXT("actual carrier emits nonzero boulder aeration"), Surface->LastBoulderWakeFoamVertexCount > 0);
    AddInfo(FString::Printf(TEXT("Actual Cartesian carrier refresh: %d displaced samples, max height error %.12g m, old-axis difference %.12g m. Analytic integration regression, not river visual acceptance."),
        NonzeroSamples, MaxErrorM, MaxWrongAxisDifferenceM));
    AddInfo(FString::Printf(TEXT("Actual foam transport error %.12g; wrong-north difference %.12g"), MaxFoamError, WrongNorthDifference));
    return !HasAnyErrors();
}
#endif
