#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/World.h"
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
#endif
