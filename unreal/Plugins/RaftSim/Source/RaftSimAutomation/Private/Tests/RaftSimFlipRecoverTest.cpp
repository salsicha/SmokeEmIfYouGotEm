// Production fixed-clock water forces -> actual inversion -> crew -> recovery.
// No laboratory force/drag/contact opt-ins and no imposed pose or angular rate.
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimFlipTestEnvironment.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRaftFlipsAndRecoversTest,
    "RaftSim.P2.RaftFlipsAndRecovers",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
namespace
{
ARaftSimRaftActor* FindRaft()
{
    UWorld* W=nullptr;
    for(const auto& C:GEngine->GetWorldContexts())
        if(C.World() && (C.WorldType==EWorldType::PIE || C.WorldType==EWorldType::Game))W=C.World();
    if(W)for(TActorIterator<ARaftSimRaftActor> It(W);It;++It)return *It;
    return nullptr;
}
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FRaftSimForceOverwashCommand,FAutomationTestBase*,Test);
bool FRaftSimForceOverwashCommand::Update()
{
    auto* Raft=FindRaft();if(!Raft){Test->AddError(TEXT("Production raft missing"));return true;}
    Test->TestTrue(TEXT("production boat initially upright"),Raft->GetActorQuat().GetUpVector().Z>.99);
    auto* Bridge=Raft->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    auto* Runtime=Bridge?Bridge->GetRaftRuntime():nullptr;
    if(!Runtime){Test->AddError(TEXT("Normal physics bridge missing for shared breaker"));return true;}
    Test->TestTrue(TEXT("calm full original shape reuses shading, not physics"),
        Raft->GetSharedHullShadingUploadCount()>0 && Raft->GetSharedHullShadingUploadCount()<Runtime->GetHullGeometryRevision());
    const auto Scenes=RaftSimFlipTestEnvironment::Scenes();
    const auto Wave=*Scenes.FindByPredicate([](const auto& S){return S.Name==TEXT("breaking_broadside_3p2m");});
    const double Started=Raft->GetWorld()->GetTimeSeconds();
    const FVector Origin(Raft->GetActorLocation().X,Raft->GetActorLocation().Y,0.);
    const TWeakObjectPtr<UWorld> WeakWorld(Raft->GetWorld());
    Runtime->SetFlexibleUniformWater(FRaftSimFlexUniformWater{},false);
    Runtime->SetWaterSurfaceSampler([Wave,Started,Origin,WeakWorld](const FVector& P,float& Height)
    {if(!WeakWorld.IsValid())return false;Height=Wave.Surface(P-Origin,WeakWorld->GetTimeSeconds()-Started)*100.+Origin.Z;return true;});
    Runtime->SetFlexibleWaterFieldSampler([Wave,Started,Origin,WeakWorld](const FVector& P,FRaftSimFlexUniformWater& W)
    {if(!WeakWorld.IsValid())return false;const double Seconds=WeakWorld->GetTimeSeconds()-Started;
     W.bWet=Wave.Wet(P-Origin);W.SurfaceHeightM=Wave.Surface(P-Origin,Seconds)+Origin.Z*.01;W.VelocityMps=Wave.Velocity(P-Origin,Seconds);return true;});
    return true;
}
class FObserveProductionFlip final:public IAutomationLatentCommand
{
    FAutomationTestBase* Test;double Started=-1.;bool Turned=false;
public:
    explicit FObserveProductionFlip(FAutomationTestBase* T):Test(T){}
    virtual bool Update() override
    {
        auto* Raft=FindRaft();if(!Raft){Test->AddError(TEXT("Production raft disappeared"));return true;}
        const double Now=Raft->GetWorld()->GetTimeSeconds();if(Started<0.)Started=Now;
        auto* Bridge=Raft->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
        auto* Runtime=Bridge?Bridge->GetRaftRuntime():nullptr;
        if(!Runtime){Test->AddError(TEXT("Normal physics bridge missing"));return true;}
        const auto& K=Runtime->GetKinematicState();
        if(K.WorldTransform.ContainsNaN() || K.AngularVelocityRadiansPerSecond.ContainsNaN())
        {Test->AddError(TEXT("Non-finite production flip state"));return true;}
        Turned|=K.AngularVelocityRadiansPerSecond.Size()>.1;
        Test->TestFalse(TEXT("normal gameplay never prescribes a timed capsize pose"),Raft->HasScriptedCapsizeTransition());
        if(Raft->GetRaftMode()==ERaftSimRaftMode::Capsized)
        {
            Test->TestTrue(TEXT("water caused actual rotation before crew ejection"),Turned);
            Test->TestTrue(TEXT("capsize enters only after actual 100-degree inversion"),Raft->GetPhysicalCapsizeEntryUpZ()<=FMath::Cos(FMath::DegreesToRadians(100.)));
            Test->TestEqual(TEXT("original full production hull retained"),Runtime->GetHullGeometry().Faces.Num(),38344);
            Test->TestEqual(TEXT("all five crew eject from physical flip"),Raft->GetSwimmerCount(),5);
            Test->AddInfo(FString::Printf(TEXT("PRODUCTION_PHYSICAL_CAPSIZE up_z=%.9f omega=%.9f swimmers=%d elapsed=%.6f"),
                K.WorldTransform.GetRotation().GetUpVector().Z,K.AngularVelocityRadiansPerSecond.Size(),Raft->GetSwimmerCount(),Now-Started));
            // Return the test tank to its actual flat calm datum before rescue.
            // Only the test water forcing changes; normal boat code is retained.
            Runtime->SetWaterSurfaceSampler([](const FVector&,float& H){H=0.f;return true;});
            Runtime->SetFlexibleWaterFieldSampler([](const FVector&,FRaftSimFlexUniformWater& W)
            {W={};W.bWet=true;return true;});
            Raft->RequestReflip();return true;
        }
        if(Now-Started>15.){Test->AddError(TEXT("Water-generated physical flip did not occur in 15 seconds"));return true;}
        return false;
    }
};
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FRaftSimAssertRecoveredCommand,FAutomationTestBase*,Test);
bool FRaftSimAssertRecoveredCommand::Update()
{
    auto* Raft=FindRaft();if(!Raft){Test->AddError(TEXT("Raft missing during recovery"));return true;}
    Test->TestEqual(TEXT("normal rescue returns upright"),int32(Raft->GetRaftMode()),int32(ERaftSimRaftMode::Upright));
    Test->TestEqual(TEXT("all crew reseated"),Raft->GetSwimmerCount(),0);
    Test->TestTrue(TEXT("recovered raft level"),Raft->GetActorQuat().GetUpVector().Z>FMath::Cos(FMath::DegreesToRadians(30.)));
    return true;
}
}
bool FRaftSimRaftFlipsAndRecoversTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimForceOverwashCommand(this));
    AddCommand(new FObserveProductionFlip(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertRecoveredCommand(this));
    return true;
}
#endif
