#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Misc/CommandLine.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "UObject/Package.h"
#include "../RaftSimRunManager.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRunProgressCoordinatesTest,
    "RaftSim.Survey.RunProgressDistinctFromRapidHydraulics",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimRunProgressCoordinatesTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("coordinate fixture world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Run = World->SpawnActor<ARaftSimRunManager>();
    if (!TestNotNull(TEXT("real run manager"), Run)) return false;
    TestFalse(TEXT("no progress observation exists before sampling"), Run->GetLastProgressSample().bValid);
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>();
    const FString Base = TEXT("physics/data/real_world/south_fork_american_chili_bar/"
        "reconstruction_2026_09/full_reach/");
    if (!TestTrue(TEXT("rigid joined rapid coordinates load"),
            Water->ConfigureRiverCoordinateMap(Base + TEXT("rapid_join_flow/coordinate_map.json")))) return false;
    TestTrue(TEXT("unconfigured legacy runs still use hydraulic coordinates"),
        Run->GetProgressCoordinates(Water) == Water);
    if (!TestTrue(TEXT("run binds the full South Fork descent axis"),
            Run->ConfigureProgressCoordinateMap(Base + TEXT("playable_route/coordinate_map.json")))) return false;
    const auto* Progress = Run->GetProgressCoordinates(Water);
    if (!TestNotNull(TEXT("global progress map retained by run manager"), Progress)) return false;
    TestTrue(TEXT("progress is distinct from solver-local coordinates"), Progress != Water);
    float Minimum = 0, Maximum = 0;
    TestTrue(TEXT("full route range is available"), Progress->GetRiverStationRangeM(Minimum, Maximum));
    TestTrue(TEXT("river finish has not become the rapid's end"),
        Minimum == 0 && FMath::Abs(Maximum - 33334.1463936) < .01);
    FVector Origin, Tangent, Left;
    FVector2D Global, Local;
    TestTrue(TEXT("rapid origin maps to full river world"),
        Water->RiverToWorldPosition(FVector2D::ZeroVector, 220, Origin));
    TestTrue(TEXT("same world position projects onto global progress"),
        Run->WorldToRunCoordinates(Origin, Water, Global, Tangent, Left));
    AddInfo(FString::Printf(TEXT("Rapid origin global station %.9f m, lateral %.9f m"), Global.X, Global.Y));
    TestTrue(TEXT("Troublemaker is about 8.344 km into South Fork, not station zero"),
        FMath::Abs(Global.X - 8343.945510) < .01);
    TestTrue(TEXT("rapid local coordinates remain unchanged"),
        Water->WorldToRiverCoordinates(Origin, Local, Tangent, Left));
    TestTrue(TEXT("hydraulic origin remains local zero"), Local.Size() < .0001);
    FVector SectionStart;
    TestTrue(TEXT("a global section start is placed with the descent axis"),
        Progress->RiverToWorldPosition(FVector2D(Global.X, 0), 227, SectionStart));
    TestTrue(TEXT("section world position converts back to the local hydraulic window"),
        Water->WorldToRiverCoordinates(SectionStart, Local, Tangent, Left));
    TestTrue(TEXT("window seed is nearby local metres, never 8344 local metres"), Local.Size() < 3.);
    TestFalse(TEXT("distant unsupported world position does not create progress"),
        Run->WorldToRunCoordinates(FVector(1e9, 1e9, 0), Water, Global, Tangent, Left));
    double MaximumStationError = 0;
    for (int32 Pass = 0; Pass < 2; ++Pass)
    {
        for (int32 Index = 0; Index <= 1000; ++Index)
        {
            const int32 SampleIndex = Pass == 0 ? Index : (Index * 137) % 1001;
            const double Station = Maximum * static_cast<double>(SampleIndex) / 1000.;
            FVector Position;
            if (!Progress->RiverToWorldPosition(FVector2D(Station, 0), 227, Position) ||
                !Run->WorldToRunCoordinates(Position, Water, Global, Tangent, Left))
            {
                AddError(FString::Printf(TEXT("Missing global progress at %.9f m"), Station));
                return false;
            }
            MaximumStationError = FMath::Max(MaximumStationError, FMath::Abs(Global.X - Station));
        }
    }
    AddInfo(FString::Printf(TEXT("2002 downstream/scrambled progress queries, max station error %.9f m"), MaximumStationError));
    TestTrue(TEXT("global progress retains one-centimetre chainage accuracy across the full descent"), MaximumStationError < .01);

    AddExpectedError(TEXT("RaftSim coordinate map not found"), EAutomationExpectedErrorFlags::Contains, 1);
    TestFalse(TEXT("invalid explicitly configured global path is rejected"),
        Run->ConfigureProgressCoordinateMap(Base + TEXT("missing-progress-coordinate-test.json")));
    TestTrue(TEXT("invalid global path never silently falls back to rapid progress"),
        Run->GetProgressCoordinates(Water) == nullptr);
    TestTrue(TEXT("explicitly clearing override restores legacy behavior"), Run->ConfigureProgressCoordinateMap(TEXT("")));
    TestTrue(TEXT("legacy adapter identity retained"), Run->GetProgressCoordinates(Water) == Water);
    auto* CartesianWater = NewObject<URaftSimWaterRuntimeAdapter>();
    TestTrue(TEXT("geographic water coordinates load separately"),
        CartesianWater->ConfigureRiverCoordinateMap(Base + TEXT("hydraulic_regions_context/coordinate_map.json")));
    TestTrue(TEXT("unconfigured progress cannot use hydraulic east/north"),
        Run->GetProgressCoordinates(CartesianWater) == nullptr);
    TestFalse(TEXT("unconfigured run never treats easting as score progress"),
        Run->WorldToRunCoordinates(Origin, CartesianWater, Global, Tangent, Left));
    TestTrue(TEXT("global run axis can accompany Cartesian water"),
        Run->ConfigureProgressCoordinateMap(Base + TEXT("playable_route/coordinate_map.json")));
    TestTrue(TEXT("Cartesian water and downstream progress remain independent"),
        Run->WorldToRunCoordinates(Origin, CartesianWater, Global, Tangent, Left) &&
        FMath::Abs(Global.X - 8343.945510) < .01);
    TestFalse(TEXT("Cartesian map is rejected as an explicitly configured progress map"),
        Run->ConfigureProgressCoordinateMap(Base + TEXT("hydraulic_regions_context/coordinate_map.json")));
    TestTrue(TEXT("rejected Cartesian progress cannot survive as a partial binding"),
        Run->GetProgressCoordinates(CartesianWater) == nullptr);
    Run->RestartRun();
    TestFalse(TEXT("restart never exposes an old progress observation"), Run->GetLastProgressSample().bValid);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimReviewDownstreamCoordinatesTest,
    "RaftSim.Survey.ReviewCameraUsesScenarioDownstream",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimReviewDownstreamCoordinatesTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("review fixture world"), World)) return false;
    GEngine->CreateNewWorldContext(EWorldType::Editor).SetCurrentWorld(World);
    ON_SCOPE_EXIT { World->DestroyWorld(false); GEngine->DestroyWorldContext(World); World->RemoveFromRoot(); };
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>();
    const FString Base = TEXT("physics/data/real_world/south_fork_american_chili_bar/"
        "reconstruction_2026_09/full_reach/");
    if (!TestTrue(TEXT("original Cartesian map loads"), Water->ConfigureRiverCoordinateMap(
        Base + TEXT("hydraulic_regions_context/coordinate_map.json")))) return false;
    FVector Position(-543792.4, -360843.6, 736.8);
    FVector Location, Tangent, Left;
    FRotator Rotation;
    FVector2D Coordinates;
    TestNull(TEXT("no provider never converts Cartesian axes into a river"),
        RaftSimReviewCoordinates::GetMap(World, Water));
    TestFalse(TEXT("shore camera without downstream evidence fails"),
        RaftSimReviewCoordinates::ShorePose(World, Water, Position, true, false, false, Location, Rotation));
    auto* Run = World->SpawnActor<ARaftSimRunManager>();
    if (!TestNotNull(TEXT("real scenario provider"), Run)) return false;
    TestNotNull(TEXT("run exposes the plugin interface without a game-module dependency"),
        Cast<IRaftSimRunCoordinateProvider>(Run));
    if (!TestTrue(TEXT("authored downstream axis loads"), Run->ConfigureProgressCoordinateMap(
        Base + TEXT("playable_route/coordinate_map.json")))) return false;
    TestTrue(TEXT("review uses exactly the scenario's retained map"),
        RaftSimReviewCoordinates::GetMap(World, Water) == Run->GetProgressCoordinates(Water));
    if (!TestTrue(TEXT("original capture position projects onto the scenario"),
        Run->WorldToRunCoordinates(Position, Water, Coordinates, Tangent, Left))) return false;
    FVector2D ReviewCoordinates;
    FVector ReviewTangent, ReviewLeft;
    TestTrue(TEXT("review query succeeds"), RaftSimReviewCoordinates::WorldToCoordinates(
        World, Water, Position, ReviewCoordinates, ReviewTangent, ReviewLeft));
    TestTrue(TEXT("review preserves exact authoritative nearest-polyline results"),
        ReviewCoordinates == Coordinates && ReviewTangent == Tangent && ReviewLeft == Left);
    TestTrue(TEXT("Troublemaker downstream is west, not the east hydraulic axis"), Tangent.X < -.5);
    TestTrue(TEXT("river-left preserves the map's Y reflection"),
        Left.Equals(FVector(Tangent.Y, -Tangent.X, 0), 1e-10));
    for (bool bLow : {false, true})
        for (bool bLeft : {false, true})
        {
            TestTrue(TEXT("both banks and camera heights resolve"),
                RaftSimReviewCoordinates::ShorePose(World, Water, Position, bLeft, bLow, false, Location, Rotation));
            const FVector ExpectedLocation = Position - Tangent * 300. + FVector::UpVector * (bLow ? 70. : 320.);
            const FVector Target = Position + (bLeft ? Left : -Left) * (bLow ? 2200. : 1500.) +
                Tangent * (bLow ? 600. : 1400.) + FVector::UpVector * (bLow ? 40. : 0.);
            TestTrue(TEXT("camera uses unchanged offsets in the downstream frame"), Location.Equals(ExpectedLocation, 1e-7));
            TestTrue(TEXT("camera points at the requested downstream bank"),
                Rotation.Vector().Equals((Target - Location).GetSafeNormal(), 1e-10));
            TestTrue(TEXT("explicit old-frame control resolves"),
                RaftSimReviewCoordinates::ShorePose(World, Water, Position, bLeft, bLow, true, Location, Rotation));
            const FVector OldLocation = Position - FVector::ForwardVector * 300. + FVector::UpVector * (bLow ? 70. : 320.);
            const FVector OldTarget = Position + FVector(0, bLeft ? -1. : 1., 0) * (bLow ? 2200. : 1500.) +
                FVector::ForwardVector * (bLow ? 600. : 1400.) + FVector::UpVector * (bLow ? 40. : 0.);
            TestTrue(TEXT("comparison preserves original camera location"), Location.Equals(OldLocation, 1e-7));
            TestTrue(TEXT("comparison preserves original camera orientation"),
                Rotation.Vector().Equals((OldTarget - OldLocation).GetSafeNormal(), 1e-10));
        }
    TestTrue(TEXT("camera queries did not modify hydraulic coordinates"),
        Water->WorldToRiverCoordinates(Position, ReviewCoordinates, ReviewTangent, ReviewLeft) &&
        ReviewCoordinates.Equals(FVector2D(Position.X / 100., -Position.Y / 100.), 1e-10) &&
        ReviewTangent == FVector::ForwardVector && ReviewLeft == FVector(0, -1, 0));
    TestFalse(TEXT("outside the supported corridor never falls back east"),
        RaftSimReviewCoordinates::WorldToCoordinates(World, Water, FVector(1e9), ReviewCoordinates, ReviewTangent, ReviewLeft));
    auto* OtherRun = World->SpawnActor<ARaftSimRunManager>();
    if (!TestNotNull(TEXT("ambiguous provider fixture"), OtherRun)) return false;
    TestNull(TEXT("two scenario providers fail closed independent of actor order"),
        RaftSimReviewCoordinates::GetMap(World, Water));
    TestFalse(TEXT("ambiguous world never chooses an arbitrary bank"),
        RaftSimReviewCoordinates::ShorePose(World, Water, Position, true, false, false, Location, Rotation));
    OtherRun->Destroy();
    TestTrue(TEXT("clearing override succeeds"), Run->ConfigureProgressCoordinateMap(TEXT("")));
    TestNull(TEXT("invalid provider cannot fall back to Cartesian water"), RaftSimReviewCoordinates::GetMap(World, Water));
    auto* Legacy = NewObject<URaftSimWaterRuntimeAdapter>();
    if (!TestTrue(TEXT("legacy non-Cartesian map loads"), Legacy->ConfigureRiverCoordinateMap(
        Base + TEXT("rapid_join_flow/coordinate_map.json")))) return false;
    TestTrue(TEXT("legacy scenario still uses its hydraulic ribbon"),
        RaftSimReviewCoordinates::GetMap(World, Legacy) == Legacy);
    AddExpectedError(TEXT("RaftSim coordinate map not found"), EAutomationExpectedErrorFlags::Contains, 1);
    TestFalse(TEXT("broken explicit scenario path rejected"), Run->ConfigureProgressCoordinateMap(Base + TEXT("missing-review-axis.json")));
    TestNull(TEXT("broken explicit path never falls back even to a legacy ribbon"), RaftSimReviewCoordinates::GetMap(World, Legacy));
    Run->Destroy();
    TestTrue(TEXT("no-provider legacy worlds retain their original map"), RaftSimReviewCoordinates::GetMap(World, Legacy) == Legacy);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimReviewStartRangeTest,
    "RaftSim.Survey.ReviewStartUsesScenarioRange",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimReviewStartRangeTest::RunTest(const FString&)
{
    const FString PreviousCommandLine = FCommandLine::Get();
    ON_SCOPE_EXIT { FCommandLine::Set(*PreviousCommandLine); };
    // GetMapName uses the outer package, not the UWorld object's name.
    // A unique transient package models the scope without loading/saving a map.
    const FString PackageName = TEXT("/Temp/RaftSimReviewRange_") + FGuid::NewGuid().ToString() +
        TEXT("/L_SouthForkAmerican_FullReach");
    UPackage* Package = CreatePackage(*PackageName);
    Package->SetFlags(RF_Transient);
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false, TEXT("L_SouthForkAmerican_FullReach"), Package);
    if (!TestNotNull(TEXT("review range fixture world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    if (!TestEqual(TEXT("fixture has the real map-scoped name"),
        World->GetMapName(), FString(TEXT("L_SouthForkAmerican_FullReach")))) return false;
    auto* Run = World->SpawnActor<ARaftSimRunManager>();
    if (!TestNotNull(TEXT("actual run manager"), Run)) return false;
    const FString Path = TEXT("physics/data/real_world/south_fork_american_chili_bar/"
        "reconstruction_2026_09/full_reach/playable_route/coordinate_map.json");
    if (!TestTrue(TEXT("captured full-route range loads"), Run->ConfigureProgressCoordinateMap(Path))) return false;
    float Minimum = 0, Maximum = 0;
    if (!TestTrue(TEXT("actual route bounds available"),
        Run->GetProgressCoordinates(nullptr)->GetRiverStationRangeM(Minimum, Maximum))) return false;
    FRaftSimCareerScenarioDefinition Scenario;
    Scenario.ScenarioId = TEXT("range_test_original");
    Scenario.StartStationM = 10.f;
    Scenario.FinishStationM = 20.f;
    for (float Station : {Minimum, 8330.f, Maximum, Minimum - 1.f, Maximum + 1.f, 48000.f})
    {
        FCommandLine::Set(*FString::Printf(TEXT("-RaftSimWaterReviewStation=%.9f"), Station));
        Run->ConfigureSession(Scenario, ERaftSimGameMode::FreeRun);
        const bool bInside = Station >= Minimum && Station <= Maximum;
        TestEqual(TEXT("review start is accepted only inside the real route"),
            Run->StartStationM, bInside ? Station : Scenario.StartStationM);
        TestEqual(TEXT("review finish comes from the real route, not the old 48.9 km constant"),
            Run->FinishStationM, bInside ? Maximum : Scenario.FinishStationM);
        TestEqual(TEXT("rejected review leaves the selected scenario intact"),
            Run->ScenarioId, bInside ? FName(TEXT("south_fork_full_descent")) : Scenario.ScenarioId);
    }
    return true;
}
#endif
