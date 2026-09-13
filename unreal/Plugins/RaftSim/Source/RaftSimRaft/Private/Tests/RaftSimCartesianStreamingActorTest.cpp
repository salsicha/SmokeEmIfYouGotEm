#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianStreamingActorTest,
    "RaftSim.M3.CartesianStreamingActorFollowsBothAxes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCartesianStreamingActorTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("isolated streaming fixture world"),World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Stream = World->SpawnActor<ARaftSimRiverWaterStreamingActor>();
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!Stream || !Raft) { AddError(TEXT("fixture actors failed to spawn")); return false; }
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Water->Configure(Config);
    const FString Base = TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/");
    if (!Water->ConfigureRiverCoordinateMap(Base+TEXT("hydraulic_regions_context/coordinate_map.json"))) return false;

    // Use the existing crop-compatible gameplay cook as a controller fixture.
    // This is the older procedural field, NOT reconstructed geography or a
    // physics acceptance test. Survey replays correctly reject partial crops;
    // retain that safeguard. No normal scenario or field manifest changes.
    auto Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("schema"),TEXT("raftsim.cartesian_water_streaming.v1"));
    Root->SetNumberField(TEXT("grid_spacing_m"),4.);
    Root->SetNumberField(TEXT("advance_m"),8.);
    Root->SetNumberField(TEXT("roughness_manning"),.041);
    Root->SetArrayField(TEXT("live_window_extent_m"),{MakeShared<FJsonValueNumber>(80.),MakeShared<FJsonValueNumber>(32.)});
    auto Window = MakeShared<FJsonObject>();
    Window->SetStringField(TEXT("window_id"),TEXT("bounded_solver_axis_fixture"));
    Window->SetStringField(TEXT("cooked_fields_manifest"),TEXT("physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/chili_bar_hole/cooked/manifest.json"));
    Window->SetArrayField(TEXT("hydraulic_bounds_m"),{MakeShared<FJsonValueNumber>(0.),MakeShared<FJsonValueNumber>(-40.),
        MakeShared<FJsonValueNumber>(400.),MakeShared<FJsonValueNumber>(40.)});
    Root->SetArrayField(TEXT("windows"),{MakeShared<FJsonValueObject>(Window)});
    FString Error;
    if (!TestTrue(TEXT("fixture source geometry accepted"),Stream->CartesianRegions.Load(Root,Error))) return false;
    Stream->bCartesianStreaming = true;
    Stream->WaterAdapter = Water;
    Stream->Raft = Raft;
    Stream->CachedFlowBand = TEXT("median_runnable");
    Raft->SetActorLocation(FVector(12000.,0.,0.));
    if (!TestTrue(TEXT("real actor creates first solver crop"),Stream->UpdateWaterWindow(true))) return false;
    TestEqual(TEXT("first crop recorded"),Stream->GetSuccessfulHandoffCount(),1);
    if (!TestTrue(TEXT("actual live solver advances before handoff"),Water->StepWater(1.f/60.f))) return false;
    const float Time = Water->GetSimTimeSeconds();

    Raft->SetActorLocation(FVector(12000.,-1200.,0.)); // Same X, hydraulic north +12.
    if (!TestTrue(TEXT("north-only raft motion is followed"),Stream->UpdateWaterWindow(false))) return false;
    TestEqual(TEXT("north-only motion causes an actual handoff"),Stream->GetSuccessfulHandoffCount(),2);
    TestTrue(TEXT("crop is centered on both raft coordinates, not Y=0"),Stream->LastCartesianCenterM==FVector2D(120.,12.));
    Raft->SetActorLocation(FVector(10800.,-1200.,0.));
    if (!TestTrue(TEXT("west-only raft motion is followed"),Stream->UpdateWaterWindow(false))) return false;
    TestEqual(TEXT("reverse-X motion causes an actual handoff"),Stream->GetSuccessfulHandoffCount(),3);
    TestTrue(TEXT("shared local coordinates retained in both axes"),Stream->LastCartesianCenterM==FVector2D(108.,12.));
    TestEqual(TEXT("water clock never resets during axis changes"),Water->GetSimTimeSeconds(),Time);
    FRaftSimWaterLiveWindowStats Stats;
    TestTrue(TEXT("actual handoff statistics available"),Water->GetLiveWindowStats(Stats));
    TestTrue(TEXT("actual solver state was transferred"),Stats.bLastHandoffPreservedState && Stats.LastHandoffTransferredCellCount>0);
    TestFalse(TEXT("handoff state remains finite"),Stats.bHasNonFinite);
    Raft->SetActorLocation(FVector(10900.,-1300.,0.));
    TestTrue(TEXT("small movement still covered"),Stream->UpdateWaterWindow(false));
    TestEqual(TEXT("small movement avoids redundant source reload"),Stream->GetSuccessfulHandoffCount(),3);
    TestTrue(TEXT("handed-off solver still advances"),Water->StepWater(1.f/60.f));
    Root->SetNumberField(TEXT("source_context_cells"),3.);
    Root->SetNumberField(TEXT("minimum_raft_interior_margin_m"),8.);
    Window->SetArrayField(TEXT("valid_live_center_bounds_m"),{
        MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{MakeShared<FJsonValueNumber>(100.),
            MakeShared<FJsonValueNumber>(0.),MakeShared<FJsonValueNumber>(140.),MakeShared<FJsonValueNumber>(0.)})});
    if (!TestTrue(TEXT("bounded-center fixture loads"),Stream->CartesianRegions.Load(Root,Error))) return false;
    Raft->SetActorLocation(FVector(12000.,0.,0.));
    if (!TestTrue(TEXT("bounded-center crop created"),Stream->UpdateWaterWindow(true))) return false;
    const int32 BoundedCount=Stream->GetSuccessfulHandoffCount();
    Raft->SetActorLocation(FVector(12000.,-800.,0.));
    TestTrue(TEXT("raft can move off-center within safety margin"),Stream->UpdateWaterWindow(false));
    TestEqual(TEXT("unchanged legal center avoids repeated reload at old raft-motion threshold"),Stream->GetSuccessfulHandoffCount(),BoundedCount);
    TestTrue(TEXT("boundary center remains on audited line"),Stream->LastCartesianCenterM==FVector2D(120.,0.));
    Raft->SetActorLocation(FVector(13000.,-800.,0.));
    TestTrue(TEXT("legal center follows longitudinal movement"),Stream->UpdateWaterWindow(false));
    TestEqual(TEXT("legal center motion triggers real handoff"),Stream->GetSuccessfulHandoffCount(),BoundedCount+1);
    TestTrue(TEXT("handoff uses selected center rather than raft position"),Stream->LastCartesianCenterM==FVector2D(130.,0.));
    TestTrue(TEXT("bounded-center handoff statistics available"),Water->GetLiveWindowStats(Stats));
    TestTrue(TEXT("bounded-center handoff transfers actual solver state"),Stats.bLastHandoffPreservedState && Stats.LastHandoffTransferredCellCount>0);
    AddInfo(TEXT("Real streaming actor loaded and stepped hash-verified flow; north-only and reverse-X moves preserved overlapping state and clock. Fixture only, not full-river integration."));
    return !HasAnyErrors();
}
#endif
