#include "RaftSimEddyDemoBoundary.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimEddyDemoBoundaryTest,
    "RaftSim.Demo.EddySolidBoundary",EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimEddyDemoBoundaryTest::RunTest(const FString&)
{
    using namespace RaftSimEddyDemoBoundary;
    TestEqual(TEXT("solid reaches the hydraulic bed"),BoxCm().Min.Z,BedM*100.);
    int32 Excluded=0;
    for(int32 Y=0;Y<96;++Y)for(int32 X=0;X<184;++X)
    {
        const FVector2D P(-800.+25.*X,-1200.+25.*Y);
        if(OverlapsFootprint(FBox2D(P,P+FVector2D(25.,25.))))++Excluded;
    }
    TestEqual(TEXT("exact 4 by 8 metre opening excludes 512 quarter-metre cells"),Excluded,512);
    TestFalse(TEXT("water cell touching but outside block is retained"),OverlapsFootprint(FBox2D(FVector2D(200,-25),FVector2D(225,0))));
    double MaximumNormal=0.,MaximumDivergence=0.;
    for(int32 I=-100;I<=100;++I)
    {
        const double T=double(I)/100.;
        for(const FVector P:{FVector(-200,400*T,0),FVector(200,400*T,0),FVector(200*T,-400,0),FVector(200*T,400,0)})
            MaximumNormal=FMath::Max(MaximumNormal,Velocity(P).Size());
    }
    TestEqual(TEXT("all solid faces have zero normal current"),MaximumNormal,0.);
    TestTrue(TEXT("upstream flow diverts outward above block"),Velocity(FVector(-400,300,0)).Y>0.);
    TestTrue(TEXT("upstream flow diverts outward below block"),Velocity(FVector(-400,-300,0)).Y<0.);
    TestTrue(TEXT("flow passes along upper side"),Velocity(FVector(0,550,0)).X>0.);
    TestTrue(TEXT("far upstream current is unchanged"),Velocity(FVector(-800,300,0)).Equals(FVector(2,0,0),1.e-12));
    TestTrue(TEXT("direct wake has upstream return, not downstream centre seam"),Velocity(FVector(1600,0,0)).X<0.);
    TestTrue(TEXT("near-centre wake pulls toward obstacle"),Velocity(FVector(1600,160,0)).X<0.);
    TestTrue(TEXT("eddy head turns outward on upper side"),Velocity(FVector(700,240,0)).Y>0.);
    TestTrue(TEXT("eddy head turns outward on lower side"),Velocity(FVector(700,-240,0)).Y<0.);
    TestTrue(TEXT("outer branch rejoins downstream current"),Velocity(FVector(900,500,0)).X>0.);
    TestEqual(TEXT("symmetry axis has no artificial lateral boat kick"),Velocity(FVector(1600,0,0)).Y,0.);
    constexpr double H=.001;
    for(int32 Y=-23;Y<=23;++Y)for(int32 X=-19;X<=45;++X)
    {
        const FVector P(X*55.+7,Y*55.+9,0);if(Solid(P))continue;
        const double D=(Velocity(P+FVector(H*100.,0,0)).X-Velocity(P-FVector(H*100.,0,0)).X+
            Velocity(P+FVector(0,H*100.,0)).Y-Velocity(P-FVector(0,H*100.,0)).Y)/(2.*H);
        MaximumDivergence=FMath::Max(MaximumDivergence,FMath::Abs(D));
    }
    TestTrue(TEXT("outside flow remains divergence free to finite difference tolerance"),MaximumDivergence<1.e-4);
    TestTrue(TEXT("swept path through block is rejected even with outside endpoints"),SegmentEntersSolid(FVector(-500,0,0),FVector(500,0,0)));
    int32 Steps=0;
    for(int32 I=0;I<61;++I)
    {
        FVector P(-650,-1050.+35.*I,2);
        for(int32 J=0;J<3600;++J)
        {
            if(!TestTrue(TEXT("RK2 tracer path never crosses solid"),Advect(P,1./120.)))return false;
            ++Steps;
            if(P.X>3700 || FMath::Abs(P.Y)>1100)break;
        }
    }
    // Exercise the same full-hull collision query used by the live demo, not
    // just Unreal's visual component collision or a position clamp.
    FRaftSimHullGeometry Hull;Hull.VerticesM={FVector(.5,-.3,-.2),FVector(.5,.3,-.2),FVector(.5,0,.3)};
    Hull.Faces={FIntVector(0,1,2)};Hull.Sections={{0,3,0,1}};
    FRaftSimFlexRigidState Before;Before.Position=FVector(-2.8,0,0);Before.LinearVelocity=FVector(4,0,0);
    auto State=Before;constexpr double Dt=.15;RaftSimSweptGround::Advance(State,Dt);
    const auto Contact=RaftSimHullContact::Integrate(State,Before,Hull,Hull,605.,FVector(100,100,100),Dt,Sweep);
    TestTrue(FString::Printf(TEXT("full-hull solid impact completes: %s"),*Contact.Failure),Contact.bCompleted);
    TestTrue(TEXT("collision applies a real production contact impulse"),Contact.Impulses>0);
    for(const auto& P:Hull.VerticesM)TestTrue(TEXT("front face stays outside upstream wall"),State.WorldPoint(P).X<=-2.+1.e-8);
    TestTrue(TEXT("collision does not add energy"),Contact.KineticChangeJ<=1.e-8);
    AddInfo(FString::Printf(TEXT("masked_cells=%d tracer_steps=%d maximum_divergence=%.12g contact_impulses=%d"),Excluded,Steps,MaximumDivergence,Contact.Impulses));
    return !HasAnyErrors();
}
#endif
