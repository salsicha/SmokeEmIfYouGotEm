// Opt-in normal-input gameplay observation with localized rock attribution and explicit recovery. No physics tuning.
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Tests/AutomationCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include "RaftSimRaftActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRapidChallengeProfiles.h"
#include "RaftSimTrialSteeringSchedule.h"
#include "RaftSimTrialRockApproach.h"
#include "RaftSimTrialStallRecovery.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "RaftSimRockObstacleActor.h"
#include "../RaftSimRunManager.h"

#if WITH_AUTOMATION_TESTS
// Test-only preparation; never invoked by normal gameplay checkpoint repair.
class FRaftSimRiverTrialSetup
{
public:
    static void ResetCondition(ARaftSimRaftActor& Raft) { Raft.RaftCondition=FRaftSimRaftConditionState{}; }
    static void RefillCrew(ARaftSimRaftActor& Raft) { Raft.CrewStamina.Init(1.f,Raft.GetCrewAvatarCount()); }
};

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimIndependentTrialSetupTest,
    "RaftSim.Review.IndependentTrialSetup",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimIndependentTrialSetupTest::RunTest(const FString&)
{
    auto* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if(!TestNotNull(TEXT("test world"),World))return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false);World->RemoveFromRoot(); };
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>();
    if(!TestNotNull(TEXT("production raft"),Raft))return false;
    Raft->CrewAvatars.SetNum(4);Raft->CrewStamina.Init(.07f,4);
    Raft->RaftCondition.FabricIntegrity=.6f;Raft->RaftCondition.PermanentCreaseAmplitudeM=.15f;
    Raft->RaftCondition.PinEventCount=9;
    const auto Repair=URaftSimRaftConditionLibrary::ApplyCheckpointRepair(Raft->RaftCondition);
    TestTrue(TEXT("ordinary repair retains history"),Repair.PermanentCreaseAmplitudeM>0);
    FRaftSimRiverTrialSetup::ResetCondition(*Raft);FRaftSimRiverTrialSetup::RefillCrew(*Raft);
    TestEqual(TEXT("all four test crew replenished"),Raft->CrewStamina.Num(),4);
    for(float Stamina:Raft->CrewStamina)TestEqual(TEXT("equal initial stamina"),Stamina,1.f);
    TestEqual(TEXT("intact fabric"),Raft->RaftCondition.FabricIntegrity,1.f);
    TestEqual(TEXT("no inherited crease"),Raft->RaftCondition.PermanentCreaseAmplitudeM,0.f);
    TestEqual(TEXT("no inherited pins"),Raft->RaftCondition.PinEventCount,0);
    return !HasAnyErrors();
}

