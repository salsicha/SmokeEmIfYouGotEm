#include "RaftSimSurfaceSweep.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTriangleSweep.h"
#include "RaftSimHullShapeEnclosure.h"
#include "RaftSimLocalEndpointEnclosure.h"
#include "RaftSimHullContact.h"
#include "RaftSimFaceOrdering.h"
#include "Interface_CollisionDataProviderCore.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
using namespace RaftSimSurfaceSweep;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimOriginalVertexEnclosureTest,"RaftSim.Physics.OriginalVertexEnclosure",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimOriginalVertexEnclosureTest::RunTest(const FString&)
{
    FRandomStream Random(20261004);
    FRaftSimHullGeometry Before,After;
    // This numerical control is not an alternative production collision hull.
    // Production contact and captured-pin tests below exercise the real asset.
    for(int32 I=0;I<26610;++I)
    {
        const FVector V(Random.FRandRange(-5.f,5.f),Random.FRandRange(-3.f,3.f),Random.FRandRange(-2.f,2.f));
        Before.VerticesM.Add(V);
        After.VerticesM.Add(V+FVector(Random.FRandRange(-.7f,.7f),Random.FRandRange(-.7f,.7f),Random.FRandRange(-.7f,.7f)));
    }
    const auto Check=[&](double Dt)
    {
        double LegacyRadius=0.,LegacySpeed=0.,Radius=0.,Speed=0.;
        for(int32 I=0;I<Before.VerticesM.Num();++I)
        {
            LegacyRadius=FMath::Max(LegacyRadius,FMath::Max(Before.VerticesM[I].Length(),After.VerticesM[I].Length()));
            LegacySpeed=FMath::Max(LegacySpeed,(After.VerticesM[I]-Before.VerticesM[I]).Length()/Dt);
        }
        RaftSimHullContact::MeasureShapeEnclosure(Before,After,Dt,Radius,Speed);
        TestTrue(TEXT("radius equals the original all-vertex loop exactly, without tolerance"),Radius==LegacyRadius);
        TestTrue(TEXT("shape speed equals the original all-vertex loop exactly, without tolerance"),Speed==LegacySpeed);
    };
    for(double Dt:{1.01e-12,1./120.,1./60.,.1,1.,1.e100})Check(Dt);
    // A late deformed vertex must still enlarge both bounds.
    After.VerticesM.Last()=FVector(80.,-40.,90.);Check(1./60.);
    After.VerticesM=Before.VerticesM;Check(1./60.);
    Before.VerticesM[0]=After.VerticesM[0]=FVector(0.,-0.,0.);Check(1./60.);
    // Finite inputs can overflow their squared norm: preserve that result too.
    After.VerticesM.Last()=FVector(1.e200,0.,0.);Check(1./60.);
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimEndpointFaceTreeTest,"RaftSim.Physics.LandscapeOriginalFaceTree",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimEndpointFaceTreeTest::RunTest(const FString&)
{
    TestTrue(TEXT("normal landscape ordering uses qualified exact radix"),
        RaftSimFaceOrdering::UsesRadixLandscapeOrder(TEXT("")));
    TestFalse(TEXT("explicit original ordering remains available"),
        RaftSimFaceOrdering::UsesRadixLandscapeOrder(TEXT("-RaftSimReferenceLandscapeOrder")));
    TestTrue(TEXT("legacy radix opt-in remains compatible with normal ordering"),
        RaftSimFaceOrdering::UsesRadixLandscapeOrder(TEXT("-RaftSimRadixLandscapeOrder")));
    TestFalse(TEXT("explicit reference wins over legacy opt-in"),
        RaftSimFaceOrdering::UsesRadixLandscapeOrder(TEXT("-RaftSimRadixLandscapeOrder -RaftSimReferenceLandscapeOrder")));
    FRandomStream Random(20261003);
    // Sorting is exact, not a uniqueness assumption about mutable tree IDs.
    // Include duplicates, every signed byte boundary, odd/even active passes,
    // all-equal input, empty/singleton lists, and production-sized lists.
    TArray<int32> OrderingScratch;
    for(int32 Count:{0,1,2,7,64,255,256,1024,38344})
    {
        for(int32 Pattern=0;Pattern<7;++Pattern)
        {
            TArray<int32> Values;
            for(int32 I=0;I<Count;++I)
            {
                const uint32 Bits=Random.GetUnsignedInt();
                int32 V=0;FMemory::Memcpy(&V,&Bits,sizeof(V));
                if(Pattern==1)V=17;
                if(Pattern==2)V=Count-I;
                if(Pattern==3)V=I%3-1;
                if(Pattern==4)V=int32(Bits&0xffu)+0x12340000;
                if(Pattern==5)V=int32(Bits&0xffffu);
                if(Pattern==6)V=I%2?std::numeric_limits<int32>::max():std::numeric_limits<int32>::min();
                Values.Add(V);
            }
            auto Reference=Values;Reference.Sort();
            RaftSimFaceOrdering::Radix(Values,OrderingScratch);
            TestTrue(TEXT("candidate ordering preserves the complete signed multiset exactly"),Values==Reference);
        }
    }
    TArray<FVector> Rest,Start,End;TArray<FIntVector> Faces;
    for(int32 I=0;I<512;++I)
    {
        const int32 Base=Rest.Num();
        const FVector Center(Random.FRandRange(-6.f,6.f),Random.FRandRange(-3.f,3.f),Random.FRandRange(-1.f,1.f));
        for(int32 J=0;J<3;++J)Rest.Add(Center+FVector(Random.FRandRange(-.2f,.2f),Random.FRandRange(-.2f,.2f),Random.FRandRange(-.2f,.2f)));
        Faces.Add(FIntVector(Base,Base+1,Base+2));
    }
    FRaftSimEndpointFaceTree Tree;
    for(int32 Pose=0;Pose<48;++Pose)
    {
        Start.Reset();End.Reset();
        const FVector Origin=Pose%2?FVector(-543186,-360044,235):FVector::ZeroVector;
        const FTransform Transform(FRotator(Pose*7.,Pose*11.,Pose*13.),Origin,Pose%3?FVector(100,100,100):FVector(-120,80,110));
        for(const auto& P:Rest)
        {
            const FVector A=Transform.TransformPosition(P);
            Start.Add(A);End.Add(A+FVector(Random.FRandRange(-40.f,40.f),Random.FRandRange(-40.f,40.f),Random.FRandRange(-40.f,40.f)));
        }
        // Connectivity changes must invalidate topology; shape changes must
        // refit all leaves rather than inherit previous/rest-pose bounds.
        if(Pose==17)Swap(Faces[0].Y,Faces[0].Z);
        if(Pose==31)Faces.RemoveAt(3);
        const auto OriginalStart=Start,OriginalEnd=End;const auto OriginalFaces=Faces;
        const double Skin=Pose%2?.001:4.;
        TestTrue(TEXT("valid original endpoints refit"),Tree.Refit(Start,End,Faces,Skin));
        FRaftSimEndpointFaceTree MeterTree;TArray<FVector> StartM,EndM;
        for(int32 I=0;I<Start.Num();++I){StartM.Add(Start[I]*.01);EndM.Add(End[I]*.01);}
        TestTrue(TEXT("origin-relative metre inputs refit"),MeterTree.Refit(StartM,EndM,Faces,Skin*.01,true));
        for(int32 I=0;I<Faces.Num();++I)
        {
            FBox Reference(ForceInit);
            for(int32 J=0;J<3;++J){Reference+=Start[Faces[I][J]]*.01;Reference+=End[Faces[I][J]]*.01;}
            Reference=Reference.ExpandBy(Skin*.01);
            TestTrue(TEXT("every shared-vertex face enclosure equals the original six-endpoint construction exactly"),
                Tree.FaceBounds[I].Min==Reference.Min && Tree.FaceBounds[I].Max==Reference.Max && Tree.FaceBounds[I].IsValid==Reference.IsValid);
            TestTrue(TEXT("metre-input enclosure equals the original six-endpoint construction exactly"),
                MeterTree.FaceBounds[I].Min==Reference.Min && MeterTree.FaceBounds[I].Max==Reference.Max);
        }
        for(int32 Query=0;Query<48;++Query)
        {
            const FVector Center=(Query==0?Origin+FVector(1.e6):Transform.TransformPosition(Rest[Random.RandRange(0,Rest.Num()-1)]))*.01;
            const FVector Extent(Query%2?.015:.3);
            const FBox GroundBounds(Center-Extent,Center+Extent);
            TArray<int32> Actual,Reference;Tree.Candidates(GroundBounds,Actual);
            TArray<int32> RadixActual;Tree.GatherCandidates(GroundBounds,RadixActual);
            RaftSimFaceOrdering::Radix(RadixActual,OrderingScratch);
            TestTrue(TEXT("radix ordering equals original query ordering exactly"),RadixActual==Actual);
            for(int32 I=0;I<Faces.Num();++I)
            {
                FBox Box(ForceInit);
                for(int32 J=0;J<3;++J){Box+=Start[Faces[I][J]]*.01;Box+=End[Faces[I][J]]*.01;}
                if(Box.ExpandBy(Skin*.01).Intersect(GroundBounds))Reference.Add(I);
            }
            TestTrue(TEXT("every original overlapping face and tie order matches exhaustive enumeration"),Actual==Reference);
            TArray<int32> MeterActual;MeterTree.Candidates(GroundBounds,MeterActual);
            TestTrue(TEXT("metre-input captured-mesh path preserves exact endpoint bounds"),MeterActual==Reference);
            if(Query<8)
            {
                const FTriangle Ground{{GroundBounds.Min,
                    FVector(GroundBounds.Max.X,GroundBounds.Min.Y,GroundBounds.Min.Z),GroundBounds.Max}};
                for(int32 K=0;K<FMath::Min(Actual.Num(),2);++K)
                {
                    const int32 Face=Actual[K];FTriangle A,B,CachedA,CachedB;
                    for(int32 J=0;J<3;++J)
                    {
                        A.V[J]=Start[Faces[Face][J]]*.01;B.V[J]=End[Faces[Face][J]]*.01;
                        CachedA.V[J]=StartM[Faces[Face][J]];CachedB.V[J]=EndM[Faces[Face][J]];
                        TestTrue(TEXT("per-query original endpoint conversion preserves every triangle point exactly"),
                            A.V[J]==CachedA.V[J] && B.V[J]==CachedB.V[J]);
                    }
                    const auto ReferenceHit=Sweep(A,B,Ground,Skin*.01,128,-.01);
                    const auto CachedHit=Sweep(CachedA,CachedB,Ground,Skin*.01,128,-.01);
                    TestTrue(TEXT("removing the duplicate candidate bounds test preserves contact status and time exactly"),
                        ReferenceHit.Status==CachedHit.Status && ReferenceHit.Time==CachedHit.Time);
                    TestTrue(TEXT("cached endpoints preserve exact contact witnesses"),
                        ReferenceHit.Witness.MovingPoint==CachedHit.Witness.MovingPoint &&
                        ReferenceHit.Witness.GroundPoint==CachedHit.Witness.GroundPoint);
                }
            }
            TArray<int32> Groups;
            Tree.CandidateGroups([&](const FBox& Box){return Box.Intersect(GroundBounds);},Groups);
            for(const int32 I:Reference)TestTrue(TEXT("group pruning preserves every original overlapping face"),Groups.Contains(I));
            for(int32 I=1;I<Groups.Num();++I)TestTrue(TEXT("group IDs retain strict original order"),Groups[I]>Groups[I-1]);
        }
        TestTrue(TEXT("no hull vertex or index was edited"),Start==OriginalStart && End==OriginalEnd && Faces==OriginalFaces);
    }
    // Dense shared-index numerical fixture at production vertex/face counts.
    // This is NOT a replacement production hull; real-asset contact and pin
    // controls remain separate mandatory tests.
    Start.Reset();End.Reset();Faces.Reset();
    for(int32 I=0;I<26610;++I)
    {
        const FVector A(Random.FRandRange(-600.f,600.f),Random.FRandRange(-300.f,300.f),Random.FRandRange(-100.f,100.f));
        Start.Add(A);End.Add(A+FVector(Random.FRandRange(-40.f,40.f),Random.FRandRange(-40.f,40.f),Random.FRandRange(-40.f,40.f)));
    }
    for(int32 I=0;I<38344;++I)Faces.Add(FIntVector(I%Start.Num(),(I+1)%Start.Num(),(I+7)%Start.Num()));
    Start[0]=FVector(0.,-0.,0.);End[0]=FVector(-0.,0.,-0.);
    TestTrue(TEXT("dense shared-vertex pose refits all original faces"),Tree.Refit(Start,End,Faces,.001));
    for(int32 I=0;I<Faces.Num();++I)
    {
        FBox Reference(ForceInit);
        for(int32 J=0;J<3;++J){Reference+=Start[Faces[I][J]]*.01;Reference+=End[Faces[I][J]]*.01;}
        Reference=Reference.ExpandBy(.001*.01);
        TestTrue(TEXT("dense indexed face bounds equal original six-endpoint bounds without tolerance"),
            Tree.FaceBounds[I].Min==Reference.Min && Tree.FaceBounds[I].Max==Reference.Max);
    }
    auto BadFaces=Faces;BadFaces[0].X=Start.Num();
    TestFalse(TEXT("invalid source index refuses"),Tree.Refit(Start,End,BadFaces,.001));
    TestFalse(TEXT("nonfinite skin refuses"),Tree.Refit(Start,End,Faces,std::numeric_limits<double>::quiet_NaN()));
    End[0].Z=std::numeric_limits<double>::infinity();
    TestFalse(TEXT("nonfinite endpoint refuses"),Tree.Refit(Start,End,Faces,.001));
    return !HasAnyErrors();
}
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimExactHullValidityCertificateTest,"RaftSim.Physics.ExactHullValidityCertificate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimExactHullValidityCertificateTest::RunTest(const FString&)
{
    const auto Reference=[](const FRaftSimHullGeometry& G)
    {
        if(G.VerticesM.IsEmpty() || G.Faces.IsEmpty() || G.Sections.IsEmpty())return false;
        for(const auto& V:G.VerticesM)if(V.ContainsNaN())return false;
        for(const auto& F:G.Faces)
            if(!G.VerticesM.IsValidIndex(F.X) || !G.VerticesM.IsValidIndex(F.Y) || !G.VerticesM.IsValidIndex(F.Z))return false;
        int64 Vertices=0,Triangles=0;
        for(const auto& S:G.Sections)
        {
            if(S.VertexStart!=Vertices || S.FaceStart!=Triangles || S.VertexCount<=0 || S.FaceCount<=0)return false;
            Vertices+=S.VertexCount;Triangles+=S.FaceCount;
        }
        return Vertices==G.VerticesM.Num() && Triangles==G.Faces.Num();
    };
    // Numerical mutation controls, NOT an alternative game hull. The actual
    // original production hull/flip/contact controls remain mandatory.
    FRaftSimHullGeometry Original;
    for(int32 I=0;I<26610;++I)Original.VerticesM.Add(FVector(I*.001,(I%31)*.002,(I%23)*.003));
    for(int32 I=0;I<38344;++I)Original.Faces.Add(FIntVector(I%26610,(I+1)%26610,(I+2)%26610));
    Original.Sections.Add({0,26610,0,38344});
    const auto Compare=[&](const FRaftSimHullGeometry& G)
    {TestEqual(TEXT("exact certificate agrees with original full validation"),G.IsValid(),Reference(G));};
    Compare(Original);Compare(Original);
    auto Other=Original;Other.VerticesM.Last().X+=.001;Compare(Other);Compare(Original);Compare(Other);
    auto Changed=Original;
    Changed.VerticesM.Last().Z=std::numeric_limits<double>::quiet_NaN();Compare(Changed);Compare(Original);
    Changed=Original;Changed.VerticesM.Last().Z=std::numeric_limits<double>::infinity();Compare(Changed);
    Changed=Original;Changed.VerticesM[0].X=-0.;Compare(Changed);Compare(Changed);
    Changed=Original;Changed.Faces.Last().Z=26610;Compare(Changed);Compare(Original);
    Changed=Original;Changed.Faces.Last().Y=-1;Compare(Changed);
    Changed=Original;Changed.Sections[0].VertexCount--;Compare(Changed);
    Changed=Original;Changed.Sections[0].FaceCount--;Compare(Changed);
    Changed=Original;Changed.Sections[0].VertexStart=1;Compare(Changed);
    Changed=Original;Changed.Sections[0].FaceStart=1;Compare(Changed);
    Changed=Original;Changed.VerticesM.RemoveAt(Changed.VerticesM.Num()-1);Compare(Changed);
    Changed=Original;
    // Copy before appending: TArray rejects an element aliased into itself,
    // even when the intended mutation is only the face count.
    const FIntVector ExtraFace=Changed.Faces.Last();
    Changed.Faces.Add(ExtraFace);Compare(Changed);
    Changed=Original;Changed.Sections.Reset();Compare(Changed);
    FRandomStream Random(481039);
    for(int32 I=0;I<128;++I)
    {
        Changed=Original;
        const int32 Vertex=Random.RandRange(0,Changed.VerticesM.Num()-1);
        const int32 Face=Random.RandRange(0,Changed.Faces.Num()-1);
        switch(I%4)
        {
        case 0:Changed.VerticesM[Vertex].Y+=Random.FRand();break;
        case 1:Changed.VerticesM[Vertex].X=std::numeric_limits<double>::quiet_NaN();break;
        case 2:Changed.Faces[Face][I%3]=Changed.VerticesM.Num();break;
        default:Changed.Sections[0].FaceCount=Random.RandRange(1,Changed.Faces.Num()-1);break;
        }
        Compare(Changed);Compare(Original);
    }
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCapturedWholeHullBoundsTest,"RaftSim.Physics.CapturedWholeHullBounds",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCapturedWholeHullBoundsTest::RunTest(const FString&)
{
    // Exact enclosure arithmetic controls, not a substitute production hull.
    // The real captured-source queries below retain containment and contacts.
    FRandomStream Random(20261005);
    for(const int32 Count:{1,4,26610})
        for(const FVector Origin:{FVector::ZeroVector,FVector(-543186,-360044,235),FVector(1.e20,-1.e20,1.e20)})
        {
            TArray<FVector> Starts,Ends;
            FBox Initial(ForceInit);
            FRaftSimLocalEndpointEnclosure Accumulated;
            for(int32 I=0;I<Count;++I)
            {
                const FVector StartWorld=Origin+FVector(Random.FRandRange(-900.f,900.f),Random.FRandRange(-700.f,700.f),Random.FRandRange(-500.f,500.f));
                const FVector EndWorld=StartWorld+FVector(Random.FRandRange(-30.f,30.f),Random.FRandRange(-30.f,30.f),Random.FRandRange(-30.f,30.f));
                const FVector A=(StartWorld-Origin)*.01,B=(EndWorld-Origin)*.01;
                Starts.Add(A);Ends.Add(B);Initial+=A;Accumulated.Add(A,B);
            }
            FBox Reference=Initial;for(const auto& E:Ends)Reference+=E;
            FBox Actual(ForceInit);
            TestTrue(TEXT("every original finite endpoint participates"),Accumulated.Whole(Initial,Actual));
            TestTrue(TEXT("gathered enclosure exactly matches the original second scan"),
                Actual.Min==Reference.Min && Actual.Max==Reference.Max && Actual.IsValid==Reference.IsValid);
            FRaftSimLocalEndpointEnclosure Bad;
            Bad.Add(Starts[0],Ends[0]);
            Bad.Add(Starts.Last(),FVector(std::numeric_limits<double>::quiet_NaN(),0,0));
            TestFalse(TEXT("late local NaN cannot become a separation proof"),Bad.Whole(Initial,Actual));
            FRaftSimLocalEndpointEnclosure Overflow;
            const double Large=std::numeric_limits<double>::max();
            Overflow.Add(FVector::ZeroVector,(FVector(Large,0,0)-FVector(-Large,0,0))*.01);
            TestFalse(TEXT("finite world inputs with overflowing local subtraction refuse"),Overflow.Whole(Initial,Actual));
        }
    FRaftSimLocalEndpointEnclosure SignedZero;
    const FVector NegativeZero(-0.,0.,-0.);
    SignedZero.Add(NegativeZero,FVector::ZeroVector);
    FBox ZeroBounds(ForceInit);ZeroBounds+=NegativeZero;FBox ZeroWhole(ForceInit);
    TestTrue(TEXT("signed-zero enclosure remains valid"),SignedZero.Whole(ZeroBounds,ZeroWhole));
    TestTrue(TEXT("signed-zero enclosure remains zero"),ZeroWhole.Min==FVector::ZeroVector && ZeroWhole.Max==FVector::ZeroVector);
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Actor=World->SpawnActor<AStaticMeshActor>();
    if(!Asset || !Actor){AddError(TEXT("source cube unavailable"));return false;}
    auto* Component=Actor->GetStaticMeshComponent();Component->SetStaticMesh(Asset);
    const TArray<FIntVector> Faces{FIntVector(0,1,2),FIntVector(0,2,3)};
    for(const FTransform Transform:{FTransform::Identity,
        FTransform(FRotator(17,33,-11),FVector(-543186,-360044,235),FVector(1.2,-.8,1.1))})
    {
        Actor->SetActorTransform(Transform);
        FRaftSimTriangleSweepMesh Mesh;if(!Mesh.Build(Component))return false;
        TArray<FVector> Start,End;
        const auto Pose=[&](double StartZ,double EndZ)
        {
            Start.Reset();End.Reset();
            for(const FVector V:{FVector(-20,-20,0),FVector(20,-20,0),FVector(20,20,0),FVector(-20,20,0)})
            {Start.Add(Transform.TransformPosition(V+FVector(0,0,StartZ)));End.Add(Transform.TransformPosition(V+FVector(0,0,EndZ)));}
        };
        const auto Check=[&](EStatus Expected)
        {
            FRaftSimHullGeometry Before,After;Before.Faces=Faces;After.Faces=Faces;
            Before.Sections.Add({0,4,0,2});After.Sections=Before.Sections;
            for(const auto& V:Start)Before.VerticesM.Add(V*.01);
            for(const auto& V:End)After.VerticesM.Add(V*.01);
            // Same linear-deforming path represented through the production
            // arc interface, not an alternate hull used by the game.
            FRaftSimHullArcPath Path;Path.Before=&Before;Path.After=&After;
            Path.Interval=Path.Dt=1.;Path.State.Orientation=FQuat::Identity;
            const auto Reference=Mesh.SweepSurface(Start,End,Faces,.001,-1.,false,&Path);
            const auto Actual=Mesh.SweepSurface(Start,End,Faces,.001,-1.,true,&Path);
            TestTrue(TEXT("empty-space proof preserves original source-query status"),Actual.Status==Expected && Reference.Status==Expected);
            if(Expected==EStatus::Contact)
            {
                TestTrue(TEXT("real contact retains original face identities"),Actual.MovingFace==Reference.MovingFace && Actual.GroundFace==Reference.GroundFace);
                TestTrue(TEXT("real contact retains reference time of impact"),FMath::Abs(Actual.Time-Reference.Time)<1.e-10);
            }
            if(Expected==EStatus::Clear)TestEqual(TEXT("disjoint full enclosure needs no triangle pairs"),Actual.TrianglePairs,uint64(0));
        };
        Pose(150,150);Check(EStatus::Clear);
        Pose(150,-150);Check(EStatus::Contact);
        Pose(0,0);Check(EStatus::InitialIntersection);
        Pose(0,200);Check(EStatus::InitialIntersection);
        Pose(150,150);
        auto InvalidFaces=Faces;InvalidFaces[0].Z=999;
        FRaftSimHullArcPath UnusedPath;
        TestTrue(TEXT("invalid original index cannot vanish behind an empty-space proof"),
            Mesh.SweepSurface(Start,End,InvalidFaces,.001,-1.,true,&UnusedPath).Status==EStatus::Invalid);
        End.Last().Z=std::numeric_limits<double>::infinity();
        TestTrue(TEXT("nonfinite original endpoint cannot vanish behind an empty-space proof"),
            Mesh.SweepSurface(Start,End,Faces,.001,-1.,true,&UnusedPath).Status==EStatus::Invalid);
    }
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimClosedGroundTopologyTest,"RaftSim.Physics.ClosedGroundTopology",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimClosedGroundTopologyTest::RunTest(const FString&)
{
    using ELocation=FRaftSimClosedGround::ELocation;
    auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    FTriMeshCollisionData Data;if(!Asset || !Asset->GetPhysicsTriMeshData(&Data,false))return false;
    TArray<FVector> Vertices;TArray<FIntVector> Faces;
    // Deliberately split EVERY original triangle corner: exact seam topology
    // must work without rewriting any collision vertex or triangle.
    for(const auto& F:Data.Indices)
    {
        const int32 Base=Vertices.Num();
        for(const int32 I:{F.v0,F.v1,F.v2})Vertices.Add(FVector(Data.Vertices[I])*.01);
        Faces.Add(FIntVector(Base,Base+1,Base+2));
    }
    const auto OriginalVertices=Vertices;const auto OriginalFaces=Faces;
    FRaftSimClosedGround Closed;Closed.Build(Vertices,Faces);
    TestEqual(TEXT("split source corners reconstruct one closed component"),Closed.ComponentCount(),1);
    TestTrue(TEXT("centre is inside original triangles"),Closed.Classify(FVector::ZeroVector,Vertices,Faces)==ELocation::Inside);
    TestTrue(TEXT("outside is not a solid"),Closed.Classify(FVector(2,0,0),Vertices,Faces)==ELocation::Outside);
    TestTrue(TEXT("singular source vertex cannot be declared clear"),Closed.Classify(Vertices[0],Vertices,Faces)==ELocation::Unresolved);
    TestTrue(TEXT("classification never changes geometry"),Vertices==OriginalVertices && Faces==OriginalFaces);
    for(auto& F:Faces)Swap(F.Y,F.Z);
    Closed.Build(Vertices,Faces);
    TestTrue(TEXT("global reversed winding retains the solid"),Closed.Classify(FVector::ZeroVector,Vertices,Faces)==ELocation::Inside);
    Swap(Faces[0].Y,Faces[0].Z);Closed.Build(Vertices,Faces);
    TestTrue(TEXT("inconsistent closed winding refuses rather than inventing inside/outside"),Closed.Classify(FVector::ZeroVector,Vertices,Faces)==ELocation::Unresolved);
    Faces=OriginalFaces;Faces.RemoveAt(Faces.Num()-1);Closed.Build(Vertices,Faces);
    TestEqual(TEXT("open terrain sheet is not declared a closed volume"),Closed.ComponentCount(),0);
    TArray<FVector> OpenPoints;Closed.AddEnclosedRepresentatives(FBox(FVector(-2),FVector(2)),Vertices,OpenPoints);
    TestEqual(TEXT("open source sheet is retained for reverse containment"),OpenPoints.Num(),1);
    Faces=OriginalFaces;
    // Nested separately indexed solids with opposite orientation must not
    // cancel one another into a false zero winding number.
    const int32 Offset=Vertices.Num();for(const auto& V:OriginalVertices)Vertices.Add(V*.5);
    for(const auto& F:OriginalFaces)Faces.Add(FIntVector(F.X+Offset,F.Z+Offset,F.Y+Offset));
    Closed.Build(Vertices,Faces);
    TestEqual(TEXT("independent source solids stay separate"),Closed.ComponentCount(),2);
    TestTrue(TEXT("nested opposite winding cannot cancel containment"),Closed.Classify(FVector::ZeroVector,Vertices,Faces)==ELocation::Inside);
    // Concave closed source: an L-shaped prism. Its missing upper-right square
    // is inside the AABB but outside the solid, independently of triangle tests.
    Vertices={FVector(0,0,-1),FVector(2,0,-1),FVector(2,1,-1),FVector(1,1,-1),FVector(1,2,-1),FVector(0,2,-1)};
    for(int32 I=0;I<6;++I)Vertices.Add(Vertices[I]+FVector(0,0,2));
    Faces.Reset();
    const TArray<FIntVector> Cap{FIntVector(0,1,3),FIntVector(1,2,3),FIntVector(0,3,5),FIntVector(3,4,5)};
    for(const auto& F:Cap){Faces.Add(FIntVector(F.X,F.Z,F.Y));Faces.Add(FIntVector(F.X+6,F.Y+6,F.Z+6));}
    for(int32 I=0;I<6;++I){const int32 J=(I+1)%6;Faces.Add(FIntVector(I,J,J+6));Faces.Add(FIntVector(I,J+6,I+6));}
    Closed.Build(Vertices,Faces);
    TestTrue(TEXT("concave arm is inside"),Closed.Classify(FVector(.5,1.5,0),Vertices,Faces)==ELocation::Inside);
    TestTrue(TEXT("concavity is not filled by component bounds"),Closed.Classify(FVector(1.5,1.5,0),Vertices,Faces)==ELocation::Outside);
    FRandomStream Random(481027);
    for(int32 I=0;I<2048;++I)
    {
        const FVector P(Random.FRandRange(-.5f,2.5f),Random.FRandRange(-.5f,2.5f),Random.FRandRange(-1.5f,1.5f));
        const bool Inside=P.X>0. && P.X<2. && P.Y>0. && P.Y<2. && (P.X<1. || P.Y<1.) && FMath::Abs(P.Z)<1.;
        const auto Fast=Closed.Classify(P,Vertices,Faces),Reference=Closed.Classify(P,Vertices,Faces,false);
        TestTrue(TEXT("accelerated winding agrees with full solid angle"),Fast==Reference);
        TestTrue(TEXT("both classifiers agree with independent concave-prism volume"),Fast==(Inside?ELocation::Inside:ELocation::Outside));
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSourceContainmentTest,"RaftSim.Physics.SourceClosedContainment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSourceContainmentTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Actor=World->SpawnActor<AStaticMeshActor>();if(!Asset || !Actor)return false;
    Actor->Tags.Add(TEXT("RaftSimPhysicalGround"));auto* Component=Actor->GetStaticMeshComponent();
    Component->SetStaticMesh(Asset);Component->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    FRaftSimGroundSourceRegistry Registry(World);
    for(const FTransform Transform:{FTransform::Identity,
        FTransform(FRotator(17,33,-11),FVector(-543186,-360044,235),FVector(1.2,-.8,1.1))})
    {
        Actor->SetActorTransform(Transform);
        TArray<FVector> Start,End;
        for(const FVector V:{FVector(100,0,0),FVector(110,0,0),FVector(100,10,0),
            FVector(-10,-10,0),FVector(10,-10,0),FVector(0,10,0)})
        {Start.Add(Transform.TransformPosition(V));End.Add(Transform.TransformPosition(V+FVector(0,0,200)));}
        TArray<FIntVector> Faces{FIntVector(0,1,2),FIntVector(0,1,2)};
        TestTrue(TEXT("unreferenced inside vertices are not physical hull faces"),Registry.SweepCapturedSurface(Start,Start,Faces,.001).Status==EStatus::Clear);
        Faces[1]=FIntVector(3,4,5); // same count and allocation, different topology
        for(const bool Grouped:{false,true})
        {
            const auto Stationary=Registry.SweepCapturedSurface(Start,Start,Faces,.001,-1.,Grouped);
            TestTrue(TEXT("disconnected contained sheet is initial overlap"),Stationary.Status==EStatus::InitialIntersection && Stationary.Time==0. && Stationary.MovingFace==1);
            TestTrue(TEXT("source component retained without fabricating a contact normal"),Stationary.GroundComponent.Get()==Component && Stationary.Normal.IsZero());
            const auto Exiting=Registry.SweepCapturedSurface(Start,End,Faces,.001,-1.,Grouped);
            TestTrue(TEXT("an exit from a closed source is not a valid entering contact"),Exiting.Status==EStatus::InitialIntersection && Exiting.Time==0.);
        }
        Faces[1]=FIntVector(0,1,2);
        TestTrue(TEXT("topology replacement invalidates inside representative cache"),Registry.SweepCapturedSurface(Start,Start,Faces,.001).Status==EStatus::Clear);
        FTriMeshCollisionData Data;if(!Asset->GetPhysicsTriMeshData(&Data,false))return false;
        TArray<FVector> Enclosing;TArray<FIntVector> EnclosingFaces;
        for(const auto& V:Data.Vertices)Enclosing.Add(Transform.TransformPosition(FVector(V)*3.));
        for(const auto& F:Data.Indices)EnclosingFaces.Add(FIntVector(F.v0,F.v1,F.v2));
        for(const bool Grouped:{false,true})
            TestTrue(TEXT("closed source entirely inside a closed moving hull refuses"),
                Registry.SweepCapturedSurface(Enclosing,Enclosing,EnclosingFaces,.001,-1.,Grouped).Status==EStatus::InitialIntersection);
        // Opening the current pose cannot inherit the previous closed topology.
        EnclosingFaces.RemoveAt(EnclosingFaces.Num()-1);
        TestTrue(TEXT("an open surrounding sheet does not invent an interior"),
            Registry.SweepCapturedSurface(Enclosing,Enclosing,EnclosingFaces,.001).Status==EStatus::Clear);
    }
    return !HasAnyErrors();
}
#endif
