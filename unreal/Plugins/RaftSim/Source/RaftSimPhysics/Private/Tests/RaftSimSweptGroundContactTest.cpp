#include "RaftSimSweptGroundContact.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTriangleSweep.h"
#include "Interface_CollisionDataProviderCore.h"
#include "Misc/AutomationTest.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTriangleFeaturesTest,
    "RaftSim.Physics.SourceTriangleSweepFeatures",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimTriangleFeaturesTest::RunTest(const FString&)
{
    const FVector A(0,0,0),B(2,0,0),C(0,2,0);FHitResult Hit;
    TestTrue(TEXT("face contact"),RaftSimTriangleSweep::Triangle(FVector(.5,.5,1),FVector(.5,.5,-1),.25,A,B,C,Hit));
    TestTrue(TEXT("face time/normal/source point"),FMath::Abs(Hit.Time-.375)<1.e-7 && Hit.Normal.Equals(FVector::UpVector,1.e-12) && Hit.ImpactPoint.Equals(FVector(.5,.5,0),1.e-12));
    TestTrue(TEXT("edge contact outside face projection"),RaftSimTriangleSweep::Triangle(FVector(1,-.15,1),FVector(1,-.15,-1),.25,A,B,C,Hit));
    TestTrue(TEXT("edge analytic time and oblique normal"),FMath::Abs(Hit.Time-.4)<1.e-7 && Hit.Normal.Equals(FVector(0,-.6,.8),1.e-12) && Hit.ImpactPoint.Equals(FVector(1,0,0),1.e-12));
    TestTrue(TEXT("vertex contact outside both edge projections"),RaftSimTriangleSweep::Triangle(FVector(-.15,-.15,1),FVector(-.15,-.15,-1),.25,A,B,C,Hit));
    TestTrue(TEXT("vertex analytic time/source point"),FMath::Abs(Hit.Time-(1.-FMath::Sqrt(.25*.25-2.*.15*.15))*.5)<1.e-7 && Hit.ImpactPoint.Equals(A,1.e-12));
    TestFalse(TEXT("tangent motion does not create a blocking impulse"),RaftSimTriangleSweep::Triangle(FVector(-1,.5,.25),FVector(1,.5,.25),.25,A,B,C,Hit));
    TestFalse(TEXT("clear near miss"),RaftSimTriangleSweep::Triangle(FVector(-1,.5,.251),FVector(1,.5,.251),.25,A,B,C,Hit));
    TestTrue(TEXT("real initial overlap"),RaftSimTriangleSweep::Triangle(FVector(.5,.5,.1),FVector(.6,.5,.1),.25,A,B,C,Hit) && Hit.bStartPenetrating && FMath::Abs(Hit.PenetrationDepth-.15)<1.e-7);
    TestTrue(TEXT("winding does not remove a physical face"),RaftSimTriangleSweep::Triangle(FVector(.5,.5,1),FVector(.5,.5,-1),.25,A,C,B,Hit) && FMath::Abs(Hit.Time-.375)<1.e-7);
    TestTrue(TEXT("opposite-side source contact"),RaftSimTriangleSweep::Triangle(FVector(.5,.5,-1),FVector(.5,.5,1),.25,A,B,C,Hit) && Hit.Normal.Equals(-FVector::UpVector,1.e-12));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSweptContactSustainedTest,
    "RaftSim.Physics.SweptGroundSustainedSupport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSweptContactSustainedTest::RunTest(const FString&)
{
    const TArray<FVector> Supports{FVector(1.85,-.85,0),FVector(1.85,.85,0),
        FVector(0,-1,0),FVector(0,1,0),FVector(-1.85,-.85,0),FVector(-1.85,.85,0)};
    constexpr double Dt=1./120.,Radius=.28,Mass=605.;const FVector Inertia(180,180,400);
    // Independent analytic plane query; all six supports share the same ground.
    const auto Plane=[](const FVector& Normal)
    {
        return FRaftSimGroundSweep([Normal](const FVector& A,const FVector& B,double R,FHitResult& Hit)
        {
            const double DA=FVector::DotProduct(A,Normal)-R;
            const double DB=FVector::DotProduct(B,Normal)-R;
            if(DB>=0 || DB>=DA)return false;
            Hit.Normal=Normal;
            if(DA<0){Hit.bStartPenetrating=true;Hit.PenetrationDepth=-DA;Hit.Time=0;}
            else Hit.Time=DA/(DA-DB);
            return true;
        });
    };
    for(const FVector InitialAngular:{FVector(.15,-.12,.2),FVector(2,-3,4)})
    for(const FVector Normal:{FVector::UpVector,FVector(-.25,0,1).GetSafeNormal()})
    {
        const auto Sweep=Plane(Normal);
        FRaftSimFlexRigidState State;State.Position=Normal*1.5;
        State.LinearVelocity=FVector(.8,.3,-1);State.AngularVelocity=InitialAngular;
        double MinimumGap=DBL_MAX,MaximumEnergyIncrease=0,MaximumTimeError=0;
        int32 TotalImpulses=0,Completed=0;
        for(int32 Step=0;Step<600;++Step)
        {
            const auto Previous=State;
            State.LinearVelocity.Z-=9.80665*Dt;
            const auto BeforeContact=State;
            const auto Energy=[&](const FRaftSimFlexRigidState& S)
            {const FVector W=S.AngularVelocity;return .5*(Mass*S.LinearVelocity.SizeSquared()+Inertia.X*W.X*W.X+Inertia.Y*W.Y*W.Y+Inertia.Z*W.Z*W.Z);};
            RaftSimSweptGround::Advance(State,Dt);
            const auto R=RaftSimSweptGround::Integrate(State,Previous,Supports,Radius,Mass,Inertia,Dt,Sweep);
            if(!R.bCompleted)
            {AddError(FString::Printf(TEXT("six-support sustained step %d: %s (%.12g / %.12g s)"),Step,*R.Failure,R.ConsumedSeconds,Dt));break;}
            TotalImpulses+=R.Impulses;
            ++Completed;
            MaximumEnergyIncrease=FMath::Max(MaximumEnergyIncrease,Energy(State)-Energy(BeforeContact));
            MaximumTimeError=FMath::Max(MaximumTimeError,FMath::Abs(R.ConsumedSeconds-Dt));
            if(FMath::Abs(R.ConsumedSeconds-Dt)>1.e-12 || Energy(State)>Energy(BeforeContact)+1.e-8)
            {AddError(TEXT("contact lost substep time or created kinetic energy"));break;}
            for(const auto& P:Supports)MinimumGap=FMath::Min(MinimumGap,FVector::DotProduct(State.WorldPoint(P),Normal)-Radius);
        }
        TestTrue(TEXT("gravity exercises repeated contacts"),TotalImpulses>100);
        TestTrue(FString::Printf(TEXT("six-support clearance remains within 10 micrometres: %.12g m"),MinimumGap),MinimumGap>=-1.e-5);
        TestTrue(TEXT("resting/slope-contact state remains finite"),!State.Position.ContainsNaN() && !State.AngularVelocity.ContainsNaN());
        AddInfo(FString::Printf(TEXT("support normal=%s initial_angular=%s completed=%d impulses=%d minimum_gap_m=%.12g maximum_energy_increase_j=%.12g maximum_time_error_s=%.12g"),
            *Normal.ToString(),*InitialAngular.ToString(),Completed,TotalImpulses,MinimumGap,MaximumEnergyIncrease,MaximumTimeError));
    }
    return !HasAnyErrors();
}

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
    // Reuse the actual captured component as a wide floor, top at world Z=0.
    Mesh->SetMobility(EComponentMobility::Movable);
    Ground->SetActorScale3D(FVector(1000,1000,1));Ground->SetActorLocation(FVector(0,0,-50));
    TestTrue(TEXT("actual deep initial overlap is not hidden by face refinement"),
        Sources.SweepCapturedSphere(FVector(0,0,20),FVector(1,0,19),28.,Hit) &&
        Hit.bStartPenetrating && FMath::Abs(Hit.PenetrationDepth-8.)<.001);
    int32 QueryDiscrepancies=0;
    const FRaftSimGroundSweep Sweep=[&](const FVector& A,const FVector& B,double R,FHitResult& H)
    {
        const bool Found=Sources.SweepCapturedSphere(A,B,R,H);
        if(A.Z>=R && B.Z<R)
        {
            const double Expected=(A.Z-R)/(A.Z-B.Z);
            if((!Found || H.Time>Expected+1.e-7 || H.Normal.Z<.999999) && QueryDiscrepancies++<12)
                AddInfo(FString::Printf(TEXT("query discrepancy found=%d az=%.12g bz=%.12g radius=%.12g time=%.12g expected=%.12g normal=%s impact=%s"),
                    int32(Found),A.Z,B.Z,R,double(H.Time),Expected,*H.Normal.ToString(),*H.ImpactPoint.ToString()));
        }
        return Found;
    };
    const TArray<FVector> Supports{FVector(1.85,-.85,0),FVector(1.85,.85,0),
        FVector(0,-1,0),FVector(0,1,0),FVector(-1.85,-.85,0),FVector(-1.85,.85,0)};
    FRaftSimFlexRigidState State;State.Position=FVector(0,0,1.5);
    State.LinearVelocity=FVector(.8,.3,-1);State.AngularVelocity=FVector(.15,-.12,.2);
    constexpr double Dt=1./120.;double MinimumGap=DBL_MAX;int32 Completed=0,Impulses=0;
    for(int32 Step=0;Step<600;++Step)
    {
        const auto Previous=State;State.LinearVelocity.Z-=9.80665*Dt;
        RaftSimSweptGround::Advance(State,Dt);
        const auto R=RaftSimSweptGround::Integrate(State,Previous,Supports,.28,605.,FVector(180,180,400),Dt,Sweep);
        if(!R.bCompleted){AddError(FString::Printf(TEXT("actual-mesh support step %d: %s"),Step,*R.Failure));break;}
        ++Completed;Impulses+=R.Impulses;
        for(const auto& P:Supports)
        {
            const FVector WorldPoint=State.WorldPoint(P);
            if(!Sources.SampleGround(WorldPoint*100.,GroundZ,N))
            {AddError(TEXT("actual-mesh independent ground query missing"));return false;}
            MinimumGap=FMath::Min(MinimumGap,WorldPoint.Z-GroundZ*.01-.28);
        }
    }
    TestEqual(TEXT("all actual-mesh sustained steps complete"),Completed,600);
    TestTrue(TEXT("actual mesh exercises repeated contact"),Impulses>100);
    TestTrue(TEXT("actual mesh maintains ten-micrometre support clearance"),MinimumGap>=-1.e-5);
    TestEqual(TEXT("every flat mesh query agrees with independent plane oracle"),QueryDiscrepancies,0);
    AddInfo(FString::Printf(TEXT("actual-mesh completed=%d impulses=%d minimum_gap_m=%.12g"),Completed,Impulses,MinimumGap));

    // Independent brute-force indexing check at a real river-sized world
    // offset, with rotation, reflection, nonuniform scale and a cache rebuild.
    const FTransform Changed(FRotator(17,31,-8),FVector(-543700,-360000,700),FVector(2,-3,.75));
    Ground->SetActorTransform(Changed);
    FTriMeshCollisionData Data;
    if(!Cube->GetPhysicsTriMeshData(&Data,false)){AddError(TEXT("source triangles unavailable"));return false;}
    const FVector Origin=Changed.GetTranslation();TArray<FVector> SourceVertices;
    for(const auto& V:Data.Vertices)SourceVertices.Add((Changed.TransformPosition(FVector(V))-Origin)*.01);
    FRandomStream Random(87131);int32 Compared=0;
    for(int32 Query=0;Query<96;++Query)
    {
        const FVector Direction=Random.VRand();const FVector Start=Direction*5.,End=-Direction*5.;
        FHitResult Indexed,Brute;bool BruteFound=false;
        const bool IndexedFound=Sources.SweepCapturedSphere(Origin+Start*100.,Origin+End*100.,28.,Indexed);
        for(const auto& T:Data.Indices)
        {
            FHitResult Candidate;
            if(RaftSimTriangleSweep::Triangle(Start,End,.28,SourceVertices[T.v0],SourceVertices[T.v1],SourceVertices[T.v2],Candidate) &&
                (!BruteFound || Candidate.Time<Brute.Time))
            {Brute=Candidate;BruteFound=true;}
        }
        if(IndexedFound!=BruteFound || (BruteFound && (FMath::Abs(Indexed.Time-Brute.Time)>1.e-7 || !Indexed.Normal.Equals(Brute.Normal,1.e-7))))
        {AddError(FString::Printf(TEXT("BVH/brute-force mismatch at query %d"),Query));break;}
        ++Compared;
    }
    TestEqual(TEXT("all transformed source queries match all-triangle evaluation"),Compared,96);
    return !HasAnyErrors();
}
#endif
