// Small engine-rendered controls of the same authored feature current and
// production raft dynamics used by South Fork. No scripted boat trajectories.
#include "RaftSimWaterFeatureKinematics.h"
#include "RaftSimEddyDemoBoundary.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterVfxActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimCameraPresentation.h"
#include "RaftSimScreenRecorderSubsystem.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/DirectionalLight.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "UObject/StrongObjectPtr.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include "ShaderCompiler.h"

#if !UE_BUILD_SHIPPING
#include "RaftSimActualEddyClearanceAudit.h"
namespace
{
struct FWaterFeatureDemo : TSharedFromThis<FWaterFeatureDemo>
{
    TWeakObjectPtr<UWorld> World;
    TStrongObjectPtr<URaftSimChronoRuntimeAdapter> Dynamics;
    TWeakObjectPtr<ARaftSimRaftActor> Boat;
    TWeakObjectPtr<UProceduralMeshComponent> Foam;
    TArray<FVector> Tracers;
    TArray<float> FoamAge;
    TArray<TWeakObjectPtr<UNiagaraComponent>> Spray;
    TArray<FVector> FoamVertices,FoamNormals;
    TArray<FVector2D> FoamUV;
    TArray<FLinearColor> FoamColors;
    TArray<FProcMeshTangent> FoamTangents;
    TArray<TSharedPtr<FJsonValue>> Motion;
    FTimerHandle Timer;
    FString Kind,Label;
    double Seconds=0.0,LastWorldSeconds=0.0,Debt=0.0,LastReceipt=-1.0;
    bool bRecording=false,bFailed=false,bSprayAudited=false;
    bool bCollisionControl=false,bMirroredEddy=false;
    double CollisionRecordingStart=-1.;
    double CollisionWarmupEndSeconds=0.;
    int32 ExcludedWaterCells=0,HiddenFoamPatches=0,ContactImpulses=0,ContactQueries=0,BlockedTracerSteps=0;
    URaftSimWaterRuntimeAdapter::FSupportBreakingSite HoleSite;
    double Duration() const { return Kind==TEXT("eddy") && !bCollisionControl ? 18.0 : 12.0; }

    void UpdateFoamGeometry()
    {
        FoamVertices.Reset();
        for(int32 I=0;I<Tracers.Num();++I)
        {
            const FVector P=Tracers[I];
            const FVector Flow=Velocity(P,true).GetSafeNormal2D();
            const FVector Across(-Flow.Y,Flow.X,0.);
            const bool bSourceFroth=Kind==TEXT("froth") && I>=600;
            const double RadiusCm=bSourceFroth ? 22.+5.*(I%5) : 14.+4.*(I%5);
            FBox2D PatchBounds(ForceInit);
            for(const FVector2D Q : {FVector2D(-1,-1),FVector2D(1,-1),FVector2D(1,1),FVector2D(-1,1)})
            {
                FVector Vertex=P+Flow*(Q.X*RadiusCm*1.6)+Across*(Q.Y*RadiusCm);
                Vertex.Z=Surface(Vertex)*100.+3.;
                FoamVertices.Add(Vertex);
                PatchBounds+=FVector2D(Vertex.X,Vertex.Y);
            }
            if(Kind==TEXT("eddy"))
            {
                // Entire texture support must stay outside the block, not just
                // its centre. Suppress boundary-straddling quads, never move a
                // tracer through/over the solid to conceal a flow error.
                const bool Hidden=RaftSimEddyDemoBoundary::OverlapsFootprint(PatchBounds);
                if(Hidden)++HiddenFoamPatches;
                for(int32 K=0;K<4;++K)
                {
                    FoamColors[I*4+K]=FLinearColor(.92f,.96f,1.f,Hidden?0.f:.9f);
                    if(Hidden)FoamVertices[I*4+K]=P;
                }
            }
            if(bSourceFroth)
            {
                const float Alpha=.9f*(1.f-FMath::SmoothStep(3.f,6.f,FoamAge[I]));
                for(int32 K=0;K<4;++K)FoamColors[I*4+K]=FLinearColor(.92f,.96f,1.f,Alpha);
            }
        }
    }

