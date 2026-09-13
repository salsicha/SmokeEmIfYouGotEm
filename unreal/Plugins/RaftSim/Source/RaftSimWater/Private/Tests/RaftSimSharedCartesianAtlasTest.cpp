#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"
#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSharedCartesianAtlasTest,
    "RaftSim.M3.SharedCartesianAtlas",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSharedCartesianAtlasTest::RunTest(const FString&)
{
    const FString Base=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(TEXT("tmp/cartesian-atlas-fixture-v1"));
    const FString Dense=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(TEXT("tmp/cartesian-runtime-crop-fixture-v1/valid"));
    const FVector2D Center(-5417.,3614.),Extent(12.,10.);
    FString Error;
    const int32 Before=FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting();
    auto Shared=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("valid"),TEXT("analytic"),Center,Extent,.035f,Error,false);
    if (!TestTrue(*FString::Printf(TEXT("shared four-tile source loads: %s"),*Error),Shared.IsValid())) return false;
    const int32 Loaded=FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting();
    TestTrue(TEXT("at most one immutable atlas load"),Loaded==Before || Loaded==Before+1);
    auto Reference=FRaftSimLiveWaterWindow::CreateFromCookedFields(Dense,TEXT("analytic"),Center,Extent,.035f,Error,false);
    if (!TestTrue(TEXT("independent dense source loads"),Reference.IsValid())) return false;
    TestEqual(TEXT("shared atlas preserves exact vertical datum"),Shared->ElevationDatumM,Reference->ElevationDatumM);
    const auto Compare=[&]()
    {
        const auto& A=Shared->Solver->state(); const auto& B=Reference->Solver->state();
        return A.h.values()==B.h.values() && A.u.values()==B.u.values() && A.v.values()==B.v.values() &&
            A.hu.values()==B.hu.values() && A.hv.values()==B.hv.values() && A.eta.values()==B.eta.values() && A.wet.values==B.wet.values;
    };
    TestTrue(TEXT("shared state exactly matches dense loader"),Compare());
    const auto& A=Shared->Solver->scenario(); const auto& B=Reference->Solver->scenario();
    int32 Ghosts=0;
    for (size_t I=0;I<A.boundaries.size();++I)
    {
        const auto& Left=A.boundaries[I]; const auto& Right=B.boundaries[I];
        if (!TestEqual(TEXT("same exact source ghost count"),int32(Left.ghost_cells.size()),int32(Right.ghost_cells.size()))) return false;
        for (size_t J=0;J<Left.ghost_cells.size();++J)
        {
            const auto& L=Left.ghost_cells[J]; const auto& R=Right.ghost_cells[J];
            if (!TestTrue(TEXT("shared atlas preserves ghost bed/h/u/v"),L.bed==R.bed && L.h==R.h && L.u==R.u && L.v==R.v)) return false;
            ++Ghosts;
        }
    }
    for (int32 Step=0;Step<10;++Step)
    { Shared->Step(.037f); Reference->Step(.037f); if (!TestTrue(TEXT("shared/dense evolution remains bit-exact"),Compare())) return false; }
    auto Shifted=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("shifted_packet"),TEXT("analytic"),Center,Extent,.035f,Error,false);
    if (!TestTrue(*FString::Printf(TEXT("second source packet shares atlas: %s"),*Error),Shifted.IsValid())) return false;
    TestEqual(TEXT("second packet does not reread or hash shared arrays"),FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting(),Loaded);
    auto Missing=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("valid"),TEXT("analytic"),Center+FVector2D(2.,0.),Extent,.035f,Error,false);
    TestFalse(TEXT("unknown captured water in ghost footprint is not filled as dry"),Missing.IsValid());
    TestTrue(TEXT("missing-state rejection is explicit"),Error.Contains(TEXT("unavailable")));
    Missing=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("physical_dry_exterior"),TEXT("analytic"),
        Center+FVector2D(2.,0.),Extent,.035f,Error,false);
    TestFalse(TEXT("captured-dry exterior cannot replace a wet physical inlet/outlet"),Missing.IsValid());
    TestTrue(TEXT("physical-exterior state rejection is explicit"),Error.Contains(TEXT("unavailable")));
    for (const TCHAR* Name:{TEXT("bad_bed"),TEXT("bad_mask"),TEXT("wrong_grid"),TEXT("wrong_datum"),TEXT("wrong_tolerance"),
        TEXT("legacy"),TEXT("mixed_dense"),TEXT("bad_manifest_hash"),TEXT("bad_array_hash"),TEXT("duplicate_tile"),
        TEXT("wet_artificial_edge"),TEXT("fractional_tile"),TEXT("float32"),TEXT("nonfinite")})
    {
        auto Bad=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/Name,TEXT("analytic"),Center,Extent,.035f,Error,false);
        TestFalse(*FString::Printf(TEXT("invalid shared source %s rejected"),Name),Bad.IsValid());
        TestFalse(TEXT("failed source supplies a reason"),Error.IsEmpty());
    }
    auto Reload=FRaftSimLiveWaterWindow::CreateFromCookedFields(Base/TEXT("valid"),TEXT("analytic"),Center,Extent,.035f,Error,false);
    TestTrue(TEXT("failed atlas replacements retain the verified cache"),Reload.IsValid());
    TestEqual(TEXT("no successful extra atlas loads"),FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting(),Loaded);
    AddInfo(FString::Printf(TEXT("Four-tile shared atlas matches dense state, %d ghost cells and ten live steps exactly; second packet uses verified cache; unavailable and malformed sources rejected. Analytic loader test only."),Ghosts));
    for (const TCHAR* Fixture : {TEXT("tmp/south-fork-runtime-atlas-201s-v1-20260912"),
        TEXT("tmp/south-fork-runtime-atlas-301s-v1-20260912"),
        TEXT("tmp/south-fork-runtime-atlas-600s-v1-20260912")})
    {
    const FString River=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Fixture);
    FString Text;
    TSharedPtr<FJsonObject> Windows;
    FFileHelper::LoadFileToString(Text,*(River/TEXT("validation_windows.json")));
    FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Windows);
    if (!TestTrue(TEXT("actual source-exact river export is available"),Windows.IsValid())) return false;
    const auto& Cases=Windows->GetArrayField(TEXT("windows"));
    TestEqual(TEXT("three independently exported full-size river references"),Cases.Num(),3);
    const int32 BeforeRiver=FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting();
    int64 ComparedCells=0;
    int64 PresentationCells=0, UnavailableDryCells=0;
    double MaxPresentationError=0.;
    for (const auto& Value:Cases)
    {
        const auto Case=Value->AsObject();
        const auto& P=Case->GetArrayField(TEXT("center_m"));
        const FVector2D RiverCenter(P[0]->AsNumber(),P[1]->AsNumber());
        Shared=FRaftSimLiveWaterWindow::CreateFromCookedFields(River/Case->GetStringField(TEXT("shared")),
            TEXT("median_runnable"),RiverCenter,FVector2D(224.,224.),.035f,Error,false);
        if (!TestTrue(*FString::Printf(TEXT("actual river shared state loads: %s"),*Error),Shared.IsValid())) return false;
        Reference=FRaftSimLiveWaterWindow::CreateFromCookedFields(River/Case->GetStringField(TEXT("dense")),
            TEXT("median_runnable"),RiverCenter,FVector2D(224.,224.),.035f,Error,false);
        if (!TestTrue(*FString::Printf(TEXT("independent dense river state loads: %s"),*Error),Reference.IsValid())) return false;
        TestTrue(TEXT("full river crop was not shortened"),Shared->Solver->scenario().grid.nx>=225 && Shared->Solver->scenario().grid.ny>=225);
        TestEqual(TEXT("actual river datum agrees exactly"),Shared->ElevationDatumM,Reference->ElevationDatumM);
        if (!TestTrue(TEXT("actual river shared/dense state is bit-exact"),Compare())) return false;
        const auto& Grid = Reference->Solver->scenario().grid;
        const auto& State = Reference->Solver->state();
        for (size_t Y=0; Y<Grid.ny; ++Y) for (size_t X=0; X<Grid.nx; ++X)
        {
            const FVector2D Position = Reference->OriginM + FVector2D(X*double(Reference->CellXM),Y*double(Reference->CellYM));
            const auto Source = Shared->SamplePresentationSource(Position);
            if (!Source.bValid)
            {
                // Captured-dry packet context may lie outside the solved
                // atlas; it is not an invented source surface. No wet cell
                // from the independent source may be lost at a tile seam.
                if (!TestTrue(TEXT("unavailable source contains no solved water"),State.h(Y,X)==0.)) return false;
                ++UnavailableDryCells;
                continue;
            }
            const double Bed = Reference->Solver->scenario().bed(Y,X) + Reference->ElevationDatumM;
            const double Depth = State.h(Y,X);
            for (const double Difference : {double(Source.DepthM)-float(Depth),
                double(Source.BedHeightM)-float(Bed), double(Source.SurfaceHeightM)-float(Bed+Depth),
                Source.VelocityMps.X-float(State.u(Y,X)), Source.VelocityMps.Y-float(State.v(Y,X))})
                MaxPresentationError=FMath::Max(MaxPresentationError,FMath::Abs(Difference));
            ++PresentationCells;
        }
        for (int32 Step=0;Step<3;++Step)
        {
            Shared->Step(.005f); Reference->Step(.005f);
            if (!TestTrue(TEXT("actual river shared/dense evolution is bit-exact"),Compare())) return false;
        }
        ComparedCells+=Shared->Solver->state().h.size();
        TestEqual(TEXT("river atlas is loaded only once across real source packets"),
            FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting(),BeforeRiver+1);
    }
    AddInfo(FString::Printf(TEXT("Actual South Fork atlas %s: %lld cells across three full224m windows match independent dense export and three live steps bit-exact; one shared dataset load. Transient diagnostic, NOT normal-map or settled-flow acceptance."),Fixture,ComparedCells));
    TestTrue(TEXT("real baseline samples all modeled terrain and water without fabricated fields"),MaxPresentationError<1.e-4 && PresentationCells>10000);
    AddInfo(FString::Printf(TEXT("Real source baseline %s: %lld modeled cells, %lld unavailable dry-context cells, maximum field error %.12g."),Fixture,PresentationCells,UnavailableDryCells,MaxPresentationError));
    }
    return !HasAnyErrors();
}
#endif
