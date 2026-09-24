#include "RaftSimDetailSourceFootprint.h"
#include "RaftSimCartesianWaterRegions.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimRaftActor.h"
#include "Engine/World.h"
#include "Misc/ScopeExit.h"
#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
namespace
{
bool ReadCoverageRoute(const TSharedPtr<FJsonObject>& Route,TArray<TArray<double>>& Points,FString& Error)
{
    Points.Reset();
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    if(!Route.IsValid() || !Route->TryGetArrayField(TEXT("points"),Values) || Values->Num()<2)
    { Error=TEXT("Coverage route requires at least two points");return false; }
    double PreviousStation=-TNumericLimits<double>::Max();
    for(const auto& Value:*Values)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row=nullptr;
        if(!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num()<5)
        { Error=TEXT("Coverage route point requires station, XY and normal XY");return false; }
        TArray<double> Point;
        for(int32 Column=0;Column<5;++Column)
        {
            double Number=0.;
            if(!(*Row)[Column].IsValid() || (*Row)[Column]->Type!=EJson::Number ||
                !(*Row)[Column]->TryGetNumber(Number) || !FMath::IsFinite(Number))
            { Error=TEXT("Coverage route contains a non-finite or non-numeric coordinate");return false; }
            Point.Add(Number);
        }
        if(Point[0]<=PreviousStation || FMath::Abs(Point[3]*Point[3]+Point[4]*Point[4]-1.)>1.e-4)
        { Error=TEXT("Coverage route requires increasing stations and unit side normals");return false; }
        PreviousStation=Point[0];Points.Add(MoveTemp(Point));
    }
    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailCoverageRouteInputTest,
    "RaftSim.M3.DetailCoverageRouteInput",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailCoverageRouteInputTest::RunTest(const FString&)
{
    for(const TCHAR* Text:{TEXT("{}"),TEXT("{\"points\":[]}"),
        TEXT("{\"points\":[[0,0,0,1,0]]}"),
        TEXT("{\"points\":[[0,0,0,1,0],[1,0]]}"),
        TEXT("{\"points\":[[0,0,0,1,0],[1,\"bad\",0,1,0]]}"),
        TEXT("{\"points\":[[0,0,0,1,0],[0,1,0,1,0]]}"),
        TEXT("{\"points\":[[0,0,0,1,0],[1,1,0,0,0]]}")})
    {
        TSharedPtr<FJsonObject> Root;TArray<TArray<double>> Points;FString Error;
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root);
        TestFalse(TEXT("malformed or vacuous route rejected"),ReadCoverageRoute(Root,Points,Error));
        TestFalse(TEXT("rejection explains missing evidence"),Error.IsEmpty());
    }
    TSharedPtr<FJsonObject> Root;TArray<TArray<double>> Points;FString Error;
    FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(TEXT("{\"points\":[[0,2,3,1,0],[1,4,5,0,1]]}")),Root);
    TestTrue(TEXT("valid route accepted"),ReadCoverageRoute(Root,Points,Error));
    TestEqual(TEXT("all route rows retained"),Points.Num(),2);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailSourceFootprintTest,
    "RaftSim.M3.DetailSourceFootprint",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailSourceFootprintTest::RunTest(const FString&)
{
    for(int32 Side:{67,69})for(float PhaseX:{0.f,.5f})for(float PhaseY:{0.f,.5f})
    for(FVector2f Move:{FVector2f(0,0),FVector2f(8,0),FVector2f(-8,0),FVector2f(0,8),FVector2f(0,-8),FVector2f(-8,8)})
    {
        const FVector2f Old(-5626.f+PhaseX,3600.f+PhaseY),Next=Old+Move;
        FBox2D Required;
        TestTrue(TEXT("full requested footprint computed"),FRaftSimDetailSourceFootprint::Required(Old,Next,Side,Required));
        for(const FVector2f Origin:{Old,Next})
        {
            FRaftSimDetailSampleGrid Grid;Grid.Register(Origin);
            const int32 Halo=(Side-65)/2;
            for(int32 Y=0;Y<Side;++Y)for(int32 X=0;X<Side;++X)
                if(!Required.IsInsideOrOn(FVector2D(Grid.CoarseOriginMeters)+FVector2D(X-Halo,Y-Halo)))
                { AddError(TEXT("closing or next native halo sample omitted"));return false; }
        }
    }
    FBox2D Required;
    TestTrue(TEXT("observed westward move footprint"),FRaftSimDetailSourceFootprint::Required(FVector2f(-5626,3600),FVector2f(-5634,3602),67,Required));
    TestTrue(TEXT("closing and next extrema both retained"),Required.Min==FVector2D(-5635,3599) && Required.Max==FVector2D(-5561,3667));
    const FBox2D OldField(FVector2D(-5634.999999998952,3509),FVector2D(-5408.999999998952,3734));
    TestFalse(TEXT("nanometre-outside halo is not silently clamped"),FRaftSimDetailSourceFootprint::Covered(OldField,Required));
    TestTrue(TEXT("teleport requests only new footprint"),FRaftSimDetailSourceFootprint::Required(FVector2f(0,0),FVector2f(1000,1000),67,Required));
    TestTrue(TEXT("distant old source not required for reset"),Required.Min==FVector2D(999,999) && Required.Max==FVector2D(1065,1065));
    TestFalse(TEXT("unsupported source ring rejected"),FRaftSimDetailSourceFootprint::Required(FVector2f(0,0),FVector2f(0,0),65,Required));
    TestFalse(TEXT("non-half-cell source rejected"),FRaftSimDetailSourceFootprint::Required(FVector2f(.25,0),FVector2f(0,0),67,Required));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailCropSelectionTest,
    "RaftSim.M3.DetailCropSelection",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailCropSelectionTest::RunTest(const FString&)
{
    const TCHAR* Text=TEXT(R"({"schema":"raftsim.cartesian_water_streaming.v1","grid_spacing_m":1,"advance_m":80,"roughness_manning":0.035,"source_context_cells":3,"minimum_raft_interior_margin_m":10,"live_window_extent_m":[224,224],"windows":[{"window_id":"source","cooked_fields_manifest":"fixture/source/manifest.json","hydraulic_bounds_m":[-5800,3400,-5300,3900],"valid_live_center_bounds_m":[[-5685,3515,-5415,3785]]}]})");
    TSharedPtr<FJsonObject> Root;FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root);
    FRaftSimCartesianWaterRegions Regions;FString Error;
    if(!TestTrue(TEXT("source geometry fixture"),Regions.Load(Root,Error)))return false;
    const FVector2D Position(-5602.1,3633.966),Previous(-5522.17,3621.345);
    TestTrue(TEXT("old raft-only coverage accepts the failing move"),Regions.CoversRaft(Position,Previous));
    TestFalse(TEXT("old advance rule has not yet triggered"),Regions.NeedsRecentering(Position,Previous));
    FBox2D Required;FRaftSimDetailSourceFootprint::Required(FVector2f(-5626,3600),FVector2f(-5634,3602),67,Required);
    FVector2D Center;
    if(!TestNotNull(TEXT("complete replacement crop selected"),Regions.Select(Position,TEXT("fixture/source"),&Center,&Required)))return false;
    TestTrue(TEXT("selected field covers all actual detail requests"),FRaftSimDetailSourceFootprint::Covered(FBox2D(Center-FVector2D(112),Center+FVector2D(112)),Required));
    const FBox2D Large(FVector2D(-5800,3500),FVector2D(-5400,3600));
    TestNull(TEXT("oversized request cannot shrink or clamp"),Regions.Select(Position,TEXT(""),&Center,&Large));
    const FBox2D Unavailable(FVector2D(1.e5,1.e5),FVector2D(1.e5+1,1.e5+1));
    TestNull(TEXT("no nearby-source fallback"),Regions.Select(Position,TEXT(""),&Center,&Unavailable));
    // A feasible crop may need its center shifted from the nearest raft point.
    const FBox2D Offset(FVector2D(-5720,3590),FVector2D(-5650,3660));
    if(!TestNotNull(TEXT("consumer intersection selects a legal shifted center"),Regions.Select(Position,TEXT(""),&Center,&Offset)))return false;
    TestTrue(TEXT("shift respects required source and unchanged raft margin"),
        Center.X<=-5608 && Regions.CoversRaft(Position,Center) && FRaftSimDetailSourceFootprint::Covered(FBox2D(Center-FVector2D(112),Center+FVector2D(112)),Offset));
    return !HasAnyErrors();
}

