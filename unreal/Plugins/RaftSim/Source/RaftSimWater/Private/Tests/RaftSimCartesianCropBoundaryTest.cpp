#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianCropBoundaryTest,
    "RaftSim.M3.CartesianCropBoundaries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCartesianCropBoundaryTest::RunTest(const FString&)
{
    const FString Base = URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("tmp/cartesian-runtime-crop-fixture-v1"));
    const FVector2D Center(-5432.+15.,3600.+14.), Extent(12.,10.);
    FString Error;
    auto Window = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        Base/TEXT("valid"),TEXT("analytic"),Center,Extent,.035f,Error,false);
    if (!TestTrue(*FString::Printf(TEXT("analytic source loads (run prepare_cartesian_runtime_fixture.py): %s"),*Error),Window.IsValid())) return false;
    const auto Bed = [](int32 R,int32 C) { return 100.+.031*R+.017*C+.007*((R+2*C)%5); };
    const auto Depth = [](int32 R,int32 C) { return 1.5+.003*R+.005*C; };
    const auto U = [](int32 R,int32 C) { return -.3+.001*R+.01*((R+C)%3); };
    const auto V = [](int32 R,int32 C) { return .5+.002*C; };
    double Datum = 0.;
    for (int32 R=9; R<=19; ++R) for (int32 C=9; C<=21; ++C) Datum += Bed(R,C)+Depth(R,C);
    Datum /= 13.*11.;
    TestEqual(TEXT("absolute datum restored exactly"),Window->ElevationDatumM,Datum+220.);
    TestFalse(TEXT("Cartesian surface does not inherit legacy bake-wave motion"),Window->HasTravelingWavePresentation());
    const auto& Scenario = Window->Solver->scenario();
    TestTrue(TEXT("outward crop dimensions and global XY retained"),Scenario.grid.nx==13 && Scenario.grid.ny==11 &&
        Window->OriginM==FVector2D(-5432.+9.,3600.+9.));
    TestEqual(TEXT("four spatial ghost boundaries"),int32(Scenario.boundaries.size()),4);
    int32 Ghosts = 0;
    for (const auto& Boundary : Scenario.boundaries)
    {
        const bool West=Boundary.edge=="west", East=Boundary.edge=="east", X=West||East;
        const int32 Count=X?11:13;
        if (!TestTrue(TEXT("two complete nearest-first layers"),Boundary.kind=="ghost" &&
            Boundary.ghost_cells.size()==2*Count)) return false;
        for (int32 Layer=0; Layer<2; ++Layer) for (int32 Along=0; Along<Count; ++Along)
        {
            const int32 C=X?(West?8-Layer:22+Layer):9+Along;
            const int32 R=X?9+Along:(Boundary.edge=="south"?8-Layer:20+Layer);
            const auto& Cell=Boundary.ghost_cells[Layer*Count+Along];
            TestTrue(TEXT("both source layers retain exact signed velocity and datum-adjusted bed"),
                Cell.bed==Bed(R,C)-Datum && Cell.h==Depth(R,C) && Cell.u==U(R,C) && Cell.v==V(R,C));
            ++Ghosts;
        }
    }
    raftsim::SolverConfig Config;
    Config.solver_mode="finite_volume"; Config.flux_scheme="hll"; Config.spatial_order=2;
    Config.cfl=.2; Config.dry_tolerance=1.e-6; Config.roughness_scale=1.;
    Config.bed_slope_source_scale=1.; Config.feature_strength_scale=0.;
    Config.preserve_initial_mass=false; Config.disable_fixture_calibrations=true;
    raftsim::ReducedShallowWaterSolver Reference(Scenario,Config);
    // Compare every initial face to an uncropped source. This independently
    // checks the outside reconstruction, not merely the ghost array layout.
    auto FullTank = FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5432.,3600.),31,29,1,2,1);
    auto FullScenario = FullTank->Solver->scenario();
    FullScenario.roughness=.035;
    for (int32 R=0; R<29; ++R) for (int32 C=0; C<31; ++C)
    {
        FullScenario.bed(R,C)=Bed(R,C)-Datum;
        FullScenario.initial.h(R,C)=Depth(R,C);
        FullScenario.initial.eta(R,C)=FullScenario.bed(R,C)+Depth(R,C);
        FullScenario.initial.u(R,C)=U(R,C); FullScenario.initial.v(R,C)=V(R,C);
        FullScenario.initial.hu(R,C)=Depth(R,C)*U(R,C); FullScenario.initial.hv(R,C)=Depth(R,C)*V(R,C);
    }
    raftsim::ReducedShallowWaterSolver Full(MoveTemp(FullScenario),Config);
    const auto FullFlux=Full.inspect_numerical_mass_flux_grid();
    const auto CropFlux=Window->Solver->inspect_numerical_mass_flux_grid();
    double MaxFaceError=0.;
    for (int32 R=0; R<11; ++R) for (int32 C=0; C<=13; ++C)
        MaxFaceError=FMath::Max(MaxFaceError,FMath::Abs(CropFlux.x_faces(R,C)-FullFlux.x_faces(R+9,C+9)));
    for (int32 R=0; R<=11; ++R) for (int32 C=0; C<13; ++C)
        MaxFaceError=FMath::Max(MaxFaceError,FMath::Abs(CropFlux.y_faces(R,C)-FullFlux.y_faces(R+9,C+9)));
    TestTrue(TEXT("every cropped numerical face matches uncropped MUSCL source"),MaxFaceError<1.e-11);
    constexpr float Dt=.037f;
    double MaxStateError=0.;
    for (int32 Step=0; Step<10; ++Step)
    {
        Window->Step(Dt); Reference.step(double(Dt));
        const auto& Actual=Window->Solver->state(); const auto& Expected=Reference.state();
        for (int32 R=0; R<11; ++R) for (int32 C=0; C<13; ++C)
        {
            MaxStateError=FMath::Max(MaxStateError,FMath::Abs(Actual.h(R,C)-Expected.h(R,C)));
            MaxStateError=FMath::Max(MaxStateError,FMath::Abs(Actual.u(R,C)-Expected.u(R,C)));
            MaxStateError=FMath::Max(MaxStateError,FMath::Abs(Actual.v(R,C)-Expected.v(R,C)));
        }
    }
    TestEqual(TEXT("runtime advances exactly as explicit MUSCL2 reference"),MaxStateError,0.);
    TestFalse(TEXT("evolved crop remains finite"),Window->HasNonFiniteState());
    for (const TCHAR* Variant : {TEXT("wrong_frame"),TEXT("replay_conflict"),TEXT("physical_inlet"),
            TEXT("first_order"),TEXT("mass_correction"),TEXT("forced"),TEXT("wrong_roughness")})
    {
        auto Rejected=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/Variant,TEXT("analytic"),Center,Extent,.035f,Error,false);
        TestTrue(*FString::Printf(TEXT("%s fails closed with explanation"),Variant),!Rejected.IsValid()&&!Error.IsEmpty());
    }
    for (const FVector2D BadCenter : {FVector2D(-5432.+6.,3614.),FVector2D(-5432.+24.,3614.),
            FVector2D(-5417.,3600.+5.),FVector2D(-5417.,3600.+23.)})
    {
        auto Rejected=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("valid"),TEXT("analytic"),BadCenter,Extent,.035f,Error,false);
        TestTrue(TEXT("each incomplete source halo rejected"),!Rejected.IsValid()&&Error.Contains(TEXT("ghost layers")));
    }
    auto Recentered=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("valid"),TEXT("analytic"),Center,Extent,.035f,Error,true);
    TestFalse(TEXT("hydraulic crux relocation rejected"),Recentered.IsValid());
    auto Legacy=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("legacy"),TEXT("analytic"),Center,Extent,.035f,Error,false);
    TestTrue(TEXT("legacy first-order crop unchanged"),Legacy.IsValid()&&Legacy->HasTravelingWavePresentation()&&
        Legacy->Solver->scenario().boundaries[0].kind=="transmissive");
    AddInfo(FString::Printf(TEXT("%d exact two-layer ghost cells; max uncropped face error %.12g; 10-step reference state error %.12g"),Ghosts,MaxFaceError,MaxStateError));
    return !HasAnyErrors();
}
#endif
