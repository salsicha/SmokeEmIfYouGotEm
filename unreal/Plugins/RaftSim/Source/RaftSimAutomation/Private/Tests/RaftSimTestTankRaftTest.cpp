// P1 exit-gate behavioral test (release-1.0-plan.md §7 P1): the test-tank raft
// reaches buoyancy equilibrium on flat water and a paddle stroke moves it.

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimTestTankRaftFloatsAndPaddlesTest,
    "RaftSim.P1.TestTankRaftFloatsAndPaddles",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetActiveGameWorld()
{
    // Resolve by map identity, never by context order: sequential automation
    // tests leave the previous test's world alive until GC, and taking the
    // first live game world here measured M7's river raft as the "tank"
    // (2026-08-11: 0.39 kg of river overwash and 2.57 m/s of current carry
    // failed the calm-water asserts while the real tank raft sat parked at
    // origin — a standalone 150 s tank run showed speed 0.000 throughout).
    // Every newer test in this module already selects its own world; this
    // P1-era helper was the last first-world lookup.
    UWorld* NewestGameWorld = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        UWorld* World = Context.World();
        if (World == nullptr ||
            (Context.WorldType != EWorldType::PIE && Context.WorldType != EWorldType::Game))
        {
            continue;
        }
        if (World->GetMapName().Contains(TEXT("L_RaftSimTestTank")))
        {
            return World;
        }
        NewestGameWorld = World;
    }
    return NewestGameWorld;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertRaftSettledCommand, FAutomationTestBase*, Test);

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimStrokeAndMeasureCommand, FAutomationTestBase*, Test);

bool FRaftSimAssertRaftSettledCommand::Update()
{
    UWorld* World = GetActiveGameWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No active game world for the test tank"));
        return true;
    }
    ARaftSimRaftActor* Raft = nullptr;
    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        Raft = *It;
    }
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("L_RaftSimTestTank contains no ARaftSimRaftActor"));
        return true;
    }

    // After the settle window the raft must ride near the waterline: hull
    // center within one tube diameter of Z=0 and nearly at rest vertically.
    const float ZCm = Raft->GetActorLocation().Z;
    Test->TestTrue(
        TEXT("raft settled near waterline (|Z| < 60 cm)"), FMath::Abs(ZCm) < 60.0f);
    Test->TestTrue(
        TEXT("raft vertical velocity settled (< 0.5 m/s)"),
        FMath::Abs(Raft->GetRaftVelocity().Z) < 0.5f);
    Test->TestTrue(
        TEXT("test-tank runtime water is bound into live D3"),
        Raft->IsUsingLiveD3WaterField());
    Test->TestTrue(
        FString::Printf(
            TEXT("live D3 samples every tube segment (%d samples)"),
            Raft->GetLiveD3WaterSampleCount()),
        Raft->GetLiveD3WaterSampleCount() >= 12);
    Test->TestEqual(
        TEXT("flat tank reports all live D3 samples wet"),
        Raft->GetLiveD3WetSampleCount(),
        Raft->GetLiveD3WaterSampleCount());
    Test->TestTrue(
        FString::Printf(
            TEXT("calm zero-speed water retains no D3 load (%.6f kg)"),
            Raft->GetD3RetainedWaterMassKg()),
        Raft->GetD3RetainedWaterMassKg() < 0.001f);

    // Kick off the paddle phase: record position, stroke, and let it run.
    Raft->Tags.Add(FName(*FString::Printf(TEXT("P1StartX:%f"), Raft->GetActorLocation().X)));
    Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both, 1.0f);
    Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both, 1.0f);
    return true;
}

bool FRaftSimStrokeAndMeasureCommand::Update()
{
    UWorld* World = GetActiveGameWorld();
    ARaftSimRaftActor* Raft = nullptr;
    if (World != nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            Raft = *It;
        }
    }
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("Raft disappeared before stroke measurement"));
        return true;
    }

    float StartX = 0.0f;
    for (const FName& Tag : Raft->Tags)
    {
        FString TagString = Tag.ToString();
        if (TagString.RemoveFromStart(TEXT("P1StartX:")))
        {
            StartX = FCString::Atof(*TagString);
        }
    }
    const float TraveledCm = Raft->GetActorLocation().X - StartX;
    Test->TestTrue(
        FString::Printf(
            TEXT("two forward strokes moved the raft forward (traveled %.1f cm > 40 cm)"),
            TraveledCm),
        TraveledCm > 40.0f);
    Test->TestTrue(
        TEXT("raft still near waterline after strokes (|Z| < 60 cm)"),
        FMath::Abs(Raft->GetActorLocation().Z) < 60.0f);
    return true;
}

} // namespace

bool FRaftSimTestTankRaftFloatsAndPaddlesTest::RunTest(const FString&)
{
    // Force a fresh world even when the tank map is already loaded: M7's
    // audio test drives this same map and leaves the raft under a standing
    // AllForward cadence (2026-08-11: P1 after M7 measured that raft at
    // 2.44 m/s with 0.32 kg of its own bow-wave overwash and failed the
    // calm-water asserts; P1 alone was green all along).
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"), /*bForceReload=*/true);
    // Let buoyancy settle from the 40 cm spawn drop, then assert + stroke.
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertRaftSettledCommand(this));
    // Give the strokes three seconds to translate into hull motion.
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimStrokeAndMeasureCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