#if RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailFullRouteCoverageTest,
    "RaftSim.M3.DetailFullRouteCoverage",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailFullRouteCoverageTest::RunTest(const FString&)
{
    FString Streaming;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailFootprintStreaming="),Streaming))
    { AddError(TEXT("Explicit source-bound streaming manifest required"));return false; }
    const auto Read=[](const FString& Path)
    {
        FString Text;TSharedPtr<FJsonObject> Json;
        if(FFileHelper::LoadFileToString(Text,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Path)))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json);
        return Json;
    };
    const auto Root=Read(Streaming);
    const auto Route=Read(TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json"));
    FRaftSimCartesianWaterRegions Regions;FString Error;
    TArray<TArray<double>> Points;
    if(!ReadCoverageRoute(Route,Points,Error) || !Regions.Load(Root,Error))
    { AddError(Error);return false; }
    int32 Queries=0,Missing=0;
    for(double Side:{-12.,0.,12.})
    {
        FVector2f Current(0,0);bool bFirst=true;FString Active;
        for(const auto& P:Points)
        {
            const FVector2D Position(P[1]+Side*P[3],P[2]+Side*P[4]);
            FVector2f Next(float(FMath::RoundToDouble(Position.X*2.)*.5-32.),float(-FMath::RoundToDouble(-Position.Y*2.)*.5-32.));
            if(bFirst){Current=Next;bFirst=false;}
            if(FMath::Max(FMath::Abs(Position.X-(Current.X+32.)),FMath::Abs(Position.Y-(Current.Y+32.)))<8.)Next=Current;
            FBox2D Required;
            if(!FRaftSimDetailSourceFootprint::Required(Current,Next,67,Required))
            { AddError(TEXT("Route sample cannot form a valid detail footprint"));return false; }
            FVector2D Center;
            const auto* Region=Regions.Select(Position,Active,&Center,&Required);
            if(!Region)
            {
                if(Missing<8)AddInfo(FString::Printf(TEXT("Missing full detail crop at route station %.6f side %.1f field=(%.6f,%.6f)"),P[0],Side,Position.X,Position.Y));
                ++Missing;
            }
            else
            {
                if(!FRaftSimDetailSourceFootprint::Covered(FBox2D(Center-Regions.GetExtentM()*.5,Center+Regions.GetExtentM()*.5),Required))
                { AddError(TEXT("Selected crop omits a required source sample"));return false; }
                Active=Region->FieldsDirectory;
            }
            Current=Next;++Queries;
        }
    }
    TestEqual(TEXT("every route point checked at all three side offsets"),Queries,Points.Num()*3);
    TestEqual(TEXT("all actual route/side detail and closing footprints have complete source crops"),Missing,0);
    AddInfo(FString::Printf(TEXT("Full-route source selection: %d detail/closing footprints, %d missing. No physics steps or visual/traversal acceptance."),Queries,Missing));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailNativeHandoffTest,
    "RaftSim.M3.DetailNativeHandoff",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailNativeHandoffTest::RunTest(const FString&)
{
    FString Fields,Streaming;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailFootprintFields="),Fields) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailFootprintStreaming="),Streaming))
    { AddError(TEXT("Explicit observed source packet and matching streaming manifest required"));return false; }
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;Config.bRequireAcceptedReportManifest=false;Config.bEnableDeterministicCapture=false;Water->Configure(Config);
    if(!Water->ConfigureRiverCoordinateMap(TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")) ||
        !Water->ConfigureMovingRiverWindow(Fields,TEXT("median_runnable"),FVector2D(-5522.170,3621.345),FVector2D(224,224),.035f))
    { AddError(TEXT("Actual source-bound pre-failure crop failed to load"));return false; }
    if(!TestTrue(TEXT("actual native field advances before transfer"),Water->StepWater(.05f) && Water->GetSimTimeSeconds()>0.f))return false;
    FBox2D Required,Before;FRaftSimDetailSourceFootprint::Required(FVector2f(-5626,3600),FVector2f(-5634,3602),67,Required);
    Water->GetLiveWaterFieldBoundsM(Before);
    TestFalse(TEXT("actual previous native field lacks requested source footprint"),FRaftSimDetailSourceFootprint::Covered(Before,Required));
    TArray<FVector2D> Queries;TArray<FRaftSimWaterSample> Prior;TArray<bool> Valid;
    int32 Missing=0;
    for(FVector2f Origin:{FVector2f(-5626,3600),FVector2f(-5634,3602)})
        for(int32 Y=-1;Y<=65;++Y)for(int32 X=-1;X<=65;++X)
        {
            const FVector2D P=FVector2D(Origin)+FVector2D(X,Y);FRaftSimWaterSample Sample;
            const bool bValid=Water->SampleWaterFieldAtRiverCoordinates(P,Sample);
            Queries.Add(P);Prior.Add(Sample);Valid.Add(bValid);Missing+=!bValid;
        }
    TestTrue(TEXT("actual native sampling reproduces the domain failure"),Missing>0);
    FString Text,Error;TSharedPtr<FJsonObject> Root;
    if(!FFileHelper::LoadFileToString(Text,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Streaming)) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root))return false;
    FRaftSimCartesianWaterRegions Regions;
    if(!Regions.Load(Root,Error))return false;
    FVector2D Center;
    const auto* Region=Regions.Select(FVector2D(-5602.1,3633.966),Fields,&Center,&Required);
    if(!TestNotNull(TEXT("actual manifest has complete required source"),Region))return false;
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if(!TestNotNull(TEXT("isolated controller fixture world"),World))return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false);World->RemoveFromRoot(); };
    auto* Stream=World->SpawnActor<ARaftSimRiverWaterStreamingActor>();
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>();
    auto* Owner=World->SpawnActor<AActor>();
    if(!Stream || !Raft || !Owner)return false;
    auto* Detail=NewObject<URaftSimStatefulDetailComponent>(Owner);
    Stream->WaterAdapter=Water;Stream->Raft=Raft;Stream->bCartesianStreaming=true;
    Stream->CachedFlowBand=TEXT("median_runnable");Stream->ActiveFieldsDirectory=Fields;
    Stream->LastCartesianCenterM=FVector2D(-5522.170,3621.345);
    if(!Stream->CartesianRegions.Load(Root,Error))return false;
    Raft->SetActorLocation(FVector(-560210.,-363396.6,0.));
    Detail->Water=Water;Detail->bMovingWindow=true;Detail->WindowOriginMeters=FVector2f(-5626,3600);
    const float Time=Water->GetSimTimeSeconds();const double Committed=Water->GetCommittedStepSeconds();
    if(!TestTrue(TEXT("detail consumer synchronously requests actual native replacement before sampling"),Detail->EnsureSourceCoverage(FVector2f(-5634,3602))))return false;
    TestEqual(TEXT("real controller performed one handoff"),Stream->GetSuccessfulHandoffCount(),1);
    TestTrue(TEXT("already covered detail request remains valid"),Detail->EnsureSourceCoverage(FVector2f(-5634,3602)));
    TestEqual(TEXT("covered request avoids redundant reload"),Stream->GetSuccessfulHandoffCount(),1);
    FBox2D After;Water->GetLiveWaterFieldBoundsM(After);
    TestTrue(TEXT("replacement native field covers exact requests"),FRaftSimDetailSourceFootprint::Covered(After,Required));
    TestEqual(TEXT("native simulation clock preserved"),Water->GetSimTimeSeconds(),Time);
    TestEqual(TEXT("committed water clock preserved"),Water->GetCommittedStepSeconds(),Committed);
    int32 Preserved=0;
    for(int32 I=0;I<Queries.Num();++I)
    {
        FRaftSimWaterSample Sample;
        if(!Water->SampleWaterFieldAtRiverCoordinates(Queries[I],Sample))
        { AddError(TEXT("replacement still lacks a closing/next source sample"));return false; }
        if(Valid[I])
        {
            if(Sample.DepthMeters!=Prior[I].DepthMeters || Sample.BedHeightMeters!=Prior[I].BedHeightMeters ||
                Sample.SurfaceHeightMeters!=Prior[I].SurfaceHeightMeters || Sample.VelocityMetersPerSecond!=Prior[I].VelocityMetersPerSecond)
            { AddError(TEXT("actual overlap source sample changed on handoff"));return false; }
            ++Preserved;
        }
    }
    FRaftSimWaterLiveWindowStats Stats;
    TestTrue(TEXT("native overlapping state transfer reported"),Water->GetLiveWindowStats(Stats) && Stats.bLastHandoffPreservedState && Stats.LastHandoffTransferredCellCount>0 && !Stats.bHasNonFinite);
    AddInfo(FString::Printf(TEXT("Actual failing crop: %d missing of %d queries; actual detail/controller coverage call restores every query, %d prior valid samples exact; one handoff, simulation and committed clocks unchanged. This is not actual long-game acceptance."),Missing,Queries.Num(),Preserved));
    return !HasAnyErrors();
}
#endif
#endif
