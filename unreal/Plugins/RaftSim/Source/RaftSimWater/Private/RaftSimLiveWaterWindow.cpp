#include "RaftSimLiveWaterWindow.h"

#if RAFTSIM_HAS_LIVE_SOLVER

#include "raftsim_water/scenario.hpp"
#include "raftsim_water/solver.hpp"

namespace
{
// Clamp gameplay ticks so a hitch cannot explode the CFL substep count.
constexpr float kMaxStepSeconds = 0.1f;
}

FRaftSimLiveWaterWindow::FRaftSimLiveWaterWindow() = default;
FRaftSimLiveWaterWindow::~FRaftSimLiveWaterWindow() = default;

TUniquePtr<FRaftSimLiveWaterWindow> FRaftSimLiveWaterWindow::CreateFlatTank(
    const FVector2D& WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
    float SurfaceHeightM, float DepthM)
{
    const std::size_t Nx = FMath::Max<std::size_t>(8, static_cast<std::size_t>(SizeXM / CellSizeM));
    const std::size_t Ny = FMath::Max<std::size_t>(8, static_cast<std::size_t>(SizeYM / CellSizeM));

    raftsim::Scenario Scenario;
    Scenario.scenario_id = "raftsim_game_flat_tank";
    Scenario.scenario_type = "game_runtime";
    // No fixture_kind: nothing fixture-scoped can ever engage for game water.
    Scenario.fixture_kind.clear();
    Scenario.grid.nx = Nx;
    Scenario.grid.ny = Ny;
    Scenario.grid.dx = CellSizeM;
    Scenario.fixed_dt = 1.0 / 120.0;
    Scenario.duration = 1.0e9;
    Scenario.bed = raftsim::Array2D(Ny, Nx, SurfaceHeightM - DepthM);
    Scenario.initial.h = raftsim::Array2D(Ny, Nx, DepthM);
    Scenario.initial.u = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.v = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hu = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hv = raftsim::Array2D(Ny, Nx, 0.0);

    raftsim::SolverConfig Config;
    Config.solver_mode = "finite_volume";
    Config.flux_scheme = "hll";
    Config.spatial_order = 2;
    // Game water is always the genuine solver: never playback, never calibration.
    Config.disable_fixture_calibrations = true;

    TUniquePtr<FRaftSimLiveWaterWindow> Window(new FRaftSimLiveWaterWindow());
    Window->Solver = MakePimpl<raftsim::ReducedShallowWaterSolver>(
        MoveTemp(Scenario), Config);
    Window->OriginM = WorldOriginM;
    Window->CellM = CellSizeM;
    return Window;
}

void FRaftSimLiveWaterWindow::Step(float DtSeconds)
{
    if (Solver.IsValid() && DtSeconds > 0.0f)
    {
        Solver->step(FMath::Min(DtSeconds, kMaxStepSeconds));
        ++StepCounter;
    }
}

double FRaftSimLiveWaterWindow::SimTimeSeconds() const
{
    return Solver.IsValid() ? Solver->time() : 0.0;
}

FRaftSimLiveWaterSampleResult FRaftSimLiveWaterWindow::Sample(
    const FVector2D& WorldPositionM) const
{
    FRaftSimLiveWaterSampleResult Result;
    if (!Solver.IsValid())
    {
        return Result;
    }
    const raftsim::Scenario& Scenario = Solver->scenario();
    const raftsim::WaterState& State = Solver->state();

    const double GridX = (WorldPositionM.X - OriginM.X) / CellM - 0.5;
    const double GridY = (WorldPositionM.Y - OriginM.Y) / CellM - 0.5;
    const std::size_t Nx = Scenario.grid.nx;
    const std::size_t Ny = Scenario.grid.ny;
    if (Nx < 2 || Ny < 2)
    {
        return Result;
    }
    const double ClampedX = FMath::Clamp(GridX, 0.0, static_cast<double>(Nx - 2));
    const double ClampedY = FMath::Clamp(GridY, 0.0, static_cast<double>(Ny - 2));
    const std::size_t Col = static_cast<std::size_t>(ClampedX);
    const std::size_t Row = static_cast<std::size_t>(ClampedY);
    const double Fx = ClampedX - static_cast<double>(Col);
    const double Fy = ClampedY - static_cast<double>(Row);

    const auto Bilinear = [&](const raftsim::Array2D& Field) -> double
    {
        const double V00 = Field(Row, Col);
        const double V01 = Field(Row, Col + 1);
        const double V10 = Field(Row + 1, Col);
        const double V11 = Field(Row + 1, Col + 1);
        return FMath::Lerp(FMath::Lerp(V00, V01, Fx), FMath::Lerp(V10, V11, Fx), Fy);
    };

    const double Depth = Bilinear(State.h);
    const double Bed = Bilinear(Scenario.bed);
    Result.bValid = true;
    Result.DepthM = static_cast<float>(FMath::Max(Depth, 0.0));
    Result.BedHeightM = static_cast<float>(Bed);
    Result.SurfaceHeightM = static_cast<float>(Bed + FMath::Max(Depth, 0.0));
    Result.bWet = Depth > 1.0e-4;
    Result.VelocityMps = FVector2D(
        static_cast<float>(Bilinear(State.u)), static_cast<float>(Bilinear(State.v)));

    // Surface normal from central differences of the free surface.
    const auto SurfaceAt = [&](std::size_t R, std::size_t C) -> double
    { return Scenario.bed(R, C) + FMath::Max(State.h(R, C), 0.0); };
    const std::size_t CL = Col > 0 ? Col - 1 : Col;
    const std::size_t CR = FMath::Min(Col + 1, Nx - 1);
    const std::size_t RD = Row > 0 ? Row - 1 : Row;
    const std::size_t RU = FMath::Min(Row + 1, Ny - 1);
    const double DzDx = (SurfaceAt(Row, CR) - SurfaceAt(Row, CL)) /
                        (CellM * static_cast<double>(CR - CL == 0 ? 1 : CR - CL));
    const double DzDy = (SurfaceAt(RU, Col) - SurfaceAt(RD, Col)) /
                        (CellM * static_cast<double>(RU - RD == 0 ? 1 : RU - RD));
    Result.SurfaceNormal =
        FVector(static_cast<float>(-DzDx), static_cast<float>(-DzDy), 1.0f).GetSafeNormal();
    return Result;
}

#endif // RAFTSIM_HAS_LIVE_SOLVER
