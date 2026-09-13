#include "RaftSimLiveWaterWindow.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimExactWaterOverlapTest,
    "RaftSim.M3.CartesianWindowExactOverlap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimExactWaterOverlapTest::RunTest(const FString&)
{
    // Use the actual native solver state, not its float-valued render sampler.
    auto Source = FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5432., 3600.),
        12, 12, 1, 3, 2);
    if (!TestTrue(TEXT("native source window"), Source.IsValid())) return false;
    auto Seed = Source->Solver->state();
    for (int32 R = 0; R < 12; ++R)
    {
        for (int32 C = 0; C < 12; ++C)
        {
            Seed.h(R,C) = (R+C)%3 == 0 ? .0000100000000123 : 1.1234567890123 + R*.031 + C*.017;
            Seed.u(R,C) = .23456789012345 + R*.009;
            Seed.v(R,C) = -.3456789012345 - C*.007;
        }
    }
    Source->Solver->replace_state(MoveTemp(Seed), 12.3456789012345);
    Source->StepCounter = 789;
    const auto& Before = Source->Solver->state();
    const auto RenderSample = Source->Sample(Source->OriginM);
    TestTrue(TEXT("fixture exposes old float rounding"), double(RenderSample.DepthM) != Before.h(0,0));
    TestFalse(TEXT("fixture exposes presentation threshold suppressing wet solver motion"), RenderSample.bWet);
    TestTrue(TEXT("solver really considers shallow fixture wet"), Before.wet(0,0));

    int32 ExactCellCount = 0;
    for (const FIntPoint Shift : {FIntPoint(0,0), FIntPoint(3,0), FIntPoint(-3,0),
            FIntPoint(0,3), FIntPoint(0,-3), FIntPoint(3,2), FIntPoint(-3,-2),
            FIntPoint(-3,2), FIntPoint(3,-2), FIntPoint(20,20)})
    {
        auto Target = FRaftSimLiveWaterWindow::CreateFlatTank(
            FVector2D(-5432.+Shift.X, 3600.+Shift.Y), 12, 12, 1, 3, 2);
        const int32 Expected = FMath::Max(0,12-FMath::Abs(Shift.X)) * FMath::Max(0,12-FMath::Abs(Shift.Y));
        TestEqual(TEXT("exact intersection count in either axis"), Target->TransferOverlapStateFrom(*Source), Expected);
        TestEqual(TEXT("only overlapping windows inherit simulation time"), Target->SimTimeSeconds(), Expected ? Source->SimTimeSeconds() : 0.);
        TestEqual(TEXT("only overlapping windows inherit step count"), Target->StepCount(), Expected ? uint64(789) : uint64(0));
        const auto& After = Target->Solver->state();
        for (int32 R = 0; R < 12; ++R)
        {
            for (int32 C = 0; C < 12; ++C)
            {
                const int32 SR = R+Shift.Y, SC = C+Shift.X;
                if (SR < 0 || SR >= 12 || SC < 0 || SC >= 12)
                {
                    TestTrue(TEXT("newly exposed cell keeps cooked seed"),
                        After.h(R,C) == 2. && After.u(R,C) == 0. && After.v(R,C) == 0.);
                    continue;
                }
                TestTrue(TEXT("depth, both velocities, momenta and wet state retain exact solver values"),
                    After.h(R,C) == Before.h(SR,SC) && After.u(R,C) == Before.u(SR,SC) &&
                    After.v(R,C) == Before.v(SR,SC) && After.hu(R,C) == Before.hu(SR,SC) &&
                    After.hv(R,C) == Before.hv(SR,SC) && After.wet(R,C) == Before.wet(SR,SC));
                ++ExactCellCount;
            }
        }
    }
    // Repeated same-lattice handoffs must not accumulate rounding changes.
    auto Repeated = FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5432.,3600.),12,12,1,3,2);
    Repeated->TransferOverlapStateFrom(*Source);
    for (int32 Index = 0; Index < 100; ++Index)
    {
        auto Next = FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5432.,3600.),12,12,1,3,2);
        TestEqual(TEXT("repeated full intersection"), Next->TransferOverlapStateFrom(*Repeated), 144);
        Repeated = MoveTemp(Next);
    }
    TestEqual(TEXT("100 handoffs do not change total water volume"), Repeated->TotalWaterVolumeM3(), Source->TotalWaterVolumeM3());
    TestEqual(TEXT("100 handoffs preserve shallow momentum"), Repeated->Solver->state().hu(0,0), Before.hu(0,0));

    auto Nonaligned = FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5431.5,3600.5),12,12,1,3,2);
    TestEqual(TEXT("nonaligned legacy grid still uses its spatial overlap"), Nonaligned->TransferOverlapStateFrom(*Source), 121);
    const auto Interpolated = Source->Sample(Nonaligned->OriginM);
    TestEqual(TEXT("nonaligned cell is interpolated, never snapped to a nearby index"),
        Nonaligned->Solver->state().h(0,0), double(Interpolated.DepthM));
    AddInfo(FString::Printf(TEXT("%d exact shared cells across signed XY moves; 100 repeated handoffs retain volume and shallow momentum"), ExactCellCount));
    return !HasAnyErrors();
}
#endif
