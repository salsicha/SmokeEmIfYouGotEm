#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimChilkoCropBoundaryTest,
    "RaftSim.M3.ChilkoCropBoundary",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimChilkoCropBoundaryTest::RunTest(const FString&)
{
    const FString Fields=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("physics/data/real_world/chilko_river_bc/scenario_lava_canyon_evidence_2023/cooked_flow_fields"));
    const FString Band=TEXT("summer_runnable_93cms");
    FString Error,Json; TSharedPtr<FJsonObject> Path;
    if(!FFileHelper::LoadFileToString(Json,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("unreal/Tests/Data/chilko_white_kilometre_path.json"))) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Path))return false;
    if(!TestEqual(TEXT("complete original failure trajectory is present"),Path->GetArrayField(TEXT("samples")).Num(),455))return false;
    double PreviousTime=0.;
    for(const auto& Value:Path->GetArrayField(TEXT("samples")))
    {
        const auto& Row=Value->AsArray();
        if(!TestTrue(TEXT("trajectory contains finite, chronological water probes"),Row.Num()==3 &&
            FMath::IsFinite(Row[0]->AsNumber()) && Row[0]->AsNumber()>PreviousTime &&
            FMath::IsFinite(Row[1]->AsNumber()) && FMath::IsFinite(Row[2]->AsNumber())))return false;
        PreviousTime=Row[0]->AsNumber();
    }
    auto Full=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1989,0),FVector2D(3978,56),.045f,Error,false);
    if(!TestTrue(*Error,Full.IsValid()))return false;
    const auto& Source=Full->Solver->scenario();
    const auto FullFlux=Full->Solver->inspect_numerical_mass_flux_grid();
    // Reference closure independently assembled from the uncropped source.
    // Same production finite-volume solver: no substitute fluid or raft motion.
    const auto MakeWindow=[&](double Center,int32 Variant)
    {
        auto W=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(Center,0),FVector2D(480,56),.041f,Error,false);
        if(!W.IsValid() || Variant==0)return W;
        auto S=W->Solver->scenario();
        const int32 C0=FMath::RoundToInt((W->OriginM.X-Full->OriginM.X)/W->CellXM);
        const int32 R0=FMath::RoundToInt((W->OriginM.Y-Full->OriginM.Y)/W->CellYM);
        for(auto& B:S.boundaries)
        {
            const bool West=B.edge=="west",East=B.edge=="east";
            if(!West&&!East)continue;
            B.kind="ghost";B.ghost_cells.clear();
            for(int32 Layer=0;Layer<2;++Layer)for(int32 R=0;R<int32(S.grid.ny);++R)
            {
                const int32 C=West?C0-1-Layer:C0+int32(S.grid.nx)+Layer;
                B.ghost_cells.push_back({Source.bed(R0+R,C)+Full->ElevationDatumM-W->ElevationDatumM,
                    Source.initial.h(R0+R,C),Source.initial.u(R0+R,C),Source.initial.v(R0+R,C)});
            }
        }
        // Keep the old caller coefficient as a diagnostic control; variant 2
        // is the independently constructed correct cooked physical model.
        S.roughness=Variant==1?.041:.045;
        raftsim::SolverConfig Config;
        Config.solver_mode="finite_volume";Config.flux_scheme="hll";Config.spatial_order=2;
        Config.cfl=.2;Config.dry_tolerance=1.e-6;Config.roughness_scale=1.;
        Config.bed_slope_source_scale=1.;Config.feature_strength_scale=0.;
        Config.preserve_initial_mass=false;Config.disable_fixture_calibrations=true;
        W->Solver=MakePimpl<raftsim::ReducedShallowWaterSolver>(MoveTemp(S),Config);
        return W;
    };
    auto Initial=MakeWindow(1490,0);
    if(!TestTrue(*Error,Initial.IsValid()))return false;
    const auto Flux=Initial->Solver->inspect_numerical_mass_flux_grid();
    const int32 C0=FMath::RoundToInt((Initial->OriginM.X-Full->OriginM.X)/Initial->CellXM);
    double FaceError=0.;
    for(int32 R=0;R<int32(Initial->Solver->scenario().grid.ny);++R)
        for(int32 C=0;C<=int32(Initial->Solver->scenario().grid.nx);++C)
            FaceError=FMath::Max(FaceError,FMath::Abs(Flux.x_faces(R,C)-FullFlux.x_faces(R,C+C0)));
    TestTrue(TEXT("cropped faces preserve the uncropped source flux"),FaceError<1.e-7);
    AddInfo(FString::Printf(TEXT("Chilko initial maximum face flux error %.12g m2/s"),FaceError));
    TestTrue(TEXT("band roughness overrides the legacy caller coefficient"),
        FMath::IsNearlyEqual(Initial->Solver->scenario().roughness,.045,1.e-12));
    // Exercise all four internal cuts, not only the full-width gameplay crop.
    auto Narrow=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1490,0),FVector2D(480,40),.041f,Error,false);
    if(!TestTrue(*Error,Narrow.IsValid()))return false;
    const auto NarrowFlux=Narrow->Solver->inspect_numerical_mass_flux_grid();
    const int32 NC0=FMath::RoundToInt((Narrow->OriginM.X-Full->OriginM.X)/Narrow->CellXM);
    const int32 NR0=FMath::RoundToInt((Narrow->OriginM.Y-Full->OriginM.Y)/Narrow->CellYM);
    double NarrowError=0.;
    const auto& NS=Narrow->Solver->scenario();
    for(int32 R=0;R<int32(NS.grid.ny);++R)for(int32 C=0;C<=int32(NS.grid.nx);++C)
        NarrowError=FMath::Max(NarrowError,FMath::Abs(NarrowFlux.x_faces(R,C)-FullFlux.x_faces(R+NR0,C+NC0)));
    for(int32 R=0;R<=int32(NS.grid.ny);++R)for(int32 C=0;C<int32(NS.grid.nx);++C)
        NarrowError=FMath::Max(NarrowError,FMath::Abs(NarrowFlux.y_faces(R,C)-FullFlux.y_faces(R+NR0,C+NC0)));
    TestTrue(TEXT("all four internal cuts preserve source face flux"),NarrowError<1.e-7);
    for(const auto& B:NS.boundaries)TestTrue(TEXT("internal boundary has two exact ghost layers"),
        B.kind=="ghost" && B.ghost_cells.size()==2*(B.edge=="west"||B.edge=="east"?NS.grid.ny:NS.grid.nx));
    // One-cell residual halos expand to the real physical edge rather than
    // reading outside the source or silently copying the nearest cell.
    auto Edge=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1989,0),FVector2D(3974,52),.041f,Error,false);
    if(!TestTrue(*Error,Edge.IsValid()))return false;
    TestTrue(TEXT("one-cell halos expand to the complete grid"),Edge->OriginM==Full->OriginM &&
        Edge->Solver->scenario().grid.nx==Source.grid.nx && Edge->Solver->scenario().grid.ny==Source.grid.ny);
    for(size_t I=0;I<Source.boundaries.size();++I)
        TestTrue(TEXT("physical river boundary remains authored"),
            Edge->Solver->scenario().boundaries[I].kind==Source.boundaries[I].kind);
    auto Recentered=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1490,0),FVector2D(480,56),.041f,Error,true);
    TestFalse(TEXT("cooked ghost mode rejects recentered coordinates"),Recentered.IsValid());
    for(int32 Variant=0;Variant<3;++Variant)
    {
        auto W=MakeWindow(1490,Variant);
        if(!W.IsValid())return false;
        double Elapsed=0.,Center=1490,MaxStageError=0.,MaxSpeed=0.,MaxDepth=0.;
        int32 Moves=0;
        const auto Advance=[&](double Target)
        {while(Elapsed+1.e-6<Target){const float Dt=float(FMath::Min(1./60.,Target-Elapsed));W->Step(Dt);Elapsed+=Dt;}};
        Advance(3.);
        for(const auto& Value:Path->GetArrayField(TEXT("samples")))
        {
            const auto& Row=Value->AsArray();
            const FVector2D P(Row[1]->AsNumber(),Row[2]->AsNumber());
            Advance(3.+Row[0]->AsNumber());
            if(FMath::Abs(P.X-Center)>=80.)
            {
                auto Next=MakeWindow(P.X,Variant);
                if(!Next.IsValid())return false;
                Next->TransferOverlapStateFrom(*W);W=MoveTemp(Next);Center=P.X;++Moves;
            }
            const auto Actual=W->Sample(P),Seed=Full->Sample(P);
            if(!TestTrue(TEXT("original trajectory stays in captured live water"),Actual.bValid&&Seed.bValid))return false;
            if(!TestFalse(TEXT("moving water remains finite"),W->HasNonFiniteState()))return false;
            MaxStageError=FMath::Max(MaxStageError,FMath::Abs(double(Actual.SurfaceHeightM)-Seed.SurfaceHeightM));
            MaxSpeed=FMath::Max(MaxSpeed,Actual.VelocityMps.Size());MaxDepth=FMath::Max(MaxDepth,double(Actual.DepthM));
        }
        AddInfo(FString::Printf(TEXT("Chilko water-only variant=%d moves=%d max_stage_change=%.6f m max_speed=%.6f m/s max_depth=%.6f m"),
            Variant,Moves,MaxStageError,MaxSpeed,MaxDepth));
        if(Variant==0)
        {
            TestTrue(TEXT("runtime crop retains the settled source stage along the original path within 1 cm"),MaxStageError<.01);
            TestTrue(TEXT("runtime does not manufacture a high-speed flood"),MaxSpeed<5.5);
        }
    }
    return !HasAnyErrors();
}
#endif