namespace
{
class FRiverDifficultyReview : public IAutomationLatentCommand
{
public:
    FRiverDifficultyReview(FAutomationTestBase* T, TSharedPtr<FJsonObject> P) : Test(T), Plan(P) {}
    bool Update() override;
private:
    void Finish(const FString& Reason);
    FAutomationTestBase* Test;
    TSharedPtr<FJsonObject> Plan, Result;
    TArray<TSharedPtr<FJsonValue>> Samples, Results, GateReceipts;
    int32 Index=0, Phase=0, Strokes=0, Changes=0;
    double Wall=0, Start=0, LastSample=0, LastInput=0, BestStation=0, LastProgress=0, SimulationLimit=1800;
    double MaxRoll=0, MaxPitch=0, MaxSpeed=0, PinSeconds=0, DrySeconds=0;
    double PreviousSample=0, TurnSeconds=0, MinUp=1, GroundSeconds=0;
    double MinimumCenterClearance=DBL_MAX,LastCapturedClearance=-2.;
    int32 MaxSwimmers=0, MaxContacts=0;
    bool Finite=true;
    bool ConfigCached=false, MovingWindow=false, RecenterCrux=false;
    FString FieldsDirectory, FlowBand, StreamingManifest;
    FVector2D WindowExtent;
    int32 InitialOarStrokes=0, PreparationAttempts=0, BlockedPlacements=0;
    uint64 InitialRestores=0;
    FRaftSimHullContactTotals InitialHullContact;
    double Lane=0, InitialHeading=0, MistakeStart=-1, RecoveryAt=-1, LastRecoveryInput=-1;
    double MistakeDuration=0, InputInterval=.85, StallLimit=60, WallLimit=900;
    double MaximumRouteError=0;
    double BackStrokeSeconds=0;
    int32 ReflipRequests=0, HighSides=0;
    bool Assessment=false, MistakeDone=false, Capsized=false, HandsOff=false;
    bool StrictRoute=false, Continuous=false, RescueEnabled=false;
    FRaftSimTrialSteeringSchedule Steering;
    FRaftSimTrialStallRecovery StallRecovery;
    double HeadingStart=DBL_MAX, HeadingEnd=-DBL_MAX, HeadingOffset=0;
    double RescueDrillStation=-1;
    bool RescueDrillIssued=false;
    bool TargetPhysicalRock=false,HasTargetRock=false;
    double TargetRockStation=0,TargetRockLateral=0;
    FVector TargetRockWorld=FVector::ZeroVector;
    FString TargetRockSource;
    TSet<FString> PhysicalOwnersSeen;
    TSet<TWeakObjectPtr<UStaticMeshComponent>> InspectedContactOwners;
    TArray<TWeakObjectPtr<UStaticMeshComponent>> TargetContactOwners;
    uint64 TargetOwnerImpulses=0,SampledTargetOwnerImpulses=0;
    double LastTargetContact=-DBL_MAX,ClosestTargetDistance=DBL_MAX,TargetPinSampleSeconds=0;
    bool HeadingHeld=false;
    FVector2D PreviousRoute=FVector2D::ZeroVector;
    TSet<FString> CrossedGates;
    TSet<int32> NamedSitesSeen,NamedSitesEncountered;
    int32 NamedSitesExpected=0;
    int32 RescueAttempts=0, RescueCompletionsAtStart=0;
    ERaftSimCrewCommand Command=ERaftSimCrewCommand::Rest;
};

void FRiverDifficultyReview::Finish(const FString& Reason)
{
    Result->SetStringField(TEXT("outcome"),Reason);
    Result->SetNumberField(TEXT("max_abs_roll_deg"),MaxRoll);
    Result->SetNumberField(TEXT("max_abs_pitch_deg"),MaxPitch);
    Result->SetNumberField(TEXT("max_speed_mps"),MaxSpeed);
    Result->SetNumberField(TEXT("minimum_up_z"),MinUp);
    Result->SetNumberField(TEXT("max_swimmers"),MaxSwimmers);
    Result->SetNumberField(TEXT("max_contacts"),MaxContacts);
    Result->SetNumberField(TEXT("pin_seconds"),PinSeconds);
    Result->SetNumberField(TEXT("grounded_seconds"),GroundSeconds);
    Result->SetNumberField(TEXT("dry_center_seconds"),DrySeconds);
    Result->SetNumberField(TEXT("turn_command_seconds"),TurnSeconds);
    Result->SetNumberField(TEXT("guide_strokes"),Strokes);
    Result->SetNumberField(TEXT("crew_command_changes"),Changes);
    Result->SetBoolField(TEXT("finite"),Finite);
    Result->SetNumberField(TEXT("maximum_route_error_m"),MaximumRouteError);
    Result->SetNumberField(TEXT("backstroke_seconds"),BackStrokeSeconds);
    Result->SetNumberField(TEXT("mistake_start_s"),MistakeStart);
    Result->SetNumberField(TEXT("recovered_route_at_s"),RecoveryAt);
    Result->SetNumberField(TEXT("reflip_requests"),ReflipRequests);
    Result->SetNumberField(TEXT("high_side_responses"),HighSides);
    Result->SetBoolField(TEXT("capsized_during_trial"),Capsized);
    Result->SetArrayField(TEXT("gate_receipts"),GateReceipts);
    Result->SetNumberField(TEXT("rescue_attempts"),RescueAttempts);
    Result->SetNumberField(TEXT("named_challenge_sites_seen"),NamedSitesSeen.Num());
    Result->SetNumberField(TEXT("named_challenge_sites_loaded_in_section"),NamedSitesSeen.Num());
    Result->SetNumberField(TEXT("named_challenge_sites_expected_in_section"),NamedSitesExpected);
    Result->SetNumberField(TEXT("named_challenge_footprints_crossed"),NamedSitesEncountered.Num());
    Result->SetStringField(TEXT("named_challenge_observation_scope"),TEXT("Loaded sites intersect this trial's station range. Footprint crossings require the actual raft centre inside a loaded compact relief footprint; they are not hull impulse, force magnitude or visual acceptance. A legitimate bypass need not cross one."));
    Result->SetBoolField(TEXT("rest_exit_recovery_started"),StallRecovery.StartedAt>=0);
    if(StallRecovery.StartedAt>=0)
        Result->SetNumberField(TEXT("rest_exit_recovery_started_at_s"),StallRecovery.StartedAt);
    if(TargetPhysicalRock)
    {
        Result->SetNumberField(TEXT("target_owner_impulses"),TargetOwnerImpulses);
        Result->SetNumberField(TEXT("physical_owner_sources_seen"),PhysicalOwnersSeen.Num());
        Result->SetNumberField(TEXT("pin_while_target_contact_sampled_seconds"),TargetPinSampleSeconds);
        if(ClosestTargetDistance!=DBL_MAX)Result->SetNumberField(TEXT("closest_target_center_distance_m"),ClosestTargetDistance);
        Result->SetStringField(TEXT("target_distance_scope"),TEXT("Horizontal centre-to-owner distance, NOT hull/rock clearance. Owner impulses are from committed original-triangle contacts; pin/contact overlap uses 0.2-second observation intervals."));
    }
    if(MinimumCenterClearance!=DBL_MAX)
    {
        Result->SetNumberField(TEXT("minimum_center_clearance_m"),MinimumCenterClearance);
        double RequiredMinimum=0.;
        if(Plan->TryGetNumberField(TEXT("minimum_center_clearance_m"),RequiredMinimum))
            Test->TestTrue(TEXT("boat remains within the required water-surface clearance"),MinimumCenterClearance>=RequiredMinimum);
    }
    Result->SetArrayField(TEXT("samples"),Samples);
    Results.Add(MakeShared<FJsonValueObject>(Result));
    const FString Dir=Plan->GetStringField(TEXT("output_dir"));
    IFileManager::Get().MakeDirectory(*Dir,true);
    FString Json;
    FJsonSerializer::Serialize(Result.ToSharedRef(),TJsonWriterFactory<>::Create(&Json));
    FFileHelper::SaveStringToFile(Json,*(Dir/Result->GetStringField(TEXT("id"))+TEXT(".json")));
    FScreenshotRequest::RequestScreenshot(Dir/(Result->GetStringField(TEXT("id"))+TEXT("-end.png")),true,false);
    UE_LOG(LogTemp,Display,TEXT("DIFFICULTY_TRIAL %s outcome=%s roll=%.1f pitch=%.1f swims=%d pin_s=%.1f"),
        *Result->GetStringField(TEXT("id")),*Reason,MaxRoll,MaxPitch,MaxSwimmers,PinSeconds);
    ++Index; Phase=0; Samples.Reset();
    MaxRoll=MaxPitch=MaxSpeed=PinSeconds=DrySeconds=GroundSeconds=TurnSeconds=0; MinUp=1;
    Strokes=Changes=MaxSwimmers=MaxContacts=0; Finite=true;
    MinimumCenterClearance=DBL_MAX;LastCapturedClearance=-2.;
    MaximumRouteError=BackStrokeSeconds=0;MistakeStart=RecoveryAt=LastRecoveryInput=-1;
    ReflipRequests=HighSides=0;MistakeDone=Capsized=false;
    PreparationAttempts=BlockedPlacements=0;
    GateReceipts.Reset();CrossedGates.Reset();RescueAttempts=0;
    NamedSitesSeen.Reset();NamedSitesEncountered.Reset();NamedSitesExpected=0;
    RescueDrillIssued=false;
}

bool FRiverDifficultyReview::Update()
{
    const auto& Trials=Plan->GetArrayField(TEXT("trials"));
    if(Index>=Trials.Num())
    {
        auto Summary=MakeShared<FJsonObject>();
        Summary->SetStringField(TEXT("scope"),TEXT("Normal-input trials; continuous_sequence marks one uninterrupted multi-rapid trial with no intermediate reset. Not human playtests, real-world grades, or measured safe lines."));
        Summary->SetArrayField(TEXT("trials"),Results);
        FString Json; FJsonSerializer::Serialize(Summary,TJsonWriterFactory<>::Create(&Json));
        Test->TestTrue(TEXT("Difficulty observations saved"),FFileHelper::SaveStringToFile(Json,*(Plan->GetStringField(TEXT("output_dir"))/TEXT("results.json"))));
        return true;
    }
    UWorld* World=nullptr;
    for(const auto& Context:GEngine->GetWorldContexts())
        if(Context.WorldType==EWorldType::PIE || Context.WorldType==EWorldType::Game) {World=Context.World();break;}
    if(!World) {Test->AddError(TEXT("No game world"));return true;}
    auto* Bridge=World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    auto* Water=Bridge?Bridge->GetWaterRuntime():nullptr;
    auto* Physics=Bridge?Bridge->GetRaftRuntime():nullptr;
    ARaftSimRaftActor* Raft=nullptr; ARaftSimRunManager* Run=nullptr; ARaftSimRiverWaterConfig* Config=nullptr;
    for(TActorIterator<ARaftSimRaftActor> It(World);It;++It){Raft=*It;break;}
    for(TActorIterator<ARaftSimRunManager> It(World);It;++It){Run=*It;break;}
    for(TActorIterator<ARaftSimRiverWaterConfig> It(World);It;++It){Config=*It;break;}
    if(!Raft||!Run||!Water||!Physics||(!Config&&!ConfigCached)){Test->AddError(TEXT("Missing production game runtime"));return true;}
    // The put-in config actor may unload on a long world-partitioned reach.
    if(!ConfigCached)
    {
        FieldsDirectory=Config->CookedFieldsDir; FlowBand=Config->FlowBand.ToString();
        StreamingManifest=Config->StreamingManifestPath;
        MovingWindow=Config->bEnableMovingWindowStreaming; RecenterCrux=Config->bRecenterHydraulicCrux;
        WindowExtent=MovingWindow?FVector2D(Config->MovingWindowStationExtentM,Config->MovingWindowLateralExtentM):
            FVector2D(Config->WindowExtentM,Config->WindowExtentM);
        ConfigCached=true;
    }
    const auto Trial=Trials[Index]->AsObject();
    const auto PreferredLateral=[&](double Station)
    {
        if(HasTargetRock && Station>=TargetRockStation-100. && Station<=TargetRockStation+5.)return TargetRockLateral;
        const TArray<TSharedPtr<FJsonValue>>* Waypoints=nullptr;
        if(!Trial->TryGetArrayField(TEXT("route_laterals"),Waypoints)||!Waypoints||Waypoints->IsEmpty())return Lane;
        double PreviousS=(*Waypoints)[0]->AsArray()[0]->AsNumber();
        double PreviousL=(*Waypoints)[0]->AsArray()[1]->AsNumber();
        if(Station<=PreviousS)return Lane+PreviousL;
        for(int32 I=1;I<Waypoints->Num();++I)
        {
            const auto& Point=(*Waypoints)[I]->AsArray();
            const double S=Point[0]->AsNumber(),L=Point[1]->AsNumber();
            if(Station<=S)return Lane+FMath::Lerp(PreviousL,L,FMath::Clamp((Station-PreviousS)/FMath::Max(.001,S-PreviousS),0.,1.));
            PreviousS=S;PreviousL=L;
        }
        return Lane+PreviousL;
    };
    const double Now=World->GetTimeSeconds();
    const auto* Progress=Run->GetProgressCoordinates(Water);
    if(Phase==0)
    {
        Result=MakeShared<FJsonObject>();
        Result->Values=Trial->Values;
        Result->SetStringField(TEXT("map"),World->GetMapName());
        Result->SetStringField(TEXT("flow_band"),FlowBand);
        Result->SetStringField(TEXT("cooked_fields_dir"),FieldsDirectory);
        Result->SetStringField(TEXT("streaming_manifest"),StreamingManifest);
        Result->SetStringField(TEXT("progress_map"),Run->ProgressCoordinateMapPath);
        Result->SetStringField(TEXT("driver"),TEXT("12 m centerline lookahead; shared production turn/forward commands and personal steering every 0.85 s on both paddle and oar rigs; no high-side or rescue automation."));
        Result->SetBoolField(TEXT("solo_oar_rig"),Raft->IsSoloOarRig());
        Result->SetBoolField(TEXT("full_continuous_run"),false);
        Result->SetNumberField(TEXT("assessment_protocol_version"),17);
        Assessment=Trial->HasField(TEXT("variant"));
        StrictRoute=Continuous=RescueEnabled=false;
        TargetPhysicalRock=HasTargetRock=false;
        TargetRockSource.Reset();PhysicalOwnersSeen.Reset();InspectedContactOwners.Reset();TargetContactOwners.Reset();
        TargetOwnerImpulses=SampledTargetOwnerImpulses=0;TargetPinSampleSeconds=0;
        LastTargetContact=-DBL_MAX;ClosestTargetDistance=DBL_MAX;HeadingHeld=false;
        Trial->TryGetBoolField(TEXT("target_physical_rock"),TargetPhysicalRock);
        Trial->TryGetBoolField(TEXT("strict_route"),StrictRoute);
        Trial->TryGetBoolField(TEXT("continuous_sequence"),Continuous);
        Trial->TryGetBoolField(TEXT("normal_rescue_inputs"),RescueEnabled);
        if(!Steering.Read(*Trial)){Finish(TEXT("invalid_steering_schedule"));return false;}
        if(!StallRecovery.Read(*Trial)){Finish(TEXT("invalid_stall_recovery_policy"));return false;}
        HeadingStart=DBL_MAX;HeadingEnd=-DBL_MAX;HeadingOffset=0;RescueDrillStation=-1;
        Trial->TryGetNumberField(TEXT("heading_start_m"),HeadingStart);
        Trial->TryGetNumberField(TEXT("heading_end_m"),HeadingEnd);
        Trial->TryGetNumberField(TEXT("heading_offset_deg"),HeadingOffset);
        Trial->TryGetNumberField(TEXT("rescue_drill_station_m"),RescueDrillStation);
        Result->SetBoolField(TEXT("controlled_overboard_drill"),RescueDrillStation>=0);
        Result->SetBoolField(TEXT("continuous_sequence"),Continuous);
        Lane=InitialHeading=MistakeDuration=0;InputInterval=.85;StallLimit=Assessment?60:15;WallLimit=900;
        Trial->TryGetNumberField(TEXT("lane_m"),Lane);
        Trial->TryGetNumberField(TEXT("initial_heading_deg"),InitialHeading);
        Trial->TryGetNumberField(TEXT("mistake_seconds"),MistakeDuration);
        Trial->TryGetNumberField(TEXT("input_interval_s"),InputInterval);
        Trial->TryGetNumberField(TEXT("stall_limit_s"),StallLimit);
        Trial->TryGetNumberField(TEXT("wall_limit_s"),WallLimit);
        SimulationLimit=Plan->GetNumberField(TEXT("seconds_per_trial"));
        Trial->TryGetNumberField(TEXT("simulation_limit_s"),SimulationLimit);
        if(!FMath::IsFinite(SimulationLimit) || SimulationLimit<=0.){Finish(TEXT("invalid_trial_time_limit"));return false;}
        if(Assessment)Result->SetStringField(TEXT("driver"),TEXT("Live-water depth scouting over a raft-sized footprint with preferred lateral lanes; normal crew/guide inputs at 0.85 s, deliberate 6 s steering omission, 12/40 m lookahead, ordinary backstroke/high-side/reflip recovery. No checkpoint recovery or injected forces. Scouted-route game assessment, not a human skill grade."));
        // Hands-off: the boat is placed on the center line and left alone. No
        // crew call, steering, high-side or reflip; what the river alone does.
        HandsOff=Assessment && Trial->GetStringField(TEXT("variant"))==TEXT("hands-off");
        if(HandsOff)Result->SetStringField(TEXT("driver"),TEXT("Hands-off: placed on the center lane at the checkpoint, crew resting, no guide or crew input of any kind for the whole trial. Tests whether the rapid can be passed without action."));
        if(StrictRoute)Result->SetStringField(TEXT("driver"),TEXT("Fixed authored route; NO depth scouting, start-lane fallback or adaptive lookahead. Station-bounded steering through ordinary crew/guide inputs. Gate crossings measure the actual route; no gate teleports or forces. Normal recovery only when explicitly enabled."));
        if(Trial->HasField(TEXT("portage")) && Trial->GetBoolField(TEXT("portage")))
        {Finish(TEXT("mandatory_portage_not_driven"));return false;}
        float RouteMin=0,RouteMax=0;
        if(Progress)Progress->GetRiverStationRangeM(RouteMin,RouteMax);
        Result->SetNumberField(TEXT("mapped_start_m"),RouteMin);
        Result->SetNumberField(TEXT("mapped_end_m"),RouteMax);
        if(!Progress || Trial->GetNumberField(TEXT("finish_m"))>double(RouteMax)+.01 ||
            Trial->GetNumberField(TEXT("start_m"))<double(RouteMin)-.01)
        {Finish(TEXT("test_extent_outside_mapped_reach"));return false;}
        FTransform Destination;
        if(!Progress || !ARaftSimRunManager::BuildStationStartTransform(Progress,Water,
            Trial->GetNumberField(TEXT("start_m")),Destination))
        {Finish(TEXT("start_coordinate_unavailable"));return false;}
        // A lane start that lands the hull on a bank or rock is moved toward
        // the center line (half, then all the way) before the trial begins.
        const double StartLateral=PreferredLateral(Trial->GetNumberField(TEXT("start_m")))*(StrictRoute?1.:BlockedPlacements==0?1.:BlockedPlacements==1?.5:0.);
        Result->SetNumberField(TEXT("start_lateral_m"),StartLateral);
        Result->SetNumberField(TEXT("blocked_start_placements"),BlockedPlacements);
        if(StartLateral!=0)
        {
            FVector Shifted;
            if(!Progress->RiverToWorldPosition(FVector2D(Trial->GetNumberField(TEXT("start_m")),StartLateral),
                Progress->GetRiverVerticalDatumM(),Shifted))
            {Finish(TEXT("offset_start_unavailable"));return false;}
            Shifted.Z=Destination.GetLocation().Z;
            Destination.SetLocation(Shifted);
        }
        Destination.SetRotation((Destination.Rotator()+FRotator(0,InitialHeading,0)).Quaternion());
        // Independent trials intentionally jump between distant sections.
        // Seed the destination's real cooked water before sampling its height;
        // the old live window cannot supply a distant checkpoint's elevation.
        // Cartesian checkpoint preparation already selects its native packet.
        if(!Water->HasCartesianWaterCoordinates())
        {
            FVector2D HydraulicCenter; FVector Tangent,Left;
            FRaftSimWaterSample DestinationWater;
            if(!Water->WorldToRiverCoordinates(Destination.GetLocation(),HydraulicCenter,Tangent,Left) ||
                !Water->ConfigureRiverWindow(FieldsDirectory,FlowBand,HydraulicCenter,WindowExtent,.041f,RecenterCrux) ||
                !Water->SampleWaterAtWorldPosition(Destination.GetLocation(),DestinationWater) || !DestinationWater.bWet)
            {Finish(TEXT("destination_water_unavailable"));return false;}
            FVector Position=Destination.GetLocation();
            Position.Z=DestinationWater.SurfaceHeightMeters*100.+40.;
            Destination.SetLocation(Position);
            Result->SetBoolField(TEXT("destination_water_seeded_before_placement"),true);
        }
        Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
        // Reset before checkpoint preparation rebuilds the production hull.
        FRaftSimRiverTrialSetup::ResetCondition(*Raft);
        ++PreparationAttempts;
        if(!Raft->TryRestoreCheckpoint(Destination))
        {
            // A cold world-partition destination can finish activation on the
            // next world tick after its blocking load. These bounded retries
            // are BEFORE the trial, never a recovery during a navigation test.
            if(PreparationAttempts<3)return false;
            Result->SetNumberField(TEXT("preparation_attempts"),PreparationAttempts);
            Finish(TEXT("checkpoint_preparation_rejected"));return false;
        }
        Result->SetNumberField(TEXT("preparation_attempts"),PreparationAttempts);
        InitialRestores=Raft->GetCheckpointRestoreCount();
        Wall=FPlatformTime::Seconds(); Start=Now; Phase=1;
        return false;
    }
    if(Phase==1)
    {
        if(Now-Start<3) return false;
        if(Bridge->IsRaftStepFailureLatched())
        {
            if(!StrictRoute && ++BlockedPlacements<3){PreparationAttempts=0;Phase=0;return false;}
            Finish(TEXT("start_placement_intersects_ground"));return false;
        }
        const auto& State=Physics->GetKinematicState();
        FVector2D Route; FVector Tangent,Left;
        if(!Run->WorldToRunCoordinates(State.WorldTransform.GetLocation(),Water,Route,Tangent,Left))
        {Finish(TEXT("start_projection_unavailable"));return false;}
        Result->SetNumberField(TEXT("actual_start_m"),Route.X);
        Result->SetNumberField(TEXT("actual_start_lateral_m"),Route.Y);
        Result->SetNumberField(TEXT("actual_start_yaw_deg"),State.WorldTransform.Rotator().Yaw);
        Result->SetNumberField(TEXT("actual_start_heading_relative_deg"),FMath::FindDeltaAngleDegrees(Tangent.Rotation().Yaw,State.WorldTransform.Rotator().Yaw));
        Result->SetNumberField(TEXT("actual_start_roll_deg"),State.WorldTransform.Rotator().Roll);
        Result->SetNumberField(TEXT("actual_start_pitch_deg"),State.WorldTransform.Rotator().Pitch);
        Result->SetNumberField(TEXT("actual_start_velocity_x_mps"),State.LinearVelocityMetersPerSecond.X);
        Result->SetNumberField(TEXT("actual_start_velocity_y_mps"),State.LinearVelocityMetersPerSecond.Y);
        Result->SetNumberField(TEXT("actual_start_velocity_z_mps"),State.LinearVelocityMetersPerSecond.Z);
        Result->SetNumberField(TEXT("actual_start_yaw_rate_radps"),State.AngularVelocityRadiansPerSecond.Z);
        PreviousRoute=Route;
        RescueCompletionsAtStart=Raft->GetCompletedRescueCount();
        InitialHullContact=Physics->GetHullContactTotals();
        Result->SetStringField(TEXT("ground_contact_scope"),TEXT("Committed full-hull impulse totals; grounded_seconds is the duration of fixed steps containing impulses, not resting-contact duration or a measured clearance."));
        if(FMath::Abs(Route.X-Trial->GetNumberField(TEXT("start_m")))>30)
        {Finish(TEXT("checkpoint_start_mismatch"));return false;}
        FRaftSimWaterSample InitialWater;
        if(!Water->SampleWaterAtWorldPosition(State.WorldTransform.GetLocation(),InitialWater)||!InitialWater.bWet)
        {Finish(TEXT("initial_water_unavailable"));return false;}
        const double Clearance=State.WorldTransform.GetLocation().Z*.01-InitialWater.SurfaceHeightMeters;
        Result->SetNumberField(TEXT("initial_center_minus_surface_m"),Clearance);
        if(!FMath::IsFinite(Clearance)||FMath::Abs(Clearance)>2.)
        {Finish(TEXT("initial_surface_alignment_rejected"));return false;}
        FRaftSimRiverTrialSetup::RefillCrew(*Raft);
        const auto InitialCondition=Raft->GetRaftCondition();
        Result->SetBoolField(TEXT("independent_trial_state_reset"),true);
        Result->SetNumberField(TEXT("initial_crew_energy"),Raft->GetCrewEnergy());
        Result->SetNumberField(TEXT("initial_guide_stamina"),Raft->GetCrewStamina(TEXT("guide")));
        Result->SetNumberField(TEXT("initial_fabric_integrity"),InitialCondition.FabricIntegrity);
        Result->SetNumberField(TEXT("initial_pressure_fraction"),InitialCondition.PressureFraction);
        Result->SetNumberField(TEXT("initial_permanent_crease_m"),InitialCondition.PermanentCreaseAmplitudeM);
        auto StaminaReceipt=MakeShared<FJsonObject>();
        for(int32 I=0;I<Raft->GetCrewAvatarCount();++I)
        {
            const FString Id=I==Raft->GetCrewAvatarCount()-1?TEXT("guide"):FString::Printf(TEXT("paddler_%d"),I+1);
            StaminaReceipt->SetNumberField(Id,Raft->GetCrewStamina(FName(*Id)));
        }
        Result->SetObjectField(TEXT("initial_crew_stamina"),StaminaReceipt);
        if(InitialCondition.FabricIntegrity<.999f || InitialCondition.PressureFraction<.999f ||
            InitialCondition.PermanentCreaseAmplitudeM>1.e-6f || Raft->GetCrewAvatarCount()==0)
        {Finish(TEXT("initial_trial_state_not_fresh"));return false;}
        Start=LastProgress=Now; BestStation=Route.X; LastSample=LastInput=PreviousSample=Now;
        InitialOarStrokes=Raft->GetOarRig()?Raft->GetOarRig()->GetCompletedStrokeCount():0;
        Command=HandsOff?ERaftSimCrewCommand::Rest:ERaftSimCrewCommand::AllForward;
        if(!HandsOff)Raft->IssueCrewCommand(Command);
        Phase=2;
        FScreenshotRequest::RequestScreenshot(Plan->GetStringField(TEXT("output_dir"))/(Trial->GetStringField(TEXT("id"))+TEXT("-start.png")),true,false);
        return false;
    }
    const auto& State=Physics->GetKinematicState();
    const FVector Position=State.WorldTransform.GetLocation();
    FVector2D Route; FVector Tangent,Left;
    if(!Run->WorldToRunCoordinates(Position,Water,Route,Tangent,Left))
    {Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);Finish(TEXT("left_mapped_route"));return false;}
    FRaftSimWaterSample WaterSample;
    const bool Wet=Water->SampleWaterAtWorldPosition(Position,WaterSample)&&WaterSample.bWet;
    const double Elapsed=Now-Start;
    const auto& NamedFeatures=RaftSimRapidChallengeProfiles::Features(Plan->GetStringField(TEXT("map")));
    NamedSitesExpected=0;
    for(int32 I=0;I<NamedFeatures.Num();++I)
    {
        const auto& F=NamedFeatures[I];
        if(!RaftSimRapidChallengeProfiles::OverlapsReach(F,Trial->GetNumberField(TEXT("start_m")),Trial->GetNumberField(TEXT("finish_m"))))continue;
        ++NamedSitesExpected;
        for(const auto& Site:Water->GetFeatureBreakingSites())
            if(Site.bLocalEnvelopeCap && Site.PhysicalCrestHeightMeters>0 &&
                Site.RiverCoordinatesMeters.Equals(FVector2D(F.Station,F.Lateral),.01))
            {
                NamedSitesSeen.Add(I);
                if(RaftSimRapidChallengeProfiles::InsideReliefFootprint(F,Route))NamedSitesEncountered.Add(I);
            }
    }
    // Inspect streamed owners throughout the approach; do not wait until the
    // ferry is already due. Missing geometry is never replaced by a fixture.
    if(TargetPhysicalRock && !HasTargetRock)
    {
        double Best=DBL_MAX;
        for(const auto& Rock:Water->GetFeatureBoulderFootprints())
        {
            if(Rock.PhysicalSource.IsEmpty() || !FMath::IsFinite(Rock.RadiusMeters) || Rock.RadiusMeters<=0.)continue;
            PhysicalOwnersSeen.Add(Rock.PhysicalSource);
            const auto* Source=FindObject<UObject>(nullptr,*Rock.PhysicalSource);
            const auto* Mesh=Cast<UStaticMeshComponent>(Source);
            const auto* Actor=Cast<AActor>(Source);
            const bool Dedicated=(Actor && Actor->IsA<ARaftSimRockObstacleActor>()) ||
                (Mesh && Mesh->GetOwner() && Mesh->GetOwner()->IsA<ARaftSimRockObstacleActor>());
            if(!RaftSimTrialRockApproach::IsLocalizedOwner(Dedicated,
                Mesh && Mesh->GetStaticMesh()?Mesh->GetStaticMesh()->GetName():FString()))continue;
            FVector W;FVector2D R;FVector T,L;
            if(!Water->RiverToWorldPosition(Rock.RiverCoordinatesMeters,Water->GetRiverVerticalDatumM(),W) ||
                !Run->WorldToRunCoordinates(W,Water,R,T,L) ||
                !RaftSimTrialRockApproach::Eligible(Route,R,Trial->GetNumberField(TEXT("control_m")),Trial->GetNumberField(TEXT("finish_m"))))continue;
            const double Distance=FMath::Abs(R.X-Trial->GetNumberField(TEXT("control_m")));
            if(Distance>=Best)continue;
            Best=Distance;HasTargetRock=true;TargetRockStation=R.X;TargetRockLateral=R.Y;
            TargetRockWorld=W;TargetRockSource=Rock.PhysicalSource;
            Result->SetStringField(TEXT("target_rock_source"),Rock.PhysicalSource);
            Result->SetNumberField(TEXT("target_rock_station_m"),R.X);
            Result->SetNumberField(TEXT("target_rock_lateral_m"),R.Y);
            Result->SetNumberField(TEXT("target_selected_at_station_m"),Route.X);
            Result->SetNumberField(TEXT("target_owner_wake_radius_m"),Rock.RadiusMeters);
        }
        if(HasTargetRock)
        {
            HeadingStart=TargetRockStation-40.;HeadingEnd=TargetRockStation+25.;
            HeadingOffset=RaftSimTrialRockApproach::HeadingOffset(Route.Y,TargetRockLateral,Tangent,Left);
            Result->SetNumberField(TEXT("heading_start_m"),HeadingStart);Result->SetNumberField(TEXT("heading_end_m"),HeadingEnd);
            Result->SetNumberField(TEXT("heading_offset_deg"),HeadingOffset);
            Result->SetNumberField(TEXT("rock_approach_version"),3);
            Result->SetBoolField(TEXT("target_is_localized_rock"),true);
            const auto* Source=FindObject<UObject>(nullptr,*TargetRockSource);
            Result->SetBoolField(TEXT("target_owner_attribution_supported"),Source && (Source->IsA<UStaticMeshComponent>() || Source->IsA<AActor>()));
        }
        else if(Route.X>=Trial->GetNumberField(TEXT("control_m"))+60.)
        {Finish(TEXT("physical_rock_owner_unavailable"));return false;}
    }
    if(HasTargetRock)
    {
        ClosestTargetDistance=FMath::Min(ClosestTargetDistance,(Position-TargetRockWorld).Size2D()*.01);
        const auto& Totals=Physics->GetHullContactTotals();
        for(const auto& Entry:Totals.OwnerImpulses)
        {
            auto* Component=Entry.Key.Get();
            if(!Component || InspectedContactOwners.Contains(Entry.Key))continue;
            InspectedContactOwners.Add(Entry.Key);
            if(Component->GetPathName()==TargetRockSource ||
                (Component->GetOwner() && Component->GetOwner()->GetPathName()==TargetRockSource))TargetContactOwners.Add(Entry.Key);
        }
        uint64 Count=0;
        for(const auto Owner:TargetContactOwners)
        {
            const uint64 Current=Totals.OwnerImpulses.FindRef(Owner),Initial=InitialHullContact.OwnerImpulses.FindRef(Owner);
            if(Current>=Initial)Count+=Current-Initial;
        }
        if(Count>TargetOwnerImpulses)LastTargetContact=Elapsed;
        TargetOwnerImpulses=Count;
    }
    // A separately labelled rescue drill, never counted as a naturally
    // generated washout or a rapid-difficulty observation. No pose/velocity
    // changes or subsequent teleports: recovery uses the normal public API.
    if(RescueEnabled && RescueDrillStation>=0 && !RescueDrillIssued && Route.X>=RescueDrillStation)
    {
        RescueDrillIssued=true;
        if(Raft->IsSoloOarRig())Raft->ForceGuideOverboardForTesting();
        else Raft->ForceCrewOverboardForTesting(1);
        Result->SetNumberField(TEXT("overboard_drill_actual_station_m"),Route.X);
        Result->SetNumberField(TEXT("overboard_drill_actual_time_s"),Elapsed);
        Result->SetStringField(TEXT("overboard_drill_subject"),Raft->IsSoloOarRig()?TEXT("guide"):TEXT("one_passenger"));
    }
    // Observe the first downstream crossing of each section/move gate. Linear
    // segment intersection locates the crossing; it never drives the boat.
    const TArray<TSharedPtr<FJsonValue>>* Gates=nullptr;
    if(Trial->TryGetArrayField(TEXT("gates"),Gates))for(const auto& Value:*Gates)
    {
        const auto Gate=Value->AsObject();const FString Id=Gate->GetStringField(TEXT("id"));
        const double Station=Gate->GetNumberField(TEXT("station_m"));
        if(!CrossedGates.Contains(Id) && PreviousRoute.X<Station && Route.X>=Station)
        {
            const double Lateral=FMath::Lerp(PreviousRoute.Y,Route.Y,(Station-PreviousRoute.X)/(Route.X-PreviousRoute.X));
            auto Receipt=MakeShared<FJsonObject>();Receipt->Values=Gate->Values;
            Receipt->SetNumberField(TEXT("actual_lateral_m"),Lateral);
            Receipt->SetNumberField(TEXT("elapsed_s"),Elapsed);
            Receipt->SetNumberField(TEXT("yaw_deg"),State.WorldTransform.Rotator().Yaw);
            Receipt->SetNumberField(TEXT("heading_relative_to_river_deg"),FMath::FindDeltaAngleDegrees(Tangent.Rotation().Yaw,State.WorldTransform.Rotator().Yaw));
            Receipt->SetNumberField(TEXT("ground_contacts"),Physics->GetLastHullContact().Impulses);
            Receipt->SetNumberField(TEXT("full_hull_impulses_before_gate"),Physics->GetHullContactTotals().Impulses-InitialHullContact.Impulses);
            Receipt->SetNumberField(TEXT("speed_mps"),State.LinearVelocityMetersPerSecond.Size());
            Receipt->SetNumberField(TEXT("swimmers"),Raft->GetSwimmerCount());
            Receipt->SetNumberField(TEXT("pin_seconds_before_gate"),PinSeconds);
            Receipt->SetNumberField(TEXT("checkpoint_restores_during_trial"),Raft->GetCheckpointRestoreCount()-InitialRestores);
            double Lo=-DBL_MAX,Hi=DBL_MAX;
            Gate->TryGetNumberField(TEXT("min_lateral_m"),Lo);Gate->TryGetNumberField(TEXT("max_lateral_m"),Hi);
            Receipt->SetBoolField(TEXT("inside_requested_lane"),Lateral>=Lo && Lateral<=Hi);
            GateReceipts.Add(MakeShared<FJsonValueObject>(Receipt));CrossedGates.Add(Id);
            bool CaptureGates=false;
            if(Plan->TryGetBoolField(TEXT("capture_gate_frames"),CaptureGates) && CaptureGates)
                FScreenshotRequest::RequestScreenshot(Plan->GetStringField(TEXT("output_dir"))/
                    (Trial->GetStringField(TEXT("id"))+TEXT("-gate-")+Id+TEXT(".png")),true,false);
        }
    }
    PreviousRoute=Route;
    if(Raft->GetCheckpointRestoreCount()!=InitialRestores)
    {Finish(TEXT("checkpoint_reset_not_recovery"));return false;}
    // A refused contact step freezes the raft; that is a physics fault, not
    // a stall the rapid caused.
    if(Bridge->IsRaftStepFailureLatched())
    {Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);Finish(TEXT("physics_step_refused_not_rapid_outcome"));return false;}
    const double CurrentPreferredLateral=PreferredLateral(Route.X);
    MaximumRouteError=FMath::Max(MaximumRouteError,FMath::Abs(Route.Y-CurrentPreferredLateral));
    if(MistakeDuration>0 && MistakeStart<0 && Route.X>=Steering.MistakeTrigger.Get(Trial->GetNumberField(TEXT("control_m"))-12.))
    {
        MistakeStart=Elapsed;
        Result->SetNumberField(TEXT("mistake_actual_start_station_m"),Route.X);
    }
    const bool MissingTurn=(MistakeStart>=0 && Elapsed<MistakeStart+MistakeDuration) ||
        Steering.Suppressed(Route.X);
    // Stop sustained crew turning at the omission boundary. Existing boat
    // momentum and already-started individual strokes remain physical.
    if(!HandsOff && MissingTurn && (Command==ERaftSimCrewCommand::TurnLeft || Command==ERaftSimCrewCommand::TurnRight))
    {Command=ERaftSimCrewCommand::AllForward;Raft->IssueCrewCommand(Command);++Changes;}
    if(MistakeStart>=0 && !MissingTurn)
    {
        MistakeDone=true;
        if(RecoveryAt<0 && FMath::Abs(Route.Y-CurrentPreferredLateral)<2. && Raft->GetRaftMode()==ERaftSimRaftMode::Upright &&
            Raft->GetSwimmerCount()==0 && Raft->GetPinnedRockObstacleCount()==0)
            RecoveryAt=Elapsed;
    }
    if(Raft->GetRaftMode()==ERaftSimRaftMode::Capsized)Capsized=true;
    if(Assessment && !HandsOff && (!MissingTurn || RescueEnabled) && (!StrictRoute || RescueEnabled) && Elapsed-LastRecoveryInput>=3.)
    {
        if(Raft->GetRaftMode()==ERaftSimRaftMode::Capsized)
        {Raft->RequestReflip();++ReflipRequests;LastRecoveryInput=Elapsed;}
        else if(FMath::Abs(State.WorldTransform.Rotator().Roll)>30. ||
            (TargetPhysicalRock && Elapsed-LastTargetContact<3. &&
                FMath::Abs(State.WorldTransform.Rotator().Roll)>10.))
        {
            // Use the same ordinary command path as the player. Production
            // resolves the uphill side (positive UE roll needs negative side).
            Command=ERaftSimCrewCommand::HighSide;
            Raft->IssueCrewCommand(Command);++Changes;++HighSides;
            LastRecoveryInput=Elapsed;LastInput=Now;
        }
    }
    if(RescueEnabled && !HandsOff && Now-LastInput>=InputInterval && Raft->GetSwimmerCount()>0)
    {
        // Natural incidents and explicitly labelled drills share recovery.
        // No recovery impulses or checkpoint resets. A guide must
        // swim back within reach before the production flip-line can engage.
        FVector Guide;
        if(Raft->GetSwimmerWorldPosition(TEXT("guide"),Guide))
        {
            Raft->ApplySwimmerStroke(TEXT("guide"),(Position-Guide).GetSafeNormal());
            if(Raft->GetRaftMode()==ERaftSimRaftMode::Capsized)
            {Raft->RequestReflip();++ReflipRequests;}
        }
        else if(!Raft->IsGuideRescuing() && Raft->GetRaftMode()==ERaftSimRaftMode::Upright)
        {
            Raft->SelectRescueTarget(1.f);
            const auto Rescue=Raft->GetRescueInteractionState();FVector Swimmer;
            if(Raft->GetSwimmerWorldPosition(Rescue.TargetPassengerId,Swimmer))
            {
                Raft->AimRescue(Swimmer*.01-Raft->GetRescueHandWorldM());
                ++RescueAttempts;Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine);
            }
        }
        Raft->RequestSelectedReentry();
    }
    if(Route.X>BestStation+1){BestStation=Route.X;LastProgress=Now;}
    // Explicit recovery experiment only: stop exhausting a stationary crew
    // with repeated turn calls. Rest through the normal API, then aim farther
    // down the SAME authored route. No stamina refill or progress reset.
    if(!HandsOff && RescueEnabled && StallRecovery.TryStart(Route.X,Now-LastProgress,Elapsed,
        !MissingTurn && Raft->GetRaftMode()==ERaftSimRaftMode::Upright &&
        Raft->GetSwimmerCount()==0 && Raft->GetCrewEnergy()<.35f &&
        State.LinearVelocityMetersPerSecond.Size()<.75))
    {
        Result->SetNumberField(TEXT("rest_exit_recovery_start_station_m"),Route.X);
        Result->SetNumberField(TEXT("crew_energy_before_recovery_rest"),Raft->GetCrewEnergy());
    }
    const bool RecoveryResting=StallRecovery.IsResting(Elapsed);
    if(RecoveryResting && Command!=ERaftSimCrewCommand::Rest)
    {Command=ERaftSimCrewCommand::Rest;Raft->IssueCrewCommand(Command);++Changes;LastInput=Now;}
    if(StallRecovery.IsExiting(Elapsed) && !Result->HasField(TEXT("rest_exit_recovery_rest_completed_at_s")))
    {
        Result->SetNumberField(TEXT("rest_exit_recovery_rest_completed_at_s"),Elapsed);
        Result->SetNumberField(TEXT("crew_energy_after_recovery_rest"),Raft->GetCrewEnergy());
    }
    if(!HandsOff && !RecoveryResting && Now-LastInput>=InputInterval)
    {
        FVector Aim;
        float MinStation=0,MaxStation=0;
        Progress->GetRiverStationRangeM(MinStation,MaxStation);
        // After a temporary stall, aim farther downstream to paddle out of a
        // recirculation instead of indefinitely chasing a nearby centerline
        // point. This changes only the test driver's ordinary input decisions.
        double Lookahead=12.;Trial->TryGetNumberField(TEXT("lookahead_m"),Lookahead);
        if(StallRecovery.IsExiting(Elapsed))Lookahead=FMath::Max(Lookahead,StallRecovery.Lookahead);
        if(Assessment && !StrictRoute && Now-LastProgress>15.)Lookahead=FMath::Max(Lookahead,40.);
        const double TargetLane=PreferredLateral(Route.X+Lookahead);
        if(Progress->RiverToWorldPosition(FVector2D(FMath::Clamp(Route.X+Lookahead,double(MinStation),double(MaxStation)),TargetLane),Progress->GetRiverVerticalDatumM(),Aim))
        {
            if(Assessment && !StrictRoute)
            {
                // Scout the actual live bed/water rather than drive a fixed
                // offset through shoals. Preferred lanes still differ, but a
                // successful path may converge to the only wet opening. The
                // report measures that convergence; it is not safe width.
                double BestCost=DBL_MAX;
                for(int32 Offset=-8;Offset<=8;++Offset)
                {
                    const double CandidateLateral=TargetLane+Offset*2.;
                    FVector Candidate;
                    if(!Progress->RiverToWorldPosition(FVector2D(FMath::Clamp(Route.X+Lookahead,double(MinStation),double(MaxStation)),CandidateLateral),
                        Progress->GetRiverVerticalDatumM(),Candidate))continue;
                    const FVector Forward=(Candidate-Position).GetSafeNormal2D();
                    const FVector Side(-Forward.Y,Forward.X,0);
                    double MinimumDepth=DBL_MAX; bool Usable=true;
                    for(int32 Along=-1;Along<=1 && Usable;++Along)for(int32 Across=-1;Across<=1;++Across)
                    {
                        FRaftSimWaterSample Probe;
                        if(!Water->SampleWaterAtWorldPosition(Candidate+Forward*(Along*220.)+Side*(Across*130.),Probe) || !Probe.bWet)
                        {Usable=false;break;}
                        MinimumDepth=FMath::Min(MinimumDepth,double(Probe.DepthMeters));
                    }
                    if(!Usable)continue;
                    const double Cost=FMath::Square(CandidateLateral-TargetLane)*.025+
                        FMath::Square(FMath::Max(0.,.65-MinimumDepth))*100.;
                    if(Cost<BestCost){BestCost=Cost;Aim=Candidate;}
                }
            }
            const FVector2D Track=FVector2D(Aim.X-Position.X,Aim.Y-Position.Y).GetSafeNormal();
            const FVector2D Flow=Wet?FVector2D(WaterSample.VelocityMetersPerSecond):FVector2D::ZeroVector;
            const FVector2D Across=Flow-Track*FVector2D::DotProduct(Flow,Track);
            const double RelativeSpeed=Raft->IsSoloOarRig()?1.0:2.2;
            const double Remaining=RelativeSpeed*RelativeSpeed-Across.SizeSquared();
            const FVector2D Effort=Remaining>0?Track*FMath::Sqrt(Remaining)-Across:-Across.GetSafeNormal()*RelativeSpeed;
            const bool HoldHeading=TargetPhysicalRock?
                HasTargetRock && RaftSimTrialRockApproach::AlignBroadside(Route,FVector2D(TargetRockStation,TargetRockLateral)):
                Route.X>=HeadingStart && Route.X<HeadingEnd;
            HeadingHeld=HoldHeading && !MissingTurn;
            const double AimYaw=HoldHeading?Tangent.Rotation().Yaw+HeadingOffset:FMath::RadiansToDegrees(FMath::Atan2(Effort.Y,Effort.X));
            const double Error=FMath::FindDeltaAngleDegrees(State.WorldTransform.Rotator().Yaw,AimYaw);
            const double Rate=FMath::RadiansToDegrees(State.AngularVelocityRadiansPerSecond.Z);
            const double AnticipatedError=Assessment?Error-.5*Rate:Error;
            const bool BackOff=Assessment && !StallRecovery.IsExiting(Elapsed) &&
                Now-LastProgress>20. && FMath::Fmod(Now-LastProgress-20.,15.)<3.;
            const auto Desired=RescueEnabled && Raft->GetSwimmerCount()>0?ERaftSimCrewCommand::Rest:MissingTurn?ERaftSimCrewCommand::AllForward:BackOff?ERaftSimCrewCommand::AllBackward:
                TargetPhysicalRock && HoldHeading && FMath::Abs(AnticipatedError)<12?ERaftSimCrewCommand::Rest:
                FMath::Abs(AnticipatedError)>25?(AnticipatedError>0?ERaftSimCrewCommand::TurnRight:ERaftSimCrewCommand::TurnLeft):
                FMath::Abs(AnticipatedError)<12 || Command==ERaftSimCrewCommand::HighSide?ERaftSimCrewCommand::AllForward:Command;
            if(Desired!=Command){Command=Desired;Raft->IssueCrewCommand(Command);++Changes;}
            const float Stroke=FMath::Clamp(float(Error/45.-Rate*.025),-1.f,1.f);
            if(!MissingTurn && FMath::Abs(Stroke)>.08){Raft->ApplyGuideSteerStroke(Stroke);++Strokes;}
        }
        LastInput=Now;
    }
    if(Now-LastSample<.2 && FPlatformTime::Seconds()-Wall<WallLimit) return false;
    LastSample=Now; const double Dt=Now-PreviousSample; PreviousSample=Now;
    Finite &= State.WorldTransform.IsValid()&&!State.LinearVelocityMetersPerSecond.ContainsNaN();
    MaxRoll=FMath::Max(MaxRoll,FMath::Abs(double(State.WorldTransform.Rotator().Roll)));
    MaxPitch=FMath::Max(MaxPitch,FMath::Abs(double(State.WorldTransform.Rotator().Pitch)));
    MaxSpeed=FMath::Max(MaxSpeed,double(State.LinearVelocityMetersPerSecond.Size()));
    MinUp=FMath::Min(MinUp,double(State.WorldTransform.GetUnitAxis(EAxis::Z).Z));
    MaxSwimmers=FMath::Max(MaxSwimmers,Raft->GetSwimmerCount());
    MaxContacts=FMath::Max(MaxContacts,Raft->GetActiveWaterContactCount());
    if(Raft->GetPinnedRockObstacleCount()>0)PinSeconds+=Dt;
    if(Raft->GetPinnedRockObstacleCount()>0 && TargetOwnerImpulses>SampledTargetOwnerImpulses)TargetPinSampleSeconds+=Dt;
    SampledTargetOwnerImpulses=TargetOwnerImpulses;
    GroundSeconds=Physics->GetHullContactTotals().ContactStepSeconds-InitialHullContact.ContactStepSeconds;
    if(!Wet)DrySeconds+=Dt;
    if(Command==ERaftSimCrewCommand::TurnLeft||Command==ERaftSimCrewCommand::TurnRight)TurnSeconds+=Dt;
    if(Command==ERaftSimCrewCommand::AllBackward)BackStrokeSeconds+=Dt;
    auto Row=MakeShared<FJsonObject>();
    Row->SetNumberField(TEXT("elapsed_s"),Elapsed);Row->SetNumberField(TEXT("station_m"),Route.X);
    Row->SetNumberField(TEXT("crew_energy"),Raft->GetCrewEnergy());
    Row->SetNumberField(TEXT("guide_stamina"),Raft->GetCrewStamina(TEXT("guide")));
    Row->SetNumberField(TEXT("lateral_m"),Route.Y);Row->SetNumberField(TEXT("speed_mps"),State.LinearVelocityMetersPerSecond.Size());
    Row->SetNumberField(TEXT("preferred_lateral_m"),CurrentPreferredLateral);
    Row->SetNumberField(TEXT("world_z_m"),Position.Z*.01);
    Row->SetNumberField(TEXT("roll_deg"),State.WorldTransform.Rotator().Roll);Row->SetNumberField(TEXT("pitch_deg"),State.WorldTransform.Rotator().Pitch);
    Row->SetNumberField(TEXT("swimmers"),Raft->GetSwimmerCount());Row->SetNumberField(TEXT("pinned"),Raft->GetPinnedRockObstacleCount());
    Row->SetBoolField(TEXT("wet_center"),Wet);Row->SetNumberField(TEXT("crew_command"),int32(Command));
    Row->SetBoolField(TEXT("missed_turn_active"),MissingTurn);
    Row->SetBoolField(TEXT("heading_hold_active"),HeadingHeld && !MissingTurn);
    if(TargetPhysicalRock)Row->SetNumberField(TEXT("target_owner_impulses"),TargetOwnerImpulses);
    Row->SetNumberField(TEXT("heading_relative_to_river_deg"),FMath::FindDeltaAngleDegrees(Tangent.Rotation().Yaw,State.WorldTransform.Rotator().Yaw));
    Row->SetNumberField(TEXT("ground_contacts"),Physics->GetLastHullContact().Impulses);
    Row->SetNumberField(TEXT("full_hull_impulses"),Physics->GetHullContactTotals().Impulses-InitialHullContact.Impulses);
    Row->SetNumberField(TEXT("run_state"),static_cast<int32>(Run->GetRunState()));
    Row->SetNumberField(TEXT("yaw_deg"),State.WorldTransform.Rotator().Yaw);
    if(Wet){Row->SetNumberField(TEXT("water_speed_mps"),WaterSample.VelocityMetersPerSecond.Size());Row->SetNumberField(TEXT("depth_m"),WaterSample.DepthMeters);
        Row->SetNumberField(TEXT("water_surface_m"),WaterSample.SurfaceHeightMeters);
        const double Clearance=Position.Z*.01-WaterSample.SurfaceHeightMeters;
        Row->SetNumberField(TEXT("center_minus_surface_m"),Clearance);
        MinimumCenterClearance=FMath::Min(MinimumCenterClearance,Clearance);
        FRaftSimWaterSample Support,Interaction;
        if(Water->SampleRaftSupportSurfaceAtWorldPosition(Position,Support))
            Row->SetNumberField(TEXT("raft_support_surface_m"),Support.SurfaceHeightMeters);
        if(Water->SampleRaftInteractionWaterAtWorldPosition(Position,Interaction))
            Row->SetNumberField(TEXT("raft_interaction_surface_m"),Interaction.SurfaceHeightMeters);
        Row->SetNumberField(TEXT("water_bed_m"),WaterSample.BedHeightMeters);
        double WaterClock=0.;
        if(Water->GetLiveFieldTimeSeconds(WaterClock))Row->SetNumberField(TEXT("water_clock_s"),WaterClock);
        if(Clearance<LastCapturedClearance-.5)
        {
            LastCapturedClearance=Clearance;
            FScreenshotRequest::RequestScreenshot(Plan->GetStringField(TEXT("output_dir"))/
                FString::Printf(TEXT("%s-surface-anomaly-%06d.png"),*Trial->GetStringField(TEXT("id")),int32(Elapsed*1000)),true,false);
        }
    }
    Samples.Add(MakeShared<FJsonValueObject>(Row));
    Result->SetNumberField(TEXT("elapsed_s"),Elapsed);Result->SetNumberField(TEXT("end_m"),Route.X);
    Result->SetNumberField(TEXT("final_crew_energy"),Raft->GetCrewEnergy());
    Result->SetNumberField(TEXT("final_guide_stamina"),Raft->GetCrewStamina(TEXT("guide")));
    Result->SetNumberField(TEXT("wall_seconds"),FPlatformTime::Seconds()-Wall);
    Result->SetNumberField(TEXT("recorded_incidents"),Run->GetSafetyIncidentCount());
    Result->SetNumberField(TEXT("completed_rescues"),Raft->GetCompletedRescueCount()-RescueCompletionsAtStart);
    Result->SetNumberField(TEXT("full_hull_impulses"),Physics->GetHullContactTotals().Impulses-InitialHullContact.Impulses);
    Result->SetNumberField(TEXT("full_hull_impulse_steps"),Physics->GetHullContactTotals().ImpulseSteps-InitialHullContact.ImpulseSteps);
    Result->SetNumberField(TEXT("checkpoint_restores_during_trial"),Raft->GetCheckpointRestoreCount()-InitialRestores);
    if(Raft->IsSoloOarRig()&&Raft->GetOarRig())
        Result->SetNumberField(TEXT("completed_oar_strokes"),Raft->GetOarRig()->GetCompletedStrokeCount()-InitialOarStrokes);
    FString Reason;
    if(!Finite)Reason=TEXT("nonfinite_state");
    else if(!HandsOff&&Raft->IsSoloOarRig()&&Elapsed>15&&Raft->GetOarRig()&&Raft->GetOarRig()->GetCompletedStrokeCount()==InitialOarStrokes)
        Reason=TEXT("oar_input_not_verified");
    else if(!Assessment && (Raft->GetRaftMode()!=ERaftSimRaftMode::Upright || MinUp<0))Reason=TEXT("capsized");
    else if(Route.X>=Trial->GetNumberField(TEXT("finish_m"))-.01)Reason=
        NamedSitesExpected>0 && NamedSitesSeen.IsEmpty()?TEXT("named_water_features_not_loaded_in_section"):
        Raft->GetRaftMode()==ERaftSimRaftMode::Upright && Raft->GetSwimmerCount()==0?TEXT("section_cleared"):TEXT("exit_with_unrecovered_crew");
    else if(Elapsed>20&&Now-LastProgress>StallLimit)Reason=TEXT("stalled_driver_not_proof_impassable");
    else if(Elapsed>=SimulationLimit)Reason=TEXT("time_limit_partial");
    else if(FPlatformTime::Seconds()-Wall>WallLimit)Reason=TEXT("wall_time_limit_partial");
    if(Reason.IsEmpty())return false;
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);Finish(Reason);return false;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRiverDifficultyReviewTest,"RaftSim.Review.RiverDifficulty",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimRiverDifficultyReviewTest::RunTest(const FString&)
{
    FString Path;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimDifficultyPlan="),Path))
    {AddInfo(TEXT("Skipped: explicit difficulty plan required"));return true;}
    if(!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")))
    {AddError(TEXT("An ephemeral profile is required"));return false;}
    FString Json;TSharedPtr<FJsonObject> Plan;
    if(!FFileHelper::LoadFileToString(Json,*Path)||!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Plan)||!Plan.IsValid())
    {AddError(TEXT("Cannot read trial plan"));return false;}
    if(!AutomationOpenMap(Plan->GetStringField(TEXT("map")),true))return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(5.f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRiverDifficultyReview>(this,Plan));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.f));
    return true;
}
#endif
