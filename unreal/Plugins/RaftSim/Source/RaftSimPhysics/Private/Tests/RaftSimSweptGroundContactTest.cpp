#include "RaftSimSweptGroundContact.h"
#include "RaftSimGroundSourceRegistry.h"
#include "Misc/AutomationTest.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSweptContactMathTest,
    "RaftSim.Physics.SweptGroundContactMath",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSweptContactMathTest::RunTest(const FString&)
{
    const double Mass=605.;const FVector Inertia(180,180,400);
    const auto Energy=[&](const FRaftSimFlexRigidState& S)
    {const auto& W=S.AngularVelocity;return .5*(Mass*S.LinearVelocity.SizeSquared()+Inertia.X*W.X*W.X+Inertia.Y*W.Y*W.Y+Inertia.Z*W.Z*W.Z);};
    FRaftSimFlexRigidState Impact;Impact.LinearVelocity=FVector(3,1,-.5);
    const double Before=Energy(Impact);
    const FVector Offset(1,.8,0),Normal(-1,0,0);
    TestTrue(TEXT("off-centre contact applies impulse"),RaftSimSweptGround::ApplyNormalImpulse(Impact,Offset,Normal,Mass,Inertia));
    TestTrue(TEXT("point normal speed is zero"),FMath::Abs(FVector::DotProduct(Impact.PointVelocity(Offset),Normal))<1.e-12);
    TestTrue(TEXT("normal impulse dissipates kinetic energy"),Energy(Impact)<Before);
    TestTrue(TEXT("off-centre normal impulse produces angular motion"),Impact.AngularVelocity.Z>0);
    TestFalse(TEXT("separating point needs no second impulse"),RaftSimSweptGround::ApplyNormalImpulse(Impact,Offset,Normal,Mass,Inertia));

    // Half spaces x<=100 cm and y<=100 cm, spheres in the free interior.
    const FRaftSimGroundSweep Walls=[](const FVector& A,const FVector& B,double R,FHitResult& Hit)
    {
        bool Found=false;double Best=1.;
        for(int32 Axis=0;Axis<2;++Axis)
        {
            const double Limit=100.-R;
            if(A[Axis]>Limit+1.e-8){Hit.bStartPenetrating=true;Hit.PenetrationDepth=A[Axis]-Limit;Hit.Time=0;Hit.Normal=FVector::ZeroVector;Hit.Normal[Axis]=-1;return true;}
            if(B[Axis]<=Limit || B[Axis]<=A[Axis])continue;
            const double T=(Limit-A[Axis])/(B[Axis]-A[Axis]);
            if(T<=Best){Found=true;Best=T;Hit.Time=T;Hit.Normal=FVector::ZeroVector;Hit.Normal[Axis]=-1;}
        }
        return Found;
    };
    TArray<FVector> Supports{FVector::ZeroVector};
    FRaftSimFlexRigidState Start;Start.LinearVelocity=FVector(4,1,.3);
    auto End=Start;RaftSimSweptGround::Advance(End,1.);
    const auto Contact=RaftSimSweptGround::Integrate(End,Start,Supports,.2,Mass,Inertia,1.,Walls);
    TestTrue(TEXT("corner consumes complete timestep"),Contact.bCompleted && FMath::Abs(Contact.ConsumedSeconds-1.)<1.e-12);
    TestEqual(TEXT("two different walls receive impulses"),Contact.Impulses,2);
    TestTrue(TEXT("both sphere boundaries respected within explicit ten-micrometre skin"),
        End.Position.X<=.8 && End.Position.Y<=.8 && .8-End.Position.X<=1.01e-5 && .8-End.Position.Y<=1.01e-5);
    TestTrue(TEXT("full unblocked displacement is preserved"),FMath::Abs(End.Position.Z-.3)<1.e-12);
    TestTrue(TEXT("unblocked vertical motion not lifted or discarded"),FMath::Abs(End.LinearVelocity.Z-.3)<1.e-12);
    auto Free=Start;RaftSimSweptGround::Advance(Free,.01);const auto Expected=Free;
    const auto Clear=RaftSimSweptGround::Integrate(Free,Start,Supports,.2,Mass,Inertia,.01,Walls);
    TestTrue(TEXT("no-contact state remains bit exact"),Clear.bCompleted && Clear.Impulses==0 && Free.Position==Expected.Position && Free.Orientation==Expected.Orientation && Free.LinearVelocity==Expected.LinearVelocity);
    auto OverlapStart=Start;OverlapStart.Position.X=.9;auto Overlap=OverlapStart;RaftSimSweptGround::Advance(Overlap,.01);const auto Original=Overlap;
    const auto Rejected=RaftSimSweptGround::Integrate(Overlap,OverlapStart,Supports,.2,Mass,Inertia,.01,Walls);
    TestTrue(TEXT("initial overlap is explicitly rejected without publishing partial state"),!Rejected.bCompleted && Rejected.Failure.Contains(TEXT("initial sphere overlap")) && Overlap.Position==Original.Position);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCapturedGroundSweepTest,
    "RaftSim.Physics.CapturedGroundSphereSweep",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCapturedGroundSweepTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if(!World)return false;
    ON_SCOPE_EXIT {World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Ground=World->SpawnActor<AStaticMeshActor>();
    if(!Cube || !Ground)return false;
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));
    auto* Mesh=Ground->GetStaticMeshComponent();Mesh->SetStaticMesh(Cube);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    FRaftSimGroundSourceRegistry Sources(World);FHitResult Hit;
    TestTrue(TEXT("complex captured mesh sphere sweep hits side before centre enters roof"),
        Sources.SweepCapturedSphere(FVector(-200,0,0),FVector(200,0,0),28.,Hit));
    TestTrue(TEXT("sweep hits left side at sphere radius clearance"),FMath::Abs(Hit.Time-.305)<1.e-4 && Hit.Normal.X<-.99);
    double GroundZ=0;FVector N;
    TestTrue(TEXT("same captured mesh remains roof query authority"),Sources.SampleGround(FVector::ZeroVector,GroundZ,N) && FMath::Abs(GroundZ-50.)<1.e-4);
    TestFalse(TEXT("broadphase rejects remote path"),Sources.SweepCapturedSphere(FVector(-200,1000,0),FVector(200,1000,0),28.,Hit));
    return !HasAnyErrors();
}
#endif