    float Surface(const FVector& P) const
    {
        if (Kind==TEXT("eddy")) return 0.f;
        const TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites={HoleSite};
        return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(P.X*.01,P.Y*.01),Sites,1.f,.25f);
    }
    FVector Velocity(const FVector& P,bool bSurface) const
    {
        using namespace RaftSimWaterFeatureKinematics;
        const double H=Surface(P),Depth=H+1.8;
        const double Z=bSurface ? 1.0 : FMath::Clamp((P.Z*.01+1.8)/Depth,0.0,1.0);
        if(Kind==TEXT("eddy"))return RaftSimEddyDemoBoundary::Velocity(P);
        return FVector(2.,0,0)+HoleDelta(P.X*.01,P.Y*.01,Z,Depth,2.,1.);
    }
    void Tick()
    {
        // Clearing our timer releases its owning delegate. Keep the demo alive
        // through report serialization and the final capture request.
        const TSharedRef<FWaterFeatureDemo> KeepAlive=AsShared();
        UWorld* W=World.Get();if(!W || !Boat.IsValid())return;
        const double Now=W->GetTimeSeconds();
        if(bCollisionControl && !bRecording)
        {
            // The simulation has not started. Let the actual scene/materials
            // warm up before recording the stationary pre-roll and impact.
            LastWorldSeconds=Now;
            if(Now<CollisionWarmupEndSeconds || (GShaderCompilingManager && GShaderCompilingManager->IsCompiling()))return;
            auto* Recorder=W->GetGameInstance()->GetSubsystem<URaftSimScreenRecorderSubsystem>();
            bRecording=Recorder && Recorder->StartRecording();CollisionRecordingStart=Now;
            if(!bRecording)bFailed=true;
        }
        // Start the impact recording before integration, with a one-second
        // stationary pre-roll. No already-simulated impact is cut from video.
        if(bCollisionControl && bRecording && Now-CollisionRecordingStart<1.)
        {LastWorldSeconds=Now;return;}
        Debt+=FMath::Max(Now-LastWorldSeconds,0.0);LastWorldSeconds=Now;
        int32 Steps=0;
        while(!bFailed && Debt>=1./120. && Steps<240 && Seconds<Duration())
        {
            if(!Dynamics->StepRaftDynamics(1.f/120.f)){bFailed=true;break;}
            if(Kind==TEXT("eddy"))
            {
                const auto& Contact=Dynamics->GetLastHullContact();
                ContactImpulses+=Contact.Impulses;ContactQueries+=Contact.Queries;
            }
            for(int32 I=0;I<Tracers.Num();++I)
            {
                FVector& P=Tracers[I];
                if(Kind==TEXT("eddy"))
                {
                    if(!RaftSimEddyDemoBoundary::Advect(P,1./120.))
                    {++BlockedTracerSteps;bFailed=true;break;}
                }
                else P+=Velocity(P,true)*(100./120.);
                P.Z=Surface(P)*100.+2.;
                // Explicit inlet recycling only after an exit. Not boat motion.
                if(P.X>3700. || P.X<-700. || FMath::Abs(P.Y)>1100.)
                {P.X=-650.;P.Y=FMath::Clamp(P.Y,-1050.,1050.);}
                if(Kind==TEXT("froth") && I>=600)
                {
                    // Foam is sourced by the crest, carried by the shared
                    // current, and fades with age. It adds no separate force
                    // to the raft and never prescribes a boat trajectory.
                    FoamAge[I]+=1.f/120.f;
                    if(FoamAge[I]>=6.f)
                    {
                        FoamAge[I]=0.f;
                        P.X=120.+double((I*73)%120);P.Y=-330.+double((I*113)%660);
                        P.Z=Surface(P)*100.+2.;
                    }
                }
            }
            Seconds+=1./120.;Debt-=1./120.;++Steps;
            // Capture actual integrated states at a bounded simulation-time
            // cadence, including catch-up steps on slow render frames.
            // Recording only after the loop loses contact/transient evidence.
            RecordMotion();
        }
        if(Kind==TEXT("eddy"))Boat->RefreshIsolatedFeatureHull();
        Boat->SetActorTransform(Dynamics->GetKinematicState().WorldTransform);
        if(!bSprayAudited && Seconds>=2.)
        {
            bSprayAudited=true;
            for(auto Effect:Spray)if(Effect.IsValid())
            {
                UE_LOG(LogTemp,Display,TEXT("Feature spray asset=%s active=%d visible=%d registered=%d"),
                    *GetNameSafe(Effect->GetAsset()),int32(Effect->IsActive()),int32(Effect->IsVisible()),int32(Effect->IsRegistered()));
            }
            if(GEngine)GEngine->Exec(W,TEXT("fx.Niagara.DumpComponents"));
        }
        if(Foam.IsValid())
        {
            UpdateFoamGeometry();
            Foam->UpdateMeshSection_LinearColor(0,FoamVertices,FoamNormals,FoamUV,FoamColors,FoamTangents);
        }
        if(GEngine)GEngine->AddOnScreenDebugMessage(7441,.2f,FColor::White,
            FString::Printf(TEXT("%s | shared authored current + production hull forces | t=%.2fs | no paddle"),*Kind,Seconds));
        if(!bRecording && Seconds>1.)
        {
            auto* Recorder=W->GetGameInstance()->GetSubsystem<URaftSimScreenRecorderSubsystem>();
            bRecording=Recorder && Recorder->StartRecording();
            if(!bRecording){bFailed=true;UE_LOG(LogTemp,Error,TEXT("Feature demo recorder unavailable"));}
        }
        if(bFailed || Seconds>=Duration())
        {
            RecordMotion(true);
            W->GetTimerManager().ClearTimer(Timer);
            if(bRecording)W->GetGameInstance()->GetSubsystem<URaftSimScreenRecorderSubsystem>()->StopRecording();
            auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("schema"),TEXT("raftsim.engine_feature_demo.v1"));
            Report->SetStringField(TEXT("feature"),Kind);Report->SetBoolField(TEXT("failed"),bFailed);
            Report->SetStringField(TEXT("scope"),TEXT("Authored isolated current; production CustomReducedRigidBody, no pose forcing, no paddle. Not surveyed hydraulics, final optics, river acceptance or FPS measurement."));
            Report->SetNumberField(TEXT("simulated_seconds"),Seconds);Report->SetNumberField(TEXT("unprocessed_seconds"),Debt);
            Report->SetStringField(TEXT("motion_sampling"),TEXT("Actual fixed-step integrated states; no interpolation. Video remains actual render-frame capture."));
            if(Kind==TEXT("eddy"))
            {
                Report->SetBoolField(TEXT("bed_connected_obstruction"),true);
                Report->SetBoolField(TEXT("collision_control"),bCollisionControl);
                Report->SetBoolField(TEXT("mirrored_entry"),bMirroredEddy);
                Report->SetStringField(TEXT("eddy_current"),TEXT("Boundary-masked streamfunction: -X return in obstacle shadow, outward head turn, +X outer branch. Exact centreline is a separatrix; no scripted boat kick or escape."));
                Report->SetNumberField(TEXT("excluded_water_cells"),ExcludedWaterCells);
                Report->SetNumberField(TEXT("hidden_boundary_foam_patches"),HiddenFoamPatches);
                Report->SetNumberField(TEXT("blocked_tracer_steps"),BlockedTracerSteps);
                Report->SetNumberField(TEXT("full_hull_contact_queries"),ContactQueries);
                Report->SetNumberField(TEXT("full_hull_contact_impulses"),ContactImpulses);
                if(bCollisionControl && ContactImpulses==0){bFailed=true;Report->SetBoolField(TEXT("failed"),true);}
            }
            Report->SetArrayField(TEXT("motion"),Motion);
            FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            FFileHelper::SaveStringToFile(Json,*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")/(Label+TEXT(".json"))));
            FScreenshotRequest::RequestScreenshot(Label+TEXT("-final"),false,false);
            FTimerHandle Exit;W->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},2.f,false);
        }
    }

    void RecordMotion(bool bFinal=false)
    {
        if(Seconds>LastReceipt && (bFinal || Seconds-LastReceipt>=.1))
        {
            LastReceipt=Seconds;
            const auto& S=Dynamics->GetKinematicState();const FVector P=S.WorldTransform.GetLocation();
            const FVector V=Velocity(P,false);const FRotator R=S.WorldTransform.Rotator();
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("seconds"),Seconds);
            Row->SetNumberField(TEXT("x_m"),P.X*.01);Row->SetNumberField(TEXT("y_m"),P.Y*.01);
            Row->SetNumberField(TEXT("z_m"),P.Z*.01);Row->SetNumberField(TEXT("yaw_deg"),R.Yaw);
            Row->SetNumberField(TEXT("roll_deg"),R.Roll);Row->SetNumberField(TEXT("pitch_deg"),R.Pitch);
            Row->SetNumberField(TEXT("boat_u_mps"),S.LinearVelocityMetersPerSecond.X);
            Row->SetNumberField(TEXT("boat_v_mps"),S.LinearVelocityMetersPerSecond.Y);
            Row->SetNumberField(TEXT("water_u_mps"),V.X);Row->SetNumberField(TEXT("water_v_mps"),V.Y);
            TArray<TSharedPtr<FJsonValue>> TracerRows;
            for(int32 I=0;I<FMath::Min(16,Tracers.Num());++I)
            {
                auto Tracer=MakeShared<FJsonObject>();Tracer->SetNumberField(TEXT("x_m"),Tracers[I].X*.01);
                Tracer->SetNumberField(TEXT("y_m"),Tracers[I].Y*.01);
                TracerRows.Add(MakeShared<FJsonValueObject>(Tracer));
            }
            Row->SetArrayField(TEXT("surface_tracers"),TracerRows);
            Motion.Add(MakeShared<FJsonValueObject>(Row));
        }
    }
};

