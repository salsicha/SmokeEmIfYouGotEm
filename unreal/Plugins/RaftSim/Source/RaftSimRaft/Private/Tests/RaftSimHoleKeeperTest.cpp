#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimHoleChurn.h"
#include "RaftSimHoleLab.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
namespace
{
struct FHoleRun
{
    bool bRan = false;
    double FinalXM = 0.0;
    /** Longest stretch spent stopped in the hole (between the crest and
     * just past the boil line), seconds. */
    double HeldSeconds = 0.0;
    double MaximumRollDegrees = 0.0;
    double FirstCapsizeSeconds = -1.0;
    double FirstSwimmerSeconds = -1.0;
    int32 Swimmers = 0;
    bool bGuideSwimming = false;
    FString Summary() const
    {
        return FString::Printf(TEXT("x %.1f held %.1f roll %.0f capsize %.1f swimmers %d%s"), FinalXM, HeldSeconds,
            MaximumRollDegrees, FirstCapsizeSeconds, Swimmers, bGuideSwimming ? TEXT(" (guide)") : TEXT(""));
    }
};

enum class EHoleCrew : uint8 { Drift, Paddle, HighSide };

// The production raft and crew through the test hole, under play's capsize
// gate and washout rules, its crew paddling forward or not.
FHoleRun RunHole(FAutomationTestBase& Test, UWorld* World, const FRaftSimHoleLab& Lab, const TCHAR* Label,
    FVector StartCm, double SpeedMps, double YawDegrees, EHoleCrew Crew, double Seconds, bool bVerbose)
{
    FHoleRun Run;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    ON_SCOPE_EXIT
    {
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It) if (It->GetOwner() == Raft) World->DestroyActor(*It);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Runtime = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Runtime->ConfigureRaftBody(Raft->MakeProductionBodyConfig());
    Raft->ConfigureProductionFlexModel(*Runtime);
    if (!Test.TestTrue(TEXT("the production raft rides the test hole"), Raft->BindIsolatedFlipRuntime(Runtime, false)))
    {
        return Run;
    }
    Runtime->SetWaterSurfaceSampler([&Lab](const FVector& P, float& H) { H = float(Lab.Hull(P).SurfaceM * 100.0); return true; });
    Runtime->SetFlexibleWaterFieldSampler([&Lab](const FVector& P, FRaftSimFlexUniformWater& W)
    {
        const RaftSimHoleWave::FHullWater Hull = Lab.Hull(P);
        W.bWet = true; W.SurfaceHeightM = Hull.SurfaceM; W.VelocityMps = Hull.VelocityMps;
        return true;
    });
    Runtime->SetWaterSurfaceSlopeSampler([&Lab](const FVector& P, FVector2D& Slope) { Slope = Lab.Hull(P).Slope; return true; });
    StartCm.Z = Lab.SurfaceM(StartCm) * 100.0;
    FRaftSimRaftKinematicState Initial;
    Initial.WorldTransform = FTransform(FRotator(0.0, YawDegrees, 0.0), StartCm);
    Initial.LinearVelocityMetersPerSecond = FVector(SpeedMps, 0.0, 0.0);
    Runtime->SetKinematicState(Initial);
    Raft->SetActorTransform(Initial.WorldTransform);
    if (Crew == EHoleCrew::Paddle)
    {
        Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    }
    else if (Crew == EHoleCrew::HighSide)
    {
        Raft->IssueCrewCommand(ERaftSimCrewCommand::HighSide);
    }
    const double HoleEndM = Lab.Wave.BoilAlong() + 0.5;
    double Stopped = 0.0;
    const int32 Steps = FMath::RoundToInt(Seconds * 120.0);
    for (int32 Step = 0; Step < Steps; ++Step)
    {
        if (!Raft->AdvanceIsolatedFlipDemo(1.0f / 120.0f, true))
        {
            Test.AddError(FString::Printf(TEXT("%s: the raft's step failed"), Label));
            return Run;
        }
        // The crew's poses and strokes on a 30 Hz frame clock, as in play.
        if (Step % 4 == 3)
        {
            Raft->RefreshIsolatedFlipVisual(4.0f / 120.0f);
        }
        const double T = double(Step + 1) / 120.0;
        const FRaftSimRaftKinematicState& K = Runtime->GetKinematicState();
        const FVector P = K.WorldTransform.GetLocation() * 0.01;
        const FRotator R = K.WorldTransform.Rotator();
        Run.MaximumRollDegrees = FMath::Max(Run.MaximumRollDegrees, FMath::Abs(double(R.Roll)));
        const bool bInHole = P.X > 0.0 && P.X < HoleEndM && FMath::Abs(K.LinearVelocityMetersPerSecond.X) < 0.6;
        Stopped = bInHole ? Stopped + 1.0 / 120.0 : 0.0;
        Run.HeldSeconds = FMath::Max(Run.HeldSeconds, Stopped);
        if (Run.FirstCapsizeSeconds < 0.0 && Raft->GetRaftMode() != ERaftSimRaftMode::Upright) Run.FirstCapsizeSeconds = T;
        if (Run.FirstSwimmerSeconds < 0.0 && Raft->GetSwimmerCount() > 0) Run.FirstSwimmerSeconds = T;
        Run.Swimmers = FMath::Max(Run.Swimmers, Raft->GetSwimmerCount());
        Run.bGuideSwimming |= Raft->IsPassengerSwimming(TEXT("guide"));
        if (bVerbose && Step % 60 == 59)
        {
            Test.AddInfo(FString::Printf(TEXT("%s t=%4.1f x=%5.2f y=%5.2f z=%5.2f yaw=%4.0f roll=%4.0f pitch=%4.0f u=%5.2f swimmers=%d %s"),
                Label, T, P.X, P.Y, P.Z, R.Yaw, R.Roll, R.Pitch, K.LinearVelocityMetersPerSecond.X, Raft->GetSwimmerCount(),
                Raft->GetRaftMode() == ERaftSimRaftMode::Upright ? TEXT("") : TEXT("CAPSIZED")));
        }
    }
    Run.FinalXM = Runtime->GetKinematicState().WorldTransform.GetLocation().X * 0.01;
    Run.bRan = true;
    if (bVerbose)
    {
        Test.AddInfo(FString::Printf(TEXT("%s: %s, first swimmer %.1f s"), Label, *Run.Summary(), Run.FirstSwimmerSeconds));
    }
    return Run;
}

struct FHoleScenarios
{
    FHoleRun Drift, Backward, Paddle, Side, SideHighSide;
    bool Ran() const { return Drift.bRan && Backward.bRan && Paddle.bRan && Side.bRan && SideHighSide.bRan; }
};

FHoleScenarios RunScenarios(FAutomationTestBase& Test, UWorld* World, const FRaftSimHoleLab& Lab, bool bVerbose)
{
    FHoleScenarios S;
    // Drifting in a little off straight: the bow climbs the breaking wave,
    // the stern sits under the falling water.
    S.Drift = RunHole(Test, World, Lab, TEXT("drift"), FVector(-900.0, 0.0, 0.0), 2.2, 4.0, EHoleCrew::Drift, 20.0, bVerbose);
    // Drifting in backwards: the bow ends up under the falling water.
    S.Backward = RunHole(Test, World, Lab, TEXT("backward"), FVector(-900.0, 0.0, 0.0), 2.2, 176.0, EHoleCrew::Drift, 20.0, bVerbose);
    // The crew paddling forward from well upstream.
    S.Paddle = RunHole(Test, World, Lab, TEXT("paddle"), FVector(-900.0, 0.0, 0.0), 2.2, 4.0, EHoleCrew::Paddle, 20.0, bVerbose);
    // Side-on in the hole, then the same with the crew high-siding.
    S.Side = RunHole(Test, World, Lab, TEXT("side"), FVector(330.0, 0.0, 0.0), 0.0, 90.0, EHoleCrew::Drift, 16.0, bVerbose);
    S.SideHighSide = RunHole(Test, World, Lab, TEXT("highside"), FVector(330.0, 0.0, 0.0), 0.0, 90.0, EHoleCrew::HighSide, 16.0, bVerbose);
    return S;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHoleKeeperTest, "RaftSim.Physics.HoleKeeper",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHoleKeeperTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard Guard;
    UWorld* World = nullptr;
    for (const auto& C : GEngine->GetWorldContexts()) if (C.WorldType == EWorldType::Editor) { World = C.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    FRaftSimHoleChurnSite Drawn;
    Drawn.Look = FRaftSimHoleChurnLook::Preset(TEXT("roll"));
    const RaftSimHoleWave::FShape Wave = URaftSimHoleChurnComponent::ShapeOf(Drawn);

    // Development sweep (-RaftSimHoleSweep): the scenarios across the
    // breaking wave's bearing and roll, reported, not judged.
    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimHoleSweep")))
    {
        for (const double CrestM : {0.6, 0.8, 1.0, 1.2})
        {
            for (const double Length : {2.0, 3.0})
            {
                const RaftSimHoleWave::FShape Swept = RaftSimHoleWave::FShape::ForCrest(CrestM, Length, 1.0);
                const FRaftSimHoleLab Lab(Swept, float(CrestM), float(Length));
                const FHoleScenarios S = RunScenarios(*this, World, Lab, false);
                AddInfo(FString::Printf(TEXT("SWEEP crest %.1f length %.0f (roll %.2f depth %.2f) | drift %s | backward %s | paddle %s | side %s | highside %s"),
                    CrestM, Length, Swept.RollMps, Swept.ReturnDepthM, *S.Drift.Summary(), *S.Backward.Summary(), *S.Paddle.Summary(), *S.Side.Summary(), *S.SideHighSide.Summary()));
            }
        }
        return true;
    }

    const FRaftSimHoleLab Lab(Wave);
    const FHoleScenarios S = RunScenarios(*this, World, Lab, true);
    if (!S.Ran()) return false;
    const double Boil = Lab.Wave.BoilAlong();
    TestTrue(TEXT("a drifting raft is held in the hole"), S.Drift.HeldSeconds > 8.0 && S.Drift.FinalXM < Boil + 2.0);
    TestTrue(TEXT("with the stern under the falling water it does not flip (the crew's weight holds it)"),
        S.Drift.FirstCapsizeSeconds < 0.0);
    TestTrue(TEXT("drifting in backwards it is held too"), S.Backward.HeldSeconds > 8.0);
    TestTrue(TEXT("with the bow under the falling water it does not flip"), S.Backward.FirstCapsizeSeconds < 0.0);
    TestTrue(TEXT("a crew paddling forward punches through"), S.Paddle.FinalXM > Boil + 5.0);
    TestTrue(TEXT("side-on, the falling water washes out the paddlers on that side"), S.Side.Swimmers > 0);
    TestTrue(TEXT("high-siding keeps the raft from flipping"), S.SideHighSide.FirstCapsizeSeconds < 0.0);
    return true;
}
#endif
