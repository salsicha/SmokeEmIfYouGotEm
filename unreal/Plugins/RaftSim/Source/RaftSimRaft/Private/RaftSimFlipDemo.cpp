#include "RaftSimFlipTestEnvironment.h"
#include "RaftSimFlipObstacle.h"
#include "RaftSimFlipCandidateLoads.h"
#include "RaftSimRaftActor.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimScreenRecorderSubsystem.h"
#include "RaftSimCameraPresentation.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "ProceduralMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "UObject/StrongObjectPtr.h"
#include "TimerManager.h"
#include "ShaderCompiler.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "UnrealClient.h"

#if !UE_BUILD_SHIPPING
bool ARaftSimRaftActor::BindIsolatedFlipRuntime(URaftSimChronoRuntimeAdapter* Runtime,bool bFullHullExport)
{
    if(bFullHullExport)return BindIsolatedFeatureHull(Runtime);
    if(!Runtime || !bUsingProductionRaftRestMesh || GetActorScale3D()!=FVector::OneVector)return false;
    // No terrain query in open-water controls. Use the normal production
    // mesh refresh, not an unused source-surface collision export at 120 Hz.
    RaftAdapter=Runtime;bSharedHullGeometryReview=false;bHasRenderedFlexibleRaftState=false;
    return Runtime->SetHullGeometryProvider({},{});
}
void ARaftSimRaftActor::RefreshIsolatedFlipVisual(float Dt)
{
    if(RaftAdapter && RaftAdapter->GetHullGeometryRevision()>0)RefreshIsolatedFeatureHull();
    else UpdateFlexibleRaftVisual();
    UpdateCrew(FMath::Min(Dt,.25f)); // Same render-frame clock as normal play.
}
namespace
{
struct FFlipDemo: TSharedFromThis<FFlipDemo>
{
    TWeakObjectPtr<UWorld> World;
    TWeakObjectPtr<ARaftSimRaftActor> Boat;
    TStrongObjectPtr<URaftSimChronoRuntimeAdapter> Dynamics;
    TWeakObjectPtr<UProceduralMeshComponent> Water;
    TWeakObjectPtr<ACameraActor> Camera;
    FVector GridCenter=FVector::ZeroVector;
    bool bWaterCreated=false;
    RaftSimFlipTestEnvironment::FScene Scene;
    TArray<FVector> Vertices,Normals;
    TArray<FVector2D> UV;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    TArray<TSharedPtr<FJsonValue>> Motion;
    FTimerHandle Timer;
    FString Label;
    double Seconds=0.,Debt=0.,LastWorld=0.,WarmupUntil=0.,RecordingStart=-1.,LastReceipt=-1.;
    double DurationSeconds=12.;
    double MinimumUp=1.,MaximumOmega=0.,FirstCapsizeSeconds=-1.,RiskSeconds=0.;
    double MinimumSurfaceOffset=DBL_MAX,MaximumSurfaceOffset=-DBL_MAX,MaximumPoseStep=0.;
    double MaximumOmegaStep=0.,RenderSeconds=0.;int32 RenderFrames=0;
    double LastRenderWall=0.;uint64 LastEngineFrame=MAX_uint64;
    int64 ContactImpulses=0;
    double MinimumSwimmerOffset=0.;int32 MaximumSubmergedCrew=0;
    RaftSimOverwashLoads::FLoad CandidateLoad;
    double InitialUp=1.,InitialOmega=0.,PressureWorkImpulse=0.;
    bool bRecording=false,bFailed=false;
    void UpdateWater()
    {
        constexpr double H=.05;
        if(Boat.IsValid())
        {
            const FVector P=Boat->GetActorLocation();
            GridCenter=FVector(FMath::GridSnap(P.X,300.),FMath::GridSnap(P.Y,300.),0.);
            if(Camera.IsValid())
            {
                const FVector Target(P.X,P.Y,Scene.Surface(P,Seconds)*100.);
                Camera->SetActorLocation(Target+FVector(850,-1100,800));
                Camera->SetActorRotation((Target-Camera->GetActorLocation()).Rotation());
            }
        }
        for(int32 Y=0;Y<81;++Y)for(int32 X=0;X<81;++X)
        {
            const FVector P=GridCenter+FVector((X-40)*30.,(Y-40)*30.,0);
            Vertices[Y*81+X]=FVector(P.X,P.Y,Scene.Surface(P,Seconds)*100.);
            UV[Y*81+X]=FVector2D(P.X*.005,P.Y*.005);
            const double Dx=(Scene.Surface(P+FVector(H*100,0,0),Seconds)-Scene.Surface(P-FVector(H*100,0,0),Seconds))/(2*H);
            const double Dy=(Scene.Surface(P+FVector(0,H*100,0),Seconds)-Scene.Surface(P-FVector(0,H*100,0),Seconds))/(2*H);
            Normals[Y*81+X]=FVector(-Dx,-Dy,1).GetSafeNormal();
        }
        if(Water.IsValid() && bWaterCreated)
        {
            if(Scene.bObstacle)
            {
                // The visible solid footprint stays fixed as the review
                // window follows the raft; never draw water under the rock.
                TArray<int32> Tri;
                for(int32 Y=0;Y<80;++Y)for(int32 X=0;X<80;++X)
                {
                    const double L=GridCenter.X+(X-40)*30.,B=GridCenter.Y+(Y-40)*30.;
                    if(L+30.>-60. && L<60. && B+30.>-120. && B<120.)continue;
                    const int32 I=Y*81+X;Tri.Append({I,I+81,I+1,I+1,I+81,I+82});
                }
                Water->CreateMeshSection_LinearColor(0,Vertices,Tri,Normals,UV,Colors,Tangents,false);
            }
            else Water->UpdateMeshSection_LinearColor(0,Vertices,Normals,UV,Colors,Tangents);
        }
    }
    void Receipt(bool bFinal=false)
    {
        if(Seconds<=LastReceipt || (!bFinal && Seconds-LastReceipt<.1))return;
        LastReceipt=Seconds;
        const auto& State=Dynamics->GetKinematicState();const auto& T=Dynamics->GetLastFlexibleStepTelemetry();
        const auto Q=State.WorldTransform.GetRotation();const auto P=State.WorldTransform.GetLocation();
        auto R=MakeShared<FJsonObject>();R->SetNumberField(TEXT("seconds"),Seconds);
        R->SetNumberField(TEXT("x_m"),P.X*.01);R->SetNumberField(TEXT("y_m"),P.Y*.01);R->SetNumberField(TEXT("z_m"),P.Z*.01);
        R->SetNumberField(TEXT("roll_deg"),Q.Rotator().Roll);R->SetNumberField(TEXT("pitch_deg"),Q.Rotator().Pitch);
        R->SetNumberField(TEXT("yaw_deg"),Q.Rotator().Yaw);
        R->SetNumberField(TEXT("quat_x"),Q.X);R->SetNumberField(TEXT("quat_y"),Q.Y);
        R->SetNumberField(TEXT("quat_z"),Q.Z);R->SetNumberField(TEXT("quat_w"),Q.W);
        R->SetNumberField(TEXT("omega_x_rad_s"),State.AngularVelocityRadiansPerSecond.X);
        R->SetNumberField(TEXT("omega_y_rad_s"),State.AngularVelocityRadiansPerSecond.Y);
        R->SetNumberField(TEXT("omega_z_rad_s"),State.AngularVelocityRadiansPerSecond.Z);
        R->SetNumberField(TEXT("surface_offset_m"),P.Z*.01-Scene.Surface(P,Seconds));
        R->SetNumberField(TEXT("up_z"),Q.GetUpVector().Z);R->SetNumberField(TEXT("omega_rad_s"),State.AngularVelocityRadiansPerSecond.Size());
        R->SetNumberField(TEXT("boat_u_mps"),State.LinearVelocityMetersPerSecond.X);R->SetNumberField(TEXT("boat_v_mps"),State.LinearVelocityMetersPerSecond.Y);
        R->SetNumberField(TEXT("mode"),int32(Boat->GetRaftMode()));R->SetNumberField(TEXT("swimmers"),Boat->GetSwimmerCount());
        R->SetNumberField(TEXT("flip_margin_nm"),T.ReferenceFlipMarginNm);R->SetNumberField(TEXT("dynamic_roll_nm"),T.OvertoppingDynamicRollMomentNm);
        R->SetNumberField(TEXT("torque_x_nm"),T.AppliedTorqueNm.X);R->SetNumberField(TEXT("torque_y_nm"),T.AppliedTorqueNm.Y);
        R->SetNumberField(TEXT("contact_impulses"),ContactImpulses);
        R->SetNumberField(TEXT("candidate_pressure_force_n"),CandidateLoad.ForceN.Size());
        R->SetNumberField(TEXT("candidate_pressure_roll_nm"),CandidateLoad.TorqueNm.X);
        if(Scene.bPillowRock)
        {
            // Nominal tube-centre probes, not deformed mesh vertices. Label
            // sides by downstream WORLD direction. Evidence only: no forces.
            const auto& Flex=Dynamics->GetFlexibleParameters();
            const double Side=Flex.WidthM*.5-Flex.TubeRadiusM;
            const FVector A=P*.01+Q.RotateVector(FVector(0,Side,0));
            const FVector B=P*.01+Q.RotateVector(FVector(0,-Side,0));
            const FVector Downstream=A.X>B.X ? A : B,Upstream=A.X>B.X ? B : A;
            const auto Offset=[&](const FVector& V){return V.Z-Scene.Surface(V*100.,Seconds);};
            R->SetNumberField(TEXT("downstream_tube_center_z_m"),Downstream.Z);
            R->SetNumberField(TEXT("upstream_tube_center_z_m"),Upstream.Z);
            R->SetNumberField(TEXT("downstream_minus_upstream_tube_height_m"),Downstream.Z-Upstream.Z);
            R->SetNumberField(TEXT("downstream_tube_surface_offset_m"),Offset(Downstream));
            R->SetNumberField(TEXT("upstream_tube_top_surface_offset_m"),Offset(Upstream)+Q.GetUpVector().Z*Flex.TubeRadiusM);
            // Broadside longitudinal axis is world +Y; report actual signed
            // scoop torque about that axis, not the unrelated world X torque.
            R->SetNumberField(TEXT("scoop_longitudinal_torque_nm"),FVector::DotProduct(CandidateLoad.TorqueNm,Q.GetForwardVector()));
            R->SetNumberField(TEXT("retained_water_kg"),T.TotalRetainedWaterMassKg);
            R->SetStringField(TEXT("tube_probe_scope"),TEXT("Nominal body-local tube centre/top probes transformed by actual integrated pose; not exported mesh vertices."));
        }
        TArray<TSharedPtr<FJsonValue>> Crew;int32 Submerged=0;
        for(const auto& S:Boat->GetIsolatedFlipSwimmers())
        {
            const FVector Pcm=S.SwimmerWorldPositionMeters*100.;
            const double Offset=S.SwimmerWorldPositionMeters.Z-Scene.Surface(Pcm,Seconds);
            auto C=MakeShared<FJsonObject>();C->SetStringField(TEXT("passenger"),S.PassengerId.ToString());
            C->SetNumberField(TEXT("surface_offset_m"),Offset);
            C->SetNumberField(TEXT("vertical_velocity_mps"),S.SwimmerDriftVelocityMetersPerSecond.Z);
            C->SetNumberField(TEXT("time_in_water_s"),S.TimeInWaterSeconds);
            Crew.Add(MakeShared<FJsonValueObject>(C));
            MinimumSwimmerOffset=FMath::Min(MinimumSwimmerOffset,Offset);
            Submerged+=Offset<-.1 ? 1 : 0;
        }
        MaximumSubmergedCrew=FMath::Max(MaximumSubmergedCrew,Submerged);
        R->SetArrayField(TEXT("crew_motion"),Crew);
        Motion.Add(MakeShared<FJsonValueObject>(R));
    }
    void Tick()
    {
        // A looping timer can catch up repeatedly within one engine frame.
        // Count/render once; wall-clock FPS must not count timer callbacks.
        if(LastEngineFrame==GFrameCounter)return;
        const uint64 EngineFrames=LastEngineFrame==MAX_uint64 ? 0 : GFrameCounter-LastEngineFrame;
        LastEngineFrame=GFrameCounter;
        const auto KeepAlive=AsShared();UWorld* W=World.Get();if(!W || !Boat.IsValid())return;
        const double Now=W->GetTimeSeconds();
        const double Wall=FPlatformTime::Seconds();
        if(!bRecording)
        {
            LastWorld=Now;
            if(Now<WarmupUntil || (GShaderCompilingManager && GShaderCompilingManager->IsCompiling()))return;
            auto* Recorder=W->GetGameInstance()->GetSubsystem<URaftSimScreenRecorderSubsystem>();
            bRecording=Recorder && Recorder->StartRecording();RecordingStart=Now;
            if(!bRecording)bFailed=true;
        }
        if(!bFailed && Now-RecordingStart<1.){LastWorld=Now;LastRenderWall=Wall;return;}
        const double FrameSeconds=FMath::Max(Now-LastWorld,0.);
        if(LastRenderWall>0.)RenderSeconds+=Wall-LastRenderWall;
        LastRenderWall=Wall;RenderFrames+=EngineFrames;Debt+=FrameSeconds;LastWorld=Now;
        int32 Steps=0;
        while(!bFailed && Debt>=1./120. && Steps<240 && Seconds<DurationSeconds)
        {
            CandidateLoad={};
            if(Boat->GetRaftMode()==ERaftSimRaftMode::Upright)
            {
                CandidateLoad=RaftSimFlipCandidateLoads::Evaluate(*Dynamics,Scene,Seconds,1./120.);
                if(CandidateLoad.ForceN.ContainsNaN() || CandidateLoad.TorqueNm.ContainsNaN()){bFailed=true;break;}
                Dynamics->AddExternalImpulse(CandidateLoad.ForceN/120.,CandidateLoad.TorqueNm/120.);
                PressureWorkImpulse+=CandidateLoad.TorqueNm.Size()/120.;
            }
            const auto Previous=Dynamics->GetKinematicState();
            const auto PreviousMode=Boat->GetRaftMode();
            if(!Boat->AdvanceIsolatedFlipDemo(1.f/120.f)){bFailed=true;break;}
            Seconds+=1./120.;Debt-=1./120.;++Steps;
            const auto& State=Dynamics->GetKinematicState();
            MinimumUp=FMath::Min(MinimumUp,State.WorldTransform.GetRotation().GetUpVector().Z);
            MaximumOmega=FMath::Max(MaximumOmega,State.AngularVelocityRadiansPerSecond.Size());
            MaximumPoseStep=FMath::Max(MaximumPoseStep,Previous.WorldTransform.GetRotation().AngularDistance(State.WorldTransform.GetRotation()));
            MaximumOmegaStep=FMath::Max(MaximumOmegaStep,(Previous.AngularVelocityRadiansPerSecond-State.AngularVelocityRadiansPerSecond).Size());
            const FVector P=State.WorldTransform.GetLocation();
            const double SurfaceOffset=P.Z*.01-Scene.Surface(P,Seconds);
            MinimumSurfaceOffset=FMath::Min(MinimumSurfaceOffset,SurfaceOffset);MaximumSurfaceOffset=FMath::Max(MaximumSurfaceOffset,SurfaceOffset);
            if(Dynamics->GetLastFlexibleStepTelemetry().bReferenceFlipRisk)RiskSeconds+=1./120.;
            ContactImpulses+=Dynamics->GetLastHullContact().Impulses;
            if(FirstCapsizeSeconds<0. && Boat->GetRaftMode()==ERaftSimRaftMode::Capsized)FirstCapsizeSeconds=Seconds;
            if(State.WorldTransform.ContainsNaN() || State.AngularVelocityRadiansPerSecond.ContainsNaN())bFailed=true;
            Receipt(PreviousMode!=Boat->GetRaftMode());
        }
        Boat->RefreshIsolatedFlipVisual(float(Steps/120.));
        UpdateWater();
        if(GEngine)GEngine->AddOnScreenDebugMessage(7452,.2f,FColor::White,
            FString::Printf(TEXT("Flip lab candidate: %s | native forces; no pose animation | %.2fs | %g kg"),*Scene.Name,Seconds,Dynamics->GetRaftBodyConfig().MassKg));
        if(bFailed || Seconds>=DurationSeconds)
        {
            Receipt(true);W->GetTimerManager().ClearTimer(Timer);
            if(bRecording)W->GetGameInstance()->GetSubsystem<URaftSimScreenRecorderSubsystem>()->StopRecording();
            auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("scene"),Scene.Name);R->SetBoolField(TEXT("failed"),bFailed);
            R->SetNumberField(TEXT("simulated_seconds"),Seconds);R->SetNumberField(TEXT("minimum_up_z"),MinimumUp);
            R->SetNumberField(TEXT("requested_simulated_duration_seconds"),DurationSeconds);
            R->SetNumberField(TEXT("maximum_omega_rad_s"),MaximumOmega);R->SetNumberField(TEXT("first_capsize_seconds"),FirstCapsizeSeconds);
            R->SetNumberField(TEXT("risk_seconds"),RiskSeconds);R->SetArrayField(TEXT("motion"),Motion);
            R->SetNumberField(TEXT("minimum_surface_offset_m"),MinimumSurfaceOffset);
            R->SetNumberField(TEXT("maximum_surface_offset_m"),MaximumSurfaceOffset);
            R->SetNumberField(TEXT("maximum_pose_step_rad"),MaximumPoseStep);
            R->SetNumberField(TEXT("maximum_omega_step_rad_s"),MaximumOmegaStep);
            R->SetNumberField(TEXT("rendered_fps_mean"),RenderSeconds>0. ? RenderFrames/RenderSeconds : 0.);
            R->SetBoolField(TEXT("plausible_depth"),MinimumSurfaceOffset>=-2.);
            R->SetNumberField(TEXT("contact_impulses"),ContactImpulses);
            R->SetNumberField(TEXT("initial_roll_degrees"),Scene.InitialRollDegrees);
            R->SetNumberField(TEXT("initial_roll_rate_rad_s"),Scene.InitialRollRateRadS);
            R->SetNumberField(TEXT("initial_up_z"),InitialUp);
            R->SetNumberField(TEXT("initial_omega_rad_s"),InitialOmega);
            R->SetNumberField(TEXT("sampled_pressure_angular_impulse_magnitude_nms"),PressureWorkImpulse);
            R->SetBoolField(TEXT("timed_pose_transition_used"),false);
            R->SetStringField(TEXT("external_impulse_sources"),Scene.bPillowRock
                ? TEXT("D3 dipped upper-face incoming-normal water pressure; no scripted roll impulse or quaternion target.")
                : TEXT("D3 sampled upper-face water pressure only; no scripted roll impulse or quaternion target."));
            R->SetNumberField(TEXT("minimum_swimmer_surface_offset_m"),MinimumSwimmerOffset);
            R->SetNumberField(TEXT("maximum_submerged_crew"),MaximumSubmergedCrew);
            R->SetStringField(TEXT("geometry_path"),Scene.bObstacle ? TEXT("original source triangles exported per native substep for full-hull CCD") : TEXT("normal production deformation/render path; open water, no terrain query"));
            R->SetStringField(TEXT("scope"),TEXT("Lab-only upper-face pressure and physical-inversion candidate using actual production mesh/loading, native D2/D3, game impulse integrator and real crew lifecycle. Normal gameplay unchanged. Authored field, not calibrated hydraulics. Fixed-step receipts and native video."));
            FString Json;FJsonSerializer::Serialize(R,TJsonWriterFactory<>::Create(&Json));
            const FString Dir=FPaths::ProjectSavedDir()/TEXT("FlipDemo");IFileManager::Get().MakeDirectory(*Dir,true);
            FFileHelper::SaveStringToFile(Json,*(Dir/(Label+TEXT(".json"))));
            UE_LOG(LogTemp,Display,TEXT("FLIP_DEMO_COMPLETE label=%s failed=%d min_up=%g first_capsize=%g omega_max=%g"),*Label,int32(bFailed),MinimumUp,FirstCapsizeSeconds,MaximumOmega);
            FScreenshotRequest::RequestScreenshot(Label+TEXT("-final"),false,false);
            FTimerHandle Exit;W->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},2.f,false);
        }
    }
};
void StartFlipDemo(const TArray<FString>& Args,UWorld* W)
{
    if(!W || Args.Num()!=2)return;
    auto Demo=MakeShared<FFlipDemo>();Demo->World=W;Demo->Label=Args[1];
    if(Demo->Label.IsEmpty() || Demo->Label!=FPaths::MakeValidFileName(Demo->Label) ||
        IFileManager::Get().FileExists(*(FPaths::ProjectSavedDir()/TEXT("FlipDemo")/(Demo->Label+TEXT(".json")))))
    {UE_LOG(LogTemp,Error,TEXT("Flip validation requires a fresh plain filename label; prior receipt preserved"));return;}
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimFlipValidationDuration="),Demo->DurationSeconds);
    if(!FMath::IsFinite(Demo->DurationSeconds) || Demo->DurationSeconds<12. || Demo->DurationSeconds>40.)
    {UE_LOG(LogTemp,Error,TEXT("Flip observation duration must be 12..40 seconds; no run started"));return;}
    const auto Scenes=RaftSimFlipTestEnvironment::Scenes();const auto* Scene=Scenes.FindByPredicate([&](const auto& S){return S.Name==Args[0];});
    if(!Scene){UE_LOG(LogTemp,Error,TEXT("Unknown flip lab scene: %s"),*Args[0]);return;}Demo->Scene=*Scene;
    ARaftSimRaftActor* Boat=nullptr;for(TActorIterator<ARaftSimRaftActor> It(W);It;++It){Boat=*It;break;}
    auto* Bridge=W->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    auto* Reference=Bridge ? Bridge->GetRaftRuntime() : nullptr;
    if(!Boat || !Reference){UE_LOG(LogTemp,Error,TEXT("Flip lab requires initialized production boat/runtime"));return;}
    Boat->SetActorTickEnabled(false);Demo->Boat=Boat;
    Demo->Dynamics=TStrongObjectPtr<URaftSimChronoRuntimeAdapter>(NewObject<URaftSimChronoRuntimeAdapter>());
    Demo->Dynamics->ConfigureRaftBody(Reference->GetRaftBodyConfig());
    Demo->Dynamics->ConfigureFlexibleRaftModel(Reference->GetFlexibleParameters(),Reference->GetFlexibleSeats(),18000.,true);
    const TWeakPtr<FFlipDemo> Weak=Demo;
    Demo->Dynamics->SetWaterSurfaceSampler([Weak](const FVector& P,float& H){auto D=Weak.Pin();if(!D || !D->Scene.Wet(P))return false;H=D->Scene.Surface(P,D->Seconds)*100.;return true;});
    Demo->Dynamics->SetFlexibleWaterFieldSampler([Weak](const FVector& P,FRaftSimFlexUniformWater& V)
        {auto D=Weak.Pin();if(!D)return false;V.bWet=D->Scene.Wet(P);V.SurfaceHeightM=D->Scene.Surface(P,D->Seconds);V.VelocityMps=D->Scene.Velocity(P,D->Seconds);return true;});
    if(!Boat->BindIsolatedFlipRuntime(Demo->Dynamics.Get(),Scene->bObstacle)){UE_LOG(LogTemp,Error,TEXT("Flip lab refused production hull"));return;}
    if(Scene->bObstacle)
    {
        const bool Pin=Scene->bPinnedBreaker;
        const bool Pillow=Scene->bPillowRock;
        Demo->Dynamics->SetHullGroundQuery([Pin,Pillow](TConstArrayView<FVector> A,TConstArrayView<FVector> B,
            TConstArrayView<FIntVector> Faces,double Skin,double Clearance)
            {return RaftSimFlipObstacle::Sweep(A,B,Faces,Skin,Clearance,Pin,Pillow);});
        Demo->Dynamics->SetGroundSurfaceSampler([Pin,Pillow](const FVector& P,float& Z,FVector& N)
            {const bool OnRock=FMath::Abs(P.X)<=60. && FMath::Abs(P.Y)<=120.;
             Z=OnRock ? RaftSimFlipObstacle::TopCm(P.X,Pin,Pillow) : -200.;
             N=OnRock ? RaftSimFlipObstacle::TopNormal(Pillow) : FVector::UpVector;return true;});
    }
    FRaftSimRaftKinematicState Initial;FVector Start(0,0,20);
    if(Scene->bHydraulic){Start=FVector(0,-500,20);Initial.LinearVelocityMetersPerSecond=FVector(0,3.5,0);}
    if(Scene->bObstacle){Start=FVector(-600,60,20);Initial.LinearVelocityMetersPerSecond=FVector(4,0,0);Initial.WorldTransform.SetRotation(FRotator(0,25,0).Quaternion());}
    if(Scene->bPinnedBreaker || Scene->bPillowRock)
    {
        const FQuat Q=FRotator(0,90,0).Quaternion();double HalfWidth=0.;
        for(const auto& P:Demo->Dynamics->GetHullGeometry().VerticesM)HalfWidth=FMath::Max(HalfWidth,Q.RotateVector(P).X);
        Start=FVector((- .6-HalfWidth-.4)*100.,0,0);Start.Z=Scene->Surface(Start,0.)*100.+20.;
        Initial.WorldTransform.SetRotation(Q);Initial.LinearVelocityMetersPerSecond=FVector(1.5,0,0);
        if(Scene->bPillowRock && Scene->PillowCurrentMps==0.)Initial.LinearVelocityMetersPerSecond=FVector::ZeroVector;
    }
    Initial.WorldTransform.SetLocation(Start);
    if(Scene->InitialRollDegrees!=0.)
    {
        Initial.WorldTransform.SetRotation(FQuat(FVector::ForwardVector,FMath::DegreesToRadians(Scene->InitialRollDegrees)));
        Initial.AngularVelocityRadiansPerSecond=FVector(Scene->InitialRollRateRadS,0,0);
    }
    Demo->InitialUp=Initial.WorldTransform.GetRotation().GetUpVector().Z;
    Demo->InitialOmega=Initial.AngularVelocityRadiansPerSecond.Size();
    Demo->Dynamics->SetKinematicState(Initial);Boat->SetActorTransform(Initial.WorldTransform);Boat->RefreshIsolatedFlipVisual(0.f);
    for(TActorIterator<AActor> It(W);It;++It)
        if(*It!=Boat && It->GetAttachParentActor()!=Boat && It->FindComponentByClass<UMeshComponent>())It->SetActorHiddenInGame(true);
    auto* Apparatus=W->SpawnActor<AActor>();auto* Water=NewObject<UProceduralMeshComponent>(Apparatus);Apparatus->SetRootComponent(Water);
    Water->RegisterComponent();Water->SetCollisionEnabled(ECollisionEnabled::NoCollision);Demo->Water=Water;
    TArray<int32> Tri;Demo->Vertices.SetNum(81*81);Demo->Normals.SetNum(81*81);
    for(int32 Y=0;Y<81;++Y)for(int32 X=0;X<81;++X)
    {
        Demo->UV.Add(FVector2D(X*.15,Y*.15));Demo->Colors.Add(FLinearColor(.05,.18,.23,1));Demo->Tangents.Add(FProcMeshTangent(1,0,0));
        if(X<80 && Y<80)
        {
            const double Left=(X-40)*30.,Bottom=(Y-40)*30.;
            const bool SolidCell=Scene->bObstacle && Left+30.>-60. && Left<60. && Bottom+30.>-120. && Bottom<120.;
            if(!SolidCell){const int32 I=Y*81+X;Tri.Append({I,I+81,I+1,I+1,I+81,I+82});}
        }
    }
    Demo->UpdateWater();Water->CreateMeshSection_LinearColor(0,Demo->Vertices,Tri,Demo->Normals,Demo->UV,Demo->Colors,Demo->Tangents,false);Demo->bWaterCreated=true;
    Demo->UpdateWater();
    Water->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.M_RaftSim_PhotorealRiverWater")));
    if(Scene->bObstacle)
    {
        auto* Rock=NewObject<UProceduralMeshComponent>(Apparatus);Rock->SetupAttachment(Water);Rock->RegisterComponent();
        Rock->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        TArray<FVector> RV;TArray<FIntVector> Faces;RaftSimFlipObstacle::Geometry(RV,Faces,Scene->bPinnedBreaker,Scene->bPillowRock);TArray<int32> RT;
        for(const auto& F:Faces)RT.Append({F.X,F.Y,F.Z});
        Rock->CreateMeshSection_LinearColor(0,RV,RT,{}, {}, {}, {},false);
        Rock->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
    }
    auto* Camera=W->SpawnActor<ACameraActor>(FVector(850,-1100,800),FRotator::ZeroRotator);
    Demo->Camera=Camera;Demo->UpdateWater();
    RaftSimCameraPresentation::Configure(Camera->GetCameraComponent());
    Camera->GetCameraComponent()->SetFieldOfView(60.);auto* Controller=W->GetFirstPlayerController();Controller->SetViewTarget(Camera);
    if(auto* Hud=Controller->GetHUD())Hud->bShowHUD=false;
    if(auto* Viewport=W->GetGameInstance()->GetGameViewportClient())Viewport->RemoveAllViewportWidgets();
    Demo->LastWorld=W->GetTimeSeconds();Demo->WarmupUntil=Demo->LastWorld+3.;
    W->GetTimerManager().SetTimer(Demo->Timer,FTimerDelegate::CreateLambda([Demo]{Demo->Tick();}),1.f/60.f,true);
    UE_LOG(LogTemp,Display,TEXT("FLIP_DEMO_BEGIN scene=%s label=%s production_mass=%g"),*Demo->Scene.Name,*Demo->Label,Reference->GetRaftBodyConfig().MassKg);
}
FAutoConsoleCommandWithWorldAndArgs FlipDemoCommand(TEXT("RaftSim.FlipDemo"),
    TEXT("In-engine capsize lab [scene] [fresh label]. Upright wave controls include breaking_broadside_1p8m|2m|2p4m|2p8m|3p2m (full scene names), breaking_broadside_3p2m_mirror and breaking_bow_on_3p2m. Optional -RaftSimFlipValidationDuration=12..40 changes observation time, not forcing."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&StartFlipDemo));
}
#endif
