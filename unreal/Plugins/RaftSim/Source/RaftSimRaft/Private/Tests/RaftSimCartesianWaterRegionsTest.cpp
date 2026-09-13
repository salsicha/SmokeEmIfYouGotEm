#include "RaftSimCartesianWaterRegions.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianWaterRegionsTest,
    "RaftSim.Survey.CartesianWaterRegions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCartesianWaterRegionsTest::RunTest(const FString&)
{
    const FString Base = TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/");
    const auto Read = [&](const FString& Relative) -> TSharedPtr<FJsonObject>
    {
        FString Text;
        TSharedPtr<FJsonObject> Json;
        if (FFileHelper::LoadFileToString(Text, *URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Base+Relative)))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Json);
        return Json;
    };
    auto Geometry = Read(TEXT("hydraulic_regions_context/manifest.json"));
    auto Route = Read(TEXT("playable_route/coordinate_map.json"));
    if (!TestTrue(TEXT("verified full-river source manifests available"), Geometry.IsValid() && Route.IsValid())) return false;
    FRaftSimCartesianWaterRegions Regions;
    FString Error;
    TestFalse(TEXT("geometry-only packets cannot be loaded as solved streaming fields"), Regions.Load(Geometry,Error));

    // Selection fixture only: no invented velocities and no cooked files are
    // generated. Exercise the exact native selector with all actual 799 bounds.
    auto Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("schema"), TEXT("raftsim.cartesian_water_streaming.v1"));
    Root->SetNumberField(TEXT("grid_spacing_m"),1.);
    Root->SetNumberField(TEXT("advance_m"),80.);
    Root->SetNumberField(TEXT("roughness_manning"),.035);
    Root->SetNumberField(TEXT("source_context_cells"),3.);
    Root->SetArrayField(TEXT("live_window_extent_m"), {
        MakeShared<FJsonValueNumber>(224.), MakeShared<FJsonValueNumber>(224.)});
    TArray<TSharedPtr<FJsonValue>> Windows;
    for (const auto& Value : Geometry->GetArrayField(TEXT("regions")))
    {
        const auto Record = Value->AsObject();
        const auto Origin = Record->GetArrayField(TEXT("grid_origin_local_m"));
        const double X = Origin[0]->AsNumber(), Y = Origin[1]->AsNumber();
        auto Window = MakeShared<FJsonObject>();
        const FString Id = Record->GetStringField(TEXT("name"));
        Window->SetStringField(TEXT("window_id"), Id);
        Window->SetStringField(TEXT("cooked_fields_manifest"), TEXT("selection_fixture_only/")+Id+TEXT("/manifest.json"));
        Window->SetArrayField(TEXT("hydraulic_bounds_m"), {MakeShared<FJsonValueNumber>(X),
            MakeShared<FJsonValueNumber>(Y), MakeShared<FJsonValueNumber>(X+320.), MakeShared<FJsonValueNumber>(Y+320.)});
        Windows.Add(MakeShared<FJsonValueObject>(Window));
    }
    Root->SetArrayField(TEXT("windows"), Windows);
    if (!TestTrue(TEXT("native Cartesian selector loads source-region bounds"), Regions.Load(Root,Error))) return false;
    TestEqual(TEXT("all source regions retained"), Regions.Num(),799);
    auto Water = NewObject<URaftSimWaterRuntimeAdapter>();
    if (!TestTrue(TEXT("explicit common Cartesian water frame loads"),
        Water->ConfigureRiverCoordinateMap(Base+TEXT("hydraulic_regions_context/coordinate_map.json")))) return false;
    TestTrue(TEXT("Cartesian frame is distinguished from downstream progress"),Water->HasCartesianWaterCoordinates());
    float Min = 0, Max = 0;
    TestFalse(TEXT("east bounds are never reported as a river station range"), Water->GetRiverStationRangeM(Min,Max));
    FString Active;
    double MaximumRoundTripError = 0.;
    int32 Handoffs = 0, Probes = 0;
    for (const auto& Value : Route->GetArrayField(TEXT("points")))
    {
        const auto Point = Value->AsArray();
        for (const double Side : {-12.,0.,12.})
        {
            const FVector2D Position(Point[1]->AsNumber()+Side*Point[3]->AsNumber(),
                Point[2]->AsNumber()+Side*Point[4]->AsNumber());
            const auto* Region = Regions.Select(Position,Active);
            if (!Region) { AddError(TEXT("axis/side probe has no complete native source crop")); return false; }
            Handoffs += Region->FieldsDirectory != Active;
            Active = Region->FieldsDirectory;
            FVector World, Tangent, North;
            FVector2D RoundTrip;
            if (!Water->RiverToWorldPosition(Position,227.,World) ||
                !Water->WorldToRiverCoordinates(World,RoundTrip,Tangent,North))
            { AddError(TEXT("Cartesian world conversion failed along full river")); return false; }
            MaximumRoundTripError = FMath::Max(MaximumRoundTripError,FVector2D::Distance(Position,RoundTrip));
            if (World.Z != 700. || North != FVector(0.,-1.,0.))
            { AddError(TEXT("NAVD88 datum or north reflection changed")); return false; }
            ++Probes;
        }
    }
    TestTrue(TEXT("full descent coordinate round trips remain below one micrometre"),MaximumRoundTripError < 1.e-6);
    TestTrue(TEXT("full descent actually selects multiple sources"),Handoffs>100);
    TestTrue(TEXT("north-only motion triggers recenter"), Regions.NeedsRecentering(FVector2D(0.,80.),FVector2D::ZeroVector));
    TestTrue(TEXT("west-only motion triggers recenter"), Regions.NeedsRecentering(FVector2D(-80.,0.),FVector2D::ZeroVector));
    TestFalse(TEXT("subthreshold motion does not recenter"), Regions.NeedsRecentering(FVector2D(79.,-79.),FVector2D::ZeroVector));
    TestTrue(TEXT("out-of-domain source request fails closed"),Regions.Select(FVector2D(1.e8,1.e8),Active)==nullptr);
    FVector Out;
    TestFalse(TEXT("out-of-domain world request fails closed"),Water->RiverToWorldPosition(FVector2D(1.e8,1.e8),227.,Out));
    Root->SetNumberField(TEXT("source_context_cells"),2.);
    TestFalse(TEXT("explicit MUSCL source context includes rounding margin"),Regions.Load(Root,Error));
    Root->SetNumberField(TEXT("source_context_cells"),3.);
    const TSharedPtr<FJsonValue> Duplicate = Windows[0];
    Windows.Add(Duplicate);
    Root->SetArrayField(TEXT("windows"),Windows);
    TestFalse(TEXT("duplicate source identities fail closed"),Regions.Load(Root,Error));
    TestEqual(TEXT("failed manifest leaves no partially loaded sources"),Regions.Num(),0);
    Windows.Pop();
    FString CoverageText;
    TSharedPtr<FJsonObject> Coverage;
    FFileHelper::LoadFileToString(CoverageText,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("tmp/south-fork-live-center-coverage-20260912.json")));
    FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(CoverageText),Coverage);
    if (!TestTrue(TEXT("audited boundary-center fixture available"),Coverage.IsValid())) return false;
    const auto& CenterWindows=Coverage->GetArrayField(TEXT("windows"));
    if (!TestEqual(TEXT("coverage retains every source identity"),CenterWindows.Num(),Windows.Num())) return false;
    int32 EmptySources=0;
    for (int32 I=0;I<Windows.Num();++I)
    {
        const auto Centers=CenterWindows[I]->AsObject();
        const auto Window=Windows[I]->AsObject();
        if (!TestEqual(TEXT("coverage source identity matches geometry"),
            Centers->GetStringField(TEXT("window_id")),Window->GetStringField(TEXT("window_id")))) return false;
        const auto& Rectangles=Centers->GetArrayField(TEXT("valid_live_center_bounds_m"));
        EmptySources+=Rectangles.IsEmpty();
        Window->SetArrayField(TEXT("valid_live_center_bounds_m"),Rectangles);
    }
    Root->SetArrayField(TEXT("windows"),Windows);
    TestFalse(TEXT("explicit centers require a declared raft safety margin"),Regions.Load(Root,Error));
    Root->SetNumberField(TEXT("minimum_raft_interior_margin_m"),8.);
    if (!TestTrue(TEXT("boundary-aware full-size source selection loads"),Regions.Load(Root,Error))) return false;
    TestEqual(TEXT("unusable sources retained without a fabricated fallback"),EmptySources,4);
    double MinimumMargin=112., MaximumShift=0.;
    const FVector2D UtmOrigin(689236.999999999,4293073.);
    const auto& Shifted=Coverage->GetArrayField(TEXT("shifted_probe_records"));
    TestEqual(TEXT("every previously failing wet-domain probe retained"),Shifted.Num(),3822);
    for (const auto& Value:Shifted)
    {
        const auto& P=Value->AsObject()->GetArrayField(TEXT("position_utm_m"));
        const FVector2D Position=FVector2D(P[0]->AsNumber(),P[1]->AsNumber())-UtmOrigin;
        FVector2D Center;
        const auto* Region=Regions.Select(Position,FString(),&Center);
        if (!Region) { AddError(TEXT("boundary probe has no complete full-size crop")); return false; }
        bool bInAuditedRectangle=false;
        for (const FBox2D& Rectangle:Region->LiveCenterBoundsM)
            bInAuditedRectangle|=Rectangle.IsInsideOrOn(Center);
        if (!bInAuditedRectangle || !Regions.CoversRaft(Position,Center) ||
            !Region->BoundsM.IsInsideOrOn(Center-FVector2D(115.,115.)) ||
            !Region->BoundsM.IsInsideOrOn(Center+FVector2D(115.,115.)))
        { AddError(TEXT("selected center violates audited coverage or ghost context")); return false; }
        const FVector2D Delta=Position-Center;
        MinimumMargin=FMath::Min(MinimumMargin,112.-FMath::Max(FMath::Abs(Delta.X),FMath::Abs(Delta.Y)));
        MaximumShift=FMath::Max(MaximumShift,Delta.Size());
    }
    TestTrue(TEXT("all endpoint probes keep at least ten metres inside unchanged window"),MinimumMargin>=10.-1.e-6);
    TestTrue(TEXT("endpoint shift stays within audited maximum"),MaximumShift<=102.+1.e-6);
    TestTrue(TEXT("window was not shortened to pass coverage"),Regions.GetExtentM()==FVector2D(224.,224.));
    Active.Reset();
    for (const auto& Value:Route->GetArrayField(TEXT("points")))
    {
        const auto Point=Value->AsArray();
        for (const double Side:{-12.,0.,12.})
        {
            const FVector2D Position(Point[1]->AsNumber()+Side*Point[3]->AsNumber(),
                Point[2]->AsNumber()+Side*Point[4]->AsNumber());
            FVector2D Center;
            const auto* Region=Regions.Select(Position,Active,&Center);
            if (!Region || FVector2D::Distance(Position,Center)>1.e-6)
            { AddError(TEXT("retained route/side probe unnecessarily shifted or unavailable")); return false; }
            Active=Region->FieldsDirectory;
        }
    }
    Windows[0]->AsObject()->SetArrayField(TEXT("valid_live_center_bounds_m"),{
        MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{MakeShared<FJsonValueNumber>(1.e8),
            MakeShared<FJsonValueNumber>(0.),MakeShared<FJsonValueNumber>(1.e8),MakeShared<FJsonValueNumber>(0.)})});
    TestFalse(TEXT("center rectangle outside source geometry rejected"),Regions.Load(Root,Error));
    TestEqual(TEXT("invalid center rectangle leaves no partial sources"),Regions.Num(),0);
    AddInfo(FString::Printf(TEXT("3822 endpoint crop probes covered; minimum raft margin %.9g m, maximum center shift %.9g m; 52689 route/side centers unchanged. Selection validation only, not settled-flow acceptance."),MinimumMargin,MaximumShift));
    AddInfo(FString::Printf(TEXT("%d full-river axis/side probes, %d source selections, maximum XY round-trip error %.12g m"),Probes,Handoffs,MaximumRoundTripError));
    FString VerifiedText;
    TSharedPtr<FJsonObject> Verified;
    FFileHelper::LoadFileToString(VerifiedText,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("tmp/south-fork-runtime-atlas-201s-v1-20260912/streaming_manifest_verified.json")));
    FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(VerifiedText),Verified);
    if (!TestTrue(TEXT("actual shared-atlas source-selection manifest loads"),Verified.IsValid() && Regions.Load(Verified,Error))) return false;
    TestEqual(TEXT("shared-atlas catalog retains all source identities"),Regions.Num(),799);
    for (const auto& Value:Shifted)
    {
        const auto& P=Value->AsObject()->GetArrayField(TEXT("position_utm_m"));
        const FVector2D Position=FVector2D(P[0]->AsNumber(),P[1]->AsNumber())-UtmOrigin;
        FVector2D Center;
        const auto* Selected=Regions.Select(Position,FString(),&Center);
        if (!Selected || !Regions.CoversRaft(Position,Center))
        { AddError(TEXT("physical-boundary-safe catalog lost an endpoint water position")); return false; }
    }
    Active.Reset();
    for (const auto& Value:Route->GetArrayField(TEXT("points")))
    {
        const auto Point=Value->AsArray();
        for (const double Side:{-12.,0.,12.})
        {
            const FVector2D Position(Point[1]->AsNumber()+Side*Point[3]->AsNumber(),
                Point[2]->AsNumber()+Side*Point[4]->AsNumber());
            FVector2D Center;
            const auto* Selected=Regions.Select(Position,Active,&Center);
            if (!Selected || FVector2D::Distance(Position,Center)>1.e-6)
            { AddError(TEXT("shared-atlas physical-boundary guard shifted or lost a route/side position")); return false; }
            Active=Selected->FieldsDirectory;
        }
    }
    AddInfo(TEXT("Actual 832-core shared-atlas catalog: all3822 endpoint and52689 unshifted route/side selections pass with physical-exterior-safe centers."));
    return !HasAnyErrors();
}
#endif
