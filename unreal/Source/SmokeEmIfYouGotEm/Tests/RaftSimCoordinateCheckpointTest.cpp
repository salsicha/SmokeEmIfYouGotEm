#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "../RaftSimRunManager.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimReconstructedSessionContractsTest,"RaftSim.Survey.ReconstructedSessionContracts",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimReconstructedSessionContractsTest::RunTest(const FString&)
{
    FString Text;
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Text, *URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/session_contracts.json"))) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root) return false;
    const auto& Sessions = Root->GetArrayField(TEXT("sessions"));
    TestEqual(TEXT("four sections and the full river, never a rapid scenario"), Sessions.Num(), 5);
    for (const auto& Value : Sessions)
    {
        const auto& Session = Value->AsObject();
        FRaftSimCareerScenarioDefinition Definition;
        if (!TestTrue(TEXT("source session is in the normal menu catalog"), URaftSimProgressionLibrary::FindScenario(
            FName(*Session->GetStringField(TEXT("id"))), Definition))) continue;
        TestTrue(TEXT("menu/session start and finish match source contracts to float precision"),
            Definition.StartStationM == static_cast<float>(Session->GetNumberField(TEXT("start_m"))) &&
            Definition.FinishStationM == static_cast<float>(Session->GetNumberField(TEXT("finish_m"))));
        TestEqual(TEXT("every session uses the normal full-river map"), Definition.LevelName.ToString(), Root->GetStringField(TEXT("level")));
    }
    TestFalse(TEXT("provisional mileage is not mislabeled surveyed landmark acceptance"), Root->GetBoolField(TEXT("landmark_georeferencing_accepted")));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCoordinateSaveTest,"RaftSim.M6.CoordinateFrameProgress",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCoordinateSaveTest::RunTest(const FString&)
{
    const FString NewFrame=TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json");
    const FName Level=TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
    auto* Save=NewObject<URaftSimVerticalSliceSaveGame>();
    Save->SaveVersion=3;
    FRaftSimScenarioProgress Old;
    Old.ScenarioId=TEXT("south_fork_full_descent");
    Old.FurthestStationM=24000.f; Old.bHasCheckpoint=true;
    Old.CheckpointTransform=FTransform(FVector(12000,30000,800));
    Old.BestGhostRoute={FVector(12,3,8),FVector(24,6,16)};
    Old.BestOverallScore=.97f; Old.BestSafetyScore=.99f; Old.BestMedal=ERaftSimMedal::Gold;
    Old.AttemptCount=7; Old.CompletionCount=2; Old.BestTimeSeconds=99.f;
    Save->ScenarioProgress.Add(Old);
    if (!TestTrue(TEXT("version-three profile upgrades additively"),URaftSimSaveSubsystem::NormalizeSave(Save))) return false;
    FTransform Found;
    TestTrue(TEXT("legacy checkpoint still works in its original frame"),
        URaftSimSaveSubsystem::SelectCheckpoint(Save,23990,24010,TEXT(""),Level,Found));
    TestFalse(TEXT("old coordinates are not a reconstructed-river checkpoint"),
        URaftSimSaveSubsystem::SelectCheckpoint(Save,23990,24010,NewFrame,Level,Found));
    const FTransform Current(FVector(-400000,-300000,4000));
    if (!TestTrue(TEXT("first new-frame checkpoint records"),URaftSimSaveSubsystem::ApplyCareerCheckpoint(
        Save,Old.ScenarioId,NAME_None,9012.f,Current,NewFrame))) return false;
    TestEqual(TEXT("old complete record retained once"),Save->HistoricalRouteProgress.Num(),1);
    const auto& History=Save->HistoricalRouteProgress[0];
    TestTrue(TEXT("historical transform and ghost are unchanged"),
        History.CheckpointTransform.Equals(Old.CheckpointTransform,0.f) && History.BestGhostRoute==Old.BestGhostRoute);
    TestTrue(TEXT("historical distance, time and identity remain exact"),
        History.FurthestStationM==Old.FurthestStationM && History.BestTimeSeconds==Old.BestTimeSeconds &&
        History.ScenarioId==Old.ScenarioId && History.CoordinateMapPath.IsEmpty());
    auto& Active=Save->ScenarioProgress[0];
    TestTrue(TEXT("medals and aggregate accomplishments survive the frame transition"),
        Active.BestMedal==Old.BestMedal && Active.AttemptCount==Old.AttemptCount &&
        Active.CompletionCount==Old.CompletionCount && Active.BestOverallScore==Old.BestOverallScore);
    TestTrue(TEXT("new checkpoint does not inherit old distance or ghost"),
        Active.FurthestStationM==9012.f && Active.BestGhostRoute.IsEmpty() && Active.BestTimeSeconds==0.f);
    TestTrue(TEXT("new-frame checkpoint is selected"),
        URaftSimSaveSubsystem::SelectCheckpoint(Save,9000,9020,NewFrame,Level,Found) && Found.Equals(Current,0.f));
    TestFalse(TEXT("other river cannot reuse a numerically overlapping checkpoint"),
        URaftSimSaveSubsystem::SelectCheckpoint(Save,9000,9020,NewFrame,TEXT("/Game/RaftSim/Maps/L_Hance"),Found));
    URaftSimSaveSubsystem::ApplyCareerCheckpoint(Save,Old.ScenarioId,NAME_None,9020.f,Current,NewFrame);
    TestEqual(TEXT("same-frame checkpoint adds no historical duplicate"),Save->HistoricalRouteProgress.Num(),1);
    FRaftSimRunResult Result;
    Result.ScenarioId=Old.ScenarioId; Result.CoordinateMapPath=NewFrame;
    Result.OverallScore=.5f; Result.SafetyScore=.8f; Result.RunTimeSeconds=150.f;
    Result.GhostRoute={FVector(-4000,-3000,40),FVector(-4100,-3100,42)};
    URaftSimSaveSubsystem::ApplyRunResult(Save,Result);
    TestTrue(TEXT("first new-frame ghost is accepted independently of historical best score"),Active.BestGhostRoute==Result.GhostRoute);
    TArray<uint8> Bytes;
    if (!TestTrue(TEXT("additive save serializes in memory"),UGameplayStatics::SaveGameToMemory(Save,Bytes))) return false;
    auto* Loaded=Cast<URaftSimVerticalSliceSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    if (!TestNotNull(TEXT("save round trip loads"),Loaded)) return false;
    TestTrue(TEXT("active frame and historical coordinates survive serialization"),
        Loaded->ScenarioProgress[0].CoordinateMapPath==NewFrame && Loaded->HistoricalRouteProgress.Num()==1 &&
        Loaded->HistoricalRouteProgress[0].BestGhostRoute==Old.BestGhostRoute);
    TestEqual(TEXT("schema revision persists"),Loaded->SaveVersion,URaftSimSaveSubsystem::CurrentSaveVersion);
    return !HasAnyErrors();
}

#if RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianCheckpointTest,"RaftSim.Survey.CartesianCheckpointDestination",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianCheckpointTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Config=World->SpawnActor<ARaftSimRiverWaterConfig>();
    auto* Run=World->SpawnActor<ARaftSimRunManager>();
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>(Run);
    FRaftSimWaterRuntimeConfig Runtime;
    Runtime.bRequireAcceptedReportManifest=false; Runtime.bEnableDeterministicCapture=false;
    Water->Configure(Runtime);
    const FString Base=TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/");
    if (!Water->ConfigureRiverCoordinateMap(Base+TEXT("hydraulic_regions_context/coordinate_map.json")) ||
        !Run->ConfigureProgressCoordinateMap(Base+TEXT("playable_route/coordinate_map.json"))) return false;
    Config->StreamingManifestPath=TEXT("tmp/south-fork-runtime-atlas-600s-v1-20260912/streaming_manifest_verified.json");
    Config->CookedFieldsDir=TEXT("deliberately-invalid-initial-packet-checkpoint-must-select-destination");
    const auto* Progress=Run->GetProgressCoordinates(Water);
    FVector LastPosition;
    for (float Station : {120.f,8343.9455f,9012.3264f,25427.6352f,29933.0304f,33280.f})
    {
        FVector Position;
        if (!Progress->RiverToWorldPosition(FVector2D(Station,0),220.f,Position)) return false;
        FTransform Checkpoint(Position);
        if (!TestTrue(*FString::Printf(TEXT("real full-river destination %.3fm selects a wet geographic packet"),Station),
            Run->SeedCartesianCheckpointWater(Config,Water,Checkpoint))) return false;
        FRaftSimWaterSample Sample;
        if (!TestTrue(TEXT("destination is authoritative wet water"),Water->SampleWaterAtWorldPosition(Checkpoint.GetLocation(),Sample) && Sample.bWet)) return false;
        TestTrue(TEXT("spawn Z applies datum once and keeps 40cm launch clearance"),
            FMath::Abs(Checkpoint.GetLocation().Z-(Sample.SurfaceHeightMeters*100.f+40.f))<.001);
        TestTrue(TEXT("water selection never changes route XY"),Checkpoint.GetLocation().X==Position.X && Checkpoint.GetLocation().Y==Position.Y);
        LastPosition=Checkpoint.GetLocation();
    }
    // Reject an available but actually dry point without replacing the water
    // underneath the current raft, its clock, or handoff bookkeeping.
    FBox2D Bounds; Water->GetLiveWaterFieldBoundsM(Bounds);
    bool FoundDry=false;
    for (double Y=Bounds.Min.Y+12.; !FoundDry && Y<Bounds.Max.Y-12.; Y+=8.)
        for (double X=Bounds.Min.X+12.; !FoundDry && X<Bounds.Max.X-12.; X+=8.)
        {
            FRaftSimWaterSample Sample;
            if (!Water->SampleWaterFieldAtRiverCoordinates(FVector2D(X,Y),Sample) || Sample.bWet) continue;
            FVector Position; Water->RiverToWorldPosition(FVector2D(X,Y),220.f,Position);
            FTransform Dry(Position); const FTransform BeforeTransform=Dry;
            FRaftSimWaterLiveWindowStats Before,After;
            Water->GetLiveWindowStats(Before);
            TestFalse(TEXT("dry destination is rejected"),Run->SeedCartesianCheckpointWater(Config,Water,Dry));
            Water->GetLiveWindowStats(After);
            TestTrue(TEXT("rejected destination preserves transform and live state"),Dry.Equals(BeforeTransform,0.f) &&
                Before.TotalWaterVolumeM3==After.TotalWaterVolumeM3 && Before.SimTimeSeconds==After.SimTimeSeconds &&
                Before.MovingWindowHandoffCount==After.MovingWindowHandoffCount &&
                Before.LastHandoffTransferredCellCount==After.LastHandoffTransferredCellCount);
            TestTrue(TEXT("current raft's water remains wet after rejected teleport"),
                Water->SampleWaterAtWorldPosition(LastPosition,Sample) && Sample.bWet);
            FoundDry=true;
        }
    TestTrue(TEXT("fixture exercised an available dry destination"),FoundDry);
    AddInfo(TEXT("Six real 600-second full-river destinations; exact geographic source selection and transactional dry rejection. Not full-scene traversal acceptance."));
    return !HasAnyErrors();
}
#endif
#endif
