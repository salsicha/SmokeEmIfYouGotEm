#pragma once
// Explicit ephemeral gameplay experiment. Only the normal checkpoint APIs move
// the raft; the observer never repairs/re-enables water or changes its clock.
#include "../RaftSimRunManager.h"
#include "RaftSimRaftActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "WorldPartition/WorldPartitionSubsystem.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include "GameFramework/PlayerController.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

namespace RaftSimCheckpointPlayProbe
{
struct FProbe
{
    FString Report;
    FTransform Home;
    double WallStart=-1.,PhaseStart=-1.,FirstClock=-1.,LastClock=-1.;
    uint64 LastSequence=0;
    int32 Phase=0,FreshFrames=0,Captures=0;
    bool bFinished=false,bPhaseReady=false;
    TArray<TSharedPtr<FJsonValue>> Events;

    void Finish(bool Passed,const FString& Reason)
    {
        if(bFinished)return;
        bFinished=true;
        auto Root=MakeShared<FJsonObject>();
        Root->SetStringField(TEXT("schema"),TEXT("raftsim.checkpoint_actual_play.v1"));
        Root->SetBoolField(TEXT("passed"),Passed);
        Root->SetStringField(TEXT("reason"),Reason);
        Root->SetNumberField(TEXT("phase"),Phase);
        Root->SetNumberField(TEXT("fresh_frames_in_phase"),FreshFrames);
        Root->SetNumberField(TEXT("detail_seconds_in_phase"),FirstClock<0 ? 0 : LastClock-FirstClock);
        Root->SetBoolField(TEXT("visual_accepted"),false);
        Root->SetBoolField(TEXT("performance_accepted"),false);
        Root->SetArrayField(TEXT("events"),Events);
        FString Json;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json));
        if(!FFileHelper::SaveStringToFile(Json,*Report))Passed=false;
        UE_LOG(LogTemp,Display,TEXT("CHECKPOINT_PLAY passed=%d phase=%d reason=%s"),Passed,Phase,*Reason);
        FPlatformMisc::RequestExitWithStatus(false,Passed ? 0 : 1);
    }

    void Tick(UWorld* World,ELevelTick,float)
    {
        if(bFinished || !World || !World->IsGameWorld() || !World->HasBegunPlay() ||
            !World->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))return;
        const double Now=World->GetTimeSeconds();
        if(WallStart<0){WallStart=FPlatformTime::Seconds();PhaseStart=Now;}
        if(FPlatformTime::Seconds()-WallStart>300.){Finish(false,TEXT("Round-trip observation timeout"));return;}
        ARaftSimRaftActor* Raft=nullptr;ARaftSimRunManager* Run=nullptr;
        int32 Rafts=0,Runs=0,Details=0;
        for(TActorIterator<ARaftSimRaftActor> It(World);It;++It){Raft=*It;++Rafts;}
        for(TActorIterator<ARaftSimRunManager> It(World);It;++It){Run=*It;++Runs;}
        auto* Instance=World->GetGameInstance();
        auto* Bridge=Instance ? Instance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
        auto* Water=Bridge ? Bridge->GetWaterRuntime() : nullptr;
        URaftSimStatefulDetailComponent* Detail=nullptr;
        for(TActorIterator<ARaftSimWaterSurfaceActor> It(World);It;++It)
        {
            TArray<URaftSimStatefulDetailComponent*> Found;It->GetComponents(Found);
            for(auto* Candidate:Found){Detail=Candidate;++Details;}
        }
        if(Rafts!=1 || Runs!=1 || !Water || Details!=1 || !Detail || !Detail->IsReady())
        {
            if(Phase>0 || bPhaseReady || Now-PhaseStart>20.)Finish(false,TEXT("Missing or disabled normal-play raft/run/water/detail"));
            return;
        }
        FRaftSimWaterSample Sample;
        if(!Water->SampleWaterAtWorldPosition(Raft->GetActorLocation(),Sample) || !Sample.bWet)
        {Finish(false,TEXT("Raft has no authoritative wet water"));return;}
        const auto Frame=Detail->GetPresentedFrame();
        if(!Frame)
        {
            if(bPhaseReady || Now-PhaseStart>20.)Finish(false,TEXT("No completed detail frame at destination"));
            return;
        }
        if(!Frame->Validate()){Finish(false,TEXT("Invalid completed detail frame"));return;}
        const auto Registration=Frame->Pixels[Frame->Size.X*Frame->Size.Y];
        const auto Position=Raft->GetActorLocation();
        const FVector2D Cell=(FVector2D(Position.X/100.,Position.Y*Water->GetRiverWorldYSign()/100.)-
            FVector2D(Registration.X,Registration.Y))/Registration.Z;
        const bool Covered=Cell.X>=0 && Cell.Y>=0 && Cell.X<=Frame->Size.X-1 && Cell.Y<=Frame->Size.Y-1;
        if(!Covered)
        {
            // An in-flight old-location GPU readback is not destination evidence.
            if(bPhaseReady || Now-PhaseStart>2.)Finish(false,TEXT("Presented detail does not cover the raft at destination"));
            return;
        }
        if(bPhaseReady && (Frame->Sequence<LastSequence || Frame->SimulationSeconds<LastClock))
        {Finish(false,TEXT("Detail sequence/clock regressed within a checkpoint epoch"));return;}
        if(!bPhaseReady){FirstClock=Frame->SimulationSeconds;bPhaseReady=true;}
        if(Frame->Sequence>LastSequence)++FreshFrames;
        LastSequence=Frame->Sequence;LastClock=Frame->SimulationSeconds;
        if(Captures<4 && Now-PhaseStart>=Captures*2. && !FScreenshotRequest::IsScreenshotRequested())
        {
            const FString Path=FPaths::Combine(FPaths::GetPath(Report),FString::Printf(
                TEXT("%s-phase-%d-%d.png"),*FPaths::GetBaseFilename(Report),Phase,Captures++));
            FScreenshotRequest::RequestScreenshot(Path,false,false);
            auto Row=MakeShared<FJsonObject>();
            Row->SetStringField(TEXT("capture"),Path);Row->SetNumberField(TEXT("phase"),Phase);
            Row->SetNumberField(TEXT("world_seconds"),Now);Row->SetNumberField(TEXT("sequence"),double(LastSequence));
            Row->SetNumberField(TEXT("detail_seconds"),LastClock);
            Row->SetStringField(TEXT("raft_world_cm"),Position.ToString());
            Row->SetNumberField(TEXT("origin_x_m"),Registration.X);Row->SetNumberField(TEXT("origin_y_m"),Registration.Y);
            if(Phase==1 && FParse::Param(FCommandLine::Get(),TEXT("RaftSimCheckpointTerrainRays")))
            {
                // Read-only owner probes, not rendered-pixel or collision acceptance.
                // Normalized positions cover the retained detached patches and
                // adjacent ridge at1280x720; preserve misses rather than invent owners.
                TArray<TSharedPtr<FJsonValue>> Rays;
                auto* PC=World->GetFirstPlayerController();int32 Width=0,Height=0;
                if(PC)PC->GetViewportSize(Width,Height);
                for(const FVector2D Pixel:{FVector2D(600,207),FVector2D(620,210),FVector2D(900,268),
                    FVector2D(890,275),FVector2D(840,270),FVector2D(600,240),FVector2D(900,305)})
                {
                    auto Ray=MakeShared<FJsonObject>();FVector Origin,Direction;
                    Ray->SetNumberField(TEXT("reference_pixel_x"),Pixel.X);
                    Ray->SetNumberField(TEXT("reference_pixel_y"),Pixel.Y);
                    const bool Projected=PC && Width>0 && Height>0 && PC->DeprojectScreenPositionToWorld(
                        Pixel.X*Width/1280.,Pixel.Y*Height/720.,Origin,Direction);
                    Ray->SetBoolField(TEXT("deprojected"),Projected);
                    if(Projected)
                    {
                        Ray->SetStringField(TEXT("origin_cm"),Origin.ToString());
                        Ray->SetStringField(TEXT("direction"),Direction.ToString());
                        FCollisionQueryParams Params(SCENE_QUERY_STAT(CheckpointTerrainOwner),true);
                        FHitResult Hit;
                        const bool HitTerrain=World->LineTraceSingleByChannel(Hit,Origin,
                            Origin+Direction*5000000.,ECC_Visibility,Params);
                        Ray->SetBoolField(TEXT("collision_hit"),HitTerrain);
                        if(HitTerrain)
                        {
                            Ray->SetStringField(TEXT("actor"),GetPathNameSafe(Hit.GetActor()));
                            Ray->SetStringField(TEXT("component"),GetPathNameSafe(Hit.GetComponent()));
                            Ray->SetStringField(TEXT("impact_cm"),Hit.ImpactPoint.ToString());
                            Ray->SetNumberField(TEXT("distance_cm"),Hit.Distance);
                            Ray->SetNumberField(TEXT("item"),Hit.Item);
                            if(auto* Mesh=Cast<UStaticMeshComponent>(Hit.GetComponent()))
                            {
                                Ray->SetStringField(TEXT("mesh"),GetPathNameSafe(Mesh->GetStaticMesh()));
                                Ray->SetStringField(TEXT("transform"),Mesh->GetComponentTransform().ToHumanReadableString());
                                Ray->SetStringField(TEXT("bounds_origin_cm"),Mesh->Bounds.Origin.ToString());
                                Ray->SetStringField(TEXT("bounds_extent_cm"),Mesh->Bounds.BoxExtent.ToString());
                            }
                        }
                    }
                    Rays.Add(MakeShared<FJsonValueObject>(Ray));
                }
                Row->SetArrayField(TEXT("terrain_owner_collision_rays"),Rays);
            }
            Events.Add(MakeShared<FJsonValueObject>(Row));
        }
        if(Now-PhaseStart<10. || FreshFrames<100 || LastClock-FirstClock<3. || Captures<4)return;
        auto PhaseSummary=MakeShared<FJsonObject>();
        PhaseSummary->SetNumberField(TEXT("completed_phase"),Phase);
        PhaseSummary->SetNumberField(TEXT("fresh_frames"),FreshFrames);
        PhaseSummary->SetNumberField(TEXT("detail_clock_advance_seconds"),LastClock-FirstClock);
        PhaseSummary->SetNumberField(TEXT("observed_world_seconds"),Now-PhaseStart);
        Events.Add(MakeShared<FJsonValueObject>(PhaseSummary));
        if(Phase==2){Finish(true,TEXT("Distant checkpoint and return each retain wet contact and progressing registered detail"));return;}
        FTransform Destination;
        if(Phase==0)
        {
            Home=Raft->GetActorTransform();
            const auto* Coordinates=Run->GetProgressCoordinates(Water);
            FVector Point,Ahead;
            if(!Coordinates || !Coordinates->RiverToWorldPosition(FVector2D(25427.6352,0),Water->GetRiverVerticalDatumM(),Point) ||
                !Coordinates->RiverToWorldPosition(FVector2D(25428.6352,0),Water->GetRiverVerticalDatumM(),Ahead))
            {Finish(false,TEXT("Distant scenario coordinates unavailable"));return;}
            Destination=FTransform(FRotator(0,(Ahead-Point).Rotation().Yaw,0),Point);
            if(FVector::Dist2D(Home.GetLocation(),Point)<100000.)
            {Finish(false,TEXT("Requested checkpoint is not a distant discontinuity"));return;}
        }
        else Destination=Home;
        auto* Partition=World->GetSubsystem<UWorldPartitionSubsystem>();
        const int32 ProvidersBefore=Partition ? Partition->GetStreamingSourceProviders().Num() : 0;
        const double ResetStart=FPlatformTime::Seconds();
        bool Restored=false;
        if(Phase==0)Restored=Raft->TryRestoreCheckpoint(Destination);
        else {Raft->SetCheckpointTransform(Destination,false);Restored=Raft->TryResetToCheckpoint();}
        auto Event=MakeShared<FJsonObject>();
        Event->SetNumberField(TEXT("destination_phase"),Phase+1);Event->SetBoolField(TEXT("restored"),Restored);
        Event->SetNumberField(TEXT("reset_wall_seconds"),FPlatformTime::Seconds()-ResetStart);
        Event->SetStringField(TEXT("requested_world_cm"),Destination.GetLocation().ToString());
        Event->SetStringField(TEXT("actual_world_cm"),Raft->GetActorLocation().ToString());
        Events.Add(MakeShared<FJsonValueObject>(Event));
        if(!Restored || FVector::Dist2D(Destination.GetLocation(),Raft->GetActorLocation())>.01 ||
            (Partition && Partition->GetStreamingSourceProviders().Num()!=ProvidersBefore))
        {Finish(false,TEXT("Normal checkpoint API rejected destination, changed XY or leaked streaming provider"));return;}
        ++Phase;PhaseStart=World->GetTimeSeconds();FreshFrames=Captures=0;
        FirstClock=LastClock=-1.;LastSequence=0;bPhaseReady=false;
        UE_LOG(LogTemp,Display,TEXT("CHECKPOINT_PLAY restored phase=%d location=%s"),Phase,*Raft->GetActorLocation().ToString());
    }
};

inline FDelegateHandle Register()
{
    FString Report;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimCheckpointPlayReport="),Report))return {};
    auto Probe=MakeShared<FProbe>();Probe->Report=Report;
    if(!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")))
    {Probe->Finish(false,TEXT("Ephemeral profile required; never modify a saved run"));return {};}
    return FWorldDelegates::OnWorldPostActorTick.AddLambda([Probe](UWorld* World,ELevelTick Tick,float Delta){Probe->Tick(World,Tick,Delta);});
}
}
