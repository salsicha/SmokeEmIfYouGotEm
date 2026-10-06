// Diagnostic camera flight through the WHOLE authored downstream axis.
// The real raft, water windows and physics keep running without guidance.
// Far-field presentation coverage is explicitly not live-water acceptance.
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "LandscapeProxy.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "String/LexFromString.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "RaftSimCameraPresentation.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRunCoordinateProvider.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Serialization/JsonSerializer.h"
#include "TimerManager.h"
#include "UObject/Package.h"
#include <limits>

#if CSV_PROFILER
CSV_DEFINE_CATEGORY(RaftSimRoute,true);
namespace RaftSimMapFlythrough
{
struct FFlight
{
    TWeakObjectPtr<UWorld> World;
    TWeakObjectPtr<URaftSimWaterRuntimeAdapter> Water;
    TWeakObjectPtr<const URaftSimWaterRuntimeAdapter> Axis;
    TWeakObjectPtr<ARaftSimRaftActor> Raft;
    TWeakObjectPtr<ACameraActor> Camera;
    TSharedPtr<FRaftSimGroundSourceRegistry> Ground;
    FDelegateHandle TickHandle;
    TSharedFuture<FString> CsvWritten;
    FString Label,Directory,Failure;
    double StartM=0,EndM=0,StationM=0,SpeedMps=40,HeightM=12;
    // Optional sub-route for iterating on one section; NaN = whole axis.
    double RequestedStartM=std::numeric_limits<double>::quiet_NaN(),RequestedEndM=std::numeric_limits<double>::quiet_NaN();
    int32 StartFrames=0,EndFrames=0,Frames=0;
    bool bCaptureRequested=false,bEnding=false;
};

static TWeakPtr<FFlight> ActiveFlight;

static bool SaveReceipt(const FFlight& State,bool bComplete,const FString& CsvPath=FString())
{
    TSharedRef<FJsonObject> Root=MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("schema"),TEXT("raftsim.native_map_flythrough.v1"));
    Root->SetStringField(TEXT("label"),State.Label);
    Root->SetStringField(TEXT("map"),State.World.IsValid()
        ? FPackageName::GetShortName(State.World->GetOutermost()->GetName()) : TEXT("lost_world"));
    Root->SetStringField(TEXT("mode"),TEXT("camera_only_no_boat_guidance"));
    Root->SetBoolField(TEXT("whole_authored_axis"),true);
    Root->SetBoolField(TEXT("complete"),bComplete);
    Root->SetStringField(TEXT("failure"),State.Failure);
    Root->SetStringField(TEXT("csv"),CsvPath);
    Root->SetNumberField(TEXT("start_m"),State.StartM);
    Root->SetNumberField(TEXT("end_m"),State.EndM);
    Root->SetNumberField(TEXT("last_station_m"),State.StationM);
    Root->SetNumberField(TEXT("native_route_ticks"),State.Frames);
    Root->SetNumberField(TEXT("maximum_step_m"),5);
    Root->SetNumberField(TEXT("camera_height_m"),State.HeightM);
    Root->SetBoolField(TEXT("boat_teleported_or_guided"),false);
    Root->SetBoolField(TEXT("recording_or_screenshots_enabled"),false);
    Root->SetBoolField(TEXT("all_map_water_and_boat_validation_accepted"),false);
    Root->SetStringField(TEXT("scope"),TEXT("Native camera render route, not a forced boat trajectory. Wet baseline and live-water coverage are recorded separately on every frame. Defaults and all normal simulation stay enabled."));
    FString Json;
    auto Writer=TJsonWriterFactory<>::Create(&Json);
    return FJsonSerializer::Serialize(Root,Writer) && FFileHelper::SaveStringToFile(
        Json,*(State.Directory/TEXT("route.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

static void Quit(UWorld* World)
{
    if(World && GEngine)GEngine->Exec(World,TEXT("quit"));
}

static bool Target(UWorld* World,const URaftSimWaterRuntimeAdapter* Axis,
    const URaftSimWaterRuntimeAdapter* Water,FRaftSimGroundSourceRegistry* Ground,
    double Station,FVector& Out,bool& bWet)
{
    bWet=false;
    // Never confuse hydraulic Cartesian east/north with the scenario run axis.
    for(double Lateral : {0.,2.,-2.,5.,-5.,10.,-10.,20.,-20.})
    {
        FVector Candidate,Tangent,Left;
        FVector2D Hydraulic;
        FRaftSimWaterSample Baseline;
        if(!Axis->RiverToWorldPosition({Station,Lateral},Axis->GetRiverVerticalDatumM(),Candidate) ||
            !Water->WorldToRiverCoordinates(Candidate,Hydraulic,Tangent,Left) ||
            !Water->SamplePresentationBaselineFieldAtRiverCoordinates(Hydraulic,Baseline) ||
            !Baseline.bWet || !FMath::IsFinite(Baseline.SurfaceHeightMeters))continue;
        Candidate.Z=100.*Baseline.SurfaceHeightMeters;
        if(Candidate.ContainsNaN())continue;
        Out=Candidate;bWet=true;return true;
    }
    // Compact survey replays render a real live grid but need not carry an
    // immutable presentation baseline. Sample that loaded field, never a
    // default sheet or an extrapolation. bWet remains BASELINE provenance;
    // the separate LiveWaterAtCamera stat records real live coverage below.
    if(Water->HasLiveWindow())
        for(double Lateral : {0.,2.,-2.,5.,-5.,10.,-10.,20.,-20.})
        {
            FVector Candidate;
            FRaftSimWaterSample Live;
            if(!Axis->RiverToWorldPosition({Station,Lateral},Axis->GetRiverVerticalDatumM(),Candidate) ||
                !Water->SampleWaterAtWorldPosition(Candidate,Live) || !Live.bWet ||
                !FMath::IsFinite(Live.SurfaceHeightMeters) || !FMath::IsFinite(Live.DepthMeters) ||
                Live.DepthMeters<=0.)continue;
            Candidate.Z=100.*Live.SurfaceHeightMeters;
            if(Candidate.ContainsNaN())continue;
            Out=Candidate;return true;
        }
    // An authored dry axis point may still be photographed, but cannot be
    // counted as wet/live coverage. Use ACTUAL accepted terrain, never Z=0.
    FVector Center;
    if(!Axis->RiverToWorldPosition({Station,0},Axis->GetRiverVerticalDatumM(),Center))return false;
    // Same registered captured triangles/landscapes as raft collision. Unlike
    // a world channel trace, this excludes intervening boats and accepts the
    // compact scene's RaftSimPhysicalGround component tags as well as actors.
    // Apply the SAME bounded lateral search used for wet targets. An axis
    // endpoint can lie just beyond a rectangular survey while its nearby bank
    // is actually captured. This does not shorten the axis or invent terrain.
    if(Ground)
        for(double Lateral : {0.,2.,-2.,5.,-5.,10.,-10.,20.,-20.})
        {
            FVector Candidate;double GroundZCm=0.;FVector GroundNormal;
            if(!Axis->RiverToWorldPosition({Station,Lateral},Axis->GetRiverVerticalDatumM(),Candidate) ||
                !Ground->SampleGround(Candidate,GroundZCm,GroundNormal) || !FMath::IsFinite(GroundZCm))continue;
            Candidate.Z=GroundZCm;Out=Candidate;return !Out.ContainsNaN();
        }
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimFlightTerrain),true);
    TArray<FHitResult> Hits;
    World->LineTraceMultiByChannel(Hits,Center+FVector(0,0,1.e7),Center-FVector(0,0,1.e7),ECC_Visibility,Params);
    for(const FHitResult& Hit : Hits)
    {
        const AActor* Actor=Hit.GetActor();
        if(!Actor || (!Actor->IsA<ALandscapeProxy>() &&
            !Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")) &&
            !Actor->ActorHasTag(TEXT("RaftSimSourceConditionedTerrain"))))continue;
        Out=Hit.ImpactPoint;return !Out.ContainsNaN();
    }
    return false;
}

static void Finish(const TSharedRef<FFlight>& State,const FString& Failure)
{
    if(State->bEnding)return;
    State->Failure=Failure;State->bEnding=true;
    if(!Failure.IsEmpty())UE_LOG(LogTemp,Error,TEXT("RaftSim flythrough failed at %.3f m: %s"),State->StationM,*Failure);
    SaveReceipt(*State,false);
    State->CsvWritten=FCsvProfiler::Get()->EndCapture();
}

static void Tick(const TSharedRef<FFlight>& State,UWorld* World,ELevelTick,float DeltaSeconds)
{
    if(World!=State->World.Get())return;
    if(State->bEnding)
    {
        CSV_CUSTOM_STAT(RaftSimRoute,Active,0,ECsvCustomStatOp::Set);
        if(!State->CsvWritten.IsValid() || !State->CsvWritten.IsReady())return;
        const FString Csv=State->CsvWritten.Get();
        const bool Complete=State->Failure.IsEmpty() && IFileManager::Get().FileExists(*Csv);
        if(!Complete && State->Failure.IsEmpty())State->Failure=TEXT("Native CSV file missing");
        if(!SaveReceipt(*State,Complete,Csv))UE_LOG(LogTemp,Error,TEXT("RaftSim flythrough receipt write failed"));
        UE_LOG(LogTemp,Display,TEXT("RaftSim flythrough terminal: label=%s complete=%d range=%.3f..%.3f ticks=%d csv=%s"),
            *State->Label,int32(Complete),State->StartM,State->EndM,State->Frames,*Csv);
        FWorldDelegates::OnWorldPostActorTick.Remove(State->TickHandle);
        Quit(World);return;
    }
    if(!FCsvProfiler::IsCapturing())return;
    auto* Camera=State->Camera.Get();auto* Water=State->Water.Get();auto* Axis=State->Axis.Get();auto* Raft=State->Raft.Get();
    if(!Camera || !Water || !Axis || !Raft || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds<=0)
    {Finish(State,TEXT("Lost native camera, water, axis, raft or committed world tick"));return;}
    FVector Position,Ahead;bool Wet=false,AheadWet=false;
    if(!Target(World,Axis,Water,State->Ground.Get(),State->StationM,Position,Wet))
    {Finish(State,TEXT("No wet baseline, actual live water or accepted physical terrain at authored station"));return;}
    double AheadStation=FMath::Min(State->StationM+35.,State->EndM);
    if(AheadStation<=State->StationM)
    {
        FVector Previous;bool PreviousWet=false;
        if(!Target(World,Axis,Water,State->Ground.Get(),FMath::Max(State->StartM,State->StationM-1.),Previous,PreviousWet))
        {Finish(State,TEXT("Final native route tangent unavailable"));return;}
        Ahead=Position+(Position-Previous).GetSafeNormal()*3500.;
    }
    else if(!Target(World,Axis,Water,State->Ground.Get(),AheadStation,Ahead,AheadWet))
    {Finish(State,TEXT("Native camera look-ahead data unavailable"));return;}
    const FVector Location=Position+FVector(0,0,100.*State->HeightM);
    const FVector View=Ahead-Location;
    if(View.IsNearlyZero() || View.ContainsNaN())
    {Finish(State,TEXT("Invalid camera direction"));return;}
    Camera->SetActorLocationAndRotation(Location,View.Rotation());
    FRaftSimWaterSample Live;
    const bool LiveWet=Water->SampleWaterAtWorldPosition(Position,Live) && Live.bWet && FMath::IsFinite(Live.DepthMeters);
    const double BoatDistance=(Raft->GetActorLocation()-Position).Size()/100.;
    if(!FMath::IsFinite(BoatDistance)){Finish(State,TEXT("Nonfinite actual raft position"));return;}
    CSV_CUSTOM_STAT(RaftSimRoute,Active,1,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,Sequence,State->Frames+1,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,StationM,State->StationM,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,StartM,State->StartM,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,EndM,State->EndM,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,WetBaseline,int32(Wet),ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,LiveWaterAtCamera,int32(LiveWet),ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimRoute,BoatDistanceM,BoatDistance,ECsvCustomStatOp::Set);
    ++State->Frames;
    // Render both endpoints for two complete frames. Limit spatial advance
    // under slow frames; do NOT skip the expensive section to maintain speed.
    if(State->StationM>=State->EndM)
    {if(++State->EndFrames>=2)Finish(State,FString());return;}
    if(State->StartFrames++<2)return;
    State->StationM=FMath::Min(State->EndM,State->StationM+FMath::Min(5.,State->SpeedMps*DeltaSeconds));
}

static void Start(const TArray<FString>& Args,UWorld* World)
{
    if(!World || !World->IsGameWorld() || Args.Num()<1 || ActiveFlight.IsValid())
    {UE_LOG(LogTemp,Error,TEXT("RaftSim.FlyThroughMap <fresh-label> [speedMps=40] [heightM=12] [startM] [endM] requires one game world and no flight"));return;}
    const FString Label=Args[0];
    if(Label.IsEmpty() || Label.Len()>80)return;
    for(TCHAR Ch : Label)if(!FChar::IsAlnum(Ch) && Ch!=TEXT('-') && Ch!=TEXT('_') && Ch!=TEXT('.'))return;
    TSharedRef<FFlight> State=MakeShared<FFlight>();
    State->Label=Label;State->World=World;
    State->Ground=MakeShared<FRaftSimGroundSourceRegistry>(World);
    if((Args.Num()>1 && !LexTryParseString(State->SpeedMps,*Args[1])) ||
        (Args.Num()>2 && !LexTryParseString(State->HeightM,*Args[2])) ||
        (Args.Num()>3 && !LexTryParseString(State->RequestedStartM,*Args[3])) ||
        (Args.Num()>4 && !LexTryParseString(State->RequestedEndM,*Args[4])) ||
        !FMath::IsFinite(State->SpeedMps) || State->SpeedMps<1 || State->SpeedMps>100 ||
        !FMath::IsFinite(State->HeightM) || State->HeightM<3 || State->HeightM>50)
    {UE_LOG(LogTemp,Error,TEXT("Invalid flythrough speed or camera height"));return;}
    State->Directory=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("RaftSimValidation/FlyThrough")/Label);
    if(IFileManager::Get().DirectoryExists(*State->Directory))
    {UE_LOG(LogTemp,Error,TEXT("Flythrough evidence exists; refusing overwrite"));return;}
    IFileManager::Get().MakeDirectory(*State->Directory,true);
    ActiveFlight=State;
    FTimerHandle Warmup;
    World->GetTimerManager().SetTimer(Warmup,FTimerDelegate::CreateLambda([State]()
    {
        UWorld* W=State->World.Get();
        auto* GI=W ? W->GetGameInstance() : nullptr;
        auto* Bridge=GI ? GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
        auto* Water=Bridge ? Bridge->GetWaterRuntime() : nullptr;
        const auto* Axis=W && Water ? RaftSimReviewCoordinates::GetMap(W,Water) : nullptr;
        double MinM=0,MaxM=0;ARaftSimRaftActor* Raft=nullptr;int32 Rafts=0;
        if(W)for(TActorIterator<ARaftSimRaftActor> It(W);It;++It){Raft=*It;++Rafts;}
        if(!W || !Water || !Axis || !Axis->HasRiverCoordinateMap() ||
            !Axis->GetExactRiverStationRangeM(MinM,MaxM) || !FMath::IsFinite(MinM) ||
            !FMath::IsFinite(MaxM) || MaxM<=MinM || Rafts!=1 || FCsvProfiler::IsCapturing())
        {
            State->Failure=TEXT("Whole authored axis, single actual raft, water runtime or isolated CSV unavailable");
            SaveReceipt(*State,false);UE_LOG(LogTemp,Error,TEXT("RaftSim flythrough: %s"),*State->Failure);Quit(W);return;
        }
        State->Water=Water;State->Axis=Axis;State->Raft=Raft;
        State->StartM=MinM;State->EndM=MaxM;
        // A requested section stays inside the authored axis.
        if(FMath::IsFinite(State->RequestedStartM))State->StartM=FMath::Clamp(State->RequestedStartM,MinM,MaxM);
        if(FMath::IsFinite(State->RequestedEndM))State->EndM=FMath::Clamp(State->RequestedEndM,State->StartM,MaxM);
        State->StationM=State->StartM;
        APlayerController* PC=W->GetFirstPlayerController();
        ACameraActor* Camera=W->SpawnActor<ACameraActor>();
        if(!PC || !Camera)
        {State->Failure=TEXT("Actual player camera unavailable");SaveReceipt(*State,false);Quit(W);return;}
        RaftSimCameraPresentation::Configure(Camera->GetCameraComponent(),RaftSimCameraPresentation::ResolveExposureBias(W));
        State->Camera=Camera;PC->SetViewTarget(Camera);
        SaveReceipt(*State,false);
        State->TickHandle=FWorldDelegates::OnWorldPostActorTick.AddLambda(
            [State](UWorld* TickWorld,ELevelTick Type,float Dt){Tick(State,TickWorld,Type,Dt);});
        State->bCaptureRequested=true;
        FCsvProfiler::Get()->BeginCapture(-1,State->Directory,State->Label+TEXT(".csv"));
        UE_LOG(LogTemp,Display,TEXT("RaftSim flythrough started: label=%s whole-axis=%.3f..%.3f camera-only speed=%.1f height=%.1f"),
            *State->Label,State->StartM,State->EndM,State->SpeedMps,State->HeightM);
    }),10.f,false);
}
static FAutoConsoleCommandWithWorldAndArgs Command(TEXT("RaftSim.FlyThroughMap"),
    TEXT("Native camera-only recording-free CSV flight, whole axis by default; no boat guidance. <fresh-label> [speedMps] [heightM] [startM] [endM]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&Start));
}
#endif
