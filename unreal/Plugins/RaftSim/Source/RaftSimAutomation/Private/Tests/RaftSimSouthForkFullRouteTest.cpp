#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkFullRouteCoordinatesTest,
    "RaftSim.Survey.SouthForkFullRouteCoordinates",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkFullRouteCoordinatesTest::RunTest(const FString&)
{
    auto* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    if (!TestTrue(TEXT("corrected full river coordinate contract loads without weakening runtime guards"),
        Adapter->ConfigureRiverCoordinateMap(TEXT("physics/data/real_world/"
            "south_fork_american_chili_bar/reconstruction_2026_09/full_reach/"
            "playable_route/coordinate_map.json")))) return false;
    TestEqual(TEXT("captured ENU is reflected only at engine boundary"), Adapter->GetRiverWorldYSign(), -1.0);
    float Start = 0, Finish = 0;
    TestTrue(TEXT("full route exposes station domain"), Adapter->GetRiverStationRangeM(Start, Finish));
    TestTrue(TEXT("full river, not bounded rapid or old upstream extension"),
        Start == 0 && FMath::Abs(Finish - 33334.1463936) < .01);
    double MaximumStationError = 0, MaximumLateralError = 0;
    int32 Count = 0;
    // Both downstream traversal and nonlocal jumps exercise the spatial index
    // and cached lookup. These are coordinate checks, NOT hydraulic acceptance.
    for (int32 Pass = 0; Pass < 2; ++Pass)
    {
        for (int32 Index = 0; Index <= 1000; ++Index)
        {
            const int32 SampleIndex = Pass == 0 ? Index : (Index * 137) % 1001;
            const double Station = Finish * static_cast<double>(SampleIndex) / 1000;
            FVector World, Tangent, Left;
            FVector2D Inverse;
            if (!Adapter->RiverToWorldPosition(FVector2D(Station, 0), 227.f, World) ||
                !Adapter->WorldToRiverCoordinates(World, Inverse, Tangent, Left))
            {
                AddError(FString::Printf(TEXT("full-route coordinate lookup missing at %.6f"), Station));
                return false;
            }
            MaximumStationError = FMath::Max(MaximumStationError, FMath::Abs(Inverse.X - Station));
            MaximumLateralError = FMath::Max(MaximumLateralError, FMath::Abs(Inverse.Y));
            if (FMath::Abs(World.Z - 700.) > .001)
            {
                AddError(TEXT("NAVD88 datum changed during full-river mapping"));
                return false;
            }
            ++Count;
        }
    }
    AddInfo(FString::Printf(TEXT("%d full-river queries: max station error %.9f m; lateral %.9f m"),
        Count, MaximumStationError, MaximumLateralError));
    TestTrue(TEXT("full route inverse station error below one centimetre"), MaximumStationError < .01);
    TestTrue(TEXT("full route centreline remains centreline"), MaximumLateralError < .01);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkEmbeddedRapidWaterTest,
    "RaftSim.Survey.SouthForkEmbeddedRapidWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkEmbeddedRapidWaterTest::RunTest(const FString&)
{
    const FString Base = TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/");
    const FString Fields = Base + TEXT("troublemaker/playable_flow");
    auto* Local = NewObject<URaftSimWaterRuntimeAdapter>();
    auto* Embedded = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Local->Configure(Config);
    Embedded->Configure(Config);
    if (!TestTrue(TEXT("local captured water coordinate map loads"),
            Local->ConfigureRiverCoordinateMap(Fields + TEXT("/coordinate_map.json"))) ||
        !TestTrue(TEXT("same rigid hydraulic coordinates embed into the full river world"),
            Embedded->ConfigureRiverCoordinateMap(Base + TEXT("full_reach/playable_route/troublemaker_hydraulic_coordinate_map.json"))))
        return false;
    for (auto* Adapter : {Local, Embedded})
    {
        if (!TestTrue(TEXT("matched rapid fields load without re-centering or changing bed"),
            Adapter->ConfigureRiverWindow(Fields, TEXT("median_runnable"),
                FVector2D(0, 0), FVector2D(271, 161), .035f, false))) return false;
    }
    FVector LocalOrigin, EmbeddedOrigin;
    Local->RiverToWorldPosition(FVector2D::ZeroVector, 220, LocalOrigin);
    Embedded->RiverToWorldPosition(FVector2D::ZeroVector, 220, EmbeddedOrigin);
    const FVector Translation = EmbeddedOrigin - LocalOrigin;
    TestTrue(TEXT("rapid has moved into full-river frame, not remained at isolated origin"), Translation.Size() > 500000.);
    double MaximumDepthError = 0, MaximumHeightError = 0, MaximumVelocityError = 0;
    int32 Wet = 0, Queries = 0;
    for (int32 Station = -120; Station <= 120; Station += 8)
    {
        for (int32 Lateral = -64; Lateral <= 64; Lateral += 8)
        {
            FVector LocalWorld, EmbeddedWorld;
            Local->RiverToWorldPosition(FVector2D(Station, Lateral), 227, LocalWorld);
            Embedded->RiverToWorldPosition(FVector2D(Station, Lateral), 227, EmbeddedWorld);
            if (!(EmbeddedWorld - LocalWorld).Equals(Translation, .001))
            {
                AddError(TEXT("rapid embedding deformed metric coordinates"));
                return false;
            }
            FRaftSimWaterSample A, B;
            const bool HasA = Local->SampleWaterAtWorldPosition(LocalWorld, A);
            const bool HasB = Embedded->SampleWaterAtWorldPosition(EmbeddedWorld, B);
            if (HasA != HasB || (HasA && A.bWet != B.bWet))
            {
                AddError(TEXT("full-river placement changes rapid wet/dry availability"));
                return false;
            }
            ++Queries;
            if (!HasA) continue;
            Wet += A.bWet ? 1 : 0;
            MaximumDepthError = FMath::Max(MaximumDepthError, static_cast<double>(FMath::Abs(A.DepthMeters - B.DepthMeters)));
            MaximumHeightError = FMath::Max(MaximumHeightError, static_cast<double>(FMath::Abs(A.SurfaceHeightMeters - B.SurfaceHeightMeters)));
            MaximumVelocityError = FMath::Max(MaximumVelocityError, FVector::Distance(A.VelocityMetersPerSecond, B.VelocityMetersPerSecond));
        }
    }
    AddInfo(FString::Printf(TEXT("%d embedded queries, %d wet; max depth %.9f m, height %.9f m, velocity %.9f m/s differences"),
        Queries, Wet, MaximumDepthError, MaximumHeightError, MaximumVelocityError));
    TestTrue(TEXT("comparison contains wet rapid cells"), Wet > 50);
    TestTrue(TEXT("embedding preserves depth within 0.1 mm"), MaximumDepthError < .0001);
    TestTrue(TEXT("embedding preserves water elevation within 0.1 mm"), MaximumHeightError < .0001);
    TestTrue(TEXT("embedding preserves velocity within 0.1 mm/s"), MaximumVelocityError < .0001);
    return true;
}
#endif
