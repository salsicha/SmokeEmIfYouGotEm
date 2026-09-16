#include "RaftSimSurfaceSweep.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTriangleSweep.h"
#include "Interface_CollisionDataProviderCore.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
using namespace RaftSimSurfaceSweep;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSurfaceFeaturesTest,"RaftSim.Physics.FullSurfaceFeatures",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSurfaceFeaturesTest::RunTest(const FString&)
{
    const FTriangle Floor{{FVector(-1000,-1000,0),FVector(1000,-1000,0),FVector(0,1000,0)}};
    const auto Shift=[](FTriangle T,const FVector& Delta){for(auto& V:T.V)V+=Delta;return T;};
    const auto CheckWitness=[&](const FTriangle& A,const FTriangle& B,const FDistance& D)
    {
        const auto Rebuild=[](const FTriangle& T,const FVector& W){return T.V[0]*W.X+T.V[1]*W.Y+T.V[2]*W.Z;};
        TestTrue(TEXT("moving witness is on its source triangle"),(Rebuild(A,D.MovingBary)-D.MovingPoint).Length()<1.e-10);
        TestTrue(TEXT("ground witness is on its source triangle"),(Rebuild(B,D.GroundBary)-D.GroundPoint).Length()<1.e-10);
        TestTrue(TEXT("witness barycentrics are convex"),D.MovingBary.GetMin()>=0. && D.GroundBary.GetMin()>=0. &&
            FMath::Abs(D.MovingBary.X+D.MovingBary.Y+D.MovingBary.Z-1.)<1.e-12 &&
            FMath::Abs(D.GroundBary.X+D.GroundBary.Y+D.GroundBary.Z-1.)<1.e-12);
    };
    const FTriangle A{{FVector(-1,0,1),FVector(1,0,1),FVector(0,0,2)}};
    const FTriangle B{{FVector(0,-1,0),FVector(0,1,0),FVector(0,0,-1)}};
    const auto Edge=Distance(A,B);CheckWitness(A,B,Edge);
    TestTrue(TEXT("edge interiors are closest"),FMath::Abs(Edge.Squared-1.)<1.e-12 &&
        (Edge.MovingBary-FVector(.5,.5,0)).Length()<1.e-12 &&
        (Edge.GroundBary-FVector(.5,.5,0)).Length()<1.e-12);
    const auto EdgeHit=Sweep(A,Shift(A,FVector(0,0,-2)),B);
    TestTrue(TEXT("edge/edge crossing caught continuously"),EdgeHit.Status==EStatus::Contact &&
        FMath::Abs(EdgeHit.Time-(1.-1.e-5)/2.)<1.e-9);
    const FTriangle Wide{{FVector(-5,-5,1),FVector(5,-5,1),FVector(0,5,1)}};
    const FTriangle Tip{{FVector(0,0,0),FVector(-1,-1,-1),FVector(1,-1,-1)}};
    const auto Reverse=Distance(Wide,Tip);CheckWitness(Wide,Tip,Reverse);
    TestTrue(TEXT("ground vertex can hit moving face interior"),FMath::Abs(Reverse.Squared-1.)<1.e-12 &&
        Reverse.GroundBary==FVector(1,0,0) && Reverse.MovingBary.GetMin()>0.);
    const auto ReverseHit=Sweep(Wide,Shift(Wide,FVector(0,0,-2)),Tip);
    TestTrue(TEXT("reverse vertex/face crossing caught"),ReverseHit.Status==EStatus::Contact &&
        FMath::Abs(ReverseHit.Time-(1.-1.e-5)/2.)<1.e-9);
    const FTriangle Piercing{{FVector(0,0,-1),FVector(0,0,1),FVector(2,0,1)}};
    const auto Intersection=Distance(Piercing,Floor);
    TestTrue(TEXT("crossing faces are not a positive edge distance"),Intersection.Squared<1.e-24);
    TestTrue(TEXT("initial intersection is explicit, not clear"),Sweep(Piercing,Piercing,Floor).Status==EStatus::InitialIntersection);
    const FTriangle Coplanar{{FVector(-2,0,0),FVector(2,0,0),FVector(0,2,0)}};
    TestTrue(TEXT("coplanar intersection is retained"),Distance(Coplanar,Floor).Squared<1.e-24);
    const FTriangle Point{{FVector(0,0,1),FVector(0,0,1),FVector(0,0,1)}};
    TestTrue(TEXT("degenerate point surface is not dropped"),Sweep(Point,Shift(Point,FVector(0,0,-2)),Floor).Status==EStatus::Contact);
    const FTriangle Segment{{FVector(-1,0,1),FVector(1,0,1),FVector(0,0,1)}};
    TestTrue(TEXT("degenerate edge surface is not dropped"),FMath::Abs(Distance(Segment,B).Squared-1.)<1.e-12);
    auto End=Wide;End.V[0].Z=-1;
    const auto Deforming=Sweep(Wide,End,Floor);
    TestTrue(TEXT("independently moving vertex collision"),Deforming.Status==EStatus::Contact &&
        FMath::Abs(Deforming.Time-(1.-1.e-5)/2.)<1.e-9);
    TestTrue(TEXT("stationary separated surface is clear"),Sweep(Wide,Wide,Floor).Status==EStatus::Clear);
    TestTrue(TEXT("separating sweep is clear"),Sweep(Wide,Shift(Wide,FVector(0,0,10)),Floor).Status==EStatus::Clear);
    TestTrue(TEXT("iteration exhaustion cannot become clear"),Sweep(Wide,Shift(Wide,FVector(0,0,-2)),Floor,1.e-5,1).Status==EStatus::Unresolved);
    auto Invalid=Wide;Invalid.V[0].X=std::numeric_limits<double>::quiet_NaN();
    TestTrue(TEXT("nonfinite input rejected"),Sweep(Invalid,End,Floor).Status==EStatus::Invalid);
    auto Resting=Wide;for(auto& V:Resting.V)V.Z=1.e-5;
    auto Entering=Resting;Entering.V[0].Z+=.001;Entering.V[1].Z-=.001;
    const auto Simultaneous=Sweep(Resting,Entering,Floor,1.e-5,128,1.e-9);
    TestTrue(TEXT("simultaneous contact chooses still-entering source vertex"),Simultaneous.Status==EStatus::Contact &&
        Simultaneous.Time==0. && Simultaneous.Witness.MovingBary==FVector(0,1,0));
    TestTrue(TEXT("stationary skin contact clears only with a proven separating plane"),
        Sweep(Resting,Resting,Floor,1.e-5,128,1.e-9).Status==EStatus::Clear);
    FRandomStream Random(984123);
    for(int32 Trial=0;Trial<128;++Trial)
    {
        FTriangle Start=Wide;double Lowest=DBL_MAX;
        for(auto& V:Start.V){V.Z=Random.FRandRange(.01f,10.f);Lowest=FMath::Min(Lowest,V.Z);}
        const double Travel=Trial==0?1.e6:30.;
        const auto Hit=Sweep(Start,Shift(Start,FVector(0,0,-Travel)),Floor);
        TestTrue(TEXT("analytic plane TOI, including fast crossings"),Hit.Status==EStatus::Contact &&
            FMath::Abs(Hit.Time-(Lowest-1.e-5)/Travel)*Travel<2.e-10);
        TestTrue(TEXT("reported boundary remains outside source"),FMath::Sqrt(Hit.Witness.Squared)>=1.e-5-1.e-10);
        const auto Swapped=Distance(Floor,Start),Forward=Distance(Start,Floor);
        TestTrue(TEXT("distance symmetric"),FMath::Abs(Swapped.Squared-Forward.Squared)<1.e-10);
        CheckWitness(Start,Floor,Forward);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSurfaceSeparationProofTest,"RaftSim.Physics.SurfaceSeparationProof",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSurfaceSeparationProofTest::RunTest(const FString&)
{
    const FTriangle Ground{{FVector(-100,-100,0),FVector(100,-100,0),FVector(0,100,0)}};
    FRandomStream Random(140729);TArray<FTriangle> Starts,Ends;
    for(int32 I=0;I<128;++I)
    {
        FTriangle A{{FVector(-1,-1,.2),FVector(1,-1,.5),FVector(0,1,.3)}},B=A;
        for(int32 J=0;J<3;++J)
        {A.V[J].Z=Random.FRandRange(.01f,2.f);B.V[J]=A.V[J]+FVector(.03,.05,I%2?-.005:-3.);}
        Starts.Add(A);Ends.Add(B);
        const auto Fast=Sweep(A,B,Ground,1.e-5,128,1.e-9,true),Reference=Sweep(A,B,Ground,1.e-5,128,1.e-9,false);
        TestTrue(TEXT("proof preserves actual crossing/clear classification"),Fast.Status==Reference.Status);
        if(Fast.Status==EStatus::Contact)
            TestTrue(TEXT("entering contact unchanged"),Fast.Time==Reference.Time && Fast.Witness.MovingBary==Reference.Witness.MovingBary && Fast.Normal==Reference.Normal);
        else
            for(int32 S=0;S<=32;++S)
            {
                FTriangle T;for(int32 J=0;J<3;++J)T.V[J]=FMath::Lerp(A.V[J],B.V[J],S/32.);
                TestTrue(TEXT("independent feature distance stays outside proof clearance"),Distance(T,Ground).Squared>1.e-18);
            }
    }
    for(int32 Order=0;Order<2;++Order)
    {
        double SlowMs=0.,FastMs=0.;int32 Count=0;
        for(int32 Repeat=0;Repeat<8;++Repeat)
        {
            const auto Run=[&](bool Fast)
            {const double T=FPlatformTime::Seconds();for(int32 I=1;I<Starts.Num();I+=2)
                {const auto R=Sweep(Starts[I],Ends[I],Ground,1.e-5,128,1.e-9,Fast);if(R.Status!=EStatus::Clear)AddError(TEXT("timed proof query changed result"));}
                return (FPlatformTime::Seconds()-T)*1000.;};
            if(Order==0){SlowMs+=Run(false);FastMs+=Run(true);}else{FastMs+=Run(true);SlowMs+=Run(false);}
            Count+=Starts.Num()/2;
        }
        AddInfo(FString::Printf(TEXT("same-input source-plane proof order=%d queries=%d reference_ms=%.6f proof_ms=%.6f; not gameplay FPS"),Order,Count,SlowMs,FastMs));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSourceSurfaceBVHTest,"RaftSim.Physics.SourceSurfaceBVH",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSourceSurfaceBVHTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Actor=World->SpawnActor<AStaticMeshActor>();
    if(!Asset || !Actor){AddError(TEXT("source cube unavailable"));return false;}
    Actor->Tags.Add(TEXT("RaftSimPhysicalGround"));auto* Component=Actor->GetStaticMeshComponent();
    Component->SetStaticMesh(Asset);Component->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    FTriMeshCollisionData Data;if(!Asset->GetPhysicsTriMeshData(&Data,false))return false;
    const TArray<FIntVector> Faces{FIntVector(0,1,2),FIntVector(0,2,3)};
    for(const FTransform Transform:{FTransform::Identity,
        FTransform(FRotator(17,33,-11),FVector(-543186,-360044,235),FVector(1.2,-.8,1.1))})
    {
        Actor->SetActorTransform(Transform);
        TArray<FVector> Start,End;
        for(const FVector V:{FVector(-20,-20,150),FVector(20,-20,150),FVector(20,20,150),FVector(-20,20,150)})
        {Start.Add(Transform.TransformPosition(V));End.Add(Transform.TransformPosition(V-FVector(0,0,300)));}
        FRaftSimGroundSourceRegistry Registry(World);
        const auto Actual=Registry.SweepCapturedSurface(Start,End,Faces,.001);
        TestTrue(TEXT("source BVH detects full indexed surface"),Actual.Status==EStatus::Contact);
        TestTrue(TEXT("component and original face identities retained"),Actual.GroundComponent.Get()==Component &&
            Data.Indices.IsValidIndex(Actual.GroundFace) && Faces.IsValidIndex(Actual.MovingFace));
        double Earliest=1.;
        // Independent broad phase: enumerate EVERY collision-provider face.
        const FVector Origin=Transform.GetTranslation();
        for(const auto& F:Faces)
        {
            FTriangle A,E;
            for(int32 I=0;I<3;++I){A.V[I]=(Start[F[I]]-Origin)*.01;E.V[I]=(End[F[I]]-Origin)*.01;}
            for(const auto& G:Data.Indices)
            {
                const FTriangle Ground{{Transform.TransformVector(FVector(Data.Vertices[G.v0]))*.01,
                    Transform.TransformVector(FVector(Data.Vertices[G.v1]))*.01,
                    Transform.TransformVector(FVector(Data.Vertices[G.v2]))*.01}};
                const auto Hit=Sweep(A,E,Ground);
                TestTrue(TEXT("brute source query resolves"),Hit.Status==EStatus::Clear || Hit.Status==EStatus::Contact);
                if(Hit.Status==EStatus::Contact)Earliest=FMath::Min(Earliest,Hit.Time);
            }
        }
        TestTrue(TEXT("BVH earliest TOI matches all source faces"),FMath::Abs(Actual.Time-Earliest)<1.e-10);
        const double Expected=(Transform.GetScale3D().Z-1.e-5)/(3.*Transform.GetScale3D().Z);
        TestTrue(TEXT("transformed analytic top face TOI"),FMath::Abs(Actual.Time-Expected)<1.e-9);
        TArray<FIntVector> BadFaces{FIntVector(0,1,999)};
        TestTrue(TEXT("invalid index cannot disappear in broad phase"),Registry.SweepCapturedSurface(Start,End,BadFaces,.001).Status==EStatus::Invalid);
        for(auto& V:Start)V+=FVector(100000,0,0);
        End=Start;
        const auto Far=Registry.SweepCapturedSurface(Start,End,Faces,.001);
        TestTrue(TEXT("disjoint source bounds reject without triangle work"),Far.Status==EStatus::Clear && Far.TrianglePairs==0);
    }
    return true;
}
#endif
