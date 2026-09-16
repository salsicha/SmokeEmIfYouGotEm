#include "RaftSimHullContact.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "Engine/GameInstance.h"
#include "Subsystems/SubsystemCollection.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
namespace
{
FRaftSimHullGeometry Plate()
{
    FRaftSimHullGeometry H;H.VerticesM={FVector(-.6,-.4,-.2),FVector(.6,-.4,-.2),FVector(0,.7,-.2)};
    H.Faces={FIntVector(0,1,2)};H.Sections={{0,3,0,1}};return H;
}
RaftSimSurfaceSweep::FResult FloorQuery(TConstArrayView<FVector> A,TConstArrayView<FVector> B,
    TConstArrayView<FIntVector> Faces,double Skin,double Clearance)
{
    using namespace RaftSimSurfaceSweep;
    const FTriangle Ground{{FVector(-100,-100,0),FVector(100,-100,0),FVector(0,100,0)}};
    FResult Best;Best.Status=EStatus::Clear;Best.Time=1.;
    for(int32 I=0;I<Faces.Num();++I)
    {
        FTriangle Start,End;for(int32 J=0;J<3;++J){Start.V[J]=A[Faces[I][J]]*.01;End.V[J]=B[Faces[I][J]]*.01;}
        auto Hit=Sweep(Start,End,Ground,Skin*.01,128,Clearance*.01);Hit.MovingFace=I;Hit.GroundFace=0;
        if(Hit.Status!=EStatus::Clear && Hit.Status!=EStatus::Contact)return Hit;
        if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
    }
    return Best;
}
double Kinetic(const FRaftSimFlexRigidState& S)
{return .5*(220.*S.LinearVelocity.SizeSquared()+100.*S.AngularVelocity.SizeSquared());}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullResponseTest,"RaftSim.Physics.FullHullResponse",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHullResponseTest::RunTest(const FString&)
{
    const auto Hull=Plate();const FVector Inertia(100,100,100);
    for(const FVector Spin:{FVector::ZeroVector,FVector(.15,-.12,.2)})
    {
        FRaftSimFlexRigidState S;S.Position=FVector(0,0,.4);S.LinearVelocity=FVector(.2,.1,-3);S.AngularVelocity=Spin;
        int32 Impulses=0;
        for(int32 Step=0;Step<600;++Step)
        {
            const auto Before=S;constexpr double Dt=1./120.;S.LinearVelocity.Z-=9.81*Dt;
            const double InitialEnergy=Kinetic(S);RaftSimSweptGround::Advance(S,Dt);
            const auto R=RaftSimHullContact::Integrate(S,Before,Hull,Hull,220.,Inertia,Dt,FloorQuery);
            if(!TestTrue(FString::Printf(TEXT("full surface consumes sustained step %d: %s"),Step,*R.Failure),R.bCompleted))return false;
            Impulses+=R.Impulses;
            TestTrue(TEXT("entire substep consumed"),FMath::Abs(R.ConsumedSeconds-Dt)<1.e-12);
            TestTrue(TEXT("rigid contact does not create kinetic energy"),Kinetic(S)<=InitialEnergy+1.e-8);
            TestTrue(TEXT("rigid shape has zero prescribed work"),R.PrescribedShapeWorkJ==0.);
            TestTrue(TEXT("impulse energy ledger closes"),FMath::Abs(R.KineticChangeJ+R.DissipatedJ)<1.e-8);
            for(const auto& V:Hull.VerticesM)TestTrue(TEXT("every final hull vertex stays above plane"),S.WorldPoint(V).Z>=-1.e-9);
        }
        TestTrue(TEXT("sustained support actually applies impulses"),Impulses>0);
        AddInfo(FString::Printf(TEXT("full hull sustained support spin=%s steps=600 impulses=%d"),*Spin.ToString(),Impulses));
    }
    auto Expanded=Hull;for(auto& V:Expanded.VerticesM)V.Z-=.02;
    FRaftSimFlexRigidState Before;Before.Position=FVector(0,0,.20001);auto S=Before;
    constexpr double Dt=.01;RaftSimSweptGround::Advance(S,Dt);
    const auto Expansion=RaftSimHullContact::Integrate(S,Before,Hull,Expanded,220.,Inertia,Dt,FloorQuery);
    TestTrue(FString::Printf(TEXT("moving shape completes: %s"),*Expansion.Failure),Expansion.bCompleted);
    TestTrue(TEXT("prescribed expansion work is exposed"),Expansion.PrescribedShapeWorkJ>0.);
    TestTrue(TEXT("deforming contact work balances kinetic change and dissipation"),
        FMath::Abs(Expansion.KineticChangeJ-Expansion.PrescribedShapeWorkJ+Expansion.DissipatedJ)<1.e-8);
    for(const auto& V:Expanded.VerticesM)TestTrue(TEXT("deformed endpoint above ground"),S.WorldPoint(V).Z>=-1.e-9);
    AddInfo(FString::Printf(TEXT("prescribed deformation: work_j=%.17g dissipated_j=%.17g kinetic_change_j=%.17g impulses=%d"),
        Expansion.PrescribedShapeWorkJ,Expansion.DissipatedJ,Expansion.KineticChangeJ,Expansion.Impulses));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullArcAndFailureTest,"RaftSim.Physics.FullHullArcAndFailure",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHullArcAndFailureTest::RunTest(const FString&)
{
    auto Hull=Plate();Hull.VerticesM[0]=FVector::ZeroVector;auto After=Hull;After.VerticesM[1]+=FVector(.03,.02,.01);
    FRaftSimFlexRigidState Before;Before.Position=FVector(0,0,10);Before.LinearVelocity=FVector(1,0,0);Before.AngularVelocity=FVector(0,3,0);
    constexpr double Dt=.02;auto Predicted=Before;RaftSimSweptGround::Advance(Predicted,Dt);
    int32 Queries=0,Samples=0;
    const FRaftSimHullGroundQuery Clear=[&](TConstArrayView<FVector> A,TConstArrayView<FVector> B,TConstArrayView<FIntVector>,double Skin,double Clearance)
    {
        ++Queries;const double T0=A[0].X*.01,T1=B[0].X*.01;
        for(int32 Sample=0;Sample<=100;++Sample)
        {
            const double F=Sample/100.,T=FMath::Lerp(T0,T1,F);
            auto Exact=Before;RaftSimSweptGround::Advance(Exact,T);
            for(int32 I=0;I<A.Num();++I)
            {
                const FVector V=Exact.WorldPoint(FMath::Lerp(Hull.VerticesM[I],After.VerticesM[I],T/Dt));
                const double Error=(V-FMath::Lerp(A[I],B[I],F)*.01).Length();
                TestTrue(TEXT("actual rotating/deforming path enclosed by reported chord bound"),Error<=Skin*.01-1.e-5+1.e-12);
                TestTrue(TEXT("query safety clearance encloses curved path"),Error<Clearance*.01);
                ++Samples;
            }
        }
        RaftSimSurfaceSweep::FResult R;R.Status=RaftSimSurfaceSweep::EStatus::Clear;return R;
    };
    auto S=Predicted;const auto R=RaftSimHullContact::Integrate(S,Before,Hull,After,220.,FVector(100),Dt,Clear);
    TestTrue(TEXT("bounded curved path completes"),R.bCompleted && Queries>1 && R.MaximumCurveBoundM<=1.250000001e-6);
    TestTrue(TEXT("no-contact pose agrees with exact arc"),(S.Position-Predicted.Position).Length()<1.e-12 && S.Orientation.Equals(Predicted.Orientation,1.e-12));
    int32 Calls=0;
    const FRaftSimHullGroundQuery Refuse=[&](TConstArrayView<FVector>,TConstArrayView<FVector>,TConstArrayView<FIntVector>,double,double)
    {RaftSimSurfaceSweep::FResult X;X.Status=++Calls==1?RaftSimSurfaceSweep::EStatus::Clear:RaftSimSurfaceSweep::EStatus::Unresolved;return X;};
    S=Predicted;const auto Failed=RaftSimHullContact::Integrate(S,Before,Hull,After,220.,FVector(100),Dt,Refuse);
    TestTrue(TEXT("partial refusal does not claim completed time"),!Failed.bCompleted && Failed.ConsumedSeconds>0. && Failed.ConsumedSeconds<Dt);
    TestTrue(TEXT("partial refusal never assigns caller state"),S.Position==Predicted.Position && S.Orientation==Predicted.Orientation && S.LinearVelocity==Predicted.LinearVelocity);
    AddInfo(FString::Printf(TEXT("curved path independent samples=%d queries=%d maximum_bound_m=%.17g"),Samples,Queries,R.MaximumCurveBoundM));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullAdapterIntegrationTest,"RaftSim.Physics.FullHullAdapterIntegration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHullAdapterIntegrationTest::RunTest(const FString&)
{
    auto* Adapter=NewObject<URaftSimChronoRuntimeAdapter>();FRaftSimRaftBodyConfig Body;
    Body.MassKg=220;Adapter->ConfigureRaftBody(Body);
    FRaftSimFlexParameters Params;Params.MassKg=220;Params.PassengerCount=0;Params.GuideMassKg=0;
    Adapter->ConfigureFlexibleRaftModel(Params,{});
    Adapter->SetWaterSurfaceSampler([](const FVector&,float&){return false;});
    Adapter->SetGroundSurfaceSampler([](const FVector&,float& Z,FVector& N){Z=100000;N=FVector::UpVector;return true;});
    int32 Commits=0,SphereCalls=0;
    TestTrue(TEXT("full source initializes"),Adapter->SetHullGeometryProvider([](const auto&,FRaftSimHullGeometry& H){H=Plate();return true;},[&]{++Commits;}));
    Adapter->SetHullGroundQuery(FloorQuery);
    Adapter->SetGroundSphereSweep([&](const FVector&,const FVector&,double,FHitResult&){++SphereCalls;return false;});
    FRaftSimRaftKinematicState State;State.WorldTransform.SetTranslation(FVector(0,0,40));State.LinearVelocityMetersPerSecond=FVector(0,0,-3);
    Adapter->SetKinematicState(State);
    TestTrue(TEXT("full-hull adapter step succeeds"),Adapter->StepRaftDynamics(1.f/120.f));
    TestTrue(TEXT("adapter actually ran full-hull response"),Adapter->GetLastHullContact().bCompleted && Adapter->GetLastHullContact().Queries>0);
    TestEqual(TEXT("sphere fallback never invoked"),SphereCalls,0);
    TestTrue(TEXT("legacy roof-height projection disabled"),Adapter->GetKinematicState().WorldTransform.GetTranslation().Z<40.);
    TestEqual(TEXT("successful step publishes exact hull"),Commits,2);
    const auto Published=Adapter->GetKinematicState();const uint64 Revision=Adapter->GetHullGeometryRevision();
    Adapter->SetHullGroundQuery([](TConstArrayView<FVector>,TConstArrayView<FVector>,TConstArrayView<FIntVector>,double,double){return RaftSimSurfaceSweep::FResult();});
    AddExpectedError(TEXT("Full-hull ground review rejected"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("refused surface query fails adapter step"),Adapter->StepRaftDynamics(1.f/120.f));
    TestTrue(TEXT("refused step preserves published pose"),Adapter->GetKinematicState().WorldTransform.Equals(Published.WorldTransform,0.));
    TestEqual(TEXT("refused step preserves hull revision"),Adapter->GetHullGeometryRevision(),Revision);
    TestEqual(TEXT("refused step does not invoke commit"),Commits,2);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRaftFailureClockTest,"RaftSim.Clock.RaftFailureLatch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRaftFailureClockTest::RunTest(const FString&)
{
    auto* Instance=NewObject<UGameInstance>();auto* Bridge=NewObject<URaftSimPhysicsBridgeSubsystem>(Instance);
    FSubsystemCollection<UGameInstanceSubsystem> Collection;Bridge->Initialize(Collection);
    FRaftSimWaterRuntimeConfig Config;Config.bRequireAcceptedReportManifest=false;Config.AcceptedReportSetManifestPath.Reset();Config.bEnableDeterministicCapture=false;
    const float Dt=1.f/60.f;Bridge->ConfigureBridge(Config,FRaftSimRaftBodyConfig(),FRaftSimWaterRaftCouplingPolicy(),Dt,Dt*.5f);
    auto* Raft=Bridge->GetRaftRuntime();auto* Water=Bridge->GetWaterRuntime();
    Raft->ConfigureFlexibleRaftModel(FRaftSimFlexParameters(),{});
    if(!Water->ConfigureDevTankWindow(FVector2D::ZeroVector,4,4,.5,0,1)){Bridge->Deinitialize();return false;}
    int32 Prepares=0;
    Raft->SetHullGeometryProvider([&](const auto&,FRaftSimHullGeometry&){++Prepares;return false;},[]{});
    AddExpectedError(TEXT("Shared hull geometry rejected"),EAutomationExpectedErrorFlags::Contains,1);
    AddExpectedError(TEXT("Raft fixed substep refused"),EAutomationExpectedErrorFlags::Contains,1);
    FRaftSimPhysicsTickInput Input;Input.FrameDeltaSeconds=Dt;
    const auto First=Bridge->TickBridge(Input);const double WaterAfter=Water->GetCommittedStepSeconds();const int32 CallsAfter=Prepares;
    TestTrue(TEXT("raft failure exposed"),First.bFixedTickFailed);
    TestEqual(TEXT("no failed coupled tick committed"),First.CommittedPhysicsFrame,0);
    TestEqual(TEXT("first failed tick retains time debt"),First.SimulationBacklogSeconds,double(Dt));
    TestEqual(TEXT("partial water advance explicitly observable"),WaterAfter,double(Dt));
    const auto Second=Bridge->TickBridge(Input);
    TestTrue(TEXT("failure latches across rendered frames"),Second.bFixedTickFailed);
    TestEqual(TEXT("failed request not replayed"),Prepares,CallsAfter);
    TestEqual(TEXT("water not double advanced by retry"),Water->GetCommittedStepSeconds(),WaterAfter);
    TestEqual(TEXT("new elapsed time also retained"),Second.SimulationBacklogSeconds,2.*double(Dt));
    Bridge->ConfigureBridge(Config,FRaftSimRaftBodyConfig(),FRaftSimWaterRaftCouplingPolicy(),Dt,Dt*.5f);
    Water->ConfigureDevTankWindow(FVector2D::ZeroVector,4,4,.5,0,1);
    TestFalse(TEXT("explicit reconfigure clears failure latch"),Bridge->TickBridge(Input).bFixedTickFailed);
    Bridge->Deinitialize();return true;
}
#endif
