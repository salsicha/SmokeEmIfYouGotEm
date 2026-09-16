#pragma once
// Explicit opt-in, read-only observation of actual gameplay ticks. No raft
// teleport, time override, solver stepping, crop request or detail re-enable.
#include "Engine/World.h"
#include "EngineUtils.h"
#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "HAL/PlatformTime.h"
#include "HAL/PlatformMisc.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

namespace RaftSimDetailStreamingPlayProbe
{
struct FProbe
{
    FString Report;
    double WallStart=FPlatformTime::Seconds(),Start=-1.,LastLog=-1.,FirstClock=0.,LastClock=0.;
    uint64 LastSequence=0;
    int32 Ticks=0,NewFrames=0,Handoffs=0,FirstHandoff=0,LastCapturedHandoff=-1;
    bool bSeenReady=false,bFinished=false;
    TArray<TSharedPtr<FJsonValue>> Samples;

    void Finish(bool bPassed,const FString& Reason)
    {
        if(bFinished)return;
        bFinished=true;
        auto Root=MakeShared<FJsonObject>();
        Root->SetStringField(TEXT("schema"),TEXT("raftsim.detail_streaming_actual_play.v1"));
        Root->SetBoolField(TEXT("passed"),bPassed);
        Root->SetStringField(TEXT("reason"),Reason);
        Root->SetBoolField(TEXT("visual_accepted"),false);
        Root->SetBoolField(TEXT("performance_accepted"),false);
        Root->SetBoolField(TEXT("normal_project_binary_deployed"),false);
        Root->SetNumberField(TEXT("observed_ticks"),Ticks);
        Root->SetNumberField(TEXT("new_presented_frames"),NewFrames);
        Root->SetNumberField(TEXT("handoffs_after_ready"),Handoffs-FirstHandoff);
        Root->SetNumberField(TEXT("detail_clock_advance_seconds"),LastClock-FirstClock);
        Root->SetArrayField(TEXT("samples"),Samples);
        FString Json;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json));
        if(!FFileHelper::SaveStringToFile(Json,*Report))bPassed=false;
        UE_LOG(LogTemp,Display,TEXT("DETAIL_STREAMING_PLAY passed=%d ticks=%d frames=%d handoffs=%d reason=%s"),
            bPassed,Ticks,NewFrames,Handoffs-FirstHandoff,*Reason);
        FPlatformMisc::RequestExitWithStatus(false,bPassed ? 0 : 1);
    }

    void Tick(UWorld* World,ELevelTick,float)
    {
        if(bFinished || !World || !World->IsGameWorld() || !World->HasBegunPlay() ||
            !World->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))return;
        if(Start<0)Start=World->GetTimeSeconds();
        const double Elapsed=World->GetTimeSeconds()-Start;
        URaftSimStatefulDetailComponent* Detail=nullptr;
        int32 Components=0,Streams=0;
        for(TActorIterator<ARaftSimWaterSurfaceActor> It(World);It;++It)
        {
            TArray<URaftSimStatefulDetailComponent*> Found;It->GetComponents(Found);
            for(auto* Candidate:Found){Detail=Candidate;++Components;}
        }
        for(TActorIterator<ARaftSimRiverWaterStreamingActor> It(World);It;++It)
        { Handoffs=It->GetSuccessfulHandoffCount();++Streams; }
        if(Components!=1 || Streams!=1 || !Detail || !Detail->IsReady())
        {
            if(bSeenReady || Elapsed>20.)Finish(false,TEXT("Missing, duplicate or disabled live detail/controller"));
            return;
        }
        const auto Frame=Detail->GetPresentedFrame();
        if(!Frame)
        {
            if(bSeenReady || Elapsed>20.)Finish(false,TEXT("Missing live presented frame"));
            return;
        }
        if(!Frame->Validate()){Finish(false,TEXT("Invalid presented GPU frame"));return;}
        if(!bSeenReady){bSeenReady=true;FirstClock=Frame->SimulationSeconds;FirstHandoff=Handoffs;}
        if(Frame->Sequence<LastSequence || Frame->SimulationSeconds<LastClock)
        { Finish(false,TEXT("Presentation sequence or clock regressed"));return; }
        if(Frame->Sequence>LastSequence)++NewFrames;
        LastSequence=Frame->Sequence;LastClock=Frame->SimulationSeconds;++Ticks;
        if(Handoffs!=LastCapturedHandoff && (LastCapturedHandoff<0 || Handoffs>=5))
        {
            LastCapturedHandoff=Handoffs;
            const FString Capture=FPaths::Combine(FPaths::GetPath(Report),
                FString::Printf(TEXT("%s-handoff-%03d.png"),*FPaths::GetBaseFilename(Report),Handoffs));
            FScreenshotRequest::RequestScreenshot(Capture,false,false);
        }
        if(LastLog<0 || Elapsed-LastLog>=5.)
        {
            LastLog=Elapsed;
            auto Row=MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("elapsed_world_seconds"),Elapsed);
            Row->SetNumberField(TEXT("sequence"),double(LastSequence));
            Row->SetNumberField(TEXT("detail_clock_seconds"),LastClock);
            Row->SetNumberField(TEXT("handoffs"),Handoffs);
            Row->SetBoolField(TEXT("ready"),true);
            const auto Registration=Frame->Pixels[Frame->Size.X*Frame->Size.Y];
            Row->SetNumberField(TEXT("origin_x_m"),Registration.X);
            Row->SetNumberField(TEXT("origin_y_m"),Registration.Y);
            Samples.Add(MakeShared<FJsonValueObject>(Row));
            UE_LOG(LogTemp,Display,TEXT("DETAIL_STREAMING_PLAY sample world=%.3f seq=%llu clock=%.6f handoffs=%d origin=(%.3f,%.3f)"),
                Elapsed,LastSequence,LastClock,Handoffs,Registration.X,Registration.Y);
        }
        // A loaded machine advances the fixed-step water clock more slowly
        // than world time. Keep all coverage/progression gates and observe
        // longer, rather than treating world time alone as a sufficient replay.
        if(Elapsed>=120. && Handoffs-FirstHandoff>=8 && NewFrames>=100 && LastClock-FirstClock>=60.)
            Finish(true,TEXT("At least 120 world seconds, eight handoffs, 100 fresh frames and 60 detail seconds observed"));
        else if(FPlatformTime::Seconds()-WallStart>900.)Finish(false,TEXT("Actual-play observation timeout"));
    }
};

inline FDelegateHandle Register()
{
    FString Report;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailStreamingReport="),Report))return {};
    auto Probe=MakeShared<FProbe>();Probe->Report=Report;
    if(!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")))
    { Probe->Finish(false,TEXT("Ephemeral profile required"));return {}; }
    return FWorldDelegates::OnWorldPostActorTick.AddLambda([Probe](UWorld* World,ELevelTick Tick,float Delta){Probe->Tick(World,Tick,Delta);});
}
}