void StartWaterFeatureDemo(const TArray<FString>& Args,UWorld* World)
{
    if(!World || Args.Num()<1 || (Args[0]!=TEXT("hole") && Args[0]!=TEXT("eddy") && Args[0]!=TEXT("froth")))return;
    auto Demo=MakeShared<FWaterFeatureDemo>();Demo->World=World;Demo->Kind=Args[0];
    Demo->bCollisionControl=Demo->Kind==TEXT("eddy") && Args.Num()>2 && Args[2]==TEXT("collision");
    Demo->bMirroredEddy=Demo->Kind==TEXT("eddy") && Args.Num()>2 && Args[2]==TEXT("mirror");
    Demo->Label=Args.Num()>1 ? Args[1] : TEXT("shared-feature-")+Args[0];
    Demo->HoleSite.RiverCoordinatesMeters=FVector2D::ZeroVector;Demo->HoleSite.Intensity=1.f;
    Demo->HoleSite.PhysicalCrestHeightMeters=.8f;Demo->HoleSite.PhysicalCrestLengthMeters=2.f;
    Demo->HoleSite.SpillingFraction=1.f;Demo->HoleSite.bLocalEnvelopeCap=true;
    ARaftSimRaftActor* Boat=nullptr;
    for(TActorIterator<AActor> It(World);It;++It)
    {
        if(auto* R=Cast<ARaftSimRaftActor>(*It)){Boat=R;continue;}
        if(It->FindComponentByClass<UMeshComponent>())It->SetActorHiddenInGame(true);
    }
    if(!Boat)Boat=World->SpawnActor<ARaftSimRaftActor>();
    if(!Boat){UE_LOG(LogTemp,Error,TEXT("Feature demo needs production raft visual"));return;}
    Boat->SetActorTickEnabled(false);Boat->SetActorHiddenInGame(false);Demo->Boat=Boat;
    Demo->Dynamics=TStrongObjectPtr<URaftSimChronoRuntimeAdapter>(NewObject<URaftSimChronoRuntimeAdapter>());
    FRaftSimRaftBodyConfig Body;
    if(auto* Bridge=World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        if(Bridge->GetRaftRuntime())Body=Bridge->GetRaftRuntime()->GetRaftBodyConfig();
    Body.Runtime=ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    FRaftSimFlexParameters Flex;Flex.MassKg=Body.MassKg;Flex.LengthM=Body.LengthMeters;Flex.WidthM=Body.WidthMeters;
    Flex.TubeRadiusM=Body.TubeRadiusMeters;Flex.GuideMassKg=0;Flex.PassengerMassKg=0;Flex.PassengerCount=0;
    Demo->Dynamics->ConfigureRaftBody(Body);Demo->Dynamics->ConfigureFlexibleRaftModel(Flex,{});
    TWeakPtr<FWaterFeatureDemo> Weak=Demo;
    Demo->Dynamics->SetWaterSurfaceSampler([Weak](const FVector& P,float& H){auto D=Weak.Pin();if(!D || (D->Kind==TEXT("eddy") && RaftSimEddyDemoBoundary::Solid(P)))return false;H=D->Surface(P)*100.;return true;});
    Demo->Dynamics->SetFlexibleWaterFieldSampler([Weak](const FVector& P,FRaftSimFlexUniformWater& Out)
    {auto D=Weak.Pin();if(!D)return false;Out.bWet=!(D->Kind==TEXT("eddy") && RaftSimEddyDemoBoundary::Solid(P));Out.SurfaceHeightM=D->Surface(P);Out.VelocityMps=D->Velocity(P,false);return true;});
    if(Demo->Kind==TEXT("eddy"))
    {
        const FVector Scale=Boat->GetActorScale3D();
        UE_LOG(LogTemp,Display,TEXT("Eddy production initialization: actor=%s production=%d scale=(%.17g,%.17g,%.17g)"),
            *Boat->GetName(),int32(Boat->HasProductionWhitewaterRaft()),Scale.X,Scale.Y,Scale.Z);
        if(!Boat->BindIsolatedFeatureHull(Demo->Dynamics.Get()))
        {UE_LOG(LogTemp,Error,TEXT("Eddy demo requires the actual production hull geometry"));return;}
        Demo->Dynamics->SetHullGroundQuery(RaftSimEddyDemoBoundary::Sweep);
    }
    FRaftSimRaftKinematicState Initial;
    // Within the block's downstream shadow, slightly off the exact symmetric
    // separatrix so the shared current can select the upper return branch.
    FVector Start=Demo->Kind==TEXT("eddy") ? FVector(1600,160,0) : FVector(440,0,0);
    if(Demo->bMirroredEddy)Start.Y=-Start.Y;
    if(Demo->bCollisionControl)
    {
        double NoseM=Body.LengthMeters*.5+Body.TubeRadiusMeters;
        for(const auto& P:Demo->Dynamics->GetHullGeometry().VerticesM)NoseM=FMath::Max(NoseM,P.X);
        Start=FVector(-200.-NoseM*100.-40.,0,0);
        Initial.LinearVelocityMetersPerSecond=FVector(4,0,0);
    }
    FVector StartPose=Start;StartPose.Z=Demo->Surface(Start)*100.;Initial.WorldTransform.SetLocation(StartPose);
    Initial.WorldTransform.SetRotation(FRotator(0,Demo->bCollisionControl ? 0. : Demo->Kind==TEXT("eddy") ? (Demo->bMirroredEddy ? -35. : 35.) : 10.,0).Quaternion());
    Demo->Dynamics->SetKinematicState(Initial);
    // Recording pre-roll must show this state, not the tank's original pose.
    Boat->SetActorTransform(Initial.WorldTransform);
    if(Demo->Kind==TEXT("eddy"))Boat->RefreshIsolatedFeatureHull();
    Demo->CollisionWarmupEndSeconds=World->GetTimeSeconds()+3.;
    AActor* Apparatus=World->SpawnActor<AActor>();auto* Water=NewObject<UProceduralMeshComponent>(Apparatus);
    Apparatus->SetRootComponent(Water);Water->RegisterComponent();Water->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TArray<FVector> V,N;TArray<int32> Tri;TArray<FVector2D> UV;TArray<FLinearColor> C;TArray<FProcMeshTangent> T;
    const int32 Nx=185,Ny=97;
    for(int32 Y=0;Y<Ny;++Y)for(int32 X=0;X<Nx;++X)
    {
        const FVector P(-800.+X*25.,-1200.+Y*25.,0);const float H=Demo->Surface(P);
        V.Add(FVector(P.X,P.Y,H*100.));
        N.Add(FVector(-(Demo->Surface(P+FVector(5,0,0))-Demo->Surface(P-FVector(5,0,0)))/.1,
            -(Demo->Surface(P+FVector(0,5,0))-Demo->Surface(P-FVector(0,5,0)))/.1,1.).GetSafeNormal());
        UV.Add(FVector2D(X*.15,Y*.15));
        C.Add(FLinearColor(.05f,.18f,.23f,1.f));T.Add(FProcMeshTangent(1,0,0));
        if(X<Nx-1 && Y<Ny-1)
        {
            const FBox2D Cell(FVector2D(P.X,P.Y),FVector2D(P.X+25.,P.Y+25.));
            if(Demo->Kind==TEXT("eddy") && RaftSimEddyDemoBoundary::OverlapsFootprint(Cell))++Demo->ExcludedWaterCells;
            else {const int32 I=Y*Nx+X;Tri.Append({I,I+Nx,I+1,I+1,I+Nx,I+Nx+1});}
        }
    }
    Water->CreateMeshSection_LinearColor(0,V,Tri,N,UV,C,T,false);
    Water->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.M_RaftSim_PhotorealRiverWater")));
    if(Demo->Kind!=TEXT("eddy"))
    {
        // Reuse the actual river renderer's multi-valued lip, not a new
        // liquid solver. This aerated skin is presentation-only; raft support
        // remains the documented carrier and the shared depth-aware current.
        auto* Lip=NewObject<UProceduralMeshComponent>(Apparatus);
        Lip->SetupAttachment(Water);Lip->RegisterComponent();
        Lip->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        TArray<FVector> LV,LN;TArray<int32> LT;TArray<FVector2D> LU;
        TArray<FLinearColor> LC;TArray<FProcMeshTangent> LTan;
        constexpr int32 SpanSteps=40,CurlSteps=48;
        for(int32 A=0;A<=SpanSteps;++A)for(int32 B=0;B<=CurlSteps;++B)
        {
            const float Across=float(A)/SpanSteps*2.f-1.f,Phase=float(B)/CurlSteps;
            const float Edge=FMath::Square(1.f-Across*Across);
            const FVector2D P=ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(Phase,1.f);
            const FVector2D Before=ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(FMath::Max(0.f,Phase-.01f),1.f);
            const FVector2D After=ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(FMath::Min(1.f,Phase+.01f),1.f);
            const FVector Tangent(After.X-Before.X,0,(After.Y-Before.Y)*Edge);
            const float Fold=FMath::Sin(Across*7.f+Phase*4.f)*12.f*Edge*FMath::Sin(PI*Phase);
            LV.Add(FVector(P.X,Across*330.f,P.Y*Edge+Fold+3.f));
            LN.Add(FVector::CrossProduct(Tangent,FVector::YAxisVector).GetSafeNormal());
            LU.Add(FVector2D(float(A)/SpanSteps,Phase));
            LC.Add(FLinearColor(.9f,.2f,FMath::Exp(-FMath::Square((Phase-.35f)/.18f)),Edge));
            LTan.Add(FProcMeshTangent(0,1,0));
            if(A<SpanSteps && B<CurlSteps)
            {const int32 I=A*(CurlSteps+1)+B;LT.Append({I,I+CurlSteps+1,I+1,I+1,I+CurlSteps+1,I+CurlSteps+2});}
        }
        Lip->CreateMeshSection_LinearColor(0,LV,LT,LN,LU,LC,LTan,false);
        Lip->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip.M_RaftSim_BreakingWaterLip")));
        if(auto* Material=Lip->CreateAndSetMaterialInstanceDynamic(0))
        {
            Material->SetScalarParameterValue(TEXT("BreakingWaterOpacity"),.035f);
            Material->SetScalarParameterValue(TEXT("BreakingFoamOpacity"),.86f);
            Material->SetScalarParameterValue(TEXT("BreakingFoamFloor"),.60f);
            Material->SetScalarParameterValue(TEXT("BreakingFoamIntensityGain"),.90f);
            Material->SetScalarParameterValue(TEXT("BreakingFoamRoughness"),.82f);
        }
    }
    auto* Foam=NewObject<UProceduralMeshComponent>(Apparatus);Foam->SetupAttachment(Water);Foam->RegisterComponent();
    Foam->SetCollisionEnabled(ECollisionEnabled::NoCollision);Foam->SetCastShadow(false);Demo->Foam=Foam;
    Foam->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle.M_RaftSim_NiagaraWaterParticle")));
    if(auto* FoamMaterial=Foam->CreateAndSetMaterialInstanceDynamic(0))
    {
        // Surface patches must not vanish inside the airborne spray's 14 cm
        // intersection fade. Keep the native atlas and age-weighted opacity.
        FoamMaterial->SetScalarParameterValue(TEXT("ParticleDepthFadeCm"),1.f);
        FoamMaterial->SetScalarParameterValue(TEXT("ParticleRoughness"),.8f);
        FoamMaterial->SetScalarParameterValue(TEXT("ParticleSpecular"),.08f);
    }
    FRandomStream Seed(61001);
    TArray<int32> FoamTriangles;
    for(int32 I=0;I<1200;++I)
    {
        FVector P(Seed.FRandRange(-600,3500),Seed.FRandRange(-1050,1050),0);P.Z=Demo->Surface(P)*100.+3.;
        if(Demo->Kind==TEXT("eddy"))
            while(RaftSimEddyDemoBoundary::Solid(P)){P.X=Seed.FRandRange(-600,3500);P.Y=Seed.FRandRange(-1050,1050);}
        if(Demo->Kind==TEXT("eddy") && I<16)
        {
            const double Angle=I*2.*UE_PI/16.;
            P=FVector(1600.+150.*FMath::Cos(Angle),160.+60.*FMath::Sin(Angle),2.);
            if(Demo->bMirroredEddy)P.Y=-P.Y;
        }
        if(Demo->Kind==TEXT("froth") && I>=600)
        {P.X=120.+double((I*73)%120);P.Y=-330.+double((I*113)%660);P.Z=Demo->Surface(P)*100.+2.;}
        Demo->Tracers.Add(P);Demo->FoamAge.Add(float(I%60)*.1f);
        const int32 Base=I*4;FoamTriangles.Append({Base,Base+1,Base+2,Base,Base+2,Base+3});
        const FVector2D Tile((I%4)*.25,((I/4)%4)*.25);
        for(const FVector2D Q : {FVector2D(0,0),FVector2D(1,0),FVector2D(1,1),FVector2D(0,1)})
        {
            Demo->FoamUV.Add(Tile+Q*.25);Demo->FoamColors.Add(FLinearColor(.92f,.96f,1.f,.9f));
            Demo->FoamNormals.Add(FVector::UpVector);Demo->FoamTangents.Add(FProcMeshTangent(1,0,0));
        }
    }
    Demo->UpdateFoamGeometry();
    Foam->CreateMeshSection_LinearColor(0,Demo->FoamVertices,FoamTriangles,Demo->FoamNormals,Demo->FoamUV,Demo->FoamColors,Demo->FoamTangents,false);
    auto* Rock=NewObject<UStaticMeshComponent>(Apparatus);Rock->SetupAttachment(Water);Rock->RegisterComponent();
    Rock->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Rock->SetWorldLocation(Demo->Kind==TEXT("eddy") ? RaftSimEddyDemoBoundary::BoxCm().GetCenter() : FVector(0,0,-130.));
    Rock->SetWorldScale3D(Demo->Kind==TEXT("eddy") ? RaftSimEddyDemoBoundary::BoxCm().GetSize()/100. : FVector(4.,12.,1.));
    Rock->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    if(Demo->Kind==TEXT("eddy"))
    {
        Rock->UpdateBounds();
        const FBox Expected=RaftSimEddyDemoBoundary::BoxCm(),Actual=Rock->Bounds.GetBox();
        if(!Actual.Min.Equals(Expected.Min,.01) || !Actual.Max.Equals(Expected.Max,.01))
        {UE_LOG(LogTemp,Error,TEXT("Eddy block render/contact bounds disagree"));return;}
    }
    if(Demo->Kind!=TEXT("eddy"))
    {
        for(const TCHAR* SystemName : {TEXT("NS_RaftSim_RapidRoller"),TEXT("NS_RaftSim_RapidCrestSpray")})
        {
            auto* Effect=NewObject<UNiagaraComponent>(Apparatus);Effect->SetupAttachment(Water);Effect->RegisterComponent();
            const FString Path=FString::Printf(TEXT("/Game/RaftSim/VFX/Water/%s.%s"),SystemName,SystemName);
            if(auto* System=LoadObject<UNiagaraSystem>(nullptr,*Path))
            {
                Effect->SetAsset(System);Effect->SetWorldLocation(FVector(150,0,Demo->Surface(FVector(150,0,0))*100.+10.));
                Effect->SetWorldRotation(FRotator(25.,0.,0.));
                Effect->SetVariableQuat(TEXT("User.SourcePlaneRotation"),
                    ARaftSimWaterVfxActor::ComputeRapidSourcePlaneRotation(Effect->GetForwardVector()));
                Effect->SetVariableFloat(TEXT("User.SpawnRate"),Demo->Kind==TEXT("froth") ? 600.f : 240.f);
                Effect->AddWorldOffset(FVector(0.,0.,30.));
                Effect->SetWorldScale3D(FVector(1.,2.,1.));Effect->Activate(true);
                Demo->Spray.Add(Effect);
            }
        }
    }
    auto* Camera=World->SpawnActor<ACameraActor>(FVector(1000,-1200,1000),FRotator(-33,140,0));
    if(Demo->Kind==TEXT("eddy"))Camera->SetActorLocation(Demo->bCollisionControl ? FVector(-1200,-1400,1200) : FVector(2400,-2500,2500));
    const FVector Focus=Demo->bCollisionControl ? FVector(-200,0,0) : Demo->Kind==TEXT("eddy") ? FVector(1600,250,0) : FVector(550,0,0);
    Camera->SetActorRotation((Focus-Camera->GetActorLocation()).Rotation());
    RaftSimCameraPresentation::Configure(Camera->GetCameraComponent());World->GetFirstPlayerController()->SetViewTarget(Camera);
    Camera->GetCameraComponent()->SetFieldOfView(60.f);
    if(auto* Hud=World->GetFirstPlayerController()->GetHUD())Hud->bShowHUD=false;
    if(auto* Viewport=World->GetGameInstance()->GetGameViewportClient())Viewport->RemoveAllViewportWidgets();
    IFileManager::Get().MakeDirectory(*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")),true);
    Demo->LastWorldSeconds=World->GetTimeSeconds();
    World->GetTimerManager().SetTimer(Demo->Timer,FTimerDelegate::CreateLambda([Demo]{Demo->Tick();}),1.f/60.f,true);
    UE_LOG(LogTemp,Display,TEXT("WaterFeatureDemo kind=%s body_mass=%g actual production forces; appearance prototype"),*Demo->Kind,Body.MassKg);
}
FAutoConsoleCommandWithWorldAndArgs FeatureDemoCommand(TEXT("RaftSim.FeatureDemo"),
    TEXT("Isolated engine-rendered authored feature: hole|eddy|froth [label] [collision|mirror]. Writes actual hull motion and video."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&StartWaterFeatureDemo));

// One initial condition in the ACTUAL map. No added geometry, hull, current,
// or subsequent guidance: the production raft then evolves freely.
void ScheduleActualEddyEntry(const TArray<FString>& Args,UWorld* World)
{
    if(!World || Args.Num()!=1 || !RaftSimWaterFeatureKinematics::IsPlayableRiver(World->GetMapName()))return;
    const FString Label=FPaths::MakeValidFileName(Args[0]);
    const TWeakObjectPtr<UWorld> WeakWorld=World;
    FTimerHandle Start;
    World->GetTimerManager().SetTimer(Start,FTimerDelegate::CreateLambda([WeakWorld,Label]
    {
        UWorld* W=WeakWorld.Get();if(!W)return;
        auto* Bridge=W->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
        auto* Water=Bridge ? Bridge->GetWaterRuntime() : nullptr;
        ARaftSimRaftActor* Raft=nullptr;
        if(TActorIterator<ARaftSimRaftActor> It(W);It)Raft=*It;
        if(!Water || !Raft || !Water->HasFeatureKinematics())return;
        FRaftSimGroundSourceRegistry Ground(W);
        double BestRadius=0.;FVector BestPosition,Facing;
        URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint Selected;
        for(const auto& Rock : Water->GetFeatureBoulderFootprints())
        {
            if(Rock.RadiusMeters<2.f || Rock.RadiusMeters<=BestRadius || Rock.PhysicalSource.IsEmpty())continue;
            const FVector2D D=Rock.FlowDirection,L(-D.Y,D.X);
            if(D.IsNearlyZero())continue;
            bool FlowQualified=true,HasStartPosition=false;FVector StartPosition=FVector::ZeroVector;
            for(const FVector2D Local : {FVector2D(4,.1),FVector2D(1.75,.6),FVector2D(2.25,1.25)})
            {
                const FVector2D Q=Rock.RiverCoordinatesMeters+(D*Local.X+L*Local.Y)*Rock.RadiusMeters;
                FRaftSimWaterSample Raw;
                if(!Water->SampleWaterFieldAtRiverCoordinates(Q,Raw) || !Raw.bWet){FlowQualified=false;break;}
                const FVector Shared=Water->SampleFeatureSurfaceVelocity(Q,FVector2D(Raw.VelocityMetersPerSecond.X,Raw.VelocityMetersPerSecond.Y),Raw.DepthMeters);
                const double Along=Shared.X*D.X+Shared.Y*D.Y,Across=Shared.X*L.X+Shared.Y*L.Y;
                if((Local.X==4 && Along>=-.1) || (Local.X==1.75 && Across<=.05) || (Local.X==2.25 && Along<=.1))
                {FlowQualified=false;break;}
                if(Local.X==4)
                {
                    HasStartPosition=Water->RiverToWorldPosition(Q,Raw.SurfaceHeightMeters+Water->GetRiverVerticalDatumM(),StartPosition);
                    if(!HasStartPosition){FlowQualified=false;break;}
                }
            }
            if(!FlowQualified || !HasStartPosition)continue;
            // Conservative initial-condition clearance probes only. They
            // do not replace the production raft's actual hull/contact.
            // Directly behind the obstacle, with a small nonzero offset to
            // avoid an exactly symmetric initial condition. The earlier .4R
            // entry put the finite-width hull on the outer shear/exit branch.
            const FVector2D Q0=Rock.RiverCoordinatesMeters+(D*4.+L*.1)*Rock.RadiusMeters;
            for(const FVector2D Offset : {FVector2D(0,0),FVector2D(3,1.4),FVector2D(3,-1.4),FVector2D(-3,1.4),FVector2D(-3,-1.4)})
            {
                FRaftSimWaterSample Raw;FVector P,Normal;double GroundZ=0.;
                const FVector2D Q=Q0+D*Offset.X+L*Offset.Y;
                if(!Water->SampleWaterFieldAtRiverCoordinates(Q,Raw) || !Raw.bWet || Raw.DepthMeters<.6 ||
                    !Water->RiverToWorldPosition(Q,Raw.SurfaceHeightMeters+Water->GetRiverVerticalDatumM(),P) ||
                    !Ground.SampleGround(P,GroundZ,Normal) || P.Z-GroundZ<50.)
                {FlowQualified=false;break;}
            }
            if(!FlowQualified)continue;
            FVector Ahead;
            if(!Water->RiverToWorldPosition(Q0+D,StartPosition.Z*.01,Ahead))continue;
            Facing=Ahead-StartPosition;BestPosition=StartPosition+FVector(0,0,40);
            Selected=Rock;BestRadius=Rock.RadiusMeters;
        }
        if(BestRadius<=0.)
        {
            UE_LOG(LogTemp,Error,TEXT("Actual EddyEntry refused: no existing physical owner has verified return/head/exit wet flow and safe production-raft initial clearance; nothing moved"));
            return;
        }
        Raft->TeleportForTesting(BestPosition,Facing.Rotation().Yaw,true);
        auto Receipt=MakeShared<FJsonObject>();
        Receipt->SetStringField(TEXT("scope"),TEXT("One verified initial-condition placement of the existing production raft in the actual river. No subsequent guidance, forced trajectory, new hull, or authored current override."));
        Receipt->SetStringField(TEXT("physical_source"),Selected.PhysicalSource);
        Receipt->SetNumberField(TEXT("world_seconds"),W->GetTimeSeconds());
        Receipt->SetNumberField(TEXT("owner_hydraulic_x_m"),Selected.RiverCoordinatesMeters.X);
        Receipt->SetNumberField(TEXT("owner_hydraulic_y_m"),Selected.RiverCoordinatesMeters.Y);
        Receipt->SetNumberField(TEXT("owner_direction_x"),Selected.FlowDirection.X);
        Receipt->SetNumberField(TEXT("owner_direction_y"),Selected.FlowDirection.Y);
        Receipt->SetNumberField(TEXT("inferred_radius_m"),BestRadius);
        Receipt->SetNumberField(TEXT("entry_local_x_radius"),4.);
        Receipt->SetNumberField(TEXT("entry_local_y_radius"),.1);
        RaftSimActualEddyClearanceAudit::Run(W,Water,Selected,Receipt);
        FString Json;FJsonSerializer::Serialize(Receipt,TJsonWriterFactory<>::Create(&Json));
        IFileManager::Get().MakeDirectory(*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")),true);
        FFileHelper::SaveStringToFile(Json,*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")/(Label+TEXT("-entry.json"))));
        UE_LOG(LogTemp,Display,TEXT("Actual EddyEntry placed existing raft once: owner=(%.3f,%.3f) radius=%.3f source=%s"),Selected.RiverCoordinatesMeters.X,Selected.RiverCoordinatesMeters.Y,BestRadius,*Selected.PhysicalSource);
    }),8.f,false);
}
FAutoConsoleCommandWithWorldAndArgs ActualEddyEntryCommand(TEXT("RaftSim.EddyEntry"),
    TEXT("One safe initial-condition placement behind an existing physical playable-river obstacle: [label]. Production boat then evolves freely."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ScheduleActualEddyEntry));

// Diagnostic only: verify the public hull sampler agrees with the exact
// surface-current evaluator used by foam, at actual loaded river positions.
void ScheduleFeatureAudit(const TArray<FString>& Args,UWorld* World)
{
    if(!World || Args.Num()<1 || Args.Num()>2)return;
    const float DurationSeconds=Args.Num()==2 ? FCString::Atof(*Args[1]) : 10.f;
    if(!FMath::IsFinite(DurationSeconds) || DurationSeconds<1.f || DurationSeconds>120.f)
    {
        UE_LOG(LogTemp,Error,TEXT("FeatureAudit duration must be between 1 and 120 world seconds; no audit started"));
        return;
    }
    const FString Label=Args[0];const TWeakObjectPtr<UWorld> WeakWorld=World;
    auto Motion=MakeShared<TArray<TSharedPtr<FJsonValue>>>();
    FTimerHandle MotionTimer;
    World->GetTimerManager().SetTimer(MotionTimer,FTimerDelegate::CreateLambda([WeakWorld,Motion]
    {
        UWorld* W=WeakWorld.Get();if(!W)return;
        auto* Bridge=W->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
        if(!Bridge || !Bridge->GetRaftRuntime())return;
        const auto& S=Bridge->GetRaftRuntime()->GetKinematicState();
        const FVector P=S.WorldTransform.GetLocation();const FRotator R=S.WorldTransform.Rotator();
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("world_seconds"),W->GetTimeSeconds());
        Row->SetNumberField(TEXT("world_x_m"),P.X*.01);Row->SetNumberField(TEXT("world_y_m"),P.Y*.01);
        Row->SetNumberField(TEXT("world_z_m"),P.Z*.01);Row->SetNumberField(TEXT("yaw_deg"),R.Yaw);
        Row->SetNumberField(TEXT("pitch_deg"),R.Pitch);Row->SetNumberField(TEXT("roll_deg"),R.Roll);
        Row->SetNumberField(TEXT("speed_mps"),S.LinearVelocityMetersPerSecond.Size());
        Row->SetNumberField(TEXT("velocity_world_x_mps"),S.LinearVelocityMetersPerSecond.X);
        Row->SetNumberField(TEXT("velocity_world_y_mps"),S.LinearVelocityMetersPerSecond.Y);
        Row->SetNumberField(TEXT("velocity_world_z_mps"),S.LinearVelocityMetersPerSecond.Z);
        auto* Water=Bridge->GetWaterRuntime();
        FVector2D Coordinates;FVector Tangent,Left;
        if(Water && Water->WorldToRiverCoordinates(P,Coordinates,Tangent,Left))
        {
            Row->SetNumberField(TEXT("hydraulic_x_m"),Coordinates.X);
            Row->SetNumberField(TEXT("hydraulic_y_m"),Coordinates.Y);
            Row->SetNumberField(TEXT("velocity_hydraulic_x_mps"),FVector::DotProduct(S.LinearVelocityMetersPerSecond,Tangent));
            Row->SetNumberField(TEXT("velocity_hydraulic_y_mps"),FVector::DotProduct(S.LinearVelocityMetersPerSecond,Left));
        }
        Motion->Add(MakeShared<FJsonValueObject>(Row));
    }),.5f,true);
    FTimerHandle AuditTimer;
    World->GetTimerManager().SetTimer(AuditTimer,FTimerDelegate::CreateLambda([WeakWorld,Label,Motion,MotionTimer,DurationSeconds]() mutable
    {
        UWorld* W=WeakWorld.Get();if(!W)return;
        W->GetTimerManager().ClearTimer(MotionTimer);
        auto* Bridge=W->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
        if(!Bridge || !Bridge->GetWaterRuntime() || !Bridge->GetRaftRuntime())return;
        auto* Water=Bridge->GetWaterRuntime();
        const FVector Center=Bridge->GetRaftRuntime()->GetKinematicState().WorldTransform.GetLocation();
        int32 Wet=0,Changed=0,DryViolations=0;double MaximumDelta=0.,MaximumError=0.;
        TArray<TSharedPtr<FJsonValue>> Examples;
        for(int32 X=-10;X<=10;++X)for(int32 Y=-10;Y<=10;++Y)
        {
            FVector P=Center+FVector(X*200.,Y*200.,0.);
            FRaftSimWaterSample Support,Interaction;
            if(!Water->SampleRaftSupportSurfaceAtWorldPosition(P,Support))continue;
            P.Z=Support.SurfaceHeightMeters*100.;
            if(!Water->SampleRaftInteractionWaterAtWorldPosition(P,Interaction))continue;
            if(!Support.bWet){DryViolations+=Interaction.bWet;continue;}
            ++Wet;
            FVector2D Coordinates;FVector Tangent,Left;
            if(!Water->WorldToRiverCoordinates(P,Coordinates,Tangent,Left))continue;
            const FVector2D Base(FVector::DotProduct(Support.VelocityMetersPerSecond,Tangent),
                FVector::DotProduct(Support.VelocityMetersPerSecond,Left));
            const float Depth=FMath::Max(Support.SurfaceHeightMeters-Support.BedHeightMeters,.05f);
            const FVector Field=Water->SampleFeatureSurfaceVelocity(Coordinates,Base,Depth);
            const FVector Expected=Tangent*Field.X+Left*Field.Y+FVector::UpVector*Field.Z;
            MaximumError=FMath::Max(MaximumError,(Interaction.VelocityMetersPerSecond-Expected).Size());
            const double Delta=(Interaction.VelocityMetersPerSecond-Support.VelocityMetersPerSecond).Size();
            MaximumDelta=FMath::Max(MaximumDelta,Delta);Changed+=Delta>1.e-6;
            if(Delta>.01 && Examples.Num()<24)
            {
                auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("world_x_m"),P.X*.01);
                Row->SetNumberField(TEXT("world_y_m"),P.Y*.01);Row->SetNumberField(TEXT("raw_speed_mps"),Support.VelocityMetersPerSecond.Size());
                Row->SetNumberField(TEXT("interaction_speed_mps"),Interaction.VelocityMetersPerSecond.Size());
                Row->SetNumberField(TEXT("current_delta_mps"),Delta);Examples.Add(MakeShared<FJsonValueObject>(Row));
            }
        }
        auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("scope"),TEXT("Actual public hull sampler versus shared surface-current evaluator in loaded map. No inferred global conservation or visual acceptance."));
        Report->SetBoolField(TEXT("feature_kinematics_enabled"),Water->HasFeatureKinematics());
        Report->SetStringField(TEXT("map"),W->GetMapName());Report->SetNumberField(TEXT("wet_probes"),Wet);
        Report->SetNumberField(TEXT("changed_probes"),Changed);Report->SetNumberField(TEXT("maximum_current_delta_mps"),MaximumDelta);
        Report->SetNumberField(TEXT("maximum_shared_surface_error_mps"),MaximumError);Report->SetNumberField(TEXT("dry_became_wet"),DryViolations);
        Report->SetArrayField(TEXT("examples"),Examples);
        Report->SetArrayField(TEXT("actual_boat_motion"),*Motion);
        Report->SetStringField(TEXT("motion_sampling_scope"),TEXT("Actual production raft states sampled by a world timer every 0.5 seconds; render-timer receipts, not fixed-step traces or interpolated motion."));
        Report->SetNumberField(TEXT("requested_audit_duration_seconds"),DurationSeconds);
        Report->SetNumberField(TEXT("audit_world_seconds"),W->GetTimeSeconds());
        TArray<TSharedPtr<FJsonValue>> RockRows;
        for(const auto& Rock : Water->GetFeatureBoulderFootprints())
        {
            auto Item=MakeShared<FJsonObject>();
            Item->SetNumberField(TEXT("hydraulic_x_m"),Rock.RiverCoordinatesMeters.X);
            Item->SetNumberField(TEXT("hydraulic_y_m"),Rock.RiverCoordinatesMeters.Y);
            Item->SetNumberField(TEXT("radius_m"),Rock.RadiusMeters);
            Item->SetStringField(TEXT("physical_source"),Rock.PhysicalSource);
            Item->SetStringField(TEXT("radius_scope"),TEXT("Inferred/authored wake scale; the existing physical mesh/contact owns solid geometry, not this radius."));
            Item->SetNumberField(TEXT("owner_direction_x"),Rock.FlowDirection.X);
            Item->SetNumberField(TEXT("owner_direction_y"),Rock.FlowDirection.Y);
            TArray<TSharedPtr<FJsonValue>> Probes;
            for(const FVector2D& Local : {FVector2D(4,0),FVector2D(4,.4),FVector2D(1.75,.6),FVector2D(2.25,1.25)})
            {
                const FVector2D D=Rock.FlowDirection,L(-D.Y,D.X);
                const FVector2D Q=Rock.RiverCoordinatesMeters+(D*Local.X+L*Local.Y)*Rock.RadiusMeters;
                FRaftSimWaterSample Raw;
                if(!Water->SampleWaterFieldAtRiverCoordinates(Q,Raw) || !Raw.bWet)continue;
                const FVector2D Base(Raw.VelocityMetersPerSecond.X,Raw.VelocityMetersPerSecond.Y);
                const FVector Shared=Water->SampleFeatureSurfaceVelocity(Q,Base,Raw.DepthMeters);
                auto Probe=MakeShared<FJsonObject>();
                Probe->SetNumberField(TEXT("local_x_radius"),Local.X);Probe->SetNumberField(TEXT("local_y_radius"),Local.Y);
                Probe->SetNumberField(TEXT("shared_along_mps"),Shared.X*D.X+Shared.Y*D.Y);
                Probe->SetNumberField(TEXT("shared_across_mps"),Shared.X*L.X+Shared.Y*L.Y);
                Probes.Add(MakeShared<FJsonValueObject>(Probe));
            }
            Item->SetArrayField(TEXT("actual_wet_shared_current_probes"),Probes);
            RockRows.Add(MakeShared<FJsonValueObject>(Item));
        }
        Report->SetNumberField(TEXT("active_physical_eddy_owners"),RockRows.Num());
        Report->SetArrayField(TEXT("physical_eddy_owners"),RockRows);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        IFileManager::Get().MakeDirectory(*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")),true);
        FFileHelper::SaveStringToFile(Json,*(FPaths::ProjectSavedDir()/TEXT("WaterFeatureDemo")/(Label+TEXT(".json"))));
        UE_LOG(LogTemp,Display,TEXT("SharedFeatureAudit enabled=%d wet=%d changed=%d max_delta=%g max_error=%g dry_became_wet=%d"),
            int32(Water->HasFeatureKinematics()),Wet,Changed,MaximumDelta,MaximumError,DryViolations);
    }),DurationSeconds,false);
}
FAutoConsoleCommandWithWorldAndArgs FeatureAuditCommand(TEXT("RaftSim.FeatureAudit"),
    TEXT("Audit actual shared current/hull surface parity and motion: [label] [duration_seconds=10]."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ScheduleFeatureAudit));
}
#endif
